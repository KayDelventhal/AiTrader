"""Run browser acceptance against a fresh private database and owned server.

Never reuse the interactive preview, its PID file, or the user's configuration.
Artifacts are retained for diagnosis; only the process started here is stopped.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]


def isolated_environment(run_dir: Path, instance_id: str) -> dict[str, str]:
    return {
        **os.environ,
        "AITRADER_ENV_FILE": "",
        "APP_MODE": "DEMO",
        "DATABASE_URL": f"sqlite:///{(run_dir / 'acceptance.db').as_posix()}",
        "EXTERNAL_REQUESTS_ENABLED": "false",
        "PUBLIC_FEED_REQUESTS_ALLOWED": "false",
        "LIVE_ENABLED": "false",
        "DEMO_OWNER_PASSWORD": "local-demo-owner",
        "DEMO_PARTNER_PASSWORD": "local-demo-partner",
        "MAX_ORDER_EUR": "500",
        "MAX_POSITION_EUR": "1000",
        "APPROVAL_TTL_SECONDS": "120",
        "RUNTIME_INSTANCE_ID": instance_id,
        "LANGSMITH_TRACING": "false",
        "ANONYMIZED_TELEMETRY": "false",
        "MPLCONFIGDIR": str(run_dir / "matplotlib"),
    }


def wait_ready(process, url, instance_id, timeout=40):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Isolated test server exited before readiness; inspect its server.log.")
        try:
            with urllib.request.urlopen(url + "/api/v1/health", timeout=1) as response:
                health = json.load(response)
            if health.get("instance_id") == instance_id:
                return
            raise RuntimeError("Port belongs to another process; refusing to run acceptance against it.")
        except (OSError, ValueError):
            time.sleep(.1)
    raise RuntimeError("Isolated test server readiness timed out.")


def run():
    from manage import pnpm
    instance_id = f"e2e-{uuid.uuid4().hex}"
    run_dir = ROOT / ".runtime" / "e2e" / instance_id
    run_dir.mkdir(parents=True)
    env = isolated_environment(run_dir, instance_id)
    # Bind-test an ephemeral loopback port. Instance identity also protects the
    # small handoff race between closing this reservation and uvicorn binding.
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    pnpm("build")
    subprocess.run([sys.executable, "scripts/migrate.py"], cwd=ROOT, env=env, check=True)
    report = {"instance_id": instance_id, "database": str(run_dir / "acceptance.db"), "url": url, "status": "STARTING"}
    report_path = run_dir / "run.json"
    report_path.write_text(json.dumps(report, indent=2))
    with (run_dir / "server.log").open("wb") as log:
        process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", str(port)], cwd=ROOT, env=env, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            wait_ready(process, url, instance_id)
            print(f"Isolated browser acceptance: {url}\nDatabase: {run_dir / 'acceptance.db'}", flush=True)
            pnpm("e2e", environment={**env, "APP_URL": url, "AITRADER_E2E_INSTANCE": instance_id})
            report["status"] = "PASSED"
        except BaseException:
            report["status"] = "FAILED"
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            report["server_stopped"] = process.poll() is not None
            report_path.write_text(json.dumps(report, indent=2))
            print(f"Test server stopped; evidence retained in {run_dir}", flush=True)


if __name__ == "__main__":
    run()

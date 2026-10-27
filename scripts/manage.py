"""Local-only lifecycle, build, verification, and non-destructive backups."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
RUNTIME.mkdir(exist_ok=True)
os.chdir(ROOT)
os.environ.setdefault("MPLCONFIGDIR", str(RUNTIME / "matplotlib"))
os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")


def command(args, **kwargs):
    subprocess.run(args, check=True, cwd=ROOT, **kwargs)


def pnpm(*args, environment=None):
    supplied_env = environment if environment is not None else os.environ
    nodes = sorted((ROOT / ".tools").glob("node-v24*-win-x64"))
    local = ROOT / ".tools" / "node_modules" / "pnpm" / "bin" / "pnpm.cjs"
    if nodes and local.exists():
        env = {**supplied_env, "PATH": str(nodes[-1]) + os.pathsep + supplied_env["PATH"]}
        subprocess.run([str(nodes[-1] / "node.exe"), str(local), *args], cwd=ROOT / "frontend", check=True, env=env)
    else:
        executable = shutil.which("pnpm") or shutil.which("pnpm.cmd")
        if not executable:
            raise SystemExit("Install Node 24 LTS and pnpm 10.28.2, or run scripts/bootstrap.ps1.")
        subprocess.run([executable, *args], cwd=ROOT / "frontend", check=True, env=dict(supplied_env))


def start():
    command([sys.executable, "scripts/migrate.py"])
    pidfile = RUNTIME / "server.json"
    if pidfile.exists():
        import psutil
        stored = json.loads(pidfile.read_text())
        if psutil.pid_exists(stored["pid"]) and psutil.Process(stored["pid"]).create_time() == stored["created"]:
            print("AiTrader already running at http://127.0.0.1:8000")
            return
    if not (ROOT / "frontend/dist/index.html").exists():
        pnpm("build")
    with (RUNTIME / "server.stdout.log").open("ab") as stdout, (RUNTIME / "server.stderr.log").open("ab") as stderr:
        process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8000"], cwd=ROOT, stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0, start_new_session=os.name != "nt")
    import psutil
    pidfile.write_text(json.dumps({"pid": process.pid, "created": psutil.Process(process.pid).create_time()}))
    for _ in range(100):
        if process.poll() is not None:
            raise SystemExit("Server exited. Inspect .runtime/server.stderr.log.")
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/health", timeout=1) as response:
                if response.status == 200:
                    print("AiTrader ready at http://127.0.0.1:8000")
                    return
        except OSError:
            time.sleep(.2)
    raise SystemExit("Readiness timed out. Inspect .runtime/server.stderr.log.")


def stop():
    import psutil
    path = RUNTIME / "server.json"
    if not path.exists():
        print("No managed server PID recorded."); return
    record = json.loads(path.read_text())
    if psutil.pid_exists(record["pid"]):
        p = psutil.Process(record["pid"])
        if p.create_time() != record["created"] or "app.main:app" not in p.cmdline():
            raise SystemExit("PID identity changed; refusing to stop an unrelated process.")
        p.terminate()
        p.wait(timeout=15)
    path.unlink()
    print("Stopped the managed AiTrader server.")


def backup(destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise SystemExit("Backup destination already exists; choose a new filename.")
    source = RUNTIME / "aitrader.db"
    with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as src, sqlite3.connect(destination) as dst:
        src.backup(dst)
    print(f"SQLite preview backup written: {destination}")


def restore(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file() or destination.exists():
        raise SystemExit("Restore requires an existing source and a NEW destination. It never overwrites a database.")
    with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as src, sqlite3.connect(destination) as dst:
        if src.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SystemExit("Source integrity check failed")
        src.backup(dst)
    print(f"Restored into separate database: {destination}. Review before changing DATABASE_URL.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "build", "test", "e2e", "migrate", "backup", "restore"])
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    if args.action == "start": start()
    elif args.action == "stop": stop()
    elif args.action == "build": pnpm("build")
    elif args.action == "test":
        command([sys.executable, "-m", "pytest", "--cov=app", "--cov-report=term-missing"])
        command([sys.executable, "scripts/export_openapi.py"])
        pnpm("exec", "openapi-typescript", "../artifacts/openapi.json", "-o", "src/client/schema.d.ts", "--check")
        pnpm("test")
        pnpm("build")
    elif args.action == "e2e": command([sys.executable, "scripts/e2e.py"])
    elif args.action == "migrate": command([sys.executable, "scripts/migrate.py"])
    elif args.action == "backup": backup(args.paths[0])
    elif args.action == "restore": restore(*args.paths)

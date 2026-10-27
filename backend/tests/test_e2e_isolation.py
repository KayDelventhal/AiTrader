import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

path = Path(__file__).resolve().parents[2] / "scripts" / "e2e.py"
spec = importlib.util.spec_from_file_location("e2e_launcher", path)
e2e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e2e)


def test_test_environment_cannot_target_user_database(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///user-important.db")
    monkeypatch.setenv("APP_MODE", "LIVE")
    monkeypatch.setenv("LIVE_ENABLED", "true")
    monkeypatch.setenv("AITRADER_ENV_FILE", "user.env")
    env = e2e.isolated_environment(tmp_path, "e2e-isolated")
    assert env["DATABASE_URL"] == f"sqlite:///{(tmp_path / 'acceptance.db').as_posix()}"
    assert env["AITRADER_ENV_FILE"] == ""
    assert env["APP_MODE"] == "DEMO" and env["LIVE_ENABLED"] == "false"
    assert env["EXTERNAL_REQUESTS_ENABLED"] == "false"
    assert env["LANGSMITH_TRACING"] == "false"
    assert env["RUNTIME_INSTANCE_ID"] == "e2e-isolated"


def test_readiness_refuses_an_unrelated_server(monkeypatch):
    monkeypatch.setattr(e2e.urllib.request, "urlopen", lambda *a, **k: io.StringIO(json.dumps({"instance_id": "local"})))
    with pytest.raises(RuntimeError, match="another process"):
        e2e.wait_ready(SimpleNamespace(poll=lambda: None), "http://127.0.0.1:12345", "e2e-test")


def test_readiness_detects_child_exit():
    with pytest.raises(RuntimeError, match="exited before readiness"):
        e2e.wait_ready(SimpleNamespace(poll=lambda: 1), "http://127.0.0.1:12345", "e2e-test")


def test_readiness_accepts_only_owned_instance(monkeypatch):
    monkeypatch.setattr(e2e.urllib.request, "urlopen", lambda *a, **k: io.StringIO(json.dumps({"instance_id": "e2e-test"})))
    e2e.wait_ready(SimpleNamespace(poll=lambda: None), "http://127.0.0.1:12345", "e2e-test")

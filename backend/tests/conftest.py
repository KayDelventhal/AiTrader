import pytest
from fastapi.testclient import TestClient
from app.db.models import Base
from app.db.session import make_engine
from app.main import create_app


@pytest.fixture
def app(tmp_path):
    engine = make_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Base.metadata.create_all(engine)
    app = create_app(engine)
    yield app
    engine.dispose()


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


def sign_in(client, user="owner"):
    response = client.post("/api/v1/auth/login", json={"username": user, "password": f"local-demo-{user}"})
    assert response.status_code == 200, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf"]
    return client


@pytest.fixture
def owner(client):
    return sign_in(client)

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / 'app'
sys.path.insert(0, str(APP_DIR))

from database import Base, engine
from main import app

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_and_login_flow():
    email = "asha.user@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "name": "Asha User",
            "email": email,
            "password": "supersecret123",
            "preferred_language": "English",
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["email"] == email

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "supersecret123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token

    me_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email

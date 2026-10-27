import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app import main as main_module
from app.main import app


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_login_and_authenticated_profile(client):
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
    assert "password_hash" not in register_response.json()

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "supersecret123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    profile_response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == email


def test_registration_validation_duplicate_and_invalid_login(client):
    invalid_response = client.post(
        "/auth/register",
        json={"name": "  ", "email": "bad@example.com", "password": "short"},
    )
    assert invalid_response.status_code == 422

    payload = {
        "name": "Asha User",
        "email": "asha.user@example.com",
        "password": "supersecret123",
    }
    assert client.post("/auth/register", json=payload).status_code == 200

    duplicate_response = client.post(
        "/auth/register",
        json={**payload, "email": "ASHA.USER@example.com"},
    )
    assert duplicate_response.status_code == 400

    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "incorrect-password"},
    )
    assert login_response.status_code == 401


@pytest.mark.parametrize(
    "origin",
    [
        f"http://{host}:{port}"
        for port in (5173, 5174, 5175, 5176)
        for host in ("localhost", "127.0.0.1")
    ],
)
@pytest.mark.parametrize(
    ("path", "payload", "expected_status"),
    [
        (
            "/auth/register",
            {"name": "", "email": "invalid", "password": "short"},
            422,
        ),
        (
            "/auth/login",
            {},
            422,
        ),
    ],
)
def test_auth_cors_preflight_and_request(client, origin, path, payload, expected_status):
    preflight = client.options(
        path,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == origin
    assert "POST" in preflight.headers["access-control-allow-methods"]

    response = client.post(path, headers={"Origin": origin}, json=payload)
    assert response.status_code == expected_status
    assert response.headers["access-control-allow-origin"] == origin


def test_assessment_chat_history_and_dashboard_contracts(client, monkeypatch):
    generation_calls = []

    monkeypatch.setattr(
        main_module,
        "detect_emotion",
        lambda _text: [{"label": "calm", "score": 0.91}],
    )
    monkeypatch.setattr(
        main_module,
        "detect_emergency",
        lambda _text: {
            "risk_signal": "no_crisis_signal",
            "confidence": 0.99,
            "detection_source": "test",
        },
    )
    monkeypatch.setattr(main_module, "retrieve_relevant_memories", lambda **_kwargs: [])
    monkeypatch.setattr(main_module, "store_message_embedding", lambda **_kwargs: None)

    def fake_generate_response(**kwargs):
        generation_calls.append(kwargs)
        return (
            "Thank you for sharing. What would feel helpful now?",
            "test",
        )

    monkeypatch.setattr(
        main_module,
        "generate_response",
        fake_generate_response,
    )

    registration = client.post(
        "/auth/register",
        json={
            "name": "ASHA Test",
            "email": "asha.flow@example.com",
            "password": "supersecret123",
            "preferred_language": "Tamil",
        },
    )
    assert registration.status_code == 200
    login = client.post(
        "/auth/login",
        json={
            "email": "asha.flow@example.com",
            "password": "supersecret123",
        },
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assessment = client.post(
        "/assessments",
        headers=headers,
        json={
            "assessment_type": "initial",
            "score": 2,
            "answers": {"mood": "Okay", "sleep": "Well"},
        },
    )
    assert assessment.status_code == 200
    assert assessment.json()["answers"] == {"mood": "Okay", "sleep": "Well"}
    assert client.get("/assessments", headers=headers).json()[0]["answers"] == {
        "mood": "Okay",
        "sleep": "Well",
    }

    conversation = client.post("/conversations", headers=headers, json={})
    assert conversation.status_code == 200
    conversation_id = conversation.json()["id"]
    chat = client.post(
        "/chat",
        headers=headers,
        json={
            "conversation_id": conversation_id,
            "content": "I feel calm and would like to reflect.",
        },
    )
    assert chat.status_code == 200
    assert chat.json()["assistant_message"]["content"].startswith("Thank you")
    assert chat.json()["response_mode"] == "test"
    assert chat.json()["emotion"] == "calm"
    assert chat.json()["emergency"]["risk_signal"] == "no_crisis_signal"
    assert generation_calls[0]["conversation_history"] == []
    assert generation_calls[0]["preferred_language"] == "Tamil"

    messages = client.get(
        f"/conversations/{conversation_id}/messages",
        headers=headers,
    )
    assert messages.status_code == 200
    assert messages.json()[0]["emotion"] == {"label": "calm", "confidence": 0.91}
    assert messages.json()[0]["risk_signal"] == "no_crisis_signal"
    assert messages.json()[1]["sender"] == "assistant"

    dashboard = client.get("/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_conversations"] == 1
    assert dashboard.json()["total_messages"] == 2
    assert dashboard.json()["recent_emotions"] == ["calm"]

    monkeypatch.setattr(main_module, "detect_emotion", lambda _text: [])
    unavailable_emotion = client.post(
        "/chat",
        headers=headers,
        json={
            "conversation_id": conversation_id,
            "content": "A second reflective check-in.",
        },
    )
    assert unavailable_emotion.status_code == 200
    assert unavailable_emotion.json()["emotion"] is None
    latest_messages = client.get(
        f"/conversations/{conversation_id}/messages",
        headers=headers,
    ).json()
    assert latest_messages[2]["emotion"] is None

    follow_up = client.post(
        "/chat",
        headers=headers,
        json={
            "conversation_id": conversation_id,
            "content": "Could you explain how to start?",
        },
    )
    assert follow_up.status_code == 200
    assert generation_calls[-1]["conversation_history"] == [
        {
            "sender": "user",
            "content": "I feel calm and would like to reflect.",
        },
        {
            "sender": "assistant",
            "content": "Thank you for sharing. What would feel helpful now?",
        },
        {
            "sender": "user",
            "content": "A second reflective check-in.",
        },
        {
            "sender": "assistant",
            "content": "Thank you for sharing. What would feel helpful now?",
        },
    ]


def test_chat_fails_without_gemini_and_does_not_save_or_fake_reply(client, monkeypatch):
    from app.services import chat_service

    monkeypatch.setattr(chat_service, "GEMINI_API_KEY", "")
    monkeypatch.setattr(main_module, "detect_emotion", lambda _text: [])
    monkeypatch.setattr(
        main_module,
        "detect_emergency",
        lambda _text: {
            "risk_signal": "no_crisis_signal",
            "confidence": None,
            "detection_source": "test",
        },
    )
    monkeypatch.setattr(main_module, "retrieve_relevant_memories", lambda **_kwargs: [])
    monkeypatch.setattr(main_module, "store_message_embedding", lambda **_kwargs: None)
    monkeypatch.setattr(main_module, "generate_response", chat_service.generate_response)

    registration = client.post(
        "/auth/register",
        json={
            "name": "ASHA Missing Key",
            "email": "asha.missing-key@example.com",
            "password": "supersecret123",
        },
    )
    assert registration.status_code == 200
    login = client.post(
        "/auth/login",
        json={
            "email": "asha.missing-key@example.com",
            "password": "supersecret123",
        },
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    conversation = client.post("/conversations", headers=headers, json={})
    conversation_id = conversation.json()["id"]

    response = client.post(
        "/chat",
        headers=headers,
        json={
            "conversation_id": conversation_id,
            "content": "I would like to talk about a stressful day.",
        },
    )
    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]
    assert client.get(
        f"/conversations/{conversation_id}/messages",
        headers=headers,
    ).json() == []

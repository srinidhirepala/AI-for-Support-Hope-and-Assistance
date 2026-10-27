from types import SimpleNamespace

import pytest
from google.genai.errors import APIError

from app.services import chat_service


def test_empty_inherited_key_uses_backend_env_value(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text(
        "GEMINI_API_KEY=private-test-key\nGEMINI_MODEL=test-model\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(chat_service, "BACKEND_DIR", tmp_path)
    monkeypatch.setattr(chat_service, "BACKEND_ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(chat_service, "ROOT_ENV_FILE", tmp_path / "root.env")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_MODEL", "")

    assert chat_service._configured_setting("GEMINI_API_KEY") == "private-test-key"
    assert chat_service._configured_setting("GEMINI_MODEL", "default-model") == "test-model"


def test_nonempty_process_key_overrides_backend_env(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text(
        "GEMINI_API_KEY=file-test-key\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(chat_service, "BACKEND_DIR", tmp_path)
    monkeypatch.setattr(chat_service, "BACKEND_ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(chat_service, "ROOT_ENV_FILE", tmp_path / "root.env")
    monkeypatch.setenv("GEMINI_API_KEY", "process-test-key")

    assert chat_service._configured_setting("GEMINI_API_KEY") == "process-test-key"


def test_generate_response_sends_conversation_context_and_language(monkeypatch):
    request = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            request.update(kwargs)
            return SimpleNamespace(text="I can help you think that through.")

    class FakeClient:
        def __init__(self, **kwargs):
            request["client"] = kwargs
            self.models = FakeModels()

    monkeypatch.setattr(chat_service, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        chat_service,
        "genai",
        SimpleNamespace(Client=FakeClient),
    )

    response, mode = chat_service.generate_response(
        message="What should I try first?",
        conversation_history=[
            {"sender": "user", "content": "I feel overwhelmed by my workload."},
            {"sender": "assistant", "content": "Which part feels heaviest?"},
        ],
        preferred_language="Hindi",
    )

    assert response == "I can help you think that through."
    assert mode == "gemini"
    assert request["model"] == chat_service.MODEL_NAME
    assert [turn.role for turn in request["contents"]] == [
        "user",
        "model",
        "user",
    ]
    assert request["contents"][-1].parts[0].text == "What should I try first?"
    assert "Hindi" in request["config"].system_instruction
    assert request["client"]["api_key"] == "test-key"


def test_generate_response_requires_key_without_using_fallback(monkeypatch):
    monkeypatch.setattr(chat_service, "GEMINI_API_KEY", "")

    with pytest.raises(chat_service.ChatServiceError) as error:
        chat_service.generate_response("I feel overwhelmed.")

    assert error.value.status_code == 503
    assert "GEMINI_API_KEY" in error.value.message


@pytest.mark.parametrize(
    ("code", "provider_status", "expected_message", "expected_http_status"),
    [
        (403, "PERMISSION_DENIED", "authorization failed", 503),
        (429, "RESOURCE_EXHAUSTED", "rate limit or quota", 503),
        (404, "NOT_FOUND", "model is unavailable", 502),
        (504, "DEADLINE_EXCEEDED", "provider timed out", 504),
    ],
)
def test_generate_response_reports_provider_auth_and_quota_errors(
    monkeypatch,
    code,
    provider_status,
    expected_message,
    expected_http_status,
):
    api_error = APIError(
        code,
        {
            "error": {
                "code": code,
                "status": provider_status,
                "message": "sensitive provider detail should not reach the user",
            }
        },
    )

    class FakeModels:
        def generate_content(self, **_kwargs):
            raise api_error

    class FakeClient:
        def __init__(self, **_kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(chat_service, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        chat_service,
        "genai",
        SimpleNamespace(Client=FakeClient),
    )

    with pytest.raises(chat_service.ChatServiceError) as error:
        chat_service.generate_response("A safe test message.")

    assert error.value.status_code == expected_http_status
    assert expected_message in error.value.message
    assert f"HTTP {code}, {provider_status}" in error.value.message
    assert "sensitive provider detail" not in error.value.message


def test_provider_error_log_contains_status_without_provider_body_or_key(
    monkeypatch,
    caplog,
):
    api_error = APIError(
        504,
        {
            "error": {
                "code": 504,
                "status": "DEADLINE_EXCEEDED",
                "message": "provider response body must remain private",
            }
        },
    )

    class FakeModels:
        def generate_content(self, **_kwargs):
            raise api_error

    class FakeClient:
        def __init__(self, **_kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(chat_service, "GEMINI_API_KEY", "test-key-do-not-log")
    monkeypatch.setattr(
        chat_service,
        "genai",
        SimpleNamespace(Client=FakeClient),
    )

    with pytest.raises(chat_service.ChatServiceError):
        chat_service.generate_response("A safe test message.")

    assert "http_status=504 provider_status=DEADLINE_EXCEEDED" in caplog.text
    assert "provider response body" not in caplog.text
    assert "test-key-do-not-log" not in caplog.text


def test_generate_response_maps_timeout_to_gateway_timeout(monkeypatch):
    class FakeModels:
        def generate_content(self, **_kwargs):
            raise chat_service.httpx.ReadTimeout("timeout")

    class FakeClient:
        def __init__(self, **_kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(chat_service, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        chat_service,
        "genai",
        SimpleNamespace(Client=FakeClient),
    )

    with pytest.raises(chat_service.ChatServiceError) as error:
        chat_service.generate_response("A safe test message.")

    assert error.value.status_code == 504
    assert "too long to respond" in error.value.message


def test_generate_response_reports_provider_network_failure(monkeypatch):
    class FakeModels:
        def generate_content(self, **_kwargs):
            raise chat_service.httpx.ConnectError("private network detail")

    class FakeClient:
        def __init__(self, **_kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(chat_service, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        chat_service,
        "genai",
        SimpleNamespace(Client=FakeClient),
    )

    with pytest.raises(chat_service.ChatServiceError) as error:
        chat_service.generate_response("A safe test message.")

    assert error.value.status_code == 502
    assert "could not connect to Gemini" in error.value.message
    assert "private network detail" not in error.value.message

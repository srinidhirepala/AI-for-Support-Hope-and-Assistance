import logging
import os
import re
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values, load_dotenv

try:
    from google import genai
    from google.genai import errors as genai_errors
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_errors = None
    genai_types = None

BACKEND_DIR = Path(__file__).resolve().parents[2]
BACKEND_ENV_FILE = BACKEND_DIR / ".env"
ROOT_ENV_FILE = BACKEND_DIR.parent / ".env"
load_dotenv(BACKEND_ENV_FILE)
load_dotenv(ROOT_ENV_FILE)


def _configured_setting(name: str, default: str = "") -> str:
    environment_value = os.getenv(name, "").strip()
    if environment_value:
        return environment_value

    for env_file in (BACKEND_ENV_FILE, ROOT_ENV_FILE):
        file_value = dotenv_values(env_file).get(name)
        if isinstance(file_value, str) and file_value.strip():
            return file_value.strip()

    return default


GEMINI_API_KEY = _configured_setting("GEMINI_API_KEY")
MODEL_NAME = _configured_setting("GEMINI_MODEL", "gemini-3.6-flash")
logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTIONS = """
You are ASHA, a supportive AI for reflective well-being conversations.
Respond warmly, respectfully, and naturally to what the user actually said.
Use the conversation history to understand follow-ups; do not repeat generic
advice or assume facts the user has not shared. Ask a gentle, relevant question
when more context would help. Keep wording clear and reasonably concise.
The user is communicating in {language}; respond in that language when supported.

You are not a therapist, doctor, or diagnostic service. Do not diagnose, recommend
medication, claim certainty about emotions, or replace professional care. If the
user appears to be in immediate danger, encourage contacting local emergency
services and a trusted person.
"""


class ChatServiceError(Exception):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _conversation_contents(
    conversation_history: list[dict[str, str]],
    message: str,
) -> list[Any]:
    contents = []
    for turn in conversation_history:
        role = "model" if turn.get("sender") == "assistant" else "user"
        text = turn.get("content", "").strip()
        if text:
            contents.append(
                genai_types.Content(
                    role=role,
                    parts=[genai_types.Part(text=text)],
                )
            )

    contents.append(
        genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message)],
        )
    )
    return contents


def _provider_error(error: Exception) -> ChatServiceError:
    if genai_errors is not None and isinstance(error, genai_errors.APIError):
        provider_status = re.sub(
            r"[^A-Z0-9_]",
            "",
            str(error.status or "UNKNOWN").upper(),
        ) or "UNKNOWN"
        status_detail = f"HTTP {error.code}, {provider_status}"

        if error.code in (401, 403):
            return ChatServiceError(
                f"Gemini API authorization failed ({status_detail}). Check that the "
                "key is valid and Gemini API access is enabled for its project.",
                status_code=503,
            )
        if error.code == 429:
            return ChatServiceError(
                f"Gemini rate limit or quota was reached ({status_detail}). Check "
                "the project's quota and try again later.",
                status_code=503,
            )
        if error.code == 404:
            return ChatServiceError(
                f"The configured Gemini model is unavailable to this project "
                f"({status_detail}). Check GEMINI_MODEL in backend\\.env.",
                status_code=502,
            )
        if error.code in (408, 504):
            return ChatServiceError(
                f"Gemini's provider timed out ({status_detail}). The request reached "
                "Google's API but did not finish; try again later.",
                status_code=504,
            )
        if error.code >= 500:
            return ChatServiceError(
                f"Gemini returned a provider server error ({status_detail}). "
                "Please try again later.",
                status_code=502,
            )
        return ChatServiceError(
            f"Gemini rejected the request ({status_detail}). Check the configured "
            "model and request settings.",
            status_code=502,
        )

    if isinstance(error, (TimeoutError, httpx.TimeoutException)):
        return ChatServiceError(
            "Gemini took too long to respond. Please try again.",
            status_code=504,
        )

    if isinstance(error, httpx.NetworkError):
        return ChatServiceError(
            "ASHA could not connect to Gemini. Check the backend's network access and try again.",
            status_code=502,
        )

    return ChatServiceError(
        "ASHA could not get a response from Gemini. Please try again shortly.",
        status_code=502,
    )


def generate_response(
    message: str,
    emotion: str | None = None,
    relevant_memories: list | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    preferred_language: str = "English",
) -> tuple[str, str]:
    if not GEMINI_API_KEY:
        raise ChatServiceError(
            "AI chat is not configured. Add GEMINI_API_KEY to backend\\.env and restart the backend."
        )
    if genai is None or genai_types is None:
        raise ChatServiceError(
            "The Gemini SDK is unavailable. Install backend requirements and restart the backend."
        )

    system_instructions = SYSTEM_INSTRUCTIONS.format(
        language=preferred_language or "English"
    )
    context_notes = []
    if emotion:
        context_notes.append(
            f"A language signal estimated from the latest user message is {emotion}; "
            "treat it as uncertain and never as a diagnosis."
        )
    for memory in relevant_memories or []:
        content = memory.get("content") if isinstance(memory, dict) else None
        if content:
            context_notes.append(f"Relevant earlier reflection: {content}")
    if context_notes:
        system_instructions += "\n\nPrivate context for this response:\n" + "\n".join(
            context_notes
        )

    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=genai_types.HttpOptions(
                timeout=30_000,
                retry_options=genai_types.HttpRetryOptions(attempts=3),
            ),
        )
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=_conversation_contents(conversation_history or [], message),
            config=genai_types.GenerateContentConfig(
                system_instruction=system_instructions,
                temperature=0.7,
            ),
        )
    except Exception as error:
        provider_error = _provider_error(error)
        if genai_errors is not None and isinstance(error, genai_errors.APIError):
            provider_status = re.sub(
                r"[^A-Z0-9_]",
                "",
                str(error.status or "UNKNOWN").upper(),
            ) or "UNKNOWN"
            logger.warning(
                "Gemini API request failed (http_status=%s provider_status=%s)",
                error.code,
                provider_status,
            )
        else:
            logger.warning("Gemini request failed (%s)", type(error).__name__)
        raise provider_error from error

    response_text = response.text.strip() if response and response.text else ""
    if not response_text:
        raise ChatServiceError(
            "Gemini returned an empty response. Please try sending your message again.",
            status_code=502,
        )
    return response_text, "gemini"

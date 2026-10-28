from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    preferred_language: str = Field(default="English", max_length=50)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be no more than 72 UTF-8 bytes")
        return value


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    preferred_language: str | None = Field(default=None, max_length=50)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    preferred_language: str

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be no more than 72 UTF-8 bytes")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=100)


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    started_at: str | None = None
    title: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    conversation_id: int
    content: str = Field(min_length=1, max_length=10000)
    sender: str = "user"

    @field_validator("content")
    @classmethod
    def trim_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must not be blank")
        return value


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class AssessmentCreate(BaseModel):
    assessment_type: str = Field(default="initial", min_length=1, max_length=50)
    score: float | None = None
    answers: dict[str, Any] = Field(default_factory=dict)


class AssessmentResponse(BaseModel):
    id: int
    user_id: int
    assessment_type: str
    score: float | None
    answers: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    total_conversations: int
    total_messages: int
    latest_assessment: float | None
    recent_emotions: list[str]
    latest_risk_level: str | None


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    source_language: str = Field(default="English", min_length=1, max_length=50)
    target_language: str = Field(min_length=1, max_length=50)


class TranslationResponse(BaseModel):
    translated_text: str
    provider: str
    source_language: str
    target_language: str

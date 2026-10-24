from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    preferred_language: str = "English"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    preferred_language: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    preferred_language: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    started_at: Optional[str] = None
    title: Optional[str] = None

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    conversation_id: int
    content: str
    sender: str = "user"


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender: str
    content: str

    class Config:
        from_attributes = True


class AssessmentCreate(BaseModel):
    assessment_type: str = "initial"
    score: Optional[float] = None
    answers: Dict[str, Any] = {}


class AssessmentResponse(BaseModel):
    id: int
    user_id: int
    assessment_type: str
    score: Optional[float]
    answers: Dict[str, Any]

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    total_conversations: int
    total_messages: int
    latest_assessment: Optional[float]
    recent_emotions: List[str]
    latest_risk_level: Optional[str]

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    preferred_language: str = "English"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    preferred_language: str

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    user_id: int


class ConversationResponse(BaseModel):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    conversation_id: int
    sender: str
    content: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender: str
    content: str

    class Config:
        from_attributes = True
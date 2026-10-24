import os
from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Conversation,
    EmotionResult,
    Message,
    MessageEmbedding,
    RiskAssessment,
    SelfAssessment,
    User,
)
from schemas import (
    AssessmentCreate,
    AssessmentResponse,
    ConversationCreate,
    ConversationResponse,
    DashboardSummary,
    LoginRequest,
    MessageCreate,
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from services.chat_service import generate_response
from ml.emotion.emotion_detector import detect_emotion
from ml.emergency.emergency_detector import detect_emergency
from ml.memory.memory_service import (
    retrieve_relevant_memories,
    store_message_embedding,
)

app = FastAPI(
    title="ASHA",
    description="AI-powered mental well-being assistive chatbot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "asha-dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


@app.get("/")
def root():
    return {"message": "Welcome to ASHA", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/auth/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        name=user.name,
        email=str(user.email),
        password_hash=get_password_hash(user.password),
        preferred_language=user.preferred_language,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=TokenResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@app.get("/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.patch("/users/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.name:
        current_user.name = payload.name
    if payload.preferred_language:
        current_user.preferred_language = payload.preferred_language
    db.commit()
    db.refresh(current_user)
    return current_user


@app.get("/conversations")
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.started_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "title": f"Conversation {c.id}",
        }
        for c in conversations
    ]


@app.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = Conversation(user_id=current_user.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        started_at=conversation.started_at.isoformat() if conversation.started_at else None,
        title=payload.title or f"Conversation {conversation.id}",
    )


@app.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    return [
        {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "sender": message.sender,
            "content": message.content,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
        }
        for message in messages
    ]


@app.post("/messages", response_model=MessageResponse)
def create_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == message.conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    new_message = Message(
        conversation_id=message.conversation_id,
        sender=message.sender,
        content=message.content,
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


@app.post("/chat")
def chat(
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == payload.conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    user_message = Message(
        conversation_id=payload.conversation_id,
        sender="user",
        content=payload.content,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    emotion_result = detect_emotion(payload.content)
    top_emotion = emotion_result[0]
    emotion = top_emotion["label"]
    emotion_confidence = float(top_emotion["score"])

    db.add(
        EmotionResult(
            message_id=user_message.id,
            emotion=emotion,
            confidence=emotion_confidence,
        )
    )

    emergency_result = detect_emergency(payload.content)
    risk_signal = emergency_result["risk_signal"]
    risk_confidence = float(emergency_result["confidence"])
    detection_source = emergency_result.get("detection_source")

    db.add(
        RiskAssessment(
            message_id=user_message.id,
            risk_level=risk_signal,
            confidence=risk_confidence,
        )
    )

    relevant_memories = []
    if risk_signal != "potential_crisis":
        relevant_memories = retrieve_relevant_memories(
            db=db,
            user_id=current_user.id,
            query_text=payload.content,
            top_k=5,
            max_distance=0.5,
        )

    if risk_signal == "potential_crisis":
        response_text = (
            "I'm really sorry you're going through something difficult. You do not have to face it alone. "
            "Please reach out to someone you trust, a qualified mental health professional, or a local emergency service if you feel unsafe. "
            "In India, emergency assistance is available via 112 and Tele-MANAS is 14416. Please verify current availability if needed."
        )
    else:
        response_text = generate_response(
            message=payload.content,
            emotion=emotion,
            relevant_memories=relevant_memories,
        )

    store_message_embedding(
        db=db,
        message_id=user_message.id,
        user_id=current_user.id,
        text=payload.content,
    )

    assistant_message = Message(
        conversation_id=payload.conversation_id,
        sender="assistant",
        content=response_text,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return {
        "user_message": {
            "id": user_message.id,
            "conversation_id": user_message.conversation_id,
            "sender": user_message.sender,
            "content": user_message.content,
        },
        "emotion": emotion,
        "emotion_confidence": emotion_confidence,
        "emergency": {
            "risk_signal": risk_signal,
            "confidence": risk_confidence,
            "detection_source": detection_source,
        },
        "relevant_memories": relevant_memories,
        "assistant_message": {
            "id": assistant_message.id,
            "conversation_id": assistant_message.conversation_id,
            "sender": assistant_message.sender,
            "content": assistant_message.content,
        },
    }


@app.post("/assessments", response_model=AssessmentResponse)
def create_assessment(
    payload: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessment = SelfAssessment(
        user_id=current_user.id,
        assessment_type=payload.assessment_type,
        answers=str(payload.answers),
        score=payload.score,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return AssessmentResponse(
        id=assessment.id,
        user_id=assessment.user_id,
        assessment_type=assessment.assessment_type,
        score=assessment.score,
        answers=payload.answers,
    )


@app.get("/assessments", response_model=list[AssessmentResponse])
def list_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessments = (
        db.query(SelfAssessment)
        .filter(SelfAssessment.user_id == current_user.id)
        .order_by(SelfAssessment.created_at.desc())
        .all()
    )
    response = []
    for record in assessments:
        response.append(
            AssessmentResponse(
                id=record.id,
                user_id=record.user_id,
                assessment_type=record.assessment_type,
                score=record.score,
                answers={"raw": record.answers} if record.answers else {},
            )
        )
    return response


@app.get("/dashboard", response_model=DashboardSummary)
def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total_conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    total_messages = (
        db.query(Message)
        .join(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .count()
    )
    latest_assessment = (
        db.query(SelfAssessment.score)
        .filter(SelfAssessment.user_id == current_user.id)
        .order_by(SelfAssessment.created_at.desc())
        .first()
    )
    recent_emotions = (
        db.query(EmotionResult.emotion)
        .join(Message)
        .join(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(EmotionResult.created_at.desc())
        .limit(8)
        .all()
    )
    latest_risk_level = (
        db.query(RiskAssessment.risk_level)
        .join(Message)
        .join(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(RiskAssessment.created_at.desc())
        .first()
    )
    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "latest_assessment": latest_assessment[0] if latest_assessment else None,
        "recent_emotions": [emotion[0] for emotion in recent_emotions],
        "latest_risk_level": latest_risk_level[0] if latest_risk_level else None,
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

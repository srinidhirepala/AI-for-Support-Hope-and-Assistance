from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database import get_db

from models import (
    User,
    Conversation,
    Message,
    EmotionResult,
    RiskAssessment,
)

from schemas import (
    UserCreate,
    UserResponse,
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)

from services.chat_service import generate_response
from ml.emotion.emotion_detector import detect_emotion
from ml.emergency.emergency_detector import detect_emergency


app = FastAPI(
    title="ASHA",
    description="AI-powered mental well-being assistive chatbot",
    version="1.0.0",
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Welcome to ASHA",
        "status": "running",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ============================================================
# CREATE USER
# ============================================================

@app.post("/users", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    new_user = User(
        name=user.name,
        email=user.email,
        preferred_language=user.preferred_language,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ============================================================
# CREATE CONVERSATION
# ============================================================

@app.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.id == conversation.user_id)
        .first()
    )

    if not user:
        return {"error": "User not found"}

    new_conversation = Conversation(
        user_id=conversation.user_id
    )

    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)

    return new_conversation


# ============================================================
# CREATE MESSAGE
# ============================================================

@app.post("/messages", response_model=MessageResponse)
def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == message.conversation_id)
        .first()
    )

    if not conversation:
        return {"error": "Conversation not found"}

    new_message = Message(
        conversation_id=message.conversation_id,
        sender=message.sender,
        content=message.content,
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return new_message


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
def chat(
    message: MessageCreate,
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # Check conversation
    # --------------------------------------------------------

    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == message.conversation_id)
        .first()
    )

    if not conversation:
        return {
            "error": "Conversation not found"
        }

    # --------------------------------------------------------
    # 1. Save user's message
    # --------------------------------------------------------

    user_message = Message(
        conversation_id=message.conversation_id,
        sender="user",
        content=message.content,
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # --------------------------------------------------------
    # 2. Detect emotion
    # --------------------------------------------------------

    emotion_results = detect_emotion(message.content)

    top_emotion = emotion_results[0]

    emotion = top_emotion["label"]
    emotion_confidence = top_emotion["score"]

    # --------------------------------------------------------
    # 3. Save emotion result
    # --------------------------------------------------------

    emotion_result = EmotionResult(
        message_id=user_message.id,
        emotion=emotion,
        confidence=emotion_confidence,
    )

    db.add(emotion_result)
    db.commit()
    db.refresh(emotion_result)

    # --------------------------------------------------------
    # 4. Detect potential crisis
    # --------------------------------------------------------

    emergency_result = detect_emergency(message.content)

    risk_signal = emergency_result["risk_signal"]
    risk_confidence = emergency_result["confidence"]

    # --------------------------------------------------------
    # 5. Save emergency-risk assessment
    # --------------------------------------------------------

    risk_assessment = RiskAssessment(
        message_id=user_message.id,
        risk_level=risk_signal,
        confidence=risk_confidence,
    )

    db.add(risk_assessment)
    db.commit()
    db.refresh(risk_assessment)

    # --------------------------------------------------------
    # 6. Generate response
    # --------------------------------------------------------

    if risk_signal == "potential_crisis":

        response_text = (
            "I'm really sorry you're going through something this "
            "difficult. You don't have to handle this alone. "
            "Please consider reaching out to someone you trust or "
            "a qualified mental health professional. "
            "If you feel you may be in immediate danger or might "
            "act on these thoughts, please contact your local "
            "emergency service or go to the nearest emergency "
            "department."
        )

    else:

        response_text = generate_response(
            message.content
        )

    # --------------------------------------------------------
    # 7. Save ASHA's response
    # --------------------------------------------------------

    assistant_message = Message(
        conversation_id=message.conversation_id,
        sender="assistant",
        content=response_text,
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    # --------------------------------------------------------
    # 8. Return complete response
    # --------------------------------------------------------

    return {
        "user_message": {
            "id": user_message.id,
            "conversation_id": user_message.conversation_id,
            "sender": user_message.sender,
            "content": user_message.content,
            "timestamp": user_message.timestamp,
        },

        "emotion": emotion,
        "emotion_confidence": emotion_confidence,

        "emergency": {
            "risk_signal": risk_signal,
            "confidence": risk_confidence,
        },

        "assistant_message": {
            "id": assistant_message.id,
            "conversation_id": assistant_message.conversation_id,
            "sender": assistant_message.sender,
            "content": assistant_message.content,
            "timestamp": assistant_message.timestamp,
        },
    }
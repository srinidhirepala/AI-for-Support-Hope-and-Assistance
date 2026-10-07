from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    preferred_language = Column(String(50), default="English")
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False,
    )
    sender = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )

    emotion = relationship(
        "EmotionResult",
        back_populates="message",
        uselist=False,
        cascade="all, delete-orphan",
    )

    risk_assessment = relationship(
        "RiskAssessment",
        back_populates="message",
        uselist=False,
        cascade="all, delete-orphan",
    )


class EmotionResult(Base):
    __tablename__ = "emotion_results"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(
        Integer,
        ForeignKey("messages.id"),
        nullable=False,
    )
    emotion = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship(
        "Message",
        back_populates="emotion",
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(
        Integer,
        ForeignKey("messages.id"),
        nullable=False,
    )
    risk_level = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship(
        "Message",
        back_populates="risk_assessment",
    )


class SelfAssessment(Base):
    __tablename__ = "self_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_type = Column(String(50), nullable=False)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
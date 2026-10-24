from database import Base, engine
from models import (
    User,
    Conversation,
    Message,
    EmotionResult,
    RiskAssessment,
    SelfAssessment,
    MessageEmbedding,
)


print("Creating ASHA database tables...")

Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully!")
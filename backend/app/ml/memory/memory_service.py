import json

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
from sqlalchemy.orm import Session

from models import MessageEmbedding, Message


MODEL_NAME = "all-MiniLM-L6-v2"

embedding_model = SentenceTransformer(MODEL_NAME) if SentenceTransformer is not None else None


def generate_embedding(text: str) -> list[float]:
    """Convert text into a 384-dimensional semantic embedding."""
    if embedding_model is None:
        return [0.0] * 384
    embedding = embedding_model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.asarray(vec_a, dtype=float)
    b = np.asarray(vec_b, dtype=float)
    if a.size == 0 or b.size == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def store_message_embedding(
    db: Session,
    message_id: int,
    user_id: int,
    text: str,
):
    """Generate and store an embedding for a message."""
    embedding = generate_embedding(text)
    memory = MessageEmbedding(
        message_id=message_id,
        user_id=user_id,
        embedding=json.dumps(embedding),
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def retrieve_relevant_memories(
    db: Session,
    user_id: int,
    query_text: str,
    top_k: int = 5,
    max_distance: float = 0.5,
):
    """Retrieve semantically relevant previous user messages."""
    query_embedding = generate_embedding(query_text)

    records = (
        db.query(MessageEmbedding, Message)
        .join(Message, Message.id == MessageEmbedding.message_id)
        .filter(MessageEmbedding.user_id == user_id, Message.sender == "user")
        .all()
    )

    memories = []
    for embedding_record, message in records:
        try:
            stored_embedding = json.loads(embedding_record.embedding)
        except (TypeError, ValueError):
            continue

        similarity = _cosine_similarity(query_embedding, stored_embedding)
        distance = 1.0 - max(similarity, 0.0)
        if distance <= max_distance:
            memories.append(
                {
                    "message_id": message.id,
                    "content": message.content,
                    "sender": message.sender,
                    "distance": round(float(distance), 4),
                }
            )

    memories.sort(key=lambda item: item["distance"])
    return memories[:top_k]
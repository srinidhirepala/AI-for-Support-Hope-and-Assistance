from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from models import MessageEmbedding, Message


MODEL_NAME = "all-MiniLM-L6-v2"

embedding_model = SentenceTransformer(MODEL_NAME)


def generate_embedding(text: str) -> list[float]:
    """
    Convert text into a 384-dimensional semantic embedding.
    """

    embedding = embedding_model.encode(
        text,
        normalize_embeddings=True,
    )

    return embedding.tolist()


def store_message_embedding(
    db: Session,
    message_id: int,
    user_id: int,
    text: str,
):
    """
    Generate and store an embedding for a message.
    """

    embedding = generate_embedding(text)

    memory = MessageEmbedding(
        message_id=message_id,
        user_id=user_id,
        embedding=embedding,
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
    """
    Retrieve semantically relevant previous user messages.

    Only memories with cosine distance at or below
    max_distance are returned.
    """

    query_embedding = generate_embedding(query_text)

    distance_expression = MessageEmbedding.embedding.cosine_distance(
        query_embedding
    )

    results = (
        db.query(
            MessageEmbedding,
            Message,
            distance_expression.label("distance"),
        )
        .join(
            Message,
            Message.id == MessageEmbedding.message_id,
        )
        .filter(
            MessageEmbedding.user_id == user_id,
            Message.sender == "user",
        )
        .order_by(distance_expression)
        .limit(top_k)
        .all()
    )

    memories = []

    for embedding_record, message, distance in results:

        distance = float(distance)

        if distance > max_distance:
            continue

        memories.append(
            {
                "message_id": message.id,
                "content": message.content,
                "sender": message.sender,
                "distance": distance,
            }
        )

    return memories
import logging


try:
    from transformers import pipeline
except ImportError:
    pipeline = None


emotion_classifier = None
logger = logging.getLogger(__name__)

if pipeline is not None:
    try:
        emotion_classifier = pipeline(
            "text-classification",
            model="SamLowe/roberta-base-go_emotions",
            top_k=3,
        )
    except Exception as error:
        logger.warning("Emotion model unavailable (%s)", type(error).__name__)
        emotion_classifier = None
else:
    logger.warning("Emotion model unavailable because transformers is not installed")


def detect_emotion(text: str):
    """Detect the top emotions expressed in a piece of text."""
    if emotion_classifier is None:
        return []

    results = emotion_classifier(text)
    return results[0]
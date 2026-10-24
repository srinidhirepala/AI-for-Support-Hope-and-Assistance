try:
    from transformers import pipeline
except ImportError:
    pipeline = None


emotion_classifier = None

if pipeline is not None:
    try:
        emotion_classifier = pipeline(
            "text-classification",
            model="SamLowe/roberta-base-go_emotions",
            top_k=3,
        )
    except Exception:
        emotion_classifier = None


def detect_emotion(text: str):
    """Detect the top emotions expressed in a piece of text."""
    if emotion_classifier is None:
        return [{"label": "neutral", "score": 0.5}]

    results = emotion_classifier(text)
    return results[0]
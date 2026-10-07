from transformers import pipeline


# Load the emotion classification model once
emotion_classifier = pipeline(
    "text-classification",
    model="SamLowe/roberta-base-go_emotions",
    top_k=3,
)


def detect_emotion(text: str):
    """
    Detect the top emotions expressed in a piece of text.
    """

    results = emotion_classifier(text)

    return results[0]
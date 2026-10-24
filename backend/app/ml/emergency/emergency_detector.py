from pathlib import Path
import re

try:
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        pipeline,
    )
except ImportError:
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    pipeline = None


# ============================================================
# Load trained ASHA emergency detection model
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[4]
MODEL_DIR = (
    BASE_DIR
    / "models"
    / "emergency"
    / "distilroberta_emergency"
)


tokenizer = None
model = None
emergency_classifier = None

if AutoTokenizer is not None and AutoModelForSequenceClassification is not None and pipeline is not None:
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
        emergency_classifier = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            device=-1,
        )
    except Exception:
        tokenizer = None
        model = None
        emergency_classifier = None


# ============================================================
# Explicit high-risk language guardrail
# ============================================================

EXPLICIT_CRISIS_PATTERNS = [
    r"\bthinking about hurting myself\b",
    r"\bthinking of hurting myself\b",
    r"\bwant to hurt myself\b",
    r"\bwanna hurt myself\b",
    r"\bgoing to hurt myself\b",
    r"\bplanning to hurt myself\b",
    r"\bplan to hurt myself\b",
    r"\bhurt myself\b",
    r"\bharm myself\b",
    r"\bkill myself\b",
    r"\bwant to die\b",
    r"\bgoing to die\b",
    r"\bend my life\b",
    r"\btake my own life\b",
    r"\bsuicidal\b",
]


def contains_explicit_crisis_language(text: str) -> bool:
    """
    Detect explicit self-harm or suicidal language.

    This is a safety guardrail, not a diagnosis.
    """

    normalized_text = text.lower().strip()

    for pattern in EXPLICIT_CRISIS_PATTERNS:
        if re.search(pattern, normalized_text):
            return True

    return False


# ============================================================
# Emergency detection
# ============================================================

def detect_emergency(text: str):
    """
    Detect a potential crisis signal.

    Combines:
    1. Explicit-risk safety guardrail
    2. Fine-tuned DistilRoBERTa classifier

    This is a risk signal, not a clinical diagnosis.
    """

    # --------------------------------------------------------
    # Safety guardrail
    # --------------------------------------------------------

    explicit_crisis = contains_explicit_crisis_language(text)

    # --------------------------------------------------------
    # ML classifier
    # --------------------------------------------------------

    if emergency_classifier is None:
        label = "NO_CRISIS"
        confidence = 0.5
    else:
        result = emergency_classifier(
            text,
            truncation=True,
            max_length=256,
        )[0]

        label = result["label"]
        confidence = result["score"]

    # --------------------------------------------------------
    # Final risk decision
    # --------------------------------------------------------

    if explicit_crisis:
        risk_signal = "potential_crisis"
        detection_source = "explicit_crisis_guardrail"

    elif label == "POTENTIAL_CRISIS":
        risk_signal = "potential_crisis"
        detection_source = "ml_classifier"

    else:
        risk_signal = "no_crisis_signal"
        detection_source = "ml_classifier"

    return {
        "label": label,
        "risk_signal": risk_signal,
        "confidence": confidence,
        "detection_source": detection_source,
    }
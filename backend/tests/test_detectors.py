from app.ml.emergency import emergency_detector
from app.ml.emotion import emotion_detector


def test_emotion_detector_returns_no_result_when_model_is_unavailable(monkeypatch):
    monkeypatch.setattr(emotion_detector, "emotion_classifier", None)

    assert emotion_detector.detect_emotion("A reflective check-in.") == []


def test_emergency_detector_reports_unavailable_model_and_keeps_guardrail(monkeypatch):
    monkeypatch.setattr(emergency_detector, "emergency_classifier", None)

    ordinary_result = emergency_detector.detect_emergency("A reflective check-in.")
    assert ordinary_result["classifier_available"] is False
    assert ordinary_result["detection_source"] == "explicit_guardrail_only"
    assert ordinary_result["confidence"] is None

    explicit_result = emergency_detector.detect_emergency(
        "I am thinking about hurting myself."
    )
    assert explicit_result["risk_signal"] == "potential_crisis"
    assert explicit_result["detection_source"] == "explicit_crisis_guardrail"
    assert explicit_result["confidence"] is None

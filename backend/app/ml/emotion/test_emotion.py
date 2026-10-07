from emotion_detector import detect_emotion


text = "I have been feeling really stressed and worried about everything."

results = detect_emotion(text)

print("\nDetected emotions:")

for result in results:
    print(
        f"{result['label']}: "
        f"{result['score']:.4f}"
    )
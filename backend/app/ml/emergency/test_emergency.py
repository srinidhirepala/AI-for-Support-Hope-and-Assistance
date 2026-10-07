from emergency_detector import detect_emergency

test_messages = [
    "I am having a difficult day and feel stressed.",
    "I feel hopeless and don't know what to do.",
    "I am thinking about hurting myself.",
]

for message in test_messages:
    print("\nMessage:", message)

    try:
        result = detect_emergency(message)
        print("Result:", result)
    except RuntimeError as error:
        print("Model not configured:", error)
def generate_response(message: str) -> str:
    message = message.lower()

    if "hello" in message or "hi" in message:
        return "Hello! I'm ASHA. I'm here to listen and support you. How are you feeling today?"

    if "stress" in message or "stressed" in message:
        return "It sounds like you're dealing with some stress. Would you like to talk about what's been making things difficult?"

    if "sad" in message or "lonely" in message:
        return "I'm sorry you're having a difficult time. You can share what's been bothering you with me if you'd like."

    return "I'm here to listen. Tell me a little more about what you're experiencing."
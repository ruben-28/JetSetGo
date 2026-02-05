
def analyze(message):
    message_lower = message.lower()
    intent = "general"
    if any(word in message_lower for word in ["idée", "idees", "inspiration", "suggest", "recommand", "conseil", "propose"]):
        intent = "inspiration"
    elif any(word in message_lower for word in ["vol", "flight", "avion", "fly", "voler"]):
        intent = "flight_search"
    
    print(f"Message: {message}")
    print(f"Intent: {intent}")
    print(f"'conseil' in message_lower: {'conseil' in message_lower}")

analyze("je veux savoir si cest conseille de partir en iran")

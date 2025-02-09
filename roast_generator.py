import random

# Roast templates
ROAST_TEMPLATES = [
    "Lux's performance looking like my dating life - all downhill! 📉",
    "Lux is lower than my standards on Tinder! 🔍",
    "Lux is redder than my face after explaining crypto to my parents! 😅",
    "Lux is messier than my room during finals week! 🗑️",
    "Lux dropping faster than my New Year's resolutions! 🎆",
    "Lux performing worse than my Monday motivation! 📊",
    "Lux wobblier than me after leg day! 💪",
    "Lux has more dips than a nachos party gone wrong! 🌮",
    "Lux making my bank account look good! 💸",
    "Lux flatlining harder than my caffeine crash! ☕"
]

def generate_roast():
    """Generate a random roast."""
    return random.choice(ROAST_TEMPLATES)
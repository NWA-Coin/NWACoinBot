import os
import random
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Fallback roasts in case API fails
FALLBACK_ROASTS = [
    "Lux's chart looking like my dating life - all downhill! 📉",
    "Lux dropping faster than my New Year's resolutions! 🎆",
    "Lux has more dips than a nachos party gone wrong! 🌮",
    "Lux making my bank account look good! 💸",
]

def generate_roast():
    """Generate a creative roast about Lux coin using OpenAI."""
    try:
        # Get current price trend from price_chart.py
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "system",
                    "content": "You are a witty roast generator for cryptocurrency. Create a funny, lighthearted roast about the Lux cryptocurrency. Keep it under 100 characters. Include an appropriate emoji."
                },
                {
                    "role": "user",
                    "content": "Generate a creative roast about Lux coin."
                }
            ],
            max_tokens=50,
            temperature=0.9
        )

        roast = response.choices[0].message.content.strip()
        print(f"Generated roast: {roast}")
        return roast
    except Exception as e:
        print(f"Error generating roast: {str(e)}")
        return random.choice(FALLBACK_ROASTS)
import random
from PIL import Image, ImageDraw, ImageFont
import io
import os

# Predefined roast templates
ROAST_TEMPLATES = [
    "Lux coin is so slow, Internet Explorer feels fast in comparison! 🐌",
    "Lux's market cap is like my dating life - constantly disappointing! 📉",
    "Lux coin is more unstable than my coffee addiction before morning meetings! ☕",
    "Lux's blockchain is like a maze - even the developers got lost in it! 🌀",
    "Lux coin has more forks than a restaurant supply store! 🍴",
    "Lux's white paper has more plot twists than a soap opera! 📺",
    "Lux coin is so volatile, roller coasters look stable! 🎢",
    "Investing in Lux is like trying to catch falling knives... blindfolded! 🔪",
    "Lux's roadmap is more mysterious than Area 51! 👽",
    "Lux coin has more red flags than a flag factory during Valentine's Day! ❤️"
]

def generate_roast():
    """Generate a random roast from predefined templates."""
    return random.choice(ROAST_TEMPLATES)

def create_meme_image(text):
    """Create a simple meme image with the given text."""
    # Create a new image with a gradient background
    width = 800
    height = 600
    image = Image.new('RGB', (width, height), color='black')
    draw = ImageDraw.Draw(image)
    
    # Create gradient background
    for y in range(height):
        r = int((y / height) * 100)
        g = int((y / height) * 50)
        b = int((y / height) * 150)
        for x in range(width):
            draw.point((x, y), fill=(r, g, b))
    
    # Add crypto-related symbols
    symbols = "₿ Ξ ₮ 💎 🚀 📈 💰"
    font = ImageFont.load_default()
    
    # Draw random symbols
    for _ in range(10):
        symbol = random.choice(symbols)
        x = random.randint(0, width-50)
        y = random.randint(0, height-100)
        draw.text((x, y), symbol, fill='white', font=font)
    
    # Add the roast text
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        if len(test_line) * 10 > width - 40:  # Approximate width
            if current_line:
                lines.append(' '.join(current_line[:-1]))
                current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw text
    y = height - 150
    for line in lines:
        x = (width - len(line) * 10) // 2  # Center text
        # Draw text outline
        for dx in [-1, 1]:
            for dy in [-1, 1]:
                draw.text((x + dx, y + dy), line, font=font, fill='black')
        draw.text((x, y), line, font=font, fill='white')
        y += 30
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

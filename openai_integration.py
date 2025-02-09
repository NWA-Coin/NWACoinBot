import os
import base64
import io
import json
import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found in environment variables!")

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_roast():
    """Generate a creative roast about Lux coin."""
    try:
        print("Starting roast generation...") # Debug log
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are a witty crypto critic. Generate a funny, creative roast about the Lux coin. 
                    Keep it playful and humorous, not mean-spirited. 
                    You must respond with a JSON object containing exactly one field named 'roast' with your roast as the value.
                    Example format: {"roast": "your roast text here"}"""
                },
                {
                    "role": "user",
                    "content": "Generate a funny roast about Lux coin"
                }
            ],
            response_format={"type": "json_object"}
        )

        print(f"OpenAI Response Content: {response.choices[0].message.content}")  # Debug content

        try:
            json_response = json.loads(response.choices[0].message.content)
            if 'roast' not in json_response:
                raise ValueError("Response missing 'roast' field")
            return json_response['roast']  # Return just the roast text
        except json.JSONDecodeError as je:
            print(f"JSON Parse Error: {str(je)}")
            raise
    except Exception as e:
        print(f"Error in generate_roast: {str(e)}")
        raise Exception(f"Failed to generate roast: {e}")

def generate_meme_image(roast_text):
    """Generate a meme image using DALL-E."""
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"Create a funny meme-style image about cryptocurrency that would go well with this text: {roast_text}. Make it humorous and suitable for a meme format. No text in the image.",
            n=1,
            size="1024x1024"
        )

        if not response.data or not response.data[0].url:
            raise ValueError("No image URL in DALL-E response")

        return response.data[0].url
    except Exception as e:
        print(f"Error in generate_meme_image: {str(e)}")
        raise Exception(f"Failed to generate image: {e}")

def add_text_to_image(image_url, roast_text):
    """Add the roast text to the generated image."""
    try:
        # Download the image using requests
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download image: Status code {response.status_code}")

        img = Image.open(io.BytesIO(response.content))

        # Create a drawing object
        draw = ImageDraw.Draw(img)

        # Calculate text size and position
        width, height = img.size
        font_size = int(width * 0.05)  # Scale font size with image

        # Just use the default font - more reliable across systems
        font = ImageFont.load_default()

        # Calculate text width and wrap text if needed
        words = roast_text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            # For default font, approximate width calculation
            text_width = len(test_line) * (font_size * 0.6)  
            if text_width > width * 0.9:  # 90% of image width
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(test_line)
                    current_line = []

        if current_line:
            lines.append(' '.join(current_line))

        # Draw text with outline
        y = height * 0.85  # Start position
        outline_color = "black"
        text_color = "white"
        outline_width = 2

        for line in lines:
            # Center the text
            text_width = len(line) * (font_size * 0.6)
            x = (width - text_width) / 2

            # Draw outline
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    draw.text((x + dx, y + dy), line, font=font, fill=outline_color)

            # Draw text
            draw.text((x, y), line, font=font, fill=text_color)
            y += font_size * 1.2  # Move to next line

        # Save to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

    except Exception as e:
        print(f"Error in add_text_to_image: {str(e)}")
        raise Exception(f"Failed to add text to image: {e}")
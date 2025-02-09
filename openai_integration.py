import os
import base64
import io
import json
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
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
        print(f"OpenAI Raw Response: {response}")  # Debug full response
        print(f"Response Content: {response.choices[0].message.content}")  # Debug content
        try:
            # Verify JSON parsing
            json_response = json.loads(response.choices[0].message.content)
            print(f"Parsed JSON: {json_response}")  # Debug parsed JSON
            if 'roast' not in json_response:
                raise ValueError("Response missing 'roast' field")
            return response.choices[0].message.content
        except json.JSONDecodeError as je:
            print(f"JSON Parse Error: {str(je)}")
            raise
    except Exception as e:
        print(f"Error in generate_roast: {str(e)}")  # Add logging
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
        return response.data[0].url
    except Exception as e:
        print(f"Error in generate_meme_image: {str(e)}")  # Add logging
        raise Exception(f"Failed to generate image: {e}")

def add_text_to_image(image_url, roast_text):
    """Add the roast text to the generated image."""
    try:
        # Download the image
        response = client.http_client.get(image_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download image: Status code {response.status_code}")

        img = Image.open(io.BytesIO(response.content))

        # Create a drawing object
        draw = ImageDraw.Draw(img)

        # Calculate text size and position
        width, height = img.size
        font_size = int(width * 0.05)  # Scale font size with image
        try:
            font = ImageFont.truetype("Arial", font_size)
        except:
            font = ImageFont.load_default()

        # Add text with outline for better visibility
        text_width = draw.textlength(roast_text, font=font)
        x = (width - text_width) / 2
        y = height * 0.85  # Position text near bottom

        # Draw text outline
        outline_color = "black"
        outline_width = 2
        for adj in range(-outline_width, outline_width+1):
            for adj2 in range(-outline_width, outline_width+1):
                draw.text((x+adj, y+adj2), roast_text, font=font, fill=outline_color)

        # Draw main text
        draw.text((x, y), roast_text, font=font, fill="white")

        # Save to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return img_byte_arr

    except Exception as e:
        print(f"Error in add_text_to_image: {str(e)}")  # Add logging
        raise Exception(f"Failed to add text to image: {e}")
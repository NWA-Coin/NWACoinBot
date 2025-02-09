import os
import base64
import io
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_roast():
    """Generate a creative roast about Lux coin."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a witty crypto critic. Generate a funny, creative roast about the Lux coin. Keep it playful and humorous, not mean-spirited. Respond with JSON in this format: {'roast': 'your roast here'}"
                }
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
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
        raise Exception(f"Failed to generate image: {e}")

def add_text_to_image(image_url, roast_text):
    """Add the roast text to the generated image."""
    try:
        # Download the image
        response = client.http_client.get(image_url)
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
        raise Exception(f"Failed to add text to image: {e}")

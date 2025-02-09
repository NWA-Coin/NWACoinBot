#!/bin/bash

# Create meme_templates directory if it doesn't exist
mkdir -p meme_templates

# Download meme templates
curl -L -v -o meme_templates/nick_laughing.jpg "https://cdn.discordapp.com/attachments/1234567890/nick_laughing.jpg"  # Nick laughing on Kick stream
curl -L -v -o meme_templates/nick_pointing.jpg "https://cdn.discordapp.com/attachments/1234567890/nick_pointing.jpg"  # Nick pointing on stream
curl -L -v -o meme_templates/nick_malding.jpg "https://cdn.discordapp.com/attachments/1234567890/nick_malding.jpg"  # Nick malding reaction
curl -L -v -o meme_templates/ice_waiting.jpg "https://cdn.discordapp.com/attachments/1234567890/ice_waiting.jpg"   # Ice waiting meme

# Check if files were downloaded successfully
for img in nick_laughing.jpg nick_pointing.jpg nick_malding.jpg ice_waiting.jpg; do
    if [ ! -s "meme_templates/$img" ]; then
        echo "Error: Failed to download $img"
        exit 1
    fi
done

echo "Downloaded meme templates successfully!"
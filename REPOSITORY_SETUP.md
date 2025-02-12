# NWAcoinbot Repository Setup Guide

## Files to Include

Essential files for the repository:
```
├── bot.py                 # Main Discord bot file
├── create_templates.py    # Meme template generation
├── token_balance.py      # Token balance checking
├── token_checker.js      # Solana token utilities
├── supervisor.py         # Bot supervision and monitoring
├── utils.py             # Utility functions
├── pyproject.toml       # Python dependencies
├── package.json         # Node.js dependencies
├── Procfile            # Railway deployment configuration
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

## Repository Creation Steps

1. Create a new repository:
   - Go to https://github.com/new
   - Set owner to "NWA-Coin"
   - Set repository name to "NWAcoinbot"
   - Make it Public
   - Initialize with README

2. Push the code:
   ```bash
   git clone https://github.com/NWA-Coin/NWAcoinbot.git
   cd NWAcoinbot
   # Copy all the project files here
   git add .
   git commit -m "Initial commit: NWAcoinbot Discord bot"
   git push origin main
   ```

3. Railway Deployment:
   - Go to Railway dashboard
   - Create new project
   - Connect to GitHub repository (NWA-Coin/NWAcoinbot)
   - Add required environment variables:
     - DISCORD_TOKEN
     - OPENAI_API_KEY
     - DATABASE_URL
     - COINGECKO_API_KEY
   - Deploy the project

## Environment Variables Setup

The following environment variables are required:
```
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=your_postgresql_url
COINGECKO_API_KEY=your_coingecko_api_key
```

## Verification Steps

After deployment:
1. Check Railway logs for successful bot startup
2. Verify bot is online in Discord
3. Test basic commands (!ping, !help)
4. Test core features (!roast, !meme, etc.)

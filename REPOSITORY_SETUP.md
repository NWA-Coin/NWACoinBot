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

## Quick Setup Steps

### 1. Create Repository
Go to https://github.com/new
- Set owner to "NWA-Coin"
- Repository name: "NWAcoinbot"
- Make it Public
- Initialize with README

### 2. Add Environment Variables
Required environment variables for Railway deployment:
```
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=your_postgresql_url
COINGECKO_API_KEY=your_coingecko_api_key
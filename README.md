DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=your_postgresql_url
COINGECKO_API_KEY=your_coingecko_api_key
```

## Deployment on Railway

1. Create a new project on Railway
2. Connect this repository
3. Add the required environment variables
4. Deploy! (Procfile is configured for worker deployment)

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/NWA-Coin/NWAcoinbot.git
cd NWAcoinbot
```

2. Install dependencies:
```bash
# Python packages
pip install discord-py python-dotenv openai pillow matplotlib plotly psutil numpy requests base58 psycopg2-binary anthropic emoji pytz selenium

# Node.js packages
npm install @solana/web3.js @solana/spl-token openai
```

3. Configure environment variables in `.env`
4. Run the bot:
```bash
python bot.py
# Railway Deployment Guide

## Prerequisites
- A GitHub account
- A Railway account (https://railway.app)
- Your bot's Discord token
- OpenAI API key
- CoinGecko API key

## Deployment Steps

### 1. Initial Setup
1. Fork the repository to your GitHub account
2. Connect your GitHub account to Railway
3. Create a new project in Railway from your GitHub repository

### 2. Environment Variables
Set the following environment variables in Railway:
```
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
COINGECKO_API_KEY=your_coingecko_api_key
DATABASE_URL=your_postgresql_url
```

### 3. Database Setup
1. Add a PostgreSQL database to your Railway project
2. Railway will automatically set up the DATABASE_URL

### 4. Deployment Configuration
The repository includes `railway.toml` which configures:
- Automatic restarts on failure
- Health monitoring
- Process management

### 5. Monitoring
The bot includes built-in health monitoring that:
- Checks Discord connection every 5 minutes
- Verifies database connectivity
- Auto-reconnects on disconnection
- Logs health status to Railway logs

### 6. Troubleshooting
If the bot goes offline:
1. Check Railway deployment logs for errors
2. Verify environment variables are set correctly
3. Check Discord Developer Portal for any token issues
4. Review database connection status

## Maintenance
- Monitor Railway logs for any recurring issues
- Keep dependencies updated through `pyproject.toml`
- Review bot's health check logs periodically

## High Availability
The bot is configured for high availability through:
- Railway's automatic deployment
- Built-in health monitoring
- Automatic process restarts
- Database connection management

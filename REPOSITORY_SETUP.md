# Configure Git credentials
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"

# Initialize Git repository
git init

# Add the remote repository
git remote add origin https://github.com/NWA-Coin/NWACoinBot.git

# Create and switch to main branch
git checkout -b main
```

### 3. Railway Setup
1. Go to railway.app and create an account
2. Connect your GitHub repository
3. Create a new project from the repository
4. Add PostgreSQL database from Railway dashboard
5. Configure environment variables

### 4. Initial Deployment
```bash
# Add all files
git add .

# Commit changes
git commit -m "Initial commit: NWAcoinbot Discord bot"

# Push to main branch
git push -u origin main
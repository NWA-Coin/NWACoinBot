## Quick Setup Steps

### 1. Create Repository
Go to https://github.com/new
- Set owner to "NWA-Coin"
- Repository name: "NWAcoinbot"
- Make it Public
- Initialize with README

### 2. Git Setup
# Git Setup Instructions

1. Configure Git credentials:
```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

2. Set up the repository:
```bash
# Initialize Git repository
git init

# Add the remote repository
git remote add origin https://github.com/NWA-Coin/NWACoinBot.git

# Create and switch to main branch
git checkout -b main
```

3. Add and commit files:
```bash
# Add all files
git add .

# Commit changes
git commit -m "Initial commit: NWAcoinbot Discord bot"
```

4. Push to GitHub:
```bash
# Push to main branch
git push -u origin main
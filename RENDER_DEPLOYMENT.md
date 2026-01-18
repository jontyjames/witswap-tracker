# Deploy to Render (FREE 24/7 Hosting)

## Step-by-Step Guide

### Step 1: Create a GitHub Account (if you don't have one)
1. Go to https://github.com
2. Click "Sign up"
3. Follow the prompts to create your account

### Step 2: Install Git (if not already installed)
1. Download Git from: https://git-scm.com/download/win
2. Install it with default settings
3. Restart your Command Prompt after installing

### Step 3: Push Your Code to GitHub

Open Command Prompt in your `Witswap Tracker` folder and run these commands one by one:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git init
git add .
git commit -m "Initial commit - Marine data tracker"
git branch -M main
```

Now create a new repository on GitHub:
1. Go to https://github.com/new
2. Repository name: `witswap-tracker`
3. Make it **Public**
4. **DO NOT** check "Initialize with README"
5. Click "Create repository"

GitHub will show you commands. Use these instead:
```bash
git remote add origin https://github.com/YOUR_USERNAME/witswap-tracker.git
git push -u origin main
```
(Replace YOUR_USERNAME with your GitHub username)

### Step 4: Deploy to Render

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (easier) or email
4. Once logged in, click "New +" → "Web Service"
5. Click "Connect account" to connect GitHub
6. Find and select your `witswap-tracker` repository
7. Click "Connect"

### Step 5: Configure the Service

Render will show a form. Fill it in:

- **Name**: `witswap-tracker` (or any name you like)
- **Region**: Choose closest to New Zealand (Singapore or Oregon)
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`
- **Instance Type**: Select **"Free"**

Click "Create Web Service"

### Step 6: Wait for Deployment

- Render will start building your app (takes 2-5 minutes)
- You'll see logs scrolling - this is normal
- When you see "Scheduler started" and "Fetching initial data" - it's working!
- Status will change to "Live" with a green dot

### Step 7: Access Your Tracker

- Render gives you a URL like: `witswap-tracker.onrender.com`
- Click the URL to open your live tracker
- It's now collecting data every 2 minutes, 24/7!

## Important Notes

✅ **Completely FREE** - No credit card required
✅ **Runs 24/7** - Your scheduled tasks keep it active
✅ **Auto-updates** - Push to GitHub, Render auto-deploys
✅ **Database included** - Your SQLite database persists

⚠️ **One limitation**: If no one visits the site for 15+ minutes, it MAY spin down. But it wakes up instantly when visited, and your scheduled tasks should keep it active most of the time.

## Troubleshooting

**If deployment fails:**
- Check the logs in Render dashboard
- Make sure all files are committed to GitHub
- Verify requirements.txt is in the repository

**If you need help at any step, just ask!**

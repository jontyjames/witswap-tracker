# Deployment Guide - Witswap Marine Tracker

## Quick Overview

GitHub stores your code, but you need a **hosting platform** to run it 24/7. Here are your best options:

## Option 1: Railway (Recommended - Easiest)

**Cost**: Free tier available, then ~$5/month
**Setup Time**: 5-10 minutes

### Steps:

1. **Create GitHub Repository**
   - Go to https://github.com
   - Click "New Repository"
   - Name it "witswap-tracker"
   - Make it Public
   - Don't initialize with README (we already have files)

2. **Push Your Code to GitHub**
   Open Command Prompt in your Witswap Tracker folder and run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Marine data tracker"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/witswap-tracker.git
   git push -u origin main
   ```
   (Replace YOUR_USERNAME with your actual GitHub username)

3. **Deploy to Railway**
   - Go to https://railway.app
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account
   - Select "witswap-tracker" repository
   - Railway will auto-detect it's a Python app
   - Click "Deploy"
   - It will automatically install dependencies and start running!

4. **Get Your URL**
   - Once deployed, Railway gives you a URL like: `witswap-tracker.railway.app`
   - Your tracker is now live 24/7!

---

## Option 2: Render

**Cost**: Free tier available
**Setup Time**: 5-10 minutes

### Steps:

1. **Push code to GitHub** (same as Railway step 1-2)

2. **Deploy to Render**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - Name: witswap-tracker
     - Runtime: Python 3
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python app.py`
   - Click "Create Web Service"

3. **Access your app**
   - URL will be like: `witswap-tracker.onrender.com`

---

## Option 3: PythonAnywhere

**Cost**: Free tier available
**Setup Time**: 10-15 minutes
**Note**: Free tier requires manual reload every 3 months

### Steps:

1. Go to https://www.pythonanywhere.com
2. Create a free account
3. Upload your files via the web interface
4. Set up a web app with Flask
5. Configure the scheduler (requires some manual setup)

---

## Option 4: Your Own Computer (Free but Limited)

**Cost**: Free
**Note**: Computer must stay on 24/7, only accessible on your local network unless you set up port forwarding

Just keep running `python app.py` on your computer!

---

## What I Recommend:

**For you**: Use **Railway** - it's the easiest and most reliable.

1. It auto-detects everything
2. Free trial to test it out
3. Only ~$5/month after trial
4. Runs 24/7 automatically
5. Easy to update (just push to GitHub)

---

## Need Help?

If you need step-by-step guidance with any of these options, just ask and I'll walk you through it!

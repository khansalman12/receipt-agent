# ReceiptAgent Deployment Guide

## 🚀 Step-by-Step Deployment to Render.com (FREE)

---

### Step 1: Push to GitHub

1. **Create a new GitHub repository:**
   - Go to https://github.com/new
   - Name: `receiptagent`
   - Make it **Public**
   - Don't initialize with README (we have one)

2. **Push your code:**
   ```bash
   cd "/Users/salmankhan/Downloads/RAG TUTORIAL LEARNING/expense_ai"
   
   # Initialize git
   git init
   
   # Add all files
   git add .
   
   # Commit
   git commit -m "Initial commit: ReceiptAgent - AI Expense Processing"
   
   # Add your GitHub remote (replace YOUR_USERNAME)
   git remote add origin https://github.com/YOUR_USERNAME/receiptagent.git
   
   # Push to GitHub
   git branch -M main
   git push -u origin main
   ```

---

### Step 2: Deploy to Render.com

1. **Create Render account:**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create New Blueprint:**
   - Click "New" → "Blueprint"
   - Connect your `receiptagent` repo
   - Render will read `render.yaml` automatically

3. **Set Environment Variables:**
   - After deploy starts, go to your web service
   - Add `GROQ_API_KEY` in Environment tab
   - Get free key from: https://console.groq.com

4. **Wait for deploy (5-10 minutes)**

5. **Access your app:**
   - Your URL: `https://receiptagent.onrender.com`
   - Test: `https://receiptagent.onrender.com/api/health/`

---

### Step 3: Add Demo Video (Optional but Recommended)

1. **Record with Loom:**
   - Go to https://loom.com (free account)
   - Record 2-min demo:
     - Show API in browser
     - Upload a receipt
     - Show extracted data

2. **Add to README:**
   - Get Loom share link
   - Add to GitHub README

---

## 🎯 Quick Commands Reference

```bash
# Navigate to project
cd "/Users/salmankhan/Downloads/RAG TUTORIAL LEARNING/expense_ai"

# Check git status
git status

# Add and commit changes
git add .
git commit -m "your message"
git push

# View logs on Render
# Go to Render dashboard → Your service → Logs
```

---

## ⚠️ Important Notes

1. **Free tier limitations:**
   - App sleeps after 15 min inactivity
   - First request may be slow (cold start)
   - 750 hours/month free

2. **Keep secrets safe:**
   - Never commit `.env` file
   - Use Render's environment variables

3. **Database:**
   - Free PostgreSQL: 1GB storage
   - Free Redis: 25MB

---

## ✅ Deployment Checklist

- [ ] Created GitHub repository
- [ ] Pushed code to GitHub
- [ ] Created Render account
- [ ] Connected repo to Render
- [ ] Set GROQ_API_KEY in Render
- [ ] Tested deployed API
- [ ] (Optional) Recorded demo video

---

**Your live URL will be:** `https://receiptagent.onrender.com`

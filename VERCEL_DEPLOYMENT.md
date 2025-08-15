# 🚀 Vercel Deployment Guide for OnCall Runbook

## 📋 Prerequisites

1. **GitHub Account** - Your code must be on GitHub
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
3. **OpenAI API Key** - For AI functionality
4. **PostgreSQL Database** - For session storage (we'll use Vercel Postgres)

## 🎯 **Step 1: Prepare Your Repository**

Your code is already on GitHub, so we're ready to deploy!

## 🔧 **Step 2: Deploy to Vercel**

### **Option A: One-Click Deploy (Recommended)**

1. **Click this button** (replace with your repo URL):
   ```
   https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/oncall-runbook
   ```

2. **Configure the project:**
   - **Project Name**: `oncall-runbook`
   - **Framework Preset**: `Other`
   - **Root Directory**: `./` (leave as default)
   - **Build Command**: `cd web && npm install && npm run build`
   - **Output Directory**: `web/dist`
   - **Install Command**: `cd web && npm install`

3. **Click "Deploy"**

### **Option B: Manual Deploy via Vercel CLI**

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from your project directory
vercel

# Follow the prompts
```

## 🗄️ **Step 3: Set Up Vercel Postgres Database**

1. **In your Vercel dashboard**, go to your project
2. **Click "Storage"** tab
3. **Click "Create Database"**
4. **Choose "Postgres"**
5. **Select your region** (closest to your users)
6. **Click "Create"**
7. **Copy the connection string** (we'll need this)

## ⚙️ **Step 4: Configure Environment Variables**

In your Vercel project dashboard:

1. **Go to "Settings" → "Environment Variables"**
2. **Add these variables:**

```bash
# API Configuration
VITE_API_BASE=https://your-app.vercel.app/api

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-key-here

# Database Connection
DATABASE_URL=postgresql://username:password@host:port/database
```

3. **Click "Save"**

## 🔄 **Step 5: Redeploy with Database**

1. **Go to "Deployments" tab**
2. **Click "Redeploy"** on your latest deployment
3. **Wait for deployment to complete**

## ✅ **Step 6: Test Your Deployment**

1. **Visit your app**: `https://your-app.vercel.app`
2. **Test the health check**: `https://your-app.vercel.app/api/health`
3. **Test self-check**: `https://your-app.vercel.app/api/selfcheck`

## 🎉 **You're Deployed!**

Your OnCall Runbook is now live on Vercel with:
- ✅ **Frontend**: React app with chat interface
- ✅ **Backend**: FastAPI with RAG capabilities
- ✅ **Database**: PostgreSQL for session storage
- ✅ **File Upload**: Document ingestion system
- ✅ **AI Chat**: OpenAI-powered responses

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **Build Fails**: Check that all dependencies are in `package.json`
2. **API Errors**: Verify environment variables are set correctly
3. **Database Connection**: Ensure `DATABASE_URL` is correct
4. **CORS Issues**: Check that API routes are working

### **Useful Commands:**

```bash
# Check deployment status
vercel ls

# View logs
vercel logs

# Redeploy
vercel --prod
```

## 📱 **Features That Work on Vercel:**

- ✅ **Chat Interface** - Full conversation history
- ✅ **Document Upload** - Text files, logs, markdown
- ✅ **Session Management** - Persistent chat sessions
- ✅ **AI Responses** - OpenAI-powered answers
- ✅ **File Storage** - Document persistence
- ✅ **Responsive Design** - Mobile-friendly UI

## 🚀 **Next Steps:**

1. **Upload some documents** to test the system
2. **Try asking questions** about your uploaded docs
3. **Test session persistence** by refreshing the page
4. **Share your app** with your team!

---

**Need Help?** Check the Vercel documentation or reach out if you encounter any issues!

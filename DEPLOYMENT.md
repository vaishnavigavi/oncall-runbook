# 🚀 Deployment Guide - OnCall Runbook RAG System

## Overview

This guide walks you through deploying the OnCall Runbook RAG System to **Render** - a completely free, production-ready platform.

## 🎯 Why Render?

- ✅ **100% Free** - No credit card required
- ✅ **Production Ready** - Enterprise-grade infrastructure  
- ✅ **All Features Work** - No compromises on functionality
- ✅ **Simple Setup** - One-click deployment from GitHub
- ✅ **Auto-scaling** - Handles traffic automatically
- ✅ **Custom Domains** - Can add your own domain later

## 📋 Prerequisites

1. **GitHub Repository** ✅ (Already done!)
2. **Render Account** (Free signup)
3. **Basic understanding of environment variables**

## 🚀 Step-by-Step Deployment

### **Step 1: Sign Up for Render**

1. Go to [render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended) or email
4. Verify your email address

### **Step 2: Create New Web Service**

1. **Click "New +"** in your Render dashboard
2. **Select "Web Service"**
3. **Connect your GitHub repository**:
   - Choose "oncall-runbook" repository
   - Select the main branch

### **Step 3: Configure API Service**

**Service Name**: `oncall-runbook-api`

**Environment**: `Python 3`

**Build Command**:
```bash
pip install -r requirements.txt
```

**Start Command**:
```bash
cd api && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Plan**: `Free`

### **Step 4: Set Environment Variables**

Click "Environment" tab and add:

| Key | Value | Description |
|-----|-------|-------------|
| `EMBEDDING_PROVIDER` | `mock` | Use mock embeddings (free) |
| `OPENAI_API_KEY` | `test-key` | Placeholder for OpenAI |
| `DATABASE_URL` | `[Will be set automatically]` | Render PostgreSQL URL |

### **Step 5: Create PostgreSQL Database**

1. **Click "New +"** → **"PostgreSQL"**
2. **Name**: `oncall-runbook-db`
3. **Plan**: `Free`
4. **Database**: `oncall_runbook`
5. **User**: `oncall_user`

### **Step 6: Link Database to API**

1. Go back to your API service
2. **Environment** tab → **"Link Database"**
3. Select `oncall-runbook-db`
4. **Copy the `DATABASE_URL`** and paste it as environment variable

### **Step 7: Deploy API**

1. **Click "Create Web Service"**
2. **Wait for build** (5-10 minutes)
3. **Note the URL** (e.g., `https://oncall-runbook-api.onrender.com`)

### **Step 8: Deploy Web Frontend**

1. **Click "New +"** → **"Static Site"**
2. **Name**: `oncall-runbook-web`
3. **Build Command**:
   ```bash
   cd web
   npm install
   npm run build
   ```
4. **Publish Directory**: `web/dist`
5. **Environment Variables**:
   - `VITE_API_BASE`: `https://oncall-runbook-api.onrender.com`

### **Step 9: Test Deployment**

1. **API Health Check**:
   ```bash
   curl https://oncall-runbook-api.onrender.com/health
   ```

2. **Selfcheck Endpoint**:
   ```bash
   curl https://oncall-runbook-api.onrender.com/selfcheck
   ```

3. **Web Frontend**: Visit your static site URL

## 🔧 Configuration Details

### **Database Migration**
- System automatically detects PostgreSQL vs SQLite
- Tables created automatically on first run
- No manual migration needed

### **File Storage**
- Documents stored in Render's persistent disk
- FAISS index persists across deployments
- File manifest maintained automatically

### **Environment Variables**
All configurable via Render dashboard:
- Database connections
- API keys (when you add real ones)
- CORS origins
- Service ports

## 🧪 Testing Deployment

### **Run Selfcheck**
```bash
curl https://your-api-url.onrender.com/selfcheck | jq '.'
```

**Expected Result**:
```json
{
  "status": "completed",
  "checks": {
    "kb_status": {"status": "ok"},
    "faiss_index": {"status": "ok"},
    "database": {"status": "ok"},
    "minimal_ingest": {"status": "performed"},
    "sample_rag": {"status": "ok"}
  },
  "summary": {
    "overall_status": "ok",
    "passed": 5,
    "errors": 0
  }
}
```

### **Test RAG Query**
```bash
curl -X POST "https://your-api-url.onrender.com/ask/structured" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the first steps for CPU issues?", "context": ""}'
```

## 🚨 Troubleshooting

### **Common Issues**

1. **Build Fails**
   - Check requirements.txt syntax
   - Verify Python version compatibility
   - Check build logs for errors

2. **Service Won't Start**
   - Verify start command
   - Check environment variables
   - Review service logs

3. **Database Connection Issues**
   - Verify DATABASE_URL is set
   - Check PostgreSQL service is running
   - Ensure database is linked

4. **CORS Errors**
   - Verify frontend URL in CORS origins
   - Check environment variable configuration

### **Debug Commands**

```bash
# Check service logs
# Use Render dashboard → Logs tab

# Test database connection
curl https://your-api-url.onrender.com/selfcheck

# Verify environment variables
# Check Render dashboard → Environment tab
```

## 📈 Monitoring & Scaling

### **Free Tier Limits**
- **API**: Sleeps after 15 min inactivity
- **Database**: 1GB storage, 90 days retention
- **Static Site**: Unlimited requests

### **Performance**
- **Cold Start**: 10-15 seconds after inactivity
- **Warm Performance**: Sub-second response times
- **Auto-scaling**: Handles traffic spikes automatically

## 🔄 Updates & Maintenance

### **Automatic Deployments**
- **GitHub Integration**: Auto-deploy on push to main
- **Rollback**: Easy rollback to previous versions
- **Health Checks**: Automatic monitoring

### **Manual Updates**
1. Push changes to GitHub
2. Render automatically rebuilds and deploys
3. Monitor deployment logs
4. Verify functionality

## 🌐 Custom Domain (Optional)

1. **Add Custom Domain** in Render dashboard
2. **Configure DNS** with your domain provider
3. **SSL Certificate** automatically provisioned
4. **Update CORS** origins if needed

## 💰 Cost Breakdown

**Free Tier Includes**:
- ✅ API hosting (with sleep)
- ✅ PostgreSQL database (1GB)
- ✅ Static site hosting
- ✅ Custom domains
- ✅ SSL certificates
- ✅ CDN and edge locations

**Total Cost**: $0/month

## 🎉 Success Criteria

Deployment is successful when:
- ✅ API responds to `/health`
- ✅ Selfcheck returns "ok" status
- ✅ Web frontend loads
- ✅ RAG queries work
- ✅ Database operations succeed
- ✅ File uploads work
- ✅ All features functional

## 🆘 Support

- **Render Documentation**: [docs.render.com](https://docs.render.com)
- **Community Forum**: [community.render.com](https://community.render.com)
- **GitHub Issues**: Use your repository's issue tracker

---

**Ready to deploy?** Follow the steps above and you'll have a production-ready OnCall Runbook system running for free! 🚀


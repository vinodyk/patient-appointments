# GCP Deployment Guide - Patient Appointment System

**Author:** Vinod Yadav  
**Date:** July 25, 2025

## 🚀 Quick Deployment Steps

### Prerequisites
1. **Google Cloud Account** with billing enabled
2. **Docker Desktop** installed and running
3. **Google Cloud CLI** installed
4. **OpenAI API Key**

### Step 1: Setup GCP Project

```bash
# Create a new project (or use existing)
gcloud projects create patient-appointment-demo --name="Patient Appointment Demo"

# Set the project
gcloud config set project patient-appointment-demo

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 2: Prepare Application

```bash
# Navigate to your project directory
cd C:\1-projects\Patient-appointments

# Build the frontend
cd frontend
npm install
npm run build
cd ..
```

### Step 3: Deploy to Cloud Run (Recommended)

```bash
# Build and deploy in one command
gcloud run deploy patient-appointment-app \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --set-env-vars OPENAI_API_KEY=your_openai_key_here,APP_ENV=production
```

### Step 4: Get Your Public URL

```bash
# Get the service URL
gcloud run services describe patient-appointment-app \
    --region=us-central1 \
    --format="value(status.url)"
```

## 🔧 Alternative Deployment Methods

### Option A: Using Docker Build + Cloud Run

```bash
# Build Docker image
docker build -t gcr.io/patient-appointment-demo/patient-app .

# Push to Google Container Registry
docker push gcr.io/patient-appointment-demo/patient-app

# Deploy to Cloud Run
gcloud run deploy patient-appointment-app \
    --image gcr.io/patient-appointment-demo/patient-app \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars OPENAI_API_KEY=your_key_here
```

### Option B: Using Cloud Build

```bash
# Submit build to Cloud Build
gcloud builds submit --config cloudbuild.yaml

# The cloudbuild.yaml will automatically deploy to Cloud Run
```

### Option C: App Engine (Alternative)

```bash
# Deploy to App Engine
gcloud app deploy app.yaml \
    --env-vars-file env_vars.yaml
```

## 🌐 Testing Your Deployment

### Health Check
```bash
curl https://your-app-url.run.app/health
```

### API Test
```bash
curl -X POST "https://your-app-url.run.app/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "I have a headache", "session_id": "test123"}'
```

## 🔍 Monitoring & Debugging

### View Logs
```bash
# Real-time logs
gcloud logs tail

# Specific service logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# Filter by severity
gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR"
```

### Check Service Status
```bash
# List all Cloud Run services
gcloud run services list

# Get service details
gcloud run services describe patient-appointment-app --region=us-central1
```

### Debug Issues
```bash
# Check build logs
gcloud builds list

# Get specific build details
gcloud builds describe BUILD_ID
```

## 🔐 Security & Environment Variables

### Set Environment Variables
```bash
# Update environment variables
gcloud run services update patient-appointment-app \
    --region us-central1 \
    --set-env-vars OPENAI_API_KEY=new_key,DEBUG=False,APP_ENV=production
```

### Enable Authentication (Optional)
```bash
# Remove public access
gcloud run services remove-iam-policy-binding patient-appointment-app \
    --region=us-central1 \
    --member="allUsers" \
    --role="roles/run.invoker"

# Add specific users
gcloud run services add-iam-policy-binding patient-appointment-app \
    --region=us-central1 \
    --member="user:email@example.com" \
    --role="roles/run.invoker"
```

## 💰 Cost Management

### Set Budget Alerts
```bash
# Create budget (in Cloud Console)
# Billing > Budgets & alerts > Create budget
```

### Auto-scaling Configuration
- **Min instances**: 0 (saves cost)
- **Max instances**: 10 (prevents runaway costs)
- **CPU allocation**: Only during requests
- **Request timeout**: 300 seconds max

## 🔄 CI/CD Setup (Optional)

### GitHub Actions Integration
1. Connect GitHub repository to Cloud Build
2. Add cloudbuild.yaml trigger
3. Automatic deployment on push to main branch

### Manual Trigger Setup
```bash
# Create build trigger
gcloud builds triggers create github \
    --repo-name=Patient-appointments \
    --repo-owner=your-github-username \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml
```

## 🌍 Custom Domain (Optional)

### Add Custom Domain
```bash
# Map custom domain
gcloud run domain-mappings create \
    --service patient-appointment-app \
    --domain your-domain.com \
    --region us-central1
```

## 📋 Troubleshooting

### Common Issues

**Build Failures:**
- Check Docker file syntax
- Ensure all dependencies in requirements.txt
- Verify frontend builds successfully

**Runtime Errors:**
- Check environment variables are set
- Verify OpenAI API key is valid
- Check memory/CPU limits

**502/503 Errors:**
- Increase memory allocation
- Check application startup time
- Verify health check endpoint

### Quick Fixes
```bash
# Restart service
gcloud run services update patient-appointment-app --region=us-central1

# Increase resources
gcloud run services update patient-appointment-app \
    --region=us-central1 \
    --memory=4Gi \
    --cpu=2

# View recent errors
gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=20
```

## 🎯 Final Steps

1. **Test the application** thoroughly
2. **Share the URL** with others
3. **Monitor usage** and costs
4. **Set up alerts** for errors
5. **Document any customizations**

Your application will be available at:
`https://patient-appointment-app-XXXXXXXXXX-uc.a.run.app`

## 📞 Support

- **Google Cloud Support**: https://cloud.google.com/support
- **Cloud Run Documentation**: https://cloud.google.com/run/docs
- **Pricing Calculator**: https://cloud.google.com/products/calculator
@echo off
REM Deployment script for Patient Appointment System
REM Author: Vinod Yadav
REM Date: 7-25-2025

echo 🏥 Patient Appointment System - GCP Deployment
echo =============================================

REM Check if required tools are installed
where gcloud >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Google Cloud CLI not found. Please install it first.
    echo Download from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker not found. Please install Docker Desktop first.
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Get project information
echo.
echo 📋 Setting up GCP project...
set /p PROJECT_ID="Enter your GCP Project ID: "
set /p OPENAI_API_KEY="Enter your OpenAI API Key: "

if "%PROJECT_ID%"=="" (
    echo ❌ Project ID is required
    pause
    exit /b 1
)

if "%OPENAI_API_KEY%"=="" (
    echo ❌ OpenAI API Key is required
    pause
    exit /b 1
)

echo.
echo 🔧 Configuring gcloud...
gcloud config set project %PROJECT_ID%

echo.
echo 🏗️ Building frontend...
cd frontend
call npm install
call npm run build
cd ..

echo.
echo 🐳 Building Docker image...
docker build -t gcr.io/%PROJECT_ID%/patient-appointment-app .

echo.
echo 📤 Pushing to Google Container Registry...
docker push gcr.io/%PROJECT_ID%/patient-appointment-app

echo.
echo 🚀 Deploying to Cloud Run...
gcloud run deploy patient-appointment-app ^
    --image gcr.io/%PROJECT_ID%/patient-appointment-app ^
    --platform managed ^
    --region us-central1 ^
    --allow-unauthenticated ^
    --port 8080 ^
    --memory 2Gi ^
    --cpu 2 ^
    --timeout 300 ^
    --concurrency 100 ^
    --max-instances 10 ^
    --set-env-vars OPENAI_API_KEY=%OPENAI_API_KEY%,APP_ENV=production

echo.
echo ✅ Deployment completed!
echo.
echo 🌐 Your app is now available at:
gcloud run services describe patient-appointment-app --region=us-central1 --format="value(status.url)"

echo.
echo 📋 Next steps:
echo 1. Test your application using the URL above
echo 2. Share the URL with others to test
echo 3. Monitor logs: gcloud logs tail
echo.
pause
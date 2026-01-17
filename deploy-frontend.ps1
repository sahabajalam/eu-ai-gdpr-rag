# deploy-frontend.ps1
param (
    [string]$BackendUrl
)

$ErrorActionPreference = "Stop"

# --- Configuration ---
# 1. Get Project ID from gcloud
try {
    $PROJECT_ID = gcloud config get-value project 2>$null
} catch {
    $PROJECT_ID = ""
}

if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        # Only overwrite PROJECT_ID if it's missing
        if ((-not $PROJECT_ID) -and ($_ -match "^GCP_PROJECT_ID=(.*)")) { $PROJECT_ID = $matches[1].Trim() }
        # Only overwrite BackendUrl if it's missing
        if ((-not $BackendUrl) -and ($_ -match "^BACKEND_URL=(.*)")) { $BackendUrl = $matches[1].Trim() }
    }
}

if (-not $PROJECT_ID) {
    Write-Error "Could not detect a valid GCP Project ID. Please run 'gcloud config set project YOUR_PROJECT_ID' first."
}

$REGION = "us-central1"
$SERVICE_NAME = "eu-ai-frontend"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

# --- Prompt for Backend URL ---
if (-not $BackendUrl) {
    Write-Host "Backend URL is required." -ForegroundColor Yellow
    $BackendUrl = Read-Host "Paste Backend URL (e.g., https://eu-ai-backend-xyz.run.app)"
}

if (-not $BackendUrl) { Write-Error "Backend URL required." }

Write-Host "Deploying Frontend to Project: $PROJECT_ID" -ForegroundColor Cyan

# 1. Build & Push
Write-Host "Building and Pushing Image..." -ForegroundColor Yellow
# Using local docker to support build-args easily, then pushing to GCR
# Ensure docker is authenticated: gcloud auth configure-docker
docker build -t "$IMAGE_NAME`:latest" --build-arg "NEXT_PUBLIC_API_URL=$BackendUrl" ./ui

Write-Host "Pushing to GCR..."
docker push "$IMAGE_NAME`:latest"

# 2. Deploy
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME --project $PROJECT_ID --image "$IMAGE_NAME`:latest" --region $REGION --platform managed --allow-unauthenticated --memory 512Mi

Write-Host "Frontend Deployment Complete!" -ForegroundColor Green
$FRONTEND_URL = gcloud run services describe $SERVICE_NAME --project $PROJECT_ID --platform managed --region $REGION --format 'value(status.url)'
Write-Host "Frontend URL: $FRONTEND_URL" -ForegroundColor White

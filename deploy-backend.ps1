# deploy-backend.ps1
$ErrorActionPreference = "Stop"

# --- Configuration ---
try {
    $PROJECT_ID = gcloud config get-value project 2>$null
} catch {
    $PROJECT_ID = ""
}

if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ((-not $PROJECT_ID) -and ($_ -match "^GCP_PROJECT_ID=(.*)")) { $PROJECT_ID = $matches[1].Trim() }
        if ($_ -match "^GEMINI_API_KEY=(.*)") { $GEMINI_API_KEY = $matches[1].Trim() }
    }
}

if (-not $PROJECT_ID) {
    Write-Error "Could not detect a valid GCP Project ID. Please run 'gcloud config set project YOUR_PROJECT_ID' first."
}

$REGION = "us-central1"
$SERVICE_NAME = "eu-ai-backend"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "Deploying Backend to GCP Project: $PROJECT_ID" -ForegroundColor Cyan
Write-Host "Image Tag: $IMAGE_NAME" -ForegroundColor Gray

# 1. Build Image Locally
Write-Host "Building Container Image Locally..." -ForegroundColor Yellow
docker build -t "$IMAGE_NAME`:latest" .

# check if build succeeded
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed."
}

# 2. Push Image to GCR
Write-Host "Pushing Image to Google Container Registry..." -ForegroundColor Yellow
# Ensure docker auth is configured
# gcloud auth configure-docker
docker push "$IMAGE_NAME`:latest"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker push failed. Run 'gcloud auth configure-docker' if authentication fails."
}

# 3. Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow

gcloud run deploy $SERVICE_NAME `
    --project $PROJECT_ID `
    --image "$IMAGE_NAME`:latest" `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --set-env-vars "GEMINI_API_KEY=$GEMINI_API_KEY"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Deployment failed."
}

Write-Host "Backend Deployment Complete!" -ForegroundColor Green
$BACKEND_URL = gcloud run services describe $SERVICE_NAME --project $PROJECT_ID --platform managed --region $REGION --format 'value(status.url)'
Write-Host "Backend URL: $BACKEND_URL" -ForegroundColor White
Write-Host "IMPORTANT: Copy this URL. You will need it for the frontend deployment." -ForegroundColor Magenta

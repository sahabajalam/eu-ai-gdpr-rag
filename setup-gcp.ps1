# setup-gcp.ps1
# Helper script to prepare your GCP Project
$ErrorActionPreference = "Stop"

Write-Host "Checking Google Cloud Setup..." -ForegroundColor Cyan

# 1. Check for gcloud
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Error "The 'gcloud' CLI is not installed. Please install the Google Cloud SDK first."
}

# 2. Login
Write-Host "--- Authentication ---" -ForegroundColor Yellow
$currentAuth = gcloud auth list --filter=status:ACTIVE --format="value(account)"
if (-not $currentAuth) {
    Write-Host "You need to log in..."
    gcloud auth login
} else {
    Write-Host "Logged in as: $currentAuth" -ForegroundColor Gray
}

# 3. Project Selection
Write-Host "--- Project Selection ---" -ForegroundColor Yellow
$currentProject = gcloud config get-value project 2>$null
Write-Host "Current active project: $currentProject"

$useNew = Read-Host "Do you want to use a DIFFERENT project ID? (y/n)"
if ($useNew -eq 'y') {
    $projectId = Read-Host "Enter your GCP Project ID"
    gcloud config set project $projectId
    $currentProject = $projectId
}

if (-not $currentProject) {
    Write-Error "No project selected. Please create one in the Cloud Console."
}

# Update .env check
if (Test-Path .env) {
    Write-Host "Note: Ensure GCP_PROJECT_ID=$currentProject is in your .env file." -ForegroundColor Gray
}

# 4. Enable APIs
Write-Host "--- Enabling Required APIs ---" -ForegroundColor Yellow
$apis = @("run.googleapis.com", "cloudbuild.googleapis.com", "artifactregistry.googleapis.com", "containerregistry.googleapis.com")

foreach ($api in $apis) {
    Write-Host "Enabling $api..."
    gcloud services enable $api
}

# 5. Docker Auth
Write-Host "--- Configuring Docker Auth ---" -ForegroundColor Yellow
gcloud auth configure-docker

Write-Host "Setup Complete! You can now run 'deploy-backend.ps1'." -ForegroundColor Green

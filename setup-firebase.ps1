# setup-firebase.ps1
$ErrorActionPreference = "Stop"

Write-Host "Setting up Firebase Hosting..." -ForegroundColor Cyan

# 1. Check/Install Firebase CLI
if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    Write-Host "Firebase CLI not found. Installing via npm..." -ForegroundColor Yellow
    npm install -g firebase-tools
}

# 2. Login
Write-Host "1. Authentication" -ForegroundColor Yellow
try {
    # Removed invalid --reauth flag
    firebase login --interactive
} catch {
    Write-Host "   Please log in to Firebase in the browser window..."
    firebase login
}

# 3. Project Setup
# Auto-detect defaults
$DEFAULT_ID = ""
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match "^GCP_PROJECT_ID=(.*)") { $DEFAULT_ID = $matches[1].Trim() }
    }
}

Write-Host ""
Write-Host "2. Linking Project" -ForegroundColor Yellow
Write-Host "   To get 'euaigdpr.web.app', your Firebase Project ID must be 'euaigdpr'."
Write-Host "   (Note: You must own this project or create it first in the Firebase Console)"

$FIREBASE_PROJECT_ID = Read-Host "Enter Firebase Project ID (default: $DEFAULT_ID)"
if (-not $FIREBASE_PROJECT_ID) {
    $FIREBASE_PROJECT_ID = $DEFAULT_ID
}

if (-not $FIREBASE_PROJECT_ID) {
    Write-Error "Project ID is required."
}

# Create .firebaserc
Set-Content -Path .firebaserc -Value "{`"projects`": {`"default`": `"$FIREBASE_PROJECT_ID`"}}"
Write-Host "   Linked to: $FIREBASE_PROJECT_ID" -ForegroundColor Green

# 4. Deploy
Write-Host ""
Write-Host "3. Deploying Hosting..." -ForegroundColor Yellow
firebase deploy --only hosting

Write-Host ""
Write-Host "Success! Your app should be live." -ForegroundColor Cyan

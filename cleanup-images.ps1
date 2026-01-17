# cleanup-images.ps1
# Deletes old images from GCR, keeping only the most recent ones.

param (
    [int]$Keep = 1
)

$ErrorActionPreference = "Stop"

# Configuration
try {
    $PROJECT_ID = gcloud config get-value project 2>$null
} catch {
    $PROJECT_ID = ""
}

if (-not $PROJECT_ID) {
    Write-Error "Could not detect a valid GCP Project ID."
}

$IMAGES = @(
    "gcr.io/$PROJECT_ID/eu-ai-backend",
    "gcr.io/$PROJECT_ID/eu-ai-frontend"
)

foreach ($IMAGE_NAME in $IMAGES) {
    Write-Host "Cleaning up image: $IMAGE_NAME" -ForegroundColor Cyan
    
    # List digests, sorted by date (oldest first)
    # We want to keep the NEWEST $Keep
    
    $digests = gcloud container images list-tags $IMAGE_NAME --limit=9999 --sort-by=TIMESTAMP --format='get(digest)' 2>$null
    
    if (-not $digests) {
        Write-Host "   No images found or error listing images." -ForegroundColor Gray
        continue
    }
    
    $count = $digests.Count
    if ($count -le $Keep) {
        Write-Host "   Found $count images. keeping all (Limit: $Keep)." -ForegroundColor Green
        continue
    }
    
    $toDeleteCount = $count - $Keep
    $toDelete = $digests[0..($toDeleteCount - 1)]
    
    Write-Host "   Found $count images. Deleting $toDeleteCount old images..." -ForegroundColor Yellow
    
    foreach ($digest in $toDelete) {
        $fullImage = "$IMAGE_NAME@$digest"
        Write-Host "   Deleting $fullImage..." -NoNewline
        gcloud container images delete $fullImage --force-delete-tags --quiet
        Write-Host " Done." -ForegroundColor Green
    }
}

Write-Host "Cleanup Complete!" -ForegroundColor Cyan

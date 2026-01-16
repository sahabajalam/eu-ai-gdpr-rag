# Start Backend and Frontend Servers
# usage: .\start-servers.ps1

Write-Host "🚀 Starting EU AI Act & GDPR Compliance Assistant..." -ForegroundColor Cyan
Write-Host ""

# 1. Check if .env file exists (Functionality from original start-servers.ps1)
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "   Copy .env.example to .env and add your GEMINI_API_KEY" -ForegroundColor Yellow
    Write-Host ""
    # Pause to let user read the warning
    Start-Sleep -Seconds 3
}

# 2. Port Cleanup Function (Functionality from start-servers-simple.ps1)
Write-Host "🧹 Cleaning up ports..." -ForegroundColor Cyan

function Kill-Port($port) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($connections) {
            foreach ($conn in $connections) {
                # Only kill if we can identify the process
                if ($conn.OwningProcess -ne 0) {
                    Write-Host "   Killing process $($conn.OwningProcess) on port $port" -ForegroundColor Yellow
                    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
                }
            }
        }
    } catch {
        # Ignore errors if no process found
    }
}

# Clean ports 8000 (Backend) and 3000 (Frontend)
Kill-Port 8000
Kill-Port 3000

Write-Host "✅ Ports 8000 and 3000 are clear" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Starting servers in separate windows..." -ForegroundColor Cyan

# 3. Start Servers in Separate Windows (Simplicity from start-servers-simple.ps1)

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; Write-Host 'Backend Server' -ForegroundColor Green; uv run python -m src.serving.api"

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\ui'; Write-Host 'Frontend Server' -ForegroundColor Cyan; npm run dev"

Write-Host ""
Write-Host "✅ Servers started!" -ForegroundColor Green
Write-Host "📍 Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "📍 Frontend: http://localhost:3000" -ForegroundColor White

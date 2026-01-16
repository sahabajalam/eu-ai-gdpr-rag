# Server Startup Script

This project includes a PowerShell script to start both the backend and frontend servers easily.

## `start-servers.ps1`

**Features:**
- ✅ **Automatic Port Cleanup**: Kills processes on ports 8000 & 3000 to prevent errors.
- ✅ **Environment Check**: Warns if `.env` is missing.
- ✅ **Separate Windows**: Backend and Frontend run in their own windows for clear logs.

**Usage:**
```powershell
.\start-servers.ps1
```

---

## Troubleshooting

**Error: "Execution of scripts is disabled on this system"**

Run this command in PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Backend fails to start**
- Check if `.env` file exists with `GEMINI_API_KEY`
- Ensure data ingestion has been run: `uv run python scripts/ingest_advanced.py`

**Frontend fails to start**
- Run `npm install` in the `ui/` directory first
- Check if port 3000 is blocked by another application (the script usually handles this)

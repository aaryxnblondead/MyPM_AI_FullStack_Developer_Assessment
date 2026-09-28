$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot/../backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

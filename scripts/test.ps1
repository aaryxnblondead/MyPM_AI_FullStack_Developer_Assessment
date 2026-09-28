$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot/../backend"
.\.venv\Scripts\python.exe -m pytest -q
Set-Location "$PSScriptRoot/../frontend"
npm run lint

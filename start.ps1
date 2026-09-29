# Build the frontend (if needed) and serve the whole app at http://127.0.0.1:8000
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
# Pick up Python/Node even if this terminal was opened before they were installed.
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

if (-not (Test-Path "$root\backend\.venv")) {
    python -m venv "$root\backend\.venv"
    & "$root\backend\.venv\Scripts\python.exe" -m pip install -r "$root\backend\requirements.txt"
}
if (-not (Test-Path "$root\frontend\node_modules")) {
    Push-Location "$root\frontend"; npm.cmd install; Pop-Location
}
Push-Location "$root\frontend"; npm.cmd run build; Pop-Location

Push-Location "$root\backend"
try {
    Write-Host "Open http://127.0.0.1:8000"
    & .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
} finally {
    Pop-Location
}

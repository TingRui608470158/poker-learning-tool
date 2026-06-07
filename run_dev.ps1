# Start API + React dev servers in two windows (Windows PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Frontend = Join-Path $Root "frontend"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv not found in PATH."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm not found in PATH. Install Node.js first."
}

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    Write-Host "First-time setup: npm install in frontend/ ..."
    Push-Location $Frontend
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install failed." }
    Pop-Location
}

Write-Host "Opening API window (port 8000) ..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$Root'; Write-Host 'API: http://127.0.0.1:8000/docs'; uv run uvicorn api_main:app --host 127.0.0.1 --port 8000 --reload"
)

Start-Sleep -Seconds 2

Write-Host "Opening frontend window (port 5173) ..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$Frontend'; Write-Host 'UI: http://127.0.0.1:5173'; npm run dev"
)

Write-Host ""
Write-Host "Done. Open in browser: http://127.0.0.1:5173"
Write-Host "(Use 127.0.0.1, not localhost, if connection is refused.)"

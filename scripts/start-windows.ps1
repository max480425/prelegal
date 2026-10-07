# Start Prelegal (Windows): build the Docker image and run the container.
# App available at http://localhost:8000
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "docker is not installed or not on PATH."
    exit 1
}

Write-Host "Building and starting Prelegal..."
docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Error "docker compose failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Prelegal is starting at http://localhost:8000"
Write-Host "API docs:            http://localhost:8000/docs"
Write-Host "Stop with:           scripts\stop-windows.ps1"

# Stop Prelegal (Windows): remove the container (the SQLite DB is ephemeral).
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "Stopping Prelegal..."
docker compose down
if ($LASTEXITCODE -ne 0) {
    Write-Error "docker compose failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Prelegal stopped."

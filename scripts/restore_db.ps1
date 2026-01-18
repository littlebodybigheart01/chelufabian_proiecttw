$ErrorActionPreference = "Stop"

param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile
)

if (-not (Test-Path $BackupFile)) {
    Write-Error "Backup file not found: $BackupFile"
    exit 1
}

Write-Host "Restoring from $BackupFile"
docker compose exec -T db sh -c "psql -U postgres -d garden_records -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'"
Get-Content -Path $BackupFile -Raw | docker compose exec -T db pg_restore -U postgres -d garden_records -F c
Write-Host "Done."

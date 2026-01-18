$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = Join-Path $PSScriptRoot "..\\backups"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
$backupFile = Join-Path $backupDir ("garden_records_{0}.dump" -f $stamp)

Write-Host "Backup to $backupFile"
docker compose exec -T db pg_dump -U postgres -d garden_records -F c -f /tmp/backup.dump
docker compose exec -T db sh -c "cat /tmp/backup.dump" > $backupFile
docker compose exec -T db rm -f /tmp/backup.dump
Write-Host "Done."

# ==============================================================================
# Smart Logistics Platform — PostgreSQL Database Restore Script (PowerShell)
# ==============================================================================
param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    [string]$Host = $env:POSTGRES_SERVER,
    [string]$Port = $env:POSTGRES_PORT,
    [string]$User = $env:POSTGRES_USER,
    [string]$DbName = $env:POSTGRES_DB
)

if (-not $Host) { $Host = "localhost" }
if (-not $Port) { $Port = "5432" }
if (-not $User) { $User = "postgres" }
if (-not $DbName) { $DbName = "smart_logistics" }

if (-not (Test-Path $BackupFile)) {
    Write-Host "[ERROR] Backup file not found: $BackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting Database Restore to: $DbName on $Host`:$Port" -ForegroundColor Cyan
Write-Host "Source File: $BackupFile" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$env:PGPASSWORD = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { "postgres" }

pg_restore -h $Host -p $Port -U $User -d $DbName --clean --if-exists -v $BackupFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] Database restored successfully." -ForegroundColor Green
} else {
    Write-Host "[ERROR] Database restoration failed with exit code $LASTEXITCODE" -ForegroundColor Red
}

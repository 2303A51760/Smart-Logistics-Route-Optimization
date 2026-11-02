# ==============================================================================
# Smart Logistics Platform — PostgreSQL Database Backup Script (PowerShell)
# ==============================================================================
param(
    [string]$BackupDir = "./backups",
    [string]$Host = $env:POSTGRES_SERVER,
    [string]$Port = $env:POSTGRES_PORT,
    [string]$User = $env:POSTGRES_USER,
    [string]$DbName = $env:POSTGRES_DB
)

if (-not $Host) { $Host = "localhost" }
if (-not $Port) { $Port = "5432" }
if (-not $User) { $User = "postgres" }
if (-not $DbName) { $DbName = "smart_logistics" }

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupDir/smart_logistics_backup_$Timestamp.sql"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting Database Backup for: $DbName on $Host`:$Port" -ForegroundColor Cyan
Write-Host "Destination: $BackupFile" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$env:PGPASSWORD = if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { "postgres" }

pg_dump -h $Host -p $Port -U $User -d $DbName -F c -b -f $BackupFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] Database backup completed: $BackupFile" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Database backup failed with exit code $LASTEXITCODE" -ForegroundColor Red
}

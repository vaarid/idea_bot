# backup-bot.ps1
Set-Location $PSScriptRoot

$BACKUP_DIR = "backup"
$DATE = Get-Date -Format "yyyyMMdd_HHmmss"

# Создание резервной копии базы данных
if (Test-Path "data\ideas.db") {
    Copy-Item "data\ideas.db" "$BACKUP_DIR\ideas_$DATE.db"
    Write-Host "Database backed up to $BACKUP_DIR\ideas_$DATE.db" -ForegroundColor Green
}

# Создание резервной копии логов
if (Test-Path "logs\idea_bot.log") {
    Copy-Item "logs\idea_bot.log" "$BACKUP_DIR\logs_$DATE.log"
    Write-Host "Logs backed up to $BACKUP_DIR\logs_$DATE.log" -ForegroundColor Green
}

# Удаление старых бэкапов (старше 30 дней)
Get-ChildItem "$BACKUP_DIR\*.db" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item
Get-ChildItem "$BACKUP_DIR\*.log" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item

Write-Host "Backup completed successfully" -ForegroundColor Green
# monitor-bot.ps1
Set-Location $PSScriptRoot

Write-Host "=== Idea Bot Status ===" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n=== Recent Logs ===" -ForegroundColor Cyan
docker-compose logs --tail=20 idea-bot

Write-Host "`n=== Health Check ===" -ForegroundColor Cyan
$status = docker-compose ps | Select-String "Up"
if ($status) {
    Write-Host "✅ Bot is running" -ForegroundColor Green
} else {
    Write-Host "❌ Bot is not running" -ForegroundColor Red
}
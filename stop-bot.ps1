# stop-bot.ps1
Set-Location $PSScriptRoot
docker-compose down
Write-Host "Idea Bot stopped successfully" -ForegroundColor Yellow
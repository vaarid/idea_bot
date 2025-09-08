# restart-bot.ps1
Set-Location $PSScriptRoot
docker-compose down
docker-compose up -d
Write-Host "Idea Bot restarted successfully" -ForegroundColor Green
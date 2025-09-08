# start-bot.ps1
Set-Location $PSScriptRoot
docker-compose up -d
Write-Host "Idea Bot started successfully" -ForegroundColor Green
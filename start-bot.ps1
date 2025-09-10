# start-bot.ps1
Set-Location $PSScriptRoot
docker run -d --name idea-bot --env-file .env -e TZ=Europe/Moscow -v "${PWD}/data:/app/data" -v "${PWD}/logs:/app/logs" -v "${PWD}/temp_audio:/app/temp_audio" -v "${PWD}/backup:/app/backup" idea-bot
Write-Host "Idea Bot started successfully" -ForegroundColor Green
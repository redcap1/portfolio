@echo off
chcp 65001 >nul
cd /d "%~dp0"
git add -A
git commit -m "Update portfolio"
git push
echo.
echo Done - the site updates in 1-2 minutes
pause

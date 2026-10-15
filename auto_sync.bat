@echo off
cd /d "%~dp0"
echo ============================================
echo  AUTO GIT SYNC is running
echo  Watching this folder every 5 seconds
echo  Press Ctrl+C to stop
echo ============================================
:loop
git status --porcelain > "%TEMP%\gitchanges.txt"
for %%A in ("%TEMP%\gitchanges.txt") do set SIZE=%%~zA
if %SIZE% GTR 0 (
  echo.
  echo [%time%] Change detected!
  git status --short
  git add -A
  git commit -m "Auto-commit %date% %time%"
  git push origin main
  if errorlevel 1 (echo PUSH FAILED - check internet or token) else (echo Pushed to GitHub successfully)
)
timeout /t 5 /nobreak >nul
goto loop
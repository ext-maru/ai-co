@echo off
echo Starting AI Company WSL Recovery System...

REM WSLが起動していることを確認
wsl --list --running | findstr "Ubuntu" >nul
if %errorlevel% neq 0 (
    echo WSL not running, starting WSL...
    wsl --distribution Ubuntu --exec echo "WSL started"
)

REM 復旧スクリプトを実行
wsl --distribution Ubuntu --exec bash -c "cd /home/aicompany/ai_co && ./scripts/auto_startup.sh"

echo AI Company WSL Recovery System started!
pause

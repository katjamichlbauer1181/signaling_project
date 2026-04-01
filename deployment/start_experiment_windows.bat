@echo off
:: ============================================================
:: Symbol Matrix Experiment — Windows tablet startup script
:: Double-click this file to start the experiment.
:: ============================================================

cd /d "%~dp0"

:: Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Could not find venv\Scripts\activate.bat
    echo Please run setup_windows.bat first.
    pause
    exit /b 1
)

:: Reset database for a clean session (removes all previous data)
echo Resetting database...
otree resetdb --noinput
if errorlevel 1 (
    echo ERROR: Could not reset database.
    pause
    exit /b 1
)

:: Start oTree server in background
echo Starting oTree server...
start "oTree Server" /min cmd /c "otree devserver 2>&1 | tee otree_server.log"

:: Wait a few seconds for the server to be ready
timeout /t 4 /nobreak > nul

:: Open the experiment in the default browser
echo Opening experiment in browser...
start "" "http://localhost:8000/demo"

echo.
echo ============================================================
echo  Experiment is running.
echo  Browser should have opened automatically.
echo  If not, open your browser and go to: http://localhost:8000/demo
echo.
echo  DO NOT close this window while the experiment is running.
echo  To export data: go to http://localhost:8000/export
echo ============================================================
echo.
pause

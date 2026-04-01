@echo off
:: ============================================================
:: Symbol Matrix Experiment — ONE-TIME Windows setup
:: Run this once on each tablet before the experiment.
:: Requires Python 3.10+ already installed.
:: ============================================================

cd /d "%~dp0"

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    echo Download from: https://www.python.org/downloads/
    echo Make sure to tick "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing oTree (this may take a few minutes)...
pip install otree

echo.
echo ============================================================
echo  Setup complete!
echo  Run start_experiment_windows.bat to begin the experiment.
echo ============================================================
pause

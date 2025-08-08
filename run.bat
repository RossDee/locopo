@echo off
REM Locopon - Swedish Retail Deals Intelligence System
REM Windows startup script

echo Starting Locopon...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run Locopon
python main.py %*

pause

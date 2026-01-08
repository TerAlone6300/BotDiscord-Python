@echo off
echo ===============================
echo Starting bot (Windows)
echo ===============================

echo Installing requirements...
pip install -r requirements.txt

echo.
echo ===============================
echo GIT PULL STEP
echo Please edit this file and enable git pull if needed
echo ===============================
REM git pull

echo.
echo Starting bot...
python bot.py

pause
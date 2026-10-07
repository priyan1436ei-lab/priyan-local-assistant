@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Run install-windows.bat first.
 pause
 exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements-voice.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe setup.py --voice
if errorlevel 1 goto failed
echo Voice packages and recognition model are ready. Restart the app.
pause
exit /b 0
:failed
echo Voice installation failed. Read the error above.
pause
exit /b 1

@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
 .venv\Scripts\python.exe app.py
) else (
 echo First run: double-click install-windows.bat to install the embedded AI engine.
 echo Opening the organizer without AI dependencies using your Python installation...
 python app.py
)
pause

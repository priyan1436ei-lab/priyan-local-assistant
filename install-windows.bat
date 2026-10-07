@echo off
setlocal
cd /d "%~dp0"
echo PRIYAN LOCAL - first-time installation
where py >nul 2>nul
if errorlevel 1 (
  python -m venv .venv
) else (
  py -3 -m venv .venv
)
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install --only-binary=llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu -r requirements.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install -r requirements-documents.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe setup.py --model
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip freeze > installed-versions.txt
echo.
echo Installation finished. Double-click start-windows.bat.
echo Optional voice: run install-voice-windows.bat.
pause
exit /b 0
:failed
echo.
echo Installation failed. Read the error above and SETUP.md.
echo Use 64-bit Python 3.11 or 3.12 if a compatible native wheel was not found.
pause
exit /b 1

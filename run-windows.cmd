@echo off
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo Missing venv. Run setup-windows.cmd first.
  pause
  exit /b 1
)
venv\Scripts\python.exe -u app.py
if errorlevel 1 (
  echo App exited with an error. See above.
  pause
  exit /b 1
)

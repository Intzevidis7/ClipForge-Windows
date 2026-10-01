@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.12 from python.org and include the py launcher.
  pause
  exit /b 1
)
py -3.12 -c "import sys; print(sys.version)" >nul 2>nul
if errorlevel 1 (
  echo Python 3.12 was not found. Install Python 3.12 and retry.
  pause
  exit /b 1
)
where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo ffmpeg not found on PATH. Install FFmpeg and open a NEW terminal.
  pause
  exit /b 1
)
where ffprobe >nul 2>nul
if errorlevel 1 (
  echo ffprobe not found on PATH. Install FFmpeg and open a NEW terminal.
  pause
  exit /b 1
)
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama not found. Install Ollama for Windows and open a NEW terminal.
  pause
  exit /b 1
)
if exist venv\Scripts\python.exe (
  venv\Scripts\python.exe -c "import sys; assert sys.version_info[:2] == (3, 12) and sys.prefix != sys.base_prefix" >nul 2>nul
  if errorlevel 1 (
    echo Existing venv is not a usable Python 3.12 environment. Rename venv to venv-old and retry.
    pause
    exit /b 1
  )
) else (
  py -3.12 -m venv venv
  if errorlevel 1 (
    echo Could not create venv.
    pause
    exit /b 1
  )
)
venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :fail
venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 goto :fail
venv\Scripts\python.exe -c "import gradio, faster_whisper, cv2, scenedetect, requests, av; print('Imports OK')"
if errorlevel 1 goto :fail
ffmpeg -hide_banner -filters | findstr /R /C:" ass " >nul
if errorlevel 1 echo Warning: FFmpeg ass filter missing; edited karaoke subtitle render will fail.
ollama list | findstr /C:"llama3.2:3b" >nul
if errorlevel 1 (
  echo Pulling llama3.2:3b. Ensure Ollama is running.
  ollama pull llama3.2:3b
  if errorlevel 1 goto :fail
)
echo Setup complete. Double-click run-windows.cmd to start.
pause
exit /b 0
:fail
echo Setup failed. Check errors above and README-WINDOWS.md.
pause
exit /b 1

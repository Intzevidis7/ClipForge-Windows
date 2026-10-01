# ClipForge for Windows

This guide starts with a fresh Windows computer. ClipForge is Python source code, not a prebuilt `.exe`. Install the three prerequisites below, then run the included setup script. Use **Command Prompt** for the commands shown here.

## 1. Download ClipForge

On the ClipForge-Windows GitHub repository page, choose **Code → Download ZIP**. In File Explorer, right-click the downloaded ZIP → **Extract All** → **Extract**. Open the extracted project folder and confirm `setup-windows.cmd`, `run-windows.cmd`, and `requirements.txt` are there. Do not run scripts from inside the ZIP preview.

## 2. Install Python 3.12

1. Open the official [Python 3.12.10 release page](https://www.python.org/downloads/release/python-31210/).
2. Scroll to **Files** and click **Windows installer (64-bit)**. Download and run it; do not choose the embeddable package or source code.
3. On the installer screen, select **Add python.exe to PATH** and leave the **Python launcher / py launcher** enabled. Click **Install Now**.
4. After installation, open a **new Command Prompt**: press Start, type `cmd`, and press Enter. Run:

```bat
py -3.12 --version
```

You should see `Python 3.12.x`. If `py` is not recognized, rerun the installer with the Python launcher enabled. Even if you have a newer Python installed, this project needs Python 3.12.

## 3. Install FFmpeg

FFmpeg is a ZIP download, **not** an installer. Do this on the Windows PC:

1. Click [Download FFmpeg release essentials (ZIP)](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip). This is the Windows build provider linked from [FFmpeg's official download page](https://ffmpeg.org/download.html). You do not need to download FFmpeg source code.
2. Open **Downloads** in File Explorer. Right-click `ffmpeg-release-essentials.zip` → **Extract All** → **Extract**.
3. Open the extracted folder. There may be a second folder with a version number: open it too. Find the folder called **`bin`**. Inside `bin`, you should see `ffmpeg.exe` and `ffprobe.exe` (or `ffmpeg` and `ffprobe` shown as **Application** if Windows hides extensions).
4. Move the **entire extracted FFmpeg folder** to a permanent location such as `C:fmpeg`. Keep its subfolders intact. For example, the files might now be at `C:fmpegfmpeg-9.0.2-essentials_buildinfmpeg.exe`. Your version-numbered folder may have a different name.
5. Navigate back to the **`bin` folder containing `ffmpeg.exe`**. Click File Explorer's address bar at the top, then press `Ctrl+C` to copy the folder's full path. Copy the `bin` **folder path**, not the ZIP name or the `ffmpeg.exe` file path.
6. Press **Start**, search for **Edit environment variables for your account**, and open it. In **User variables**, select **Path** → **Edit** → **New**. Paste the path you copied. Click **OK** on every window. Add a new entry; **do not delete existing Path entries**.
7. Close Command Prompt if one is open. Open a **new Command Prompt** and enter these commands one at a time:

```bat
ffmpeg -version
ffprobe -version
```

If **both** show version details, you're done. If one says “not recognized,” reopen the Path editor and check that the new entry points to the `bin` folder that actually contains both `.exe` files. Close and reopen Command Prompt after fixing it. **Do not run ClipForge setup until both commands work.**

For karaoke caption support, you can also run:

```bat
ffmpeg -hide_banner -filters | findstr ass
```

Look for a filter named `ass` in the result.

## 4. Install Ollama

1. Open the official [Ollama for Windows download page](https://ollama.com/download/windows), download the Windows installer, and run it.
2. Launch Ollama if it did not start automatically. Open a **new Command Prompt** and run:

```bat
ollama --version
ollama list
```

If `ollama` is not recognized, check that installation finished, launch Ollama from the Start menu, and open a new Command Prompt. The ClipForge setup script downloads the `llama3.2:3b` model if needed. You need internet access and available disk space for initial package and model downloads.

## 5. Set up and start ClipForge

Go to the extracted ClipForge project folder in File Explorer and double-click **`setup-windows.cmd`**. Keep the window open and read any errors. The script creates its Python environment, installs packages, checks prerequisites, and pulls the Ollama model if needed; it does not install Python, FFmpeg, or Ollama for you.

When setup finishes successfully, double-click **`run-windows.cmd`** in the same folder. Leave its Command Prompt window open while using the app. If it doesn't open a browser tab, visit [http://127.0.0.1:7860](http://127.0.0.1:7860). Press `Ctrl+C` in its terminal to stop it.

## 6. Test with a short video

Upload a short video or paste its Windows file path in ClipForge. Generate clips, review the suggested moments, and check the transcript. If you want karaoke captions, load editable captions, fix any text or timing errors, select a font that supports your language, and render a captioned version. The automatic word timing is an estimate, so review it before publishing.

## If something goes wrong

| Message or symptom | Check |
|---|---|
| `py -3.12` not recognized | Install the **64-bit Python 3.12 installer** with the py launcher; open a new Command Prompt. |
| `ffmpeg` or `ffprobe` not recognized | Add the actual FFmpeg `bin` folder to **user Path**, then open a new Command Prompt. |
| `ollama` not recognized | Finish installation, start Ollama, and open a new Command Prompt. |
| Caption rendering fails | Check `ffmpeg -hide_banner -filters | findstr ass` and try a short video first. |
| First setup takes a long time | Package and AI model downloads need internet access and free disk space. |

Generated videos and transcripts may be stored in `clips/` directory; do not add them, videos, or the local `venv/` directory to Git. The Windows launchers have not yet been fully end-to-end tested on a Windows PC; first test a short clip and caption render before processing long recordings.

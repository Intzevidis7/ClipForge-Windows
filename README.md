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

FFmpeg comes as a ZIP file, not an installer. Follow these steps **on your Windows PC**:

1. Click [Download FFmpeg release essentials (ZIP)](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip).
2. Open **File Explorer** by pressing the **Windows-logo key + E** on your keyboard. Click **Downloads** in the left-hand sidebar.
3. Right-click `ffmpeg-release-essentials.zip`, then click **Extract All** → **Extract**.
4. Open the extracted folder. If there is another folder inside with a version number in its name, open that too. Find the folder named **`bin`** and open it. You should see `ffmpeg.exe` and `ffprobe.exe`. If Windows hides file extensions, they may appear as `ffmpeg` and `ffprobe`, with **Application** shown as their file type.
5. Go back to the folder **containing** `bin`. Move that whole folder to a permanent location where you will not delete it. For example, you can move it into `C:\ffmpeg`. Keep all its files and subfolders together.
6. Open the moved folder, then open its **`bin`** folder again. Click the address bar at the top of File Explorer and press **Ctrl+C**. You have now copied the path to `bin`. It might look like `C:\ffmpeg\ffmpeg-9.0.2-essentials_build\bin`, but use the path shown on **your** PC.
7. Click the **Windows logo** on the taskbar, usually at the bottom of the screen. Or press the **Windows-logo key** on your keyboard. Type `environment variables`.
8. In the search results, click **Edit environment variables for your account**.
9. Under **User variables**, click **Path** once, then click **Edit**. In the next window, click **New** and paste the `bin` path you copied. **Do not delete or replace any existing Path entries.**
10. Click **OK** to close each window.
11. Open a **new Command Prompt**: click the Windows logo, type `cmd`, and press **Enter**. If a Command Prompt was already open, close it first.
12. Type these commands one at a time, pressing **Enter** after each:

    ```bat
    ffmpeg -version
    ffprobe -version
    ```

If **both** commands display version information, FFmpeg is ready. If either says **“not recognized,”** check that the Path entry points to the `bin` folder containing both `.exe` files. After correcting it, close Command Prompt, open a new one, and try the two commands again.

**Do not run `setup-windows.cmd` until both commands work.**

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

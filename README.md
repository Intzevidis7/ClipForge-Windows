# ClipForge for Windows — setup guide

ClipForge is a local browser app that turns videos into candidate short clips. You can review the clips and correct captions before burning a karaoke-style version. This repository contains **Python source**, not a prebuilt Windows `.exe`.

## 1. Download this project

On the GitHub repository page, click **Code → Download ZIP**. Extract the ZIP somewhere easy to find, such as `C:\ClipForge-Windows`. Open that extracted folder; `setup-windows.cmd` and `run-windows.cmd` should be beside `app.py`, `main.py`, `scorer.py`, `caption_editor.py`, and `requirements.txt`.

If you already downloaded the repository as a ZIP, **extract it first**. Do not run the `.cmd` files from inside the ZIP preview.

## 2. Install Python 3.12

1. Open the official [Python 3.12.10 release page](https://www.python.org/downloads/release/python-31210/).
2. Scroll to **Files → Windows → Windows installer (64-bit)**. Download and run that installer. Do not choose the embeddable package, source tarball, or 32-bit installer.
3. On the installer's first page, tick **Add python.exe to PATH** and leave the **Python launcher / py launcher** option enabled. Then click **Install Now** and finish the installer.
4. Open a **new Command Prompt** (Start menu → type `cmd` → Enter) and type:

```bat
py -3.12 --version
```

It must show `Python 3.12.x`. If `py` is not recognized, rerun the Python installer and enable the Python launcher. A newer Python already installed on your PC does **not** replace this requirement.

## 3. Install FFmpeg

1. Open the [Gyan FFmpeg builds page](https://www.gyan.dev/ffmpeg/builds/). This build provider is linked by the [official FFmpeg download page](https://ffmpeg.org/download.html).
2. In **Release builds**, download `ffmpeg-release-essentials.zip` (the ZIP, not the 7z archive). Its essentials build includes libass and libx264, which this app needs for captions and MP4 export.
3. Extract the ZIP in File Explorer. Open the extracted folder, then its `bin` subfolder. Confirm you can see `ffmpeg.exe` and `ffprobe.exe`.
4. Move the extracted folder to a permanent location, for example `C:\ffmpeg`. The exact `bin` path may be `C:\ffmpeg\ffmpeg-<version>-essentials_build\bin`; use the folder that **actually contains** `ffmpeg.exe` rather than guessing.
5. Add that `bin` folder to your **user PATH**: press Start, search **Edit environment variables for your account**, open it, select **Path** under *User variables*, click **Edit → New**, paste the full `bin` folder path, then click **OK** on every window.
6. Open a **new Command Prompt** and test:

```bat
ffmpeg -version
ffprobe -version
ffmpeg -hide_banner -filters | findstr ass
```

The first two commands must print version information. The last should show the `ass` filter for karaoke captions. If a command says “not recognized,” recheck the `bin` path and open a new terminal after changing PATH.

## 4. Install Ollama

1. Open the official [Ollama Windows download page](https://ollama.com/download/windows) and choose **Download for Windows**.
2. Run the downloaded installer. After it finishes, open a **new Command Prompt** and check:

```bat
ollama --version
ollama list
```

If `ollama` is not recognized, launch Ollama from the Start menu, then reopen Command Prompt. The setup script will download `llama3.2:3b` if it is not already installed, so you need internet access for the first setup. Ollama runs locally in the background on Windows.

## 5. Run ClipForge setup

Return to the extracted ClipForge folder in File Explorer and **double-click `setup-windows.cmd`**. Keep its Command Prompt window open and read the output. It checks the three programs above, creates `venv\`, installs the project's Python packages, tests them, and pulls the local Ollama model if missing.

This can take a while on the first run. It does **not** silently install Python, FFmpeg, GPU drivers, or Ollama. If it reports a missing prerequisite, complete that section above and run it again.

When it says **Setup complete**, double-click **`run-windows.cmd`**. If a browser tab does not open, visit [http://127.0.0.1:7860](http://127.0.0.1:7860). Leave the Command Prompt window open while using the app; press `Ctrl+C` to stop it.

## 6. Create and review clips

- Upload a video, or paste its local path, such as `C:\Users\YourName\Videos\stream.mp4`. For a large file, pasting the path avoids an extra browser-upload copy.
- Press **Generate clips** and watch the activity log.
- Select and preview each candidate; the AI may choose weak moments, so review before publishing.
- Click **Load editable captions**, correct the Greek text and `start`/`end` seconds in the JSON editor, choose a font, and click **Render corrected captions**. That produces a separate `_karaoke.mp4`; it does not overwrite the original clip.

Caption word timing is **estimated** from phrase-level transcript timings, so adjust cue boundaries when the karaoke sweep is off. Use a font with Greek glyphs. Your first Whisper model download also requires internet.

## Troubleshooting

| Problem | What to check |
|---|---|
| `py -3.12` not recognized | Install the Python 3.12 **64-bit installer** with the py launcher; reopen Command Prompt. |
| `ffmpeg` or `ffprobe` not recognized | Add the extracted FFmpeg `bin` directory to your user PATH; reopen Command Prompt. |
| `ollama` not recognized or not running | Install/launch Ollama, then open a new Command Prompt. |
| Python package installation fails | Keep Python 3.12; the script installs binary wheels rather than compiling PyAV against a system FFmpeg. |
| Caption render fails | Check `ffmpeg -hide_banner -filters | findstr ass` and try a short clip first. |
| No useful clips | Inspect the saved `transcript.srt`; automatic scores are only suggestions. |

The project stores generated clips, SRT transcripts, and scoring cache in `clips\` next to the source code. Do **not** include `clips\`, videos, or `venv\` when sharing the repository.

## Hardware and testing status

Whisper may use NVIDIA CUDA **only** when a compatible CTranslate2 CUDA/cuDNN runtime is installed; otherwise it should use CPU. Ollama handles its own NVIDIA/AMD GPU selection—check `ollama ps` during scoring. The AMD RX 6600 Linux systemd workaround is not a Windows setup step.

These launchers were prepared for Windows but the complete app has **not yet been end-to-end tested on a Windows PC**. Test one short video and one caption render before relying on it for long recordings.

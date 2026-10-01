# ClipForge for Windows (source build)

ClipForge runs as a local browser app on Windows. It transcribes videos with faster-whisper, asks local Ollama to pick candidate moments, exports MP4 clips with FFmpeg, and lets you edit captions before burning a karaoke-captioned copy. This is **not** a prebuilt `.exe`: setup creates a fresh Python environment on the Windows PC.

## Required files

Copy the **working** project source files into one folder:

```text
app.py
caption_editor.py
main.py
scorer.py
transcriber.py
clip_exporter.py
scene_detector.py
requirements.txt
setup-windows.cmd
run-windows.cmd
README-WINDOWS.md
```

Use the resumable `main.py` that loads existing transcripts and the indexed-line `scorer.py`. Do not copy the Linux `venv/` or `clips/` folder into a public repo, and do not copy Python virtual environments between PCs.

## Before setup

1. Install **Python 3.12 (64-bit)** with the Windows `py` launcher from [python.org](https://www.python.org/downloads/). A newer default Python does not replace the need for Python 3.12 for this project's pinned PyAV dependency.
2. Install [FFmpeg for Windows](https://ffmpeg.org/download.html). Put its `bin` folder, containing `ffmpeg.exe` and `ffprobe.exe`, on your PATH. Reopen the terminal after changing PATH. The build must support `libx264`, `aac`, and `ass`/libass for karaoke captions.
3. Install [Ollama for Windows](https://ollama.com/download/windows) and start it. Setup will pull `llama3.2:3b` if missing. This is a separate application, not bundled into ClipForge.
4. Have an internet connection for initial package and model downloads and enough disk space for the source video, output clips, and AI models.

In **Command Prompt**, check:

```bat
py -3.12 --version
ffmpeg -version
ffprobe -version
ollama list
```

If you see 'not recognized', install that prerequisite or reopen Command Prompt so updated PATH is loaded.

## Install and run

Open the project folder in File Explorer. Double-click `setup-windows.cmd` once. It creates `venv\` with Python 3.12, installs the packages from `requirements.txt`, tests imports, checks FFmpeg, and pulls `llama3.2:3b` if needed. It does not edit GPU drivers or install Python/FFmpeg/Ollama silently.

Then double-click `run-windows.cmd`. If no browser tab opens, visit [http://127.0.0.1:7860](http://127.0.0.1:7860). Keep the Command Prompt window open while working. Close it or press Ctrl+C to stop the app.

Alternatively, in Command Prompt:

```bat
cd /d C:\path\to\clipforge
setup-windows.cmd
run-windows.cmd
```

The script invokes `venv\Scripts\python.exe` directly, so you do **not** need to activate the venv or change PowerShell execution policy.

## Using videos and captions

- Upload video files, or paste a local Windows path such as `C:\Users\You\Videos\recording.mp4` into the path box. For large videos, paste a local path to avoid making an extra browser upload copy.
- Press **Generate clips**, then preview each result. One video is processed at a time.
- Select a generated clip, press **Load editable captions**, and correct the caption JSON. Start/end values are seconds relative to the selected clip.
- Choose a font and press **Render corrected captions**. The original clip remains unchanged; edited SRT/ASS and a separate karaoke MP4 are saved next to it.
- An existing `transcript.srt` and scored chunk cache are reused on reruns. The first Whisper model download requires internet.

### Karaoke limitations

The saved SRT contains phrase timestamps but not Whisper's precise per-word timestamps. Word timing in the karaoke sweep is **estimated**; editing cue times and splitting caption rows can help, but exact sync requires storing original word timestamps in a future version. Pick a font that contains Greek letters. Rendering needs FFmpeg compiled with `ass`/libass. Check:

```bat
ffmpeg -hide_banner -filters | findstr ass
ffmpeg -hide_banner -encoders | findstr libx264
```

## GPU and portability notes

- On a supported NVIDIA system with compatible CUDA/cuDNN libraries, faster-whisper may use CUDA. Otherwise use CPU. The current program's CUDA detection is not a guarantee that a driver-only installation is sufficient.
- On Windows, Ollama independently decides whether NVIDIA or AMD hardware is usable. Check `ollama ps` while scoring; a GPU is not guaranteed for every card/driver combination.
- The Nobara/AMD `HSA_OVERRIDE_GFX_VERSION=10.3.0` systemd override is **Linux-specific**. Do not copy it to Windows.
- Each Windows computer must run setup locally; copying `venv/` from Linux or another PC will fail.

## Troubleshooting

- **Missing imports:** run `setup-windows.cmd` again, then launch with `run-windows.cmd`.
- **FFmpeg not found:** ensure the correct `bin` directory is on PATH and reopen the terminal.
- **Ollama timeout:** ensure the desktop app is running and use `ollama ps`. The scorer can cache successfully completed chunks so you can rerun without retranscribing.
- **Subtitle render failure:** check the `ass` filter and your installed font. Paths with punctuation can be tricky in FFmpeg filters; inspect the app's error details.
- **Weak clips:** inspect `transcript.srt` and review results manually. More generated clips do not necessarily mean better selections.

## Status

The `.cmd` launchers and Python files are **prepared for Windows**, but I have not run the whole app on a real Windows machine here. Treat it as a portable source release that needs a first-run test, particularly for Greek-path caption rendering and specific GPU drivers. Avoid advertising it as a validated Windows executable until you have tested that flow.

# ClipForge — local AI clip maker

A local browser app that turns a video (or several videos) into short candidate clips, lets you review them, correct captions, and render a karaoke-captioned version. Nothing is uploaded to a cloud service by the app. Ollama is contacted at `127.0.0.1:11434` by default. The first setup/model download needs internet.

## Portable Linux installation

**Copy the project source files, not your `venv/`, `clips/`, or downloaded models.** Use the same project folder on each Linux PC, then run the same setup and launch commands; setup checks the machine and creates a fresh environment. This is source portability, **not** a guaranteed single-file application or universal GPU setup.

Required project files:

```text
app.py
caption_editor.py
main.py
scorer.py
transcriber.py
clip_exporter.py
scene_detector.py
requirements.txt
setup-linux.sh
run-linux.sh
README.md
```

Use the latest working `main.py` (the one that reuses `transcript.srt`) and `scorer.py` (the one that selects *numbered transcript lines*). Do not replace those with the old timestamp-guessing versions.

### Prepare each Linux computer once

1. Install Python 3.12 with `venv`, `ffmpeg`/`ffprobe`, and `curl` with your distribution's package manager. Install Ollama from its official Linux instructions. Fedora/Nobara, Ubuntu/Debian, and Arch have different package names; the setup script checks availability but does **not** install system packages or edit drivers.
2. Place all project files above in a directory and run:

```bash
cd /path/to/clipforge
bash setup-linux.sh
```

The script chooses Python 3.12, then 3.11, then 3.10 (if installed), builds or reuses `venv/`, installs only prebuilt Python wheels, tests imports, checks FFmpeg and Ollama, and offers to pull `llama3.2:3b` when the Ollama API is available. If setup cannot find a wheel, use Python 3.12. To choose another interpreter explicitly:

```bash
CLIPFORGE_PYTHON=/path/to/python3.12 bash setup-linux.sh
```

Existing environments with a different version of Python must be renamed first (for example `mv venv venv.old`) before running setup again. Do not copy an existing venv from another PC.

Start the frontend:

```bash
bash run-linux.sh
```

Open [http://127.0.0.1:7860](http://127.0.0.1:7860) if the browser does not open. Stop the terminal process with `Ctrl+C`.

### Example system dependencies

```bash
# Debian/Ubuntu: install the correct venv package for your Python version.
sudo apt update
sudo apt install ffmpeg curl python3.12 python3.12-venv

# Nobara/Fedora: check first because another FFmpeg package may already be present.
ffmpeg -version
sudo dnf install python3.12 python3-pip curl

# Arch Linux: use your distro repositories or another trusted Python 3.12 provider.
sudo pacman -S ffmpeg curl
```

Do not force a `dnf` FFmpeg swap if `ffmpeg -version` already works. On Arch, the default `python` may be newer than 3.12; use `CLIPFORGE_PYTHON` with an installed 3.12 interpreter if binary wheel compatibility fails.

## GPU behavior

Whisper and Ollama are separate processes. Standard faster-whisper automatically attempts NVIDIA CUDA when CTranslate2 sees a device; working CUDA/cuDNN libraries are still required, and if the CUDA runtime is incomplete model loading can fail rather than fall back. AMD RX 6600 normally runs standard faster-whisper on CPU. Ollama manages LLM acceleration independently; inspect `ollama ps` while scoring. Some AMD cards require ROCm-specific configuration; do **not** put an RX 6600-specific `HSA_OVERRIDE_GFX_VERSION` override on all systems.

Verify Whisper on an NVIDIA computer:

```bash
venv/bin/python -c "import ctranslate2; print('CUDA devices:', ctranslate2.get_cuda_device_count())"
```

Verify Ollama:

```bash
ollama ps
```

## Use the browser app

1. Upload one or more videos, or paste full local paths (one per line). For a very large file, paste a path to avoid an additional browser-upload copy.
2. Choose transcription model, clip count, minimum score, and optional 9:16 crop; click **Generate clips**.
3. Follow the activity log and select a clip to preview it. Automatic selections may include weak content; review before publishing.
4. Click **Load editable captions** for the selected clip. Edit JSON rows with `start`/`end` in seconds *relative to the clip* and corrected Greek text.
5. Choose an installed font, enable karaoke highlight, and click **Render corrected captions**. A separate `clip_XX_karaoke.mp4` is produced; the original MP4 is not changed.

Example caption JSON:

```json
[
  {"start": 0.0, "end": 1.8, "text": "Γεια σας παιδιά"},
  {"start": 1.8, "end": 3.4, "text": "τι κάνετε σήμερα;"}
]
```

Captions have a font outline with **no background box**. FFmpeg must have the `ass`/libass filter; the setup script warns if it is missing. The existing `transcript.srt` stores phrase-level timings, so word timing for karaoke is estimated and may need manual cue adjustment. For precise per-word alignment, a future version must preserve original Whisper word timestamps separately.

## CLI and cache

```bash
source venv/bin/activate
python main.py '/home/user/Videos/my stream!.mp4' --whisper-model medium --language el --llm-model llama3.2:3b --max-clips 8 --min-score 7
```

Use single quotes in Bash for filenames with spaces or exclamation marks. The resumable CLI writes `clips/<video name>/transcript.srt`, `scoring_cache/`, `clip_XX.mp4`, and `report.json`. Repeat runs reuse transcripts and completed scoring chunks. `--retry-failed` retries failed chunks; `--retranscribe` discards the reuse of the existing SRT on that run. Do not delete `transcript.srt` or `scoring_cache/` just to remove unwanted clips. You may delete unwanted clip MP4s, but `report.json` can still refer to them until a new run is made.

## Troubleshooting

- **`ModuleNotFoundError`:** run `bash setup-linux.sh`, then launch with `bash run-linux.sh`; use `venv/bin/python -m pip`, not a different system `pip`.
- **Ollama connection error:** check `ollama ps`, `systemctl status ollama`, and `ollama pull llama3.2:3b`.
- **No clips:** inspect `transcript.srt`, then `report.json` and `scoring_cache/`. A smaller LLM can return overly generous scores or bad selections; lowering the score threshold does not improve quality.
- **Scene detection crash:** the CLI can skip scene snapping. It does not block scoring or clip rendering.
- **Caption rendering fails:** verify `ffmpeg -hide_banner -filters | grep -E '[[:space:]]ass[[:space:]]'`, check that a font containing Greek glyphs is installed, and inspect the returned FFmpeg error.
- **Old files:** keep `clips/` if you want resume support; remove only clips you no longer need.

## Current limitations

The current frontend shows the most recently processed video's clips. It has a manual review/edit step, not a hands-free publishing workflow. Setup uses binary wheels only for reliability; a distro/CPU architecture with no compatible wheel may need a separate supported build. This distribution has not been end-to-end tested on every Linux distribution, GPU, or FFmpeg build.

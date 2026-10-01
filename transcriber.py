"""Local speech-to-text with word-level timestamps using faster-whisper."""
from dataclasses import dataclass
from typing import List, Optional
import os
import sys
import time


@dataclass
class Word:
    start: float
    end: float
    text: str


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: List[Word]


def transcribe(video_path: str, model_size: str = "small", device: str = "auto",
               language: Optional[str] = None) -> List[Segment]:
    """Transcribe a video/audio file. Returns list of Segment with word timings."""
    from faster_whisper import WhisperModel

    if device == "auto":
        device = "cpu"
        try:
            import ctranslate2
            if ctranslate2.get_cuda_device_count() > 0:
                device = "cuda"
        except Exception:
            pass

    compute_type = "float16" if device == "cuda" else "int8"
    print(f"  Loading whisper '{model_size}' model ({device}, {compute_type})...", flush=True)
    t0 = time.time()
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    print(f"  Model loaded in {time.time()-t0:.1f}s.", flush=True)

    print("  Scanning audio for speech (VAD pass)... this can take 1-2 min on large files with no output, please wait.", flush=True)
    t0 = time.time()
    segments_iter, info = model.transcribe(
        video_path,
        language=language,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    total_duration = info.duration if info and info.duration else None
    print(f"  VAD scan done in {time.time()-t0:.1f}s.", flush=True)
    if total_duration:
        print(f"  Audio duration: {total_duration/60:.1f} min. Transcribing...", flush=True)
    else:
        print("  Transcribing (duration unknown)...", flush=True)

    segments: List[Segment] = []
    bar_width = 40
    last_pct = -1
    last_print_time = time.time()
    for seg in segments_iter:
        words = [Word(w.start, w.end, w.word.strip()) for w in (seg.words or [])]
        segments.append(Segment(start=seg.start, end=seg.end, text=seg.text.strip(), words=words))

        now = time.time()
        if total_duration:
            pct = min(int((seg.end / total_duration) * 100), 100)
            if pct != last_pct or now - last_print_time > 5:
                last_pct = pct
                last_print_time = now
                filled = int(bar_width * pct / 100)
                bar = "#" * filled + "-" * (bar_width - filled)
                sys.stdout.write(f"\r  [{bar}] {pct:3d}%  ({seg.end/60:.1f}/{total_duration/60:.1f} min)")
                sys.stdout.flush()
        else:
            if now - last_print_time > 2:
                last_print_time = now
                sys.stdout.write(f"\r  Transcribed up to {seg.end/60:.1f} min...")
                sys.stdout.flush()

    print()
    return segments


def _srt_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(segments: List[Segment], out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{_srt_timestamp(seg.start)} --> {_srt_timestamp(seg.end)}\n")
            f.write(f"{seg.text}\n\n")


def write_clip_srt(segments: List[Segment], clip_start: float, clip_end: float, out_path: str) -> None:
    idx = 1
    with open(out_path, "w", encoding="utf-8") as f:
        for seg in segments:
            if seg.end < clip_start or seg.start > clip_end:
                continue
            words = seg.words if seg.words else None
            if words:
                chunk = []
                for w in words:
                    if w.start < clip_start or w.end > clip_end:
                        continue
                    chunk.append(w)
                    if len(chunk) >= 6:
                        s = chunk[0].start - clip_start
                        e = chunk[-1].end - clip_start
                        text = " ".join(c.text for c in chunk)
                        f.write(f"{idx}\n{_srt_timestamp(max(s,0))} --> {_srt_timestamp(max(e,0))}\n{text}\n\n")
                        idx += 1
                        chunk = []
                if chunk:
                    s = chunk[0].start - clip_start
                    e = chunk[-1].end - clip_start
                    text = " ".join(c.text for c in chunk)
                    f.write(f"{idx}\n{_srt_timestamp(max(s,0))} --> {_srt_timestamp(max(e,0))}\n{text}\n\n")
                    idx += 1
            else:
                s = max(seg.start - clip_start, 0)
                e = max(seg.end - clip_start, 0)
                f.write(f"{idx}\n{_srt_timestamp(s)} --> {_srt_timestamp(e)}\n{seg.text}\n\n")
                idx += 1

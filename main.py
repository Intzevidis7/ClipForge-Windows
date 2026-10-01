#!/usr/bin/env python3
"""Local clip maker: resume from SRT and per-chunk Ollama cache."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from transcriber import Segment, transcribe, write_srt, write_clip_srt
from scorer import score_moments, dedupe_overlapping
from clip_exporter import export_clip

TIMING = re.compile(r"^(\d{2,}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2,}):(\d{2}):(\d{2}),(\d{3})$")


def load_srt(path: Path):
    def seconds(groups):
        h, m, s, ms = map(int, groups)
        return h * 3600 + m * 60 + s + ms / 1000

    segments = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8-sig").strip()):
        lines = block.splitlines()
        for i, line in enumerate(lines):
            match = TIMING.match(line.strip())
            if match:
                start, end = seconds(match.groups()[:4]), seconds(match.groups()[4:])
                text = " ".join(x.strip() for x in lines[i + 1:] if x.strip())
                if end > start and text:
                    segments.append(Segment(start=start, end=end, text=text, words=[]))
                break
    if not segments:
        raise ValueError(f"No subtitles parsed from {path}; refusing to retranscribe silently")
    return segments


def duration_of(video: Path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
                            capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def run_video(video: Path, args):
    if not video.is_file():
        raise FileNotFoundError(video)
    video = video.resolve()
    out = Path(args.out_dir).expanduser().resolve() / video.stem
    out.mkdir(parents=True, exist_ok=True)
    srt = out / "transcript.srt"
    print(f"\nProcessing: {video.name}", flush=True)
    if srt.is_file() and srt.stat().st_size and not args.retranscribe:
        print(f"[1/3] Reusing {srt} (no Whisper run)", flush=True)
        segments = load_srt(srt)
        print(f"  Loaded {len(segments)} subtitle segments", flush=True)
    else:
        print("[1/3] Transcribing...", flush=True)
        segments = transcribe(str(video), model_size=args.whisper_model, device=args.device,
                              language=args.language)
        if not segments:
            raise RuntimeError("No speech detected")
        write_srt(segments, str(srt))
        print(f"  Saved {srt}", flush=True)

    print("[2/3] Scoring with Ollama (saved after each chunk)...", flush=True)
    candidates = score_moments(segments, args.min_clip_len, args.max_clip_len,
                               llm_model=args.llm_model, ollama_host=args.ollama_host,
                               min_score=args.min_score, timeout=args.llm_timeout,
                               cache_dir=out / "scoring_cache", retry_failed=args.retry_failed)
    if not candidates:
        print("No valid candidates yet. Inspect scoring_cache; retry with --retry-failed if needed.")
        return
    chosen = dedupe_overlapping(candidates, args.max_clips)
    video_end = duration_of(video)
    report = []
    print(f"[3/3] Exporting {len(chosen)} clips...", flush=True)
    for i, c in enumerate(chosen, 1):
        start = max(0.0, min(c.start, video_end))
        end = min(c.end, video_end)
        if end - start < args.min_clip_len:
            end = min(video_end, start + args.min_clip_len)
        if end - start > args.max_clip_len:
            end = start + args.max_clip_len
        if end <= start:
            continue
        target = out / f"clip_{i:02d}.mp4"
        caption_path = None
        if args.captions:
            caption_path = out / f"clip_{i:02d}.srt"
            write_clip_srt(segments, start, end, str(caption_path))
        try:
            export_clip(str(video), start, end, str(target), vertical=args.vertical,
                        srt_path=str(caption_path) if caption_path else None)
            print(f"  [{i}/{len(chosen)}] {target.name}: {start:.1f}-{end:.1f}s", flush=True)
        except Exception as exc:
            print(f"  [{i}/{len(chosen)}] Failed: {exc}", flush=True)
            continue
        report.append({"file": target.name, "start": round(start, 2), "end": round(end, 2),
                       "title": c.title, "score": c.score, "reason": c.reason,
                       "transcript": c.text})
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Done: {out} ({len(report)} clips)")


def main():
    p = argparse.ArgumentParser(description="Local AI clip maker with resumable scoring")
    p.add_argument("videos", nargs="+", type=Path)
    p.add_argument("--out-dir", default="clips")
    p.add_argument("--whisper-model", default="small")
    p.add_argument("--language", default=None)
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    p.add_argument("--llm-model", default="llama3.2:3b")
    p.add_argument("--ollama-host", default="http://localhost:11434")
    p.add_argument("--llm-timeout", type=int, default=300)
    p.add_argument("--min-clip-len", type=float, default=15)
    p.add_argument("--max-clip-len", type=float, default=60)
    p.add_argument("--max-clips", type=int, default=15)
    p.add_argument("--min-score", type=float, default=6)
    p.add_argument("--captions", action="store_true")
    p.add_argument("--vertical", action="store_true")
    p.add_argument("--retry-failed", action="store_true", help="Retry chunks that failed on a previous run")
    p.add_argument("--retranscribe", action="store_true", help="Ignore existing SRT and run Whisper again")
    args = p.parse_args()
    if args.min_clip_len <= 0 or args.max_clip_len < args.min_clip_len or args.max_clips < 1:
        p.error("Check clip duration and max-clips arguments")
    for name in ("ffmpeg", "ffprobe"):
        if not shutil.which(name):
            p.error(f"{name} is not on PATH")
    for video in args.videos:
        try:
            run_video(video, args)
        except Exception as exc:
            print(f"ERROR for {video}: {exc}", flush=True)


if __name__ == "__main__":
    main()

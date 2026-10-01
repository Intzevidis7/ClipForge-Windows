"""Cuts final clips with ffmpeg, with optional 9:16 crop and burned-in captions."""
import os
import subprocess
from typing import Optional


def _ffprobe_dimensions(video_path: str):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", video_path],
        capture_output=True, text=True, check=True,
    )
    w, h = out.stdout.strip().split(",")
    return int(w), int(h)


def export_clip(src_path: str, start: float, end: float, out_path: str,
                 vertical: bool = False, srt_path: Optional[str] = None) -> None:
    duration = max(end - start, 0.5)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    vf_filters = []
    if vertical:
        w, h = _ffprobe_dimensions(src_path)
        target_h = h
        target_w = int(round(target_h * 9 / 16))
        if target_w > w:
            target_w = w
            target_h = int(round(target_w * 16 / 9))
        vf_filters.append(f"crop={target_w}:{target_h}:(in_w-{target_w})/2:(in_h-{target_h})/2")

    if srt_path and os.path.exists(srt_path):
        escaped = srt_path.replace(":", "\\:").replace("'", "\\'")
        vf_filters.append(
            f"subtitles='{escaped}':force_style="
            "'FontName=DejaVu Sans,FontSize=14,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BorderStyle=3,Outline=2,Alignment=2,MarginV=60'"
        )

    cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", src_path, "-t", f"{duration:.3f}"]

    if vf_filters:
        cmd += ["-vf", ",".join(vf_filters)]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k"]

    cmd += [out_path]
    subprocess.run(cmd, check=True, capture_output=True)

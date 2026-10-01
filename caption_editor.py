"""Editable pre-burn captions and ASS karaoke export for locally generated clips."""
import json
import math
import re
import subprocess
from pathlib import Path

TIME = re.compile(r"^(\d+):(\d{2}):(\d{2}),(\d{3}) --> (\d+):(\d{2}):(\d{2}),(\d{3})$")
FONTS = ("DejaVu Sans", "Liberation Sans", "Noto Sans", "Noto Sans Greek")


def read_srt(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing subtitle file: {path}")
    result = []
    content = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    for block in re.split(r"\n\s*\n", content.strip()):
        lines = block.splitlines()
        for n, line in enumerate(lines):
            m = TIME.match(line.strip())
            if not m:
                continue
            a = list(map(int, m.groups()))
            start = 3600*a[0] + 60*a[1] + a[2] + a[3]/1000
            end = 3600*a[4] + 60*a[5] + a[6] + a[7]/1000
            text = " ".join(part.strip() for part in lines[n+1:] if part.strip())
            if end > start and text:
                result.append({"start": start, "end": end, "text": text})
            break
    return result


def write_srt(items, path):
    def fmt(t):
        t = round(t*1000)
        h, t = divmod(t, 3600000)
        m, t = divmod(t, 60000)
        s, t = divmod(t, 1000)
        return f"{h:02}:{m:02}:{s:02},{t:03}"
    Path(path).write_text("".join(
        f"{i}\n{fmt(item['start'])} --> {fmt(item['end'])}\n{item['text']}\n\n"
        for i, item in enumerate(items, 1)), encoding="utf-8")


def clip_words(transcript, start, end):
    words = []
    for seg in transcript:
        if seg["end"] <= start or seg["start"] >= end:
            continue
        pieces = seg["text"].split()
        if not pieces:
            continue
        a, b = max(seg["start"], start), min(seg["end"], end)
        if b <= a:
            continue
        # SRT contains segment timings only. Word timings here are estimates.
        for idx, piece in enumerate(pieces):
            left = a + (b-a)*idx/len(pieces) - start
            right = a + (b-a)*(idx+1)/len(pieces) - start
            if right > left:
                words.append((left, right, piece))
    return words


def draft_cues(words, group=4):
    return [{"start": group_words[0][0], "end": group_words[-1][1],
             "text": " ".join(x[2] for x in group_words)}
            for pos in range(0, len(words), group)
            if (group_words := words[pos:pos+group])]


def parse_editor(text, duration):
    try:
        rows = json.loads(text)
    except ValueError as exc:
        raise ValueError("Captions must be valid JSON. Keep the [ ... ] and double quotes.") from exc
    if not isinstance(rows, list) or len(rows) > 500:
        raise ValueError("Expected a JSON list of no more than 500 caption rows.")
    cues = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Every caption must be an object with start, end and text.")
        try:
            a, b = float(row["start"]), float(row["end"])
            text_value = str(row["text"]).strip()
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Every row needs numeric start/end and text.") from exc
        if not math.isfinite(a) or not math.isfinite(b) or a < 0 or b <= a or b > duration + .1:
            raise ValueError(f"Invalid cue time: {a}–{b}; clip length is {duration:.2f}s")
        if not text_value or len(text_value) > 180:
            raise ValueError("Caption text must be 1–180 characters.")
        cues.append({"start": round(a, 3), "end": round(b, 3), "text": text_value})
    cues.sort(key=lambda x: x["start"])
    if any(a["end"] > b["start"] + 0.05 for a, b in zip(cues, cues[1:])):
        raise ValueError("Caption rows overlap; adjust their times before rendering.")
    return cues


def clock(t):
    t = max(0, round(t*100))
    h, t = divmod(t, 360000)
    m, t = divmod(t, 6000)
    s, t = divmod(t, 100)
    return f"{h}:{m:02}:{s:02}.{t:02}"


def ass_escape(text):
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", " ")


def make_ass(cues, original_words, path, width, height, font, karaoke=True):
    if font not in FONTS:
        raise ValueError("Choose a font from the menu.")
    w, h = max(2, width//2*2), max(2, height//2*2)
    font_size = max(22, round(h*.053))
    margin = max(24, round(h*.09))
    # ASS colors are &HAABBGGRR, with 00 opacity meaning opaque.
    header = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
              "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
              f"Style: Main,{font},{font_size},&H0000EFFF,&H00FFFFFF,&H000C0C0C,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,25,25,{margin},1\n\n"
              "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    lines=[]
    for cue in cues:
        text = cue["text"]
        tokens = text.split()
        orig = [x for x in original_words if x[1] > cue["start"] and x[0] < cue["end"]]
        use_k = karaoke and orig and len(tokens) == len(orig)
        if use_k:
            # Corrected words preserve existing estimated word positions by index.
            cs = round(cue["start"]*100)
            parts=[]
            for i, token in enumerate(tokens):
                boundary = round((min(cue["end"], orig[i+1][0]) if i+1<len(orig) else cue["end"])*100)
                delay = max(1, boundary-cs)
                parts.append("{\\kf"+str(delay)+"}"+ass_escape(token)+( " " if i<len(tokens)-1 else ""))
                cs += delay
            content="".join(parts)
        elif karaoke and tokens:
            # Changed word counts cannot be aligned to lost word timestamps.
            total=max(1,round((cue["end"]-cue["start"])*100))
            positions=[round(total*i/len(tokens)) for i in range(len(tokens)+1)]
            content="".join("{\\kf"+str(max(1,positions[i+1]-positions[i]))+"}"+ass_escape(token)+( " " if i<len(tokens)-1 else "") for i,token in enumerate(tokens))
        else:
            content=ass_escape(text)
        lines.append(f"Dialogue: 0,{clock(cue['start'])},{clock(cue['end'])},Main,,0,0,0,,{content}\n")
    Path(path).write_text(header+"".join(lines),encoding="utf-8")


def dimensions(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],capture_output=True,text=True,check=True)
    w,h = result.stdout.strip().split(",")
    return int(w),int(h)


def burn_clip(source, dest, ass_path):
    # Use ffmpeg's ass filter; cwd avoids escaping Greek paths, quotes and punctuation in filter args.
    source, dest, ass_path = Path(source).resolve(),Path(dest).resolve(),Path(ass_path).resolve()
    result = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", str(source),
                             "-vf", "ass=filename=captions.ass", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
                             "-c:a", "copy", str(dest)], cwd=ass_path.parent,capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-2400:])

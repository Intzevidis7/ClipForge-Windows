#!/usr/bin/env python3
"""Local clip maker web frontend and editable karaoke captions."""
import json
import queue
import subprocess
import sys
import threading
from html import escape
from pathlib import Path

import gradio as gr
from caption_editor import (read_srt, clip_words, draft_cues, parse_editor,
                            make_ass, dimensions, burn_clip, FONTS)

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "clips"
EXT = {".mp4", ".mkv", ".mov", ".webm", ".avi"}
CSS = """
body,.gradio-container{background:radial-gradient(circle at 15% 0%,#26365b 0%,transparent 38%),radial-gradient(circle at 88% 8%,#164047 0%,transparent 34%),#0a1120!important;color:#edf4ff!important}
.gradio-container{max-width:1220px!important;margin:auto!important;padding:32px 20px 80px!important;font-family:Inter,ui-sans-serif,system-ui,sans-serif!important}
#hero{padding:38px 36px;border-radius:26px;background:linear-gradient(112deg,#292e53,#18283c 60%,#154843);border:1px solid #ffffff24;box-shadow:0 20px 45px #0005;margin-bottom:20px}
#hero small{font-weight:800;letter-spacing:.18em;color:#79edd6}#hero h1{font-size:clamp(2rem,5vw,3.5rem);letter-spacing:-.05em;line-height:1.1;margin:14px 0;color:#fff}#hero p{color:#c1d0e4;font-size:1.06rem;max-width:640px}#hero span{display:inline-block;background:#54e9cb20;border:1px solid #54e9cb55;color:#95efde;padding:7px 13px;border-radius:100px;margin-top:12px;font-size:.8rem;font-weight:750}
#inputs,#processing,#results,#captions{background:#121d31e8;border:1px solid #ffffff1d;padding:24px!important;border-radius:22px;margin-bottom:18px;box-shadow:0 14px 35px #0004}
.section h2{font-size:1.35rem;color:#fff;margin:0 0 2px}.section p{color:#aabbd3;margin:0 0 18px}
#go,#render{min-height:52px!important;background:linear-gradient(100deg,#48dfbb,#6ea8ff)!important;color:#071b2d!important;font-weight:850!important;border:0!important;border-radius:13px!important;font-size:1.04rem!important}#go:hover,#render:hover{filter:brightness(1.12)}
#log textarea{font-family:ui-monospace,monospace!important;font-size:.83rem!important;color:#b8f2da!important}
#footer{text-align:center;color:#94a9c5;font-size:.84rem;padding:18px}
"""


def inputs(files, paths):
    videos=[]
    for item in files or []:
        videos.append(Path(item if isinstance(item,str) else item.name).expanduser().resolve())
    for row in (paths or "").splitlines():
        text=row.strip().strip('"').strip("'")
        if text:
            path=Path(text).expanduser()
            videos.append((path if path.is_absolute() else ROOT/path).resolve())
    videos=list(dict.fromkeys(videos))
    if not videos:
        raise ValueError("Upload a video or paste a local file path.")
    for path in videos:
        if not path.is_file() or path.suffix.lower() not in EXT:
            raise ValueError(f"Not a supported video file: {path}")
    return videos


def results(video):
    folder=OUTPUTS/video.stem
    report=folder/"report.json"
    if not report.is_file():
        return [],[],"No report was produced. Check the log."
    try:
        records=json.loads(report.read_text(encoding="utf-8"))
    except (OSError,ValueError):
        return [],[],"Cannot read report.json."
    menu,files,lines=[],[],[]
    for row in records:
        path=folder/Path(row.get("file","")).name
        if path.is_file() and path.suffix.lower()==".mp4":
            menu.append((f"{path.name} · {row.get('title','Clip')} · {row.get('start','?')}s",str(path)))
            files.append(str(path))
            lines.append(f"{path.name} | {row.get('score','?')}/10 | {row.get('reason','')}")
    return menu,files,"\n".join(lines) if lines else "No clips exported."


def allowed_clip(selected):
    if not selected:
        raise ValueError("Select a generated clip first.")
    path=Path(selected).resolve()
    if not path.is_file() or OUTPUTS.resolve() not in path.parents or path.suffix.lower()!=".mp4":
        raise ValueError("Select a valid original MP4 clip from the dropdown.")
    report=path.parent/"report.json"
    if not report.is_file():
        raise ValueError("Clip report is missing.")
    rows=json.loads(report.read_text(encoding="utf-8"))
    row=next((r for r in rows if r.get("file")==path.name),None)
    if row is None:
        raise ValueError("Clip is not listed in its report.")
    return path,row


def preview(selected):
    if not selected:
        return None
    try:
        return str(allowed_clip(selected)[0])
    except (ValueError,OSError):
        return None


def edit_captions(selected):
    try:
        path,row=allowed_clip(selected)
        transcript=read_srt(path.parent/"transcript.srt")
        start,end=float(row["start"]),float(row["end"])
        word_data=clip_words(transcript,start,end)
        cues=draft_cues(word_data)
        status=("Draft timings estimated from subtitle segments, not aligned word timestamps. "
                "Edit both the Greek text and start/end seconds, then click Render.")
        return json.dumps(cues,ensure_ascii=False,indent=2),status
    except (OSError,ValueError,KeyError,TypeError) as exc:
        return "[]",str(exc)


def render_captions(selected, text, font, karaoke):
    try:
        path,row=allowed_clip(selected)
        transcript=read_srt(path.parent/"transcript.srt")
        duration=float(row["end"])-float(row["start"])
        cues=parse_editor(text,duration)
        if not cues:
            raise ValueError("No captions to render.")
        word_data=clip_words(transcript,float(row["start"]),float(row["end"]))
        width,height=dimensions(path)
        ass=path.parent/(path.stem+"_edited.ass")
        editable=path.parent/(path.stem+"_edited.srt")
        target=path.parent/(path.stem+"_karaoke.mp4")
        make_ass(cues,word_data,ass,width,height,font,karaoke=karaoke)
        from caption_editor import write_srt
        write_srt(cues,editable)
        burn_clip(path,target,ass)
        return str(target),str(target),f"Rendered {len(cues)} captions. Original MP4 was not changed; edited SRT and ASS saved beside it."
    except (OSError,ValueError,KeyError,TypeError,RuntimeError,subprocess.SubprocessError) as exc:
        return None,None,f"Rendering failed: {exc}"


def process(files, paths, model, limit, score, vertical):
    def screen(title,lines,menu,paths,details,active=None):
        return (f"<div style='color:#8df3d5;font-weight:800;padding:8px'>{escape(title)}</div>",
                "\n".join(lines[-120:]),gr.update(choices=menu,value=active),active,
                gr.update(value=paths,visible=bool(paths)),details)
    try:
        videos=inputs(files,paths)
    except ValueError as e:
        yield screen(str(e),[],[],[],"")
        return
    log,menu,paths_out,details=[],[],[],""
    for index,video in enumerate(videos,1):
        log.append(f"Starting {video.name}")
        yield screen(f"Video {index}/{len(videos)} · Starting",log,menu,paths_out,details)
        cmd=[sys.executable,"-u",str(ROOT/"main.py"),str(video),"--llm-model","llama3.2:3b",
             "--whisper-model",model,"--language","el","--max-clips",str(int(limit)),
             "--min-score",str(score),"--out-dir",str(OUTPUTS)]
        if vertical:
            cmd.append("--vertical")
        try:
            worker=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        except OSError as e:
            log.append(f"Start failed: {e}")
            yield screen("Cannot start job",log,menu,paths_out,details)
            continue
        messages=queue.Queue()
        def collect():
            try:
                for line in worker.stdout:
                    messages.put(line.strip())
            finally:
                messages.put(None)
        threading.Thread(target=collect,daemon=True).start()
        done,stage=False,"Working"
        while not done:
            try:
                line=messages.get(timeout=1)
                if line is None:
                    done=True
                elif line:
                    log.append(line)
                    if "Transcrib" in line or "Reusing" in line: stage="Preparing transcript"
                    elif "Scoring" in line: stage="Finding moments"
                    elif "Exporting" in line: stage="Rendering clips"
            except queue.Empty:
                pass
            yield screen(f"Video {index}/{len(videos)} · {stage}",log,menu,paths_out,details)
        rc=worker.wait()
        log.append(f"Finished {video.name} (exit status {rc})")
        menu,paths_out,details=results(video)
        first=menu[0][1] if menu else None
        yield screen(f"Video {index}/{len(videos)} · {'Done' if paths_out else 'No clips generated'}",log,menu,paths_out,details,first)

with gr.Blocks(css=CSS,title="ClipForge | Local AI Studio",theme=gr.themes.Base()) as demo:
    gr.HTML("<div id='hero'><small>LOCAL AI VIDEO STUDIO</small><h1>Long video in.<br>Better moments out.</h1><p>Find and review highlights on your own computer. Correct captions before you burn them in.</p><span>PRIVATE · RUNS ON THIS PC</span></div>")
    with gr.Group(elem_id="inputs"):
        gr.HTML("<div class='section'><h2>01 / Add your video</h2><p>For large videos, paste the local path instead of uploading a copy.</p></div>")
        with gr.Row():
            uploads=gr.File(label="Upload one or more videos",file_count="multiple",file_types=["video"],type="filepath",scale=1)
            paths=gr.Textbox(label="Or paste local paths (one per line)",lines=5,placeholder="/home/antonisi/Videos/stream.mp4",scale=1)
        gr.HTML("<div class='section'><h2>02 / Choose your settings</h2><p>Transcription and clip detection happen before captions are burned.</p></div>")
        with gr.Row():
            model=gr.Dropdown(["small","medium","large-v3"],value="medium",label="Whisper accuracy")
            limit=gr.Slider(1,20,value=8,step=1,label="Maximum clips per video")
            score=gr.Slider(0,10,value=7,step=.5,label="Minimum AI score")
        vertical=gr.Checkbox(label="Center crop original clips to 9:16")
        start=gr.Button("Generate clips",variant="primary",elem_id="go")
    with gr.Group(elem_id="processing"):
        gr.HTML("<div class='section'><h2>03 / Processing</h2><p>Saved transcripts and scoring results are reused.</p></div>")
        phase=gr.HTML("<div style='padding:12px;color:#8df3d5'>Ready for your video.</div>")
        log=gr.Textbox(label="Activity log",lines=10,interactive=False,autoscroll=True,elem_id="log")
    with gr.Group(elem_id="results"):
        gr.HTML("<div class='section'><h2>04 / Review clips</h2><p>Choose and preview each AI suggestion. Captions are not burned yet.</p></div>")
        menu=gr.Dropdown(label="Select a generated clip",choices=[])
        with gr.Row():
            player=gr.Video(label="Original clip preview",scale=2)
            with gr.Column(scale=1):
                details=gr.Textbox(label="Scores and reasons",lines=9,interactive=False)
                downloads=gr.File(label="Generated MP4s",file_count="multiple",visible=False)
    with gr.Group(elem_id="captions"):
        gr.HTML("<div class='section'><h2>05 / Correct &amp; style captions</h2><p>Select a clip above. Edit Greek text and timings, then burn a separate karaoke version. The original remains intact.</p></div>")
        load=gr.Button("Load editable captions")
        editor=gr.Textbox(label="Caption cues · seconds relative to selected clip (edit JSON)",lines=15,
                          placeholder='[{"start": 0.0, "end": 2.0, "text": "Γεια σας"}]')
        with gr.Row():
            font=gr.Dropdown(list(FONTS),value="DejaVu Sans",label="Font (installed font required)")
            karaoke=gr.Checkbox(value=True,label="Karaoke highlight (sweeping words)")
        render=gr.Button("Render corrected captions",elem_id="render")
        caption_status=gr.Textbox(label="Caption status",interactive=False)
        with gr.Row():
            captioned=gr.Video(label="Rendered captioned clip")
            caption_download=gr.File(label="Download captioned MP4")
    gr.HTML("<div id='footer'>Everything runs locally · Generated files live under clips/ · No captions burned until you approve the text</div>")
    start.click(process,[uploads,paths,model,limit,score,vertical],[phase,log,menu,player,downloads,details],concurrency_limit=1)
    menu.change(preview,menu,player)
    load.click(edit_captions,menu,[editor,caption_status])
    render.click(render_captions,[menu,editor,font,karaoke],[captioned,caption_download,caption_status],concurrency_limit=1)

if __name__=="__main__":
    OUTPUTS.mkdir(exist_ok=True)
    demo.queue(default_concurrency_limit=1)
    demo.launch(server_name="127.0.0.1",server_port=7860,share=False,allowed_paths=[str(OUTPUTS)],inbrowser=True,show_error=True)

#!/usr/bin/env python3
"""
studio/server.py – Fast, Local FastAPI Backend for Faceless Shorts Engine Studio.

Exposes REST and SSE endpoints for project management, AI script generation,
audio previewing, pipeline execution, and real-time frame capture monitoring.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

import psutil
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STUDIO_DIR = PROJECT_ROOT / "studio"
PROJECTS_DIR = PROJECT_ROOT / "projects"
ASSETS_DIR = PROJECT_ROOT / "assets"
STYLES_DIR = PROJECT_ROOT / "faceless-shorts" / "styles"

sys.path.insert(0, str(PROJECT_ROOT))
from engine.ai_script import generate_script as ai_generate_script

app = FastAPI(title="Faceless Shorts Engine Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State for Pipeline Execution
class PipelineState:
    running: bool = False
    process: Optional[subprocess.Popen] = None
    project: str = ""
    style: str = ""
    current_frame: int = 0
    total_frames: int = 840
    start_time: float = 0.0
    elapsed_seconds: float = 0.0
    eta_seconds: float = 0.0
    fps: float = 0.0
    logs: List[str] = []

STATE = PipelineState()


# --- Models ---
class ScriptGenRequest(BaseModel):
    topic: str
    style: str = "deep-dive"
    language: str = "en"
    voice: Optional[str] = None
    music: str = "tension"

class ProjectSaveRequest(BaseModel):
    script: Dict[str, Any]

class PipelineRunRequest(BaseModel):
    project: str = "swallow-gum"
    style: str = "deep-dive"
    quality: str = "draft"  # draft or production

class VoiceGenRequest(BaseModel):
    text: str
    voice: str = "am_michael"
    speed: float = 1.0


# --- Endpoints ---

@app.get("/api/system")
def get_system_stats():
    """Returns CPU, RAM, and Storage stats."""
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(str(PROJECT_ROOT))
    return {
        "status": "ready" if not STATE.running else "rendering",
        "cpu_percent": round(cpu, 1),
        "ram_used_gb": round(mem.used / (1024**3), 1),
        "ram_total_gb": round(mem.total / (1024**3), 1),
        "ram_percent": mem.percent,
        "storage_used_gb": round(disk.used / (1024**3), 1),
        "storage_total_gb": round(disk.total / (1024**3), 1),
        "storage_percent": disk.percent,
    }


@app.get("/api/projects")
def list_projects():
    """List all available video projects."""
    projects = []
    if PROJECTS_DIR.exists():
        for d in sorted(PROJECTS_DIR.iterdir()):
            if d.is_dir() and (d / "script.json").exists():
                script_path = d / "script.json"
                try:
                    script = json.loads(script_path.read_text(encoding="utf-8"))
                    title = script.get("title", d.name)
                    style = script.get("style", "deep-dive")
                    voice = script.get("voice", "am_michael")
                    lines = script.get("lines", [])
                    has_video = (d / "renders" / f"{d.name.replace('-', '_')}.mp4").exists() or any((d / "renders").glob("*.mp4"))
                    projects.append({
                        "id": d.name,
                        "title": title,
                        "style": style,
                        "voice": voice,
                        "scene_count": len(lines),
                        "has_render": has_video,
                        "updated_at": script_path.stat().st_mtime,
                    })
                except Exception:
                    continue
    return projects


@app.get("/api/project/{name}")
def get_project(name: str):
    """Retrieve all data for a specific project."""
    p_dir = PROJECTS_DIR / name
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    script_file = p_dir / "script.json"
    lines_file = p_dir / "data" / "lines.json"
    cues_file = p_dir / "data" / "cues.json"
    words_file = p_dir / "data" / "words.json"

    script = json.loads(script_file.read_text(encoding="utf-8")) if script_file.exists() else {}
    lines_data = json.loads(lines_file.read_text(encoding="utf-8")) if lines_file.exists() else {}
    cues = json.loads(cues_file.read_text(encoding="utf-8")) if cues_file.exists() else []
    words = json.loads(words_file.read_text(encoding="utf-8")) if words_file.exists() else []

    # Check for render video
    video_url = None
    renders_dir = p_dir / "renders"
    if renders_dir.exists():
        videos = list(renders_dir.glob("*.mp4"))
        if videos:
            video_url = f"/media/projects/{name}/renders/{videos[0].name}"

    # Check for preview image
    preview_img = "/media/assets/demo/thumb_xray.jpg"
    if (p_dir / "review" / "all.jpg").exists():
        preview_img = f"/media/projects/{name}/review/all.jpg"

    return {
        "id": name,
        "script": script,
        "lines": lines_data.get("lines", []),
        "duration": lines_data.get("duration", 35.0),
        "cues": cues,
        "words": words,
        "video_url": video_url,
        "preview_image": preview_img,
        "has_audio": (p_dir / "data" / "narration.wav").exists(),
        "audio_url": f"/media/projects/{name}/data/narration.wav" if (p_dir / "data" / "narration.wav").exists() else None,
        "mix_url": f"/media/projects/{name}/data/mix.wav" if (p_dir / "data" / "mix.wav").exists() else None,
    }


@app.post("/api/project/{name}/save")
def save_project(name: str, req: ProjectSaveRequest):
    """Save modified script.json."""
    p_dir = PROJECTS_DIR / name
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    script_path = p_dir / "script.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(req.script, f, indent=2, ensure_ascii=False)
    return {"status": "saved", "project": name}


@app.post("/api/script/ai-generate")
def api_generate_script(req: ScriptGenRequest):
    """Call Groq AI to generate a viral structured script."""
    try:
        script = ai_generate_script(
            topic=req.topic,
            style=req.style,
            language=req.language,
            voice=req.voice,
            music=req.music,
        )
        return {"status": "success", "script": script}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/preview")
def generate_voice_preview(req: VoiceGenRequest):
    """Generate on-the-fly audio preview for a single sentence."""
    try:
        import tempfile
        from scipy.io import wavfile
        import numpy as np

        SR = 24000
        preview_dir = STUDIO_DIR / "static" / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)
        out_filename = f"preview_{int(time.time() * 1000)}.wav"
        out_path = preview_dir / out_filename

        voice = req.voice
        speed = req.speed

        if "Neural" in voice or voice.startswith("bn-") or voice.startswith("en-"):
            import asyncio, edge_tts
            mp3_temp = tempfile.mktemp(suffix=".mp3")
            rate_str = f"{int((speed - 1.0) * 100):+d}%" if speed != 1.0 else "+0%"
            asyncio.run(edge_tts.Communicate(req.text, voice, rate=rate_str).save(mp3_temp))
            subprocess.run(["ffmpeg", "-y", "-i", mp3_temp, "-ar", str(SR), "-ac", "1", str(out_path)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(mp3_temp): os.unlink(mp3_temp)
        else:
            from kokoro_onnx import Kokoro
            KDIR = Path.home() / ".faceless-shorts" / "kokoro"
            k = Kokoro(str(KDIR / "kokoro-v1.0.onnx"), str(KDIR / "voices-v1.0.bin"))
            lang = "en-gb" if voice.startswith("b") else "en-us"
            samples = k.create(req.text, voice=voice, speed=speed, lang=lang)[0]
            arr = np.asarray(samples, dtype=np.float32)
            arr = arr / (np.abs(arr).max() + 1e-9) * 0.95
            wavfile.write(out_path, SR, (arr * 32767).astype(np.int16))

        return {"status": "ok", "url": f"/static/previews/{out_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice preview failed: {e}")


def _run_pipeline_worker(project: str, style: str, quality: str):
    """Background worker that runs the render pipeline and streams frame numbers."""
    global STATE
    STATE.running = True
    STATE.project = project
    STATE.style = style
    STATE.current_frame = 0
    STATE.start_time = time.time()
    STATE.fps = 24.0
    STATE.logs = [
        f"[{time.strftime('%H:%M:%S')}] ▶ Starting render: {style} for '{project}'",
        f"[{time.strftime('%H:%M:%S')}] ⚙ Initializing Node.js and Headless Chrome...",
    ]

    p_dir = PROJECTS_DIR / project
    cmd = ["bash", str(PROJECT_ROOT / "generate.sh"), style, project]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env={**os.environ, "PATH": f"{Path.home()}/.local/bin:{os.environ['PATH']}"}
        )
        STATE.process = proc

        # Monitor stdout for frame progress
        frame_pattern = re.compile(r"frame\s+(\d+)\s*/\s*(\d+)", re.IGNORECASE)
        for line in proc.stdout:
            line_str = line.strip()
            if not line_str:
                continue

            match = frame_pattern.search(line_str)
            if match:
                STATE.current_frame = int(match.group(1))
                STATE.total_frames = int(match.group(2))
                elapsed = time.time() - STATE.start_time
                STATE.elapsed_seconds = elapsed
                if STATE.current_frame > 0:
                    fps = STATE.current_frame / elapsed
                    STATE.fps = round(fps, 1)
                    rem_frames = STATE.total_frames - STATE.current_frame
                    STATE.eta_seconds = round(rem_frames / (fps or 1), 1)

            # Keep last 50 logs
            STATE.logs.append(f"[{time.strftime('%H:%M:%S')}] {line_str}")
            if len(STATE.logs) > 60:
                STATE.logs.pop(0)

        proc.wait()
        STATE.logs.append(f"[{time.strftime('%H:%M:%S')}] ✅ Video export completed successfully!")
    except Exception as e:
        STATE.logs.append(f"[{time.strftime('%H:%M:%S')}] ❌ Pipeline error: {e}")
    finally:
        STATE.running = False
        STATE.process = None


@app.post("/api/pipeline/run")
def run_pipeline(req: PipelineRunRequest, background_tasks: BackgroundTasks):
    """Start rendering a video in the background."""
    if STATE.running:
        raise HTTPException(status_code=400, detail="A render task is already running")

    background_tasks.add_task(_run_pipeline_worker, req.project, req.style, req.quality)
    return {"status": "started", "project": req.project}


@app.post("/api/pipeline/cancel")
def cancel_pipeline():
    """Cancel currently running render process."""
    if STATE.process and STATE.running:
        STATE.process.terminate()
        STATE.running = False
        STATE.logs.append(f"[{time.strftime('%H:%M:%S')}] 🛑 User cancelled agent execution.")
        return {"status": "cancelled"}
    return {"status": "not_running"}


@app.get("/api/pipeline/status")
def pipeline_status():
    """Return live render progress and terminal logs."""
    pct = round((STATE.current_frame / (STATE.total_frames or 1)) * 100, 1) if STATE.total_frames else 0.0
    return {
        "running": STATE.running,
        "project": STATE.project,
        "style": STATE.style,
        "current_frame": STATE.current_frame,
        "total_frames": STATE.total_frames,
        "percentage": min(pct, 100.0),
        "elapsed_seconds": round(STATE.elapsed_seconds, 1),
        "eta_seconds": round(STATE.eta_seconds, 1),
        "fps": STATE.fps,
        "logs": STATE.logs,
    }


# Static Media Serving
@app.get("/media/assets/{path:path}")
def serve_asset(path: str):
    f_path = ASSETS_DIR / path
    if f_path.exists():
        return FileResponse(f_path)
    raise HTTPException(status_code=404, detail="Asset not found")


@app.get("/media/projects/{path:path}")
def serve_project_media(path: str):
    f_path = PROJECTS_DIR / path
    if f_path.exists():
        return FileResponse(f_path)
    raise HTTPException(status_code=404, detail="Media not found")


# Mount static folder
STUDIO_STATIC = STUDIO_DIR / "static"
STUDIO_STATIC.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STUDIO_STATIC)), name="static")


@app.get("/")
def serve_index():
    index_file = STUDIO_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"status": "Studio UI not built yet"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("studio.server:app", host="0.0.0.0", port=8000, reload=True)


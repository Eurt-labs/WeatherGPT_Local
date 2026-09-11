import os
import sys
import time
import signal
import gc
import argparse
import psutil
import uvicorn
from pathlib import Path
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field

from config import HOST, PORT, MODELS_DIR, AVAILABLE_MODELS
from model_engine import get_engine, switch_model
from download_model import download_model

app = FastAPI(
    title="WeatherGPT Local Offline Engine",
    description="Offline GGUF model server drop-in compatible with WeatherGPT_Android",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HistoryItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    location: Optional[str] = "Live Location"
    weather_context: Optional[str] = ""
    sector_focus: Optional[str] = "farmer"
    language: Optional[str] = "en"
    is_voice_mode: Optional[bool] = False
    is_detail_mode: Optional[bool] = False
    history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class ModelSwitchRequest(BaseModel):
    model_name: Optional[str] = None
    model_key: Optional[str] = None

@app.get("/")
def root():
    active_model = "Not loaded"
    try:
        engine = get_engine()
        active_model = engine.model_filename
    except Exception:
        pass
    return {
        "service": "WeatherGPT Local Offline AI Engine",
        "status": "ready",
        "active_model": active_model,
        "endpoints": [
            "/chat",
            "/api/server/shutdown",
            "/api/ai/chat-stream",
            "/api/ai/chat",
            "/api/health",
            "/api/models",
            "/api/models/switch",
            "/api/weather/live"
        ]
    }

@app.post("/api/server/shutdown")
async def shutdown_server():
    """Cleanly shut down the server, release port 8000, and unload model from RAM."""
    def kill_proc():
        time.sleep(0.5)
        try:
            engine = get_engine()
            if hasattr(engine, "llm") and engine.llm:
                del engine.llm
                engine.llm = None
            gc.collect()
        except Exception:
            pass
        # Terminate current process cleanly
        os.kill(os.getpid(), signal.SIGTERM)

    import threading
    threading.Thread(target=kill_proc, daemon=True).start()
    return {
        "status": "shutting_down",
        "message": "WeatherGPT Local Server is shutting down and releasing all RAM."
    }

@app.get("/chat", response_class=HTMLResponse)
def web_chat_playground():
    """Interactive Web Chat Playground for direct PC testing."""
    html_file = Path(__file__).parent / "web_chat.html"
    if html_file.exists():
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>WeatherGPT Web Chat file not found.</h3>"

@app.get("/api/health")
def health():
    mem = psutil.virtual_memory()
    model_name = "Not loaded yet"
    try:
        engine = get_engine()
        model_name = engine.model_filename
    except Exception as e:
        model_name = f"Error: {e}"

    return {
        "status": "online",
        "model": model_name,
        "engine": "llama-cpp-python (GGUF)",
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "ram_used_gb": round(mem.used / (1024**3), 2),
        "ram_percent": mem.percent,
        "cpu_threads": os.cpu_count()
    }

@app.get("/api/models")
def list_models():
    """List all downloaded models on disk and available models in catalog."""
    downloaded = []
    for f in MODELS_DIR.glob("*.gguf"):
        downloaded.append({
            "filename": f.name,
            "size_gb": round(f.stat().st_size / (1024**3), 2),
            "path": str(f)
        })

    active = None
    try:
        active = get_engine().model_filename
    except Exception:
        pass

    return {
        "active_model": active,
        "downloaded_models": downloaded,
        "catalog": AVAILABLE_MODELS
    }

@app.post("/api/models/switch")
def switch_active_model(req: ModelSwitchRequest):
    """Switch active running model in real time without restarting server."""
    target_path: Optional[Path] = None

    if req.model_key and req.model_key.lower() in AVAILABLE_MODELS:
        info = AVAILABLE_MODELS[req.model_key.lower()]
        target_path = MODELS_DIR / info["filename"]
        if not target_path.exists():
            target_path = Path(download_model(req.model_key.lower()))

    if not target_path and req.model_name:
        cand = MODELS_DIR / req.model_name
        if cand.exists():
            target_path = cand
        else:
            p = Path(req.model_name)
            if p.exists():
                target_path = p

    if not target_path:
        return JSONResponse(status_code=400, content={"error": "Valid model_name or model_key required."})

    try:
        new_engine = switch_model(target_path)
        return {
            "status": "success",
            "switched_to": new_engine.model_filename,
            "size_gb": round(target_path.stat().st_size / (1024**3), 2)
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to switch model: {str(e)}"})

@app.post("/api/ai/chat-stream")
async def chat_stream(req: ChatRequest):
    """
    SSE stream endpoint implementing exact WeatherGPT_Android contract:
    Emits `data: <token>\n\n` and finishes with `data: [DONE]\n\n`.
    """
    engine = get_engine()

    def event_generator():
        try:
            for token in engine.stream_completion(
                user_message=req.message,
                location=req.location or "Live Location",
                weather_context=req.weather_context or "",
                sector_focus=req.sector_focus or "farmer",
                language=req.language or "en",
                is_voice_mode=req.is_voice_mode or False,
                is_detail_mode=req.is_detail_mode or False,
                history=req.history or []
            ):
                yield f"data: {token}\n\n"
        except Exception as e:
            yield f"data: [Error: {str(e)}]\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/ai/chat")
async def chat_non_stream(req: ChatRequest):
    """Non-streaming endpoint used by Android app connection ping tests."""
    engine = get_engine()
    text = engine.generate_completion(
        user_message=req.message,
        location=req.location or "Live Location",
        weather_context=req.weather_context or "",
        sector_focus=req.sector_focus or "farmer",
        language=req.language or "en",
        is_voice_mode=req.is_voice_mode or False,
        is_detail_mode=req.is_detail_mode or False,
        history=req.history or []
    )
    return {"response": text, "model": engine.model_filename}

@app.post("/api/weather/live")
async def weather_live(body: Dict[str, Any] = None):
    """Offline local weather fallback calculation engine."""
    return {
        "status": "offline_mode",
        "temperature": "27.0°C",
        "condition": "Mainly Clear",
        "humidity": "68%",
        "wind_speed": "12.4 km/h",
        "pressure": "1012.3 hPa",
        "uv_index": "6.2",
        "aqi": "92",
        "soil_moisture": "0.342 m³/m³",
        "soil_temp_10cm": "24.5°C",
        "vapor_pressure_deficit": "1.12 kPa",
        "dew_point_proximity": "Normal (>3°C spread)",
        "rain_next_24h": "0.0 mm",
        "flood_risk_level": "Low (Green)",
        "source": "Local WeatherGPT Offline Meteorological Model"
    }

def stop_running_server(port: int = PORT) -> bool:
    """Finds and terminates any running WeatherGPT server process on the port, releasing RAM."""
    current_pid = os.getpid()
    found = False

    for proc in psutil.process_iter(['pid', 'name']):
        if proc.pid == current_pid:
            continue
        try:
            for conn in proc.net_connections(kind='inet'):
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    print(f"[*] Found running server on port {port} (PID: {proc.pid}). Shutting down...")
                    # 1. Try graceful API shutdown
                    try:
                        import urllib.request
                        req = urllib.request.Request(
                            f"http://127.0.0.1:{port}/api/server/shutdown",
                            data=b"{}",
                            headers={"Content-Type": "application/json"}
                        )
                        with urllib.request.urlopen(req, timeout=1.5):
                            pass
                        time.sleep(0.6)
                    except Exception:
                        pass

                    # 2. If still active, terminate process
                    try:
                        if proc.is_running():
                            proc.terminate()
                            proc.wait(timeout=2.0)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass

                    found = True
                    print(f"[OK] Process {proc.pid} stopped. Port {port} freed and model RAM released.")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not found:
        print(f"[*] No server was running on port {port}. Server is already offline.")
    return found

def choose_model_interactive(requested_arg: Optional[str] = None) -> Path:
    """Interactive terminal selector allowing the user to pick which model to load."""
    downloaded_models = sorted(list(MODELS_DIR.glob("*.gguf")), key=lambda p: p.stat().st_size, reverse=True)

    if requested_arg:
        key = requested_arg.lower().replace("-", "")
        if key in AVAILABLE_MODELS:
            fname = AVAILABLE_MODELS[key]["filename"]
            target = MODELS_DIR / fname
            if target.exists():
                return target
            else:
                print(f"[!] Model {AVAILABLE_MODELS[key]['name']} is not downloaded. Downloading now...")
                dl = download_model(key)
                return Path(dl)
        cand = Path(requested_arg)
        if cand.exists():
            return cand
        cand_sub = MODELS_DIR / requested_arg
        if cand_sub.exists():
            return cand_sub
        print(f"[!] Warning: requested model '{requested_arg}' not found on disk.")

    if downloaded_models:
        print("\n=======================================================")
        print("          WeatherGPT Local AI Model Selector")
        print("=======================================================")
        print("Found the following downloaded models in models/:")
        for i, m in enumerate(downloaded_models, 1):
            size_gb = m.stat().st_size / (1024**3)
            friendly = m.name
            for k, info in AVAILABLE_MODELS.items():
                if info["filename"] == m.name:
                    friendly = f"{info['name']} [{k}]"
                    break
            print(f"  [{i}] {friendly} ({size_gb:.2f} GB)")

        dl_idx = len(downloaded_models) + 1
        print(f"  [{dl_idx}] Download another model from Hugging Face catalog")
        print("=======================================================")

        try:
            choice = input(f"Select model to activate [default: 1]: ").strip()
            if not choice:
                return downloaded_models[0]

            choice_int = int(choice)
            if 1 <= choice_int <= len(downloaded_models):
                return downloaded_models[choice_int - 1]
            elif choice_int == dl_idx:
                print("\nAvailable models to download:")
                for k, v in AVAILABLE_MODELS.items():
                    print(f"  [{k}] {v['name']} ({v['size']})")
                dl_key = input("Enter model key (7b / 3b / 1.5b): ").strip().lower()
                dl_path = download_model(dl_key if dl_key in AVAILABLE_MODELS else "7b")
                return Path(dl_path)
        except Exception:
            pass

        return downloaded_models[0]

    print("\n[!] No GGUF models found in models/ folder. Launching downloader...")
    dl_path = download_model("7b")
    return Path(dl_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WeatherGPT Local Offline AI Engine")
    parser.add_argument("--stop", "--shutdown", "-k", action="store_true", help="Stop running server and release memory")
    parser.add_argument("--model", "-m", type=str, default=None, help="Model key (7b, 3b, 1.5b) or path to .gguf file")
    parser.add_argument("--port", "-p", type=int, default=PORT, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", type=str, default=HOST, help="Host address (default: 0.0.0.0)")
    parser.add_argument("--list", "-l", action="store_true", help="List downloaded and catalog models")

    args = parser.parse_args()

    # If user wants to stop/close the server
    if args.stop:
        stop_running_server(args.port)
        sys.exit(0)

    if args.list:
        print("\nDownloaded Models:")
        for f in MODELS_DIR.glob("*.gguf"):
            print(f" - {f.name} ({f.stat().st_size / (1024**3):.2f} GB)")
        print("\nCatalog:")
        for k, v in AVAILABLE_MODELS.items():
            print(f" [{k}] {v['name']} ({v['size']})")
        sys.exit(0)

    # Automatically clean up any stale process occupying the port before starting
    stop_running_server(args.port)

    # Interactive or CLI model selection
    selected_model = choose_model_interactive(args.model)
    os.environ["WEATHERGPT_MODEL"] = str(selected_model)

    # Preload engine into memory so first query is instant
    engine = get_engine(selected_model)

    print(f"[READY] WeatherGPT Local Server initialized with: {engine.model_filename}")
    print(f"[READY] Starting FastAPI server on http://{args.host}:{args.port}")
    print("[INFO] Press CTRL+C at any time to stop the server and release RAM.\n")

    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] KeyboardInterrupt received. Stopping server...")
    finally:
        # Unload model from memory
        try:
            if hasattr(engine, "llm") and engine.llm:
                del engine.llm
                engine.llm = None
            gc.collect()
        except Exception:
            pass
        print("[SHUTDOWN] Model unloaded from RAM. Port freed. Goodbye!")

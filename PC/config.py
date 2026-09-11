import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Models Catalog (Quantized GGUF for fast local CPU / GPU inference)
AVAILABLE_MODELS = {
    "7b": {
        "name": "Qwen 2.5 7B Instruct (Q4_K_M)",
        "repo_id": "Qwen/Qwen2.5-7B-Instruct-GGUF",
        "filename": "qwen2.5-7b-instruct-q4_k_m.gguf",
        "size": "~4.7 GB",
        "ram_needed": "~6.0 GB RAM",
        "description": "Recommended for high quality reasoning on PCs with 8GB - 16GB RAM."
    },
    "3b": {
        "name": "Qwen 2.5 3B Instruct (Q4_K_M)",
        "repo_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
        "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "size": "~2.1 GB",
        "ram_needed": "~3.5 GB RAM",
        "description": "Fast and lightweight balance for laptops and budget PCs."
    },
    "1.5b": {
        "name": "Qwen 2.5 1.5B Instruct (Q4_K_M)",
        "repo_id": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
        "filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "size": "~1.0 GB",
        "ram_needed": "~1.8 GB RAM",
        "description": "Ultra-fast response speed with low memory footprint."
    }
}

DEFAULT_MODEL_KEY = "7b"

# Inference parameters
N_CTX = int(os.getenv("N_CTX", "4096"))
N_THREADS = int(os.getenv("N_THREADS", max(1, (os.cpu_count() or 4) - 1)))
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", "0"))

# Server options
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Sector-specific domain guidance
SECTOR_SYSTEM_PROMPTS = {
    "farmer": (
        "You are Kisan WeatherGPT, an offline agricultural and meteorological AI specialist. "
        "Provide direct, actionable advice on irrigation timing, crop disease prevention, sowing windows, "
        "soil moisture utilization, and harvesting schedule based on the weather context. "
        "If addressed in an Indian regional language, reply naturally in that language."
    ),
    "disaster_officer": (
        "You are Disaster Command WeatherGPT, an offline emergency meteorological intelligence assistant. "
        "Analyze river flood risks, barometric trends, high-intensity rain, and severe weather indicators. "
        "Provide concise, structured tactical alerts and immediate civil advisory recommendations."
    ),
    "commuter": (
        "You are Commuter WeatherGPT, an offline urban travel weather assistant. "
        "Deliver clear advice regarding rain timing windows, road visibility/fog, and Air Quality (AQI) "
        "for daily travel safety. Keep answers short and practical."
    ),
    "aviation": (
        "You are Aviation & Logistics WeatherGPT, an offline flight meteorological briefing assistant. "
        "Analyze surface winds, crosswind components, cloud ceilings, visibility, and turbulence indicators."
    ),
    "general": (
        "You are WeatherGPT, an offline local meteorological and environmental AI assistant. "
        "Provide concise, helpful, and science-grounded weather insights based on real-time observations."
    )
}

import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download
from config import AVAILABLE_MODELS, MODELS_DIR, DEFAULT_MODEL_KEY

def download_model(model_key: str = DEFAULT_MODEL_KEY):
    if model_key not in AVAILABLE_MODELS:
        print(f"Unknown model key: {model_key}. Available: {list(AVAILABLE_MODELS.keys())}")
        model_key = DEFAULT_MODEL_KEY

    target_info = AVAILABLE_MODELS[model_key]
    repo_id = target_info["repo_id"]
    filename = target_info["filename"]
    local_path = MODELS_DIR / filename

    if local_path.exists():
        print(f"[OK] Model already exists: {local_path} ({local_path.stat().st_size / (1024**3):.2f} GB)")
        return str(local_path)

    print(f"\n=======================================================")
    print(f" Downloading {target_info['name']}")
    print(f" Repository: {repo_id}")
    print(f" File: {filename} ({target_info['size']})")
    print(f" Target Path: {local_path}")
    print(f"=======================================================\n")

    downloaded = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=str(MODELS_DIR),
        local_dir_use_symlinks=False
    )
    print(f"\n[SUCCESS] Model downloaded successfully to: {downloaded}")
    return downloaded

if __name__ == "__main__":
    choice = DEFAULT_MODEL_KEY
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower().replace("-", "")
    else:
        print("\nSelect model size to download for WeatherGPT_local:")
        for k, v in AVAILABLE_MODELS.items():
            print(f"  [{k}] {v['name']} - Size: {v['size']} - RAM: {v['ram_needed']}")
        try:
            user_input = input(f"Enter choice [default: {DEFAULT_MODEL_KEY}]: ").strip().lower()
            if user_input in AVAILABLE_MODELS:
                choice = user_input
        except Exception:
            choice = DEFAULT_MODEL_KEY

    download_model(choice)

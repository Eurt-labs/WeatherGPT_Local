import os
import sys
import time
import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional

# Ensure UTF-8 output in Windows console without crash
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SERVER_URL = os.getenv("WEATHERGPT_URL", "http://localhost:8000")

SECTOR_DISPLAY = {
    "farmer": "Kisan (Farmer / Agriculture)",
    "disaster": "Disaster Response & Flood Command",
    "commuter": "Urban Commuter & Daily Travel",
    "aviation": "Aviation, Drone & Logistics",
    "general": "General Meteorological Inquiries"
}

def check_server() -> Optional[Dict]:
    try:
        req = urllib.request.Request(f"{SERVER_URL}/api/health", headers={"User-Agent": "WeatherGPT-CLI"})
        with urllib.request.urlopen(req, timeout=1.5) as res:
            if res.status == 200:
                return json.loads(res.read().decode("utf-8"))
    except Exception:
        pass
    return None

def stream_from_server(
    message: str,
    sector: str,
    location: str,
    weather_context: str,
    history: List[Dict[str, str]]
):
    url = f"{SERVER_URL}/api/ai/chat-stream"
    payload = {
        "message": message,
        "location": location,
        "weather_context": weather_context,
        "sector_focus": sector,
        "language": "en",
        "is_voice_mode": False,
        "history": history
    }
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})

    start_time = time.time()
    token_count = 0
    full_response = []

    with urllib.request.urlopen(req, timeout=120) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if line.startswith("data: "):
                token = line[6:]
                if token == "[DONE]":
                    break
                full_response.append(token)
                token_count += 1
                print(token, end="", flush=True)

    elapsed = max(0.01, time.time() - start_time)
    tps = token_count / elapsed
    print(f"\n\n[Speed: {token_count} tokens in {elapsed:.2f}s | {tps:.1f} tok/s]")
    return "".join(full_response)

def stream_direct_engine(
    message: str,
    sector: str,
    location: str,
    weather_context: str,
    history: List[Dict[str, str]]
):
    from model_engine import get_engine
    engine = get_engine()

    start_time = time.time()
    token_count = 0
    full_response = []

    for token in engine.stream_completion(
        user_message=message,
        location=location,
        weather_context=weather_context,
        sector_focus=sector,
        history=history
    ):
        full_response.append(token)
        token_count += 1
        print(token, end="", flush=True)

    elapsed = max(0.01, time.time() - start_time)
    tps = token_count / elapsed
    print(f"\n\n[Speed: {token_count} tokens in {elapsed:.2f}s | {tps:.1f} tok/s]")
    return "".join(full_response)

def main():
    print("=" * 70)
    print("        WeatherGPT Local Offline AI - Interactive PC Chat")
    print("=" * 70)

    server_info = check_server()
    is_server_mode = server_info is not None

    active_model = "Unknown"
    if is_server_mode:
        active_model = server_info.get("model", "Local GGUF")
        print(f"[MODE] Connected to running local server at: {SERVER_URL}")
        print(f"[MODEL] Active GGUF: {active_model}")
        print(f"[RAM] System RAM used: {server_info.get('ram_used_gb', '?')} GB / {server_info.get('ram_total_gb', '?')} GB")
    else:
        print("[MODE] Standalone Direct Engine Mode (Server offline)")
        try:
            from model_engine import get_engine
            engine = get_engine()
            active_model = engine.model_filename
            print(f"[MODEL] Active GGUF: {active_model}")
        except Exception as e:
            print(f"[ERROR] Could not load local model engine: {e}")
            print("Please run `run_pc_server.bat` first.")
            return

    current_sector = "farmer"
    current_location = "New Delhi, India"
    current_weather = "Temp: 29.5 deg C | Humidity: 68% | Wind: 14 km/h | Condition: Partly Cloudy"
    history: List[Dict[str, str]] = []

    print("-" * 70)
    print(f"Current Sector  : {SECTOR_DISPLAY.get(current_sector)}")
    print(f"Current Location: {current_location}")
    print(f"Weather Context : {current_weather}")
    print("-" * 70)
    print("Interactive Commands:")
    print("  /sector [farmer|disaster|commuter|aviation|general]  - Change role")
    print("  /weather [description]                              - Simulate weather")
    print("  /location [city/state]                              - Set location")
    print("  /clear                                              - Clear conversation")
    print("  /exit                                               - Quit chat")
    print("=" * 70 + "\n")

    while True:
        try:
            prompt = input(f"[{current_sector.upper()}] You > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting WeatherGPT Chat. Goodbye!")
            break

        if not prompt:
            continue

        cmd = prompt.lower()
        if cmd in ["/exit", "/quit", "/q", "exit", "quit"]:
            print("Exiting WeatherGPT Chat. Goodbye!")
            break

        if cmd in ["/clear", "/c", "clear"]:
            history.clear()
            print("[OK] Conversation history cleared.\n")
            continue

        if cmd.startswith("/sector") or cmd.startswith("/s "):
            parts = prompt.split(maxsplit=1)
            if len(parts) > 1:
                target = parts[1].strip().lower()
                matched = None
                for k in SECTOR_DISPLAY:
                    if target in k:
                        matched = k
                        break
                if matched:
                    current_sector = matched
                    print(f"[OK] Switched sector to: {SECTOR_DISPLAY[current_sector]}\n")
                else:
                    print(f"[!] Unknown sector. Available: {', '.join(SECTOR_DISPLAY.keys())}\n")
            else:
                print("Available sectors:")
                for k, v in SECTOR_DISPLAY.items():
                    print(f"  {k:15} - {v}")
                print()
            continue

        if cmd.startswith("/weather") or cmd.startswith("/w "):
            parts = prompt.split(maxsplit=1)
            if len(parts) > 1:
                current_weather = parts[1].strip()
                print(f"[OK] Weather context updated to: {current_weather}\n")
            else:
                print(f"Current weather: {current_weather}\n")
            continue

        if cmd.startswith("/location") or cmd.startswith("/l "):
            parts = prompt.split(maxsplit=1)
            if len(parts) > 1:
                current_location = parts[1].strip()
                print(f"[OK] Location updated to: {current_location}\n")
            else:
                print(f"Current location: {current_location}\n")
            continue

        if cmd in ["/help", "/h", "help"]:
            print("Commands: /sector, /weather, /location, /clear, /exit\n")
            continue

        print(f"\nAI ({active_model}) > ", end="", flush=True)
        try:
            if is_server_mode:
                reply = stream_from_server(
                    message=prompt,
                    sector=current_sector,
                    location=current_location,
                    weather_context=current_weather,
                    history=history
                )
            else:
                reply = stream_direct_engine(
                    message=prompt,
                    sector=current_sector,
                    location=current_location,
                    weather_context=current_weather,
                    history=history
                )

            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": reply})
            print()
        except Exception as e:
            print(f"\n[ERROR] Generation failed: {e}\n")

if __name__ == "__main__":
    main()

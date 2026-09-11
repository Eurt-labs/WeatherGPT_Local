import os
import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Optional, Tuple

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

def fetch_live_open_meteo(city: str) -> Optional[Tuple[str, str]]:
    """
    Direct Open-Meteo numerical weather model ingestion (zero API keys).
    Retrieves temperature, humidity, wind, pressure, topsoil moisture,
    evapotranspiration (ET0), and 24h precipitation probability.
    """
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
        req = urllib.request.Request(geo_url, headers={"User-Agent": "WeatherGPT-PC"})
        with urllib.request.urlopen(req, timeout=4) as res:
            data = json.loads(res.read().decode("utf-8"))
            results = data.get("results", [])
            if not results:
                return None
            loc = results[0]
            lat = loc["latitude"]
            lon = loc["longitude"]
            resolved_city = f"{loc.get('name')}, {loc.get('admin1', '')} ({loc.get('country_code', '')})"

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,surface_pressure,dew_point_2m"
            "&hourly=soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,et0_fao_evapotranspiration,precipitation_probability"
            "&daily=precipitation_sum,precipitation_probability_max,temperature_2m_max,temperature_2m_min"
            "&timezone=auto"
        )
        req2 = urllib.request.Request(weather_url, headers={"User-Agent": "WeatherGPT-PC"})
        with urllib.request.urlopen(req2, timeout=5) as res2:
            wdata = json.loads(res2.read().decode("utf-8"))
            curr = wdata.get("current", {})
            hourly = wdata.get("hourly", {})
            daily = wdata.get("daily", {})

            temp = curr.get("temperature_2m", 28.0)
            hum = curr.get("relative_humidity_2m", 60)
            wind = curr.get("wind_speed_10m", 10.0)
            dew = curr.get("dew_point_2m", 20.0)
            press = curr.get("surface_pressure", 1012.0)
            code = curr.get("weather_code", 0)

            sm1 = hourly.get("soil_moisture_0_to_1cm", [0.30])[0] if hourly.get("soil_moisture_0_to_1cm") else 0.30
            sm2 = hourly.get("soil_moisture_1_to_3cm", [0.32])[0] if hourly.get("soil_moisture_1_to_3cm") else 0.32
            soil_avg = (sm1 + sm2) / 2.0
            et0 = hourly.get("et0_fao_evapotranspiration", [4.2])[0] if hourly.get("et0_fao_evapotranspiration") else 4.2

            rain_sum = daily.get("precipitation_sum", [0.0])[0] if daily.get("precipitation_sum") else 0.0
            rain_prob = daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0

            context = (
                f"Live Atmosphere: {temp} deg C (Humidity: {hum}%, Dew Point: {dew} deg C, Pressure: {press} hPa, Wind: {wind} km/h)
"
                f"Precipitation Outlook: 24h Rain: {rain_sum} mm | Rain Chance: {rain_prob}%
"
                f"Agriculture & Soil: Topsoil Moisture: {soil_avg:.2f} m3/m3 | Evapotranspiration (ET0): {et0:.1f} mm/day"
            )
            return resolved_city, context
    except Exception as e:
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
    user_name = "Dhruv"
    user_crops = "Wheat, Mustard"
    user_land_area = "5 Acres"
    current_weather = "Live Atmosphere: 29.5 deg C (Humidity: 68%, Dew Point: 22.0 deg C, Pressure: 1012 hPa, Wind: 14 km/h)\nPrecipitation Outlook: 24h Rain: 0.0 mm | Rain Chance: 10%\nAgriculture & Soil: Topsoil Moisture: 0.33 m3/m3 | Evapotranspiration (ET0): 4.2 mm/day"

    print("[*] Contacting Open-Meteo for live telemetry...")
    om_res = fetch_live_open_meteo("New Delhi")
    if om_res:
        current_location, current_weather = om_res
        print(f"[OK] Live Open-Meteo telemetry loaded for: {current_location}")
    else:
        print(f"[*] Using cached baseline weather for: {current_location}")

    history: List[Dict[str, str]] = []

    print("-" * 70)
    print(f"Current Sector  : {SECTOR_DISPLAY.get(current_sector)}")
    print(f"Current Location: {current_location}")
    print(f"Open-Meteo Data : {current_weather.splitlines()[0]}")
    print("-" * 70)
    print("Interactive Commands:")
    print("  /fetch [city]                                       - Fetch live Open-Meteo data for any city")
    print("  /sector [farmer|disaster|commuter|aviation|general]  - Change role")
    print("  /weather [description]                              - Manually override weather")
    print("  /location [city/state]                              - Change location
  /profile [name, crops, area]                        - Set profile (e.g. /profile Dhruv | Wheat, Mustard | 5 Acres)")
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

        if cmd.startswith("/fetch"):
            parts = prompt.split(maxsplit=1)
            target_city = parts[1].strip() if len(parts) > 1 else current_location.split(",")[0]
            print(f"[*] Fetching live Open-Meteo data for '{target_city}'...")
            res = fetch_live_open_meteo(target_city)
            if res:
                current_location, current_weather = res
                print(f"[OK] Successfully updated to live Open-Meteo telemetry:")
                print(f"  Location: {current_location}")
                for l in current_weather.splitlines():
                    print(f"  {l}")
                print()
            else:
                print(f"[!] Could not fetch Open-Meteo data for '{target_city}'.\n")
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

                if cmd.startswith("/profile"):
            parts = prompt.split(maxsplit=1)
            if len(parts) > 1:
                items = [x.strip() for x in parts[1].split("|")]
                if len(items) >= 1 and items[0]: user_name = items[0]
                if len(items) >= 2 and items[1]: user_crops = items[1]
                if len(items) >= 3 and items[2]: user_land_area = items[2]
                print(f"[OK] Profile updated: Name={user_name}, Crops={user_crops}, Area={user_land_area}\n")
            else:
                print(f"Current Profile: Name={user_name}, Crops={user_crops}, Area={user_land_area}\n")
            continue

        if cmd.startswith("/location") or cmd.startswith("/l "):
            parts = prompt.split(maxsplit=1)
            if len(parts) > 1:
                new_loc = parts[1].strip()
                print(f"[*] Fetching live Open-Meteo data for '{new_loc}'...")
                res = fetch_live_open_meteo(new_loc)
                if res:
                    current_location, current_weather = res
                    print(f"[OK] Location and Open-Meteo telemetry updated to: {current_location}\n")
                else:
                    current_location = new_loc
                    print(f"[OK] Location set to: {current_location}\n")
            else:
                print(f"Current location: {current_location}\n")
            continue

        if cmd in ["/help", "/h", "help"]:
            print("Commands: /fetch, /sector, /weather, /location, /clear, /exit\n")
            continue

        print(f"\nAI ({active_model}) > ", end="", flush=True)
        try:
            if is_server_mode:
                reply = stream_from_server(
                    message=prompt,
                    sector=current_sector,
                    location=current_location,
                    weather_context=f"{current_weather}\n\nUSER PROFILE (COLLECTED DETAILS):\nName: {user_name} | Sector: {current_sector} | Primary Crops: {user_crops} | Farm Area: {user_land_area} | Region: {current_location}",
                    history=history
                )
            else:
                reply = stream_direct_engine(
                    message=prompt,
                    sector=current_sector,
                    location=current_location,
                    weather_context=f"{current_weather}\n\nUSER PROFILE (COLLECTED DETAILS):\nName: {user_name} | Sector: {current_sector} | Primary Crops: {user_crops} | Farm Area: {user_land_area} | Region: {current_location}",
                    history=history
                )

            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": reply})
            print()
        except Exception as e:
            print(f"\n[ERROR] Generation failed: {e}\n")

if __name__ == "__main__":
    main()

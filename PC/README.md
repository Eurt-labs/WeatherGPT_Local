# WeatherGPT Local Offline Server (PC Edition)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-0.3.35-792EE5?style=flat-square)](https://github.com/abetlen/llama-cpp-python)
[![Qwen 2.5](https://img.shields.io/badge/Model-Qwen%202.5%20GGUF-blue?style=flat-square)](https://huggingface.co/Qwen)

The **PC Edition** of WeatherGPT Local is a standalone offline AI engine that runs quantized GGUF models directly on your workstation or laptop. It implements the exact Server-Sent Events (SSE) streaming API contract as the Render Cloud backend, allowing the **WeatherGPT Android application** to switch seamlessly between cloud and offline edge modes.

---

## 📂 Folder Overview

```
PC/
├── models/               # Downloaded .gguf model weights (ignored by git)
├── config.py             # Model catalog, context length (4096), threads, prompts
├── download_model.py     # 1-click HuggingFace downloader with pause/resume support
├── model_engine.py       # llama-cpp-python streaming inference wrapper
├── main.py               # FastAPI server matching Render contract
├── requirements.txt      # Python dependencies
├── run_pc_server.bat     # Crash-proof 1-click Windows runner
└── README.md             # This guide
```

---

## 🧠 Supported GGUF Models

| Key | Model Name | Format | Weights Size | Recommended RAM | Best For |
|---|---|---|---|---|---|
| **`7b`** (Default) | Qwen 2.5 7B Instruct | `q4_k_m.gguf` | ~4.7 GB | ~6.0 GB | Deep agricultural, meteorological & disaster reasoning |
| **`3b`** | Qwen 2.5 3B Instruct | `q4_k_m.gguf` | ~2.1 GB | ~3.5 GB | Balanced performance on budget laptops |
| **`1.5b`** | Qwen 2.5 1.5B Instruct | `q4_k_m.gguf` | ~1.0 GB | ~1.8 GB | Ultra-fast responses with low memory footprint |

---

## ⚡ Quickstart

### 1. Automatic 1-Click Launch (Windows)
Double-click **`run_pc_server.bat`**.
- It verifies Python.
- Activates virtual environment / checks dependencies.
- Prompts for model download if missing.
- Detects your local IP address.
- Starts the FastAPI server on `http://0.0.0.0:8000`.

### 2. Manual CLI Launch
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download model (e.g. 7b or 3b)
python download_model.py 7b

# 3. Start server
python main.py
```

---

---

## 💬 Testing & Chatting Directly on PC (CLI)

You can test model responses directly on your PC using the **Interactive Terminal CLI** without needing an Android device connected:

```bash
python chat_cli.py
```

- **Real-Time Token Streaming**: Streams answers token-by-token with live speed metrics (`tok/s`).
- **Live Open-Meteo Fetching**:
  - `/fetch New Delhi` - Live real-time weather & telemetry fetch from Open-Meteo
- **Interactive Sector Switching**:
  - `/sector farmer` - Switch to Kisan / Agronomy mode
  - `/sector disaster` - Switch to Disaster Command mode
  - `/sector commuter` - Switch to Urban Travel mode
  - `/sector aviation` - Switch to Flight / Drone mode
- **Weather & Location Simulation**:
  - `/weather Temp: 34°C, Humidity: 85%, Rain: Heavy`
  - `/location Patna, Bihar`
  - `/clear` - Reset conversation memory
- **Clean Server Control & Exit**:
  - `/stop` - Instantly terminates local server on port 8000 and releases all model RAM
  - `/exit` - Quit chat session
- **Smart Memory Sharing**: Automatically connects to the running server on port 8000 to avoid loading duplicate model weights into RAM. If the server is offline, it runs the engine directly.

### Server Management via Python:
```bash
# Start server with interactive model picker
python main.py

# Start server with specific model and port
python main.py -m 7b -p 8000

# Cleanly stop running server, free port 8000 & release model RAM
python main.py --stop
```

## 🔌 API Reference & Contracts

### 1. SSE Real-Time Chat Stream (Matching Android Contract)
- **Endpoint:** `POST /api/ai/chat-stream`
- **Content-Type:** `application/json`
- **Response:** `text/event-stream` (`data: <token>\n\n` -> `data: [DONE]\n\n`)

**Request Body:**
```json
{
  "message": "Is it safe to spray fungicide on wheat today?",
  "location": "Ludhiana, Punjab",
  "weather_context": "Temp: 28°C, Humidity: 85%, Wind: 14 km/h, Rain probability: 10%",
  "sector_focus": "farmer",
  "language": "en",
  "is_voice_mode": false,
  "history": []
}
```

**cURL Test:**
```bash
curl -N -X POST http://localhost:8000/api/ai/chat-stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Give me rain guidance","sector_focus":"farmer"}'
```

---

### 2. Single-Turn Chat Completion (Test Ping)
- **Endpoint:** `POST /api/ai/chat`
- **Description:** Used by the Android app's "Test Local PC Server Connection" button to verify server health and latency.

**Response:**
```json
{
  "response": "Based on current observations, rain is unlikely...",
  "model": "qwen2.5-7b-instruct-q4_k_m.gguf"
}
```

---

### 3. Server Health & Metrics
- **Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "online",
  "model": "qwen2.5-7b-instruct-q4_k_m.gguf",
  "engine": "llama-cpp-python (GGUF)",
  "ram_total_gb": 15.82,
  "ram_used_gb": 7.14,
  "ram_percent": 45.1,
  "cpu_threads": 8
}
```

---

### 4. Offline Weather Calculations Fallback
- **Endpoint:** `POST /api/weather/live`
- **Description:** Generates realistic meteorological calculations (soil moisture, VPD, dew point spread, flood risk) when the device has zero internet connectivity.

---

## 📱 Pairing with WeatherGPT Android

### Via USB Cable (Zero Latency)
1. Connect Android phone to PC via USB cable.
2. Ensure **USB Debugging** is turned on in phone Developer Options.
3. In terminal, run:
   ```bash
   adb reverse tcp:8000 tcp:8000
   ```
4. In the app: Settings ⚙️ -> select **PC (USB)** -> tap **Test Connection**.

### Via Local Wi-Fi
1. Connect phone and PC to the same Wi-Fi router or phone mobile hotspot.
2. Note your PC IP (e.g., `192.168.1.15`).
3. In the app: Settings ⚙️ -> select **PC (Wi-Fi)** -> enter `http://192.168.1.15:8000` -> tap **Test Connection**.

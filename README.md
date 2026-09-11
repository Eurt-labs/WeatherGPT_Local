# WeatherGPT Local — Developer Evaluation & Offline AI Engine 💻🤖

[![SIH Problem Statement](https://img.shields.io/badge/SIH%202026-PS--26068-FF6F00?style=for-the-badge)](https://www.sih.gov.in/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF%20Inference-792EE5?style=for-the-badge)](https://github.com/ggerganov/llama.cpp)
[![Qwen 2.5](https://img.shields.io/badge/Qwen%202.5-7B%20%7C%203B%20%7C%201.5B-007ACC?style=for-the-badge)](https://huggingface.co/Qwen)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)

> [!IMPORTANT]
> **DEVELOPER WORKSTATION SUITE**: This repository is strictly an **internal developer evaluation and benchmarking environment** for running quantized GGUF models locally on a developer PC.  
> The **[WeatherGPT Android Application](https://github.com/Eurt-labs/WeatherGPT_Android)** is the primary production target for end-users, communicating directly with the **[Cloud Backend on Render](https://github.com/Eurt-labs/WeatherGPT_Backend)**.

---

## 🏗️ Architecture & Ecosystem Role

```
                              WEATHERGPT ECOSYSTEM
                              
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                       WeatherGPT Android Client                          │
 │                       ★ THE PRODUCTION TARGET ★                          │
 │           • Jetpack Compose M3 UI       • On-Device SQLite Cache         │
 └────────────────────────────────────┬─────────────────────────────────────┘
                   ┌──────────────────┴──────────────────┐
                   │ (Production Cloud)                  │ (Internal Dev / Benchmarking)
                   ▼                                     ▼
 ┌───────────────────────────────────┐ ┌───────────────────────────────────┐
 │       Render Cloud Backend        │ │     WeatherGPT_local (PC Dev)     │
 │  • Google Gemini 3.6 Flash        │ │  • llama-cpp-python GGUF Engine   │
 │  • Open-Meteo Satellite Feed      │ │  • Qwen 2.5 7B / 3B / 1.5B        │
 │  • Supabase Sync & Rate Limiting  │ │  • Interactive Terminal CLI       │
 └───────────────────────────────────┘ └───────────────────────────────────┘
```

---

## 📁 Repository Structure

```
WeatherGPT_local/
└── PC/                       # Developer PC Offline AI Engine
    ├── models/               # Quantized GGUF model weights (git-ignored)
    ├── config.py             # Inference parameters & SIH domain system prompts
    ├── download_model.py     # Automated HuggingFace downloader with resume support
    ├── model_engine.py       # llama-cpp-python streaming inference wrapper
    ├── chat_cli.py           # Interactive terminal CLI chat with token streaming
    ├── main.py               # FastAPI server matching Render SSE contract
    ├── requirements.txt      # Python dependencies
    ├── run_pc_server.bat     # 1-click Windows runner
    ├── AGENTS.md             # Contributor & Agent Guardrails
    └── README.md             # Dedicated PC server documentation
```

---

## 🚀 Quickstart: Running & Testing on PC

### 1. Requirements
- **OS:** Windows 10/11 or Linux.
- **Python:** Python 3.10 to 3.14.
- **RAM:** 8GB+ recommended (for 3B/7B models).

### 2. Launch the Local Server
```bash
cd PC

# Install dependencies
pip install -r requirements.txt

# Start server (with interactive model picker or CLI flags):
python main.py

# Or specify model and port directly:
python main.py -m 3b -p 8000
```

### 3. Interactive Terminal CLI Test
To test the offline LLM directly from your terminal:
```bash
python chat_cli.py
```
- **Real-Time Token Streaming**: Streams answers token-by-token with live speed metrics (`tok/s`).
- **Live Open-Meteo Telemetry**: Type `/fetch New Delhi` to pull real-time weather, soil moisture, and evapotranspiration into the conversation.
- **Role Switching**: Switch sectors on the fly with `/sector farmer`, `/sector disaster`, `/sector commuter`, etc.
- **Proactive Profile Guidance**: Generates tailored crop and location follow-ups.

### 4. Clean Shutdown & Memory Release
```bash
python main.py --stop
# Or type /stop directly in chat_cli.py
```
This immediately terminates the server process on port 8000 and releases all model weights from PC RAM.

---

## 📱 Developer Bridge: Pairing with Android

For developer testing of offline connectivity from an Android device to your local PC:

### Option A: USB Cable (Zero Latency - Recommended)
1. Plug your Android phone into your PC via USB (with **USB Debugging** enabled).
2. Open terminal and run:
   ```bash
   adb reverse tcp:8000 tcp:8000
   ```
3. In the WeatherGPT Android App:
   - Go to **Settings ⚙️** -> **AI BACKEND & CONNECTION**.
   - Select **PC (USB)** (`http://localhost:8000`).
   - Tap **Test Connection** to verify.

### Option B: Local Wi-Fi / Hotspot
1. Connect PC and phone to the same Wi-Fi or phone hotspot.
2. Find your PC's local IP address (e.g., `192.168.1.15`).
3. In the Android App Settings:
   - Select **PC (Wi-Fi)**.
   - Enter `http://<YOUR_PC_IP>:8000`.
   - Tap **Test Connection**.

---

## 📄 License

This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.

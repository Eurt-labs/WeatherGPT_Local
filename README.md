# WeatherGPT Local & Edge Offline AI Engine

[![SIH Problem Statement](https://img.shields.io/badge/SIH%202024-PS--26068-FF6F00?style=for-the-badge)](https://www.sih.gov.in/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF%20Inference-792EE5?style=for-the-badge)](https://github.com/ggerganov/llama.cpp)
[![Qwen 2.5](https://img.shields.io/badge/Qwen%202.5-7B%20%7C%203B%20%7C%201.5B-007ACC?style=for-the-badge)](https://huggingface.co/Qwen)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)

**WeatherGPT_local** is an offline, edge-capable meteorological AI intelligence service designed to provide uninterrupted weather forecasting, agricultural crop advice, and disaster warning briefings in scenarios with **zero internet or cellular connectivity**.

Built specifically to solve **Smart India Hackathon (SIH) Problem Statement PS-26068**, this repository powers the offline edge computing layer for the **[WeatherGPT Android Application](https://github.com/Eurt-labs/WeatherGPT_Android)**.

---

## 🏛️ System Architecture

```
                                  WEATHERGPT ECOSYSTEM
                                  
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      WeatherGPT Android Client                         │
 │           • Jetpack Compose Material 3 UI  • Offline Cache             │
 └─────────────────┬──────────────────────────────────┬───────────────────┘
                   │ Online Mode                      │ Offline / Edge Mode
                   ▼                                  ▼
 ┌──────────────────────────────────┐   ┌─────────────────────────────────┐
 │       Render Cloud Backend       │   │     WeatherGPT_local (Edge)     │
 │  • Google Gemini 3.6 Flash       │   │  • High-performance GGUF Engine │
 │  • OpenMeteo Satellite Feed      │   │  • Qwen 2.5 7B / 3B / 1.5B      │
 │  • PostgreSQL & Supabase Sync    │   │  • Zero-cloud reliance          │
 └──────────────────────────────────┘   └───┬─────────────────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
       ┌───────────────────────────┐                 ┌───────────────────────────┐
       │   PC Edge Server (Active) │                 │  On-Device Mobile (Phase 2)│
       │ • FastAPI SSE Streaming   │                 │ • Direct Phone Execution  │
       │ • CPU/GPU AVX2 Inference  │                 │ • Qualcomm NPU / APU      │
       │ • USB / Wi-Fi Subnet Link │                 │ • ExecuTorch / ONNX       │
       └───────────────────────────┘                 └───────────────────────────┘
```

---

## 📁 Repository Structure

```
WeatherGPT_local/
├── PC/                       # Complete PC / Laptop Offline AI Engine
│   ├── models/               # Quantized GGUF model weights
│   ├── config.py             # Inference parameters & SIH domain system prompts
│   ├── download_model.py     # Automated HuggingFace downloader
│   ├── model_engine.py       # llama-cpp-python streaming inference wrapper
│   ├── main.py               # FastAPI server matching Render contract
│   ├── requirements.txt      # Python dependencies
│   ├── run_pc_server.bat     # 1-click Windows launcher
│   └── README.md             # Dedicated PC server documentation
├── Mobile/                   # Phase 2: Direct On-Device Mobile Integration
│   └── README.md             # Mobile roadmap & architecture specifications
├── .gitignore                # Production ignore rules (weights, venv, cache)
├── LICENSE                   # Apache 2.0 Open Source License
└── README.md                 # Project root documentation
```

---

## 🚀 Quickstart: Running the PC Offline Server

### 1. Requirements
- **PC:** Windows 10/11, 8GB+ RAM, 6GB free disk space.
- **Python:** Python 3.10 to 3.14.
- **Phone:** Android device with [WeatherGPT Android App](https://github.com/Eurt-labs/WeatherGPT_Android).

### 2. 1-Click Launch
1. Open the **`PC`** folder.
2. Double-click **`run_pc_server.bat`**.
3. Choose your model size:
   - **`7b`** (Recommended): Qwen 2.5 7B Instruct (Q4_K_M ~4.7 GB) — High-quality reasoning.
   - **`3b`**: Qwen 2.5 3B Instruct (Q4_K_M ~2.1 GB) — Fast & lightweight.
   - **`1.5b`**: Qwen 2.5 1.5B Instruct (Q4_K_M ~1.0 GB) — Ultra-fast.
4. The server starts at `http://0.0.0.0:8000`.

---

## 📱 Connecting to WeatherGPT Android

### Option A: USB Cable (Zero Latency - Recommended)
1. Plug your Android phone into your PC via USB (with **USB Debugging** enabled).
2. Open terminal and run:
   ```bash
   adb reverse tcp:8000 tcp:8000
   ```
3. In the WeatherGPT Android App:
   - Go to **Settings ⚙️** -> **AI BACKEND & CONNECTION**.
   - Select **PC (USB)** (`http://localhost:8000`).
   - Tap **Test Local PC Server Connection** to verify.

### Option B: Local Wi-Fi / Hotspot
1. Connect PC and phone to the same Wi-Fi or phone hotspot.
2. Check your PC's IP address (shown in `run_pc_server.bat`, e.g. `192.168.1.15`).
3. In the Android App Settings:
   - Select **PC (Wi-Fi)**.
   - Enter `http://<YOUR_PC_IP>:8000`.
   - Tap **Test Local PC Server Connection**.

---

## 🎯 Sector-Specific Domain Intelligence

WeatherGPT Local incorporates pre-configured system prompts tailored to specialized Indian user groups:
- 🌾 **Kisan (Farmer):** Sowing advice, irrigation timing, soil moisture utilization, crop diseases, regional language communication.
- 🚨 **Disaster Command Officer:** Barometric pressure analysis, river flood risks, actionable civil advisory alerts.
- 🚗 **Urban Commuter:** Rain windows, fog visibility, Air Quality (AQI) safety alerts.
- ✈️ **Aviation & Logistics:** Crosswind components, cloud ceilings, turbulence indicators.
- 🌍 **General Citizen:** Real-time atmospheric insights and weather interpretations.

---

## 📜 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.\n
# Mobile Experimental On-Device GGUF Research 📱🧪

> [!NOTE]
> **RESEARCH DIRECTORY ONLY**:
> The primary production mobile application is **[`WeatherGPT_Android`](https://github.com/Eurt-labs/WeatherGPT_Android)**. In production, users run the Android phone app directly, which communicates with the **[`WeatherGPT_Backend`](https://github.com/Eurt-labs/WeatherGPT_Backend)** on Render and uses on-device SQLite and telemetry caches when offline.
>
> This directory is strictly an **internal experimental research track** investigating embedded `llama.cpp` C++ Android NDK builds and mobile quantization.

---

## 🎯 Research Scope & Exploration

- Evaluating embedded ARM64-v8a NDK libraries (`libllama.so`).
- Benchmarking memory consumption and thermal performance of sub-2B parameter models under Android's Low Memory Killer (LMK).
- Exploring hardware acceleration across mobile GPUs and NPUs (Qualcomm QNN / Vulkan).

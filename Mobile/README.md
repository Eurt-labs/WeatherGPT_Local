# Phase 2: Direct On-Device Mobile Integration

This directory is designated for **Phase 2** of the offline AI initiative: running compact quantized models directly on the Android mobile device without needing an external PC server.

---

## 🎯 Objective

Enable the **WeatherGPT Android application** to perform local LLM inference directly on mobile hardware (Snapdragon, MediaTek, Tensor) with zero cellular data and zero local network infrastructure.

---

## 🏗️ Technical Architecture & Approach

| Component | Target Technology | Description |
|---|---|---|
| **Quantization** | Q3_K_S / Q4_K_M (1.5B - 3B) | Quantized to ~1.0 GB to safely operate under Android's Low Memory Killer (LMK). |
| **Runtime Engine** | llama.cpp Android NDK / ExecuTorch | Native C++ JNI bindings embedded directly inside the Android `.apk`. |
| **Hardware Acceleration** | Qualcomm QNN / Vulkan / OpenCL | Offloading matrix multiplication to mobile GPU / NPU for fast token generation. |
| **Fallback Strategy** | Graceful Degradation | App automatically falls back: Render Cloud -> Local PC Edge -> On-Device Mobile. |

---

## 🗺️ Roadmap

- [x] **Phase 1 (Active):** Standalone Local PC Server running Qwen 2.5 GGUF with drop-in FastAPI SSE streaming for high-quality testing.
- [ ] **Phase 2.1:** Android NDK C++ build integration (`libllama.so` with ARM64-v8a optimizations).
- [ ] **Phase 2.2:** JNI Kotlin wrapper and streaming callback interface.
- [ ] **Phase 2.3:** On-device model downloader and local asset verification.
- [ ] **Phase 2.4:** Benchmark power consumption, memory footprint, and thermal throttling.\n
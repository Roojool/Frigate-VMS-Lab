# Hardware Profiles & Acceleration Reference

This document provides a standardized template for recording test hardware environments and catalogues planned hardware acceleration evaluation targets for the Frigate VMS Lab.

---

## 1. Standard Hardware Evaluation Template

When publishing experimental benchmark runs, record the physical host topology using this standardized schema:

| Parameter | Specification Field | Example Entry |
| :--- | :--- | :--- |
| **Host CPU** | Processor model, cores, frequency | Intel Core i5-12400 (6C/12T, up to 4.4 GHz) |
| **Host GPU** | Integrated or discrete GPU | Intel UHD Graphics 730 |
| **NPU / Accelerator** | Edge AI coprocessor | Google Coral M.2 / Hailo-8 M.2 |
| **Host RAM** | Installed memory & technology | 32 GB DDR4-3200 CL16 |
| **Operating System** | OS distribution & kernel version | Ubuntu 24.04 LTS (Kernel 6.8.0) |
| **Docker Engine** | Container runtime & build version | Docker Community 26.1.1 |
| **Frigate Version** | Upstream container release tag | `0.18.0` (`ghcr.io/blakeblackshear/frigate:0.18.0`) |
| **Camera Count** | Physical cameras under test | 2 cameras |
| **Camera Model(s)** | Sensor / make / model | 4MP IP PoE Turret (Model sanitized) |
| **Source Resolution** | Ingest stream dimensions | 2560×1440 @ 20 fps (Main) / 704×480 @ 15 fps (Sub) |
| **Detect Resolution** | Dimension passed to decode engine | 1280×720 @ 5 fps |
| **Video Codec** | Stream compression format | H.264 (High Profile, Constant GOP) |
| **Network Topology** | Switch backplane, PoE budget, cabling | 8-port GbE PoE+ (802.3at), Cat6 UTP, MTU 1500 |

> [!CAUTION]
> Never publish hardware serial numbers, MAC addresses, internal LAN IP addresses, or camera GUIDs in benchmark outputs.

---

## 2. Operating System & Platform Assumptions

### Linux Native Docker (Supported Baseline)
Frigate is natively designed for Linux. The official deployment model relies on Linux kernel device access (`/dev/dri/renderD128` for Intel VAAPI, `/dev/apex_0` for Coral PCIe TPUs, or NVIDIA Container Toolkit). Benchmark baselines for this lab target native Linux installations.

### Windows / WSL2 (Experimental / Development Environment)
Frigate does not officially support native Windows. While Frigate containers can be executed within Windows Subsystem for Linux (WSL2) or Docker Desktop for development and configuration validation, this environment is strictly labeled:
```text
STATUS: EXPERIMENTAL / DEVELOPMENT ENVIRONMENT ONLY
```
Virtualization translation overhead, Hyper-V virtual network adapters, and Windows host GPU scheduling introduce measurement noise that invalidates production performance comparisons.

---

## 3. Hardware Acceleration Roadmap & Status

All hardware acceleration targets are documented with supported upstream presets. Unvalidated paths are explicitly marked `NOT YET MEASURED`.

### Target A: Commodity x86 CPU (Baseline)
- **Status**: Supported in baseline configuration.
- **Detector**: Software CPU inference (`type: cpu`, 2–4 threads).
- **Video Decode**: Software ffmpeg decode.
- **Empirical Status**: `NOT YET MEASURED` *(protocol defined in EXP-001)*.

### Target B: Intel Integrated GPU (iGPU) with QuickSync / VAAPI
- **Status**: Upstream supported via `/dev/dri/renderD128`.
- **Decode**: Hardware VAAPI/QSV (`hwaccel_args: preset-vaapi`).
- **Inference**: OpenVINO CPU/iGPU detector (`type: openvino`, `device: GPU`).
- **Empirical Status**: `NOT YET MEASURED`.

### Target C: Dedicated Edge AI Accelerator (Google Coral TPU)
- **Status**: Upstream supported via PCIe or USB.
- **Decode**: Host CPU or iGPU.
- **Inference**: EdgeTPU runtime (`type: edgetpu`, `device: pci` or `usb`).
- **Empirical Status**: `NOT YET MEASURED`.

### Target D: Raspberry Pi 5
- **Status**: Future research evaluation target.
- **Architecture**: ARM64 (BCM2712, 4× Cortex-A76).
- **Decode**: Software CPU decode (RPI5 lacks hardware H.264 decode blocks).
- **Inference**: CPU or PCIe Hailo-8L / Coral.
- **Empirical Status**: `NOT YET MEASURED`.

### Target E: Hailo-8 / Hailo-8L NPU
- **Status**: Future research evaluation target.
- **Inference**: HailoRT runtime.
- **Empirical Status**: `NOT YET MEASURED`.

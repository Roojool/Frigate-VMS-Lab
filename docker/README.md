# Docker Deployment Guide

This directory provides reference container deployment configurations for the Frigate VMS Lab research environment.

---

## Deployment Architecture

Frigate includes an **integrated go2rtc instance** by default. Therefore, the standard lab architecture deploys a single container:

```text
IP Camera (RTSP)
       ↓
Frigate Container (ghcr.io/blakeblackshear/frigate:stable)
   ├── Integrated go2rtc (RTSP Restreaming, WebRTC)
   ├── Detect Pipeline (Motion Detection & Object Detection)
   ├── Record Pipeline (Segment Writing)
   └── REST / Stats API (:5000)
```

A standalone external go2rtc container is **not** part of the default deployment. External go2rtc setups are reserved exclusively for **optional / advanced experiments** comparing integrated vs. decoupled go2rtc resource consumption.

---

## Operating System & Environment Support

- **Supported Reference Baseline**: Native Linux with Docker Engine (Ubuntu LTS / Debian). Linux is the officially supported deployment environment for Frigate and provides direct kernel-level access to video decode accelerators (`/dev/dri`) and TPUs/NPUs.
- **Windows / WSL2**: Categorized as an **EXPERIMENTAL / DEVELOPMENT ENVIRONMENT**. While Frigate can be spun up inside WSL2 or Docker Desktop for testing configuration files and pipeline collectors, Windows is not officially supported upstream for production VMS deployments due to virtualization overhead, GPU passthrough friction, and network translation layers.

---

## Key Configuration Parameters

### Shared Memory (`shm_size`)
Frigate uses shared memory (`/dev/shm`) to pass uncompressed video frames between decode, motion detection, and object detection processes. If `shm_size` is too small, processes will crash with bus errors.

Baseline formula:
$$\text{Memory per camera (MB)} = \frac{\text{Width} \times \text{Height} \times 1.5 \times (\text{Detection FPS} + 1)}{1024 \times 1024} \times \text{Buffer Count}$$

For baseline experiments (1–2 cameras at 720p or 1080p), `shm_size: "256mb"` is generally sufficient. For multi-camera 4K scaling, 512MB–1GB may be required.

### Variable Interpolation Distinction
Notice the difference between Docker Compose and Frigate syntax:
- **Docker Compose (`compose.yml`)**: Uses `${VARIABLE_NAME}` syntax to read variables from the host `.env` file.
- **Frigate Configuration (`frigate.yml`)**: Uses `{FRIGATE_VARIABLE_NAME}` substitution (only variables prefixed with `FRIGATE_` are recognized by Frigate).

Example workflow:
1. Define in `.env`: `FRIGATE_RTSP_PASSWORD=your_actual_password`
2. Pass via `compose.yml`:
   ```yaml
   environment:
     FRIGATE_RTSP_PASSWORD: ${FRIGATE_RTSP_PASSWORD}
   ```
3. Reference in `frigate.yml`:
   ```yaml
   rtsp://CAMERA_USERNAME:{FRIGATE_RTSP_PASSWORD}@CAMERA_1_HOST/STREAM_PATH
   ```

---

## Port Allocations

Only ports required for VMS operation and lab instrumentation are exposed:
- `5000`: Frigate Web UI and REST API (used by `frigate-vms-lab` collector to query `/api/stats`)
- `8554`: Integrated go2rtc RTSP restreaming port (for downstream consumers)
- `8555/tcp` & `8555/udp`: Integrated go2rtc WebRTC signalling and media transport

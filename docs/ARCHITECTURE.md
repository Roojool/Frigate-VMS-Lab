# System Architecture

This document details the architectural topology of the Frigate Video Management System (VMS) lab and its instrumentation framework.

---

## High-Level Topology

Frigate integrates [go2rtc](https://github.com/AlexxIT/go2rtc) internally to manage stream ingestion, transcoding, and restreaming. In the standard lab architecture, cameras stream once into the integrated go2rtc instance, which subsequently fans out streams to Frigate's detection engine, recording engine, and live WebRTC/MSE endpoints.

```mermaid
flowchart TD
    subgraph Camera_Layer["Camera Layer (Physical / PoE Network)"]
        Cam1["IP Camera 1<br/>(Substream + Mainstream)"]
        Cam2["IP Camera 2<br/>(Substream + Mainstream)"]
    end

    subgraph Frigate_Host["Frigate Container (Host / Virtualized Engine)"]
        subgraph Integrated_go2rtc["Integrated go2rtc (Stream Multiplexer)"]
            In1["RTSP Ingest Worker"]
            Restream["Local Restream Server<br/>(rtsp://127.0.0.1:8554)"]
            In1 --> Restream
        end

        subgraph Pipelines["Frigate Processing Pipelines"]
            DetectPipe["Detect Pipeline<br/>(Motion Detection -> Crop -> Tensor -> Detector)"]
            RecordPipe["Record Pipeline<br/>(Muxer -> Segment Cache -> Storage)"]
            LiveAPI["Live Streaming Engine<br/>(WebRTC / MSE / HLS)"]
            StatsAPI["Internal Telemetry API<br/>(/api/stats & /api/version)"]
        end

        Restream -->|Substream: 720p @ 5fps| DetectPipe
        Restream -->|Mainstream: 1080p @ 15fps| RecordPipe
        Restream -->|Low Latency| LiveAPI
    end

    subgraph Instrumentation["Experiment Instrumentation Suite"]
        Collector["frigate-vms-lab collector<br/>(SystemCollector, DockerCollector, FrigateCollector)"]
        Storage["Structured Artifacts<br/>(JSON & CSV)"]
        Analyzer["Statistical Analyzer & Reporter<br/>(Descriptive Stats & Markdown)"]

        StatsAPI -->|REST Polling| Collector
        Frigate_Host -.->|Docker Stats API| Collector
        HostOS["Host OS Metrics<br/>(CPU, RAM, Load)"] --> Collector

        Collector --> Storage
        Storage --> Analyzer
    end

    Cam1 -->|RTSP Stream| In1
    Cam2 -->|RTSP Stream| In1
```

---

## Why go2rtc Restreaming Matters

IP cameras typically support only a limited number of simultaneous RTSP clients (often 2–4 connections maximum) before their onboard microcontrollers overheat, drop frames, or reset.

Without a restreamer:
1. Frigate detect pipeline opens connection 1.
2. Frigate record pipeline opens connection 2.
3. User live view in web UI opens connection 3.
4. Second mobile client opens connection 4 $\rightarrow$ **Camera limits exceeded / packet loss occurs.**

With Frigate's **integrated go2rtc**:
- The camera transmits exactly **one** network stream per channel to the host.
- Integrated go2rtc receives the stream and shares it locally via internal loopback (`rtsp://127.0.0.1:8554/<name>`).
- Detection, recording, and multi-client live streaming all consume the local restream without imposing network or CPU load on the physical camera.

> [!NOTE]
> While a separate standalone go2rtc container can be deployed, Frigate includes go2rtc natively. The standard lab configuration uses the integrated instance to reflect standard production patterns. A standalone container is evaluated only as an optional advanced experiment.

---

## Detection vs. Recording Pipeline Separation

Frigate decouples video processing into two specialized pipelines:

```mermaid
graph LR
    Substream["Camera Substream<br/>(e.g., 1280x720 @ 5 fps)"] --> DecodeSub["FFmpeg Decode"]
    DecodeSub --> Motion["Motion Detection<br/>(Scene Pixel Change)"]
    Motion -->|Motion Found| Box["Bounding Box Crop"]
    Box --> Detector["Object Inference<br/>(CPU / Coral / NPU)"]

    Mainstream["Camera Mainstream<br/>(e.g., 1920x1080 @ 15-25 fps)"] --> PassThrough["FFmpeg Stream Copy<br/>(No Transcode)"]
    PassThrough --> Disk["Segment Writing & Storage"]
```

1. **Detect Pipeline**:
   - Decodes video frames to uncompressed pixel buffers.
   - Requires substantial CPU/GPU decode bandwidth.
   - Run at low resolution (substream: 720p or 360p) and low frame rate (5 fps) to minimize compute overhead.
2. **Record Pipeline**:
   - Performs direct stream copying (`-c copy`) without re-encoding video frames.
   - Minimal CPU utilization.
   - Run at native mainstream resolution (1080p, 4K) to maintain archival evidence quality.

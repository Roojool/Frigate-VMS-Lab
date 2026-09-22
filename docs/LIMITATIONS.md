# Research Limitations & Environmental Constraints

This document formalizes the methodological boundaries and environmental constraints governing research conducted within the Frigate VMS Lab.

---

## 1. Non-Generalizability Across Silicon Architectures

Video decoding and neural network inference behavior vary fundamentally across CPU architectures and accelerator silicon:
- **Instruction Sets**: An x86 processor supporting AVX-512 will exhibit markedly different vector decode throughput compared to an older processor limited to SSE4.2 or an ARM64 Cortex core.
- **Hardware Decode Pipelines**: Software CPU decoding scales linearly with frame count and resolution, whereas hardware-accelerated decoding (Intel QuickSync / VAAPI, NVIDIA NVDEC) offloads pixel reconstruction to fixed-function ASICs, decoupling decode load from general CPU cores.
- **Inference Runtimes**: TensorFlow Lite, OpenVINO, and TensorRT utilize distinct quantization strategies (FP32, FP16, INT8). Latency benchmarks obtained on one runtime cannot be transferred to another.

---

## 2. Environmental Noise & Confounding Factors

Empirical performance measurements in physical VMS deployments are subject to environmental fluctuations:
- **Thermal Throttling**: Embedded platforms (e.g., mini-PCs, Raspberry Pi units, fanless industrial chassis) often experience thermal down-clocking during sustained multi-stream decode. A 10-minute trial may exhibit performance degradation unrelated to VMS software efficiency.
- **Motion Entropy**: Video compression algorithms (H.264 / H.265) utilize inter-frame predictive coding (P-frames and B-frames). A scene with stationary background requires drastically fewer bits and lower decode compute than a scene with dense motion (e.g., wind-blown trees, rain, moving vehicles). Identical stream resolutions will yield divergent CPU utilization depending on scene activity.
- **Network Micro-bursts & PoE Budgeting**: Multi-camera stream synchronization over shared Ethernet switches can induce micro-burst packet loss if switch buffer queues overflow, causing artificial frame drops (`skipped_fps > 0`) independent of host processing capacity.

---

## 3. Synthetic vs. Physical RTSP Streams

While synthetic video generators (e.g., FFmpeg looping test videos into an RTSP server) offer reproducible deterministic bitstreams, they fail to replicate several physical camera characteristics:
- Clock drift between independent camera oscillators.
- Variable keyframe (I-frame) intervals under dynamic lighting transitions.
- Automatic Gain Control (AGC) noise spikes in low-light environments which inflate video entropy.

---

## 4. Software Boundaries & Versioning

Upstream Frigate and go2rtc are under active development. Optimizations, refactored FFmpeg filtergraphs, or changes in shared memory buffer structures between minor releases can alter benchmark metrics. Consequently:
- All reported benchmarks must document the exact upstream container release tag and go2rtc version.
- Cross-version comparisons must explicitly control for configuration syntax alterations.

---

## 5. Scope of Detection Metrics vs. Model Accuracy

The instrumentation provided by this lab captures computational pipeline performance (frame ingestion rates, decode throughput, frame drops, and detector invocation frequency). It does **not** evaluate labeled ground-truth object detection accuracy (such as mean Average Precision [mAP] or precision-recall curves against ground-truth datasets). Quantifying detection accuracy across resolution degradation is designated as future work; current metrics strictly measure resource cost and execution rates.

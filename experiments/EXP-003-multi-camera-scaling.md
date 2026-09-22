# EXP-003: Multi-Camera Concurrency & Scaling

---

## OBJECTIVE

Investigate how multi-camera stream concurrency scales system resources (CPU load, memory growth, and go2rtc network throughput) on commodity host hardware.

---

## HYPOTHESIS

Resource utilization will scale sub-linearly with stream count when go2rtc restreaming multiplexes connections, but decode bottlenecks will emerge as stream count increases without dedicated hardware video decode (VAAPI/QSV).

---

## CONTROLLED VARIABLES

- **Upstream Engine**: Frigate `v0.18.0` running in Linux Docker container.
- **Per-Camera Detect Stream**: 1280×720 @ 5 fps.
- **Per-Camera Record Stream**: 1920×1080 @ 15 fps (retained continuously).
- **Detector**: Software CPU detector (allocated thread pool: 4 threads).
- **Sample Interval**: 1.0 second.
- **Duration Per Trial**: 300 seconds (5 minutes).
- **Warm-up Period**: 30 seconds before measurement.

---

## INDEPENDENT VARIABLES

- **Camera Concurrency (Planned Conditions)**:
  1. Condition 1: 1 Camera stream
  2. Condition 2: 2 Concurrent camera streams
  3. Condition 3: 4 Concurrent camera streams

---

## DEPENDENT VARIABLES

- Overall Host CPU utilization (`cpu_percent`, mean, p50, p95)
- Overall Host Memory consumption (`memory_percent`, `used_bytes`)
- Container Network I/O (RX/TX bytes per second)
- Per-camera pipeline health (`camera_fps`, `process_fps`, `skipped_fps`, `detection_fps`)
- Stream stability and frame drop rate across camera instances

---

## PROCEDURE

1. Deploy condition configuration:
   - For 1 camera: use [`../configs/frigate.example.yml`](../configs/frigate.example.yml) copied to `configs/frigate.local.yml`.
   - For 2 cameras: use [`../configs/two-camera.example.yml`](../configs/two-camera.example.yml) copied to `configs/frigate.local.yml`.
   - For 4 cameras: extend configuration template with four RTSP streams.
2. Start Frigate container and verify all camera pipelines in Web UI.
3. Allow 30 seconds of warm-up.
4. Execute collection:
   ```bash
   frigate-vms-lab collect \
     --experiment-id EXP-003-CAM-<1|2|4> \
     --duration 300 \
     --warmup 30 \
     --interval 1.0 \
     --frigate-url http://127.0.0.1:5000 \
     --container frigate \
     --output results/EXP-003_cam_<1|2|4>.json \
     --csv results/EXP-003_cam_<1|2|4>.csv
   ```
5. Generate reports and evaluate per-stream degradation and aggregate host metrics.

---

## METRICS

- **Aggregate CPU & Memory**: System-wide headroom under multi-camera load.
- **Per-Camera `process_fps`**: Decoder throughput consistency across streams.
- **Per-Camera `skipped_fps`**: Detection pipeline starvation indicators.
- **Container Network RX**: Ingest data volume across all active feeds.

---

## RESULTS

```text
NOT YET MEASURED
```

*Multi-camera physical benchmark trials have not yet been performed. All conditions reflect planned research protocols.*

---

## LIMITATIONS

- Network switch backplane capacity and PoE budget may become confounding variables when scaling physical cameras.
- CPU thermal throttling on small-form-factor devices (e.g. mini-PCs) can skew longer trials.
- Camera timing jitter (differing RTSP clock references) may cause intermittent synchronization overhead.

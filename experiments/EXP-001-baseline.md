# EXP-001: Baseline Single-Camera Resource Profile

---

## OBJECTIVE

Establish the empirical baseline resource utilization and pipeline timing for a single standard IP camera connected to Frigate via integrated go2rtc, with separated detection and recording stream roles.

---

## HYPOTHESIS

A single IP camera utilizing a separate low-resolution substream (1280×720 @ 5 fps) for detection and high-resolution mainstream (1920×1080 @ 15–25 fps) for recording will maintain stable memory allocation and sub-20% single-thread CPU consumption during periods without continuous motion, with 0 skipped frames (`skipped_fps == 0`).

---

## CONTROLLED VARIABLES

- **Upstream Engine**: Frigate `v0.18.0` running in Linux Docker container.
- **Detector**: Software CPU detector (2 threads).
- **Stream Ingestion**: Frigate-integrated go2rtc restreaming.
- **Recording Role**: Mainstream (1080p, continuous 24/7 retention mode).
- **Sampling Interval**: 1.0 second.
- **Baseline Duration**: 600 seconds (10 minutes).
- **Warm-up Period**: 30 seconds prior to metric logging.

---

## INDEPENDENT VARIABLES

- **Baseline Profile**: Baseline single camera operation (fixed configuration).

---

## DEPENDENT VARIABLES

- Host CPU utilization (`cpu_percent`)
- Host Memory utilization (`memory_percent`, `used_bytes`)
- Container CPU & Memory usage (`docker.containers[frigate]`)
- Ingest Frame Rate (`camera_fps`)
- Processing Frame Rate (`process_fps`)
- Skipped Frames (`skipped_fps`)
- Detector Frame Rate (`detection_fps`)

---

## PROCEDURE

1. Instantiate local configuration from template:
   ```bash
   cp configs/frigate.example.yml configs/frigate.local.yml
   ```
2. Deploy Frigate container on target Linux host using [`../docker/compose.example.yml`](../docker/compose.example.yml) and [`../configs/frigate.example.yml`](../configs/frigate.example.yml).
3. Set local camera authentication token:
   ```bash
   export FRIGATE_RTSP_PASSWORD="<local-secret>"
   ```
4. Verify stream health in Frigate Web UI (`http://127.0.0.1:5000`).
5. Execute the baseline collector:
   ```bash
   frigate-vms-lab collect \
     --experiment-id EXP-001 \
     --duration 600 \
     --warmup 30 \
     --interval 1.0 \
     --frigate-url http://127.0.0.1:5000 \
     --container frigate \
     --output results/EXP-001_run.json \
     --csv results/EXP-001_timeseries.csv
   ```
6. Generate the analysis and markdown report:
   ```bash
   frigate-vms-lab analyze results/EXP-001_run.json
   frigate-vms-lab report results/EXP-001_run.json --output results/EXP-001_report.md
   ```

---

## METRICS

- **`camera_fps`**: Rate of video frames pulled from the RTSP camera feed by go2rtc/ffmpeg.
- **`process_fps`**: Rate of video frames decoded and passed to motion analysis.
- **`skipped_fps`**: Rate of frames dropped due to CPU or decoder queue saturation.
- **`detection_fps`**: Rate at which bounding-box inference tasks are dispatched to the detector.
- **`cpu_percent`**: Total host CPU percentage utilized across all cores.
- **`memory_percent`**: Percentage of total host physical memory in active use.

---

## RESULTS

```text
NOT YET MEASURED
```

*Baseline physical experiments are pending execution on dedicated lab hardware. The protocol and automated collection tooling are verified and operational.*

---

## LIMITATIONS

- Baseline results reflect a stationary indoor or outdoor scene with natural ambient motion variance.
- High motion density (e.g. foliage in heavy wind or busy traffic) increases detector dispatch frequency and will alter CPU metrics.
- Findings are coupled to the specific host CPU architecture and network switch topology.

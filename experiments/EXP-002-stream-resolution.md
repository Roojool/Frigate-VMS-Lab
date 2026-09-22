# EXP-002: Detect Stream Resolution Tradeoffs

---

## OBJECTIVE

Quantify the relationship between detect stream decode resolution and system resource utilization (CPU, RAM, and `process_fps` stability) in Frigate.

---

## HYPOTHESIS

Increasing the detect stream resolution from 640×360 to 1920×1080 will result in higher software video decode CPU utilization and shared memory consumption, with increased likelihood of `skipped_fps > 0` on entry-level host CPUs.

> [!NOTE]
> Ground-truth object detection accuracy evaluation (e.g. mAP or recall curves against labeled test datasets) is designated as future work. The current lab tooling measures computational decode throughput, frame pacing, and resource consumption.

---

## CONTROLLED VARIABLES

- **Upstream Engine**: Frigate `v0.18.0` running in Linux Docker container.
- **Detector**: Software CPU detector (2 threads).
- **Target Frame Rate**: 5 fps for detection across all conditions.
- **Recording Stream**: Mainstream recording disabled to isolate detect pipeline costs.
- **Sample Interval**: 1.0 second.
- **Trial Duration**: 300 seconds (5 minutes per condition).
- **Warm-up Period**: 30 seconds before each trial.

---

## INDEPENDENT VARIABLES

- **Detect Stream Resolution (Planned Conditions)**:
  1. Condition A: `640×360` (Low-resolution substream)
  2. Condition B: `1280×720` (Standard HD substream)
  3. Condition C: `1920×1080` (Full HD mainstream used as detect)

---

## DEPENDENT VARIABLES

- CPU utilization (`cpu_percent`, mean and p95)
- Shared memory allocation (`/dev/shm` pressure and memory percent)
- Ingest Frame Rate (`camera_fps`)
- Processing Frame Rate (`process_fps`)
- Frame Drops (`skipped_fps`)
- Detector Dispatch Rate (`detection_fps`)

---

## PROCEDURE

For each condition ($A, B, C$):
1. Configure `detect.width` and `detect.height` in `configs/frigate.local.yml` corresponding to the condition.
2. Restart the Frigate container:
   ```bash
   docker compose -f docker/compose.example.yml restart
   ```
3. Allow a 30-second warm-up stabilization window.
4. Execute collection:
   ```bash
   frigate-vms-lab collect \
     --experiment-id EXP-002-COND-<A|B|C> \
     --duration 300 \
     --warmup 30 \
     --interval 1.0 \
     --frigate-url http://127.0.0.1:5000 \
     --container frigate \
     --output results/EXP-002_cond_<A|B|C>.json \
     --csv results/EXP-002_cond_<A|B|C>.csv
   ```
5. Compare resulting descriptive statistics across all three trials.

---

## METRICS

- **`cpu_percent`**: Host CPU demand under software decode load.
- **`process_fps`**: Maintained decode rate through ffmpeg.
- **`skipped_fps`**: Decoder drops indicating CPU saturation.
- **`memory_percent`**: Resident set size and shared memory impact.

---

## RESULTS

```text
NOT YET MEASURED
```

*Planned conditions only. Empirical comparative trials have not yet been conducted. The repository provides the instrumentation and protocol framework.*

---

## LIMITATIONS

- **Accuracy Scope**: Labeled ground-truth detection accuracy (mAP / precision-recall) is not evaluated by this protocol; metrics capture purely computational decode and resource consumption.
- Results depend heavily on hardware acceleration availability; software CPU decode represents the worst-case scenario.
- Video stream complexity (high entropy scenes with foliage) increases H.264/H.265 decode overhead compared to low entropy static scenes.
- Network bandwidth consumption scales with resolution if substream vs mainstream are both pulled over the LAN.

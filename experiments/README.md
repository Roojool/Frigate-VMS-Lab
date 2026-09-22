# Experiment Matrix & Protocols

This directory contains formal scientific protocols for empirical experimentation within the Frigate VMS Lab.

---

## Protocol Standards

Every experiment protocol follows a rigorous, reproducible structure:
1. **OBJECTIVE**: The specific research question being tested.
2. **HYPOTHESIS**: Testable prediction of system behavior.
3. **CONTROLLED VARIABLES**: System parameters held constant (e.g., model architecture, host OS, codec).
4. **INDEPENDENT VARIABLES**: The manipulated variable (e.g., resolution, camera count).
5. **DEPENDENT VARIABLES**: Measured metrics (`cpu_percent`, `memory_percent`, `camera_fps`, `process_fps`, `skipped_fps`, `detection_fps`).
6. **PROCEDURE**: Step-by-step setup, warm-up, and sampling run commands.
7. **METRICS**: Explicit definitions of logged parameters.
8. **RESULTS**: Empirical findings. Strictly marked `NOT YET MEASURED` until verified physical benchmarks are run.
9. **LIMITATIONS**: Explicit boundaries on reproducibility and conclusions.

---

## Active Experiment Matrix

| ID | Title | Independent Variable | Test Conditions | Status |
| :--- | :--- | :--- | :--- | :--- |
| [`EXP-001`](EXP-001-baseline.md) | Baseline Single-Camera Resource Profile | Baseline Profile | 1 camera, 720p detect, 1080p record, CPU detector | `NOT YET MEASURED` |
| [`EXP-002`](EXP-002-stream-resolution.md) | Detect Stream Resolution Tradeoffs | Detection Resolution | 640×360, 1280×720, 1920×1080 | `NOT YET MEASURED` |
| [`EXP-003`](EXP-003-multi-camera-scaling.md) | Multi-Camera Stream Scaling | Stream Concurrency | 1 Camera, 2 Cameras, 4 Cameras | `NOT YET MEASURED` |

---

## Execution Command Template

To execute an experiment protocol locally without exposing credentials:

```bash
# Instantiate user-specific local configuration
cp configs/frigate.example.yml configs/frigate.local.yml

# Set local camera password in environment
export FRIGATE_RTSP_PASSWORD="your_actual_password"

# Launch Frigate with the reference Docker Compose deployment
docker compose -f docker/compose.example.yml up -d

# Execute the experiment collector with warm-up stabilization
frigate-vms-lab collect \
  --experiment-id EXP-001 \
  --duration 600 \
  --warmup 30 \
  --interval 1.0 \
  --frigate-url http://localhost:5000 \
  --container frigate \
  --output results/EXP-001_run.json \
  --csv results/EXP-001_timeseries.csv

# Generate publication markdown report
frigate-vms-lab report results/EXP-001_run.json --output results/EXP-001_report.md
```

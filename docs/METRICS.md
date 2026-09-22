# Metrics Dictionary & Instrumentation Reference

This document provides definitive specifications for all telemetry metrics recorded, analyzed, and reported by the Frigate VMS Lab.

---

## 1. Frigate Pipeline Rate Metrics

Frigate exposes pipeline rates per configured camera via its `/api/stats` endpoint. To avoid ambiguous labeling, these rates are rigorously distinguished:

| Metric Name | Unit | Definition | Interpretation & Failure Modes |
| :--- | :--- | :--- | :--- |
| **`camera_fps`** | frames/sec | Frame rate actively **consumed from the camera feed** by ffmpeg / go2rtc. | If this drops below the camera's configured nominal output rate, network packet loss, RTSP handshake timeouts, or camera hardware strain is occurring. |
| **`process_fps`** | frames/sec | Frame rate actively **decoded and evaluated** by the motion detection engine. | In a healthy pipeline, this matches the configured `detect.fps` (e.g. 5 fps). If this drops below `detect.fps`, the CPU/GPU decoder is overloaded. |
| **`skipped_fps`** | frames/sec | Frame rate of **frames dropped / skipped** by Frigate because processing queues are backed up. | Should ideally be `0.0`. Sustained values $> 0$ indicate severe pipeline bottlenecks where frames are discarded prior to object detection. |
| **`detection_fps`** | frames/sec | Rate of **inference executions dispatched** to the object detection model. | Represents how many frames contained motion regions requiring neural network classification. Rises when motion occurs; drops to zero during static scenes. |

---

## 2. Host Operating System Metrics

Collected via `psutil` directly on the host machine:

| Metric Name | Unit | Description | Platform Behavior |
| :--- | :--- | :--- | :--- |
| **`cpu_percent`** | % | Aggregate host CPU utilization across all cores. | Sampled non-blocking over elapsed tick interval. |
| **`cpu_cores_percent`** | list[%] | Per-core host CPU utilization breakdown. | Enables detection of single-core thread pinning or decoder core saturation. |
| **`memory.total_bytes`** | bytes | Total installed physical RAM on the host. | Constant over run. |
| **`memory.used_bytes`** | bytes | Resident physical RAM in active use by OS and processes. | Excludes file caches and buffers. |
| **`memory.percent`** | % | Percentage of total physical RAM in active use. | Monitored to detect memory leaks in long trials. |
| **`load_average`** | float[3] | 1, 5, and 15-minute system load averages. | Supported on Linux and macOS (`os.getloadavg()`). Evaluates to `null` on Windows hosts. |

---

## 3. Container-Level Metrics

Collected via Docker daemon statistics when containerization is available:

| Metric Name | Unit | Description |
| :--- | :--- | :--- |
| **`docker.containers[].cpu_percent`** | % | CPU percentage consumed specifically by the container process tree. |
| **`docker.containers[].memory_usage`** | string / bytes | Memory utilized by container compared to container limit. |
| **`docker.containers[].memory_percent`** | % | Percentage of container memory limit currently allocated. |
| **`docker.containers[].net_io`** | string | Cumulative network inbound (RX) and outbound (TX) traffic. |

---

## 4. RTSP Stream Probe Metrics

Collected via `ffprobe` during observed state inspection:

| Metric Name | Unit | Description |
| :--- | :--- | :--- |
| **`codec`** | string | Video compression format (e.g., `h264`, `hevc`). |
| **`width`** | pixels | Horizontal frame dimension delivered by stream. |
| **`height`** | pixels | Vertical frame dimension delivered by stream. |
| **`nominal_fps`** | frames/sec | Nominal frame rate encoded in container headers (`avg_frame_rate` / `r_frame_rate`). |
| **`bitrate_bps`** | bits/sec | Bitrate reported by stream container metadata (where available). |
| **`probe_duration_seconds`** | seconds | Wall-clock time required for `ffprobe` to complete stream handshake. |

---

## 5. Statistical Aggregations

For all sampled time-series metrics, only defensible descriptive statistics are computed:

- **`sample_count`**: Number of valid, non-null observations in the trial.
- **`mean`**: Arithmetic average.
- **`median`**: 50th percentile (central tendency robust to burst spikes).
- **`min` / `max`**: Absolute floor and ceiling observed during the sampling window.
- **`stdev`**: Sample standard deviation ($N-1$ degrees of freedom).
- **`p50`**: 50th percentile (computed via linear interpolation).
- **`p95`**: 95th percentile, isolating worst-case latency and utilization spikes while discarding extreme single-sample outliers.

> [!NOTE]
> Statistical significance (p-values, ANOVA, t-tests) is deliberately omitted unless an experiment specifically establishes formal randomized treatment trials.

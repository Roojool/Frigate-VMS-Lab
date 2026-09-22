# Reference Configurations

This directory contains sanitized, reproducible configuration templates for Video Management System experimentation with Frigate and go2rtc.

---

## Configuration Inventory

| File | Purpose | Architecture |
| :--- | :--- | :--- |
| [`frigate.example.yml`](file:///configs/frigate.example.yml) | Baseline 1-camera research profile (EXP-001) | Frigate with integrated go2rtc |
| [`two-camera.example.yml`](file:///configs/two-camera.example.yml) | Multi-camera scaling profile (EXP-003) | Frigate with integrated go2rtc |
| [`go2rtc.example.yml`](file:///configs/go2rtc.example.yml) | Optional standalone go2rtc profile | Decoupled go2rtc for comparative experiments |

---

## Safe Placeholder Convention

All configurations in this repository strictly enforce non-routable symbolic placeholders to prevent credential and network topology exposure:

| Symbolic Placeholder | Description | Example Target |
| :--- | :--- | :--- |
| `CAMERA_1_HOST` | Hostname or IP of primary camera | e.g. `cam-entry.lan` |
| `CAMERA_2_HOST` | Hostname or IP of secondary camera | e.g. `cam-driveway.lan` |
| `CAMERA_USERNAME` | Service account for RTSP camera feed | e.g. `frigate_service` |
| `{FRIGATE_RTSP_PASSWORD}` | Password substitution token | Read from environment |
| `STREAM_PATH_SUB` | Camera RTSP substream URI path | e.g. `h264Preview_01_sub` |
| `STREAM_PATH_MAIN` | Camera RTSP mainstream URI path | e.g. `h264Preview_01_main` |

---

## Variable Substitution vs. Interpolation

Take careful note of the two different variable mechanisms:

1. **Frigate Configuration Substitution (`{FRIGATE_...}`)**:
   Frigate directly parses `{FRIGATE_VARIABLE}` strings from YAML keys and substitutes them from container environment variables at runtime. Only environment variables prefixed with `FRIGATE_` are eligible for substitution.
   ```yaml
   rtsp://CAMERA_USERNAME:{FRIGATE_RTSP_PASSWORD}@CAMERA_1_HOST/STREAM_PATH
   ```

2. **Docker Compose Interpolation (`${...}`)**:
   Docker Compose substitutes `${VARIABLE}` on the host machine before launching the container:
   ```yaml
   environment:
     FRIGATE_RTSP_PASSWORD: ${FRIGATE_RTSP_PASSWORD}
   ```

---

## Validating Configurations

You can validate any configuration file against YAML syntax errors and accidental credential/private IP leakage using the lab CLI:

```bash
frigate-vms-lab validate-config configs/frigate.example.yml
```

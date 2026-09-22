# Privacy, Security & Sanitization Protocol

Surveillance systems and Closed-Circuit Television (CCTV) feeds inherently capture sensitive personal data, physical spaces, and network authentication tokens. The Frigate VMS Lab enforces strict privacy, security, and data sanitization protocols.

---

## 1. Zero Private Footage in Git

- **Absolute Prohibition**: No video recordings, raw RTSP packet captures, or identifiable image snapshots from physical camera feeds may be committed to this repository.
- **Synthesized Data**: If test media is required for automated test suites, it must be generated synthetically via FFmpeg (e.g. test patterns, SMPTE bars, or artificial motion boxes).
- **Transient Storage**: Docker recordings and cache volumes (`./storage/`, `/tmp/cache/`) are ignored by `.gitignore` and must never be staged.

---

## 2. Credential Sanitization & Masking

### Automated Stream URL Redaction
The `frigate-vms-lab` collection tooling includes built-in credential redaction (`sanitize_url`). Any URL probed or recorded in experimental output JSON has user passwords masked:
```text
Raw:        rtsp://admin:SecretPass123@192.0.2.10/stream1
Sanitized:  rtsp://admin:***@192.0.2.10/stream1
```

### Environment Variable Substitution
Never hardcode passwords in configuration files. Frigate configurations must use `{FRIGATE_RTSP_PASSWORD}` substitution tokens, supplied at container launch via Docker Compose environment variables.

---

## 3. Network Topology Redaction & RFC1918 Placeholders

Public configuration examples and experiment protocols must not expose private network topology, routing architecture, or device identifiers.

### Conceptual RFC1918 Private Address Ranges
In physical local area networks, surveillance cameras commonly reside within private IPv4 subnets defined by RFC 1918:
- `10.0.0.0/8` (e.g., enterprise CCTV VLANs)
- `172.16.0.0/12` (e.g., intermediate subnets)
- `192.168.0.0/16` (e.g., standard residential subnets)

While these private IP spaces are technically non-routable on the public Internet, committing specific local IPs and subnet schemes into public git repositories exposes internal network layout and device addressing.

### Mandatory Symbolic Placeholders
To eliminate all risk of private IP disclosure, configuration examples in this repository strictly mandate symbolic hostname placeholders:
- `CAMERA_1_HOST`
- `CAMERA_2_HOST`
- `CAMERA_USERNAME`
- `STREAM_PATH`

---

## 4. Personally Identifiable Information (PII)

- Benchmark experiments measure **system resource consumption** (CPU, RAM, frame rates, skip rates), not human behavioral tracking or facial biometrics.
- Bounding box coordinates, event clip thumbnails, and label classifications involving identifiable persons are excluded from public results artifacts.

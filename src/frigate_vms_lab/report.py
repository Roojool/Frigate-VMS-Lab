"""Generates reproducible Markdown research reports from experiment data."""

from __future__ import annotations

from typing import Any


def generate_markdown_report(data: dict[str, Any]) -> str:
    """Transform structured experiment data into a publication-ready Markdown report."""
    exp_id = data.get("experiment_id", "UNKNOWN-EXP")
    timestamp = data.get("timestamp", "N/A")
    duration = data.get("duration_seconds", 0)
    warmup = data.get("warmup_seconds", 0)
    env = data.get("environment", {})
    summary = data.get("summary", {})
    streams = data.get("streams", [])

    lines = [
        f"# Experiment Report: {exp_id}",
        "",
        f"- **Execution Timestamp (UTC)**: `{timestamp}`",
        f"- **Benchmark Duration**: `{duration}s` (Warm-up: `{warmup}s`)",
        f"- **Host Platform**: `{env.get('platform', 'N/A')}` (`{env.get('machine', 'N/A')}`)",
        f"- **Frigate Version**: `{env.get('frigate_version') or 'Not Reported / Offline'}`",
        f"- **Docker Availability**: `{env.get('docker_available', False)}`",
        f"- **Total System RAM**: `{_format_bytes(env.get('memory_total_bytes'))}`",
        "",
        "---",
        "",
        "## 1. Probed Stream Characteristics",
        "",
    ]

    if streams:
        lines.extend([
            "| Stream URL | Codec | Resolution | Nominal FPS | Bitrate (kbps) |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for s in streams:
            url = s.get("url", "N/A")
            codec = s.get("codec", "N/A")
            res = f"{s.get('width', '?')}x{s.get('height', '?')}" if s.get("video_stream_found") else "No video stream"
            fps = s.get("nominal_fps", "N/A")
            br = round(s["bitrate_bps"] / 1000, 1) if s.get("bitrate_bps") else "N/A"
            lines.append(f"| `{url}` | {codec} | {res} | {fps} | {br} |")
        lines.append("")
    else:
        lines.extend(["*No RTSP streams were probed for this experiment run.*", ""])

    lines.extend([
        "## 2. System Resource Statistics",
        "",
        "| Metric | Samples | Mean | Median | Min | Max | StDev | p50 | p95 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    sys_cpu = summary.get("system", {}).get("cpu_percent", {})
    sys_mem = summary.get("system", {}).get("memory_percent", {})
    lines.append(_format_stat_row("System CPU (%)", sys_cpu))
    lines.append(_format_stat_row("System RAM (%)", sys_mem))
    lines.append("")

    # Docker section
    docker_summary = summary.get("docker", {})
    if docker_summary:
        lines.extend([
            "## 3. Container Resource Statistics",
            "",
            "| Container | Metric | Samples | Mean | Median | Min | Max | StDev | p50 | p95 |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for cname, cstats in docker_summary.items():
            lines.append(_format_stat_row(f"`{cname}` CPU (%)", cstats.get("cpu_percent", {}), prefix_cols=[cname]))
            lines.append(_format_stat_row(f"`{cname}` RAM (%)", cstats.get("memory_percent", {}), prefix_cols=[cname]))
        lines.append("")

    # Frigate section
    frig_cams = summary.get("frigate", {}).get("cameras", {})
    if frig_cams:
        lines.extend([
            "## 4. Frigate Pipeline Rates",
            "",
            "| Camera | Pipeline Stage | Definition | Samples | Mean | Median | Min | Max | StDev | p50 | p95 |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for cam_name, metrics in frig_cams.items():
            stages = [
                ("camera_fps", "Ingest / Consumed", metrics.get("camera_fps", {})),
                ("process_fps", "Decode / Processed", metrics.get("process_fps", {})),
                ("skipped_fps", "Frame Drops", metrics.get("skipped_fps", {})),
                ("detection_fps", "Detector Invocations", metrics.get("detection_fps", {})),
            ]
            for metric_key, defn, stat in stages:
                row_str = _format_stat_row(metric_key, stat)
                # Split and insert camera name and definition
                parts = [p.strip() for p in row_str.split("|")[1:-1]]
                formatted = f"| `{cam_name}` | `{parts[0]}` | {defn} | " + " | ".join(parts[1:]) + " |"
                lines.append(formatted)
        lines.append("")
    else:
        lines.extend([
            "## 4. Frigate Pipeline Rates",
            "",
            "*No telemetry captured from Frigate REST API during this run.*",
            "",
        ])

    lines.extend([
        "## 5. Methodology & Interpretation Boundary",
        "",
        "- **Descriptive Boundaries**: Reported statistics represent empirical observations from this specific test run only. No broad generalization or statistical significance is inferred without repeated trials across identical controlled conditions.",
        "- **Metric Separation**: Note that `camera_fps` reflects frames consumed from the camera stream, `process_fps` measures decoder throughput, `skipped_fps` captures skipped frames, and `detection_fps` isolates detector execution rate.",
        "- **Hardware Coupling**: Results are strictly coupled to the host hardware, GPU/NPU accelerators, driver versions, and network topology recorded above.",
        "",
    ])

    return "\n".join(lines)


def _format_stat_row(name: str, stats: dict[str, Any], prefix_cols: list[str] | None = None) -> str:
    count = stats.get("sample_count", 0)
    mean = stats.get("mean", "null")
    med = stats.get("median", "null")
    min_v = stats.get("min", "null")
    max_v = stats.get("max", "null")
    stdev = stats.get("stdev", "null")
    p50 = stats.get("p50", "null")
    p95 = stats.get("p95", "null")

    prefix = " | ".join(prefix_cols) + " | " if prefix_cols else ""
    return f"| {prefix}{name} | {count} | {mean} | {med} | {min_v} | {max_v} | {stdev} | {p50} | {p95} |"


def _format_bytes(size: int | float | None) -> str:
    if size is None:
        return "N/A"
    try:
        gb = float(size) / (1024 ** 3)
        return f"{gb:.2f} GB"
    except Exception:
        return "N/A"

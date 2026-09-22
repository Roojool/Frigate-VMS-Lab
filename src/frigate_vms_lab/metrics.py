"""Defensible descriptive statistics and sample aggregation for VMS experiments."""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from typing import Any


def calculate_descriptive_stats(
    values: Sequence[float | int | None] | None,
) -> dict[str, float | int | None]:
    """Calculate strictly defensible descriptive statistics for a numeric sequence.

    Filters out None/null values. If fewer than 1 valid value exists, returns
    sample_count=0 and None for summary fields. No statistical significance or
    confidence intervals are claimed without an explicit test design.
    """
    if values is None:
        return _empty_stats()

    clean: list[float] = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    count = len(clean)

    if count == 0:
        return _empty_stats()

    clean_sorted = sorted(clean)

    min_val = clean_sorted[0]
    max_val = clean_sorted[-1]
    mean_val = round(statistics.mean(clean), 3)
    median_val = round(statistics.median(clean), 3)

    if count >= 2:
        stdev_val = round(statistics.stdev(clean), 3)
    else:
        stdev_val = 0.0

    p50_val = round(_percentile(clean_sorted, 50.0), 3)
    p95_val = round(_percentile(clean_sorted, 95.0), 3)

    return {
        "sample_count": count,
        "mean": mean_val,
        "median": median_val,
        "min": min_val,
        "max": max_val,
        "stdev": stdev_val,
        "p50": p50_val,
        "p95": p95_val,
    }


def _percentile(sorted_data: list[float], percent: float) -> float:
    """Calculate percentile using standard linear interpolation."""
    if not sorted_data:
        raise ValueError("Cannot calculate percentile on empty list")
    if len(sorted_data) == 1:
        return sorted_data[0]

    k = (len(sorted_data) - 1) * (percent / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1


def _empty_stats() -> dict[str, float | int | None]:
    return {
        "sample_count": 0,
        "mean": None,
        "median": None,
        "min": None,
        "max": None,
        "stdev": None,
        "p50": None,
        "p95": None,
    }


def summarize_samples(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate a time series of collected samples into descriptive summary tables."""
    if not samples:
        return {
            "total_samples": 0,
            "system": {},
            "docker": {},
            "frigate": {},
        }

    # Extract System Metrics
    sys_cpu = [s.get("system", {}).get("cpu_percent") for s in samples]
    sys_mem = [s.get("system", {}).get("memory", {}).get("percent") for s in samples]

    summary: dict[str, Any] = {
        "total_samples": len(samples),
        "system": {
            "cpu_percent": calculate_descriptive_stats(sys_cpu),
            "memory_percent": calculate_descriptive_stats(sys_mem),
        },
        "docker": {},
        "frigate": {
            "cameras": {},
        },
    }

    # Docker Containers
    container_cpus: dict[str, list[float | None]] = {}
    container_mems: dict[str, list[float | None]] = {}

    for s in samples:
        docker_info = s.get("docker", {})
        if docker_info.get("available") and "containers" in docker_info:
            for c in docker_info["containers"]:
                cname = c.get("name", "unknown")
                container_cpus.setdefault(cname, []).append(c.get("cpu_percent"))
                container_mems.setdefault(cname, []).append(c.get("memory_percent"))

    for cname in container_cpus:
        summary["docker"][cname] = {
            "cpu_percent": calculate_descriptive_stats(container_cpus[cname]),
            "memory_percent": calculate_descriptive_stats(container_mems[cname]),
        }

    # Frigate Pipeline Metrics
    # Specifically distinguishing: camera_fps, process_fps, skipped_fps, detection_fps
    cam_metrics: dict[str, dict[str, list[float | None]]] = {}

    for s in samples:
        frig = s.get("frigate", {})
        if frig.get("available") and "cameras" in frig:
            for cam_name, cam_data in frig["cameras"].items():
                if cam_name not in cam_metrics:
                    cam_metrics[cam_name] = {
                        "camera_fps": [],
                        "process_fps": [],
                        "skipped_fps": [],
                        "detection_fps": [],
                    }
                cam_metrics[cam_name]["camera_fps"].append(cam_data.get("camera_fps"))
                cam_metrics[cam_name]["process_fps"].append(cam_data.get("process_fps"))
                cam_metrics[cam_name]["skipped_fps"].append(cam_data.get("skipped_fps"))
                cam_metrics[cam_name]["detection_fps"].append(cam_data.get("detection_fps"))

    for cam_name, metrics_dict in cam_metrics.items():
        summary["frigate"]["cameras"][cam_name] = {
            "camera_fps": calculate_descriptive_stats(metrics_dict["camera_fps"]),
            "process_fps": calculate_descriptive_stats(metrics_dict["process_fps"]),
            "skipped_fps": calculate_descriptive_stats(metrics_dict["skipped_fps"]),
            "detection_fps": calculate_descriptive_stats(metrics_dict["detection_fps"]),
        }

    return summary

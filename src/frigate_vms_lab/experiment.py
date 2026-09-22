"""Experiment execution engine and telemetry coordinator."""

from __future__ import annotations

import csv
import json
import platform
import time
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil

from frigate_vms_lab.collectors import (
    DockerCollector,
    FrigateCollector,
    RtspProbeCollector,
    SystemCollector,
)
from frigate_vms_lab.metrics import summarize_samples


class ExperimentRunner:
    """Coordinates benchmark experiments, warm-up phases, and sample aggregation."""

    def __init__(
        self,
        experiment_id: str = "EXP-001",
        duration_seconds: int = 60,
        interval_seconds: float = 1.0,
        warmup_seconds: int = 0,
        frigate_url: str | None = None,
        rtsp_urls: Sequence[str] | None = None,
        target_container: str | None = None,
        notes: str | None = None,
    ):
        self.experiment_id = experiment_id
        self.duration_seconds = max(1, int(duration_seconds))
        self.interval_seconds = max(0.1, float(interval_seconds))
        self.warmup_seconds = max(0, int(warmup_seconds))
        self.frigate_url = frigate_url
        self.rtsp_urls = list(rtsp_urls) if rtsp_urls else []
        self.target_container = target_container
        self.notes = notes

        self.sys_collector = SystemCollector()
        self.docker_collector = DockerCollector(target_container=self.target_container)
        self.frigate_collector = FrigateCollector(base_url=self.frigate_url) if self.frigate_url else None
        self.probe_collector = RtspProbeCollector()

    def get_environment_info(self) -> dict[str, Any]:
        """Inspect host runtime environment metadata."""
        frigate_ver = self.frigate_collector.get_version() if self.frigate_collector else None
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "memory_total_bytes": psutil.virtual_memory().total,
            "docker_available": self.docker_collector.is_available(),
            "frigate_version": frigate_ver,
            "notes": self.notes,
        }

    def run(self) -> dict[str, Any]:
        """Execute the configured experimental run."""
        env_info = self.get_environment_info()

        # Probe RTSP streams if requested
        probed_streams = []
        for url in self.rtsp_urls:
            probe_res = self.probe_collector.probe(url)
            probed_streams.append(probe_res)

        start_utc = datetime.now(timezone.utc).isoformat()

        # Warm-up phase (stabilizes ffmpeg decoders and caches before logging)
        if self.warmup_seconds > 0:
            time.sleep(self.warmup_seconds)

        samples: list[dict[str, Any]] = []
        end_time = time.monotonic() + self.duration_seconds

        while time.monotonic() < end_time:
            sample_start = time.monotonic()

            sample_data: dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system": self.sys_collector.collect(),
                "docker": self.docker_collector.collect(),
                "frigate": (
                    self.frigate_collector.collect()
                    if self.frigate_collector
                    else {"available": False, "note": "No Frigate URL provided"}
                ),
            }
            samples.append(sample_data)

            elapsed = time.monotonic() - sample_start
            sleep_time = max(0.0, self.interval_seconds - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

        summary = summarize_samples(samples)

        return {
            "experiment_id": self.experiment_id,
            "timestamp": start_utc,
            "duration_seconds": self.duration_seconds,
            "interval_seconds": self.interval_seconds,
            "warmup_seconds": self.warmup_seconds,
            "environment": env_info,
            "streams": probed_streams,
            "samples": samples,
            "summary": summary,
        }

    @staticmethod
    def export_json(data: dict[str, Any], filepath: str | Path) -> None:
        """Export experiment run payload to formatted JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def export_csv(data: dict[str, Any], filepath: str | Path) -> None:
        """Export sample timeseries to CSV for external tabular analysis."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        samples = data.get("samples", [])
        if not samples:
            return

        # Determine all camera names present in frigate samples
        cam_names = set()
        for s in samples:
            frig = s.get("frigate", {})
            if frig.get("available") and "cameras" in frig:
                cam_names.update(frig["cameras"].keys())

        headers = ["timestamp", "system_cpu_percent", "system_memory_percent"]
        for c in sorted(cam_names):
            headers.extend([
                f"{c}_camera_fps",
                f"{c}_process_fps",
                f"{c}_skipped_fps",
                f"{c}_detection_fps",
            ])

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for s in samples:
                ts = s.get("timestamp", "")
                sys_cpu = s.get("system", {}).get("cpu_percent")
                sys_mem = s.get("system", {}).get("memory", {}).get("percent")
                row = [ts, sys_cpu, sys_mem]

                frig_cams = s.get("frigate", {}).get("cameras", {})
                for c in sorted(cam_names):
                    cdata = frig_cams.get(c, {})
                    row.extend([
                        cdata.get("camera_fps"),
                        cdata.get("process_fps"),
                        cdata.get("skipped_fps"),
                        cdata.get("detection_fps"),
                    ])
                writer.writerow(row)

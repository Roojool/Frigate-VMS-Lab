"""Instrumentation collectors for System, Docker, Frigate, and RTSP streams."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

import psutil


def sanitize_url(url: str) -> str:
    """Redact embedded credentials from URLs to preserve privacy."""
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", url)


class SystemCollector:
    """Collects host operating system resource utilization metrics."""

    def __init__(self, per_cpu: bool = False):
        self.per_cpu = per_cpu
        # Prime psutil's internal counter
        psutil.cpu_percent(interval=None)

    def collect(self) -> dict[str, Any]:
        """Sample current CPU, memory, load average, and timestamp."""
        now = datetime.now(timezone.utc).isoformat()
        cpu_total = psutil.cpu_percent(interval=None)
        cpu_cores = psutil.cpu_percent(interval=None, percpu=True) if self.per_cpu else None

        mem = psutil.virtual_memory()
        memory_data = {
            "total_bytes": mem.total,
            "available_bytes": mem.available,
            "used_bytes": mem.used,
            "percent": mem.percent,
        }

        # System load average (supported on Linux / macOS; None on Windows)
        load_avg = list(os.getloadavg()) if hasattr(os, "getloadavg") else None

        return {
            "timestamp": now,
            "cpu_percent": cpu_total,
            "cpu_cores_percent": cpu_cores,
            "memory": memory_data,
            "load_average": load_avg,
        }


class DockerCollector:
    """Collects container-level resource statistics if Docker daemon is accessible."""

    def __init__(self, target_container: str | None = None):
        self.target_container = target_container
        self.docker_path = shutil.which("docker")

    def is_available(self) -> bool:
        """Check if Docker CLI is found and daemon responds."""
        if not self.docker_path:
            return False
        try:
            res = subprocess.run(
                [self.docker_path, "info"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    def collect(self) -> dict[str, Any]:
        """Sample Docker container stats or return graceful unavailable payload."""
        if not self.is_available():
            return {
                "available": False,
                "containers": [],
                "note": "Docker daemon or CLI unavailable.",
            }

        cmd = [self.docker_path, "stats", "--no-stream", "--format", "{{json .}}"]
        if self.target_container:
            cmd.append(self.target_container)

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                return {
                    "available": False,
                    "containers": [],
                    "note": f"docker stats error: {res.stderr.strip()}",
                }

            containers = []
            for line in res.stdout.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    cdata = json.loads(line)
                    containers.append({
                        "name": cdata.get("Name") or cdata.get("Container"),
                        "id": cdata.get("ID"),
                        "cpu_percent": self._parse_percentage(cdata.get("CPUPerc")),
                        "memory_usage": cdata.get("MemUsage"),
                        "memory_percent": self._parse_percentage(cdata.get("MemPerc")),
                        "net_io": cdata.get("NetIO"),
                        "block_io": cdata.get("BlockIO"),
                        "pids": cdata.get("PIDs"),
                    })
                except json.JSONDecodeError:
                    continue

            return {
                "available": True,
                "containers": containers,
            }
        except Exception as e:
            return {
                "available": False,
                "containers": [],
                "note": f"Exception querying docker: {e}",
            }

    @staticmethod
    def _parse_percentage(val: Any) -> float | None:
        if val is None:
            return None
        clean = str(val).replace("%", "").strip()
        try:
            return float(clean)
        except ValueError:
            return None


class FrigateCollector:
    """Collects defensive telemetry from a local or networked Frigate instance."""

    def __init__(self, base_url: str = "http://localhost:5000", timeout: float = 2.5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_version(self) -> str | None:
        """Query /api/version to determine the upstream Frigate version."""
        url = f"{self.base_url}/api/version"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Frigate-VMS-Lab/0.1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read().decode("utf-8").strip()
                # May return plaintext string or JSON
                if data.startswith("{"):
                    parsed = json.loads(data)
                    return parsed.get("version") or str(parsed)
                return data.strip('"')
        except Exception:
            return None

    def collect(self) -> dict[str, Any]:
        """Fetch and defensively parse /api/stats.

        Returns null for missing fields rather than substituting zero.
        """
        stats_url = f"{self.base_url}/api/stats"
        try:
            req = urllib.request.Request(stats_url, headers={"User-Agent": "Frigate-VMS-Lab/0.1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))

            frigate_version = self.get_version() or raw.get("service", {}).get("version")

            # Parse cameras defensively
            cameras_summary: dict[str, dict[str, float | None]] = {}
            raw_cameras = raw.get("cameras", {})
            if isinstance(raw_cameras, dict):
                for cam_name, cam_stats in raw_cameras.items():
                    if isinstance(cam_stats, dict):
                        cameras_summary[cam_name] = {
                            "camera_fps": self._to_float(cam_stats.get("camera_fps")),
                            "process_fps": self._to_float(cam_stats.get("process_fps")),
                            "skipped_fps": self._to_float(cam_stats.get("skipped_fps")),
                            "detection_fps": self._to_float(cam_stats.get("detection_fps")),
                        }

            # Parse detectors
            detectors_summary: dict[str, Any] = {}
            raw_detectors = raw.get("detectors", {})
            if isinstance(raw_detectors, dict):
                for det_name, det_stats in raw_detectors.items():
                    if isinstance(det_stats, dict):
                        detectors_summary[det_name] = {
                            "inference_speed": self._to_float(det_stats.get("inference_speed")),
                            "detection_start": det_stats.get("detection_start"),
                            "pid": det_stats.get("pid"),
                        }

            return {
                "available": True,
                "frigate_version": frigate_version,
                "uptime": raw.get("service", {}).get("uptime"),
                "cameras": cameras_summary,
                "detectors": detectors_summary,
            }
        except Exception as e:
            return {
                "available": False,
                "frigate_version": None,
                "cameras": {},
                "detectors": {},
                "note": f"Frigate endpoint unreachable: {e}",
            }

    @staticmethod
    def _to_float(val: Any) -> float | None:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None


class RtspProbeCollector:
    """Optional stream inspection utility using ffprobe."""

    def __init__(self):
        self.ffprobe_path = shutil.which("ffprobe")

    def is_available(self) -> bool:
        return self.ffprobe_path is not None

    def probe(self, rtsp_url: str, timeout: float = 8.0) -> dict[str, Any]:
        """Probe an RTSP stream using ffprobe to gather codec and frame geometry."""
        sanitized = sanitize_url(rtsp_url)
        if not self.is_available():
            return {
                "available": False,
                "url": sanitized,
                "note": "ffprobe executable not found in PATH.",
            }

        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-analyzeduration", "5000000",
            "-probesize", "5000000",
            rtsp_url,
        ]

        start_time = datetime.now(timezone.utc)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            probe_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            if res.returncode != 0:
                return {
                    "available": False,
                    "url": sanitized,
                    "probe_duration_seconds": probe_duration,
                    "note": f"ffprobe failed: {res.stderr.strip()}",
                }

            data = json.loads(res.stdout)
            streams = data.get("streams", [])
            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)

            if not video_stream:
                return {
                    "available": True,
                    "url": sanitized,
                    "video_stream_found": False,
                    "probe_duration_seconds": probe_duration,
                }

            nominal_fps = self._parse_framerate(video_stream.get("avg_frame_rate")) or \
                          self._parse_framerate(video_stream.get("r_frame_rate"))

            bitrate = None
            if "bit_rate" in video_stream:
                try:
                    bitrate = int(video_stream["bit_rate"])
                except (ValueError, TypeError):
                    bitrate = None

            return {
                "available": True,
                "url": sanitized,
                "video_stream_found": True,
                "codec": video_stream.get("codec_name"),
                "profile": video_stream.get("profile"),
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "nominal_fps": nominal_fps,
                "bitrate_bps": bitrate,
                "probe_duration_seconds": probe_duration,
            }
        except Exception as e:
            return {
                "available": False,
                "url": sanitized,
                "note": f"Probe error: {e}",
            }

    @staticmethod
    def _parse_framerate(rate_str: Any) -> float | None:
        if not rate_str or not isinstance(rate_str, str):
            return None
        if "/" in rate_str:
            num, den = rate_str.split("/", 1)
            try:
                n, d = float(num), float(den)
                if d == 0:
                    return None
                return round(n / d, 2)
            except ValueError:
                return None
        try:
            return float(rate_str)
        except ValueError:
            return None

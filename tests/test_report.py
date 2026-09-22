"""Unit tests for experiment report generation."""

from __future__ import annotations

from frigate_vms_lab.report import generate_markdown_report


def test_generate_markdown_report_structure():
    data = {
        "experiment_id": "EXP-001",
        "timestamp": "2026-09-23T04:00:00Z",
        "duration_seconds": 60,
        "warmup_seconds": 10,
        "environment": {
            "platform": "Linux-6.8.0-generic-x86_64",
            "machine": "x86_64",
            "python_version": "3.10.11",
            "memory_total_bytes": 17179869184,
            "docker_available": True,
            "frigate_version": "0.18.0",
        },
        "streams": [
            {
                "url": "rtsp://CAMERA_USERNAME:***@CAMERA_1_HOST/stream",
                "video_stream_found": True,
                "codec": "h264",
                "width": 1280,
                "height": 720,
                "nominal_fps": 15.0,
                "bitrate_bps": 2048000,
            }
        ],
        "summary": {
            "total_samples": 60,
            "system": {
                "cpu_percent": {
                    "sample_count": 60,
                    "mean": 14.5,
                    "median": 14.0,
                    "min": 10.0,
                    "max": 20.0,
                    "stdev": 2.1,
                    "p50": 14.0,
                    "p95": 18.2,
                },
                "memory_percent": {
                    "sample_count": 60,
                    "mean": 35.0,
                    "median": 35.0,
                    "min": 34.8,
                    "max": 35.2,
                    "stdev": 0.1,
                    "p50": 35.0,
                    "p95": 35.1,
                },
            },
            "docker": {
                "frigate": {
                    "cpu_percent": {"sample_count": 60, "mean": 12.0, "p95": 15.0},
                    "memory_percent": {"sample_count": 60, "mean": 6.5, "p95": 6.6},
                }
            },
            "frigate": {
                "cameras": {
                    "cam_front": {
                        "camera_fps": {"sample_count": 60, "mean": 15.0, "median": 15.0, "p95": 15.0},
                        "process_fps": {"sample_count": 60, "mean": 5.0, "median": 5.0, "p95": 5.0},
                        "skipped_fps": {"sample_count": 60, "mean": 0.0, "median": 0.0, "p95": 0.0},
                        "detection_fps": {"sample_count": 60, "mean": 4.8, "median": 4.8, "p95": 5.0},
                    }
                }
            },
        },
    }

    report = generate_markdown_report(data)

    assert "# Experiment Report: EXP-001" in report
    assert "Frigate Version**: `0.18.0`" in report
    assert "rtsp://CAMERA_USERNAME:***@CAMERA_1_HOST/stream" in report
    assert "System CPU (%)" in report
    assert "camera_fps" in report
    assert "process_fps" in report
    assert "skipped_fps" in report
    assert "detection_fps" in report
    assert "cam_front" in report
    assert "Methodology & Interpretation Boundary" in report

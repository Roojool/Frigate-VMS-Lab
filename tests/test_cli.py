"""Integration tests for the frigate-vms-lab CLI subcommands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from frigate_vms_lab.cli import build_parser, cmd_analyze, cmd_report, cmd_validate_config


def test_cli_validate_config_success(tmp_path: Path):
    clean_cfg = tmp_path / "valid_frigate.yml"
    clean_cfg.write_text(
        "go2rtc:\n  streams:\n    cam: rtsp://CAMERA_USERNAME:{FRIGATE_RTSP_PASSWORD}@CAMERA_1_HOST/path\n",
        encoding="utf-8",
    )

    parser = build_parser()
    args = parser.parse_args(["validate-config", str(clean_cfg)])
    assert cmd_validate_config(args) == 0


def test_cli_validate_config_failure(tmp_path: Path):
    bad_cfg = tmp_path / "leaky_config.yml"
    bad_cfg.write_text(
        "go2rtc:\n  streams:\n    cam: rtsp://admin:pass123@192.168.1.50/live\n",
        encoding="utf-8",
    )

    parser = build_parser()
    args = parser.parse_args(["validate-config", str(bad_cfg)])
    assert cmd_validate_config(args) == 1


def test_cli_analyze_and_report(tmp_path: Path, capsys: pytest.CaptureFixture):
    run_file = tmp_path / "run.json"
    data = {
        "experiment_id": "EXP-CLI-TEST",
        "timestamp": "2026-09-23T05:00:00Z",
        "duration_seconds": 10,
        "environment": {"platform": "TestOS", "python_version": "3.10.11"},
        "streams": [],
        "samples": [
            {
                "timestamp": "2026-09-23T05:00:01Z",
                "system": {"cpu_percent": 15.0, "memory": {"percent": 40.0}},
                "docker": {"available": False},
                "frigate": {
                    "available": True,
                    "cameras": {
                        "cam1": {
                            "camera_fps": 15.0,
                            "process_fps": 5.0,
                            "skipped_fps": 0.0,
                            "detection_fps": 4.5,
                        }
                    },
                },
            }
        ],
        "summary": {
            "system": {
                "cpu_percent": {"sample_count": 1, "mean": 15.0, "median": 15.0, "p95": 15.0},
                "memory_percent": {"sample_count": 1, "mean": 40.0, "median": 40.0, "p95": 40.0},
            },
            "frigate": {
                "cameras": {
                    "cam1": {
                        "camera_fps": {"sample_count": 1, "mean": 15.0, "median": 15.0, "p95": 15.0},
                        "process_fps": {"sample_count": 1, "mean": 5.0, "median": 5.0, "p95": 5.0},
                        "skipped_fps": {"sample_count": 1, "mean": 0.0, "median": 0.0, "p95": 0.0},
                        "detection_fps": {"sample_count": 1, "mean": 4.5, "median": 4.5, "p95": 4.5},
                    }
                }
            },
        },
    }
    run_file.write_text(json.dumps(data), encoding="utf-8")

    parser = build_parser()

    # Test analyze
    args_analyze = parser.parse_args(["analyze", str(run_file)])
    assert cmd_analyze(args_analyze) == 0
    captured = capsys.readouterr()
    assert "EXP-CLI-TEST" in captured.out
    assert "camera_fps" in captured.out

    # Test report
    out_md = tmp_path / "report.md"
    args_report = parser.parse_args(["report", str(run_file), "--output", str(out_md)])
    assert cmd_report(args_report) == 0
    assert out_md.is_file()
    md_text = out_md.read_text(encoding="utf-8")
    assert "# Experiment Report: EXP-CLI-TEST" in md_text

"""Unit tests for defensible descriptive statistics and sample aggregation."""

from __future__ import annotations

from frigate_vms_lab.metrics import calculate_descriptive_stats, summarize_samples


def test_empty_and_none_input():
    res_none = calculate_descriptive_stats(None)
    assert res_none["sample_count"] == 0
    assert res_none["mean"] is None
    assert res_none["median"] is None
    assert res_none["stdev"] is None

    res_empty = calculate_descriptive_stats([])
    assert res_empty["sample_count"] == 0
    assert res_empty["mean"] is None


def test_single_value():
    res = calculate_descriptive_stats([42.5])
    assert res["sample_count"] == 1
    assert res["mean"] == 42.5
    assert res["median"] == 42.5
    assert res["min"] == 42.5
    assert res["max"] == 42.5
    assert res["stdev"] == 0.0
    assert res["p50"] == 42.5
    assert res["p95"] == 42.5


def test_mixed_none_and_known_sequence():
    data = [10.0, None, 20.0, float("nan"), 30.0, None, 40.0, 50.0]
    res = calculate_descriptive_stats(data)

    assert res["sample_count"] == 5
    assert res["min"] == 10.0
    assert res["max"] == 50.0
    assert res["mean"] == 30.0
    assert res["median"] == 30.0
    # Sample stdev of [10, 20, 30, 40, 50] with N-1=4 is sqrt(1000/4) = sqrt(250) ≈ 15.811
    assert res["stdev"] == 15.811
    assert res["p50"] == 30.0
    # p95 on 5 points (index (5-1)*0.95 = 3.8) -> 40 + 0.8 * 10 = 48.0
    assert res["p95"] == 48.0


def test_summarize_samples_comprehensive():
    sample1 = {
        "timestamp": "2026-09-23T00:00:01Z",
        "system": {
            "cpu_percent": 10.0,
            "memory": {"percent": 40.0},
        },
        "docker": {
            "available": True,
            "containers": [
                {"name": "frigate", "cpu_percent": 8.0, "memory_percent": 12.0}
            ],
        },
        "frigate": {
            "available": True,
            "cameras": {
                "cam_front": {
                    "camera_fps": 15.0,
                    "process_fps": 5.0,
                    "skipped_fps": 0.0,
                    "detection_fps": 4.5,
                }
            },
        },
    }

    sample2 = {
        "timestamp": "2026-09-23T00:00:02Z",
        "system": {
            "cpu_percent": 20.0,
            "memory": {"percent": 42.0},
        },
        "docker": {
            "available": True,
            "containers": [
                {"name": "frigate", "cpu_percent": 14.0, "memory_percent": 12.5}
            ],
        },
        "frigate": {
            "available": True,
            "cameras": {
                "cam_front": {
                    "camera_fps": 15.0,
                    "process_fps": 5.0,
                    "skipped_fps": 0.0,
                    "detection_fps": 5.0,
                }
            },
        },
    }

    summary = summarize_samples([sample1, sample2])

    assert summary["total_samples"] == 2
    assert summary["system"]["cpu_percent"]["mean"] == 15.0
    assert summary["system"]["memory_percent"]["mean"] == 41.0

    # Docker verification
    docker_cams = summary["docker"]["frigate"]
    assert docker_cams["cpu_percent"]["mean"] == 11.0

    # Frigate metrics verification (strictly separating fps types)
    cam_summary = summary["frigate"]["cameras"]["cam_front"]
    assert cam_summary["camera_fps"]["mean"] == 15.0
    assert cam_summary["process_fps"]["mean"] == 5.0
    assert cam_summary["skipped_fps"]["mean"] == 0.0
    assert cam_summary["detection_fps"]["mean"] == 4.75

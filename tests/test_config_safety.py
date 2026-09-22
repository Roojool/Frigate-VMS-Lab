"""Automated privacy and security tests enforcing zero-leakage of IPs and credentials."""

from __future__ import annotations

from pathlib import Path

import pytest

from frigate_vms_lab.cli import validate_config_content


def get_repo_root() -> Path:
    # tests/ is located under repository root
    return Path(__file__).resolve().parent.parent


def test_repository_example_configs_are_clean():
    """Verify that all configuration templates in configs/ and docker/ are safe."""
    root = get_repo_root()
    target_dirs = [root / "configs", root / "docker"]

    files_checked = 0
    for d in target_dirs:
        if not d.is_dir():
            continue
        for ext in ["*.yml", "*.yaml", "*.json"]:
            for config_file in d.glob(ext):
                files_checked += 1
                content = config_file.read_text(encoding="utf-8")
                errors = validate_config_content(content, filename=config_file.name)
                assert not errors, (
                    f"Config safety violation in {config_file.relative_to(root)}:\n"
                    + "\n".join(errors)
                )

    # Ensure we actually inspected example files
    assert files_checked >= 3, f"Expected at least 3 configs checked, found {files_checked}"


def test_committed_results_are_clean():
    """Verify that any committed JSON result artifacts in results/ do not leak private IPs or passwords."""
    root = get_repo_root()
    results_dir = root / "results"
    if results_dir.is_dir():
        for res_file in results_dir.glob("*.json"):
            content = res_file.read_text(encoding="utf-8")
            errors = validate_config_content(content, filename=res_file.name)
            assert not errors, f"Results privacy violation in {res_file.name}: {errors}"


@pytest.mark.parametrize(
    "bad_content,expected_keyword",
    [
        (
            "go2rtc:\n  streams:\n    cam: rtsp://user:pass@192.168.1.120/stream\n",
            "Private IP address",
        ),
        (
            "go2rtc:\n  streams:\n    cam: rtsp://user:pass@10.0.4.50/stream\n",
            "Private IP address",
        ),
        (
            "go2rtc:\n  streams:\n    cam: rtsp://user:pass@172.20.1.10/stream\n",
            "Private IP address",
        ),
        (
            "go2rtc:\n  streams:\n    cam: rtsp://admin:mysecretpassword@CAMERA_1_HOST/stream\n",
            "Hardcoded URL credentials",
        ),
        (
            "auth:\n  password: 'admin'\n",
            "Plaintext default/insecure password literal",
        ),
    ],
)
def test_validator_detects_deliberate_hazards(bad_content: str, expected_keyword: str):
    """Negative tests: verify that the validator actively catches hazards."""
    errors = validate_config_content(bad_content, filename="test_hazard.yml")
    assert len(errors) > 0
    assert any(expected_keyword in e for e in errors), f"Expected '{expected_keyword}' in {errors}"


def test_safe_placeholder_passes():
    """Verify that legitimate substitution tokens pass without false positives."""
    clean_sample = """
    go2rtc:
      streams:
        cam:
          - rtsp://CAMERA_USERNAME:{FRIGATE_RTSP_PASSWORD}@CAMERA_1_HOST/STREAM_PATH
    """
    errors = validate_config_content(clean_sample, filename="clean_sample.yml")
    assert errors == []

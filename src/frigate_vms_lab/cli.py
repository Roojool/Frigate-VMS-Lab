"""Command-line interface for the Frigate VMS Lab research suite."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from frigate_vms_lab.experiment import ExperimentRunner
from frigate_vms_lab.report import generate_markdown_report

# Regex patterns for detecting un-sanitized IP addresses and passwords
PRIVATE_IPV4_REGEX = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(?:1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3})\b"
)

# Detect URLs with explicit plaintext credentials (e.g. rtsp://user:pass@host)
# Excludes safe substitution placeholders like {FRIGATE_...} or ${...}
PLAINTEXT_URL_CRED_REGEX = re.compile(
    r"://(?![^@]*\{)[a-zA-Z0-9_\-\.]+:[^@\s\{\}\$]+@"
)

# Common insecure password literals in configs
PASSWORD_LITERAL_REGEX = re.compile(
    r'(?:password|secret)\s*:\s*["\']?(?:admin|password|123456|pass123|root)["\']?',
    re.IGNORECASE,
)


def validate_config_content(content: str, filename: str = "") -> list[str]:
    """Inspect configuration text for YAML validity and privacy/security hazards."""
    errors = []

    # 1. YAML syntax validity
    try:
        yaml.safe_load(content)
    except yaml.YAMLError as exc:
        errors.append(f"Invalid YAML syntax in {filename}: {exc}")
        return errors

    # 2. Check for private IPv4 addresses
    ip_matches = PRIVATE_IPV4_REGEX.findall(content)
    if ip_matches:
        unique_ips = sorted(set(ip_matches))
        errors.append(
            f"Private IP address(es) detected in {filename}: {unique_ips}. "
            f"Use symbolic placeholders (e.g., CAMERA_1_HOST) instead."
        )

    # 3. Check for plaintext embedded URL credentials
    cred_matches = PLAINTEXT_URL_CRED_REGEX.findall(content)
    if cred_matches:
        errors.append(
            f"Hardcoded URL credentials detected in {filename}. "
            f"Use Frigate substitution syntax {{FRIGATE_RTSP_PASSWORD}} or Compose ${{...}}."
        )

    # 4. Check for obvious password literals
    lit_matches = PASSWORD_LITERAL_REGEX.findall(content)
    if lit_matches:
        errors.append(
            f"Plaintext default/insecure password literal detected in {filename}: {lit_matches}"
        )

    return errors


def cmd_validate_config(args: argparse.Namespace) -> int:
    path = Path(args.config_file)
    if not path.is_file():
        print(f"Error: Configuration file not found: {path}", file=sys.stderr)
        return 1

    content = path.read_text(encoding="utf-8")
    errors = validate_config_content(content, filename=path.name)

    if errors:
        print(f"[FAIL] Configuration validation failed for {path.name}:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"[PASS] Configuration '{path.name}' is valid YAML and clean of hardcoded credentials/private IPs.")
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    print(f"Starting experiment '{args.experiment_id}'...")
    print(f"Duration: {args.duration}s | Interval: {args.interval}s | Warm-up: {args.warmup}s")
    if args.frigate_url:
        print(f"Frigate Endpoint: {args.frigate_url}")
    if args.container:
        print(f"Docker Target Container: {args.container}")

    runner = ExperimentRunner(
        experiment_id=args.experiment_id,
        duration_seconds=args.duration,
        interval_seconds=args.interval,
        warmup_seconds=args.warmup,
        frigate_url=args.frigate_url,
        rtsp_urls=args.rtsp_url,
        target_container=args.container,
        notes=args.notes,
    )

    data = runner.run()

    out_path = Path(args.output)
    runner.export_json(data, out_path)
    print(f"Wrote experiment JSON results to: {out_path}")

    if args.csv:
        csv_path = Path(args.csv)
        runner.export_csv(data, csv_path)
        print(f"Wrote sample CSV timeseries to: {csv_path}")

    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    path = Path(args.input_file)
    if not path.is_file():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    exp_id = data.get("experiment_id", "UNKNOWN")
    samples = data.get("samples", [])
    summary = data.get("summary", {})
    env = data.get("environment", {})

    print(f"=== Experiment Analysis: {exp_id} ===")
    print(f"Timestamp: {data.get('timestamp')}")
    print(f"Samples Recorded: {len(samples)} over {data.get('duration_seconds')}s")
    print(f"Platform: {env.get('platform')}")
    print(f"Frigate Version: {env.get('frigate_version') or 'N/A'}")
    print()

    sys_cpu = summary.get("system", {}).get("cpu_percent", {})
    sys_mem = summary.get("system", {}).get("memory_percent", {})
    print("System Statistics:")
    print(f"  CPU %: mean={sys_cpu.get('mean')}, median={sys_cpu.get('median')}, p95={sys_cpu.get('p95')}")
    print(f"  RAM %: mean={sys_mem.get('mean')}, median={sys_mem.get('median')}, p95={sys_mem.get('p95')}")
    print()

    docker_stats = summary.get("docker", {})
    if docker_stats:
        print("Docker Containers:")
        for cname, cstat in docker_stats.items():
            ccpu = cstat.get("cpu_percent", {})
            cmem = cstat.get("memory_percent", {})
            print(f"  [{cname}] CPU % mean={ccpu.get('mean')}, p95={ccpu.get('p95')} | RAM % mean={cmem.get('mean')}")
        print()

    frig_cams = summary.get("frigate", {}).get("cameras", {})
    if frig_cams:
        print("Frigate Pipeline FPS:")
        for cname, metrics in frig_cams.items():
            print(f"  [{cname}]")
            for mkey in ["camera_fps", "process_fps", "skipped_fps", "detection_fps"]:
                st = metrics.get(mkey, {})
                print(f"    - {mkey:14}: mean={st.get('mean')}, median={st.get('median')}, p95={st.get('p95')}")
        print()

    return 0


def cmd_report(args: argparse.Namespace) -> int:
    path = Path(args.input_file)
    if not path.is_file():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    md_content = generate_markdown_report(data)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_content, encoding="utf-8")
        print(f"Wrote markdown report to: {out_path}")
    else:
        print(md_content)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="frigate-vms-lab",
        description="Frigate VMS Lab: Research instrumentation, benchmarking, and analysis CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # collect
    p_collect = subparsers.add_parser("collect", help="Execute an empirical resource measurement run.")
    p_collect.add_argument("--duration", type=int, default=60, help="Measurement duration in seconds (default: 60).")
    p_collect.add_argument("--interval", type=float, default=1.0, help="Sampling interval in seconds (default: 1.0).")
    p_collect.add_argument("--warmup", type=int, default=0, help="Warm-up stabilization period in seconds (default: 0).")
    p_collect.add_argument("--experiment-id", default="EXP-001", help="Experiment identifier (e.g. EXP-001).")
    p_collect.add_argument("--frigate-url", default=None, help="Frigate REST API base URL (e.g. http://localhost:5000).")
    p_collect.add_argument("--rtsp-url", action="append", help="RTSP stream URL to probe (can be repeated).")
    p_collect.add_argument("--container", default=None, help="Target Docker container name (e.g. frigate).")
    p_collect.add_argument("--output", "-o", default="results/run.json", help="Path to write JSON results.")
    p_collect.add_argument("--csv", default=None, help="Optional path to write sample timeseries CSV.")
    p_collect.add_argument("--notes", default=None, help="Additional context annotations.")
    p_collect.set_defaults(func=cmd_collect)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Print summary statistics from an experiment JSON file.")
    p_analyze.add_argument("input_file", help="Path to experiment JSON file.")
    p_analyze.set_defaults(func=cmd_analyze)

    # report
    p_report = subparsers.add_parser("report", help="Generate a Markdown research report from experiment data.")
    p_report.add_argument("input_file", help="Path to experiment JSON file.")
    p_report.add_argument("--output", "-o", default=None, help="Output Markdown file path (prints to stdout if omitted).")
    p_report.set_defaults(func=cmd_report)

    # validate-config
    p_val = subparsers.add_parser("validate-config", help="Validate YAML syntax and verify privacy/credential safety.")
    p_val.add_argument("config_file", help="Path to YAML configuration file.")
    p_val.set_defaults(func=cmd_validate_config)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

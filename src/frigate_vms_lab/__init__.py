"""Frigate VMS Lab: Research instrumentation and benchmarking for Video Management Systems."""

from frigate_vms_lab.collectors import (
    DockerCollector,
    FrigateCollector,
    RtspProbeCollector,
    SystemCollector,
)
from frigate_vms_lab.experiment import ExperimentRunner
from frigate_vms_lab.metrics import calculate_descriptive_stats, summarize_samples
from frigate_vms_lab.report import generate_markdown_report

__version__ = "0.1.0"
__all__ = [
    "SystemCollector",
    "DockerCollector",
    "FrigateCollector",
    "RtspProbeCollector",
    "ExperimentRunner",
    "calculate_descriptive_stats",
    "summarize_samples",
    "generate_markdown_report",
]

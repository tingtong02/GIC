"""Phase 3 signal frontend exports."""

from gic.signal.comparison import build_comparison_report
from gic.signal.export import export_comparison_report, export_frontend_result
from gic.signal.methods import FRONTEND_REGISTRY, build_frontend
from gic.signal.preprocess import build_signal_sample_from_timeseries
from gic.signal.schema import (
    FrontendComparisonReport,
    FrontendConfig,
    FrontendResult,
    QuasiDCSeries,
    SignalFeatureSet,
    SignalQualityReport,
    SignalSample,
    signal_to_dict,
)
from gic.signal.validation import validate_frontend_result, validate_signal_sample

__all__ = [
    "FRONTEND_REGISTRY",
    "FrontendComparisonReport",
    "FrontendConfig",
    "FrontendResult",
    "QuasiDCSeries",
    "SignalFeatureSet",
    "SignalQualityReport",
    "SignalSample",
    "build_comparison_report",
    "build_frontend",
    "build_signal_sample_from_timeseries",
    "export_comparison_report",
    "export_frontend_result",
    "signal_to_dict",
    "validate_frontend_result",
    "validate_signal_sample",
]

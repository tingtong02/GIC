from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from gic.signal.postprocess import build_frontend_result
from gic.signal.schema import FrontendConfig, FrontendResult, SignalSample


@dataclass(slots=True)
class FrontendComputation:
    denoised_values: dict[str, list[float]]
    quasi_dc_values: dict[str, list[float]]
    status: str = "ok"
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseFrontend(ABC):
    method_name = "base"
    method_version = "0.1"

    def run(self, signal_sample: SignalSample, config: FrontendConfig) -> FrontendResult:
        start = perf_counter()
        computation = self._run(signal_sample, config)
        runtime_ms = (perf_counter() - start) * 1000.0
        return build_frontend_result(
            signal_sample=signal_sample,
            frontend_config=config,
            denoised_values=computation.denoised_values,
            quasi_dc_values=computation.quasi_dc_values,
            runtime_ms=runtime_ms,
            status=computation.status,
            notes=computation.notes,
            metadata=computation.metadata,
        )

    @abstractmethod
    def _run(self, signal_sample: SignalSample, config: FrontendConfig) -> FrontendComputation:
        raise NotImplementedError

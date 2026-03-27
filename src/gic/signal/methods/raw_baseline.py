from __future__ import annotations

from gic.signal.base import BaseFrontend, FrontendComputation
from gic.signal.schema import FrontendConfig, SignalSample


class RawBaselineFrontend(BaseFrontend):
    method_name = "raw_baseline"
    method_version = "1.0"

    def _run(self, signal_sample: SignalSample, config: FrontendConfig) -> FrontendComputation:
        values = {channel: [float(item) for item in signal_sample.values[channel]] for channel in signal_sample.channels}
        return FrontendComputation(
            denoised_values=values,
            quasi_dc_values={channel: list(items) for channel, items in values.items()},
            status="ok",
            notes="No frontend processing applied.",
            metadata={"baseline": "identity"},
        )

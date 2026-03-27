from __future__ import annotations

from gic.signal.base import BaseFrontend, FrontendComputation
from gic.signal.preprocess import matrix_to_channel_values, prepare_matrix
from gic.signal.schema import FrontendConfig, SignalSample


class RawBaselineFrontend(BaseFrontend):
    method_name = "raw_baseline"
    method_version = "1.1"

    def _run(self, signal_sample: SignalSample, config: FrontendConfig) -> FrontendComputation:
        matrix = prepare_matrix(signal_sample, config.parameters)
        values = matrix_to_channel_values(matrix, signal_sample.channels)
        return FrontendComputation(
            denoised_values=values,
            quasi_dc_values={channel: list(items) for channel, items in values.items()},
            status="ok",
            notes="No frontend processing applied after configured missing-value handling.",
            metadata={"baseline": "identity"},
        )

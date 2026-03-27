from __future__ import annotations

from gic.signal.base import BaseFrontend, FrontendComputation
from gic.signal.preprocess import matrix_to_channel_values, moving_average, prepare_matrix
from gic.signal.schema import FrontendConfig, SignalSample


class LowFrequencyFrontend(BaseFrontend):
    method_name = "lowfreq_baseline"
    method_version = "1.0"

    def _run(self, signal_sample: SignalSample, config: FrontendConfig) -> FrontendComputation:
        matrix = prepare_matrix(signal_sample, config.parameters)
        window = int(config.parameters.get("smoothing_window", 3))
        quasi_dc = moving_average(matrix, window)
        return FrontendComputation(
            denoised_values=matrix_to_channel_values(quasi_dc, signal_sample.channels),
            quasi_dc_values=matrix_to_channel_values(quasi_dc, signal_sample.channels),
            status="ok",
            notes="Moving-average low-frequency baseline.",
            metadata={"smoothing_window": window},
        )

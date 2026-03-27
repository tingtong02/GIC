from __future__ import annotations

from gic.signal.base import BaseFrontend, FrontendComputation
from gic.signal.preprocess import (
    matrix_to_channel_values,
    moving_average,
    prepare_matrix,
    soft_threshold,
)
from gic.signal.schema import FrontendConfig, SignalSample


class SparseFrontend(BaseFrontend):
    method_name = "sparse_denoise"
    method_version = "1.0"

    def _run(self, signal_sample: SignalSample, config: FrontendConfig) -> FrontendComputation:
        matrix = prepare_matrix(signal_sample, config.parameters)
        trend_window = int(config.parameters.get("trend_window", 3))
        refine_window = int(config.parameters.get("refine_window", trend_window))
        sparsity_lambda = float(config.parameters.get("sparsity_lambda", 1.0))
        trend = moving_average(matrix, trend_window)
        residual = matrix - trend
        sparse_noise = soft_threshold(residual, sparsity_lambda)
        denoised = matrix - sparse_noise
        quasi_dc = moving_average(denoised, refine_window)
        retained_energy = float((sparse_noise ** 2).sum() / ((residual ** 2).sum() + 1e-9))
        return FrontendComputation(
            denoised_values=matrix_to_channel_values(denoised, signal_sample.channels),
            quasi_dc_values=matrix_to_channel_values(quasi_dc, signal_sample.channels),
            status="ok",
            notes="Sparse residual shrinkage baseline.",
            metadata={
                "trend_window": trend_window,
                "refine_window": refine_window,
                "sparsity_lambda": sparsity_lambda,
                "retained_sparse_energy_ratio": retained_energy,
            },
        )

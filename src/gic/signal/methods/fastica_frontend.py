from __future__ import annotations

import numpy as np

from gic.signal.base import BaseFrontend, FrontendComputation
from gic.signal.preprocess import matrix_to_channel_values, moving_average, prepare_matrix
from gic.signal.schema import FrontendConfig, SignalSample


def _sym_decorrelation(matrix: np.ndarray) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(matrix @ matrix.T)
    clipped = np.clip(eigenvalues, 1e-9, None)
    inv_sqrt = eigenvectors @ np.diag(1.0 / np.sqrt(clipped)) @ eigenvectors.T
    return inv_sqrt @ matrix


class FastICAFrontend(BaseFrontend):
    method_name = "fastica"
    method_version = "1.0"

    def _run(self, signal_sample: SignalSample, config: FrontendConfig) -> FrontendComputation:
        matrix = prepare_matrix(signal_sample, config.parameters)
        if matrix.shape[1] < 2:
            values = matrix_to_channel_values(matrix, signal_sample.channels)
            return FrontendComputation(
                denoised_values=values,
                quasi_dc_values=values,
                status="failed",
                notes="FastICA requires at least two channels.",
                metadata={"reason": "insufficient_channels"},
            )

        n_components = min(int(config.parameters.get("n_components", matrix.shape[1])), matrix.shape[1])
        max_iter = int(config.parameters.get("max_iter", 200))
        tol = float(config.parameters.get("tol", 1e-4))
        alpha = float(config.parameters.get("alpha", 1.0))
        random_seed = int(config.parameters.get("random_seed", 13))
        selection_window = int(config.parameters.get("selection_window", 3))
        quasi_window = int(config.parameters.get("quasi_window", 3))

        centered = matrix - matrix.mean(axis=0, keepdims=True)
        covariance = np.cov(centered, rowvar=False)
        eigenvectors, singular_values, _ = np.linalg.svd(covariance, full_matrices=False)
        whitening = eigenvectors[:, :n_components] / np.sqrt(singular_values[:n_components] + 1e-9)
        whitened = centered @ whitening

        rng = np.random.default_rng(random_seed)
        weights = rng.normal(size=(n_components, n_components))
        weights = _sym_decorrelation(weights)
        converged = False
        iterations = 0
        sample_count = whitened.shape[0]
        for iterations in range(1, max_iter + 1):
            projected = whitened @ weights.T
            gwx = np.tanh(alpha * projected)
            gprime = alpha * (1.0 - np.square(np.tanh(alpha * projected)))
            updated = (gwx.T @ whitened) / float(sample_count)
            updated -= np.diag(gprime.mean(axis=0)) @ weights
            updated = _sym_decorrelation(updated)
            delta = np.max(np.abs(np.abs(np.diag(updated @ weights.T)) - 1.0))
            weights = updated
            if delta < tol:
                converged = True
                break

        sources = whitened @ weights.T
        scores: list[float] = []
        for index in range(sources.shape[1]):
            component = sources[:, [index]]
            smooth = moving_average(component, selection_window)
            total = float(np.var(component) + 1e-9)
            lowfreq = float(np.var(smooth))
            scores.append(lowfreq / total)
        selected = int(np.argmax(scores))
        selected_source = sources[:, [selected]]
        coefficients, *_ = np.linalg.lstsq(selected_source, centered, rcond=None)
        reconstructed = selected_source @ coefficients + matrix.mean(axis=0, keepdims=True)
        quasi_dc = moving_average(reconstructed, quasi_window)
        status = "ok" if converged else "warning"
        return FrontendComputation(
            denoised_values=matrix_to_channel_values(reconstructed, signal_sample.channels),
            quasi_dc_values=matrix_to_channel_values(quasi_dc, signal_sample.channels),
            status=status,
            notes="FastICA low-frequency component reconstruction.",
            metadata={
                "n_components": n_components,
                "selected_component": selected,
                "component_scores": [float(item) for item in scores],
                "iterations": iterations,
                "converged": converged,
            },
        )

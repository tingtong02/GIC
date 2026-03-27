from __future__ import annotations

import warnings

import numpy as np
from sklearn.decomposition import FastICA
from sklearn.exceptions import ConvergenceWarning

from gic.signal.base import BaseFrontend, FrontendComputation
from gic.signal.preprocess import matrix_to_channel_values, moving_average, prepare_matrix
from gic.signal.schema import FrontendConfig, SignalSample


class FastICAFrontend(BaseFrontend):
    method_name = 'fastica'
    method_version = '1.1'

    def _run(self, signal_sample: SignalSample, config: FrontendConfig) -> FrontendComputation:
        matrix = prepare_matrix(signal_sample, config.parameters)
        if matrix.shape[1] < 2:
            values = matrix_to_channel_values(matrix, signal_sample.channels)
            return FrontendComputation(
                denoised_values=values,
                quasi_dc_values=values,
                status='failed',
                notes='FastICA requires at least two channels.',
                metadata={'reason': 'insufficient_channels'},
            )

        backend = str(config.parameters.get('backend', 'sklearn_fastica'))
        requested_components = int(config.parameters.get('n_components', matrix.shape[1]))
        n_components = max(1, min(requested_components, matrix.shape[1]))
        max_iter = int(config.parameters.get('max_iter', 600))
        tol = float(config.parameters.get('tol', 5e-4))
        random_seed = int(config.parameters.get('random_seed', 13))
        selection_window = int(config.parameters.get('selection_window', 5))
        quasi_window = int(config.parameters.get('quasi_window', 5))

        if backend != 'sklearn_fastica':
            values = matrix_to_channel_values(matrix, signal_sample.channels)
            return FrontendComputation(
                denoised_values=values,
                quasi_dc_values=values,
                status='failed',
                notes=f'Unsupported FastICA backend: {backend}',
                metadata={'backend': backend, 'reason': 'unsupported_backend'},
            )

        try:
            estimator = FastICA(
                n_components=n_components,
                whiten='unit-variance',
                algorithm='parallel',
                max_iter=max_iter,
                tol=tol,
                random_state=random_seed,
            )
            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter('always', ConvergenceWarning)
                sources = estimator.fit_transform(matrix)
            fit_warnings = [str(item.message) for item in caught_warnings if issubclass(item.category, Warning)]
            mixing = estimator.mixing_
            mean_vector = estimator.mean_
            scores: list[float | None] = []
            valid_components: list[int] = []
            for index in range(sources.shape[1]):
                component = sources[:, [index]]
                if not np.isfinite(component).all():
                    scores.append(None)
                    continue
                total = float(np.var(component))
                if not np.isfinite(total) or total <= 1e-9:
                    scores.append(None)
                    continue
                smooth = moving_average(component, selection_window)
                lowfreq = float(np.var(smooth))
                if not np.isfinite(lowfreq):
                    scores.append(None)
                    continue
                scores.append(lowfreq / total)
                valid_components.append(index)

            if not valid_components:
                values = matrix_to_channel_values(matrix, signal_sample.channels)
                return FrontendComputation(
                    denoised_values=values,
                    quasi_dc_values=values,
                    status='failed',
                    notes='FastICA produced no finite, non-degenerate components for selection.',
                    metadata={
                        'backend': backend,
                        'n_components': n_components,
                        'component_scores': scores,
                        'reason': 'no_valid_components',
                    },
                )

            selected = max(valid_components, key=lambda index: float(scores[index]))
            selected_source = sources[:, [selected]]
            selected_mixing = mixing[:, [selected]]
            reconstructed = selected_source @ selected_mixing.T + mean_vector
            quasi_dc = moving_average(reconstructed, quasi_window)
            iterations = int(getattr(estimator, 'n_iter_', max_iter))
            convergence_warning = any('did not converge' in item.lower() for item in fit_warnings)
            converged = iterations < max_iter and not convergence_warning
            status = 'ok' if converged else 'warning'
            return FrontendComputation(
                denoised_values=matrix_to_channel_values(reconstructed, signal_sample.channels),
                quasi_dc_values=matrix_to_channel_values(quasi_dc, signal_sample.channels),
                status=status,
                notes='FastICA low-frequency component reconstruction using sklearn FastICA.',
                metadata={
                    'backend': backend,
                    'n_components': n_components,
                    'selected_component': selected,
                    'component_scores': scores,
                    'iterations': iterations,
                    'converged': converged,
                    'fit_warnings': fit_warnings,
                },
            )
        except Exception as exc:
            values = matrix_to_channel_values(matrix, signal_sample.channels)
            return FrontendComputation(
                denoised_values=values,
                quasi_dc_values=values,
                status='failed',
                notes=f'FastICA failed: {type(exc).__name__}: {exc}',
                metadata={'backend': backend, 'reason': 'sklearn_fastica_failed'},
            )

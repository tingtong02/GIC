from __future__ import annotations

import numpy as np
from sklearn.decomposition import MiniBatchDictionaryLearning, sparse_encode

from gic.signal.base import BaseFrontend, FrontendComputation
from gic.signal.preprocess import (
    matrix_to_channel_values,
    moving_average,
    prepare_matrix,
    soft_threshold,
)
from gic.signal.schema import FrontendConfig, SignalSample


class SparseFrontend(BaseFrontend):
    method_name = 'sparse_denoise'
    method_version = '1.1'

    def _legacy_run(self, matrix: np.ndarray, signal_sample: SignalSample, config: FrontendConfig) -> FrontendComputation:
        trend_window = int(config.parameters.get('trend_window', 3))
        refine_window = int(config.parameters.get('refine_window', trend_window))
        sparsity_lambda = float(config.parameters.get('sparsity_lambda', 1.0))
        trend = moving_average(matrix, trend_window)
        residual = matrix - trend
        sparse_noise = soft_threshold(residual, sparsity_lambda)
        denoised = matrix - sparse_noise
        quasi_dc = moving_average(denoised, refine_window)
        retained_energy = float((sparse_noise ** 2).sum() / ((residual ** 2).sum() + 1e-9))
        return FrontendComputation(
            denoised_values=matrix_to_channel_values(denoised, signal_sample.channels),
            quasi_dc_values=matrix_to_channel_values(quasi_dc, signal_sample.channels),
            status='ok',
            notes='Legacy sparse residual shrinkage baseline.',
            metadata={
                'backend': 'legacy_sparse_baseline',
                'trend_window': trend_window,
                'refine_window': refine_window,
                'sparsity_lambda': sparsity_lambda,
                'retained_sparse_energy_ratio': retained_energy,
            },
        )

    def _run(self, signal_sample: SignalSample, config: FrontendConfig) -> FrontendComputation:
        matrix = prepare_matrix(signal_sample, config.parameters)
        backend = str(config.parameters.get('backend', 'dictionary_lasso'))
        if backend == 'legacy_sparse_baseline':
            return self._legacy_run(matrix, signal_sample, config)
        if backend != 'dictionary_lasso':
            values = matrix_to_channel_values(matrix, signal_sample.channels)
            return FrontendComputation(
                denoised_values=values,
                quasi_dc_values=values,
                status='failed',
                notes=f'Unsupported sparse backend: {backend}',
                metadata={'backend': backend, 'reason': 'unsupported_backend'},
            )

        trend_window = int(config.parameters.get('trend_window', 5))
        refine_window = int(config.parameters.get('refine_window', trend_window))
        alpha = float(config.parameters.get('sparsity_lambda', 1.0))
        n_components = int(config.parameters.get('n_dictionary_components', max(matrix.shape[1] * 2, 4)))
        max_iter = int(config.parameters.get('max_iter', 200))
        random_seed = int(config.parameters.get('random_seed', 17))
        trend = moving_average(matrix, trend_window)
        residual = matrix - trend
        try:
            learner = MiniBatchDictionaryLearning(
                n_components=max(2, n_components),
                alpha=alpha,
                max_iter=max_iter,
                random_state=random_seed,
                batch_size=min(64, max(len(residual), 1)),
                transform_algorithm='lasso_lars',
            )
            learner.fit(residual)
            dictionary = learner.components_
            codes = sparse_encode(residual, dictionary, algorithm='lasso_lars', alpha=alpha)
            sparse_residual = codes @ dictionary
            denoised = matrix - sparse_residual
            quasi_dc = moving_average(denoised, refine_window)
            sparsity_fraction = float(np.mean(np.isclose(codes, 0.0)))
            retained_energy = float((sparse_residual ** 2).sum() / ((residual ** 2).sum() + 1e-9))
            return FrontendComputation(
                denoised_values=matrix_to_channel_values(denoised, signal_sample.channels),
                quasi_dc_values=matrix_to_channel_values(quasi_dc, signal_sample.channels),
                status='ok',
                notes='Sparse denoising baseline using dictionary learning and sparse coding.',
                metadata={
                    'backend': backend,
                    'trend_window': trend_window,
                    'refine_window': refine_window,
                    'sparsity_lambda': alpha,
                    'dictionary_components': int(dictionary.shape[0]),
                    'code_sparsity_fraction': sparsity_fraction,
                    'retained_sparse_energy_ratio': retained_energy,
                },
            )
        except Exception as exc:
            values = matrix_to_channel_values(matrix, signal_sample.channels)
            return FrontendComputation(
                denoised_values=values,
                quasi_dc_values=values,
                status='failed',
                notes=f'Sparse denoising failed: {type(exc).__name__}: {exc}',
                metadata={'backend': backend, 'reason': 'dictionary_lasso_failed'},
            )

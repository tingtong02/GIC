# Signal Frontend Overview

## Goal

Phase 3 builds a unified, comparable, and exportable signal frontend layer that turns noisy or mixed time series into quasi-DC series and signal-ready features.

## Inputs and Outputs

- Input: standardized time series from Phase 1 and optional Phase 2 time-indexed references.
- Output: `FrontendResult`, `SignalFeatureSet`, quality report, comparison report, and signal-ready exported assets.

## Method Set

- `raw_baseline`: no processing baseline.
- `lowfreq_baseline`: moving-average low-frequency extraction.
- `fastica`: numpy-based FastICA baseline for multi-channel blind source separation.
- `sparse_denoise`: sparse residual shrinkage baseline.

## Why Multiple Methods

Different frontends respond differently to noise, smoothing strength, runtime cost, and quasi-DC fidelity. Phase 3 therefore compares methods under one schema instead of binding the project to a single signal trick.

## Current Default Recommendation

The default recommendation is selected from the comparison report using configured score weights plus a stable tie-break priority. The current configuration favors `lowfreq_baseline` first when scores are close because it is stable, cheap, and easy to trace.

## Known Limits

- `fastica` is implemented as a numpy baseline because `scipy` and `sklearn` are not installed in the current environment.
- `sparse_denoise` is a simplified sparse residual baseline, not a full dictionary learning system.
- Current Phase 3 examples rely on one small geomagnetic fixture plus synthetic noise injection for controlled comparison.

# Phase 4 Completion Note

Phase 4 implementation status:
- Graph-ready schema, builder, export, manifest validation, and dataset reload interfaces are implemented and tested.
- Baseline model coverage now includes `mlp`, `gcn`, `graphsage`, and `gat` on one shared Phase 4 dataset interface.
- `train-baseline` and `eval-baseline` now support both non-graph and graph baselines, with checkpoint, metric, prediction, and reconstruction-map export.
- `graph-build-report` now generates a baseline comparison report plus minimum ablation for sparsity and signal/physics feature toggles.
- Graph-ready ablation variants export to dataset-specific sample directories, so repeated Phase 4 report runs do not overwrite each other.

Current default Phase 4 results:
- Latest report: `reports/phase_4_20260327T140729Z_1355128f/phase4_baseline_report.json`
- Default graph baseline: `gat`
- Default dataset ranking: `mlp > gat > graphsage > gcn`
- Current graph vs non-graph result: graph does **not** beat the non-graph baseline on hidden-node MAE for the default dataset.
- Hidden-node MAE on the default dataset: `mlp = 46.4156`, `gat = 47.1538`, `graphsage = 55.0604`, `gcn = 58.3188`

Minimum ablation takeaways:
- Sparsity sweep was exported and evaluated at `0.3`, `0.7`, and `0.9`.
- On the current small default dataset, `mlp` remained better than `gcn` at all tested sparsity levels.
- Disabling signal features hurt both `mlp` and `gcn` on the current default setup.
- Disabling physics baseline features caused only a small change for `mlp` and improved `gcn` slightly relative to its default setting, which should be revisited in Phase 5 rather than overfit inside Phase 4.

Phase-boundary conclusion:
- Phase 4 code, data, CLI, reporting, and test coverage are now in place.
- The Phase 4 implementation scope is therefore complete as an engineering baseline.
- However, the stronger empirical acceptance claim from the roadmap, namely that graph baseline should clearly beat non-graph baseline, is **not yet met** on the current default benchmark.
- This gap should be treated as an explicit Phase 5 input, not hidden or papered over.

Known cautions for handoff:
- The current Phase 4 benchmark remains very small, so model ranking stability is limited.
- Graph structure is now testable and reproducible, but not yet validated as a winning reconstruction strategy on the present default dataset.
- Phase 5 should reuse the current graph-ready schema, dataset loader, training loop, and evaluation exports rather than rebuilding them.

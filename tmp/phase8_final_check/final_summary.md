# Final System Summary

## Default Path
- Default variant: `without_kg`
- KG in default: `False`
- Default model id: `phase5_default`
- Phase 7 promotion decision: `phase5_default_real_event_leader`

## Synthetic Benchmark Summary
- Dataset: `case118_graph_broader`
- Phase 4 best hidden-node MAE: `21.214930`
- Phase 4 graph hidden-node MAE: `22.175137`
- Phase 5 default hidden-node MAE: `7.737464`
- Phase 6 feature_only hidden-node MAE: `5.947531`

## Real Event Summary
- Event assets: `9`
- Evaluation rows: `27`
- Decision: `phase5_default_real_event_leader`
- phase4_best_graph: mean proxy hidden MAE `1363.753755`, mean trend correlation `-0.722894`
- phase5_default: mean proxy hidden MAE `85.786338`, mean trend correlation `-0.711156`
- phase6_feature_only: mean proxy hidden MAE `77.114395`, mean trend correlation `-0.733496`

## Limitations
- Final default remains evidence-bounded and is not a production deployment claim.
- Real-event validation still relies on station-local disturbance references rather than full-network truth.
- KG remains available as an optional final variant even when it is not promoted to the default path.

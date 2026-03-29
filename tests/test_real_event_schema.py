from pathlib import Path

import json

from gic.config import load_config
from gic.eval.real_events import flatten_event_records
from gic.eval.real_pipeline import load_all_real_event_records

ROOT = Path(__file__).resolve().parents[1]


def test_phase7_event_configs_flatten_into_records() -> None:
    main_payload = json.loads((ROOT / 'configs/phase7/events/main_event_set.yaml').read_text(encoding='utf-8'))
    dataset = flatten_event_records(main_payload)
    assert dataset.event_set_name == 'intermagnet_2020_main_event_set'
    assert len(dataset.records) == 1
    assert dataset.records[0].event_id == 'storm_2020_sep01'
    assert dataset.records[0].evidence.normalized_level() == 3


def test_phase7_combined_event_dataset_contains_three_events() -> None:
    config = load_config(ROOT / 'configs/phase7/phase7_dev.yaml')
    dataset = load_all_real_event_records(ROOT, config)
    assert len(dataset.records) == 3
    assert {item.event_id for item in dataset.records} == {
        'storm_2020_sep01',
        'storm_2020_oct01',
        'storm_2020_nov01',
    }

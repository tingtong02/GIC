from __future__ import annotations

import re
import struct
from pathlib import Path
from typing import Any

import pandas as pd


_MONTH_INDEX = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
_DAY_BLOCK_SIZE = 23552
_DAY_HEADER_SIZE = 512
_COMPONENT_BLOCK_SIZE = 5760
_RECORD_STRUCT = struct.Struct('<4i')
_SCALE_MAP = {"X": 0.1, "Y": 0.1, "Z": 0.1, "H": 0.1, "F": 0.1, "G": 0.1, "D": 0.1}
_UNIT_MAP = {"X": "nT", "Y": "nT", "Z": "nT", "H": "nT", "F": "nT", "G": "nT", "D": "arcmin"}


def parse_intermagnet_readme(readme_path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    current_key: str | None = None
    buffer: list[str] = []
    for raw_line in readme_path.read_text(encoding='latin1').splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if ':' in line:
            key, value = line.split(':', 1)
            normalized = key.strip().lower().replace(' ', '_').replace('-', '_')
            current_key = normalized
            buffer = [value.strip()]
            metadata[current_key] = value.strip()
        elif current_key is not None:
            buffer.append(line.strip())
            metadata[current_key] = ' '.join(part for part in buffer if part)
    metadata['readme_path'] = str(readme_path)
    metadata['station_id'] = str(metadata.get('station_id') or readme_path.suffix.replace('.', '').upper())
    return metadata


def _header_component_order(day_header: bytes) -> str:
    order = day_header[44:48].decode('ascii', errors='ignore').strip().upper()
    return order if len(order) == 4 else 'XYZF'


def _normalize_value(component: str, value: int) -> float | None:
    if abs(value) >= 9_000_000 or value == -1:
        return None
    if component in {'F', 'G'} and value == 0:
        return None
    return float(value) * _SCALE_MAP.get(component, 1.0)


def _extract_component_series(component_block: bytes, component: str) -> list[float | None]:
    values: list[float | None] = []
    for offset in range(0, len(component_block), _RECORD_STRUCT.size):
        packed = component_block[offset : offset + _RECORD_STRUCT.size]
        if len(packed) != _RECORD_STRUCT.size:
            break
        values.extend(_normalize_value(component, item) for item in _RECORD_STRUCT.unpack(packed))
    return values


def parse_intermagnet_station_archive(station_root: Path) -> dict[str, Any]:
    if not station_root.exists() or not station_root.is_dir():
        raise ValueError(f'INTERMAGNET station root does not exist: {station_root}')
    readme_candidates = sorted(station_root.glob('readme.*'))
    if not readme_candidates:
        raise ValueError(f'INTERMAGNET station root missing readme.* file: {station_root}')
    readme_path = readme_candidates[0]
    metadata = parse_intermagnet_readme(readme_path)
    station_id = str(metadata.get('station_id', station_root.name.upper())).upper()
    bin_files = sorted(station_root.glob(f'{station_root.name}20*.bin'))
    if not bin_files:
        raise ValueError(f'INTERMAGNET station root missing monthly .bin files: {station_root}')
    dka_paths = [str(path) for path in sorted(station_root.glob('*.dka'))]
    blv_paths = [str(path) for path in sorted(station_root.glob('*.blv'))]
    yearmean_paths = [str(path) for path in sorted(station_root.glob('yearmean.*'))]

    component_order = ''
    time_index: list[str] = []
    component_values: dict[str, list[float | None]] = {}

    for monthly_path in bin_files:
        month_code = monthly_path.stem[-3:].lower()
        month = _MONTH_INDEX.get(month_code)
        if month is None:
            raise ValueError(f'Unsupported INTERMAGNET month code in {monthly_path.name}')
        year_match = re.search(r'[a-z]{3}(\d{2})[a-z]{3}$', monthly_path.stem, flags=re.IGNORECASE)
        if not year_match:
            raise ValueError(f'Failed to parse year from {monthly_path.name}')
        year = 2000 + int(year_match.group(1))
        raw_bytes = monthly_path.read_bytes()
        if len(raw_bytes) % _DAY_BLOCK_SIZE != 0:
            raise ValueError(f'Unexpected INTERMAGNET block size for {monthly_path}')
        day_count = len(raw_bytes) // _DAY_BLOCK_SIZE
        for day_offset in range(day_count):
            start = day_offset * _DAY_BLOCK_SIZE
            block = raw_bytes[start : start + _DAY_BLOCK_SIZE]
            header = block[:_DAY_HEADER_SIZE]
            data = block[_DAY_HEADER_SIZE:]
            day_components = _header_component_order(header)
            if not component_order:
                component_order = day_components
                component_values = {component: [] for component in component_order}
            if day_components != component_order:
                raise ValueError(
                    f'Inconsistent component order in {monthly_path.name}: {day_components} != {component_order}'
                )
            start_time = pd.Timestamp(year=year, month=month, day=day_offset + 1, tz='UTC')
            stamps = pd.date_range(start=start_time, periods=1440, freq='min', inclusive='left')
            time_index.extend(stamp.strftime('%Y-%m-%dT%H:%M:%SZ') for stamp in stamps)
            for component_index, component in enumerate(component_order):
                comp_start = component_index * _COMPONENT_BLOCK_SIZE
                comp_stop = comp_start + _COMPONENT_BLOCK_SIZE
                component_block = data[comp_start:comp_stop]
                component_values[component].extend(_extract_component_series(component_block, component))

    metadata.update(
        {
            'provenance_blv_paths': blv_paths,
            'provenance_dka_paths': dka_paths,
            'provenance_yearmean_paths': yearmean_paths,
            'component_order': list(component_order),
            'raw_monthly_paths': [str(path) for path in bin_files],
            'disable_synthetic_noise': True,
            'reference_available': False,
            'source_format': 'intermagnet_bin_v1',
            'benchmark_type': 'real_event',
        }
    )
    return {
        'station_id': station_id,
        'time_index': time_index,
        'value_columns': list(component_order),
        'values': component_values,
        'units': {component: _UNIT_MAP.get(component, 'unknown') for component in component_order},
        'metadata': metadata,
    }

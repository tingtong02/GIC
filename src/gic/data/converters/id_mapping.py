from __future__ import annotations


def build_id_mapping(raw_ids: list[str], prefix: str) -> dict[str, str]:
    return {raw_id: f"{prefix}_{raw_id}" for raw_id in raw_ids}

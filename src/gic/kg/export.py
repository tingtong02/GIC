from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gic.kg.schema import KGManifest, KGSchemaDefinition, kg_to_dict
from gic.utils.paths import ensure_directory, resolve_path


def _kg_root(project_root: Path, kg_config: dict[str, Any]) -> Path:
    return ensure_directory(resolve_path(project_root, kg_config.get('output_root', 'data/processed/kg')))


def export_schema(*, project_root: Path, kg_config: dict[str, Any], dataset_name: str, schema: KGSchemaDefinition) -> str:
    root = ensure_directory(_kg_root(project_root, kg_config) / 'schema')
    destination = root / f'{dataset_name}.schema.json'
    destination.write_text(json.dumps(kg_to_dict(schema), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return str(destination)


def export_kg_bundle(
    *,
    project_root: Path,
    kg_config: dict[str, Any],
    dataset_name: str,
    entities: list[object],
    relations: list[object],
    manifest: KGManifest,
    feature_payload: dict[str, Any] | None = None,
    rule_payload: dict[str, Any] | None = None,
) -> dict[str, str]:
    root = _kg_root(project_root, kg_config)
    entities_root = ensure_directory(root / 'entities')
    relations_root = ensure_directory(root / 'relations')
    manifests_root = ensure_directory(root / 'manifests')
    exports_root = ensure_directory(root / 'exports')

    entity_path = entities_root / f'{dataset_name}.entities.json'
    relation_path = relations_root / f'{dataset_name}.relations.json'
    manifest_path = manifests_root / f'{dataset_name}.manifest.json'

    entity_path.write_text(json.dumps(kg_to_dict(entities), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    relation_path.write_text(json.dumps(kg_to_dict(relations), indent=2, sort_keys=True) + '\n', encoding='utf-8')

    paths = {
        'entities': str(entity_path),
        'relations': str(relation_path),
        'manifest': str(manifest_path),
    }
    if feature_payload is not None:
        feature_path = exports_root / f'{dataset_name}.features.json'
        feature_path.write_text(json.dumps(feature_payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        paths['features'] = str(feature_path)
    if rule_payload is not None:
        rule_path = exports_root / f'{dataset_name}.rules.json'
        rule_path.write_text(json.dumps(rule_payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        paths['rules'] = str(rule_path)

    manifest.paths.update(paths)
    manifest_path.write_text(json.dumps(kg_to_dict(manifest), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return paths

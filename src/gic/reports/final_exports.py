from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def export_final_report_bundle(report: dict[str, Any], *, destination_root: Path, summary_name: str = 'final_summary') -> dict[str, str]:
    destination_root.mkdir(parents=True, exist_ok=True)
    json_path = destination_root / f'{summary_name}.json'
    md_path = destination_root / f'{summary_name}.md'
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    markdown = str(report.get('markdown', ''))
    _write_text(md_path, markdown.rstrip() + '\n')
    return {
        'summary_json_path': str(json_path),
        'summary_markdown_path': str(md_path),
    }


def export_final_casebook(casebook: dict[str, Any], *, destination_root: Path, json_name: str, md_name: str) -> dict[str, str]:
    destination_root.mkdir(parents=True, exist_ok=True)
    json_path = destination_root / json_name
    md_path = destination_root / md_name
    json_path.write_text(json.dumps(casebook, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    lines = ['# Final Casebook', '']
    for item in casebook.get('cases', []):
        lines.append(f"## {item.get('case_type', 'case')}")
        lines.append(f"- Title: `{item.get('title', '')}`")
        lines.append(f"- Summary: {item.get('summary', '')}")
        for bullet in item.get('details', []):
            lines.append(f'- {bullet}')
        lines.append('')
    _write_text(md_path, '\n'.join(lines).rstrip() + '\n')
    return {
        'casebook_json_path': str(json_path),
        'casebook_markdown_path': str(md_path),
    }


def export_final_doc_summary(text: str, *, destination_root: Path, filename: str) -> str:
    return str(_write_text(destination_root / filename, text.rstrip() + '\n'))

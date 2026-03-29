from __future__ import annotations

import html
from pathlib import Path


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def write_svg(path: str | Path, width: int, height: int, body: str, *, title: str) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="100%" height="100%" fill="#fbfbfd" stroke="#d0d7de"/>'
        f'<text x="24" y="36" font-size="22" font-family="monospace" fill="#0f172a">{_escape(title)}</text>'
        f'{body}'
        '</svg>'
    )
    destination.write_text(svg, encoding='utf-8')
    return destination


def bar_chart_body(labels: list[str], values: list[float], *, width: int = 860, height: int = 420, color: str = '#1d4ed8') -> str:
    chart_left = 80
    chart_bottom = height - 70
    chart_top = 70
    chart_width = width - 120
    chart_height = chart_bottom - chart_top
    safe_values = [max(0.0, float(value)) for value in values] or [0.0]
    max_value = max(safe_values) or 1.0
    step = chart_width / max(len(labels), 1)
    bar_width = min(72, step * 0.55)
    parts = [
        f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_left + chart_width}" y2="{chart_bottom}" stroke="#475569"/>',
        f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#475569"/>',
    ]
    for index, (label, value) in enumerate(zip(labels, safe_values)):
        x = chart_left + step * index + (step - bar_width) / 2
        bar_height = 0.0 if max_value <= 0 else chart_height * (value / max_value)
        y = chart_bottom - bar_height
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" fill="{color}" opacity="0.88"/>')
        parts.append(f'<text x="{x + bar_width / 2:.2f}" y="{chart_bottom + 22}" text-anchor="middle" font-size="12" font-family="monospace" fill="#0f172a">{_escape(label)}</text>')
        parts.append(f'<text x="{x + bar_width / 2:.2f}" y="{y - 8:.2f}" text-anchor="middle" font-size="12" font-family="monospace" fill="#0f172a">{value:.2f}</text>')
    return ''.join(parts)


def line_chart_body(labels: list[str], series: dict[str, list[float]], *, width: int = 860, height: int = 420) -> str:
    chart_left = 80
    chart_bottom = height - 70
    chart_top = 80
    chart_width = width - 140
    chart_height = chart_bottom - chart_top
    palette = ['#1d4ed8', '#dc2626', '#16a34a', '#7c3aed']
    all_values = [float(value) for values in series.values() for value in values]
    min_value = min(all_values) if all_values else 0.0
    max_value = max(all_values) if all_values else 1.0
    if abs(max_value - min_value) < 1e-9:
        max_value = min_value + 1.0
    step = chart_width / max(len(labels) - 1, 1)
    parts = [
        f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_left + chart_width}" y2="{chart_bottom}" stroke="#475569"/>',
        f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#475569"/>',
    ]
    for idx, label in enumerate(labels):
        x = chart_left + idx * step
        parts.append(f'<text x="{x:.2f}" y="{chart_bottom + 22}" text-anchor="middle" font-size="12" font-family="monospace" fill="#0f172a">{_escape(label)}</text>')
    for series_index, (name, values) in enumerate(series.items()):
        color = palette[series_index % len(palette)]
        points = []
        for idx, value in enumerate(values):
            x = chart_left + idx * step
            ratio = (float(value) - min_value) / (max_value - min_value)
            y = chart_bottom - ratio * chart_height
            points.append((x, y, float(value)))
        parts.append('<polyline fill="none" stroke="%s" stroke-width="3" points="%s"/>' % (color, ' '.join(f'{x:.2f},{y:.2f}' for x, y, _ in points)))
        for x, y, value in points:
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>')
            parts.append(f'<text x="{x:.2f}" y="{y - 10:.2f}" text-anchor="middle" font-size="11" font-family="monospace" fill="#334155">{value:.2f}</text>')
        legend_y = 42 + series_index * 18
        parts.append(f'<rect x="640" y="{legend_y - 10}" width="12" height="12" fill="{color}"/>')
        parts.append(f'<text x="660" y="{legend_y}" font-size="12" font-family="monospace" fill="#0f172a">{_escape(name)}</text>')
    return ''.join(parts)


def info_cards_body(items: list[tuple[str, str]], *, width: int = 860) -> str:
    parts = []
    x = 30
    y = 72
    card_width = min(240, max(180, width // max(len(items), 1) - 20))
    for title, value in items:
        parts.append(f'<rect x="{x}" y="{y}" rx="12" ry="12" width="{card_width}" height="96" fill="#ffffff" stroke="#cbd5e1"/>')
        parts.append(f'<text x="{x + 16}" y="{y + 30}" font-size="14" font-family="monospace" fill="#475569">{_escape(title)}</text>')
        parts.append(f'<text x="{x + 16}" y="{y + 62}" font-size="20" font-family="monospace" fill="#0f172a">{_escape(value)}</text>')
        x += card_width + 16
    return ''.join(parts)

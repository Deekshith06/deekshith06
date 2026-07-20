#!/usr/bin/env python3
"""Render the verified contribution JSON as an accessible animated SVG."""

from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
IN_PATH = HERE.parent / "data" / "contributions.json"
OUT_PATH = HERE.parent / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
CELL, GAP, STEP = 12, 3, 15
PAD, LEFT_LABEL_W, TOP_LABEL_H, TITLEBAR_H = 22, 30, 20, 30
BG, BG2, FRAME = "#0a0e14", "#0d1420", "#1f6feb"
MUTED, TEXT, ACCENT, GREEN, GOLD = "#7d8590", "#e6edf3", "#22d3ee", "#39d353", "#f2cc60"
COL_T, ROW_T, CELL_DUR = 0.018, 0.045, 0.42


def level_for(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    if count <= 50:
        return 4
    return 5


def validate_data(data: dict[str, Any]) -> list[dict[str, Any]]:
    days = data.get("days")
    if not isinstance(days, list) or not days:
        raise ValueError("contributions.json has no day records")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in days:
        if not isinstance(item, dict):
            raise ValueError("a contribution day is not an object")
        date_text = str(item.get("date", ""))
        date = dt.date.fromisoformat(date_text)
        count = int(item.get("count", 0))
        if count < 0:
            raise ValueError(f"negative contribution count for {date_text}")
        if date_text in seen:
            raise ValueError(f"duplicate contribution date: {date_text}")
        seen.add(date_text)
        normalized.append({"date": date, "date_text": date_text, "count": count})

    normalized.sort(key=lambda item: item["date"])
    return normalized


def build_grid(days: list[dict[str, Any]]) -> tuple[list[list[dict[str, Any] | None]], dt.date]:
    first_date = days[0]["date"]
    last_date = days[-1]["date"]
    start_sunday = first_date - dt.timedelta(days=(first_date.weekday() + 1) % 7)
    end_saturday = last_date + dt.timedelta(days=(5 - last_date.weekday()) % 7)
    column_count = ((end_saturday - start_sunday).days // 7) + 1
    grid: list[list[dict[str, Any] | None]] = [[None for _ in range(7)] for _ in range(column_count)]

    for item in days:
        offset = (item["date"] - start_sunday).days
        column, row = divmod(offset, 7)
        grid[column][row] = item

    return grid, start_sunday


def render(data: dict[str, Any]) -> str:
    days = validate_data(data)
    grid, start_sunday = build_grid(days)
    username = html.escape(str(data.get("username") or "Deekshith06"))
    column_count = len(grid)
    art_width, art_height = column_count * STEP, 7 * STEP

    month_labels: list[tuple[int, str]] = []
    seen_months: set[tuple[int, int]] = set()
    for column_index, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = cell["date"]
            key = (date.year, date.month)
            if key not in seen_months and date.day <= 7:
                seen_months.add(key)
                month_labels.append((column_index, date.strftime("%b")))
            break

    canvas_width = PAD + LEFT_LABEL_W + art_width + PAD
    stats_height = 88
    canvas_height = TITLEBAR_H + TOP_LABEL_H + art_height + stats_height + PAD
    title = f"{username}'s GitHub contribution graph"
    description = (
        f"{int(data.get('total_contributions', 0)):,} public contributions from "
        f"{days[0]['date_text']} to {days[-1]['date_text']}."
    )

    css = f"""
@keyframes cell {{
  0% {{ opacity: 0; transform: translateY(-6px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
.c {{ opacity: 0; animation: cell {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both; transform-box: fill-box; }}
@media (prefers-reduced-motion: reduce) {{ .c {{ opacity: 1; animation: none; }} }}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" '
        f'viewBox="0 0 {canvas_width} {canvas_height}" role="img" aria-labelledby="title desc" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f"<title id=\"title\">{title}</title>",
        f"<desc id=\"desc\">{html.escape(description)}</desc>",
        f"<style>{css}</style>",
        "<defs>",
        f'<linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        "</defs>",
        f'<rect width="{canvas_width}" height="{canvas_height}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_width - 1}" height="{canvas_height - 1}" rx="12" fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_width}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
    ]

    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + index * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{color}"/>')

    parts.append(
        f'<text x="{canvas_width / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
        f'{username}@github: ~/contributions --graph</text>'
    )

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    for column_index, label in month_labels:
        parts.append(
            f'<text x="{grid_left + column_index * STEP}" y="{TITLEBAR_H + 14}" fill="{MUTED}" font-size="10">{label}</text>'
        )

    for weekday_index, weekday_name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = grid_top + weekday_index * STEP + CELL * 0.78
        parts.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="9">{weekday_name}</text>')

    for column_index, column in enumerate(grid):
        x = grid_left + column_index * STEP
        for row_index, cell in enumerate(column):
            if cell is None:
                continue
            y = grid_top + row_index * STEP
            count = int(cell["count"])
            level = level_for(count)
            delay = column_index * COL_T + row_index * ROW_T
            plural = "s" if count != 1 else ""
            parts.append(
                f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{PALETTE[level]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{cell["date_text"]}: {count} contribution{plural}</title></rect>'
            )

    legend_y = grid_top + art_height + 6
    legend_x = canvas_width - PAD - (len(PALETTE) * (CELL - 1) + 70)
    parts.append(f'<text x="{legend_x}" y="{legend_y + CELL * 0.8:.1f}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    current_x = legend_x + 8
    for color in PALETTE:
        parts.append(f'<rect x="{current_x}" y="{legend_y}" width="{CELL - 1}" height="{CELL - 1}" rx="2.2" fill="{color}"/>')
        current_x += CELL
    parts.append(f'<text x="{current_x + 4}" y="{legend_y + CELL * 0.8:.1f}" fill="{MUTED}" font-size="10">More</text>')

    separator_y = legend_y + CELL + 14
    parts.append(f'<line x1="0" y1="{separator_y}" x2="{canvas_width}" y2="{separator_y}" stroke="{FRAME}" stroke-opacity="0.25"/>')

    current_streak = int(data.get("current_streak", {}).get("length", 0))
    longest_streak = int(data.get("longest_streak", {}).get("length", 0))
    total = int(data.get("total_contributions", 0))
    best = data.get("best_day", {"count": 0, "date": days[0]["date_text"]})
    line_y = separator_y + 24

    parts.append(
        f'<text x="{PAD}" y="{line_y}" font-size="13" fill="{GREEN}"><tspan font-weight="700">{total:,}</tspan>'
        f'<tspan fill="{MUTED}"> public contributions in the last year</tspan></text>'
    )
    parts.append(
        f'<text x="{canvas_width - PAD}" y="{line_y}" font-size="12" fill="{MUTED}" text-anchor="end">'
        f'{days[0]["date_text"]} &#8594; {days[-1]["date_text"]}</text>'
    )
    line_y += 24
    parts.append(
        f'<text x="{PAD}" y="{line_y}" font-size="13" fill="{MUTED}">current streak '
        f'<tspan fill="{ACCENT}" font-weight="700">{current_streak} days</tspan>'
        f'<tspan>   &#183;   longest </tspan><tspan fill="{ACCENT}" font-weight="700">{longest_streak} days</tspan></text>'
    )
    parts.append(
        f'<text x="{canvas_width - PAD}" y="{line_y}" font-size="12" fill="{MUTED}" text-anchor="end">best day '
        f'<tspan fill="{GOLD}" font-weight="700">{int(best.get("count", 0))}</tspan> on {html.escape(str(best.get("date", "")))}</text>'
    )

    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    data = json.loads(IN_PATH.read_text(encoding="utf-8"))
    svg = render(data)
    OUT_PATH.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()

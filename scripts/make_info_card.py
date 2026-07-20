"""Build the accurate neofetch-style profile information card SVG."""

from __future__ import annotations

import html
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "info-card.svg"
STATIC = bool(os.environ.get("STATIC"))

W, H = 480, 390
PAD, TITLEBAR_H, KEY_X, VAL_X, LINE_H = 20, 30, 20, 112, 20.5
BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK, KEY = "#7d8590", "#c9d1d9", "#ffa657"
SECTION, GREEN, ACCENT = "#58a6ff", "#3fb950", "#22d3ee"

ROWS = [
    ("host",),
    ("kv", "Status", "CSE Student · Full-Stack & AI/ML"),
    ("kv", "Degree", "B.Tech, Computer Science & Engineering"),
    ("kv", "University", "Lovely Professional University"),
    ("kv", "Graduation", "Expected 2027"),
    ("gap",),
    ("sec", "Core Stack"),
    ("kv", "Languages", "Java, Python, C, C++"),
    ("kv", "Frontend", "React, TypeScript, HTML, CSS"),
    ("kv", "Backend", "Spring Boot, Node.js, REST APIs"),
    ("kv", "AI / ML", "Machine Learning, NLP, Computer Vision"),
    ("kv", "Tools", "Git, GitHub, Docker, Vercel"),
    ("gap",),
    ("sec", "Current Focus"),
    ("bul", "Production-focused student projects"),
    ("bul", "Logistics, finance and language AI"),
]


def esc(value: str) -> str:
    return html.escape(value)


def rise(inner: str, index: int) -> str:
    if STATIC:
        return f"<g>{inner}</g>"
    delay = 0.15 + index * 0.06
    return (
        f'<g opacity="0" transform="translate(0,5)">{inner}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.4s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 5" to="0 0" begin="{delay:.2f}s" '
        f'dur="0.4s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/></g>'
    )


def build_svg() -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
        f'aria-labelledby="title desc" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        "<title id=\"title\">Deekshith's profile information</title>",
        "<desc id=\"desc\">B.Tech Computer Science and Engineering student at Lovely Professional University, expected to graduate in 2027.</desc>",
        "<defs>",
        f'<linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#ibg)"/>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + index * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{color}"/>')

    parts.append(
        f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
        "deekshith06@github: ~$ neofetch</text>"
    )

    y = TITLEBAR_H + 30
    for index, row in enumerate(ROWS):
        kind = row[0]
        if kind == "gap":
            y += LINE_H * 0.5
            continue
        if kind == "host":
            inner = (
                f'<text x="{KEY_X}" y="{y:.1f}" font-size="14" font-weight="700">'
                f'<tspan fill="{GREEN}">deekshith06</tspan><tspan fill="{MUTED}">@</tspan>'
                f'<tspan fill="{ACCENT}">github</tspan></text>'
                f'<line x1="{KEY_X + 112}" y1="{y - 4:.1f}" x2="{W - PAD}" y2="{y - 4:.1f}" stroke="{FRAME}" stroke-opacity="0.8"/>'
            )
        elif kind == "sec":
            title = esc(row[1])
            inner = (
                f'<text x="{KEY_X}" y="{y:.1f}" fill="{SECTION}" font-size="12.5" font-weight="700">&#8212; {title}</text>'
                f'<line x1="{KEY_X + 12 + len(row[1]) * 8}" y1="{y - 4:.1f}" x2="{W - PAD}" y2="{y - 4:.1f}" stroke="{FRAME}" stroke-opacity="0.8"/>'
            )
        elif kind == "kv":
            key, value = esc(row[1]), esc(row[2])
            inner = (
                f'<text x="{KEY_X}" y="{y:.1f}" fill="{KEY}" font-size="12.5" font-weight="700">{key}</text>'
                f'<text x="{VAL_X}" y="{y:.1f}" fill="{INK}" font-size="12.5">{value}</text>'
            )
        elif kind == "bul":
            text = esc(row[1])
            inner = (
                f'<circle cx="{KEY_X + 3}" cy="{y - 4:.1f}" r="2.5" fill="{GREEN}"/>'
                f'<text x="{KEY_X + 14}" y="{y:.1f}" fill="{INK}" font-size="12.5">{text}</text>'
            )
        else:
            continue
        parts.append(rise(inner, index))
        y += LINE_H

    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    svg = build_svg()
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} {len(svg)} bytes; {W}x{H}")


if __name__ == "__main__":
    main()

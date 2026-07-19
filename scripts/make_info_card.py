#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG that prints in next to the portrait.

The contribution graph already covers your GitHub stats, so this card is for the
story numbers can't tell: what you're building, your stack, the highlights. Each
line fades + slides in on a short stagger (SMIL, so GitHub plays it). Set
STATIC=1 for a frozen frame (handy for local Quick Look previews).

    python scripts/make_info_card.py   # writes info-card.svg
"""
from __future__ import annotations

import os

# ---- edit your story here --------------------------------------------------
USER = "ayotov18@github"
ROWS = [
    ("Name",       "Anthony Yotov"),
    ("Role",       "Founder · Full-Stack Engineer"),
    ("Now",        "Building AdOS — an AI ad operating system"),
    ("Stack",      "Flutter · Dart · Go · Postgres"),
    ("Also",       "Riverpod · GraphQL · ent · NATS · Casbin"),
    ("Infra",      "Cloudflare · MinIO · Meilisearch · OpenBao"),
    ("Focus",      "AI agents · ad-platform integrations"),
    ("Platforms",  "Meta · Google Ads · TikTok"),
    ("Motto",      "ship real, verify with logs"),
]
# ----------------------------------------------------------------------------

FONT_PX = 15
LINE_H = 30
PAD = 22
KEY_W = 108          # column where values start
BG = "#0d1117"
BORDER = "#30363d"
KEY = "#39d353"      # green keys, like neofetch
VAL = "#c9d1d9"      # light-gray values
DIM = "#8b949e"
ACCENT = "#58a6ff"   # blue title
DOT = "#f85149"      # window "traffic light"

STAGGER = 0.12
FADE = 0.5


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def line_group(idx: int, inner: str, y: float) -> str:
    """Wrap a line so it fades + rises into place (or freezes if STATIC)."""
    if os.environ.get("STATIC") == "1":
        return f'<g transform="translate(0 {y:.1f})">{inner}</g>'
    begin = round(idx * STAGGER, 3)
    return (
        f'<g transform="translate(0 {y + 6:.1f})" opacity="0">'
        f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" '
        f'dur="{FADE}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="0 {y + 6:.1f}" to="0 {y:.1f}" begin="{begin}s" dur="{FADE}s" '
        f'fill="freeze" calcMode="spline" keySplines="0.2 0.7 0.2 1"/>'
        f'{inner}</g>'
    )


def build() -> str:
    width = 560
    # title bar + rule + rows
    n_lines = len(ROWS)
    height = PAD * 2 + LINE_H * (n_lines + 2)

    parts = []
    # window dots
    for i, col in enumerate(("#f85149", "#e3b341", "#3fb950")):
        parts.append(f'<circle cx="{PAD + 6 + i * 18}" cy="{PAD}" r="6" fill="{col}"/>')

    y = PAD + LINE_H
    # title:  user@github
    title_inner = (
        f'<text x="{PAD}" y="0" font-size="{FONT_PX}px" font-weight="700" '
        f'fill="{ACCENT}" font-family="monospace">{esc(USER)}</text>'
    )
    parts.append(line_group(0, title_inner, y))

    # rule of dashes under the title (neofetch style)
    y += LINE_H
    rule = "-" * 34
    rule_inner = (
        f'<text x="{PAD}" y="0" font-size="{FONT_PX}px" fill="{DIM}" '
        f'font-family="monospace">{rule}</text>'
    )
    parts.append(line_group(1, rule_inner, y))

    # key: value rows
    for i, (k, v) in enumerate(ROWS):
        y += LINE_H
        inner = (
            f'<text x="{PAD}" y="0" font-size="{FONT_PX}px" font-weight="700" '
            f'fill="{KEY}" font-family="monospace">{esc(k)}</text>'
            f'<text x="{PAD + KEY_W}" y="0" font-size="{FONT_PX}px" fill="{VAL}" '
            f'font-family="monospace">{esc(v)}</text>'
        )
        parts.append(line_group(i + 2, inner, y))

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}"/>'
        f'{"".join(parts)}'
        f'</svg>'
    )


if __name__ == "__main__":
    with open("info-card.svg", "w") as f:
        f.write(build())
    print("wrote info-card.svg")

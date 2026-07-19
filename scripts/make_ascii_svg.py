#!/usr/bin/env python3
"""Turn the prepped portrait into a self-typing, monochrome ASCII-art SVG.

Downsamples to a character grid, maps each cell's brightness to a glyph on a
density ramp (bright -> sparse, dark -> dense), then emits an SVG where each row
wipes in left-to-right on a top-to-bottom stagger, with a small block cursor
riding the wipe edge. Pure SMIL, so GitHub plays it. It prints once and freezes
(no looping). Monochrome + high-contrast on purpose: rainbow ASCII reads as
static; one calm colour reads as a portrait.

    python scripts/make_ascii_svg.py [source-prepped.png] [--out avi-ascii.svg]
"""
from __future__ import annotations

import argparse
from PIL import Image

# bright (sparse) -> dark (dense). Leading space clears the background to nothing.
RAMP = " .`:-=+*cs#%@"

COLS = 100          # character columns; rows derive from the photo aspect
FONT_PX = 11        # monospace font size
CHAR_W = FONT_PX * 0.60   # monospace advance width
LINE_H = FONT_PX * 1.12
PAD = 18
FILL = "#c9d1d9"    # one calm light-gray
CURSOR = "#39d353"  # the wipe-edge block
BG = "#0d1117"      # own terminal panel, so it reads on light OR dark GitHub
BORDER = "#30363d"

ROW_STAGGER = 0.055  # seconds between rows starting
ROW_DUR = 0.5        # seconds for one row to wipe in


def to_rows(path: str) -> list[str]:
    img = Image.open(path).convert("L")
    # Characters are ~twice as tall as wide, so halve the row count to keep
    # the face's proportions.
    rows = max(1, round(COLS * img.height / img.width * 0.5))
    img = img.resize((COLS, rows))
    px = img.load()
    out = []
    last = len(RAMP) - 1
    for y in range(rows):
        line = []
        for x in range(COLS):
            brightness = px[x, y]
            # bright -> index 0 (space), dark -> last (@)
            idx = round((255 - brightness) / 255 * last)
            line.append(RAMP[idx])
        out.append("".join(line).rstrip())
    # trim fully-blank leading/trailing rows
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(rows: list[str]) -> str:
    text_w = COLS * CHAR_W
    w = PAD * 2 + text_w
    h = PAD * 2 + len(rows) * LINE_H
    clips, texts, cursors = [], [], []
    for r, line in enumerate(rows):
        y = PAD + r * LINE_H
        baseline = y + FONT_PX * 0.9
        begin = round(r * ROW_STAGGER, 3)
        row_w = max(1.0, len(line) * CHAR_W)
        clips.append(
            f'<clipPath id="c{r}"><rect x="{PAD:.1f}" y="{y:.1f}" '
            f'width="0" height="{LINE_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{row_w:.1f}" '
            f'begin="{begin}s" dur="{ROW_DUR}s" fill="freeze" calcMode="linear"/>'
            f'</rect></clipPath>'
        )
        if line.strip():
            texts.append(
                f'<text x="{PAD:.1f}" y="{baseline:.1f}" clip-path="url(#c{r})" '
                f'xml:space="preserve">{esc(line)}</text>'
            )
            cursors.append(
                f'<rect x="{PAD:.1f}" y="{y:.1f}" width="{CHAR_W:.1f}" '
                f'height="{LINE_H:.1f}" fill="{CURSOR}" opacity="0">'
                f'<animate attributeName="x" from="{PAD:.1f}" to="{PAD + row_w:.1f}" '
                f'begin="{begin}s" dur="{ROW_DUR}s" fill="freeze"/>'
                f'<animate attributeName="opacity" values="0.9;0.9;0" '
                f'keyTimes="0;0.85;1" begin="{begin}s" dur="{ROW_DUR}s" fill="freeze"/>'
                f'</rect>'
            )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'width="{w:.0f}" height="{h:.0f}" font-family="\'SFMono-Regular\',Consolas,'
        f'\'Liberation Mono\',Menlo,monospace">'
        f'<style>text{{font-size:{FONT_PX}px;fill:{FILL};white-space:pre;}}</style>'
        f'<rect x="0.5" y="0.5" width="{w-1:.1f}" height="{h-1:.1f}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}"/>'
        f'<defs>{"".join(clips)}</defs>'
        f'{"".join(texts)}{"".join(cursors)}'
        f'</svg>'
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default="source-prepped.png")
    ap.add_argument("--out", default="avi-ascii.svg")
    a = ap.parse_args()
    svg = build(to_rows(a.src))
    with open(a.out, "w") as f:
        f.write(svg)
    print(f"wrote {a.out}")

#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53-week contribution heatmap.

Rounded, colour-ramped boxes laid out as the classic weeks x weekdays calendar.
They reveal once on load with a diagonal, line-after-line slide-down (CSS
keyframes, which GitHub plays inside an <img>-embedded SVG), then freeze — no
looping glow. Month + weekday labels, a Less->More legend, and a stats footer.

    python scripts/render_heatmap_svg.py   # writes contrib-heatmap.svg
"""
from __future__ import annotations

import datetime as dt
import json

IN = "data/contributions.json"
OUT = "contrib-heatmap.svg"

# none -> brightest (level 5 is a neon top end, used for your best day)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

BOX = 11
GAP = 3
STEP = BOX + GAP
PAD = 20
TOP = 30          # room for month labels
LEFT = 30         # room for weekday labels
BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
DIM = "#8b949e"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def build(data: dict) -> str:
    days = data["days"]
    st = data["stats"]
    first = d(days[0]["date"])
    first_sunday = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    best_date = (st.get("best_day") or {}).get("date")

    cols = 0
    cells = []
    month_labels = []
    seen_months = set()
    for day in days:
        date = d(day["date"])
        col = (date - first_sunday).days // 7
        row = (date.weekday() + 1) % 7  # Sun=0 .. Sat=6
        cols = max(cols, col)
        level = min(int(day["level"]), 4)
        if day["date"] == best_date and day["count"] > 0:
            level = 5
        x = LEFT + col * STEP
        y = TOP + row * STEP
        delay = round((col + row) * 0.012, 3)
        cells.append(
            f'<rect x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2.5" '
            f'fill="{PALETTE[level]}" class="cell" style="animation-delay:{delay}s">'
            f'<title>{day["count"]} on {day["date"]}</title></rect>'
        )
        # month label at the first column of each new month (top row)
        key = day["date"][:7]
        if date.day <= 7 and key not in seen_months and row == 0:
            seen_months.add(key)
            month_labels.append(
                f'<text x="{x}" y="{TOP - 8}" fill="{DIM}" font-size="10">'
                f'{MONTHS[date.month - 1]}</text>'
            )

    width = LEFT + (cols + 1) * STEP + PAD
    grid_bottom = TOP + 7 * STEP
    legend_y = grid_bottom + 16
    footer_y = legend_y + 28
    height = footer_y + 14

    # weekday labels (Mon/Wed/Fri like GitHub)
    wd = []
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        wd.append(
            f'<text x="2" y="{TOP + row * STEP + BOX - 1}" fill="{DIM}" '
            f'font-size="9">{label}</text>'
        )

    # legend: Less [swatches] More
    legend = [f'<text x="{width - 210}" y="{legend_y + BOX - 1}" fill="{DIM}" '
              f'font-size="10">Less</text>']
    for i in range(5):
        lx = width - 178 + i * (BOX + 3)
        legend.append(
            f'<rect x="{lx}" y="{legend_y}" width="{BOX}" height="{BOX}" rx="2.5" '
            f'fill="{PALETTE[i]}"/>'
        )
    legend.append(
        f'<text x="{width - 178 + 5 * (BOX + 3) + 6}" y="{legend_y + BOX - 1}" '
        f'fill="{DIM}" font-size="10">More</text>'
    )

    total = st["total"]
    footer = (
        f'<text x="{LEFT}" y="{footer_y + BOX - 1}" fill="{TEXT}" font-size="12">'
        f'<tspan font-weight="700">{total:,}</tspan> contributions in the last year'
        f'</text>'
        f'<text x="{width - PAD}" y="{footer_y + BOX - 1}" fill="{DIM}" '
        f'font-size="11" text-anchor="end">'
        f'\U0001F525 {st["current_streak"]}d streak &#183; best {st["longest_streak"]}d '
        f'&#183; top day {st["best_day"]["count"]}</text>'
    )

    style = (
        "<style>"
        "text{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;}"
        ".cell{opacity:0;transform:translateY(3px) scale(.6);"
        "transform-origin:center;transform-box:fill-box;"
        "animation:pop .45s ease-out forwards;}"
        "@keyframes pop{to{opacity:1;transform:translateY(0) scale(1);}}"
        "</style>"
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
        f'{style}'
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}"/>'
        f'{"".join(month_labels)}{"".join(wd)}'
        f'{"".join(cells)}'
        f'{"".join(legend)}{footer}'
        f'</svg>'
    )


if __name__ == "__main__":
    with open(IN) as f:
        data = json.load(f)
    with open(OUT, "w") as f:
        f.write(build(data))
    print(f"wrote {OUT}")

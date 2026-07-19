#!/usr/bin/env python3
"""Fetch a real GitHub contribution calendar as public HTML — no token, no API.

GitHub serves the calendar the profile page itself uses at
https://github.com/users/<user>/contributions. We parse the day cells and the
associated <tool-tip> counts, then write data/contributions.json with the raw
days plus derived stats (totals, streaks, best day, monthly totals).

    python scripts/fetch_contributions.py            # uses USERNAME below / $GH_USER
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USER", "ayotov18")
URL = "https://github.com/users/{}/contributions"
OUT = "data/contributions.json"


def fetch_html(user: str) -> str:
    r = requests.get(
        URL.format(user),
        headers={
            "User-Agent": "Mozilla/5.0 (profile-art; +https://github.com/{})".format(user),
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "text/html",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.text


def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # id -> count, from the tooltip elements ("12 contributions on ..." / "No ...")
    tips: dict[str, int] = {}
    for tip in soup.find_all("tool-tip"):
        fid = tip.get("for")
        if not fid:
            continue
        txt = tip.get_text(" ", strip=True)
        m = re.match(r"\s*([\d,]+)\s+contribution", txt)
        tips[fid] = int(m.group(1).replace(",", "")) if m else 0

    days: list[dict] = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        level = int(td.get("data-level") or 0)
        # count: prefer a legacy data-count, else the tooltip, else 0
        if td.get("data-count") is not None:
            count = int(td["data-count"])
        else:
            count = tips.get(td.get("id", ""), 0)
        days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def stats(days: list[dict]) -> dict:
    today = dt.date.today().isoformat()
    past = [d for d in days if d["date"] <= today]
    total = sum(d["count"] for d in past)
    best = max(past, key=lambda d: d["count"], default={"count": 0, "date": None})

    # longest streak
    longest = cur = 0
    for d in past:
        cur = cur + 1 if d["count"] > 0 else 0
        longest = max(longest, cur)

    # current streak (trailing). Today counts if >0; if today is still 0, the
    # streak can still stand on yesterday.
    current = 0
    for d in reversed(past):
        if d["count"] > 0:
            current += 1
        elif d["date"] == today:
            continue  # a not-yet-active today doesn't break the streak
        else:
            break

    monthly: dict[str, int] = defaultdict(int)
    for d in past:
        monthly[d["date"][:7]] += d["count"]

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best.get("date"), "count": best.get("count", 0)},
        "monthly": dict(sorted(monthly.items())),
        "range": {"from": past[0]["date"], "to": past[-1]["date"]} if past else {},
    }


def main() -> int:
    user = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    days = parse(fetch_html(user))
    if not days:
        print("no day cells parsed — GitHub markup may have changed", file=sys.stderr)
        return 1
    payload = {
        "user": user,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "days": days,
        "stats": stats(days),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    s = payload["stats"]
    print(f"wrote {OUT}: {len(days)} days, {s['total']} contributions, "
          f"streak {s['current_streak']} (max {s['longest_streak']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

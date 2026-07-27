"""Scrape the public contribution calendar and render it as an animated SVG.

No API token needed: GitHub serves the calendar as public HTML at
https://github.com/users/<user>/contributions - the same fragment the profile uses.

Two gotchas that cost time if you follow the usual write-ups:
  * The <td> day cells are EMPTY. The per-day count lives in a separate <tool-tip>
    element, joined to the cell via tool-tip[for] -> td[id].
  * The "N contributions in the last year" summary is not in this fragment at all,
    so the total has to be summed from the parsed days.

Usage:  python update_heatmap.py [--no-fetch]
        --no-fetch  re-render from data/contributions.json without hitting GitHub
"""

import json
import os
import re
import sys
from datetime import date, timedelta

USER = "Tarek-9"
URL = f"https://github.com/users/{USER}/contributions"
DATA = os.path.join("data", "contributions.json")
OUT = "contrib-heatmap.svg"

# GitHub only ever emits levels 0-4; a 6th "neon" entry would never be used.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

WIDTH = 860  # matches the donut (378) + info card (482) sitting side by side
PAD = 16
LABEL_W = 32
BOX, GAP = 12, 3
PITCH = BOX + GAP
MONTH_H = 18
FOOT_H = 34
WEEKS, DAYS = 53, 7
BG, BORDER, FG, DIM = "#0d1117", "#30363d", "#c9d1d9", "#8b949e"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
REVEAL_STEP = 0.012  # seconds of extra delay per diagonal step
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

COUNT_RE = re.compile(r"^(No|[\d,]+)\s+contributions?", re.I)
ID_RE = re.compile(r"contribution-day-component-(\d+)-(\d+)$")


def fetch():
    import requests
    from bs4 import BeautifulSoup

    html = requests.get(URL, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (profile-readme heatmap generator)",
        "X-Requested-With": "XMLHttpRequest",
    })
    html.raise_for_status()
    soup = BeautifulSoup(html.text, "html.parser")

    # the count lives in the tooltip, not the cell
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        cell_id, day = td.get("id"), td.get("data-date")
        if not cell_id or not day:
            continue
        m = ID_RE.search(cell_id)
        if not m:
            continue
        row, week = int(m.group(1)), int(m.group(2))

        count = 0
        tip = tips.get(cell_id)
        if tip:
            cm = COUNT_RE.match(tip)
            if cm:
                raw = cm.group(1)
                count = 0 if raw.lower() == "no" else int(raw.replace(",", ""))
        days.append({
            "date": day,
            "count": count,
            "level": int(td.get("data-level", 0)),
            "week": week,
            "row": row,
        })

    assert days, "no day cells parsed - GitHub changed the markup"
    assert all(0 <= d["row"] < DAYS for d in days), "unexpected weekday index"
    return days


def streaks(days):
    """Current and longest run of consecutive days with at least one contribution."""
    ordered = sorted(days, key=lambda d: d["date"])
    longest = run = 0
    for d in ordered:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # today counting zero does not break a streak yet - the day is not over
    tail = ordered[:]
    if tail and tail[-1]["date"] == date.today().isoformat() and tail[-1]["count"] == 0:
        tail.pop()
    current = 0
    for d in reversed(tail):
        if d["count"] == 0:
            break
        current += 1
    return current, longest


def build(days):
    best = max(days, key=lambda d: d["count"])
    current, longest = streaks(days)
    return {
        "user": USER,
        "generated": date.today().isoformat(),
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "days": days,
    }


MIN_LABEL_GAP = 3  # weeks; a label is ~3 cells wide, closer than that and they collide


def month_labels(days):
    """One label per month, placed at the first week that month appears in."""
    seen, out = set(), []
    last_week = -MIN_LABEL_GAP
    for d in sorted(days, key=lambda d: d["date"]):
        y, m, _ = d["date"].split("-")
        key = (y, m)
        if key in seen:
            continue
        seen.add(key)
        if d["week"] >= WEEKS - 1:  # crammed against the right edge
            continue
        label = (d["week"], MONTHS[int(m) - 1])
        if out and d["week"] - last_week < MIN_LABEL_GAP:
            # The year starts mid-month, so the first label collides with the next one.
            # Keep the later month - it's the one that actually owns those columns.
            out[-1] = label
        else:
            out.append(label)
        last_week = d["week"]
    return out


def render(payload, static=False):
    days = payload["days"]
    grid_h = DAYS * PITCH - GAP
    height = PAD + MONTH_H + grid_h + FOOT_H + PAD
    gx, gy = PAD + LABEL_W, PAD + MONTH_H

    cells = []
    for d in days:
        x = gx + d["week"] * PITCH
        y = gy + d["row"] * PITCH
        delay = (d["week"] + d["row"]) * REVEAL_STEP
        anim = "" if static else f' class="c" style="animation-delay:{delay:.2f}s"'
        cells.append(
            f'<rect{anim} x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2" '
            f'fill="{PALETTE[d["level"]]}"/>'
        )

    months = "".join(
        f'<text x="{gx + w * PITCH}" y="{PAD + 12}" fill="{DIM}" font-size="11">{name}</text>'
        for w, name in month_labels(days)
    )
    weekdays = "".join(
        f'<text x="{PAD}" y="{gy + r * PITCH + BOX - 2}" fill="{DIM}" font-size="10">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    fy = gy + grid_h + 22
    legend_x = WIDTH - PAD - 5 * PITCH - 68
    legend = (
        f'<text x="{legend_x}" y="{fy}" fill="{DIM}" font-size="11">Less</text>'
        + "".join(
            f'<rect x="{legend_x + 30 + i * PITCH}" y="{fy - 9}" width="{BOX}" '
            f'height="{BOX}" rx="2" fill="{c}"/>'
            for i, c in enumerate(PALETTE)
        )
        + f'<text x="{legend_x + 34 + 5 * PITCH}" y="{fy}" fill="{DIM}" '
          f'font-size="11">More</text>'
    )
    summary = (
        f'<text x="{PAD}" y="{fy}" fill="{FG}" font-size="12">'
        f'{payload["total"]:,} contributions in the last year'
        f'<tspan fill="{DIM}">   ·   streak {payload["current_streak"]}d '
        f'(best {payload["longest_streak"]}d)   ·   peak '
        f'{payload["best_day"]["count"]} on {payload["best_day"]["date"]}</tspan></text>'
    )

    # `both` (not `forwards`) and no base opacity:0 - the reveal is an enhancement, so a
    # renderer that ignores CSS animation shows the grid instead of a blank panel.
    style = "" if static else (
        "<style>"
        "@keyframes pop{from{opacity:0}to{opacity:1}}"
        ".c{animation:pop .35s ease-out both}"
        "</style>"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}" font-family="{FONT}">'
        f"{style}"
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}"/>'
        f"{months}{weekdays}{''.join(cells)}{summary}{legend}</svg>"
    )


def main():
    if "--no-fetch" in sys.argv:
        with open(DATA, encoding="utf-8") as f:
            payload = json.load(f)
        print(f"reusing {DATA} ({len(payload['days'])} days)")
    else:
        payload = build(fetch())
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        with open(DATA, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1)

    svg = render(payload, static=os.environ.get("STATIC") == "1")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)

    levels = {}
    for d in payload["days"]:
        levels[d["level"]] = levels.get(d["level"], 0) + 1
    print(f"{OUT}: {len(svg) / 1024:.0f} KB · {len(payload['days'])} days · "
          f"{payload['total']} contributions · streak {payload['current_streak']}d "
          f"(best {payload['longest_streak']}d)")
    print(f"levels: {dict(sorted(levels.items()))}")


if __name__ == "__main__":
    main()

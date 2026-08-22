#!/usr/bin/env python3
"""
render_heatmap_svg.py
Reads data/contributions.json and draws the classic 53-week x 7-day grid as
rounded boxes, revealed once with a diagonal line-after-line slide-down
(pure CSS keyframes inside the <svg>, no JS, GitHub-safe).
"""
import json
import os
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG = "#0d1117"
FG = "#8b949e"
ACCENT = "#39d353"
TEXT = "#c9d1d9"

BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 30
TOP_PAD = 64
MONTH_LABEL_H = 16
STATIC = os.environ.get("STATIC") == "1"


def level_for(count: int) -> int:
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    if count <= 14:
        return 4
    return 5


def build_weeks(days):
    # days sorted ascending by date, first entry may not be a Sunday.
    weeks = []
    current_week = []
    for d in days:
        dow = datetime.strptime(d["date"], "%Y-%m-%d").weekday()  # Mon=0..Sun=6
        gh_dow = (dow + 1) % 7  # Sun=0..Sat=6, matches GitHub's grid
        if gh_dow == 0 and current_week:
            weeks.append(current_week)
            current_week = []
        current_week.append((d, gh_dow))
    if current_week:
        weeks.append(current_week)
    return weeks


def month_labels(weeks):
    labels = []
    last_month = None
    for wi, week in enumerate(weeks):
        first_day = week[0][0]
        month = first_day["date"][:7]
        month_num = int(month[5:7])
        if month_num != last_month:
            month_name = datetime.strptime(month, "%Y-%m").strftime("%b")
            labels.append((wi, month_name))
            last_month = month_num
    return labels


def main():
    with open(DATA_PATH) as f:
        data = json.load(f)

    days = data["days"]
    stats = data["stats"]
    username = data["username"]
    total = data.get("total_from_page") or stats["total_computed"]

    weeks = build_weeks(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * CELL + 20
    height = TOP_PAD + 7 * CELL + 46

    svg_parts = []
    svg_parts.append(
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )

    cell_anim = "" if STATIC else '''
      opacity: 0;
      transform-box: fill-box;
      transform-origin: center;
      animation: reveal 0.5s ease-out forwards;
'''
    keyframes = "" if STATIC else '''
    @keyframes reveal {
      0%   { opacity: 0; transform: translateY(-6px) scale(0.6); }
      100% { opacity: 1; transform: translateY(0) scale(1); }
    }
'''
    svg_parts.append(f'''
  <style>
    .bg {{ fill: {BG}; }}
    .hdr {{ fill: {TEXT}; font-size: 13px; font-weight: 600; }}
    .sub {{ fill: {FG}; font-size: 11px; }}
    .mo  {{ fill: {FG}; font-size: 10px; }}
    .cell {{
      rx: 2px;
      {cell_anim}
    }}
    {keyframes}
  </style>
''')

    svg_parts.append(f'<rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10"/>')
    svg_parts.append(
        f'<text x="{LEFT_PAD}" y="20" class="hdr">{username} · contribution activity</text>'
    )
    svg_parts.append(
        f'<text x="{LEFT_PAD}" y="36" class="sub">'
        f'{total} contributions in the last year &#183; '
        f'longest streak {stats["longest_streak"]}d &#183; '
        f'best day {stats["best_day"]["count"] if stats["best_day"] else 0}</text>'
    )

    for wi, label in month_labels(weeks):
        x = LEFT_PAD + wi * CELL
        svg_parts.append(f'<text x="{x}" y="{TOP_PAD - 6}" class="mo">{label}</text>')

    max_delay = 0.0
    for wi, week in enumerate(weeks):
        for day, gh_dow in week:
            x = LEFT_PAD + wi * CELL
            y = TOP_PAD + gh_dow * CELL
            level = day["level"] if "level" in day else level_for(day["count"])
            color = PALETTE[min(level, 5)]
            # diagonal stagger: weeks move right, days move down -> combine
            delay = (wi * 0.012) + (gh_dow * 0.03)
            max_delay = max(max_delay, delay)
            title = f'{day["count"]} contributions on {day["date"]}'
            style_attr = "" if STATIC else f' style="animation-delay:{delay:.3f}s"'
            svg_parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{BOX}" height="{BOX}" '
                f'fill="{color}"{style_attr}>'
                f'<title>{title}</title></rect>'
            )

    legend_y = height - 22
    legend_x = LEFT_PAD
    svg_parts.append(f'<text x="{legend_x}" y="{legend_y + 9}" class="mo">Less</text>')
    lx = legend_x + 34
    for i, color in enumerate(PALETTE):
        svg_parts.append(
            f'<rect x="{lx + i * (BOX + 3)}" y="{legend_y}" width="{BOX}" height="{BOX}" '
            f'rx="2" fill="{color}"/>'
        )
    svg_parts.append(
        f'<text x="{lx + len(PALETTE) * (BOX + 3) + 6}" y="{legend_y + 9}" class="mo">More</text>'
    )

    svg_parts.append("</svg>")

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(svg_parts))

    print(f"Wrote {OUT_PATH} ({width}x{height}, {n_weeks} weeks, max reveal delay {max_delay:.2f}s)")


if __name__ == "__main__":
    main()

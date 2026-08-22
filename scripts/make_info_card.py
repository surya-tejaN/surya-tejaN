#!/usr/bin/env python3
"""
make_info_card.py
Hand-authors a neofetch-style SVG panel: title bar + colored key/value rows.
Each line fades + slides in on a short stagger (CSS keyframes, GitHub-safe).
Set STATIC=1 to emit a frozen (no-animation) frame for local Quick Look previews.
"""
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

BG = "#0d1117"
BORDER = "#30363d"
TITLE_BAR = "#161b22"
KEY_COLOR = "#39d353"
VAL_COLOR = "#c9d1d9"
DIM = "#8b949e"

WIDTH = 490
ROW_H = 24
PAD_X = 22
TITLE_H = 30

# ---- content: role, stack, highlights ----
ROWS = [
    ("os", "surya-tejaN@github"),
    ("role", "SWE + AI Intern @ Cyclical Inc (KNOWN)"),
    ("also", "MS Computer Science @ DePaul University"),
    ("stack", "TypeScript / React / Swift / Python / Supabase"),
    ("shipped", "Google Sign-In prod fix, tips/rituals swipe UI,"),
    ("", "AI PII-scrubbing pipeline for gemini-proxy"),
    ("founded", "Legalhubly -- solo-built legal marketplace"),
    ("bias", "ship fast, iterate in prod"),
]

HEIGHT = TITLE_H + len(ROWS) * ROW_H + 26


def esc(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def main():
    parts = []
    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {HEIGHT}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    )

    anim_css = "" if STATIC else '''
    .line {
      opacity: 0;
      transform: translateX(-6px);
      transform-box: fill-box;
      animation: type-in 0.35s ease-out forwards;
    }
    @keyframes type-in {
      0%   { opacity: 0; transform: translateX(-6px); }
      100% { opacity: 1; transform: translateX(0); }
    }
'''
    parts.append(f'''
  <style>
    .card {{ fill: {BG}; stroke: {BORDER}; stroke-width: 1; }}
    .titlebar {{ fill: {TITLE_BAR}; }}
    .dot {{ }}
    .k {{ fill: {KEY_COLOR}; font-size: 12.5px; font-weight: 600; }}
    .v {{ fill: {VAL_COLOR}; font-size: 12.5px; }}
    .path {{ fill: {DIM}; font-size: 11.5px; }}
    {anim_css}
  </style>
''')

    parts.append(f'<rect class="card" x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8"/>')
    parts.append(f'<path class="titlebar" d="M0.5,8 a8,8 0 0 1 8,-7.5 h{WIDTH - 17} a8,8 0 0 1 8,7.5 v{TITLE_H - 8} h-{WIDTH - 1} z"/>')
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{18 + i * 16}" cy="{TITLE_H / 2}" r="5" fill="{color}"/>')
    parts.append(f'<text x="{WIDTH / 2}" y="{TITLE_H / 2 + 4}" text-anchor="middle" class="path">neofetch</text>')

    y = TITLE_H + 24
    delay = 0.15
    for key, val in ROWS:
        cls = "line" if not STATIC else ""
        style = f'style="animation-delay:{delay:.2f}s"' if not STATIC else ""
        if key:
            parts.append(
                f'<text x="{PAD_X}" y="{y}" class="{cls}" {style}>'
                f'<tspan class="k">{esc(key)}</tspan>'
                f'<tspan class="v" dx="6">{esc(val)}</tspan></text>'
            )
        else:
            parts.append(
                f'<text x="{PAD_X + 58}" y="{y}" class="{cls} v" {style}>{esc(val)}</text>'
            )
        y += ROW_H
        delay += 0.09

    parts.append("</svg>")

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(parts))
    print(f"Wrote {OUT_PATH} ({WIDTH}x{HEIGHT}, static={STATIC})")


if __name__ == "__main__":
    main()

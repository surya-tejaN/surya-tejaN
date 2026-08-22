#!/usr/bin/env python3
"""
make_ascii_svg.py [source-prepped.png]
Downsamples the prepped grayscale image to a character grid and maps each
pixel's brightness to a glyph from a density ramp. Monochrome, single fill
color -- per-character rainbow coloring is what makes ASCII art look noisy.

Each row is wrapped in a clip-path that wipes left-to-right (SMIL <animate>),
staggered top to bottom. Prints once and freezes -- no looping.

If no source-prepped.png exists yet (no photo has been run through
prep_photo.py), falls back to a procedurally generated placeholder banner so
the pipeline still produces a working preview end to end.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "avi-ascii.svg")
STATIC = os.environ.get("STATIC") == "1"

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space clears bg
COLS = 70
ROWS = 40
FONT_SIZE = 9
CHAR_W = 5.6
CHAR_H = 10.5
FILL = "#8b949e"
BG = "#0d1117"


def make_placeholder_image(path, size=(700, 400)):
    """No real photo supplied -- generate a simple monogram silhouette so the
    pipeline still runs end to end. Swap in a real photo + prep_photo.py for
    the actual portrait version."""
    img = Image.new("L", size, color=255)
    draw = ImageDraw.Draw(img)
    text = "ST"
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 260
        )
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size[0] - tw) / 2 - bbox[0], (size[1] - th) / 2 - bbox[1]),
        text,
        fill=30,
        font=font,
    )
    img.save(path)
    return path


def pixel_to_glyph(brightness):
    idx = int((1 - brightness / 255) * (len(RAMP) - 1))
    idx = max(0, min(len(RAMP) - 1, idx))
    return RAMP[idx]


def image_to_grid(img_path, cols=COLS, rows=ROWS):
    img = Image.open(img_path).convert("L")
    img = img.resize((cols, rows))
    pixels = list(img.getdata())
    grid = []
    for r in range(rows):
        row = [pixels[r * cols + c] for c in range(cols)]
        grid.append([pixel_to_glyph(p) for p in row])
    return grid


def esc(ch):
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;"}.get(ch, ch)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if not src:
        default_prepped = os.path.join(os.path.dirname(__file__), "..", "source-prepped.png")
        if os.path.exists(default_prepped):
            src = default_prepped
        else:
            placeholder_path = os.path.join(os.path.dirname(__file__), "..", "_placeholder.png")
            src = make_placeholder_image(placeholder_path)
            print(f"No source-prepped.png found -- using generated placeholder ({src}). "
                  f"Run prep_photo.py on a real photo for the actual portrait.")

    grid = image_to_grid(src)

    width = COLS * CHAR_W + 20
    height = ROWS * CHAR_H + 20

    parts = [
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
    ]
    parts.append(f'<rect x="0" y="0" width="{width:.0f}" height="{height:.0f}" fill="{BG}" rx="10"/>')
    parts.append(f'<style>text {{ font-size:{FONT_SIZE}px; fill:{FILL}; white-space:pre; }}</style>')

    row_delay_step = 0.045
    wipe_dur = 0.5

    for r, row in enumerate(grid):
        line = "".join(esc(ch) for ch in row)
        y = 16 + r * CHAR_H
        clip_id = f"clip{r}"
        delay = r * row_delay_step
        start_w = width if STATIC else 0

        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(f'  <rect x="0" y="{y - CHAR_H + 2:.1f}" width="{start_w:.0f}" height="{CHAR_H:.0f}">')
        if not STATIC:
            parts.append(
                f'    <animate attributeName="width" from="0" to="{width:.0f}" '
                f'begin="{delay:.3f}s" dur="{wipe_dur}s" fill="freeze" calcMode="spline" '
                f'keySplines="0.25 0.1 0.25 1"/>'
            )
        parts.append("  </rect>")
        parts.append("</clipPath>")

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(f'  <text x="10" y="{y:.1f}" xml:space="preserve">{line}</text>')
        parts.append("</g>")

    parts.append("</svg>")

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(parts))
    print(f"Wrote {OUT_PATH} ({width:.0f}x{height:.0f}, {ROWS} rows)")


if __name__ == "__main__":
    main()

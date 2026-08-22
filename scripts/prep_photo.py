#!/usr/bin/env python3
"""
prep_photo.py <source-photo.jpg>
Run this once, locally, per photo (needs rembg + opencv -- not part of the
daily Actions workflow). Produces source-prepped.png:
  1. rembg strips the background so only the subject remains.
  2. OpenCV CLAHE boosts local contrast (fixes flatly-lit faces going muddy).
  3. Composited onto pure white so background maps to the blank end of the
     ASCII ramp (white -> space).
"""
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def main():
    if len(sys.argv) != 2:
        print("usage: python prep_photo.py <source-photo.jpg>")
        sys.exit(1)

    src_path = sys.argv[1]
    print(f"Removing background from {src_path} ...")
    with open(src_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)

    rgba = Image.open(__import__("io").BytesIO(output_bytes)).convert("RGBA")

    # Composite onto pure white
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba).convert("RGB")

    # CLAHE for local contrast (operates on the L channel in LAB space)
    arr = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(arr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge((l2, a, b))
    boosted = cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)
    gray = cv2.cvtColor(boosted, cv2.COLOR_BGR2GRAY)

    out_path = "source-prepped.png"
    cv2.imwrite(out_path, gray)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

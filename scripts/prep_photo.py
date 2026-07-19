#!/usr/bin/env python3
"""Prep a portrait for ASCII conversion.

A flatly-lit face converts to a dark, unreadable blob. This normalises it:
  1. grayscale
  2. local-ish contrast boost (autocontrast + equalize) so a flat face gets
     real highlights and shadows (a lightweight stand-in for OpenCV CLAHE)
  3. lift the highlights so the light background maps to pure white -> the
     blank end of the ASCII ramp (white -> spaces), leaving only the subject.

Pillow only, so there are no heavy native deps. If your source has a busy
background, crop it to the face first (or drop in rembg) before running this.

    python scripts/prep_photo.py source-photo.jpg [--out source-prepped.png]
"""
from __future__ import annotations

import argparse
from PIL import Image, ImageOps


def prep(src: str, out: str) -> None:
    img = Image.open(src).convert("L")

    # Stretch the tonal range, trimming a little off each end so a stray
    # bright/dark pixel doesn't flatten everything else. (No histogram
    # equalisation — it lifts the light background into mid-gray, which then
    # prints as a wall of glyphs instead of blank space.)
    img = ImageOps.autocontrast(img, cutoff=2)

    # Knockout curve: clip the light background to pure white (-> spaces) while
    # keeping the subject's tones. Everything at/above WHITE becomes 255, at/below
    # BLACK becomes 0, and the middle is stretched with a mild gamma for detail.
    black, white = 20, 165
    lut = []
    for v in range(256):
        if v <= black:
            lut.append(0)
        elif v >= white:
            lut.append(255)
        else:
            t = (v - black) / (white - black)
            lut.append(int((t ** 0.85) * 255))
    img = img.point(lut)

    img.save(out)
    print(f"wrote {out} ({img.width}x{img.height})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default="source-prepped.png")
    a = ap.parse_args()
    prep(a.src, a.out)

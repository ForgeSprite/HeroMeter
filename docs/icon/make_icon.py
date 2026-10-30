"""Builds src/icon.ico (16-256 px) and docs/icon/icon-256.png from hero-medallion.svg.
Small sizes drop the sparkle, soften the gloss and thicken the bar outlines so they stay crisp.
Needs:  pip install resvg-py pillow"""
import io
import os

import resvg_py
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "hero-medallion.svg"), encoding="utf-8").read()
SMALL = (SRC.replace('<path id="sparkle"', '<path id="sparkle" visibility="hidden"')
            .replace('id="gloss-shape"', 'id="gloss-shape" opacity=".5"')
            .replace('stroke-width="5" stroke-linejoin="round" id="bars"',
                     'stroke-width="8" stroke-linejoin="round" id="bars"'))


def render(svg, size):
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=size, height=size))
    return Image.open(io.BytesIO(png)).convert("RGBA")


sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
imgs = [render(SMALL if s <= 32 else SRC, s) for s in sizes]
out = os.path.join(HERE, "..", "..", "src", "icon.ico")
imgs[-1].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=imgs[:-1])
imgs[-1].save(os.path.join(HERE, "icon-256.png"))
print("wrote", os.path.abspath(out), [i.size for i in imgs])

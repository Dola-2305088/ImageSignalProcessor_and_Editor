"""Colour language shared by the Discover lessons.

Roles never change colour, so the eye can follow the story:

    input values   -> cyan
    kernel weights -> amber (positive: cyan tint, negative: rose tint)
    products / sum -> pink
    output values  -> the same brightness map as the input

Pixel brightness (0..255) is drawn with a "space" colour map instead of
flat grey. The number on every tile is still the true brightness; the
map only makes the picture match the AETHERIS theme.
"""

from io import BytesIO

import numpy as np
from PIL import Image


INPUT = "#22D3EE"
INPUT_SOFT = "#67E8F9"
KERNEL = "#FBBF24"
KERNEL_FRAME = "#A78BFA"
PRODUCT = "#F472B6"
OUTPUT = "#F472B6"
POSITIVE = "#22D3EE"
NEGATIVE = "#FB7185"

# brightness 0..1 -> RGB
_STOPS = [
    (0.00, (6, 10, 22)),
    (0.35, (30, 42, 90)),
    (0.62, (109, 91, 208)),
    (0.85, (165, 232, 245)),
    (1.00, (255, 255, 255)),
]


def _build_lut():
    lut = np.zeros((256, 3), dtype=np.uint8)
    for value in range(256):
        t = value / 255.0
        for (p0, c0), (p1, c1) in zip(_STOPS, _STOPS[1:]):
            if p0 <= t <= p1:
                f = (t - p0) / (p1 - p0)
                lut[value] = [round(a + (b - a) * f) for a, b in zip(c0, c1)]
                break
    return lut


LUT = _build_lut()

_HEX = ["#{:02X}{:02X}{:02X}".format(*LUT[v]) for v in range(256)]
_TEXT = [
    "#0B1020"
    if (0.2126 * LUT[v][0] + 0.7152 * LUT[v][1] + 0.0722 * LUT[v][2]) > 150
    else "#EEF2FF"
    for v in range(256)
]


def _clamp(value):
    return int(min(255, max(0, round(float(value)))))


def pixel_color(value):
    """Tile colour for a brightness value."""
    return _HEX[_clamp(value)]


def pixel_text_color(value):
    """Readable number colour on top of pixel_color(value)."""
    return _TEXT[_clamp(value)]


def argb(alpha_hex, color):
    """Flet hex colours are #AARRGGBB; prepend an alpha to #RRGGBB."""
    return "#" + alpha_hex + color.lstrip("#")


def weight_color(weight, max_abs):
    """Cell tint for a kernel weight: hue from sign, strength from size."""
    if max_abs <= 0 or abs(weight) < 1e-12:
        return "#FF0B1120"

    strength = min(1.0, abs(weight) / max_abs)
    alpha = "{:02X}".format(int(0x26 + strength * (0xB8 - 0x26)))
    return argb(alpha, POSITIVE if weight > 0 else NEGATIVE)


def colorize(image):
    """uint8 grayscale array -> RGB array through the space colour map."""
    image = np.clip(np.asarray(image), 0, 255).astype(np.uint8)
    return LUT[image]


def png_bytes(image, scale=1):
    """Colour-mapped PNG bytes; scale > 1 enlarges with crisp pixels."""
    rgb = colorize(image)
    if scale > 1:
        rgb = np.repeat(np.repeat(rgb, scale, axis=0), scale, axis=1)

    buffer = BytesIO()
    Image.fromarray(rgb).save(buffer, format="PNG")
    return buffer.getvalue()


def legend_colors(steps=8):
    """Evenly spaced map colours, for the brightness legend gradient."""
    return [pixel_color(round(i * 255 / (steps - 1))) for i in range(steps)]


# ============================================================
# NUMBER FORMATTING
# ============================================================

def fmt_weight(weight):
    """Short, honest kernel-weight label that fits a small cell."""
    weight = float(weight)
    if abs(weight - round(weight)) < 1e-9:
        return str(int(round(weight)))
    if abs(weight) < 0.01:
        return f"{weight:.3f}".replace("0.", ".", 1)
    return f"{weight:.2f}".rstrip("0").rstrip(".")


def fmt_product(value):
    value = float(value)
    if abs(value) >= 100:
        return f"{value:.0f}"
    return f"{value:.1f}"


def fmt_sum(value):
    return f"{float(value):.1f}"

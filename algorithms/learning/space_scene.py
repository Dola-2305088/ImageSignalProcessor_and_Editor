"""Procedurally generated space scene used by the Discover lessons.

The lesson needs one fixed image that is:

* small enough that every pixel can be drawn as a numbered tile,
* space themed, to match the AETHERIS interface,
* rich in both sharp edges (planet limb, ring, stars) and smooth
  gradients (the shaded planet), so blur, sharpen and edge kernels all
  produce a visible, explainable change.

It is drawn in code rather than loaded from disk, so it is identical on
every run and needs no asset file.

Two versions come from the same drawing:

    render_space_scene(96)  -> the detailed "reveal" image
    lesson_grid()           -> the 16 x 16 lesson grid, made by averaging
                               each 6 x 6 block of the 96 x 96 scene

So the lesson grid is honestly *the same picture at lower resolution*,
which is exactly what the lesson tells the viewer.
"""

from functools import lru_cache

import numpy as np


LESSON_SIZE = 16
REVEAL_SIZE = 96


def _scene_intensity(x, y):
    """Scene brightness (0..1) at normalised coordinates in [0, 1]."""

    # ---------------------------------------------------------
    # Background: deep space with a faint diagonal nebula glow.
    # ---------------------------------------------------------
    nebula = 0.10 * np.exp(-(((x - 0.15) + (y - 0.85)) ** 2) / 0.10)
    value = 0.03 + nebula

    # ---------------------------------------------------------
    # Planet: lit from the upper left, so one side is bright and
    # the far side falls into shadow (a smooth gradient).
    # ---------------------------------------------------------
    cx, cy, radius = 0.56, 0.54, 0.29
    dx, dy = x - cx, y - cy
    distance = np.sqrt(dx * dx + dy * dy)
    inside = distance <= radius

    light_x, light_y = -0.72, -0.69
    nz = np.sqrt(np.clip(1.0 - (distance / radius) ** 2, 0.0, 1.0))
    shade = (dx / radius) * light_x + (dy / radius) * light_y + nz * 0.35
    # The night side stays well above the background so the disc keeps a
    # clear outline even after averaging down to the lesson grid.
    planet = np.clip(0.38 + 0.62 * shade, 0.34, 1.0)

    # Soft cloud bands across the planet surface.
    bands = 0.07 * np.sin((dy / radius) * 9.0 + (dx / radius) * 1.5)
    planet = np.clip(planet + bands * inside, 0.0, 1.0)

    value = np.where(inside, planet, value)

    # ---------------------------------------------------------
    # Ring: a tilted ellipse. The part behind the planet is hidden.
    # ---------------------------------------------------------
    angle = -0.35
    rx = dx * np.cos(angle) - dy * np.sin(angle)
    ry = dx * np.sin(angle) + dy * np.cos(angle)
    ring_r = np.sqrt((rx / 0.47) ** 2 + (ry / 0.12) ** 2)
    on_ring = np.abs(ring_r - 1.0) < 0.16
    ring_in_front = ry > 0
    ring_visible = on_ring & (ring_in_front | ~inside)
    value = np.where(ring_visible, np.maximum(value, 0.86), value)

    # ---------------------------------------------------------
    # Stars: small bright discs, sized so they survive the
    # 8 x 8 averaging down to the lesson grid.
    # ---------------------------------------------------------
    stars = [
        (0.12, 0.13, 0.055, 1.00),
        (0.86, 0.13, 0.045, 0.90),
        (0.13, 0.80, 0.040, 0.80),
        (0.88, 0.88, 0.050, 0.95),
    ]
    for sx, sy, sr, brightness in stars:
        star = np.exp(-((x - sx) ** 2 + (y - sy) ** 2) / (2 * sr * sr))
        value = np.maximum(value, brightness * star * (~inside))

    return np.clip(value, 0.0, 1.0)


@lru_cache(maxsize=4)
def render_space_scene(size=REVEAL_SIZE, supersample=4):
    """Render the scene as a size x size uint8 grayscale image.

    Each pixel averages supersample x supersample sub-samples, so edges
    are anti-aliased instead of jagged.
    """
    n = size * supersample
    coords = (np.arange(n) + 0.5) / n
    x, y = np.meshgrid(coords, coords)

    fine = _scene_intensity(x, y)
    image = fine.reshape(size, supersample, size, supersample).mean(axis=(1, 3))

    result = np.round(image * 255).astype(np.uint8)
    result.setflags(write=False)
    return result


@lru_cache(maxsize=4)
def lesson_grid(size=LESSON_SIZE, source_size=REVEAL_SIZE):
    """The small lesson image: block-average of the reveal image."""
    if source_size % size != 0:
        raise ValueError("source_size must be a multiple of size")

    block = source_size // size
    scene = render_space_scene(source_size).astype(np.float64)
    small = scene.reshape(size, block, size, block).mean(axis=(1, 3))

    result = np.round(small).astype(np.uint8)
    result.setflags(write=False)
    return result

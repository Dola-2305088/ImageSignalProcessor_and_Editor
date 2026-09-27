"""Procedural space scene for SaveEarth.

Every challenge starts from this clean image. It is generated with NumPy
(no asset file needed) and is deterministic for a given seed, so the same
seed always rebuilds the same game.

The scene deliberately contains:
  * a shaded planet with a sharp limb   -> strong curved edges
  * a thin tilted ring                  -> diagonal structure
  * a small moon                        -> a second object with edges
  * point-like stars                    -> fine detail that blur destroys
"""

from __future__ import annotations

import numpy as np

DEFAULT_SIZE = 128


def make_space_scene(size: int = DEFAULT_SIZE, seed: int = 0) -> np.ndarray:
    """Return a (size, size) uint8 grayscale space scene."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size].astype(np.float64)
    s = size / 128.0  # scale factor so the layout works at any size

    # Dark background with a faint diagonal nebula glow.
    img = 12.0 + 22.0 * np.exp(-(((x - 0.25 * size) + (y - 0.2 * size)) ** 2) / (2 * (30 * s) ** 2))

    # Stars: a few dozen single bright pixels plus a handful of 2x2 bright stars.
    n_small = int(55 * s * s)
    sx = rng.integers(0, size, n_small)
    sy = rng.integers(0, size, n_small)
    img[sy, sx] = rng.uniform(120, 230, n_small)
    for _ in range(int(6 * s * s)):
        cx, cy = rng.integers(2, size - 3, 2)
        img[cy:cy + 2, cx:cx + 2] = 245.0

    # Planet: disk with limb shading, lit from the upper left.
    pcx, pcy, pr = 0.58 * size, 0.60 * size, 30 * s
    d = np.sqrt((x - pcx) ** 2 + (y - pcy) ** 2)
    planet = d <= pr
    light = np.clip(1.0 - ((x - (pcx - 0.4 * pr)) ** 2 + (y - (pcy - 0.4 * pr)) ** 2) / (2.2 * pr) ** 2, 0, 1)
    bands = 12.0 * np.sin((y - pcy) / (4.0 * s))  # horizontal cloud bands
    img[planet] = (70.0 + 150.0 * light + bands)[planet]

    # Ring: thin tilted ellipse, hidden where it passes behind the planet.
    angle = np.deg2rad(-18)
    rx = (x - pcx) * np.cos(angle) + (y - pcy) * np.sin(angle)
    ry = -(x - pcx) * np.sin(angle) + (y - pcy) * np.cos(angle)
    ring_r = np.sqrt((rx / (48 * s)) ** 2 + (ry / (11 * s)) ** 2)
    ring = (np.abs(ring_r - 1.0) < 0.07) & ~(planet & (ry < 0))
    img[ring] = 200.0

    # Moon: small bright disk in the upper right.
    moon = np.sqrt((x - 0.84 * size) ** 2 + (y - 0.2 * size) ** 2) <= 7 * s
    img[moon] = 185.0

    return np.clip(np.rint(img), 0, 255).astype(np.uint8)

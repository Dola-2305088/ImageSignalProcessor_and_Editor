"""Backends for the texture and colour lessons.

TextureTrace makes patterns whose spacing and angle are known exactly,
so the project's ``analyze_texture`` can be checked against the truth
rather than trusted. That is also what makes the lesson teachable: when
the answer is known in advance, the spectrum stops being mysterious.

ColourTrace splits a picture into brightness and colour and then
damages each separately, which is the experiment behind chroma
subsampling. The project has ``rgb_to_ycbcr`` but no way back, so the
inverse lives here (Shreya may want to move it into
``color_analysis.py`` — it is the exact inverse of the matrix there).
"""

import numpy as np

from algorithms.frequency.color_analysis import rgb_to_ycbcr, split_rgb_channels
from algorithms.frequency.texture import analyze_texture
from algorithms.learning.space_scene import render_space_scene
from algorithms.learning.spectrum_trace import spectrum_picture
from ui.learning.palette import LUT
from utils.metrics import calculate_psnr


# ============================================================
# TEXTURE
# ============================================================

def weave(size=128, spacing=8, angle=0.0):
    """Cloth: two sets of threads crossing at right angles."""
    y, x = np.mgrid[0:size, 0:size]
    radians = np.deg2rad(angle)

    along = x * np.cos(radians) + y * np.sin(radians)
    across = -x * np.sin(radians) + y * np.cos(radians)

    threads = (
        0.5 * np.sin(2 * np.pi * along / spacing)
        + 0.5 * np.sin(2 * np.pi * across / spacing)
    )
    return np.clip(np.round(128 + 95 * threads), 0, 255).astype(np.uint8)


def bricks(size=128, spacing=16, angle=0.0):
    """Brick: strong horizontal courses, weaker vertical joins."""
    y, x = np.mgrid[0:size, 0:size]
    radians = np.deg2rad(angle)

    along = x * np.cos(radians) + y * np.sin(radians)
    across = -x * np.sin(radians) + y * np.cos(radians)

    courses = np.sin(2 * np.pi * across / spacing)
    stagger = np.sin(2 * np.pi * (along / (spacing * 2)
                                  + 0.5 * np.floor(across / spacing)))

    return np.clip(
        np.round(140 + 80 * courses + 28 * stagger), 0, 255
    ).astype(np.uint8)


def grass(size=128, spacing=6, angle=0.0, seed=3):
    """Grass: one strong direction, but irregular, like real texture."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]
    radians = np.deg2rad(angle)

    across = -x * np.sin(radians) + y * np.cos(radians)

    blades = np.sin(2 * np.pi * across / spacing)
    jitter = rng.normal(0, 0.35, size=(size, size))

    return np.clip(np.round(120 + 70 * blades + 30 * jitter), 0, 255).astype(np.uint8)


TEXTURES = {
    "Cloth": (weave, 8),
    "Brick": (bricks, 16),
    "Grass": (grass, 6),
}


class TextureTrace:
    """Patterns with known spacing and angle, measured by the app."""

    def __init__(self, size=128):
        self.size = size

    def make(self, kind="Cloth", spacing=None, angle=0.0):
        builder, default_spacing = TEXTURES[kind]
        spacing = default_spacing if spacing is None else spacing

        image = builder(self.size, spacing, angle)

        return {
            "kind": kind,
            "image": image,
            "spectrum": spectrum_picture(np.fft.fft2(image.astype(np.float64))),
            "true_spacing": float(spacing),
            "true_angle": float(angle),
        }

    def measure(self, image):
        """What the project's analyzer says about a texture."""
        result = analyze_texture(np.asarray(image))

        return {
            "spacing": float(result.get("spacing_pixels", 0.0)),
            "angle": float(result.get("texture_angle", 0.0)),
            "orientation": result.get("orientation", "—"),
            "strength": float(result.get("periodicity_strength", 0.0)),
            "peak": (int(result.get("peak_row", 0)), int(result.get("peak_col", 0))),
        }

    def rotation_series(self, kind="Cloth", spacing=None, angles=(0, 20, 45, 70)):
        """The same texture at several angles, each measured."""
        series = []
        for angle in angles:
            made = self.make(kind, spacing, angle)
            made["measured"] = self.measure(made["image"])
            series.append(made)
        return series

    def spacing_series(self, kind="Cloth", spacings=(6, 10, 16, 24)):
        series = []
        for spacing in spacings:
            made = self.make(kind, spacing, 0.0)
            made["measured"] = self.measure(made["image"])
            series.append(made)
        return series

    def verify(self):
        """Does the analyzer recover what we built?

        Spacing should come back within a pixel or so. Angle is checked
        as a change: rotating the picture by 20 degrees should move the
        measured angle by about 20 degrees, which is the claim the
        lesson actually makes.
        """
        spacing_errors = []
        for made in self.spacing_series("Cloth"):
            spacing_errors.append(
                abs(made["measured"]["spacing"] - made["true_spacing"])
            )

        rotations = self.rotation_series("Grass", angles=(0, 20, 45, 70))
        base = rotations[0]["measured"]["angle"]
        rotation_errors = []
        for made in rotations[1:]:
            turned = (made["measured"]["angle"] - base) % 180
            expected = made["true_angle"] % 180
            error = min(abs(turned - expected), 180 - abs(turned - expected))
            rotation_errors.append(error)

        return {
            "spacing_within_2px": max(spacing_errors) < 2.0,
            "worst_spacing_error": max(spacing_errors),
            "rotation_tracks_within_10deg": max(rotation_errors) < 10.0,
            "worst_rotation_error": max(rotation_errors),
        }


# ============================================================
# COLOUR
# ============================================================

def ycbcr_to_rgb(y, cb, cr):
    """Inverse of the project's rgb_to_ycbcr (BT.601, full range)."""
    y = np.asarray(y, dtype=np.float64)
    cb = np.asarray(cb, dtype=np.float64) - 128.0
    cr = np.asarray(cr, dtype=np.float64) - 128.0

    r = y + 1.402 * cr
    g = y - 0.344136 * cb - 0.714136 * cr
    b = y + 1.772 * cb

    stacked = np.dstack([r, g, b])
    return np.clip(np.round(stacked), 0, 255).astype(np.uint8)


def colour_space_scene(size=128):
    """A colourful version of the lesson's space scene.

    The app's own colour map turns the grey scene into deep blues,
    violets and pale cyans, so the picture has real colour to lose.
    """
    grey = np.asarray(render_space_scene(size), dtype=np.uint8)
    return LUT[grey].astype(np.uint8)


def block_average(channel, factor):
    """Shrink by averaging blocks, then stretch back: subsampling."""
    channel = np.asarray(channel, dtype=np.float64)
    size = channel.shape[0]
    usable = (size // factor) * factor

    trimmed = channel[:usable, :usable]
    small = trimmed.reshape(
        usable // factor, factor, usable // factor, factor
    ).mean(axis=(1, 3))

    stretched = np.repeat(np.repeat(small, factor, axis=0), factor, axis=1)

    result = channel.copy()
    result[:usable, :usable] = stretched
    return result


class ColourTrace:
    """Brightness and colour, damaged separately."""

    def __init__(self, image=None, size=128):
        self.image = (
            np.asarray(image, dtype=np.uint8)
            if image is not None
            else colour_space_scene(size)
        )
        self.size = self.image.shape[0]

        self.red, self.green, self.blue = split_rgb_channels(self.image)
        self.y, self.cb, self.cr = rgb_to_ycbcr(self.image)

        self.roundtrip = ycbcr_to_rgb(self.y, self.cb, self.cr)
        self.roundtrip_psnr = calculate_psnr(self.image, self.roundtrip)

    def channel_pictures(self):
        """Each channel on its own, plus its spectrum."""
        items = [
            ("Y  ·  brightness", self.y, palette_free_grey(self.y)),
            ("Cb  ·  blue-ness", self.cb, palette_free_grey(self.cb)),
            ("Cr  ·  red-ness", self.cr, palette_free_grey(self.cr)),
        ]
        return [
            {
                "name": name,
                "channel": channel,
                "picture": picture,
                "spectrum": spectrum_picture(
                    np.fft.fft2(np.asarray(channel, dtype=np.float64))
                ),
                "detail": float(np.abs(np.diff(np.asarray(channel,
                                                          dtype=np.float64))).mean()),
            }
            for name, channel, picture in items
        ]

    def damage(self, target, factor):
        """Subsample one part and rebuild, to see what it cost.

        target is "luma" or "chroma"; factor is the block size, so 2
        means each 2x2 block shares one value.
        """
        y, cb, cr = self.y.astype(np.float64), self.cb.astype(np.float64), \
            self.cr.astype(np.float64)

        if target == "luma":
            y = block_average(y, factor)
        else:
            cb = block_average(cb, factor)
            cr = block_average(cr, factor)

        rebuilt = ycbcr_to_rgb(y, cb, cr)

        return {
            "target": target,
            "factor": factor,
            "image": rebuilt,
            "psnr": calculate_psnr(self.image, rebuilt),
            "saved": 0.0 if factor <= 1 else (
                2 / 3 * (1 - 1 / (factor * factor)) if target == "chroma"
                else 1 / 3 * (1 - 1 / (factor * factor))
            ),
        }

    def comparison(self, factors=(2, 4, 8)):
        """The whole experiment: same damage to luma and to chroma."""
        return [
            {
                "factor": factor,
                "luma": self.damage("luma", factor),
                "chroma": self.damage("chroma", factor),
            }
            for factor in factors
        ]

    def verify(self):
        rows = self.comparison()

        return {
            "ycbcr_roundtrip_is_clean": self.roundtrip_psnr > 45,
            "roundtrip_psnr": self.roundtrip_psnr,
            "chroma_damage_always_cheaper": all(
                row["chroma"]["psnr"] > row["luma"]["psnr"] for row in rows
            ),
            "gap_at_4x": (
                rows[1]["chroma"]["psnr"] - rows[1]["luma"]["psnr"]
            ),
            "luma_carries_more_detail": (
                float(np.abs(np.diff(self.y.astype(float))).mean())
                > float(np.abs(np.diff(self.cb.astype(float))).mean())
            ),
        }


def palette_free_grey(channel):
    """A channel shown as plain grey levels, not through the colour map."""
    channel = np.clip(np.asarray(channel, dtype=np.float64), 0, 255)
    grey = np.round(channel).astype(np.uint8)
    return np.dstack([grey, grey, grey])

"""Everything the resize lesson needs, computed with the project's own
resampling code.

The images come from ``resize_nearest``, ``resize_bilinear`` and
``resize_antialiased``. The per-pixel breakdown below re-derives one
destination pixel using the same half-pixel centre mapping the real
code uses, and checks the result against what the real code produced.
If they disagreed, this raises rather than animating a wrong number.
"""

import numpy as np

from algorithms.spatial.resize import (
    resize_bilinear,
    resize_nearest,
    resize_antialiased,
)
from utils.metrics import calculate_psnr


# A hand-drawn 8 x 8 scene: a lit sphere with a hard rim, one bright
# star, and a flat dark background. Small enough that every pixel can
# carry its own number on screen, and deliberately high-contrast so the
# difference between copying a pixel and blending four is obvious.
TINY_SCENE = np.array([
    [ 20,  20,  20,  20,  20,  20, 255,  20],
    [ 20,  20,  90, 150, 150,  90,  20,  20],
    [ 20,  90, 180, 220, 200, 140,  60,  20],
    [ 20, 150, 220, 255, 230, 170,  80,  20],
    [ 20, 150, 210, 240, 210, 150,  70,  20],
    [ 20,  90, 170, 200, 170, 110,  40,  20],
    [ 20,  20,  80, 120, 110,  60,  20,  20],
    [255,  20,  20,  20,  20,  20,  20,  20],
], dtype=np.uint8)


# Named colours, chosen to be unmistakable from each other. When
# bilinear blends sky into roof you get a colour that is visibly
# neither, which is the entire point of the lesson.
PALETTE = {
    "sky":   (86, 132, 220),
    "sun":   (250, 204, 70),
    "roof":  (214, 80, 70),
    "wall":  (238, 226, 200),
    "door":  (120, 78, 50),
    "grass": (90, 176, 96),
}

# An 8 x 8 picture a child could name: sky, a sun, a house with a door,
# and grass. Big flat areas of one colour, hard edges between them.
_SCENE_PLAN = [
    ["sky",   "sky",  "sky",  "sky",  "sky",  "sky",  "sun",   "sun"],
    ["sky",   "sky",  "sky",  "sky",  "sky",  "sky",  "sun",   "sun"],
    ["sky",   "sky",  "roof", "roof", "roof", "sky",  "sky",   "sky"],
    ["sky",   "roof", "roof", "roof", "roof", "roof", "sky",   "sky"],
    ["sky",   "wall", "wall", "wall", "wall", "wall", "sky",   "sky"],
    ["sky",   "wall", "wall", "door", "wall", "wall", "sky",   "sky"],
    ["grass", "grass", "grass", "grass", "grass", "grass", "grass", "grass"],
    ["grass", "grass", "grass", "grass", "grass", "grass", "grass", "grass"],
]

SCENE_NAMES = [list(row) for row in _SCENE_PLAN]

TINY_SCENE_RGB = np.array(
    [[PALETTE[name] for name in row] for row in _SCENE_PLAN],
    dtype=np.uint8,
)


def smooth_scene_rgb(size=8):
    """A soft, shaded 8 x 8 patch: the opposite of flat pixel art.

    Flat art and photographs want different resamplers, and a lesson
    that only ever shows flat art teaches the wrong lesson. This is the
    space scene at 8 x 8, run through the app's colour map, so every
    neighbouring pixel differs a little and blending has something real
    to work with.
    """
    from algorithms.learning.space_scene import render_space_scene
    from ui.learning.palette import LUT

    grey = render_space_scene(size)
    return LUT[np.asarray(grey, dtype=np.uint8)].astype(np.uint8)


def tiny_scene_rgb():
    """The 8 x 8 colour teaching picture."""
    return TINY_SCENE_RGB.copy()


def colour_name(row, col):
    """What the pixel at (row, col) of the colour scene is called."""
    return SCENE_NAMES[row][col]


def stripe_strip(length=24, width=3,
                 colours=((236, 128, 52), (46, 168, 178))):
    """A one-dimensional stripe pattern: the simplest thing to alias.

    A single row of pixels removes every distraction from sampling.
    There is one axis, the stripes are evenly spaced, and it is obvious
    which pixels a shrink keeps and which it never looks at.
    """
    strip = np.zeros((length, 3), dtype=np.uint8)
    for index in range(length):
        strip[index] = colours[(index // width) % len(colours)]
    return strip


def strip_shrink(strip, factor):
    """Shrink a strip two ways, and say what the honest answer was.

    kept      : take every factor-th pixel, the naive shrink
    blurred   : average each run of factor pixels first, then take one
    ideal     : the block average, which is what the small strip
                should contain, since finer detail cannot be shown
    """
    strip = np.asarray(strip, dtype=np.float64)
    length = strip.shape[0]
    new_length = max(1, length // factor)

    indices = sample_positions(length, new_length)
    kept = strip[indices]

    blocks = strip[: new_length * factor].reshape(new_length, factor, 3)
    ideal = blocks.mean(axis=1)

    # A box blur of the same width is the 1D version of the low-pass
    # filter resize.py applies before downsampling.
    padded = np.pad(strip, ((factor, factor), (0, 0)), mode="reflect")
    smoothed = np.stack(
        [
            padded[index: index + 2 * factor + 1].mean(axis=0)
            for index in range(length)
        ]
    )
    blurred = smoothed[indices]

    def error(result):
        return float(np.sqrt(np.mean((result - ideal) ** 2)))

    return {
        "indices": indices,
        "kept": np.round(kept).astype(np.uint8),
        "blurred": np.round(blurred).astype(np.uint8),
        "ideal": np.round(ideal).astype(np.uint8),
        "smoothed": np.round(smoothed).astype(np.uint8),
        "kept_error": error(kept),
        "blurred_error": error(blurred),
        "new_length": new_length,
    }


class ColourResizeTrace:
    """The colour version of ResizeTrace, for the enlargement chapters.

    resize.py already handles RGB, so the images come straight from it.
    The per-pixel breakdown runs the same mapping on each channel and
    checks the result against the real resized image.
    """

    def __init__(self, image, scale=3, names=None):
        self.image = np.asarray(image, dtype=np.uint8)
        if self.image.ndim != 3:
            raise ValueError("ColourResizeTrace expects an RGB image.")

        # Flat art has named colours ("sky", "roof"); a photograph does
        # not, so it falls back to the RGB triplet.
        self.names = names

        self.scale = int(scale)
        self.old_height, self.old_width = self.image.shape[:2]
        self.new_width = self.old_width * self.scale
        self.new_height = self.old_height * self.scale

        self.nearest = np.asarray(
            resize_nearest(self.image, self.new_width, self.new_height)
        )
        self.bilinear = np.asarray(
            resize_bilinear(self.image, self.new_width, self.new_height)
        )

        self.scale_x = self.old_width / self.new_width
        self.scale_y = self.old_height / self.new_height

    def _source_position(self, new_index, scale, old_limit):
        position = (new_index + 0.5) * scale - 0.5
        return max(0.0, min(position, old_limit - 1))

    def pixel(self, new_y, new_x):
        source_y = self._source_position(new_y, self.scale_y, self.old_height)
        source_x = self._source_position(new_x, self.scale_x, self.old_width)

        y0, x0 = int(np.floor(source_y)), int(np.floor(source_x))
        y1 = min(y0 + 1, self.old_height - 1)
        x1 = min(x0 + 1, self.old_width - 1)

        dy, dx = source_y - y0, source_x - x0

        corners = [
            ("top-left", y0, x0, (1 - dx) * (1 - dy)),
            ("top-right", y0, x1, dx * (1 - dy)),
            ("bottom-left", y1, x0, (1 - dx) * dy),
            ("bottom-right", y1, x1, dx * dy),
        ]

        blended = np.zeros(3, dtype=np.float64)
        described = []

        for label, row, col, weight in corners:
            colour = self.image[row, col].astype(np.float64)
            blended += colour * weight
            described.append({
                "label": label,
                "row": row,
                "col": col,
                "name": self._name(row, col),
                "colour": tuple(int(v) for v in self.image[row, col]),
                "weight": float(weight),
            })

        nearest_y = int(min(round(source_y), self.old_height - 1))
        nearest_x = int(min(round(source_x), self.old_width - 1))

        produced = self.bilinear[new_y, new_x].astype(int)
        mine = np.clip(np.round(blended), 0, 255).astype(int)
        if np.abs(produced - mine).max() > 1:
            raise AssertionError(
                f"Bilinear disagrees at ({new_y}, {new_x}): {produced} vs {mine}"
            )

        return {
            "new_y": new_y,
            "new_x": new_x,
            "source_y": source_y,
            "source_x": source_x,
            "dx": dx,
            "dy": dy,
            "corners": described,
            "blend": tuple(int(v) for v in mine),
            "nearest_source": (nearest_y, nearest_x),
            "nearest_name": self._name(nearest_y, nearest_x),
            "nearest_colour": tuple(
                int(v) for v in self.image[nearest_y, nearest_x]
            ),
            "weights_sum": float(sum(item["weight"] for item in described)),
        }

    def _name(self, row, col):
        if self.names is None:
            r, g, b = self.image[row, col]
            return f"{r},{g},{b}"
        return self.names[row][col]

    def disagreement(self, new_y, new_x):
        """How far apart the two methods are at one pixel (0-255)."""
        a = self.nearest[new_y, new_x].astype(float)
        b = self.bilinear[new_y, new_x].astype(float)
        return float(np.abs(a - b).max())

    def interesting_pixel(self):
        """A pixel where the two methods clearly disagree, near an edge."""
        best, best_score = (0, 0), -1.0

        for new_y in range(self.new_height):
            for new_x in range(self.new_width):
                score = self.disagreement(new_y, new_x)
                if score > best_score:
                    best, best_score = (new_y, new_x), score

        return best


def tiny_scene():
    """The 8 x 8 teaching image."""
    return TINY_SCENE.copy()


def sample_positions(old_size, new_size):
    """Which source pixels a plain shrink actually looks at.

    Returns the rounded source index for every destination index, using
    the same half-pixel centre mapping resize.py uses. Drawing these on
    the pattern is what makes aliasing click: the samples march along in
    step with the squares, so they keep landing on the same colour.
    """
    scale = old_size / new_size
    return [
        int(min(round((index + 0.5) * scale - 0.5), old_size - 1))
        for index in range(new_size)
    ]


def checkerboard(size=128, square=2):
    """A high-frequency pattern: the classic way to show aliasing."""
    y, x = np.mgrid[0:size, 0:size]
    pattern = (((x // square) + (y // square)) % 2) * 255
    return pattern.astype(np.uint8)


class ResizeTrace:
    """One resize experiment: the same source at a new size, three ways."""

    def __init__(self, image, scale=4.0):
        self.image = np.asarray(image, dtype=np.uint8)
        if self.image.ndim != 2:
            raise ValueError("The resize lesson uses a grayscale image.")

        self.scale = float(scale)

        self.old_height, self.old_width = self.image.shape
        self.new_width = max(1, int(round(self.old_width * self.scale)))
        self.new_height = max(1, int(round(self.old_height * self.scale)))

        self.nearest = np.asarray(
            resize_nearest(self.image, self.new_width, self.new_height)
        )
        self.bilinear = np.asarray(
            resize_bilinear(self.image, self.new_width, self.new_height)
        )

        self.scale_x = self.old_width / self.new_width
        self.scale_y = self.old_height / self.new_height

    # ---------------------------------------------------------
    # ONE DESTINATION PIXEL
    # ---------------------------------------------------------

    def _source_position(self, new_index, scale, old_limit):
        """Half-pixel centre mapping, exactly as resize.py does it."""
        position = (new_index + 0.5) * scale - 0.5
        return max(0.0, min(position, old_limit - 1))

    def pixel(self, new_y, new_x):
        """Where a destination pixel comes from, and what both methods say."""
        if not (0 <= new_y < self.new_height and 0 <= new_x < self.new_width):
            raise IndexError("Destination pixel is outside the new image.")

        source_y = self._source_position(new_y, self.scale_y, self.old_height)
        source_x = self._source_position(new_x, self.scale_x, self.old_width)

        y0 = int(np.floor(source_y))
        x0 = int(np.floor(source_x))
        y1 = min(y0 + 1, self.old_height - 1)
        x1 = min(x0 + 1, self.old_width - 1)

        dy = source_y - y0
        dx = source_x - x0

        corners = {
            "q00": (y0, x0, float(self.image[y0, x0]), (1 - dx) * (1 - dy)),
            "q01": (y0, x1, float(self.image[y0, x1]), dx * (1 - dy)),
            "q10": (y1, x0, float(self.image[y1, x0]), (1 - dx) * dy),
            "q11": (y1, x1, float(self.image[y1, x1]), dx * dy),
        }

        blended = sum(value * weight for _, _, value, weight in corners.values())

        nearest_y = int(min(round(source_y), self.old_height - 1))
        nearest_x = int(min(round(source_x), self.old_width - 1))
        nearest_value = int(self.image[nearest_y, nearest_x])

        # Check against what the real functions produced.
        produced_bilinear = int(self.bilinear[new_y, new_x])
        if abs(produced_bilinear - int(round(blended))) > 1:
            raise AssertionError(
                f"Bilinear disagrees at ({new_y}, {new_x}): "
                f"{produced_bilinear} vs {round(blended)}"
            )

        return {
            "new_y": new_y,
            "new_x": new_x,
            "source_y": source_y,
            "source_x": source_x,
            "dx": dx,
            "dy": dy,
            "corners": corners,
            "bilinear": blended,
            "bilinear_shown": produced_bilinear,
            "nearest": nearest_value,
            "nearest_source": (nearest_y, nearest_x),
            "weights_sum": sum(weight for _, _, _, weight in corners.values()),
        }

    def interesting_pixel(self):
        """A destination pixel that sits well between four different values."""
        best = (0, 0)
        best_score = -1.0

        step = max(1, self.new_height // 40)

        for new_y in range(0, self.new_height, step):
            for new_x in range(0, self.new_width, step):
                info = self.pixel(new_y, new_x)
                values = [value for _, _, value, _ in info["corners"].values()]
                spread = max(values) - min(values)
                centred = min(info["dx"], 1 - info["dx"]) * min(
                    info["dy"], 1 - info["dy"]
                )
                score = spread * (0.2 + centred)

                if score > best_score:
                    best, best_score = (new_y, new_x), score

        return best

    def verify(self):
        """Claims the lesson makes about upscaling."""
        checks = []
        for new_y in range(0, self.new_height, max(1, self.new_height // 12)):
            for new_x in range(0, self.new_width, max(1, self.new_width // 12)):
                info = self.pixel(new_y, new_x)
                checks.append(abs(info["weights_sum"] - 1.0) < 1e-9)

        return {
            "weights_always_sum_to_one": all(checks),
            "nearest_only_copies": bool(
                np.isin(np.unique(self.nearest), np.unique(self.image)).all()
            ),
            "bilinear_invents_values": int(
                len(set(np.unique(self.bilinear)) - set(np.unique(self.image)))
            ),
        }


class DownscaleTrace:
    """Shrinking: the same pattern with and without anti-aliasing."""

    def __init__(self, image, factor=4):
        self.image = np.asarray(image, dtype=np.uint8)
        self.factor = int(factor)

        height, width = self.image.shape
        self.new_width = max(1, width // self.factor)
        self.new_height = max(1, height // self.factor)

        self.nearest = np.asarray(
            resize_nearest(self.image, self.new_width, self.new_height)
        )
        self.bilinear = np.asarray(
            resize_bilinear(self.image, self.new_width, self.new_height)
        )
        self.antialiased = np.asarray(
            resize_antialiased(
                self.image, self.new_width, self.new_height, "bilinear"
            )
        )

    def ideal(self):
        """What the smaller image *should* contain: the area average.

        Detail finer than the new pixel grid cannot be represented, so
        the honest answer for each new pixel is the average of the block
        it covers. Anything else is invented structure.
        """
        block_y = self.image.shape[0] // self.new_height
        block_x = self.image.shape[1] // self.new_width

        usable = self.image[
            : self.new_height * block_y,
            : self.new_width * block_x,
        ].astype(np.float64)

        return usable.reshape(
            self.new_height, block_y, self.new_width, block_x
        ).mean(axis=(1, 3))

    def detail(self):
        """How far each shrink lands from that honest answer (RMSE)."""
        target = self.ideal()

        def error(result):
            difference = result.astype(np.float64) - target
            return float(np.sqrt(np.mean(difference ** 2)))

        return {
            "nearest": error(self.nearest),
            "bilinear": error(self.bilinear),
            "antialiased": error(self.antialiased),
        }

    def verify(self):
        spread = self.detail()
        return {
            "antialias_is_closest":
                spread["antialiased"] <= min(spread["nearest"],
                                             spread["bilinear"]),
            "spread": spread,
        }


def upscale_quality(image, scale=4.0):
    """Shrink then re-enlarge, so the two methods can be scored by PSNR."""
    image = np.asarray(image, dtype=np.uint8)
    height, width = image.shape

    small_w = max(2, int(width / scale))
    small_h = max(2, int(height / scale))

    small = np.asarray(resize_antialiased(image, small_w, small_h, "bilinear"))

    back_nearest = np.asarray(resize_nearest(small, width, height))
    back_bilinear = np.asarray(resize_bilinear(small, width, height))

    return {
        "small": small,
        "nearest": back_nearest,
        "bilinear": back_bilinear,
        "nearest_psnr": calculate_psnr(image, back_nearest),
        "bilinear_psnr": calculate_psnr(image, back_bilinear),
    }

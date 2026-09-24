"""Step-by-step convolution trace for the Discover lesson.

The lesson animates every number it shows, so those numbers must be
exactly the ones the project's convolution produces. This module
therefore does not invent its own convolution:

* the full output comes from ``convolve2d_gray`` (the same manual
  routine the Explore pages use), and
* the per-pixel breakdown (window, flipped kernel, products, sum) is
  rebuilt with the *same* reflect padding and kernel flip, then checked
  against that output. A mismatch raises instead of being animated.

No Flet code lives here, so everything can be unit-tested headless.
"""

import numpy as np

from algorithms.spatial.convolution import convolve2d_gray


KERNEL_SIZES = (3, 5, 7)


# ============================================================
# KERNEL PRESETS
# ============================================================

def _box(size):
    return np.full((size, size), 1.0 / (size * size))


def _gaussian(size):
    sigma = 0.3 * ((size - 1) * 0.5 - 1) + 0.8     # OpenCV's default rule
    axis = np.arange(size) - size // 2
    g1 = np.exp(-(axis ** 2) / (2 * sigma * sigma))
    g2 = np.outer(g1, g1)
    return g2 / g2.sum()


def _identity(size):
    kernel = np.zeros((size, size))
    kernel[size // 2, size // 2] = 1.0
    return kernel


def _motion(size):
    kernel = np.zeros((size, size))
    kernel[size // 2, :] = 1.0 / size
    return kernel


# key -> (label, one-line meaning, builder(size) -> array, allowed sizes)
PRESETS = {
    "identity": (
        "Identity",
        "copies every pixel unchanged",
        _identity,
        KERNEL_SIZES,
    ),
    "box_blur": (
        "Box blur",
        "replaces each pixel with the average of its neighbours",
        _box,
        KERNEL_SIZES,
    ),
    "gaussian": (
        "Gaussian blur",
        "a weighted average that trusts close neighbours more",
        _gaussian,
        KERNEL_SIZES,
    ),
    "sharpen": (
        "Sharpen",
        "boosts a pixel against its neighbours, so edges pop",
        lambda size: np.array(
            [[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float64
        ),
        (3,),
    ),
    "sobel_x": (
        "Sobel X",
        "responds to left-right brightness changes (vertical edges)",
        lambda size: np.array(
            [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64
        ),
        (3,),
    ),
    "sobel_y": (
        "Sobel Y",
        "responds to up-down brightness changes (horizontal edges)",
        lambda size: np.array(
            [[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float64
        ),
        (3,),
    ),
    "laplacian": (
        "Edge (Laplacian)",
        "zero on flat areas, large wherever brightness changes",
        lambda size: np.array(
            [[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]], dtype=np.float64
        ),
        (3,),
    ),
    "emboss": (
        "Emboss",
        "lights one side of every edge and shadows the other",
        lambda size: np.array(
            [[-2, -1, 0], [-1, 1, 1], [0, 1, 2]], dtype=np.float64
        ),
        (3,),
    ),
    "motion": (
        "Motion blur",
        "averages along a line, like a camera moving sideways",
        _motion,
        (5, 7),
    ),
}


def preset_kernel(key, size=3):
    """Build a preset kernel. Fixed-size presets ignore ``size``."""
    if key not in PRESETS:
        raise KeyError(f"Unknown preset: {key}")

    _, _, builder, sizes = PRESETS[key]
    size = size if size in sizes else sizes[0]
    return np.asarray(builder(size), dtype=np.float64)


def preset_sizes(key):
    return PRESETS[key][3]


def identify_kernel(kernel):
    """Return the preset key a kernel matches, or None if it is custom."""
    kernel = np.asarray(kernel, dtype=np.float64)
    size = kernel.shape[0]

    for key, (_, _, _, sizes) in PRESETS.items():
        if size in sizes and np.allclose(kernel, preset_kernel(key, size)):
            return key
    return None


def validate_kernel(kernel):
    """Return a float kernel or raise ValueError with a readable message."""
    kernel = np.asarray(kernel, dtype=np.float64)

    if kernel.ndim != 2 or kernel.shape[0] != kernel.shape[1]:
        raise ValueError("The kernel must be a square grid.")
    if kernel.shape[0] not in KERNEL_SIZES:
        raise ValueError("Kernel size must be 3, 5 or 7.")
    if not np.all(np.isfinite(kernel)):
        raise ValueError("Every kernel cell must be a finite number.")

    return kernel


# ============================================================
# TRACE
# ============================================================

class ConvolutionTrace:
    """Everything the lesson needs to animate one kernel on one image."""

    def __init__(self, image, kernel):
        self.image = np.asarray(image, dtype=np.float64)
        if self.image.ndim != 2:
            raise ValueError("The lesson image must be grayscale (2D).")

        self.kernel = validate_kernel(kernel)
        self.size = self.kernel.shape[0]
        self.pad = self.size // 2

        # Identical padding and flip to convolve2d_gray.
        self.padded = np.pad(self.image, self.pad, mode="reflect")
        self.flipped = np.flip(self.kernel, axis=(0, 1))

        # Ground truth from the project's own routine.
        self.output_raw = convolve2d_gray(self.image, self.kernel)
        self.output = np.clip(np.round(self.output_raw), 0, 255).astype(np.uint8)

        self.height, self.width = self.image.shape

    def pixel(self, row, col):
        """Break output pixel (row, col) into the steps the lesson shows."""
        if not (0 <= row < self.height and 0 <= col < self.width):
            raise IndexError(f"Pixel ({row}, {col}) is outside the image.")

        window = self.padded[row: row + self.size, col: col + self.size]
        products = window * self.flipped
        total = float(products.sum())

        expected = float(self.output_raw[row, col])
        if not np.isclose(total, expected, rtol=1e-9, atol=1e-6):
            raise AssertionError(
                f"Trace mismatch at ({row}, {col}): {total} != {expected}"
            )

        return {
            "row": row,
            "col": col,
            "window": window,
            "flipped": self.flipped,
            "products": products,
            "total": total,
            "clipped": int(self.output[row, col]),
            # Which window cells come from the mirrored border.
            "outside": self._outside_mask(row, col),
        }

    def _outside_mask(self, row, col):
        rows = np.arange(row - self.pad, row + self.pad + 1)
        cols = np.arange(col - self.pad, col + self.pad + 1)
        out_r = (rows < 0) | (rows >= self.height)
        out_c = (cols < 0) | (cols >= self.width)
        return out_r[:, None] | out_c[None, :]

    def ghost_value(self, row, col):
        """Reflect-padded value at image coords that may lie outside."""
        return int(round(self.padded[row + self.pad, col + self.pad]))

    def most_interesting_pixel(self):
        """An inner pixel whose window has the most variety to show."""
        best, best_score = (self.height // 2, self.width // 2), -1.0

        for row in range(self.pad, self.height - self.pad):
            for col in range(self.pad, self.width - self.pad):
                window = self.padded[row: row + self.size, col: col + self.size]
                score = float(window.std())
                if score > best_score:
                    best, best_score = (row, col), score
        return best

    def verify_all(self):
        """Check every pixel's breakdown against convolve2d_gray."""
        for row in range(self.height):
            for col in range(self.width):
                self.pixel(row, col)
        return True


def convolve_reveal(image, kernel):
    """Full-resolution result for the lesson's final reveal (uint8)."""
    kernel = validate_kernel(kernel)
    raw = convolve2d_gray(np.asarray(image, dtype=np.float64), kernel)
    return np.clip(np.round(raw), 0, 255).astype(np.uint8)

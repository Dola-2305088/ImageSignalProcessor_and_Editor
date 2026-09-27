"""Everything the noise lesson needs, computed with the project's own
noise generators and cleaning filters.

Nothing here re-implements the maths: the damage comes from
``noise_cleaner.add_gaussian_noise`` / ``add_salt_pepper_noise``, the
repairs from ``mean_filter``, ``gaussian_filter`` and ``median_filter``,
and the scores from the shared ``calculate_psnr``.

The one extra thing this module provides is a *window view*: the
neighbourhood behind a single output pixel, with its mean and its
median, checked against what the real filters produced at that pixel.
If they ever disagreed, the lesson would raise instead of animating a
number that isn't true.
"""

import numpy as np

from algorithms.spatial.noise_cleaner import (
    add_gaussian_noise,
    add_salt_pepper_noise,
    gaussian_filter,
    mean_filter,
    median_filter,
)
from utils.metrics import calculate_psnr


GAUSSIAN = "gaussian"
SALT_PEPPER = "salt_pepper"

NOISE_LABELS = {
    GAUSSIAN: "Gaussian grain",
    SALT_PEPPER: "Salt & pepper",
}

FILTERS = ("mean", "gaussian", "median")

FILTER_LABELS = {
    "mean": "Mean",
    "gaussian": "Gaussian",
    "median": "Median",
}

DEFAULT_SIGMA = 24.0
DEFAULT_AMOUNT = 0.06
DEFAULT_SIZE = 3


def _apply(name, image, kernel_size):
    if name == "mean":
        return mean_filter(image, kernel_size)
    if name == "gaussian":
        return gaussian_filter(image, kernel_size)
    if name == "median":
        return median_filter(image, kernel_size)
    raise ValueError(f"Unknown filter: {name}")


class NoiseTrace:
    """One noisy image and the three attempts to clean it."""

    def __init__(
        self,
        image,
        noise_type=SALT_PEPPER,
        sigma=DEFAULT_SIGMA,
        amount=DEFAULT_AMOUNT,
        kernel_size=DEFAULT_SIZE,
        seed=5,
    ):
        self.image = np.asarray(image, dtype=np.uint8)
        if self.image.ndim != 2:
            raise ValueError("The noise lesson uses a grayscale image.")

        self.noise_type = noise_type
        self.sigma = float(sigma)
        self.amount = float(amount)
        self.kernel_size = int(kernel_size)
        self.pad = self.kernel_size // 2
        self.seed = seed

        self.noisy = self._make_noisy(noise_type)
        self.padded = np.pad(
            self.noisy.astype(np.float64),
            self.pad,
            mode="reflect",
        )

        self.cleaned = {
            name: np.asarray(_apply(name, self.noisy, self.kernel_size))
            for name in FILTERS
        }

        self.noisy_psnr = calculate_psnr(self.image, self.noisy)
        self.psnr = {
            name: calculate_psnr(self.image, self.cleaned[name])
            for name in FILTERS
        }

        self.best_filter = max(FILTERS, key=lambda name: self.psnr[name])

    # ---------------------------------------------------------
    # DAMAGE
    # ---------------------------------------------------------

    def _make_noisy(self, noise_type):
        if noise_type == GAUSSIAN:
            return np.asarray(
                add_gaussian_noise(self.image, sigma=self.sigma, seed=self.seed)
            )

        return np.asarray(
            add_salt_pepper_noise(self.image, amount=self.amount, seed=self.seed)
        )

    def damaged_pixels(self):
        """How many pixels the noise actually changed, and by how much."""
        difference = np.abs(
            self.noisy.astype(np.float64) - self.image.astype(np.float64)
        )

        return {
            "changed": int((difference > 0).sum()),
            "total": int(self.image.size),
            "heavily_changed": int((difference > 100).sum()),
            "mean_shift": float(difference.mean()),
            "max_shift": float(difference.max()),
        }

    # ---------------------------------------------------------
    # ONE WINDOW
    # ---------------------------------------------------------

    def window(self, row, col):
        """The neighbourhood behind one output pixel, with both verdicts.

        The mean and median here are checked against the real filter
        outputs at the same pixel, so the lesson can only ever animate
        numbers the filters actually produced.
        """
        if not (0 <= row < self.image.shape[0] and 0 <= col < self.image.shape[1]):
            raise IndexError(f"Pixel ({row}, {col}) is outside the image.")

        values = self.padded[
            row: row + self.kernel_size,
            col: col + self.kernel_size,
        ]

        mean_value = float(values.mean())
        median_value = float(np.median(values))

        mean_shown = int(np.clip(round(mean_value), 0, 255))
        median_shown = int(np.clip(round(median_value), 0, 255))

        # The filters round the same way, so these must agree within one
        # grey level (rounding of a .5 case is the only slack allowed).
        for name, shown in (("mean", mean_shown), ("median", median_shown)):
            produced = int(self.cleaned[name][row, col])
            if abs(produced - shown) > 1:
                raise AssertionError(
                    f"{name} filter disagrees at ({row}, {col}): "
                    f"{produced} vs {shown}"
                )

        return {
            "row": row,
            "col": col,
            "values": values,
            "sorted": np.sort(values.flatten()),
            "mean": mean_value,
            "median": median_value,
            "mean_shown": mean_shown,
            "median_shown": median_shown,
            "true_value": int(self.image[row, col]),
            "noisy_value": int(self.noisy[row, col]),
            "extremes": int(((values <= 0) | (values >= 255)).sum()),
        }

    def dramatic_window(self):
        """A window that makes the point: a speck among calm neighbours.

        For salt-and-pepper it looks for the neighbourhood where the
        mean and the median disagree most. For Gaussian grain it picks
        the busiest neighbourhood instead, since no single pixel is to
        blame there.
        """
        best = (self.pad, self.pad)
        best_score = -1.0

        height, width = self.image.shape

        for row in range(self.pad, height - self.pad):
            for col in range(self.pad, width - self.pad):
                values = self.padded[
                    row: row + self.kernel_size,
                    col: col + self.kernel_size,
                ]

                if self.noise_type == SALT_PEPPER:
                    score = abs(float(values.mean()) - float(np.median(values)))
                else:
                    score = float(values.std())

                if score > best_score:
                    best, best_score = (row, col), score

        return best

    # ---------------------------------------------------------
    # THE VERDICT TABLE
    # ---------------------------------------------------------

    def comparison_table(self):
        """PSNR for both noise types against all three filters."""
        table = {}

        for noise_type in (GAUSSIAN, SALT_PEPPER):
            if noise_type == self.noise_type:
                noisy = self.noisy
                cleaned = self.cleaned
                noisy_psnr = self.noisy_psnr
                scores = self.psnr
            else:
                noisy = self._make_noisy(noise_type)
                cleaned = {
                    name: np.asarray(_apply(name, noisy, self.kernel_size))
                    for name in FILTERS
                }
                noisy_psnr = calculate_psnr(self.image, noisy)
                scores = {
                    name: calculate_psnr(self.image, cleaned[name])
                    for name in FILTERS
                }

            table[noise_type] = {
                "noisy": noisy_psnr,
                "scores": scores,
                "best": max(FILTERS, key=lambda name: scores[name]),
            }

        return table

    def verify(self):
        """The claims the lesson makes, checked against the numbers.

        Note what is *not* claimed: that averaging beats the median on
        Gaussian grain. On this scene -- large smooth areas with a few
        hard edges -- the median usually wins there too, because it
        keeps edges sharp. The honest, measurable claims are the three
        below, and the lesson says only those.
        """
        table = self.comparison_table()

        return {
            "median_wins_on_specks":
                table[SALT_PEPPER]["best"] == "median",
            "weighted_beats_flat_on_grain":
                table[GAUSSIAN]["scores"]["gaussian"]
                > table[GAUSSIAN]["scores"]["mean"],
            "median_margin_bigger_on_specks":
                (table[SALT_PEPPER]["scores"]["median"]
                 - table[SALT_PEPPER]["scores"]["mean"])
                > (table[GAUSSIAN]["scores"]["median"]
                   - table[GAUSSIAN]["scores"]["mean"]),
            "cleaning_helps":
                all(
                    table[kind]["scores"][table[kind]["best"]]
                    > table[kind]["noisy"]
                    for kind in (GAUSSIAN, SALT_PEPPER)
                ),
            "table": table,
        }

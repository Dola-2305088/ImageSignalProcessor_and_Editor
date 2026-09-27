"""Everything the restoration lesson needs, computed with the project's
own algorithms.

As with the convolution lesson, nothing here re-implements the maths:

* the blur comes from ``motion_blur``,
* the restorations come from ``wiener`` (naive inverse and Wiener),
* the quality numbers come from the shared ``calculate_psnr``.

This module only arranges those results and turns spectra into
displayable images, so the view can animate them.
"""

import numpy as np

from algorithms.spatial.convolution import convolve2d_gray
from algorithms.spatial.motion_blur import create_motion_kernel
from algorithms.spatial.wiener import (
    add_gaussian_noise,
    inverse_filter_gray,
    psf_to_otf,
    wiener_filter_gray,
)
from utils.metrics import calculate_psnr


# Wiener K values the lesson sweeps through, log-spaced from
# "almost no regularisation" to "heavily smoothed".
K_SWEEP = (0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2)

DEFAULT_LENGTH = 15
DEFAULT_ANGLE = 0
DEFAULT_NOISE = 4.0
DEFAULT_K = 0.02


def clip_to_uint8(image):
    return np.clip(np.round(image), 0, 255).astype(np.uint8)


def spectrum_image(values, shape=None):
    """Log-magnitude spectrum, centred, scaled to 0-255."""
    magnitude = np.abs(np.fft.fftshift(values))
    magnitude = np.log1p(magnitude)

    top = magnitude.max()
    if top <= 0:
        return np.zeros(magnitude.shape, dtype=np.uint8)

    return clip_to_uint8(magnitude / top * 255.0)


class RestorationTrace:
    """One complete blur-and-restore experiment."""

    def __init__(
        self,
        image,
        length=DEFAULT_LENGTH,
        angle=DEFAULT_ANGLE,
        noise_sigma=DEFAULT_NOISE,
        seed=7,
    ):
        self.image = np.asarray(image, dtype=np.uint8)
        if self.image.ndim != 2:
            raise ValueError("The restoration lesson uses a grayscale image.")

        self.length = int(length)
        self.angle = float(angle)
        self.noise_sigma = float(noise_sigma)
        self.seed = seed

        self.kernel = create_motion_kernel(self.length, self.angle)
        self.kernel_size = self.kernel.shape[0]

        # Degrade: blur with the project's manual convolution, then add
        # the sensor noise that makes restoration hard.
        self.blurred = clip_to_uint8(
            convolve2d_gray(self.image.astype(np.float64), self.kernel)
        )

        if self.noise_sigma > 0:
            self.degraded = add_gaussian_noise(
                self.blurred,
                sigma=self.noise_sigma,
                seed=self.seed,
            )
        else:
            self.degraded = self.blurred.copy()

        # Restore, both ways.
        self.inverse = clip_to_uint8(
            inverse_filter_gray(self.degraded, self.kernel)
        )

        self._wiener_cache = {}

        # Frequency-domain views.
        self.otf = psf_to_otf(self.kernel, self.image.shape)
        self.kernel_spectrum = spectrum_image(self.otf)
        self.degraded_spectrum = spectrum_image(np.fft.fft2(self.degraded))

        # How much of the spectrum the blur has almost erased: these are
        # the frequencies a naive inverse divides by, and blows up.
        magnitude = np.abs(self.otf)
        self.null_fraction = float((magnitude < 0.05).mean())
        self.min_response = float(magnitude.min())

        # Quality.
        self.blurred_psnr = calculate_psnr(self.image, self.blurred)
        self.degraded_psnr = calculate_psnr(self.image, self.degraded)
        self.inverse_psnr = calculate_psnr(self.image, self.inverse)

    # ---------------------------------------------------------
    # WIENER
    # ---------------------------------------------------------

    def wiener(self, k):
        """Restored image for a given K (cached)."""
        key = round(float(k), 6)

        if key not in self._wiener_cache:
            restored = clip_to_uint8(
                wiener_filter_gray(self.degraded, self.kernel, key)
            )
            self._wiener_cache[key] = (
                restored,
                calculate_psnr(self.image, restored),
            )

        return self._wiener_cache[key]

    def wiener_image(self, k):
        return self.wiener(k)[0]

    def wiener_psnr(self, k):
        return self.wiener(k)[1]

    def sweep(self, values=K_SWEEP):
        """PSNR for each K, plus the best one."""
        results = [(float(k), self.wiener_psnr(k)) for k in values]
        best = max(results, key=lambda pair: pair[1])
        return results, best

    def best_k(self, values=K_SWEEP):
        return self.sweep(values)[1]

    # ---------------------------------------------------------
    # SELF-CHECK
    # ---------------------------------------------------------

    def verify(self):
        """The lesson's claims must hold for the numbers on screen.

        Returns the facts the narration relies on, so a view can assert
        them instead of asserting them in prose only.
        """
        best_k, best_psnr = self.best_k()

        return {
            "kernel_sums_to_one": bool(np.isclose(self.kernel.sum(), 1.0)),
            "blur_lowers_quality": self.blurred_psnr < 99,
            "wiener_beats_degraded": best_psnr > self.degraded_psnr,
            "wiener_beats_inverse": best_psnr > self.inverse_psnr,
            "best_k": best_k,
            "best_psnr": best_psnr,
        }

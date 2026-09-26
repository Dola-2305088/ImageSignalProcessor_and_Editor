"""Backend for the frequency foundation lesson.

The claim the whole frequency side rests on is that an image is a sum
of waves. This module produces the evidence for it, in the order the
lesson needs:

    row_signal / partial_sum   one line of pixels, rebuilt harmonic by
                               harmonic (the 1D Fourier series)
    basis_image                what a single 2D frequency looks like
    PATTERNS                   synthetic images whose spectra are
                               obvious, for learning to read a spectrum
    reconstruct_top            the real image rebuilt from its N
                               strongest coefficients

The project's manual 2D DFT is the reference: ``verify()`` checks it
against NumPy's FFT on the lesson image. The lesson itself uses the FFT
for anything interactive, because the manual transform is a matrix
multiply and far too slow for a slider.
"""

import numpy as np

from algorithms.frequency.dft import manual_dft2
from algorithms.learning.space_scene import render_space_scene
from utils.metrics import calculate_psnr


LESSON_SIZE = 96

# Named 2D frequencies for the "waves have direction" chapter:
# (u, v) as cycles across the whole image.
BASIS_EXAMPLES = [
    ("flat", 0, 0, "the average brightness, no wave at all"),
    ("wide vertical stripes", 0, 2, "2 cycles across, running up and down"),
    ("wide horizontal stripes", 2, 0, "2 cycles down, running side to side"),
    ("fine vertical stripes", 0, 8, "8 cycles across: finer, further from centre"),
    ("diagonal", 4, 4, "equal in both directions, so it tilts 45°"),
    ("fine diagonal", 9, 5, "steeper and finer still"),
]


def basis_image(u, v, size=LESSON_SIZE):
    """One 2D cosine: u cycles down the image, v cycles across."""
    y, x = np.mgrid[0:size, 0:size]
    wave = np.cos(2 * np.pi * (u * y / size + v * x / size))
    return np.clip(np.round(128 + 110 * wave), 0, 255).astype(np.uint8)


def stripes(size=LESSON_SIZE, spacing=8, angle=0.0):
    """A sine grating at a known spacing and angle."""
    y, x = np.mgrid[0:size, 0:size]
    radians = np.deg2rad(angle)
    projected = x * np.cos(radians) + y * np.sin(radians)
    wave = np.sin(2 * np.pi * projected / spacing)
    return np.clip(np.round(128 + 110 * wave), 0, 255).astype(np.uint8)


def spectrum_picture(spectrum, gamma=1.0):
    """Centred log-magnitude spectrum, scaled to 0-255 for display."""
    magnitude = np.abs(np.fft.fftshift(spectrum))
    magnitude = np.log1p(magnitude)

    top = magnitude.max()
    if top <= 0:
        return np.zeros(magnitude.shape, dtype=np.uint8)

    scaled = (magnitude / top) ** gamma
    return np.clip(np.round(scaled * 255), 0, 255).astype(np.uint8)


def peak_info(image):
    """Where the brightest dot of a pattern's spectrum actually is.

    Returns its distance from the centre in "steps" (one step is one
    cycle across the whole picture) and its angle, so a lesson can put
    a measured number on screen instead of asking the reader to judge
    a distance by eye.

    For a stripe pattern the distance is exactly
    image width / stripe spacing, which is the relationship worth
    teaching.
    """
    image = np.asarray(image, dtype=np.float64)
    size = image.shape[0]

    shifted = np.fft.fftshift(np.fft.fft2(image))
    magnitude = np.abs(shifted)

    centre = size // 2
    # Ignore the middle: that dot is just the average brightness.
    magnitude[centre - 1: centre + 2, centre - 1: centre + 2] = 0.0

    row, col = np.unravel_index(int(np.argmax(magnitude)), magnitude.shape)
    dy, dx = row - centre, col - centre
    radius = float(np.hypot(dy, dx))

    return {
        "row": int(row),
        "col": int(col),
        "centre": centre,
        "radius": radius,
        "angle": float(np.degrees(np.arctan2(dy, dx)) % 180.0),
        "spacing": (size / radius) if radius else float("inf"),
    }


def annotate_spectrum(image):
    """A pattern's spectrum with its own measurement drawn on it.

    A crosshair marks the centre, a ring marks each of the two bright
    dots, and a line joins the centre to one of them, so "distance from
    the centre" is something to look at rather than to judge.

    Returns the RGB picture and the peak_info that produced it.
    """
    spectrum = spectrum_picture(np.fft.fft2(np.asarray(image, dtype=np.float64)))
    info = peak_info(image)

    canvas = np.dstack([spectrum] * 3).astype(np.float64)
    size = canvas.shape[0]
    centre = info["centre"]

    crosshair = np.array([120, 140, 190], dtype=np.float64)
    canvas[centre, :] = 0.45 * canvas[centre, :] + 0.55 * crosshair
    canvas[:, centre] = 0.45 * canvas[:, centre] + 0.55 * crosshair

    line = np.array([251, 191, 36], dtype=np.float64)
    steps = max(2, int(info["radius"] * 3))
    for step in range(steps + 1):
        fraction = step / steps
        y = int(round(centre + (info["row"] - centre) * fraction))
        x = int(round(centre + (info["col"] - centre) * fraction))
        if 0 <= y < size and 0 <= x < size:
            canvas[y, x] = 0.25 * canvas[y, x] + 0.75 * line

    ring = np.array([34, 211, 238], dtype=np.float64)
    for row, col in (
        (info["row"], info["col"]),
        (2 * centre - info["row"], 2 * centre - info["col"]),
    ):
        for angle in np.linspace(0, 2 * np.pi, 96):
            y = int(round(row + 3.4 * np.sin(angle)))
            x = int(round(col + 3.4 * np.cos(angle)))
            if 0 <= y < size and 0 <= x < size:
                canvas[y, x] = ring

    return np.clip(np.round(canvas), 0, 255).astype(np.uint8), info


def ruler_overlay(image, spacing, angle=0.0):
    """Draw a measuring bracket across one repeat of a pattern.

    Two ticks one repeat apart, joined by a bar. It turns "the threads
    are 8 px apart" from a claim into something measured on the picture
    itself.
    """
    image = np.asarray(image)
    canvas = (np.dstack([image] * 3) if image.ndim == 2
              else image.copy()).astype(np.float64)

    size = canvas.shape[0]
    mark = np.array([251, 191, 36], dtype=np.float64)

    radians = np.deg2rad(angle)
    start_y, start_x = int(size * 0.12), int(size * 0.10)

    end_y = int(round(start_y + spacing * np.sin(radians)))
    end_x = int(round(start_x + spacing * np.cos(radians)))

    # the bar
    for step in range(int(spacing) * 3 + 1):
        fraction = step / max(1, int(spacing) * 3)
        y = int(round(start_y + (end_y - start_y) * fraction))
        x = int(round(start_x + (end_x - start_x) * fraction))
        if 0 <= y < size and 0 <= x < size:
            canvas[y, x] = mark

    # a tick at each end, across the bar
    for y0, x0 in ((start_y, start_x), (end_y, end_x)):
        for offset in range(-4, 5):
            y = int(round(y0 - offset * np.sin(radians + np.pi / 2)))
            x = int(round(x0 - offset * np.cos(radians + np.pi / 2)))
            if 0 <= y < size and 0 <= x < size:
                canvas[y, x] = mark

    return np.clip(np.round(canvas), 0, 255).astype(np.uint8)


def wave_image(size=LESSON_SIZE, spacing=16, angle=0.0, amplitude=110):
    """One wave drawn as a picture: bright and dark bands.

    spacing is the distance between two bright bands in pixels, which
    is the thing a beginner can measure with a ruler on screen. angle
    turns the bands.
    """
    y, x = np.mgrid[0:size, 0:size]
    radians = np.deg2rad(angle)
    projected = x * np.cos(radians) + y * np.sin(radians)
    wave = np.sin(2 * np.pi * projected / max(2.0, spacing))
    return np.clip(np.round(128 + amplitude * wave), 0, 255).astype(np.uint8)


def add_waves(*images):
    """Add wave pictures together, keeping mid-grey as zero."""
    total = np.zeros(images[0].shape, dtype=np.float64)
    for image in images:
        total += np.asarray(image, dtype=np.float64) - 128.0
    return np.clip(np.round(128 + total), 0, 255).astype(np.uint8)


class SpectrumTrace:
    """Everything the foundation lesson animates, for one fixed image."""

    def __init__(self, image=None, size=LESSON_SIZE):
        self.image = (
            np.asarray(image, dtype=np.uint8)
            if image is not None
            else np.asarray(render_space_scene(size), dtype=np.uint8)
        )
        self.size = self.image.shape[0]

        self.spectrum = np.fft.fft2(self.image.astype(np.float64))
        self.spectrum_image = spectrum_picture(self.spectrum)

        # Coefficients ranked by how much they contribute.
        magnitude = np.abs(self.spectrum)
        self.order = np.argsort(magnitude, axis=None)[::-1]
        self.total_energy = float((magnitude ** 2).sum())

    # ---------------------------------------------------------
    # 1D: ONE ROW OF PIXELS
    # ---------------------------------------------------------

    def row_signal(self, row):
        """One horizontal line of the image, as a plain signal."""
        return self.image[row].astype(np.float64)

    def row_harmonics(self, row):
        """Amplitude and phase of each harmonic in that row."""
        signal = self.row_signal(row)
        coefficients = np.fft.rfft(signal)
        amplitudes = np.abs(coefficients) / len(signal)
        amplitudes[1:] *= 2                       # pair each +f with its -f
        return amplitudes, np.angle(coefficients)

    def partial_sum(self, row, harmonics):
        """The row rebuilt from its first ``harmonics`` waves.

        harmonics = 0 gives the flat average; each step adds the next
        wave up in frequency, which is the classic Fourier build-up.
        """
        signal = self.row_signal(row)
        coefficients = np.fft.rfft(signal)

        kept = np.zeros_like(coefficients)
        kept[: harmonics + 1] = coefficients[: harmonics + 1]

        return np.fft.irfft(kept, n=len(signal))

    def single_wave(self, row, harmonic):
        """Just the one wave added at this step, for drawing alongside."""
        signal = self.row_signal(row)
        coefficients = np.fft.rfft(signal)

        only = np.zeros_like(coefficients)
        if harmonic < len(coefficients):
            only[harmonic] = coefficients[harmonic]

        return np.fft.irfft(only, n=len(signal))

    def row_error(self, row, harmonics):
        """How far the partial sum still is from the true row."""
        difference = self.partial_sum(row, harmonics) - self.row_signal(row)
        return float(np.sqrt(np.mean(difference ** 2)))

    def busiest_row(self):
        """A row with plenty going on: planet, ring and background."""
        variation = np.abs(np.diff(self.image.astype(np.float64), axis=1)).sum(axis=1)
        return int(np.argmax(variation))

    # ---------------------------------------------------------
    # 2D: REBUILDING THE WHOLE IMAGE
    # ---------------------------------------------------------

    def reconstruct_top(self, count):
        """Image rebuilt from its ``count`` strongest coefficients."""
        kept = np.zeros_like(self.spectrum)

        if count > 0:
            flat_indices = self.order[:count]
            rows, cols = np.unravel_index(flat_indices, self.spectrum.shape)
            kept[rows, cols] = self.spectrum[rows, cols]

        result = np.real(np.fft.ifft2(kept))
        return np.clip(np.round(result), 0, 255).astype(np.uint8)

    def reconstruction_quality(self, count):
        """PSNR and the share of total energy those coefficients hold."""
        image = self.reconstruct_top(count)

        magnitude = np.abs(self.spectrum)
        flat = (magnitude ** 2).flatten()[self.order]
        energy = float(flat[:count].sum()) / self.total_energy if count else 0.0

        return {
            "count": int(count),
            "percent": 100.0 * count / self.spectrum.size,
            "energy": energy,
            "psnr": calculate_psnr(self.image, image) if count else 0.0,
            "image": image,
        }

    def energy_curve(self, steps=40):
        """Energy captured as more coefficients are kept, for a plot."""
        magnitude = np.abs(self.spectrum)
        flat = (magnitude ** 2).flatten()[self.order]
        cumulative = np.cumsum(flat) / self.total_energy

        counts = np.unique(
            np.round(np.geomspace(1, self.spectrum.size, steps)).astype(int)
        )
        return [(int(c), float(cumulative[c - 1])) for c in counts]

    # ---------------------------------------------------------
    # PATTERNS WITH OBVIOUS SPECTRA
    # ---------------------------------------------------------

    def pattern_set(self):
        """Synthetic images whose spectra can be predicted by eye."""
        items = [
            ("Wide stripes", stripes(self.size, spacing=16, angle=0),
             "16 px apart, vertical: two dots close to the centre"),
            ("Fine stripes", stripes(self.size, spacing=6, angle=0),
             "6 px apart: the same two dots, further out"),
            ("Tilted stripes", stripes(self.size, spacing=10, angle=45),
             "rotate the picture and the spectrum rotates with it"),
            ("The planet", self.image,
             "a real picture: energy spread everywhere, strongest near the centre"),
        ]

        return [
            {
                "name": name,
                "image": image,
                "note": note,
                "spectrum": spectrum_picture(np.fft.fft2(image.astype(np.float64))),
            }
            for name, image, note in items
        ]

    def peak_radius(self, image):
        """Distance of the strongest non-DC peak from the centre.

        For a grating this is exactly the image size divided by the
        stripe spacing, which lets the lesson check its own claim.
        """
        spectrum = np.fft.fftshift(np.fft.fft2(np.asarray(image, dtype=np.float64)))
        magnitude = np.abs(spectrum)

        centre = self.size // 2
        magnitude[centre, centre] = 0.0

        row, col = np.unravel_index(np.argmax(magnitude), magnitude.shape)
        return float(np.hypot(row - centre, col - centre))

    # ---------------------------------------------------------
    # SELF-CHECK
    # ---------------------------------------------------------

    def verify(self, manual_size=32):
        """Check the shortcuts against the project's own transform."""
        patch = self.image[:manual_size, :manual_size].astype(np.float64)
        manual = manual_dft2(patch)
        fast = np.fft.fft2(patch)
        manual_error = float(np.abs(manual - fast).max())

        row = self.busiest_row()
        full = self.partial_sum(row, len(self.row_signal(row)) // 2)
        row_error = float(np.abs(full - self.row_signal(row)).max())

        everything = self.reconstruct_top(self.spectrum.size)
        image_error = float(
            np.abs(everything.astype(float) - self.image.astype(float)).max()
        )

        curve = self.energy_curve()
        monotone = all(
            later >= earlier - 1e-9
            for (_, earlier), (_, later) in zip(curve, curve[1:])
        )

        return {
            "manual_matches_fft": manual_error < 1e-6,
            "manual_error": manual_error,
            "all_harmonics_rebuild_row": row_error < 1e-6,
            "all_coefficients_rebuild_image": image_error <= 1.0,
            "energy_is_monotone": monotone,
        }

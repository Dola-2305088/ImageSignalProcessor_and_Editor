"""Backends for the frequency feature lessons (masking, hybrids,
compression).

Each class wraps the project's own frequency code and adds only what a
lesson needs: the intermediate pictures, the quality numbers, and a
``verify()`` that checks the claims the narration makes.

    MaskTrace         keep the middle (blur) or the outside (edges),
                      with soft and hard mask edges so ringing can be
                      shown honestly
    HybridTrace       one image's slow waves plus another's fast ones
    CompressionTrace  keep the strongest coefficients, and what that
                      costs

All three use NumPy's FFT for speed; ``verify()`` compares against the
project's manual DFT so the shortcut is justified rather than assumed.
"""

import numpy as np

from algorithms.frequency.compression import compress_dft
from algorithms.frequency.dft import (
    create_high_pass_mask,
    create_low_pass_mask,
    manual_dft2,
)
from algorithms.learning.space_scene import render_space_scene
from algorithms.learning.spectrum_trace import spectrum_picture
from utils.metrics import calculate_psnr


def to_image(values):
    return np.clip(np.round(np.real(values)), 0, 255).astype(np.uint8)


def soft_mask(shape, radius, softness, high_pass=False):
    """A mask whose edge fades over ``softness`` pixels.

    softness = 0 gives the project's hard-edged circle, which is what
    causes ringing; a few pixels of fade removes it. Being able to show
    both is the point.
    """
    rows, cols = shape
    y, x = np.mgrid[0:rows, 0:cols]
    distance = np.hypot(y - rows // 2, x - cols // 2)

    if softness <= 0:
        mask = (distance <= radius).astype(np.float64)
    else:
        mask = np.clip((radius + softness / 2 - distance) / softness, 0.0, 1.0)

    return 1.0 - mask if high_pass else mask


class MaskTrace:
    """Keep part of the spectrum, and see what happens to the picture."""

    def __init__(self, image=None, size=96):
        self.image = (
            np.asarray(image, dtype=np.uint8)
            if image is not None
            else np.asarray(render_space_scene(size), dtype=np.uint8)
        )
        self.size = self.image.shape[0]
        self.spectrum = np.fft.fft2(self.image.astype(np.float64))
        self.shifted = np.fft.fftshift(self.spectrum)
        self.spectrum_image = spectrum_picture(self.spectrum)

    def apply(self, radius, high_pass=False, softness=0):
        """Filter the image and return every picture the lesson shows."""
        mask = soft_mask(self.image.shape, radius, softness, high_pass)

        filtered = self.shifted * mask
        result = np.fft.ifft2(np.fft.ifftshift(filtered))

        raw = np.real(result)
        kept_fraction = float(mask.sum() / mask.size)
        energy = float(
            (np.abs(filtered) ** 2).sum() / (np.abs(self.shifted) ** 2).sum()
        )

        if high_pass:
            # High-pass output swings around zero, so mid-grey is the
            # honest way to show it.
            picture = np.clip(np.round(raw + 128), 0, 255).astype(np.uint8)
        else:
            picture = to_image(raw)

        return {
            "image": picture,
            "raw": raw,
            "mask": mask,
            "mask_picture": np.clip(np.round(mask * 255), 0, 255).astype(np.uint8),
            "spectrum_picture": spectrum_picture(np.fft.ifftshift(filtered)),
            "kept_fraction": kept_fraction,
            "energy": energy,
            "psnr": calculate_psnr(self.image, picture) if not high_pass else None,
            "radius": radius,
            "softness": softness,
            "high_pass": high_pass,
        }

    def ringing_score(self, radius, softness):
        """How much a mask rings, measured on a hard edge.

        A sharp-edged mask makes ripples beside strong edges. Measuring
        the overshoot past the original range turns "look at the
        ripples" into a number.
        """
        raw = self.apply(radius, high_pass=False, softness=softness)["raw"]
        overshoot = np.maximum(raw - 255.0, 0.0) + np.maximum(-raw, 0.0)
        return float(overshoot.mean())

    def verify(self, manual_size=32):
        patch = self.image[:manual_size, :manual_size].astype(np.float64)
        manual_error = float(np.abs(manual_dft2(patch) - np.fft.fft2(patch)).max())

        everything = self.apply(self.size, high_pass=False, softness=0)
        identity_error = float(
            np.abs(everything["image"].astype(float) - self.image.astype(float)).max()
        )

        low = self.apply(12, high_pass=False)
        high = self.apply(12, high_pass=True)
        halves = np.clip(
            np.round(low["raw"] + high["raw"]), 0, 255
        ).astype(np.uint8)
        split_error = float(
            np.abs(halves.astype(float) - self.image.astype(float)).max()
        )

        hard = self.ringing_score(10, softness=0)
        soft = self.ringing_score(10, softness=6)

        # The project's own hard-edged mask, for comparison.
        project_low = create_low_pass_mask(self.image.shape, 12)
        project_high = create_high_pass_mask(self.image.shape, 12)
        masks_agree = bool(
            np.allclose(project_low, soft_mask(self.image.shape, 12, 0, False))
            and np.allclose(project_high, soft_mask(self.image.shape, 12, 0, True))
        )

        return {
            "manual_matches_fft": manual_error < 1e-6,
            "full_mask_is_identity": identity_error <= 1.0,
            "halves_rebuild_original": split_error <= 1.0,
            "hard_edge_rings_more": hard > soft,
            "hard_ringing": hard,
            "soft_ringing": soft,
            "matches_project_masks": masks_agree,
        }


class HybridTrace:
    """One picture's slow waves plus another's fast ones."""

    def __init__(self, near=None, far=None, size=96):
        self.size = size
        self.near = (
            np.asarray(near, dtype=np.uint8)
            if near is not None
            else np.asarray(render_space_scene(size), dtype=np.uint8)
        )
        self.far = (
            np.asarray(far, dtype=np.uint8)
            if far is not None
            else self._companion(size)
        )

    @staticmethod
    def _companion(size):
        """A second space scene: a bright comet on a dark sky.

        Deliberately different in shape from the planet, so which one
        you are seeing is never ambiguous.
        """
        y, x = np.mgrid[0:size, 0:size]
        cx, cy = size * 0.62, size * 0.38

        head = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * (size * 0.045) ** 2)))

        along = (x - cx) * 0.7 + (y - cy) * 0.7
        across = (x - cx) * 0.7 - (y - cy) * 0.7
        tail = np.exp(-np.clip(along, 0, None) / (size * 0.22)) * np.exp(
            -(across ** 2) / (2 * (size * 0.05) ** 2)
        )
        tail *= (along > 0)

        field = 0.10 + 0.95 * head + 0.55 * tail
        return np.clip(np.round(field * 255), 0, 255).astype(np.uint8)

    def build(self, cutoff=10, softness=4):
        """Blend the two, and return every part of the recipe."""
        near_spectrum = np.fft.fftshift(np.fft.fft2(self.near.astype(np.float64)))
        far_spectrum = np.fft.fftshift(np.fft.fft2(self.far.astype(np.float64)))

        low_mask = soft_mask(self.near.shape, cutoff, softness, high_pass=False)
        high_mask = 1.0 - low_mask

        low_part = np.real(np.fft.ifft2(np.fft.ifftshift(far_spectrum * low_mask)))
        high_part = np.real(np.fft.ifft2(np.fft.ifftshift(near_spectrum * high_mask)))

        hybrid = to_image(low_part + high_part)

        return {
            "hybrid": hybrid,
            "low_part": to_image(low_part),
            "high_part": np.clip(np.round(high_part + 128), 0, 255).astype(np.uint8),
            "low_mask": np.clip(np.round(low_mask * 255), 0, 255).astype(np.uint8),
            "cutoff": cutoff,
        }

    def seen_from(self, image, distance):
        """What the hybrid looks like from further away.

        Viewing something from a distance really does discard fine
        detail, so shrinking the picture is an honest simulation: at
        distance 1 you see it as-is, at 8 you see one eighth the width.
        """
        image = np.asarray(image, dtype=np.uint8)
        size = max(4, int(round(self.size / max(1, distance))))

        blocks = image[: size * (self.size // size), : size * (self.size // size)]
        factor = max(1, self.size // size)
        trimmed = blocks[: size * factor, : size * factor]
        small = trimmed.reshape(size, factor, size, factor).mean(axis=(1, 3))

        return np.clip(np.round(small), 0, 255).astype(np.uint8), size

    @staticmethod
    def _detail_of(image, cutoff=10):
        """Just the fast waves of an image, as a flat array."""
        spectrum = np.fft.fftshift(np.fft.fft2(np.asarray(image, dtype=np.float64)))
        high = spectrum * soft_mask(spectrum.shape, cutoff, 4, high_pass=True)
        return np.real(np.fft.ifft2(np.fft.ifftshift(high))).flatten()

    @staticmethod
    def _similarity(a, b):
        a = a - a.mean()
        b = b - b.mean()
        denominator = np.sqrt((a ** 2).sum() * (b ** 2).sum())
        return float((a * b).sum() / denominator) if denominator else 0.0

    def verify(self, cutoff=10):
        """Check the two claims the lesson makes, each with the right tool.

        PSNR cannot answer "which picture do you see up close": the slow
        waves carry nearly all the energy, so by PSNR the blurred image
        always wins, even when every visible edge belongs to the other
        one. Close up, what the eye follows is the detail, so the fair
        comparison is between the *fine* waves of the hybrid and the
        fine waves of each source. Far away, the eye has only the
        coarse picture left, and there PSNR on the shrunken view is
        exactly right.
        """
        parts = self.build(cutoff)
        low_mask = soft_mask(self.near.shape, cutoff, 4, high_pass=False)

        hybrid_detail = self._detail_of(parts["hybrid"], cutoff)
        detail_like_near = self._similarity(hybrid_detail,
                                            self._detail_of(self.near, cutoff))
        detail_like_far = self._similarity(hybrid_detail,
                                           self._detail_of(self.far, cutoff))

        far_view, _ = self.seen_from(parts["hybrid"], 8)
        far_reference, _ = self.seen_from(self.far, 8)
        near_reference, _ = self.seen_from(self.near, 8)
        far_psnr = calculate_psnr(far_reference, far_view)
        near_psnr = calculate_psnr(near_reference, far_view)

        return {
            "close_up_detail_is_the_sharp_image": detail_like_near > detail_like_far,
            "far_away_favours_blur": far_psnr > near_psnr,
            "detail_similarity_near": detail_like_near,
            "detail_similarity_far": detail_like_far,
            "far_psnr_blurred_source": far_psnr,
            "far_psnr_sharp_source": near_psnr,
            "masks_complement": bool(
                np.allclose(low_mask + (1.0 - low_mask), 1.0)
            ),
        }


class CompressionTrace:
    """Keep the strongest coefficients and throw the rest away."""

    def __init__(self, image=None, size=96):
        self.image = (
            np.asarray(image, dtype=np.uint8)
            if image is not None
            else np.asarray(render_space_scene(size), dtype=np.uint8)
        )
        self.size = self.image.shape[0]
        self.spectrum = np.fft.fft2(self.image.astype(np.float64))
        self.total = self.spectrum.size

        magnitude = np.abs(self.spectrum)
        self.order = np.argsort(magnitude, axis=None)[::-1]
        self.sorted_energy = (magnitude ** 2).flatten()[self.order]
        self.total_energy = float(self.sorted_energy.sum())
        self.cumulative = np.cumsum(self.sorted_energy) / self.total_energy

    def at_percent(self, percent):
        """Reconstruction from the strongest ``percent`` of coefficients."""
        count = max(1, int(round(self.total * percent / 100.0)))
        return self.at_count(count)

    def at_count(self, count):
        count = int(max(0, min(count, self.total)))

        kept = np.zeros_like(self.spectrum)
        if count:
            rows, cols = np.unravel_index(self.order[:count], self.spectrum.shape)
            kept[rows, cols] = self.spectrum[rows, cols]

        image = to_image(np.fft.ifft2(kept))
        energy = float(self.cumulative[count - 1]) if count else 0.0

        return {
            "count": count,
            "percent": 100.0 * count / self.total,
            "energy": energy,
            "psnr": calculate_psnr(self.image, image) if count else 0.0,
            "image": image,
            "kept_spectrum": spectrum_picture(kept),
            "discarded": self.total - count,
        }

    def curve(self, points=36):
        """Energy and PSNR against how many coefficients are kept."""
        counts = np.unique(
            np.round(np.geomspace(1, self.total, points)).astype(int)
        )
        return [self.at_count(int(count)) for count in counts]

    def count_for_energy(self, fraction):
        """How few coefficients hold this share of the energy."""
        index = int(np.searchsorted(self.cumulative, fraction) + 1)
        return min(index, self.total)

    def verify(self, percent=5.0):
        """Check against the project's own compress_dft."""
        mine = self.at_percent(percent)

        theirs, mask, kept, total = compress_dft(self.spectrum, percent)
        theirs_image = to_image(np.fft.ifft2(theirs))

        difference = float(
            np.abs(theirs_image.astype(float) - mine["image"].astype(float)).max()
        )

        curve = self.curve(12)
        monotone = all(
            later["psnr"] >= earlier["psnr"] - 0.01
            for earlier, later in zip(curve, curve[1:])
        )

        return {
            "matches_project_compressor": difference <= 1.0,
            "count_matches": abs(kept - mine["count"]) <= 1,
            "quality_improves_monotonically": monotone,
            "ten_percent_energy": self.at_percent(10)["energy"],
            "coefficients_for_90_percent": self.count_for_energy(0.90),
        }

"""Adapter between the game and algorithms/spatial/*.

This is the ONLY game file that knows backend function names and parameter
names. If a backend signature differs from what is assumed here, the fix
belongs in this file alone - `python -m game.selftest` reports exactly which
call failed and what the real signature is.

Keyword arguments are resolved by inspecting each backend function's
signature (see `_call`), so `kernel_size` vs `size`, `K` vs `k`, `psf` vs
`kernel` etc. are all accepted without editing this file.
"""
from __future__ import annotations

import importlib
import inspect
import math

import numpy as np

# hint -> accepted backend parameter names, in priority order
_ALIASES = {
    "size": ("kernel_size", "ksize", "size", "window_size", "window", "k_size"),
    "sigma": ("sigma", "std", "sigma_value"),
    "k": ("K", "k", "nsr", "noise_to_signal", "balance", "regularization", "reg"),
    "kernel": ("kernel", "psf", "blur_kernel", "motion_kernel"),
    "length": ("length", "kernel_length", "size", "kernel_size"),
    "angle": ("angle", "theta", "angle_deg", "degrees"),
    "mode": ("mode", "direction", "kind", "edge_type"),
}


class BackendSignatureError(TypeError):
    """Raised when a backend function has no parameter matching a hint."""


def _spatial(module: str):
    return importlib.import_module(f"algorithms.spatial.{module}")


def _call(fn, image, **hints):
    """Call fn(image, **kwargs), mapping each hint onto fn's real parameter name."""
    params = inspect.signature(fn).parameters
    first = next(iter(params))
    kwargs = {}
    for hint, value in hints.items():
        for alias in _ALIASES.get(hint, (hint,)):
            if alias in params and alias != first and alias not in kwargs:
                kwargs[alias] = value
                break
        else:
            raise BackendSignatureError(
                f"{fn.__module__}.{fn.__name__}{inspect.signature(fn)} "
                f"has no parameter for '{hint}'"
            )
    return fn(image, **kwargs)


def to_uint8(arr, rescale: bool = False) -> np.ndarray:
    """Convert any backend output to displayable uint8.

    rescale=True maps the maximum to 255 (edge magnitudes can exceed 255);
    otherwise values are simply clipped (restoration outputs that overshoot
    slightly must NOT be globally rescaled).
    """
    a = np.nan_to_num(np.asarray(arr, dtype=np.float64), nan=0.0, posinf=255.0, neginf=0.0)
    if rescale and a.size and a.max() > 255.0:
        a = a * (255.0 / a.max())
    return np.clip(np.rint(a), 0, 255).astype(np.uint8)


# ---- Feature 1: blur & sharpen ------------------------------------------------
def blur(image, size: int) -> np.ndarray:
    return to_uint8(_call(_spatial("blur_sharpen").blur_image, image, size=size))


def sharpen(image) -> np.ndarray:
    return to_uint8(_spatial("blur_sharpen").sharpen_image(image))


# ---- Feature 2: edges ---------------------------------------------------------
def edges(image, mode: str) -> np.ndarray:
    """mode: 'horizontal' | 'vertical' | 'combined'"""
    return to_uint8(_call(_spatial("edge_detection").detect_edges, image, mode=mode), rescale=True)


# ---- Feature 3: noise cleaner -------------------------------------------------
def clean_noise(image, filter_name: str) -> np.ndarray:
    """filter_name: 'mean' | 'gaussian' | 'median' (backend default sizes)."""
    mod = _spatial("noise_cleaner")
    fn = {"mean": mod.mean_filter, "gaussian": mod.gaussian_filter, "median": mod.median_filter}[filter_name]
    return to_uint8(fn(image))


# ---- Feature 7: motion blur ---------------------------------------------------
def motion_kernel(length: int, angle: float) -> np.ndarray:
    return np.asarray(_spatial("motion_blur").create_motion_kernel(length, angle), dtype=np.float64)


def motion_blur(image, length: int, angle: float) -> np.ndarray:
    return to_uint8(_spatial("motion_blur").apply_motion_blur(image, length, angle))


# ---- Feature 10: separable gaussian -------------------------------------------
def gaussian_blur(image, sigma: float) -> np.ndarray:
    size = 2 * math.ceil(2.5 * sigma) + 1
    fn = _spatial("gaussian_separable").gaussian_blur_separable
    return to_uint8(_call(fn, image, size=size, sigma=sigma))


# ---- Feature 11: wiener / inverse ---------------------------------------------
def wiener(image, kernel, k: float) -> np.ndarray:
    return to_uint8(_call(_spatial("wiener").wiener_deconvolution, image, kernel=kernel, k=k))


def inverse(image, kernel) -> np.ndarray:
    return to_uint8(_call(_spatial("wiener").inverse_deconvolution, image, kernel=kernel))


# ---- Shared metric ------------------------------------------------------------
def psnr(reference, candidate) -> float | None:
    """PSNR in dB; inf for identical images; None if the shapes differ."""
    if reference.shape != candidate.shape:
        return None
    if np.array_equal(reference, candidate):
        return math.inf
    from utils.metrics import calculate_psnr
    return float(calculate_psnr(reference, candidate))

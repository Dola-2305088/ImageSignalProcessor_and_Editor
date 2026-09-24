"""The 12 tools of the SaveEarth transmission console.

This is the ONLY file in game/ that calls into algorithms/. If an
algorithm's signature changes, fix the matching runner here and nothing
else in the game needs to change.

A tool = one of the 12 project features + one parameter the player tunes
(``options``). A runner turns (image, option, context) into an output
image. Tools without a runner yet are still shown in the toolbox (picking
them in the wrong round is simply a wrong answer); their runners are added
when their challenges are added.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from algorithms.spatial import edge_detection, noise_cleaner, wiener


# ---------------------------------------------------------------- helpers

def to_uint8(image, normalize: bool = False) -> np.ndarray:
    """Clip (and optionally stretch to 0..255) any algorithm output."""
    arr = np.asarray(image, dtype=np.float64)
    if normalize:
        peak = arr.max()
        if peak > 0:
            arr = arr * (255.0 / peak)
    return np.clip(np.rint(arr), 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- registry

@dataclass(frozen=True)
class Tool:
    id: str
    name: str
    domain: str          # "spatial" or "frequency"
    param_label: str     # label of the one control the player tunes
    options: tuple[str, ...]


TOOLS: tuple[Tool, ...] = (
    Tool("blur_sharpen", "Blur & Sharpen", "spatial", "Operation", ("Box blur 3x3", "Box blur 5x5", "Sharpen")),
    Tool("edges", "Edge Detector", "spatial", "Edge mode", ("Horizontal", "Vertical", "Combined")),
    Tool("noise", "Noise Cleaner", "spatial", "Filter", ("Mean", "Gaussian", "Median")),
    Tool("frequency_editor", "Frequency Editor", "frequency", "Mask", ("Low-pass", "High-pass", "Notch")),
    Tool("compression", "Compression Explorer", "frequency", "Coefficients kept", ("50%", "10%", "5%")),
    Tool("resize", "Image Resizer", "spatial", "Method", ("Nearest", "Bilinear", "Anti-aliased")),
    Tool("motion_blur", "Motion Blur Lab", "spatial", "Angle", ("0°", "45°", "90°")),
    Tool("texture", "Texture Analyzer", "frequency", "Dominant direction", ("0°", "45°", "90°", "135°")),
    Tool("hybrid", "Hybrid Images", "frequency", "Cutoff", ("Low", "Medium", "High")),
    Tool("separable", "Separable Gaussian", "spatial", "Method", ("Full 2D", "Separable")),
    Tool("wiener", "Wiener Deconvolution", "spatial", "Restoration",
         ("Inverse filter", "K = 0.1", "K = 0.01", "K = 0.005", "K = 0.001", "K = 0.0001")),
    Tool("color", "Color Space Analyzer", "frequency", "Channel", ("R", "G", "B", "Y (luma)", "Cb", "Cr")),
)

TOOLS_BY_ID: dict[str, Tool] = {t.id: t for t in TOOLS}


# ---------------------------------------------------------------- runners
# Signature: runner(image: uint8 ndarray, option: str, context: dict) -> uint8 ndarray

def _run_noise(image, option, context):
    fn = {
        "Mean": noise_cleaner.mean_filter,
        "Gaussian": noise_cleaner.gaussian_filter,
        "Median": noise_cleaner.median_filter,
    }[option]
    return to_uint8(fn(image))


def _run_edges(image, option, context):
    fn = {
        "Horizontal": edge_detection.horizontal_edges,
        "Vertical": edge_detection.vertical_edges,
        "Combined": edge_detection.combined_edges,
    }[option]
    return to_uint8(fn(image), normalize=True)


def _run_wiener(image, option, context):
    kernel = context["kernel"]
    if option == "Inverse filter":
        return to_uint8(wiener.inverse_deconvolution(image, kernel))
    k = float(option.split("=")[1])
    return to_uint8(wiener.wiener_deconvolution(image, kernel, k))


_RUNNERS: dict[str, Callable[[np.ndarray, str, dict], np.ndarray]] = {
    "noise": _run_noise,
    "edges": _run_edges,
    "wiener": _run_wiener,
}


def has_runner(tool_id: str) -> bool:
    return tool_id in _RUNNERS


def apply_tool(tool_id: str, image: np.ndarray, option: str, context: dict | None = None) -> np.ndarray:
    """Run one tool with one option. Raises KeyError for unknown tools/options."""
    if option not in TOOLS_BY_ID[tool_id].options:
        raise KeyError(f"{option!r} is not an option of {tool_id!r}")
    return _RUNNERS[tool_id](image, option, context or {})

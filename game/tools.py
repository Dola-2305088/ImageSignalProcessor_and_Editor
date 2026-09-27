"""The 12 tools of the SaveEarth transmission console.

This is the ONLY file in game/ that calls into algorithms/. Frequency
tools go through the Discover lesson backends (algorithms/learning/),
which wrap Shreya's algorithms/frequency code, so the game shows exactly
what the lessons teach. If an
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

from algorithms.learning.frequency_trace import CompressionTrace, HybridTrace, MaskTrace
from algorithms.learning.spectrum_trace import spectrum_picture
from algorithms.learning.texture_colour_trace import ColourTrace
from algorithms.spatial import blur_sharpen, edge_detection, motion_blur, noise_cleaner, wiener


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
    Tool("frequency_editor", "Frequency Editor", "frequency", "Mask",
         ("Low-pass · small circle", "Low-pass · large circle",
          "High-pass · small circle", "High-pass · large circle")),
    Tool("compression", "Compression Explorer", "frequency", "Coefficients kept",
         ("50%", "25%", "10%", "5%", "1%")),
    Tool("resize", "Image Resizer", "spatial", "Method", ("Nearest", "Bilinear", "Anti-aliased")),
    Tool("motion_blur", "Motion Blur Lab", "spatial", "Angle", ("0°", "45°", "90°")),
    Tool("texture", "Texture Analyzer", "frequency", "Repeat spacing",
         ("6 px", "8 px", "12 px", "16 px", "24 px")),
    Tool("hybrid", "Hybrid Images", "frequency", "Recipe",
         ("Planet near · comet far", "Comet near · planet far")),
    Tool("separable", "Separable Gaussian", "spatial", "Method", ("Full 2D", "Separable")),
    Tool("wiener", "Wiener Deconvolution", "spatial", "Restoration",
         ("Inverse filter", "K = 0.1", "K = 0.01", "K = 0.005", "K = 0.001", "K = 0.0001")),
    Tool("color", "Color Space Analyzer", "frequency", "Operation",
         ("R channel", "G channel", "B channel", "Y (luma)",
          "Subsample chroma 4×", "Subsample luma 4×")),
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


def _run_blur_sharpen(image, option, context):
    if option == "Sharpen":
        return to_uint8(blur_sharpen.sharpen_image(image))
    size = int(option.split()[-1].split("x")[0])          # "Box blur 5x5" -> 5
    return to_uint8(blur_sharpen.blur_image(image, size))


MOTION_LENGTH = 11


def _run_motion_blur(image, option, context):
    angle = int(option.rstrip("°"))
    return to_uint8(motion_blur.apply_motion_blur(image, MOTION_LENGTH, angle))


def _run_wiener(image, option, context):
    kernel = context["kernel"]
    if option == "Inverse filter":
        return to_uint8(wiener.inverse_deconvolution(image, kernel))
    k = float(option.split("=")[1])
    return to_uint8(wiener.wiener_deconvolution(image, kernel, k))


# Mask radii for a 128 x 128 image: "small" keeps only the slowest waves,
# "large" keeps everything but the finest detail.
MASK_RADIUS = {"small": 8, "large": 24}
HYBRID_CUTOFF = 10


def _run_frequency_editor(image, option, context):
    kind, size = option.split(" · ")
    radius = MASK_RADIUS[size.split()[0]]
    return MaskTrace(image).apply(radius, high_pass=kind == "High-pass")["image"]


def _run_compression(image, option, context):
    return CompressionTrace(image).at_percent(float(option.rstrip("%")))["image"]


def _run_hybrid(image, option, context):
    planet, comet = context["planet"], context["comet"]
    near, far = (planet, comet) if option.startswith("Planet near") else (comet, planet)
    return HybridTrace(near, far, size=near.shape[0]).build(HYBRID_CUTOFF)["hybrid"]


def _run_texture(image, option, context):
    # The analyzer's evidence is the spectrum; the answer is the option.
    return spectrum_picture(np.fft.fft2(np.asarray(image, dtype=np.float64)))


def _grey_rgb(channel):
    grey = np.clip(np.round(np.asarray(channel, dtype=np.float64)), 0, 255).astype(np.uint8)
    return np.dstack([grey, grey, grey])


def _run_color(image, option, context):
    trace = ColourTrace(image)
    if option.startswith("Subsample"):
        target = "chroma" if "chroma" in option else "luma"
        return trace.damage(target, 4)["image"]
    channel = {"R channel": trace.red, "G channel": trace.green,
               "B channel": trace.blue, "Y (luma)": trace.y}[option]
    return _grey_rgb(channel)   # always RGB, so every option compares like-for-like


_RUNNERS: dict[str, Callable[[np.ndarray, str, dict], np.ndarray]] = {
    "noise": _run_noise,
    "edges": _run_edges,
    "wiener": _run_wiener,
    "blur_sharpen": _run_blur_sharpen,
    "motion_blur": _run_motion_blur,
    "frequency_editor": _run_frequency_editor,
    "compression": _run_compression,
    "hybrid": _run_hybrid,
    "texture": _run_texture,
    "color": _run_color,
}


def has_runner(tool_id: str) -> bool:
    return tool_id in _RUNNERS


def apply_tool(tool_id: str, image: np.ndarray, option: str, context: dict | None = None) -> np.ndarray:
    """Run one tool with one option. Raises KeyError for unknown tools/options."""
    if option not in TOOLS_BY_ID[tool_id].options:
        raise KeyError(f"{option!r} is not an option of {tool_id!r}")
    return _RUNNERS[tool_id](image, option, context or {})

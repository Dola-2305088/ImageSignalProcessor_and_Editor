"""SaveEarth challenges.

A challenge = what the aliens send (``received``) + what they want back.

Building a challenge runs EVERY option of the correct tool once and caches
the outputs and their PSNR scores. That makes three things cheap later:
  * Transmit is a dictionary lookup (no heavy work while the player waits)
  * the UI can preview any option instantly
  * the results screen can show "Median 38 dB vs Mean 24 dB" to explain why

Two judging modes:
  "restore" - the aliens want the clean scene back. Score = PSNR(player, clean).
              The best option defines the bar; anything within
              RESTORE_TOLERANCE_DB of the best also passes.
  "match"   - the aliens want a specific transformed image (e.g. outlines).
              Score = PSNR(player, target made with the correct option).
              Passes at MATCH_THRESHOLD_DB or above.

Builders only use algorithms/ through game.tools (and the motion kernel /
convolution for creating the degraded input). Random noise uses a seeded
generator so a given seed always rebuilds the same game.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from algorithms.spatial.convolution import convolve2d
from algorithms.spatial.motion_blur import create_motion_kernel
from game.tools import TOOLS_BY_ID, apply_tool, to_uint8
from utils.metrics import calculate_psnr

RESTORE_TOLERANCE_DB = 1.0
MATCH_THRESHOLD_DB = 35.0


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    """Shared project PSNR, guarded for identical images."""
    if np.array_equal(a, b):
        return float("inf")
    return float(calculate_psnr(a, b))


@dataclass
class Challenge:
    id: str
    title: str
    riddle: str               # what the aliens "say" (shown after glyph decoding)
    hint: str                 # shown after a strike; points back to Discover
    correct_tool: str
    mode: str                 # "restore" or "match"
    received: np.ndarray      # image the aliens send
    reference: np.ndarray     # clean scene (restore) or target image (match)
    outputs: dict[str, np.ndarray] = field(default_factory=dict)  # option -> output
    scores: dict[str, float] = field(default_factory=dict)        # option -> PSNR vs reference
    best_option: str = ""
    pass_db: float = 0.0
    context: dict = field(default_factory=dict)
    variant: str = ""

    @property
    def tool(self):
        return TOOLS_BY_ID[self.correct_tool]

    def passes(self, option: str) -> bool:
        return self.scores[option] >= self.pass_db


# ---------------------------------------------------------------- building helpers

def _evaluate_all(ch: Challenge) -> Challenge:
    """Run every option of the correct tool on the received image and score it."""
    for option in ch.tool.options:
        out = apply_tool(ch.correct_tool, ch.received, option, ch.context)
        ch.outputs[option] = out
        ch.scores[option] = psnr(ch.reference, out)
    ch.best_option = max(ch.scores, key=ch.scores.get)
    if ch.mode == "restore":
        ch.pass_db = ch.scores[ch.best_option] - RESTORE_TOLERANCE_DB
    return ch


def _salt_pepper(image: np.ndarray, rng: np.random.Generator, amount: float) -> np.ndarray:
    out = image.copy()
    mask = rng.random(image.shape)
    out[mask < amount / 2] = 0
    out[mask > 1 - amount / 2] = 255
    return out


def _gaussian_noise(image: np.ndarray, rng: np.random.Generator, sigma: float) -> np.ndarray:
    return to_uint8(image.astype(np.float64) + rng.normal(0.0, sigma, image.shape))


# ---------------------------------------------------------------- the challenges
# Each tool has several variants, so a 5-round game never repeats a puzzle
# and the correct SETTING changes too (the player can't memorize one answer).

# A Gaussian-noise variant was tried and dropped: on this cartoon-like scene
# the median filter beats averaging even on Gaussian noise (it keeps edges
# crisp), so the textbook answer would be judged wrong.
NOISE_VARIANTS = ("salt_pepper",)
EDGE_VARIANTS = ("combined", "horizontal", "vertical")
WIENER_VARIANTS = ("horizontal", "vertical", "diagonal")


def build_noise(clean: np.ndarray, rng: np.random.Generator, variant: str = "salt_pepper") -> Challenge:
    title = "The Burning Stars"
    riddle = ("Your transmission is infested with burning white and black stars that do not "
              "belong to your sky. Remove them, but do not melt the picture.")
    hint = ("Isolated extreme pixels are outliers. Averaging smears them; one filter ignores them. "
            "Revisit Discover → Noise Cleaner.")
    received = _salt_pepper(clean, rng, amount=float(rng.uniform(0.06, 0.10)))
    return _evaluate_all(Challenge(
        id="noise", variant=variant, title=title, riddle=riddle, hint=hint,
        correct_tool="noise", mode="restore", received=received, reference=clean,
    ))


_EDGE_TEXT = {
    "combined": ("Eyes of Outline",
                 "Our eyes do not see light, only boundaries. Send us every outline of your world, "
                 "in all directions.",
                 "Combined"),
    "horizontal": ("The Horizon Seers",
                   "We only perceive boundaries that lie flat, like your horizon. Send us only those.",
                   "Horizontal"),
    "vertical": ("The Pillar Watchers",
                 "We only perceive boundaries that stand upright, like pillars. Send us only those.",
                 "Vertical"),
}


def build_edges(clean: np.ndarray, rng: np.random.Generator, variant: str = "combined") -> Challenge:
    title, riddle, option = _EDGE_TEXT[variant]
    ch = Challenge(
        id="edges", variant=variant, title=title, riddle=riddle,
        hint=("Boundaries are where brightness changes sharply. Which direction of change do they "
              "want? Revisit Discover → Edge Detector."),
        correct_tool="edges", mode="match", received=clean,
        reference=apply_tool("edges", clean, option),
    )
    ch.pass_db = MATCH_THRESHOLD_DB
    return _evaluate_all(ch)


_WIENER_TEXT = {
    "horizontal": ("The Spinning Planet", 0,
                   "Your planet spun while you took this picture, and cosmic static crept in."),
    "vertical": ("The Falling Ship", 90,
                 "Your camera fell as the picture was taken, and cosmic static crept in."),
    "diagonal": ("The Diagonal Comet", 45,
                 "A comet dragged your camera sideways and up, and cosmic static crept in."),
}


def build_wiener(clean: np.ndarray, rng: np.random.Generator, variant: str = "horizontal") -> Challenge:
    title, angle, story = _WIENER_TEXT[variant]
    length = int(rng.choice([9, 11, 13]))
    kernel = create_motion_kernel(length, angle)
    blurred = to_uint8(convolve2d(clean, kernel))
    return _evaluate_all(Challenge(
        id="wiener", variant=variant, title=title,
        riddle=f"{story} We know exactly how it moved. Undo the motion, but beware the static.",
        hint=("Dividing by the blur directly explodes the noise. You need a restoration that is "
              "regularized against noise. Revisit Discover → Wiener Deconvolution."),
        correct_tool="wiener", mode="restore",
        received=_gaussian_noise(blurred, rng, sigma=float(rng.uniform(3, 6))),
        reference=clean, context={"kernel": kernel, "length": length, "angle": angle},
    ))


CHALLENGE_BUILDERS: dict[str, Callable[..., Challenge]] = {
    "noise": build_noise,
    "edges": build_edges,
    "wiener": build_wiener,
}

CHALLENGE_VARIANTS: dict[str, tuple[str, ...]] = {
    "noise": NOISE_VARIANTS,
    "edges": EDGE_VARIANTS,
    "wiener": WIENER_VARIANTS,
}

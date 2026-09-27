"""SaveEarth challenges.

A challenge = what the aliens send (``received``) + what they want back.

Building a challenge runs EVERY option of the correct tool once and caches
the outputs and their PSNR scores. That makes three things cheap later:
  * Transmit is a dictionary lookup (no heavy work while the player waits)
  * the UI can preview any option instantly
  * the results screen can show "Median 38 dB vs Mean 24 dB" to explain why

Three judging modes:
  "restore" - the aliens want the clean scene back. Score = PSNR(player, clean).
              The best option defines the bar; anything within
              RESTORE_TOLERANCE_DB of the best also passes.
  "match"   - the aliens want a specific transformed image (e.g. outlines).
              Score = PSNR(player, target made with the correct option).
              Passes at MATCH_THRESHOLD_DB or above.
  "choice"  - the answer is a measurement, not an image (texture spacing).
              Exactly one option is correct; the output shown is the
              evidence (the spectrum), and no PSNR is reported.

Builders only use algorithms/ through game.tools (and the motion kernel /
convolution for creating the degraded input). Random noise uses a seeded
generator so a given seed always rebuilds the same game.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from algorithms.learning.frequency_trace import HybridTrace
from algorithms.learning.texture_colour_trace import TextureTrace
from algorithms.spatial.convolution import convolve2d
from algorithms.spatial.motion_blur import create_motion_kernel
from game.tools import TOOLS_BY_ID, apply_tool, to_uint8
from ui.learning.palette import LUT
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
    mode: str                 # "restore", "match" or "choice"
    received: np.ndarray      # image the aliens send
    reference: np.ndarray     # clean scene (restore) or target image (match)
    outputs: dict[str, np.ndarray] = field(default_factory=dict)  # option -> output
    scores: dict[str, float] = field(default_factory=dict)        # option -> PSNR vs reference
    best_option: str = ""
    pass_db: float = 0.0
    context: dict = field(default_factory=dict)
    variant: str = ""
    discover_route: tuple[str, str] | None = None   # (route key, button label)
    answer_note: str = ""                           # extra explanation after the round

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
        if ch.mode == "choice":
            ch.scores[option] = float("inf") if option == ch.best_option else 0.0
        else:
            ch.scores[option] = psnr(ch.reference, out)
    if ch.mode == "choice":
        ch.pass_db = 1.0
        return ch
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
        discover_route=("learn_noise", "Noise lesson"),
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
        discover_route=("learn_convolution", "Convolution lesson"),
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
        discover_route=("learn_restore", "Restoration lesson"),
    ))


_BLUR_TEXT = {
    "soft": ("The Gentle Ones",
             "Your edges are too sharp for our young ones. Soften your world just a little, "
             "averaging each point with only its nearest neighbours.",
             "Box blur 3x3"),
    "dream": ("The Dreamers",
              "We see the universe as in a dream: every point melted into a wide ring of its "
              "neighbours. Soften your world much more.",
              "Box blur 5x5"),
    "crisp": ("The Sharp-Eyed",
              "Your picture looks soft to us. Make every edge crisper by pushing each point "
              "away from the average of its neighbours.",
              "Sharpen"),
}


def build_blur_sharpen(clean, rng, variant="soft"):
    title, riddle, option = _BLUR_TEXT[variant]
    ch = Challenge(
        id="blur_sharpen", variant=variant, title=title, riddle=riddle,
        hint=("Averaging neighbours blurs, and a bigger neighbourhood blurs more; subtracting "
              "the neighbours sharpens. Revisit Discover → Convolution."),
        correct_tool="blur_sharpen", mode="match", received=clean,
        reference=apply_tool("blur_sharpen", clean, option),
        discover_route=("learn_convolution", "Convolution lesson"),
    )
    ch.pass_db = MATCH_THRESHOLD_DB
    return _evaluate_all(ch)


_MOTION_TEXT = {
    "sideways": ("The Passing Ship",
                 "Show us your planet as our ship sees it while racing past it sideways, "
                 "smeared from left to right.", "0°"),
    "falling": ("The Falling Probe",
                "Show us your planet as our probe sees it while dropping straight down past it, "
                "smeared from top to bottom.", "90°"),
    "slanting": ("The Slanting Dive",
                 "Show us your planet as our lander sees it while diving past on a slant, "
                 "smeared along the diagonal.", "45°"),
}


def build_motion_blur(clean, rng, variant="sideways"):
    title, riddle, option = _MOTION_TEXT[variant]
    ch = Challenge(
        id="motion_blur", variant=variant, title=title, riddle=riddle,
        hint=("Motion blur averages along a line in the direction of movement; the kernel's "
              "angle must match it. Revisit Discover → Restoration."),
        correct_tool="motion_blur", mode="match", received=clean,
        reference=apply_tool("motion_blur", clean, option),
        discover_route=("learn_restore", "Restoration lesson"),
    )
    ch.pass_db = MATCH_THRESHOLD_DB
    return _evaluate_all(ch)


# ---------------------------------------------------------------- frequency challenges
# These follow Shreya's Discover lessons (algorithms/learning/), so the
# riddles speak the lessons' language: slow and fast waves, the centre of
# the spectrum, the strongest coefficients, brightness vs colour.

# Route keys of the frequency lessons in the Discover sidebar.
# smoke_test checks they exist in ui/main_window.py.
FILTER_LESSON = ("learn_filter", "Frequency filter lesson")
COMPRESSION_LESSON = ("learn_compression", "Compression lesson")
COLOUR_LESSON = ("learn_colour", "Texture & colour lesson")

_FREQ_TEXT = {
    "very_slow": ("The Slow Giants",
                  "We are enormous and see only the slowest waves of light. Keep just a small "
                  "circle at the very centre of your spectrum and silence everything else.",
                  "Low-pass · small circle"),
    "gentle": ("The Tired Eyes",
               "Your finest ripples tire our eyes, but we still want your shapes. Keep most of "
               "your spectrum around the centre; remove only its outermost, fastest waves.",
               "Low-pass · large circle"),
    "fast": ("The Quick Ones",
             "We live too fast to notice slow shading. Remove the centre of your spectrum and "
             "send only the quick waves that draw your edges.",
             "High-pass · small circle"),
}


def build_frequency_editor(clean, rng, variant="very_slow"):
    title, riddle, option = _FREQ_TEXT[variant]
    ch = Challenge(
        id="frequency_editor", variant=variant, title=title, riddle=riddle,
        hint=("The centre of the spectrum holds the slow waves, the outside holds the fast ones. "
              "Keep the part they asked for, and mind how big the circle is. "
              "Revisit Discover → Frequency filters."),
        correct_tool="frequency_editor", mode="match", received=clean,
        reference=apply_tool("frequency_editor", clean, option),
        discover_route=FILTER_LESSON,
    )
    ch.pass_db = MATCH_THRESHOLD_DB
    return _evaluate_all(ch)


_COMPRESSION_TEXT = {
    "tenth": ("One Tenth", "one tenth", "10%"),
    "twentieth": ("The Narrow Beam", "one twentieth", "5%"),
    "hundredth": ("Whisper Across Stars", "one hundredth", "1%"),
}


def build_compression(clean, rng, variant="tenth"):
    title, fraction, option = _COMPRESSION_TEXT[variant]
    ch = Challenge(
        id="compression", variant=variant, title=title,
        riddle=(f"Our beam is thin. It can carry only {fraction} of your image's frequency "
                f"coefficients. Keep the strongest ones, and not one coefficient more."),
        hint=("An image's energy lives in a few strong coefficients; keep the strongest and "
              "discard the rest. Match the share they can carry. Revisit Discover → Compression."),
        correct_tool="compression", mode="match", received=clean,
        reference=apply_tool("compression", clean, option),
        discover_route=COMPRESSION_LESSON,
    )
    ch.pass_db = MATCH_THRESHOLD_DB
    return _evaluate_all(ch)


_HYBRID_TEXT = {
    "planet_near": ("Two Faces of Aetheris",
                    "Send us one picture. Up close we must see your ringed planet, but from far "
                    "away it must become the comet.",
                    "Planet near · comet far"),
    "comet_near": ("The Hidden Planet",
                   "Send us one picture. Up close we must see the comet, but from far away it "
                   "must become your ringed planet.",
                   "Comet near · planet far"),
}


def build_hybrid(clean, rng, variant="planet_near"):
    title, riddle, option = _HYBRID_TEXT[variant]
    comet = HybridTrace._companion(clean.shape[0])
    gap = np.full((clean.shape[0], 6), 0, dtype=np.uint8)
    ch = Challenge(
        id="hybrid", variant=variant, title=title, riddle=riddle,
        hint=("Up close the eye follows fast waves; from far away only slow waves survive. "
              "The image seen from far must supply the low frequencies. "
              "Revisit Discover → Hybrid images."),
        correct_tool="hybrid", mode="match",
        received=np.hstack([clean, gap, comet]),          # both images, side by side
        reference=clean,  # replaced below
        context={"planet": clean, "comet": comet},
        discover_route=FILTER_LESSON,
    )
    ch.reference = apply_tool("hybrid", ch.received, option, ch.context)
    ch.pass_db = MATCH_THRESHOLD_DB
    return _evaluate_all(ch)


_TEXTURE_TEXT = {
    "cloth": ("Cloth", "an alien cloth, woven from crossing threads", (8, 12)),
    "brick": ("Brick", "a wall from our homeworld, laid in courses", (16, 24)),
    "grass": ("Grass", "the grass of Aetheris, blades leaning together", (6, 8)),
}


def _nearest_option(options, value):
    return min(options, key=lambda o: abs(float(o.split()[0]) - value))


def build_texture(clean, rng, variant="cloth"):
    kind, description, spacings = _TEXTURE_TEXT[variant]
    spacing = int(rng.choice(spacings))
    angle = float(rng.choice([0, 30]))
    texture = TextureTrace(clean.shape[0]).make(kind, spacing, angle)["image"]
    options = TOOLS_BY_ID["texture"].options
    ch = Challenge(
        id="texture", variant=variant, title=f"The {kind} of Aetheris",
        riddle=(f"This is {description}. Tell us how many pixels apart its pattern repeats. "
                f"Read it from the waves, not by guessing."),
        hint=("A repeating pattern makes bright peaks in the spectrum; the further the peak "
              "from the centre, the smaller the spacing. Revisit Discover → Texture."),
        correct_tool="texture", mode="choice", received=texture, reference=texture,
        best_option=_nearest_option(options, spacing),
        answer_note=f"True spacing: {spacing} px.",
        context={"true_spacing": spacing, "angle": angle},
        discover_route=COLOUR_LESSON,
    )
    return _evaluate_all(ch)


_COLOR_TEXT = {
    "luma": ("The Colour-Blind Envoys", "match",
             "We cannot see colour at all, only brightness, weighted the way your own eyes "
             "weigh red, green and blue. Send us just that.",
             "Y (luma)"),
    "chroma": ("The Thin Channel", "restore",
               "Our channel is thin. Make your image smaller the way your JPEG does, "
               "so cleverly that we cannot tell anything was lost.",
               "Subsample chroma 4×"),
}


def build_color(clean, rng, variant="luma"):
    title, mode, riddle, option = _COLOR_TEXT[variant]
    colour = LUT[clean].astype(np.uint8)          # the lesson's colour map on our scene
    ch = Challenge(
        id="color", variant=variant, title=title, riddle=riddle,
        hint=("Brightness (Y) carries the detail; colour (Cb, Cr) can lose resolution almost "
              "unnoticed, which is what JPEG exploits. Revisit Discover → Colour."),
        correct_tool="color", mode=mode, received=colour, reference=colour,
        discover_route=COLOUR_LESSON,
    )
    if mode == "match":
        ch.reference = apply_tool("color", colour, option)
        ch.pass_db = MATCH_THRESHOLD_DB
    return _evaluate_all(ch)


CHALLENGE_BUILDERS: dict[str, Callable[..., Challenge]] = {
    "noise": build_noise,
    "edges": build_edges,
    "wiener": build_wiener,
    "blur_sharpen": build_blur_sharpen,
    "motion_blur": build_motion_blur,
    "frequency_editor": build_frequency_editor,
    "compression": build_compression,
    "hybrid": build_hybrid,
    "texture": build_texture,
    "color": build_color,
}

CHALLENGE_VARIANTS: dict[str, tuple[str, ...]] = {
    "noise": NOISE_VARIANTS,
    "edges": EDGE_VARIANTS,
    "wiener": WIENER_VARIANTS,
    "blur_sharpen": tuple(_BLUR_TEXT),
    "motion_blur": tuple(_MOTION_TEXT),
    "frequency_editor": tuple(_FREQ_TEXT),
    "compression": tuple(_COMPRESSION_TEXT),
    "hybrid": tuple(_HYBRID_TEXT),
    "texture": tuple(_TEXTURE_TEXT),
    "color": tuple(_COLOR_TEXT),
}

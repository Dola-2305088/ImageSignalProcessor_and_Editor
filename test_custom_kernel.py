"""
AETHERIS - Custom kernel test suite (Feature 1: Blur & Sharpen)

Checks apply_custom_kernel() against an independent, vectorized NumPy
reference convolution, plus the edge cases that usually break custom
kernels: kernel flipping, negative results, overflow, RGB channels,
even-sized kernels and input mutation.

Run from the project root:
    python tests/test_custom_kernel.py

Test images are tiny on purpose, because the manual convolution loops
pixel by pixel. The whole suite should finish in a few seconds.
"""

import sys
import time
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.spatial.blur_sharpen import apply_custom_kernel  # noqa: E402


# ============================================================
# Helpers
# ============================================================

RESULTS = []


def check(name, passed, detail=""):
    RESULTS.append((name, bool(passed)))
    tag = "PASS" if passed else "FAIL"
    print(f"[{tag}] {name}" + (f"  ->  {detail}" if detail else ""))


def info(name, detail):
    print(f"[INFO] {name}  ->  {detail}")


def run(image, kernel):
    """Call the project function on a copy, return a float array."""
    out = apply_custom_kernel(image.copy(), np.asarray(kernel, dtype=np.float64))
    return np.asarray(out)


def reference_valid(image, kernel):
    """
    Independent TRUE convolution (kernel flipped), computed only on the
    'valid' interior so border-padding conventions don't matter.
    Works for grayscale (H, W) and colour (H, W, C) images.
    """
    img = image.astype(np.float64)
    k = np.asarray(kernel, dtype=np.float64)[::-1, ::-1]  # flip = convolution
    kh, kw = k.shape
    windows = sliding_window_view(img, (kh, kw), axis=(0, 1))
    if img.ndim == 2:
        return np.einsum("ijkl,kl->ij", windows, k)
    return np.einsum("ijckl,kl->ijc", windows, k)


def interior(arr, kernel):
    kh, kw = np.asarray(kernel).shape
    rh, rw = kh // 2, kw // 2
    return arr[rh: arr.shape[0] - rh, rw: arr.shape[1] - rw]


def max_diff_to_reference(out, ref):
    """
    Compare against the reference, accepting any of the reasonable
    output conventions: raw float, clipped float, or rounded uint8.
    Returns the smallest max-abs-difference among those conventions.
    """
    o = out.astype(np.float64)
    candidates = [ref, np.clip(ref, 0, 255), np.clip(np.round(ref), 0, 255)]
    return min(float(np.max(np.abs(o - c))) for c in candidates)


# ============================================================
# Test images (deterministic)
# ============================================================

rng = np.random.default_rng(220)
GRAY = rng.integers(10, 246, size=(18, 22), dtype=np.uint8)
RGB = rng.integers(10, 246, size=(18, 22, 3), dtype=np.uint8)

IDENTITY = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
BOX3 = np.full((3, 3), 1 / 9)
SHARPEN = [[0, -1, 0], [-1, 5, -1], [0, -1, 0]]
LAPLACIAN = [[0, 1, 0], [1, -4, 1], [0, 1, 0]]


# ============================================================
# 1. Identity kernel must return the image unchanged
# ============================================================

out = run(GRAY, IDENTITY)
check(
    "Identity kernel leaves image unchanged (whole image, incl. borders)",
    out.shape == GRAY.shape and np.max(np.abs(out.astype(float) - GRAY)) <= 0.5,
    f"max difference = {np.max(np.abs(out.astype(float) - GRAY)):.3f}",
)


# ============================================================
# 2. Kernel orientation: convolution must FLIP the kernel
# ============================================================
# A single 1 to the RIGHT of centre. With true convolution:
#     out[i, j] = in[i, j - 1]   (image moves 1 px to the right)
# With correlation (kernel NOT flipped) it would be in[i, j + 1].

SHIFT = [[0, 0, 0], [0, 0, 1], [0, 0, 0]]
out = run(GRAY, SHIFT).astype(float)
inner = out[:, 1:-1]
conv_diff = np.max(np.abs(inner - GRAY[:, :-2]))
corr_diff = np.max(np.abs(inner - GRAY[:, 2:]))

if conv_diff <= 0.5:
    check("Kernel is flipped (true convolution, not correlation)", True)
elif corr_diff <= 0.5:
    check(
        "Kernel is flipped (true convolution, not correlation)",
        False,
        "output matches CORRELATION - the kernel is not being flipped",
    )
else:
    check(
        "Kernel is flipped (true convolution, not correlation)",
        False,
        f"matches neither (conv diff {conv_diff:.2f}, corr diff {corr_diff:.2f})",
    )


# ============================================================
# 3-5. Agreement with the independent reference (interior)
# ============================================================

for name, kernel in [
    ("3x3 box blur (1/9)", BOX3),
    ("3x3 sharpen", SHARPEN),
    ("5x5 random mixed-sign kernel", rng.uniform(-1, 1, size=(5, 5))),
]:
    out = run(GRAY, kernel)
    diff = max_diff_to_reference(interior(out, kernel), reference_valid(GRAY, kernel))
    check(f"{name} matches reference convolution", diff <= 1.0, f"max diff = {diff:.3f}")


# ============================================================
# 6. Non-square odd kernel (optional feature)
# ============================================================

try:
    k13 = [[1 / 3, 1 / 3, 1 / 3]]
    out = run(GRAY, k13)
    diff = max_diff_to_reference(interior(out, k13), reference_valid(GRAY, k13))
    check("1x3 non-square kernel matches reference", diff <= 1.0, f"max diff = {diff:.3f}")
except Exception as error:
    info(
        "1x3 non-square kernel",
        f"not supported ({type(error).__name__}: {error}). "
        "Fine as long as the UI only offers square kernels.",
    )


# ============================================================
# 7. Zero-sum kernel on a flat image must give 0 everywhere
# ============================================================

flat = np.full((12, 14), 128, dtype=np.uint8)
out = run(flat, LAPLACIAN).astype(float)
check(
    "Zero-sum kernel on flat image gives 0 everywhere (incl. borders)",
    np.max(np.abs(out)) <= 0.5,
    f"max |value| = {np.max(np.abs(out)):.3f}",
)


# ============================================================
# 8. Negative results must not wrap around
# ============================================================
# Kernel = -1 at centre. Every result is negative. A uint8 wrap-around
# bug turns -100 into 156, which shows up as random bright noise.

NEG = [[0, 0, 0], [0, -1, 0], [0, 0, 0]]
out = run(GRAY, NEG).astype(float)
if np.allclose(out, 0, atol=0.5):
    check("Negative results are clipped to 0 (no wrap-around)", True)
elif np.allclose(out, -GRAY.astype(float), atol=0.5):
    check("Negative results kept as float (no wrap-around)", True)
elif np.allclose(out, GRAY.astype(float), atol=1.0):
    info("Negative results", "absolute value is taken (|x|). OK if intentional.")
else:
    check(
        "Negative results do not wrap around",
        False,
        f"got values {out.min():.0f}..{out.max():.0f}; expected 0 (clipped). "
        "Likely a uint8 cast without np.clip.",
    )


# ============================================================
# 9. Overflow must not wrap around
# ============================================================
# Un-normalized all-ones kernel (sum 9) on a bright image:
# 200 * 9 = 1800 -> should become 255, NOT 1800 % 256 = 8.

bright = np.full((12, 14), 200, dtype=np.uint8)
ONES = np.ones((3, 3))
out = run(bright, ONES).astype(float)
if np.all(out >= 254.5) and np.all(out <= 255.5):
    check("Overflow is clipped to 255 (no wrap-around)", True)
elif np.allclose(out, 1800, atol=1):
    check("Overflow kept as float (no wrap-around)", True)
elif np.allclose(out, 200, atol=1):
    info("Overflow", "kernel is auto-normalized (sum divided out). OK if intentional.")
else:
    check(
        "Overflow does not wrap around",
        False,
        f"got values {out.min():.0f}..{out.max():.0f}; expected 255",
    )


# ============================================================
# 10. RGB: channels processed independently
# ============================================================

red_only = np.zeros_like(RGB)
red_only[..., 0] = RGB[..., 0]
out = run(red_only, BOX3).astype(float)
check(
    "RGB output has the same shape as input",
    out.shape == RGB.shape,
    f"in {RGB.shape}, out {out.shape}",
)
if out.shape == RGB.shape:
    check(
        "RGB channels don't leak into each other",
        np.max(np.abs(out[..., 1:])) <= 0.5,
        f"max value in G/B = {np.max(np.abs(out[..., 1:])):.3f} (expected 0)",
    )
    diff = max_diff_to_reference(interior(out, BOX3), reference_valid(red_only, BOX3))
    check("RGB box blur matches reference", diff <= 1.0, f"max diff = {diff:.3f}")


# ============================================================
# 11. Brightness preserved by a normalized kernel
# ============================================================

out = run(GRAY, BOX3).astype(float)
mean_shift = abs(out.mean() - GRAY.mean())
check(
    "Normalized kernel (sum = 1) preserves average brightness",
    mean_shift <= 1.5,
    f"mean {GRAY.mean():.2f} -> {out.mean():.2f}",
)


# ============================================================
# 12. Even-sized kernel must be rejected clearly
# ============================================================

try:
    apply_custom_kernel(GRAY.copy(), np.ones((2, 2)) / 4)
    check(
        "Even-sized kernel (2x2) is rejected",
        False,
        "accepted silently - output would be shifted half a pixel. "
        "Raise an error, or make sure the UI never sends even sizes.",
    )
except Exception as error:
    check(
        "Even-sized kernel (2x2) is rejected",
        True,
        f"{type(error).__name__}: {error}",
    )


# ============================================================
# 13. Input image must not be modified (Reset relies on this)
# ============================================================

original = GRAY.copy()
probe = GRAY.copy()
apply_custom_kernel(probe, np.asarray(SHARPEN, dtype=float))
check("Input image is not modified in place", np.array_equal(probe, original))


# ============================================================
# 14. Kernel given as a plain Python list (as UIs often send it)
# ============================================================

try:
    out = np.asarray(apply_custom_kernel(GRAY.copy(), [[0, 0, 0], [0, 1, 0], [0, 0, 0]]))
    check(
        "Kernel as a plain Python list works",
        np.max(np.abs(out.astype(float) - GRAY)) <= 0.5,
    )
except Exception as error:
    info(
        "Kernel as plain list",
        f"not accepted ({type(error).__name__}). "
        "Fine if the UI converts to a NumPy array first.",
    )


# ============================================================
# 15. Output type and speed (information only)
# ============================================================

out = np.asarray(apply_custom_kernel(GRAY.copy(), BOX3))
info("Output dtype", f"{out.dtype}, range {out.min()}..{out.max()}")

speed_img = rng.integers(0, 256, size=(100, 100, 3), dtype=np.uint8)
start = time.perf_counter()
apply_custom_kernel(speed_img, BOX3)
elapsed = time.perf_counter() - start
info("Speed", f"100x100 RGB, 3x3 kernel: {elapsed:.2f} s")


# ============================================================
# Summary
# ============================================================

passed = sum(1 for _, ok in RESULTS if ok)
failed = [name for name, ok in RESULTS if not ok]
print()
print(f"{passed}/{len(RESULTS)} checks passed")
if failed:
    print("Failed:")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)

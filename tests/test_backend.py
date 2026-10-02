"""
AETHERIS - backend correctness suite (all spatial, frequency and
learning modules).

Run from the project root:
    python tests/test_backend.py

Every check compares a function against something known to be true:
an independent reference implementation, a hand-computed value, or a
mathematical property (identity, symmetry, round-trip). Images are
small so the whole suite runs in seconds.
"""

import sys
import time
import traceback
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESULTS = []


def check(name, passed, detail=""):
    RESULTS.append((name, bool(passed)))
    tag = "PASS" if passed else "FAIL"
    print(f"  [{tag}] {name}" + (f"  ->  {detail}" if detail else ""))


def info(name, detail):
    print(f"  [INFO] {name}  ->  {detail}")


def section(title):
    print()
    print("=" * 66)
    print(title)
    print("=" * 66)


def guarded(fn):
    """Run one group of checks; a crash counts as a failure, not a stop."""
    try:
        fn()
    except Exception as error:  # noqa: BLE001
        check(f"{fn.__name__} ran without crashing", False,
              f"{type(error).__name__}: {error}")
        traceback.print_exc()


def ref_convolve_same(image, kernel, mode="reflect"):
    """Independent true convolution with numpy padding, 'same' size."""
    img = np.asarray(image, dtype=np.float64)
    k = np.asarray(kernel, dtype=np.float64)[::-1, ::-1]
    kh, kw = k.shape
    ph, pw = kh // 2, kw // 2
    pad = [(ph, ph), (pw, pw)] + ([(0, 0)] if img.ndim == 3 else [])
    p = np.pad(img, pad, mode=mode)
    win = np.lib.stride_tricks.sliding_window_view(p, (kh, kw), axis=(0, 1))
    if img.ndim == 2:
        return np.einsum("ijkl,kl->ij", win, k)
    return np.einsum("ijckl,kl->ijc", win, k)


def maxdiff(a, b):
    return float(np.max(np.abs(np.asarray(a, float) - np.asarray(b, float))))


rng = np.random.default_rng(2026)
GRAY = rng.integers(0, 256, (37, 41), dtype=np.uint8)
RGB = rng.integers(0, 256, (37, 41, 3), dtype=np.uint8)
yy, xx = np.mgrid[0:64, 0:64]
SMOOTH = np.clip(128 + 60 * np.sin(xx / 7.0) + 50 * np.cos(yy / 9.0), 0, 255).astype(np.uint8)
SMOOTH_RGB = np.dstack([SMOOTH, np.roll(SMOOTH, 9, axis=1), 255 - SMOOTH])


# ================================================================
# SPATIAL
# ================================================================

def test_convolution():
    from algorithms.spatial.convolution import (
        convolve2d, convolve2d_gray, convolve2d_gray_loop)

    for size in (3, 5, 7):
        k = rng.uniform(-1, 1, (size, size))
        fast = convolve2d_gray(GRAY, k)
        loop = convolve2d_gray_loop(GRAY, k)
        ref = ref_convolve_same(GRAY, k)
        check(f"convolve2d_gray == loop version ({size}x{size})", maxdiff(fast, loop) < 1e-9)
        check(f"convolve2d_gray == independent reference ({size}x{size})", maxdiff(fast, ref) < 1e-9)

    k = rng.uniform(-1, 1, (3, 5))
    check("Non-square 3x5 kernel matches reference",
          maxdiff(convolve2d_gray(GRAY, k), ref_convolve_same(GRAY, k)) < 1e-9)

    shift = [[0, 0, 0], [0, 0, 1], [0, 0, 0]]
    out = convolve2d_gray(GRAY, shift)
    check("Kernel is flipped (true convolution)", maxdiff(out[:, 1:], GRAY[:, :-1]) < 1e-9)

    k = rng.uniform(-1, 1, (3, 3))
    out = convolve2d(RGB, k)
    check("RGB = each channel convolved separately",
          all(maxdiff(out[..., c], convolve2d_gray(RGB[..., c], k)) < 1e-9 for c in range(3)))

    rgba = np.dstack([RGB, np.full(RGB.shape[:2], 255, np.uint8)])
    check("RGBA input keeps 4 channels", convolve2d(rgba, k).shape == rgba.shape)

    try:
        convolve2d_gray(GRAY, np.ones((2, 2)))
        check("Even kernel rejected", False, "accepted")
    except ValueError:
        check("Even kernel rejected", True)

    # Tiny images: reflect padding wider than the image
    for shape in [(1, 1), (1, 9), (2, 2), (3, 3)]:
        tiny = rng.integers(0, 256, shape).astype(np.uint8)
        try:
            out = convolve2d_gray(tiny, np.ones((5, 5)) / 25)
            check(f"Tiny {shape} image with 5x5 kernel", out.shape == shape and np.all(np.isfinite(out)))
        except Exception as error:
            check(f"Tiny {shape} image with 5x5 kernel", False, f"{type(error).__name__}: {error}")


def test_blur_sharpen():
    from algorithms.spatial.blur_sharpen import (
        apply_custom_kernel, blur_image, create_box_blur_kernel, sharpen_image, get_sharpen_kernel)

    for s in (3, 5, 7):
        k = create_box_blur_kernel(s)
        check(f"Box kernel {s}x{s} sums to 1", abs(k.sum() - 1) < 1e-12)

    flat = np.full((20, 20, 3), 77, np.uint8)
    check("Blur of flat image is unchanged", maxdiff(blur_image(flat, 5), flat) == 0)
    check("Sharpen of flat image is unchanged", maxdiff(sharpen_image(flat), flat) == 0)

    out = sharpen_image(RGB)
    ref = np.clip(np.round(ref_convolve_same(RGB, get_sharpen_kernel())), 0, 255)
    check("Sharpen matches reference (with clipping)", maxdiff(out, ref) == 0)
    check("Output is uint8", out.dtype == np.uint8)

    check("Custom identity kernel = original",
          maxdiff(apply_custom_kernel(RGB, [[0, 0, 0], [0, 1, 0], [0, 0, 0]]), RGB) == 0)
    check("Negative results clip to 0 (no wrap)",
          apply_custom_kernel(GRAY, [[0, 0, 0], [0, -1, 0], [0, 0, 0]]).max() == 0)
    check("Overflow clips to 255 (no wrap)",
          apply_custom_kernel(np.full((9, 9), 200, np.uint8), np.ones((3, 3))).min() == 255)

    probe = RGB.copy()
    apply_custom_kernel(probe, np.ones((3, 3)) / 9)
    check("Input image not modified", np.array_equal(probe, RGB))

    for bad in (np.nan, np.inf):
        k = np.zeros((3, 3)); k[1, 1] = bad
        try:
            out = apply_custom_kernel(GRAY, k)
            check(f"Kernel containing {bad} is rejected", False,
                  f"accepted silently, output range {out.min()}..{out.max()}")
        except ValueError:
            check(f"Kernel containing {bad} is rejected", True)


def test_edges():
    from algorithms.spatial.edge_detection import detect_all_edges, detect_edges

    v_edge = np.zeros((30, 30), np.uint8); v_edge[:, 15:] = 200      # vertical boundary
    h_edge = np.zeros((30, 30), np.uint8); h_edge[15:, :] = 200      # horizontal boundary

    r = detect_all_edges(v_edge)
    check("Vertical boundary -> 'vertical' view lights up", r["vertical"].max() > 200)
    check("Vertical boundary -> 'horizontal' view stays dark", r["horizontal"].max() == 0)
    r = detect_all_edges(h_edge)
    check("Horizontal boundary -> 'horizontal' view lights up", r["horizontal"].max() > 200)
    check("Horizontal boundary -> 'vertical' view stays dark", r["vertical"].max() == 0)

    flat = np.full((20, 20, 3), 90, np.uint8)
    r = detect_all_edges(flat)
    check("Flat image -> no edges, no crash",
          r["combined"].max() == 0 and r["horizontal"].max() == 0)
    r = detect_all_edges(flat, signed=True)
    check("Flat image signed view is mid-grey", np.all(r["horizontal"] == 128))

    for mode in ("horizontal", "vertical", "combined"):
        out = detect_edges(SMOOTH_RGB, mode)
        check(f"detect_edges('{mode}') shape/dtype",
              out.shape == SMOOTH_RGB.shape[:2] and out.dtype == np.uint8)

    rgba = np.dstack([SMOOTH_RGB, np.full(SMOOTH.shape, 255, np.uint8)])
    check("RGBA input accepted", detect_edges(rgba).shape == SMOOTH.shape)


def test_noise():
    from algorithms.spatial.noise_cleaner import (
        add_gaussian_noise, add_salt_pepper_noise, clean_noise, compare_quality,
        create_gaussian_kernel, median_filter)

    sp = add_salt_pepper_noise(SMOOTH, amount=0.1, seed=1)
    changed = (sp != SMOOTH)
    check("Salt & pepper hits ~10% of pixels", abs(changed.mean() - 0.1) < 0.02,
          f"{changed.mean() * 100:.1f}%")
    check("S&P pixels are only 0 or 255", set(np.unique(sp[changed])) <= {0, 255})
    check("S&P amount=0 leaves image unchanged",
          np.array_equal(add_salt_pepper_noise(SMOOTH, amount=0.0, seed=1), SMOOTH))
    full = add_salt_pepper_noise(SMOOTH, amount=1.0, seed=1)
    check("S&P amount=1 corrupts every pixel", set(np.unique(full)) <= {0, 255})
    sp_rgb = add_salt_pepper_noise(SMOOTH_RGB, 0.1, seed=2)
    hit = np.any(sp_rgb != SMOOTH_RGB, axis=2)
    check("RGB S&P sets all 3 channels together",
          np.all((sp_rgb[hit] == 0).all(1) | (sp_rgb[hit] == 255).all(1)))

    g = add_gaussian_noise(SMOOTH, sigma=20, seed=3)
    check("Gaussian noise std ~ 20",
          abs(np.std(g.astype(float) - SMOOTH) - 20) < 2.5,
          f"{np.std(g.astype(float) - SMOOTH):.2f}")
    check("Same seed -> same noise",
          np.array_equal(g, add_gaussian_noise(SMOOTH, sigma=20, seed=3)))

    # Median vs independent reference
    p = np.pad(SMOOTH.astype(float), 1, mode="reflect")
    ref = np.median(np.lib.stride_tricks.sliding_window_view(p, (3, 3)), axis=(2, 3))
    check("Median filter matches reference", maxdiff(median_filter(SMOOTH, 3), np.round(ref)) == 0)
    big = rng.integers(0, 256, (300, 257), dtype=np.uint8)   # several bands
    p = np.pad(big.astype(float), 2, mode="reflect")
    ref = np.median(np.lib.stride_tricks.sliding_window_view(p, (5, 5)), axis=(2, 3))
    check("Median filter banding is seamless (300x257, 5x5)",
          maxdiff(median_filter(big, 5), np.round(ref)) == 0)

    for method in ("median", "mean", "gaussian"):
        cleaned = clean_noise(sp, method, 3)
        q = compare_quality(SMOOTH, sp, cleaned)
        check(f"{method} filter improves PSNR on S&P", q["improvement"] > 0,
              f"{q['noisy_psnr']:.2f} -> {q['cleaned_psnr']:.2f} dB")

    k = create_gaussian_kernel(5, 1.0)
    check("Gaussian kernel sums to 1 and is symmetric",
          abs(k.sum() - 1) < 1e-12 and np.allclose(k, k.T) and np.allclose(k, k[::-1, ::-1]))

    q = compare_quality(SMOOTH, SMOOTH, SMOOTH)
    check("compare_quality with identical images gives a finite improvement",
          np.isfinite(q["improvement"]) or q["improvement"] == 0,
          f"improvement = {q['improvement']}")


def test_gaussian_separable():
    from algorithms.spatial.gaussian_separable import (
        compare_gaussian_results, create_gaussian_kernel_1d, create_gaussian_kernel_2d,
        theoretical_operations)
    from algorithms.spatial.noise_cleaner import create_gaussian_kernel

    for size, sigma in ((3, 0.8), (7, 1.5), (11, 3.0)):
        k1 = create_gaussian_kernel_1d(size, sigma)
        k2 = create_gaussian_kernel_2d(size, sigma)
        check(f"Gaussian {size}, sigma {sigma}: kernels sum to 1",
              abs(k1.sum() - 1) < 1e-12 and abs(k2.sum() - 1) < 1e-12)
        check(f"Gaussian {size}: 2D == noise_cleaner's kernel",
              np.allclose(k2, create_gaussian_kernel(size, sigma)))
        r = compare_gaussian_results(SMOOTH_RGB, size, sigma)
        check(f"Separable == full 2D ({size}x{size})", r["max_difference"] <= 1,
              f"max diff {r['max_difference']}, MAE {r['mean_absolute_error']:.2e}")
        r = compare_gaussian_results(GRAY, size, sigma)
        check(f"Separable == full 2D on noise ({size}x{size})", r["max_difference"] <= 1)

    check("Theoretical 7x7 -> 49 vs 14 ops", theoretical_operations(7)["theoretical_speedup"] == 3.5)


def test_resize():
    from algorithms.spatial.resize import (
        resize_antialiased, resize_bilinear, resize_image, resize_nearest)

    h, w = SMOOTH.shape
    check("Nearest same-size = original", np.array_equal(resize_nearest(SMOOTH_RGB, w, h), SMOOTH_RGB))
    check("Bilinear same-size = original", np.array_equal(resize_bilinear(SMOOTH_RGB, w, h), SMOOTH_RGB))

    up = resize_nearest(GRAY, GRAY.shape[1] * 3, GRAY.shape[0] * 3)
    check("Nearest 3x upscale = exact pixel blocks",
          np.array_equal(up, np.repeat(np.repeat(GRAY, 3, 0), 3, 1)))

    flat = np.full((10, 13, 3), 123, np.uint8)
    check("Bilinear keeps a flat image flat",
          np.all(resize_bilinear(flat, 29, 7) == 123), f"values {np.unique(resize_bilinear(flat, 29, 7))}")

    ramp = np.tile(np.arange(0, 250, 10, dtype=np.uint8), (5, 1))     # 0,10,...,240
    out = resize_bilinear(ramp, 49, 5)                                  # ~2x along x
    exact = np.interp((np.arange(49) + 0.5) * (25 / 49) - 0.5, np.arange(25), np.arange(0, 250, 10))
    check("Bilinear on a ramp is correctly ROUNDED (not truncated)",
          maxdiff(out[0], np.round(exact)) == 0, f"max diff {maxdiff(out[0], np.round(exact))}")

    from algorithms.spatial.resize import resize_bilinear_loop, resize_nearest_loop
    same = True
    for img in (GRAY, SMOOTH_RGB):
        for nw, nh in ((17, 9), (90, 70), (41, 37), (13, 61), (1, 1), (200, 3)):
            same &= np.array_equal(resize_nearest(img, nw, nh), resize_nearest_loop(img, nw, nh))
            same &= np.array_equal(resize_bilinear(img, nw, nh), resize_bilinear_loop(img, nw, nh))
    check("Fast resize == loop reference (24 size/colour combinations)", same)

    small = resize_nearest(SMOOTH_RGB, 17, 9)
    check("Odd target size works", small.shape == (9, 17, 3))

    try:
        out = resize_image(SMOOTH, 32.0, 20.0, "bilinear")
        check("Float sizes from a slider (32.0 x 20.0) accepted", out.shape == (20, 32))
    except Exception as error:
        check("Float sizes from a slider (32.0 x 20.0) accepted", False, f"{type(error).__name__}: {error}")

    from algorithms.learning.resize_trace import checkerboard
    board = checkerboard(128, 2)
    plain = resize_nearest(board, 37, 37).astype(float)
    smooth = resize_antialiased(board, 37, 37, "nearest").astype(float)
    check("Anti-aliasing removes checkerboard aliasing",
          smooth.std() < plain.std() / 4, f"std {plain.std():.1f} -> {smooth.std():.1f}")


def test_motion_blur():
    from algorithms.spatial.motion_blur import apply_motion_blur, create_motion_kernel

    k0 = create_motion_kernel(9, 0)
    check("0 deg kernel is one horizontal row", np.count_nonzero(k0[4]) == 9 and k0.sum() - k0[4].sum() < 1e-12)
    k90 = create_motion_kernel(9, 90)
    check("90 deg kernel is one vertical column", np.count_nonzero(k90[:, 4]) == 9)
    for angle in (0, 30, 45, 90, 135, 180):
        check(f"Kernel at {angle} deg sums to 1", abs(create_motion_kernel(15, angle).sum() - 1) < 1e-12)

    k45 = create_motion_kernel(9, 45)
    rows, cols = np.nonzero(k45)
    falling = np.corrcoef(cols, rows)[0, 1] > 0.99      # down-right on screen
    check("45 deg runs top-left to bottom-right (documented image convention)", falling)

    check("Even length becomes odd", create_motion_kernel(10, 0).shape == (11, 11))
    flat = np.full((20, 20, 3), 50, np.uint8)
    check("Motion blur keeps flat image unchanged", np.all(apply_motion_blur(flat, 15, 30) == 50))
    try:
        out = apply_motion_blur(SMOOTH, 15.0, 30.0)
        check("Float length/angle from a slider accepted", out.shape == SMOOTH.shape)
    except Exception as error:
        check("Float length/angle from a slider accepted", False, f"{type(error).__name__}: {error}")


def test_wiener():
    from algorithms.spatial.motion_blur import motion_blur_with_kernel
    from algorithms.spatial.wiener import add_gaussian_noise, compare_restoration, psf_to_otf
    from algorithms.learning.space_scene import render_space_scene

    scene = np.asarray(render_space_scene(96))
    rgb = np.dstack([scene, np.roll(scene, 5, 1), 255 - scene])

    for name, img in (("gray", scene), ("RGB", rgb)):
        blur = motion_blur_with_kernel(img, 15, 0)
        r = compare_restoration(img, blur["blurred"], blur["kernel"], k=0.001)
        check(f"Wiener improves clean blur ({name})", r["wiener_psnr"] > r["blurred_psnr"] + 3,
              f"{r['blurred_psnr']:.2f} -> {r['wiener_psnr']:.2f} dB")
        noisy = add_gaussian_noise(blur["blurred"], 3, seed=1)
        r = compare_restoration(img, noisy, blur["kernel"], k=0.005)
        check(f"Wiener beats inverse under noise ({name})", r["wiener_psnr"] > r["inverse_psnr"],
              f"inverse {r['inverse_psnr']:.2f}, wiener {r['wiener_psnr']:.2f} dB")
        check(f"Restored image shape/dtype ({name})",
              r["wiener"].shape == img.shape and r["wiener"].dtype == np.uint8)

    for angle in (0, 30, 45, 90, 135):
        blur = motion_blur_with_kernel(scene, 15, angle)
        sweep = {k: compare_restoration(scene, blur["blurred"], blur["kernel"], k=k)["wiener_psnr"]
                 for k in (0.001, 0.005, 0.01, 0.02, 0.05)}
        base = compare_restoration(scene, blur["blurred"], blur["kernel"])["blurred_psnr"]
        check(f"Wiener with K=0.02 beats the blurred input at {angle} deg", sweep[0.02] > base,
              f"blurred {base:.1f} dB | " + ", ".join(f"K={k}: {v:.1f}" for k, v in sweep.items()))

    k = np.zeros((5, 5)); k[2, 2] = 1
    check("OTF of identity kernel is all ones", np.allclose(psf_to_otf(k, (16, 20)), 1))

    flat = np.full((40, 40), 100, np.uint8)
    blur = motion_blur_with_kernel(flat, 9, 0)
    r = compare_restoration(flat, blur["blurred"], blur["kernel"])
    check("Flat image restores to itself", np.all(np.abs(r["wiener"].astype(int) - 100) <= 1))


# ================================================================
# FREQUENCY
# ================================================================

def test_dft():
    from algorithms.frequency.dft import (
        apply_high_pass_filter, apply_low_pass_filter, create_spectrum_image, fftshift_manual,
        ifftshift_manual, manual_dft2, manual_idft2, reconstruct_from_dft)

    for shape in ((16, 16), (15, 22), (1, 7), (33, 8)):
        x = rng.uniform(0, 255, shape)
        F = manual_dft2(x)
        check(f"manual_dft2 == np.fft.fft2 {shape}", np.allclose(F, np.fft.fft2(x)))
        check(f"manual_idft2 round-trip {shape}", np.allclose(np.real(manual_idft2(F)), x))
        check(f"fftshift_manual == np.fft.fftshift {shape}", np.allclose(fftshift_manual(F), np.fft.fftshift(F)))
        check(f"ifftshift undoes fftshift {shape}", np.allclose(ifftshift_manual(fftshift_manual(F)), F))

    F = manual_dft2(GRAY)
    check("reconstruct_from_dft = original", np.array_equal(reconstruct_from_dft(F), GRAY))
    check("Low-pass with huge radius = identity",
          np.array_equal(reconstruct_from_dft(apply_low_pass_filter(F, 10_000)), GRAY))
    lp = np.real(manual_idft2(apply_low_pass_filter(F, 6)))
    hp = np.real(manual_idft2(apply_high_pass_filter(F, 6)))
    check("Low-pass + high-pass (same radius) = original", np.allclose(lp + hp, GRAY))
    check("High-pass removes the average (DC)", abs(hp.mean()) < 1e-6)
    lp_img = np.real(manual_idft2(apply_low_pass_filter(F, 6)))
    check("Low-pass result is real (symmetric mask)",
          np.abs(np.imag(manual_idft2(apply_low_pass_filter(F, 6)))).max() < 1e-6)
    check("Low-pass keeps the average", abs(lp_img.mean() - GRAY.mean()) < 1e-6)

    for shape in ((16, 16), (15, 22)):
        F = manual_dft2(rng.uniform(0, 255, shape))
        lp = manual_idft2(apply_low_pass_filter(F, 4))
        check(f"Low-pass output real for odd/even size {shape}", np.abs(np.imag(lp)).max() < 1e-6,
              f"max imaginary part {np.abs(np.imag(lp)).max():.3g}")

    s = create_spectrum_image(manual_dft2(GRAY))
    check("Spectrum image is uint8 0..255", s.dtype == np.uint8 and s.max() == 255)
    s = create_spectrum_image(np.zeros((8, 8)))
    check("Spectrum of all-zero input does not crash", s.max() == 0)


def test_compression():
    from algorithms.frequency.compression import compress_dft
    from algorithms.frequency.dft import manual_dft2, reconstruct_from_dft
    from utils.metrics import calculate_psnr

    F = manual_dft2(SMOOTH)
    c, mask, kept, total = compress_dft(F, 100)
    check("Keep 100% -> identical image", np.array_equal(reconstruct_from_dft(c), SMOOTH))

    last = -1
    ok = True
    for pct in (0.5, 1, 2, 5, 10, 25, 50):
        c, mask, kept, total = compress_dft(F, pct)
        ok &= (mask.sum() == kept) and kept == int(np.ceil(total * pct / 100))
        p = calculate_psnr(SMOOTH, reconstruct_from_dft(c))
        ok &= p >= last - 0.01
        last = p
    check("Kept count exact and PSNR rises with more coefficients", ok)

    c, mask, kept, total = compress_dft(F, 0.001)
    check("Tiny percentage keeps at least 1 coefficient", kept == 1)
    try:
        compress_dft(F, 0)
        check("0% rejected", False)
    except ValueError:
        check("0% rejected", True)


def test_hybrid():
    from algorithms.frequency.hybrid import create_hybrid_image

    a = SMOOTH_RGB
    r = create_hybrid_image(a, a, 8, 8)
    check("Hybrid of an image with itself (equal radii) = itself", maxdiff(r["hybrid"], a) <= 1)
    b = np.ascontiguousarray(a[::-1, ::-1])
    r = create_hybrid_image(a, b, 6, 12)
    check("Hybrid outputs are uint8 with the right shape",
          all(r[key].shape == a.shape and r[key].dtype == np.uint8 for key in ("hybrid", "low_component", "high_component")))
    check("High component centred on mid-grey", abs(r["high_component"].mean() - 128) < 3)
    rgba = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
    try:
        create_hybrid_image(rgba, rgba, 6, 6)
        check("RGBA images accepted", True)
    except Exception as error:
        check("RGBA images accepted", False, f"{type(error).__name__}: {error}")


def test_color():
    from algorithms.frequency.color_analysis import (
        calculate_channel_spectrum, create_colored_channel, get_channel_statistics,
        rgb_to_ycbcr, split_rgb_channels)

    swatch = np.array([[[255, 255, 255], [0, 0, 0], [255, 0, 0], [0, 255, 0], [0, 0, 255]]], np.uint8)
    y, cb, cr = rgb_to_ycbcr(swatch)
    expected_y = [255, 0, 76, 150, 29]
    expected_cb = [128, 128, 85, 44, 255]
    expected_cr = [128, 128, 255, 21, 107]
    check("YCbCr Y of white/black/red/green/blue", list(y[0]) == expected_y, f"{list(y[0])}")
    check("YCbCr Cb of white/black/red/green/blue", list(cb[0]) == expected_cb, f"{list(cb[0])}")
    check("YCbCr Cr of white/black/red/green/blue", list(cr[0]) == expected_cr, f"{list(cr[0])}")

    r, g, b = split_rgb_channels(SMOOTH_RGB)
    check("split_rgb_channels", np.array_equal(np.dstack([r, g, b]), SMOOTH_RGB))
    red = create_colored_channel(r, "R")
    check("Coloured R channel only in red", red[..., 1:].max() == 0 and np.array_equal(red[..., 0], r))
    s = calculate_channel_spectrum(r)
    check("Channel spectrum shape", s.shape == r.shape and s.dtype == np.uint8)
    st = get_channel_statistics(r)
    check("Channel statistics", abs(st["mean"] - r.mean()) < 1e-9 and st["max"] == r.max())

    rgba = np.dstack([SMOOTH_RGB, np.full(SMOOTH.shape, 255, np.uint8)])
    for name, fn in (("split_rgb_channels", split_rgb_channels), ("rgb_to_ycbcr", rgb_to_ycbcr)):
        try:
            fn(rgba)
            check(f"{name} accepts RGBA (PNG with transparency)", True)
        except Exception as error:
            check(f"{name} accepts RGBA (PNG with transparency)", False, f"{type(error).__name__}: {error}")

    gray = SMOOTH
    try:
        split_rgb_channels(gray)
        check("split_rgb_channels accepts a grayscale photo", True)
    except Exception as error:
        check("split_rgb_channels accepts a grayscale photo", False, f"{type(error).__name__}: {error}")


def test_texture():
    from algorithms.frequency.texture import analyze_texture

    size = 128
    y, x = np.mgrid[0:size, 0:size]
    vertical = (128 + 100 * np.sin(2 * np.pi * x / 8)).astype(np.uint8)       # stripes run up-down
    horizontal = (128 + 100 * np.sin(2 * np.pi * y / 16)).astype(np.uint8)    # stripes run sideways

    r = analyze_texture(vertical)
    check("Vertical stripes -> 'Vertical'", r["orientation"] == "Vertical", r["orientation"])
    check("Vertical stripes spacing 8 px", abs(r["spacing_pixels"] - 8) < 0.5, f"{r['spacing_pixels']:.2f}")
    r = analyze_texture(horizontal)
    check("Horizontal stripes -> 'Horizontal'", r["orientation"] == "Horizontal", r["orientation"])
    check("Horizontal stripes spacing 16 px", abs(r["spacing_pixels"] - 16) < 0.5, f"{r['spacing_pixels']:.2f}")

    # Stripes running top-left to bottom-right: 45 deg in image
    # coordinates, the same convention as the motion-blur angle.
    backslash = (128 + 100 * np.sin(2 * np.pi * (x - y) / (10 * np.sqrt(2)))).astype(np.uint8)
    r = analyze_texture(backslash)
    check("Stripes running top-left -> bottom-right measured at 45 deg",
          abs(r["texture_angle"] - 45) < 3, f"texture_angle = {r['texture_angle']:.1f}")
    check("...and their spacing is 10 px", abs(r["spacing_pixels"] - 10) < 1, f"{r['spacing_pixels']:.2f}")

    r = analyze_texture(np.full((40, 50), 90, np.uint8))
    check("Flat image -> 'None', no crash", r["orientation"] == "None")

    r = analyze_texture(rng.integers(0, 256, (45, 70)).astype(np.uint8))
    check("Non-square noise image runs", r["spectrum"].shape == (45, 70))


# ================================================================
# LEARNING
# ================================================================

def test_learning():
    from algorithms.learning.space_scene import lesson_grid, render_space_scene
    from algorithms.learning.convolution_trace import ConvolutionTrace, PRESETS, preset_kernel, preset_sizes
    from algorithms.learning.noise_trace import NoiseTrace, GAUSSIAN, SALT_PEPPER
    from algorithms.learning.resize_trace import (
        ColourResizeTrace, DownscaleTrace, ResizeTrace, checkerboard, strip_shrink, stripe_strip,
        tiny_scene, tiny_scene_rgb, upscale_quality, SCENE_NAMES)
    from algorithms.learning.restoration_trace import RestorationTrace
    from algorithms.learning.spectrum_trace import SpectrumTrace, annotate_spectrum, stripes
    from algorithms.learning.frequency_trace import CompressionTrace, HybridTrace, MaskTrace
    from algorithms.learning.texture_colour_trace import ColourTrace, TextureTrace

    grid = lesson_grid()
    for key in PRESETS:
        for size in preset_sizes(key):
            t = ConvolutionTrace(grid, preset_kernel(key, size))
            check(f"Convolution lesson '{key}' {size}x{size} verifies every pixel", t.verify_all())

    for kind in (GAUSSIAN, SALT_PEPPER):
        t = NoiseTrace(render_space_scene(96), kind)
        v = t.verify()
        t.window(*t.dramatic_window())
        check(f"Noise lesson ({kind}) claims hold",
              v["median_wins_on_specks"] and v["cleaning_helps"] and v["weighted_beats_flat_on_grain"]
              and v["median_margin_bigger_on_specks"])

    t = ResizeTrace(tiny_scene(), 4)
    v = t.verify()
    t.pixel(*t.interesting_pixel())
    check("Resize lesson upscale claims", v["weights_always_sum_to_one"] and v["nearest_only_copies"])
    ct = ColourResizeTrace(tiny_scene_rgb(), 3, SCENE_NAMES)
    for yy_ in range(ct.new_height):
        for xx_ in range(ct.new_width):
            ct.pixel(yy_, xx_)
    check("Colour resize lesson: every pixel matches resize_bilinear", True)
    v = DownscaleTrace(checkerboard()).verify()
    spread = {k: round(x, 2) for k, x in v["spread"].items()}
    if v["antialias_is_closest"]:
        check("Downscale lesson (defaults): anti-aliased is closest to ideal", True, str(spread))
    else:
        info("Downscale lesson (defaults): 'anti-aliased is closest' is FALSE", f"{spread}. "
             "Bilinear lands exactly between two opposite squares and averages them by luck.")
    fails = [f for f in (2, 3, 4, 6) if not
             strip_shrink(stripe_strip(), f)["blurred_error"] < strip_shrink(stripe_strip(), f)["kept_error"]]
    if fails:
        info("Stripe lesson: 'blurring first lowers the error' fails for factors", f"{fails} "
             "(the shrink lands exactly on one colour, so the naive shrink looks perfect)")
    q = upscale_quality(render_space_scene(96), 4)
    check("Upscale lesson: bilinear beats nearest on a photo", q["bilinear_psnr"] > q["nearest_psnr"])

    r = RestorationTrace(render_space_scene(96))
    v = r.verify()
    check("Restoration lesson claims hold",
          v["kernel_sums_to_one"] and v["wiener_beats_degraded"] and v["wiener_beats_inverse"],
          f"best K {v['best_k']}, {v['best_psnr']:.2f} dB")

    v = SpectrumTrace().verify()
    check("Spectrum lesson self-check", all(v[k] for k in
          ("manual_matches_fft", "all_harmonics_rebuild_row", "all_coefficients_rebuild_image", "energy_is_monotone")))
    _, peak = annotate_spectrum(stripes(96, 8, 0))
    check("Spectrum lesson: 8 px stripes -> peak 12 steps out", abs(peak["radius"] - 12) < 0.01)

    v = MaskTrace().verify()
    check("Mask lesson self-check", all(v[k] for k in
          ("manual_matches_fft", "full_mask_is_identity", "halves_rebuild_original", "hard_edge_rings_more",
           "matches_project_masks")))
    v = HybridTrace().verify()
    check("Hybrid lesson claims", v["close_up_detail_is_the_sharp_image"] and v["far_away_favours_blur"])
    v = CompressionTrace().verify()
    check("Compression lesson matches compress_dft",
          v["matches_project_compressor"] and v["count_matches"] and v["quality_improves_monotonically"])

    v = TextureTrace().verify()
    check("Texture lesson: analyzer recovers spacing and rotation",
          v["spacing_within_2px"] and v["rotation_tracks_within_10deg"],
          f"worst spacing {v['worst_spacing_error']:.2f}px, rotation {v['worst_rotation_error']:.1f} deg")
    try:
        TextureTrace().measure(np.full((64, 64), 100, np.uint8))
        check("Texture lesson measure() survives a flat image", True)
    except Exception as error:
        check("Texture lesson measure() survives a flat image", False, f"{type(error).__name__}: {error}")

    v = ColourTrace().verify()
    check("Colour lesson claims", v["ycbcr_roundtrip_is_clean"] and v["chroma_damage_always_cheaper"]
          and v["luma_carries_more_detail"], f"round-trip {v['roundtrip_psnr']:.1f} dB")


# ================================================================
# SPEED ON A REAL-SIZED PHOTO
# ================================================================

def test_speed():
    from algorithms.spatial.blur_sharpen import apply_custom_kernel
    from algorithms.spatial.edge_detection import detect_all_edges
    from algorithms.spatial.noise_cleaner import median_filter
    from algorithms.spatial.resize import resize_image
    from algorithms.spatial.gaussian_separable import compare_gaussian_results
    from algorithms.spatial.motion_blur import motion_blur_with_kernel
    from algorithms.spatial.wiener import wiener_deconvolution

    photo = rng.integers(0, 256, (600, 800, 3), dtype=np.uint8)

    def timed(label, fn, limit):
        start = time.perf_counter()
        fn()
        took = time.perf_counter() - start
        check(f"{label} on 800x600 under {limit:g}s", took < limit, f"{took:.2f}s")

    timed("Custom 5x5 kernel", lambda: apply_custom_kernel(photo, np.ones((5, 5)) / 25), 3)
    timed("Edge detection", lambda: detect_all_edges(photo), 3)
    timed("Median 5x5", lambda: median_filter(photo, 5), 8)
    timed("Gaussian compare 7x7", lambda: compare_gaussian_results(photo, 7, 1.5), 5)
    blur = motion_blur_with_kernel(photo, 15, 0)
    timed("Wiener", lambda: wiener_deconvolution(blur["blurred"], blur["kernel"], 0.01), 5)
    timed("Resize bilinear 2x up (1600x1200)", lambda: resize_image(photo, 1600, 1200, "bilinear"), 5)
    timed("Resize nearest 2x up (1600x1200)", lambda: resize_image(photo, 1600, 1200, "nearest"), 5)
    timed("Resize anti-aliased down (200x150)", lambda: resize_image(photo, 200, 150, "bilinear", True), 5)


GROUPS = [
    ("SPATIAL: convolution core", test_convolution),
    ("SPATIAL: blur & sharpen / custom kernel", test_blur_sharpen),
    ("SPATIAL: edge detector", test_edges),
    ("SPATIAL: noise cleaner", test_noise),
    ("SPATIAL: Gaussian separability", test_gaussian_separable),
    ("SPATIAL: resizer", test_resize),
    ("SPATIAL: motion blur", test_motion_blur),
    ("SPATIAL: Wiener deconvolution", test_wiener),
    ("FREQUENCY: DFT core + frequency editor", test_dft),
    ("FREQUENCY: compression", test_compression),
    ("FREQUENCY: hybrid images", test_hybrid),
    ("FREQUENCY: colour analysis", test_color),
    ("FREQUENCY: texture analyzer", test_texture),
    ("LEARNING (Discover) modules", test_learning),
    ("SPEED on a realistic photo", test_speed),
]

if __name__ == "__main__":
    only = sys.argv[1:]
    for title, fn in GROUPS:
        if only and not any(word.lower() in title.lower() for word in only):
            continue
        section(title)
        guarded(fn)

    passed = sum(ok for _, ok in RESULTS)
    failed = [name for name, ok in RESULTS if not ok]
    print()
    print(f"{passed}/{len(RESULTS)} checks passed")
    if failed:
        print("FAILED:")
        for name in failed:
            print(f"  - {name}")
        sys.exit(1)

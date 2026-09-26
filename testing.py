from PIL import Image
import numpy as np

from algorithms.spatial.wiener import (
    wiener_deconvolution,
    inverse_deconvolution,
    add_gaussian_noise,
    compare_restoration
)

from utils.metrics import calculate_psnr


# ============================================================
# LOAD FEATURE 7 RESULTS
# ============================================================

original = np.array(
    Image.open(
        "test_images/motion_original.png"
    ).convert("RGB")
)


blurred = np.array(
    Image.open(
        "test_images/motion_for_wiener.png"
    ).convert("RGB")
)


kernel = np.load(
    "test_images/motion_kernel.npy"
)


print("\n=== INPUT INFORMATION ===")

print(
    "Original shape:",
    original.shape
)

print(
    "Blurred shape:",
    blurred.shape
)

print(
    "Kernel shape:",
    kernel.shape
)

print(
    "Kernel sum:",
    kernel.sum()
)


# ============================================================
# TEST 1: CLEAN MOTION BLUR
# ============================================================

print(
    "\n=== CLEAN MOTION BLUR RESTORATION ==="
)


# Try Wiener
wiener_clean = wiener_deconvolution(
    blurred,
    kernel,
    k=0.01
)


# Try naive inverse
inverse_clean = inverse_deconvolution(
    blurred,
    kernel,
    epsilon=0.02
)


Image.fromarray(
    inverse_clean
).save(
    "test_images/inverse_restored_clean.png"
)


Image.fromarray(
    wiener_clean
).save(
    "test_images/wiener_restored_clean.png"
)


print(
    "Blurred PSNR:",
    calculate_psnr(
        original,
        blurred
    )
)

print(
    "Inverse PSNR:",
    calculate_psnr(
        original,
        inverse_clean
    )
)

print(
    "Wiener PSNR:",
    calculate_psnr(
        original,
        wiener_clean
    )
)


# ============================================================
# TEST 2: ADD NOISE TO BLURRED IMAGE
# ============================================================

noisy_blurred = add_gaussian_noise(
    blurred,
    sigma=3.0,
    seed=42
)


Image.fromarray(
    noisy_blurred
).save(
    "test_images/motion_blurred_noisy.png"
)


print(
    "\n=== NOISY MOTION BLUR RESTORATION ==="
)


# ------------------------------------------------------------
# NAIVE INVERSE
# ------------------------------------------------------------

inverse_noisy = inverse_deconvolution(
    noisy_blurred,
    kernel,
    epsilon=0.02
)


# ------------------------------------------------------------
# WIENER
# ------------------------------------------------------------
wiener_noisy = wiener_deconvolution(
    noisy_blurred,
    kernel,
    k=0.001
)


Image.fromarray(
    inverse_noisy
).save(
    "test_images/inverse_restored_noisy.png"
)


Image.fromarray(
    wiener_noisy
).save(
    "test_images/wiener_restored_noisy.png"
)


print(
    "Noisy blurred PSNR:",
    calculate_psnr(
        original,
        noisy_blurred
    )
)

print(
    "Inverse filtered PSNR:",
    calculate_psnr(
        original,
        inverse_noisy
    )
)

print(
    "Wiener restored PSNR:",
    calculate_psnr(
        original,
        wiener_noisy
    )
)


# ============================================================
# TRY DIFFERENT K VALUES
# ============================================================

print(
    "\n=== WIENER K PARAMETER TEST ==="
)


k_values = [
    0.0001,
    0.001,
    0.005,
    0.01,
    0.02,
    0.05,
    0.1
]


best_psnr = -float("inf")
best_k = None
best_image = None


for k in k_values:

    restored = wiener_deconvolution(
        noisy_blurred,
        kernel,
        k=k
    )

    psnr = calculate_psnr(
        original,
        restored
    )

    print(
        f"K = {k:<7} "
        f"PSNR = {psnr:.4f} dB"
    )

    if psnr > best_psnr:

        best_psnr = psnr
        best_k = k
        best_image = restored


Image.fromarray(
    best_image
).save(
    "test_images/wiener_best.png"
)


print(
    "\nBest K:",
    best_k
)

print(
    "Best Wiener PSNR:",
    best_psnr
)


print(
    "\nWiener deconvolution tests completed."
)
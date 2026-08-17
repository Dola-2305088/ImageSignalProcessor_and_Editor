import numpy as np


def calculate_psnr(original, processed, max_value=255.0):
    """
    Calculate Peak Signal-to-Noise Ratio (PSNR).

    Higher PSNR = reconstructed image is closer to original.
    """

    original = np.asarray(original, dtype=np.float64)
    processed = np.asarray(processed, dtype=np.float64)

    if original.shape != processed.shape:
        raise ValueError(
            "Original and processed images must have the same shape."
        )

    mse = np.mean(
        (original - processed) ** 2
    )

    if mse == 0:
        return float("inf")

    psnr = 10 * np.log10(
        (max_value ** 2) / mse
    )

    return psnr
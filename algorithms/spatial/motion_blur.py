import numpy as np

from algorithms.spatial.convolution import convolve2d
from utils.metrics import calculate_psnr


# ============================================================
# BASIC HELPER
# ============================================================

def clip_image(image):
    """
    Clip image values to [0, 255] and convert to uint8.
    """

    return np.clip(
        image,
        0,
        255
    ).astype(np.uint8)


# ============================================================
# MOTION BLUR KERNEL
# ============================================================

def create_motion_kernel(
    length=15,
    angle=0
):
    """
    Create a normalized line-shaped motion blur kernel.

    Parameters
    ----------
    length : int
        Length of the motion blur.

        Odd values are preferred because our manual
        convolution requires odd kernel dimensions.

    angle : float
        Blur direction in degrees.

        0 degrees   -> horizontal
        45 degrees  -> diagonal
        90 degrees  -> vertical

    Returns
    -------
    numpy.ndarray
        Normalized 2D motion blur kernel.
    """

    if length <= 0:
        raise ValueError(
            "Motion blur length must be positive."
        )

    # Our convolution function expects odd-sized kernels.
    if length % 2 == 0:
        length += 1

    kernel = np.zeros(
        (length, length),
        dtype=np.float64
    )

    center = length // 2

    # Convert angle to radians.
    theta = np.deg2rad(angle)

    # --------------------------------------------------------
    # GENERATE POINTS ALONG A LINE THROUGH THE CENTER
    # --------------------------------------------------------

    half = length // 2

    # Extra samples reduce gaps when the line is diagonal.
    t_values = np.linspace(
        -half,
        half,
        length * 4
    )

    for t in t_values:

        x = int(
            round(
                center
                +
                t * np.cos(theta)
            )
        )

        y = int(
            round(
                center
                +
                t * np.sin(theta)
            )
        )

        if (
            0 <= x < length
            and
            0 <= y < length
        ):
            kernel[y, x] = 1.0

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    total = kernel.sum()

    if total == 0:
        kernel[
            center,
            center
        ] = 1.0

        total = 1.0

    kernel /= total

    return kernel


# ============================================================
# APPLY MOTION BLUR
# ============================================================

def apply_motion_blur(
    image,
    length=15,
    angle=0
):
    """
    Apply motion blur using the project's manual 2D
    convolution implementation.
    """

    kernel = create_motion_kernel(
        length,
        angle
    )

    result = convolve2d(
        image,
        kernel
    )

    return clip_image(result)


# ============================================================
# APPLY + RETURN KERNEL
# ============================================================

def motion_blur_with_kernel(
    image,
    length=15,
    angle=0
):
    """
    Apply motion blur and also return the generated kernel.

    Returning the kernel is important because Wiener
    deconvolution later needs the known blur kernel.
    """

    kernel = create_motion_kernel(
        length,
        angle
    )

    blurred = convolve2d(
        image,
        kernel
    )

    blurred = clip_image(
        blurred
    )

    return {
        "blurred": blurred,
        "kernel": kernel,
        "length": kernel.shape[0],
        "angle": angle
    }


# ============================================================
# QUALITY COMPARISON
# ============================================================

def motion_blur_quality(
    original,
    blurred
):
    """
    Calculate PSNR between original and motion-blurred image.
    """

    psnr = calculate_psnr(
        original,
        blurred
    )

    return {
        "psnr": psnr
    }
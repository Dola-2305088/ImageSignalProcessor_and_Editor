import numpy as np

from algorithms.spatial.convolution import convolve2d
from utils.metrics import calculate_psnr


# ============================================================
# BASIC HELPERS
# ============================================================

def clip_image(image):
    """
    Clip pixel values to [0, 255] and return uint8 image.
    """

    return np.clip(
        image,
        0,
        255
    ).astype(np.uint8)


# ============================================================
# NOISE GENERATION
# ============================================================

def add_gaussian_noise(
    image,
    mean=0.0,
    sigma=20.0,
    seed=None
):
    """
    Add Gaussian noise to an image.

    Parameters
    ----------
    image : numpy.ndarray
        Grayscale or RGB image.

    mean : float
        Mean of Gaussian noise.

    sigma : float
        Standard deviation of Gaussian noise.

    seed : int or None
        Optional random seed for repeatable tests.
    """

    image = np.asarray(
        image,
        dtype=np.float64
    )

    rng = np.random.default_rng(seed)

    noise = rng.normal(
        mean,
        sigma,
        size=image.shape
    )

    noisy_image = image + noise

    return clip_image(noisy_image)


def add_salt_pepper_noise(
    image,
    amount=0.05,
    salt_ratio=0.5,
    seed=None
):
    """
    Add salt-and-pepper noise.

    Parameters
    ----------
    image : numpy.ndarray
        Grayscale or RGB image.

    amount : float
        Fraction of image pixels affected.

        Example:
        0.05 means approximately 5% of pixels.

    salt_ratio : float
        Fraction of corrupted pixels that become white.

        0.5 means:
            50% salt
            50% pepper

    seed : int or None
        Optional random seed.
    """

    if not 0 <= amount <= 1:
        raise ValueError(
            "amount must be between 0 and 1."
        )

    if not 0 <= salt_ratio <= 1:
        raise ValueError(
            "salt_ratio must be between 0 and 1."
        )

    image = np.asarray(image)

    noisy_image = image.copy()

    rows, cols = image.shape[:2]

    total_pixels = rows * cols

    number_noisy = int(
        amount * total_pixels
    )

    number_salt = int(
        number_noisy * salt_ratio
    )

    number_pepper = (
        number_noisy - number_salt
    )

    rng = np.random.default_rng(seed)

    # ========================================================
    # SALT PIXELS
    # ========================================================

    salt_indices = rng.choice(
        total_pixels,
        size=number_salt,
        replace=False
    )

    salt_rows = (
        salt_indices // cols
    )

    salt_cols = (
        salt_indices % cols
    )

    if image.ndim == 2:

        noisy_image[
            salt_rows,
            salt_cols
        ] = 255

    elif image.ndim == 3:

        noisy_image[
            salt_rows,
            salt_cols,
            :
        ] = 255

    else:

        raise ValueError(
            "Unsupported image format."
        )

    # ========================================================
    # PEPPER PIXELS
    # ========================================================

    # Avoid selecting the same locations already used for salt.

    remaining_indices = np.setdiff1d(
        np.arange(total_pixels),
        salt_indices
    )

    number_pepper = min(
        number_pepper,
        len(remaining_indices)
    )

    pepper_indices = rng.choice(
        remaining_indices,
        size=number_pepper,
        replace=False
    )

    pepper_rows = (
        pepper_indices // cols
    )

    pepper_cols = (
        pepper_indices % cols
    )

    if image.ndim == 2:

        noisy_image[
            pepper_rows,
            pepper_cols
        ] = 0

    else:

        noisy_image[
            pepper_rows,
            pepper_cols,
            :
        ] = 0

    return noisy_image.astype(
        np.uint8
    )


# ============================================================
# MEAN / AVERAGING FILTER
# ============================================================

def create_mean_kernel(
    kernel_size=3
):
    """
    Create a normalized averaging kernel.
    """

    if kernel_size <= 0:
        raise ValueError(
            "Kernel size must be positive."
        )

    if kernel_size % 2 == 0:
        raise ValueError(
            "Kernel size must be odd."
        )

    kernel = np.ones(
        (kernel_size, kernel_size),
        dtype=np.float64
    )

    kernel /= kernel.sum()

    return kernel


def mean_filter(
    image,
    kernel_size=3
):
    """
    Remove noise using an averaging filter.

    Uses the project's manual 2D convolution.
    """

    kernel = create_mean_kernel(
        kernel_size
    )

    result = convolve2d(
        image,
        kernel
    )

    return clip_image(result)


# ============================================================
# GAUSSIAN FILTER
# ============================================================

def create_gaussian_kernel(
    kernel_size=5,
    sigma=1.0
):
    """
    Create a normalized 2D Gaussian kernel manually.
    """

    if kernel_size <= 0:
        raise ValueError(
            "Kernel size must be positive."
        )

    if kernel_size % 2 == 0:
        raise ValueError(
            "Kernel size must be odd."
        )

    if sigma <= 0:
        raise ValueError(
            "Sigma must be greater than zero."
        )

    radius = (
        kernel_size // 2
    )

    y, x = np.mgrid[
        -radius:radius + 1,
        -radius:radius + 1
    ]

    kernel = np.exp(
        -(x ** 2 + y ** 2)
        /
        (2 * sigma ** 2)
    )

    kernel /= kernel.sum()

    return kernel


def gaussian_filter(
    image,
    kernel_size=5,
    sigma=1.0
):
    """
    Smooth Gaussian-like noise using Gaussian convolution.
    """

    kernel = create_gaussian_kernel(
        kernel_size,
        sigma
    )

    result = convolve2d(
        image,
        kernel
    )

    return clip_image(result)


# ============================================================
# MANUAL MEDIAN FILTER
# ============================================================

def median_filter_gray(
    image,
    kernel_size=3
):
    """
    Apply a manual median filter to a grayscale image.

    Median filtering is especially effective
    for salt-and-pepper noise.
    """

    image = np.asarray(
        image,
        dtype=np.float64
    )

    if image.ndim != 2:
        raise ValueError(
            "median_filter_gray expects a 2D image."
        )

    if kernel_size <= 0:
        raise ValueError(
            "Kernel size must be positive."
        )

    if kernel_size % 2 == 0:
        raise ValueError(
            "Kernel size must be odd."
        )

    padding = (
        kernel_size // 2
    )

    padded_image = np.pad(
        image,
        (
            (padding, padding),
            (padding, padding)
        ),
        mode="reflect"
    )

    rows, cols = image.shape

    output = np.zeros_like(
        image,
        dtype=np.float64
    )

    for row in range(rows):

        for col in range(cols):

            region = padded_image[
                row:row + kernel_size,
                col:col + kernel_size
            ]

            output[row, col] = np.median(
                region
            )

    return output


def median_filter(
    image,
    kernel_size=3
):
    """
    Apply median filtering to grayscale or RGB images.
    """

    image = np.asarray(image)

    if image.ndim == 2:

        result = median_filter_gray(
            image,
            kernel_size
        )

        return clip_image(result)

    elif image.ndim == 3:

        channels = []

        for channel_index in range(
            image.shape[2]
        ):

            channel = image[
                :,
                :,
                channel_index
            ]

            filtered = median_filter_gray(
                channel,
                kernel_size
            )

            channels.append(
                filtered
            )

        result = np.stack(
            channels,
            axis=2
        )

        return clip_image(result)

    else:

        raise ValueError(
            "Unsupported image format."
        )


# ============================================================
# GENERAL CLEANING INTERFACE
# ============================================================

def clean_noise(
    image,
    method="median",
    kernel_size=3,
    sigma=1.0
):
    """
    General interface for noise-cleaning filters.

    Supported methods:
        median
        mean
        gaussian
    """

    method = method.lower()

    if method == "median":

        return median_filter(
            image,
            kernel_size
        )

    elif method == "mean":

        return mean_filter(
            image,
            kernel_size
        )

    elif method == "gaussian":

        return gaussian_filter(
            image,
            kernel_size,
            sigma
        )

    else:

        raise ValueError(
            "Method must be 'median', 'mean', or 'gaussian'."
        )


# ============================================================
# PSNR COMPARISON
# ============================================================

def compare_quality(
    original,
    noisy,
    cleaned
):
    """
    Compare noisy and cleaned images using the shared
    PSNR utility from utils.metrics.

    Returns
    -------
    dict
        noisy_psnr:
            PSNR between original and noisy image.

        cleaned_psnr:
            PSNR between original and cleaned image.

        improvement:
            Increase in PSNR after cleaning.
    """

    noisy_psnr = calculate_psnr(
        original,
        noisy
    )

    cleaned_psnr = calculate_psnr(
        original,
        cleaned
    )

    improvement = (
        cleaned_psnr
        -
        noisy_psnr
    )

    return {
        "noisy_psnr": noisy_psnr,
        "cleaned_psnr": cleaned_psnr,
        "improvement": improvement
    }
import time
import numpy as np

from algorithms.spatial.convolution import convolve2d


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
# 1D GAUSSIAN KERNEL
# ============================================================

def create_gaussian_kernel_1d(
    kernel_size=5,
    sigma=1.0
):
    """
    Create a normalized 1D Gaussian kernel.

    Example shape for kernel_size=5:

        [a, b, c, b, a]

    The sum of all values is 1.
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

    radius = kernel_size // 2

    x = np.arange(
        -radius,
        radius + 1,
        dtype=np.float64
    )

    kernel = np.exp(
        -(x ** 2)
        /
        (2 * sigma ** 2)
    )

    kernel /= kernel.sum()

    return kernel


# ============================================================
# FULL 2D GAUSSIAN KERNEL
# ============================================================

def create_gaussian_kernel_2d(
    kernel_size=5,
    sigma=1.0
):
    """
    Create a normalized 2D Gaussian kernel.

    A 2D Gaussian is separable:

        G2D = G1D(vertical) × G1D(horizontal)
    """

    kernel_1d = create_gaussian_kernel_1d(
        kernel_size,
        sigma
    )

    kernel_2d = np.outer(
        kernel_1d,
        kernel_1d
    )

    kernel_2d /= kernel_2d.sum()

    return kernel_2d


# ============================================================
# FULL 2D GAUSSIAN BLUR
# ============================================================

def gaussian_blur_2d(
    image,
    kernel_size=5,
    sigma=1.0
):
    """
    Apply Gaussian blur using one full K x K convolution.
    """

    kernel = create_gaussian_kernel_2d(
        kernel_size,
        sigma
    )

    result = convolve2d(
        image,
        kernel
    )

    return clip_image(result)


# ============================================================
# SPECIALIZED 1D CONVOLUTION
# ============================================================

def convolve_horizontal_gray(image, kernel_1d):
    """
    Manual 1D horizontal convolution for a grayscale image.
    """

    image = np.asarray(
        image,
        dtype=np.float64
    )

    kernel_1d = np.asarray(
        kernel_1d,
        dtype=np.float64
    )

    if image.ndim != 2:
        raise ValueError(
            "convolve_horizontal_gray expects a 2D image."
        )

    kernel_size = len(kernel_1d)

    if kernel_size % 2 == 0:
        raise ValueError(
            "Kernel size must be odd."
        )

    padding = kernel_size // 2

    padded = np.pad(
        image,
        (
            (0, 0),
            (padding, padding)
        ),
        mode="reflect"
    )

    rows, cols = image.shape

    output = np.zeros_like(
        image,
        dtype=np.float64
    )

    # Gaussian kernel is symmetric, so flipping does not
    # change it, but this keeps the operation conceptually
    # consistent with convolution.
    flipped_kernel = kernel_1d[::-1]

    for row in range(rows):

        for col in range(cols):

            region = padded[
                row,
                col:col + kernel_size
            ]

            output[row, col] = np.dot(
                region,
                flipped_kernel
            )

    return output


def convolve_vertical_gray(image, kernel_1d):
    """
    Manual 1D vertical convolution for a grayscale image.
    """

    image = np.asarray(
        image,
        dtype=np.float64
    )

    kernel_1d = np.asarray(
        kernel_1d,
        dtype=np.float64
    )

    if image.ndim != 2:
        raise ValueError(
            "convolve_vertical_gray expects a 2D image."
        )

    kernel_size = len(kernel_1d)

    if kernel_size % 2 == 0:
        raise ValueError(
            "Kernel size must be odd."
        )

    padding = kernel_size // 2

    padded = np.pad(
        image,
        (
            (padding, padding),
            (0, 0)
        ),
        mode="reflect"
    )

    rows, cols = image.shape

    output = np.zeros_like(
        image,
        dtype=np.float64
    )

    flipped_kernel = kernel_1d[::-1]

    for row in range(rows):

        for col in range(cols):

            region = padded[
                row:row + kernel_size,
                col
            ]

            output[row, col] = np.dot(
                region,
                flipped_kernel
            )

    return output


def convolve_horizontal(image, kernel_1d):
    """
    Apply horizontal 1D convolution to grayscale or RGB images.
    """

    image = np.asarray(image)

    if image.ndim == 2:

        return convolve_horizontal_gray(
            image,
            kernel_1d
        )

    elif image.ndim == 3:

        channels = []

        for channel_index in range(
            image.shape[2]
        ):

            filtered = convolve_horizontal_gray(
                image[:, :, channel_index],
                kernel_1d
            )

            channels.append(filtered)

        return np.stack(
            channels,
            axis=2
        )

    else:

        raise ValueError(
            "Unsupported image format."
        )


def convolve_vertical(image, kernel_1d):
    """
    Apply vertical 1D convolution to grayscale or RGB images.
    """

    image = np.asarray(image)

    if image.ndim == 2:

        return convolve_vertical_gray(
            image,
            kernel_1d
        )

    elif image.ndim == 3:

        channels = []

        for channel_index in range(
            image.shape[2]
        ):

            filtered = convolve_vertical_gray(
                image[:, :, channel_index],
                kernel_1d
            )

            channels.append(filtered)

        return np.stack(
            channels,
            axis=2
        )

    else:

        raise ValueError(
            "Unsupported image format."
        )

# ============================================================
# SEPARABLE GAUSSIAN BLUR
# ============================================================

def gaussian_blur_separable(
    image,
    kernel_size=5,
    sigma=1.0
):
    """
    Apply Gaussian blur using two specialized
    1D convolution passes.

    Pass 1:
        Horizontal Gaussian convolution.

    Pass 2:
        Vertical Gaussian convolution.
    """

    # Create the 1D Gaussian kernel
    kernel_1d = create_gaussian_kernel_1d(
        kernel_size,
        sigma
    )

    # --------------------------------------------------------
    # PASS 1: HORIZONTAL
    # --------------------------------------------------------

    horizontal_result = convolve_horizontal(
        image,
        kernel_1d
    )

    # --------------------------------------------------------
    # PASS 2: VERTICAL
    # --------------------------------------------------------

    final_result = convolve_vertical(
        horizontal_result,
        kernel_1d
    )

    return clip_image(
        final_result
    )


# ============================================================
# COMPARE RESULTS
# ============================================================

def compare_gaussian_results(
    image,
    kernel_size=5,
    sigma=1.0
):
    """
    Compare full 2D Gaussian convolution against
    separable Gaussian convolution.

    Returns:
        - both images
        - mean absolute error
        - maximum pixel difference
    """

    full_result = gaussian_blur_2d(
        image,
        kernel_size,
        sigma
    )

    separable_result = gaussian_blur_separable(
        image,
        kernel_size,
        sigma
    )

    difference = np.abs(
        full_result.astype(np.float64)
        -
        separable_result.astype(np.float64)
    )

    mean_absolute_error = np.mean(
        difference
    )

    max_difference = np.max(
        difference
    )

    return {
        "full_2d": full_result,
        "separable": separable_result,
        "mean_absolute_error": mean_absolute_error,
        "max_difference": max_difference
    }


# ============================================================
# PERFORMANCE COMPARISON
# ============================================================

def compare_execution_time(
    image,
    kernel_size=5,
    sigma=1.0,
    repetitions=3
):
    """
    Compare execution time of full 2D Gaussian convolution
    and separable Gaussian convolution.

    Multiple repetitions are used to make the measurement
    more stable.
    """

    if repetitions <= 0:
        raise ValueError(
            "repetitions must be positive."
        )

    full_times = []
    separable_times = []

    # --------------------------------------------------------
    # FULL 2D
    # --------------------------------------------------------

    for _ in range(repetitions):

        start = time.perf_counter()

        gaussian_blur_2d(
            image,
            kernel_size,
            sigma
        )

        end = time.perf_counter()

        full_times.append(
            end - start
        )

    # --------------------------------------------------------
    # SEPARABLE
    # --------------------------------------------------------

    for _ in range(repetitions):

        start = time.perf_counter()

        gaussian_blur_separable(
            image,
            kernel_size,
            sigma
        )

        end = time.perf_counter()

        separable_times.append(
            end - start
        )

    full_time = np.mean(
        full_times
    )

    separable_time = np.mean(
        separable_times
    )

    if separable_time > 0:
        speedup = (
            full_time
            /
            separable_time
        )
    else:
        speedup = float("inf")

    return {
        "full_2d_time": full_time,
        "separable_time": separable_time,
        "speedup": speedup
    }


# ============================================================
# THEORETICAL OPERATION COUNT
# ============================================================

def theoretical_operations(
    kernel_size
):
    """
    Compare approximate multiplications per pixel.

    Full 2D:
        K x K = K^2

    Separable:
        K horizontal + K vertical = 2K
    """

    if kernel_size <= 0:
        raise ValueError(
            "Kernel size must be positive."
        )

    full_operations = (
        kernel_size ** 2
    )

    separable_operations = (
        2 * kernel_size
    )

    theoretical_speedup = (
        full_operations
        /
        separable_operations
    )

    return {
        "full_2d_operations_per_pixel":
            full_operations,

        "separable_operations_per_pixel":
            separable_operations,

        "theoretical_speedup":
            theoretical_speedup
    }
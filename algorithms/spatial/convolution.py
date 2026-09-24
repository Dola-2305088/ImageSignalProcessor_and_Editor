import numpy as np


def convolve2d_gray_loop(image, kernel):
    """
    Manual 2D convolution, written as an explicit pixel-by-pixel loop.

    This is the readable reference version: for every output pixel it
    lifts the neighbourhood out of the padded image and multiplies it
    by the flipped kernel. ``convolve2d_gray`` below computes exactly
    the same thing far more quickly; this one is kept for the report
    and for the timing comparison in the separable-Gaussian feature.

    Parameters
    ----------
    image : numpy.ndarray
        2D grayscale image.

    kernel : numpy.ndarray
        2D convolution kernel.

    Returns
    -------
    numpy.ndarray
        Filtered image.
    """

    image = image.astype(np.float64)
    kernel = np.asarray(kernel, dtype=np.float64)

    if image.ndim != 2:
        raise ValueError("convolve2d_gray_loop expects a grayscale 2D image.")

    if kernel.ndim != 2:
        raise ValueError("Kernel must be a 2D matrix.")

    kernel_height, kernel_width = kernel.shape

    if kernel_height % 2 == 0 or kernel_width % 2 == 0:
        raise ValueError("Kernel dimensions must be odd.")

    pad_height = kernel_height // 2
    pad_width = kernel_width // 2

    padded_image = np.pad(
        image,
        (
            (pad_height, pad_height),
            (pad_width, pad_width)
        ),
        mode="reflect"
    )

    output = np.zeros_like(image, dtype=np.float64)

    # Flip kernel because mathematical convolution
    # requires the kernel to be reversed.
    flipped_kernel = np.flip(kernel, axis=(0, 1))

    image_height, image_width = image.shape

    for row in range(image_height):
        for col in range(image_width):

            region = padded_image[
                row: row + kernel_height,
                col: col + kernel_width
            ]

            output[row, col] = np.sum(region * flipped_kernel)

    return output


def convolve2d_gray(image, kernel):
    """
    Manual 2D convolution on a grayscale image.

    Same definition as ``convolve2d_gray_loop``: reflect padding, the
    kernel flipped, then a weighted sum of every neighbourhood. The
    difference is only the order of the work. Instead of walking the
    image pixel by pixel, we walk the *kernel* and add one shifted copy
    of the image per kernel weight:

        output = sum over (i, j) of  flipped[i, j] * padded[i:i+H, j:j+W]

    That is a handful of array operations rather than millions of
    Python iterations, which is what makes the interactive features
    usable on real photographs. The results match the loop version to
    floating-point precision.

    Parameters
    ----------
    image : numpy.ndarray
        2D grayscale image.

    kernel : numpy.ndarray
        2D convolution kernel.

    Returns
    -------
    numpy.ndarray
        Filtered image.
    """

    image = np.asarray(image, dtype=np.float64)
    kernel = np.asarray(kernel, dtype=np.float64)

    if image.ndim != 2:
        raise ValueError("convolve2d_gray expects a grayscale 2D image.")

    if kernel.ndim != 2:
        raise ValueError("Kernel must be a 2D matrix.")

    kernel_height, kernel_width = kernel.shape

    if kernel_height % 2 == 0 or kernel_width % 2 == 0:
        raise ValueError("Kernel dimensions must be odd.")

    pad_height = kernel_height // 2
    pad_width = kernel_width // 2

    padded_image = np.pad(
        image,
        (
            (pad_height, pad_height),
            (pad_width, pad_width)
        ),
        mode="reflect"
    )

    # Flip the kernel, exactly as the loop version does.
    flipped_kernel = np.flip(kernel, axis=(0, 1))

    image_height, image_width = image.shape

    output = np.zeros_like(image, dtype=np.float64)

    for kernel_row in range(kernel_height):
        for kernel_col in range(kernel_width):

            weight = flipped_kernel[kernel_row, kernel_col]

            if weight == 0.0:
                continue

            shifted = padded_image[
                kernel_row: kernel_row + image_height,
                kernel_col: kernel_col + image_width
            ]

            output += weight * shifted

    return output


def convolve2d(image, kernel):
    """
    Apply manual 2D convolution to grayscale or RGB images.

    Grayscale image:
        H x W

    Color image:
        H x W x 3
    """

    image = np.asarray(image)

    if image.ndim == 2:
        return convolve2d_gray(image, kernel)

    elif image.ndim == 3:

        channels = []

        for channel_index in range(image.shape[2]):

            channel = image[:, :, channel_index]

            filtered_channel = convolve2d_gray(
                channel,
                kernel
            )

            channels.append(filtered_channel)

        output = np.stack(channels, axis=2)

        return output

    else:
        raise ValueError("Unsupported image format.")
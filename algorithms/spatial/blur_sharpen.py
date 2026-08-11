import numpy as np

from algorithms.spatial.convolution import convolve2d


def create_box_blur_kernel(size=3):
    """
    Create an averaging/box blur kernel.

    Example for size=3:

    1/9 * [
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]
    ]
    """

    if size <= 0:
        raise ValueError("Kernel size must be positive.")

    if size % 2 == 0:
        raise ValueError("Kernel size must be odd.")

    kernel = np.ones(
        (size, size),
        dtype=np.float64
    )

    kernel = kernel / kernel.sum()

    return kernel


def get_sharpen_kernel():
    """
    Standard sharpening kernel.
    """

    return np.array(
        [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ],
        dtype=np.float64
    )


def clip_image(image):
    """
    Ensure pixel values remain between 0 and 255.
    """

    image = np.clip(image, 0, 255)

    return image.astype(np.uint8)


def blur_image(image, kernel_size=3):
    """
    Blur an image using manual convolution.
    """

    kernel = create_box_blur_kernel(kernel_size)

    result = convolve2d(
        image,
        kernel
    )

    return clip_image(result)


def sharpen_image(image):
    """
    Sharpen an image using manual convolution.
    """

    kernel = get_sharpen_kernel()

    result = convolve2d(
        image,
        kernel
    )

    return clip_image(result)


def apply_custom_kernel(image, kernel):
    """
    Allows a user-defined/custom kernel.

    This will later be connected to Shreya's UI
    so the user can type kernel values.
    """

    kernel = np.asarray(
        kernel,
        dtype=np.float64
    )

    result = convolve2d(
        image,
        kernel
    )

    return clip_image(result)
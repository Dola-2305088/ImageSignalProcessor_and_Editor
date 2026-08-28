import numpy as np

from algorithms.spatial.convolution import convolve2d


SOBEL_X = np.array(
    [
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ],
    dtype=np.float64
)


SOBEL_Y = np.array(
    [
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ],
    dtype=np.float64
)


def to_grayscale(image):
    """
    Convert RGB image to grayscale.
    Leave grayscale input unchanged.
    """

    image = np.asarray(image)

    if image.ndim == 2:
        return image.astype(np.float64)

    if image.ndim == 3 and image.shape[2] >= 3:
        r = image[:, :, 0]
        g = image[:, :, 1]
        b = image[:, :, 2]

        gray = (
            0.299 * r
            + 0.587 * g
            + 0.114 * b
        )

        return gray.astype(np.float64)

    raise ValueError("Unsupported image format.")


def normalize_edge_image(image):
    """
    Normalize an edge response to 0-255.
    """

    image = np.abs(image)

    maximum = np.max(image)

    if maximum == 0:
        return np.zeros_like(
            image,
            dtype=np.uint8
        )

    normalized = (
        image / maximum
    ) * 255

    return normalized.astype(np.uint8)


def horizontal_edges(image):
    """
    Detect horizontal intensity changes.
    """

    gray = to_grayscale(image)

    result = convolve2d(
        gray,
        SOBEL_Y
    )

    return normalize_edge_image(result)


def vertical_edges(image):
    """
    Detect vertical intensity changes.
    """

    gray = to_grayscale(image)

    result = convolve2d(
        gray,
        SOBEL_X
    )

    return normalize_edge_image(result)


def combined_edges(image):
    """
    Compute Sobel edge magnitude.
    """

    gray = to_grayscale(image)

    gx = convolve2d(
        gray,
        SOBEL_X
    )

    gy = convolve2d(
        gray,
        SOBEL_Y
    )

    magnitude = np.sqrt(
        gx ** 2 + gy ** 2
    )

    return normalize_edge_image(
        magnitude
    )


def detect_edges(image, mode="combined"):
    """
    General edge-detection interface.

    mode:
        horizontal
        vertical
        combined
    """

    mode = mode.lower()

    if mode == "horizontal":
        return horizontal_edges(image)

    if mode == "vertical":
        return vertical_edges(image)

    if mode == "combined":
        return combined_edges(image)

    raise ValueError(
        "Mode must be 'horizontal', 'vertical', or 'combined'."
    )
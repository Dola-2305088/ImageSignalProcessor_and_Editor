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


# Edge images are scaled by a high percentile instead of the single
# largest value. One very strong edge (a specular highlight, a dark
# frame border) would otherwise set the gain for the whole picture and
# push every real edge down into the near-black range.
EDGE_PERCENTILE = 99.5


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


def sobel_responses(image):
    """
    Run both Sobel kernels once and return the raw responses.

    Returns
    -------
    gx : ndarray
        Response to SOBEL_X (signed; strong on vertical edges).

    gy : ndarray
        Response to SOBEL_Y (signed; strong on horizontal edges).

    magnitude : ndarray
        sqrt(gx^2 + gy^2).
    """

    gray = to_grayscale(image)

    gx = convolve2d(gray, SOBEL_X)
    gy = convolve2d(gray, SOBEL_Y)

    magnitude = np.sqrt(gx ** 2 + gy ** 2)

    return gx, gy, magnitude


def edge_scale(magnitude):
    """
    Choose one display gain from the magnitude image.

    The same gain is used for the horizontal, vertical and combined
    views, so the three are directly comparable: a weak horizontal
    edge stays weak next to a strong combined edge, instead of every
    view being stretched to its own maximum.
    """

    magnitude = np.abs(np.asarray(magnitude, dtype=np.float64))

    scale = float(np.percentile(magnitude, EDGE_PERCENTILE))

    if scale <= 1e-9:
        scale = float(magnitude.max())

    if scale <= 1e-9:
        return 1.0

    return scale


def scale_edges(response, scale):
    """
    Scale an edge response to a 0-255 image by its magnitude.
    """

    response = np.abs(np.asarray(response, dtype=np.float64))

    scaled = (response / scale) * 255.0

    return np.clip(np.round(scaled), 0, 255).astype(np.uint8)


def signed_edges(response, scale):
    """
    Show a signed response with mid-grey as zero.

    Dark means brightness falling, bright means brightness rising.
    Useful for the horizontal and vertical views, where the sign is
    the direction of the change; the absolute value throws it away.
    """

    response = np.asarray(response, dtype=np.float64)

    scaled = 128.0 + (response / scale) * 127.0

    return np.clip(np.round(scaled), 0, 255).astype(np.uint8)


def normalize_edge_image(image, scale=None):
    """
    Normalize an edge response to 0-255.

    Kept for backwards compatibility. Pass ``scale`` (from
    ``edge_scale``) to keep several views on the same gain.
    """

    image = np.abs(np.asarray(image, dtype=np.float64))

    if scale is None:
        scale = edge_scale(image)

    return scale_edges(image, scale)


def horizontal_edges(image, scale=None, signed=False):
    """
    Detect horizontal intensity changes (SOBEL_Y).
    """

    gx, gy, magnitude = sobel_responses(image)

    if scale is None:
        scale = edge_scale(magnitude)

    if signed:
        return signed_edges(gy, scale)

    return scale_edges(gy, scale)


def vertical_edges(image, scale=None, signed=False):
    """
    Detect vertical intensity changes (SOBEL_X).
    """

    gx, gy, magnitude = sobel_responses(image)

    if scale is None:
        scale = edge_scale(magnitude)

    if signed:
        return signed_edges(gx, scale)

    return scale_edges(gx, scale)


def combined_edges(image, scale=None):
    """
    Compute Sobel edge magnitude.
    """

    gx, gy, magnitude = sobel_responses(image)

    if scale is None:
        scale = edge_scale(magnitude)

    return scale_edges(magnitude, scale)


def detect_edges(image, mode="combined", signed=False):
    """
    General edge-detection interface.

    mode:
        horizontal
        vertical
        combined

    signed:
        Only affects horizontal and vertical. When True the result is
        centred on mid-grey, so the direction of the brightness
        change stays visible.
    """

    mode = mode.lower()

    gx, gy, magnitude = sobel_responses(image)
    scale = edge_scale(magnitude)

    if mode == "horizontal":
        return signed_edges(gy, scale) if signed else scale_edges(gy, scale)

    if mode == "vertical":
        return signed_edges(gx, scale) if signed else scale_edges(gx, scale)

    if mode == "combined":
        return scale_edges(magnitude, scale)

    raise ValueError(
        "Mode must be 'horizontal', 'vertical', or 'combined'."
    )


def detect_all_edges(image, signed=False):
    """
    All three views computed once, sharing a single display gain.

    Convolution runs twice in total instead of six times, which is
    exactly what the comparison view needs.
    """

    gx, gy, magnitude = sobel_responses(image)
    scale = edge_scale(magnitude)

    return {
        "horizontal": signed_edges(gy, scale) if signed else scale_edges(gy, scale),
        "vertical": signed_edges(gx, scale) if signed else scale_edges(gx, scale),
        "combined": scale_edges(magnitude, scale),
        "scale": scale,
        "max_magnitude": float(magnitude.max()),
        "mean_magnitude": float(magnitude.mean()),
    }

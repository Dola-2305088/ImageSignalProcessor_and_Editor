import numpy as np

from algorithms.spatial.gaussian_separable import (
    gaussian_blur_separable
)


# ============================================================
# BASIC HELPERS
# ============================================================

def validate_image(image):
    """
    Validate grayscale or RGB image.
    """

    image = np.asarray(image)

    if image.ndim not in (2, 3):
        raise ValueError(
            "Image must be grayscale (H x W) or color (H x W x C)."
        )

    return image


def validate_size(new_width, new_height):
    """
    Validate requested output dimensions.
    """

    if new_width <= 0 or new_height <= 0:
        raise ValueError(
            "Output width and height must be positive."
        )


def clip_image(image):
    """
    Clip pixel values to [0, 255] and return uint8.
    """

    return np.clip(
        image,
        0,
        255
    ).astype(np.uint8)


# ============================================================
# NEAREST-NEIGHBOR RESIZING
# ============================================================

def resize_nearest(
    image,
    new_width,
    new_height
):
    """
    Resize an image using manual nearest-neighbor interpolation.

    Each destination pixel is mapped back to the closest
    source pixel.
    """

    image = validate_image(image)

    validate_size(
        new_width,
        new_height
    )

    old_height, old_width = image.shape[:2]

    # --------------------------------------------------------
    # CREATE OUTPUT IMAGE
    # --------------------------------------------------------

    if image.ndim == 2:

        output = np.zeros(
            (new_height, new_width),
            dtype=image.dtype
        )

    else:

        output = np.zeros(
            (
                new_height,
                new_width,
                image.shape[2]
            ),
            dtype=image.dtype
        )

    # --------------------------------------------------------
    # SCALE FACTORS
    # --------------------------------------------------------

    scale_x = (
        old_width / new_width
    )

    scale_y = (
        old_height / new_height
    )

    # --------------------------------------------------------
    # MAP EACH OUTPUT PIXEL BACK TO SOURCE
    # --------------------------------------------------------

    for new_y in range(new_height):

        source_y = (
            (new_y + 0.5) * scale_y
            - 0.5
        )

        source_y = int(
            round(source_y)
        )

        source_y = np.clip(
            source_y,
            0,
            old_height - 1
        )

        for new_x in range(new_width):

            source_x = (
                (new_x + 0.5) * scale_x
                - 0.5
            )

            source_x = int(
                round(source_x)
            )

            source_x = np.clip(
                source_x,
                0,
                old_width - 1
            )

            output[
                new_y,
                new_x
            ] = image[
                source_y,
                source_x
            ]

    return output


# ============================================================
# BILINEAR INTERPOLATION
# ============================================================

def resize_bilinear(
    image,
    new_width,
    new_height
):
    """
    Resize an image using manual bilinear interpolation.

    Each destination pixel is estimated from the four
    nearest source pixels.
    """

    image = validate_image(image)

    validate_size(
        new_width,
        new_height
    )

    image_float = image.astype(
        np.float64
    )

    old_height, old_width = image.shape[:2]

    # --------------------------------------------------------
    # CREATE OUTPUT IMAGE
    # --------------------------------------------------------

    if image.ndim == 2:

        output = np.zeros(
            (new_height, new_width),
            dtype=np.float64
        )

    else:

        output = np.zeros(
            (
                new_height,
                new_width,
                image.shape[2]
            ),
            dtype=np.float64
        )

    scale_x = (
        old_width / new_width
    )

    scale_y = (
        old_height / new_height
    )

    # --------------------------------------------------------
    # PROCESS EVERY DESTINATION PIXEL
    # --------------------------------------------------------

    for new_y in range(new_height):

        source_y = (
            (new_y + 0.5) * scale_y
            - 0.5
        )

        # Clamp before selecting neighbours
        source_y = max(
            0.0,
            min(
                source_y,
                old_height - 1
            )
        )

        y0 = int(
            np.floor(source_y)
        )

        y1 = min(
            y0 + 1,
            old_height - 1
        )

        dy = (
            source_y - y0
        )

        for new_x in range(new_width):

            source_x = (
                (new_x + 0.5) * scale_x
                - 0.5
            )

            source_x = max(
                0.0,
                min(
                    source_x,
                    old_width - 1
                )
            )

            x0 = int(
                np.floor(source_x)
            )

            x1 = min(
                x0 + 1,
                old_width - 1
            )

            dx = (
                source_x - x0
            )

            # ------------------------------------------------
            # FOUR NEIGHBOURING SOURCE PIXELS
            #
            # Q00 -------- Q01
            #  |            |
            #  |      P     |
            #  |            |
            # Q10 -------- Q11
            # ------------------------------------------------

            q00 = image_float[
                y0,
                x0
            ]

            q01 = image_float[
                y0,
                x1
            ]

            q10 = image_float[
                y1,
                x0
            ]

            q11 = image_float[
                y1,
                x1
            ]

            # Horizontal interpolation at top
            top = (
                (1 - dx) * q00
                +
                dx * q01
            )

            # Horizontal interpolation at bottom
            bottom = (
                (1 - dx) * q10
                +
                dx * q11
            )

            # Vertical interpolation
            value = (
                (1 - dy) * top
                +
                dy * bottom
            )

            output[
                new_y,
                new_x
            ] = value

    return clip_image(output)


# ============================================================
# ANTI-ALIASING
# ============================================================

def antialias_before_downsampling(
    image,
    new_width,
    new_height
):
    """
    Apply Gaussian low-pass filtering before downsampling.

    Downsampling removes samples.

    Without low-pass filtering, high-frequency information
    may fold into lower frequencies and create aliasing.
    """

    image = validate_image(image)

    validate_size(
        new_width,
        new_height
    )

    old_height, old_width = image.shape[:2]

    scale_x = (
        new_width / old_width
    )

    scale_y = (
        new_height / old_height
    )

    # --------------------------------------------------------
    # IF WE ARE NOT DOWNSAMPLING, ANTI-ALIASING IS NOT NEEDED
    # --------------------------------------------------------

    if (
        scale_x >= 1.0
        and
        scale_y >= 1.0
    ):
        return image.copy()

    smallest_scale = min(
        scale_x,
        scale_y
    )

    # --------------------------------------------------------
    # CHOOSE GAUSSIAN STRENGTH
    #
    # Stronger reduction -> stronger low-pass filtering
    # --------------------------------------------------------

    sigma = max(
        0.8,
        0.5 / max(
            smallest_scale,
            1e-6
        )
    )

    # Approximately +/- 3 sigma
    radius = int(
        np.ceil(
            3 * sigma
        )
    )

    kernel_size = (
        2 * radius + 1
    )

    # Prevent extremely large kernels in this educational
    # manual implementation.
    kernel_size = min(
        kernel_size,
        15
    )

    # Ensure odd size
    if kernel_size % 2 == 0:
        kernel_size += 1

    filtered = gaussian_blur_separable(
        image,
        kernel_size=kernel_size,
        sigma=sigma
    )

    return filtered


# ============================================================
# ANTI-ALIASED RESIZING
# ============================================================

def resize_antialiased(
    image,
    new_width,
    new_height,
    method="bilinear"
):
    """
    Resize with anti-aliasing when downsampling.

    Processing flow:

        Image
          ↓
        Gaussian low-pass filter
          ↓
        Downsample
    """

    filtered = antialias_before_downsampling(
        image,
        new_width,
        new_height
    )

    method = method.lower()

    if method == "nearest":

        return resize_nearest(
            filtered,
            new_width,
            new_height
        )

    elif method == "bilinear":

        return resize_bilinear(
            filtered,
            new_width,
            new_height
        )

    else:

        raise ValueError(
            "Method must be 'nearest' or 'bilinear'."
        )


# ============================================================
# GENERAL RESIZE INTERFACE
# ============================================================

def resize_image(
    image,
    new_width,
    new_height,
    method="bilinear",
    antialias=False
):
    """
    General interface for image resizing.

    Parameters
    ----------
    method:
        "nearest"
        "bilinear"

    antialias:
        Apply Gaussian anti-aliasing before downsampling.
    """

    if antialias:

        return resize_antialiased(
            image,
            new_width,
            new_height,
            method
        )

    method = method.lower()

    if method == "nearest":

        return resize_nearest(
            image,
            new_width,
            new_height
        )

    elif method == "bilinear":

        return resize_bilinear(
            image,
            new_width,
            new_height
        )

    else:

        raise ValueError(
            "Method must be 'nearest' or 'bilinear'."
        )
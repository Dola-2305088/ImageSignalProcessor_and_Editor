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
    Validate requested output dimensions and return them as ints.

    Sizes typed into a field or read from a slider often arrive as
    floats (640.0); array shapes and range() need integers.
    """

    new_width = int(round(float(new_width)))
    new_height = int(round(float(new_height)))

    if new_width <= 0 or new_height <= 0:
        raise ValueError(
            "Output width and height must be positive."
        )

    return new_width, new_height


def clip_image(image):
    """
    Clip pixel values to [0, 255] and return uint8.
    """

    # Round before casting: astype() truncates, which would darken
    # every interpolated pixel by up to one grey level.
    return np.clip(
        np.round(image),
        0,
        255
    ).astype(np.uint8)


# ============================================================
# NEAREST-NEIGHBOR RESIZING
# ============================================================

def resize_nearest_loop(
    image,
    new_width,
    new_height
):
    """
    Resize an image using manual nearest-neighbor interpolation,
    written as an explicit pixel-by-pixel loop.

    This is the readable reference version, kept for the report.
    ``resize_nearest`` below computes exactly the same result far
    more quickly.

    Each destination pixel is mapped back to the closest
    source pixel.
    """

    image = validate_image(image)

    new_width, new_height = validate_size(
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

def resize_bilinear_loop(
    image,
    new_width,
    new_height
):
    """
    Resize an image using manual bilinear interpolation, written as an
    explicit pixel-by-pixel loop.

    This is the readable reference version, kept for the report.
    ``resize_bilinear`` below computes exactly the same result far
    more quickly.

    Each destination pixel is estimated from the four
    nearest source pixels.
    """

    image = validate_image(image)

    new_width, new_height = validate_size(
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
# FAST VERSIONS (same maths, whole rows/columns at once)
# ============================================================
#
# The loop versions above visit every destination pixel in Python:
# about 10 seconds to enlarge an 800 x 600 photo to 1600 x 1200.
# The mapping from destination to source only depends on the row
# (for y) or the column (for x), so it can be computed once per axis
# and applied to the whole image with array indexing. The formulas,
# clamping and rounding are identical to the loops, so the results
# match them exactly; tests/test_backend.py checks this.

def _source_coordinates(new_size, old_size):
    """
    Half-pixel centre mapping for every destination index:

        source = (destination + 0.5) * (old / new) - 0.5
    """

    scale = old_size / new_size

    return (np.arange(new_size) + 0.5) * scale - 0.5


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

    new_width, new_height = validate_size(
        new_width,
        new_height
    )

    old_height, old_width = image.shape[:2]

    source_y = np.clip(
        np.round(_source_coordinates(new_height, old_height)).astype(np.int64),
        0,
        old_height - 1
    )

    source_x = np.clip(
        np.round(_source_coordinates(new_width, old_width)).astype(np.int64),
        0,
        old_width - 1
    )

    return image[
        source_y[:, None],
        source_x[None, :]
    ]


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

    new_width, new_height = validate_size(
        new_width,
        new_height
    )

    image_float = image.astype(
        np.float64
    )

    old_height, old_width = image.shape[:2]

    # --------------------------------------------------------
    # PER-AXIS SOURCE POSITIONS, NEIGHBOURS AND WEIGHTS
    # --------------------------------------------------------

    source_y = np.clip(
        _source_coordinates(new_height, old_height),
        0.0,
        old_height - 1
    )

    y0 = np.floor(source_y).astype(np.int64)
    y1 = np.minimum(y0 + 1, old_height - 1)
    dy = source_y - y0

    source_x = np.clip(
        _source_coordinates(new_width, old_width),
        0.0,
        old_width - 1
    )

    x0 = np.floor(source_x).astype(np.int64)
    x1 = np.minimum(x0 + 1, old_width - 1)
    dx = source_x - x0

    # Broadcast shapes: rows down, columns across, channels last.
    extra = (1,) * (image.ndim - 2)
    dx = dx.reshape((1, new_width) + extra)

    if image.ndim == 2:
        output_shape = (new_height, new_width)
    else:
        output_shape = (new_height, new_width, image.shape[2])

    output = np.empty(output_shape, dtype=np.float64)

    # Work in bands of rows so a very large output does not need
    # several full-size temporary arrays at once.
    channels = 1 if image.ndim == 2 else image.shape[2]
    band_height = max(1, 2_000_000 // max(1, new_width * channels))

    for start in range(0, new_height, band_height):

        stop = min(start + band_height, new_height)

        top_rows = y0[start:stop, None]
        bottom_rows = y1[start:stop, None]
        band_dy = dy[start:stop].reshape((-1, 1) + extra)

        # Q00 -------- Q01
        #  |            |
        #  |      P     |
        #  |            |
        # Q10 -------- Q11
        q00 = image_float[top_rows, x0[None, :]]
        q01 = image_float[top_rows, x1[None, :]]
        q10 = image_float[bottom_rows, x0[None, :]]
        q11 = image_float[bottom_rows, x1[None, :]]

        top = (1 - dx) * q00 + dx * q01
        bottom = (1 - dx) * q10 + dx * q11

        output[start:stop] = (1 - band_dy) * top + band_dy * bottom

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

    new_width, new_height = validate_size(
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
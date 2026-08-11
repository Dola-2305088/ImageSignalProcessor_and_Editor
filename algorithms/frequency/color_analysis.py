import numpy as np

from algorithms.frequency.dft import (
    manual_dft2,
    create_spectrum_image
)


# ============================================================
# SPLIT RGB CHANNELS
# ============================================================

def split_rgb_channels(image):
    """
    Split an RGB image into R, G and B channels.
    """

    image = np.asarray(
        image,
        dtype=np.uint8
    )

    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(
            "Expected an RGB image."
        )

    red = image[:, :, 0]
    green = image[:, :, 1]
    blue = image[:, :, 2]

    return red, green, blue


# ============================================================
# CREATE VISIBLE RGB CHANNEL IMAGE
# ============================================================

def create_colored_channel(channel, channel_name):
    """
    Display one channel using its actual color.

    R -> red image
    G -> green image
    B -> blue image
    """

    channel = np.asarray(
        channel,
        dtype=np.uint8
    )

    height, width = channel.shape

    result = np.zeros(
        (height, width, 3),
        dtype=np.uint8
    )

    if channel_name == "R":

        result[:, :, 0] = channel

    elif channel_name == "G":

        result[:, :, 1] = channel

    elif channel_name == "B":

        result[:, :, 2] = channel

    else:

        raise ValueError(
            "Channel must be R, G or B."
        )

    return result


# ============================================================
# RGB -> YCbCr
# ============================================================

def rgb_to_ycbcr(image):
    """
    Convert RGB image to YCbCr manually.

    Y  = luminance / brightness
    Cb = blue-difference chroma
    Cr = red-difference chroma
    """

    image = np.asarray(
        image,
        dtype=np.float64
    )

    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(
            "Expected an RGB image."
        )

    r = image[:, :, 0]
    g = image[:, :, 1]
    b = image[:, :, 2]

    # BT.601-style conversion

    y = (
        0.299 * r
        +
        0.587 * g
        +
        0.114 * b
    )

    cb = (
        -0.168736 * r
        -
        0.331264 * g
        +
        0.5 * b
        +
        128
    )

    cr = (
        0.5 * r
        -
        0.418688 * g
        -
        0.081312 * b
        +
        128
    )

    y = np.clip(
        y,
        0,
        255
    ).astype(
        np.uint8
    )

    cb = np.clip(
        cb,
        0,
        255
    ).astype(
        np.uint8
    )

    cr = np.clip(
        cr,
        0,
        255
    ).astype(
        np.uint8
    )

    return y, cb, cr


# ============================================================
# CHANNEL FREQUENCY SPECTRUM
# ============================================================

def calculate_channel_spectrum(channel):
    """
    Compute the manual 2D DFT of one image channel
    and return a displayable frequency spectrum.
    """

    channel = np.asarray(
        channel,
        dtype=np.float64
    )

    if channel.ndim != 2:
        raise ValueError(
            "Expected a single 2D channel."
        )

    frequency = manual_dft2(
        channel
    )

    spectrum = create_spectrum_image(
        frequency
    )

    return spectrum


# ============================================================
# CHANNEL STATISTICS
# ============================================================

def get_channel_statistics(channel):
    """
    Return useful numerical information
    about a channel.
    """

    channel = np.asarray(
        channel,
        dtype=np.float64
    )

    return {
        "mean": float(np.mean(channel)),
        "std": float(np.std(channel)),
        "min": float(np.min(channel)),
        "max": float(np.max(channel))
    }
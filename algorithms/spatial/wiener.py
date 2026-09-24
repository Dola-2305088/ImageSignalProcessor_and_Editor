import numpy as np

from utils.metrics import calculate_psnr


# ============================================================
# BASIC HELPERS
# ============================================================

def clip_image(image):
    """
    Clip image values to [0, 255] and convert to uint8.
    """

    # Round before casting: astype() truncates, which would darken
    # every processed image by up to one grey level.
    return np.clip(
        np.round(image),
        0,
        255
    ).astype(np.uint8)


def validate_image(image):
    """
    Validate grayscale or RGB image.
    """

    image = np.asarray(image)

    if image.ndim not in (2, 3):
        raise ValueError(
            "Image must be grayscale or RGB."
        )

    return image


# Frequency-domain restoration assumes the blur wrapped around the
# image edges (circular convolution). Our motion blur does not: it
# uses reflect padding, like every other spatial filter here. Feeding
# the image straight to the FFT therefore makes the left edge fight
# the right edge, and the ringing that follows ruins the restoration.
#
# The fix is to reflect-pad the blurred image before the transform and
# crop the result afterwards, so the wrap-around happens in a margin
# we throw away. On a 96x96 test scene this lifts Wiener restoration
# from about 22 dB (no better than the blurred input) to about 29 dB.
BORDER_FACTOR = 3


def restoration_pad(kernel, image_shape):
    """
    Margin to reflect-pad before an FFT-based restoration.
    """

    kernel = np.asarray(kernel)

    longest = max(kernel.shape[0], kernel.shape[1])

    pad = BORDER_FACTOR * longest

    # Never pad more than the image itself can support.
    limit = max(1, min(image_shape[0], image_shape[1]) // 2)

    return int(min(pad, limit))


def pad_for_restoration(image, pad):
    """
    Reflect-pad a 2D image by ``pad`` on every side.
    """

    return np.pad(
        image,
        (
            (pad, pad),
            (pad, pad)
        ),
        mode="reflect"
    )


def crop_after_restoration(image, pad, shape):
    """
    Undo pad_for_restoration().
    """

    rows, cols = shape

    return image[
        pad: pad + rows,
        pad: pad + cols
    ]


# ============================================================
# PSF -> OTF
# ============================================================

def psf_to_otf(kernel, image_shape):
    """
    Convert a spatial blur kernel (PSF) into its
    frequency-domain representation (OTF).

    Parameters
    ----------
    kernel : ndarray
        2D blur kernel.

    image_shape : tuple
        (height, width) of image.

    Returns
    -------
    ndarray
        Frequency response of the blur kernel.
    """

    kernel = np.asarray(
        kernel,
        dtype=np.float64
    )

    if kernel.ndim != 2:
        raise ValueError(
            "Blur kernel must be 2D."
        )

    image_height, image_width = image_shape

    kernel_height, kernel_width = kernel.shape

    if (
        kernel_height > image_height
        or
        kernel_width > image_width
    ):
        raise ValueError(
            "Kernel cannot be larger than image."
        )

    # --------------------------------------------------------
    # ZERO-PAD KERNEL TO IMAGE SIZE
    # --------------------------------------------------------

    padded = np.zeros(
        (image_height, image_width),
        dtype=np.float64
    )

    padded[
        :kernel_height,
        :kernel_width
    ] = kernel

    # --------------------------------------------------------
    # MOVE KERNEL CENTER TO ORIGIN
    #
    # Required before taking FFT.
    # --------------------------------------------------------

    padded = np.roll(
        padded,
        -(kernel_height // 2),
        axis=0
    )

    padded = np.roll(
        padded,
        -(kernel_width // 2),
        axis=1
    )

    # Convert PSF to frequency response
    otf = np.fft.fft2(
        padded
    )

    return otf


# ============================================================
# SINGLE-CHANNEL NAIVE INVERSE FILTER
# ============================================================

def inverse_filter_gray(
    blurred,
    kernel,
    epsilon=0.01
):
    """
    Restore a grayscale image using naive inverse filtering.

    F_hat = G / H

    Very small values of H cause instability, so epsilon
    prevents division by zero.

    This method is intentionally included to demonstrate
    why naive inverse filtering fails in noise.
    """

    blurred = np.asarray(
        blurred,
        dtype=np.float64
    )

    shape = blurred.shape

    pad = restoration_pad(kernel, shape)

    padded = pad_for_restoration(blurred, pad)

    H = psf_to_otf(
        kernel,
        padded.shape
    )

    G = np.fft.fft2(
        padded
    )

    magnitude_H = np.abs(H)

    # --------------------------------------------------------
    # STABILIZE VERY SMALL FREQUENCIES
    # --------------------------------------------------------

    safe_H = H.copy()

    small_mask = (
        magnitude_H < epsilon
    )

    # Preserve phase while limiting very small magnitude
    phase = np.exp(
        1j * np.angle(
            safe_H[small_mask]
        )
    )

    safe_H[small_mask] = (
        epsilon * phase
    )

    F_hat = (
        G / safe_H
    )

    restored = np.real(
        np.fft.ifft2(
            F_hat
        )
    )

    return crop_after_restoration(
        restored,
        pad,
        shape
    )


# ============================================================
# SINGLE-CHANNEL WIENER FILTER
# ============================================================

def wiener_filter_gray(
    blurred,
    kernel,
    k=0.01
):
    """
    Wiener deconvolution for one grayscale channel.

    Formula:

                 H*
        F = ------------- G
             |H|^2 + K

    where

        G = DFT of blurred image
        H = DFT of blur kernel
        H* = complex conjugate of H
        K = regularization / noise parameter
    """

    if k < 0:
        raise ValueError(
            "Wiener parameter k must be non-negative."
        )

    blurred = np.asarray(
        blurred,
        dtype=np.float64
    )

    if blurred.ndim != 2:
        raise ValueError(
            "wiener_filter_gray expects a 2D image."
        )

    shape = blurred.shape

    pad = restoration_pad(kernel, shape)

    padded = pad_for_restoration(blurred, pad)

    # Blur kernel frequency response
    H = psf_to_otf(
        kernel,
        padded.shape
    )

    # Blurred image frequency spectrum
    G = np.fft.fft2(
        padded
    )

    H_conjugate = np.conj(
        H
    )

    denominator = (
        np.abs(H) ** 2
        +
        k
    )

    F_hat = (
        H_conjugate
        /
        denominator
    ) * G

    restored = np.real(
        np.fft.ifft2(
            F_hat
        )
    )

    return crop_after_restoration(
        restored,
        pad,
        shape
    )


# ============================================================
# RGB / GRAYSCALE WIENER
# ============================================================

def wiener_deconvolution(
    blurred,
    kernel,
    k=0.01
):
    """
    Wiener deconvolution for grayscale or RGB images.
    """

    blurred = validate_image(
        blurred
    )

    if blurred.ndim == 2:

        restored = wiener_filter_gray(
            blurred,
            kernel,
            k
        )

        return clip_image(
            restored
        )

    # --------------------------------------------------------
    # RGB IMAGE
    # --------------------------------------------------------

    channels = []

    for channel_index in range(
        blurred.shape[2]
    ):

        channel = blurred[
            :,
            :,
            channel_index
        ]

        restored_channel = (
            wiener_filter_gray(
                channel,
                kernel,
                k
            )
        )

        channels.append(
            restored_channel
        )

    restored = np.stack(
        channels,
        axis=2
    )

    return clip_image(
        restored
    )


# ============================================================
# RGB / GRAYSCALE INVERSE FILTER
# ============================================================

def inverse_deconvolution(
    blurred,
    kernel,
    epsilon=0.01
):
    """
    Naive inverse filtering for grayscale or RGB images.
    """

    blurred = validate_image(
        blurred
    )

    if blurred.ndim == 2:

        restored = inverse_filter_gray(
            blurred,
            kernel,
            epsilon
        )

        return clip_image(
            restored
        )

    channels = []

    for channel_index in range(
        blurred.shape[2]
    ):

        channel = blurred[
            :,
            :,
            channel_index
        ]

        restored_channel = (
            inverse_filter_gray(
                channel,
                kernel,
                epsilon
            )
        )

        channels.append(
            restored_channel
        )

    restored = np.stack(
        channels,
        axis=2
    )

    return clip_image(
        restored
    )


# ============================================================
# ADD RESTORATION NOISE
# ============================================================

def add_gaussian_noise(
    image,
    sigma=3.0,
    seed=None
):
    """
    Add mild Gaussian noise to a blurred image.

    This allows us to demonstrate why Wiener filtering
    is more stable than naive inverse filtering.
    """

    image = np.asarray(
        image,
        dtype=np.float64
    )

    rng = np.random.default_rng(
        seed
    )

    noise = rng.normal(
        0.0,
        sigma,
        image.shape
    )

    return clip_image(
        image + noise
    )


# ============================================================
# COMPLETE COMPARISON
# ============================================================

def compare_restoration(
    original,
    blurred,
    kernel,
    k=0.01,
    inverse_epsilon=0.01
):
    """
    Compare blurred image, naive inverse filtering,
    and Wiener restoration.

    Returns images and PSNR values.
    """

    original = np.asarray(
        original
    )

    blurred = np.asarray(
        blurred
    )

    inverse = inverse_deconvolution(
        blurred,
        kernel,
        inverse_epsilon
    )

    wiener = wiener_deconvolution(
        blurred,
        kernel,
        k
    )

    blurred_psnr = calculate_psnr(
        original,
        blurred
    )

    inverse_psnr = calculate_psnr(
        original,
        inverse
    )

    wiener_psnr = calculate_psnr(
        original,
        wiener
    )

    return {
        "blurred": blurred,
        "inverse": inverse,
        "wiener": wiener,

        "blurred_psnr": blurred_psnr,
        "inverse_psnr": inverse_psnr,
        "wiener_psnr": wiener_psnr,

        "wiener_improvement":
            wiener_psnr - blurred_psnr
    }
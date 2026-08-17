import numpy as np


def manual_dft2(image):
    """
    Compute the 2D Discrete Fourier Transform manually.

    We do NOT use np.fft.fft2() here.

    Parameters
    ----------
    image : numpy.ndarray
        2D grayscale image.

    Returns
    -------
    numpy.ndarray
        Complex 2D DFT coefficients.
    """

    image = np.asarray(image, dtype=np.float64)

    if image.ndim != 2:
        raise ValueError("manual_dft2 expects a 2D grayscale image.")

    rows, cols = image.shape

    # Row DFT matrix
    row_indices = np.arange(rows)

    W_rows = np.exp(
        -2j
        * np.pi
        * np.outer(row_indices, row_indices)
        / rows
    )

    # Column DFT matrix
    col_indices = np.arange(cols)

    W_cols = np.exp(
        -2j
        * np.pi
        * np.outer(col_indices, col_indices)
        / cols
    )

    # F = W_rows * image * W_cols^T
    frequency = W_rows @ image @ W_cols.T

    return frequency


def manual_idft2(frequency):
    """
    Compute the inverse 2D DFT manually.
    """

    frequency = np.asarray(
        frequency,
        dtype=np.complex128
    )

    rows, cols = frequency.shape

    row_indices = np.arange(rows)

    W_rows = np.exp(
        -2j
        * np.pi
        * np.outer(row_indices, row_indices)
        / rows
    )

    col_indices = np.arange(cols)

    W_cols = np.exp(
        -2j
        * np.pi
        * np.outer(col_indices, col_indices)
        / cols
    )

    reconstructed = (
        W_rows.conj().T
        @ frequency
        @ W_cols.conj()
    )

    reconstructed = reconstructed / (rows * cols)

    return reconstructed


def fftshift_manual(frequency):
    """
    Move zero/low frequency to the center.
    """

    rows, cols = frequency.shape

    shifted = np.roll(
        frequency,
        rows // 2,
        axis=0
    )

    shifted = np.roll(
        shifted,
        cols // 2,
        axis=1
    )

    return shifted


def ifftshift_manual(frequency):
    """
    Reverse fftshift_manual().
    """

    rows, cols = frequency.shape

    shifted = np.roll(
        frequency,
        -(rows // 2),
        axis=0
    )

    shifted = np.roll(
        shifted,
        -(cols // 2),
        axis=1
    )

    return shifted


def create_spectrum_image(frequency):
    """
    Convert DFT magnitudes into a visible 0-255 image.
    """

    shifted = fftshift_manual(frequency)

    magnitude = np.abs(shifted)

    # Log is necessary because DFT magnitude
    # values can have a huge range.
    magnitude = np.log1p(magnitude)

    minimum = magnitude.min()
    maximum = magnitude.max()

    if maximum == minimum:
        normalized = np.zeros_like(magnitude)

    else:
        normalized = (
            (magnitude - minimum)
            / (maximum - minimum)
        ) * 255

    return normalized.astype(np.uint8)


def reconstruct_from_dft(frequency):
    """
    Reconstruct an image using the manual inverse DFT.
    """

    reconstructed = manual_idft2(frequency)

    # Numerical calculations may leave tiny
    # imaginary values such as 1e-12j.
    reconstructed = np.real(reconstructed)

    reconstructed = np.clip(
        reconstructed,
        0,
        255
    )

    return reconstructed.astype(np.uint8)

def create_low_pass_mask(shape, radius):
    """
    Create a circular low-pass mask.

    Center frequencies are kept.
    Frequencies outside the radius are removed.
    """

    rows, cols = shape

    center_row = rows // 2
    center_col = cols // 2

    y, x = np.ogrid[:rows, :cols]

    distance = np.sqrt(
        (y - center_row) ** 2
        +
        (x - center_col) ** 2
    )

    mask = distance <= radius

    return mask.astype(np.float64)


def create_high_pass_mask(shape, radius):
    """
    Create a circular high-pass mask.

    Center frequencies are removed.
    Frequencies outside the radius are kept.
    """

    low_pass_mask = create_low_pass_mask(
        shape,
        radius
    )

    return 1.0 - low_pass_mask


def apply_low_pass_filter(frequency, radius):
    """
    Apply circular low-pass filtering
    to DFT coefficients.
    """

    shifted = fftshift_manual(
        frequency
    )

    mask = create_low_pass_mask(
        shifted.shape,
        radius
    )

    filtered_shifted = shifted * mask

    filtered_frequency = ifftshift_manual(
        filtered_shifted
    )

    return filtered_frequency


def apply_high_pass_filter(frequency, radius):
    """
    Apply circular high-pass filtering
    to DFT coefficients.
    """

    shifted = fftshift_manual(
        frequency
    )

    mask = create_high_pass_mask(
        shifted.shape,
        radius
    )

    filtered_shifted = shifted * mask

    filtered_frequency = ifftshift_manual(
        filtered_shifted
    )

    return filtered_frequency
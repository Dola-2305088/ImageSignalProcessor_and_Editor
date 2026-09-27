import numpy as np


def compress_dft(frequency, keep_percentage):
    """
    Keep only the largest DFT coefficients.

    Parameters
    ----------
    frequency : numpy.ndarray
        2D complex DFT coefficients.

    keep_percentage : float
        Percentage of coefficients to keep.
        Example:
            10 means keep largest 10%.

    Returns
    -------
    compressed_frequency
        DFT after removing small coefficients.

    mask
        Boolean mask showing which coefficients were kept.

    kept_count
        Number of coefficients kept.

    total_count
        Total number of coefficients.
    """

    if keep_percentage <= 0 or keep_percentage > 100:
        raise ValueError(
            "Keep percentage must be between 0 and 100."
        )

    frequency = np.asarray(
        frequency,
        dtype=np.complex128
    )

    magnitude = np.abs(
        frequency
    )

    flat_magnitude = magnitude.flatten()

    total_count = flat_magnitude.size

    kept_count = int(
        np.ceil(
            total_count
            * keep_percentage
            / 100.0
        )
    )

    kept_count = max(
        1,
        kept_count
    )

    # If keeping everything
    if kept_count >= total_count:

        mask = np.ones(
            frequency.shape,
            dtype=bool
        )

        return (
            frequency.copy(),
            mask,
            total_count,
            total_count
        )

    # Find indices of largest coefficients
    largest_indices = np.argpartition(
        flat_magnitude,
        -kept_count
    )[-kept_count:]

    mask_flat = np.zeros(
        total_count,
        dtype=bool
    )

    mask_flat[
        largest_indices
    ] = True

    mask = mask_flat.reshape(
        frequency.shape
    )

    compressed_frequency = np.where(
        mask,
        frequency,
        0
    )

    return (
        compressed_frequency,
        mask,
        kept_count,
        total_count
    )
import numpy as np

from algorithms.frequency.dft import (
    manual_dft2,
    fftshift_manual
)


def classify_orientation(angle):
    """
    Convert an orientation angle into an easy-to-read direction.

    Angle is in degrees from 0 to 180.
    """

    angle = angle % 180

    if angle < 22.5 or angle >= 157.5:
        return "Horizontal"

    elif angle < 67.5:
        return "Diagonal"

    elif angle < 112.5:
        return "Vertical"

    else:
        return "Diagonal"


def normalize_spectrum(log_magnitude):
    """
    Convert a logarithmic magnitude spectrum into
    a visible 0-255 grayscale image.
    """

    minimum = np.min(log_magnitude)
    maximum = np.max(log_magnitude)

    if maximum == minimum:
        return np.zeros_like(
            log_magnitude,
            dtype=np.uint8
        )

    normalized = (
        (log_magnitude - minimum)
        /
        (maximum - minimum)
    ) * 255

    return normalized.astype(
        np.uint8
    )


def analyze_texture(
    image,
    dc_exclusion_radius=4
):
    """
    Analyze a grayscale texture using its 2D DFT.

    Parameters
    ----------
    image : numpy.ndarray
        2D grayscale image.

    dc_exclusion_radius : int
        Radius around the center of the DFT that
        will be ignored when searching for peaks.

    Returns
    -------
    dict
        Contains spectrum image, dominant direction,
        frequency, approximate repetition spacing,
        and other useful information.
    """

    image = np.asarray(
        image,
        dtype=np.float64
    )

    if image.ndim != 2:
        raise ValueError(
            "Texture analyzer expects a 2D grayscale image."
        )

    rows, cols = image.shape

    # =====================================================
    # STEP 1: REMOVE AVERAGE BRIGHTNESS
    # =====================================================

    centered_image = (
        image - np.mean(image)
    )


    # =====================================================
    # STEP 2: APPLY HANN WINDOW
    # =====================================================
    #
    # This reduces strong artificial frequency components
    # caused by the image boundaries.
    # =====================================================

    if rows > 1:
        row_window = np.hanning(rows)
    else:
        row_window = np.ones(rows)

    if cols > 1:
        col_window = np.hanning(cols)
    else:
        col_window = np.ones(cols)

    window_2d = np.outer(
        row_window,
        col_window
    )

    windowed_image = (
        centered_image * window_2d
    )


    # =====================================================
    # STEP 3: MANUAL 2D DFT
    # =====================================================

    frequency = manual_dft2(
        windowed_image
    )


    # =====================================================
    # STEP 4: MOVE LOW FREQUENCIES TO CENTER
    # =====================================================

    shifted_frequency = fftshift_manual(
        frequency
    )


    # =====================================================
    # STEP 5: MAGNITUDE SPECTRUM
    # =====================================================

    magnitude = np.abs(
        shifted_frequency
    )

    log_magnitude = np.log1p(
        magnitude
    )

    spectrum_image = normalize_spectrum(
        log_magnitude
    )


    # =====================================================
    # STEP 6: IGNORE CENTER / DC REGION
    # =====================================================

    center_row = rows // 2
    center_col = cols // 2

    y, x = np.ogrid[
        :rows,
        :cols
    ]

    distance_from_center = np.sqrt(
        (y - center_row) ** 2
        +
        (x - center_col) ** 2
    )

    valid_frequency_mask = (
        distance_from_center
        > dc_exclusion_radius
    )

    search_magnitude = magnitude.copy()

    search_magnitude[
        ~valid_frequency_mask
    ] = 0


# =====================================================
# STEP 7: FIND STRONGEST FREQUENCY PEAK
# =====================================================

    max_frequency_strength = np.max(search_magnitude)

    # No texture / no non-DC frequency exists
    if max_frequency_strength <= 1e-12:
        return {
            "spectrum": spectrum_image,
            "frequency_x": 0.0,
            "frequency_y": 0.0,
            "radial_frequency": 0.0,
            "frequency_angle": 0.0,
            "texture_angle": 0.0,
            "orientation": "None",
            "spacing_pixels": float("inf"),
            "periodicity_strength": 0.0,
            "peak_row": None,
            "peak_col": None
        }

    peak_index = np.argmax(search_magnitude)

    peak_row, peak_col = np.unravel_index(
        peak_index,
        search_magnitude.shape
    )
    # =====================================================
    # STEP 8: FREQUENCY VECTOR
    # =====================================================

    delta_row = (
        peak_row - center_row
    )

    delta_col = (
        peak_col - center_col
    )


    # Frequency in cycles per pixel
    frequency_x = (
        delta_col / cols
    )

    frequency_y = (
        delta_row / rows
    )

    radial_frequency = np.sqrt(
        frequency_x ** 2
        +
        frequency_y ** 2
    )


    # =====================================================
    # STEP 9: ESTIMATE REPEATING SPACING
    # =====================================================

    if radial_frequency > 0:

        spacing_pixels = (
            1.0 / radial_frequency
        )

    else:

        spacing_pixels = float(
            "inf"
        )


    # =====================================================
    # STEP 10: FREQUENCY ANGLE
    # =====================================================

    frequency_angle = np.degrees(
        np.arctan2(
            frequency_y,
            frequency_x
        )
    )

    frequency_angle = (
        frequency_angle % 180
    )


    # =====================================================
    # TEXTURE ORIENTATION
    # =====================================================
    #
    # Fourier frequency direction is perpendicular
    # to the visual stripe/repetition direction.
    #
    # Therefore:
    #
    # texture orientation =
    # frequency direction + 90 degrees
    # =====================================================

    texture_angle = (
        frequency_angle + 90
    ) % 180

    orientation = classify_orientation(
        texture_angle
    )


    # =====================================================
    # PERIODICITY STRENGTH
    # =====================================================

    valid_values = search_magnitude[
        valid_frequency_mask
    ]

    mean_frequency_strength = np.mean(
        valid_values
    )

    peak_strength = search_magnitude[
        peak_row,
        peak_col
    ]

    if mean_frequency_strength > 0:

        periodicity_strength = (
            peak_strength
            /
            mean_frequency_strength
        )

    else:

        periodicity_strength = 0


    # =====================================================
    # MARK DOMINANT PEAK ON DISPLAY SPECTRUM
    # =====================================================

    marked_spectrum = spectrum_image.copy()

    marker_size = 2

    row_start = max(
        0,
        peak_row - marker_size
    )

    row_end = min(
        rows,
        peak_row + marker_size + 1
    )

    col_start = max(
        0,
        peak_col - marker_size
    )

    col_end = min(
        cols,
        peak_col + marker_size + 1
    )

    marked_spectrum[
        row_start:row_end,
        col_start:col_end
    ] = 255


    # Also mark symmetric Fourier peak

    symmetric_row = (
        2 * center_row - peak_row
    ) % rows

    symmetric_col = (
        2 * center_col - peak_col
    ) % cols

    row_start = max(
        0,
        symmetric_row - marker_size
    )

    row_end = min(
        rows,
        symmetric_row + marker_size + 1
    )

    col_start = max(
        0,
        symmetric_col - marker_size
    )

    col_end = min(
        cols,
        symmetric_col + marker_size + 1
    )

    marked_spectrum[
        row_start:row_end,
        col_start:col_end
    ] = 255


    return {

        "spectrum": marked_spectrum,

        "frequency_x": frequency_x,

        "frequency_y": frequency_y,

        "radial_frequency": radial_frequency,

        "frequency_angle": frequency_angle,

        "texture_angle": texture_angle,

        "orientation": orientation,

        "spacing_pixels": spacing_pixels,

        "periodicity_strength": periodicity_strength,

        "peak_row": peak_row,

        "peak_col": peak_col
    }
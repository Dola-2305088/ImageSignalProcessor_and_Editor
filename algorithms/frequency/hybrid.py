import numpy as np

from algorithms.frequency.dft import (
    manual_dft2,
    manual_idft2,
    apply_low_pass_filter,
    apply_high_pass_filter
)


def create_hybrid_image(
    low_image,
    high_image,
    low_radius=15,
    high_radius=15
):
    """
    Create a hybrid image.

    low_image:
        Image whose LOW frequencies will be preserved.

    high_image:
        Image whose HIGH frequencies will be preserved.

    Both images must have the same dimensions.
    """

    low_image = np.asarray(
        low_image,
        dtype=np.float64
    )

    high_image = np.asarray(
        high_image,
        dtype=np.float64
    )


    # ============================================
    # CHECK IMAGE SIZE
    # ============================================

    if low_image.shape != high_image.shape:

        raise ValueError(
            "Both images must have the same dimensions."
        )


    if low_image.ndim != 3:

        raise ValueError(
            "Hybrid images must be RGB images."
        )


    # ============================================
    # STORE RGB CHANNEL RESULTS
    # ============================================

    low_components = []
    high_components = []
    hybrid_channels = []


    # ============================================
    # PROCESS R, G, B SEPARATELY
    # ============================================

    for channel_index in range(3):

        low_channel = low_image[
            :, :,
            channel_index
        ]

        high_channel = high_image[
            :, :,
            channel_index
        ]


        # ========================================
        # DFT OF IMAGE A
        # ========================================

        low_frequency = manual_dft2(
            low_channel
        )


        # ========================================
        # DFT OF IMAGE B
        # ========================================

        high_frequency = manual_dft2(
            high_channel
        )


        # ========================================
        # KEEP LOW FREQUENCIES FROM IMAGE A
        # ========================================

        filtered_low_frequency = (
            apply_low_pass_filter(
                low_frequency,
                low_radius
            )
        )


        # ========================================
        # KEEP HIGH FREQUENCIES FROM IMAGE B
        # ========================================

        filtered_high_frequency = (
            apply_high_pass_filter(
                high_frequency,
                high_radius
            )
        )


        # ========================================
        # RETURN TO SPATIAL DOMAIN
        # ========================================

        low_component = manual_idft2(
            filtered_low_frequency
        )

        high_component = manual_idft2(
            filtered_high_frequency
        )


        # Numerical errors can leave tiny
        # imaginary values.
        low_component = np.real(
            low_component
        )

        high_component = np.real(
            high_component
        )


        # ========================================
        # COMBINE
        # ========================================

        hybrid_channel = (
            low_component
            +
            high_component
        )


        low_components.append(
            low_component
        )

        high_components.append(
            high_component
        )

        hybrid_channels.append(
            hybrid_channel
        )


    # ============================================
    # REBUILD RGB IMAGES
    # ============================================

    low_result = np.stack(
        low_components,
        axis=2
    )

    high_result = np.stack(
        high_components,
        axis=2
    )

    hybrid_result = np.stack(
        hybrid_channels,
        axis=2
    )


    # ============================================
    # CLIP FINAL PIXEL VALUES
    # ============================================

    low_result = np.clip(
        low_result,
        0,
        255
    ).astype(
        np.uint8
    )


    hybrid_result = np.clip(
        hybrid_result,
        0,
        255
    ).astype(
        np.uint8
    )


    # High-frequency components can contain
    # negative values.
    # Add 128 only for visualization.
    high_display = np.clip(
        high_result + 128,
        0,
        255
    ).astype(
        np.uint8
    )


    return {

        "low_component": low_result,

        "high_component": high_display,

        "hybrid": hybrid_result
    }
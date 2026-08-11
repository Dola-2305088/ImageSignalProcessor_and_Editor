import numpy as np
from scipy.signal import convolve2d


def convolve2d_grayscale(image, kernel):
    image = image.astype(np.float64)
    kernel = np.array(kernel, dtype=np.float64)

    result = convolve2d(
        image,
        kernel,
        mode="same",
        boundary="symm"
    )

    return result


def convolve2d_rgb(image, kernel):
    image = image.astype(np.float64)

    output = np.zeros_like(
        image,
        dtype=np.float64
    )

    for channel in range(3):
        output[:, :, channel] = convolve2d_grayscale(
            image[:, :, channel],
            kernel
        )

    return output
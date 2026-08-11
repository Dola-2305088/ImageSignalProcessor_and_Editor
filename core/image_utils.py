from PIL import Image
import numpy as np


def load_image_as_array(file_path):
    image = Image.open(file_path)

    # Convert every input image to RGB
    image = image.convert("RGB")

    image_array = np.array(image)

    return image_array


def rgb_to_grayscale(image_array):
    red = image_array[:, :, 0].astype(np.float64)
    green = image_array[:, :, 1].astype(np.float64)
    blue = image_array[:, :, 2].astype(np.float64)

    grayscale = (
        0.299 * red
        + 0.587 * green
        + 0.114 * blue
    )

    return grayscale


def normalize_to_uint8(image_array):
    image_array = np.clip(
        image_array,
        0,
        255
    )

    return image_array.astype(np.uint8)
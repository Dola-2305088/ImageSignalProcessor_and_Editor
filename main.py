import matplotlib.pyplot as plt

from utils.image_utils import load_image
from algorithms.spatial.blur_sharpen import (
    blur_image,
    sharpen_image
)


IMAGE_PATH = "test_images/Test1.png"


def main():

    original = load_image(IMAGE_PATH)

    blurred = blur_image(
        original,
        kernel_size=3
    )

    sharpened = sharpen_image(
        original
    )

    plt.figure(figsize=(15, 5))

    # Original
    plt.subplot(1, 3, 1)

    plt.imshow(original)

    plt.title("Original Image")

    plt.axis("off")


    # Blurred
    plt.subplot(1, 3, 2)

    plt.imshow(blurred)

    plt.title("Blurred Image")

    plt.axis("off")


    # Sharpened
    plt.subplot(1, 3, 3)

    plt.imshow(sharpened)

    plt.title("Sharpened Image")

    plt.axis("off")


    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()

    #python main.py
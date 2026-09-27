import cv2


def load_image(path):
    """
    Load an image from the given path.

    OpenCV loads images as BGR,
    so convert them to RGB.
    """

    image = cv2.imread(path)

    if image is None:
        raise ValueError(
            f"Could not load image: {path}"
        )

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    return image
import cv2


def load_image(path):
    """
    Load an image from disk.

    OpenCV normally loads as BGR.
    We convert it to RGB.
    """

    image = cv2.imread(path)

    if image is None:
        raise FileNotFoundError(
            f"Could not load image: {path}"
        )

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    return image


def save_image(path, image):
    """
    Save RGB image using OpenCV.
    """

    bgr_image = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2BGR
    )

    cv2.imwrite(
        path,
        bgr_image
    )
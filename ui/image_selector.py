from tkinter import filedialog


def select_image():
    """
    Open a file browser and allow the user to select an image.

    Returns
    -------
    str
        Path of selected image.

    Returns None if the user cancels.
    """

    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[
            (
                "Image Files",
                "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"
            ),
            ("JPEG Files", "*.jpg *.jpeg"),
            ("PNG Files", "*.png"),
            ("BMP Files", "*.bmp"),
            ("All Files", "*.*")
        ]
    )

    if file_path == "":
        return None

    return file_path
import numpy as np

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog
)

from PyQt6.QtGui import (
    QPixmap,
    QImage
)

from PyQt6.QtCore import Qt

from core.image_utils import (
    load_image_as_array,
    normalize_to_uint8
)

from core.convolution import (
    convolve2d_rgb
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Signal Image Lab"
        )

        self.resize(
            1100,
            750
        )

        self.image_path = None
        self.image_array = None

        self.setup_ui()

    # ==================================================
    # UI SETUP
    # ==================================================

    def setup_ui(self):

        central_widget = QWidget()

        main_layout = QVBoxLayout()

        # ------------------------------------------------
        # TITLE
        # ------------------------------------------------

        self.title_label = QLabel(
            "Signal Image Lab"
        )

        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.title_label.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
        """)

        main_layout.addWidget(
            self.title_label
        )

        # ------------------------------------------------
        # IMAGE AREA
        # ------------------------------------------------

        image_layout = QHBoxLayout()

        # ==========================
        # ORIGINAL IMAGE
        # ==========================

        original_container = QVBoxLayout()

        original_title = QLabel(
            "Original"
        )

        original_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        original_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
        """)

        self.original_image_label = QLabel(
            "No Image Loaded"
        )

        self.original_image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.original_image_label.setMinimumSize(
            450,
            450
        )

        self.original_image_label.setStyleSheet("""
            border: 2px dashed #666666;
            border-radius: 8px;
        """)

        original_container.addWidget(
            original_title
        )

        original_container.addWidget(
            self.original_image_label
        )

        # ==========================
        # PROCESSED IMAGE
        # ==========================

        processed_container = QVBoxLayout()

        processed_title = QLabel(
            "Processed"
        )

        processed_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        processed_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
        """)

        self.processed_image_label = QLabel(
            "No Result"
        )

        self.processed_image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.processed_image_label.setMinimumSize(
            450,
            450
        )

        self.processed_image_label.setStyleSheet("""
            border: 2px dashed #666666;
            border-radius: 8px;
        """)

        processed_container.addWidget(
            processed_title
        )

        processed_container.addWidget(
            self.processed_image_label
        )

        # Add both columns
        image_layout.addLayout(
            original_container
        )

        image_layout.addLayout(
            processed_container
        )

        main_layout.addLayout(
            image_layout
        )

        # ------------------------------------------------
        # BUTTON AREA
        # ------------------------------------------------

        button_layout = QHBoxLayout()

        self.load_button = QPushButton(
            "Load Image"
        )

        self.blur_button = QPushButton(
            "Apply Blur"
        )

        self.load_button.clicked.connect(
            self.load_image
        )

        self.blur_button.clicked.connect(
            self.apply_blur
        )

        button_layout.addWidget(
            self.load_button
        )

        button_layout.addWidget(
            self.blur_button
        )

        main_layout.addLayout(
            button_layout
        )

        # ------------------------------------------------
        # STATUS
        # ------------------------------------------------

        self.status_label = QLabel(
            "Load an image to begin."
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addWidget(
            self.status_label
        )

        # ------------------------------------------------
        # STYLE
        # ------------------------------------------------

        self.setStyleSheet("""
            QMainWindow {
                background-color: #16181d;
            }

            QLabel {
                color: white;
            }

            QPushButton {
                background-color: #2f80ed;
                color: white;

                border: none;
                border-radius: 7px;

                padding: 12px 20px;

                font-size: 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #4c97f5;
            }

            QPushButton:pressed {
                background-color: #2468bd;
            }
        """)

        central_widget.setLayout(
            main_layout
        )

        self.setCentralWidget(
            central_widget
        )

    # ==================================================
    # LOAD IMAGE
    # ==================================================

    def load_image(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )

        if not file_path:
            return

        self.image_path = file_path

        # Convert image file into RGB NumPy array
        self.image_array = load_image_as_array(
            file_path
        )

        print(
            "Image loaded successfully"
        )

        print(
            "Image shape:",
            self.image_array.shape
        )

        print(
            "Data type:",
            self.image_array.dtype
        )

        print(
            "Minimum pixel value:",
            self.image_array.min()
        )

        print(
            "Maximum pixel value:",
            self.image_array.max()
        )

        # Display original image
        pixmap = QPixmap(
            file_path
        )

        scaled_pixmap = pixmap.scaled(
            self.original_image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.original_image_label.setPixmap(
            scaled_pixmap
        )

        # Clear previous result
        self.processed_image_label.clear()

        self.processed_image_label.setText(
            "No Result"
        )

        height = self.image_array.shape[0]
        width = self.image_array.shape[1]

        self.status_label.setText(
            f"Image loaded: {width} × {height} pixels"
        )

    # ==================================================
    # APPLY RGB BLUR
    # ==================================================

    def apply_blur(self):

        if self.image_array is None:

            self.status_label.setText(
                "Please load an image first."
            )

            return

        self.status_label.setText(
            "Applying RGB blur using custom 2D convolution..."
        )

        # 3 x 3 averaging kernel
        blur_kernel = np.array([
            [1/9, 1/9, 1/9],
            [1/9, 1/9, 1/9],
            [1/9, 1/9, 1/9]
        ])

        # Apply our own convolution separately
        # to R, G and B channels
        blurred = convolve2d_rgb(
            self.image_array,
            blur_kernel
        )

        # Restrict values to 0 ... 255
        blurred = normalize_to_uint8(
            blurred
        )

        # Display the RGB result
        self.display_rgb_result(
            blurred
        )

        self.status_label.setText(
            "Color blur complete."
        )

    # ==================================================
    # DISPLAY RGB NUMPY ARRAY
    # ==================================================

    def display_rgb_result(
        self,
        image_array
    ):

        height, width, channels = image_array.shape

        # RGB = 3 bytes per pixel
        bytes_per_line = width * channels

        qimage = QImage(
            image_array.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )

        # Important:
        # create an independent copy of the image data
        qimage = qimage.copy()

        pixmap = QPixmap.fromImage(
            qimage
        )

        scaled_pixmap = pixmap.scaled(
            self.processed_image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.processed_image_label.setPixmap(
            scaled_pixmap
        )
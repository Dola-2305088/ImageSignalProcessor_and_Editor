# Image Signal Processor and Editor

CSE 220 Signal Lab Project
Developed by Shreya and Dola.
/*pip install numpy pillow matplotlib PyQt6*/

/*pip install numpy opencv-python matplotlib*/
/*pip install pillow*/
/*pip install "flet[all]"*/

/*ImageSignalProcessor_and_Editor/
ImageSignalProcessor_and_Editor/
│
├── main.py
│
├── requirements.txt
├── README.md
├── PROJECT_WORK_DISTRIBUTION.txt
│
├── algorithms/
│   │
│   ├── __init__.py
│   │
│   ├── spatial/
│   │   ├── __init__.py
│   │   │
│   │   ├── convolution.py
│   │   ├── blur_sharpen.py
│   │   ├── edge_detection.py
│   │   ├── noise_cleaner.py
│   │   ├── resize.py
│   │   ├── motion_blur.py
│   │   ├── gaussian_separable.py
│   │   └── wiener.py
│   │
│   └── frequency/
│       ├── __init__.py
│       │
│       ├── dft.py
│       ├── compression.py
│       ├── texture.py
│       ├── hybrid.py
│       └── color_analysis.py
│
├── ui/
│   │
│   ├── __init__.py
│   │
│   ├── main_window.py
│   ├── theme.py
│   │
│   ├── components/
│   │   ├── __init__.py
│   │   ├── sidebar.py
│   │   ├── top_bar.py
│   │   ├── image_card.py
│   │   ├── control_card.py
│   │   ├── result_card.py
│   │   ├── status_bar.py
│   │   ├── loading_overlay.py
│   │   └── section_header.py
│   │
│   └── views/
│       ├── __init__.py
│       │
│       ├── home_view.py
│       │
│       ├── frequency_view.py
│       ├── compression_view.py
│       ├── texture_view.py
│       ├── hybrid_view.py
│       ├── color_view.py
│       │
│       ├── blur_sharpen_view.py
│       ├── edge_view.py
│       ├── noise_view.py
│       ├── resize_view.py
│       ├── motion_blur_view.py
│       ├── gaussian_view.py
│       └── wiener_view.py
│
├── utils/
│   ├── __init__.py
│   ├── image_utils.py
│   ├── metrics.py
│   ├── file_utils.py
│   └── plot_utils.py
│
├── assets/
│   │
│   ├── images/
│   │
│   ├── icons/
│   │
│   └── animations/
│
├── test_images/
│
└── tests/
    ├── __init__.py
    ├── test_convolution.py
    ├── test_dft.py
    ├── test_compression.py
    └── test_metrics.py
*/
import tkinter as tk
from tkinter import messagebox

import numpy as np
from PIL import Image, ImageTk, ImageOps

from ui.image_selector import select_image

from algorithms.frequency.dft import (
    manual_dft2,
    create_spectrum_image,
    reconstruct_from_dft,
    apply_low_pass_filter,
    apply_high_pass_filter
)


class ImageProcessorApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Image Signal Processor and Editor"
        )

        self.root.geometry("1200x750")
        self.root.minsize(900, 600)

        # ==========================================
        # IMAGE VARIABLES
        # ==========================================

        # Original PIL image
        self.original_image = None

        # Tkinter version of original image
        self.original_photo = None

        # Processed PIL image
        self.processed_image = None

        # Tkinter version of processed image
        self.processed_photo = None

        # Stores calculated DFT
        self.current_dft = None

        self.create_ui()


    # =========================================================
    # CREATE USER INTERFACE
    # =========================================================

    def create_ui(self):

        # =====================================================
        # MAIN TITLE
        # =====================================================

        title = tk.Label(
            self.root,
            text="Image Signal Processor and Editor",
            font=("Arial", 22, "bold")
        )

        title.pack(
            pady=15
        )


        # =====================================================
        # MAIN CONTENT FRAME
        # =====================================================

        content_frame = tk.Frame(
            self.root
        )

        content_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )


        # =====================================================
        # LEFT CONTROL PANEL
        # =====================================================

        control_frame = tk.Frame(
            content_frame,
            width=250,
            relief="ridge",
            borderwidth=2
        )

        control_frame.pack(
            side="left",
            fill="y",
            padx=(0, 15)
        )

        control_frame.pack_propagate(
            False
        )


        # =====================================================
        # CONTROL TITLE
        # =====================================================

        control_title = tk.Label(
            control_frame,
            text="Controls",
            font=("Arial", 16, "bold")
        )

        control_title.pack(
            pady=(20, 15)
        )


        # =====================================================
        # OPEN IMAGE BUTTON
        # =====================================================

        open_button = tk.Button(
            control_frame,
            text="Open Image",
            font=("Arial", 12),
            width=20,
            height=2,
            command=self.open_image
        )

        open_button.pack(
            pady=8
        )


        # =====================================================
        # GRAYSCALE BUTTON
        # =====================================================

        grayscale_button = tk.Button(
            control_frame,
            text="Convert to Grayscale",
            font=("Arial", 12),
            width=20,
            height=2,
            command=self.convert_to_grayscale
        )

        grayscale_button.pack(
            pady=8
        )


        # =====================================================
        # FREQUENCY DOMAIN SECTION TITLE
        # =====================================================

        frequency_title = tk.Label(
            control_frame,
            text="Frequency Domain",
            font=("Arial", 14, "bold")
        )

        frequency_title.pack(
            pady=(25, 10)
        )


        # =====================================================
        # SHOW DFT SPECTRUM
        # =====================================================

        spectrum_button = tk.Button(
            control_frame,
            text="Show DFT Spectrum",
            font=("Arial", 12),
            width=20,
            height=2,
            command=self.show_frequency_spectrum
        )

        spectrum_button.pack(
            pady=8
        )


        # =====================================================
        # CUTOFF RADIUS LABEL
        # =====================================================

        cutoff_label = tk.Label(
            control_frame,
            text="Cutoff Radius",
            font=("Arial", 11, "bold")
        )

        cutoff_label.pack(
            pady=(15, 2)
        )


        # =====================================================
        # CUTOFF RADIUS SLIDER
        # =====================================================

        self.cutoff_slider = tk.Scale(
            control_frame,
            from_=2,
            to=60,
            orient="horizontal",
            length=180
        )

        self.cutoff_slider.set(
            15
        )

        self.cutoff_slider.pack(
            pady=5
        )


        # =====================================================
        # LOW PASS FILTER BUTTON
        # =====================================================

        low_pass_button = tk.Button(
            control_frame,
            text="Low-Pass Filter",
            font=("Arial", 12),
            width=20,
            height=2,
            command=self.apply_low_pass
        )

        low_pass_button.pack(
            pady=8
        )


        # =====================================================
        # HIGH PASS FILTER BUTTON
        # =====================================================

        high_pass_button = tk.Button(
            control_frame,
            text="High-Pass Filter",
            font=("Arial", 12),
            width=20,
            height=2,
            command=self.apply_high_pass
        )

        high_pass_button.pack(
            pady=8
        )


        # =====================================================
        # RECONSTRUCT BUTTON
        # =====================================================

        reconstruct_button = tk.Button(
            control_frame,
            text="Reconstruct from DFT",
            font=("Arial", 12),
            width=20,
            height=2,
            command=self.reconstruct_dft
        )

        reconstruct_button.pack(
            pady=8
        )


        # =====================================================
        # RESET BUTTON
        # =====================================================

        reset_button = tk.Button(
            control_frame,
            text="Reset Processed",
            font=("Arial", 12),
            width=20,
            height=2,
            command=self.reset_processed
        )

        reset_button.pack(
            pady=20
        )


        # =====================================================
        # IMAGE DISPLAY AREA
        # =====================================================

        image_area = tk.Frame(
            content_frame
        )

        image_area.pack(
            side="right",
            fill="both",
            expand=True
        )


        # =====================================================
        # ORIGINAL IMAGE FRAME
        # =====================================================

        original_frame = tk.LabelFrame(
            image_area,
            text="Original Image",
            font=("Arial", 13, "bold")
        )

        original_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10
        )


        self.original_label = tk.Label(
            original_frame,
            text="No image selected",
            font=("Arial", 12)
        )

        self.original_label.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )


        # =====================================================
        # PROCESSED IMAGE FRAME
        # =====================================================

        self.processed_frame = tk.LabelFrame(
            image_area,
            text="Processed Image",
            font=("Arial", 13, "bold")
        )

        self.processed_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10
        )


        self.processed_label = tk.Label(
            self.processed_frame,
            text="Processed image will appear here",
            font=("Arial", 12)
        )

        self.processed_label.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )


    # =========================================================
    # OPEN IMAGE FROM PC
    # =========================================================

    def open_image(self):

        file_path = select_image()

        # User pressed Cancel
        if file_path is None:
            return

        try:

            image = Image.open(
                file_path
            )

            image = image.convert(
                "RGB"
            )

            self.original_image = image

            # Display image
            self.display_original_image()

            # Old DFT belongs to previous image
            self.current_dft = None

            # Remove previous processed image
            self.reset_processed()

        except Exception as error:

            messagebox.showerror(
                "Error",
                f"Could not open image.\n\n{error}"
            )


    # =========================================================
    # DISPLAY ORIGINAL IMAGE
    # =========================================================

    def display_original_image(self):

        if self.original_image is None:
            return

        image = self.original_image.copy()

        # Resize only for UI display.
        # Original image itself remains unchanged.
        image.thumbnail(
            (430, 500),
            Image.Resampling.LANCZOS
        )

        self.original_photo = ImageTk.PhotoImage(
            image
        )

        self.original_label.configure(
            image=self.original_photo,
            text=""
        )


    # =========================================================
    # DISPLAY PROCESSED IMAGE
    # =========================================================

    def display_processed_image(self):

        if self.processed_image is None:
            return

        image = self.processed_image.copy()

        image.thumbnail(
            (430, 500),
            Image.Resampling.LANCZOS
        )

        self.processed_photo = ImageTk.PhotoImage(
            image
        )

        self.processed_label.configure(
            image=self.processed_photo,
            text=""
        )


    # =========================================================
    # CONVERT ORIGINAL IMAGE TO GRAYSCALE
    # =========================================================

    def convert_to_grayscale(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

        grayscale = ImageOps.grayscale(
            self.original_image
        )

        # Convert to RGB so all UI images
        # use the same representation.
        grayscale = grayscale.convert(
            "RGB"
        )

        self.processed_image = grayscale

        self.processed_frame.configure(
            text="Grayscale Image"
        )

        self.display_processed_image()


    # =========================================================
    # PREPARE IMAGE FOR MANUAL DFT
    # =========================================================

    def prepare_image_for_dft(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return None

        # DFT is performed on grayscale image
        grayscale = self.original_image.convert(
            "L"
        )

        # Manual DFT is computationally expensive.
        # Use maximum size 128 x 128.
        grayscale.thumbnail(
            (128, 128),
            Image.Resampling.LANCZOS
        )

        image_array = np.array(
            grayscale,
            dtype=np.float64
        )

        return image_array


    # =========================================================
    # COMPUTE MANUAL 2D DFT
    # =========================================================

    def compute_dft(self):

        image_array = self.prepare_image_for_dft()

        if image_array is None:
            return False

        # Show loading cursor
        self.root.config(
            cursor="wait"
        )

        self.root.update()

        try:

            self.current_dft = manual_dft2(
                image_array
            )

        except Exception as error:

            messagebox.showerror(
                "DFT Error",
                f"Could not calculate DFT.\n\n{error}"
            )

            return False

        finally:

            self.root.config(
                cursor=""
            )

        return True


    # =========================================================
    # SHOW DFT FREQUENCY SPECTRUM
    # =========================================================

    def show_frequency_spectrum(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

        # Calculate DFT if necessary
        if self.current_dft is None:

            if not self.compute_dft():
                return

        spectrum = create_spectrum_image(
            self.current_dft
        )

        self.processed_image = Image.fromarray(
            spectrum
        ).convert(
            "RGB"
        )

        self.processed_frame.configure(
            text="2D DFT Frequency Spectrum"
        )

        self.display_processed_image()


    # =========================================================
    # RECONSTRUCT IMAGE USING INVERSE DFT
    # =========================================================

    def reconstruct_dft(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

        # If DFT has not been calculated,
        # calculate it first.
        if self.current_dft is None:

            if not self.compute_dft():
                return

        try:

            reconstructed = reconstruct_from_dft(
                self.current_dft
            )

            self.processed_image = Image.fromarray(
                reconstructed
            ).convert(
                "RGB"
            )

            self.processed_frame.configure(
                text="Reconstructed from 2D DFT"
            )

            self.display_processed_image()

        except Exception as error:

            messagebox.showerror(
                "Reconstruction Error",
                f"Could not reconstruct image.\n\n{error}"
            )


    # =========================================================
    # LOW PASS FILTER
    # =========================================================

    def apply_low_pass(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

        # Calculate DFT if it does not exist
        if self.current_dft is None:

            if not self.compute_dft():
                return

        try:

            # Get radius from slider
            radius = self.cutoff_slider.get()

            # Apply frequency-domain low-pass mask
            filtered_frequency = apply_low_pass_filter(
                self.current_dft,
                radius
            )

            # Convert filtered frequencies
            # back into spatial-domain image
            reconstructed = reconstruct_from_dft(
                filtered_frequency
            )

            self.processed_image = Image.fromarray(
                reconstructed
            ).convert(
                "RGB"
            )

            self.processed_frame.configure(
                text=f"Low-Pass Filter — Radius {radius}"
            )

            self.display_processed_image()

        except Exception as error:

            messagebox.showerror(
                "Low-Pass Filter Error",
                f"Could not apply low-pass filter.\n\n{error}"
            )


    # =========================================================
    # HIGH PASS FILTER
    # =========================================================

    def apply_high_pass(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

        # Calculate DFT if necessary
        if self.current_dft is None:

            if not self.compute_dft():
                return

        try:

            # Read cutoff radius
            radius = self.cutoff_slider.get()

            # Remove central low frequencies
            filtered_frequency = apply_high_pass_filter(
                self.current_dft,
                radius
            )

            # Return to spatial domain
            reconstructed = reconstruct_from_dft(
                filtered_frequency
            )

            self.processed_image = Image.fromarray(
                reconstructed
            ).convert(
                "RGB"
            )

            self.processed_frame.configure(
                text=f"High-Pass Filter — Radius {radius}"
            )

            self.display_processed_image()

        except Exception as error:

            messagebox.showerror(
                "High-Pass Filter Error",
                f"Could not apply high-pass filter.\n\n{error}"
            )


    # =========================================================
    # RESET PROCESSED IMAGE
    # =========================================================

    def reset_processed(self):

        self.processed_image = None
        self.processed_photo = None

        self.processed_frame.configure(
            text="Processed Image"
        )

        self.processed_label.configure(
            image="",
            text="Processed image will appear here"
        )
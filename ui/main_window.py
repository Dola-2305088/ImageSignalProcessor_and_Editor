import tkinter as tk
from tkinter import messagebox

import numpy as np
import matplotlib.pyplot as plt

from PIL import Image, ImageTk, ImageOps

from ui.image_selector import select_image

from algorithms.frequency.dft import (
    manual_dft2,
    create_spectrum_image,
    reconstruct_from_dft,
    apply_low_pass_filter,
    apply_high_pass_filter
)

from algorithms.frequency.compression import (
    compress_dft
)

from utils.metrics import (
    calculate_psnr
)


class ImageProcessorApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Image Signal Processor and Editor"
        )

        self.root.geometry(
            "1250x780"
        )

        self.root.minsize(
            950,
            650
        )

        # =========================================
        # IMAGE DATA
        # =========================================

        self.original_image = None
        self.original_photo = None

        self.processed_image = None
        self.processed_photo = None

        # =========================================
        # FREQUENCY DATA
        # =========================================

        self.current_dft = None

        # Grayscale image actually used for DFT
        self.current_dft_source = None

        # Latest compressed DFT
        self.current_compressed_dft = None

        self.create_ui()


    # ======================================================
    # CREATE UI
    # ======================================================

    def create_ui(self):

        # =========================================
        # TITLE
        # =========================================

        title = tk.Label(
            self.root,
            text="Image Signal Processor and Editor",
            font=("Arial", 22, "bold")
        )

        title.pack(
            pady=12
        )


        # =========================================
        # MAIN CONTENT
        # =========================================

        content_frame = tk.Frame(
            self.root
        )

        content_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )


        # =========================================
        # SCROLLABLE LEFT CONTROL PANEL
        # =========================================

        control_outer = tk.Frame(
            content_frame,
            width=285,
            relief="ridge",
            borderwidth=2
        )

        control_outer.pack(
            side="left",
            fill="y",
            padx=(0, 15)
        )

        control_outer.pack_propagate(
            False
        )


        control_canvas = tk.Canvas(
            control_outer,
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            control_outer,
            orient="vertical",
            command=control_canvas.yview
        )

        control_canvas.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        control_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )


        self.control_frame = tk.Frame(
            control_canvas
        )

        control_window = control_canvas.create_window(
            (0, 0),
            window=self.control_frame,
            anchor="nw"
        )


        def update_scroll_region(event):

            control_canvas.configure(
                scrollregion=control_canvas.bbox("all")
            )


        def resize_control_frame(event):

            control_canvas.itemconfig(
                control_window,
                width=event.width
            )


        self.control_frame.bind(
            "<Configure>",
            update_scroll_region
        )

        control_canvas.bind(
            "<Configure>",
            resize_control_frame
        )


        # =========================================
        # CONTROLS TITLE
        # =========================================

        control_title = tk.Label(
            self.control_frame,
            text="Controls",
            font=("Arial", 16, "bold")
        )

        control_title.pack(
            pady=(20, 15)
        )


        # =========================================
        # OPEN IMAGE
        # =========================================

        open_button = tk.Button(
            self.control_frame,
            text="Open Image",
            font=("Arial", 12),
            width=21,
            height=2,
            command=self.open_image
        )

        open_button.pack(
            pady=6
        )


        # =========================================
        # GRAYSCALE
        # =========================================

        grayscale_button = tk.Button(
            self.control_frame,
            text="Convert to Grayscale",
            font=("Arial", 12),
            width=21,
            height=2,
            command=self.convert_to_grayscale
        )

        grayscale_button.pack(
            pady=6
        )


        # =========================================
        # FEATURE 4 TITLE
        # =========================================

        frequency_title = tk.Label(
            self.control_frame,
            text="Feature 4",
            font=("Arial", 10)
        )

        frequency_title.pack(
            pady=(25, 0)
        )

        frequency_title2 = tk.Label(
            self.control_frame,
            text="Frequency Editor",
            font=("Arial", 14, "bold")
        )

        frequency_title2.pack(
            pady=(0, 10)
        )


        # =========================================
        # DFT SPECTRUM
        # =========================================

        spectrum_button = tk.Button(
            self.control_frame,
            text="Show DFT Spectrum",
            font=("Arial", 12),
            width=21,
            height=2,
            command=self.show_frequency_spectrum
        )

        spectrum_button.pack(
            pady=6
        )


        # =========================================
        # CUTOFF RADIUS
        # =========================================

        cutoff_label = tk.Label(
            self.control_frame,
            text="Cutoff Radius",
            font=("Arial", 11, "bold")
        )

        cutoff_label.pack(
            pady=(12, 0)
        )


        self.cutoff_slider = tk.Scale(
            self.control_frame,
            from_=2,
            to=60,
            orient="horizontal",
            length=190
        )

        self.cutoff_slider.set(
            15
        )

        self.cutoff_slider.pack(
            pady=3
        )


        # =========================================
        # LOW PASS
        # =========================================

        low_pass_button = tk.Button(
            self.control_frame,
            text="Low-Pass Filter",
            font=("Arial", 12),
            width=21,
            height=2,
            command=self.apply_low_pass
        )

        low_pass_button.pack(
            pady=6
        )


        # =========================================
        # HIGH PASS
        # =========================================

        high_pass_button = tk.Button(
            self.control_frame,
            text="High-Pass Filter",
            font=("Arial", 12),
            width=21,
            height=2,
            command=self.apply_high_pass
        )

        high_pass_button.pack(
            pady=6
        )


        # =========================================
        # RECONSTRUCT
        # =========================================

        reconstruct_button = tk.Button(
            self.control_frame,
            text="Reconstruct from DFT",
            font=("Arial", 12),
            width=21,
            height=2,
            command=self.reconstruct_dft
        )

        reconstruct_button.pack(
            pady=6
        )


        # =========================================
        # FEATURE 5 TITLE
        # =========================================

        separator = tk.Frame(
            self.control_frame,
            height=2,
            bg="gray"
        )

        separator.pack(
            fill="x",
            padx=20,
            pady=25
        )


        compression_number = tk.Label(
            self.control_frame,
            text="Feature 5",
            font=("Arial", 10)
        )

        compression_number.pack()


        compression_title = tk.Label(
            self.control_frame,
            text="Compression Explorer",
            font=("Arial", 14, "bold")
        )

        compression_title.pack(
            pady=(0, 12)
        )


        # =========================================
        # KEEP PERCENTAGE
        # =========================================

        self.compression_value_label = tk.Label(
            self.control_frame,
            text="Keep DFT Coefficients: 10%",
            font=("Arial", 11, "bold")
        )

        self.compression_value_label.pack(
            pady=(5, 0)
        )


        self.compression_slider = tk.Scale(
            self.control_frame,
            from_=1,
            to=100,
            orient="horizontal",
            length=190,
            command=self.update_compression_label
        )

        self.compression_slider.set(
            10
        )

        self.compression_slider.pack(
            pady=5
        )


        # =========================================
        # APPLY COMPRESSION
        # =========================================

        compression_button = tk.Button(
            self.control_frame,
            text="Apply DFT Compression",
            font=("Arial", 12),
            width=21,
            height=2,
            command=self.apply_dft_compression
        )

        compression_button.pack(
            pady=7
        )


        # =========================================
        # COMPRESSION INFORMATION
        # =========================================

        self.compression_info = tk.Label(
            self.control_frame,
            text="No compression performed",
            font=("Arial", 10),
            justify="left",
            wraplength=230
        )

        self.compression_info.pack(
            pady=10
        )


        # =========================================
        # QUALITY CURVE BUTTON
        # =========================================

        quality_button = tk.Button(
            self.control_frame,
            text="Plot Compression vs PSNR",
            font=("Arial", 11),
            width=21,
            height=2,
            command=self.plot_compression_quality
        )

        quality_button.pack(
            pady=7
        )


        # =========================================
        # RESET
        # =========================================

        reset_button = tk.Button(
            self.control_frame,
            text="Reset Processed",
            font=("Arial", 12),
            width=21,
            height=2,
            command=self.reset_processed
        )

        reset_button.pack(
            pady=25
        )


        # ======================================================
        # IMAGE AREA
        # ======================================================

        image_area = tk.Frame(
            content_frame
        )

        image_area.pack(
            side="right",
            fill="both",
            expand=True
        )


        # =========================================
        # ORIGINAL IMAGE
        # =========================================

        original_frame = tk.LabelFrame(
            image_area,
            text="Original Image",
            font=("Arial", 13, "bold")
        )

        original_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=8
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


        # =========================================
        # PROCESSED IMAGE
        # =========================================

        self.processed_frame = tk.LabelFrame(
            image_area,
            text="Processed Image",
            font=("Arial", 13, "bold")
        )

        self.processed_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=8
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


    # ======================================================
    # OPEN IMAGE
    # ======================================================

    def open_image(self):

        file_path = select_image()

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

            self.current_dft = None
            self.current_dft_source = None
            self.current_compressed_dft = None

            self.display_original_image()

            self.reset_processed()

            self.compression_info.configure(
                text="No compression performed"
            )

        except Exception as error:

            messagebox.showerror(
                "Error",
                f"Could not open image.\n\n{error}"
            )


    # ======================================================
    # DISPLAY ORIGINAL
    # ======================================================

    def display_original_image(self):

        if self.original_image is None:
            return

        image = self.original_image.copy()

        image.thumbnail(
            (430, 520),
            Image.Resampling.LANCZOS
        )

        self.original_photo = ImageTk.PhotoImage(
            image
        )

        self.original_label.configure(
            image=self.original_photo,
            text=""
        )


    # ======================================================
    # DISPLAY PROCESSED
    # ======================================================

    def display_processed_image(self):

        if self.processed_image is None:
            return

        image = self.processed_image.copy()

        image.thumbnail(
            (430, 520),
            Image.Resampling.LANCZOS
        )

        self.processed_photo = ImageTk.PhotoImage(
            image
        )

        self.processed_label.configure(
            image=self.processed_photo,
            text=""
        )


    # ======================================================
    # GRAYSCALE
    # ======================================================

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

        grayscale = grayscale.convert(
            "RGB"
        )

        self.processed_image = grayscale

        self.processed_frame.configure(
            text="Grayscale Image"
        )

        self.display_processed_image()


    # ======================================================
    # PREPARE IMAGE FOR DFT
    # ======================================================

    def prepare_image_for_dft(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return None

        grayscale = self.original_image.convert(
            "L"
        )

        # Manual DFT is expensive.
        grayscale.thumbnail(
            (128, 128),
            Image.Resampling.LANCZOS
        )

        image_array = np.array(
            grayscale,
            dtype=np.float64
        )

        return image_array


    # ======================================================
    # COMPUTE MANUAL DFT
    # ======================================================

    def compute_dft(self):

        image_array = self.prepare_image_for_dft()

        if image_array is None:
            return False

        self.root.config(
            cursor="wait"
        )

        self.root.update()

        try:

            self.current_dft_source = image_array

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


    # ======================================================
    # SHOW DFT SPECTRUM
    # ======================================================

    def show_frequency_spectrum(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

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


    # ======================================================
    # RECONSTRUCT NORMAL DFT
    # ======================================================

    def reconstruct_dft(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

        if self.current_dft is None:

            if not self.compute_dft():
                return

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


    # ======================================================
    # LOW PASS
    # ======================================================

    def apply_low_pass(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

        if self.current_dft is None:

            if not self.compute_dft():
                return

        radius = self.cutoff_slider.get()

        filtered_frequency = apply_low_pass_filter(
            self.current_dft,
            radius
        )

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


    # ======================================================
    # HIGH PASS
    # ======================================================

    def apply_high_pass(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

        if self.current_dft is None:

            if not self.compute_dft():
                return

        radius = self.cutoff_slider.get()

        filtered_frequency = apply_high_pass_filter(
            self.current_dft,
            radius
        )

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


    # ======================================================
    # UPDATE COMPRESSION SLIDER LABEL
    # ======================================================

    def update_compression_label(self, value):

        percentage = int(
            float(value)
        )

        self.compression_value_label.configure(
            text=f"Keep DFT Coefficients: {percentage}%"
        )


    # ======================================================
    # APPLY DFT COMPRESSION
    # ======================================================

    def apply_dft_compression(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

        if self.current_dft is None:

            if not self.compute_dft():
                return

        try:

            percentage = self.compression_slider.get()

            (
                compressed_frequency,
                mask,
                kept_count,
                total_count
            ) = compress_dft(
                self.current_dft,
                percentage
            )

            self.current_compressed_dft = (
                compressed_frequency
            )

            reconstructed = reconstruct_from_dft(
                compressed_frequency
            )

            original_for_psnr = np.clip(
                self.current_dft_source,
                0,
                255
            ).astype(
                np.uint8
            )

            psnr = calculate_psnr(
                original_for_psnr,
                reconstructed
            )

            removed_count = (
                total_count - kept_count
            )

            removed_percentage = (
                removed_count
                / total_count
                * 100
            )

            self.processed_image = Image.fromarray(
                reconstructed
            ).convert(
                "RGB"
            )

            self.processed_frame.configure(
                text=f"DFT Compression — Keep {percentage}%"
            )

            self.display_processed_image()

            if np.isinf(psnr):

                psnr_text = "∞"

            else:

                psnr_text = f"{psnr:.2f} dB"

            self.compression_info.configure(
                text=(
                    f"Total coefficients: {total_count}\n"
                    f"Kept: {kept_count}\n"
                    f"Removed: {removed_count}\n"
                    f"Reduction: {removed_percentage:.1f}%\n"
                    f"PSNR: {psnr_text}"
                )
            )

        except Exception as error:

            messagebox.showerror(
                "Compression Error",
                f"Could not compress image.\n\n{error}"
            )


    # ======================================================
    # PLOT COMPRESSION VS PSNR
    # ======================================================

    def plot_compression_quality(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open an image first."
            )

            return

        if self.current_dft is None:

            if not self.compute_dft():
                return

        self.root.config(
            cursor="wait"
        )

        self.root.update()

        try:

            percentages = [
                1,
                2,
                5,
                10,
                20,
                40,
                60,
                80,
                95
            ]

            psnr_values = []

            original_for_psnr = np.clip(
                self.current_dft_source,
                0,
                255
            ).astype(
                np.uint8
            )

            for percentage in percentages:

                (
                    compressed_frequency,
                    _,
                    _,
                    _
                ) = compress_dft(
                    self.current_dft,
                    percentage
                )

                reconstructed = reconstruct_from_dft(
                    compressed_frequency
                )

                psnr = calculate_psnr(
                    original_for_psnr,
                    reconstructed
                )

                psnr_values.append(
                    psnr
                )

            plt.figure(
                figsize=(8, 5)
            )

            plt.plot(
                percentages,
                psnr_values,
                marker="o"
            )

            plt.xlabel(
                "DFT Coefficients Kept (%)"
            )

            plt.ylabel(
                "PSNR (dB)"
            )

            plt.title(
                "DFT Compression vs Reconstruction Quality"
            )

            plt.grid(
                True
            )

            plt.tight_layout()

            plt.show()

        except Exception as error:

            messagebox.showerror(
                "Plot Error",
                f"Could not create compression plot.\n\n{error}"
            )

        finally:

            self.root.config(
                cursor=""
            )


    # ======================================================
    # RESET PROCESSED
    # ======================================================

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
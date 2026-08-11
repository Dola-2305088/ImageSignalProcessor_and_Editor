import os
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

from algorithms.frequency.texture import (
    analyze_texture
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
            "1300x800"
        )

        self.root.minsize(
            1000,
            650
        )

        # =====================================================
        # IMAGE DATA
        # =====================================================

        self.original_image = None
        self.original_photo = None

        self.processed_image = None
        self.processed_photo = None

        self.current_image_name = None

        # =====================================================
        # FREQUENCY DOMAIN DATA
        # =====================================================

        self.current_dft = None

        # The grayscale 128x128-or-smaller image
        # actually used for DFT processing
        self.current_dft_source = None

        # Latest compressed DFT
        self.current_compressed_dft = None

        # =====================================================
        # TEXTURE DATA
        # =====================================================

        # Stores multiple analyzed texture results
        self.texture_results = {}

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
            pady=12
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
            padx=15,
            pady=10
        )


        # =====================================================
        # SCROLLABLE LEFT CONTROL PANEL
        # =====================================================

        control_outer = tk.Frame(
            content_frame,
            width=290,
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


        # =====================================================
        # CONTROL PANEL TITLE
        # =====================================================

        control_title = tk.Label(
            self.control_frame,
            text="Controls",
            font=("Arial", 16, "bold")
        )

        control_title.pack(
            pady=(20, 15)
        )


        # =====================================================
        # OPEN IMAGE
        # =====================================================

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


        # =====================================================
        # GRAYSCALE
        # =====================================================

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


        # =====================================================
        # FEATURE 4
        # =====================================================

        separator1 = tk.Frame(
            self.control_frame,
            height=2,
            bg="gray"
        )

        separator1.pack(
            fill="x",
            padx=20,
            pady=20
        )


        feature4_number = tk.Label(
            self.control_frame,
            text="Feature 4",
            font=("Arial", 10)
        )

        feature4_number.pack()


        feature4_title = tk.Label(
            self.control_frame,
            text="Frequency Editor",
            font=("Arial", 14, "bold")
        )

        feature4_title.pack(
            pady=(0, 10)
        )


        # =====================================================
        # DFT SPECTRUM
        # =====================================================

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


        # =====================================================
        # CUTOFF RADIUS
        # =====================================================

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


        # =====================================================
        # LOW-PASS
        # =====================================================

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


        # =====================================================
        # HIGH-PASS
        # =====================================================

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


        # =====================================================
        # RECONSTRUCT
        # =====================================================

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


        # =====================================================
        # FEATURE 5
        # =====================================================

        separator2 = tk.Frame(
            self.control_frame,
            height=2,
            bg="gray"
        )

        separator2.pack(
            fill="x",
            padx=20,
            pady=25
        )


        feature5_number = tk.Label(
            self.control_frame,
            text="Feature 5",
            font=("Arial", 10)
        )

        feature5_number.pack()


        feature5_title = tk.Label(
            self.control_frame,
            text="Compression Explorer",
            font=("Arial", 14, "bold")
        )

        feature5_title.pack(
            pady=(0, 12)
        )


        # =====================================================
        # COMPRESSION PERCENTAGE
        # =====================================================

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


        # =====================================================
        # APPLY COMPRESSION
        # =====================================================

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


        # =====================================================
        # COMPRESSION RESULT
        # =====================================================

        self.compression_info = tk.Label(
            self.control_frame,
            text="No compression performed",
            font=("Arial", 10),
            justify="left",
            wraplength=235
        )

        self.compression_info.pack(
            pady=10
        )


        # =====================================================
        # COMPRESSION VS PSNR GRAPH
        # =====================================================

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


        # =====================================================
        # FEATURE 8
        # =====================================================

        separator3 = tk.Frame(
            self.control_frame,
            height=2,
            bg="gray"
        )

        separator3.pack(
            fill="x",
            padx=20,
            pady=25
        )


        feature8_number = tk.Label(
            self.control_frame,
            text="Feature 8",
            font=("Arial", 10)
        )

        feature8_number.pack()


        feature8_title = tk.Label(
            self.control_frame,
            text="Texture Analyzer",
            font=("Arial", 14, "bold")
        )

        feature8_title.pack(
            pady=(0, 12)
        )


        # =====================================================
        # ANALYZE TEXTURE
        # =====================================================

        texture_button = tk.Button(
            self.control_frame,
            text="Analyze Texture",
            font=("Arial", 12),
            width=21,
            height=2,
            command=self.analyze_current_texture
        )

        texture_button.pack(
            pady=7
        )


        # =====================================================
        # TEXTURE INFORMATION
        # =====================================================

        self.texture_info = tk.Label(
            self.control_frame,
            text="No texture analyzed",
            font=("Arial", 10),
            justify="left",
            wraplength=235
        )

        self.texture_info.pack(
            pady=10
        )


        # =====================================================
        # COMPARE TEXTURES
        # =====================================================

        texture_compare_button = tk.Button(
            self.control_frame,
            text="Compare Textures",
            font=("Arial", 11),
            width=21,
            height=2,
            command=self.show_texture_comparison
        )

        texture_compare_button.pack(
            pady=7
        )


        # =====================================================
        # RESET
        # =====================================================

        separator4 = tk.Frame(
            self.control_frame,
            height=2,
            bg="gray"
        )

        separator4.pack(
            fill="x",
            padx=20,
            pady=25
        )


        reset_button = tk.Button(
            self.control_frame,
            text="Reset Processed",
            font=("Arial", 12),
            width=21,
            height=2,
            command=self.reset_processed
        )

        reset_button.pack(
            pady=(0, 30)
        )


        # =====================================================
        # IMAGE AREA
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
        # ORIGINAL IMAGE PANEL
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


        # =====================================================
        # PROCESSED IMAGE PANEL
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


    # =========================================================
    # OPEN IMAGE
    # =========================================================

    def open_image(self):

        file_path = select_image()

        if file_path is None:
            return

        try:

            self.current_image_name = os.path.basename(
                file_path
            )

            image = Image.open(
                file_path
            )

            image = image.convert(
                "RGB"
            )

            self.original_image = image

            # New image means old DFT does not belong
            # to the current image anymore.
            self.current_dft = None
            self.current_dft_source = None
            self.current_compressed_dft = None

            self.display_original_image()

            self.reset_processed()

            self.compression_info.configure(
                text="No compression performed"
            )

            self.texture_info.configure(
                text="No texture analyzed"
            )

        except Exception as error:

            messagebox.showerror(
                "Error",
                f"Could not open image.\n\n{error}"
            )


    # =========================================================
    # DISPLAY ORIGINAL
    # =========================================================

    def display_original_image(self):

        if self.original_image is None:
            return

        image = self.original_image.copy()

        image.thumbnail(
            (450, 550),
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
    # DISPLAY PROCESSED
    # =========================================================

    def display_processed_image(self):

        if self.processed_image is None:
            return

        image = self.processed_image.copy()

        image.thumbnail(
            (450, 550),
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
    # GRAYSCALE
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

        grayscale = self.original_image.convert(
            "L"
        )

        # Manual DFT is expensive.
        # Limit the working image size.
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
    # COMPUTE MANUAL DFT
    # =========================================================

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


    # =========================================================
    # SHOW DFT SPECTRUM
    # =========================================================

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

        try:

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

        except Exception as error:

            messagebox.showerror(
                "Spectrum Error",
                f"Could not display DFT spectrum.\n\n{error}"
            )


    # =========================================================
    # RECONSTRUCT ORIGINAL FROM DFT
    # =========================================================

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
    # LOW-PASS FILTER
    # =========================================================

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

        try:

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

        except Exception as error:

            messagebox.showerror(
                "Low-Pass Error",
                f"Could not apply low-pass filter.\n\n{error}"
            )


    # =========================================================
    # HIGH-PASS FILTER
    # =========================================================

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

        try:

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

        except Exception as error:

            messagebox.showerror(
                "High-Pass Error",
                f"Could not apply high-pass filter.\n\n{error}"
            )


    # =========================================================
    # UPDATE COMPRESSION LABEL
    # =========================================================

    def update_compression_label(self, value):

        percentage = int(
            float(value)
        )

        self.compression_value_label.configure(
            text=f"Keep DFT Coefficients: {percentage}%"
        )


    # =========================================================
    # APPLY DFT COMPRESSION
    # =========================================================

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
                /
                total_count
                *
                100
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

                psnr_text = (
                    f"{psnr:.2f} dB"
                )


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


    # =========================================================
    # PLOT COMPRESSION VS PSNR
    # =========================================================

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
                f"Could not create compression graph.\n\n{error}"
            )

        finally:

            self.root.config(
                cursor=""
            )


    # =========================================================
    # ANALYZE CURRENT TEXTURE
    # =========================================================

    def analyze_current_texture(self):

        if self.original_image is None:

            messagebox.showwarning(
                "No Image",
                "Please open a texture image first."
            )

            return

        image_array = self.prepare_image_for_dft()

        if image_array is None:
            return

        self.root.config(
            cursor="wait"
        )

        self.root.update()

        try:

            result = analyze_texture(
                image_array
            )


            # =================================================
            # DISPLAY TEXTURE SPECTRUM
            # =================================================

            spectrum = result[
                "spectrum"
            ]

            self.processed_image = Image.fromarray(
                spectrum
            ).convert(
                "RGB"
            )

            self.processed_frame.configure(
                text="Texture Frequency Spectrum"
            )

            self.display_processed_image()


            # =================================================
            # ANALYSIS VALUES
            # =================================================

            orientation = result[
                "orientation"
            ]

            texture_angle = result[
                "texture_angle"
            ]

            spacing = result[
                "spacing_pixels"
            ]

            frequency = result[
                "radial_frequency"
            ]

            strength = result[
                "periodicity_strength"
            ]


            # =================================================
            # SPACING TEXT
            # =================================================

            if np.isinf(spacing):

                spacing_text = (
                    "No clear repetition"
                )

            else:

                spacing_text = (
                    f"{spacing:.2f} pixels"
                )


            # =================================================
            # SHOW RESULTS
            # =================================================

            self.texture_info.configure(

                text=(
                    f"Image: {self.current_image_name}\n\n"
                    f"Dominant direction: {orientation}\n"
                    f"Orientation angle: {texture_angle:.1f}°\n"
                    f"Dominant frequency: "
                    f"{frequency:.4f} cycles/pixel\n"
                    f"Repeating spacing: {spacing_text}\n"
                    f"Periodicity strength: {strength:.2f}"
                )
            )


            # =================================================
            # SAVE RESULT FOR COMPARISON
            # =================================================

            if self.current_image_name is None:

                image_name = (
                    f"Texture "
                    f"{len(self.texture_results) + 1}"
                )

            else:

                image_name = self.current_image_name


            self.texture_results[
                image_name
            ] = result


        except Exception as error:

            messagebox.showerror(
                "Texture Analysis Error",
                f"Could not analyze texture.\n\n{error}"
            )

        finally:

            self.root.config(
                cursor=""
            )


    # =========================================================
    # SHOW TEXTURE COMPARISON
    # =========================================================

    def show_texture_comparison(self):

        if len(self.texture_results) == 0:

            messagebox.showwarning(
                "No Texture Results",
                "Analyze at least one texture first."
            )

            return


        # =====================================================
        # NEW WINDOW
        # =====================================================

        comparison_window = tk.Toplevel(
            self.root
        )

        comparison_window.title(
            "Texture Comparison"
        )

        comparison_window.geometry(
            "950x450"
        )


        # =====================================================
        # TITLE
        # =====================================================

        title = tk.Label(
            comparison_window,
            text="Texture Frequency Comparison",
            font=("Arial", 18, "bold")
        )

        title.pack(
            pady=20
        )


        # =====================================================
        # TABLE
        # =====================================================

        table_frame = tk.Frame(
            comparison_window
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )


        headers = [
            "Texture",
            "Direction",
            "Angle",
            "Spacing",
            "Frequency",
            "Strength"
        ]


        for column, header in enumerate(
            headers
        ):

            label = tk.Label(
                table_frame,
                text=header,
                font=("Arial", 11, "bold"),
                relief="ridge",
                borderwidth=1,
                padx=8,
                pady=8
            )

            label.grid(
                row=0,
                column=column,
                sticky="nsew"
            )


        # =====================================================
        # ADD RESULTS
        # =====================================================

        for row_index, (
            name,
            result
        ) in enumerate(
            self.texture_results.items(),
            start=1
        ):

            spacing = result[
                "spacing_pixels"
            ]

            if np.isinf(spacing):

                spacing_text = "N/A"

            else:

                spacing_text = (
                    f"{spacing:.2f}px"
                )


            values = [

                name,

                result[
                    "orientation"
                ],

                f"{result['texture_angle']:.1f}°",

                spacing_text,

                f"{result['radial_frequency']:.4f}",

                f"{result['periodicity_strength']:.2f}"
            ]


            for column, value in enumerate(
                values
            ):

                label = tk.Label(
                    table_frame,
                    text=value,
                    font=("Arial", 10),
                    relief="ridge",
                    borderwidth=1,
                    padx=8,
                    pady=8
                )

                label.grid(
                    row=row_index,
                    column=column,
                    sticky="nsew"
                )


        # =====================================================
        # MAKE TABLE COLUMNS EXPAND
        # =====================================================

        for column in range(
            len(headers)
        ):

            table_frame.grid_columnconfigure(
                column,
                weight=1
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
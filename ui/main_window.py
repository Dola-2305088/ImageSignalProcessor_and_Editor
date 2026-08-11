import asyncio
import os
from io import BytesIO

import flet as ft
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps

from algorithms.frequency.dft import (
    manual_dft2,
    create_spectrum_image,
    reconstruct_from_dft,
    apply_low_pass_filter,
    apply_high_pass_filter,
)
from algorithms.frequency.compression import compress_dft
from algorithms.frequency.texture import analyze_texture
from algorithms.frequency.hybrid import create_hybrid_image
from algorithms.frequency.color_analysis import (
    split_rgb_channels,
    create_colored_channel,
    rgb_to_ycbcr,
    calculate_channel_spectrum,
    get_channel_statistics,
)
from utils.metrics import calculate_psnr


class ImageProcessorApp:
    # ---------------------------------------------------------
    # Dark UI palette
    # ---------------------------------------------------------
    BG = "#080B12"
    SIDEBAR = "#0D121E"
    SURFACE = "#111827"
    SURFACE_2 = "#151E2F"
    SURFACE_3 = "#1B263A"
    BORDER = "#26344D"
    TEXT = "#F8FAFC"
    MUTED = "#8FA0B8"
    CYAN = "#22D3EE"
    BLUE = "#3B82F6"
    PURPLE = "#8B5CF6"
    PINK = "#EC4899"
    GREEN = "#10B981"
    ORANGE = "#F59E0B"
    RED = "#EF4444"

    NAV_ITEMS = [
        ("General", ft.Icons.HOME_OUTLINED, ft.Icons.HOME),
        ("Frequency", ft.Icons.TUNE, ft.Icons.TUNE),
        ("Compression", ft.Icons.BAR_CHART, ft.Icons.BAR_CHART),
        ("Texture", ft.Icons.GRID_VIEW, ft.Icons.GRID_VIEW),
        ("Hybrid", ft.Icons.AUTO_AWESOME_OUTLINED, ft.Icons.AUTO_AWESOME),
        ("Color", ft.Icons.PALETTE_OUTLINED, ft.Icons.PALETTE),
    ]

    def __init__(self, page: ft.Page):
        self.page = page

        # Image state
        self.original_image = None
        self.processed_image = None
        self.processed_bytes = None
        self.current_image_name = None

        # Frequency state
        self.current_dft = None
        self.current_dft_source = None
        self.current_compressed_dft = None

        # Texture state
        self.texture_results = {}

        # Hybrid-image state
        self.hybrid_low_image = None
        self.hybrid_high_image = None
        self.hybrid_low_name = None
        self.hybrid_high_name = None
        self.hybrid_low_preview_bytes = None
        self.hybrid_high_preview_bytes = None

        self._configure_page()
        self._build_ui()

    # =========================================================
    # PAGE / ROOT UI
    # =========================================================

    def _configure_page(self):
        self.page.title = "Image Signal Processor & Editor"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.dark_theme = ft.Theme(color_scheme_seed=self.CYAN)
        self.page.bgcolor = self.BG
        self.page.padding = 0
        self.page.spacing = 0

        # Desktop-focused project UI.
        self.page.window.min_width = 1080
        self.page.window.min_height = 700
        self.page.window.maximized = True

    def _build_ui(self):
        # Header values
        self.active_feature_text = ft.Text(
            "General",
            size=13,
            weight=ft.FontWeight.W_600,
            color=self.CYAN,
        )

        self.status_text = ft.Text(
            "Ready",
            size=12,
            color=self.MUTED,
            expand=True,
        )

        self.busy_ring = ft.ProgressRing(
            width=18,
            height=18,
            stroke_width=2,
            color=self.CYAN,
            visible=False,
        )

        header = self._build_header()

        # Image workspace
        self.original_title = ft.Text(
            "Original Image",
            size=15,
            weight=ft.FontWeight.BOLD,
            color=self.TEXT,
        )
        self.original_name = ft.Text(
            "No image selected",
            size=11,
            color=self.MUTED,
            max_lines=1,
        )
        self.processed_title = ft.Text(
            "Processed Result",
            size=15,
            weight=ft.FontWeight.BOLD,
            color=self.TEXT,
        )

        self.original_switcher = ft.AnimatedSwitcher(
            content=self._image_placeholder(
                ft.Icons.IMAGE_OUTLINED,
                "Open an image to begin",
                "JPG • PNG • BMP • TIFF • WebP",
            ),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=350,
            reverse_duration=180,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
        )

        self.processed_switcher = ft.AnimatedSwitcher(
            content=self._image_placeholder(
                ft.Icons.AUTO_FIX_HIGH_OUTLINED,
                "Processed output appears here",
                "Choose a feature from the sidebar",
            ),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=350,
            reverse_duration=180,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
        )

        self.original_card = self._image_card(
            self.original_title,
            self.original_name,
            self.original_switcher,
            self.BLUE,
        )
        self.processed_card = self._image_card(
            self.processed_title,
            ft.Text("Live preview", size=11, color=self.MUTED),
            self.processed_switcher,
            self.PURPLE,
        )

        image_row = ft.Row(
            controls=[
                ft.Container(content=self.original_card, expand=True),
                ft.Container(content=self.processed_card, expand=True),
            ],
            spacing=16,
        )

        # Feature panels
        self.feature_views = [
            self._build_general_panel(),
            self._build_frequency_panel(),
            self._build_compression_panel(),
            self._build_texture_panel(),
            self._build_hybrid_panel(),
            self._build_color_panel(),
        ]

        self.feature_switcher = ft.AnimatedSwitcher(
            content=self.feature_views[0],
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=300,
            reverse_duration=150,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
        )

        self.navigation_rail = ft.NavigationRail(
            selected_index=0,
            extended=True,
            label_type=ft.NavigationRailLabelType.NONE,
            min_width=76,
            min_extended_width=220,
            group_alignment=-0.95,
            use_indicator=True,
            indicator_color="#1D4ED8",
            bgcolor=self.SIDEBAR,
            scrollable=True,
            on_change=self._on_navigation_change,
            leading=ft.Container(
                padding=ft.Padding.only(top=10, bottom=14),
                content=ft.Column(
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=44,
                            height=44,
                            border_radius=ft.BorderRadius.all(14),
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_LEFT,
                                end=ft.Alignment.BOTTOM_RIGHT,
                                colors=[self.CYAN, self.PURPLE],
                            ),
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(
                                ft.Icons.WAVES,
                                color="#05070B",
                                size=26,
                            ),
                        ),
                        ft.Text(
                            "DSP LAB",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=self.MUTED,
                        ),
                    ],
                ),
            ),
            destinations=[
                ft.NavigationRailDestination(
                    label=label,
                    icon=icon,
                    selected_icon=selected,
                )
                for label, icon, selected in self.NAV_ITEMS
            ],
        )

        self.sidebar = ft.Container(
            width=230,
            bgcolor=self.SIDEBAR,
            border=ft.Border.only(
                right=ft.BorderSide(1, self.BORDER),
            ),
            animate=ft.Animation(duration=220, curve=ft.AnimationCurve.EASE_OUT),
            content=self.navigation_rail,
        )

        main_scroller = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                image_row,
                self.feature_switcher,
                ft.Container(height=6),
            ],
        )

        content = ft.Row(
            expand=True,
            spacing=0,
            controls=[
                self.sidebar,
                ft.Container(
                    expand=True,
                    padding=ft.Padding.all(20),
                    content=main_scroller,
                ),
            ],
        )

        status_bar = ft.Container(
            height=38,
            bgcolor="#090E17",
            border=ft.Border.only(top=ft.BorderSide(1, self.BORDER)),
            padding=ft.Padding.symmetric(horizontal=20),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.busy_ring,
                    self.status_text,
                    ft.Text(
                        "Spatial + Frequency Domain",
                        size=11,
                        color="#64748B",
                    ),
                ],
            ),
        )

        root = ft.Column(
            expand=True,
            spacing=0,
            controls=[header, content, status_bar],
        )

        self.page.add(root)

    def _build_header(self):
        return ft.Container(
            height=82,
            padding=ft.Padding.symmetric(horizontal=22, vertical=12),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=["#0B1220", "#10172A", "#151329"],
            ),
            border=ft.Border.only(bottom=ft.BorderSide(1, self.BORDER)),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.MENU,
                        icon_color=self.TEXT,
                        tooltip="Collapse / expand sidebar",
                        on_click=self._toggle_sidebar,
                    ),
                    ft.Container(
                        width=46,
                        height=46,
                        border_radius=ft.BorderRadius.all(15),
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_LEFT,
                            end=ft.Alignment.BOTTOM_RIGHT,
                            colors=[self.CYAN, self.PURPLE],
                        ),
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(ft.Icons.IMAGE, color="#05070B", size=26),
                    ),
                    ft.Column(
                        spacing=1,
                        expand=True,
                        controls=[
                            ft.Text(
                                "Image Signal Processor",
                                size=21,
                                weight=ft.FontWeight.BOLD,
                                color=self.TEXT,
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Text(
                                        "CSE 220 Signal Lab",
                                        size=11,
                                        color=self.MUTED,
                                    ),
                                    ft.Text("•", color="#475569"),
                                    self.active_feature_text,
                                ],
                            ),
                        ],
                    ),
                    self._action_button(
                        "Open Image",
                        ft.Icons.FOLDER_OPEN,
                        self.open_image,
                        self.BLUE,
                    ),
                    self._action_button(
                        "Save Result",
                        ft.Icons.DOWNLOAD,
                        self.save_processed,
                        self.GREEN,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.RESTART_ALT,
                        icon_color=self.MUTED,
                        tooltip="Reset result",
                        on_click=self.reset_processed,
                    ),
                ],
            ),
        )

    # =========================================================
    # GENERIC UI BUILDERS
    # =========================================================

    def _action_button(self, text, icon, handler, color):
        return ft.Button(
            content=text,
            icon=icon,
            on_click=handler,
            bgcolor=color,
            color="#FFFFFF",
            elevation=0,
        )

    def _outline_button(self, text, icon, handler):
        return ft.OutlinedButton(
            content=text,
            icon=icon,
            on_click=handler,
        )

    def _image_placeholder(self, icon, title, subtitle):
        return ft.Container(
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                tight=True,
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=46, color="#3A4A63"),
                    ft.Text(
                        title,
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=self.MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        subtitle,
                        size=11,
                        color="#5E718C",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

    def _image_card(self, title, subtitle, switcher, accent):
        card = ft.Container(
            expand=True,
            height=385,
            bgcolor=self.SURFACE,
            border=ft.Border.all(1, self.BORDER),
            border_radius=ft.BorderRadius.all(20),
            padding=ft.Padding.all(14),
            animate_scale=ft.Animation(
                duration=180,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            on_hover=self._hover_card,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=8,
                                height=32,
                                border_radius=ft.BorderRadius.all(8),
                                bgcolor=accent,
                            ),
                            ft.Column(
                                spacing=1,
                                expand=True,
                                controls=[title, subtitle],
                            ),
                        ],
                    ),
                    ft.Container(
                        expand=True,
                        alignment=ft.Alignment.CENTER,
                        bgcolor="#0A0F19",
                        border=ft.Border.all(1, "#1C2940"),
                        border_radius=ft.BorderRadius.all(16),
                        padding=10,
                        content=switcher,
                    ),
                ],
            ),
        )
        return card

    def _hover_card(self, e):
        e.control.scale = 1.008 if e.data else 1.0
        e.control.update()

    def _panel_shell(self, title, subtitle, icon, accent, controls):
        return ft.Container(
            key=f"panel-{title}",
            bgcolor=self.SURFACE,
            border=ft.Border.all(1, self.BORDER),
            border_radius=ft.BorderRadius.all(20),
            padding=ft.Padding.all(20),
            content=ft.Column(
                spacing=16,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=44,
                                height=44,
                                alignment=ft.Alignment.CENTER,
                                bgcolor=self.SURFACE_3,
                                border_radius=ft.BorderRadius.all(14),
                                content=ft.Icon(icon, color=accent, size=24),
                            ),
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        title,
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=self.TEXT,
                                    ),
                                    ft.Text(
                                        subtitle,
                                        size=11,
                                        color=self.MUTED,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=self.BORDER),
                    *controls,
                ],
            ),
        )

    def _info_box(self, title, value="Waiting for analysis…", accent=None):
        accent = accent or self.CYAN
        return ft.Container(
            bgcolor="#0C1422",
            border=ft.Border.all(1, self.BORDER),
            border_radius=ft.BorderRadius.all(14),
            padding=ft.Padding.all(14),
            content=ft.Column(
                spacing=5,
                controls=[
                    ft.Text(
                        title.upper(),
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color=accent,
                    ),
                    ft.Text(value, size=12, color=self.TEXT),
                ],
            ),
        )

    def _metric(self, title, value, accent):
        value_text = ft.Text(
            value,
            size=17,
            weight=ft.FontWeight.BOLD,
            color=self.TEXT,
        )
        box = ft.Container(
            expand=True,
            bgcolor="#0C1422",
            border=ft.Border.all(1, self.BORDER),
            border_radius=ft.BorderRadius.all(14),
            padding=ft.Padding.all(14),
            content=ft.Column(
                spacing=5,
                controls=[
                    ft.Text(title, size=10, color=self.MUTED),
                    value_text,
                    ft.Container(height=3, bgcolor=accent, border_radius=3),
                ],
            ),
        )
        return box, value_text

    # =========================================================
    # FEATURE PANELS
    # =========================================================

    def _build_general_panel(self):
        return self._panel_shell(
            "General Workspace",
            "Load an image, inspect it, or create a quick grayscale preview.",
            ft.Icons.HOME,
            self.BLUE,
            [
                ft.Row(
                    wrap=True,
                    spacing=10,
                    controls=[
                        self._action_button(
                            "Open Image", ft.Icons.FOLDER_OPEN, self.open_image, self.BLUE
                        ),
                        self._action_button(
                            "Grayscale",
                            ft.Icons.MONOCHROME_PHOTOS,
                            self.convert_to_grayscale,
                            self.PURPLE,
                        ),
                        self._outline_button(
                            "Reset Result", ft.Icons.RESTART_ALT, self.reset_processed
                        ),
                    ],
                ),
                ft.Container(
                    bgcolor="#0C1422",
                    border_radius=ft.BorderRadius.all(14),
                    padding=16,
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=self.CYAN),
                            ft.Text(
                                "Original images are kept intact. Processing always appears in the result card, so you can compare before and after immediately.",
                                size=12,
                                color=self.MUTED,
                                expand=True,
                            ),
                        ],
                    ),
                ),
            ],
        )

    def _build_frequency_panel(self):
        self.cutoff_value_text = ft.Text(
            "15 px",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=self.CYAN,
        )
        self.cutoff_slider = ft.Slider(
            min=2,
            max=60,
            value=15,
            divisions=58,
            active_color=self.CYAN,
            on_change=self._on_cutoff_change,
        )

        return self._panel_shell(
            "Feature 4 — Frequency Editor",
            "Inspect the 2D DFT and interactively keep low- or high-frequency regions.",
            ft.Icons.TUNE,
            self.CYAN,
            [
                ft.Row(
                    wrap=True,
                    spacing=10,
                    controls=[
                        self._action_button(
                            "DFT Spectrum",
                            ft.Icons.BUBBLE_CHART,
                            self.show_frequency_spectrum,
                            self.PURPLE,
                        ),
                        self._outline_button(
                            "Reconstruct DFT",
                            ft.Icons.REPLAY,
                            self.reconstruct_dft,
                        ),
                    ],
                ),
                ft.Container(
                    bgcolor="#0C1422",
                    border_radius=ft.BorderRadius.all(14),
                    padding=16,
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "Cutoff Radius",
                                        size=12,
                                        weight=ft.FontWeight.W_600,
                                        color=self.TEXT,
                                    ),
                                    ft.Container(expand=True),
                                    self.cutoff_value_text,
                                ],
                            ),
                            self.cutoff_slider,
                            ft.Text(
                                "Low-pass keeps the bright center of the shifted spectrum; high-pass removes it and emphasizes fine detail.",
                                size=10,
                                color=self.MUTED,
                            ),
                        ],
                    ),
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    controls=[
                        self._action_button(
                            "Apply Low-Pass",
                            ft.Icons.BLUR_ON,
                            self.apply_low_pass,
                            self.BLUE,
                        ),
                        self._action_button(
                            "Apply High-Pass",
                            ft.Icons.FILTER_ALT,
                            self.apply_high_pass,
                            self.PINK,
                        ),
                    ],
                ),
            ],
        )

    def _build_compression_panel(self):
        self.compression_percent_text = ft.Text(
            "10%",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=self.GREEN,
        )
        self.compression_slider = ft.Slider(
            min=1,
            max=100,
            value=10,
            divisions=99,
            active_color=self.GREEN,
            on_change=self._on_compression_change,
        )

        self.metric_total, self.metric_total_value = self._metric(
            "Total coefficients", "—", self.BLUE
        )
        self.metric_kept, self.metric_kept_value = self._metric(
            "Kept", "—", self.GREEN
        )
        self.metric_reduction, self.metric_reduction_value = self._metric(
            "Reduction", "—", self.ORANGE
        )
        self.metric_psnr, self.metric_psnr_value = self._metric(
            "PSNR", "—", self.PURPLE
        )

        return self._panel_shell(
            "Feature 5 — Compression Explorer",
            "Retain only the strongest DFT coefficients and measure reconstruction quality.",
            ft.Icons.BAR_CHART,
            self.GREEN,
            [
                ft.Container(
                    bgcolor="#0C1422",
                    border_radius=ft.BorderRadius.all(14),
                    padding=16,
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "Coefficients to keep",
                                        size=12,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                    ft.Container(expand=True),
                                    self.compression_percent_text,
                                ],
                            ),
                            self.compression_slider,
                        ],
                    ),
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        self.metric_total,
                        self.metric_kept,
                        self.metric_reduction,
                        self.metric_psnr,
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    controls=[
                        self._action_button(
                            "Apply Compression",
                            ft.Icons.COMPRESS,
                            self.apply_dft_compression,
                            self.GREEN,
                        ),
                        self._action_button(
                            "Quality Curve",
                            ft.Icons.SHOW_CHART,
                            self.plot_compression_quality,
                            self.PURPLE,
                        ),
                    ],
                ),
            ],
        )

    def _build_texture_panel(self):
        self.texture_info = ft.Text(
            "Analyze a repeating texture such as brick, cloth, tiles, or grass.",
            size=12,
            color=self.MUTED,
        )
        self.texture_comparison = ft.Column(spacing=6)

        return self._panel_shell(
            "Feature 8 — Texture Analyzer",
            "Estimate dominant orientation and repetition using frequency-domain peaks — no machine learning.",
            ft.Icons.GRID_VIEW,
            self.ORANGE,
            [
                ft.Row(
                    wrap=True,
                    spacing=10,
                    controls=[
                        self._action_button(
                            "Analyze Texture",
                            ft.Icons.SEARCH,
                            self.analyze_current_texture,
                            self.ORANGE,
                        ),
                        self._outline_button(
                            "Show Comparisons",
                            ft.Icons.COMPARE_ARROWS,
                            self.show_texture_comparison,
                        ),
                    ],
                ),
                ft.Container(
                    bgcolor="#17130B",
                    border=ft.Border.all(1, "#4B3510"),
                    border_radius=ft.BorderRadius.all(14),
                    padding=16,
                    content=self.texture_info,
                ),
                self.texture_comparison,
            ],
        )

    def _build_hybrid_panel(self):
        self.hybrid_low_name_text = ft.Text(
            "Not selected", size=11, color=self.MUTED, max_lines=1
        )
        self.hybrid_high_name_text = ft.Text(
            "Not selected", size=11, color=self.MUTED, max_lines=1
        )

        self.hybrid_low_preview = ft.AnimatedSwitcher(
            content=ft.Icon(ft.Icons.IMAGE_OUTLINED, size=36, color="#40516D"),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=250,
        )
        self.hybrid_high_preview = ft.AnimatedSwitcher(
            content=ft.Icon(ft.Icons.IMAGE_OUTLINED, size=36, color="#40516D"),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=250,
        )

        self.hybrid_low_radius_text = ft.Text(
            "15 px", weight=ft.FontWeight.BOLD, color=self.BLUE
        )
        self.hybrid_high_radius_text = ft.Text(
            "15 px", weight=ft.FontWeight.BOLD, color=self.PINK
        )
        self.hybrid_low_radius = ft.Slider(
            min=2,
            max=50,
            value=15,
            divisions=48,
            active_color=self.BLUE,
            on_change=self._on_hybrid_low_radius_change,
        )
        self.hybrid_high_radius = ft.Slider(
            min=2,
            max=50,
            value=15,
            divisions=48,
            active_color=self.PINK,
            on_change=self._on_hybrid_high_radius_change,
        )
        self.hybrid_info = ft.Text(
            "Select Image A and Image B, then tune the two cutoffs.",
            size=11,
            color=self.MUTED,
        )

        source_row = ft.Row(
            spacing=12,
            controls=[
                self._hybrid_source_card(
                    "IMAGE A • LOW FREQUENCIES",
                    self.hybrid_low_name_text,
                    self.hybrid_low_preview,
                    self.BLUE,
                    self.select_hybrid_low_image,
                ),
                self._hybrid_source_card(
                    "IMAGE B • HIGH FREQUENCIES",
                    self.hybrid_high_name_text,
                    self.hybrid_high_preview,
                    self.PINK,
                    self.select_hybrid_high_image,
                ),
            ],
        )

        return self._panel_shell(
            "Feature 9 — Hybrid Images",
            "Combine broad structure from one image with fine details from another.",
            ft.Icons.AUTO_AWESOME,
            self.PINK,
            [
                source_row,
                ft.Row(
                    spacing=12,
                    controls=[
                        self._slider_card(
                            "Low-pass radius",
                            self.hybrid_low_radius_text,
                            self.hybrid_low_radius,
                            self.BLUE,
                        ),
                        self._slider_card(
                            "High-pass radius",
                            self.hybrid_high_radius_text,
                            self.hybrid_high_radius,
                            self.PINK,
                        ),
                    ],
                ),
                self._action_button(
                    "Create Hybrid Image",
                    ft.Icons.AUTO_AWESOME,
                    self.generate_hybrid_image,
                    self.PURPLE,
                ),
                self.hybrid_info,
            ],
        )

    def _hybrid_source_card(self, title, name_text, preview, accent, handler):
        return ft.Container(
            expand=True,
            bgcolor="#0C1422",
            border=ft.Border.all(1, self.BORDER),
            border_radius=ft.BorderRadius.all(14),
            padding=14,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=92,
                        height=72,
                        bgcolor="#080D16",
                        border_radius=ft.BorderRadius.all(12),
                        alignment=ft.Alignment.CENTER,
                        content=preview,
                    ),
                    ft.Column(
                        spacing=5,
                        expand=True,
                        controls=[
                            ft.Text(
                                title,
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=accent,
                            ),
                            name_text,
                            ft.OutlinedButton(
                                content="Choose image",
                                icon=ft.Icons.FOLDER_OPEN,
                                on_click=handler,
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _slider_card(self, title, value_text, slider, accent):
        return ft.Container(
            expand=True,
            bgcolor="#0C1422",
            border_radius=ft.BorderRadius.all(14),
            padding=14,
            content=ft.Column(
                spacing=3,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(title, size=11, color=self.TEXT),
                            ft.Container(expand=True),
                            value_text,
                        ],
                    ),
                    slider,
                ],
            ),
        )

    def _build_color_panel(self):
        self.color_info = ft.Text(
            "Choose a channel or analysis mode.",
            size=12,
            color=self.MUTED,
        )

        return self._panel_shell(
            "Feature 12 — Color & Color-Space Analyzer",
            "Inspect RGB channels, histograms, per-channel spectra, and YCbCr components.",
            ft.Icons.PALETTE,
            self.CYAN,
            [
                ft.Text(
                    "RGB CHANNELS",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=self.MUTED,
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    controls=[
                        self._action_button(
                            "Red Channel",
                            ft.Icons.LENS,
                            lambda e: self.show_rgb_channel("R"),
                            self.RED,
                        ),
                        self._action_button(
                            "Green Channel",
                            ft.Icons.LENS,
                            lambda e: self.show_rgb_channel("G"),
                            self.GREEN,
                        ),
                        self._action_button(
                            "Blue Channel",
                            ft.Icons.LENS,
                            lambda e: self.show_rgb_channel("B"),
                            self.BLUE,
                        ),
                    ],
                ),
                ft.Divider(height=1, color=self.BORDER),
                ft.Text(
                    "ANALYSIS",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=self.MUTED,
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    controls=[
                        self._action_button(
                            "RGB Histograms",
                            ft.Icons.BAR_CHART,
                            self.show_rgb_histograms,
                            self.ORANGE,
                        ),
                        self._action_button(
                            "RGB Frequencies",
                            ft.Icons.WAVES,
                            self.show_rgb_frequency_spectra,
                            self.PURPLE,
                        ),
                        self._action_button(
                            "YCbCr Channels",
                            ft.Icons.COLOR_LENS,
                            self.show_ycbcr_channels,
                            self.CYAN,
                        ),
                    ],
                ),
                ft.Container(
                    bgcolor="#0C1422",
                    border=ft.Border.all(1, self.BORDER),
                    border_radius=ft.BorderRadius.all(14),
                    padding=16,
                    content=self.color_info,
                ),
            ],
        )

    # =========================================================
    # NAVIGATION / ANIMATION EVENTS
    # =========================================================

    def _toggle_sidebar(self, e):
        self.navigation_rail.extended = not self.navigation_rail.extended
        self.navigation_rail.label_type = (
            ft.NavigationRailLabelType.NONE
            if self.navigation_rail.extended
            else ft.NavigationRailLabelType.ALL
        )
        self.sidebar.width = 230 if self.navigation_rail.extended else 92
        self.navigation_rail.update()
        self.sidebar.update()

    def _on_navigation_change(self, e):
        index = e.control.selected_index or 0
        self.active_feature_text.value = self.NAV_ITEMS[index][0]
        self.feature_switcher.content = self.feature_views[index]
        self.active_feature_text.update()
        self.feature_switcher.update()

    def _on_cutoff_change(self, e):
        self.cutoff_value_text.value = f"{int(e.control.value)} px"
        self.cutoff_value_text.update()

    def _on_compression_change(self, e):
        self.compression_percent_text.value = f"{int(e.control.value)}%"
        self.compression_percent_text.update()

    def _on_hybrid_low_radius_change(self, e):
        self.hybrid_low_radius_text.value = f"{int(e.control.value)} px"
        self.hybrid_low_radius_text.update()

    def _on_hybrid_high_radius_change(self, e):
        self.hybrid_high_radius_text.value = f"{int(e.control.value)} px"
        self.hybrid_high_radius_text.update()

    # =========================================================
    # FILE / IMAGE HELPERS
    # =========================================================

    async def _pick_pil_image(self, title):
        files = await ft.FilePicker().pick_files(
            dialog_title=title,
            allow_multiple=False,
            with_data=True,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=[
                "jpg",
                "jpeg",
                "png",
                "bmp",
                "tif",
                "tiff",
                "webp",
            ],
        )

        if not files:
            return None, None

        selected = files[0]
        raw = selected.bytes

        if raw is None:
            path = getattr(selected, "path", None)
            if path:
                with open(path, "rb") as file:
                    raw = file.read()

        if raw is None:
            raise ValueError("The selected image could not be read.")

        image = Image.open(BytesIO(raw)).convert("RGB")
        return image, selected.name

    @staticmethod
    def _pil_to_png_bytes(image):
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def _image_control_from_pil(self, image):
        return self._image_control_from_bytes(self._pil_to_png_bytes(image))

    def _image_control_from_bytes(self, image_bytes):
        return ft.Image(
            src=image_bytes,
            width=560,
            height=300,
            fit=ft.BoxFit.CONTAIN,
            filter_quality=ft.FilterQuality.HIGH,
            border_radius=ft.BorderRadius.all(12),
            gapless_playback=True,
            fade_in_animation=ft.Animation(
                duration=300,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),
        )

    def _set_original_preview(self, image, name):
        self.original_switcher.content = self._image_control_from_pil(image)
        self.original_name.value = name
        self.original_switcher.update()
        self.original_name.update()

    def _set_processed_pil(self, image, title, status=None):
        self.processed_image = image.copy()
        self.processed_bytes = self._pil_to_png_bytes(image)
        self.processed_switcher.content = self._image_control_from_bytes(
            self.processed_bytes
        )
        self.processed_title.value = title
        self.processed_switcher.update()
        self.processed_title.update()
        if status:
            self._set_status(status)

    def _set_processed_bytes(self, image_bytes, title, status=None):
        self.processed_image = None
        self.processed_bytes = image_bytes
        self.processed_switcher.content = self._image_control_from_bytes(image_bytes)
        self.processed_title.value = title
        self.processed_switcher.update()
        self.processed_title.update()
        if status:
            self._set_status(status)

    def _require_image(self):
        if self.original_image is None:
            self._toast("Open an image first.", error=True)
            return False
        return True

    def _set_status(self, text):
        self.status_text.value = text
        self.status_text.update()

    def _set_busy(self, busy, text=None):
        self.busy_ring.visible = busy
        if text:
            self.status_text.value = text
        self.busy_ring.update()
        self.status_text.update()

    def _toast(self, text, error=False):
        icon = ft.Icons.ERROR_OUTLINE if error else ft.Icons.CHECK_CIRCLE_OUTLINE
        color = self.RED if error else self.GREEN
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(icon, color=color),
                        ft.Text(text, color=self.TEXT),
                    ]
                ),
                show_close_icon=True,
            )
        )

    # =========================================================
    # GENERAL ACTIONS
    # =========================================================

    async def open_image(self, e):
        try:
            image, name = await self._pick_pil_image("Open an image")
            if image is None:
                return

            self.original_image = image
            self.current_image_name = name
            self.current_dft = None
            self.current_dft_source = None
            self.current_compressed_dft = None

            self._set_original_preview(image, name)
            self.reset_processed(None)

            self.metric_total_value.value = "—"
            self.metric_kept_value.value = "—"
            self.metric_reduction_value.value = "—"
            self.metric_psnr_value.value = "—"
            self.metric_total_value.update()
            self.metric_kept_value.update()
            self.metric_reduction_value.update()
            self.metric_psnr_value.update()

            self.texture_info.value = (
                "Analyze a repeating texture such as brick, cloth, tiles, or grass."
            )
            self.color_info.value = "Choose a channel or analysis mode."
            self.texture_info.update()
            self.color_info.update()

            self._set_status(f"Loaded {name}")
            self._toast(f"Loaded {name}")

        except Exception as error:
            self._toast(f"Could not open image: {error}", error=True)

    async def save_processed(self, e):
        if not self.processed_bytes:
            self._toast("There is no processed result to save.", error=True)
            return

        try:
            path = await ft.FilePicker().save_file(
                dialog_title="Save processed image",
                file_name="processed_result.png",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["png"],
                src_bytes=self.processed_bytes,
            )
            if path:
                self._toast(f"Saved result: {os.path.basename(path)}")
                self._set_status(f"Saved processed result to {path}")
        except Exception as error:
            self._toast(f"Could not save result: {error}", error=True)

    def reset_processed(self, e):
        self.processed_image = None
        self.processed_bytes = None
        self.processed_title.value = "Processed Result"
        self.processed_switcher.content = self._image_placeholder(
            ft.Icons.AUTO_FIX_HIGH_OUTLINED,
            "Processed output appears here",
            "Choose a feature from the sidebar",
        )
        self.processed_title.update()
        self.processed_switcher.update()
        self._set_status("Result cleared")

    def convert_to_grayscale(self, e):
        if not self._require_image():
            return

        grayscale = ImageOps.grayscale(self.original_image).convert("RGB")
        self._set_processed_pil(
            grayscale,
            "Grayscale Preview",
            "Converted image to grayscale.",
        )

    # =========================================================
    # DFT HELPERS
    # =========================================================

    def _prepare_image_for_dft(self):
        grayscale = self.original_image.convert("L")
        grayscale.thumbnail((128, 128), Image.Resampling.LANCZOS)
        return np.array(grayscale, dtype=np.float64)

    def _compute_dft_sync(self):
        image_array = self._prepare_image_for_dft()
        return image_array, manual_dft2(image_array)

    async def _ensure_dft(self):
        if self.current_dft is not None:
            return True
        if not self._require_image():
            return False

        self._set_busy(True, "Computing manual 2D DFT…")
        try:
            source, dft = await asyncio.to_thread(self._compute_dft_sync)
            self.current_dft_source = source
            self.current_dft = dft
            self._set_status("Manual 2D DFT completed.")
            return True
        except Exception as error:
            self._toast(f"DFT error: {error}", error=True)
            return False
        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 4 — FREQUENCY EDITOR
    # =========================================================

    async def show_frequency_spectrum(self, e):
        if not await self._ensure_dft():
            return
        spectrum = await asyncio.to_thread(create_spectrum_image, self.current_dft)
        image = Image.fromarray(spectrum).convert("RGB")
        self._set_processed_pil(
            image,
            "2D DFT Frequency Spectrum",
            "Displaying centered log-magnitude DFT spectrum.",
        )

    async def reconstruct_dft(self, e):
        if not await self._ensure_dft():
            return
        reconstructed = await asyncio.to_thread(
            reconstruct_from_dft, self.current_dft
        )
        image = Image.fromarray(reconstructed).convert("RGB")
        self._set_processed_pil(
            image,
            "Reconstructed from DFT",
            "Inverse DFT reconstruction completed.",
        )

    async def apply_low_pass(self, e):
        if not await self._ensure_dft():
            return
        radius = int(self.cutoff_slider.value)
        self._set_busy(True, "Applying low-pass frequency mask…")
        try:
            filtered = await asyncio.to_thread(
                apply_low_pass_filter, self.current_dft, radius
            )
            reconstructed = await asyncio.to_thread(
                reconstruct_from_dft, filtered
            )
            self._set_processed_pil(
                Image.fromarray(reconstructed).convert("RGB"),
                f"Low-Pass • Radius {radius}",
                f"Low-pass filter applied with radius {radius}.",
            )
        finally:
            self._set_busy(False)

    async def apply_high_pass(self, e):
        if not await self._ensure_dft():
            return
        radius = int(self.cutoff_slider.value)
        self._set_busy(True, "Applying high-pass frequency mask…")
        try:
            filtered = await asyncio.to_thread(
                apply_high_pass_filter, self.current_dft, radius
            )
            reconstructed = await asyncio.to_thread(
                reconstruct_from_dft, filtered
            )
            self._set_processed_pil(
                Image.fromarray(reconstructed).convert("RGB"),
                f"High-Pass • Radius {radius}",
                f"High-pass filter applied with radius {radius}.",
            )
        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 5 — COMPRESSION
    # =========================================================

    async def apply_dft_compression(self, e):
        if not await self._ensure_dft():
            return

        percentage = int(self.compression_slider.value)
        self._set_busy(True, "Compressing DFT coefficients…")

        try:
            (
                compressed_frequency,
                _,
                kept_count,
                total_count,
            ) = await asyncio.to_thread(
                compress_dft, self.current_dft, percentage
            )

            self.current_compressed_dft = compressed_frequency
            reconstructed = await asyncio.to_thread(
                reconstruct_from_dft, compressed_frequency
            )

            original_for_psnr = np.clip(
                self.current_dft_source, 0, 255
            ).astype(np.uint8)
            psnr = calculate_psnr(original_for_psnr, reconstructed)

            removed_count = total_count - kept_count
            reduction = removed_count / total_count * 100.0
            psnr_text = "∞" if np.isinf(psnr) else f"{psnr:.2f} dB"

            self.metric_total_value.value = f"{total_count:,}"
            self.metric_kept_value.value = f"{kept_count:,}"
            self.metric_reduction_value.value = f"{reduction:.1f}%"
            self.metric_psnr_value.value = psnr_text
            self.metric_total_value.update()
            self.metric_kept_value.update()
            self.metric_reduction_value.update()
            self.metric_psnr_value.update()

            self._set_processed_pil(
                Image.fromarray(reconstructed).convert("RGB"),
                f"DFT Compression • Keep {percentage}%",
                f"Compression complete — retained {percentage}% of coefficients.",
            )

        except Exception as error:
            self._toast(f"Compression error: {error}", error=True)
        finally:
            self._set_busy(False)

    def _build_compression_curve_plot(self):
        percentages = [1, 2, 5, 10, 20, 40, 60, 80, 95]
        original = np.clip(self.current_dft_source, 0, 255).astype(np.uint8)
        psnr_values = []

        for percentage in percentages:
            compressed, _, _, _ = compress_dft(self.current_dft, percentage)
            reconstructed = reconstruct_from_dft(compressed)
            psnr_values.append(calculate_psnr(original, reconstructed))

        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        fig.patch.set_facecolor("#0A0F19")
        ax.set_facecolor("#0A0F19")
        ax.plot(percentages, psnr_values, marker="o", linewidth=2.2)
        ax.fill_between(percentages, psnr_values, alpha=0.08)
        ax.set_xlabel("DFT coefficients kept (%)", color="#CBD5E1")
        ax.set_ylabel("PSNR (dB)", color="#CBD5E1")
        ax.set_title(
            "Compression vs Reconstruction Quality",
            color="#F8FAFC",
            weight="bold",
        )
        ax.grid(alpha=0.16)
        ax.tick_params(colors="#94A3B8")
        for spine in ax.spines.values():
            spine.set_color("#334155")
        fig.tight_layout()
        return self._figure_to_png_bytes(fig)

    async def plot_compression_quality(self, e):
        if not await self._ensure_dft():
            return

        self._set_busy(True, "Building compression quality curve…")
        try:
            plot_bytes = await asyncio.to_thread(
                self._build_compression_curve_plot
            )
            self._set_processed_bytes(
                plot_bytes,
                "Compression vs PSNR",
                "Compression quality curve generated.",
            )
        except Exception as error:
            self._toast(f"Could not create plot: {error}", error=True)
        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 8 — TEXTURE ANALYZER
    # =========================================================

    async def analyze_current_texture(self, e):
        if not self._require_image():
            return

        self._set_busy(True, "Analyzing texture spectrum…")
        try:
            image_array = self._prepare_image_for_dft()
            result = await asyncio.to_thread(analyze_texture, image_array)

            spectrum = Image.fromarray(result["spectrum"]).convert("RGB")
            self._set_processed_pil(
                spectrum,
                "Texture Frequency Spectrum",
                f"Texture analysis completed for {self.current_image_name}.",
            )

            spacing = result["spacing_pixels"]
            spacing_text = (
                "No clear repetition"
                if np.isinf(spacing)
                else f"{spacing:.2f} px"
            )

            self.texture_info.value = (
                f"{self.current_image_name}\n"
                f"Direction: {result['orientation']}    •    "
                f"Angle: {result['texture_angle']:.1f}°\n"
                f"Frequency: {result['radial_frequency']:.4f} cycles/pixel    •    "
                f"Spacing: {spacing_text}\n"
                f"Periodicity strength: {result['periodicity_strength']:.2f}"
            )
            self.texture_info.update()

            key = self.current_image_name or f"Texture {len(self.texture_results) + 1}"
            self.texture_results[key] = result

        except Exception as error:
            self._toast(f"Texture analysis error: {error}", error=True)
        finally:
            self._set_busy(False)

    def show_texture_comparison(self, e):
        if not self.texture_results:
            self._toast("Analyze at least one texture first.", error=True)
            return

        rows = [
            ft.Container(
                bgcolor=self.SURFACE_3,
                border_radius=ft.BorderRadius.all(10),
                padding=10,
                content=ft.Row(
                    controls=[
                        ft.Text("Texture", width=150, weight=ft.FontWeight.BOLD),
                        ft.Text("Direction", width=100, weight=ft.FontWeight.BOLD),
                        ft.Text("Angle", width=85, weight=ft.FontWeight.BOLD),
                        ft.Text("Spacing", width=95, weight=ft.FontWeight.BOLD),
                        ft.Text("Frequency", width=100, weight=ft.FontWeight.BOLD),
                        ft.Text("Strength", width=90, weight=ft.FontWeight.BOLD),
                    ]
                ),
            )
        ]

        for name, result in self.texture_results.items():
            spacing = result["spacing_pixels"]
            spacing_text = "N/A" if np.isinf(spacing) else f"{spacing:.2f}px"
            rows.append(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                    border=ft.Border.only(bottom=ft.BorderSide(1, self.BORDER)),
                    content=ft.Row(
                        controls=[
                            ft.Text(name, width=150, color=self.TEXT),
                            ft.Text(result["orientation"], width=100, color=self.MUTED),
                            ft.Text(f"{result['texture_angle']:.1f}°", width=85),
                            ft.Text(spacing_text, width=95),
                            ft.Text(f"{result['radial_frequency']:.4f}", width=100),
                            ft.Text(f"{result['periodicity_strength']:.2f}", width=90),
                        ]
                    ),
                )
            )

        self.texture_comparison.controls = [
            ft.Text(
                "Saved texture comparisons",
                size=13,
                weight=ft.FontWeight.BOLD,
                color=self.ORANGE,
            ),
            ft.Row(
                scroll=ft.ScrollMode.AUTO,
                controls=[ft.Column(spacing=2, controls=rows)],
            ),
        ]
        self.texture_comparison.update()

    # =========================================================
    # FEATURE 9 — HYBRID IMAGES
    # =========================================================

    async def select_hybrid_low_image(self, e):
        try:
            image, name = await self._pick_pil_image(
                "Select low-frequency source image"
            )
            if image is None:
                return

            self.hybrid_low_image = image
            self.hybrid_low_name = name
            self.hybrid_low_preview_bytes = self._pil_to_png_bytes(image)
            self.hybrid_low_name_text.value = name
            self.hybrid_low_preview.content = ft.Image(
                src=self.hybrid_low_preview_bytes,
                width=88,
                height=68,
                fit=ft.BoxFit.COVER,
                border_radius=ft.BorderRadius.all(10),
            )
            self.hybrid_low_name_text.update()
            self.hybrid_low_preview.update()

            # Treat A as the current original image too.
            self.original_image = image
            self.current_image_name = name
            self.current_dft = None
            self.current_dft_source = None
            self._set_original_preview(image, name)
            self.hybrid_info.value = "Image A selected. Now choose Image B."
            self.hybrid_info.update()
            self._set_status(f"Hybrid low-frequency source: {name}")

        except Exception as error:
            self._toast(f"Could not select Image A: {error}", error=True)

    async def select_hybrid_high_image(self, e):
        try:
            image, name = await self._pick_pil_image(
                "Select high-frequency source image"
            )
            if image is None:
                return

            self.hybrid_high_image = image
            self.hybrid_high_name = name
            self.hybrid_high_preview_bytes = self._pil_to_png_bytes(image)
            self.hybrid_high_name_text.value = name
            self.hybrid_high_preview.content = ft.Image(
                src=self.hybrid_high_preview_bytes,
                width=88,
                height=68,
                fit=ft.BoxFit.COVER,
                border_radius=ft.BorderRadius.all(10),
            )
            self.hybrid_high_name_text.update()
            self.hybrid_high_preview.update()
            self.hybrid_info.value = (
                "Both sources are ready. Adjust the radii and create the hybrid."
            )
            self.hybrid_info.update()
            self._set_status(f"Hybrid high-frequency source: {name}")

        except Exception as error:
            self._toast(f"Could not select Image B: {error}", error=True)

    def _create_hybrid_sync(self, low_radius, high_radius):
        target_size = (128, 128)
        low_image = ImageOps.fit(
            self.hybrid_low_image,
            target_size,
            method=Image.Resampling.LANCZOS,
        )
        high_image = ImageOps.fit(
            self.hybrid_high_image,
            target_size,
            method=Image.Resampling.LANCZOS,
        )

        low_array = np.array(low_image, dtype=np.float64)
        high_array = np.array(high_image, dtype=np.float64)
        return create_hybrid_image(
            low_array,
            high_array,
            low_radius,
            high_radius,
        )

    async def generate_hybrid_image(self, e):
        if self.hybrid_low_image is None or self.hybrid_high_image is None:
            self._toast("Select both hybrid source images first.", error=True)
            return

        low_radius = int(self.hybrid_low_radius.value)
        high_radius = int(self.hybrid_high_radius.value)

        self._set_busy(True, "Creating hybrid image from two DFTs…")
        try:
            result = await asyncio.to_thread(
                self._create_hybrid_sync,
                low_radius,
                high_radius,
            )
            hybrid = Image.fromarray(result["hybrid"])
            self._set_processed_pil(
                hybrid,
                "Hybrid Image",
                "Hybrid image created successfully.",
            )
            self.hybrid_info.value = (
                f"Low frequencies: {self.hybrid_low_name} (r={low_radius})\n"
                f"High frequencies: {self.hybrid_high_name} (r={high_radius})"
            )
            self.hybrid_info.update()
        except Exception as error:
            self._toast(f"Hybrid image error: {error}", error=True)
        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 12 — COLOR ANALYSIS
    # =========================================================

    def show_rgb_channel(self, channel_name):
        if not self._require_image():
            return

        try:
            image_array = np.array(self.original_image, dtype=np.uint8)
            red, green, blue = split_rgb_channels(image_array)
            channel_map = {"R": red, "G": green, "B": blue}
            name_map = {"R": "Red", "G": "Green", "B": "Blue"}

            channel = channel_map[channel_name]
            colored = create_colored_channel(channel, channel_name)
            stats = get_channel_statistics(channel)

            self._set_processed_pil(
                Image.fromarray(colored),
                f"{name_map[channel_name]} Channel",
                f"Displaying the {name_map[channel_name].lower()} channel.",
            )
            self.color_info.value = (
                f"{name_map[channel_name]} channel statistics\n"
                f"Mean: {stats['mean']:.2f}    •    Std: {stats['std']:.2f}    •    "
                f"Min: {stats['min']:.0f}    •    Max: {stats['max']:.0f}"
            )
            self.color_info.update()
        except Exception as error:
            self._toast(f"Color analysis error: {error}", error=True)

    def _build_rgb_histogram_plot(self):
        image_array = np.array(self.original_image, dtype=np.uint8)
        red, green, blue = split_rgb_channels(image_array)

        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        fig.patch.set_facecolor("#0A0F19")
        ax.set_facecolor("#0A0F19")
        ax.hist(red.flatten(), bins=256, range=(0, 255), alpha=0.45, label="Red", color="#EF4444")
        ax.hist(green.flatten(), bins=256, range=(0, 255), alpha=0.45, label="Green", color="#10B981")
        ax.hist(blue.flatten(), bins=256, range=(0, 255), alpha=0.45, label="Blue", color="#3B82F6")
        ax.set_xlabel("Intensity", color="#CBD5E1")
        ax.set_ylabel("Pixel count", color="#CBD5E1")
        ax.set_title("RGB Channel Histogram Comparison", color="#F8FAFC", weight="bold")
        ax.tick_params(colors="#94A3B8")
        ax.grid(alpha=0.12)
        ax.legend(facecolor="#111827", edgecolor="#334155", labelcolor="#E2E8F0")
        for spine in ax.spines.values():
            spine.set_color("#334155")
        fig.tight_layout()
        return self._figure_to_png_bytes(fig)

    async def show_rgb_histograms(self, e):
        if not self._require_image():
            return
        self._set_busy(True, "Building RGB histograms…")
        try:
            plot_bytes = await asyncio.to_thread(self._build_rgb_histogram_plot)
            self._set_processed_bytes(
                plot_bytes,
                "RGB Histogram Comparison",
                "RGB histogram comparison generated.",
            )
            self.color_info.value = (
                "Each distribution shows how intensities are spread across the red, green, and blue channels."
            )
            self.color_info.update()
        except Exception as error:
            self._toast(f"Histogram error: {error}", error=True)
        finally:
            self._set_busy(False)

    def _build_rgb_frequency_plot(self):
        working = self.original_image.copy()
        working.thumbnail((128, 128), Image.Resampling.LANCZOS)
        image_array = np.array(working, dtype=np.uint8)
        red, green, blue = split_rgb_channels(image_array)

        spectra = [
            calculate_channel_spectrum(red),
            calculate_channel_spectrum(green),
            calculate_channel_spectrum(blue),
        ]
        titles = ["Red Spectrum", "Green Spectrum", "Blue Spectrum"]

        fig, axes = plt.subplots(1, 3, figsize=(11, 4))
        fig.patch.set_facecolor("#0A0F19")
        for ax, spectrum, title in zip(axes, spectra, titles):
            ax.imshow(spectrum, cmap="gray")
            ax.set_title(title, color="#F8FAFC", weight="bold")
            ax.axis("off")
        fig.tight_layout()
        return self._figure_to_png_bytes(fig)

    async def show_rgb_frequency_spectra(self, e):
        if not self._require_image():
            return
        self._set_busy(True, "Computing three channel DFT spectra…")
        try:
            plot_bytes = await asyncio.to_thread(self._build_rgb_frequency_plot)
            self._set_processed_bytes(
                plot_bytes,
                "RGB Frequency Content",
                "RGB channel spectra generated.",
            )
            self.color_info.value = (
                "The center contains low-frequency energy; farther regions represent progressively finer spatial detail."
            )
            self.color_info.update()
        except Exception as error:
            self._toast(f"RGB frequency error: {error}", error=True)
        finally:
            self._set_busy(False)

    def _build_ycbcr_plot(self):
        image_array = np.array(self.original_image, dtype=np.uint8)
        y, cb, cr = rgb_to_ycbcr(image_array)

        fig, axes = plt.subplots(1, 3, figsize=(11, 4))
        fig.patch.set_facecolor("#0A0F19")
        items = [
            (y, "Y • Luminance"),
            (cb, "Cb • Blue chroma"),
            (cr, "Cr • Red chroma"),
        ]
        for ax, channel, title in zip(axes, [y, cb, cr], [x[1] for x in items]):
            ax.imshow(channel, cmap="gray", vmin=0, vmax=255)
            ax.set_title(title, color="#F8FAFC", weight="bold")
            ax.axis("off")
        fig.tight_layout()
        return self._figure_to_png_bytes(fig), y, cb, cr

    async def show_ycbcr_channels(self, e):
        if not self._require_image():
            return
        self._set_busy(True, "Converting RGB to YCbCr…")
        try:
            plot_bytes, y, cb, cr = await asyncio.to_thread(self._build_ycbcr_plot)
            self._set_processed_bytes(
                plot_bytes,
                "YCbCr Color Space",
                "YCbCr components generated.",
            )

            y_stats = get_channel_statistics(y)
            cb_stats = get_channel_statistics(cb)
            cr_stats = get_channel_statistics(cr)
            self.color_info.value = (
                "Y = luminance, Cb = blue-difference chroma, Cr = red-difference chroma\n"
                f"Mean Y: {y_stats['mean']:.2f}    •    "
                f"Mean Cb: {cb_stats['mean']:.2f}    •    "
                f"Mean Cr: {cr_stats['mean']:.2f}"
            )
            self.color_info.update()
        except Exception as error:
            self._toast(f"YCbCr error: {error}", error=True)
        finally:
            self._set_busy(False)

    # =========================================================
    # MATPLOTLIB -> FLET IMAGE
    # =========================================================

    @staticmethod
    def _figure_to_png_bytes(fig):
        buffer = BytesIO()
        fig.savefig(
            buffer,
            format="png",
            dpi=130,
            bbox_inches="tight",
            facecolor=fig.get_facecolor(),
        )
        plt.close(fig)
        return buffer.getvalue()
import asyncio
import time
import os
from io import BytesIO

import flet as ft
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps

from algorithms.spatial.blur_sharpen import (
    blur_image,
    sharpen_image,
    apply_custom_kernel,
)
from algorithms.spatial.edge_detection import detect_edges
from algorithms.spatial.noise_cleaner import (
    add_gaussian_noise,
    add_salt_pepper_noise,
    clean_noise,
)
from algorithms.spatial.resize import resize_image
from algorithms.spatial.gaussian_separable import (
    gaussian_blur_2d,
    gaussian_blur_separable,
    compare_gaussian_results,
    compare_execution_time,
    theoretical_operations,
)
from algorithms.spatial.motion_blur import (
    create_motion_kernel,
    motion_blur_with_kernel,
)
from algorithms.spatial.wiener import (
    wiener_deconvolution,
    inverse_deconvolution,
    add_gaussian_noise as add_blur_noise,
)

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

from ui.theme import AppColors, configure_page
from ui.app_preferences import (
    AppProfile,
    PLAN_OPTIONS,
    WORKSPACE_OPTIONS,
    WORKSPACE_ROUTES,
    PreferencesStore,
)
from ui.components.top_bar import TopBar
from ui.components.sidebar import Sidebar, NAV_ITEMS, route_index
from ui.components.image_card import ImageCard
from ui.components.status_bar import StatusBar
from ui.components.loading_overlay import LoadingOverlay

from ui.views.blur_sharpen_view import BlurSharpenView
from ui.views.edge_view import EdgeView
from ui.views.noise_view import NoiseView
from ui.views.resize_view import ResizeView
from ui.views.gaussian_view import GaussianView
from ui.views.motion_view import MotionView
from ui.views.wiener_view import WienerView
from ui.views.home_view import HomeView
from ui.views.splash_view import SplashView
from ui.views.frequency_view import FrequencyView
from ui.views.compression_view import CompressionView
from ui.views.texture_view import TextureView
from ui.views.hybrid_view import HybridView
from ui.views.color_view import ColorView


class ImageProcessorApp:
    """Main UI controller. DSP stays inside algorithms/."""

    def __init__(self, page: ft.Page):
        self.page = page

        # -----------------------------------------------------
        # Persistent local display preferences
        # -----------------------------------------------------
        self.preferences_store = PreferencesStore()
        self.profile = self.preferences_store.load()

        # -----------------------------------------------------
        # Image state
        # -----------------------------------------------------
        self.original_image = None
        self.processed_image = None
        self.processed_bytes = None
        self.current_image_name = None

        # -----------------------------------------------------
        # Frequency state
        # -----------------------------------------------------
        self.current_dft = None
        self.current_dft_source = None
        self.current_compressed_dft = None

        # -----------------------------------------------------
        # Spatial state
        # -----------------------------------------------------
        self.noisy_image = None
        self.noisy_label = None
        self.motion_kernel = None
        self.motion_blurred = None
        self.motion_params = None

        # -----------------------------------------------------
        # Texture state
        # -----------------------------------------------------
        self.texture_results = {}

        # -----------------------------------------------------
        # Hybrid state
        # -----------------------------------------------------
        self.hybrid_low_image = None
        self.hybrid_high_image = None
        self.hybrid_low_name = None
        self.hybrid_high_name = None
        self.hybrid_low_preview_bytes = None
        self.hybrid_high_preview_bytes = None

        # -----------------------------------------------------
        # Navigation state
        # -----------------------------------------------------
        self.current_feature_index = 0

        configure_page(self.page)
        self._build_ui()

    # =========================================================
    # UI BUILD
    # =========================================================

    def _build_ui(self):
        self.status_bar = StatusBar()
        self.loading_overlay = LoadingOverlay()
        self.splash_view = SplashView()

        self.sidebar = Sidebar(
            on_navigation_change=self._on_sidebar_navigation,
            profile=self.profile,
            on_edit_profile=self.show_settings_dialog,
            on_show_about=self.show_about_dialog,
        )

        # Approved layout: sidebar remains visible on Home too.
        self.sidebar.control.visible = True

        self.top_bar = TopBar(
            on_open_image=self.open_image,
            on_save_result=self.save_processed,
            on_reset_result=self.reset_processed,
        )

        # Home has its own compact dashboard header.
        self.top_bar.control.visible = False

        self.original_card = ImageCard(
            title="Original Image",
            subtitle="No image selected",
            accent=AppColors.BLUE,
            placeholder_icon=ft.Icons.IMAGE_OUTLINED,
            placeholder_title="Open an image to begin",
            placeholder_subtitle="JPG • PNG • BMP • TIFF • WebP",
        )

        self.processed_card = ImageCard(
            title="Processed Result",
            subtitle="Live preview",
            accent=AppColors.PURPLE,
            placeholder_icon=ft.Icons.AUTO_FIX_HIGH_OUTLINED,
            placeholder_title="Processed output appears here",
            placeholder_subtitle="Choose a feature from the sidebar",
        )

        self.image_workspace = ft.ResponsiveRow(
            spacing=16,
            run_spacing=16,
            controls=[
                ft.Container(
                    col={"xs": 12, "md": 6},
                    content=self.original_card.control,
                ),
                ft.Container(
                    col={"xs": 12, "md": 6},
                    content=self.processed_card.control,
                ),
            ],
        )

        # -----------------------------
        # Views
        # -----------------------------

        self.home_view = HomeView(
            on_start_session=self.start_new_session,
            on_open_image=self.open_image,
            on_navigate=self._navigate_to,
            profile=self.profile,
            on_workspace_change=self.change_workspace,
        )

        self.frequency_view = FrequencyView(
            on_show_spectrum=self.show_frequency_spectrum,
            on_reconstruct=self.reconstruct_dft,
            on_low_pass=self.apply_low_pass,
            on_high_pass=self.apply_high_pass,
        )

        self.compression_view = CompressionView(
            on_apply_compression=self.apply_dft_compression,
            on_quality_curve=self.plot_compression_quality,
        )

        self.texture_view = TextureView(
            on_analyze=self.analyze_current_texture,
            on_show_comparisons=self.show_texture_comparison,
        )

        self.hybrid_view = HybridView(
            on_select_low=self.select_hybrid_low_image,
            on_select_high=self.select_hybrid_high_image,
            on_create_hybrid=self.generate_hybrid_image,
        )

        self.color_view = ColorView(
            on_red_channel=lambda e: self.show_rgb_channel("R"),
            on_green_channel=lambda e: self.show_rgb_channel("G"),
            on_blue_channel=lambda e: self.show_rgb_channel("B"),
            on_histograms=self.show_rgb_histograms,
            on_frequencies=self.show_rgb_frequency_spectra,
            on_ycbcr=self.show_ycbcr_channels,
        )

        # -----------------------------
        # Spatial pages
        # -----------------------------
        # The algorithms are implemented and verified on the Dola branch;
        # only the controls are missing. Each placeholder is swapped for
        # a real view without touching routing.

        self.spatial_views = self._build_spatial_views()

        # -----------------------------
        # Route table
        # -----------------------------
        # Keyed by sidebar route key, then flattened in NAV_ITEMS order.
        # Nothing here depends on a hardcoded index.

        self.views_by_key = {
            "home": self.home_view.control,
            "frequency": self.frequency_view.control,
            "compression": self.compression_view.control,
            "texture": self.texture_view.control,
            "hybrid": self.hybrid_view.control,
            "color": self.color_view.control,
        }

        for key, view in self.spatial_views.items():
            self.views_by_key[key] = view.control

        self.feature_views = [
            self.views_by_key[item["key"]] for item in NAV_ITEMS
        ]

        # Home starts without the processing image cards.
        self.page_content = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                self.home_view.control,
                ft.Container(height=10),
            ],
        )

        body = ft.Row(
            expand=True,
            spacing=0,
            controls=[
                self.sidebar.control,
                ft.Container(
                    expand=True,
                    padding=ft.Padding.all(20),
                    content=self.page_content,
                ),
            ],
        )

        app_shell = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                self.top_bar.control,
                body,
                self.status_bar.control,
            ],
        )

        self.root = ft.Stack(
            expand=True,
            controls=[
                app_shell,
                self.loading_overlay.control,
                self.splash_view.control,
            ],
        )

        self.page.add(self.root)

        # Start in Home mode.
        self.top_bar.set_home_mode(True)
        self.status_bar.control.visible = False

        # Run the branded launch screen first. Home's continuous
        # animations begin only after the splash has faded away.
        self.page.run_task(self._run_launch_sequence)

    # =========================================================
    # SPATIAL VIEWS
    # =========================================================

    def _build_spatial_views(self):
        """Construct the seven spatial pages, keyed by sidebar route."""

        self.blur_sharpen_view = BlurSharpenView(
            on_apply=self.apply_blur_sharpen,
        )

        self.edge_view = EdgeView(
            on_detect=self.detect_image_edges,
            on_compare=self.compare_edge_modes,
        )

        self.noise_view = NoiseView(
            on_add_noise=self.add_image_noise,
            on_clean=self.clean_image_noise,
            on_compare=self.compare_noise_filters,
        )

        self.resize_view = ResizeView(
            on_resize=self.resize_current_image,
            on_compare=self.compare_resize_methods,
        )

        self.gaussian_view = GaussianView(
            on_separable=self.apply_separable_blur,
            on_full_2d=self.apply_full_2d_blur,
            on_benchmark=self.benchmark_separability,
        )

        self.motion_view = MotionView(
            on_apply=self.apply_motion_blur,
            on_show_kernel=self.show_motion_kernel,
        )

        self.wiener_view = WienerView(
            on_restore=self.restore_with_wiener,
            on_compare=self.compare_restoration_methods,
            on_sweep=self.sweep_wiener_k,
        )

        return {
            "blur_sharpen": self.blur_sharpen_view,
            "edges": self.edge_view,
            "noise": self.noise_view,
            "resize": self.resize_view,
            "gaussian": self.gaussian_view,
            "motion": self.motion_view,
            "wiener": self.wiener_view,
        }

    # ROUTE HELPER
    # =========================================================

    @staticmethod
    def route(key):
        """Resolve a sidebar route key to its navigation index."""
        return route_index(key)

    async def _run_launch_sequence(self):
        """Play the splash screen, then start Home's background animations."""
        try:
            await self.splash_view.play()
        finally:
            # Even if the splash exits early for any reason, the main Home
            # animation should still be allowed to start.
            self.page.run_task(self.home_view.start_orbit_animation)

    # =========================================================
    # NAVIGATION
    # =========================================================

    def _on_sidebar_navigation(self, index):
        self._show_feature(index)

    def _navigate_to(self, index):
        self.sidebar.set_selected_index(index)
        self._show_feature(index)

    def change_workspace(self, workspace):
        """Persist the startup-page choice and open it once."""
        route_key = WORKSPACE_ROUTES.get(workspace)
        if route_key is None:
            return

        route = self.route(route_key)

        self.profile.workspace = workspace

        try:
            self.preferences_store.save(self.profile)
        except OSError as error:
            self._toast(
                f"Could not save workspace preference: {error}",
                error=True,
            )
            return

        self.home_view.set_profile(
            self.profile,
            refresh=self.current_feature_index == 0,
        )
        self.sidebar.set_profile(self.profile, refresh=True)
        self._navigate_to(route)
        self._toast(f"Workspace changed to {workspace}")

    # =========================================================
    # SETTINGS / ABOUT
    # =========================================================

    def show_settings_dialog(self, e=None):
        """Open functional settings and persist the selected preferences."""
        name_field = ft.TextField(
            label="Display name",
            value=self.profile.name,
            autofocus=True,
            max_length=40,
            prefix_icon=ft.Icons.PERSON_OUTLINE,
        )

        plan_field = ft.Dropdown(
            label="Plan",
            value=self.profile.plan,
            width=360,
            leading_icon=ft.Icons.STARS_OUTLINED,
            options=[
                ft.DropdownOption(key=plan, text=plan)
                for plan in PLAN_OPTIONS
            ],
        )

        workspace_field = ft.Dropdown(
            label="Default workspace",
            value=self.profile.workspace,
            width=360,
            leading_icon=ft.Icons.WORKSPACES_OUTLINE,
            options=[
                ft.DropdownOption(key=workspace, text=workspace)
                for workspace in WORKSPACE_OPTIONS
            ],
        )

        def close_dialog(event=None):
            self.page.pop_dialog()

        def save_settings(event=None):
            name = " ".join((name_field.value or "").split())

            if not name:
                name_field.error_text = "Enter a display name"
                name_field.update()
                return

            updated = AppProfile(
                name=name[:40],
                plan=(
                    plan_field.value
                    if plan_field.value in PLAN_OPTIONS
                    else PLAN_OPTIONS[0]
                ),
                workspace=(
                    workspace_field.value
                    if workspace_field.value in WORKSPACE_OPTIONS
                    else "Default"
                ),
            )

            try:
                self.preferences_store.save(updated)
            except OSError as error:
                self._toast(
                    f"Could not save settings: {error}",
                    error=True,
                )
                return

            self.profile = updated

            self.home_view.set_profile(
                self.profile,
                refresh=self.current_feature_index == 0,
            )
            self.sidebar.set_profile(self.profile, refresh=True)

            close_dialog()

            # Make the chosen startup page active immediately.
            route = self.route(
                WORKSPACE_ROUTES.get(self.profile.workspace, "home")
            )
            if route != self.current_feature_index:
                self._navigate_to(route)

            self._toast("Settings saved")

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(
                            ft.Icons.SETTINGS_OUTLINED,
                            color=AppColors.CYAN,
                        ),
                        ft.Text(
                            "Settings",
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
                content=ft.Container(
                    width=400,
                    content=ft.Column(
                        tight=True,
                        spacing=14,
                        controls=[
                            ft.Text(
                                "Personalize Signal Studio. These preferences "
                                "are saved locally on this device.",
                                size=11,
                                color=AppColors.TEXT_SECONDARY,
                            ),
                            name_field,
                            plan_field,
                            workspace_field,
                        ],
                    ),
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=close_dialog),
                    ft.Button(
                        content="Save changes",
                        icon=ft.Icons.CHECK,
                        on_click=save_settings,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    # Backward compatibility if another component still calls the old name.
    def show_profile_dialog(self, e=None):
        self.show_settings_dialog(e)

    def show_about_dialog(self, e=None):
        def close_dialog(event=None):
            self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(
                            ft.Icons.INFO_OUTLINE,
                            color=AppColors.PURPLE_LIGHT,
                        ),
                        ft.Text(
                            "About Signal Studio",
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                ),
                content=ft.Container(
                    width=440,
                    content=ft.Column(
                        tight=True,
                        spacing=12,
                        controls=[
                            ft.Text(
                                "AETHERIS",
                                size=17,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),
                            
                            ft.Divider(color=AppColors.BORDER_SOFT),
                            ft.Text(
                                "A desktop image-processing workspace that "
                                "demonstrates spatial-domain convolution and "
                                "frequency-domain 2D DFT processing through "
                                "interactive visual tools.",
                                size=11,
                                color=AppColors.TEXT_SECONDARY,
                            ),
                            ft.Row(
                                spacing=8,
                                wrap=True,
                                controls=[
                                    ft.Chip(label=ft.Text("12 DSP Features")),
                                    ft.Chip(label=ft.Text("Spatial Domain")),
                                    ft.Chip(label=ft.Text("Frequency Domain")),
                                    ft.Chip(label=ft.Text("PSNR")),
                                    ft.Chip(label=ft.Text("Python + Flet")),
                                ],
                            ),
                            ft.Divider(color=AppColors.BORDER_SOFT),
                            ft.Text(
                                "Signal Studio • Version 1.0",
                                size=10,
                                color=AppColors.MUTED,
                            ),
                        ],
                    ),
                ),
                actions=[
                    ft.TextButton("Close", on_click=close_dialog),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _show_feature(self, index):
        if index < 0 or index >= len(self.feature_views):
            index = 0

        self.current_feature_index = index

        # The workspace preference is a startup choice, not a mirror of
        # the current page. Navigating no longer rewrites it, so the
        # sidebar is the single source of truth for where you are.

        feature_name = self.sidebar.get_feature_name(index)
        is_home = index == 0

        # Persistent navigation on every page.
        self.sidebar.control.visible = True

        if is_home:
            self.page_content.controls = [
                self.home_view.control,
                ft.Container(height=10),
            ]
        else:
            self.page_content.controls = [
                self.image_workspace,
                self.feature_views[index],
                ft.Container(height=10),
            ]

        self.top_bar.set_active_feature(feature_name)
        self.top_bar.set_home_mode(is_home)
        self.top_bar.control.visible = not is_home
        self.status_bar.control.visible = not is_home

        if is_home:
            self._set_status("Signal Studio ready")
        else:
            self._set_status(f"{feature_name} workspace")

        self.page.update()

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

    def _set_original_preview(self, image, name):
        image_bytes = self._pil_to_png_bytes(image)
        self.original_card.set_image_bytes(
            image_bytes,
            title="Original Image",
            subtitle=name,
        )

    def _set_processed_pil(self, image, title, status=None):
        self.processed_image = image.copy()
        self.processed_bytes = self._pil_to_png_bytes(image)
        self.processed_card.set_image_bytes(
            self.processed_bytes,
            title=title,
            subtitle=status if status else "Processing complete",
        )
        self._add_processed_result_to_home(self.processed_bytes, title)

        if status:
            self._set_status(status)

    def _set_processed_bytes(self, image_bytes, title, status=None):
        self.processed_image = None
        self.processed_bytes = image_bytes
        self.processed_card.set_image_bytes(
            image_bytes,
            title=title,
            subtitle=status if status else "Processing complete",
        )
        self._add_processed_result_to_home(image_bytes, title)

        if status:
            self._set_status(status)

    def _add_processed_result_to_home(self, image_bytes, title):
        """Snapshot the actual output as a lightweight Recent Projects card."""
        try:
            with Image.open(BytesIO(image_bytes)) as decoded:
                width, height = decoded.size
                output_format = (decoded.format or "PNG").upper()

                preview = decoded.convert("RGB")
                preview.thumbnail((960, 560), Image.Resampling.LANCZOS)

                buffer = BytesIO()
                preview.save(
                    buffer,
                    format="JPEG",
                    quality=86,
                    optimize=True,
                )
                preview_bytes = buffer.getvalue()

            self.home_view.add_processed_result(
                image_bytes=preview_bytes,
                title=title,
                source_name=self.current_image_name,
                resolution=f"{width} × {height}",
                fmt=output_format,
                refresh=self.current_feature_index == 0,
            )
        except Exception:
            # Home preview failure must never break image processing.
            pass

    def _require_image(self):
        if self.original_image is None:
            self._toast("Open an image first.", error=True)
            return False
        return True

    # =========================================================
    # STATUS / LOADING
    # =========================================================

    def _set_status(self, text):
        self.status_bar.set_status(text)

    def _set_busy(self, busy, text=None):
        self.status_bar.set_busy(busy, text)

        if not busy:
            self.loading_overlay.hide_immediately()
            return

        message = text or "Processing image..."
        lower = message.lower()

        if "manual 2d dft" in lower or "computing 2d dft" in lower:
            self.loading_overlay.show_dft()
        elif "compress" in lower or "quality curve" in lower:
            self.loading_overlay.show_compression()
        elif "texture" in lower:
            self.loading_overlay.show_texture()
        elif "hybrid" in lower:
            self.loading_overlay.show_hybrid()
        elif "three channel dft" in lower or "rgb frequenc" in lower:
            self.loading_overlay.show_color_frequency()
        else:
            self.loading_overlay.show(
                title=self._processing_title(message),
                subtitle=message,
                detail="Signal-processing operation in progress",
                accent=AppColors.CYAN,
            )

    @staticmethod
    def _processing_title(text):
        cleaned = text.strip().replace("…", "").replace("...", "")
        return cleaned if len(cleaned) <= 38 else "Processing Image"

    def _toast(self, text, error=False):
        icon = (
            ft.Icons.ERROR_OUTLINE
            if error
            else ft.Icons.CHECK_CIRCLE_OUTLINE
        )
        color = AppColors.RED if error else AppColors.GREEN

        if error:
            self.status_bar.show_error(text)

        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(icon, color=color),
                        ft.Text(text, color=AppColors.TEXT),
                    ],
                ),
                show_close_icon=True,
            )
        )

    # =========================================================
    # RESET HIDDEN VIEW STATE SAFELY
    # =========================================================

    def _reset_analysis_display_state(self):
        # These views may currently be detached from page.
        self.compression_view.metric_total_value.value = "—"
        self.compression_view.metric_kept_value.value = "—"
        self.compression_view.metric_reduction_value.value = "—"
        self.compression_view.metric_psnr_value.value = "—"

        self.texture_view.current_result = None
        self.texture_view.current_name = None
        self.texture_view.analysis_image_name.value = "No texture analyzed"
        self.texture_view.analysis_status.value = (
            "Open a repeating texture such as brick, cloth, tiles, "
            "woven fabric, grass or stripes."
        )
        self.texture_view.direction_text.value = "WAITING"
        self.texture_view.direction_text.color = AppColors.ORANGE
        self.texture_view.angle_text.value = "—°"
        self.texture_view.direction_icon.name = ft.Icons.EXPLORE_OUTLINED
        self.texture_view.direction_icon.color = AppColors.ORANGE
        self.texture_view.metric_direction_value.value = "—"
        self.texture_view.metric_spacing_value.value = "—"
        self.texture_view.metric_frequency_value.value = "—"
        self.texture_view.metric_strength_value.value = "—"

        self.color_view.active_channel = None
        self.color_view.channel_statistics = {
            "R": None,
            "G": None,
            "B": None,
        }

        for control in [
            self.color_view.red_mean,
            self.color_view.red_std,
            self.color_view.red_min,
            self.color_view.red_max,
            self.color_view.green_mean,
            self.color_view.green_std,
            self.color_view.green_min,
            self.color_view.green_max,
            self.color_view.blue_mean,
            self.color_view.blue_std,
            self.color_view.blue_min,
            self.color_view.blue_max,
        ]:
            control.value = "—"

        self.color_view.mode_icon.name = ft.Icons.INFO_OUTLINE
        self.color_view.mode_icon.color = AppColors.PURPLE_LIGHT
        self.color_view.mode_title.value = "Color Analysis Ready"
        self.color_view.mode_title.color = AppColors.PURPLE_LIGHT
        self.color_view.mode_description.value = (
            "Choose a channel or analysis mode. Results will appear "
            "in the processed-image workspace."
        )

    def _reset_processed_card_silently(self):
        self.processed_card.title_text.value = "Processed Result"
        self.processed_card.subtitle_text.value = "Live preview"
        self.processed_card.placeholder_title = (
            "Processed output appears here"
        )
        self.processed_card.placeholder_subtitle = (
            "Choose a feature from the sidebar"
        )
        self.processed_card.switcher.content = (
            self.processed_card._create_placeholder()
        )

    # =========================================================
    # GENERAL ACTIONS
    # =========================================================

    async def start_new_session(self, e):
        await self.open_image(e)

    async def open_image(self, e):
        try:
            image, name = await self._pick_pil_image("Open an image")
            if image is None:
                return False

            self.original_image = image
            self.current_image_name = name
            self.current_dft = None
            self.current_dft_source = None
            self.current_compressed_dft = None

            # Update Home while mounted, then open the saved startup
            # page. Falls back to the first spatial feature so opening an
            # image never leaves the user on a page with nothing to do.
            if self.current_feature_index == 0:
                self.home_view.set_session_name(name, refresh=True)

                startup_key = WORKSPACE_ROUTES.get(
                    self.profile.workspace,
                    "home",
                )

                if startup_key == "home":
                    startup_key = "blur_sharpen"

                self._navigate_to(self.route(startup_key))
            else:
                self.home_view.set_session_name(name, refresh=False)

            self._set_original_preview(image, name)
            self.reset_processed(None)
            self._reset_analysis_display_state()

            self._set_status(f"Loaded {name}")
            self._toast(f"Loaded {name}")
            return True

        except Exception as error:
            self._toast(f"Could not open image: {error}", error=True)
            return False

    async def save_processed(self, e):
        if not self.processed_bytes:
            self._toast(
                "There is no processed result to save.",
                error=True,
            )
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
                self._toast(
                    f"Saved result: {os.path.basename(path)}"
                )
                self._set_status(
                    f"Saved processed result to {path}"
                )

        except Exception as error:
            self._toast(
                f"Could not save result: {error}",
                error=True,
            )

    def reset_processed(self, e):
        self.processed_image = None
        self.processed_bytes = None

        if self.current_feature_index == 0:
            self._reset_processed_card_silently()
        else:
            self.processed_card.reset(
                title="Processed Result",
                subtitle="Live preview",
                placeholder_title="Processed output appears here",
                placeholder_subtitle="Choose a feature from the sidebar",
            )

        self._set_status("Result cleared")

    def convert_to_grayscale(self, e):
        if not self._require_image():
            return

        grayscale = ImageOps.grayscale(
            self.original_image
        ).convert("RGB")

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
            source, dft = await asyncio.to_thread(
                self._compute_dft_sync
            )
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
    # SPATIAL HELPERS
    # =========================================================

    def _image_array(self):
        """Current original image as a uint8 RGB array."""
        return np.array(self.original_image.convert("RGB"), dtype=np.uint8)

    @staticmethod
    def _to_pil(array):
        """Wrap an algorithm result as a displayable RGB image.

        Edge detection returns a single-channel gradient, so 2D arrays
        are widened to three channels rather than failing.
        """
        array = np.asarray(array)

        if array.ndim == 2:
            array = np.stack([array] * 3, axis=-1)

        return Image.fromarray(
            np.clip(array, 0, 255).astype(np.uint8)
        ).convert("RGB")

    async def _run(self, function, *args, **kwargs):
        """Run a blocking algorithm off the UI thread, returning elapsed."""
        start = time.perf_counter()
        result = await asyncio.to_thread(function, *args, **kwargs)
        return result, time.perf_counter() - start

    @staticmethod
    def _seconds(value):
        if value < 1:
            return f"{value * 1000:.0f} ms"
        return f"{value:.2f} s"

    @staticmethod
    def _psnr_text(value):
        if value == float("inf"):
            return "identical"
        return f"{value:.2f} dB"

    def _panel_figure(self, panels, title):
        """Comparison grid: panels is a list of (array, caption)."""
        columns = len(panels)
        fig, axes = plt.subplots(
            1,
            columns,
            figsize=(4.0 * columns, 4.4),
        )
        fig.patch.set_facecolor("#0A0F19")

        if columns == 1:
            axes = [axes]

        for axis, (array, caption) in zip(axes, panels):
            array = np.asarray(array)
            if array.ndim == 2:
                axis.imshow(array, cmap="gray", vmin=0, vmax=255)
            else:
                axis.imshow(np.clip(array, 0, 255).astype(np.uint8))
            axis.set_title(caption, color="#F8FAFC", fontsize=10)
            axis.axis("off")

        fig.suptitle(title, color="#22D3EE", fontsize=12, y=1.04)
        fig.tight_layout()
        return self._figure_to_png_bytes(fig)

    # =========================================================
    # FEATURE 1 — BLUR & SHARPEN
    # =========================================================

    async def apply_blur_sharpen(self, e):
        if not self._require_image():
            return

        view = self.blur_sharpen_view
        mode = view.get_mode()
        source = self._image_array()

        if mode == "custom":
            try:
                kernel = np.array(view.get_custom_kernel(), dtype=np.float64)
            except ValueError as error:
                view.show_kernel_error(str(error))
                self._toast(str(error), error=True)
                return
            view.show_kernel_error(None)

        self._set_busy(True, "Applying convolution kernel…")

        try:
            if mode == "blur":
                size = view.get_kernel_size()
                result, elapsed = await self._run(blur_image, source, size)
                label = f"Box blur {size}×{size}"
                kernel_text = f"{size}×{size} box"

            elif mode == "sharpen":
                result, elapsed = await self._run(sharpen_image, source)
                label = "Sharpen"
                kernel_text = "3×3 sharpen"

            else:
                result, elapsed = await self._run(
                    apply_custom_kernel,
                    source,
                    kernel,
                )
                label = "Custom kernel"
                kernel_text = (
                    "3×3 custom"
                    + (" (normalised)" if view.kernel_grid.is_normalised() else "")
                )

            psnr = calculate_psnr(source, np.asarray(result))

            self._set_processed_pil(
                self._to_pil(result),
                label,
                f"{label} applied in {self._seconds(elapsed)}.",
            )

            view.metrics.set_values(
                {
                    "operation": label,
                    "kernel": kernel_text,
                    "psnr": self._psnr_text(psnr),
                    "elapsed": self._seconds(elapsed),
                },
                note="Lower PSNR simply means the result differs more "
                     "from the original — expected for a strong blur.",
            )

        except Exception as error:
            self._toast(f"Convolution error: {error}", error=True)

        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 2 — EDGE DETECTOR
    # =========================================================

    async def detect_image_edges(self, e):
        if not self._require_image():
            return

        mode = self.edge_view.get_mode()
        source = self._image_array()

        self._set_busy(True, f"Running Sobel {mode} edge detection…")

        try:
            edges, elapsed = await self._run(detect_edges, source, mode)
            edges = np.asarray(edges)

            self._set_processed_pil(
                self._to_pil(edges),
                f"Edges • {mode.title()}",
                f"Sobel {mode} detection in {self._seconds(elapsed)}.",
            )

            self.edge_view.metrics.set_values(
                {
                    "mode": mode.title(),
                    "max": f"{edges.max():.0f}",
                    "mean": f"{edges.mean():.1f}",
                    "elapsed": self._seconds(elapsed),
                },
                note="Gradient magnitude is single-channel, so the result "
                     "is displayed in grayscale.",
            )

        except Exception as error:
            self._toast(f"Edge detection error: {error}", error=True)

        finally:
            self._set_busy(False)

    async def compare_edge_modes(self, e):
        if not self._require_image():
            return

        source = self._image_array()
        self._set_busy(True, "Running all three Sobel modes…")

        try:
            panels = [(source, "Original")]

            for mode in ("horizontal", "vertical", "combined"):
                edges, _ = await self._run(detect_edges, source, mode)
                panels.append((np.asarray(edges), mode.title()))

            image_bytes = await asyncio.to_thread(
                self._panel_figure,
                panels,
                "Sobel edge detection modes",
            )

            self._set_processed_bytes(
                image_bytes,
                "Edge Mode Comparison",
                "Horizontal, vertical and combined edges.",
            )

        except Exception as error:
            self._toast(f"Comparison error: {error}", error=True)

        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 3 — NOISE CLEANER
    # =========================================================

    async def add_image_noise(self, e):
        if not self._require_image():
            return

        view = self.noise_view
        noise_type = view.get_noise_type()
        source = self._image_array()

        self._set_busy(True, "Adding noise…")

        try:
            if noise_type == "gaussian":
                sigma = view.get_sigma()
                noisy, elapsed = await self._run(
                    add_gaussian_noise,
                    source,
                    0.0,
                    sigma,
                )
                label = f"Gaussian noise σ={sigma:.0f}"
            else:
                density = view.get_density()
                noisy, elapsed = await self._run(
                    add_salt_pepper_noise,
                    source,
                    density,
                )
                label = f"Salt & pepper {density * 100:.0f}%"

            self.noisy_image = np.asarray(noisy)
            self.noisy_label = label

            psnr = calculate_psnr(source, self.noisy_image)

            self._set_processed_pil(
                self._to_pil(self.noisy_image),
                label,
                f"{label} added. Now clean it.",
            )

            view.metrics.set_values(
                {
                    "noise": label,
                    "noisy_psnr": self._psnr_text(psnr),
                    "cleaned_psnr": "—",
                    "gain": "—",
                },
                note="Noisy image stored. Pick a filter and clean it.",
            )

        except Exception as error:
            self._toast(f"Noise error: {error}", error=True)

        finally:
            self._set_busy(False)

    async def clean_image_noise(self, e):
        if not self._require_image():
            return

        if self.noisy_image is None:
            self._toast("Add noise first, then clean it.", error=True)
            return

        view = self.noise_view
        method = view.get_filter()
        size = view.get_filter_size()
        source = self._image_array()

        self._set_busy(True, f"Applying {method} filter…")

        try:
            cleaned, elapsed = await self._run(
                clean_noise,
                self.noisy_image,
                method,
                size,
            )
            cleaned = np.asarray(cleaned)

            noisy_psnr = calculate_psnr(source, self.noisy_image)
            cleaned_psnr = calculate_psnr(source, cleaned)
            gain = cleaned_psnr - noisy_psnr

            self._set_processed_pil(
                self._to_pil(cleaned),
                f"{method.title()} filter {size}×{size}",
                f"Cleaned in {self._seconds(elapsed)}.",
            )

            view.metrics.set_values(
                {
                    "noise": self.noisy_label or "—",
                    "noisy_psnr": self._psnr_text(noisy_psnr),
                    "cleaned_psnr": self._psnr_text(cleaned_psnr),
                    "gain": f"{gain:+.2f} dB",
                },
                note="A positive gain means the filter recovered more than "
                     "it destroyed.",
            )

        except Exception as error:
            self._toast(f"Filter error: {error}", error=True)

        finally:
            self._set_busy(False)

    async def compare_noise_filters(self, e):
        if not self._require_image():
            return

        if self.noisy_image is None:
            self._toast("Add noise first, then compare.", error=True)
            return

        source = self._image_array()
        size = self.noise_view.get_filter_size()

        self._set_busy(True, "Running mean, Gaussian and median filters…")

        try:
            noisy_psnr = calculate_psnr(source, self.noisy_image)
            panels = [
                (source, "Original"),
                (
                    self.noisy_image,
                    f"Noisy\n{self._psnr_text(noisy_psnr)}",
                ),
            ]

            best_name, best_psnr = None, -1.0

            for method in ("mean", "gaussian", "median"):
                cleaned, _ = await self._run(
                    clean_noise,
                    self.noisy_image,
                    method,
                    size,
                )
                cleaned = np.asarray(cleaned)
                psnr = calculate_psnr(source, cleaned)

                if psnr > best_psnr:
                    best_name, best_psnr = method, psnr

                panels.append(
                    (cleaned, f"{method.title()}\n{self._psnr_text(psnr)}")
                )

            image_bytes = await asyncio.to_thread(
                self._panel_figure,
                panels,
                f"Noise filter comparison • {size}×{size} kernel",
            )

            self._set_processed_bytes(
                image_bytes,
                "Filter Comparison",
                f"Best result: {best_name} at {self._psnr_text(best_psnr)}.",
            )

            self.noise_view.metrics.set_values(
                {
                    "noise": self.noisy_label or "—",
                    "noisy_psnr": self._psnr_text(noisy_psnr),
                    "cleaned_psnr": self._psnr_text(best_psnr),
                    "gain": f"{best_psnr - noisy_psnr:+.2f} dB",
                },
                note=f"Best filter for this noise: {best_name}.",
            )

        except Exception as error:
            self._toast(f"Comparison error: {error}", error=True)

        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 6 — IMAGE RESIZER
    # =========================================================

    def _target_size(self, scale):
        height, width = self._image_array().shape[:2]
        return (
            max(1, int(round(width * scale))),
            max(1, int(round(height * scale))),
        )

    async def resize_current_image(self, e):
        if not self._require_image():
            return

        view = self.resize_view
        method = view.get_method()
        scale = view.get_scale()
        antialias = view.get_antialias() and scale < 1.0

        source = self._image_array()
        new_width, new_height = self._target_size(scale)

        self._set_busy(True, f"Resizing to {new_width}×{new_height}…")

        try:
            result, elapsed = await self._run(
                resize_image,
                source,
                new_width,
                new_height,
                method,
                antialias,
            )

            self._set_processed_pil(
                self._to_pil(result),
                f"{method.title()} • {new_width}×{new_height}",
                f"Resized in {self._seconds(elapsed)}.",
            )

            view.metrics.set_values(
                {
                    "method": method.title(),
                    "size": f"{new_width} × {new_height}",
                    "antialias": "On" if antialias else "Off",
                    "elapsed": self._seconds(elapsed),
                },
                note="Anti-aliasing only applies when downsampling."
                     if scale >= 1.0
                     else "Pre-filtering removes detail the smaller grid "
                          "cannot represent.",
            )

        except Exception as error:
            self._toast(f"Resize error: {error}", error=True)

        finally:
            self._set_busy(False)

    async def compare_resize_methods(self, e):
        if not self._require_image():
            return

        scale = self.resize_view.get_scale()
        source = self._image_array()
        new_width, new_height = self._target_size(scale)

        self._set_busy(True, "Comparing resampling methods…")

        try:
            variants = [
                ("nearest", False, "Nearest"),
                ("bilinear", False, "Bilinear"),
                ("bilinear", True, "Bilinear + anti-alias"),
            ]

            panels = [(source, f"Original\n{source.shape[1]}×{source.shape[0]}")]

            for method, antialias, caption in variants:
                result, _ = await self._run(
                    resize_image,
                    source,
                    new_width,
                    new_height,
                    method,
                    antialias,
                )
                result = np.asarray(result)
                panels.append(
                    (result, f"{caption}\nstd {result.std():.1f}")
                )

            image_bytes = await asyncio.to_thread(
                self._panel_figure,
                panels,
                f"Resampling comparison • {new_width}×{new_height}",
            )

            self._set_processed_bytes(
                image_bytes,
                "Resampling Comparison",
                "Low std-dev after anti-aliasing means aliasing was "
                "suppressed, not that the image broke.",
            )

        except Exception as error:
            self._toast(f"Comparison error: {error}", error=True)

        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 10 — GAUSSIAN SEPARABILITY
    # =========================================================

    async def apply_separable_blur(self, e):
        await self._gaussian_blur(separable=True)

    async def apply_full_2d_blur(self, e):
        await self._gaussian_blur(separable=False)

    async def _gaussian_blur(self, separable):
        if not self._require_image():
            return

        view = self.gaussian_view
        size = view.get_kernel_size()
        sigma = view.get_sigma()
        source = self._image_array()

        function = gaussian_blur_separable if separable else gaussian_blur_2d
        label = "Separable" if separable else "Full 2D"

        self._set_busy(True, f"{label} Gaussian blur…")

        try:
            result, elapsed = await self._run(function, source, size, sigma)

            self._set_processed_pil(
                self._to_pil(result),
                f"{label} Gaussian • {size}×{size}, σ={sigma}",
                f"Completed in {self._seconds(elapsed)}.",
            )

            key = "sep_time" if separable else "full_time"
            view.metrics.set_values(
                {key: self._seconds(elapsed)},
                note="Run the benchmark to compare both paths fairly.",
            )

        except Exception as error:
            self._toast(f"Gaussian blur error: {error}", error=True)

        finally:
            self._set_busy(False)

    async def benchmark_separability(self, e):
        if not self._require_image():
            return

        view = self.gaussian_view
        size = view.get_kernel_size()
        sigma = view.get_sigma()
        source = self._image_array()

        pixels = source.shape[0] * source.shape[1]
        if pixels > 400_000:
            self._toast(
                "That image is large for a pure-Python benchmark. "
                "Use a 128×128 image for timing runs.",
                error=True,
            )

        self._set_busy(True, "Benchmarking separable vs full 2D…")

        try:
            timing, _ = await self._run(
                compare_execution_time,
                source,
                size,
                sigma,
                1,
            )
            equality, _ = await self._run(
                compare_gaussian_results,
                source,
                size,
                sigma,
            )
            theory = theoretical_operations(size)

            self._set_processed_pil(
                self._to_pil(equality["separable"]),
                f"Separable Gaussian • {size}×{size}",
                "Separable output shown; it matches the full 2D result.",
            )

            view.metrics.set_values(
                {
                    "full_time": self._seconds(timing["full_2d_time"]),
                    "sep_time": self._seconds(timing["separable_time"]),
                    "speedup": f"{timing['speedup']:.2f}×",
                    "theory": f"{theory['theoretical_speedup']:.2f}×",
                    "mae": f"{equality['mean_absolute_error']:.2e}",
                    "max_diff": f"{equality['max_difference']:.0f} level",
                },
                note=f"{theory['full_2d_operations_per_pixel']} vs "
                     f"{theory['separable_operations_per_pixel']} "
                     f"operations per pixel. Measured speed-up trails "
                     f"theory because Python loop overhead dominates.",
            )

        except Exception as error:
            self._toast(f"Benchmark error: {error}", error=True)

        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 7 — MOTION BLUR
    # =========================================================

    async def apply_motion_blur(self, e):
        if not self._require_image():
            return

        view = self.motion_view
        length = view.get_length()
        angle = view.get_angle()
        source = self._image_array()

        self._set_busy(True, f"Applying motion blur • {length}px at {angle}°…")

        try:
            result, elapsed = await self._run(
                motion_blur_with_kernel,
                source,
                length,
                angle,
            )

            self.motion_blurred = np.asarray(result["blurred"])
            self.motion_kernel = np.asarray(result["kernel"])
            self.motion_params = (length, angle)

            psnr = calculate_psnr(source, self.motion_blurred)

            self._set_processed_pil(
                self._to_pil(self.motion_blurred),
                f"Motion Blur • {length}px at {angle}°",
                f"Blurred in {self._seconds(elapsed)}.",
            )

            view.metrics.set_values(
                {
                    "kernel": f"{result['length']}×{result['length']}",
                    "angle": f"{angle}°",
                    "psnr": self._psnr_text(psnr),
                    "elapsed": self._seconds(elapsed),
                },
                note="The kernel is stored exactly, which is what makes "
                     "honest deconvolution possible.",
            )

            view.set_handoff(
                f"Kernel ready for Restoration "
                f"({result['length']}×{result['length']}, {angle}°).",
            )

        except Exception as error:
            self._toast(f"Motion blur error: {error}", error=True)

        finally:
            self._set_busy(False)

    async def show_motion_kernel(self, e):
        view = self.motion_view
        length = view.get_length()
        angle = view.get_angle()

        self._set_busy(True, "Building motion kernel…")

        try:
            kernel, _ = await self._run(create_motion_kernel, length, angle)
            kernel = np.asarray(kernel)

            display = kernel / kernel.max() * 255.0

            self._set_processed_bytes(
                await asyncio.to_thread(
                    self._panel_figure,
                    [(display, f"{kernel.shape[0]}×{kernel.shape[0]} PSF")],
                    f"Motion kernel • {length}px at {angle}°",
                ),
                "Motion Kernel",
                f"Kernel sums to {kernel.sum():.4f}, so brightness is "
                f"preserved.",
            )

        except Exception as error:
            self._toast(f"Kernel error: {error}", error=True)

        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 11 — WIENER DECONVOLUTION
    # =========================================================

    async def _degraded_pair(self, sigma):
        """Blurred image + its exact kernel, with optional added noise."""
        source = self._image_array()

        if self.motion_kernel is not None and self.motion_blurred is not None:
            blurred = self.motion_blurred
            kernel = self.motion_kernel
            origin = "kernel from Motion Blur Lab"
        else:
            result, _ = await self._run(
                motion_blur_with_kernel,
                source,
                15,
                0,
            )
            blurred = np.asarray(result["blurred"])
            kernel = np.asarray(result["kernel"])
            origin = "generated 15px kernel at 0°"

        if sigma > 0:
            blurred, _ = await self._run(add_blur_noise, blurred, sigma)
            blurred = np.asarray(blurred)
            origin += f", noise σ={sigma:.0f}"

        return source, blurred, kernel, origin

    async def restore_with_wiener(self, e):
        if not self._require_image():
            return

        view = self.wiener_view
        k = view.get_k()
        sigma = view.get_noise_sigma()

        self._set_busy(True, f"Wiener deconvolution • K={k}…")

        try:
            source, blurred, kernel, origin = await self._degraded_pair(sigma)

            restored, elapsed = await self._run(
                wiener_deconvolution,
                blurred,
                kernel,
                k,
            )
            restored = np.asarray(restored)

            blurred_psnr = calculate_psnr(source, blurred)
            wiener_psnr = calculate_psnr(source, restored)

            self._set_processed_pil(
                self._to_pil(restored),
                f"Wiener Restored • K={k}",
                f"Restored in {self._seconds(elapsed)}.",
            )

            view.metrics.set_values(
                {
                    "blurred": self._psnr_text(blurred_psnr),
                    "inverse": "—",
                    "wiener": self._psnr_text(wiener_psnr),
                    "gain": f"{wiener_psnr - blurred_psnr:+.2f} dB",
                    "k": str(k),
                },
                note=f"Using {origin}.",
            )

        except Exception as error:
            self._toast(f"Restoration error: {error}", error=True)

        finally:
            self._set_busy(False)

    async def compare_restoration_methods(self, e):
        if not self._require_image():
            return

        view = self.wiener_view
        k = view.get_k()
        sigma = view.get_noise_sigma()

        self._set_busy(True, "Comparing inverse filtering with Wiener…")

        try:
            source, blurred, kernel, origin = await self._degraded_pair(sigma)

            inverse, _ = await self._run(
                inverse_deconvolution,
                blurred,
                kernel,
            )
            wiener, _ = await self._run(
                wiener_deconvolution,
                blurred,
                kernel,
                k,
            )

            inverse = np.asarray(inverse)
            wiener = np.asarray(wiener)

            blurred_psnr = calculate_psnr(source, blurred)
            inverse_psnr = calculate_psnr(source, inverse)
            wiener_psnr = calculate_psnr(source, wiener)

            panels = [
                (source, "Original"),
                (blurred, f"Degraded\n{self._psnr_text(blurred_psnr)}"),
                (inverse, f"Inverse filter\n{self._psnr_text(inverse_psnr)}"),
                (wiener, f"Wiener K={k}\n{self._psnr_text(wiener_psnr)}"),
            ]

            image_bytes = await asyncio.to_thread(
                self._panel_figure,
                panels,
                "Inverse filtering vs Wiener deconvolution",
            )

            self._set_processed_bytes(
                image_bytes,
                "Restoration Comparison",
                f"Wiener leads inverse by "
                f"{wiener_psnr - inverse_psnr:+.2f} dB.",
            )

            view.metrics.set_values(
                {
                    "blurred": self._psnr_text(blurred_psnr),
                    "inverse": self._psnr_text(inverse_psnr),
                    "wiener": self._psnr_text(wiener_psnr),
                    "gain": f"{wiener_psnr - inverse_psnr:+.2f} dB",
                    "k": str(k),
                },
                note=f"Using {origin}. With no noise the inverse filter "
                     f"often wins — add noise to see it collapse.",
            )

        except Exception as error:
            self._toast(f"Comparison error: {error}", error=True)

        finally:
            self._set_busy(False)

    async def sweep_wiener_k(self, e):
        if not self._require_image():
            return

        view = self.wiener_view
        sigma = view.get_noise_sigma()
        ladder = view.k_ladder()

        self._set_busy(True, "Sweeping the K parameter…")

        try:
            source, blurred, kernel, origin = await self._degraded_pair(sigma)

            blurred_psnr = calculate_psnr(source, blurred)
            inverse, _ = await self._run(
                inverse_deconvolution,
                blurred,
                kernel,
            )
            inverse_psnr = calculate_psnr(source, np.asarray(inverse))

            scores = []
            for k in ladder:
                restored, _ = await self._run(
                    wiener_deconvolution,
                    blurred,
                    kernel,
                    k,
                )
                scores.append(calculate_psnr(source, np.asarray(restored)))

            best_index = int(np.argmax(scores))
            best_k = ladder[best_index]
            best_psnr = scores[best_index]

            image_bytes = await asyncio.to_thread(
                self._build_k_sweep_plot,
                ladder,
                scores,
                blurred_psnr,
                inverse_psnr,
                best_k,
                best_psnr,
            )

            self._set_processed_bytes(
                image_bytes,
                "Wiener K Sweep",
                f"Best K = {best_k} at {self._psnr_text(best_psnr)}.",
            )

            view.metrics.set_values(
                {
                    "blurred": self._psnr_text(blurred_psnr),
                    "inverse": self._psnr_text(inverse_psnr),
                    "wiener": self._psnr_text(best_psnr),
                    "gain": f"{best_psnr - inverse_psnr:+.2f} dB",
                    "k": f"{best_k} (best)",
                },
                note=f"Using {origin}. Optimal K rises with noise level.",
            )

        except Exception as error:
            self._toast(f"Sweep error: {error}", error=True)

        finally:
            self._set_busy(False)

    def _build_k_sweep_plot(
        self,
        ladder,
        scores,
        blurred_psnr,
        inverse_psnr,
        best_k,
        best_psnr,
    ):
        fig, ax = plt.subplots(figsize=(8.4, 4.6))
        fig.patch.set_facecolor("#0A0F19")
        ax.set_facecolor("#0A0F19")

        ax.plot(
            ladder,
            scores,
            marker="o",
            color="#A78BFA",
            label="Wiener",
        )
        ax.axhline(
            blurred_psnr,
            color="#8FA0B8",
            linestyle=":",
            label="Degraded input",
        )
        ax.axhline(
            inverse_psnr,
            color="#EF4444",
            linestyle="--",
            label="Inverse filter",
        )
        ax.scatter(
            [best_k],
            [best_psnr],
            s=90,
            color="#10B981",
            zorder=5,
            label=f"Best K = {best_k}",
        )

        ax.set_xscale("log")
        ax.set_xlabel("K (regularisation)", color="#CBD5E1")
        ax.set_ylabel("PSNR (dB)", color="#CBD5E1")
        ax.set_title(
            "Restoration quality against K",
            color="#22D3EE",
        )
        ax.tick_params(colors="#8FA0B8")
        ax.grid(True, alpha=0.15, color="#8FA0B8")

        legend = ax.legend(facecolor="#111827", edgecolor="#26344D")
        for text in legend.get_texts():
            text.set_color("#CBD5E1")

        for spine in ax.spines.values():
            spine.set_color("#26344D")

        fig.tight_layout()
        return self._figure_to_png_bytes(fig)

    # =========================================================
    # FEATURE 4 — FREQUENCY EDITOR
    # =========================================================

    async def show_frequency_spectrum(self, e):
        if not await self._ensure_dft():
            return

        self._set_busy(True, "Creating centered DFT spectrum…")

        try:
            spectrum = await asyncio.to_thread(
                create_spectrum_image,
                self.current_dft,
            )
            image = Image.fromarray(spectrum).convert("RGB")

            self._set_processed_pil(
                image,
                "2D DFT Frequency Spectrum",
                "Displaying centered log-magnitude DFT spectrum.",
            )

        except Exception as error:
            self._toast(f"Spectrum error: {error}", error=True)

        finally:
            self._set_busy(False)

    async def reconstruct_dft(self, e):
        if not await self._ensure_dft():
            return

        self._set_busy(
            True,
            "Reconstructing image with inverse 2D DFT…",
        )

        try:
            reconstructed = await asyncio.to_thread(
                reconstruct_from_dft,
                self.current_dft,
            )
            image = Image.fromarray(reconstructed).convert("RGB")

            self._set_processed_pil(
                image,
                "Reconstructed from DFT",
                "Inverse DFT reconstruction completed.",
            )

        except Exception as error:
            self._toast(
                f"Reconstruction error: {error}",
                error=True,
            )

        finally:
            self._set_busy(False)

    async def apply_low_pass(self, e):
        if not await self._ensure_dft():
            return

        radius = self.frequency_view.get_cutoff_radius()
        self._set_busy(True, "Applying low-pass frequency mask…")

        try:
            filtered = await asyncio.to_thread(
                apply_low_pass_filter,
                self.current_dft,
                radius,
            )
            reconstructed = await asyncio.to_thread(
                reconstruct_from_dft,
                filtered,
            )
            result_image = Image.fromarray(
                reconstructed
            ).convert("RGB")

            self._set_processed_pil(
                result_image,
                f"Low-Pass • Radius {radius}",
                f"Low-pass filter applied with radius {radius}.",
            )

        except Exception as error:
            self._toast(f"Low-pass error: {error}", error=True)

        finally:
            self._set_busy(False)

    async def apply_high_pass(self, e):
        if not await self._ensure_dft():
            return

        radius = self.frequency_view.get_cutoff_radius()
        self._set_busy(True, "Applying high-pass frequency mask…")

        try:
            filtered = await asyncio.to_thread(
                apply_high_pass_filter,
                self.current_dft,
                radius,
            )
            reconstructed = await asyncio.to_thread(
                reconstruct_from_dft,
                filtered,
            )
            result_image = Image.fromarray(
                reconstructed
            ).convert("RGB")

            self._set_processed_pil(
                result_image,
                f"High-Pass • Radius {radius}",
                f"High-pass filter applied with radius {radius}.",
            )

        except Exception as error:
            self._toast(f"High-pass error: {error}", error=True)

        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 5 — COMPRESSION
    # =========================================================

    async def apply_dft_compression(self, e):
        if not await self._ensure_dft():
            return

        percentage = self.compression_view.get_keep_percentage()
        self._set_busy(True, "Compressing DFT coefficients…")

        try:
            (
                compressed_frequency,
                _,
                kept_count,
                total_count,
            ) = await asyncio.to_thread(
                compress_dft,
                self.current_dft,
                percentage,
            )

            self.current_compressed_dft = compressed_frequency

            reconstructed = await asyncio.to_thread(
                reconstruct_from_dft,
                compressed_frequency,
            )

            original_for_psnr = np.clip(
                self.current_dft_source,
                0,
                255,
            ).astype(np.uint8)

            psnr = calculate_psnr(
                original_for_psnr,
                reconstructed,
            )
            removed_count = total_count - kept_count
            reduction = removed_count / total_count * 100.0
            psnr_text = (
                "∞"
                if np.isinf(psnr)
                else f"{psnr:.2f} dB"
            )

            self.compression_view.update_metrics(
                total=total_count,
                kept=kept_count,
                reduction=reduction,
                psnr=psnr_text,
            )

            self._set_processed_pil(
                Image.fromarray(reconstructed).convert("RGB"),
                f"DFT Compression • Keep {percentage}%",
                f"Compression complete — retained {percentage}% "
                "of coefficients.",
            )

        except Exception as error:
            self._toast(
                f"Compression error: {error}",
                error=True,
            )

        finally:
            self._set_busy(False)

    def _build_compression_curve_plot(self):
        percentages = [1, 2, 5, 10, 20, 40, 60, 80, 95]

        original = np.clip(
            self.current_dft_source,
            0,
            255,
        ).astype(np.uint8)

        psnr_values = []

        for percentage in percentages:
            compressed, _, _, _ = compress_dft(
                self.current_dft,
                percentage,
            )
            reconstructed = reconstruct_from_dft(compressed)
            psnr_values.append(
                calculate_psnr(original, reconstructed)
            )

        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        fig.patch.set_facecolor("#0A0F19")
        ax.set_facecolor("#0A0F19")
        ax.plot(
            percentages,
            psnr_values,
            marker="o",
            linewidth=2.2,
        )
        ax.fill_between(
            percentages,
            psnr_values,
            alpha=0.08,
        )
        ax.set_xlabel(
            "DFT coefficients kept (%)",
            color="#CBD5E1",
        )
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

        self._set_busy(
            True,
            "Building compression quality curve…",
        )

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
            self._toast(
                f"Could not create plot: {error}",
                error=True,
            )

        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 8 — TEXTURE
    # =========================================================

    async def analyze_current_texture(self, e):
        if not self._require_image():
            return

        self._set_busy(True, "Analyzing texture spectrum…")

        try:
            image_array = self._prepare_image_for_dft()
            result = await asyncio.to_thread(
                analyze_texture,
                image_array,
            )

            spectrum = Image.fromarray(
                result["spectrum"]
            ).convert("RGB")

            self._set_processed_pil(
                spectrum,
                "Texture Frequency Spectrum",
                f"Texture analysis completed for "
                f"{self.current_image_name}.",
            )

            key = (
                self.current_image_name
                or f"Texture {len(self.texture_results) + 1}"
            )

            self.texture_view.update_result(key, result)
            self.texture_results[key] = result
            self.texture_view.update_comparisons(
                self.texture_results
            )

        except Exception as error:
            self._toast(
                f"Texture analysis error: {error}",
                error=True,
            )

        finally:
            self._set_busy(False)

    def show_texture_comparison(self, e):
        if not self.texture_results:
            self._toast(
                "Analyze at least one texture first.",
                error=True,
            )
            return

        self.texture_view.update_comparisons(
            self.texture_results
        )
        self._set_status(
            f"Showing {len(self.texture_results)} saved "
            "texture result(s)."
        )

    # =========================================================
    # FEATURE 9 — HYBRID
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
            self.hybrid_low_preview_bytes = (
                self._pil_to_png_bytes(image)
            )

            self.hybrid_view.update_low_source(
                name,
                self.hybrid_low_preview_bytes,
            )

            self.original_image = image
            self.current_image_name = name
            self.current_dft = None
            self.current_dft_source = None
            self.current_compressed_dft = None

            self._set_original_preview(image, name)
            self.home_view.set_session_name(name, refresh=False)
            self._set_status(
                f"Hybrid low-frequency source: {name}"
            )

        except Exception as error:
            self._toast(
                f"Could not select Image A: {error}",
                error=True,
            )

    async def select_hybrid_high_image(self, e):
        try:
            image, name = await self._pick_pil_image(
                "Select high-frequency source image"
            )

            if image is None:
                return

            self.hybrid_high_image = image
            self.hybrid_high_name = name
            self.hybrid_high_preview_bytes = (
                self._pil_to_png_bytes(image)
            )

            self.hybrid_view.update_high_source(
                name,
                self.hybrid_high_preview_bytes,
            )

            self._set_status(
                f"Hybrid high-frequency source: {name}"
            )

        except Exception as error:
            self._toast(
                f"Could not select Image B: {error}",
                error=True,
            )

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
        if (
            self.hybrid_low_image is None
            or self.hybrid_high_image is None
        ):
            self._toast(
                "Select both hybrid source images first.",
                error=True,
            )
            return

        low_radius = self.hybrid_view.get_low_radius()
        high_radius = self.hybrid_view.get_high_radius()

        self._set_busy(
            True,
            "Creating hybrid image from two DFTs…",
        )

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

            self.hybrid_view.show_created_status()

        except Exception as error:
            self._toast(
                f"Hybrid image error: {error}",
                error=True,
            )

        finally:
            self._set_busy(False)

    # =========================================================
    # FEATURE 12 — COLOR
    # =========================================================

    def show_rgb_channel(self, channel_name):
        if not self._require_image():
            return

        try:
            image_array = np.array(
                self.original_image,
                dtype=np.uint8,
            )
            red, green, blue = split_rgb_channels(image_array)

            channel_map = {
                "R": red,
                "G": green,
                "B": blue,
            }
            name_map = {
                "R": "Red",
                "G": "Green",
                "B": "Blue",
            }

            channel = channel_map[channel_name]
            colored = create_colored_channel(
                channel,
                channel_name,
            )
            stats = get_channel_statistics(channel)

            self._set_processed_pil(
                Image.fromarray(colored),
                f"{name_map[channel_name]} Channel",
                f"Displaying the "
                f"{name_map[channel_name].lower()} channel.",
            )

            self.color_view.update_channel_statistics(
                channel_name,
                stats,
            )

        except Exception as error:
            self._toast(
                f"Color analysis error: {error}",
                error=True,
            )

    def _build_rgb_histogram_plot(self):
        image_array = np.array(
            self.original_image,
            dtype=np.uint8,
        )
        red, green, blue = split_rgb_channels(image_array)

        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        fig.patch.set_facecolor("#0A0F19")
        ax.set_facecolor("#0A0F19")

        ax.hist(
            red.flatten(),
            bins=256,
            range=(0, 255),
            alpha=0.45,
            label="Red",
            color="#EF4444",
        )
        ax.hist(
            green.flatten(),
            bins=256,
            range=(0, 255),
            alpha=0.45,
            label="Green",
            color="#10B981",
        )
        ax.hist(
            blue.flatten(),
            bins=256,
            range=(0, 255),
            alpha=0.45,
            label="Blue",
            color="#3B82F6",
        )

        ax.set_xlabel("Intensity", color="#CBD5E1")
        ax.set_ylabel("Pixel count", color="#CBD5E1")
        ax.set_title(
            "RGB Channel Histogram Comparison",
            color="#F8FAFC",
            weight="bold",
        )
        ax.tick_params(colors="#94A3B8")
        ax.grid(alpha=0.12)
        ax.legend(
            facecolor="#111827",
            edgecolor="#334155",
            labelcolor="#E2E8F0",
        )

        for spine in ax.spines.values():
            spine.set_color("#334155")

        fig.tight_layout()
        return self._figure_to_png_bytes(fig)

    async def show_rgb_histograms(self, e):
        if not self._require_image():
            return

        self._set_busy(True, "Building RGB histograms…")

        try:
            plot_bytes = await asyncio.to_thread(
                self._build_rgb_histogram_plot
            )

            self._set_processed_bytes(
                plot_bytes,
                "RGB Histogram Comparison",
                "RGB histogram comparison generated.",
            )

            self.color_view.show_histogram_status()

        except Exception as error:
            self._toast(
                f"Histogram error: {error}",
                error=True,
            )

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
        titles = [
            "Red Spectrum",
            "Green Spectrum",
            "Blue Spectrum",
        ]

        fig, axes = plt.subplots(1, 3, figsize=(11, 4))
        fig.patch.set_facecolor("#0A0F19")

        for ax, spectrum, title in zip(
            axes,
            spectra,
            titles,
        ):
            ax.imshow(spectrum, cmap="gray")
            ax.set_title(
                title,
                color="#F8FAFC",
                weight="bold",
            )
            ax.axis("off")

        fig.tight_layout()
        return self._figure_to_png_bytes(fig)

    async def show_rgb_frequency_spectra(self, e):
        if not self._require_image():
            return

        self._set_busy(
            True,
            "Computing three channel DFT spectra…",
        )

        try:
            plot_bytes = await asyncio.to_thread(
                self._build_rgb_frequency_plot
            )

            self._set_processed_bytes(
                plot_bytes,
                "RGB Frequency Content",
                "RGB channel spectra generated.",
            )

            self.color_view.show_frequency_status()

        except Exception as error:
            self._toast(
                f"RGB frequency error: {error}",
                error=True,
            )

        finally:
            self._set_busy(False)

    def _build_ycbcr_plot(self):
        image_array = np.array(
            self.original_image,
            dtype=np.uint8,
        )
        y, cb, cr = rgb_to_ycbcr(image_array)

        fig, axes = plt.subplots(1, 3, figsize=(11, 4))
        fig.patch.set_facecolor("#0A0F19")

        titles = [
            "Y • Luminance",
            "Cb • Blue chroma",
            "Cr • Red chroma",
        ]

        for ax, channel, title in zip(
            axes,
            [y, cb, cr],
            titles,
        ):
            ax.imshow(
                channel,
                cmap="gray",
                vmin=0,
                vmax=255,
            )
            ax.set_title(
                title,
                color="#F8FAFC",
                weight="bold",
            )
            ax.axis("off")

        fig.tight_layout()
        return self._figure_to_png_bytes(fig), y, cb, cr

    async def show_ycbcr_channels(self, e):
        if not self._require_image():
            return

        self._set_busy(True, "Converting RGB to YCbCr…")

        try:
            plot_bytes, y, cb, cr = await asyncio.to_thread(
                self._build_ycbcr_plot
            )

            self._set_processed_bytes(
                plot_bytes,
                "YCbCr Color Space",
                "YCbCr components generated.",
            )

            y_stats = get_channel_statistics(y)
            cb_stats = get_channel_statistics(cb)
            cr_stats = get_channel_statistics(cr)

            self.color_view.show_ycbcr_status()
            self.color_view.mode_description.value = (
                "Y = luminance • Cb = blue chroma • "
                "Cr = red chroma   |   "
                f"Mean Y: {y_stats['mean']:.1f} • "
                f"Cb: {cb_stats['mean']:.1f} • "
                f"Cr: {cr_stats['mean']:.1f}"
            )
            self.color_view.mode_description.update()

        except Exception as error:
            self._toast(f"YCbCr error: {error}", error=True)

        finally:
            self._set_busy(False)

    # =========================================================
    # MATPLOTLIB -> PNG BYTES
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
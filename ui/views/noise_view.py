"""Feature 3 — Image Noise Cleaner."""

import flet as ft

from ui.theme import AppColors
from ui.components.control_card import SliderControlCard
from ui.components.spatial_controls import (
    ActionButton,
    MetricPanel,
    SegmentedSelector,
    SpatialPage,
    hint,
    parameter_card,
)

ACCENT = AppColors.PURPLE


class NoiseView:

    def __init__(self, on_add_noise, on_clean, on_compare):
        self.on_add_noise = on_add_noise
        self.on_clean = on_clean
        self.on_compare = on_compare

        # -------------------------------------------------
        # NOISE
        # -------------------------------------------------

        self.noise_selector = SegmentedSelector(
            options=[
                ("gaussian", "Gaussian", ft.Icons.BLUR_LINEAR),
                ("salt_pepper", "Salt & pepper", ft.Icons.GRAIN),
            ],
            value="gaussian",
            accent=ACCENT,
            on_change=self._on_noise_change,
        )

        self.sigma_control = SliderControlCard(
            title="Gaussian sigma",
            min_value=5,
            max_value=60,
            value=20,
            divisions=11,
            accent=ACCENT,
            description="Standard deviation of the added noise.",
        )

        self.density_control = SliderControlCard(
            title="Corrupted pixels",
            min_value=1,
            max_value=30,
            value=5,
            divisions=29,
            suffix=" %",
            accent=ACCENT,
            description="Fraction of pixels forced to pure black or white.",
        )

        self.sigma_panel = ft.Container(
            visible=True,
            content=self.sigma_control.control,
        )

        self.density_panel = ft.Container(
            visible=False,
            content=self.density_control.control,
        )

        # -------------------------------------------------
        # FILTER
        # -------------------------------------------------

        self.filter_selector = SegmentedSelector(
            options=[
                ("mean", "Mean", ft.Icons.CALCULATE_OUTLINED),
                ("gaussian", "Gaussian", ft.Icons.BLUR_ON),
                ("median", "Median", ft.Icons.FILTER_ALT_OUTLINED),
            ],
            value="gaussian",
            accent=AppColors.BLUE,
        )

        self.filter_size_control = SliderControlCard(
            title="Filter size",
            min_value=3,
            max_value=9,
            value=3,
            divisions=3,
            suffix=" px",
            accent=AppColors.BLUE,
            description="Odd sizes only.",
        )

        self.metrics = MetricPanel(
            title="Quality",
            accent=ACCENT,
            rows=[
                ("noise", "Noise applied"),
                ("noisy_psnr", "Noisy PSNR"),
                ("cleaned_psnr", "Cleaned PSNR"),
                ("gain", "Improvement"),
            ],
        )

        self.control = SpatialPage(
            badge="FEATURE 3",
            title="Image Noise Cleaner",
            subtitle=(
                "Add noise, then remove it. The right filter depends "
                "entirely on the kind of noise present."
            ),
            icon=ft.Icons.GRAIN,
            accent=ACCENT,
            sections=[
                ft.ResponsiveRow(
                    spacing=14,
                    run_spacing=14,
                    controls=[
                        parameter_card(
                            "1. Add noise",
                            ft.Icons.SCATTER_PLOT_OUTLINED,
                            ACCENT,
                            [
                                self.noise_selector.control,
                                self.sigma_panel,
                                self.density_panel,
                                ActionButton(
                                    "Add noise",
                                    "Corrupt the original image",
                                    ft.Icons.PLAY_ARROW_ROUNDED,
                                    ACCENT,
                                    self.on_add_noise,
                                    col={"xs": 12},
                                ).control,
                            ],
                        ),
                        parameter_card(
                            "2. Clean it",
                            ft.Icons.CLEANING_SERVICES_OUTLINED,
                            AppColors.BLUE,
                            [
                                self.filter_selector.control,
                                self.filter_size_control.control,
                                ActionButton(
                                    "Clean noise",
                                    "Apply the selected filter",
                                    ft.Icons.PLAY_ARROW_ROUNDED,
                                    AppColors.BLUE,
                                    self.on_clean,
                                    col={"xs": 12},
                                ).control,
                            ],
                        ),
                    ],
                ),
                ft.ResponsiveRow(
                    spacing=14,
                    run_spacing=14,
                    controls=[
                        ft.Container(
                            col={"xs": 12, "md": 6},
                            content=ActionButton(
                                "Compare all three filters",
                                "Mean vs Gaussian vs median, with PSNR",
                                ft.Icons.INSIGHTS_OUTLINED,
                                AppColors.GREEN,
                                self.on_compare,
                                col={"xs": 12},
                            ).control,
                        ),
                        ft.Container(
                            col={"xs": 12, "md": 6},
                            content=self.metrics.control,
                        ),
                    ],
                ),
                self._guide(),
            ],
        ).control

    # =========================================================
    # NOISE TYPE
    # =========================================================

    def _on_noise_change(self, noise_type):
        self.sigma_panel.visible = noise_type == "gaussian"
        self.density_panel.visible = noise_type == "salt_pepper"

        # Median is the right default for impulse noise, Gaussian
        # smoothing for additive noise. Nudge, don't force.
        self.filter_selector.set_value(
            "median" if noise_type == "salt_pepper" else "gaussian",
            notify=False,
        )

        try:
            self.sigma_panel.update()
            self.density_panel.update()
        except Exception:
            pass

    def _guide(self):
        return ft.Container(
            padding=13,
            bgcolor=AppColors.SURFACE_SOFT,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            border_radius=ft.BorderRadius.all(14),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(
                                ft.Icons.LIGHTBULB_OUTLINE,
                                size=15,
                                color=AppColors.ORANGE,
                            ),
                            ft.Text(
                                "The point of this feature",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=AppColors.TEXT,
                            ),
                        ],
                    ),
                    hint(
                        "On salt-and-pepper noise, median filtering beats "
                        "averaging by roughly 14 dB — a single black pixel "
                        "drags a mean but not a median."
                    ),
                    hint(
                        "On Gaussian noise the two are within about 0.5 dB, "
                        "because averaging is close to optimal when the "
                        "noise is symmetric around zero."
                    ),
                    hint(
                        "Use smooth_scene.png: flat patches make the noise "
                        "obvious and the gradients reveal over-smoothing."
                    ),
                ],
            ),
        )

    # =========================================================
    # PUBLIC GETTERS
    # =========================================================

    def get_noise_type(self):
        return self.noise_selector.get_value()

    def get_sigma(self):
        return float(self.sigma_control.get_value())

    def get_density(self):
        return float(self.density_control.get_value()) / 100.0

    def get_filter(self):
        return self.filter_selector.get_value()

    def get_filter_size(self):
        size = self.filter_size_control.get_int_value()
        return size if size % 2 == 1 else size + 1

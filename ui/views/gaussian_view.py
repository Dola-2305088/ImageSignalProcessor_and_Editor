"""Feature 10 — Gaussian Blur with Separability."""

import flet as ft

from ui.theme import AppColors
from ui.components.control_card import SliderControlCard
from ui.components.spatial_controls import (
    ActionButton,
    MetricPanel,
    SpatialPage,
    hint,
    parameter_card,
)

ACCENT = AppColors.PURPLE


class GaussianView:

    def __init__(self, on_separable, on_full_2d, on_benchmark):
        self.on_separable = on_separable
        self.on_full_2d = on_full_2d
        self.on_benchmark = on_benchmark

        self.size_control = SliderControlCard(
            title="Kernel size",
            min_value=3,
            max_value=15,
            value=7,
            divisions=6,
            suffix=" px",
            accent=ACCENT,
            description="Odd sizes only.",
        )

        self.sigma_control = SliderControlCard(
            title="Sigma",
            min_value=0.5,
            max_value=5.0,
            value=1.5,
            divisions=9,
            accent=ACCENT,
            description="Spread of the Gaussian. Larger blurs more.",
        )

        self.metrics = MetricPanel(
            title="Separability report",
            accent=ACCENT,
            rows=[
                ("full_time", "Full 2D time"),
                ("sep_time", "Separable time"),
                ("speedup", "Measured speed-up"),
                ("theory", "Theoretical speed-up"),
                ("mae", "Mean absolute error"),
                ("max_diff", "Max pixel difference"),
            ],
        )

        self.control = SpatialPage(
            badge="FEATURE 10",
            title="Gaussian Blur with Separability",
            subtitle=(
                "A 2D Gaussian is separable: one K×K pass equals a 1×K "
                "pass followed by a K×1 pass, for far less work."
            ),
            icon=ft.Icons.BLUR_LINEAR,
            accent=ACCENT,
            sections=[
                ft.ResponsiveRow(
                    spacing=14,
                    run_spacing=14,
                    controls=[
                        parameter_card(
                            "Parameters",
                            ft.Icons.TUNE,
                            ACCENT,
                            [
                                self.size_control.control,
                                self.sigma_control.control,
                            ],
                        ),
                        ft.Container(
                            col={"xs": 12, "md": 6},
                            content=ft.Column(
                                spacing=14,
                                controls=[
                                    ft.ResponsiveRow(
                                        spacing=12,
                                        run_spacing=12,
                                        controls=[
                                            ActionButton(
                                                "Separable blur",
                                                "Two 1D passes",
                                                ft.Icons.PLAY_ARROW_ROUNDED,
                                                ACCENT,
                                                self.on_separable,
                                                col={"xs": 12},
                                            ).control,
                                            ActionButton(
                                                "Full 2D blur",
                                                "Single K×K pass",
                                                ft.Icons.GRID_4X4,
                                                AppColors.BLUE,
                                                self.on_full_2d,
                                                col={"xs": 12},
                                            ).control,
                                            ActionButton(
                                                "Benchmark both",
                                                "Time them and prove they "
                                                "match",
                                                ft.Icons.SPEED,
                                                AppColors.GREEN,
                                                self.on_benchmark,
                                                col={"xs": 12},
                                            ).control,
                                        ],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                self.metrics.control,
                self._guide(),
            ],
        ).control

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
                                ft.Icons.WARNING_AMBER_ROUNDED,
                                size=15,
                                color=AppColors.ORANGE,
                            ),
                            ft.Text(
                                "Use a small image for the benchmark",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=AppColors.TEXT,
                            ),
                        ],
                    ),
                    hint(
                        "Benchmarking runs full 2D convolution several "
                        "times in pure Python. Use small_scene.png (128×128) "
                        "— a 2048×2048 image is 256 times the work."
                    ),
                    hint(
                        "Cost per pixel drops from K² to 2K: a 7×7 kernel "
                        "goes from 49 multiply-adds to 14, a 3.5× "
                        "theoretical saving."
                    ),
                    hint(
                        "Measured speed-up is always below theory because "
                        "Python loop overhead dominates the arithmetic."
                    ),
                ],
            ),
        )

    # =========================================================
    # PUBLIC GETTERS
    # =========================================================

    def get_kernel_size(self):
        size = self.size_control.get_int_value()
        return size if size % 2 == 1 else size + 1

    def get_sigma(self):
        return round(float(self.sigma_control.get_value()), 2)

"""Feature 1 — Blur & Sharpen.

UI only. All convolution happens in algorithms/spatial/blur_sharpen.py,
which main_window calls through the callbacks passed in here.
"""

import flet as ft

from ui.theme import AppColors
from ui.components.control_card import SliderControlCard
from ui.components.spatial_controls import (
    ActionButton,
    KernelGrid,
    MetricPanel,
    SegmentedSelector,
    SpatialPage,
    hint,
    parameter_card,
)

ACCENT = AppColors.PURPLE


class BlurSharpenView:

    def __init__(self, on_apply, on_reset=None):
        self.on_apply = on_apply
        self.on_reset = on_reset

        self.mode_selector = SegmentedSelector(
            options=[
                ("blur", "Box blur", ft.Icons.BLUR_ON),
                ("sharpen", "Sharpen", ft.Icons.AUTO_AWESOME),
                ("custom", "Custom kernel", ft.Icons.GRID_4X4),
            ],
            value="blur",
            accent=ACCENT,
            on_change=self._on_mode_change,
        )

        self.size_control = SliderControlCard(
            title="Kernel size",
            min_value=3,
            max_value=15,
            value=3,
            divisions=6,
            suffix=" px",
            accent=ACCENT,
            description="Odd sizes only. Larger kernels blur more and "
                        "take longer — cost grows with size squared.",
        )

        self.kernel_grid = KernelGrid(size=3, accent=ACCENT)

        self.kernel_panel = ft.Container(
            visible=False,
            content=self.kernel_grid.control,
        )

        self.size_panel = ft.Container(
            visible=True,
            content=self.size_control.control,
        )

        self.metrics = MetricPanel(
            title="Result",
            accent=ACCENT,
            rows=[
                ("operation", "Operation"),
                ("kernel", "Kernel"),
                ("psnr", "PSNR vs original"),
                ("elapsed", "Time taken"),
            ],
        )

        self.control = SpatialPage(
            badge="FEATURE 1",
            title="Blur & Sharpen",
            subtitle=(
                "Apply blur, sharpening or your own kernel using the "
                "project's manual 2D convolution."
            ),
            icon=ft.Icons.BLUR_ON,
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
                                self.mode_selector.control,
                                self.size_panel,
                                self.kernel_panel,
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
                                                "Apply",
                                                "Convolve and preview",
                                                ft.Icons.PLAY_ARROW_ROUNDED,
                                                ACCENT,
                                                self.on_apply,
                                                col={"xs": 12},
                                            ).control,
                                        ],
                                    ),
                                    self.metrics.control,
                                ],
                            ),
                        ),
                    ],
                ),
                self._guide(),
            ],
        ).control

    # =========================================================
    # MODE
    # =========================================================

    def _on_mode_change(self, mode):
        self.size_panel.visible = mode == "blur"
        self.kernel_panel.visible = mode == "custom"

        try:
            self.size_panel.update()
            self.kernel_panel.update()
        except Exception:
            pass

    # =========================================================
    # GUIDE
    # =========================================================

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
                                "How to read the result",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=AppColors.TEXT,
                            ),
                        ],
                    ),
                    hint(
                        "Blur is a low-pass filter: it removes fine detail "
                        "first. On resolution_chart.png the tight line pairs "
                        "vanish while the wide ones survive."
                    ),
                    hint(
                        "An impulse convolved with a kernel reproduces the "
                        "kernel exactly. Zoom into one of the single dots to "
                        "see the kernel's true footprint."
                    ),
                    hint(
                        "Sharpening amplifies high frequencies, so it also "
                        "amplifies noise and produces halos around edges."
                    ),
                ],
            ),
        )

    # =========================================================
    # PUBLIC GETTERS
    # =========================================================

    def get_mode(self):
        return self.mode_selector.get_value()

    def get_kernel_size(self):
        size = self.size_control.get_int_value()
        return size if size % 2 == 1 else size + 1

    def get_custom_kernel(self):
        return self.kernel_grid.get_kernel()

    def show_kernel_error(self, message):
        self.kernel_grid.show_error(message)

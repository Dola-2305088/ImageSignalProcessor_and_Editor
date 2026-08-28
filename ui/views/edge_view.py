"""Feature 2 — Edge Detector (Sobel)."""

import flet as ft

from ui.theme import AppColors
from ui.components.spatial_controls import (
    ActionButton,
    MetricPanel,
    SegmentedSelector,
    SpatialPage,
    hint,
    kernel_preview,
    parameter_card,
)

ACCENT = AppColors.PURPLE

SOBEL_X = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
SOBEL_Y = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]


class EdgeView:

    def __init__(self, on_detect, on_compare=None):
        self.on_detect = on_detect
        self.on_compare = on_compare

        self.mode_selector = SegmentedSelector(
            options=[
                ("horizontal", "Horizontal", ft.Icons.HORIZONTAL_RULE),
                ("vertical", "Vertical", ft.Icons.VERTICAL_ALIGN_CENTER),
                ("combined", "Combined", ft.Icons.BORDER_OUTER),
            ],
            value="combined",
            accent=ACCENT,
        )

        self.metrics = MetricPanel(
            title="Edge statistics",
            accent=ACCENT,
            rows=[
                ("mode", "Mode"),
                ("max", "Peak edge strength"),
                ("mean", "Mean edge strength"),
                ("elapsed", "Time taken"),
            ],
        )

        actions = [
            ActionButton(
                "Detect edges",
                "Run the selected Sobel mode",
                ft.Icons.PLAY_ARROW_ROUNDED,
                ACCENT,
                self.on_detect,
                col={"xs": 12},
            ).control,
        ]

        if self.on_compare is not None:
            actions.append(
                ActionButton(
                    "Compare all three",
                    "Horizontal, vertical and combined side by side",
                    ft.Icons.DASHBOARD_OUTLINED,
                    AppColors.BLUE,
                    self.on_compare,
                    col={"xs": 12},
                ).control
            )

        self.control = SpatialPage(
            badge="FEATURE 2",
            title="Edge Detector",
            subtitle=(
                "Find horizontal, vertical and combined edges with Sobel "
                "convolution kernels."
            ),
            icon=ft.Icons.BORDER_OUTER,
            accent=ACCENT,
            sections=[
                ft.ResponsiveRow(
                    spacing=14,
                    run_spacing=14,
                    controls=[
                        parameter_card(
                            "Detection mode",
                            ft.Icons.TUNE,
                            ACCENT,
                            [
                                self.mode_selector.control,
                                hint(
                                    "Combined mode returns the gradient "
                                    "magnitude, sqrt(Gx² + Gy²), so it "
                                    "responds to edges at any angle."
                                ),
                                self._kernels(),
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
                                        controls=actions,
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
    # KERNELS
    # =========================================================

    def _kernels(self):
        return ft.Row(
            spacing=26,
            controls=[
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(
                            "Sobel X",
                            size=10,
                            weight=ft.FontWeight.W_600,
                            color=AppColors.TEXT_SECONDARY,
                        ),
                        kernel_preview(SOBEL_X, ACCENT),
                    ],
                ),
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(
                            "Sobel Y",
                            size=10,
                            weight=ft.FontWeight.W_600,
                            color=AppColors.TEXT_SECONDARY,
                        ),
                        kernel_preview(SOBEL_Y, ACCENT),
                    ],
                ),
            ],
        )

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
                                "What to expect",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=AppColors.TEXT,
                            ),
                        ],
                    ),
                    hint(
                        "On edges_shapes.png the square gives strong "
                        "horizontal and vertical responses but nothing "
                        "diagonal; the triangle is the reverse."
                    ),
                    hint(
                        "Sobel X detects intensity change along x, which "
                        "means it highlights vertical edges — the naming "
                        "trips people up."
                    ),
                    hint(
                        "Output is a single-channel gradient image, so the "
                        "result is always shown in grayscale."
                    ),
                ],
            ),
        )

    # =========================================================
    # PUBLIC GETTERS
    # =========================================================

    def get_mode(self):
        return self.mode_selector.get_value()

"""Feature 6 — Image Resizer."""

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


class ResizeView:

    def __init__(self, on_resize, on_compare):
        self.on_resize = on_resize
        self.on_compare = on_compare

        self.method_selector = SegmentedSelector(
            options=[
                ("nearest", "Nearest", ft.Icons.GRID_ON),
                ("bilinear", "Bilinear", ft.Icons.GRADIENT),
            ],
            value="bilinear",
            accent=ACCENT,
        )

        self.scale_control = SliderControlCard(
            title="Scale",
            min_value=10,
            max_value=400,
            value=25,
            divisions=39,
            suffix=" %",
            accent=ACCENT,
            description="Below 100% downsamples, above 100% enlarges.",
        )

        self.antialias_switch = ft.Switch(
            value=True,
            active_color=AppColors.GREEN,
            scale=0.85,
        )

        self.metrics = MetricPanel(
            title="Output",
            accent=ACCENT,
            rows=[
                ("method", "Method"),
                ("size", "Output size"),
                ("antialias", "Anti-aliasing"),
                ("elapsed", "Time taken"),
            ],
        )

        self.control = SpatialPage(
            badge="FEATURE 6",
            title="Image Resizer",
            subtitle=(
                "Nearest-neighbour and bilinear interpolation, with "
                "Gaussian pre-filtering before downsampling."
            ),
            icon=ft.Icons.ASPECT_RATIO,
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
                                self.method_selector.control,
                                self.scale_control.control,
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        self.antialias_switch,
                                        ft.Column(
                                            spacing=1,
                                            expand=True,
                                            controls=[
                                                ft.Text(
                                                    "Anti-alias before "
                                                    "downsampling",
                                                    size=11,
                                                    color=AppColors.TEXT,
                                                ),
                                                hint(
                                                    "Ignored when enlarging."
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
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
                                                "Resize",
                                                "Run with current settings",
                                                ft.Icons.PLAY_ARROW_ROUNDED,
                                                ACCENT,
                                                self.on_resize,
                                                col={"xs": 12},
                                            ).control,
                                            ActionButton(
                                                "Compare methods",
                                                "Nearest vs bilinear vs "
                                                "anti-aliased",
                                                ft.Icons.DASHBOARD_OUTLINED,
                                                AppColors.GREEN,
                                                self.on_compare,
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
                                "Aliasing, and why grey is correct",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=AppColors.TEXT,
                            ),
                        ],
                    ),
                    hint(
                        "Load zoneplate.png and downsample to 25% with "
                        "anti-aliasing off. The outer rings fold into false "
                        "low-frequency patterns — that is aliasing."
                    ),
                    hint(
                        "checker_fine.png downsampled with anti-aliasing on "
                        "goes almost uniformly grey. That is the right "
                        "answer: the pattern cannot be represented at the "
                        "smaller size, so it is averaged away rather than "
                        "faked."
                    ),
                    hint(
                        "Enlarging shows the opposite pair: nearest gives "
                        "hard blocky steps, bilinear gives smooth ramps."
                    ),
                ],
            ),
        )

    # =========================================================
    # PUBLIC GETTERS
    # =========================================================

    def get_method(self):
        return self.method_selector.get_value()

    def get_scale(self):
        return float(self.scale_control.get_value()) / 100.0

    def get_antialias(self):
        return bool(self.antialias_switch.value)

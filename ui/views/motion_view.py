"""Feature 7 — Motion Blur Lab."""

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


class MotionView:

    def __init__(self, on_apply, on_show_kernel=None):
        self.on_apply = on_apply
        self.on_show_kernel = on_show_kernel

        self.length_control = SliderControlCard(
            title="Blur length",
            min_value=3,
            max_value=35,
            value=15,
            divisions=16,
            suffix=" px",
            accent=ACCENT,
            description="How far the camera moved during exposure.",
        )

        self.angle_control = SliderControlCard(
            title="Blur angle",
            min_value=0,
            max_value=180,
            value=0,
            divisions=36,
            suffix="°",
            accent=ACCENT,
            description="0° horizontal, 45° diagonal, 90° vertical.",
        )

        self.handoff = ft.Text(
            "No kernel generated yet.",
            size=10,
            color=AppColors.MUTED,
        )

        self.metrics = MetricPanel(
            title="Blur report",
            accent=ACCENT,
            rows=[
                ("kernel", "Kernel size"),
                ("angle", "Angle"),
                ("psnr", "PSNR vs original"),
                ("elapsed", "Time taken"),
            ],
        )

        actions = [
            ActionButton(
                "Apply motion blur",
                "Convolve with the line kernel",
                ft.Icons.PLAY_ARROW_ROUNDED,
                ACCENT,
                self.on_apply,
                col={"xs": 12},
            ).control,
        ]

        if self.on_show_kernel is not None:
            actions.append(
                ActionButton(
                    "Show the kernel",
                    "Preview the line-shaped PSF",
                    ft.Icons.GRID_4X4,
                    AppColors.BLUE,
                    self.on_show_kernel,
                    col={"xs": 12},
                ).control
            )

        self.control = SpatialPage(
            badge="FEATURE 7",
            title="Motion Blur Lab",
            subtitle=(
                "Simulate camera motion with a line-shaped kernel. The "
                "exact kernel is handed to Restoration."
            ),
            icon=ft.Icons.MOTION_PHOTOS_ON,
            accent=ACCENT,
            sections=[
                ft.ResponsiveRow(
                    spacing=14,
                    run_spacing=14,
                    controls=[
                        parameter_card(
                            "Motion parameters",
                            ft.Icons.TUNE,
                            ACCENT,
                            [
                                self.length_control.control,
                                self.angle_control.control,
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
                                    ft.Container(
                                        padding=ft.Padding.symmetric(
                                            horizontal=12,
                                            vertical=10,
                                        ),
                                        bgcolor=AppColors.SURFACE_DARK,
                                        border_radius=ft.BorderRadius.all(10),
                                        content=ft.Row(
                                            spacing=8,
                                            controls=[
                                                ft.Icon(
                                                    ft.Icons.LINK,
                                                    size=15,
                                                    color=AppColors.GREEN,
                                                ),
                                                self.handoff,
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                self._guide(),
            ],
        ).control

    # =========================================================
    # HANDOFF STATE
    # =========================================================

    def set_handoff(self, message, ready=True):
        self.handoff.value = message
        self.handoff.color = (
            AppColors.TEXT_SECONDARY if ready else AppColors.MUTED
        )

        try:
            self.handoff.update()
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
                                "Half of a two-part story",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=AppColors.TEXT,
                            ),
                        ],
                    ),
                    hint(
                        "This page degrades the image; Restoration recovers "
                        "it. Because the kernel is known exactly, the "
                        "recovery is a fair test of deconvolution."
                    ),
                    hint(
                        "The kernel sums to 1, so overall brightness is "
                        "preserved — only detail is smeared."
                    ),
                    hint(
                        "Use text_grid.png: letters and bar gratings make "
                        "the direction obvious, and the impulse grid shows "
                        "the kernel shape directly in the output."
                    ),
                ],
            ),
        )

    # =========================================================
    # PUBLIC GETTERS
    # =========================================================

    def get_length(self):
        return self.length_control.get_int_value()

    def get_angle(self):
        return self.angle_control.get_int_value()

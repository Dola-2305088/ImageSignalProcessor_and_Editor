"""Feature 11 — Wiener Deconvolution / Restoration."""

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

# A linear K slider is useless because the useful range spans three
# decades. The slider picks an index into this ladder instead.
K_VALUES = [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1]


class WienerView:

    def __init__(self, on_restore, on_compare, on_sweep):
        self.on_restore = on_restore
        self.on_compare = on_compare
        self.on_sweep = on_sweep

        self.k_control = SliderControlCard(
            title="Regularisation K (index)",
            min_value=0,
            max_value=len(K_VALUES) - 1,
            value=4,
            divisions=len(K_VALUES) - 1,
            accent=ACCENT,
            on_change=self._on_k_change,
            description="Small K restores aggressively but amplifies "
                        "noise; large K is safer but oversmooths.",
        )

        self.k_readout = ft.Text(
            f"K = {K_VALUES[4]}",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=ACCENT,
        )

        self.noise_control = SliderControlCard(
            title="Noise added to blur",
            min_value=0,
            max_value=20,
            value=5,
            divisions=20,
            suffix=" σ",
            accent=AppColors.ORANGE,
            description="Set to 0 for a clean blur. Noise is what makes "
                        "naive inverse filtering fail.",
        )

        self.source_note = ft.Text(
            "Using the kernel from Motion Blur Lab if one exists, "
            "otherwise generating length 15 at 0°.",
            size=10,
            color=AppColors.MUTED,
        )

        self.metrics = MetricPanel(
            title="Restoration quality",
            accent=ACCENT,
            rows=[
                ("blurred", "Blurred PSNR"),
                ("inverse", "Inverse filter PSNR"),
                ("wiener", "Wiener PSNR"),
                ("gain", "Wiener advantage"),
                ("k", "K used"),
            ],
        )

        self.control = SpatialPage(
            badge="FEATURE 11",
            title="Wiener Deconvolution",
            subtitle=(
                "Recover a blurred image from its known kernel, and show "
                "where naive inverse filtering breaks down."
            ),
            icon=ft.Icons.AUTO_FIX_HIGH,
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
                                self.k_control.control,
                                ft.Row(
                                    controls=[
                                        ft.Text(
                                            "Actual value",
                                            size=11,
                                            color=AppColors.TEXT_SECONDARY,
                                        ),
                                        ft.Container(expand=True),
                                        self.k_readout,
                                    ],
                                ),
                                self.noise_control.control,
                                self.source_note,
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
                                                "Restore with Wiener",
                                                "Deconvolve at the current K",
                                                ft.Icons.PLAY_ARROW_ROUNDED,
                                                ACCENT,
                                                self.on_restore,
                                                col={"xs": 12},
                                            ).control,
                                            ActionButton(
                                                "Inverse vs Wiener",
                                                "Run both and compare PSNR",
                                                ft.Icons.COMPARE_ARROWS,
                                                AppColors.BLUE,
                                                self.on_compare,
                                                col={"xs": 12},
                                            ).control,
                                            ActionButton(
                                                "Sweep K",
                                                "Plot PSNR against K",
                                                ft.Icons.SHOW_CHART,
                                                AppColors.GREEN,
                                                self.on_sweep,
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

    # =========================================================
    # K READOUT
    # =========================================================

    def _on_k_change(self, e):
        self.k_readout.value = f"K = {self.get_k()}"

        try:
            self.k_readout.update()
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
                                "Getting a convincing demo",
                                size=11,
                                weight=ft.FontWeight.W_600,
                                color=AppColors.TEXT,
                            ),
                        ],
                    ),
                    hint(
                        "With noise at 0, naive inverse filtering actually "
                        "wins — it inverts the blur almost perfectly. That "
                        "is worth showing before you show it failing."
                    ),
                    hint(
                        "Set noise to 5 and K to 0.01: on text_grid.png the "
                        "inverse filter collapses to roughly 7 dB while "
                        "Wiener holds around 18 dB."
                    ),
                    hint(
                        "Optimal K rises with noise — near 0.001 at σ=2, "
                        "0.01 at σ=5, 0.02 at σ=10. Sweep K to find it."
                    ),
                ],
            ),
        )

    # =========================================================
    # PUBLIC GETTERS
    # =========================================================

    def get_k(self):
        index = int(round(self.k_control.get_value()))
        index = max(0, min(index, len(K_VALUES) - 1))
        return K_VALUES[index]

    def get_noise_sigma(self):
        return float(self.noise_control.get_value())

    @staticmethod
    def k_ladder():
        return list(K_VALUES)

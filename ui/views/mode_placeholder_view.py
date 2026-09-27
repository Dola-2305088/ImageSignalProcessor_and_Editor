"""Temporary stage for the Discover and SaveEarth modes.

Routing, the sidebar and the Home mode cards are wired to these pages
now, so the real lesson / game views can later replace them one-for-one
in main_window without touching navigation again.
"""

import flet as ft

from ui.theme import AppColors, AppLayout


class ModePlaceholderView:
    """A styled "arriving soon" stage for a mode that is still in progress."""

    def __init__(self, badge, title, subtitle, icon, accent, chapters):
        self.control = ft.Container(
            padding=ft.Padding.symmetric(horizontal=36, vertical=40),
            border_radius=ft.BorderRadius.all(AppLayout.CARD_RADIUS),
            border=ft.Border.all(1, AppColors.BORDER),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#0E1526", "#0A0F1C", "#120F24"],
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    ft.Container(
                        width=92,
                        height=92,
                        alignment=ft.Alignment.CENTER,
                        border_radius=46,
                        bgcolor=AppColors.SURFACE_DARK,
                        border=ft.Border.all(1.5, accent),
                        shadow=ft.BoxShadow(
                            blur_radius=40,
                            spread_radius=2,
                            color="#55" + accent.lstrip("#"),  # Flet hex is #AARRGGBB
                        ),
                        content=ft.Icon(icon, size=42, color=accent),
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        border_radius=8,
                        bgcolor=AppColors.SURFACE_3,
                        content=ft.Text(
                            badge,
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=accent,
                        ),
                    ),
                    ft.Text(
                        title,
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT,
                    ),
                    ft.Text(
                        subtitle,
                        size=13,
                        color=AppColors.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=6),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True,
                        spacing=10,
                        run_spacing=10,
                        controls=[
                            self._chapter(number, text, accent)
                            for number, text in enumerate(chapters, start=1)
                        ],
                    ),
                ],
            ),
        )

    @staticmethod
    def _chapter(number, text, accent):
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            border_radius=12,
            bgcolor=AppColors.SURFACE_SOFT,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Row(
                tight=True,
                spacing=10,
                controls=[
                    ft.Container(
                        width=24,
                        height=24,
                        alignment=ft.Alignment.CENTER,
                        border_radius=12,
                        border=ft.Border.all(1, accent),
                        content=ft.Text(
                            str(number),
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=accent,
                        ),
                    ),
                    ft.Text(text, size=11, color=AppColors.TEXT_SECONDARY),
                ],
            ),
        )

import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
)


class SectionHeader:
    """
    Reusable header for feature views.

    Example:

        Feature 4 — Frequency Editor
        Inspect the 2D DFT and apply frequency filters.

    Can optionally show:
    - Icon
    - Feature number/tag
    - Title
    - Subtitle
    - Accent color
    - Right-side custom control
    """

    def __init__(
        self,
        title,
        subtitle=None,
        icon=None,
        accent=None,
        badge=None,
        trailing=None,
    ):

        # =====================================================
        # CONFIGURATION
        # =====================================================

        self.title = title

        self.subtitle = subtitle

        self.icon = icon

        self.accent = (
            accent
            or AppColors.CYAN
        )

        self.badge = badge

        self.trailing = trailing


        # =====================================================
        # BUILD
        # =====================================================

        self.control = self._build()


    # =========================================================
    # BUILD HEADER
    # =========================================================

    def _build(self):

        left_controls = []


        # =====================================================
        # ICON
        # =====================================================

        if self.icon is not None:

            left_controls.append(

                ft.Container(

                    width=48,
                    height=48,

                    alignment=ft.Alignment.CENTER,

                    bgcolor=AppColors.SURFACE_3,

                    border_radius=ft.BorderRadius.all(
                        15
                    ),

                    border=ft.Border.all(
                        1,
                        AppColors.BORDER,
                    ),

                    content=ft.Icon(
                        self.icon,
                        size=24,
                        color=self.accent,
                    ),
                )
            )


        # =====================================================
        # TEXT AREA
        # =====================================================

        text_controls = []


        # =====================================================
        # BADGE
        # =====================================================

        if self.badge:

            text_controls.append(

                ft.Container(

                    padding=ft.Padding.symmetric(
                        horizontal=9,
                        vertical=4,
                    ),

                    bgcolor=self._badge_background(),

                    border_radius=ft.BorderRadius.all(
                        100
                    ),

                    content=ft.Text(
                        self.badge,
                        size=9,
                        weight=ft.FontWeight.BOLD,
                        color=self.accent,
                    ),
                )
            )


        # =====================================================
        # TITLE
        # =====================================================

        text_controls.append(

            ft.Text(
                self.title,
                size=18,
                weight=ft.FontWeight.BOLD,
                color=AppColors.TEXT,
            )
        )


        # =====================================================
        # SUBTITLE
        # =====================================================

        if self.subtitle:

            text_controls.append(

                ft.Text(
                    self.subtitle,
                    size=11,
                    color=AppColors.MUTED,
                )
            )


        left_controls.append(

            ft.Column(
                spacing=3,
                expand=True,
                controls=text_controls,
            )
        )


        # =====================================================
        # MAIN ROW
        # =====================================================

        row_controls = [

            ft.Row(
                spacing=14,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=left_controls,
            )
        ]


        # =====================================================
        # OPTIONAL RIGHT-SIDE CONTROL
        # =====================================================

        if self.trailing is not None:

            row_controls.append(
                self.trailing
            )


        return ft.Container(

            padding=ft.Padding.only(
                bottom=4
            ),

            content=ft.Column(

                spacing=12,

                controls=[

                    # =========================================
                    # HEADER ROW
                    # =========================================

                    ft.Row(
                        vertical_alignment=(
                            ft.CrossAxisAlignment.CENTER
                        ),
                        controls=row_controls,
                    ),


                    # =========================================
                    # ACCENT DIVIDER
                    # =========================================

                    ft.Row(

                        spacing=0,

                        controls=[

                            ft.Container(
                                width=80,
                                height=3,
                                bgcolor=self.accent,
                                border_radius=3,
                            ),

                            ft.Container(
                                expand=True,
                                height=1,
                                bgcolor=AppColors.BORDER,
                            ),
                        ],
                    ),
                ],
            ),
        )


    # =========================================================
    # BADGE BACKGROUND
    # =========================================================

    def _badge_background(self):

        # Slight transparent-looking dark tints
        # chosen according to the feature accent.

        color_map = {

            AppColors.BLUE:
                AppColors.BLUE_TINT,

            AppColors.CYAN:
                AppColors.CYAN_TINT,

            AppColors.PURPLE:
                AppColors.PURPLE_TINT,

            AppColors.GREEN:
                AppColors.GREEN_TINT,

            AppColors.ORANGE:
                AppColors.ORANGE_TINT,

            AppColors.PINK:
                AppColors.PINK_TINT,
        }


        return color_map.get(
            self.accent,
            AppColors.SURFACE_3,
        )
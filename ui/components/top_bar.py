from pathlib import Path

import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    app_logo_gradient,
    header_gradient,
)


class TopBar:
    """
    Modern AETHERIS galaxy-themed application header.

    Public API intentionally matches the previous TopBar:
        - self.control
        - self.open_button
        - self.save_button
        - self.reset_button / self.reset_shell
        - set_active_feature()
        - set_home_mode()

    This version uses the supplied AETHERIS PNG emblem in the header.
    """

    def __init__(
        self,
        on_open_image,
        on_save_result,
        on_reset_result,
    ):
        self.on_open_image = on_open_image
        self.on_save_result = on_save_result
        self.on_reset_result = on_reset_result

        self.active_feature_text = ft.Text(
            "Home",
            size=10,
            weight=ft.FontWeight.W_600,
            color="#DDE7FF",
        )

        self.logo_shell = None
        self.feature_pill = None
        self.open_button = None
        self.save_button = None
        self.reset_shell = None
        self.reset_button = None
        self.status_badge = None

        self.control = self._build()

    # =========================================================
    # AETHERIS PNG LOGO
    # =========================================================

    @staticmethod
    def _logo_path():
        """
        Resolve the AETHERIS top-bar logo without depending on the
        process working directory.

        Recommended project location:
            assets/aetheris_topbar_logo.png
        """
        current_file = Path(__file__).resolve()

        # Expected structure: <project>/ui/components/top_bar.py
        project_root = current_file.parents[2]

        candidates = [
            project_root / "assets" / "aetheris_topbar_logo.png",
            project_root / "assets" / "logo.png",
            project_root / "aetheris_topbar_logo.png",
        ]

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        # Safe fallback for projects launched with Flet's assets_dir.
        return "assets/images/logo.png"

    def _aetheris_logo_image(self):
        return ft.Image(
            src=self._logo_path(),
            width=54,
            height=54,
            fit=ft.BoxFit.COVER,
        )

    # =========================================================
    # BUILD
    # =========================================================

    def _build(self):
        self.logo_shell = ft.Container(
            width=56,
            height=56,
            border_radius=18,
            gradient=app_logo_gradient(),
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(
                1,
                "#2B3D62",
            ),
            shadow=ft.BoxShadow(
                blur_radius=26,
                spread_radius=-3,
                color="#553D54FF",
            ),
            animate_scale=ft.Animation(
                duration=180,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            on_hover=self._hover_logo,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=self._aetheris_logo_image(),
        )

        self.feature_pill = ft.Container(
            padding=ft.Padding.symmetric(
                horizontal=11,
                vertical=6,
            ),
            border_radius=999,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[
                    "#1A1E3528",
                    "#11152224",
                ],
            ),
            border=ft.Border.all(
                1,
                "#34456476",
            ),
            shadow=ft.BoxShadow(
                blur_radius=16,
                spread_radius=-6,
                color="#5522D3EE",
            ),
            content=ft.Row(
                tight=True,
                spacing=7,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=7,
                        height=7,
                        border_radius=999,
                        bgcolor="#8EA1FF",
                        shadow=ft.BoxShadow(
                            blur_radius=9,
                            spread_radius=0,
                            color="#778EA1FF",
                        ),
                    ),
                    self.active_feature_text,
                ],
            ),
        )

        brand_text = ft.Column(
            spacing=2,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    tight=True,
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "A E T H E R I S",
                            size=18,
                            weight=ft.FontWeight.W_600,
                            color="#F7F2FF",
                        ),
                        ft.Container(
                            padding=ft.Padding.symmetric(
                                horizontal=7,
                                vertical=3,
                            ),
                            border_radius=999,
                            bgcolor="#171328",
                            border=ft.Border.all(
                                1,
                                "#3F315F",
                            ),
                            content=ft.Text(
                                "LAB",
                                size=7,
                                weight=ft.FontWeight.BOLD,
                                color="#C9B4FF",
                            ),
                        ),
                    ],
                ),
                ft.Row(
                    tight=True,
                    spacing=9,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "DIGITAL IMAGING LAB",
                            size=8,
                            weight=ft.FontWeight.W_500,
                            color="#8C97B8",
                        ),
                        ft.Container(
                            width=3,
                            height=3,
                            border_radius=999,
                            bgcolor="#48516A",
                        ),
                        self.feature_pill,
                    ],
                ),
            ],
        )

        brand_area = ft.Row(
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.logo_shell,
                brand_text,
            ],
        )

        self.status_badge = ft.Container(
            padding=ft.Padding.symmetric(
                horizontal=11,
                vertical=7,
            ),
            border_radius=999,
            bgcolor="#0A1817",
            border=ft.Border.all(
                1,
                "#20483E",
            ),
            shadow=ft.BoxShadow(
                blur_radius=14,
                spread_radius=-5,
                color="#4434D399",
            ),
            content=ft.Row(
                tight=True,
                spacing=7,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=7,
                        height=7,
                        border_radius=999,
                        bgcolor=AppColors.GREEN,
                        shadow=ft.BoxShadow(
                            blur_radius=9,
                            color="#6634D399",
                        ),
                    ),
                    ft.Text(
                        "SYSTEM READY",
                        size=8,
                        weight=ft.FontWeight.W_600,
                        color="#A9E8CF",
                    ),
                ],
            ),
        )

        self.open_button = self._action_button(
            text="Open Image",
            icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
            handler=self.on_open_image,
            accent="#7D8CFF",
            fill_top="#242956",
            fill_bottom="#171D3B",
            border="#3A4C8F",
            primary=True,
        )

        self.save_button = self._action_button(
            text="Save Result",
            icon=ft.Icons.DOWNLOAD_ROUNDED,
            handler=self.on_save_result,
            accent="#66D6AF",
            fill_top="#15392F",
            fill_bottom="#0D2721",
            border="#26624E",
        )
        self.save_button.visible = False

        self.reset_shell = ft.Container(
            width=42,
            height=42,
            alignment=ft.Alignment.CENTER,
            border_radius=14,
            bgcolor="#0D1220",
            border=ft.Border.all(
                1,
                "#293148",
            ),
            animate_scale=ft.Animation(
                duration=160,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate=ft.Animation(
                duration=160,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            on_hover=self._hover_reset,
            visible=False,
            shadow=ft.BoxShadow(
                blur_radius=12,
                spread_radius=-6,
                color="#33111C3A",
            ),
            content=ft.IconButton(
                icon=ft.Icons.RESTART_ALT_ROUNDED,
                icon_color="#8E9AB6",
                icon_size=19,
                tooltip="Reset processed result",
                on_click=self.on_reset_result,
            ),
        )

        self.reset_button = self.reset_shell

        action_controls = ft.Row(
            tight=True,
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.status_badge,
                ft.Container(
                    width=1,
                    height=25,
                    bgcolor="#283249",
                    margin=ft.Margin.symmetric(horizontal=3),
                ),
                self.open_button,
                self.save_button,
                self.reset_shell,
            ],
        )

        action_area = ft.Container(
            padding=ft.Padding.symmetric(
                horizontal=8,
                vertical=6,
            ),
            border_radius=18,
            bgcolor="#760A0F1B",
            border=ft.Border.all(
                1,
                "#2A344E",
            ),
            shadow=ft.BoxShadow(
                blur_radius=24,
                spread_radius=-10,
                color="#44101A34",
            ),
            content=action_controls,
        )

        main_row = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                brand_area,
                ft.Container(expand=True),
                action_area,
            ],
        )

        background_fx = ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    left=-90,
                    top=-60,
                    width=320,
                    height=150,
                    border_radius=999,
                    gradient=ft.RadialGradient(
                        colors=[
                            "#245F2C92",
                            "#005F2C92",
                        ],
                    ),
                ),
                ft.Container(
                    right=90,
                    top=-70,
                    width=340,
                    height=160,
                    border_radius=999,
                    gradient=ft.RadialGradient(
                        colors=[
                            "#243B63FF",
                            "#003B63FF",
                        ],
                    ),
                ),
                ft.Container(
                    left=330,
                    top=-80,
                    width=220,
                    height=150,
                    border_radius=999,
                    gradient=ft.RadialGradient(
                        colors=[
                            "#1FFFB36F",
                            "#00FFB36F",
                        ],
                    ),
                ),
            ],
        )

        return ft.Container(
            height=AppLayout.HEADER_HEIGHT,
            gradient=header_gradient(),
            border=ft.Border.only(
                bottom=ft.BorderSide(
                    1,
                    "#273047",
                ),
            ),
            shadow=ft.BoxShadow(
                blur_radius=24,
                spread_radius=-8,
                color="#66000000",
                offset=ft.Offset(0, 6),
            ),
            content=ft.Stack(
                expand=True,
                controls=[
                    background_fx,
                    ft.Container(
                        left=0,
                        right=0,
                        top=0,
                        height=1,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.CENTER_LEFT,
                            end=ft.Alignment.CENTER_RIGHT,
                            colors=[
                                "#001C2742",
                                "#446C7DFF",
                                "#446953B7",
                                "#001C2742",
                            ],
                        ),
                    ),
                    ft.Container(
                        left=0,
                        right=0,
                        top=0,
                        bottom=0,
                        padding=ft.Padding.symmetric(
                            horizontal=22,
                            vertical=9,
                        ),
                        content=main_row,
                    ),
                    ft.Container(
                        left=0,
                        right=0,
                        bottom=0,
                        height=1,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.CENTER_LEFT,
                            end=ft.Alignment.CENTER_RIGHT,
                            colors=[
                                "#0022D3EE",
                                "#4A22D3EE",
                                "#668B5CF6",
                                "#4AE9A5FF",
                                "#00E9A5FF",
                            ],
                        ),
                    ),
                ],
            ),
        )

    # =========================================================
    # ACTION BUTTON
    # =========================================================

    def _action_button(
        self,
        text,
        icon,
        handler,
        accent,
        fill_top,
        fill_bottom,
        border,
        primary=False,
    ):
        button = ft.Button(
            content=text,
            icon=icon,
            on_click=handler,
            bgcolor="#00000000",
            color="#F5F7FF",
            elevation=0,
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(
                    horizontal=15 if primary else 14,
                    vertical=11,
                ),
                shape=ft.RoundedRectangleBorder(
                    radius=12,
                ),
                side=ft.BorderSide(
                    0,
                    "#00000000",
                ),
            ),
        )

        shell = ft.Container(
            border_radius=13,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[
                    fill_top,
                    fill_bottom,
                ],
            ),
            border=ft.Border.all(
                1,
                border,
            ),
            animate_scale=ft.Animation(
                duration=160,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate=ft.Animation(
                duration=160,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            shadow=ft.BoxShadow(
                blur_radius=15 if primary else 12,
                spread_radius=-5,
                color=f"38{accent[1:]}",
            ),
            on_hover=self._hover_action_button,
            data={
                "accent": accent,
                "fill_top": fill_top,
                "fill_bottom": fill_bottom,
                "border": border,
                "primary": primary,
            },
            content=button,
        )

        return shell

    # =========================================================
    # HOVER HELPERS
    # =========================================================

    @staticmethod
    def _is_hovered(value):
        if isinstance(value, bool):
            return value

        return str(value).strip().lower() in {
            "true",
            "1",
            "yes",
        }

    def _hover_logo(self, e):
        hovered = self._is_hovered(e.data)

        if hovered:
            e.control.scale = 1.07
            e.control.shadow = ft.BoxShadow(
                blur_radius=34,
                spread_radius=-1,
                color="#665D4CFF",
            )
            e.control.border = ft.Border.all(
                1,
                "#777E75FF",
            )
        else:
            e.control.scale = 1.0
            e.control.shadow = ft.BoxShadow(
                blur_radius=26,
                spread_radius=-3,
                color="#553D54FF",
            )
            e.control.border = ft.Border.all(
                1,
                "#2B3D62",
            )

        e.control.update()

    def _hover_action_button(self, e):
        hovered = self._is_hovered(e.data)
        data = e.control.data

        accent = data["accent"]
        border = data["border"]
        primary = data["primary"]

        if hovered:
            e.control.scale = 1.025
            e.control.border = ft.Border.all(
                1,
                accent,
            )
            e.control.shadow = ft.BoxShadow(
                blur_radius=24 if primary else 20,
                spread_radius=-3,
                color=f"55{accent[1:]}",
            )
        else:
            e.control.scale = 1.0
            e.control.border = ft.Border.all(
                1,
                border,
            )
            e.control.shadow = ft.BoxShadow(
                blur_radius=15 if primary else 12,
                spread_radius=-5,
                color=f"38{accent[1:]}",
            )

        e.control.update()

    def _hover_reset(self, e):
        hovered = self._is_hovered(e.data)

        if hovered:
            e.control.scale = 1.06
            e.control.bgcolor = "#221326"
            e.control.border = ft.Border.all(
                1,
                "#684477",
            )
            e.control.shadow = ft.BoxShadow(
                blur_radius=20,
                spread_radius=-4,
                color="#445C2A73",
            )
            e.control.content.icon_color = "#D4AEFF"
        else:
            e.control.scale = 1.0
            e.control.bgcolor = "#0D1220"
            e.control.border = ft.Border.all(
                1,
                "#293148",
            )
            e.control.shadow = ft.BoxShadow(
                blur_radius=12,
                spread_radius=-6,
                color="#33111C3A",
            )
            e.control.content.icon_color = "#8E9AB6"

        e.control.update()

    # =========================================================
    # ACTIVE FEATURE
    # =========================================================

    def set_active_feature(
        self,
        feature_name,
    ):
        self.active_feature_text.value = feature_name
        self.active_feature_text.update()

    # =========================================================
    # HOME / WORKSPACE MODE
    # =========================================================

    def set_home_mode(
        self,
        is_home,
    ):
        self.save_button.visible = not is_home
        self.reset_shell.visible = not is_home

        self.save_button.update()
        self.reset_shell.update()
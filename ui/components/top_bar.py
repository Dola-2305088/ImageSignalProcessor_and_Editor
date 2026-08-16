import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
    app_logo_gradient,
    header_gradient,
)


class TopBar:
    def __init__(
        self,
        on_open_image,
        on_save_result,
        on_reset_result,
    ):
        self.on_open_image = on_open_image
        self.on_save_result = on_save_result
        self.on_reset_result = on_reset_result

        # =====================================================
        # CURRENT WORKSPACE
        # =====================================================

        self.active_feature_text = ft.Text(
            "Home",
            size=10,
            weight=ft.FontWeight.BOLD,
            color=AppColors.CYAN_LIGHT,
        )

        self.control = self._build()

    # =========================================================
    # BUILD TOP BAR
    # =========================================================

    def _build(self):

        # -----------------------------------------------------
        # APP LOGO
        # KEEPING YOUR EXISTING LOGO
        # -----------------------------------------------------

        self.logo_shell = ft.Container(
            width=48,
            height=48,
            border_radius=16,
            gradient=app_logo_gradient(),
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(
                blur_radius=18,
                spread_radius=0,
                color="#3522D3EE",
            ),
            animate_scale=ft.Animation(
                duration=180,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            on_hover=self._hover_logo,
            content=ft.Icon(
                ft.Icons.IMAGE,
                color=AppColors.BLACK,
                size=26,
            ),
        )

        # -----------------------------------------------------
        # ACTIVE FEATURE PILL
        # -----------------------------------------------------

        self.feature_pill = ft.Container(
            padding=ft.Padding.symmetric(
                horizontal=11,
                vertical=5,
            ),
            border_radius=100,
            bgcolor="#0B1C2B",
            border=ft.Border.all(
                1,
                "#244764",
            ),
            shadow=ft.BoxShadow(
                blur_radius=12,
                color="#1622D3EE",
            ),
            content=ft.Row(
                tight=True,
                spacing=6,
                controls=[
                    ft.Container(
                        width=6,
                        height=6,
                        border_radius=100,
                        bgcolor=AppColors.CYAN,
                        shadow=ft.BoxShadow(
                            blur_radius=8,
                            color="#6622D3EE",
                        ),
                    ),
                    self.active_feature_text,
                ],
            ),
        )

        # -----------------------------------------------------
        # BRAND AREA
        # -----------------------------------------------------

        brand_area = ft.Row(
            spacing=13,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.logo_shell,

                ft.Column(
                    spacing=3,
                    controls=[
                        ft.Text(
                            "Image Signal Processor",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.TEXT,
                        ),

                        ft.Row(
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(
                                    "CSE 220 Signal Lab",
                                    size=9,
                                    weight=ft.FontWeight.W_500,
                                    color=AppColors.MUTED,
                                ),

                                ft.Container(
                                    width=3,
                                    height=3,
                                    border_radius=100,
                                    bgcolor=AppColors.MUTED_DARK,
                                ),

                                self.feature_pill,
                            ],
                        ),
                    ],
                ),
            ],
        )

        # -----------------------------------------------------
        # OPEN BUTTON
        # -----------------------------------------------------

        self.open_button = self._action_button(
            text="Open Image",
            icon=ft.Icons.FOLDER_OPEN,
            handler=self.on_open_image,
            accent=AppColors.BLUE,
            dark_bg="#13284A",
            border="#265BA5",
        )

        # -----------------------------------------------------
        # SAVE BUTTON
        # -----------------------------------------------------

        self.save_button = self._action_button(
            text="Save Result",
            icon=ft.Icons.DOWNLOAD,
            handler=self.on_save_result,
            accent=AppColors.GREEN,
            dark_bg="#0D2D25",
            border="#176349",
        )

        self.save_button.visible = False

        # -----------------------------------------------------
        # RESET BUTTON
        # -----------------------------------------------------

        self.reset_shell = ft.Container(
            width=42,
            height=42,
            alignment=ft.Alignment.CENTER,
            border_radius=13,
            bgcolor="#111827",
            border=ft.Border.all(
                1,
                AppColors.BORDER,
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
            content=ft.IconButton(
                icon=ft.Icons.RESTART_ALT,
                icon_color=AppColors.MUTED,
                icon_size=20,
                tooltip="Reset processed result",
                on_click=self.on_reset_result,
            ),
        )

        # Maintain old public reference if anything uses it
        self.reset_button = self.reset_shell

        # -----------------------------------------------------
        # SYSTEM STATUS
        # -----------------------------------------------------

        self.status_badge = ft.Container(
            padding=ft.Padding.symmetric(
                horizontal=10,
                vertical=7,
            ),
            border_radius=100,
            bgcolor="#091B17",
            border=ft.Border.all(
                1,
                "#164738",
            ),
            content=ft.Row(
                tight=True,
                spacing=6,
                controls=[
                    ft.Container(
                        width=7,
                        height=7,
                        border_radius=100,
                        bgcolor=AppColors.GREEN,
                        shadow=ft.BoxShadow(
                            blur_radius=8,
                            color="#6634D399",
                        ),
                    ),

                    ft.Text(
                        "LAB ONLINE",
                        size=8,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.GREEN_LIGHT,
                    ),
                ],
            ),
        )

        # -----------------------------------------------------
        # ACTION AREA
        # -----------------------------------------------------

        action_area = ft.Row(
            spacing=9,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.status_badge,

                ft.Container(
                    width=1,
                    height=30,
                    bgcolor=AppColors.BORDER,
                    margin=ft.Margin.symmetric(
                        horizontal=4,
                    ),
                ),

                self.open_button,
                self.save_button,
                self.reset_shell,
            ],
        )

        # -----------------------------------------------------
        # MAIN BAR CONTENT
        # -----------------------------------------------------

        main_row = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                brand_area,

                ft.Container(
                    expand=True,
                ),

                action_area,
            ],
        )

        # -----------------------------------------------------
        # TOP BAR WITH SUBTLE GLOW / ACCENT LINE
        # -----------------------------------------------------

        return ft.Container(
            height=AppLayout.HEADER_HEIGHT,
            gradient=header_gradient(),
            border=ft.Border.only(
                bottom=ft.BorderSide(
                    1,
                    AppColors.BORDER,
                ),
            ),
            shadow=ft.BoxShadow(
                blur_radius=18,
                spread_radius=0,
                color="#20000000",
                offset=ft.Offset(
                    0,
                    5,
                ),
            ),
            content=ft.Stack(
                expand=True,
                controls=[
                    # -----------------------------------------
                    # MAIN CONTENT
                    # -----------------------------------------

                    ft.Container(
                        left=0,
                        right=0,
                        top=0,
                        bottom=0,
                        padding=ft.Padding.symmetric(
                            horizontal=22,
                            vertical=10,
                        ),
                        content=main_row,
                    ),

                    # -----------------------------------------
                    # BOTTOM CYAN / PURPLE ACCENT
                    # -----------------------------------------

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
                                "#5522D3EE",
                                "#558B5CF6",
                                "#00EC4899",
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
        dark_bg,
        border,
    ):

        button = ft.Button(
            content=text,
            icon=icon,
            on_click=handler,
            bgcolor=dark_bg,
            color=AppColors.WHITE,
            elevation=0,
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(
                    horizontal=17,
                    vertical=12,
                ),
                shape=ft.RoundedRectangleBorder(
                    radius=12,
                ),
                side=ft.BorderSide(
                    1,
                    border,
                ),
            ),
        )

        shell = ft.Container(
            border_radius=12,
            animate_scale=ft.Animation(
                duration=160,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            shadow=ft.BoxShadow(
                blur_radius=12,
                spread_radius=0,
                color=f"20{accent[1:]}",
            ),
            on_hover=self._hover_action_button,
            data={
                "accent": accent,
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

    # ---------------------------------------------------------
    # LOGO HOVER
    # ---------------------------------------------------------

    def _hover_logo(self, e):

        hovered = self._is_hovered(
            e.data
        )

        if hovered:

            e.control.scale = 1.08

            e.control.shadow = ft.BoxShadow(
                blur_radius=28,
                spread_radius=1,
                color="#5522D3EE",
            )

        else:

            e.control.scale = 1.0

            e.control.shadow = ft.BoxShadow(
                blur_radius=18,
                spread_radius=0,
                color="#3522D3EE",
            )

        e.control.update()

    # ---------------------------------------------------------
    # ACTION BUTTON HOVER
    # ---------------------------------------------------------

    def _hover_action_button(self, e):

        hovered = self._is_hovered(
            e.data
        )

        accent = (
            e.control
            .data["accent"]
        )

        if hovered:

            e.control.scale = 1.035

            e.control.shadow = ft.BoxShadow(
                blur_radius=22,
                spread_radius=1,
                color=f"42{accent[1:]}",
            )

        else:

            e.control.scale = 1.0

            e.control.shadow = ft.BoxShadow(
                blur_radius=12,
                spread_radius=0,
                color=f"20{accent[1:]}",
            )

        e.control.update()

    # ---------------------------------------------------------
    # RESET HOVER
    # ---------------------------------------------------------

    def _hover_reset(self, e):

        hovered = self._is_hovered(
            e.data
        )

        if hovered:

            e.control.scale = 1.08

            e.control.bgcolor = "#26151C"

            e.control.border = ft.Border.all(
                1,
                "#713342",
            )

            e.control.content.icon_color = (
                AppColors.PINK
            )

        else:

            e.control.scale = 1.0

            e.control.bgcolor = "#111827"

            e.control.border = ft.Border.all(
                1,
                AppColors.BORDER,
            )

            e.control.content.icon_color = (
                AppColors.MUTED
            )

        e.control.update()

    # =========================================================
    # ACTIVE FEATURE
    # =========================================================

    def set_active_feature(
        self,
        feature_name,
    ):

        self.active_feature_text.value = (
            feature_name
        )

        self.active_feature_text.update()

    # =========================================================
    # HOME / WORKSPACE MODE
    # =========================================================

    def set_home_mode(
        self,
        is_home,
    ):

        self.save_button.visible = (
            not is_home
        )

        self.reset_shell.visible = (
            not is_home
        )

        self.save_button.update()

        self.reset_shell.update()
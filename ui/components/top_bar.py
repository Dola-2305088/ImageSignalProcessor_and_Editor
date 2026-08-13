import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    app_logo_gradient,
    header_gradient,
)


class TopBar:
    """
    Reusable application header.

    Contains:
    - Sidebar toggle button
    - App logo
    - App title
    - Current feature name
    - Open Image button
    - Save Result button
    - Reset Result button
    """

    def __init__(
        self,
        on_toggle_sidebar,
        on_open_image,
        on_save_result,
        on_reset_result,
    ):

        # =====================================================
        # CALLBACKS FROM MAIN WINDOW
        # =====================================================

        self.on_toggle_sidebar = on_toggle_sidebar

        self.on_open_image = on_open_image

        self.on_save_result = on_save_result

        self.on_reset_result = on_reset_result


        # =====================================================
        # CURRENT FEATURE TEXT
        # =====================================================

        self.active_feature_text = ft.Text(
            "General",
            size=13,
            weight=ft.FontWeight.W_600,
            color=AppColors.CYAN,
        )


        # =====================================================
        # BUILD COMPONENT
        # =====================================================

        self.control = self._build()


    # =========================================================
    # BUILD TOP BAR
    # =========================================================

    def _build(self):

        return ft.Container(

            height=AppLayout.HEADER_HEIGHT,

            padding=ft.Padding.symmetric(
                horizontal=22,
                vertical=12,
            ),

            gradient=header_gradient(),

            border=ft.Border.only(
                bottom=ft.BorderSide(
                    1,
                    AppColors.BORDER,
                )
            ),

            content=ft.Row(

                vertical_alignment=ft.CrossAxisAlignment.CENTER,

                controls=[

                    # =========================================
                    # SIDEBAR BUTTON
                    # =========================================

                    ft.IconButton(
                        icon=ft.Icons.MENU,
                        icon_color=AppColors.TEXT,
                        tooltip="Collapse / expand sidebar",
                        on_click=self.on_toggle_sidebar,
                    ),


                    # =========================================
                    # APP LOGO
                    # =========================================

                    ft.Container(
                        width=46,
                        height=46,

                        border_radius=ft.BorderRadius.all(
                            15
                        ),

                        gradient=app_logo_gradient(),

                        alignment=ft.Alignment.CENTER,

                        content=ft.Icon(
                            ft.Icons.IMAGE,
                            color=AppColors.BLACK,
                            size=26,
                        ),
                    ),


                    # =========================================
                    # TITLE AREA
                    # =========================================

                    ft.Column(

                        spacing=1,

                        expand=True,

                        controls=[

                            ft.Text(
                                "Image Signal Processor",
                                size=21,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),


                            ft.Row(

                                spacing=8,

                                controls=[

                                    ft.Text(
                                        "CSE 220 Signal Lab",
                                        size=11,
                                        color=AppColors.MUTED,
                                    ),


                                    ft.Text(
                                        "•",
                                        color=AppColors.MUTED_DARK,
                                    ),


                                    self.active_feature_text,
                                ],
                            ),
                        ],
                    ),


                    # =========================================
                    # OPEN IMAGE
                    # =========================================

                    self._action_button(
                        text="Open Image",
                        icon=ft.Icons.FOLDER_OPEN,
                        handler=self.on_open_image,
                        color=AppColors.BLUE,
                    ),


                    # =========================================
                    # SAVE RESULT
                    # =========================================

                    self._action_button(
                        text="Save Result",
                        icon=ft.Icons.DOWNLOAD,
                        handler=self.on_save_result,
                        color=AppColors.GREEN,
                    ),


                    # =========================================
                    # RESET
                    # =========================================

                    ft.IconButton(
                        icon=ft.Icons.RESTART_ALT,
                        icon_color=AppColors.MUTED,
                        tooltip="Reset processed result",
                        on_click=self.on_reset_result,
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
        color,
    ):

        return ft.Button(

            content=text,

            icon=icon,

            on_click=handler,

            bgcolor=color,

            color=AppColors.WHITE,

            elevation=0,
        )


    # =========================================================
    # CHANGE CURRENT FEATURE
    # =========================================================

    def set_active_feature(
        self,
        feature_name,
    ):

        self.active_feature_text.value = (
            feature_name
        )

        self.active_feature_text.update()
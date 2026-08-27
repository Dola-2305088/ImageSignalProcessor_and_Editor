import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
)


class StatusBar:
    """
    Bottom application status bar.

    Displays:
    - Busy spinner
    - Current status message
    - Application mode label

    Examples:
        Ready

        Computing manual 2D DFT...

        Compression complete.

        Spatial + Frequency Domain
    """

    def __init__(
        self,
        initial_text="Ready",
        mode_text="Spatial + Frequency Domain",
    ):

        # =====================================================
        # STATE
        # =====================================================

        self.current_text = initial_text

        self.mode_text = mode_text


        # =====================================================
        # BUSY SPINNER
        # =====================================================

        self.busy_ring = ft.ProgressRing(
            width=18,
            height=18,
            stroke_width=2,
            color=AppColors.CYAN,
            visible=False,
        )


        # =====================================================
        # STATUS MESSAGE
        # =====================================================

        self.status_text = ft.Text(
            initial_text,
            size=12,
            color=AppColors.MUTED,
            expand=True,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )


        # =====================================================
        # MODE LABEL
        # =====================================================

        self.mode_label = ft.Text(
            mode_text,
            size=11,
            color=AppColors.MUTED_2,
        )


        # =====================================================
        # STATUS DOT
        # =====================================================

        self.status_dot = ft.Container(
            width=8,
            height=8,
            bgcolor=AppColors.GREEN,
            border_radius=ft.BorderRadius.all(100),
        )


        # =====================================================
        # BUILD CONTROL
        # =====================================================

        self.control = self._build()


    # =========================================================
    # BUILD STATUS BAR
    # =========================================================

    def _build(self):

        return ft.Container(

            height=AppLayout.STATUS_BAR_HEIGHT,

            bgcolor="#090E17",

            border=ft.Border.only(
                top=ft.BorderSide(
                    1,
                    AppColors.BORDER,
                )
            ),

            padding=ft.Padding.symmetric(
                horizontal=20
            ),

            content=ft.Row(

                vertical_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                spacing=10,

                controls=[

                    # =========================================
                    # STATUS DOT
                    # =========================================

                    self.status_dot,


                    # =========================================
                    # BUSY SPINNER
                    # =========================================

                    self.busy_ring,


                    # =========================================
                    # CURRENT STATUS
                    # =========================================

                    self.status_text,


                    # =========================================
                    # MODE
                    # =========================================

                    ft.Row(

                        spacing=7,

                        controls=[

                            ft.Icon(
                                ft.Icons.WAVES,
                                size=14,
                                color=AppColors.MUTED_2,
                            ),

                            self.mode_label,
                        ],
                    ),
                ],
            ),
        )


    # =========================================================
    # SET STATUS TEXT
    # =========================================================

    def set_status(
        self,
        text,
    ):

        self.current_text = text

        self.status_text.value = text

        self.status_text.update()


    # =========================================================
    # SET BUSY
    # =========================================================

    def set_busy(
        self,
        busy,
        text=None,
    ):

        self.busy_ring.visible = busy


        # =====================================================
        # BUSY APPEARANCE
        # =====================================================

        if busy:

            self.status_dot.bgcolor = (
                AppColors.ORANGE
            )


            if text:

                self.current_text = text

                self.status_text.value = text


        # =====================================================
        # READY APPEARANCE
        # =====================================================

        else:

            self.status_dot.bgcolor = (
                AppColors.GREEN
            )


            if text:

                self.current_text = text

                self.status_text.value = text


        self.busy_ring.update()

        self.status_dot.update()

        self.status_text.update()


    # =========================================================
    # SUCCESS STATUS
    # =========================================================

    def show_success(
        self,
        text,
    ):

        self.current_text = text

        self.busy_ring.visible = False

        self.status_dot.bgcolor = (
            AppColors.GREEN
        )

        self.status_text.value = text


        self.busy_ring.update()

        self.status_dot.update()

        self.status_text.update()


    # =========================================================
    # WARNING STATUS
    # =========================================================

    def show_warning(
        self,
        text,
    ):

        self.current_text = text

        self.busy_ring.visible = False

        self.status_dot.bgcolor = (
            AppColors.ORANGE
        )

        self.status_text.value = text


        self.busy_ring.update()

        self.status_dot.update()

        self.status_text.update()


    # =========================================================
    # ERROR STATUS
    # =========================================================

    def show_error(
        self,
        text,
    ):

        self.current_text = text

        self.busy_ring.visible = False

        self.status_dot.bgcolor = (
            AppColors.RED
        )

        self.status_text.value = text


        self.busy_ring.update()

        self.status_dot.update()

        self.status_text.update()


    # =========================================================
    # RESET TO READY
    # =========================================================

    def reset(
        self,
    ):

        self.current_text = "Ready"

        self.busy_ring.visible = False

        self.status_dot.bgcolor = (
            AppColors.GREEN
        )

        self.status_text.value = (
            "Ready"
        )


        self.busy_ring.update()

        self.status_dot.update()

        self.status_text.update()


    # =========================================================
    # SET MODE TEXT
    # =========================================================

    def set_mode(
        self,
        text,
    ):

        self.mode_text = text

        self.mode_label.value = text

        self.mode_label.update()
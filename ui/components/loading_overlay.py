import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
)


class LoadingOverlay:
    """
    Full-area loading overlay.

    Intended for slower operations such as:
    - Manual 2D DFT
    - IDFT reconstruction
    - Compression analysis
    - Texture analysis
    - Hybrid image creation
    - RGB frequency analysis

    The overlay sits above the workspace while an operation runs.
    """

    def __init__(self):

        # =====================================================
        # STATE
        # =====================================================

        self.visible = False


        # =====================================================
        # MAIN TITLE
        # =====================================================

        self.title_text = ft.Text(
            "Processing image...",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
            text_align=ft.TextAlign.CENTER,
        )


        # =====================================================
        # SUBTITLE
        # =====================================================

        self.subtitle_text = ft.Text(
            "Please wait while the signal-processing operation completes.",
            size=11,
            color=AppColors.MUTED,
            text_align=ft.TextAlign.CENTER,
        )


        # =====================================================
        # EXTRA DETAIL
        # =====================================================

        self.detail_text = ft.Text(
            "",
            size=10,
            color=AppColors.MUTED_2,
            text_align=ft.TextAlign.CENTER,
        )


        # =====================================================
        # SPINNER
        # =====================================================

        self.progress_ring = ft.ProgressRing(
            width=54,
            height=54,
            stroke_width=4,
            color=AppColors.CYAN,
        )


        # =====================================================
        # PROCESSING CARD
        # =====================================================

        self.processing_card = ft.Container(

            width=430,

            padding=ft.Padding.symmetric(
                horizontal=34,
                vertical=30,
            ),

            bgcolor=AppColors.SURFACE,

            border=ft.Border.all(
                1,
                AppColors.BORDER_LIGHT,
            ),

            border_radius=ft.BorderRadius.all(
                AppLayout.CARD_RADIUS
            ),

            shadow=ft.BoxShadow(
                blur_radius=30,
                spread_radius=2,
                color="#66000000",
                offset=ft.Offset(0, 10),
            ),

            content=ft.Column(

                tight=True,

                spacing=16,

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                controls=[

                    # =========================================
                    # ICON AREA
                    # =========================================

                    ft.Container(

                        width=82,
                        height=82,

                        alignment=ft.Alignment.CENTER,

                        border_radius=ft.BorderRadius.all(
                            24
                        ),

                        gradient=ft.LinearGradient(

                            begin=ft.Alignment.TOP_LEFT,

                            end=ft.Alignment.BOTTOM_RIGHT,

                            colors=[
                                "#142A38",
                                "#211A42",
                            ],
                        ),

                        content=self.progress_ring,
                    ),


                    # =========================================
                    # TEXT
                    # =========================================

                    self.title_text,

                    self.subtitle_text,

                    self.detail_text,


                    # =========================================
                    # SMALL DECORATIVE LINE
                    # =========================================

                    ft.Container(

                        width=100,
                        height=3,

                        border_radius=3,

                        gradient=ft.LinearGradient(

                            begin=ft.Alignment.CENTER_LEFT,

                            end=ft.Alignment.CENTER_RIGHT,

                            colors=[
                                AppColors.CYAN,
                                AppColors.PURPLE,
                            ],
                        ),
                    ),
                ],
            ),
        )


        # =====================================================
        # BACKDROP
        # =====================================================

        self.backdrop = ft.Container(

            expand=True,

            alignment=ft.Alignment.CENTER,

            bgcolor="#B3080B12",

            content=self.processing_card,

            opacity=0,

            animate_opacity=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            visible=False,
        )


        # =====================================================
        # EXPOSED CONTROL
        # =====================================================

        self.control = self.backdrop


    # =========================================================
    # SHOW OVERLAY
    # =========================================================

    def show(
        self,
        title="Processing image...",
        subtitle=None,
        detail=None,
        accent=None,
    ):

        self.visible = True


        # =====================================================
        # TEXT
        # =====================================================

        self.title_text.value = title


        if subtitle is None:

            subtitle = (
                "Please wait while the signal-processing "
                "operation completes."
            )


        self.subtitle_text.value = subtitle


        self.detail_text.value = (
            detail
            if detail
            else ""
        )


        # =====================================================
        # COLOR
        # =====================================================

        if accent is not None:

            self.progress_ring.color = accent

        else:

            self.progress_ring.color = (
                AppColors.CYAN
            )


        # =====================================================
        # SHOW
        # =====================================================

        self.backdrop.visible = True

        self.backdrop.opacity = 1


        self.title_text.update()

        self.subtitle_text.update()

        self.detail_text.update()

        self.progress_ring.update()

        self.backdrop.update()


    # =========================================================
    # HIDE OVERLAY
    # =========================================================

    def hide(self):

        self.visible = False


        # Start fade-out.
        self.backdrop.opacity = 0

        self.backdrop.update()


        # We keep visible=True here during the fade.
        #
        # main_window.py can call:
        #
        #     self.loading_overlay.finish_hide()
        #
        # shortly afterwards if desired.
        #
        # Or you can simply use hide_immediately()
        # when you don't need a delayed fade.


    # =========================================================
    # FINISH HIDE
    # =========================================================

    def finish_hide(self):

        self.backdrop.visible = False

        self.backdrop.update()


    # =========================================================
    # HIDE IMMEDIATELY
    # =========================================================

    def hide_immediately(self):

        self.visible = False

        self.backdrop.opacity = 0

        self.backdrop.visible = False

        self.backdrop.update()


    # =========================================================
    # UPDATE MESSAGE
    # =========================================================

    def update_message(
        self,
        title=None,
        subtitle=None,
        detail=None,
    ):

        if title is not None:

            self.title_text.value = title


        if subtitle is not None:

            self.subtitle_text.value = (
                subtitle
            )


        if detail is not None:

            self.detail_text.value = (
                detail
            )


        self.title_text.update()

        self.subtitle_text.update()

        self.detail_text.update()


    # =========================================================
    # COMMON PRESETS
    # =========================================================

    def show_dft(self):

        self.show(

            title="Computing 2D DFT",

            subtitle=(
                "Transforming the image from the "
                "spatial domain into the frequency domain."
            ),

            detail=(
                "Manual 2D Fourier Transform • 128 × 128"
            ),

            accent=AppColors.CYAN,
        )


    def show_compression(self):

        self.show(

            title="Compressing Frequency Data",

            subtitle=(
                "Keeping the strongest DFT coefficients "
                "and reconstructing the image."
            ),

            detail=(
                "Calculating reconstruction quality and PSNR"
            ),

            accent=AppColors.GREEN,
        )


    def show_texture(self):

        self.show(

            title="Analyzing Texture",

            subtitle=(
                "Searching the frequency spectrum for "
                "dominant repetition and orientation."
            ),

            detail=(
                "Frequency-domain texture analysis"
            ),

            accent=AppColors.ORANGE,
        )


    def show_hybrid(self):

        self.show(

            title="Creating Hybrid Image",

            subtitle=(
                "Combining low-frequency structure from "
                "Image A with high-frequency detail from Image B."
            ),

            detail=(
                "Processing two frequency-domain images"
            ),

            accent=AppColors.PINK,
        )


    def show_color_frequency(self):

        self.show(

            title="Analyzing RGB Frequencies",

            subtitle=(
                "Computing the 2D frequency spectrum "
                "for the red, green, and blue channels."
            ),

            detail=(
                "Three manual channel transforms"
            ),

            accent=AppColors.PURPLE,
        )
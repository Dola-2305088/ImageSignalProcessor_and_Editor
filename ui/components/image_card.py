import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
)


class ImageCard:
    """
    Reusable image/result display card.

    Can be used for:
    - Original image
    - Processed image
    - DFT spectrum
    - Compression result
    - Texture spectrum
    - Hybrid result
    - Graphs
    - Color analysis results
    """

    def __init__(
        self,
        title,
        subtitle="",
        accent=None,
        placeholder_icon=ft.Icons.IMAGE_OUTLINED,
        placeholder_title="No image",
        placeholder_subtitle="Nothing to display",
    ):

        # =====================================================
        # COLORS / CONFIGURATION
        # =====================================================

        self.accent = (
            accent
            or AppColors.CYAN
        )


        # =====================================================
        # TITLE
        # =====================================================

        self.title_text = ft.Text(
            title,
            size=15,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
        )


        # =====================================================
        # SUBTITLE
        # =====================================================

        self.subtitle_text = ft.Text(
            subtitle,
            size=11,
            color=AppColors.MUTED,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )


        # =====================================================
        # PLACEHOLDER
        # =====================================================

        self.placeholder_icon = (
            placeholder_icon
        )

        self.placeholder_title = (
            placeholder_title
        )

        self.placeholder_subtitle = (
            placeholder_subtitle
        )


        # =====================================================
        # ANIMATED CONTENT AREA
        # =====================================================

        self.switcher = ft.AnimatedSwitcher(

            content=self._create_placeholder(),

            transition=(
                ft.AnimatedSwitcherTransition.FADE
            ),

            duration=AppAnimations.MEDIUM,

            reverse_duration=(
                AppAnimations.FAST
            ),

            switch_in_curve=(
                ft.AnimationCurve.EASE_OUT
            ),

            switch_out_curve=(
                ft.AnimationCurve.EASE_IN
            ),
        )


        # =====================================================
        # BUILD CARD
        # =====================================================

        self.control = self._build()


    # =========================================================
    # BUILD COMPLETE CARD
    # =========================================================

    def _build(self):

        self.preview_container = ft.Container(

            expand=True,

            alignment=ft.Alignment.CENTER,

            bgcolor=AppColors.SURFACE_DARK,

            border=ft.Border.all(
                1,
                AppColors.BORDER_SOFT,
            ),

            border_radius=ft.BorderRadius.all(
                AppLayout.INNER_RADIUS
            ),

            padding=10,

            content=self.switcher,
        )


        self.card = ft.Container(

            expand=True,

            height=(
                AppLayout.IMAGE_CARD_HEIGHT
            ),

            bgcolor=AppColors.SURFACE,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                AppLayout.CARD_RADIUS
            ),

            padding=14,

            # Smooth card movement when hovered.
            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._on_hover,

            content=ft.Column(

                spacing=10,

                controls=[

                    # =========================================
                    # CARD HEADER
                    # =========================================

                    ft.Row(

                        vertical_alignment=(
                            ft.CrossAxisAlignment.CENTER
                        ),

                        controls=[

                            # Accent line
                            ft.Container(
                                width=8,
                                height=32,
                                bgcolor=self.accent,
                                border_radius=(
                                    ft.BorderRadius.all(8)
                                ),
                            ),


                            # Title / subtitle
                            ft.Column(

                                spacing=1,

                                expand=True,

                                controls=[
                                    self.title_text,
                                    self.subtitle_text,
                                ],
                            ),


                            # Decorative status icon
                            ft.Container(

                                width=34,
                                height=34,

                                alignment=(
                                    ft.Alignment.CENTER
                                ),

                                bgcolor=(
                                    AppColors.SURFACE_2
                                ),

                                border_radius=(
                                    ft.BorderRadius.all(10)
                                ),

                                content=ft.Icon(
                                    ft.Icons.IMAGE_OUTLINED,
                                    size=18,
                                    color=self.accent,
                                ),
                            ),
                        ],
                    ),


                    # =========================================
                    # IMAGE / RESULT AREA
                    # =========================================

                    self.preview_container,
                ],
            ),
        )


        return self.card


    # =========================================================
    # PLACEHOLDER
    # =========================================================

    def _create_placeholder(self):

        return ft.Container(

            alignment=ft.Alignment.CENTER,

            content=ft.Column(

                tight=True,

                spacing=8,

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                controls=[

                    ft.Icon(
                        self.placeholder_icon,
                        size=46,
                        color="#3A4A63",
                    ),


                    ft.Text(
                        self.placeholder_title,
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=AppColors.MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),


                    ft.Text(
                        self.placeholder_subtitle,
                        size=11,
                        color="#5E718C",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )


    # =========================================================
    # HOVER ANIMATION
    # =========================================================

    def _on_hover(self, e):

        # Slight enlargement only.
        # Keeps animation professional instead of excessive.

        e.control.scale = (
            1.008
            if e.data
            else 1.0
        )

        e.control.update()


    # =========================================================
    # DISPLAY IMAGE FROM BYTES
    # =========================================================

    def set_image_bytes(
        self,
        image_bytes,
        title=None,
        subtitle=None,
    ):

        image_control = ft.Image(

            src=image_bytes,

            width=(
                AppLayout
                .IMAGE_PREVIEW_WIDTH
            ),

            height=(
                AppLayout
                .IMAGE_PREVIEW_HEIGHT
            ),

            fit=ft.BoxFit.CONTAIN,

            filter_quality=(
                ft.FilterQuality.HIGH
            ),

            border_radius=(
                ft.BorderRadius.all(12)
            ),

            gapless_playback=True,

            fade_in_animation=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=(
                    ft.AnimationCurve
                    .EASE_IN_OUT
                ),
            ),
        )


        self.set_content(
            image_control,
            title=title,
            subtitle=subtitle,
        )


    # =========================================================
    # DISPLAY ANY FLET CONTROL
    # =========================================================

    def set_content(
        self,
        control,
        title=None,
        subtitle=None,
    ):

        if title is not None:

            self.title_text.value = title


        if subtitle is not None:

            self.subtitle_text.value = (
                subtitle
            )


        self.switcher.content = control


        self.title_text.update()

        self.subtitle_text.update()

        self.switcher.update()


    # =========================================================
    # CHANGE TITLE
    # =========================================================

    def set_title(
        self,
        title,
    ):

        self.title_text.value = title

        self.title_text.update()


    # =========================================================
    # CHANGE SUBTITLE
    # =========================================================

    def set_subtitle(
        self,
        subtitle,
    ):

        self.subtitle_text.value = (
            subtitle
        )

        self.subtitle_text.update()


    # =========================================================
    # RESET CARD
    # =========================================================

    def reset(
        self,
        title=None,
        subtitle=None,
        placeholder_title=None,
        placeholder_subtitle=None,
    ):

        if title is not None:

            self.title_text.value = title


        if subtitle is not None:

            self.subtitle_text.value = (
                subtitle
            )


        if placeholder_title is not None:

            self.placeholder_title = (
                placeholder_title
            )


        if placeholder_subtitle is not None:

            self.placeholder_subtitle = (
                placeholder_subtitle
            )


        self.switcher.content = (
            self._create_placeholder()
        )


        self.title_text.update()

        self.subtitle_text.update()

        self.switcher.update()
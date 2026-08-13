import asyncio

import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
)


class HomeView:
    """
    Signal Studio landing / general workspace.

    Responsibilities:
    - Welcome screen
    - Open image
    - Grayscale quick action
    - Fast navigation to important features
    - Project capability summary
    - Premium animated visual identity

    This view does NOT contain signal-processing logic.
    It only sends actions back to main_window.py.
    """

    def __init__(
        self,
        on_open_image,
        on_grayscale,
        on_navigate,
    ):

        # =====================================================
        # CALLBACKS
        # =====================================================

        self.on_open_image = on_open_image

        self.on_grayscale = on_grayscale

        # Expected form:
        #
        # on_navigate(index)
        #
        # 0 = Home / General
        # 1 = Frequency
        # 2 = Compression
        # 3 = Texture
        # 4 = Hybrid
        # 5 = Color

        self.on_navigate = on_navigate


        # =====================================================
        # ANIMATION STATE
        # =====================================================

        self._ambient_running = False

        self._pulse_large = False


        # =====================================================
        # BUILD
        # =====================================================

        self.control = self._build()


    # =========================================================
    # MAIN BUILD
    # =========================================================

    def _build(self):

        return ft.Column(

            spacing=18,

            controls=[

                # =================================================
                # HERO AREA
                # =================================================

                self._build_hero(),


                # =================================================
                # QUICK ACTIONS
                # =================================================

                self._build_quick_actions(),


                # =================================================
                # CAPABILITY STRIP
                # =================================================

                self._build_capability_strip(),
            ],
        )


    # =========================================================
    # HERO
    # =========================================================

    def _build_hero(self):

        # -----------------------------------------------------
        # Status badge
        # -----------------------------------------------------

        status_badge = ft.Container(

            padding=ft.Padding.symmetric(
                horizontal=12,
                vertical=7,
            ),

            bgcolor="#0B1D1A",

            border=ft.Border.all(
                1,
                "#17483D",
            ),

            border_radius=100,

            content=ft.Row(

                tight=True,

                spacing=7,

                controls=[

                    ft.Container(
                        width=8,
                        height=8,
                        bgcolor=AppColors.GREEN,
                        border_radius=100,
                    ),

                    ft.Text(
                        "SYSTEM READY",
                        size=9,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.GREEN_LIGHT,
                    ),
                ],
            ),
        )


        # -----------------------------------------------------
        # Hero title
        # -----------------------------------------------------

        hero_title = ft.Text(
            "Turn pixels into signals.\nTurn signals into insight.",
            size=35,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
            height=1.12,
        )


        # -----------------------------------------------------
        # Accent sentence
        # -----------------------------------------------------

        hero_description = ft.Text(
            (
                "A modern signal-processing workspace for spatial filtering, "
                "Fourier analysis, image compression, texture intelligence, "
                "restoration and color-space exploration."
            ),
            size=13,
            color=AppColors.MUTED,
            height=1.55,
        )


        # -----------------------------------------------------
        # Main buttons
        # -----------------------------------------------------

        open_button = self._primary_button(
            text="Open Image",
            icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
            handler=self.on_open_image,
            color=AppColors.BLUE,
        )


        frequency_button = self._secondary_button(
            text="Explore Frequency",
            icon=ft.Icons.WAVES,
            handler=lambda e: self._navigate(1),
            accent=AppColors.CYAN,
        )


        # -----------------------------------------------------
        # Text side
        # -----------------------------------------------------

        left = ft.Column(

            expand=True,

            spacing=17,

            alignment=ft.MainAxisAlignment.CENTER,

            controls=[

                ft.Row(
                    controls=[status_badge]
                ),

                ft.Text(
                    "SIGNAL STUDIO",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=AppColors.CYAN,
                ),

                hero_title,

                ft.Container(
                    width=80,
                    height=4,
                    border_radius=4,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment.CENTER_LEFT,
                        end=ft.Alignment.CENTER_RIGHT,
                        colors=[
                            AppColors.CYAN,
                            AppColors.PURPLE,
                            AppColors.PINK,
                        ],
                    ),
                ),

                hero_description,

                ft.Row(
                    wrap=True,
                    spacing=10,
                    controls=[
                        open_button,
                        frequency_button,
                    ],
                ),
            ],
        )


        # -----------------------------------------------------
        # Signal visualization
        # -----------------------------------------------------

        right = self._build_signal_visual()


        # -----------------------------------------------------
        # Hero card
        # -----------------------------------------------------

        self.hero_card = ft.Container(

            height=330,

            padding=ft.Padding.symmetric(
                horizontal=32,
                vertical=30,
            ),

            border_radius=ft.BorderRadius.all(
                24
            ),

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            gradient=ft.LinearGradient(

                begin=ft.Alignment.TOP_LEFT,

                end=ft.Alignment.BOTTOM_RIGHT,

                colors=[
                    "#0E1728",
                    "#0C1322",
                    "#151127",
                ],
            ),

            shadow=ft.BoxShadow(
                blur_radius=32,
                spread_radius=0,
                color="#30000000",
                offset=ft.Offset(0, 14),
            ),

            content=ft.Row(

                spacing=30,

                vertical_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                controls=[
                    left,
                    right,
                ],
            ),
        )


        return self.hero_card


    # =========================================================
    # SIGNAL VISUALIZATION
    # =========================================================

    def _build_signal_visual(self):

        # =====================================================
        # OUTER ORBIT
        # =====================================================

        self.outer_orbit = ft.Container(

            width=260,
            height=260,

            alignment=ft.Alignment.CENTER,

            border_radius=130,

            border=ft.Border.all(
                1,
                "#2B3955",
            ),

            animate_scale=ft.Animation(
                duration=1200,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),

            content=ft.Container(

                width=206,
                height=206,

                alignment=ft.Alignment.CENTER,

                border_radius=103,

                border=ft.Border.all(
                    1,
                    "#29365A",
                ),

                content=ft.Container(

                    width=152,
                    height=152,

                    alignment=ft.Alignment.CENTER,

                    border_radius=76,

                    gradient=ft.RadialGradient(
                        colors=[
                            "#283B61",
                            "#171A35",
                            "#0D1220",
                        ],
                    ),

                    border=ft.Border.all(
                        1,
                        "#40527A",
                    ),

                    shadow=ft.BoxShadow(
                        blur_radius=30,
                        spread_radius=2,
                        color="#304FD1FF",
                    ),

                    content=ft.Column(

                        tight=True,

                        spacing=4,

                        horizontal_alignment=(
                            ft.CrossAxisAlignment.CENTER
                        ),

                        controls=[

                            ft.Icon(
                                ft.Icons.WAVES,
                                size=45,
                                color=AppColors.CYAN,
                            ),

                            ft.Text(
                                "SIGNAL",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),

                            ft.Text(
                                "STUDIO",
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.PURPLE_LIGHT,
                            ),
                        ],
                    ),
                ),
            ),
        )


        # =====================================================
        # DECORATIVE SIGNAL NODES
        # =====================================================

        top_node = self._signal_node(
            AppColors.CYAN,
            ft.Icons.GRAIN,
        )


        right_node = self._signal_node(
            AppColors.PINK,
            ft.Icons.AUTO_AWESOME,
        )


        bottom_node = self._signal_node(
            AppColors.GREEN,
            ft.Icons.SHOW_CHART,
        )


        left_node = self._signal_node(
            AppColors.PURPLE,
            ft.Icons.BLUR_ON,
        )


        # =====================================================
        # STACK
        # =====================================================

        return ft.Container(

            width=330,
            height=290,

            alignment=ft.Alignment.CENTER,

            content=ft.Stack(

                width=300,
                height=280,

                controls=[

                    # Main orbit

                    ft.Container(
                        left=20,
                        top=10,
                        content=self.outer_orbit,
                    ),


                    # Top node

                    ft.Container(
                        left=134,
                        top=0,
                        content=top_node,
                    ),


                    # Right node

                    ft.Container(
                        right=0,
                        top=115,
                        content=right_node,
                    ),


                    # Bottom node

                    ft.Container(
                        left=134,
                        bottom=0,
                        content=bottom_node,
                    ),


                    # Left node

                    ft.Container(
                        left=0,
                        top=115,
                        content=left_node,
                    ),
                ],
            ),
        )


    # =========================================================
    # SIGNAL NODE
    # =========================================================

    def _signal_node(
        self,
        color,
        icon,
    ):

        node = ft.Container(

            width=42,
            height=42,

            alignment=ft.Alignment.CENTER,

            bgcolor=AppColors.SURFACE_2,

            border=ft.Border.all(
                1,
                color,
            ),

            border_radius=14,

            shadow=ft.BoxShadow(
                blur_radius=16,
                color=f"55{color[1:]}",
            ),

            animate_scale=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._hover_node,

            content=ft.Icon(
                icon,
                size=19,
                color=color,
            ),
        )


        return node


    # =========================================================
    # QUICK ACTIONS
    # =========================================================

    def _build_quick_actions(self):

        title = ft.Row(

            controls=[

                ft.Column(

                    spacing=2,

                    expand=True,

                    controls=[

                        ft.Text(
                            "Quick Start",
                            size=17,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.TEXT,
                        ),

                        ft.Text(
                            "Jump directly into the most useful processing workflows.",
                            size=11,
                            color=AppColors.MUTED,
                        ),
                    ],
                ),

                ft.Container(

                    padding=ft.Padding.symmetric(
                        horizontal=10,
                        vertical=5,
                    ),

                    bgcolor=AppColors.SURFACE_2,

                    border_radius=100,

                    content=ft.Text(
                        "INTERACTIVE DSP",
                        size=9,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.CYAN,
                    ),
                ),
            ],
        )


        cards = ft.Row(

            spacing=12,

            controls=[

                self._quick_action_card(
                    title="Grayscale",
                    subtitle="Inspect luminance structure",
                    icon=ft.Icons.MONOCHROME_PHOTOS,
                    accent=AppColors.BLUE,
                    handler=self.on_grayscale,
                ),

                self._quick_action_card(
                    title="Frequency",
                    subtitle="Explore the 2D spectrum",
                    icon=ft.Icons.WAVES,
                    accent=AppColors.CYAN,
                    handler=lambda e: self._navigate(1),
                ),

                self._quick_action_card(
                    title="Compression",
                    subtitle="DFT coefficient reduction",
                    icon=ft.Icons.COMPRESS,
                    accent=AppColors.GREEN,
                    handler=lambda e: self._navigate(2),
                ),

                self._quick_action_card(
                    title="Texture",
                    subtitle="Find dominant repetition",
                    icon=ft.Icons.GRID_VIEW,
                    accent=AppColors.ORANGE,
                    handler=lambda e: self._navigate(3),
                ),

                self._quick_action_card(
                    title="Hybrid",
                    subtitle="Fuse frequency information",
                    icon=ft.Icons.AUTO_AWESOME,
                    accent=AppColors.PINK,
                    handler=lambda e: self._navigate(4),
                ),

                self._quick_action_card(
                    title="Color",
                    subtitle="RGB & YCbCr analysis",
                    icon=ft.Icons.PALETTE,
                    accent=AppColors.PURPLE,
                    handler=lambda e: self._navigate(5),
                ),
            ],
        )


        return ft.Container(

            bgcolor=AppColors.SURFACE,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                AppLayout.CARD_RADIUS
            ),

            padding=20,

            content=ft.Column(

                spacing=16,

                controls=[
                    title,

                    ft.Row(
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            cards,
                        ],
                    ),
                ],
            ),
        )


    # =========================================================
    # QUICK ACTION CARD
    # =========================================================

    def _quick_action_card(
        self,
        title,
        subtitle,
        icon,
        accent,
        handler,
    ):

        icon_box = ft.Container(

            width=46,
            height=46,

            alignment=ft.Alignment.CENTER,

            bgcolor=AppColors.SURFACE_3,

            border_radius=15,

            content=ft.Icon(
                icon,
                size=23,
                color=accent,
            ),
        )


        arrow = ft.Icon(
            ft.Icons.ARROW_FORWARD_ROUNDED,
            size=18,
            color=AppColors.MUTED_2,
        )


        card = ft.Container(

            width=205,
            height=132,

            padding=15,

            bgcolor=AppColors.SURFACE_SOFT,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                17
            ),

            ink=True,

            on_click=handler,

            on_hover=self._hover_quick_card,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            content=ft.Column(

                spacing=10,

                controls=[

                    ft.Row(
                        controls=[
                            icon_box,
                            ft.Container(expand=True),
                            arrow,
                        ],
                    ),

                    ft.Text(
                        title,
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT,
                    ),

                    ft.Text(
                        subtitle,
                        size=10,
                        color=AppColors.MUTED,
                    ),
                ],
            ),
        )


        # Store original accent so hover can use it.

        card.data = accent


        return card


    # =========================================================
    # CAPABILITY STRIP
    # =========================================================

    def _build_capability_strip(self):

        return ft.Container(

            bgcolor="#090E17",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                18
            ),

            padding=ft.Padding.symmetric(
                horizontal=18,
                vertical=14,
            ),

            content=ft.Row(

                spacing=8,

                controls=[

                    self._capability(
                        "12",
                        "DSP FEATURES",
                        AppColors.CYAN,
                    ),

                    self._separator(),

                    self._capability(
                        "2D",
                        "MANUAL DFT",
                        AppColors.PURPLE,
                    ),

                    self._separator(),

                    self._capability(
                        "PSNR",
                        "QUALITY METRIC",
                        AppColors.GREEN,
                    ),

                    self._separator(),

                    self._capability(
                        "RGB",
                        "COLOR CHANNELS",
                        AppColors.RED,
                    ),

                    self._separator(),

                    self._capability(
                        "YCbCr",
                        "COLOR SPACE",
                        AppColors.ORANGE,
                    ),

                    self._separator(),

                    self._capability(
                        "LIVE",
                        "VISUAL ANALYSIS",
                        AppColors.PINK,
                    ),
                ],
            ),
        )


    # =========================================================
    # CAPABILITY ITEM
    # =========================================================

    def _capability(
        self,
        value,
        label,
        accent,
    ):

        return ft.Container(

            expand=True,

            content=ft.Column(

                spacing=2,

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                controls=[

                    ft.Text(
                        value,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=accent,
                    ),

                    ft.Text(
                        label,
                        size=8,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )


    # =========================================================
    # STRIP SEPARATOR
    # =========================================================

    def _separator(self):

        return ft.Container(
            width=1,
            height=35,
            bgcolor=AppColors.BORDER,
        )


    # =========================================================
    # PRIMARY BUTTON
    # =========================================================

    def _primary_button(
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
    # SECONDARY BUTTON
    # =========================================================

    def _secondary_button(
        self,
        text,
        icon,
        handler,
        accent,
    ):

        return ft.OutlinedButton(

            content=text,

            icon=icon,

            on_click=handler,

            style=ft.ButtonStyle(
                color=accent,
                side=ft.BorderSide(
                    1,
                    AppColors.BORDER_LIGHT,
                ),
            ),
        )


    # =========================================================
    # NAVIGATION
    # =========================================================

    def _navigate(
        self,
        index,
    ):

        if self.on_navigate:

            self.on_navigate(index)


    # =========================================================
    # QUICK CARD HOVER
    # =========================================================

    def _hover_quick_card(
        self,
        e,
    ):

        accent = e.control.data


        if e.data:

            e.control.scale = 1.025

            e.control.border = ft.Border.all(
                1,
                accent,
            )

            e.control.bgcolor = (
                AppColors.SURFACE_2
            )


        else:

            e.control.scale = 1.0

            e.control.border = ft.Border.all(
                1,
                AppColors.BORDER,
            )

            e.control.bgcolor = (
                AppColors.SURFACE_SOFT
            )


        e.control.update()


    # =========================================================
    # NODE HOVER
    # =========================================================

    def _hover_node(
        self,
        e,
    ):

        e.control.scale = (
            1.12
            if e.data
            else 1.0
        )

        e.control.update()


    # =========================================================
    # AMBIENT ANIMATION
    # =========================================================

    async def start_ambient_animation(self):
        """
        Starts a subtle breathing animation on the
        central signal visualization.

        Call this after the HomeView has been mounted.

        main_window.py will eventually do:

            self.page.run_task(
                self.home_view.start_ambient_animation
            )
        """

        if self._ambient_running:
            return


        self._ambient_running = True


        while self._ambient_running:

            try:

                self._pulse_large = (
                    not self._pulse_large
                )


                self.outer_orbit.scale = (
                    1.025
                    if self._pulse_large
                    else 1.0
                )


                self.outer_orbit.update()


                await asyncio.sleep(
                    1.25
                )


            except Exception:

                # View may temporarily be detached
                # when switching screens.

                await asyncio.sleep(
                    0.5
                )


    # =========================================================
    # STOP AMBIENT ANIMATION
    # =========================================================

    def stop_ambient_animation(self):

        self._ambient_running = False
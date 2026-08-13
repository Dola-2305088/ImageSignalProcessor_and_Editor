import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
)

from ui.components.section_header import (
    SectionHeader,
)


class ColorView:
    """
    Feature 12 — Color Channel / Color Space Analyzer.

    UI responsibilities:
    - Display/select R, G and B channels
    - Show channel statistics
    - Trigger RGB histogram comparison
    - Trigger RGB frequency analysis
    - Trigger RGB -> YCbCr conversion
    - Explain luminance/chrominance roles

    All image-processing logic remains outside this view.
    """

    def __init__(
        self,
        on_red_channel,
        on_green_channel,
        on_blue_channel,
        on_histograms,
        on_frequencies,
        on_ycbcr,
    ):

        # =====================================================
        # CALLBACKS
        # =====================================================

        self.on_red_channel = on_red_channel
        self.on_green_channel = on_green_channel
        self.on_blue_channel = on_blue_channel

        self.on_histograms = on_histograms
        self.on_frequencies = on_frequencies
        self.on_ycbcr = on_ycbcr


        # =====================================================
        # STATE
        # =====================================================

        self.active_channel = None

        self.channel_statistics = {
            "R": None,
            "G": None,
            "B": None,
        }


        # =====================================================
        # BUILD
        # =====================================================

        self.control = self._build()


    # =========================================================
    # BUILD VIEW
    # =========================================================

    def _build(self):

        # =====================================================
        # HEADER
        # =====================================================

        header = SectionHeader(

            badge="FEATURE 12",

            title="Color Intelligence Lab",

            subtitle=(
                "Decompose the image into RGB signals, inspect "
                "their intensity distributions and frequency content, "
                "then transform the image into luminance and "
                "chrominance components."
            ),

            icon=ft.Icons.PALETTE,

            accent=AppColors.PURPLE,
        )


        # =====================================================
        # COLOR PIPELINE
        # =====================================================

        pipeline = self._build_pipeline()


        # =====================================================
        # RGB CHANNEL LAB
        # =====================================================

        rgb_section = self._build_rgb_section()


        # =====================================================
        # ANALYSIS CONSOLE
        # =====================================================

        analysis_section = (
            self._build_analysis_section()
        )


        # =====================================================
        # YCBCR SECTION
        # =====================================================

        ycbcr_section = (
            self._build_ycbcr_section()
        )


        # =====================================================
        # STATUS / CONCEPT
        # =====================================================

        concept_strip = (
            self._build_concept_strip()
        )


        # =====================================================
        # COMPLETE PAGE
        # =====================================================

        return ft.Container(

            bgcolor=AppColors.SURFACE,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                AppLayout.CARD_RADIUS
            ),

            padding=AppLayout.CARD_PADDING,

            content=ft.Column(

                spacing=20,

                controls=[

                    header.control,

                    pipeline,

                    rgb_section,

                    analysis_section,

                    ycbcr_section,

                    concept_strip,
                ],
            ),
        )


    # =========================================================
    # PIPELINE
    # =========================================================

    def _build_pipeline(self):

        return ft.Container(

            bgcolor="#09111D",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=16,

            padding=ft.Padding.symmetric(
                horizontal=18,
                vertical=15,
            ),

            content=ft.Row(

                scroll=ft.ScrollMode.AUTO,

                vertical_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                controls=[

                    self._pipeline_step(
                        ft.Icons.IMAGE_OUTLINED,
                        "RGB Image",
                        "3-channel signal",
                        AppColors.PURPLE,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_step(
                        ft.Icons.CALL_SPLIT,
                        "Split",
                        "R • G • B",
                        AppColors.CYAN,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_step(
                        ft.Icons.BAR_CHART,
                        "Histogram",
                        "Intensity",
                        AppColors.ORANGE,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_step(
                        ft.Icons.WAVES,
                        "2D DFT",
                        "Per channel",
                        AppColors.PINK,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_step(
                        ft.Icons.SWAP_HORIZ,
                        "Convert",
                        "RGB → YCbCr",
                        AppColors.GREEN,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_step(
                        ft.Icons.VISIBILITY,
                        "Analyze",
                        "Color information",
                        AppColors.BLUE,
                    ),
                ],
            ),
        )


    # =========================================================
    # PIPELINE STEP
    # =========================================================

    def _pipeline_step(
        self,
        icon,
        title,
        subtitle,
        accent,
    ):

        return ft.Container(

            width=132,

            padding=12,

            bgcolor=AppColors.SURFACE_SOFT,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=14,

            data=accent,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._hover_card,

            content=ft.Column(

                spacing=6,

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                controls=[

                    ft.Container(

                        width=38,
                        height=38,

                        alignment=ft.Alignment.CENTER,

                        bgcolor=AppColors.SURFACE_3,

                        border_radius=12,

                        content=ft.Icon(
                            icon,
                            size=20,
                            color=accent,
                        ),
                    ),

                    ft.Text(
                        title,
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT,
                    ),

                    ft.Text(
                        subtitle,
                        size=9,
                        color=AppColors.MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )


    def _pipeline_arrow(self):

        return ft.Icon(
            ft.Icons.ARROW_FORWARD_ROUNDED,
            size=18,
            color=AppColors.MUTED_2,
        )


    # =========================================================
    # RGB SECTION
    # =========================================================

    def _build_rgb_section(self):

        # =====================================================
        # STAT CONTROLS
        # =====================================================

        self.red_mean = self._stat_value()
        self.red_std = self._stat_value()
        self.red_min = self._stat_value()
        self.red_max = self._stat_value()

        self.green_mean = self._stat_value()
        self.green_std = self._stat_value()
        self.green_min = self._stat_value()
        self.green_max = self._stat_value()

        self.blue_mean = self._stat_value()
        self.blue_std = self._stat_value()
        self.blue_min = self._stat_value()
        self.blue_max = self._stat_value()


        # =====================================================
        # CHANNEL CARDS
        # =====================================================

        self.red_card = self._channel_card(

            channel="R",

            title="Red Channel",

            subtitle="Long-wavelength intensity",

            accent=AppColors.RED,

            glow="#3D1218",

            icon=ft.Icons.LENS,

            stats={
                "mean": self.red_mean,
                "std": self.red_std,
                "min": self.red_min,
                "max": self.red_max,
            },

            handler=self._red_clicked,
        )


        self.green_card = self._channel_card(

            channel="G",

            title="Green Channel",

            subtitle="Mid-spectrum intensity",

            accent=AppColors.GREEN,

            glow="#0B2A20",

            icon=ft.Icons.LENS,

            stats={
                "mean": self.green_mean,
                "std": self.green_std,
                "min": self.green_min,
                "max": self.green_max,
            },

            handler=self._green_clicked,
        )


        self.blue_card = self._channel_card(

            channel="B",

            title="Blue Channel",

            subtitle="Short-wavelength intensity",

            accent=AppColors.BLUE,

            glow="#10254B",

            icon=ft.Icons.LENS,

            stats={
                "mean": self.blue_mean,
                "std": self.blue_std,
                "min": self.blue_min,
                "max": self.blue_max,
            },

            handler=self._blue_clicked,
        )


        return ft.Column(

            spacing=13,

            controls=[

                ft.Row(

                    controls=[

                        ft.Column(

                            spacing=2,

                            expand=True,

                            controls=[

                                ft.Text(
                                    "RGB Signal Channels",
                                    size=15,
                                    weight=ft.FontWeight.BOLD,
                                    color=AppColors.TEXT,
                                ),

                                ft.Text(
                                    (
                                        "Inspect each channel as an "
                                        "independent 2D intensity signal."
                                    ),
                                    size=10,
                                    color=AppColors.MUTED,
                                ),
                            ],
                        ),

                        ft.Container(

                            padding=ft.Padding.symmetric(
                                horizontal=10,
                                vertical=5,
                            ),

                            bgcolor="#161126",

                            border_radius=100,

                            content=ft.Text(
                                "3 SIGNAL PLANES",
                                size=8,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.PURPLE_LIGHT,
                            ),
                        ),
                    ],
                ),

                ft.ResponsiveRow(

                    spacing=12,

                    run_spacing=12,

                    controls=[

                        self.red_card,

                        self.green_card,

                        self.blue_card,
                    ],
                ),
            ],
        )


    # =========================================================
    # CHANNEL CARD
    # =========================================================

    def _channel_card(
        self,
        channel,
        title,
        subtitle,
        accent,
        glow,
        icon,
        stats,
        handler,
    ):

        return ft.Container(

            col={
                "xs": 12,
                "sm": 12,
                "md": 4,
            },

            bgcolor="#0B111C",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=18,

            padding=16,

            ink=True,

            on_click=handler,

            on_hover=self._hover_channel,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            data={
                "accent": accent,
                "channel": channel,
            },

            content=ft.Column(

                spacing=13,

                controls=[

                    # =================================================
                    # COLOR VISUAL
                    # =================================================

                    ft.Container(

                        height=92,

                        alignment=ft.Alignment.CENTER,

                        border_radius=16,

                        gradient=ft.LinearGradient(

                            begin=ft.Alignment.TOP_LEFT,

                            end=ft.Alignment.BOTTOM_RIGHT,

                            colors=[
                                "#080B12",
                                glow,
                                accent,
                            ],
                        ),

                        border=ft.Border.all(
                            1,
                            accent,
                        ),

                        content=ft.Stack(

                            controls=[

                                ft.Container(

                                    alignment=ft.Alignment.CENTER,

                                    content=ft.Container(

                                        width=56,
                                        height=56,

                                        border_radius=28,

                                        bgcolor=accent,

                                        opacity=0.75,

                                        shadow=ft.BoxShadow(
                                            blur_radius=30,
                                            spread_radius=2,
                                            color=glow,
                                        ),
                                    ),
                                ),

                                ft.Container(

                                    alignment=ft.Alignment.CENTER,

                                    content=ft.Text(

                                        channel,

                                        size=26,

                                        weight=ft.FontWeight.BOLD,

                                        color=AppColors.WHITE,
                                    ),
                                ),
                            ],
                        ),
                    ),


                    # =================================================
                    # LABEL
                    # =================================================

                    ft.Row(

                        controls=[

                            ft.Container(

                                width=38,
                                height=38,

                                alignment=ft.Alignment.CENTER,

                                border_radius=12,

                                bgcolor=AppColors.SURFACE_3,

                                content=ft.Icon(
                                    icon,
                                    color=accent,
                                    size=21,
                                ),
                            ),

                            ft.Column(

                                spacing=2,

                                expand=True,

                                controls=[

                                    ft.Text(
                                        title,
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.TEXT,
                                    ),

                                    ft.Text(
                                        subtitle,
                                        size=9,
                                        color=AppColors.MUTED,
                                    ),
                                ],
                            ),

                            ft.Icon(
                                ft.Icons.ARROW_FORWARD_ROUNDED,
                                size=18,
                                color=accent,
                            ),
                        ],
                    ),


                    # =================================================
                    # STATS
                    # =================================================

                    ft.Container(

                        bgcolor=AppColors.SURFACE_SOFT,

                        border_radius=13,

                        padding=10,

                        content=ft.Row(

                            controls=[

                                self._mini_stat(
                                    "MEAN",
                                    stats["mean"],
                                ),

                                self._mini_separator(),

                                self._mini_stat(
                                    "STD",
                                    stats["std"],
                                ),

                                self._mini_separator(),

                                self._mini_stat(
                                    "MIN",
                                    stats["min"],
                                ),

                                self._mini_separator(),

                                self._mini_stat(
                                    "MAX",
                                    stats["max"],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )


    # =========================================================
    # STAT VALUE
    # =========================================================

    def _stat_value(self):

        return ft.Text(

            "—",

            size=11,

            weight=ft.FontWeight.BOLD,

            color=AppColors.TEXT,
        )


    # =========================================================
    # MINI STAT
    # =========================================================

    def _mini_stat(
        self,
        title,
        value_control,
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
                        title,
                        size=7,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.MUTED_2,
                    ),

                    value_control,
                ],
            ),
        )


    def _mini_separator(self):

        return ft.Container(
            width=1,
            height=28,
            bgcolor=AppColors.BORDER,
        )


    # =========================================================
    # ANALYSIS SECTION
    # =========================================================

    def _build_analysis_section(self):

        histogram_card = self._analysis_card(

            title="RGB Histograms",

            subtitle=(
                "Compare how intensity values are distributed "
                "across all three channels."
            ),

            badge="INTENSITY",

            icon=ft.Icons.BAR_CHART,

            accent=AppColors.ORANGE,

            visual=self._histogram_visual(),

            handler=self.on_histograms,

            col={
                "xs": 12,
                "sm": 6,
                "lg": 4,
            },
        )


        frequency_card = self._analysis_card(

            title="RGB Frequency Spectra",

            subtitle=(
                "Compute and compare frequency content "
                "independently for R, G and B."
            ),

            badge="2D DFT",

            icon=ft.Icons.WAVES,

            accent=AppColors.PURPLE,

            visual=self._frequency_visual(),

            handler=self.on_frequencies,

            col={
                "xs": 12,
                "sm": 6,
                "lg": 4,
            },
        )


        ycbcr_card = self._analysis_card(

            title="YCbCr Decomposition",

            subtitle=(
                "Separate brightness information from "
                "blue and red chrominance components."
            ),

            badge="COLOR SPACE",

            icon=ft.Icons.COLOR_LENS,

            accent=AppColors.CYAN,

            visual=self._ycbcr_visual(),

            handler=self.on_ycbcr,

            col={
                "xs": 12,
                "sm": 12,
                "lg": 4,
            },
        )


        return ft.Column(

            spacing=13,

            controls=[

                ft.Row(

                    controls=[

                        ft.Text(
                            "Analysis Console",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.TEXT,
                        ),

                        ft.Container(
                            expand=True
                        ),

                        ft.Text(
                            "Choose an analysis mode",
                            size=9,
                            color=AppColors.MUTED,
                        ),
                    ],
                ),

                ft.ResponsiveRow(

                    spacing=12,

                    run_spacing=12,

                    controls=[

                        histogram_card,

                        frequency_card,

                        ycbcr_card,
                    ],
                ),
            ],
        )


    # =========================================================
    # ANALYSIS CARD
    # =========================================================

    def _analysis_card(
        self,
        title,
        subtitle,
        badge,
        icon,
        accent,
        visual,
        handler,
        col,
    ):

        return ft.Container(

            col=col,

            bgcolor="#0C1422",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=17,

            padding=15,

            ink=True,

            on_click=handler,

            data=accent,

            on_hover=self._hover_card,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            content=ft.Column(

                spacing=12,

                controls=[

                    ft.Row(

                        controls=[

                            ft.Container(

                                width=42,
                                height=42,

                                alignment=ft.Alignment.CENTER,

                                bgcolor=AppColors.SURFACE_3,

                                border_radius=13,

                                content=ft.Icon(
                                    icon,
                                    size=22,
                                    color=accent,
                                ),
                            ),

                            ft.Column(

                                spacing=2,

                                expand=True,

                                controls=[

                                    ft.Text(
                                        title,
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.TEXT,
                                    ),

                                    ft.Text(
                                        badge,
                                        size=8,
                                        weight=ft.FontWeight.BOLD,
                                        color=accent,
                                    ),
                                ],
                            ),

                            ft.Icon(
                                ft.Icons.OPEN_IN_NEW,
                                size=17,
                                color=AppColors.MUTED_2,
                            ),
                        ],
                    ),

                    visual,

                    ft.Text(
                        subtitle,
                        size=9,
                        color=AppColors.MUTED,
                    ),
                ],
            ),
        )


    # =========================================================
    # HISTOGRAM VISUAL
    # =========================================================

    def _histogram_visual(self):

        bars = []

        heights = [
            24,
            42,
            64,
            83,
            68,
            47,
            31,
        ]


        colors = [
            AppColors.RED,
            AppColors.RED,
            AppColors.GREEN,
            AppColors.GREEN,
            AppColors.BLUE,
            AppColors.BLUE,
            AppColors.PURPLE,
        ]


        for height, color in zip(
            heights,
            colors,
        ):

            bars.append(

                ft.Container(

                    width=18,
                    height=height,

                    bgcolor=color,

                    border_radius=ft.BorderRadius.only(
                        top_left=5,
                        top_right=5,
                    ),

                    opacity=0.85,
                )
            )


        return ft.Container(

            height=110,

            padding=12,

            bgcolor="#070B13",

            border_radius=14,

            alignment=ft.Alignment.BOTTOM_CENTER,

            content=ft.Row(

                alignment=(
                    ft.MainAxisAlignment.CENTER
                ),

                vertical_alignment=(
                    ft.CrossAxisAlignment.END
                ),

                spacing=7,

                controls=bars,
            ),
        )


    # =========================================================
    # FREQUENCY VISUAL
    # =========================================================

    def _frequency_visual(self):

        return ft.Container(

            height=110,

            bgcolor="#070B13",

            border_radius=14,

            alignment=ft.Alignment.CENTER,

            content=ft.Row(

                alignment=ft.MainAxisAlignment.CENTER,

                spacing=13,

                controls=[

                    self._spectrum_disc(
                        AppColors.RED,
                    ),

                    self._spectrum_disc(
                        AppColors.GREEN,
                    ),

                    self._spectrum_disc(
                        AppColors.BLUE,
                    ),
                ],
            ),
        )


    # =========================================================
    # SPECTRUM DISC
    # =========================================================

    def _spectrum_disc(
        self,
        accent,
    ):

        return ft.Container(

            width=62,
            height=62,

            border_radius=31,

            border=ft.Border.all(
                1,
                accent,
            ),

            alignment=ft.Alignment.CENTER,

            content=ft.Stack(

                width=62,
                height=62,

                controls=[

                    ft.Container(

                        left=10,
                        top=10,

                        width=42,
                        height=42,

                        border_radius=21,

                        border=ft.Border.all(
                            1,
                            AppColors.BORDER_LIGHT,
                        ),
                    ),

                    ft.Container(

                        left=25,
                        top=25,

                        width=12,
                        height=12,

                        border_radius=6,

                        bgcolor=accent,
                    ),

                    ft.Container(

                        left=7,
                        top=22,

                        width=6,
                        height=6,

                        border_radius=3,

                        bgcolor=accent,
                    ),

                    ft.Container(

                        right=7,
                        bottom=20,

                        width=6,
                        height=6,

                        border_radius=3,

                        bgcolor=accent,
                    ),
                ],
            ),
        )


    # =========================================================
    # YCBCR VISUAL
    # =========================================================

    def _ycbcr_visual(self):

        return ft.Container(

            height=110,

            bgcolor="#070B13",

            border_radius=14,

            alignment=ft.Alignment.CENTER,

            content=ft.Row(

                alignment=(
                    ft.MainAxisAlignment.CENTER
                ),

                spacing=10,

                controls=[

                    self._ycbcr_visual_block(
                        "Y",
                        "#E2E8F0",
                    ),

                    self._ycbcr_visual_block(
                        "Cb",
                        AppColors.BLUE,
                    ),

                    self._ycbcr_visual_block(
                        "Cr",
                        AppColors.RED,
                    ),
                ],
            ),
        )


    def _ycbcr_visual_block(
        self,
        text,
        accent,
    ):

        return ft.Container(

            width=64,
            height=64,

            alignment=ft.Alignment.CENTER,

            border_radius=18,

            gradient=ft.LinearGradient(

                begin=ft.Alignment.TOP_LEFT,

                end=ft.Alignment.BOTTOM_RIGHT,

                colors=[
                    AppColors.SURFACE_3,
                    accent,
                ],
            ),

            border=ft.Border.all(
                1,
                accent,
            ),

            content=ft.Text(

                text,

                size=15,

                weight=ft.FontWeight.BOLD,

                color=AppColors.WHITE,
            ),
        )


    # =========================================================
    # YCBCR SECTION
    # =========================================================

    def _build_ycbcr_section(self):

        return ft.Container(

            bgcolor="#09111D",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=17,

            padding=18,

            content=ft.Column(

                spacing=15,

                controls=[

                    # =================================================
                    # HEADER
                    # =================================================

                    ft.Row(

                        controls=[

                            ft.Container(

                                width=44,
                                height=44,

                                alignment=ft.Alignment.CENTER,

                                border_radius=14,

                                gradient=ft.LinearGradient(

                                    begin=ft.Alignment.TOP_LEFT,

                                    end=ft.Alignment.BOTTOM_RIGHT,

                                    colors=[
                                        "#13304A",
                                        "#262044",
                                    ],
                                ),

                                content=ft.Icon(
                                    ft.Icons.COLOR_LENS,
                                    color=AppColors.CYAN,
                                    size=23,
                                ),
                            ),

                            ft.Column(

                                spacing=2,

                                expand=True,

                                controls=[

                                    ft.Text(
                                        "RGB → YCbCr",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.TEXT,
                                    ),

                                    ft.Text(
                                        (
                                            "Separate perceived brightness "
                                            "from color-difference information."
                                        ),
                                        size=10,
                                        color=AppColors.MUTED,
                                    ),
                                ],
                            ),

                            ft.Container(

                                padding=ft.Padding.symmetric(
                                    horizontal=10,
                                    vertical=5,
                                ),

                                border_radius=100,

                                bgcolor="#0B2530",

                                content=ft.Text(
                                    "COLOR TRANSFORM",
                                    size=8,
                                    weight=ft.FontWeight.BOLD,
                                    color=AppColors.CYAN_LIGHT,
                                ),
                            ),
                        ],
                    ),


                    # =================================================
                    # FLOW
                    # =================================================

                    ft.ResponsiveRow(

                        spacing=12,

                        run_spacing=12,

                        controls=[

                            self._component_card(

                                title="Y",

                                subtitle="LUMINANCE",

                                description=(
                                    "Represents brightness "
                                    "and structural intensity."
                                ),

                                icon=ft.Icons.LIGHT_MODE_OUTLINED,

                                accent="#E2E8F0",

                                col={
                                    "xs": 12,
                                    "sm": 4,
                                },
                            ),

                            self._component_card(

                                title="Cb",

                                subtitle="BLUE CHROMA",

                                description=(
                                    "Represents blue-difference "
                                    "chrominance information."
                                ),

                                icon=ft.Icons.WATER_DROP_OUTLINED,

                                accent=AppColors.BLUE,

                                col={
                                    "xs": 12,
                                    "sm": 4,
                                },
                            ),

                            self._component_card(

                                title="Cr",

                                subtitle="RED CHROMA",

                                description=(
                                    "Represents red-difference "
                                    "chrominance information."
                                ),

                                icon=ft.Icons.WATER_DROP,

                                accent=AppColors.RED,

                                col={
                                    "xs": 12,
                                    "sm": 4,
                                },
                            ),
                        ],
                    ),
                ],
            ),
        )


    # =========================================================
    # YCBCR COMPONENT
    # =========================================================

    def _component_card(
        self,
        title,
        subtitle,
        description,
        icon,
        accent,
        col,
    ):

        return ft.Container(

            col=col,

            bgcolor=AppColors.SURFACE_SOFT,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=15,

            padding=14,

            data=accent,

            on_hover=self._hover_card,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            content=ft.Row(

                spacing=12,

                controls=[

                    ft.Container(

                        width=54,
                        height=54,

                        alignment=ft.Alignment.CENTER,

                        border_radius=17,

                        bgcolor=AppColors.SURFACE_3,

                        border=ft.Border.all(
                            1,
                            accent,
                        ),

                        content=ft.Text(

                            title,

                            size=18,

                            weight=ft.FontWeight.BOLD,

                            color=accent,
                        ),
                    ),

                    ft.Column(

                        spacing=3,

                        expand=True,

                        controls=[

                            ft.Row(

                                controls=[

                                    ft.Icon(
                                        icon,
                                        size=16,
                                        color=accent,
                                    ),

                                    ft.Text(
                                        subtitle,
                                        size=9,
                                        weight=ft.FontWeight.BOLD,
                                        color=accent,
                                    ),
                                ],
                            ),

                            ft.Text(
                                description,
                                size=9,
                                color=AppColors.MUTED,
                            ),
                        ],
                    ),
                ],
            ),
        )


    # =========================================================
    # CONCEPT STRIP
    # =========================================================

    def _build_concept_strip(self):

        self.mode_icon = ft.Icon(

            ft.Icons.INFO_OUTLINE,

            size=18,

            color=AppColors.PURPLE_LIGHT,
        )


        self.mode_title = ft.Text(

            "Color Analysis Ready",

            size=11,

            weight=ft.FontWeight.BOLD,

            color=AppColors.PURPLE_LIGHT,
        )


        self.mode_description = ft.Text(

            (
                "Choose a channel or analysis mode. "
                "Results will appear in the processed-image workspace."
            ),

            size=9,

            color=AppColors.MUTED,

            expand=True,
        )


        return ft.Container(

            padding=14,

            border_radius=15,

            gradient=ft.LinearGradient(

                begin=ft.Alignment.CENTER_LEFT,

                end=ft.Alignment.CENTER_RIGHT,

                colors=[
                    "#0A1622",
                    "#121326",
                    "#1B1020",
                ],
            ),

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            content=ft.Row(

                spacing=11,

                controls=[

                    ft.Container(

                        width=40,
                        height=40,

                        alignment=ft.Alignment.CENTER,

                        border_radius=12,

                        bgcolor=AppColors.SURFACE_3,

                        content=self.mode_icon,
                    ),

                    ft.Column(

                        spacing=2,

                        expand=True,

                        controls=[

                            self.mode_title,

                            self.mode_description,
                        ],
                    ),

                    ft.Row(

                        tight=True,

                        spacing=5,

                        controls=[

                            self._color_dot(
                                AppColors.RED
                            ),

                            self._color_dot(
                                AppColors.GREEN
                            ),

                            self._color_dot(
                                AppColors.BLUE
                            ),
                        ],
                    ),
                ],
            ),
        )


    # =========================================================
    # COLOR DOT
    # =========================================================

    def _color_dot(
        self,
        color,
    ):

        return ft.Container(

            width=10,
            height=10,

            border_radius=100,

            bgcolor=color,
        )


    # =========================================================
    # CHANNEL EVENTS
    # =========================================================

    def _red_clicked(
        self,
        e,
    ):

        self._select_channel(
            "R",
            "Red Channel",
            AppColors.RED,
        )


        if self.on_red_channel:

            self.on_red_channel(e)


    def _green_clicked(
        self,
        e,
    ):

        self._select_channel(
            "G",
            "Green Channel",
            AppColors.GREEN,
        )


        if self.on_green_channel:

            self.on_green_channel(e)


    def _blue_clicked(
        self,
        e,
    ):

        self._select_channel(
            "B",
            "Blue Channel",
            AppColors.BLUE,
        )


        if self.on_blue_channel:

            self.on_blue_channel(e)


    # =========================================================
    # SELECT CHANNEL
    # =========================================================

    def _select_channel(
        self,
        channel,
        title,
        accent,
    ):

        self.active_channel = channel


        self.mode_icon.name = (
            ft.Icons.LENS
        )

        self.mode_icon.color = accent


        self.mode_title.value = (
            f"{title} Selected"
        )

        self.mode_title.color = accent


        self.mode_description.value = (
            f"Displaying the {title.lower()} "
            f"as an independent intensity signal."
        )


        self.mode_icon.update()

        self.mode_title.update()

        self.mode_description.update()


    # =========================================================
    # PUBLIC — UPDATE CHANNEL STATISTICS
    # =========================================================

    def update_channel_statistics(
        self,
        channel,
        stats,
    ):
        """
        stats expected:

        {
            "mean": ...,
            "std": ...,
            "min": ...,
            "max": ...
        }
        """

        channel = channel.upper()


        if channel not in {
            "R",
            "G",
            "B",
        }:

            return


        self.channel_statistics[
            channel
        ] = stats


        control_map = {

            "R": {
                "mean": self.red_mean,
                "std": self.red_std,
                "min": self.red_min,
                "max": self.red_max,
            },

            "G": {
                "mean": self.green_mean,
                "std": self.green_std,
                "min": self.green_min,
                "max": self.green_max,
            },

            "B": {
                "mean": self.blue_mean,
                "std": self.blue_std,
                "min": self.blue_min,
                "max": self.blue_max,
            },
        }


        controls = control_map[
            channel
        ]


        controls["mean"].value = (
            f"{stats['mean']:.1f}"
        )


        controls["std"].value = (
            f"{stats['std']:.1f}"
        )


        controls["min"].value = (
            f"{stats['min']:.0f}"
        )


        controls["max"].value = (
            f"{stats['max']:.0f}"
        )


        for control in controls.values():

            control.update()


    # =========================================================
    # PUBLIC — ANALYSIS STATUS
    # =========================================================

    def show_histogram_status(
        self,
    ):

        self._set_mode_status(

            title="RGB Histogram Comparison",

            description=(
                "Comparing the distribution of red, green "
                "and blue intensity values."
            ),

            icon=ft.Icons.BAR_CHART,

            accent=AppColors.ORANGE,
        )


    def show_frequency_status(
        self,
    ):

        self._set_mode_status(

            title="RGB Frequency Analysis",

            description=(
                "Comparing the 2D frequency content "
                "of all three color channels."
            ),

            icon=ft.Icons.WAVES,

            accent=AppColors.PURPLE,
        )


    def show_ycbcr_status(
        self,
    ):

        self._set_mode_status(

            title="YCbCr Color Space",

            description=(
                "Displaying luminance Y together with "
                "Cb and Cr chrominance components."
            ),

            icon=ft.Icons.COLOR_LENS,

            accent=AppColors.CYAN,
        )


    # =========================================================
    # SET MODE STATUS
    # =========================================================

    def _set_mode_status(
        self,
        title,
        description,
        icon,
        accent,
    ):

        self.mode_icon.name = icon

        self.mode_icon.color = accent


        self.mode_title.value = title

        self.mode_title.color = accent


        self.mode_description.value = (
            description
        )


        self.mode_icon.update()

        self.mode_title.update()

        self.mode_description.update()


    # =========================================================
    # PUBLIC — RESET
    # =========================================================

    def reset(
        self,
    ):

        self.active_channel = None


        self.channel_statistics = {
            "R": None,
            "G": None,
            "B": None,
        }


        controls = [

            self.red_mean,
            self.red_std,
            self.red_min,
            self.red_max,

            self.green_mean,
            self.green_std,
            self.green_min,
            self.green_max,

            self.blue_mean,
            self.blue_std,
            self.blue_min,
            self.blue_max,
        ]


        for control in controls:

            control.value = "—"

            control.update()


        self.mode_icon.name = (
            ft.Icons.INFO_OUTLINE
        )

        self.mode_icon.color = (
            AppColors.PURPLE_LIGHT
        )


        self.mode_title.value = (
            "Color Analysis Ready"
        )

        self.mode_title.color = (
            AppColors.PURPLE_LIGHT
        )


        self.mode_description.value = (
            "Choose a channel or analysis mode. "
            "Results will appear in the processed-image workspace."
        )


        self.mode_icon.update()

        self.mode_title.update()

        self.mode_description.update()


    # =========================================================
    # HOVER — CHANNEL
    # =========================================================

    def _hover_channel(
        self,
        e,
    ):

        accent = e.control.data[
            "accent"
        ]


        if e.data:

            e.control.scale = 1.018

            e.control.border = (
                ft.Border.all(
                    1,
                    accent,
                )
            )


        else:

            e.control.scale = 1.0

            e.control.border = (
                ft.Border.all(
                    1,
                    AppColors.BORDER,
                )
            )


        e.control.update()


    # =========================================================
    # HOVER — CARD
    # =========================================================

    def _hover_card(
        self,
        e,
    ):

        accent = e.control.data


        if e.data:

            e.control.scale = 1.015

            e.control.border = (
                ft.Border.all(
                    1,
                    accent,
                )
            )


        else:

            e.control.scale = 1.0

            e.control.border = (
                ft.Border.all(
                    1,
                    AppColors.BORDER,
                )
            )


        e.control.update()
import math

import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
)

from ui.components.section_header import (
    SectionHeader,
)


class TextureView:
    """
    Feature 8 — Texture Analyzer.

    UI responsibilities:
    - Trigger texture analysis
    - Display dominant direction
    - Display texture orientation angle
    - Display frequency and spacing
    - Display periodicity strength
    - Display saved texture comparisons

    Signal-processing calculations stay outside this view.

    main_window.py will eventually call:

        texture_view.update_result(name, result)

    where result is the dictionary returned by:

        analyze_texture(...)
    """

    def __init__(
        self,
        on_analyze,
        on_show_comparisons=None,
    ):

        # =====================================================
        # CALLBACKS
        # =====================================================

        self.on_analyze = on_analyze

        self.on_show_comparisons = (
            on_show_comparisons
        )


        # =====================================================
        # CURRENT RESULT
        # =====================================================

        self.current_result = None

        self.current_name = None


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

            badge="FEATURE 3",

            title="Texture Analyzer",

            subtitle=(
                "Detect repeating structures and dominant "
                "orientation by analyzing peaks in the "
                "2D frequency spectrum — without machine learning."
            ),

            icon=ft.Icons.GRID_VIEW,

            accent=AppColors.ORANGE,
        )


        # =====================================================
        # PROCESS PIPELINE
        # =====================================================

        pipeline = self._build_pipeline()


        # =====================================================
        # MAIN ANALYSIS AREA
        # =====================================================

        main_area = ft.ResponsiveRow(

            spacing=14,

            run_spacing=14,

            controls=[

                self._build_analysis_console(),

                self._build_orientation_console(),
            ],
        )


        # =====================================================
        # METRIC DASHBOARD
        # =====================================================

        metrics = self._build_metric_dashboard()


        # =====================================================
        # COMPARISON SECTION
        # =====================================================

        comparison = (
            self._build_comparison_section()
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

                    main_area,

                    metrics,

                    comparison,
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
                        "Texture",
                        "Input image",
                        AppColors.BLUE,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_step(
                        ft.Icons.FILTER_CENTER_FOCUS,
                        "Window",
                        "Hann window",
                        AppColors.CYAN,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_step(
                        ft.Icons.WAVES,
                        "2D DFT",
                        "Frequency domain",
                        AppColors.PURPLE,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_step(
                        ft.Icons.RADAR,
                        "Peak",
                        "Dominant frequency",
                        AppColors.ORANGE,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_step(
                        ft.Icons.EXPLORE_OUTLINED,
                        "Direction",
                        "Orientation",
                        AppColors.PINK,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_step(
                        ft.Icons.STRAIGHTEN,
                        "Spacing",
                        "Repeating pattern",
                        AppColors.GREEN,
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

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._hover_card,

            data=accent,

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

                        border_radius=12,

                        bgcolor=AppColors.SURFACE_3,

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
    # ANALYSIS CONSOLE
    # =========================================================

    def _build_analysis_console(self):

        self.analysis_image_name = ft.Text(

            "No texture analyzed",

            size=13,

            weight=ft.FontWeight.BOLD,

            color=AppColors.TEXT,
        )


        self.analysis_status = ft.Text(

            (
                "Open a repeating texture such as brick, "
                "cloth, tiles, woven fabric, grass or stripes."
            ),

            size=10,

            color=AppColors.MUTED,
        )


        # =====================================================
        # MINI SPECTRUM VISUAL
        # =====================================================

        visual = ft.Container(

            height=135,

            alignment=ft.Alignment.CENTER,

            bgcolor="#050A12",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=16,

            content=self._texture_visual(),
        )


        # =====================================================
        # ANALYZE BUTTON
        # =====================================================

        analyze_button = ft.Container(

            padding=15,

            bgcolor=AppColors.SURFACE_SOFT,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=15,

            ink=True,

            on_click=self.on_analyze,

            data=AppColors.ORANGE,

            on_hover=self._hover_action,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            content=ft.Row(

                spacing=12,

                controls=[

                    ft.Container(

                        width=46,
                        height=46,

                        alignment=ft.Alignment.CENTER,

                        bgcolor=AppColors.SURFACE_3,

                        border_radius=14,

                        content=ft.Icon(
                            ft.Icons.SEARCH,
                            size=24,
                            color=AppColors.ORANGE,
                        ),
                    ),

                    ft.Column(

                        spacing=3,

                        expand=True,

                        controls=[

                            ft.Text(
                                "Analyze Current Texture",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),

                            ft.Text(
                                (
                                    "Locate dominant non-DC "
                                    "frequency peaks."
                                ),
                                size=9,
                                color=AppColors.MUTED,
                            ),
                        ],
                    ),

                    ft.Icon(
                        ft.Icons.ARROW_FORWARD_ROUNDED,
                        color=AppColors.ORANGE,
                    ),
                ],
            ),
        )


        return ft.Container(

            col={
                "xs": 12,
                "sm": 12,
                "md": 6,
                "lg": 7,
            },

            bgcolor="#0C1422",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=17,

            padding=18,

            content=ft.Column(

                spacing=15,

                controls=[

                    self._console_header(

                        icon=ft.Icons.QUERY_STATS,

                        title="Frequency Pattern Detector",

                        subtitle=(
                            "Search for repeating spatial "
                            "patterns using spectral peaks."
                        ),

                        accent=AppColors.ORANGE,
                    ),

                    visual,

                    ft.Container(

                        bgcolor="#17130B",

                        border=ft.Border.all(
                            1,
                            "#4B3510",
                        ),

                        border_radius=13,

                        padding=14,

                        content=ft.Column(

                            spacing=5,

                            controls=[

                                self.analysis_image_name,

                                self.analysis_status,
                            ],
                        ),
                    ),

                    analyze_button,
                ],
            ),
        )


    # =========================================================
    # TEXTURE MINI VISUAL
    # =========================================================

    def _texture_visual(self):

        dot_positions = [

            (76, 29, 8),
            (34, 70, 7),
            (104, 78, 6),
            (64, 95, 5),
            (22, 34, 4),
            (117, 41, 4),
            (49, 23, 4),
        ]


        controls = [

            # Outer frequency rings

            ft.Container(

                left=18,
                top=7,

                width=115,
                height=115,

                border_radius=58,

                border=ft.Border.all(
                    1,
                    "#24324A",
                ),
            ),

            ft.Container(

                left=34,
                top=23,

                width=83,
                height=83,

                border_radius=42,

                border=ft.Border.all(
                    1,
                    "#2E3B55",
                ),
            ),

            # DC center

            ft.Container(

                left=65,
                top=54,

                width=22,
                height=22,

                border_radius=11,

                bgcolor=AppColors.CYAN,

                opacity=0.55,
            ),
        ]


        for x, y, size in dot_positions:

            controls.append(

                ft.Container(

                    left=x,
                    top=y,

                    width=size,
                    height=size,

                    border_radius=size / 2,

                    bgcolor=AppColors.ORANGE,
                )
            )


        # Dominant symmetric peaks

        controls.extend(

            [

                ft.Container(

                    left=43,
                    top=39,

                    width=13,
                    height=13,

                    border_radius=7,

                    bgcolor=AppColors.ORANGE,

                    shadow=ft.BoxShadow(
                        blur_radius=12,
                        color="#77F59E0B",
                    ),
                ),

                ft.Container(

                    left=96,
                    top=88,

                    width=13,
                    height=13,

                    border_radius=7,

                    bgcolor=AppColors.ORANGE,

                    shadow=ft.BoxShadow(
                        blur_radius=12,
                        color="#77F59E0B",
                    ),
                ),
            ]
        )


        return ft.Stack(

            width=150,
            height=130,

            controls=controls,
        )


    # =========================================================
    # ORIENTATION CONSOLE
    # =========================================================

    def _build_orientation_console(self):

        # =====================================================
        # DIRECTION ICON
        # =====================================================

        self.direction_icon = ft.Icon(

            ft.Icons.EXPLORE_OUTLINED,

            size=49,

            color=AppColors.ORANGE,
        )


        self.direction_text = ft.Text(

            "WAITING",

            size=19,

            weight=ft.FontWeight.BOLD,

            color=AppColors.ORANGE,

            text_align=ft.TextAlign.CENTER,
        )


        self.angle_text = ft.Text(

            "—°",

            size=30,

            weight=ft.FontWeight.BOLD,

            color=AppColors.TEXT,

            text_align=ft.TextAlign.CENTER,
        )


        # =====================================================
        # COMPASS
        # =====================================================

        self.compass_center = ft.Container(

            width=150,
            height=150,

            border_radius=75,

            alignment=ft.Alignment.CENTER,

            border=ft.Border.all(
                1,
                AppColors.BORDER_LIGHT,
            ),

            gradient=ft.RadialGradient(

                colors=[
                    "#1E2638",
                    "#111827",
                    "#090D16",
                ],
            ),

            content=ft.Stack(

                width=150,
                height=150,

                controls=[

                    # Crosshair

                    ft.Container(
                        left=74,
                        top=16,
                        width=1,
                        height=118,
                        bgcolor="#34445F",
                    ),

                    ft.Container(
                        left=16,
                        top=74,
                        width=118,
                        height=1,
                        bgcolor="#34445F",
                    ),


                    # Labels

                    ft.Container(
                        top=5,
                        left=69,
                        content=ft.Text(
                            "90°",
                            size=8,
                            color=AppColors.MUTED,
                        ),
                    ),

                    ft.Container(
                        bottom=5,
                        left=69,
                        content=ft.Text(
                            "90°",
                            size=8,
                            color=AppColors.MUTED,
                        ),
                    ),

                    ft.Container(
                        left=5,
                        top=68,
                        content=ft.Text(
                            "0°",
                            size=8,
                            color=AppColors.MUTED,
                        ),
                    ),

                    ft.Container(
                        right=5,
                        top=68,
                        content=ft.Text(
                            "0°",
                            size=8,
                            color=AppColors.MUTED,
                        ),
                    ),


                    # Center visual

                    ft.Container(

                        left=48,
                        top=48,

                        width=54,
                        height=54,

                        border_radius=27,

                        bgcolor=AppColors.SURFACE_3,

                        border=ft.Border.all(
                            1,
                            "#46597A",
                        ),

                        alignment=ft.Alignment.CENTER,

                        content=self.direction_icon,
                    ),
                ],
            ),
        )


        return ft.Container(

            col={
                "xs": 12,
                "sm": 12,
                "md": 6,
                "lg": 5,
            },

            bgcolor="#0C1422",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=17,

            padding=18,

            content=ft.Column(

                spacing=14,

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                controls=[

                    self._console_header(

                        icon=ft.Icons.EXPLORE,

                        title="Dominant Orientation",

                        subtitle=(
                            "The texture direction is derived "
                            "from the strongest spectral peak."
                        ),

                        accent=AppColors.ORANGE,
                    ),

                    self.compass_center,

                    self.direction_text,

                    self.angle_text,

                    ft.Text(

                        (
                            "Texture orientation is perpendicular "
                            "to the dominant frequency direction."
                        ),

                        size=9,

                        color=AppColors.MUTED,

                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )


    # =========================================================
    # METRICS
    # =========================================================

    def _build_metric_dashboard(self):

        # =====================================================
        # VALUES
        # =====================================================

        self.metric_direction_value = ft.Text(
            "—",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
        )


        self.metric_spacing_value = ft.Text(
            "—",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
        )


        self.metric_frequency_value = ft.Text(
            "—",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
        )


        self.metric_strength_value = ft.Text(
            "—",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
        )


        # =====================================================
        # CARDS
        # =====================================================

        direction_card = self._metric_card(

            "DIRECTION",

            self.metric_direction_value,

            ft.Icons.EXPLORE,

            AppColors.ORANGE,

            "Dominant texture orientation",
        )


        spacing_card = self._metric_card(

            "REPEATING SPACING",

            self.metric_spacing_value,

            ft.Icons.STRAIGHTEN,

            AppColors.GREEN,

            "Estimated spatial period",
        )


        frequency_card = self._metric_card(

            "DOMINANT FREQUENCY",

            self.metric_frequency_value,

            ft.Icons.WAVES,

            AppColors.CYAN,

            "Cycles per image pixel",
        )


        strength_card = self._metric_card(

            "PERIODICITY STRENGTH",

            self.metric_strength_value,

            ft.Icons.SIGNAL_CELLULAR_ALT,

            AppColors.PURPLE,

            "Peak / average spectral magnitude",
        )


        return ft.Column(

            spacing=12,

            controls=[

                ft.Row(

                    controls=[

                        ft.Text(

                            "Texture Measurements",

                            size=14,

                            weight=ft.FontWeight.BOLD,

                            color=AppColors.TEXT,
                        ),

                        ft.Container(
                            expand=True
                        ),

                        ft.Text(

                            "Frequency-domain estimates",

                            size=10,

                            color=AppColors.MUTED,
                        ),
                    ],
                ),

                ft.ResponsiveRow(

                    spacing=12,

                    run_spacing=12,

                    controls=[

                        direction_card,

                        spacing_card,

                        frequency_card,

                        strength_card,
                    ],
                ),
            ],
        )


    # =========================================================
    # METRIC CARD
    # =========================================================

    def _metric_card(
        self,
        title,
        value_control,
        icon,
        accent,
        subtitle,
    ):

        return ft.Container(

            col={
                "xs": 12,
                "sm": 6,
                "lg": 3,
            },

            bgcolor="#09111D",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=16,

            padding=16,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._hover_card,

            data=accent,

            content=ft.Column(

                spacing=10,

                controls=[

                    ft.Row(

                        controls=[

                            ft.Container(

                                width=40,
                                height=40,

                                alignment=ft.Alignment.CENTER,

                                bgcolor=AppColors.SURFACE_3,

                                border_radius=12,

                                content=ft.Icon(
                                    icon,
                                    size=21,
                                    color=accent,
                                ),
                            ),

                            ft.Container(
                                expand=True
                            ),

                            ft.Container(

                                width=9,
                                height=9,

                                bgcolor=accent,

                                border_radius=100,
                            ),
                        ],
                    ),

                    ft.Text(

                        title,

                        size=9,

                        weight=ft.FontWeight.BOLD,

                        color=AppColors.MUTED,
                    ),

                    value_control,

                    ft.Text(

                        subtitle,

                        size=9,

                        color=AppColors.MUTED_2,
                    ),

                    ft.Container(

                        height=3,

                        bgcolor=accent,

                        border_radius=3,
                    ),
                ],
            ),
        )


    # =========================================================
    # COMPARISON SECTION
    # =========================================================

    def _build_comparison_section(self):

        self.comparison_count = ft.Text(

            "0 saved",

            size=10,

            weight=ft.FontWeight.BOLD,

            color=AppColors.ORANGE,
        )


        self.comparison_content = ft.Column(

            spacing=7,

            controls=[

                self._comparison_placeholder()
            ],
        )


        compare_button = ft.OutlinedButton(

            content="Refresh Comparison",

            icon=ft.Icons.COMPARE_ARROWS,

            on_click=self.on_show_comparisons,

            visible=(
                self.on_show_comparisons
                is not None
            ),
        )


        return ft.Container(

            bgcolor="#09111D",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=17,

            padding=18,

            content=ft.Column(

                spacing=14,

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
                                    ft.Icons.COMPARE_ARROWS,
                                    color=AppColors.ORANGE,
                                ),
                            ),

                            ft.Column(

                                spacing=2,

                                expand=True,

                                controls=[

                                    ft.Text(

                                        "Texture Comparison",

                                        size=13,

                                        weight=ft.FontWeight.BOLD,

                                        color=AppColors.TEXT,
                                    ),

                                    ft.Text(

                                        (
                                            "Analyze multiple images "
                                            "and compare their frequency patterns."
                                        ),

                                        size=10,

                                        color=AppColors.MUTED,
                                    ),
                                ],
                            ),

                            self.comparison_count,

                            compare_button,
                        ],
                    ),

                    ft.Divider(
                        height=1,
                        color=AppColors.BORDER,
                    ),

                    ft.Row(

                        scroll=ft.ScrollMode.AUTO,

                        controls=[

                            ft.Container(

                                content=self.comparison_content,

                                expand=True,
                            )
                        ],
                    ),
                ],
            ),
        )


    # =========================================================
    # COMPARISON PLACEHOLDER
    # =========================================================

    def _comparison_placeholder(self):

        return ft.Container(

            height=80,

            alignment=ft.Alignment.CENTER,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=13,

            bgcolor=AppColors.SURFACE_SOFT,

            content=ft.Row(

                alignment=ft.MainAxisAlignment.CENTER,

                controls=[

                    ft.Icon(

                        ft.Icons.GRID_VIEW_OUTLINED,

                        color=AppColors.MUTED_2,
                    ),

                    ft.Text(

                        (
                            "Texture results will appear here "
                            "after analysis."
                        ),

                        size=10,

                        color=AppColors.MUTED,
                    ),
                ],
            ),
        )


    # =========================================================
    # CONSOLE HEADER
    # =========================================================

    def _console_header(
        self,
        icon,
        title,
        subtitle,
        accent,
    ):

        return ft.Row(

            spacing=12,

            controls=[

                ft.Container(

                    width=42,
                    height=42,

                    alignment=ft.Alignment.CENTER,

                    bgcolor=AppColors.SURFACE_3,

                    border_radius=13,

                    content=ft.Icon(
                        icon,
                        size=21,
                        color=accent,
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

                            size=10,

                            color=AppColors.MUTED,
                        ),
                    ],
                ),
            ],
        )


    # =========================================================
    # PUBLIC — UPDATE RESULT
    # =========================================================

    def update_result(
        self,
        image_name,
        result,
    ):
        """
        Update the visual dashboard using the dictionary
        returned by analyze_texture().
        """

        self.current_name = image_name

        self.current_result = result


        # =====================================================
        # EXTRACT RESULT
        # =====================================================

        orientation = result[
            "orientation"
        ]


        angle = result[
            "texture_angle"
        ]


        frequency = result[
            "radial_frequency"
        ]


        spacing = result[
            "spacing_pixels"
        ]


        strength = result[
            "periodicity_strength"
        ]


        # =====================================================
        # SPACING
        # =====================================================

        if math.isinf(spacing):

            spacing_text = "N/A"

        else:

            spacing_text = (
                f"{spacing:.2f} px"
            )


        # =====================================================
        # MAIN ANALYSIS STATUS
        # =====================================================

        self.analysis_image_name.value = (
            image_name
        )


        self.analysis_status.value = (

            f"Dominant {orientation.lower()} pattern detected • "
            f"{frequency:.4f} cycles/pixel"
        )


        # =====================================================
        # ORIENTATION CONSOLE
        # =====================================================

        self.direction_text.value = (
            orientation.upper()
        )


        self.angle_text.value = (
            f"{angle:.1f}°"
        )


        direction_icon, direction_color = (
            self._orientation_style(
                orientation
            )
        )


        self.direction_icon.name = (
            direction_icon
        )


        self.direction_icon.color = (
            direction_color
        )


        self.direction_text.color = (
            direction_color
        )


        # =====================================================
        # METRICS
        # =====================================================

        self.metric_direction_value.value = (
            orientation
        )


        self.metric_spacing_value.value = (
            spacing_text
        )


        self.metric_frequency_value.value = (
            f"{frequency:.4f}"
        )


        self.metric_strength_value.value = (
            f"{strength:.2f}"
        )


        # =====================================================
        # UPDATE CONTROLS
        # =====================================================

        self.analysis_image_name.update()

        self.analysis_status.update()

        self.direction_text.update()

        self.angle_text.update()

        self.direction_icon.update()

        self.metric_direction_value.update()

        self.metric_spacing_value.update()

        self.metric_frequency_value.update()

        self.metric_strength_value.update()


    # =========================================================
    # ORIENTATION STYLE
    # =========================================================

    def _orientation_style(
        self,
        orientation,
    ):

        orientation_lower = (
            orientation.lower()
        )


        if orientation_lower == "horizontal":

            return (
                ft.Icons.SWAP_HORIZ,
                AppColors.BLUE,
            )


        if orientation_lower == "vertical":

            return (
                ft.Icons.SWAP_VERT,
                AppColors.GREEN,
            )


        return (
            ft.Icons.NORTH_EAST,
            AppColors.ORANGE,
        )


    # =========================================================
    # PUBLIC — UPDATE COMPARISONS
    # =========================================================

    def update_comparisons(
        self,
        texture_results,
    ):
        """
        texture_results should have the same structure as:

            {
                "brick.jpg": result_dict,
                "cloth.jpg": result_dict,
                ...
            }
        """

        if not texture_results:

            self.comparison_content.controls = [

                self._comparison_placeholder()
            ]


            self.comparison_count.value = (
                "0 saved"
            )


            self.comparison_content.update()

            self.comparison_count.update()

            return


        # =====================================================
        # HEADER
        # =====================================================

        rows = [

            ft.Container(

                bgcolor=AppColors.SURFACE_3,

                border_radius=10,

                padding=10,

                content=ft.Row(

                    controls=[

                        self._table_header(
                            "Texture",
                            175,
                        ),

                        self._table_header(
                            "Direction",
                            105,
                        ),

                        self._table_header(
                            "Angle",
                            85,
                        ),

                        self._table_header(
                            "Spacing",
                            105,
                        ),

                        self._table_header(
                            "Frequency",
                            120,
                        ),

                        self._table_header(
                            "Strength",
                            95,
                        ),
                    ],
                ),
            )
        ]


        # =====================================================
        # RESULTS
        # =====================================================

        for (
            name,
            result,
        ) in texture_results.items():

            spacing = result[
                "spacing_pixels"
            ]


            if math.isinf(spacing):

                spacing_text = "N/A"

            else:

                spacing_text = (
                    f"{spacing:.2f} px"
                )


            orientation = result[
                "orientation"
            ]


            _, accent = (
                self._orientation_style(
                    orientation
                )
            )


            row = ft.Container(

                padding=ft.Padding.symmetric(
                    horizontal=10,
                    vertical=9,
                ),

                border=ft.Border.only(

                    bottom=ft.BorderSide(
                        1,
                        AppColors.BORDER,
                    )
                ),

                content=ft.Row(

                    controls=[

                        ft.Text(
                            name,
                            width=175,
                            size=10,
                            color=AppColors.TEXT,
                        ),

                        ft.Container(

                            width=105,

                            content=ft.Text(
                                orientation,
                                size=10,
                                weight=ft.FontWeight.BOLD,
                                color=accent,
                            ),
                        ),

                        ft.Text(
                            f"{result['texture_angle']:.1f}°",
                            width=85,
                            size=10,
                            color=AppColors.TEXT_SECONDARY,
                        ),

                        ft.Text(
                            spacing_text,
                            width=105,
                            size=10,
                            color=AppColors.TEXT_SECONDARY,
                        ),

                        ft.Text(
                            f"{result['radial_frequency']:.4f}",
                            width=120,
                            size=10,
                            color=AppColors.TEXT_SECONDARY,
                        ),

                        ft.Text(
                            f"{result['periodicity_strength']:.2f}",
                            width=95,
                            size=10,
                            color=AppColors.TEXT_SECONDARY,
                        ),
                    ],
                ),
            )


            rows.append(
                row
            )


        self.comparison_content.controls = (
            rows
        )


        count = len(
            texture_results
        )


        self.comparison_count.value = (
            f"{count} saved"
        )


        self.comparison_content.update()

        self.comparison_count.update()


    # =========================================================
    # TABLE HEADER
    # =========================================================

    def _table_header(
        self,
        text,
        width,
    ):

        return ft.Text(

            text,

            width=width,

            size=9,

            weight=ft.FontWeight.BOLD,

            color=AppColors.MUTED,
        )


    # =========================================================
    # PUBLIC — RESET CURRENT RESULT
    # =========================================================

    def reset_result(
        self,
    ):

        self.current_result = None

        self.current_name = None


        self.analysis_image_name.value = (
            "No texture analyzed"
        )


        self.analysis_status.value = (

            "Open a repeating texture such as brick, "
            "cloth, tiles, woven fabric, grass or stripes."
        )


        self.direction_text.value = (
            "WAITING"
        )


        self.direction_text.color = (
            AppColors.ORANGE
        )


        self.angle_text.value = (
            "—°"
        )


        self.direction_icon.name = (
            ft.Icons.EXPLORE_OUTLINED
        )


        self.direction_icon.color = (
            AppColors.ORANGE
        )


        self.metric_direction_value.value = "—"

        self.metric_spacing_value.value = "—"

        self.metric_frequency_value.value = "—"

        self.metric_strength_value.value = "—"


        self.analysis_image_name.update()

        self.analysis_status.update()

        self.direction_text.update()

        self.angle_text.update()

        self.direction_icon.update()

        self.metric_direction_value.update()

        self.metric_spacing_value.update()

        self.metric_frequency_value.update()

        self.metric_strength_value.update()


    # =========================================================
    # HOVER CARD
    # =========================================================

    def _hover_card(
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


        else:

            e.control.scale = 1.0

            e.control.border = ft.Border.all(
                1,
                AppColors.BORDER,
            )


        e.control.update()


    # =========================================================
    # HOVER ACTION
    # =========================================================

    def _hover_action(
        self,
        e,
    ):

        accent = e.control.data


        if e.data:

            e.control.scale = 1.015

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
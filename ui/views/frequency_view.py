import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
)

from ui.components.section_header import SectionHeader

from ui.components.control_card import (
    SliderControlCard,
)


class FrequencyView:
    """
    Feature 4 — Frequency Editor.

    UI responsibilities only.

    This view does NOT perform the DFT itself.

    main_window.py supplies callbacks for:

    - Show DFT spectrum
    - Reconstruct from DFT
    - Apply low-pass filter
    - Apply high-pass filter

    The current cutoff radius can be obtained using:

        get_cutoff_radius()
    """

    def __init__(
        self,
        on_show_spectrum,
        on_reconstruct,
        on_low_pass,
        on_high_pass,
    ):

        # =====================================================
        # CALLBACKS
        # =====================================================

        self.on_show_spectrum = (
            on_show_spectrum
        )

        self.on_reconstruct = (
            on_reconstruct
        )

        self.on_low_pass = (
            on_low_pass
        )

        self.on_high_pass = (
            on_high_pass
        )


        # =====================================================
        # STATE
        # =====================================================

        self.selected_filter = None


        # =====================================================
        # BUILD
        # =====================================================

        self.control = self._build()


    # =========================================================
    # BUILD PAGE
    # =========================================================

    def _build(self):

        # =====================================================
        # HEADER
        # =====================================================

        header = SectionHeader(

            badge="FEATURE 4",

            title="Frequency Editor",

            subtitle=(
                "Transform the image into the 2D frequency domain, "
                "inspect its spectrum and selectively preserve "
                "low- or high-frequency information."
            ),

            icon=ft.Icons.TUNE,

            accent=AppColors.CYAN,
        )


        # =====================================================
        # SIGNAL FLOW
        # =====================================================

        signal_flow = self._build_signal_flow()


        # =====================================================
        # MAIN WORK AREA
        # =====================================================

        main_controls = ft.ResponsiveRow(

            spacing=14,

            run_spacing=14,

            controls=[

                self._build_analysis_console(),

                self._build_filter_console(),
            ],
        )


        # =====================================================
        # EXPLANATION AREA
        # =====================================================

        frequency_guide = ft.ResponsiveRow(

            spacing=14,

            run_spacing=14,

            controls=[

                self._build_low_frequency_card(),

                self._build_high_frequency_card(),

                self._build_cutoff_guide(),
            ],
        )


        # =====================================================
        # FULL VIEW
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

                    signal_flow,

                    main_controls,

                    frequency_guide,
                ],
            ),
        )


    # =========================================================
    # SIGNAL FLOW
    # =========================================================

    def _build_signal_flow(self):

        return ft.Container(

            bgcolor="#09111D",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                16
            ),

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

                    self._flow_step(
                        icon=ft.Icons.IMAGE_OUTLINED,
                        title="Spatial Image",
                        subtitle="f(x, y)",
                        accent=AppColors.BLUE,
                    ),

                    self._flow_arrow(),

                    self._flow_step(
                        icon=ft.Icons.FUNCTIONS,
                        title="2D DFT",
                        subtitle="Transform",
                        accent=AppColors.CYAN,
                    ),

                    self._flow_arrow(),

                    self._flow_step(
                        icon=ft.Icons.BUBBLE_CHART,
                        title="Spectrum",
                        subtitle="F(u, v)",
                        accent=AppColors.PURPLE,
                    ),

                    self._flow_arrow(),

                    self._flow_step(
                        icon=ft.Icons.FILTER_ALT,
                        title="Filter",
                        subtitle="H(u, v)",
                        accent=AppColors.PINK,
                    ),

                    self._flow_arrow(),

                    self._flow_step(
                        icon=ft.Icons.REPLAY,
                        title="2D IDFT",
                        subtitle="Reconstruct",
                        accent=AppColors.GREEN,
                    ),

                    self._flow_arrow(),

                    self._flow_step(
                        icon=ft.Icons.IMAGE,
                        title="Result",
                        subtitle="g(x, y)",
                        accent=AppColors.ORANGE,
                    ),
                ],
            ),
        )


    # =========================================================
    # FLOW STEP
    # =========================================================

    def _flow_step(
        self,
        icon,
        title,
        subtitle,
        accent,
    ):

        return ft.Container(

            width=128,

            padding=12,

            bgcolor=AppColors.SURFACE_SOFT,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                14
            ),

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._hover_flow_step,

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
                            color=accent,
                            size=20,
                        ),
                    ),

                    ft.Text(
                        title,
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT,
                        text_align=ft.TextAlign.CENTER,
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


    # =========================================================
    # FLOW ARROW
    # =========================================================

    def _flow_arrow(self):

        return ft.Container(

            width=28,

            alignment=ft.Alignment.CENTER,

            content=ft.Icon(
                ft.Icons.ARROW_FORWARD_ROUNDED,
                size=18,
                color=AppColors.MUTED_2,
            ),
        )


    # =========================================================
    # ANALYSIS CONSOLE
    # =========================================================

    def _build_analysis_console(self):

        spectrum_action = self._large_action(

            title="View DFT Spectrum",

            subtitle=(
                "Display the centered log-magnitude "
                "frequency representation."
            ),

            icon=ft.Icons.BUBBLE_CHART,

            accent=AppColors.PURPLE,

            handler=self.on_show_spectrum,
        )


        reconstruction_action = self._large_action(

            title="Reconstruct Original",

            subtitle=(
                "Apply the inverse transform without "
                "discarding frequency coefficients."
            ),

            icon=ft.Icons.REPLAY,

            accent=AppColors.GREEN,

            handler=self.on_reconstruct,
        )


        container = ft.Container(

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

            border_radius=ft.BorderRadius.all(
                17
            ),

            padding=18,

            content=ft.Column(

                spacing=15,

                controls=[

                    self._console_title(

                        icon=ft.Icons.QUERY_STATS,

                        title="Frequency Analysis",

                        subtitle=(
                            "Inspect the transform before "
                            "changing its coefficients."
                        ),

                        accent=AppColors.PURPLE,
                    ),

                    spectrum_action,

                    reconstruction_action,
                ],
            ),
        )


        return container


    # =========================================================
    # FILTER CONSOLE
    # =========================================================

    def _build_filter_console(self):

        # =====================================================
        # SLIDER
        # =====================================================

        self.cutoff_control = SliderControlCard(

            title="Cutoff Radius",

            min_value=2,

            max_value=60,

            value=15,

            divisions=58,

            suffix=" px",

            accent=AppColors.CYAN,

            description=(
                "The radius controls the circular region "
                "around the center of the shifted spectrum."
            ),
        )


        # =====================================================
        # FILTER BUTTONS
        # =====================================================

        self.low_pass_card = self._filter_button(

            title="Low-Pass",

            subtitle=(
                "Keep low frequencies\n"
                "Suppress fine details"
            ),

            icon=ft.Icons.BLUR_ON,

            accent=AppColors.BLUE,

            handler=self._low_pass_clicked,

            filter_name="low",
        )


        self.high_pass_card = self._filter_button(

            title="High-Pass",

            subtitle=(
                "Keep high frequencies\n"
                "Emphasize fine details"
            ),

            icon=ft.Icons.FILTER_ALT,

            accent=AppColors.PINK,

            handler=self._high_pass_clicked,

            filter_name="high",
        )


        filter_buttons = ft.ResponsiveRow(

            spacing=10,

            run_spacing=10,

            controls=[

                self.low_pass_card,

                self.high_pass_card,
            ],
        )


        container = ft.Container(

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

            border_radius=ft.BorderRadius.all(
                17
            ),

            padding=18,

            content=ft.Column(

                spacing=15,

                controls=[

                    self._console_title(

                        icon=ft.Icons.TUNE,

                        title="Frequency Filter Console",

                        subtitle=(
                            "Choose a cutoff and decide which "
                            "frequency region survives."
                        ),

                        accent=AppColors.CYAN,
                    ),

                    self.cutoff_control.control,

                    filter_buttons,

                    self._build_filter_status(),
                ],
            ),
        )


        return container


    # =========================================================
    # CONSOLE TITLE
    # =========================================================

    def _console_title(
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

                    width=40,
                    height=40,

                    alignment=ft.Alignment.CENTER,

                    border_radius=12,

                    bgcolor=AppColors.SURFACE_3,

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
    # LARGE ACTION
    # =========================================================

    def _large_action(
        self,
        title,
        subtitle,
        icon,
        accent,
        handler,
    ):

        container = ft.Container(

            padding=15,

            bgcolor=AppColors.SURFACE_SOFT,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                15
            ),

            ink=True,

            on_click=handler,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._hover_action,

            data=accent,

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
                            icon,
                            size=24,
                            color=accent,
                        ),
                    ),

                    ft.Column(

                        spacing=3,

                        expand=True,

                        controls=[

                            ft.Text(
                                title,
                                size=12,
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

                    ft.Icon(
                        ft.Icons.ARROW_FORWARD_ROUNDED,
                        size=19,
                        color=accent,
                    ),
                ],
            ),
        )


        return container


    # =========================================================
    # FILTER BUTTON
    # =========================================================

    def _filter_button(
        self,
        title,
        subtitle,
        icon,
        accent,
        handler,
        filter_name,
    ):

        container = ft.Container(

            col={
                "xs": 12,
                "sm": 6,
            },

            padding=14,

            bgcolor=AppColors.SURFACE_SOFT,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                15
            ),

            ink=True,

            on_click=handler,

            on_hover=self._hover_filter,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            data={
                "accent": accent,
                "filter": filter_name,
            },

            content=ft.Column(

                spacing=10,

                controls=[

                    ft.Row(

                        controls=[

                            ft.Container(

                                width=42,
                                height=42,

                                alignment=ft.Alignment.CENTER,

                                border_radius=13,

                                bgcolor=AppColors.SURFACE_3,

                                content=ft.Icon(
                                    icon,
                                    color=accent,
                                    size=22,
                                ),
                            ),

                            ft.Container(
                                expand=True
                            ),

                            ft.Icon(
                                ft.Icons.PLAY_ARROW_ROUNDED,
                                color=accent,
                                size=23,
                            ),
                        ],
                    ),

                    ft.Text(
                        title,
                        size=12,
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
        )


        return container


    # =========================================================
    # FILTER STATUS
    # =========================================================

    def _build_filter_status(self):

        self.filter_status_icon = ft.Icon(
            ft.Icons.RADIO_BUTTON_UNCHECKED,
            size=16,
            color=AppColors.MUTED_2,
        )


        self.filter_status_text = ft.Text(
            "Choose Low-Pass or High-Pass to process the image.",
            size=10,
            color=AppColors.MUTED,
            expand=True,
        )


        return ft.Container(

            bgcolor="#09111D",

            border_radius=ft.BorderRadius.all(
                12
            ),

            padding=12,

            content=ft.Row(

                spacing=9,

                controls=[

                    self.filter_status_icon,

                    self.filter_status_text,
                ],
            ),
        )


    # =========================================================
    # LOW FREQUENCY GUIDE
    # =========================================================

    def _build_low_frequency_card(self):

        return self._frequency_concept_card(

            title="Low Frequencies",

            badge="CENTER",

            subtitle=(
                "Broad intensity changes and large image structures."
            ),

            explanation=(
                "A low-pass filter preserves the central "
                "frequency region and removes much of the "
                "fine detail."
            ),

            accent=AppColors.BLUE,

            center=True,

            col={
                "xs": 12,
                "sm": 6,
                "lg": 4,
            },
        )


    # =========================================================
    # HIGH FREQUENCY GUIDE
    # =========================================================

    def _build_high_frequency_card(self):

        return self._frequency_concept_card(

            title="High Frequencies",

            badge="OUTER",

            subtitle=(
                "Rapid pixel changes, edges and small image details."
            ),

            explanation=(
                "A high-pass filter suppresses the spectrum "
                "center while preserving components farther away."
            ),

            accent=AppColors.PINK,

            center=False,

            col={
                "xs": 12,
                "sm": 6,
                "lg": 4,
            },
        )


    # =========================================================
    # CUTOFF GUIDE
    # =========================================================

    def _build_cutoff_guide(self):

        return ft.Container(

            col={
                "xs": 12,
                "sm": 12,
                "lg": 4,
            },

            bgcolor="#09111D",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                16
            ),

            padding=16,

            content=ft.Column(

                spacing=12,

                controls=[

                    ft.Row(

                        controls=[

                            ft.Container(

                                width=42,
                                height=42,

                                alignment=ft.Alignment.CENTER,

                                border_radius=13,

                                gradient=ft.LinearGradient(
                                    begin=ft.Alignment.TOP_LEFT,
                                    end=ft.Alignment.BOTTOM_RIGHT,
                                    colors=[
                                        "#123248",
                                        "#251D46",
                                    ],
                                ),

                                content=ft.Icon(
                                    ft.Icons.RADAR,
                                    color=AppColors.CYAN,
                                    size=23,
                                ),
                            ),

                            ft.Column(

                                spacing=2,

                                controls=[

                                    ft.Text(
                                        "Cutoff Radius",
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.TEXT,
                                    ),

                                    ft.Text(
                                        "Your main frequency control",
                                        size=9,
                                        color=AppColors.MUTED,
                                    ),
                                ],
                            ),
                        ],
                    ),

                    ft.Text(
                        (
                            "Smaller radius → stronger frequency filtering.\n"
                            "Larger radius → more frequencies remain available."
                        ),
                        size=10,
                        color=AppColors.MUTED,
                    ),

                    ft.Container(

                        bgcolor=AppColors.SURFACE_SOFT,

                        border_radius=12,

                        padding=12,

                        content=ft.Row(

                            controls=[

                                ft.Text(
                                    "2 px",
                                    size=9,
                                    color=AppColors.MUTED_2,
                                ),

                                ft.Container(
                                    expand=True,
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

                                ft.Text(
                                    "60 px",
                                    size=9,
                                    color=AppColors.MUTED_2,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )


    # =========================================================
    # FREQUENCY CONCEPT CARD
    # =========================================================

    def _frequency_concept_card(
        self,
        title,
        badge,
        subtitle,
        explanation,
        accent,
        center,
        col,
    ):

        spectrum_visual = (
            self._low_frequency_visual(
                accent
            )
            if center
            else self._high_frequency_visual(
                accent
            )
        )


        return ft.Container(

            col=col,

            bgcolor="#09111D",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                16
            ),

            padding=16,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._hover_concept,

            data=accent,

            content=ft.Column(

                spacing=11,

                controls=[

                    ft.Row(

                        controls=[

                            ft.Text(
                                title,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),

                            ft.Container(
                                expand=True
                            ),

                            ft.Container(

                                padding=ft.Padding.symmetric(
                                    horizontal=8,
                                    vertical=4,
                                ),

                                border_radius=100,

                                bgcolor=AppColors.SURFACE_3,

                                content=ft.Text(
                                    badge,
                                    size=8,
                                    weight=ft.FontWeight.BOLD,
                                    color=accent,
                                ),
                            ),
                        ],
                    ),

                    spectrum_visual,

                    ft.Text(
                        subtitle,
                        size=10,
                        weight=ft.FontWeight.W_600,
                        color=accent,
                    ),

                    ft.Text(
                        explanation,
                        size=9,
                        color=AppColors.MUTED,
                    ),
                ],
            ),
        )


    # =========================================================
    # LOW FREQUENCY VISUAL
    # =========================================================

    def _low_frequency_visual(
        self,
        accent,
    ):

        return ft.Container(

            height=105,

            alignment=ft.Alignment.CENTER,

            bgcolor="#050A12",

            border_radius=14,

            content=ft.Stack(

                width=110,
                height=100,

                controls=[

                    self._spectrum_ring(
                        100,
                        "#233149",
                    ),

                    ft.Container(
                        left=15,
                        top=15,
                        content=self._spectrum_ring(
                            70,
                            "#2D3D59",
                        ),
                    ),

                    ft.Container(
                        left=32,
                        top=32,
                        width=36,
                        height=36,
                        border_radius=18,
                        bgcolor=accent,
                        opacity=0.85,
                    ),

                    ft.Container(
                        left=43,
                        top=43,
                        width=14,
                        height=14,
                        border_radius=7,
                        bgcolor=AppColors.WHITE,
                    ),
                ],
            ),
        )


    # =========================================================
    # HIGH FREQUENCY VISUAL
    # =========================================================

    def _high_frequency_visual(
        self,
        accent,
    ):

        dots = []


        positions = [

            (10, 16),
            (73, 12),
            (18, 70),
            (76, 68),
            (45, 6),
            (8, 45),
            (86, 42),
            (47, 80),
        ]


        for x, y in positions:

            dots.append(

                ft.Container(

                    left=x,
                    top=y,

                    width=8,
                    height=8,

                    border_radius=4,

                    bgcolor=accent,
                )
            )


        dots.append(

            ft.Container(

                left=37,
                top=37,

                width=26,
                height=26,

                border_radius=13,

                border=ft.Border.all(
                    1,
                    "#3C475B",
                ),

                bgcolor="#07101B",
            )
        )


        return ft.Container(

            height=105,

            alignment=ft.Alignment.CENTER,

            bgcolor="#050A12",

            border_radius=14,

            content=ft.Stack(

                width=100,
                height=95,

                controls=dots,
            ),
        )


    # =========================================================
    # SPECTRUM RING
    # =========================================================

    def _spectrum_ring(
        self,
        size,
        color,
    ):

        return ft.Container(

            width=size,
            height=size,

            border_radius=size / 2,

            border=ft.Border.all(
                1,
                color,
            ),
        )


    # =========================================================
    # LOW PASS CLICK
    # =========================================================

    def _low_pass_clicked(
        self,
        e,
    ):

        self.selected_filter = "low"


        self.filter_status_icon.name = (
            ft.Icons.BLUR_ON
        )

        self.filter_status_icon.color = (
            AppColors.BLUE
        )


        self.filter_status_text.value = (
            f"Low-Pass selected • "
            f"Radius {self.get_cutoff_radius()} px"
        )


        self.filter_status_text.color = (
            AppColors.BLUE_LIGHT
        )


        self.filter_status_icon.update()

        self.filter_status_text.update()


        if self.on_low_pass:

            self.on_low_pass(e)


    # =========================================================
    # HIGH PASS CLICK
    # =========================================================

    def _high_pass_clicked(
        self,
        e,
    ):

        self.selected_filter = "high"


        self.filter_status_icon.name = (
            ft.Icons.FILTER_ALT
        )

        self.filter_status_icon.color = (
            AppColors.PINK
        )


        self.filter_status_text.value = (
            f"High-Pass selected • "
            f"Radius {self.get_cutoff_radius()} px"
        )


        self.filter_status_text.color = (
            AppColors.PINK_LIGHT
        )


        self.filter_status_icon.update()

        self.filter_status_text.update()


        if self.on_high_pass:

            self.on_high_pass(e)


    # =========================================================
    # GET CUTOFF
    # =========================================================

    def get_cutoff_radius(
        self,
    ):

        return (
            self.cutoff_control
            .get_int_value()
        )


    # =========================================================
    # SET CUTOFF
    # =========================================================

    def set_cutoff_radius(
        self,
        value,
    ):

        self.cutoff_control.set_value(
            value
        )


    # =========================================================
    # HOVER — FLOW
    # =========================================================

    def _hover_flow_step(
        self,
        e,
    ):

        accent = e.control.data


        if e.data:

            e.control.scale = 1.04

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
    # HOVER — ACTION
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


    # =========================================================
    # HOVER — FILTER
    # =========================================================

    def _hover_filter(
        self,
        e,
    ):

        accent = e.control.data[
            "accent"
        ]


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
    # HOVER — CONCEPT
    # =========================================================

    def _hover_concept(
        self,
        e,
    ):

        accent = e.control.data


        if e.data:

            e.control.scale = 1.012

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
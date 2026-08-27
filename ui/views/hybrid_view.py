import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
)

from ui.components.section_header import (
    SectionHeader,
)

from ui.components.control_card import (
    SliderControlCard,
)


class HybridView:
    """
    Feature 9 — Hybrid Images.

    UI responsibilities:
    - Select low-frequency source image
    - Select high-frequency source image
    - Preview both sources
    - Control low-pass radius
    - Control high-pass radius
    - Trigger hybrid generation
    - Display source/fusion status
    - Explain near/far hybrid perception

    The actual DFT processing stays outside this view.
    """

    def __init__(
        self,
        on_select_low,
        on_select_high,
        on_create_hybrid,
    ):

        # =====================================================
        # CALLBACKS
        # =====================================================

        self.on_select_low = (
            on_select_low
        )

        self.on_select_high = (
            on_select_high
        )

        self.on_create_hybrid = (
            on_create_hybrid
        )


        # =====================================================
        # STATE
        # =====================================================

        self.low_source_ready = False

        self.high_source_ready = False

        self.low_source_name = None

        self.high_source_name = None


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

            badge="FEATURE 4",

            title="Hybrid Image Studio",

            subtitle=(
                "Blend the broad low-frequency structure of one "
                "image with the fine high-frequency detail of another "
                "to create an image whose perception changes with distance."
            ),

            icon=ft.Icons.AUTO_AWESOME,

            accent=AppColors.PINK,
        )


        # =====================================================
        # PIPELINE
        # =====================================================

        pipeline = self._build_pipeline()


        # =====================================================
        # SOURCE LAB
        # =====================================================

        source_area = self._build_source_area()


        # =====================================================
        # FREQUENCY CONTROLS
        # =====================================================

        frequency_controls = (
            self._build_frequency_controls()
        )


        # =====================================================
        # FUSION ACTION
        # =====================================================

        fusion_action = (
            self._build_fusion_action()
        )


        # =====================================================
        # DISTANCE EXPLANATION
        # =====================================================

        distance_demo = (
            self._build_distance_demo()
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

                    source_area,

                    frequency_controls,

                    fusion_action,

                    distance_demo,
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

                    self._pipeline_source(
                        ft.Icons.IMAGE_OUTLINED,
                        "Image A",
                        "Low frequencies",
                        AppColors.BLUE,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_source(
                        ft.Icons.BLUR_ON,
                        "Low-Pass",
                        "Broad structure",
                        AppColors.BLUE_LIGHT,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_fusion(),

                    self._pipeline_arrow(),

                    self._pipeline_source(
                        ft.Icons.FILTER_ALT,
                        "High-Pass",
                        "Fine detail",
                        AppColors.PINK,
                    ),

                    self._pipeline_arrow(),

                    self._pipeline_source(
                        ft.Icons.IMAGE_OUTLINED,
                        "Image B",
                        "High frequencies",
                        AppColors.PINK_LIGHT,
                    ),
                ],
            ),
        )


    # =========================================================
    # PIPELINE SOURCE
    # =========================================================

    def _pipeline_source(
        self,
        icon,
        title,
        subtitle,
        accent,
    ):

        return ft.Container(

            width=140,

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


    # =========================================================
    # PIPELINE FUSION
    # =========================================================

    def _pipeline_fusion(self):

        return ft.Container(

            width=155,

            padding=12,

            gradient=ft.LinearGradient(

                begin=ft.Alignment.TOP_LEFT,

                end=ft.Alignment.BOTTOM_RIGHT,

                colors=[
                    "#10233D",
                    "#25152F",
                ],
            ),

            border=ft.Border.all(
                1,
                AppColors.PURPLE,
            ),

            border_radius=14,

            content=ft.Column(

                spacing=6,

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                controls=[

                    ft.Container(

                        width=42,
                        height=42,

                        alignment=ft.Alignment.CENTER,

                        border_radius=21,

                        gradient=ft.LinearGradient(

                            begin=ft.Alignment.TOP_LEFT,

                            end=ft.Alignment.BOTTOM_RIGHT,

                            colors=[
                                AppColors.BLUE,
                                AppColors.PURPLE,
                                AppColors.PINK,
                            ],
                        ),

                        content=ft.Icon(
                            ft.Icons.AUTO_AWESOME,
                            size=21,
                            color=AppColors.WHITE,
                        ),
                    ),

                    ft.Text(
                        "Frequency Fusion",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT,
                    ),

                    ft.Text(
                        "Low + High",
                        size=9,
                        color=AppColors.PURPLE_LIGHT,
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
    # SOURCE AREA
    # =========================================================

    def _build_source_area(self):

        # =====================================================
        # LOW SOURCE
        # =====================================================

        self.low_preview = (
            self._source_placeholder(
                AppColors.BLUE,
                ft.Icons.LANDSCAPE_OUTLINED,
            )
        )


        self.low_preview_container = ft.Container(

            height=205,

            alignment=ft.Alignment.CENTER,

            bgcolor="#07101D",

            border_radius=16,

            border=ft.Border.all(
                1,
                "#173B69",
            ),

            content=self.low_preview,
        )


        self.low_name_text = ft.Text(

            "No Image A selected",

            size=11,

            weight=ft.FontWeight.W_600,

            color=AppColors.MUTED,

            max_lines=1,

            overflow=ft.TextOverflow.ELLIPSIS,
        )


        self.low_status_dot = ft.Container(

            width=8,
            height=8,

            border_radius=100,

            bgcolor=AppColors.MUTED_DARK,
        )


        low_card = self._source_card(

            title="IMAGE A",

            frequency_label="LOW-FREQUENCY SOURCE",

            description=(
                "Provides broad shapes, lighting and "
                "large-scale visual structure."
            ),

            accent=AppColors.BLUE,

            icon=ft.Icons.BLUR_ON,

            preview=self.low_preview_container,

            name_control=self.low_name_text,

            status_dot=self.low_status_dot,

            button_text="Choose Image A",

            handler=self.on_select_low,

            col={
                "xs": 12,
                "sm": 12,
                "md": 5,
            },
        )


        # =====================================================
        # HIGH SOURCE
        # =====================================================

        self.high_preview = (
            self._source_placeholder(
                AppColors.PINK,
                ft.Icons.DETAILS_OUTLINED,
            )
        )


        self.high_preview_container = ft.Container(

            height=205,

            alignment=ft.Alignment.CENTER,

            bgcolor="#160A15",

            border_radius=16,

            border=ft.Border.all(
                1,
                "#632247",
            ),

            content=self.high_preview,
        )


        self.high_name_text = ft.Text(

            "No Image B selected",

            size=11,

            weight=ft.FontWeight.W_600,

            color=AppColors.MUTED,

            max_lines=1,

            overflow=ft.TextOverflow.ELLIPSIS,
        )


        self.high_status_dot = ft.Container(

            width=8,
            height=8,

            border_radius=100,

            bgcolor=AppColors.MUTED_DARK,
        )


        high_card = self._source_card(

            title="IMAGE B",

            frequency_label="HIGH-FREQUENCY SOURCE",

            description=(
                "Provides edges, texture and fine "
                "high-frequency visual detail."
            ),

            accent=AppColors.PINK,

            icon=ft.Icons.FILTER_ALT,

            preview=self.high_preview_container,

            name_control=self.high_name_text,

            status_dot=self.high_status_dot,

            button_text="Choose Image B",

            handler=self.on_select_high,

            col={
                "xs": 12,
                "sm": 12,
                "md": 5,
            },
        )


        # =====================================================
        # CENTRAL FUSION CORE
        # =====================================================

        fusion_core = ft.Container(

            col={
                "xs": 12,
                "sm": 12,
                "md": 2,
            },

            alignment=ft.Alignment.CENTER,

            content=self._build_fusion_core(),
        )


        return ft.ResponsiveRow(

            spacing=14,

            run_spacing=14,

            vertical_alignment=(
                ft.CrossAxisAlignment.CENTER
            ),

            controls=[

                low_card,

                fusion_core,

                high_card,
            ],
        )


    # =========================================================
    # SOURCE CARD
    # =========================================================

    def _source_card(
        self,
        title,
        frequency_label,
        description,
        accent,
        icon,
        preview,
        name_control,
        status_dot,
        button_text,
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

            border_radius=18,

            padding=16,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._hover_card,

            data=accent,

            content=ft.Column(

                spacing=13,

                controls=[

                    # Header

                    ft.Row(

                        controls=[

                            ft.Container(

                                width=43,
                                height=43,

                                alignment=ft.Alignment.CENTER,

                                border_radius=13,

                                bgcolor=AppColors.SURFACE_3,

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
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.TEXT,
                                    ),

                                    ft.Text(
                                        frequency_label,
                                        size=8,
                                        weight=ft.FontWeight.BOLD,
                                        color=accent,
                                    ),
                                ],
                            ),

                            status_dot,
                        ],
                    ),


                    # Preview

                    preview,


                    # Filename

                    ft.Container(

                        padding=ft.Padding.symmetric(
                            horizontal=10,
                            vertical=8,
                        ),

                        bgcolor=AppColors.SURFACE_SOFT,

                        border_radius=10,

                        content=ft.Row(

                            spacing=8,

                            controls=[

                                ft.Icon(
                                    ft.Icons.INSERT_DRIVE_FILE_OUTLINED,
                                    size=15,
                                    color=accent,
                                ),

                                ft.Container(
                                    expand=True,
                                    content=name_control,
                                ),
                            ],
                        ),
                    ),


                    # Description

                    ft.Text(
                        description,
                        size=9,
                        color=AppColors.MUTED,
                    ),


                    # Choose button

                    ft.OutlinedButton(

                        content=button_text,

                        icon=ft.Icons.FOLDER_OPEN,

                        on_click=handler,

                        style=ft.ButtonStyle(
                            color=accent,
                            side=ft.BorderSide(
                                1,
                                accent,
                            ),
                        ),
                    ),
                ],
            ),
        )


    # =========================================================
    # SOURCE PLACEHOLDER
    # =========================================================

    def _source_placeholder(
        self,
        accent,
        icon,
    ):

        return ft.Column(

            tight=True,

            spacing=9,

            horizontal_alignment=(
                ft.CrossAxisAlignment.CENTER
            ),

            controls=[

                ft.Container(

                    width=66,
                    height=66,

                    alignment=ft.Alignment.CENTER,

                    border_radius=20,

                    bgcolor=AppColors.SURFACE_3,

                    border=ft.Border.all(
                        1,
                        AppColors.BORDER,
                    ),

                    content=ft.Icon(
                        icon,
                        size=31,
                        color=accent,
                    ),
                ),

                ft.Text(
                    "Waiting for source",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=AppColors.MUTED,
                ),

                ft.Text(
                    "Choose an image",
                    size=9,
                    color=AppColors.MUTED_2,
                ),
            ],
        )


    # =========================================================
    # FUSION CORE
    # =========================================================

    def _build_fusion_core(self):

        self.fusion_core_icon = ft.Icon(

            ft.Icons.LINK,

            size=31,

            color=AppColors.MUTED,
        )


        self.fusion_core_text = ft.Text(

            "0 / 2",

            size=15,

            weight=ft.FontWeight.BOLD,

            color=AppColors.MUTED,
        )


        self.fusion_core_status = ft.Text(

            "SOURCES",

            size=8,

            weight=ft.FontWeight.BOLD,

            color=AppColors.MUTED_2,
        )


        self.fusion_core_container = ft.Container(

            width=115,
            height=115,

            alignment=ft.Alignment.CENTER,

            border_radius=58,

            border=ft.Border.all(
                1,
                AppColors.BORDER_LIGHT,
            ),

            gradient=ft.RadialGradient(

                colors=[
                    "#1A2440",
                    "#121629",
                    "#090D17",
                ],
            ),

            animate_scale=ft.Animation(

                duration=AppAnimations.NORMAL,

                curve=ft.AnimationCurve.EASE_OUT,
            ),

            content=ft.Column(

                tight=True,

                spacing=3,

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                controls=[

                    self.fusion_core_icon,

                    self.fusion_core_text,

                    self.fusion_core_status,
                ],
            ),
        )


        return ft.Column(

            spacing=10,

            horizontal_alignment=(
                ft.CrossAxisAlignment.CENTER
            ),

            controls=[

                ft.Text(
                    "FUSION",
                    size=9,
                    weight=ft.FontWeight.BOLD,
                    color=AppColors.PURPLE_LIGHT,
                ),

                self.fusion_core_container,

                ft.Text(
                    "A + B",
                    size=10,
                    color=AppColors.MUTED,
                ),
            ],
        )


    # =========================================================
    # FREQUENCY CONTROLS
    # =========================================================

    def _build_frequency_controls(self):

        # =====================================================
        # LOW RADIUS
        # =====================================================

        self.low_radius_control = (
            SliderControlCard(

                title="Low-Pass Radius",

                min_value=2,

                max_value=50,

                value=15,

                divisions=48,

                suffix=" px",

                accent=AppColors.BLUE,

                on_change=self._on_low_radius_change,

                description=(
                    "Controls how much central low-frequency "
                    "content is preserved from Image A."
                ),
            )
        )


        # =====================================================
        # HIGH RADIUS
        # =====================================================

        self.high_radius_control = (
            SliderControlCard(

                title="High-Pass Radius",

                min_value=2,

                max_value=50,

                value=15,

                divisions=48,

                suffix=" px",

                accent=AppColors.PINK,

                on_change=self._on_high_radius_change,

                description=(
                    "Controls the central region removed from "
                    "Image B before retaining its high frequencies."
                ),
            )
        )


        # =====================================================
        # LIVE LABELS
        # =====================================================

        self.low_frequency_text = ft.Text(

            "r = 15 px",

            size=12,

            weight=ft.FontWeight.BOLD,

            color=AppColors.BLUE_LIGHT,
        )


        self.high_frequency_text = ft.Text(

            "r = 15 px",

            size=12,

            weight=ft.FontWeight.BOLD,

            color=AppColors.PINK_LIGHT,
        )


        low_panel = ft.Container(

            col={
                "xs": 12,
                "sm": 6,
            },

            content=ft.Column(

                spacing=10,

                controls=[

                    self.low_radius_control.control,

                    self._frequency_role(

                        title="STRUCTURE",

                        value_control=(
                            self.low_frequency_text
                        ),

                        icon=ft.Icons.BLUR_ON,

                        accent=AppColors.BLUE,

                        description=(
                            "Low frequencies dominate perception "
                            "from farther viewing distances."
                        ),
                    ),
                ],
            ),
        )


        high_panel = ft.Container(

            col={
                "xs": 12,
                "sm": 6,
            },

            content=ft.Column(

                spacing=10,

                controls=[

                    self.high_radius_control.control,

                    self._frequency_role(

                        title="DETAIL",

                        value_control=(
                            self.high_frequency_text
                        ),

                        icon=ft.Icons.GRAIN,

                        accent=AppColors.PINK,

                        description=(
                            "High frequencies dominate fine "
                            "detail when viewed up close."
                        ),
                    ),
                ],
            ),
        )


        return ft.Column(

            spacing=12,

            controls=[

                ft.Row(

                    controls=[

                        ft.Text(
                            "Frequency Mixing Controls",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.TEXT,
                        ),

                        ft.Container(
                            expand=True
                        ),

                        ft.Container(

                            padding=ft.Padding.symmetric(
                                horizontal=10,
                                vertical=5,
                            ),

                            border_radius=100,

                            bgcolor="#151226",

                            content=ft.Text(
                                "DUAL DFT CONTROL",
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
                        low_panel,
                        high_panel,
                    ],
                ),
            ],
        )


    # =========================================================
    # FREQUENCY ROLE
    # =========================================================

    def _frequency_role(
        self,
        title,
        value_control,
        icon,
        accent,
        description,
    ):

        return ft.Container(

            bgcolor="#09111D",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=14,

            padding=13,

            content=ft.Row(

                spacing=11,

                controls=[

                    ft.Container(

                        width=41,
                        height=41,

                        alignment=ft.Alignment.CENTER,

                        border_radius=13,

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

                            ft.Row(

                                controls=[

                                    ft.Text(
                                        title,
                                        size=9,
                                        weight=ft.FontWeight.BOLD,
                                        color=accent,
                                    ),

                                    ft.Container(
                                        expand=True
                                    ),

                                    value_control,
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
    # FUSION ACTION
    # =========================================================

    def _build_fusion_action(self):

        self.fusion_status_icon = ft.Icon(

            ft.Icons.RADIO_BUTTON_UNCHECKED,

            size=17,

            color=AppColors.MUTED_2,
        )


        self.fusion_status_text = ft.Text(

            "Select both Image A and Image B to unlock frequency fusion.",

            size=10,

            color=AppColors.MUTED,

            expand=True,
        )


        self.create_button = ft.Container(

            padding=16,

            border_radius=16,

            gradient=ft.LinearGradient(

                begin=ft.Alignment.CENTER_LEFT,

                end=ft.Alignment.CENTER_RIGHT,

                colors=[
                    "#173D70",
                    "#4A2381",
                    "#7B254E",
                ],
            ),

            border=ft.Border.all(
                1,
                "#704C9E",
            ),

            ink=True,

            on_click=self.on_create_hybrid,

            on_hover=self._hover_create,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            content=ft.Row(

                spacing=14,

                controls=[

                    ft.Container(

                        width=50,
                        height=50,

                        alignment=ft.Alignment.CENTER,

                        border_radius=16,

                        bgcolor="#33000000",

                        content=ft.Icon(
                            ft.Icons.AUTO_AWESOME,
                            size=26,
                            color=AppColors.WHITE,
                        ),
                    ),

                    ft.Column(

                        spacing=3,

                        expand=True,

                        controls=[

                            ft.Text(
                                "Create Hybrid Image",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.WHITE,
                            ),

                            ft.Text(
                                (
                                    "Transform both images, isolate their "
                                    "frequency components and fuse them."
                                ),
                                size=10,
                                color="#DDD6FE",
                            ),
                        ],
                    ),

                    ft.Icon(
                        ft.Icons.ARROW_FORWARD_ROUNDED,
                        size=23,
                        color=AppColors.WHITE,
                    ),
                ],
            ),
        )


        status = ft.Container(

            padding=12,

            bgcolor="#09111D",

            border_radius=12,

            content=ft.Row(

                spacing=9,

                controls=[

                    self.fusion_status_icon,

                    self.fusion_status_text,
                ],
            ),
        )


        return ft.Container(

            bgcolor="#0C1422",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=17,

            padding=17,

            content=ft.Column(

                spacing=12,

                controls=[

                    self.create_button,

                    status,
                ],
            ),
        )


    # =========================================================
    # DISTANCE DEMO
    # =========================================================

    def _build_distance_demo(self):

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

                    # Header

                    ft.Row(

                        controls=[

                            ft.Container(

                                width=42,
                                height=42,

                                alignment=ft.Alignment.CENTER,

                                border_radius=13,

                                bgcolor=AppColors.SURFACE_3,

                                content=ft.Icon(
                                    ft.Icons.VISIBILITY_OUTLINED,
                                    color=AppColors.PURPLE_LIGHT,
                                    size=22,
                                ),
                            ),

                            ft.Column(

                                spacing=2,

                                expand=True,

                                controls=[

                                    ft.Text(
                                        "The Hybrid Perception Effect",
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.TEXT,
                                    ),

                                    ft.Text(
                                        (
                                            "Different frequency bands dominate "
                                            "our perception at different viewing scales."
                                        ),
                                        size=10,
                                        color=AppColors.MUTED,
                                    ),
                                ],
                            ),
                        ],
                    ),


                    # Near/far cards

                    ft.ResponsiveRow(

                        spacing=12,

                        run_spacing=12,

                        controls=[

                            self._distance_card(

                                title="VIEW UP CLOSE",

                                subtitle="HIGH FREQUENCIES",

                                description=(
                                    "Edges and fine detail from Image B "
                                    "are easier to perceive."
                                ),

                                icon=ft.Icons.ZOOM_IN,

                                accent=AppColors.PINK,

                                scale_label="NEAR",

                                col={
                                    "xs": 12,
                                    "sm": 6,
                                },
                            ),

                            self._distance_card(

                                title="VIEW FROM FAR AWAY",

                                subtitle="LOW FREQUENCIES",

                                description=(
                                    "Fine details become less noticeable and "
                                    "the broad structure of Image A dominates."
                                ),

                                icon=ft.Icons.ZOOM_OUT,

                                accent=AppColors.BLUE,

                                scale_label="FAR",

                                col={
                                    "xs": 12,
                                    "sm": 6,
                                },
                            ),
                        ],
                    ),
                ],
            ),
        )


    # =========================================================
    # DISTANCE CARD
    # =========================================================

    def _distance_card(
        self,
        title,
        subtitle,
        description,
        icon,
        accent,
        scale_label,
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

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._hover_card,

            data=accent,

            content=ft.Row(

                spacing=13,

                controls=[

                    ft.Container(

                        width=60,
                        height=60,

                        alignment=ft.Alignment.CENTER,

                        border_radius=18,

                        bgcolor=AppColors.SURFACE_3,

                        content=ft.Icon(
                            icon,
                            size=29,
                            color=accent,
                        ),
                    ),

                    ft.Column(

                        spacing=3,

                        expand=True,

                        controls=[

                            ft.Row(

                                controls=[

                                    ft.Text(
                                        title,
                                        size=10,
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
                                            scale_label,
                                            size=8,
                                            weight=ft.FontWeight.BOLD,
                                            color=accent,
                                        ),
                                    ),
                                ],
                            ),

                            ft.Text(
                                subtitle,
                                size=9,
                                weight=ft.FontWeight.BOLD,
                                color=accent,
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
    # LOW RADIUS CHANGE
    # =========================================================

    def _on_low_radius_change(
        self,
        e,
    ):

        value = int(
            e.control.value
        )


        self.low_frequency_text.value = (
            f"r = {value} px"
        )


        self.low_frequency_text.update()


    # =========================================================
    # HIGH RADIUS CHANGE
    # =========================================================

    def _on_high_radius_change(
        self,
        e,
    ):

        value = int(
            e.control.value
        )


        self.high_frequency_text.value = (
            f"r = {value} px"
        )


        self.high_frequency_text.update()


    # =========================================================
    # PUBLIC — LOW SOURCE
    # =========================================================

    def update_low_source(
        self,
        image_name,
        image_bytes,
    ):

        self.low_source_ready = True

        self.low_source_name = (
            image_name
        )


        self.low_name_text.value = (
            image_name
        )


        self.low_name_text.color = (
            AppColors.TEXT
        )


        self.low_preview_container.content = (
            ft.Image(

                src=image_bytes,

                width=420,

                height=205,

                fit=ft.BoxFit.COVER,

                border_radius=16,

                gapless_playback=True,
            )
        )


        self.low_status_dot.bgcolor = (
            AppColors.BLUE
        )


        self.low_preview_container.border = (
            ft.Border.all(
                1,
                AppColors.BLUE,
            )
        )


        self.low_name_text.update()

        self.low_preview_container.update()

        self.low_status_dot.update()


        self._update_source_state()


    # =========================================================
    # PUBLIC — HIGH SOURCE
    # =========================================================

    def update_high_source(
        self,
        image_name,
        image_bytes,
    ):

        self.high_source_ready = True

        self.high_source_name = (
            image_name
        )


        self.high_name_text.value = (
            image_name
        )


        self.high_name_text.color = (
            AppColors.TEXT
        )


        self.high_preview_container.content = (
            ft.Image(

                src=image_bytes,

                width=420,

                height=205,

                fit=ft.BoxFit.COVER,

                border_radius=16,

                gapless_playback=True,
            )
        )


        self.high_status_dot.bgcolor = (
            AppColors.PINK
        )


        self.high_preview_container.border = (
            ft.Border.all(
                1,
                AppColors.PINK,
            )
        )


        self.high_name_text.update()

        self.high_preview_container.update()

        self.high_status_dot.update()


        self._update_source_state()


    # =========================================================
    # UPDATE SOURCE STATE
    # =========================================================

    def _update_source_state(
        self,
    ):

        count = (
            int(self.low_source_ready)
            +
            int(self.high_source_ready)
        )


        self.fusion_core_text.value = (
            f"{count} / 2"
        )


        # =====================================================
        # ZERO SOURCES
        # =====================================================

        if count == 0:

            self.fusion_core_icon.name = (
                ft.Icons.LINK
            )

            self.fusion_core_icon.color = (
                AppColors.MUTED
            )

            self.fusion_core_status.value = (
                "SOURCES"
            )

            self.fusion_status_icon.name = (
                ft.Icons.RADIO_BUTTON_UNCHECKED
            )

            self.fusion_status_icon.color = (
                AppColors.MUTED_2
            )

            self.fusion_status_text.value = (
                "Select both Image A and Image B "
                "to unlock frequency fusion."
            )

            self.fusion_status_text.color = (
                AppColors.MUTED
            )


        # =====================================================
        # ONE SOURCE
        # =====================================================

        elif count == 1:

            self.fusion_core_icon.name = (
                ft.Icons.LINK
            )

            self.fusion_core_icon.color = (
                AppColors.PURPLE_LIGHT
            )

            self.fusion_core_status.value = (
                "ONE MORE"
            )

            self.fusion_status_icon.name = (
                ft.Icons.HOURGLASS_TOP
            )

            self.fusion_status_icon.color = (
                AppColors.ORANGE
            )

            self.fusion_status_text.value = (
                "One source is ready. Select the second "
                "image to complete the hybrid pair."
            )

            self.fusion_status_text.color = (
                AppColors.ORANGE_LIGHT
            )


        # =====================================================
        # BOTH SOURCES
        # =====================================================

        else:

            self.fusion_core_icon.name = (
                ft.Icons.AUTO_AWESOME
            )

            self.fusion_core_icon.color = (
                AppColors.WHITE
            )

            self.fusion_core_status.value = (
                "READY"
            )

            self.fusion_core_container.border = (
                ft.Border.all(
                    1,
                    AppColors.PURPLE,
                )
            )

            self.fusion_core_container.scale = (
                1.06
            )

            self.fusion_status_icon.name = (
                ft.Icons.CHECK_CIRCLE
            )

            self.fusion_status_icon.color = (
                AppColors.GREEN
            )

            self.fusion_status_text.value = (
                "Both sources are ready. Tune the two "
                "cutoff radii and create the hybrid."
            )

            self.fusion_status_text.color = (
                AppColors.GREEN_LIGHT
            )


        self.fusion_core_text.update()

        self.fusion_core_icon.update()

        self.fusion_core_status.update()

        self.fusion_core_container.update()

        self.fusion_status_icon.update()

        self.fusion_status_text.update()


    # =========================================================
    # PUBLIC — MARK RESULT CREATED
    # =========================================================

    def show_created_status(
        self,
    ):

        low_radius = (
            self.get_low_radius()
        )

        high_radius = (
            self.get_high_radius()
        )


        self.fusion_status_icon.name = (
            ft.Icons.AUTO_AWESOME
        )


        self.fusion_status_icon.color = (
            AppColors.PURPLE_LIGHT
        )


        self.fusion_status_text.value = (

            f"Hybrid created • "
            f"Low: {self.low_source_name} "
            f"(r={low_radius}) • "
            f"High: {self.high_source_name} "
            f"(r={high_radius})"
        )


        self.fusion_status_text.color = (
            AppColors.PURPLE_LIGHT
        )


        self.fusion_status_icon.update()

        self.fusion_status_text.update()


    # =========================================================
    # PUBLIC — GET RADII
    # =========================================================

    def get_low_radius(
        self,
    ):

        return (
            self.low_radius_control
            .get_int_value()
        )


    def get_high_radius(
        self,
    ):

        return (
            self.high_radius_control
            .get_int_value()
        )


    # =========================================================
    # PUBLIC — SET RADII
    # =========================================================

    def set_low_radius(
        self,
        value,
    ):

        self.low_radius_control.set_value(
            value
        )


        self.low_frequency_text.value = (
            f"r = {int(value)} px"
        )


        self.low_frequency_text.update()


    def set_high_radius(
        self,
        value,
    ):

        self.high_radius_control.set_value(
            value
        )


        self.high_frequency_text.value = (
            f"r = {int(value)} px"
        )


        self.high_frequency_text.update()


    # =========================================================
    # PUBLIC — RESET
    # =========================================================

    def reset(
        self,
    ):

        self.low_source_ready = False

        self.high_source_ready = False

        self.low_source_name = None

        self.high_source_name = None


        self.low_name_text.value = (
            "No Image A selected"
        )

        self.high_name_text.value = (
            "No Image B selected"
        )


        self.low_name_text.color = (
            AppColors.MUTED
        )

        self.high_name_text.color = (
            AppColors.MUTED
        )


        self.low_preview_container.content = (
            self._source_placeholder(
                AppColors.BLUE,
                ft.Icons.LANDSCAPE_OUTLINED,
            )
        )


        self.high_preview_container.content = (
            self._source_placeholder(
                AppColors.PINK,
                ft.Icons.DETAILS_OUTLINED,
            )
        )


        self.low_status_dot.bgcolor = (
            AppColors.MUTED_DARK
        )

        self.high_status_dot.bgcolor = (
            AppColors.MUTED_DARK
        )


        self.low_preview_container.border = (
            ft.Border.all(
                1,
                "#173B69",
            )
        )


        self.high_preview_container.border = (
            ft.Border.all(
                1,
                "#632247",
            )
        )


        self.set_low_radius(
            15
        )

        self.set_high_radius(
            15
        )


        self.low_name_text.update()

        self.high_name_text.update()

        self.low_preview_container.update()

        self.high_preview_container.update()

        self.low_status_dot.update()

        self.high_status_dot.update()


        self._update_source_state()


    # =========================================================
    # HOVER CARD
    # =========================================================

    def _hover_card(
        self,
        e,
    ):

        accent = e.control.data


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
    # HOVER CREATE
    # =========================================================

    def _hover_create(
        self,
        e,
    ):

        e.control.scale = (
            1.012
            if e.data
            else 1.0
        )


        e.control.update()
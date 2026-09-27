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


class CompressionView:
    """
    Feature 5 — DFT Compression Explorer.

    UI responsibilities:
    - Select percentage of coefficients to keep
    - Trigger DFT compression
    - Trigger compression-vs-PSNR curve
    - Display compression metrics
    - Visualize compression / quality tradeoff

    DSP calculations remain in main_window.py.
    """

    def __init__(
        self,
        on_apply_compression,
        on_quality_curve,
    ):

        # =====================================================
        # CALLBACKS
        # =====================================================

        self.on_apply_compression = (
            on_apply_compression
        )

        self.on_quality_curve = (
            on_quality_curve
        )


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

            badge="FEATURE 2",

            title="Compression Explorer",

            subtitle=(
                "Keep only the most significant DFT coefficients "
                "and observe the relationship between data reduction "
                "and reconstruction quality."
            ),

            icon=ft.Icons.COMPRESS,

            accent=AppColors.GREEN,
        )


        # =====================================================
        # HERO / MAIN CONTROL AREA
        # =====================================================

        top_area = ft.ResponsiveRow(

            spacing=14,

            run_spacing=14,

            controls=[

                self._build_compression_console(),

                self._build_tradeoff_panel(),
            ],
        )


        # =====================================================
        # METRICS
        # =====================================================

        metrics = self._build_metrics_dashboard()


        # =====================================================
        # EXPLANATION
        # =====================================================

        explanation = self._build_explanation_section()


        # =====================================================
        # FULL PAGE
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

                    self._build_pipeline(),

                    top_area,

                    metrics,

                    explanation,
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
                        "Image",
                        "Spatial domain",
                        AppColors.BLUE,
                    ),

                    self._arrow(),

                    self._pipeline_step(
                        ft.Icons.WAVES,
                        "2D DFT",
                        "Coefficients",
                        AppColors.CYAN,
                    ),

                    self._arrow(),

                    self._pipeline_step(
                        ft.Icons.FILTER_CENTER_FOCUS,
                        "Rank",
                        "Magnitude",
                        AppColors.PURPLE,
                    ),

                    self._arrow(),

                    self._pipeline_step(
                        ft.Icons.COMPRESS,
                        "Keep",
                        "Largest values",
                        AppColors.GREEN,
                    ),

                    self._arrow(),

                    self._pipeline_step(
                        ft.Icons.REPLAY,
                        "IDFT",
                        "Reconstruct",
                        AppColors.ORANGE,
                    ),

                    self._arrow(),

                    self._pipeline_step(
                        ft.Icons.QUERY_STATS,
                        "PSNR",
                        "Measure quality",
                        AppColors.PINK,
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

            width=130,

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

            on_hover=self._hover_pipeline,

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


    def _arrow(self):

        return ft.Icon(
            ft.Icons.ARROW_FORWARD_ROUNDED,
            size=18,
            color=AppColors.MUTED_2,
        )


    # =========================================================
    # COMPRESSION CONSOLE
    # =========================================================

    def _build_compression_console(self):

        # =====================================================
        # RETENTION SLIDER
        # =====================================================

        self.percentage_control = SliderControlCard(

            title="DFT Coefficients to Keep",

            min_value=1,

            max_value=100,

            value=10,

            divisions=99,

            suffix="%",

            accent=AppColors.GREEN,

            on_change=self._on_percentage_change,

            description=(
                "Only coefficients with the largest magnitudes "
                "will remain. The rest are set to zero."
            ),
        )


        # =====================================================
        # LIVE INFO
        # =====================================================

        self.live_keep_text = ft.Text(
            "10% retained",
            size=19,
            weight=ft.FontWeight.BOLD,
            color=AppColors.GREEN,
        )


        self.live_removed_text = ft.Text(
            "90% removed",
            size=11,
            color=AppColors.MUTED,
        )


        self.retention_bar = ft.ProgressBar(

            value=0.10,

            color=AppColors.GREEN,

            bgcolor=AppColors.SURFACE_3,

            bar_height=8,

            border_radius=8,
        )


        self.compression_mode_text = ft.Text(
            "Aggressive compression",
            size=11,
            weight=ft.FontWeight.BOLD,
            color=AppColors.ORANGE,
        )


        live_panel = ft.Container(

            bgcolor="#09140F",

            border=ft.Border.all(
                1,
                "#19462F",
            ),

            border_radius=14,

            padding=15,

            content=ft.Column(

                spacing=8,

                controls=[

                    ft.Row(

                        controls=[

                            ft.Column(

                                spacing=2,

                                expand=True,

                                controls=[
                                    self.live_keep_text,
                                    self.live_removed_text,
                                ],
                            ),

                            ft.Container(

                                padding=ft.Padding.symmetric(
                                    horizontal=10,
                                    vertical=6,
                                ),

                                bgcolor=AppColors.SURFACE_3,

                                border_radius=100,

                                content=self.compression_mode_text,
                            ),
                        ],
                    ),

                    self.retention_bar,

                    ft.Row(

                        controls=[

                            ft.Text(
                                "More compression",
                                size=9,
                                color=AppColors.ORANGE,
                            ),

                            ft.Container(
                                expand=True
                            ),

                            ft.Text(
                                "More retained data",
                                size=9,
                                color=AppColors.GREEN,
                            ),
                        ],
                    ),
                ],
            ),
        )


        # =====================================================
        # ACTION BUTTON
        # =====================================================

        apply_button = self._primary_action(

            title="Apply DFT Compression",

            subtitle=(
                "Zero discarded coefficients, reconstruct "
                "the image and calculate PSNR."
            ),

            icon=ft.Icons.COMPRESS,

            accent=AppColors.GREEN,

            handler=self.on_apply_compression,
        )


        return ft.Container(

            col={
                "xs": 12,
                "sm": 12,
                "md": 7,
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
                        icon=ft.Icons.TUNE,
                        title="Compression Console",
                        subtitle=(
                            "Control how much frequency-domain "
                            "information survives."
                        ),
                        accent=AppColors.GREEN,
                    ),

                    self.percentage_control.control,

                    live_panel,

                    apply_button,
                ],
            ),
        )


    # =========================================================
    # TRADEOFF PANEL
    # =========================================================

    def _build_tradeoff_panel(self):

        self.tradeoff_icon = ft.Icon(
            ft.Icons.SPEED,
            size=35,
            color=AppColors.ORANGE,
        )


        self.tradeoff_title = ft.Text(
            "High Compression",
            size=17,
            weight=ft.FontWeight.BOLD,
            color=AppColors.ORANGE,
            text_align=ft.TextAlign.CENTER,
        )


        self.tradeoff_description = ft.Text(
            (
                "Most coefficients are discarded. "
                "The reconstructed image may lose fine detail."
            ),
            size=10,
            color=AppColors.MUTED,
            text_align=ft.TextAlign.CENTER,
        )


        self.quality_bar = ft.ProgressBar(

            value=0.10,

            color=AppColors.PURPLE,

            bgcolor=AppColors.SURFACE_3,

            bar_height=8,

            border_radius=8,
        )


        quality_button = self._primary_action(

            title="Generate Quality Curve",

            subtitle=(
                "Compare retained coefficient percentage "
                "against reconstruction PSNR."
            ),

            icon=ft.Icons.SHOW_CHART,

            accent=AppColors.PURPLE,

            handler=self.on_quality_curve,
        )


        return ft.Container(

            col={
                "xs": 12,
                "sm": 12,
                "md": 5,
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

                spacing=15,

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                ),

                controls=[

                    self._console_header(
                        icon=ft.Icons.BALANCE,
                        title="Compression ↔ Quality",
                        subtitle=(
                            "Visualize the tradeoff before "
                            "running the reconstruction."
                        ),
                        accent=AppColors.PURPLE,
                    ),

                    ft.Container(

                        width=105,
                        height=105,

                        alignment=ft.Alignment.CENTER,

                        border_radius=53,

                        gradient=ft.RadialGradient(

                            colors=[
                                "#30231D",
                                "#171428",
                                "#0D1220",
                            ],
                        ),

                        border=ft.Border.all(
                            1,
                            AppColors.BORDER_LIGHT,
                        ),

                        content=self.tradeoff_icon,
                    ),

                    self.tradeoff_title,

                    self.tradeoff_description,

                    ft.Container(
                        width=260,
                        content=self.quality_bar,
                    ),

                    ft.Row(

                        controls=[

                            ft.Text(
                                "1%",
                                size=9,
                                color=AppColors.ORANGE,
                            ),

                            ft.Container(
                                expand=True
                            ),

                            ft.Text(
                                "100%",
                                size=9,
                                color=AppColors.GREEN,
                            ),
                        ],
                    ),

                    quality_button,
                ],
            ),
        )


    # =========================================================
    # METRIC DASHBOARD
    # =========================================================

    def _build_metrics_dashboard(self):

        self.metric_total_value = ft.Text(
            "—",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
        )


        self.metric_kept_value = ft.Text(
            "—",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
        )


        self.metric_reduction_value = ft.Text(
            "—",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
        )


        self.metric_psnr_value = ft.Text(
            "—",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
        )


        self.metric_total_card = self._metric_card(

            title="TOTAL COEFFICIENTS",

            value_control=self.metric_total_value,

            icon=ft.Icons.GRID_4X4,

            accent=AppColors.BLUE,

            subtitle="Frequency-domain values",
        )


        self.metric_kept_card = self._metric_card(

            title="COEFFICIENTS KEPT",

            value_control=self.metric_kept_value,

            icon=ft.Icons.CHECK_CIRCLE_OUTLINE,

            accent=AppColors.GREEN,

            subtitle="Non-zero after compression",
        )


        self.metric_reduction_card = self._metric_card(

            title="REDUCTION",

            value_control=self.metric_reduction_value,

            icon=ft.Icons.TRENDING_DOWN,

            accent=AppColors.ORANGE,

            subtitle="Coefficients discarded",
        )


        self.metric_psnr_card = self._metric_card(

            title="PSNR",

            value_control=self.metric_psnr_value,

            icon=ft.Icons.QUERY_STATS,

            accent=AppColors.PURPLE,

            subtitle="Reconstruction quality",
        )


        return ft.Column(

            spacing=12,

            controls=[

                ft.Row(

                    controls=[

                        ft.Text(
                            "Compression Metrics",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.TEXT,
                        ),

                        ft.Container(
                            expand=True
                        ),

                        ft.Text(
                            "Updated after compression",
                            size=10,
                            color=AppColors.MUTED,
                        ),
                    ],
                ),

                ft.ResponsiveRow(

                    spacing=12,

                    run_spacing=12,

                    controls=[

                        self.metric_total_card,

                        self.metric_kept_card,

                        self.metric_reduction_card,

                        self.metric_psnr_card,
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

            on_hover=self._hover_metric,

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

                                border_radius=12,

                                bgcolor=AppColors.SURFACE_3,

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
                                border_radius=100,
                                bgcolor=accent,
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
    # EXPLANATION
    # =========================================================

    def _build_explanation_section(self):

        return ft.ResponsiveRow(

            spacing=12,

            run_spacing=12,

            controls=[

                self._info_card(

                    title="Why compression works",

                    icon=ft.Icons.LIGHTBULB_OUTLINE,

                    accent=AppColors.CYAN,

                    text=(
                        "Many images concentrate much of their "
                        "important frequency information in a smaller "
                        "set of strong coefficients."
                    ),
                ),

                self._info_card(

                    title="What is discarded",

                    icon=ft.Icons.DELETE_SWEEP_OUTLINED,

                    accent=AppColors.ORANGE,

                    text=(
                        "Coefficients with smaller magnitudes are "
                        "replaced by zero while the strongest "
                        "coefficients are preserved."
                    ),
                ),

                self._info_card(

                    title="Why measure PSNR",

                    icon=ft.Icons.QUERY_STATS,

                    accent=AppColors.PURPLE,

                    text=(
                        "PSNR gives a numerical comparison between "
                        "the source image and its reconstructed result."
                    ),
                ),
            ],
        )


    # =========================================================
    # INFORMATION CARD
    # =========================================================

    def _info_card(
        self,
        title,
        icon,
        accent,
        text,
    ):

        return ft.Container(

            col={
                "xs": 12,
                "sm": 12,
                "md": 4,
            },

            bgcolor="#09111D",

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=15,

            padding=15,

            content=ft.Column(

                spacing=9,

                controls=[

                    ft.Row(

                        controls=[

                            ft.Icon(
                                icon,
                                size=20,
                                color=accent,
                            ),

                            ft.Text(
                                title,
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),
                        ],
                    ),

                    ft.Text(
                        text,
                        size=9,
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
    # PRIMARY ACTION
    # =========================================================

    def _primary_action(
        self,
        title,
        subtitle,
        icon,
        accent,
        handler,
    ):

        control = ft.Container(

            padding=15,

            bgcolor=AppColors.SURFACE_SOFT,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=15,

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

                        border_radius=14,

                        bgcolor=AppColors.SURFACE_3,

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
                                size=9,
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


        return control


    # =========================================================
    # SLIDER CHANGE
    # =========================================================

    def _on_percentage_change(
        self,
        e,
    ):

        percentage = int(
            e.control.value
        )


        removed = (
            100 - percentage
        )


        # =====================================================
        # LIVE VALUES
        # =====================================================

        self.live_keep_text.value = (
            f"{percentage}% retained"
        )


        self.live_removed_text.value = (
            f"{removed}% removed"
        )


        self.retention_bar.value = (
            percentage / 100.0
        )


        self.quality_bar.value = (
            percentage / 100.0
        )


        # =====================================================
        # QUALITATIVE UI STATE
        # =====================================================

        if percentage <= 10:

            mode = (
                "Aggressive compression"
            )

            title = (
                "High Compression"
            )

            description = (
                "Most coefficients are discarded. "
                "Fine details may be strongly reduced."
            )

            accent = AppColors.ORANGE

            icon = ft.Icons.SPEED


        elif percentage <= 30:

            mode = (
                "Strong compression"
            )

            title = (
                "Compression Focused"
            )

            description = (
                "A relatively small coefficient set remains "
                "while more image structure is preserved."
            )

            accent = AppColors.ORANGE_LIGHT

            icon = ft.Icons.COMPRESS


        elif percentage <= 60:

            mode = (
                "Balanced"
            )

            title = (
                "Balanced Tradeoff"
            )

            description = (
                "Compression and reconstruction fidelity "
                "are being balanced."
            )

            accent = AppColors.CYAN

            icon = ft.Icons.BALANCE


        elif percentage <= 85:

            mode = (
                "Quality focused"
            )

            title = (
                "High Retention"
            )

            description = (
                "Most DFT coefficients remain, so less "
                "frequency information is discarded."
            )

            accent = AppColors.GREEN

            icon = ft.Icons.HIGH_QUALITY


        else:

            mode = (
                "Near-original"
            )

            title = (
                "Maximum Retention"
            )

            description = (
                "Very little coefficient reduction is being "
                "applied to the frequency representation."
            )

            accent = AppColors.GREEN_LIGHT

            icon = ft.Icons.VERIFIED


        self.compression_mode_text.value = mode

        self.compression_mode_text.color = accent


        self.tradeoff_title.value = title

        self.tradeoff_title.color = accent


        self.tradeoff_description.value = (
            description
        )


        self.tradeoff_icon.name = icon

        self.tradeoff_icon.color = accent


        # =====================================================
        # UPDATE
        # =====================================================

        self.live_keep_text.update()

        self.live_removed_text.update()

        self.retention_bar.update()

        self.quality_bar.update()

        self.compression_mode_text.update()

        self.tradeoff_title.update()

        self.tradeoff_description.update()

        self.tradeoff_icon.update()


    # =========================================================
    # PUBLIC — GET PERCENTAGE
    # =========================================================

    def get_keep_percentage(
        self,
    ):

        return (
            self.percentage_control
            .get_int_value()
        )


    # =========================================================
    # PUBLIC — SET PERCENTAGE
    # =========================================================

    def set_keep_percentage(
        self,
        value,
    ):

        self.percentage_control.set_value(
            value
        )


        # Update dependent visual state too.

        fake_event = type(
            "CompressionEvent",
            (),
            {
                "control":
                    self.percentage_control.slider
            },
        )()


        self._on_percentage_change(
            fake_event
        )


    # =========================================================
    # PUBLIC — UPDATE METRICS
    # =========================================================

    def update_metrics(
        self,
        total,
        kept,
        reduction,
        psnr,
    ):

        self.metric_total_value.value = (
            f"{total:,}"
            if isinstance(total, int)
            else str(total)
        )


        self.metric_kept_value.value = (
            f"{kept:,}"
            if isinstance(kept, int)
            else str(kept)
        )


        self.metric_reduction_value.value = (
            f"{reduction:.1f}%"
            if isinstance(
                reduction,
                (int, float)
            )
            else str(reduction)
        )


        self.metric_psnr_value.value = (
            str(psnr)
        )


        self.metric_total_value.update()

        self.metric_kept_value.update()

        self.metric_reduction_value.update()

        self.metric_psnr_value.update()


    # =========================================================
    # PUBLIC — RESET METRICS
    # =========================================================

    def reset_metrics(
        self,
    ):

        self.metric_total_value.value = "—"

        self.metric_kept_value.value = "—"

        self.metric_reduction_value.value = "—"

        self.metric_psnr_value.value = "—"


        self.metric_total_value.update()

        self.metric_kept_value.update()

        self.metric_reduction_value.update()

        self.metric_psnr_value.update()


    # =========================================================
    # HOVER — PIPELINE
    # =========================================================

    def _hover_pipeline(
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
    # HOVER — METRIC
    # =========================================================

    def _hover_metric(
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
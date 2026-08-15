import asyncio
import math

import flet as ft

from ui.theme import AppColors, AppLayout, AppAnimations

# Put your background image at: assets/images/galaxy.jpg
HERO_BACKGROUND_IMAGE = "images/Nasa2.jpg"

# Background image used inside Explore the Lab / Round Console.
# You can use the same image as the Hero or a different one.
LAB_BACKGROUND_IMAGE = "images/Nasa2.jpg"


class HomeView:
    """
    App-style landing page for Signal Studio.

    IMPORTANT:
    - Keeps the existing hero / Signal Workspace visual unchanged.
    - Keeps the existing app logo/header untouched.
    - Replaces only "Explore the Lab" with a reliable round orbital interface.
    - Constructor matches the current main_window.py:
        HomeView(on_start_session=..., on_open_image=..., on_navigate=...)
    """

    def __init__(self, on_start_session, on_open_image, on_navigate):
        self.on_start_session = on_start_session
        self.on_open_image = on_open_image
        self.on_navigate = on_navigate

        # Orbital animation state.
        self._orbit_running = False
        self._orbit_paused = False
        self._orbit_phase = 0.0
        self._orbit_nodes = []
        self.orbit_stack = None

        # Central Signal Studio logo animation state.
        self.logo_core = None
        self.logo_rotor_outer = None
        self.logo_rotor_inner = None

        # Hero Signal Workspace animation state.
        self._signal_phase = 0.0
        self._signal_scan_phase = 0.0
        self._signal_bars = []
        self._signal_particles = []
        self._signal_hovered = False

        self.signal_console = None
        self.signal_wave_area = None
        self.signal_scan_line = None
        self.signal_live_dot = None
        self.signal_frequency_text = None

        # Soft ambient hero glows.
        self.hero_glow_left = None
        self.hero_glow_right = None

        # Refined hero interaction / entrance animation state.
        self._hero_intro_done = False
        self.hero_copy_panel = None
        self.hero_visual_panel = None
        self.hero_status_dot = None
        self.hero_primary_shell = None
        self.hero_secondary_shell = None
        self.session_strip = None

        # Width used by the live scanner/particles inside the hero console.
        # Keeping it in one place makes the animation responsive to the
        # redesigned, narrower product-style visual.
        self._signal_scan_span = 470

        self.control = self._build()

    # =========================================================
    # ROOT
    # =========================================================

    def _build(self):
        """Build the Home page as a polished product landing experience."""

        self.session_name_text = ft.Text(
            "No active image",
            size=10,
            weight=ft.FontWeight.W_500,
            color=AppColors.MUTED,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        return ft.Column(
            spacing=22,
            controls=[
                self._build_hero(),
                self._build_explore_lab(),
                self._build_capability_strip(),
                ft.Container(height=10),
            ],
        )

    def _build_hero(self):
        """
        Product-style hero.

        Layout:
            left  -> clear message, trust/status, CTA, active session
            right -> interactive live signal preview

        The hero is deliberately less "dashboard-like" and more like a
        polished software landing page while preserving the galaxy identity.
        """

        # =====================================================
        # SMALL PRODUCT / STATUS LABELS
        # =====================================================

        self.hero_status_dot = ft.Container(
            width=7,
            height=7,
            border_radius=100,
            bgcolor=AppColors.GREEN,
            shadow=ft.BoxShadow(
                blur_radius=10,
                color="#6634D399",
            ),
            animate_scale=ft.Animation(
                duration=420,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),
        )

        ready_badge = ft.Container(
            padding=ft.Padding.symmetric(horizontal=11, vertical=6),
            bgcolor="#B20A1716",
            border=ft.Border.all(1, "#304D463E"),
            border_radius=100,
            content=ft.Row(
                tight=True,
                spacing=7,
                controls=[
                    self.hero_status_dot,
                    ft.Text(
                        "SYSTEM READY",
                        size=8,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.GREEN_LIGHT,
                    ),
                ],
            ),
        )

        product_badge = ft.Container(
            padding=ft.Padding.symmetric(horizontal=11, vertical=6),
            bgcolor="#A40B1524",
            border=ft.Border.all(1, "#3340645E"),
            border_radius=100,
            content=ft.Row(
                tight=True,
                spacing=7,
                controls=[
                    ft.Icon(
                        ft.Icons.WAVES,
                        size=13,
                        color=AppColors.CYAN,
                    ),
                    ft.Text(
                        "CSE 220 • SIGNAL STUDIO",
                        size=8,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.CYAN_LIGHT,
                    ),
                ],
            ),
        )

        # =====================================================
        # HERO TYPOGRAPHY
        # =====================================================

        hero_title = ft.Column(
            spacing=1,
            controls=[
                ft.Text(
                    "See image processing",
                    size=42,
                    weight=ft.FontWeight.BOLD,
                    color=AppColors.TEXT,
                    height=1.03,
                ),
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(
                            "through signals.",
                            size=42,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.CYAN_LIGHT,
                            height=1.03,
                        ),
                        ft.Container(
                            width=42,
                            height=3,
                            border_radius=3,
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
                    ],
                ),
            ],
        )

        hero_description = ft.Container(
            width=520,
            content=ft.Text(
                "Explore spatial filtering, Fourier-domain editing, compression, "
                "texture analysis, hybrid imaging and color spaces in one visual "
                "signal-processing workspace.",
                size=12,
                color="#A9B8CC",
                height=1.62,
            ),
        )

        # =====================================================
        # PRIMARY / SECONDARY ACTIONS
        # =====================================================

        primary_button = ft.Button(
            content="Start New Session",
            icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
            on_click=self.on_start_session,
            bgcolor=AppColors.BLUE,
            color=AppColors.WHITE,
            elevation=0,
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=20, vertical=14),
                shape=ft.RoundedRectangleBorder(radius=13),
            ),
        )

        self.hero_primary_shell = ft.Container(
            border_radius=13,
            scale=1.0,
            offset=ft.Offset(0, 0),
            animate_scale=ft.Animation(
                duration=190,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate_offset=ft.Animation(
                duration=190,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate=ft.Animation(
                duration=190,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            shadow=ft.BoxShadow(
                blur_radius=18,
                color="#302F7BFF",
                offset=ft.Offset(0, 7),
            ),
            on_hover=self._hover_primary_action,
            content=primary_button,
        )

        secondary_button = ft.OutlinedButton(
            content="Browse Image",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self.on_open_image,
            style=ft.ButtonStyle(
                color=AppColors.CYAN_LIGHT,
                padding=ft.Padding.symmetric(horizontal=20, vertical=14),
                shape=ft.RoundedRectangleBorder(radius=13),
                side=ft.BorderSide(1, "#43536C"),
            ),
        )

        self.hero_secondary_shell = ft.Container(
            border_radius=13,
            scale=1.0,
            offset=ft.Offset(0, 0),
            animate_scale=ft.Animation(
                duration=190,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate_offset=ft.Animation(
                duration=190,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate=ft.Animation(
                duration=190,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            on_hover=self._hover_secondary_action,
            content=secondary_button,
        )

        # =====================================================
        # CURRENT SESSION CARD
        # =====================================================

        self.session_strip = ft.Container(
            width=520,
            padding=ft.Padding.symmetric(horizontal=13, vertical=11),
            bgcolor="#9A0A111C",
            border=ft.Border.all(1, "#2B3A4E"),
            border_radius=14,
            animate=ft.Animation(
                duration=180,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate_scale=ft.Animation(
                duration=180,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            on_hover=self._hover_session_strip,
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=34,
                        height=34,
                        alignment=ft.Alignment.CENTER,
                        border_radius=10,
                        bgcolor="#101C2B",
                        border=ft.Border.all(1, "#2D4058"),
                        content=ft.Icon(
                            ft.Icons.INSERT_PHOTO_OUTLINED,
                            size=16,
                            color=AppColors.CYAN,
                        ),
                    ),
                    ft.Column(
                        spacing=1,
                        expand=True,
                        controls=[
                            ft.Text(
                                "CURRENT SESSION",
                                size=7,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.MUTED_2,
                            ),
                            self.session_name_text,
                        ],
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=9, vertical=5),
                        border_radius=100,
                        bgcolor="#0B1824",
                        content=ft.Text(
                            "PNG • JPG • BMP • TIFF",
                            size=7,
                            weight=ft.FontWeight.W_600,
                            color=AppColors.MUTED,
                        ),
                    ),
                ],
            ),
        )

        # =====================================================
        # QUICK VALUE PROPS
        # =====================================================

        value_row = ft.Row(
            spacing=9,
            wrap=True,
            controls=[
                self._hero_value_chip(
                    ft.Icons.GRID_ON_OUTLINED,
                    "12 DSP tools",
                    AppColors.CYAN,
                ),
                self._hero_value_chip(
                    ft.Icons.FUNCTIONS,
                    "Manual 2D DFT",
                    AppColors.PURPLE,
                ),
                self._hero_value_chip(
                    ft.Icons.INSIGHTS_OUTLINED,
                    "PSNR metrics",
                    AppColors.GREEN,
                ),
            ],
        )

        # =====================================================
        # LEFT HERO COPY
        # =====================================================

        self.hero_copy_panel = ft.Container(
            col={"xs": 12, "lg": 6},
            opacity=0,
            offset=ft.Offset(-0.025, 0),
            animate_opacity=ft.Animation(
                duration=650,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate_offset=ft.Animation(
                duration=650,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=ft.Column(
                spacing=18,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Row(
                        spacing=8,
                        wrap=True,
                        controls=[
                            product_badge,
                            ready_badge,
                        ],
                    ),
                    hero_title,
                    hero_description,
                    value_row,
                    ft.Row(
                        spacing=10,
                        wrap=True,
                        controls=[
                            self.hero_primary_shell,
                            self.hero_secondary_shell,
                        ],
                    ),
                    self.session_strip,
                ],
            ),
        )

        # =====================================================
        # RIGHT HERO VISUAL
        # =====================================================

        visual_top_label = ft.Row(
            controls=[
                ft.Column(
                    spacing=1,
                    expand=True,
                    controls=[
                        ft.Text(
                            "LIVE PROCESSING PREVIEW",
                            size=8,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.CYAN_LIGHT,
                        ),
                        ft.Text(
                            "Interactive signal visualization",
                            size=9,
                            color=AppColors.MUTED,
                        ),
                    ],
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=9, vertical=5),
                    border_radius=100,
                    bgcolor="#0A1A17",
                    border=ft.Border.all(1, "#1D493D"),
                    content=ft.Text(
                        "REAL-TIME",
                        size=7,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.GREEN_LIGHT,
                    ),
                ),
            ],
        )

        self.hero_visual_panel = ft.Container(
            col={"xs": 12, "lg": 6},
            opacity=0,
            offset=ft.Offset(0.025, 0),
            animate_opacity=ft.Animation(
                duration=720,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate_offset=ft.Animation(
                duration=720,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            padding=ft.Padding.all(16),
            border_radius=22,
            bgcolor="#62070C15",
            border=ft.Border.all(1, "#31425B"),
            shadow=ft.BoxShadow(
                blur_radius=30,
                color="#2A000000",
                offset=ft.Offset(0, 12),
            ),
            content=ft.Column(
                spacing=12,
                controls=[
                    visual_top_label,
                    self._build_signal_console(),
                ],
            ),
        )

        # =====================================================
        # AMBIENT HERO LIGHT
        # =====================================================

        self.hero_glow_left = ft.Container(
            left=-45,
            top=30,
            width=220,
            height=220,
            border_radius=110,
            bgcolor="#13213B66",
            blur=55,
            opacity=0.45,
            scale=1.0,
            animate_scale=ft.Animation(
                duration=1000,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),
            animate_opacity=ft.Animation(
                duration=1000,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),
        )

        self.hero_glow_right = ft.Container(
            right=-35,
            bottom=-30,
            width=260,
            height=260,
            border_radius=130,
            bgcolor="#28163E66",
            blur=60,
            opacity=0.38,
            scale=1.0,
            animate_scale=ft.Animation(
                duration=1100,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),
            animate_opacity=ft.Animation(
                duration=1100,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),
        )

        hero_layout = ft.ResponsiveRow(
            spacing=26,
            run_spacing=24,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.hero_copy_panel,
                self.hero_visual_panel,
            ],
        )

        # =====================================================
        # COMPLETE HERO
        # =====================================================

        return ft.Container(
            border_radius=ft.BorderRadius.all(28),
            border=ft.Border.all(1, "#344760"),
            shadow=ft.BoxShadow(
                blur_radius=42,
                spread_radius=0,
                color="#3A000000",
                offset=ft.Offset(0, 16),
            ),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack(
                controls=[
                    ft.Image(
                        src=HERO_BACKGROUND_IMAGE,
                        left=0,
                        right=0,
                        top=0,
                        bottom=0,
                        fit=ft.BoxFit.COVER,
                    ),

                    # Readability layer: dark on the left, slightly clearer
                    # around the product preview on the right.
                    ft.Container(
                        left=0,
                        right=0,
                        top=0,
                        bottom=0,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.CENTER_LEFT,
                            end=ft.Alignment.CENTER_RIGHT,
                            colors=[
                                "#EA060A12",
                                "#C7080D18",
                                "#A8090E19",
                                "#C0070B13",
                            ],
                        ),
                    ),

                    ft.Container(
                        left=0,
                        right=0,
                        top=0,
                        bottom=0,
                        gradient=ft.RadialGradient(
                            center=ft.Alignment.CENTER,
                            radius=1.05,
                            colors=[
                                "#05000000",
                                "#24080D18",
                                "#81050A12",
                            ],
                        ),
                    ),

                    self.hero_glow_left,
                    self.hero_glow_right,

                    ft.Container(
                        padding=ft.Padding.symmetric(
                            horizontal=34,
                            vertical=32,
                        ),
                        content=hero_layout,
                    ),

                    # Fine top highlight gives the card a premium glass edge.
                    ft.Container(
                        left=28,
                        right=28,
                        top=0,
                        height=1,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.CENTER_LEFT,
                            end=ft.Alignment.CENTER_RIGHT,
                            colors=[
                                "#0022D3EE",
                                "#6622D3EE",
                                "#448B5CF6",
                                "#00EC4899",
                            ],
                        ),
                    ),
                ],
            ),
        )

    def _build_signal_console(self):
        """Build the interactive live signal visual used inside the hero."""

        self.signal_live_dot = ft.Container(
            width=7,
            height=7,
            bgcolor=AppColors.GREEN,
            border_radius=100,
            shadow=ft.BoxShadow(
                blur_radius=8,
                color="#6634D399",
            ),
            animate_scale=ft.Animation(
                duration=180,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),
        )

        live_badge = ft.Container(
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=100,
            bgcolor="#0B1D1A",
            border=ft.Border.all(1, "#18483C"),
            content=ft.Row(
                tight=True,
                spacing=5,
                controls=[
                    self.signal_live_dot,
                    ft.Text(
                        "LIVE",
                        size=7,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.GREEN_LIGHT,
                    ),
                ],
            ),
        )

        self._signal_bars = []

        bar_colors = [
            AppColors.CYAN,
            AppColors.CYAN,
            AppColors.BLUE,
            AppColors.PURPLE,
            AppColors.PURPLE,
            AppColors.PINK,
            AppColors.PURPLE,
            AppColors.BLUE,
            AppColors.CYAN,
            AppColors.PURPLE,
            AppColors.PINK,
            AppColors.CYAN,
            AppColors.BLUE,
            AppColors.PURPLE,
            AppColors.PINK,
        ]

        initial_heights = [
            26, 42, 62, 48, 78,
            57, 36, 69, 51, 82,
            64, 40, 72, 55, 32,
        ]

        for index, height in enumerate(initial_heights):
            bar = ft.Container(
                width=8,
                height=height,
                border_radius=5,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment.TOP_CENTER,
                    end=ft.Alignment.BOTTOM_CENTER,
                    colors=[
                        bar_colors[index],
                        "#26293D58",
                    ],
                ),
                shadow=ft.BoxShadow(
                    blur_radius=7,
                    color=f"2A{bar_colors[index][1:]}",
                ),
                animate_size=ft.Animation(
                    duration=105,
                    curve=ft.AnimationCurve.EASE_IN_OUT,
                ),
                animate_opacity=ft.Animation(
                    duration=105,
                    curve=ft.AnimationCurve.EASE_IN_OUT,
                ),
            )
            self._signal_bars.append(bar)

        waveform_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=self._signal_bars,
        )

        self.signal_scan_line = ft.Container(
            left=8,
            top=8,
            width=2,
            bottom=8,
            border_radius=2,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=[
                    "#0022D3EE",
                    "#B822D3EE",
                    "#0022D3EE",
                ],
            ),
            shadow=ft.BoxShadow(
                blur_radius=14,
                color="#6622D3EE",
            ),
            animate_position=ft.Animation(
                duration=95,
                curve=ft.AnimationCurve.LINEAR,
            ),
        )

        self.signal_frequency_text = ft.Text(
            "LIVE SIGNAL • 2D IMAGE DOMAIN",
            size=7,
            weight=ft.FontWeight.BOLD,
            color=AppColors.CYAN_LIGHT,
        )

        self._signal_particles = []
        particle_colors = [
            AppColors.CYAN,
            AppColors.PURPLE,
            AppColors.PINK,
            AppColors.CYAN,
        ]

        for index, particle_color in enumerate(particle_colors):
            particle = ft.Container(
                left=18 + index * 90,
                top=16 + index * 18,
                width=4,
                height=4,
                border_radius=100,
                bgcolor=particle_color,
                opacity=0.42,
                shadow=ft.BoxShadow(
                    blur_radius=8,
                    color=f"55{particle_color[1:]}",
                ),
                animate_position=ft.Animation(
                    duration=105,
                    curve=ft.AnimationCurve.LINEAR,
                ),
                animate_opacity=ft.Animation(
                    duration=105,
                    curve=ft.AnimationCurve.EASE_IN_OUT,
                ),
            )
            self._signal_particles.append(particle)

        signal_grid = ft.Container(
            expand=True,
            padding=10,
            alignment=ft.Alignment.CENTER,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Container(
                        top=23,
                        left=0,
                        right=0,
                        height=1,
                        bgcolor="#15243A58",
                    ),
                    ft.Container(
                        top=50,
                        left=0,
                        right=0,
                        height=1,
                        bgcolor="#15243A58",
                    ),
                    ft.Container(
                        top=77,
                        left=0,
                        right=0,
                        height=1,
                        bgcolor="#15243A58",
                    ),
                    *self._signal_particles,
                    ft.Container(
                        left=0,
                        right=0,
                        top=8,
                        bottom=8,
                        alignment=ft.Alignment.CENTER,
                        content=waveform_row,
                    ),
                    self.signal_scan_line,
                    ft.Container(
                        left=8,
                        bottom=5,
                        padding=ft.Padding.symmetric(
                            horizontal=7,
                            vertical=3,
                        ),
                        border_radius=100,
                        bgcolor="#C0070B13",
                        content=self.signal_frequency_text,
                    ),
                ],
            ),
        )

        self.signal_wave_area = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            bgcolor="#D4070B13",
            border=ft.Border.all(1, "#2A3B53"),
            border_radius=15,
            content=signal_grid,
        )

        self.signal_console = ft.Container(
            height=270,
            padding=16,
            border_radius=18,
            border=ft.Border.all(1, "#34455E"),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[
                    "#D00A1422",
                    "#CE11172B",
                    "#D0171127",
                ],
            ),
            shadow=ft.BoxShadow(
                blur_radius=22,
                color="#28000000",
                offset=ft.Offset(0, 8),
            ),
            ink=True,
            on_click=lambda e: self._navigate(1),
            offset=ft.Offset(0, 0),
            scale=1.0,
            animate_offset=ft.Animation(
                duration=210,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate_scale=ft.Animation(
                duration=210,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate=ft.Animation(
                duration=210,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            on_hover=self._hover_signal_console,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=38,
                                height=38,
                                alignment=ft.Alignment.CENTER,
                                border_radius=12,
                                gradient=ft.LinearGradient(
                                    begin=ft.Alignment.TOP_LEFT,
                                    end=ft.Alignment.BOTTOM_RIGHT,
                                    colors=[
                                        AppColors.CYAN,
                                        AppColors.PURPLE,
                                    ],
                                ),
                                content=ft.Icon(
                                    ft.Icons.WAVES,
                                    size=21,
                                    color=AppColors.BLACK,
                                ),
                            ),
                            ft.Container(width=10),
                            ft.Column(
                                spacing=1,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        "SIGNAL WORKSPACE",
                                        size=9,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.TEXT,
                                    ),
                                    ft.Text(
                                        "Spatial • Frequency • Restoration",
                                        size=8,
                                        color=AppColors.MUTED,
                                    ),
                                ],
                            ),
                            live_badge,
                        ],
                    ),
                    self.signal_wave_area,
                    ft.Row(
                        spacing=0,
                        controls=[
                            self._mini_console_metric(
                                "2D", "SIGNALS", AppColors.CYAN
                            ),
                            self._mini_metric_divider(),
                            self._mini_console_metric(
                                "DFT", "DOMAIN", AppColors.PURPLE
                            ),
                            self._mini_metric_divider(),
                            self._mini_console_metric(
                                "PSNR", "QUALITY", AppColors.GREEN
                            ),
                        ],
                    ),
                ],
            ),
        )

        return self.signal_console

    def _mini_console_metric(self, value, label, accent):
        return ft.Container(
            expand=True,
            padding=ft.Padding.symmetric(vertical=3),
            content=ft.Column(
                spacing=1,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        value,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=accent,
                    ),
                    ft.Text(
                        label,
                        size=6,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.MUTED_2,
                    ),
                ],
            ),
        )

    def _mini_metric_divider(self):
        return ft.Container(
            width=1,
            height=24,
            bgcolor="#293A50",
        )

    def _hero_value_chip(self, icon, text, accent):
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=7),
            border_radius=11,
            bgcolor="#780A121E",
            border=ft.Border.all(1, "#293B52"),
            content=ft.Row(
                tight=True,
                spacing=7,
                controls=[
                    ft.Icon(icon, size=13, color=accent),
                    ft.Text(
                        text,
                        size=8,
                        weight=ft.FontWeight.W_600,
                        color="#C4D0DE",
                    ),
                ],
            ),
        )

    def _hover_primary_action(self, e):
        hovered = self._is_hovered(e.data)

        e.control.scale = 1.025 if hovered else 1.0
        e.control.offset = (
            ft.Offset(0, -0.025)
            if hovered
            else ft.Offset(0, 0)
        )
        e.control.shadow = (
            ft.BoxShadow(
                blur_radius=28,
                spread_radius=1,
                color="#4A2F7BFF",
                offset=ft.Offset(0, 10),
            )
            if hovered
            else ft.BoxShadow(
                blur_radius=18,
                color="#302F7BFF",
                offset=ft.Offset(0, 7),
            )
        )
        e.control.update()

    def _hover_secondary_action(self, e):
        hovered = self._is_hovered(e.data)

        e.control.scale = 1.02 if hovered else 1.0
        e.control.offset = (
            ft.Offset(0, -0.02)
            if hovered
            else ft.Offset(0, 0)
        )
        e.control.update()

    def _hover_session_strip(self, e):
        hovered = self._is_hovered(e.data)

        e.control.scale = 1.008 if hovered else 1.0
        e.control.bgcolor = "#B10D1724" if hovered else "#9A0A111C"
        e.control.border = ft.Border.all(
            1,
            "#3A5675" if hovered else "#2B3A4E",
        )
        e.control.update()

    def _build_explore_lab(self):
        header = ft.Row(
            controls=[
                ft.Column(
                    spacing=2,
                    expand=True,
                    controls=[
                        ft.Text(
                            "Explore the Lab",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.TEXT,
                        ),
                        ft.Text(
                            "Hover over a glowing node, then click to enter a DSP workspace.",
                            size=10,
                            color=AppColors.MUTED,
                        ),
                    ],
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                    bgcolor="#0D1727",
                    border=ft.Border.all(1, AppColors.BORDER_SOFT),
                    border_radius=100,
                    content=ft.Row(
                        tight=True,
                        spacing=6,
                        controls=[
                            ft.Icon(
                                ft.Icons.TOUCH_APP_OUTLINED,
                                size=13,
                                color=AppColors.CYAN,
                            ),
                            ft.Text(
                                "HOVER • CLICK • EXPLORE",
                                size=8,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.CYAN_LIGHT,
                            ),
                        ],
                    ),
                ),
            ],
        )

        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=22, vertical=20),
            bgcolor=AppColors.SURFACE,
            border=ft.Border.all(1, AppColors.BORDER),
            border_radius=ft.BorderRadius.all(22),
            content=ft.Column(
                spacing=14,
                controls=[
                    header,
                    self._build_orbit(),
                ],
            ),
        )

    def _build_orbit(self):
        """
        Animated orbital navigation.

        The six feature bubbles continuously revolve around the central
        Signal Studio core. Text stays upright for readability.

        Hovering a bubble:
        - pauses the orbit
        - enlarges the bubble
        - strengthens its border
        - adds a feature-colored glow

        Flet's animate_position smoothly interpolates left/top changes.
        """

        canvas_width = 820
        canvas_height = 500

        center_x = canvas_width / 2
        center_y = canvas_height / 2

        node_size = 112
        orbit_radius_x = 300
        orbit_radius_y = 182

        # -----------------------------------------------------
        # ORBIT RINGS
        # -----------------------------------------------------

        rings = [
            self._orbit_ring(
                left=center_x - 210,
                top=center_y - 210,
                size=420,
                color="#22314D",
            ),
            self._orbit_ring(
                left=center_x - 165,
                top=center_y - 165,
                size=330,
                color="#2A3C5D",
            ),
            self._orbit_ring(
                left=center_x - 120,
                top=center_y - 120,
                size=240,
                color="#385174",
            ),
        ]

        # -----------------------------------------------------
        # CENTRAL CORE
        # -----------------------------------------------------

        core_size = 164

        # -----------------------------------------------------
        # ANIMATED LOGO HALOS
        #
        # The actual Signal Studio logo/text remains unchanged.
        # Only the decorative rings rotate and the core gently breathes.
        # -----------------------------------------------------

        outer_rotor_size = 210

        self.logo_rotor_outer = ft.Stack(
            left=center_x - outer_rotor_size / 2,
            top=center_y - outer_rotor_size / 2,
            width=outer_rotor_size,
            height=outer_rotor_size,
            rotate=0.0,
            animate_rotation=ft.Animation(
                duration=120,
                curve=ft.AnimationCurve.LINEAR,
            ),
            controls=[
                ft.Container(
                    left=0,
                    top=0,
                    width=outer_rotor_size,
                    height=outer_rotor_size,
                    border_radius=outer_rotor_size / 2,
                    border=ft.Border.all(1, "#355074"),
                ),
                ft.Container(
                    left=outer_rotor_size / 2 - 5,
                    top=-5,
                    width=10,
                    height=10,
                    border_radius=5,
                    bgcolor=AppColors.CYAN,
                    shadow=ft.BoxShadow(
                        blur_radius=14,
                        color="#7722D3EE",
                    ),
                ),
                ft.Container(
                    right=-4,
                    top=outer_rotor_size / 2 - 4,
                    width=8,
                    height=8,
                    border_radius=4,
                    bgcolor=AppColors.PURPLE,
                    shadow=ft.BoxShadow(
                        blur_radius=12,
                        color="#778B5CF6",
                    ),
                ),
                ft.Container(
                    left=outer_rotor_size / 2 - 4,
                    bottom=-4,
                    width=8,
                    height=8,
                    border_radius=4,
                    bgcolor=AppColors.PINK,
                    shadow=ft.BoxShadow(
                        blur_radius=12,
                        color="#77EC4899",
                    ),
                ),
            ],
        )

        inner_rotor_size = 188

        self.logo_rotor_inner = ft.Stack(
            left=center_x - inner_rotor_size / 2,
            top=center_y - inner_rotor_size / 2,
            width=inner_rotor_size,
            height=inner_rotor_size,
            rotate=0.0,
            animate_rotation=ft.Animation(
                duration=120,
                curve=ft.AnimationCurve.LINEAR,
            ),
            controls=[
                ft.Container(
                    left=0,
                    top=0,
                    width=inner_rotor_size,
                    height=inner_rotor_size,
                    border_radius=inner_rotor_size / 2,
                    border=ft.Border.all(1, "#263A59"),
                ),
                ft.Container(
                    left=-4,
                    top=inner_rotor_size / 2 - 4,
                    width=8,
                    height=8,
                    border_radius=4,
                    bgcolor=AppColors.BLUE,
                ),
                ft.Container(
                    right=inner_rotor_size / 2 - 3,
                    top=-3,
                    width=6,
                    height=6,
                    border_radius=3,
                    bgcolor=AppColors.GREEN,
                ),
            ],
        )

        self.logo_core = ft.Container(
            left=center_x - core_size / 2,
            top=center_y - core_size / 2,
            width=core_size,
            height=core_size,
            alignment=ft.Alignment.CENTER,
            border_radius=core_size / 2,
            gradient=ft.RadialGradient(
                colors=[
                    "#24415D",
                    "#171A34",
                    "#0A0F1B",
                ],
            ),
            border=ft.Border.all(1.5, "#496788"),
            shadow=ft.BoxShadow(
                blur_radius=34,
                spread_radius=2,
                color="#3022D3EE",
            ),
            animate_scale=ft.Animation(
                duration=360,
                curve=ft.AnimationCurve.EASE_IN_OUT,
            ),
            content=ft.Column(
                tight=True,
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        ft.Icons.WAVES,
                        size=42,
                        color=AppColors.CYAN,
                    ),
                    ft.Text(
                        "SIGNAL",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT,
                    ),
                    ft.Text(
                        "STUDIO",
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.PURPLE_LIGHT,
                    ),
                    ft.Text(
                        "EXPLORE",
                        size=7,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.MUTED,
                    ),
                ],
            ),
        )

        # -----------------------------------------------------
        # FEATURE DEFINITIONS
        #
        # Equal 60-degree spacing keeps the interface balanced.
        # -----------------------------------------------------

        specs = [
            {
                "angle": -90,
                "title": "Frequency",
                "badge": "FEATURE 4",
                "icon": ft.Icons.TUNE,
                "accent": AppColors.CYAN,
                "tint": "#0B2630",
                "handler": lambda e: self._navigate(1),
            },
            {
                "angle": -30,
                "title": "Compression",
                "badge": "FEATURE 5",
                "icon": ft.Icons.BAR_CHART,
                "accent": AppColors.GREEN,
                "tint": "#0B2A21",
                "handler": lambda e: self._navigate(2),
            },
            {
                "angle": 30,
                "title": "Texture",
                "badge": "FEATURE 8",
                "icon": ft.Icons.GRID_VIEW,
                "accent": AppColors.ORANGE,
                "tint": "#2A210E",
                "handler": lambda e: self._navigate(3),
            },
            {
                "angle": 90,
                "title": "New Session",
                "badge": "OPEN IMAGE",
                "icon": ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
                "accent": AppColors.BLUE,
                "tint": "#10284A",
                "handler": self.on_start_session,
            },
            {
                "angle": 150,
                "title": "Hybrid",
                "badge": "FEATURE 9",
                "icon": ft.Icons.AUTO_AWESOME,
                "accent": AppColors.PINK,
                "tint": "#301121",
                "handler": lambda e: self._navigate(4),
            },
            {
                "angle": 210,
                "title": "Color Lab",
                "badge": "FEATURE 12",
                "icon": ft.Icons.PALETTE,
                "accent": AppColors.PURPLE,
                "tint": "#241636",
                "handler": lambda e: self._navigate(5),
            },
        ]

        self._orbit_nodes = []

        for spec in specs:
            angle_rad = math.radians(spec["angle"])

            left = (
                center_x
                + orbit_radius_x * math.cos(angle_rad)
                - node_size / 2
            )

            top = (
                center_y
                + orbit_radius_y * math.sin(angle_rad)
                - node_size / 2
            )

            node = self._orbit_node(
                left=left,
                top=top,
                size=node_size,
                title=spec["title"],
                badge=spec["badge"],
                icon=spec["icon"],
                accent=spec["accent"],
                tint=spec["tint"],
                handler=spec["handler"],
            )

            self._orbit_nodes.append(
                {
                    "control": node,
                    "base_angle": spec["angle"],
                }
            )

        # -----------------------------------------------------
        # DECORATIVE SIGNAL POINTS
        # -----------------------------------------------------

        decorations = [
            self._signal_dot(244, 56, AppColors.CYAN),
            self._signal_dot(560, 55, AppColors.PURPLE),
            self._signal_dot(715, 250, AppColors.GREEN),
            self._signal_dot(535, 432, AppColors.PINK),
            self._signal_dot(280, 437, AppColors.ORANGE),
            self._signal_dot(101, 250, AppColors.BLUE),
        ]

        self.orbit_stack = ft.Stack(
            width=canvas_width,
            height=canvas_height,
            controls=[
                *rings,
                *decorations,

                # Animated logo layers
                self.logo_rotor_outer,
                self.logo_rotor_inner,
                self.logo_core,

                *[
                    item["control"]
                    for item in self._orbit_nodes
                ],
            ],
        )

        # -----------------------------------------------------
        # ROUND CONSOLE BACKGROUND
        #
        # Layer order:
        # 1. galaxy image
        # 2. dark overlay
        # 3. radial vignette
        # 4. animated orbit interface
        # -----------------------------------------------------

        return ft.Container(
            height=520,
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(
                1,
                AppColors.BORDER_SOFT,
            ),
            border_radius=ft.BorderRadius.all(19),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack(
                expand=True,
                controls=[
                    # =================================================
                    # 1. GALAXY BACKGROUND
                    # =================================================
                    ft.Image(
                        src=LAB_BACKGROUND_IMAGE,
                        left=0,
                        right=0,
                        top=0,
                        bottom=0,
                        fit=ft.BoxFit.COVER,
                    ),

                    # =================================================
                    # 2. DARK GLASS OVERLAY
                    #
                    # Slightly darker than the Hero because the orbit
                    # rings and labels need strong contrast.
                    # =================================================
                    ft.Container(
                        left=0,
                        right=0,
                        top=0,
                        bottom=0,
                        gradient=ft.LinearGradient(
                            begin=ft.Alignment.TOP_CENTER,
                            end=ft.Alignment.BOTTOM_CENTER,
                            colors=[
                                "#B8070C16",
                                "#A6080D18",
                                "#C4070B14",
                            ],
                        ),
                    ),

                    # =================================================
                    # 3. RADIAL VIGNETTE
                    #
                    # Keeps the center glowing and the edges darker,
                    # making the circular interface stand out.
                    # =================================================
                    ft.Container(
                        left=0,
                        right=0,
                        top=0,
                        bottom=0,
                        gradient=ft.RadialGradient(
                            center=ft.Alignment.CENTER,
                            radius=1.0,
                            colors=[
                                "#08000000",
                                "#2508111F",
                                "#7C040810",
                            ],
                        ),
                    ),

                    # =================================================
                    # 4. ORBITAL DSP INTERFACE
                    # =================================================
                    ft.Container(
                        left=0,
                        right=0,
                        top=0,
                        bottom=0,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            scroll=ft.ScrollMode.AUTO,
                            controls=[
                                self.orbit_stack,
                            ],
                        ),
                    ),
                ],
            ),
        )

    def _orbit_ring(self, left, top, size, color):
        return ft.Container(
            left=left,
            top=top,
            width=size,
            height=size,
            border_radius=size / 2,
            border=ft.Border.all(1, color),
        )

    def _orbit_node(
        self,
        left,
        top,
        size,
        title,
        badge,
        icon,
        accent,
        tint,
        handler,
    ):
        """
        A circular clickable node.

        Hover deliberately changes only well-supported properties:
        scale, border and shadow. The gradient remains static so the
        control does not need to swap between bgcolor/gradient at runtime.
        """

        return ft.Container(
            left=left,
            top=top,
            width=size,
            height=size,
            alignment=ft.Alignment.CENTER,
            border_radius=size / 2,
            gradient=ft.RadialGradient(
                colors=[
                    tint,
                    "#0D1523",
                    "#080D16",
                ],
            ),
            border=ft.Border.all(1.4, accent),
            shadow=ft.BoxShadow(
                blur_radius=14,
                spread_radius=0,
                color="#26000000",
            ),
            ink=True,
            on_click=handler,
            on_hover=self._hover_orbit_node,
            animate_scale=ft.Animation(
                duration=180,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            # Smooth movement around the orbit.
            animate_position=ft.Animation(
                duration=120,
                curve=ft.AnimationCurve.LINEAR,
            ),
            data={
                "accent": accent,
            },
            content=ft.Column(
                tight=True,
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=43,
                        height=43,
                        alignment=ft.Alignment.CENTER,
                        border_radius=22,
                        bgcolor="#191FFFFFF",
                        border=ft.Border.all(1, accent),
                        content=ft.Icon(
                            icon,
                            size=22,
                            color=accent,
                        ),
                    ),
                    ft.Text(
                        title,
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        badge,
                        size=7,
                        weight=ft.FontWeight.BOLD,
                        color=accent,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

    def _signal_dot(self, left, top, color):
        return ft.Container(
            left=left,
            top=top,
            width=6,
            height=6,
            border_radius=3,
            bgcolor=color,
            opacity=0.65,
        )

    # =========================================================
    # CAPABILITY STRIP
    # =========================================================

    def _build_capability_strip(self):
        """Compact product-proof strip below the orbital section."""

        specs = [
            ("12", "DSP FEATURES", ft.Icons.DASHBOARD_OUTLINED, AppColors.CYAN),
            ("2D", "MANUAL DFT", ft.Icons.FUNCTIONS, AppColors.PURPLE),
            ("PSNR", "QUALITY", ft.Icons.INSIGHTS_OUTLINED, AppColors.GREEN),
            ("RGB", "CHANNELS", ft.Icons.PALETTE_OUTLINED, AppColors.RED),
            ("YCbCr", "COLOR SPACE", ft.Icons.COLOR_LENS_OUTLINED, AppColors.ORANGE),
            ("LIVE", "PREVIEW", ft.Icons.VISIBILITY_OUTLINED, AppColors.PINK),
        ]

        return ft.Container(
            padding=ft.Padding.all(10),
            bgcolor="#8E080D15",
            border=ft.Border.all(1, AppColors.BORDER),
            border_radius=ft.BorderRadius.all(18),
            content=ft.ResponsiveRow(
                spacing=8,
                run_spacing=8,
                controls=[
                    ft.Container(
                        col={"xs": 6, "sm": 4, "md": 2},
                        content=self._capability(
                            value,
                            label,
                            icon,
                            accent,
                        ),
                    )
                    for value, label, icon, accent in specs
                ],
            ),
        )

    def _capability(self, value, label, icon, accent):
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=10),
            border_radius=13,
            bgcolor="#620B121D",
            border=ft.Border.all(1, "#243348"),
            content=ft.Row(
                spacing=9,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=30,
                        height=30,
                        alignment=ft.Alignment.CENTER,
                        border_radius=9,
                        bgcolor=f"18{accent[1:]}",
                        content=ft.Icon(
                            icon,
                            size=14,
                            color=accent,
                        ),
                    ),
                    ft.Column(
                        spacing=0,
                        controls=[
                            ft.Text(
                                value,
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=accent,
                            ),
                            ft.Text(
                                label,
                                size=6,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.MUTED,
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _separator(self):
        # Retained for backwards compatibility with older view code.
        return ft.Container(
            width=1,
            height=28,
            bgcolor=AppColors.BORDER,
        )

    def set_session_name(self, image_name, refresh=True):
        self.session_name_text.value = image_name
        self.session_name_text.color = AppColors.CYAN_LIGHT

        if refresh:
            self.session_name_text.update()

    # =========================================================
    # NAVIGATION
    # =========================================================

    def _navigate(self, index):
        if self.on_navigate:
            self.on_navigate(index)

    # =========================================================
    # HOVER HANDLERS
    # =========================================================

    @staticmethod
    def _is_hovered(value):
        """
        Works whether the Flet version supplies event.data
        as a bool or as a string such as "true"/"false".
        """
        if isinstance(value, bool):
            return value

        return str(value).strip().lower() in {
            "true",
            "1",
            "yes",
        }

    def _hover_orbit_node(self, e):
        hovered = self._is_hovered(e.data)
        accent = e.control.data["accent"]

        # Freeze the orbit while the pointer is on a feature.
        # This makes clicking easy and avoids a "moving target".
        self._orbit_paused = hovered

        if hovered:
            e.control.scale = 1.12
            e.control.border = ft.Border.all(2.2, accent)
            e.control.shadow = ft.BoxShadow(
                blur_radius=30,
                spread_radius=2,
                color=f"55{accent[1:]}",
            )
        else:
            e.control.scale = 1.0
            e.control.border = ft.Border.all(1.4, accent)
            e.control.shadow = ft.BoxShadow(
                blur_radius=14,
                spread_radius=0,
                color="#26000000",
            )

        e.control.update()

    # =========================================================
    # CONTINUOUS ORBIT ANIMATION
    # =========================================================

    async def start_orbit_animation(self):
        """
        Start continuous clockwise orbital motion.

        main_window.py should call this once, after page.add(...):

            self.page.run_task(
                self.home_view.start_orbit_animation
            )

        The feature cards move around the center while their text remains
        upright and readable.
        """

        if self._orbit_running:
            return

        self._orbit_running = True

        # Smooth hero entrance. main_window.py starts this task only after
        # the page has been mounted, so the transition is visible instead
        # of appearing already completed.
        if not self._hero_intro_done:
            self._hero_intro_done = True

            if self.hero_copy_panel is not None:
                self.hero_copy_panel.opacity = 1
                self.hero_copy_panel.offset = ft.Offset(0, 0)

            if self.hero_visual_panel is not None:
                self.hero_visual_panel.opacity = 1
                self.hero_visual_panel.offset = ft.Offset(0, 0)

            try:
                if self.hero_copy_panel is not None:
                    self.hero_copy_panel.update()

                # Tiny stagger makes the entrance feel more natural.
                await asyncio.sleep(0.08)

                if self.hero_visual_panel is not None:
                    self.hero_visual_panel.update()
            except Exception:
                pass

        center_x = 820 / 2
        center_y = 500 / 2

        node_size = 112
        orbit_radius_x = 300
        orbit_radius_y = 182

        while self._orbit_running:
            try:
                if not self._orbit_paused:
                    # About one full revolution every ~25 seconds.
                    self._orbit_phase = (
                        self._orbit_phase + 1.15
                    ) % 360.0

                    for item in self._orbit_nodes:
                        angle = math.radians(
                            item["base_angle"]
                            + self._orbit_phase
                        )

                        node = item["control"]

                        node.left = (
                            center_x
                            + orbit_radius_x * math.cos(angle)
                            - node_size / 2
                        )

                        node.top = (
                            center_y
                            + orbit_radius_y * math.sin(angle)
                            - node_size / 2
                        )

                    # ---------------------------------------------
                    # Animate the central logo at the same time.
                    # Outer and inner decorative halos rotate in
                    # opposite directions while the actual logo stays
                    # upright and gently pulses.
                    # ---------------------------------------------

                    if self.logo_rotor_outer is not None:
                        self.logo_rotor_outer.rotate = math.radians(
                            self._orbit_phase * 1.6
                        )

                    if self.logo_rotor_inner is not None:
                        self.logo_rotor_inner.rotate = math.radians(
                            -self._orbit_phase * 1.15
                        )

                    if self.logo_core is not None:
                        pulse = (
                            1.0
                            + 0.025
                            * (
                                0.5
                                + 0.5
                                * math.sin(
                                    math.radians(
                                        self._orbit_phase * 3.0
                                    )
                                )
                            )
                        )

                        self.logo_core.scale = pulse

                    # ---------------------------------------------
                    # HERO SIGNAL WORKSPACE FLOW
                    # ---------------------------------------------

                    # Faster, smaller steps make the motion feel continuous.
                    phase_speed = (
                        8.0
                        if self._signal_hovered
                        else 5.2
                    )

                    scan_speed = (
                        2.8
                        if self._signal_hovered
                        else 1.75
                    )

                    amplitude_boost = (
                        1.15
                        if self._signal_hovered
                        else 1.0
                    )

                    self._signal_phase = (
                        self._signal_phase + phase_speed
                    ) % 360.0

                    self._signal_scan_phase = (
                        self._signal_scan_phase + scan_speed
                    ) % 100.0

                    if self._signal_bars:
                        for index, bar in enumerate(
                            self._signal_bars
                        ):
                            phase = math.radians(
                                self._signal_phase
                                + index * 22
                            )

                            # Three harmonics create a more organic wave.
                            wave = (
                                0.58 * math.sin(phase)
                                + 0.27 * math.sin(
                                    phase * 1.85 + 0.65
                                )
                                + 0.15 * math.sin(
                                    phase * 3.2 + index * 0.11
                                )
                            )

                            normalized = max(
                                0.0,
                                min(
                                    1.0,
                                    (wave + 1.0) / 2.0,
                                ),
                            )

                            bar.height = (
                                22
                                + normalized
                                * 78
                                * amplitude_boost
                            )

                            bar.opacity = (
                                0.52
                                + normalized * 0.48
                            )

                    # One-way scanner rather than a back-and-forth sweep.
                    if self.signal_scan_line is not None:
                        self.signal_scan_line.left = (
                            8
                            + (
                                self._signal_scan_phase
                                / 100.0
                            )
                            * self._signal_scan_span
                        )

                    # Moving energy particles.
                    for index, particle in enumerate(
                        self._signal_particles
                    ):
                        progress = (
                            (
                                self._signal_scan_phase
                                + index * 22
                            )
                            % 100.0
                        ) / 100.0

                        particle.left = (
                            14 + progress * (self._signal_scan_span - 10)
                        )

                        particle.top = (
                            18
                            + 34
                            * (
                                0.5
                                + 0.5
                                * math.sin(
                                    math.radians(
                                        self._signal_phase
                                        + index * 70
                                    )
                                )
                            )
                        )

                        particle.opacity = (
                            0.25
                            + 0.55
                            * (
                                0.5
                                + 0.5
                                * math.sin(
                                    math.radians(
                                        self._signal_phase * 1.4
                                        + index * 80
                                    )
                                )
                            )
                        )

                    # Smooth LIVE pulse.
                    if self.signal_live_dot is not None:
                        live_wave = (
                            0.5
                            + 0.5
                            * math.sin(
                                math.radians(
                                    self._signal_phase * 2.0
                                )
                            )
                        )

                        self.signal_live_dot.scale = (
                            0.86 + live_wave * 0.52
                        )

                    # Hero readiness indicator breathes more slowly than
                    # the LIVE signal so the page stays calm.
                    if self.hero_status_dot is not None:
                        self.hero_status_dot.scale = (
                            0.92
                            + 0.16
                            * (
                                0.5
                                + 0.5
                                * math.sin(
                                    math.radians(
                                        self._signal_phase * 0.72
                                    )
                                )
                            )
                        )

                    # Slow ambient hero light movement.
                    ambient_wave = (
                        0.5
                        + 0.5
                        * math.sin(
                            math.radians(
                                self._signal_phase * 0.7
                            )
                        )
                    )

                    if self.hero_glow_left is not None:
                        self.hero_glow_left.scale = (
                            0.96 + ambient_wave * 0.12
                        )
                        self.hero_glow_left.opacity = (
                            0.35 + ambient_wave * 0.30
                        )

                    if self.hero_glow_right is not None:
                        inverse_wave = 1.0 - ambient_wave
                        self.hero_glow_right.scale = (
                            0.96 + inverse_wave * 0.13
                        )
                        self.hero_glow_right.opacity = (
                            0.34 + inverse_wave * 0.30
                        )

                    if self.orbit_stack is not None:
                        self.orbit_stack.update()

                    if self.signal_console is not None:
                        self.signal_console.update()

                    if self.hero_glow_left is not None:
                        self.hero_glow_left.update()

                    if self.hero_glow_right is not None:
                        self.hero_glow_right.update()

                # ~12.5 updates per second. The implicit animations interpolate
                # between updates, producing smooth motion without excessive UI load.
                await asyncio.sleep(0.08)

            except Exception:
                # The Home page can be temporarily detached while the user
                # is inside another workspace. Keep the task alive safely.
                await asyncio.sleep(0.5)

    def stop_orbit_animation(self):
        self._orbit_running = False

    def _hover_signal_console(self, e):
        hovered = self._is_hovered(e.data)
        self._signal_hovered = hovered

        if hovered:
            e.control.scale = 1.012
            e.control.offset = ft.Offset(0, -0.012)
            e.control.border = ft.Border.all(1.4, AppColors.CYAN)
            e.control.shadow = ft.BoxShadow(
                blur_radius=30,
                spread_radius=1,
                color="#3922D3EE",
                offset=ft.Offset(0, 10),
            )

            if self.signal_frequency_text is not None:
                self.signal_frequency_text.value = (
                    "CLICK TO OPEN FREQUENCY LAB  →"
                )
                self.signal_frequency_text.color = AppColors.WHITE
        else:
            e.control.scale = 1.0
            e.control.offset = ft.Offset(0, 0)
            e.control.border = ft.Border.all(1, "#34455E")
            e.control.shadow = ft.BoxShadow(
                blur_radius=22,
                color="#28000000",
                offset=ft.Offset(0, 8),
            )

            if self.signal_frequency_text is not None:
                self.signal_frequency_text.value = (
                    "LIVE SIGNAL • 2D IMAGE DOMAIN"
                )
                self.signal_frequency_text.color = AppColors.CYAN_LIGHT

        e.control.update()
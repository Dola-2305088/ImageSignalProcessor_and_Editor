import flet as ft

from ui.theme import AppColors, AppLayout, AppAnimations


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
        self.control = self._build()

    # =========================================================
    # ROOT
    # =========================================================

    def _build(self):
        self.session_name_text = ft.Text(
            "No active image",
            size=10,
            color=AppColors.MUTED,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        return ft.Column(
            spacing=18,
            controls=[
                self._build_hero(),
                self._build_explore_lab(),
                self._build_capability_strip(),
                ft.Container(height=8),
            ],
        )

    # =========================================================
    # HERO — KEPT IN THE SAME STYLE
    # =========================================================

    def _build_hero(self):
        ready_badge = ft.Container(
            padding=ft.Padding.symmetric(horizontal=11, vertical=6),
            bgcolor="#0B1D1A",
            border=ft.Border.all(1, "#17483D"),
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
                        size=8,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.GREEN_LIGHT,
                    ),
                ],
            ),
        )

        start_button = ft.Button(
            content="Start New Session",
            icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
            on_click=self.on_start_session,
            bgcolor=AppColors.BLUE,
            color=AppColors.WHITE,
            elevation=0,
        )

        browse_button = ft.OutlinedButton(
            content="Browse Image",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self.on_open_image,
            style=ft.ButtonStyle(
                color=AppColors.CYAN_LIGHT,
                side=ft.BorderSide(1, AppColors.BORDER_LIGHT),
            ),
        )

        left = ft.Column(
            expand=True,
            spacing=15,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Row(controls=[ready_badge]),
                ft.Text(
                    "SIGNAL STUDIO",
                    size=10,
                    weight=ft.FontWeight.BOLD,
                    color=AppColors.CYAN,
                ),
                ft.Text(
                    "Image Signal Processor\n& Editor",
                    size=38,
                    weight=ft.FontWeight.BOLD,
                    color=AppColors.TEXT,
                    height=1.05,
                ),
                ft.Container(
                    width=86,
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
                    "Explore images as two-dimensional signals through spatial "
                    "filtering, Fourier analysis, compression, texture and color.",
                    size=12,
                    color=AppColors.MUTED,
                    height=1.5,
                ),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    controls=[start_button, browse_button],
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=11, vertical=8),
                    bgcolor="#0A111D",
                    border=ft.Border.all(1, AppColors.BORDER_SOFT),
                    border_radius=11,
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(
                                ft.Icons.INSERT_PHOTO_OUTLINED,
                                size=15,
                                color=AppColors.MUTED_2,
                            ),
                            ft.Text(
                                "Current session",
                                size=9,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.MUTED_2,
                            ),
                            ft.Container(expand=True),
                            self.session_name_text,
                        ],
                    ),
                ),
            ],
        )

        # Keep the existing right-side Signal Workspace visual.
        right = self._build_signal_console()

        return ft.Container(
            height=350,
            padding=ft.Padding.symmetric(horizontal=30, vertical=26),
            border_radius=ft.BorderRadius.all(24),
            border=ft.Border.all(1, AppColors.BORDER),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#0D1728", "#0C1220", "#181126"],
            ),
            shadow=ft.BoxShadow(
                blur_radius=32,
                spread_radius=0,
                color="#26000000",
                offset=ft.Offset(0, 12),
            ),
            content=ft.Row(
                spacing=26,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[left, right],
            ),
        )

    # =========================================================
    # SIGNAL CONSOLE VISUAL — UNCHANGED STYLE
    # =========================================================

    def _build_signal_console(self):
        heights = [35, 58, 82, 52, 96, 68, 42, 75, 54, 88, 48]
        bars = []

        for index, height in enumerate(heights):
            if index % 3 == 0:
                accent = AppColors.CYAN
            elif index % 3 == 1:
                accent = AppColors.PURPLE
            else:
                accent = AppColors.PINK

            bars.append(
                ft.Container(
                    width=11,
                    height=height,
                    bgcolor=accent,
                    opacity=0.80,
                    border_radius=6,
                )
            )

        waveform = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=7,
            controls=bars,
        )

        self.signal_console = ft.Container(
            width=330,
            height=260,
            padding=20,
            border_radius=ft.BorderRadius.all(22),
            border=ft.Border.all(1, "#34435F"),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#0B1525", "#12172B", "#21152D"],
            ),
            animate_scale=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            on_hover=self._hover_signal_console,
            content=ft.Column(
                spacing=15,
                controls=[
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
                                    colors=[AppColors.CYAN, AppColors.PURPLE],
                                ),
                                content=ft.Icon(
                                    ft.Icons.WAVES,
                                    size=24,
                                    color=AppColors.BLACK,
                                ),
                            ),
                            ft.Column(
                                spacing=1,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        "SIGNAL WORKSPACE",
                                        size=10,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.CYAN_LIGHT,
                                    ),
                                    ft.Text(
                                        "Spatial • Frequency • Restoration",
                                        size=9,
                                        color=AppColors.MUTED,
                                    ),
                                ],
                            ),
                            ft.Container(
                                padding=ft.Padding.symmetric(
                                    horizontal=8, vertical=4
                                ),
                                border_radius=100,
                                bgcolor="#0B1D1A",
                                content=ft.Text(
                                    "LIVE",
                                    size=8,
                                    weight=ft.FontWeight.BOLD,
                                    color=AppColors.GREEN_LIGHT,
                                ),
                            ),
                        ],
                    ),
                    ft.Container(
                        expand=True,
                        alignment=ft.Alignment.CENTER,
                        bgcolor="#070B13",
                        border=ft.Border.all(1, AppColors.BORDER_SOFT),
                        border_radius=16,
                        content=waveform,
                    ),
                    ft.Row(
                        controls=[
                            self._mini_console_metric(
                                "2D", "SIGNALS", AppColors.CYAN
                            ),
                            self._mini_console_metric(
                                "DFT", "DOMAIN", AppColors.PURPLE
                            ),
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
            content=ft.Column(
                spacing=1,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        value,
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=accent,
                    ),
                    ft.Text(
                        label,
                        size=7,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.MUTED_2,
                    ),
                ],
            ),
        )

    # =========================================================
    # EXPLORE THE LAB — ROUND ORBITAL INTERFACE
    # =========================================================

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
        Fixed-size orbital canvas inside a horizontally scrollable wrapper.

        This is intentionally built with Stack + positioned Containers.
        No experimental animation loop is used: hover is local, simple,
        and reliable.
        """

        canvas_width = 820
        canvas_height = 500

        center_x = canvas_width / 2
        center_y = canvas_height / 2

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

        core = ft.Container(
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
        # SIX ROUND INTERACTIVE NODES
        # -----------------------------------------------------

        node_size = 112

        nodes = [
            # Top
            self._orbit_node(
                left=center_x - node_size / 2,
                top=18,
                size=node_size,
                title="Frequency",
                badge="FEATURE 4",
                icon=ft.Icons.TUNE,
                accent=AppColors.CYAN,
                tint="#0B2630",
                handler=lambda e: self._navigate(1),
            ),

            # Upper-right
            self._orbit_node(
                left=620,
                top=112,
                size=node_size,
                title="Compression",
                badge="FEATURE 5",
                icon=ft.Icons.BAR_CHART,
                accent=AppColors.GREEN,
                tint="#0B2A21",
                handler=lambda e: self._navigate(2),
            ),

            # Lower-right
            self._orbit_node(
                left=620,
                top=300,
                size=node_size,
                title="Texture",
                badge="FEATURE 8",
                icon=ft.Icons.GRID_VIEW,
                accent=AppColors.ORANGE,
                tint="#2A210E",
                handler=lambda e: self._navigate(3),
            ),

            # Bottom
            self._orbit_node(
                left=center_x - node_size / 2,
                top=370,
                size=node_size,
                title="New Session",
                badge="OPEN IMAGE",
                icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
                accent=AppColors.BLUE,
                tint="#10284A",
                handler=self.on_start_session,
            ),

            # Lower-left
            self._orbit_node(
                left=88,
                top=300,
                size=node_size,
                title="Hybrid",
                badge="FEATURE 9",
                icon=ft.Icons.AUTO_AWESOME,
                accent=AppColors.PINK,
                tint="#301121",
                handler=lambda e: self._navigate(4),
            ),

            # Upper-left
            self._orbit_node(
                left=88,
                top=112,
                size=node_size,
                title="Color Lab",
                badge="FEATURE 12",
                icon=ft.Icons.PALETTE,
                accent=AppColors.PURPLE,
                tint="#241636",
                handler=lambda e: self._navigate(5),
            ),
        ]

        # -----------------------------------------------------
        # SMALL DECORATIVE SIGNAL POINTS
        # -----------------------------------------------------

        decorations = [
            self._signal_dot(244, 56, AppColors.CYAN),
            self._signal_dot(560, 55, AppColors.PURPLE),
            self._signal_dot(715, 250, AppColors.GREEN),
            self._signal_dot(535, 432, AppColors.PINK),
            self._signal_dot(280, 437, AppColors.ORANGE),
            self._signal_dot(101, 250, AppColors.BLUE),
        ]

        orbit_stack = ft.Stack(
            width=canvas_width,
            height=canvas_height,
            controls=[
                *rings,
                *decorations,
                core,
                *nodes,
            ],
        )

        # Scroll only when needed on a smaller desktop window.
        return ft.Container(
            height=520,
            alignment=ft.Alignment.CENTER,
            bgcolor="#070C15",
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            border_radius=ft.BorderRadius.all(19),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                controls=[orbit_stack],
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
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=18, vertical=14),
            bgcolor="#090E17",
            border=ft.Border.all(1, AppColors.BORDER),
            border_radius=ft.BorderRadius.all(17),
            content=ft.Row(
                controls=[
                    self._capability("12", "DSP FEATURES", AppColors.CYAN),
                    self._separator(),
                    self._capability("2D", "MANUAL DFT", AppColors.PURPLE),
                    self._separator(),
                    self._capability("PSNR", "QUALITY", AppColors.GREEN),
                    self._separator(),
                    self._capability("RGB", "CHANNELS", AppColors.RED),
                    self._separator(),
                    self._capability("YCbCr", "COLOR SPACE", AppColors.ORANGE),
                    self._separator(),
                    self._capability("LIVE", "PREVIEW", AppColors.PINK),
                ],
            ),
        )

    def _capability(self, value, label, accent):
        return ft.Container(
            expand=True,
            content=ft.Column(
                spacing=1,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        value,
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=accent,
                    ),
                    ft.Text(
                        label,
                        size=7,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

    def _separator(self):
        return ft.Container(
            width=1,
            height=32,
            bgcolor=AppColors.BORDER,
        )

    # =========================================================
    # PUBLIC SESSION STATE
    # =========================================================

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

    def _hover_signal_console(self, e):
        hovered = self._is_hovered(e.data)
        e.control.scale = 1.012 if hovered else 1.0
        e.control.update()
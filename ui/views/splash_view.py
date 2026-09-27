import asyncio
import math
import random
import time

import flet as ft
import flet.canvas as fc


class SplashView:
    """
    AETHERIS cinematic galaxy splash screen.

    Designed as a drop-in replacement for the existing SplashView:
        self.control -> root splash control
        await self.play() -> runs the intro and hides the splash
        self.stop() -> stops the animation

    Put ``self.control`` last in the application's root Stack so it stays
    above the HomeView while the splash is playing.
    """

    FRAME_INTERVAL = 0.025

    # Stage coordinates. The stage itself is centered inside the window.
    STAGE_W = 1000
    STAGE_H = 700
    LOGO_CX = 500
    LOGO_CY = 265

    def __init__(self):
        self._running = False
        self._phase = 0.0
        self._spark_phase = 0.0
        self._orbit_nodes = []

        self.logo_glow = None
        self.logo_shell = None
        self.brand_group = None
        self.status_text = None
        self.progress_bar = None
        self.progress_value = None
        self.launch_panel = None
        self.main_flare = None
        self.ornament = None

        self.control = self._build()

    # =========================================================
    # BACKGROUND ART
    # =========================================================

    @staticmethod
    def _star_field(width: int, height: int):
        """Deterministic star field so the splash looks identical each run."""
        rng = random.Random(42)
        shapes = []

        # Tiny distant stars.
        for _ in range(155):
            x = rng.uniform(18, width - 18)
            y = rng.uniform(16, height - 16)
            r = rng.choice([0.45, 0.55, 0.65, 0.75, 0.95])
            color = rng.choice(
                [
                    "#62FFFFFF",
                    "#54DDE8FF",
                    "#55B8C7FF",
                    "#55FFD3EA",
                    "#6BD9D4FF",
                ]
            )
            shapes.append(
                fc.Circle(
                    x,
                    y,
                    r,
                    paint=ft.Paint(
                        style=ft.PaintingStyle.FILL,
                        color=color,
                    ),
                )
            )

        # A handful of crisp four-point stars.
        for x, y, s, color in [
            (198, 170, 5, "#D9FFC5F2"),
            (322, 94, 3.8, "#BCE9E6FF"),
            (768, 194, 4.0, "#D5DBE8FF"),
            (862, 334, 3.2, "#BDEEE5FF"),
            (680, 82, 3.0, "#A6D8E1FF"),
            (112, 348, 3.8, "#B9FFB7E7"),
        ]:
            shapes.append(
                fc.Path(
                    elements=[
                        fc.Path.MoveTo(x, y - s),
                        fc.Path.LineTo(x + s * 0.25, y - s * 0.25),
                        fc.Path.LineTo(x + s, y),
                        fc.Path.LineTo(x + s * 0.25, y + s * 0.25),
                        fc.Path.LineTo(x, y + s),
                        fc.Path.LineTo(x - s * 0.25, y + s * 0.25),
                        fc.Path.LineTo(x - s, y),
                        fc.Path.LineTo(x - s * 0.25, y - s * 0.25),
                        fc.Path.Close(),
                    ],
                    paint=ft.Paint(
                        style=ft.PaintingStyle.FILL,
                        color=color,
                    ),
                )
            )

        return fc.Canvas(width=width, height=height, shapes=shapes)

    @staticmethod
    def _logo_canvas(size: int = 270):
        """
        A stylized AETHERIS aperture mark inspired by the supplied Vespera art:
        celestial ring + luminous orbital sweep + four-point flare + elegant A.
        """
        cx = cy = size / 2
        shapes = []

        # -----------------------------------------------------
        # Celestial halo / circle
        # -----------------------------------------------------
        shapes.append(
            fc.Oval(
                cx - 84,
                cy - 84,
                168,
                168,
                paint=ft.Paint(
                    style=ft.PaintingStyle.STROKE,
                    stroke_width=5.5,
                    color="#165E68FF",
                ),
            )
        )
        shapes.append(
            fc.Oval(
                cx - 84,
                cy - 84,
                168,
                168,
                paint=ft.Paint(
                    style=ft.PaintingStyle.STROKE,
                    stroke_width=1.35,
                    color="#CCEDEBFF",
                ),
            )
        )

        # -----------------------------------------------------
        # Stylized capital A - glow pass, then core pass.
        # -----------------------------------------------------
        a_elements = [
            fc.Path.MoveTo(cx - 55, cy + 48),
            fc.Path.LineTo(cx, cy - 65),
            fc.Path.LineTo(cx + 55, cy + 48),
        ]

        shapes.append(
            fc.Path(
                elements=a_elements,
                paint=ft.Paint(
                    style=ft.PaintingStyle.STROKE,
                    stroke_width=13,
                    color="#2DFF7BB8",
                ),
            )
        )
        shapes.append(
            fc.Path(
                elements=[
                    fc.Path.MoveTo(cx - 55, cy + 48),
                    fc.Path.LineTo(cx, cy - 65),
                    fc.Path.LineTo(cx + 55, cy + 48),
                ],
                paint=ft.Paint(
                    style=ft.PaintingStyle.STROKE,
                    stroke_width=4.0,
                    color="#FFF0D5FF",
                ),
            )
        )

        # A cross-bar that feels like a signal aperture.
        shapes.append(
            fc.Path(
                elements=[
                    fc.Path.MoveTo(cx - 25, cy + 10),
                    fc.Path.LineTo(cx + 25, cy + 10),
                ],
                paint=ft.Paint(
                    style=ft.PaintingStyle.STROKE,
                    stroke_width=8.0,
                    color="#268F72FF",
                ),
            )
        )
        shapes.append(
            fc.Path(
                elements=[
                    fc.Path.MoveTo(cx - 25, cy + 10),
                    fc.Path.LineTo(cx + 25, cy + 10),
                ],
                paint=ft.Paint(
                    style=ft.PaintingStyle.STROKE,
                    stroke_width=2.6,
                    color="#FFEEDAFF",
                ),
            )
        )

        # -----------------------------------------------------
        # Orbital sweep across the lower half.
        # Two passes create the neon/luminous look.
        # -----------------------------------------------------
        orbit_elements = [
            fc.Path.MoveTo(cx - 112, cy + 39),
            fc.Path.CubicTo(
                cx - 88,
                cy + 78,
                cx + 67,
                cy + 74,
                cx + 112,
                cy + 8,
            ),
        ]
        shapes.append(
            fc.Path(
                elements=orbit_elements,
                paint=ft.Paint(
                    style=ft.PaintingStyle.STROKE,
                    stroke_width=11.0,
                    color="#2C8B65FF",
                ),
            )
        )
        shapes.append(
            fc.Path(
                elements=[
                    fc.Path.MoveTo(cx - 112, cy + 39),
                    fc.Path.CubicTo(
                        cx - 88,
                        cy + 78,
                        cx + 67,
                        cy + 74,
                        cx + 112,
                        cy + 8,
                    ),
                ],
                paint=ft.Paint(
                    style=ft.PaintingStyle.STROKE,
                    stroke_width=3.0,
                    color="#FFF2D0FF",
                ),
            )
        )

        # Small violet continuation at the right side of the orbit.
        shapes.append(
            fc.Path(
                elements=[
                    fc.Path.MoveTo(cx + 38, cy + 61),
                    fc.Path.CubicTo(
                        cx + 76,
                        cy + 51,
                        cx + 104,
                        cy + 30,
                        cx + 112,
                        cy + 8,
                    ),
                ],
                paint=ft.Paint(
                    style=ft.PaintingStyle.STROKE,
                    stroke_width=3.2,
                    color="#C2A98CFF",
                ),
            )
        )

        # -----------------------------------------------------
        # Four-point cosmic flare above the aperture.
        # -----------------------------------------------------
        sx, sy = cx, cy - 26
        shapes.append(
            fc.Path(
                elements=[
                    fc.Path.MoveTo(sx, sy - 38),
                    fc.Path.LineTo(sx + 5.2, sy - 5.2),
                    fc.Path.LineTo(sx + 31, sy),
                    fc.Path.LineTo(sx + 5.2, sy + 5.2),
                    fc.Path.LineTo(sx, sy + 38),
                    fc.Path.LineTo(sx - 5.2, sy + 5.2),
                    fc.Path.LineTo(sx - 31, sy),
                    fc.Path.LineTo(sx - 5.2, sy - 5.2),
                    fc.Path.Close(),
                ],
                paint=ft.Paint(
                    style=ft.PaintingStyle.FILL,
                    color="#FFF4E4FF",
                ),
            )
        )
        shapes.append(
            fc.Circle(
                sx,
                sy,
                5.4,
                paint=ft.Paint(
                    style=ft.PaintingStyle.FILL,
                    color="#FFFFFFFF",
                ),
            )
        )

        return fc.Canvas(width=size, height=size, shapes=shapes)

    # =========================================================
    # BUILD
    # =========================================================

    def _build(self):
        w = self.STAGE_W
        h = self.STAGE_H
        cx = self.LOGO_CX
        cy = self.LOGO_CY

        stage = ft.Stack(
            width=w,
            height=h,
            controls=[],
        )

        # -----------------------------------------------------
        # Space background layers
        # -----------------------------------------------------
        stage.controls.append(self._star_field(w, h))

        # Purple nebula glow on left.
        stage.controls.append(
            ft.Container(
                left=55,
                top=165,
                width=320,
                height=320,
                border_radius=999,
                bgcolor="#06150B24",
                shadow=ft.BoxShadow(
                    blur_radius=125,
                    spread_radius=20,
                    color="#4824105F",
                ),
            )
        )

        # Blue-violet nebula glow on right.
        stage.controls.append(
            ft.Container(
                left=640,
                top=285,
                width=280,
                height=210,
                border_radius=999,
                bgcolor="#040C1734",
                shadow=ft.BoxShadow(
                    blur_radius=115,
                    spread_radius=12,
                    color="#3A183A86",
                ),
            )
        )

        # Upper-right small planet.
        stage.controls.append(
            ft.Container(
                left=842,
                top=38,
                width=125,
                height=125,
                border_radius=999,
                bgcolor="#E8030710",
                border=ft.Border.all(1.1, "#695D6FFF"),
                shadow=ft.BoxShadow(
                    blur_radius=22,
                    spread_radius=-1,
                    color="#7A374FC8",
                ),
            )
        )

        # Large lower-left planet entering the frame.
        stage.controls.append(
            ft.Container(
                left=-235,
                top=510,
                width=390,
                height=390,
                border_radius=999,
                bgcolor="#F0040610",
                border=ft.Border.all(1.4, "#8D5A4FCE"),
                shadow=ft.BoxShadow(
                    blur_radius=40,
                    spread_radius=2,
                    color="#8A2B0F5C",
                ),
            )
        )

        # A thin violet rim just inside the large planet edge.
        stage.controls.append(
            ft.Container(
                left=-229,
                top=516,
                width=378,
                height=378,
                border_radius=999,
                border=ft.Border.all(1.0, "#6E7558F0"),
            )
        )

        # -----------------------------------------------------
        # Main logo area
        # -----------------------------------------------------
        self.logo_glow = ft.Container(
            left=cx - 115,
            top=cy - 115,
            width=230,
            height=230,
            border_radius=999,
            opacity=0.0,
            scale=0.74,
            bgcolor="#04000000",
            animate_opacity=ft.Animation(700, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(900, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(
                blur_radius=72,
                spread_radius=12,
                color="#62652B91",
            ),
        )
        stage.controls.append(self.logo_glow)

        self.logo_shell = ft.Container(
            left=cx - 135,
            top=cy - 135,
            width=270,
            height=270,
            opacity=0.0,
            scale=0.72,
            alignment=ft.Alignment.CENTER,
            animate_opacity=ft.Animation(560, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(920, ft.AnimationCurve.EASE_OUT),
            content=self._logo_canvas(270),
        )
        stage.controls.append(self.logo_shell)

        # Separate animated flare layered over the canvas.
        self.main_flare = ft.Container(
            left=cx - 6,
            top=cy - 32,
            width=12,
            height=12,
            border_radius=99,
            opacity=0.0,
            scale=0.6,
            bgcolor="#FFFDF6",
            animate_opacity=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(
                blur_radius=28,
                spread_radius=5,
                color="#A8FFD7A0",
            ),
        )
        stage.controls.append(self.main_flare)

        # Three moving glints along the imaginary orbital system.
        node_specs = [
            ("#FFF0B7", 0.15, 119),
            ("#B59BFF", 2.30, 119),
            ("#FF9DCB", 4.25, 119),
        ]
        for color, base_angle, radius in node_specs:
            node = ft.Container(
                width=4.8,
                height=4.8,
                left=cx - 2.4,
                top=cy - 2.4,
                opacity=0.0,
                border_radius=99,
                bgcolor=color,
                shadow=ft.BoxShadow(
                    blur_radius=12,
                    spread_radius=1,
                    color="#88FFFFFF",
                ),
                animate_position=ft.Animation(55, ft.AnimationCurve.LINEAR),
                animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            )
            stage.controls.append(node)
            self._orbit_nodes.append((node, base_angle, radius))

        # -----------------------------------------------------
        # AETHERIS wordmark and subtitle
        # -----------------------------------------------------
        brand_name = ft.Text(
            "A  E  T  H  E  R  I  S",
            size=50,
            weight=ft.FontWeight.W_400,
            color="#FFF4EA",
            font_family="Georgia",
            text_align=ft.TextAlign.CENTER,
        )

        subtitle = ft.Text(
            "D I G I T A L   I M A G I N G   L A B",
            size=11,
            weight=ft.FontWeight.W_500,
            color="#F1BE88",
            text_align=ft.TextAlign.CENTER,
        )

        subtitle_row = ft.Row(
            width=540,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
            controls=[
                ft.Container(width=78, height=1, bgcolor="#846B4D"),
                subtitle,
                ft.Container(width=78, height=1, bgcolor="#846B4D"),
            ],
        )

        self.status_text = ft.Text(
            "Awakening the imaging engine",
            size=8.5,
            color="#6F7893",
            text_align=ft.TextAlign.CENTER,
        )

        self.progress_bar = ft.ProgressBar(
            value=0.0,
            width=180,
            height=1.5,
            bgcolor="#182033",
            color="#E9B77D",
            border_radius=99,
        )

        self.progress_value = ft.Text(
            "0%",
            size=7.5,
            color="#5F6A81",
        )

        self.brand_group = ft.Container(
            left=cx - 310,
            top=420,
            width=620,
            opacity=0.0,
            offset=ft.Offset(0, 0.10),
            animate_opacity=ft.Animation(700, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(760, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=13,
                controls=[
                    brand_name,
                    subtitle_row,
                    ft.Container(height=8),
                    self.status_text,
                    ft.Row(
                        tight=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            self.progress_bar,
                            self.progress_value,
                        ],
                    ),
                ],
            ),
        )
        stage.controls.append(self.brand_group)

        # -----------------------------------------------------
        # Bottom ornamental divider, matching the reference mood
        # -----------------------------------------------------
        self.ornament = ft.Container(
            left=cx - 100,
            top=607,
            width=200,
            opacity=0.0,
            animate_opacity=ft.Animation(800, ft.AnimationCurve.EASE_OUT),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=7,
                controls=[
                    ft.Container(width=54, height=1, bgcolor="#594F5A"),
                    ft.Container(width=3, height=3, border_radius=99, bgcolor="#E5B57D"),
                    ft.Text("✦", size=15, color="#F1BE88"),
                    ft.Container(width=3, height=3, border_radius=99, bgcolor="#E5B57D"),
                    ft.Container(width=54, height=1, bgcolor="#594F5A"),
                ],
            ),
        )
        stage.controls.append(self.ornament)

        self.launch_panel = ft.Container(
            width=w,
            height=h,
            opacity=1.0,
            scale=1.0,
            animate_opacity=ft.Animation(650, ft.AnimationCurve.EASE_IN_OUT),
            animate_scale=ft.Animation(820, ft.AnimationCurve.EASE_IN_OUT),
            content=stage,
        )

        # Root black-violet space background.
        return ft.Container(
            expand=True,
            visible=True,
            opacity=1.0,
            alignment=ft.Alignment.CENTER,
            bgcolor="#02040B",
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[
                    "#02040B",
                    "#040714",
                    "#090615",
                    "#02040B",
                ],
            ),
            animate_opacity=ft.Animation(650, ft.AnimationCurve.EASE_IN_OUT),
            content=self.launch_panel,
        )

    # =========================================================
    # ANIMATION HELPERS
    # =========================================================

    def _place_orbit_nodes(self):
        """Move tiny luminous particles around a flattened orbit."""
        cx = self.LOGO_CX
        cy = self.LOGO_CY + 12

        for index, (node, base_angle, radius) in enumerate(self._orbit_nodes):
            angle = base_angle + self._phase * (1.0 + index * 0.06)
            aspect = 0.35

            node.left = cx + math.cos(angle) * radius - 2.4
            node.top = cy + math.sin(angle) * radius * aspect - 2.4

    def _safe_update(self, control):
        try:
            control.update()
            return True
        except Exception:
            return False

    # =========================================================
    # PUBLIC ANIMATION API
    # =========================================================

    async def play(self):
        """
        Runs the complete AETHERIS intro and then fades it away.

        Typical use:
            page.run_task(self.splash_view.play)
        """
        if self._running:
            return

        self._running = True
        self.control.visible = True
        self.control.opacity = 1.0

        await asyncio.sleep(0.08)

        # 1) Nebula/logo awakening.
        self.logo_glow.opacity = 1.0
        self.logo_glow.scale = 1.0
        self.logo_shell.opacity = 1.0
        self.logo_shell.scale = 1.0
        self.main_flare.opacity = 1.0
        self.main_flare.scale = 1.0

        for node, _, _ in self._orbit_nodes:
            node.opacity = 0.88

        if not self._safe_update(self.control):
            self._running = False
            return

        await asyncio.sleep(0.32)

        # 2) Wordmark glides in after the emblem.
        self.brand_group.opacity = 1.0
        self.brand_group.offset = ft.Offset(0, 0)
        self.ornament.opacity = 1.0

        if not self._safe_update(self.control):
            self._running = False
            return

        # 3) Loading sequence while the orbital glints and flare remain alive.
        stages = [
            (0.06, "Calibrating celestial workspace"),
            (0.26, "Initializing spatial engine"),
            (0.50, "Synchronizing frequency domain"),
            (0.74, "Preparing restoration pipeline"),
            (0.92, "Finalizing Aetheris interface"),
            (1.00, "Workspace ready"),
        ]
        stage_index = 0

        start = time.monotonic()
        duration = 2.70
        last = start

        while self._running:
            await asyncio.sleep(self.FRAME_INTERVAL)

            now = time.monotonic()
            dt = now - last
            elapsed = now - start
            last = now

            self._phase += 0.72 * dt
            self._spark_phase += 3.25 * dt
            self._place_orbit_nodes()

            progress = min(1.0, elapsed / duration)

            while stage_index < len(stages) and progress >= stages[stage_index][0]:
                _, message = stages[stage_index]
                self.status_text.value = message
                stage_index += 1

            self.progress_bar.value = progress
            self.progress_value.value = f"{round(progress * 100):d}%"

            # Slow breathing halo.
            halo_pulse = 0.5 + 0.5 * math.sin(elapsed * 2.4)
            self.logo_glow.shadow = ft.BoxShadow(
                blur_radius=62 + 20 * halo_pulse,
                spread_radius=8 + 5 * halo_pulse,
                color="#62652B91",
            )

            # Tiny flare shimmer without aggressive scaling.
            flare_pulse = 0.5 + 0.5 * math.sin(self._spark_phase)
            self.main_flare.scale = 0.92 + 0.18 * flare_pulse
            self.main_flare.opacity = 0.72 + 0.28 * flare_pulse

            # Microscopic logo breathing keeps it cinematic, not bouncy.
            self.logo_shell.scale = 1.0 + 0.008 * math.sin(elapsed * 2.0)

            if not self._safe_update(self.launch_panel):
                break

            if progress >= 1.0:
                break

        if not self._running:
            return

        # Completed state.
        self.progress_bar.value = 1.0
        self.progress_value.value = "100%"
        self.status_text.value = "Workspace ready"
        self.logo_shell.scale = 1.025
        self.main_flare.scale = 1.30

        if not self._safe_update(self.launch_panel):
            self._running = False
            return

        await asyncio.sleep(0.38)

        # 4) Premium handoff into the already-rendered HomeView.
        self.launch_panel.scale = 1.022
        self.launch_panel.opacity = 0.0
        self.control.opacity = 0.0

        if not self._safe_update(self.control):
            self._running = False
            return

        await asyncio.sleep(0.68)

        self.control.visible = False
        self._running = False
        self._safe_update(self.control)

    def stop(self):
        self._running = False
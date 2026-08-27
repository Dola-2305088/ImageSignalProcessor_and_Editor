import asyncio
import math
import time
from datetime import datetime
import flet as ft
import flet.canvas as fc

from ui.theme import AppAnimations, AppColors
from ui.app_preferences import WORKSPACE_OPTIONS

GALAXY_IMAGE = "images/Nasa2.jpg"
AETHERIS_ORBIT_LOGO = "images/logo.png"

# Permanent demo projects. These three cards always stay at the top of
# Recent Projects. Put the matching image files inside assets/images/.
DEMO_PROJECTS = [
    {
        "title": "Spatial Blur Study",
        "edited": "Demo Project  •  Spatial Domain",
        "resolution": "1920 × 1080",
        "fmt": "JPG",
        "image": "images/earth.jpg",
    },
    {
        "title": "Frequency Spectrum",
        "edited": "Demo Project  •  Frequency Domain",
        "resolution": "1920 × 1080",
        "fmt": "JPG",
        "image": "images/Moon.jpg",
    },
    {
        "title": "Image Restoration",
        "edited": "Demo Project  •  Wiener Deconvolution",
        "resolution": "1920 × 1080",
        "fmt": "JPG",
        "image": "images/demo.jpg",
    },
]

# Orbit tuning
ORBIT_FRAME_INTERVAL = 0.02          # ~50fps target
ORBIT_ANGULAR_SPEED = 0.28           # radians/sec, independent of frame rate
ORBIT_GLOW_SPEED = 1.6               # breathing speed of the center glow
ORBIT_TRANSITION_MS = int(ORBIT_FRAME_INTERVAL * 1000 * 2.4)  # slight overlap smooths jitter/frame drops
ORBIT_ASPECT = 0.66                  # gives the AETHERIS mark enough vertical breathing room

# Compact center hub. Keeping the hub comfortably smaller than the outer
# feature path makes the six feature bubbles visibly orbit around it.
CENTER_HUB_SIZE = 110
CENTER_LOGO_SIZE = 120
CENTER_GLOW_SIZE = 100

# Same six accent colors used by the orbit nodes below, so the center mark
# reads as "built from" the six operations orbiting it.
LOGO_BLADE_COLORS = ["#6280FF", "#A65CF6", "#2CC8E8", "#8B58E9", "#24B8D1", "#C05AA5"]


def _build_aperture_logo(size: float) -> fc.Canvas:
    """Draws a six-blade aperture mark natively on a canvas (no raster asset,
    stays crisp at any size and themable via LOGO_BLADE_COLORS)."""
    cx = cy = size / 2
    outer_r = size * 0.46
    hole_r = size * 0.16

    def rotate(px, py, angle_deg):
        rad = math.radians(angle_deg)
        dx, dy = px - cx, py - cy
        rx = dx * math.cos(rad) - dy * math.sin(rad)
        ry = dx * math.sin(rad) + dy * math.cos(rad)
        return cx + rx, cy + ry

    base_tip = (cx + outer_r * 0.16, cy - outer_r)
    base_side = (cx + outer_r * 0.52, cy - outer_r * 0.58)

    shapes = []
    for i, color in enumerate(LOGO_BLADE_COLORS):
        angle = i * 60
        tip = rotate(*base_tip, angle)
        side = rotate(*base_side, angle)
        shapes.append(fc.Path(
            elements=[
                fc.Path.MoveTo(cx, cy),
                fc.Path.LineTo(tip[0], tip[1]),
                fc.Path.LineTo(side[0], side[1]),
                fc.Path.Close(),
            ],
            paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color),
        ))

    shapes.append(fc.Circle(cx, cy, hole_r, paint=ft.Paint(style=ft.PaintingStyle.FILL, color="#0B1220")))
    shapes.append(fc.Circle(cx, cy, hole_r, paint=ft.Paint(
        style=ft.PaintingStyle.STROKE, stroke_width=1.5, color="#DCE4F5",
    )))

    return fc.Canvas(width=size, height=size, shapes=shapes)


def _build_orbit_spark_logo(size: float) -> fc.Canvas:
    """Draws the 'orbit and spark' mark: a dashed elliptical rail, a bright
    center star, and a small spark riding the rail — all native canvas shapes."""
    cx = cy = size / 2
    rail_rx = size * 0.36
    rail_ry = size * 0.21
    star_r = size * 0.15
    spark_r = size * 0.055
    spark_angle = math.radians(-50)
    spark_x = cx + rail_rx * math.cos(spark_angle)
    spark_y = cy + rail_ry * math.sin(spark_angle)

    shapes = [
        fc.Oval(
            cx - rail_rx, cy - rail_ry, rail_rx * 2, rail_ry * 2,
            paint=ft.Paint(
                style=ft.PaintingStyle.STROKE, stroke_width=1.4,
                color="#4A5C82", stroke_dash_pattern=[5, 5],
            ),
        ),
        fc.Circle(cx, cy, star_r * 1.7, paint=ft.Paint(style=ft.PaintingStyle.FILL, color="#406280FF")),
        fc.Circle(cx, cy, star_r, paint=ft.Paint(style=ft.PaintingStyle.FILL, color="#EAF1FF")),
        fc.Circle(cx, cy, star_r, paint=ft.Paint(style=ft.PaintingStyle.STROKE, stroke_width=1.5, color="#6280FF")),
        fc.Circle(spark_x, spark_y, spark_r * 1.9, paint=ft.Paint(style=ft.PaintingStyle.FILL, color="#402CC8E8")),
        fc.Circle(spark_x, spark_y, spark_r, paint=ft.Paint(style=ft.PaintingStyle.FILL, color="#2CC8E8")),
    ]

    return fc.Canvas(width=size, height=size, shapes=shapes)



class HomeView:
    """Approved galaxy dashboard; public API remains compatible with main_window.py."""

    def __init__(
        self,
        on_start_session,
        on_open_image,
        on_navigate,
        profile=None,
        on_workspace_change=None,
    ):
        self.on_start_session = on_start_session
        self.on_open_image = on_open_image
        self.on_navigate = on_navigate
        self.profile = profile
        self.on_workspace_change = on_workspace_change
        self._orbit_running = False
        self._phase = 0.0
        self._nodes = []
        self._recent_results = []
        self._center_container = None
        self._glow_container = None

        # Animated Spatial/Frequency workflow state.
        # Both workflow cards are animated from the existing Home animation loop,
        # so no extra background task is required.
        self._workflow_tracks = []
        self._workflow_elapsed = 0.0

        # Seconds spent travelling from one processing stage to the next.
        # A full cycle is intentionally slow and fluid instead of "blinking".
        self._workflow_segment_seconds = 0.95
        self._workflow_end_hold_seconds = 0.75

        # Live header values. These keep the approved Home UI unchanged while
        # allowing Settings to update what the user actually sees.
        self.greeting_text = ft.Text(
            self._greeting_value(),
            size=27,
            weight=ft.FontWeight.BOLD,
            color=AppColors.TEXT,
        )
        self.workspace_name_text = ft.Text(
            self._workspace_name(),
            size=11,
            color=AppColors.TEXT,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.workspace_menu = self._build_workspace_menu()

        self.session_name_text = ft.Text("No active image", size=9, color=AppColors.MUTED)
        self.control = self._build()

    def _display_name(self):
        return getattr(self.profile, "name", None) or "Shreya"

    def _workspace_name(self):
        workspace = getattr(self.profile, "workspace", None) or "Default"
        return workspace if workspace in WORKSPACE_OPTIONS else "Default"

    def _greeting_value(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            period = "Good morning"
        elif 12 <= hour < 17:
            period = "Good afternoon"
        else:
            period = "Good evening"
        return f"{period}, {self._display_name()}"

    def _build_workspace_menu(self):
        current = self._workspace_name()
        return ft.PopupMenuButton(
            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
            icon_size=17,
            icon_color=AppColors.MUTED,
            width=24,
            height=24,
            tooltip="Switch workspace",
            items=[
                ft.PopupMenuItem(
                    content=workspace,
                    checked=workspace == current,
                    data=workspace,
                    on_click=lambda e, selected=workspace: self._select_workspace(selected),
                )
                for workspace in WORKSPACE_OPTIONS
            ],
        )

    def _select_workspace(self, workspace):
        if workspace not in WORKSPACE_OPTIONS:
            return
        if self.on_workspace_change:
            self.on_workspace_change(workspace)

    def set_profile(self, profile, refresh=True):
        """Refresh the visible Home identity without rebuilding the page."""
        self.profile = profile
        self.greeting_text.value = self._greeting_value()
        self.workspace_name_text.value = self._workspace_name()

        for item in self.workspace_menu.items:
            item.checked = item.data == self._workspace_name()

        if refresh:
            try:
                self.greeting_text.update()
                self.workspace_name_text.update()
                self.workspace_menu.update()
            except Exception:
                pass

    def _build(self):
        return ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                self._header(),
                self._hero(),
                ft.ResponsiveRow(spacing=12, run_spacing=12, controls=[
                    ft.Container(col={"xs": 12, "lg": 6}, content=self._workflow(True)),
                    ft.Container(col={"xs": 12, "lg": 6}, content=self._workflow(False)),
                ]),
                self._recent_projects(),
                ft.Container(height=4),
            ],
        )

    def _header(self):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(spacing=4, controls=[
                    self.greeting_text,
                    ft.Row(spacing=9, controls=[
                        ft.Container(width=7, height=7, bgcolor="#4DDB8A", border_radius=99),
                        ft.Text("Workspace ready", size=10, color=AppColors.TEXT_SECONDARY),
                    ]),
                ]),
                ft.Container(
                    width=184, height=56,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                    bgcolor="#B308111D", border=ft.Border.all(1, AppColors.BORDER_SOFT), border_radius=15,
                    content=ft.Row(controls=[
                        ft.Icon(ft.Icons.STORAGE_OUTLINED, size=21, color=AppColors.TEXT_SECONDARY),
                        ft.Column(expand=True, spacing=0, controls=[
                            ft.Text("Workspace", size=8, color=AppColors.MUTED),
                            self.workspace_name_text,
                        ]),
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=18, color="#43DE90"),
                        self.workspace_menu,
                    ]),
                ),
            ],
        )

    def _hero(self):
        upload = ft.Container(
            width=410,
            height=218,
            padding=ft.Padding.symmetric(horizontal=20, vertical=16),
            alignment=ft.Alignment.CENTER,
            bgcolor="#B80A1322",
            gradient=ft.LinearGradient(
                colors=["#C30C1627", "#A60B1424", "#9B15142D"],
            ),
            border=ft.Border.all(1, "#43536F"),
            border_radius=18,
            shadow=ft.BoxShadow(
                blur_radius=24,
                spread_radius=-8,
                offset=ft.Offset(0, 10),
                color="#42000000",
            ),
            ink=True,
            on_click=self.on_open_image,
            on_hover=self._hover_upload,
            animate=ft.Animation(AppAnimations.FAST, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(AppAnimations.FAST, ft.AnimationCurve.EASE_OUT),
            scale=1.0,
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=9,
                controls=[
                    ft.Container(
                        width=54,
                        height=54,
                        alignment=ft.Alignment.CENTER,
                        border_radius=16,
                        gradient=ft.LinearGradient(
                            colors=["#293A7B", "#24275F"],
                        ),
                        border=ft.Border.all(1, "#6074DA"),
                        shadow=ft.BoxShadow(
                            blur_radius=22,
                            spread_radius=-4,
                            color="#725B72FF",
                        ),
                        content=ft.Icon(
                            ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
                            size=27,
                            color="#EEF2FF",
                        ),
                    ),
                    ft.Text(
                        "Drop an image to start",
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color=AppColors.TEXT,
                    ),
                    ft.Row(
                        tight=True,
                        spacing=7,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text("or", size=9, color=AppColors.MUTED),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                                border_radius=9,
                                bgcolor="#1B2B56",
                                border=ft.Border.all(1, "#5369D9"),
                                content=ft.Row(
                                    tight=True,
                                    spacing=6,
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.FOLDER_OPEN_OUTLINED,
                                            size=14,
                                            color="#AEB9FF",
                                        ),
                                        ft.Text(
                                            "Browse files",
                                            size=10,
                                            weight=ft.FontWeight.W_600,
                                            color="#DCE3FF",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                    ft.Row(
                        tight=True,
                        spacing=5,
                        controls=[
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                                border_radius=6,
                                bgcolor="#101B2C",
                                border=ft.Border.all(1, "#2C3B52"),
                                content=ft.Text("PNG", size=7, color=AppColors.TEXT_SECONDARY),
                            ),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                                border_radius=6,
                                bgcolor="#101B2C",
                                border=ft.Border.all(1, "#2C3B52"),
                                content=ft.Text("JPG", size=7, color=AppColors.TEXT_SECONDARY),
                            ),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                                border_radius=6,
                                bgcolor="#101B2C",
                                border=ft.Border.all(1, "#2C3B52"),
                                content=ft.Text("TIFF", size=7, color=AppColors.TEXT_SECONDARY),
                            ),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                                border_radius=6,
                                bgcolor="#101B2C",
                                border=ft.Border.all(1, "#2C3B52"),
                                content=ft.Text("BMP", size=7, color=AppColors.TEXT_SECONDARY),
                            ),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                                border_radius=6,
                                bgcolor="#101B2C",
                                border=ft.Border.all(1, "#2C3B52"),
                                content=ft.Text("WebP", size=7, color=AppColors.TEXT_SECONDARY),
                            ),
                        ],
                    ),
                    ft.Row(
                        tight=True,
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.DRAG_INDICATOR, size=13, color=AppColors.MUTED),
                            ft.Text(
                                "Drag & drop or click anywhere in this card",
                                size=8,
                                color=AppColors.MUTED,
                            ),
                        ],
                    ),
                ],
            ),
        )
        return ft.Container(
            height=314,
            padding=ft.Padding.only(left=26, right=20, top=16, bottom=14),
            border=ft.Border.all(1, "#293B59"), border_radius=17,
            image=ft.DecorationImage(src=GALAXY_IMAGE, fit=ft.BoxFit.COVER, opacity=0.46),
            bgcolor="#B407111F",
            shadow=ft.BoxShadow(blur_radius=28, spread_radius=-10, offset=ft.Offset(0, 12), color="#400A0F22"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(spacing=14, controls=[
                        ft.Text("Your Image Processing Universe", size=23, weight=ft.FontWeight.BOLD, color=AppColors.TEXT),
                        upload,
                    ]),
                    ft.Container(width=560, height=278, content=self._orbit()),
                ],
            ),
        )

    def _orbit(self):
        cx, cy = 280, 139

        # Dashed elliptical orbit rails, drawn on a canvas so they read as
        # "orbit paths" rather than plain circles.
        ring_paths = fc.Canvas(
            width=560, height=278,
            shapes=[
                fc.Oval(
                    x=cx - radius, y=cy - radius * ORBIT_ASPECT,
                    width=radius * 2, height=radius * 2 * ORBIT_ASPECT,
                    paint=ft.Paint(
                        style=ft.PaintingStyle.STROKE,
                        stroke_width=1,
                        color="#4A5C82",
                        stroke_dash_pattern=[5, 5],
                    ),
                )
                for radius in (78, 112, 148)
            ],
        )

        self.orbit_stack = ft.Stack(width=560, height=278, controls=[ring_paths])

        # No background glow behind the center logo.
        self._glow_container = None

        # Clean circular AETHERIS centerpiece.
        # No sparkle ring — just the logo fitted neatly inside a circle.
        self._center_container = ft.Container(
            left=cx - CENTER_HUB_SIZE / 2,
            top=cy - CENTER_HUB_SIZE / 2,
            width=CENTER_HUB_SIZE,
            height=CENTER_HUB_SIZE,
            padding=8,
            border_radius=999,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            alignment=ft.Alignment.CENTER,
            bgcolor="#0B1020",
            border=ft.Border.all(1.0, "#6F7FA8"),
            shadow=None,
            content=ft.Image(
                src=AETHERIS_ORBIT_LOGO,
                width=CENTER_LOGO_SIZE,
                height=CENTER_LOGO_SIZE,
                fit=ft.BoxFit.CONTAIN,
                gapless_playback=True,
            ),
        )
        self.orbit_stack.controls.append(self._center_container)

        specs = [
            ("Blur", ft.Icons.BLUR_ON, "#6280FF", -math.pi / 2),
            ("Edges", ft.Icons.SELECT_ALL, "#A65CF6", -math.pi / 6),
            ("DFT", ft.Icons.GRAPHIC_EQ, "#2CC8E8", math.pi / 6),
            ("Restore", ft.Icons.AUTO_FIX_HIGH_OUTLINED, "#8B58E9", math.pi / 2),
            ("Compress", ft.Icons.DOWNLOAD_FOR_OFFLINE_OUTLINED, "#24B8D1", math.pi + math.pi / 6),
            ("Color", ft.Icons.WATER_DROP_OUTLINED, "#C05AA5", math.pi - math.pi / 6),
        ]
        for label, icon, accent, angle in specs:
            shell = ft.Container(
                width=49, height=49, alignment=ft.Alignment.CENTER, border_radius=99,
                bgcolor=f"B328{accent[1:]}", border=ft.Border.all(1, accent),
                shadow=ft.BoxShadow(blur_radius=16, color=f"55{accent[1:]}"),
                content=ft.Icon(icon, size=21, color="#EAF1FF"),
            )
            holder = ft.Container(
                width=86, height=72,
                # Smoothly interpolates between the positions set every animation
                # tick, so the orbit reads as continuous motion, not a stepped jump.
                animate_position=ft.Animation(ORBIT_TRANSITION_MS, ft.AnimationCurve.LINEAR),
                content=ft.Column(spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                  controls=[ft.Text(label, size=10, color=AppColors.TEXT), shell]),
            )
            self.orbit_stack.controls.append(holder)
            self._nodes.append((holder, angle, 148))
        self._place_nodes()
        return self.orbit_stack

    def _place_nodes(self):
        cx, cy = 280, 139
        for holder, base, radius in self._nodes:
            angle = base + self._phase
            holder.left = cx + math.cos(angle) * radius - 43
            holder.top = cy + math.sin(angle) * radius * ORBIT_ASPECT - 36

    @staticmethod
    def _mix_hex(color_a, color_b, amount):
        """Blend two #RRGGBB colors. Used for fluid workflow highlights."""
        amount = max(0.0, min(1.0, float(amount)))
        a = color_a.lstrip("#")
        b = color_b.lstrip("#")

        ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
        br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)

        r = round(ar + (br - ar) * amount)
        g = round(ag + (bg - ag) * amount)
        bl = round(ab + (bb - ab) * amount)

        return f"#{r:02X}{g:02X}{bl:02X}"

    @staticmethod
    def _smoothstep(value):
        value = max(0.0, min(1.0, float(value)))
        return value * value * (3.0 - 2.0 * value)

    def _workflow(self, spatial):
        accent = "#9B55F1" if spatial else "#29B8E8"
        accent_bright = "#C98CFF" if spatial else "#73E5FF"
        node_base = "#132036"
        border_base = "#39506E"

        title = "Spatial Domain" if spatial else "Frequency Domain"
        subtitle = (
            "Process images directly in the pixel domain."
            if spatial
            else "Analyze and filter using frequency transforms."
        )

        labels = (
            ["Input", "Filter", "Enhance", "Output"]
            if spatial
            else ["Input", "DFT", "Filter", "IDFT", "Output"]
        )

        icons = (
            [
                ft.Icons.IMAGE_OUTLINED,
                ft.Icons.BLUR_ON,
                ft.Icons.TUNE,
                ft.Icons.IMAGE,
            ]
            if spatial
            else [
                ft.Icons.IMAGE_OUTLINED,
                ft.Icons.GRAPHIC_EQ,
                ft.Icons.RADIO_BUTTON_CHECKED,
                ft.Icons.GRAPHIC_EQ,
                ft.Icons.IMAGE,
            ]
        )

        stage_shells = []
        stage_icons = []
        stage_labels = []
        connectors = []
        row_controls = []

        # -----------------------------------------------------
        # PROCESSING NODES
        # -----------------------------------------------------
        for i, (label, icon) in enumerate(zip(labels, icons)):
            icon_control = ft.Icon(
                icon,
                size=21,
                color=accent,
            )

            shell = ft.Container(
                width=56,
                height=44,
                alignment=ft.Alignment.CENTER,
                border_radius=11,
                bgcolor=node_base,
                border=ft.Border.all(1, border_base),
                shadow=ft.BoxShadow(
                    blur_radius=5,
                    spread_radius=-2,
                    color=f"16{accent[1:]}",
                ),
                scale=1.0,
                animate=ft.Animation(
                    70,
                    ft.AnimationCurve.LINEAR,
                ),
                animate_scale=ft.Animation(
                    70,
                    ft.AnimationCurve.LINEAR,
                ),
                content=icon_control,
            )

            label_control = ft.Text(
                label,
                size=9,
                color=AppColors.TEXT_SECONDARY,
                weight=ft.FontWeight.W_500,
            )

            stage = ft.Column(
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    shell,
                    label_control,
                ],
            )

            row_controls.append(stage)
            stage_shells.append(shell)
            stage_icons.append(icon_control)
            stage_labels.append(label_control)

            # -------------------------------------------------
            # CONNECTOR WITH A REAL TRAVELLING "SIGNAL" SPARK
            # -------------------------------------------------
            if i < len(labels) - 1:
                rail = ft.Container(
                    left=1,
                    top=10,
                    width=31,
                    height=2,
                    border_radius=99,
                    bgcolor="#263850",
                    shadow=ft.BoxShadow(
                        blur_radius=0,
                        color="#00000000",
                    ),
                    animate=ft.Animation(
                        70,
                        ft.AnimationCurve.LINEAR,
                    ),
                )

                spark = ft.Container(
                    left=1,
                    top=7,
                    width=8,
                    height=8,
                    border_radius=99,
                    bgcolor=accent_bright,
                    opacity=0.0,
                    shadow=ft.BoxShadow(
                        blur_radius=12,
                        spread_radius=1,
                        color=f"AA{accent[1:]}",
                    ),
                    animate_position=ft.Animation(
                        65,
                        ft.AnimationCurve.LINEAR,
                    ),
                    animate_opacity=ft.Animation(
                        65,
                        ft.AnimationCurve.LINEAR,
                    ),
                )

                arrow_head = ft.Container(
                    right=0,
                    top=4,
                    width=14,
                    height=14,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        ft.Icons.CHEVRON_RIGHT,
                        size=14,
                        color=AppColors.MUTED_2,
                    ),
                )

                connector = ft.Stack(
                    width=38,
                    height=22,
                    controls=[
                        rail,
                        spark,
                        arrow_head,
                    ],
                )

                row_controls.append(connector)
                connectors.append(
                    {
                        "stack": connector,
                        "rail": rail,
                        "spark": spark,
                        "head": arrow_head.content,
                    }
                )

        flow_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=row_controls,
        )

        # Small live-flow badge: subtle and useful, not flashy.
        live_dot = ft.Container(
            width=6,
            height=6,
            border_radius=99,
            bgcolor=accent,
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=f"88{accent[1:]}",
            ),
        )


        card = ft.Container(
            height=190,
            padding=ft.Padding.symmetric(
                horizontal=20,
                vertical=14,
            ),
            border_radius=16,
            border=ft.Border.all(1, accent),
            gradient=ft.LinearGradient(
                colors=(
                    ["#101329", "#071728"]
                    if spatial
                    else ["#071728", "#0A1C2D"]
                )
            ),
            shadow=ft.BoxShadow(
                blur_radius=15,
                spread_radius=-7,
                offset=ft.Offset(0, 7),
                color=f"30{accent[1:]}",
            ),
            scale=1.0,
            animate=ft.Animation(
                180,
                ft.AnimationCurve.EASE_OUT,
            ),
            animate_scale=ft.Animation(
                180,
                ft.AnimationCurve.EASE_OUT,
            ),
            on_hover=self._hover_workflow,
            data={
                "accent": accent,
                "hovered": False,
            },
            content=ft.Column(
                spacing=9,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Row(
                                        tight=True,
                                        spacing=8,
                                        controls=[
                                            ft.Text(
                                                title,
                                                size=17,
                                                weight=ft.FontWeight.BOLD,
                                                color=AppColors.TEXT,
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        subtitle,
                                        size=9,
                                        color=AppColors.TEXT_SECONDARY,
                                    ),
                                ],
                            ),
                            ft.Button(
                                content="Start",
                                icon=ft.Icons.PLAY_ARROW_OUTLINED,
                                on_click=lambda e: self._navigate(1),
                                bgcolor="#27387C" if spatial else "#15528A",
                                color=AppColors.TEXT,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(
                                        radius=9,
                                    )
                                ),
                            ),
                        ],
                    ),
                    flow_row,
                    ft.Text(
                        (
                            "Examples: Blur, Sharpen, Edge Detect, Smooth, Morphology"
                            if spatial
                            else "Examples: Low-pass, High-pass, Band-stop, Notch, Homomorphic"
                        ),
                        size=8,
                        color=AppColors.MUTED,
                    ),
                ],
            ),
        )

        self._workflow_tracks.append(
            {
                "spatial": spatial,
                "accent": accent,
                "accent_bright": accent_bright,
                "node_base": node_base,
                "border_base": border_base,
                "shells": stage_shells,
                "icons": stage_icons,
                "labels": stage_labels,
                "connectors": connectors,
                "row": flow_row,
                "card": card,
                "live_dot": live_dot,
            }
        )

        return card

    @staticmethod
    def _hover_workflow(e):
        hovered = str(e.data).strip().lower() == "true"
        accent = (e.control.data or {}).get("accent", "#6280FF")

        if e.control.data is None:
            e.control.data = {}

        e.control.data["hovered"] = hovered
        e.control.scale = 1.012 if hovered else 1.0

        e.control.shadow = ft.BoxShadow(
            blur_radius=27 if hovered else 15,
            spread_radius=-3 if hovered else -7,
            offset=ft.Offset(0, 10 if hovered else 7),
            color=f"58{accent[1:]}" if hovered else f"30{accent[1:]}",
        )

        e.control.update()

    def _advance_workflow_animation(self, dt):
        """
        Smooth, continuous DSP-flow animation.

        Instead of switching a discrete "active step", a virtual signal moves
        continuously from node to node. The two surrounding stages cross-fade,
        the current connector glows, and a spark physically travels along it.
        """
        if not self._workflow_tracks:
            return

        self._workflow_elapsed += dt

        for track in self._workflow_tracks:
            shells = track["shells"]
            count = len(shells)

            if count < 2:
                continue

            travel_seconds = (count - 1) * self._workflow_segment_seconds
            cycle_seconds = travel_seconds + self._workflow_end_hold_seconds

            # Frequency gets a gentle offset so both cards don't mirror
            # one another exactly.
            offset = 0.0 if track["spatial"] else 0.52
            t = (self._workflow_elapsed + offset) % cycle_seconds

            if t <= travel_seconds:
                position = t / self._workflow_segment_seconds
                position = min(position, count - 1)

                segment = min(int(position), count - 2)
                local = position - segment
                eased = self._smoothstep(local)
                holding_output = False
            else:
                # Soft output hold/fade before the signal restarts.
                position = count - 1
                segment = count - 2
                local = 1.0
                eased = 1.0
                holding_output = True

            # -------------------------------------------------
            # NODE CROSS-FADE
            # -------------------------------------------------
            for i, shell in enumerate(shells):
                distance = abs(i - position)

                # Soft gaussian-like falloff without expensive math.
                intensity = max(0.0, 1.0 - distance)
                intensity = self._smoothstep(intensity)

                if holding_output and i == count - 1:
                    hold_progress = (t - travel_seconds) / self._workflow_end_hold_seconds
                    # Breathing output glow during the brief hold.
                    intensity = 0.72 + 0.20 * (
                        0.5 + 0.5 * math.sin(hold_progress * math.pi * 2)
                    )

                shell.scale = 1.0 + 0.085 * intensity
                shell.bgcolor = self._mix_hex(
                    track["node_base"],
                    track["accent"],
                    0.20 * intensity,
                )
                shell.border = ft.Border.all(
                    1.0 + 0.45 * intensity,
                    self._mix_hex(
                        track["border_base"],
                        track["accent_bright"],
                        0.92 * intensity,
                    ),
                )
                shell.shadow = ft.BoxShadow(
                    blur_radius=5 + 18 * intensity,
                    spread_radius=-2 + 2 * intensity,
                    color=f"{int(18 + 120 * intensity):02X}{track['accent'][1:]}",
                )

                track["icons"][i].color = self._mix_hex(
                    track["accent"],
                    "#FFFFFF",
                    0.82 * intensity,
                )

                track["labels"][i].color = self._mix_hex(
                    "#8A97AA",
                    "#F7FAFF",
                    0.90 * intensity,
                )

            # -------------------------------------------------
            # CONNECTOR RAIL + TRAVELLING SPARK
            # -------------------------------------------------
            for i, connector in enumerate(track["connectors"]):
                completed = i < segment
                current = (i == segment) and not holding_output

                if completed:
                    connector["rail"].bgcolor = self._mix_hex(
                        "#263850",
                        track["accent"],
                        0.58,
                    )
                    connector["rail"].shadow = ft.BoxShadow(
                        blur_radius=5,
                        color=f"55{track['accent'][1:]}",
                    )
                    connector["head"].color = track["accent"]
                    connector["spark"].opacity = 0.0

                elif current:
                    connector["rail"].bgcolor = self._mix_hex(
                        "#263850",
                        track["accent"],
                        0.38 + 0.48 * eased,
                    )
                    connector["rail"].shadow = ft.BoxShadow(
                        blur_radius=7 + 6 * math.sin(math.pi * eased),
                        color=f"88{track['accent'][1:]}",
                    )

                    # Spark moves from the beginning to the arrow head.
                    connector["spark"].left = 1 + 24 * eased
                    connector["spark"].opacity = (
                        0.45 + 0.55 * math.sin(math.pi * eased)
                    )
                    connector["head"].color = self._mix_hex(
                        "#617088",
                        track["accent_bright"],
                        eased,
                    )

                else:
                    connector["rail"].bgcolor = "#263850"
                    connector["rail"].shadow = ft.BoxShadow(
                        blur_radius=0,
                        color="#00000000",
                    )
                    connector["head"].color = AppColors.MUTED_2
                    connector["spark"].opacity = 0.0

            # -------------------------------------------------
            # SUBTLE CARD "BREATHING" GLOW
            # -------------------------------------------------
            pulse = 0.5 + 0.5 * math.sin(
                self._workflow_elapsed * 1.35
                + (0.0 if track["spatial"] else math.pi)
            )

            hovered = bool((track["card"].data or {}).get("hovered", False))

            if not hovered:
                track["card"].shadow = ft.BoxShadow(
                    blur_radius=14 + 4 * pulse,
                    spread_radius=-7,
                    offset=ft.Offset(0, 7),
                    color=f"{int(32 + 18 * pulse):02X}{track['accent'][1:]}",
                )

            # Tiny status dot breathes independently.
            track["live_dot"].scale = 0.88 + 0.18 * pulse

            try:
                track["row"].update()
                track["live_dot"].update()

                if not hovered:
                    track["card"].update()
            except Exception:
                pass

    def _recent_projects(self):
        self.project_count_text = ft.Text(
            "Images opened or processed in this session",
            size=9,
            color=AppColors.MUTED,
        )
        self.projects_grid = ft.ResponsiveRow(spacing=14, run_spacing=14)
        self._rebuild_project_cards()
        return ft.Container(
            padding=14, bgcolor="#D907101D", border=ft.Border.all(1, "#263650"), border_radius=16,
            content=ft.Column(spacing=10, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Column(spacing=2, controls=[
                        ft.Text("Recent Projects", size=14, weight=ft.FontWeight.BOLD, color=AppColors.TEXT),
                        self.project_count_text,
                    ]),
                    ft.TextButton("View all", style=ft.ButtonStyle(color="#7292FF")),
                ]),
                self.projects_grid,
            ]),
        )

    def _rebuild_project_cards(self):
        # Permanent demo cards always stay first.
        demo_cards = [
            ft.Container(
                col={"xs": 12, "md": 4},
                content=self._project(**project),
            )
            for project in DEMO_PROJECTS
        ]

        # Real images opened/processed during the current session come after
        # the demos. `_recent_results` is already capped at three items.
        recent_cards = [
            ft.Container(
                col={"xs": 12, "md": 4},
                content=self._project(**project),
            )
            for project in self._recent_results
        ]

        self.projects_grid.controls = demo_cards + recent_cards

        count = len(self._recent_results)
        if count == 0:
            self.project_count_text.value = "3 demo projects  •  No session images yet"
        elif count == 1:
            self.project_count_text.value = "3 demo projects  •  1 recent image from this session"
        else:
            self.project_count_text.value = (
                f"3 demo projects  •  {count} recent images from this session"
            )

    def add_recent_project(
        self,
        image_bytes,
        title,
        source_name,
        resolution,
        fmt="PNG",
        refresh=False,
    ):
        """Add an opened or processed image to the three-card session history."""
        self._recent_results.insert(
            0,
            {
                "title": title or "Processed Result",
                "edited": f"Just now  •  {source_name or 'Untitled image'}",
                "resolution": resolution,
                "fmt": fmt,
                "image": image_bytes,
            },
        )
        del self._recent_results[3:]
        self._rebuild_project_cards()

        if refresh:
            try:
                self.project_count_text.update()
                self.projects_grid.update()
            except Exception:
                pass

    def add_processed_result(
        self,
        image_bytes,
        title,
        source_name,
        resolution,
        fmt="PNG",
        refresh=False,
    ):
        """Backward-compatible alias for older main_window.py versions."""
        self.add_recent_project(
            image_bytes=image_bytes,
            title=title,
            source_name=source_name,
            resolution=resolution,
            fmt=fmt,
            refresh=refresh,
        )

    def _project(self, title, edited, resolution, fmt, image):
        # `image` may be a bundled asset path (str) or raw processed bytes —
        # ft.Image.src accepts either directly in this Flet version.
        return ft.Container(
            height=282, bgcolor="#0B1526", border=ft.Border.all(1, "#30405A"), border_radius=13,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=ft.Animation(AppAnimations.FAST, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(AppAnimations.FAST, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(blur_radius=0, spread_radius=0, offset=ft.Offset(0, 8), color="#00000000"),
            on_hover=self._hover_project,
            ink=True,
            on_click=lambda e: self._navigate(1),
            content=ft.Column(spacing=0, controls=[
                ft.Image(src=image, height=165, width=600, fit=ft.BoxFit.COVER,
                         gapless_playback=True,
                         error_content=ft.Container(
                             alignment=ft.Alignment.CENTER,
                             bgcolor="#0F1C31",
                             content=ft.Icon(ft.Icons.BROKEN_IMAGE_OUTLINED, color=AppColors.MUTED),
                         )),
                ft.Container(expand=True, padding=11, content=ft.Column(spacing=7, controls=[
                    ft.Row(controls=[
                        ft.Column(expand=True, spacing=4, controls=[
                            ft.Text(title, size=11, weight=ft.FontWeight.W_600, color=AppColors.TEXT),
                            ft.Text(edited, size=9, color=AppColors.MUTED),
                        ]),
                        ft.Icon(ft.Icons.MORE_VERT, size=18, color=AppColors.TEXT_SECONDARY),
                    ]),
                    ft.Row(spacing=7, controls=[self._chip(resolution), self._chip(fmt)]),
                ])),
            ]),
        )

    @staticmethod
    def _chip(text):
        return ft.Container(padding=ft.Padding.symmetric(horizontal=9, vertical=5), border_radius=6,
                            bgcolor="#111D31", border=ft.Border.all(1, "#293950"),
                            content=ft.Text(text, size=8, color=AppColors.TEXT_SECONDARY))

    @staticmethod
    def _hover_project(e):
        hovered = str(e.data).lower() == "true"
        e.control.scale = 1.016 if hovered else 1.0
        e.control.border = ft.Border.all(1, "#4B6EFF" if hovered else "#30405A")
        e.control.shadow = ft.BoxShadow(
            blur_radius=24 if hovered else 0,
            spread_radius=-4 if hovered else 0,
            offset=ft.Offset(0, 10),
            color="#4D2A44FF" if hovered else "#00000000",
        )
        e.control.update()

    @staticmethod
    def _hover_upload(e):
        hovered = str(e.data).lower() == "true"
        e.control.border = ft.Border.all(
            1,
            "#8494FF" if hovered else "#43536F",
        )
        e.control.scale = 1.012 if hovered else 1.0
        e.control.shadow = ft.BoxShadow(
            blur_radius=32 if hovered else 24,
            spread_radius=-5 if hovered else -8,
            offset=ft.Offset(0, 12 if hovered else 10),
            color="#765D72FF" if hovered else "#42000000",
        )
        e.control.update()

    async def start_orbit_animation(self):
        if self._orbit_running:
            return
        self._orbit_running = True
        last = time.monotonic()
        glow_phase = 0.0
        try:
            while self._orbit_running:
                await asyncio.sleep(ORBIT_FRAME_INTERVAL)
                now = time.monotonic()
                dt = now - last
                last = now

                # Advance by real elapsed time rather than a fixed step, so the
                # motion stays smooth even if a frame is delayed.
                self._phase += ORBIT_ANGULAR_SPEED * dt
                self._place_nodes()

                # Animate Spatial/Frequency workflow signal flow using the
                # same timing loop as the orbital animation.
                self._advance_workflow_animation(dt)

                # Gentle breathing glow behind the center thumbnail.
                glow_phase += ORBIT_GLOW_SPEED * dt
                pulse = (math.sin(glow_phase) + 1) / 2  # 0..1
                if self._glow_container is not None:
                    intensity = 20 + pulse * 12
                    self._glow_container.shadow = ft.BoxShadow(
                        blur_radius=intensity, spread_radius=1, color="#426676FF",
                    )

                try:
                    self.orbit_stack.update()
                except Exception:
                    pass
        finally:
            self._orbit_running = False

    def stop_orbit_animation(self):
        self._orbit_running = False

    def set_session_name(self, image_name, refresh=True):
        self.session_name_text.value = image_name or "No active image"
        if refresh:
            try:
                self.session_name_text.update()
            except Exception:
                pass

    def _navigate(self, index):
        if self.on_navigate:
            self.on_navigate(index)
"""Discover · Lesson 1 — How a kernel sees an image.

An animated, interactive walk through 2D convolution on a fixed 16 x 16
space scene. Every number on screen comes from ConvolutionTrace, which
is checked against the project's own convolve2d_gray, so the animation
is a slowed-down view of the real computation, not an imitation.

Stage layout (absolute coordinates, one Stack per layer so each update
only walks the layer that changed):

    caption ........................................................
    [ghost ring | input 16x16]   [kernel · products · Σ]   [output 16x16]

Chapters
    1  An image is numbers      smooth scene -> pixels -> numbered tiles
    2  Meet the kernel          weights appear, then flip 180°
    3  Slide, multiply, sum     two pixels in full detail (one on the border)
    4  Sweep the whole image    every remaining pixel, accelerating
    5  The big reveal           same kernel on the 96 x 96 scene
"""

import asyncio
import math

import flet as ft
import numpy as np

from algorithms.learning.convolution_trace import (
    PRESETS,
    ConvolutionTrace,
    convolve_reveal,
    identify_kernel,
)
from algorithms.learning.space_scene import (
    LESSON_SIZE,
    REVEAL_SIZE,
    lesson_grid,
    render_space_scene,
)
from ui.learning import palette
from ui.learning.kernel_editor import KernelEditor
from ui.learning.scene_engine import Cancelled, Timeline
from ui.theme import AppAnimations, AppColors, AppLayout


# ============================================================
# GEOMETRY
# ============================================================

N = LESSON_SIZE          # 16 x 16 lesson image
MAX_PAD = 3              # room for a 7 x 7 kernel's border

# Base geometry, at zoom = 1.0. Everything on the stage is measured from
# these, so the whole lesson can be redrawn at a smaller size to fit a
# window: the stage is re-laid out, not shrunk by a transform, so the
# numbers stay crisp at any zoom.
BASE = dict(
    p=22,            # tile pitch
    t=19,            # tile size (p - t = gap)
    gx=12, gy=64,    # ghost-ring origin
    mx=520, mw=260,  # middle panel x and width
    kp=20, kt=18,    # kernel mini cells
    kernel_top=96,
    pp=36, pt=33,    # product cells
    product_top=258,
    sum_h=48,
    ox=812,          # output image origin (y = y0)
)

BASE_W = BASE["ox"] + (N * BASE["p"] - (BASE["p"] - BASE["t"])) + 20
BASE_H = max(
    BASE["gy"] + (N + 2 * MAX_PAD) * BASE["p"],
    BASE["product_top"] + 7 * BASE["pp"] + 12 + BASE["sum_h"],
) + 12

MIN_ZOOM = 0.55
MAX_ZOOM = 1.15
SIDE_ALLOWANCE = 210       # page padding + stage card padding + scrollbar
VERTICAL_ALLOWANCE = 300   # top bar, chapter header, status bar, margins

CHAPTERS = [
    "An image is numbers",
    "Meet the kernel",
    "Slide, multiply, sum",
    "Sweep the whole image",
    "Numbers back to light",
    "The big reveal",
]


def _mono(size, color, weight=ft.FontWeight.BOLD):
    return dict(size=size, color=color, weight=weight, font_family="Consolas")


class LearnConvolutionView:
    def __init__(self, page):
        self.page = page

        self.image = np.asarray(lesson_grid(), dtype=np.uint8)
        self.scene = np.asarray(render_space_scene(REVEAL_SIZE), dtype=np.uint8)

        self.timeline = Timeline(page, on_state_change=self._on_running_changed)

        self.chapter = 0
        self.lit = set()              # output pixels already computed
        self.numbers_shown = False
        self.kernel_shown = False
        self.flipped_shown = False
        self.ghosts_shown = False
        self.assembled = False
        self.last_pixel = None

        self.editor = KernelEditor(on_change=self._on_kernel_change)
        self.trace = ConvolutionTrace(self.image, self.editor.get_kernel())

        self.zoom = 0.0
        self.manual_zoom = None
        self._set_geometry(1.0)

        self._build_stage()
        self.stage_holder = ft.Container(content=self.stage)
        self.control = self._build_page()
        self._apply_chapter_state(0, first_build=True)

    # =========================================================
    # GEOMETRY
    # =========================================================

    def _set_geometry(self, zoom):
        """Recompute every stage measurement for a zoom level."""
        self.zoom = zoom
        scale = lambda value: max(1, int(round(value * zoom)))

        for key, value in BASE.items():
            setattr(self, key, scale(value))

        self.x0 = self.gx + MAX_PAD * self.p
        self.y0 = self.gy + MAX_PAD * self.p
        self.grid = N * self.p - (self.p - self.t)
        self.sum_top = self.product_top + 7 * self.pp + scale(12)
        self.stage_w = self.ox + self.grid + scale(20)
        self.stage_h = max(
            self.gy + (N + 2 * MAX_PAD) * self.p,
            self.sum_top + self.sum_h,
        ) + scale(12)

        # Type scales with the tiles, with a floor so it stays legible.
        self.f_tile = max(6, round(8 * zoom))
        self.f_ghost = max(5, round(7 * zoom))
        self.f_cell = max(6, round(8 * zoom))
        self.f_cell_small = max(5, round(7 * zoom))
        self.f_kernel = max(5, round(6.5 * zoom))
        self.f_label = max(7, round(10 * zoom))
        self.f_caption = max(11, round(15 * zoom))
        self.f_sum = max(12, round(18 * zoom))
        self.reveal_image = max(170, round(300 * zoom))

    def fit_to_window(self, width=None, height=None):
        """Redraw the stage at the largest zoom that fits the window."""
        width = width or getattr(self.page, "width", None) or 0
        height = height or getattr(self.page, "height", None) or 0

        zoom = MAX_ZOOM
        if width:
            zoom = min(zoom, (width - SIDE_ALLOWANCE) / BASE_W)
        if height:
            zoom = min(zoom, (height - VERTICAL_ALLOWANCE) / BASE_H)
        zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))

        # Snap, so dragging a window edge does not rebuild on every pixel.
        zoom = round(zoom * 20) / 20
        if self.manual_zoom is not None:
            zoom = self.manual_zoom

        if abs(zoom - self.zoom) < 0.001:
            return
        self._rebuild_stage(zoom)

    def set_zoom(self, zoom):
        """Manual zoom from the slider; overrides the automatic fit."""
        self.manual_zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        self.zoom_label.value = f"{self.manual_zoom:.2f}".rstrip("0").rstrip(".") + "×"
        self._safe_update(self.zoom_label)
        if abs(self.manual_zoom - self.zoom) >= 0.001:
            self._rebuild_stage(self.manual_zoom)

    def _rebuild_stage(self, zoom):
        """Rebuild the stage at a new zoom, keeping the lesson's state."""
        was_running = self.timeline.running
        self.timeline.cancel()

        chapter = self.chapter
        lit = set(self.lit)
        last_pixel = self.last_pixel

        self._set_geometry(zoom)
        self._build_stage()
        self.stage_holder.content = self.stage

        self._apply_chapter_state(chapter, first_build=True)
        self.lit = lit
        for r, c in lit:
            self._light_output(r, c)
        self.last_pixel = last_pixel
        self._refresh_readout()
        self._safe_update(self.stage_holder)
        for control in (self.readout_pixel, self.readout_sum, self.readout_out,
                        self.readout_done):
            self._safe_update(control)

        # A resize should not end the lesson: pick the chapter back up.
        if was_running:
            self.timeline.start(lambda gen: self._play_from(gen, chapter))

    # =========================================================
    # PAGE
    # =========================================================

    def _build_page(self):
        self.chapter_pills = [self._chapter_pill(i) for i in range(len(CHAPTERS))]

        header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=24, vertical=18),
            border_radius=AppLayout.CARD_RADIUS,
            border=ft.Border.all(1, AppColors.BORDER),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=["#161226", "#0E1526", "#0B1222"],
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
                run_spacing=12,
                controls=[
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=9, vertical=3),
                                border_radius=7,
                                bgcolor=palette.argb("22", palette.KERNEL),
                                content=ft.Text(
                                    "DISCOVER  •  LESSON 1",
                                    size=9,
                                    weight=ft.FontWeight.BOLD,
                                    color=palette.KERNEL,
                                ),
                            ),
                            ft.Text(
                                "How a kernel sees an image",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),
                            ft.Text(
                                "2D convolution, one pixel at a time. "
                                "Click any input pixel to inspect it.",
                                size=11,
                                color=AppColors.TEXT_SECONDARY,
                            ),
                        ],
                    ),
                    ft.Row(spacing=8, wrap=True, controls=self.chapter_pills),
                ],
            ),
        )

        stage_card = ft.Container(
            padding=ft.Padding.symmetric(horizontal=12, vertical=12),
            border_radius=AppLayout.CARD_RADIUS,
            border=ft.Border.all(1, AppColors.BORDER),
            gradient=ft.RadialGradient(
                center=ft.Alignment(0, -0.2),
                radius=1.2,
                colors=["#101A33", "#070C18"],
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                controls=[self.stage_holder],
            ),
        )

        controls_card = ft.ResponsiveRow(
            spacing=14,
            run_spacing=14,
            controls=[
                ft.Container(col={"xs": 12, "lg": 4}, content=self._playback_panel()),
                ft.Container(col={"xs": 12, "lg": 5}, content=self._panel(
                    "KERNEL",
                    "Edit any weight, pick a size or a preset.",
                    ft.Icons.GRID_ON,
                    palette.KERNEL,
                    self.editor.control,
                )),
                ft.Container(col={"xs": 12, "lg": 3}, content=self._readout_panel()),
            ],
        )

        return ft.Column(spacing=16, controls=[header, stage_card, controls_card])

    def _chapter_pill(self, index):
        number = ft.Container(
            width=22,
            height=22,
            alignment=ft.Alignment.CENTER,
            border_radius=11,
            border=ft.Border.all(1, palette.KERNEL),
            content=ft.Text(str(index + 1), size=9, weight=ft.FontWeight.BOLD,
                            color=palette.KERNEL),
        )
        pill = ft.Container(
            padding=ft.Padding.only(left=6, right=12, top=6, bottom=6),
            border_radius=12,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            ink=True,
            tooltip=f"Jump to chapter {index + 1}",
            on_click=lambda e, i=index: self.jump_to(i),
            animate=ft.Animation(AppAnimations.NORMAL, ft.AnimationCurve.EASE_OUT),
            data=number,
            content=ft.Row(
                tight=True,
                spacing=8,
                controls=[number, ft.Text(CHAPTERS[index], size=10,
                                          color=AppColors.TEXT_SECONDARY)],
            ),
        )
        return pill

    def _panel(self, title, subtitle, icon, accent, body):
        return ft.Container(
            padding=18,
            border_radius=AppLayout.CARD_RADIUS,
            bgcolor=AppColors.SURFACE,
            border=ft.Border.all(1, AppColors.BORDER),
            content=ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=34,
                                height=34,
                                alignment=ft.Alignment.CENTER,
                                border_radius=10,
                                bgcolor=palette.argb("22", accent),
                                content=ft.Icon(icon, size=18, color=accent),
                            ),
                            ft.Column(
                                spacing=0,
                                controls=[
                                    ft.Text(title, size=11, weight=ft.FontWeight.BOLD,
                                            color=accent),
                                    ft.Text(subtitle, size=10, color=AppColors.MUTED),
                                ],
                            ),
                        ],
                    ),
                    body,
                ],
            ),
        )

    def _playback_panel(self):
        self.play_icon = ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=26, color="#0B1020")
        self.play_label = ft.Text("Play lesson", size=13, weight=ft.FontWeight.BOLD,
                                  color="#0B1020")

        self.play_button = ft.Container(
            height=50,
            padding=ft.Padding.symmetric(horizontal=18),
            border_radius=14,
            gradient=ft.LinearGradient(colors=[palette.KERNEL, "#F59E0B"]),
            shadow=ft.BoxShadow(blur_radius=22, spread_radius=-6,
                                color=palette.argb("99", palette.KERNEL)),
            ink=True,
            on_click=self.toggle_play,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[self.play_icon, self.play_label],
            ),
        )

        self.speed_label = ft.Text("1.0×", size=11, weight=ft.FontWeight.BOLD,
                                   color=palette.KERNEL)
        self.zoom_label = ft.Text("auto", size=11, weight=ft.FontWeight.BOLD,
                                  color=palette.INPUT)
        speed_slider = ft.Slider(
            min=0.5,
            max=3.0,
            divisions=10,
            value=1.0,
            active_color=palette.KERNEL,
            on_change=self._on_speed,
        )

        body = ft.Column(
            spacing=12,
            controls=[
                self.play_button,
                ft.Row(
                    spacing=8,
                    controls=[
                        self._small_button("Previous", ft.Icons.SKIP_PREVIOUS_ROUNDED,
                                           lambda e: self.jump_to(max(0, self.chapter - 1))),
                        self._small_button("Next", ft.Icons.SKIP_NEXT_ROUNDED,
                                           lambda e: self.jump_to(
                                               min(len(CHAPTERS) - 1, self.chapter + 1))),
                        self._small_button("Restart", ft.Icons.REPLAY_ROUNDED,
                                           lambda e: self.jump_to(0)),
                    ],
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        self._small_button("Replay pixel", ft.Icons.CENTER_FOCUS_STRONG,
                                           self._replay_pixel),
                        self._small_button("Fill output", ft.Icons.FORMAT_COLOR_FILL,
                                           self._fill_output),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ZOOM_IN, size=16, color=AppColors.MUTED),
                        ft.Text("Zoom", size=10, color=AppColors.MUTED),
                        ft.Container(expand=True, content=ft.Slider(
                            min=MIN_ZOOM,
                            max=MAX_ZOOM,
                            divisions=12,
                            value=1.0,
                            active_color=palette.INPUT,
                            on_change=lambda e: self.set_zoom(float(e.control.value)),
                        )),
                        self.zoom_label,
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SPEED, size=16, color=AppColors.MUTED),
                        ft.Text("Speed", size=10, color=AppColors.MUTED),
                        ft.Container(expand=True, content=speed_slider),
                        self.speed_label,
                    ],
                ),
            ],
        )

        return self._panel("PLAYBACK", "Play, pause, or jump to a chapter.",
                           ft.Icons.SMART_DISPLAY_OUTLINED, palette.KERNEL, body)

    def _small_button(self, label, icon, handler):
        return ft.Container(
            expand=True,
            height=38,
            border_radius=11,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            ink=True,
            on_click=handler,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(icon, size=15, color=AppColors.TEXT_SECONDARY),
                    ft.Text(label, size=10, color=AppColors.TEXT_SECONDARY),
                ],
            ),
        )

    def _readout_panel(self):
        self.readout_pixel = ft.Text("—", **_mono(13, palette.INPUT_SOFT))
        self.readout_sum = ft.Text("—", **_mono(13, palette.PRODUCT))
        self.readout_out = ft.Text("—", **_mono(13, AppColors.TEXT))
        self.readout_done = ft.Text(f"0 / {N * N}", **_mono(13, AppColors.GREEN_LIGHT))

        def row(label, value):
            return ft.Container(
                padding=ft.Padding.symmetric(horizontal=12, vertical=9),
                border_radius=10,
                bgcolor=AppColors.SURFACE_DARK,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[ft.Text(label, size=10, color=AppColors.MUTED), value],
                ),
            )

        body = ft.Column(
            spacing=8,
            controls=[
                row("Pixel (row, col)", self.readout_pixel),
                row("Σ products", self.readout_sum),
                row("Output value", self.readout_out),
                row("Pixels computed", self.readout_done),
                ft.Container(height=4),
                ft.Text(
                    "Colours: the number on each tile is its true brightness "
                    "(0–255). The space colour map is only how it is drawn.",
                    size=10,
                    color=AppColors.MUTED,
                ),
            ],
        )
        return self._panel("READOUT", "The current computation.",
                           ft.Icons.ANALYTICS_OUTLINED, palette.PRODUCT, body)

    # =========================================================
    # STAGE
    # =========================================================

    def _build_stage(self):
        self.caption_step = ft.Text("", size=10, weight=ft.FontWeight.BOLD,
                                    color=palette.KERNEL)
        self.caption_text = ft.Text("", size=self.f_caption, weight=ft.FontWeight.W_600,
                                    color=AppColors.TEXT)
        self.caption = ft.Container(
            left=0,
            top=4,
            width=self.stage_w,
            alignment=ft.Alignment.CENTER,
            opacity=1.0,
            animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.caption_step, self.caption_text],
            ),
        )

        labels = [
            self._label(self.gx, self.gy - 20, "INPUT IMAGE  ·  16 × 16", palette.INPUT),
            self._label(self.mx, self.kernel_top - 24, "", palette.KERNEL, key="kernel_label"),
            self._label(self.mx, self.product_top - 24, "PIXEL × WEIGHT", palette.PRODUCT),
            self._label(self.ox, self.y0 - 24, "OUTPUT IMAGE", palette.OUTPUT),
        ]

        self._build_input_layer()
        self._build_middle_layer()
        self._build_output_layer()
        self._build_token_layer()
        self._build_reveal_overlay()

        self.frame = ft.Container(
            left=self.x0 - 3,
            top=self.y0 - 3,
            width=3 * self.p - (self.p - self.t) + 6,
            height=3 * self.p - (self.p - self.t) + 6,
            border_radius=7,
            bgcolor=palette.argb("14", palette.KERNEL_FRAME),
            border=ft.Border.all(2, palette.KERNEL_FRAME),
            shadow=ft.BoxShadow(blur_radius=18, spread_radius=1,
                                color=palette.argb("88", palette.KERNEL_FRAME)),
            visible=False,
            animate_position=ft.Animation(450, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
        )

        self.stage = ft.Stack(
            width=self.stage_w,
            height=self.stage_h,
            controls=[
                *labels,
                self.input_layer,
                self.middle_layer,
                self.output_layer,
                self.frame,
                self.token_layer,
                self.caption,
                self.reveal_overlay,
            ],
        )

    def _label(self, x, y, text, color, key=None):
        label = ft.Text(text, size=self.f_label, weight=ft.FontWeight.BOLD, color=color)
        if key:
            setattr(self, key, label)
        return ft.Container(left=x, top=y, content=label)

    # ---------------- input + ghost ring ----------------

    def _build_input_layer(self):
        self.input_tiles = {}
        self.ghost_tiles = {}
        controls = []

        # Intro images sit under the tiles and cross-fade into them.
        self.smooth_image = ft.Image(
            src=palette.png_bytes(self.scene, scale=4),
            left=self.x0, top=self.y0, width=self.grid, height=self.grid,
            fit=ft.BoxFit.FILL,
            border_radius=8,
            gapless_playback=True,
            opacity=0.0,
            animate_opacity=ft.Animation(700, ft.AnimationCurve.EASE_IN_OUT),
        )
        self.pixel_image = ft.Image(
            src=palette.png_bytes(self.image, scale=24),
            left=self.x0, top=self.y0, width=self.grid, height=self.grid,
            fit=ft.BoxFit.FILL,
            filter_quality=ft.FilterQuality.NONE,
            border_radius=8,
            gapless_playback=True,
            opacity=0.0,
            animate_opacity=ft.Animation(700, ft.AnimationCurve.EASE_IN_OUT),
        )
        controls += [self.smooth_image, self.pixel_image]

        for r in range(-MAX_PAD, N + MAX_PAD):
            for c in range(-MAX_PAD, N + MAX_PAD):
                inside = 0 <= r < N and 0 <= c < N
                x = self.x0 + c * self.p
                y = self.y0 + r * self.p

                if inside:
                    value = int(self.image[r, c])
                    text = ft.Text(
                        str(value),
                        size=self.f_tile,
                        weight=ft.FontWeight.BOLD,
                        color=palette.pixel_text_color(value),
                        opacity=0.0,
                        animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                    )
                    tile = ft.Container(
                        left=x, top=y, width=self.t, height=self.t,
                        alignment=ft.Alignment.CENTER,
                        border_radius=5,
                        bgcolor=palette.pixel_color(value),
                        border=ft.Border.all(1, "#00000000"),
                        opacity=0.0,
                        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
                        animate=ft.Animation(AppAnimations.FAST, ft.AnimationCurve.EASE_OUT),
                        ink=False,
                        on_click=lambda e, rr=r, cc=c: self.inspect(rr, cc),
                        on_hover=self._hover_tile,
                        data=text,
                        content=text,
                    )
                    self.input_tiles[(r, c)] = tile
                else:
                    text = ft.Text("", size=self.f_ghost, italic=True,
                                   color=AppColors.TEXT_SECONDARY)
                    tile = ft.Container(
                        left=x, top=y, width=self.t, height=self.t,
                        alignment=ft.Alignment.CENTER,
                        border_radius=5,
                        bgcolor="#0C1628",
                        border=ft.Border.all(1, palette.argb("55", palette.INPUT)),
                        opacity=0.0,
                        animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
                        data=text,
                        content=text,
                    )
                    self.ghost_tiles[(r, c)] = tile
                controls.append(tile)

        self.input_layer = ft.Stack(left=0, top=0, width=self.stage_w, height=self.stage_h,
                                    controls=controls)

    def _hover_tile(self, e):
        hovered = str(e.data).lower() == "true"
        e.control.border = ft.Border.all(1.5 if hovered else 1,
                                         palette.INPUT if hovered else "#00000000")
        try:
            e.control.update()
        except Exception:
            pass

    # ---------------- kernel + products + sum ----------------

    def _build_middle_layer(self):
        self.kernel_box = ft.Stack(width=7 * self.kp, height=7 * self.kp)
        self.kernel_holder = ft.Container(
            left=self.mx + (self.mw - 7 * self.kp) / 2,
            top=self.kernel_top,
            width=7 * self.kp,
            height=7 * self.kp,
            rotate=0.0,
            animate_rotation=ft.Animation(900, ft.AnimationCurve.EASE_IN_OUT),
            opacity=0.0,
            offset=ft.Offset(0, 0.25),
            animate_opacity=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(550, ft.AnimationCurve.EASE_OUT),
            content=self.kernel_box,
        )

        # Product cells: a pool of 7 x 7, positioned per kernel size.
        self.product_cells = []
        for _ in range(49):
            top = ft.Text("", size=self.f_cell, weight=ft.FontWeight.BOLD,
                          color=palette.INPUT_SOFT)
            bottom = ft.Text("", size=self.f_cell_small, weight=ft.FontWeight.BOLD,
                             color=palette.KERNEL)
            cell = ft.Container(
                width=self.pt, height=self.pt,
                alignment=ft.Alignment.CENTER,
                border_radius=8,
                bgcolor=AppColors.SURFACE_DARK,
                border=ft.Border.all(1, AppColors.BORDER_SOFT),
                visible=False,
                opacity=1.0,
                scale=1.0,
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                animate_scale=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
                data=(top, bottom),
                content=ft.Column(
                    spacing=0,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[top, bottom],
                ),
            )
            self.product_cells.append(cell)

        self.sum_value = ft.Text("Σ", **_mono(self.f_sum, palette.PRODUCT))
        self.sum_detail = ft.Text("", size=11, color=AppColors.TEXT_SECONDARY)
        self.sum_box = ft.Container(
            left=self.mx,
            top=self.sum_top,
            width=self.mw,
            height=48,
            border_radius=14,
            bgcolor="#E6140F26",
            border=ft.Border.all(1.5, palette.argb("99", palette.PRODUCT)),
            shadow=ft.BoxShadow(blur_radius=20, spread_radius=-6,
                                color=palette.argb("66", palette.PRODUCT)),
            opacity=0.0,
            scale=1.0,
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
                controls=[self.sum_value, self.sum_detail],
            ),
        )

        self.middle_layer = ft.Stack(
            left=0, top=0, width=self.stage_w, height=self.stage_h,
            controls=[self.kernel_holder, *self.product_cells, self.sum_box],
        )

        self._layout_kernel_cells(flipped=False)
        self._layout_product_cells()

    def _layout_kernel_cells(self, flipped):
        kernel = self.trace.flipped if flipped else self.trace.kernel
        k = kernel.shape[0]
        max_abs = float(np.max(np.abs(kernel))) or 1.0
        offset = (7 - k) * self.kp / 2

        cells = []
        for r in range(k):
            for c in range(k):
                weight = float(kernel[r, c])
                cells.append(
                    ft.Container(
                        left=offset + c * self.kp,
                        top=offset + r * self.kp,
                        width=self.kt,
                        height=self.kt,
                        alignment=ft.Alignment.CENTER,
                        border_radius=5,
                        bgcolor=palette.weight_color(weight, max_abs),
                        border=ft.Border.all(1, palette.argb("66", palette.KERNEL)),
                        content=ft.Text(palette.fmt_weight(weight), size=self.f_kernel,
                                        weight=ft.FontWeight.BOLD, color=AppColors.TEXT),
                    )
                )
        self.kernel_box.controls = cells

        name = identify_kernel(self.trace.kernel)
        label = PRESETS[name][0].upper() if name else "CUSTOM KERNEL"
        self.kernel_label.value = f"KERNEL  ·  {label}" + ("  ·  FLIPPED" if flipped else "")

    def _product_origin(self):
        k = self.trace.size
        x = self.mx + (self.mw - k * self.pp) / 2
        y = self.product_top + (7 - k) * self.pp / 2
        return x, y

    def _layout_product_cells(self):
        k = self.trace.size
        x0, y0 = self._product_origin()
        for index, cell in enumerate(self.product_cells):
            if index < k * k:
                r, c = divmod(index, k)
                cell.left = x0 + c * self.pp
                cell.top = y0 + r * self.pp
            cell.visible = False

    # ---------------- output ----------------

    def _build_output_layer(self):
        self.output_tiles = {}
        controls = []
        for r in range(N):
            for c in range(N):
                text = ft.Text("", size=self.f_tile, weight=ft.FontWeight.BOLD,
                               color=AppColors.TEXT, opacity=1.0,
                               animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT))
                tile = ft.Container(
                    left=self.ox + c * self.p, top=self.y0 + r * self.p, width=self.t, height=self.t,
                    alignment=ft.Alignment.CENTER,
                    border_radius=5,
                    bgcolor="#0A1120",
                    border=ft.Border.all(1, AppColors.BORDER_SOFT),
                    scale=1.0,
                    opacity=1.0,
                    animate=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
                    animate_scale=ft.Animation(260, ft.AnimationCurve.EASE_OUT),
                    animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT),
                    data=text,
                    content=text,
                )
                self.output_tiles[(r, c)] = tile
                controls.append(tile)

        # The assembled picture: the numbered tiles dissolve into this,
        # which is the reverse of chapter 1's "picture -> numbers".
        self.output_image = ft.Image(
            src=palette.png_bytes(self.trace.output, scale=24),
            left=self.ox, top=self.y0, width=self.grid, height=self.grid,
            fit=ft.BoxFit.FILL,
            filter_quality=ft.FilterQuality.NONE,
            border_radius=8,
            gapless_playback=True,
            opacity=0.0,
            scale=1.0,
            animate_opacity=ft.Animation(700, ft.AnimationCurve.EASE_IN_OUT),
            animate_scale=ft.Animation(700, ft.AnimationCurve.EASE_OUT),
        )
        controls.append(self.output_image)

        legend_top = self.y0 + self.grid + 18
        controls += [
            ft.Container(
                left=self.ox, top=legend_top, width=self.grid, height=8, border_radius=4,
                gradient=ft.LinearGradient(colors=palette.legend_colors()),
            ),
            ft.Container(left=self.ox, top=legend_top + 12,
                         content=ft.Text("0  dark", size=9, color=AppColors.MUTED)),
            ft.Container(left=self.ox + self.grid - 64, top=legend_top + 12,
                         content=ft.Text("bright  255", size=9, color=AppColors.MUTED)),
        ]

        self.output_layer = ft.Stack(left=0, top=0, width=self.stage_w, height=self.stage_h,
                                     controls=controls)

    # ---------------- flying tokens ----------------

    def _build_token_layer(self):
        self.tokens = []
        for _ in range(49):
            text = ft.Text("", size=self.f_tile, weight=ft.FontWeight.BOLD,
                           color=AppColors.TEXT)
            token = ft.Container(
                left=0, top=0, width=self.t, height=self.t,
                alignment=ft.Alignment.CENTER,
                border_radius=7,
                bgcolor="#EE0B1426",
                border=ft.Border.all(1.5, palette.INPUT),
                shadow=ft.BoxShadow(blur_radius=12, spread_radius=0,
                                    color=palette.argb("88", palette.INPUT)),
                visible=False,
                opacity=1.0,
                scale=1.0,
                animate_position=ft.Animation(650, ft.AnimationCurve.EASE_IN_OUT),
                animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
                animate_scale=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
                data=text,
                content=text,
            )
            self.tokens.append(token)

        self.result_token_text = ft.Text("", size=10, weight=ft.FontWeight.BOLD,
                                         color="#0B1020")
        self.result_token = ft.Container(
            left=0, top=0, width=self.t + 14, height=self.t,
            alignment=ft.Alignment.CENTER,
            border_radius=8,
            bgcolor=palette.PRODUCT,
            shadow=ft.BoxShadow(blur_radius=18, spread_radius=1,
                                color=palette.argb("AA", palette.PRODUCT)),
            visible=False,
            animate_position=ft.Animation(700, ft.AnimationCurve.EASE_IN_OUT),
            animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            content=self.result_token_text,
        )

        self.token_layer = ft.Stack(
            left=0, top=0, width=self.stage_w, height=self.stage_h,
            controls=[*self.tokens, self.result_token],
        )

    # ---------------- reveal ----------------

    def _build_reveal_overlay(self):
        size = self.reveal_image
        self.reveal_before = ft.Image(
            src=palette.png_bytes(self.scene, scale=4),
            width=size, height=size, fit=ft.BoxFit.FILL, border_radius=14,
            gapless_playback=True,
        )
        self.reveal_after = ft.Image(
            src=palette.png_bytes(self.scene, scale=4),
            width=size, height=size, fit=ft.BoxFit.FILL, border_radius=14,
            gapless_playback=True,
        )
        self.reveal_title = ft.Text("", size=22, weight=ft.FontWeight.BOLD,
                                    color=AppColors.TEXT)
        self.reveal_note = ft.Text("", size=12, color=AppColors.TEXT_SECONDARY,
                                   text_align=ft.TextAlign.CENTER)
        self.reveal_kernel_name = ft.Text("", size=11, weight=ft.FontWeight.BOLD,
                                          color=palette.KERNEL)

        def framed(image, caption, accent):
            return ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Container(
                        border_radius=16,
                        border=ft.Border.all(1.5, accent),
                        shadow=ft.BoxShadow(blur_radius=30, spread_radius=-6,
                                            color=palette.argb("77", accent)),
                        content=image,
                    ),
                    ft.Text(caption, size=11, weight=ft.FontWeight.BOLD, color=accent),
                ],
            )

        close = ft.Container(
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            border_radius=12,
            bgcolor=AppColors.SURFACE_3,
            border=ft.Border.all(1, AppColors.BORDER_LIGHT),
            ink=True,
            on_click=self._close_reveal,
            content=ft.Row(tight=True, spacing=8, controls=[
                ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, size=16, color=AppColors.TEXT),
                ft.Text("Back to the pixels", size=11, color=AppColors.TEXT),
            ]),
        )

        self.reveal_overlay = ft.Container(
            left=0, top=0, width=self.stage_w, height=self.stage_h,
            border_radius=16,
            bgcolor="#F4050B16",
            visible=False,
            opacity=0.0,
            animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_OUT),
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=18,
                controls=[
                    self.reveal_title,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=34,
                        controls=[
                            framed(self.reveal_before, f"BEFORE  ·  {REVEAL_SIZE} × {REVEAL_SIZE}",
                                   palette.INPUT),
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=6,
                                controls=[
                                    ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=34,
                                            color=palette.KERNEL),
                                    self.reveal_kernel_name,
                                ],
                            ),
                            framed(self.reveal_after, "AFTER", palette.OUTPUT),
                        ],
                    ),
                    self.reveal_note,
                    close,
                ],
            ),
        )

    # =========================================================
    # GEOMETRY HELPERS
    # =========================================================

    def _tile_pos(self, r, c):
        return self.x0 + c * self.p, self.y0 + r * self.p

    def _frame_rect(self, r, c):
        pad = self.trace.pad
        size = self.trace.size * self.p - (self.p - self.t) + 6
        return self.x0 + (c - pad) * self.p - 3, self.y0 + (r - pad) * self.p - 3, size

    def _product_pos(self, i, j):
        x0, y0 = self._product_origin()
        return x0 + j * self.pp + (self.pt - self.t) / 2, y0 + i * self.pp + (self.pt - self.t) / 2

    # =========================================================
    # STATE (instant, no narration)
    # =========================================================

    def _apply_chapter_state(self, chapter, first_build=False):
        """Put the stage in the resting state a chapter starts from."""
        self.chapter = chapter

        numbers = chapter >= 1
        self.numbers_shown = numbers
        self.smooth_image.opacity = 1.0 if chapter == 0 else 0.0
        self.pixel_image.opacity = 0.0
        for tile in self.input_tiles.values():
            tile.opacity = 1.0 if numbers else 0.0
            tile.data.opacity = 1.0 if numbers else 0.0

        self.kernel_shown = chapter >= 2
        self.flipped_shown = chapter >= 2
        self._layout_kernel_cells(flipped=self.flipped_shown)
        self.kernel_holder.opacity = 1.0 if self.kernel_shown else 0.0
        self.kernel_holder.offset = ft.Offset(0, 0 if self.kernel_shown else 0.25)
        self.kernel_holder.rotate = 0.0

        self._layout_product_cells()
        self.sum_box.opacity = 0.0
        self.assembled = False
        self.output_image.opacity = 0.0
        self.output_image.scale = 1.0
        for tile in self.output_tiles.values():
            tile.opacity = 1.0
            tile.data.opacity = 1.0
        self.frame.visible = False
        self._set_ghosts(False)
        self._hide_tokens()

        if chapter <= 2:
            self._clear_output()
        elif chapter >= 4 and len(self.lit) < N * N:
            # Chapters 5 and 6 need a finished output to work with.
            for r in range(N):
                for c in range(N):
                    self._light_output(r, c)

        self.reveal_overlay.visible = False
        self.reveal_overlay.opacity = 0.0

        step, text = self._resting_caption(chapter)
        self.caption_step.value = step
        self.caption_text.value = text

        self._refresh_chapter_pills()
        self._refresh_readout()

        if not first_build:
            self._safe_update(self.stage)

    def _resting_caption(self, chapter):
        step = f"CHAPTER {chapter + 1}  ·  {CHAPTERS[chapter].upper()}"
        if chapter == 0:
            return step, "Press Play to watch a kernel process an image, pixel by pixel."
        return step, "Press Play to continue, or click any input pixel."

    def _clear_output(self):
        self.lit.clear()
        self.assembled = False
        self.output_image.opacity = 0.0
        self.output_image.scale = 1.0
        for tile in self.output_tiles.values():
            tile.bgcolor = "#0A1120"
            tile.border = ft.Border.all(1, AppColors.BORDER_SOFT)
            tile.data.value = ""
            tile.scale = 1.0
            tile.opacity = 1.0
            tile.data.opacity = 1.0

    def _light_output(self, r, c, pulse=False):
        value = int(self.trace.output[r, c])
        tile = self.output_tiles[(r, c)]
        tile.bgcolor = palette.pixel_color(value)
        tile.border = ft.Border.all(1, "#00000000")
        tile.data.value = str(value)
        tile.data.color = palette.pixel_text_color(value)
        tile.opacity = 1.0
        tile.data.opacity = 1.0
        tile.scale = 1.3 if pulse else 1.0
        self.lit.add((r, c))
        return tile

    def _set_ghosts(self, show, window=None):
        """Show the reflect-padded border for the current kernel size."""
        self.ghosts_shown = show
        pad = self.trace.pad
        for (r, c), tile in self.ghost_tiles.items():
            in_range = -pad <= r < N + pad and -pad <= c < N + pad
            if show and in_range:
                value = self.trace.ghost_value(r, c)
                tile.data.value = str(value)
                highlighted = window is not None and window(r, c)
                tile.opacity = 0.95 if highlighted else 0.38
                tile.bgcolor = palette.argb("CC", palette.pixel_color(value))
                tile.data.color = palette.pixel_text_color(value)
            else:
                tile.opacity = 0.0

    def _hide_tokens(self):
        for token in self.tokens:
            token.visible = False
        self.result_token.visible = False

    def _refresh_chapter_pills(self):
        for index, pill in enumerate(self.chapter_pills):
            active = index == self.chapter
            done = index < self.chapter
            pill.bgcolor = palette.argb("26", palette.KERNEL) if active else AppColors.SURFACE_DARK
            pill.border = ft.Border.all(
                1, palette.KERNEL if active else AppColors.BORDER_SOFT
            )
            number = pill.data
            number.bgcolor = palette.KERNEL if (active or done) else None
            number.content.color = "#0B1020" if (active or done) else palette.KERNEL

    def _refresh_readout(self, pixel=None, total=None, value=None):
        self.readout_pixel.value = f"({pixel[0]}, {pixel[1]})" if pixel else "—"
        self.readout_sum.value = palette.fmt_sum(total) if total is not None else "—"
        self.readout_out.value = str(value) if value is not None else "—"
        self.readout_done.value = f"{len(self.lit)} / {N * N}"

    @staticmethod
    def _safe_update(control):
        try:
            control.update()
        except Exception:
            pass

    # =========================================================
    # USER ACTIONS
    # =========================================================

    def toggle_play(self, e=None):
        if self.timeline.running:
            self.timeline.cancel()
            self.caption_text.value = "Paused. Press Play to continue."
            self._safe_update(self.caption)
            return

        start = self.chapter
        if start == len(CHAPTERS) - 1 and self.reveal_overlay.visible:
            start = 0
            self._apply_chapter_state(0)
        self.timeline.start(lambda gen: self._play_from(gen, start))

    def jump_to(self, chapter):
        self.timeline.cancel()
        self._apply_chapter_state(chapter)
        self.timeline.start(lambda gen: self._play_from(gen, chapter))

    def inspect(self, r, c):
        """Clicked an input pixel: show its computation in full detail."""
        if not self.numbers_shown:
            return
        self.timeline.cancel()
        self.last_pixel = (r, c)
        self.timeline.start(lambda gen: self._inspect_scene(gen, r, c))

    def _replay_pixel(self, e):
        pixel = self.last_pixel or self.trace.most_interesting_pixel()
        if not self.numbers_shown:
            self._apply_chapter_state(2)
        self.inspect(*pixel)

    def _fill_output(self, e):
        self.timeline.cancel()
        if not self.numbers_shown:
            self._apply_chapter_state(3)
        for r in range(N):
            for c in range(N):
                self._light_output(r, c)
        self.frame.visible = False
        self._set_ghosts(False)
        self.caption_text.value = "Every output pixel, computed. Chapter 5 shows the full-size result."
        self._refresh_readout()
        self._safe_update(self.stage)
        self._safe_update(self.readout_done)

    def _on_speed(self, e):
        self.timeline.speed = float(e.control.value)
        self.speed_label.value = f"{self.timeline.speed:.2f}".rstrip("0").rstrip(".") + "×"
        self._safe_update(self.speed_label)

    def _on_kernel_change(self, kernel):
        try:
            trace = ConvolutionTrace(self.image, kernel)
        except (ValueError, AssertionError) as error:
            self.editor._show_error(str(error))
            return

        self.timeline.cancel()
        self.trace = trace

        # Resize the frame instantly for the new kernel.
        self.frame.visible = False
        self._layout_kernel_cells(flipped=self.flipped_shown)
        self._layout_product_cells()
        self.sum_box.opacity = 0.0
        self._set_ghosts(False)
        self._hide_tokens()
        self._clear_output()
        self.pixel_image.opacity = 0.0
        for tile in self.input_tiles.values():
            tile.opacity = 1.0
            tile.data.opacity = 1.0
        self.reveal_overlay.visible = False

        if self.chapter > 2:
            self.chapter = 2
        self._refresh_chapter_pills()
        self._refresh_readout()

        name = identify_kernel(kernel)
        label = PRESETS[name][0] if name else "Custom kernel"
        self.caption_text.value = f"New kernel: {label}. Press Play, or click any pixel."
        self._safe_update(self.stage)
        for control in (self.readout_pixel, self.readout_sum, self.readout_out,
                        self.readout_done):
            self._safe_update(control)
        for pill in self.chapter_pills:
            self._safe_update(pill)

    def stop(self):
        """Called when the user navigates away from the lesson."""
        self.timeline.cancel(notify=False)
        self.play_icon.icon = ft.Icons.PLAY_ARROW_ROUNDED
        self.play_label.value = "Play lesson"

    def _on_running_changed(self, running):
        self.play_icon.icon = ft.Icons.PAUSE_ROUNDED if running else ft.Icons.PLAY_ARROW_ROUNDED
        self.play_label.value = "Pause" if running else "Play lesson"
        self._safe_update(self.play_button)

    def _close_reveal(self, e):
        self.timeline.cancel()
        self.reveal_overlay.opacity = 0.0
        self.reveal_overlay.visible = False
        self._safe_update(self.stage)

    # =========================================================
    # NARRATION HELPERS
    # =========================================================

    async def _say(self, gen, text, step=None, hold=0.0):
        tl = self.timeline
        self.caption.opacity = 0.0
        tl.push(gen, self.caption)
        await tl.wait(gen, 0.2)
        if step is not None:
            self.caption_step.value = step
        self.caption_text.value = text
        self.caption.opacity = 1.0
        tl.push(gen, self.caption)
        if hold:
            await tl.wait(gen, hold)

    def _enter_chapter(self, chapter):
        self.chapter = chapter
        self._refresh_chapter_pills()
        for pill in self.chapter_pills:
            self._safe_update(pill)

    # =========================================================
    # SCENES
    # =========================================================

    async def _play_from(self, gen, chapter):
        scenes = [
            self._scene_intro,
            self._scene_kernel,
            self._scene_detail,
            self._scene_sweep,
            self._scene_assemble,
            self._scene_reveal,
        ]
        for index in range(chapter, len(scenes)):
            self._enter_chapter(index)
            await scenes[index](gen)
            self.timeline.check(gen)
            if index < len(scenes) - 1:
                self.chapter = index + 1
                self._refresh_chapter_pills()

    def _step(self, chapter):
        return f"CHAPTER {chapter + 1}  ·  {CHAPTERS[chapter].upper()}"

    # ---------------- 1. an image is numbers ----------------

    async def _scene_intro(self, gen):
        tl = self.timeline
        step = self._step(0)

        self.smooth_image.opacity = 1.0
        self.pixel_image.opacity = 0.0
        for tile in self.input_tiles.values():
            tile.opacity = 0.0
            tile.data.opacity = 0.0
        tl.push(gen, self.input_layer)

        await self._say(gen, "This is a tiny patch of space: a planet, its ring, a few stars.",
                        step, hold=2.2)
        await self._say(gen, "A computer doesn't see a planet. It stores a grid of pixels.",
                        hold=0.4)

        self.pixel_image.opacity = 1.0
        tl.push(gen, self.input_layer)
        await tl.wait(gen, 0.5)
        self.smooth_image.opacity = 0.0
        tl.push(gen, self.input_layer)
        await tl.wait(gen, 1.4)

        await self._say(gen, "Let's shrink it to 16 × 16, so every single pixel is visible.",
                        hold=0.3)
        for tile in self.input_tiles.values():
            tile.opacity = 1.0
        tl.push(gen, self.input_layer)
        await tl.wait(gen, 0.5)
        self.pixel_image.opacity = 0.0
        tl.push(gen, self.input_layer)
        await tl.wait(gen, 0.9)

        await self._say(gen, "Each pixel is just one number: its brightness, "
                             "from 0 (black) to 255 (white).", hold=0.3)
        for r in range(N):
            for c in range(N):
                self.input_tiles[(r, c)].data.opacity = 1.0
            tl.push(gen, self.input_layer)
            await tl.wait(gen, 0.07)
        self.numbers_shown = True
        await tl.wait(gen, 1.8)

    # ---------------- 2. meet the kernel ----------------

    async def _scene_kernel(self, gen):
        tl = self.timeline
        step = self._step(1)

        if not self.numbers_shown:
            self._apply_chapter_state(1)

        self.flipped_shown = False
        self._layout_kernel_cells(flipped=False)
        self.kernel_holder.rotate = 0.0
        self.kernel_holder.opacity = 0.0
        self.kernel_holder.offset = ft.Offset(0, 0.25)
        tl.push(gen, self.middle_layer, self.kernel_label)

        await self._say(gen, "Now meet the kernel: a small grid of weights.", step, hold=0.3)
        self.kernel_holder.opacity = 1.0
        self.kernel_holder.offset = ft.Offset(0, 0)
        tl.push(gen, self.middle_layer)
        self.kernel_shown = True
        await tl.wait(gen, 1.6)

        name = identify_kernel(self.trace.kernel)
        if name:
            label, meaning, _, _ = PRESETS[name]
            await self._say(gen, f"This one is a {label.lower()}: it {meaning}.", hold=2.4)
        else:
            await self._say(gen, "This is your own custom kernel. Let's see what it does.",
                            hold=2.0)

        await self._say(gen, "Convolution first flips the kernel by 180°.", hold=0.3)
        self.kernel_holder.animate_rotation = ft.Animation(tl.ms(1000),
                                                           ft.AnimationCurve.EASE_IN_OUT)
        self.kernel_holder.rotate = math.pi
        tl.push(gen, self.kernel_holder)
        await tl.wait(gen, 1.15)

        # Snap back without animation and show the flipped values upright:
        # a 180° turn *is* the flip, only the text was upside down.
        self.kernel_holder.animate_rotation = ft.Animation(1, ft.AnimationCurve.LINEAR)
        self.kernel_holder.rotate = 0.0
        self.flipped_shown = True
        self._layout_kernel_cells(flipped=True)
        tl.push(gen, self.middle_layer, self.kernel_label)
        await tl.wait(gen, 0.1)
        self.kernel_holder.animate_rotation = ft.Animation(900, ft.AnimationCurve.EASE_IN_OUT)

        if np.allclose(self.trace.kernel, self.trace.flipped):
            await self._say(gen, "This kernel is symmetric, so flipping it changes nothing.",
                            hold=2.0)
        else:
            await self._say(gen, "Every weight moved to the opposite corner. "
                                 "This flipped grid is what slides over the image.", hold=2.4)

    # ---------------- 3. slide, multiply, sum ----------------

    async def _scene_detail(self, gen):
        step = self._step(2)
        if not self.kernel_shown:
            self._apply_chapter_state(2)
            self.timeline.push(gen, self.stage)

        await self._say(gen, "Place the kernel on the very first pixel, the top-left corner.",
                        step, hold=0.2)
        await self._compute_pixel(gen, 0, 0, narrate=True)

        r, c = self.trace.most_interesting_pixel()
        await self._say(gen, f"Once more, on a busier spot: pixel ({r}, {c}).", hold=0.3)
        await self._compute_pixel(gen, r, c, narrate=True, first=False)
        await self._say(gen, "Every output pixel is made exactly this way.", hold=1.6)

    async def _inspect_scene(self, gen, r, c):
        tl = self.timeline
        if not self.kernel_shown or not self.flipped_shown:
            self.kernel_shown = True
            self.flipped_shown = True
            self._layout_kernel_cells(flipped=True)
            self.kernel_holder.opacity = 1.0
            self.kernel_holder.offset = ft.Offset(0, 0)
            self.kernel_holder.rotate = 0.0
            tl.push(gen, self.middle_layer, self.kernel_label)
        if self.reveal_overlay.visible:
            self.reveal_overlay.visible = False
            tl.push(gen, self.reveal_overlay)

        await self._say(gen, f"Pixel ({r}, {c}): slide, multiply, sum.",
                        "INSPECTING A PIXEL")
        await self._compute_pixel(gen, r, c, narrate=False)

    async def _compute_pixel(self, gen, r, c, narrate, first=True):
        """The heart of the lesson: one output pixel, fully animated."""
        tl = self.timeline
        info = self.trace.pixel(r, c)
        k = self.trace.size
        pad = self.trace.pad
        self.last_pixel = (r, c)

        self._hide_tokens()
        self.result_token.visible = False
        tl.push(gen, self.token_layer)

        # ---- 1. slide the kernel frame onto the window ----------------
        fx, fy, fsize = self._frame_rect(r, c)
        if not self.frame.visible:
            self.frame.visible = True
            self.frame.left, self.frame.top = fx, fy
            self.frame.width = self.frame.height = fsize
            tl.push(gen, self.frame)
            await tl.frame(gen)
        else:
            self.frame.animate_position = ft.Animation(tl.ms(550), ft.AnimationCurve.EASE_IN_OUT)
            self.frame.left, self.frame.top = fx, fy
            self.frame.width = self.frame.height = fsize
            tl.push(gen, self.frame)
        await tl.wait(gen, 0.65)

        # ---- border pixels: reveal the mirrored ring ------------------
        outside = info["outside"]
        in_window = lambda rr, cc: (r - pad <= rr <= r + pad) and (c - pad <= cc <= c + pad)
        if outside.any():
            self._set_ghosts(True, window=in_window)
            tl.push(gen, self.input_layer)
            if narrate:
                await self._say(gen, "Part of the kernel hangs off the image. The border is "
                                     "mirrored (reflect padding), exactly as convolve2d_gray does.",
                                hold=2.6)
            else:
                await tl.wait(gen, 0.5)
        elif self.ghosts_shown:
            self._set_ghosts(False)
            tl.push(gen, self.input_layer)

        # ---- 2. show the weights waiting in the product grid ----------
        flipped = info["flipped"]
        for index in range(k * k):
            i, j = divmod(index, k)
            cell = self.product_cells[index]
            top, bottom = cell.data
            top.value = ""
            bottom.value = "× " + palette.fmt_weight(flipped[i, j])
            bottom.visible = True
            top.color = palette.INPUT_SOFT
            cell.bgcolor = AppColors.SURFACE_DARK
            cell.border = ft.Border.all(1, palette.argb("55", palette.KERNEL))
            cell.visible = True
            cell.opacity = 1.0
            cell.scale = 1.0
        self.sum_box.opacity = 1.0
        self.sum_value.value = "Σ = 0"
        self.sum_detail.value = ""
        tl.push(gen, self.middle_layer)

        if narrate and first:
            await self._say(gen, "Multiply every pixel under the kernel by the weight on top of it…",
                            hold=0.3)

        # ---- 3. tokens rise from the window and fly to their cells ----
        window = info["window"]
        for index in range(k * k):
            i, j = divmod(index, k)
            token = self.tokens[index]
            x, y = self._tile_pos(r - pad + i, c - pad + j)
            token.left, token.top = x, y
            token.data.value = str(int(round(window[i, j])))
            token.border = ft.Border.all(1.5, palette.INPUT)
            token.opacity = 1.0
            token.scale = 1.0
            token.animate_position = ft.Animation(tl.ms(700), ft.AnimationCurve.EASE_IN_OUT)
            token.visible = True
        tl.push(gen, self.token_layer)
        await tl.frame(gen)
        await tl.wait(gen, 0.25)

        for i in range(k):
            for j in range(k):
                token = self.tokens[i * k + j]
                token.left, token.top = self._product_pos(i, j)
            tl.push(gen, self.token_layer)
            await tl.wait(gen, 0.06)
        await tl.wait(gen, 0.75)

        # tokens land: each cell now reads "value × weight"
        for index in range(k * k):
            i, j = divmod(index, k)
            top, bottom = self.product_cells[index].data
            top.value = str(int(round(window[i, j])))
            self.tokens[index].visible = False
        tl.push(gen, self.middle_layer, self.token_layer)
        await tl.wait(gen, 0.9 if narrate else 0.5)

        # ---- 4. each pair collapses into its product ------------------
        products = info["products"]
        max_abs = float(np.max(np.abs(products))) or 1.0
        for index in range(k * k):
            i, j = divmod(index, k)
            cell = self.product_cells[index]
            top, bottom = cell.data
            value = float(products[i, j])
            top.value = palette.fmt_product(value)
            top.color = AppColors.TEXT
            bottom.visible = False
            cell.bgcolor = palette.weight_color(value, max_abs)
            cell.border = ft.Border.all(1, palette.argb("88", palette.PRODUCT))
            cell.scale = 1.12
        tl.push(gen, self.middle_layer)
        await tl.wait(gen, 0.25)
        for cell in self.product_cells[: k * k]:
            cell.scale = 1.0
        tl.push(gen, self.middle_layer)
        await tl.wait(gen, 0.8 if narrate else 0.4)

        if narrate and first:
            await self._say(gen, "…then add all the products together.", hold=0.2)

        # ---- 5. products stream into the Σ box, adding up as they go --
        sum_x = self.mx + self.mw / 2 - self.t / 2
        sum_y = self.sum_top + (48 - self.t) / 2
        for index in range(k * k):
            i, j = divmod(index, k)
            token = self.tokens[index]
            token.left, token.top = self._product_pos(i, j)
            token.data.value = palette.fmt_product(products[i, j])
            token.border = ft.Border.all(1.5, palette.PRODUCT)
            token.opacity = 1.0
            token.scale = 1.0
            token.animate_position = ft.Animation(tl.ms(520), ft.AnimationCurve.EASE_IN)
            token.visible = True
        tl.push(gen, self.token_layer)
        await tl.frame(gen)

        running = 0.0
        batch = max(1, (k * k) // 9)          # 3x3: one by one; 7x7: ~5 at a time
        order = list(range(k * k))
        for start in range(0, len(order), batch):
            chunk = order[start:start + batch]
            for index in chunk:
                token = self.tokens[index]
                token.left, token.top = sum_x, sum_y
                token.scale = 0.55
                token.opacity = 0.0
                i, j = divmod(index, k)
                running += float(products[i, j])
                self.product_cells[index].opacity = 0.35
            tl.push(gen, self.token_layer)
            await tl.wait(gen, 0.12)
            self.sum_value.value = f"Σ = {palette.fmt_sum(running)}"
            self.sum_box.scale = 1.06
            tl.push(gen, self.middle_layer)
            await tl.wait(gen, 0.05)
            self.sum_box.scale = 1.0
        tl.push(gen, self.middle_layer)
        self._hide_tokens()
        tl.push(gen, self.token_layer)

        total = info["total"]
        clipped = info["clipped"]
        self.sum_value.value = f"Σ = {palette.fmt_sum(total)}"
        tl.push(gen, self.middle_layer)
        self._refresh_readout((r, c), total, clipped)
        tl.push(gen, self.readout_pixel, self.readout_sum, self.readout_out)
        await tl.wait(gen, 0.5)

        # ---- 6. round / clip into a valid brightness ------------------
        if total < 0 or total > 255:
            self.sum_detail.value = f"clip → {clipped}"
            if narrate:
                await self._say(gen, f"Brightness must stay within 0–255, so "
                                     f"{palette.fmt_sum(total)} is clipped to {clipped}.",
                                hold=0.4)
        else:
            self.sum_detail.value = f"round → {clipped}"
        tl.push(gen, self.middle_layer)
        await tl.wait(gen, 0.7 if narrate else 0.4)

        # ---- 7. the result flies to its output pixel -----------------
        ox, oy = self.ox + c * self.p, self.y0 + r * self.p
        self.result_token_text.value = str(clipped)
        self.result_token.left = self.mx + self.mw / 2 - (self.t + 14) / 2
        self.result_token.top = sum_y
        self.result_token.opacity = 1.0
        self.result_token.animate_position = ft.Animation(tl.ms(750),
                                                          ft.AnimationCurve.EASE_IN_OUT)
        self.result_token.visible = True
        tl.push(gen, self.token_layer)
        await tl.frame(gen)
        self.result_token.left, self.result_token.top = ox - 6, oy
        tl.push(gen, self.token_layer)
        if narrate and first:
            await self._say(gen, "That single number becomes one pixel of the output image.")
        await tl.wait(gen, 0.8)

        self.result_token.visible = False
        tile = self._light_output(r, c, pulse=True)
        tl.push(gen, self.token_layer, self.output_layer)
        await tl.wait(gen, 0.3)
        tile.scale = 1.0
        tl.push(gen, self.output_layer)
        self._refresh_readout((r, c), total, clipped)
        tl.push(gen, self.readout_done)
        await tl.wait(gen, 1.2 if narrate else 0.3)

    # ---------------- 4. sweep ----------------

    async def _scene_sweep(self, gen):
        tl = self.timeline
        step = self._step(3)

        if not self.kernel_shown:
            self._apply_chapter_state(3)
            tl.push(gen, self.stage)

        for cell in self.product_cells:
            cell.visible = False
        self.sum_box.opacity = 1.0
        self.sum_detail.value = ""
        self._set_ghosts(False)
        tl.push(gen, self.middle_layer, self.input_layer)

        await self._say(gen, "Now repeat it for every pixel: slide, multiply, sum…", step)

        self.frame.visible = True
        tl.push(gen, self.frame)
        pending = [(r, c) for r in range(N) for c in range(N) if (r, c) not in self.lit]

        for count, (r, c) in enumerate(pending):
            # Start deliberate, then accelerate like a montage.
            interval = max(0.028, 0.16 * (0.955 ** count))
            fx, fy, fsize = self._frame_rect(r, c)
            self.frame.animate_position = ft.Animation(
                tl.ms(interval * 1000 * 0.9), ft.AnimationCurve.EASE_OUT
            )
            self.frame.left, self.frame.top = fx, fy
            self.frame.width = self.frame.height = fsize
            self._light_output(r, c)
            info_total = float(self.trace.output_raw[r, c])
            self.sum_value.value = f"Σ = {palette.fmt_sum(info_total)}"
            self.readout_done.value = f"{len(self.lit)} / {N * N}"
            tl.push(gen, self.frame, self.output_tiles[(r, c)], self.sum_value,
                    self.readout_done)
            await tl.wait(gen, interval)

        self.frame.visible = False
        tl.push(gen, self.frame)
        await self._say(gen, "Done: every output pixel is a weighted sum of its neighbourhood.",
                        hold=2.2)

    # ---------------- 5. numbers back into a picture ----------------

    async def _scene_assemble(self, gen):
        """Its own chapter: the output numbers turn back into an image."""
        await self._assemble_output(gen, self._step(4))
        await self.timeline.wait(gen, 1.0)

    async def _assemble_output(self, gen, step):
        """Reverse of chapter 1: the output numbers dissolve into a picture."""
        tl = self.timeline

        if self.assembled:
            return

        if len(self.lit) < N * N:
            for r in range(N):
                for c in range(N):
                    self._light_output(r, c)
            self._refresh_readout()
            tl.push(gen, self.output_layer, self.readout_done)

        self.frame.visible = False
        self.sum_box.opacity = 0.0
        for cell in self.product_cells:
            cell.visible = False
        self._set_ghosts(False)
        tl.push(gen, self.frame, self.middle_layer, self.input_layer)

        await self._say(gen, "Chapter 1 turned a picture into numbers. "
                             "Now run that backwards.", step, hold=1.4)

        # numbers fade away, bottom row first
        for r in reversed(range(N)):
            for c in range(N):
                self.output_tiles[(r, c)].data.opacity = 0.0
            tl.push(gen, self.output_layer)
            await tl.wait(gen, 0.05)
        await tl.wait(gen, 0.5)

        await self._say(gen, "Every brightness becomes a pixel again…", hold=0.3)

        self.output_image.src = palette.png_bytes(self.trace.output, scale=24)
        self.output_image.opacity = 1.0
        tl.push(gen, self.output_layer)
        await tl.wait(gen, 0.5)

        # the grid lines close up as the tiles hand over to the picture
        for tile in self.output_tiles.values():
            tile.opacity = 0.0
        tl.push(gen, self.output_layer)
        await tl.wait(gen, 0.9)

        self.output_image.scale = 1.06
        tl.push(gen, self.output_layer)
        await tl.wait(gen, 0.7)
        self.output_image.scale = 1.0
        tl.push(gen, self.output_layer)
        await tl.wait(gen, 0.4)

        # the input does the same, so both sides are pictures again
        await self._say(gen, "…and the input is a picture again too. "
                             "One kernel took the left image to the right one.", hold=0.3)
        self.pixel_image.opacity = 1.0
        tl.push(gen, self.input_layer)
        await tl.wait(gen, 0.4)
        for tile in self.input_tiles.values():
            tile.opacity = 0.0
        self._set_ghosts(False)
        tl.push(gen, self.input_layer)
        await tl.wait(gen, 1.2)

        await self._say(gen, "Before, and after. Two pictures, one kernel between them.",
                        hold=2.4)
        self.assembled = True

    # ---------------- 6. reveal ----------------

    async def _scene_reveal(self, gen):
        tl = self.timeline

        # Jumping straight here still assembles the picture first.
        await self._assemble_output(gen, self._step(4))

        await self._say(gen, "Same kernel, same arithmetic, on the full-resolution scene…",
                        hold=0.2)

        kernel = self.trace.kernel.copy()
        result = await asyncio.to_thread(convolve_reveal, self.scene, kernel)
        tl.check(gen)

        name = identify_kernel(kernel)
        label = PRESETS[name][0] if name else "Custom kernel"
        self.reveal_after.src = palette.png_bytes(result, scale=4)
        self.reveal_title.value = "The big reveal"
        self.reveal_kernel_name.value = f"{label}  ·  {self.trace.size}×{self.trace.size}"
        self.reveal_note.value = (
            f"{REVEAL_SIZE * REVEAL_SIZE:,} pixels, each one computed exactly like the "
            f"{N * N} you just watched.\nTry another kernel and play it again."
        )
        self.reveal_overlay.visible = True
        self.reveal_overlay.opacity = 0.0
        tl.push(gen, self.reveal_overlay)
        await tl.frame(gen)
        self.reveal_overlay.opacity = 1.0
        tl.push(gen, self.reveal_overlay)

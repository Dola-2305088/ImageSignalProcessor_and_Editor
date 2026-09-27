"""Discover · Lesson 4 — Making a picture bigger and smaller.

Built for someone meeting resampling for the first time.

* **A picture you can name.** The source is an 8 x 8 scene — sky, sun,
  a house with a door, grass — in six unmistakable colours. When
  bilinear blends sky into roof, the new pixel is visibly neither, so
  "blending" is something you see rather than a claim about numbers.

* **One destination pixel, followed the whole way.** Its position is
  mapped back, its four neighbours are named ("sky", "roof"), each gets
  a share, and the blended colour appears as a swatch.

* **Shrinking taught in one dimension.** A single row of stripes, with
  the kept pixels ringed and the discarded ones faded. At the default
  setting the stripes vanish completely and the shrunken strip claims
  the whole row was teal — a lie you can see, next to what it should
  have been.

Every colour and number comes from ColourResizeTrace and strip_shrink,
which use the project's own resize functions and check themselves
against them.

Chapters
    1  A picture is a grid       the 8x8 scene, pixel by pixel
    2  A bigger grid             576 slots, 64 known colours
    3  Where does it come from   one new pixel, mapped back
    4  Nearest: copy one         the closest neighbour, and blockiness
    5  Bilinear: share four      weights, the blend, the smooth edges
    6  Shrinking throws away     one row of stripes, sampled
"""

import flet as ft
import numpy as np

from algorithms.learning.resize_trace import (
    SCENE_NAMES,
    ColourResizeTrace,
    smooth_scene_rgb,
    stripe_strip,
    strip_shrink,
    tiny_scene_rgb,
    upscale_quality,
)
from algorithms.learning.space_scene import render_space_scene
from ui.learning import palette
from ui.learning.scene_engine import Timeline
from ui.theme import AppAnimations, AppColors, AppLayout


SOURCE_TILE = 38
RESULT_BOX = 300
STRIP_TILE = 23
RESULT_STRIP_TILE = 46

SOURCE_ACCENT = palette.INPUT
NEAREST_ACCENT = "#F59E0B"
BILINEAR_ACCENT = palette.PRODUCT
SAMPLE_ACCENT = "#FBBF24"

CHAPTERS = [
    "A picture is a grid",
    "A bigger grid",
    "Where does it come from?",
    "Nearest: copy one",
    "Bilinear: share four",
    "Shrinking throws away",
]


def _hex(colour):
    return "#{:02X}{:02X}{:02X}".format(*[int(v) for v in colour])


def _ink(colour):
    """Readable text colour on top of a given fill."""
    r, g, b = [int(v) for v in colour]
    return "#0B1020" if (0.2126 * r + 0.7152 * g + 0.0722 * b) > 140 else "#F8FAFF"


def _mono(size, color):
    return dict(size=size, color=color, weight=ft.FontWeight.BOLD,
                font_family="Consolas")


def _ordinal(number):
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(
        number if number % 100 not in (11, 12, 13) else 0, "th"
    )
    return f"{number}{suffix}"


class LearnResizeView:
    def __init__(self, page):
        self.page = page

        self.source_kind = "art"
        self.source = tiny_scene_rgb()
        self.scale = 3
        # Chapter 6 opens with a shrink that works, then breaks it.
        self.stripe_width = 4
        self.factor = 2
        self.chapter = 0
        self.method = "nearest"
        self.pixel = None

        self.timeline = Timeline(page, on_state_change=self._on_running_changed)
        self.trace = ColourResizeTrace(self.source, self.scale, names=SCENE_NAMES)
        self.strip = stripe_strip(24, self.stripe_width)
        self.shrunk = strip_shrink(self.strip, self.factor)

        self.control = self._build_page()
        self._apply_chapter_state(0, first_build=True)

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
                                content=ft.Text("DISCOVER  •  LESSON 4", size=9,
                                                weight=ft.FontWeight.BOLD,
                                                color=palette.KERNEL),
                            ),
                            ft.Text("Making a picture bigger and smaller",
                                    size=24, weight=ft.FontWeight.BOLD,
                                    color=AppColors.TEXT),
                            ft.Text("Sky, a sun, a house and grass — "
                                    "sixty-four coloured squares.",
                                    size=11, color=AppColors.TEXT_SECONDARY),
                        ],
                    ),
                    ft.Row(spacing=8, wrap=True, controls=self.chapter_pills),
                ],
            ),
        )

        stage = ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=18),
            border_radius=AppLayout.CARD_RADIUS,
            border=ft.Border.all(1, AppColors.BORDER),
            gradient=ft.RadialGradient(
                center=ft.Alignment(0, -0.3),
                radius=1.3,
                colors=["#101A33", "#070C18"],
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=18,
                controls=[
                    self._caption_block(),
                    self._grids_row(),
                    self._maths_panel(),
                    self._strip_block(),
                ],
            ),
        )

        controls = ft.ResponsiveRow(
            spacing=14,
            run_spacing=14,
            controls=[
                ft.Container(col={"xs": 12, "lg": 4}, content=self._playback_panel()),
                ft.Container(col={"xs": 12, "lg": 4}, content=self._enlarge_panel()),
                ft.Container(col={"xs": 12, "lg": 4}, content=self._shrink_panel()),
            ],
        )

        return ft.Column(
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[header, stage, controls],
        )

    def _chapter_pill(self, index):
        number = ft.Container(
            width=22, height=22,
            alignment=ft.Alignment.CENTER,
            border_radius=11,
            border=ft.Border.all(1, palette.KERNEL),
            content=ft.Text(str(index + 1), size=9, weight=ft.FontWeight.BOLD,
                            color=palette.KERNEL),
        )
        return ft.Container(
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
                tight=True, spacing=8,
                controls=[number, ft.Text(CHAPTERS[index], size=10,
                                          color=AppColors.TEXT_SECONDARY)],
            ),
        )

    def _caption_block(self):
        self.caption_step = ft.Text("", size=10, weight=ft.FontWeight.BOLD,
                                    color=palette.KERNEL)
        self.caption_text = ft.Text("", size=16, weight=ft.FontWeight.W_600,
                                    color=AppColors.TEXT,
                                    text_align=ft.TextAlign.CENTER)
        self.caption = ft.Container(
            width=780,
            opacity=1.0,
            animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.caption_step, self.caption_text],
            ),
        )
        return self.caption

    # ---------------- source and result grids ----------------

    def _grids_row(self):
        self.source_grid = ft.Column(spacing=3,
                                     horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.source_tiles = {}
        self._build_source_grid()

        self.source_card = self._card("SOURCE  ·  8 × 8", SOURCE_ACCENT,
                                      self.source_grid, opacity=1.0)

        self.result_grid = ft.Column(spacing=1,
                                     horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.result_tiles = {}
        self.result_title = ft.Text("", size=9, weight=ft.FontWeight.BOLD,
                                    color=NEAREST_ACCENT)
        self._build_result_grid()

        self.result_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=12,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[self.result_title, self.result_grid],
            ),
        )

        self.compare_card = self._compare_card()

        self.grids_arrow = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            opacity=0.0,
            animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
            controls=[
                ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=26, color=palette.KERNEL),
                ft.Text("enlarge", size=9, color=AppColors.MUTED),
            ],
        )

        return ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
            spacing=16,
            run_spacing=16,
            controls=[self.source_card, self.grids_arrow,
                      self.result_card, self.compare_card],
        )

    def _card(self, title, accent, body, opacity=0.0):
        return ft.Container(
            opacity=opacity,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=12,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text(title, size=9, weight=ft.FontWeight.BOLD, color=accent),
                    body,
                ],
            ),
        )

    def _source_label(self, r, c):
        if self.source_kind == "art":
            return SCENE_NAMES[r][c]
        return ""

    def _build_source_grid(self):
        self.source_tiles = {}
        rows = []

        for r in range(8):
            row = []
            for c in range(8):
                colour = self.source[r, c]
                tile = ft.Container(
                    width=SOURCE_TILE, height=SOURCE_TILE,
                    alignment=ft.Alignment.CENTER,
                    border_radius=6,
                    bgcolor=_hex(colour),
                    border=ft.Border.all(1, "#00000000"),
                    opacity=0.0,
                    scale=1.0,
                    animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                    animate_scale=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
                    animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
                    content=ft.Text(self._source_label(r, c), size=8,
                                    weight=ft.FontWeight.BOLD,
                                    color=_ink(colour)),
                )
                self.source_tiles[(r, c)] = tile
                row.append(tile)
            rows.append(ft.Row(spacing=3, tight=True, controls=row))

        self.source_grid.controls = rows

    def _build_result_grid(self):
        size = self.trace.new_width
        tile = max(4, int(RESULT_BOX / size) - 1)

        self.result_tiles = {}
        rows = []

        for r in range(size):
            row = []
            for c in range(size):
                cell = ft.Container(
                    width=tile, height=tile,
                    border_radius=2,
                    bgcolor="#0A1120",
                    border=ft.Border.all(0.6, "#182338"),
                    animate=ft.Animation(260, ft.AnimationCurve.EASE_OUT),
                )
                self.result_tiles[(r, c)] = cell
                row.append(cell)
            rows.append(ft.Row(spacing=1, tight=True, controls=row))

        self.result_grid.controls = rows
        self.result_title.value = (
            f"RESULT  ·  {size} × {size}  ·  {self.method.upper()}"
        )

    def _compare_card(self):
        self.compare_near = ft.Image(
            src=palette.png_bytes(self.trace.nearest[:, :, 0], scale=1),
            width=150, height=150, fit=ft.BoxFit.FILL,
            filter_quality=ft.FilterQuality.NONE,
            border_radius=10, gapless_playback=True,
        )
        self.compare_bilin = ft.Image(
            src=palette.png_bytes(self.trace.bilinear[:, :, 0], scale=1),
            width=150, height=150, fit=ft.BoxFit.FILL,
            filter_quality=ft.FilterQuality.NONE,
            border_radius=10, gapless_playback=True,
        )
        self._refresh_compare()

        def framed(image, label, accent):
            return ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Container(
                        border_radius=12,
                        border=ft.Border.all(1.2, palette.argb("88", accent)),
                        content=image,
                    ),
                    ft.Text(label, size=9, weight=ft.FontWeight.BOLD, color=accent),
                ],
            )

        return ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=12,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text("SIDE BY SIDE", size=9, weight=ft.FontWeight.BOLD,
                            color=AppColors.MUTED),
                    ft.Row(
                        spacing=10,
                        controls=[
                            framed(self.compare_near, "NEAREST", NEAREST_ACCENT),
                            framed(self.compare_bilin, "BILINEAR", BILINEAR_ACCENT),
                        ],
                    ),
                ],
            ),
        )

    @staticmethod
    def _rgb_png(image):
        from io import BytesIO

        from PIL import Image

        buffer = BytesIO()
        Image.fromarray(np.asarray(image, dtype=np.uint8)).save(buffer, format="PNG")
        return buffer.getvalue()

    def _refresh_compare(self):
        self.compare_near.src = self._rgb_png(self.trace.nearest)
        self.compare_bilin.src = self._rgb_png(self.trace.bilinear)

    # ---------------- the arithmetic ----------------

    def _maths_panel(self):
        self.line_target = self._maths_line("1", "Pick one new pixel", SOURCE_ACCENT)
        self.line_formula = self._maths_line("2", "Map it back", palette.KERNEL)
        self.line_lands = self._maths_line("3", "It lands between pixels",
                                           palette.KERNEL_FRAME)
        self.line_answer = self._maths_line("4", "So the colour is", NEAREST_ACCENT)

        self.answer_swatch = ft.Container(
            width=26, height=26, border_radius=7,
            bgcolor="#00000000",
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )
        self.line_answer["row"].controls.append(self.answer_swatch)

        self.weights_row = ft.Row(spacing=8, alignment=ft.MainAxisAlignment.CENTER,
                                  wrap=True, run_spacing=8)
        self.weights_holder = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
            content=self.weights_row,
        )

        self.maths_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            width=780,
            padding=16,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                spacing=10,
                controls=[
                    self.line_target["row"],
                    self.line_formula["row"],
                    self.line_lands["row"],
                    self.weights_holder,
                    self.line_answer["row"],
                ],
            ),
        )
        return self.maths_card

    def _maths_line(self, number, label, accent):
        value = ft.Text("", **_mono(13, AppColors.TEXT))
        row = ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            opacity=0.0,
            animate_opacity=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
            controls=[
                ft.Container(
                    width=22, height=22,
                    alignment=ft.Alignment.CENTER,
                    border_radius=11,
                    bgcolor=palette.argb("22", accent),
                    border=ft.Border.all(1, accent),
                    content=ft.Text(number, size=9, weight=ft.FontWeight.BOLD,
                                    color=accent),
                ),
                ft.Container(
                    width=190,
                    content=ft.Text(label, size=11, color=AppColors.TEXT_SECONDARY),
                ),
                value,
            ],
        )
        return {"row": row, "value": value, "accent": accent}

    def _weight_chip(self, item):
        colour = item["colour"]
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            border_radius=10,
            bgcolor=AppColors.SURFACE_3,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Row(
                tight=True,
                spacing=8,
                controls=[
                    ft.Container(width=22, height=22, border_radius=6,
                                 bgcolor=_hex(colour)),
                    ft.Column(
                        spacing=0,
                        controls=[
                            ft.Text(item["name"], size=10, weight=ft.FontWeight.BOLD,
                                    color=AppColors.TEXT),
                            ft.Text(f"{item['weight'] * 100:.0f}% of the vote",
                                    size=9, color=AppColors.TEXT_SECONDARY),
                        ],
                    ),
                ],
            ),
        )

    # ---------------- the stripe (shrinking) demo ----------------

    def _strip_block(self):
        self.strip_row = ft.Row(spacing=2, alignment=ft.MainAxisAlignment.CENTER,
                                tight=True)
        self.kept_row = ft.Row(spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                               tight=True)
        self.ideal_row = ft.Row(spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                                tight=True)
        self.blurred_row = ft.Row(spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                                  tight=True)

        self.strip_note = ft.Text("", size=10, color=AppColors.MUTED)
        self.kept_note = ft.Text("", **_mono(10, NEAREST_ACCENT))
        self.ideal_note = ft.Text("", **_mono(10, SOURCE_ACCENT))
        self.blurred_note = ft.Text("", **_mono(10, BILINEAR_ACCENT))

        self.ideal_holder = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
            content=self._strip_line("WHAT IT SHOULD BE  ·  the honest average",
                                     SOURCE_ACCENT, self.ideal_row, self.ideal_note),
        )
        self.blurred_holder = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
            content=self._strip_line("BLUR FIRST, THEN KEEP", BILINEAR_ACCENT,
                                     self.blurred_row, self.blurred_note),
        )
        self.kept_holder = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
            content=self._strip_line("KEEP THE RINGED PIXELS", NEAREST_ACCENT,
                                     self.kept_row, self.kept_note),
        )

        self._build_strip(show_samples=False)

        self.strip_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=18,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                controls=[
                    self._strip_line("ONE ROW OF A STRIPED PICTURE  ·  24 pixels",
                                     SAMPLE_ACCENT, self.strip_row, self.strip_note),
                    self.kept_holder,
                    self.ideal_holder,
                    self.blurred_holder,
                ],
            ),
        )
        return self.strip_card

    @staticmethod
    def _strip_line(title, accent, row, note):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            controls=[
                ft.Text(title, size=9, weight=ft.FontWeight.BOLD, color=accent),
                row,
                note,
            ],
        )

    def _build_strip(self, show_samples=False):
        kept_indices = set(self.shrunk["indices"])

        cells = []
        for index, colour in enumerate(self.strip):
            sampled = index in kept_indices
            cells.append(ft.Container(
                width=STRIP_TILE, height=STRIP_TILE * 2,
                border_radius=4,
                bgcolor=_hex(colour),
                border=ft.Border.all(2.5 if (show_samples and sampled) else 0.5,
                                     SAMPLE_ACCENT if (show_samples and sampled)
                                     else "#00000000"),
                opacity=1.0 if (not show_samples or sampled) else 0.28,
                animate=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
                animate_opacity=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
            ))
        self.strip_row.controls = cells

        self.strip_note.value = (
            f"{self.stripe_width} px stripes  ·  shrink ÷{self.factor}"
            + ("  ·  only the ringed ones are ever read" if show_samples else "")
        )

        self._fill_strip(self.kept_row, self.shrunk["kept"])
        self._fill_strip(self.ideal_row, self.shrunk["ideal"])
        self._fill_strip(self.blurred_row, self.shrunk["blurred"])

        self.kept_note.value = f"off by {self.shrunk['kept_error']:.1f}"
        self.ideal_note.value = "this is the target"
        self.blurred_note.value = f"off by {self.shrunk['blurred_error']:.1f}"

    def _fill_strip(self, row, colours):
        # Match the source strip's total width so the eye can compare
        # shapes directly instead of guessing at the scale.
        total = 24 * (STRIP_TILE + 2)
        width = max(18, total / max(1, len(colours)) - 4)

        row.controls = [
            ft.Container(
                width=width, height=STRIP_TILE * 2,
                border_radius=6,
                bgcolor=_hex(colour),
                animate=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
            )
            for colour in colours
        ]

    # ---------------- control panels ----------------

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
                                width=34, height=34,
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

    def _small_button(self, label, icon, handler, accent=None):
        return ft.Container(
            expand=True,
            height=38,
            border_radius=11,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, accent or AppColors.BORDER_SOFT),
            ink=True,
            on_click=handler,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(icon, size=15, color=accent or AppColors.TEXT_SECONDARY),
                    ft.Text(label, size=10, color=accent or AppColors.TEXT_SECONDARY),
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

        self.speed_label = ft.Text("1×", size=11, weight=ft.FontWeight.BOLD,
                                   color=palette.KERNEL)

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
                    controls=[
                        ft.Icon(ft.Icons.SPEED, size=16, color=AppColors.MUTED),
                        ft.Text("Speed", size=10, color=AppColors.MUTED),
                        ft.Container(expand=True, content=ft.Slider(
                            min=0.5, max=2.0, divisions=6, value=1.0,
                            active_color=palette.KERNEL,
                            on_change=self._on_speed,
                        )),
                        self.speed_label,
                    ],
                ),
            ],
        )
        return self._panel("PLAYBACK", "One idea at a time.",
                           ft.Icons.SMART_DISPLAY_OUTLINED, palette.KERNEL, body)

    def _enlarge_panel(self):
        self.scale_buttons = {
            value: self._small_button(f"{value}×", ft.Icons.ZOOM_OUT_MAP,
                                      lambda e, v=value: self.set_scale(v))
            for value in (2, 3, 4)
        }
        self.method_buttons = {
            "nearest": self._small_button("Nearest", ft.Icons.GRID_4X4,
                                          lambda e: self.set_method("nearest")),
            "bilinear": self._small_button("Bilinear", ft.Icons.BLUR_LINEAR,
                                           lambda e: self.set_method("bilinear")),
        }

        self.source_buttons = {
            "art": self._small_button("Flat art", ft.Icons.HOME_OUTLINED,
                                      lambda e: self.set_source("art")),
            "photo": self._small_button("Photo", ft.Icons.PHOTO_CAMERA_OUTLINED,
                                        lambda e: self.set_source("photo")),
        }

        body = ft.Column(
            spacing=10,
            controls=[
                ft.Text("Picture", size=10, color=AppColors.MUTED),
                ft.Row(spacing=8, controls=list(self.source_buttons.values())),
                ft.Text("Enlarge by", size=10, color=AppColors.MUTED),
                ft.Row(spacing=8, controls=list(self.scale_buttons.values())),
                ft.Text("Method", size=10, color=AppColors.MUTED),
                ft.Row(spacing=8, controls=list(self.method_buttons.values())),
                self._small_button("Another new pixel", ft.Icons.CENTER_FOCUS_STRONG,
                                   lambda e: self.pick_pixel()),
            ],
        )
        return self._panel("ENLARGING", "Invent the in-between pixels.",
                           ft.Icons.PHOTO_SIZE_SELECT_LARGE, SOURCE_ACCENT, body)

    def _shrink_panel(self):
        self.width_buttons = {
            value: self._small_button(f"{value} px", ft.Icons.VIEW_WEEK,
                                      lambda e, v=value: self.set_stripe_width(v))
            for value in (2, 3, 4)
        }
        self.factor_buttons = {
            value: self._small_button(f"÷{value}", ft.Icons.COMPRESS,
                                      lambda e, v=value: self.set_factor(v))
            for value in (2, 3, 4)
        }

        body = ft.Column(
            spacing=10,
            controls=[
                ft.Text("Stripe width", size=10, color=AppColors.MUTED),
                ft.Row(spacing=8, controls=list(self.width_buttons.values())),
                ft.Text("Shrink by", size=10, color=AppColors.MUTED),
                ft.Row(spacing=8, controls=list(self.factor_buttons.values())),
                ft.Text("Some combinations line up and need no blur. "
                        "The numbers say which.", size=10, color=AppColors.MUTED),
            ],
        )
        return self._panel("SHRINKING", "Choose what to throw away.",
                           ft.Icons.PHOTO_SIZE_SELECT_SMALL, SAMPLE_ACCENT, body)

    # =========================================================
    # STATE
    # =========================================================

    def _apply_chapter_state(self, chapter, first_build=False):
        self.chapter = chapter

        for tile in self.source_tiles.values():
            tile.opacity = 1.0
            tile.border = ft.Border.all(1, "#00000000")
            tile.scale = 1.0

        self.grids_arrow.opacity = 1.0 if chapter >= 1 else 0.0
        self.result_card.opacity = 1.0 if chapter >= 1 else 0.0
        self.maths_card.opacity = 1.0 if chapter >= 2 else 0.0
        self.weights_holder.opacity = 1.0 if chapter >= 4 else 0.0
        self.compare_card.opacity = 1.0 if chapter >= 4 else 0.0
        self.strip_card.opacity = 1.0 if chapter >= 5 else 0.0

        for line in (self.line_target, self.line_formula,
                     self.line_lands, self.line_answer):
            line["row"].opacity = 1.0 if chapter >= 2 else 0.0
            line["value"].value = ""
        self.answer_swatch.bgcolor = "#00000000"

        self.method = "bilinear" if chapter >= 4 else "nearest"
        self._build_result_grid()

        if chapter >= 3:
            self._fill_result(self.method)
        if chapter >= 2:
            self._prepare_pixel()
            self._write_maths(full=chapter >= 3, weights=chapter >= 4)
        if chapter >= 4:
            self._refresh_compare()
        if chapter >= 5:
            self._build_strip(show_samples=True)
            self.kept_holder.opacity = 1.0
            self.ideal_holder.opacity = 1.0
            self.blurred_holder.opacity = 1.0
        else:
            self.kept_holder.opacity = 0.0
            self.ideal_holder.opacity = 0.0
            self.blurred_holder.opacity = 0.0

        self._refresh_toggles()

        step, text = self._resting_caption(chapter)
        self.caption_step.value = step
        self.caption_text.value = text

        self._refresh_chapter_pills()

        if not first_build:
            self._safe_update(self.control)

    def _resting_caption(self, chapter):
        step = f"CHAPTER {chapter + 1}  ·  {CHAPTERS[chapter].upper()}"
        if chapter == 0:
            return step, "Press Play. We will enlarge an eight by eight picture."
        return step, "Press Play to continue, or use the controls yourself."

    def _prepare_pixel(self):
        if self.pixel is None:
            self.pixel = self.trace.interesting_pixel()

        self.info = self.trace.pixel(*self.pixel)
        self._highlight_neighbours()
        self._highlight_target()

    def _highlight_neighbours(self, only_nearest=False):
        for tile in self.source_tiles.values():
            tile.border = ft.Border.all(1, "#00000000")
            tile.scale = 1.0

        if only_nearest:
            r, c = self.info["nearest_source"]
            tile = self.source_tiles[(r, c)]
            tile.border = ft.Border.all(3, NEAREST_ACCENT)
            tile.scale = 1.12
            return

        for item in self.info["corners"]:
            tile = self.source_tiles[(item["row"], item["col"])]
            tile.border = ft.Border.all(2.5, palette.KERNEL_FRAME)
            tile.scale = 1.08

    def _highlight_target(self):
        for (r, c), cell in self.result_tiles.items():
            if (r, c) == (self.info["new_y"], self.info["new_x"]):
                cell.border = ft.Border.all(1.8, "#FFFFFF")
            else:
                cell.border = ft.Border.all(0.6, "#182338")

    def _fill_result(self, method, only=None):
        image = self.trace.nearest if method == "nearest" else self.trace.bilinear

        cells = only if only is not None else list(self.result_tiles.keys())
        for (r, c) in cells:
            self.result_tiles[(r, c)].bgcolor = _hex(image[r, c])

        self.result_title.value = (
            f"RESULT  ·  {self.trace.new_width} × {self.trace.new_height}  ·  "
            f"{method.upper()}"
        )
        self.result_title.color = (NEAREST_ACCENT if method == "nearest"
                                   else BILINEAR_ACCENT)

    def _clear_result(self):
        for cell in self.result_tiles.values():
            cell.bgcolor = "#0A1120"

    def _write_maths(self, full=True, weights=False):
        info = self.info

        self.line_target["value"].value = (
            f"row {info['new_y']}, column {info['new_x']}"
        )
        self.line_formula["value"].value = (
            f"({info['new_x']} + 0.5) × 8/{self.trace.new_width} − 0.5"
        )
        self.line_lands["value"].value = (
            f"column {info['source_x']:.2f}, row {info['source_y']:.2f}"
        )

        if not full:
            self.line_answer["value"].value = ""
            self.answer_swatch.bgcolor = "#00000000"
            return

        if weights:
            self.weights_row.controls = [
                self._weight_chip(item) for item in info["corners"]
            ]
            self.line_answer["value"].value = (
                f"blend of four  =  RGB {info['blend']}"
            )
            self.answer_swatch.bgcolor = _hex(info["blend"])
        else:
            r, c = info["nearest_source"]
            self.line_answer["value"].value = (
                f"copy '{info['nearest_name']}' at row {r}, column {c}"
            )
            self.answer_swatch.bgcolor = _hex(info["nearest_colour"])

    def _refresh_toggles(self):
        for kind, button in self.source_buttons.items():
            active = kind == self.source_kind
            button.border = ft.Border.all(
                1, SOURCE_ACCENT if active else AppColors.BORDER_SOFT)
            button.bgcolor = (palette.argb("22", SOURCE_ACCENT) if active
                              else AppColors.SURFACE_DARK)

        for value, button in self.scale_buttons.items():
            active = value == self.scale
            button.border = ft.Border.all(
                1, SOURCE_ACCENT if active else AppColors.BORDER_SOFT)
            button.bgcolor = (palette.argb("22", SOURCE_ACCENT) if active
                              else AppColors.SURFACE_DARK)

        for name, button in self.method_buttons.items():
            active = name == self.method
            accent = NEAREST_ACCENT if name == "nearest" else BILINEAR_ACCENT
            button.border = ft.Border.all(
                1, accent if active else AppColors.BORDER_SOFT)
            button.bgcolor = (palette.argb("22", accent) if active
                              else AppColors.SURFACE_DARK)

        for value, button in self.width_buttons.items():
            active = value == self.stripe_width
            button.border = ft.Border.all(
                1, SAMPLE_ACCENT if active else AppColors.BORDER_SOFT)
            button.bgcolor = (palette.argb("22", SAMPLE_ACCENT) if active
                              else AppColors.SURFACE_DARK)

        for value, button in self.factor_buttons.items():
            active = value == self.factor
            button.border = ft.Border.all(
                1, SAMPLE_ACCENT if active else AppColors.BORDER_SOFT)
            button.bgcolor = (palette.argb("22", SAMPLE_ACCENT) if active
                              else AppColors.SURFACE_DARK)

    def _refresh_chapter_pills(self):
        for index, pill in enumerate(self.chapter_pills):
            active = index == self.chapter
            done = index < self.chapter
            pill.bgcolor = (palette.argb("26", palette.KERNEL) if active
                            else AppColors.SURFACE_DARK)
            pill.border = ft.Border.all(
                1, palette.KERNEL if active else AppColors.BORDER_SOFT)
            number = pill.data
            number.bgcolor = palette.KERNEL if (active or done) else None
            number.content.color = "#0B1020" if (active or done) else palette.KERNEL

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

        start = 0 if self.chapter >= len(CHAPTERS) - 1 else self.chapter
        if start == 0:
            self._apply_chapter_state(0)
        self.timeline.start(lambda gen: self._play_from(gen, start))

    def jump_to(self, chapter):
        self.timeline.cancel()
        self._apply_chapter_state(chapter)
        self.timeline.start(lambda gen: self._play_from(gen, chapter))

    def set_source(self, kind):
        """Flat pixel art, or a softly shaded photograph."""
        self.timeline.cancel()
        self.source_kind = kind

        if kind == "art":
            self.source = tiny_scene_rgb()
            message = ("Flat art: big areas of one colour with hard edges "
                       "between them.")
        else:
            self.source = smooth_scene_rgb(8)
            message = ("A photograph: every neighbour differs a little, and "
                       "nothing is flat.")

        self.trace = ColourResizeTrace(self.source, self.scale,
                                       names=self._names())
        self.pixel = None

        self._build_source_grid()
        self._build_result_grid()
        self._prepare_pixel()
        self._fill_result(self.method)
        self._write_maths(full=True, weights=self.method == "bilinear")
        self._refresh_compare()
        self._refresh_toggles()

        self.caption_text.value = message
        self._safe_update(self.control)

    def _names(self):
        return SCENE_NAMES if self.source_kind == "art" else None

    def set_scale(self, value):
        self.timeline.cancel()
        self.scale = int(value)
        self.trace = ColourResizeTrace(self.source, self.scale,
                                       names=self._names())
        self.pixel = None
        self._build_result_grid()
        self._prepare_pixel()
        self._fill_result(self.method)
        self._write_maths(full=True, weights=self.method == "bilinear")
        self._refresh_compare()
        self._refresh_toggles()
        self.caption_text.value = (
            f"{self.scale}× enlargement: each source pixel now covers "
            f"{self.scale * self.scale} new ones."
        )
        self._safe_update(self.control)

    def set_method(self, name):
        self.timeline.cancel()
        self.method = name
        self._fill_result(name)
        self._write_maths(full=True, weights=name == "bilinear")
        self.weights_holder.opacity = 1.0 if name == "bilinear" else 0.0
        self._highlight_neighbours(only_nearest=name == "nearest")
        self._refresh_toggles()

        info = self.info
        self.caption_text.value = (
            f"Nearest copies '{info['nearest_name']}'; bilinear mixes the four "
            f"into RGB {info['blend']}. Same pixel, two answers."
        )
        self._safe_update(self.control)

    def pick_pixel(self):
        self.timeline.cancel()

        rng = np.random.default_rng()

        # Keep the best handful and pick one at random, so pressing the
        # button twice does not land on the same pixel.
        candidates = []
        for _ in range(120):
            new_y = int(rng.integers(0, self.trace.new_height))
            new_x = int(rng.integers(0, self.trace.new_width))
            candidates.append(
                (self.trace.disagreement(new_y, new_x), (new_y, new_x))
            )

        candidates.sort(key=lambda pair: pair[0], reverse=True)
        top = [pixel for _, pixel in candidates[:6]]
        self.pixel = top[int(rng.integers(0, len(top)))]
        self._prepare_pixel()
        self._write_maths(full=True, weights=self.method == "bilinear")
        self._highlight_neighbours(only_nearest=self.method == "nearest")
        self.caption_text.value = (
            f"This new pixel sits between "
            f"{', '.join(sorted({item['name'] for item in self.info['corners']}))}."
        )
        self._safe_update(self.control)

    def set_stripe_width(self, value):
        self.timeline.cancel()
        self.stripe_width = int(value)
        self._rebuild_strip()

    def set_factor(self, value):
        self.timeline.cancel()
        self.factor = int(value)
        self._rebuild_strip()

    def _rebuild_strip(self):
        self.strip = stripe_strip(24, self.stripe_width)
        self.shrunk = strip_shrink(self.strip, self.factor)
        self._build_strip(show_samples=True)
        self.strip_card.opacity = 1.0
        self.kept_holder.opacity = 1.0
        self.ideal_holder.opacity = 1.0
        self.blurred_holder.opacity = 1.0
        self._refresh_toggles()

        self.caption_text.value = self._strip_verdict(long_form=False)
        self._safe_update(self.control)

    def _strip_verdict(self, long_form=True):
        """What the two errors actually say, in three honest cases."""
        kept = self.shrunk["kept_error"]
        blurred = self.shrunk["blurred_error"]
        every = _ordinal(self.factor)

        if kept < 1.0:
            return (
                f"Here the stripes line up exactly with the shrink, so keeping "
                f"every {every} pixel is already right ({kept:.1f}) and blurring "
                f"first would only cost sharpness ({blurred:.1f})."
            )

        if blurred < kept - 1.0:
            if long_form:
                return (
                    f"Off by {blurred:.1f} instead of {kept:.1f}. It looks duller, "
                    f"and it is the truthful answer."
                )
            return (
                f"{self.stripe_width} px stripes shrunk by {self.factor}: keeping "
                f"every {every} pixel is off by {kept:.1f}, blurring first only "
                f"{blurred:.1f}."
            )

        return (
            f"This one is a draw: {kept:.1f} against {blurred:.1f}. The stripes "
            f"are too close to the shrink size for either choice to rescue them."
        )

    def _on_speed(self, e):
        self.timeline.speed = float(e.control.value)
        self.speed_label.value = f"{self.timeline.speed:.2f}".rstrip("0").rstrip(".") + "×"
        self._safe_update(self.speed_label)

    def stop(self):
        self.timeline.cancel(notify=False)
        self.play_icon.icon = ft.Icons.PLAY_ARROW_ROUNDED
        self.play_label.value = "Play lesson"

    def _on_running_changed(self, running):
        self.play_icon.icon = (ft.Icons.PAUSE_ROUNDED if running
                               else ft.Icons.PLAY_ARROW_ROUNDED)
        self.play_label.value = "Pause" if running else "Play lesson"
        self._safe_update(self.play_button)

    # =========================================================
    # SCENES
    # =========================================================

    async def _say(self, gen, text, step=None, hold=0.0):
        tl = self.timeline
        self.caption.opacity = 0.0
        tl.push(gen, self.caption)
        await tl.wait(gen, 0.25)
        if step is not None:
            self.caption_step.value = step
        self.caption_text.value = text
        self.caption.opacity = 1.0
        tl.push(gen, self.caption)
        if hold:
            await tl.wait(gen, hold)

    def _step(self, chapter):
        return f"CHAPTER {chapter + 1}  ·  {CHAPTERS[chapter].upper()}"

    def _enter_chapter(self, index):
        self.chapter = index
        self._refresh_chapter_pills()
        for pill in self.chapter_pills:
            self._safe_update(pill)

    async def _play_from(self, gen, chapter):
        scenes = [
            self._scene_grid,
            self._scene_bigger,
            self._scene_mapping,
            self._scene_nearest,
            self._scene_bilinear,
            self._scene_strip,
        ]
        for index in range(chapter, len(scenes)):
            self._enter_chapter(index)
            await scenes[index](gen)
            self.timeline.check(gen)

    # ---------------- 1 ----------------

    async def _scene_grid(self, gen):
        tl = self.timeline

        for tile in self.source_tiles.values():
            tile.opacity = 0.0
        self.grids_arrow.opacity = 0.0
        self.result_card.opacity = 0.0
        self.maths_card.opacity = 0.0
        self.compare_card.opacity = 0.0
        self.strip_card.opacity = 0.0
        tl.push(gen, self.control)

        await self._say(gen, "A picture of a house: sky, a sun, a roof, a wall, "
                             "a door and grass.", self._step(0), hold=0.6)

        for r in range(8):
            for c in range(8):
                self.source_tiles[(r, c)].opacity = 1.0
            tl.push(gen, self.source_card)
            await tl.wait(gen, 0.2)

        await tl.wait(gen, 1.6)
        await self._say(gen, "Eight squares across, eight down. Sixty-four coloured "
                             "squares is the entire picture — there is nothing "
                             "stored between them.", hold=4.2)

    # ---------------- 2 ----------------

    async def _scene_bigger(self, gen):
        tl = self.timeline
        size = self.trace.new_width

        await self._say(gen, f"We want it {self.scale} times bigger: {size} squares "
                             f"across instead of 8.", self._step(1), hold=0.5)

        self._clear_result()
        self.grids_arrow.opacity = 1.0
        self.result_card.opacity = 1.0
        tl.push(gen, self.control)
        await tl.wait(gen, 2.0)

        await self._say(gen, f"{size * size} empty squares, and only 64 known "
                             f"colours to fill them from. The rest have to be "
                             f"worked out.", hold=4.2)

        await self._say(gen, "Nothing is stretched. A new empty grid is built, and "
                             "each of its squares asks the old picture what colour "
                             "it should be.", hold=4.4)

    # ---------------- 3 ----------------

    async def _scene_mapping(self, gen):
        tl = self.timeline

        await self._say(gen, "Follow one empty square all the way through.",
                        self._step(2), hold=0.5)

        self.pixel = self.trace.interesting_pixel()
        self._prepare_pixel()
        for line in (self.line_target, self.line_formula,
                     self.line_lands, self.line_answer):
            line["row"].opacity = 0.0
            line["value"].value = ""
        self.answer_swatch.bgcolor = "#00000000"
        for tile in self.source_tiles.values():
            tile.border = ft.Border.all(1, "#00000000")
            tile.scale = 1.0
        self.weights_holder.opacity = 0.0
        self.maths_card.opacity = 1.0
        tl.push(gen, self.control)
        await tl.wait(gen, 0.6)

        info = self.info

        self._write_maths(full=False)
        self.line_target["row"].opacity = 1.0
        tl.push(gen, self.maths_card)
        self._highlight_target()
        tl.push(gen, self.result_card)
        await self._say(gen, f"This one: row {info['new_y']}, column "
                             f"{info['new_x']} of the new grid — outlined in white.",
                        hold=3.0)

        self.line_formula["row"].opacity = 1.0
        tl.push(gen, self.maths_card)
        await self._say(gen, "Ask where it sits in the old picture: multiply by the "
                             "size ratio. The halves appear because a square's "
                             "position is its centre, not its corner.", hold=4.6)

        self.line_lands["row"].opacity = 1.0
        tl.push(gen, self.maths_card)
        await tl.wait(gen, 0.4)

        self._highlight_neighbours()
        tl.push(gen, self.source_card)
        await self._say(gen, f"It lands at column {info['source_x']:.2f}, row "
                             f"{info['source_y']:.2f} — between squares, not on "
                             f"one.", hold=4.0)

        names = ", ".join(sorted({item["name"] for item in info["corners"]}))
        await self._say(gen, f"The four outlined squares are its neighbours: "
                             f"{names}. Everything now depends on how you use them.",
                        hold=4.4)

    # ---------------- 4 ----------------

    async def _scene_nearest(self, gen):
        tl = self.timeline
        info = self.info

        await self._say(gen, "Simplest answer: whichever neighbour is closest, "
                             "copy its colour.", self._step(3), hold=0.5)

        self.method = "nearest"
        self._highlight_neighbours(only_nearest=True)
        self._write_maths(full=True, weights=False)
        self.line_answer["row"].opacity = 1.0
        self.weights_holder.opacity = 0.0
        self._refresh_toggles()
        tl.push(gen, self.control)

        r, c = info["nearest_source"]
        await self._say(gen, f"The closest is '{info['nearest_name']}' at row {r}, "
                             f"column {c}. So the new square becomes that exact "
                             f"colour. Nothing is calculated — it is a copy.",
                        hold=4.6)

        self._clear_result()
        self._fill_result("nearest", only=[(info["new_y"], info["new_x"])])
        self._highlight_target()
        tl.push(gen, self.result_card)
        await tl.wait(gen, 1.4)

        await self._say(gen, "Now every square, the same way.", hold=0.4)

        size = self.trace.new_width
        for r in range(size):
            self._fill_result("nearest", only=[(r, c) for c in range(size)])
            tl.push(gen, self.result_card)
            await tl.wait(gen, 0.08)

        await tl.wait(gen, 1.2)
        await self._say(gen, f"Each old square became a solid block of "
                             f"{self.scale}×{self.scale}. The roof edge is now a "
                             f"staircase, because no colour was ever invented "
                             f"between roof and sky.", hold=4.8)

    # ---------------- 5 ----------------

    async def _scene_bilinear(self, gen):
        tl = self.timeline
        info = self.info

        await self._say(gen, "Better answer: let all four neighbours vote, and give "
                             "the closest ones the loudest voice.",
                        self._step(4), hold=0.5)

        self.method = "bilinear"
        self._highlight_neighbours()
        self._write_maths(full=True, weights=True)
        self.weights_holder.opacity = 1.0
        self._refresh_toggles()
        tl.push(gen, self.control)
        await tl.wait(gen, 1.2)

        shares = "  ".join(
            f"{item['name']} {item['weight'] * 100:.0f}%" for item in info["corners"]
        )
        await self._say(gen, f"It landed {info['dx']:.2f} of the way across and "
                             f"{info['dy']:.2f} of the way down, which gives: "
                             f"{shares}.", hold=5.0)

        await self._say(gen, f"Mix them in those proportions and you get RGB "
                             f"{info['blend']} — the swatch on line 4. It is a "
                             f"colour that appears nowhere in the original.",
                        hold=4.8)

        self._clear_result()
        tl.push(gen, self.result_card)
        size = self.trace.new_width
        for r in range(size):
            self._fill_result("bilinear", only=[(r, c) for c in range(size)])
            tl.push(gen, self.result_card)
            await tl.wait(gen, 0.08)

        self._refresh_compare()
        self.compare_card.opacity = 1.0
        tl.push(gen, self.control)
        await tl.wait(gen, 1.8)

        await self._say(gen, "Side by side: nearest keeps hard blocks, bilinear "
                             "fades between colours.", hold=3.4)

        if self.source_kind == "art":
            await self._say(gen, "And on this picture, nearest honestly looks "
                                 "better. Flat art has no in-between colours to "
                                 "find, so blending only smears clean edges.",
                            hold=5.0)

            quality = upscale_quality(render_space_scene(128), 4.0)
            await self._say(gen, f"On a real photograph it flips. Shrink one and "
                                 f"enlarge it back: nearest scores "
                                 f"{quality['nearest_psnr']:.2f} dB, bilinear "
                                 f"{quality['bilinear_psnr']:.2f} dB.", hold=5.2)

            await self._say(gen, "Switch the picture to Photo below and enlarge "
                                 "again — the smears become gradients, which is "
                                 "what a photograph actually contains.", hold=5.0)
        else:
            await self._say(gen, "On a shaded picture this is what you want: the "
                                 "blend continues the gradient, where nearest "
                                 "would break it into steps.", hold=5.0)

            await self._say(gen, "So neither method wins everywhere. Flat art "
                                 "wants nearest; photographs want bilinear.",
                            hold=4.4)

    # ---------------- 6 ----------------

    async def _scene_strip(self, gen):
        tl = self.timeline

        await self._say(gen, "Shrinking sounds easier. It is the dangerous "
                             "direction, so let's use a single row of pixels.",
                        self._step(5), hold=0.6)

        self.kept_holder.opacity = 0.0
        self.ideal_holder.opacity = 0.0
        self.blurred_holder.opacity = 0.0
        self._build_strip(show_samples=False)
        self.strip_card.opacity = 1.0
        tl.push(gen, self.control)
        await tl.wait(gen, 1.6)

        await self._say(gen, f"Twenty-four pixels, striped orange and teal, "
                             f"{self.stripe_width} pixels per stripe. We want it "
                             f"{self.factor} times shorter.", hold=4.0)

        self._build_strip(show_samples=True)
        tl.push(gen, self.strip_card)
        await self._say(gen, f"The simple way: keep every {_ordinal(self.factor)} "
                             f"pixel. Only the ringed ones are ever read. "
                             f"Everything faded is thrown away unseen.", hold=4.8)

        self.kept_holder.opacity = 1.0
        tl.push(gen, self.strip_card)
        await tl.wait(gen, 1.6)

        await self._say(gen, f"This one came out fine: still orange and teal, "
                             f"still striped, just shorter — off by "
                             f"{self.shrunk['kept_error']:.1f}. Shrinking is not "
                             f"broken by itself.", hold=5.0)

        # Now break it: finer stripes, a bigger jump.
        self.stripe_width = 2
        self.factor = 4
        self.strip = stripe_strip(24, self.stripe_width)
        self.shrunk = strip_shrink(self.strip, self.factor)
        self._build_strip(show_samples=True)
        self._refresh_toggles()
        tl.push(gen, self.control)

        await self._say(gen, "Now make the stripes finer — 2 pixels each — and "
                             "shrink harder, down to six pixels.", hold=4.6)

        kept_colours = {tuple(c) for c in self.shrunk["kept"]}
        if len(kept_colours) == 1:
            observation = (
                "Look what happened. Every ringed pixel landed on the same "
                "stripe, so the stripes have vanished completely. The small "
                "row claims the whole picture was one colour."
            )
        else:
            observation = (
                "The stripes came back at the wrong spacing: the sampling "
                "drifts in and out of step with them, so the small row shows "
                "a pattern the original never had."
            )
        await self._say(gen, observation, hold=5.2)

        self.ideal_holder.opacity = 1.0
        tl.push(gen, self.strip_card)
        await self._say(gen, "This is what it should have been. Six pixels cannot "
                             "show eight stripes, so the honest answer is the "
                             "average of each group — a muted blend.", hold=5.0)

        await self._say(gen, f"The naive shrink is off by "
                             f"{self.shrunk['kept_error']:.1f} from that target. "
                             f"Not blurry — wrong.", hold=4.0)

        self.blurred_holder.opacity = 1.0
        tl.push(gen, self.strip_card)
        await self._say(gen, "The fix: blur first. Averaging each neighbourhood "
                             "before picking removes the detail the short row could "
                             "never hold, so nothing is left to be misread.",
                        hold=5.0)

        await self._say(gen, self._strip_verdict(), hold=4.6)

        await self._say(gen, "Enlarging invents in-between colours. Shrinking "
                             "decides what to throw away, and throwing away "
                             "carelessly invents things that were never there.",
                        hold=4.6)

"""Discover · Lesson 3 — Noise, and the right cure.

Two kinds of damage, three filters, and the point that the filter has
to match the damage. Gaussian grain nudges every pixel a little;
salt-and-pepper replaces a few pixels completely, and that difference
decides whether you should average a neighbourhood or sort it.

Every image and number comes from NoiseTrace, which calls the project's
own noise generators and cleaning filters. The single-window scene is
checked against the real filter output at that pixel, so the arithmetic
on screen is the arithmetic that produced the cleaned image.

Chapters
    1  Two kinds of damage    grain vs specks, and what each did
    2  Averaging              the mean filter on the current damage
    3  One bad pixel          a 3x3 window, and the average it drags
    4  Sorting, not averaging the same window, lined up, middle picked
    5  The verdict            all six PSNR numbers, best of each row
"""

import flet as ft
import numpy as np

from algorithms.learning.noise_trace import (
    DEFAULT_AMOUNT,
    DEFAULT_SIGMA,
    DEFAULT_SIZE,
    FILTER_LABELS,
    FILTERS,
    GAUSSIAN,
    NOISE_LABELS,
    SALT_PEPPER,
    NoiseTrace,
)
from algorithms.learning.space_scene import render_space_scene
from ui.learning import palette
from ui.learning.scene_engine import Timeline
from ui.theme import AppAnimations, AppColors, AppLayout


SCENE_SIZE = 128
PANEL = 210

TILE = 34           # window tiles
TILE_GAP = 4
SORT_TILE = 26      # tiles in the sorted row

ORIGINAL_ACCENT = palette.INPUT
NOISY_ACCENT = palette.KERNEL
CLEAN_ACCENT = palette.PRODUCT
MEAN_ACCENT = "#F97316"
MEDIAN_ACCENT = "#34D399"

CHAPTERS = [
    "Two kinds of damage",
    "Averaging",
    "One bad pixel",
    "Sorting, not averaging",
    "The verdict",
]


def _mono(size, color):
    return dict(size=size, color=color, weight=ft.FontWeight.BOLD,
                font_family="Consolas")


class LearnNoiseView:
    def __init__(self, page):
        self.page = page

        self.scene = np.asarray(render_space_scene(SCENE_SIZE), dtype=np.uint8)

        self.noise_type = SALT_PEPPER
        self.sigma = DEFAULT_SIGMA
        self.amount = DEFAULT_AMOUNT
        self.kernel_size = DEFAULT_SIZE
        self.filter_name = "median"
        self.chapter = 0
        self.pixel = None

        self.timeline = Timeline(page, on_state_change=self._on_running_changed)
        self.trace = self._build_trace()

        self.control = self._build_page()
        self._apply_chapter_state(0, first_build=True)

    def _build_trace(self):
        return NoiseTrace(
            self.scene,
            noise_type=self.noise_type,
            sigma=self.sigma,
            amount=self.amount,
            kernel_size=self.kernel_size,
        )

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
                                    "DISCOVER  •  LESSON 3",
                                    size=9,
                                    weight=ft.FontWeight.BOLD,
                                    color=palette.KERNEL,
                                ),
                            ),
                            ft.Text(
                                "Noise, and the right cure",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),
                            ft.Text(
                                "Why a speck of salt breaks an average, "
                                "and sorting does not.",
                                size=11,
                                color=AppColors.TEXT_SECONDARY,
                            ),
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
                    self._panels_row(),
                    self._window_block(),
                    self._verdict_block(),
                ],
            ),
        )

        controls = ft.ResponsiveRow(
            spacing=14,
            run_spacing=14,
            controls=[
                ft.Container(col={"xs": 12, "lg": 4}, content=self._playback_panel()),
                ft.Container(col={"xs": 12, "lg": 4}, content=self._damage_panel()),
                ft.Container(col={"xs": 12, "lg": 4}, content=self._repair_panel()),
            ],
        )

        return ft.Column(spacing=16, controls=[header, stage, controls])

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
        self.caption_text = ft.Text("", size=15, weight=ft.FontWeight.W_600,
                                    color=AppColors.TEXT,
                                    text_align=ft.TextAlign.CENTER)
        self.caption = ft.Container(
            opacity=1.0,
            animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.caption_step, self.caption_text],
            ),
        )
        return self.caption

    # ---------------- image panels ----------------

    def _image_panel(self, label, accent, source):
        image = ft.Image(
            src=palette.png_bytes(source, scale=2),
            width=PANEL, height=PANEL,
            fit=ft.BoxFit.FILL,
            border_radius=12,
            gapless_playback=True,
        )
        psnr = ft.Text("—", **_mono(11, accent))
        caption = ft.Text(label, size=10, weight=ft.FontWeight.BOLD, color=accent)

        holder = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
            scale=1.0,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Container(
                        border_radius=14,
                        border=ft.Border.all(1.5, palette.argb("88", accent)),
                        shadow=ft.BoxShadow(blur_radius=24, spread_radius=-8,
                                            color=palette.argb("77", accent)),
                        content=image,
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            caption,
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=7, vertical=2),
                                border_radius=6,
                                bgcolor=palette.argb("1F", accent),
                                content=psnr,
                            ),
                        ],
                    ),
                ],
            ),
        )
        return holder, image, psnr, caption

    def _panels_row(self):
        (self.original_holder, self.original_image,
         self.original_psnr, _) = self._image_panel(
            "ORIGINAL", ORIGINAL_ACCENT, self.scene)
        (self.noisy_holder, self.noisy_image,
         self.noisy_psnr, self.noisy_caption) = self._image_panel(
            "NOISY", NOISY_ACCENT, self.trace.noisy)
        (self.clean_holder, self.clean_image,
         self.clean_psnr, self.clean_caption) = self._image_panel(
            "CLEANED", CLEAN_ACCENT, self.trace.cleaned["median"])

        self.original_psnr.value = "reference"

        return ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
            spacing=16,
            run_spacing=16,
            controls=[self.original_holder, self.noisy_holder, self.clean_holder],
        )

    # ---------------- the single-window stage ----------------

    def _window_block(self):
        self.window_grid = ft.Column(spacing=TILE_GAP,
                                     horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.window_tiles = []

        self.sorted_row = ft.Row(spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                                 wrap=True, run_spacing=4)
        self.sorted_tiles = []

        self.mean_box, self.mean_value = self._result_box("MEAN", MEAN_ACCENT)
        self.median_box, self.median_value = self._result_box("MEDIAN", MEDIAN_ACCENT)
        self.truth_box, self.truth_value = self._result_box(
            "TRUE VALUE", ORIGINAL_ACCENT)

        self.window_note = ft.Text("", size=10, color=AppColors.MUTED,
                                   text_align=ft.TextAlign.CENTER)

        self.window_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=16,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Text("ONE NEIGHBOURHOOD", size=9, weight=ft.FontWeight.BOLD,
                            color=palette.KERNEL_FRAME),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        wrap=True,
                        spacing=20,
                        run_spacing=12,
                        controls=[
                            self.window_grid,
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=8,
                                controls=[
                                    self.sorted_row,
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=10,
                                        controls=[self.mean_box, self.median_box,
                                                  self.truth_box],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    self.window_note,
                ],
            ),
        )
        return self.window_card

    def _result_box(self, label, accent):
        value = ft.Text("—", **_mono(17, accent))
        box = ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            border_radius=12,
            bgcolor=palette.argb("18", accent),
            border=ft.Border.all(1.2, palette.argb("77", accent)),
            opacity=0.25,
            scale=1.0,
            animate_opacity=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
                controls=[
                    ft.Text(label, size=8, weight=ft.FontWeight.BOLD, color=accent),
                    value,
                ],
            ),
        )
        return box, value

    def _rebuild_window_tiles(self, info):
        values = info["values"]
        size = values.shape[0]

        self.window_tiles = []
        rows = []

        for r in range(size):
            row = []
            for c in range(size):
                value = int(round(float(values[r, c])))
                extreme = value <= 0 or value >= 255

                tile = ft.Container(
                    width=TILE, height=TILE,
                    alignment=ft.Alignment.CENTER,
                    border_radius=6,
                    bgcolor=palette.pixel_color(value),
                    border=ft.Border.all(
                        1.5 if extreme else 1,
                        NOISY_ACCENT if extreme else "#00000000",
                    ),
                    opacity=0.0,
                    scale=1.0,
                    animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                    animate_scale=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
                    content=ft.Text(
                        str(value),
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color=palette.pixel_text_color(value),
                    ),
                )
                row.append(tile)
                self.window_tiles.append(tile)
            rows.append(ft.Row(spacing=TILE_GAP, tight=True, controls=row))

        self.window_grid.controls = rows

        self.sorted_tiles = []
        for value in info["sorted"]:
            value = int(round(float(value)))
            tile = ft.Container(
                width=SORT_TILE, height=SORT_TILE,
                alignment=ft.Alignment.CENTER,
                border_radius=5,
                bgcolor=palette.pixel_color(value),
                border=ft.Border.all(1, "#00000000"),
                opacity=0.0,
                scale=1.0,
                animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
                animate_scale=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
                content=ft.Text(
                    str(value), size=8, weight=ft.FontWeight.BOLD,
                    color=palette.pixel_text_color(value),
                ),
            )
            self.sorted_tiles.append(tile)

        self.sorted_row.controls = self.sorted_tiles

    # ---------------- verdict table ----------------

    def _verdict_block(self):
        self.verdict_rows = {}
        rows = [self._verdict_header()]

        for kind in (GAUSSIAN, SALT_PEPPER):
            cells = {
                "noisy": ft.Text("—", **_mono(12, NOISY_ACCENT)),
            }
            for name in FILTERS:
                cells[name] = ft.Text("—", **_mono(12, AppColors.TEXT))

            holders = {
                key: ft.Container(
                    width=96, height=34,
                    alignment=ft.Alignment.CENTER,
                    border_radius=8,
                    bgcolor=AppColors.SURFACE_3,
                    border=ft.Border.all(1, AppColors.BORDER_SOFT),
                    animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                    content=text,
                )
                for key, text in cells.items()
            }

            self.verdict_rows[kind] = (cells, holders)

            rows.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Container(
                            width=120,
                            content=ft.Text(NOISE_LABELS[kind], size=11,
                                            weight=ft.FontWeight.BOLD,
                                            color=AppColors.TEXT),
                        ),
                        holders["noisy"],
                        *[holders[name] for name in FILTERS],
                    ],
                )
            )

        self.verdict_note = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY,
                                    text_align=ft.TextAlign.CENTER)

        self.verdict_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=16,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Text("PSNR — HIGHER IS BETTER", size=9,
                            weight=ft.FontWeight.BOLD, color=CLEAN_ACCENT),
                    *rows,
                    self.verdict_note,
                ],
            ),
        )
        return self.verdict_card

    def _verdict_header(self):
        def head(text):
            return ft.Container(
                width=96,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(text, size=9, weight=ft.FontWeight.BOLD,
                                color=AppColors.MUTED),
            )

        return ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Container(width=120),
                head("NOISY"),
                *[head(FILTER_LABELS[name].upper()) for name in FILTERS],
            ],
        )

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
                            min=0.5, max=3.0, divisions=10, value=1.0,
                            active_color=palette.KERNEL,
                            on_change=self._on_speed,
                        )),
                        self.speed_label,
                    ],
                ),
            ],
        )
        return self._panel("PLAYBACK", "Play, pause, or jump to a chapter.",
                           ft.Icons.SMART_DISPLAY_OUTLINED, palette.KERNEL, body)

    def _damage_panel(self):
        self.type_buttons = {
            GAUSSIAN: self._small_button(
                "Gaussian grain", ft.Icons.GRAIN,
                lambda e: self.set_noise_type(GAUSSIAN)),
            SALT_PEPPER: self._small_button(
                "Salt & pepper", ft.Icons.SCATTER_PLOT,
                lambda e: self.set_noise_type(SALT_PEPPER)),
        }

        self.strength_text = ft.Text("", **_mono(11, NOISY_ACCENT))
        self.strength_slider = ft.Slider(
            min=1, max=20, divisions=19, value=6,
            active_color=NOISY_ACCENT,
            on_change=lambda e: self.set_strength(e.control.value),
        )

        self.size_buttons = {
            size: self._small_button(
                f"{size}×{size}", ft.Icons.GRID_ON,
                lambda e, s=size: self.set_kernel_size(s))
            for size in (3, 5, 7)
        }

        body = ft.Column(
            spacing=10,
            controls=[
                ft.Row(spacing=8, controls=list(self.type_buttons.values())),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Strength", size=10, color=AppColors.MUTED),
                                self.strength_text,
                            ],
                        ),
                        self.strength_slider,
                    ],
                ),
                ft.Text("Filter size", size=10, color=AppColors.MUTED),
                ft.Row(spacing=8, controls=list(self.size_buttons.values())),
            ],
        )
        return self._panel("THE DAMAGE", "Pick the noise and how bad it is.",
                           ft.Icons.BLUR_ON, NOISY_ACCENT, body)

    def _repair_panel(self):
        self.filter_buttons = {
            name: self._small_button(
                FILTER_LABELS[name], ft.Icons.FILTER_ALT,
                lambda e, n=name: self.set_filter(n))
            for name in FILTERS
        }

        self.repair_note = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)

        body = ft.Column(
            spacing=10,
            controls=[
                ft.Row(spacing=8, controls=list(self.filter_buttons.values())),
                self._small_button("Another neighbourhood", ft.Icons.CENTER_FOCUS_STRONG,
                                   lambda e: self.pick_window()),
                self.repair_note,
            ],
        )
        return self._panel("THE CURE", "Three filters, judged by PSNR.",
                           ft.Icons.HEALING, CLEAN_ACCENT, body)

    # =========================================================
    # STATE
    # =========================================================

    def _apply_chapter_state(self, chapter, first_build=False):
        self.chapter = chapter

        self.original_holder.opacity = 1.0
        self.noisy_holder.opacity = 1.0 if chapter >= 0 else 0.0
        self.clean_holder.opacity = 1.0 if chapter >= 1 else 0.0

        self.window_card.opacity = 1.0 if chapter >= 2 else 0.0
        self.verdict_card.opacity = 1.0 if chapter >= 4 else 0.0

        self._refresh_noisy()
        self._refresh_clean()
        self._refresh_strength_label()
        self._refresh_toggles()

        if chapter >= 2:
            self._prepare_window(reveal=True, sorted_visible=chapter >= 3)
        if chapter >= 4:
            self._fill_verdict()

        step, text = self._resting_caption(chapter)
        self.caption_step.value = step
        self.caption_text.value = text

        self._refresh_chapter_pills()

        if not first_build:
            self._safe_update(self.control)

    def _resting_caption(self, chapter):
        step = f"CHAPTER {chapter + 1}  ·  {CHAPTERS[chapter].upper()}"
        if chapter == 0:
            return step, "Press Play to see what noise does, and what cures it."
        return step, "Press Play to continue, or try the controls yourself."

    def _refresh_noisy(self):
        self.noisy_image.src = palette.png_bytes(self.trace.noisy, scale=2)
        self.noisy_psnr.value = f"{self.trace.noisy_psnr:.2f} dB"
        self.noisy_caption.value = NOISE_LABELS[self.noise_type].upper()

    def _refresh_clean(self):
        name = self.filter_name
        self.clean_image.src = palette.png_bytes(self.trace.cleaned[name], scale=2)
        self.clean_psnr.value = f"{self.trace.psnr[name]:.2f} dB"
        self.clean_caption.value = f"{FILTER_LABELS[name].upper()} {self.kernel_size}×{self.kernel_size}"

        gain = self.trace.psnr[name] - self.trace.noisy_psnr
        self.repair_note.value = (
            f"{FILTER_LABELS[name]} {self.kernel_size}×{self.kernel_size} on "
            f"{NOISE_LABELS[self.noise_type].lower()}: {gain:+.2f} dB."
        )

    def _refresh_strength_label(self):
        if self.noise_type == GAUSSIAN:
            self.strength_text.value = f"σ {self.sigma:.0f}"
        else:
            self.strength_text.value = f"{self.amount * 100:.0f}% of pixels"

    def _refresh_toggles(self):
        for kind, button in self.type_buttons.items():
            active = kind == self.noise_type
            button.border = ft.Border.all(
                1, NOISY_ACCENT if active else AppColors.BORDER_SOFT)
            button.bgcolor = (palette.argb("22", NOISY_ACCENT) if active
                              else AppColors.SURFACE_DARK)

        for size, button in self.size_buttons.items():
            active = size == self.kernel_size
            button.border = ft.Border.all(
                1, palette.KERNEL_FRAME if active else AppColors.BORDER_SOFT)
            button.bgcolor = (palette.argb("22", palette.KERNEL_FRAME) if active
                              else AppColors.SURFACE_DARK)

        for name, button in self.filter_buttons.items():
            active = name == self.filter_name
            button.border = ft.Border.all(
                1, CLEAN_ACCENT if active else AppColors.BORDER_SOFT)
            button.bgcolor = (palette.argb("22", CLEAN_ACCENT) if active
                              else AppColors.SURFACE_DARK)

    def _prepare_window(self, reveal=False, sorted_visible=False):
        if self.pixel is None:
            self.pixel = self.trace.dramatic_window()

        try:
            info = self.trace.window(*self.pixel)
        except (IndexError, AssertionError):
            self.pixel = self.trace.dramatic_window()
            info = self.trace.window(*self.pixel)

        self.window_info = info
        self._rebuild_window_tiles(info)

        opacity = 1.0 if reveal else 0.0
        for tile in self.window_tiles:
            tile.opacity = opacity
        for tile in self.sorted_tiles:
            tile.opacity = 1.0 if sorted_visible else 0.0

        self.mean_value.value = str(info["mean_shown"])
        self.median_value.value = str(info["median_shown"])
        self.truth_value.value = str(info["true_value"])

        self.mean_box.opacity = 1.0 if reveal else 0.25
        self.median_box.opacity = 1.0 if sorted_visible else 0.25
        self.truth_box.opacity = 1.0 if reveal else 0.25

        self.window_note.value = (
            f"Pixel ({info['row']}, {info['col']})  ·  "
            f"{info['extremes']} of {info['values'].size} neighbours are "
            f"pure black or pure white"
        )

        if sorted_visible:
            self._highlight_median()

    def _highlight_median(self):
        middle = len(self.sorted_tiles) // 2
        for index, tile in enumerate(self.sorted_tiles):
            chosen = index == middle
            tile.border = ft.Border.all(
                2 if chosen else 1,
                MEDIAN_ACCENT if chosen else "#00000000",
            )
            tile.scale = 1.15 if chosen else 1.0

    def _fill_verdict(self):
        table = self.trace.comparison_table()

        for kind, (cells, holders) in self.verdict_rows.items():
            data = table[kind]
            cells["noisy"].value = f"{data['noisy']:.2f}"

            for name in FILTERS:
                score = data["scores"][name]
                cells[name].value = f"{score:.2f}"
                best = name == data["best"]
                holders[name].bgcolor = (palette.argb("26", CLEAN_ACCENT) if best
                                         else AppColors.SURFACE_3)
                holders[name].border = ft.Border.all(
                    1.5 if best else 1,
                    CLEAN_ACCENT if best else AppColors.BORDER_SOFT)
                cells[name].color = CLEAN_ACCENT if best else AppColors.TEXT

        salt = table[SALT_PEPPER]["scores"]
        grain = table[GAUSSIAN]["scores"]
        self.verdict_note.value = (
            f"On specks, sorting beats averaging by "
            f"{salt['median'] - salt['mean']:+.2f} dB. On grain the gap is only "
            f"{grain['median'] - grain['mean']:+.2f} dB, and the weighted average "
            f"beats the flat one by {grain['gaussian'] - grain['mean']:+.2f} dB."
        )

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

    def set_noise_type(self, kind):
        self.timeline.cancel()
        self.noise_type = kind
        self.strength_slider.value = 6 if kind == SALT_PEPPER else 12
        self._on_strength_value(self.strength_slider.value)
        self._rebuild_after_change(
            f"{NOISE_LABELS[kind]} it is. Play again, or compare the filters."
        )

    def set_strength(self, value):
        self.timeline.cancel()
        self._on_strength_value(value)
        self._rebuild_after_change("New damage. The right cure may have changed.")

    def _on_strength_value(self, value):
        value = float(value)
        if self.noise_type == GAUSSIAN:
            self.sigma = max(2.0, value * 2.5)
        else:
            self.amount = max(0.005, value / 100.0)

    def set_kernel_size(self, size):
        self.timeline.cancel()
        self.kernel_size = size
        self._rebuild_after_change(
            f"{size}×{size} window: more neighbours to average, or to sort."
        )

    def set_filter(self, name):
        self.timeline.cancel()
        self.filter_name = name
        self._refresh_clean()
        self._refresh_toggles()
        self.caption_text.value = (
            f"{FILTER_LABELS[name]} filter: "
            f"{self.trace.psnr[name]:.2f} dB against "
            f"{self.trace.noisy_psnr:.2f} dB noisy."
        )
        self._safe_update(self.control)

    def pick_window(self):
        """Move to another neighbourhood worth looking at."""
        self.timeline.cancel()

        height, width = self.scene.shape
        pad = self.trace.pad
        rng = np.random.default_rng()

        best = None
        best_score = -1.0

        # Sample a few candidates and keep the one where mean and median
        # disagree most: that is where the lesson's point lives.
        for _ in range(60):
            row = int(rng.integers(pad, height - pad))
            col = int(rng.integers(pad, width - pad))
            info = self.trace.window(row, col)
            score = abs(info["mean"] - info["median"])
            if score > best_score:
                best, best_score = (row, col), score

        self.pixel = best
        self._prepare_window(reveal=True, sorted_visible=self.chapter >= 3)
        self.window_card.opacity = 1.0
        self._safe_update(self.control)

    def _rebuild_after_change(self, message):
        try:
            self.trace = self._build_trace()
        except ValueError:
            return

        self.pixel = None
        self._refresh_noisy()
        self._refresh_clean()
        self._refresh_strength_label()
        self._refresh_toggles()

        if self.chapter >= 2:
            self._prepare_window(reveal=True, sorted_visible=self.chapter >= 3)
        if self.chapter >= 4:
            self._fill_verdict()

        self.caption_text.value = message
        self._safe_update(self.control)

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
        await tl.wait(gen, 0.2)
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
            self._scene_damage,
            self._scene_average,
            self._scene_window,
            self._scene_sort,
            self._scene_verdict,
        ]
        for index in range(chapter, len(scenes)):
            self._enter_chapter(index)
            await scenes[index](gen)
            self.timeline.check(gen)

    # ---------------- 1. two kinds of damage ----------------

    async def _scene_damage(self, gen):
        tl = self.timeline

        self.clean_holder.opacity = 0.0
        self.window_card.opacity = 0.0
        self.verdict_card.opacity = 0.0
        tl.push(gen, self.control)

        await self._say(gen, "Noise is not one thing. There are two very different "
                             "kinds, and they need different cures.",
                        self._step(0), hold=2.2)

        # Show whichever kind is selected, then the other, then settle back.
        first = self.noise_type
        second = GAUSSIAN if first == SALT_PEPPER else SALT_PEPPER

        for kind in (first, second, first):
            self.noise_type = kind
            self.trace = self._build_trace()
            self.pixel = None
            self._refresh_noisy()
            self._refresh_clean()
            self._refresh_strength_label()
            self._refresh_toggles()
            damage = self.trace.damaged_pixels()

            if kind == GAUSSIAN:
                text = (
                    f"Gaussian grain nudges almost every pixel a little: "
                    f"{damage['changed']:,} of {damage['total']:,} pixels moved, "
                    f"by {damage['mean_shift']:.1f} levels on average."
                )
            else:
                text = (
                    f"Salt and pepper is different: only "
                    f"{damage['changed']:,} pixels changed, but "
                    f"{damage['heavily_changed']:,} of them were replaced outright "
                    f"by pure black or pure white."
                )

            tl.push(gen, self.control)
            await self._say(gen, text, hold=3.0)

    # ---------------- 2. averaging ----------------

    async def _scene_average(self, gen):
        tl = self.timeline

        await self._say(gen, "The obvious cure: replace every pixel with the average "
                             "of its neighbours.", self._step(1), hold=0.3)

        self.filter_name = "mean"
        self._refresh_clean()
        self._refresh_toggles()
        self.clean_holder.opacity = 1.0
        self.clean_holder.scale = 1.04
        tl.push(gen, self.control)
        await tl.wait(gen, 0.5)
        self.clean_holder.scale = 1.0
        tl.push(gen, self.clean_holder)
        await tl.wait(gen, 1.6)

        mean_psnr = self.trace.psnr["mean"]
        gain = mean_psnr - self.trace.noisy_psnr

        if self.noise_type == GAUSSIAN:
            text = (f"On grain it works: {self.trace.noisy_psnr:.2f} dB becomes "
                    f"{mean_psnr:.2f} dB, a gain of {gain:.2f} dB.")
        else:
            text = (f"On specks it is far less convincing: "
                    f"{self.trace.noisy_psnr:.2f} dB becomes only "
                    f"{mean_psnr:.2f} dB, and every speck has been smeared into "
                    f"a grey smudge.")

        await self._say(gen, text, hold=3.0)

    # ---------------- 3. one bad pixel ----------------

    async def _scene_window(self, gen):
        tl = self.timeline

        await self._say(gen, "To see why, zoom into a single neighbourhood.",
                        self._step(2), hold=0.3)

        self._prepare_window(reveal=False, sorted_visible=False)
        self.window_card.opacity = 1.0
        tl.push(gen, self.control)
        await tl.wait(gen, 0.4)

        for tile in self.window_tiles:
            tile.opacity = 1.0
            tl.push(gen, self.window_card)
            await tl.wait(gen, 0.05)

        info = self.window_info
        await tl.wait(gen, 0.6)

        if info["extremes"]:
            await self._say(gen, f"{info['extremes']} of these "
                                 f"{info['values'].size} neighbours are not real "
                                 f"measurements at all: the noise replaced them with "
                                 f"pure black or pure white.", hold=3.0)
        else:
            await self._say(gen, "Every neighbour here is a real measurement, just "
                                 "shifted a little by the grain.", hold=2.6)

        await self._say(gen, "Add them up, divide by the count.", hold=0.3)
        self.mean_box.opacity = 1.0
        self.mean_box.scale = 1.12
        tl.push(gen, self.window_card)
        await tl.wait(gen, 0.4)
        self.mean_box.scale = 1.0
        self.truth_box.opacity = 1.0
        tl.push(gen, self.window_card)
        await tl.wait(gen, 1.4)

        error = abs(info["mean_shown"] - info["true_value"])
        await self._say(gen, f"The average says {info['mean_shown']}. The pixel's true "
                             f"value is {info['true_value']} — out by {error}. "
                             f"A single extreme neighbour drags the whole average "
                             f"with it.", hold=3.4)

    # ---------------- 4. sorting, not averaging ----------------

    async def _scene_sort(self, gen):
        tl = self.timeline
        info = self.window_info

        await self._say(gen, "So don't average them. Line them up in order instead.",
                        self._step(3), hold=0.3)

        for tile in self.sorted_tiles:
            tile.opacity = 1.0
            tl.push(gen, self.window_card)
            await tl.wait(gen, 0.06)
        await tl.wait(gen, 0.8)

        await self._say(gen, "The extremes end up at the two ends, where they can do "
                             "no harm. Take whatever sits in the middle.", hold=0.4)

        self._highlight_median()
        self.median_box.opacity = 1.0
        self.median_box.scale = 1.14
        tl.push(gen, self.window_card)
        await tl.wait(gen, 0.5)
        self.median_box.scale = 1.0
        tl.push(gen, self.window_card)
        await tl.wait(gen, 1.2)

        median_error = abs(info["median_shown"] - info["true_value"])
        mean_error = abs(info["mean_shown"] - info["true_value"])

        await self._say(gen, f"The median says {info['median_shown']}, against a true "
                             f"{info['true_value']} — out by {median_error}, where the "
                             f"average was out by {mean_error}.", hold=3.0)

        self.filter_name = "median"
        self._refresh_clean()
        self._refresh_toggles()
        tl.push(gen, self.control)

        await self._say(gen, f"Do that for every pixel and the whole picture comes "
                             f"back: {self.trace.psnr['median']:.2f} dB, against "
                             f"{self.trace.psnr['mean']:.2f} dB for the average.",
                        hold=3.0)

    # ---------------- 5. the verdict ----------------

    async def _scene_verdict(self, gen):
        tl = self.timeline

        await self._say(gen, "Both kinds of noise, all three filters, same picture.",
                        self._step(4), hold=0.3)

        self._fill_verdict()
        self.verdict_card.opacity = 1.0
        tl.push(gen, self.control)
        await tl.wait(gen, 2.6)

        table = self.trace.comparison_table()
        salt = table[SALT_PEPPER]["scores"]
        grain = table[GAUSSIAN]["scores"]

        await self._say(gen, f"On salt and pepper it is not close: sorting beats "
                             f"averaging by {salt['median'] - salt['mean']:.2f} dB.",
                        hold=3.0)

        await self._say(gen, f"On grain the three are much closer, and the weighted "
                             f"Gaussian average beats the flat one by "
                             f"{grain['gaussian'] - grain['mean']:.2f} dB, because "
                             f"near neighbours deserve more say than far ones.",
                        hold=3.4)

        await self._say(gen, "That is the whole lesson: look at the damage first, "
                             "then pick the filter. Change the noise below and see "
                             "which cure wins.", hold=3.0)

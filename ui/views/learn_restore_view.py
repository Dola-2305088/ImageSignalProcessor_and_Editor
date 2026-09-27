"""Discover · Lesson 2 — Blur it, then take it back.

Motion blur and its undoing, animated. The lesson degrades one fixed
space scene (camera shake, then sensor noise), shows what that did in
the frequency domain, then restores it twice: the naive inverse, which
collapses, and Wiener, which survives.

Every image and every number comes from RestorationTrace, which in
turn calls the project's own motion blur, inverse filter, Wiener filter
and PSNR. The view only arranges and animates them.

Chapters
    1  The camera moved        kernel slides in, blurred result appears
    2  Noise creeps in         sensor noise added on top of the blur
    3  What the blur erased    |H| spectrum, and the frequencies lost
    4  The naive inverse       divide by H, and watch it explode
    5  Wiener's compromise     K sweeps, PSNR follows, best K wins
"""

import flet as ft
import numpy as np

from algorithms.learning.restoration_trace import (
    DEFAULT_ANGLE,
    DEFAULT_K,
    DEFAULT_LENGTH,
    DEFAULT_NOISE,
    K_SWEEP,
    RestorationTrace,
)
from algorithms.learning.space_scene import render_space_scene
from ui.learning import palette
from ui.learning.scene_engine import Cancelled, Timeline
from ui.theme import AppAnimations, AppColors, AppLayout


SCENE_SIZE = 128
PANEL = 232          # displayed size of the three image panels
SPECTRUM = 150       # displayed size of the spectrum panels

CHAPTERS = [
    "The camera moved",
    "Noise creeps in",
    "What the blur erased",
    "The naive inverse",
    "Wiener's compromise",
]

ORIGINAL_ACCENT = palette.INPUT
DEGRADED_ACCENT = palette.KERNEL
RESTORED_ACCENT = palette.PRODUCT


def _mono(size, color):
    return dict(size=size, color=color, weight=ft.FontWeight.BOLD,
                font_family="Consolas")


class LearnRestoreView:
    def __init__(self, page):
        self.page = page

        self.scene = np.asarray(render_space_scene(SCENE_SIZE), dtype=np.uint8)

        self.length = DEFAULT_LENGTH
        self.angle = DEFAULT_ANGLE
        self.noise = DEFAULT_NOISE
        self.k = DEFAULT_K
        self.chapter = 0
        self.method = "wiener"

        self.timeline = Timeline(page, on_state_change=self._on_running_changed)
        self.trace = RestorationTrace(self.scene, self.length, self.angle, self.noise)

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
                                content=ft.Text(
                                    "DISCOVER  •  LESSON 2",
                                    size=9,
                                    weight=ft.FontWeight.BOLD,
                                    color=palette.KERNEL,
                                ),
                            ),
                            ft.Text(
                                "Blur it, then take it back",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),
                            ft.Text(
                                "Motion blur, and why Wiener deconvolution "
                                "survives noise when a plain inverse does not.",
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
                    self._analysis_row(),
                ],
            ),
        )

        controls = ft.ResponsiveRow(
            spacing=14,
            run_spacing=14,
            controls=[
                ft.Container(col={"xs": 12, "lg": 4}, content=self._playback_panel()),
                ft.Container(col={"xs": 12, "lg": 4}, content=self._degrade_panel()),
                ft.Container(col={"xs": 12, "lg": 4}, content=self._restore_panel()),
            ],
        )

        return ft.Column(
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[header, stage, controls],
        )

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
                tight=True,
                spacing=8,
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

    def _image_panel(self, label, accent, source, size=PANEL):
        image = ft.Image(
            src=palette.png_bytes(source, scale=2),
            width=size,
            height=size,
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
                        shadow=ft.BoxShadow(blur_radius=26, spread_radius=-8,
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
        (self.degraded_holder, self.degraded_image,
         self.degraded_psnr, self.degraded_caption) = self._image_panel(
            "BLURRED", DEGRADED_ACCENT, self.trace.degraded)
        (self.restored_holder, self.restored_image,
         self.restored_psnr, self.restored_caption) = self._image_panel(
            "RESTORED", RESTORED_ACCENT, self.trace.inverse)

        self.original_psnr.value = "reference"

        self.arrow_one = self._arrow("blur + noise")
        self.arrow_two = self._arrow("restore")

        return ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
            spacing=14,
            run_spacing=14,
            controls=[
                self.original_holder,
                self.arrow_one,
                self.degraded_holder,
                self.arrow_two,
                self.restored_holder,
            ],
        )

    def _arrow(self, label):
        return ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=26,
                            color=palette.KERNEL),
                    ft.Text(label, size=9, color=AppColors.MUTED),
                ],
            ),
        )

    # ---------------- spectra, kernel and formula ----------------

    def _analysis_row(self):
        self.kernel_image = ft.Image(
            src=palette.png_bytes(self.trace.kernel_spectrum, scale=1),
            width=SPECTRUM, height=SPECTRUM, fit=ft.BoxFit.FILL,
            filter_quality=ft.FilterQuality.NONE,
            border_radius=10, gapless_playback=True,
        )
        self.kernel_note = ft.Text("", size=9, color=AppColors.MUTED)
        self.kernel_card = self._analysis_card(
            "BLUR KERNEL", self.kernel_image, self.kernel_note, palette.KERNEL_FRAME)

        self.spectrum_image_control = ft.Image(
            src=palette.png_bytes(self.trace.kernel_spectrum, scale=1),
            width=SPECTRUM, height=SPECTRUM, fit=ft.BoxFit.FILL,
            border_radius=10, gapless_playback=True,
        )
        self.spectrum_note = ft.Text("", size=9, color=AppColors.MUTED)
        self.spectrum_card = self._analysis_card(
            "WHAT THE BLUR KEEPS  |H|", self.spectrum_image_control,
            self.spectrum_note, palette.INPUT)

        self.formula = ft.Text("F̂  =  ( H* / ( |H|² + K ) ) · G",
                               **_mono(15, RESTORED_ACCENT))
        self.formula_note = ft.Text(
            "K is the only knob: it stops the division from exploding.",
            size=10, color=AppColors.TEXT_SECONDARY,
        )
        self.sweep_bars = ft.Row(spacing=4, alignment=ft.MainAxisAlignment.CENTER,
                                 vertical_alignment=ft.CrossAxisAlignment.END)
        self._build_sweep_bars()

        self.formula_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=16,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, palette.argb("55", RESTORED_ACCENT)),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Text("WIENER FILTER", size=10, weight=ft.FontWeight.BOLD,
                            color=RESTORED_ACCENT),
                    self.formula,
                    self.formula_note,
                    ft.Container(height=2),
                    ft.Text("PSNR ACROSS K", size=9, color=AppColors.MUTED),
                    ft.Container(height=64, content=self.sweep_bars),
                ],
            ),
        )

        return ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            wrap=True,
            spacing=14,
            run_spacing=14,
            controls=[self.kernel_card, self.spectrum_card, self.formula_card],
        )

    def _analysis_card(self, title, image, note, accent):
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
                    ft.Text(title, size=9, weight=ft.FontWeight.BOLD, color=accent),
                    image,
                    note,
                ],
            ),
        )

    def _build_sweep_bars(self):
        self.bars = []
        for k in K_SWEEP:
            bar = ft.Container(
                width=14,
                height=6,
                border_radius=3,
                bgcolor=palette.argb("55", RESTORED_ACCENT),
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                tooltip=f"K = {k}",
            )
            self.bars.append(bar)

        self.sweep_bars.controls = [
            ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.END,
                spacing=3,
                controls=[bar],
            )
            for bar in self.bars
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

    def _slider_row(self, label, value_text, slider):
        return ft.Column(
            spacing=2,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(label, size=10, color=AppColors.MUTED),
                        value_text,
                    ],
                ),
                slider,
            ],
        )

    def _degrade_panel(self):
        self.length_text = ft.Text(f"{self.length} px", **_mono(11, DEGRADED_ACCENT))
        self.angle_text = ft.Text(f"{int(self.angle)}°", **_mono(11, DEGRADED_ACCENT))
        self.noise_text = ft.Text(f"σ {self.noise:.0f}", **_mono(11, DEGRADED_ACCENT))

        body = ft.Column(
            spacing=10,
            controls=[
                self._slider_row(
                    "Shake length", self.length_text,
                    ft.Slider(min=7, max=31, divisions=12, value=self.length,
                              active_color=DEGRADED_ACCENT,
                              on_change=lambda e: self._on_degrade("length", e.control.value)),
                ),
                self._slider_row(
                    "Shake angle", self.angle_text,
                    ft.Slider(min=0, max=180, divisions=12, value=self.angle,
                              active_color=DEGRADED_ACCENT,
                              on_change=lambda e: self._on_degrade("angle", e.control.value)),
                ),
                self._slider_row(
                    "Sensor noise", self.noise_text,
                    ft.Slider(min=0, max=16, divisions=8, value=self.noise,
                              active_color=DEGRADED_ACCENT,
                              on_change=lambda e: self._on_degrade("noise", e.control.value)),
                ),
                ft.Text(
                    "The kernel used to restore is exactly the kernel used "
                    "to blur — that is what makes this solvable.",
                    size=10, color=AppColors.MUTED,
                ),
            ],
        )
        return self._panel("THE DAMAGE", "Shape the blur and the noise.",
                           ft.Icons.MOTION_PHOTOS_ON, DEGRADED_ACCENT, body)

    def _restore_panel(self):
        self.k_text = ft.Text(f"K = {self.k}", **_mono(11, RESTORED_ACCENT))
        self.k_slider = ft.Slider(
            min=0, max=len(K_SWEEP) - 1, divisions=len(K_SWEEP) - 1,
            value=K_SWEEP.index(DEFAULT_K) if DEFAULT_K in K_SWEEP else 5,
            active_color=RESTORED_ACCENT,
            on_change=lambda e: self._on_k(int(round(e.control.value))),
        )

        self.method_note = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)

        body = ft.Column(
            spacing=10,
            controls=[
                self._slider_row("Wiener K", self.k_text, self.k_slider),
                ft.Row(
                    spacing=8,
                    controls=[
                        self._small_button("Naive inverse", ft.Icons.CALL_SPLIT,
                                           lambda e: self.show_method("inverse")),
                        self._small_button("Wiener", ft.Icons.AUTO_FIX_HIGH,
                                           lambda e: self.show_method("wiener")),
                    ],
                ),
                self._small_button("Find the best K", ft.Icons.INSIGHTS,
                                   lambda e: self.find_best_k()),
                self.method_note,
            ],
        )
        return self._panel("THE REPAIR", "Restore, and judge it by PSNR.",
                           ft.Icons.HEALING, RESTORED_ACCENT, body)

    # =========================================================
    # STATE
    # =========================================================

    def _apply_chapter_state(self, chapter, first_build=False):
        self.chapter = chapter

        self.original_holder.opacity = 1.0
        self.original_image.src = palette.png_bytes(self.scene, scale=2)

        show_degraded = chapter >= 1
        self.arrow_one.opacity = 1.0 if show_degraded else 0.0
        self.degraded_holder.opacity = 1.0 if show_degraded else 0.0
        self._refresh_degraded(noise=chapter >= 2)

        show_analysis = chapter >= 2
        self.kernel_card.opacity = 1.0 if chapter >= 1 else 0.0
        self.spectrum_card.opacity = 1.0 if show_analysis else 0.0
        self.formula_card.opacity = 1.0 if chapter >= 4 else 0.0

        show_restored = chapter >= 3
        self.arrow_two.opacity = 1.0 if show_restored else 0.0
        self.restored_holder.opacity = 1.0 if show_restored else 0.0

        if chapter >= 4:
            self.show_method("wiener", update=False)
        elif chapter == 3:
            self.show_method("inverse", update=False)

        self._refresh_kernel_card()
        self._refresh_spectrum_card()
        self._refresh_bars()

        step, text = self._resting_caption(chapter)
        self.caption_step.value = step
        self.caption_text.value = text

        self._refresh_chapter_pills()

        if not first_build:
            self._safe_update(self.control)

    def _resting_caption(self, chapter):
        step = f"CHAPTER {chapter + 1}  ·  {CHAPTERS[chapter].upper()}"
        if chapter == 0:
            return step, "Press Play to blur this image and then win it back."
        return step, "Press Play to continue, or move the sliders yourself."

    def _refresh_degraded(self, noise=True):
        image = self.trace.degraded if noise else self.trace.blurred
        psnr = self.trace.degraded_psnr if noise else self.trace.blurred_psnr

        self.degraded_image.src = palette.png_bytes(image, scale=2)
        self.degraded_psnr.value = f"{psnr:.2f} dB"
        self.degraded_caption.value = "BLURRED + NOISE" if noise else "BLURRED"

    def _refresh_kernel_card(self):
        kernel = self.trace.kernel
        top = kernel.max() or 1.0
        picture = np.clip(np.round(kernel / top * 255.0), 0, 255).astype(np.uint8)

        self.kernel_image.src = palette.png_bytes(picture, scale=8)
        self.kernel_note.value = (
            f"{self.trace.kernel_size}×{self.trace.kernel_size} line  ·  "
            f"{self.length} px at {int(self.angle)}°  ·  sums to 1"
        )

    def _refresh_spectrum_card(self):
        self.spectrum_image_control.src = palette.png_bytes(
            self.trace.kernel_spectrum, scale=2
        )
        self.spectrum_note.value = (
            f"dark bands = frequencies erased  ·  "
            f"{self.trace.null_fraction * 100:.0f}% almost gone"
        )

    def _refresh_bars(self, active=None):
        results, (best_k, best_psnr) = self.trace.sweep()
        values = [psnr for _, psnr in results]

        low = min(values)
        span = max(1e-6, max(values) - low)

        for bar, (k, psnr) in zip(self.bars, results):
            bar.height = 6 + 52 * (psnr - low) / span
            if active is not None and abs(k - active) < 1e-9:
                bar.bgcolor = "#FFFFFF"
            elif abs(k - best_k) < 1e-9:
                bar.bgcolor = RESTORED_ACCENT
            else:
                bar.bgcolor = palette.argb("55", RESTORED_ACCENT)

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

    def show_method(self, method, update=True):
        """Swap the restored panel between the two restorations."""
        self.method = method

        if method == "inverse":
            self.restored_image.src = palette.png_bytes(self.trace.inverse, scale=2)
            self.restored_psnr.value = f"{self.trace.inverse_psnr:.2f} dB"
            self.restored_caption.value = "NAIVE INVERSE"
            self.method_note.value = (
                "Naive inverse divides by H everywhere, including the "
                "frequencies the blur nearly erased."
            )
        else:
            image, psnr = self.trace.wiener(self.k)
            self.restored_image.src = palette.png_bytes(image, scale=2)
            self.restored_psnr.value = f"{psnr:.2f} dB"
            self.restored_caption.value = "WIENER RESTORED"
            self.method_note.value = (
                f"Wiener at K = {self.k}: "
                f"{psnr - self.trace.degraded_psnr:+.2f} dB against the "
                "blurred input."
            )

        if update:
            self.restored_holder.opacity = 1.0
            self.arrow_two.opacity = 1.0
            self._safe_update(self.control)

    def find_best_k(self):
        self.timeline.cancel()
        best_k, best_psnr = self.trace.best_k()
        self.k = best_k
        self.k_slider.value = K_SWEEP.index(best_k)
        self.k_text.value = f"K = {best_k}"
        self.show_method("wiener", update=False)
        self._refresh_bars(active=best_k)
        self.caption_text.value = self._verdict(best_k, best_psnr)
        self._safe_update(self.control)

    def _verdict(self, best_k, best_psnr):
        """Say what the numbers actually show, win or lose."""
        gain = best_psnr - self.trace.degraded_psnr

        if gain > 0:
            return (
                f"Best of the tested values: K = {best_k}, at {best_psnr:.2f} dB — "
                f"{gain:+.2f} dB against the damaged photo."
            )

        return (
            f"Best K = {best_k} reaches {best_psnr:.2f} dB, still {gain:.2f} dB "
            "below the damaged photo: this blur is too mild to be worth undoing "
            "at this noise level. Lengthen the shake and try again."
        )

    def _on_speed(self, e):
        self.timeline.speed = float(e.control.value)
        self.speed_label.value = f"{self.timeline.speed:.2f}".rstrip("0").rstrip(".") + "×"
        self._safe_update(self.speed_label)

    def _on_k(self, index):
        self.timeline.cancel()
        self.k = K_SWEEP[max(0, min(len(K_SWEEP) - 1, index))]
        self.k_text.value = f"K = {self.k}"
        self.show_method("wiener", update=False)
        self._refresh_bars(active=self.k)
        self._safe_update(self.control)

    def _on_degrade(self, field, value):
        """Re-run the whole experiment when the damage changes."""
        self.timeline.cancel()

        if field == "length":
            self.length = int(round(value))
            self.length_text.value = f"{self.length} px"
        elif field == "angle":
            self.angle = float(round(value))
            self.angle_text.value = f"{int(self.angle)}°"
        else:
            self.noise = float(round(value))
            self.noise_text.value = f"σ {self.noise:.0f}"

        try:
            self.trace = RestorationTrace(
                self.scene, self.length, self.angle, self.noise
            )
        except ValueError:
            return

        self._refresh_degraded(noise=self.chapter >= 2 or self.noise > 0)
        self._refresh_kernel_card()
        self._refresh_spectrum_card()
        self._refresh_bars(active=self.k)
        self.show_method(self.method, update=False)

        self.caption_text.value = (
            "New damage. Play again, or hunt for the best K yourself."
        )
        self._safe_update(self.control)

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
            self._scene_blur,
            self._scene_noise,
            self._scene_spectrum,
            self._scene_inverse,
            self._scene_wiener,
        ]
        for index in range(chapter, len(scenes)):
            self._enter_chapter(index)
            await scenes[index](gen)
            self.timeline.check(gen)

    # ---------------- 1. the camera moved ----------------

    async def _scene_blur(self, gen):
        tl = self.timeline

        self.degraded_holder.opacity = 0.0
        self.restored_holder.opacity = 0.0
        self.arrow_one.opacity = 0.0
        self.arrow_two.opacity = 0.0
        self.kernel_card.opacity = 0.0
        self.spectrum_card.opacity = 0.0
        self.formula_card.opacity = 0.0
        tl.push(gen, self.control)

        await self._say(gen, "A sharp photograph of a planet. Nothing wrong with it yet.",
                        self._step(0), hold=2.0)

        await self._say(gen, f"Now the camera moves {self.length} pixels during the "
                             f"exposure, at {int(self.angle)}°.", hold=0.3)
        self._refresh_kernel_card()
        self.kernel_card.opacity = 1.0
        tl.push(gen, self.control)
        await tl.wait(gen, 1.6)

        await self._say(gen, "Every point of light smears along that line: each pixel "
                             "becomes an average of its neighbours down the path.",
                        hold=0.3)
        self._refresh_degraded(noise=False)
        self.arrow_one.opacity = 1.0
        self.degraded_holder.opacity = 1.0
        self.degraded_holder.scale = 1.04
        tl.push(gen, self.control)
        await tl.wait(gen, 0.5)
        self.degraded_holder.scale = 1.0
        tl.push(gen, self.degraded_holder)
        await tl.wait(gen, 1.8)

        await self._say(gen, f"The blur alone costs us: "
                             f"{self.trace.blurred_psnr:.2f} dB against the original.",
                        hold=2.0)

    # ---------------- 2. noise creeps in ----------------

    async def _scene_noise(self, gen):
        tl = self.timeline

        await self._say(gen, "Real sensors also add noise. A little grain, "
                             "barely visible.", self._step(1), hold=0.3)

        self._refresh_degraded(noise=True)
        tl.push(gen, self.control)
        await tl.wait(gen, 1.8)

        await self._say(gen, f"It hardly changes the picture — "
                             f"{self.trace.degraded_psnr:.2f} dB — but hold on to it. "
                             "This grain decides the whole lesson.", hold=2.6)

    # ---------------- 3. what the blur erased ----------------

    async def _scene_spectrum(self, gen):
        tl = self.timeline

        await self._say(gen, "To undo a blur you have to look at it in frequencies.",
                        self._step(2), hold=0.3)

        self._refresh_spectrum_card()
        self.spectrum_card.opacity = 1.0
        tl.push(gen, self.control)
        await tl.wait(gen, 2.0)

        await self._say(gen, "This is |H|, the blur's frequency response. Bright means "
                             "the frequency survived; dark means it was wiped out.",
                        hold=2.6)

        await self._say(gen, f"About {self.trace.null_fraction * 100:.0f}% of the "
                             f"spectrum is near zero. The weakest survives at "
                             f"{self.trace.min_response:.4f}.", hold=2.8)

    # ---------------- 4. the naive inverse ----------------

    async def _scene_inverse(self, gen):
        tl = self.timeline

        await self._say(gen, "The obvious repair: if blurring multiplied by H, "
                             "divide by H.", self._step(3), hold=1.8)

        self.show_method("inverse", update=False)
        self.arrow_two.opacity = 1.0
        self.restored_holder.opacity = 1.0
        tl.push(gen, self.control)
        await tl.wait(gen, 2.0)

        await self._say(gen, f"It collapses: {self.trace.inverse_psnr:.2f} dB, far "
                             f"worse than the blurred photo we started from.", hold=2.4)

        await self._say(gen, "Where |H| is nearly zero, dividing multiplies that tiny "
                             "grain of noise by an enormous number.", hold=2.8)

    # ---------------- 5. Wiener's compromise ----------------

    async def _scene_wiener(self, gen):
        tl = self.timeline

        await self._say(gen, "Wiener deconvolution adds one term to that division.",
                        self._step(4), hold=0.3)

        self.formula_card.opacity = 1.0
        tl.push(gen, self.control)
        await tl.wait(gen, 2.2)

        await self._say(gen, "Where the blur kept a frequency, K is negligible and it "
                             "divides as before. Where the blur erased one, K takes "
                             "over and the answer stays finite.", hold=3.0)

        await self._say(gen, "Watch what K does. Too small and the noise wins; "
                             "too large and the picture stays soft.", hold=0.4)

        for k in K_SWEEP:
            image, psnr = self.trace.wiener(k)
            self.k = k
            self.restored_image.src = palette.png_bytes(image, scale=2)
            self.restored_psnr.value = f"{psnr:.2f} dB"
            self.restored_caption.value = "WIENER RESTORED"
            self.k_text.value = f"K = {k}"
            self.k_slider.value = K_SWEEP.index(k)
            self.method_note.value = f"Wiener at K = {k}"
            self._refresh_bars(active=k)
            tl.push(gen, self.control)
            await tl.wait(gen, 0.55)

        best_k, best_psnr = self.trace.best_k()
        self.k = best_k
        self.show_method("wiener", update=False)
        self.k_slider.value = K_SWEEP.index(best_k)
        self.k_text.value = f"K = {best_k}"
        self._refresh_bars(active=best_k)
        tl.push(gen, self.control)

        await self._say(gen, self._verdict(best_k, best_psnr), hold=3.2)

        await self._say(gen, f"Either way it beats the naive inverse by "
                             f"{best_psnr - self.trace.inverse_psnr:+.2f} dB.",
                        hold=2.2)

        await self._say(gen, "Change the shake, the angle or the noise, and hunt for "
                             "the best K again. Stronger noise always wants a larger K.",
                        hold=2.6)

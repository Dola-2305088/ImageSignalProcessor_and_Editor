"""Discover · Lesson 5 — An image is a sum of waves.

The foundation for every frequency feature. Compression, filtering,
hybrids and texture all become "edit the list of ingredients" once a
viewer believes this one claim, so this lesson earns it before any of
them are mentioned.

The argument runs in one dimension first, where it is easy to accept
that a wiggly line is a sum of sine waves, and only then moves to 2D:

    1  One line of pixels      a row of the planet, drawn as a signal
    2  Add the waves back      the Fourier build-up, harmonic by harmonic
    3  Waves have direction    single 2D frequencies, and where they sit
    4  Reading a spectrum      gratings whose spectra you can predict
    5  Rebuild the picture     the planet from its strongest coefficients

All numbers come from SpectrumTrace, whose verify() checks the
project's manual 2D DFT against NumPy's FFT before any of this is
drawn. The lesson uses the FFT for anything interactive: the manual
transform is a matrix multiply and far too slow for a slider.
"""

import flet as ft
import flet.canvas as fc
import numpy as np

from algorithms.learning.spectrum_trace import (
    BASIS_EXAMPLES,
    SpectrumTrace,
    basis_image,
    spectrum_picture,
)
from ui.learning import palette
from ui.learning.scene_engine import Timeline
from ui.theme import AppAnimations, AppColors, AppLayout


PLOT_W, PLOT_H = 560, 170
IMAGE_PANEL = 188
SPECTRUM_PANEL = 188

SIGNAL_COLOUR = "#8FA6C8"
SUM_COLOUR = palette.INPUT
WAVE_COLOUR = palette.KERNEL
SPECTRUM_ACCENT = palette.PRODUCT

CHAPTERS = [
    "One line of pixels",
    "Add the waves back",
    "Waves have direction",
    "Reading a spectrum",
    "Rebuild the picture",
]

COEFFICIENT_STEPS = (1, 5, 20, 60, 150, 400, 1000, 2500, 9216)


def _mono(size, color):
    return dict(size=size, color=color, weight=ft.FontWeight.BOLD,
                font_family="Consolas")


class LearnSpectrumView:
    def __init__(self, page):
        self.page = page

        self.trace = SpectrumTrace()
        self.row = self.trace.busiest_row()
        self.harmonics = 0
        self.coefficients = 60
        self.basis_index = 1
        self.pattern_index = 0
        self.chapter = 0

        self.timeline = Timeline(page, on_state_change=self._on_running_changed)

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
                colors=["#101C2E", "#0E1526", "#0B1222"],
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
                                bgcolor=palette.argb("22", palette.INPUT),
                                content=ft.Text("DISCOVER  •  LESSON 5", size=9,
                                                weight=ft.FontWeight.BOLD,
                                                color=palette.INPUT),
                            ),
                            ft.Text("An image is a sum of waves",
                                    size=24, weight=ft.FontWeight.BOLD,
                                    color=AppColors.TEXT),
                            ft.Text("The idea every frequency feature is built on, "
                                    "starting with a single line of pixels.",
                                    size=11, color=AppColors.TEXT_SECONDARY),
                        ],
                    ),
                    ft.Row(spacing=8, wrap=True, controls=self.chapter_pills),
                ],
            ),
        )

        stage = ft.Container(
            padding=ft.Padding.symmetric(horizontal=28, vertical=22),
            border_radius=AppLayout.CARD_RADIUS,
            border=ft.Border.all(1, AppColors.BORDER),
            gradient=ft.RadialGradient(
                center=ft.Alignment(0, -0.3),
                radius=1.3,
                colors=["#101A33", "#070C18"],
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    self._caption_block(),
                    self._image_row(),
                    self._plot_card(),
                    self._basis_card(),
                    self._pattern_card(),
                ],
            ),
        )

        controls = ft.ResponsiveRow(
            spacing=14,
            run_spacing=14,
            controls=[
                ft.Container(col={"xs": 12, "lg": 4}, content=self._playback_panel()),
                ft.Container(col={"xs": 12, "lg": 4}, content=self._signal_panel()),
                ft.Container(col={"xs": 12, "lg": 4}, content=self._rebuild_panel()),
            ],
        )

        return ft.Column(spacing=16, controls=[header, stage, controls])

    def _chapter_pill(self, index):
        number = ft.Container(
            width=22, height=22,
            alignment=ft.Alignment.CENTER,
            border_radius=11,
            border=ft.Border.all(1, palette.INPUT),
            content=ft.Text(str(index + 1), size=9, weight=ft.FontWeight.BOLD,
                            color=palette.INPUT),
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
                                    color=palette.INPUT)
        self.caption_text = ft.Text("", size=16, weight=ft.FontWeight.W_600,
                                    color=AppColors.TEXT,
                                    text_align=ft.TextAlign.CENTER,
                                    max_lines=2)
        self.caption = ft.Container(
            width=760,
            height=72,
            alignment=ft.Alignment.TOP_CENTER,
            opacity=1.0,
            animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.caption_step, self.caption_text],
            ),
        )
        return self.caption

    # ---------------- images ----------------

    def _image_row(self):
        self.scene_image = ft.Image(
            src=palette.png_bytes(self.trace.image, scale=2),
            width=IMAGE_PANEL, height=IMAGE_PANEL,
            fit=ft.BoxFit.FILL, border_radius=12, gapless_playback=True,
        )
        self.row_marker = ft.Container(
            width=IMAGE_PANEL, height=3,
            bgcolor=WAVE_COLOUR,
            border_radius=2,
            animate_position=ft.Animation(450, ft.AnimationCurve.EASE_IN_OUT),
            left=0,
            top=0,
            shadow=ft.BoxShadow(blur_radius=10, color=palette.argb("CC", WAVE_COLOUR)),
        )

        self.scene_card = self._framed(
            ft.Stack(
                width=IMAGE_PANEL, height=IMAGE_PANEL,
                controls=[self.scene_image, self.row_marker],
            ),
            "THE PICTURE", palette.INPUT,
        )

        self.rebuilt_image = ft.Image(
            src=palette.png_bytes(self.trace.image, scale=2),
            width=IMAGE_PANEL, height=IMAGE_PANEL,
            fit=ft.BoxFit.FILL, border_radius=12, gapless_playback=True,
        )
        self.rebuilt_note = ft.Text("", **_mono(11, SPECTRUM_ACCENT))
        self.rebuilt_card = self._framed(self.rebuilt_image, "REBUILT",
                                         SPECTRUM_ACCENT, self.rebuilt_note)
        self._show(self.rebuilt_card, False)

        self.spectrum_image = ft.Image(
            src=palette.png_bytes(self.trace.spectrum_image, scale=2),
            width=SPECTRUM_PANEL, height=SPECTRUM_PANEL,
            fit=ft.BoxFit.FILL, border_radius=12, gapless_playback=True,
        )
        self.spectrum_note = ft.Text("", size=9, color=AppColors.MUTED)
        self.spectrum_card = self._framed(self.spectrum_image, "SPECTRUM  ·  |F(u,v)|",
                                          palette.KERNEL_FRAME, self.spectrum_note)
        self._show(self.spectrum_card, False)

        self.image_row_control = ft.Container(
            width=float("inf"),
            alignment=ft.Alignment.CENTER,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START,
                wrap=True,
                spacing=18,
                run_spacing=18,
                controls=[self.scene_card, self.spectrum_card, self.rebuilt_card],
            ),
        )
        return self.image_row_control

    @staticmethod
    def _show(control, visible):
        """Fade a card without moving it: the layout stays put."""
        control.opacity = 1.0 if visible else 0.0
        control.visible = True

    def _framed(self, body, title, accent, note=None):
        controls = [
            ft.Row(
                tight=True, spacing=7,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=7, height=7, border_radius=4, bgcolor=accent),
                    ft.Text(title, size=9, weight=ft.FontWeight.BOLD, color=accent),
                ],
            ),
            ft.Container(
                border_radius=13,
                border=ft.Border.all(1.4, palette.argb("88", accent)),
                shadow=ft.BoxShadow(blur_radius=26, spread_radius=-9,
                                    color=palette.argb("66", accent)),
                content=body,
            ),
            ft.Container(height=18, alignment=ft.Alignment.CENTER, content=note),
        ]

        return ft.Container(
            width=IMAGE_PANEL + 32,
            height=IMAGE_PANEL + 80,
            alignment=ft.Alignment.TOP_CENTER,
            opacity=1.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=14,
            border_radius=16,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#121A2B", "#0C1220"],
            ),
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=9,
                controls=controls,
            ),
        )

    # ---------------- the signal plot ----------------

    def _plot_card(self):
        self.plot = fc.Canvas(width=PLOT_W, height=PLOT_H, shapes=[])
        self.plot_legend = ft.Row(
            spacing=16,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                self._legend("original row signal", SIGNAL_COLOUR),
                self._legend("reconstruction so far", SUM_COLOUR),
                self._legend("wave being added", WAVE_COLOUR),
            ],
        )
        self.plot_note = ft.Text("", **_mono(11, SUM_COLOUR))

        self.plot_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=14,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            width=720,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=9,
                controls=[
                    ft.Text("SELECTED IMAGE ROW → 1D SIGNAL", size=10,
                            weight=ft.FontWeight.BOLD, color=SUM_COLOUR),
                    ft.Text("Each point is one pixel: left/right = position, height = brightness.",
                            size=10, color=AppColors.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Column(
                                width=62,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=52,
                                controls=[
                                    ft.Text("BRIGHT", size=8, weight=ft.FontWeight.BOLD, color=WAVE_COLOUR),
                                    ft.Text("DARK", size=8, weight=ft.FontWeight.BOLD, color=AppColors.MUTED),
                                ],
                            ),
                            self.plot,
                        ],
                    ),
                    ft.Text("← pixel position →", size=9, color=AppColors.MUTED),
                    self.plot_legend,
                    self.plot_note,
                ],
            ),
        )
        self._draw_plot(show_sum=False, show_wave=False)
        return self.plot_card

    @staticmethod
    def _legend(label, colour):
        return ft.Row(
            tight=True, spacing=6,
            controls=[
                ft.Container(width=16, height=3, border_radius=2, bgcolor=colour),
                ft.Text(label, size=9, color=AppColors.TEXT_SECONDARY),
            ],
        )

    def _polyline(self, values, colour, width=2.0, baseline=128.0, scale=None):
        """Turn a 1D array into a canvas path across the plot area."""
        values = np.asarray(values, dtype=np.float64)
        count = len(values)
        if count < 2:
            return None

        scale = scale or 255.0
        step = PLOT_W / (count - 1)
        margin = 12

        def y_of(value):
            fraction = (value - baseline) / scale
            return PLOT_H / 2 - fraction * (PLOT_H - 2 * margin)

        elements = [fc.Path.MoveTo(0, y_of(values[0]))]
        for index in range(1, count):
            elements.append(fc.Path.LineTo(index * step, y_of(values[index])))

        return fc.Path(
            elements=elements,
            paint=ft.Paint(
                style=ft.PaintingStyle.STROKE,
                stroke_width=width,
                color=colour,
            ),
        )

    def _draw_plot(self, show_sum=True, show_wave=False):
        shapes = []

        # midline
        shapes.append(
            fc.Path(
                elements=[fc.Path.MoveTo(0, PLOT_H / 2),
                          fc.Path.LineTo(PLOT_W, PLOT_H / 2)],
                paint=ft.Paint(style=ft.PaintingStyle.STROKE, stroke_width=1,
                               color="#1E2C46"),
            )
        )

        signal = self.trace.row_signal(self.row)
        line = self._polyline(signal, SIGNAL_COLOUR, 2.0)
        if line:
            shapes.append(line)

        if show_wave and self.harmonics > 0:
            wave = self.trace.single_wave(self.row, self.harmonics)
            drawn = self._polyline(wave, WAVE_COLOUR, 1.6, baseline=0.0, scale=255.0)
            if drawn:
                shapes.append(drawn)

        if show_sum:
            partial = self.trace.partial_sum(self.row, self.harmonics)
            drawn = self._polyline(partial, SUM_COLOUR, 2.6)
            if drawn:
                shapes.append(drawn)

        self.plot.shapes = shapes

        if show_sum:
            error = self.trace.row_error(self.row, self.harmonics)
            self.plot_note.value = (
                f"row {self.row}  ·  {self.harmonics} "
                f"wave{'' if self.harmonics == 1 else 's'} added  ·  "
                f"still off by {error:.1f}"
            )
        else:
            self.plot_note.value = f"row {self.row} of the picture, as a signal"

    # ---------------- basis images ----------------

    def _basis_card(self):
        self.basis_image_control = ft.Image(
            src=palette.png_bytes(basis_image(0, 2, self.trace.size), scale=2),
            width=170, height=170, fit=ft.BoxFit.FILL,
            border_radius=10, gapless_playback=True,
        )
        self.basis_spectrum = ft.Image(
            src=palette.png_bytes(
                spectrum_picture(np.fft.fft2(basis_image(0, 2, self.trace.size)
                                             .astype(float))), scale=2),
            width=170, height=170, fit=ft.BoxFit.FILL,
            border_radius=10, gapless_playback=True,
        )
        self.basis_title = ft.Text("", size=12, weight=ft.FontWeight.BOLD,
                                   color=WAVE_COLOUR)
        self.basis_note = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)

        self.basis_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=14,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    self.basis_title,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=16,
                        controls=[
                            self._mini("ONE WAVE", self.basis_image_control,
                                       WAVE_COLOUR),
                            ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=22,
                                    color=AppColors.MUTED),
                            self._mini("ITS PLACE  ·  F(u,v)",
                                       self.basis_spectrum, palette.KERNEL_FRAME),
                        ],
                    ),
                    self.basis_note,
                ],
            ),
        )
        return self.basis_card

    @staticmethod
    def _mini(title, image, accent):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            controls=[
                ft.Container(
                    border_radius=12,
                    border=ft.Border.all(1.2, palette.argb("77", accent)),
                    content=image,
                ),
                ft.Text(title, size=8, weight=ft.FontWeight.BOLD, color=accent),
            ],
        )

    def _show_basis(self, index):
        self.basis_index = index % len(BASIS_EXAMPLES)
        name, u, v, note = BASIS_EXAMPLES[self.basis_index]

        wave = basis_image(u, v, self.trace.size)
        self.basis_image_control.src = palette.png_bytes(wave, scale=2)
        self.basis_spectrum.src = palette.png_bytes(
            spectrum_picture(np.fft.fft2(wave.astype(float))), scale=2
        )
        self.basis_title.value = f"{name}   ·   u = {u}, v = {v}"
        self.basis_note.value = note

    # ---------------- patterns ----------------

    def _pattern_card(self):
        self.patterns = self.trace.pattern_set()

        self.pattern_image = ft.Image(
            src=palette.png_bytes(self.patterns[0]["image"], scale=2),
            width=180, height=180, fit=ft.BoxFit.FILL,
            border_radius=10, gapless_playback=True,
        )
        self.pattern_spectrum = ft.Image(
            src=palette.png_bytes(self.patterns[0]["spectrum"], scale=2),
            width=180, height=180, fit=ft.BoxFit.FILL,
            border_radius=10, gapless_playback=True,
        )
        self.pattern_title = ft.Text("", size=12, weight=ft.FontWeight.BOLD,
                                     color=palette.KERNEL_FRAME)
        self.pattern_note = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY,
                                    text_align=ft.TextAlign.CENTER)
        self.pattern_measure = ft.Text("", **_mono(11, SPECTRUM_ACCENT))

        self.pattern_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=14,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    self.pattern_title,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=16,
                        controls=[
                            self._mini("PICTURE", self.pattern_image, palette.INPUT),
                            ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=22,
                                    color=AppColors.MUTED),
                            self._mini("SPECTRUM", self.pattern_spectrum,
                                       palette.KERNEL_FRAME),
                        ],
                    ),
                    self.pattern_note,
                    self.pattern_measure,
                ],
            ),
        )
        self._show_pattern(0)
        return self.pattern_card

    def _show_pattern(self, index):
        self.pattern_index = index % len(self.patterns)
        item = self.patterns[self.pattern_index]

        self.pattern_image.src = palette.png_bytes(item["image"], scale=2)
        self.pattern_spectrum.src = palette.png_bytes(item["spectrum"], scale=2)
        self.pattern_title.value = item["name"]
        self.pattern_note.value = item["note"]

        radius = self.trace.peak_radius(item["image"])
        if item["name"] == "The planet":
            self.pattern_measure.value = "no single peak: a real picture needs them all"
        else:
            spacing = self.trace.size / radius if radius else 0
            self.pattern_measure.value = (
                f"brightest peak {radius:.1f} from the centre  →  "
                f"stripes about {spacing:.1f} px apart"
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
            gradient=ft.LinearGradient(colors=[palette.INPUT, "#0EA5E9"]),
            shadow=ft.BoxShadow(blur_radius=22, spread_radius=-6,
                                color=palette.argb("99", palette.INPUT)),
            ink=True,
            on_click=self.toggle_play,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[self.play_icon, self.play_label],
            ),
        )
        self.speed_label = ft.Text("1×", size=11, weight=ft.FontWeight.BOLD,
                                   color=palette.INPUT)

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
                            active_color=palette.INPUT,
                            on_change=self._on_speed,
                        )),
                        self.speed_label,
                    ],
                ),
            ],
        )
        return self._panel("PLAYBACK", "One idea at a time.",
                           ft.Icons.SMART_DISPLAY_OUTLINED, palette.INPUT, body)

    def _signal_panel(self):
        self.row_text = ft.Text(f"row {self.row}", **_mono(11, WAVE_COLOUR))
        self.harmonic_text = ft.Text("0 waves", **_mono(11, SUM_COLOUR))

        body = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[ft.Text("Which row", size=10, color=AppColors.MUTED),
                              self.row_text],
                ),
                ft.Slider(min=0, max=self.trace.size - 1, divisions=self.trace.size - 1,
                          value=self.row, active_color=WAVE_COLOUR,
                          on_change=lambda e: self.set_row(int(e.control.value))),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[ft.Text("Waves added", size=10, color=AppColors.MUTED),
                              self.harmonic_text],
                ),
                ft.Slider(min=0, max=self.trace.size // 2, divisions=self.trace.size // 2,
                          value=0, active_color=SUM_COLOUR,
                          on_change=lambda e: self.set_harmonics(int(e.control.value))),
                ft.Text("Try it: move right to add more waves. The reconstruction should gradually match the original row.",
                        size=10, color=AppColors.MUTED),
            ],
        )
        return self._panel("THE SIGNAL", "One row, rebuilt from waves.",
                           ft.Icons.SHOW_CHART, SUM_COLOUR, body)

    def _rebuild_panel(self):
        self.coefficient_text = ft.Text("", **_mono(11, SPECTRUM_ACCENT))
        self.quality_text = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)

        body = ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[ft.Text("Coefficients kept", size=10,
                                      color=AppColors.MUTED),
                              self.coefficient_text],
                ),
                ft.Slider(min=0, max=len(COEFFICIENT_STEPS) - 1,
                          divisions=len(COEFFICIENT_STEPS) - 1,
                          value=3, active_color=SPECTRUM_ACCENT,
                          on_change=lambda e: self.set_coefficients(
                              COEFFICIENT_STEPS[int(e.control.value)])),
                self.quality_text,
                ft.Row(
                    spacing=8,
                    controls=[
                        self._small_button("Next wave shape", ft.Icons.WAVES,
                                           lambda e: self._cycle_basis()),
                        self._small_button("Next pattern", ft.Icons.PATTERN,
                                           lambda e: self._cycle_pattern()),
                    ],
                ),
            ],
        )
        return self._panel("THE PICTURE", "Rebuilt from its strongest waves.",
                           ft.Icons.AUTO_AWESOME_MOSAIC, SPECTRUM_ACCENT, body)

    # =========================================================
    # STATE
    # =========================================================

    def _apply_chapter_state(self, chapter, first_build=False):
        self.chapter = chapter

        self._show(self.plot_card, chapter <= 1)
        self._show(self.basis_card, chapter == 2)
        self._show(self.pattern_card, chapter == 3)
        self._show(self.spectrum_card, chapter >= 3)
        self._show(self.rebuilt_card, chapter >= 4)
        self.row_marker.opacity = 1.0 if chapter <= 1 else 0.0

        self._move_marker()

        if chapter == 0:
            self.harmonics = 0
            self._draw_plot(show_sum=False)
        elif chapter == 1:
            self._draw_plot(show_sum=True, show_wave=True)

        if chapter >= 4:
            self._refresh_rebuild()

        self._sync_labels()

        step, text = self._resting_caption(chapter)
        self.caption_step.value = step
        self.caption_text.value = text

        self._refresh_chapter_pills()

        if not first_build:
            self._safe_update(self.control)

    def _resting_caption(self, chapter):
        step = f"CHAPTER {chapter + 1}  ·  {CHAPTERS[chapter].upper()}"
        if chapter == 0:
            return step, "Press Play — first we turn one horizontal row of pixels into a simple signal."
        return step, "Press Play to continue, or explore the controls yourself."

    def _move_marker(self):
        self.row_marker.top = (self.row / self.trace.size) * IMAGE_PANEL

    def _sync_labels(self):
        self.row_text.value = f"row {self.row}"
        self.harmonic_text.value = (
            f"{self.harmonics} wave{'' if self.harmonics == 1 else 's'}"
        )
        self.coefficient_text.value = f"{self.coefficients:,}"

    @staticmethod
    def _psnr_text(psnr):
        """A perfect rebuild scores infinite PSNR; say so in words."""
        return "exact" if not np.isfinite(psnr) else f"{psnr:.1f} dB"

    def _refresh_rebuild(self):
        quality = self.trace.reconstruction_quality(self.coefficients)
        self.rebuilt_image.src = palette.png_bytes(quality["image"], scale=2)
        self.rebuilt_note.value = (
            f"{quality['count']:,} of {self.trace.spectrum.size:,}  ·  "
            f"{self._psnr_text(quality['psnr'])}"
        )
        self.quality_text.value = (
            f"{quality['percent']:.2f}% of the coefficients hold "
            f"{quality['energy'] * 100:.1f}% of the energy."
        )

    def _refresh_chapter_pills(self):
        for index, pill in enumerate(self.chapter_pills):
            active = index == self.chapter
            done = index < self.chapter
            pill.bgcolor = (palette.argb("26", palette.INPUT) if active
                            else AppColors.SURFACE_DARK)
            pill.border = ft.Border.all(
                1, palette.INPUT if active else AppColors.BORDER_SOFT)
            number = pill.data
            number.bgcolor = palette.INPUT if (active or done) else None
            number.content.color = "#0B1020" if (active or done) else palette.INPUT

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

    def set_row(self, row):
        self.timeline.cancel()
        self.row = int(row)
        self._move_marker()
        self._draw_plot(show_sum=self.chapter >= 1, show_wave=self.chapter == 1)
        self._sync_labels()
        self.caption_text.value = (
            f"Row {self.row}: a different line through the picture, "
            f"a different set of waves."
        )
        self._safe_update(self.control)

    def set_harmonics(self, value):
        self.timeline.cancel()
        self.harmonics = int(value)
        self._show(self.plot_card, True)
        self._draw_plot(show_sum=True, show_wave=True)
        self._sync_labels()

        error = self.trace.row_error(self.row, self.harmonics)
        if self.harmonics == 0:
            message = "Zero waves: just the average brightness, a flat line."
        elif error < 1.0:
            message = (f"{self.harmonics} waves and the curves sit on top of each "
                       f"other. That row *is* those waves.")
        else:
            message = (f"{self.harmonics} waves: off by {error:.1f} and closing.")

        self.caption_text.value = message
        self._safe_update(self.control)

    def set_coefficients(self, value):
        self.timeline.cancel()
        self.coefficients = int(value)
        self._show(self.rebuilt_card, True)
        self._show(self.spectrum_card, True)
        self._refresh_rebuild()
        self._sync_labels()

        quality = self.trace.reconstruction_quality(self.coefficients)
        if np.isfinite(quality["psnr"]):
            self.caption_text.value = (
                f"{quality['count']:,} waves out of {self.trace.spectrum.size:,} — "
                f"{quality['percent']:.2f}% — and the picture is already at "
                f"{quality['psnr']:.1f} dB."
            )
        else:
            self.caption_text.value = (
                "Every wave kept, so the picture comes back exactly."
            )
        self._safe_update(self.control)

    def _cycle_basis(self):
        self.timeline.cancel()
        self._show_basis(self.basis_index + 1)
        self._show(self.basis_card, True)
        name, u, v, note = BASIS_EXAMPLES[self.basis_index]
        self.caption_text.value = f"{name}: u = {u}, v = {v} — {note}."
        self._safe_update(self.control)

    def _cycle_pattern(self):
        self.timeline.cancel()
        self._show_pattern(self.pattern_index + 1)
        self._show(self.pattern_card, True)
        self.caption_text.value = self.patterns[self.pattern_index]["note"]
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
            self._scene_row,
            self._scene_build,
            self._scene_direction,
            self._scene_reading,
            self._scene_rebuild,
        ]
        for index in range(chapter, len(scenes)):
            self._enter_chapter(index)
            await scenes[index](gen)
            self.timeline.check(gen)

    # ---------------- 1 ----------------

    async def _scene_row(self, gen):
        tl = self.timeline

        self._show(self.plot_card, False)
        self._show(self.basis_card, False)
        self._show(self.pattern_card, False)
        self._show(self.spectrum_card, False)
        self._show(self.rebuilt_card, False)
        tl.push(gen, self.control)

        await self._say(gen, "A planet, its ring, a few stars. We are going to take "
                             "it apart — but not into pixels this time.",
                        self._step(0), hold=4.0)

        await self._say(gen, "Start with something simpler than a whole picture: one horizontal row. "
                             "The yellow line shows exactly which pixels we selected.", hold=0.4)

        self.row = self.trace.busiest_row()
        self._move_marker()
        self.row_marker.opacity = 1.0
        tl.push(gen, self.scene_card)
        await tl.wait(gen, 1.6)

        self.harmonics = 0
        self._draw_plot(show_sum=False)
        self._show(self.plot_card, True)
        tl.push(gen, self.control)
        await tl.wait(gen, 1.8)

        await self._say(gen, f"Now read row {self.row} from left to right. Every pixel becomes one point: "
                             f"higher means brighter, lower means darker. So this graph is simply "
                             f"{self.trace.size} pixel brightness values.", hold=4.8)

        await self._say(gen, "Here is the claim: that wiggle is nothing more than "
                             "smooth waves added together. Let's prove it.", hold=4.2)

    # ---------------- 2 ----------------

    async def _scene_build(self, gen):
        tl = self.timeline

        await self._say(gen, "Start with no waves at all — just the average "
                             "brightness of the row.", self._step(1), hold=0.4)

        self.harmonics = 0
        self._draw_plot(show_sum=True, show_wave=False)
        self._sync_labels()
        tl.push(gen, self.control)
        await tl.wait(gen, 2.2)

        await self._say(gen, "A flat line. Now add the slowest wave: one single "
                             "rise and fall across the whole row.", hold=0.4)

        for harmonic in range(1, 4):
            self.harmonics = harmonic
            self._draw_plot(show_sum=True, show_wave=True)
            self._sync_labels()
            tl.push(gen, self.plot_card, self.harmonic_text)
            await tl.wait(gen, 1.6)

        await self._say(gen, "Amber is the wave being added, blue is everything so "
                             "far. Each new wave is faster than the last, and fixes "
                             "detail the earlier ones were too slow to catch.",
                        hold=5.0)

        for harmonic in range(4, 25):
            self.harmonics = harmonic
            self._draw_plot(show_sum=True, show_wave=True)
            self._sync_labels()
            tl.push(gen, self.plot_card, self.harmonic_text)
            await tl.wait(gen, 0.22)

        await tl.wait(gen, 1.0)
        error = self.trace.row_error(self.row, self.harmonics)
        await self._say(gen, f"Twenty-four waves and the blue curve is within "
                             f"{error:.1f} of the real row.", hold=3.6)

        full = self.trace.size // 2
        for harmonic in range(25, full + 1, 2):
            self.harmonics = harmonic
            self._draw_plot(show_sum=True, show_wave=False)
            self._sync_labels()
            tl.push(gen, self.plot_card, self.harmonic_text)
            await tl.wait(gen, 0.12)

        self.harmonics = full
        self._draw_plot(show_sum=True, show_wave=False)
        tl.push(gen, self.plot_card)

        await self._say(gen, f"With all {full}, the two curves are identical — the "
                             f"error is exactly zero. The row was never anything "
                             f"but a sum of waves.", hold=5.0)

    # ---------------- 3 ----------------

    async def _scene_direction(self, gen):
        tl = self.timeline

        self._show(self.plot_card, False)
        self._show_basis(1)
        self._show(self.basis_card, True)
        tl.push(gen, self.control)

        await self._say(gen, "A picture has two directions, so its waves need a "
                             "direction too.", self._step(2), hold=3.4)

        for index in range(len(BASIS_EXAMPLES)):
            self._show_basis(index)
            tl.push(gen, self.basis_card)

            name, u, v, note = BASIS_EXAMPLES[index]
            await self._say(gen, f"{name}: {note}.", hold=3.4)

        await self._say(gen, "Notice where each one sits in the spectrum. Close to "
                             "the centre means a slow, wide wave. Far out means "
                             "fine detail. The direction of the dots matches the "
                             "tilt of the stripes.", hold=5.4)

    # ---------------- 4 ----------------

    async def _scene_reading(self, gen):
        tl = self.timeline

        self._show(self.basis_card, False)
        self._show_pattern(0)
        self._show(self.pattern_card, True)
        self._show(self.spectrum_card, True)
        tl.push(gen, self.control)

        await self._say(gen, "Now read a spectrum properly — starting with pictures "
                             "whose answer you can guess.", self._step(3), hold=3.4)

        for index in range(len(self.patterns)):
            self._show_pattern(index)
            tl.push(gen, self.pattern_card)

            item = self.patterns[index]
            if item["name"] == "Fine stripes":
                text = ("Halve the spacing and the two dots move twice as far out. "
                        "Distance from the centre is fineness, nothing else.")
            elif item["name"] == "Tilted stripes":
                text = ("Rotate the picture and the whole spectrum rotates with it. "
                        "That single fact is how texture orientation is measured.")
            elif item["name"] == "The planet":
                text = ("A real picture is all of them at once: bright at the "
                        "centre, because most of an image is smooth, with a faint "
                        "haze further out for the edges.")
            else:
                text = ("Wide stripes: one spacing, one direction, so the spectrum "
                        "is two dots near the centre and almost nothing else.")

            await self._say(gen, text, hold=4.8)

        await self._say(gen, "Centre is the average, distance is fineness, "
                             "direction is orientation, brightness is how much. "
                             "That is the whole alphabet.", hold=5.0)

    # ---------------- 5 ----------------

    async def _scene_rebuild(self, gen):
        tl = self.timeline

        self._show(self.pattern_card, False)
        self._show(self.spectrum_card, True)
        self._show(self.rebuilt_card, True)
        tl.push(gen, self.control)

        await self._say(gen, "Back to the planet, and the same trick as the row — "
                             "now in two dimensions.", self._step(4), hold=3.4)

        for count in COEFFICIENT_STEPS:
            self.coefficients = count
            self._refresh_rebuild()
            self._sync_labels()
            tl.push(gen, self.rebuilt_card, self.coefficient_text, self.quality_text)

            quality = self.trace.reconstruction_quality(count)
            if count == 1:
                text = ("One single wave — the average brightness. A flat grey "
                        "square.")
            elif count <= 20:
                text = (f"{count} waves: the planet is a blob, but it is in the "
                        f"right place.")
            elif count <= 400:
                text = (f"{count} waves, {quality['percent']:.1f}% of the total, and "
                        f"the ring has appeared: {self._psnr_text(quality['psnr'])}.")
            elif count < self.trace.spectrum.size:
                text = (f"{count:,} waves — {quality['percent']:.1f}% — holding "
                        f"{quality['energy'] * 100:.1f}% of the energy at "
                        f"{self._psnr_text(quality['psnr'])}.")
            else:
                text = "All of them, and the original is back exactly."

            await self._say(gen, text, hold=3.4)

        hundred = self.trace.reconstruction_quality(100)
        await self._say(gen, f"That is the fact the whole frequency side lives on: "
                             f"{hundred['percent']:.1f}% of the waves carry "
                             f"{hundred['energy'] * 100:.0f}% of the picture.",
                        hold=5.0)

        await self._say(gen, "Keep only the strong ones and you have compression. "
                             "Keep the slow ones and you have blur. Keep the fast "
                             "ones and you have edges. Every frequency feature is "
                             "a different way of choosing.", hold=5.6)

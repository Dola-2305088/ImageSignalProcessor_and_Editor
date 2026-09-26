"""Discover · Lesson 5 — Waves and spectra.

Rebuilt to start from something a first-timer can see rather than from
an equation. The old version opened on a line graph of one row of
pixels, which is the most abstract possible entry point; this one opens
on a picture of stripes and says "that is a wave".

The argument, in five steps:

    1  a wave is a picture of stripes, and it makes two dots
    2  add two wave pictures together and the dots add too
    3  a photograph is thousands of them stacked
    4  the spectrum is the shopping list: where a dot sits says
       how fine the stripes are and which way they run
    5  every frequency feature is a way of editing that list

Numbers come from SpectrumTrace, whose verify() checks the project's
manual 2D DFT against NumPy's FFT before any of this is drawn.
"""

import flet as ft
import flet.canvas as fc
import numpy as np

from algorithms.learning.spectrum_trace import (
    SpectrumTrace,
    add_waves,
    annotate_spectrum,
    peak_info,
    spectrum_picture,
    wave_image,
)
from ui.learning import palette
from ui.learning.lesson_shell import LessonShell, mono
from ui.theme import AppColors


PICTURE = 188
PLOT_W, PLOT_H = 620, 96

WAVE_A = palette.INPUT
WAVE_B = palette.KERNEL
SUM_ACCENT = palette.PRODUCT
SPECTRUM_ACCENT = palette.KERNEL_FRAME

# How many waves the rebuild chapter steps through.
REBUILD_STEPS = (1, 4, 20, 100, 600, 3000, 9216)

# Band spacings that divide the 96 px picture exactly, so the lesson's
# "steps x spacing = picture width" line is always literally true and
# never has to hedge with an approximation.
SPACING_STEPS = (4, 6, 8, 12, 16, 24, 32, 48)


class LearnSpectrumView(LessonShell):
    CHAPTERS = [
        "A wave is stripes",
        "Two waves add up",
        "A photo is many waves",
        "Reading the spectrum",
        "What it is all for",
    ]
    ACCENT = palette.INPUT
    BADGE = "DISCOVER  •  LESSON 5"
    TITLE = "Waves and spectra"
    SUBTITLE = "Start with one stripe pattern. Finish with a photograph."

    def __init__(self, page):
        super().__init__(page)

        self.trace = SpectrumTrace()
        self.size = self.trace.size

        self.spacing_a = 24
        self.angle_a = 0
        self.spacing_b = 8
        self.angle_b = 90
        self.kept = 100

        self.build()
        self.set_chapter_state(0, first_build=True)

    # =========================================================
    # STAGE
    # =========================================================

    def build_stage(self):
        # ---- chapter 1 and 2: wave pictures ----
        self.wave_a_image = self._picture(self._wave_a())
        self.wave_b_image = self._picture(self._wave_b())
        self.sum_image = self._picture(self._sum_wave())

        self.wave_a_note = ft.Text("", **mono(11, WAVE_A))
        self.wave_b_note = ft.Text("", **mono(11, WAVE_B))
        self.sum_note = ft.Text("", **mono(11, SUM_ACCENT))

        self.wave_a_card = self.picture_card(
            self.wave_a_image, "WAVE A", WAVE_A, self.wave_a_note)
        self.wave_b_card = self.picture_card(
            self.wave_b_image, "WAVE B", WAVE_B, self.wave_b_note)
        self.sum_card = self.picture_card(
            self.sum_image, "A + B", SUM_ACCENT, self.sum_note)
        self.plus_slot = self.slot(self.arrow("add"), width=70)

        self.waves_row = self.row([
            self.wave_a_card,
            self.plus_slot,
            self.wave_b_card,
            self.slot(self.arrow("="), width=70),
            self.sum_card,
        ])

        # ---- the wave, drawn as a graph, under the pictures ----
        self.plot = fc.Canvas(width=PLOT_W, height=PLOT_H, shapes=[])
        self.plot_note = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)
        self.plot_card = ft.Container(
            opacity=0.0,
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
                spacing=8,
                controls=[
                    self.card_title("BRIGHTNESS ALONG ONE LINE OF THE PICTURE",
                                    WAVE_A),
                    self.plot,
                    self.plot_note,
                ],
            ),
        )

        # ---- chapter 1 and 4: the spectrum of whatever is shown ----
        self.spectrum_image = self._picture(self._spectrum_of(self._wave_a()))
        self.spectrum_note = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)
        self.spectrum_card = self.picture_card(
            self.spectrum_image, "ITS SPECTRUM", SPECTRUM_ACCENT,
            self.spectrum_note)

        self.spectrum_row = self.row([self.spectrum_card])

        # ---- chapter 3: the planet, rebuilt ----
        self.original_image = self._picture(self.trace.image)
        self.rebuilt_image = self._picture(self.trace.reconstruct_top(self.kept))
        self.rebuilt_note = ft.Text("", **mono(11, SUM_ACCENT))

        self.rebuild_row = self.row([
            self.picture_card(self.original_image, "A REAL PHOTOGRAPH", WAVE_A),
            self.slot(self.arrow("built from waves"), width=110),
            self.picture_card(self.rebuilt_image, "WAVES ADDED SO FAR",
                              SUM_ACCENT, self.rebuilt_note),
        ])

        # ---- chapter 4: measure one pattern, then compare three ----
        self.measured_stripes = self._picture(self._wave_a())
        self.measured_spectrum = self._picture(self._wave_a())
        self.measure_lines = {
            "bands": ft.Text("", **mono(15, WAVE_A)),
            "steps": ft.Text("", **mono(15, SPECTRUM_ACCENT)),
            "check": ft.Text("", **mono(15, SUM_ACCENT)),
            "angle": ft.Text("", **mono(15, WAVE_B)),
        }

        self.measure_card = ft.Container(
            width=310,
            padding=16,
            border_radius=16,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#121A2B", "#0C1220"],
            ),
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                spacing=11,
                controls=[
                    self.card_title("WHAT THE DOT IS TELLING YOU",
                                    SPECTRUM_ACCENT),
                    self._measure_row("Bands are", self.measure_lines["bands"]),
                    self._measure_row("Dot sits", self.measure_lines["steps"]),
                    ft.Divider(height=1, color="#1E2C46"),
                    self._measure_row("So", self.measure_lines["check"]),
                    self._measure_row("Tilt", self.measure_lines["angle"]),
                ],
            ),
        )

        self.guide_row = self.row([
            self.picture_card(self.measured_stripes, "THE STRIPES", WAVE_A),
            self.slot(self.arrow("measure"), width=84),
            self.picture_card(self.measured_spectrum, "ITS SPECTRUM, MEASURED",
                              SPECTRUM_ACCENT),
            self.measure_card,
        ])

        # A compact three-up so the pattern is obvious at a glance.
        self.compare_row = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=self.row([
                self._compare_card(spacing) for spacing in (32, 12, 6)
            ]),
        )

        return [self.waves_row, self.plot_card, self.spectrum_row,
                self.rebuild_row, self.guide_row, self.compare_row]

    def _picture(self, array, size=PICTURE):
        return ft.Image(
            src=palette.png_bytes(array, scale=2),
            width=size, height=size,
            fit=ft.BoxFit.FILL, border_radius=12, gapless_playback=True,
        )

    @staticmethod
    def _measure_row(label, value):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(label, size=10, color=AppColors.MUTED),
                value,
            ],
        )

    def _compare_card(self, spacing):
        """One spacing, its spectrum, and the two numbers underneath."""
        picture = wave_image(self.size, spacing, 0)
        marked, info = self._annotated_spectrum(picture)

        return ft.Container(
            padding=12,
            border_radius=16,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#121A2B", "#0C1220"],
            ),
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Row(
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            self._picture(picture, 104),
                            ft.Image(
                                src=self._rgb_png(marked),
                                width=104, height=104,
                                fit=ft.BoxFit.FILL, border_radius=10,
                                gapless_playback=True,
                            ),
                        ],
                    ),
                    ft.Text(f"{spacing} px bands", size=11,
                            weight=ft.FontWeight.BOLD, color=WAVE_A),
                    ft.Text(f"dot {info['radius']:.0f} steps out", size=10,
                            color=AppColors.TEXT_SECONDARY),
                ],
            ),
        )

    # ---------------- pictures ----------------

    def _wave_a(self):
        return wave_image(self.size, self.spacing_a, self.angle_a)

    def _wave_b(self):
        return wave_image(self.size, self.spacing_b, self.angle_b)

    def _sum_wave(self):
        return add_waves(self._wave_a(), self._wave_b())

    @staticmethod
    def _spectrum_of(image):
        return spectrum_picture(np.fft.fft2(np.asarray(image, dtype=np.float64)))

    @staticmethod
    def _rgb_png(array):
        from io import BytesIO

        from PIL import Image

        buffer = BytesIO()
        Image.fromarray(np.asarray(array, dtype=np.uint8)).save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def _annotated_spectrum(image):
        """Shared with the texture lesson: see spectrum_trace."""
        return annotate_spectrum(image)

    # ---------------- the graph ----------------

    def _draw_plot(self, image, colour, label):
        """One row of a picture, drawn as a rising and falling line."""
        row = np.asarray(image, dtype=np.float64)[self.size // 2]

        margin = 10
        step = PLOT_W / max(1, len(row) - 1)

        def y_of(value):
            return PLOT_H - margin - (value / 255.0) * (PLOT_H - 2 * margin)

        shapes = [
            fc.Path(
                elements=[fc.Path.MoveTo(0, PLOT_H / 2),
                          fc.Path.LineTo(PLOT_W, PLOT_H / 2)],
                paint=ft.Paint(style=ft.PaintingStyle.STROKE, stroke_width=1,
                               color="#1E2C46"),
            ),
            fc.Path(
                elements=(
                    [fc.Path.MoveTo(0, y_of(row[0]))]
                    + [fc.Path.LineTo(i * step, y_of(row[i]))
                       for i in range(1, len(row))]
                ),
                paint=ft.Paint(style=ft.PaintingStyle.STROKE, stroke_width=2.6,
                               color=colour),
            ),
        ]

        self.plot.shapes = shapes
        self.plot_note.value = label

    # =========================================================
    # PANELS
    # =========================================================

    def side_panels(self):
        self.spacing_a_text = ft.Text("", **mono(11, WAVE_A))
        self.spacing_b_text = ft.Text("", **mono(11, WAVE_B))
        self.angle_a_text = ft.Text("", **mono(11, WAVE_A))
        self.angle_b_text = ft.Text("", **mono(11, WAVE_B))
        self.kept_text = ft.Text("", **mono(11, SUM_ACCENT))

        waves_body = ft.Column(
            spacing=10,
            controls=[
                self.slider_row(
                    "Wave A: stripe spacing", self.spacing_a_text,
                    ft.Slider(min=0, max=len(SPACING_STEPS) - 1,
                              divisions=len(SPACING_STEPS) - 1,
                              value=SPACING_STEPS.index(self.spacing_a),
                              active_color=WAVE_A,
                              on_change=lambda e: self.set_wave(
                                  "a", SPACING_STEPS[int(e.control.value)])),
                ),
                self.slider_row(
                    "Wave B: stripe spacing", self.spacing_b_text,
                    ft.Slider(min=0, max=len(SPACING_STEPS) - 1,
                              divisions=len(SPACING_STEPS) - 1,
                              value=SPACING_STEPS.index(self.spacing_b),
                              active_color=WAVE_B,
                              on_change=lambda e: self.set_wave(
                                  "b", SPACING_STEPS[int(e.control.value)])),
                ),
                self.slider_row(
                    "Wave A: direction", self.angle_a_text,
                    ft.Slider(min=0, max=90, divisions=6, value=self.angle_a,
                              active_color=WAVE_A,
                              on_change=lambda e: self.set_wave("angle_a", e.control.value)),
                ),
                self.slider_row(
                    "Wave B: direction", self.angle_b_text,
                    ft.Slider(min=0, max=90, divisions=6, value=self.angle_b,
                              active_color=WAVE_B,
                              on_change=lambda e: self.set_wave("angle", e.control.value)),
                ),
            ],
        )

        self.rebuild_summary = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)
        rebuild_body = ft.Column(
            spacing=10,
            controls=[
                self.slider_row(
                    "Waves used", self.kept_text,
                    ft.Slider(min=0, max=len(REBUILD_STEPS) - 1,
                              divisions=len(REBUILD_STEPS) - 1, value=3,
                              active_color=SUM_ACCENT,
                              on_change=lambda e: self.set_kept(
                                  REBUILD_STEPS[int(e.control.value)])),
                ),
                self.rebuild_summary,
                self.small_button("Check the maths", ft.Icons.FACT_CHECK,
                                  lambda e: self.run_check()),
            ],
        )

        return [
            self.panel("THE TWO WAVES", "Change them and watch the dots move.",
                       ft.Icons.WAVES, WAVE_A, waves_body),
            self.panel("THE REBUILD", "How many waves the photo needs.",
                       ft.Icons.AUTO_AWESOME_MOSAIC, SUM_ACCENT, rebuild_body),
        ]

    # =========================================================
    # STATE
    # =========================================================

    def apply_chapter_state(self, chapter):
        self.show(self.waves_row, chapter <= 1)
        self.show(self.wave_b_card, chapter == 1)
        self.show(self.plus_slot, chapter == 1)
        self.show(self.sum_card, chapter == 1)
        self.show(self.plot_card, chapter <= 1)
        self.show(self.spectrum_row, chapter in (0, 3))
        self.show(self.rebuild_row, chapter in (2, 4))
        self.show(self.guide_row, chapter == 3)
        self.show(self.compare_row, chapter == 3)

        if chapter <= 1:
            self._refresh_waves(show_sum=chapter == 1)
        if chapter == 3:
            self._refresh_measure()
            self.spectrum_image.src = palette.png_bytes(
                self.trace.spectrum_image, scale=2)
            self.spectrum_note.value = "a real photograph needs dots everywhere"
        if chapter in (2, 4):
            self._refresh_rebuild()

        self._sync_labels()

    def _sync_labels(self):
        self.spacing_a_text.value = f"{int(self.spacing_a)} px apart"
        self.spacing_b_text.value = f"{int(self.spacing_b)} px apart"
        self.angle_a_text.value = f"{int(self.angle_a)}°"
        self.angle_b_text.value = f"{int(self.angle_b)}°"
        self.kept_text.value = f"{self.kept:,}"

    def _refresh_waves(self, show_sum=False):
        wave_a = self._wave_a()
        self.wave_a_image.src = palette.png_bytes(wave_a, scale=2)
        self.wave_a_note.value = f"{int(self.spacing_a)} px between bands"

        wave_b = self._wave_b()
        self.wave_b_image.src = palette.png_bytes(wave_b, scale=2)
        self.wave_b_note.value = (
            f"{int(self.spacing_b)} px  ·  {int(self.angle_b)}°"
        )

        if show_sum:
            total = self._sum_wave()
            self.sum_image.src = palette.png_bytes(total, scale=2)
            self.sum_note.value = "two waves, one picture"
            self._draw_plot(total, SUM_ACCENT,
                            "the two waves added: bumpy, but still just waves")
        else:
            self.spectrum_image.src = palette.png_bytes(
                self._spectrum_of(wave_a), scale=2)
            self.spectrum_note.value = "one wave  →  one pair of dots"
            self._draw_plot(wave_a, WAVE_A,
                            "brightness rises and falls: that is all a wave is")

    def _refresh_measure(self):
        """Redraw the measured pair from the current wave A."""
        picture = self._wave_a()
        marked, info = self._annotated_spectrum(picture)

        self.measured_stripes.src = palette.png_bytes(picture, scale=2)
        self.measured_spectrum.src = self._rgb_png(marked)

        self.measure_lines["bands"].value = f"{int(self.spacing_a)} px apart"
        self.measure_lines["steps"].value = f"{info['radius']:.0f} steps out"
        product = info["radius"] * self.spacing_a
        joiner = "=" if abs(product - self.size) < 1.0 else "≈"
        self.measure_lines["check"].value = (
            f"{info['radius']:.0f} × {int(self.spacing_a)} {joiner} {self.size}"
        )
        self.measure_lines["angle"].value = (
            f"{int(self.angle_a)}°  →  dot at {info['angle']:.0f}°"
        )

    def _refresh_rebuild(self):
        quality = self.trace.reconstruction_quality(self.kept)
        self.rebuilt_image.src = palette.png_bytes(quality["image"], scale=2)

        if self.kept >= self.trace.spectrum.size:
            self.rebuilt_note.value = f"{self.kept:,} waves  ·  exact"
        else:
            self.rebuilt_note.value = (
                f"{self.kept:,} waves  ·  {quality['psnr']:.1f} dB"
            )

        self.rebuild_summary.value = (
            f"{quality['count']:,} of {self.trace.spectrum.size:,} waves — "
            f"{quality['percent']:.1f}% — carry "
            f"{quality['energy'] * 100:.0f}% of the picture."
        )

    # =========================================================
    # ACTIONS
    # =========================================================

    def set_wave(self, which, value):
        self.timeline.cancel()

        if which == "a":
            self.spacing_a = int(value)
        elif which == "b":
            self.spacing_b = int(value)
        elif which == "angle_a":
            self.angle_a = int(value)
        else:
            self.angle_b = int(value)

        if self.chapter == 3:
            # In the measuring chapter the sliders drive the measurement.
            self._refresh_measure()
            self._sync_labels()
            info = peak_info(self._wave_a())
            self.caption_text.value = (
                f"{int(self.spacing_a)} px bands at {int(self.angle_a)}°: the dot "
                f"sits {info['radius']:.0f} steps out, at {info['angle']:.0f}°."
            )
            self.safe_update(self.control)
            return

        self.show(self.waves_row, True)
        self.show(self.plot_card, True)
        showing_sum = self.chapter == 1
        self._refresh_waves(show_sum=showing_sum)
        self._sync_labels()

        if which == "a":
            self.caption_text.value = (
                f"Wider bands mean a slower wave, and its dots sit closer to "
                f"the centre. Now {int(self.spacing_a)} px apart."
            )
        elif which == "b":
            self.caption_text.value = (
                f"Wave B is now {int(self.spacing_b)} px apart — finer stripes, "
                f"dots further out."
            )
        else:
            self.caption_text.value = (
                f"Turn the stripes to {int(self.angle_b)}° and their dots turn "
                f"with them."
            )

        self.safe_update(self.control)

    def set_kept(self, count):
        self.timeline.cancel()
        self.kept = int(count)
        self.show(self.rebuild_row, True)
        self._refresh_rebuild()
        self._sync_labels()

        quality = self.trace.reconstruction_quality(self.kept)
        self.caption_text.value = (
            f"{self.kept:,} waves added together, and the planet is at "
            f"{quality['psnr']:.1f} dB."
            if self.kept < self.trace.spectrum.size
            else "Every wave added: the photograph is back, exactly."
        )
        self.safe_update(self.control)

    def run_check(self):
        self.timeline.cancel()
        checks = self.trace.verify()

        self.rebuild_summary.value = (
            "The app's own 2D DFT matches NumPy's FFT"
            f" ({'yes' if checks['manual_matches_fft'] else 'no'}), all waves "
            f"rebuild the picture exactly"
            f" ({'yes' if checks['all_coefficients_rebuild_image'] else 'no'})."
        )
        self.caption_text.value = (
            "Every number here comes from the app's own transform, checked "
            "against NumPy."
        )
        self.safe_update(self.control)

    # =========================================================
    # SCENES
    # =========================================================

    def scenes(self):
        return [self._scene_one_wave, self._scene_two_waves,
                self._scene_many_waves, self._scene_reading, self._scene_why]

    # ---------------- 1 ----------------

    async def _scene_one_wave(self, gen):
        tl = self.timeline

        self.show(self.wave_b_card, False)
        self.show(self.plus_slot, False)
        self.show(self.sum_card, False)
        self.show(self.rebuild_row, False)
        self.show(self.guide_row, False)
        self.show(self.waves_row, True)
        self.show(self.spectrum_row, True)
        self.show(self.plot_card, True)
        self.spacing_a = 24
        self._refresh_waves()
        self._sync_labels()
        tl.push(gen, self.control)

        await self.say(gen, "This is a wave. Not a formula — a picture of one: "
                            "bright bands and dark bands, evenly spaced.",
                       self.step_label(0), hold=4.6)

        await self.say(gen, "Read one line across it and the brightness simply "
                            "rises and falls, over and over. That is the whole "
                            "idea of a wave.", hold=5.0)

        await self.say(gen, f"Two numbers describe it completely: how far apart "
                            f"the bands are ({int(self.spacing_a)} px here) and "
                            f"which way they run.", hold=5.0)

        await self.say(gen, "And here is the useful part. A wave's spectrum is "
                            "almost empty: one wave makes exactly one pair of "
                            "bright dots.", hold=5.0)

        for spacing in (36, 12, 6, 24):
            self.spacing_a = spacing
            self._refresh_waves()
            self._sync_labels()
            tl.push(gen, self.control)
            await self.say(gen, f"{spacing} px between bands — watch the dots move "
                                f"{'outward' if spacing < 24 else 'inward'}.",
                           hold=2.8)

        await self.say(gen, "Closer stripes push the dots further from the centre. "
                            "That single rule is most of what a spectrum means.",
                       hold=5.0)

    # ---------------- 2 ----------------

    async def _scene_two_waves(self, gen):
        tl = self.timeline

        self.show(self.spectrum_row, False)
        self.show(self.wave_b_card, True)
        self.show(self.plus_slot, True)
        self.show(self.sum_card, True)
        self.spacing_b = 10
        self.angle_b = 90
        self._refresh_waves(show_sum=True)
        self._sync_labels()
        tl.push(gen, self.control)

        await self.say(gen, "Now take a second wave: finer stripes, turned "
                            "sideways.", self.step_label(1), hold=4.0)

        await self.say(gen, "Add the two pictures together, pixel by pixel. Bright "
                            "plus bright makes brighter, bright plus dark cancels "
                            "out.", hold=5.0)

        await self.say(gen, "The result already looks like a woven texture — and "
                            "neither wave was lost. Both are still in there.",
                       hold=5.0)

        for spacing, angle in ((6, 90), (16, 45), (10, 90)):
            self.spacing_b = spacing
            self.angle_b = angle
            self._refresh_waves(show_sum=True)
            self._sync_labels()
            tl.push(gen, self.control)
            await self.say(gen, f"Change wave B to {spacing} px at {angle}° and the "
                                f"pattern changes with it.", hold=3.2)

        await self.say(gen, "Two waves give a pattern. The obvious question is how "
                            "far this goes.", hold=4.2)

    # ---------------- 3 ----------------

    async def _scene_many_waves(self, gen):
        tl = self.timeline

        self.show(self.waves_row, False)
        self.show(self.plot_card, False)
        self.show(self.spectrum_row, False)
        self.show(self.rebuild_row, True)
        tl.push(gen, self.control)

        await self.say(gen, "All the way. Any photograph is a stack of these "
                            "stripe patterns, added together.",
                       self.step_label(2), hold=4.6)

        for count in REBUILD_STEPS:
            self.kept = count
            self._refresh_rebuild()
            self._sync_labels()
            tl.push(gen, self.control)

            quality = self.trace.reconstruction_quality(count)
            if count == 1:
                text = "One wave: a flat grey square. Not much of a planet yet."
            elif count <= 20:
                text = (f"{count} waves and there is a blob in roughly the right "
                        f"place.")
            elif count <= 600:
                text = (f"{count} waves: the ring appears — "
                        f"{quality['psnr']:.1f} dB.")
            elif count < self.trace.spectrum.size:
                text = (f"{count:,} waves, and it is hard to tell from the "
                        f"original.")
            else:
                text = "All 9,216, and it is the original, exactly."

            await self.say(gen, text, hold=3.4)

        await self.say(gen, "That is the claim, and you just watched it happen: "
                            "the photograph was never anything but waves.",
                       hold=5.0)

    # ---------------- 4 ----------------

    async def _scene_reading(self, gen):
        tl = self.timeline

        self.show(self.rebuild_row, False)
        self.show(self.spectrum_row, False)
        self.show(self.compare_row, False)
        self.show(self.guide_row, True)

        self.spacing_a = 24
        self.angle_a = 0
        self._refresh_measure()
        self._sync_labels()
        tl.push(gen, self.control)

        await self.say(gen, "One dot, measured properly. The cross marks the "
                            "centre; the ring marks the dot; the line between "
                            "them is what we are measuring.",
                       self.step_label(3), hold=5.4)

        await self.say(gen, "Count the line in steps, where one step means one "
                            "stripe across the whole picture. Right now the dot "
                            "is 4 steps out, and the bands are 24 px apart.",
                       hold=5.6)

        await self.say(gen, f"4 × 24 = {self.size}, the width of the picture. "
                            f"That is not a coincidence: 4 steps *means* four "
                            f"stripes fit across, so each one is a quarter of "
                            f"the width.", hold=6.0)

        # Halve the spacing twice; the number doubles each time.
        for spacing in (12, 6):
            self.spacing_a = spacing
            self._refresh_measure()
            self._sync_labels()
            tl.push(gen, self.control)

            info = peak_info(self._wave_a())
            await self.say(gen, f"Halve the bands to {spacing} px and the dot "
                                f"doubles its distance: {info['radius']:.0f} steps. "
                                f"{info['radius']:.0f} × {spacing} is still "
                                f"{self.size}.", hold=5.2)

        self.show(self.compare_row, True)
        tl.push(gen, self.control)
        await self.say(gen, "All three together: finer stripes, dot further out. "
                            "Nothing to judge by eye — the number is written "
                            "under each one.", hold=5.2)

        # Now the second reading: direction.
        self.spacing_a = 12
        for angle in (0, 45, 90):
            self.angle_a = angle
            self._refresh_measure()
            self._sync_labels()
            tl.push(gen, self.control)

            info = peak_info(self._wave_a())
            await self.say(gen, f"Turn the stripes to {angle}° and the dot turns "
                                f"to {info['angle']:.0f}°. The dot always points "
                                f"the way the stripes run.", hold=4.4)

        self.angle_a = 0
        self._refresh_measure()
        self._sync_labels()
        self.show(self.compare_row, False)
        self.show(self.spectrum_row, True)
        self.spectrum_image.src = palette.png_bytes(self.trace.spectrum_image,
                                                    scale=2)
        self.spectrum_note.value = "thousands of dots, all at once"
        tl.push(gen, self.control)

        await self.say(gen, "So a photograph's spectrum is just thousands of those "
                            "measurements at once, each dot one stripe pattern.",
                       hold=5.2)

        await self.say(gen, "Bright in the middle means mostly wide, gentle "
                            "shading. The faint haze further out is the edges: "
                            "fewer of those, but they are what makes it sharp.",
                       hold=5.8)

    # ---------------- 5 ----------------

    async def _scene_why(self, gen):
        tl = self.timeline

        self.show(self.guide_row, False)
        self.show(self.rebuild_row, True)
        self.kept = 100
        self._refresh_rebuild()
        self._sync_labels()
        tl.push(gen, self.control)

        await self.say(gen, "Once a picture is a list of waves, editing the list "
                            "edits the picture. That is the whole frequency side "
                            "of this app.", self.step_label(4), hold=5.4)

        await self.say(gen, "Keep only the waves near the centre and you have "
                            "thrown away the detail: that is a blur.", hold=4.8)

        await self.say(gen, "Keep only the ones far out and you are left with the "
                            "edges.", hold=4.2)

        quality = self.trace.reconstruction_quality(100)
        await self.say(gen, f"Keep only the strongest few and you have compression: "
                            f"100 waves out of {self.trace.spectrum.size:,} already "
                            f"carry {quality['energy'] * 100:.0f}% of this picture.",
                       hold=5.6)

        await self.say(gen, "Filtering, hybrids, compression, texture, colour — "
                            "every one of them is a different way of choosing from "
                            "the same list.", hold=5.2)

"""Discover · Lesson 7 — Keeping only the loudest waves.

Lesson 6 chose waves by *where* they sit. This one chooses by *how
strong* they are, which is the whole idea behind image compression.

The lesson's spine is a single measured fact about this picture:
sixty-five coefficients out of 9,216 carry 90% of its energy. Once
that is on screen, "throw away the quiet ones" stops sounding reckless.

Chapters
    1  Most waves are nearly silent   the ranked list, and the top one
    2  Keep the loudest few           quality climbing as more are kept
    3  How few is enough?             counts for 90, 95 and 99% energy
    4  What you actually lose         the error, and where it hides
    5  This is what JPEG does         the idea in the wild, honestly

Every number comes from CompressionTrace, which is checked against the
project's own compress_dft.
"""

import flet as ft
import flet.canvas as fc
import numpy as np

from algorithms.learning.frequency_trace import CompressionTrace
from ui.learning import palette
from ui.learning.lesson_shell import LessonShell, mono
from ui.theme import AppColors


PANEL = 188
CURVE_W, CURVE_H = 620, 150

KEPT_ACCENT = palette.PRODUCT
LOST_ACCENT = palette.KERNEL
SOURCE_ACCENT = palette.INPUT

PERCENT_STEPS = (0.1, 0.5, 1, 2, 5, 10, 25, 50, 100)


class LearnCompressionView(LessonShell):
    CHAPTERS = [
        "Most waves are silent",
        "Keep the loudest few",
        "How few is enough?",
        "What you lose",
        "This is what JPEG does",
    ]
    ACCENT = palette.PRODUCT
    BADGE = "DISCOVER  •  LESSON 7"
    TITLE = "Keeping only the loudest waves"
    SUBTITLE = "Sixty-five waves out of 9,216 carry ninety percent of this picture."

    def __init__(self, page):
        super().__init__(page)

        self.trace = CompressionTrace()
        self.percent = 5.0
        self.result = self.trace.at_percent(self.percent)
        self.curve = self.trace.curve(30)

        self.build()
        self.set_chapter_state(0, first_build=True)

    # =========================================================
    # STAGE
    # =========================================================

    def build_stage(self):
        self.original_image = self._picture(self.trace.image)
        self.kept_image = self._picture(self.result["image"])
        self.spectrum_image = self._picture(self.result["kept_spectrum"])
        self.error_image = self._picture(self._error_picture())

        self.kept_note = ft.Text("", **mono(11, KEPT_ACCENT))
        self.spectrum_note = ft.Text("", size=9, color=AppColors.MUTED)
        self.error_note = ft.Text("", **mono(10, LOST_ACCENT))

        self.original_card = self.picture_card(
            self.original_image, "THE ORIGINAL", SOURCE_ACCENT)
        self.kept_card = self.picture_card(
            self.kept_image, "REBUILT FROM WHAT WE KEPT", KEPT_ACCENT,
            self.kept_note)
        self.spectrum_card = self.picture_card(
            self.spectrum_image, "KEPT  ·  the largest |F(u,v)|", palette.KERNEL_FRAME,
            self.spectrum_note)
        self.error_card = self.picture_card(
            self.error_image, "WHAT WENT MISSING", LOST_ACCENT, self.error_note)
        self.show(self.error_card, False)

        pictures = self.row([self.original_card, self.spectrum_card,
                             self.kept_card, self.error_card])

        # ---- the energy curve ----
        self.curve_canvas = fc.Canvas(width=CURVE_W, height=CURVE_H, shapes=[])
        self.curve_note = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)
        self.curve_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=14,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text("ENERGY CAPTURED AS MORE WAVES ARE KEPT", size=9,
                            weight=ft.FontWeight.BOLD, color=KEPT_ACCENT),
                    self.curve_canvas,
                    self.curve_note,
                ],
            ),
        )
        self._draw_curve()

        # ---- the milestone table ----
        self.milestone_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=True, spacing=12, run_spacing=12,
            controls=[],
        )
        self.milestone_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=self.milestone_row,
        )
        self._build_milestones()

        return [pictures, self.curve_card, self.milestone_card]

    def _picture(self, array, size=PANEL):
        return ft.Image(
            src=palette.png_bytes(array, scale=2),
            width=size, height=size,
            fit=ft.BoxFit.FILL, border_radius=12, gapless_playback=True,
        )

    def _error_picture(self):
        """Where the rebuilt picture differs from the original."""
        difference = np.abs(
            self.result["image"].astype(np.float64)
            - self.trace.image.astype(np.float64)
        )
        top = max(1.0, difference.max())
        return np.clip(np.round(difference / top * 255), 0, 255).astype(np.uint8)

    def _build_milestones(self):
        chips = []
        for fraction in (0.50, 0.90, 0.95, 0.99):
            count = self.trace.count_for_energy(fraction)
            quality = self.trace.at_count(count)

            chips.append(ft.Container(
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                border_radius=12,
                bgcolor=AppColors.SURFACE_3,
                border=ft.Border.all(1, palette.argb("55", KEPT_ACCENT)),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=3,
                    controls=[
                        ft.Text(f"{fraction * 100:.0f}% of the energy", size=9,
                                color=AppColors.MUTED),
                        ft.Text(f"{count:,}", **mono(18, KEPT_ACCENT)),
                        ft.Text(f"waves  ·  {quality['percent']:.2f}%  ·  "
                                f"{quality['psnr']:.1f} dB",
                                size=9, color=AppColors.TEXT_SECONDARY),
                    ],
                ),
            ))
        self.milestone_row.controls = chips

    def _draw_curve(self, marker=None):
        shapes = []
        margin = 10

        def x_of(count):
            return margin + (np.log10(count) / np.log10(self.trace.total)) * (
                CURVE_W - 2 * margin)

        def y_of(energy):
            return CURVE_H - margin - energy * (CURVE_H - 2 * margin)

        for level in (0.5, 0.9, 1.0):
            y = y_of(level)
            shapes.append(fc.Path(
                elements=[fc.Path.MoveTo(0, y), fc.Path.LineTo(CURVE_W, y)],
                paint=ft.Paint(style=ft.PaintingStyle.STROKE, stroke_width=1,
                               color="#1E2C46"),
            ))

        points = [(item["count"], item["energy"]) for item in self.curve]
        elements = [fc.Path.MoveTo(x_of(points[0][0]), y_of(points[0][1]))]
        for count, energy in points[1:]:
            elements.append(fc.Path.LineTo(x_of(count), y_of(energy)))

        shapes.append(fc.Path(
            elements=elements,
            paint=ft.Paint(style=ft.PaintingStyle.STROKE, stroke_width=2.6,
                           color=KEPT_ACCENT),
        ))

        if marker:
            x = x_of(max(1, marker["count"]))
            shapes.append(fc.Path(
                elements=[fc.Path.MoveTo(x, 0), fc.Path.LineTo(x, CURVE_H)],
                paint=ft.Paint(style=ft.PaintingStyle.STROKE, stroke_width=1.6,
                               color=palette.argb("AA", SOURCE_ACCENT)),
            ))
            shapes.append(fc.Circle(
                x, y_of(marker["energy"]), 5,
                paint=ft.Paint(color=SOURCE_ACCENT),
            ))

        self.curve_canvas.shapes = shapes
        self.curve_note.value = (
            "left edge: one wave   ·   right edge: all 9,216   ·   "
            "the line reaches 90% long before the halfway mark"
        )

    # =========================================================
    # PANELS
    # =========================================================

    def side_panels(self):
        self.percent_text = ft.Text("", **mono(11, KEPT_ACCENT))
        self.quality_text = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)

        keep_body = ft.Column(
            spacing=10,
            controls=[
                self.slider_row(
                    "Waves kept", self.percent_text,
                    ft.Slider(min=0, max=len(PERCENT_STEPS) - 1,
                              divisions=len(PERCENT_STEPS) - 1, value=4,
                              active_color=KEPT_ACCENT,
                              on_change=lambda e: self.set_percent(
                                  PERCENT_STEPS[int(e.control.value)])),
                ),
                self.quality_text,
                ft.Row(
                    spacing=8,
                    controls=[
                        self.small_button("90% energy", ft.Icons.BOLT,
                                          lambda e: self.set_energy(0.90)),
                        self.small_button("99% energy", ft.Icons.BOLT,
                                          lambda e: self.set_energy(0.99)),
                    ],
                ),
            ],
        )

        self.check_text = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)
        check_body = ft.Column(
            spacing=10,
            controls=[
                self.check_text,
                self.small_button("Check against the app's compressor",
                                  ft.Icons.FACT_CHECK,
                                  lambda e: self.run_check()),
            ],
        )

        return [
            self.panel("HOW MUCH TO KEEP", "Strongest waves first.",
                       ft.Icons.COMPRESS, KEPT_ACCENT, keep_body),
            self.panel("THE NUMBERS", "Where the claims come from.",
                       ft.Icons.RULE, SOURCE_ACCENT, check_body),
        ]

    # =========================================================
    # STATE
    # =========================================================

    def apply_chapter_state(self, chapter):
        self.show(self.spectrum_card, chapter >= 1)
        self.show(self.kept_card, chapter >= 1)
        self.show(self.error_card, chapter >= 3)
        self.show(self.curve_card, chapter == 2)
        self.show(self.milestone_card, chapter >= 2)

        if chapter == 0:
            self.percent = 0.1
        self._refresh()

    def _refresh(self):
        self.result = self.trace.at_percent(self.percent)

        self.kept_image.src = palette.png_bytes(self.result["image"], scale=2)
        self.spectrum_image.src = palette.png_bytes(
            self.result["kept_spectrum"], scale=2)
        self.error_image.src = palette.png_bytes(self._error_picture(), scale=2)

        self.kept_note.value = (
            f"{self.result['count']:,} waves  ·  {self.result['psnr']:.1f} dB"
        )
        self.spectrum_note.value = (
            f"{self.result['discarded']:,} of {self.trace.total:,} deleted"
        )
        self.error_note.value = (
            f"brightest where the edges are"
        )
        self.percent_text.value = f"{self.result['percent']:.2f}%"
        self.quality_text.value = (
            f"{self.result['count']:,} of {self.trace.total:,} waves hold "
            f"{self.result['energy'] * 100:.1f}% of the energy, at "
            f"{self.result['psnr']:.1f} dB."
        )
        self._draw_curve(marker=self.result)

    # =========================================================
    # ACTIONS
    # =========================================================

    def set_percent(self, percent):
        self.timeline.cancel()
        self.percent = float(percent)
        self.show(self.kept_card, True)
        self.show(self.spectrum_card, True)
        self._refresh()
        self.caption_text.value = (
            f"Keeping the strongest {self.result['percent']:.2f}% — "
            f"{self.result['count']:,} waves — gives "
            f"{self.result['psnr']:.1f} dB."
        )
        self.safe_update(self.control)

    def set_energy(self, fraction):
        self.timeline.cancel()
        count = self.trace.count_for_energy(fraction)
        self.percent = 100.0 * count / self.trace.total
        self.show(self.kept_card, True)
        self.show(self.spectrum_card, True)
        self._refresh()
        self.caption_text.value = (
            f"{count:,} waves — {self.result['percent']:.2f}% of them — already "
            f"hold {fraction * 100:.0f}% of the picture's energy."
        )
        self.safe_update(self.control)

    def run_check(self):
        self.timeline.cancel()
        checks = self.trace.verify(self.percent)

        self.check_text.value = (
            f"Matches the app's compress_dft: "
            f"{'yes' if checks['matches_project_compressor'] else 'no'}. "
            f"Quality never drops as more waves are kept: "
            f"{'yes' if checks['quality_improves_monotonically'] else 'no'}. "
            f"90% of the energy needs "
            f"{checks['coefficients_for_90_percent']:,} waves."
        )
        self.caption_text.value = (
            "Every number in this lesson was produced by the app's own "
            "compressor, not by a second implementation."
        )
        self.safe_update(self.control)

    # =========================================================
    # SCENES
    # =========================================================

    def scenes(self):
        return [self._scene_silent, self._scene_keep, self._scene_howfew,
                self._scene_lose, self._scene_jpeg]

    async def _scene_silent(self, gen):
        tl = self.timeline

        self.show(self.kept_card, False)
        self.show(self.spectrum_card, False)
        self.show(self.error_card, False)
        self.show(self.curve_card, False)
        self.show(self.milestone_card, False)
        tl.push(gen, self.control)

        await self.say(gen, "This picture is 9,216 waves added together. Here is "
                            "the part nobody expects.", self.step_label(0), hold=4.0)

        self.percent = 0.1
        self._refresh()
        self.show(self.kept_card, True)
        self.show(self.spectrum_card, True)
        tl.push(gen, self.control)
        await tl.wait(gen, 2.0)

        strongest = self.trace.at_count(1)
        await self.say(gen, f"Almost all of them are nearly silent. The single "
                            f"strongest wave alone carries "
                            f"{strongest['energy'] * 100:.0f}% of the energy.",
                       hold=5.0)

        await self.say(gen, "So instead of choosing waves by where they sit, choose "
                            "them by how loud they are: sort every wave by strength "
                            "and keep the top of the list.", hold=5.2)

    async def _scene_keep(self, gen):
        tl = self.timeline

        await self.say(gen, "Watch the picture come back as we keep more of them.",
                       self.step_label(1), hold=0.4)

        for percent in PERCENT_STEPS:
            self.percent = percent
            self._refresh()
            tl.push(gen, self.control)

            if percent <= 0.5:
                text = (f"{self.result['count']:,} waves: the planet is a smudge, "
                        f"but it is there.")
            elif percent <= 5:
                text = (f"{self.result['percent']:.0f}% of the waves — "
                        f"{self.result['count']:,} — and the ring is back: "
                        f"{self.result['psnr']:.1f} dB.")
            elif percent < 100:
                text = (f"{self.result['percent']:.0f}%: "
                        f"{self.result['psnr']:.1f} dB, and the deleted waves are "
                        f"getting hard to miss.")
            else:
                text = "Everything kept, which is not compression at all."

            await self.say(gen, text, hold=3.2)

        await self.say(gen, "Notice how early it stopped looking broken. That is "
                            "the whole opportunity.", hold=4.2)

    async def _scene_howfew(self, gen):
        tl = self.timeline

        self.show(self.curve_card, True)
        self.show(self.milestone_card, True)
        self._draw_curve(marker=self.result)
        tl.push(gen, self.control)

        await self.say(gen, "So how few is enough? Put the energy on a graph.",
                       self.step_label(2), hold=3.6)

        await self.say(gen, "Left edge is one wave, right edge is all 9,216. The "
                            "line shoots up immediately and then crawls.", hold=4.6)

        for fraction in (0.50, 0.90, 0.99):
            count = self.trace.count_for_energy(fraction)
            quality = self.trace.at_count(count)
            self.percent = 100.0 * count / self.trace.total
            self._refresh()
            tl.push(gen, self.control)

            await self.say(gen, f"{fraction * 100:.0f}% of the energy needs only "
                                f"{count:,} waves — {quality['percent']:.2f}% of "
                                f"them — at {quality['psnr']:.1f} dB.", hold=4.6)

        await self.say(gen, "Ninety percent of this picture fits in sixty-five "
                            "numbers. That is the sentence the whole field is built "
                            "on.", hold=5.0)

    async def _scene_lose(self, gen):
        tl = self.timeline

        self.percent = 1.0
        self._refresh()
        self.show(self.error_card, True)
        self.show(self.curve_card, False)
        tl.push(gen, self.control)

        await self.say(gen, "Nothing is free. Here is exactly what the deleted "
                            "waves were carrying.", self.step_label(3), hold=4.0)

        await self.say(gen, "The error picture is brightest along the ring, the "
                            "planet's rim and the stars — every hard edge.",
                       hold=4.8)

        await self.say(gen, "That makes sense: edges are where the fast waves live, "
                            "and fast waves are the quiet ones we deleted.",
                       hold=4.8)

        await self.say(gen, "Flat areas survive perfectly. Detail is what "
                            "compression spends first.", hold=4.4)

    async def _scene_jpeg(self, gen):
        tl = self.timeline

        self.percent = 5.0
        self._refresh()
        self.show(self.error_card, True)
        self.show(self.milestone_card, True)
        tl.push(gen, self.control)

        await self.say(gen, "This is, in outline, what JPEG does to every photograph "
                            "you have ever opened.", self.step_label(4), hold=4.4)

        await self.say(gen, "It transforms the image, keeps the strong low "
                            "frequencies, and throws away the weak high ones.",
                       hold=4.6)

        await self.say(gen, "Two honest differences. JPEG works on 8×8 blocks rather "
                            "than the whole picture, and it uses a cosine transform, "
                            "which avoids complex numbers.", hold=5.4)

        await self.say(gen, "And instead of a hard cut-off it divides each "
                            "coefficient by a quality table, which rounds the quiet "
                            "ones to zero — a gentler version of the same choice.",
                       hold=5.6)

        await self.say(gen, "Same idea underneath: most waves are silent, so stop "
                            "storing them.", hold=4.4)

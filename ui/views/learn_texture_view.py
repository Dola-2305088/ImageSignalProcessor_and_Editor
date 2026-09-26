"""Discover · Lesson 8 — Reading a texture.

The other lessons edit the spectrum. This one only reads it, and the
reward is that two questions a person would otherwise answer by eye —
"how far apart are these threads?" and "which way do they run?" — get
answered by a single bright dot.

The patterns are generated with a known spacing and angle, so the
lesson can put the app's answer next to the truth on every screen.
That is the student-friendly part: nothing has to be taken on trust.

Chapters
    1  A pattern is a repeat     cloth, and its two bright dots
    2  Closer threads, further   spacing becomes distance from centre
    3  Turn it, and it turns     rotating the cloth rotates the spectrum
    4  Three real textures       cloth, brick, grass, each measured
    5  Measuring without eyes    what the app does, in one sentence
"""

import flet as ft

from algorithms.learning.texture_colour_trace import TEXTURES, TextureTrace
from ui.learning import palette
from ui.learning.lesson_shell import LessonShell, mono
from ui.theme import AppColors


PANEL = 188
MINI = 128

PATTERN_ACCENT = palette.INPUT
SPECTRUM_ACCENT = palette.KERNEL_FRAME
TRUTH_ACCENT = "#34D399"
MEASURED_ACCENT = palette.PRODUCT


class LearnTextureView(LessonShell):
    CHAPTERS = [
        "A pattern is a repeat",
        "Closer threads, further out",
        "Turn it, and it turns",
        "Three real textures",
        "Measuring without eyes",
    ]
    ACCENT = palette.KERNEL_FRAME
    BADGE = "DISCOVER  •  LESSON 8"
    TITLE = "Reading a texture"
    SUBTITLE = "How far apart, and which way — answered by one bright dot."

    def __init__(self, page):
        super().__init__(page)

        self.trace = TextureTrace()
        self.kind = "Cloth"
        self.spacing = TEXTURES[self.kind][1]
        self.angle = 0

        self.current = self.trace.make(self.kind, self.spacing, self.angle)
        self.measured = self.trace.measure(self.current["image"])

        self.build()
        self.set_chapter_state(0, first_build=True)

    # =========================================================
    # STAGE
    # =========================================================

    def build_stage(self):
        self.pattern_image = self._picture(self.current["image"])
        self.spectrum_image = self._picture(self.current["spectrum"])

        self.pair_row = self.row([
            self.picture_card(self.pattern_image, "THE TEXTURE", PATTERN_ACCENT),
            self.slot(self.arrow("transform"), width=90),
            self.picture_card(self.spectrum_image, "SPECTRUM  ·  |F(u,v)|",
                              SPECTRUM_ACCENT),
        ])

        # ---- the scoreboard: what we built vs what the app measured ----
        self.truth_spacing = ft.Text("", **mono(17, TRUTH_ACCENT))
        self.truth_angle = ft.Text("", **mono(17, TRUTH_ACCENT))
        self.measured_spacing = ft.Text("", **mono(17, MEASURED_ACCENT))
        self.measured_angle = ft.Text("", **mono(17, MEASURED_ACCENT))
        self.measured_word = ft.Text("", **mono(17, MEASURED_ACCENT))

        self.scoreboard = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=16,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True, spacing=28, run_spacing=12,
                controls=[
                    self._score_column("WHAT WE BUILT", TRUTH_ACCENT,
                                       [("spacing", self.truth_spacing),
                                        ("angle", self.truth_angle)]),
                    ft.Icon(ft.Icons.COMPARE_ARROWS, size=26, color=AppColors.MUTED),
                    self._score_column("WHAT THE APP MEASURED", MEASURED_ACCENT,
                                       [("spacing", self.measured_spacing),
                                        ("angle", self.measured_angle),
                                        ("direction", self.measured_word)]),
                ],
            ),
        )

        # ---- the four-up comparison used in chapters 2, 3 and 4 ----
        self.series_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=True, spacing=12, run_spacing=12, controls=[],
        )
        self.series_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=self.series_row,
        )

        return [self.pair_row, self.scoreboard, self.series_card]

    def _picture(self, array, size=PANEL):
        return ft.Image(
            src=palette.png_bytes(array, scale=1),
            width=size, height=size,
            fit=ft.BoxFit.FILL, border_radius=12, gapless_playback=True,
        )

    @staticmethod
    def _score_column(title, accent, rows):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            controls=[
                ft.Text(title, size=9, weight=ft.FontWeight.BOLD, color=accent),
                *[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Text(label, size=10, color=AppColors.MUTED),
                            value,
                        ],
                    )
                    for label, value in rows
                ],
            ],
        )

    def _show_series(self, items, label_of):
        cards = []
        for item in items:
            cards.append(ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Container(
                                border_radius=10,
                                border=ft.Border.all(
                                    1, palette.argb("66", PATTERN_ACCENT)),
                                content=self._picture(item["image"], MINI),
                            ),
                            ft.Container(
                                border_radius=10,
                                border=ft.Border.all(
                                    1, palette.argb("66", SPECTRUM_ACCENT)),
                                content=self._picture(item["spectrum"], MINI),
                            ),
                        ],
                    ),
                    ft.Text(label_of(item), size=10,
                            color=AppColors.TEXT_SECONDARY),
                ],
            ))
        self.series_row.controls = cards

    # =========================================================
    # PANELS
    # =========================================================

    def side_panels(self):
        self.kind_buttons = {
            kind: self.small_button(kind, ft.Icons.TEXTURE,
                                    lambda e, k=kind: self.set_kind(k))
            for kind in TEXTURES
        }
        self.spacing_text = ft.Text("", **mono(11, PATTERN_ACCENT))
        self.angle_text = ft.Text("", **mono(11, SPECTRUM_ACCENT))

        pattern_body = ft.Column(
            spacing=10,
            controls=[
                ft.Row(spacing=8, controls=list(self.kind_buttons.values())),
                self.slider_row(
                    "Repeat spacing", self.spacing_text,
                    ft.Slider(min=4, max=28, divisions=12, value=self.spacing,
                              active_color=PATTERN_ACCENT,
                              on_change=lambda e: self.set_spacing(e.control.value)),
                ),
                self.slider_row(
                    "Turn the picture", self.angle_text,
                    ft.Slider(min=0, max=90, divisions=9, value=self.angle,
                              active_color=SPECTRUM_ACCENT,
                              on_change=lambda e: self.set_angle(e.control.value)),
                ),
            ],
        )

        self.verdict_text = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)
        check_body = ft.Column(
            spacing=10,
            controls=[
                self.verdict_text,
                self.small_button("Check every pattern", ft.Icons.FACT_CHECK,
                                  lambda e: self.run_check()),
            ],
        )

        return [
            self.panel("THE PATTERN", "Built to a known recipe.",
                       ft.Icons.GRID_GOLDENRATIO, PATTERN_ACCENT, pattern_body),
            self.panel("THE ANSWER", "Measured, then checked.",
                       ft.Icons.RULE, MEASURED_ACCENT, check_body),
        ]

    # =========================================================
    # STATE
    # =========================================================

    def apply_chapter_state(self, chapter):
        self.show(self.pair_row, True)
        self.scoreboard.opacity = 1.0 if chapter >= 1 else 0.0
        self.show(self.series_card, chapter in (1, 2, 3))

        if chapter == 1:
            self._show_series(self.trace.spacing_series(self.kind),
                              lambda item: f"{item['true_spacing']:.0f} px apart")
        elif chapter == 2:
            self._show_series(self.trace.rotation_series(self.kind),
                              lambda item: f"turned {item['true_angle']:.0f}°")
        elif chapter == 3:
            self._show_series(
                [self.trace.make(kind) for kind in TEXTURES],
                lambda item: item["kind"],
            )

        self._refresh()

    def _refresh(self):
        self.current = self.trace.make(self.kind, int(self.spacing), int(self.angle))
        self.measured = self.trace.measure(self.current["image"])

        self.pattern_image.src = palette.png_bytes(self.current["image"], scale=1)
        self.spectrum_image.src = palette.png_bytes(self.current["spectrum"], scale=1)

        self.truth_spacing.value = f"{self.current['true_spacing']:.0f} px"
        self.truth_angle.value = f"{self.current['true_angle']:.0f}°"
        self.measured_spacing.value = f"{self.measured['spacing']:.1f} px"
        self.measured_angle.value = f"{self.measured['angle']:.0f}°"
        self.measured_word.value = self.measured["orientation"]

        self.spacing_text.value = f"{int(self.spacing)} px"
        self.angle_text.value = f"{int(self.angle)}°"

    # =========================================================
    # ACTIONS
    # =========================================================

    def set_kind(self, kind):
        self.timeline.cancel()
        self.kind = kind
        self.spacing = TEXTURES[kind][1]
        self.scoreboard.opacity = 1.0
        self._refresh()
        self.caption_text.value = (
            f"{kind}: the app reads {self.measured['spacing']:.1f} px, "
            f"running {self.measured['orientation'].lower()}."
        )
        self.safe_update(self.control)

    def set_spacing(self, value):
        self.timeline.cancel()
        self.spacing = int(value)
        self.scoreboard.opacity = 1.0
        self._refresh()
        error = abs(self.measured["spacing"] - self.spacing)
        self.caption_text.value = (
            f"Built {self.spacing} px apart, measured "
            f"{self.measured['spacing']:.1f} px — off by {error:.1f}."
        )
        self.safe_update(self.control)

    def set_angle(self, value):
        self.timeline.cancel()
        self.angle = int(value)
        self.scoreboard.opacity = 1.0
        self._refresh()
        self.caption_text.value = (
            f"Turned {self.angle}°, and the app reads "
            f"{self.measured['angle']:.0f}° ({self.measured['orientation'].lower()})."
        )
        self.safe_update(self.control)

    def run_check(self):
        self.timeline.cancel()
        checks = self.trace.verify()

        self.verdict_text.value = (
            f"Spacing recovered within {checks['worst_spacing_error']:.1f} px on "
            f"every test pattern. Rotation tracked within "
            f"{checks['worst_rotation_error']:.1f}°."
        )
        self.caption_text.value = (
            "Every pattern in this lesson was built to a known recipe, so the "
            "app's answer can be checked rather than believed."
        )
        self.safe_update(self.control)

    # =========================================================
    # SCENES
    # =========================================================

    def scenes(self):
        return [self._scene_repeat, self._scene_spacing, self._scene_rotate,
                self._scene_real, self._scene_why]

    async def _scene_repeat(self, gen):
        tl = self.timeline

        self.scoreboard.opacity = 0.0
        self.show(self.series_card, False)
        self.kind = "Cloth"
        self.spacing = 8
        self.angle = 0
        self._refresh()
        tl.push(gen, self.control)

        await self.say(gen, "A piece of cloth. Threads crossing, evenly spaced — "
                            "the most ordinary texture there is.",
                       self.step_label(0), hold=4.2)

        await self.say(gen, "Evenly spaced is the important word. Something that "
                            "repeats is exactly what a wave is.", hold=4.4)

        await self.say(gen, "So its spectrum is not a haze. It is a few bright dots, "
                            "one pair for each direction the threads run.", hold=4.8)

        self.scoreboard.opacity = 1.0
        tl.push(gen, self.control)
        await self.say(gen, f"And the app reads those dots: threads "
                            f"{self.measured['spacing']:.0f} px apart. We built them "
                            f"{self.spacing} px apart.", hold=5.0)

    async def _scene_spacing(self, gen):
        tl = self.timeline

        self._show_series(self.trace.spacing_series(self.kind),
                          lambda item: f"{item['true_spacing']:.0f} px apart")
        self.show(self.series_card, True)
        tl.push(gen, self.control)

        await self.say(gen, "Now weave the same cloth at four different thread "
                            "spacings.", self.step_label(1), hold=3.6)

        await self.say(gen, "Look along the row. As the threads get closer together, "
                            "the dots move further out from the centre.", hold=4.8)

        await self.say(gen, "That is the rule from lesson 5, seen in the wild: "
                            "distance from the centre means fineness. Close threads "
                            "are fine detail.", hold=5.0)

        for made in self.trace.spacing_series(self.kind):
            self.spacing = int(made["true_spacing"])
            self._refresh()
            tl.push(gen, self.control)
            await self.say(gen, f"Built {made['true_spacing']:.0f} px apart, "
                                f"measured {made['measured']['spacing']:.1f}.",
                           hold=2.8)

        await self.say(gen, "Never more than a pixel or so out — and no one had to "
                            "look at the cloth to get it.", hold=4.2)

    async def _scene_rotate(self, gen):
        tl = self.timeline

        self._show_series(self.trace.rotation_series(self.kind),
                          lambda item: f"turned {item['true_angle']:.0f}°")
        self.show(self.series_card, True)
        tl.push(gen, self.control)

        await self.say(gen, "Now the second question: which way does it run?",
                       self.step_label(2), hold=3.2)

        await self.say(gen, "Turn the cloth, and watch the spectrum. It turns with "
                            "it, by the same amount, every time.", hold=4.6)

        for angle in (0, 20, 45, 70):
            self.angle = angle
            self._refresh()
            tl.push(gen, self.control)
            await self.say(gen, f"Turned {angle}°, measured "
                                f"{self.measured['angle']:.0f}° — "
                                f"{self.measured['orientation'].lower()}.", hold=3.0)

        await self.say(gen, "The spectrum is locked to the picture's orientation. "
                            "Find the brightest dot, take its angle, and you have "
                            "the direction of the weave.", hold=5.2)

    async def _scene_real(self, gen):
        tl = self.timeline

        self._show_series([self.trace.make(kind) for kind in TEXTURES],
                          lambda item: item["kind"])
        self.show(self.series_card, True)
        tl.push(gen, self.control)

        await self.say(gen, "Three textures, and three different-looking spectra.",
                       self.step_label(3), hold=3.6)

        for kind in TEXTURES:
            self.kind = kind
            self.spacing = TEXTURES[kind][1]
            self.angle = 0
            self._refresh()
            tl.push(gen, self.control)

            if kind == "Cloth":
                text = (f"Cloth repeats in two directions, so it has two pairs of "
                        f"dots: {self.measured['spacing']:.0f} px apart.")
            elif kind == "Brick":
                text = (f"Brick has strong courses and weaker joins, so one pair is "
                        f"much brighter: {self.measured['spacing']:.0f} px apart.")
            else:
                text = (f"Grass is irregular — no two blades are identical — so the "
                        f"dots are smeared into a smudge. The direction still reads "
                        f"clearly at {self.measured['spacing']:.0f} px.")

            await self.say(gen, text, hold=4.8)

        await self.say(gen, "Regular patterns give sharp dots, natural ones give "
                            "soft smudges. Both still point the right way.",
                       hold=4.6)

    async def _scene_why(self, gen):
        tl = self.timeline

        checks = self.trace.verify()
        self.verdict_text.value = (
            f"Spacing recovered within {checks['worst_spacing_error']:.1f} px. "
            f"Rotation tracked within {checks['worst_rotation_error']:.1f}°."
        )
        tl.push(gen, self.control)

        await self.say(gen, "Here is what the texture feature actually does.",
                       self.step_label(4), hold=3.2)

        await self.say(gen, "Transform the picture, ignore the bright centre, find "
                            "the strongest remaining dot, and report its distance "
                            "and its angle.", hold=5.2)

        await self.say(gen, "That is the whole algorithm. No training, no examples, "
                            "no machine learning — just the position of one dot.",
                       hold=5.0)

        await self.say(gen, f"And it is accurate: across every pattern here, spacing "
                            f"came back within {checks['worst_spacing_error']:.1f} px "
                            f"and rotation within "
                            f"{checks['worst_rotation_error']:.1f}°.", hold=5.2)

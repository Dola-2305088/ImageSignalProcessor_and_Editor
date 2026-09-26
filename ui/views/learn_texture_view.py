"""Discover · Lesson 8 — Reading a texture.

Rebuilt in the same style as lesson 5: instead of telling you that a
dot's distance means fineness, the lesson measures it on screen and
shows the arithmetic.

Every pattern is generated to a known recipe, so three numbers can sit
side by side on every screen: what we built, what the dot says, and
what the app's own analyzer reports. Nothing has to be taken on trust.

    1  A repeat has a size      cloth, a ruler on it, and its two dots
    2  Closer threads, further  16 -> 8 -> 4 px, and the dot doubles
    3  Turn it and it turns     the dot follows the weave
    4  Real textures are messy  brick and grass, sharp dots vs smudges
    5  The whole algorithm      three sentences, no machine learning
"""

import flet as ft

from algorithms.learning.spectrum_trace import (
    annotate_spectrum,
    peak_info,
    ruler_overlay,
)
from algorithms.learning.texture_colour_trace import TEXTURES, TextureTrace
from ui.learning import palette
from ui.learning.lesson_shell import LessonShell, mono
from ui.theme import AppColors


PICTURE = 188
MINI = 104

PATTERN_ACCENT = palette.INPUT
SPECTRUM_ACCENT = palette.KERNEL_FRAME
BUILT_ACCENT = "#34D399"
APP_ACCENT = palette.PRODUCT

# Spacings that divide the 128 px pattern exactly, so "steps × spacing
# = 128" is always literally true.
SPACING_STEPS = (4, 8, 16)
ANGLES = (0, 30, 45, 60, 90)


class LearnTextureView(LessonShell):
    CHAPTERS = [
        "A repeat has a size",
        "Closer threads, further out",
        "Turn it and it turns",
        "Real textures are messier",
        "The whole algorithm",
    ]
    ACCENT = palette.KERNEL_FRAME
    BADGE = "DISCOVER  •  LESSON 8"
    TITLE = "Reading a texture"
    SUBTITLE = "How far apart the threads are, and which way they run — from one dot."

    def __init__(self, page):
        super().__init__(page)

        self.trace = TextureTrace()
        self.size = self.trace.size

        self.kind = "Cloth"
        self.spacing = 8
        self.angle = 0

        self.build()
        self.set_chapter_state(0, first_build=True)

    # =========================================================
    # STAGE
    # =========================================================

    def build_stage(self):
        made = self._make()

        self.pattern_image = self._picture(
            ruler_overlay(made["image"], self.spacing, self.angle))
        marked, info = annotate_spectrum(made["image"])
        self.spectrum_image = ft.Image(
            src=self._rgb_png(marked),
            width=PICTURE, height=PICTURE,
            fit=ft.BoxFit.FILL, border_radius=12, gapless_playback=True,
        )

        self.pattern_note = ft.Text("", **mono(11, PATTERN_ACCENT))
        self.spectrum_note = ft.Text("", **mono(11, SPECTRUM_ACCENT))

        self.measure_lines = {
            "threads": ft.Text("", **mono(15, PATTERN_ACCENT)),
            "dot": ft.Text("", **mono(15, SPECTRUM_ACCENT)),
            "check": ft.Text("", **mono(15, BUILT_ACCENT)),
            "tilt": ft.Text("", **mono(15, palette.KERNEL)),
            "app": ft.Text("", **mono(15, APP_ACCENT)),
        }

        self.measure_card = ft.Container(
            width=320,
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
                    self.card_title("WHAT THE DOT SAYS", SPECTRUM_ACCENT),
                    self._measure_row("Threads", self.measure_lines["threads"]),
                    self._measure_row("Dot sits", self.measure_lines["dot"]),
                    ft.Divider(height=1, color="#1E2C46"),
                    self._measure_row("So", self.measure_lines["check"]),
                    self._measure_row("Tilt", self.measure_lines["tilt"]),
                    ft.Divider(height=1, color="#1E2C46"),
                    self._measure_row("The app reads", self.measure_lines["app"]),
                ],
            ),
        )

        self.main_row = self.row([
            self.picture_card(self.pattern_image, "THE TEXTURE", PATTERN_ACCENT,
                              self.pattern_note),
            self.slot(self.arrow("measure"), width=84),
            self.picture_card(self.spectrum_image, "ITS SPECTRUM",
                              SPECTRUM_ACCENT, self.spectrum_note),
            self.measure_card,
        ])

        # three spacings at a glance
        self.compare_row = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=self.row([self._compare_card(s) for s in SPACING_STEPS]),
        )

        # the three textures at a glance
        self.family_row = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=self.row([self._family_card(kind) for kind in TEXTURES]),
        )

        return [self.main_row, self.compare_row, self.family_row]

    def _picture(self, array, size=PICTURE):
        if getattr(array, "ndim", 2) == 3:
            return ft.Image(
                src=self._rgb_png(array),
                width=size, height=size,
                fit=ft.BoxFit.FILL, border_radius=12, gapless_playback=True,
            )
        return ft.Image(
            src=palette.png_bytes(array, scale=1),
            width=size, height=size,
            fit=ft.BoxFit.FILL, border_radius=12, gapless_playback=True,
        )

    @staticmethod
    def _rgb_png(array):
        from io import BytesIO

        import numpy as np
        from PIL import Image

        buffer = BytesIO()
        Image.fromarray(np.asarray(array, dtype="uint8")).save(buffer, format="PNG")
        return buffer.getvalue()

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

    def _mini_pair(self, image, marked):
        return ft.Row(
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                self._picture(image, MINI),
                ft.Image(
                    src=self._rgb_png(marked),
                    width=MINI, height=MINI,
                    fit=ft.BoxFit.FILL, border_radius=10, gapless_playback=True,
                ),
            ],
        )

    def _mini_card(self, title, accent, body, caption):
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
                    self.card_title(title, accent),
                    body,
                    ft.Text(caption, size=10, color=AppColors.TEXT_SECONDARY),
                ],
            ),
        )

    def _compare_card(self, spacing):
        made = self.trace.make(self.kind, spacing, 0)
        marked, info = annotate_spectrum(made["image"])

        return self._mini_card(
            f"{spacing} PX THREADS",
            PATTERN_ACCENT,
            self._mini_pair(made["image"], marked),
            f"dot {info['radius']:.0f} steps out  ·  "
            f"{info['radius']:.0f} × {spacing} = {self.size}",
        )

    def _family_card(self, kind):
        made = self.trace.make(kind)
        marked, info = annotate_spectrum(made["image"])
        measured = self.trace.measure(made["image"])

        notes = {
            "Cloth": "two thread directions, so two pairs of dots",
            "Brick": "strong courses, weak joins: one pair dominates",
            "Grass": "irregular, so the dots smear into a smudge",
        }

        return self._mini_card(
            kind.upper(),
            SPECTRUM_ACCENT,
            self._mini_pair(made["image"], marked),
            f"{notes[kind]}  ·  app reads {measured['spacing']:.0f} px",
        )

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
        self.angle_text = ft.Text("", **mono(11, palette.KERNEL))

        pattern_body = ft.Column(
            spacing=10,
            controls=[
                ft.Row(spacing=8, controls=list(self.kind_buttons.values())),
                self.slider_row(
                    "Thread spacing", self.spacing_text,
                    ft.Slider(min=0, max=len(SPACING_STEPS) - 1,
                              divisions=len(SPACING_STEPS) - 1,
                              value=SPACING_STEPS.index(self.spacing),
                              active_color=PATTERN_ACCENT,
                              on_change=lambda e: self.set_spacing(
                                  SPACING_STEPS[int(e.control.value)])),
                ),
                self.slider_row(
                    "Turn the picture", self.angle_text,
                    ft.Slider(min=0, max=len(ANGLES) - 1,
                              divisions=len(ANGLES) - 1,
                              value=0,
                              active_color=palette.KERNEL,
                              on_change=lambda e: self.set_angle(
                                  ANGLES[int(e.control.value)])),
                ),
            ],
        )

        self.verdict_text = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)
        check_body = ft.Column(
            spacing=10,
            controls=[
                ft.Text("Every pattern here is built to a known recipe, so the "
                        "app's answer can be checked, not believed.",
                        size=10, color=AppColors.MUTED),
                self.verdict_text,
                self.small_button("Check every pattern", ft.Icons.FACT_CHECK,
                                  lambda e: self.run_check()),
            ],
        )

        return [
            self.panel("THE PATTERN", "Built to order.",
                       ft.Icons.GRID_GOLDENRATIO, PATTERN_ACCENT, pattern_body),
            self.panel("THE ANSWER", "Measured, then checked.",
                       ft.Icons.RULE, APP_ACCENT, check_body),
        ]

    # =========================================================
    # STATE
    # =========================================================

    def _make(self):
        return self.trace.make(self.kind, self.spacing, self.angle)

    def _turned_by(self, info):
        """How far the dot has turned from the untilted pattern.

        The dot sits at right angles to the threads, not along them, so
        quoting its raw angle beside the picture's angle looks wrong
        even when it is right. What actually matters -- and what is
        true either way -- is that the dot turns by the same amount the
        picture does.
        """
        baseline = peak_info(self.trace.make(self.kind, self.spacing, 0)["image"])
        turned = (info["angle"] - baseline["angle"]) % 180.0
        return min(turned, 180.0 - turned) if turned > 90.0 else turned

    def apply_chapter_state(self, chapter):
        self.show(self.main_row, True)
        self.show(self.compare_row, chapter == 1)
        self.show(self.family_row, chapter == 3)

        if chapter == 2 and self.kind == "Cloth":
            # A weave looks the same turned by 90 degrees, so the
            # rotation chapter uses a texture with one clear direction.
            self.kind = "Grass"

        self._refresh()

    def _refresh(self):
        made = self._make()
        marked, info = annotate_spectrum(made["image"])
        measured = self.trace.measure(made["image"])

        self.pattern_image.src = self._rgb_png(
            ruler_overlay(made["image"], self.spacing, self.angle))
        self.spectrum_image.src = self._rgb_png(marked)

        self.pattern_note.value = (
            f"{self.kind.lower()}  ·  built {self.spacing} px apart"
        )
        self.spectrum_note.value = f"dot {info['radius']:.0f} steps from centre"

        product = info["radius"] * self.spacing
        joiner = "=" if abs(product - self.size) < 1.0 else "≈"

        self.measure_lines["threads"].value = f"{self.spacing} px apart"
        self.measure_lines["dot"].value = f"{info['radius']:.0f} steps out"
        self.measure_lines["check"].value = (
            f"{info['radius']:.0f} × {self.spacing} {joiner} {self.size}"
        )
        self.measure_lines["tilt"].value = (
            f"turned {self.angle}°  →  dot turned {self._turned_by(info):.0f}°"
        )
        self.measure_lines["app"].value = (
            f"{measured['spacing']:.0f} px  ·  {measured['orientation'].lower()}"
        )

        self.spacing_text.value = f"{self.spacing} px"
        self.angle_text.value = f"{self.angle}°"

    # =========================================================
    # ACTIONS
    # =========================================================

    def set_kind(self, kind):
        self.timeline.cancel()
        self.kind = kind
        self._refresh()
        self.caption_text.value = (
            f"{kind}: the app reads "
            f"{self.trace.measure(self._make()['image'])['spacing']:.0f} px "
            f"between repeats."
        )
        self.safe_update(self.control)

    def set_spacing(self, spacing):
        self.timeline.cancel()
        self.spacing = int(spacing)
        self._refresh()
        self.caption_text.value = (
            f"Threads {self.spacing} px apart: {self.measure_lines['check'].value}."
        )
        self.safe_update(self.control)

    def set_angle(self, angle):
        self.timeline.cancel()
        self.angle = int(angle)
        self._refresh()
        self.caption_text.value = (
            f"Turned {self.angle}°, and {self.measure_lines['tilt'].value}."
        )
        self.safe_update(self.control)

    def run_check(self):
        self.timeline.cancel()
        checks = self.trace.verify()

        self.verdict_text.value = (
            f"Spacing recovered within {checks['worst_spacing_error']:.1f} px on "
            f"every test pattern; rotation tracked within "
            f"{checks['worst_rotation_error']:.1f}°."
        )
        self.caption_text.value = (
            "Checked across every pattern and angle in this lesson."
        )
        self.safe_update(self.control)

    # =========================================================
    # SCENES
    # =========================================================

    def scenes(self):
        return [self._scene_repeat, self._scene_spacing, self._scene_rotate,
                self._scene_family, self._scene_algorithm]

    # ---------------- 1 ----------------

    async def _scene_repeat(self, gen):
        tl = self.timeline

        self.show(self.compare_row, False)
        self.show(self.family_row, False)
        self.kind, self.spacing, self.angle = "Cloth", 8, 0
        self._refresh()
        tl.push(gen, self.control)

        await self.say(gen, "A piece of cloth. The amber bracket on it marks one "
                            "repeat: from one thread to the next is 8 px.",
                       self.step_label(0), hold=5.2)

        await self.say(gen, "Something that repeats evenly is a wave — so this "
                            "picture is mostly made of just a couple of waves, "
                            "and its spectrum is nearly empty.", hold=5.4)

        await self.say(gen, "The ring marks the bright dot, and the amber line "
                            "runs from the centre out to it. That line is the "
                            "measurement.", hold=5.0)

        await self.say(gen, f"It is 16 steps long, where one step means one stripe "
                            f"across the picture. And 16 × 8 = {self.size}, the "
                            f"width of the picture.", hold=5.6)

        await self.say(gen, "So the dot's distance and the thread spacing are the "
                            "same fact, written two ways.", hold=4.6)

    # ---------------- 2 ----------------

    async def _scene_spacing(self, gen):
        tl = self.timeline

        await self.say(gen, "Weave it tighter and watch the number.",
                       self.step_label(1), hold=3.0)

        for spacing in (16, 8, 4):
            self.spacing = spacing
            self._refresh()
            tl.push(gen, self.control)
            await self.say(gen, f"{spacing} px threads: "
                                f"{self.measure_lines['check'].value}.", hold=3.6)

        self.show(self.compare_row, True)
        tl.push(gen, self.control)

        await self.say(gen, "Halve the spacing, double the distance, every time. "
                            "The three together make it obvious.", hold=5.0)

        await self.say(gen, "That is the first half of texture analysis: to find "
                            "how fine a texture is, measure how far its dot sits "
                            "from the centre.", hold=5.4)

    # ---------------- 3 ----------------

    async def _scene_rotate(self, gen):
        tl = self.timeline

        self.show(self.compare_row, False)
        self.kind, self.spacing, self.angle = "Grass", 8, 0
        self._refresh()
        tl.push(gen, self.control)

        await self.say(gen, "Second question: which way does it run? Here is grass "
                            "— blades all going one way.",
                       self.step_label(2), hold=4.6)

        await self.say(gen, "One detail worth knowing: the dot sits at right "
                            "angles to the blades, because it marks the direction "
                            "the brightness changes in. What matters is that it "
                            "turns exactly as much as the picture does.",
                       hold=6.0)

        for angle in (0, 30, 45, 60, 90):
            self.angle = angle
            self._refresh()
            tl.push(gen, self.control)
            await self.say(gen, f"Turned {angle}° — {self.measure_lines['tilt'].value}. "
                                f"The app calls it "
                                f"{self.trace.measure(self._make()['image'])['orientation'].lower()}.",
                           hold=3.6)

        self.angle = 0
        self._refresh()
        tl.push(gen, self.control)

        await self.say(gen, "Degree for degree, the dot follows. So reading its "
                            "angle tells you which way the texture runs.",
                       hold=5.0)

    # ---------------- 4 ----------------

    async def _scene_family(self, gen):
        tl = self.timeline

        self.show(self.family_row, True)
        tl.push(gen, self.control)

        await self.say(gen, "Three textures, and their spectra look different in a "
                            "way that makes sense.", self.step_label(3), hold=4.4)

        for kind in TEXTURES:
            self.kind = kind
            self.spacing = TEXTURES[kind][1] if TEXTURES[kind][1] in SPACING_STEPS else 8
            self.angle = 0
            self._refresh()
            tl.push(gen, self.control)

            if kind == "Cloth":
                text = ("Cloth repeats in two directions at once, so it gets two "
                        "pairs of dots — one pair per thread direction.")
            elif kind == "Brick":
                text = ("Brick has strong courses and weaker joins, so one pair "
                        "of dots is much brighter than the other.")
            else:
                text = ("Grass is irregular — no two blades match — so instead of "
                        "sharp dots you get a smudge pointing the right way.")

            await self.say(gen, text, hold=5.0)

        await self.say(gen, "Regular patterns give sharp dots; natural ones give "
                            "soft smudges. Both still say how fine and which way.",
                       hold=5.0)

    # ---------------- 5 ----------------

    async def _scene_algorithm(self, gen):
        tl = self.timeline

        self.show(self.family_row, False)
        self.kind, self.spacing, self.angle = "Cloth", 8, 0
        self._refresh()
        checks = self.trace.verify()
        self.verdict_text.value = (
            f"Spacing within {checks['worst_spacing_error']:.1f} px; rotation "
            f"within {checks['worst_rotation_error']:.1f}°."
        )
        tl.push(gen, self.control)

        await self.say(gen, "Here is the entire texture feature, in three steps.",
                       self.step_label(4), hold=3.6)

        await self.say(gen, "One: transform the picture and ignore the bright "
                            "middle, which is only the average brightness.",
                       hold=4.8)

        await self.say(gen, "Two: find the brightest dot that is left.", hold=3.4)

        await self.say(gen, "Three: its distance gives the spacing, and its angle "
                            "gives the direction.", hold=4.4)

        await self.say(gen, f"No training and no examples — and across every "
                            f"pattern here the spacing came back within "
                            f"{checks['worst_spacing_error']:.1f} px and the angle "
                            f"within {checks['worst_rotation_error']:.1f}°.",
                       hold=5.6)

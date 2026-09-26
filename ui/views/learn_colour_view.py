"""Discover · Lesson 9 — Brightness and colour are not equals.

The last frequency lesson, and the one with the most surprising
result: you can throw away most of a picture's colour information and
almost nobody notices, but do the same to its brightness and the
picture falls apart.

The lesson runs it as a fair experiment — the same damage, to each part
in turn — and lets the pictures and the numbers agree. On this scene
the gap is 12 dB at 4x4 blocks.

Chapters
    1  Three colours, or one       R, G, B all look like the picture
    2  Split it differently        Y carries the shape, Cb and Cr are soft
    3  Wreck the colour            2x2, 4x4, 8x8 blocks, barely a change
    4  Wreck the brightness        the same damage, and it collapses
    5  That is why JPEG does it    chroma subsampling, in one screen
"""

import flet as ft

from algorithms.learning.texture_colour_trace import ColourTrace, palette_free_grey
from ui.learning import palette
from ui.learning.lesson_shell import LessonShell, mono
from ui.theme import AppColors


PANEL = 188
MINI = 128

SOURCE_ACCENT = palette.INPUT
LUMA_ACCENT = "#FBBF24"
CHROMA_ACCENT = palette.PRODUCT
FACTORS = (1, 2, 4, 8)


class LearnColourView(LessonShell):
    CHAPTERS = [
        "Three colours, or one",
        "Split it differently",
        "Wreck the colour",
        "Wreck the brightness",
        "Why JPEG does it",
    ]
    ACCENT = palette.PRODUCT
    BADGE = "DISCOVER  •  LESSON 9"
    TITLE = "Brightness and colour are not equals"
    SUBTITLE = "Throw away most of the colour and the picture survives. Try that with brightness."

    def __init__(self, page):
        super().__init__(page)

        self.trace = ColourTrace()
        self.target = "chroma"
        self.factor = 4

        self.result = self.trace.damage(self.target, self.factor)
        self.channels = self.trace.channel_pictures()

        self.build()
        self.set_chapter_state(0, first_build=True)

    # =========================================================
    # STAGE
    # =========================================================

    def build_stage(self):
        self.original_image = self._picture(self.trace.image)
        self.damaged_image = self._picture(self.result["image"])
        self.damaged_note = ft.Text("", **mono(11, CHROMA_ACCENT))

        self.original_card = self.picture_card(
            self.original_image, "THE ORIGINAL", SOURCE_ACCENT)
        self.damaged_card = self.picture_card(
            self.damaged_image, "AFTER THE DAMAGE", CHROMA_ACCENT,
            self.damaged_note)
        self.show(self.damaged_card, False)

        self.main_arrow = self.slot(self.arrow("damage one part"), width=110)
        self.main_arrow.opacity = 0.0
        self.main_arrow.visible = False

        self.main_row = self.row([
            self.original_card,
            self.main_arrow,
            self.damaged_card,
        ])

        # ---- R, G, B ----
        red, green, blue = self.trace.red, self.trace.green, self.trace.blue
        self.rgb_row = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True, spacing=12, run_spacing=12,
                controls=[
                    self._mini_card("RED", palette_free_grey(red), "#F87171"),
                    self._mini_card("GREEN", palette_free_grey(green), "#4ADE80"),
                    self._mini_card("BLUE", palette_free_grey(blue), "#60A5FA"),
                ],
            ),
        )

        # ---- Y, Cb, Cr ----
        self.channel_cards = []
        cards = []
        for item in self.channels:
            note = ft.Text("", size=9, color=AppColors.MUTED)
            card = ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Text(item["name"], size=10, weight=ft.FontWeight.BOLD,
                            color=LUMA_ACCENT if item["name"].startswith("Y")
                            else CHROMA_ACCENT),
                    ft.Container(
                        border_radius=12,
                        border=ft.Border.all(1.2, palette.argb("66", SOURCE_ACCENT)),
                        content=self._picture(item["picture"], MINI),
                    ),
                    note,
                ],
            )
            note.value = f"detail {item['detail']:.2f}"
            self.channel_cards.append(note)
            cards.append(card)

        self.ycbcr_row = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True, spacing=12, run_spacing=12, controls=cards,
            ),
        )

        # ---- the fair experiment ----
        self.experiment_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=True, spacing=12, run_spacing=12, controls=[],
        )
        self.experiment_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Text("SAME DAMAGE, DIFFERENT VICTIM", size=9,
                            weight=ft.FontWeight.BOLD, color=AppColors.MUTED),
                    self.experiment_row,
                ],
            ),
        )

        return [self.main_row, self.rgb_row, self.ycbcr_row, self.experiment_card]

    def _picture(self, array, size=PANEL):
        return ft.Image(
            src=palette.png_bytes(array, scale=1) if array.ndim == 2
            else self._rgb_png(array),
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

    def _mini_card(self, title, array, accent):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            controls=[
                ft.Text(title, size=10, weight=ft.FontWeight.BOLD, color=accent),
                ft.Container(
                    border_radius=12,
                    border=ft.Border.all(1.2, palette.argb("66", accent)),
                    content=self._picture(array, MINI),
                ),
            ],
        )

    def _show_experiment(self, factors=(2, 4, 8)):
        cards = []
        for row in self.trace.comparison(factors):
            cards.append(ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Text(f"{row['factor']}×{row['factor']} blocks", size=10,
                            weight=ft.FontWeight.BOLD, color=AppColors.TEXT),
                    ft.Row(
                        spacing=8,
                        controls=[
                            self._labelled(row["chroma"]["image"], "colour spoiled",
                                           row["chroma"]["psnr"], CHROMA_ACCENT),
                            self._labelled(row["luma"]["image"], "brightness spoiled",
                                           row["luma"]["psnr"], LUMA_ACCENT),
                        ],
                    ),
                ],
            ))
        self.experiment_row.controls = cards

    def _labelled(self, array, label, psnr, accent):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            controls=[
                ft.Container(
                    border_radius=10,
                    border=ft.Border.all(1.2, palette.argb("77", accent)),
                    content=self._picture(array, MINI),
                ),
                ft.Text(label, size=9, color=accent),
                ft.Text(f"{psnr:.1f} dB", **mono(10, accent)),
            ],
        )

    # =========================================================
    # PANELS
    # =========================================================

    def side_panels(self):
        self.factor_text = ft.Text("", **mono(11, CHROMA_ACCENT))
        self.target_buttons = {
            "chroma": self.small_button("Spoil the colour", ft.Icons.PALETTE,
                                        lambda e: self.set_target("chroma")),
            "luma": self.small_button("Spoil the brightness", ft.Icons.LIGHT_MODE,
                                      lambda e: self.set_target("luma")),
        }

        damage_body = ft.Column(
            spacing=10,
            controls=[
                ft.Row(spacing=8, controls=list(self.target_buttons.values())),
                self.slider_row(
                    "Block size", self.factor_text,
                    ft.Slider(min=0, max=len(FACTORS) - 1,
                              divisions=len(FACTORS) - 1, value=2,
                              active_color=CHROMA_ACCENT,
                              on_change=lambda e: self.set_factor(
                                  FACTORS[int(e.control.value)])),
                ),
                ft.Text("Each block of pixels is forced to share one value. "
                        "Bigger blocks mean less data stored.",
                        size=10, color=AppColors.MUTED),
            ],
        )

        self.verdict_text = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)
        check_body = ft.Column(
            spacing=10,
            controls=[
                self.verdict_text,
                self.small_button("Run the comparison", ft.Icons.FACT_CHECK,
                                  lambda e: self.run_check()),
            ],
        )

        return [
            self.panel("THE DAMAGE", "Same treatment, different part.",
                       ft.Icons.BROKEN_IMAGE, CHROMA_ACCENT, damage_body),
            self.panel("THE VERDICT", "Measured, not assumed.",
                       ft.Icons.RULE, SOURCE_ACCENT, check_body),
        ]

    # =========================================================
    # STATE
    # =========================================================

    def apply_chapter_state(self, chapter):
        self.show(self.rgb_row, chapter == 0)
        self.show(self.ycbcr_row, chapter in (1, 2, 3))
        self.show(self.damaged_card, chapter in (2, 3))
        self.show(self.main_arrow, chapter in (2, 3))
        self.show(self.experiment_card, chapter == 4)

        if chapter == 2:
            self.target = "chroma"
        elif chapter == 3:
            self.target = "luma"
        if chapter == 4:
            self._show_experiment()

        self._refresh()

    def _refresh(self):
        self.result = self.trace.damage(self.target, self.factor)
        self.damaged_image.src = self._rgb_png(self.result["image"])

        word = "colour" if self.target == "chroma" else "brightness"
        self.damaged_note.value = (
            f"{word} in {self.factor}×{self.factor} blocks  ·  "
            f"{self.result['psnr']:.1f} dB"
        )
        self.factor_text.value = (
            "untouched" if self.factor == 1 else f"{self.factor}×{self.factor}"
        )

        for note, item in zip(self.channel_cards, self.channels):
            note.value = f"detail {item['detail']:.2f}"

    # =========================================================
    # ACTIONS
    # =========================================================

    def set_target(self, target):
        self.timeline.cancel()
        self.target = target
        self.show(self.damaged_card, True)
        self.show(self.main_arrow, True)
        self._refresh()

        other = self.trace.damage(
            "luma" if target == "chroma" else "chroma", self.factor
        )
        word = "colour" if target == "chroma" else "brightness"
        self.caption_text.value = (
            f"Spoiling the {word} in {self.factor}×{self.factor} blocks: "
            f"{self.result['psnr']:.1f} dB, against {other['psnr']:.1f} dB for "
            f"the other one."
        )
        self.safe_update(self.control)

    def set_factor(self, factor):
        self.timeline.cancel()
        self.factor = int(factor)
        self.show(self.damaged_card, True)
        self.show(self.main_arrow, True)
        self._refresh()
        if self.chapter == 4:
            self._show_experiment()

        if self.factor == 1:
            self.caption_text.value = "Nothing damaged yet."
        else:
            self.caption_text.value = (
                f"{self.factor}×{self.factor} blocks means storing "
                f"{100 / (self.factor ** 2):.0f}% as many values for that part: "
                f"{self.result['psnr']:.1f} dB."
            )
        self.safe_update(self.control)

    def run_check(self):
        self.timeline.cancel()
        checks = self.trace.verify()

        self.verdict_text.value = (
            f"Colour damage costs less than brightness damage at every block "
            f"size: {'yes' if checks['chroma_damage_always_cheaper'] else 'no'}. "
            f"Gap at 4×4: {checks['gap_at_4x']:.1f} dB. Converting to YCbCr and "
            f"back loses almost nothing ({checks['roundtrip_psnr']:.1f} dB)."
        )
        self.caption_text.value = (
            "Both halves of the experiment run on the app's own colour "
            "conversion, so the comparison is fair."
        )
        self.safe_update(self.control)

    # =========================================================
    # SCENES
    # =========================================================

    def scenes(self):
        return [self._scene_rgb, self._scene_split, self._scene_chroma,
                self._scene_luma, self._scene_jpeg]

    async def _scene_rgb(self, gen):
        tl = self.timeline

        self.show(self.damaged_card, False)
        self.show(self.main_arrow, False)
        self.show(self.ycbcr_row, False)
        self.show(self.experiment_card, False)
        self.show(self.rgb_row, True)
        tl.push(gen, self.control)

        await self.say(gen, "A colour picture is three pictures stacked: how much "
                            "red, how much green, how much blue.",
                       self.step_label(0), hold=4.6)

        await self.say(gen, "But look at them. All three show the planet, the ring "
                            "and the stars. They are almost the same picture three "
                            "times over.", hold=5.0)

        await self.say(gen, "That is wasteful, and it hides the thing we actually "
                            "want to know: which part of this picture could we "
                            "afford to lose?", hold=5.0)

    async def _scene_split(self, gen):
        tl = self.timeline

        self.show(self.rgb_row, False)
        self.show(self.ycbcr_row, True)
        tl.push(gen, self.control)

        await self.say(gen, "So split it a smarter way: one channel for brightness, "
                            "two for colour. That is YCbCr.",
                       self.step_label(1), hold=4.6)

        luma, blue_diff, red_diff = self.channels

        await self.say(gen, f"Y is brightness alone, and it looks like the "
                            f"photograph in grey. Every edge is in it. Its detail "
                            f"score is {luma['detail']:.2f}.", hold=5.0)

        await self.say(gen, f"Cb and Cr hold only colour, and they are smooth and "
                            f"dull: {blue_diff['detail']:.2f} and "
                            f"{red_diff['detail']:.2f}, a fraction of Y's.",
                       hold=5.2)

        await self.say(gen, "Your eyes work the same way. They have far more "
                            "brightness receptors than colour ones, which is why "
                            "detail feels like a brightness thing.", hold=5.4)

        await self.say(gen, "So here is a question with a testable answer: does "
                            "colour matter less than brightness?", hold=4.6)

    async def _scene_chroma(self, gen):
        tl = self.timeline

        self.target = "chroma"
        self.factor = 1
        self._refresh()
        self.show(self.damaged_card, True)
        self.show(self.main_arrow, True)
        tl.push(gen, self.control)

        await self.say(gen, "Test it. Force blocks of pixels to share one colour "
                            "value, and keep brightness untouched.",
                       self.step_label(2), hold=4.8)

        for factor in (2, 4, 8):
            self.factor = factor
            self._refresh()
            tl.push(gen, self.control)
            await self.say(gen, f"{factor}×{factor} blocks — storing "
                                f"{100 / (factor ** 2):.0f}% of the colour data — "
                                f"and it still looks like the picture: "
                                f"{self.result['psnr']:.1f} dB.", hold=4.6)

        await self.say(gen, "Sixty-four pixels sharing one colour, and you have to "
                            "look hard to see it. Colour is cheap to lose.",
                       hold=5.0)

    async def _scene_luma(self, gen):
        tl = self.timeline

        self.target = "luma"
        self.factor = 1
        self._refresh()
        tl.push(gen, self.control)

        await self.say(gen, "Now be fair: exactly the same damage, but to brightness "
                            "instead of colour.", self.step_label(3), hold=4.4)

        for factor in (2, 4, 8):
            self.factor = factor
            self._refresh()
            tl.push(gen, self.control)

            chroma = self.trace.damage("chroma", factor)
            await self.say(gen, f"{factor}×{factor} blocks: {self.result['psnr']:.1f} dB, "
                                f"where the colour version scored "
                                f"{chroma['psnr']:.1f} dB. And you can see it — "
                                f"the picture has gone blocky.", hold=5.0)

        checks = self.trace.verify()
        await self.say(gen, f"Same treatment, same amount of data thrown away, "
                            f"{checks['gap_at_4x']:.1f} dB apart at 4×4. Brightness "
                            f"is where the picture lives.", hold=5.4)

    async def _scene_jpeg(self, gen):
        tl = self.timeline

        self.target = "chroma"
        self.factor = 2
        self._refresh()
        self._show_experiment()
        self.show(self.experiment_card, True)
        self.show(self.ycbcr_row, False)
        tl.push(gen, self.control)

        await self.say(gen, "Both halves of the experiment, side by side.",
                       self.step_label(4), hold=3.4)

        await self.say(gen, "This is exactly why JPEG stores colour at lower "
                            "resolution than brightness. It is called chroma "
                            "subsampling.", hold=5.0)

        chroma = self.trace.damage("chroma", 2)
        await self.say(gen, f"The common setting, 4:2:0, is the 2×2 case: half the "
                            f"total data saved, at {chroma['psnr']:.1f} dB on this "
                            f"picture.", hold=5.0)

        await self.say(gen, "Your phone camera, every video stream and almost every "
                            "photo on the web does this before you ever see the "
                            "image.", hold=5.0)

        await self.say(gen, "And it works for one reason: brightness and colour were "
                            "never equals, so there was no sense storing them as "
                            "though they were.", hold=5.2)

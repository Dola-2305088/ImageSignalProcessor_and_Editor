"""Discover · Lesson 6 — Choosing which waves to keep.

Lesson 5 established the alphabet: centre means slow, outward means
fine, direction means orientation. This one uses it. A mask over the
spectrum is the whole idea, and three familiar things fall out of it:

    keep the middle          -> blur
    keep the outside         -> edges
    middle of one picture
    + outside of another     -> a hybrid that changes identity with
                                viewing distance

It also shows the artifact honestly: a hard-edged mask rings, a soft
one does not, and the lesson measures the difference rather than
asserting it.

Chapters
    1  A circle on the spectrum   keep the middle, get blur
    2  Keep the outside instead   the edges, and low + high = original
    3  The ripples nobody wants   hard versus soft mask edges
    4  Two pictures in one        the hybrid recipe
    5  Walk away                  the same picture becomes the other one
"""

import flet as ft

from algorithms.learning.frequency_trace import HybridTrace, MaskTrace
from ui.learning import palette
from ui.learning.lesson_shell import LessonShell, mono
from ui.theme import AppColors


PANEL = 188
DISTANCES = (1, 2, 3, 4, 6, 8)

LOW_ACCENT = palette.INPUT
HIGH_ACCENT = palette.KERNEL
MASK_ACCENT = palette.KERNEL_FRAME
HYBRID_ACCENT = palette.PRODUCT


class LearnFilterView(LessonShell):
    CHAPTERS = [
        "A circle on the spectrum",
        "Keep the outside instead",
        "The ripples nobody wants",
        "Two pictures in one",
        "Walk away",
    ]
    ACCENT = palette.KERNEL_FRAME
    BADGE = "DISCOVER  •  LESSON 6"
    TITLE = "Choosing which waves to keep"
    SUBTITLE = ("One mask over the spectrum gives you blur, edges "
                "and hybrid images.")

    def __init__(self, page):
        super().__init__(page)

        self.mask = MaskTrace()
        self.hybrid = HybridTrace()

        self.radius = 12
        self.softness = 0
        self.high_pass = False
        self.cutoff = 10
        self.distance = 1

        # Which picture is playing which role; swapping exchanges them,
        # so every label reads from here rather than being hardcoded.
        self.blur_name = "comet"
        self.detail_name = "planet"

        self.result = self.mask.apply(self.radius, self.high_pass, self.softness)
        self.recipe = self.hybrid.build(self.cutoff)

        self.build()
        self.set_chapter_state(0, first_build=True)

    # =========================================================
    # STAGE
    # =========================================================

    def build_stage(self):
        self.source_image = self._picture(self.mask.image)
        self.spectrum_image = self._picture(self.mask.spectrum_image)
        self.mask_image = self._picture(self.result["mask_picture"])
        self.result_image = self._picture(self.result["image"])

        self.result_note = ft.Text("", **mono(11, LOW_ACCENT))
        self.mask_note = ft.Text("", size=9, color=AppColors.MUTED)

        self.filter_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            wrap=True, spacing=14, run_spacing=14,
            controls=[
                self.picture_card(self.source_image, "THE PICTURE", LOW_ACCENT),
                self.slot(self.arrow("transform"), width=70),
                self.picture_card(self.spectrum_image, "SPECTRUM  ·  F(u,v)",
                                  MASK_ACCENT),
                self.slot(self.arrow("× mask"), width=70),
                self.picture_card(self.mask_image, "MASK  ·  M(u,v)", MASK_ACCENT,
                                  self.mask_note),
                self.slot(self.arrow("back"), width=70),
                self.picture_card(self.result_image, "RESULT", HYBRID_ACCENT,
                                  self.result_note),
            ],
        )

        # ---- ringing comparison ----
        self.hard_image = self._picture(
            self.mask.apply(10, softness=0)["image"], size=170)
        self.soft_image = self._picture(
            self.mask.apply(10, softness=6)["image"], size=170)
        self.hard_note = ft.Text("", **mono(10, HIGH_ACCENT))
        self.soft_note = ft.Text("", **mono(10, LOW_ACCENT))

        self.ringing_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True, spacing=14, run_spacing=14,
                controls=[
                    self.picture_card(self.hard_image, "HARD-EDGED MASK",
                                      HIGH_ACCENT, self.hard_note),
                    self.picture_card(self.soft_image, "SOFT-EDGED MASK",
                                      LOW_ACCENT, self.soft_note),
                ],
            ),
        )

        # ---- hybrid ----
        self.far_image = self._picture(self.hybrid.far, size=150)
        self.near_image = self._picture(self.hybrid.near, size=150)
        self.low_part_image = self._picture(self.recipe["low_part"], size=150)
        self.high_part_image = self._picture(self.recipe["high_part"], size=150)
        self.hybrid_image = self._picture(self.recipe["hybrid"], size=190)
        self.hybrid_note = ft.Text("", size=10, color=AppColors.TEXT_SECONDARY)
        self.blur_label = ft.Text(self.blur_name, size=10,
                                  weight=ft.FontWeight.BOLD, color=LOW_ACCENT)
        self.detail_label = ft.Text(self.detail_name, size=10,
                                    weight=ft.FontWeight.BOLD, color=HIGH_ACCENT)

        self.hybrid_card = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        wrap=True, spacing=12, run_spacing=12,
                        controls=[
                            self.picture_card(self.far_image, "SLOW WAVES FROM",
                                              LOW_ACCENT, self.blur_label),
                            self.picture_card(self.low_part_image, "ITS BLUR",
                                              LOW_ACCENT),
                            self.picture_card(self.near_image, "FAST WAVES FROM",
                                              HIGH_ACCENT, self.detail_label),
                            self.picture_card(self.high_part_image, "ITS EDGES",
                                              HIGH_ACCENT),
                        ],
                    ),
                    self.hybrid_note,
                ],
            ),
        )

        # ---- distance ----
        self.distance_images = []
        for distance in DISTANCES:
            view, _ = self.hybrid.seen_from(self.recipe["hybrid"], distance)
            size = max(60, int(190 / distance) + 40)
            image = self._picture(view, size=size)
            label = ft.Text(f"{distance}×", size=9, weight=ft.FontWeight.BOLD,
                            color=AppColors.TEXT_SECONDARY)
            self.distance_images.append((image, label, distance))

        self.distance_row = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            content=self.row([
                self.slot(
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Container(
                                border_radius=12,
                                border=ft.Border.all(
                                    1.2, palette.argb("77", HYBRID_ACCENT)),
                                content=image,
                            ),
                            label,
                        ],
                    ),
                    width=210, height=240,
                )
                for image, label, _ in self.distance_images
            ]),
        )

        self.hybrid_big_card = self.picture_card(
            self.hybrid_image, "THE HYBRID", HYBRID_ACCENT)
        self.show(self.hybrid_big_card, False)

        return [self.filter_row, self.ringing_card, self.hybrid_card,
                self.hybrid_big_card, self.distance_row]

    def _picture(self, array, size=PANEL):
        return ft.Image(
            src=palette.png_bytes(array, scale=2),
            width=size, height=size,
            fit=ft.BoxFit.FILL, border_radius=12, gapless_playback=True,
        )

    # =========================================================
    # PANELS
    # =========================================================

    def side_panels(self):
        self.radius_text = ft.Text("", **mono(11, MASK_ACCENT))
        self.softness_text = ft.Text("", **mono(11, LOW_ACCENT))
        self.cutoff_text = ft.Text("", **mono(11, HYBRID_ACCENT))

        filter_body = ft.Column(
            spacing=10,
            controls=[
                self.slider_row(
                    "Circle size", self.radius_text,
                    ft.Slider(min=2, max=48, divisions=23, value=self.radius,
                              active_color=MASK_ACCENT,
                              on_change=lambda e: self.set_radius(e.control.value)),
                ),
                self.slider_row(
                    "Edge softness", self.softness_text,
                    ft.Slider(min=0, max=12, divisions=6, value=self.softness,
                              active_color=LOW_ACCENT,
                              on_change=lambda e: self.set_softness(e.control.value)),
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        self.small_button("Keep middle", ft.Icons.BLUR_ON,
                                          lambda e: self.set_mode(False)),
                        self.small_button("Keep outside", ft.Icons.BORDER_OUTER,
                                          lambda e: self.set_mode(True)),
                    ],
                ),
            ],
        )

        hybrid_body = ft.Column(
            spacing=10,
            controls=[
                self.slider_row(
                    "Where to split", self.cutoff_text,
                    ft.Slider(min=4, max=24, divisions=10, value=self.cutoff,
                              active_color=HYBRID_ACCENT,
                              on_change=lambda e: self.set_cutoff(e.control.value)),
                ),
                ft.Text("Low waves come from the comet, high waves from the "
                        "planet. Move the split and watch which one wins.",
                        size=10, color=AppColors.MUTED),
                self.small_button("Swap the two pictures", ft.Icons.SWAP_HORIZ,
                                  lambda e: self.swap_hybrid()),
            ],
        )

        return [
            self.panel("THE MASK", "Which waves survive.",
                       ft.Icons.ADJUST, MASK_ACCENT, filter_body),
            self.panel("THE HYBRID", "Two pictures, one image.",
                       ft.Icons.LAYERS, HYBRID_ACCENT, hybrid_body),
        ]

    # =========================================================
    # STATE
    # =========================================================

    def apply_chapter_state(self, chapter):
        self.show(self.filter_row, chapter <= 2)
        self.show(self.ringing_card, chapter == 2)
        self.show(self.hybrid_card, chapter == 3)
        self.show(self.hybrid_big_card, chapter >= 3)
        self.show(self.distance_row, chapter == 4)

        if chapter <= 2:
            self.high_pass = chapter == 1
            self.softness = 0 if chapter < 2 else 6
            self._refresh_filter()
        if chapter >= 3:
            self._refresh_hybrid()
        if chapter == 2:
            self._refresh_ringing()

        self._sync_labels()

    def _sync_labels(self):
        self.radius_text.value = f"radius {int(self.radius)}"
        self.softness_text.value = (
            "hard edge" if self.softness == 0 else f"{int(self.softness)} px fade"
        )
        self.cutoff_text.value = f"radius {int(self.cutoff)}"

    def _refresh_filter(self):
        self.result = self.mask.apply(
            int(self.radius), self.high_pass, int(self.softness)
        )
        self.mask_image.src = palette.png_bytes(self.result["mask_picture"], scale=2)
        self.result_image.src = palette.png_bytes(self.result["image"], scale=2)

        self.mask_note.value = (
            f"keeps {self.result['kept_fraction'] * 100:.1f}% of the waves  ·  "
            f"{self.result['energy'] * 100:.1f}% of the energy"
        )

        if self.high_pass:
            self.result_note.value = "edges only (grey = no change)"
        else:
            self.result_note.value = f"{self.result['psnr']:.1f} dB against the original"

    def _refresh_ringing(self):
        radius = int(self.radius)
        hard = self.mask.apply(radius, softness=0)
        soft = self.mask.apply(radius, softness=6)

        self.hard_image.src = palette.png_bytes(hard["image"], scale=2)
        self.soft_image.src = palette.png_bytes(soft["image"], scale=2)
        self.hard_note.value = (
            f"ripple {self.mask.ringing_score(radius, 0):.2f}"
        )
        self.soft_note.value = (
            f"ripple {self.mask.ringing_score(radius, 6):.2f}"
        )

    def _refresh_hybrid(self):
        self.recipe = self.hybrid.build(int(self.cutoff))

        self.far_image.src = palette.png_bytes(self.hybrid.far, scale=2)
        self.near_image.src = palette.png_bytes(self.hybrid.near, scale=2)
        self.low_part_image.src = palette.png_bytes(self.recipe["low_part"], scale=2)
        self.high_part_image.src = palette.png_bytes(self.recipe["high_part"], scale=2)
        self.hybrid_image.src = palette.png_bytes(self.recipe["hybrid"], scale=2)

        for image, _, distance in self.distance_images:
            view, _ = self.hybrid.seen_from(self.recipe["hybrid"], distance)
            image.src = palette.png_bytes(view, scale=2)

        checks = self.hybrid.verify(int(self.cutoff))
        self.blur_label.value = self.blur_name
        self.detail_label.value = self.detail_name
        self.hybrid_note.value = (
            f"up close the fine detail matches the {self.detail_name} "
            f"{checks['detail_similarity_near']:.2f} against the "
            f"{self.blur_name}'s {checks['detail_similarity_far']:.2f}"
        )

    # =========================================================
    # ACTIONS
    # =========================================================

    def set_radius(self, value):
        self.timeline.cancel()
        self.radius = int(value)
        self.show(self.filter_row, True)
        self._refresh_filter()
        if self.chapter == 2:
            self._refresh_ringing()
        self._sync_labels()

        if self.high_pass:
            self.caption_text.value = (
                f"Throwing away everything within {self.radius} of the centre "
                f"leaves {self.result['energy'] * 100:.1f}% of the energy: only edges."
            )
        else:
            self.caption_text.value = (
                f"A circle of radius {self.radius} keeps "
                f"{self.result['kept_fraction'] * 100:.1f}% of the waves and "
                f"{self.result['energy'] * 100:.1f}% of the energy."
            )
        self.safe_update(self.control)

    def set_softness(self, value):
        self.timeline.cancel()
        self.softness = int(value)
        self._refresh_filter()
        if self.chapter == 2:
            self._refresh_ringing()
        self._sync_labels()
        self.caption_text.value = (
            "A hard edge on the mask makes ripples; fading it over a few pixels "
            "removes them." if self.softness == 0 else
            f"Fading the mask edge over {self.softness} px: ripple "
            f"{self.mask.ringing_score(int(self.radius), self.softness):.2f}."
        )
        self.safe_update(self.control)

    def set_mode(self, high_pass):
        self.timeline.cancel()
        self.high_pass = high_pass
        self.show(self.filter_row, True)
        self._refresh_filter()
        self.caption_text.value = (
            "Keeping only the fast waves leaves the edges."
            if high_pass else
            "Keeping only the slow waves leaves a blur."
        )
        self.safe_update(self.control)

    def set_cutoff(self, value):
        self.timeline.cancel()
        self.cutoff = int(value)
        self.show(self.hybrid_big_card, True)
        self._refresh_hybrid()
        self._sync_labels()
        self.caption_text.value = (
            f"Splitting at radius {self.cutoff}: a bigger circle gives the comet "
            f"more of the picture, a smaller one gives the planet more."
        )
        self.safe_update(self.control)

    def swap_hybrid(self):
        self.timeline.cancel()
        self.hybrid.near, self.hybrid.far = self.hybrid.far, self.hybrid.near
        self.blur_name, self.detail_name = self.detail_name, self.blur_name
        self._refresh_hybrid()
        self.caption_text.value = (
            f"Swapped: now the {self.blur_name} supplies the blur and the "
            f"{self.detail_name} supplies the detail."
        )
        self.safe_update(self.control)

    # =========================================================
    # SCENES
    # =========================================================

    def scenes(self):
        return [self._scene_low, self._scene_high, self._scene_ringing,
                self._scene_hybrid, self._scene_distance]

    async def _scene_low(self, gen):
        tl = self.timeline

        self.show(self.ringing_card, False)
        self.show(self.hybrid_card, False)
        self.show(self.hybrid_big_card, False)
        self.show(self.distance_row, False)
        self.show(self.filter_row, True)
        self.high_pass = False
        self.softness = 0
        tl.push(gen, self.control)

        await self.say(gen, "Last lesson turned the picture into a spectrum. Now we "
                            "start crossing parts of it out.",
                       self.step_label(0), hold=4.0)

        await self.say(gen, "Draw a circle around the centre and keep only what is "
                            "inside it — only the slow, wide waves.", hold=0.4)

        for radius in (48, 32, 20, 12, 6, 3):
            self.radius = radius
            self._refresh_filter()
            self._sync_labels()
            tl.push(gen, self.control)
            await tl.wait(gen, 1.0)

        await self.say(gen, f"Radius 3 keeps only {self.result['kept_fraction'] * 100:.1f}% "
                            f"of the waves, and the picture is a soft blob. The "
                            f"detail lived in everything we crossed out.", hold=5.0)

        self.radius = 12
        self._refresh_filter()
        self._sync_labels()
        tl.push(gen, self.control)
        await self.say(gen, "That is all a blur is: throw away the fast waves. "
                            "No averaging, no kernel, just deletion.", hold=4.6)

    async def _scene_high(self, gen):
        tl = self.timeline

        await self.say(gen, "Now cross out the other half: keep everything "
                            "*outside* the circle.", self.step_label(1), hold=0.4)

        self.high_pass = True
        self._refresh_filter()
        tl.push(gen, self.control)
        await tl.wait(gen, 2.2)

        await self.say(gen, f"Only {self.result['energy'] * 100:.1f}% of the energy "
                            f"survives, yet every edge in the picture is here. "
                            f"Grey means nothing changed.", hold=5.0)

        checks = self.mask.verify()
        await self.say(gen, "And the two halves are exactly complementary: add the "
                            "blur and the edges back together and you get the "
                            f"original again, to within "
                            f"{'one grey level' if checks['halves_rebuild_original'] else 'rounding'}.",
                       hold=5.2)

        await self.say(gen, "Blur and sharpen are not two different tools. They are "
                            "the same cut, kept from opposite sides.", hold=4.6)

    async def _scene_ringing(self, gen):
        tl = self.timeline

        self.high_pass = False
        self.radius = 10
        self.softness = 0
        self._refresh_filter()
        self._refresh_ringing()
        self.show(self.ringing_card, True)
        tl.push(gen, self.control)

        await self.say(gen, "There is a catch, and it is worth seeing.",
                       self.step_label(2), hold=3.0)

        hard = self.mask.ringing_score(10, 0)
        soft = self.mask.ringing_score(10, 6)

        await self.say(gen, "The circle has a hard edge: a wave is either kept "
                            "completely or deleted completely. Nothing in between.",
                       hold=4.4)

        await self.say(gen, f"That produces ripples beside every strong edge — look "
                            f"at the ring and the star. Overshoot measures "
                            f"{hard:.2f}.", hold=4.8)

        await self.say(gen, f"Fade the mask edge over a few pixels instead and the "
                            f"ripples drop to {soft:.2f}, less than half.",
                       hold=4.6)

        await self.say(gen, "A sharp cut in one domain makes ripples in the other. "
                            "That single sentence explains ringing everywhere it "
                            "shows up.", hold=5.0)

    async def _scene_hybrid(self, gen):
        tl = self.timeline

        self.show(self.filter_row, False)
        self.show(self.ringing_card, False)
        self._refresh_hybrid()
        self.show(self.hybrid_card, True)
        self.show(self.hybrid_big_card, True)
        tl.push(gen, self.control)

        await self.say(gen, f"Here is the trick that gets the most attention. Two "
                            f"pictures: a {self.blur_name} and a {self.detail_name}.",
                       self.step_label(3), hold=4.0)

        await self.say(gen, f"Take only the slow waves of the {self.blur_name} — its "
                            f"blur — and only the fast waves of the "
                            f"{self.detail_name} — its edges.", hold=4.6)

        await self.say(gen, "Add those two together. One picture, built from two "
                            "different sources that never overlap, because each one "
                            "owns a different part of the spectrum.", hold=5.2)

        checks = self.hybrid.verify(int(self.cutoff))
        await self.say(gen, f"Up close, the detail you see belongs to the "
                            f"{self.detail_name}: its fine waves match at "
                            f"{checks['detail_similarity_near']:.2f} against the "
                            f"{self.blur_name}'s "
                            f"{checks['detail_similarity_far']:.2f}.", hold=5.2)

    async def _scene_distance(self, gen):
        tl = self.timeline

        self.show(self.hybrid_card, False)
        self.show(self.distance_row, True)
        tl.push(gen, self.control)

        await self.say(gen, "Now step back from the screen. Or, since we can do it "
                            "honestly here, shrink the picture.",
                       self.step_label(4), hold=4.2)

        await self.say(gen, "Shrinking is what distance does: the fine waves stop "
                            "fitting, exactly as lesson 4 showed.", hold=4.4)

        await tl.wait(gen, 1.6)

        checks = self.hybrid.verify(int(self.cutoff))
        await self.say(gen, f"And the picture changes identity. Seen at one eighth "
                            f"the size it matches the {self.blur_name} at "
                            f"{checks['far_psnr_blurred_source']:.1f} dB and the "
                            f"{self.detail_name} at only "
                            f"{checks['far_psnr_sharp_source']:.1f} dB.", hold=5.4)

        await self.say(gen, "Nothing about the file changed. Your eye simply stopped "
                            "receiving the fast waves, and what was left was a "
                            "different picture.", hold=5.2)

        await self.say(gen, "Keep the middle, keep the outside, or give each to a "
                            "different picture. Every frequency filter is that one "
                            "decision.", hold=5.0)

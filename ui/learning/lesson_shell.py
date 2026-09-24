"""Shared chrome for Discover lessons.

The first five lessons each grew their own copy of the same furniture:
header, chapter pills, caption block, playback panel, small buttons,
card frames. This collects that into a base class so a new lesson is
only its own content.

A subclass provides:

    CHAPTERS       list of chapter names
    ACCENT         the lesson's colour
    BADGE, TITLE, SUBTITLE
    build_stage()  the controls between the caption and the panels
    side_panels()  the control cards beside Playback
    apply_chapter_state(chapter)   resting state for a chapter
    scenes()       the async scene functions, one per chapter
"""

import flet as ft

from ui.learning import palette
from ui.learning.scene_engine import Timeline
from ui.theme import AppAnimations, AppColors, AppLayout


# One visual language across every lesson, so a colour always means
# the same thing and cards never disagree about size or spacing.
ROLE = {
    "source": palette.INPUT,          # what we started with
    "tool": palette.KERNEL_FRAME,     # the kernel, mask or transform
    "result": palette.PRODUCT,        # what came out
    "measure": "#34D399",             # a measured, checkable number
    "warn": palette.KERNEL,           # the artifact or the cost
}

CARD_RADIUS = 16
CARD_PADDING = 14
CARD_GAP = 16
NOTE_HEIGHT = 18          # reserved, so cards with and without notes align
CAPTION_HEIGHT = 66       # reserved, so the stage never jumps


def mono(size, color):
    return dict(size=size, color=color, weight=ft.FontWeight.BOLD,
                font_family="Consolas")


def card_gradient():
    return ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=["#121A2B", "#0C1220"],
    )


class LessonShell:
    CHAPTERS = []
    ACCENT = palette.INPUT
    BADGE = "DISCOVER"
    TITLE = "Lesson"
    SUBTITLE = ""

    def __init__(self, page):
        self.page = page
        self.chapter = 0
        self.timeline = Timeline(page, on_state_change=self._on_running_changed)

    # =========================================================
    # BUILD
    # =========================================================

    def build(self):
        """Assemble the page. Call once the subclass is ready."""
        self.chapter_pills = [
            self._chapter_pill(i) for i in range(len(self.CHAPTERS))
        ]

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
                                bgcolor=palette.argb("22", self.ACCENT),
                                content=ft.Text(self.BADGE, size=9,
                                                weight=ft.FontWeight.BOLD,
                                                color=self.ACCENT),
                            ),
                            ft.Text(self.TITLE, size=24, weight=ft.FontWeight.BOLD,
                                    color=AppColors.TEXT),
                            ft.Text(self.SUBTITLE, size=11,
                                    color=AppColors.TEXT_SECONDARY),
                        ],
                    ),
                    ft.Row(spacing=8, wrap=True, controls=self.chapter_pills),
                ],
            ),
        )

        self.progress = ft.Container(
            width=0,
            height=3,
            border_radius=2,
            bgcolor=self.ACCENT,
            animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        )
        progress_track = ft.Container(
            height=3,
            border_radius=2,
            bgcolor=AppColors.SURFACE_3,
            content=ft.Row(controls=[self.progress]),
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
                controls=[self._caption_block()] + self.build_stage(),
            ),
        )

        panels = [ft.Container(col={"xs": 12, "lg": 4},
                               content=self.playback_panel())]
        panels += [
            ft.Container(col={"xs": 12, "lg": 4}, content=panel)
            for panel in self.side_panels()
        ]

        self.control = ft.Column(
            spacing=14,
            controls=[header, progress_track, stage,
                      ft.ResponsiveRow(spacing=14, run_spacing=14, controls=panels)],
        )
        return self.control

    # ---------------- pieces ----------------

    def _chapter_pill(self, index):
        number = ft.Container(
            width=22, height=22,
            alignment=ft.Alignment.CENTER,
            border_radius=11,
            border=ft.Border.all(1, self.ACCENT),
            content=ft.Text(str(index + 1), size=9, weight=ft.FontWeight.BOLD,
                            color=self.ACCENT),
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
                controls=[number, ft.Text(self.CHAPTERS[index], size=10,
                                          color=AppColors.TEXT_SECONDARY)],
            ),
        )

    def _caption_block(self):
        self.caption_step = ft.Text("", size=10, weight=ft.FontWeight.BOLD,
                                    color=self.ACCENT)
        self.caption_text = ft.Text("", size=16, weight=ft.FontWeight.W_600,
                                    color=AppColors.TEXT,
                                    text_align=ft.TextAlign.CENTER,
                                    max_lines=2)

        # The height is reserved rather than measured: a one-line
        # caption and a two-line caption must not shift everything
        # below them.
        self.caption = ft.Container(
            width=820,
            height=CAPTION_HEIGHT,
            alignment=ft.Alignment.TOP_CENTER,
            opacity=1.0,
            animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.caption_step, self.caption_text],
            ),
        )
        return self.caption

    def panel(self, title, subtitle, icon, accent, body):
        return ft.Container(
            padding=18,
            border_radius=CARD_RADIUS,
            gradient=card_gradient(),
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

    def small_button(self, label, icon, handler, accent=None):
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

    def card_title(self, title, accent):
        """A small colour dot and a spaced caps label."""
        return ft.Row(
            tight=True,
            spacing=7,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(width=7, height=7, border_radius=4, bgcolor=accent),
                ft.Text(title, size=9, weight=ft.FontWeight.BOLD, color=accent),
            ],
        )

    def picture_card(self, image_control, title, accent, note=None,
                     opacity=1.0, picture=188):
        """A card whose footprint never changes.

        Width and height are fixed from the picture size, so a row of
        them lines up on both edges whether or not each one has a note,
        and so nothing shifts when a card fades in or out.
        """
        controls = [
            self.card_title(title, accent),
            ft.Container(
                border_radius=13,
                border=ft.Border.all(1.4, palette.argb("88", accent)),
                shadow=ft.BoxShadow(blur_radius=26, spread_radius=-9,
                                    color=palette.argb("66", accent)),
                content=image_control,
            ),
            # Reserved line: cards with a note and cards without still
            # end at the same height, so a row of them stays level.
            ft.Container(height=NOTE_HEIGHT,
                         alignment=ft.Alignment.CENTER,
                         content=note),
        ]

        return ft.Container(
            width=picture + 2 * CARD_PADDING + 4,
            height=picture + 2 * CARD_PADDING + NOTE_HEIGHT + 34,
            opacity=opacity,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=CARD_PADDING,
            border_radius=CARD_RADIUS,
            gradient=card_gradient(),
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            alignment=ft.Alignment.TOP_CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.START,
                spacing=9,
                controls=controls,
            ),
        )

    def slot(self, control, width=220, height=264):
        """A fixed box for anything that is not a picture card.

        Arrows, stat blocks and small groups sit in one of these so a
        mixed row still aligns on a single baseline.
        """
        return ft.Container(
            width=width,
            height=height,
            alignment=ft.Alignment.CENTER,
            content=control,
        )

    def stat(self, label, value_control, accent):
        """A labelled number, aligned with its neighbours."""
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            border_radius=11,
            bgcolor=palette.argb("14", accent),
            border=ft.Border.all(1, palette.argb("44", accent)),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=1,
                controls=[
                    ft.Text(label.upper(), size=8, weight=ft.FontWeight.BOLD,
                            color=AppColors.MUTED),
                    value_control,
                ],
            ),
        )

    def arrow(self, label=None, accent=None):
        """A consistent connector between two cards."""
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=3,
            controls=[
                ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=22,
                        color=accent or AppColors.MUTED),
                ft.Text(label or "", size=8, color=AppColors.MUTED),
            ],
        )

    def row(self, controls, align_top=False):
        """The standard stage row: centred, wrapping, evenly spaced."""
        return ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=(ft.CrossAxisAlignment.START if align_top
                                else ft.CrossAxisAlignment.CENTER),
            wrap=True,
            spacing=CARD_GAP,
            run_spacing=CARD_GAP,
            controls=controls,
        )

    @staticmethod
    def show(control, visible):
        """Fade a card in or out, and give its space back when hidden.

        Reserving the space of a hidden card sounds tidier, but a row
        is centred on everything it contains, including what cannot be
        seen: one hidden card pushes the whole comparison off to the
        left. Cards keep a fixed footprint (see picture_card) so the
        ones that remain still line up with each other.
        """
        control.opacity = 1.0 if visible else 0.0
        control.visible = bool(visible)

    def slider_row(self, label, value_text, slider):
        return ft.Column(
            spacing=2,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[ft.Text(label, size=10, color=AppColors.MUTED),
                              value_text],
                ),
                slider,
            ],
        )

    def playback_panel(self):
        self.play_icon = ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=26, color="#0B1020")
        self.play_label = ft.Text("Play lesson", size=13, weight=ft.FontWeight.BOLD,
                                  color="#0B1020")
        self.play_button = ft.Container(
            height=50,
            padding=ft.Padding.symmetric(horizontal=18),
            border_radius=14,
            gradient=ft.LinearGradient(colors=[self.ACCENT, "#0EA5E9"]),
            shadow=ft.BoxShadow(blur_radius=22, spread_radius=-6,
                                color=palette.argb("99", self.ACCENT)),
            ink=True,
            on_click=self.toggle_play,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                controls=[self.play_icon, self.play_label],
            ),
        )
        self.speed_label = ft.Text("1×", size=11, weight=ft.FontWeight.BOLD,
                                   color=self.ACCENT)

        body = ft.Column(
            spacing=12,
            controls=[
                self.play_button,
                ft.Row(
                    spacing=8,
                    controls=[
                        self.small_button("Previous", ft.Icons.SKIP_PREVIOUS_ROUNDED,
                                          lambda e: self.jump_to(max(0, self.chapter - 1))),
                        self.small_button("Next", ft.Icons.SKIP_NEXT_ROUNDED,
                                          lambda e: self.jump_to(
                                              min(len(self.CHAPTERS) - 1,
                                                  self.chapter + 1))),
                        self.small_button("Restart", ft.Icons.REPLAY_ROUNDED,
                                          lambda e: self.jump_to(0)),
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SPEED, size=16, color=AppColors.MUTED),
                        ft.Text("Speed", size=10, color=AppColors.MUTED),
                        ft.Container(expand=True, content=ft.Slider(
                            min=0.5, max=2.0, divisions=6, value=1.0,
                            active_color=self.ACCENT,
                            on_change=self._on_speed,
                        )),
                        self.speed_label,
                    ],
                ),
            ],
        )
        return self.panel("PLAYBACK", "One idea at a time.",
                          ft.Icons.SMART_DISPLAY_OUTLINED, self.ACCENT, body)

    # =========================================================
    # PLAYBACK
    # =========================================================

    def toggle_play(self, e=None):
        if self.timeline.running:
            self.timeline.cancel()
            self.caption_text.value = "Paused. Press Play to continue."
            self.safe_update(self.caption)
            return

        start = 0 if self.chapter >= len(self.CHAPTERS) - 1 else self.chapter
        if start == 0:
            self.set_chapter_state(0)
        self.timeline.start(lambda gen: self._play_from(gen, start))

    def jump_to(self, chapter):
        self.timeline.cancel()
        self.set_chapter_state(chapter)
        self.timeline.start(lambda gen: self._play_from(gen, chapter))

    async def _play_from(self, gen, chapter):
        scenes = self.scenes()
        for index in range(chapter, len(scenes)):
            self.enter_chapter(index)
            await scenes[index](gen)
            self.timeline.check(gen)

    def set_chapter_state(self, chapter, first_build=False):
        self.chapter = chapter
        self.apply_chapter_state(chapter)

        self.caption_step.value = self.step_label(chapter)
        self.caption_text.value = (
            "Press Play to start." if chapter == 0
            else "Press Play to continue, or use the controls yourself."
        )

        self.refresh_pills()
        self.refresh_progress()
        if not first_build:
            self.safe_update(self.control)

    def enter_chapter(self, index):
        self.chapter = index
        self.refresh_progress()
        self.refresh_pills()
        for pill in self.chapter_pills:
            self.safe_update(pill)

    def step_label(self, chapter):
        return f"CHAPTER {chapter + 1}  ·  {self.CHAPTERS[chapter].upper()}"

    def refresh_progress(self):
        share = (self.chapter + 1) / max(1, len(self.CHAPTERS))
        self.progress.width = 1180 * share
        self.safe_update(self.progress)

    def refresh_pills(self):
        for index, pill in enumerate(self.chapter_pills):
            active = index == self.chapter
            done = index < self.chapter
            pill.bgcolor = (palette.argb("26", self.ACCENT) if active
                            else AppColors.SURFACE_DARK)
            pill.border = ft.Border.all(
                1, self.ACCENT if active else AppColors.BORDER_SOFT)
            number = pill.data
            number.bgcolor = self.ACCENT if (active or done) else None
            number.content.color = "#0B1020" if (active or done) else self.ACCENT

    async def say(self, gen, text, step=None, hold=0.0):
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

    def _on_speed(self, e):
        self.timeline.speed = float(e.control.value)
        self.speed_label.value = (
            f"{self.timeline.speed:.2f}".rstrip("0").rstrip(".") + "×"
        )
        self.safe_update(self.speed_label)

    def _on_running_changed(self, running):
        self.play_icon.icon = (ft.Icons.PAUSE_ROUNDED if running
                               else ft.Icons.PLAY_ARROW_ROUNDED)
        self.play_label.value = "Pause" if running else "Play lesson"
        self.safe_update(self.play_button)

    def stop(self):
        self.timeline.cancel(notify=False)
        self.play_icon.icon = ft.Icons.PLAY_ARROW_ROUNDED
        self.play_label.value = "Play lesson"

    @staticmethod
    def safe_update(control):
        try:
            control.update()
        except Exception:
            pass

    # ---------------- subclass hooks ----------------

    def build_stage(self):
        raise NotImplementedError

    def side_panels(self):
        return []

    def apply_chapter_state(self, chapter):
        raise NotImplementedError

    def scenes(self):
        raise NotImplementedError

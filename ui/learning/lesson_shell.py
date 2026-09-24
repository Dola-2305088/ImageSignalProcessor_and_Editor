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


def mono(size, color):
    return dict(size=size, color=color, weight=ft.FontWeight.BOLD,
                font_family="Consolas")


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
            spacing=16,
            controls=[header, stage,
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
                                    text_align=ft.TextAlign.CENTER)
        self.caption = ft.Container(
            width=780,
            opacity=1.0,
            animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.caption_step, self.caption_text],
            ),
        )
        return self.caption

    def panel(self, title, subtitle, icon, accent, body):
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

    def picture_card(self, image_control, title, accent, note=None, opacity=1.0):
        controls = [
            ft.Text(title, size=9, weight=ft.FontWeight.BOLD, color=accent),
            ft.Container(
                border_radius=14,
                border=ft.Border.all(1.4, palette.argb("88", accent)),
                shadow=ft.BoxShadow(blur_radius=24, spread_radius=-8,
                                    color=palette.argb("66", accent)),
                content=image_control,
            ),
        ]
        if note is not None:
            controls.append(note)

        return ft.Container(
            opacity=opacity,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
            padding=12,
            border_radius=14,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=controls,
            ),
        )

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
        if not first_build:
            self.safe_update(self.control)

    def enter_chapter(self, index):
        self.chapter = index
        self.refresh_pills()
        for pill in self.chapter_pills:
            self.safe_update(pill)

    def step_label(self, chapter):
        return f"CHAPTER {chapter + 1}  ·  {self.CHAPTERS[chapter].upper()}"

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

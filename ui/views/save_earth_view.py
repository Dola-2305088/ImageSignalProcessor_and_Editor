"""SaveEarth game mode view.

Screens:
  intro      cinematic: the Aetheris ship over Earth, the game title and
             the story revealed one sentence at a time
  briefing   themed mission briefing with the rules (the old start page)
  round      the gameplay (unchanged rules and layout)
  ending     cinematic: Earth destroyed, or Earth saved, then the log

All game rules live in game/ (pure Python). This view only draws the
current state of a GameSession and forwards the player's choices to it.
build_session() runs in a background thread and starts during the intro,
so the game is ready by the time the player reaches the briefing.

Sounds (assets/sounds/*.wav, via ui/components/game_sound.py) are kept to
key moments only: intro, transmit, the three verdicts, and the two endings.
A speaker button mutes them.

Deliberately, nothing previews a tool's output before Transmit: a preview
that only worked for the correct tool would give the answer away.
"""

from __future__ import annotations

import asyncio
from io import BytesIO

import flet as ft
import numpy as np
from PIL import Image

from game.game_state import (
    ANGER_LEVELS,
    MAX_STRIKES,
    GameSession,
    Outcome,
    Phase,
    Verdict,
    build_session,
)
from game.tools import TOOLS, TOOLS_BY_ID
from ui.components.game_sound import GameSound
from ui.components.section_header import SectionHeader
from ui.components.spatial_controls import (
    ActionButton,
    SegmentedSelector,
    hint,
    parameter_card,
)
from ui.theme import AppColors, AppLayout

# Colours taken from the artwork: the Aetheris ship's violet and cyan lights.
ACCENT = "#A855F7"
ACCENT_2 = "#22D3EE"
DEEP_SPACE = "#020410"
WIN_COLOR = "#6EE7B7"
LOSE_COLOR = "#FF2A2A"
IMAGE_SIZE = 256        # on-screen size of the 128x128 game images

# Paths are relative to the app's assets folder (like images/Nasa2.jpg on Home).
INTRO_IMAGE = "images/saveearth_intro.jpg"
DESTROYED_IMAGE = "images/saveearth_destroyed.jpg"
SAVED_IMAGE = "images/saveearth_saved.jpg"

INTRO_LINES = (
    "Beings from the planet Aetheris have reached Earth's orbit.",
    "They come in friendship, but they speak only in images.",
    "Five transmissions will arrive. Answer each with the right image-processing tool.",
    "In this image processing universe, your knowledge is Earth's only hope.",
    "Fail them three times, and they will destroy our worthless planet.",
)
LOSE_LINES = ("Game over.", "You don't belong to", "the image processing universe !")
WIN_LINES = ("Congratulations!!", "Earth has been saved by your knowledge !")

TOOL_ICONS = {
    "blur_sharpen": "BLUR_ON",
    "edges": "BORDER_STYLE",
    "noise": "GRAIN",
    "frequency_editor": "EQUALIZER",
    "compression": "COMPRESS",
    "resize": "PHOTO_SIZE_SELECT_LARGE",
    "motion_blur": "MOTION_PHOTOS_ON",
    "texture": "TEXTURE",
    "hybrid": "LAYERS",
    "separable": "CALL_SPLIT",
    "wiener": "RESTORE",
    "color": "PALETTE",
}

ANGER_COLORS = (AppColors.GREEN_LIGHT, AppColors.ORANGE, AppColors.RED, AppColors.RED)
VERDICT_SOUNDS = {Outcome.ACCEPTED: "accept", Outcome.RETRY: "retry", Outcome.STRIKE: "strike"}


def _icon(name):
    return getattr(ft.Icons, name, ft.Icons.CIRCLE_OUTLINED)


def _png(array):
    buffer = BytesIO()
    Image.fromarray(np.asarray(array, dtype=np.uint8)).save(buffer, format="PNG")
    return buffer.getvalue()


def _db(value):
    if value is None:
        return "—"
    if value == float("inf"):
        return "∞ dB (exact match)"
    return f"{value:.2f} dB"


def _fill(**kwargs):
    """A container stretched over the whole stage (a Stack layer)."""
    return ft.Container(left=0, top=0, right=0, bottom=0, **kwargs)


def _fading(control, dx=0.0, dy=0.35, ms=700):
    """Wrap a control so it can slide + fade in later via _reveal()."""
    return ft.Container(
        content=control,
        opacity=0,
        offset=ft.Offset(dx, dy),
        animate_opacity=ft.Animation(ms, ft.AnimationCurve.EASE_OUT),
        animate_offset=ft.Animation(ms, ft.AnimationCurve.EASE_OUT),
    )


class SaveEarthView:
    def __init__(self, page, on_open_discover=None):
        self.page = page
        self.on_open_discover = on_open_discover
        self.sound = GameSound()

        self.session: GameSession | None = None
        self._screen = None            # intro / briefing / round / ending
        self._token = 0                # bumps to cancel running animations
        self._build_future = None
        self._building = False
        self._transmitting = False
        self._awaiting_continue = False
        self._tool_selector = None
        self._option_selector = None
        self._ending_fades = []
        self._mute_buttons = []

        self.header = SectionHeader(
            badge="SAVEEARTH  •  GAME MODE",
            title="A Message from Aetheris",
            subtitle="Aetheris speaks only in images. Answer well, and Earth gains a friend among the stars.",
            icon=ft.Icons.PUBLIC,
            accent=ACCENT,
        )
        self.body = ft.Column(spacing=18)
        self._card = ft.Container(
            bgcolor=AppColors.SURFACE,
            border=ft.Border.all(1, AppColors.BORDER),
            border_radius=ft.BorderRadius.all(AppLayout.CARD_RADIUS),
            padding=AppLayout.CARD_PADDING,
            offset=ft.Offset(0, 0),
            animate_offset=ft.Animation(55, ft.AnimationCurve.LINEAR),
            content=ft.Column(spacing=18, controls=[self.header.control, self.body]),
        )

        self.control = ft.Container(content=ft.Container())

    # =========================================================
    # LIFECYCLE (called by main_window on navigation)
    # =========================================================

    def start(self):
        if self._screen in (None, "intro"):
            if self.page is not None:
                self.page.run_task(self._play_intro)
            else:
                self._show_briefing()

    def stop(self):
        self._token += 1                       # cancels intro / ending animations
        self.sound.stop()
        if self._screen == "intro":
            self._screen = None                # replay the intro next time
        elif self._screen == "ending":
            for c in self._ending_fades:       # never leave the ending half-drawn
                c.opacity, c.offset = 1, ft.Offset(0, 0)

    # =========================================================
    # SMALL UTILITIES
    # =========================================================

    def _next_token(self):
        self._token += 1
        return self._token

    async def _wait(self, token, seconds):
        await asyncio.sleep(seconds)
        return token == self._token

    def _set_content(self, content):
        self.control.content = content
        self._refresh()

    @staticmethod
    def _update(control):
        try:
            control.update()
        except Exception:
            pass

    def _reveal(self, control):
        control.opacity = 1
        control.offset = ft.Offset(0, 0)
        self._update(control)

    def _stage_height(self, minimum=460):
        height = getattr(self.page, "height", None) or 760
        return int(max(minimum, min(880, height - 170)))

    def _ensure_build(self):
        if self._build_future is None:
            self._build_future = asyncio.ensure_future(asyncio.to_thread(build_session))

    def _mute_button(self, **position):
        button = ft.IconButton(
            icon=ft.Icons.VOLUME_UP_ROUNDED if self.sound.enabled else ft.Icons.VOLUME_OFF_ROUNDED,
            icon_color="#E5E7EB",
            tooltip="Sound on / off",
            on_click=self._on_toggle_sound,
            **position,
        )
        self._mute_buttons.append(button)
        return button

    def _pill(self, text, icon, on_click, primary=True):
        pill = ft.Container(
            padding=ft.Padding.symmetric(horizontal=26, vertical=14),
            border_radius=ft.BorderRadius.all(30),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[ACCENT, "#6D28D9"] if primary else ["#331E293B", "#331E293B"],
            ),
            border=None if primary else ft.Border.all(1, "#8822D3EE"),
            shadow=ft.BoxShadow(blur_radius=24, spread_radius=-4, color="#99A855F7") if primary else None,
            scale=1.0,
            animate_scale=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
            on_click=on_click,
            content=ft.Row(
                tight=True,
                spacing=10,
                controls=[
                    ft.Icon(icon, size=20, color="#FFFFFF" if primary else ACCENT_2),
                    ft.Text(text, size=15, weight=ft.FontWeight.BOLD,
                            color="#FFFFFF" if primary else "#E5E7EB"),
                ],
            ),
        )

        def hover(e, c=pill):
            c.scale = 1.05 if e.data in (True, "true") else 1.0
            self._update(c)

        pill.on_hover = hover
        return pill

    def _stage(self, layers, height):
        return ft.ResponsiveRow(
            controls=[
                ft.Container(
                    col=12,
                    height=height,
                    bgcolor=DEEP_SPACE,
                    border=ft.Border.all(1, "#553B2A7A"),
                    border_radius=ft.BorderRadius.all(24),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    offset=ft.Offset(0, 0),
                    animate_offset=ft.Animation(55, ft.AnimationCurve.LINEAR),
                    content=ft.Stack(expand=True, controls=layers),
                )
            ]
        )

    async def _shake(self, control, strength=0.012):
        for dx in (strength, -strength, strength * 0.66, -strength * 0.5, strength * 0.25, 0):
            control.offset = ft.Offset(dx, 0)
            self._update(control)
            await asyncio.sleep(0.055)

    # =========================================================
    # INTRO
    # =========================================================

    async def _play_intro(self):
        token = self._next_token()
        self._screen = "intro"
        self._ensure_build()                   # the game builds while the story plays

        background = ft.Image(
            src=INTRO_IMAGE, fit=ft.BoxFit.COVER, left=0, top=0, right=0, bottom=0,
            opacity=0, scale=1.0,
            animate_opacity=ft.Animation(1400, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(16000, ft.AnimationCurve.LINEAR),
        )
        shade = _fill(gradient=ft.LinearGradient(
            begin=ft.Alignment.CENTER_LEFT, end=ft.Alignment.CENTER_RIGHT,
            colors=["#00000000", "#14020410", "#D0020410", "#F0020410"],
            stops=[0.0, 0.42, 0.72, 1.0],
        ))

        tag = _fading(ft.Text("AN AETHERIS TRANSMISSION", size=13, weight=ft.FontWeight.BOLD,
                              color=ACCENT_2, style=ft.TextStyle(letter_spacing=5)), dx=0.1, dy=0)
        title = _fading(
            ft.Column(spacing=10, controls=[
                ft.Text("SAVE EARTH", size=58, weight=ft.FontWeight.W_900, color="#FFFFFF",
                        style=ft.TextStyle(letter_spacing=8,
                                           shadow=ft.BoxShadow(blur_radius=28, color="#CCA855F7"))),
                ft.Container(width=96, height=3, bgcolor=ACCENT, border_radius=ft.BorderRadius.all(2)),
            ]),
            dx=0.1, dy=0, ms=900,
        )
        lines = [_fading(ft.Text(line, size=17, color="#E5E7EB")) for line in INTRO_LINES]
        begin = _fading(self._pill("Begin mission", ft.Icons.ROCKET_LAUNCH_ROUNDED, self._on_intro_done))

        story = ft.Container(
            right=56, top=0, bottom=0, width=500,
            alignment=ft.Alignment.CENTER_LEFT,
            content=ft.Column(
                tight=True, spacing=14,
                controls=[tag, title, ft.Container(height=6), *lines, ft.Container(height=10), begin],
            ),
        )
        skip = ft.TextButton("Skip intro", icon=ft.Icons.SKIP_NEXT_ROUNDED,
                             on_click=self._on_intro_done, right=18, bottom=12)

        self._mute_buttons = []
        self._set_content(self._stage(
            [background, shade, story, skip, self._mute_button(right=12, top=10)],
            self._stage_height(),
        ))

        if not await self._wait(token, 0.08):
            return
        self.sound.play("intro")
        background.opacity, background.scale = 1, 1.1
        self._update(background)
        if not await self._wait(token, 0.8):
            return
        self._reveal(tag)
        if not await self._wait(token, 0.35):
            return
        self._reveal(title)
        for line in lines:
            if not await self._wait(token, 1.55):
                return
            self._reveal(line)
        if not await self._wait(token, 0.9):
            return
        self._reveal(begin)

    def _on_intro_done(self, e=None):
        self._next_token()                     # stop the intro sequence
        self._show_briefing()

    # =========================================================
    # BRIEFING (the start page, themed)
    # =========================================================

    def _show_briefing(self, e=None):
        self._next_token()
        self._screen = "briefing"
        self._mute_buttons = []

        background = ft.Image(src=INTRO_IMAGE, fit=ft.BoxFit.COVER, left=0, top=0, right=0, bottom=0,
                              opacity=0.35)
        panel = ft.Container(
            width=640,
            padding=ft.Padding.symmetric(horizontal=34, vertical=30),
            bgcolor="#E00B1120",
            border=ft.Border.all(1, "#88A855F7"),
            border_radius=ft.BorderRadius.all(22),
            shadow=ft.BoxShadow(blur_radius=40, spread_radius=-8, color="#66A855F7"),
            content=ft.Column(
                tight=True, spacing=12,
                controls=[
                    ft.Text("MISSION BRIEFING", size=12, weight=ft.FontWeight.BOLD, color=ACCENT_2,
                            style=ft.TextStyle(letter_spacing=5)),
                    ft.Text("A Message from Aetheris", size=28, weight=ft.FontWeight.W_800, color="#FFFFFF"),
                    ft.Text(
                        "Aetheris will send five transmissions. Each describes the image they "
                        "want back. Choose the right tool, tune it, and transmit.",
                        size=14, color="#CBD5E1",
                    ),
                    ft.Container(height=4),
                    self._rule(ft.Icons.CHECK_CIRCLE_OUTLINE, AppColors.GREEN_LIGHT,
                               "Right tool, right setting: the message is accepted."),
                    self._rule(ft.Icons.REPLAY, AppColors.ORANGE,
                               "Right tool, wrong setting: one free retry per transmission."),
                    self._rule(ft.Icons.WARNING_AMBER_ROUNDED, AppColors.RED,
                               f"Wrong tool: a strike. {MAX_STRIKES} strikes and Aetheris destroys Earth."),
                    ft.Container(height=8),
                    ft.Row(
                        wrap=True, spacing=14, run_spacing=10,
                        controls=[
                            self._pill("Begin transmission", ft.Icons.SEND_ROUNDED, self._on_begin),
                            self._pill("Replay intro", ft.Icons.MOVIE_OUTLINED,
                                       self._on_replay_intro, primary=False),
                        ],
                    ),
                ],
            ),
        )
        self._set_content(self._stage(
            [background, _fill(bgcolor="#8C020410"),
             _fill(alignment=ft.Alignment.CENTER, content=panel),
             self._mute_button(right=12, top=10)],
            self._stage_height(minimum=600),
        ))

    def _on_replay_intro(self, e=None):
        if self.page is not None:
            self.page.run_task(self._play_intro)

    # =========================================================
    # GAMEPLAY (rules and layout unchanged)
    # =========================================================

    def _show_loading(self):
        self._screen = "round"
        self.body.controls = [
            self._panel(
                ft.Row(
                    spacing=14,
                    controls=[
                        ft.ProgressRing(width=22, height=22, stroke_width=3, color=ACCENT),
                        ft.Text("Receiving transmissions from Aetheris…", size=13, color=AppColors.TEXT),
                    ],
                )
            )
        ]
        self._set_content(self._card)

    def _show_round(self, verdict: Verdict | None = None, sent_image=None, fresh=False, transmitting=False):
        self._screen = "round"
        s = self.session
        ch = s.current if verdict is None or not verdict.round_over else s.challenges[s.round_index - 1]

        if fresh:
            self._awaiting_continue = False
            self._tool_selector = SegmentedSelector(
                [(t.id, t.name, _icon(TOOL_ICONS[t.id])) for t in TOOLS],
                value=TOOLS[0].id,
                accent=ACCENT,
                on_change=self._on_tool_change,
            )
            self._option_holder = ft.Container()
            self._build_option_selector(TOOLS[0].id)

        transmission = self._panel(
            ft.Column(
                spacing=12,
                controls=[
                    self._title_row(ft.Icons.SATELLITE_ALT, f"Transmission: {ch.title}", ACCENT_2),
                    ft.Text(f"“{ch.riddle}”", size=13, italic=True, color=AppColors.TEXT),
                    self._image_box(ch.received, "Received image"),
                ],
            ),
            col={"xs": 12, "lg": 5},
        )

        console_controls = [
            parameter_card("Toolbox", ft.Icons.HANDYMAN_OUTLINED, ACCENT,
                           [self._tool_selector.control,
                            hint("Spatial and frequency tools. Choose the one the message calls for.")],
                           col={"xs": 12}),
            parameter_card("Setting", ft.Icons.TUNE, ACCENT, [self._option_holder], col={"xs": 12}),
        ]

        if transmitting:
            console_controls.append(
                ft.Container(
                    col={"xs": 12},
                    padding=AppLayout.SMALL_PADDING,
                    bgcolor=AppColors.SURFACE_SOFT,
                    border=ft.Border.all(1, ACCENT),
                    border_radius=ft.BorderRadius.all(AppLayout.INNER_RADIUS),
                    content=ft.Row(spacing=12, controls=[
                        ft.ProgressRing(width=20, height=20, stroke_width=3, color=ACCENT_2),
                        ft.Text("Transmitting to Aetheris…", size=13, color=AppColors.TEXT),
                    ]),
                )
            )
        elif self._awaiting_continue:
            last = s.phase is not Phase.PLAYING
            console_controls.append(
                ActionButton(
                    "See Earth's fate" if last else "Next transmission",
                    "Aetheris has decided" if last else "Receive the next message from Aetheris",
                    ft.Icons.ARROW_FORWARD_ROUNDED,
                    ACCENT_2,
                    self._on_continue,
                    col={"xs": 12},
                ).control
            )
        else:
            console_controls.append(
                ActionButton(
                    "Transmit",
                    "Send your processed image to Aetheris",
                    ft.Icons.SEND_ROUNDED,
                    ACCENT,
                    self._on_transmit,
                    col={"xs": 12},
                ).control
            )

        if verdict is not None:
            console_controls.append(self._reply_panel(ch, verdict, sent_image))

        console = ft.Container(
            col={"xs": 12, "lg": 7},
            content=ft.ResponsiveRow(spacing=12, run_spacing=12, controls=console_controls),
        )

        self._mute_buttons = []
        self.body.controls = [
            self._status_strip(),
            ft.ResponsiveRow(spacing=16, run_spacing=16, controls=[transmission, console]),
        ]
        if self.control.content is not self._card:
            self._set_content(self._card)
        else:
            self._refresh()

    # =========================================================
    # ENDING (cinematic)
    # =========================================================

    def _show_ending(self):
        token = self._next_token()
        self._screen = "ending"
        s = self.session
        won = s.phase is Phase.WON
        accent = WIN_COLOR if won else LOSE_COLOR

        background = ft.Image(
            src=SAVED_IMAGE if won else DESTROYED_IMAGE,
            fit=ft.BoxFit.COVER, left=0, top=0, right=0, bottom=0,
            opacity=0, scale=1.0,
            animate_opacity=ft.Animation(1000, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(18000, ft.AnimationCurve.LINEAR),
        )
        shade = _fill(gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER, end=ft.Alignment.BOTTOM_CENTER,
            colors=["#00000000", "#00000000", "#E6020410"],
            stops=[0.0, 0.42 if won else 0.3, 1.0],     # darker band reaches higher for game over
        ))
        flash = _fill(
            bgcolor="#FFFFD6A0" if not won else "#99FDE68A",
            opacity=0,
            animate_opacity=ft.Animation(900, ft.AnimationCurve.EASE_OUT),
        )

        lines_text = WIN_LINES if won else LOSE_LINES
        text_lines = []
        for i, line in enumerate(lines_text):
            if i == 0:
                # A tight dark shadow keeps the letters crisp; a soft red glow sits behind it.
                glow = "#99B91C1C" if not won else "#886EE7B7"
                text = ft.Text(line, size=52, weight=ft.FontWeight.W_900, color=accent,
                               text_align=ft.TextAlign.CENTER,
                               style=ft.TextStyle(letter_spacing=2, shadow=[
                                   ft.BoxShadow(blur_radius=4, color="#E6000000"),
                                   ft.BoxShadow(blur_radius=22, color=glow),
                               ]))
            else:
                text = ft.Text(line, size=28, weight=ft.FontWeight.W_600, color="#FFFFFF",
                               text_align=ft.TextAlign.CENTER,
                               style=ft.TextStyle(shadow=ft.BoxShadow(blur_radius=12, color="#E6000000")))
            text_lines.append(_fading(text, dy=0.4, ms=800))

        stats = _fading(ft.Text(
            (f"Aetheris understood {s.accepted_count} of {s.total_rounds} transmissions.")
            if won else
            (f"{s.strikes} failed transmissions after {s.round_index} of {s.total_rounds}."),
            size=14, color="#CBD5E1", text_align=ft.TextAlign.CENTER,
        ), dy=0.4)

        height = self._stage_height()
        words = ft.Container(
            # Game over sits higher, over the darker middle of the artwork.
            left=24, right=24, bottom=34 if won else int(height * 0.2),
            content=ft.Column(tight=True, spacing=6,
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                              controls=[*text_lines, ft.Container(height=6), stats]),
        )

        self._mute_buttons = []
        stage = self._stage([background, shade, flash, words, self._mute_button(right=12, top=10)],
                            height)

        buttons = _fading(ft.Row(
            wrap=True, spacing=14, run_spacing=10, alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                self._pill("Play again", ft.Icons.REPLAY_ROUNDED, self._on_play_again),
                self._pill("Mission briefing", ft.Icons.MENU_BOOK_OUTLINED, self._show_briefing, primary=False),
                self._pill("Replay intro", ft.Icons.MOVIE_OUTLINED, self._on_replay_intro, primary=False),
            ],
        ), dy=0.3)

        self._ending_fades = [*text_lines, stats, buttons]
        self._set_content(ft.Column(spacing=18, controls=[stage, buttons, self._transmission_log()]))

        if self.page is not None:
            self.page.run_task(self._play_ending, token, won, background, flash, stage.controls[0])
        else:
            for c in self._ending_fades:
                c.opacity = 1

    async def _play_ending(self, token, won, background, flash, frame):
        if not await self._wait(token, 0.08):
            return
        if won:
            self.sound.play("victory")
            background.opacity, background.scale = 1, 1.06
            flash.opacity = 0.6
            self._update(background)
            self._update(flash)
            if not await self._wait(token, 0.25):
                return
            flash.opacity = 0
            self._update(flash)
        else:
            self.sound.play("gameover")
            flash.opacity = 0.95
            self._update(flash)
            if not await self._wait(token, 0.12):
                return
            background.opacity, background.scale = 1, 1.06
            flash.opacity = 0
            self._update(background)
            self._update(flash)
            await self._shake(frame, strength=0.01)
        if not await self._wait(token, 0.8):
            return
        for c in self._ending_fades[:-1]:
            self._reveal(c)
            if not await self._wait(token, 0.65):
                return
        self._reveal(self._ending_fades[-1])

    def _transmission_log(self):
        rows = []
        for (ch, tool_id, option, verdict) in self.session.history:
            outcome_color = {
                Outcome.ACCEPTED: AppColors.GREEN_LIGHT,
                Outcome.RETRY: AppColors.ORANGE,
                Outcome.STRIKE: AppColors.RED,
            }[verdict.outcome]
            rows.append(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=12, vertical=9),
                    bgcolor=AppColors.SURFACE_DARK,
                    border_radius=ft.BorderRadius.all(AppLayout.SMALL_RADIUS),
                    content=ft.Row(
                        wrap=True,
                        spacing=10,
                        controls=[
                            ft.Text(ch.title, size=12, weight=ft.FontWeight.BOLD, color=AppColors.TEXT, width=190),
                            ft.Text(f"You: {TOOLS_BY_ID[tool_id].name} · {option}", size=11,
                                    color=AppColors.TEXT_SECONDARY, width=280),
                            ft.Text(verdict.outcome.value.upper(), size=11, weight=ft.FontWeight.BOLD,
                                    color=outcome_color, width=80),
                            ft.Text(f"Best: {ch.tool.name} · {ch.best_option} ({self._best_note(ch)})",
                                    size=11, color=AppColors.MUTED),
                        ],
                    ),
                )
            )
        return ft.Container(
            bgcolor=AppColors.SURFACE,
            border=ft.Border.all(1, AppColors.BORDER),
            border_radius=ft.BorderRadius.all(AppLayout.CARD_RADIUS),
            padding=AppLayout.CARD_PADDING,
            content=ft.Column(
                spacing=8,
                controls=[self._title_row(ft.Icons.INSIGHTS_OUTLINED, "Transmission log", ACCENT_2)] + rows,
            ),
        )

    # =========================================================
    # EVENTS
    # =========================================================

    async def _on_begin(self, e=None):
        if self._building:
            return
        self._building = True
        try:
            self._ensure_build()
            if not self._build_future.done():
                self._show_loading()
            self.session = await self._build_future
        except Exception as error:  # show the failure instead of freezing on the spinner
            self.body.controls = [
                self._panel(ft.Text(f"Could not build the game: {error}", color=AppColors.RED, size=13))
            ]
            self._set_content(self._card)
            return
        finally:
            self._build_future = None
            self._building = False
        self._show_round(fresh=True)

    async def _on_play_again(self, e=None):
        self._next_token()
        self._build_future = None
        await self._on_begin()

    def _on_tool_change(self, tool_id):
        if self._awaiting_continue or self._transmitting:
            return
        self._build_option_selector(tool_id)
        self._refresh()

    async def _on_transmit(self, e=None):
        if self.session is None or self._awaiting_continue or self._transmitting:
            return
        tool_id = self._tool_selector.get_value()
        option = self._option_selector.get_value()
        ch = self.session.current

        self._transmitting = True
        self._show_round(transmitting=True)
        self.sound.play("transmit")
        await asyncio.sleep(0.5)

        verdict = self.session.submit(tool_id, option)
        sent = ch.outputs.get(option) if tool_id == ch.correct_tool else None
        self._transmitting = False
        self._awaiting_continue = verdict.round_over
        self._show_round(verdict, sent)

        self.sound.play(VERDICT_SOUNDS[verdict.outcome])
        if verdict.outcome is Outcome.STRIKE:
            await self._shake(self._card, strength=0.006)

    def _on_continue(self, e=None):
        if self.session.phase is Phase.PLAYING:
            self._show_round(fresh=True)
        else:
            self._show_ending()

    def _on_toggle_sound(self, e=None):
        on = self.sound.toggle()
        for button in self._mute_buttons:
            button.icon = ft.Icons.VOLUME_UP_ROUNDED if on else ft.Icons.VOLUME_OFF_ROUNDED
            self._update(button)

    def _open_discover(self, route_key):
        if not self.on_open_discover:
            return
        try:
            self.on_open_discover(route_key)
        except Exception:
            pass  # unknown route: stay in the game rather than crash

    @staticmethod
    def _best_note(ch):
        if ch.mode == "choice":
            return ch.answer_note.rstrip(".")
        return _db(ch.scores[ch.best_option])

    # =========================================================
    # PIECES
    # =========================================================

    def _build_option_selector(self, tool_id):
        tool = TOOLS_BY_ID[tool_id]
        self._option_selector = SegmentedSelector(
            [(opt, opt, ft.Icons.TUNE) for opt in tool.options],
            value=tool.options[0],
            accent=ACCENT_2,
        )
        self._option_holder.content = ft.Column(
            spacing=8,
            controls=[
                ft.Text(tool.param_label, size=11, color=AppColors.TEXT_SECONDARY),
                self._option_selector.control,
            ],
        )

    def _status_strip(self):
        s = self.session
        level = s.anger
        color = ANGER_COLORS[level]
        pips = [
            ft.Container(
                width=14, height=14, border_radius=7,
                bgcolor=AppColors.RED if i < s.strikes else AppColors.SURFACE_3,
                border=ft.Border.all(1, AppColors.BORDER_SOFT),
            )
            for i in range(MAX_STRIKES)
        ]
        round_no = min(s.round_index + (0 if self._awaiting_continue else 1), s.total_rounds)
        return self._panel(
            ft.Row(
                wrap=True,
                spacing=18,
                controls=[
                    ft.Text(f"Transmission {round_no} of {s.total_rounds}", size=13,
                            weight=ft.FontWeight.BOLD, color=AppColors.TEXT),
                    ft.Row(spacing=8, controls=[
                        ft.Text("Aetheris mood:", size=12, color=AppColors.TEXT_SECONDARY),
                        ft.Text(ANGER_LEVELS[level], size=12, weight=ft.FontWeight.BOLD, color=color),
                    ]),
                    ft.Row(spacing=6, controls=[ft.Text("Strikes", size=12, color=AppColors.TEXT_SECONDARY)] + pips),
                    ft.Text(
                        "Retry used" if s.retry_used else "Retry available",
                        size=12,
                        color=AppColors.MUTED if s.retry_used else AppColors.GREEN_LIGHT,
                    ),
                
                    self._mute_button(),
                ],
            )
        )

    def _reply_panel(self, ch, verdict: Verdict, sent_image):
        color, icon = {
            Outcome.ACCEPTED: (AppColors.GREEN_LIGHT, ft.Icons.CHECK_CIRCLE_OUTLINE),
            Outcome.RETRY: (AppColors.ORANGE, ft.Icons.REPLAY),
            Outcome.STRIKE: (AppColors.RED, ft.Icons.WARNING_AMBER_ROUNDED),
        }[verdict.outcome]

        controls = [
            ft.Row(spacing=10, controls=[
                ft.Icon(icon, color=color, size=20),
                ft.Text("Reply from Aetheris", size=12, weight=ft.FontWeight.BOLD, color=AppColors.TEXT),
            ]),
            ft.Text(verdict.message, size=13, color=color),
        ]
        if verdict.psnr is not None and ch.mode != "choice":
            target = "their target" if ch.mode == "match" else "the original"
            controls.append(ft.Text(
                f"Signal quality vs {target}: {_db(verdict.psnr)}   (needed ≥ {ch.pass_db:.2f} dB)",
                size=11, color=AppColors.TEXT_SECONDARY,
            ))
        if ch.mode == "choice" and verdict.round_over and ch.answer_note:
            controls.append(ft.Text(ch.answer_note, size=11, color=AppColors.TEXT_SECONDARY))
        if sent_image is not None:
            caption = ("The spectrum you read the answer from" if ch.mode == "choice"
                       else "What you sent")
            controls.append(self._image_box(sent_image, caption))
        if verdict.hint:
            controls.append(ft.Text(verdict.hint, size=12, color=AppColors.TEXT_SECONDARY))
            route = ch.discover_route
            if route and self.on_open_discover:
                key, label = route
                controls.append(
                    ft.TextButton(
                        f"Open Discover → {label}",
                        icon=ft.Icons.AUTO_STORIES_OUTLINED,
                        on_click=lambda e, k=key: self._open_discover(k),
                    )
                )

        return ft.Container(
            col={"xs": 12},
            padding=AppLayout.SMALL_PADDING,
            bgcolor=AppColors.SURFACE_SOFT,
            border=ft.Border.all(1, color),
            border_radius=ft.BorderRadius.all(AppLayout.INNER_RADIUS),
            content=ft.Column(spacing=10, controls=controls),
        )

    def _image_box(self, array, caption):
        return ft.Column(
            spacing=6,
            controls=[
                ft.Container(
                    width=IMAGE_SIZE,
                    height=IMAGE_SIZE,
                    bgcolor=AppColors.SURFACE_DARK,
                    border=ft.Border.all(1, AppColors.BORDER_SOFT),
                    border_radius=ft.BorderRadius.all(AppLayout.SMALL_RADIUS),
                    content=ft.Image(src=_png(array), width=IMAGE_SIZE, height=IMAGE_SIZE,
                                     fit=ft.BoxFit.CONTAIN, gapless_playback=True),
                ),
                hint(caption),
            ],
        )

    @staticmethod
    def _panel(content, col=None):
        return ft.Container(
            col=col,
            padding=AppLayout.SMALL_PADDING,
            bgcolor=AppColors.SURFACE_SOFT,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            border_radius=ft.BorderRadius.all(AppLayout.INNER_RADIUS),
            content=content,
        )

    @staticmethod
    def _title_row(icon, text, color):
        return ft.Row(spacing=8, controls=[
            ft.Icon(icon, size=18, color=color),
            ft.Text(text, size=14, weight=ft.FontWeight.BOLD, color=AppColors.TEXT),
        ])

    @staticmethod
    def _rule(icon, color, text):
        return ft.Row(spacing=10, controls=[
            ft.Icon(icon, size=16, color=color),
            ft.Text(text, size=12, color=AppColors.TEXT_SECONDARY, expand=True),
        ])

    def _refresh(self):
        try:
            self.control.update()
        except Exception:
            pass  # not mounted yet; the next navigation will draw it

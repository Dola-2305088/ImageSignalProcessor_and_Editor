"""SaveEarth game mode view (step 2: plain, fully playable loop).

Screens:  lobby  ->  loading  ->  round (repeat)  ->  ending

All game rules live in game/ (pure Python). This view only draws the
current state of a GameSession and forwards the player's choices to it.
build_session() runs the algorithms, so it goes through asyncio.to_thread;
submit() is an instant lookup.

Deliberately, nothing previews a tool's output before Transmit: a preview
that only worked for the correct tool would give the answer away.

Animation (fleet, anger meter, intro/ending slides) arrives in step 3 and
hooks into start()/stop(), which main_window already calls on navigation.
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
from ui.components.section_header import SectionHeader
from ui.components.spatial_controls import (
    ActionButton,
    SegmentedSelector,
    hint,
    parameter_card,
)
from ui.theme import AppColors, AppLayout

ACCENT = "#34D399"      # SaveEarth card accent on Home
ACCENT_2 = "#22D3EE"
IMAGE_SIZE = 256        # on-screen size of the 128x128 game images

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

# Where a player should go to relearn what a challenge tests.
DISCOVER_ROUTES = {
    "noise": ("learn_noise", "Noise lesson"),
    "edges": ("learn_convolution", "Convolution lesson"),
    "wiener": ("learn_restore", "Restoration lesson"),
}

ANGER_COLORS = (AppColors.GREEN_LIGHT, AppColors.ORANGE, AppColors.RED, AppColors.RED)


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


class SaveEarthView:
    def __init__(self, page, on_open_discover=None):
        self.page = page
        self.on_open_discover = on_open_discover

        self.session: GameSession | None = None
        self._building = False
        self._active = False
        self._awaiting_continue = False
        self._tool_selector = None
        self._option_selector = None

        self.header = SectionHeader(
            badge="SAVEEARTH  •  GAME MODE",
            title="A Message from Aetheris",
            subtitle="Aetheris speaks only in images. Answer well, and Earth gains a friend among the stars.",
            icon=ft.Icons.PUBLIC,
            accent=ACCENT,
        )

        self.body = ft.Column(spacing=18)

        self.control = ft.Container(
            bgcolor=AppColors.SURFACE,
            border=ft.Border.all(1, AppColors.BORDER),
            border_radius=ft.BorderRadius.all(AppLayout.CARD_RADIUS),
            padding=AppLayout.CARD_PADDING,
            content=ft.Column(spacing=18, controls=[self.header.control, self.body]),
        )

        self._show_lobby()

    # =========================================================
    # LIFECYCLE (called by main_window on navigation)
    # =========================================================

    def start(self):
        self._active = True

    def stop(self):
        # Step 3 will stop the fleet animation loop here.
        self._active = False

    # =========================================================
    # SCREENS
    # =========================================================

    def _show_lobby(self):
        self.session = None
        self.body.controls = [
            self._panel(
                ft.Column(
                    spacing=10,
                    controls=[
                        self._title_row(ft.Icons.SATELLITE_ALT, "Incoming signal from Aetheris", ACCENT_2),
                        ft.Text(
                            "Beings from the planet Aetheris have arrived in Earth's orbit. They "
                            "come seeking friendship, but they speak only in images. They will send "
                            "you transmissions and describe the image they want back. In this "
                            "image-processing universe, your knowledge is Earth's only hope: pick the "
                            "right tool, tune it, and transmit. Fail them, and they will destroy "
                            "our worthless planet.",
                            size=13,
                            color=AppColors.TEXT_SECONDARY,
                        ),
                        self._rule(ft.Icons.CHECK_CIRCLE_OUTLINE, AppColors.GREEN_LIGHT,
                                   "Right tool, right setting: the message is accepted."),
                        self._rule(ft.Icons.REPLAY, AppColors.ORANGE,
                                   "Right tool, wrong setting: one free retry per transmission."),
                        self._rule(ft.Icons.WARNING_AMBER_ROUNDED, AppColors.RED,
                                   f"Wrong tool: Aetheris loses faith in Earth. {MAX_STRIKES} strikes and they destroy it."),
                    ],
                )
            ),
            ft.ResponsiveRow(
                controls=[
                    ActionButton(
                        "Begin transmission",
                        "Open the channel to Aetheris",
                        ft.Icons.ROCKET_LAUNCH_OUTLINED,
                        ACCENT,
                        self._on_begin,
                        col={"xs": 12, "md": 6},
                    ).control
                ]
            ),
        ]
        self._refresh()

    def _show_loading(self):
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
        self._refresh()

    def _show_round(self, verdict: Verdict | None = None, sent_image=None):
        s = self.session
        ch = s.current if verdict is None or not verdict.round_over else s.challenges[s.round_index - 1]

        if verdict is None:
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

        if self._awaiting_continue:
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

        self.body.controls = [
            self._status_strip(),
            ft.ResponsiveRow(spacing=16, run_spacing=16, controls=[transmission, console]),
        ]
        self._refresh()

    def _show_ending(self):
        s = self.session
        won = s.phase is Phase.WON
        color = AppColors.GREEN_LIGHT if won else AppColors.RED

        rows = []
        for (ch, tool_id, option, verdict) in s.history:
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
                            ft.Text(ch.title, size=12, weight=ft.FontWeight.BOLD, color=AppColors.TEXT, width=170),
                            ft.Text(f"You: {TOOLS_BY_ID[tool_id].name} · {option}", size=11,
                                    color=AppColors.TEXT_SECONDARY, width=260),
                            ft.Text(verdict.outcome.value.upper(), size=11, weight=ft.FontWeight.BOLD,
                                    color=outcome_color, width=80),
                            ft.Text(f"Best: {ch.tool.name} · {ch.best_option} ({_db(ch.scores[ch.best_option])})",
                                    size=11, color=AppColors.MUTED),
                        ],
                    ),
                )
            )

        self.body.controls = [
            self._panel(
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Row(
                            spacing=12,
                            controls=[
                                ft.Icon(ft.Icons.PUBLIC if won else ft.Icons.WARNING_AMBER_ROUNDED,
                                        color=color, size=30),
                                ft.Text("FRIENDSHIP ESTABLISHED" if won else "EARTH HAS BEEN DESTROYED",
                                        size=22, weight=ft.FontWeight.BOLD, color=color),
                            ],
                        ),
                        ft.Text(
                            (f"Aetheris understood {s.accepted_count} of {s.total_rounds} messages. "
                             f"Your knowledge saved Earth, and it now has a friend among the stars.")
                            if won else
                            (f"{s.strikes} failed messages after {s.round_index} of {s.total_rounds} "
                             f"transmissions. Aetheris judged our planet worthless and erased it."),
                            size=13,
                            color=AppColors.TEXT_SECONDARY,
                        ),
                    ],
                )
            ),
            self._panel(
                ft.Column(
                    spacing=8,
                    controls=[self._title_row(ft.Icons.INSIGHTS_OUTLINED, "Transmission log", ACCENT_2)] + rows,
                )
            ),
            ft.ResponsiveRow(
                controls=[
                    ActionButton("Play again", "New messages from Aetheris", ft.Icons.REPLAY,
                                 ACCENT, self._on_begin, col={"xs": 12, "md": 6}).control,
                    ActionButton("Back to briefing", "Read the rules again", ft.Icons.MENU_BOOK_OUTLINED,
                                 ACCENT_2, lambda e: self._show_lobby(), col={"xs": 12, "md": 6}).control,
                ]
            ),
        ]
        self._refresh()

    # =========================================================
    # EVENTS
    # =========================================================

    async def _on_begin(self, e=None):
        if self._building:
            return
        self._building = True
        self._show_loading()
        try:
            self.session = await asyncio.to_thread(build_session)
        except Exception as error:  # show the failure instead of freezing on the spinner
            self.body.controls = [
                self._panel(ft.Text(f"Could not build the game: {error}", color=AppColors.RED, size=13))
            ]
            self._refresh()
            return
        finally:
            self._building = False
        self._show_round()

    def _on_tool_change(self, tool_id):
        if self._awaiting_continue:
            return
        self._build_option_selector(tool_id)
        self._refresh()

    def _on_transmit(self, e=None):
        if self.session is None or self._awaiting_continue:
            return
        tool_id = self._tool_selector.get_value()
        option = self._option_selector.get_value()
        ch = self.session.current

        verdict = self.session.submit(tool_id, option)
        sent = ch.outputs.get(option) if tool_id == ch.correct_tool else None

        self._awaiting_continue = verdict.round_over
        self._show_round(verdict, sent)

    def _on_continue(self, e=None):
        if self.session.phase is Phase.PLAYING:
            self._show_round()
        else:
            self._show_ending()

    def _open_discover(self, route_key):
        if self.on_open_discover:
            self.on_open_discover(route_key)

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
        if verdict.psnr is not None:
            target = "their target" if ch.mode == "match" else "the original"
            controls.append(ft.Text(
                f"Signal quality vs {target}: {_db(verdict.psnr)}   (needed ≥ {ch.pass_db:.2f} dB)",
                size=11, color=AppColors.TEXT_SECONDARY,
            ))
        if sent_image is not None:
            controls.append(self._image_box(sent_image, "What you sent"))
        if verdict.hint:
            controls.append(ft.Text(verdict.hint, size=12, color=AppColors.TEXT_SECONDARY))
            route = DISCOVER_ROUTES.get(ch.id)
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

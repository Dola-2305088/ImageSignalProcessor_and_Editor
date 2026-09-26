"""SaveEarth game session (no UI code here).

Rules:
  * Always 5 rounds, each with a DIFFERENT tool, mixing at least 2 spatial
    and 2 frequency tools. Each tool has several puzzle variants, so
    repeated games stay fresh.
  * Wrong tool                          -> strike, next round.
  * Right tool, option below the bar    -> one free retry per round;
                                           failing the retry is a strike.
  * Right tool, option passes           -> accepted, next round.
  * 3 strikes                           -> Aetheris destroys Earth (LOST).
  * All rounds done with < 3 strikes    -> friendship established (WON).

Heavy work happens only in build_session() (call it with asyncio.to_thread
from the UI, e.g. while the intro story plays). submit() is instant.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from game.challenges import CHALLENGE_BUILDERS, CHALLENGE_VARIANTS, Challenge
from game.scene import make_space_scene
from game.tools import TOOLS_BY_ID

MIN_PER_DOMAIN = 2

MAX_STRIKES = 3
DEFAULT_ROUNDS = 5
ANGER_LEVELS = ("Friendly", "Doubtful", "Hostile", "Destroying")  # index = strikes


class Phase(Enum):
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


class Outcome(Enum):
    ACCEPTED = "accepted"
    RETRY = "retry"
    STRIKE = "strike"


@dataclass(frozen=True)
class Verdict:
    outcome: Outcome
    message: str               # the aliens' reply
    psnr: float | None         # None when the wrong tool was used
    hint: str | None           # only after a strike
    round_over: bool           # True -> UI should advance to the next round / ending


class GameSession:
    def __init__(self, challenges: list[Challenge]):
        if not challenges:
            raise ValueError("A game needs at least one challenge.")
        self.challenges = challenges
        self.round_index = 0
        self.strikes = 0
        self.retry_used = False
        self.history: list[tuple[Challenge, str, str, Verdict]] = []  # (challenge, tool, option, verdict)

    # ----------------------------------------------------------- read-only state
    @property
    def total_rounds(self) -> int:
        return len(self.challenges)

    @property
    def phase(self) -> Phase:
        if self.strikes >= MAX_STRIKES:
            return Phase.LOST
        if self.round_index >= self.total_rounds:
            return Phase.WON
        return Phase.PLAYING

    @property
    def current(self) -> Challenge | None:
        return self.challenges[self.round_index] if self.phase is Phase.PLAYING else None

    @property
    def anger(self) -> int:
        return min(self.strikes, MAX_STRIKES)

    @property
    def anger_label(self) -> str:
        return ANGER_LEVELS[self.anger]

    @property
    def accepted_count(self) -> int:
        return sum(1 for *_, v in self.history if v.outcome is Outcome.ACCEPTED)

    # ----------------------------------------------------------- actions
    def submit(self, tool_id: str, option: str) -> Verdict:
        ch = self.current
        if ch is None:
            raise RuntimeError(f"Game is over ({self.phase.value}).")
        if tool_id not in TOOLS_BY_ID:
            raise KeyError(f"Unknown tool {tool_id!r}")

        if tool_id != ch.correct_tool:
            verdict = self._strike(ch, psnr=None,
                                   message="That is not what we asked for. Aetheris begins to doubt Earth.")
        elif ch.passes(option):
            verdict = Verdict(Outcome.ACCEPTED,
                              "Signal received and understood. Aetheris welcomes your reply, and the friendship grows.",
                              ch.scores[option], None, round_over=True)
            self._next_round()
        elif not self.retry_used:
            self.retry_used = True
            verdict = Verdict(Outcome.RETRY,
                              f"Close... but the signal is still distorted. "
                              f"Adjust your {ch.tool.param_label.lower()} and transmit again.",
                              ch.scores[option], None, round_over=False)
        else:
            verdict = self._strike(ch, psnr=ch.scores[option],
                                   message="Still distorted. The patience of Aetheris is fading.")

        self.history.append((ch, tool_id, option, verdict))
        return verdict

    # ----------------------------------------------------------- internals
    def _strike(self, ch: Challenge, psnr: float | None, message: str) -> Verdict:
        self.strikes += 1
        if self.strikes >= MAX_STRIKES:
            message = "Enough. Earth cannot speak our language. Aetheris will erase this worthless planet."
        self._next_round()
        return Verdict(Outcome.STRIKE, message, psnr, ch.hint, round_over=True)

    def _next_round(self) -> None:
        self.round_index += 1
        self.retry_used = False


def plan_rounds(rng: np.random.Generator, rounds: int = DEFAULT_ROUNDS) -> list[tuple[str, str]]:
    """Choose (challenge type, variant) pairs for one game.

    Every round uses a different tool; at least MIN_PER_DOMAIN spatial and
    MIN_PER_DOMAIN frequency tools (when that many exist); one random
    variant per tool.
    """
    types = list(CHALLENGE_VARIANTS)
    if rounds > len(types):
        raise ValueError(f"Only {len(types)} tools have challenges; cannot fill {rounds} rounds.")

    by_domain: dict[str, list[str]] = {}
    for cid in types:
        by_domain.setdefault(TOOLS_BY_ID[cid].domain, []).append(cid)

    chosen: list[str] = []
    for members in by_domain.values():                       # guaranteed share per domain
        take = min(MIN_PER_DOMAIN, len(members), rounds - len(chosen))
        chosen += [str(c) for c in rng.choice(members, size=take, replace=False)]
    rest = [c for c in types if c not in chosen]             # fill the remaining rounds
    chosen += [str(c) for c in rng.choice(rest, size=rounds - len(chosen), replace=False)]

    order = [chosen[i] for i in rng.permutation(len(chosen))]
    return [(cid, str(rng.choice(CHALLENGE_VARIANTS[cid]))) for cid in order]


def build_session(seed: int | None = None, rounds: int = DEFAULT_ROUNDS) -> GameSession:
    """Build a new game. Slow (runs the algorithms); call it off the UI thread."""
    rng = np.random.default_rng(seed)
    clean = make_space_scene(seed=int(rng.integers(0, 2**31)))
    return GameSession([
        CHALLENGE_BUILDERS[cid](clean, rng, variant) for cid, variant in plan_rounds(rng, rounds)
    ])

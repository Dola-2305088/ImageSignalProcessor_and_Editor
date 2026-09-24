"""SaveEarth backend smoke test.

Run from the project root:
    python -m game.smoke_test

1. prints the algorithm signatures the game relies on
2. builds every puzzle variant and checks it is fair (the intended
   setting passes, the classic mistake fails)
3. checks the rules: 5 rounds, 3 strikes = Earth destroyed, 2 strikes can still win
4. saves one game's images to game/_smoke_out/
"""

from __future__ import annotations

import inspect
import time
from pathlib import Path

import numpy as np
from PIL import Image

from algorithms.spatial import convolution, edge_detection, motion_blur, noise_cleaner, wiener
from game.challenges import CHALLENGE_BUILDERS, CHALLENGE_VARIANTS
from game.game_state import DEFAULT_ROUNDS, MAX_STRIKES, Outcome, Phase, build_session
from game.scene import make_space_scene

OUT = Path(__file__).parent / "_smoke_out"

# The setting that must FAIL in each variant (the classic wrong choice).
MUST_FAIL = {
    ("noise", "salt_pepper"): "Mean",
    ("edges", "combined"): "Horizontal",
    ("edges", "horizontal"): "Vertical",
    ("edges", "vertical"): "Horizontal",
    ("wiener", "horizontal"): "Inverse filter",
    ("wiener", "vertical"): "Inverse filter",
    ("wiener", "diagonal"): "Inverse filter",
}


def show_signatures() -> None:
    print("== Algorithm signatures used by the game ==")
    for fn in (convolution.convolve2d, motion_blur.create_motion_kernel,
               noise_cleaner.mean_filter, noise_cleaner.gaussian_filter, noise_cleaner.median_filter,
               edge_detection.horizontal_edges, edge_detection.vertical_edges, edge_detection.combined_edges,
               wiener.inverse_deconvolution, wiener.wiener_deconvolution):
        print(f"  {fn.__module__}.{fn.__name__}{inspect.signature(fn)}")


def check_variants(seeds=(1, 2, 3)) -> None:
    print("\n== Every puzzle variant (3 seeds each) ==")
    problems = []
    for cid, variants in CHALLENGE_VARIANTS.items():
        for variant in variants:
            for seed in seeds:
                rng = np.random.default_rng(seed)
                ch = CHALLENGE_BUILDERS[cid](make_space_scene(seed=seed), rng, variant)
                passing = [o for o in ch.tool.options if ch.passes(o)]
                bad = MUST_FAIL.get((cid, variant))
                ok = bool(passing) and (bad is None or bad not in passing)
                if not ok:
                    problems.append(f"{cid}/{variant}/seed{seed}")
                if seed == seeds[0]:
                    scores = "  ".join(f"{o}={ch.scores[o]:.1f}" for o in ch.tool.options)
                    print(f"  {cid:<7}{variant:<12} pass>={ch.pass_db:6.2f}  passing={passing}")
                    print(f"      {scores}")
    assert not problems, f"Unfair puzzles: {problems}"
    print("  All variants fair.")


def report_one_game(seed: int) -> None:
    t0 = time.perf_counter()
    s = build_session(seed=seed)
    print(f"\n== One game (seed {seed}): {s.total_rounds} rounds built in {time.perf_counter() - t0:.2f} s ==")
    OUT.mkdir(exist_ok=True)
    for i, ch in enumerate(s.challenges, 1):
        print(f"  {i}. {ch.title:<22} tool={ch.tool.name:<22} best={ch.best_option}")
        Image.fromarray(ch.received).save(OUT / f"{i}_{ch.id}_{ch.variant}_received.png")
        Image.fromarray(ch.outputs[ch.best_option]).save(OUT / f"{i}_{ch.id}_{ch.variant}_answer.png")


def _wrong_tool(ch) -> str:
    return "color" if ch.correct_tool != "color" else "edges"


def check_rules(seeds=range(10)) -> None:
    for seed in seeds:
        # Always 5 rounds, no same tool twice in a row
        s = build_session(seed=seed)
        assert s.total_rounds == DEFAULT_ROUNDS, "a game must have 5 rounds"
        kinds = [c.id for c in s.challenges]
        assert all(a != b for a, b in zip(kinds, kinds[1:])), f"same tool twice in a row: {kinds}"
        assert len({(c.id, c.variant) for c in s.challenges}) == DEFAULT_ROUNDS, "a puzzle repeated"

        # Perfect run -> won
        while s.phase is Phase.PLAYING:
            s.submit(s.current.correct_tool, s.current.best_option)
        assert s.phase is Phase.WON and s.accepted_count == 5

        # 3 wrong in a row -> invaded immediately after round 3
        s = build_session(seed=seed)
        for _ in range(MAX_STRIKES):
            s.submit(_wrong_tool(s.current), "R")
        assert s.phase is Phase.LOST and s.round_index == 3, "3 strikes must end the game at once"

        # 2 strikes + 3 correct -> still won
        s = build_session(seed=seed)
        for i in range(DEFAULT_ROUNDS):
            ch = s.current
            if i < 2:
                s.submit(_wrong_tool(ch), "R")
            else:
                s.submit(ch.correct_tool, ch.best_option)
        assert s.phase is Phase.WON and s.strikes == 2 and s.accepted_count == 3

        # Retry: first miss with right tool is free, second miss is a strike
        s = build_session(seed=seed)
        ch = s.current
        bad = [o for o in ch.tool.options if not ch.passes(o)]
        if bad:
            v1 = s.submit(ch.correct_tool, bad[0])
            v2 = s.submit(ch.correct_tool, bad[0])
            assert v1.outcome is Outcome.RETRY and not v1.round_over
            assert v2.outcome is Outcome.STRIKE and s.strikes == 1
    print(f"\n== Rule checks passed on {len(list(seeds))} games ==")
    print("   5 rounds always · 3 strikes = Earth destroyed · 2 strikes + 3 correct = friendship · retry rule")


if __name__ == "__main__":
    show_signatures()
    check_variants()
    report_one_game(seed=7)
    check_rules()
    print(f"\nImages saved to {OUT}")

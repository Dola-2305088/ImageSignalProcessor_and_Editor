"""SaveEarth backend smoke test.

Run from the project root:
    python -m game.smoke_test

1. prints the algorithm signatures the game relies on
2. builds every puzzle variant and checks it is fair (the intended
   setting passes, the classic mistake fails)
3. checks the texture answers against the project's analyze_texture
4. checks every Discover link points at a route that exists in the app
5. checks the rules: 5 rounds, 5 different tools, spatial + frequency mix,
   3 strikes = Earth destroyed, 2 strikes can still win, retry rule
6. saves one game's images to game/_smoke_out/
"""

from __future__ import annotations

import inspect
import time
from pathlib import Path

import numpy as np
from PIL import Image

from algorithms.frequency import color_analysis, compression, dft, texture
from algorithms.learning.texture_colour_trace import TextureTrace
from algorithms.spatial import blur_sharpen, convolution, edge_detection, motion_blur, noise_cleaner, wiener
from game.challenges import CHALLENGE_BUILDERS, CHALLENGE_VARIANTS, _TEXTURE_TEXT, _nearest_option
from game.game_state import DEFAULT_ROUNDS, MAX_STRIKES, Outcome, Phase, build_session
from game.scene import make_space_scene
from game.tools import TOOLS_BY_ID

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
    ("blur_sharpen", "soft"): "Box blur 5x5",
    ("blur_sharpen", "dream"): "Box blur 3x3",
    ("blur_sharpen", "crisp"): "Box blur 3x3",
    ("motion_blur", "sideways"): "45°",
    ("motion_blur", "falling"): "45°",
    ("motion_blur", "slanting"): "90°",
    ("frequency_editor", "very_slow"): "Low-pass · large circle",
    ("frequency_editor", "gentle"): "Low-pass · small circle",
    ("frequency_editor", "fast"): "Low-pass · small circle",
    ("compression", "tenth"): "5%",
    ("compression", "twentieth"): "10%",
    ("compression", "hundredth"): "5%",
    ("hybrid", "planet_near"): "Comet near · planet far",
    ("hybrid", "comet_near"): "Planet near · comet far",
    ("color", "luma"): "G channel",
    ("color", "chroma"): "Subsample luma 4×",
}


def show_signatures() -> None:
    print("== Algorithm signatures used by the game ==")
    for fn in (convolution.convolve2d, motion_blur.create_motion_kernel, motion_blur.apply_motion_blur,
               blur_sharpen.blur_image, blur_sharpen.sharpen_image,
               noise_cleaner.mean_filter, noise_cleaner.gaussian_filter, noise_cleaner.median_filter,
               edge_detection.horizontal_edges, edge_detection.vertical_edges, edge_detection.combined_edges,
               wiener.inverse_deconvolution, wiener.wiener_deconvolution,
               dft.manual_dft2, dft.create_low_pass_mask, dft.create_high_pass_mask,
               compression.compress_dft, texture.analyze_texture,
               color_analysis.rgb_to_ycbcr, color_analysis.split_rgb_channels):
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
                if not passing or (bad is not None and bad in passing):
                    problems.append(f"{cid}/{variant}/seed{seed}")
                if seed == seeds[0]:
                    print(f"  {cid:<17}{variant:<12} passing={passing}")
                    if ch.mode != "choice":
                        print("      " + "  ".join(f"{o}={ch.scores[o]:.1f}" for o in ch.tool.options))
    assert not problems, f"Unfair puzzles: {problems}"
    print("  All variants fair.")


def check_balance(games: int = 2000) -> None:
    print("\n== Domain balance ==")
    types, puzzles, rounds = {}, {}, {}
    for cid, variants in CHALLENGE_VARIANTS.items():
        d = TOOLS_BY_ID[cid].domain
        types[d] = types.get(d, 0) + 1
        puzzles[d] = puzzles.get(d, 0) + len(variants)
    for seed in range(games):
        for c in build_session(seed=seed).challenges:
            rounds[c.tool.domain] = rounds.get(c.tool.domain, 0) + 1
    total = sum(rounds.values())
    print(f"  tools   {types}")
    print(f"  puzzles {puzzles}")
    print("  rounds  " + "  ".join(f"{d} {n / total:.1%}" for d, n in rounds.items()) + f"  ({games} games)")
    assert types["spatial"] == types["frequency"], "unequal tool counts"
    assert puzzles["spatial"] == puzzles["frequency"], "unequal puzzle counts"
    assert abs(rounds["spatial"] - rounds["frequency"]) / total < 0.02, "rounds not balanced"


def check_texture_answers() -> None:
    print("\n== Texture answers vs the project's analyze_texture ==")
    trace, options, problems = TextureTrace(128), TOOLS_BY_ID["texture"].options, []
    for kind, _, spacings in _TEXTURE_TEXT.values():
        for spacing in spacings:
            for angle in (0, 30):
                measured = trace.measure(trace.make(kind, spacing, angle)["image"])["spacing"]
                ok = _nearest_option(options, measured) == _nearest_option(options, spacing)
                print(f"  {kind:<6} true {spacing:>2} px @ {angle:>2}°  analyzer {measured:5.1f} px  "
                      f"{'ok' if ok else 'MISMATCH'}")
                if not ok:
                    problems.append(f"{kind}/{spacing}/{angle}")
    assert not problems, f"Analyzer disagrees with the answer key: {problems}"


def check_discover_routes() -> None:
    print("\n== Discover links ==")
    root = Path(__file__).resolve().parent.parent
    sources = "".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in (root / "ui" / "main_window.py", root / "ui" / "components" / "sidebar.py")
        if p.exists()
    )
    rng = np.random.default_rng(0)
    for cid, variants in CHALLENGE_VARIANTS.items():
        key, _ = CHALLENGE_BUILDERS[cid](make_space_scene(seed=0), rng, variants[0]).discover_route
        found = f'"{key}"' in sources or f"'{key}'" in sources
        print(f"  {cid:<17} -> {key:<18} {'ok' if found else 'NOT FOUND (button will do nothing)'}")


def report_one_game(seed: int) -> None:
    t0 = time.perf_counter()
    s = build_session(seed=seed)
    print(f"\n== One game (seed {seed}): {s.total_rounds} rounds built in {time.perf_counter() - t0:.2f} s ==")
    OUT.mkdir(exist_ok=True)
    for i, ch in enumerate(s.challenges, 1):
        print(f"  {i}. {ch.title:<26} {ch.tool.domain:<9} tool={ch.tool.name:<22} best={ch.best_option}")
        Image.fromarray(np.asarray(ch.received)).save(OUT / f"{i}_{ch.id}_{ch.variant}_received.png")
        Image.fromarray(np.asarray(ch.outputs[ch.best_option])).save(OUT / f"{i}_{ch.id}_{ch.variant}_answer.png")


def _wrong_tool(ch) -> str:
    return "separable"      # has no challenge, so it is always a wrong answer


def check_rules(seeds=range(20)) -> None:
    for seed in seeds:
        s = build_session(seed=seed)
        kinds = [c.id for c in s.challenges]
        domains = [TOOLS_BY_ID[k].domain for k in kinds]
        assert s.total_rounds == DEFAULT_ROUNDS, "a game must have 5 rounds"
        assert len(set(kinds)) == DEFAULT_ROUNDS, f"a tool repeated: {kinds}"
        assert domains.count("spatial") >= 2 and domains.count("frequency") >= 2, f"unbalanced: {kinds}"

        while s.phase is Phase.PLAYING:                          # perfect run
            s.submit(s.current.correct_tool, s.current.best_option)
        assert s.phase is Phase.WON and s.accepted_count == 5

        s = build_session(seed=seed)                             # 3 strikes end it at once
        for _ in range(MAX_STRIKES):
            s.submit(_wrong_tool(s.current), "Full 2D")
        assert s.phase is Phase.LOST and s.round_index == 3

        s = build_session(seed=seed)                             # 2 strikes + 3 correct = win
        for i in range(DEFAULT_ROUNDS):
            ch = s.current
            if i < 2:
                s.submit(_wrong_tool(ch), "Full 2D")
            else:
                s.submit(ch.correct_tool, ch.best_option)
        assert s.phase is Phase.WON and s.strikes == 2

        s = build_session(seed=seed)                             # retry rule
        ch = s.current
        bad = [o for o in ch.tool.options if not ch.passes(o)]
        if bad:
            v1 = s.submit(ch.correct_tool, bad[0])
            v2 = s.submit(ch.correct_tool, bad[0])
            assert v1.outcome is Outcome.RETRY and not v1.round_over
            assert v2.outcome is Outcome.STRIKE and s.strikes == 1
    print(f"\n== Rule checks passed on {len(list(seeds))} games ==")
    print("   5 rounds · 5 different tools · spatial + frequency mix · 3 strikes = Earth destroyed")
    print("   2 strikes + 3 correct = friendship · retry rule")


if __name__ == "__main__":
    show_signatures()
    check_variants()
    check_balance()
    check_texture_answers()
    check_discover_routes()
    report_one_game(seed=7)
    check_rules()
    print(f"\nImages saved to {OUT}")

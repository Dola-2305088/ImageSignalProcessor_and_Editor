"""SaveEarth engine self-test.   Run from the project root:

    python -m game.selftest            full check + calibration (a few minutes)
    python -m game.selftest --quick    backend check only

1. Backend check   - every available tool/option runs on the scene (timed).
2. Calibration     - for each challenge, PSNR of EVERY tool/option vs the
                     hidden target. Flags ambiguous rounds (a wrong answer
                     that passes) so thresholds can be tuned.
3. Simulation      - a perfect player must win, a wrong-tool player must lose.
4. Images          - received/target PNGs saved to game/_selftest_out/.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

from game import backend
from game.challenges import CHALLENGE_FACTORIES, build_challenge
from game.game_state import GameState, Status, Verdict, format_psnr
from game.scene import make_space_scene
from game.tools import TOOL_BY_ID, available_tools, run_tool

OUT = Path(__file__).parent / "_selftest_out"


def _save(img, name):
    try:
        from PIL import Image
        OUT.mkdir(exist_ok=True)
        Image.fromarray(img).save(OUT / f"{name}.png")
    except Exception as exc:  # pillow missing is not fatal
        print(f"   (could not save {name}.png: {exc})")


def backend_check() -> bool:
    print("\n[1] BACKEND CHECK (128×128 space scene)")
    scene = make_space_scene()
    _save(scene, "scene")
    ok = True
    for tool in available_tools():
        for i, name in enumerate(tool.choices):
            t0 = time.perf_counter()
            try:
                out = run_tool(tool.id, i, scene)
                assert out.dtype.name == "uint8", f"dtype {out.dtype}"
                print(f"   OK    {tool.label:<16} {name:<16} {time.perf_counter() - t0:6.2f}s  {out.shape}")
            except Exception as exc:
                ok = False
                print(f"   FAIL  {tool.label:<16} {name:<16} {type(exc).__name__}: {exc}")
                traceback.print_exc(limit=1)
    return ok


def calibration() -> bool:
    print("\n[2] CALIBRATION  (* = aliens would accept this image)")
    clean = True
    for cid in CHALLENGE_FACTORIES:
        t0 = time.perf_counter()
        ch = build_challenge(cid, seed=1)
        _save(ch.received, f"{cid}_received")
        _save(ch.target, f"{cid}_target")
        kind = f"pass ≥ {ch.threshold_db} dB vs target"
        if ch.reference is not None:
            gain = f"vs clean: received {format_psnr(backend.psnr(ch.reference, ch.received))}" \
                   f" → target {format_psnr(backend.psnr(ch.reference, ch.target))}"
            kind += f"; {gain}"
        print(f"\n   {cid}  [{kind}]  built in {time.perf_counter() - t0:.2f}s")
        for tool in available_tools():
            for i, name in enumerate(tool.choices):
                out = run_tool(tool.id, i, ch.received, ch.context)
                p = ch.score(out)
                passed = ch.passes(out)
                correct = tool.id == ch.correct_tool and i == ch.correct_choice
                if correct:
                    tag = "<- CORRECT" if passed else "<- CORRECT BUT FAILS (bug!)"
                    clean &= passed
                elif passed and tool.id == ch.correct_tool:
                    tag = "<- also accepted (same tool)"
                elif passed and tool.id in ch.also_accepts:
                    tag = "<- also accepted (expected alternative)"
                elif passed:
                    tag = "<- also accepted (DIFFERENT tool - check riddle)"
                    clean = False
                else:
                    tag = ""
                print(f"     {'*' if passed else ' '} {tool.label:<16} {name:<16} {format_psnr(p):>16}  {tag}")
    return clean


def simulation() -> bool:
    print("\n[3] SIMULATION")
    ids = list(CHALLENGE_FACTORIES)[:5]
    perfect = GameState([build_challenge(c, seed=2) for c in ids])
    while perfect.status is Status.PLAYING:
        ch = perfect.current
        r = perfect.transmit(ch.correct_tool, ch.correct_choice)
        assert r.verdict is Verdict.ACCEPTED, r
    print(f"   perfect player  -> {perfect.status.value}, accepted {perfect.accepted_count}/{perfect.total_rounds}")

    bad = GameState([build_challenge(c, seed=2) for c in ids])
    moods = [bad.mood]
    while bad.status is Status.PLAYING:
        wrong = "motion" if bad.current.correct_tool == "edges" else "edges"
        bad.transmit(wrong, 0)
        moods.append(bad.mood)
    print(f"   wrong-tool player -> {bad.status.value}, moods {' → '.join(moods)}")

    retry = GameState([build_challenge("salt_pepper_static", seed=2)])
    r1 = retry.transmit("noise", 0)   # mean filter: right tool, wrong option
    r2 = retry.transmit("noise", 2)   # median: correct
    print(f"   retry rule      -> {r1.verdict.value} then {r2.verdict.value}, strikes {retry.strikes}")
    return (perfect.status is Status.WON and bad.status is Status.LOST
            and r1.verdict is Verdict.RETRY and r2.verdict is Verdict.ACCEPTED
            and retry.strikes == 0)


def main() -> int:
    ok = backend_check()
    if not ok:
        print("\nBackend check failed - paste this output so game/backend.py can be adjusted.")
        return 1
    if "--quick" in sys.argv:
        return 0
    clean = calibration()
    sim = simulation()
    print(f"\nRESULT: backend OK | calibration {'clean' if clean else 'NEEDS REVIEW (see flags)'} | "
          f"simulation {'OK' if sim else 'FAILED'}")
    print(f"PNG files: {OUT}")
    return 0 if sim else 1


if __name__ == "__main__":
    raise SystemExit(main())

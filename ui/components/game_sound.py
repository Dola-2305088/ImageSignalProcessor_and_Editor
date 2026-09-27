"""Tiny sound player for SaveEarth.

Uses Python's built-in winsound (Windows), so no extra package is needed.
Sounds play asynchronously (the UI never waits); a new sound replaces the
one playing. On other systems, or if a file is missing, play() does nothing.

Sound files live in assets/sounds/*.wav.
"""

from __future__ import annotations

from pathlib import Path

try:
    import winsound
except ImportError:  # not Windows
    winsound = None

SOUND_DIR = Path(__file__).resolve().parents[2] / "assets" / "sounds"


class GameSound:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and winsound is not None

    @property
    def available(self) -> bool:
        return winsound is not None

    def play(self, name: str) -> None:
        if not self.enabled:
            return
        path = SOUND_DIR / f"{name}.wav"
        if not path.exists():
            return
        try:
            winsound.PlaySound(
                str(path),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
        except Exception:
            pass

    def stop(self) -> None:
        if winsound is not None:
            try:
                winsound.PlaySound(None, 0)
            except Exception:
                pass

    def toggle(self) -> bool:
        self.enabled = not self.enabled and winsound is not None
        if not self.enabled:
            self.stop()
        return self.enabled

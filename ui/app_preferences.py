"""Small, offline preference store shared by Home and Sidebar."""

from __future__ import annotations

import getpass
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


PLAN_OPTIONS = ("Student Plan", "Standard Plan", "Pro Plan")

WORKSPACE_OPTIONS = (
    "Default",
    "Frequency Lab",
    "Compression Lab",
    "Texture Lab",
    "Hybrid Lab",
    "Color Lab",
)

WORKSPACE_ROUTES = {
    "Default": 0,
    "Frequency Lab": 1,
    "Compression Lab": 2,
    "Texture Lab": 3,
    "Hybrid Lab": 4,
    "Color Lab": 5,
}


def _default_display_name() -> str:
    raw_name = getpass.getuser().strip()
    cleaned = re.sub(r"[._-]+", " ", raw_name).strip()
    return cleaned.title() if cleaned else "User"


@dataclass
class AppProfile:
    name: str = "User"
    plan: str = "Student Plan"
    workspace: str = "Default"

    @property
    def initials(self) -> str:
        words = [word for word in self.name.split() if word]
        if not words:
            return "U"
        return "".join(word[0] for word in words[:2]).upper()


class PreferencesStore:
    """Loads and saves non-sensitive display preferences as local JSON."""

    def __init__(self, path: Path | None = None):
        self.path = path or Path.home() / ".signal_studio" / "profile.json"

    def load(self) -> AppProfile:
        defaults = AppProfile(name=_default_display_name())
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return defaults

        return AppProfile(
            name=self._clean_name(data.get("name"), defaults.name),
            plan=self._choice(data.get("plan"), PLAN_OPTIONS, defaults.plan),
            workspace=self._choice(
                data.get("workspace"), WORKSPACE_OPTIONS, defaults.workspace
            ),
        )

    def save(self, profile: AppProfile) -> None:
        normalized = AppProfile(
            name=self._clean_name(profile.name, _default_display_name()),
            plan=self._choice(profile.plan, PLAN_OPTIONS, PLAN_OPTIONS[0]),
            workspace=self._choice(
                profile.workspace, WORKSPACE_OPTIONS, WORKSPACE_OPTIONS[0]
            ),
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(asdict(normalized), indent=2), encoding="utf-8"
        )
        temporary_path.replace(self.path)

    @staticmethod
    def _clean_name(value, fallback: str) -> str:
        if not isinstance(value, str):
            return fallback
        cleaned = " ".join(value.split())[:40]
        return cleaned or fallback

    @staticmethod
    def _choice(value, options, fallback: str) -> str:
        return value if value in options else fallback
"""Small, offline preference store shared by Home and Sidebar.

The old build stored one workspace per feature page ("Frequency Lab",
"Texture Lab", ...) and treated that value as a navigation control. That
duplicated the sidebar: picking a workspace navigated, and navigating
rewrote the workspace. With 13 destinations that duplication becomes
unmanageable, so the preference now means one thing only:

    "which page should the app open on?"

Navigation itself belongs to the sidebar.
"""

from __future__ import annotations

import getpass
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


PLAN_OPTIONS = ("Student Plan", "Standard Plan", "Pro Plan")


# ============================================================
# STARTUP PAGE
# ============================================================
#
# Values map to sidebar route keys (see ui/components/sidebar.py).
# Kept deliberately short: three entry points, not thirteen.

WORKSPACE_OPTIONS = (
    "Home",
    "Spatial domain",
    "Frequency domain",
)

WORKSPACE_ROUTES = {
    "Home": "home",
    "Spatial domain": "blur_sharpen",
    "Frequency domain": "frequency",
}

# Profiles saved by the previous build used one workspace per feature.
# Map them forward so an existing profile.json is not silently reset.
LEGACY_WORKSPACES = {
    "Default": "Home",
    "Frequency Lab": "Frequency domain",
    "Compression Lab": "Frequency domain",
    "Texture Lab": "Frequency domain",
    "Hybrid Lab": "Frequency domain",
    "Color Lab": "Frequency domain",
}


def _default_display_name() -> str:
    raw_name = getpass.getuser().strip()
    cleaned = re.sub(r"[._-]+", " ", raw_name).strip()
    return cleaned.title() if cleaned else "User"


@dataclass
class AppProfile:
    name: str = "User"
    plan: str = "Student Plan"
    workspace: str = "Home"

    @property
    def initials(self) -> str:
        words = [word for word in self.name.split() if word]
        if not words:
            return "U"
        return "".join(word[0] for word in words[:2]).upper()

    @property
    def startup_route_key(self) -> str:
        """Sidebar route key this profile should open on."""
        return WORKSPACE_ROUTES.get(self.workspace, "home")


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
            workspace=self._workspace(
                data.get("workspace"), defaults.workspace
            ),
        )

    def save(self, profile: AppProfile) -> None:
        normalized = AppProfile(
            name=self._clean_name(profile.name, _default_display_name()),
            plan=self._choice(profile.plan, PLAN_OPTIONS, PLAN_OPTIONS[0]),
            workspace=self._workspace(
                profile.workspace, WORKSPACE_OPTIONS[0]
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

    @staticmethod
    def _workspace(value, fallback: str) -> str:
        if value in WORKSPACE_OPTIONS:
            return value
        migrated = LEGACY_WORKSPACES.get(value)
        return migrated if migrated else fallback

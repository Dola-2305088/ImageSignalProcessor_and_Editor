"""Reusable controls shared by the seven spatial-domain pages.

The frequency pages each hand-rolled their own buttons and panels. That
was fine for five pages; for twelve it becomes copy-paste. These pieces
carry the same visual language so a spatial page looks native next to a
frequency page, while keeping each view file short enough to read.
"""

import flet as ft

from ui.theme import AppAnimations, AppColors, AppLayout
from ui.components.section_header import SectionHeader


# ============================================================
# PAGE SHELL
# ============================================================

class SpatialPage:
    """Outer card + section header shared by every spatial view."""

    def __init__(self, badge, title, subtitle, icon, accent, sections):
        self.header = SectionHeader(
            badge=badge,
            title=title,
            subtitle=subtitle,
            icon=icon,
            accent=accent,
        )

        self.control = ft.Container(
            bgcolor=AppColors.SURFACE,
            border=ft.Border.all(1, AppColors.BORDER),
            border_radius=ft.BorderRadius.all(AppLayout.CARD_RADIUS),
            padding=AppLayout.CARD_PADDING,
            content=ft.Column(
                spacing=18,
                controls=[self.header.control] + list(sections),
            ),
        )


# ============================================================
# SEGMENTED SELECTOR
# ============================================================

class SegmentedSelector:
    """A row of mutually exclusive pill buttons.

    options: list of (key, label, icon)
    """

    def __init__(self, options, value=None, accent=None, on_change=None):
        self.options = options
        self.accent = accent or AppColors.PURPLE
        self.on_change = on_change
        self.value = value if value is not None else options[0][0]

        self.pills = {}

        self.control = ft.Row(
            spacing=8,
            wrap=True,
            controls=[
                self._pill(key, label, icon)
                for key, label, icon in options
            ],
        )

    def _pill(self, key, label, icon):
        selected = key == self.value

        icon_control = ft.Icon(
            icon,
            size=16,
            color=self.accent if selected else AppColors.MUTED,
        )

        text_control = ft.Text(
            label,
            size=11,
            weight=ft.FontWeight.W_600,
            color=AppColors.TEXT if selected else AppColors.TEXT_SECONDARY,
        )

        pill = ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=9),
            border_radius=ft.BorderRadius.all(11),
            bgcolor=AppColors.SURFACE_3 if selected else AppColors.SURFACE_DARK,
            border=ft.Border.all(
                1,
                self.accent if selected else AppColors.BORDER_SOFT,
            ),
            ink=True,
            on_click=lambda e, k=key: self.set_value(k),
            animate=ft.Animation(
                AppAnimations.FAST,
                ft.AnimationCurve.EASE_OUT,
            ),
            data={"icon": icon_control, "text": text_control},
            content=ft.Row(
                spacing=8,
                tight=True,
                controls=[icon_control, text_control],
            ),
        )

        self.pills[key] = pill
        return pill

    def set_value(self, key, notify=True):
        if key not in self.pills:
            return

        self.value = key

        for pill_key, pill in self.pills.items():
            selected = pill_key == key
            data = pill.data

            pill.bgcolor = (
                AppColors.SURFACE_3
                if selected
                else AppColors.SURFACE_DARK
            )
            pill.border = ft.Border.all(
                1,
                self.accent if selected else AppColors.BORDER_SOFT,
            )
            data["icon"].color = (
                self.accent if selected else AppColors.MUTED
            )
            data["text"].color = (
                AppColors.TEXT if selected else AppColors.TEXT_SECONDARY
            )

        try:
            self.control.update()
        except Exception:
            pass

        if notify and self.on_change:
            self.on_change(key)

    def get_value(self):
        return self.value


# ============================================================
# KERNEL GRID
# ============================================================

class KernelGrid:
    """Editable NxN kernel of numeric fields."""

    PRESETS = {
        "identity": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
        "box_blur": [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
        "sharpen": [[0, -1, 0], [-1, 5, -1], [0, -1, 0]],
        "edge": [[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]],
        "emboss": [[-2, -1, 0], [-1, 1, 1], [0, 1, 2]],
    }

    def __init__(self, size=3, values=None, accent=None):
        self.size = size
        self.accent = accent or AppColors.PURPLE

        values = values or self.PRESETS["sharpen"]

        self.fields = [
            [
                ft.TextField(
                    value=str(values[r][c]),
                    width=58,
                    height=42,
                    text_size=12,
                    text_align=ft.TextAlign.CENTER,
                    content_padding=ft.Padding.symmetric(vertical=4),
                    border_color=AppColors.BORDER,
                    focused_border_color=self.accent,
                    bgcolor=AppColors.SURFACE_DARK,
                )
                for c in range(size)
            ]
            for r in range(size)
        ]

        self.normalize_switch = ft.Switch(
            value=False,
            active_color=self.accent,
            scale=0.8,
        )

        self.error_text = ft.Text(
            "",
            size=10,
            color=AppColors.RED,
            visible=False,
        )

        self.control = ft.Column(
            spacing=10,
            controls=[
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(spacing=6, controls=row)
                        for row in self.fields
                    ],
                ),
                ft.Row(
                    spacing=6,
                    controls=[
                        self.normalize_switch,
                        ft.Text(
                            "Normalise (divide by sum)",
                            size=10,
                            color=AppColors.TEXT_SECONDARY,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=6,
                    wrap=True,
                    controls=[
                        self._preset_chip("Sharpen", "sharpen"),
                        self._preset_chip("Box blur", "box_blur"),
                        self._preset_chip("Edge", "edge"),
                        self._preset_chip("Emboss", "emboss"),
                        self._preset_chip("Identity", "identity"),
                    ],
                ),
                self.error_text,
            ],
        )

    def _preset_chip(self, label, key):
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            border_radius=ft.BorderRadius.all(8),
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            ink=True,
            on_click=lambda e, k=key: self.set_values(self.PRESETS[k]),
            content=ft.Text(
                label,
                size=10,
                color=AppColors.TEXT_SECONDARY,
            ),
        )

    def set_values(self, values):
        for r in range(self.size):
            for c in range(self.size):
                self.fields[r][c].value = str(values[r][c])

        self.show_error(None)

        try:
            self.control.update()
        except Exception:
            pass

    def show_error(self, message):
        self.error_text.value = message or ""
        self.error_text.visible = bool(message)

        try:
            self.error_text.update()
        except Exception:
            pass

    def get_kernel(self):
        """Return the kernel as nested floats, or None if invalid.

        Raises ValueError with a readable message so the caller can
        surface it as a toast rather than a stack trace.
        """
        kernel = []

        for r in range(self.size):
            row = []
            for c in range(self.size):
                raw = (self.fields[r][c].value or "").strip()
                if raw == "":
                    raw = "0"
                try:
                    row.append(float(raw))
                except ValueError:
                    raise ValueError(
                        f"Cell row {r + 1}, column {c + 1} "
                        f"is not a number: '{raw}'"
                    )
            kernel.append(row)

        if self.normalize_switch.value:
            total = sum(sum(row) for row in kernel)
            if abs(total) < 1e-9:
                raise ValueError(
                    "Cannot normalise: the kernel sums to zero."
                )
            kernel = [[value / total for value in row] for row in kernel]

        return kernel

    def is_normalised(self):
        return bool(self.normalize_switch.value)


# ============================================================
# ACTION BUTTON
# ============================================================

class ActionButton:
    """Large clickable card used to run an operation."""

    def __init__(
        self,
        title,
        subtitle,
        icon,
        accent,
        handler,
        col=None,
    ):
        self.accent = accent

        self.control = ft.Container(
            col=col or {"xs": 12, "sm": 6},
            padding=14,
            bgcolor=AppColors.SURFACE_SOFT,
            border=ft.Border.all(1, AppColors.BORDER),
            border_radius=ft.BorderRadius.all(15),
            ink=True,
            on_click=handler,
            on_hover=self._hover,
            animate=ft.Animation(
                AppAnimations.FAST,
                ft.AnimationCurve.EASE_OUT,
            ),
            data=accent,
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Container(
                        width=42,
                        height=42,
                        alignment=ft.Alignment.CENTER,
                        border_radius=13,
                        bgcolor=AppColors.SURFACE_3,
                        content=ft.Icon(icon, color=accent, size=21),
                    ),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(
                                title,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),
                            ft.Text(
                                subtitle,
                                size=10,
                                color=AppColors.TEXT_SECONDARY,
                            ),
                        ],
                    ),
                    ft.Icon(
                        ft.Icons.PLAY_ARROW_ROUNDED,
                        color=accent,
                        size=22,
                    ),
                ],
            ),
        )

    @staticmethod
    def _hover(e):
        hovered = str(e.data).strip().lower() in {"true", "1", "yes"}
        accent = e.control.data

        e.control.bgcolor = (
            AppColors.SURFACE_3 if hovered else AppColors.SURFACE_SOFT
        )
        e.control.border = ft.Border.all(
            1,
            accent if hovered else AppColors.BORDER,
        )
        e.control.update()


# ============================================================
# METRIC PANEL
# ============================================================

class MetricPanel:
    """Result readout. Values are pushed in by main_window after a run."""

    def __init__(self, title="Results", rows=None, accent=None):
        self.accent = accent or AppColors.PURPLE
        self.rows = rows or []
        self.value_texts = {}

        row_controls = []

        for key, label in self.rows:
            value_text = ft.Text(
                "—",
                size=13,
                weight=ft.FontWeight.BOLD,
                color=AppColors.MUTED,
            )
            self.value_texts[key] = value_text

            row_controls.append(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=12, vertical=9),
                    bgcolor=AppColors.SURFACE_DARK,
                    border_radius=ft.BorderRadius.all(
                        AppLayout.SMALL_RADIUS
                    ),
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                label,
                                size=11,
                                color=AppColors.TEXT_SECONDARY,
                            ),
                            ft.Container(expand=True),
                            value_text,
                        ],
                    ),
                )
            )

        self.note = ft.Text(
            "Run an operation to populate these values.",
            size=10,
            color=AppColors.MUTED,
        )

        self.control = ft.Container(
            padding=AppLayout.SMALL_PADDING,
            bgcolor=AppColors.SURFACE_SOFT,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            border_radius=ft.BorderRadius.all(AppLayout.INNER_RADIUS),
            content=ft.Column(
                spacing=9,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(
                                ft.Icons.INSIGHTS_OUTLINED,
                                size=16,
                                color=self.accent,
                            ),
                            ft.Text(
                                title,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT,
                            ),
                        ],
                    ),
                    ft.Column(spacing=6, controls=row_controls),
                    self.note,
                ],
            ),
        )

    def set_values(self, values, note=None):
        for key, value in values.items():
            text = self.value_texts.get(key)
            if text is None:
                continue
            text.value = value
            text.color = AppColors.TEXT

        if note is not None:
            self.note.value = note

        try:
            self.control.update()
        except Exception:
            pass

    def clear(self, note="Run an operation to populate these values."):
        for text in self.value_texts.values():
            text.value = "—"
            text.color = AppColors.MUTED

        self.note.value = note

        try:
            self.control.update()
        except Exception:
            pass


# ============================================================
# SMALL LAYOUT HELPERS
# ============================================================

def parameter_card(title, icon, accent, controls, col=None):
    """Bordered panel holding a group of parameter controls."""
    return ft.Container(
        col=col or {"xs": 12, "md": 6},
        padding=AppLayout.SMALL_PADDING,
        bgcolor=AppColors.SURFACE_SOFT,
        border=ft.Border.all(1, AppColors.BORDER_SOFT),
        border_radius=ft.BorderRadius.all(AppLayout.INNER_RADIUS),
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(icon, size=16, color=accent),
                        ft.Text(
                            title,
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.TEXT,
                        ),
                    ],
                ),
            ] + list(controls),
        ),
    )


def field_label(text):
    return ft.Text(text, size=11, color=AppColors.TEXT_SECONDARY)


def hint(text):
    return ft.Text(text, size=10, color=AppColors.MUTED)


def kernel_preview(rows, accent):
    """Static monospace display of a fixed kernel, e.g. the Sobel pair."""
    return ft.Column(
        spacing=3,
        controls=[
            ft.Text(
                "  ".join(f"{value:>3}" for value in row),
                size=11,
                font_family="monospace",
                color=accent,
            )
            for row in rows
        ],
    )

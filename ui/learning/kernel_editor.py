"""Resizable kernel editor used by the convolution lesson.

Unlike the Explore page's KernelGrid (fixed 3 x 3), this editor switches
between 3 x 3, 5 x 5 and 7 x 7, tints every cell by the sign and size of
its weight, and keeps full-precision values internally: a Gaussian
weight of 0.0012 is *shown* rounded but *used* exactly, so presets stay
recognisable and the lesson's numbers stay true.
"""

import flet as ft
import numpy as np

from algorithms.learning.convolution_trace import (
    KERNEL_SIZES,
    PRESETS,
    identify_kernel,
    preset_kernel,
    preset_sizes,
)
from ui.components.spatial_controls import SegmentedSelector
from ui.learning import palette
from ui.theme import AppAnimations, AppColors


class KernelEditor:
    def __init__(self, on_change, preset="box_blur", size=3):
        self.on_change = on_change
        self.values = preset_kernel(preset, size)
        self.size = self.values.shape[0]
        self.fields = []

        self.size_selector = SegmentedSelector(
            options=[
                (3, "3 × 3", ft.Icons.GRID_3X3),
                (5, "5 × 5", ft.Icons.GRID_4X4),
                (7, "7 × 7", ft.Icons.GRID_ON),
            ],
            value=self.size,
            accent=palette.KERNEL,
            on_change=self._on_size_change,
        )

        self.grid_holder = ft.Column(spacing=5)

        self.sum_text = ft.Text("", size=11, color=AppColors.TEXT_SECONDARY)
        self.name_text = ft.Text(
            "",
            size=11,
            weight=ft.FontWeight.BOLD,
            color=palette.KERNEL,
        )
        self.error_text = ft.Text("", size=10, color=AppColors.RED, visible=False)

        self.preset_row = ft.Row(
            spacing=6,
            run_spacing=6,
            wrap=True,
            controls=[self._preset_chip(key) for key in PRESETS],
        )

        normalize_chip = self._chip(
            "Normalize (÷ Σ)",
            ft.Icons.BALANCE,
            self._normalize,
            AppColors.GREEN_LIGHT,
        )

        self.control = ft.Column(
            spacing=12,
            controls=[
                self.size_selector.control,
                ft.Container(
                    padding=12,
                    border_radius=14,
                    bgcolor=AppColors.SURFACE_DARK,
                    border=ft.Border.all(1, AppColors.BORDER_SOFT),
                    content=self.grid_holder,
                ),
                ft.Row(
                    spacing=10,
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[self.name_text, self.sum_text, normalize_chip],
                ),
                self.error_text,
                ft.Text("Presets", size=10, color=AppColors.MUTED),
                self.preset_row,
            ],
        )

        self._rebuild_fields()
        self._refresh_labels()

    # =========================================================
    # PUBLIC
    # =========================================================

    def get_kernel(self):
        return self.values.copy()

    def set_kernel(self, kernel, notify=True):
        kernel = np.asarray(kernel, dtype=np.float64)
        resized = kernel.shape[0] != self.size

        self.values = kernel.copy()
        self.size = kernel.shape[0]

        if resized:
            self.size_selector.set_value(self.size, notify=False)
            self._rebuild_fields()
        else:
            for r in range(self.size):
                for c in range(self.size):
                    self._style_field(r, c, write_text=True)

        self._show_error(None)
        self._refresh_labels()
        self._safe_update(self.control)

        if notify and self.on_change:
            self.on_change(self.get_kernel())

    # =========================================================
    # BUILD
    # =========================================================

    def _rebuild_fields(self):
        cell = {3: 58, 5: 50, 7: 44}[self.size]

        self.fields = []
        rows = []

        for r in range(self.size):
            row = []
            for c in range(self.size):
                field = ft.TextField(
                    value=palette.fmt_weight(self.values[r, c]),
                    width=cell,
                    height=36,
                    text_size=11,
                    text_align=ft.TextAlign.CENTER,
                    content_padding=ft.Padding.symmetric(vertical=2),
                    border_radius=8,
                    filled=True,
                    border_color=AppColors.BORDER_SOFT,
                    focused_border_color=palette.KERNEL,
                    color=AppColors.TEXT,
                    data=(r, c),
                    on_change=self._on_field_change,
                )
                row.append(field)
            self.fields.append(row)
            rows.append(ft.Row(spacing=5, controls=row))

        self.grid_holder.controls = rows

        for r in range(self.size):
            for c in range(self.size):
                self._style_field(r, c, write_text=False)

    def _style_field(self, r, c, write_text):
        field = self.fields[r][c]
        max_abs = float(np.max(np.abs(self.values))) or 1.0
        field.bgcolor = palette.weight_color(self.values[r, c], max_abs)
        field.border_color = AppColors.BORDER_SOFT
        if write_text:
            field.value = palette.fmt_weight(self.values[r, c])

    def _preset_chip(self, key):
        label = PRESETS[key][0]
        sizes = preset_sizes(key)
        suffix = "" if len(sizes) == len(KERNEL_SIZES) else (
            " (" + "/".join(str(s) for s in sizes) + ")"
        )

        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            border_radius=9,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, AppColors.BORDER_SOFT),
            ink=True,
            tooltip=PRESETS[key][1],
            on_click=lambda e, k=key: self._apply_preset(k),
            on_hover=self._hover_chip,
            animate=ft.Animation(AppAnimations.FAST, ft.AnimationCurve.EASE_OUT),
            content=ft.Text(label + suffix, size=10, color=AppColors.TEXT_SECONDARY),
        )

    def _chip(self, label, icon, handler, accent):
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            border_radius=9,
            bgcolor=AppColors.SURFACE_DARK,
            border=ft.Border.all(1, palette.argb("66", accent)),
            ink=True,
            on_click=handler,
            content=ft.Row(
                tight=True,
                spacing=6,
                controls=[
                    ft.Icon(icon, size=13, color=accent),
                    ft.Text(label, size=10, color=accent),
                ],
            ),
        )

    @staticmethod
    def _hover_chip(e):
        hovered = str(e.data).lower() == "true"
        e.control.border = ft.Border.all(
            1, palette.KERNEL if hovered else AppColors.BORDER_SOFT
        )
        e.control.bgcolor = AppColors.SURFACE_3 if hovered else AppColors.SURFACE_DARK
        e.control.update()

    # =========================================================
    # EVENTS
    # =========================================================

    def _on_size_change(self, size):
        if size == self.size:
            return

        # Keep the current preset when it exists at the new size,
        # otherwise fall back to a box blur of that size.
        key = identify_kernel(self.values)
        if key is None or size not in preset_sizes(key):
            key = "box_blur"

        self.set_kernel(preset_kernel(key, size))

    def _apply_preset(self, key):
        size = self.size if self.size in preset_sizes(key) else preset_sizes(key)[0]
        self.set_kernel(preset_kernel(key, size))

    def _on_field_change(self, e):
        r, c = e.control.data
        raw = (e.control.value or "").strip()

        if raw in ("", "-", ".", "-."):
            return  # mid-typing: wait for a complete number

        try:
            value = float(raw)
            if not np.isfinite(value):
                raise ValueError
        except ValueError:
            e.control.border_color = AppColors.RED
            self._safe_update(e.control)
            self._show_error(f"Row {r + 1}, column {c + 1}: '{raw}' is not a number.")
            return

        self.values[r, c] = value
        self._style_field(r, c, write_text=False)
        self._safe_update(e.control)
        self._show_error(None)
        self._refresh_labels()

        if self.on_change:
            self.on_change(self.get_kernel())

    def _normalize(self, e):
        total = float(self.values.sum())
        if abs(total) < 1e-9:
            self._show_error("This kernel sums to zero, so it cannot be normalized.")
            return
        self.set_kernel(self.values / total)

    # =========================================================
    # HELPERS
    # =========================================================

    def _refresh_labels(self):
        key = identify_kernel(self.values)
        self.name_text.value = PRESETS[key][0] if key else "Custom kernel"
        self.sum_text.value = f"Σ weights = {palette.fmt_weight(self.values.sum())}"
        self._safe_update(self.name_text)
        self._safe_update(self.sum_text)

    def _show_error(self, message):
        self.error_text.value = message or ""
        self.error_text.visible = bool(message)
        self._safe_update(self.error_text)

    @staticmethod
    def _safe_update(control):
        try:
            control.update()
        except Exception:
            pass

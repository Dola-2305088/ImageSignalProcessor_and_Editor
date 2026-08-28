"""Grouped navigation sidebar.

The application has 13 destinations (Home + 7 spatial features + 5
frequency features). A flat list of 13 items is unreadable, so the
features are organised under two collapsible domain groups that mirror
the project's core story:

    Spatial domain    -> convolution based processing
    Frequency domain  -> 2D DFT based processing

Every destination has a stable string ``key``. Callers should resolve a
key to an index with ``Sidebar.index_of(key)`` instead of hardcoding
integers, so inserting a feature later never renumbers the rest.
"""

import flet as ft

from ui.theme import AppAnimations, AppColors, AppLayout


# ============================================================
# GROUPS
# ============================================================

SPATIAL = "spatial"
FREQUENCY = "frequency"

GROUPS = {
    SPATIAL: {
        "title": "Spatial domain",
        "icon": ft.Icons.WIDGETS_OUTLINED,
        "accent": AppColors.PURPLE,
        "accent_bg": "#211741",
        "accent_border": "#4C3A8C",
    },
    FREQUENCY: {
        "title": "Frequency domain",
        "icon": ft.Icons.WAVES,
        "accent": AppColors.CYAN,
        "accent_bg": "#0C2C36",
        "accent_border": "#1F6274",
    },
}


# ============================================================
# NAVIGATION REGISTRY
# ============================================================
#
# Order matters: this is the order the items appear in, and the index
# of each entry is its route index. Spatial features are listed in the
# recommended integration order from the Dola branch handout.

NAV_ITEMS = [
    {
        "key": "home",
        "label": "Home",
        "icon": ft.Icons.HOME_OUTLINED,
        "selected_icon": ft.Icons.HOME,
        "group": None,
    },

    # ------------------------------------------------------------------
    # SPATIAL DOMAIN
    # ------------------------------------------------------------------
    {
        "key": "blur_sharpen",
        "label": "Blur & Sharpen",
        "icon": ft.Icons.BLUR_ON,
        "selected_icon": ft.Icons.BLUR_ON,
        "group": SPATIAL,
    },
    {
        "key": "edges",
        "label": "Edge Detector",
        "icon": ft.Icons.BORDER_OUTER,
        "selected_icon": ft.Icons.BORDER_OUTER,
        "group": SPATIAL,
    },
    {
        "key": "noise",
        "label": "Noise Cleaner",
        "icon": ft.Icons.GRAIN,
        "selected_icon": ft.Icons.GRAIN,
        "group": SPATIAL,
    },
    {
        "key": "resize",
        "label": "Resizer",
        "icon": ft.Icons.ASPECT_RATIO,
        "selected_icon": ft.Icons.ASPECT_RATIO,
        "group": SPATIAL,
    },
    {
        "key": "gaussian",
        "label": "Separable Blur",
        "icon": ft.Icons.BLUR_LINEAR,
        "selected_icon": ft.Icons.BLUR_LINEAR,
        "group": SPATIAL,
    },
    {
        "key": "motion",
        "label": "Motion Blur",
        "icon": ft.Icons.MOTION_PHOTOS_ON,
        "selected_icon": ft.Icons.MOTION_PHOTOS_ON,
        "group": SPATIAL,
    },
    {
        "key": "wiener",
        "label": "Restoration",
        "icon": ft.Icons.AUTO_FIX_HIGH,
        "selected_icon": ft.Icons.AUTO_FIX_HIGH,
        "group": SPATIAL,
    },

    # ------------------------------------------------------------------
    # FREQUENCY DOMAIN
    # ------------------------------------------------------------------
    {
        "key": "frequency",
        "label": "Frequency",
        "icon": ft.Icons.GRAPHIC_EQ,
        "selected_icon": ft.Icons.GRAPHIC_EQ,
        "group": FREQUENCY,
    },
    {
        "key": "compression",
        "label": "Compression",
        "icon": ft.Icons.ARCHIVE_OUTLINED,
        "selected_icon": ft.Icons.ARCHIVE,
        "group": FREQUENCY,
    },
    {
        "key": "texture",
        "label": "Texture",
        "icon": ft.Icons.GRID_ON_OUTLINED,
        "selected_icon": ft.Icons.GRID_ON,
        "group": FREQUENCY,
    },
    {
        "key": "hybrid",
        "label": "Hybrid",
        "icon": ft.Icons.COMPARE_OUTLINED,
        "selected_icon": ft.Icons.COMPARE,
        "group": FREQUENCY,
    },
    {
        "key": "color",
        "label": "Color",
        "icon": ft.Icons.PALETTE_OUTLINED,
        "selected_icon": ft.Icons.PALETTE,
        "group": FREQUENCY,
    },
]


# key -> index, built once so nothing hardcodes an integer route.
ROUTES = {item["key"]: index for index, item in enumerate(NAV_ITEMS)}


def route_index(key, default=0):
    """Resolve a route key to its navigation index."""
    return ROUTES.get(key, default)


def group_keys(group):
    """All route keys belonging to one domain group."""
    return [item["key"] for item in NAV_ITEMS if item["group"] == group]


LABEL_WIDTH = 122
ITEM_HEIGHT = 42
HEADER_HEIGHT = 34


class Sidebar:
    """Persistent navigation with collapsible domain groups."""

    def __init__(
        self,
        on_navigation_change,
        profile=None,
        on_edit_profile=None,
        on_show_about=None,
    ):
        self.on_navigation_change = on_navigation_change
        self.profile = profile
        self.on_edit_profile = on_edit_profile
        self.on_show_about = on_show_about

        self.extended = True
        self.selected_index = 0

        # Both domain groups start closed. Home is the only visible
        # destination, which keeps the two-domain story readable instead
        # of dropping 13 links on the user at once.
        self.group_open = {SPATIAL: False, FREQUENCY: False}

        self.items = []
        self.labels = []
        self.group_headers = {}
        self.group_chevrons = {}
        self.group_items = {SPATIAL: [], FREQUENCY: []}

        self.control = self._build()

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _is_hovered(value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes"}

    @staticmethod
    def _accent_bg(group):
        if group in GROUPS:
            return GROUPS[group]["accent_bg"]
        return "#17284C"

    @staticmethod
    def _accent_border(group):
        if group in GROUPS:
            return GROUPS[group]["accent_border"]
        return "#314A84"

    # =========================================================
    # BUILD
    # =========================================================

    def _build(self):
        nav_controls = []
        rendered_groups = set()

        for index, item in enumerate(NAV_ITEMS):
            group = item["group"]

            if group is not None and group not in rendered_groups:
                rendered_groups.add(group)
                nav_controls.append(self._group_header(group))

            nav_controls.append(self._nav_item(index, item))

        # 13 destinations will not fit at the minimum window height, so
        # the navigation list scrolls while the profile stays pinned.
        nav = ft.Column(
            spacing=3,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=nav_controls,
        )

        self._apply_group_visibility()

        return ft.Container(
            width=AppLayout.SIDEBAR_EXPANDED_WIDTH,
            padding=ft.Padding.only(
                left=12,
                right=12,
                top=10,
                bottom=12,
            ),
            bgcolor="#07101C",
            border=ft.Border.only(
                right=ft.BorderSide(1, "#1D2A3E"),
            ),
            animate=ft.Animation(
                AppAnimations.NORMAL,
                ft.AnimationCurve.EASE_OUT,
            ),
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    ft.Container(
                        height=54,
                        content=ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.MENU,
                                    icon_size=21,
                                    icon_color=AppColors.TEXT_SECONDARY,
                                    tooltip="Collapse / expand sidebar",
                                    on_click=lambda e: self.toggle(),
                                ),
                                ft.Container(expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.CHEVRON_LEFT,
                                    icon_size=18,
                                    icon_color=AppColors.TEXT_SECONDARY,
                                    bgcolor="#101A2B",
                                    tooltip="Collapse / expand sidebar",
                                    on_click=lambda e: self.toggle(),
                                ),
                            ],
                        ),
                    ),

                    nav,

                    ft.Container(
                        height=1,
                        bgcolor="#1C2A3E",
                        margin=ft.Margin.only(top=10, bottom=10),
                    ),

                    self._simple_item(
                        "Settings",
                        ft.Icons.SETTINGS_OUTLINED,
                        self._edit_profile,
                    ),
                    self._simple_item(
                        "About",
                        ft.Icons.INFO_OUTLINE,
                        self._show_about,
                    ),

                    self._profile(),
                ],
            ),
        )

    # =========================================================
    # GROUP HEADER
    # =========================================================

    def _group_header(self, group):
        meta = GROUPS[group]
        count = len(group_keys(group))

        chevron = ft.Icon(
            ft.Icons.EXPAND_MORE
            if self.group_open[group]
            else ft.Icons.CHEVRON_RIGHT,
            size=17,
            color=AppColors.MUTED,
        )

        self.group_chevrons[group] = chevron

        label_holder = ft.Container(
            width=LABEL_WIDTH,
            content=ft.Row(
                spacing=6,
                controls=[
                    ft.Text(
                        meta["title"],
                        size=10,
                        weight=ft.FontWeight.W_600,
                        color=AppColors.MUTED,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        str(count),
                        size=9,
                        color=AppColors.MUTED_DARK,
                    ),
                    chevron,
                ],
            ),
            animate=ft.Animation(
                AppAnimations.NORMAL,
                ft.AnimationCurve.EASE_OUT,
            ),
        )

        self.labels.append(label_holder)

        header = ft.Container(
            height=HEADER_HEIGHT,
            margin=ft.Margin.only(top=8),
            padding=ft.Padding.symmetric(horizontal=10),
            border_radius=8,
            ink=True,
            tooltip=f"{meta['title']} ({count} features)",
            on_click=lambda e, g=group: self.toggle_group(g),
            on_hover=self._hover_simple,
            data={"rest_bg": "#00000000"},
            content=ft.Row(
                spacing=13,
                controls=[
                    ft.Icon(
                        meta["icon"],
                        size=17,
                        color=meta["accent"],
                    ),
                    label_holder,
                ],
            ),
        )

        self.group_headers[group] = header
        return header

    # =========================================================
    # NAVIGATION ITEM
    # =========================================================

    def _nav_item(self, index, item):
        label = item["label"]
        icon = item["icon"]
        selected_icon = item["selected_icon"]
        group = item["group"]

        selected = index == self.selected_index

        icon_control = ft.Icon(
            selected_icon if selected else icon,
            size=20,
            color="#EAF0FF" if selected else AppColors.TEXT_SECONDARY,
        )

        label_control = ft.Text(
            label,
            size=11,
            color="#F4F6FD" if selected else AppColors.TEXT_SECONDARY,
        )

        label_holder = ft.Container(
            width=LABEL_WIDTH,
            content=label_control,
            animate=ft.Animation(
                AppAnimations.NORMAL,
                ft.AnimationCurve.EASE_OUT,
            ),
        )

        control = ft.Container(
            height=ITEM_HEIGHT,
            padding=ft.Padding.only(
                left=10 if group is None else 18,
                right=10,
            ),
            border_radius=10,
            bgcolor=self._accent_bg(group) if selected else "#00000000",
            border=ft.Border.all(
                1,
                self._accent_border(group) if selected else "#00000000",
            ),
            ink=True,
            tooltip=label,
            on_click=lambda e, i=index: self._select(i),
            on_hover=self._hover,
            animate=ft.Animation(
                AppAnimations.FAST,
                ft.AnimationCurve.EASE_OUT,
            ),
            data={
                "index": index,
                "key": item["key"],
                "group": group,
                "icon": icon,
                "selected_icon": selected_icon,
                "icon_control": icon_control,
                "label_control": label_control,
            },
            content=ft.Row(
                spacing=13,
                controls=[
                    icon_control,
                    label_holder,
                ],
            ),
        )

        self.items.append(control)
        self.labels.append(label_holder)

        if group is not None:
            self.group_items[group].append(control)

        return control

    # =========================================================
    # GROUP OPEN / CLOSE
    # =========================================================

    def _apply_group_visibility(self):
        for group, controls in self.group_items.items():
            # When the sidebar is collapsed to icons there is nowhere to
            # show a group header, so every item stays reachable.
            visible = (not self.extended) or self.group_open[group]

            for control in controls:
                control.visible = visible

            header = self.group_headers.get(group)
            if header is not None:
                header.visible = self.extended

            chevron = self.group_chevrons.get(group)
            if chevron is not None:
                chevron.name = (
                    ft.Icons.EXPAND_MORE
                    if self.group_open[group]
                    else ft.Icons.CHEVRON_RIGHT
                )

    def toggle_group(self, group, refresh=True):
        if group not in self.group_open:
            return

        self.group_open[group] = not self.group_open[group]
        self._apply_group_visibility()

        if refresh:
            self._safe_update()

    def open_group(self, group, refresh=True):
        if group not in self.group_open or self.group_open[group]:
            return

        self.group_open[group] = True
        self._apply_group_visibility()

        if refresh:
            self._safe_update()

    def _reveal_index(self, index):
        """Make sure the group containing an item is open."""
        if not 0 <= index < len(NAV_ITEMS):
            return

        group = NAV_ITEMS[index]["group"]

        if group is not None and not self.group_open[group]:
            self.group_open[group] = True
            self._apply_group_visibility()

    # =========================================================
    # SIMPLE ITEM
    # =========================================================

    def _simple_item(self, label, icon, on_click=None):
        holder = ft.Container(
            width=LABEL_WIDTH,
            content=ft.Text(
                label,
                size=11,
                color=AppColors.TEXT_SECONDARY,
            ),
            animate=ft.Animation(
                AppAnimations.NORMAL,
                ft.AnimationCurve.EASE_OUT,
            ),
        )

        self.labels.append(holder)

        return ft.Container(
            height=42,
            padding=ft.Padding.symmetric(horizontal=10),
            border_radius=10,
            ink=True,
            tooltip=label,
            on_click=on_click,
            on_hover=self._hover_simple,
            data={"rest_bg": "#00000000"},
            content=ft.Row(
                spacing=13,
                controls=[
                    ft.Icon(
                        icon,
                        size=20,
                        color=AppColors.TEXT_SECONDARY,
                    ),
                    holder,
                ],
            ),
        )

    # =========================================================
    # PROFILE
    # =========================================================

    def _profile(self):
        self.profile_name_text = ft.Text(
            getattr(self.profile, "name", None) or "User",
            size=10,
            color=AppColors.TEXT,
        )

        self.profile_plan_text = ft.Text(
            getattr(self.profile, "plan", None) or "Student Plan",
            size=8,
            color=AppColors.MUTED,
        )

        self.profile_avatar_text = ft.Text(
            getattr(self.profile, "initials", None) or "U",
            size=13,
            color=AppColors.WHITE,
        )

        self.profile_text = ft.Container(
            width=LABEL_WIDTH,
            content=ft.Column(
                spacing=0,
                controls=[
                    self.profile_name_text,
                    self.profile_plan_text,
                ],
            ),
            animate=ft.Animation(
                AppAnimations.NORMAL,
                ft.AnimationCurve.EASE_OUT,
            ),
        )

        self.labels.append(self.profile_text)

        return ft.Container(
            height=64,
            margin=ft.Margin.only(top=10),
            padding=ft.Padding.symmetric(horizontal=10),
            border_radius=12,
            bgcolor="#0A1422",
            border=ft.Border.all(1, "#223047"),
            ink=True,
            tooltip="Edit profile",
            on_click=self._edit_profile,
            on_hover=self._hover_simple,
            data={"rest_bg": "#0A1422"},
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Container(
                        width=35,
                        height=35,
                        border_radius=99,
                        alignment=ft.Alignment.CENTER,
                        gradient=ft.LinearGradient(
                            colors=["#7B4AE2", "#3158B6"],
                        ),
                        content=self.profile_avatar_text,
                    ),
                    self.profile_text,
                    ft.Icon(
                        ft.Icons.UNFOLD_MORE,
                        size=16,
                        color=AppColors.TEXT_SECONDARY,
                    ),
                ],
            ),
        )

    # =========================================================
    # HOVER
    # =========================================================

    @staticmethod
    def _hover_simple(e):
        rest_bg = (e.control.data or {}).get("rest_bg", "#00000000")

        e.control.bgcolor = (
            "#101D31"
            if Sidebar._is_hovered(e.data)
            else rest_bg
        )

        e.control.update()

    def _hover(self, e):
        item = e.control

        if item.data["index"] != self.selected_index:
            item.bgcolor = (
                "#101D31"
                if self._is_hovered(e.data)
                else "#00000000"
            )
            item.update()

    # =========================================================
    # SETTINGS / ABOUT
    # =========================================================

    def _edit_profile(self, e):
        if self.on_edit_profile:
            self.on_edit_profile(e)

    def _show_about(self, e):
        if self.on_show_about:
            self.on_show_about(e)

    def set_profile(self, profile, refresh=True):
        self.profile = profile

        self.profile_name_text.value = profile.name
        self.profile_plan_text.value = profile.plan
        self.profile_avatar_text.value = profile.initials

        if refresh:
            try:
                self.profile_name_text.update()
                self.profile_plan_text.update()
                self.profile_avatar_text.update()
            except Exception:
                pass

    # =========================================================
    # SELECTION
    # =========================================================

    def _select(self, index):
        if not 0 <= index < len(NAV_ITEMS):
            return

        self.selected_index = index
        self._reveal_index(index)
        self._refresh_selection()

        if self.on_navigation_change:
            self.on_navigation_change(index)

    def _refresh_selection(self):
        for control in self.items:
            data = control.data
            selected = data["index"] == self.selected_index
            group = data["group"]

            control.bgcolor = (
                self._accent_bg(group)
                if selected
                else "#00000000"
            )

            control.border = ft.Border.all(
                1,
                self._accent_border(group)
                if selected
                else "#00000000",
            )

            data["icon_control"].name = (
                data["selected_icon"]
                if selected
                else data["icon"]
            )

            data["icon_control"].color = (
                "#EAF0FF"
                if selected
                else AppColors.TEXT_SECONDARY
            )

            data["label_control"].color = (
                "#F4F6FD"
                if selected
                else AppColors.TEXT_SECONDARY
            )

        self._safe_update()

    def _safe_update(self):
        try:
            self.control.update()
        except Exception:
            pass

    # =========================================================
    # COLLAPSE / EXPAND
    # =========================================================

    def toggle(self):
        self.extended = not self.extended

        self.control.width = (
            AppLayout.SIDEBAR_EXPANDED_WIDTH
            if self.extended
            else AppLayout.SIDEBAR_COLLAPSED_WIDTH
        )

        for label in self.labels:
            label.width = LABEL_WIDTH if self.extended else 0

        self._apply_group_visibility()
        self._safe_update()

    # =========================================================
    # PUBLIC ROUTE API
    # =========================================================

    @staticmethod
    def index_of(key, default=0):
        return route_index(key, default)

    @staticmethod
    def key_of(index):
        if 0 <= index < len(NAV_ITEMS):
            return NAV_ITEMS[index]["key"]
        return "home"

    @staticmethod
    def group_of(index):
        if 0 <= index < len(NAV_ITEMS):
            return NAV_ITEMS[index]["group"]
        return None

    @staticmethod
    def route_count():
        return len(NAV_ITEMS)

    def get_selected_index(self):
        return self.selected_index

    def set_selected_index(self, index):
        if 0 <= index < len(NAV_ITEMS):
            self.selected_index = index
            self._reveal_index(index)
            self._refresh_selection()

    def get_feature_name(self, index=None):
        index = self.selected_index if index is None else index

        return (
            NAV_ITEMS[index]["label"]
            if 0 <= index < len(NAV_ITEMS)
            else "Home"
        )

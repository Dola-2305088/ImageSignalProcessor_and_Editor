import flet as ft

from ui.theme import AppAnimations, AppColors, AppLayout


NAV_ITEMS = [
    ("Home", ft.Icons.HOME_OUTLINED, ft.Icons.HOME),
    ("Frequency", ft.Icons.GRAPHIC_EQ, ft.Icons.GRAPHIC_EQ),
    ("Compression", ft.Icons.ARCHIVE_OUTLINED, ft.Icons.ARCHIVE),
    ("Texture", ft.Icons.GRID_ON_OUTLINED, ft.Icons.GRID_ON),
    ("Hybrid", ft.Icons.COMPARE_OUTLINED, ft.Icons.COMPARE),
    ("Color", ft.Icons.PALETTE_OUTLINED, ft.Icons.PALETTE),
]


class Sidebar:
    """Persistent mockup-style navigation with its own collapse/expand control."""

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

        self.items = []
        self.labels = []

        self.control = self._build()

    @staticmethod
    def _is_hovered(value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes"}

    def _build(self):
        nav = ft.Column(
            spacing=4,
            controls=[
                self._nav_item(i, *item)
                for i, item in enumerate(NAV_ITEMS)
            ],
        )

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
                    # -----------------------------------------
                    # SIDEBAR OWNED COLLAPSE / EXPAND CONTROLS
                    # -----------------------------------------
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

                    ft.Container(expand=True),

                    self._profile(),
                ],
            ),
        )

    # =========================================================
    # NAVIGATION ITEM
    # =========================================================

    def _nav_item(self, index, label, icon, selected_icon):
        selected = index == self.selected_index

        icon_control = ft.Icon(
            selected_icon if selected else icon,
            size=21,
            color="#EAF0FF" if selected else AppColors.TEXT_SECONDARY,
        )

        label_control = ft.Text(
            label,
            size=11,
            color="#F4F6FD" if selected else AppColors.TEXT_SECONDARY,
        )

        label_holder = ft.Container(
            width=128,
            content=label_control,
            animate=ft.Animation(
                AppAnimations.NORMAL,
                ft.AnimationCurve.EASE_OUT,
            ),
        )

        item = ft.Container(
            height=46,
            padding=ft.Padding.symmetric(horizontal=10),
            border_radius=10,
            bgcolor="#17284C" if selected else "#00000000",
            border=ft.Border.all(
                1,
                "#314A84" if selected else "#00000000",
            ),
            ink=True,
            on_click=lambda e, i=index: self._select(i),
            on_hover=self._hover,
            animate=ft.Animation(
                AppAnimations.FAST,
                ft.AnimationCurve.EASE_OUT,
            ),
            data={
                "index": index,
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

        self.items.append(item)
        self.labels.append(label_holder)

        return item

    # =========================================================
    # SIMPLE ITEM
    # =========================================================

    def _simple_item(self, label, icon, on_click=None):
        holder = ft.Container(
            width=128,
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
            height=44,
            padding=ft.Padding.symmetric(horizontal=10),
            border_radius=10,
            ink=True,
            on_click=on_click,
            on_hover=self._hover_simple,
            data={"rest_bg": "#00000000"},
            content=ft.Row(
                spacing=13,
                controls=[
                    ft.Icon(
                        icon,
                        size=21,
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
            width=125,
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
        rest_bg = (e.control.data or {}).get(
            "rest_bg",
            "#00000000",
        )

        e.control.bgcolor = (
            "#101D31"
            if str(e.data).lower() == "true"
            else rest_bg
        )

        e.control.update()

    def _hover(self, e):
        item = e.control

        if item.data["index"] != self.selected_index:
            item.bgcolor = (
                "#101D31"
                if str(e.data).lower() == "true"
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
        self._refresh_selection()
        if self.on_navigation_change:
            self.on_navigation_change(index)

    def _refresh_selection(self):
        for i, item in enumerate(self.items):
            selected = i == self.selected_index
            data = item.data

            item.bgcolor = (
                "#17284C"
                if selected
                else "#00000000"
            )

            item.border = ft.Border.all(
                1,
                "#314A84"
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
            label.width = 128 if self.extended else 0

        try:
            self.control.update()
        except Exception:
            pass

    def get_selected_index(self):
        return self.selected_index

    def set_selected_index(self, index):
        if 0 <= index < len(NAV_ITEMS):
            self.selected_index = index
            self._refresh_selection()

    def get_feature_name(self, index=None):
        index = (
            self.selected_index
            if index is None
            else index
        )

        return (
            NAV_ITEMS[index][0]
            if 0 <= index < len(NAV_ITEMS)
            else "Home"
        )
import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
    app_logo_gradient,
)


NAV_ITEMS = [
    ("Home", ft.Icons.HOME_OUTLINED, ft.Icons.HOME, AppColors.CYAN),
    ("Frequency", ft.Icons.TUNE, ft.Icons.TUNE, AppColors.CYAN),
    ("Compression", ft.Icons.BAR_CHART_OUTLINED, ft.Icons.BAR_CHART, AppColors.GREEN),
    ("Texture", ft.Icons.GRID_VIEW_OUTLINED, ft.Icons.GRID_VIEW, AppColors.ORANGE),
    ("Hybrid", ft.Icons.AUTO_AWESOME_OUTLINED, ft.Icons.AUTO_AWESOME, AppColors.PINK),
    ("Color", ft.Icons.PALETTE_OUTLINED, ft.Icons.PALETTE, AppColors.PURPLE),
]


class Sidebar:
    """
    Animated custom sidebar.

    Public API intentionally matches the old Sidebar class:
        - .control
        - toggle()
        - get_selected_index()
        - set_selected_index(index)
        - get_feature_name(index=None)

    This means main_window.py does not need to change.
    """

    def __init__(self, on_navigation_change):
        self.on_navigation_change = on_navigation_change

        self.extended = True
        self.selected_index = 0

        self.nav_controls = []
        self.label_wrappers = []
        self.logo_text_wrapper = None
        self.footer_text_wrapper = None

        self.control = self._build()

    # =========================================================
    # BUILD
    # =========================================================

    def _build(self):
        logo = self._build_logo()

        nav_column = ft.Column(
            spacing=8,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                self._build_nav_item(
                    index=i,
                    label=label,
                    icon=icon,
                    selected_icon=selected_icon,
                    accent=accent,
                )
                for i, (label, icon, selected_icon, accent)
                in enumerate(NAV_ITEMS)
            ],
        )

        footer = self._build_footer()

        body = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                logo,
                ft.Container(height=14),
                nav_column,
                ft.Container(height=10),
                footer,
            ],
        )

        return ft.Container(
            width=AppLayout.SIDEBAR_EXPANDED_WIDTH,
            padding=ft.Padding.only(
                left=12,
                right=12,
                top=14,
                bottom=12,
            ),
            bgcolor=AppColors.SIDEBAR,
            border=ft.Border.only(
                right=ft.BorderSide(
                    1,
                    AppColors.BORDER,
                ),
            ),
            shadow=ft.BoxShadow(
                blur_radius=18,
                spread_radius=0,
                color="#18000000",
                offset=ft.Offset(5, 0),
            ),
            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=body,
        )

    # =========================================================
    # LOGO
    # =========================================================

    def _build_logo(self):
        logo_box = ft.Container(
            width=48,
            height=48,
            border_radius=15,
            gradient=app_logo_gradient(),
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                ft.Icons.WAVES,
                color=AppColors.BLACK,
                size=27,
            ),
        )

        self.logo_text_wrapper = ft.Container(
            width=130,
            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=ft.Column(
                spacing=1,
                controls=[
                    ft.Text(
                        "DSP LAB",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT,
                    ),
                    ft.Text(
                        "Signal Studio",
                        size=8,
                        color=AppColors.MUTED,
                    ),
                ],
            ),
        )

        return ft.Container(
            height=58,
            padding=ft.Padding.symmetric(
                horizontal=4,
                vertical=4,
            ),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    logo_box,
                    self.logo_text_wrapper,
                ],
            ),
        )

    # =========================================================
    # NAV ITEM
    # =========================================================

    def _build_nav_item(
        self,
        index,
        label,
        icon,
        selected_icon,
        accent,
    ):
        icon_control = ft.Icon(
            selected_icon if index == self.selected_index else icon,
            size=20,
            color=(
                accent
                if index == self.selected_index
                else AppColors.MUTED_2
            ),
        )

        icon_shell = ft.Container(
            width=38,
            height=38,
            border_radius=12,
            alignment=ft.Alignment.CENTER,
            bgcolor=(
                f"24{accent[1:]}"
                if index == self.selected_index
                else "#00000000"
            ),
            animate=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=icon_control,
        )

        label_text = ft.Text(
            label,
            size=10,
            weight=(
                ft.FontWeight.BOLD
                if index == self.selected_index
                else ft.FontWeight.W_500
            ),
            color=(
                AppColors.TEXT
                if index == self.selected_index
                else AppColors.MUTED
            ),
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        label_wrapper = ft.Container(
            width=118,
            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=label_text,
        )

        self.label_wrappers.append(label_wrapper)

        indicator = ft.Container(
            width=3,
            height=26 if index == self.selected_index else 8,
            border_radius=4,
            bgcolor=(
                accent
                if index == self.selected_index
                else "#00000000"
            ),
            shadow=(
                ft.BoxShadow(
                    blur_radius=12,
                    color=f"66{accent[1:]}",
                )
                if index == self.selected_index
                else None
            ),
            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
        )

        item = ft.Container(
            height=50,
            padding=ft.Padding.symmetric(
                horizontal=7,
                vertical=5,
            ),
            border_radius=15,
            bgcolor=(
                f"18{accent[1:]}"
                if index == self.selected_index
                else "#00000000"
            ),
            border=ft.Border.all(
                1,
                (
                    f"34{accent[1:]}"
                    if index == self.selected_index
                    else "#00000000"
                ),
            ),
            offset=ft.Offset(0, 0),
            scale=1.0,
            animate_offset=ft.Animation(
                duration=170,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate_scale=ft.Animation(
                duration=170,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            animate=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            ink=True,
            on_click=lambda e, i=index: self._select(i),
            on_hover=self._hover_nav_item,
            data={
                "index": index,
                "accent": accent,
                "icon_shell": icon_shell,
                "icon_control": icon_control,
                "label_text": label_text,
                "indicator": indicator,
            },
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    indicator,
                    icon_shell,
                    label_wrapper,
                ],
            ),
        )

        self.nav_controls.append(item)
        return item

    # =========================================================
    # FOOTER
    # =========================================================

    def _build_footer(self):
        status_dot = ft.Container(
            width=7,
            height=7,
            border_radius=100,
            bgcolor=AppColors.GREEN,
            shadow=ft.BoxShadow(
                blur_radius=7,
                color="#5534D399",
            ),
        )

        self.footer_text_wrapper = ft.Container(
            width=120,
            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=ft.Column(
                spacing=1,
                controls=[
                    ft.Text(
                        "LAB READY",
                        size=8,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.GREEN_LIGHT,
                    ),
                    ft.Text(
                        "6 workspaces online",
                        size=7,
                        color=AppColors.MUTED,
                    ),
                ],
            ),
        )

        return ft.Container(
            height=48,
            padding=ft.Padding.symmetric(
                horizontal=11,
                vertical=7,
            ),
            border_radius=14,
            bgcolor="#09141A",
            border=ft.Border.all(
                1,
                "#17342D",
            ),
            content=ft.Row(
                spacing=10,
                controls=[
                    status_dot,
                    self.footer_text_wrapper,
                ],
            ),
        )

    # =========================================================
    # HOVER
    # =========================================================

    @staticmethod
    def _is_hovered(value):
        if isinstance(value, bool):
            return value

        return str(value).strip().lower() in {
            "true",
            "1",
            "yes",
        }

    def _hover_nav_item(self, e):
        hovered = self._is_hovered(e.data)

        item = e.control
        data = item.data

        index = data["index"]
        accent = data["accent"]
        icon_shell = data["icon_shell"]
        icon_control = data["icon_control"]
        label_text = data["label_text"]
        indicator = data["indicator"]

        selected = index == self.selected_index

        if hovered:
            # Small slide + scale gives the sidebar a responsive "lift".
            item.offset = ft.Offset(0.035, 0)
            item.scale = 1.018

            item.bgcolor = (
                f"24{accent[1:]}"
                if selected
                else f"12{accent[1:]}"
            )

            item.border = ft.Border.all(
                1,
                f"38{accent[1:]}",
            )

            icon_shell.bgcolor = f"28{accent[1:]}"
            icon_shell.scale = 1.08

            icon_control.color = accent
            label_text.color = AppColors.TEXT

            if not selected:
                indicator.height = 16
                indicator.bgcolor = f"AA{accent[1:]}"

        else:
            item.offset = ft.Offset(0, 0)
            item.scale = 1.0

            if selected:
                item.bgcolor = f"18{accent[1:]}"
                item.border = ft.Border.all(
                    1,
                    f"34{accent[1:]}",
                )

                icon_shell.bgcolor = f"24{accent[1:]}"
                icon_shell.scale = 1.0

                icon_control.color = accent
                label_text.color = AppColors.TEXT

                indicator.height = 26
                indicator.bgcolor = accent
            else:
                item.bgcolor = "#00000000"
                item.border = ft.Border.all(
                    1,
                    "#00000000",
                )

                icon_shell.bgcolor = "#00000000"
                icon_shell.scale = 1.0

                icon_control.color = AppColors.MUTED_2
                label_text.color = AppColors.MUTED

                indicator.height = 8
                indicator.bgcolor = "#00000000"

        item.update()

    # =========================================================
    # SELECTION
    # =========================================================

    def _select(self, index):
        if index < 0 or index >= len(NAV_ITEMS):
            return

        self.selected_index = index
        self._refresh_selection()

        if self.on_navigation_change:
            self.on_navigation_change(index)

    def _refresh_selection(self):
        for index, item in enumerate(self.nav_controls):
            (
                label,
                normal_icon,
                selected_icon,
                accent,
            ) = NAV_ITEMS[index]

            data = item.data

            icon_shell = data["icon_shell"]
            icon_control = data["icon_control"]
            label_text = data["label_text"]
            indicator = data["indicator"]

            selected = index == self.selected_index

            if selected:
                item.bgcolor = f"18{accent[1:]}"
                item.border = ft.Border.all(
                    1,
                    f"34{accent[1:]}",
                )

                icon_shell.bgcolor = f"24{accent[1:]}"
                icon_control.name = selected_icon
                icon_control.color = accent

                label_text.color = AppColors.TEXT
                label_text.weight = ft.FontWeight.BOLD

                indicator.height = 26
                indicator.bgcolor = accent
                indicator.shadow = ft.BoxShadow(
                    blur_radius=12,
                    color=f"66{accent[1:]}",
                )
            else:
                item.bgcolor = "#00000000"
                item.border = ft.Border.all(
                    1,
                    "#00000000",
                )

                icon_shell.bgcolor = "#00000000"
                icon_control.name = normal_icon
                icon_control.color = AppColors.MUTED_2

                label_text.color = AppColors.MUTED
                label_text.weight = ft.FontWeight.W_500

                indicator.height = 8
                indicator.bgcolor = "#00000000"
                indicator.shadow = None

        self.control.update()

    # =========================================================
    # COLLAPSE / EXPAND ANIMATION
    # =========================================================

    def toggle(self):
        self.extended = not self.extended

        if self.extended:
            self.control.width = AppLayout.SIDEBAR_EXPANDED_WIDTH

            self.logo_text_wrapper.width = 130
            self.footer_text_wrapper.width = 120

            for wrapper in self.label_wrappers:
                wrapper.width = 118

        else:
            self.control.width = AppLayout.SIDEBAR_COLLAPSED_WIDTH

            self.logo_text_wrapper.width = 0
            self.footer_text_wrapper.width = 0

            for wrapper in self.label_wrappers:
                wrapper.width = 0

        self.control.update()

    # =========================================================
    # PUBLIC API
    # =========================================================

    def get_selected_index(self):
        return self.selected_index

    def set_selected_index(self, index):
        if index < 0 or index >= len(NAV_ITEMS):
            return

        self.selected_index = index
        self._refresh_selection()

    def get_feature_name(self, index=None):
        if index is None:
            index = self.selected_index

        if index < 0 or index >= len(NAV_ITEMS):
            return "Home"

        return NAV_ITEMS[index][0]
import flet as ft

from ui.theme import AppColors, AppLayout, AppAnimations, app_logo_gradient


NAV_ITEMS = [
    ("Home", ft.Icons.HOME_OUTLINED, ft.Icons.HOME),
    ("Frequency", ft.Icons.TUNE, ft.Icons.TUNE),
    ("Compression", ft.Icons.BAR_CHART_OUTLINED, ft.Icons.BAR_CHART),
    ("Texture", ft.Icons.GRID_VIEW_OUTLINED, ft.Icons.GRID_VIEW),
    ("Hybrid", ft.Icons.AUTO_AWESOME_OUTLINED, ft.Icons.AUTO_AWESOME),
    ("Color", ft.Icons.PALETTE_OUTLINED, ft.Icons.PALETTE),
]


class Sidebar:
    def __init__(self, on_navigation_change):
        self.on_navigation_change = on_navigation_change
        self.extended = True
        self.navigation_rail = self._build_navigation_rail()
        self.control = ft.Container(
            width=AppLayout.SIDEBAR_EXPANDED_WIDTH,
            bgcolor=AppColors.SIDEBAR,
            border=ft.Border.only(
                right=ft.BorderSide(1, AppColors.BORDER),
            ),
            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=self.navigation_rail,
        )

    def _build_navigation_rail(self):
        return ft.NavigationRail(
            selected_index=0,
            extended=True,
            label_type=ft.NavigationRailLabelType.NONE,
            min_width=76,
            min_extended_width=AppLayout.SIDEBAR_EXPANDED_WIDTH,
            group_alignment=-0.95,
            use_indicator=True,
            indicator_color="#1D4ED8",
            bgcolor=AppColors.SIDEBAR,
            scrollable=True,
            on_change=self._handle_navigation_change,
            leading=ft.Container(
                padding=ft.Padding.only(top=14, bottom=18),
                content=ft.Column(
                    spacing=7,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=48,
                            height=48,
                            border_radius=ft.BorderRadius.all(15),
                            gradient=app_logo_gradient(),
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(
                                ft.Icons.WAVES,
                                color=AppColors.BLACK,
                                size=27,
                            ),
                        ),
                        ft.Text(
                            "DSP LAB",
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.MUTED,
                        ),
                    ],
                ),
            ),
            destinations=[
                ft.NavigationRailDestination(
                    label=label,
                    icon=icon,
                    selected_icon=selected_icon,
                )
                for label, icon, selected_icon in NAV_ITEMS
            ],
        )

    def _handle_navigation_change(self, e):
        index = e.control.selected_index if e.control.selected_index is not None else 0
        if self.on_navigation_change:
            self.on_navigation_change(index)

    def toggle(self):
        self.extended = not self.extended
        if self.extended:
            self.navigation_rail.extended = True
            self.navigation_rail.label_type = ft.NavigationRailLabelType.NONE
            self.control.width = AppLayout.SIDEBAR_EXPANDED_WIDTH
        else:
            self.navigation_rail.extended = False
            self.navigation_rail.label_type = ft.NavigationRailLabelType.ALL
            self.control.width = AppLayout.SIDEBAR_COLLAPSED_WIDTH
        self.navigation_rail.update()
        self.control.update()

    def get_selected_index(self):
        index = self.navigation_rail.selected_index
        return 0 if index is None else index

    def set_selected_index(self, index):
        if index < 0 or index >= len(NAV_ITEMS):
            return
        self.navigation_rail.selected_index = index
        self.navigation_rail.update()

    def get_feature_name(self, index=None):
        if index is None:
            index = self.get_selected_index()
        if index < 0 or index >= len(NAV_ITEMS):
            return "Home"
        return NAV_ITEMS[index][0]
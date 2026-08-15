import flet as ft

from ui.theme import AppColors, AppLayout, AppAnimations, app_logo_gradient


NAV_ITEMS = [
    ("Home", "Overview", ft.Icons.HOME_OUTLINED, ft.Icons.HOME, AppColors.CYAN),
    ("Frequency", "2D DFT tools", ft.Icons.TUNE, ft.Icons.TUNE, AppColors.CYAN),
    ("Compression", "DFT + PSNR", ft.Icons.BAR_CHART_OUTLINED, ft.Icons.BAR_CHART, AppColors.GREEN),
    ("Texture", "Pattern analysis", ft.Icons.GRID_VIEW_OUTLINED, ft.Icons.GRID_VIEW, AppColors.ORANGE),
    ("Hybrid", "Frequency fusion", ft.Icons.AUTO_AWESOME_OUTLINED, ft.Icons.AUTO_AWESOME, AppColors.PINK),
    ("Color", "RGB + YCbCr", ft.Icons.PALETTE_OUTLINED, ft.Icons.PALETTE, AppColors.PURPLE),
]


class Sidebar:
    """Modern app-navigation rail. Public API matches the original Sidebar."""

    def __init__(self, on_navigation_change):
        self.on_navigation_change = on_navigation_change
        self.extended = True
        self.selected_index = 0
        self.nav_controls = []
        self.label_wrappers = []
        self.subtitle_wrappers = []
        self.logo_text_wrapper = None
        self.footer_text_wrapper = None
        self.control = self._build()

    @staticmethod
    def _is_hovered(value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes"}

    def _build(self):
        nav = ft.Column(
            spacing=7,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                self._build_nav_item(i, *item)
                for i, item in enumerate(NAV_ITEMS)
            ],
        )

        return ft.Container(
            width=AppLayout.SIDEBAR_EXPANDED_WIDTH,
            padding=ft.Padding.only(left=11, right=11, top=12, bottom=11),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_CENTER,
                end=ft.Alignment.BOTTOM_CENTER,
                colors=["#0B121E", "#080D15", "#0A1019"],
            ),
            border=ft.Border.only(right=ft.BorderSide(1, AppColors.BORDER_SOFT)),
            shadow=ft.BoxShadow(
                blur_radius=24,
                spread_radius=0,
                color="#24000000",
                offset=ft.Offset(7, 0),
            ),
            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    self._build_logo(),
                    ft.Container(height=13),
                    ft.Container(
                        padding=ft.Padding.only(left=8, bottom=8),
                        content=ft.Text(
                            "WORKSPACES",
                            size=7,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.MUTED_2,
                        ),
                    ),
                    nav,
                    ft.Container(height=12),
                    self._build_footer(),
                ],
            ),
        )

    def _build_logo(self):
        logo = ft.Container(
            width=44,
            height=44,
            border_radius=14,
            gradient=app_logo_gradient(),
            alignment=ft.Alignment.CENTER,
            shadow=ft.BoxShadow(blur_radius=18, color="#3022D3EE"),
            content=ft.Icon(ft.Icons.WAVES, color=AppColors.BLACK, size=24),
        )

        self.logo_text_wrapper = ft.Container(
            width=130,
            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Text(
                        "SIGNAL STUDIO",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.TEXT,
                    ),
                    ft.Text(
                        "Image DSP workspace",
                        size=7,
                        color=AppColors.MUTED,
                    ),
                ],
            ),
        )

        return ft.Container(
            height=58,
            padding=ft.Padding.symmetric(horizontal=5, vertical=5),
            content=ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[logo, self.logo_text_wrapper],
            ),
        )

    def _build_nav_item(self, index, label, subtitle, icon, selected_icon, accent):
        selected = index == self.selected_index

        icon_control = ft.Icon(
            selected_icon if selected else icon,
            size=19,
            color=accent if selected else AppColors.MUTED_2,
        )
        icon_shell = ft.Container(
            width=38,
            height=38,
            alignment=ft.Alignment.CENTER,
            border_radius=12,
            bgcolor=f"1C{accent[1:]}" if selected else "#081019",
            border=ft.Border.all(1, f"38{accent[1:]}" if selected else AppColors.BORDER_SOFT),
            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=icon_control,
        )

        label_text = ft.Text(
            label,
            size=10,
            weight=ft.FontWeight.BOLD if selected else ft.FontWeight.W_600,
            color=AppColors.TEXT if selected else AppColors.MUTED,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        subtitle_text = ft.Text(
            subtitle,
            size=7,
            color=accent if selected else AppColors.MUTED_2,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        label_wrapper = ft.Container(
            width=120,
            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=ft.Column(spacing=0, controls=[label_text, subtitle_text]),
        )
        self.label_wrappers.append(label_wrapper)

        indicator = ft.Container(
            width=3,
            height=24 if selected else 0,
            border_radius=4,
            bgcolor=accent if selected else "#00000000",
            shadow=ft.BoxShadow(blur_radius=10, color=f"66{accent[1:]}") if selected else None,
            animate=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
        )

        item = ft.Container(
            height=55,
            padding=ft.Padding.symmetric(horizontal=7, vertical=6),
            border_radius=15,
            bgcolor=f"12{accent[1:]}" if selected else "#00000000",
            border=ft.Border.all(1, f"2D{accent[1:]}" if selected else "#00000000"),
            scale=1.0,
            offset=ft.Offset(0, 0),
            animate_scale=ft.Animation(duration=160, curve=ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(duration=160, curve=ft.AnimationCurve.EASE_OUT),
            animate=ft.Animation(duration=160, curve=ft.AnimationCurve.EASE_OUT),
            ink=True,
            on_click=lambda e, i=index: self._select(i),
            on_hover=self._hover_nav_item,
            data={
                "index": index,
                "accent": accent,
                "icon": icon,
                "selected_icon": selected_icon,
                "icon_shell": icon_shell,
                "icon_control": icon_control,
                "label_text": label_text,
                "subtitle_text": subtitle_text,
                "indicator": indicator,
            },
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[indicator, icon_shell, label_wrapper],
            ),
        )
        self.nav_controls.append(item)
        return item

    def _build_footer(self):
        self.footer_text_wrapper = ft.Container(
            width=128,
            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Text(
                        "ENGINE READY",
                        size=8,
                        weight=ft.FontWeight.BOLD,
                        color=AppColors.GREEN_LIGHT,
                    ),
                    ft.Text(
                        "Frequency pipeline online",
                        size=7,
                        color=AppColors.MUTED_2,
                    ),
                ],
            ),
        )

        return ft.Container(
            height=54,
            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
            border_radius=15,
            bgcolor="#08120F",
            border=ft.Border.all(1, "#18352D"),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Container(
                        width=32,
                        height=32,
                        alignment=ft.Alignment.CENTER,
                        border_radius=10,
                        bgcolor="#10261F",
                        content=ft.Container(
                            width=8,
                            height=8,
                            border_radius=100,
                            bgcolor=AppColors.GREEN,
                            shadow=ft.BoxShadow(blur_radius=9, color="#6634D399"),
                        ),
                    ),
                    self.footer_text_wrapper,
                ],
            ),
        )

    def _hover_nav_item(self, e):
        hovered = self._is_hovered(e.data)
        item = e.control
        data = item.data
        selected = data["index"] == self.selected_index
        accent = data["accent"]

        item.scale = 1.012 if hovered else 1.0
        item.offset = ft.Offset(0.02, 0) if hovered else ft.Offset(0, 0)

        if hovered and not selected:
            item.bgcolor = f"0E{accent[1:]}"
            item.border = ft.Border.all(1, f"25{accent[1:]}")
            data["icon_shell"].bgcolor = f"15{accent[1:]}"
            data["icon_control"].color = accent
            data["label_text"].color = AppColors.TEXT
        elif not selected:
            item.bgcolor = "#00000000"
            item.border = ft.Border.all(1, "#00000000")
            data["icon_shell"].bgcolor = "#081019"
            data["icon_control"].color = AppColors.MUTED_2
            data["label_text"].color = AppColors.MUTED
        item.update()

    def _select(self, index):
        if not 0 <= index < len(NAV_ITEMS):
            return
        self.selected_index = index
        self._refresh_selection()
        if self.on_navigation_change:
            self.on_navigation_change(index)

    def _refresh_selection(self):
        for index, item in enumerate(self.nav_controls):
            label, subtitle, normal_icon, selected_icon, accent = NAV_ITEMS[index]
            data = item.data
            selected = index == self.selected_index

            item.bgcolor = f"12{accent[1:]}" if selected else "#00000000"
            item.border = ft.Border.all(1, f"2D{accent[1:]}" if selected else "#00000000")
            data["icon_shell"].bgcolor = f"1C{accent[1:]}" if selected else "#081019"
            data["icon_shell"].border = ft.Border.all(1, f"38{accent[1:]}" if selected else AppColors.BORDER_SOFT)
            data["icon_control"].name = selected_icon if selected else normal_icon
            data["icon_control"].color = accent if selected else AppColors.MUTED_2
            data["label_text"].color = AppColors.TEXT if selected else AppColors.MUTED
            data["label_text"].weight = ft.FontWeight.BOLD if selected else ft.FontWeight.W_600
            data["subtitle_text"].color = accent if selected else AppColors.MUTED_2
            data["indicator"].height = 24 if selected else 0
            data["indicator"].bgcolor = accent if selected else "#00000000"
            data["indicator"].shadow = ft.BoxShadow(blur_radius=10, color=f"66{accent[1:]}") if selected else None
        self.control.update()

    def toggle(self):
        self.extended = not self.extended
        if self.extended:
            self.control.width = AppLayout.SIDEBAR_EXPANDED_WIDTH
            self.logo_text_wrapper.width = 130
            self.footer_text_wrapper.width = 128
            for wrapper in self.label_wrappers:
                wrapper.width = 120
        else:
            self.control.width = AppLayout.SIDEBAR_COLLAPSED_WIDTH
            self.logo_text_wrapper.width = 0
            self.footer_text_wrapper.width = 0
            for wrapper in self.label_wrappers:
                wrapper.width = 0
        self.control.update()

    def get_selected_index(self):
        return self.selected_index

    def set_selected_index(self, index):
        if not 0 <= index < len(NAV_ITEMS):
            return
        self.selected_index = index
        self._refresh_selection()

    def get_feature_name(self, index=None):
        index = self.selected_index if index is None else index
        if not 0 <= index < len(NAV_ITEMS):
            return "Home"
        return NAV_ITEMS[index][0]

"""Grouped navigation sidebar.

The application has three modes, chosen from the Home page:

    Explore    -> Spatial domain + Frequency domain feature pages

    Discover   -> animated lessons (learning mode)

    SaveEarth  -> the image-processing mini-game

Feature pages are organised under collapsible groups that mirror the

project's core story:

    Spatial domain    -> convolution based processing

    Frequency domain  -> 2D DFT based processing

    Discover          -> lessons that animate those operations

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

LEARN_SPATIAL = "learn_spatial"

LEARN_FREQUENCY = "learn_frequency"

# Which band of the sidebar a group belongs to. Nine lessons under one

# "Discover" heading was a wall of text; split by domain they mirror the

# feature groups directly above them.

SECTIONS = [

    ("WORKSPACE", (SPATIAL, FREQUENCY)),

    ("LEARN", (LEARN_SPATIAL, LEARN_FREQUENCY)),

]

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

    LEARN_SPATIAL: {

        "title": "Spatial lessons",

        "icon": ft.Icons.SCHOOL_OUTLINED,

        "accent": AppColors.ORANGE_LIGHT,

        "accent_bg": "#2A2110",

        "accent_border": "#7A5A1C",

        "unit": "lessons",

    },

    LEARN_FREQUENCY: {

        "title": "Frequency lessons",

        "icon": ft.Icons.GRAPHIC_EQ,

        "accent": "#34D399",

        "accent_bg": "#0F2A22",

        "accent_border": "#1F6B52",

        "unit": "lessons",

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

        "icon": ft.Icons.HOME_ROUNDED,

        "selected_icon": ft.Icons.HOME_ROUNDED,

        "group": None,

        "tile": ("#8998FF", "#A66CF5"),

        "tile_bg": "#182443",

        "tile_selected": ("#5C74EE", "#9261D8"),

        "selected_bg": "#172343",

        "selected_border": "#465B9B",

    },

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

    {

        "key": "learn_convolution",

        "label": "Convolution",

        "icon": ft.Icons.GRID_4X4,

        "selected_icon": ft.Icons.GRID_4X4,

        "group": LEARN_SPATIAL,

        "full_page": True,

    },

    {

        "key": "learn_resize",

        "label": "Resizing",

        "icon": ft.Icons.PHOTO_SIZE_SELECT_LARGE,

        "selected_icon": ft.Icons.PHOTO_SIZE_SELECT_LARGE,

        "group": LEARN_SPATIAL,

        "full_page": True,

    },

    {

        "key": "learn_noise",

        "label": "Noise",

        "icon": ft.Icons.GRAIN,

        "selected_icon": ft.Icons.GRAIN,

        "group": LEARN_SPATIAL,

        "full_page": True,

    },

    {

        "key": "learn_restore",

        "label": "Restoration",

        "icon": ft.Icons.AUTO_FIX_HIGH,

        "selected_icon": ft.Icons.AUTO_FIX_HIGH,

        "group": LEARN_SPATIAL,

        "full_page": True,

    },

    {

        "key": "learn_spectrum",

        "label": "Waves & spectra",

        "icon": ft.Icons.GRAPHIC_EQ,

        "selected_icon": ft.Icons.GRAPHIC_EQ,

        "group": LEARN_FREQUENCY,

        "full_page": True,

    },

    {

        "key": "learn_filter",

        "label": "Filtering & hybrids",

        "icon": ft.Icons.ADJUST,

        "selected_icon": ft.Icons.ADJUST,

        "group": LEARN_FREQUENCY,

        "full_page": True,

    },

    {

        "key": "learn_compression",

        "label": "Compression",

        "icon": ft.Icons.COMPRESS,

        "selected_icon": ft.Icons.COMPRESS,

        "group": LEARN_FREQUENCY,

        "full_page": True,

    },

    {

        "key": "learn_texture",

        "label": "Texture",

        "icon": ft.Icons.TEXTURE,

        "selected_icon": ft.Icons.TEXTURE,

        "group": LEARN_FREQUENCY,

        "full_page": True,

    },

    {

        "key": "learn_colour",

        "label": "Colour",

        "icon": ft.Icons.PALETTE_OUTLINED,

        "selected_icon": ft.Icons.PALETTE_OUTLINED,

        "group": LEARN_FREQUENCY,

        "full_page": True,

    },

    {

        "key": "save_earth",

        "label": "SaveEarth",

        "icon": ft.Icons.PUBLIC,

        "selected_icon": ft.Icons.PUBLIC,

        "group": None,

        "full_page": True,

        "tile": ("#65E8B3", "#31C8E7"),

        "tile_bg": "#102D2B",

        "tile_selected": ("#23AE7E", "#168EA8"),

        "selected_bg": "#102E2D",

        "selected_border": "#277C76",

    },

]

# key -> index, built once so nothing hardcodes an integer route.

ROUTES = {item["key"]: index for index, item in enumerate(NAV_ITEMS)}

def route_index(key, default=0):

    """Resolve a route key to its navigation index."""

    return ROUTES.get(key, default)

def is_full_page(index):

    """True for pages that draw their own stage (Discover, SaveEarth)."""

    if 0 <= index < len(NAV_ITEMS):

        return bool(NAV_ITEMS[index].get("full_page", False))

    return False

def group_keys(group):

    """All route keys belonging to one domain group."""

    return [item["key"] for item in NAV_ITEMS if item["group"] == group]

# One shared grid for every row: marker | icon tile | label.
LABEL_WIDTH = 122
MARKER_WIDTH = 3
ICON_SIZE = 28
ROW_GAP = 9
ROW_INSET = 8
ITEM_HEIGHT = 42
HEADER_HEIGHT = 38

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

        self.group_open = {group: False for group in GROUPS}

        self.items = []

        self.labels = []

        self.group_headers = {}

        self.group_chevrons = {}

        self.group_items = {group: [] for group in GROUPS}

        # These remain aligned when the sidebar is collapsed.
        self.section_controls = []
        self.footer_controls = []
        self.profile_control = None

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

    def _accent_line(group):

        if group is None:

            return AppColors.BLUE_LIGHT

        return GROUPS[group]["accent"]

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

    def _section_label(self, title):
        """Section captions share exactly the same text x-position as links."""
        label = ft.Container(
            width=LABEL_WIDTH,
            alignment=ft.Alignment.CENTER_LEFT,
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(title, size=8, weight=ft.FontWeight.BOLD,
                            color=AppColors.MUTED_DARK),
                    ft.Container(expand=True, height=1, bgcolor="#20334B"),
                ],
            ),
        )
        self.labels.append(label)
        section = ft.Container(
            height=26,
            margin=ft.Margin.only(top=12, bottom=2),
            padding=ft.Padding.symmetric(horizontal=ROW_INSET),
            content=ft.Row(
                spacing=ROW_GAP,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=MARKER_WIDTH),
                    ft.Container(width=ICON_SIZE, height=1, bgcolor="#25364F"),
                    label,
                ],
            ),
        )
        self.section_controls.append(section)
        return section

    def _sidebar_header(self):
        """Place the menu button on the same icon axis as the rows below."""
        self.menu_spacer = ft.Container(width=20)
        self.collapse_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT, width=28, height=28,
            icon_size=18, icon_color=AppColors.TEXT_SECONDARY,
            bgcolor="#101A2B", tooltip="Collapse sidebar",
            on_click=lambda e: self.toggle(),
        )
        return ft.Container(
            height=54,
            content=ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.menu_spacer,
                    ft.IconButton(
                        icon=ft.Icons.MENU, width=28, height=28,
                        icon_size=20, icon_color=AppColors.TEXT_SECONDARY,
                        tooltip="Collapse / expand sidebar",
                        on_click=lambda e: self.toggle(),
                    ),
                    ft.Container(expand=True),
                    self.collapse_button,
                ],
            ),
        )

    def _build(self):

        nav_controls = []

        rendered_groups = set()

        rendered_sections = set()

        for index, item in enumerate(NAV_ITEMS):

            group = item["group"]

            section = next(

                (name for name, groups in SECTIONS if group in groups), None

            )

            if section is not None and section not in rendered_sections:

                rendered_sections.add(section)

                nav_controls.append(self._section_label(section))

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

                    self._sidebar_header(),

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
            ft.Icons.EXPAND_MORE if self.group_open[group] else ft.Icons.CHEVRON_RIGHT,
            size=14, color=AppColors.MUTED,
        )
        self.group_chevrons[group] = chevron
        count_pill = ft.Container(
            width=16, height=16, border_radius=8,
            alignment=ft.Alignment.CENTER,
            bgcolor=meta["accent_bg"],
            border=ft.Border.all(1, meta["accent_border"]),
            content=ft.Text(str(count), size=8, weight=ft.FontWeight.BOLD,
                            color=meta["accent"]),
        )
        label_holder = ft.Container(
            width=LABEL_WIDTH,
            alignment=ft.Alignment.CENTER_LEFT,
            content=ft.Row(
                spacing=3,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=80,
                        alignment=ft.Alignment.CENTER_LEFT,
                        content=ft.Text(meta["title"], size=9.5,
                                        weight=ft.FontWeight.BOLD,
                                        no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
                                        color=AppColors.TEXT_SECONDARY),
                    ),
                    ft.Container(expand=True), count_pill, chevron,
                ],
            ),
        )
        self.labels.append(label_holder)
        header = ft.Container(
            height=HEADER_HEIGHT,
            margin=ft.Margin.only(top=4),
            padding=ft.Padding.symmetric(horizontal=ROW_INSET),
            border_radius=11, ink=True,
            tooltip=f"{meta['title']} ({count} {meta.get('unit', 'features')})",
            on_click=lambda e, g=group: self.toggle_group(g),
            on_hover=self._hover_simple,
            data={"rest_bg": "#00000000"},
            content=ft.Row(
                spacing=ROW_GAP,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=MARKER_WIDTH),
                    ft.Container(
                        width=ICON_SIZE, height=ICON_SIZE,
                        alignment=ft.Alignment.CENTER, border_radius=9,
                        bgcolor=meta["accent_bg"],
                        border=ft.Border.all(1, meta["accent_border"]),
                        content=ft.Icon(meta["icon"], size=16, color=meta["accent"]),
                    ),
                    label_holder,
                ],
            ),
        )
        self.group_headers[group] = header
        return header

    def _nav_item(self, index, item):
        """Use one geometry for Home, SaveEarth, and all standard features."""
        selected = index == self.selected_index
        group = item["group"]
        tile_colors = item.get("tile")
        key = item["key"]
        accent = tile_colors[0] if tile_colors else self._accent_line(group)
        icon_control = ft.Icon(
            item["selected_icon"] if selected else item["icon"],
            size=19 if tile_colors else 18,
            color=("#FFFFFF" if selected else tile_colors[0])
                  if tile_colors else
                  ("#EAF0FF" if selected else AppColors.TEXT_SECONDARY),
        )
        leaf = None
        leaf_badge = None
        if key == "save_earth":
            # A tiny leaf on the globe makes the SaveEarth emblem recognisable
            # at sidebar size. It is built entirely with native Flet controls.
            leaf = ft.Icon(ft.Icons.ECO, size=9,
                           color="#C8FFE1" if selected else "#79E7B5")
            leaf_badge = ft.Container(
                right=0, bottom=0, width=12, height=12,
                alignment=ft.Alignment.CENTER, border_radius=6,
                bgcolor="#176B62" if selected else "#123B37",
                border=ft.Border.all(1, "#5BE1B2"), content=leaf,
            )
            icon_contents = ft.Stack(
                width=24, height=24, alignment=ft.Alignment.CENTER,
                controls=[
                    ft.Container(width=24, height=24, alignment=ft.Alignment.CENTER,
                                 content=icon_control),
                    leaf_badge,
                ],
            )
        else:
            icon_contents = icon_control

        tile = ft.Container(
            width=ICON_SIZE, height=ICON_SIZE, border_radius=9,
            alignment=ft.Alignment.CENTER,
            bgcolor=(None if selected else item["tile_bg"]) if tile_colors else "#00000000",
            gradient=(ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                colors=list(item["tile_selected"]),
            ) if selected and tile_colors else None),
            border=ft.Border.all(1, accent if selected else
                                 (tile_colors[1] if tile_colors else "#00000000"))
                   if tile_colors else None,
            shadow=(ft.BoxShadow(blur_radius=13, spread_radius=-5, color=accent)
                    if selected and tile_colors else None),
            content=icon_contents,
        )
        marker = ft.Container(
            width=MARKER_WIDTH, height=18 if selected else 0,
            border_radius=2, bgcolor=accent,
            animate=ft.Animation(AppAnimations.FAST, ft.AnimationCurve.EASE_OUT),
        )
        label_control = ft.Text(
            item["label"], size=11,
            weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400,
            color="#F4F6FD" if selected else AppColors.TEXT_SECONDARY,
            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
        )
        label_holder = ft.Container(
            width=LABEL_WIDTH, alignment=ft.Alignment.CENTER_LEFT,
            content=label_control,
            animate=ft.Animation(AppAnimations.NORMAL, ft.AnimationCurve.EASE_OUT),
        )
        control = ft.Container(
            height=ITEM_HEIGHT,
            padding=ft.Padding.symmetric(horizontal=ROW_INSET),
            border_radius=11,
            bgcolor=(item["selected_bg"] if tile_colors else self._accent_bg(group))
                    if selected else "#00000000",
            border=ft.Border.all(1,
                (item["selected_border"] if tile_colors else self._accent_border(group))
                if selected else "#00000000"),
            ink=True, tooltip=item["label"],
            on_click=lambda e, i=index: self._select(i),
            on_hover=self._hover,
            animate=ft.Animation(AppAnimations.FAST, ft.AnimationCurve.EASE_OUT),
            data={
                "index": index, "key": key, "group": group,
                "icon": item["icon"], "selected_icon": item["selected_icon"],
                "icon_control": icon_control, "icon_tile": tile,
                "tile_colors": tile_colors, "tile_bg": item.get("tile_bg"),
                "tile_selected": item.get("tile_selected"),
                "selected_bg": item.get("selected_bg"),
                "selected_border": item.get("selected_border"),
                "leaf": leaf, "leaf_badge": leaf_badge,
                "label_control": label_control, "marker": marker,
            },
            content=ft.Row(
                spacing=ROW_GAP,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[marker, tile, label_holder],
            ),
        )
        self.items.append(control)
        self.labels.append(label_holder)
        if group is not None:
            self.group_items[group].append(control)
        return control

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

                chevron.icon = (

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
            width=LABEL_WIDTH, alignment=ft.Alignment.CENTER_LEFT,
            content=ft.Text(label, size=11, color=AppColors.TEXT_SECONDARY),
            animate=ft.Animation(AppAnimations.NORMAL, ft.AnimationCurve.EASE_OUT),
        )
        self.labels.append(holder)
        control = ft.Container(
            height=ITEM_HEIGHT,
            padding=ft.Padding.symmetric(horizontal=ROW_INSET),
            border_radius=10, ink=True, tooltip=label,
            on_click=on_click, on_hover=self._hover_simple,
            data={"rest_bg": "#00000000"},
            content=ft.Row(
                spacing=ROW_GAP,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=MARKER_WIDTH),
                    ft.Container(width=ICON_SIZE, height=ICON_SIZE,
                                 alignment=ft.Alignment.CENTER,
                                 content=ft.Icon(icon, size=18,
                                                 color=AppColors.TEXT_SECONDARY)),
                    holder,
                ],
            ),
        )
        self.footer_controls.append(control)
        return control

    def _profile(self):
        """The avatar and the account name use the same two navigation columns."""
        self.profile_name_text = ft.Text(
            getattr(self.profile, "name", None) or "User", size=11,
            weight=ft.FontWeight.W_600, color=AppColors.TEXT,
            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.profile_avatar_text = ft.Text(
            getattr(self.profile, "initials", None) or "U", size=10,
            weight=ft.FontWeight.BOLD, color=AppColors.WHITE,
        )
        self.profile_text = ft.Container(
            width=LABEL_WIDTH, alignment=ft.Alignment.CENTER_LEFT,
            content=ft.Row(
                spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=100, alignment=ft.Alignment.CENTER_LEFT,
                                 content=self.profile_name_text),
                    ft.Container(width=18, height=18,
                                 alignment=ft.Alignment.CENTER, border_radius=6,
                                 bgcolor="#182A40",
                                 content=ft.Icon(ft.Icons.TUNE_ROUNDED, size=12,
                                                 color=AppColors.TEXT_SECONDARY)),
                ],
            ),
            animate=ft.Animation(AppAnimations.NORMAL, ft.AnimationCurve.EASE_OUT),
        )
        self.labels.append(self.profile_text)
        avatar = ft.Container(
            width=ICON_SIZE, height=ICON_SIZE, border_radius=99,
            alignment=ft.Alignment.CENTER,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#8B5CF6", "#3158B6"],
            ),
            border=ft.Border.all(1, "#5967AF"),
            content=self.profile_avatar_text,
        )
        self.profile_control = ft.Container(
            height=50, margin=ft.Margin.only(top=10),
            padding=ft.Padding.symmetric(horizontal=ROW_INSET),
            border_radius=13,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                colors=["#101A2B", "#0A1220"],
            ),
            border=ft.Border.all(1, "#223047"),
            ink=True, tooltip="Edit profile", on_click=self._edit_profile,
            content=ft.Row(
                spacing=ROW_GAP,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[ft.Container(width=MARKER_WIDTH), avatar, self.profile_text],
            ),
        )
        return self.profile_control

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

        # The plan is intentionally not shown here; Settings owns it.

        self.profile_name_text.value = profile.name

        self.profile_avatar_text.value = profile.initials

        if refresh:

            try:

                self.profile_name_text.update()

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
            special = data["tile_colors"] is not None
            accent = data["tile_colors"][0] if special else self._accent_line(group)
            control.bgcolor = (
                (data["selected_bg"] if special else self._accent_bg(group))
                if selected else "#00000000"
            )
            control.border = ft.Border.all(
                1,
                (data["selected_border"] if special else self._accent_border(group))
                if selected else "#00000000",
            )
            data["marker"].bgcolor = accent
            data["marker"].height = 18 if selected else 0
            icon = data["icon_control"]
            icon.icon = data["selected_icon"] if selected else data["icon"]
            icon.color = (
                "#FFFFFF" if selected else accent
            ) if special else (
                "#EAF0FF" if selected else AppColors.TEXT_SECONDARY
            )
            if special:
                tile = data["icon_tile"]
                tile.bgcolor = None if selected else data["tile_bg"]
                tile.gradient = (ft.LinearGradient(
                    begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                    colors=list(data["tile_selected"]),
                ) if selected else None)
                tile.border = ft.Border.all(1,
                    accent if selected else data["tile_colors"][1])
                tile.shadow = (ft.BoxShadow(
                    blur_radius=13, spread_radius=-5, color=accent,
                ) if selected else None)
                if data["leaf"] is not None:
                    data["leaf"].color = "#C8FFE1" if selected else "#79E7B5"
                    data["leaf_badge"].bgcolor = "#176B62" if selected else "#123B37"
            data["label_control"].color = (
                "#F4F6FD" if selected else AppColors.TEXT_SECONDARY
            )
            data["label_control"].weight = (
                ft.FontWeight.W_600 if selected else ft.FontWeight.W_400
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
            AppLayout.SIDEBAR_EXPANDED_WIDTH if self.extended
            else AppLayout.SIDEBAR_COLLAPSED_WIDTH
        )
        self.control.padding = ft.Padding.only(
            left=12 if self.extended else 7,
            right=12 if self.extended else 7, top=10, bottom=12,
        )
        for label in self.labels:
            label.width = LABEL_WIDTH if self.extended else 0
        for section in self.section_controls:
            section.visible = self.extended
        self.menu_spacer.width = 20 if self.extended else 14
        self.collapse_button.visible = self.extended
        for control in self.items + self.footer_controls + [self.profile_control]:
            control.padding = ft.Padding.symmetric(
                horizontal=ROW_INSET if self.extended else 3
            )
            control.content.spacing = ROW_GAP if self.extended else 3
            control.content.alignment = (
                ft.MainAxisAlignment.START if self.extended
                else ft.MainAxisAlignment.CENTER
            )
        self._apply_group_visibility()
        self._safe_update()

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

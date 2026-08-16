import flet as ft


# ============================================================
# APPLICATION COLORS
# ============================================================

class AppColors:

    # --------------------------------------------------------
    # MAIN BACKGROUNDS
    # --------------------------------------------------------

    BG = "#050B14"

    SIDEBAR = "#0D121E"

    SURFACE = "#111827"

    SURFACE_2 = "#151E2F"

    SURFACE_3 = "#1B263A"

    SURFACE_DARK = "#0A0F19"

    SURFACE_SOFT = "#0C1422"


    # --------------------------------------------------------
    # BORDERS
    # --------------------------------------------------------

    BORDER = "#26344D"

    BORDER_LIGHT = "#334155"

    BORDER_SOFT = "#1C2940"


    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    TEXT = "#F8FAFC"

    TEXT_SECONDARY = "#CBD5E1"

    MUTED = "#8FA0B8"

    MUTED_2 = "#64748B"

    MUTED_DARK = "#475569"


    # --------------------------------------------------------
    # MAIN ACCENTS
    # --------------------------------------------------------

    CYAN = "#22D3EE"

    BLUE = "#3B82F6"

    PURPLE = "#8B5CF6"

    PINK = "#EC4899"

    GREEN = "#10B981"

    ORANGE = "#F59E0B"

    RED = "#EF4444"


    # --------------------------------------------------------
    # EXTRA ACCENTS
    # --------------------------------------------------------

    CYAN_LIGHT = "#67E8F9"

    BLUE_LIGHT = "#60A5FA"

    PURPLE_LIGHT = "#A78BFA"

    PINK_LIGHT = "#F472B6"

    GREEN_LIGHT = "#34D399"

    ORANGE_LIGHT = "#FBBF24"


    # --------------------------------------------------------
    # FEATURE BACKGROUNDS
    # --------------------------------------------------------

    BLUE_TINT = "#0C1830"

    CYAN_TINT = "#071A20"

    PURPLE_TINT = "#171128"

    GREEN_TINT = "#081A16"

    ORANGE_TINT = "#17130B"

    PINK_TINT = "#1B0D18"


    # --------------------------------------------------------
    # SPECIAL COLORS
    # --------------------------------------------------------

    BLACK = "#05070B"

    WHITE = "#FFFFFF"

    SUCCESS = GREEN

    WARNING = ORANGE

    ERROR = RED


# ============================================================
# FEATURE COLORS
# ============================================================

class FeatureColors:

    GENERAL = AppColors.BLUE

    FREQUENCY = AppColors.CYAN

    COMPRESSION = AppColors.GREEN

    TEXTURE = AppColors.ORANGE

    HYBRID = AppColors.PINK

    COLOR = AppColors.PURPLE


# ============================================================
# LAYOUT CONSTANTS
# ============================================================

class AppLayout:

    # --------------------------------------------------------
    # WINDOW
    # --------------------------------------------------------

    MIN_WIDTH = 1080

    MIN_HEIGHT = 700


    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    SIDEBAR_EXPANDED_WIDTH = 218

    SIDEBAR_COLLAPSED_WIDTH = 74


    # --------------------------------------------------------
    # TOP BAR
    # --------------------------------------------------------

    HEADER_HEIGHT = 82

    STATUS_BAR_HEIGHT = 38


    # --------------------------------------------------------
    # CARDS
    # --------------------------------------------------------

    CARD_RADIUS = 20

    INNER_RADIUS = 14

    SMALL_RADIUS = 10


    # --------------------------------------------------------
    # SPACING
    # --------------------------------------------------------

    PAGE_PADDING = 20

    CARD_PADDING = 20

    SMALL_PADDING = 14

    SECTION_SPACING = 16


    # --------------------------------------------------------
    # IMAGE PREVIEW
    # --------------------------------------------------------

    IMAGE_CARD_HEIGHT = 385

    IMAGE_PREVIEW_WIDTH = 560

    IMAGE_PREVIEW_HEIGHT = 300


# ============================================================
# ANIMATION CONSTANTS
# ============================================================

class AppAnimations:

    FAST = 150

    NORMAL = 250

    MEDIUM = 350

    SLOW = 450


# ============================================================
# GRADIENTS
# ============================================================

def app_logo_gradient():

    return ft.LinearGradient(
        begin=ft.Alignment.TOP_LEFT,
        end=ft.Alignment.BOTTOM_RIGHT,
        colors=[
            AppColors.CYAN,
            AppColors.PURPLE,
        ],
    )


def header_gradient():

    return ft.LinearGradient(
        begin=ft.Alignment.CENTER_LEFT,
        end=ft.Alignment.CENTER_RIGHT,
        colors=[
            "#0B1220",
            "#10172A",
            "#151329",
        ],
    )


# ============================================================
# DARK THEME
# ============================================================

def create_dark_theme():

    return ft.Theme(

        color_scheme=ft.ColorScheme(

            # Main brand
            primary=AppColors.CYAN,

            secondary=AppColors.PURPLE,

            tertiary=AppColors.PINK,


            # Main surfaces
            surface=AppColors.SURFACE,

            surface_container=AppColors.SURFACE_2,

            surface_container_high=AppColors.SURFACE_3,


            # Borders
            outline=AppColors.BORDER,

            outline_variant=AppColors.BORDER_SOFT,


            # Errors
            error=AppColors.RED,


            # Foreground colors
            on_primary=AppColors.BLACK,

            on_secondary=AppColors.WHITE,

            on_surface=AppColors.TEXT,

            on_error=AppColors.WHITE,
        ),

        scaffold_bgcolor=AppColors.BG,

        card_bgcolor=AppColors.SURFACE,

        divider_color=AppColors.BORDER,

        hover_color="#162033",

        focus_color="#1A2941",

        highlight_color="#182641",

        font_family="Segoe UI",

        use_material3=True,
    )


# ============================================================
# PAGE CONFIGURATION
# ============================================================

def configure_page(page: ft.Page):

    page.title = "Image Signal Processor & Editor"

    page.theme_mode = ft.ThemeMode.DARK

    page.dark_theme = create_dark_theme()

    page.bgcolor = AppColors.BG

    page.padding = 0

    page.spacing = 0


    # --------------------------------------------------------
    # DESKTOP WINDOW
    # --------------------------------------------------------

    page.window.min_width = AppLayout.MIN_WIDTH

    page.window.min_height = AppLayout.MIN_HEIGHT

    page.window.maximized = True

import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
    app_logo_gradient,
)


# ============================================================
# NAVIGATION ITEMS
# ============================================================

NAV_ITEMS = [
    (
        "General",
        ft.Icons.HOME_OUTLINED,
        ft.Icons.HOME,
    ),

    (
        "Frequency",
        ft.Icons.TUNE,
        ft.Icons.TUNE,
    ),

    (
        "Compression",
        ft.Icons.BAR_CHART_OUTLINED,
        ft.Icons.BAR_CHART,
    ),

    (
        "Texture",
        ft.Icons.GRID_VIEW_OUTLINED,
        ft.Icons.GRID_VIEW,
    ),

    (
        "Hybrid",
        ft.Icons.AUTO_AWESOME_OUTLINED,
        ft.Icons.AUTO_AWESOME,
    ),

    (
        "Color",
        ft.Icons.PALETTE_OUTLINED,
        ft.Icons.PALETTE,
    ),
]


# ============================================================
# SIDEBAR
# ============================================================

class Sidebar:

    def __init__(
        self,
        on_navigation_change,
    ):

        # =====================================================
        # CALLBACK
        # =====================================================

        self.on_navigation_change = (
            on_navigation_change
        )


        # =====================================================
        # STATE
        # =====================================================

        self.extended = True


        # =====================================================
        # NAVIGATION RAIL
        # =====================================================

        self.navigation_rail = (
            self._build_navigation_rail()
        )


        # =====================================================
        # MAIN SIDEBAR CONTAINER
        # =====================================================

        self.control = ft.Container(

            width=(
                AppLayout
                .SIDEBAR_EXPANDED_WIDTH
            ),

            bgcolor=AppColors.SIDEBAR,

            border=ft.Border.only(

                right=ft.BorderSide(
                    1,
                    AppColors.BORDER,
                )
            ),

            animate=ft.Animation(
                duration=AppAnimations.NORMAL,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            content=self.navigation_rail,
        )


    # =========================================================
    # BUILD NAVIGATION RAIL
    # =========================================================

    def _build_navigation_rail(self):

        return ft.NavigationRail(

            selected_index=0,

            extended=True,

            label_type=(
                ft.NavigationRailLabelType.NONE
            ),

            min_width=76,

            min_extended_width=(
                AppLayout
                .SIDEBAR_EXPANDED_WIDTH
            ),

            group_alignment=-0.95,

            use_indicator=True,

            indicator_color="#1D4ED8",

            bgcolor=AppColors.SIDEBAR,

            scrollable=True,

            on_change=self._handle_navigation_change,


            # =================================================
            # TOP LOGO
            # =================================================

            leading=ft.Container(

                padding=ft.Padding.only(
                    top=14,
                    bottom=18,
                ),

                content=ft.Column(

                    spacing=7,

                    horizontal_alignment=(
                        ft.CrossAxisAlignment.CENTER
                    ),

                    controls=[

                        # =====================================
                        # LOGO
                        # =====================================

                        ft.Container(

                            width=48,
                            height=48,

                            border_radius=(
                                ft.BorderRadius.all(
                                    15
                                )
                            ),

                            gradient=(
                                app_logo_gradient()
                            ),

                            alignment=(
                                ft.Alignment.CENTER
                            ),

                            content=ft.Icon(
                                ft.Icons.WAVES,
                                color=AppColors.BLACK,
                                size=27,
                            ),
                        ),


                        # =====================================
                        # DSP LABEL
                        # =====================================

                        ft.Text(

                            "DSP LAB",

                            size=10,

                            weight=(
                                ft.FontWeight.BOLD
                            ),

                            color=AppColors.MUTED,
                        ),
                    ],
                ),
            ),


            # =================================================
            # NAVIGATION DESTINATIONS
            # =================================================

            destinations=[

                ft.NavigationRailDestination(

                    label=label,

                    icon=icon,

                    selected_icon=selected_icon,
                )

                for (
                    label,
                    icon,
                    selected_icon,
                ) in NAV_ITEMS
            ],
        )


    # =========================================================
    # HANDLE NAVIGATION CHANGE
    # =========================================================

    def _handle_navigation_change(
        self,
        e,
    ):

        index = (
            e.control.selected_index
            if e.control.selected_index is not None
            else 0
        )


        # Pass the selected index back
        # to main_window.py.

        if self.on_navigation_change:

            self.on_navigation_change(
                index
            )


    # =========================================================
    # TOGGLE EXPANDED / COLLAPSED
    # =========================================================

    def toggle(self):

        self.extended = (
            not self.extended
        )


        # =====================================================
        # EXPANDED SIDEBAR
        # =====================================================

        if self.extended:

            self.navigation_rail.extended = True

            self.navigation_rail.label_type = (
                ft.NavigationRailLabelType.NONE
            )

            self.control.width = (
                AppLayout
                .SIDEBAR_EXPANDED_WIDTH
            )


        # =====================================================
        # COLLAPSED SIDEBAR
        # =====================================================

        else:

            self.navigation_rail.extended = False

            self.navigation_rail.label_type = (
                ft.NavigationRailLabelType.ALL
            )

            self.control.width = (
                AppLayout
                .SIDEBAR_COLLAPSED_WIDTH
            )


        self.navigation_rail.update()

        self.control.update()


    # =========================================================
    # GET CURRENT INDEX
    # =========================================================

    def get_selected_index(self):

        index = (
            self.navigation_rail
            .selected_index
        )


        if index is None:

            return 0


        return index


    # =========================================================
    # SET CURRENT INDEX
    # =========================================================

    def set_selected_index(
        self,
        index,
    ):

        if (
            index < 0
            or index >= len(NAV_ITEMS)
        ):

            return


        self.navigation_rail.selected_index = (
            index
        )


        self.navigation_rail.update()


    # =========================================================
    # GET FEATURE NAME
    # =========================================================

    def get_feature_name(
        self,
        index=None,
    ):

        if index is None:

            index = (
                self.get_selected_index()
            )


        if (
            index < 0
            or index >= len(NAV_ITEMS)
        ):

            return "General"


        return NAV_ITEMS[
            index
        ][0]
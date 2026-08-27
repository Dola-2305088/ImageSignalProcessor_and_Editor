import flet as ft

from ui.theme import (
    AppColors,
    AppLayout,
    AppAnimations,
)


class ControlCard:
    """
    Reusable control container.

    Useful for:
    - Sliders
    - Parameter sections
    - Kernel settings
    - Compression controls
    - Frequency cutoffs
    - Resize settings
    - Blur settings
    - Noise controls
    """

    def __init__(
        self,
        title,
        subtitle=None,
        icon=None,
        accent=None,
        controls=None,
        expand=False,
    ):

        # =====================================================
        # CONFIGURATION
        # =====================================================

        self.title = title

        self.subtitle = subtitle

        self.icon = icon

        self.accent = (
            accent
            or AppColors.CYAN
        )

        self.controls = (
            controls
            or []
        )

        self.expand = expand


        # =====================================================
        # CONTENT COLUMN
        # =====================================================

        self.content_column = ft.Column(
            spacing=12,
            controls=self.controls,
        )


        # =====================================================
        # BUILD
        # =====================================================

        self.control = self._build()


    # =========================================================
    # BUILD CARD
    # =========================================================

    def _build(self):

        header_controls = []


        # =====================================================
        # OPTIONAL ICON
        # =====================================================

        if self.icon is not None:

            header_controls.append(

                ft.Container(

                    width=38,
                    height=38,

                    alignment=ft.Alignment.CENTER,

                    bgcolor=AppColors.SURFACE_3,

                    border_radius=ft.BorderRadius.all(
                        12
                    ),

                    content=ft.Icon(
                        self.icon,
                        size=20,
                        color=self.accent,
                    ),
                )
            )


        # =====================================================
        # TITLE / SUBTITLE
        # =====================================================

        title_column_controls = [

            ft.Text(
                self.title,
                size=12,
                weight=ft.FontWeight.BOLD,
                color=AppColors.TEXT,
            )
        ]


        if self.subtitle:

            title_column_controls.append(

                ft.Text(
                    self.subtitle,
                    size=10,
                    color=AppColors.MUTED,
                )
            )


        header_controls.append(

            ft.Column(

                spacing=2,

                expand=True,

                controls=title_column_controls,
            )
        )


        # =====================================================
        # CARD
        # =====================================================

        return ft.Container(

            expand=self.expand,

            bgcolor=AppColors.SURFACE_SOFT,

            border=ft.Border.all(
                1,
                AppColors.BORDER,
            ),

            border_radius=ft.BorderRadius.all(
                AppLayout.INNER_RADIUS
            ),

            padding=AppLayout.SMALL_PADDING,

            animate_scale=ft.Animation(
                duration=AppAnimations.FAST,
                curve=ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self._on_hover,

            content=ft.Column(

                spacing=12,

                controls=[

                    # =========================================
                    # HEADER
                    # =========================================

                    ft.Row(
                        vertical_alignment=(
                            ft.CrossAxisAlignment.CENTER
                        ),
                        controls=header_controls,
                    ),


                    # =========================================
                    # ACCENT LINE
                    # =========================================

                    ft.Container(
                        height=2,
                        bgcolor=self.accent,
                        border_radius=2,
                    ),


                    # =========================================
                    # USER CONTROLS
                    # =========================================

                    self.content_column,
                ],
            ),
        )


    # =========================================================
    # HOVER
    # =========================================================

    def _on_hover(self, e):

        e.control.scale = (
            1.005
            if e.data
            else 1.0
        )

        e.control.update()


    # =========================================================
    # REPLACE CONTENT
    # =========================================================

    def set_controls(
        self,
        controls,
    ):

        self.controls = controls

        self.content_column.controls = (
            controls
        )

        self.content_column.update()


    # =========================================================
    # ADD CONTROL
    # =========================================================

    def add_control(
        self,
        control,
    ):

        self.content_column.controls.append(
            control
        )

        self.content_column.update()


# ============================================================
# SLIDER CONTROL CARD
# ============================================================

class SliderControlCard:
    """
    Specialized reusable slider card.

    Example:

        slider = SliderControlCard(
            title="Cutoff Radius",
            min_value=2,
            max_value=60,
            value=15,
            suffix="px",
            accent=AppColors.CYAN,
            on_change=my_handler,
        )

        slider.control
    """

    def __init__(
        self,
        title,
        min_value,
        max_value,
        value,
        divisions=None,
        suffix="",
        accent=None,
        on_change=None,
        description=None,
        expand=False,
    ):

        self.title = title

        self.min_value = min_value

        self.max_value = max_value

        self.value = value

        self.divisions = divisions

        self.suffix = suffix

        self.accent = (
            accent
            or AppColors.CYAN
        )

        self.on_change = on_change

        self.description = description


        # =====================================================
        # VALUE LABEL
        # =====================================================

        self.value_text = ft.Text(

            self._format_value(
                value
            ),

            size=13,

            weight=ft.FontWeight.BOLD,

            color=self.accent,
        )


        # =====================================================
        # SLIDER
        # =====================================================

        self.slider = ft.Slider(

            min=min_value,

            max=max_value,

            value=value,

            divisions=divisions,

            active_color=self.accent,

            on_change=self._handle_change,
        )


        # =====================================================
        # BUILD CONTENT
        # =====================================================

        card_controls = [

            ft.Row(

                controls=[

                    ft.Text(
                        title,
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=AppColors.TEXT,
                    ),

                    ft.Container(
                        expand=True
                    ),

                    self.value_text,
                ],
            ),

            self.slider,
        ]


        if description:

            card_controls.append(

                ft.Text(
                    description,
                    size=10,
                    color=AppColors.MUTED,
                )
            )


        # =====================================================
        # REUSE CONTROL CARD
        # =====================================================

        self.card = ControlCard(

            title=title,

            accent=self.accent,

            controls=card_controls,

            expand=expand,
        )


        self.control = (
            self.card.control
        )


    # =========================================================
    # FORMAT VALUE
    # =========================================================

    def _format_value(
        self,
        value,
    ):

        # 15.0 -> 15
        if float(value).is_integer():

            formatted = str(
                int(value)
            )

        else:

            formatted = (
                f"{value:.2f}"
            )


        return (
            f"{formatted}{self.suffix}"
        )


    # =========================================================
    # HANDLE SLIDER CHANGE
    # =========================================================

    def _handle_change(
        self,
        e,
    ):

        self.value = (
            e.control.value
        )


        self.value_text.value = (
            self._format_value(
                self.value
            )
        )


        self.value_text.update()


        # Pass event outward
        # if a view wants to react.

        if self.on_change:

            self.on_change(e)


    # =========================================================
    # GET VALUE
    # =========================================================

    def get_value(self):

        return self.slider.value


    # =========================================================
    # GET INTEGER VALUE
    # =========================================================

    def get_int_value(self):

        return int(
            self.slider.value
        )


    # =========================================================
    # SET VALUE
    # =========================================================

    def set_value(
        self,
        value,
    ):

        self.value = value

        self.slider.value = value

        self.value_text.value = (
            self._format_value(
                value
            )
        )

        self.slider.update()

        self.value_text.update()
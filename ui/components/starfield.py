"""
StarField — animated galaxy background used behind the entire app shell.
Drop this in as ui/components/starfield.py, then make it the FIRST child
of the root ft.Stack in main.py so every view renders on top of a living
star field instead of a flat background.

Wiring it in (inside ImageProcessorApp._build_ui, before self.root):

    from ui.components.starfield import StarField
    ...
    self.starfield = StarField()
    self.root = ft.Stack(
        expand=True,
        controls=[
            self.starfield.control,   # <-- new bottom layer
            app_shell,
            self.loading_overlay.control,
        ],
    )
    ...
    self.page.run_task(self.starfield.start_twinkle)
"""

import asyncio
import random

import flet as ft

from ui.theme import AppColors


class StarField:
    def __init__(self, star_count: int = 90):
        self._stars: list[ft.Container] = []
        self._running = False

        base = ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=AppColors.DEEP_SPACE_GRADIENT,
            ),
        )

        nebula_glow = ft.Container(
            expand=True,
            gradient=ft.RadialGradient(
                center=ft.Alignment(-0.6, -0.8),
                radius=1.4,
                colors=[
                    ft.Colors.with_opacity(0.22, AppColors.PURPLE_DEEP),
                    ft.Colors.with_opacity(0.10, AppColors.BLUE_DEEP),
                    "transparent",
                ],
            ),
        )

        second_glow = ft.Container(
            expand=True,
            gradient=ft.RadialGradient(
                center=ft.Alignment(0.85, 0.9),
                radius=1.2,
                colors=[
                    ft.Colors.with_opacity(0.16, AppColors.PINK),
                    "transparent",
                ],
            ),
        )

        star_dots = []
        for _ in range(star_count):
            size = random.choice([1, 1, 1, 2, 2, 3])
            dot = ft.Container(
                width=size,
                height=size,
                bgcolor=random.choice(
                    [AppColors.TEXT, AppColors.PURPLE_LIGHT, AppColors.CYAN]
                ),
                border_radius=size,
                opacity=random.uniform(0.15, 0.9),
                animate_opacity=ft.Animation(
                    random.randint(900, 2600), ft.AnimationCurve.EASE_IN_OUT
                ),
            )
            self._stars.append(dot)
            # Position proportionally so the scatter holds up at any
            # window size — each star lives in its own full-bleed layer,
            # aligned by fractional coordinates rather than raw pixels.
            star_dots.append(
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(
                        random.uniform(-1, 1), random.uniform(-1, 1)
                    ),
                    content=dot,
                )
            )

        star_layer = ft.Stack(expand=True, controls=star_dots)

        self.control = ft.Stack(
            expand=True,
            controls=[base, nebula_glow, second_glow, star_layer],
        )

    async def start_twinkle(self):
        """Continuously fades random stars in and out. Call via page.run_task()."""
        self._running = True
        while self._running:
            batch_size = max(1, len(self._stars) // 6)
            for star in random.sample(self._stars, k=batch_size):
                star.opacity = random.uniform(0.1, 1.0)
                star.update()
            await asyncio.sleep(random.uniform(1.2, 2.2))

    def stop(self):
        self._running = False
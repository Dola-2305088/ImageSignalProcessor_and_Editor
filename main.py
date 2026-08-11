import flet as ft

from ui.main_window import ImageProcessorApp


def main(page: ft.Page):
    ImageProcessorApp(page)


if __name__ == "__main__":
    ft.run(main)
    #python main.py
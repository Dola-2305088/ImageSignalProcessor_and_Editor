import tkinter as tk

from ui.main_window import ImageProcessorApp


def main():

    root = tk.Tk()

    app = ImageProcessorApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()

    #python main.py
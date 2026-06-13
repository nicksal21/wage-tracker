"""Entry point — simply starts the application."""

from ui.ui_main import App


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
"""Application entry point for Shoki."""

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw  # noqa: E402

APP_ID = "com.farsononline.shoki"


class ShokiWindow(Adw.ApplicationWindow):
    """The main window. Empty in Phase 0 — chrome only, no app logic."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title("Shoki")
        self.set_default_size(800, 600)

        # AdwApplicationWindow has no titlebar of its own, so the header bar
        # goes inside the content tree via AdwToolbarView.
        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(Adw.HeaderBar())
        self.set_content(toolbar_view)


class ShokiApplication(Adw.Application):
    """AdwApplication calls adw_init() in its default startup handler.

    do_startup is intentionally not overridden — the libadwaita docs require
    any subclass to chain up before using GTK or Adwaita API.
    """

    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        window = self.props.active_window
        if not window:
            window = ShokiWindow(application=self)
        window.present()


def main() -> int:
    return ShokiApplication().run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

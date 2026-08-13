"""Application entry point for Shoki."""

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Soup", "3.0")

from gi.repository import Adw, Gio, GLib, Gtk, Soup  # noqa: E402

from shoki.transcribe import DEFAULT_ENDPOINT, transcribe_async  # noqa: E402

APP_ID = "com.farsononline.shoki"

# What the picker offers. Whether the server can actually decode any given one
# depends on it being started with --convert. See docs/ROADMAP.md.
MEDIA_SUFFIXES = (
    "wav", "mp3", "m4a", "flac", "ogg", "oga", "opus", "aac", "wma",
    "mp4", "m4v", "mkv", "mov", "webm", "avi",
)


def load_settings():
    """Return a Gio.Settings, or None if the schema is not installed.

    g_settings_new() treats a missing schema as a programmer error and takes
    the process with it, so look it up first. GIO's documentation recommends
    exactly this for schemas that may not be present. Falling back beats
    crashing: the same rule the Dolphin service menu follows.
    """
    source = Gio.SettingsSchemaSource.get_default()
    if source is None or source.lookup(APP_ID, True) is None:
        return None
    return Gio.Settings.new(APP_ID)


class ShokiWindow(Adw.ApplicationWindow):
    """Source picker, a Transcribe button, and somewhere to put the result."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title("Shoki")
        self.set_default_size(700, 720)

        self._session = Soup.Session()
        self._source = None

        self._settings = load_settings()
        if self._settings is None:
            print(
                f"shoki: GSettings schema {APP_ID} not found; "
                f"falling back to {DEFAULT_ENDPOINT}",
                file=sys.stderr,
            )

        self._toasts = Adw.ToastOverlay()
        self.set_content(self._toasts)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        self._toasts.set_child(toolbar)

        scroller = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        toolbar.set_content(scroller)

        clamp = Adw.Clamp(
            margin_top=24, margin_bottom=24, margin_start=12, margin_end=12
        )
        scroller.set_child(clamp)

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(page)

        page.append(self._build_source_group())
        page.append(self._build_action_button())
        page.append(self._build_transcript_group())

    # ---- settings ---------------------------------------------------------

    def _endpoint(self) -> str:
        """Where to POST. GSettings when available, shipped default otherwise."""
        if self._settings is not None:
            return self._settings.get_string("endpoint-url")
        return DEFAULT_ENDPOINT

    # ---- construction -----------------------------------------------------

    def _build_source_group(self):
        group = Adw.PreferencesGroup(title="Source")

        self._source_row = Adw.ActionRow(
            title="No file chosen",
            subtitle="Pick an audio or video file to transcribe",
        )
        button = Gtk.Button(label="Choose File…", valign=Gtk.Align.CENTER)
        button.connect("clicked", self._on_choose_clicked)
        self._source_row.add_suffix(button)
        self._source_row.set_activatable_widget(button)

        group.add(self._source_row)
        return group

    def _build_action_button(self):
        self._transcribe_button = Gtk.Button(
            label="Transcribe", halign=Gtk.Align.CENTER, sensitive=False
        )
        self._transcribe_button.add_css_class("suggested-action")
        self._transcribe_button.add_css_class("pill")
        self._transcribe_button.connect("clicked", self._on_transcribe_clicked)
        return self._transcribe_button

    def _build_transcript_group(self):
        group = Adw.PreferencesGroup(title="Transcript")

        self._transcript = Gtk.TextView(
            editable=False,
            cursor_visible=False,
            wrap_mode=Gtk.WrapMode.WORD_CHAR,
            top_margin=12, bottom_margin=12, left_margin=12, right_margin=12,
        )
        self._transcript.update_property(
            [Gtk.AccessibleProperty.LABEL], ["Transcript"]
        )

        frame = Gtk.Frame()
        frame.set_child(self._transcript)
        frame.set_size_request(-1, 280)

        group.add(frame)
        return group

    # ---- choosing a file --------------------------------------------------

    def _on_choose_clicked(self, _button):
        media = Gtk.FileFilter(name="Audio and video")
        for suffix in MEDIA_SUFFIXES:
            media.add_suffix(suffix)

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(media)

        dialog = Gtk.FileDialog(
            title="Choose a file to transcribe",
            filters=filters,
            default_filter=media,
        )
        dialog.open(self, None, self._on_file_chosen)

    def _on_file_chosen(self, dialog, result):
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error as exc:
            # Closing the dialog raises DISMISSED. That is not a failure.
            if exc.code != Gtk.DialogError.DISMISSED:
                self._toast(f"Could not open that file: {exc.message}")
            return

        self._source = gfile
        self._source_row.set_title(gfile.get_basename())
        parent = gfile.get_parent()
        self._source_row.set_subtitle(parent.get_path() if parent else "")
        self._transcribe_button.set_sensitive(True)

    # ---- transcribing -----------------------------------------------------

    def _on_transcribe_clicked(self, _button):
        if self._source is None:
            return

        path = self._source.get_path()
        if path is None:
            self._toast("That file is not on the local filesystem.")
            return

        self._set_busy(True)
        self._set_transcript("")

        transcribe_async(
            self._session,
            self._endpoint(),
            path,
            {},                 # Phase 2 fills this dict from the UI
            None,               # Phase 2 passes a Gio.Cancellable here
            self._on_transcription_done,
        )

    def _on_transcription_done(self, transcript, error):
        self._set_busy(False)
        if error is not None:
            self._toast(str(error))
            return
        self._set_transcript(transcript)

    # ---- small helpers ----------------------------------------------------

    def _set_busy(self, busy):
        self._transcribe_button.set_sensitive(not busy)
        self._transcribe_button.set_label(
            "Transcribing…" if busy else "Transcribe"
        )

    def _set_transcript(self, text):
        self._transcript.get_buffer().set_text(text)

    def _toast(self, message):
        self._toasts.add_toast(Adw.Toast(title=message, timeout=6))


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

"""Application entry point for Shoki."""

import os
import shutil
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Soup", "3.0")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk, Soup  # noqa: E402

from shoki import __version__  # noqa: E402
from shoki.transcribe import (  # noqa: E402
    TranscriptionCancelled,
    DEFAULT_ENDPOINT,
    endpoint_problem,
    DEFAULT_RESPONSE_FORMAT,
    FILE_SUFFIXES,
    RESPONSE_FORMATS,
    transcribe_async,
)

APP_ID = "com.farsononline.shoki"

# One constant so the About dialog and the file-manager row cannot drift.
PROJECT_URL = "https://github.com/tonyfarson/shoki"

# What the picker offers. Whether the server can actually decode any given one
# depends on it being started with --convert. See docs/SERVER.md.
MEDIA_SUFFIXES = (
    "wav", "mp3", "m4a", "flac", "ogg", "oga", "opus", "aac", "wma",
    "mp4", "m4v", "mkv", "mov", "webm", "avi",
)

# Shown in the format picker, in RESPONSE_FORMATS order. Keys are the wire
# values; nothing user-facing is ever sent to the server.
FORMAT_LABELS = {
    "text": "Plain text",
    "srt": "SubRip subtitles (SRT)",
    "vtt": "WebVTT subtitles (VTT)",
    "json": "JSON",
    "verbose_json": "JSON with timings and segments",
}

# The only two formats the subtitle tuning settings affect. output_str(), which
# builds every other format, never consults them.
SUBTITLE_FORMATS = ("srt", "vtt")

# Only three of AdwColorScheme's five members are offered. PREFER_LIGHT and
# PREFER_DARK are for applications that want to nudge rather than decide, which
# is not a distinction worth putting in front of a user here.
# How often the liveness check pokes the server during a job. Phase 1 measured
# /health at 0.0004-0.0008 s per reply with an inference outstanding, so this is
# nowhere near expensive; it is this slow because a faster answer tells nobody
# anything they did not already know a second ago.
HEALTH_INTERVAL_SECONDS = 2

# Action, accelerator, and the label the shortcuts dialog shows. One list, so
# the dialog cannot drift out of step with what the keys actually do.
SHORTCUTS = (
    ("win.open-file", "<Primary>o", "Choose a file"),
    ("win.open-folder", "<Primary><Shift>o", "Choose a folder"),
    ("win.transcribe", "<Primary>Return", "Transcribe"),
    ("win.cancel", "Escape", "Cancel the current run"),
    ("win.copy-transcript", "<Primary><Shift>c", "Copy the transcript"),
    ("win.save-transcript", "<Primary>s", "Save the transcript"),
    ("app.preferences", "<Primary>comma", "Preferences"),
    ("app.shortcuts", "<Primary>question", "Keyboard shortcuts"),
    ("app.quit", "<Primary>q", "Quit"),
)

COLOR_SCHEMES = {
    "default": Adw.ColorScheme.DEFAULT,
    "light": Adw.ColorScheme.FORCE_LIGHT,
    "dark": Adw.ColorScheme.FORCE_DARK,
}


def health_url(endpoint: str):
    """Where GET /health lives, derived from the inference endpoint.

    The two cannot be assumed to share a path. `inference_path` is a server
    startup flag -- Tony\'s container moves it to /v1/audio/transcriptions --
    while /health is fixed at the server root. So keep the origin and replace
    the path entirely. Returns None if the endpoint will not parse, in which
    case there is nothing honest to display.
    """
    try:
        uri = GLib.Uri.parse(endpoint, GLib.UriFlags.NONE)
    except GLib.Error:
        return None

    host = uri.get_host()
    if not host:
        return None

    # An absent port is reported as a non-positive value; leaving it off lets
    # the scheme\'s default apply rather than inventing one.
    port = uri.get_port()
    authority = f"{host}:{port}" if port and port > 0 else host

    return f"{uri.get_scheme()}://{authority}/health"


def media_files_in(directory: str):
    """Every media file directly inside `directory`, sorted, non-recursive.

    Non-recursive on purpose: a batch whose size the user cannot predict is a
    batch they cannot sensibly decide to start. Filtered by the same suffix list
    the file picker offers, so the two agree about what Shoki will attempt.
    """
    found = []
    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        if os.path.splitext(name)[1].lstrip(".").lower() in MEDIA_SUFFIXES:
            found.append(path)
    return found


def default_destination() -> str:
    """Where transcripts go when nothing has been chosen.

    Resolved at runtime, never baked into the schema: XDG puts Documents in a
    different place on a localised system, and a hardcoded path would be wrong
    on every machine but the one it was written on.
    """
    documents = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
    return os.path.join(documents or GLib.get_home_dir(), "Transcriptions")


def open_unique(directory: str, stem: str, suffix: str):
    """Create and open a file that did not already exist. Never overwrite.

    Names go foo.txt, foo-1.txt, foo-2.txt. HYPHEN, settled 2026-08-13: it
    matches the existing Dolphin service menu and the transcripts already in
    that folder, and from Phase 3 the two write into the same directory.

    O_EXCL rather than an os.path.exists() check, because between checking and
    opening, a second Shoki window or the service menu could take the name.
    """
    index = 0
    while True:
        name = f"{stem}{suffix}" if index == 0 else f"{stem}-{index}{suffix}"
        path = os.path.join(directory, name)
        try:
            handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            index += 1
            continue
        return path, os.fdopen(handle, "w", encoding="utf-8")


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


class ShokiPreferences(Adw.PreferencesDialog):
    """Defaults, not overrides.

    Nothing changed here touches the job currently set up in the main window.
    The one exception is the colour scheme, which is applied the moment it is
    picked -- a look-and-feel setting that waited for a restart would read as
    broken rather than as deliberate.
    """

    def __init__(self, settings, apply_color_scheme, **kwargs):
        super().__init__(**kwargs)

        self._settings = settings
        self._apply_color_scheme = apply_color_scheme

        self.set_title("Preferences")

        page = Adw.PreferencesPage()
        self.add(page)

        page.add(self._build_server_group())
        page.add(self._build_output_group())
        page.add(self._build_destination_group())
        page.add(self._build_subtitle_group())
        page.add(self._build_integration_group())
        page.add(self._build_appearance_group())

    # ---- groups -----------------------------------------------------------

    def _build_server_group(self):
        group = Adw.PreferencesGroup(
            title="Server",
            description=(
                "The whisper.cpp inference endpoint. The shipped default is the "
                "route an unflagged server serves; a server started with "
                "--inference-path serves a different one."
            ),
        )

        row = Adw.EntryRow(title="Endpoint URL")
        self._settings.bind(
            "endpoint-url", row, "text", Gio.SettingsBindFlags.DEFAULT
        )
        group.add(row)

        return group

    def _build_output_group(self):
        group = Adw.PreferencesGroup(
            title="Output",
            description="What new transcriptions start as. The main window can "
                        "override this for a single job without changing it here.",
        )

        row = Adw.ComboRow(
            title="Default output format",
            model=Gtk.StringList.new([FORMAT_LABELS[f] for f in RESPONSE_FORMATS]),
        )
        self._bind_combo(row, "response-format", RESPONSE_FORMATS)
        group.add(row)

        return group

    def _build_destination_group(self):
        group = Adw.PreferencesGroup(
            title="Destination",
            description="Where transcripts are saved unless the main window "
                        "overrides it for a single job.",
        )

        self._destination_row = Adw.ActionRow(title="Default folder")
        self._sync_destination_row()

        button = Gtk.Button(label="Choose\u2026", valign=Gtk.Align.CENTER)
        button.connect("clicked", self._on_choose_destination)
        self._destination_row.add_suffix(button)
        self._destination_row.set_activatable_widget(button)

        group.add(self._destination_row)
        return group

    def _sync_destination_row(self):
        configured = self._settings.get_string("destination-directory")
        if configured:
            self._destination_row.set_subtitle(configured)
        else:
            self._destination_row.set_subtitle(
                f"Not set \u2014 using {default_destination()}"
            )

    def _on_choose_destination(self, _button):
        dialog = Gtk.FileDialog(title="Choose where transcripts are saved")

        def chosen(file_dialog, result):
            try:
                folder = file_dialog.select_folder_finish(result)
            except GLib.Error:
                return          # dismissed is not a failure
            path = folder.get_path()
            if path:
                self._settings.set_string("destination-directory", path)
                self._sync_destination_row()

        dialog.select_folder(self.get_root(), None, chosen)

    def _build_subtitle_group(self):
        group = Adw.PreferencesGroup(
            title="Subtitles",
            description=(
                "Only affects SRT and VTT. The server builds every other format "
                "with a function that ignores all three of these."
            ),
        )

        no_timestamps = Adw.SwitchRow(title="Omit timestamps")
        self._settings.bind(
            "no-timestamps", no_timestamps, "active", Gio.SettingsBindFlags.DEFAULT
        )
        group.add(no_timestamps)

        max_len = Adw.SpinRow.new_with_range(0, 1000, 1)
        max_len.set_title("Maximum segment length")
        max_len.set_subtitle("Characters. Zero means no limit.")
        max_len.set_value(self._settings.get_int("max-len"))
        # Not bound: SpinRow's value is a double and the key is an integer, so
        # g_settings_bind has no matching type mapping to apply.
        max_len.connect(
            "notify::value",
            lambda row, _p: self._settings.set_int("max-len", int(row.get_value())),
        )
        group.add(max_len)

        split_on_word = Adw.SwitchRow(
            title="Split on word boundaries",
            subtitle="Only applies when a maximum segment length is set.",
        )
        self._settings.bind(
            "split-on-word", split_on_word, "active", Gio.SettingsBindFlags.DEFAULT
        )
        group.add(split_on_word)

        return group

    def _build_integration_group(self):
        """Tells the user the right-click exists, and what governs it.

        Nothing here is a setting. The service menu has no configuration of its
        own -- it reads the values above at runtime -- so this is a status row
        rather than a switch, and there is nothing for it to link to.

        Presence is tested by looking for the helper on PATH rather than for the
        .desktop file, because the helper is what actually does the work. Under
        Flatpak it will not be found, the host binary being outside the sandbox,
        and saying so plainly beats showing nothing.

        An affordance only the author knows about is not a feature -- the same
        lesson drag and drop taught in Phase 2.
        """
        group = Adw.PreferencesGroup(
            title="File manager integration",
            description="Transcribing straight from a file manager, without opening Shoki.",
        )

        installed = shutil.which("shoki-transcribe") is not None

        if installed:
            subtitle = (
                "Right-click an audio or video file and choose Send to Whisper. It uses "
                "the endpoint, destination and output format set above."
            )
        else:
            # Deliberately not "you are sandboxed": the helper is equally absent
            # when running from a source checkout, and a message that guesses
            # wrong about why is worse than one that only reports what it knows.
            subtitle = (
                "Not detected. The helper ships with Shoki's native package. A standalone "
                "version, for use alongside a Flatpak install, is on the project page."
            )

        row = Adw.ActionRow(
            title="Right-click transcription",
            subtitle=subtitle,
            subtitle_lines=0,
        )

        if not installed:
            # GtkLinkButton rather than GtkUriLauncher: the launcher is async and
            # needs a callback, a finish call, and a live reference kept for the
            # duration -- three things to get wrong for one hyperlink.
            link = Gtk.LinkButton(
                uri=PROJECT_URL,
                label="Get it",
                valign=Gtk.Align.CENTER,
            )
            link.update_property(
                [Gtk.AccessibleProperty.LABEL],
                ["Open the Shoki project page"],
            )
            row.add_suffix(link)

        group.add(row)

        return group

    def _build_appearance_group(self):
        group = Adw.PreferencesGroup(title="Appearance")

        row = Adw.ComboRow(
            title="Style",
            model=Gtk.StringList.new(["Follow system", "Light", "Dark"]),
        )
        self._bind_combo(
            row, "color-scheme", tuple(COLOR_SCHEMES), on_change=self._apply_color_scheme
        )
        group.add(row)

        return group

    # ---- helpers ----------------------------------------------------------

    def _bind_combo(self, row, key, values, on_change=None):
        """Two-way sync between a ComboRow position and a string key.

        g_settings_bind cannot do this one: the row speaks in positions and the
        key speaks in names, and there is no documented mapping between them.
        """
        current = self._settings.get_string(key)
        row.set_selected(values.index(current) if current in values else 0)

        def changed(combo, _param):
            self._settings.set_string(key, values[combo.get_selected()])
            if on_change is not None:
                on_change()

        row.connect("notify::selected", changed)


class ShokiWindow(Adw.ApplicationWindow):
    """Source, options, the action, and the result -- one scrolling page."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title("Shoki")
        self.set_default_size(700, 820)

        self._session = Soup.Session()
        # A second session, so a liveness poll can never queue behind the
        # upload it is meant to be reporting on.
        self._health_session = Soup.Session()
        self._source_path = None      # a single chosen file
        self._folder_path = None      # or a chosen folder
        self._dropped_paths = []      # or files dropped on the window; only one of the three
        self._queue = []
        self._queue_total = 0
        self._queue_index = 0
        self._current_path = None
        self._batch_log = []
        self._run_cancelled = False
        self._consecutive_failures = 0
        self._cancellable = None
        self._started_at = None
        self._elapsed_source = None
        self._health_source = None
        self._health_pending = False
        self._destination = None      # session override; None means use settings

        self._settings = load_settings()
        if self._settings is None:
            print(
                f"shoki: GSettings schema {APP_ID} not found; "
                f"falling back to {DEFAULT_ENDPOINT}",
                file=sys.stderr,
            )

        self._apply_color_scheme()

        self._toasts = Adw.ToastOverlay()
        self.set_content(self._toasts)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(self._build_header_bar())
        self._toasts.set_child(toolbar)

        scroller = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        toolbar.set_content(scroller)

        clamp = Adw.Clamp(
            margin_top=24, margin_bottom=24, margin_start=12, margin_end=12
        )
        scroller.set_child(clamp)

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        clamp.set_child(page)

        # Vertical order settled 2026-08-13: the prompt sits last before the
        # action, because the jargon worth priming with is not known until the
        # file is chosen. Destination joins above Options once saving exists.
        page.append(self._build_source_group())
        page.append(self._build_destination_group())
        page.append(self._build_options_group())
        page.append(self._build_prompt_group())
        page.append(self._build_action_button())
        page.append(self._build_status_row())
        page.append(self._build_transcript_group())

        self._create_actions()
        self._sync_transcript_font()

        # Drop anywhere on the window, not just on the source row -- the roadmap
        # asks for the window, and a small target is a worse target.
        drop = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop.connect("drop", self._on_drop)
        self.add_controller(drop)

        # Preferences writes the default folder; this window shows it. Without
        # this the row goes stale until the next launch.
        if self._settings is not None:
            self._settings.connect(
                "changed::destination-directory", self._on_destination_setting_changed
            )

    # ---- settings ---------------------------------------------------------
    #
    # Settings hold DEFAULTS. The main window overrides them for the current
    # session and deliberately never writes back -- changing the format for one
    # job must not silently redefine what every future job starts as.

    def _setting_str(self, key, fallback):
        if self._settings is not None:
            return self._settings.get_string(key)
        return fallback

    def _setting_bool(self, key, fallback=False):
        if self._settings is not None:
            return self._settings.get_boolean(key)
        return fallback

    def _setting_int(self, key, fallback=0):
        if self._settings is not None:
            return self._settings.get_int(key)
        return fallback

    def _endpoint(self) -> str:
        """Where to POST. GSettings when available, shipped default otherwise."""
        return self._setting_str("endpoint-url", DEFAULT_ENDPOINT)

    def _apply_color_scheme(self):
        """AdwStyleManager is global, so this is set once from wherever we are."""
        name = self._setting_str("color-scheme", "default")
        scheme = COLOR_SCHEMES.get(name, Adw.ColorScheme.DEFAULT)
        Adw.StyleManager.get_default().set_color_scheme(scheme)

    def _create_actions(self):
        """Every shortcut drives an action, not a widget.

        Actions carry an enabled state, so Escape does nothing when no run is in
        flight and Ctrl+S does nothing with an empty transcript -- and the menu
        greys out to match, for free.
        """
        self._actions = {}
        handlers = {
            "open-file": self._on_choose_clicked,
            "open-folder": self._on_choose_folder_clicked,
            "transcribe": self._on_transcribe_clicked,
            "cancel": self._on_cancel_clicked,
            "copy-transcript": self._on_copy_clicked,
            "save-transcript": self._on_save_clicked,
        }

        for name, handler in handlers.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect(
                "activate", lambda _a, _p, run=handler: run(None)
            )
            self.add_action(action)
            self._actions[name] = action

        self._sync_actions()

    def _sync_actions(self):
        """Keep the actions in step with the buttons they mirror."""
        if not hasattr(self, "_actions"):
            return
        enabled = {
            "open-file": self._source_row.get_sensitive(),
            "open-folder": self._source_row.get_sensitive(),
            "transcribe": self._transcribe_button.get_sensitive(),
            "cancel": self._status.get_visible()
            and self._cancel_button.get_sensitive(),
            "copy-transcript": self._copy_button.get_sensitive(),
            "save-transcript": self._save_button.get_sensitive(),
        }
        for name, value in enabled.items():
            self._actions[name].set_enabled(value)

    def show_preferences(self):
        """No schema means nothing to persist, so there is nothing to show."""
        if self._settings is None:
            self._toast("Settings need the GSettings schema, which is not installed.")
            return
        ShokiPreferences(self._settings, self._apply_color_scheme).present(self)

    # ---- construction -----------------------------------------------------

    def _build_header_bar(self):
        header = Adw.HeaderBar()

        menu = Gio.Menu()
        menu.append("Preferences", "app.preferences")
        menu.append("Keyboard Shortcuts", "app.shortcuts")
        menu.append("About Shoki", "app.about")
        menu.append("Quit", "app.quit")

        button = Gtk.MenuButton(
            icon_name="open-menu-symbolic",
            menu_model=menu,
            primary=True,          # gives it F10, the GNOME convention
            tooltip_text="Main Menu",
        )
        button.update_property([Gtk.AccessibleProperty.LABEL], ["Main menu"])
        header.pack_end(button)

        return header

    def _build_source_group(self):
        group = Adw.PreferencesGroup(title="Source")

        self._source_row = Adw.ActionRow(
            title="No file chosen",
            # The drop target is invisible otherwise. An affordance only the
            # author knows about is not a feature -- noted 2026-08-14 when drag
            # and drop turned out to work and be entirely undiscoverable.
            subtitle="Choose an audio or video file, a folder, "
                     "or drop them anywhere on this window",
        )
        folder_button = Gtk.Button(
            label="Choose Folder\u2026", valign=Gtk.Align.CENTER
        )
        folder_button.connect("clicked", self._on_choose_folder_clicked)
        self._source_row.add_suffix(folder_button)

        button = Gtk.Button(label="Choose File\u2026", valign=Gtk.Align.CENTER)
        button.connect("clicked", self._on_choose_clicked)
        self._source_row.add_suffix(button)
        self._source_row.set_activatable_widget(button)

        group.add(self._source_row)
        return group

    def _build_destination_group(self):
        group = Adw.PreferencesGroup(title="Destination")

        self._destination_row = Adw.ActionRow(title="Save transcripts to")

        button = Gtk.Button(label="Choose\u2026", valign=Gtk.Align.CENTER)
        button.connect("clicked", self._on_choose_destination)
        button.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Choose a destination folder for this session only"],
        )
        self._destination_row.add_suffix(button)
        self._destination_row.set_activatable_widget(button)

        group.add(self._destination_row)
        self._sync_destination_row()
        return group

    def _build_options_group(self):
        group = Adw.PreferencesGroup(title="Options")

        labels = Gtk.StringList.new([FORMAT_LABELS[f] for f in RESPONSE_FORMATS])
        self._format_row = Adw.ComboRow(
            title="Output format",
            model=labels,
            selected=self._default_format_index(),
        )
        self._format_row.connect("notify::selected", self._on_format_changed)
        group.add(self._format_row)

        self._translate_row = Adw.SwitchRow(
            title="Translate to English",
            subtitle="Whisper only translates into English. There is no other target.",
            active=False,
        )
        group.add(self._translate_row)

        return group

    def _build_prompt_group(self):
        group = Adw.PreferencesGroup(
            title="Initial prompt",
            description=(
                "Optional, and not an instruction \u2014 the model does not read this "
                "as a command. It is prior context: write words you expect to "
                "hear, and the model leans toward them. Names, jargon, or "
                "spellings. Roughly 224 tokens are used."
            ),
        )

        self._prompt_row = Adw.EntryRow(title="Words to expect")
        group.add(self._prompt_row)

        return group

    def _build_action_button(self):
        self._transcribe_button = Gtk.Button(
            label="Transcribe", halign=Gtk.Align.CENTER, sensitive=False
        )
        self._transcribe_button.add_css_class("suggested-action")
        self._transcribe_button.add_css_class("pill")
        self._transcribe_button.connect("clicked", self._on_transcribe_clicked)
        return self._transcribe_button

    def _build_status_row(self):
        """Only what is actually known: time spent, and whether the server answers."""
        self._status = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=12,
            halign=Gtk.Align.CENTER,
            visible=False,
            # STATUS is a polite live region, so a screen reader announces the
            # counter and liveness changing instead of the user having to go
            # looking for them.
            accessible_role=Gtk.AccessibleRole.STATUS,
        )

        spinner = Adw.Spinner()
        spinner.set_size_request(20, 20)
        self._status.append(spinner)

        self._elapsed_label = Gtk.Label(label="Transcribing\u2026 0:00")
        self._status.append(self._elapsed_label)

        # Files, not audio. The roadmap is explicit that this bar must never
        # imply knowledge of how far through a recording the model is.
        self._progress = Gtk.ProgressBar(valign=Gtk.Align.CENTER, visible=False)
        self._progress.set_size_request(120, -1)
        self._progress.update_property(
            [Gtk.AccessibleProperty.LABEL], ["Files completed in this batch"]
        )
        self._status.append(self._progress)

        self._liveness_label = Gtk.Label()
        self._liveness_label.add_css_class("dim-label")
        # Phase 1 proved /health answers during an inference. It does NOT prove
        # the inference is progressing -- /health returns a static OK and knows
        # nothing about the model. The tooltip says so rather than letting the
        # label imply otherwise.
        self._liveness_label.set_tooltip_text(
            "Whether the server answers on a second connection. It cannot "
            "detect an inference that has stalled on a healthy server."
        )
        self._status.append(self._liveness_label)

        self._cancel_button = Gtk.Button(label="Cancel")
        self._cancel_button.add_css_class("destructive-action")
        self._cancel_button.connect("clicked", self._on_cancel_clicked)
        self._status.append(self._cancel_button)

        return self._status

    def _build_transcript_group(self):
        group = Adw.PreferencesGroup(title="Transcript")

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self._copy_button = Gtk.Button(label="Copy", sensitive=False)
        self._copy_button.connect("clicked", self._on_copy_clicked)
        self._copy_button.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Copy the transcript to the clipboard"],
        )
        actions.append(self._copy_button)

        self._save_button = Gtk.Button(label="Save", sensitive=False)
        self._save_button.connect("clicked", self._on_save_clicked)
        self._save_button.update_property(
            [Gtk.AccessibleProperty.DESCRIPTION],
            ["Save the transcript to the destination folder"],
        )
        actions.append(self._save_button)

        group.set_header_suffix(actions)

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

    # ---- options ----------------------------------------------------------

    def _default_format_index(self) -> int:
        """Where the picker starts, from settings, guarded against nonsense."""
        wanted = self._setting_str("response-format", DEFAULT_RESPONSE_FORMAT)
        if wanted not in RESPONSE_FORMATS:
            wanted = DEFAULT_RESPONSE_FORMAT
        return RESPONSE_FORMATS.index(wanted)

    def _selected_format(self) -> str:
        return RESPONSE_FORMATS[self._format_row.get_selected()]

    def _on_format_changed(self, _row, _param):
        self._sync_transcript_font()

    def _sync_transcript_font(self):
        """Prose reads better proportional; subtitles and JSON read better not.

        SRT cue numbering, VTT timing lines and JSON indentation all carry
        meaning in their alignment, which a proportional font destroys.
        """
        if self._selected_format() == "text":
            self._transcript.remove_css_class("monospace")
        else:
            self._transcript.add_css_class("monospace")

    def _request_params(self) -> dict:
        """Everything the UI contributes to one request.

        Fields are added deliberately, never blanket-sent: server.cpp reads each
        under `if (req.has_file(name))`, so an omitted field takes the server's
        own default rather than ours.
        """
        response_format = self._selected_format()

        params = {
            "response_format": response_format,
            "translate": self._translate_row.get_active(),
        }

        prompt = self._prompt_row.get_text().strip()
        if prompt:
            params["prompt"] = prompt

        if response_format in SUBTITLE_FORMATS:
            params["no_timestamps"] = self._setting_bool("no-timestamps")
            params["split_on_word"] = self._setting_bool("split-on-word")
            params["max_len"] = self._setting_int("max-len")

        return params

    # ---- progress, liveness, cancel ---------------------------------------

    def _start_indicators(self):
        self._started_at = GLib.get_monotonic_time()
        self._liveness_label.set_text("Checking server\u2026")
        self._cancel_button.set_sensitive(True)

        self._on_tick()                 # show 0:00 now, not in a second
        self._elapsed_source = GLib.timeout_add_seconds(1, self._on_tick)
        self._health_source = GLib.timeout_add_seconds(
            HEALTH_INTERVAL_SECONDS, self._on_health_tick
        )
        self._on_health_tick()

    def _stop_indicators(self):
        for attribute in ("_elapsed_source", "_health_source"):
            source = getattr(self, attribute)
            if source is not None:
                GLib.Source.remove(source)
                setattr(self, attribute, None)
        self._health_pending = False

    def _on_tick(self):
        seconds = int((GLib.get_monotonic_time() - self._started_at) // 1_000_000)
        self._elapsed_label.set_text(
            f"Transcribing\u2026 {seconds // 60}:{seconds % 60:02d}"
        )
        return GLib.SOURCE_CONTINUE

    def _on_health_tick(self):
        # Skip rather than pile up. A poll still outstanding is itself the
        # answer to the question the next one would ask.
        if self._health_pending:
            return GLib.SOURCE_CONTINUE

        url = health_url(self._endpoint())
        if url is None:
            self._liveness_label.set_text("Cannot check this endpoint")
            return GLib.SOURCE_CONTINUE

        message = Soup.Message.new("GET", url)
        if message is None:
            self._liveness_label.set_text("Cannot check this endpoint")
            return GLib.SOURCE_CONTINUE

        self._health_pending = True
        self._health_session.send_and_read_async(
            message, GLib.PRIORITY_LOW, None, self._on_health_reply, message
        )
        return GLib.SOURCE_CONTINUE

    def _on_health_reply(self, session, result, message):
        self._health_pending = False

        try:
            session.send_and_read_finish(result)
        except GLib.Error:
            self._liveness_label.set_text("Server not responding")
            return

        status = message.get_status()
        if status == Soup.Status.OK:
            self._liveness_label.set_text("Server responding")
        else:
            self._liveness_label.set_text(f"Server replied {int(status)}")

    def _on_cancel_clicked(self, _button):
        # Two separate effects: abort the request in flight, and make sure the
        # queue does not start another. The second is what makes cancelling a
        # batch worth doing.
        self._run_cancelled = True
        if self._cancellable is not None:
            self._cancellable.cancel()
        self._cancel_button.set_sensitive(False)
        self._sync_actions()
        self._elapsed_label.set_text("Cancelling\u2026")

    # ---- destination ------------------------------------------------------

    def _destination_path(self) -> str:
        """Session override, then the saved default, then the XDG fallback."""
        if self._destination is not None:
            return self._destination
        return self._setting_str("destination-directory", "") or default_destination()

    def _on_destination_setting_changed(self, _settings, _key):
        # A session override outranks the default, so leave it alone.
        if self._destination is None:
            self._sync_destination_row()

    def _sync_destination_row(self):
        path = self._destination_path()
        if self._destination is not None:
            self._destination_row.set_subtitle(f"{path}  (this session only)")
        else:
            self._destination_row.set_subtitle(path)

    def _on_choose_destination(self, _button):
        dialog = Gtk.FileDialog(title="Choose where to save this transcript")

        current = self._destination_path()
        if os.path.isdir(current):
            dialog.set_initial_folder(Gio.File.new_for_path(current))

        dialog.select_folder(self, None, self._on_destination_chosen)

    def _on_destination_chosen(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error as exc:
            if exc.code != Gtk.DialogError.DISMISSED:
                self._toast(f"Could not use that folder: {exc.message}")
            return

        path = folder.get_path()
        if path is None:
            self._toast("That folder is not on the local filesystem.")
            return

        # Deliberately does NOT write to settings. The main window overrides for
        # the current session; Preferences is where the default is changed.
        self._destination = path
        self._sync_destination_row()

    # ---- copy and save ----------------------------------------------------

    def _transcript_text(self) -> str:
        buffer = self._transcript.get_buffer()
        return buffer.get_text(
            buffer.get_start_iter(), buffer.get_end_iter(), False
        )

    def _save_text(self, text: str, source_path) -> str:
        """Write one transcript to the destination. Returns the path written.

        Raises OSError; both callers want to report the failure their own way.
        """
        directory = self._destination_path()
        stem = (
            os.path.splitext(os.path.basename(source_path))[0]
            if source_path
            else "transcript"
        )
        suffix = FILE_SUFFIXES[self._selected_format()]

        os.makedirs(directory, exist_ok=True)
        path, handle = open_unique(directory, stem, suffix)
        with handle:
            handle.write(text if text.endswith("\n") else text + "\n")
        return path

    def _on_copy_clicked(self, _button):
        text = self._transcript_text()
        if not text:
            return
        # gdk_clipboard_set_text() exists in C but is not exposed through
        # introspection, so PyGObject has no Clipboard.set_text -- confirmed the
        # hard way on Wayland, 2026-08-13. Handing the clipboard an explicit
        # content provider is the route that survives the binding: a MIME type,
        # and the bytes to serve for it.
        provider = Gdk.ContentProvider.new_for_bytes(
            "text/plain;charset=utf-8", GLib.Bytes.new(text.encode("utf-8"))
        )
        self.get_clipboard().set_content(provider)
        self._toast("Transcript copied to the clipboard.")

    def _on_save_clicked(self, _button):
        text = self._transcript_text()
        if not text:
            return

        try:
            path = self._save_text(text, self._current_path or self._source_path)
        except OSError as exc:
            self._toast(f"Could not save: {exc.strerror or exc}")
            return

        self._toast(f"Saved as {os.path.basename(path)}")

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

    def _clear_source(self):
        self._source_path = None
        self._folder_path = None
        self._dropped_paths = []

    def _accept_file(self, path):
        self._clear_source()
        self._source_path = path
        self._source_row.set_title(os.path.basename(path))
        self._source_row.set_subtitle(os.path.dirname(path))
        self._transcribe_button.set_sensitive(True)
        self._sync_actions()

    def _accept_folder(self, path) -> bool:
        try:
            found = media_files_in(path)
        except OSError as exc:
            self._toast(f"Could not read that folder: {exc.strerror or exc}")
            return False

        if not found:
            self._toast("No audio or video files in that folder.")
            return False

        self._clear_source()
        self._folder_path = path
        self._source_row.set_title(os.path.basename(path) or path)
        plural = "" if len(found) == 1 else "s"
        self._source_row.set_subtitle(f"{len(found)} file{plural} \u2014 {path}")
        self._transcribe_button.set_sensitive(True)
        self._sync_actions()
        return True

    def _accept_dropped(self, paths):
        self._clear_source()
        self._dropped_paths = paths
        self._source_row.set_title(f"{len(paths)} dropped files")
        self._source_row.set_subtitle(os.path.dirname(paths[0]))
        self._transcribe_button.set_sensitive(True)
        self._sync_actions()

    # ---- drag and drop ----------------------------------------------------

    def _on_drop(self, _target, value, _x, _y):
        """A folder, a file, or several files. Anything else is refused.

        Returning False tells GTK the drop was not accepted, so the cursor shows
        a rejection rather than the drop being silently swallowed.
        """
        if self._queue:
            self._toast("Busy transcribing. Wait for this run to finish.")
            return False

        paths = [gfile.get_path() for gfile in value.get_files()]
        if not paths:
            return False

        if any(path is None for path in paths):
            self._toast("Dropped items must be on the local filesystem.")
            return False

        if len(paths) == 1 and os.path.isdir(paths[0]):
            return self._accept_folder(paths[0])

        media = [
            path
            for path in paths
            if os.path.isfile(path)
            and os.path.splitext(path)[1].lstrip(".").lower() in MEDIA_SUFFIXES
        ]

        if not media:
            self._toast("Nothing dropped that Shoki can transcribe.")
            return False

        skipped = len(paths) - len(media)
        if len(media) == 1:
            self._accept_file(media[0])
        else:
            self._accept_dropped(sorted(media))

        if skipped:
            plural = "" if skipped == 1 else "s"
            self._toast(f"Ignored {skipped} item{plural}.")
        return True

    def _on_choose_folder_clicked(self, _button):
        dialog = Gtk.FileDialog(title="Choose a folder to transcribe")
        dialog.select_folder(self, None, self._on_folder_chosen)

    def _on_folder_chosen(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error as exc:
            if exc.code != Gtk.DialogError.DISMISSED:
                self._toast(f"Could not open that folder: {exc.message}")
            return

        path = folder.get_path()
        if path is None:
            self._toast("That folder is not on the local filesystem.")
            return

        self._accept_folder(path)

    def _on_file_chosen(self, dialog, result):
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error as exc:
            # Closing the dialog raises DISMISSED. That is not a failure.
            if exc.code != Gtk.DialogError.DISMISSED:
                self._toast(f"Could not open that file: {exc.message}")
            return

        path = gfile.get_path()
        if path is None:
            self._toast("That file is not on the local filesystem.")
            return

        self._accept_file(path)

    # ---- transcribing -----------------------------------------------------

    def _on_transcribe_clicked(self, _button):
        # Before anything else. Starting a doomed run and reporting it forty
        # seconds later through a quiet status label is the worst of both.
        problem = endpoint_problem(self._endpoint())
        if problem is not None:
            self._toast(problem)
            return

        try:
            paths = self._pending_paths()
        except OSError as exc:
            self._toast(f"Could not read that folder: {exc.strerror or exc}")
            return

        if not paths:
            return

        self._queue = paths
        self._queue_total = len(paths)
        self._queue_index = 0
        self._batch_log = []
        self._run_cancelled = False
        self._consecutive_failures = 0

        self._set_busy(True)
        self._set_transcript("")
        self._progress.set_visible(self._is_batch())
        self._progress.set_fraction(0.0)

        self._start_next()

    def _is_batch(self) -> bool:
        return self._queue_total > 1

    def _pending_paths(self):
        """Whatever the current source resolves to. Exactly one kind is ever set.

        A folder is re-listed at Transcribe time rather than reused from
        selection, so a file added since is picked up and one deleted since does
        not fail the whole run.
        """
        if self._dropped_paths:
            return list(self._dropped_paths)
        if self._folder_path is not None:
            return media_files_in(self._folder_path)
        if self._source_path is not None:
            return [self._source_path]
        return []

    def _start_next(self):
        if self._run_cancelled or not self._queue:
            self._finish_run()
            return

        self._current_path = self._queue.pop(0)
        self._queue_index += 1

        # Elapsed time restarts per file. A running total across a twelve-file
        # batch answers a question nobody asked; how long THIS file is taking is
        # the thing worth knowing.
        self._started_at = GLib.get_monotonic_time()
        self._on_tick()

        self._cancellable = Gio.Cancellable()
        transcribe_async(
            self._session,
            self._endpoint(),
            self._current_path,
            self._request_params(),
            self._cancellable,
            self._on_transcription_done,
        )

    def _finish_run(self):
        was_batch = self._is_batch()

        self._set_busy(False)
        self._progress.set_visible(False)
        self._cancellable = None
        self._current_path = None

        if was_batch:
            self._set_transcript("\n".join(self._batch_log))
            saved = sum(1 for line in self._batch_log if "\u2192" in line)
            if not self._run_cancelled:
                verb = "Finished"
            elif self._consecutive_failures >= 3:
                verb = "Batch stopped"
            else:
                verb = "Batch cancelled"
            self._toast(f"{verb}. {saved} of {self._queue_total} saved.")

    def _on_transcription_done(self, transcript, error):
        if self._is_batch():
            self._on_batch_item_done(transcript, error)
            return

        self._set_busy(False)
        self._cancellable = None

        if isinstance(error, TranscriptionCancelled):
            # The server really does stop. server.cpp sets abort_callback to
            # httplib is_connection_closed(), so closing the socket aborts the
            # inference -- verified 2026-08-14 by watching GPU utilisation fall
            # and "client disconnected, aborted processing" appear in the log.
            # An earlier version of this toast claimed the opposite.
            self._toast("Cancelled \u2014 the server stopped too.")
            return

        if error is not None:
            self._toast(str(error))
            return

        self._set_transcript(transcript)

    def _on_batch_item_done(self, transcript, error):
        """One file finished. Record what happened, then move the queue on.

        A batch saves as it goes. Holding results until the end would mean each
        transcript overwriting the last in the view, and eleven of twelve lost.
        """
        name = os.path.basename(self._current_path)

        if isinstance(error, TranscriptionCancelled):
            self._batch_log.append(f"{name} \u2014 cancelled")
        elif error is not None:
            self._batch_log.append(f"{name} \u2014 failed: {error}")
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = 0
            try:
                saved = self._save_text(transcript, self._current_path)
            except OSError as exc:
                self._batch_log.append(
                    f"{name} \u2014 transcribed but not saved: {exc.strerror or exc}"
                )
            else:
                self._batch_log.append(f"{name} \u2192 {os.path.basename(saved)}")

        # Three failures in a row is a broken server, not three broken files.
        # Grinding through the remaining nine to say so twelve times is not
        # error handling, it is making the user wait for bad news they have.
        if self._consecutive_failures >= 3 and self._queue:
            self._run_cancelled = True
            self._batch_log.append(
                f"Stopped after 3 failures in a row. "
                f"{len(self._queue)} file(s) not attempted."
            )

        self._set_transcript("\n".join(self._batch_log))
        self._progress.set_fraction(self._queue_index / self._queue_total)
        self._elapsed_label.set_text(
            f"File {self._queue_index} of {self._queue_total}"
        )

        self._start_next()

    # ---- small helpers ----------------------------------------------------

    def _set_busy(self, busy):
        self._transcribe_button.set_sensitive(not busy)
        self._transcribe_button.set_label(
            "Transcribing…" if busy else "Transcribe"
        )
        # Changing options mid-flight would describe a request that is no longer
        # the one in the air.
        self._format_row.set_sensitive(not busy)
        self._translate_row.set_sensitive(not busy)
        self._prompt_row.set_sensitive(not busy)
        self._destination_row.set_sensitive(not busy)
        self._source_row.set_sensitive(not busy)

        self._status.set_visible(busy)
        if busy:
            self._start_indicators()
        else:
            self._stop_indicators()

        self._sync_actions()

    def _set_transcript(self, text):
        self._transcript.get_buffer().set_text(text)
        # Nothing to copy or save until there is something in the view.
        self._copy_button.set_sensitive(bool(text))
        self._save_button.set_sensitive(bool(text))
        self._sync_actions()

    def _toast(self, message):
        self._toasts.add_toast(Adw.Toast(title=message, timeout=6))


class ShokiApplication(Adw.Application):
    """AdwApplication calls adw_init() in its default startup handler.

    do_startup IS overridden as of Phase 2, and chains up on its first line --
    the libadwaita docs require any subclass to do so before touching GTK or
    Adwaita API. Until there were actions to register there was nothing to put
    here, so it was left alone.
    """

    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_startup(self):
        Adw.Application.do_startup(self)

        for name, handler in (
            ("preferences", self._on_preferences),
            ("shortcuts", self._on_shortcuts),
            ("about", self._on_about),
            ("quit", self._on_quit),
        ):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", handler)
            self.add_action(action)

        for action_name, accelerator, _label in SHORTCUTS:
            self.set_accels_for_action(action_name, [accelerator])

    def _on_quit(self, _action, _param):
        self.quit()

    def _on_shortcuts(self, _action, _param):
        """Built from the same SHORTCUTS list that registers the accelerators.

        AdwShortcutsDialog rather than GtkShortcutsWindow: the latter is
        deprecated since GTK 4.18 and is removed in GTK 5.
        """
        dialog = Adw.ShortcutsDialog()
        section = Adw.ShortcutsSection(title="Shoki")

        for action_name, accelerator, label in SHORTCUTS:
            section.add(
                Adw.ShortcutsItem(
                    title=label,
                    accelerator=accelerator,
                    action_name=action_name,
                )
            )

        dialog.add(section)
        dialog.present(self.props.active_window)

    def _on_about(self, _action, _param):
        """AdwAboutDialog rather than AdwAboutWindow.

        The dialog form is the current one, and it matches AdwPreferencesDialog
        and AdwShortcutsDialog already in use here -- all three then present the
        same way, inside the window rather than as a separate toplevel.

        The version is read from shoki.__version__ rather than restated, so the
        About box cannot drift from the package.
        """
        dialog = Adw.AboutDialog(
            application_name="Shoki",
            application_icon=APP_ID,
            developer_name="Tony Farson",
            version=__version__,
            comments="A control surface for a whisper.cpp transcription server.",
            website=PROJECT_URL,
            issue_url=f"{PROJECT_URL}/issues",
            developers=["Tony Farson"],
            copyright="\u00a9 2026 Tony Farson",
            license_type=Gtk.License.MIT_X11,
        )
        dialog.present(self.props.active_window)

    def _on_preferences(self, _action, _param):
        window = self.props.active_window
        if window is not None:
            window.show_preferences()

    def do_activate(self):
        window = self.props.active_window
        if not window:
            window = ShokiWindow(application=self)
        window.present()


def main() -> int:
    return ShokiApplication().run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

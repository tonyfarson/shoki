---
type: roadmap
status: active
project: shoki
created: 2026-08-12
updated: 2026-08-14
---

# Shoki Roadmap

Shoki is a GTK4/libadwaita desktop application (Python) that provides a graphical control surface for
a whisper.cpp transcription server, and ships a Dolphin service menu that transcribes files by
right-click. This document tracks phased development from empty repo to (optionally) published
application.

Core principles:

- Simple, not overwhelming, easy to maintain
- Each phase has a clean stopping point where "we're done" is a valid answer
- No scope creep — new ideas go to `FUTURE.md`, not into the current phase

Testing backend: whisper.cpp server running on Otachi. See `README.md` for the setup this app
depends on, and `docs/SERVER.md` for what that server actually accepts.

---

## What Shoki Is

Decided during Phase 0.5 on 2026-08-13, after the original premise was challenged and nearly
abandoned.

Shoki is not a GUI wrapper around one curl call. That version of the idea does not survive scrutiny:
a right-click service menu already transcribes files in one step, and a web page served by the
container itself would beat a desktop window on almost every axis.

What Shoki is instead:

1. A control surface for an API far richer than its documentation suggests — roughly thirty request
   parameters, five output formats, translation, and diarization. No client for it exists.
2. A file-manager verb — a Dolphin service menu that transcribes any audio or video file by
   right-click, without opening the application at all.

The two are deliberately decoupled. The service menu is a standalone script; it does not launch
Shoki. They share settings, not a process.

---

## Versioning

Shoki follows [Semantic Versioning](https://semver.org/). Per SemVer item 4, major version zero is
for initial development and nothing about the interface is promised.

- `0.1.0` — first fully-featured working copy. Runs on Otachi, used daily by its author, nothing
  promised to anyone else.
- `1.0.0` — a stranger can install it, and configuration stability becomes a commitment.

Scope sorting rule: does this need to work before *the author* uses it daily, or before *someone
else* does?

---

## The Server

Shoki talks to a whisper.cpp server it does not manage. What that server accepts, what it returns,
and the behaviour that constrains Shoki's design are documented in **`docs/SERVER.md`** — moved out
of this file on 2026-08-14, because reference material about an external dependency is not a
roadmap.

---

## Phase 0 — Scaffolding

Goal: prove the toolchain works and a git repo exists.

Progress checklist:

- [x] Directory skeleton created (2026-08-13)
- [x] `.gitignore`, `LICENSE`, `README.md`, `FUTURE.md` written (2026-08-13)
- [x] CachyOS prerequisites verified installed (2026-08-13)
- [x] Hello-world window runs (2026-08-13)
- [x] `git init` + GitHub repo + `origin` remote (2026-08-13)
- [x] First commit pushed (2026-08-13)

Verified toolchain (2026-08-13): python 3.14.6-2, python-gobject 3.56.3-1, gtk4 1:4.22.4-1.1,
libadwaita 1:1.9.3-1.1, flatpak 1:1.18.0-1.1, flatpak-builder 1.4.10-1.1. PyGObject imports Gtk 4.0
and Adw 1 cleanly on Python 3.14 — this was an open risk and is now closed.

Two startup warnings are expected and are not Shoki bugs:

```
Adwaita-WARNING **: Using GtkSettings:gtk-application-prefer-dark-theme with
libadwaita is unsupported. Please use AdwStyleManager:color-scheme instead.
```

Emitted because the desktop environment sets the GTK dark-theme preference globally. Shoki never
touches `GtkSettings`.

```
WARNING: radv is not a conformant Vulkan implementation, testing use only.
```

Standard Mesa RADV boilerplate, printed as GTK4 initialises its renderer. Unrelated to the
whisper.cpp Vulkan backend and unrelated to Shoki.

Status: ✅ Complete — 2026-08-13

---

## Phase 0.5 — Scoping Session

Goal: re-validate Phases 1 through 5 against findings made after this roadmap was written. No code
produced.

Decisions reached:

1. Product identity settled — see What Shoki Is. The premise was challenged directly and survived in
   a changed form.
2. Versioning adopted — SemVer 0.x, `0.1.0` as the first working copy.
3. Server behaviour verified and documented. This closed the language question, which earlier
   documentation had wrongly deferred as possibly unimplementable.
4. Endpoint decided — ships pre-filled with `http://127.0.0.1:8080/inference`.
5. Interface direction decided — a single vertically-scrolling page, not a wizard. See Interface
   Direction below.
6. Control placement decided — see Interface Direction below.
7. Progress, liveness, and cancel all pulled into v0.1.0, with honest limits recorded.
8. Packaging resolved — both native and Flatpak ship, because the Dolphin integration was decoupled
   from the application. See Phase 3.
9. Output destination and filename-collision rules decided — see Phase 2.
10. `Adw.PreferencesDialog` verified against current libadwaita documentation: available since 1.5,
    with `Adw.PreferencesWindow` carrying "deprecated: 1.6 — Use AdwPreferencesDialog."
11. Tray icon, autostart, and any resident background process ruled out. `GtkStatusIcon` was removed
    in GTK4 with no successor; a tray icon requires implementing freedesktop StatusNotifierItem over
    D-Bus or depending on libayatana-appindicator. Moot in any case now that the service menu does
    not launch Shoki.
12. Accessibility is a build standard, not a settings pane. Accessible roles, real labels, full
    keyboard navigation, and respect for system contrast and text-size settings are v0 requirements.
13. Public distribution deferred with written criteria rather than decided — later taken on
    2026-08-14. See Phase 6.

Stopping condition met: Phases 1 and 2 are rewritten and free of unverified claims. Remaining
assumptions are labelled as assumptions.

Status: ✅ Complete — 2026-08-13

---

## Interface Direction

Decided 2026-08-13. The stated goal is clean, simple, and intuitive — explicitly not an early-2000s
dialog with a thousand options.

Shoki is a **single vertically-scrolling page**, not a stepped wizard.

A wizard was considered, drawing on Fedora Media Writer and Audimorf. It was rejected because a transcript is a document you read, scroll, copy, save, and re-run with a tweaked prompt — not a task that ends in a completion screen. Splitting settings and results across screens makes the
tweak-and-retry loop walk backwards through the flow.

Vertical scrolling keeps the guided reading order — source at the top, then options, then the action,
then the result — while letting every part coexist and stay reachable. It is also the native
libadwaita idiom.

> **Note:** `Adw.Carousel` implements `GtkOrientable` and does support vertical orientation, so a
> literal sliding version remains possible if the scrolling page ever proves wrong.

Control placement:

| Control | Location |
|---|---|
| Source picker (also the drag-and-drop target) | Main window |
| Destination directory | Main window |
| Output format | Main window |
| Translate to English | Main window |
| Initial prompt | Main window |
| Transcribe | Main window |
| Transcript view, with Copy and Save | Main window |
| Whisper server URL | Settings |
| Default destination directory | Settings |
| Default output format | Settings |
| Interface look and feel | Settings |
| Dolphin integration behaviour | Settings |
| `no_timestamps`, `split_on_word`, `max_len` | Settings |

Settings holds defaults; the main window overrides them for the current session. The three subtitle
controls only affect `srt` and `vtt` output.

> **Resolved 2026-08-13:** the initial prompt sits below the options and directly above Transcribe.
> Order is Source → Destination → Output format and Translate → Initial prompt → Transcribe →
> Transcript. It is the last thing touched before starting a job, which matches how it is used: the
> jargon worth priming with is not known until the file has been chosen.

---

## Phase 1 — Walking Skeleton

Goal: the thinnest end-to-end path that touches every layer, running for real. Everything in Phase 2
hangs off this. The purpose is to discover what is actually hard — PyGObject idioms, multipart
upload, threading, error paths — while there is almost nothing to unpick.

Deliverables:

- Main window: file selection area, a Transcribe button, and a scrollable read-only output area
- File picker using `Gtk.FileDialog`, filtered to common audio and video MIME types
- A single request function that takes a **dict of parameters**, performs the multipart POST, and
  returns text. Fields are never built inline in a button handler.
- Endpoint configurable, not hardcoded, defaulting to `http://127.0.0.1:8080/inference`. The
  configurable endpoint is load-bearing, not polish — every user's path differs.
- Requests send `response_format=json` and parse the transcript out of it. `json` is the format most
  likely to be portable to other backends; `text` is not universally confirmed.
- Requests send `language=auto`.
- Transcript displays on success; a plain `Adw.Toast` or dialog on failure
- Blocking UI during transcription is acceptable here. Threading arrives in Phase 2.

Two choices to make deliberately during Phase 1, because reversing them later is expensive:

- **HTTP library must be able to report body-upload progress.** The upload percentage in Phase 2
  depends on it. Choosing a library that cannot do this makes that feature a rewrite rather than an
  addition.
- **GSettings keys are named neutrally** — `endpoint-url` not `whisper-url`, `response-format` not
  `format`. Adding keys later is easy; renaming them is a migration.

One test belongs in this phase, deferred from Phase 0.5 as a labelled assumption:

- [x] Does `GET /health` still answer while an inference is in flight? **Yes** — verified
      2026-08-13. Twenty-four consecutive polls at one-second intervals during an outstanding POST,
      every one HTTP 200 in 0.0004–0.0008 s, against a job that took 46.6 s in total. No queueing,
      no degradation.

> **Note:** This proves the HTTP server is still *serving*. It does not prove the inference is
> *progressing* — `/health` returns a static OK and knows nothing about the model. The Phase 2
> indicator can honestly distinguish "alive and reachable" from "dead, wedged, or unreachable"; it
> cannot detect a stalled inference on a live server. Word the interface to match what it knows.

Decided during Phase 1:

- **HTTP library — libsoup 3**, over `requests` plus `requests-toolbelt`. The deciding argument was
  not upload progress but threads. GNOME's threading tutorial states that "the default approach
  should be to never use threads", directing callers to asynchronous operations on the GLib main
  context instead. libsoup is async-native, so Shoki has no worker threads at all. It also adds no
  Python dependency, which matters across four packaging formats in Phases 3 and 4, and its
  `send_and_read_async` takes a `GCancellable` — making Phase 2's cancel a documented parameter
  rather than an invention.
- **`Soup.Multipart.to_message()` writes Content-Type including the multipart boundary.** The body is
  then attached with `set_request_body_from_bytes(None, body)`, and that `None` is load-bearing:
  passing a content-type string overwrites the boundary and the server cannot parse the request.
- **A missing GSettings schema must not be fatal.** `g_settings_new()` treats an absent schema as a
  programmer error and takes the process down, so Shoki looks the schema up through
  `Gio.SettingsSchemaSource` first and falls back to the shipped default with a message on stderr.
  Same rule the Dolphin service menu follows in Phase 3.

Stopping condition: an audio file picked in the app produces a correct transcript in the output area,
against the Otachi server.

Met 2026-08-13. An mp3 chosen through `Gtk.FileDialog` transcribed correctly against the Otachi
server, the window stayed responsive and draggable throughout, and the endpoint came from GSettings
rather than from anything hardcoded. The shipped `/inference` default returned 404 first, exactly as
intended — the configuration path was exercised on day one instead of shipped untested.

Explicitly not in Phase 1: save, copy, settings, batch, drag and drop, translation, format choice,
progress, threading, keyboard shortcuts, Dolphin integration, styling beyond default libadwaita.

Status: ✅ Complete — 2026-08-13

---

## Phase 2 — Feature Complete (v0.1.0)

Goal: the first fully-featured working copy. Used daily by its author. Nothing promised to anyone
else.

Deliverables:

- [x] Asynchronous requests — transcription runs on the GLib main context and the UI stays
      responsive. Already true as of Phase 1; this line now means keeping it true as features are
      added. Renamed from "Threading" on 2026-08-13, because libsoup is async-native and GNOME's own
      guidance is to reach for threads last rather than first. (2026-08-13)
- [x] Output format picker — `text` (default), `srt`, `vtt`, `json`, `verbose_json` (2026-08-13)
- [x] Translate to English — a checkbox (2026-08-13)
- [x] Initial prompt field — a large accuracy win for proper nouns and jargon (2026-08-13)
- [x] Subtitle tuning in settings — `no_timestamps`, `split_on_word`, `max_len` (2026-08-13).
      `max_len`'s effect on cue length is wired and sent but not yet observed against the server.
- [x] Batch a directory — client-side loop, one POST per file, sequential. No server support
      required. A batch saves each transcript to the destination as it completes and shows a
      running log; holding results until the end would mean each overwriting the last in the
      view. (2026-08-14)
- [x] Save output to a chosen directory; copy to clipboard (2026-08-13)
- [x] Drag and drop onto the window (`Gtk.DropTarget`) — accepts a folder, one file, or several
      files at once. Several files is a source kind neither dialog can produce: an ad-hoc batch
      drawn from different folders. Non-media items are filtered out and reported rather than
      silently dropped. (2026-08-14)
- [x] Settings via `Adw.PreferencesDialog`, persisted with `GSettings` (2026-08-13)
- [x] Error handling — clear user-facing messages for unreachable server, non-2xx responses,
      unreadable files. No stack traces in the UI. Verified 2026-08-14 by deliberately breaking
      each path; nothing reached the console. (2026-08-14)

      Three defects this found. `str(OSError)` was reaching toasts as
      `[Errno 13] Permission denied: '/path/x.mp3'` — an errno and a repr'd path. Non-2xx replies
      discarded the server's own explanation, which a 404 puts in the body. And an unreachable
      endpoint was reported only by a quiet status label while the spinner and timer ran, so a
      doomed job looked like a working one — endpoints are now validated *before* a run starts.

      `Soup.Message.new()` accepts far more than it can reach: `nonsense` yields a valid message
      whose request never completes, and `localhost:8080` parses as scheme `localhost` with path
      `8080`. Neither can be caught after the fact, which is why the guard is ours and runs first.
      Corollary for the interface: a failure to START is an event and gets a toast; liveness is a
      status that can flip back, and gets a label.
- [x] Keyboard shortcuts and full keyboard navigation (2026-08-14). Every shortcut drives a
      `Gio.SimpleAction` rather than poking a widget, so each carries an enabled state — Escape does
      nothing when idle, Ctrl+S nothing with an empty transcript, and the menu greys to match for
      free. The shortcuts dialog is generated from the same list that registers the accelerators, so
      the two cannot drift. Uses `Adw.ShortcutsDialog` (libadwaita 1.8+): `Gtk.ShortcutsWindow` is
      deprecated since GTK 4.18 and is removed in GTK 5.
- [x] Accessible roles and labels on every interactive widget (2026-08-14). The status row is a
      `STATUS` live region so the file counter and liveness are announced rather than having to be
      hunted for; the progress bar, the menu button, the transcript view, and the Copy, Save and
      Choose buttons all carry labels or descriptions beyond their visible text. Keyboard
      reachability confirmed by tabbing the whole window, including Copy and Save, which sit in a
      group header suffix rather than the normal content flow.

      The drop target is now discoverable — the Source row reads "Choose an audio or video file, a
      folder, or drop them anywhere on this window". Noted 2026-08-14 when drag and drop turned out
      to work and be completely invisible. An affordance only the author knows about is not a
      feature.

      > **Not audited, only implemented.** No screen reader has been run against Shoki and no
      > contrast check has been done. Roles and labels being present is not the same as the result
      > being usable with assistive technology. A real pass belongs in Phase 5 alongside the
      > screenshots.

Progress and liveness — three honest indicators, no invented percentages:

- [x] Spinner plus an **elapsed-time counter**. A real number beats a bar creeping toward a
      fabricated 100%. The counter restarts per file in a batch — a running total across twelve
      files answers a question nobody asked. (2026-08-14)
- [x] **Batch counter** — "file 3 of 12" is measurable and true. The progress bar exists; it
      measures files, not audio. (2026-08-14)
- [x] **Liveness via `GET /health`**, polled on a second connection during a job (2026-08-14).
      `/health` sits at the server root and does NOT move with `--inference-path`, so the URL is
      derived by keeping the endpoint's origin and replacing the path. Confirmed viable
      by the Phase 1 test. It distinguishes "server alive and reachable" from "server dead, wedged,
      or unreachable". It cannot see a stalled inference on a healthy server, so the interface must
      not claim to show that.

> **Deferred 2026-08-13, at the author's call: upload percentage.** Pointless against a server on
> localhost. The capability is retained rather than lost — `SoupMessage::wrote-body-data` reports
> bytes written, so this stays an addition rather than becoming a rewrite. It returns if Shoki is
> ever used from a second machine over the tailnet. See `FUTURE.md`.

Cancel:

- [x] Cancelling a single file closes the connection, which aborts the inference server-side.
      Verified 2026-08-14 — see `docs/SERVER.md`. The UI may say the server stops, because
      it does. (2026-08-14)
- [x] Cancelling a batch is genuinely effective — remaining files are never sent. Verified
      2026-08-14: cancelling during file 2 of 3 logged file 2 as cancelled and produced no log line
      at all for file 3, because no request was ever made for it. (2026-08-14)

Output destination and filenames:

- [x] One shared destination directory by default for both Shoki and the Dolphin service menu. All
      transcripts land in one place; the user decides what happens next. Both are customisable.
      (2026-08-13)
- [x] The shipped default resolves the XDG Documents directory plus a `Transcriptions` subfolder at
      runtime. `~/Nextcloud/Documents/Transcriptions/` is a personal setting, not a shipped default.
      (2026-08-13)
- [x] **Collision rule: append a numeric suffix after a hyphen** — `interview.txt`, then
      `interview-1.txt`. Never overwrite silently. Implemented with `O_CREAT|O_EXCL` rather than an
      existence check, so a second window or the Dolphin service menu cannot win a race for the
      name. (2026-08-13)

> **Resolved 2026-08-13: the hyphen wins.** Transcripts already on disk use it, so the folder stays
> consistent with its own history and nothing already saved looks out of place. The Dolphin helper
> script is rewritten and shipped fresh in Phase 3 anyway, so matching it costs nothing.

> **Note:** under Flatpak the destination is chosen once through the folder-chooser portal and the
> result stored, rather than declared as a static filesystem permission. That work belongs to
> Phase 4, not here.

> **Resolved 2026-08-13: reflow `text`, pass everything else through untouched.** The leading space
> turned out to be an instruction rather than noise. Whisper's tokenizer marks a word-initial token
> with a leading space, so a segment beginning *without* one continues the previous word — the
> newline landed mid-word. Stripping every line and joining on spaces produced `kings hip`,
> `eight-year- olds` and `our way ,`. The rule now: a line starting with whitespace is appended after
> a single space, one that is not is appended flush. `json` is NOT reflowed, deviating from the first
> answer given — it is now a user-selectable output format, so reflowing it would corrupt the
> document and make the menu entry redundant with `text`. Saved output and the on-screen view are
> identical in every format.

Language auto-detect is always on and has no control. A manual language override is deferred to the
advanced drawer — see `FUTURE.md`.

Build order, agreed 2026-08-13: **schema first, then UI.** Key names are the expensive-to-reverse
thing, per Phase 1's lesson, and Settings holds the defaults the main window overrides — so building
controls before those defaults exist means reworking them.

The deliverable lists above are the checklist — there is no second copy to drift out of step with
them. Work order so far: schema, then the response layer, then main-window controls, then the
preferences dialog, then destination and save and copy.

Settled during Phase 2:

- **Booleans are `"true"` / `"false"` on the wire.** `parse_str_to_bool()` in `server.cpp` accepts
  `true`, `1`, `yes` and `y`. This was the last unverified item carried out of Phase 1.
- **Omitting a form field sends the *server's* default, not Shoki's.** Every field is read under
  `if (req.has_file(name))`. `language` and `response_format` are therefore sent unconditionally on
  every request; the server would otherwise fall back to `en` and `json`.
- **Branch on the format requested, never on the reply's Content-Type.** The `text` branch labels
  itself `text/html; charset=utf-8`, which is neither true nor safe to act on.
- **Responses are decoded with replacement, not strictly.** Whisper's tokenizer works on bytes, so a
  token boundary can land mid-character and the server ships a truncated UTF-8 sequence. Observed on
  mixed English/Japanese audio. No client can repair it; failing the whole transcript over one bad
  byte would discard everything else.
- **`Gdk.Clipboard` has no `set_text` in PyGObject** — the C function is not exposed through
  introspection. Copy goes through `Gdk.ContentProvider.new_for_bytes()` and `set_content()`.
- **`do_startup` is now overridden**, chaining up on its first line as the libadwaita docs require.
  Phase 1 deliberately left it alone; it now registers the Preferences action and its accelerator.

Stopping condition: Shoki is used for a real transcription task and feels finished rather than
prototype-ish. Tag `v0.1.0`.

Explicitly not in Phase 2: packaging, model switching, system monitoring, the advanced-parameters
drawer, batch queue UI, alternative backends.

Status: 🚧 Feature-complete — all 20 deliverables ticked 2026-08-14. Not yet tagged `v0.1.0`:
the stopping condition is real daily use, not a full checklist.

---

## Phase 3 — Packaging and Desktop Integration

Goal: Shoki installs as a real application, and right-clicking an audio file transcribes it.

This phase ships **one package format on one desktop, end to end**: a pacman package and the
Dolphin service menu. Breadth — Flatpak, `.deb`, `.rpm`, and the other file managers — is Phase 4.
Doing one completely first is what surfaced the byte-identical-output problem and the four wrong
claims corrected below; a broader first pass would have found them later and in worse company.

The decoupling: the service menu is a **standalone script that never launches Shoki**. Right-click,
transcribe, done. Because the script is not sandboxed, the Flatpak never needs to read arbitrary
files handed to it by the file manager, and therefore never needs broad filesystem access.

### Build system — Meson

No deliverable below named this, and every one of them rests on it. Added 2026-08-14:
`meson.build`, `src/meson.build`, `src/shoki.in`, `data/meson.build`.

- **`meson_version: '>= 0.59.0'`, not the 1.12.0 that happens to be installed.** 0.59.0 is the real
  floor — `update_desktop_database` in `gnome.post_install()` is the highest requirement in use.
  Declaring the installed version would lock out the `.deb` and `.rpm` builders this phase
  anticipates; Ubuntu 24.04 LTS ships meson 1.3.2.
- **`project()` declares no language.** Shoki is pure Python; naming one would make Meson demand a C
  compiler in order to copy files.
- **Shoki installs to `pkgdatadir`, not `site-packages`** — `/usr/share/shoki/shoki/*.py` plus a
  generated `/usr/bin/shoki` that does `sys.path.insert(1, '@PKGDATADIR@')`. Inside a Flatpak the
  interpreter is the runtime's `/usr/bin/python3` while the app lives under `/app`, so
  `/app/lib/pythonX.Y/site-packages` is not on that interpreter's default path. One mechanism then
  works under `/usr`, under `/app`, and under a throwaway `--prefix`. The cost is that `import shoki`
  from a REPL does not work, which nobody wants from a GUI app.
- **Python modules are listed explicitly, never globbed.** Adding one is a deliberate edit, and
  `__pycache__` can never be installed by accident.
- **Validation runs as `meson test`**, so `makepkg`'s `check()` stops a build that would otherwise
  ship a malformed desktop file or schema.

> **`gnome.post_install()` scripts are skipped when `DESTDIR` is set.** A plain `meson install`
> prints "Compiling GSettings schemas"; `makepkg` prints "Skipping custom install script because
> DESTDIR is set". Both are correct — the package's own pacman hooks do the refresh on the target
> machine. Expect the difference rather than debugging it.

### Native package

- [x] Ship the application, the helper script, and the `.desktop` service menu (2026-08-14).
      `build-aux/PKGBUILD`, deliberately not at the repo root: `makepkg` creates `src/` and `pkg/`
      beside the PKGBUILD, and at the root that `src/` would collide with Shoki's own source
      directory. It builds the working tree via `$startdir/..`, which makes it a local package
      rather than an AUR-ready one — there is no `v0.1.0` tag yet, and the tag waits on real daily
      use rather than on a checklist.
- [x] Install the GSettings schema system-wide, so the script can read Shoki's settings directly with
      `gsettings get com.farsononline.shoki endpoint-url`. One settings dialog governs both, and they
      cannot drift. (2026-08-14)
- [x] Icon, pulled forward from Phase 5 (2026-08-14). Two SVGs, not a ladder of PNGs — see Phase 5.
- [x] About dialog, `Adw.AboutDialog`, with the repository and issue tracker (2026-08-14). Not on any
      deliverable list; added because a packaged application that cannot tell you where it came from
      is not finished. The version is read from `shoki.__version__` so it cannot drift.
- [x] A status row in Preferences reporting whether the right-click integration is present
      (2026-08-14). Not a setting — the service menu has no configuration of its own. Presence is
      tested with `shutil.which("shoki-transcribe")` rather than by looking for the `.desktop` file,
      because the helper is what does the work.

`.deb` and `.rpm` are not started and are not required by the stopping condition.

### Corrections to this section, made 2026-08-14

Three claims written here before anything was built turned out to be wrong. A fourth — that the
helper falling back to built-in defaults was "graceful degradation" — was about the Flatpak, and
moved to Phase 4 with the work it concerns.

> **The executable-bit rule is narrower than this document claimed.** It previously said flatly that
> the `.desktop` file must be executable. KDE's own documentation ties that to *unauthorised* user
> locations — a Get-Hot-New-Stuff install under `~/.local/share/`. `/usr/share/kio/servicemenus/` is
> system data and already authorised, so the packaged file is installed `0644` and works.

> **There is no per-user setup step, and there could not be one.** The expectation that installation
> would open some configuration for the user does not survive contact with pacman: a `post_install`
> scriptlet runs as root, non-interactively, with no session and no display. It cannot open a window,
> and it must not write into anyone's home directory. None of that matters, because a service menu in
> `/usr/share/kio/servicemenus/` is live for every user the moment the package lands.

> **There is no Dolphin configuration to link to from Preferences.** The service menu has no settings
> of its own; it reads Shoki's, so Shoki's Preferences *is* the configuration and a link would point
> at itself. The only other surface — Dolphin's enable/disable list — has no standalone settings
> module: `kcmshell6 --list` offers only `kcm_kded`, which is KDE's background daemons and unrelated.
> Verified on Otachi 2026-08-14.

### Rules for the file-manager integration

- **No sudo, ever.** Plasma 6 reads user service menus from `~/.local/share/kio/servicemenus/`, and
  system ones from `/usr/share/kio/servicemenus/`, which a package writes during its own privileged
  install.
- **Never download and execute.** Fetching a script at runtime and running it is remote code
  execution by design, breaks offline installs, and bypasses package verification. The files are
  tiny — bundle them.
- The script must always fall back to defaults if `gsettings` fails. A right-click that silently does
  nothing is the worst available failure mode. Every path through `shoki-transcribe` ends in a
  notification for the same reason.
- Settings meaningful to the right-click path: endpoint, destination, output format. Not the initial
  prompt, which is per-file and meaningless without someone to type it. **Not translate either** —
  there is no such GSettings key; it is a per-session switch in the main window. If the right-click
  ever needs it, a second `[Desktop Action]` is a better answer than a hidden setting.

### The helper script must match the application byte for byte

`data/shoki-transcribe` reads settings, POSTs, and saves — and its output has to be indistinguishable
from the application's, or the same audio saved two ways produces two different files and reads as
Shoki being broken rather than Shoki being different.

Three divergences were found and fixed on 2026-08-14, every one of them invisible on a
one-segment test file and glaring on a real recording:

1. `text` was not reflowed. `_reflow()` is ported to `awk` as `reflow_text()`.
2. `srt` and `vtt` did not get `strip("\n")`.
3. The file did not end with exactly one newline, which `main.py` guarantees.

Confirmed by transcribing a 31 MiB recording both ways and comparing: identical SHA-256, 25,020
bytes each. The cost, accepted deliberately: the reflow rule now lives in Python *and* in shell, with
a cross-reference comment in each. Change one, change the other.

Stopping condition: Shoki installs from a native package, appears in the application menu, and
right-clicking an audio file in Dolphin produces a transcript in the destination folder.

**Met 2026-08-14.** All three, verified on Otachi: `sudo pacman -U` installed
`shoki-0.1.0-2-any.pkg.tar.zst`, Shoki appeared in the application menu with its icon, and
"Send to Whisper" on Dolphin's top-level context menu wrote a transcript to
`~/Nextcloud/Documents/Transcriptions/`.

Status: ✅ Complete 2026-08-14. Native package only, by design — the other formats are Phase 4.

---

## Phase 4 — Broader Packaging and File Manager Support

Goal: Shoki installs on Debian- and Fedora-based systems and from a Flatpak, and the right-click
works on the file managers those systems actually ship.

Created 2026-08-14, when the author decided on a public release. Phase 3 deliberately did one
package format on one desktop, end to end. This phase is the breadth.

### Flatpak

- [ ] Manifest `build-aux/com.farsononline.shoki.yml`, on an `org.gnome.Platform` runtime. Meson
      already does the install, so the manifest itself is thin.
- [ ] Ships the GUI. No broad filesystem permission required.
- [ ] The destination directory is chosen once through the folder-chooser portal and stored.
- [ ] The file-manager helper is offered as a **link to a standalone version**, not as an
      "Install Dolphin integration" button that copies bundled files into the user's home. Revised
      2026-08-14: the button was more machinery than a URL. Preferences already carries that link
      (`PROJECT_URL` in `main.py`); it points at the project page and should point at the helper's
      own home once it has one.
- [ ] Give the helper a configuration surface that does not depend on Shoki. Falling back to
      built-in defaults alone leaves a Flatpak user's right-click *unconfigurable* — it works only
      for someone who happens to want `127.0.0.1:8080` and our idea of a destination folder. One
      lookup chain, keyed on which surface exists, so each install type has exactly one source of
      truth:
      1. GSettings, if the schema is readable — native. Preferences governs, and cannot drift.
      2. `~/.config/shoki/servicemenu.conf`, if not — Flatpak. The user edits a shipped example.
      3. Built-in defaults, if neither.

Sandbox filesystem access follows Flathub's rule: *"Static permissions must be kept to an absolute
minimum. Applications should rely on XDG Portals... when a suitable XDG portal exists... using the
portal becomes mandatory instead of static permissions."*

> **The unknown that could be the whole job.** GTK4's file dialog goes through the portal
> automatically inside a sandbox, so *choosing* a destination should work. But Shoki **stores** that
> path in GSettings and writes to it on every later run, including from a batch with no dialog in
> sight. Whether a portal grant survives an application restart has been flagged since 2026-08-13
> as an assumption to test rather than a promise. If it does not persist, that is
> not a packaging bug — it is a change to how Shoki remembers its destination, and it lands in
> `main.py`.

### Debian and Fedora packages

- [x] `.deb` (2026-08-15). Built and installed on Ubuntu 26.04 LTS; a real transcription ran.
      `lintian` gives two deferred warnings and one Phase 6 note, nothing else.
- [x] `.rpm` (2026-08-15). Built and installed on Fedora 44; a real transcription ran.
      `rpmlint` is clean apart from two dictionary false positives, the same two missing man
      pages, and four `explicit-lib-dependency` errors that are deliberately kept — see below.

> **What building both actually taught us, 2026-08-15.**
>
> - **Debian normalises file permissions; RPM does not.** `dh_fixperms` runs in every debhelper
>   build. RPM has no equivalent, so a `README.md` that was mode `0600` in the working tree went
>   into the package unreadable and `rpmlint` caught it. Meson is not the culprit — `install_data`
>   writes 644 regardless — so the blast radius is exactly the files RPM copies itself, `%doc` and
>   `%license`. Git records only the executable bit, so a build from a clone was never affected.
> - **RPM's automatic dependency generator finds nothing in a pure-Python app.** It produced only
>   `Requires: /usr/bin/bash /usr/bin/python3`, derived from shebangs. Every library dependency is
>   hand-written and therefore load-bearing. `rpmlint`'s `explicit-lib-dependency` error assumes ELF
>   linkage and does not apply here; removing those lines would yield a package that installs on a
>   bare system and dies on first import. Fedora has no `typelib()` provides to use instead.
> - **Installing on a full desktop proves almost nothing about dependencies.** `dnf` pulled ZERO
>   extra packages, because Workstation already had them all. Completeness was established by
>   reading every import in the source instead, not by watching an install succeed.
> - **Fedora ships introspection typelibs in the main library package**, unlike Debian's separate
>   `gir1.2-*` packages. `Requires: gtk4` covers `Gtk-4.0.typelib`; `glib2` carries `GLib-2.0`,
>   `Gio-2.0`, `gsettings` and `glib-compile-schemas`.
> - **Neither package needs an upstream tarball during development.** `dpkg-buildpackage -b` never
>   invokes `dpkg-source`, and `rpmbuild --build-in-place` skips `%prep`. Both verified.

Both wrap the same Meson install. The meson floor was set to `>= 0.59.0` in Phase 3 precisely so
these stay possible — Ubuntu 24.04 LTS ships meson 1.3.2, and declaring the version that happened to
be on the development machine would have locked them out.

> **"Official repos" is two very different jobs.** Building a `.deb` and a `.rpm` is packaging work
> and belongs here. Getting them *into* Debian or Fedora proper is a social process — a Debian
> Developer sponsor, or a Fedora package review — measured in months and largely out of the
> packager's control. That half is Phase 6, and it should be sized honestly rather than folded in
> here as if it were a build step.

### File manager support

The helper script is the constant. It knows nothing about any file manager, reads its settings at
runtime, and takes paths or `file://` URLs. **Every file manager below needs a way to invoke it, not
a reimplementation of it.** That is what makes this phase affordable.

| File manager | Ships with | Mechanism | System-wide install? |
|---|---|---|---|
| Dolphin | KDE Plasma | `.desktop`, `Type=Service` | ✅ `/usr/share/kio/servicemenus/` |
| Nautilus | GNOME — Ubuntu, Fedora Workstation | executable script, paths via environment | ❌ `~/.local/share/nautilus/scripts/` only |
| Nemo | Cinnamon — Linux Mint | `.nemo_action`, declarative | Believed yes; unverified |
| Thunar | Xfce — Xubuntu, Mint Xfce | custom action in `uca.xml` | ❌ a user config file that must be merged |
| COSMIC Files | Pop!_OS | none confirmed | — |

- [ ] Nautilus
- [ ] Nemo
- [ ] Thunar
- [ ] COSMIC Files, if it is possible at all

> **The architectural problem, and it is not the one anticipated.** Phase 3 assumed the cost of a
> second file manager was writing a second integration. It is not — Nemo's actions are close cousins
> of KDE's service menus, and Nautilus takes an ordinary executable script. The real problem is that
> **Nautilus and Thunar have no system-wide location.** A `.deb` cannot install into a user's home,
> and Thunar's actions live in a config file that would have to be *merged* rather than dropped in.
>
> So the "Install integration" button rejected for the Flatpak comes back — for a different reason.
> Not sandboxing, but the absence of a system path. Copying bundled files into the user's own home,
> on an explicit click, remains categorically different from downloading and executing something,
> which stays forbidden.
>
> Nautilus also puts scripts under a **Scripts** submenu rather than at the top level, so the GNOME
> experience is inherently one click deeper than the KDE one. Worth knowing before promising parity.

> **Source tiering, stated plainly.** Dolphin's mechanism is Tier 1 and verified on Otachi. The
> Nautilus scripts directory and its environment variables come from Ubuntu community documentation
> — Tier 3, and it needs confirming against GNOME's own docs and a real Nautilus before anything is
> built on it. Nemo's and Thunar's mechanisms are Tier 3/4 and unverified. COSMIC Files' feature
> request (`pop-os/cosmic-files` issue #1445) is *closed*, but whether it was closed as implemented
> or declined could not be determined — check a current build before promising anything.

### One install list, every package — decided 2026-08-15

Every package format ships the SAME set of file-manager files. There is no per-distro tailoring, and
Meson's install list is the single source of truth for all of them.

The reason is that a packager cannot know which desktop the user runs. "Arch users get the KDE
files" sounds reasonable until an Omarchy box — Arch, Hyprland, and Nautilus as the default handler
for `inode/directory` — walks in. Any per-distro guess about the desktop is wrong for somebody.

This is already how it behaves: the `.deb` and `.rpm` built on 2026-08-15 both contain
`/usr/share/kio/servicemenus/shoki-transcribe.desktop` on machines with no KDE. It costs a few
hundred bytes, and a file manager that is not installed never reads its directory. Dormant, not
broken.

The four targets split into two categories, and the split is what drives the design:

| | Where it must live | Who installs it |
|---|---|---|
| Dolphin, Nemo | `/usr/share/...` | the package, directly |
| Nautilus, Thunar | the user's home | Shoki, on an explicit click |

### Why a package must not write into a user's home

Worth writing down, because "the installer runs as root, so it can write anywhere" is true and still
does not help.

- **Which home?** A package is installed once for a machine that may have zero users, one, or fifty,
  including service accounts and directory-server users who do not exist yet. `dpkg` has no basis
  for choosing among them.
- **Users created after installation get nothing.** A file in `/usr/share` serves every user
  forever, including ones added next year. A file copied into `/home/tony` serves exactly one.
- **Uninstalling would delete files out of a user's home.** `dpkg` and `rpm` own and track every
  file they install, and remove them on uninstall. That is the behaviour you want for `/usr` and
  emphatically not for `/home`.
- **The home directory may not be readable at install time** — encrypted homes, network homes not
  yet mounted, or an atomic distro where `/home` is not part of the layered image at all.
- **A post-install scriptlet cannot ask.** Established in Phase 3 and it applies identically here: it
  runs as root, non-interactively, with no session and no display.

So the correct actor is the application itself, running as the user, with the user's consent. That
is the whole justification for the Preferences button — not convenience, and not a workaround.

Note this is a practical and structural argument rather than a quoted prohibition. Debian Policy
chapter 9 was checked and does not contain an explicit "must not install into /home" rule; it defers
to the FHS. The reasons above stand on their own.

Deliberately out of scope: PCManFM, Caja, Krusader, and anything else outside the desktops that ship
on mainstream Debian- and Fedora-derived distributions.

Stopping condition: Shoki installs from a Flatpak, a `.deb` and an `.rpm`, and right-click
transcription works on Dolphin, Nautilus and Nemo.

Status: 🔨 In progress. Packaging done 2026-08-15; Flatpak and file managers outstanding.

---

## Phase 5 — Polish for Release

Goal: the project is presentable to strangers. Nothing is published yet.

Deliverables:

- [x] Custom icon (2026-08-14). Pulled forward into Phase 3 — a packaged application wearing a
      generic placeholder does not feel installed, and the icon turned out not to block anything, so
      there was no reason to wait.

      **Two SVGs, not a ladder of PNGs.** GNOME's HIG asks for one full-colour icon drawn in a
      128×128 area plus one symbolic version; the PNG-size-ladder model is pre-GTK4. Shipped as
      `icons/hicolor/scalable/apps/com.farsononline.shoki.svg` and
      `icons/hicolor/symbolic/apps/com.farsononline.shoki-symbolic.svg`. There are no separate
      light and dark variants either — the symbolic icon is monochrome and GTK recolours it.

      **The kanji are not in the icon.** 書記 is the mark, but 書 alone is ten strokes: at 32×32
      those land under a pixel each and turn to grey. The icon is the nib and waveform; the
      characters belong where they are rendered large — About, the README, the repository page.

      The full-colour icon inherits the reference artwork with three fixes: the left waveform tail
      was 2px against the right's 4px and vanished below 48px; the pen slit was a hardcoded
      `#303238`, the gradient's *top* colour, while the nib sits where the gradient has moved well
      past it — it now samples the same gradient via `gradientUnits="userSpaceOnUse"`; and there was
      no `<title>` for screen readers. The symbolic version drops everything but the nib and two
      waveform stubs, on whole-pixel coordinates, with the slit as a real hole so it survives being
      recoloured either way.

      > **A stale-icon episode that is not worth documenting for users.** Installing a `.desktop`
      > file whose `Icon=` pointed at a not-yet-existing file made every Plasma process cache the
      > failure, and clearing it took `kbuildsycoca6`, deleting `~/.cache/icon-cache.kcache`,
      > restarting plasmashell, and restarting KRunner separately. That window is an artefact of
      > building in two steps. A real install lands the desktop entry and its icon in one
      > transaction, so the first lookup succeeds and there is nothing stale to clear.
- [ ] Appstream metainfo `com.farsononline.shoki.metainfo.xml`, validating cleanly with
      `appstreamcli validate`
- [ ] Screenshots — 2–3, consistent window size, meaningful content, no personal data
- [ ] README a stranger can follow: prerequisites, the server requirement including `--convert`,
      install steps, troubleshooting
- [ ] LICENSE finalised — copyright holder confirmed 2026-08-13 as Tony Farson, personally rather
      than an entity
- [ ] `CONTRIBUTING.md`, if PRs are wanted
- [ ] Repo hygiene — issue and PR templates, `.editorconfig`

Stopping condition: a stranger could clone the repo, follow the README, install it, and run it.

Status: ⏳ Not started

---

## Phase 6 — Public Distribution

Goal: Shoki is available to Linux users who did not build it.

**Decided 2026-08-14: yes.** This supersedes the 2026-08-13 entry that deferred the decision until
after Phase 3.

> **Warning, unchanged and now accepted.** This creates an ongoing maintenance obligation. Users
> file issues, request features on their own timelines, and expect updates when their distribution
> moves under them. Stopping after Phase 5 was always a perfectly good outcome; the author has
> chosen otherwise, knowingly.

The four criteria written on 2026-08-13 were meant to be answered by evidence from real packages.
Three of them still have not been, because Phase 4 has not run yet. Recording that honestly:

- **Did the Flatpak avoid broad static permissions?** Unanswered — no Flatpak exists. The design
  intends portals only, but intent is not evidence, and Flathub review is where it gets tested.
- **Is a GUI-only Flatpak worth shipping?** Partly answered by Phase 4's approach: it is not
  GUI-only in effect, because the file-manager helper is offered alongside it as a standalone
  download rather than being absent.
- **Does the audience want a Flatpak at all, versus an AUR package?** Unanswered. Every Shoki user
  must already run their own whisper.cpp server, which skews the realistic audience toward people
  comfortable with the AUR.
- **Is maintainership wanted?** **Yes.** This was always a preference rather than a technical
  question, and it is the one that actually decided the matter.

Targets, in ascending order of how much of the work is out of the author's hands:

- [ ] **Flathub.** Self-service submission, a manifest, and a review that is technical and
      tractable. The most likely to land first.
- [ ] **AUR.** The PKGBUILD becomes a proper source-tarball build against a tagged release rather
      than the `$startdir/..` working-tree build Phase 3 uses. Cheap, and arguably the best match
      for the actual audience.
- [ ] **Debian.** Requires a Debian Developer to sponsor the package. Months, and the timeline is
      not the author's to set.
- [ ] **Fedora.** Requires a package review by an existing packager. Same shape, same caveat.

> **`v0.1.0` must be tagged before any of this.** Every route above builds from a release, not from
> a branch. The tag is still gated on the Phase 2 stopping condition — Shoki being used for real
> work and feeling finished rather than prototype-ish — which is a judgement, not a checklist.

Prerequisite: Phase 5 in full. A stranger-ready README, appstream metainfo that validates,
screenshots, and a `CONTRIBUTING.md` are not polish here; they are submission requirements. Flathub
in particular will reject a manifest without valid metainfo.

Status: ⏳ Not started

---

## Log of Completed Phases

> **Re-scoped 2026-08-14.** Phase 3 originally carried the Flatpak, and polish was Phase 4.
> When public release was decided, the three remaining package formats and the other file
> managers became Phase 4 in their own right, polish moved to Phase 5, and public distribution
> to Phase 6. Nothing was dropped. The phase sections themselves describe what they are, not
> what they used to be — git holds that history.

### Phase 0 — Scaffolding — completed 2026-08-13

Repository initialised at `~/Projects/github/shoki` on branch `main`, pushed to
`github.com/tonyfarson/shoki` (public, MIT) over SSH. Root commit `fd7db32`, 10 files.

An empty `Adw.ApplicationWindow` titled "Shoki" opens via `PYTHONPATH=src python -m shoki`,
confirmed visually.

Notes worth carrying forward:

- The repo path is `~/Projects/github/shoki`, not `~/Projects/apps/shoki` as originally planned.
- Claude's working files live in `.claude/` and are gitignored, along with `.obsidian/`,
  `_to_delete/`, and Python bytecode.
- `Adw.ApplicationWindow` has no titlebar of its own; the header bar lives inside the content tree
  via `Adw.ToolbarView`. An empty window with no `Adw.HeaderBar` would have looked broken.

### Phase 0.5 — Scoping Session — completed 2026-08-13

Produced the What Shoki Is, Versioning, Interface Direction and server-behaviour sections — the
last of which now lives in `docs/SERVER.md` —
plus rewritten Phases 1 through 5.

The premise was challenged directly during this phase: given an existing Dolphin service menu that
already transcribes by right-click, and a container capable of serving its own web UI, a desktop
window adds little. The project survived by changing shape — from a GUI wrapper around one HTTP call
to a control surface for a thirty-parameter API, shipped alongside the file-manager verb rather than
in place of it.

Corrections made to prior documentation:

- Per-request `language` and `translate` are supported. Earlier notes deferred language as possibly
  unimplementable, based on the upstream README's incomplete parameter list.
- `response_format` accepts five values, now confirmed in source rather than assumed.
- whisper.cpp serves static files from `--public` but ships no UI. The mount point exists; the
  content does not. It is a bring-your-own-UI hook.
- Cancellation was described as impossible. That was wrong twice over, and both corrections came
  from Tony refusing to accept the claim. Phase 0.5 established the library exposes `abort_callback`
  and downgraded "impossible" to "unexposed". Phase 2 then found the server example *does* wire it,
  to `httplib::Request::is_connection_closed()` — so cancellation is neither impossible nor
  unexposed, and closing the connection genuinely stops the inference.
- Flatpak was recorded as a decision in earlier documents. It was a preference. Decoupling the
  Dolphin integration removed the conflict entirely, and both formats now ship.

Ideas rejected during this phase, with reasons, are in `FUTURE.md`.

### Phase 1 — Walking Skeleton — completed 2026-08-13

An end-to-end path exists: choose a file, POST it as multipart, read the transcript. Built as
`src/shoki/transcribe.py` (no knowledge of the GUI) and a rewritten `src/shoki/main.py`.

What the skeleton was for — finding out what is actually hard — paid off in five places:

- The HTTP library question resolved to libsoup 3 on a stronger argument than the one that motivated
  the constraint. The upload percentage that made it load-bearing was dropped mid-phase; the reason
  to keep libsoup was that it removes threading from the project entirely.
- `set_request_body_from_bytes` needs `None` as its content type, or the multipart boundary written
  by `to_message()` is overwritten and every request fails. The natural thing to write is wrong.
- The `json` reply shape was an assumption in the code, labelled as one, and is now observed.
- `GET /health` answers during an inference, which keeps the Phase 2 liveness indicator alive — with
  a narrower promise than the word "health" suggests.
- Input format support turned out to be a server startup flag rather than an API guarantee, which
  makes the file picker's filter a local truth rather than a portable one.

Two deliberate deviations from the plan, both agreed rather than assumed:

- Requests were written asynchronously in Phase 1 although the roadmap permitted a blocking UI,
  because with libsoup the async version was the same work and the blocking version would have been
  discarded in Phase 2.
- The upload percentage was removed from Phase 2 rather than built, on the grounds that it measures
  nothing interesting over loopback.

Everything in this phase was run on Otachi and its output pasted back. Nothing is recorded as
verified on the strength of reasoning alone.

---

## Notes on Approach

- Claude writes files; Tony runs them. Claude has read/write access to `~/Projects/github/shoki/` and
  creates and edits files directly rather than dictating them. Claude's shell runs in an isolated VM
  with no GTK, no PyGObject, no Flatpak, and no network — it cannot launch the app, install packages,
  or reach the whisper.cpp server. Every build, run, and test happens on Otachi, executed by Tony,
  with output pasted back.
- One commit per session, at the end. Do not propose small follow-up commits afterwards.
- Build the skeleton before the features. The walking skeleton in Phase 1 exists to find out what is
  actually hard before ten features depend on the answer.
- One seam, not ten. The request builder takes a parameter dict. Adding the advanced drawer later
  then costs a UI, not a rewrite.
- Small, verifiable commits. Every commit should leave the app in a runnable state, or say
  explicitly that it does not.
- When in doubt, check the current docs. GTK4 and libadwaita evolve; training data goes stale. A
  README is not automatically sufficient Tier 1 evidence either — this roadmap was rewritten once
  because a README's parameter list was incomplete and two features were wrongly declared impossible.
- Scope creep is the enemy. Ideas go to `FUTURE.md`. Every time.

---
type: roadmap
status: active
project: shoki
created: 2026-08-12
updated: 2026-08-13
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
depends on, and Verified Server Behaviour below for what that server actually accepts.

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

## Verified Server Behaviour

Confirmed against `examples/server/server.cpp`, `examples/server/README.md`, and `include/whisper.h`
in `ggml-org/whisper.cpp` on 2026-08-13. This supersedes several claims made earlier in this
project's documentation.

Routes are registered as `request_path + inference_path`. Defaults: `request_path` empty,
`inference_path` `/inference`, bound to `127.0.0.1:8080`. Other routes are `GET /`, `GET /health`,
`POST /load`, and a CORS preflight on the inference path. There is no `/v1/` alias upstream and the
upstream README makes no OpenAI-compatibility claim.

> **Note:** The endpoint `/v1/audio/transcriptions` used during development comes from the Otachi
> container's own `--inference-path` flag. That flag *replaces* the default route rather than adding
> one, which is why `/inference` returns 404 on that server. The 404 is confirmation the flag took
> effect, not a fault.

The README's list of six request parameters is incomplete. `get_req_parameters()` reads roughly
thirty form fields:

- Strings — `language`, `prompt`, `response_format`
- Booleans — `translate`, `diarize`, `tinydiarize`, `detect_language`, `split_on_word`,
  `no_timestamps`, `token_timestamps`, `carry_initial_prompt`, `suppress_non_speech`, `suppress_nst`,
  `vad`, `no_language_probabilities`, `debug_mode`
- Numeric — `offset_t`, `offset_n`, `duration`, `max_context`, `max_len`, `best_of`, `beam_size`,
  `audio_ctx`, `word_thold`, `entropy_thold`, `logprob_thold`, `no_speech_thold`, `temperature`,
  `temperature_inc`, and six `vad_*` tuning fields
- Not read from requests — `threads` and `no_context` are startup options only

`response_format` is branched on five string literals: `text`, `srt`, `vtt`, `verbose_json`, and
`json` as the default fallback.

Behaviour that constrains design:

- The server defaults to `language=en`. Auto-detect is not free — the client must send
  `language=auto` on every request.
- `detect_language` detects the language and exits, returning no transcript. It is not the
  auto-detect switch.
- `translate` is source-to-English only. Whisper's translation task has no target-language
  parameter. This is a checkbox, never a dropdown.
- `vad` is a request field, but the VAD model is a startup flag (`-vm`). Toggling `vad` against a
  server started without one will fail.
- `tinydiarize` requires a tdrz model at startup; plain `diarize` requires stereo audio.
- `POST /load` swaps the server's model, reading a `model` form field. There is no endpoint listing
  available models, the path is server-side, the swap is global across all clients, and upstream
  warns it loads arbitrary server-side paths.
- The inference endpoint is blocking. No SSE, chunked encoding, or websockets. Progress percentages
  and live partial transcripts are impossible without patching the server.
- Cancellation is an *exposure* limit, not a capability limit. `whisper_full_params` carries
  `abort_callback` and `encoder_begin_callback`, and `whisper.h` states of the latter: "If it returns
  false, the computation is aborted." The server example never wires either to anything
  client-facing, and there is no cancel route. A client can stop waiting; it cannot stop the server.

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
13. Phase 5 deferred with written criteria rather than decided — see Phase 5.

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

> **Open:** where the initial prompt sits in the vertical order. It was suggested it should come
> first, but the jargon worth priming it with is usually not known until the file is chosen. Resolve
> during Phase 2 layout.

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

- [ ] Does `GET /health` still answer while an inference is in flight? The liveness indicator in
      Phase 2 depends on it. Assume nothing until it is observed.

Stopping condition: an audio file picked in the app produces a correct transcript in the output area,
against the Otachi server.

Explicitly not in Phase 1: save, copy, settings, batch, drag and drop, translation, format choice,
progress, threading, keyboard shortcuts, Dolphin integration, styling beyond default libadwaita.

Status: ⏳ Not started

---

## Phase 2 — Feature Complete (v0.1.0)

Goal: the first fully-featured working copy. Used daily by its author. Nothing promised to anyone
else.

Deliverables:

- Threading — transcription runs on a worker thread and the UI stays responsive
- Output format picker — `text` (default), `srt`, `vtt`, `json`, `verbose_json`
- Translate to English — a checkbox
- Initial prompt field — a large accuracy win for proper nouns and jargon
- Subtitle tuning in settings — `no_timestamps`, `split_on_word`, `max_len`
- Batch a directory — client-side loop, one POST per file, sequential. No server support required.
- Save output to a chosen directory; copy to clipboard
- Drag and drop onto the window (`Gtk.DropTarget`)
- Settings via `Adw.PreferencesDialog`, persisted with `GSettings`
- Error handling — clear user-facing messages for unreachable server, non-2xx responses, unreadable
  files. No stack traces in the UI.
- Keyboard shortcuts and full keyboard navigation
- Accessible roles and labels on every interactive widget

Progress and liveness — three honest indicators, no invented percentages:

- Spinner plus an **elapsed-time counter**. A real number beats a bar creeping toward a fabricated
  100%.
- **Batch counter** — "file 3 of 12" is measurable and true. The progress bar exists; it measures
  files, not audio.
- **Upload percentage** — the POST body upload is measurable, and matters for large files over a
  network. Depends on the Phase 1 library choice.
- **Liveness via `GET /health`**, polled on a second connection during a job, distinguishing "server
  wedged" from "server working". Conditional on the Phase 1 test.

Cancel:

- Cancelling a single file stops Shoki waiting. It does **not** stop the server, which continues to
  completion and discards the result. Say so in the UI rather than implying otherwise.
- Cancelling a batch is genuinely effective — remaining files are never sent.

Output destination and filenames:

- One shared destination directory by default for both Shoki and the Dolphin service menu. All
  transcripts land in one place; the user decides what happens next. Both are customisable.
- The shipped default resolves the XDG Documents directory plus a `Transcriptions` subfolder at
  runtime. `~/Nextcloud/Documents/Transcriptions/` is a personal setting, not a shipped default.
- **Collision rule: append a numeric suffix** — `interview.txt`, then `interview_1.txt`. Never
  overwrite silently.
- Under Flatpak the destination is chosen once through the folder-chooser portal and the result
  stored, rather than declared as a static filesystem permission. See Phase 3.

Language auto-detect is always on and has no control. A manual language override is deferred to the
advanced drawer — see `FUTURE.md`.

Stopping condition: Shoki is used for a real transcription task and feels finished rather than
prototype-ish. Tag `v0.1.0`.

Explicitly not in Phase 2: packaging, model switching, system monitoring, the advanced-parameters
drawer, batch queue UI, alternative backends.

Status: ⏳ Not started

---

## Phase 3 — Packaging and Desktop Integration

Goal: Shoki installs as a real application, and right-clicking an audio file transcribes it.

Packaging was resolved on 2026-08-13. **Both native packages and a Flatpak ship**, with no
compromise on either — a conclusion that only became available once the Dolphin integration was
decoupled from the application.

The decoupling: the service menu is a **standalone script that never launches Shoki**. Right-click,
transcribe, done. Because the script is not sandboxed, the Flatpak never needs to read arbitrary
files handed to it by the file manager, and therefore never needs broad filesystem access.

Native packages — pacman first, then `.deb` and `.rpm`:

- Ship the application, the helper script, and the `.desktop` service menu
- Install the GSettings schema system-wide, so the script can read Shoki's settings directly with
  `gsettings get com.farsononline.shoki endpoint-url`. One settings dialog governs both, and they
  cannot drift.

Flatpak:

- Ships the GUI. No broad filesystem permission required.
- An "Install Dolphin integration" button copies **bundled** files into
  `~/.local/share/kio/servicemenus/` and marks the `.desktop` executable.
- The schema lives inside the sandbox and is invisible to a host script, so the script falls back to
  its own built-in defaults. Graceful degradation, not a separate code branch.

Rules that apply to both:

- **No sudo, ever.** Plasma 6 reads service menus from `~/.local/share/kio/servicemenus/` — the
  user's own home directory. That is also why the `.desktop` file must be executable: the directory
  is not a system-authorised location and Plasma silently ignores non-executable entries there.
- **Never download and execute.** Fetching a script at runtime and running it is remote code
  execution by design, breaks offline installs, and bypasses package verification. The files are
  tiny — bundle them.
- The script must always fall back to defaults if `gsettings` fails. A right-click that silently does
  nothing is the worst available failure mode.
- Settings meaningful to the right-click path: endpoint, destination, output format, translate. Not
  the initial prompt, which is per-file and meaningless without someone to type it.

Sandbox filesystem access follows Flathub's rule: *"Static permissions must be kept to an absolute
minimum. Applications should rely on XDG Portals... when a suitable XDG portal exists... using the
portal becomes mandatory instead of static permissions."* The destination directory is therefore
chosen once through the folder-chooser portal and stored, rather than declared as
`--filesystem=xdg-documents`.

> **Assumption to test, not a promise:** how durably folder access granted through the portal
> persists across application restarts. The principle is Tier 1; the persistence behaviour needs
> observing against a real Flatpak build before Phase 2's "default destination" is relied upon.

Open:

- [ ] Which file managers beyond Dolphin are targeted. Nautilus, Thunar, and Nemo each use a
      different, incompatible extension mechanism — a per-manager cost, not a shared one.

Stopping condition: Shoki installs from a native package, appears in the application menu, and
right-clicking an audio file in Dolphin produces a transcript in the destination folder.

Status: ⏳ Not started

---

## Phase 4 — Polish for Release

Goal: the project is presentable to strangers. Nothing is published yet.

Deliverables:

- Custom icon — proper SVG following the relevant icon guidelines
- Appstream metainfo `com.farsononline.shoki.metainfo.xml`, validating cleanly with
  `appstreamcli validate`
- Screenshots — 2–3, consistent window size, meaningful content, no personal data
- README a stranger can follow: prerequisites, the server requirement, install steps, troubleshooting
- LICENSE finalised — copyright holder confirmed 2026-08-13 as Tony Farson, personally rather than an
  entity
- `CONTRIBUTING.md`, if PRs are wanted
- Repo hygiene — issue and PR templates, `.editorconfig`

Stopping condition: a stranger could clone the repo, follow the README, install it, and run it.

Status: ⏳ Not started

---

## Phase 5 — Public Distribution (Optional)

Goal: Shoki is available to Linux users who did not build it.

> **Warning:** This creates an ongoing maintenance obligation. Users file issues, request features,
> and expect updates. Only proceed if being a maintainer is genuinely wanted. Stopping after Phase 4
> is a perfectly good outcome.

Decided 2026-08-13: **the decision is deferred until after Phase 3, not taken now.** Deferring it is
deliberate rather than an omission — the information that would settle it does not exist yet.

Decide it against these criteria, once Phase 3 has produced real packages:

- [ ] Did the Flatpak survive Phase 3 without broad static permissions? If it needed them, Flathub
      review will be a fight, and that changes the answer.
- [ ] Is the GUI-only Flatpak — no right-click integration — actually worth shipping to strangers, or
      does it under-deliver the thing that makes Shoki worth having?
- [ ] Does the audience want a Flatpak at all? An AUR package may serve the realistic user base
      better, given that every user must already be running their own whisper.cpp server.
- [ ] Is maintainership wanted? This is a preference, not a technical question, and it is the one
      that actually decides.

Status: ⏳ Deferred until after Phase 3

---

## Log of Completed Phases

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

Produced the What Shoki Is, Versioning, Verified Server Behaviour, and Interface Direction sections,
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
- Cancellation was described as impossible. It is unexposed, not impossible — the library has
  `abort_callback`; the server never wires it up.
- Flatpak was recorded as a decision in earlier documents. It was a preference. Decoupling the
  Dolphin integration removed the conflict entirely, and both formats now ship.

Ideas rejected during this phase, with reasons, are in `FUTURE.md`.

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

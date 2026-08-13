---
type: roadmap
status: active
project: shoki
created: 2026-08-12
updated: 2026-08-13
---

# Shoki Roadmap

Shoki is a GTK4/libadwaita desktop application (Python) that provides a simple GUI for the whisper.cpp transcription server. This document tracks phased development from empty repo to (optionally) published Flathub app.

**Core principles:**
- Simple, not overwhelming, easy to maintain
- Each phase has a clean stopping point where "we're done" is a valid answer
- No scope creep — new ideas go to `FUTURE.md`, not into the current phase

**Testing backend:** whisper.cpp server running on Otachi at `http://localhost:8080/v1/audio/transcriptions`. See `README.md` for the setup this app depends on.

---

## Phase 0 — Scaffolding

**Goal:** prove the toolchain works and a git repo exists.

**Deliverables:**
- Local project directory `~/Projects/github/shoki/` (already exists — `git init` here and add
  `origin`; this is not a clone)
- GitHub repo `tonyfarson/shoki` created empty, public, MIT license
- Initial directory structure:
  ```
  shoki/
  ├── .claude/            ← Claude operating instructions (gitignored, never published)
  ├── src/shoki/          ← Python package (module code)
  ├── data/               ← icons, .desktop, appstream (placeholders for now)
  ├── build-aux/          ← reserved for Flatpak manifest (empty in P0)
  ├── docs/
  │   └── ROADMAP.md      ← this file
  ├── FUTURE.md           ← scope-creep log (starts empty)
  ├── README.md           ← what it is, how to run from source (Phase 0 version)
  ├── LICENSE             ← MIT text
  └── .gitignore          ← Claude files + Python + Flatpak build artifacts
  ```
- CachyOS prerequisites installed: `python`, `python-gobject`, `gtk4`, `libadwaita`, `flatpak`, `flatpak-builder`
- A ~10-line Python script (`src/shoki/main.py` or similar) that opens an empty Adw.ApplicationWindow titled "Shoki"
- Script runs successfully; window appears

**Stopping condition:** `python -m shoki` (or equivalent) opens a titled empty window. Close it. First commit made and pushed to GitHub.

**Progress checklist:**

- [x] Directory skeleton created (2026-08-13)
- [x] `.gitignore`, `LICENSE`, `README.md`, `FUTURE.md` written (2026-08-13)
- [x] CachyOS prerequisites verified installed (2026-08-13)
- [x] Hello-world window runs (2026-08-13)
- [ ] `git init` + GitHub repo + `origin` remote
- [ ] First commit pushed

**Verified toolchain (2026-08-13):** python 3.14.6-2, python-gobject 3.56.3-1, gtk4 1:4.22.4-1.1,
libadwaita 1:1.9.3-1.1, flatpak 1:1.18.0-1.1, flatpak-builder 1.4.10-1.1. PyGObject imports Gtk 4.0
and Adw 1 cleanly on Python 3.14 — this was an open risk and is now closed.

**Two startup warnings are expected and are not Shoki bugs:**

```
Adwaita-WARNING **: Using GtkSettings:gtk-application-prefer-dark-theme with
libadwaita is unsupported. Please use AdwStyleManager:color-scheme instead.
```

Emitted because the desktop environment sets the GTK dark-theme preference globally. Shoki never
touches `GtkSettings`. It would disappear only if the DE stopped setting it, or if Shoki explicitly
drove `AdwStyleManager` — which is not Phase 0 scope.

```
WARNING: radv is not a conformant Vulkan implementation, testing use only.
```

Standard Mesa RADV boilerplate, printed as GTK4 initialises its renderer. Unrelated to the
whisper.cpp Vulkan backend and unrelated to Shoki.

**Explicitly NOT in Phase 0:** any transcription logic, any HTTP calls, any settings UI, any Flatpak concern beyond making sure `flatpak-builder` is installed.

**Status:** 🚧 In progress

---

## Phase 0.5 — Scoping Session

**Goal:** re-validate Phases 1 through 5 against findings made *after* this roadmap was written.
No code is produced in this phase. It exists because several Phase 1 and Phase 2 deliverables rest
on assumptions that have since been contradicted by primary sources.

> **Note:** Phases 1–5 below are preserved as originally written on 2026-08-12. They are known to
> contain at least one confirmed-wrong API and several unverified claims. Do not build from them
> until this phase closes.

**Findings requiring a decision:**

- whisper.cpp's server registers routes as `request_path + inference_path`, defaulting to
  `/inference`. No `/v1/` alias exists in `examples/server/server.cpp`. The endpoint
  `/v1/audio/transcriptions` used during development comes from local runtime configuration, not
  from an OpenAI compatibility layer. Phase 1 presents it as standard.
- Documented request parameters are only `file`, `temperature`, `temperature_inc`, `prompt`,
  `carry_initial_prompt`, `response_format`. Language is a server *startup* option. Phase 2's
  language dropdown may not be implementable.
- The inference endpoint is blocking request/response — no SSE, chunked encoding, or websockets.
  Progress reporting and streaming partial transcripts are impossible without patching the server.
- `Adw.PreferencesWindow`, named in Phase 2, is deprecated since libadwaita 1.6 in favour of
  `Adw.PreferencesDialog`. The development host runs libadwaita 1.9.3.
- Accepted `response_format` values are unverified beyond `json`. Phase 1 assumes `text`; Phase 2
  assumes `text`, `json`, `srt`, `vtt`.
- Flathub requires that static permissions be kept to an absolute minimum and mandates XDG portals
  where they exist. Phase 2's default save directory outside the sandbox interacts with this.
- Backend portability has four axes, verified 2026-08-13. All of whisper.cpp, speaches and OpenAI
  accept `multipart/form-data` with a field named `file`. They diverge on: (a) path — whisper.cpp
  defaults to `/inference`, the others use `/v1/audio/transcriptions`; (b) `model` — REQUIRED by
  OpenAI and speaches, absent from whisper.cpp, which loads one model at startup; (c) auth — none
  for whisper.cpp and speaches, API key for hosted providers, which under Flatpak means libsecret
  and the Secret portal; (d) `response_format` — OpenAI supports json, text, srt, verbose_json, vtt,
  diarized_json and the set varies by model, so no fixed dropdown is correct everywhere. Decide how
  far portability goes: free-form fields cost nothing and exclude nothing, whereas per-provider
  presets adopt those providers and their support burden.
- The product framing changed: Shoki is a thin, decoupled client, not a "GPU agnostic" app. Hardware
  breadth belongs to whisper.cpp. This affects README positioning and whether Phase 5 makes sense
  for an app that cannot work without a separately-run server.

### Universal backend support — named now, built later

Stated intent, 2026-08-13: Shoki should eventually work with any popular transcription backend —
a choice of servers, their models, and an API key for services that require one. These are
explicitly future features, not Phase 1 or Phase 2 work. They are recorded here so that Phase 1 can
avoid decisions that make them expensive to add later.

Candidate backends:

| Backend | Shape | `model` | Auth | Status |
|---|---|---|---|---|
| whisper.cpp | own path, default `/inference` | absent | none | current target, verified |
| speaches | OpenAI-shaped | required | none | verified |
| OpenAI hosted | OpenAI-shaped | required | API key | verified |
| Groq, Deepgram, AssemblyAI, others | unknown | unknown | unknown | unverified — do not assume |

> **Note:** The dividing line for "universal" is whether a backend is OpenAI-shaped. Anything that
> accepts `multipart/form-data` with a `file` field and returns a transcript is reachable by
> parameterising what Shoki already sends. Anything with its own request or response schema needs a
> per-backend adapter, and that is the point where universality stops being free.

Cheap now, expensive later — decisions Phase 1 should make deliberately:

- [ ] Put the HTTP call behind a single function that takes a config object and returns text, rather
      than building the request inline in a button handler. Adding `model`, headers, or auth later
      then touches one place.
- [ ] Request `json` rather than `text` as the response format, and extract the transcript from it.
      `json` is the one format all three verified backends support; `text` is not universally
      confirmed. This costs a few lines of parsing in Phase 1 and buys portability for free.
- [ ] Keep a single seam for response parsing and a single seam for error normalisation. Different
      backends fail differently, and retrofitting a seam is harder than leaving one.
- [ ] Name settings keys neutrally — `endpoint-url`, not `whisper-url`; `response-format`, not
      `format`. GSettings tolerates added keys but renaming them is a migration.
- [ ] Decide whether the settings shape anticipates several named backend profiles
      (`{name, url, model, auth, format}`) or a single endpoint. Single is fine for Phase 2, but
      going from one to many later is a schema change, so make the choice knowingly.
- [ ] Keep endpoint, model, and format as free-form fields rather than dropdowns. Free-form excludes
      nothing and claims nothing; per-provider presets adopt those providers and their bug reports.

Blockers that cannot be designed around in advance:

- **Secrets.** API keys must never go in GSettings — dconf is readable by anything in the session.
  They belong in libsecret, reached through the Secret portal under Flatpak. This is a feature with
  its own permission implications, not a text field.
- **Non-OpenAI-shaped APIs.** These need adapters. No amount of Phase 1 tidiness avoids that work.
- **Streaming.** None of this changes the fact that progress reporting and live partial transcripts
  are impossible against a blocking endpoint.
- **Privacy framing.** An app whose pitch is that audio stays on the user's own server needs to be
  deliberate about offering to send that audio to a third party. This is a positioning decision as
  much as a technical one.
- **Flathub surface.** Every added capability — auth, secret storage, wider network use — widens the
  permission set that reviewers scrutinise.

**Deliverables:**

- Each finding above resolved into a decision, recorded in this document
- Phase 1 and Phase 2 rewritten to match those decisions
- Contradictions between `docs/ROADMAP.md` and `FUTURE.md` reconciled — currently the language
  dropdown appears as a Phase 2 deliverable *and* as a deferred item
- Explicit decision on whether Phase 5 remains a goal

**Stopping condition:** Phases 1 and 2 are rewritten, agreed, and free of unverified claims. Every
remaining assumption is either verified against a Tier 1 source or explicitly labelled as an
assumption to be tested during implementation.

**Explicitly NOT in Phase 0.5:** writing application code, touching `src/`, designing UI layouts,
Flatpak work. This phase produces documents and decisions only.

**Status:** ⏳ Not started

---

## Phase 1 — Core Transcription

**Goal:** end-to-end transcription in the app. If Phase 1 works, Shoki is already better than curl for daily use.

**Deliverables:**
- Main window with three regions: file selection area (top), "Transcribe" button (middle), text output area (bottom, scrollable, read-only for now)
- File picker (`Gtk.FileDialog` — the modern API, not the deprecated `FileChooserDialog`) that filters to common audio/video MIME types
- HTTP POST to the whisper.cpp server on button click:
  - Multipart form with `file=@<path>` and `response_format=text`
  - Default endpoint: `http://localhost:8080/v1/audio/transcriptions` (hardcoded in P1; configurable in P2)
- Transcript displays in the output text area on success
- Basic error message on failure (network unreachable, non-2xx response, etc.) — a simple `Adw.Toast` or dialog is enough
- Blocking UI during transcription is acceptable in P1 (spinner and threading come in P2)

**Stopping condition:** Tony picks the JFK sample audio in the app, clicks Transcribe, and sees the correct transcript appear in the output area.

**Explicitly NOT in Phase 1:** save button, copy button, settings, spinner, threading, keyboard shortcuts, drag-and-drop, batch, styling beyond default libadwaita.

**Status:** ⏳ Not started

---

## Phase 2 — Usable Polish

**Goal:** app is genuinely usable day-to-day. Tony would reach for it before the CLI or the Dolphin service menu.

**Deliverables:**
- **Threading:** transcription runs on a worker thread so the UI stays responsive. Loading spinner shows during work.
- **Save button:** writes the transcript to a file (`Gtk.FileDialog` in save mode). Default location: `~/Nextcloud/Documents/Transcriptions/` (matching the existing Dolphin service menu behavior).
- **Copy button:** copies transcript to clipboard.
- **Settings dialog** (`Adw.PreferencesWindow`):
  - Endpoint URL (default `http://localhost:8080/v1/audio/transcriptions`)
  - Output format (dropdown: text, json, srt, vtt)
  - Language (dropdown: auto-detect + common languages)
  - Default save directory
- **Settings persistence:** `GSettings` (proper GNOME way) — this is a small learning curve but the right choice long-term.
- **Error handling:** clear user-facing messages for common failures (server unreachable, file too large, invalid audio, etc.). No stack traces in the UI.
- **Keyboard shortcuts:** Ctrl+O to open file, Ctrl+S to save, Ctrl+C to copy transcript (when the output area has focus).

**Stopping condition:** Tony uses Shoki for a real transcription task and reports it feels finished, not prototype-ish.

**Explicitly NOT in Phase 2:** Flatpak packaging, drag-and-drop, batch mode, live mic recording, streaming progress, subtitle preview, timestamped output editing.

**Status:** ⏳ Not started

---

## Phase 3 — Local Flatpak

**Goal:** Shoki is a real installed Linux application, not a script.

**Deliverables:**
- Flatpak manifest at `build-aux/com.farsononline.shoki.yml` (or `.json`)
- Base runtime: `org.gnome.Platform//48` (or current stable at time of build)
- SDK: `org.gnome.Sdk//48`
- Manifest builds successfully with `flatpak-builder --user --install --force-clean`
- Sandbox permissions declared correctly:
  - `--share=network` (needs to reach whisper.cpp server)
  - `--filesystem=host` or narrower (needs to read audio files; save destination needs write)
  - No unnecessary permissions
- App launches from the app menu with a placeholder icon
- Transcription works from inside the sandbox (localhost network access verified)
- `.desktop` file properly installed, app appears in menus

**Stopping condition:** Tony uninstalls the source-run version, installs the Flatpak bundle, and it works identically. He has a real installed app.

**Explicitly NOT in Phase 3:** publishing anywhere, screenshots, appstream metadata (the manifest needs a stub, but polished metainfo comes in P4), custom icon design.

**Status:** ⏳ Not started

---

## Phase 4 — Polish for Release

**Goal:** the project is presentable to strangers. Nothing is published yet.

**Deliverables:**
- **Custom icon:** proper SVG icon following GNOME icon guidelines (or a simpler design if we're not going for GNOME-native aesthetic). Both symbolic and full-color variants if using libadwaita conventions.
- **Appstream metainfo:** `com.farsononline.shoki.metainfo.xml` with description, screenshots, release notes, categories, developer info, content ratings. Validates cleanly with `appstreamcli validate`.
- **Screenshots:** 2–3 clean screenshots showing the app in typical use. Consistent window size, meaningful content, no personal data.
- **README overhaul:** clone-and-build instructions a stranger can follow. Includes prerequisites, whisper.cpp server requirement, build steps, troubleshooting.
- **LICENSE finalized:** MIT text with correct year and author.
- **CONTRIBUTING.md** (optional): if Tony wants to accept PRs.
- **Repo hygiene:** issues templates, PR template, `.editorconfig`, whatever polish makes the repo feel maintained rather than abandoned.

**Stopping condition:** a stranger could clone the repo, follow the README, build the Flatpak, and run it successfully.

**Explicitly NOT in Phase 4:** submitting to Flathub, requesting reviews, promoting the app. Just readiness.

**Status:** ⏳ Not started

---

## Phase 5 — Flathub Submission (Optional)

**Goal:** Shoki is published on Flathub and available to any Linux user with a Flatpak-enabled distro.

**⚠️ Warning:** this creates an ongoing maintenance obligation. Users will file issues, request features, and expect updates. Only proceed if Tony wants to be a Flathub maintainer.

**Deliverables:**
- PR to `flathub/flathub` following the [submission guidelines](https://docs.flathub.org/docs/for-app-authors/submission/)
- Manifest adjusted for Flathub build environment (no local file references; all sources must be reproducible from git tags / tarballs)
- Respond to reviewer feedback (usually 1–3 rounds of manifest tweaks)
- App published, listed, discoverable

**Stopping condition:** `flatpak install flathub com.farsononline.shoki` works from any machine.

**Post-Phase-5 responsibilities:**
- Respond to issues and PRs
- Publish updates for security or bug fixes
- Track upstream (whisper.cpp API changes, GTK/libadwaita updates)

**Status:** ⏳ Not started (may never start — perfectly fine)

---

## Log of Completed Phases

*(populated as phases finish)*

---

## Notes on Approach

- **Claude writes files; Tony runs them.** Claude has read/write access to `~/Projects/github/shoki/`
  and should create and edit files directly rather than dictating them. Claude's shell, however, runs in
  an isolated VM with no GTK, no PyGObject, no Flatpak, and no network — so Claude cannot launch the app,
  install packages, or hit the whisper.cpp server. Every build, run, and test happens on Otachi, executed
  by Tony, with output pasted back.
- **Small, verifiable commits.** Every commit should leave the app in a runnable state (or explicitly noted otherwise).
- **When in doubt, check the current docs.** GTK4 and libadwaita evolve. Training data goes stale. Web-search first, code second.
- **Scope creep is the enemy.** Ideas go to `FUTURE.md`. Every time.

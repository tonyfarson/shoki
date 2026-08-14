---
type: readme
status: active
project: shoki
created: 2026-08-13
updated: 2026-08-14
---

# Shoki

Shoki (書記, "scribe") is a GTK4/libadwaita desktop application that provides a graphical
control surface for a [whisper.cpp](https://github.com/ggml-org/whisper.cpp) transcription
server — and will ship a Dolphin service menu that transcribes any audio or video file by
right-click, without opening the application at all.

Shoki does no transcription itself. It sends an audio file to a server you run, and shows
you what comes back.

> **Note:** This project is pre-release. The application works and is used daily by its
> author, but it is not installable yet — there is no package, and it runs from a checkout.
> Packaging is Phase 3. See `docs/ROADMAP.md`.

## Status

- App ID: `com.farsononline.shoki`
- Platform: Linux only
- License: MIT
- Current phase: Phase 2 — Feature Complete. All deliverables met; `v0.1.0` not yet tagged.
- First planned release: `v0.1.0`

Both native packages and a Flatpak are planned. The Dolphin service menu is a standalone
script that does not launch Shoki, which is what lets the Flatpak stay minimally
permissioned. Native packages get tighter integration — the script reads the application's
own settings — while the Flatpak's script falls back to its built-in defaults. See Phase 3
in `docs/ROADMAP.md`.

## What It Does

- Transcribe a single file, a whole folder, or files dropped onto the window
- Five output formats: plain text, SRT, VTT, JSON, and verbose JSON
- Translate to English — Whisper translates *into* English only; there is no other target
- Initial prompt, for priming the model with names, jargon, and spellings
- Subtitle tuning for SRT and VTT: omit timestamps, maximum segment length, split on word
- Save to a destination folder, or copy to the clipboard
- Elapsed-time counter and a server liveness indicator during a job
- Cancel, which stops the server too rather than just stopping Shoki waiting
- Batch runs save each transcript as they go and show a running log

Language auto-detection is always on and has no control.

## Requirements

Shoki is a client. It needs a whisper.cpp server, running separately, that you can reach
over HTTP.

The reference deployment used during development runs the Vulkan container image:

```
ghcr.io/ggml-org/whisper.cpp:main-vulkan
```

An unflagged whisper.cpp server binds `127.0.0.1:8080` and serves its inference endpoint
at:

```
POST /inference
```

That is the endpoint Shoki ships as its default.

> **Note:** The path is configurable server-side. `--inference-path` *replaces* the default
> route rather than adding to it, so a server started with
> `--inference-path /v1/audio/transcriptions` serves only that path and returns 404 on
> `/inference`. Shoki therefore treats the endpoint URL as configuration, not as a constant.
> The upstream project makes no OpenAI-compatibility claim, and neither does Shoki —
> compatibility with other transcription backends is a future goal, not a present fact.

> **Video and non-WAV audio depend on a server flag, not on Shoki.** whisper.cpp accepts WAV
> unless the server was started with `--convert`, which makes it transcode with ffmpeg first.
> Shoki's file picker offers common audio and video formats, but no route reports which flags
> a server was started with, so Shoki cannot detect the difference. If a format is rejected,
> check the server.

## Running from Source

Shoki is not installable yet. To run it from a checkout:

```
cd shoki
glib-compile-schemas data/
GSETTINGS_SCHEMA_DIR=$PWD/data PYTHONPATH=src python -m shoki
```

Runtime requirements (Arch/CachyOS package names):

```
python python-gobject gtk4 libadwaita libsoup3
```

Shoki needs libadwaita 1.6 or newer for `AdwSpinner`, and 1.8 or newer for
`AdwShortcutsDialog`.

> **Note:** `PYTHONPATH=src` and `GSETTINGS_SCHEMA_DIR` are development conveniences — the
> package is not installed where Python searches, and the settings schema is not installed
> system-wide. Shoki falls back to built-in defaults when the schema is missing rather than
> crashing, but settings will not persist. Packaging in Phase 3 removes the need for both.

## Configuration

Settings live in GSettings under `com.farsononline.shoki` and are edited in the application's
Preferences dialog (`Ctrl+,`):

| Key | Purpose |
|---|---|
| `endpoint-url` | The whisper.cpp inference endpoint |
| `response-format` | Which format new transcriptions start in |
| `destination-directory` | Where transcripts are saved; empty resolves XDG Documents plus `Transcriptions` at runtime |
| `no-timestamps`, `split-on-word`, `max-len` | Subtitle tuning; only affects SRT and VTT |
| `color-scheme` | Follow the system light/dark preference, or force one |

Settings hold *defaults*. The main window overrides them for the current session without
changing them.

## Repository Layout

```
shoki/
├── src/shoki/      Python package (application code)
│   ├── __init__.py
│   ├── __main__.py     `python -m shoki` entry point
│   ├── main.py         application, window, and preferences dialog
│   └── transcribe.py   request building and response parsing
├── data/           GSettings schema; later icons, .desktop entry,
│                   appstream metadata, Dolphin service menu
├── build-aux/      packaging manifests
├── docs/           project documentation
│   └── ROADMAP.md  phased development plan
├── FUTURE.md       deferred ideas / scope-creep log
├── README.md       this file
├── LICENSE         MIT
└── .gitignore
```

## License

MIT — see `LICENSE`.

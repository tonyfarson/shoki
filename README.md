---
type: readme
status: active
project: shoki
created: 2026-08-13
updated: 2026-08-13
---

# Shoki

Shoki (書記, "scribe") is a GTK4/libadwaita desktop application that provides a graphical
control surface for a [whisper.cpp](https://github.com/ggml-org/whisper.cpp) transcription
server — and ships a Dolphin service menu that transcribes any audio or video file by
right-click, without opening the application at all.

Shoki does no transcription itself. It sends an audio file to a server you run, and shows
you what comes back.

> **Note:** This project is pre-release. There is no working application yet — Phase 0
> (scaffolding) and Phase 0.5 (scoping) are complete, and Phase 1 has not started. See
> `docs/ROADMAP.md` for the development plan.

## Status

- App ID: `com.farsononline.shoki`
- Platform: Linux only
- License: MIT
- Current phase: Phase 1 — Walking Skeleton (not started)
- First planned release: `v0.1.0`

Both native packages and a Flatpak are planned. The Dolphin service menu is a standalone
script that does not launch Shoki, which is what lets the Flatpak stay minimally
permissioned. Native packages get tighter integration — the script reads the application's
own settings — while the Flatpak's script falls back to its built-in defaults. See Phase 3
in `docs/ROADMAP.md`.

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

## Running from Source

Shoki is not installable yet. To run it from a checkout:

```
cd shoki
PYTHONPATH=src python -m shoki
```

An empty window titled Shoki should open. There is no application logic yet.

Runtime requirements (Arch/CachyOS package names):

```
python python-gobject gtk4 libadwaita
```

> **Note:** `PYTHONPATH=src` is a development convenience — the package is not installed to
> a location Python searches by default. Packaging in Phase 3 removes the need for it.

## Repository Layout

```
shoki/
├── src/shoki/      Python package (application code)
│   ├── __init__.py
│   ├── __main__.py     `python -m shoki` entry point
│   └── main.py         application and window classes
├── data/           icons, .desktop entry, appstream metadata,
│                   Dolphin service menu and helper script
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

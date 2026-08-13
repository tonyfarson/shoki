---
type: readme
status: active
project: shoki
created: 2026-08-13
updated: 2026-08-13
---

# Shoki

Shoki (書記, "scribe") is a GTK4/libadwaita desktop application that provides a
simple graphical frontend for a [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
transcription server.

Pick an audio file, click Transcribe, read the transcript. That is the whole idea.

> **Note:** This project is in Phase 0 (scaffolding). There is no working
> application yet. See `docs/ROADMAP.md` for the development plan.

## Status

- App ID: `com.farsononline.shoki`
- Platform: Linux only, packaged as a Flatpak
- License: MIT
- Current phase: Phase 0 — Scaffolding (window runs; git and GitHub outstanding)

## Requirements

Shoki is a client. It does not transcribe anything itself — it talks to a
whisper.cpp server that exposes the OpenAI-compatible transcription endpoint:

```
POST /v1/audio/transcriptions
```

Any whisper.cpp build serving that endpoint will work. The reference deployment
used during development runs the Vulkan container image:

```
ghcr.io/ggml-org/whisper.cpp:main-vulkan
```

Default endpoint assumed by the app:

```
http://localhost:8080/v1/audio/transcriptions
```

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

> **Note:** `PYTHONPATH=src` is a development convenience — the package is not installed to a
> location Python searches by default. Flatpak packaging in Phase 3 removes the need for it.

## Repository Layout

```
shoki/
├── src/shoki/      Python package (application code)
│   ├── __init__.py
│   ├── __main__.py     `python -m shoki` entry point
│   └── main.py         application and window classes
├── data/           icons, .desktop entry, appstream metadata
├── build-aux/      Flatpak manifest
├── docs/           project documentation
│   └── ROADMAP.md  phased development plan
├── FUTURE.md       deferred ideas / scope-creep log
├── README.md       this file
├── LICENSE         MIT
└── .gitignore
```

## License

MIT — see `LICENSE`.

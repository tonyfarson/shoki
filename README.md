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
server, and ships a Dolphin service menu that transcribes any audio or video file by
right-click, without opening the application at all.

Shoki does no transcription itself. It sends an audio file to a server you run, and shows
you what comes back.

> **Note:** This project is pre-release. It installs from a native package and is used daily
> by its author, but `v0.1.0` is not tagged yet and there is no Flatpak. See `docs/ROADMAP.md`.

## Status

- App ID: `com.farsononline.shoki`
- Platform: Linux only
- License: MIT
- Current phase: Phase 3 — Packaging. Native package complete and verified; Flatpak not started.
- First planned release: `v0.1.0`

The Dolphin service menu is a standalone script that never launches Shoki, which is what
lets a future Flatpak stay minimally permissioned. In the native package the script reads
Shoki's own GSettings, so one Preferences dialog governs both the application and the
right-click, and the two cannot drift. See Phase 3 in `docs/ROADMAP.md`.

## What It Does

- Transcribe a single file, a whole folder, or files dropped onto the window
- Right-click an audio or video file in Dolphin and send it straight to your server,
  without opening Shoki at all
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

## Installing

### Arch, CachyOS and derivatives

```
cd build-aux
makepkg
sudo pacman -U shoki-*.pkg.tar.zst
```

That installs the application, the `shoki-transcribe` helper, the Dolphin service menu, the
GSettings schema and the icons. Shoki appears in the application menu, and right-clicking an
audio or video file in Dolphin offers **Send to Whisper** at the top level of the context
menu — not buried under *Actions*.

The PKGBUILD builds the working tree rather than a released tarball, because `v0.1.0` is not
tagged yet. It is a local package, not an AUR submission.

Dependencies, all from the official repositories:

```
python python-gobject gtk4 libadwaita libsoup3 glib2 curl libnotify hicolor-icon-theme
```

`curl`, `glib2` and `libnotify` are there for the standalone helper rather than for the GUI —
the right-click has to keep working whether or not anyone ever opens Shoki. `xdg-user-dirs` is
an optional dependency; without it the default destination resolves to `~/Transcriptions`
instead of your XDG Documents folder.

### Other distributions

`.deb` and `.rpm` are planned but not written, and there is no Flatpak yet. Meson does the
install, so packaging elsewhere is a matter of wrapping two commands:

```
meson setup --prefix=/usr builddir
meson install -C builddir --destdir "$DESTDIR"
```

## Running from Source

To run from a checkout without installing anything:

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

> **Note:** `PYTHONPATH=src` and `GSETTINGS_SCHEMA_DIR` are development conveniences, needed
> only when running from a checkout — the package is not where Python searches, and the schema
> is not installed system-wide. Shoki falls back to built-in defaults when the schema is missing
> rather than crashing, but settings will not persist. Installing the package removes the need
> for both, and also puts the right-click helper on your `PATH`; running from source does not.

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

The Dolphin service menu reads these same keys at runtime with `gsettings get`, so changing
your endpoint, destination or output format in Preferences changes the right-click too. It
does not read the initial prompt, which is per-file and meaningless without someone to type
it. Preferences shows whether the right-click integration is present under **File manager
integration**.

## Repository Layout

```
shoki/
├── src/shoki/      Python package (application code)
│   ├── __init__.py
│   ├── __main__.py     `python -m shoki` entry point
│   ├── main.py         application, window, and preferences dialog
│   └── transcribe.py   request building and response parsing
├── data/
│   ├── com.farsononline.shoki.gschema.xml   GSettings schema
│   ├── com.farsononline.shoki.desktop       application menu entry
│   ├── shoki-transcribe.desktop             Dolphin service menu
│   ├── shoki-transcribe                     standalone helper script
│   └── icons/hicolor/                       app icon and symbolic icon
├── build-aux/
│   └── PKGBUILD    Arch package; makepkg is run from this directory
├── meson.build     build definition (src/ and data/ have their own)
├── docs/           project documentation
│   └── ROADMAP.md  phased development plan
├── FUTURE.md       deferred ideas / scope-creep log
├── README.md       this file
├── LICENSE         MIT
└── .gitignore
```

## License

MIT — see `LICENSE`.

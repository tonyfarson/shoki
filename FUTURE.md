---
type: backlog
status: active
project: shoki
created: 2026-08-13
updated: 2026-08-13
---

# Future Ideas

Scope-creep catcher. Any idea that is not in the current phase's scope gets logged
here with a date and a one-line description, then dropped. Nothing in this file is
a commitment.

> **Note:** Do not implement anything from this list without first moving it into
> `docs/ROADMAP.md` under a phase. This file is a parking lot, not a plan.

Items are grouped by whether they are wanted, blocked, or rejected. Reconciled against
`docs/ROADMAP.md` on 2026-08-13 at the close of Phase 0.5.

## Wanted — roadmap candidates after v0.1.0

### 2026-08-13 — Advanced parameters drawer

A collapsible panel exposing the decoding parameters the server accepts but the minimal interface
deliberately hides: `beam_size`, `best_of`, `temperature`, `temperature_inc`, `word_thold`,
`entropy_thold`, `logprob_thold`, `no_speech_thold`, `max_context`, `offset_t`, `offset_n`,
`duration`, `audio_ctx`, `token_timestamps`, `suppress_non_speech`, `suppress_nst`,
`carry_initial_prompt`.

> **Wanted, explicitly.** This is why Phase 1 requires the request builder to take a parameter dict
> rather than constructing fields inline. With that seam in place this costs a UI, not a rewrite.
> Deferred from v0.1.0 only to keep the first interface minimal.

### 2026-08-13 — Manual language override

A language selector for when auto-detect misfires.

> **Wanted.** `language` is a per-request field and is fully supported by the server, contrary to an
> earlier note in this file that deferred it as possibly unimplementable. That note came from the
> upstream README's incomplete parameter list. Auto-detect handles the common case; detection gets
> unreliable on short or noisy clips, which is what this is for. Belongs in the advanced drawer.

### 2026-08-13 — Upload percentage for the POST body

A true progress bar for the request upload, distinct from the impossible inference progress bar.

> **Deferred, not blocked** — pulled out of Phase 2 on 2026-08-13 by the author, on the grounds that
> it measures nothing worth watching when the server is on loopback. It was originally the reason the
> Phase 1 HTTP library had to support body-upload reporting.
>
> The capability survived the decision. `SoupMessage::wrote-body-data` emits the number of bytes
> written as the body goes out, so this remains an addition rather than a rewrite. Whether it fires
> repeatedly for a body supplied as a single `GBytes`, or only once at the end, has not been
> observed — check that before promising it.
>
> **Bring it back when:** Shoki is used from a machine other than the one running the server, over
> the tailnet, where a large file takes long enough that silence looks like a hang.

### 2026-08-13 — Batch queue interface

Per-file status, reordering, retry of individual failures, cancel remaining.

> Basic batch — point at a directory, transcribe everything, write outputs to a destination — is in
> Phase 2 and needs no server support. This is the richer interface on top of it.

### 2026-08-13 — Universal backend support (multi-server, model selection, API keys)

Selectable transcription backends, per-backend model choice, and an API key for services that
require one.

> whisper.cpp, speaches, and OpenAI all accept `multipart/form-data` with a `file` field but diverge
> on path, on `model` (required by the latter two, absent from whisper.cpp), on auth, and on the
> `response_format` set. Anything OpenAI-shaped is reachable by parameterising what Shoki already
> sends; anything else needs a per-backend adapter, and that is where universality stops being free.
>
> Blockers that cannot be designed around in advance: API keys must never go in `GSettings` — dconf
> is readable by anything in the session — so this needs libsecret, and the Secret portal under
> Flatpak. An app whose pitch is that audio stays on your own server also needs to be deliberate
> about offering to send that audio to a third party.

### 2026-08-13 — Local system monitoring

CPU, memory, and GPU utilisation shown while a transcription runs.

> **Wanted for enjoyment, not need** — stated plainly, which is a fine reason.
>
> One distinction decides whether this is honest. A gauge labelled "this machine" is always true and
> is easy: read local counters. A gauge labelled "the server" is a lie the moment Shoki is used from
> a laptop over Tailnet, because it would show the laptop idling while the server does the work.
>
> Doing it truthfully for a remote server means the server host exposes metrics — node_exporter,
> amdgpu telemetry, Prometheus — and Shoki becomes a monitoring client as well as a transcription
> client. That is a second application. Reading local `/sys/class/hwmon` also requires broad static
> filesystem permissions under Flatpak, where no portal for GPU telemetry exists.

### 2026-08-13 — "Open in Shoki" as a second service menu entry

A second Dolphin action that loads the file into the app rather than transcribing it silently.

> The v0 service menu deliberately does not launch Shoki — it transcribes and exits. This would be a
> separate menu entry for when the file needs different settings than the defaults. `GApplication`
> with a unique application ID and the `HANDLES_OPEN` flag routes a second launch's file arguments
> to the running instance over D-Bus, so this is cheap if wanted. Not v0.

## Blocked upstream

### 2026-08-13 — Progress percentage for a single file

> **Blocked.** Verified in `examples/server/server.cpp`: the handler calls
> `whisper_full_parallel(...)`, blocks until the entire file is done, then sends everything at once
> via `res.set_content(...)`. A `progress_callback` exists but writes only to stderr — it is never
> wired to the HTTP response. No SSE, no chunked encoding, no websockets.
>
> What v0 ships instead, all honest: elapsed-time counter, batch file counter, upload percentage,
> and `GET /health` liveness. See Phase 2.

### 2026-08-13 — Live "transcription in action" (streaming partial text)

> **Blocked.** Same root cause: the inference endpoint is request/response only.

### 2026-08-13 — Server-side cancellation

> **Blocked at the server, not the library.** `whisper_full_params` carries `abort_callback` and
> `encoder_begin_callback`, and `whisper.h` says of the latter: "If it returns false, the computation
> is aborted." The server example wires neither to anything client-facing and exposes no cancel
> route. Shoki's cancel therefore stops the client waiting; the server runs to completion and
> discards the result. Fixing this properly means patching the server.

### 2026-08-13 — Audio duration / ETA estimate

> Requires reading media duration (ffprobe or a tagging library) — a new dependency and a packaging
> entry — to estimate against a job whose progress cannot be measured. The elapsed-time counter in
> Phase 2 delivers most of the reassurance for zero dependencies.

### 2026-08-13 — Voice Activity Detection controls

> `vad` and six `vad_*` tuning fields are accepted per request, but the VAD model itself is a server
> startup flag (`-vm, --vad-model`). The Otachi container does not pass it, so these controls would
> fail until the server configuration changes. Blocked on server config, not on Shoki.

### 2026-08-13 — Model selection dropdown

> `POST /load` swaps the server's model, but no endpoint lists available models, so a dropdown cannot
> be populated. The path is server-side, so the user would type a container path. The swap is global
> — it yanks the model out from under every other client mid-flight. Loading a 1.6 GB model takes
> real time. Upstream warns that `/load` loads arbitrary server-side paths. Possible, genuinely hard,
> and hostile to a minimal interface.

## Rejected

### 2026-08-13 — Translate to a chosen target language

> **Not possible.** Whisper's translate task is source-to-English only; the model has no
> target-language parameter, and `-tr, --translate` is documented as "translate from source language
> to english". Other targets require a separate translation service entirely — a different product.

### 2026-08-13 — Cancel by restarting the Docker container

> **Rejected.** Reaching the container needs `docker.sock` (root-equivalent on the host), the Docker
> API over TCP (an unauthenticated root-equivalent daemon on a port), or SSH credentials. All three
> only work when the server is local, so they break over Tailnet exactly as the GPU gauge would. It
> also crosses the project's own scope line: the whisper.cpp server and Otachi's Docker stack belong
> to the Otachi project, not to Shoki. Arcane, already running on port 3552, is the tool built for
> this. Shoki detects the hang via `GET /health` and reports it; the user pulls the cord elsewhere.

### 2026-08-13 — Downloading the Dolphin integration at runtime

> **Rejected.** A button that fetches a script from GitHub and executes it — with or without sudo —
> is remote code execution by design, fails without a network, and bypasses package verification.
> The files are tiny and are bundled with the app instead. No sudo is needed either: Plasma reads
> service menus from `~/.local/share/kio/servicemenus/`, in the user's own home.

### 2026-08-13 — System tray icon and autostart

> **Rejected.** `GtkStatusIcon` was removed in GTK4 with no successor. A tray icon means implementing
> the freedesktop StatusNotifierItem D-Bus interface or depending on libayatana-appindicator; Plasma
> supports it natively, GNOME dropped it and needs a user-installed extension. It is also moot: the
> Dolphin service menu is a standalone script that never launches Shoki, so nothing needs to be
> resident.

### 2026-08-13 — Stepped wizard interface

> **Rejected in favour of a single vertically-scrolling page.** A transcript is a document you read,
> scroll, copy, save, and re-run with a tweaked prompt — not a task that ends in a completion screen.
> Splitting settings and results across screens makes the tweak-and-retry loop walk backwards through
> the flow. Vertical scrolling keeps the guided reading order while letting everything coexist.
> `Adw.Carousel` does support vertical orientation if this is ever revisited.

### 2026-08-13 — Accessibility options pane

> **Rejected as a feature, adopted as a standard.** Accessibility comes from accessible roles, real
> labels, full keyboard navigation, and respecting the system's contrast and text-size settings — all
> v0 requirements in Phase 2. A pane of accessibility toggles is usually evidence it was bolted on
> afterwards.

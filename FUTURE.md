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

## Logged Ideas

### 2026-08-13 — Universal backend support (multi-server, model selection, API keys)

Selectable transcription backends, per-backend model choice, and an API key for services that
require one.

> **Tracked in the roadmap, not here.** Full detail — candidate backends, the four axes of
> divergence, the Phase 1 decisions that keep this cheap, and the blockers that cannot be designed
> around — lives under Phase 0.5 in `docs/ROADMAP.md`. Do not duplicate the detail into this file;
> two copies will drift.

### 2026-08-13 — Progress indicator (processed vs. remaining)

Show how much of the audio has been transcribed and how much is left.

> **Blocked upstream.** whisper.cpp's server cannot do this. Verified in
> `examples/server/server.cpp`: the handler calls `whisper_full_parallel(...)`, blocks until the
> entire file is done, then sends everything at once via `res.set_content(...)`. A
> `progress_callback` exists but writes only to stderr — it is never wired to the HTTP response.
> No SSE, no chunked encoding, no websockets. The client receives nothing until completion.
> Implementing this requires patching the server, which is out of Shoki's scope.

### 2026-08-13 — Live "transcription in action" (streaming partial text)

Stream partial transcript text into the output pane as it is produced.

> **Blocked upstream.** Same root cause as above: the inference endpoint is request/response only.
> Would require server-side SSE or websocket support that does not exist.

### 2026-08-13 — GPU utilization and temperature gauges

Show live GPU load and temps while a transcription runs.

> **Not recommended — architecturally wrong for a thin client.** Three problems:
>
> 1. whisper.cpp exposes no telemetry endpoint. The only routes are the inference path, `/load`
>    and `/health`. Shoki would need an entirely separate metrics source on the server host.
> 2. Reading temps locally means `/sys/class/hwmon` or `/sys/class/drm/*/device/hwmon/*`. Flathub
>    requires that "static permissions must be kept to an absolute minimum" and mandates XDG
>    portals where they exist. There is no portal for GPU telemetry, so this needs broad static
>    filesystem access to power a decorative gauge — a submission risk.
> 3. It reports the wrong machine. Reading local sysfs only tells the truth when the server is on
>    localhost. Used from a laptop over Tailnet — the whole point of the thin-client design — the
>    gauge would show the laptop's idle GPU while the server does the work. A confidently wrong
>    gauge is worse than no gauge.
>
> Doing this correctly means the server host exposes metrics (node_exporter, amdgpu telemetry,
> Prometheus) and Shoki becomes a monitoring client as well as a transcription client. That is a
> second application, not a feature.

### 2026-08-13 — Per-request language selection

Language dropdown in the settings dialog, currently listed under Phase 2.

> **Verify before building.** whisper.cpp documents `--language` as a server startup option, not a
> request parameter. Documented request fields are only `file`, `temperature`, `temperature_inc`,
> `prompt`, `carry_initial_prompt`, `response_format`. A dropdown that silently does nothing is
> worse than no dropdown. Pending confirmation of the running server's actual behavior.

### 2026-08-13 — Audio duration / ETA estimate

Show elapsed time as a ratio against total audio length.

> Requires reading media duration (ffprobe or a tagging library) — a new dependency and a Flatpak
> manifest entry. The plain elapsed-time counter in Phase 2 delivers most of the reassurance for
> zero dependencies. Revisit only if the bare counter proves insufficient in daily use.

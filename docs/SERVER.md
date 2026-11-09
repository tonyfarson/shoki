---
type: reference
status: active
project: shoki
created: 2026-08-14
updated: 2026-08-14
---

# The whisper.cpp Server

Shoki is a client. It does no transcription: it sends a file to a
[whisper.cpp](https://github.com/ggml-org/whisper.cpp) server you run, and shows what comes back.

This file records what that server actually accepts and does. It was extracted from
the project's planning notes on 2026-08-14 — it is reference material about an external dependency, not a plan,
and it was the most re-read section in a document nobody could skim.

> **Scope.** The whisper.cpp server itself is not part of Shoki and is not maintained here. This
> file exists so that Shoki's behaviour can be justified against something observed rather than
> assumed. Anything wrong with the *server* belongs upstream.


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
`json` as the default fallback. The `json` reply is shaped `{"text": "..."}` — assumed while writing
Phase 1, then observed against the running server on 2026-08-13.

Input formats are a property of server *flags*, not of the API. The README states that "WAV Files are
passed to the inference model via http requests", and it is `--convert` — documented as "Convert
audio to WAV, requires ffmpeg on the server" — that admits anything else. The Otachi container passes
it, confirmed 2026-08-13 from its compose command, which is why mp3 and video files work there.

> **Warning:** Shoki cannot detect this. No route reports the server's startup flags. An unflagged
> whisper.cpp server accepts WAV only, so the file picker's audio-and-video filter is optimistic on
> anyone else's deployment. Phase 5's README must state the `--convert` requirement plainly.

`GET /health` answers normally while an inference is in flight — measured in Phase 1.

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
- **Cancellation works, and the client does stop the server.** Corrected 2026-08-14 — this entry
  previously said the server example "never wires either to anything client-facing" and that a client
  "cannot stop the server." Both halves were wrong. `examples/server/server.cpp` wires the abort to
  the HTTP connection state:

  ```cpp
  wparams.abort_callback = [](void *user_data) {
      auto req_ptr = static_cast<const httplib::Request*>(user_data);
      return req_ptr->is_connection_closed();
  };
  wparams.abort_callback_user_data = (void*)&req;
  ```

  Closing the connection therefore aborts the inference, and the server logs `client disconnected,
  aborted processing`. Confirmed on Otachi 2026-08-14 against
  `ghcr.io/ggml-org/whisper.cpp:main-vulkan`: GPU utilisation dropped the instant Cancel was clicked,
  and that line appeared in the container log. No cancel *route* exists, and none is needed — closing
  the socket is the mechanism.

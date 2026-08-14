"""Builds and sends transcription requests to a whisper.cpp server.

Nothing in this module knows that a GUI exists. Callers hand it a dict of
request parameters and a callback; it hands back a transcript or an error.
"""

import json
import os

import gi

gi.require_version("Soup", "3.0")

from gi.repository import GLib, Soup  # noqa: E402

DEFAULT_ENDPOINT = "http://127.0.0.1:8080/inference"

# The five literals server.cpp branches on. Anything else falls through to the
# json branch server-side, so Shoki never sends anything else.
RESPONSE_FORMATS = ("text", "srt", "vtt", "json", "verbose_json")

DEFAULT_RESPONSE_FORMAT = "text"

# What a saved transcript is called. Both JSON formats share one suffix; they
# differ in content, not in kind.
FILE_SUFFIXES = {
    "text": ".txt",
    "srt": ".srt",
    "vtt": ".vtt",
    "json": ".json",
    "verbose_json": ".json",
}

# Sent on every request unless the caller overrides it.
#
# Both entries are here for the same reason: server.cpp reads each form field
# under `if (req.has_file(name))`, so a field Shoki omits is not "the default" --
# it is the SERVER's default, which is not the same thing. It defaults to
# language=en and to response_format=json. Neither is what Shoki wants, so both
# have to be stated on every request rather than left off.
BASE_PARAMS = {
    "language": "auto",
    "response_format": DEFAULT_RESPONSE_FORMAT,
}


class TranscriptionError(Exception):
    """A failure worth showing a user. No stack traces in the UI."""


class TranscriptionCancelled(TranscriptionError):
    """The user cancelled. A subclass so that callers which have not yet
    learned to tell the two apart still behave sensibly."""

    def __init__(self):
        super().__init__("Transcription cancelled.")


def endpoint_problem(endpoint: str):
    """A human-readable reason this endpoint cannot work, or None if it can.

    Checked BEFORE a run starts rather than after it fails. Soup.Message.new()
    accepts far more than it can reach: "nonsense" yields a perfectly valid
    message object whose request then sits there, so the app shows a spinner and
    a counting timer for a job that can never complete. Observed 2026-08-14.
    The guard has to be ours.
    """
    if not endpoint.strip():
        return "No endpoint URL is set. Add one in Preferences."

    try:
        uri = GLib.Uri.parse(endpoint, GLib.UriFlags.NONE)
    except GLib.Error:
        return f"\u201c{endpoint}\u201d is not a usable endpoint URL. Fix it in Preferences."

    # "localhost:8080" parses, but as scheme "localhost" with path "8080".
    if uri.get_scheme() not in ("http", "https"):
        return f"\u201c{endpoint}\u201d is missing http:// or https://."

    if not uri.get_host():
        return f"\u201c{endpoint}\u201d has no server name in it."

    return None


def build_request(endpoint: str, file_path: str, params: dict) -> Soup.Message:
    """Assemble one multipart POST. Every form field comes from `params`."""

    try:
        with open(file_path, "rb") as handle:
            audio = GLib.Bytes.new(handle.read())
    except OSError as exc:
        # str(OSError) is "[Errno 13] Permission denied: '/path/x.mp3'" -- an
        # errno and a repr\'d path. strerror alone is the human half.
        raise TranscriptionError(
            f"Could not read {os.path.basename(file_path)}: "
            f"{exc.strerror or exc}"
        ) from exc

    multipart = Soup.Multipart.new("multipart/form-data")
    multipart.append_form_file(
        "file",
        os.path.basename(file_path),
        "application/octet-stream",
        audio,
    )

    for name, value in {**BASE_PARAMS, **params}.items():
        multipart.append_form_string(name, _as_form_value(value))

    message = Soup.Message.new("POST", endpoint)
    if message is None:
        raise TranscriptionError(
            f"\u201c{endpoint}\u201d is not a usable endpoint URL."
        )

    # to_message() writes Content-Type *including the multipart boundary* into
    # the message's headers, and hands back the serialised body.
    body = multipart.to_message(message.get_request_headers())

    # Passing None here is load-bearing, not laziness. libsoup's docs: "If
    # content_type is NULL and bytes is not NULL the Content-Type header will
    # not be changed if present." A string here would overwrite the boundary
    # that to_message() just set, and the server would reject the request.
    message.set_request_body_from_bytes(None, body)

    return message


def transcribe_async(session, endpoint, file_path, params, cancellable, on_done):
    """Send one file for transcription.

    `on_done(transcript, error)` is called later on the main thread. Exactly one
    of its two arguments is ever None. A cancelled request reports a
    TranscriptionCancelled rather than a silent no-op, so the caller decides how
    loudly to say so.
    """
    response_format = params.get("response_format", DEFAULT_RESPONSE_FORMAT)

    try:
        message = build_request(endpoint, file_path, params)
    except TranscriptionError as exc:
        # Deliver even immediate failures through the callback, never by raising.
        # A caller should not have to handle failure in two different shapes.
        _fail_later(on_done, exc)
        return

    session.send_and_read_async(
        message,
        GLib.PRIORITY_DEFAULT,
        cancellable,
        _on_response,
        (message, response_format, cancellable, on_done),
    )


def _on_response(session, result, user_data):
    """Runs on the main thread once the server has replied, or failed to."""
    message, response_format, cancellable, on_done = user_data

    try:
        body = session.send_and_read_finish(result)
    except GLib.Error as exc:
        # Ask the cancellable rather than decoding the GError's domain and code.
        # GCancellable.is_cancelled() is the documented question to ask, and it
        # keeps this free of guesses about error-quark spellings.
        if cancellable is not None and cancellable.is_cancelled():
            on_done(None, TranscriptionCancelled())
        else:
            on_done(None, TranscriptionError(f"Could not reach the server: {exc.message}"))
        return

    status = message.get_status()
    if status != Soup.Status.OK:
        reply = f"The server replied {int(status)} {message.get_reason_phrase()}."
        detail = _short_body(body)
        on_done(None, TranscriptionError(f"{reply} {detail}" if detail else reply))
        return

    try:
        on_done(_extract_transcript(body, response_format), None)
    except TranscriptionError as exc:
        on_done(None, exc)


def _extract_transcript(body, response_format: str) -> str:
    """Turn the response body into what the transcript view should display.

    Branches on the format that was REQUESTED, never on the reply's Content-Type.
    server.cpp labels the text branch "text/html; charset=utf-8", which is not a
    thing to trust or to render.

    Verified against examples/server/server.cpp, 2026-08-13:
      text          plain text, one segment per line, each prefixed with a space
      srt           application/x-subrip
      vtt           text/vtt, "WEBVTT" header first
      json          {"text": ...}
      verbose_json  {"task", "language", "duration", "text", "segments"}
    """
    raw = body.get_data() if body else b""
    if not raw:
        raise TranscriptionError("The server returned an empty response.")

    # Replacement, not strict. Whisper's tokenizer operates on BYTES, so a token
    # boundary can land mid-character and the server ships a truncated UTF-8
    # sequence. Verified 2026-08-13 on mixed English/Japanese audio: byte 1390 of
    # the reply was "e5 9c" followed by ASCII "r" -- the third byte of that
    # character does not exist anywhere in the payload. No client can repair it,
    # so failing the whole transcript over it would discard 2,400 good bytes to
    # protest one bad one. The U+FFFD that replaces it is visible in the output.
    decoded = raw.decode("utf-8", errors="replace")

    if response_format in ("json", "verbose_json"):
        # Shown verbatim -- someone who picks a machine format wants the document,
        # not a sentence pulled out of it. Parsed only to fail clearly on garbage.
        try:
            json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise TranscriptionError("The server's reply was not valid JSON.") from exc
        return decoded

    if response_format == "text":
        return _reflow(decoded)

    # srt and vtt are structured by line. Touching that whitespace breaks them.
    return decoded.strip("\n")


def _reflow(text: str) -> str:
    """Rejoin Whisper's one-segment-per-line text into paragraphs.

    The leading space on each line is an instruction, not noise. Whisper's
    tokenizer marks a word-initial token with a leading space, so a segment that
    begins WITHOUT one is the continuation of the word the previous segment ended
    on -- the newline landed mid-word. Observed 2026-08-13 against a real
    transcript: "God\'s kings" / "hip over them", "eight-year-" / "olds",
    "our way" / ", the right way". Stripping every line and joining on spaces
    turns those into "kings hip", "eight-year- olds" and "our way ,".

    So: a line that starts with whitespace is appended after a space, and a line
    that does not is appended flush against what came before. Blank lines, if the
    model ever emits any, are kept as paragraph breaks.
    """
    paragraphs = []
    current = ""

    for line in text.splitlines():
        piece = line.strip()

        if not piece:
            if current:
                paragraphs.append(current)
                current = ""
            continue

        if not current:
            current = piece
        elif line[0].isspace():
            current += " " + piece
        else:
            current += piece

    if current:
        paragraphs.append(current)

    return "\n\n".join(paragraphs)


def _short_body(body, limit: int = 160) -> str:
    """A trimmed single-line excerpt of an error body, or an empty string.

    Servers say useful things in error bodies -- a wrong path returns a 404 with
    a reason. They also sometimes return an entire HTML page, so this is
    flattened and capped rather than shown whole.
    """
    raw = body.get_data() if body else b""
    if not raw:
        return ""

    text = " ".join(raw.decode("utf-8", errors="replace").split())
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit] + "\u2026"


def _as_form_value(value) -> str:
    """Form fields are strings on the wire. Booleans need an explicit spelling.

    Verified against examples/server/server.cpp, 2026-08-13. parse_str_to_bool()
    accepts "true", "1", "yes" and "y"; everything else is false. Each field is
    read under `if (req.has_file(name))`, so omitting a field leaves the server's
    own default rather than clearing it.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _fail_later(on_done, error):
    """Report a failure through the main loop, so the callback is always async."""

    def deliver():
        on_done(None, error)
        return GLib.SOURCE_REMOVE

    GLib.idle_add(deliver)

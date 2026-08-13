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

# Sent on every request unless the caller overrides them.
#   language=auto         the server defaults to English; auto-detect is not free
#   response_format=json  the format most likely to port to another backend
BASE_PARAMS = {
    "language": "auto",
    "response_format": "json",
}


class TranscriptionError(Exception):
    """A failure worth showing a user. No stack traces in the UI."""


def build_request(endpoint: str, file_path: str, params: dict) -> Soup.Message:
    """Assemble one multipart POST. Every form field comes from `params`."""

    with open(file_path, "rb") as handle:
        audio = GLib.Bytes.new(handle.read())

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
        raise TranscriptionError(f"Not a usable endpoint URL: {endpoint}")

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
    of its two arguments is ever None.
    """
    try:
        message = build_request(endpoint, file_path, params)
    except (OSError, TranscriptionError) as exc:
        # Deliver even immediate failures through the callback, never by raising.
        # A caller should not have to handle failure in two different shapes.
        _fail_later(on_done, TranscriptionError(str(exc)))
        return

    session.send_and_read_async(
        message,
        GLib.PRIORITY_DEFAULT,
        cancellable,
        _on_response,
        (message, on_done),
    )


def _on_response(session, result, user_data):
    """Runs on the main thread once the server has replied, or failed to."""
    message, on_done = user_data

    try:
        body = session.send_and_read_finish(result)
    except GLib.Error as exc:
        on_done(None, TranscriptionError(f"Could not reach the server: {exc.message}"))
        return

    status = message.get_status()
    if status != Soup.Status.OK:
        on_done(
            None,
            TranscriptionError(
                f"The server replied {int(status)} {message.get_reason_phrase()}."
            ),
        )
        return

    try:
        on_done(_extract_transcript(body), None)
    except TranscriptionError as exc:
        on_done(None, exc)


def _extract_transcript(body) -> str:
    """Pull the transcript out of a response_format=json reply.

    ASSUMPTION, unverified as of 2026-08-13: the reply is JSON shaped
    {"text": "..."}. Not yet read in server.cpp. If it is wrong, this raises a
    clear message rather than crashing, and Phase 1 will tell us the real shape.
    """
    raw = body.get_data() if body else b""
    if not raw:
        raise TranscriptionError("The server returned an empty response.")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TranscriptionError("The server's reply was not valid JSON.") from exc

    text = payload.get("text")
    if text is None:
        raise TranscriptionError("The server's reply contained no 'text' field.")
    return text.strip()


def _as_form_value(value) -> str:
    """Form fields are strings on the wire. Booleans need an explicit spelling.

    ASSUMPTION: whisper.cpp reads booleans as the literal "true"/"false".
    Phase 1 sends no booleans, so this is unexercised. Confirm against
    server.cpp before Phase 2 sends translate= or no_timestamps=.
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

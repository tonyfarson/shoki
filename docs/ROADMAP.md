# Shoki Roadmap

Where Shoki is and where it is going. This page is short on purpose; the detailed planning is kept
privately. Nothing here is a promise of a date.

## Where it stands

- **Works today:** transcribe a file, a folder or dropped files against your own whisper.cpp server;
  five output formats; translate to English; batch runs; cancel; a Dolphin right-click that
  transcribes without opening the app.
- **Installs from:** an Arch package, a `.deb` and an `.rpm` (built from this repository).
- **Not yet:** a Flatpak, a tagged `v0.1.0`, support for file managers other than Dolphin.

## Next

1. Tag `v0.1.0` and publish the packages.
2. A Flatpak.
3. A friendlier first run: say clearly whether the server is down or the endpoint path is wrong.
4. Hosted transcription services as well as your own server, with API keys kept in the system
   keyring. Sending audio to a third party will always be an explicit choice.
5. Packages in the official repositories of the major distributions, starting with the AUR.

## Under consideration

- Windows and macOS. Reaching them may mean changing the toolkit; that decision has not been made.
- Other file managers (Nautilus, Thunar, Nemo).

## Not planned

- Doing the transcription inside Shoki. It stays a client for a server you choose.
- Translating into languages other than English; Whisper does not support it.

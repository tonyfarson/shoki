# Shoki — Fedora/RPM packaging.
#
# Meson does the install, so this spec is thin. It deliberately mirrors the
# decisions already made in debian/control rather than inventing new ones.
#
# Development loop (no tarball needed):
#   cd ~/shoki && rpmbuild -bb --build-in-place --noclean build-aux/shoki.spec
#
# --build-in-place skips %prep and points the build directory at the current
# working directory, which is the RPM analogue of "dpkg-buildpackage -b".
# Phase 6 replaces this with a real tarball build from a tagged release.

Name:           shoki
Version:        0.1.0
Release:        1%{?dist}
Summary:        Graphical control surface for a whisper.cpp transcription server

License:        MIT
URL:            https://github.com/tonyfarson/shoki
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  meson >= 0.59.0
BuildRequires:  ninja-build
BuildRequires:  desktop-file-utils
BuildRequires:  glib2

# Unlike Debian, Fedora ships GObject introspection typelibs inside the main
# library package rather than in separate gir1.2-* packages, so gtk4 and
# libadwaita are named directly. Verified for gtk4 on Fedora 44.
Requires:       python3
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       libsoup3
Requires:       glib2
Requires:       curl
Requires:       file
Requires:       libnotify

%description
Shoki is a GTK4/libadwaita desktop application that sends audio and video files
to a whisper.cpp server and saves the transcripts it returns. It puts the
server's request parameters -- output format, translation, initial prompt,
subtitle tuning -- behind a single window instead of a command line.

A standalone helper, shoki-transcribe, is installed alongside it, together with
a KDE service menu so that files can be transcribed by right-click from Dolphin.
The helper never launches the application and reads its settings at runtime, so
the two share one configuration and cannot drift apart.

Shoki does not include a transcription engine. It requires a reachable
whisper.cpp server, which it treats as an external HTTP service.

%prep
# Intentionally empty: builds are driven by --build-in-place during development.
# Phase 6 restores %autosetup here when Source0 becomes a real tagged tarball.

%build
%meson
%meson_build

%install
%meson_install

%check
%meson_test

%files
%license LICENSE
%doc README.md
%{_bindir}/shoki
%{_bindir}/shoki-transcribe
%{_datadir}/applications/com.farsononline.shoki.desktop
%{_datadir}/glib-2.0/schemas/com.farsononline.shoki.gschema.xml
%{_datadir}/icons/hicolor/scalable/apps/com.farsononline.shoki.svg
%{_datadir}/icons/hicolor/symbolic/apps/com.farsononline.shoki-symbolic.svg
%{_datadir}/kio/servicemenus/shoki-transcribe.desktop
%{_datadir}/shoki/

%changelog
* Sat Aug 15 2026 Tony Farson <ajfarson@gmail.com> - 0.1.0-1
- Initial RPM packaging.

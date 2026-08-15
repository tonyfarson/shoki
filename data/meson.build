install_data(
  'com.farsononline.shoki.gschema.xml',
  install_dir: datadir / 'glib-2.0' / 'schemas',
)

desktop_file = files('com.farsononline.shoki.desktop')

install_data(
  desktop_file,
  install_dir: datadir / 'applications',
)

# The Dolphin service menu and its helper.
#
# shoki-transcribe.desktop is deliberately NOT passed to desktop-file-validate.
# KDE service menus sit outside the freedesktop spec: Type=Service is a KDE
# extension, and the validator rejects MimeType and Actions as "only valid for
# type Application". A correct service menu therefore fails validation, so only
# the application .desktop is checked.
#
# No executable bit on the .desktop: /usr/share is system data and already
# authorised. That requirement applies to unauthorised user locations such as a
# Get-Hot-New-Stuff install under ~/.local/share.
install_data(
  'shoki-transcribe.desktop',
  install_dir: datadir / 'kio' / 'servicemenus',
)

# The helper is standalone: it never launches Shoki and knows nothing about any
# file manager. It lives in data/ beside the service menu that invokes it, but
# installs to bindir because shoki-transcribe.desktop calls it by bare name.
install_data(
  'shoki-transcribe',
  install_dir: bindir,
  install_mode: 'rwxr-xr-x',
)

# Icons. Two SVGs, not a ladder of PNGs: GNOME's HIG asks for one full-colour
# icon drawn in a 128x128 area plus one symbolic version, and the source tree
# mirrors the installed hicolor layout so the mapping is obvious.
install_data(
  'icons/hicolor/scalable/apps/@0@.svg'.format(app_id),
  install_dir: datadir / 'icons' / 'hicolor' / 'scalable' / 'apps',
)

install_data(
  'icons/hicolor/symbolic/apps/@0@-symbolic.svg'.format(app_id),
  install_dir: datadir / 'icons' / 'hicolor' / 'symbolic' / 'apps',
)

# Validation runs as tests rather than as build steps, so a missing validator
# never blocks a build — but `meson test` proves both files against their
# reference implementations rather than against anyone's recollection of the spec.
desktop_file_validate = find_program('desktop-file-validate', required: false)
if desktop_file_validate.found()
  test('desktop-file', desktop_file_validate, args: [desktop_file])
endif

glib_compile_schemas = find_program('glib-compile-schemas', required: false)
if glib_compile_schemas.found()
  test(
    'gschema',
    glib_compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()],
  )
endif

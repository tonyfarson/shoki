# Shoki — build and install definition.
#
# No language is declared, deliberately: Shoki is pure Python, so Meson must not
# demand a C compiler just to install some files.

project(
  'shoki',
  version: '0.1.0',
  license: 'MIT',
  meson_version: '>= 0.59.0',
)

gnome = import('gnome')

app_id = 'com.farsononline.shoki'

prefix     = get_option('prefix')
bindir     = prefix / get_option('bindir')
datadir    = prefix / get_option('datadir')
pkgdatadir = datadir / meson.project_name()

subdir('src')
subdir('data')

# Refreshes the caches an installed app depends on. Meson skips these when
# DESTDIR is set, which is exactly what packaging needs — makepkg always sets it,
# and the package's own hooks do the refresh on the user's machine instead.
gnome.post_install(
  glib_compile_schemas: true,
  update_desktop_database: true,
  gtk_update_icon_cache: true,
)

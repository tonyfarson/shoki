# The launcher. PKGDATADIR is baked in at configure time so the installed script
# knows where its package lives without guessing or reading the environment.
launcher_conf = configuration_data()
launcher_conf.set('PKGDATADIR', pkgdatadir)

configure_file(
  input: 'shoki.in',
  output: 'shoki',
  configuration: launcher_conf,
  install: true,
  install_dir: bindir,
  install_mode: 'rwxr-xr-x',
)

# Listed explicitly rather than globbed: a new module is a deliberate one-line
# edit here, and __pycache__ can never be installed by accident.
install_data(
  files(
    'shoki/__init__.py',
    'shoki/__main__.py',
    'shoki/main.py',
    'shoki/transcribe.py',
  ),
  install_dir: pkgdatadir / 'shoki',
)

# Tests

The tests start the real program (`--local`, from this repository). The
program writes `~/.openastro.org`, so `HOME` must point to a scratch
directory; the tools refuse to run with a `HOME` outside `/tmp`.

The golden chart set and the flows of the Qt window need no display (Qt runs
offscreen). The flows and the smoke test of the GTK dialogs (not yet ported
to Qt) need one and are skipped without.

```
# everything (each in a fresh home)
xvfb-run python3 -m unittest discover -s tests -v

# render the golden chart set, e.g. to compare two versions byte by byte
HOME=$(mktemp -d) python3 tests/golden.py /tmp/golden-new
diff -r /tmp/golden-old /tmp/golden-new

# Qt main window: menus, quick open, wheel and lists, chart types, zoom,
# tables, export, print, chart files, database export/import, light and dark
HOME=$(mktemp -d) python3 tests/qt_flows.py

# GTK dialog flows: event data, home location, event database, settings, tables
HOME=$(mktemp -d) xvfb-run python3 tests/flows.py

# GTK smoke test: opens every dialog via the window actions, records exceptions
HOME=$(mktemp -d) xvfb-run python3 tests/smoke.py /tmp/smoke.json
```

Without `xvfb-run`: `Xvfb :99 &` and `DISPLAY=:99 GDK_BACKEND=x11 GSK_RENDERER=cairo`.

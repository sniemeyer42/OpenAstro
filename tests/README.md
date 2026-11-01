# Tests

The tests start the real program (`--local`, from this repository). The
program writes `~/.openastro.org`, so `HOME` must point to a scratch
directory; the tools refuse to run with a `HOME` outside `/tmp`.

No display is needed: the golden chart set draws without user interface,
the Qt program runs offscreen.

```
# everything (each in a fresh home)
python3 -m unittest discover -s tests -v

# render the golden chart set, e.g. to compare two versions byte by byte
HOME=$(mktemp -d) python3 tests/golden.py /tmp/golden-new
diff -r /tmp/golden-old /tmp/golden-new

# Qt program: menus, quick open, wheel and lists, chart types, zoom, tables,
# export, print, chart files, database export/import, Here and Now (time
# bar, mouse wheel, steps, clock), event dialog, event
# database, famous people, home location, configuration, aspects, planets,
# font size of the lists, light and dark
HOME=$(mktemp -d) python3 tests/qt_flows.py
```

To watch the Qt program instead of running it offscreen, set
`QT_QPA_PLATFORM=xcb` (or `wayland`).

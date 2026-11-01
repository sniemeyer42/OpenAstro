# Tests

The tests start the real program (`--local`, from this repository) and need a
display. The program writes `~/.openastro.org`, so `HOME` must point to a
scratch directory; the tools refuse to run with a `HOME` outside `/tmp`.

```
# everything (golden chart set, dialog flows, GUI smoke test, each in a fresh home)
xvfb-run python3 -m unittest discover -s tests -v

# render the golden chart set, e.g. to compare two versions byte by byte
HOME=$(mktemp -d) xvfb-run python3 tests/golden.py /tmp/golden-new
diff -r /tmp/golden-old /tmp/golden-new

# dialog flows: event data, home location, event database, settings, tables
HOME=$(mktemp -d) xvfb-run python3 tests/flows.py

# GUI smoke test: opens every dialog via the window actions, records exceptions
HOME=$(mktemp -d) xvfb-run python3 tests/smoke.py /tmp/smoke.json
```

Without `xvfb-run`: `Xvfb :99 &` and `DISPLAY=:99 GDK_BACKEND=x11 GSK_RENDERER=cairo`.

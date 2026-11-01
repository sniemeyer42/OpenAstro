#!/usr/bin/env python3
#    This file is part of openastro.org.
#
#    OpenAstro.org is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    OpenAstro.org is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with OpenAstro.org.  If not, see <http://www.gnu.org/licenses/>.
"""
GUI smoke test, driven only through the window actions and button labels:
every step activates an action, optionally clicks a button of the new
window and closes all new windows. Python exceptions are recorded.

	HOME=$(mktemp -d) xvfb-run python3 tests/smoke.py [RESULT.json]
"""
import os
import sys
import json
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import start_application

# (name, window action, action target, label of the button to click)
STEPS = [
	('about', 'about', None, None),
	('event data', 'eventData', None, 'Cancel'),
	('new chart', 'newChart', None, None),
	('open database', 'openDatabase', None, None),
	('famous', 'openDataFamous', None, None),
	('location', 'settingsLocation', None, 'Cancel'),
	('configuration', 'settingsConfiguration', None, None),
	('configuration ok', 'settingsConfiguration', None, 'OK'),
	('aspects', 'settingsAspects', None, 'Cancel'),
	('aspects ok', 'settingsAspects', None, 'OK'),
	('planets', 'settingsPlanets', None, 'Cancel'),
	('planets ok', 'settingsPlanets', None, 'OK'),
	('radix', 'specialRadix', None, None),
	('transit', 'specialTransit', None, None),
	('synastry select', 'chartType', 'Synastry', None),
	('composite select', 'chartType', 'Composite', None),
	('combine select', 'chartType', 'Combine', None),
	('solar', 'specialSolar', None, None),
	('solar ok', 'specialSolar', None, 'OK'),
	('radix again', 'specialRadix', None, None),
	('progression', 'specialProgression', None, None),
	('progression ok', 'specialProgression', None, 'OK'),
	('radix again 2', 'specialRadix', None, None),
	('timeline month', 'tableMonthlyTimeline', None, 'Cancel'),
	('timeline', 'tableMonthlyTimeline', None, 'OK'),
	('cusp aspects', 'tableCuspAspects', None, None),
	('zoom in', 'zoom', 'zIn', None),
	('zoom out', 'zoom', 'zOut', None),
	('zoom 80', 'zoom', 'z80', None),
	('zoom 150', 'zoom', 'z150', None),
	('zoom 200', 'zoom', 'z200', None),
	('zoom 100', 'zoom', 'z100', None),
	('maximize', 'maximize', None, None),
	('maximize again', 'maximize', None, None),
]

def main(result_file):
	exceptions = []
	def hook(t, v, tb):
		exceptions.append(''.join(traceback.format_exception(t, v, tb)))
		sys.__excepthook__(t, v, tb)
	sys.excepthook = hook
	app, run = start_application(steps_after_ms=2500)
	from gi.repository import GLib, Gtk
	import builtins
	results = []
	state = {'i': 0, 'before': set(), 'exc': 0}

	def toplevels():
		model = Gtk.Window.get_toplevels()
		return [model.get_item(i) for i in range(model.get_n_items())]

	def new_windows():
		windows = [w for w in toplevels() if id(w) not in state['before'] and w.get_visible()]
		#libadwaita dialogs (Adw.Dialog) are shown inside the main window
		dialog = main_window().get_visible_dialog() if hasattr(main_window(), 'get_visible_dialog') else None
		return windows + ([dialog] if dialog is not None else [])

	def main_window():
		return [w for w in toplevels() if isinstance(w, Gtk.ApplicationWindow)][0]

	def find_buttons(widget, label):
		labels = (label, builtins._(label), '_' + builtins._(label))
		out = []
		child = widget.get_first_child()
		while child is not None:
			if isinstance(child, Gtk.Button) and not isinstance(child, Gtk.CheckButton) and child.get_label() in labels:
				out.append(child)
			out += find_buttons(child, label)
			child = child.get_next_sibling()
		return out

	def start_step():
		if state['i'] >= len(STEPS):
			GLib.timeout_add(300, finish)
			return False
		name, action, target, click = STEPS[state['i']]
		state['before'] = set(id(w) for w in toplevels())
		state['exc'] = len(exceptions)
		try:
			main_window().activate_action('win.' + action, None if target is None else GLib.Variant('s', target))
		except Exception:
			exceptions.append(traceback.format_exc())
		GLib.timeout_add(700, click_step)
		return False

	def click_step():
		name, action, target, click = STEPS[state['i']]
		new = new_windows()
		clicked = None
		if click:
			for w in new:
				buttons = find_buttons(w, click)
				if buttons:
					buttons[0].emit('clicked')
					clicked = w.get_title()
					break
		results.append({'step': name, 'new': sorted(str(w.get_title()) for w in new), 'clicked': clicked})
		GLib.timeout_add(700, close_step)
		return False

	def close_step():
		for w in new_windows():
			if hasattr(w, 'force_close'):
				w.force_close()
			else:
				w.close()
		GLib.timeout_add(400, end_step)
		return False

	def end_step():
		for w in new_windows():
			if hasattr(w, 'force_close'):
				w.force_close()
			else:
				w.close()
		r = results[-1]
		r['exceptions'] = [e.strip().split('\n')[-1] for e in exceptions[state['exc']:]]
		print('%-18s new=%s clicked=%s exceptions=%s' % (r['step'], r['new'], r['clicked'], r['exceptions']), flush=True)
		state['i'] += 1
		GLib.timeout_add(200, start_step)
		return False

	def finish():
		if result_file:
			with open(result_file, 'w') as f:
				json.dump({'results': results, 'exceptions': exceptions}, f, indent=1)
		print('smoke: %d steps, %d exceptions' % (len(results), len(exceptions)), flush=True)
		app.exit_code = 1 if exceptions else 0
		app.quit()
		return False

	return run(lambda app: start_step())

if __name__ == '__main__':
	sys.exit(main(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else None))

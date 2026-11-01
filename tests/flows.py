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
Functional test of the dialog flows (offline geonames database): event data,
home location, event database (add, edit, delete, open, select as second
event), aspect and planet settings, solar return, progression, timeline.
Confirmation dialogs are answered with OK.

	HOME=$(mktemp -d) xvfb-run python3 tests/flows.py
"""
import os
import sys
import sqlite3
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import start_application

results = []
def check(name, ok, info=''):
	results.append((name, bool(ok)))
	print(('PASS ' if ok else 'FAIL ') + name + ('  ' + str(info)[:300] if info != '' else ''), flush=True)

def main():
	exceptions = []
	def hook(t, v, tb):
		exceptions.append(''.join(traceback.format_exception(t, v, tb)))
		sys.__excepthook__(t, v, tb)
	sys.excepthook = hook
	app, run = start_application(steps_after_ms=2500)
	from gi.repository import GLib, Gtk
	import builtins
	T = lambda s: builtins._(s)

	class Confirm:
		"""stand-in for Gtk.AlertDialog that answers OK at once"""
		def __init__(self, *args, **kwargs): pass
		def set_message(self, *a): pass
		def set_detail(self, *a): pass
		def set_modal(self, *a): pass
		def set_buttons(self, *a): pass
		def choose(self, parent=None, cancellable=None, callback=None, user_data=None):
			callback(self, None, user_data)
		def choose_finish(self, result):
			return 1
	Gtk.AlertDialog = Confirm

	def toplevels():
		model = Gtk.Window.get_toplevels()
		return [model.get_item(i) for i in range(model.get_n_items())]

	def find(title):
		ws = [w for w in toplevels() if w.get_visible() and w.get_title() == title]
		return ws[-1] if ws else None

	def buttons(widget, label):
		labels = (label, T(label), '_' + T(label))
		out = []
		child = widget.get_first_child()
		while child is not None:
			if isinstance(child, Gtk.Button) and not isinstance(child, Gtk.CheckButton) and child.get_label() in labels:
				out.append(child)
			out += buttons(child, label)
			child = child.get_next_sibling()
		return out

	def click(window, label):
		b = buttons(window, label)
		assert b, 'no button %s in %s' % (label, window.get_title())
		b[0].emit('clicked')

	def widgets(widget, cls):
		out = []
		child = widget.get_first_child()
		while child is not None:
			if isinstance(child, cls):
				out.append(child)
			out += widgets(child, cls)
			child = child.get_next_sibling()
		return out

	def people():
		l = sqlite3.connect(app.cfg.peopledb)
		r = l.execute('SELECT id, name, location FROM event_natal ORDER BY id').fetchall()
		l.close()
		return r

	def chooser_of(window):
		for attr in ('chooser',):
			if hasattr(window, attr):
				return getattr(window, attr)
		return None

	def flow(app):
		win = app.window
		chart = app.chart
		app.db.setAstrocfg('use_geonames.org', '0') if hasattr(app.db, 'setAstrocfg') else None
		# ---- event dialog: search a city, OK
		win.activate_action('win.eventData', None)
		d = find(T('Edit Event Details'))
		check('event dialog open', d is not None)
		ch = chooser_of(d)
		check('event dialog offline city chooser', ch is not None)
		d.citysearch.set_text('Hamburg, DE')
		click(d, 'Search')
		d.name.set_text('Flow Test')
		d.dateY.set_value(1985); d.dateM.set_value(3); d.dateD.set_value(20)
		d.timeH.set_value(9); d.timeM.set_value(0); d.timeS.set_value(0)
		history_before = len(app.db.history)
		click(d, 'OK')
		check('event OK: chart name/place', chart.name == 'Flow Test' and 'Hamburg' in chart.location, (chart.name, chart.location))
		check('event OK: local date', (chart.year_loc, chart.month_loc, chart.day_loc, chart.hour_loc) == (1985, 3, 20, 9), (chart.year_loc, chart.month_loc, chart.day_loc, chart.hour_loc))
		check('event OK: closed', not d.get_visible())
		check('event OK: history entry', len(app.db.history) >= min(history_before + 1, 10), (history_before, len(app.db.history)))
		# ---- lists of the side bar (data of the calculated chart)
		from astrochart.chart.data import houseOf
		rows = chart.bodyRows()
		check('lists: shown bodies', len(rows) == len([p for p in chart.planets if p['visible'] == 1]) > 10, len(rows))
		houses = chart.houseRows()
		check('lists: 12 house cusps', [h['house'] for h in houses] == list(range(1, 13)))
		check('lists: houses of the bodies', all(houseOf(chart.houses_degree_ut[r['house'] - 1], chart.houses_degree_ut) == r['house'] for r in rows))
		aspects = chart.aspectRows()
		orbs = {a['degree']: a['orb'] for a in chart.aspects}
		check('lists: aspects sorted by orb within orb', aspects and all(a['orb'] <= orbs[a['degree']] + 1e-9 for a in aspects)
			and [a['orb'] for a in aspects] == sorted(a['orb'] for a in aspects), len(aspects))
		check('lists: side bar filled', win.panels.boxes['aspects'].get_first_child() is not None)
		# ---- add to database
		win.activate_action('win.eventData', None)
		d = find(T('Edit Event Details'))
		before = people()
		click(d, 'Add to Database')
		after = people()
		check('add to database', len(after) == len(before) + 1 and after[-1][1] == 'Flow Test', after[-1:])
		entry_id = after[-1][0]
		# duplicate name refused
		win.activate_action('win.eventData', None)
		d = find(T('Edit Event Details'))
		click(d, 'Add to Database')
		dup = find(T('Found Duplicate'))
		check('duplicate name refused', dup is not None and len(people()) == len(after))
		if dup:
			dup.close()
		d.close()
		# ---- home location from the geonames database
		win.activate_action('win.settingsLocation', None)
		d = find(T('Please Set Your Home Location'))
		ch = chooser_of(d)
		check('location dialog chooser', ch is not None)
		ch.search('Berlin, DE')
		click(d, 'OK')
		l = sqlite3.connect(app.cfg.astrodb)
		home = l.execute("SELECT value FROM astrocfg WHERE name='home_location'").fetchone()[0]
		l.close()
		check('home location saved', 'Berlin' in home and 'Berlin' in chart.home_location, (home, chart.home_location))
		check('location dialog closed', not d.get_visible())
		# ---- database: edit the entry without renaming, then delete
		win.activate_action('win.openDatabase', None)
		od = find(T('Open Database Entry'))
		check('database window', od is not None)
		sel = [w for w in widgets(od, Gtk.ColumnView)][0].get_model()
		ids = [int(sel.get_item(i).id) for i in range(sel.get_n_items())]
		sel.set_selected(ids.index(entry_id))
		click(od, 'Edit')
		ed = find(T('Edit Event Details'))
		check('edit dialog', ed is not None)
		ed.citysearch.set_text('Munich, DE')
		click(ed, 'Search')
		click(ed, 'Save')
		row = [p for p in people() if p[0] == entry_id]
		check('edit saved without rename', row and row[0][1] == 'Flow Test' and ('Munich' in row[0][2] or 'München' in row[0][2]), row)
		check('edit dialog closed', not ed.get_visible())
		for w in [w for w in toplevels() if w.get_visible() and w.get_title() == T('Open Database Entry')]:
			w.close()
		# ---- select the entry as partner for a synastry
		win.activate_action('win.chartType', GLib.Variant('s', 'Synastry'))
		sd = find(T('Select Database Entry'))
		check('select window', sd is not None)
		sel = [w for w in widgets(sd, Gtk.ColumnView)][0].get_model()
		ids = [int(sel.get_item(i).id) for i in range(sel.get_n_items())]
		sel.set_selected(ids.index(entry_id))
		click(sd, 'Select for Synastry')
		check('synastry chart', chart.type == 'Transit' and chart.synastry and chart.t_name == 'Flow Test', (chart.type, chart.synastry, getattr(chart, 't_name', None)))
		check('synastry lists: partner side', chart.bodyRows(transit=True) and all(a['second']['transit'] for a in chart.aspectRows()))
		# ---- delete
		win.activate_action('win.openDatabase', None)
		od = find(T('Open Database Entry'))
		sel = [w for w in widgets(od, Gtk.ColumnView)][0].get_model()
		ids = [int(sel.get_item(i).id) for i in range(sel.get_n_items())]
		sel.set_selected(ids.index(entry_id))
		click(od, 'Delete')
		check('entry deleted', entry_id not in [p[0] for p in people()])
		for w in [w for w in toplevels() if w.get_visible() and w.get_title() == T('Open Database Entry')]:
			w.close()
		# ---- aspect settings: invalid orb is refused, valid orb saved
		win.activate_action('win.specialRadix', None)
		win.activate_action('win.settingsAspects', None)
		d = find(T('Aspect Settings'))
		entries = widgets(d, Gtk.Entry)
		entries[0].set_text('x')
		click(d, 'Apply')
		check('invalid orb refused', 'error' in entries[0].get_css_classes() and d.get_visible())
		entries[0].set_text('7,5')
		click(d, 'OK')
		check('orb saved', app.db.getSettingsAspect('radix')[0]['orb'] == 7.5 and not d.get_visible(), app.db.getSettingsAspect('radix')[0]['orb'])
		# ---- planet settings: radix chiron off
		win.activate_action('win.settingsPlanets', None)
		d = find(T('Planets & Angles Settings'))
		checks = widgets(d, Gtk.CheckButton)
		state = checks[0].get_active()
		checks[0].set_active(not state)
		click(d, 'OK')
		check('planet setting saved', app.db.getSettingsPlanet('radix')[0]['visible'] == int(not state))
		# ---- solar return and progression with the default values
		win.activate_action('win.specialSolar', None)
		d = [w for w in toplevels() if w.get_visible() and w.get_title() == T('Select year for Solar Return')][-1]
		click(d, 'OK')
		check('solar return', chart.type == 'Solar', chart.type)
		win.activate_action('win.specialProgression', None)
		d = [w for w in toplevels() if w.get_visible() and w.get_title() == T('Enter Date')][-1]
		click(d, 'OK')
		check('progression', chart.type == 'SecondaryProgression', chart.type)
		# ---- timeline window
		win.activate_action('win.specialRadix', None)
		win.activate_action('win.tableMonthlyTimeline', None)
		d = find(T('Select Month in Year'))
		click(d, 'OK')
		tw = find('OpenAstro.org Monthly Timeline')
		check('timeline window', tw is not None)
		if tw:
			tw.close()
		check('no exceptions', not exceptions, [e.strip().split('\n')[-1] for e in exceptions])
		fails = [n for n, ok in results if not ok]
		print('flows: %d checks, %d failed' % (len(results), len(fails)), flush=True)
		app.exit_code = 1 if fails else 0
		app.quit()

	return run(flow)

if __name__ == '__main__':
	sys.exit(main())

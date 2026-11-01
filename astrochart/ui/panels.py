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
Side bar of the main window: positions, houses, aspects and data of the
chart as native lists
"""

from gi.repository import Adw, GLib, Gtk, Pango
from astrochart.chart.data import formatDegree
from astrochart.constants import HOUSE_SYSTEMS

def label(text, xalign=0.0, css=None, ellipsize=False):
	widget = Gtk.Label(label=text, xalign=xalign)
	if css:
		for name in css.split():
			widget.add_css_class(name)
	if ellipsize:
		widget.set_ellipsize(Pango.EllipsizeMode.END)
		widget.set_hexpand(True)
	return widget

def table():
	grid = Gtk.Grid(column_spacing=10, row_spacing=4)
	return grid

def heading(text):
	widget = label(text, css='heading')
	widget.set_margin_top(12)
	widget.set_margin_bottom(4)
	return widget

def page(child):
	"""scrolled page with margins"""
	box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
	box.set_margin_start(12)
	box.set_margin_end(12)
	box.set_margin_bottom(12)
	box.append(child)
	scrolled = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
	scrolled.set_child(box)
	return scrolled, box

class ChartPanels(Gtk.Box):
	"""switchable pages: positions, houses, aspects, info"""

	PAGES = (('positions', 'view-list-symbolic'), ('houses', 'go-home-symbolic'),
		('aspects', 'insert-link-symbolic'), ('info', 'dialog-information-symbolic'))

	def __init__(self, window, symbols):
		super().__init__(orientation=Gtk.Orientation.VERTICAL)
		self.window = window
		self.chart = window.chart
		self.symbols = symbols
		self.stack = Adw.ViewStack(vexpand=True)
		titles = {'positions': _('Positions'), 'houses': _('Houses'), 'aspects': _('Aspects'), 'info': _('Info')}
		self.boxes = {}
		for name, icon in self.PAGES:
			scrolled, box = page(Gtk.Box())
			self.boxes[name] = box
			self.stack.add_titled_with_icon(scrolled, name, titles[name], icon)
		switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.NARROW)
		switcher.set_margin_top(6)
		switcher.set_margin_bottom(6)
		self.append(switcher)
		self.append(self.stack)

	def clear(self, name):
		box = self.boxes[name]
		child = box.get_first_child()
		while child is not None:
			next_child = child.get_next_sibling()
			box.remove(child)
			child = next_child
		return box

	def update(self):
		"""fill the pages from the calculated chart"""
		self.scale = self.window.get_scale_factor()
		self.updatePositions()
		self.updateHouses()
		self.updateAspects()
		self.updateInfo()

	def picture(self, name, size=20):
		return self.symbols.picture(name, size, self.scale)

	def updatePositions(self):
		box = self.clear('positions')
		chart = self.chart
		sides = [(_('Radix'), chart.bodyRows())]
		if chart.type == "Transit":
			sides.append((_('Partner') if chart.synastry else _('Transit'), chart.bodyRows(transit=True)))
		for title, rows in sides:
			if len(sides) > 1:
				box.append(heading(title))
			grid = table()
			for line, row in enumerate(rows):
				grid.attach(self.picture(row['symbol']), 0, line, 1, 1)
				grid.attach(label(row['label'], ellipsize=True), 1, line, 1, 1)
				grid.attach(self.picture(row['sign'], 16), 2, line, 1, 1)
				grid.attach(label(row['degree'], xalign=1.0, css='numeric'), 3, line, 1, 1)
				grid.attach(label('℞' if row['retrograde'] else '', css='dim-label'), 4, line, 1, 1)
				grid.attach(label('%s' % row['house'], xalign=1.0, css='dim-label numeric'), 5, line, 1, 1)
			box.append(grid)
		#elements of the radix
		box.append(heading(_('Elements')))
		grid = table()
		for line, (key, text, percent) in enumerate(chart.elementRows()):
			grid.attach(label(text), 0, line, 1, 1)
			bar = Gtk.LevelBar(min_value=0, max_value=100, value=percent, hexpand=True, valign=Gtk.Align.CENTER)
			grid.attach(bar, 1, line, 1, 1)
			grid.attach(label('%d%%' % percent, xalign=1.0, css='numeric'), 2, line, 1, 1)
		box.append(grid)

	def updateHouses(self):
		box = self.clear('houses')
		grid = table()
		grid.set_margin_top(8)
		for line, row in enumerate(self.chart.houseRows()):
			grid.attach(label('%s %s' % (self.chart.label['cusp'], row['house']), ellipsize=True), 0, line, 1, 1)
			grid.attach(self.picture(row['sign'], 16), 1, line, 1, 1)
			grid.attach(label(row['degree'], xalign=1.0, css='numeric'), 2, line, 1, 1)
		box.append(grid)

	def updateAspects(self):
		box = self.clear('aspects')
		rows = self.chart.aspectRows()
		box.append(heading('%s (%d)' % (_('Aspects'), len(rows))))
		grid = table()
		for line, row in enumerate(rows):
			first, second = row['first'], row['second']
			grid.attach(self.picture(first['symbol'], 18), 0, line, 1, 1)
			grid.attach(self.picture('orb%s' % row['degree'], 14), 1, line, 1, 1)
			grid.attach(self.picture(second['symbol'], 18), 2, line, 1, 1)
			names = '%s %s %s' % (first['label'], row['name'], second['label'])
			grid.attach(label(names, ellipsize=True), 3, line, 1, 1)
			grid.attach(label(formatDegree(row['orb'], seconds=False), xalign=1.0, css='numeric dim-label'), 4, line, 1, 1)
		box.append(grid)

	def updateInfo(self):
		box = self.clear('info')
		chart = self.chart
		group = Adw.PreferencesGroup()
		group.set_margin_top(8)
		cfg = chart.db.astrocfg
		date = '%s-%02d-%02d %02d:%02d:%02d %s' % (chart.year_loc, chart.month_loc, chart.day_loc,
			chart.hour_loc, chart.minute_loc, chart.second_loc, chart.decTzStr(chart.timezone))
		postype = {"geo": chart.label["apparent_geocentric"], "truegeo": chart.label["true_geocentric"],
			"topo": chart.label["topocentric"], "helio": chart.label["heliocentric"]}
		zodiac = _("Sidereal") + ' (%s)' % cfg['siderealmode'] if cfg['zodiactype'] == 'sidereal' else _("Tropical")
		lunar = chart.lunar_phase
		rows = [
			(chart.charttype, str(chart.name)),
			(date, chart.location),
			('%s · %s' % (chart.lat2str(chart.geolat), chart.lon2str(chart.geolon)), '%s / %s' % (chart.label['latitude'], chart.label['longitude'])),
			(postype.get(cfg['postype'], cfg['postype']), _('Position Calculation')),
			(zodiac, _('Zodiac Type')),
			(HOUSE_SYSTEMS.get(cfg['houses_system'], cfg['houses_system']), _('Houses System')),
			('%s (%s) · %s (%s) · %s' % (lunar['sun_phase'], _('Sun'), lunar['moon_phase'], _('Moon'),
				formatDegree(lunar['degrees'])), _('Lunar Phase')),
		]
		for title, subtitle in rows:
			row = Adw.ActionRow(title=GLib.markup_escape_text(str(title)), subtitle=GLib.markup_escape_text(str(subtitle)))
			row.add_css_class('property')
			group.add(row)
		box.append(group)


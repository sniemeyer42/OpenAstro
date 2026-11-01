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
Dialog 'Settings > Planets & Angles': shown bodies per chart type
"""

from gi.repository import Gtk
from astrochart.constants import ASPECT_CHART_TYPES, PLANET_DEFAULT_VISIBLE, PLANET_FIRST_ANGLE, PLANET_FIRST_POINT, PLANET_TRANSIT_HIDDEN
from astrochart.ui.dialog import AstroDialog
from astrochart.util import aspectFlag, dprint

class PlanetSettingsDialog(AstroDialog):
	"""one notebook page per chart type, check boxes per body"""

	def __init__(self, window):
		super().__init__(window, title=_("Planets & Angles Settings"), transient_for=window, modal=True)
		self.set_default_size(420,-1)
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
		vbox.set_spacing(8)
		vbox.props.margin_start = 16
		vbox.props.margin_end = 16
		vbox.props.margin_top = 16
		vbox.props.margin_bottom = 16
		#check boxes (planet setting, header): radix with symbol, aspect line and
		#aspect grid, transit and synastry per side
		columns = {
			'radix': [('visible', _('Symbol')), ('visible_aspect_line', _('Aspect Line')),
				('visible_aspect_grid', _('Aspect Grid'))],
			'transit': [('visible', _('Radix')), ('visible_transit', _('Transit'))],
			'synastry': [('visible', _('Radix')), ('visible_transit', _('Partner'))]
			}
		titles = {'radix':_('Radix'), 'transit':_('Transit'), 'synastry':_('Synastry')}
		self.notebook = Gtk.Notebook(vexpand=True)
		self.data = {}
		self.saved = {}
		for ctype in ASPECT_CHART_TYPES:
			grid = Gtk.Grid()
			grid.set_column_spacing(16)
			grid.set_row_spacing(2)
			grid.props.margin_start = 12
			grid.props.margin_end = 12
			grid.props.margin_top = 12
			grid.props.margin_bottom = 12
			rows = []
			saved = []
			line = 0
			for planet in self.db.getSettingsPlanet(ctype):
				pid = planet['id']
				#header above planets, angles and sensitive points
				if line == 0 or pid in (PLANET_FIRST_ANGLE, PLANET_FIRST_POINT):
					if pid >= PLANET_FIRST_POINT:
						text = _('Point Label')
					elif pid >= PLANET_FIRST_ANGLE:
						text = _('Angle Label')
					else:
						text = _('Planet Label')
					label = Gtk.Label(label=text, xalign=0)
					label.add_css_class('heading')
					if line > 0:
						label.set_margin_top(10)
					grid.attach(label, 0, line, 1, 1)
					for col, (key, header) in enumerate(columns[ctype], start=1):
						label = Gtk.Label(label=header, justify=Gtk.Justification.CENTER)
						if line > 0:
							label.set_margin_top(10)
						grid.attach(label, col, line, 1, 1)
					line += 1
				grid.attach(Gtk.Label(label=planet['label'], xalign=0), 0, line, 1, 1)
				widgets = {'id': pid}
				values = {'id': pid}
				for col, (key, header) in enumerate(columns[ctype], start=1):
					values[key] = aspectFlag(planet[key], 0)
					widgets[key] = Gtk.CheckButton(halign=Gtk.Align.CENTER)
					widgets[key].set_active(values[key] == 1)
					grid.attach(widgets[key], col, line, 1, 1)
				rows.append(widgets)
				saved.append(values)
				line += 1
			self.data[ctype] = rows
			self.saved[ctype] = saved
			scrolled_window = Gtk.ScrolledWindow()
			scrolled_window.set_vexpand(True)
			scrolled_window.set_propagate_natural_height(True)
			scrolled_window.set_max_content_height(560)
			scrolled_window.set_child(grid)
			self.notebook.append_page(scrolled_window, Gtk.Label(label=titles[ctype]))
		vbox.append(self.notebook)
		#open the page of the chart shown
		self.notebook.set_current_page(self.chartTypePage(self.chart))
		#buttons, window manager close button, cancel and ok all end in close-request
		vbox.append(self.buttonRow([
			(_("Default"), self.default),
			(_("Cancel"), self.close),
			(_("Apply"), lambda: self.submit(close=False)),
			(_("OK"), lambda: self.submit(close=True))]))
		self.set_child(vbox)

	def default(self):
		#reset the widgets of the current page only, saved with apply or ok
		ctype = ASPECT_CHART_TYPES[self.notebook.get_current_page()]
		for widgets in self.data[ctype]:
			pid = widgets['id']
			for key, check in widgets.items():
				if key == 'id':
					continue
				value = PLANET_DEFAULT_VISIBLE[pid] if pid < len(PLANET_DEFAULT_VISIBLE) else 0
				if key == 'visible_transit' and ctype == 'transit' and pid in PLANET_TRANSIT_HIDDEN:
					value = 0
				check.set_active(value == 1)

	def submit(self, close=True):
		changed = []
		for ctype in ASPECT_CHART_TYPES:
			new = []
			for widgets in self.data[ctype]:
				values = {'id': widgets['id']}
				for key, check in widgets.items():
					if key != 'id':
						values[key] = int(check.get_active())
				new.append(values)
			if new != self.saved[ctype]:
				dprint('PlanetSettingsDialog.submit: saving %s planets' % (ctype))
				self.db.setSettingsPlanet(ctype, new)
				self.saved[ctype] = new
				changed.append(ctype)
		if changed:
			self.window.refreshChart()
			#open timeline uses the transit planet settings
			self.window.refreshTableWindows(changed)
		if close:
			self.close()

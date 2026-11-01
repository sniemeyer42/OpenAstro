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
Menu 'Settings': shown bodies per chart type
"""

from gi.repository import Gtk
from astrochart.constants import ASPECT_CHART_TYPES, PLANET_DEFAULT_VISIBLE, PLANET_FIRST_ANGLE, PLANET_FIRST_POINT, PLANET_TRANSIT_HIDDEN
from astrochart.state import app
from astrochart.util import aspectFlag, dprint

class PlanetSettingsMixin:
	"""Menu 'Settings': shown bodies per chart type"""

	"""
	Menu item to set the shown bodies per chart type:
		setPlanets_callback
		settingsPlanetsDefault
		settingsPlanetsSubmit
		settingsPlanetsClose
	"""
	def setPlanets_callback(self, action, parameter):
		#only one planet settings window
		if getattr(self, 'win_SP', None) is not None:
			self.win_SP.present()
			return
		self.win_SP = Gtk.Window(title=_("Planets & Angles Settings"), transient_for=self, modal=True)
		self.win_SP.set_default_size(420,-1)
		#window manager close button, cancel and ok all end in close-request
		self.win_SP.connect('close-request', self.settingsPlanetsClose)
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
		vbox.set_spacing(8)
		vbox.props.margin_start = 16
		vbox.props.margin_end = 16
		vbox.props.margin_top = 16
		vbox.props.margin_bottom = 16
		#one notebook page per chart type, check boxes (planet setting, header):
		#radix like the Gtk3 planet settings, transit and synastry per side
		columns = {
			'radix': [('visible', _('Symbol')), ('visible_aspect_line', _('Aspect Line')),
				('visible_aspect_grid', _('Aspect Grid'))],
			'transit': [('visible', _('Radix')), ('visible_transit', _('Transit'))],
			'synastry': [('visible', _('Radix')), ('visible_transit', _('Partner'))]
			}
		titles = {'radix':_('Radix'), 'transit':_('Transit'), 'synastry':_('Synastry')}
		self.planetsNotebook = Gtk.Notebook(vexpand=True)
		self.planetsData = {}
		self.planetsSaved = {}
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
			for planet in app.db.getSettingsPlanet(ctype):
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
			self.planetsData[ctype] = rows
			self.planetsSaved[ctype] = saved
			scrolled_window = Gtk.ScrolledWindow()
			scrolled_window.set_vexpand(True)
			scrolled_window.set_propagate_natural_height(True)
			scrolled_window.set_max_content_height(560)
			scrolled_window.set_child(grid)
			self.planetsNotebook.append_page(scrolled_window, Gtk.Label(label=titles[ctype]))
		vbox.append(self.planetsNotebook)
		#open the page of the chart shown
		if app.type == "Transit":
			if app.synastry:
				self.planetsNotebook.set_current_page(ASPECT_CHART_TYPES.index('synastry'))
			else:
				self.planetsNotebook.set_current_page(ASPECT_CHART_TYPES.index('transit'))
		else:
			self.planetsNotebook.set_current_page(ASPECT_CHART_TYPES.index('radix'))
		#buttons
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_homogeneous(True)
		button_box.set_spacing(8)
		button = Gtk.Button.new_with_mnemonic(label=_("Default"))
		button.connect("clicked", self.settingsPlanetsDefault)
		button_box.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_("Cancel"))
		button.connect("clicked", lambda w: self.win_SP.close())
		button_box.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_("Apply"))
		button.connect("clicked", lambda w: self.settingsPlanetsSubmit(close=False))
		button_box.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_("OK"))
		button.connect("clicked", lambda w: self.settingsPlanetsSubmit(close=True))
		button_box.append(button)
		vbox.append(button_box)
		self.win_SP.set_child(vbox)
		self.win_SP.present()

	def settingsPlanetsDefault(self, widget):
		#reset the widgets of the current page only, saved with apply or ok
		ctype = ASPECT_CHART_TYPES[self.planetsNotebook.get_current_page()]
		for widgets in self.planetsData[ctype]:
			pid = widgets['id']
			for key, check in widgets.items():
				if key == 'id':
					continue
				value = PLANET_DEFAULT_VISIBLE[pid] if pid < len(PLANET_DEFAULT_VISIBLE) else 0
				if key == 'visible_transit' and ctype == 'transit' and pid in PLANET_TRANSIT_HIDDEN:
					value = 0
				check.set_active(value == 1)

	def settingsPlanetsSubmit(self, close=True):
		changed = []
		for ctype in ASPECT_CHART_TYPES:
			new = []
			for widgets in self.planetsData[ctype]:
				values = {'id': widgets['id']}
				for key, check in widgets.items():
					if key != 'id':
						values[key] = int(check.get_active())
				new.append(values)
			if new != self.planetsSaved[ctype]:
				dprint('settingsPlanetsSubmit: saving %s planets' % (ctype))
				app.db.setSettingsPlanet(ctype, new)
				self.planetsSaved[ctype] = new
				changed.append(ctype)
		if changed:
			#keep zoom level
			scale = self.image.scale
			self.updateChart()
			self.image.scale = scale
			#open timeline uses the transit planet settings
			self.settingsAspectsTables(changed)
		if close:
			self.win_SP.close()

	def settingsPlanetsClose(self, window):
		#forget the window, gtk destroys it after this handler
		self.win_SP = None
		self.planetsData = {}
		self.planetsSaved = {}
		return False

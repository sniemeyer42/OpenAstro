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
Menu 'Settings': aspects per chart type
"""

import math
import os
import locale
from gi.repository import Gtk
from astrochart.constants import ASPECT_CHART_TYPES, ASPECT_DEFAULTS, ASPECT_DEGREES, ASPECT_ORB_MAX
from astrochart.state import app
from astrochart.util import dprint

class AspectSettingsMixin:
	"""Menu 'Settings': aspects per chart type"""

	"""
	Menu item to set the aspects (line, grid, orb) per chart type:
		setAspects_callback
		settingsAspectsDefault
		settingsAspectsSubmit
		settingsAspectsClose
	"""
	def setAspects_callback(self, action, parameter):
		#only one aspect settings window
		if getattr(self, 'win_SA', None) is not None:
			self.win_SA.present()
			return
		self.win_SA = Gtk.Window(title=_("Aspect Settings"), transient_for=self, modal=True)
		self.win_SA.set_default_size(560,-1)
		#window manager close button, cancel and ok all end in close-request
		self.win_SA.connect('close-request', self.settingsAspectsClose)
		#create a VBox
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
		vbox.set_spacing(8)
		vbox.props.margin_start = 16
		vbox.props.margin_end = 16
		vbox.props.margin_top = 16
		vbox.props.margin_bottom = 16
		#one notebook page per aspect set
		self.aspectsNotebook = Gtk.Notebook(vexpand=True)
		self.aspectsData = {}
		self.aspectsSaved = {}
		titles = {'radix':_('Radix'), 'transit':_('Transit'), 'synastry':_('Synastry')}
		for ctype in ASPECT_CHART_TYPES:
			grid = Gtk.Grid()
			grid.set_column_spacing(12)
			grid.set_row_spacing(4)
			grid.props.margin_start = 12
			grid.props.margin_end = 12
			grid.props.margin_top = 12
			grid.props.margin_bottom = 12
			header = ['', _('Deg'), _('Aspect Name'), _('Visible\nin Circle'), _('Visible\nin Grid'), _('Orb')]
			for col, text in enumerate(header):
				grid.attach(Gtk.Label(label=text, justify=Gtk.Justification.CENTER), col, 0, 1, 1)
			rows = []
			saved = []
			for row, aspect in enumerate(app.db.getSettingsAspect(ctype), start=1):
				icon = Gtk.Image.new_from_file(os.path.join(app.cfg.iconAspects, '%s.svg' % (aspect['degree'])))
				icon.set_pixel_size(16)
				widgets = {'degree': aspect['degree']}
				widgets['visible'] = Gtk.CheckButton(halign=Gtk.Align.CENTER)
				widgets['visible'].set_active(aspect['visible'] == 1)
				widgets['visible_grid'] = Gtk.CheckButton(halign=Gtk.Align.CENTER)
				widgets['visible_grid'].set_active(aspect['visible_grid'] == 1)
				#orb as text like the Gtk3 programs: accepts decimal point and comma,
				#invalid input is marked instead of silently saved as 0
				orb = aspect['orb']
				widgets['orb'] = Gtk.Entry()
				widgets['orb'].set_width_chars(6)
				widgets['orb'].set_max_length(6)
				widgets['orb'].set_alignment(1.0)
				widgets['orb'].set_input_purpose(Gtk.InputPurpose.NUMBER)
				widgets['orb'].set_text(self.aspectOrbText(orb))
				line = [icon, Gtk.Label(label='%s°' % (aspect['degree']), xalign=1),
					Gtk.Label(label=aspect['name'], xalign=0), widgets['visible'], widgets['visible_grid'], widgets['orb']]
				for col, widget in enumerate(line):
					grid.attach(widget, col, row, 1, 1)
				rows.append(widgets)
				saved.append({'degree':aspect['degree'], 'visible':aspect['visible'],
					'visible_grid':aspect['visible_grid'], 'orb':orb})
			self.aspectsData[ctype] = rows
			self.aspectsSaved[ctype] = saved
			scrolled_window = Gtk.ScrolledWindow()
			scrolled_window.set_vexpand(True)
			#show all aspects without scrolling if the screen allows
			scrolled_window.set_propagate_natural_height(True)
			scrolled_window.set_child(grid)
			self.aspectsNotebook.append_page(scrolled_window, Gtk.Label(label=titles[ctype]))
		vbox.append(self.aspectsNotebook)
		#open the page of the chart shown
		if app.type == "Transit":
			if app.synastry:
				self.aspectsNotebook.set_current_page(ASPECT_CHART_TYPES.index('synastry'))
			else:
				self.aspectsNotebook.set_current_page(ASPECT_CHART_TYPES.index('transit'))
		else:
			self.aspectsNotebook.set_current_page(ASPECT_CHART_TYPES.index('radix'))
		#buttons
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_homogeneous(True)
		button_box.set_spacing(8)
		button = Gtk.Button.new_with_mnemonic(label=_("Default"))
		button.connect("clicked", self.settingsAspectsDefault)
		button_box.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_("Cancel"))
		button.connect("clicked", lambda w: self.win_SA.close())
		button_box.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_("Apply"))
		button.connect("clicked", lambda w: self.settingsAspectsSubmit(close=False))
		button_box.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_("OK"))
		button.connect("clicked", lambda w: self.settingsAspectsSubmit(close=True))
		button_box.append(button)
		vbox.append(button_box)
		self.win_SA.set_child(vbox)
		self.win_SA.present()

	def settingsAspectsDefault(self, widget):
		#reset the widgets of the current page only, saved with apply or ok
		ctype = ASPECT_CHART_TYPES[self.aspectsNotebook.get_current_page()]
		default = ASPECT_DEFAULTS[ctype]
		for widgets in self.aspectsData[ctype]:
			i = ASPECT_DEGREES.index(widgets['degree'])
			widgets['visible'].set_active(default['visible'][i] == 1)
			widgets['visible_grid'].set_active(default['visible_grid'][i] == 1)
			widgets['orb'].set_text(self.aspectOrbText(default['orb'][i]))
			widgets['orb'].remove_css_class('error')

	def aspectOrbText(self, orb):
		#orb with up to two decimals and the decimal point of the locale
		text = ('%.2f' % (orb)).rstrip('0').rstrip('.')
		return text.replace('.', locale.localeconv()['decimal_point'])

	def aspectOrbParse(self, text, saved):
		#orb from the entry (decimal point or comma), None if invalid,
		#an unchanged orb keeps its stored value (no rounding of untouched data)
		try:
			orb = float(text.strip().replace(',', '.'))
		except ValueError:
			return None
		if not math.isfinite(orb) or orb < 0:
			return None
		if round(orb, 2) == round(saved, 2):
			return saved
		if orb > ASPECT_ORB_MAX:
			return None
		return round(orb, 2)

	def settingsAspectsSubmit(self, close=True):
		new = {}
		invalid = []
		for ctype in ASPECT_CHART_TYPES:
			rows = []
			for i, widgets in enumerate(self.aspectsData[ctype]):
				orb = self.aspectOrbParse(widgets['orb'].get_text(), self.aspectsSaved[ctype][i]['orb'])
				if orb is None:
					widgets['orb'].add_css_class('error')
					if ctype not in invalid:
						invalid.append(ctype)
				else:
					widgets['orb'].remove_css_class('error')
				rows.append({'degree':widgets['degree'],
					'visible':int(widgets['visible'].get_active()),
					'visible_grid':int(widgets['visible_grid'].get_active()),
					'orb':orb})
			new[ctype] = rows
		if invalid:
			#nothing is saved, show the first page with an invalid orb
			dprint('settingsAspectsSubmit: invalid orb in %s' % (invalid))
			self.aspectsNotebook.set_current_page(ASPECT_CHART_TYPES.index(invalid[0]))
			return
		changed = []
		for ctype in ASPECT_CHART_TYPES:
			if new[ctype] != self.aspectsSaved[ctype]:
				dprint('settingsAspectsSubmit: saving %s aspects' % (ctype))
				app.db.setSettingsAspect(ctype, new[ctype])
				self.aspectsSaved[ctype] = new[ctype]
				changed.append(ctype)
		if changed:
			#keep zoom level
			scale = self.image.scale
			self.updateChart()
			self.image.scale = scale
			self.settingsAspectsTables(changed)
		if close:
			self.win_SA.close()

	def settingsAspectsTables(self, changed):
		#redraw open table windows with the changed aspect sets, the table
		#of self.tabletype is drawn last (shared temp file and page count)
		tables = []
		if 'transit' in changed:
			tables.append('timeline')
		if 'radix' in changed:
			tables.append('cuspaspects')
		tables.sort(key=lambda t: t == getattr(self, 'tabletype', None))
		for table in tables:
			if table == 'timeline':
				window = getattr(self, 'win_TMT', None)
				if window is None or not window.get_visible():
					continue
				app.makeTimelineSVG(printing=None, y=self.tMT_year, m=self.tMT_month)
			else:
				window = getattr(self, 'win_TCA', None)
				if window is None or not window.get_visible():
					continue
				app.makeCuspAspectsSVG(printing=None)
			window.image.setupSVG(app.cfg.tempfilenametable)
			window.image.queue_resize()

	def settingsAspectsClose(self, window):
		#forget the window, gtk destroys it after this handler
		self.win_SA = None
		self.aspectsData = {}
		self.aspectsSaved = {}
		return False

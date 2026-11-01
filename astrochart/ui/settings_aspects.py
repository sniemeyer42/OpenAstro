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
Dialog 'Settings > Aspects': aspects (line, grid, orb) per chart type
"""

import math
import os
import locale
from gi.repository import Gtk
from astrochart.constants import ASPECT_CHART_TYPES, ASPECT_DEFAULTS, ASPECT_DEGREES, ASPECT_ORB_MAX
from astrochart.ui.dialog import AstroDialog
from astrochart.util import dprint

def aspectOrbText(orb):
	#orb with up to two decimals and the decimal point of the locale
	text = ('%.2f' % (orb)).rstrip('0').rstrip('.')
	return text.replace('.', locale.localeconv()['decimal_point'])

def aspectOrbParse(text, saved):
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

class AspectSettingsDialog(AstroDialog):
	"""one notebook page per aspect set (radix, transit, synastry)"""

	def __init__(self, window):
		super().__init__(window, title=_("Aspect Settings"), transient_for=window, modal=True)
		self.set_default_size(560,-1)
		#create a VBox
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
		vbox.set_spacing(8)
		vbox.props.margin_start = 16
		vbox.props.margin_end = 16
		vbox.props.margin_top = 16
		vbox.props.margin_bottom = 16
		#one notebook page per aspect set
		self.notebook = Gtk.Notebook(vexpand=True)
		self.data = {}
		self.saved = {}
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
			for row, aspect in enumerate(self.db.getSettingsAspect(ctype), start=1):
				icon = Gtk.Image.new_from_file(os.path.join(self.cfg.iconAspects, '%s.svg' % (aspect['degree'])))
				icon.set_pixel_size(16)
				widgets = {'degree': aspect['degree']}
				widgets['visible'] = Gtk.CheckButton(halign=Gtk.Align.CENTER)
				widgets['visible'].set_active(aspect['visible'] == 1)
				widgets['visible_grid'] = Gtk.CheckButton(halign=Gtk.Align.CENTER)
				widgets['visible_grid'].set_active(aspect['visible_grid'] == 1)
				#orb as text: accepts decimal point and comma,
				#invalid input is marked instead of silently saved as 0
				orb = aspect['orb']
				widgets['orb'] = Gtk.Entry()
				widgets['orb'].set_width_chars(6)
				widgets['orb'].set_max_length(6)
				widgets['orb'].set_alignment(1.0)
				widgets['orb'].set_input_purpose(Gtk.InputPurpose.NUMBER)
				widgets['orb'].set_text(aspectOrbText(orb))
				line = [icon, Gtk.Label(label='%s°' % (aspect['degree']), xalign=1),
					Gtk.Label(label=aspect['name'], xalign=0), widgets['visible'], widgets['visible_grid'], widgets['orb']]
				for col, widget in enumerate(line):
					grid.attach(widget, col, row, 1, 1)
				rows.append(widgets)
				saved.append({'degree':aspect['degree'], 'visible':aspect['visible'],
					'visible_grid':aspect['visible_grid'], 'orb':orb})
			self.data[ctype] = rows
			self.saved[ctype] = saved
			scrolled_window = Gtk.ScrolledWindow()
			scrolled_window.set_vexpand(True)
			#show all aspects without scrolling if the screen allows
			scrolled_window.set_propagate_natural_height(True)
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
		default = ASPECT_DEFAULTS[ctype]
		for widgets in self.data[ctype]:
			i = ASPECT_DEGREES.index(widgets['degree'])
			widgets['visible'].set_active(default['visible'][i] == 1)
			widgets['visible_grid'].set_active(default['visible_grid'][i] == 1)
			widgets['orb'].set_text(aspectOrbText(default['orb'][i]))
			widgets['orb'].remove_css_class('error')

	def submit(self, close=True):
		new = {}
		invalid = []
		for ctype in ASPECT_CHART_TYPES:
			rows = []
			for i, widgets in enumerate(self.data[ctype]):
				orb = aspectOrbParse(widgets['orb'].get_text(), self.saved[ctype][i]['orb'])
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
			dprint('AspectSettingsDialog.submit: invalid orb in %s' % (invalid))
			self.notebook.set_current_page(ASPECT_CHART_TYPES.index(invalid[0]))
			return
		changed = []
		for ctype in ASPECT_CHART_TYPES:
			if new[ctype] != self.saved[ctype]:
				dprint('AspectSettingsDialog.submit: saving %s aspects' % (ctype))
				self.db.setSettingsAspect(ctype, new[ctype])
				self.saved[ctype] = new[ctype]
				changed.append(ctype)
		if changed:
			self.window.refreshChart()
			self.window.refreshTableWindows(changed)
		if close:
			self.close()

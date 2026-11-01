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
import locale
from gi.repository import Adw, Gtk
from astrochart.constants import ASPECT_CHART_TYPES, ASPECT_DEFAULTS, ASPECT_DEGREES, ASPECT_ORB_MAX
from astrochart.ui.dialog import AstroDialog, page
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
	"""one page per aspect set (radix, transit, synastry), a row per aspect"""

	def __init__(self, window):
		super().__init__(window, title=_("Aspect Settings"), transient_for=window, modal=True)
		self.set_default_size(560, 720)
		self.stack = Adw.ViewStack()
		self.data = {}
		self.saved = {}
		titles = {'radix':_('Radix'), 'transit':_('Transit'), 'synastry':_('Synastry')}
		scale = window.get_scale_factor()
		for ctype in ASPECT_CHART_TYPES:
			#column headings above the check boxes and orbs
			columns = [Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL) for k in range(3)]
			header = Gtk.Box(spacing=12)
			for k, text in enumerate((_('Visible\nin Circle'), _('Visible\nin Grid'), _('Orb'))):
				heading = Gtk.Label(label=text, justify=Gtk.Justification.CENTER)
				heading.add_css_class('caption')
				columns[k].add_widget(heading)
				header.append(heading)
			header.set_margin_end(12)
			group = Adw.PreferencesGroup()
			group.set_header_suffix(header)
			rows = []
			saved = []
			for aspect in self.db.getSettingsAspect(ctype):
				widgets = {'degree': aspect['degree']}
				widgets['visible'] = Gtk.CheckButton(halign=Gtk.Align.CENTER, tooltip_text=_('Visible\nin Circle').replace('\n', ' '))
				widgets['visible'].set_active(aspect['visible'] == 1)
				widgets['visible_grid'] = Gtk.CheckButton(halign=Gtk.Align.CENTER, tooltip_text=_('Visible\nin Grid').replace('\n', ' '))
				widgets['visible_grid'].set_active(aspect['visible_grid'] == 1)
				#orb as text: accepts decimal point and comma,
				#invalid input is marked instead of silently saved as 0
				orb = aspect['orb']
				widgets['orb'] = Gtk.Entry(valign=Gtk.Align.CENTER)
				widgets['orb'].set_width_chars(5)
				widgets['orb'].set_max_length(6)
				widgets['orb'].set_alignment(1.0)
				widgets['orb'].set_input_purpose(Gtk.InputPurpose.NUMBER)
				widgets['orb'].set_text(aspectOrbText(orb))
				row = Adw.ActionRow(title=aspect['name'], subtitle='%s°' % (aspect['degree']))
				row.add_prefix(window.symbols.picture('orb%s' % (aspect['degree']), 16, scale))
				suffix = Gtk.Box(spacing=12)
				for k, key in enumerate(('visible', 'visible_grid', 'orb')):
					columns[k].add_widget(widgets[key])
					suffix.append(widgets[key])
				row.add_suffix(suffix)
				group.add(row)
				rows.append(widgets)
				saved.append({'degree':aspect['degree'], 'visible':aspect['visible'],
					'visible_grid':aspect['visible_grid'], 'orb':orb})
			self.data[ctype] = rows
			self.saved[ctype] = saved
			self.stack.add_titled(page(group), ctype, titles[ctype])
		#page of the chart shown
		self.stack.set_visible_child_name(ASPECT_CHART_TYPES[self.chartTypePage(self.chart)])
		switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
		switcher.set_halign(Gtk.Align.CENTER)
		self.toolbarView.add_top_bar(switcher)
		self.set_child(self.stack)
		#window manager close button, cancel and ok all end in close-request
		self.headerButtons(cancel=self.close, ok=lambda: self.submit(close=True),
			extra=[(_("Default"), self.default), (_("Apply"), lambda: self.submit(close=False))])

	def default(self):
		#reset the widgets of the current page only, saved with apply or ok
		ctype = self.stack.get_visible_child_name()
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
			self.stack.set_visible_child_name(invalid[0])
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

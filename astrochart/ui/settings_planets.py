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

from gi.repository import Adw, GLib, Gtk
from astrochart.constants import ASPECT_CHART_TYPES, PLANET_DEFAULT_VISIBLE, PLANET_FIRST_ANGLE, PLANET_FIRST_POINT, PLANET_TRANSIT_HIDDEN
from astrochart.ui.dialog import AstroDialog, pageSwitcher, pillButton
from astrochart.util import aspectFlag, dprint

class PlanetSettingsDialog(AstroDialog):
	"""one page per chart type, a row with check boxes per body"""

	def __init__(self, window):
		super().__init__(window, title=_("Planets & Angles Settings"), transient_for=window, modal=True)
		self.set_default_size(600, 720)
		#check boxes (planet setting, heading): radix with symbol, aspect line and
		#aspect grid, transit and synastry per side
		columns = {
			'radix': [('visible', _('Symbol')), ('visible_aspect_line', _('Aspect Line')),
				('visible_aspect_grid', _('Aspect Grid'))],
			'transit': [('visible', _('Radix')), ('visible_transit', _('Transit'))],
			'synastry': [('visible', _('Radix')), ('visible_transit', _('Partner'))]
			}
		titles = {'radix':_('Radix'), 'transit':_('Transit'), 'synastry':_('Synastry')}
		groups = ((0, _('Planet Label')), (PLANET_FIRST_ANGLE, _('Angle Label')), (PLANET_FIRST_POINT, _('Point Label')))
		scale = window.get_scale_factor()
		self.stack = Adw.ViewStack()
		self.data = {}
		self.saved = {}
		for ctype in ASPECT_CHART_TYPES:
			sizes = [Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL) for k in columns[ctype]]
			preferences = Adw.PreferencesPage()
			rows = []
			saved = []
			group = None
			for planet in self.db.getSettingsPlanet(ctype):
				pid = planet['id']
				#group of planets, angles and sensitive points with column headings
				for first, title in groups:
					if pid == first:
						group = Adw.PreferencesGroup(title=title)
						header = Gtk.Box(spacing=12, margin_end=12)
						for k, (key, text) in enumerate(columns[ctype]):
							heading = Gtk.Label(label=text, justify=Gtk.Justification.CENTER)
							heading.add_css_class('caption')
							sizes[k].add_widget(heading)
							header.append(heading)
						group.set_header_suffix(header)
						preferences.add(group)
				row = Adw.ActionRow(title=GLib.markup_escape_text(planet['label']))
				symbol = window.symbols.picture(self.chart.svgSafeHref(planet['name']), 18, scale)
				if symbol.get_paintable() is not None:
					row.add_prefix(symbol)
				suffix = Gtk.Box(spacing=12)
				widgets = {'id': pid}
				values = {'id': pid}
				for k, (key, text) in enumerate(columns[ctype]):
					values[key] = aspectFlag(planet[key], 0)
					widgets[key] = Gtk.CheckButton(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, tooltip_text=text)
					widgets[key].set_active(values[key] == 1)
					sizes[k].add_widget(widgets[key])
					suffix.append(widgets[key])
				row.add_suffix(suffix)
				group.add(row)
				rows.append(widgets)
				saved.append(values)
			#defaults of this page
			preferences.add(pillButton(_("Default"), self.default))
			self.data[ctype] = rows
			self.saved[ctype] = saved
			self.stack.add_titled(preferences, ctype, titles[ctype])
		#page of the chart shown
		self.stack.set_visible_child_name(ASPECT_CHART_TYPES[self.chartTypePage(self.chart)])
		self.toolbarView.add_top_bar(pageSwitcher(self.stack))
		self.set_child(self.stack)
		#window manager close button, cancel and ok all end in close-request
		self.headerButtons(cancel=self.close, ok=lambda: self.submit(close=True),
			extra=[(_("Apply"), lambda: self.submit(close=False))])

	def default(self):
		#reset the widgets of the current page only, saved with apply or ok
		ctype = self.stack.get_visible_child_name()
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

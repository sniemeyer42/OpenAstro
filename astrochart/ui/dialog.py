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
Base class of the windows beside the main window and helpers for their
rows in the style of libadwaita
"""

from gi.repository import Adw, Gtk

class AstroDialog(Adw.Window):
	"""
	window of the program beside the main window: knows the main window
	(self.window), the chart shown, configuration and databases; it has a
	header bar with the title, set_child sets the content below it
	"""

	def __init__(self, window, **properties):
		super().__init__(**properties)
		self.window = window
		self.app = window.app
		self.chart = window.chart
		self.cfg = window.cfg
		self.db = window.db
		self.headerBar = Adw.HeaderBar()
		self.toolbarView = Adw.ToolbarView()
		self.toolbarView.add_top_bar(self.headerBar)
		self.set_content(self.toolbarView)

	def set_child(self, child):
		self.toolbarView.set_content(child)

	def headerButtons(self, cancel=None, ok=None, extra=()):
		"""
		dialog actions in the header bar: Cancel at the start, OK as the
		suggested action at the end, extra (label, callback) beside it
		"""
		if cancel is not None:
			button = Gtk.Button.new_with_mnemonic(label=_("Cancel"))
			button.connect("clicked", lambda w: cancel())
			self.headerBar.pack_start(button)
		if ok is not None:
			button = Gtk.Button.new_with_mnemonic(label=_("OK"))
			button.add_css_class('suggested-action')
			button.connect("clicked", lambda w: ok())
			self.headerBar.pack_end(button)
			self.set_default_widget(button)
		for label, callback in reversed(list(extra)):
			button = Gtk.Button.new_with_mnemonic(label=label)
			button.connect("clicked", lambda w, callback=callback: callback())
			self.headerBar.pack_end(button)
		if cancel is not None or ok is not None:
			self.headerBar.set_show_start_title_buttons(False)
			self.headerBar.set_show_end_title_buttons(False)

	def buttonRow(self, buttons):
		"""homogeneous row of buttons, buttons is a list of (label, callback)"""
		box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		box.set_homogeneous(True)
		box.set_spacing(8)
		for label, callback in buttons:
			button = Gtk.Button.new_with_mnemonic(label=label)
			button.connect("clicked", lambda w, callback=callback: callback())
			box.append(button)
		return box

	@staticmethod
	def chartTypePage(chart):
		"""settings page (index into ASPECT_CHART_TYPES) of the chart shown"""
		from astrochart.constants import ASPECT_CHART_TYPES
		if chart.type == "Transit":
			return ASPECT_CHART_TYPES.index('synastry' if chart.synastry else 'transit')
		return ASPECT_CHART_TYPES.index('radix')

def comboRow(title, items, selected=0):
	"""Adw.ComboRow of the texts items"""
	row = Adw.ComboRow(title=title)
	row.set_model(Gtk.StringList.new(list(items)))
	row.set_selected(selected)
	return row

def spinRow(title, lower, upper, value, page=10):
	"""Adw.SpinRow of whole numbers; value_as_int() like a Gtk.SpinButton"""
	row = Adw.SpinRow.new_with_range(lower, upper, 1)
	row.set_title(title)
	row.get_adjustment().set_page_increment(page)
	row.set_numeric(True)
	row.set_value(value)
	return row

def spinValue(row):
	"""whole number of an Adw.SpinRow or Gtk.SpinButton"""
	return int(round(row.get_value()))

def suffixRow(title, widget, subtitle=None):
	"""Adw.ActionRow with a widget at its end"""
	row = Adw.ActionRow(title=title)
	if subtitle:
		row.set_subtitle(subtitle)
	widget.set_valign(Gtk.Align.CENTER)
	row.add_suffix(widget)
	return row

def page(*groups):
	"""Adw.PreferencesPage (scrolls) of the groups"""
	preferences = Adw.PreferencesPage()
	for group in groups:
		preferences.add(group)
	return preferences

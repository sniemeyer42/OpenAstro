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
Base class of the windows beside the main window
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
		self.toolbarView = Adw.ToolbarView()
		self.toolbarView.add_top_bar(Adw.HeaderBar())
		self.set_content(self.toolbarView)

	def set_child(self, child):
		self.toolbarView.set_content(child)

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

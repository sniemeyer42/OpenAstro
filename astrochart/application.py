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
Application: chart state, calculation and SVG
"""

import xml.etree.ElementTree as ET
#versions of the GTK libraries
import astrochart.ui
from gi.repository import Adw, GLib, Gio, Gtk, Gdk
from astrochart.chart.chart import Chart
from astrochart.config import OpenAstroCfg
from astrochart.constants import APPLICATION_ID, OFFSET, RATIO
from astrochart.database import OpenAstroSqlite
from astrochart.ui.menus import MENU_XML
from astrochart.ui.window import AstroWindow

class AstroApplication(Adw.Application):
	def __init__(self, *args, **kwargs):
		super().__init__(
			*args,
			application_id=APPLICATION_ID,
			flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
			**kwargs,
		)
		display = Gdk.Display.get_default()
		monitors = display.get_monitors()
		#take default monitor
		geometry = monitors[0].get_geometry()
		self.screen_width = geometry.width
		self.screen_height = geometry.height
		#calculate available screen size, correct dimensions
		self.height = self.screen_height-OFFSET
		self.width = self.height * RATIO
		self.window = None
		#command line options
		self.add_main_option(
			"dbcheck",
			ord("c"),
			GLib.OptionFlags.NONE,
			GLib.OptionArg.NONE,
			"AstroChart Database Check",
			None,
		)
		self.add_main_option(
			"local",
			ord("l"),
			GLib.OptionFlags.NONE,
			GLib.OptionArg.NONE,
			"AstroChart Standakone",
			None,
		)
		self.add_main_option(
			"purge",
			ord("p"),
			GLib.OptionFlags.NONE,
			GLib.OptionArg.NONE,
			"AstroChart Database Cleanup",
			None,
		)

	def do_startup(self):
		Adw.Application.do_startup(self)

		quit_action = Gio.SimpleAction.new("quit", None)
		quit_action.connect("activate", self.on_quit)
		self.add_action(quit_action)
		self.set_accels_for_action("app.quit", ["<Primary>Q"])
		#configuration
		self.cfg = OpenAstroCfg()
		# handle data bases
		self.db = OpenAstroSqlite(self.cfg)
		#chart shown in the window: event data, chart type, settings, positions
		self.chart = Chart(self.cfg, self.db)

	def translate_menu_items(self, text, items):
		interface = ET.fromstring(text)
		for i, node in enumerate(interface.findall(".//*[@translatable='yes']")):
			node.text = items[i]
		return ET.tostring(element=interface,encoding='unicode',method='xml')

	def do_activate(self):
		#translate menu items
		menu_items = [ _('Application'),_('Maximize'),_('About'),_('Quit'),_('Settings'),
			_('Set Location'),_('Configuration'),_('Aspects'),_('Planets & Angles'),_('Chart Types'),_('Radix Chart'),
			_('Transit Chart'),_('Synastry Chart'),_('Composite Chart'),_('Combine Chart'),
			_('Solar Return'),_('Solar Progression'),_('Tables'),_('Monthly Timeline'),
			_('Cusp Aspects'),_('Zoom'),_('Out'),_('80%'),_('100%'),_('150%'),
			_('200%'),_('In'),_('Extra'),_('Export Database'),_('Import Database'),
			_('Help'),_('About') ]
		menu_xml = self.translate_menu_items(text=MENU_XML,items=menu_items)
		builder = Gtk.Builder()
		builder.add_from_string(menu_xml)
		#main menu of the window (menu button of the header bar)
		self.mainMenu = builder.get_object("MenuBar")
		# allow only a single window and raise any existing ones
		if self.window is None:
			# Windows are associated with the application
			# when the last one is closed the application shuts down
			self.window = AstroWindow(
				application=self,
				title="AstroChart Window",
				default_height=self.height,
				default_width=self.width,
			)
		self.window.present()

	def do_command_line(self, command_line):
		options = command_line.get_options_dict()
		# convert GVariantDict -> GVariant -> dict
		options = options.end().unpack()
		if "local" in options:
			LOCAL = True
			pass
		self.activate()
		return 0

	def on_quit(self, action, parameter):
		self.quit()

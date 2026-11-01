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

import datetime
import pytz
import xml.etree.ElementTree as ET
from gi.repository import GLib, Gio, Gtk, Gdk
from astrochart.chart.importexport import ImportExportMixin
from astrochart.chart.svg_aspects import AspectsSVGMixin
from astrochart.chart.svg_chart import ChartSVGMixin
from astrochart.chart.svg_lists import ListsSVGMixin
from astrochart.chart.svg_planets import PlanetsSVGMixin
from astrochart.chart.svg_tables import TablesSVGMixin
from astrochart.chart.timecalc import TimeCalcMixin
from astrochart.config import OpenAstroCfg
from astrochart.constants import APPLICATION_ID, OFFSET, RATIO
from astrochart.database import OpenAstroSqlite
from astrochart.state import app
from astrochart.ui.menus import MENU_XML
from astrochart.ui.window import AstroWindow
from astrochart.util import dprint

class AstroApplication(TimeCalcMixin, ChartSVGMixin, PlanetsSVGMixin, AspectsSVGMixin, ListsSVGMixin, TablesSVGMixin, ImportExportMixin, Gtk.Application):
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
		Gtk.Application.do_startup(self)

		quit_action = Gio.SimpleAction.new("quit", None)
		quit_action.connect("activate", self.on_quit)
		self.add_action(quit_action)
		self.set_accels_for_action("app.quit", ["<Primary>Q"])
		#configuration
		self.cfg = OpenAstroCfg()
		# handle data bases
		self.db = OpenAstroSqlite()
		#get color configuration
		self.colors = self.db.getColors()
		#get label configuration
		#self.label = self.db.getLabel()
		# 12 zodiacs
		self.zodiac = ['aries','taurus','gemini','cancer','leo','virgo','libra','scorpio','sagittarius','capricorn','aquarius','pisces']
		self.zodiac_short = ['Ari','Tau','Gem','Cnc','Leo','Vir','Lib','Sco','Sgr','Cap','Aqr','Psc']
		self.zodiac_color = ['#482900','#6b3d00','#5995e7','#2b4972','#c54100','#2b286f','#69acf1','#ffd237','#ff7200','#863c00','#4f0377','#6cbfff']
		self.zodiac_element = ['fire','earth','air','water','fire','earth','air','water','fire','earth','air','water']

		""" Configuration / Data Base / Calculations / Window """
		#check for home
		self.home_location,self.home_geolat,self.home_geolon,self.home_countrycode,self.home_timezonestr = app.db.getSettingsLocation()
		if self.home_location == '' or self.home_geolat == '' or self.home_geolon == '':
			dprint('Unknown home location, asking for new')
			self.ask_for_home = True
			self.home_location='Ooyerhoek'
			self.home_geolon=6.219530
			self.home_geolat=52.120710
			self.home_countrycode='NL'
			self.home_timezonestr='Europe/Amsterdam'
		else:
			self.ask_for_home = False
			dprint('known home location: %s %s %s' % (self.home_location, self.home_geolat, self.home_geolon))
		#default location
		self.location=self.home_location
		self.geolat=float(self.home_geolat)
		self.geolon=float(self.home_geolon)
		self.countrycode=self.home_countrycode
		self.timezonestr=self.home_timezonestr
		#current datetime
		now = datetime.datetime.now()
		#aware datetime object
		dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
		dt = pytz.timezone(self.timezonestr).localize(dt_input)
		#naive utc datetime object
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		#Default
		self.name = _("Here and Now")
		self.charttype = _('Radix')
		self.year = dt_utc.year
		self.month = dt_utc.month
		self.day = dt_utc.day
		self.hour = self.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		self.timezone = self.offsetToTz(dt.utcoffset())
		self.altitude = 25
		self.geonameid = None
		# Make locals
		self.utcToLocal()
		# configuration
		# ZOOM 1 = 100%
		self.zoom = 1
		self.type = "Radix"
		# synastry is drawn as type Transit, flag selects the synastry aspect set
		self.synastry = False
		# Default dpi for svg
		self.default_dpi=400

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
		self.menubar = builder.get_object("MenuBar")
		self.set_menubar(self.menubar)
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

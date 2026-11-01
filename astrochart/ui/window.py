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
Main window
"""

import datetime
import pytz
from string import Template
from gi.repository import GLib, Gio, Gtk, Gdk
from openastromod import zonetab
from astrochart.constants import LIMIT, VERSION
from astrochart.ui.chart_types import ProgressionDialog, SolarReturnDialog, TransitBar
from astrochart.ui.database_dialogs import DatabaseDialog, FamousDialog, SelectEventDialog
from astrochart.ui.event_dialog import EventDialog
from astrochart.ui.files import ChartFiles
from astrochart.ui.menus import BEGIN_XML, CHART_XML, END_XML, EVENT_XML, E_ITEM, M_ITEM
from astrochart.ui.settings_aspects import AspectSettingsDialog
from astrochart.ui.settings_configuration import ConfigurationDialog
from astrochart.ui.settings_location import LocationDialog
from astrochart.ui.settings_planets import PlanetSettingsDialog
from astrochart.ui.table_windows import CuspAspectsWindow, MonthDialog
from astrochart.ui.widgets import ViewSVG

""" Application Window """
class AstroWindow(Gtk.ApplicationWindow):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		#the application, the chart shown, configuration and databases
		self.app = self.get_application()
		self.chart = self.app.chart
		self.cfg = self.app.cfg
		self.db = self.app.db
		#open dialogs of which only one may exist, see presentDialog
		self.dialogs = {}
		#open table windows, see refreshTableWindows
		self.tableWindows = set()
		#file dialogs, import, export and printing
		self.files = ChartFiles(self)

		""" >>> set icon changed in GTK4 """

		self.props.show_menubar = True
		#belonges in the windows group and hence have the 'win' prefix
		max_action = Gio.SimpleAction.new_stateful(
			"maximize", None, GLib.Variant.new_boolean(False)
		)
		max_action.connect("change-state", self.on_maximize_toggle)
		self.add_action(max_action)

		# Keep it in sync with the actual state
		self.connect(
			"notify::maximized",
			lambda obj, _pspec: max_action.set_state(
				GLib.Variant.new_boolean(obj.props.maximized)
			),
		)
		#Menuitem 'About'
		about_action = Gio.SimpleAction.new("about", None)
		about_action.connect("activate", self.about_callback)
		self.add_action(about_action)

		# Menu 'Chart'
		newChart_action = Gio.SimpleAction.new("newChart", None)
		newChart_action.connect("activate", self.eventDataNew_callback)
		self.add_action(newChart_action)
		openChart_action = Gio.SimpleAction.new("openChart", None)
		openChart_action.connect("activate", self.files.openChart_callback)
		self.add_action(openChart_action)
		saveChart_action = Gio.SimpleAction.new("saveChart", None)
		saveChart_action.connect("activate", self.files.saveChart_callback)
		self.add_action(saveChart_action)
		 # Menu item 'Import'
		import_action = Gio.SimpleAction.new_stateful(
			"import", GLib.VariantType.new('s'), #submit a string type
			GLib.Variant.new_string('importAstrolog')
		)
		import_action.connect("activate", self.files.import_callback)
		self.add_action(import_action)
		 # Menu item 'Export'
		export_action = Gio.SimpleAction.new_stateful(
			"export", GLib.VariantType.new('s'), #submit a string type
			GLib.Variant.new_string('jpgfile')
		)
		export_action.connect("activate", self.files.export_callback)
		self.add_action(export_action)
		# Menu item 'Close'
		close_action = Gio.SimpleAction.new("close", None)
		close_action.connect("activate", self.on_close)
		self.add_action(close_action)

		# Menu 'Event'
		event_action = Gio.SimpleAction.new("eventData", None)
		event_action.connect("activate", self.eventData_callback)
		self.add_action(event_action)
		openBase_action = Gio.SimpleAction.new("openDatabase", None)
		openBase_action.connect("activate", self.openDatabase_callback)
		self.add_action(openBase_action)
		openFamous_action = Gio.SimpleAction.new("openDataFamous", None)
		openFamous_action.connect("activate", self.openDataFamous_callback)
		self.add_action(openFamous_action)

		# Menu 'Settings'
		setLocation_action = Gio.SimpleAction.new("settingsLocation", None)
		setLocation_action.connect("activate", self.setLocation_callback)
		self.add_action(setLocation_action)
		setConfig_action = Gio.SimpleAction.new("settingsConfiguration", None)
		setConfig_action.connect("activate", self.setConfiguration_callback)
		self.add_action(setConfig_action)
		setAspects_action = Gio.SimpleAction.new("settingsAspects", None)
		setAspects_action.connect("activate", self.setAspects_callback)
		self.add_action(setAspects_action)
		setPlanets_action = Gio.SimpleAction.new("settingsPlanets", None)
		setPlanets_action.connect("activate", self.setPlanets_callback)
		self.add_action(setPlanets_action)

		# Menu 'Chart Types'
		radix_action = Gio.SimpleAction.new("specialRadix", None)
		radix_action.connect("activate", self.specialRadix_callback)
		self.add_action(radix_action)
		transit_action = Gio.SimpleAction.new("specialTransit", None)
		transit_action.connect("activate", self.specialTransit_callback)
		self.add_action(transit_action)

		chart_type_action = Gio.SimpleAction.new_stateful("chartType",GLib.VariantType.new('s'),GLib.Variant.new_string('Synastry'))
		chart_type_action.connect("activate", self.chartType_callback)
		self.add_action(chart_type_action)

		solar_action = Gio.SimpleAction.new("specialSolar", None)
		solar_action.connect("activate", self.specialSolar_callback)
		self.add_action(solar_action)
		progression_action = Gio.SimpleAction.new("specialProgression", None)
		progression_action.connect("activate", self.specialProgression_callback)
		self.add_action(progression_action)

		# Menu 'Tables'
		timeline_action = Gio.SimpleAction.new("tableMonthlyTimeline", None)
		timeline_action.connect("activate", self.tableMonthlyTimeline_callback)
		self.add_action(timeline_action)
		cuspaspects_action = Gio.SimpleAction.new("tableCuspAspects", None)
		cuspaspects_action.connect("activate", self.tableCuspAspects_callback)
		self.add_action(cuspaspects_action)

		# Menu 'Zoom'
		zoom_action = Gio.SimpleAction.new_stateful("zoom", GLib.VariantType.new('s'), GLib.Variant.new_string('zIn'))
		zoom_action.connect("activate", self.zoom_callback)
		self.add_action(zoom_action)
		self.app.set_accels_for_action(detailed_action_name="win.zoom::zIn", accels=["<Ctrl>plus"])
		self.app.set_accels_for_action(detailed_action_name="win.zoom::z100", accels=["<Ctrl>1"])
		self.app.set_accels_for_action(detailed_action_name="win.zoom::zOut", accels=["<Ctrl>minus"])

		# Menu 'Extra'
		exportdb_action = Gio.SimpleAction.new("exportdb", None)
		exportdb_action.connect("activate", self.files.exportdb_callback)
		self.add_action(exportdb_action)
		importdb_action = Gio.SimpleAction.new("importdb", None)
		importdb_action.connect("activate", self.files.importdb_callback)
		self.add_action(importdb_action)

		self.updateUI(first_time=True)

		# display astrological chart
		box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.set_child(box)
		# date bar above chart, visible for transit charts only
		self.transitBar = TransitBar(self)
		box.append(self.transitBar)
		scrolled_window = Gtk.ScrolledWindow()
		# Draw svg pixbuf
		svg = self.chart.makeSVG()
		self.saveChartSVG(svg)
		#drawing_area to render SVG
		self.image = ViewSVG(svg)
		self.image.set_vexpand(True)
		self.image.set_hexpand(True)
		self.image.set_valign(Gtk.Align.CENTER)
		self.image.set_halign(Gtk.Align.CENTER)
		scrolled_window.set_child(self.image)
		box.append(scrolled_window)

	def presentDialog(self, name, dialog_class, **arguments):
		#only one dialog of a kind, forgotten when it closes
		dialog = self.dialogs.get(name)
		if dialog is None:
			dialog = dialog_class(self, **arguments)
			self.dialogs[name] = dialog
			dialog.connect('close-request', self.onDialogCloseRequest, name)
		dialog.present()
		return dialog

	def onDialogCloseRequest(self, dialog, name):
		#gtk destroys the dialog after this handler
		if self.dialogs.get(name) is dialog:
			del self.dialogs[name]
		return False

	""" Menu 'Event' """
	def eventDataNew_callback(self, action, parameter):
		# default location
		self.chart.location = self.chart.home_location
		self.chart.geolat = float(self.chart.home_geolat)
		self.chart.geolon = float(self.chart.home_geolon)
		self.chart.countrycode = self.chart.home_countrycode
		# timezone string, example Europe/Amsterdam
		now = datetime.datetime.now()
		self.chart.timezone_str = zonetab.nearest_tz(self.chart.geolat,self.chart.geolon,zonetab.timezones())[2]
		#aware datetime object
		dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
		dt = pytz.timezone(self.chart.timezonestr).localize(dt_input)
		#naive utc datetime object
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		# default
		self.chart.name = _("New Chart")
		self.chart.charttype = self.chart.label["radix"]
		self.chart.year = dt_utc.year
		self.chart.month = dt_utc.month
		self.chart.day = dt_utc.day
		self.chart.hour = self.chart.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		self.chart.timezone = self.chart.offsetToTz(dt.utcoffset())
		# make locals
		self.chart.utcToLocal()
		# open editor
		self.presentDialog('event', EventDialog)

	def eventData_callback(self, action, parameter):
		self.presentDialog('event', EventDialog)

	def openDatabase_callback(self, action, parameter):
		self.presentDialog('database', DatabaseDialog)

	def openDataFamous_callback(self, action, parameter):
		self.presentDialog('famous', FamousDialog)

	def quickopendb_callback(self, action, parameter):
		idx = parameter.get_int32()
		action.set_state(parameter)
		for entry in self.DB:
			if entry['id'] == idx:
				self.updateChartList(None, entry)
				break

	""" Menu 'Chart Types': synastry, composite and combine with a database entry """
	def chartType_callback(self, action, parameter):
		selected = parameter.get_string()
		action.set_state(parameter)
		self.presentDialog('select-' + selected, SelectEventDialog, ctype=selected)

	def specialRadix_callback(self, action, parameter):
		self.chart.type = "Radix"
		self.chart.charttype = self.chart.label["radix"]
		self.chart.transit = False
		self.updateChart()

	def specialTransit_callback(self, action, parameter):
		self.transitBar.start()

	def specialSolar_callback(self, action, parameter):
		self.presentDialog('solar', SolarReturnDialog)

	def specialProgression_callback(self, action, parameter):
		self.presentDialog('progression', ProgressionDialog)

	""" Menu 'Settings' """
	def setLocation_callback(self, action, parameter):
		self.presentDialog('location', LocationDialog)

	def setConfiguration_callback(self, action, parameter):
		self.presentDialog('configuration', ConfigurationDialog)

	def setAspects_callback(self, action, parameter):
		self.presentDialog('aspects', AspectSettingsDialog)

	def setPlanets_callback(self, action, parameter):
		self.presentDialog('planets', PlanetSettingsDialog)

	def refreshTableWindows(self, changed):
		#redraw open table windows using the changed settings (chart types)
		for window in list(self.tableWindows):
			if window.settings in changed and window.get_visible():
				window.refresh()

	""" Menu 'Tables' """
	def tableMonthlyTimeline_callback(self, action, parameter):
		self.presentDialog('month', MonthDialog)

	def tableCuspAspects_callback(self, action, parameter):
		CuspAspectsWindow(self).present()

	def refreshChart(self):
		#redraw the chart after changed settings, keep zoom level
		scale = self.image.scale
		self.updateChart()
		self.image.scale = scale

	def on_change_label_state(self, action, value):
		action.set_state(value)
		self.label.set_text(value.get_string())

	def on_maximize_toggle(self, action, value):
		action.set_state(value)
		if value.get_boolean():
			self.maximize()
		else:
			self.unmaximize()

	def updateUI(self, first_time):
		parent = self.get_application()
		if first_time:
			#init menu items
			chart_items = [ _('New'),_('Open'),_('Save'),_('Import'),
				_('Oroboros (*.xml)'),_('Astrolog (*.dat)'),_('Skylendar (*.skif)'),
				_('Zet8 Dbase (*.zbs)'),_('Export'),_('PNG file'),_('JPG file'),
				_('SVG file'),_('PDF file'),_('Close') ]
			self.chart_xml = parent.translate_menu_items(text=CHART_XML,items=chart_items)
			self.history_label =_('History')
			self.chart_label = _('Chart')
			event_items = [ _('Edit Event'),_('Open Database'),
				_('Open Famous People Database') ]
			self.event_xml = parent.translate_menu_items(text=EVENT_XML,items=event_items)
			self.quick_label = _('Quick Open Database')
			self.event_label = _('Event')
		#get menubar of application
		menu = parent.get_menubar()
		#uüdate labels
		#self.label = parent.db.getLabel()
		#create history actions, last will be first
		entries = self.db.history
		l = len(entries)
		t_item = Template(M_ITEM)
		items = []
		if len(entries) > 0:
			#maximal 10 entries
			i = LIMIT
			for entry in reversed(entries):
				i -= 1
				l -= 1
				if (i < 0) or (l < 0):
					break
				# substitute id and name
				item = t_item.substitute(db='historydb', idx=entry[0], label=entry[1])
				items.append(item)
			history_items = '\n'.join(items)
		if first_time:
			#generate 'Chart' menu
			chart_builder = Gtk.Builder()
			chart_builder.add_from_string(self.chart_xml)
			self.chart_menu = chart_builder.get_object("ChartUI")
			#make action for 'quickopendb'
			history_action = Gio.SimpleAction.new_stateful(
				"historydb",
				GLib.VariantType.new('i'),
				GLib.Variant.new_int32(value=0)
			)
			history_action.connect("activate", self.historydb_callback)
			self.add_action(history_action)
		else:
			menu.remove(1)
		if len(items) > 0:
			history_xml = BEGIN_XML + history_items + END_XML
		else:
			#insert 'empty' menu item
			history_xml = BEGIN_XML + E_ITEM + END_XML
		update_builder = Gtk.Builder()
		update_builder.add_from_string(history_xml)
		history_menu = update_builder.get_object("UpdateUI")
		if not first_time:
			self.chart_menu.remove(3)
		self.chart_menu.insert_submenu(3, self.history_label, history_menu)
		#becomes second item in menubar
		menu.insert_submenu(1, self.chart_label, self.chart_menu)
		# create 'Quick Open' actions
		self.DB = self.db.getDatabase()
		t_item = Template(M_ITEM)
		items = []
		for entry in self.DB:
			# substitute id and name
			item = t_item.substitute(db='quickopendb', idx=entry['id'], label=entry['name'])
			items.append(item)
		quick_open_items = '\n'.join(items)
		if first_time:
			#generate 'Event' menu
			event_builder = Gtk.Builder()
			event_builder.add_from_string(self.event_xml)
			self.event_menu = event_builder.get_object("EventUI")
			#make action for 'quickopendb'
			quick_open_action = Gio.SimpleAction.new_stateful(
				"quickopendb",
				GLib.VariantType.new('i'),
				GLib.Variant.new_int32(value=0)
			)
			quick_open_action.connect("activate", self.quickopendb_callback)
			self.add_action(quick_open_action)
		else:
			menu.remove(2)
		if len(items) > 0:
			quick_open_xml = BEGIN_XML + quick_open_items + END_XML
		else:
			#insert 'empty' menu item
			quick_open_xml = BEGIN_XML + E_ITEM + END_XML
		update_builder = Gtk.Builder()
		update_builder.add_from_string(quick_open_xml)
		quick_open_menu = update_builder.get_object("UpdateUI")
		if not first_time:
			self.event_menu.remove(1)
		self.event_menu.insert_submenu(1, self.quick_label, quick_open_menu)
		menu.insert_submenu(2, self.event_label, self.event_menu)
		if first_time:
			self.props.show_menubar = True

	def historydb_callback(self, action, parameter):
		idx = parameter.get_int32()
		action.set_state(parameter)
		for entry in self.db.history:
			if entry['id'] == idx:
				self.updateChartList(None, entry)
				break

	""" Update the chart with input list data """
	def updateChartList(self, b, record):
		#radix chart of a database or history record
		self.chart.setEvent(record)
		self.updateChart()

	def updateChart(self):
		svg = self.chart.makeSVG()
		self.saveChartSVG(svg)
		self.image.setupSVG(svg)
		self.image.queue_resize()
		# date bar belongs to transit charts only
		if self.chart.type != "Transit":
			self.transitBar.set_visible(False)

	def saveChartSVG(self, svg):
		#the chart shown is kept as file for the export and for scripts
		with open(self.cfg.tempfilename, 'w') as f:
			f.write(svg)

	""" Menu 'Zoom' """
	def zoom_callback(self, action, parameter):
		""" check for zoom level and draw """
		z_level = parameter.get_string()
		action.set_state(parameter)
		#action.set_state(parameter)
		ratio = self.image.scale
		if z_level == 'zIn':
			self.image.scale += 0.1
		elif z_level == 'z80':
			self.image.scale = 0.8
		elif z_level == 'z100':
			self.image.scale = 1.0
		elif z_level == 'z150':
			self.image.scale = 1.5
		elif z_level == 'z200':
			self.image.scale = 2.0
		elif z_level == 'zOut':
			if ratio >= 0.2:
				self.image.scale -= 0.1
			else:
				return
		self.image.queue_resize()

	def about_callback(self, action, parameter):
		about = Gtk.AboutDialog(transient_for=self, modal=True)
		about.set_logo(Gdk.Texture.new_from_filename('about.xpm'));
		about.set_program_name("Gtk4 OpenAstro.org - Open Source Astrology")
		about.set_size_request(480, -1)
		about.set_version('Gtk4 Version ' + VERSION)
		about.set_authors(["Pelle van der Scheer, Amsterdam / The Netherlands"])
		documenters = ["Erich Küster, Krefeld / Nortrhine-Westfalia / Germany"]
		about.set_copyright("Copyright © 2012-2026 Pelle van der Scheer. All rights reserved.")
		with open('COMMENTS', "r") as f:
			comments = f.read()
		about.set_comments(comments)
		with open('LICENSE', "r") as f:
			license = f.read()
		about.set_license(license)
		about.set_website("https://pygobject.gnome.org/tutorials/gtk4.html");
		about.set_website_label("GTK4 — PyGObject")
		# show the aboutdialog
		about.present()

	# a callback function to destroy the aboutdialog
	def on_close(self, action, parameter):
		self.close()

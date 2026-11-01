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
Menu 'Settings': home location
"""

import datetime
import pytz
from gi.repository import Gtk
from openastromod import geoname
from astrochart.state import app
from astrochart.util import dprint

class LocationSettingsMixin:
	"""Menu 'Settings': home location"""

	"""
	Menu item to set home location:
		settingsLocation
		settingsLocationSubmit
		settingsLocationApply
		settingsLocationDestroy
		settingsLocationClose
	"""
	def setLocation_callback(self, action, parameter):
		self.settingsLocationMode = True
		# check connection to the internet
		self.checkInternetConnection()
		# create a new window
		self.win_SL = Gtk.Window(title=_("Please Set Your Home Location"), modal=True)
		""" >>> set_icon changed in GTK4 """

		#window manager close button, cancel and ok all end in close-request
		#("destroy" is not emitted while python still references the window)
		self.win_SL.connect('close-request', self.settingsLocationClose)
		self.win_SL.set_default_size(-1,144)
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True)
		vbox.props.margin_start = 16
		vbox.props.margin_end = 16
		vbox.props.margin_top = 16
		vbox.props.margin_bottom = 16
		# create a grid, method 'attach', left, top, width, height
		grid = Gtk.Grid()
		grid.set_column_spacing(16)
		grid.set_row_spacing(16)
		# display of location (non editable)
		location = Gtk.Label(label=_('Location')+':')
		grid.attach(location, 0, 1, 1, 1)
		self.LLoc = Gtk.Label(label=app.home_location)
		#self.LLoc = Gtk.Label(label='XXXXXXXXX')
		grid.attach_next_to(child=self.LLoc, sibling=location, side=Gtk.PositionType.RIGHT, width=1, height=1)
		latitude = Gtk.Label(label=_('Latitude')+':')
		grid.attach(latitude, 0, 2, 1, 1)
		self.LLat = Gtk.Label(label=str(app.home_geolat))
		grid.attach_next_to(child=self.LLat, sibling=latitude, side=Gtk.PositionType.RIGHT, width=1, height=1)
		longitude = Gtk.Label(label=_('Longitude')+':')
		grid.attach(longitude, 0, 3, 1, 1)
		self.LLon = Gtk.Label(label=str(app.home_geolon))
		grid.attach_next_to(child=self.LLon, sibling=longitude, side=Gtk.PositionType.RIGHT, width=1, height=1)
		#use geocoders if we have an internet connection else geonames database
		if self.iconn:
			# entry for location (edigrid)
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
			label = Gtk.Label(label=_("City")+": ")
			hbox.append(label)
			self.geoLoc = Gtk.Entry()
			self.geoLoc.set_max_length(100)
			self.geoLoc.set_width_chars(30)
			self.geoLoc.set_text(app.home_location.partition(',')[0])
			hbox.append(self.geoLoc)
			label = Gtk.Label(label=" "+_("Country-code")+": ")
			hbox.append(label)
			self.geoCC = Gtk.Entry()
			self.geoCC.set_max_length(2)
			self.geoCC.set_width_chars(2)
			self.geoCC.set_text(app.home_countrycode)
			hbox.append(self.geoCC)
			grid.attach(hbox, 0, 0, 2, 1)
		else:
			# get nearest home
			self.GEON_nearest = app.db.gnearest(app.geolat,app.geolon)
			# continents
			self.continents = Gtk.DropDown()
			self.contstore = Gtk.ListStore(str,str)
			grid.attach(self.continents, 0, 0, 1, 1)
			sql = 'SELECT * FROM continent ORDER BY name ASC'
			app.db.gquery(sql)
			continent_info = Gtk.StringList()
			self.continent_infos = []
			activecont = 3
			for i, row in enumerate(app.db.gcursor):
				if row['code'] == self.GEON_nearest['continent']:
					activecont = i
					self.GEON_nearest['continent'] = None
				self.contstore.append([row['name'],row['code']])
				items = [row['name'],row['code']]
				self.continent_infos.append(items)
				continent_info.append(row['name'])
			app.db.gclose()
			self.continents.set_model(continent_info)
			# countries
			self.countries = Gtk.DropDown.new()
			grid.attach(self.countries, 1, 0, 1, 1)
			#self.countries.set_wrap_width(1) 
			self.countries.connect('notify::selected-item', self.eventDataChangedCountrybox)
			# provinces
			self.provinces = Gtk.DropDown()
			grid.attach(self.provinces, 2, 0, 1, 1)
			#self.provinces.set_wrap_width(1) 
			self.provinces.connect('notify::selected-item', self.eventDataChangedProvbox)
			# cities
			self.cities = Gtk.DropDown()
			grid.attach(self.cities, 3, 0, 1, 1)
			self.cities.set_enable_search(True)
			expr = Gtk.PropertyExpression.new(Gtk.StringObject(), None, 'string')
			self.cities.set_expression(expression=expr)
			self.cities.connect('notify::selected-item', self.eventDataChangedCitybox)
			self.continents.connect('notify::selected-item', self.eventDataChangedContbox)
			self.continents.set_selected(activecont)
		# buttonbox
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_homogeneous(True)
   		# ok button
		button = Gtk.Button.new_with_mnemonic(label="OK")
		button.connect("clicked", self.settingsLocationSubmit)
		button_box.append(button)
		# Apply button
		button = Gtk.Button.new_with_mnemonic(label=_('Apply'))
		button.connect("clicked", self.settingsLocationApply)
		button_box.append(button)
		# Cancel button
		button = Gtk.Button.new_with_mnemonic(label=_("Cancel"))
		button.connect("clicked", self.settingsLocationDestroy)
		button_box.append(button)
		grid.attach(button_box, 0, 4, 4, 1)
		vbox.append(grid)
		self.win_SL.set_child(vbox)
		# show all
		self.win_SL.present()

	def settingsLocationSubmit(self, widget):
		self.settingsLocationApply(widget)
		if self.geoLocFound:
			self.settingsLocationDestroy(widget)
			return
		else:
			return

	def settingsLocationApply(self, widget):
		# check for internet connection to decide geocode/database
		self.geoLocFound = True
		if self.iconn:
			result = geoname.search(self.geoLoc.get_text(),self.geoCC.get_text())
			if result:
				self.geoLocFound = True
				lat = float(result[0]['lat'])
				lon = float(result[0]['lng'])
				tzstr = result[0]['timezonestr']
				cc = result[0]['countryCode']
				loc='%s, %s' % (result[0]['name'],result[0]['countryName'])
				dprint('settingsLocationApply: %s found; %s %s %s' % (self.geoLoc.get_text(),lat,lon,loc))
			else:
				self.geoLocFound = False
				#revert to defaults
				lat = app.geolat
				lon = app.geolon
				loc = app.location
				cc = app.countrycode
				tzstr = app.timezonestr
				dprint('settingsLocationApply: %s not found, reverting to defaults' % self.geoLoc.get_text() )
				self.geoLoc.set_text('City Not Found, Try Again!')
				return
		else:
			lat = float(self.GEON_lat)
			lon = float(self.GEON_lon)
			loc = self.GEON_loc
			cc = self.GEON_cc
			tzstr = self.GEON_tzstr
		# apply settings to database
		app.db.setSettingsLocation(lat, lon, loc, cc, tzstr)
		app.home_location = loc
		app.home_geolat = lat
		app.home_geolon = lon
		app.home_countrycode = cc
		app.home_timezonestr = tzstr
		app.location=loc
		app.timezonestr = tzstr
		app.geolat = lat
		app.geolon = lon
		app.countrycode = cc
		app.transit = False
		app.name = _("Here and Now")
		app.type = "Radix"
		self.LLat.set_text(str(lat))
		self.LLon.set_text(str(lon))
		self.LLoc.set_text(str(loc))
		# set defaults for chart creation
		now = datetime.datetime.now()
		dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
		dt = pytz.timezone(app.timezonestr).localize(dt_input)
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		app.name = _("Here and Now")
		app.charttype = app.label["radix"]
		app.year = dt_utc.year
		app.month = dt_utc.month
		app.day = dt_utc.day
		app.hour = app.decHourJoin(dt_utc. hour, dt_utc. minute, dt_utc. second)
		app.timezone = app.offsetToTz(dt.utcoffset())
		app.altitude = 25
		app.utcToLocal()
		self.updateChart()

		dprint('Setting New Home Location: %s %s %s' % (lat,lon,loc) )

		return

	def settingsLocationDestroy(self, widget):
		self.win_SL.close()
		return

	def settingsLocationClose(self, window):
		#forget the window, gtk destroys it after this handler
		self.settingsLocationMode = False
		self.win_SL = None
		return False

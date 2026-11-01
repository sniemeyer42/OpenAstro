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
Dialog 'Settings > Set Location': home location
"""

import datetime
import pytz
from gi.repository import Gtk
from openastromod import geoname
from astrochart.ui.city_chooser import CityChooser, geocodingAvailable
from astrochart.ui.dialog import AstroDialog
from astrochart.util import dprint

class LocationDialog(AstroDialog):
	"""home location by online geocoding or from the geonames database"""

	def __init__(self, window):
		super().__init__(window, title=_("Please Set Your Home Location"), modal=True)
		# check connection to the internet
		self.iconn = geocodingAvailable(self.db)
		self.geoLocFound = True
		self.set_default_size(-1,144)
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
		self.LLoc = Gtk.Label(label=self.chart.home_location)
		grid.attach_next_to(child=self.LLoc, sibling=location, side=Gtk.PositionType.RIGHT, width=1, height=1)
		latitude = Gtk.Label(label=_('Latitude')+':')
		grid.attach(latitude, 0, 2, 1, 1)
		self.LLat = Gtk.Label(label=str(self.chart.home_geolat))
		grid.attach_next_to(child=self.LLat, sibling=latitude, side=Gtk.PositionType.RIGHT, width=1, height=1)
		longitude = Gtk.Label(label=_('Longitude')+':')
		grid.attach(longitude, 0, 3, 1, 1)
		self.LLon = Gtk.Label(label=str(self.chart.home_geolon))
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
			self.geoLoc.set_text(self.chart.home_location.partition(',')[0])
			hbox.append(self.geoLoc)
			label = Gtk.Label(label=" "+_("Country-code")+": ")
			hbox.append(label)
			self.geoCC = Gtk.Entry()
			self.geoCC.set_max_length(2)
			self.geoCC.set_width_chars(2)
			self.geoCC.set_text(self.chart.home_countrycode)
			hbox.append(self.geoCC)
			grid.attach(hbox, 0, 0, 2, 1)
		else:
			# geonames database, preselect the place nearest to the chart
			self.chooser = CityChooser(self.db, self.chart.geolat, self.chart.geolon, self.cityChanged)
			grid.attach(self.chooser.continents, 0, 0, 1, 1)
			grid.attach(self.chooser.countries, 1, 0, 1, 1)
			grid.attach(self.chooser.provinces, 2, 0, 1, 1)
			grid.attach(self.chooser.cities, 3, 0, 1, 1)
			self.chooser.start()
		# buttonbox
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_homogeneous(True)
   		# ok button
		button = Gtk.Button.new_with_mnemonic(label="OK")
		button.connect("clicked", lambda w: self.submit())
		button_box.append(button)
		# Apply button
		button = Gtk.Button.new_with_mnemonic(label=_('Apply'))
		button.connect("clicked", lambda w: self.apply())
		button_box.append(button)
		# Cancel button, window manager close button and ok end in close-request
		button = Gtk.Button.new_with_mnemonic(label=_("Cancel"))
		button.connect("clicked", lambda w: self.close())
		button_box.append(button)
		grid.attach(button_box, 0, 4, 4, 1)
		vbox.append(grid)
		self.set_child(vbox)

	def cityChanged(self, city):
		#show the city chosen in the geonames database
		self.LLoc.set_text('{}: '.format(city['loc']))
		self.LLat.set_text('{}: '.format(city['lat']))
		self.LLon.set_text('{}: '.format(city['lon']))

	def submit(self):
		self.apply()
		if self.geoLocFound:
			self.close()

	def apply(self):
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
				dprint('LocationDialog.apply: %s found; %s %s %s' % (self.geoLoc.get_text(),lat,lon,loc))
			else:
				self.geoLocFound = False
				dprint('LocationDialog.apply: %s not found' % self.geoLoc.get_text() )
				self.geoLoc.set_text('City Not Found, Try Again!')
				return
		else:
			city = self.chooser.city
			lat = float(city['lat'])
			lon = float(city['lon'])
			loc = city['loc']
			cc = city['cc']
			tzstr = city['tzstr']
		# apply settings to database
		self.db.setSettingsLocation(lat, lon, loc, cc, tzstr)
		self.chart.home_location = loc
		self.chart.home_geolat = lat
		self.chart.home_geolon = lon
		self.chart.home_countrycode = cc
		self.chart.home_timezonestr = tzstr
		self.chart.location=loc
		self.chart.timezonestr = tzstr
		self.chart.geolat = lat
		self.chart.geolon = lon
		self.chart.countrycode = cc
		self.chart.transit = False
		self.chart.name = _("Here and Now")
		self.chart.type = "Radix"
		self.LLat.set_text(str(lat))
		self.LLon.set_text(str(lon))
		self.LLoc.set_text(str(loc))
		# set defaults for chart creation
		now = datetime.datetime.now()
		dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
		dt = pytz.timezone(self.chart.timezonestr).localize(dt_input)
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		self.chart.name = _("Here and Now")
		self.chart.charttype = self.chart.label["radix"]
		self.chart.year = dt_utc.year
		self.chart.month = dt_utc.month
		self.chart.day = dt_utc.day
		self.chart.hour = self.chart.decHourJoin(dt_utc. hour, dt_utc. minute, dt_utc. second)
		self.chart.timezone = self.chart.offsetToTz(dt.utcoffset())
		self.chart.altitude = 25
		self.chart.utcToLocal()
		self.window.updateChart()
		dprint('Setting New Home Location: %s %s %s' % (lat,lon,loc) )

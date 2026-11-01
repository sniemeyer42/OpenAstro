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
from gi.repository import Adw, GLib
from openastromod import geoname
from astrochart.ui.city_chooser import CityChooser, geocodingAvailable
from astrochart.ui.dialog import AstroDialog, page
from astrochart.util import dprint

class LocationDialog(AstroDialog):
	"""home location by online geocoding or from the geonames database"""

	def __init__(self, window):
		super().__init__(window, title=_("Please Set Your Home Location"), modal=True, transient_for=window)
		self.set_default_size(520, 560)
		# check connection to the internet
		self.iconn = geocodingAvailable(self.db)
		self.geoLocFound = True
		#home location as it is now
		self.homeRow = Adw.ActionRow()
		self.homeRow.add_css_class('property')
		home = Adw.PreferencesGroup()
		home.add(self.homeRow)
		self.showHome(self.chart.home_location, self.chart.home_geolat, self.chart.home_geolon)
		#use geocoders if we have an internet connection else geonames database
		place = Adw.PreferencesGroup(title=_("Location"))
		if self.iconn:
			self.geoLoc = Adw.EntryRow(title=_("City"), text=self.chart.home_location.partition(',')[0])
			self.geoCC = Adw.EntryRow(title=_("Country-code"), text=self.chart.home_countrycode)
			place.add(self.geoLoc)
			place.add(self.geoCC)
		else:
			# geonames database, preselect the place nearest to the chart
			self.chooser = CityChooser(self.db, self.chart.geolat, self.chart.geolon, self.cityChanged)
			for row in self.chooser.rows():
				place.add(row)
			self.chooser.start()
		self.set_child(page(home, place))
		#window manager close button, cancel and ok end in close-request
		self.headerButtons(cancel=self.close, ok=self.submit, extra=[(_('Apply'), self.apply)])

	def showHome(self, location, lat, lon):
		self.homeRow.set_title(GLib.markup_escape_text(str(location)))
		self.homeRow.set_subtitle('%s: %s  ·  %s: %s' % (_('Latitude'), lat, _('Longitude'), lon))

	def cityChanged(self, city):
		#show the city chosen in the geonames database
		self.showHome(city['loc'], city['lat'], city['lon'])

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
		self.showHome(loc, lat, lon)
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

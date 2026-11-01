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
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from astrochart.places import geocodingAvailable
from astrochart.qt.city_chooser import CityChooser, OnlinePlace
from astrochart.qt.dialog import AstroDialog, Button, heading, warn
from astrochart.qt.event_dialog import placeText
from astrochart.util import dprint

class LocationDialog(AstroDialog):
	"""home location by online geocoding or from the geonames database"""

	def __init__(self, window):
		super().__init__(window, _("Please Set Your Home Location"))
		self.setMinimumWidth(460)
		chart = self.chart
		layout = QVBoxLayout(self)
		#home location as it is now
		self.home = QLabel()
		self.home.setTextFormat(Qt.TextFormat.RichText)
		self.home.setWordWrap(True)
		self.home.setFrameShape(QFrame.Shape.StyledPanel)
		self.home.setMargin(8)
		layout.addWidget(self.home)
		self.showHome(chart.home_location, chart.home_geolat, chart.home_geolon)
		#online geocoding if there is a connection, else the geonames database
		layout.addWidget(heading(_("Location")))
		self.online = None
		self.chooser = None
		if geocodingAvailable(self.db):
			self.online = OnlinePlace(str(chart.home_location).partition(',')[0], chart.home_countrycode)
			layout.addWidget(self.online)
		else:
			#preselect the city nearest to the home location
			self.chooser = CityChooser(self.db, float(chart.home_geolat), float(chart.home_geolon), self.cityChanged)
			layout.addWidget(self.chooser)
		layout.addStretch(1)
		layout.addWidget(self.buttonBox(Button.Ok | Button.Apply | Button.Cancel, {Button.Ok: self.submit, Button.Apply: self.apply}))

	def showHome(self, location, lat, lon):
		self.home.setText(placeText(location, lat, lon))

	def cityChanged(self, city):
		#the city chosen in the geonames database
		self.showHome(city['loc'], city['lat'], city['lon'])

	def submit(self):
		if self.apply():
			self.close()

	def apply(self):
		"""save the home location, chart 'Here and Now' there; False if the place is not found"""
		if self.online is not None:
			city = self.online.lookup()
			if city is None:
				warn(self, _("Location"), _('City not found! Try Again.'))
				return False
		else:
			city = self.chooser.city
		lat = float(city['lat'])
		lon = float(city['lon'])
		loc = city['loc']
		cc = city['cc']
		tzstr = city['tzstr']
		# apply settings to database
		self.db.setSettingsLocation(lat, lon, loc, cc, tzstr)
		chart = self.chart
		chart.home_location = loc
		chart.home_geolat = lat
		chart.home_geolon = lon
		chart.home_countrycode = cc
		chart.home_timezonestr = tzstr
		chart.location = loc
		chart.timezonestr = tzstr
		chart.geolat = lat
		chart.geolon = lon
		chart.countrycode = cc
		chart.geonameid = city.get('geonameid')
		chart.transit = False
		chart.type = "Radix"
		self.showHome(loc, lat, lon)
		# set defaults for chart creation
		now = datetime.datetime.now()
		dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
		dt = pytz.timezone(chart.timezonestr).localize(dt_input)
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		chart.name = _("Here and Now")
		chart.charttype = chart.label["radix"]
		chart.year = dt_utc.year
		chart.month = dt_utc.month
		chart.day = dt_utc.day
		chart.hour = chart.decHourJoin(dt_utc.hour, dt_utc.minute, dt_utc.second)
		chart.timezone = chart.offsetToTz(dt.utcoffset())
		chart.altitude = 25
		chart.utcToLocal()
		self.window.updateChart()
		dprint('Setting New Home Location: %s %s %s' % (lat, lon, loc))
		return True

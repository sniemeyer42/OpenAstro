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
Dialog 'Event > Edit Event' and 'Chart > New': name, date, time and place
of the chart
"""

import datetime
from html import escape
import pytz
from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtWidgets import QDateEdit, QDialogButtonBox, QFormLayout, QFrame, QLabel, QLineEdit, QTimeEdit, QVBoxLayout
from astrochart.constants import TRANSIT_YEAR_MAX, TRANSIT_YEAR_MIN
from astrochart.events import insertEvent, nameTaken
from astrochart.places import geocodingAvailable
from astrochart.qt.city_chooser import CityChooser, OnlinePlace
from astrochart.qt.dialog import AstroDialog, Button, confirm, heading, warn
from astrochart.util import dprint

def placeText(location, lat, lon):
	return '%s<br>%s: %s  ·  %s: %s' % (escape(str(location)), _('Latitude'), lat, _('Longitude'), lon)

def duplicateName(parent):
	warn(parent, _('Found Duplicate'), _('There is already an entry for this name, please choose another'))

class EventDialog(AstroDialog):
	"""
	event of the chart; new=True starts with a new event (now, at the home
	location); with on_save the dialog edits an entry of the event database:
	its button Save calls on_save(dialog)
	"""

	def __init__(self, window, new=False, on_save=None, parent=None):
		super().__init__(window, _("Edit Event Details"), parent)
		self.setMinimumWidth(460)
		self.on_save = on_save
		chart = self.chart
		if new:
			now = datetime.datetime.now()
			name = _("New Chart")
			date = (now.year, now.month, now.day, now.hour, now.minute, now.second)
			self.place = {'lat': float(chart.home_geolat), 'lon': float(chart.home_geolon), 'loc': chart.home_location,
				'cc': chart.home_countrycode, 'tzstr': chart.home_timezonestr, 'geonameid': chart.geonameid}
		else:
			name = chart.name
			date = (chart.year_loc, chart.month_loc, chart.day_loc, chart.hour_loc, chart.minute_loc, chart.second_loc)
			self.place = {'lat': chart.geolat, 'lon': chart.geolon, 'loc': chart.location,
				'cc': chart.countrycode, 'tzstr': chart.timezonestr, 'geonameid': chart.geonameid}
		layout = QVBoxLayout(self)
		#summary: name, local date and time with timezone, place
		self.summary = QLabel()
		self.summary.setTextFormat(Qt.TextFormat.RichText)
		self.summary.setWordWrap(True)
		self.summary.setFrameShape(QFrame.Shape.StyledPanel)
		self.summary.setMargin(8)
		layout.addWidget(self.summary)
		#name, local date and time
		layout.addWidget(heading(_("Event")))
		form = QFormLayout()
		self.name = QLineEdit(str(name))
		self.date = QDateEdit()
		self.date.setDisplayFormat('yyyy-MM-dd')
		self.date.setCalendarPopup(True)
		self.date.setDateRange(QDate(TRANSIT_YEAR_MIN, 1, 1), QDate(TRANSIT_YEAR_MAX, 12, 31))
		self.date.setDate(QDate(*date[:3]))
		self.time = QTimeEdit()
		self.time.setDisplayFormat('HH:mm:ss')
		self.time.setTime(QTime(*date[3:]))
		form.addRow(_("Name"), self.name)
		form.addRow(_("Date"), self.date)
		form.addRow(_("Time"), self.time)
		layout.addLayout(form)
		#place: online geocoding or the geonames database
		layout.addWidget(heading(_("Location")))
		self.online = None
		self.chooser = None
		if geocodingAvailable(self.db):
			self.online = OnlinePlace(str(self.place['loc']).partition(',')[0], self.place['cc'])
			layout.addWidget(self.online)
		else:
			#preselect the city nearest to the place
			self.chooser = CityChooser(self.db, float(self.place['lat']), float(self.place['lon']), self.cityChanged)
			self.chooser.searchEdit.setToolTip(_("For example: London, GB"))
			layout.addWidget(self.chooser)
		layout.addStretch(1)
		#save the database entry or add the event to the database
		if on_save is not None:
			box = self.buttonBox(Button.Save | Button.Apply | Button.Cancel,
				{Button.Save: lambda: self.on_save(self), Button.Apply: self.apply})
		else:
			box = self.buttonBox(Button.Ok | Button.Apply | Button.Cancel, {Button.Ok: self.submit, Button.Apply: self.apply},
				[(_("Add to Database"), QDialogButtonBox.ButtonRole.ActionRole, self.addToDatabase)])
		layout.addWidget(box)
		for signal in (self.name.textChanged, self.date.dateChanged, self.time.timeChanged):
			signal.connect(lambda *args: self.showSummary())
		self.showSummary()
		self.name.setFocus()
		self.name.selectAll()

	def localDate(self):
		date, time = self.date.date(), self.time.time()
		return datetime.datetime(date.year(), date.month(), date.day(), time.hour(), time.minute(), time.second())

	def showSummary(self):
		#name, local date and time with the timezone of the place, place
		local = self.localDate()
		zone = ''
		try:
			offset = pytz.timezone(self.place['tzstr']).localize(local).utcoffset()
			zone = self.chart.decTzStr(self.chart.offsetToTz(offset))
		except (pytz.UnknownTimeZoneError, AttributeError, TypeError, ValueError):
			pass
		self.summary.setText('<b>%s</b><br>%s%s<br>%s' % (escape(self.name.text()),
			local.strftime('%Y-%m-%d  %H:%M:%S'), zone, placeText(self.place['loc'], self.place['lat'], self.place['lon'])))

	def cityChanged(self, city):
		#the city chosen in the geonames database
		self.place = city
		self.showSummary()

	def findPlace(self):
		"""the place of the event, looked up online if geocoding is used; None if not found"""
		if self.online is None:
			return self.chooser.city
		city = self.online.lookup()
		if city is None:
			warn(self, _("Location"), _('City not found! Try Again.'))
			self.online.geoLoc.setFocus()
			return None
		self.place = city
		self.showSummary()
		return city

	def updateChartData(self):
		"""event data of the dialog into the chart, False if the place is not found"""
		city = self.findPlace()
		if city is None:
			return False
		chart = self.chart
		chart.timezonestr = city['tzstr']
		chart.geonameid = city['geonameid']
		# aware datetime object
		dt = pytz.timezone(chart.timezonestr).localize(self.localDate())
		dprint(dt.strftime('%Y-%m-%d %H:%M:%S %Z%z'))
		# naive datetime object UTC
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		chart.year = dt_utc.year
		chart.month = dt_utc.month
		chart.day = dt_utc.day
		chart.hour = chart.decHourJoin(dt_utc.hour, dt_utc.minute, dt_utc.second)
		chart.timezone = chart.offsetToTz(dt.utcoffset())
		chart.name = self.name.text()
		chart.geolat = float(city['lat'])
		chart.geolon = float(city['lon'])
		chart.location = city['loc']
		chart.countrycode = city['cc']
		# update local time
		chart.utcToLocal()
		return True

	def apply(self):
		"""radix chart of the event, False if the place is not found"""
		chart = self.chart
		before = (chart.name, chart.year, chart.month, chart.day, chart.hour, chart.geolat, chart.geolon)
		if not self.updateChartData():
			return False
		chart.charttype = chart.label["radix"]
		chart.type = "Radix"
		chart.transit = False
		self.window.updateChart()
		self.changed = before != (chart.name, chart.year, chart.month, chart.day, chart.hour, chart.geolat, chart.geolon)
		return True

	def submit(self):
		if self.apply():
			if self.changed:
				self.db.addHistory(self.chart)
			self.close()

	def addToDatabase(self):
		"""add the event to the database, the name must be new"""
		name = self.name.text()
		if nameTaken(self.db, name):
			duplicateName(self)
			return
		if not confirm(self, _('Are you sure you want to save < {0} > to the database?').format(name)):
			return
		if self.apply():
			insertEvent(self.db, self.chart)
			self.window.databaseChanged()
			self.close()

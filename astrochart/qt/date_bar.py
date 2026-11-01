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
Date bar above the wheel (transit, 'Here and Now'): day, month, year, hour
and minute of a moment at the home location, scrolled through field by field
"""

import calendar
import datetime
import pytz
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSpinBox, QWidget
from astrochart.constants import TRANSIT_YEAR_MAX, TRANSIT_YEAR_MIN

class TwoDigitSpinBox(QSpinBox):
	"""day, month, hour and minute with two digits"""

	def textFromValue(self, value):
		return '%02d' % value

class DateBar(QWidget):
	"""
	day, month, year, hour and minute of a moment at the home location, each
	scrolled with the mouse wheel, the arrow keys or its arrows; stepping
	beyond the last day, month, hour or minute carries over (the 31st + 1 day
	is the 1st of the next month), the chart follows at once. Hours and
	minutes are steps of clock time (also across changes of daylight saving
	time), days, months and years keep the local time. Subclasses apply the
	moment to the chart (apply) and add their buttons to self.bar.
	"""

	def __init__(self, window, title):
		super().__init__()
		self.window = window
		self.chart = window.chart
		self.zoneInfo = pytz.utc
		self.moment = None
		self.spinLock = False
		#fast scrolling through the dates is gathered into one redraw
		self.redrawTimer = QTimer(self)
		self.redrawTimer.setSingleShot(True)
		self.redrawTimer.setInterval(0)
		self.redrawTimer.timeout.connect(self.redraw)
		self.bar = QHBoxLayout(self)
		self.bar.setContentsMargins(8, 4, 8, 4)
		self.bar.addWidget(QLabel(title + ":"))
		#bounds exceed the valid values by one page, so that stepping
		#beyond the last day, month, hour or minute carries over
		spinners = [
			('D', _("Day"), -6, 38, 7),
			('M', _("Month"), -2, 15, 3),
			('Y', _("Year"), TRANSIT_YEAR_MIN, TRANSIT_YEAR_MAX, 10),
			('h', _("Hour"), -6, 29, 6),
			('m', _("Min"), -15, 74, 15) ]
		self.spin = {}
		for key, label, lower, upper, page in spinners:
			spinner = QSpinBox() if key == 'Y' else TwoDigitSpinBox()
			spinner.setRange(lower, upper)
			spinner.setAccelerated(True)
			spinner.setToolTip(label)
			spinner.valueChanged.connect(lambda value, key=key: self.spinChanged(key, value))
			self.spin[key] = spinner
			caption = QLabel(label)
			caption.setBuddy(spinner)
			self.bar.addWidget(caption)
			self.bar.addWidget(spinner)
		#timezone of the moment
		self.zone = QLabel()
		self.bar.addWidget(self.zone)
		self.bar.addStretch(1)
		self.setVisible(False)

	def homeZone(self):
		"""timezone of the home location"""
		self.zoneInfo = pytz.timezone(self.chart.homeTimezone())

	def now(self):
		"""the current minute at the home location"""
		return datetime.datetime.now(pytz.utc).replace(second=0, microsecond=0).astimezone(self.zoneInfo)

	def local(self):
		"""local (naive) datetime of the moment"""
		return self.moment.replace(tzinfo=None)

	def setLocal(self, local):
		"""moment at the local (naive) datetime; one in the gap of daylight saving time is moved behind it"""
		self.setMoment(self.zoneInfo.normalize(self.zoneInfo.localize(local)))

	def setMoment(self, moment):
		"""moment (aware datetime of the home timezone): shown, applied to the chart and redrawn soon"""
		#stay within the range of the ephemeris files
		if moment.year < TRANSIT_YEAR_MIN or moment.year > TRANSIT_YEAR_MAX:
			if self.moment is None:
				return
			moment = self.moment
		self.moment = moment
		#show carried over values
		self.spinLock = True
		for key, value in (('D', moment.day), ('M', moment.month), ('Y', moment.year), ('h', moment.hour), ('m', moment.minute)):
			self.spin[key].setValue(value)
		self.spinLock = False
		self.zone.setText(moment.tzname() + self.chart.decTzStr(self.chart.offsetToTz(moment.utcoffset())))
		self.apply(moment)
		if not self.redrawTimer.isActive():
			self.redrawTimer.start()

	def spinChanged(self, key, value):
		if self.spinLock:
			return
		self.changedByHand()
		local = self.local()
		if key == 'Y' or key == 'M':
			if key == 'Y':
				year, month = value, local.month
			else:
				#month 13 is january of next year, month 0 december of last year
				year, month = divmod(local.year * 12 + value - 1, 12)
				month += 1
			#keep day within month, e.g. 31st of january + 1 month = 28th of february
			day = min(local.day, calendar.monthrange(year, month)[1])
			self.setLocal(local.replace(year=year, month=month, day=day))
		elif key == 'D':
			self.setLocal(local + datetime.timedelta(days=value - local.day))
		else:
			#clock time
			delta = datetime.timedelta(hours=value - local.hour) if key == 'h' else datetime.timedelta(minutes=value - local.minute)
			self.setMoment(self.zoneInfo.normalize(self.moment + delta))

	def apply(self, moment):
		"""the moment into the chart"""

	def changedByHand(self):
		"""a field is changed by the user"""

	def redraw(self):
		#keep zoom level while scrolling through the dates
		self.window.refreshChart()

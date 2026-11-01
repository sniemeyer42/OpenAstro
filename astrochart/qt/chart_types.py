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
Chart types: date bar of transit charts, dialogs of solar return, secondary
progression and of the month of the timeline
"""

import datetime
import calendar
import pytz
from PySide6.QtCore import QDateTime, QDate, QTime, QTimer
from PySide6.QtWidgets import (QDateTimeEdit, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QInputDialog,
	QLabel, QPushButton, QSpinBox, QWidget)
from astrochart.constants import TRANSIT_YEAR_MAX, TRANSIT_YEAR_MIN

class TwoDigitSpinBox(QSpinBox):
	"""day, month, hour and minute with two digits"""

	def textFromValue(self, value):
		return '%02d' % value

class TransitBar(QWidget):
	"""date bar for transit charts, the chart is updated on the fly"""

	def __init__(self, window):
		super().__init__()
		self.window = window
		self.chart = window.chart
		self.transitSpinLock = False
		self.transitDate = None
		#fast scrolling through the dates is gathered into one redraw
		self.redrawTimer = QTimer(self)
		self.redrawTimer.setSingleShot(True)
		self.redrawTimer.setInterval(0)
		self.redrawTimer.timeout.connect(self.transitRedraw)
		bar = QHBoxLayout(self)
		bar.setContentsMargins(8, 4, 8, 4)
		bar.addWidget(QLabel(_("Transit") + ":"))
		#bounds exceed the valid values by one page, so that stepping
		#beyond the last day, month, hour or minute carries over
		spinners = [
			('D', _("Day"), -6, 38, 7),
			('M', _("Month"), -2, 15, 3),
			('Y', _("Year"), TRANSIT_YEAR_MIN, TRANSIT_YEAR_MAX, 10),
			('h', _("Hour"), -6, 29, 6),
			('m', _("Min"), -15, 74, 15) ]
		self.transitSpin = {}
		for key, label, lower, upper, page in spinners:
			spinner = QSpinBox() if key == 'Y' else TwoDigitSpinBox()
			spinner.setRange(lower, upper)
			spinner.setAccelerated(True)
			spinner.setToolTip(label)
			spinner.valueChanged.connect(lambda value, key=key: self.transitSpinChanged(key, value))
			self.transitSpin[key] = spinner
			caption = QLabel(label)
			caption.setBuddy(spinner)
			bar.addWidget(caption)
			bar.addWidget(spinner)
		#timezone of transit
		self.transitZone = QLabel()
		bar.addWidget(self.transitZone)
		bar.addStretch(1)
		button = QPushButton(_("Here and Now"))
		button.clicked.connect(self.setTransitNow)
		bar.addWidget(button)
		self.setVisible(False)

	def start(self):
		#transit at home location, nearest timezone if home has none
		self.chart.t_timezonestr = self.chart.homeTimezone()
		self.transitZone.setToolTip('%s (%s)' % (self.chart.home_location, self.chart.t_timezonestr))
		self.setVisible(True)
		self.setTransitNow()

	def setTransitNow(self):
		now = datetime.datetime.now(pytz.timezone(self.chart.t_timezonestr))
		self.setTransitDate(now.replace(tzinfo=None, second=0, microsecond=0))

	def setTransitDate(self, dt):
		""" Set transit to local datetime dt, show it in the date bar and redraw """
		#stay within the range of the ephemeris files
		if dt.year < TRANSIT_YEAR_MIN or dt.year > TRANSIT_YEAR_MAX:
			dt = self.transitDate
		self.transitDate = dt
		#show carried over values
		self.transitSpinLock = True
		self.transitSpin['D'].setValue(dt.day)
		self.transitSpin['M'].setValue(dt.month)
		self.transitSpin['Y'].setValue(dt.year)
		self.transitSpin['h'].setValue(dt.hour)
		self.transitSpin['m'].setValue(dt.minute)
		self.transitSpinLock = False
		dt_aware = self.chart.localToTransit(dt)
		self.transitZone.setText(dt_aware.tzname() + self.chart.decTzStr(self.chart.t_timezone))
		if not self.redrawTimer.isActive():
			self.redrawTimer.start()

	def transitSpinChanged(self, key, value):
		if self.transitSpinLock:
			return
		dt = self.transitDate
		if key == 'Y' or key == 'M':
			if key == 'Y':
				year, month = value, dt.month
			else:
				#month 13 is january of next year, month 0 december of last year
				year, month = divmod(dt.year * 12 + value - 1, 12)
				month += 1
			#keep day within month, e.g. 31st of january + 1 month = 28th of february
			day = min(dt.day, calendar.monthrange(year, month)[1])
			dt = dt.replace(year=year, month=month, day=day)
		elif key == 'D':
			dt += datetime.timedelta(days=value - dt.day)
		elif key == 'h':
			dt += datetime.timedelta(hours=value - dt.hour)
		elif key == 'm':
			dt += datetime.timedelta(minutes=value - dt.minute)
		self.setTransitDate(dt)

	def transitRedraw(self):
		#keep zoom level while scrolling through the dates
		self.window.refreshChart()

def askSolarReturn(window):
	"""year of the solar return"""
	year, ok = QInputDialog.getInt(window, _("Solar Return"), _("Select year for Solar Return"),
		datetime.datetime.now().year, 1, 2600)
	if ok:
		window.chart.localToSolar(year)
		window.updateChart()

class DateDialog(QDialog):
	"""date (and time) with a calendar"""

	def __init__(self, parent, title, description, caption, time=True):
		super().__init__(parent)
		self.setWindowTitle(title)
		layout = QFormLayout(self)
		if description:
			text = QLabel(description)
			text.setWordWrap(True)
			layout.addRow(text)
		now = datetime.datetime.now()
		self.edit = QDateTimeEdit(QDateTime(QDate(now.year, now.month, now.day), QTime(now.hour, now.minute)))
		self.edit.setCalendarPopup(True)
		self.edit.setDisplayFormat('yyyy-MM-dd HH:mm' if time else 'MMMM yyyy')
		self.edit.setDateRange(QDate(1, 1, 1), QDate(2400, 12, 31))
		layout.addRow(caption + ':', self.edit)
		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addRow(buttons)

	def value(self):
		dt = self.edit.dateTime()
		date, time = dt.date(), dt.time()
		return datetime.datetime(date.year(), date.month(), date.day(), time.hour(), time.minute())

def askProgression(window):
	"""date of the secondary progression"""
	dialog = DateDialog(window, _("Solar Progression"), _("Select date for Secondary Progression"), _("Enter Date"))
	if dialog.exec() == QDialog.DialogCode.Accepted:
		window.chart.localToSecondaryProgression(dialog.value())
		window.updateChart()

def askMonth(window):
	"""month and year of the monthly timeline, None if cancelled"""
	dialog = DateDialog(window, _("Monthly Timeline"), None, _("Select Month in Year"), time=False)
	if dialog.exec() == QDialog.DialogCode.Accepted:
		value = dialog.value()
		return value.year, value.month
	return None

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
Chart 'Here and Now': the radix of a moment at the home location with a
time bar to step through the time, also with the mouse wheel over the chart
"""

import calendar
import datetime
import pytz
from PySide6.QtCore import QDate, QDateTime, QTime, QTimer, Qt
from PySide6.QtWidgets import QComboBox, QDateTimeEdit, QHBoxLayout, QLabel, QToolButton, QWidget
from astrochart.constants import TRANSIT_YEAR_MAX, TRANSIT_YEAR_MIN

#steps of the time bar: key, minutes (time steps) or months (calendar steps)
STEPS = (('minute', 1, 0), ('hour', 60, 0), ('day', 0, 0), ('week', 0, 0), ('month', 0, 1), ('year', 0, 12))
#angle of one notch of the mouse wheel (eighths of a degree)
WHEEL_NOTCH = 120

def stepTitles():
	return {'minute': _('Minute'), 'hour': _('Hour'), 'day': _('Day'), 'week': _('Week'), 'month': _('Month'), 'year': _('Year')}

def addMonths(local, months):
	"""local datetime some months later, the day kept within the month (31st of january + 1 = 28th of february)"""
	year, month = divmod(local.year * 12 + local.month - 1 + months, 12)
	month += 1
	return local.replace(year=year, month=month, day=min(local.day, calendar.monthrange(year, month)[1]))

class HereAndNowBar(QWidget):
	"""
	time bar of the chart 'Here and Now': date and time at the home location,
	a step earlier or later (buttons, mouse wheel over the chart) in minutes,
	hours, days, weeks, months or years; Now follows the clock (the chart is
	redrawn every minute) until the time is changed. The bar is shown as long
	as the chart is the one it has set.
	"""

	def __init__(self, window):
		super().__init__()
		self.window = window
		self.chart = window.chart
		self.db = window.db
		self.utc = None
		self.applied = None
		self.wheelRest = 0
		#fast stepping is gathered into one redraw
		self.redrawTimer = QTimer(self)
		self.redrawTimer.setSingleShot(True)
		self.redrawTimer.setInterval(0)
		self.redrawTimer.timeout.connect(self.window.refreshChart)
		#the clock: next full minute
		self.clockTimer = QTimer(self)
		self.clockTimer.setSingleShot(True)
		self.clockTimer.timeout.connect(self.tick)
		bar = QHBoxLayout(self)
		bar.setContentsMargins(8, 4, 8, 4)
		title = QLabel(_("Here and Now") + ":")
		bar.addWidget(title)
		self.earlier = QToolButton()
		self.earlier.setArrowType(Qt.ArrowType.LeftArrow)
		self.earlier.setToolTip(_("Earlier"))
		self.earlier.setAutoRepeat(True)
		self.earlier.clicked.connect(lambda: self.step(-1))
		bar.addWidget(self.earlier)
		self.edit = QDateTimeEdit()
		self.edit.setDisplayFormat('ddd yyyy-MM-dd  HH:mm')
		self.edit.setDateRange(QDate(TRANSIT_YEAR_MIN, 1, 1), QDate(TRANSIT_YEAR_MAX, 12, 31))
		self.edit.setCalendarPopup(True)
		self.edit.dateTimeChanged.connect(self.editChanged)
		bar.addWidget(self.edit)
		self.later = QToolButton()
		self.later.setArrowType(Qt.ArrowType.RightArrow)
		self.later.setToolTip(_("Later"))
		self.later.setAutoRepeat(True)
		self.later.clicked.connect(lambda: self.step(1))
		bar.addWidget(self.later)
		#size of a step, kept in the configuration
		self.stepBox = QComboBox()
		titles = stepTitles()
		for key, minutes, months in STEPS:
			self.stepBox.addItem(titles[key], key)
		index = self.stepBox.findData(self.db.astrocfg.get('herenow_step', 'hour'))
		self.stepBox.setCurrentIndex(index if index >= 0 else 1)
		self.stepBox.setToolTip(_("Step"))
		self.stepBox.currentIndexChanged.connect(lambda index: self.db.setAstrocfg('herenow_step', self.stepBox.currentData()))
		bar.addWidget(self.stepBox)
		self.zone = QLabel()
		bar.addWidget(self.zone)
		bar.addStretch(1)
		#the home location, set in Settings > Set Location
		self.place = QToolButton()
		self.place.setAutoRaise(True)
		self.place.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
		self.place.setToolTip(_("Place of the chart 'Here and Now' and of new events"))
		self.place.clicked.connect(lambda: self.window.locationAction.trigger())
		bar.addWidget(self.place)
		self.nowButton = QToolButton()
		self.nowButton.setText(_("Now"))
		self.nowButton.setCheckable(True)
		#flat while the time is chosen by hand, pressed while following the clock
		self.nowButton.setAutoRaise(True)
		self.nowButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
		self.nowButton.setToolTip(_("Follow the clock"))
		self.nowButton.toggled.connect(self.followClock)
		bar.addWidget(self.nowButton)
		self.setToolTip(_("Mouse wheel over the chart: one step earlier or later"))
		self.setVisible(False)

	def setIcons(self, place, clock, earlier, later):
		"""icons of the theme, the arrows stay where it has none"""
		self.place.setIcon(place)
		self.nowButton.setIcon(clock)
		for button, icon in ((self.earlier, earlier), (self.later, later)):
			if not icon.isNull():
				button.setArrowType(Qt.ArrowType.NoArrow)
				button.setIcon(icon)

	def start(self, follow=True):
		"""show the chart 'Here and Now', now following the clock or at the moment shown last"""
		self.zoneInfo = pytz.timezone(self.chart.homeTimezone())
		self.place.setText(str(self.chart.home_location))
		self.setVisible(True)
		if follow or self.utc is None:
			if self.nowButton.isChecked():
				self.setNow()
			else:
				self.nowButton.setChecked(True)
		else:
			self.setMoment(self.utc)

	""" The moment shown """

	def setNow(self):
		self.setMoment(datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None, second=0, microsecond=0), follow=True)

	def setMoment(self, utc, follow=False):
		"""
		chart 'Here and Now' at utc (naive UTC datetime), shown in the bar and
		redrawn soon; a moment chosen by hand ends following the clock
		"""
		if not follow:
			self.stopFollowing()
		local = pytz.utc.localize(utc).astimezone(self.zoneInfo)
		#stay within the range of the ephemeris files
		if local.year < TRANSIT_YEAR_MIN or local.year > TRANSIT_YEAR_MAX:
			return
		self.utc = utc
		self.chart.setHereAndNow(utc)
		self.applied = self.chart.eventKey()
		self.edit.blockSignals(True)
		self.edit.setDateTime(QDateTime(QDate(local.year, local.month, local.day), QTime(local.hour, local.minute)))
		self.edit.blockSignals(False)
		self.zone.setText(local.tzname() + self.chart.decTzStr(self.chart.timezone))
		if not self.redrawTimer.isActive():
			self.redrawTimer.start()

	def setLocal(self, local):
		"""moment at the local (naive) datetime of the home location"""
		utc = self.zoneInfo.localize(local).astimezone(pytz.utc).replace(tzinfo=None)
		self.setMoment(utc)

	def local(self):
		return pytz.utc.localize(self.utc).astimezone(self.zoneInfo).replace(tzinfo=None)

	def editChanged(self, value):
		date, time = value.date(), value.time()
		self.setLocal(datetime.datetime(date.year(), date.month(), date.day(), time.hour(), time.minute()))

	def step(self, count):
		"""count steps of the chosen size later (earlier if negative)"""
		if not count or self.utc is None:
			return
		key = self.stepBox.currentData()
		for name, minutes, months in STEPS:
			if name == key:
				break
		if minutes:
			#clock time: the same span at every change of daylight saving time
			self.setMoment(self.utc + datetime.timedelta(minutes=minutes * count))
		elif months:
			self.setLocal(addMonths(self.local(), months * count))
		else:
			#calendar days: the same local time on another day
			self.setLocal(self.local() + datetime.timedelta(days=count * (7 if key == 'week' else 1)))

	def wheel(self, event):
		"""mouse wheel over the chart: a step per notch (later when turned away), True if used"""
		delta = event.angleDelta()
		self.wheelRest += delta.y() if abs(delta.y()) >= abs(delta.x()) else -delta.x()
		count = int(self.wheelRest / WHEEL_NOTCH)
		self.wheelRest -= count * WHEEL_NOTCH
		self.step(count)
		return True

	""" Following the clock """

	def followClock(self, follow):
		if follow:
			self.setNow()
			self.scheduleTick()
		else:
			self.clockTimer.stop()

	def stopFollowing(self):
		if self.nowButton.isChecked():
			self.nowButton.blockSignals(True)
			self.nowButton.setChecked(False)
			self.nowButton.blockSignals(False)
			self.clockTimer.stop()

	def scheduleTick(self):
		#shortly after the next full minute
		now = datetime.datetime.now()
		self.clockTimer.start((60 - now.second) * 1000 - now.microsecond // 1000 + 50)

	def tick(self):
		if self.nowButton.isChecked() and not self.isHidden():
			self.setNow()
			self.scheduleTick()

	""" Shown while the chart is the one of the bar """

	def follow(self):
		"""the chart has been redrawn: hide the bar if it shows another chart now"""
		if not self.isHidden() and self.chart.eventKey() != self.applied:
			self.stopFollowing()
			self.setVisible(False)
		elif self.isHidden() and self.applied is not None and self.chart.eventKey() == self.applied:
			#back to the radix of the moment (e.g. after a transit chart)
			self.setVisible(True)

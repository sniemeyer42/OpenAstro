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
from PySide6.QtCore import QDateTime, QDate, QTime
from PySide6.QtWidgets import QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox, QFormLayout, QLabel, QPushButton, QSpinBox
from astrochart.qt.date_bar import DateBar

class TransitBar(DateBar):
	"""date bar of transit charts at the home location, the chart is updated on the fly"""

	def __init__(self, window):
		super().__init__(window, _("Transit"))
		button = QPushButton(_("Here and Now"))
		button.clicked.connect(lambda: self.setMoment(self.now()))
		self.bar.addWidget(button)

	def start(self):
		#transit at home location, nearest timezone if home has none
		self.chart.t_timezonestr = self.chart.homeTimezone()
		self.homeZone()
		self.zone.setToolTip('%s (%s)' % (self.chart.home_location, self.chart.t_timezonestr))
		self.setVisible(True)
		self.setMoment(self.now() if self.moment is None else self.moment.astimezone(self.zoneInfo))

	def apply(self, moment):
		self.chart.localToTransit(moment)

class SolarReturnDialog(QDialog):
	"""year and presentation of the solar return of the current radix"""

	def __init__(self, window):
		super().__init__(window)
		self.setWindowTitle(_("Solar Return"))
		layout = QFormLayout(self)
		chart = window.chart
		active = chart.type == 'Solar' or chart.solar_return
		self.year = QSpinBox()
		self.year.setRange(1, 2600)
		self.year.setValue(chart.solar_year if active and chart.solar_year is not None else datetime.datetime.now().year)
		layout.addRow(_("Select year for Solar Return") + ':', self.year)
		self.view = QComboBox()
		self.view.addItem(_("Own chart"))
		self.view.addItem(_("Overlay on radix"))
		self.view.setCurrentIndex(1 if chart.solar_return else 0)
		layout.addRow(_("Display") + ':', self.view)
		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addRow(buttons)
		self.year.setFocus()

	def value(self):
		return self.year.value(), self.view.currentIndex() == 1

def askSolarReturn(window):
	"""choose the year and whether to show the solar alone or over its radix"""
	dialog = SolarReturnDialog(window)
	if dialog.exec() == QDialog.DialogCode.Accepted:
		year, overlay = dialog.value()
		window.chart.localToSolar(year, overlay=overlay)
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

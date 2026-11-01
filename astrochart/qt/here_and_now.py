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
date bar like the one of transits to scroll through the time
"""

import datetime
import pytz
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QToolButton
from astrochart.qt.date_bar import DateBar

class HereAndNowBar(DateBar):
	"""
	date bar of the chart 'Here and Now' at the home location: day, month,
	year, hour and minute scroll through the time like the transit bar; Now
	follows the clock (the chart is redrawn every minute) until the time is
	changed. The bar is shown as long as the chart is the one it has set.
	"""

	def __init__(self, window):
		super().__init__(window, _("Here and Now"))
		self.applied = None
		#the clock: next full minute
		self.clockTimer = QTimer(self)
		self.clockTimer.setSingleShot(True)
		self.clockTimer.timeout.connect(self.tick)
		#the home location, set in Settings > Set Location
		self.place = QToolButton()
		self.place.setAutoRaise(True)
		self.place.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
		self.place.setToolTip(_("Place of the chart 'Here and Now' and of new events"))
		self.place.clicked.connect(lambda: self.window.locationAction.trigger())
		self.bar.addWidget(self.place)
		self.nowButton = QToolButton()
		self.nowButton.setText(_("Now"))
		self.nowButton.setCheckable(True)
		#flat while the time is chosen by hand, pressed while following the clock
		self.nowButton.setAutoRaise(True)
		self.nowButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
		self.nowButton.setToolTip(_("Follow the clock"))
		self.nowButton.toggled.connect(self.followClock)
		self.bar.addWidget(self.nowButton)

	def setIcons(self, place, clock):
		self.place.setIcon(place)
		self.nowButton.setIcon(clock)

	def start(self):
		"""show the chart 'Here and Now' at the home location, following the clock"""
		self.homeZone()
		self.place.setText(str(self.chart.home_location))
		self.zone.setToolTip('%s (%s)' % (self.chart.home_location, self.zoneInfo.zone))
		self.setVisible(True)
		if self.nowButton.isChecked():
			self.setMoment(self.now())
		else:
			self.nowButton.setChecked(True)

	def apply(self, moment):
		self.chart.setHereAndNow(moment.astimezone(pytz.utc).replace(tzinfo=None))
		self.applied = self.chart.eventKey()

	def changedByHand(self):
		self.stopFollowing()

	""" Following the clock """

	def followClock(self, follow):
		if follow:
			self.setMoment(self.now())
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
			self.setMoment(self.now())
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

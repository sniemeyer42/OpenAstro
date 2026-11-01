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
Chart types: date bar of transit charts, dialogs of solar return and
secondary progression
"""

import datetime
import calendar
import pytz
from gi.repository import Adw, GLib, Gtk
from openastromod import zonetab
from astrochart.constants import TRANSIT_YEAR_MAX, TRANSIT_YEAR_MIN
from astrochart.ui.dialog import AstroDialog, page, spinRow, spinValue

class TransitBar(Gtk.Box):
	"""date bar for transit charts, the chart is updated on the fly"""

	def __init__(self, window):
		super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		self.window = window
		self.chart = window.chart
		self.transitSpinLock = False
		self.transitRedrawPending = False
		bar = self
		bar.props.margin_start = 12
		bar.props.margin_end = 12
		bar.props.margin_top = 6
		bar.props.margin_bottom = 6
		bar.append(Gtk.Label(label=_("Transit")+":"))
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
			bar.append(Gtk.Label(label=label))
			adjustment = Gtk.Adjustment(lower=lower, upper=upper, step_increment=1, page_increment=page)
			spinner = Gtk.SpinButton()
			spinner.props.adjustment = adjustment
			spinner.set_numeric(True)
			if key == 'Y':
				spinner.set_width_chars(4)
			else:
				spinner.set_width_chars(2)
				spinner.connect("output", self.transitSpinOutput)
			spinner.connect("value-changed", self.transitSpinChanged, key)
			self.transitSpin[key] = spinner
			bar.append(spinner)
		#timezone of transit
		self.transitZone = Gtk.Label()
		bar.append(self.transitZone)
		button = Gtk.Button.new_with_mnemonic(label=_("Here and Now"))
		button.connect("clicked", lambda w: self.setTransitNow())
		bar.append(button)
		bar.set_visible(False)

	def start(self):
		#transit at home location, nearest timezone if home has none
		self.chart.t_timezonestr = self.chart.home_timezonestr
		if self.chart.t_timezonestr not in pytz.all_timezones_set:
			self.chart.t_timezonestr = zonetab.nearest_tz(float(self.chart.home_geolat), float(self.chart.home_geolon), zonetab.timezones())[2]
		self.transitZone.set_tooltip_text('%s (%s)' % (self.chart.home_location, self.chart.t_timezonestr))
		self.set_visible(True)
		self.setTransitNow()

	def setTransitNow(self):
		now = datetime.datetime.now(pytz.timezone(self.chart.t_timezonestr))
		self.setTransitDate(now.replace(tzinfo=None, second=0, microsecond=0))

	""" Set transit to local datetime dt, show it in the date bar and redraw """
	def setTransitDate(self, dt):
		#stay within the range of the ephemeris files
		if dt.year < TRANSIT_YEAR_MIN or dt.year > TRANSIT_YEAR_MAX:
			dt = self.transitDate
		self.transitDate = dt
		#show carried over values
		self.transitSpinLock = True
		self.transitSpin['D'].set_value(dt.day)
		self.transitSpin['M'].set_value(dt.month)
		self.transitSpin['Y'].set_value(dt.year)
		self.transitSpin['h'].set_value(dt.hour)
		self.transitSpin['m'].set_value(dt.minute)
		self.transitSpinLock = False
		dt_aware = self.chart.localToTransit(dt)
		self.transitZone.set_text(dt_aware.tzname() + self.chart.decTzStr(self.chart.t_timezone))
		#fast scrolling through the dates is gathered into one redraw
		if not self.transitRedrawPending:
			self.transitRedrawPending = True
			GLib.idle_add(self.transitRedraw)

	def transitSpinChanged(self, spinner, key):
		if self.transitSpinLock:
			return
		dt = self.transitDate
		value = spinner.get_value_as_int()
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

	def transitSpinOutput(self, spinner):
		#two digits for day, month, hour and minute
		spinner.set_text('%02d' % spinner.get_value_as_int())
		return True

	def transitRedraw(self):
		self.transitRedrawPending = False
		#keep zoom level while scrolling through the dates
		self.window.refreshChart()
		return False

class SolarReturnDialog(AstroDialog):
	"""year of the solar return"""

	def __init__(self, window):
		super().__init__(window, title=_("Select year for Solar Return"), modal=True, transient_for=window)
		self.set_default_size(420, -1)
		self.year = spinRow(_('Year'), 1, 2600, datetime.datetime.now().year)
		group = Adw.PreferencesGroup(description=_("Select year for Solar Return"))
		group.add(self.year)
		self.set_child(page(group))
		self.headerButtons(cancel=self.close, ok=self.submit)

	def submit(self):
		self.chart.localToSolar(spinValue(self.year))
		self.close()
		self.window.updateChart()

class ProgressionDialog(AstroDialog):
	"""date of the secondary progression"""

	def __init__(self, window):
		super().__init__(window, title=_("Enter Date"), modal=True, transient_for=window)
		self.set_default_size(420, -1)
		now = datetime.datetime.now()
		self.spinner = {
			'Y': spinRow(_('Year'), 1, 2400, now.year),
			'M': spinRow(_('Month'), 1, 12, now.month, 3),
			'D': spinRow(_('Day'), 1, 31, now.day, 7),
			'h': spinRow(_('Hour'), 0, 23, now.hour, 6),
			'm': spinRow(_('Minute'), 0, 59, now.minute, 15)}
		group = Adw.PreferencesGroup(description=_("Select date for Secondary Progression"))
		for key in ('Y', 'M', 'D', 'h', 'm'):
			group.add(self.spinner[key])
		self.set_child(page(group))
		self.headerButtons(cancel=self.close, ok=self.submit)

	def submit(self):
		y, mon, d, h, m = (spinValue(self.spinner[key]) for key in ('Y', 'M', 'D', 'h', 'm'))
		#day within the month
		d = min(d, calendar.monthrange(y, mon)[1])
		dt = datetime.datetime(y, mon, d, h, m)
		self.chart.localToSecondaryProgression(dt)
		self.close()
		self.window.updateChart()

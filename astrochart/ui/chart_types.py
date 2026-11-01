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
Menu 'Chart Types': radix, transit (date bar), solar return, progression
"""

import datetime
import calendar
import pytz
from gi.repository import GLib, Gtk
from openastromod import zonetab
from astrochart.constants import TRANSIT_YEAR_MAX, TRANSIT_YEAR_MIN

class ChartTypesMixin:
	"""Menu 'Chart Types': radix, transit (date bar), solar return, progression"""

	"""
	 'Chart Types' Menu Items Callbacks
	  specialRadix
	  specialTransit
	  makeTransitBar
	  setTransitNow
	  setTransitDate
	  transitSpinChanged
	  transitSpinOutput
	  transitRedraw
	  specialSolar
	  specialProgression
	"""
	def specialRadix_callback(self, action, parameter):
		self.chart.type = "Radix"
		self.chart.charttype = self.chart.label["radix"]
		self.chart.transit = False
		self.updateChart()

	def specialTransit_callback(self, action, parameter):
		#transit at home location, nearest timezone if home has none
		self.chart.t_timezonestr = self.chart.home_timezonestr
		if self.chart.t_timezonestr not in pytz.all_timezones_set:
			self.chart.t_timezonestr = zonetab.nearest_tz(float(self.chart.home_geolat), float(self.chart.home_geolon), zonetab.timezones())[2]
		self.transitZone.set_tooltip_text('%s (%s)' % (self.chart.home_location, self.chart.t_timezonestr))
		self.transitBar.set_visible(True)
		self.setTransitNow()

	""" Date bar for transit charts, chart is updated on the fly """
	def makeTransitBar(self):
		self.transitSpinLock = False
		self.transitRedrawPending = False
		bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
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
		return bar

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
		scale = self.image.scale
		self.updateChart()
		self.image.scale = scale
		return False

	def specialSolar_callback(self, action, parameter):
		# create a new window
		self.win_SS = Gtk.Window()
		""" >>> set_icon """
		#self.win_SS.set_icon_from_file(self.cfg.iconWindow)
		self.win_SS.set_title(_("Select year for Solar Return"))
		#self.win_SS.connect("delete_event", lambda w,e: self.win_SS.destroy())
		#self.win_SS.move(150,150)
		#self.win_SS.set_border_width(5)
		self.win_SS.set_size_request(300,100)
		#create a grid
		grid = Gtk.Grid()
		grid.set_column_spacing(8)
		grid.set_row_spacing(8)
		#grid.set_border_width(10)
		# options
		header = Gtk.Label(label=_("Select year for Solar Return")+":")
		grid.attach(header, 0, 0, 2, 1)
		label_year = Gtk.Label(label=_('Year')+": ")
		#hbox.pack_start(label_year, True, False, 8)
		grid.attach(label_year, 0, 1, 1, 1)
		spinner = {}
		adjustment = Gtk.Adjustment(lower=1, upper=2600, step_increment=1, page_increment=10)
		spinner['Y'] = Gtk.SpinButton()
		spinner['Y'].props.adjustment = adjustment
		spinner['Y'].set_numeric(True)
		spinner['Y'].set_value(datetime.datetime.now().year)
		grid.attach(spinner['Y'], 1, 1, 1, 1)
		#ok button
		button = Gtk.Button.new_with_mnemonic(label = _("OK"))
		button.connect("clicked", self.specialSolarSubmit, spinner)
		#button.set_can_default(True)
		grid.attach(button, 0, 2, 1, 1)
		#self.win_SS.action_area.pack_start(button, True, True, 0)
		#button.grab_default()
		#cancel button
		button = Gtk.Button.new_with_mnemonic(label = _("Cancel"))
		button.connect("clicked", lambda w: self.win_SS.destroy())
		grid.attach(button, 1, 2, 1, 1)
		#self.win_SS.action_area.pack_start(button, True, True, 0)
		self.win_SS.set_child(grid)
		self.win_SS.present()

	def specialSolarSubmit(self, widget, spinner):
		y = spinner['Y'].get_value_as_int()
		self.chart.localToSolar(y)
		self.win_SS.close()
		self.updateChart()

	def specialProgression_callback(self, action, parameter):
		# create a new window
		self.win_SSP = Gtk.Window()
		""" set_icon """
		self.win_SSP.set_title(_("Enter Date"))
		self.win_SSP.set_size_request(320,180)
		#create a grid
		grid = Gtk.Grid()
		grid.set_column_spacing(8)
		grid.set_row_spacing(8)
		grid.set_vexpand(True)
		# options
		header = Gtk.Label(label=_("Select date for Secondary Progression")+":")
		grid.attach(header, 0, 0, 6, 1)
		label_year = Gtk.Label(label=_('Year')+": ")
		grid.attach(label_year, 0, 1, 1, 1)
		spinner = {}
		adjustment = Gtk.Adjustment(lower=1, upper=2400, step_increment=1, page_increment=10)
		spinner['Y'] = Gtk.SpinButton()
		spinner['Y'].props.adjustment = adjustment
		spinner['Y'].set_numeric(True)
		spinner['Y'].set_value(datetime.datetime.now().year)
		grid.attach(spinner['Y'], 1, 1, 1, 1)
		label_month = Gtk.Label(label=_('Month')+": ")
		grid.attach(label_month, 2, 1, 1, 1)
		adjustment = Gtk.Adjustment(lower=1, upper=12, step_increment=1)
		spinner['M'] = Gtk.SpinButton()
		spinner['M'].props.adjustment = adjustment
		spinner['M'].set_numeric(True)
		spinner['M'].set_value(datetime.datetime.now().month)
		grid.attach(spinner['M'], 3, 1, 1, 1)
		label_day = Gtk.Label(label=_('Day')+": ")
		grid.attach(label_day, 4, 1, 1, 1)
		adjustment = Gtk.Adjustment(lower=1, upper=31, step_increment=1)
		spinner['D'] = Gtk.SpinButton()
		spinner['D'].props.adjustment = adjustment
		spinner['D'].set_numeric(True)
		spinner['D'].set_value(datetime.datetime.now().day)
		grid.attach(spinner['D'], 5, 1, 1, 1)
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		hbox.append(Gtk.Label(label=_('Hour')+": "))
		adjustment = Gtk.Adjustment(lower=0, upper=23, step_increment=1)
		spinner['h'] = Gtk.SpinButton()
		spinner['h'].props.adjustment = adjustment
		spinner['h'].set_numeric(True)
		spinner['h'].set_value(datetime.datetime.now().hour)
		hbox.append(spinner['h'])
		hbox.append(Gtk.Label(label=_('Minute')+": "))
		adjustment = Gtk.Adjustment(lower=0, upper=59, step_increment=1)
		spinner['m'] = Gtk.SpinButton()
		spinner['m'].props.adjustment = adjustment
		spinner['m'].set_numeric(True)
		spinner['m'].set_value(datetime.datetime.now().minute)
		hbox.append(spinner['m'])
		grid.attach(hbox, 1, 2, 5, 1)
		#make the ui layout with ok button
		#ok button
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_homogeneous(True)
		button_box.set_vexpand(False)
		button = Gtk.Button.new_with_mnemonic(label = _("OK"))
		button.connect("clicked", self.specialSecondaryProgressionSubmit, spinner)
		button_box.prepend(button)
		#cancel button
		button = Gtk.Button.new_with_mnemonic(label = _("Cancel"))
		button.connect("clicked", lambda w: self.win_SSP.destroy())
		button_box.append(button)
		grid.attach(button_box, 0, 3, 5, 1)
		self.win_SSP.set_child(grid)
		self.win_SSP.present()

	def specialSecondaryProgressionSubmit(self, widget, spinner):
		y = spinner['Y'].get_value_as_int()
		mon = spinner['M'].get_value_as_int()
		d = spinner['D'].get_value_as_int()
		h = spinner['h'].get_value_as_int()
		m = spinner['m'].get_value_as_int()
		dt = datetime.datetime(y, mon, d, h, m)
		self.chart.localToSecondaryProgression(dt)
		self.win_SSP.destroy()
		self.updateChart()

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
Dialog 'Event > Edit Event': name, date, time and location of the chart
"""

import datetime
import pytz
from gi.repository import Adw, GLib, Gtk
from openastromod import geoname
from astrochart.ui.city_chooser import CityChooser, geocodingAvailable
from astrochart.ui.dialog import AstroDialog, page, spinRow, spinValue
from astrochart.util import dprint

def showDuplicateName(parent):
	"""message window: the name exists in the database"""
	dialog = Gtk.Window(title=_('Found Duplicate'), modal=True, transient_for=parent)
	dialog.set_default_size(256,-1)
	vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
	double = Gtk.Label(label=_('There is already an entry for this name, please choose another'))
	double.set_wrap(True)
	vbox.append(double)
	button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
	button_box.set_homogeneous(True)
	#OK button
	button = Gtk.Button.new_with_mnemonic(label=_("OK"))
	button.connect("clicked",  lambda w: dialog.close())
	button_box.append(button)
	vbox.append(button_box)
	dialog.set_child(vbox)
	dialog.present()

class EventDialog(AstroDialog):
	"""
	edit the event of the chart; edit=True edits a database entry: the save
	button then calls on_save(dialog) instead of adding a new entry
	"""

	def __init__(self, window, edit=False, on_save=None):
		super().__init__(window, title=_("Edit Event Details"), modal=True, transient_for=window)
		self.set_default_size(520, 760)
		self.on_save = on_save
		self.geoLocFound = True
		# check internet connection
		self.iconn = geocodingAvailable(self.db)
		chart = self.chart
		#summary: name, local date and time, place
		self.eventRow = Adw.ActionRow()
		self.eventRow.add_css_class('property')
		self.placeRow = Adw.ActionRow()
		self.placeRow.add_css_class('property')
		summary = Adw.PreferencesGroup()
		summary.add(self.eventRow)
		summary.add(self.placeRow)
		self.showEvent(chart.name)
		self.showPlace(chart.geolat, chart.geolon, chart.location)
		#name, local date and time
		self.name = Adw.EntryRow(title=_("Name"), text=chart.name)
		event = Adw.PreferencesGroup(title=_("Event"))
		event.add(self.name)
		self.dateY = spinRow(_("Year"), 1800, 2400, chart.year_loc)
		self.dateM = spinRow(_("Month"), 1, 12, chart.month_loc, 3)
		self.dateD = spinRow(_("Day"), 1, 31, chart.day_loc, 7)
		self.timeH = spinRow(_("Hour"), 0, 23, chart.hour_loc, 6)
		self.timeM = spinRow(_("Min"), 0, 59, chart.minute_loc, 15)
		self.timeS = spinRow(_("Sec"), 0, 59, chart.second_loc, 15)
		for row in (self.dateY, self.dateM, self.dateD, self.timeH, self.timeM, self.timeS):
			event.add(row)
		#place: online geocoding or the geonames database
		place = Adw.PreferencesGroup(title=_("Location"))
		if self.iconn:
			self.geoLoc = Adw.EntryRow(title=_("City"), text=chart.location.partition(',')[0])
			self.geoCC = Adw.EntryRow(title=_("Country-code"), text=chart.countrycode)
			place.add(self.geoLoc)
			place.add(self.geoCC)
		else:
			#geonames sql database, preselect the nearest geoname
			self.chooser = CityChooser(self.db, chart.geolat, chart.geolon, self.cityChanged)
			for row in self.chooser.rows():
				place.add(row)
			self.citysearch = self.chooser.searchRow
			self.citysearch.set_tooltip_text(_("For example: London, GB"))
			self.chooser.start()
		#save the database entry or add the event to the database
		if edit:
			self.savebutton = Gtk.Button.new_with_mnemonic(label=_("Save"))
			self.savebutton.connect("clicked", lambda w: self.on_save(self))
		else:
			self.savebutton = Gtk.Button.new_with_mnemonic(label=_("Add to Database"))
			self.savebutton.connect("clicked", lambda w: self.saveAsk())
		self.savebutton.add_css_class('pill')
		self.savebutton.set_halign(Gtk.Align.CENTER)
		database = Adw.PreferencesGroup()
		database.add(self.savebutton)
		self.set_child(page(summary, event, place, database))
		#apply, ok (new events only), cancel
		if edit:
			self.headerButtons(cancel=self.close, extra=[(_("Apply"), self.apply)])
		else:
			self.headerButtons(cancel=self.close, ok=self.submit, extra=[(_("Apply"), self.apply)])

	def showEvent(self, name):
		#name with local date, time and timezone of the chart
		chart = self.chart
		self.eventRow.set_title(GLib.markup_escape_text(str(name)))
		self.eventRow.set_subtitle('%s-%02d-%02d  %02d:%02d:%02d%s' % (chart.year_loc, chart.month_loc, chart.day_loc,
			chart.hour_loc, chart.minute_loc, chart.second_loc, chart.decTzStr(chart.timezone)))

	def showPlace(self, lat, lon, location):
		self.placeRow.set_title(GLib.markup_escape_text(str(location)))
		self.placeRow.set_subtitle('%s: %s  ·  %s: %s' % (_('Latitude'), lat, _('Longitude'), lon))

	def cityChanged(self, city):
		#show the city chosen in the geonames database
		self.showPlace(city['lat'], city['lon'], city['loc'])

	def saveAsk(self):
		""" test for duplicate entry and save when unique """
		en = self.db.getDatabase()
		#test for duplicate
		for i in range(len(en)):
			if en[i]["name"] == self.name.get_text():
				showDuplicateName(self)
				return
		#ask for confirmation
		alert_dialog = Gtk.AlertDialog()
		alert_dialog.set_message(_('Caution'))
		confirm = _('Are you sure you want to save < {0} > to the database?').format(self.name.props.text)
		alert_dialog.set_detail(confirm)
		alert_dialog.set_modal(True)
		alert_dialog.set_buttons(["Cancel", "OK"])
		alert_dialog.choose(parent=self, cancellable=None, callback=self.onSaveAnswer, user_data=None)

	def onSaveAnswer(self, source_obj, async_res, user_data):
		result = source_obj.choose_finish(async_res)
		if result == 1:
			#OK button clicked
			self.close()
			self.save()
		else:
			self.present()

	def save(self):
		#update chart data
		self.updateChartData()
		#add data into event_natal table
		sql='INSERT INTO event_natal (id, name, year, month, day, hour, geolon, geolat, altitude, location, timezone, notes, image, countrycode, geonameid, timezonestr, extra) VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
		tuple=(self.chart.name,self.chart.year,self.chart.month,self.chart.day,self.chart.hour, self.chart.geolon, self.chart.geolat, self.chart.altitude, self.chart.location, self.chart.timezone, '', '', self.chart.countrycode, self.chart.geonameid, self.chart.timezonestr, '')
		self.db.pquery([sql],[tuple])
		dprint('Saved to Database: '+self.chart.name)
		self.window.updateUI(first_time=False)

	def submit(self):
		#check if no changes were made
		if self.name.get_text() == self.chart.name and \
		spinValue(self.dateY) == self.chart.year_loc and \
		spinValue(self.dateM) == self.chart.month_loc and \
		spinValue(self.dateD) == self.chart.day_loc and \
		spinValue(self.timeH) == self.chart.hour_loc and \
		spinValue(self.timeM) == self.chart.minute_loc and \
		spinValue(self.timeS) == self.chart.second_loc:
			if self.iconn and self.geoCC.get_text() == self.chart.countrycode and self.geoLoc.get_text() == self.chart.location.partition(',')[0]:
				# go ahead ;)
				self.close()
				return
		#apply data
		self.apply()
		if self.geoLocFound:
			self.close()
			#update history
			self.db.addHistory(self.chart)
			self.window.updateUI(first_time=False)

	def apply(self):
		#update chart data
		self.chart.charttype = self.chart.label["radix"]
		self.chart.type = "Radix"
		self.chart.transit = False
		self.updateChartData()
		#update chart
		self.window.updateChart()

	def updateChartData(self):
		"""event data of the dialog into the chart"""
		if self.iconn:
			result = geoname.search(self.geoLoc.get_text(),self.geoCC.get_text())
			if result:
				self.geoLocFound = True
				lat = float(result[0]['lat'])
				lon = float(result[0]['lng'])
				gid = int(result[0]['geonameId'])
				cc = result[0]['countryCode']
				tzstr = result[0]['timezonestr']
				loc = '%s, %s' % (result[0]['name'],result[0]['countryName'])
				dprint('updateChartData: %s,%s found; %s %s %s' % (
					self.geoLoc.get_text(),self.geoCC.get_text(),lat,lon,loc))
			else:
				self.geoLocFound = False
				dprint('updateChartData: %s,%s not found, reverting to defaults' % (
					self.geoLoc.get_text(),self.geoCC.get_text()) )
				self.geoLoc.set_text(_('City not found! Try Again.'))
				return
		else:
			# using geonames database
			self.geoLocFound = True
			city = self.chooser.city
			lat = float(city['lat'])
			lon = float(city['lon'])
			loc = city['loc']
			cc = city['cc']
			tzstr = city['tzstr']
			gid = city['geonameid']
		# calculate timezone
		self.chart.timezonestr = tzstr
		self.chart.geonameid = gid
		# aware datetime object
		dt_input = datetime.datetime(spinValue(self.dateY), spinValue(self.dateM), spinValue(self.dateD), spinValue(self.timeH), spinValue(self.timeM), spinValue(self.timeS))
		dt = pytz.timezone(self.chart.timezonestr).localize(dt_input)

		dprint( dt.strftime('%Y-%m-%d %H:%M:%S %Z%z') )
		dprint( 'Daylight Saving Time: %s' %((dt.dst().seconds / 3600.0)) )

		# naive datetime object UTC
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		# set globals
		self.chart.year = dt_utc.year
		self.chart.month = dt_utc.month
		self.chart.day = dt_utc.day
		self.chart.hour = self.chart.decHourJoin(dt_utc.hour, dt_utc.minute, dt_utc.second)
		self.chart.timezone = self.chart.offsetToTz(dt.utcoffset())
		self.chart.name = self.name.get_text()
		# location
		self.chart.geolat=lat
		self.chart.geolon=lon
		self.chart.location=loc
		self.chart.countrycode=cc
		# update local time
		self.chart.utcToLocal()
		# update the summary
		self.showEvent(self.chart.name)
		self.showPlace(lat, lon, loc)

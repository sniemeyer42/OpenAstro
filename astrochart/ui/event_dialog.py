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
from gi.repository import Gtk
from openastromod import geoname
from astrochart.ui.city_chooser import CityChooser, geocodingAvailable
from astrochart.ui.dialog import AstroDialog
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
		super().__init__(window, title=_("Edit Event Details"), modal=True)
		self.on_save = on_save
		self.geoLocFound = True
		# check internet connection
		self.iconn = geocodingAvailable(self.db)
		#vertical box for all
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
		vbox.props.margin_start = 16
		vbox.props.margin_end = 16
		vbox.props.margin_top = 16
		vbox.props.margin_bottom = 16
		# create a grid
		grid = Gtk.Grid()
		grid.set_column_spacing(8)
		grid.set_row_spacing(8)
		#Name entry
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
		grid.attach(hbox, 0, 1, 4, 1)
		label = Gtk.Label(label = _("Name")+":", halign=Gtk.Align.END)
		hbox.append(child=label)
		self.name = Gtk.Entry(text=self.chart.name, halign=Gtk.Align.END)
		self.name.set_max_length(50)
		self.name.set_width_chars(25)
		hbox.prepend(child=self.name)
		# name entry (non editable)
		self.ename = Gtk.Label(label=self.chart.name)
		grid.attach(self.ename, 4, 1, 1, 1)
		# data of location (non editable)
		self.entry2 = Gtk.Label(label=' '+_('Latitude')+': %s\n '%self.chart.geolat+_('Longitude')+': %s\n '%self.chart.geolon+_('Location')+': %s'%self.chart.location)
		grid.attach(self.entry2, 4, 2, 1, 2)
		#do we have a  connection
		if self.iconn:
			#use geocoders,
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
			grid.attach(hbox, 0, 3, 1, 1)
			# entry for location (editable)
			label = Gtk.Label(label=_("City")+": ")
			hbox.prepend(child=label)
			self.geoLoc = Gtk.Entry()
			self.geoLoc.set_max_length(50)
			self.geoLoc.set_width_chars(20)
			self.geoLoc.set_text(self.chart.location.partition(',')[0])
			hbox.prepend(child=self.geoLoc)
			label = Gtk.Label(label=" "+_("Country-code")+": ")
			hbox.prepend(child=label)
			self.geoCC = Gtk.Entry()
			self.geoCC.set_max_length(2)
			self.geoCC.set_width_chars(2)
			self.geoCC.set_text(self.chart.countrycode)
			hbox.prepend(child=self.geoCC)
		else:
			#otherwise use geonames sql database, preselect the nearest geoname
			self.chooser = CityChooser(self.db, self.chart.geolat, self.chart.geolon, self.cityChanged)
			grid.attach(self.chooser.continents, 0, 3, 1, 1)
			grid.attach(self.chooser.countries, 1, 3, 1, 1)
			grid.attach(self.chooser.provinces, 2, 3, 1, 1)
			grid.attach(self.chooser.cities, 3, 3, 1, 1)
			# add search in database
			label = Gtk.Label(label=_("Search City")+":")
			grid.attach(label, 1, 4, 1, 1)
			self.citysearch = Gtk.Entry()
			self.citysearch.set_placeholder_text(_("Name of city?"))
			self.citysearch.set_max_length(34)
			self.citysearch.set_width_chars(24)
			grid.attach(self.citysearch, 2, 4, 1, 1)
			self.chooser.start()
			self.citysearchbutton = Gtk.Button.new_with_mnemonic(label = _("Search"))
			self.citysearchbutton.connect("clicked", lambda w: self.chooser.search(self.citysearch.get_text()))
			self.citysearch.connect("activate", lambda w: self.chooser.search(self.citysearch.get_text()))
			grid.attach(self.citysearchbutton, 3, 4, 1, 1)
			label = Gtk.Label(label="("+_("For example: London, GB")+")")
			grid.attach(label, 4, 4, 1, 1)
		# Year month day entry
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		grid.attach(hbox, 0, 5, 3, 1)
		label = Gtk.Label(label=_("Year")+":")
		hbox.prepend(child=label)
		# years from 1800 to 2400
		adjustment = Gtk.Adjustment(lower=1800, upper=2400, step_increment=1, page_increment=10)
		self.dateY = Gtk.SpinButton()
		self.dateY.props.adjustment = adjustment
		self.dateY.set_numeric(True)
		self.dateY.set_value(self.chart.year_loc)
		hbox.prepend(child=self.dateY)
		label = Gtk.Label(label=_("Month")+":")
		hbox.prepend(child=label)
		adjustment = Gtk.Adjustment(lower=1, upper=12, step_increment=1)
		self.dateM = Gtk.SpinButton()
		self.dateM.props.adjustment = adjustment
		self.dateM.set_numeric(True)
		self.dateM.set_value(self.chart.month_loc)
		hbox.prepend(child=self.dateM)
		label = Gtk.Label(label=_("Day")+":")
		hbox.prepend(child=label)
		adjustment = Gtk.Adjustment(lower=1, upper=31, step_increment=1)
		self.dateD = Gtk.SpinButton()
		self.dateD.props.adjustment = adjustment
		self.dateD.set_numeric(True)
		self.dateD.set_value(self.chart.day_loc)
		hbox.prepend(child=self.dateD)
		# date entry (non editable)
		labelDateStr = str(self.chart.year_loc)+'-%(#1)02d-%(#2)02d' % {'#1':self.chart.month_loc, '#2':self.chart.day_loc}
		self.labelDate = Gtk.Label(label=labelDateStr)
		grid.attach(self.labelDate, 3, 5, 1, 1)
		# time entry (editable) (Hour, Minutes, Seconds, Timezone)
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		grid.attach(hbox, 0, 6, 3, 1)
		label = Gtk.Label(label=_("Hour")+":")
		hbox.prepend(child=label)
		adjustment = Gtk.Adjustment(lower=0, upper=23, step_increment=1)
		self.timeH = Gtk.SpinButton()
		self.timeH.props.adjustment = adjustment
		self.timeH.set_numeric(True)
		self.timeH.set_value(self.chart.hour_loc)
		hbox.prepend(child=self.timeH)
		label = Gtk.Label(label=_("Min")+":")
		hbox.prepend(child=label)
		adjustment = Gtk.Adjustment(lower=0, upper=59, step_increment=1)
		self.timeM = Gtk.SpinButton()
		self.timeM.props.adjustment = adjustment
		self.timeM.set_numeric(True)
		self.timeM.set_value(self.chart.minute_loc)
		hbox.prepend(child=self.timeM)
		label = Gtk.Label(label="Sec:")
		hbox.prepend(child=label)
		adjustment = Gtk.Adjustment(lower=0, upper=59, step_increment=1)
		self.timeS = Gtk.SpinButton()
		self.timeS.props.adjustment = adjustment
		self.timeS.set_numeric(True)
		self.timeS.set_value(self.chart.second_loc)
		hbox.prepend(child=self.timeS)
		#time entry (non editable)
		labelTzStr = '%(#1)02d:%(#2)02d:%(#3)02d' % {'#1':self.chart.hour_loc, '#2':self.chart.minute_loc, '#3':self.chart.second_loc} + self.chart.decTzStr(self.chart.timezone)
		self.labelTz = Gtk.Label(label=labelTzStr)
		grid.attach(self.labelTz, 3, 6, 1, 1)
		# buttonbox
		buttonbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		grid.attach(buttonbox, 1, 7, 4, 1)
		# save to database button
		if edit:
			self.savebutton = Gtk.Button.new_with_mnemonic(label = _("Save"))
			self.savebutton.connect("clicked", lambda w: self.on_save(self))
			buttonbox.append(child=self.savebutton)
		else:
			self.savebutton = Gtk.Button.new_with_mnemonic(label = _("Add to Database"))
			self.savebutton.connect("clicked", lambda w: self.saveAsk())
			buttonbox.append(child=self.savebutton)
		# Apply button
		button = Gtk.Button.new_with_mnemonic(label = _("Apply"))
		button.connect("clicked", lambda w: self.apply())
		buttonbox.append(child=button)
  		#ok button
		if edit == False:
			button = Gtk.Button.new_with_mnemonic(label = _("OK"))
			button.connect("clicked", lambda w: self.submit())
			buttonbox.append(child=button)
		# cancel button
		button = Gtk.Button.new_with_mnemonic(label = _("Cancel"))
		button.connect("clicked", lambda w: self.close())
		buttonbox.append(child=button)
		vbox.append(grid)
		self.set_child(vbox)

	def cityChanged(self, city):
		#show the city chosen in the geonames database
		self.entry2.set_text(' %s: %s\n %s: %s\n %s: %s' % (_('Latitude'), city['lat'], _('Longitude'), city['lon'], _('Location'), city['loc']) )

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
		self.dateY.get_value_as_int() == str(self.chart.year_loc) and \
		self.dateM.get_value_as_int() == self.chart.month_loc and \
		self.dateD.get_value_as_int() == self.chart.day_loc and \
		self.timeH.get_value_as_int() == self.chart.hour_loc and \
		self.timeM.get_value_as_int() == self.chart.minute_loc and \
		self.timeS.get_value_as_int() == self.chart.second_loc:
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
		dt_input = datetime.datetime(self.dateY.get_value_as_int(), self.dateM.get_value_as_int(), self.dateD.get_value_as_int(), self.timeH.get_value_as_int(), self.timeM.get_value_as_int(), self.timeS.get_value_as_int())
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
		# update labels
		labelDar = str(self.chart.year_loc)+'-%(#1)02d-%(#2)02d' % {'#1':self.chart.month_loc,'#2':self.chart.day_loc}
		self.labelDate.set_text(labelDar)
		labelTzStr = '%(#1)02d:%(#2)02d:%(#3)02d' % {'#1':self.chart.hour_loc,'#2':self.chart.minute_loc,'#3':self.chart.second_loc} + self.chart.decTzStr(self.chart.timezone)
		self.labelTz.set_text(labelTzStr)
		self.ename.set_text(self.chart.name)
		self.entry2.set_text(' %s: %s\n %s: %s\n %s: %s' % ( _('Latitude'),lat,_('Longitude'),lon,_('Location'),loc) )

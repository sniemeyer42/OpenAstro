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
Menu 'Event': edit event data
"""

import datetime
import pytz
from gi.repository import Gtk
from openastromod import zonetab
from astrochart.state import app
from astrochart.util import dprint

class EventDialogMixin:
	"""Menu 'Event': edit event data"""

	"""
	 Menu 'Event'
	  eventDataNew
	  eventData_callback
	  eventData
	  citySearch
	  eventDataChangedContbox
	  eventDataChangedCountrybox
	  eventDataChangedProvbox(
	  eventDataChangedCitybox
	  eventDataSaveAsk
	  quickopendb
	"""
	def eventDataNew_callback(self, action, parameter):
		# default location
		app.location = app.home_location
		app.geolat = float(app.home_geolat)
		app.geolon = float(app.home_geolon)
		app.countrycode = app.home_countrycode
		# timezone string, example Europe/Amsterdam
		now = datetime.datetime.now()
		app.timezone_str = zonetab.nearest_tz(app.geolat,app.geolon,zonetab.timezones())[2]
		#aware datetime object
		dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
		dt = pytz.timezone(app.timezonestr).localize(dt_input)
		#naive utc datetime object
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		# default
		app.name = _("New Chart")
		app.charttype = app.label["radix"]
		app.year = dt_utc.year
		app.month = dt_utc.month
		app.day = dt_utc.day
		app.hour = app.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		app.timezone = app.offsetToTz(dt.utcoffset())
		# make locals
		app.utcToLocal()
		# open editor
		self.eventData(edit=False)

	def eventData_callback(self, action, parameter):
		self.eventData(edit=False)

	def eventData(self, edit):
		self.settingsLocationMode = False
		# create a new window
		self.window2 = Gtk.Window(title=_("Edit Event Details"), modal=True)
		""" set_icon changed in GTK4 """
		#self.window2.set_icon_from_file(app.cfg.iconWindow)
		self.window2.set_title()
		#self.window2.connect("delete_event", lambda w,e: self.window2.destroy())
		#self.window2.move(150,150)
		#self.window2.set_border_width(10)
		# check internet connection
		self.checkInternetConnection()
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
		self.name = Gtk.Entry(text=app.name, halign=Gtk.Align.END)
		self.name.set_max_length(50)
		self.name.set_width_chars(25)
		hbox.prepend(child=self.name)
		# name entry (non editable)
		self.ename = Gtk.Label(label=app.name)
		grid.attach(self.ename, 4, 1, 1, 1)
		# data of location (non editable)
		self.entry2 = Gtk.Label(label=' '+_('Latitude')+': %s\n '%app.geolat+_('Longitude')+': %s\n '%app.geolon+_('Location')+': %s'%app.location)
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
			self.geoLoc.set_text(app.location.partition(',')[0])
			hbox.prepend(child=self.geoLoc)
			label = Gtk.Label(label=" "+_("Country-code")+": ")
			hbox.prepend(child=label)
			self.geoCC = Gtk.Entry()
			self.geoCC.set_max_length(2)
			self.geoCC.set_width_chars(2)
			self.geoCC.set_text(app.countrycode)
			hbox.prepend(child=self.geoCC)
		else:
			#otherwise use geonames sql database and get nearest geoname
			self.GEON_nearest = app.db.gnearest(app.geolat, app.geolon)
			# continents
			self.continents = Gtk.DropDown()
			grid.attach(self.continents, 0, 3, 1, 1)
			#self.continents.set_wrap_width(1)
			sql = 'SELECT * FROM continent ORDER BY name ASC'
			app.db.gquery(sql)
			self.continent_infos = []
			continent_info = Gtk.StringList()
			self.searchcontinent = {}
			activecont = 3
			for i, row in enumerate(app.db.gcursor):
				self.searchcontinent[row['code']] = i
				if row['code'] == self.GEON_nearest['continent']:
					activecont = i
					self.GEON_nearest['continent'] = None
				items = [row['name'], row['code']]
				self.continent_infos.append(items)
				continent_info.append(row['name'])
			app.db.gclose()
			#self.continents.set_model(self.contstore)
			self.continents.set_model(model=continent_info)
			# countries
			self.countries = Gtk.DropDown()
			grid.attach(self.countries, 1, 3, 1, 1)
			#self.countries.set_wrap_width(1) 
			self.countries.connect('notify::selected-item', self.eventDataChangedCountrybox)
			# provinces
			self.provinces = Gtk.DropDown()
			grid.attach(self.provinces, 2, 3, 1, 1)
			#self.provinces.set_wrap_width(1) 
			self.provinces.connect('notify::selected-item', self.eventDataChangedProvbox)
			# cities
			self.cities = Gtk.DropDown()
			grid.attach(self.cities, 3, 3, 1, 1)
			self.cities.set_enable_search(True)
			expr = Gtk.PropertyExpression.new(Gtk.StringObject(), None, 'string')
			self.cities.set_expression(expression=expr)
			self.cities.connect('notify::selected-item', self.eventDataChangedCitybox)
			# add search in database
			label = Gtk.Label(label=_("Search City")+":")
			grid.attach(label, 1, 4, 1, 1)
			self.citysearch = Gtk.Entry()
			self.citysearch.set_placeholder_text(_("Name of city?"))
			self.citysearch.set_max_length(34)
			self.citysearch.set_width_chars(24)
			grid .attach(self.citysearch, 2, 4, 1, 1)
			# CAVEAT: ChangedContbox callback relies on other box changes
			self.continents.connect('notify::selected-item', self.eventDataChangedContbox)
			#for dropdown
			self.continents.set_selected(activecont)
			#for combobox
			#self.continents.set_active(activecont)
			self.citysearchbutton = Gtk.Button.new_with_mnemonic(label = _("Search"))
			self.citysearchbutton.connect("clicked", self.citySearch)
			self.citysearch.connect("activate", self.citySearch)
			grid .attach(self.citysearchbutton, 3, 4, 1, 1)
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
		self.dateY.set_value(app.year_loc)
		hbox.prepend(child=self.dateY)
		label = Gtk.Label(label=_("Month")+":")
		hbox.prepend(child=label)
		adjustment = Gtk.Adjustment(lower=1, upper=12, step_increment=1)
		self.dateM = Gtk.SpinButton()
		self.dateM.props.adjustment = adjustment
		self.dateM.set_numeric(True)
		self.dateM.set_value(app.month_loc)
		hbox.prepend(child=self.dateM)
		label = Gtk.Label(label=_("Day")+":")
		hbox.prepend(child=label)
		adjustment = Gtk.Adjustment(lower=1, upper=31, step_increment=1)
		self.dateD = Gtk.SpinButton()
		self.dateD.props.adjustment = adjustment
		self.dateD.set_numeric(True)
		self.dateD.set_value(app.day_loc)
		hbox.prepend(child=self.dateD)
		# date entry (non editable)
		labelDateStr = str(app.year_loc)+'-%(#1)02d-%(#2)02d' % {'#1':app.month_loc, '#2':app.day_loc}
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
		self.timeH.set_value(app.hour_loc)
		hbox.prepend(child=self.timeH)
		label = Gtk.Label(label=_("Min")+":")
		hbox.prepend(child=label)
		adjustment = Gtk.Adjustment(lower=0, upper=59, step_increment=1)
		self.timeM = Gtk.SpinButton()
		self.timeM.props.adjustment = adjustment
		self.timeM.set_numeric(True)
		self.timeM.set_value(app.minute_loc)
		hbox.prepend(child=self.timeM)
		label = Gtk.Label(label="Sec:")
		hbox.prepend(child=label)
		adjustment = Gtk.Adjustment(lower=0, upper=59, step_increment=1)
		self.timeS = Gtk.SpinButton()
		self.timeS.props.adjustment = adjustment
		self.timeS.set_numeric(True)
		self.timeS.set_value(app.second_loc)
		hbox.prepend(child=self.timeS)
		#time entry (non editable)
		labelTzStr = '%(#1)02d:%(#2)02d:%(#3)02d' % {'#1':app.hour_loc, '#2':app.minute_loc, '#3':app.second_loc} + app.decTzStr(app.timezone)
		self.labelTz = Gtk.Label(label=labelTzStr)
		grid.attach(self.labelTz, 3, 6, 1, 1)
		# buttonbox
		buttonbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		grid.attach(buttonbox, 1, 7, 4, 1)
		# save to database button
		if edit:
			self.savebutton = Gtk.Button.new_with_mnemonic(label = _("Save"))
			self.savebutton.connect("clicked", self.openDatabaseEditAsk)
			buttonbox.append(child=self.savebutton)
		else:
			self.savebutton = Gtk.Button.new_with_mnemonic(label = _("Add to Database"))
			self.savebutton.connect("clicked", self.eventDataSaveAsk)
			buttonbox.append(child=self.savebutton)
		# Apply button
		button = Gtk.Button.new_with_mnemonic(label = _("Apply"))
		button.connect("clicked", self.eventDataApply)
		buttonbox.append(child=button)
  		#ok button
		if edit == False:
			button = Gtk.Button.new_with_mnemonic(label = _("OK"))
			button.connect("clicked", self.eventDataSubmit)
			buttonbox.append(child=button)
		# cancel button
		button = Gtk.Button.new_with_mnemonic(label = _("Cancel"))
		button.connect("clicked", lambda w: self.window2.destroy())
		buttonbox.append(child=button)
		vbox.append(grid)
		self.window2.set_child(vbox)
		self.window2.present()

	def citySearch(self, widget):
		#text entry
		city = self.citysearch.get_text()
		#look for country in search string
		isoalpha2 = None
		if city.find(","):
			split = city.split(",")
			for x in range(len(split)):
				sql = "SELECT * FROM countryinfo WHERE (isoalpha2 LIKE ? OR name LIKE ?) LIMIT 1"
				y = split[x].strip()
				app.db.gquery(sql,(y,y))
				result = app.db.gcursor.fetchone()
				if result != None:
					isoalpha2 = result["isoalpha2"]
					city = city.replace(split[x]+",","").replace(","+split[x],"").strip()
					break
		#normal search
		normal = city
		fuzzy = "%"+city+"%"
		if isoalpha2:
			extra = " AND country='%s'"%(isoalpha2)
		else:
			extra = ""
		sql = "SELECT * FROM geonames WHERE (name LIKE ? OR asciiname LIKE ?)%s LIMIT 1" %(extra)
		app.db.gquery(sql,(normal,normal))
		result = app.db.gcursor.fetchone()
		if result == None:
			sql = "SELECT * FROM geonames WHERE (name LIKE ? OR asciiname LIKE ?)%s LIMIT 1" %(extra)
			app.db.gquery(sql,(fuzzy,fuzzy))
			result = app.db.gcursor.fetchone()
		if result == None:
			sql = "SELECT * FROM geonames WHERE (alternatenames LIKE ?)%s LIMIT 1"%(extra)
			app.db.gquery(sql,(fuzzy,))
			result = app.db.gcursor.fetchone()
		if result != None:
			#set continent
			sql = "SELECT continent FROM countryinfo WHERE isoalpha2=? LIMIT 1"
			app.db.gquery(sql,(result["country"],))
			self.continents.set_selected(self.searchcontinent[app.db.gcursor.fetchone()[0]])
			#set country
			self.countries.set_selected(self.searchcountry[result["country"]])
			#set admin1
			self.provinces.set_selected(self.searchprov[result["admin1"]])
			#set city
			self.cities.set_selected(self.searchcity[result["geonameid"]])
		return

	def eventDataChangedContbox(self, dropdown, _pspec):
		model = dropdown.get_model()
		index = dropdown.get_selected()
		info = self.continent_infos[index]
		sql = "SELECT * FROM countryinfo WHERE continent=? ORDER BY name ASC"
		app.db.gquery(sql,(info[1],))
		country_info = Gtk.StringList()
		self.country_infos = []
		#self.country_list = []
		activecountry=0
		self.searchcountry={}
		for i, row in enumerate(app.db.gcursor):
			self.searchcountry[row['isoalpha2']]=i
			if self.GEON_nearest['country'] == row['isoalpha2']:
				activecountry=i
				self.GEON_nearest['country'] = None
			items = [row['name'],row['isoalpha2']]
			self.country_infos.append(items)
			#self.country_list.append((row['name'],row['isoalpha2']))
			country_info.append(row['name'])
		app.db.gclose()
		self.countries.set_model(country_info)
		self.countries.set_selected(activecountry) 
		return

	def eventDataChangedCountrybox(self, dropdown, _pspec):
		model = dropdown.get_model()
		index = dropdown.get_selected()
		info = self.country_infos[index]
		sql = "SELECT * FROM admin1codes WHERE country=? ORDER BY admin1 ASC"
		app.db.gquery(sql,(info[1],))
		self.province_infos = []
		province_info = Gtk.StringList()
		activeprov = 0
		self.searchprov={}
		for i, row in enumerate(app.db.gcursor):
			self.searchprov[row["admin1"]] = i
			if self.GEON_nearest['admin1'] == row['admin1']:
				activeprov = i
				self.GEON_nearest['admin1'] = None
			items = [row['province'],row['country'],row['admin1'],info[0]]
			self.province_infos.append(items)
			province_info.append(row['province'])
		app.db.gclose()
		self.provinces.set_model(province_info)
		self.provinces.set_selected(activeprov) 
		return

	def eventDataChangedProvbox(self, dropdown, _pspec):
		model = dropdown.get_model()
		index = dropdown.get_selected()
		info = self.province_infos[index]
		sql = 'SELECT * FROM geonames WHERE country=? AND admin1=? ORDER BY name ASC'
		app.db.gquery(sql,(info[1],info[2]))
		self.city_infos = []
		city_info = Gtk.StringList()
		activecity = 0
		self.searchcity = {}
		for i, row in enumerate(app.db.gcursor):
			self.searchcity[row["geonameid"]]=i
			if self.GEON_nearest['geonameid'] == row['geonameid']:
				activecity = i
				self.GEON_nearest['geonameid'] = None
			items = [row['name'], str(row['latitude']), str(row['longitude']), info[3], info[0], row['country'], str(row['geonameid']), row['timezone']]
			self.city_infos.append(items)
			city_info.append(row['name'])
		app.db.gclose()
		self.cities.set_model(city_info)
		self.cities.set_selected(activecity) 
		return

	def eventDataChangedCitybox(self, dropdown, _pspec):
		model = dropdown.get_model()
		index = dropdown.get_selected()
		info = self.city_infos[index]
		#change label for eventdata
		self.GEON_lat = info[1]
		self.GEON_lon = info[2]
		self.GEON_loc = '%s, %s, %s' % (info[0],info[4],info[3])
		self.GEON_cc = info[5]
		self.GEON_id = info[6]
		self.GEON_tzstr = info[7]

		dprint( 'evenDataChangedCitybox: %s:%s:%s:%s:%s:%s' % (self.GEON_loc, self.GEON_lat, self.GEON_lon, self.GEON_cc, self.GEON_tzstr, self.GEON_id) )

		if self.settingsLocationMode:
			#set home location
			self.LLoc.set_text('{}: '.format(self.GEON_loc))
			self.LLat.set_text('{}: '.format(self.GEON_lat))
			self.LLon.set_text('{}: '.format(self.GEON_lon))
		else:
			#set event data
			self.entry2.set_text(' %s: %s\n %s: %s\n %s: %s' % (_('Latitude'), self.GEON_lat, _('Longitude'), self.GEON_lon, _('Location'), self.GEON_loc) )

	def eventDataSaveAsk(self, widget):
		""" test for duplicate entry and save when unique """
		en = app.db.getDatabase()
		#test for duplicate
		for i in range(len(en)):
			if en[i]["name"] == self.name.get_text():
				dialog = Gtk.Window(title=_('Found Duplicate'),modal=True)
				""" set_icon """
				#dialog.set_icon_from_file(app.cfg.iconWindow)
				dialog.set_default_size(256,-1)
				vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
				double = Gtk.Label(label=_('There is already an entry for this name, please choose another'))
				double.set_wrap(True)
				vbox.append(double)
				button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
				button_box.set_homogeneous(True)
				#OK button
				button = Gtk.Button.new_with_mnemonic(label=_("OK"))
				button.connect("clicked",  lambda w: dialog.destroy())
				button_box.append(button)
				vbox.append(button_box)
				dialog.set_child(vbox)
				dialog.present()
				return
		#ask for confirmation
		alert_dialog = Gtk.AlertDialog()
		alert_dialog.set_message(_('Caution'))
		confirm = _('Are you sure you want to save < {0} > to the database?').format(self.name.props.text)
		alert_dialog.set_detail(confirm)
		alert_dialog.set_modal(True)
		alert_dialog.set_buttons(["Cancel", "OK"])
		alert_dialog.choose(parent=self, cancellable=None, callback=self.on_save_perform, user_data=None)

	def on_save_perform(self, source_obj, async_res, user_data):
		result = source_obj.choose_finish(async_res)
		if result == 1:
			#OK button clicked
			self.window2.close()
			self.eventDataSave()
		else:
			self.window2.present()

	def eventDataSave(self):
		#update chart data
		self.updateChartData()
		#add data into event_natal table
		sql='INSERT INTO event_natal (id, name, year, month, day, hour, geolon, geolat, altitude, location, timezone, notes, image, countrycode, geonameid, timezonestr, extra) VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
		tuple=(app.name,app.year,app.month,app.day,app.hour, app.geolon, app.geolat, app.altitude, app.location, app.timezone, '', '', app.countrycode, app.geonameid, app.timezonestr, '')
		app.db.pquery([sql],[tuple])
		dprint('Saved to Database: '+app.name)
		self.updateUI(first_time=False)

	def eventDataSubmit(self, widget):
		#check if no changes were made
		if self.name.get_text() == app.name and \
		self.dateY.get_value_as_int() == str(app.year_loc) and \
		self.dateM.get_value_as_int() == app.month_loc and \
		self.dateD.get_value_as_int() == app.day_loc and \
		self.timeH.get_value_as_int() == app.hour_loc and \
		self.timeM.get_value_as_int() == app.minute_loc and \
		self.timeS.get_value_as_int() == app.second_loc:
			if self.iconn and self.geoCC.get_text() == app.countrycode and self.geoLoc.get_text() == app.location.partition(',')[0]:
				# go ahead ;)
				self.window2.destroy()
				return
		#apply data
		self.eventDataApply(widget)
		if self.geoLocFound:
			self.window2.destroy()
			#update history
			app.db.addHistory()
			self.updateUI(first_time=False)
			return
		else:
			return

	def eventDataApply(self, widget):
		#update chart data
		app.charttype = app.label["radix"]
		app.type = "Radix"
		app.transit = False
		self.updateChartData()
		#update chart
		self.updateChart()

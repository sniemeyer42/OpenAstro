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
Event databases: open, edit, delete, famous people, select a second event
"""

import datetime
import pytz
import sqlite3
from gi.repository import Gio, Gtk
from openastromod import zonetab
from astrochart.state import app
from astrochart.ui.widgets import EventData, bind_birth, bind_ident, bind_location, bind_name, setup
from astrochart.util import dprint

class DatabaseDialogsMixin:
	"""Event databases: open, edit, delete, famous people, select a second event"""

	def openDatabase_callback(self, action, parameter):
		self.openDatabase(extraDB=None)

	def openDatabase(self, extraDB):
		self.win_OD = Gtk.Window()
		""" set_icon """
		#self.win_OD.set_icon_from_file(app.cfg.iconWindow)
		self.win_OD.set_title(_('Open Database Entry'))
		self.win_OD.set_default_size(480, 480)
		#self.win_OD.move(150,150)
		#self.win_OD.connect("delete_event", lambda w,e: self.win_OD.destroy())
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
		vbox.props.margin_start = 12
		vbox.props.margin_end = 12
		vbox.props.margin_top = 6
		vbox.props.margin_bottom = 6
		#listmodel
		self.win_OD.selection = Gtk.SingleSelection()
		self.listmodel = Gio.ListStore.new(EventData)
		self.win_OD.selection.set_model(self.listmodel)
		#add data from event_natal table
		if extraDB is not None:
			#self.win_OD_treeview.set_enable_search(False)
			self.DB = extraDB
		else:
			#self.win_OD_treeview.set_enable_search(True)
			self.DB = app.db.getDatabase()
		for data in self.DB:
			h,m,s = app.decHour(float(data["hour"]))
			dt_utc = datetime.datetime(int(data["year"]), int(data["month"]), int(data["day"]), h, m, s)
			dt = dt_utc + datetime.timedelta(seconds=float(data["timezone"])*float(3600))
			birth_date = str(dt.year)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':dt.month,'#2':dt.day,'#3':dt.hour,'#4':dt.minute,'#5':dt.second}
			event_data = EventData(ident=str(data["id"]),name=data["name"],birth=birth_date,location=data["location"])
			self.listmodel.append(event_data)
		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_vexpand(True)

		column_view = Gtk.ColumnView()
		column_view.props.show_row_separators = False
		column_view.props.show_column_separators = True

		#id_col.set_fixed_width(112)
		id_factory = Gtk.SignalListItemFactory()
		id_factory.connect("setup", setup)
		id_factory.connect("bind", bind_ident)
		id_col = Gtk.ColumnViewColumn.new(title="Id",factory=id_factory)
		id_col.set_resizable(True)
		#id_col.set_factory(id_factory)
		column_view.append_column(id_col)

		name_col = Gtk.ColumnViewColumn.new("Name")
		name_col.set_resizable(True)
		#name_col.set_fixed_width(112)
		name_factory = Gtk.SignalListItemFactory()
		name_factory.connect("setup", setup)
		name_factory.connect("bind", bind_name)
		name_col.set_factory(name_factory)
		column_view.append_column(name_col)

		birth_col = Gtk.ColumnViewColumn.new("Birth Date")
		birth_col.set_resizable(True)
		#birth_col.set_fixed_width(112)
		birth_factory = Gtk.SignalListItemFactory()
		birth_factory.connect("setup", setup)
		birth_factory.connect("bind", bind_birth)
		birth_col.set_factory(birth_factory)
		column_view.append_column(birth_col)

		location_col = Gtk.ColumnViewColumn.new("Location")
		location_col.set_resizable(True)
		#location_col.set_fixed_width(112)
		location_factory = Gtk.SignalListItemFactory()
		location_factory.connect("setup", setup)
		location_factory.connect("bind", bind_location)
		location_col.set_factory(location_factory)
		column_view.append_column(location_col)
		column_view.set_model(self.win_OD.selection)
		scrolled_window.set_child(column_view)
		vbox.append(scrolled_window)
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_spacing(16)
		button_box.set_homogeneous(False)
		#buttons
		if extraDB is None:
			button = Gtk.Button.new_with_mnemonic(label=_("Edit"))
			button.connect("clicked", self.openDatabaseEdit)
			button_box.append(button)
			button = Gtk.Button.new_with_mnemonic(label=_("Delete"))
			button.connect("clicked", self.openDatabaseDel)
			button_box.append(button)
			button = Gtk.Button.new_with_mnemonic(label=_("Open"))
			button.connect("clicked", self.openDatabaseOpen)
			button_box.append(button)
			button = Gtk.Button.new_with_mnemonic(label=_("Cancel"))
			button.connect("clicked", lambda w: self.win_OD.destroy())
			button_box.append(button)
		else:
			label=Gtk.Label(label=_("Search Name")+":")
			self.namesearch = Gtk.Entry()
			self.namesearch.set_max_length(34)
			self.namesearch.set_width_chars(24)
			self.namesearchbutton = Gtk.Button.new_with_mnemonic(label=_('Search'))
			self.namesearchbutton.connect("clicked", self.nameSearch)
			self.namesearch.connect("activate", self.nameSearch)
			self.nameresetbutton = Gtk.Button.new_with_mnemonic(label=_('Reset'))
			self.nameresetbutton.connect("clicked", self.nameSearchReset)
			button_box.append(self.nameresetbutton)
			button_box.append(label)
			button_box.append(self.namesearch)
			button_box.append(self.namesearchbutton)
			button = Gtk.Button.new_with_mnemonic(label=_("Open"))
			button.connect("clicked", self.openDatabaseOpen)
			button_box.prepend(button)
			button = Gtk.Button.new_with_mnemonic(label=_("Close"))
			button.connect("clicked", lambda w: self.win_OD.destroy())
			button_box.append(button)
		#display window
		vbox.append(button_box)
		self.win_OD.set_child(vbox)
		self.win_OD.present()
		return

	def openDatabaseEdit(self, widget):
		#get selection of selected item
		active = self.win_OD.selection.get_selected()
		self.oDE_list = self.DB[active]
		app.type="Radix"
		app.charttype = app.label["radix"]
		app.transit = False
		#self.updateChartList(widget, self.oDE_list)
		self.updateChartList(widget, self.oDE_list)
		self.eventData(edit=True)
		return

	def openDatabaseEditAsk(self, widget):
		#check for duplicate name without duplicate id
		en = app.db.getDatabase()
		for i, row in enumerate(en):
			if row["name"] == self.name.props.text and self.oDE_list["id"] == row["id"]:
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
		alert_dialog.set_buttons([_("Cancel"), _("OK")])
		alert_dialog.choose(parent=self, cancellable=None, callback=self.on_save_record, user_data=None)

	def on_save_record(self, source_obj, async_res, user_data):
		result = source_obj.choose_finish(async_res)
		if result == 1:
			#OK button clicked
			self.win_OD.destroy()
			self.openDatabaseEditSave()
		else:
			self.win_OD.present()
			dprint('rejected save to database')

	def openDatabaseOpen(self, widget):
		active = self.win_OD.selection.get_selected()
		self.oDE_list = self.DB[active]
		app.type="Radix"
		app.charttype = app.label["radix"]
		app.transit = False
		self.updateChartList(widget, self.oDE_list)
		self.win_OD.destroy()

	def openDatabaseEditSave(self):
		#update chart data
		self.updateChartData()
		#set query to save
		sql = 'UPDATE event_natal SET name=?,year=?,month=?,day=?,hour=?, geolon=?, geolat=?, altitude=?, location=?, timezone=?, notes=?, image=?, countrycode=?, timezonestr=?, geonameid=? WHERE id=?'
		values = (app.name, app.year, app.month, app.day, app.hour, app.geolon, app.geolat, app.altitude, app.location, app.timezone, '', '', app.countrycode,app.timezonestr,app.geonameid,self.oDE_list["id"])
		app.db.pquery([sql],[values])
		dprint('After editing saved to database: '+app.name)
		#widget.destroy()
		self.window2.destroy()
		#self.win_OD.destroy()
		self.openDatabase(extraDB=None)
		#self.openDatabase_callback( None, None)
		self.updateUI(first_time=False)

	def openDatabaseDel(self, widget):
		#get selection of selected item
		active = self.win_OD.selection.get_selected()
		del_record = self.DB[active]
		choosen_name = del_record['name']
		#ask for confirmation
		alert_dialog = Gtk.AlertDialog()
		alert_dialog.set_message(_("Caution"))
		confirm = _('You are about to delete record < {0} >. Proceed?').format(choosen_name)
		alert_dialog.set_detail(confirm)
		alert_dialog.set_modal(True)
		alert_dialog.set_buttons([_("Cancel"), _("OK")])
		alert_dialog.choose(parent=self, cancellable=None, callback=self.on_delete_perform, user_data=del_record)

	def on_delete_perform(self, source_obj, async_res, record):
		result = source_obj.choose_finish(async_res)
		if result == 1:
			#OK button clicked
			self.win_OD.close()
			self.openDatabaseDelDo(record)
		self.win_OD.present()

	def openDatabaseDelDo(self, del_rec):
		#get id from selection
		del_id = del_rec["id"]
		#delete database entry
		sql='DELETE FROM event_natal WHERE id='+str(del_id)
		app.db.pquery([sql])
		dprint('Deleted Database Entry: '+del_rec["name"])
		#dialog.destroy()
		#self.win_OD.destroy()
		self.openDatabase(extraDB=None)
		self.updateUI(first_time=False)

	def quickopendb_callback(self, action, parameter):
		idx = parameter.get_int32()
		action.set_state(parameter)
		for entry in self.DB:
			if entry['id'] == idx:
				self.updateChartList(None, entry)
				break

	def nameSearch(self, widget):
		self.listmodel.remove_all()
		self.DB = self.getDatabaseFamous(limit="15",search=self.namesearch.get_text())
		for data in self.DB:
			h,m,s = app.decHour(float(data["hour"]))
			dt_utc = datetime.datetime(int(data["year"]), int(data["month"]), int(data["day"]), h, m, s)
			dt = dt_utc + datetime.timedelta(seconds=float(data["timezone"])*float(3600))
			birth_date = str(dt.year)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':dt.month,'#2':dt.day,'#3':dt.hour,'#4':dt.minute,'#5':dt.second}
			event_data = EventData(ident=str(data["id"]),name=data["name"],birth=birth_date,location=data["location"])
			self.listmodel.append(event_data)
		return

	def nameSearchReset(self, widget):
		self.listmodel.remove_all()
		self.DB = self.getDatabaseFamous(limit="2000", search=None)
		for data in self.DB:
			h,m,s = app.decHour(float(data["hour"]))
			dt_utc=datetime.datetime(int(data["year"]),int(data["month"]),int(data["day"]),h,m,s)
			dt = dt_utc + datetime.timedelta(seconds=float(data["timezone"])*float(3600))
			birth_date = str(dt.year)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':dt.month,'#2':dt.day,'#3':dt.hour,'#4':dt.minute,'#5':dt.second}
			event_data = EventData(ident=str(data["id"]),name=data["name"],birth=birth_date,location=data["location"])
			self.listmodel.append(event_data)
		return

	def openDataFamous_callback(self, action, parameter):
		self.openDatabase(extraDB=self.getDatabaseFamous(limit="2000", search=None))

	def getDatabaseFamous(self, limit, search):
		""" Start searching from year 1800 onwards """
		self.flink = sqlite3.connect(app.cfg.famousdb)
		self.flink.row_factory = sqlite3.Row
		self.fcursor = self.flink.cursor()
		if search is not None:
			sql='SELECT * FROM famous WHERE year>? AND \
			(lastname LIKE ? OR firstname LIKE ? OR name LIKE ?) \
			LIMIT %s'%(limit)
			self.fcursor.execute(sql,(1800,search,search,search))
		else:
			sql='SELECT * FROM famous WHERE year>? LIMIT %s'%(limit)
			self.fcursor.execute(sql,(1800,))
		oldDB=self.fcursor.fetchall()
		self.fcursor.close()
		self.flink.close()
		#p rocess database
		newDB = []
		for a in range(len(oldDB)):
			# minus years
			if oldDB[a][12] == '571/': #Muhammad
				year = 571
			elif oldDB[a][12] <= 0:
				year = 1
			else:
				year = oldDB[a][12]
			month = oldDB[a][13]
			day = oldDB[a][14]
			hour = oldDB[a][15]
			h,m,s = app.decHour(hour)
			# aware datetime object
			dt_input = datetime.datetime(year,month,day,h,m,s)
			dt = pytz.timezone(oldDB[a][20]).localize(dt_input)
			# naive utc datetime object
			dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
			# timezone
			timezone=app.offsetToTz(dt.utcoffset())
			year = dt_utc.year
			month = dt_utc.month
			day = dt_utc.day
			hour = app.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
			newDB.append({
				"id":oldDB[a][0], #index
				"name":oldDB[a][3]+" "+oldDB[a][4], #christian name, name
				"year":year, #year
				"month":month, #month
				"day":day, #day
				"hour":hour, #hour
				"geolon":oldDB[a][18], #geolon
				"geolat":oldDB[a][17], #geolat
				"altitude":"25", #altitude
				"location":oldDB[a][16], #location
				"timezone":timezone, #timezone
				"notes":"",#notes
				"image":"",#image
				"countrycode":oldDB[a][8], #countrycode
				"geonameid":oldDB[a][19], #geonameid
				"timezonestr":oldDB[a][20], #timezonestr
				"extra":"" #extra
			})
		return newDB

	def chartType_callback(self, action, parameter):
		selected = parameter.get_string()
		action.set_state(parameter)
		if selected == "Synastry":
			selectstr = "Select for Synastry"
		elif selected == "Composite":
			selectstr = "Select for Composite"
		elif selected == "Combine":
			selectstr = "Select for Combine"
		self.openDatabaseSelect(selectstr, selected)

	def openDatabaseSelect(self, selectstr, ctype):
		self.win_OD = Gtk.Window()
		self.win_OD.set_title(_('Select Database Entry'))
		""" >>> set_icon """
		#self.win_OD.set_icon_from_file(app.cfg.iconWindow)
		self.win_OD.set_size_request(480, 480)
		#self.win_OD.move(150,150)
		#self.win_OD.connect("delete_event", lambda w,e: self.openDatabaseSelectReject())
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		vbox.set_vexpand(True)
		#define listmodel	
		self.win_OD.selection = Gtk.SingleSelection()
		self.listmodel = Gio.ListStore.new(EventData)
		self.win_OD.selection.set_model(self.listmodel)
		#add data from event_natal table
		self.DB = app.db.getDatabase()
		for data in self.DB:
			h,m,s = app.decHour(float(data["hour"]))
			dt_utc=datetime.datetime(int(data["year"]),int(data["month"]),int(data["day"]),h,m,s)
			dt = dt_utc + datetime.timedelta(seconds=float(data["timezone"])*float(3600))
			birth_date = str(dt.year)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':dt.month,'#2':dt.day,'#3':dt.hour,'#4':dt.minute,'#5':dt.second}
			event_data = EventData(str(data["id"]),data["name"],birth_date,data["location"])
			self.listmodel.append(event_data)
		#add columnview to scrolledwindow
		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_vexpand(True)

		column_view = Gtk.ColumnView()
		column_view.props.show_row_separators = False
		column_view.props.show_column_separators = True

		id_col = Gtk.ColumnViewColumn.new("Id")
		id_col.set_resizable(True)
		#id_col.set_fixed_width(112)
		id_factory = Gtk.SignalListItemFactory()
		id_factory.connect("setup", setup)
		id_factory.connect("bind", bind_ident)
		id_col.set_factory(id_factory)
		column_view.append_column(id_col)

		name_col = Gtk.ColumnViewColumn.new("Name")
		name_col.set_resizable(True)
		#name_col.set_fixed_width(112)
		name_factory = Gtk.SignalListItemFactory()
		name_factory.connect("setup", setup)
		name_factory.connect("bind", bind_name)
		name_col.set_factory(name_factory)
		column_view.append_column(name_col)

		birth_col = Gtk.ColumnViewColumn.new("Birth Date")
		birth_col.set_resizable(True)
		#birth_col.set_fixed_width(112)
		birth_factory = Gtk.SignalListItemFactory()
		birth_factory.connect("setup", setup)
		birth_factory.connect("bind", bind_birth)
		birth_col.set_factory(birth_factory)
		column_view.append_column(birth_col)

		location_col = Gtk.ColumnViewColumn.new("Location")
		location_col.set_resizable(True)
		#location_col.set_fixed_width(112)
		location_factory = Gtk.SignalListItemFactory()
		location_factory.connect("setup", setup)
		location_factory.connect("bind", bind_location)
		location_col.set_factory(location_factory)
		column_view.append_column(location_col)
		column_view.set_model(self.win_OD.selection)

		scrolled_window.set_child(column_view)
		vbox.append(scrolled_window)

		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_homogeneous(True)
		#buttons
		button = Gtk.Button.new_with_mnemonic(label=_('Cancel'))
		button.connect("clicked", lambda w: self.openDatabaseSelectReject())
		button_box.append(button)	
		button = Gtk.Button.new_with_mnemonic(label=selectstr)
		button.connect("clicked", lambda w: self.openDatabaseSelectReturn(ctype))
		button_box.prepend(button)		
		#display window
		vbox.append(button_box)
		self.win_OD.set_child(vbox)
		#self.win_OD_treeview.set_model(model=self.listmodel)
		self.win_OD.present()

	def openDatabaseSelectReject(self):
		self.win_OD.destroy()
		return

	def openDatabaseSelectReturn(self, ctype):
		active = self.win_OD.selection.get_selected()
		data_record = self.DB[active]
		#synastry
		if ctype == "Synastry":
			app.type="Transit"
			app.t_name=str(data_record["name"])
			app.t_year=int(data_record["year"])
			app.t_month=int(data_record["month"])
			app.t_day=int(data_record["day"])
			app.t_hour=float(data_record["hour"])
			app.t_geolon=float(data_record["geolon"])
			app.t_geolat=float(data_record["geolat"])
			app.t_altitude=int(data_record["altitude"])
			app.t_location=str(data_record["location"])
			app.t_timezone=float(data_record["timezone"])
			app.charttype="%s (%s)" % (app.label["synastry"],app.t_name)
			app.transit=True
			app.synastry=True
			#chart_name = app.makeSVG()
		elif ctype == "Composite":
			app.type="Composite"
			app.t_name=str(data_record["name"])
			app.t_year=int(data_record["year"])
			app.t_month=int(data_record["month"])
			app.t_day=int(data_record["day"])
			app.t_hour=float(data_record["hour"])
			app.t_geolon=float(data_record["geolon"])
			app.t_geolat=float(data_record["geolat"])
			app.t_altitude=int(data_record["altitude"])
			app.t_location=str(data_record["location"])
			app.t_timezone=float(data_record["timezone"])
			app.charttype="%s (%s)" % (app.label["composite"],app.t_name)
			app.transit=False
			app.synastry=False
			#chart_name = app.makeSVG()
		elif ctype == "Combine":
			app.type="Combine"
			app.t_name=str(data_record["name"])
			app.t_year=int(data_record["year"])
			app.t_month=int(data_record["month"])
			app.t_day=int(data_record["day"])
			app.t_hour=float(data_record["hour"])
			app.t_geolon=float(data_record["geolon"])
			app.t_geolat=float(data_record["geolat"])
			app.t_altitude=int(data_record["altitude"])
			app.t_location=str(data_record["location"])
			app.t_timezone=float(data_record["timezone"])
			#calculate combine between both utc times
			h,m,s = app.decHour(app.hour)
			dt1 = datetime.datetime(app.year,app.month,app.day,h,m,s)
			h,m,s = app.decHour(app.t_hour)
			dt2 = datetime.datetime(app.t_year,app.t_month,app.t_day,h,m,s)
			if dt1 > dt2:
				delta = dt1 - dt2
				hdelta = delta // 2
				combine = dt2 + hdelta
			else:
				delta = dt2 - dt1
				hdelta = delta // 2
				combine = dt1 + hdelta
			#take lon,lat middle
			app.c_geolon = (app.geolon + app.t_geolon)/2.0
			app.c_geolat = (app.geolat + app.t_geolat)/2.0
			app.c_altitude = (app.t_altitude + app.altitude)/2.0
			app.c_year = combine.year
			app.c_month = combine.month
			app.c_day = combine.day
			app.c_hour = app.decHourJoin(combine.hour,combine.minute,combine.second)
			app.charttype = "%s (%s)" % (app.label["combine"],app.t_name)
			app.transit = False
			app.synastry = False
			#set new date for printing in svg
			app.year = app.c_year
			app.month = app.c_month
			app.day = app.c_day
			app.hour = app.c_hour
			app.geolat = app.c_geolat
			app.geolon = app.c_geolon
			app.timezone_str = zonetab.nearest_tz(app.geolat,app.geolon,zonetab.timezones())[2]
			#aware datetime object
			dt_input = datetime.datetime(combine.year, combine.month, combine.day, combine.hour, combine.minute, combine.second)
			dt = pytz.timezone(app.timezone_str).localize(dt_input)
			app.timezone=app.offsetToTz(dt.utcoffset())
			app.utcToLocal()
		# synastry is drawn as transit chart, but has no transit date
		self.transitBar.set_visible(False)
		chart_name = app.makeSVG()
		self.image.setupSVG(chart_name)
		self.image.queue_resize()
		self.win_OD.close()

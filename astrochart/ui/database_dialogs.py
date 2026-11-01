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
Event databases: own events (open, edit, delete), famous people, selection
of the second event of synastry, composite and combine charts
"""

import datetime
import pytz
import sqlite3
from gi.repository import Gio, Gtk
from astrochart.ui.dialog import AstroDialog
from astrochart.ui.event_dialog import EventDialog, showDuplicateName
from astrochart.ui.widgets import EventData, bind_birth, bind_ident, bind_location, bind_name, setup
from astrochart.util import dprint

def loadFamous(cfg, chart, limit, search):
	""" famous people from year 1800 onwards as event records (times in UTC) """
	flink = sqlite3.connect(cfg.famousdb)
	flink.row_factory = sqlite3.Row
	fcursor = flink.cursor()
	if search is not None:
		sql='SELECT * FROM famous WHERE year>? AND \
		(lastname LIKE ? OR firstname LIKE ? OR name LIKE ?) \
		LIMIT %s'%(limit)
		fcursor.execute(sql,(1800,search,search,search))
	else:
		sql='SELECT * FROM famous WHERE year>? LIMIT %s'%(limit)
		fcursor.execute(sql,(1800,))
	oldDB=fcursor.fetchall()
	fcursor.close()
	flink.close()
	#process database
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
		h,m,s = chart.decHour(hour)
		# aware datetime object
		dt_input = datetime.datetime(year,month,day,h,m,s)
		dt = pytz.timezone(oldDB[a][20]).localize(dt_input)
		# naive utc datetime object
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		# timezone
		timezone=chart.offsetToTz(dt.utcoffset())
		year = dt_utc.year
		month = dt_utc.month
		day = dt_utc.day
		hour = chart.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
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

def confirm(parent, message, callback, user_data=None):
	"""ask Cancel/OK, callback(answer_ok, user_data)"""
	alert_dialog = Gtk.AlertDialog()
	alert_dialog.set_message(_("Caution"))
	alert_dialog.set_detail(message)
	alert_dialog.set_modal(True)
	alert_dialog.set_buttons([_("Cancel"), _("OK")])
	def answer(source_obj, async_res, data):
		callback(source_obj.choose_finish(async_res) == 1, data)
	alert_dialog.choose(parent=parent, cancellable=None, callback=answer, user_data=user_data)

class EventListWindow(AstroDialog):
	"""list of event records: id, name, local birth date, location"""

	def __init__(self, window, title):
		super().__init__(window, title=title)
		self.records = []
		self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
		self.selection = Gtk.SingleSelection()
		self.listmodel = Gio.ListStore.new(EventData)
		self.selection.set_model(self.listmodel)
		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_vexpand(True)
		column_view = Gtk.ColumnView()
		column_view.props.show_row_separators = False
		column_view.props.show_column_separators = True
		for title, bind in (("Id", bind_ident), ("Name", bind_name), ("Birth Date", bind_birth), ("Location", bind_location)):
			factory = Gtk.SignalListItemFactory()
			factory.connect("setup", setup)
			factory.connect("bind", bind)
			column = Gtk.ColumnViewColumn.new(title=title, factory=factory)
			column.set_resizable(True)
			column_view.append_column(column)
		column_view.set_model(self.selection)
		scrolled_window.set_child(column_view)
		self.vbox.append(scrolled_window)
		self.set_child(self.vbox)

	def fill(self, records):
		"""show the records, birth date in local time"""
		self.records = records
		self.listmodel.remove_all()
		for data in records:
			h,m,s = self.chart.decHour(float(data["hour"]))
			dt_utc = datetime.datetime(int(data["year"]), int(data["month"]), int(data["day"]), h, m, s)
			dt = dt_utc + datetime.timedelta(seconds=float(data["timezone"])*float(3600))
			birth_date = str(dt.year)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':dt.month,'#2':dt.day,'#3':dt.hour,'#4':dt.minute,'#5':dt.second}
			self.listmodel.append(EventData(ident=str(data["id"]),name=data["name"],birth=birth_date,location=data["location"]))

	def selectedRecord(self):
		"""record of the selected line, None without selection"""
		active = self.selection.get_selected()
		if active == Gtk.INVALID_LIST_POSITION or active >= len(self.records):
			return None
		return self.records[active]

	def openSelected(self):
		"""radix chart of the selected record"""
		record = self.selectedRecord()
		if record is None:
			return
		self.window.updateChartList(None, record)
		self.close()

class DatabaseDialog(EventListWindow):
	"""own events of peopledb: edit, delete, open"""

	def __init__(self, window):
		super().__init__(window, _('Open Database Entry'))
		self.set_default_size(480, 480)
		self.vbox.props.margin_start = 12
		self.vbox.props.margin_end = 12
		self.vbox.props.margin_top = 6
		self.vbox.props.margin_bottom = 6
		self.fill(self.db.getDatabase())
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_spacing(16)
		button_box.set_homogeneous(False)
		for label, callback in ((_("Edit"), self.edit), (_("Delete"), self.delete),
			(_("Open"), self.openSelected), (_("Cancel"), self.close)):
			button = Gtk.Button.new_with_mnemonic(label=label)
			button.connect("clicked", lambda w, callback=callback: callback())
			button_box.append(button)
		self.vbox.append(button_box)

	def reopen(self):
		"""close and show the list again (after changes of the database)"""
		self.close()
		self.window.presentDialog('database', DatabaseDialog)
		self.window.updateUI(first_time=False)

	def edit(self):
		self.editRecord = self.selectedRecord()
		if self.editRecord is None:
			return
		self.window.updateChartList(None, self.editRecord)
		self.window.presentDialog('event', EventDialog, edit=True, on_save=self.saveAsk)

	def saveAsk(self, dialog):
		#the event dialog edits self.editRecord, check for the name in another entry
		for row in self.db.getDatabase():
			if row["name"] == dialog.name.props.text and self.editRecord["id"] != row["id"]:
				showDuplicateName(dialog)
				return
		confirm(dialog, _('Are you sure you want to save < {0} > to the database?').format(dialog.name.props.text),
			self.saveAnswer, dialog)

	def saveAnswer(self, ok, dialog):
		if not ok:
			dprint('rejected save to database')
			self.present()
			return
		#update chart data
		dialog.updateChartData()
		#set query to save
		sql = 'UPDATE event_natal SET name=?,year=?,month=?,day=?,hour=?, geolon=?, geolat=?, altitude=?, location=?, timezone=?, notes=?, image=?, countrycode=?, timezonestr=?, geonameid=? WHERE id=?'
		values = (self.chart.name, self.chart.year, self.chart.month, self.chart.day, self.chart.hour, self.chart.geolon, self.chart.geolat, self.chart.altitude, self.chart.location, self.chart.timezone, '', '', self.chart.countrycode,self.chart.timezonestr,self.chart.geonameid,self.editRecord["id"])
		self.db.pquery([sql],[values])
		dprint('After editing saved to database: '+self.chart.name)
		dialog.close()
		self.reopen()

	def delete(self):
		record = self.selectedRecord()
		if record is None:
			return
		confirm(self, _('You are about to delete record < {0} >. Proceed?').format(record['name']),
			self.deleteAnswer, record)

	def deleteAnswer(self, ok, record):
		if not ok:
			self.present()
			return
		#delete database entry
		sql='DELETE FROM event_natal WHERE id=?'
		self.db.pquery([sql], [(record["id"],)])
		dprint('Deleted Database Entry: '+record["name"])
		self.reopen()

class FamousDialog(EventListWindow):
	"""famous people database with search by name"""

	def __init__(self, window):
		super().__init__(window, _('Open Database Entry'))
		self.set_default_size(480, 480)
		self.vbox.props.margin_start = 12
		self.vbox.props.margin_end = 12
		self.vbox.props.margin_top = 6
		self.vbox.props.margin_bottom = 6
		self.fill(loadFamous(self.cfg, self.chart, limit="2000", search=None))
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_spacing(16)
		button_box.set_homogeneous(False)
		label=Gtk.Label(label=_("Search Name")+":")
		self.namesearch = Gtk.Entry()
		self.namesearch.set_max_length(34)
		self.namesearch.set_width_chars(24)
		self.namesearchbutton = Gtk.Button.new_with_mnemonic(label=_('Search'))
		self.namesearchbutton.connect("clicked", lambda w: self.search())
		self.namesearch.connect("activate", lambda w: self.search())
		self.nameresetbutton = Gtk.Button.new_with_mnemonic(label=_('Reset'))
		self.nameresetbutton.connect("clicked", lambda w: self.reset())
		button = Gtk.Button.new_with_mnemonic(label=_("Open"))
		button.connect("clicked", lambda w: self.openSelected())
		button_box.append(button)
		button_box.append(self.nameresetbutton)
		button_box.append(label)
		button_box.append(self.namesearch)
		button_box.append(self.namesearchbutton)
		button = Gtk.Button.new_with_mnemonic(label=_("Close"))
		button.connect("clicked", lambda w: self.close())
		button_box.append(button)
		self.vbox.append(button_box)

	def search(self):
		self.fill(loadFamous(self.cfg, self.chart, limit="15", search=self.namesearch.get_text()))

	def reset(self):
		self.fill(loadFamous(self.cfg, self.chart, limit="2000", search=None))

class SelectEventDialog(EventListWindow):
	"""second event of synastry, composite or combine charts"""

	SELECT = {"Synastry": "Select for Synastry", "Composite": "Select for Composite", "Combine": "Select for Combine"}

	def __init__(self, window, ctype):
		super().__init__(window, _('Select Database Entry'))
		self.ctype = ctype
		self.set_size_request(480, 480)
		self.fill(self.db.getDatabase())
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_homogeneous(True)
		button = Gtk.Button.new_with_mnemonic(label=_(self.SELECT[ctype]))
		button.connect("clicked", lambda w: self.select())
		button_box.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_('Cancel'))
		button.connect("clicked", lambda w: self.close())
		button_box.append(button)
		self.vbox.append(button_box)

	def select(self):
		record = self.selectedRecord()
		if record is None:
			return
		if self.ctype == "Synastry":
			self.chart.setSynastry(record)
		elif self.ctype == "Composite":
			self.chart.setComposite(record)
		elif self.ctype == "Combine":
			self.chart.setCombine(record)
		# synastry is drawn as transit chart, but has no transit date
		self.window.transitBar.set_visible(False)
		self.window.updateChart()
		self.close()

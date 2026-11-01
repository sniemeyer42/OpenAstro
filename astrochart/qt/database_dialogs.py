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
Event databases: own events (open, edit, delete) and famous people, both
with a name filter
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QDialogButtonBox, QHeaderView, QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout
from astrochart.events import deleteEvent, loadFamous, localDate, nameTaken, updateEvent
from astrochart.qt.dialog import AstroDialog, Button, confirm
from astrochart.qt.event_dialog import EventDialog, duplicateName

RECORD = Qt.ItemDataRole.UserRole

class EventListDialog(AstroDialog):
	"""list of event records (name, local birth date, location), filtered by name"""

	def __init__(self, window, title):
		super().__init__(window, title, modal=False)
		self.resize(620, 560)
		self.records = []
		self.layout = QVBoxLayout(self)
		self.filter = QLineEdit()
		self.filter.setPlaceholderText(_("Search Name"))
		self.filter.setClearButtonEnabled(True)
		self.filter.textChanged.connect(self.applyFilter)
		self.layout.addWidget(self.filter)
		self.tree = QTreeWidget()
		self.tree.setColumnCount(3)
		self.tree.setHeaderLabels([_("Name"), _("Birth Date (Local)"), _("Location")])
		self.tree.setRootIsDecorated(False)
		self.tree.setUniformRowHeights(True)
		self.tree.setAlternatingRowColors(True)
		self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
		self.tree.setSortingEnabled(True)
		self.tree.sortByColumn(-1, Qt.SortOrder.AscendingOrder)
		header = self.tree.header()
		header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
		header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
		header.setStretchLastSection(True)
		self.tree.itemActivated.connect(lambda item, column: self.openSelected())
		self.layout.addWidget(self.tree, 1)

	def fill(self, records):
		"""show the records, birth date in local time; the selected entry stays selected"""
		selected = self.selectedRecord()
		self.records = records
		self.tree.clear()
		items = []
		for index, record in enumerate(records):
			item = QTreeWidgetItem([str(record["name"]), localDate(self.chart, record), str(record["location"])])
			item.setData(0, RECORD, index)
			items.append(item)
			if selected is not None and record["id"] == selected["id"]:
				current = item
		self.tree.addTopLevelItems(items)
		self.tree.resizeColumnToContents(0)
		self.tree.setColumnWidth(0, min(self.tree.columnWidth(0) + 16, 260))
		if selected is not None and any(record["id"] == selected["id"] for record in records):
			self.tree.setCurrentItem(current)
		self.applyFilter(self.filter.text())

	def applyFilter(self, text):
		text = text.strip().casefold()
		for i in range(self.tree.topLevelItemCount()):
			item = self.tree.topLevelItem(i)
			item.setHidden(text not in item.text(0).casefold())
		#the first entry shown is selected if the selected one is hidden
		current = self.tree.currentItem()
		if current is None or current.isHidden():
			for i in range(self.tree.topLevelItemCount()):
				item = self.tree.topLevelItem(i)
				if not item.isHidden():
					self.tree.setCurrentItem(item)
					break

	def selectedRecord(self):
		"""record of the selected line, None without selection"""
		item = self.tree.currentItem()
		if item is None or item.isHidden():
			return None
		return self.records[item.data(0, RECORD)]

	def openSelected(self):
		"""radix chart of the selected record"""
		record = self.selectedRecord()
		if record is None:
			return
		self.window.openRecord(record)
		self.close()

class DatabaseDialog(EventListDialog):
	"""own events of the event database: edit, delete, open"""

	def __init__(self, window):
		super().__init__(window, _('Open Database Entry'))
		self.editRecord = None
		self.fill(self.db.getDatabase())
		self.layout.addWidget(self.buttonBox(Button.Open | Button.Close, {Button.Open: self.openSelected},
			[(_("Edit"), QDialogButtonBox.ButtonRole.ActionRole, self.edit),
			(_("Delete"), QDialogButtonBox.ButtonRole.ActionRole, self.delete)]))
		self.button[Button.Open].setDefault(True)
		self.filter.setFocus()

	def refresh(self):
		"""the event database changed"""
		self.fill(self.db.getDatabase())

	def edit(self):
		"""edit the selected entry in the event dialog, its chart is shown"""
		self.editRecord = self.selectedRecord()
		if self.editRecord is None:
			return
		self.window.openRecord(self.editRecord)
		self.window.presentDialog('event', lambda: EventDialog(self.window, on_save=self.saveEdited, parent=self), replace=True)

	def saveEdited(self, dialog):
		#the event dialog edits self.editRecord, the name must not be taken by another entry
		name = dialog.name.text()
		if nameTaken(self.db, name, self.editRecord["id"]):
			duplicateName(dialog)
			return
		if not confirm(dialog, _('Are you sure you want to save < {0} > to the database?').format(name)):
			return
		if dialog.apply():
			updateEvent(self.db, self.chart, self.editRecord["id"])
			dialog.close()
			self.window.databaseChanged()

	def delete(self):
		record = self.selectedRecord()
		if record is None:
			return
		if confirm(self, _('You are about to delete record < {0} >. Proceed?').format(record['name'])):
			deleteEvent(self.db, record)
			self.window.databaseChanged()

class FamousDialog(EventListDialog):
	"""famous people database"""

	def __init__(self, window):
		super().__init__(window, _('Open Famous People Database'))
		self.fill(loadFamous(self.cfg, self.chart))
		self.layout.addWidget(self.buttonBox(Button.Open | Button.Close, {Button.Open: self.openSelected}))
		self.button[Button.Open].setDefault(True)
		self.filter.setFocus()

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
Main window: menu bar, tool bar, chart wheel and lists
"""

from html import escape
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPalette
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QMessageBox, QSizePolicy, QSplitter, QToolBar,
	QToolButton, QVBoxLayout, QWidget)
from astrochart.constants import LIMIT, OFFSET, RATIO, VERSION
from astrochart.qt.chart_types import TransitBar, askMonth, askProgression, askSolarReturn
from astrochart.qt.chart_view import ChartView
from astrochart.qt.database_dialogs import DatabaseDialog, FamousDialog
from astrochart.qt.event_dialog import EventDialog
from astrochart.qt.files import ChartFiles
from astrochart.qt.here_and_now import HereAndNowBar
from astrochart.qt.panels import ChartPanels, listFontSize
from astrochart.qt.settings_aspects import AspectSettingsDialog
from astrochart.qt.settings_configuration import ConfigurationDialog
from astrochart.qt.settings_location import LocationDialog
from astrochart.qt.settings_planets import PlanetSettingsDialog
from astrochart.qt.symbols import Symbols
from astrochart.qt.table_windows import CuspAspectsWindow, TimelineWindow

def themeIcon(*names):
	"""first icon of the theme of names, empty icon if there is none"""
	for name in names:
		if QIcon.hasThemeIcon(name):
			return QIcon.fromTheme(name)
	return QIcon()

class MainWindow(QMainWindow):

	def __init__(self, app):
		super().__init__()
		#the application, the chart shown, configuration and databases
		self.app = app
		self.chart = app.chart
		self.cfg = app.cfg
		self.db = app.db
		#open table windows, see refreshTableWindows
		self.tableWindows = set()
		#open dialogs of which only one may exist, see presentDialog
		self.dialogs = {}
		#file dialogs, import, export and printing
		self.files = ChartFiles(self)
		self.symbols = Symbols()
		#the modern wheel is drawn for the background of the window
		self.chart.dark = self.isDark()
		#chart wheel with the date bar of transits above, lists beside
		self.transitBar = TransitBar(self)
		self.nowBar = HereAndNowBar(self)
		self.image = ChartView(self.chartSVGs(), self.chart, self.selectBody)
		self.image.viewport().setBackgroundRole(QPalette.ColorRole.Window)
		chartArea = QWidget()
		layout = QVBoxLayout(chartArea)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)
		layout.addWidget(self.transitBar)
		layout.addWidget(self.nowBar)
		layout.addWidget(self.image, 1)
		self.panels = ChartPanels(self, self.symbols, listFontSize(self.db.astrocfg.get('listfontsize')))
		self.panels.setMinimumWidth(280)
		self.splitter = QSplitter(Qt.Orientation.Horizontal)
		self.splitter.addWidget(chartArea)
		self.splitter.addWidget(self.panels)
		self.splitter.setStretchFactor(0, 1)
		self.splitter.setStretchFactor(1, 0)
		self.splitter.setCollapsible(0, False)
		self.setCentralWidget(self.splitter)
		self.createActions()
		self.createMenus()
		self.createToolBar()
		#chart type, date and place
		self.status = QLabel()
		self.statusBar().addWidget(self.status, 1)
		#size: most of the screen height, the wheel beside the lists
		screen = self.screen().availableGeometry()
		height = max(480, screen.height() - OFFSET)
		width = min(screen.width(), int(height * RATIO))
		self.resize(width, height)
		self.splitter.setSizes([int(width * 0.68), int(width * 0.32)])
		self.updateTitle()
		self.panels.update()
		#the chart at the start: 'Here and Now', following the clock
		self.nowBar.setIcons(themeIcon('mark-location', 'find-location', 'gps'), themeIcon('chronometer', 'clock', 'appointment-soon'))
		self.nowBar.start()

	""" Actions, menus and tool bar """

	def action(self, text, slot=None, shortcut=None, icon=None, checkable=False, enabled=True):
		action = QAction(text, self)
		if icon is not None:
			action.setIcon(icon)
		if shortcut is not None:
			if isinstance(shortcut, (list, tuple)):
				action.setShortcuts([QKeySequence(key) for key in shortcut])
			else:
				action.setShortcut(QKeySequence(shortcut))
		action.setCheckable(checkable)
		if slot is not None:
			action.triggered.connect(slot)
		action.setEnabled(enabled)
		self.addAction(action)
		return action

	def createActions(self):
		Key = QKeySequence.StandardKey
		self.newAction = self.action(_('New'), self.newEvent, Key.New, themeIcon('document-new'))
		self.openAction = self.action(_('Open'), self.files.openChart, Key.Open, themeIcon('document-open'))
		self.saveAction = self.action(_('Save'), self.files.saveChart, Key.Save, themeIcon('document-save'))
		self.printAction = self.action(_('Print'), self.files.printChart, Key.Print, themeIcon('document-print'))
		self.quitAction = self.action(_('Quit'), self.close, Key.Quit, themeIcon('application-exit'))
		self.editAction = self.action(_('Edit Event'), self.editEvent, 'Ctrl+E', themeIcon('document-edit', 'document-properties'))
		self.databaseAction = self.action(_('Open Database'), lambda: self.presentDialog('database', lambda: DatabaseDialog(self)),
			'Ctrl+D', themeIcon('x-office-address-book', 'document-open'))
		self.famousAction = self.action(_('Open Famous People Database'), lambda: self.presentDialog('famous', lambda: FamousDialog(self)))
		self.hereNowAction = self.action(_('Here and Now'), self.showHereAndNow, 'Ctrl+H', themeIcon('chronometer', 'clock', 'appointment-soon'))
		self.radixAction = self.action(_('Radix Chart'), self.showRadix, 'Ctrl+R')
		self.transitAction = self.action(_('Transit Chart'), self.transitBar.start, 'Ctrl+T')
		self.solarAction = self.action(_('Solar Return'), lambda: askSolarReturn(self))
		self.progressionAction = self.action(_('Solar Progression'), lambda: askProgression(self))
		self.timelineAction = self.action(_('Monthly Timeline'), self.showTimeline)
		self.cuspAspectsAction = self.action(_('Cusp Aspects'), lambda: CuspAspectsWindow(self).show())
		self.zoomInAction = self.action(_('In'), lambda: self.image.setScale(self.image.scale * 1.25),
			(Key.ZoomIn, 'Ctrl+='), themeIcon('zoom-in'))
		self.zoomOutAction = self.action(_('Out'), lambda: self.image.setScale(self.image.scale / 1.25),
			Key.ZoomOut, themeIcon('zoom-out'))
		self.zoomActions = []
		for percent, shortcut in ((80, None), (100, ('Ctrl+0', 'Ctrl+1')), (150, None), (200, None)):
			action = self.action('%d%%' % percent, lambda checked=False, scale=percent / 100.0: self.image.setScale(scale), shortcut)
			self.zoomActions.append(action)
		self.zoomActions[1].setIcon(themeIcon('zoom-original'))
		self.listsAction = self.action(_('Lists'), self.showLists, 'F9', themeIcon('sidebar-show', 'view-right-new', 'view-split-left-right'), checkable=True)
		self.listsAction.setChecked(True)
		self.maximizeAction = self.action(_('Maximize'), self.setMaximized, None, themeIcon('view-fullscreen', 'window-maximize'), checkable=True)
		self.locationAction = self.action(_('Set Location'), lambda: self.presentDialog('location', lambda: LocationDialog(self)))
		self.configurationAction = self.action(_('General Configuration'), lambda: self.presentDialog('configuration', lambda: ConfigurationDialog(self)),
			None, themeIcon('configure', 'preferences-system'))
		self.aspectsAction = self.action(_('Aspects'), lambda: self.presentDialog('aspects', lambda: AspectSettingsDialog(self)))
		self.planetsAction = self.action(_('Planets & Angles'), lambda: self.presentDialog('planets', lambda: PlanetSettingsDialog(self)))
		self.exportDatabaseAction = self.action(_('Export Database'), self.files.exportDatabase)
		self.importDatabaseAction = self.action(_('Import Database'), self.files.importDatabase)
		self.aboutAction = self.action(_('About'), self.about, None, themeIcon('help-about'))
		self.aboutQtAction = self.action('%s Qt' % _('About'), QApplication.aboutQt, None, themeIcon('qtlogo'))
		#escape: no selected body
		self.action('', self.clearSelection, 'Escape')

	def showLists(self, visible):
		self.panels.setVisible(visible)

	def setListFontSize(self, size):
		"""font size of the lists (points), kept in the configuration"""
		size = listFontSize(size)
		self.db.setAstrocfg('listfontsize', '%g' % (size))
		self.panels.setFontSize(size)

	def setMaximized(self, maximized):
		if maximized:
			self.showMaximized()
		else:
			self.showNormal()

	def changeEvent(self, event):
		if event.type() == QEvent.Type.WindowStateChange:
			self.maximizeAction.setChecked(self.isMaximized())
		elif event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange):
			self.onPaletteChanged()
		super().changeEvent(event)

	def createMenus(self):
		bar = self.menuBar()
		#chart: file operations and history
		menu = bar.addMenu(_('Chart'))
		menu.addAction(self.newAction)
		menu.addAction(self.openAction)
		self.historyMenu = self.dynamicMenu(menu, _('History'), self.fillHistory)
		menu.addAction(self.saveAction)
		menu.addSeparator()
		submenu = menu.addMenu(_('Import'))
		for label, kind in (('Oroboros (*.xml)', 'Oroboros'), ('Astrolog (*.dat)', 'Astrolog'),
			('Skylendar (*.skif)', 'Skylendar'), ('Zet8 Dbase (*.zbs)', 'Zet8')):
			submenu.addAction(_(label), lambda kind=kind: self.files.importChart(kind))
		submenu = menu.addMenu(_('Export'))
		for label, kind in (('PNG file', 'png'), ('JPG file', 'jpg'), ('SVG file', 'svg'), ('PDF file', 'pdf')):
			submenu.addAction(_(label), lambda kind=kind: self.files.export(kind))
		menu.addSeparator()
		menu.addAction(self.printAction)
		menu.addSeparator()
		menu.addAction(self.quitAction)
		#event: the event database
		menu = bar.addMenu(_('Event'))
		menu.addAction(self.editAction)
		self.quickMenu = self.dynamicMenu(menu, _('Quick Open Database'), self.fillQuickOpen)
		menu.addAction(self.databaseAction)
		menu.addAction(self.famousAction)
		#chart types, the second event of synastry, composite and combine from the event database
		self.chartTypesMenu = menu = bar.addMenu(_('Chart Types'))
		menu.addAction(self.hereNowAction)
		menu.addSeparator()
		menu.addAction(self.radixAction)
		menu.addAction(self.transitAction)
		menu.addSeparator()
		for label, ctype in ((_('Synastry Chart'), 'Synastry'), (_('Composite Chart'), 'Composite'), (_('Combine Chart'), 'Combine')):
			self.dynamicMenu(menu, label, lambda submenu, ctype=ctype: self.fillSecondEvent(submenu, ctype))
		menu.addSeparator()
		menu.addAction(self.solarAction)
		menu.addAction(self.progressionAction)
		#tables
		menu = bar.addMenu(_('Tables'))
		menu.addAction(self.timelineAction)
		menu.addAction(self.cuspAspectsAction)
		#view: zoom, lists
		menu = bar.addMenu(_('Zoom'))
		menu.addAction(self.zoomInAction)
		menu.addAction(self.zoomOutAction)
		menu.addSeparator()
		for action in self.zoomActions:
			menu.addAction(action)
		menu.addSeparator()
		menu.addAction(self.listsAction)
		menu.addAction(self.maximizeAction)
		#settings
		menu = bar.addMenu(_('Settings'))
		menu.addAction(self.locationAction)
		menu.addAction(self.configurationAction)
		menu.addAction(self.aspectsAction)
		menu.addAction(self.planetsAction)
		menu.addSeparator()
		menu.addAction(self.exportDatabaseAction)
		menu.addAction(self.importDatabaseAction)
		#help
		menu = bar.addMenu(_('Help'))
		menu.addAction(self.aboutAction)
		menu.addAction(self.aboutQtAction)

	def dynamicMenu(self, menu, title, fill):
		"""submenu filled by fill(submenu) whenever it opens"""
		submenu = menu.addMenu(title)
		submenu.aboutToShow.connect(lambda: fill(submenu))
		#the entries for keyboard navigation before the first opening
		fill(submenu)
		return submenu

	@staticmethod
	def fillMenu(submenu, entries, slot):
		"""replace the entries of submenu by entries (label, record) calling slot(record)"""
		submenu.clear()
		for label, record in entries:
			#ampersands of names are no mnemonics
			action = submenu.addAction(str(label).replace('&', '&&'))
			action.triggered.connect(lambda checked=False, record=record: slot(record))
		if not entries:
			submenu.addAction('—').setEnabled(False)

	def fillHistory(self, submenu):
		#the last LIMIT entries, last first
		history = list(reversed(self.db.history))[:LIMIT]
		self.fillMenu(submenu, [(entry['name'], entry) for entry in history], self.openRecord)

	def fillQuickOpen(self, submenu):
		self.fillMenu(submenu, [(entry['name'], entry) for entry in self.db.getDatabase()], self.openRecord)

	def fillSecondEvent(self, submenu, ctype):
		self.fillMenu(submenu, [(entry['name'], entry) for entry in self.db.getDatabase()],
			lambda record: self.setSecondEvent(ctype, record))

	def createToolBar(self):
		toolbar = QToolBar(_('Menu'))
		toolbar.setObjectName('mainToolBar')
		toolbar.setMovable(False)
		toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonFollowStyle)
		toolbar.addAction(self.newAction)
		toolbar.addAction(self.editAction)
		toolbar.addAction(self.databaseAction)
		toolbar.addSeparator()
		toolbar.addAction(self.hereNowAction)
		button = QToolButton()
		button.setText(_('Chart Types'))
		button.setMenu(self.chartTypesMenu)
		button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
		button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
		toolbar.addWidget(button)
		toolbar.addSeparator()
		toolbar.addAction(self.printAction)
		spacer = QWidget()
		spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
		toolbar.addWidget(spacer)
		toolbar.addAction(self.listsAction)
		self.addToolBar(toolbar)

	""" Dialogs """

	def presentDialog(self, name, factory, replace=False):
		"""
		show the dialog of a kind, only one at a time: factory() creates it,
		an open one is raised (closed and created again if replace)
		"""
		dialog = self.dialogs.get(name)
		if dialog is not None and replace:
			dialog.close()
			dialog = None
		if dialog is None:
			dialog = factory()
			self.dialogs[name] = dialog
			dialog.finished.connect(lambda result, name=name, dialog=dialog: self.forgetDialog(name, dialog))
		dialog.show()
		dialog.raise_()
		dialog.activateWindow()
		return dialog

	def forgetDialog(self, name, dialog):
		if self.dialogs.get(name) is dialog:
			del self.dialogs[name]

	def newEvent(self):
		"""event dialog with a new event: now, at the home location"""
		self.presentDialog('event', lambda: EventDialog(self, new=True), replace=True)

	def editEvent(self):
		self.presentDialog('event', lambda: EventDialog(self))

	def databaseChanged(self):
		#the database window shows the changed entries (menus are filled when they open)
		dialog = self.dialogs.get('database')
		if dialog is not None:
			dialog.refresh()

	""" Chart """

	def chartSVGs(self):
		"""calculate the chart: wheel for the window (returned) and the printed
		page for export and scripts (self.chartSVG), symbols of the lists"""
		td = self.chart.templateData()
		#template data of the wheel shown, redrawn when the selection changes
		self.wheelData = td
		wheel = self.chart.makeWheelSVG(td)
		self.saveChartSVG(self.chart.makePrintSVG(td))
		self.symbols.update(wheel, chip=not self.chart.modernStyle())
		return wheel

	def saveChartSVG(self, svg):
		#the chart shown, also kept as file for scripts
		self.chartSVG = svg
		with open(self.cfg.tempfilename, 'w') as f:
			f.write(svg)

	def updateChart(self):
		self.image.setupSVG(self.chartSVGs())
		self.updateTitle()
		self.panels.update()
		# date bar belongs to transit charts only (synastry: no date)
		if self.chart.type != "Transit" or self.chart.synastry:
			self.transitBar.setVisible(False)
		#time bar as long as the chart is 'Here and Now'
		self.nowBar.follow()

	def refreshChart(self):
		#redraw the chart after changed settings, keep zoom level
		scale = self.image.scale
		self.updateChart()
		self.image.setScale(scale)

	def updateTitle(self):
		#chart name in the title, type, local date and place in the status bar
		chart = self.chart
		date = '%s-%02d-%02d %02d:%02d' % (chart.year_loc, chart.month_loc, chart.day_loc, chart.hour_loc, chart.minute_loc)
		self.setWindowTitle(str(chart.name))
		self.status.setText('%s  ·  %s  ·  %s' % (chart.charttype, date, chart.location))

	def openRecord(self, record):
		#radix chart of a database or history record
		self.chart.setEvent(record)
		self.updateChart()

	def showHereAndNow(self):
		"""chart 'Here and Now' at the home location, following the clock"""
		self.nowBar.start()

	def showRadix(self):
		self.chart.type = "Radix"
		self.chart.charttype = self.chart.label["radix"]
		self.chart.transit = False
		self.updateChart()

	def setSecondEvent(self, ctype, record):
		"""synastry, composite or combine chart with record as second event"""
		if ctype == "Synastry":
			self.chart.setSynastry(record)
		elif ctype == "Composite":
			self.chart.setComposite(record)
		elif ctype == "Combine":
			self.chart.setCombine(record)
		# synastry is drawn as transit chart, but has no transit date
		self.transitBar.setVisible(False)
		self.updateChart()

	def selectBody(self, side, ident):
		"""select a body (or none): its aspects are highlighted in wheel and lists"""
		selection = None if side is None else (side, ident)
		if selection == self.chart.highlight:
			selection = None
		self.chart.highlight = selection
		self.wheelData = self.chart.redrawAspects(self.wheelData)
		self.image.replaceSVG(self.chart.makeWheelSVG(self.wheelData))
		self.panels.updateSelection()

	def clearSelection(self):
		if self.chart.highlight is not None:
			self.selectBody(None, None)

	def isDark(self):
		"""True if the window has a dark background"""
		return QApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128

	def onPaletteChanged(self):
		#the modern wheel and its symbols in the lists follow light or dark colours
		dark = self.isDark()
		if dark != self.chart.dark and hasattr(self, 'panels'):
			self.chart.dark = dark
			wheel = self.chart.makeWheelSVG(self.wheelData)
			self.symbols.update(wheel, chip=not self.chart.modernStyle())
			self.image.replaceSVG(wheel)
			self.panels.update()

	""" Tables """

	def showTimeline(self):
		month = askMonth(self)
		if month is not None:
			TimelineWindow(self, *month).show()

	def refreshTableWindows(self, changed):
		#redraw open table windows using the changed settings (chart types)
		for window in list(self.tableWindows):
			if window.settings in changed and window.isVisible():
				window.refresh()

	def about(self):
		box = QMessageBox(self)
		box.setWindowTitle(_('About'))
		box.setIconPixmap(QIcon(self.cfg.iconWindow).pixmap(96, 96))
		with open(self.cfg.comments, "r") as f:
			comments = f.read()
		with open(self.cfg.license, "r") as f:
			box.setDetailedText(f.read())
		box.setText('<h3>OpenAstro.org - Open Source Astrology</h3><p>%s</p>' % escape(VERSION))
		box.setInformativeText('<p>%s</p><p>Pelle van der Scheer, Amsterdam / The Netherlands<br>'
			'Erich Küster, Krefeld / Nortrhine-Westfalia / Germany</p>'
			'<p>Copyright © 2012-2026 Pelle van der Scheer. All rights reserved.</p>'
			'<p><a href="https://github.com/ekuester/OpenAstro">github.com/ekuester/OpenAstro</a></p>' % escape(comments).replace('\n', '<br>'))
		box.exec()

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
Functional test of the Qt program (offscreen, no display needed): menus,
quick open and history, interactive wheel and lists, chart types, zoom,
tables, export, print, chart files, database export/import, the dialogs
(event, event database, famous people, home location, configuration,
aspects, planets), font size of the lists, light and dark colours. File,
print, input and message dialogs are answered by stand-ins.

	HOME=$(mktemp -d) python3 tests/qt_flows.py
"""
import os
import sys
import shutil
import sqlite3
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import start_qt

results = []
def check(name, ok, info=''):
	results.append((name, bool(ok)))
	print(('PASS ' if ok else 'FAIL ') + name + ('  ' + str(info)[:300] if info != '' else ''), flush=True)

PARTNER = ('Flow Test', 1985, 3, 20, 8.0, 9.99, 53.55, 25, 'Hamburg, Germany', 1.0, 'DE', 'Europe/Berlin')

def addPerson(path, record):
	link = sqlite3.connect(path)
	link.execute('INSERT INTO event_natal (name, year, month, day, hour, geolon, geolat, altitude, location, timezone, '
		'countrycode, timezonestr) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', record)
	link.commit()
	link.close()

def main():
	exceptions = []
	def hook(t, v, tb):
		exceptions.append(''.join(traceback.format_exception(t, v, tb)))
		sys.__excepthook__(t, v, tb)
	sys.excepthook = hook
	app, run = start_qt()
	import builtins
	from PySide6.QtCore import QDate, QPoint, QPointF, Qt, QTime
	from PySide6.QtGui import QColor, QImage, QPalette, QWheelEvent
	from PySide6.QtTest import QTest
	from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QFileDialog, QInputDialog, QMessageBox
	from astrochart.constants import ASPECT_DEFAULTS, RADIUS, WHEEL_MARGIN
	from astrochart.qt import chart_types, files
	Button = QDialogButtonBox.StandardButton
	T = lambda s: builtins._(s)
	home = os.environ['HOME']

	def events():
		for i in range(3):
			QApplication.processEvents()

	def submenu(menu, title):
		for action in menu.actions():
			if action.menu() is not None and action.text() == title:
				return action.menu()
		return None

	def entries(menu):
		menu.aboutToShow.emit()
		return [(a.text(), a.isEnabled()) for a in menu.actions() if a.text()]

	def trigger(menu, text):
		menu.aboutToShow.emit()
		for action in menu.actions():
			if action.text() == text:
				action.trigger()
				events()
				return True
		return False

	def answers(save=None, open_=None):
		QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: (save, ''))
		QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (open_, ''))

	#questions answered with ok (or cancel), warnings recorded
	questions = []
	warnings = []
	def answer(ok):
		def question(parent, title, text, *args):
			questions.append(text)
			return QMessageBox.StandardButton.Ok if ok else QMessageBox.StandardButton.Cancel
		QMessageBox.question = staticmethod(question)
	QMessageBox.warning = staticmethod(lambda parent, title, text, *args: warnings.append(text))

	def people():
		return [(row['id'], row['name'], row['location']) for row in app.db.getDatabase()]

	def visibleNames(dialog):
		tree = dialog.tree
		return [tree.topLevelItem(i).text(0) for i in range(tree.topLevelItemCount()) if not tree.topLevelItem(i).isHidden()]

	def eventDialog(action, name, date, time, city):
		"""event dialog of action with name, local date, time and a city searched in the geonames database"""
		action.trigger()
		events()
		dialog = app.window.dialogs.get('event')
		dialog.name.setText(name)
		dialog.date.setDate(QDate(*date))
		dialog.time.setTime(QTime(*time))
		if city is not None:
			dialog.chooser.search(city)
		return dialog

	def flow(app):
		win = app.window
		chart = app.chart
		events()
		# ---- window: menus, wheel and lists
		bar = win.menuBar()
		titles = [a.text() for a in bar.actions()]
		check('menu bar', titles == [T('Chart'), T('Event'), T('Chart Types'), T('Tables'), T('Zoom'), T('Settings'), T('Help')], titles)
		check('wheel drawn', win.image.renderer.isValid() and win.image.pixmap is not None)
		check('lists filled', win.panels.positions.topLevelItemCount() == len(chart.bodyRows()) > 10, win.panels.positions.topLevelItemCount())
		check('status bar: chart type and place', chart.location in win.status.text(), win.status.text())
		# ---- quick open: the database entries, current whenever the menu opens
		addPerson(app.cfg.peopledb, PARTNER)
		menus = {a.text(): a.menu() for a in bar.actions()}
		quick = submenu(menus[T('Event')], T('Quick Open Database'))
		check('quick open lists new entry at once', ('Flow Test', True) in entries(quick), entries(quick))
		trigger(quick, 'Flow Test')
		check('quick open: chart of the entry', chart.name == 'Flow Test' and 'Hamburg' in chart.location, (chart.name, chart.location))
		check('quick open: title and lists', win.windowTitle().startswith('Flow Test') and win.panels.positions.topLevelItemCount() > 10, win.windowTitle())
		history = submenu(menus[T('Chart')], T('History'))
		check('history menu', entries(history) and all(text for text, enabled in entries(history)), entries(history))
		# ---- interactive wheel and lists
		win.selectBody('radix', 0)
		check('select: highlight', chart.highlight == ('radix', 0) and win.wheelData['highlight'] != '')
		item = win.panels.positionItems[('radix', 0)]
		check('select: list row marked', item.isSelected())
		check('select: aspects of the body', chart.planets[0]['label'] in win.panels.aspectsTitle.text() and not win.panels.allAspects.isHidden(), win.panels.aspectsTitle.text())
		win.selectBody('radix', 0)
		check('select again: none', chart.highlight is None and not item.isSelected())
		glyph = [g for g in chart.glyphs if g['side'] == 'radix' and g['id'] == 0][0]
		rect = win.image.drawingRect()
		extent = 2.0 * (RADIUS + WHEEL_MARGIN)
		point = QPoint(int(rect.x() + (glyph['x'] + WHEEL_MARGIN) * rect.width() / extent),
			int(rect.y() + (glyph['y'] + WHEEL_MARGIN) * rect.height() / extent))
		QTest.mouseClick(win.image.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
		events()
		check('click on the sun symbol selects it', chart.highlight == ('radix', 0), chart.highlight)
		check('tooltip of the sun', chart.planets[0]['label'] in win.image.tooltipHtml('radix', 0))
		win.panels.onPositionClicked(win.panels.positionItems[('radix', 1)], 0)
		check('click in the list selects', chart.highlight == ('radix', 1), chart.highlight)
		QTest.keyClick(win, Qt.Key.Key_Escape)
		events()
		check('escape: no selection', chart.highlight is None, chart.highlight)
		QTest.mouseClick(win.image.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(2, 2))
		check('click beside the symbols: none', chart.highlight is None)
		# ---- transit with date bar, carrying over
		win.transitAction.trigger()
		events()
		check('transit: date bar', win.transitBar.isVisible() and chart.type == 'Transit')
		groups = [win.panels.positions.topLevelItem(i).text(0) for i in range(win.panels.positions.topLevelItemCount())
			if win.panels.positions.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole) is None]
		check('transit: radix and transit lists', groups == [T('Radix'), T('Transit')], groups)
		bar_ = win.transitBar
		bar_.setTransitDate(bar_.transitDate.replace(year=2026, month=12, day=31, hour=23, minute=59))
		bar_.transitSpin['m'].setValue(60)
		events()
		check('transit: minute carries over to the next year', bar_.transitDate.year == 2027 and (bar_.transitDate.month, bar_.transitDate.day, bar_.transitDate.hour, bar_.transitDate.minute) == (1, 1, 0, 0), bar_.transitDate)
		check('transit: chart follows the date bar', '2027-01-01' in chart.charttype, chart.charttype)
		win.radixAction.trigger()
		events()
		check('radix: no date bar', not win.transitBar.isVisible() and chart.type == 'Radix')
		# ---- second event from the database
		types = menus[T('Chart Types')]
		trigger(submenu(types, T('Synastry Chart')), 'Flow Test')
		check('synastry with database entry', chart.type == 'Transit' and chart.synastry and 'Flow Test' in chart.charttype and not win.transitBar.isVisible(), chart.charttype)
		trigger(submenu(types, T('Composite Chart')), 'Flow Test')
		check('composite with database entry', 'Flow Test' in chart.charttype, chart.charttype)
		trigger(submenu(types, T('Combine Chart')), 'Flow Test')
		check('combine with database entry', 'Flow Test' in chart.charttype, chart.charttype)
		# ---- solar return, progression (input dialogs answered)
		QInputDialog.getInt = staticmethod(lambda *a, **k: (2026, True))
		win.solarAction.trigger()
		check('solar return', '2026' in chart.charttype, chart.charttype)
		chart_types.DateDialog.exec = lambda self: QDialog.DialogCode.Accepted
		win.progressionAction.trigger()
		check('progression', chart.charttype != '' and win.panels.positions.topLevelItemCount() > 10, chart.charttype)
		# ---- zoom
		win.zoomActions[1].trigger()
		win.zoomInAction.trigger()
		check('zoom in', abs(win.image.scale - 1.25) < 1e-9, win.image.scale)
		win.zoomActions[3].trigger()
		events()
		check('zoom 200%: scrolls', win.image.horizontalScrollBar().maximum() > 0 and win.image.verticalScrollBar().maximum() > 0)
		win.zoomActions[1].trigger()
		check('zoom 100%: fits', win.image.horizontalScrollBar().maximum() == 0 and win.image.verticalScrollBar().maximum() == 0)
		# ---- tables
		win.openRecord({'name': 'Flow Test', 'year': 1985, 'month': 3, 'day': 20, 'hour': 8.0, 'geolon': 9.99,
			'geolat': 53.55, 'altitude': 25, 'location': 'Hamburg, Germany', 'timezone': 1.0, 'timezonestr': 'Europe/Berlin'})
		chart_types.DateDialog.value = lambda self: __import__('datetime').datetime(2026, 10, 1)
		win.timelineAction.trigger()
		events()
		timeline = [w for w in win.tableWindows if w.windowTitle() == T('Monthly Timeline')]
		check('timeline window', len(timeline) == 1 and timeline[0].isVisible())
		pages = timeline[0].pages()
		check('timeline pages', len(pages) >= 1 and all('<svg' in page for page in pages), len(pages))
		answers(save=os.path.join(home, 'timeline.pdf'))
		timeline[0].exportPDF()
		check('timeline as PDF', open(os.path.join(home, 'timeline.pdf'), 'rb').read(4) == b'%PDF')
		win.cuspAspectsAction.trigger()
		events()
		check('cusp aspects window', len(win.tableWindows) == 2)
		win.refreshTableWindows(['radix', 'transit'])
		for window in list(win.tableWindows):
			window.close()
		events()
		check('table windows closed', not win.tableWindows)
		# ---- export of the chart page
		for kind in ('png', 'jpg', 'svg', 'pdf'):
			path = os.path.join(home, 'chart.' + kind)
			answers(save=path)
			win.files.export(kind)
			check('export ' + kind, os.path.exists(path) and os.path.getsize(path) > 1000)
		check('export png: 2400 pixels wide', QImage(os.path.join(home, 'chart.png')).width() == files.EXPORT_WIDTH)
		check('export svg: the page', open(os.path.join(home, 'chart.svg')).read() == win.chartSVG)
		# ---- print (printer writing a PDF file)
		class PdfPrinter(files.QPrinter):
			def __init__(self, *args):
				super().__init__(*args)
				self.setOutputFormat(files.QPrinter.OutputFormat.PdfFormat)
				self.setOutputFileName(os.path.join(home, 'printed.pdf'))
		files.QPrinter = PdfPrinter
		files.QPrintDialog.exec = lambda self: QDialog.DialogCode.Accepted
		win.printAction.trigger()
		check('print', open(os.path.join(home, 'printed.pdf'), 'rb').read(4) == b'%PDF')
		# ---- chart file: save and open again
		answers(save=os.path.join(home, 'chart.oac'))
		win.saveAction.trigger()
		win.openRecord({'name': 'Other', 'year': 1990, 'month': 1, 'day': 1, 'hour': 12.0, 'geolon': 13.4,
			'geolat': 52.52, 'altitude': 25, 'location': 'Berlin', 'timezone': 1.0, 'timezonestr': 'Europe/Berlin'})
		answers(open_=os.path.join(home, 'chart.oac'))
		win.openAction.trigger()
		check('chart file saved and opened', chart.name == 'Flow Test' and win.windowTitle().startswith('Flow Test'), chart.name)
		# ---- database export and import (merge)
		answers(save=os.path.join(home, 'export.sql'))
		win.exportDatabaseAction.trigger()
		check('database export', os.path.getsize(os.path.join(home, 'export.sql')) == os.path.getsize(app.cfg.peopledb))
		other = os.path.join(home, 'other.sql')
		shutil.copyfile(os.path.join(home, 'export.sql'), other)
		addPerson(other, ('Merged Person',) + PARTNER[1:])
		answers(open_=other)
		win.importDatabaseAction.trigger()
		check('database import: entry in quick open', ('Merged Person', True) in entries(quick), entries(quick))
		# ---- event dialog: new event, offline place from the geonames database
		history_before = len(app.db.history)
		d = eventDialog(win.newAction, 'Dialog Test', (1985, 3, 20), (9, 30, 0), 'Hamburg, DE')
		check('new event: dialog with city chooser', d is not None and d.chooser is not None and 'Hamburg' in d.chooser.city['loc'],
			d.chooser.city if d is not None and d.chooser is not None else None)
		check('new event: summary shows the place', 'Hamburg' in d.summary.text(), d.summary.text())
		d.button[Button.Ok].click()
		events()
		check('new event OK: chart', chart.name == 'Dialog Test' and 'Hamburg' in chart.location and chart.type == 'Radix', (chart.name, chart.location))
		check('new event OK: local date and timezone', (chart.year_loc, chart.month_loc, chart.day_loc, chart.hour_loc, chart.minute_loc) == (1985, 3, 20, 9, 30)
			and chart.timezonestr == 'Europe/Berlin' and chart.timezone == 1.0, (chart.year_loc, chart.month_loc, chart.day_loc, chart.hour_loc, chart.timezonestr, chart.timezone))
		check('new event OK: dialog closed, history entry', 'event' not in win.dialogs and len(app.db.history) >= min(history_before + 1, 10))
		check('new event OK: title and lists', win.windowTitle().startswith('Dialog Test') and win.panels.positions.topLevelItemCount() > 10)
		# ---- edit the event: apply keeps the dialog open
		d = eventDialog(win.editAction, 'Dialog Test', (1985, 3, 20), (10, 0, 0), None)
		check('edit event: fields of the chart', d.name.text() == 'Dialog Test' and 'Hamburg' in d.chooser.city['loc'])
		d.button[Button.Apply].click()
		check('edit event apply: chart changed, dialog open', chart.hour_loc == 10 and 'event' in win.dialogs)
		d.button[Button.Cancel].click()
		events()
		check('edit event cancel: closed', 'event' not in win.dialogs)
		# ---- add to the database, a name only once
		before = people()
		d = eventDialog(win.newAction, 'Dialog Test', (1985, 3, 20), (9, 30, 0), 'Hamburg, DE')
		answer(True)
		d.button[T('Add to Database')].click()
		events()
		after = people()
		check('add to database', len(after) == len(before) + 1 and after[-1][1] == 'Dialog Test' and 'Hamburg' in after[-1][2], after[-1:])
		check('add to database: asked, chart shown, closed', questions and chart.name == 'Dialog Test' and 'event' not in win.dialogs)
		check('add to database: quick open lists it', ('Dialog Test', True) in entries(quick))
		d = eventDialog(win.newAction, 'Dialog Test', (1990, 1, 1), (12, 0, 0), 'Berlin, DE')
		d.button[T('Add to Database')].click()
		check('duplicate name refused', warnings and len(people()) == len(after) and 'event' in win.dialogs, warnings)
		d.close()
		events()
		# ---- event database: filter, edit, delete, open
		win.databaseAction.trigger()
		events()
		db_dialog = win.dialogs.get('database')
		check('database window', db_dialog is not None and set(visibleNames(db_dialog)) >= {'Flow Test', 'Dialog Test', 'Merged Person'}, visibleNames(db_dialog) if db_dialog else None)
		db_dialog.filter.setText('dialog')
		check('database filter', visibleNames(db_dialog) == ['Dialog Test'] and db_dialog.selectedRecord()['name'] == 'Dialog Test', visibleNames(db_dialog))
		db_dialog.button[T('Edit')].click()
		events()
		ed = win.dialogs.get('event')
		check('edit entry: event dialog with save', ed is not None and Button.Save in ed.button and chart.name == 'Dialog Test')
		ed.chooser.search('Munich, DE')
		ed.time.setTime(QTime(11, 15, 0))
		ed.button[Button.Save].click()
		events()
		entry = [p for p in people() if p[1] == 'Dialog Test']
		check('edit entry saved', len(entry) == 1 and 'Munich' in entry[0][2] and 'event' not in win.dialogs, entry)
		check('edit entry: list and chart updated', 'Munich' in db_dialog.tree.topLevelItem(0).text(2) + ''.join(
			db_dialog.tree.topLevelItem(i).text(2) for i in range(db_dialog.tree.topLevelItemCount())) and 'Munich' in chart.location and chart.hour_loc == 11)
		db_dialog.filter.setText('merged')
		count = len(people())
		db_dialog.button[T('Delete')].click()
		check('delete entry', len(people()) == count - 1 and 'Merged Person' not in [p[1] for p in people()] and visibleNames(db_dialog) == [], visibleNames(db_dialog))
		db_dialog.filter.setText('flow')
		db_dialog.button[Button.Open].click()
		events()
		check('open entry', chart.name.startswith('Flow Test') and 'database' not in win.dialogs, chart.name)
		# ---- famous people
		win.famousAction.trigger()
		events()
		fd = win.dialogs.get('famous')
		check('famous people', fd is not None and len(visibleNames(fd)) > 1000, len(visibleNames(fd)) if fd else None)
		fd.filter.setText('einstein')
		fd.tree.itemActivated.emit(fd.tree.currentItem(), 0)
		events()
		check('famous person opened', 'Einstein' in chart.name and 'famous' not in win.dialogs, chart.name)
		# ---- home location
		win.locationAction.trigger()
		events()
		ld = win.dialogs.get('location')
		ld.chooser.search('Berlin, DE')
		ld.button[Button.Ok].click()
		events()
		check('home location saved', 'Berlin' in app.db.astrocfg['home_location'] and 'Berlin' in chart.home_location
			and chart.home_timezonestr == 'Europe/Berlin' and 'location' not in win.dialogs, app.db.astrocfg['home_location'])
		check('home location: chart here and now', chart.name == T('Here and Now') and 'Berlin' in chart.location)
		d = eventDialog(win.newAction, 'Other', (2000, 1, 1), (0, 0, 0), None)
		check('new event starts at home', 'Berlin' in d.chooser.city['loc'], d.chooser.city['loc'])
		d.close()
		events()
		# ---- configuration: classic wheel, back to the modern one
		check('modern wheel by default', win.wheelData.get('style') == 'modern')
		win.configurationAction.trigger()
		events()
		cd = win.dialogs.get('configuration')
		cd.chartview.setCurrentIndex(cd.chartview.findData('traditional'))
		cd.button[Button.Ok].click()
		events()
		check('classic wheel chosen', app.db.astrocfg['chartstyle'] == 'classic' and app.db.astrocfg['chartview'] == 'traditional'
			and win.wheelData.get('style') != 'modern', (app.db.astrocfg.get('chartstyle'), app.db.astrocfg.get('chartview')))
		win.configurationAction.trigger()
		events()
		cd = win.dialogs.get('configuration')
		check('configuration shows the classic view', cd.chartview.currentData() == 'traditional')
		check('sidereal mode only for the sidereal zodiac', not cd.siderealmode.isEnabled())
		cd.zodiactype.setCurrentIndex(cd.zodiactype.findData('sidereal'))
		check('sidereal mode enabled', cd.siderealmode.isEnabled())
		cd.zodiactype.setCurrentIndex(cd.zodiactype.findData('tropical'))
		cd.chartview.setCurrentIndex(cd.chartview.findData('modern'))
		cd.fontSize.setValue(14)
		#a new language is asked for (answered with cancel: no restart)
		cd.language.setCurrentIndex(cd.language.findData('en'))
		answer(False)
		questions.clear()
		cd.button[Button.Ok].click()
		events()
		check('modern wheel again', app.db.astrocfg['chartstyle'] == 'modern' and win.wheelData.get('style') == 'modern')
		check('language asked, kept when cancelled', len(questions) == 1 and app.db.astrocfg['language'] == 'default', questions)
		# ---- font size of the lists: configuration and ctrl + mouse wheel
		check('list font size saved', win.panels.fontSize == 14 and app.db.astrocfg.get('listfontsize') == '14'
			and win.panels.positions.font().pointSizeF() == 14, (win.panels.fontSize, app.db.astrocfg.get('listfontsize')))
		check('list symbols grow with the font', win.panels.positions.iconSize().width() > 20, win.panels.positions.iconSize())
		viewport = win.panels.positions.viewport()
		wheel = QWheelEvent(QPointF(10, 10), QPointF(viewport.mapToGlobal(QPoint(10, 10))), QPoint(0, 0), QPoint(0, 120),
			Qt.MouseButton.NoButton, Qt.KeyboardModifier.ControlModifier, Qt.ScrollPhase.NoScrollPhase, False)
		QApplication.sendEvent(viewport, wheel)
		check('ctrl + mouse wheel: larger list font', win.panels.fontSize == 15 and app.db.astrocfg.get('listfontsize') == '15', win.panels.fontSize)
		# ---- aspect settings
		win.radixAction.trigger()
		win.aspectsAction.trigger()
		events()
		ad = win.dialogs.get('aspects')
		check('aspect settings: page of the chart', ad is not None and ad.tabs.currentIndex() == 0)
		ad.data['radix'][0]['orb'].setValue(7.5)
		ad.button[Button.Apply].click()
		check('orb saved with apply', app.db.getSettingsAspect('radix')[0]['orb'] == 7.5 and 'aspects' in win.dialogs, app.db.getSettingsAspect('radix')[0]['orb'])
		ad.button[Button.RestoreDefaults].click()
		check('default orb restored in the dialog', ad.data['radix'][0]['orb'].value() == ASPECT_DEFAULTS['radix']['orb'][0])
		ad.button[Button.Ok].click()
		events()
		check('default orb saved, closed', app.db.getSettingsAspect('radix')[0]['orb'] == ASPECT_DEFAULTS['radix']['orb'][0] and 'aspects' not in win.dialogs)
		# ---- planet settings
		win.planetsAction.trigger()
		events()
		pd = win.dialogs.get('planets')
		state = app.db.getSettingsPlanet('radix')[0]['visible']
		pd.data['radix'][0]['visible'].setChecked(not state)
		pd.button[Button.Ok].click()
		events()
		check('planet setting saved', app.db.getSettingsPlanet('radix')[0]['visible'] == int(not state) and 'planets' not in win.dialogs)
		check('hidden sun not listed', ('radix', 0) not in win.panels.positionItems if state else ('radix', 0) in win.panels.positionItems)
		win.planetsAction.trigger()
		events()
		pd = win.dialogs.get('planets')
		pd.button[Button.RestoreDefaults].click()
		pd.button[Button.Ok].click()
		events()
		check('planet defaults', app.db.getSettingsPlanet('radix')[0]['visible'] == 1 and ('radix', 0) in win.panels.positionItems)
		# ---- light and dark colours follow the palette
		dark = QPalette(QColor('#202326'))
		QApplication.setPalette(dark)
		events()
		check('dark palette: dark wheel', chart.dark and '#e4e4e7' in win.chart.makeWheelSVG(win.wheelData))
		light = QPalette(QColor('#eff0f1'))
		QApplication.setPalette(light)
		events()
		check('light palette: light wheel', not chart.dark)
		# ---- about
		QMessageBox.exec = lambda self: 0
		win.aboutAction.trigger()
		check('about', True)
		check('no exceptions', not exceptions, '\n'.join(exceptions)[-2000:])
		failed = [name for name, ok in results if not ok]
		print('qt flows: %d checks, %d failed' % (len(results), len(failed)), flush=True)
		if failed:
			raise AssertionError('failed: %s' % ', '.join(failed))

	return run(flow)

if __name__ == '__main__':
	sys.exit(main())

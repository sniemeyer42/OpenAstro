#!/usr/bin/env python3
"""Regression flows for replacing a transit's radix and both solar views."""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import start_qt

BASE = {'name': 'First Radix', 'year': 1980, 'month': 6, 'day': 15, 'hour': 11.0,
	'geolon': 13.4, 'geolat': 52.52, 'altitude': 25, 'location': 'Berlin, Germany',
	'timezone': 2.0, 'timezonestr': 'Europe/Berlin', 'countrycode': 'DE'}
OTHER = dict(BASE, name='Second Radix', year=1985, month=11, day=20, hour=8.0,
	geolon=9.99, geolat=53.55, location='Hamburg, Germany', timezone=1.0)


def main():
	app, run = start_qt()
	from PySide6.QtCore import QTime, Qt
	from PySide6.QtGui import QColor, QImage, QPalette
	from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QPushButton
	from astrochart.events import insertEvent
	from astrochart.qt import chart_types, files

	def events():
		for i in range(3):
			QApplication.processEvents()

	def flow(app):
		win, chart = app.window, app.chart
		home = os.environ['HOME']
		win.openRecord(BASE)
		insertEvent(app.db, chart)
		app.db.addHistory(chart)
		win.openRecord(OTHER)
		insertEvent(app.db, chart)
		app.db.addHistory(chart)
		oac = os.path.join(home, 'second.oac')
		chart.exportOAC(oac)
		win.openRecord(BASE)

		def baseKey():
			return tuple(getattr(chart, name) for name in
				('name', 'year', 'month', 'day', 'hour', 'geolon', 'geolat', 'altitude', 'location', 'timezone'))

		def transitKey():
			return (chart.t_year, chart.t_month, chart.t_day, chart.t_hour)

		def solarKey():
			return (chart.s_year, chart.s_month, chart.s_day, chart.s_hour)

		def transitUnchanged():
			events()
			assert chart.type == 'Transit' and not chart.synastry and not chart.solar_return
			assert win.transitBar.isVisible() and win.transitBar.moment == moment
			assert transitKey() == transit_time

		def menu(title):
			return next(a.menu() for a in win.menuBar().actions() if a.text() == _(title))

		def submenu(parent, title):
			return next(a.menu() for a in parent.actions() if a.text() == _(title))

		def openMenu(parent, name):
			parent.aboutToShow.emit()
			next(a for a in parent.actions() if a.text() == name).trigger()
			events()

		win.transitAction.trigger()
		events()
		bar = win.transitBar
		# An ambiguous local clock time retains its chosen UTC instant and seconds.
		moment = bar.zoneInfo.localize(datetime.datetime(2026, 10, 25, 2, 30, 17), is_dst=False)
		bar.setMoment(moment)
		events()
		transit_time = transitKey()
		old_inner = list(chart.planets_degree_ut)
		outer = list(chart.t_planets_degree_ut)
		win.openRecord(OTHER)
		transitUnchanged()
		assert chart.name == OTHER['name'] and chart.planets_degree_ut != old_inner
		assert chart.t_planets_degree_ut == outer
		openMenu(submenu(menu('Event'), 'Quick Open Database'), BASE['name'])
		transitUnchanged()
		assert chart.name == BASE['name']
		openMenu(submenu(menu('Chart'), 'History'), OTHER['name'])
		transitUnchanged()
		assert chart.name == OTHER['name']

		win.databaseAction.trigger()
		events()
		dialog = win.dialogs['database']
		dialog.filter.setText(BASE['name'])
		dialog.openSelected()
		transitUnchanged()
		assert chart.name == BASE['name']
		win.famousAction.trigger()
		events()
		dialog = win.dialogs['famous']
		dialog.filter.setText('einstein')
		dialog.openSelected()
		transitUnchanged()
		assert 'Einstein' in chart.name

		QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (oac, ''))
		win.openAction.trigger()
		transitUnchanged()
		assert chart.name == OTHER['name']
		win.files.importAstrolog(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'charts', 'WP.dat'))
		transitUnchanged()
		assert chart.name != OTHER['name']

		win.editAction.trigger()
		events()
		dialog = win.dialogs['event']
		dialog.time.setTime(QTime(12, 34, 56))
		assert dialog.apply()
		transitUnchanged()
		assert (chart.hour_loc, chart.minute_loc, chart.second_loc) == (12, 34, 56)
		dialog.close()
		win.radixAction.trigger()
		win.transitAction.trigger()
		transitUnchanged()
		win.setSecondEvent('Synastry', OTHER)
		assert chart.synastry and not bar.isVisible()
		win.transitAction.trigger()
		transitUnchanged()
		print('transit: opening routes, edit, UTC instant and session memory passed', flush=True)

		# A new event starts a radix, while the transit moment remains remembered.
		win.newAction.trigger()
		events()
		dialog = win.dialogs['event']
		assert dialog.apply()
		assert chart.type == 'Radix' and not chart.solar_return
		dialog.close()
		win.openRecord(BASE)
		base = baseKey()
		inner = list(chart.planets_degree_ut)
		dialog = chart_types.SolarReturnDialog(win)
		assert dialog.value() == (datetime.datetime.now().year, False)
		dialog.close()

		def answerSolar(year, overlay, accepted=True):
			def answer(dialog):
				dialog.year.setValue(year)
				dialog.view.setCurrentIndex(int(overlay))
				return QDialog.DialogCode.Accepted if accepted else QDialog.DialogCode.Rejected
			chart_types.SolarReturnDialog.exec = answer

		answerSolar(2026, False)
		win.solarAction.trigger()
		events()
		assert chart.type == 'Solar' and not chart.solar_return
		assert chart.solar_year == 2026 and baseKey() == base
		solar_time = solarKey()
		solar_positions = list(chart.planets_degree_ut)
		answerSolar(2026, True)
		win.solarAction.trigger()
		events()
		assert chart.type == 'Transit' and chart.solar_return and not chart.synastry
		assert transitKey() == solar_time and chart.t_planets_degree_ut == solar_positions
		assert baseKey() == base and chart.planets_degree_ut == inner
		assert chart.degreeDiff(chart.planets_degree_ut[0], chart.t_planets_degree_ut[0]) < 0.001
		assert not bar.isVisible() and chart.aspectset == 'transit'
		assert win.image.renderer.isValid() and chart.aspectRows()
		groups = [win.panels.positions.topLevelItem(i).text(0) for i in range(win.panels.positions.topLevelItemCount())
			if win.panels.positions.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole) is None]
		assert groups == [_('Radix'), _('Solar Return')]
		assert _('Solar Return') in win.chartSVG and 'UTC' in win.status.text()
		dialog = chart_types.SolarReturnDialog(win)
		assert dialog.value() == (2026, True)
		dialog.close()
		unchanged = (baseKey(), transitKey(), win.chartSVG)
		answerSolar(2030, False, accepted=False)
		win.solarAction.trigger()
		events()
		assert (baseKey(), transitKey(), win.chartSVG) == unchanged and chart.solar_return
		win.selectBody('transit', 0)
		assert chart.highlight == ('transit', 0) and win.panels.positionItems[('transit', 0)].isSelected()
		assert chart.planets[0]['label'] in win.image.tooltipHtml('transit', 0)
		win.clearSelection()

		for style in ('classic', 'modern'):
			app.db.astrocfg['chartstyle'] = style
			win.refreshChart()
			assert win.image.renderer.isValid() and chart.solar_return
		QApplication.setPalette(QPalette(QColor('#202326')))
		events()
		assert chart.dark and win.image.renderer.isValid() and chart.solar_return
		for kind in ('svg', 'pdf', 'png', 'jpg'):
			path = os.path.join(home, 'solar.' + kind)
			QFileDialog.getSaveFileName = staticmethod(lambda *a, path=path, **k: (path, ''))
			win.files.export(kind)
			assert os.path.getsize(path) > 1000
		assert QImage(os.path.join(home, 'solar.png')).width() == files.EXPORT_WIDTH
		with open(os.path.join(home, 'solar.svg')) as exported:
			assert exported.read() == win.chartSVG
		with open(os.path.join(home, 'solar.pdf'), 'rb') as exported:
			assert exported.read(4) == b'%PDF'

		# Replacing a solar's radix keeps its year, but computes a new return.
		win.openRecord(OTHER)
		events()
		assert chart.solar_return and chart.solar_year == 2026 and chart.name == OTHER['name']
		assert transitKey() != solar_time and not bar.isVisible()
		assert chart.degreeDiff(chart.planets_degree_ut[0], chart.t_planets_degree_ut[0]) < 0.001
		win.transitAction.trigger()
		transitUnchanged()
		assert chart.secondSideLabel() == _('Transit')
		win.radixAction.trigger()
		win.openRecord(BASE)
		chart.setComposite(OTHER)
		win.updateChart()
		# A previous calculation of a different chart must not supply the solar's target sun.
		chart.localToSolar(2026, overlay=True)
		win.updateChart()
		assert transitKey() == solar_time and chart.t_planets_degree_ut == solar_positions
		chart.localToSolar(2027)
		win.updateChart()
		chart.localToSolar(2026)
		win.updateChart()
		assert solarKey() == solar_time and chart.planets_degree_ut == solar_positions
		assert not chart.solar_return and chart.type == 'Solar'
		win.radixAction.trigger()
		assert chart.type == 'Radix' and not chart.solar_return and baseKey() == base
		win.transitAction.trigger()
		transitUnchanged()
		button = next(button for button in bar.findChildren(QPushButton) if button.text() == _('Here and Now'))
		button.click()
		events()
		assert abs((bar.moment - datetime.datetime.now(datetime.timezone.utc)).total_seconds()) < 120
		assert transitKey() != transit_time
		print('solar: both views, dialogs, radix changes, rendering and export passed', flush=True)
		print('transit and solar flows passed', flush=True)

	return run(flow)


if __name__ == '__main__':
	sys.exit(main())

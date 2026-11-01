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
Menu 'Chart' (open, save, import, export, print) and database export/import;
printing and PDF export of SVG pages
"""

import pytz
from shutil import copyfile
from PySide6.QtCore import QMarginsF, QRectF
from PySide6.QtGui import QPageLayout, QPageSize, QPainter, QPdfWriter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import QDialog, QFileDialog, QInputDialog, QMessageBox
from astrochart.qt.svg_view import documentSize, renderImage, svgRenderer

#width in pixels of exported PNG and JPG images (about 300 dpi on A4)
EXPORT_WIDTH = 2400

def fileFilter(name, *patterns):
	return '%s (%s)' % (name, ' '.join(patterns))

ALL_FILES = fileFilter('ALL', '*')

def paintPages(device, pages):
	"""paint pages (SVG documents) on the pages of a printer or PDF writer"""
	painter = QPainter()
	if not painter.begin(device):
		return False
	for number, svg in enumerate(pages):
		if number:
			device.newPage()
		renderer = svgRenderer(svg)
		target = QRectF(painter.viewport())
		#keep the aspect ratio of the page
		width, height = documentSize(renderer)
		factor = min(target.width() / width, target.height() / height)
		target = QRectF(target.x(), target.y(), width * factor, height * factor)
		renderer.render(painter, target)
	painter.end()
	return True

def pageLayout(landscape):
	orientation = QPageLayout.Orientation.Landscape if landscape else QPageLayout.Orientation.Portrait
	return QPageLayout(QPageSize(QPageSize.PageSizeId.A4), orientation, QMarginsF(0, 0, 0, 0))

def writePDF(path, pages, landscape):
	"""PDF file of the pages (SVG documents), A4"""
	writer = QPdfWriter(path)
	writer.setResolution(300)
	writer.setPageLayout(pageLayout(landscape))
	writer.setCreator('OpenAstro.org')
	return paintPages(writer, pages)

def printPages(parent, pages, landscape):
	"""print dialog, then the pages (SVG documents, a function returning them)"""
	printer = QPrinter(QPrinter.PrinterMode.HighResolution)
	printer.setPageLayout(pageLayout(landscape))
	dialog = QPrintDialog(printer, parent)
	if dialog.exec() != QDialog.DialogCode.Accepted:
		return
	if not paintPages(printer, pages()):
		QMessageBox.warning(parent, _('Print'), _("Error printing"))

def saveFileName(parent, name, *filters):
	path, selected = QFileDialog.getSaveFileName(parent, _('Select file for saving'), name, ';;'.join(filters + (ALL_FILES,)))
	return path

def openFileName(parent, title, *filters):
	path, selected = QFileDialog.getOpenFileName(parent, title, '', ';;'.join(filters + (ALL_FILES,)))
	return path

class ChartFiles:
	"""file dialogs, import, export and printing of the main window"""

	def __init__(self, window):
		self.window = window
		self.chart = window.chart
		self.cfg = window.cfg
		self.db = window.db

	def openChart(self):
		path = openFileName(self.window, _('Open'), fileFilter('OAC', '*.oac'), fileFilter('TXT', '*.txt'))
		if path:
			self.chart.importOAC(path)
			self.window.updateChart()

	def saveChart(self):
		path = saveFileName(self.window, 'AstroChart.oac', fileFilter('OAC', '*.oac'), fileFilter('TXT', '*.txt'))
		if path:
			self.chart.exportOAC(path)

	def importChart(self, kind):
		"""import a chart of another program: kind Oroboros, Astrolog, Skylendar, Zet8"""
		filters = {'Oroboros': fileFilter('XML', '*.xml'), 'Astrolog': fileFilter('DAT', '*.dat'),
			'Skylendar': fileFilter('SKIF', '*.skif'), 'Zet8': fileFilter('ZBS', '*.zbs')}
		path = openFileName(self.window, _('Select file to import'), filters[kind])
		if not path:
			return
		if kind == 'Astrolog':
			self.importAstrolog(path)
			return
		{'Oroboros': self.chart.importOroboros, 'Skylendar': self.chart.importSkylendar, 'Zet8': self.chart.importZet8}[kind](path)
		self.window.updateChart()

	def importAstrolog(self, path):
		#with daylight saving time the user confirms the timezone
		record, timezone_str = self.chart.readAstrolog(path)
		if record['daylight']:
			zones = sorted(pytz.common_timezones)
			current = zones.index(timezone_str) if timezone_str in zones else 0
			timezone_str, ok = QInputDialog.getItem(self.window, _("Change Timezone ?"), _("Actual Timezone:"), zones, current, False)
			if not ok:
				return
		self.chart.setAstrolog(record, timezone_str)
		self.window.updateChart()

	def chartImage(self):
		"""the printed page of the chart on white, EXPORT_WIDTH pixels wide"""
		renderer = svgRenderer(self.window.chartSVG)
		width, height = documentSize(renderer)
		return renderImage(renderer, EXPORT_WIDTH, EXPORT_WIDTH * height / width, background='#ffffff')

	def export(self, kind):
		"""export the printed page of the chart: kind png, jpg, svg or pdf"""
		filters = {'png': fileFilter('PNG', '*.png'), 'jpg': fileFilter('JPG', '*.jpg', '*.jpeg'),
			'svg': fileFilter('SVG', '*.svg'), 'pdf': fileFilter('PDF', '*.pdf')}
		path = saveFileName(self.window, 'AstroData.%s' % kind, filters[kind])
		if not path:
			return
		if kind == 'png':
			self.chartImage().save(path, 'PNG')
		elif kind == 'jpg':
			self.chartImage().save(path, 'JPG', 92)
		elif kind == 'svg':
			with open(path, 'w') as f:
				f.write(self.window.chartSVG)
		elif kind == 'pdf':
			writePDF(path, [self.window.chartSVG], landscape=True)

	def printChart(self):
		printPages(self.window, lambda: [self.window.chartSVG], landscape=True)

	def exportDatabase(self):
		path = saveFileName(self.window, 'openastro-database.sql', fileFilter('SQL', '*.sql'))
		if path:
			copyfile(self.cfg.peopledb, path)

	def importDatabase(self):
		path = openFileName(self.window, _('Select file to import'), fileFilter('SQL', '*.sql'))
		if path:
			#the menus of the database entries fill themselves when they open
			self.db.databaseMerge(self.cfg.peopledb, path)

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
Menu 'Tables': monthly timeline and cusp aspects windows
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import QMainWindow, QToolBar
from astrochart.qt.files import fileFilter, printPages, saveFileName, writePDF
from astrochart.qt.svg_view import SvgView

class TableWindow(QMainWindow):
	"""
	window with a table of the chart (SVG pages), print and PDF export;
	settings is the chart type of the settings it uses ('radix', 'transit'),
	open table windows are redrawn when these settings change
	"""

	settings = 'radix'

	def __init__(self, window, title, size, pdfname):
		super().__init__(window)
		self.setWindowFlag(Qt.WindowType.Window)
		self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
		self.window = window
		self.chart = window.chart
		self.pdfname = pdfname
		self.setWindowTitle(title)
		self.resize(*size)
		#print and PDF export in the tool bar
		toolbar = QToolBar()
		toolbar.setMovable(False)
		toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
		action = toolbar.addAction(QIcon.fromTheme('document-print'), _('Print'), self.printTable)
		action.setShortcut(QKeySequence.StandardKey.Print)
		toolbar.addAction(QIcon.fromTheme('application-pdf'), _('Save as PDF'), self.exportPDF)
		self.addToolBar(toolbar)
		#pages fitted to the window width, scrolling down
		self.image = SvgView(self.render(), fit='width')
		self.setCentralWidget(self.image)
		#the main window redraws the open table windows
		window.tableWindows.add(self)

	def closeEvent(self, event):
		self.window.tableWindows.discard(self)
		super().closeEvent(event)

	def render(self, printing=None):
		"""SVG document of the table, sets self.chart.pages"""
		raise NotImplementedError

	def refresh(self):
		self.image.replaceSVG(self.render())

	def pages(self):
		"""the pages of the table, one SVG document each"""
		self.render()
		return [self.render({'pagenum': number, 'width': 210, 'height': 297}) for number in range(self.chart.pages)]

	def printTable(self):
		printPages(self, self.pages, landscape=False)

	def exportPDF(self):
		path = saveFileName(self, self.pdfname, fileFilter('PDF', '*.pdf'))
		if path:
			writePDF(path, self.pages(), landscape=False)

class TimelineWindow(TableWindow):
	"""transits of a month, uses the transit settings"""

	settings = 'transit'

	def __init__(self, window, year, month):
		self.year = year
		self.month = month
		super().__init__(window, _("Monthly Timeline"), (1024, 760), "Timeline-%s.pdf" % (window.chart.name))

	def render(self, printing=None):
		return self.chart.makeTimelineSVG(printing=printing, y=self.year, m=self.month)

class CuspAspectsWindow(TableWindow):
	"""aspects of the planets to the house cusps, uses the radix settings"""

	def __init__(self, window):
		super().__init__(window, _("Cusp Aspects"), (900, 760), "CuspAspects-%s.pdf" % (window.chart.name))

	def render(self, printing=None):
		return self.chart.makeCuspAspectsSVG(printing=printing)

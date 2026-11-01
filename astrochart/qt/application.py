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
Application: configuration, databases, the chart shown and the main window
"""

import sys
from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from astrochart.chart.chart import Chart
from astrochart.config import OpenAstroCfg
from astrochart.constants import VERSION
from astrochart.database import OpenAstroSqlite

class AstroApplication(QApplication):

	def __init__(self, argv):
		super().__init__(argv)
		self.setApplicationName('OpenAstro.org')
		self.setApplicationDisplayName('OpenAstro')
		self.setOrganizationDomain('openastro.org')
		self.setApplicationVersion(VERSION)
		self.setDesktopFileName('astrochart')
		#configuration, databases (installs the translation of the program)
		self.cfg = OpenAstroCfg()
		self.db = OpenAstroSqlite(self.cfg)
		#chart shown in the window: event data, chart type, settings, positions
		self.chart = Chart(self.cfg, self.db)
		self.setWindowIcon(QIcon(self.cfg.iconWindow))
		self.installQtTranslation()
		self.window = None

	def installQtTranslation(self):
		"""texts of the Qt dialogs (buttons, file and print dialogs) in the language of the program"""
		language = self.db.astrocfg.get('language', 'default')
		locale = QLocale.system() if language in (None, '', 'default') else QLocale(language)
		self.qtTranslator = QTranslator(self)
		if self.qtTranslator.load(locale, 'qtbase', '_', QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
			self.installTranslator(self.qtTranslator)

	def run(self):
		from astrochart.qt.window import MainWindow
		self.window = MainWindow(self)
		self.window.show()
		return self.exec()

def main(argv=None):
	"""start the program, returns the exit status"""
	app = AstroApplication(sys.argv if argv is None else argv)
	return app.run()

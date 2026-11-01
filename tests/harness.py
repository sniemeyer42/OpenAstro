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
Common start of the test programs: the program runs with --local from the
repository, HOME must point to a scratch directory (the program writes
~/.openastro.org). The chart alone and the Qt program (offscreen) need no
display; the GTK program needs one (Xvfb works, see tests/README.md).
"""
import os
import sys
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def prepare():
	"""scratch HOME, the repository as data directory (--local), its ephemeris files"""
	if not os.environ.get('HOME', '').startswith(('/tmp', '/var/tmp')) and not os.environ.get('OPENASTRO_TEST_HOME_OK'):
		sys.exit('refusing to run with the real HOME, set HOME to a scratch directory')
	sys.path.insert(0, REPO)
	os.chdir(REPO)
	sys.argv = [os.path.join(REPO, 'astroChart.py'), '--local']
	from openastromod import swiss
	# the swiss ephemeris drops too long paths silently, use the repository files
	#(OPENASTRO_EPHE: ephemeris files of another directory, e.g. for copies in long paths)
	swiss.ephe_path = os.environ.get('OPENASTRO_EPHE', os.path.join(REPO, 'swisseph'))

def create_chart():
	"""configuration, databases and the chart, without user interface"""
	prepare()
	#month and day names of the tables in the language of the environment, as in the program
	import locale
	locale.setlocale(locale.LC_ALL, '')
	from astrochart.chart.chart import Chart
	from astrochart.config import OpenAstroCfg
	from astrochart.database import OpenAstroSqlite
	cfg = OpenAstroCfg()
	return Chart(cfg, OpenAstroSqlite(cfg))

def start_qt(steps_after_ms=300):
	"""
	Qt application with its main window (offscreen unless QT_QPA_PLATFORM is
	set), returns (app, run) where run(step) calls step(app) once the event
	loop runs and returns the exit status (1 if step raised)
	"""
	os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
	prepare()
	from PySide6.QtCore import QTimer
	from astrochart.qt.application import AstroApplication
	from astrochart.qt.window import MainWindow
	app = AstroApplication(sys.argv)
	app.window = MainWindow(app)
	app.window.show()

	def run(step):
		def wrapper():
			try:
				step(app)
			except Exception:
				traceback.print_exc()
				app.exit(1)
				return
			app.exit(0)
		QTimer.singleShot(steps_after_ms, wrapper)
		return app.exec()
	return app, run

def start_application(steps_after_ms=1500):
	"""
	GTK program (its dialogs are not yet ported to Qt): import and create the
	application, returns (app, run) where run(step) calls step(app) once the
	main loop runs and quits afterwards
	"""
	prepare()
	import gi
	gi.require_version('Gtk', '4.0')
	from gi.repository import GLib, Gio
	from astrochart.application import AstroApplication
	app = AstroApplication()
	app.set_flags(app.get_flags() | Gio.ApplicationFlags.NON_UNIQUE)

	def run(step):
		def wrapper():
			try:
				step(app)
			except Exception:
				traceback.print_exc()
				app.exit_code = 1
				app.quit()
			return False
		app.exit_code = 0
		GLib.timeout_add(steps_after_ms, wrapper)
		app.run([sys.argv[0], '--local'])
		return app.exit_code
	return app, run

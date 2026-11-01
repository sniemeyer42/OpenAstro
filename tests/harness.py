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
Common start of the test programs: the application runs with --local from
the repository, HOME must point to a scratch directory (the program writes
~/.openastro.org), a display is needed (Xvfb works, see tests/README.md).
"""
import os
import sys
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def start_application(steps_after_ms=1500):
	"""
	import and create the application, returns (app, run) where run(step)
	calls step(app) once the main loop runs and quits afterwards
	"""
	if not os.environ.get('HOME', '').startswith(('/tmp', '/var/tmp')) and not os.environ.get('OPENASTRO_TEST_HOME_OK'):
		sys.exit('refusing to run with the real HOME, set HOME to a scratch directory')
	sys.path.insert(0, REPO)
	os.chdir(REPO)
	sys.argv = [os.path.join(REPO, 'astroChart.py'), '--local']
	import gi
	gi.require_version('Gtk', '4.0')
	from gi.repository import GLib, Gio
	from astrochart.application import AstroApplication
	from openastromod import swiss
	# the swiss ephemeris drops too long paths silently, use the repository files
	swiss.ephe_path = os.path.join(REPO, 'swisseph')
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

#!/usr/bin/env python3
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
Start the OpenAstro Gtk4 program: ./astroChart.py [--local] [--purge] [--debug]
"""
import sys

from astrochart.application import AstroApplication

if __name__ == "__main__":
	app = AstroApplication()
	exit_status = app.run(sys.argv)
	sys.exit(exit_status)

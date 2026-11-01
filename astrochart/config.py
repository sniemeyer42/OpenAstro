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
Configuration (paths of data and user files)
"""

import os
from astrochart.constants import LOCAL, VERSION
from astrochart.paths import DATADIR
from astrochart.util import dprint

""" OpenAstro configuration class """
class OpenAstroCfg:
	def __init__(self):
		self.version = VERSION
		dprint("-------------------------------")
		dprint('  OpenAstro.org '+str(self.version))
		dprint("-------------------------------")
		self.homedir = os.path.expanduser("~")
		# printing variables
		self.pages = 1
		self.pagesY = 0
		#check for astrodir
		self.astrodir = os.path.join(self.homedir, '.openastro.org')
		if os.path.isdir(self.astrodir) == False:
			os.mkdir(self.astrodir)
		#check for tmpdir
		self.tmpdir = os.path.join(self.astrodir, 'tmp')
		if os.path.isdir(self.tmpdir) == False:
			os.mkdir(self.tmpdir)
		#check for swiss local dir
		self.swissLocalDir = os.path.join(self.astrodir, 'swiss_ephemeris')
		if os.path.isdir(self.swissLocalDir) == False:
			os.mkdir(self.swissLocalDir)
		#geonames database
		if LOCAL:
			self.geonamesdb = os.path.join(DATADIR, 'data', 'geonames.sql' )
		else:
			self.geonamesdb = os.path.join(DATADIR, 'geonames.sql' )
		#icons
		icons = os.path.join(DATADIR,'icons')
		self.iconWindow = os.path.join(icons, 'openastro.svg')
		self.iconAspects = os.path.join(icons, 'aspects')
		#basic files
		self.about = os.path.join(DATADIR, 'about.xpm')
		self.comments = os.path.join(DATADIR, 'COMMENTS')
		self.license = os.path.join(DATADIR, 'LICENSE')
		self.tempfilename = os.path.join(self.tmpdir,"openAstroChart.svg")
		self.xml_svg_wheel = os.path.join(DATADIR, 'openastro-svg-wheel.xml')
		self.xml_svg_symbols = os.path.join(DATADIR, 'openastro-svg-symbols.xml')
		self.xml_svg_table = os.path.join(DATADIR, 'openastro-svg-table.xml')
		#sqlite databases		
		self.astrodb = os.path.join(self.astrodir, 'astrodb.sql')
		self.peopledb = os.path.join(self.astrodir, 'peopledb.sql')
		if LOCAL:
			self.famousdb = os.path.join(DATADIR, 'data', 'famous.sql' )
		else:
			self.famousdb = os.path.join(DATADIR, 'famous.sql' )
		return

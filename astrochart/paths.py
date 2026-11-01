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
Data directory of the program (repository with --local)
"""

import sys
import os
from astrochart.constants import LOCAL
from astrochart.util import dprint

#directories
if LOCAL:
	DATADIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
elif os.path.exists(os.path.join(sys.prefix,'share','openastro.org')):
	DATADIR=os.path.join(sys.prefix,'share','openastro.org')
elif os.path.exists(os.path.join('usr','local','share','openastro.org')):
	DATADIR=os.path.join('usr','local','share','openastro.org')
elif os.path.exists(os.path.join('usr','share','openastro.org')):
	DATADIR=os.path.join('usr','share','openastro.org')
else:
	dprint("Exiting... can't find data directory")
	sys.exit()

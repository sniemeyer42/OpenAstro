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
Small helper functions
"""

import math
import sys
from astrochart.constants import DEBUG

def dprint(str):
	""" debug print function """
	if "--debug" in sys.argv or DEBUG:
		print('%s' % str)

def aspectOrb(value, default):
	""" orb from database (text, number, None, decimal comma) as float """
	try:
		orb = float(str(value).replace(',','.'))
	except (TypeError, ValueError):
		return float(default)
	if math.isfinite(orb) and orb >= 0:
		return orb
	return float(default)

def aspectFlag(value, default):
	""" visibility flag from database as 0 or 1 """
	try:
		return 1 if int(value) else 0
	except (TypeError, ValueError):
		return default

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
Constants and default settings
"""

import math
import sys

DEBUG = False
#for debugging set to True
LOCAL = False
if "--local" in sys.argv:
	LOCAL = True
#radius of zodiac
RADIUS = 240
OFFSET = 64
RATIO = math.sqrt(2)
VERSION = "1.1.111"

APPLICATION_ID = "org.openastro.AstroApp"
#maximal number of items of history
LIMIT=10
#years of transit date bar, the included swiss ephemeris files
#cover 1200-2400 AD, a margin of one year is left for timezones
TRANSIT_YEAR_MIN = 1201
TRANSIT_YEAR_MAX = 2398
#aspects, always all of them in this order (template symbols orb<degree>)
ASPECT_DEGREES = [ 0 , 30 , 45 , 60 , 72 , 90 , 120 , 135 , 144 , 150 , 180 ]
ASPECT_IS_MAJOR = [ 1 , 0 , 0 , 1 , 0 , 1 , 1 , 0 , 0 , 0 , 1 ]
ASPECT_IS_MINOR = [ 0 , 1 , 1 , 0 , 1 , 0 , 0 , 1 , 1 , 0 , 0 ]
ASPECT_COLORS = [ '#5757e2' , '#810757' , '#b14e58' , '#d59e28' , '#1f99b3' , '#dc0000' , '#36d100' , '#985a10' , '#7a9810' , '#fff600' , '#510060' ]
#aspect sets, order of the pages in the aspect settings
ASPECT_CHART_TYPES = ( 'radix' , 'transit' , 'synastry' )
#upper limit of the orb in the aspect settings
ASPECT_ORB_MAX = 15.0
#default aspect settings, radix is stored in settings_aspect (shared with
#the Gtk3 programs), transit and synastry in settings_aspect_chart
ASPECT_DEFAULTS = {
	'radix': {
		'visible':      [ 1 , 0 , 0 , 1 , 1 , 1 , 1 , 0 , 1 , 1 , 1 ],
		'visible_grid': [ 1 , 0 , 0 , 1 , 1 , 1 , 1 , 0 , 1 , 1 , 1 ],
		'orb':          [ 10 , 3 , 3 , 6 , 2 , 8 , 8 , 3 , 2 , 3 , 10 ]
		},
	'transit': {
		'visible':      [ 1 , 0 , 0 , 1 , 0 , 1 , 1 , 0 , 0 , 1 , 1 ],
		'visible_grid': [ 1 , 0 , 0 , 1 , 0 , 1 , 1 , 0 , 0 , 1 , 1 ],
		'orb':          [ 2 , 1 , 1 , 2 , 1 , 2 , 2 , 1 , 1 , 1 , 2 ]
		},
	'synastry': {
		'visible':      [ 1 , 0 , 0 , 1 , 0 , 1 , 1 , 0 , 0 , 1 , 1 ],
		'visible_grid': [ 1 , 0 , 0 , 1 , 0 , 1 , 1 , 0 , 0 , 1 , 1 ],
		'orb':          [ 6 , 1 , 1 , 4 , 1 , 5 , 5 , 1 , 1 , 2 , 6 ]
		}
	}
#default visibility of the bodies (index = settings_planet id), used for
#symbol, aspect line and aspect grid of radix charts and both sides of
#transit and synastry charts
PLANET_DEFAULT_VISIBLE = [
	1,1,1,1,1,1,1,
	1,1,1,1,0,1,0,
	0,1,0,0,0,0,0,
	0,0,1,1,0,0,1,
	1,0,0,0,0,0,0]
#asc based points (day pars, night pars, marriage pars) move as fast as the
#ascendant, transiting they are hidden by default
PLANET_TRANSIT_HIDDEN = ( 27 , 28 , 30 )
#first id of the angles (Asc, Mc, Dsc, Ic) and of the sensitive points
PLANET_FIRST_ANGLE = 23
PLANET_FIRST_POINT = 27
#dimensions of chart
CHARTX = 772.2 
CHARTY = 546.0
#radius of zodiac
RADIUS = 240

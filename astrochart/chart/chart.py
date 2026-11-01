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
State of the chart shown: event data, chart type and second event (transit,
partner, solar return, progression, combine), settings and positions.
Calculation and SVG drawing come from the mixins of astrochart.chart.
"""

import datetime
import pytz
from openastromod import zonetab
from astrochart.chart.data import ChartDataMixin
from astrochart.chart.importexport import ImportExportMixin
from astrochart.chart.svg_aspects import AspectsSVGMixin
from astrochart.chart.svg_chart import ChartSVGMixin
from astrochart.chart.svg_lists import ListsSVGMixin
from astrochart.chart.svg_planets import PlanetsSVGMixin
from astrochart.chart.svg_tables import TablesSVGMixin
from astrochart.chart.timecalc import TimeCalcMixin
from astrochart.util import dprint

class Chart(TimeCalcMixin, ChartSVGMixin, PlanetsSVGMixin, AspectsSVGMixin, ListsSVGMixin, TablesSVGMixin, ImportExportMixin, ChartDataMixin):
	def __init__(self, cfg, db, screen_width, screen_height):
		self.cfg = cfg
		self.db = db
		#the SVG size follows the screen size
		self.screen_width = screen_width
		self.screen_height = screen_height
		#get color configuration
		self.colors = self.db.getColors()
		#get label configuration
		#self.label = self.db.getLabel()
		# 12 zodiacs
		self.zodiac = ['aries','taurus','gemini','cancer','leo','virgo','libra','scorpio','sagittarius','capricorn','aquarius','pisces']
		self.zodiac_short = ['Ari','Tau','Gem','Cnc','Leo','Vir','Lib','Sco','Sgr','Cap','Aqr','Psc']
		self.zodiac_color = ['#482900','#6b3d00','#5995e7','#2b4972','#c54100','#2b286f','#69acf1','#ffd237','#ff7200','#863c00','#4f0377','#6cbfff']
		self.zodiac_element = ['fire','earth','air','water','fire','earth','air','water','fire','earth','air','water']

		#check for home
		self.home_location,self.home_geolat,self.home_geolon,self.home_countrycode,self.home_timezonestr = self.db.getSettingsLocation()
		if self.home_location == '' or self.home_geolat == '' or self.home_geolon == '':
			dprint('Unknown home location, asking for new')
			self.ask_for_home = True
			self.home_location='Ooyerhoek'
			self.home_geolon=6.219530
			self.home_geolat=52.120710
			self.home_countrycode='NL'
			self.home_timezonestr='Europe/Amsterdam'
		else:
			self.ask_for_home = False
			dprint('known home location: %s %s %s' % (self.home_location, self.home_geolat, self.home_geolon))
		#default location
		self.location=self.home_location
		self.geolat=float(self.home_geolat)
		self.geolon=float(self.home_geolon)
		self.countrycode=self.home_countrycode
		self.timezonestr=self.home_timezonestr
		#current datetime
		now = datetime.datetime.now()
		#aware datetime object
		dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
		dt = pytz.timezone(self.timezonestr).localize(dt_input)
		#naive utc datetime object
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		#Default
		self.name = _("Here and Now")
		self.charttype = _('Radix')
		self.year = dt_utc.year
		self.month = dt_utc.month
		self.day = dt_utc.day
		self.hour = self.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		self.timezone = self.offsetToTz(dt.utcoffset())
		self.altitude = 25
		self.geonameid = None
		# Make locals
		self.utcToLocal()
		self.type = "Radix"
		# synastry is drawn as type Transit, flag selects the synastry aspect set
		self.synastry = False

	def setSecondEvent(self, record):
		"""second event (partner) from a record of the event database"""
		self.t_name=str(record["name"])
		self.t_year=int(record["year"])
		self.t_month=int(record["month"])
		self.t_day=int(record["day"])
		self.t_hour=float(record["hour"])
		self.t_geolon=float(record["geolon"])
		self.t_geolat=float(record["geolat"])
		self.t_altitude=int(record["altitude"])
		self.t_location=str(record["location"])
		self.t_timezone=float(record["timezone"])

	def setSynastry(self, record):
		"""synastry with the partner record, drawn as transit chart"""
		self.type="Transit"
		self.setSecondEvent(record)
		self.charttype="%s (%s)" % (self.label["synastry"],self.t_name)
		self.transit=True
		self.synastry=True

	def setComposite(self, record):
		"""composite chart with the partner record"""
		self.type="Composite"
		self.setSecondEvent(record)
		self.charttype="%s (%s)" % (self.label["composite"],self.t_name)
		self.transit=False
		self.synastry=False

	def setCombine(self, record):
		"""combine chart: midpoint in time and space of chart and partner record"""
		self.type="Combine"
		self.setSecondEvent(record)
		#calculate combine between both utc times
		h,m,s = self.decHour(self.hour)
		dt1 = datetime.datetime(self.year,self.month,self.day,h,m,s)
		h,m,s = self.decHour(self.t_hour)
		dt2 = datetime.datetime(self.t_year,self.t_month,self.t_day,h,m,s)
		if dt1 > dt2:
			delta = dt1 - dt2
			hdelta = delta // 2
			combine = dt2 + hdelta
		else:
			delta = dt2 - dt1
			hdelta = delta // 2
			combine = dt1 + hdelta
		#take lon,lat middle
		self.c_geolon = (self.geolon + self.t_geolon)/2.0
		self.c_geolat = (self.geolat + self.t_geolat)/2.0
		self.c_altitude = (self.t_altitude + self.altitude)/2.0
		self.c_year = combine.year
		self.c_month = combine.month
		self.c_day = combine.day
		self.c_hour = self.decHourJoin(combine.hour,combine.minute,combine.second)
		self.charttype = "%s (%s)" % (self.label["combine"],self.t_name)
		self.transit = False
		self.synastry = False
		#set new date for printing in svg
		self.year = self.c_year
		self.month = self.c_month
		self.day = self.c_day
		self.hour = self.c_hour
		self.geolat = self.c_geolat
		self.geolon = self.c_geolon
		self.timezone_str = zonetab.nearest_tz(self.geolat,self.geolon,zonetab.timezones())[2]
		#aware datetime object
		dt_input = datetime.datetime(combine.year, combine.month, combine.day, combine.hour, combine.minute, combine.second)
		dt = pytz.timezone(self.timezone_str).localize(dt_input)
		self.timezone=self.offsetToTz(dt.utcoffset())
		self.utcToLocal()

	def setEvent(self, record):
		"""radix chart of a record of the event database or the history"""
		self.type = "Radix"
		self.charttype = self.label["radix"]
		self.name = str(record["name"])
		self.year = int(record["year"])
		self.month = int(record["month"])
		self.day = int(record["day"])
		self.hour = float(record["hour"])
		self.geolon = float(record["geolon"])
		self.geolat = float(record["geolat"])
		self.altitude = int(record["altitude"])
		self.location = str(record["location"])
		self.timezone = float(record["timezone"])
		self.countrycode = ''
		if "countrycode" in record:
			self.countrycode = record["countrycode"]
		if "timezonestr" in record:
			self.timezonestr = record["timezonestr"]
		else:
			self.timezonestr = self.db.gnearest(self.geolat,self.geolon)['timezonestr']
		self.geonameid = None
		if "geonameid" in record:
			self.geonameid = record['geonameid']
		self.utcToLocal()

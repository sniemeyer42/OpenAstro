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
Date, time and coordinate conversions, solar return, progression, transit dates
"""

import calendar
import datetime
import pytz
from openastromod import swiss as ephemeris
from astrochart.util import dprint

class TimeCalcMixin:
	"""Date, time and coordinate conversions, solar return, progression, transit dates"""

	def utcToLocal(self):
		# make local time variables from global UTC
		h, m, s = self.decHour(self.hour)
		utc = datetime.datetime(self.year, self.month, self.day, h, m, s)
		tz = datetime.timedelta(seconds=float(self.timezone)*float(3600))
		loc = utc + tz
		self.year_loc = loc.year
		self.month_loc = loc.month
		self.day_loc = loc.day
		self.hour_loc = loc.hour
		self.minute_loc = loc.minute
		self.second_loc = loc.second

		# print some info
		dprint('utcToLocal: '+str(utc)+' => '+str(loc)+self.decTzStr(self.timezone))

	def solarReturnMoment(self, newyear):
		"""solar return of the base event in newyear, as a naive UTC datetime;
		independent of the positions calculated for the current view"""
		planets = self.db.getSettingsPlanet('radix')
		def sun(moment):
			hour = self.decHourJoin(moment.hour, moment.minute, moment.second)
			data = ephemeris.ephData(moment.year, moment.month, moment.day, hour,
				self.geolon, self.geolat, self.altitude, planets, self.zodiac, self.db.astrocfg)
			return data.planets_degree_ut[0]

		h, m, s = self.decHour(self.hour)
		original = datetime.datetime(self.year, self.month, self.day, h, m, s)
		target = ephemeris.ephData(self.year, self.month, self.day, self.hour,
			self.geolon, self.geolat, self.altitude, planets, self.zodiac, self.db.astrocfg).planets_degree_ut[0]
		#February 29 also has a solar return in a non-leap year.
		day = min(self.day, calendar.monthrange(newyear, self.month)[1])
		moment = original.replace(year=newyear, day=day)
		def difference():
			#The signed angle also works across the 0/360 degree boundary.
			return (target - sun(moment) + 180.0) % 360.0 - 180.0
		#Keep the established mean-year, second and millisecond corrections.
		moment += datetime.timedelta(seconds=int(difference() / 360.0 * 31556925.51))
		moment += datetime.timedelta(seconds=int(difference() / 0.000011408))
		moment += datetime.timedelta(milliseconds=int(difference() / 0.000000011408))
		#The chart state stores whole seconds, shared by both solar views.
		return moment.replace(microsecond=0)

	def localToSolar(self, newyear, overlay=False):
		"""solar return alone, or as the outer ring over the unchanged radix"""
		moment = self.solarReturnMoment(newyear)
		self.solar_year = newyear
		self.solar_return = bool(overlay)
		self.synastry = False
		self.transit = bool(overlay)
		if overlay:
			self.type = "Transit"
			self.t_year, self.t_month, self.t_day = moment.year, moment.month, moment.day
			self.t_hour = self.decHourJoin(moment.hour, moment.minute, moment.second)
			self.t_geolon, self.t_geolat, self.t_altitude = self.geolon, self.geolat, self.altitude
			self.t_location = self.location
			self.t_name = _("Solar Return")
			self.t_timezonestr = self.timezonestr
			if self.t_timezonestr in pytz.all_timezones_set:
				zone = pytz.timezone(self.t_timezonestr)
				self.t_timezone = self.offsetToTz(pytz.utc.localize(moment).astimezone(zone).utcoffset())
			else:
				#Older chart files may contain only a numeric timezone offset.
				self.t_timezone = self.timezone
		else:
			self.type = "Solar"
			self.s_year, self.s_month, self.s_day = moment.year, moment.month, moment.day
			self.s_hour = self.decHourJoin(moment.hour, moment.minute, moment.second)
			self.s_geolon, self.s_geolat, self.s_altitude = self.geolon, self.geolat, self.altitude
		self.charttype = "%s (%s-%02d-%02d %02d:%02d:%02d UTC)" % (
			self.label["solar"], moment.year, moment.month, moment.day, moment.hour, moment.minute, moment.second)
		return moment

	"""
	 Secondary Progression
	  Calculate years between birth and date,
	  add as days to birth date
	"""	
	def localToSecondaryProgression(self, dt):
		# remove timezone
		dt_utc = dt - datetime.timedelta(seconds=float(self.timezone)*float(3600))
		y,mth,d,hrs = ephemeris.years_diff(self.year, self.month, self.day, self.hour,
dt_utc.year, dt_utc.month, dt_utc.day,self.decHourJoin(dt_utc.hour,dt_utc.minute, dt_utc.second))
		h,m,s = self.decHour(hrs)
		dt_new = datetime.datetime(y,mth,d,h,m,s)
		self.sp_year = dt_new.year
		self.sp_month = dt_new.month
		self.sp_day = dt_new.day
		self.sp_hour = self.decHourJoin(dt_new.hour,dt_new.minute,dt_new.second)
		self.sp_geolon = self.geolon
		self.sp_geolat = self.geolat
		self.sp_altitude = self.altitude
		self.houses_override = [dt_new.year, dt_new.month, dt_new.day, self.hour]

		dprint("localToSecondaryProgression: got UTC %s-%s-%s %s:%s:%s"%(dt_new.year, dt_new.month, dt_new.day, dt_new.hour, dt_new.minute, dt_new.second))

		self.type = "SecondaryProgression"
		self.charttype="%s (%s-%02d-%02d %02d:%02d)" % (self.label["secondary_progressions"], dt.year, dt.month, dt.day, dt.hour, dt.minute)
		self.transit = False
		self.synastry = False
		self.solar_return = False
		self.solar_year = None
		return

	"""
	 Transit
	  local date and time at home location converted to UTC,
	  daylight saving time is regarded for every date
	"""
	def localToTransit(self, dt):
		#aware datetime object (a naive one is the local time of the transit timezone)
		dt_aware = dt if dt.tzinfo is not None else pytz.timezone(self.t_timezonestr).localize(dt)
		#naive utc datetime object
		dt_utc = dt_aware.replace(tzinfo=None) - dt_aware.utcoffset()
		self.t_year = dt_utc.year
		self.t_month = dt_utc.month
		self.t_day = dt_utc.day
		self.t_hour = self.decHourJoin(dt_utc.hour, dt_utc.minute, dt_utc.second)
		self.t_timezone = self.offsetToTz(dt_aware.utcoffset())
		self.t_geolon = float(self.home_geolon)
		self.t_geolat = float(self.home_geolat)
		self.t_altitude = 25
		self.type = "Transit"
		self.charttype = "%s (%s-%02d-%02d %02d:%02d)" % (self.label["transit"], dt.year, dt.month, dt.day, dt.hour, dt.minute)
		self.transit = True
		self.synastry = False
		self.solar_return = False
		self.solar_year = None
		return dt_aware

	""" Convert latitude and longitude floats to string """
	def lat2str( self, coord ):
		sign=self.label["north"]
		if coord < 0.0:
			sign = self.label["south"]
			coord = abs(coord)
		deg = int(coord)
		min = int( (float(coord) - deg) * 60 )
		sec = int( round( float( ( (float(coord) - deg) * 60 ) - min) * 60.0 ) )
		return "%s°%s'%s\" %s" % (deg,min,sec,sign)

	def lon2str( self, coord ):
		sign = self.label["east"]
		if coord < 0.0:
			sign = self.label["west"]
			coord = abs(coord)
		deg = int(coord)
		min = int( (float(coord) - deg) * 60 )
		sec = int( round( float( ( (float(coord) - deg) * 60 ) - min) * 60.0 ) )
		return "%s°%s'%s\" %s" % (deg,min,sec,sign)

	"""
		Convert decimal hour to minutes and seconds
		corrected for rounding error in case of repeating decimal
	"""
	def decHour( self , input ):
		total= int(input * 3600 + 0.5)
		m, s = divmod(total, 60)
		h, m = divmod(m, 60)
		return [h,m,s]

	""" join hour, minutes, seconds, timezone integere to hour float """
	def decHourJoin( self, inH, inM, inS ):
		dh = float(inH)
		dm = float(inM)/60
		ds = float(inS)/3600
		output = dh + dm + ds
		return output

	""" Convert datetime offset to hours as float"""
	def offsetToTz( self, dtoffset ):
		dh = float(dtoffset.days * 24)
		sh = float(dtoffset.seconds / 3600.0)
		output = dh + sh
		return output

	""" Decimal timezone string """
	def decTzStr( self, tz ):
		if tz > 0:
			h = int(tz)
			m = int((float(tz)-float(h))*float(60))
			return " [+%(#1)02d:%(#2)02d]" % {'#1':h,'#2':m}
		else:
			h = int(tz)
			m = int((float(tz)-float(h))*float(60))/-1
			return " [-%(#1)02d:%(#2)02d]" % {'#1':h/-1,'#2':m}

	""" Degree difference """
	def degreeDiff( self, a ,b ):
		out=float()
		if a > b:
			out=a-b
		if a < b:
			out=b-a
		if out > 180.0:
			out=360.0-out
		return out

	""" Decimal to degrees (a°b'c") """
	def dec2deg( self, dec, type="3" ):
		dec=float(dec)
		a=int(dec)
		a_new=(dec-float(a)) * 60.0
		b_rounded = int(round(a_new))
		b=int(a_new)
		c=int(round((a_new-float(b))*60.0))
		if type=="3":
			out = '%(#1)02d&#176;%(#2)02d&#39;%(#3)02d&#34;' % {'#1':a,'#2':b, '#3':c}
		elif type=="2":
			out = '%(#1)02d&#176;%(#2)02d&#39;' % {'#1':a,'#2':b_rounded}
		elif type=="1":
			out = '%(#1)02d&#176;' % {'#1':a}
		return str(out)

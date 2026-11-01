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
Chart files: OAC export/import and imports of other programs
"""

import datetime
import codecs
import pytz
from string import Template
from gi.repository import Gtk
from openastromod import zonetab, importfile
from astrochart.state import app
from astrochart.util import dprint

class ImportExportMixin:
	"""Chart files: OAC export/import and imports of other programs"""

	"""
	 Export/Import Functions situated in AstroApplication
	  exportOAC(filename)
	  importOAC(filename)
	  importOroboros(filename)
	"""
	def exportOAC(self,filename):
		template = """<?xml version='1.0' encoding='UTF-8'?>
<openastrochart>
	<name>$name</name>
	<datetime>$datetime</datetime>
	<location>$location</location>
	<altitude>$altitude</altitude>
	<latitude>$latitude</latitude>
	<longitude>$longitude</longitude>
	<countrycode>$countrycode</countrycode>
	<timezone>$timezone</timezone>
	<geonameid>$geonameid</geonameid>
	<timezonestr>$timezonestr</timezonestr>
	<extra>$extra</extra>
</openastrochart>"""
		h,m,s = self.decHour(self.hour)
		dt = datetime.datetime(self.year,self.month,self.day,h,m,s)
		substitute = {}
		substitute['name'] = self.name
		substitute['datetime'] = dt.strftime("%Y-%m-%d %H:%M:%S")
		substitute['location'] = self.location
		substitute['altitude'] = self.altitude
		substitute['latitude'] = self.geolat
		substitute['longitude'] = self.geolon
		substitute['countrycode'] = self.countrycode
		substitute['timezone'] = self.timezone
		substitute['timezonestr'] = self.timezonestr
		substitute['geonameid'] = self.geonameid
		substitute['extra'] = ''
		#write the results to the template
		output = Template(template).substitute(substitute)
		f = open(filename,"w")
		f.write(output)
		f.close()

		dprint("exporting OAC: %s" % filename)

		return

	def importOAC(self, filename):
		r = importfile.getOAC(filename)[0]
		dt = datetime.datetime.strptime(r['datetime'],"%Y-%m-%d %H:%M:%S")
		self.name = r['name']
		self.countrycode = r['countrycode']
		self.altitude = int(r['altitude'])
		self.geolat = float(r['latitude'])
		self.geolon = float(r['longitude'])
		self.timezone = float(r['timezone'])
		self.geonameid = r['geonameid']
		if "timezonestr" in r:
			self.timezonestr = r['timezonestr']
		else:
			self.timezonestr = self.db.gnearest(self.geolat,self.geolon)['timezonestr']
		self.location = r['location']
		self.year = dt.year
		self.month = dt.month
		self.day = dt.day
		self.hour = self.decHourJoin(dt.hour,dt.minute,dt.second)
		# make locals
		self.utcToLocal()

		# debug print
		dprint('importOAC: %s' % filename)

		return

	def importOroboros(self, filename):
		r = importfile.getOroboros(filename)[0]
		# naive local datetime
		naive = datetime.datetime.strptime(r['datetime'],"%Y-%m-%d %H:%M:%S")
		# aware datetime object
		dt_input = datetime.datetime(naive.year, naive.month, naive.day, naive.hour, naive.minute, naive.second)
		dt = pytz.timezone(r['zoneinfo']).localize(dt_input)
		# naive utc datetime object
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		# process latitude/longitude
		deg,type,min,sec = r['latitude'].split(":")
		lat = float(deg)+( float(min) / 60.0 )+( float(sec) / 3600.0 )
		if type == "S":
			lat = decimal / -1.0
		deg,type,min,sec = r['longitude'].split(":")
		lon = float(deg)+( float(min) / 60.0 )+( float(sec) / 3600.0 )
		if type == "W":
			lon = decimal / -1.0
		geon = self.db.gnearest(float(lat),float(lon))
		self.timezonestr = geon['timezonestr']
		self.geonameid = geon['geonameid']
		self.name = r['name']
		self.countrycode = ''
		self.altitude = int(r['altitude'])
		self.geolat = lat
		self.geolon = lon
		self.timezone = self.offsetToTz(dt.utcoffset())
		self.location = '%s, %s' % (r['location'],r['countryname'])
		self.year = dt_utc.year
		self.month = dt_utc.month
		self.day = dt_utc.day
		self.hour = self.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		# make locals
		self.utcToLocal()

		# debug print
		dprint('importOroboros: UTC: %s file: %s' % (dt_utc,filename))

		return

	def importSkylendar(self, filename):
		r = importfile.getSkylendar(filename)[0]
		# naive local datetime
		naive = datetime.datetime(int(r['year']),int(r['month']),int(r['day']),int(r['hour']),int(r['minute']))
		# aware datetime object
		dt_input = datetime.datetime(naive.year, naive.month, naive.day, naive.hour, naive.minute, naive.second)
		dt = pytz.timezone(r['zoneinfofile']).localize(dt_input)
		# naive utc datetime object
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		geon = self.db.gnearest(float(r['latitude']),float(r['longitude']))
		self.timezonestr=geon['timezonestr']
		self.geonameid=geon['geonameid']
		self.name=r['name']
		self.countrycode=''
		self.altitude=25
		self.geolat=float(r['latitude'])
		self.geolon=float(r['longitude'])
		self.timezone=float(r['timezone'])
		self.location='%s, %s' % (r['location'],r['countryname'])
		self.year=dt_utc.year
		self.month=dt_utc.month
		self.day=dt_utc.day
		self.hour=self.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		# make locals
		self.utcToLocal()
		return

	"""
	 Check Timezone in case of Daylight Saving
	"""
	def specialTimeZone(self, tz):
		# create a new window
		self.win_TZ = Gtk.Window(title=_("Daylight Saving Time Detected"))
		""" set_icon """
		#self.win_TZ.set_icon_from_file(app.cfg.iconWindow)
		#self.win_TZ.connect("delete_event", lambda w,e: self.win_TZ.destroy())
		#self.win_TZ.move(150, 150)
		#self.win_TZ.set_border_width(5)
		self.win_TZ.set_default_size(300,100)
		self.win_TZ.set_modal()
		tz_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		tz_box.set_spacing(12)
		header = Gtk.Label(label=_("Change Timezone ?"))
		tz_box.append(header)
		entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		_label = Gtk.Label(label=_("Actual Timezone:"))
		entry_box.append(_label)
		tz_split = tz.split('/')
		_entry = Gtk.Entry()
		_entry.set_max_length(16)
		_entry.set_width_chars(12)
		_entry.set_alignment(xalign=1)
		_entry.set_editable(False)
		_entry.set_text(tz_split[0])
		entry_box.append(_entry)
		_label = Gtk.Label(label=_(" / "))
		entry_box.append(_label)
		tz_entry = Gtk.Entry()
		tz_entry.set_max_length(32)
		tz_entry.set_width_chars(24)
		tz_entry.set_text(tz_split[1])
		tz_entry.connect("activate", self.specialTimeZoneSubmit, tz_entry)
		entry_box.append(tz_entry)
		tz_box.append(entry_box)
		hints = Gtk.Label(label=_("Change Timezone and press <Enter>"))
		tz_box.append(hints)
		button = Gtk.Button.new_with_mnemonic(label = _("Cancel"))
		#button.set_can_default(True)
		button.connect("clicked", lambda w: self.win_TZ.destroy())
		self.win_TZ.set_child(tz_box)
		#self.win_TZ.action_area.pack_end(child=button, expand=False, fill=False, padding=16)
		#self.win_TZ.action_area.pack_start(button, True, True, 0)
		self.win_TZ.present()
		tz_entry.grab_focus()

		#self.win_TZ.run()

	def specialTimeZoneSubmit(self, widged, entry):
		s = self.timezone_str
		self.timezone_str = s[:s.find('/')+1] + entry.get_text()
		self.win_TZ.destroy()

	def importAstrolog(self, filename):
		r = importfile.getAstrolog32(filename)[0]
		#timezone string
		self.timezone_str = zonetab.nearest_tz(float(r['latitude']),float(r['longitude']),zonetab.timezones())[2]
		"""
		  Above looks for nearest noted continent/city, but sometimes
		  this is a city with deviating daylight saving time
		"""
		if r['daylight']:
			self.specialTimeZone(self.timezone_str)
		# naive local datetime
		naive = datetime.datetime(int(r['year']),int(r['month']),int(r['day']),int(r['hour']),int(r['minute']),int(r['second']))
		# aware datetime object
		dt_input = datetime.datetime(naive.year, naive.month, naive.day, naive.hour, naive.minute, naive.second)
		dt = pytz.timezone(self.timezone_str).localize(dt_input)
		# naive utc datetime object
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		geon = self.db.gnearest(float(r['latitude']),float(r['longitude']))
		self.timezonestr=geon['timezonestr']
		self.geonameid=geon['geonameid']
		self.name=r['name']
		self.countrycode=''
		self.altitude=25
		self.geolat=float(r['latitude'])
		self.geolon=float(r['longitude'])
		self.timezone=self.offsetToTz(dt.utcoffset())
		self.location=r['location']
		self.year=dt_utc.year
		self.month=dt_utc.month
		self.day=dt_utc.day
		self.hour=self.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		# make locals
		self.utcToLocal()
		return

	def importZet8(self, filename):
		h=open(filename)
		f=codecs.EncodedFile(h,"utf-8","latin-1")
		data=[]
		for line in f.readlines():
			s=line.split(";")
			if s[0] == line:
				continue
			data.append({})
			data[-1]['name']=s[0].strip()
			day=int( s[1].strip().split('.')[0] )
			month=int( s[1].strip().split('.')[1] )
			year=int( s[1].strip().split('.')[2] )
			hour=int(  s[2].strip().split(':')[0] )
			minute=int( s[2].strip().split(':')[1] )
			if len(s[3].strip()) > 3:
				data[-1]['timezone']=float( s[3].strip().split(":")[0] )
				if data[-1]['timezone'] < 0:
					data[-1]['timezone']-= float( s[3].strip().split(":")[1] ) / 60.0
				else:
					data[-1]['timezone']+= float( s[3].strip().split(":")[1] ) / 60.0
			elif len(s[3].strip()) > 0:
				data[-1]['timezone']=int(s[3].strip())
			else:
				data[-1]['timezone']=0
			# substract timezone from date
			dt = datetime.datetime(year,month,day,hour,minute)
			dt = dt - datetime.timedelta(seconds=float(data[-1]['timezone'])*float(3600))
			data[-1]['year'] = dt.year
			data[-1]['month'] = dt.month
			data[-1]['day'] = dt.day
			data[-1]['hour'] =  float(dt.hour) + float(dt.minute/60.0)
			data[-1]['location']=s[4].strip()
			# latitude
			p=s[5].strip()
			if p.find("°") != -1:
				# later version of zet8
				if p.find("S") == -1:
					deg=p.split("°")[0] #\xc2
					min=p[p.find("°")+2:p.find("'")]
					sec=p[p.find("'")+1:p.find('"')]
					data[-1]['latitude']=float(deg)+(float(min)/60.0)
				else:
					deg=p.split("°")[0] #\xc2
					min=p[p.find("°")+2:p.find("'")]
					sec=p[p.find("'")+1:p.find('"')]
					data[-1]['latitude']=( float(deg)+(float(min)/60.0) ) / -1.0
			else:
				# earlier version of zet8
				if p.find("s") == -1:
					i=p.find("n")
					data[-1]['latitude']=float(p[:i])+(float(p[i+1:])/60.0)
				else:
					i=p.find("s")
					data[-1]['latitude']=( float(p[:i])+(float(p[i+1:])/60.0) ) / -1.0
			# longitude
			p=s[6].strip()
			if p.find("°") != -1:
				#later version of zet8
				if p.find("W") == -1:
					deg = p.split("°")[0] #\xc2
					min = p[p.find("°")+2:p.find("'")]
					sec = p[p.find("'")+1:p.find('"')]
					data[-1]['longitude'] = float(deg)+(float(min)/60.0)
				else:
					deg = p.split("°")[0] #\xc2
					min = p[p.find("°")+2:p.find("'")]
					sec = p[p.find("'")+1:p.find('"')]
					data[-1]['longitude'] = ( float(deg)+(float(min)/60.0) ) / -1.0
			else:
				# earlier version of zet8
				if p.find("w") == -1:
					i=p.find("e")
					data[-1]['longitude'] = float(p[:i])+(float(p[i+1:])/60.0)
				else:
					i=p.find("w")
					data[-1]['longitude'] = ( float(p[:i])+(float(p[i+1:])/60.0) ) / -1.0
		self.db.importZet8(app.cfg.peopledb , data)

		dprint('importZet8: database with %s entries: %s' % (len(data),filename))

		f.close()
		return

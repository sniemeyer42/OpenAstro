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
Event records: own events (add, change, delete), famous people, local date
of a record
"""

import datetime
import pytz
import sqlite3
from astrochart.util import dprint

def loadFamous(cfg, chart, limit=None, search=None):
	""" famous people from year 1800 onwards as event records (times in UTC) """
	flink = sqlite3.connect(cfg.famousdb)
	flink.row_factory = sqlite3.Row
	fcursor = flink.cursor()
	sql = 'SELECT * FROM famous WHERE year>?'
	args = (1800,)
	if search is not None:
		sql += ' AND (lastname LIKE ? OR firstname LIKE ? OR name LIKE ?)'
		args += (search, search, search)
	if limit is not None:
		sql += ' LIMIT %d' % (int(limit))
	fcursor.execute(sql, args)
	oldDB=fcursor.fetchall()
	fcursor.close()
	flink.close()
	#process database
	newDB = []
	for a in range(len(oldDB)):
		# minus years
		if oldDB[a][12] == '571/': #Muhammad
			year = 571
		elif oldDB[a][12] <= 0:
			year = 1
		else:
			year = oldDB[a][12]
		month = oldDB[a][13]
		day = oldDB[a][14]
		hour = oldDB[a][15]
		h,m,s = chart.decHour(hour)
		# aware datetime object
		dt_input = datetime.datetime(year,month,day,h,m,s)
		dt = pytz.timezone(oldDB[a][20]).localize(dt_input)
		# naive utc datetime object
		dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()
		# timezone
		timezone=chart.offsetToTz(dt.utcoffset())
		year = dt_utc.year
		month = dt_utc.month
		day = dt_utc.day
		hour = chart.decHourJoin(dt_utc.hour,dt_utc.minute,dt_utc.second)
		newDB.append({
			"id":oldDB[a][0], #index
			"name":oldDB[a][3]+" "+oldDB[a][4], #christian name, name
			"year":year, #year
			"month":month, #month
			"day":day, #day
			"hour":hour, #hour
			"geolon":oldDB[a][18], #geolon
			"geolat":oldDB[a][17], #geolat
			"altitude":"25", #altitude
			"location":oldDB[a][16], #location
			"timezone":timezone, #timezone
			"notes":"",#notes
			"image":"",#image
			"countrycode":oldDB[a][8], #countrycode
			"geonameid":oldDB[a][19], #geonameid
			"timezonestr":oldDB[a][20], #timezonestr
			"extra":"" #extra
		})
	return newDB

def localDate(chart, record):
	"""local date and time of a record as text YYYY-MM-DD hh:mm:ss"""
	h, m, s = chart.decHour(float(record["hour"]))
	dt_utc = datetime.datetime(int(record["year"]), int(record["month"]), int(record["day"]), h, m, s)
	dt = dt_utc + datetime.timedelta(seconds=float(record["timezone"]) * 3600.0)
	return '%04d-%02d-%02d %02d:%02d:%02d' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

def nameTaken(db, name, ident=None):
	"""True if another entry of the event database (not ident) has the name"""
	return any(row["name"] == name and row["id"] != ident for row in db.getDatabase())

def insertEvent(db, chart):
	"""add the event of the chart to the event database"""
	sql='INSERT INTO event_natal (id, name, year, month, day, hour, geolon, geolat, altitude, location, timezone, notes, image, countrycode, geonameid, timezonestr, extra) VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
	values=(chart.name, chart.year, chart.month, chart.day, chart.hour, chart.geolon, chart.geolat, chart.altitude, chart.location, chart.timezone, '', '', chart.countrycode, chart.geonameid, chart.timezonestr, '')
	db.pquery([sql], [values])
	dprint('Saved to Database: ' + chart.name)

def updateEvent(db, chart, ident):
	"""entry ident of the event database gets the event of the chart"""
	sql = 'UPDATE event_natal SET name=?,year=?,month=?,day=?,hour=?, geolon=?, geolat=?, altitude=?, location=?, timezone=?, notes=?, image=?, countrycode=?, timezonestr=?, geonameid=? WHERE id=?'
	values = (chart.name, chart.year, chart.month, chart.day, chart.hour, chart.geolon, chart.geolat, chart.altitude, chart.location, chart.timezone, '', '', chart.countrycode, chart.timezonestr, chart.geonameid, ident)
	db.pquery([sql], [values])
	dprint('After editing saved to database: ' + chart.name)

def deleteEvent(db, record):
	"""remove the entry of record from the event database"""
	db.pquery(['DELETE FROM event_natal WHERE id=?'], [(record["id"],)])
	dprint('Deleted Database Entry: ' + record["name"])

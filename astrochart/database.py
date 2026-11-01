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
Sqlite databases (settings, history, people, geonames)
"""

import sys
import sqlite3
from openastromod import zonetab, geoname
from astrochart.constants import ASPECT_CHART_TYPES, ASPECT_COLORS, ASPECT_DEFAULTS, ASPECT_DEGREES, ASPECT_IS_MAJOR, ASPECT_IS_MINOR, LIMIT, PLANET_DEFAULT_VISIBLE, PLANET_TRANSIT_HIDDEN
from astrochart.i18n import LANGUAGES_LABEL, TRANSLATION
from astrochart.state import app
from astrochart.util import aspectFlag, aspectOrb, dprint

""" OpenAstro Sqlite Database """
class OpenAstroSqlite:
	def __init__(self):
		self.dbcheck=False
		self.dbpurge="IGNORE"

		#--dbcheck puts dbcheck to true
		if "--dbcheck" in sys.argv:
			self.dbcheck=True
			dprint("  Database Check Enabled!")
			dprint("-------------------------------")
		#--purge purges database
		if "--purge" in sys.argv:
			self.dbcheck=True
			self.dbpurge="REPLACE"
			dprint("  Database Check Enabled!")
			dprint("  Database Purge Enabled!")
			dprint("-------------------------------")
		self.open()
		#get table names from sqlite_master for astrodb
		sql='SELECT name FROM sqlite_master'
		self.cursor.execute(sql)
		list=self.cursor.fetchall()
		self.tables={}
		for i in range(len(list)):
			self.tables[list[i][0]]=1

		#get table names from sqlite_master for peopledb
		sql='SELECT name FROM sqlite_master'
		self.pcursor.execute(sql)
		list=self.pcursor.fetchall()
		self.ptables={}
		for i in range(len(list)):
			self.ptables[list[i][0]]=1

		#check for event_natal table in peopledb
		self.ptable_event_natal = {
			"id":"INTEGER PRIMARY KEY",
			"name":"VARCHAR(50)",
			"year":"VARCHAR(4)",
			"month":"VARCHAR(2)",
			"day":"VARCHAR(2)",
			"hour":"VARCHAR(50)",
			"geolon":"VARCHAR(50)",
			"geolat":"VARCHAR(50)",
			"altitude":"VARCHAR(50)",
			"location":"VARCHAR(150)",
			"timezone":"VARCHAR(50)",
			"notes":"VARCHAR(500)",
			"image":"VARCHAR(250)",
			"countrycode":"VARCHAR(2)",
			"geonameid":"INTEGER",
			"timezonestr":"VARCHAR(100)",
			"extra":"VARCHAR(500)"
			}
		if 'event_natal' not in self.ptables:
			sql='CREATE TABLE IF NOT EXISTS event_natal (id INTEGER PRIMARY KEY,name VARCHAR(50)\
				 ,year VARCHAR(4),month VARCHAR(2), day VARCHAR(2), hour VARCHAR(50), geolon VARCHAR(50)\
			 	,geolat VARCHAR(50), altitude VARCHAR(50), location VARCHAR(150), timezone VARCHAR(50)\
			 	,notes VARCHAR(500), image VARCHAR(250), countrycode VARCHAR(2), geonameid INTEGER\
			 	,timezonestr VARCHAR(100), extra VARCHAR(250))'
			self.pcursor.execute(sql)
			dprint('creating sqlite table event_natal in peopledb')

		#check for astrocfg table in astrodb
		if 'astrocfg' not in self.tables:
			#0=cfg_name, 1=cfg_value
			sql='CREATE TABLE IF NOT EXISTS astrocfg (name VARCHAR(150) UNIQUE,value VARCHAR(150))'
			self.cursor.execute(sql)
			self.dbcheck=True
			dprint('creating sqlite table astrocfg in astrodb')

		#check for astrocfg version
		sql='INSERT OR IGNORE INTO astrocfg (name,value) VALUES(?,?)'
		self.cursor.execute(sql,("version", app.cfg.version))
		#get astrocfg dict
		sql='SELECT value FROM astrocfg WHERE name="version"'
		self.cursor.execute(sql)
		self.astrocfg = {}
		self.astrocfg["version"]=self.cursor.fetchone()[0]

		#check for updated version 
		if self.astrocfg['version'] != str(app.cfg.version):
			dprint('version mismatch(%s != %s), checking table structure' % (self.astrocfg['version'], app.cfg.version))
			#insert current version and set dbcheck to true
			self.dbcheck = True
			sql='INSERT OR REPLACE INTO astrocfg VALUES("version","'+str(app.cfg.version)+'")'
			self.cursor.execute(sql)

		#default astrocfg keys (if dbcheck)
		if self.dbcheck:
			dprint('dbcheck astrodb.astrocfg')
			default = {
				"version":str(app.cfg.version),
				"use_geonames.org":"0",
				"houses_system":"P",
				"language":"default",
				"postype":"geo",
				"chartview":"traditional",
				"zodiactype":"tropical",
				"siderealmode":"FAGAN_BRADLEY"
			 }
			for k, v in default.items():
				sql='INSERT OR %s INTO astrocfg (name,value) VALUES(?,?)' % (self.dbpurge)
				self.cursor.execute(sql,(k,v))

		#get astrocfg dict
		sql = 'SELECT * FROM astrocfg'
		self.cursor.execute(sql)
		self.astrocfg = {}
		for row in self.cursor:
			self.astrocfg[row['name']] = row['value']
		#install language
		self.setLanguage(self.astrocfg['language'])
		self.lang_label = LANGUAGES_LABEL
		#fix inconsitencies between in people's database
		if self.dbcheck:
			sql='PRAGMA table_info(event_natal)'
			self.pcursor.execute(sql)
			list=self.pcursor.fetchall()
			vacuum = False
			cnames=[]
			for i in range(len(list)):
				cnames.append(list[i][1])
			for key,val in self.ptable_event_natal.items():
				if key not in cnames:
					sql = 'ALTER TABLE event_natal ADD %s %s'%(key,val)
					dprint("dbcheck peopledb.event_natal adding %s %s"%(key,val))
					self.pcursor.execute(sql)
					vacuum = True
			if vacuum:
				sql = "VACUUM"
				self.pcursor.execute(sql)

				dprint('dbcheck peopledb.event_natal: updating table definitions!')

		#check for history table in astrodb
		if 'history' not in self.tables:
			#0=id,1=name,2=year,3=month,4=day,5=hour,6=geolon,7=geolat,8=alt,9=location,10=tz
			sql='CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY,name VARCHAR(50)\
				 ,year VARCHAR(50),month VARCHAR(50), day VARCHAR(50), hour VARCHAR(50), geolon VARCHAR(50)\
			 	,geolat VARCHAR(50), altitude VARCHAR(50), location VARCHAR(150), timezone VARCHAR(50)\
			 	,notes VARCHAR(500), image VARCHAR(250), countrycode VARCHAR(2), geonameid INTEGER, extra VARCHAR(250))'
			self.cursor.execute(sql)

			dprint('creating sqlite table history in astrodb')

		#fix inconsitencies between 0.6x and 0.7x in history table
		if self.dbcheck:
			sql='PRAGMA table_info(history)'
			self.cursor.execute(sql)
			list=self.cursor.fetchall()
			cnames=[]
			for i in range(len(list)):
				cnames.append(list[i][1])
			vacuum = False
			if "notes" not in cnames:
				sql = 'ALTER TABLE history ADD notes VARCHAR(500)'
				self.cursor.execute(sql)
				vacuum = True
			if "image" not in cnames:
				sql = 'ALTER TABLE history ADD image VARCHAR(250)'
				self.cursor.execute(sql)
				vacuum = True
			if "countrycode" not in cnames:
				sql = 'ALTER TABLE history ADD countrycode VARCHAR(2)'
				self.cursor.execute(sql)
				vacuum = True
			if "geonameid" not in cnames:
				sql = 'ALTER TABLE history ADD geonameid INTEGER'
				self.cursor.execute(sql)
				vacuum = True
			if "extra" not in cnames:
				sql = 'ALTER TABLE history ADD extra VARCHAR(250)'
				self.cursor.execute(sql)
				vacuum = True
			if vacuum:
				sql = "VACUUM"
				self.cursor.execute(sql)

				dprint('dbcheck: updating history table definitions!')

		#check for settings_aspect table in astrodb
		if 'settings_aspect' not in self.tables:
			sql='CREATE TABLE IF NOT EXISTS settings_aspect (degree INTEGER UNIQUE, name VARCHAR(50)\
				 ,color VARCHAR(50),visible INTEGER, visible_grid INTEGER\
				 ,is_major INTEGER, is_minor INTEGER, orb VARCHAR(5))'
			self.cursor.execute(sql)
			self.dbcheck=True

			dprint('creating sqlite table settings_aspect in astrodb')

		#if update, check if everything is in order
		if self.dbcheck:
			sql='PRAGMA table_info(settings_aspect)'
			self.cursor.execute(sql)
			list=self.cursor.fetchall()
			cnames=[]
			for i in range(len(list)):
				cnames.append(list[i][1])
			vacuum = False
			if "visible" not in cnames:
				sql = 'ALTER TABLE settings_aspect ADD visible INTEGER'
				self.cursor.execute(sql)
				vacuum = True
			if "visible_grid" not in cnames:
				sql = 'ALTER TABLE settings_aspect ADD visible_grid INTEGER'
				self.cursor.execute(sql)
				vacuum = True
			if "is_major" not in cnames:
				sql = 'ALTER TABLE settings_aspect ADD is_major INTEGER'
				self.cursor.execute(sql)
				vacuum = True
			if "is_minor" not in cnames:
				sql = 'ALTER TABLE settings_aspect ADD is_minor INTEGER'
				self.cursor.execute(sql)
				vacuum = True
			if "orb" not in cnames:
				sql = 'ALTER TABLE settings_aspect ADD orb VARCHAR(5)'
				self.cursor.execute(sql)
				vacuum = True
			if vacuum:
				sql = "VACUUM"
				self.cursor.execute(sql)
		#default values for settings_aspect (if dbcheck)
		if self.dbcheck:
			dprint('dbcheck astrodb.settings_aspect')
			degree = ASPECT_DEGREES
			name = self.getAspectLabels()
			color = ASPECT_COLORS
			visible =      ASPECT_DEFAULTS['radix']['visible']
			visible_grid = ASPECT_DEFAULTS['radix']['visible_grid']
			is_major =     ASPECT_IS_MAJOR
			is_minor =     ASPECT_IS_MINOR
			orb =          ASPECT_DEFAULTS['radix']['orb']
			#insert values
			for i in range(len(degree)):
				sql='INSERT OR %s INTO settings_aspect \
				(degree, name, color, visible, visible_grid, is_major, is_minor, orb)\
				VALUES(%s,"%s","%s",%s,%s,%s,%s,"%s")' % ( self.dbpurge,degree[i],name[i],color[i],visible[i],
				visible_grid[i],is_major[i],is_minor[i],orb[i] )
				self.cursor.execute(sql)
		#aspect settings of transit and synastry charts (radix stays in settings_aspect,
		#which is shared with the Gtk3 programs), new rows get the defaults on every start
		sql='CREATE TABLE IF NOT EXISTS settings_aspect_chart (chart_type VARCHAR(16) NOT NULL\
			 ,degree INTEGER NOT NULL, visible INTEGER, visible_grid INTEGER, orb REAL\
			 ,PRIMARY KEY (chart_type, degree))'
		self.cursor.execute(sql)
		for ctype in ASPECT_CHART_TYPES:
			if ctype == 'radix':
				continue
			default = ASPECT_DEFAULTS[ctype]
			for i in range(len(ASPECT_DEGREES)):
				sql='INSERT OR %s INTO settings_aspect_chart (chart_type, degree, visible, visible_grid, orb)\
					VALUES(?,?,?,?,?)' % (self.dbpurge)
				self.cursor.execute(sql,(ctype, ASPECT_DEGREES[i], default['visible'][i],
					default['visible_grid'][i], float(default['orb'][i])))
		#check for colors table in astrodb
		if 'color_codes' not in self.tables:
			sql='CREATE TABLE IF NOT EXISTS color_codes (name VARCHAR(50) UNIQUE\
				 ,code VARCHAR(50))'
			self.cursor.execute(sql)
			self.dbcheck=True

			dprint('creating sqlite table color_codes in astrodb')

		#default values for colors (if dbcheck)
		self.defaultColors = {
			"paper_0":"#000000",
			"paper_1":"#ffffff",
			"zodiac_bg_0":"#482900",
			"zodiac_bg_1":"#6b3d00",
			"zodiac_bg_2":"#5995e7",
			"zodiac_bg_3":"#2b4972",
			"zodiac_bg_4":"#c54100",
			"zodiac_bg_5":"#2b286f",
			"zodiac_bg_6":"#69acf1",
			"zodiac_bg_7":"#ffd237",
			"zodiac_bg_8":"#ff7200",
			"zodiac_bg_9":"#863c00",
			"zodiac_bg_10":"#4f0377",
			"zodiac_bg_11":"#6cbfff",
			"zodiac_icon_0":"#482900",
			"zodiac_icon_1":"#6b3d00",
			"zodiac_icon_2":"#5995e7",
			"zodiac_icon_3":"#2b4972",
			"zodiac_icon_4":"#c54100",
			"zodiac_icon_5":"#2b286f",
			"zodiac_icon_6":"#69acf1",
			"zodiac_icon_7":"#ffd237",
			"zodiac_icon_8":"#ff7200",
			"zodiac_icon_9":"#863c00",
			"zodiac_icon_10":"#4f0377",
			"zodiac_icon_11":"#6cbfff",
			"zodiac_radix_ring_0":"#ff0000",
			"zodiac_radix_ring_1":"#ff0000",
			"zodiac_radix_ring_2":"#ff0000",
			"zodiac_transit_ring_0":"#ff0000",
			"zodiac_transit_ring_1":"#ff0000",
			"zodiac_transit_ring_2":"#0000ff",
			"zodiac_transit_ring_3":"#0000ff",
			"houses_radix_line":"#ff0000",
			"houses_transit_line":"#0000ff",
			"aspect_0":"#5757e2",
			"aspect_30":"#810757",
			"aspect_45":"#b14e58",
			"aspect_60":"#d59e28",
			"aspect_72":"#1f99b3",
			"aspect_90":"#dc0000",
			"aspect_120":"#36d100",
			"aspect_135":"#985a10",
			"aspect_144":"#7a9810",
			"aspect_150":"#fff600",
			"aspect_180":"#510060",
			"planet_0":"#984b00",
			"planet_1":"#150052",
			"planet_2":"#520800",
			"planet_3":"#400052",
			"planet_4":"#540000",
			"planet_5":"#47133d",
			"planet_6":"#124500",
			"planet_7":"#6f0766",
			"planet_8":"#06537f",
			"planet_9":"#713f04",
			"planet_10":"#4c1541",
			"planet_11":"#4c1541",
			"planet_12":"#331820",
			"planet_13":"#585858",
			"planet_14":"#000000",
			"planet_15":"#666f06",
			"planet_16":"#000000",
			"planet_17":"#000000",
			"planet_18":"#000000",
			"planet_19":"#000000",
			"planet_20":"#000000",
			"planet_21":"#000000",
			"planet_22":"#000000",
			"planet_23":"#ff7e00",
			"planet_24":"#FF0000",
			"planet_25":"#0000FF",
			"planet_26":"#000000",
			"planet_27":"#000000",
			"planet_28":"#000000",
			"planet_29":"#000000",
			"planet_30":"#000000",
			"planet_31":"#000000",
			"planet_32":"#000000",
			"planet_33":"#000000",
			"planet_34":"#000000",
			"lunar_phase_0":"#000000",
			"lunar_phase_1":"#FFFFFF",
			"lunar_phase_2":"#CCCCCC"
		}
		if self.dbcheck:
			dprint('dbcheck astrodb.color_codes')
			#insert values
			for k,v in self.defaultColors.items():
				sql='INSERT OR %s INTO color_codes \
				(name, code)\
				VALUES("%s","%s")' % ( self.dbpurge , k, v )
				self.cursor.execute(sql)
		#check for label table in astrodb
		if 'label' not in self.tables:
			sql='CREATE TABLE IF NOT EXISTS label (name VARCHAR(150) UNIQUE\
				 ,value VARCHAR(200))'
			self.cursor.execute(sql)
			self.dbcheck=True

			dprint('creating sqlite table label in astrodb')

		#default values for label (if dbcheck)
		self.defaultLabels = {
			"cusp":_("Cusp"),
			"longitude":_("Longitude"),
			"latitude":_("Latitude"),
			"north":_("North"),
			"east":_("East"),
			"south":_("South"),
			"west":_("West"),
			"apparent_geocentric":_("Apparent Geocentric"),
			"true_geocentric":_("True Geocentric"),
			"topocentric":_("Topocentric"),
			"heliocentric":_("Heliocentric"),
			"fire":_("Fire"),
			"earth":_("Earth (element)"),
			"air":_("Air"),
			"water":_("Water"),
			"radix":_("Radix"),
			"transit":_("Transit"),
			"synastry":_("Synastry"),
			"composite":_("Composite"),
			"combine":_("Combine"),
			"solar":_("Solar"),
			"secondary_progressions":_("Secondary Progressions")
		}
		if self.dbcheck:
			dprint('dbcheck astrodb.label')
			#insert values
			for k,v in self.defaultLabels.items():
				sql='INSERT OR %s INTO label \
				(name, value)\
				VALUES("%s","%s")' % ( self.dbpurge , k, v )
				self.cursor.execute(sql)
		#check for settings_planet table in astrodb
		self.table_settings_planet={
				"id":"INTEGER UNIQUE",
				"name":"VARCHAR(50)",
				"color":"VARCHAR(50)",
				"visible":"INTEGER",
				"element_points":"INTEGER",
				"zodiac_relation":"VARCHAR(50)",
				"label":"VARCHAR(50)",
				"label_short":"VARCHAR(20)",
				"visible_aspect_line":"INTEGER",
				"visible_aspect_grid":"INTEGER"
				}
		if 'settings_planet' not in self.tables:
			sql='CREATE TABLE IF NOT EXISTS settings_planet (id INTEGER UNIQUE, name VARCHAR(50)\
				,color VARCHAR(50),visible INTEGER, element_points INTEGER, zodiac_relation VARCHAR(50)\
			 	,label VARCHAR(50), label_short VARCHAR(20), visible_aspect_line INTEGER\
			 	,visible_aspect_grid INTEGER)'
			self.cursor.execute(sql)
			self.dbcheck = True

			dprint('creating sqlite table settings_planet in astrodb')

		#default values for settings_planet (if dbcheck)
		if self.dbcheck:
			dprint('dbcheck astrodb.settings_planet')
			self.value_settings_planet={}
			self.value_settings_planet['name'] = [
			'sun','moon','mercury','venus','mars','jupiter','saturn',
			'uranus','neptune','pluto','mean node','true node','mean apogee','osc. apogee',
			'earth','chiron','pholus','ceres','pallas','juno','vesta',
			'intp. apogee','intp. perigee','Asc','Mc','Dsc','Ic','day pars',
			'night pars','south node', 'marriage pars', 'black sun', 'vulcanus', 'persephone',
			'true lilith']
			orb = [
			#sun
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#moon
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#mercury
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#venus
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#mars
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#jupiter
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#saturn
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#uranus
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#neptunus
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}',
			#pluto
			'{0:10,180:10,90:10,120:10,60:6,30:3,150:3,45:3,135:3,72:1,144:1}'
			]
			self.value_settings_planet['label'] = [
				_('Sun'),_('Moon'), _('Mercury'),_('Venus'), _('Mars'),
				_('Jupiter'), _('Saturn'), _('Uranus'), _('Neptune'),
				_('Pluto'), _('North Node'),_('True Node'), _('Lilith'), _('Osc. Lilith'),
				_('Earth'), _('Chiron'), _('Pholus'), _('Ceres'), _('Pallas'),
				_('Juno'),_('Vesta'), _('Intp. Lilith'), _('Intp. Perigee'),
				_('Asc'), _('Mc'), _('Dsc'), _('Ic'), _('Day Pars'),
				_('Night Pars'),_('South Node'),_('Marriage Pars'),
				_('Black Sun'), _('Vulcanus'), _('Persephone'),_('True Lilith')
			]
			self.value_settings_planet['label_short'] = [
			'sun','moon','mercury','venus','mars','jupiter','saturn',
			'uranus','neptune','pluto','Node','?','Lilith','?',
			'earth','chiron','pholus','ceres','pallas','juno','vesta',
			'intp. apogee','intp. perigee','Asc','Mc','Dsc','Ic','DP',
			'NP','SNode','marriage','blacksun','vulcanus','persephone','truelilith']
			self.value_settings_planet['color'] = [
			'#984b00','#150052','#520800','#400052','#540000','#47133d','#124500',
			'#6f0766','#06537f','#713f04','#4c1541','#4c1541','#33182','#000000',
			'#000000','#666f06','#000000','#000000','#000000','#000000','#000000',
			'#000000','#000000','orange','#FF0000','#0000FF','#000000','#000000',
			'#000000','#000000','#000000','#000000','#000000','#000000','#000000']
			self.value_settings_planet['visible'] = PLANET_DEFAULT_VISIBLE[:]
			self.value_settings_planet['visible_aspect_line'] = PLANET_DEFAULT_VISIBLE[:]
			self.value_settings_planet['visible_aspect_grid'] = PLANET_DEFAULT_VISIBLE[:]
			self.value_settings_planet['element_points'] = [
			40,40,15,15,15,10,10,
			10,10,10,20,0,0,0,
			0,5,0,0,0,0,0,
			0,0,40,20,0,0,0,
			0,0,0,0,0,0,0]
			#zodiac relation gives 10 extra points in element calculation
			self.value_settings_planet['zodiac_relation'] = [
			'4','3','2,5','1,6','0','8','9',
			'10','11','7','-1','-1','-1','-1',
			'-1','-1','-1','-1','-1','-1','-1',
			'-1','-1','-1','-1','-1','-1','-1',
			'-1','-1','-1','-1','-1','-1','-1']
			#if update, check if everything is in order with settings_planet
			sql='PRAGMA table_info(settings_planet)'
			self.cursor.execute(sql)
			list=self.cursor.fetchall()
			vacuum = False
			cnames=[]
			for i in range(len(list)):
				cnames.append(list[i][1])
			for key,val in self.table_settings_planet.items():
				if key not in cnames:
					sql = 'ALTER TABLE settings_planet ADD %s %s'%(key,val)
					dprint("dbcheck astrodb.settings_planet adding %s %s"%(key,val))
					self.cursor.execute(sql)
					#update values for col
					self.cursor.execute("SELECT id FROM settings_planet ORDER BY id DESC LIMIT 1")
					c = self.cursor.fetchone()[0]+1
					for rowid in range(c):
						sql = 'UPDATE settings_planet SET %s=? WHERE id=?' %(key)
						self.cursor.execute(sql,(self.value_settings_planet[key][rowid],rowid))
					vacuum = True
			if vacuum:
				sql = "VACUUM"
				self.cursor.execute(sql)
			#insert values for planets that don't exists
			for i in range(len(self.value_settings_planet['name'])):
				sql='INSERT OR %s INTO settings_planet VALUES(?,?,?,?,?,?,?,?,?,?)'%(self.dbpurge)
				values=(i,
						self.value_settings_planet['name'][i],
						self.value_settings_planet['color'][i],
						self.value_settings_planet['visible'][i],
						self.value_settings_planet['element_points'][i],
						self.value_settings_planet['zodiac_relation'][i],
						self.value_settings_planet['label'][i],
						self.value_settings_planet['label_short'][i],
						self.value_settings_planet['visible_aspect_line'][i],
						self.value_settings_planet['visible_aspect_grid'][i]
				)
				self.cursor.execute(sql,values)
		#bodies of transit and synastry charts, radix side (visible) and transit or
		#partner side (visible_transit); radix stays in settings_planet, which is
		#shared with the Gtk3 programs; new rows take the radix visibility on every
		#start, asc based points are hidden as transits
		sql='CREATE TABLE IF NOT EXISTS settings_planet_chart (chart_type VARCHAR(16) NOT NULL\
			 ,id INTEGER NOT NULL, visible INTEGER, visible_transit INTEGER\
			 ,PRIMARY KEY (chart_type, id))'
		self.cursor.execute(sql)
		for ctype in ASPECT_CHART_TYPES:
			if ctype == 'radix':
				continue
			hidden = PLANET_TRANSIT_HIDDEN if ctype == 'transit' else ()
			sql='INSERT OR %s INTO settings_planet_chart (chart_type, id, visible, visible_transit)\
				SELECT ?, id, visible, CASE WHEN id IN (%s) THEN 0 ELSE visible END FROM settings_planet' % (
				self.dbpurge, ','.join(str(i) for i in hidden) or 'NULL')
			self.cursor.execute(sql, (ctype,))
		#commit initial changes
		self.updateHistory()
		self.link.commit()
		self.plink.commit()
		self.close()

	""" still class OpenAstroSqlite """
	def setLanguage(self, lang=None):

		if lang==None or lang=="default":
			TRANSLATION["default"].install()
			dprint("installing default language")
		else:
			TRANSLATION[lang].install()
			dprint("installing language (%s)"%(lang))
		return

	def addHistory(self):
		self.open()
		sql = 'INSERT INTO history  (id,name,year,month,day,hour,geolon,geolat,altitude,location,timezone,countrycode) VALUES (null,?,?,?,?,?,?,?,?,?,?,?)'
		tuple = (app.name, app.year, app.month, app.day, app.hour, app.geolon, app.geolat, app.altitude, app.location, app.timezone, app.countrycode)
		self.cursor.execute(sql,tuple)
		self.link.commit()
		self.updateHistory()
		self.close()

	def getAstrocfg(self,key):
		self.open()
		sql='SELECT value FROM astrocfg WHERE name="%s"' % key
		self.cursor.execute(sql)
		one=self.cursor.fetchone()
		self.close()
		if one == None:
			return None
		else:
			return one[0]

	def setAstrocfg(self,key,val):
		sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES (?,?)'
		self.query([sql],[(key,val)])
		self.astrocfg[key] = val
		return

	def getColors(self):
		self.open()
		sql='SELECT * FROM color_codes'
		self.cursor.execute(sql)
		list=self.cursor.fetchall()
		out={}
		for i in range(len(list)):
			out[list[i][0]] = list[i][1]
		self.close()
		return out

	def getLabel(self):
		self.open()
		sql='SELECT * FROM label'
		self.cursor.execute(sql)
		rows = self.cursor.fetchall()
		#convert row list into dictionary
		labels = {}
		for row in rows:
			labels[row[0]] = row[1]
		self.close()
		#update values for label
		label_labels = {
			"cusp":_("Cusp"),
			"longitude":_("Longitude"),
			"latitude":_("Latitude"),
			"north":_("North"),
			"east":_("East"),
			"south":_("South"),
			"west":_("West"),
			"apparent_geocentric":_("Apparent Geocentric"),
			"true_geocentric":_("True Geocentric"),
			"topocentric":_("Topocentric"),
			"heliocentric":_("Heliocentric"),
			"fire":_("Fire"),
			"earth":_("Earth (element)"),
			"air":_("Air"),
			"water":_("Water"),
			"radix":_("Radix"),
			"transit":_("Transit"),
			"synastry":_("Synastry"),
			"composite":_("Composite"),
			"combine":_("Combine"),
			"solar":_("Solar"),
			"secondary_progressions":_("Secondary Progressions")
		}
		for i, key in enumerate(labels.keys()):
			labels[key] = label_labels[key]
		return labels
	"""
	def getLabel(self):
		self.open()
		sql='SELECT * FROM label'
		self.cursor.execute(sql)
		list=self.cursor.fetchall()
		out={}
		for i in range(len(list)):
			out[list[i][0]] = list[i][1]
		self.close()
		return out
	"""
	def getDatabase(self):
		self.open()
		sql = 'SELECT * FROM event_natal ORDER BY id ASC'
		self.pcursor.execute(sql)
		records = []
		for row in self.pcursor:
			s = {}
			for key,val in self.ptable_event_natal.items():
				if row[key] == None:
					s[key] = ""
				else:
					s[key] = row[key]
			records.append(s)
		self.close()
		return records

	def getSettingsPlanet(self, chart_type='radix'):
		"""
		list of all bodies (dictionary per settings_planet row), chart_type is one
		of ASPECT_CHART_TYPES: 'visible' shows the body of the chart (radix side of
		transit and synastry charts), 'visible_transit' the transit or partner body;
		transit and synastry take both from settings_planet_chart
		"""
		self.open()
		sql = 'SELECT * FROM settings_planet ORDER BY id ASC'
		self.cursor.execute(sql)
		#planets is a list if a dictionary for every planet
		planets = []
		for row in self.cursor:
			s = {}
			for key, val in self.table_settings_planet.items():
				s[key] = row[key]
			planets.append(s)
		chart_rows = {}
		if chart_type in ASPECT_CHART_TYPES and chart_type != 'radix':
			try:
				sql = 'SELECT id, visible, visible_transit FROM settings_planet_chart WHERE chart_type=?'
				self.cursor.execute(sql, (chart_type,))
				for row in self.cursor:
					chart_rows[row['id']] = row
			except sqlite3.OperationalError:
				dprint('getSettingsPlanet: no table settings_planet_chart, using radix')
		self.close()
		for planet in planets:
			radix = aspectFlag(planet['visible'], 0)
			if chart_type in ASPECT_CHART_TYPES and chart_type != 'radix':
				transit = radix
				if chart_type == 'transit' and planet['id'] in PLANET_TRANSIT_HIDDEN:
					transit = 0
				row = chart_rows.get(planet['id'])
				if row is not None:
					planet['visible'] = aspectFlag(row['visible'], radix)
					planet['visible_transit'] = aspectFlag(row['visible_transit'], transit)
				else:
					planet['visible'] = radix
					planet['visible_transit'] = transit
			else:
				planet['visible_transit'] = radix
		planet_labels = [
			_('Sun'),_('Moon'), _('Mercury'),_('Venus'), _('Mars'),
			_('Jupiter'), _('Saturn'), _('Uranus'), _('Neptune'),
			_('Pluto'), _('North Node'),_('True Node'), _('Lilith'), _('Osc. Lilith'),
			_('Earth'), _('Chiron'), _('Pholus'), _('Ceres'), _('Pallas'),
			_('Juno'),_('Vesta'), _('Intp. Lilith'), _('Intp. Perigee'),
			_('Asc'), _('Mc'), _('Dsc'), _('Ic'), _('Day Pars'),
			_('Night Pars'),_('South Node'),_('Marriage Pars'),
			_('Black Sun'), _('Vulcanus'), _('Persephone'),_('True Lilith')
		]
		#planets is a list if dictionaries for every planet
		for i, planet in enumerate(planets):
			planet['label'] = planet_labels[i]
		return planets

	def setSettingsPlanet(self, chart_type, planets):
		"""
		save the visibility of bodies (list of dicts with id), radix into
		settings_planet (visible, visible_aspect_line, visible_aspect_grid like the
		Gtk3 planet settings), transit and synastry into settings_planet_chart
		(visible, visible_transit)
		"""
		sql = []
		values = []
		for planet in planets:
			if chart_type == 'radix':
				sql.append('UPDATE settings_planet SET visible=?, visible_aspect_line=?, visible_aspect_grid=? WHERE id=?')
				values.append((1 if planet['visible'] else 0, 1 if planet['visible_aspect_line'] else 0,
					1 if planet['visible_aspect_grid'] else 0, planet['id']))
			elif chart_type in ASPECT_CHART_TYPES:
				sql.append('INSERT OR REPLACE INTO settings_planet_chart (chart_type, id, visible, visible_transit) VALUES(?,?,?,?)')
				values.append((chart_type, planet['id'], 1 if planet['visible'] else 0, 1 if planet['visible_transit'] else 0))
		if sql:
			self.query(sql, values)

	def getSettingsAspect(self, chart_type='radix'):
		"""
		list of all aspects in the order of ASPECT_DEGREES (never filtered,
		hidden aspects have visible/visible_grid 0), chart_type is one of
		ASPECT_CHART_TYPES: radix from settings_aspect, transit and synastry
		take visible, visible_grid and orb from settings_aspect_chart
		"""
		if chart_type not in ASPECT_CHART_TYPES:
			chart_type = 'radix'
		self.open()
		sql = 'SELECT * FROM settings_aspect ORDER BY degree ASC'
		self.cursor.execute(sql)
		rows = {}
		for row in self.cursor:
			#degree, name, color, visible, visible_grid, is_major, is_minor, orb
			rows[row['degree']] = row
		chart_rows = {}
		if chart_type != 'radix':
			try:
				sql = 'SELECT degree, visible, visible_grid, orb FROM settings_aspect_chart WHERE chart_type=?'
				self.cursor.execute(sql, (chart_type,))
				for row in self.cursor:
					chart_rows[row['degree']] = row
			except sqlite3.OperationalError:
				dprint('getSettingsAspect: no table settings_aspect_chart, using defaults')
		self.close()
		aspect_labels = self.getAspectLabels()
		default = ASPECT_DEFAULTS[chart_type]
		aspects = []
		for i, degree in enumerate(ASPECT_DEGREES):
			row = rows.get(degree)
			if chart_type == 'radix':
				values = row
			else:
				values = chart_rows.get(degree)
			aspects.append({'degree':degree, 'name':aspect_labels[i]
			,'color':row['color'] if row is not None else None
			,'visible':aspectFlag(values['visible'] if values is not None else None, default['visible'][i])
			,'visible_grid':aspectFlag(values['visible_grid'] if values is not None else None, default['visible_grid'][i])
			,'is_major':aspectFlag(row['is_major'] if row is not None else None, ASPECT_IS_MAJOR[i])
			,'is_minor':aspectFlag(row['is_minor'] if row is not None else None, ASPECT_IS_MINOR[i])
			,'orb':aspectOrb(values['orb'] if values is not None else None, default['orb'][i])})
		return aspects

	def getAspectLabels(self):
		#translated aspect names in the order of ASPECT_DEGREES
		return [
			_('conjunction'), _('semi-sextile'), _('semi-square'),
			_('sextile'), _('quintile') , _('square'),
			_('trine'), _('sesquiquadrate'), _('biquintile'),
			_('quincunx') , _('opposition')
		]

	def setSettingsAspect(self, chart_type, aspects):
		"""
		save visible, visible_grid and orb of aspects (list of dicts with degree),
		radix into settings_aspect (orb as text like the Gtk3 programs, name is
		never written), transit and synastry into settings_aspect_chart
		"""
		sql = []
		values = []
		labels = self.getAspectLabels()
		for aspect in aspects:
			visible = 1 if aspect['visible'] else 0
			visible_grid = 1 if aspect['visible_grid'] else 0
			orb = float(aspect['orb'])
			if chart_type == 'radix':
				if orb == int(orb):
					orb = str(int(orb))
				else:
					orb = str(orb)
				#a missing row gets the defaults first, else the update would be lost
				i = ASPECT_DEGREES.index(aspect['degree'])
				default = ASPECT_DEFAULTS['radix']
				sql.append('INSERT OR IGNORE INTO settings_aspect (degree, name, color, visible, visible_grid, is_major, is_minor, orb) VALUES(?,?,?,?,?,?,?,?)')
				values.append((aspect['degree'], labels[i], ASPECT_COLORS[i], default['visible'][i], default['visible_grid'][i],
					ASPECT_IS_MAJOR[i], ASPECT_IS_MINOR[i], str(default['orb'][i])))
				sql.append('UPDATE settings_aspect SET visible=?, visible_grid=?, orb=? WHERE degree=?')
				values.append((visible, visible_grid, orb, aspect['degree']))
			elif chart_type in ASPECT_CHART_TYPES:
				sql.append('INSERT OR REPLACE INTO settings_aspect_chart (chart_type, degree, visible, visible_grid, orb) VALUES(?,?,?,?,?)')
				values.append((chart_type, aspect['degree'], visible, visible_grid, orb))
		if sql:
			self.query(sql, values)

	def getSettingsLocation(self):
		#look if location is known
		if 'home_location' not in self.astrocfg or 'home_timezonestr' not in self.astrocfg:
			self.open()
			sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES("home_location","")'
			self.cursor.execute(sql)
			sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES("home_geolat","")'
			self.cursor.execute(sql)
			sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES("home_geolon","")'
			self.cursor.execute(sql)
			sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES("home_countrycode","")'
			self.cursor.execute(sql)
			sql='INSERT OR REPLACE INTO astrocfg (name,value) VALUES("home_timezonestr","")'
			self.cursor.execute(sql)
			self.link.commit()
			self.close
			return '','','','',''
		else:
			return self.astrocfg['home_location'],self.astrocfg['home_geolat'],self.astrocfg['home_geolon'],self.astrocfg['home_countrycode'],self.astrocfg['home_timezonestr']

	def setSettingsLocation(self, lat, lon, loc, cc, tzstr):
		self.open()
		sql = 'UPDATE astrocfg SET value="%s" WHERE name="home_location"' % loc
		self.cursor.execute(sql)
		sql = 'UPDATE astrocfg SET value="%s" WHERE name="home_geolat"' % lat
		self.cursor.execute(sql)
		sql = 'UPDATE astrocfg SET value="%s" WHERE name="home_geolon"' % lon
		self.cursor.execute(sql)
		sql = 'UPDATE astrocfg SET value="%s" WHERE name="home_countrycode"' % cc
		self.cursor.execute(sql)
		sql = 'UPDATE astrocfg SET value="%s" WHERE name="home_timezonestr"' % tzstr
		self.cursor.execute(sql)
		self.link.commit()
		self.close()

	def updateHistory(self):
		sql='SELECT * FROM history'
		self.cursor.execute(sql)
		self.history = self.cursor.fetchall()
		#check if limit is exceeded
		limit=LIMIT
		if len(self.history) > limit:
			sql = "DELETE FROM history WHERE id < '"+str(self.history[len(self.history)-limit][0])+"'"
			self.cursor.execute(sql)
			self.link.commit()
			#update self.history
			sql = 'SELECT * FROM history'
			self.cursor.execute(sql)
			self.history = self.cursor.fetchall()
		return

	""" Function to import zet8 databases """
	def importZet8(self, target_db, data):

		target_con = sqlite3.connect(target_db)
		target_con.row_factory = sqlite3.Row
		target_cur = target_con.cursor()

		#get target names
		target_names={}
		sql='SELECT name FROM event_natal'
		target_cur.execute(sql)
		for row in target_cur:
			target_names[row['name']]=1
		for k,v in target_names.items():
			for i in range(1,10):
				if '%s (#%s)' % (k,i) in target_names:
					target_names[k] += 1

		#read input write target
		for row in data:

			if row['name'] in target_names:
				name_suffix = ' (#%s)' % target_names[row['name']]
				target_names[row['name']] += 1
			else:
				name_suffix = ''

			gname = self.gnearest( float(row['latitude']),float(row['longitude']) )

			sql = 'INSERT INTO event_natal (id,name,year,month,day,hour,geolon,geolat,altitude,\
				location,timezone,notes,image,countrycode,geonameid,timezonestr,extra) VALUES \
				(null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
			tuple = (row['name']+name_suffix,row['year'],row['month'],row['day'],row['hour'],row['longitude'],
				row['latitude'],25,row['location'],row['timezone'],"",
				"",gname['geonameid'],gname['timezonestr'],"")
			target_cur.execute(sql,tuple)

		#Finished, close connection
		target_con.commit()
		target_cur.close()
		target_con.close()
		return

	"""
	Function to merge two databases containing entries for persons
	databaseMerge(target_db,input_db)

	database format:
	'CREATE TABLE IF NOT EXISTS event_natal (id INTEGER PRIMARY KEY,name VARCHAR(50),\
	 year VARCHAR(4),month VARCHAR(2), day VARCHAR(2), hour VARCHAR(50), geolon VARCHAR(50),\
	 geolat VARCHAR(50), altitude VARCHAR(50), location VARCHAR(150), timezone VARCHAR(50),\
	 notes VARCHAR(500), image VARCHAR(250), countrycode VARCHAR(2), geonameid INTEGER,\
	 timezonestr VARCHAR(100), extra VARCHAR(250))'
	"""
	def databaseMerge(self,target_db,input_db):
		dprint('db.databaseMerge: %s << %s'%(target_db,input_db))
		target_con = sqlite3.connect(target_db)
		target_con.row_factory = sqlite3.Row
		target_cur = target_con.cursor()
		input_con = sqlite3.connect(input_db)
		input_con.row_factory = sqlite3.Row
		input_cur = input_con.cursor()
		#get target names
		target_names={}
		sql='SELECT name FROM event_natal'
		target_cur.execute(sql)
		for row in target_cur:
			target_names[row['name']]=1
		for k,v in target_names.items():
			for i in range(1,10):
				if '%s (#%s)'% (k,i) in target_names:
					target_names[k] += 1

		#read input write target
		sql='SELECT * FROM event_natal'
		input_cur.execute(sql)
		for row in input_cur:
			if row['name'] in target_names:
				name_suffix = ' (#%s)' % target_names[row['name']]
				target_names[row['name']] += 1
			else:
				name_suffix = ''
			sql = 'INSERT INTO event_natal (id,name,year,month,day,hour,geolon,geolat,altitude,\
				location,timezone,notes,image,countrycode,geonameid,timezonestr,extra) VALUES \
				(null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
			tuple = (row['name']+name_suffix,row['year'],row['month'],row['day'],row['hour'],row['geolon'],
				row['geolat'],row['altitude'],row['location'],row['timezone'],row['notes'],
				row['image'],row['countrycode'],row['geonameid'],row['timezonestr'],row['extra'])
			target_cur.execute(sql,tuple)

		#Finished, close connection
		target_con.commit()
		target_cur.close()
		target_con.close()
		input_cur.close()
		input_con.close()
		return

	""" Basic Query Functions for common databases 	"""
	def query(self, sql, tuple=None):
		l=sqlite3.connect(app.cfg.astrodb)
		c=l.cursor()
		for i in range(len(sql)):
			if tuple == None:
				c.execute(sql[i])
			else:
				c.execute(sql[i],tuple[i])
		l.commit()
		c.close()
		l.close()

	def pquery(self, sql, tuple=None):
		l=sqlite3.connect(app.cfg.peopledb)
		c=l.cursor()
		for i in range(len(sql)):
			if tuple == None:
				c.execute(sql[i])
			else:
				c.execute(sql[i],tuple[i])
		l.commit()
		c.close()
		l.close()

	def gnearest(self, lat=None, lon=None):
		#check for none
		if lat==None or lon==None:
			return {'country':None,'admin1':None,'geonameid':None,'continent':None,'timezonestr':None}
		#get closest value to lat lon
		dprint('gnearest: using %s,%s' %(lat,lon))
		diff = {}
		sql = 'SELECT id,latitude,longitude FROM geonames WHERE latitude >= %s AND latitude <= %s AND longitude >= %s AND longitude <= %s' % (lat-0.5,lat+0.5,lon-0.5,lon+0.5)
		self.gquery(sql)
		for row in self.gcursor:
			diff[zonetab.distance( lat , lon , row['latitude'] , row['longitude'])]=row['id']
		self.gclose()
		keys=list(diff.keys())
		keys.sort()
 
		dict={}
		if keys == []:
			dict = {'country':None,'admin1':None,'geonameid':None,'continent':None,'timezonestr':None}
			dprint('gnearest: no town found within 66km range!')
		else:
			sql = 'SELECT * FROM geonames WHERE id=%s LIMIT 1' % (diff[keys[0]])
			self.gquery(sql)
			geoname = self.gcursor.fetchone()
			self.gclose()
			dict['country']=geoname['country']
			dict['admin1']=geoname['admin1']
			dict['geonameid']=geoname['geonameid']
			dict['timezonestr']=geoname['timezone']
			sql = 'SELECT * FROM countryinfo WHERE isoalpha2="%s" LIMIT 1' % (geoname['country'])
			self.gquery(sql) 
			countryinfo = self.gcursor.fetchone()
			dict['continent']=countryinfo['continent']
			self.gclose()
			dprint('gnearest: found town %s at %s,%s,%s' % (geoname['name'],geoname['latitude'],
				geoname['longitude'],geoname['timezone']))
		return dict

	def gquery(self, sql, tuple=None):
		self.glink = sqlite3.connect(app.cfg.geonamesdb)
		self.glink.row_factory = sqlite3.Row
		self.gcursor = self.glink.cursor()
		if tuple:
			self.gcursor.execute(sql,tuple)
		else:
			self.gcursor.execute(sql)

	def gclose(self):
		self.glink.commit()
		self.gcursor.close()
		self.glink.close()

	def open(self):
		self.link = sqlite3.connect(app.cfg.astrodb)
		self.link.row_factory = sqlite3.Row
		self.cursor = self.link.cursor()

		self.plink = sqlite3.connect(app.cfg.peopledb)
		self.plink.row_factory = sqlite3.Row
		self.pcursor = self.plink.cursor()

	def close(self):
		self.cursor.close()
		self.pcursor.close()
		self.link.close()
		self.plink.close()

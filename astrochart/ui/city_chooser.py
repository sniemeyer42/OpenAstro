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
Location input: online geocoding check and the city chooser of the geonames
database (continent, country, province, city drop downs, city search)
"""

import socket
from gi.repository import Gtk
from astrochart.util import dprint

def geocodingAvailable(db):
	"""True if online geocoding is enabled and api.geonames.org can be reached"""
	if db.getAstrocfg('use_geonames.org') == "0":
		dprint('iconn: not using geocoding!')
		return False
	HOST='api.geonames.org'
	PORT=80
	try:
		addresses = socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM)
	except OSError:
		dprint('iconn: no connection (getaddrinfo)')
		return False
	for af, socktype, proto, canonname, sa in addresses:
		try:
			s = socket.socket(af, socktype, proto)
		except OSError:
			continue
		s.settimeout(2)
		try:
			s.connect(sa)
		except OSError:
			s.close()
			continue
		s.close()
		dprint('iconn: got connection')
		return True
	dprint('iconn: no connection')
	return False

class CityChooser:
	"""
	drop downs continent, country, province and city of the geonames
	database, preselected with the place nearest to (geolat, geolon);
	the chosen city is in self.city (lat, lon, loc, cc, geonameid, tzstr)
	and is passed to on_city whenever it changes
	"""

	def __init__(self, db, geolat, geolon, on_city):
		self.db = db
		self.on_city = on_city
		self.city = None
		# get nearest geoname
		self.GEON_nearest = self.db.gnearest(geolat, geolon)
		# continents
		self.continents = Gtk.DropDown()
		sql = 'SELECT * FROM continent ORDER BY name ASC'
		self.db.gquery(sql)
		self.continent_infos = []
		continent_info = Gtk.StringList()
		self.searchcontinent = {}
		self.activecont = 3
		for i, row in enumerate(self.db.gcursor):
			self.searchcontinent[row['code']] = i
			if row['code'] == self.GEON_nearest['continent']:
				self.activecont = i
				self.GEON_nearest['continent'] = None
			items = [row['name'], row['code']]
			self.continent_infos.append(items)
			continent_info.append(row['name'])
		self.db.gclose()
		self.continents.set_model(model=continent_info)
		# countries
		self.countries = Gtk.DropDown()
		self.countries.connect('notify::selected-item', self.changedCountry)
		# provinces
		self.provinces = Gtk.DropDown()
		self.provinces.connect('notify::selected-item', self.changedProvince)
		# cities
		self.cities = Gtk.DropDown()
		self.cities.set_enable_search(True)
		expr = Gtk.PropertyExpression.new(Gtk.StringObject(), None, 'string')
		self.cities.set_expression(expression=expr)
		self.cities.connect('notify::selected-item', self.changedCity)
		# CAVEAT: changedContinent relies on the other drop downs
		self.continents.connect('notify::selected-item', self.changedContinent)

	def start(self):
		"""select the nearest place, fills the drop downs one after the other"""
		self.continents.set_selected(self.activecont)

	def search(self, text):
		"""select the first city of the database matching 'city[, country]'"""
		city = text
		#look for country in search string
		isoalpha2 = None
		if city.find(","):
			split = city.split(",")
			for x in range(len(split)):
				sql = "SELECT * FROM countryinfo WHERE (isoalpha2 LIKE ? OR name LIKE ?) LIMIT 1"
				y = split[x].strip()
				self.db.gquery(sql,(y,y))
				result = self.db.gcursor.fetchone()
				if result != None:
					isoalpha2 = result["isoalpha2"]
					city = city.replace(split[x]+",","").replace(","+split[x],"").strip()
					break
		#normal search
		normal = city
		fuzzy = "%"+city+"%"
		if isoalpha2:
			extra = " AND country='%s'"%(isoalpha2)
		else:
			extra = ""
		sql = "SELECT * FROM geonames WHERE (name LIKE ? OR asciiname LIKE ?)%s LIMIT 1" %(extra)
		self.db.gquery(sql,(normal,normal))
		result = self.db.gcursor.fetchone()
		if result == None:
			sql = "SELECT * FROM geonames WHERE (name LIKE ? OR asciiname LIKE ?)%s LIMIT 1" %(extra)
			self.db.gquery(sql,(fuzzy,fuzzy))
			result = self.db.gcursor.fetchone()
		if result == None:
			sql = "SELECT * FROM geonames WHERE (alternatenames LIKE ?)%s LIMIT 1"%(extra)
			self.db.gquery(sql,(fuzzy,))
			result = self.db.gcursor.fetchone()
		if result != None:
			#set continent
			sql = "SELECT continent FROM countryinfo WHERE isoalpha2=? LIMIT 1"
			self.db.gquery(sql,(result["country"],))
			self.continents.set_selected(self.searchcontinent[self.db.gcursor.fetchone()[0]])
			#set country
			self.countries.set_selected(self.searchcountry[result["country"]])
			#set admin1
			self.provinces.set_selected(self.searchprov[result["admin1"]])
			#set city
			self.cities.set_selected(self.searchcity[result["geonameid"]])
		return

	def changedContinent(self, dropdown, _pspec):
		index = dropdown.get_selected()
		info = self.continent_infos[index]
		sql = "SELECT * FROM countryinfo WHERE continent=? ORDER BY name ASC"
		self.db.gquery(sql,(info[1],))
		country_info = Gtk.StringList()
		self.country_infos = []
		activecountry=0
		self.searchcountry={}
		for i, row in enumerate(self.db.gcursor):
			self.searchcountry[row['isoalpha2']]=i
			if self.GEON_nearest['country'] == row['isoalpha2']:
				activecountry=i
				self.GEON_nearest['country'] = None
			items = [row['name'],row['isoalpha2']]
			self.country_infos.append(items)
			country_info.append(row['name'])
		self.db.gclose()
		self.countries.set_model(country_info)
		self.countries.set_selected(activecountry)
		return

	def changedCountry(self, dropdown, _pspec):
		index = dropdown.get_selected()
		info = self.country_infos[index]
		sql = "SELECT * FROM admin1codes WHERE country=? ORDER BY admin1 ASC"
		self.db.gquery(sql,(info[1],))
		self.province_infos = []
		province_info = Gtk.StringList()
		activeprov = 0
		self.searchprov={}
		for i, row in enumerate(self.db.gcursor):
			self.searchprov[row["admin1"]] = i
			if self.GEON_nearest['admin1'] == row['admin1']:
				activeprov = i
				self.GEON_nearest['admin1'] = None
			items = [row['province'],row['country'],row['admin1'],info[0]]
			self.province_infos.append(items)
			province_info.append(row['province'])
		self.db.gclose()
		self.provinces.set_model(province_info)
		self.provinces.set_selected(activeprov)
		return

	def changedProvince(self, dropdown, _pspec):
		index = dropdown.get_selected()
		info = self.province_infos[index]
		sql = 'SELECT * FROM geonames WHERE country=? AND admin1=? ORDER BY name ASC'
		self.db.gquery(sql,(info[1],info[2]))
		self.city_infos = []
		city_info = Gtk.StringList()
		activecity = 0
		self.searchcity = {}
		for i, row in enumerate(self.db.gcursor):
			self.searchcity[row["geonameid"]]=i
			if self.GEON_nearest['geonameid'] == row['geonameid']:
				activecity = i
				self.GEON_nearest['geonameid'] = None
			items = [row['name'], str(row['latitude']), str(row['longitude']), info[3], info[0], row['country'], str(row['geonameid']), row['timezone']]
			self.city_infos.append(items)
			city_info.append(row['name'])
		self.db.gclose()
		self.cities.set_model(city_info)
		self.cities.set_selected(activecity)
		return

	def changedCity(self, dropdown, _pspec):
		index = dropdown.get_selected()
		info = self.city_infos[index]
		self.city = {
			'lat': info[1],
			'lon': info[2],
			'loc': '%s, %s, %s' % (info[0],info[4],info[3]),
			'cc': info[5],
			'geonameid': info[6],
			'tzstr': info[7]}
		dprint('CityChooser: %(loc)s:%(lat)s:%(lon)s:%(cc)s:%(tzstr)s:%(geonameid)s' % self.city)
		self.on_city(self.city)

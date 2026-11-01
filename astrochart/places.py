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
Places: online geocoding check and the geonames database (continents,
countries, provinces, cities, search by name)
"""

import socket
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

class Geonames:
	"""continents, countries, provinces and cities of the geonames database"""

	def __init__(self, db):
		self.db = db

	def rows(self, sql, args=()):
		self.db.gquery(sql, tuple(args) or None)
		rows = self.db.gcursor.fetchall()
		self.db.gclose()
		return rows

	def continents(self):
		"""(name, code) of the continents"""
		return [(row['name'], row['code']) for row in self.rows('SELECT * FROM continent ORDER BY name ASC')]

	def countries(self, continent):
		"""(name, iso code) of the countries of a continent"""
		return [(row['name'], row['isoalpha2']) for row in
			self.rows('SELECT * FROM countryinfo WHERE continent=? ORDER BY name ASC', (continent,))]

	def provinces(self, country):
		"""(name, admin1 code) of the provinces of a country"""
		return [(row['province'], row['admin1']) for row in
			self.rows('SELECT * FROM admin1codes WHERE country=? ORDER BY admin1 ASC', (country,))]

	def cities(self, country, admin1):
		"""geonames rows of the cities of a province"""
		return self.rows('SELECT * FROM geonames WHERE country=? AND admin1=? ORDER BY name ASC', (country, admin1))

	def continentOf(self, country):
		rows = self.rows('SELECT continent FROM countryinfo WHERE isoalpha2=? LIMIT 1', (country,))
		return rows[0][0] if rows else None

	def search(self, text):
		"""
		first city matching 'city[, country]' (country as name or iso code):
		dict continent, country, admin1, geonameid; None if there is none
		"""
		parts = [part.strip() for part in text.split(',')]
		country = None
		if len(parts) > 1:
			for i, part in enumerate(parts):
				rows = self.rows('SELECT * FROM countryinfo WHERE (isoalpha2 LIKE ? OR name LIKE ?) LIMIT 1', (part, part))
				if rows:
					country = rows[0]['isoalpha2']
					del parts[i]
					break
		city = ', '.join(part for part in parts if part)
		if not city:
			return None
		extra, args = ('', ()) if country is None else (' AND country=?', (country,))
		fuzzy = '%' + city + '%'
		result = None
		for sql, values in (
			('SELECT * FROM geonames WHERE (name LIKE ? OR asciiname LIKE ?)%s LIMIT 1', (city, city)),
			('SELECT * FROM geonames WHERE (name LIKE ? OR asciiname LIKE ?)%s LIMIT 1', (fuzzy, fuzzy)),
			('SELECT * FROM geonames WHERE (alternatenames LIKE ?)%s LIMIT 1', (fuzzy,))):
			rows = self.rows(sql % extra, values + args)
			if rows:
				result = rows[0]
				break
		if result is None:
			return None
		return {'continent': self.continentOf(result['country']), 'country': result['country'],
			'admin1': result['admin1'], 'geonameid': result['geonameid']}

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
Location input: the place by online geocoding (city and country code) or
chosen in the geonames database (continent, country, province, city, search)
"""

from PySide6.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLineEdit, QPushButton, QWidget
from openastromod import geoname
from astrochart.places import Geonames
from astrochart.qt.dialog import SearchEdit
from astrochart.util import dprint

class CityChooser(QWidget):
	"""
	drop downs continent, country, province and city of the geonames
	database, preselected with the place nearest to (geolat, geolon); the
	chosen city is in self.city (lat, lon, loc, cc, geonameid, tzstr) and is
	passed to on_city whenever it changes
	"""

	def __init__(self, db, geolat, geolon, on_city, search=True):
		super().__init__()
		self.geonames = Geonames(db)
		self.on_city = on_city
		self.city = None
		form = QFormLayout(self)
		form.setContentsMargins(0, 0, 0, 0)
		self.continents = QComboBox()
		self.countries = QComboBox()
		self.provinces = QComboBox()
		self.cities = QComboBox()
		for combo in (self.continents, self.countries, self.provinces, self.cities):
			combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
			combo.setMinimumContentsLength(16)
		form.addRow(_('Continent'), self.continents)
		form.addRow(_('Country'), self.countries)
		form.addRow(_('Province'), self.provinces)
		form.addRow(_('City'), self.cities)
		if search:
			#search 'city[, country]' in the database
			row = QHBoxLayout()
			self.searchEdit = SearchEdit()
			self.searchEdit.setPlaceholderText(_("For example: London, GB"))
			self.searchEdit.setClearButtonEnabled(True)
			self.searchEdit.returnPressed.connect(lambda: self.search(self.searchEdit.text()))
			row.addWidget(self.searchEdit, 1)
			button = QPushButton(_("Search"))
			button.setAutoDefault(False)
			button.clicked.connect(lambda: self.search(self.searchEdit.text()))
			row.addWidget(button)
			form.addRow(_("Search City"), row)
		#user changes fill the drop downs below
		self.continents.currentIndexChanged.connect(lambda index: self.fillCountries())
		self.countries.currentIndexChanged.connect(lambda index: self.fillProvinces())
		self.provinces.currentIndexChanged.connect(lambda index: self.fillCities())
		self.cities.currentIndexChanged.connect(lambda index: self.cityChanged())
		#the place nearest to the coordinates
		nearest = db.gnearest(geolat, geolon)
		self.select(nearest['continent'], nearest['country'], nearest['admin1'], nearest['geonameid'])

	@staticmethod
	def setItems(combo, items, wanted):
		"""items (text, data) into combo, select the item of data wanted (else the first)"""
		combo.blockSignals(True)
		combo.clear()
		active = 0
		for i, (text, data) in enumerate(items):
			combo.addItem(str(text), data)
			if data == wanted:
				active = i
		combo.setCurrentIndex(active if items else -1)
		combo.blockSignals(False)

	def select(self, continent, country=None, admin1=None, geonameid=None):
		"""select a place, missing parts take the first entry of their drop down"""
		continents = self.geonames.continents()
		if continent is None and continents:
			#no place known: Europe as before
			continent = continents[min(3, len(continents) - 1)][1]
		self.setItems(self.continents, continents, continent)
		self.fillCountries(country, admin1, geonameid)

	def fillCountries(self, country=None, admin1=None, geonameid=None):
		self.setItems(self.countries, self.geonames.countries(self.continents.currentData()), country)
		self.fillProvinces(admin1, geonameid)

	def fillProvinces(self, admin1=None, geonameid=None):
		self.countryName = self.countries.currentText()
		self.setItems(self.provinces, self.geonames.provinces(self.countries.currentData()), admin1)
		self.fillCities(geonameid)

	def fillCities(self, geonameid=None):
		province = self.provinces.currentText()
		cities = []
		for row in self.geonames.cities(self.countries.currentData(), self.provinces.currentData()):
			cities.append((row['name'], {
				'lat': str(row['latitude']),
				'lon': str(row['longitude']),
				'loc': '%s, %s, %s' % (row['name'], province, self.countryName),
				'cc': row['country'],
				'geonameid': str(row['geonameid']),
				'tzstr': row['timezone']}))
		wanted = None
		for text, city in cities:
			if geonameid is not None and city['geonameid'] == str(geonameid):
				wanted = city
		self.setItems(self.cities, cities, wanted)
		self.cityChanged()

	def cityChanged(self):
		city = self.cities.currentData()
		if city is None or city == self.city:
			return
		self.city = city
		dprint('CityChooser: %(loc)s:%(lat)s:%(lon)s:%(cc)s:%(tzstr)s:%(geonameid)s' % city)
		self.on_city(city)

	def search(self, text):
		"""select the first city of the database matching 'city[, country]'"""
		found = self.geonames.search(text)
		if found is not None:
			self.select(found['continent'], found['country'], found['admin1'], found['geonameid'])
		return found

class OnlinePlace(QWidget):
	"""city and country code, looked up by online geocoding (api.geonames.org)"""

	def __init__(self, city, countrycode):
		super().__init__()
		form = QFormLayout(self)
		form.setContentsMargins(0, 0, 0, 0)
		self.geoLoc = QLineEdit(city)
		self.geoCC = QLineEdit(countrycode)
		self.geoCC.setMaxLength(8)
		form.addRow(_("City"), self.geoLoc)
		form.addRow(_("Country-code"), self.geoCC)

	def lookup(self):
		"""city found online: dict lat, lon, loc, cc, geonameid, tzstr; None if not found"""
		result = geoname.search(self.geoLoc.text(), self.geoCC.text())
		if not result:
			dprint('geocoding: %s,%s not found' % (self.geoLoc.text(), self.geoCC.text()))
			return None
		found = result[0]
		city = {'lat': float(found['lat']), 'lon': float(found['lng']), 'geonameid': int(found['geonameId']),
			'cc': found['countryCode'], 'tzstr': found['timezonestr'],
			'loc': '%s, %s' % (found['name'], found['countryName'])}
		dprint('geocoding: %s,%s found; %s %s %s' % (self.geoLoc.text(), self.geoCC.text(), city['lat'], city['lon'], city['loc']))
		return city

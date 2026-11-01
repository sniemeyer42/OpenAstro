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
Data of a calculated chart for lists and tables: positions of the bodies,
house cusps, aspects and elements (call after makeSVG, makeWheelSVG or
templateData, which calculate the chart)
"""

def formatDegree(value, seconds=True):
	"""degrees within the sign as 12°34′56″ (or 12°35′)"""
	value = float(value)
	degrees = int(value)
	minutes_float = (value - degrees) * 60.0
	if not seconds:
		minutes = int(round(minutes_float))
		if minutes == 60:
			degrees, minutes = degrees + 1, 0
		return '%02d°%02d′' % (degrees, minutes)
	minutes = int(minutes_float)
	secs = int(round((minutes_float - minutes) * 60.0))
	if secs == 60:
		minutes, secs = minutes + 1, 0
	if minutes == 60:
		degrees, minutes = degrees + 1, 0
	return '%02d°%02d′%02d″' % (degrees, minutes, secs)

def houseOf(longitude, cusps):
	"""number (1-12) of the house of longitude between the 12 cusps"""
	for i in range(12):
		start = cusps[i]
		end = cusps[(i + 1) % 12]
		if (longitude - start) % 360.0 < (end - start) % 360.0:
			return i + 1
	return 12

class ChartDataMixin:
	"""lists of the calculated chart"""

	def bodyRows(self, transit=False):
		"""
		shown bodies of the radix (or the transit / partner side): id, symbol,
		label, longitude, sign, degree in sign, retrograde, radix house
		"""
		rows = []
		if transit and self.type != "Transit":
			return rows
		for i, planet in enumerate(self.planets):
			if transit:
				if planet['visible_transit'] != 1:
					continue
				longitude = self.t_planets_degree_ut[i]
				sign = self.t_planets_sign[i]
				degree = self.t_planets_degree[i]
				retrograde = self.t_planets_retrograde[i]
			else:
				if planet['visible'] != 1:
					continue
				longitude = self.planets_degree_ut[i]
				sign = self.planets_sign[i]
				degree = self.planets_degree[i]
				retrograde = self.planets_retrograde[i]
			rows.append({'id': i, 'symbol': self.svgSafeHref(planet['name']), 'label': planet['label'],
				'longitude': longitude, 'sign': self.zodiac[sign], 'degree': formatDegree(degree),
				'retrograde': bool(retrograde) and i < 23, 'house': houseOf(longitude, self.houses_degree_ut)})
		return rows

	def houseRows(self):
		"""house cusps: number, longitude, sign, degree in sign"""
		return [{'house': i + 1, 'longitude': self.houses_degree_ut[i], 'sign': self.zodiac[self.houses_sign[i]],
			'degree': formatDegree(self.houses_degree[i])} for i in range(12)]

	def aspectRows(self):
		"""
		aspects of the aspect list or grid sorted by orb: bodies (id, symbol,
		label), transit or partner side of the second body, aspect, orb;
		radix charts use the grid settings of bodies and aspects
		"""
		rows = []
		def body(i, side):
			planet = self.planets[i]
			return {'id': i, 'symbol': self.svgSafeHref(planet['name']), 'label': planet['label'], 'transit': side}
		def aspect(z, diff):
			a = self.aspects[z]
			return {'degree': a['degree'], 'name': a['name'], 'orb': abs(diff - a['degree'])}
		if self.type == "Transit":
			for item in getattr(self, 'atgrid', []):
				rows.append(dict(aspect(item['aid'], item['diff']), first=body(item['p1'], False), second=body(item['p2'], True)))
		else:
			for i in range(len(self.planets)):
				if self.planets[i]['visible_aspect_grid'] != 1:
					continue
				for x in range(i):
					if self.planets[x]['visible_aspect_grid'] != 1:
						continue
					diff = float(self.degreeDiff(self.planets_degree_ut[i], self.planets_degree_ut[x]))
					z = self.matchAspect(diff)
					if z is not None and self.aspects[z]['visible_grid'] == 1:
						rows.append(dict(aspect(z, diff), first=body(i, False), second=body(x, False)))
		rows.sort(key=lambda row: row['orb'])
		return rows

	def elementRows(self):
		"""fire, earth, air and water in percent (as on the chart page)"""
		total = self.fire + self.earth + self.air + self.water
		if total <= 0:
			total = 1.0
		return [(key, self.label[key], int(round(100 * value / total))) for key, value in
			(('fire', self.fire), ('earth', self.earth), ('air', self.air), ('water', self.water))]

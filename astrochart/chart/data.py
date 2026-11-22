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
house cusps, aspects and elements (call after templateData or makeWheelSVG,
which calculate the chart and draw the wheel: element points and transit
aspects are collected while drawing)
"""

from astrochart.constants import PLANET_SHORT_TRANSIT

#groups of the transits by their duration, in the order they are listed
TRANSIT_DURATIONS = ('short', 'long')

def transitDuration(ident):
	"""'short' if the transits of body ident are short-term, else 'long'"""
	return 'short' if ident in PLANET_SHORT_TRANSIT else 'long'

def durationTitle(duration):
	"""heading of the transits of a duration ('short' or 'long')"""
	return _('Short-term') if duration == 'short' else _('Long-term')

def formatDegree(value, seconds=True):
	"""degrees within the sign as 12°34′56″ (or 12°35′)"""
	value = float(value)
	sign = '-' if value < 0 else ''
	value = abs(value)
	degrees = int(value)
	minutes_float = (value - degrees) * 60.0
	if not seconds:
		minutes = int(round(minutes_float))
		if minutes == 60:
			degrees, minutes = degrees + 1, 0
		return '%s%02d°%02d′' % (sign, degrees, minutes)
	minutes = int(minutes_float)
	secs = int(round((minutes_float - minutes) * 60.0))
	if secs == 60:
		minutes, secs = minutes + 1, 0
	if minutes == 60:
		degrees, minutes = degrees + 1, 0
	return '%s%02d°%02d′%02d″' % (sign, degrees, minutes, secs)

def signedAspectOrb(start, end, degree, start_speed, end_speed):
	"""Orb with a minus when the distance from exactness is increasing.

	Longitudes wrap at 360 degrees; speeds are signed degrees per day.
	A transit uses zero speed for the fixed radix position.
	"""
	distance = (end - start + 180.0) % 360.0 - 180.0
	deviation = abs(distance) - degree
	change = (end_speed - start_speed) * (1 if distance >= 0 else -1)
	orb = abs(deviation)
	return -orb if deviation * change > 0 else orb

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
		aspects of the aspect list or grid sorted by absolute orb: bodies (id,
		symbol, label, transit or partner side), aspect, signed orb (negative
		when separating); transits are read
		'transit body - aspect - radix body', so the transit body comes
		first, synastries name the radix body first; radix charts use the
		grid settings of bodies and aspects
		"""
		rows = []
		def body(i, side):
			planet = self.planets[i]
			return {'id': i, 'symbol': self.svgSafeHref(planet['name']), 'label': planet['label'], 'transit': side}
		def aspect(z, i, x, transit=False):
			a = self.aspects[z]
			start_speed = self.planets_speed[i] if not transit or self.synastry else 0.0
			end = self.t_planets_degree_ut[x] if transit else self.planets_degree_ut[x]
			end_speed = self.t_planets_speed[x] if transit else self.planets_speed[x]
			return {'degree': a['degree'], 'name': a['name'], 'orb': signedAspectOrb(
				self.planets_degree_ut[i], end, a['degree'], start_speed, end_speed)}
		if self.type == "Transit":
			for item in getattr(self, 'atgrid', []):
				radix, other = body(item['p1'], False), body(item['p2'], True)
				if self.synastry:
					rows.append(dict(aspect(item['aid'], item['p1'], item['p2'], True), first=radix, second=other))
				else:
					rows.append(dict(aspect(item['aid'], item['p1'], item['p2'], True), first=other, second=radix))
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
						rows.append(dict(aspect(z, i, x), first=body(i, False), second=body(x, False)))
		rows.sort(key=lambda row: abs(row['orb']))
		return rows

	def groupsTransits(self):
		"""
		True if the aspects are transits listed by their duration: ordinary
		transits, not synastries and solar returns, whose second side does not
		move on
		"""
		return self.type == "Transit" and not self.synastry and not self.solar_return

	def aspectGroups(self, rows):
		"""
		aspect rows in groups (duration, rows), the order of the rows kept:
		transits by the transit body, 'short' (sun, moon, mercury, venus,
		mars, ...) before 'long' (jupiter and slower, nodes, lilith, ...),
		groups without rows left out; aspects of other charts are one group
		(None, rows)
		"""
		if not self.groupsTransits():
			return [(None, rows)]
		groups = []
		for duration in TRANSIT_DURATIONS:
			members = [row for row in rows if transitDuration(
				(row['first'] if row['first']['transit'] else row['second'])['id']) == duration]
			if members:
				groups.append((duration, members))
		return groups

	def elementRows(self):
		"""fire, earth, air and water in percent (as on the chart page)"""
		total = self.fire + self.earth + self.air + self.water
		if total <= 0:
			total = 1.0
		return [(key, self.label[key], int(round(100 * value / total))) for key, value in
			(('fire', self.fire), ('earth', self.earth), ('air', self.air), ('water', self.water))]

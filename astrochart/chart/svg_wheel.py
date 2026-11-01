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
Modern chart wheel: a zodiac band tinted by the elements with a fine degree
scale, houses as thin lines numbered around the aspect circle, the axes with
their labels, body symbols in one colour with degree and minute (spread
apart where they crowd), aspect lines coloured by their character and the
stronger the closer. Transits and partners get a ring outside the zodiac.

Same coordinates as the classic wheel (centre at RADIUS, RADIUS) for the
interactive view; colours are CSS classes, a light and a dark palette.
"""

import math
from xml.sax.saxutils import escape
from astrochart.constants import MODERN_ELEMENT_COLORS as ELEMENT_COLORS, RADIUS, WHEEL_MARGIN
from astrochart.chart.svg_print import FONT

#rings (radius in wheel units): radix chart and chart with a second ring
#degree, minute and retrograde mark are stacked inwards far enough apart
#that their texts do not touch where the radius runs horizontally
LAYOUT_RADIX = {'zodiac_out': 228, 'zodiac_in': 198, 'glyph': 176, 'glyph_size': 20, 'degree': 156,
	'minute': 141, 'house': 120, 'hub': 110, 'axis_end': 234, 'label': 243}
LAYOUT_RINGS = {'outer': 246, 'outer_glyph': 220, 'outer_glyph_size': 16, 'outer_degree': 236,
	'zodiac_out': 200, 'zodiac_in': 174, 'glyph': 154, 'glyph_size': 18, 'degree': 135, 'minute': 121,
	'house': 102, 'hub': 92, 'axis_end': 248, 'label': 253}

ELEMENTS = ('fire', 'earth', 'air', 'water')
#character of the aspects: colour class and major (solid) or minor (dashed)
ASPECT_KIND = {0: 'conj', 30: 'green', 45: 'hard', 60: 'soft', 72: 'purple', 90: 'hard',
	120: 'soft', 135: 'hard', 144: 'purple', 150: 'green', 180: 'hard'}
MAJOR = (0, 60, 90, 120, 180)
ASPECT_COLORS = {'conj': '#b7791f', 'hard': '#d1242f', 'soft': '#1f6feb', 'green': '#1a7f37', 'purple': '#8250df'}
ANGLE_LABELS = {23: 'AC', 24: 'MC', 25: 'DC', 26: 'IC'}

PALETTES = {
	False: {'ink': '#1d1d20', 'muted': '#6b6b73', 'paper': 'fill: #ffffff;', 'hub': 'fill: #f5f6f8;',
		'line': '#c9c9cf', 'tick': '#9b9ba3', 'band': .11, 'aspects': ASPECT_COLORS},
	True: {'ink': '#e4e4e7', 'muted': '#a0a0a8', 'paper': 'fill: none;', 'hub': 'fill: #ffffff; fill-opacity: .04;',
		'line': '#505057', 'tick': '#7c7c85', 'band': .14,
		'aspects': {'conj': '#f2c94c', 'hard': '#ff6b6b', 'soft': '#5aa9ff', 'green': '#4cc96a', 'purple': '#b799ff'}},
}

def css(dark):
	"""style sheet of the wheel"""
	p = PALETTES[bool(dark)]
	rules = [
		'.w-chart { color: %s; }' % p['ink'],
		'.w-paper { %s }' % p['paper'],
		'.w-hub { %s stroke: %s; stroke-width: .8; }' % (p['hub'], p['line']),
		'.w-line { fill: none; stroke: %s; stroke-width: .7; }' % p['line'],
		'.w-tick { stroke: %s; stroke-width: .6; }' % p['tick'],
		'.w-link { stroke: %s; stroke-width: .6; fill: none; }' % p['tick'],
		'.w-axis { stroke: %s; stroke-width: 1.4; }' % p['ink'],
		'.w-ink { fill: %s; }' % p['ink'],
		'.w-muted { fill: %s; }' % p['muted'],
		'.w-dot { fill: %s; }' % p['ink'],
		'.w-retrograde { fill: %s; }' % p['aspects']['hard'],
		'.w-ring { fill: none; stroke: %s; stroke-opacity: %.2f; }' % (p['muted'], p['band'] / 2.0),
	]
	for element in ELEMENTS:
		rules.append('.w-%s { fill: %s; fill-opacity: %.2f; }' % (element, ELEMENT_COLORS[element], p['band']))
	for kind, color in p['aspects'].items():
		rules.append('.w-a-%s { stroke: %s; fill: none; }' % (kind, color))
	return '\n'.join(rules)

def spread(points, separation):
	"""
	display longitudes of points {key: longitude}: at least separation
	degrees apart and as close to their own longitude as possible
	"""
	if not points:
		return {}
	n = len(points)
	separation = min(separation, 360.0 / n)
	items = sorted(points.items(), key=lambda item: item[1] % 360.0)
	lons = [lon % 360.0 for key, lon in items]
	#begin after the widest gap, no cluster crosses it
	gaps = [(lons[(j + 1) % n] - lons[j]) % 360.0 if n > 1 else 360.0 for j in range(n)]
	start = (max(range(n), key=lambda j: gaps[j]) + 1) % n
	order = items[start:] + items[:start]
	base = order[0][1] % 360.0
	unwrapped = [base + ((lon - base) % 360.0) for key, lon in order]
	def place(cluster):
		centre = sum(unwrapped[j] for j in cluster) / len(cluster)
		return [centre + (m - (len(cluster) - 1) / 2.0) * separation for m in range(len(cluster))]
	clusters = [[j] for j in range(n)]
	merged = True
	while merged:
		merged = False
		k = 0
		while k < len(clusters) - 1:
			if place(clusters[k + 1])[0] - place(clusters[k])[-1] < separation - 1e-9:
				clusters[k] += clusters.pop(k + 1)
				merged = True
			else:
				k += 1
	result = {}
	for cluster in clusters:
		for j, lon in zip(cluster, place(cluster)):
			result[order[j][0]] = lon % 360.0
	return result

def separationOf(size, radius):
	"""angle in degrees taken by a symbol of size at radius"""
	return math.degrees(size * 1.08 / radius)

def text(x, y, content, cls, size, anchor='middle', weight='normal'):
	return '<text x="%.2f" y="%.2f" class="%s" style="font-size: %.1fpx; text-anchor: %s; font-weight: %s;">%s</text>\n' % (
		x, y, cls, size, anchor, weight, escape(str(content)))

def use(name, cx, cy, size, box=24.0):
	"""symbol of the definitions centred at cx, cy"""
	return '<g transform="translate(%.2f,%.2f) scale(%.4f)"><use xlink:href="#%s"/></g>\n' % (
		cx - size / 2.0, cy - size / 2.0, size / box, name)

def line(p, q, cls, style=''):
	return '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" class="%s"%s/>\n' % (
		p[0], p[1], q[0], q[1], cls, ' style="%s"' % style if style else '')

class ModernWheelMixin:
	"""modern chart wheel, parts in the template data of templateData()"""

	def modernStyle(self):
		"""True for the modern wheel (default), False for the classic one"""
		return self.db.astrocfg.get('chartstyle', 'modern') == 'modern'

	def aspectColor(self, degree):
		"""colour of an aspect: by its character (modern) or of the colour settings (classic)"""
		if self.modernStyle():
			return ASPECT_COLORS[ASPECT_KIND.get(degree, 'green')]
		return self.colors["aspect_%s" % (degree)]

	def chartSymbols(self):
		"""symbol definitions in the colours of the chart style"""
		return self.symbolDefinitions(self.modernColorData() if self.modernStyle() else None)

	def wheelLayout(self):
		return LAYOUT_RINGS if self.type == "Transit" else LAYOUT_RADIX

	def point(self, lon, r):
		"""wheel coordinates of longitude lon at radius r, the ascendant on the left"""
		a = math.radians(lon - self.planets_degree_ut[23] - 180.0)
		return (RADIUS + r * math.cos(a), RADIUS - r * math.sin(a))

	def modernColorData(self):
		"""colours of the symbol definitions: bodies in the colour of the text, signs by element"""
		td = {'paper_color_0': 'currentColor', 'paper_color_1': '#ffffff'}
		for i in range(len(self.planets)):
			td['planets_color_%s' % (i)] = 'currentColor'
		for i in range(12):
			td['zodiac_color_%s' % (i)] = ELEMENT_COLORS[self.zodiac_element[i]]
		for degree, kind in ASPECT_KIND.items():
			td['orb_color_%s' % (degree)] = ASPECT_COLORS[kind]
		return td

	def modernTemplateData(self):
		"""parts of the modern wheel of the calculated chart"""
		L = self.wheelLayout()
		self.glyphs = []
		td = {'style': 'modern'}
		td['zodiac'] = self.modernZodiac(L)
		td['houses'] = self.modernHouses(L)
		td['bodies'] = self.modernBodies(L)
		td['axes'] = self.modernAxes(L)
		td['aspects'] = self.modernAspects(L)
		td['highlight'] = self.makeHighlight() if self.highlight is not None else ''
		return td

	def modernZodiac(self, L):
		out = ['<circle cx="%s" cy="%s" r="%s" class="w-paper"/>\n' % (RADIUS, RADIUS, RADIUS + WHEEL_MARGIN)]
		if 'outer' in L:
			#faint ring of the transit or partner bodies
			width = L['outer'] - L['zodiac_out']
			out.append('<circle cx="%s" cy="%s" r="%s" class="w-ring" style="stroke-width: %s;"/>\n' % (
				RADIUS, RADIUS, L['zodiac_out'] + width / 2.0, width))
		r1, r2 = L['zodiac_in'], L['zodiac_out']
		for k in range(12):
			a1, a2 = self.point(k * 30, r2), self.point(k * 30 + 30, r2)
			b1, b2 = self.point(k * 30 + 30, r1), self.point(k * 30, r1)
			out.append('<path d="M%.2f,%.2f A%s,%s 0 0,0 %.2f,%.2f L%.2f,%.2f A%s,%s 0 0,1 %.2f,%.2f Z" class="w-%s"/>\n' % (
				a1[0], a1[1], r2, r2, a2[0], a2[1], b1[0], b1[1], r1, r1, b2[0], b2[1], self.zodiac_element[k]))
			out.append(line(self.point(k * 30, r1), self.point(k * 30, r2), 'w-line'))
			size = (r2 - r1) * 0.62
			out.append(use(self.zodiac[k], *self.point(k * 30 + 15, (r1 + r2) / 2.0), size, 32.0))
		for r in (r1, r2):
			out.append('<circle cx="%s" cy="%s" r="%s" class="w-line"/>\n' % (RADIUS, RADIUS, r))
		#degree scale on the inside of the band: 1, 5 and 10 degrees
		for d in range(360):
			length = 6.0 if d % 10 == 0 else (4.0 if d % 5 == 0 else 2.0)
			out.append(line(self.point(d, r1), self.point(d, r1 - length), 'w-tick'))
		return ''.join(out)

	def modernHouses(self, L):
		out = []
		cusps = self.houses_degree_ut[:36 if self.db.astrocfg['houses_system'] == "G" else 12]
		n = len(cusps)
		size = 9.0 if n == 12 else 6.5
		for i, cusp in enumerate(cusps):
			out.append(line(self.point(cusp, L['hub']), self.point(cusp, L['zodiac_in']), 'w-line'))
			#number in the middle of the house, next to the aspect circle
			span = (cusps[(i + 1) % n] - cusp) % 360.0
			if span > 180.0:
				span -= 360.0
			x, y = self.point(cusp + span / 2.0, L['house'])
			out.append(text(x, y + size * 0.35, i + 1, 'w-muted', size))
		return ''.join(out)

	def modernAxes(self, L):
		"""axes ascendant - descendant and midheaven - imum coeli with their labels"""
		out = []
		for i in (23, 24, 25, 26):
			lon = self.planets_degree_ut[i]
			out.append(line(self.point(lon, L['hub']), self.point(lon, L['axis_end']), 'w-axis'))
			if self.planets[i]['visible'] != 1:
				continue
			x, y = self.point(lon, L['label'])
			degree = self.planets_degree[i]
			out.append(text(x, y + 1, ANGLE_LABELS[i], 'w-ink', 10.5, weight='bold'))
			out.append(text(x, y + 10.5, '%d°%02d′' % (int(degree), int((degree - int(degree)) * 60)), 'w-muted', 7.5))
			self.glyphs.append({'side': 'radix', 'id': i, 'x': x, 'y': y - 2, 'r': 9})
		return ''.join(out)

	def modernBodies(self, L):
		out = []
		#radix bodies inside the zodiac, the angles are the axes
		shown = [i for i in range(len(self.planets)) if self.planets[i]['visible'] == 1 and not 23 <= i <= 26]
		lons = dict((i, self.planets_degree_ut[i]) for i in shown)
		places = spread(lons, separationOf(L['glyph_size'], L['glyph']))
		for i in shown:
			lon, place = lons[i], places[i]
			out.append(line(self.point(lon, L['zodiac_in']), self.point(lon, L['zodiac_in'] - 6), 'w-axis', 'stroke-width: 1;'))
			out.append(line(self.point(lon, L['zodiac_in'] - 6), self.point(place, L['glyph'] + L['glyph_size'] / 2.0 + 1), 'w-link'))
			x, y = self.point(place, L['glyph'])
			out.append(use(self.svgSafeHref(self.planets[i]['name']), x, y, L['glyph_size']))
			self.glyphs.append({'side': 'radix', 'id': i, 'x': x, 'y': y, 'r': L['glyph_size'] / 2.0})
			degree = self.planets_degree[i]
			x, y = self.point(place, L['degree'])
			out.append(text(x, y + 3.2, '%d°' % int(degree), 'w-ink', 9))
			#minutes, retrograde mark after them
			x, y = self.point(place, L['minute'])
			mark = '<tspan class="w-retrograde">℞</tspan>' if self.planets_retrograde[i] else ''
			out.append('<text x="%.2f" y="%.2f" class="w-muted" style="font-size: 7.5px; text-anchor: middle;">%02d′%s</text>\n' % (
				x + (2.5 if mark else 0), y + 2.6, int((degree - int(degree)) * 60), mark))
		if 'outer' not in L:
			return ''.join(out)
		#transit or partner bodies outside the zodiac
		shown = [i for i in range(len(self.planets)) if self.planets[i]['visible_transit'] == 1]
		lons = dict((i, self.t_planets_degree_ut[i]) for i in shown)
		places = spread(lons, separationOf(L['outer_glyph_size'], L['outer_glyph']))
		for i in shown:
			lon, place = lons[i], places[i]
			out.append(line(self.point(lon, L['zodiac_out']), self.point(lon, L['zodiac_out'] + 5), 'w-axis', 'stroke-width: 1;'))
			out.append(line(self.point(lon, L['zodiac_out'] + 5), self.point(place, L['outer_glyph'] - L['outer_glyph_size'] / 2.0 - 1), 'w-link'))
			x, y = self.point(place, L['outer_glyph'])
			if i in ANGLE_LABELS:
				out.append(text(x, y + 3.5, ANGLE_LABELS[i], 'w-ink', 9.5, weight='bold'))
			else:
				out.append(use(self.svgSafeHref(self.planets[i]['name']), x, y, L['outer_glyph_size']))
			self.glyphs.append({'side': 'transit', 'id': i, 'x': x, 'y': y, 'r': L['outer_glyph_size'] / 2.0})
			x, y = self.point(place, L['outer_degree'])
			mark = '<tspan class="w-retrograde">℞</tspan>' if self.t_planets_retrograde[i] else ''
			out.append('<text x="%.2f" y="%.2f" class="w-muted" style="font-size: 7.5px; text-anchor: middle;">%d°%s</text>\n' % (
				x + (2.5 if mark else 0), y + 2.6, int(self.t_planets_degree[i]), mark))
		return ''.join(out)

	def modernAspects(self, L):
		"""aspect lines across the aspect circle, dots at the radix bodies"""
		r = L['hub']
		out = ['<circle cx="%s" cy="%s" r="%s" class="w-hub"/>\n' % (RADIUS, RADIUS, r)]
		def draw(lon_a, lon_b, z, emphasis):
			aspect = self.aspects[z]
			if aspect['degree'] == 0:
				return
			orb = abs(float(self.degreeDiff(lon_a, lon_b)) - aspect['degree'])
			close = 1.0 - min(1.0, orb / aspect['orb']) if aspect['orb'] > 0 else 1.0
			major = aspect['degree'] in MAJOR
			width = (0.6 + 1.2 * close) if major else (0.5 + 0.6 * close)
			opacity = 0.35 + 0.6 * close
			if emphasis is True:
				width, opacity = 2.4, 1.0
			elif emphasis is False:
				opacity = 0.07
			style = 'stroke-width: %.2f; stroke-opacity: %.2f;' % (width, opacity)
			if not major:
				style += ' stroke-dasharray: 3,2.5;'
			out.append(line(self.point(lon_a, r), self.point(lon_b, r), 'w-a-%s' % ASPECT_KIND.get(aspect['degree'], 'green'), style))
		if self.type == "Transit":
			for pair in self.transitAspectPairs():
				i, x, z = pair['p1'], pair['p2'], pair['aid']
				if self.aspects[z]['visible'] == 1:
					draw(self.planets_degree_ut[i], self.t_planets_degree_ut[x], z, self.emphasis('radix', i, 'transit', x))
		else:
			for i in range(len(self.planets)):
				for x in range(i):
					if self.planets[i]['visible_aspect_line'] != 1 or self.planets[x]['visible_aspect_line'] != 1:
						continue
					z = self.matchAspect(float(self.degreeDiff(self.planets_degree_ut[i], self.planets_degree_ut[x])))
					if z is not None and self.aspects[z]['visible'] == 1:
						draw(self.planets_degree_ut[i], self.planets_degree_ut[x], z, self.emphasis('radix', i, 'radix', x))
		#where the radix bodies are
		for i in range(len(self.planets)):
			if self.planets[i]['visible'] == 1:
				x, y = self.point(self.planets_degree_ut[i], r)
				out.append('<circle cx="%.2f" cy="%.2f" r="1.6" class="w-dot"/>\n' % (x, y))
		return ''.join(out)

	def makeModernWheelSVG(self, td, dark=False):
		"""modern wheel as SVG document, dark: palette for dark backgrounds"""
		extent = 2 * (RADIUS + WHEEL_MARGIN)
		return ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
			'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
			'width="%s" height="%s" viewBox="%s %s %s %s" preserveAspectRatio="xMidYMid">\n'
			'<title>OpenAstro chart</title>\n%s\n<style type="text/css">\n%s\n</style>\n'
			'<g class="w-chart" style="font-family: %s;">\n%s%s%s%s%s%s</g>\n</svg>\n') % (
			extent, extent, -WHEEL_MARGIN, -WHEEL_MARGIN, extent, extent,
			self.symbolDefinitions(self.modernColorData()), css(dark), FONT,
			td['zodiac'], td['houses'], td['aspects'], td['axes'], td['bodies'], td['highlight'])

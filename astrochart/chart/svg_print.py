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
Printed page of a chart (A4 landscape): header with the event, the wheel,
tables of positions, house cusps, elements and aspects
"""

import datetime
from xml.sax.saxutils import escape
from astrochart.chart.data import formatDegree
from astrochart.constants import HOUSE_SYSTEMS, MODERN_ELEMENT_COLORS, RADIUS, WHEEL_MARGIN

#page in units of 0.25 mm: A4 landscape 297 x 210 mm
PAGE_WIDTH = 1188
PAGE_HEIGHT = 840
MARGIN = 48
TOP = 176
WHEEL = 584
GAP = 28
COLUMN = (PAGE_WIDTH - 2 * MARGIN - WHEEL - GAP - 20) / 2.0
FONT = "Cantarell, 'DejaVu Sans', 'Liberation Sans', sans-serif"
INK = '#1d1d20'
GREY = '#6b6b70'
RULE = '#d0d0d4'
SIGNS = ('aries','taurus','gemini','cancer','leo','virgo','libra','scorpio','sagittarius','capricorn','aquarius','pisces')
ELEMENT_COLORS = {'fire': '#e66100', 'earth': '#865e3c', 'air': '#62a0ea', 'water': '#613583'}

def text(x, y, content, size=16, color=INK, weight='normal', anchor='start'):
	return '<text x="%.1f" y="%.1f" style="font-size: %.1fpx; fill: %s; font-weight: %s; text-anchor: %s;">%s</text>\n' % (
		x, y, size, color, weight, anchor, escape(str(content)))

def symbol(name, x, y, size):
	"""symbol of the chart template (drawn in a box of 24 units, signs 32, aspects 12) at x, y (top left)"""
	box = 32.0 if name in SIGNS else (12.0 if name.startswith('orb') else 24.0)
	return '<g transform="translate(%.1f,%.1f) scale(%.4f)"><use xlink:href="#%s"/></g>\n' % (x, y, size / box, name)

def rule(x1, y, x2):
	return '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" style="stroke: %s; stroke-width: 1px;"/>\n' % (x1, y, x2, y, RULE)

def shorten(name, length=15):
	return name if len(name) <= length else name[:length - 1].rstrip() + '…'

class PrintSVGMixin:
	"""printed page, uses the template data of the calculated chart"""

	def makePrintSVG(self, td=None):
		"""A4 landscape page as SVG document (calculates the chart unless td is given)"""
		if td is None:
			td = self.templateData()
		wheel = self.makeWheelSVG(td, dark=False)
		out = [self.printHeader()]
		#wheel on the left, below the header
		bottom = PAGE_HEIGHT - MARGIN
		top = TOP + (bottom - TOP - WHEEL) / 2.0
		#content of the wheel document placed by a transformed group (Qt draws
		#no nested svg elements), clipped to the wheel as the document is
		inner = wheel[wheel.index('>', wheel.index('<svg')) + 1:wheel.rindex('</svg>')]
		extent = 2 * (RADIUS + WHEEL_MARGIN)
		out.append('<defs><clipPath id="wheel-clip"><rect x="%s" y="%s" width="%s" height="%s"/></clipPath></defs>\n'
			'<g transform="translate(%s,%.1f) scale(%.6f) translate(%s,%s)" clip-path="url(#wheel-clip)">%s</g>\n' % (
			-WHEEL_MARGIN, -WHEEL_MARGIN, extent, extent,
			MARGIN, top, WHEEL / float(extent), WHEEL_MARGIN, WHEEL_MARGIN, inner))
		#two columns of tables on the right
		x1 = MARGIN + WHEEL + GAP
		x2 = x1 + COLUMN + 20
		self.printPositions(out, x1, TOP, COLUMN, bottom)
		y = self.printHouses(out, x2, TOP, COLUMN)
		y = self.printElements(out, x2, y + 14, COLUMN)
		self.printAspects(out, x2, y + 14, COLUMN, bottom)
		out.append(text(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 18, 'OpenAstro.org', 11, GREY, anchor='end'))
		return ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
			'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
			'width="297mm" height="210mm" viewBox="0 0 %s %s">\n<title>%s</title>\n'
			'<rect x="0" y="0" width="%s" height="%s" style="fill: white;"/>\n'
			'<g style="font-family: %s;">\n%s</g>\n</svg>\n') % (
			PAGE_WIDTH, PAGE_HEIGHT, escape(str(self.name)), PAGE_WIDTH, PAGE_HEIGHT, FONT, ''.join(out))

	def printHeader(self):
		cfg = self.db.astrocfg
		date = '%s-%02d-%02d %02d:%02d:%02d %s' % (self.year_loc, self.month_loc, self.day_loc,
			self.hour_loc, self.minute_loc, self.second_loc, self.decTzStr(self.timezone))
		out = text(MARGIN, MARGIN + 28, self.name, 34, weight='bold')
		out += text(MARGIN, MARGIN + 58, '%s  ·  %s' % (self.charttype, date), 17)
		out += text(MARGIN, MARGIN + 82, '%s  ·  %s  %s' % (self.location, self.lat2str(self.geolat), self.lon2str(self.geolon)), 15, GREY)
		second = self.printSecondEvent()
		if second:
			out += text(MARGIN, MARGIN + 104, second, 15, GREY)
		postype = {"geo": self.label["apparent_geocentric"], "truegeo": self.label["true_geocentric"],
			"topo": self.label["topocentric"], "helio": self.label["heliocentric"]}
		if cfg['zodiactype'] == 'sidereal':
			zodiac = '%s (%s)' % (_("Sidereal"), cfg['siderealmode'])
		else:
			zodiac = _("Tropical")
		right = PAGE_WIDTH - MARGIN
		out += text(right, MARGIN + 28, zodiac, 14, GREY, anchor='end')
		out += text(right, MARGIN + 50, HOUSE_SYSTEMS.get(cfg['houses_system'], cfg['houses_system']), 14, GREY, anchor='end')
		out += text(right, MARGIN + 72, postype.get(cfg['postype'], ''), 14, GREY, anchor='end')
		out += rule(MARGIN, MARGIN + 116, right)
		return out

	def printSecondEvent(self):
		"""partner of synastry and composite charts: name, local date, place"""
		if not (self.type == "Composite" or (self.type == "Transit" and self.synastry)):
			return ''
		h, m, s = self.decHour(self.t_hour)
		local = datetime.datetime(self.t_year, self.t_month, self.t_day, h, m, s) + datetime.timedelta(hours=float(self.t_timezone))
		return '%s:  %s  ·  %s %s  ·  %s' % (_('Partner'), self.t_name, local.strftime('%Y-%m-%d %H:%M'), self.decTzStr(self.t_timezone), self.t_location)

	def printPositions(self, out, x, y, width, bottom):
		"""positions of the radix (and of transit or partner), rows fitted to the height"""
		sides = [(_('Radix'), self.bodyRows())]
		if self.type == "Transit":
			sides.append((_('Partner') if self.synastry else _('Transit'), self.bodyRows(transit=True)))
		count = sum(len(rows) for title, rows in sides)
		headers = 26 + (len(sides) * 24 if len(sides) > 1 else 0)
		line = max(9.0, min(18.0, (bottom - y - headers) / max(1, count)))
		size = min(13.0, line * 0.74)
		out.append(text(x, y + 12, _('Positions'), 17, weight='bold'))
		y += 26
		for title, rows in sides:
			if len(sides) > 1:
				out.append(text(x, y + 14, title, 13, GREY, weight='bold'))
				y += 24
			for row in rows:
				y += line
				out.append(symbol(row['symbol'], x, y - line * 0.82, line * 0.9))
				out.append(text(x + line + 4, y, shorten(row['label']), size))
				out.append(symbol(row['sign'], x + width - 114, y - line * 0.72, line * 0.78))
				out.append(text(x + width - 34, y, row['degree'], size, anchor='end'))
				out.append(text(x + width - 31, y, '℞' if row['retrograde'] else '', size * 0.85, GREY))
				out.append(text(x + width, y, '%s' % row['house'], size * 0.85, GREY, anchor='end'))
		return y

	def printHouses(self, out, x, y, width):
		"""house cusps in two columns"""
		out.append(text(x, y + 12, _('Houses'), 17, weight='bold'))
		y += 26
		line = 17
		column = width / 2.0
		for k, row in enumerate(self.houseRows()):
			cx = x + (k // 6) * column
			cy = y + line * (k % 6 + 1)
			out.append(text(cx + 16, cy, '%s' % row['house'], 12, GREY, anchor='end'))
			out.append(symbol(row['sign'], cx + 22, cy - 12, 13))
			out.append(text(cx + 38, cy, row['degree'], 12))
		return y + line * 6

	def printElements(self, out, x, y, width):
		"""elements as bars"""
		#the modern wheel tints its zodiac band with these colours
		colors = MODERN_ELEMENT_COLORS if self.modernStyle() else ELEMENT_COLORS
		out.append(text(x, y + 12, _('Elements'), 17, weight='bold'))
		y += 26
		line = 17
		for k, (key, label, percent) in enumerate(self.elementRows()):
			cy = y + line * (k + 1)
			out.append(text(x, cy, label, 12))
			bar = width - 110
			out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="7" rx="3.5" style="fill: %s;"/>\n' % (x + 64, cy - 8, bar, RULE))
			out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="7" rx="3.5" style="fill: %s;"/>\n' % (x + 64, cy - 8, bar * percent / 100.0, colors[key]))
			out.append(text(x + width, cy, '%d%%' % percent, 12, anchor='end'))
		return y + line * 4

	def printAspects(self, out, x, y, width, bottom):
		"""aspects sorted by orb in two columns, as many as fit"""
		rows = self.aspectRows()
		line = 16
		per_column = max(0, int((bottom - y - 26) // line))
		shown = rows[:2 * per_column]
		out.append(text(x, y + 12, _('Aspects'), 17, weight='bold'))
		if len(rows) > len(shown):
			out.append(text(x + width, y + 12, '%d / %d' % (len(shown), len(rows)), 12, GREY, anchor='end'))
		y += 26
		column = width / 2.0
		for k, row in enumerate(shown):
			cx = x + (k // per_column) * column
			cy = y + line * (k % per_column + 1)
			out.append(symbol(row['first']['symbol'], cx, cy - 12, 13))
			out.append(symbol('orb%s' % row['degree'], cx + 16, cy - 10, 10))
			out.append(symbol(row['second']['symbol'], cx + 29, cy - 12, 13))
			out.append(text(cx + column - 10, cy, formatDegree(row['orb'], seconds=False), 11, GREY, anchor='end'))
		return y

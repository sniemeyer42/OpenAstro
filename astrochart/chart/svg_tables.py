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
SVG of the tables (A4 portrait pages): monthly timeline of the transits and
the aspects of the bodies to the house cusps
"""

import datetime
from xml.sax.saxutils import escape
from openastromod import swiss as ephemeris
from astrochart.chart.svg_print import FONT, INK, GREY, rule, symbol, text

#page in units of 0.25 mm: A4 portrait 210 x 297 mm, pages stacked with a gap
PAGE_WIDTH = 840
PAGE_HEIGHT = 1188
PAGE_GAP = 10
MARGIN = 36
ZEBRA = '#f4f4f6'
ACCENT = '#3584e4'

def document(pages, printing, symbols, content, title):
	"""
	SVG of pages stacked vertically; printing (pagenum, width, height) shows
	one page at the size of the printed page
	"""
	height = pages * (PAGE_HEIGHT + PAGE_GAP) - PAGE_GAP
	if printing is None:
		size = 'width="%s" height="%s" viewBox="0 0 %s %s"' % (PAGE_WIDTH, height, PAGE_WIDTH, height)
	else:
		size = 'width="%s" height="%s" viewBox="0 %s %s %s"' % (printing['width'], printing['height'],
			printing['pagenum'] * (PAGE_HEIGHT + PAGE_GAP), PAGE_WIDTH, PAGE_HEIGHT)
	paper = ''.join('<rect x="0" y="%s" width="%s" height="%s" style="fill: white;"/>\n' % (
		p * (PAGE_HEIGHT + PAGE_GAP), PAGE_WIDTH, PAGE_HEIGHT) for p in range(pages))
	return ('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
		'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" %s>\n'
		'<title>%s</title>\n%s\n%s<g style="font-family: %s;">\n%s</g>\n</svg>\n') % (
		size, escape(str(title)), symbols, paper, FONT, content)

class TablesSVGMixin:
	"""tables of the radix chart: monthly timeline and cusp aspects"""

	def tableHeader(self, top, title, subtitle, page=0, pages=1):
		"""title, subtitle, page number and footer of a table page"""
		out = text(MARGIN, top + MARGIN + 22, title, 22, weight='bold')
		out += text(MARGIN, top + MARGIN + 44, subtitle, 12, GREY)
		if pages > 1:
			out += text(PAGE_WIDTH - MARGIN, top + MARGIN + 22, '%d / %d' % (page + 1, pages), 12, GREY, anchor='end')
		out += text(PAGE_WIDTH - MARGIN, top + PAGE_HEIGHT - 16, 'OpenAstro.org', 10, GREY, anchor='end')
		return out

	def radixLine(self):
		"""name, local date and place of the radix for table headers"""
		return '%s  ·  %s-%02d-%02d %02d:%02d%s  ·  %s' % (self.name, self.year_loc, self.month_loc, self.day_loc,
			self.hour_loc, self.minute_loc, self.decTzStr(self.timezone), self.location)

	""" make graphic for monthly timeline """
	def makeTimelineSVG(self,printing,y,m):
		#transits of the month use the aspect and planet settings of transit charts
		aspects = self.db.getSettingsAspect('transit')
		bodies = self.db.getSettingsPlanet('transit')
		tz = datetime.timedelta(seconds=float(self.timezone)*float(3600))
		startdate = datetime.datetime(y,m,1,12) - tz
		q,r = divmod(startdate.month, 12)
		enddate = datetime.datetime(startdate.year+q, r+1, 1,12)
		delta = enddate - startdate
		atgrid={}
		astypes={}
		retrogrid={}
		for d in range(delta.days):
			cdate = startdate + datetime.timedelta(days=d)
			tmoddata = ephemeris.ephData(cdate.year,cdate.month,cdate.day,cdate.hour, self.geolon,self.geolat,self.altitude,self.planets,self.zodiac,self.db.astrocfg)
			for i in range(len(self.planets)):
				start=self.planets_degree_ut[i]
				#every radix planet against every transit planet (not symmetric)
				for x in range(len(self.planets)):
					#skip transit points too fast for one sample per day: moon (1),
					#asc/mc/dsc/ic (23-26) and the asc based day/night pars (27, 28)
					#and marriage pars (30)
					if x == 1 or 23 <= x <= 28 or x == 30:
						continue
					end=tmoddata.planets_degree_ut[x]
					diff=float(self.degreeDiff(start,end))
					#aspect with orb of the transit aspect set
					if (bodies[i]['visible'] == 1) & (bodies[x]['visible_transit'] == 1):
						z = self.matchAspect(diff, aspects)
						if z is not None and aspects[z]['visible_grid'] == 1:
							orb = abs(diff - aspects[z]['degree'])
							#aspect grid dictionary
							s="%02d%02d%02d"%(i,z,x)
							astypes[s]=(i,x,z)
							retrogrid.setdefault(s, {})[d]=tmoddata.planets_retrograde[x]
							atgrid.setdefault(s, {})[d]=orb
		keys = sorted(astypes.keys())
		days = delta.days
		#layout: label column, a column per day, rows on as many pages as needed
		row = 16.0
		top = MARGIN + 96
		per_page = int((PAGE_HEIGHT - top - MARGIN - 24) // row)
		self.pages = max(1, -(-len(keys) // per_page))
		label = 70.0
		column = (PAGE_WIDTH - 2 * MARGIN - label) / days
		x0 = MARGIN + label
		local = [datetime.date(y, m, 1) + datetime.timedelta(days=d) for d in range(days)]
		today = datetime.date.today()
		title = '%s  ·  %s' % (datetime.date(y, m, 1).strftime('%B %Y'), self.name)
		out = []
		for p in range(self.pages):
			oy = p * (PAGE_HEIGHT + PAGE_GAP)
			rows = keys[p * per_page:(p + 1) * per_page]
			out.append(self.tableHeader(oy, title, '%s  ·  %s' % (_('Transit'), self.radixLine()), p, self.pages))
			head = oy + top - 34
			bottom = oy + top + row * len(rows)
			#days: weekday and number, weekends shaded, today framed
			for d, day in enumerate(local):
				x = x0 + d * column
				if day.weekday() >= 5:
					out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" style="fill: %s;"/>\n' % (x, head, column, bottom - head, ZEBRA))
				out.append(text(x + column / 2, oy + top - 22, day.strftime('%a')[:2], 8, GREY, anchor='middle'))
				out.append(text(x + column / 2, oy + top - 8, day.day, 11, INK, weight='bold' if day == today else 'normal', anchor='middle'))
				if day == today:
					out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" style="fill: none; stroke: %s; stroke-width: 1.5;"/>\n' % (
						x + 0.5, head, column - 1, bottom - head, ACCENT))
			out.append(rule(MARGIN, oy + top, PAGE_WIDTH - MARGIN))
			for k, key in enumerate(rows):
				i, x, z = astypes[key]
				ry = oy + top + k * row
				if k % 2:
					out.append('<rect x="%s" y="%.1f" width="%s" height="%s" style="fill: %s;"/>\n' % (MARGIN, ry, label, row, ZEBRA))
				#transit body, aspect, radix body
				out.append(symbol(self.svgSafeHref(self.planets[x]['name']), MARGIN + 2, ry + 1.5, 13))
				out.append(symbol('orb%s' % aspects[z]['degree'], MARGIN + 25, ry + 3.5, 9))
				out.append(symbol(self.svgSafeHref(self.planets[i]['name']), MARGIN + 42, ry + 1.5, 13))
				orbs = atgrid[key]
				exact = min(orbs, key=orbs.get)
				maxorb = aspects[z]['orb']
				color = self.aspectColor(aspects[z]['degree'])
				for d, orb in orbs.items():
					#opacity from .85 (exact) to .15 (at the orb of the aspect)
					opacity = .85 - .7 * (orb / maxorb) if maxorb > 0 else .85
					cx = x0 + d * column
					style = 'fill: %s; fill-opacity: %.2f;' % (color, max(.15, min(.85, opacity)))
					if d == exact:
						style += ' stroke: %s; stroke-width: 1;' % (INK)
					out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2.5" style="%s"/>\n' % (cx + 1, ry + 1.5, column - 2, row - 3, style))
					#orb fitting the day cell: one decimal (truncated) below 10 degrees
					value = '%.1f' % (int(orb * 10) / 10.0) if orb < 10 else '%d' % (int(orb))
					out.append(text(cx + column / 2, ry + row - 4.5, value, 7.5, INK, weight='bold' if d == exact else 'normal', anchor='middle'))
					if retrogrid[key][d]:
						out.append(text(cx + column - 2, ry + 7, '℞', 5.5, GREY, anchor='end'))
			out.append(rule(MARGIN, bottom, PAGE_WIDTH - MARGIN))
		return document(self.pages, printing, self.chartSymbols(), ''.join(out), title)

	""" make graphic for cusp aspects """
	def makeCuspAspectsSVG(self, printing):
		#cusp aspects belong to the radix, self.aspects may hold the transit set
		aspects = self.db.getSettingsAspect('radix')
		bodies = self.db.getSettingsPlanet('radix')
		#shown bodies, the angles are cusps themselves
		rows = [i for i in range(len(bodies)) if bodies[i]['visible'] == 1 and not 23 <= i <= 26]
		self.pages = 1
		title = '%s  ·  %s' % (_('Cusp Aspects'), self.name)
		label = 170.0
		column = (PAGE_WIDTH - 2 * MARGIN - label) / 12.0
		top = MARGIN + 96
		height = min(28.0, (PAGE_HEIGHT - top - MARGIN - 110) / (len(rows) + 12 + 2))
		out = [self.tableHeader(0, title, self.radixLine())]

		def cuspHeader(y, columns):
			#number and sign of the cusps
			for c in range(columns):
				x = MARGIN + label + c * column
				out.append(text(x + column / 2 - 6, y, c + 1, 12, INK, weight='bold', anchor='middle'))
				out.append(symbol(self.zodiac[self.houses_sign[c]], x + column / 2 + 2, y - 11, 13))
			out.append(rule(MARGIN, y + 6, PAGE_WIDTH - MARGIN))

		def cell(x, y, start, end):
			#aspect symbol and orb
			diff = float(self.degreeDiff(start, end))
			z = self.matchAspect(diff, aspects)
			if z is not None and aspects[z]['visible_grid'] == 1:
				size = min(16.0, height * 0.6)
				out.append(symbol('orb%s' % aspects[z]['degree'], x + column / 2 - size / 2, y + 2, size))
				orb = abs(diff - aspects[z]['degree'])
				out.append(text(x + column / 2, y + height - 2, '%.1f°' % orb, min(8.0, height * 0.32), GREY, anchor='middle'))

		#bodies to the cusps
		y = top
		cuspHeader(y - 8, 12)
		for k, i in enumerate(rows):
			ry = y + k * height
			if k % 2:
				out.append('<rect x="%s" y="%.1f" width="%s" height="%.1f" style="fill: %s;"/>\n' % (MARGIN, ry, PAGE_WIDTH - 2 * MARGIN, height, ZEBRA))
			size = min(16.0, height * 0.7)
			out.append(symbol(self.svgSafeHref(bodies[i]['name']), MARGIN + 2, ry + (height - size) / 2, size))
			out.append(text(MARGIN + size + 8, ry + height / 2 + 4, bodies[i]['label'], min(12.0, height * 0.5)))
			for c in range(12):
				cell(MARGIN + label + c * column, ry, self.planets_degree_ut[i], self.houses_degree_ut[c])
		y += len(rows) * height + 60
		#cusps among each other
		out.append(text(MARGIN, y - 30, _('Houses'), 16, weight='bold'))
		cuspHeader(y - 8, 11)
		for k in range(1, 12):
			ry = y + (k - 1) * height
			if k % 2 == 0:
				out.append('<rect x="%s" y="%.1f" width="%s" height="%.1f" style="fill: %s;"/>\n' % (MARGIN, ry, PAGE_WIDTH - 2 * MARGIN, height, ZEBRA))
			out.append(text(MARGIN + 2, ry + height / 2 + 4, '%s %s' % (self.label['cusp'], k + 1), min(12.0, height * 0.5)))
			for c in range(k):
				cell(MARGIN + label + c * column, ry, self.houses_degree_ut[k], self.houses_degree_ut[c])
		return document(self.pages, printing, self.chartSymbols(), ''.join(out), title)

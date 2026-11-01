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
SVG of the lists beside the chart: elements, legend, planets, houses
"""

import math
from astrochart.constants import RADIUS

class ListsSVGMixin:
	"""SVG of the lists beside the chart: elements, legend, planets, houses"""

	def makeElements( self , r ):
		total = self.fire + self.earth + self.air + self.water
		pf = int(round(100*self.fire/total))
		pe = int(round(100*self.earth/total))
		pa = int(round(100*self.air/total))
		pw = int(round(100*self.water/total))
		out = '<g transform="translate(-30,79)">\n'
		out = out + '<text y="0" style="fill:#ff6600; font-size: 10px;">'+self.label['fire']+'  '+str(pf)+'%</text>\n'
		out = out + '<text y="12" style="fill:#6a2d04; font-size: 10px;">'+self.label['earth']+' '+str(pe)+'%</text>\n'
		out = out + '<text y="24" style="fill:#6f76d1; font-size: 10px;">'+self.label['air']+'   '+str(pa)+'%</text>\n'
		out = out + '<text y="36" style="fill:#630e73; font-size: 10px;">'+self.label['water']+' '+str(pw)+'%</text>\n'
		out = out + '</g>\n'
		return out

	def makeLegend( self ):
		out = '<g transform="translate(624,256)">\n'
		out = out + '<text x="0" y="0" style="fill:#000000; font-size: 12px;">'
		signs = _('Zodiac signs:')
		out = out + signs + '</text>\n'
		out = out + '<g transform="translate(8,8)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[0]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="16" style="fill:#482900; font-size: 10px;"> Aries</text>\n'
		out = out + '<g transform="translate(8,20)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[1]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="28" style="fill:#6b3d00; font-size: 10px;"> Taurus</text>\n'
		out = out + '<g transform="translate(8,32)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[2]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="40" style="fill:#5995e7; font-size: 10px;"> Gemini</text>\n'
		out = out + '<g transform="translate(8,44)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[3]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="52" style="fill:#2b4972; font-size: 10px;"> Cancer</text>\n'
		out = out + '<g transform="translate(8,56)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[4]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="64" style="fill:#c54100; font-size: 10px;"> Leo</text>\n'
		out = out + '<g transform="translate(8,68)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[5]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="76" style="fill:#2b286f; font-size: 10px;"> Virgo</text>\n'
		out = out + '<g transform="translate(8,80)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[6]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="88" style="fill:#69acf1; font-size: 10px;"> Libra</text>\n'
		out = out + '<g transform="translate(8,92)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[7]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="100" style="fill:#ffd237; font-size: 10px;"> Scorpio</text>\n'
		out = out + '<g transform="translate(8,104)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[8]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="112" style="fill:#ff7200; font-size: 10px;"> Sagittarius</text>\n'
		out = out + '<g transform="translate(8,116)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[9]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="124" style="fill:#863c00; font-size: 10px;"> Capricorn</text>\n'
		out = out + '<g transform="translate(8,128)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[10]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="136" style="fill:#4f0377; font-size: 10px;"> Aquarius</text>\n'
		out = out + '<g transform="translate(8,140)">\n'
		out = out + '<use transform="scale(0.3)" xlink:href="#'+self.zodiac[11]+'" />\n'
		out = out + '</g>\n'
		out = out + '<text x="20" y="148" style="fill:#6cbfff; font-size: 10px;"> Pisces</text>\n'
		out = out + '</g>\n'
		return out

	"""
	 Font size for a line of text beside the chart circle, so that it keeps
	 a distance 'keep' from the centre. x,y are page coordinates of anchor
	 and baseline, text width is estimated with 0.45 em per character
	"""
	def fitFontSize( self, text, size, x, y, anchor, keep ):
		# centre of chart circle on page, see template
		cx = cy = 50 + RADIUS
		# point of text nearest to the centre in vertical direction
		dy = min(max(cy, y - 0.8 * size), y + 0.2 * size) - cy
		if abs(dy) >= keep:
			return size
		dx = math.sqrt(keep * keep - dy * dy)
		if anchor == "end":
			room = x - (cx + dx)
		else:
			room = (cx - dx) - x
		width = 0.45 * size * len(text)
		if width <= room:
			return size
		return max(6.0, round(size * room / width, 1))

	def makePlanetGrid( self ):
		out = '<g transform="translate(510,-40)">'
		# loop over all planets
		li=10
		offset=0
		for i in range(len(self.planets)):
			if i == 27:
				li = 10
				offset = -120
			if self.planets[i]['visible'] == 1:
				# start of line
				out = out + '<g transform="translate(%s,%s)">' % (offset,li)
				# planet text, long labels are scaled down to keep clear of chart circle
				size = self.fitFontSize(self.planets[i]['label'], 10, 560+offset, 10+li, "end", RADIUS+4)
				out = out + '<text text-anchor="end" style="fill:%s; font-size: %spx;">%s</text>' % (self.colors['paper_0'],size,self.planets[i]['label'])
				# planet symbol
				out = out + '<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#'+self.svgSafeHref(self.planets[i]['name'])+'" /></g>'
				# planet degree
				out = out + '<text text-anchor="start" x="19" style="fill:%s; font-size: 10px;">%s</text>' % (self.colors['paper_0'],self.dec2deg(self.planets_degree[i]))
				# zodiac
				out = out + '<g transform="translate(60,-8)"><use transform="scale(0.3)" xlink:href="#'+self.zodiac[self.planets_sign[i]]+'" /></g>'
				# planet retrograde
				if self.planets_retrograde[i]:
					out = out + '<g transform="translate(74,-8)"><use transform="scale(0.7)" xlink:href="#retrograde" /></g>'
				# end of line
				out = out + '</g>\n'
				# offset between lines
				li = li + 14
		out = out + '</g>\n'
		return out

	def makeHousesGrid( self ):
		set_x = '624'
		if len(self.label['cusp']) < 8:
			set_x = '608'
		out = '<g transform="translate({0},-40)">'.format(set_x)
		li=10
		for i in range(12):
			if i < 9:
				cusp = '&#160;&#160;'+str(i+1)
			else:
				cusp = str(i+1)
			out += '<g transform="translate(0,'+str(li)+')">'
			out += '<text text-anchor="end" x="40" style="fill:%s; font-size: 10px;">%s %s:</text>' % (self.colors['paper_0'],self.label['cusp'],cusp)
			out += '<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#'+self.zodiac[self.houses_sign[i]]+'" /></g>'
			out += '<text x="53" style="fill:%s; font-size: 10px;"> %s</text>' % (self.colors['paper_0'], self.dec2deg(self.houses_degree[i]))
			out += '</g>\n'
			li = li + 14
		out += '</g>\n'
		return out

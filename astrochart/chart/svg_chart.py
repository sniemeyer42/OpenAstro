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
SVG of a chart: calculation, template, zodiac, houses and rings
"""

import math
from string import Template
from openastromod import swiss as ephemeris
from astrochart.constants import RADIUS, WHEEL_MARGIN

class ChartSVGMixin:
	"""SVG of a chart: calculation, template, zodiac, houses and rings"""

	def makeWheelSVG(self, td=None):
		"""chart wheel alone as SVG document (calculates the chart unless the
		template data td of templateData() is given)"""
		td = dict(td) if td is not None else self.templateData()
		td['viewbox'] = '%s %s %s %s' % (-WHEEL_MARGIN, -WHEEL_MARGIN, 2*(RADIUS+WHEEL_MARGIN), 2*(RADIUS+WHEEL_MARGIN))
		td['svgWidth'] = td['svgHeight'] = str(2*(RADIUS+WHEEL_MARGIN))
		td['wheelCenter'] = str(RADIUS)
		td['wheelRadius'] = str(RADIUS+WHEEL_MARGIN)
		return Template(self.loadTemplate(self.cfg.xml_svg_wheel)).substitute(td)

	def loadTemplate(self, path):
		"""template text with the shared symbol definitions inserted"""
		with open(path) as f:
			text = f.read()
		if '<!--#symbols#-->' in text:
			with open(self.cfg.xml_svg_symbols) as f:
				text = text.replace('<!--#symbols#-->', f.read().rstrip('\n'))
		return text

	def calculate(self):
		"""positions of the chart: settings of the chart type, ephemeris, composite averages"""
		#empty element points
		self.fire=0.0
		self.earth=0.0
		self.air=0.0
		self.water=0.0
		#get database aspect and planet settings of the chart type (synastry is drawn as transit)
		if self.type == "Transit":
			if self.synastry:
				self.aspectset = 'synastry'
			else:
				self.aspectset = 'transit'
		else:
			#Radix, Composite, Combine, Solar, SecondaryProgression
			self.aspectset = 'radix'
		self.planets = self.db.getSettingsPlanet(self.aspectset)
		self.aspects = self.db.getSettingsAspect(self.aspectset)
		#update the labels
		self.label = self.db.getLabel()
		#Combine module data
		if self.type == "Combine":
			#make calculations
			module_data = ephemeris.ephData(self.c_year,self.c_month,self.c_day,self.c_hour,self.c_geolon,self.c_geolat,self.c_altitude,self.planets,self.zodiac,self.db.astrocfg)
		#Solar module data
		if self.type == "Solar":
			module_data = ephemeris.ephData(self.s_year,self.s_month,self.s_day,self.s_hour,self.s_geolon,self.s_geolat,self.s_altitude,self.planets,self.zodiac,self.db.astrocfg)
		elif self.type == "SecondaryProgression":
			module_data = ephemeris.ephData(self.sp_year,self.sp_month,self.sp_day,self.sp_hour,self.sp_geolon,self.sp_geolat,self.sp_altitude,self.planets,self.zodiac,self.db.astrocfg,houses_override=self.houses_override)				
		elif self.type == "Transit" or self.type == "Composite":
			module_data = ephemeris.ephData(self.year,self.month,self.day,self.hour,self.geolon,self.geolat,self.altitude,self.planets,self.zodiac,self.db.astrocfg)
			t_module_data = ephemeris.ephData(self.t_year,self.t_month,self.t_day,self.t_hour,self.t_geolon,self.t_geolat,self.t_altitude,self.planets,self.zodiac,self.db.astrocfg)
		else:
			#make calculations
			module_data = ephemeris.ephData(self.year,self.month,self.day,self.hour,self.geolon,self.geolat,self.altitude,self.planets,self.zodiac,self.db.astrocfg)
		#Transit module data
		if self.type == "Transit" or self.type == "Composite":
			#grab transiting module data
			self.t_planets_sign = t_module_data.planets_sign
			self.t_planets_degree = t_module_data.planets_degree
			self.t_planets_degree_ut = t_module_data.planets_degree_ut
			self.t_planets_retrograde = t_module_data.planets_retrograde
			self.t_houses_degree = t_module_data.houses_degree
			self.t_houses_sign = t_module_data.houses_sign
			self.t_houses_degree_ut = t_module_data.houses_degree_ut
		#grab normal module data
		self.planets_sign = module_data.planets_sign
		self.planets_degree = module_data.planets_degree
		self.planets_degree_ut = module_data.planets_degree_ut
		self.planets_retrograde = module_data.planets_retrograde
		self.houses_degree = module_data.houses_degree
		self.houses_sign = module_data.houses_sign
		self.houses_degree_ut = module_data.houses_degree_ut		
		self.lunar_phase = module_data.lunar_phase
		#make composite averages
		if self.type == "Composite":
			#new houses
			asc = self.houses_degree_ut[0]
			t_asc = self.t_houses_degree_ut[0]
			for i in range(12):
				#difference in distances measured from ASC
				diff = self.houses_degree_ut[i] - asc
				if diff < 0:
					diff = diff + 360.0
				t_diff = self.t_houses_degree_ut[i] - t_asc
				if t_diff < 0:
					t_diff = t_diff + 360.0	
				newdiff = (diff + t_diff) / 2.0
				#new ascendant
				if asc > t_asc:
					diff = asc - t_asc
					if diff > 180:
						diff = 360.0 - diff
						nasc = asc + (diff / 2.0)
					else:
						nasc = t_asc + (diff / 2.0)
				else:
					diff = t_asc - asc
					if diff > 180:
						diff = 360.0 - diff
						nasc = t_asc + (diff / 2.0)
					else:
						nasc = asc + (diff / 2.0)
				#new house degrees
				self.houses_degree_ut[i] = nasc + newdiff
				if self.houses_degree_ut[i] > 360:
					self.houses_degree_ut[i] = self.houses_degree_ut[i] - 360.0	
				#new house sign				
				for x in range(len(self.zodiac)):
					deg_low=float(x*30)
					deg_high=float((x+1)*30)
					if self.houses_degree_ut[i] >= deg_low:
						if self.houses_degree_ut[i] <= deg_high:
							self.houses_sign[i]=x
							self.houses_degree[i] = self.houses_degree_ut[i] - deg_low
			#new planets
			for i in range(23):
				#difference in degrees
				p1 = self.planets_degree_ut[i]
				p2 = self.t_planets_degree_ut[i]
				if p1 > p2:
					diff = p1 - p2
					if diff > 180:
						diff = 360.0 - diff
						self.planets_degree_ut[i] = (diff / 2.0) + p1
					else:
						self.planets_degree_ut[i] = (diff / 2.0) + p2
				else:
					diff = p2 - p1
					if diff > 180:
						diff = 360.0 - diff
						self.planets_degree_ut[i] = (diff / 2.0) + p2
					else:
						self.planets_degree_ut[i] = (diff / 2.0) + p1
				if self.planets_degree_ut[i] > 360:
					self.planets_degree_ut[i] = self.planets_degree_ut[i] - 360.0
			#list index 23 is asc, 24 is Mc, 25 is Dsc, 26 is Ic
			self.planets_degree_ut[23] = self.houses_degree_ut[0]
			self.planets_degree_ut[24] = self.houses_degree_ut[9]
			self.planets_degree_ut[25] = self.houses_degree_ut[6]
			self.planets_degree_ut[26] = self.houses_degree_ut[3]
			#new planet signs
			for i in range(27):
				for x in range(len(self.zodiac)):
					deg_low=float(x*30)
					deg_high=float((x+1)*30)
					if self.planets_degree_ut[i] >= deg_low:
						if self.planets_degree_ut[i] <= deg_high:
							self.planets_sign[i]=x
							self.planets_degree[i] = self.planets_degree_ut[i] - deg_low
							self.planets_retrograde[i] = False

	def templateData(self):
		"""calculate the chart and fill the template dictionary of the wheel"""
		self.calculate()
		#the selected body must still be shown
		if self.highlight is not None:
			side, ident = self.highlight
			key = 'visible_transit' if side == 'transit' else 'visible'
			if (side == 'transit' and self.type != "Transit") or self.planets[ident][key] != 1:
				self.highlight = None
		#template dictionary		
		td=dict()
		r=RADIUS
		if(self.db.astrocfg['chartview']=="european"):
			self.c1=56
			self.c2=92
			self.c3=112
		else:				
			self.c1=0
			self.c2=36
			self.c3=120
		#transit
		if self.type == "Transit":
			td['transitRing']=self.transitRing( r )
			td['degreeRing']=self.degreeTransitRing( r )
			#circles
			td['c1'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-36) + '"'
			td['c1style'] = 'fill: none; stroke: %s; stroke-width: 1px; stroke-opacity:.4;'%(self.colors['zodiac_transit_ring_2'])
			td['c2'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-72) + '"'
			td['c2style'] = 'fill: %s; fill-opacity:.4; stroke: %s; stroke-opacity:.4; stroke-width: 1px'%(self.colors['paper_1'],self.colors['zodiac_transit_ring_1'])
			td['c3'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-160) + '"'
			td['c3style'] = 'fill: %s; fill-opacity:.8; stroke: %s; stroke-width: 1px'%(self.colors['paper_1'],self.colors['zodiac_transit_ring_0'])
			td['makeAspects'] = self.makeAspectsTransit( r , (r-160))
		else:
			td['transitRing'] = ""
			td['degreeRing'] = self.degreeRing( r )
			#circles
			td['c1'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-self.c1) + '"'
			td['c1style'] = 'fill: none; stroke: %s; stroke-width: 1px; '%(self.colors['zodiac_radix_ring_2'])
			td['c2'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-self.c2) + '"'
			td['c2style'] = 'fill: %s; fill-opacity:.2; stroke: %s; stroke-opacity:.4; stroke-width: 1px'%(self.colors['paper_1'],self.colors['zodiac_radix_ring_1'])
			td['c3'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-self.c3) + '"'
			td['c3style'] = 'fill: %s; fill-opacity:.8; stroke: %s; stroke-width: 1px'%(self.colors['paper_1'],self.colors['zodiac_radix_ring_0'])
			td['makeAspects'] = self.makeAspects( r , (r-self.c3))
		#paper_color_X
		td['paper_color_0']=self.colors["paper_0"]
		td['paper_color_1']=self.colors["paper_1"]
		#planets_color_X
		for i in range(len(self.planets)):
			td['planets_color_%s'%(i)]=self.colors["planet_%s"%(i)]
		#zodiac_color_X
		for i in range(12):
			td['zodiac_color_%s'%(i)]=self.colors["zodiac_icon_%s" %(i)]
		#orb_color_X
		for i in range(len(self.aspects)):
			td['orb_color_%s'%(self.aspects[i]['degree'])]=self.colors["aspect_%s" %(self.aspects[i]['degree'])]
		#functions
		td['makeZodiac'] = self.makeZodiac( r )
		td['makeHouses'] = self.makeHouses( r )
		td['makePlanets'] = self.makePlanets( r )
		#ring around the selected body, on top of the planets
		if self.highlight is not None:
			td['makeAspects'] += self.makeHighlight()
		return td

	""" Draw transit ring """
	def transitRing( self , r ):
		out = '<circle cx="%s" cy="%s" r="%s" style="fill: none; stroke: %s; stroke-width: 36px; stroke-opacity: .4;"/>' % (r,r,r-18,self.colors['paper_1'])
		out += '<circle cx="%s" cy="%s" r="%s" style="fill: none; stroke: %s; stroke-width: 1px; stroke-opacity: .6;"/>' % (r,r,r,self.colors['zodiac_transit_ring_3'])
		return out

	""" Draw degree ring """
	def degreeRing( self , r ):
		out=''
		for i in range(72):
			offset = float(i*5) - self.houses_degree_ut[6]
			if offset < 0:
				offset = offset + 360.0
			elif offset > 360:
				offset = offset - 360.0
			x1 = self.sliceToX( 0 , r-self.c1 , offset ) + self.c1
			y1 = self.sliceToY( 0 , r-self.c1 , offset ) + self.c1
			x2 = self.sliceToX( 0 , r+2-self.c1 , offset ) - 2 + self.c1
			y2 = self.sliceToY( 0 , r+2-self.c1 , offset ) - 2 + self.c1
			out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: 1px; stroke-opacity:.9;"/>\n' % (
				x1,y1,x2,y2,self.colors['paper_0'] )
		return out

	def degreeTransitRing( self , r ):
		out=''
		for i in range(72):
			offset = float(i*5) - self.houses_degree_ut[6]
			if offset < 0:
				offset = offset + 360.0
			elif offset > 360:
				offset = offset - 360.0
			x1 = self.sliceToX( 0 , r , offset )
			y1 = self.sliceToY( 0 , r , offset )
			x2 = self.sliceToX( 0 , r+2 , offset ) - 2
			y2 = self.sliceToY( 0 , r+2 , offset ) - 2
			out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: #F00; stroke-width: 1px; stroke-opacity:.9;"/>\n' %(x1, y1, x2, y2)
		return out

	""" draw svg aspects: ring, aspect ring, degreeA degreeB """
	def drawAspect( self, r, ar, degA, degB, color, emphasis=None ):
		"""aspect line; emphasis: None (normal), True (selected body), False (other bodies)"""
		offset = (int(self.houses_degree_ut[6]) / -1) + int(degA)
		x1 = self.sliceToX( 0 , ar , offset ) + (r-ar)
		y1 = self.sliceToY( 0 , ar , offset ) + (r-ar)
		offset = (int(self.houses_degree_ut[6]) / -1) + int(degB)
		x2 = self.sliceToX( 0 , ar , offset ) + (r-ar)
		y2 = self.sliceToY( 0 , ar , offset ) + (r-ar)
		if emphasis is None:
			style = 'stroke: '+color+'; stroke-width: 1; stroke-opacity: .9;'
		elif emphasis:
			style = 'stroke: '+color+'; stroke-width: 2.5; stroke-opacity: 1;'
		else:
			style = 'stroke: '+color+'; stroke-width: 1; stroke-opacity: .12;'
		out = '			<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="'+style+'"/>\n'
		return out

	def emphasis(self, side_a, id_a, side_b, id_b):
		"""emphasis of an aspect line between two bodies for the selected body (self.highlight)"""
		if self.highlight is None:
			return None
		return self.highlight in ((side_a, id_a), (side_b, id_b))

	def makeHighlight(self):
		"""ring around the symbol of the selected body"""
		for glyph in getattr(self, 'glyphs', []):
			if (glyph['side'], glyph['id']) == self.highlight:
				return '<circle cx="%s" cy="%s" r="%s" style="fill: none; stroke: #3584e4; stroke-width: 2.5;"/>\n' % (
					glyph['x'], glyph['y'], glyph['r'] + 4)
		return ''

	def redrawAspects(self, td):
		"""template data with the aspect lines drawn again (after a change of self.highlight)"""
		td = dict(td)
		r = RADIUS
		if self.type == "Transit":
			td['makeAspects'] = self.makeAspectsTransit( r , (r-160))
		else:
			td['makeAspects'] = self.makeAspects( r , (r-self.c3))
		if self.highlight is not None:
			td['makeAspects'] += self.makeHighlight()
		return td

	def sliceToX(self, slice, r, offset ):
		plus = (math.pi * offset) / 180
		radial = ((math.pi/6) * slice) + plus
		return r * (math.cos(radial)+1)

	def sliceToY(self , slice , r, offset):
		plus = (math.pi * offset) / 180
		radial = ((math.pi/6) * slice) + plus
		return r * ((math.sin(radial)/-1)+1)

	def zodiacSlice(self, num, r, style, type ):
		# pie slices
		if self.db.astrocfg["houses_system"] == "G":
			offset = 360 - self.houses_degree_ut[18]
		else:
			offset = 360 - self.houses_degree_ut[6]
		#check transit
		if self.type == "Transit":
			dropin=0
		else:
			dropin = self.c1
		slice = '<path d="M' + str(r) + ',' + str(r) + ' L' + str(dropin + self.sliceToX(num,r-dropin,offset)) + ',' + str( dropin + self.sliceToY(num,r-dropin,offset)) + ' A' + str(r-dropin) + ',' + str(r-dropin) + ' 0 0,0 ' + str(dropin + self.sliceToX(num+1,r-dropin,offset)) + ',' + str(dropin + self.sliceToY(num+1,r-dropin,offset)) + ' z" style="' + style + '"/>'
		# symbols
		offset = offset + 15
		# check transit
		if self.type == "Transit":
			dropin=54
		else:
			dropin=18+self.c1
		sign = '<g transform="translate(-16,-16)"><use x="' + str(dropin + self.sliceToX(num,r-dropin,offset)) + '" y="' + str(dropin + self.sliceToY(num,r-dropin,offset)) + '" xlink:href="#' + type + '" /></g>\n'
		return slice + '\n' + sign

	def makeZodiac( self, r ):
		output = ""
		for i in range(len(self.zodiac)):
			output = output + self.zodiacSlice( i , r , "fill:" + self.colors["zodiac_bg_%s"%(i)] + "; fill-opacity: 0.5;" , self.zodiac[i]) + '\n'
		return output

	def makeHouses( self, r ):
		path = ""
		if self.db.astrocfg["houses_system"] == "G":
			xr = 36
		else:
			xr = 12
		for i in range(xr):
			# check transit
			if self.type == "Transit":
				dropin=160
				roff=72
				t_roff=36
			else:
				dropin=self.c3
				roff=self.c1
			# offset is negative desc houses_degree_ut[6]
			offset = (int(self.houses_degree_ut[int(xr/2)]) / -1) + int(self.houses_degree_ut[i])
			x1 = self.sliceToX( 0 , (r-dropin) , offset ) + dropin
			y1 = self.sliceToY( 0 , (r-dropin) , offset ) + dropin
			x2 = self.sliceToX( 0 , r-roff , offset ) + roff
			y2 = self.sliceToY( 0 , r-roff , offset ) + roff
			if i < (xr-1):
				text_offset = offset + int(self.degreeDiff( self.houses_degree_ut[(i+1)], self.houses_degree_ut[i] ) / 2 )
			else:
				text_offset = offset + int(self.degreeDiff( self.houses_degree_ut[0], self.houses_degree_ut[(xr-1)] ) / 2 )
			# mc, asc, dsc, ic
			if i == 0:
				linecolor=self.planets[23]['color']
			elif i == 9:
				linecolor=self.planets[24]['color']
			elif i == 6:
				linecolor=self.planets[25]['color']
			elif i == 3:
				linecolor=self.planets[26]['color']
			else:
				linecolor=self.colors['houses_radix_line']
			# transit houses lines
			if self.type == "Transit":
				#degrees for point zero
				zeropoint = 360 - self.houses_degree_ut[6]
				t_offset = zeropoint + self.t_houses_degree_ut[i]
				if t_offset > 360:
					t_offset = t_offset - 360
				t_x1 = self.sliceToX( 0 , (r-t_roff) , t_offset ) + t_roff
				t_y1 = self.sliceToY( 0 , (r-t_roff) , t_offset ) + t_roff
				t_x2 = self.sliceToX( 0 , r , t_offset )
				t_y2 = self.sliceToY( 0 , r , t_offset )
				if i < 11:
					t_text_offset = t_offset + int(self.degreeDiff( self.t_houses_degree_ut[(i+1)], self.t_houses_degree_ut[i] ) / 2 )
				else:
					t_text_offset = t_offset + int(self.degreeDiff( self.t_houses_degree_ut[0], self.t_houses_degree_ut[11] ) / 2 )
				#linecolor
				if i == 0 or i == 9 or i == 6 or i == 3:
					t_linecolor=linecolor
				else:
					t_linecolor = self.colors['houses_transit_line']
				xtext = self.sliceToX( 0 , (r-8) , t_text_offset ) + 8
				ytext = self.sliceToY( 0 , (r-8) , t_text_offset ) + 8
				path = path + '<text style="fill: #00f; fill-opacity: .4; font-size: 14px"><tspan x="'+str(xtext-3)+'" y="'+str(ytext+3)+'">'+str(i+1)+'</tspan></text>\n'
				path = path + '<line x1="'+str(t_x1)+'" y1="'+str(t_y1)+'" x2="'+str(t_x2)+'" y2="'+str(t_y2)+'" style="stroke: '+t_linecolor+'; stroke-width: 2px; stroke-opacity:.3;"/>\n'
			# if transit
			if self.type == "Transit":
				dropin=84
			elif self.db.astrocfg["chartview"] == "european":
				dropin=100
			else:
				dropin=48
			xtext = self.sliceToX( 0 , (r-dropin) , text_offset ) + dropin #was 132
			ytext = self.sliceToY( 0 , (r-dropin) , text_offset ) + dropin #was 132
			path = path + '<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+linecolor+'; stroke-width: 2px; stroke-dasharray:3,2; stroke-opacity:.4;"/>\n'
			path = path + '<text style="fill: #f00; fill-opacity: .6; font-size: 14px"><tspan x="'+str(xtext-3)+'" y="'+str(ytext+3)+'">'+str(i+1)+'</tspan></text>\n'
		return path

	def svgSafeHref(self, name):
		name=name.replace(' ','_')
		return name

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
SVG of the planets of radix and transit ring
"""

class PlanetsSVGMixin:
	"""SVG of the planets of radix and transit ring"""

	def makePlanets( self , r ):
		#positions of the drawn symbols (wheel coordinates) for the interactive wheel
		self.glyphs = []
		planets_degut={}
		diff=range(len(self.planets))
		for i in range(len(self.planets)):
			if self.planets[i]['visible'] == 1:
				# list of planets sorted by degree
				planets_degut[self.planets_degree_ut[i]]=i
			#element: get extra points if planet is in own zodiac
			pz = self.planets[i]['zodiac_relation']
			cz = self.planets_sign[i]
			extrapoints = 0
			if pz != -1:
				for e in range(len(pz.split(','))):
					if int(pz.split(',')[e]) == int(cz):
						extrapoints = 10
			# calculate element points for all planets
			ele = self.zodiac_element[self.planets_sign[i]]
			if ele == "fire":
				self.fire = self.fire + self.planets[i]['element_points'] + extrapoints
			elif ele == "earth":
				self.earth = self.earth + self.planets[i]['element_points'] + extrapoints
			elif ele == "air":
				self.air = self.air + self.planets[i]['element_points'] + extrapoints
			elif ele == "water":
				self.water = self.water + self.planets[i]['element_points'] + extrapoints
		output = ""
		keys = list(planets_degut.keys())
		keys.sort()
		switch=0
		planets_degrouped = {}
		groups = []
		planets_by_pos = list(range(len(planets_degut)))
		planet_drange = 3.4
		# get groups closely together
		group_open = False
		for e in range(len(keys)):
			i=planets_degut[keys[e]]
			# get distances between planets
			if e == 0:
				prev = self.planets_degree_ut[planets_degut[keys[-1]]]
				next = self.planets_degree_ut[planets_degut[keys[1]]]
			elif e == (len(keys)-1):
				prev = self.planets_degree_ut[planets_degut[keys[e-1]]]
				next = self.planets_degree_ut[planets_degut[keys[0]]]
			else:
				prev = self.planets_degree_ut[planets_degut[keys[e-1]]]
				next = self.planets_degree_ut[planets_degut[keys[e+1]]]
			diffa=self.degreeDiff(prev,self.planets_degree_ut[i])
			diffb=self.degreeDiff(next,self.planets_degree_ut[i])
			planets_by_pos[e]=[i,diffa,diffb]
			# print "%s %s %s" % (self.planets[i]['label'],diffa,diffb)
			if (diffb < planet_drange):
				if group_open:
					groups[-1].append([e,diffa,diffb,self.planets[planets_degut[keys[e]]]["label"]])
				else:
					group_open=True
					groups.append([])
					groups[-1].append([e, diffa, diffb, self.planets[planets_degut[keys[e]]]["label"]])
			else:
				if group_open:
					groups[-1].append([e, diffa, diffb, self.planets[planets_degut[keys[e]]]["label"]])
				group_open=False
		def zero(x): return 0
		planets_delta = list(map(zero,range(len(self.planets))))
		# print groups
		# print planets_by_pos
		for a in range(len(groups)):
			#Two grouped planets
			if len(groups[a]) == 2:
				next_to_a = groups[a][0][0]-1
				if groups[a][1][0] == (len(planets_by_pos)-1):
					next_to_b = 0
				else:
					next_to_b = groups[a][1][0]+1
				# if both planets have room
				if (groups[a][0][1] > (2*planet_drange))&(groups[a][1][2] > (2*planet_drange)):
					planets_delta[groups[a][0][0]]=-(planet_drange-groups[a][0][2])/2
					planets_delta[groups[a][1][0]]=+(planet_drange-groups[a][0][2])/2
				# if planet a has room
				elif (groups[a][0][1] > (2*planet_drange)):
					planets_delta[groups[a][0][0]]=-planet_drange
				#if planet b has room
				elif (groups[a][1][2] > (2*planet_drange)):
					planets_delta[groups[a][1][0]]=+planet_drange
				# if planets next to a and b have room move them
				elif (planets_by_pos[next_to_a][1] > (2.4*planet_drange))&(planets_by_pos[next_to_b][2] > (2.4*planet_drange)):
					planets_delta[(next_to_a)]=(groups[a][0][1]-planet_drange*2)
					planets_delta[groups[a][0][0]]=-planet_drange*.5
					planets_delta[next_to_b]=-(groups[a][1][2]-planet_drange*2)
					planets_delta[groups[a][1][0]]=+planet_drange*.5
				# if planet next to a has room move them
				elif (planets_by_pos[next_to_a][1] > (2*planet_drange)):
					planets_delta[(next_to_a)]=(groups[a][0][1]-planet_drange*2.5)
					planets_delta[groups[a][0][0]]=-planet_drange*1.2
				# if planet next to b has room move them
				elif (planets_by_pos[next_to_b][2] > (2*planet_drange)):
					planets_delta[next_to_b]=-(groups[a][1][2]-planet_drange*2.5)
					planets_delta[groups[a][1][0]]=+planet_drange*1.2
			# Three grouped planets or more
			xl = len(groups[a])
			if xl >= 3:
				available = groups[a][0][1]
				for f in range(xl):
					available += groups[a][f][2]
				need = (3*planet_drange)+(1.2*(xl-1)*planet_drange)
				leftover = available - need
				xa=groups[a][0][1]
				xb=groups[a][(xl-1)][2]
				# center
				if (xa > (need*.5)) & (xb > (need*.5)):
					startA = xa - (need*.5)
				# position relative to next planets
				else:
					startA = (leftover/(xa+xb))*xa
					startB = (leftover/(xa+xb))*xb
				if available > need:
					planets_delta[groups[a][0][0]] = startA-groups[a][0][1]+(1.5*planet_drange)
					for f in range(xl-1):
						planets_delta[groups[a][(f+1)][0]] = 1.2*planet_drange+planets_delta[groups[a][f][0]]-groups[a][f][2]
		for e in range(len(keys)):
			i = planets_degut[keys[e]]
			#coordinates
			if self.type == "Transit":
				if 22 < i < 27:
					rplanet = 76
				elif switch == 1:
					rplanet=110
					switch = 0
				else:
					rplanet=130
					switch = 1
			else:
				# if 22 < i < 27 it is asc, mc, dsc, ic (angles of chart)
				# put on special line (rplanet is range from outer ring)
				amin, bmin, cmin = 0, 0, 0
				if self.db.astrocfg["chartview"] == "european":
					amin = 74-10
					bmin = 94-10
					cmin = 40-10
				if 22 < i < 27:
					rplanet = 40-cmin
				elif switch == 1:
					rplanet=74-amin
					switch = 0
				else:
					rplanet=94-bmin
					switch = 1
			rtext=45
			if self.db.astrocfg['houses_system'] == "G":
				offset = (int(self.houses_degree_ut[18]) / -1) + int(self.planets_degree_ut[i])
			else:
				offset = (int(self.houses_degree_ut[6]) / -1) + int(self.planets_degree_ut[i]+planets_delta[e])
				trueoffset = (int(self.houses_degree_ut[6]) / -1) + int(self.planets_degree_ut[i])
			planet_x = self.sliceToX( 0 , (r-rplanet) , offset ) + rplanet
			planet_y = self.sliceToY( 0 , (r-rplanet) , offset ) + rplanet
			if self.type == "Transit":
				scale=0.8
			elif self.db.astrocfg["chartview"] == "european":
				scale=0.8
				# line1
				x1=self.sliceToX( 0 , (r-self.c3) , trueoffset ) + self.c3
				y1=self.sliceToY( 0 , (r-self.c3) , trueoffset ) + self.c3
				x2=self.sliceToX( 0 , (r-rplanet-30) , trueoffset ) + rplanet + 30
				y2=self.sliceToY( 0 , (r-rplanet-30) , trueoffset ) + rplanet + 30
				color=self.planets[i]["color"]
				output += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke-width:1px;stroke:%s;stroke-opacity:.3;"/>\n' % (x1,y1,x2,y2,color)
				# line2
				x1=self.sliceToX( 0 , (r-rplanet-30) , trueoffset ) + rplanet + 30
				y1=self.sliceToY( 0 , (r-rplanet-30) , trueoffset ) + rplanet + 30
				x2=self.sliceToX( 0 , (r-rplanet-10) , offset ) + rplanet + 10
				y2=self.sliceToY( 0 , (r-rplanet-10) , offset ) + rplanet + 10
				output += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke-width:1px;stroke:%s;stroke-opacity:.5;"/>\n' % (x1,y1,x2,y2,color)
			else:
				scale=1
			# output planet
			self.glyphs.append({'side': 'radix', 'id': i, 'x': planet_x, 'y': planet_y, 'r': 12*scale})
			output = output + '<g transform="translate(-'+str(12*scale)+',-'+str(12*scale)+')"><g transform="scale('+str(scale)+')"><use x="' + str(planet_x*(1/scale)) + '" y="' + str(planet_y*(1/scale)) + '" xlink:href="#' + self.svgSafeHref(self.planets[i]['name']) + '" /></g></g>\n'
		#make transit degut and display planets
		if self.type == "Transit":
			group_offset={}
			t_planets_degut={}
			for i in range(len(self.planets)):
				group_offset[i]=0
				#transit or partner side of the planet settings
				if self.planets[i]['visible_transit'] == 1:
					t_planets_degut[self.t_planets_degree_ut[i]]=i
			t_keys = list(t_planets_degut.keys())
			t_keys.sort()
			#grab closely grouped planets
			groups=[]
			in_group=False
			for e in range(len(t_keys)):
				i_a=t_planets_degut[t_keys[e]]
				if e == (len(t_keys)-1):
					i_b=t_planets_degut[t_keys[0]]
				else:
					i_b=t_planets_degut[t_keys[e+1]]
				a=self.t_planets_degree_ut[i_a]
				b=self.t_planets_degree_ut[i_b]
				diff = self.degreeDiff(a,b)
				if diff <= 2.5:
					if in_group:
						groups[-1].append(i_b)
					else:
						groups.append([i_a])
						groups[-1].append(i_b)
						in_group=True
				else:
					in_group=False
			#loop groups and set degrees display adjustment
			for i in range(len(groups)):
				if len(groups[i]) == 2:
					group_offset[groups[i][0]]=-1.0
					group_offset[groups[i][1]]=1.0
				elif len(groups[i]) == 3:
					group_offset[groups[i][0]]=-1.5
					group_offset[groups[i][1]]=0
					group_offset[groups[i][2]]=1.5
				elif len(groups[i]) == 4:
					group_offset[groups[i][0]]=-2.0
					group_offset[groups[i][1]]=-1.0
					group_offset[groups[i][2]]=1.0
					group_offset[groups[i][3]]=2.0
			switch = 0
			for e in range(len(t_keys)):
				i = t_planets_degut[t_keys[e]]
				if 22 < i < 27:
					rplanet = 9
				elif switch == 1:
					rplanet=18
					switch = 0
				else:
					rplanet=26
					switch = 1
				zeropoint = 360 - self.houses_degree_ut[6]
				t_offset = zeropoint + self.t_planets_degree_ut[i]
				if t_offset > 360:
					t_offset = t_offset - 360
				planet_x = self.sliceToX( 0 , (r-rplanet) , t_offset ) + rplanet
				planet_y = self.sliceToY( 0 , (r-rplanet) , t_offset ) + rplanet
				self.glyphs.append({'side': 'transit', 'id': i, 'x': planet_x, 'y': planet_y, 'r': 6})
				output = output + '<g transform="translate(-6,-6)"><g transform="scale(0.5)"><use x="' + str(planet_x*2) + '" y="' + str(planet_y*2) + '" xlink:href="#' + self.svgSafeHref(self.planets[i]['name']) + '" /></g></g>\n'
				#transit planet line
				x1 = self.sliceToX( 0 , r+3 , t_offset ) - 3
				y1 = self.sliceToY( 0 , r+3 , t_offset ) - 3
				x2 = self.sliceToX( 0 , r-3 , t_offset ) + 3
				y2 = self.sliceToY( 0 , r-3 , t_offset ) + 3
				output = output + '<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+self.planets[i]['color']+'; stroke-width: 1px; stroke-opacity:.8;"/>\n'
				#transit planet degree text
				rotate = self.houses_degree_ut[0] - self.t_planets_degree_ut[i]
				textanchor="end"
				t_offset += group_offset[i]
				rtext=-3.0
				if -90 > rotate > -270:
					rotate = rotate + 180.0
					textanchor="start"
				if 270 > rotate > 90:
					rotate = rotate - 180.0
					textanchor="start"
				if textanchor == "end":
					xo=1
				else:
					xo=-1
				deg_x = self.sliceToX( 0 , (r-rtext) , t_offset + xo ) + rtext
				deg_y = self.sliceToY( 0 , (r-rtext) , t_offset + xo ) + rtext
				degree=int(t_offset)
				output += '<g transform="translate(%s,%s)">' % (deg_x,deg_y)
				output += '<text transform="rotate(%s)" text-anchor="%s' % (rotate,textanchor)
				output += '" style="fill: '+self.planets[i]['color']+'; font-size: 10px;">'+self.dec2deg(self.t_planets_degree[i],type="1")
				output += '</text></g>\n'
			#check transit
			if self.type == "Transit":
				dropin=36
			else:
				dropin=0
			#planet line
			x1 = self.sliceToX( 0 , r-(dropin+3) , offset ) + (dropin+3)
			y1 = self.sliceToY( 0 , r-(dropin+3) , offset ) + (dropin+3)
			x2 = self.sliceToX( 0 , (r-(dropin-3)) , offset ) + (dropin-3)
			y2 = self.sliceToY( 0 , (r-(dropin-3)) , offset ) + (dropin-3)
			output = output + '<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+self.planets[i]['color']+'; stroke-width: 2px; stroke-opacity:.6;"/>\n'
			#check transit
			if self.type == "Transit":
				dropin=160
			else:
				dropin=120
			x1 = self.sliceToX( 0 , r-dropin , offset ) + dropin
			y1 = self.sliceToY( 0 , r-dropin , offset ) + dropin
			x2 = self.sliceToX( 0 , (r-(dropin-3)) , offset ) + (dropin-3)
			y2 = self.sliceToY( 0 , (r-(dropin-3)) , offset ) + (dropin-3)
			output = output + '<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+self.planets[i]['color']+'; stroke-width: 2px; stroke-opacity:.6;"/>\n'
		return output

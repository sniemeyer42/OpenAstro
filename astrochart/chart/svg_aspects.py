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
SVG of aspects: patterns, lines, aspect list and grid
"""

class AspectsSVGMixin:
	"""SVG of aspects: patterns, lines, aspect list and grid"""

	def matchAspect( self , diff , aspects=None ):
		"""
		index of the aspect nearest to diff (separation 0..180) within its orb,
		only aspects shown as line or in grid take part, None if no aspect matches;
		one aspect per pair keeps line and grid consistent when orbs overlap
		"""
		if aspects is None:
			aspects = self.aspects
		best = None
		best_dev = None
		for z in range(len(aspects)):
			if aspects[z]['visible'] != 1 and aspects[z]['visible_grid'] != 1:
				continue
			dev = abs(diff - aspects[z]['degree'])
			if dev <= aspects[z]['orb'] and (best_dev is None or dev < best_dev):
				best = z
				best_dev = dev
		return best

	def makeAspects( self , r , ar ):
		out=""
		for i in range(len(self.planets)):
			start=self.planets_degree_ut[i]
			for x in range(i):
				end=self.planets_degree_ut[x]
				diff=float(self.degreeDiff(start,end))
				# aspect with orb of the current aspect set
				if (self.planets[i]['visible_aspect_line'] == 1) & (self.planets[x]['visible_aspect_line'] == 1):
					z = self.matchAspect(diff)
					# check if we want to display this aspect
					if z is not None and self.aspects[z]['visible'] == 1:
						out = out + self.drawAspect( r , ar , self.planets_degree_ut[i] , self.planets_degree_ut[x] , self.colors["aspect_%s" %(self.aspects[z]['degree'])],
							self.emphasis('radix', i, 'radix', x) )
		return out

	def makeAspectsTransit( self , r , ar ):
		out = ""
		self.atgrid=[]
		for i in range(len(self.planets)):
			start=self.planets_degree_ut[i]
			# every radix planet against every transit (synastry) planet
			for x in range(len(self.planets)):
				end=self.t_planets_degree_ut[x]
				diff=float(self.degreeDiff(start,end))
				# symmetric orb of the transit or synastry aspect set,
				# radix side and transit (partner) side of the planet settings
				if (self.planets[i]['visible'] == 1) & (self.planets[x]['visible_transit'] == 1):
					z = self.matchAspect(diff)
					if z is None:
						continue
					# check if we want to display this aspect
					if self.aspects[z]['visible'] == 1:
						out = out + self.drawAspect( r , ar , self.planets_degree_ut[i] , self.t_planets_degree_ut[x] , self.colors["aspect_%s" %(self.aspects[z]['degree'])],
							self.emphasis('radix', i, 'transit', x) )
					# aspect grid dictionary
					if self.aspects[z]['visible_grid'] == 1:
						self.atgrid.append({})
						self.atgrid[-1]['p1']=i
						self.atgrid[-1]['p2']=x
						self.atgrid[-1]['aid']=z
						self.atgrid[-1]['diff']=diff
		return out

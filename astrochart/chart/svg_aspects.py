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

	def makePatterns( self ):
		"""
		* Stellium: At least four planets linked together in a series of continuous conjunctions.
    	* Grand trine: Three trine aspects together.
		* Grand cross: Two pairs of opposing planets squared to each other.
		* T-Square: Two planets in opposition squared to a third. 
		* Yod: Two qunicunxes together joined by a sextile. 
		"""
		conj = {} #0
		opp = {} #10
		sq = {} #5
		tr = {} #6
		qc = {} #9
		sext = {} #3
		for i in range(len(self.planets)):
			a=self.planets_degree_ut[i]
			qc[i]={}
			sext[i]={}
			opp[i]={}
			sq[i]={}
			tr[i]={}
			conj[i]={}
			#skip some points
			n = self.planets[i]['name']
			if n == 'earth' or n == 'true node' or n == 'osc. apogee' or n == 'intp. apogee' or n == 'intp. perigee':
				continue
			if n == 'Dsc' or n == 'Ic':
				continue
			for j in range(len(self.planets)):
				#skip some points
				n = self.planets[j]['name']
				if n == 'earth' or n == 'true node' or n == 'osc. apogee' or n == 'intp. apogee' or n == 'intp. perigee':
					continue
				if n == 'Dsc' or n == 'Ic':
					continue
				b = self.planets_degree_ut[j]
				delta=float(self.degreeDiff(a,b))
				#check for opposition
				xa = float(self.aspects[10]['degree']) - float(self.aspects[10]['orb'])
				xb = float(self.aspects[10]['degree']) + float(self.aspects[10]['orb'])
				if (xa <= delta <= xb):
					opp[i][j]=True
				#check for conjunction
				xa = float(self.aspects[0]['degree']) - float(self.aspects[0]['orb'])
				xb = float(self.aspects[0]['degree']) + float(self.aspects[0]['orb'])
				if (xa <= delta <= xb):
					conj[i][j]=True
				#check for squares
				xa = float(self.aspects[5]['degree']) - float(self.aspects[5]['orb'])
				xb = float(self.aspects[5]['degree']) + float(self.aspects[5]['orb'])
				if (xa <= delta <= xb):
					sq[i][j]=True
				#check for qunicunxes
				xa = float(self.aspects[9]['degree']) - float(self.aspects[9]['orb'])
				xb = float(self.aspects[9]['degree']) + float(self.aspects[9]['orb'])
				if (xa <= delta <= xb):
					qc[i][j]=True
				#check for sextiles
				xa = float(self.aspects[3]['degree']) - float(self.aspects[3]['orb'])
				xb = float(self.aspects[3]['degree']) + float(self.aspects[3]['orb'])
				if (xa <= delta <= xb):
					sext[i][j]=True
		yot={}
		#check for double qunicunxes
		for k,v in qc.items():
			if len(qc[k]) >= 2:
				#check for sextile
				for l,w in qc[k].items():
					for m,x in qc[k].items():
						if m in sext[l]:
							if l > m:
								yot['%s,%s,%s' % (k,m,l)] = [k,m,l]
							else:
								yot['%s,%s,%s' % (k,l,m)] = [k,l,m]
		tsquare={}
		# check for opposition
		for k,v in opp.items():
			if len(opp[k]) >= 1:
				# check for square
				for l,w in opp[k].items():
						for a,b in sq.items():
							if k in sq[a] and l in sq[a]:
								#print 'got tsquare %s %s %s' % (a,k,l)
								if k > l:
									tsquare['%s,%s,%s' % (a,l,k)] = '%s => %s, %s' % (
										self.planets[a]['label'],self.planets[l]['label'],self.planets[k]['label'])
								else:
									tsquare['%s,%s,%s' % (a,k,l)] = '%s => %s, %s' % (
										self.planets[a]['label'],self.planets[k]['label'],self.planets[l]['label'])
		stellium={}
		# check for 4 continuous conjunctions
		for k,v in conj.items():
			if len(conj[k]) >= 1:
				# first conjunction
				for l,m in conj[k].items():
					if len(conj[l]) >= 1:
						for n,o in conj[l].items():
							# skip 1st conj
							if n == k:
								continue
							if len(conj[n]) >= 1:
								# third conjunction
								for p,q in conj[n].items():
									# skip first and second conj
									if p == k or p == n:
										continue
									if len(conj[p]) >= 1:
										# fourth conjunction
										for r,s in conj[p].items():
											# skip conj 1,2,3
											if r == k or r == n or r == p:
												continue
											l=[k,n,p,r]
											l.sort()
											stellium['%s %s %s %s' % (l[0],l[1],l[2],l[3])]='%s %s %s %s' % (self.planets[l[0]]['label'], self.planets[l[1]]['label'], self.planets[l[2]]['label'], self.planets[l[3]]['label'])
		# print yots
		out='<g transform="translate(-30,380)">'
		if len(yot) >= 1:
			y=0
			for k,v in yot.items():
				out += '<text y="%s" style="fill:%s; font-size: 12px;">%s</text>\n' % (y,self.colors['paper_0'],_("Yot"))
				# first planet symbol
				out += '<g transform="translate(20,%s)">' % (y)
				out += '<use transform="scale(0.4)" x="0" y="-20" xlink:href="#%s" /></g>\n' % (
					self.svgSafeHref(self.planets[yot[k][0]]['name']))
				# second planet symbol
				out += '<g transform="translate(30,%s)">'  % (y)
				out += '<use transform="scale(0.4)" x="0" y="-20" xlink:href="#%s" /></g>\n' % (
					self.svgSafeHref(self.planets[yot[k][1]]['name']))
				# third planet symbol
				out += '<g transform="translate(40,%s)">'  % (y)
				out += '<use transform="scale(0.4)" x="0" y="-20" xlink:href="#%s" /></g>\n' % (
					self.svgSafeHref(self.planets[yot[k][2]]['name']))
				y=y+14
		# finalize
		out += '</g>'
		# return out
		return ''

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
						out = out + self.drawAspect( r , ar , self.planets_degree_ut[i] , self.planets_degree_ut[x] , self.colors["aspect_%s" %(self.aspects[z]['degree'])] )
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
						out = out + self.drawAspect( r , ar , self.planets_degree_ut[i] , self.t_planets_degree_ut[x] , self.colors["aspect_%s" %(self.aspects[z]['degree'])] )
					# aspect grid dictionary
					if self.aspects[z]['visible_grid'] == 1:
						self.atgrid.append({})
						self.atgrid[-1]['p1']=i
						self.atgrid[-1]['p2']=x
						self.atgrid[-1]['aid']=z
						self.atgrid[-1]['diff']=diff
		return out

	def makeAspectTransitGrid( self , r ):
		# list fills the box below planet and houses grid down to the bottom,
		# coordinates relative to group translate(50,50) of template
		visible = [i for i in range(min(27, len(self.planets))) if self.planets[i]['visible'] == 1]
		top = 14 * (max(12, len(visible)) - 1)
		left = 502
		width = 216.0
		height = 490.0 - (top + 8)
		colw = 105.0
		rowh = 14.0
		# number of columns allowing the largest scale (not above 1)
		n = len(self.atgrid)
		cols, scale = 1, 0.0
		for c in range(1, max(1, n) + 1):
			s = min(1.0, width / (c * colw - 10.0), height / (max(1, -(-n // c)) * rowh))
			if s > scale + 0.001:
				cols, scale = c, s
		rows = max(1, -(-n // cols))
		if self.synastry:
			heading = "%s %s" % (_("Synastry"), _("Aspects"))
		else:
			heading = _("Planets in Transit")
		out = '<g transform="translate(%s,%s)">' % (left, top)
		out += '<text y="0" x="0" style="fill:%s; font-size: 12px;">%s</text>\n' % (self.colors['paper_0'],heading)
		out += '<g transform="translate(0,8) scale(%s)">' % (round(scale, 3))
		for i in range(n):
			col, row = divmod(i, rows)
			out += '<g transform="translate(%s,%s)">' % (col * colw, row * rowh)
			# first planet symbol
			out += '<use transform="scale(0.4)" x="0" y="3" xlink:href="#%s" />\n' % (
				self.svgSafeHref(self.planets[self.atgrid[i]['p2']]['name']))
			# aspect symbol
			out += '<use  x="15" y="0" xlink:href="#orb%s" />\n' % (
				self.aspects[self.atgrid[i]['aid']]['degree'])
			# second planet symbol
			out += '<g transform="translate(30,0)">'
			out += '<use transform="scale(0.4)" x="0" y="3" xlink:href="#%s" />\n' % (
				self.svgSafeHref(self.planets[self.atgrid[i]['p1']]['name']))
			out += '</g>'
			# difference in degrees
			out += '<text y="8" x="45" style="fill:%s; font-size: 10px;">%s</text>' % (
				self.colors['paper_0'],
				self.dec2deg(self.atgrid[i]['diff']) )
			# line
			out += '</g>'
		out += '</g></g>'
		return out

	def makeAspectGrid( self , r ):
		out=""
		style='stroke:%s; stroke-width: 1px; stroke-opacity:.6; fill:none' % (self.colors['paper_0'])
		xindent=380
		yindent=468
		box=14
		#the grid grows up and right from its lower left corner, more bodies than
		#fit left of the zodiac legend (x=624) and below the planet list scale it down
		left, bottom = xindent, yindent + box
		n = len([p for p in self.planets if p['visible_aspect_grid'] == 1])
		rows = len([i for i in range(min(27, len(self.planets))) if self.planets[i]['visible'] == 1])
		width = 620.0 - left
		height = bottom - (14 * rows - 34)
		scale = 1.0
		if n > 0:
			scale = min(1.0, width / (n * box), height / (n * box))
		revr=list(range(len(self.planets)))
		revr.reverse()
		for a in revr:
			if self.planets[a]['visible_aspect_grid'] == 1:
				start=self.planets_degree_ut[a]
				# first planet 
				out = out + '<rect x="'+str(xindent)+'" y="'+str(yindent)+'" width="'+str(box)+'" height="'+str(box)+'" style="'+style+'"/>\n'
				out = out + '<use transform="scale(0.4)" x="'+str((xindent+2)*2.5)+'" y="'+str((yindent+1)*2.5)+'" xlink:href="#'+self.svgSafeHref(self.planets[a]['name'])+'" />\n'
				xindent = xindent + box
				yindent = yindent - box
				revr2=list(range(a))
				revr2.reverse()
				xorb=xindent
				yorb=yindent + box
				for b in revr2:
					if self.planets[b]['visible_aspect_grid'] == 1:
						end=self.planets_degree_ut[b]
						diff=self.degreeDiff(start,end)
						out = out + '<rect x="'+str(xorb)+'" y="'+str(yorb)+'" width="'+str(box)+'" height="'+str(box)+'" style="'+style+'"/>\n'
						xorb=xorb+box
						z = self.matchAspect(float(diff))
						if z is not None and self.aspects[z]['visible_grid'] == 1:
							out = out + '<use  x="'+str(xorb-box+1)+'" y="'+str(yorb+1)+'" xlink:href="#orb'+str(self.aspects[z]['degree'])+'" />\n'
		if scale < 1.0:
			out = '<g transform="translate(%s,%s) scale(%s) translate(%s,%s)">\n%s</g>\n' % (
				left, bottom, round(scale, 3), -left, -bottom, out)
		return out

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
SVG of the tables: monthly timeline and cusp aspects
"""

import math
import datetime
from string import Template
from openastromod import swiss as ephemeris
from astrochart.constants import ASPECT_DEGREES

class TablesSVGMixin:
	"""SVG of the tables: monthly timeline and cusp aspects"""

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
			#planets_sign,planets_degree,planets_degree_ut,planets_retrograde,houses_degree
			#houses_sign,houses_degree_ut
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

							if s not in retrogrid:
								retrogrid[s]={}
							retrogrid[s][d]=tmoddata.planets_retrograde[x]

							if s not in atgrid:
								atgrid[s]={}
							atgrid[s][d]=orb
		#sort
		keys = list(astypes.keys())
		keys.sort()
		#at least one page (all transit aspects may be hidden)
		self.pages = max(1, int(math.ceil(len(keys)/65.0)))
		out = ""
		#make numbers of days in month
		dx=[80]
		skipdays = [9,19]
		for d in range(delta.days):
			if d in skipdays:
				dx.append(dx[-1]+40)
			else:
				dx.append(dx[-1]+20)	
		for p in range(self.pages):
			if p == 0:
				ystart = 10
			else:
				ystart = (1188 * p) + 62
			pagelen = (len(keys)+1)-p*65
			if pagelen > 65:
				pagelen = 66
			ylen = ((len(keys)+1)-p*65)*16	
			for a in range(delta.days):
				out += '<text x="%s" y="%s" style="fill: %s; font-size: 10">%02d</text>\n'%(
					dx[a],ystart,self.colors['paper_0'],a+1)
				out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
					dx[a]-5,ystart,dx[a]-5,ystart+pagelen*16,self.colors['paper_0'])	
				#skipdays line
				if a in skipdays:
					out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
						dx[a]-5+20,ystart,dx[a]-5+20,ystart+pagelen*16,self.colors['paper_0'])						
			#last line
			out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
					dx[-1]-5,ystart,dx[-1]-5,ystart+pagelen*16,self.colors['paper_0'])
		#get the number of total aspects
		c = 0
		for m in range(len(keys)):
			i,x,z = astypes[keys[m]]
			c += 1
			pagenum = int(math.ceil(c/65.0))
			pagey = (pagenum - 1) * 200
			y = (c*16) + pagey
			#horizontal lines
			out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
				0,y-1,dx[skipdays[0]]+15,y-1,self.colors['paper_0'])
			for s in range(len(skipdays)):
				if s is len(skipdays)-1:
					out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
						dx[skipdays[s]+1]-5,y-1,dx[-1],y-1,self.colors['paper_0'])
				else:
					out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: .5; stroke-opacity:1;"/>\n'%(
						dx[skipdays[s]+1]-5,y-1,dx[skipdays[s+1]]+15,y-1,self.colors['paper_0'])
			#outer planet (symbol ids of the shared table template are the
			#database names with spaces, as in makeCuspAspectsSVG)
			out += '<g transform="translate(0,%s)"><g transform="scale(.5)"><use x="0" y="0" xlink:href="#%s" /></g></g>\n'%(
				y,self.planets[x]['name'])
			#aspect
			out += '<g><use x="20" y="%s" xlink:href="#orb%s" /></g>\n'%(
				y,aspects[z]['degree'])
			#inner planet
			out += '<g transform="translate(40,%s)"><g transform="scale(.5)"><use x="0" y="0" xlink:href="#%s" /></g></g>\n'%(y,
				self.planets[i]['name'])
			for d in range(delta.days):					
				if d in atgrid[keys[m]]:
					orb = atgrid[keys[m]][d]
					#opacity from .8 (exact) to .1 (at the orb of the aspect)
					maxorb = aspects[z]['orb']
					if maxorb > 0:
						op = .8-.7*(orb/maxorb)
					else:
						op = .8
					if op > 1:
						op = 1
					#orb label fitting the day cell: one decimal (truncated) below 10 degrees
					if orb < 10:
						strop = '%.1f' % (math.floor(orb*10)/10.0)
					else:
						strop = '%d' % (int(orb))
					out += '<rect x="%s" y="%s" width="20" height="16" style="fill: %s; fill-opacity:%s;" />'%(dx[d]-5,y-1,self.colors["aspect_%s" %(aspects[z]['degree'])],op)
					#check for retrograde outer planet
					if retrogrid[keys[m]][d]:
						out += '<g transform="translate(%s,%s)"><g transform="scale(.3)">\
							<use x="0" y="0" xlink:href="#retrograde" style="fill:%s; fill-opacity:.8;" /></g></g>\n'%(dx[d]+10,y+10,self.colors['paper_0'],)							
					out += '<text x="%s" y="%s" style="fill: %s; font-size: 10">%s</text>\n'%(
						dx[d],y+9,self.colors['paper_0'],strop)
				else:
					out += ""
		#template
		td = {}
		td['paper_color_0']=self.colors["paper_0"]
		td['paper_color_1']=self.colors["paper_1"]
		for i in range(len(self.planets)):
			td['planets_color_%s'%(i)]=self.colors["planet_%s"%(i)]
		for i in range(12):
			td['zodiac_color_%s'%(i)]=self.colors["zodiac_icon_%s" %(i)]
		for deg in ASPECT_DEGREES:
			td['orb_color_%s'%(deg)]=self.colors["aspect_%s" %(deg)]
		td['stringTitle'] = "%s Timeline for %s"%(
			startdate.strftime("%B %Y"),self.name)
		self.pagesY = (1188 * self.pages)+10 #ten is buffer between self.pages
		if printing is None:
			td['svgWidth'] = 1050
			td['svgHeight'] = (td['svgWidth']/840.0)* self.pagesY
			td['viewbox'] = "0 0 840 %s" %(self.pagesY) 
		else:
			# add buffer of ten between self.pages
			self.pagesY += 10
			td['svgWidth'] = printing['width']
			td['svgHeight'] = printing['height']
			td['viewbox'] = "0 %s 840 1188" %( printing['pagenum']*(1188+10) )
		td['data'] = out
		#self.pages rectangles
		pagesRect,x,y,w,h="",0,0,840,1188
		for p in range(self.pages):
			if p == 0:
				offset=0
			else:
				offset=10
			pagesRect += '<rect x="%s" y="%s" width="%s" height="%s" style="fill: %s;" />'%(x,y+(p*1188)+offset,w,h,self.colors['paper_1'],)
		td['pagesRect'] = pagesRect
		#read and write template
		f=open(self.cfg.xml_svg_table)
		template=Template(f.read()).substitute(td)
		f.close()
		#svg document as text
		return template

	""" make graphic for cusp aspects """
	def makeCuspAspectsSVG(self, printing):
		#cusp aspects belong to the radix, self.aspects may hold the transit set
		aspects = self.db.getSettingsAspect('radix')
		#data
		out='<g transform="scale(1.5)">'
		xindent=50
		yindent=200
		box=14
		style='stroke:%s; stroke-width: 1px; stroke-opacity:.6; fill:none' % (self.colors['paper_0'],)
		textstyle="font-size: 11px; color: %s" % (self.colors['paper_0'],)
		#draw cusps
		for cusp in range(len(self.houses_degree_ut)):
				x = xindent - box
				y = yindent - (box*(cusp+1))
				out += '<text x="%s" y="%s" style="%s">%s</text>\n'%(x-30, y+box-5, textstyle, self.label['cusp']+" "+str(cusp+1))
		# add some space
		xindent += 32
		revr=range(len(self.planets))
		for a in revr:
			if 23 <= a <= 26:
				continue; #skip asc/dsc/mc/ic
			if a == 11 or a == 13 or a == 21 or a == 22:
				continue; #skip ?,?,intp. apogee, intp. perigee
			start=self.planets_degree_ut[a]
			#first planet 
			out += '<rect x="%s" y="%s" width="%s" height="%s" style="%s"/>\n' %(xindent,yindent,box,box,style)
			out += '<use transform="scale(0.4)" x="%s" \
					y="%s" xlink:href="#%s" />\n'%((xindent+2)*2.5,(yindent+1)*2.5, self.planets[a]['name'])
			yorb=yindent - box
			for b in range(12):
				end=self.houses_degree_ut[b]
				diff=self.degreeDiff(start,end)
				out += '<rect x="%s" y="%s" width="%s" height="%s" style="%s"/>\n'%(xindent,yorb,box,box,style)
				z = self.matchAspect(float(diff), aspects)
				if z is not None and aspects[z]['visible_grid'] == 1:
					out += '<use x="%s" y="%s" xlink:href="#orb%s" />\n'%(xindent,yorb+1,aspects[z]['degree'])
				yorb=yorb-box
			xindent += box
		#add cusp to cusp
		xindent = 50
		yindent = 400
		#draw cusps
		for cusp in range(len(self.houses_degree_ut)):
				x = xindent - box
				y = yindent - (box*(cusp+1))
				out += '<text x="%s" y="%s" style="%s">%s</text>\n'%(x-30, y+box-5, textstyle, self.label['cusp']+" "+str(cusp+1))
		#add some space
		xindent += 32
		for a in range(12):
			start=self.houses_degree_ut[a]
			#first planet 
			out += '<rect x="%s" y="%s" width="%s" height="%s" style="%s"/>\n' %(xindent,yindent,box,box,style)
			out += '<text x="%s" y="%s" style="%s">%s</text>\n'%((xindent+2), (yindent+box-4), textstyle, ""+str(a+1))
			yorb=yindent - box
			for b in range(12):
				end=self.houses_degree_ut[b]
				diff=self.degreeDiff(start,end)
				out += '<rect x="%s" y="%s" width="%s" height="%s" style="%s"/>\n'%(xindent,yorb,box,box,style)
				z = self.matchAspect(float(diff), aspects)
				if z is not None and aspects[z]['visible_grid'] == 1:
					out += '<use x="%s" y="%s" xlink:href="#orb%s" />\n'%(xindent,yorb+1,aspects[z]['degree'])
				yorb=yorb-box
			xindent += box	
		out += "</g>"
		#template
		td = {}
		td['paper_color_0']=self.colors["paper_0"]
		td['paper_color_1']=self.colors["paper_1"]
		for i in range(len(self.planets)):
			td['planets_color_%s'%(i)]=self.colors["planet_%s"%(i)]
		for i in range(12):
			td['zodiac_color_%s'%(i)]=self.colors["zodiac_icon_%s" %(i)]
		for deg in ASPECT_DEGREES:
			td['orb_color_%s'%(deg)]=self.colors["aspect_%s" %(deg)]
		td['stringTitle'] = "Cusp Aspects for %s"%(self.name)
		self.pages=1
		#ten is buffer between self.pages
		self.pagesY = (1188 * self.pages)+10
		if printing is None:
			td['svgWidth'] = 1050
			td['svgHeight'] = (td['svgWidth']/840.0)* self.pagesY
			td['viewbox'] = "0 0 840 %s" %( self.pagesY ) 
		else:
			td['svgWidth'] = printing['width']
			td['svgHeight'] = printing['height']
			td['viewbox'] = "0 %s 840 1188" %( printing['pagenum']*(1188+10) )
		td['data'] = out
		td['pagesRect'] = '<rect x="0" y="0" width="840" height="1188" style="fill: %s;" />' % (self.colors['paper_1'],)
		#read and write template
		f=open(self.cfg.xml_svg_table)
		template=Template(f.read()).substitute(td)
		f.close()
		#svg document as text
		return template

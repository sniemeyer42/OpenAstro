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
Symbols of the chart (bodies, signs, aspects) as small images for lists,
drawn from the symbol definitions of a chart SVG with its colours
"""

import re
from gi.repository import GLib, Gdk, Gtk, Rsvg
from astrochart.ui.widgets import renderSVG

SIGNS = ('aries','taurus','gemini','cancer','leo','virgo','libra','scorpio','sagittarius','capricorn','aquarius','pisces')

CSS = b"""
image.astro-symbol {
	background-color: white;
	border-radius: 6px;
	padding: 2px;
}
"""
_css_loaded = False

def loadCss():
	"""style of the symbol images: light chip, readable in dark themes too"""
	global _css_loaded
	if _css_loaded:
		return
	provider = Gtk.CssProvider()
	provider.load_from_data(CSS)
	Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
	_css_loaded = True

def symbolBox(name):
	"""size of the drawing area of a symbol in the chart template"""
	if name in SIGNS:
		return 32
	if name.startswith('orb') or name == 'retrograde':
		return 12
	return 24

class Symbols:
	"""cache of symbol images of the symbol definitions in a chart SVG"""

	def __init__(self):
		self.definitions = {}
		self.cache = {}

	def update(self, svg):
		"""take the symbols (with the colours of the chart) from an SVG document"""
		definitions = {}
		for block, name in re.findall(r'(<symbol id="([^"]+)">.*?</symbol>)', svg, re.S):
			definitions[name] = block
		if definitions != self.definitions:
			self.definitions = definitions
			self.cache = {}

	def texture(self, name, size, scale=1):
		"""image of symbol name, size x size pixels (times scale for HiDPI)"""
		key = (name, size, scale)
		if key not in self.cache:
			block = self.definitions.get(name)
			if block is None:
				return None
			box = symbolBox(name)
			svg = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
				'width="%s" height="%s" viewBox="0 0 %s %s">%s<use xlink:href="#%s"/></svg>' % (box, box, box, box, block, name))
			handle = Rsvg.Handle.new_from_data(svg.encode('utf-8'))
			surface = renderSVG(handle, size * scale, size * scale)
			self.cache[key] = Gdk.MemoryTexture.new(surface.get_width(), surface.get_height(),
				Gdk.MemoryFormat.B8G8R8A8_PREMULTIPLIED, GLib.Bytes.new(bytes(surface.get_data())), surface.get_stride())
		return self.cache[key]

	def picture(self, name, size=20, scale=1):
		"""image of a symbol on a light chip, size x size pixels"""
		loadCss()
		image = Gtk.Image.new_from_paintable(self.texture(name, size, scale))
		image.set_pixel_size(size)
		image.add_css_class('astro-symbol')
		image.set_valign(Gtk.Align.CENTER)
		return image

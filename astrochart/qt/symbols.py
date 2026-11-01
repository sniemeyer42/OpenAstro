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
Symbols of the chart (bodies, signs, aspects) as icons for lists, drawn
from the symbol definitions of a chart SVG with its colours
"""

import re
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from astrochart.qt.svg_view import svgRenderer

SIGNS = ('aries','taurus','gemini','cancer','leo','virgo','libra','scorpio','sagittarius','capricorn','aquarius','pisces')

def symbolBox(name):
	"""size of the drawing area of a symbol in the chart template"""
	if name in SIGNS:
		return 32
	if name.startswith('orb') or name == 'retrograde':
		return 12
	return 24

class Symbols:
	"""
	cache of symbol icons of the symbol definitions in a chart SVG; chip:
	symbols on a light background (colours of the classic wheel, made for
	white paper)
	"""

	def __init__(self):
		self.definitions = {}
		self.cache = {}
		self.chip = False

	def update(self, svg, chip=False):
		"""take the symbols (with the colours of the chart) from an SVG document"""
		definitions = {}
		for block, name in re.findall(r'(<symbol id="([^"]+)">.*?</symbol>)', svg, re.S):
			definitions[name] = block
		if definitions != self.definitions or chip != self.chip:
			self.definitions = definitions
			self.chip = chip
			self.cache = {}

	def pixmap(self, name, size=20, ratio=1.0):
		"""image of symbol name, size x size (logical) pixels"""
		key = (name, size, ratio)
		if key not in self.cache:
			block = self.definitions.get(name)
			if block is None:
				return None
			box = symbolBox(name)
			svg = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
				'width="%s" height="%s" viewBox="0 0 %s %s">%s<use xlink:href="#%s"/></svg>' % (box, box, box, box, block, name))
			pixels = max(1, int(round(size * ratio)))
			pixmap = QPixmap(pixels, pixels)
			pixmap.fill(Qt.GlobalColor.transparent)
			painter = QPainter(pixmap)
			painter.setRenderHint(QPainter.RenderHint.Antialiasing)
			margin = 0.0
			if self.chip:
				painter.setPen(Qt.PenStyle.NoPen)
				painter.setBrush(QColor('#ffffff'))
				painter.drawRoundedRect(QRectF(0, 0, pixels, pixels), pixels * 0.25, pixels * 0.25)
				margin = pixels * 0.1
			svgRenderer(svg).render(painter, QRectF(margin, margin, pixels - 2 * margin, pixels - 2 * margin))
			painter.end()
			pixmap.setDevicePixelRatio(ratio)
			self.cache[key] = pixmap
		return self.cache[key]

	def icon(self, name, size=20, ratio=1.0):
		pixmap = self.pixmap(name, size, ratio)
		return QIcon(pixmap) if pixmap is not None else QIcon()

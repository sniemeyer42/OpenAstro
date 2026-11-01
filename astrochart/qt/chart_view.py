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
Interactive chart wheel: tooltips on the bodies, a click selects a body and
highlights its aspects
"""

import math
from html import escape
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QToolTip
from astrochart.chart.data import formatDegree
from astrochart.constants import RADIUS, WHEEL_MARGIN
from astrochart.qt.svg_view import SvgView

SIGN_GLYPHS = dict(zip(('aries','taurus','gemini','cancer','leo','virgo','libra','scorpio','sagittarius','capricorn','aquarius','pisces'),
	'♈♉♊♋♌♍♎♏♐♑♒♓'))

def involves(aspect, side, ident):
	"""True if the aspect row has the body (side, ident)"""
	transit = side == 'transit'
	return (aspect['first']['id'], aspect['first']['transit']) == (ident, transit) or \
		(aspect['second']['id'], aspect['second']['transit']) == (ident, transit)

class ChartView(SvgView):
	"""
	wheel of chart (calculated and drawn), on_select(side, id) or
	on_select(None, None); on_wheel(event) may take the mouse wheel (True
	if it did), Ctrl + mouse wheel always zooms
	"""

	def __init__(self, svg, chart, on_select, parent=None):
		super().__init__(svg, fit='page', parent=parent)
		self.chart = chart
		self.on_select = on_select
		self.on_wheel = None
		self.viewport().setMouseTracking(True)

	def wheelEvent(self, event):
		if not event.modifiers() & Qt.KeyboardModifier.ControlModifier and self.on_wheel is not None and self.on_wheel(event):
			event.accept()
			return
		super().wheelEvent(event)

	def wheelPoint(self, x, y):
		"""viewport point in coordinates of the wheel template"""
		rect = self.drawingRect()
		extent = 2.0 * (RADIUS + WHEEL_MARGIN)
		return -WHEEL_MARGIN + (x - rect.x()) * extent / rect.width(), -WHEEL_MARGIN + (y - rect.y()) * extent / rect.height()

	def glyphAt(self, x, y):
		"""drawn body symbol at the viewport point, None if there is none"""
		wx, wy = self.wheelPoint(x, y)
		best, distance = None, None
		for glyph in getattr(self.chart, 'glyphs', []):
			d = math.hypot(glyph['x'] - wx, glyph['y'] - wy)
			if d <= glyph['r'] + 3 and (distance is None or d < distance):
				best, distance = glyph, d
		return best

	def mouseMoveEvent(self, event):
		position = event.position()
		if self.glyphAt(position.x(), position.y()):
			self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
		else:
			self.viewport().unsetCursor()
		super().mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			position = event.position()
			glyph = self.glyphAt(position.x(), position.y())
			if glyph is None:
				self.on_select(None, None)
			else:
				self.on_select(glyph['side'], glyph['id'])
		super().mouseReleaseEvent(event)

	def viewportEvent(self, event):
		if event.type() == QEvent.Type.ToolTip:
			glyph = self.glyphAt(event.pos().x(), event.pos().y())
			if glyph is None:
				QToolTip.hideText()
				event.ignore()
			else:
				QToolTip.showText(event.globalPos(), self.tooltipHtml(glyph['side'], glyph['id']), self.viewport())
			return True
		return super().viewportEvent(event)

	def tooltipHtml(self, side, ident):
		"""name, side, position, house and the closest aspects of a body"""
		chart = self.chart
		rows = [row for row in chart.bodyRows(transit=(side == 'transit')) if row['id'] == ident]
		if not rows:
			return ''
		row = rows[0]
		if chart.type == "Transit":
			where = _('Radix') if side == 'radix' else (_('Partner') if chart.synastry else _('Transit'))
			title = '<b>%s</b>&nbsp;&nbsp;<small>%s</small>' % (escape(row['label']), escape(where))
		else:
			title = '<b>%s</b>' % escape(row['label'])
		lines = [title, '%s %s%s&nbsp;&nbsp;·&nbsp;&nbsp;%s %s' % (SIGN_GLYPHS.get(row['sign'], ''), row['degree'],
			' ℞' if row['retrograde'] else '', escape(_('House')), row['house'])]
		aspects = [a for a in chart.aspectRows() if involves(a, side, ident)]
		for aspect in aspects[:6]:
			other = aspect['second'] if (aspect['first']['id'], aspect['first']['transit']) == (ident, side == 'transit') else aspect['first']
			lines.append('%s %s&nbsp;&nbsp;<small>%s</small>' % (escape(aspect['name']),
				escape(other['label']), formatDegree(aspect['orb'], seconds=False)))
		if len(aspects) > 6:
			lines.append('<small>+%d</small>' % (len(aspects) - 6))
		return '<p style="white-space: nowrap;">%s</p>' % '<br>'.join(lines)

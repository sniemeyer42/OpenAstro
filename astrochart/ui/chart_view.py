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
from gi.repository import GLib, Gtk
from astrochart.chart.data import formatDegree
from astrochart.constants import RADIUS, WHEEL_MARGIN
from astrochart.ui.widgets import ViewSVG

SIGN_GLYPHS = dict(zip(('aries','taurus','gemini','cancer','leo','virgo','libra','scorpio','sagittarius','capricorn','aquarius','pisces'),
	'♈♉♊♋♌♍♎♏♐♑♒♓'))

class ChartView(ViewSVG):
	"""wheel of chart (calculated and drawn), on_select(side, id) or on_select(None, None)"""

	def __init__(self, svg, chart, on_select):
		super().__init__(svg, fit='page')
		self.chart = chart
		self.on_select = on_select
		self.set_has_tooltip(True)
		self.connect('query-tooltip', self.onQueryTooltip)
		click = Gtk.GestureClick()
		click.connect('released', self.onClick)
		self.add_controller(click)
		motion = Gtk.EventControllerMotion()
		motion.connect('motion', self.onMotion)
		self.add_controller(motion)

	def wheelPoint(self, x, y):
		"""widget point in coordinates of the wheel template"""
		width, height = self.drawingSize()
		x0 = max(0.0, (self.get_width() - width) / 2.0)
		y0 = max(0.0, (self.get_height() - height) / 2.0)
		extent = 2.0 * (RADIUS + WHEEL_MARGIN)
		return -WHEEL_MARGIN + (x - x0) * extent / width, -WHEEL_MARGIN + (y - y0) * extent / height

	def glyphAt(self, x, y):
		"""drawn body symbol at the widget point, None if there is none"""
		wx, wy = self.wheelPoint(x, y)
		best, distance = None, None
		for glyph in getattr(self.chart, 'glyphs', []):
			d = math.hypot(glyph['x'] - wx, glyph['y'] - wy)
			if d <= glyph['r'] + 3 and (distance is None or d < distance):
				best, distance = glyph, d
		return best

	def onMotion(self, controller, x, y):
		self.set_cursor_from_name('pointer' if self.glyphAt(x, y) else None)

	def onClick(self, gesture, n_press, x, y):
		glyph = self.glyphAt(x, y)
		if glyph is None:
			self.on_select(None, None)
		else:
			self.on_select(glyph['side'], glyph['id'])

	def onQueryTooltip(self, widget, x, y, keyboard_mode, tooltip):
		glyph = self.glyphAt(x, y)
		if glyph is None:
			return False
		tooltip.set_markup(self.tooltipMarkup(glyph['side'], glyph['id']))
		return True

	def tooltipMarkup(self, side, ident):
		"""name, side, position, house and the closest aspects of a body"""
		chart = self.chart
		rows = [row for row in chart.bodyRows(transit=(side == 'transit')) if row['id'] == ident]
		if not rows:
			return ''
		row = rows[0]
		if chart.type == "Transit":
			where = _('Radix') if side == 'radix' else (_('Partner') if chart.synastry else _('Transit'))
			title = '<b>%s</b>  <small>%s</small>' % (GLib.markup_escape_text(row['label']), GLib.markup_escape_text(where))
		else:
			title = '<b>%s</b>' % GLib.markup_escape_text(row['label'])
		lines = [title, '%s %s%s  ·  %s %s' % (SIGN_GLYPHS.get(row['sign'], ''), row['degree'],
			' ℞' if row['retrograde'] else '', GLib.markup_escape_text(_('House')), row['house'])]
		aspects = [a for a in chart.aspectRows() if self.involves(a, side, ident)]
		for aspect in aspects[:6]:
			other = aspect['second'] if (aspect['first']['id'], aspect['first']['transit']) == (ident, side == 'transit') else aspect['first']
			lines.append('%s %s  <small>%s</small>' % (GLib.markup_escape_text(aspect['name']),
				GLib.markup_escape_text(other['label']), formatDegree(aspect['orb'], seconds=False)))
		if len(aspects) > 6:
			lines.append('<small>+%d</small>' % (len(aspects) - 6))
		return '\n'.join(lines)

	@staticmethod
	def involves(aspect, side, ident):
		"""True if the aspect row has the body (side, ident)"""
		transit = side == 'transit'
		return (aspect['first']['id'], aspect['first']['transit']) == (ident, transit) or \
			(aspect['second']['id'], aspect['second']['transit']) == (ident, transit)

	def replaceSVG(self, svg):
		"""new drawing of the same chart, the zoom stays"""
		scale = self.scale
		self.setupSVG(svg)
		self.setScale(scale)

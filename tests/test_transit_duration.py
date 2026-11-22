"""Transits listed by their duration: short-term (moon, sun, mercury, venus,
mars, ...) and long-term (jupiter and slower, nodes, lilith, ...)."""
import builtins
import gettext
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not hasattr(builtins, '_'):
	builtins._ = lambda text: text
from astrochart.chart.data import ChartDataMixin, TRANSIT_DURATIONS, durationTitle, transitDuration
from astrochart.chart.svg_print import PrintSVGMixin
from astrochart.chart.svg_tables import groupPages

#settings_planet names by id
NAMES = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn',
	'uranus', 'neptune', 'pluto', 'mean node', 'true node', 'mean apogee', 'osc. apogee',
	'earth', 'chiron', 'pholus', 'ceres', 'pallas', 'juno', 'vesta',
	'intp. apogee', 'intp. perigee', 'Asc', 'Mc', 'Dsc', 'Ic', 'day pars',
	'night pars', 'south node', 'marriage pars', 'black sun', 'vulcanus', 'persephone',
	'true lilith']
SHORT = {'sun', 'moon', 'mercury', 'venus', 'mars', 'earth', 'Asc', 'Mc', 'Dsc', 'Ic',
	'day pars', 'night pars', 'marriage pars'}
#catalogs that translate the interface
UI_LANGUAGES = 'ar bg ca cs da de el eo es fi fr hu it ja nb nds nl pl pt_BR rom ru sv uk'.split()
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def body(ident, transit):
	return {'id': ident, 'symbol': NAMES[ident], 'label': NAMES[ident], 'transit': transit}


def transitRow(transit, radix, orb, synastry=False):
	"""aspect row as aspectRows makes it: transits name the transit body first, synastries the radix body"""
	first, second = body(transit, True), body(radix, False)
	if synastry:
		first, second = second, first
	return {'degree': 90, 'name': 'square', 'orb': orb, 'first': first, 'second': second}


class Chart(ChartDataMixin, PrintSVGMixin):
	def __init__(self, rows, kind='Transit', synastry=False, solar_return=False):
		self.rows = rows
		self.type = kind
		self.synastry = synastry
		self.solar_return = solar_return

	def aspectRows(self):
		return self.rows


class TransitDurationTest(unittest.TestCase):

	def test_bodies_of_the_request(self):
		# 'transits of moon, sun, mercury, venus etc. short-running, of uranus,
		# lunar nodes, lilith, jupiter etc. long-running'
		for name in ('moon', 'sun', 'mercury', 'venus', 'mars'):
			self.assertEqual(transitDuration(NAMES.index(name)), 'short', name)
		# every lilith is long-term, also the osculating one (and the intp.
		# perigee): they swing around the lunar apsides, but move on with them
		for name in ('uranus', 'mean node', 'true node', 'south node', 'mean apogee', 'osc. apogee',
				'intp. apogee', 'intp. perigee', 'true lilith', 'jupiter', 'saturn', 'neptune', 'pluto', 'chiron'):
			self.assertEqual(transitDuration(NAMES.index(name)), 'long', name)

	def test_every_body(self):
		self.assertEqual({NAMES[i] for i in range(len(NAMES)) if transitDuration(i) == 'short'}, SHORT)
		self.assertEqual(TRANSIT_DURATIONS, ('short', 'long'))
		self.assertNotEqual(durationTitle('short'), durationTitle('long'))

	def titles(self, language):
		"""headings of both groups in a language, the catalog of the repository installed as the program does"""
		saved = builtins._
		builtins._ = gettext.translation('openastro', os.path.join(REPO, 'locale'), [language]).gettext
		try:
			return durationTitle('short'), durationTitle('long')
		finally:
			builtins._ = saved

	def test_headings_translated(self):
		# the words of the request
		self.assertEqual(self.titles('de'), ('Kurzläufig', 'Langläufig'))
		english = self.titles('en')
		self.assertEqual(english, ('Short-term', 'Long-term'))
		for language in UI_LANGUAGES:
			with self.subTest(language=language):
				short, long = self.titles(language)
				self.assertNotIn(short, english)
				self.assertNotIn(long, english)
				self.assertNotEqual(short, long)

	def test_groups_of_transits(self):
		rows = [transitRow(5, 0, 0.1), transitRow(1, 3, -0.2), transitRow(12, 1, 0.3), transitRow(0, 9, 0.4),
			transitRow(23, 5, -0.5), transitRow(10, 10, 0.6)]
		groups = Chart(rows).aspectGroups(rows)
		self.assertEqual([duration for duration, group in groups], ['short', 'long'])
		self.assertEqual([row['first']['id'] for row in groups[0][1]], [1, 0, 23])
		self.assertEqual([row['first']['id'] for row in groups[1][1]], [5, 12, 10])

	def test_empty_group_left_out(self):
		rows = [transitRow(7, 0, 0.1), transitRow(10, 1, 0.2)]
		self.assertEqual(Chart(rows).aspectGroups(rows), [('long', rows)])
		self.assertEqual(Chart([]).aspectGroups([]), [])

	def test_body_of_the_transit_side(self):
		# a radix moon aspected by transit saturn is a long-term transit
		rows = [transitRow(6, 1, 0.1)]
		rows[0]['first'], rows[0]['second'] = rows[0]['second'], rows[0]['first']
		self.assertEqual(Chart(rows).aspectGroups(rows), [('long', rows)])

	def test_other_charts_not_grouped(self):
		rows = [transitRow(5, 0, 0.1), transitRow(1, 3, -0.2)]
		self.assertEqual(Chart(rows, synastry=True).aspectGroups(rows), [(None, rows)])
		self.assertEqual(Chart(rows, solar_return=True).aspectGroups(rows), [(None, rows)])
		self.assertEqual(Chart(rows, kind='Radix').aspectGroups(rows), [(None, rows)])
		self.assertEqual(Chart([], kind='Radix').aspectGroups([]), [(None, [])])

	def test_group_pages(self):
		self.assertEqual(groupPages([], 10), [[]])
		for per_page in range(2, 9):
			for short in range(0, 13):
				for long in range(0, 13):
					groups = [(d, ['%s%d' % (d, k) for k in range(n)]) for d, n in (('short', short), ('long', long)) if n]
					pages = groupPages(groups, per_page)
					with self.subTest(per_page=per_page, short=short, long=long):
						keys = [key for page in pages for duration, key in page if key is not None]
						self.assertEqual(keys, [key for d, group in groups for key in group])
						for page in pages:
							self.assertLessEqual(len(page), per_page)
							if groups:
								self.assertIsNone(page[0][1], 'a page starts with a heading')
								self.assertIsNotNone(page[-1][1], 'no heading at the foot of a page')
							#every key under the heading of its group shown above it on the page
							shown = None
							for duration, key in page:
								if key is None:
									shown = duration
								else:
									self.assertIsNotNone(shown, 'a key under a heading')
									self.assertTrue(key.startswith(shown), (key, shown))
						headings = [duration for page in pages for duration, key in page if key is None]
						self.assertEqual(sorted(set(headings), key=TRANSIT_DURATIONS.index), [d for d, group in groups])

	def test_print_headings(self):
		def lines(chart, per_column):
			#texts of the aspects (x, y, text) of the printed page
			out = []
			chart.printAspects(out, 0, 0, 200, 26 + 16 * per_column + 5)
			found = []
			for entry in out:
				match = re.match(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*>(.*)</text>', entry)
				if match:
					found.append((float(match.group(1)), float(match.group(2)), match.group(3)))
			return found[1:]
		short, long = durationTitle('short'), durationTitle('long')
		# three short-term transits: the long-term heading would be the last
		# line of the first column, it begins the second one
		rows = [transitRow(1, i, 0.1 * i) for i in range(3)] + [transitRow(5, i, 0.5 + 0.1 * i) for i in range(4)]
		found = lines(Chart(rows), 5)
		headings = [(x, y) for x, y, content in found if content in (short, long)]
		self.assertEqual([content for x, y, content in found if content in (short, long)], [short, long])
		self.assertEqual(headings, [(0.0, 42.0), (100.0, 42.0)])
		self.assertEqual(len([content for x, y, content in found if content not in (short, long)]), len(rows))
		# four short-term transits, seven lines a column: both headings in the first column
		rows = [transitRow(1, i, 0.1 * i) for i in range(4)] + [transitRow(5, i, 0.5 + 0.1 * i) for i in range(4)]
		found = lines(Chart(rows), 7)
		self.assertEqual([(x, y) for x, y, content in found if content in (short, long)], [(0.0, 42.0), (0.0, 122.0)])
		# more than fit: the count of the shown aspects
		out = []
		Chart(rows).printAspects(out, 0, 0, 200, 26 + 16 * 3 + 5)
		self.assertIn('4 / 8', ''.join(out))
		# not grouped: no headings, all lines aspects
		found = lines(Chart(rows, synastry=True), 6)
		self.assertFalse([content for x, y, content in found if content in (short, long)])
		self.assertEqual(len(found), len(rows))

	def test_print_closest_aspects(self):
		# more aspects than fit: the closest ones are printed, then grouped; 40
		# wide short-term transits must not push the closer long-term ones off
		rows = [transitRow(5 + k % 5, k, 0.01 * (k + 1)) for k in range(5)] + \
			[transitRow(k % 5, k % 30, 1.0 + 0.01 * k) for k in range(40)]
		out = []
		Chart(rows).printAspects(out, 0, 0, 400, 26 + 16 * 21 + 5)
		page = ''.join(out)
		orbs = re.findall(r'>(-?\d\d°\d\d′)</text>', page)
		self.assertIn(durationTitle('long'), page)
		self.assertIn('40 / 45', page)
		self.assertEqual(len(orbs), 40)
		#the five long-term transits and the 35 closest short-term ones (orbs 1.00 to 1.34)
		self.assertIn('00°01′', orbs)
		self.assertIn('00°03′', orbs)
		self.assertIn('01°20′', orbs)
		self.assertNotIn('01°21′', orbs)
		# everything fits: all of them, both headings
		out = []
		Chart(rows[:30]).printAspects(out, 0, 0, 400, 26 + 16 * 21 + 5)
		page = ''.join(out)
		self.assertEqual(len(re.findall(r'>(-?\d\d°\d\d′)</text>', page)), 30)
		self.assertIn(durationTitle('short'), page)
		self.assertNotIn(' / 30', page)


if __name__ == '__main__':
	unittest.main()

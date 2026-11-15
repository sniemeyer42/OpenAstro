"""Applying and separating aspects, including wraparound and retrograde motion."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from astrochart.chart.data import ChartDataMixin, formatDegree, signedAspectOrb
from astrochart.chart.svg_aspects import AspectsSVGMixin


class Chart(ChartDataMixin, AspectsSVGMixin):
	def __init__(self, positions, speeds):
		self.type = 'Radix'
		self.synastry = False
		self.planets_degree_ut = positions
		self.planets_speed = speeds
		self.planets = [{'name': str(i), 'label': str(i), 'visible_aspect_grid': 1}
			for i in range(len(positions))]
		self.aspects = [{'degree': d, 'name': str(d), 'orb': 10, 'visible': 1, 'visible_grid': 1}
			for d in (0, 60, 90, 120, 180)]

	@staticmethod
	def svgSafeHref(name):
		return name

	@staticmethod
	def degreeDiff(start, end):
		return abs((end - start + 180.0) % 360.0 - 180.0)


class AspectMotionTest(unittest.TestCase):
	def test_signed_orbs(self):
		# Expected signs follow whether the instantaneous motion makes the
		# deviation from the exact aspect smaller (positive) or larger (minus).
		cases = [
			('direct applying', 0, 89, 90, 0, 1, 1),
			('direct separating', 0, 91, 90, 0, 1, -1),
			('retrograde applying', 0, 91, 90, 0, -1, 1),
			('retrograde separating', 0, 89, 90, 0, -1, -1),
			('faster first body applying', 0, 91, 90, 2, 1, 1),
			('both retrograde separating', 0, 91, 90, -2, -1, -1),
			('waning applying', 0, 271, 90, 0, -1, 1),
			('waning separating', 0, 269, 90, 0, -1, -1),
			('wrap conjunction applying', 359, 1, 0, 2, 1, 2),
			('wrap conjunction separating', 359, 1, 0, 1, 2, -2),
			('opposition applying', 0, 179, 180, 0, 1, 1),
			('opposition separating', 0, 181, 180, 0, 1, -1),
			('equal speeds', 0, 91, 90, 1, 1, 1),
			('exact aspect', 0, 90, 90, 0, 1, 0),
		]
		for name, start, end, degree, first_speed, second_speed, expected in cases:
			with self.subTest(name=name):
				self.assertEqual(signedAspectOrb(start, end, degree, first_speed, second_speed), expected)
				self.assertEqual(signedAspectOrb(end, start, degree, second_speed, first_speed), expected)

	def test_negative_degree_format(self):
		self.assertEqual(formatDegree(-1.5, seconds=False), '-01°30′')
		self.assertEqual(formatDegree(-0.5, seconds=False), '-00°30′')
		self.assertEqual(formatDegree(-0.0001, seconds=False), '-00°00′')
		self.assertEqual(formatDegree(-1.9999, seconds=False), '-02°00′')
		self.assertEqual(formatDegree(-1.5), '-01°30′00″')
		self.assertEqual(formatDegree(1.5, seconds=False), '01°30′')
		self.assertEqual(formatDegree(0, seconds=False), '00°00′')

	def test_radix_list_stays_sorted_by_absolute_orb(self):
		chart = Chart([0, 89, 122], [0, 1, 1])
		rows = chart.aspectRows()
		self.assertEqual([row['orb'] for row in rows], [1, -2])

	def test_transit_keeps_radix_fixed(self):
		chart = Chart([0], [2])
		chart.type = 'Transit'
		chart.t_planets_degree_ut = [91]
		chart.t_planets_speed = [1]
		chart.atgrid = [{'p1': 0, 'p2': 0, 'aid': 2, 'diff': 91}]
		row = chart.aspectRows()[0]
		self.assertEqual(row['orb'], -1)
		self.assertTrue(row['first']['transit'])
		self.assertFalse(row['second']['transit'])
		chart.t_planets_speed = [-1]
		self.assertEqual(chart.aspectRows()[0]['orb'], 1)

	def test_synastry_uses_both_speeds(self):
		chart = Chart([0], [2])
		chart.type = 'Transit'
		chart.synastry = True
		chart.t_planets_degree_ut = [91]
		chart.t_planets_speed = [1]
		chart.atgrid = [{'p1': 0, 'p2': 0, 'aid': 2, 'diff': 91}]
		row = chart.aspectRows()[0]
		self.assertEqual(row['orb'], 1)
		self.assertFalse(row['first']['transit'])
		self.assertTrue(row['second']['transit'])


if __name__ == '__main__':
	unittest.main()

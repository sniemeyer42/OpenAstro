#!/usr/bin/env python3
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
Render a fixed set of charts and tables as SVG files into OUTDIR.

	HOME=$(mktemp -d) xvfb-run python3 tests/golden.py OUTDIR

The output is deterministic: two runs (or two versions of the program that
should draw the same) can be compared with `diff -r OUTDIR1 OUTDIR2`.
"""
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import start_application

def scenarios(app):
	"""yield (name, svg text) for every chart of the test set"""
	app = app.chart
	if not hasattr(app, 'label'):
		app.label = app.db.getLabel()

	def natal():
		app.name = 'Test Natal'
		app.year, app.month, app.day, app.hour = 1980, 3, 30, 11.0
		app.geolon, app.geolat, app.altitude = 13.4, 52.52, 25
		app.location = 'Berlin, Germany'
		app.timezone = 1.0
		app.countrycode = 'DE'
		app.timezonestr = 'Europe/Berlin'
		app.geonameid = None
		app.utcToLocal()
		app.type = 'Radix'; app.charttype = app.label['radix']
		app.transit = False; app.synastry = False

	# second event as record of the event database
	partner = {'name': 'Partner', 'year': 1985, 'month': 3, 'day': 20, 'hour': 8.0,
		'geolon': 9.99, 'geolat': 53.55, 'altitude': 25, 'location': 'Hamburg, Germany', 'timezone': 1.0}

	def chart(printing=None):
		return app.makeSVG(printing=printing)

	natal(); app.makeSVG()
	yield 'radix', chart()
	yield 'radix_print', chart(printing={'width': 1200, 'height': 850})
	natal(); app.makeSVG()
	app.type = 'Transit'; app.transit = True; app.synastry = False
	app.t_year, app.t_month, app.t_day, app.t_hour = 2026, 10, 15, 12.0
	app.t_geolon, app.t_geolat, app.t_altitude, app.t_timezone = 13.4, 52.52, 25, 1.0
	app.charttype = 'Transit (2026-10-15 13:00)'
	yield 'transit', chart()
	natal(); app.setSynastry(partner)
	yield 'synastry', chart()
	natal(); app.setComposite(partner)
	app.charttype = 'Composite (Partner)'
	yield 'composite', chart()
	# combine: midpoint in time and space
	natal(); app.setCombine(partner)
	yield 'combine', chart()
	natal(); app.makeSVG(); app.localToSolar(2026)
	yield 'solar', chart()
	natal(); app.makeSVG(); app.localToSecondaryProgression(datetime.datetime(2026, 10, 15, 12, 0))
	yield 'progression', chart()
	natal(); app.makeSVG()
	yield 'timeline', app.makeTimelineSVG(None, 2026, 10)
	yield 'cuspaspects', app.makeCuspAspectsSVG(None)
	# every body visible
	n = len(app.db.getSettingsPlanet())
	app.db.setSettingsPlanet('radix', [{'id': i, 'visible': 1, 'visible_aspect_line': 1, 'visible_aspect_grid': 1} for i in range(n)])
	for ctype in ('transit', 'synastry'):
		app.db.setSettingsPlanet(ctype, [{'id': i, 'visible': 1, 'visible_transit': 1} for i in range(n)])
	natal(); app.makeSVG()
	yield 'radix_all', chart()
	natal(); app.setSynastry(partner)
	yield 'synastry_all', chart()

def main(outdir):
	os.makedirs(outdir, exist_ok=True)
	app, run = start_application()
	def step(app):
		count = 0
		for name, svg in scenarios(app):
			with open(os.path.join(outdir, name + '.svg'), 'w') as f:
				f.write(svg)
			count += 1
		print('golden: %d files written to %s' % (count, outdir), flush=True)
		app.quit()
	return run(step)

if __name__ == '__main__':
	if len(sys.argv) != 2:
		sys.exit(__doc__)
	sys.exit(main(os.path.abspath(sys.argv[1])))

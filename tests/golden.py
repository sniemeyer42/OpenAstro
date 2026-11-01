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

	def partner():
		app.t_name = 'Partner'
		app.t_year, app.t_month, app.t_day, app.t_hour = 1985, 3, 20, 8.0
		app.t_geolon, app.t_geolat, app.t_altitude = 9.99, 53.55, 25
		app.t_location = 'Hamburg, Germany'
		app.t_timezone = 1.0

	def read(path):
		with open(path) as f:
			return f.read()

	def chart(printing=None):
		app.makeSVG(printing=printing)
		return read(app.cfg.tempfilename if printing is None else app.cfg.tempfilenameprint)

	natal(); app.makeSVG()
	yield 'radix', chart()
	yield 'radix_print', chart(printing={'width': 1200, 'height': 850})
	natal(); app.makeSVG()
	app.type = 'Transit'; app.transit = True; app.synastry = False
	app.t_year, app.t_month, app.t_day, app.t_hour = 2026, 10, 15, 12.0
	app.t_geolon, app.t_geolat, app.t_altitude, app.t_timezone = 13.4, 52.52, 25, 1.0
	app.charttype = 'Transit (2026-10-15 13:00)'
	yield 'transit', chart()
	natal(); partner()
	app.type = 'Transit'; app.transit = True; app.synastry = True
	app.charttype = '%s (%s)' % (app.label['synastry'], app.t_name)
	yield 'synastry', chart()
	natal(); partner()
	app.type = 'Composite'; app.charttype = 'Composite (Partner)'
	yield 'composite', chart()
	# combine: midpoint in time and space as in the database selection
	natal(); partner()
	h, m, s = app.decHour(app.hour); dt1 = datetime.datetime(app.year, app.month, app.day, h, m, s)
	h, m, s = app.decHour(app.t_hour); dt2 = datetime.datetime(app.t_year, app.t_month, app.t_day, h, m, s)
	combine = dt1 + (dt2 - dt1) // 2
	app.type = 'Combine'
	app.c_geolon = (app.geolon + app.t_geolon) / 2.0
	app.c_geolat = (app.geolat + app.t_geolat) / 2.0
	app.c_altitude = (app.t_altitude + app.altitude) / 2.0
	app.c_year, app.c_month, app.c_day = combine.year, combine.month, combine.day
	app.c_hour = app.decHourJoin(combine.hour, combine.minute, combine.second)
	app.charttype = '%s (%s)' % (app.label['combine'], app.t_name)
	app.year, app.month, app.day, app.hour = app.c_year, app.c_month, app.c_day, app.c_hour
	app.geolat, app.geolon = app.c_geolat, app.c_geolon
	app.utcToLocal()
	yield 'combine', chart()
	natal(); app.makeSVG(); app.localToSolar(2026)
	yield 'solar', chart()
	natal(); app.makeSVG(); app.localToSecondaryProgression(datetime.datetime(2026, 10, 15, 12, 0))
	yield 'progression', chart()
	natal(); app.makeSVG()
	app.makeTimelineSVG(None, 2026, 10)
	yield 'timeline', read(app.cfg.tempfilenametable)
	app.makeCuspAspectsSVG(None)
	yield 'cuspaspects', read(app.cfg.tempfilenametable)
	# every body visible
	n = len(app.db.getSettingsPlanet())
	app.db.setSettingsPlanet('radix', [{'id': i, 'visible': 1, 'visible_aspect_line': 1, 'visible_aspect_grid': 1} for i in range(n)])
	for ctype in ('transit', 'synastry'):
		app.db.setSettingsPlanet(ctype, [{'id': i, 'visible': 1, 'visible_transit': 1} for i in range(n)])
	natal(); app.makeSVG()
	yield 'radix_all', chart()
	natal(); partner(); app.type = 'Transit'; app.transit = True; app.synastry = True
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

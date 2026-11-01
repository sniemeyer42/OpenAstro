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
Run the golden chart set and the GUI smoke test in fresh scratch homes.

	xvfb-run python3 -m unittest discover -s tests -v
"""
import os
import re
import sys
import json
import shutil
import tempfile
import unittest
import subprocess
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))

def run_tool(args, home):
	env = dict(os.environ, HOME=home, PYTHONDONTWRITEBYTECODE='1')
	return subprocess.run([sys.executable] + args, env=env, capture_output=True, text=True, timeout=600)

@unittest.skipUnless(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'), 'needs a display (xvfb-run)')
class ProgramTest(unittest.TestCase):

	def setUp(self):
		self.home = tempfile.mkdtemp(prefix='openastro-test-')

	def tearDown(self):
		shutil.rmtree(self.home, ignore_errors=True)

	def test_golden_charts(self):
		out = os.path.join(self.home, 'golden')
		result = run_tool([os.path.join(HERE, 'golden.py'), out], self.home)
		self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
		files = sorted(os.listdir(out))
		self.assertEqual(len(files), 12, files)
		for name in files:
			with open(os.path.join(out, name)) as f:
				svg = f.read()
			ET.fromstring(svg)
			ids = set(re.findall(r'id="([^"]+)"', svg))
			refs = set(re.findall(r'xlink:href="#([^"]+)"', svg))
			self.assertFalse(refs - ids, '%s: unresolved symbols %s' % (name, sorted(refs - ids)))

	def test_gui_smoke(self):
		out = os.path.join(self.home, 'smoke.json')
		result = run_tool([os.path.join(HERE, 'smoke.py'), out], self.home)
		self.assertEqual(result.returncode, 0, result.stdout[-3000:] + result.stderr[-3000:])
		with open(out) as f:
			data = json.load(f)
		self.assertEqual(data['exceptions'], [])
		for r in data['results']:
			if r['step'].split()[0] in ('radix', 'transit', 'zoom', 'maximize'):
				continue
			self.assertTrue(r['new'], '%s opened no window' % r['step'])

if __name__ == '__main__':
	unittest.main()

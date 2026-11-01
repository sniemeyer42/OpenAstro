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
Dialog 'Settings > Planets & Angles': shown bodies per chart type
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QGridLayout, QLabel, QVBoxLayout, QWidget
from astrochart.constants import ASPECT_CHART_TYPES, PLANET_DEFAULT_VISIBLE, PLANET_FIRST_ANGLE, PLANET_FIRST_POINT, PLANET_TRANSIT_HIDDEN
from astrochart.qt.dialog import AstroDialog, Button, captionLabel, chartTypeTabs, heading
from astrochart.util import aspectFlag, dprint

class PlanetSettingsDialog(AstroDialog):
	"""one page per chart type, a row with check boxes per body"""

	def __init__(self, window):
		super().__init__(window, _("Planets & Angles Settings"))
		self.resize(560, 720)
		#check boxes (planet setting, heading): radix with symbol, aspect line and
		#aspect grid, transit and synastry per side
		columns = {
			'radix': [('visible', _('Symbol')), ('visible_aspect_line', _('Aspect Line')),
				('visible_aspect_grid', _('Aspect Grid'))],
			'transit': [('visible', _('Radix')), ('visible_transit', _('Transit'))],
			'synastry': [('visible', _('Radix')), ('visible_transit', _('Partner'))]
			}
		groups = {0: _('Planet Label'), PLANET_FIRST_ANGLE: _('Angle Label'), PLANET_FIRST_POINT: _('Point Label')}
		ratio = self.devicePixelRatioF()
		self.data = {}
		self.saved = {}
		pages = {}
		for ctype in ASPECT_CHART_TYPES:
			page = QWidget()
			grid = QGridLayout(page)
			grid.setHorizontalSpacing(16)
			rows = []
			saved = []
			line = 0
			for planet in self.db.getSettingsPlanet(ctype):
				pid = planet['id']
				#group of planets, angles and sensitive points with column headings
				if pid in groups:
					if line:
						grid.setRowMinimumHeight(line, 12)
						line += 1
					grid.addWidget(heading(groups[pid]), line, 0, 1, 2)
					for k, (key, text) in enumerate(columns[ctype]):
						grid.addWidget(captionLabel(text), line, 2 + k)
					line += 1
				symbol = QLabel()
				pixmap = window.symbols.pixmap(self.chart.svgSafeHref(planet['name']), 18, ratio)
				if pixmap is not None:
					symbol.setPixmap(pixmap)
				grid.addWidget(symbol, line, 0)
				grid.addWidget(QLabel(planet['label']), line, 1)
				widgets = {'id': pid}
				values = {'id': pid}
				for k, (key, text) in enumerate(columns[ctype]):
					values[key] = aspectFlag(planet[key], 0)
					check = QCheckBox()
					check.setChecked(values[key] == 1)
					check.setToolTip(text)
					grid.addWidget(check, line, 2 + k, Qt.AlignmentFlag.AlignCenter)
					widgets[key] = check
				rows.append(widgets)
				saved.append(values)
				line += 1
			grid.setColumnStretch(1, 1)
			grid.setRowStretch(line, 1)
			pages[ctype] = page
			self.data[ctype] = rows
			self.saved[ctype] = saved
		layout = QVBoxLayout(self)
		self.tabs = chartTypeTabs(pages, self.chart)
		layout.addWidget(self.tabs, 1)
		layout.addWidget(self.buttonBox(Button.RestoreDefaults | Button.Ok | Button.Apply | Button.Cancel,
			{Button.RestoreDefaults: self.default, Button.Ok: lambda: self.submit(close=True), Button.Apply: lambda: self.submit(close=False)}))

	def default(self):
		#reset the widgets of the current page only, saved with apply or ok
		ctype = ASPECT_CHART_TYPES[self.tabs.currentIndex()]
		for widgets in self.data[ctype]:
			pid = widgets['id']
			for key, check in widgets.items():
				if key == 'id':
					continue
				value = PLANET_DEFAULT_VISIBLE[pid] if pid < len(PLANET_DEFAULT_VISIBLE) else 0
				if key == 'visible_transit' and ctype == 'transit' and pid in PLANET_TRANSIT_HIDDEN:
					value = 0
				check.setChecked(value == 1)

	def submit(self, close=True):
		changed = []
		for ctype in ASPECT_CHART_TYPES:
			new = []
			for widgets in self.data[ctype]:
				values = {'id': widgets['id']}
				for key, check in widgets.items():
					if key != 'id':
						values[key] = int(check.isChecked())
				new.append(values)
			if new != self.saved[ctype]:
				dprint('PlanetSettingsDialog.submit: saving %s planets' % (ctype))
				self.db.setSettingsPlanet(ctype, new)
				self.saved[ctype] = new
				changed.append(ctype)
		if changed:
			self.window.refreshChart()
			#open timeline uses the transit planet settings
			self.window.refreshTableWindows(changed)
		if close:
			self.close()

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
Dialog 'Settings > Aspects': aspects (line, grid, orb) per chart type
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QGridLayout, QLabel, QVBoxLayout, QWidget
from astrochart.constants import ASPECT_CHART_TYPES, ASPECT_DEFAULTS, ASPECT_DEGREES, ASPECT_ORB_MAX
from astrochart.qt.dialog import AstroDialog, Button, captionLabel, chartTypeTabs
from astrochart.util import dprint

def orbValue(value, saved):
	"""orb of the spin box, an unchanged orb keeps its stored value (no rounding of untouched data)"""
	if round(value, 2) == round(saved, 2):
		return saved
	return round(value, 2)

class AspectSettingsDialog(AstroDialog):
	"""one page per aspect set (radix, transit, synastry), a row per aspect"""

	def __init__(self, window):
		super().__init__(window, _("Aspect Settings"))
		self.resize(560, 700)
		self.data = {}
		self.saved = {}
		ratio = self.devicePixelRatioF()
		pages = {}
		for ctype in ASPECT_CHART_TYPES:
			page = QWidget()
			grid = QGridLayout(page)
			grid.setHorizontalSpacing(16)
			#column headings above the check boxes and orbs
			for column, text in ((3, _('Visible\nin Circle')), (4, _('Visible\nin Grid')), (5, _('Orb'))):
				grid.addWidget(captionLabel(text), 0, column)
			rows = []
			saved = []
			for line, aspect in enumerate(self.db.getSettingsAspect(ctype), 1):
				widgets = {'degree': aspect['degree']}
				symbol = QLabel()
				pixmap = window.symbols.pixmap('orb%s' % (aspect['degree']), 16, ratio)
				if pixmap is not None:
					symbol.setPixmap(pixmap)
				grid.addWidget(symbol, line, 0)
				grid.addWidget(QLabel(aspect['name']), line, 1)
				degree = QLabel('%s°' % (aspect['degree']))
				degree.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
				grid.addWidget(degree, line, 2)
				for column, key, tip in ((3, 'visible', _('Visible\nin Circle')), (4, 'visible_grid', _('Visible\nin Grid'))):
					check = QCheckBox()
					check.setChecked(aspect[key] == 1)
					check.setToolTip(tip.replace('\n', ' '))
					grid.addWidget(check, line, column, Qt.AlignmentFlag.AlignCenter)
					widgets[key] = check
				orb = QDoubleSpinBox()
				orb.setDecimals(2)
				orb.setRange(0.0, max(ASPECT_ORB_MAX, aspect['orb']))
				orb.setSingleStep(0.5)
				orb.setSuffix('°')
				orb.setValue(aspect['orb'])
				grid.addWidget(orb, line, 5)
				widgets['orb'] = orb
				rows.append(widgets)
				saved.append({'degree':aspect['degree'], 'visible':aspect['visible'],
					'visible_grid':aspect['visible_grid'], 'orb':aspect['orb']})
			grid.setColumnStretch(1, 1)
			grid.setRowStretch(len(rows) + 1, 1)
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
		default = ASPECT_DEFAULTS[ctype]
		for widgets in self.data[ctype]:
			i = ASPECT_DEGREES.index(widgets['degree'])
			widgets['visible'].setChecked(default['visible'][i] == 1)
			widgets['visible_grid'].setChecked(default['visible_grid'][i] == 1)
			widgets['orb'].setValue(default['orb'][i])

	def submit(self, close=True):
		changed = []
		for ctype in ASPECT_CHART_TYPES:
			new = []
			for i, widgets in enumerate(self.data[ctype]):
				new.append({'degree':widgets['degree'],
					'visible':int(widgets['visible'].isChecked()),
					'visible_grid':int(widgets['visible_grid'].isChecked()),
					'orb':orbValue(widgets['orb'].value(), self.saved[ctype][i]['orb'])})
			if new != self.saved[ctype]:
				dprint('AspectSettingsDialog.submit: saving %s aspects' % (ctype))
				self.db.setSettingsAspect(ctype, new)
				self.saved[ctype] = new
				changed.append(ctype)
		if changed:
			self.window.refreshChart()
			self.window.refreshTableWindows(changed)
		if close:
			self.close()

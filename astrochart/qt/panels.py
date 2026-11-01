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
Side bar of the main window: positions, houses, aspects and data of the
chart as lists
"""

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
	QHeaderView, QLabel, QProgressBar, QTabWidget, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from astrochart.chart.data import formatDegree
from astrochart.constants import HOUSE_SYSTEMS, MODERN_ELEMENT_COLORS
from astrochart.qt.chart_view import involves

BODY = Qt.ItemDataRole.UserRole

#font size of the lists in points
LIST_FONT_MIN = 7
LIST_FONT_MAX = 24

def baseFontSize():
	"""point size of the font of the desktop"""
	size = QApplication.font().pointSizeF()
	return size if size > 0 else 10.0

def listFontSize(value):
	"""font size of the lists: the setting (points), else a bit larger than the desktop font"""
	try:
		size = float(value)
	except (TypeError, ValueError):
		size = baseFontSize() + 1
	return min(LIST_FONT_MAX, max(LIST_FONT_MIN, size))

def numericFont(font):
	"""font with digits of equal width"""
	font = QFont(font)
	try:
		font.setFeature(QFont.Tag('tnum'), 1)
	except (AttributeError, TypeError):
		pass
	return font

def numberText(text):
	"""degrees right aligned in a column: a thin space after the minute sign,
	which reaches beyond its advance and would be cut off at the edge"""
	return text + '\u2009'

def treeWidget(columns, stretch):
	"""list without header, column stretch takes the free width"""
	tree = QTreeWidget()
	tree.setColumnCount(columns)
	tree.setHeaderHidden(True)
	tree.setRootIsDecorated(False)
	tree.setItemsExpandable(False)
	tree.setUniformRowHeights(True)
	tree.setIconSize(QSize(20, 20))
	tree.setFrameShape(QTreeWidget.Shape.NoFrame)
	tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
	tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
	header = tree.header()
	header.setStretchLastSection(False)
	for column in range(columns):
		header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch if column == stretch else QHeaderView.ResizeMode.ResizeToContents)
	return tree

def heading(text):
	label = QLabel(text)
	font = label.font()
	font.setBold(True)
	label.setFont(font)
	return label

class ChartPanels(QTabWidget):
	"""
	pages: positions, houses, aspects, info; the font size of the lists
	(points) is fontSize, ctrl + mouse wheel changes it
	"""

	def __init__(self, window, symbols, fontSize):
		super().__init__()
		self.window = window
		self.chart = window.chart
		self.symbols = symbols
		self.setDocumentMode(True)
		self.positionItems = {}
		self.ratio = self.devicePixelRatioF()
		#positions and elements
		page = QWidget()
		layout = QVBoxLayout(page)
		self.positions = treeWidget(4, 0)
		self.positions.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
		self.positions.itemClicked.connect(self.onPositionClicked)
		layout.addWidget(self.positions, 1)
		self.elements = QGroupBox(_('Elements'))
		self.elementsLayout = QGridLayout(self.elements)
		layout.addWidget(self.elements)
		self.addTab(page, _('Positions'))
		#houses
		self.houses = treeWidget(2, 0)
		self.addTab(self.houses, _('Houses'))
		#aspects, of the selected body only if there is one
		page = QWidget()
		layout = QVBoxLayout(page)
		row = QHBoxLayout()
		self.aspectsTitle = heading('')
		row.addWidget(self.aspectsTitle, 1)
		self.allAspects = QToolButton()
		self.allAspects.setIcon(QIcon.fromTheme('edit-clear'))
		self.allAspects.setText(_('All aspects'))
		self.allAspects.setToolTip(_('All aspects'))
		self.allAspects.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
		self.allAspects.setAutoRaise(True)
		self.allAspects.clicked.connect(lambda: self.window.selectBody(None, None))
		row.addWidget(self.allAspects)
		layout.addLayout(row)
		self.aspects = treeWidget(5, 3)
		layout.addWidget(self.aspects, 1)
		self.addTab(page, _('Aspects'))
		#data of the chart
		page = QWidget()
		self.info = QFormLayout(page)
		self.info.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
		self.addTab(page, _('Info'))
		for tree in (self.positions, self.houses, self.aspects):
			tree.viewport().installEventFilter(self)
		self.applyFontSize(fontSize)

	def applyFontSize(self, size):
		"""font of the lists, the symbols grow with it"""
		self.fontSize = size
		font = QFont(self.font())
		font.setPointSizeF(size)
		self.setFont(font)
		self.factor = size / baseFontSize()
		for tree in (self.positions, self.houses, self.aspects):
			tree.setIconSize(QSize(self.iconSize(20), self.iconSize(20)))

	def setFontSize(self, size):
		self.applyFontSize(size)
		self.update()

	def zoomFont(self, delta):
		#ctrl + mouse wheel: one point larger or smaller
		if delta:
			self.window.setListFontSize(round(self.fontSize) + (1 if delta > 0 else -1))

	def eventFilter(self, watched, event):
		if event.type() == QEvent.Type.Wheel and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
			self.zoomFont(event.angleDelta().y())
			return True
		return super().eventFilter(watched, event)

	def wheelEvent(self, event):
		if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
			self.zoomFont(event.angleDelta().y())
			event.accept()
			return
		super().wheelEvent(event)

	def update(self):
		"""fill the pages from the calculated chart"""
		self.ratio = self.devicePixelRatioF()
		self.updatePositions()
		self.updateHouses()
		self.updateAspects()
		self.updateInfo()

	def iconSize(self, size):
		"""size of a symbol for the font size of the lists"""
		return max(8, int(round(size * self.factor)))

	def icon(self, name, size=20):
		return self.symbols.icon(name, self.iconSize(size), self.ratio)

	def muted(self):
		return self.palette().color(QPalette.ColorRole.PlaceholderText)

	def updatePositions(self):
		tree = self.positions
		tree.clear()
		chart = self.chart
		sides = [('radix', _('Radix'), chart.bodyRows())]
		if chart.type == "Transit":
			sides.append(('transit', _('Partner') if chart.synastry else _('Transit'), chart.bodyRows(transit=True)))
		number = numericFont(tree.font())
		self.positionItems = {}
		for side, title, rows in sides:
			if len(sides) > 1:
				group = QTreeWidgetItem([title])
				bold = QFont(tree.font())
				bold.setBold(True)
				group.setFont(0, bold)
				group.setFlags(Qt.ItemFlag.ItemIsEnabled)
				tree.addTopLevelItem(group)
				group.setFirstColumnSpanned(True)
			for row in rows:
				item = QTreeWidgetItem(['  ' + row['label'], numberText(row['degree']), '℞' if row['retrograde'] else '', str(row['house'])])
				item.setIcon(0, self.icon(row['symbol']))
				item.setIcon(1, self.icon(row['sign'], 16))
				for column in (1, 3):
					item.setFont(column, number)
					item.setTextAlignment(column, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
				item.setForeground(2, QColor('#d1242f'))
				item.setForeground(3, self.muted())
				item.setToolTip(0, '%s %s' % (_('House'), row['house']))
				item.setData(0, BODY, (side, row['id']))
				tree.addTopLevelItem(item)
				self.positionItems[(side, row['id'])] = item
		self.showSelection()
		#elements of the radix
		layout = self.elementsLayout
		while layout.count():
			#gone at once, not only when the event loop deletes it
			widget = layout.takeAt(0).widget()
			widget.hide()
			widget.setParent(None)
			widget.deleteLater()
		for line, (key, text, percent) in enumerate(chart.elementRows()):
			layout.addWidget(QLabel(text), line, 0)
			bar = QProgressBar()
			bar.setRange(0, 100)
			bar.setValue(int(round(percent)))
			bar.setTextVisible(False)
			bar.setMaximumHeight(8)
			if key in MODERN_ELEMENT_COLORS:
				palette = bar.palette()
				palette.setColor(QPalette.ColorRole.Highlight, QColor(MODERN_ELEMENT_COLORS[key]))
				bar.setPalette(palette)
			layout.addWidget(bar, line, 1)
			value = QLabel('%d%%' % percent)
			value.setFont(numericFont(value.font()))
			value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
			layout.addWidget(value, line, 2)
		layout.setColumnStretch(1, 1)

	def onPositionClicked(self, item, column):
		body = item.data(0, BODY)
		if body is not None:
			self.window.selectBody(*body)

	def showSelection(self):
		#mark the row of the selected body
		tree = self.positions
		tree.blockSignals(True)
		tree.clearSelection()
		item = self.positionItems.get(self.chart.highlight)
		if item is not None:
			item.setSelected(True)
			tree.scrollToItem(item)
		tree.blockSignals(False)

	def updateSelection(self):
		"""selected body changed: mark it, show its aspects"""
		self.showSelection()
		self.updateAspects()

	def updateHouses(self):
		tree = self.houses
		tree.clear()
		number = numericFont(tree.font())
		for row in self.chart.houseRows():
			item = QTreeWidgetItem(['%s %s' % (self.chart.label['cusp'], row['house']), numberText(row['degree'])])
			item.setIcon(1, self.icon(row['sign'], 16))
			item.setFont(1, number)
			item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
			tree.addTopLevelItem(item)

	def updateAspects(self):
		tree = self.aspects
		tree.clear()
		rows = self.chart.aspectRows()
		selected = self.chart.highlight
		if selected is None:
			self.aspectsTitle.setText('%s (%d)' % (_('Aspects'), len(rows)))
		else:
			rows = [row for row in rows if involves(row, *selected)]
			name = self.chart.planets[selected[1]]['label']
			self.aspectsTitle.setText('%s · %s (%d)' % (_('Aspects'), name, len(rows)))
		self.allAspects.setVisible(selected is not None)
		number = numericFont(tree.font())
		for row in rows:
			first, second = row['first'], row['second']
			item = QTreeWidgetItem(['', '', '', '%s %s %s' % (first['label'], row['name'], second['label']),
				numberText(formatDegree(row['orb'], seconds=False))])
			item.setIcon(0, self.icon(first['symbol'], 18))
			item.setIcon(1, self.icon('orb%s' % row['degree'], 14))
			item.setIcon(2, self.icon(second['symbol'], 18))
			item.setToolTip(3, item.text(3))
			item.setFont(4, number)
			item.setForeground(4, self.muted())
			item.setTextAlignment(4, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
			tree.addTopLevelItem(item)

	def updateInfo(self):
		layout = self.info
		while layout.rowCount():
			layout.removeRow(0)
		chart = self.chart
		cfg = chart.db.astrocfg
		date = '%s-%02d-%02d %02d:%02d:%02d %s' % (chart.year_loc, chart.month_loc, chart.day_loc,
			chart.hour_loc, chart.minute_loc, chart.second_loc, chart.decTzStr(chart.timezone))
		postype = {"geo": chart.label["apparent_geocentric"], "truegeo": chart.label["true_geocentric"],
			"topo": chart.label["topocentric"], "helio": chart.label["heliocentric"]}
		zodiac = _("Sidereal") + ' (%s)' % cfg['siderealmode'] if cfg['zodiactype'] == 'sidereal' else _("Tropical")
		lunar = chart.lunar_phase
		title = heading(str(chart.name))
		title.setWordWrap(True)
		layout.addRow(title)
		for text in (chart.charttype, date, chart.location,
			'%s · %s' % (chart.lat2str(chart.geolat), chart.lon2str(chart.geolon))):
			label = QLabel(str(text))
			label.setWordWrap(True)
			label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
			layout.addRow(label)
		for caption, value in (
			(_('Position Calculation'), postype.get(cfg['postype'], cfg['postype'])),
			(_('Zodiac Type'), zodiac),
			(_('Houses System'), HOUSE_SYSTEMS.get(cfg['houses_system'], cfg['houses_system'])),
			(_('Lunar Phase'), '%s (%s) · %s (%s) · %s' % (lunar['sun_phase'], _('Sun'), lunar['moon_phase'], _('Moon'),
				formatDegree(lunar['degrees'])))):
			label = QLabel(str(value))
			label.setWordWrap(True)
			label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
			layout.addRow(caption + ':', label)

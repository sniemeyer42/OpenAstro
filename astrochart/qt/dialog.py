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
Base class of the dialogs beside the main window, questions and messages
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFrame, QLabel, QLineEdit, QMessageBox, QScrollArea, QTabWidget
from astrochart.constants import ASPECT_CHART_TYPES

Button = QDialogButtonBox.StandardButton

def chartTypePage(chart):
	"""settings page (index into ASPECT_CHART_TYPES) of the chart shown"""
	if chart.type == "Transit":
		return ASPECT_CHART_TYPES.index('synastry' if chart.synastry else 'transit')
	return ASPECT_CHART_TYPES.index('radix')

def chartTypeTabs(pages, chart):
	"""
	tabs radix, transit, synastry of the settings pages {chart type: widget},
	scrolling, the page of the chart shown is the current one
	"""
	titles = {'radix': _('Radix'), 'transit': _('Transit'), 'synastry': _('Synastry')}
	tabs = QTabWidget()
	for ctype in ASPECT_CHART_TYPES:
		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setFrameShape(QFrame.Shape.NoFrame)
		scroll.setWidget(pages[ctype])
		tabs.addTab(scroll, titles[ctype])
	tabs.setCurrentIndex(chartTypePage(chart))
	return tabs

def captionLabel(text):
	"""column heading of a settings table, centred"""
	label = QLabel(text)
	label.setAlignment(Qt.AlignmentFlag.AlignCenter)
	font = QFont(label.font())
	font.setPointSizeF(font.pointSizeF() * 0.9)
	label.setFont(font)
	return label

def confirm(parent, text):
	"""ask OK or Cancel, True for OK"""
	Answer = QMessageBox.StandardButton
	return QMessageBox.question(parent, _("Caution"), text, Answer.Ok | Answer.Cancel, Answer.Cancel) == Answer.Ok

def warn(parent, title, text):
	QMessageBox.warning(parent, title, text)

def heading(text):
	"""bold label above a group of settings"""
	label = QLabel(text)
	font = QFont(label.font())
	font.setBold(True)
	label.setFont(font)
	return label

class SearchEdit(QLineEdit):
	"""line edit whose Enter key starts its search instead of the default button of the dialog"""

	def keyPressEvent(self, event):
		super().keyPressEvent(event)
		if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
			event.accept()

class AstroDialog(QDialog):
	"""
	dialog of the program: knows the main window (self.window), the chart
	shown, configuration and databases; it is deleted when it closes and
	is modal unless modal=False
	"""

	def __init__(self, window, title, parent=None, modal=True):
		super().__init__(parent if parent is not None else window)
		self.window = window
		self.app = window.app
		self.chart = window.chart
		self.cfg = window.cfg
		self.db = window.db
		self.setWindowTitle(title)
		self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
		if modal:
			self.setWindowModality(Qt.WindowModality.ApplicationModal)

	def buttonBox(self, buttons, actions, extra=()):
		"""
		buttons of the dialog: standard buttons with actions {button: callback}
		(Cancel closes without action), extra: (label, role, callback) of more
		buttons; self.button[key] are the buttons by standard button or label
		"""
		box = QDialogButtonBox(buttons)
		self.button = {}
		for standard in (Button.Ok, Button.Save, Button.Apply, Button.Cancel, Button.Close, Button.RestoreDefaults, Button.Open):
			button = box.button(standard)
			if button is None:
				continue
			self.button[standard] = button
			callback = actions.get(standard, self.close if standard in (Button.Cancel, Button.Close) else None)
			if callback is not None:
				button.clicked.connect(lambda checked=False, callback=callback: callback())
		for label, role, callback in extra:
			button = box.addButton(label, role)
			button.clicked.connect(lambda checked=False, callback=callback: callback())
			self.button[label] = button
		#Enter: OK if there is one, else no button
		for button in box.buttons():
			button.setAutoDefault(False)
		if Button.Ok in self.button:
			self.button[Button.Ok].setDefault(True)
		return box

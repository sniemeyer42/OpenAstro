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
Dialog 'Settings > General Configuration': geocoding, houses, positions,
zodiac, chart view, font size of the lists and language
"""

import os
import sys
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QSpinBox, QVBoxLayout
from astrochart.constants import HOUSE_SYSTEMS
from astrochart.i18n import LANGUAGES, LANGUAGES_LABEL
from astrochart.qt.dialog import AstroDialog, Button, confirm
from astrochart.qt.panels import LIST_FONT_MAX, LIST_FONT_MIN
from astrochart.util import dprint

def siderealModes():
	"""(key, text) of the sidereal modes"""
	return (
		("FAGAN_BRADLEY", _("Fagan Bradley")),
		("LAHIRI", _("Lahiri")),
		("DELUCE", _("Deluce")),
		("RAMAN", _("Ramanb")),
		("USHASHASHI", _("Ushashashi")),
		("KRISHNAMURTI", _("Krishnamurti")),
		("DJWHAL_KHUL", _("Djwhal Khul")),
		("YUKTESHWAR", _("Yukteshwar")),
		("JN_BHASIN", _("Jn Bhasin")),
		("BABYL_KUGLER1", _("Babyl Kugler 1")),
		("BABYL_KUGLER2", _("Babyl Kugler 2")),
		("BABYL_KUGLER3", _("Babyl Kugler 3")),
		("BABYL_HUBER", _("Babyl Huber")),
		("BABYL_ETPSC", _("Babyl Etpsc")),
		("ALDEBARAN_15TAU", _("Aldebaran 15Tau")),
		("HIPPARCHOS", _("Hipparchos")),
		("SASSANIAN", _("Sassanian")),
		("J2000", _("J2000")),
		("J1900", _("J1900")),
		("B1950", _("B1950")))

def comboBox(items, selected):
	"""drop down of items (key, text), the item of key selected is chosen"""
	combo = QComboBox()
	for key, text in items:
		combo.addItem(text, key)
	index = combo.findData(selected)
	combo.setCurrentIndex(index if index >= 0 else 0)
	return combo

class ConfigurationDialog(AstroDialog):
	"""general configuration and language"""

	def __init__(self, window):
		super().__init__(window, _("General Configuration"))
		cfg = self.db.astrocfg
		chart = self.chart
		layout = QVBoxLayout(self)
		# online geocoding
		self.geocoding = QCheckBox(_("Use Online Geocoding (ws.geonames.org)"))
		self.geocoding.setChecked(self.db.getAstrocfg('use_geonames.org') == "1")
		layout.addWidget(self.geocoding)
		#calculation: house system, positions, zodiac
		form = QFormLayout()
		layout.addLayout(form)
		self.houses = comboBox(HOUSE_SYSTEMS.items(), cfg['houses_system'])
		form.addRow(_('Houses System'), self.houses)
		self.postype = comboBox((
			("geo", chart.label["apparent_geocentric"] + " " + _("(default)")),
			("truegeo", chart.label["true_geocentric"]),
			("topo", chart.label["topocentric"]),
			("helio", chart.label["heliocentric"])), cfg['postype'])
		form.addRow(_('Position Calculation'), self.postype)
		self.zodiactype = comboBox((("tropical", _("Tropical")), ("sidereal", _("Sidereal"))), cfg['zodiactype'])
		form.addRow(_('Zodiac Type'), self.zodiactype)
		#sidereal mode, only for the sidereal zodiac
		self.siderealmode = comboBox(siderealModes(), cfg['siderealmode'])
		form.addRow(_('Sidereal Mode'), self.siderealmode)
		self.zodiactype.currentIndexChanged.connect(lambda index: self.siderealmode.setEnabled(self.zodiactype.currentData() == 'sidereal'))
		self.siderealmode.setEnabled(cfg['zodiactype'] == 'sidereal')
		#view: modern wheel or the classic one (traditional, european), lists, language
		form.addRow(' ', None)
		self.chartview = comboBox((
			("modern", _("Modern")),
			("traditional", '%s · %s' % (_("Classic"), _("Planets in Zodiac"))),
			("european", '%s · %s' % (_("Classic"), _("Planets around Zodiac")))), self.chartView())
		form.addRow(_('Chart View'), self.chartview)
		self.fontSize = QSpinBox()
		self.fontSize.setRange(LIST_FONT_MIN, LIST_FONT_MAX)
		self.fontSize.setSuffix(' pt')
		self.fontSize.setValue(round(window.panels.fontSize))
		form.addRow(_('Font Size of the Lists'), self.fontSize)
		languages = [('default', _("Default"))] + [(language, LANGUAGES_LABEL[language]) for language in LANGUAGES if language != 'default']
		self.language = comboBox(languages, cfg['language'] if cfg['language'] in LANGUAGES else 'default')
		form.addRow(_('Language'), self.language)
		layout.addStretch(1)
		layout.addWidget(self.buttonBox(Button.Ok | Button.Cancel, {Button.Ok: self.submit}))

	def chartView(self):
		"""'modern' or the view of the classic wheel"""
		if self.db.astrocfg.get('chartstyle', 'modern') == 'modern':
			return 'modern'
		return self.db.astrocfg['chartview']

	def submit(self):
		db = self.db
		update = False
		db.setAstrocfg("use_geonames.org", "1" if self.geocoding.isChecked() else "0")
		#calculation
		for key, combo in (("houses_system", self.houses), ("postype", self.postype),
			("zodiactype", self.zodiactype), ("siderealmode", self.siderealmode)):
			if combo.currentData() != db.astrocfg[key]:
				dprint('%s chosen: %s' % (key, combo.currentData()))
				update = True
				db.setAstrocfg(key, combo.currentData())
		#chart view: style modern or classic, the view of the classic wheel
		view = self.chartview.currentData()
		if view != self.chartView():
			update = True
			if view == "modern":
				db.setAstrocfg("chartstyle", "modern")
			else:
				db.setAstrocfg("chartstyle", "classic")
				db.setAstrocfg("chartview", view)
		#font size of the lists
		if self.fontSize.value() != round(self.window.panels.fontSize):
			self.window.setListFontSize(self.fontSize.value())
		if update:
			self.window.refreshChart()
			self.window.refreshTableWindows(['radix', 'transit', 'synastry'])
		self.close()
		#language: the program restarts
		language = self.language.currentData()
		if language != db.astrocfg['language']:
			self.changeLanguage(language)

	def changeLanguage(self, language):
		text = _('Really change to language < {0} > ?\n').format(LANGUAGES_LABEL[language]) + _('Program will restart !')
		if confirm(self.window, text):
			self.db.setAstrocfg("language", language)
			self.db.setLanguage(lang=language)
			#restart
			os.execv(sys.executable, [sys.executable] + sys.argv)

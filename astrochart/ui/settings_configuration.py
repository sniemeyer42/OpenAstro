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
Dialog 'Settings > Configuration': geocoding, houses, positions, chart view,
zodiac and language
"""

import sys
import os
from gi.repository import Adw, Gtk
from astrochart.constants import HOUSE_SYSTEMS
from astrochart.i18n import LANGUAGES, LANGUAGES_LABEL
from astrochart.ui.dialog import AstroDialog, comboRow, page
from astrochart.util import dprint

class ConfigurationDialog(AstroDialog):
	"""general configuration and language"""

	def __init__(self, window):
		super().__init__(window, title=_("General Configuration"), transient_for=window, modal=True)
		self.set_default_size(460, 600)
		cfg = self.db.astrocfg
		#widgets of the settings
		data = self.data = {}
		# online geocoding
		data['use_geonames.org'] = Adw.SwitchRow(title=_("Use Online Geocoding (ws.geonames.org)"))
		data['use_geonames.org'].set_active(self.db.getAstrocfg('use_geonames.org') == "1")
		# house system
		self.houses_list = list(HOUSE_SYSTEMS.keys())
		data['houses_system'] = comboRow(_('Houses System'), HOUSE_SYSTEMS.values(),
			self.houses_list.index(cfg['houses_system']) if cfg['houses_system'] in self.houses_list else 0)
		#position calculation (geo,truegeo,topo,helio)
		postype={
			"geo":self.chart.label["apparent_geocentric"]+" "+_("(default)"),
			"truegeo":self.chart.label["true_geocentric"],
			"topo":self.chart.label["topocentric"],
			"helio":self.chart.label["heliocentric"]
		}
		self.postype_list=["geo","truegeo","topo","helio"]
		data['postype'] = comboRow(_('Position Calculation'), postype.values(),
			self.postype_list.index(cfg['postype']) if cfg['postype'] in self.postype_list else 0)
		#chart view: modern wheel or the classic one (traditional, european)
		chartview={
			"modern":_("Modern"),
			"traditional":'%s · %s' % (_("Classic"), _("Planets in Zodiac")),
			"european":'%s · %s' % (_("Classic"), _("Planets around Zodiac"))
		}
		self.chartview_list = ["modern","traditional","european"]
		data['chartview'] = comboRow(_('Chart View'), chartview.values(),
			self.chartview_list.index(self.chartView()) if self.chartView() in self.chartview_list else 0)
		#zodiac type (tropical, sidereal)
		zodiactype = {"tropical":_("Tropical"), "sidereal":_("Sidereal")}
		self.zodiactype_list=["tropical","sidereal"]
		data['zodiactype'] = comboRow(_('Zodiac Type'), zodiactype.values(),
			self.zodiactype_list.index(cfg['zodiactype']) if cfg['zodiactype'] in self.zodiactype_list else 0)
		#sidereal mode, only for the sidereal zodiac
		self.siderealmode_chartview={
				"FAGAN_BRADLEY":_("Fagan Bradley"),
				"LAHIRI":_("Lahiri"),
				"DELUCE":_("Deluce"),
				"RAMAN":_("Ramanb"),
				"USHASHASHI":_("Ushashashi"),
				"KRISHNAMURTI":_("Krishnamurti"),
				"DJWHAL_KHUL":_("Djwhal Khul"),
				"YUKTESHWAR":_("Yukteshwar"),
				"JN_BHASIN":_("Jn Bhasin"),
				"BABYL_KUGLER1":_("Babyl Kugler 1"),
				"BABYL_KUGLER2":_("Babyl Kugler 2"),
				"BABYL_KUGLER3":_("Babyl Kugler 3"),
				"BABYL_HUBER":_("Babyl Huber"),
				"BABYL_ETPSC":_("Babyl Etpsc"),
				"ALDEBARAN_15TAU":_("Aldebaran 15Tau"),
				"HIPPARCHOS":_("Hipparchos"),
				"SASSANIAN":_("Sassanian"),
				"J2000":_("J2000"),
				"J1900":_("J1900"),
				"B1950":_("B1950")
		}
		self.siderealmode_list = list(self.siderealmode_chartview.keys())
		data['siderealmode'] = comboRow(_('Sidereal Mode'), self.siderealmode_chartview.values(),
			self.siderealmode_list.index(cfg['siderealmode']) if cfg['siderealmode'] in self.siderealmode_list else 0)
		data['siderealmode'].set_sensitive(cfg['zodiactype'] == 'sidereal')
		data['zodiactype'].connect("notify::selected", lambda row, _pspec:
			data['siderealmode'].set_sensitive(self.zodiactype_list[row.get_selected()] == 'sidereal'))
		#language, default first
		languages = [_("Default")] + [self.db.lang_label[language] for language in LANGUAGES]
		active = LANGUAGES.index(cfg['language']) + 1 if cfg['language'] in LANGUAGES else 0
		data['language'] = comboRow(_('Language'), languages, active)
		#groups: geocoding, calculation, view and language
		groups = []
		for keys in (('use_geonames.org',), ('houses_system', 'postype', 'zodiactype', 'siderealmode'), ('chartview', 'language')):
			group = Adw.PreferencesGroup()
			for key in keys:
				group.add(data[key])
			groups.append(group)
		self.set_child(page(*groups))
		self.headerButtons(cancel=self.close, ok=self.submit)

	def chartView(self):
		"""'modern' or the view of the classic wheel"""
		if self.db.astrocfg.get('chartstyle', 'modern') == 'modern':
			return 'modern'
		return self.db.astrocfg['chartview']

	def submit(self):
		data = self.data
		update = False
		if data['use_geonames.org'].get_active():
			self.db.setAstrocfg("use_geonames.org","1")
		else:
			self.db.setAstrocfg("use_geonames.org","0")
		# houses system
		model = data['houses_system'].get_model()
		active = data['houses_system'].get_selected()
		dprint('House system choosen: '+model.get_string(active))
		if self.houses_list[active] != self.db.astrocfg['houses_system']:
			update = True
			self.db.setAstrocfg("houses_system",self.houses_list[active])
		# position calculation
		model = data['postype'].get_model()
		active = data['postype'].get_selected()
		dprint('Position Type choosen: '+model.get_string(active))
		if self.postype_list[active] != self.db.astrocfg['postype']:
			update = True
			self.db.setAstrocfg("postype",self.postype_list[active])
		#chart view: style modern or classic, the view of the classic wheel
		model = data['chartview'].get_model()
		active = data['chartview'].get_selected()
		dprint('Chart View choosen: '+model.get_string(active))
		if self.chartview_list[active] != self.chartView():
			update = True
			if self.chartview_list[active] == "modern":
				self.db.setAstrocfg("chartstyle", "modern")
			else:
				self.db.setAstrocfg("chartstyle", "classic")
				self.db.setAstrocfg("chartview",self.chartview_list[active])
		#zodiac type
		model = data['zodiactype'].get_model()
		active = data['zodiactype'].get_selected()
		if self.zodiactype_list[active] != self.db.astrocfg['zodiactype']:
			update = True
			self.db.setAstrocfg("zodiactype",self.zodiactype_list[active])
		#sidereal mode
		model = data['siderealmode'].get_model()
		active = data['siderealmode'].get_selected()
		if self.siderealmode_list[active] != self.db.astrocfg['siderealmode']:
			update = True
			self.db.setAstrocfg("siderealmode",self.siderealmode_list[active])
		#language
		model = data['language'].get_model()
		active = data['language'].get_selected()
		if active == 0:
			active_lang = "default"
		else:
			active_lang = LANGUAGES[active-1]
		if active_lang != self.db.astrocfg['language']:
			self.confirm_language(active_lang)
		self.window.updateUI(first_time=False)
		# updatechart
		if update:
			self.window.updateChart()
		self.close()
		return

	def confirm_language(self,lang):
		alert_dialog = Gtk.AlertDialog()
		alert_dialog.set_message(_('Caution'))
		confirm = _('Really change to language < {0} > ?\n').format(LANGUAGES_LABEL[lang])+_('Program will restart !')
		alert_dialog.set_detail(confirm)
		alert_dialog.set_modal(True)
		alert_dialog.set_buttons([_("Cancel"), _("OK")])
		#the main window is the parent, this dialog closes at once
		alert_dialog.choose(parent=self.window, cancellable=None, callback=self.on_change_language, user_data=lang)

	def on_change_language(self, source_obj, async_res, lang):
		result = source_obj.choose_finish(async_res)
		if result == 1:
			self.db.setAstrocfg("language",lang)
			# set language to be used
			self.db.setLanguage(lang=lang)
			#restart
			os.execv(sys.executable, ['python'] + sys.argv)

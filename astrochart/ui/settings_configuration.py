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
Menu 'Settings': general configuration and language
"""

import sys
import os
from gi.repository import Gtk
from astrochart.i18n import LANGUAGES, LANGUAGES_LABEL
from astrochart.util import dprint

class ConfigurationSettingsMixin:
	"""Menu 'Settings': general configuration and language"""

	def setConfiguration_callback(self, action, parameter):
		# create a new window
		self.win_SC = Gtk.Window(title=_("General Configuration"))
		""" >>> set_icon changed in GTK4 """

		self.win_SC.set_default_size(364,512)
		#data dictionary
		data = {}
		#create a VBox
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
		vbox.props.margin_start = 32
		vbox.props.margin_end = 16
		vbox.props.margin_top = 16
		vbox.props.margin_bottom = 16
		#create a grid with 8 rows and 1 column
		grid = Gtk.Grid()
		grid.set_column_spacing(8)
		grid.set_row_spacing(8)
		#grid.set_border_width(10)
		grid.set_column_homogeneous(True)
		# options
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		hbox.set_spacing(8)
		geobase = Gtk.Label(label=_("Use Online Geocoding (ws.geonames.org)"))
		hbox.prepend(geobase)
		data['use_geonames.org'] = Gtk.CheckButton()
		hbox.append(data['use_geonames.org'])
		grid.attach(hbox, 0, 0, 1, 1)
		if self.db.getAstrocfg('use_geonames.org') == "1":
			data['use_geonames.org'].set_active(True)
		"""
		 replace ComboBox by DrowDown
		 https://pygobject.gnome.org/tutorials/gtk4/controls/dropdownhtml
		"""
		# house system
		data['houses_system'] = Gtk.DropDown.new()
		grid.attach(Gtk.Label(label=_('Houses System')), 0, 1, 1, 1)
		grid.attach(data['houses_system'], 0, 2, 1, 1)
		house_systems = {
			"P":"Placidus",
			"K":"Koch",
			"O":"Porphyrius",
			"R":"Regiomontanus",
			"C":"Campanus",
			"A":"Equal (Cusp 1 = Asc)",
			"V":"Vehlow Equal (Asc = 1/2 House 1)",
			"W":"Whole",
			"X":"Axial Rotation",
			"H":"Azimuthal or Horizontal System",
			"T":"Polich/Page ('topocentric system')",
			"B":"Alcabitus",
			"G":"Gauquelin sectors",
			"M":"Morinus"
		}
		active = 0
		self.houses_list = []
		systems = Gtk.StringList()
		for i, key in enumerate(house_systems.keys()):
			self.houses_list.append(key)
			systems.append(house_systems[key])
			if self.db.astrocfg['houses_system'] == key:
				active = i
		data['houses_system'].set_model(model=systems)
		data['houses_system'].set_selected(active)

		#position calculation (geo,truegeo,topo,helio)
		data['postype'] = Gtk.DropDown.new()
		grid.attach(Gtk.Label(label=_('Position Calculation')), 0, 3, 1, 1)
		grid.attach(data['postype'], 0, 4, 1, 1)
		postype={
			"geo":self.chart.label["apparent_geocentric"]+" "+_("(default)"),
			"truegeo":self.chart.label["true_geocentric"],
			"topo":self.chart.label["topocentric"],
			"helio":self.chart.label["heliocentric"]
		}
		self.postype_list=["geo","truegeo","topo","helio"]
		postypes = Gtk.StringList()
		active = 0
		for i, key in enumerate(postype.keys()):
			postypes.append(postype[key])
			if self.db.astrocfg['postype'] == key:
				active = i
		data['postype'].set_model(model=postypes)
		data['postype'].set_selected(active)

		#chart view (traditional,european)
		data['chartview'] = Gtk.DropDown.new()
		grid.attach(Gtk.Label(label=_('Chart View')), 0, 5, 1, 1)
		grid.attach(data['chartview'], 0, 6, 1, 1)
		chartview={
			"traditional":_("Planets in Zodiac"),
			"european":_("Planets around Zodiac")
		}
		self.chartview_list = ["traditional","european"]
		chartviews = Gtk.StringList()
		active = 0
		for i, key in enumerate(chartview.keys()):
			chartviews.append(chartview[key])
			if self.db.astrocfg['chartview'] == key:
				active = i
		data['chartview'].set_model(model=chartviews)
		data['chartview'].set_selected(active)

		#zodiac type (tropical, sidereal)
		data['zodiactype'] = Gtk.DropDown.new()
		grid.attach(Gtk.Label(label=_('Zodiac Type')), 0, 7, 1, 1)
		grid.attach(data['zodiactype'], 0, 8, 1, 1)
		zodiactype = {"tropical":_("Tropical"), "sidereal":_("Sidereal")}
		self.zodiactype_list=["tropical","sidereal"]
		zodiactypes = Gtk.StringList()
		active = 0
		for i, key in enumerate(zodiactype.keys()):
			zodiactypes.append(zodiactype[key])
			if self.db.astrocfg['zodiactype'] == key:
				active = i
		data['zodiactype'].set_model(model=zodiactypes)
		data['zodiactype'].set_selected(active)

		#sidereal mode
		data['siderealmode'] = Gtk.DropDown.new()
		if self.db.astrocfg['zodiactype'] != 'sidereal':
			data['siderealmode'].set_sensitive(False)

		def zodiactype_changed(dropdown, _pspec):
			# Selected Gtk.StringObject
			selected = dropdown.get_selected()
			if selected is not None:
				type_string = self.zodiactype_list[selected]
				if type_string != 'sidereal':
					data['siderealmode'].set_sensitive(False)
				else:
					data['siderealmode'].set_sensitive(True)

		data['zodiactype'].connect("notify::selected-item", zodiactype_changed)
		grid.attach(Gtk.Label(label=_('Sidereal Mode')), 0, 9, 1, 1)
		grid.attach(data['siderealmode'], 0, 10, 1, 1)
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
		self.siderealmode_list = [
				"FAGAN_BRADLEY",
				"LAHIRI",
				"DELUCE",
				"RAMAN",
				"USHASHASHI",
				"KRISHNAMURTI",
				"DJWHAL_KHUL",
				"YUKTESHWAR",
				"JN_BHASIN",
				"BABYL_KUGLER1",
				"BABYL_KUGLER2",
				"BABYL_KUGLER3",
				"BABYL_HUBER",
				"BABYL_ETPSC",
				"ALDEBARAN_15TAU",
				"HIPPARCHOS",
				"SASSANIAN",
				"J2000",
				"J1900",
				"B1950"
		]
		sideralmodes = Gtk.StringList()
		active = 0
		for i, key in enumerate(self.siderealmode_chartview.keys()):
			sideralmodes.append(self.siderealmode_chartview[key])
			if self.db.astrocfg['siderealmode'] == key:
				active = i
		data['siderealmode'].set_model(model=sideralmodes)
		data['siderealmode'].set_selected(active)
		#language
		grid.attach(Gtk.Label(label=_('Language')), 0, 11, 1, 1)
		data['language'] = Gtk.DropDown.new()
		grid.attach(data['language'], 0, 12, 1, 1)
		languages = Gtk.StringList()
		languages.append(_("Default"))
		active = 0
		for i, language in enumerate(LANGUAGES):
			languages.append(self.db.lang_label[language])
			if self.db.astrocfg['language'] == language:
				active = i+1
		data['language'].set_model(model=languages)
		data['language'].set_selected(active)
		#make the ui layout with ok button
		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_vexpand(True)
		scrolled_window.set_child(grid)
		vbox.append(scrolled_window)
		#self.win_SC.vbox.pack_start(scrolledwindow, True, True, 0)
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_homogeneous(True)
		# ok button
		button = Gtk.Button.new_with_mnemonic(label=_("OK"))
		button.connect("clicked", self.settingsConfigurationSubmit, data)
		button_box.prepend(button)
		# cancel button
		button = Gtk.Button.new_with_mnemonic(label=_("Cancel"))
		button.connect("clicked", lambda w: self.win_SC.destroy())
		#self.win_SC.action_area.pack_start(button, True, True, 0)
		button_box.prepend(button)
		vbox.append(button_box)
		self.win_SC.set_child(vbox)
		self.win_SC.present()

	def settingsConfigurationSubmit(self, widget, data):
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
		#chart view
		model = data['chartview'].get_model()
		active = data['chartview'].get_selected()
		dprint('Chart View choosen: '+model.get_string(active))
		if self.chartview_list[active] != self.db.astrocfg['chartview']:
			update = True
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
		self.updateUI(first_time=False)
		# updatechart
		if update:
			self.updateChart()
		self.win_SC.destroy()
		return

	def confirm_language(self,lang):
		alert_dialog = Gtk.AlertDialog()
		alert_dialog.set_message(_('Caution'))
		confirm = _('Really change to language < {0} > ?\n').format(LANGUAGES_LABEL[lang])+_('Program will restart !')
		alert_dialog.set_detail(confirm)
		alert_dialog.set_modal(True)
		alert_dialog.set_buttons(["Cancel", "OK"])
		alert_dialog.choose(parent=self, cancellable=None, callback=self.on_change_language, user_data=lang)

	def on_change_language(self, source_obj, async_res, lang):
		result = source_obj.choose_finish(async_res)
		if result == 1:
			self.db.setAstrocfg("language",lang)
			# set language to be used
			self.db.setLanguage(lang=lang)
			#restart
			os.execv(sys.executable, ['python'] + sys.argv)

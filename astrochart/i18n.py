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
Translations
"""

import os
import gettext
from astrochart.constants import LOCAL
from astrochart.paths import DATADIR
from astrochart.util import dprint

#Translations
LANGUAGES_LABEL={
			"ar":"الْعَرَبيّة",
			"pt_BR":"Português brasileiro",
			"bg":"български език",
			"ca":"català",
			"cs":"čeština",
			"da":"dansk",
			"en":"English",
			"eo":"Esperanto",
			"es":"Español",
			"fi":"suomi",
			"fr":"Français",
			"de":"Deutsch",
			"default":"default",
			"el":"ελληνικά",
			"hu":"magyar nyelv",
			"it":"Italiano",
			"ja":"日本",
			"nds":"Plattdüütsch",
			"nb":"Bokmål",
			"nl":"Nederlands",
			"pl":"język polski",
			"rom":"rromani ćhib",
			"ru":"Русский",
			"sv":"svenska",
			"uk":"українська мова",
			"zh_TW":"正體字"
		}

TDomain = os.path.join(DATADIR, 'locale')
if not LOCAL:
	TDomain = os.path.dirname(DATADIR)
	TDomain = os.path.join(TDomain, 'locale')
LANGUAGES=list(LANGUAGES_LABEL.keys())
TRANSLATION={}
#tell the domain, 'locale' is the folder containing your translations
gettext.bindtextdomain('openastro', 'TDomain')
gettext.textdomain('openastro')

for i in range(len(LANGUAGES)):
	try:
		TRANSLATION[LANGUAGES[i]] = gettext.translation("openastro",TDomain,languages=[LANGUAGES[i]])
	except IOError as err:
		dprint("IOError! Invalid languages specified (%s) in %s" %(LANGUAGES[i],TDomain))
		TRANSLATION[LANGUAGES[i]] = gettext.translation("openastro",TDomain,languages=['en'])
try:
	TRANSLATION["default"] = gettext.translation("openastro",TDomain)
except IOError as err:
	dprint("OpenAstro.org has not yet been translated in your language! Could not load translation...")
	TRANSLATION["default"] = gettext.translation("openastro",TDomain,languages=['en'])

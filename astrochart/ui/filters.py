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
File filters of the file dialogs
"""

from gi.repository import Gtk

""" Construct FileFilters """
FILTER_ALL_FILES = Gtk.FileFilter()
FILTER_ALL_FILES.set_name(name='ALL')
FILTER_ALL_FILES.add_pattern(pattern='*')

FILTER_DAT_FILES = Gtk.FileFilter()
FILTER_DAT_FILES.set_name(name='DAT')
FILTER_DAT_FILES.add_pattern(pattern='*.dat')
FILTER_DAT_FILES.add_mime_type(mime_type='chart/dat')

FILTER_JPG_FILES = Gtk.FileFilter()
FILTER_JPG_FILES.set_name(name='JPG')
FILTER_JPG_FILES.add_pattern(pattern='*.jpg')
FILTER_JPG_FILES.add_mime_type(mime_type='image/jpg')

FILTER_OAC_FILES = Gtk.FileFilter()
FILTER_OAC_FILES.set_name(name='OAC')
FILTER_OAC_FILES.add_pattern(pattern='*.oac')
FILTER_OAC_FILES.add_mime_type(mime_type='chart/oac')

FILTER_PDF_FILES = Gtk.FileFilter()
FILTER_PDF_FILES.set_name(name='PDF')
FILTER_PDF_FILES.add_pattern(pattern='*.pdf')
FILTER_PDF_FILES.add_mime_type(mime_type='application/pdf')

FILTER_PNG_FILES = Gtk.FileFilter()
FILTER_PNG_FILES.set_name(name='PNG')
FILTER_PNG_FILES.add_pattern(pattern='*.png')
FILTER_PNG_FILES.add_mime_type(mime_type='image/png')

FILTER_PY_FILES = Gtk.FileFilter()
FILTER_PY_FILES.set_name(name='Python')
FILTER_PY_FILES.add_pattern(pattern='*.py')
FILTER_PY_FILES.add_mime_type(mime_type='text/x-python')

FILTER_SKIF_FILES = Gtk.FileFilter()
FILTER_SKIF_FILES.set_name(name='SKIF')
FILTER_SKIF_FILES.add_pattern(pattern='*.skif')
FILTER_SKIF_FILES.add_mime_type(mime_type='chart/skif')

FILTER_SQL_FILES = Gtk.FileFilter()
FILTER_SQL_FILES.set_name(name='SQL')
FILTER_SQL_FILES.add_pattern(pattern='*.sql')
FILTER_SQL_FILES.add_mime_type(mime_type='database/sql')

FILTER_SVG_FILES = Gtk.FileFilter()
FILTER_SVG_FILES.set_name(name='SVG')
FILTER_SVG_FILES.add_pattern(pattern='*.svg')
FILTER_SVG_FILES.add_mime_type(mime_type='image/svg')

FILTER_TXT_FILES = Gtk.FileFilter()
FILTER_TXT_FILES.set_name(name='TXT')
FILTER_TXT_FILES.add_pattern(pattern='*.txt')
FILTER_TXT_FILES.add_mime_type(mime_type='text/plain')

FILTER_XML_FILES = Gtk.FileFilter()
FILTER_XML_FILES.set_name(name='XML')
FILTER_XML_FILES.add_pattern(pattern='*.xml')
FILTER_XML_FILES.add_mime_type(mime_type='application/xml')

FILTER_ZBS_FILES = Gtk.FileFilter()
FILTER_ZBS_FILES.set_name(name='ZBS')
FILTER_ZBS_FILES.add_pattern(pattern='*.zbs')
FILTER_ZBS_FILES.add_mime_type(mime_type='chart/zbs')

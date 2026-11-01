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
Menu 'Chart' (open, save, import, export, print) and database export/import
"""

import os
from shutil import copyfile
from gi.repository import GLib, Gio, Gtk, Rsvg
from astrochart.state import app
from astrochart.ui.filters import FILTER_ALL_FILES, FILTER_DAT_FILES, FILTER_JPG_FILES, FILTER_OAC_FILES, FILTER_PDF_FILES, FILTER_PNG_FILES, FILTER_SKIF_FILES, FILTER_SQL_FILES, FILTER_SVG_FILES, FILTER_TXT_FILES, FILTER_XML_FILES, FILTER_ZBS_FILES
from astrochart.util import dprint

class FilesMixin:
	"""Menu 'Chart' (open, save, import, export, print) and database export/import"""

	""" Open chart in OAC format """
	def openChart_callback(self, action, parameter):
		gio_list_store = Gio.ListStore.new(Gtk.FileFilter)
		gio_list_store.append(item=FILTER_ALL_FILES)
		gio_list_store.append(item=FILTER_OAC_FILES)
		gio_list_store.append(item=FILTER_TXT_FILES)

		file_dialog = Gtk.FileDialog.new()
		file_dialog.set_title(title=_('Open'))
		file_dialog.set_initial_name(name=_('file-name'))
		file_dialog.set_modal(modal=True)
		file_dialog.set_filters(filters=gio_list_store)
		file_dialog.open(parent=self, callback=self.on_file_dialog_dismissed)

	def on_file_dialog_dismissed(self, file_dialog, gio_task):
		if gio_task.get_name() == 'gtk_file_dialog_open':
			try:
				local_file = file_dialog.open_finish(gio_task)
			except GLib.Error:
				return
			app.importOAC(local_file)
			self.eventData(edit=False)
		elif gio_task.get_name() == 'gtk_file_dialog_save':
			try:
				local_file = file_dialog.save_finish(gio_task)
			except GLib.Error:
				return
			app.exportOAC(local_file)

		"""
		print(f'File name: {local_file.get_basename()}')
		print(f'File path: {local_file.get_path()}')
		print(f'File URI: {local_file.get_uri()}\n')
		"""

	""" Select file to import by FileDialog """
	def file_to_open(self, filters, name, import_app):
		file_dialog = Gtk.FileDialog.new()
		file_dialog.set_title(title=_('Select file to import'))
		file_dialog.set_initial_name(name)
		file_dialog.set_modal(modal=True)
		file_dialog.set_filters(filters=filters)
		file_dialog.open(parent=self, callback=self.on_open_file_dialog_completed, user_data=import_app)

	def on_open_file_dialog_completed(self, file_dialog, gio_task, import_app):
		try:
			local_file = file_dialog.open_finish(gio_task)
		except GLib.Error:
			return
		import_app(local_file)
		self.updateChart()

	""" Import chart in different formats """
	def import_callback(self, action, parameter):
		# mark choosed menu item
		selected = parameter.get_string()
		action.set_state(parameter)
		gio_filters = Gio.ListStore.new(Gtk.FileFilter)
		gio_filters.append(item=FILTER_ALL_FILES)
		#select file formats
		if selected == 'importOroboros':
			gio_filters.append(item=FILTER_XML_FILES)
			self.file_to_open(filters=gio_filters, name='', import_app=app.importOroboros)
		elif selected == 'importAstrolog':
			gio_filters.append(item=FILTER_DAT_FILES)
			self.file_to_open(filters=gio_filters, name='', import_app=app.importAstrolog)
		elif selected == 'importSkylendar':
			gio_filters.append(item=FILTER_SKIF_FILES)
			self.file_to_open(filters=gio_filters, name='', import_app=app.importSkylendar)
		elif selected == 'importZet8':
			gio_filters.append(item=FILTER_ZBS_FILES)
			self.file_to_open(filters=gio_filters, name='', import_app=app.importZet8)

		dprint('Dialog closed, no files selected')

	""" Save chart in OAC format """
	def saveChart_callback(self, action, parameter):
		gio_list_store = Gio.ListStore.new(Gtk.FileFilter)
		gio_list_store.append(item=FILTER_ALL_FILES)
		gio_list_store.append(item=FILTER_OAC_FILES)
		gio_list_store.append(item=FILTER_TXT_FILES)
		file_dialog = Gtk.FileDialog.new()
		file_dialog.set_title(title=_('Save Chart'))
		file_dialog.set_initial_name(name='AstroChart.oac')
		file_dialog.set_modal(modal=True)
		file_dialog.set_filters(filters=gio_list_store)
		file_dialog.save(parent=self, callback=self.on_file_dialog_dismissed)

	""" Select file for saving by FileDialog"""
	def file_to_save(self, filters, name, export_app):
		file_dialog = Gtk.FileDialog.new()
		file_dialog.set_title(title=_('Select file for saving'))
		file_dialog.set_initial_name(name=name)
		file_dialog.set_modal(modal=True)
		file_dialog.set_filters(filters=filters)
		file_dialog.save(parent=self, callback=self.save_file_dialog_completed, user_data=export_app)

	def save_file_dialog_completed(self, file_dialog, gio_task, export_app):
		try:
			local_file = file_dialog.save_finish(gio_task)
		except GLib.Error:
			return
		export_app(local_file)

	def exportPNG(self, local_file):
		os.system("%s %s %s" % ('magick', app.cfg.tempfilename,"'"+local_file.get_path()+"'"))

	def exportJPG(self, local_file):
		os.system("%s %s %s" % ('magick', app.cfg.tempfilename,"'"+local_file.get_path()+"'"))

	def exportSVG(self, local_file):
		copyfile(app.cfg.tempfilename, local_file.get_path())

	def exportPDF(self, local_file):
		#prepare printing into PDF
		settings = Gtk.PrintSettings()
		settings.set_resolution(300)
		print_op = Gtk.PrintOperation()
		print_op.set_unit(Gtk.Unit.MM)
		print_op.set_print_settings(settings)
		print_op.connect("begin_print", self.doPrintBegin)
		print_op.connect("draw_page", self.doPrintDraw)
		print_op.set_export_filename(local_file.get_path())
		result = print_op.run(Gtk.PrintOperationAction.EXPORT, self)
		if result == Gtk.PrintOperationResult.ERROR:
			print_op.cancel()
		return

	""" Export chart in different formats """
	def export_callback(self, action, parameter):
		# mark choosed menu item
		selected = parameter.get_string()
		action.set_state(parameter)
		gio_filters = Gio.ListStore.new(Gtk.FileFilter)
		gio_filters.append(item=FILTER_ALL_FILES)
		#select file formats
		if selected == 'pngfile':
			initial_name = 'AstroData.png'
			gio_filters.append(item=FILTER_PNG_FILES)
			self.file_to_save(filters=gio_filters, name=initial_name, export_app=self.exportPNG)
		elif selected == 'jpgfile':
			initial_name = 'AstroData.jpg'
			gio_filters.append(item=FILTER_JPG_FILES)
			self.file_to_save(filters=gio_filters, name=initial_name, export_app=self.exportJPG)
		elif selected == 'svgfile':
			initial_name = 'AstroData.svg'
			gio_filters.append(item=FILTER_SVG_FILES)
			self.file_to_save(filters=gio_filters, name=initial_name, export_app=self.exportSVG)
		elif selected == 'pdffile':
			initial_name = 'AstroData.pdf'
			gio_filters.append(item=FILTER_PDF_FILES)
			self.file_to_save(filters=gio_filters, name=initial_name, export_app=self.exportPDF)

	""" Print Operations """
	def doPrintBegin(self, operation, context):
		operation.set_n_pages(1)
		operation.set_use_full_page(False)
		ps = Gtk.PageSetup()
		ps.set_orientation(Gtk.PageOrientation.LANDSCAPE)
		ps.set_paper_size(Gtk.PaperSize(Gtk.PAPER_NAME_A4))
		operation.set_default_page_setup(ps)

	""" Render SVG into cairo context """
	def doPrintDraw(self, operation, context, page_nr):
		cr = context.get_cairo_context()
		#draw svg
		printing={}
		printing['pagenum']=page_nr
		printing['width']=context.get_width()
		printing['height']=context.get_height()
		printing['dpi_x']=context.get_dpi_x()
		printing['dpi_y']=context.get_dpi_y()
		#make printing svg
		app.makeSVG(printing=printing)
		svg = Rsvg.Handle.new_from_file(app.cfg.tempfilenameprint)
		#render SVG into cairo context
		if svg is not None:
			cr = Gtk.PrintContext.get_cairo_context(context)
			svg.set_dpi(300)
			viewport = Rsvg.Rectangle()
			viewport.x=0
			viewport.y=0
			viewport.width = Gtk.PrintContext.get_width(context)
			viewport.height = Gtk.PrintContext.get_height(context)
			svg.render_document(cr, viewport)

	"""
	'Extra' Menu Items Functions
	  exportdb
	  importdb
	"""
	def exportdb_callback(self, action, parameter):
		gio_filters = Gio.ListStore.new(Gtk.FileFilter)
		gio_filters.append(item=FILTER_ALL_FILES)
		gio_filters.append(item=FILTER_SQL_FILES)
		self.file_to_save(filters=gio_filters, name='openastro-database.sql', export_app=self.exportSQL)

	def exportSQL(self, local_file):
		copyfile(app.cfg.peopledb, local_file.get_path())

	def importdb_callback(self, action, parameter):
		gio_filters = Gio.ListStore.new(Gtk.FileFilter)
		gio_filters.append(item=FILTER_ALL_FILES)
		gio_filters.append(item=FILTER_SQL_FILES)
		self.file_to_open(filters=gio_filters, name='openastro-database.sql', import_app=self.importSQL)

	def importSQL(self, local_file):
		app.db.databaseMerge(app.cfg.peopledb, local_file.get_path())

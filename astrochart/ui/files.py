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
Menu 'Chart' (open, save, import, export, print) and database export/import,
dialog for the timezone of imported charts with daylight saving time
"""

import pytz
from shutil import copyfile
from gi.repository import GLib, Gio, Gtk, GdkPixbuf, Rsvg
from astrochart.ui.dialog import AstroDialog
from astrochart.ui.event_dialog import EventDialog
from astrochart.ui.filters import FILTER_ALL_FILES, FILTER_DAT_FILES, FILTER_JPG_FILES, FILTER_OAC_FILES, FILTER_PDF_FILES, FILTER_PNG_FILES, FILTER_SKIF_FILES, FILTER_SQL_FILES, FILTER_SVG_FILES, FILTER_TXT_FILES, FILTER_XML_FILES, FILTER_ZBS_FILES
from astrochart.ui.widgets import renderSVG, viewBoxSize
from astrochart.util import dprint

#width in pixels of exported PNG and JPG images (about 300 dpi on A4)
EXPORT_WIDTH = 2400

class ChartFiles:
	"""file dialogs, import, export and printing of the main window"""

	def __init__(self, window):
		self.window = window
		self.chart = window.chart
		self.cfg = window.cfg
		self.db = window.db

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
		file_dialog.open(parent=self.window, callback=self.on_file_dialog_dismissed)

	def on_file_dialog_dismissed(self, file_dialog, gio_task):
		if gio_task.get_name() == 'gtk_file_dialog_open':
			try:
				local_file = file_dialog.open_finish(gio_task)
			except GLib.Error:
				return
			self.chart.importOAC(local_file)
			self.window.presentDialog('event', EventDialog)
		elif gio_task.get_name() == 'gtk_file_dialog_save':
			try:
				local_file = file_dialog.save_finish(gio_task)
			except GLib.Error:
				return
			self.chart.exportOAC(local_file)

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
		file_dialog.open(parent=self.window, callback=self.on_open_file_dialog_completed, user_data=import_app)

	def on_open_file_dialog_completed(self, file_dialog, gio_task, import_app):
		try:
			local_file = file_dialog.open_finish(gio_task)
		except GLib.Error:
			return
		import_app(local_file)

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
			self.file_to_open(filters=gio_filters, name='', import_app=lambda f: self.importChart(self.chart.importOroboros, f))
		elif selected == 'importAstrolog':
			gio_filters.append(item=FILTER_DAT_FILES)
			self.file_to_open(filters=gio_filters, name='', import_app=self.importAstrolog)
		elif selected == 'importSkylendar':
			gio_filters.append(item=FILTER_SKIF_FILES)
			self.file_to_open(filters=gio_filters, name='', import_app=lambda f: self.importChart(self.chart.importSkylendar, f))
		elif selected == 'importZet8':
			gio_filters.append(item=FILTER_ZBS_FILES)
			self.file_to_open(filters=gio_filters, name='', import_app=lambda f: self.importChart(self.chart.importZet8, f))

		dprint('Dialog closed, no files selected')

	def importChart(self, import_app, local_file):
		import_app(local_file)
		self.window.updateChart()

	def importAstrolog(self, local_file):
		#with daylight saving time the user confirms the timezone
		record, timezone_str = self.chart.readAstrolog(local_file)
		def apply(timezone_str):
			self.chart.setAstrolog(record, timezone_str)
			self.window.updateChart()
		if record['daylight']:
			TimezoneDialog(self.window, timezone_str, apply).present()
		else:
			apply(timezone_str)

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
		file_dialog.save(parent=self.window, callback=self.on_file_dialog_dismissed)

	""" Select file for saving by FileDialog"""
	def file_to_save(self, filters, name, export_app):
		file_dialog = Gtk.FileDialog.new()
		file_dialog.set_title(title=_('Select file for saving'))
		file_dialog.set_initial_name(name=name)
		file_dialog.set_modal(modal=True)
		file_dialog.set_filters(filters=filters)
		file_dialog.save(parent=self.window, callback=self.save_file_dialog_completed, user_data=export_app)

	def save_file_dialog_completed(self, file_dialog, gio_task, export_app):
		try:
			local_file = file_dialog.save_finish(gio_task)
		except GLib.Error:
			return
		export_app(local_file)

	def chartImage(self):
		"""the chart shown rendered on white, EXPORT_WIDTH pixels wide"""
		handle = Rsvg.Handle.new_from_data(self.window.chartSVG.encode('utf-8'))
		width, height = viewBoxSize(handle)
		return renderSVG(handle, EXPORT_WIDTH, EXPORT_WIDTH * height / width, background=(1, 1, 1))

	def exportPNG(self, local_file):
		self.chartImage().write_to_png(local_file.get_path())

	def exportJPG(self, local_file):
		surface = self.chartImage()
		width, height = surface.get_width(), surface.get_height()
		#cairo ARGB32 (little endian BGRA, opaque) to RGB
		data = bytes(surface.get_data())
		rgb = bytearray(width * height * 3)
		rgb[0::3] = data[2::4]
		rgb[1::3] = data[1::4]
		rgb[2::3] = data[0::4]
		pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(bytes(rgb)), GdkPixbuf.Colorspace.RGB, False, 8, width, height, width * 3)
		pixbuf.savev(local_file.get_path(), 'jpeg', ['quality'], ['92'])

	def exportSVG(self, local_file):
		with open(local_file.get_path(), 'w') as f:
			f.write(self.window.chartSVG)

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
		result = print_op.run(Gtk.PrintOperationAction.EXPORT, self.window)
		if result == Gtk.PrintOperationResult.ERROR:
			print_op.cancel()
		return

	def printChart_callback(self, action, parameter):
		#print dialog for the printed page of the chart
		print_op = Gtk.PrintOperation()
		print_op.set_unit(Gtk.Unit.MM)
		print_op.connect("begin_print", self.doPrintBegin)
		print_op.connect("draw_page", self.doPrintDraw)
		if print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self.window) == Gtk.PrintOperationResult.ERROR:
			alert_dialog = Gtk.AlertDialog()
			alert_dialog.set_message(_("Error printing"))
			alert_dialog.show(self.window)

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

	""" Render the printed page into the cairo context """
	def doPrintDraw(self, operation, context, page_nr):
		svg = Rsvg.Handle.new_from_data(self.window.chartSVG.encode('utf-8'))
		cr = context.get_cairo_context()
		viewport = Rsvg.Rectangle()
		viewport.x=0
		viewport.y=0
		viewport.width = context.get_width()
		viewport.height = context.get_height()
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
		copyfile(self.cfg.peopledb, local_file.get_path())

	def importdb_callback(self, action, parameter):
		gio_filters = Gio.ListStore.new(Gtk.FileFilter)
		gio_filters.append(item=FILTER_ALL_FILES)
		gio_filters.append(item=FILTER_SQL_FILES)
		self.file_to_open(filters=gio_filters, name='openastro-database.sql', import_app=self.importSQL)

	def importSQL(self, local_file):
		self.db.databaseMerge(self.cfg.peopledb, local_file.get_path())
		self.window.updateUI(first_time=False)

class TimezoneDialog(AstroDialog):
	"""confirm or change the timezone (continent/city) of an imported chart"""

	def __init__(self, window, timezone_str, on_timezone):
		super().__init__(window, title=_("Daylight Saving Time Detected"), modal=True, transient_for=window)
		self.timezone_str = timezone_str
		self.on_timezone = on_timezone
		self.set_default_size(300,100)
		tz_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		tz_box.set_spacing(12)
		tz_box.props.margin_start = 16
		tz_box.props.margin_end = 16
		tz_box.props.margin_top = 16
		tz_box.props.margin_bottom = 16
		header = Gtk.Label(label=_("Change Timezone ?"))
		tz_box.append(header)
		entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		_label = Gtk.Label(label=_("Actual Timezone:"))
		entry_box.append(_label)
		tz_split = timezone_str.split('/')
		_entry = Gtk.Entry()
		_entry.set_max_length(16)
		_entry.set_width_chars(12)
		_entry.set_alignment(xalign=1)
		_entry.set_editable(False)
		_entry.set_text(tz_split[0])
		entry_box.append(_entry)
		_label = Gtk.Label(label=_(" / "))
		entry_box.append(_label)
		self.tz_entry = Gtk.Entry()
		self.tz_entry.set_max_length(32)
		self.tz_entry.set_width_chars(24)
		self.tz_entry.set_text(timezone_str[timezone_str.find('/')+1:])
		self.tz_entry.connect("activate", lambda w: self.submit())
		entry_box.append(self.tz_entry)
		tz_box.append(entry_box)
		hints = Gtk.Label(label=_("Change Timezone and press <Enter>"))
		tz_box.append(hints)
		#cancel keeps the proposed timezone
		tz_box.append(self.buttonRow([(_("OK"), self.submit), (_("Cancel"), lambda: self.done(self.timezone_str))]))
		self.set_child(tz_box)
		self.tz_entry.grab_focus()

	def submit(self):
		s = self.timezone_str
		timezone_str = s[:s.find('/')+1] + self.tz_entry.get_text()
		if timezone_str not in pytz.all_timezones_set:
			self.tz_entry.add_css_class('error')
			return
		self.done(timezone_str)

	def done(self, timezone_str):
		self.close()
		self.on_timezone(timezone_str)

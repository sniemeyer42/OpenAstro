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
Menu 'Tables': monthly timeline and cusp aspects windows
"""

import datetime
from gi.repository import Gio, Gtk, Rsvg
from astrochart.ui.dialog import AstroDialog
from astrochart.ui.filters import FILTER_ALL_FILES, FILTER_PDF_FILES
from astrochart.ui.widgets import ViewSVG

class MonthDialog(AstroDialog):
	"""month and year of the monthly timeline"""

	def __init__(self, window):
		super().__init__(window, title=_("Select Month in Year"))
		self.set_default_size(272, 128)
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		vbox.set_vexpand(True)
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		hbox.set_homogeneous(True)
		label_year = Gtk.Label(label=_('Year')+": ")
		hbox.append(label_year)
		self.spinner = {}
		adjustment = Gtk.Adjustment(lower=1, upper=2400, step_increment=1, page_increment=10)
		self.spinner['Y'] = Gtk.SpinButton()
		self.spinner['Y'].props.adjustment = adjustment
		self.spinner['Y'].set_numeric(True)
		self.spinner['Y'].set_value(datetime.datetime.now().year)
		hbox.append(self.spinner['Y'])
		vbox.append(hbox)
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		hbox.set_homogeneous(True)
		label_month = Gtk.Label(label=_('Month')+": ")
		hbox.append(label_month)
		adjustment = Gtk.Adjustment(lower=1, upper=12, step_increment=1)
		self.spinner['M'] = Gtk.SpinButton()
		self.spinner['M'].props.adjustment = adjustment
		self.spinner['M'].set_numeric(True)
		self.spinner['M'].set_value(datetime.datetime.now().month)
		hbox.append(self.spinner['M'])
		vbox.append(hbox)
		vbox.append(self.buttonRow([(_('OK'), self.submit), (_('Cancel'), self.close)]))
		self.set_child(vbox)

	def submit(self):
		self.close()
		TimelineWindow(self.window, self.spinner['Y'].get_value_as_int(), self.spinner['M'].get_value_as_int()).present()

class TableWindow(AstroDialog):
	"""
	window with a table of the chart (SVG pages), print and PDF export;
	settings is the chart type of the settings it uses ('radix', 'transit'),
	open table windows are redrawn when these settings change
	"""

	settings = 'radix'

	def __init__(self, window, title, size, pdfname):
		super().__init__(window, title=title)
		self.pdfname = pdfname
		self.set_default_size(*size)
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		vbox.set_vexpand(True)
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button = Gtk.Button.new_with_mnemonic(label=_('Print'))
		button.connect("clicked", lambda w: self.printTable(pdf=False))
		button_box.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_('Save as PDF'))
		button.connect("clicked", lambda w: self.printTable(pdf=True))
		button_box.append(button)
		vbox.append(button_box)
		self.image = ViewSVG(self.render())
		self.image.set_vexpand(True)
		self.image.set_hexpand(True)
		self.image.set_valign(Gtk.Align.CENTER)
		self.image.set_halign(Gtk.Align.CENTER)
		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_child(self.image)
		vbox.append(scrolled_window)
		self.set_child(vbox)
		#the main window redraws the open table windows
		window.tableWindows.add(self)
		self.connect('close-request', lambda w: window.tableWindows.discard(self) or False)

	def render(self, printing=None):
		"""SVG document of the table, sets self.chart.pages"""
		raise NotImplementedError

	def refresh(self):
		self.image.setupSVG(self.render())
		self.image.queue_resize()

	def printTable(self, pdf):
		self.print_op = Gtk.PrintOperation()
		self.print_op.set_unit(Gtk.Unit.MM)
		self.print_op.connect("begin_print", self.printBegin)
		self.print_op.connect("draw_page", self.printDraw)
		if pdf:
			gio_filters = Gio.ListStore.new(Gtk.FileFilter)
			gio_filters.append(item=FILTER_ALL_FILES)
			gio_filters.append(item=FILTER_PDF_FILES)
			self.window.files.file_to_save(filters=gio_filters, name=self.pdfname, export_app=self.exportPDF)
			return
		res = self.print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)
		if res == Gtk.PrintOperationResult.ERROR:
			alert_dialog = Gtk.AlertDialog()
			alert_dialog.set_message(_("Error printing"))
			alert_dialog.show(self)

	def exportPDF(self, local_file):
		self.print_op.set_export_filename(local_file.get_path())
		self.print_op.run(Gtk.PrintOperationAction.EXPORT, self)
		self.close()

	def printBegin(self, operation, context):
		#number of pages of the table
		self.render()
		operation.set_n_pages(self.chart.pages)
		operation.set_use_full_page(False)
		ps = Gtk.PageSetup()
		ps.set_orientation(Gtk.PageOrientation.PORTRAIT)
		ps.set_paper_size(Gtk.PaperSize(Gtk.PAPER_NAME_A4))
		operation.set_default_page_setup(ps)

	def printDraw(self, operation, context, page_nr):
		cr = Gtk.PrintContext.get_cairo_context(context)
		#print options
		printing={}
		printing['pagenum']=page_nr
		printing['width']=Gtk.PrintContext.get_width(context)
		printing['height']=Gtk.PrintContext.get_height(context)
		printing['dpi_x']=Gtk.PrintContext.get_dpi_x(context)
		printing['dpi_y']=Gtk.PrintContext.get_dpi_y(context)
		#draw svg for printing
		svg = Rsvg.Handle.new_from_data(self.render(printing).encode('utf-8'))
		viewport = Rsvg.Rectangle()
		viewport.x = 0
		viewport.y = 0
		viewport.width = Gtk.PrintContext.get_width(context)
		viewport.height = Gtk.PrintContext.get_height(context)
		svg.render_document(cr, viewport)

class TimelineWindow(TableWindow):
	"""transits of a month, uses the transit settings"""

	settings = 'transit'

	def __init__(self, window, year, month):
		self.year = year
		self.month = month
		super().__init__(window, "OpenAstro.org Monthly Timeline", (1024, 732), "Timeline-%s.pdf" % (window.chart.name))

	def render(self, printing=None):
		return self.chart.makeTimelineSVG(printing=printing, y=self.year, m=self.month)

class CuspAspectsWindow(TableWindow):
	"""aspects of the planets to the house cusps, uses the radix settings"""

	def __init__(self, window):
		super().__init__(window, "OpenAstro.org Cusp Aspects", (924, 732), "CuspAspects-%s.pdf" % (window.chart.name))

	def render(self, printing=None):
		return self.chart.makeCuspAspectsSVG(printing=printing)

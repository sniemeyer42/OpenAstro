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
from astrochart.state import app
from astrochart.ui.filters import FILTER_ALL_FILES, FILTER_PDF_FILES
from astrochart.ui.widgets import ViewSVG

class TableWindowsMixin:
	"""Menu 'Tables': monthly timeline and cusp aspects windows"""

	"""
	 Menu 'Tables' callbacks
	  MonthlyTimeline
	  MonthlyTimelineShow
	  MonthlyTimelinePrint
	  MonthlyTimelinePrintBegin
	  MonthlyTimelinePrintDraw
	  tableExposeEvent
	  CuspAspects
	"""
	def tableMonthlyTimeline_callback(self, action, parameter):
		self.dialog = Gtk.Window(title=_("Select Month in Year"))
		self.dialog.set_destroy_with_parent(True)
		self.dialog.set_default_size(272, 128)
		#dialog.move(64,128)
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		vbox.set_vexpand(True)
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		hbox.set_homogeneous(True)
		label_year = Gtk.Label(label=_('Year')+": ")
		hbox.append(label_year)
		self.tMTspinner = {}
		adjustment = Gtk.Adjustment(lower=1, upper=2400, step_increment=1, page_increment=10)
		self.tMTspinner['Y'] = Gtk.SpinButton()
		self.tMTspinner['Y'].props.adjustment = adjustment
		self.tMTspinner['Y'].set_numeric(True)
		self.tMTspinner['Y'].set_value(datetime.datetime.now().year)
		hbox.append(self.tMTspinner['Y'])
		vbox.append(hbox)
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		hbox.set_homogeneous(True)
		label_month = Gtk.Label(label=_('Month')+": ")
		hbox.append(label_month)
		adjustment = Gtk.Adjustment(lower=1, upper=12, step_increment=1)
		self.tMTspinner['M'] = Gtk.SpinButton()
		self.tMTspinner['M'].props.adjustment = adjustment
		self.tMTspinner['M'].set_numeric(True)
		self.tMTspinner['M'].set_value(datetime.datetime.now().month)
		hbox.append(self.tMTspinner['M'])
		vbox.append(hbox)
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button_box.set_homogeneous(True)
		#buttons
		button = Gtk.Button.new_with_mnemonic(label=_('Cancel'))
		button.connect("clicked", lambda w: self.dialog.close())
		button_box.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_('OK'))
		button.connect("clicked", lambda w: self.tableMonthlyTimelineShow(spinner=self.tMTspinner))
		button_box.prepend(button)		
		#display window
		vbox.append(button_box)
		self.dialog.set_child(vbox)
		self.dialog.present()

	def tableMonthlyTimelineShow(self, spinner):
		self.dialog.close()
		self.tabletype="timeline"
		self.tMT_year = spinner['Y'].get_value_as_int()
		self.tMT_month = spinner['M'].get_value_as_int()
		app.makeTimelineSVG(printing=None,y=self.tMT_year,m=self.tMT_month)
			#generate window
		self.win_TMT = Gtk.Window()
		self.win_TMT.set_title("OpenAstro.org Monthly Timeline")
		""" >>> set_icon """
		#self.win_TMT.set_icon_from_file(app.cfg.iconWindow)
		self.win_TMT.set_default_size(1024, 732)
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button = Gtk.Button.new_with_mnemonic(label=_('Print'))
		button.connect("clicked", lambda w: self.tablesChartPrint(app.pages,pdf=False,window=self.win_TMT,name="Timeline-%s.pdf"%(app.name)))
		button_box.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_('Save as PDF'))
		button.connect("clicked", lambda w: self.tablesChartPrint(app.pages,pdf=True,window=self.win_TMT,name="Timeline-%s.pdf"%(app.name)))
		button_box.append(button)
		vbox.append(button_box)
		self.win_TMT.image = ViewSVG(app.cfg.tempfilenametable)
		self.win_TMT.image.set_vexpand(True)
		self.win_TMT.image.set_hexpand(True)
		self.win_TMT.image.set_valign(Gtk.Align.CENTER)
		self.win_TMT.image.set_halign(Gtk.Align.CENTER)
		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_child(self.win_TMT.image)
		vbox.append(scrolled_window)
		self.win_TMT.set_child(vbox)
		self.win_TMT.present()

	def tablesChartPrint(self, pages, pdf, window, name):
		settings = None
		window.print_op = Gtk.PrintOperation()
		window.print_op.set_unit(Gtk.Unit.MM)
		if settings != None: 
			window.print_op.set_print_settings(settings)
		window.print_op.connect("begin_print", self.tablesChartPrintBegin, app.pages)
		window.print_op.connect("draw_page", self.tablesChartPrintDraw)
		res = None
		if pdf:
			initial_name = name
			gio_filters = Gio.ListStore.new(Gtk.FileFilter)
			gio_filters.append(item=FILTER_ALL_FILES)
			gio_filters.append(item=FILTER_PDF_FILES)
			self.file_to_save(filters=gio_filters, name=initial_name, export_app=self.tablesChartPDF)
		else:
			res = window.print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, window)		
		if res == Gtk.PrintOperationResult.ERROR:
			error_dialog = Gtk.MessageDialog(window,0,Gtk.MESSAGE_ERROR,Gtk.ButtonS_CLOSE,"Error printing:\n")
			error_dialog.set_destroy_with_parent(True)
			error_dialog.connect("response", lambda w,id: w.destroy())
			error_dialog.show()
		elif res == Gtk.PrintOperationResult.APPLY:
			settings = window.print_op.get_print_settings()

	def tablesChartPDF(self, local_file):
		if (self.tabletype == "timeline"):
			window = self.win_TMT
		elif (self.tabletype == "cuspaspects"):
			window = self.win_TCA
		window.print_op.set_export_filename(local_file.get_path())
		res = window.print_op.run(Gtk.PrintOperationAction.EXPORT, window)
		window.close()

	def tablesChartPrintBegin(self, operation, context, pages):
		operation.set_n_pages(app.pages)
		operation.set_use_full_page(False)
		ps = Gtk.PageSetup()
		ps.set_orientation(Gtk.PageOrientation.PORTRAIT)
		ps.set_paper_size(Gtk.PaperSize(Gtk.PAPER_NAME_A4))
		operation.set_default_page_setup(ps)

	def tablesChartPrintDraw(self, operation, context, page_nr):
		cr = Gtk.PrintContext.get_cairo_context(context)
		#print options
		printing={}
		printing['pagenum']=page_nr
		printing['width']=Gtk.PrintContext.get_width(context)
		printing['height']=Gtk.PrintContext.get_height(context)
		printing['dpi_x']=Gtk.PrintContext.get_dpi_x(context)
		printing['dpi_y']=Gtk.PrintContext.get_dpi_y(context)
		#draw svg
		if(self.tabletype == "timeline"):
			app.makeTimelineSVG(printing=printing,y=self.tMT_year,m=self.tMT_month)
			#draw svg for printing
			svg = Rsvg.Handle.new_from_file(app.cfg.tempfilenametableprint)
		elif(self.tabletype == "cuspaspects"):
			app.makeCuspAspectsSVG(printing=printing)
			#draw svg for printing
			svg = Rsvg.Handle.new_from_file(app.cfg.tempfilenametableprint)
		viewport = Rsvg.Rectangle()
		viewport.x = 0
		viewport.y = 0
		viewport.width = Gtk.PrintContext.get_width(context)
		viewport.height = Gtk.PrintContext.get_height(context)
		svg.render_document(cr, viewport)

	def tableExposeEvent(self, drawing, context):
		if (self.tabletype == "timeline"):
			svg = self.svg_TMT
		elif (self.tabletype == "cuspaspects"):
			svg = self.svg_TCA
		if svg is not None:
			w = svg.get_property("width")
			h = svg.get_property("height")
			drawing.set_size_request(w, h)
			# prepare viewport for display
			viewport = Rsvg.Rectangle()
			viewport.x=0
			viewport.y=0
			viewport.width = w
			viewport.height = h
			svg.render_document(context, viewport)

	def tableCuspAspects_callback(self, action, parameter):
		self.tabletype="cuspaspects"
		app.makeCuspAspectsSVG(printing=None)
		#generate window
		self.win_TCA = Gtk.Window()
		self.win_TCA.set_title("OpenAstro.org Cusp Aspects")
		""" >>> set_icon """
		#self.win_TCA.set_icon_from_file(app.cfg.iconWindow)
		self.win_TCA.set_default_size(924,732)
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		vbox.set_vexpand(True)
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		button = Gtk.Button.new_with_mnemonic(label=_('Print'))
		button.connect("clicked", lambda w: self.tablesChartPrint(pages=1,pdf=False,window=self.win_TCA,name="CuspAspects-%s.pdf"%(app.name)))
		hbox.append(button)
		button = Gtk.Button.new_with_mnemonic(label=_('Save as PDF'))
		button.connect("clicked", lambda w: self.tablesChartPrint(pages=1,pdf=True,window=self.win_TCA,name="CuspAspects-%s.pdf"%(app.name)))
		hbox.append(button)
		vbox.append(hbox)
		self.win_TCA.image = ViewSVG(app.cfg.tempfilenametable)
		self.win_TCA.image.set_vexpand(True)
		self.win_TCA.image.set_hexpand(True)
		self.win_TCA.image.set_valign(Gtk.Align.CENTER)
		self.win_TCA.image.set_halign(Gtk.Align.CENTER)
		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_child(self.win_TCA.image)
		vbox.append(scrolled_window)
		self.win_TCA.set_child(vbox)
		self.win_TCA.present()

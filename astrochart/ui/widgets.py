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
Widgets: scaling SVG view, list item of the event database
"""

import cairo
from gi.repository import GLib, Gtk, Gdk, GObject, Graphene, Rsvg

def renderSVG(handle, width, height, background=None):
	"""cairo image surface of the svg document (Rsvg.Handle) scaled into width x height"""
	surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, int(width)), max(1, int(height)))
	context = cairo.Context(surface)
	if background is not None:
		context.set_source_rgb(*background)
		context.paint()
	viewport = Rsvg.Rectangle()
	viewport.x = 0
	viewport.y = 0
	viewport.width = int(width)
	viewport.height = int(height)
	handle.render_document(context, viewport)
	surface.flush()
	return surface

def viewBoxSize(handle):
	"""width and height of the drawing (view box, else intrinsic size)"""
	dimensions = handle.get_intrinsic_dimensions()
	if dimensions.out_has_viewbox:
		return dimensions.out_viewbox.width, dimensions.out_viewbox.height
	ok, width, height = handle.get_intrinsic_size_in_pixels()
	return (width, height) if ok else (100.0, 100.0)

class ViewSVG(Gtk.Widget):
	"""
	SVG document drawn as vector graphic at the size it is shown: it fits
	into the scrolled window around it (fit 'page': whole page, fit 'width':
	page width, scrolling down), scale is the zoom relative to that fit.
	The drawing is cached; while the size changes the cached drawing is
	stretched and drawn sharp again after a short pause.
	"""

	def __init__(self, svg, fit='page', *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fit = fit
		self.texture = None
		self.textureSize = None
		self.renderPending = 0
		self.setupSVG(svg)
		#ctrl + mouse wheel zooms
		scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.VERTICAL)
		scroll.connect('scroll', self.onScroll)
		self.add_controller(scroll)

	def setupSVG(self, svg):
		self.handle = Rsvg.Handle.new_from_data(svg.encode('utf-8'))
		self.docWidth, self.docHeight = viewBoxSize(self.handle)
		self.scale = 1
		self.texture = None
		self.queue_resize()
		self.queue_draw()

	def setScale(self, scale):
		self.scale = min(4.0, max(0.25, scale))
		self.queue_resize()
		self.queue_draw()

	def onScroll(self, controller, dx, dy):
		if not controller.get_current_event_state() & Gdk.ModifierType.CONTROL_MASK:
			return False
		self.setScale(self.scale * (0.9 if dy > 0 else 1.1))
		return True

	def viewport(self):
		"""size of the visible area: the scrolled window around, else the widget"""
		parent = self.get_parent()
		while parent is not None and not isinstance(parent, Gtk.ScrolledWindow):
			parent = parent.get_parent()
		if parent is not None and parent.get_width() > 0:
			return parent.get_width(), parent.get_height()
		return self.get_width(), self.get_height()

	def drawingSize(self):
		"""size of the drawing: fitted into the viewport, times scale"""
		width, height = self.viewport()
		if width <= 0 or height <= 0:
			width, height = self.docWidth, self.docHeight
		if self.fit == 'width':
			factor = width / self.docWidth
		else:
			factor = min(width / self.docWidth, height / self.docHeight)
		return self.docWidth * factor * self.scale, self.docHeight * factor * self.scale

	def do_get_request_mode(self):
		return Gtk.SizeRequestMode.CONSTANT_SIZE

	def do_measure(self, orientation, for_size):
		#the drawing fits into the viewport: no minimum size, larger
		#drawings (zoom, tables longer than the window) make it scroll
		width, height = self.drawingSize()
		vw, vh = self.viewport()
		if orientation == Gtk.Orientation.HORIZONTAL:
			size = int(width) if width > vw + 1 else 0
		else:
			size = int(height) if height > vh + 1 else 0
		return (size, size, -1, -1)

	def do_snapshot(self, snapshot):
		width, height = self.drawingSize()
		factor = self.get_scale_factor()
		wanted = (int(width * factor), int(height * factor))
		if self.texture is None:
			self.renderTexture(wanted)
		elif self.textureSize != wanted and not self.renderPending:
			#size changes: stretch the last drawing, render it sharp after a pause
			self.renderPending = GLib.timeout_add(80, self.renderLater)
		x = max(0.0, (self.get_width() - width) / 2.0)
		y = max(0.0, (self.get_height() - height) / 2.0)
		point = Graphene.Point()
		point.x, point.y = x, y
		snapshot.save()
		snapshot.translate(point)
		self.texture.snapshot(snapshot, width, height)
		snapshot.restore()

	def renderLater(self):
		self.renderPending = 0
		width, height = self.drawingSize()
		factor = self.get_scale_factor()
		self.renderTexture((int(width * factor), int(height * factor)))
		self.queue_draw()
		return False

	def renderTexture(self, size):
		surface = renderSVG(self.handle, size[0], size[1])
		self.texture = Gdk.MemoryTexture.new(surface.get_width(), surface.get_height(),
			Gdk.MemoryFormat.B8G8R8A8_PREMULTIPLIED, GLib.Bytes.new(bytes(surface.get_data())), surface.get_stride())
		self.textureSize = size

""" EventData to populate ColumnView """
class EventData(GObject.GObject):
	def __init__(self, ident: int, name: str, birth: str, location: str):
		super(EventData, self).__init__()
		self.id = ident
		self.name = name
		self.birth = birth
		self.location = location

def setup(widget, item):
	"""Setup the widget to show in the Gtk.Listview"""
	label = Gtk.Label()
	label.props.xalign = 0.0
	item.set_child(label)

def bind_ident(widget, item):
	"""bind data from the store object to the widget"""
	label = item.get_child()
	obj = item.get_item()
	label.set_label(obj.id)

def bind_name(widget, item):
	"""bind data from the store object to the widget"""
	label = item.get_child()
	obj = item.get_item()
	label.set_label(obj.name)

def bind_birth(widget, item):
	"""bind data from the store object to the widget"""
	label = item.get_child()
	obj = item.get_item()
	label.set_label(obj.birth)

def bind_location(widget, item):
	"""bind data from the store object to the widget"""
	label = item.get_child()
	obj = item.get_item()
	label.set_label(obj.location)

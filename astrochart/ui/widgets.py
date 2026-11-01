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
Widgets: SVG view, list item of the event database
"""

from gi.repository import Gtk, Gdk, GObject

class ViewSVG(Gtk.Widget):
	def __init__(self, path, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# loads now SVG files, Pixbuf not needed anymore
		self.setupSVG(path)

	def setupSVG(self, path):
		self.texture = Gdk.Texture.new_from_filename(path)
		self.scale = 1

	def do_snapshot(self, snapshot):
		width = self.texture.get_intrinsic_width() * self.scale
		height = self.texture.get_intrinsic_height() * self.scale
		self.texture.snapshot(snapshot, width, height)

	def do_get_request_mode(self):
		return Gtk.SizeRequestMode.CONSTANT_SIZE

	def do_measure(self, orientation, for_size):
		if orientation == Gtk.Orientation.HORIZONTAL:
			width = self.texture.get_intrinsic_width() * self.scale
			return (width, width, -1, -1)
		else:
			height = self.texture.get_intrinsic_height() * self.scale
			return (height, height, -1, -1)

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

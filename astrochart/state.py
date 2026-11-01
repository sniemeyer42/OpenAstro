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
The running application as module global `app`.

Transitional: the code refers to the application through the module global
`app`. This proxy forwards attribute access to the instance registered with
set_app(), so the modules can import `app` before the application exists.
"""

_application = None

def set_app(application):
	global _application
	_application = application

def get_app():
	return _application

class _AppProxy:
	__slots__ = ()

	def __getattr__(self, name):
		return getattr(_application, name)

	def __setattr__(self, name, value):
		setattr(_application, name, value)

	def __delattr__(self, name):
		delattr(_application, name)

app = _AppProxy()

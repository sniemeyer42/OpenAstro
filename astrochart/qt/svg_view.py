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
SVG documents drawn with Qt: scaling and scrolling view, images of documents
"""

from PySide6.QtCore import QByteArray, QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QAbstractScrollArea, QFrame

def svgRenderer(svg, parent=None):
	"""renderer of an SVG document given as text"""
	return QSvgRenderer(QByteArray(svg.encode('utf-8')), parent)

def documentSize(renderer):
	"""width and height of the drawing (view box, else default size)"""
	box = renderer.viewBoxF()
	if box.width() > 0 and box.height() > 0:
		return box.width(), box.height()
	size = renderer.defaultSize()
	return (float(size.width()), float(size.height())) if not size.isEmpty() else (100.0, 100.0)

def renderImage(renderer, width, height, background=None):
	"""image of the document scaled into width x height pixels"""
	image = QImage(max(1, int(width)), max(1, int(height)), QImage.Format.Format_ARGB32_Premultiplied)
	image.fill(QColor(background) if background is not None else Qt.GlobalColor.transparent)
	painter = QPainter(image)
	painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing | QPainter.RenderHint.SmoothPixmapTransform)
	renderer.render(painter, QRectF(0, 0, image.width(), image.height()))
	painter.end()
	return image

class SvgView(QAbstractScrollArea):
	"""
	SVG document drawn as vector graphic at the size it is shown: it fits
	into the view (fit 'page': whole page, fit 'width': page width, scrolling
	down), scale is the zoom relative to that fit. The drawing is cached;
	while the size changes the cached drawing is stretched and drawn sharp
	again after a short pause.
	"""

	MIN_SCALE = 0.25
	MAX_SCALE = 4.0

	def __init__(self, svg, fit='page', parent=None):
		super().__init__(parent)
		self.fit = fit
		self.scale = 1.0
		self.pixmap = None
		self.setFrameShape(QFrame.Shape.NoFrame)
		self.renderTimer = QTimer(self)
		self.renderTimer.setSingleShot(True)
		self.renderTimer.setInterval(80)
		self.renderTimer.timeout.connect(self.renderLater)
		self.setupSVG(svg)

	def setupSVG(self, svg):
		"""show a new document at the fitted size"""
		self.setDocument(svg)
		self.scale = 1.0
		self.updateScrollBars()

	def replaceSVG(self, svg):
		"""new drawing of the same document, the zoom stays"""
		self.setDocument(svg)
		self.updateScrollBars()

	def setDocument(self, svg):
		self.renderer = svgRenderer(svg, self)
		self.docWidth, self.docHeight = documentSize(self.renderer)
		self.pixmap = None
		self.viewport().update()

	def setScale(self, scale):
		self.scale = min(self.MAX_SCALE, max(self.MIN_SCALE, scale))
		self.updateScrollBars()
		self.viewport().update()

	def area(self):
		"""size of the view without scroll bars"""
		rect = self.contentsRect()
		return max(1, rect.width()), max(1, rect.height())

	def drawingSize(self):
		"""size of the drawing: fitted into the view, times scale"""
		width, height = self.area()
		if self.fit == 'width':
			factor = width / self.docWidth
			if self.docHeight * factor * self.scale > height:
				#room for the vertical scroll bar
				width -= self.verticalScrollBar().sizeHint().width()
				factor = width / self.docWidth
		else:
			factor = min(width / self.docWidth, height / self.docHeight)
		return self.docWidth * factor * self.scale, self.docHeight * factor * self.scale

	def drawingRect(self):
		"""rectangle of the drawing in viewport coordinates"""
		width, height = self.drawingSize()
		view = self.viewport()
		x = max(0.0, (view.width() - width) / 2.0) - self.horizontalScrollBar().value()
		y = max(0.0, (view.height() - height) / 2.0) - self.verticalScrollBar().value()
		return QRectF(x, y, width, height)

	def updateScrollBars(self):
		width, height = self.drawingSize()
		view = self.viewport()
		if width <= self.area()[0] + 0.5 and height <= self.area()[1] + 0.5:
			#fits without scroll bars (the viewport is smaller while they are shown)
			width, height = 0, 0
		for bar, extent, page in ((self.horizontalScrollBar(), width, view.width()), (self.verticalScrollBar(), height, view.height())):
			bar.setPageStep(max(1, page))
			bar.setSingleStep(max(1, page // 20))
			bar.setRange(0, max(0, int(extent - page + 0.5)))

	def resizeEvent(self, event):
		super().resizeEvent(event)
		self.updateScrollBars()

	def scrollContentsBy(self, dx, dy):
		self.viewport().update()

	def wheelEvent(self, event):
		#ctrl + mouse wheel zooms
		if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
			delta = event.angleDelta().y()
			if delta:
				self.setScale(self.scale * (1.1 if delta > 0 else 1 / 1.1))
			event.accept()
			return
		super().wheelEvent(event)

	def wantedSize(self):
		"""pixel size of the cached drawing for the current size"""
		rect = self.drawingRect()
		ratio = self.devicePixelRatioF()
		return QSize(int(rect.width() * ratio), int(rect.height() * ratio))

	def renderPixmap(self):
		size = self.wantedSize()
		image = renderImage(self.renderer, size.width(), size.height())
		self.pixmap = QPixmap.fromImage(image)
		self.pixmap.setDevicePixelRatio(self.devicePixelRatioF())

	def renderLater(self):
		self.renderPixmap()
		self.viewport().update()

	def paintEvent(self, event):
		painter = QPainter(self.viewport())
		painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
		if self.pixmap is None:
			self.renderPixmap()
		elif self.pixmap.size() != self.wantedSize() and not self.renderTimer.isActive():
			#size changes: stretch the last drawing, render it sharp after a pause
			self.renderTimer.start()
		rect = self.drawingRect()
		painter.drawPixmap(rect, self.pixmap, QRectF(QPointF(0, 0), self.pixmap.size()))
		painter.end()

##############################################################################
#
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.uic import *
from NaNScaN.template import *
from NaNScaN.ocr import *
from NaNScaN.recognizer import *


from TemplateStorageManager import *
from opentemplatedialog import *
from commands import *

from modules.gui.login import LoginDialog
import rpc

class ToolWidget(QWidget):

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		loadUi( 'toolwidget.ui', self )

		for x in TemplateBox.recognizers:
			self.uiRecognizer.addItem( x )

		for x in TemplateBox.types:
			self.uiType.addItem( x )

		for x in TemplateBox.filters:
			self.uiFilter.addItem( x )

		self._box = None
		self.load()
		self.connect( self.uiRecognizer, SIGNAL('activated(QString)'), self.recognizerChanged )

	def recognizerChanged(self, recognizer):
		self.emit(SIGNAL('recognizerChanged(QString)'), recognizer)

	def setText(self, text):
		self.uiText.setText( text )

	def setBox(self, box):
		self._box = box
		self.load()

	def getBox(self):
		return self._box
	box=property(getBox,setBox)

	def store(self):
		if not self._box:
			return
		self._box.rect = QRectF( self.uiX.value(), self.uiY.value(), self.uiWidth.value(), self.uiHeight.value() )
		self._box.recognizer = unicode( self.uiRecognizer.currentText() )
		self._box.type = unicode( self.uiType.currentText() )
		self._box.filter = unicode( self.uiFilter.currentText() )
		self._box.name = unicode( self.uiName.text() )
		self._box.text = unicode( self.uiText.text() )

	def enable(self, value):
		if not value:
			self.uiX.setValue( -1 )
			self.uiY.setValue( -1 )
			self.uiWidth.setValue( -1 )
			self.uiHeight.setValue( -1 )
		self.uiName.clear()
		self.uiText.clear()
		self.uiRecognizer.setEnabled( value )
		self.uiName.setEnabled( value )
		self.uiText.setEnabled( value )
		self.uiType.setEnabled( value )
		self.uiFilter.setEnabled( value )

	def load(self):
		if self._box:
			self.enable( True )
			self.uiX.setValue( self._box.rect.x() )
			self.uiY.setValue( self._box.rect.y() )
			self.uiWidth.setValue( self._box.rect.width() )
			self.uiHeight.setValue( self._box.rect.height() )
			self.uiRecognizer.setCurrentIndex( self.uiRecognizer.findText( self._box.recognizer ) )
			self.uiType.setCurrentIndex( self.uiType.findText( self._box.type ) )
			self.uiFilter.setCurrentIndex( self.uiFilter.findText( self._box.filter ) )
			self.uiText.setText( self._box.text )
			self.uiName.setText( self._box.name )
		else:
			self.enable( False )


class TemplateBoxItem(QGraphicsRectItem):
	def __init__(self, rect, featureRect = None):
		QGraphicsRectItem.__init__(self, rect)
		self.templateBox = None
		if featureRect:
			self.feature = QGraphicsRectItem(featureRect, self)

class DocumentScene(QGraphicsScene):

	CreationMode = 1
	SelectionMode = 2

	MovingState = 1
	CreationState = 2

	def __init__(self, parent=None):
		QGraphicsScene.__init__(self,parent)
		self._imageBoxesVisible = True
		self._templateBoxesVisible = True
		self._featureBoxesVisible = True
		self._binarizedVisible = False
		self._mode = self.CreationMode
		self._selection = None
		self._activeItem = None
		self._imageBoxes = None
		self._templateBoxes = []
		self._activeItemPen = QPen( QBrush( QColor('green') ), 1 )
		self._activeItemBrush = QBrush( QColor( 0, 255, 0, 50 ) )
		self._boxItemPen = QPen( QBrush( QColor( 'red' ) ), 1 )
		self._boxItemBrush = QBrush( QColor( 255, 0, 0, 50 ) )
		self._selectionPen = QPen( QBrush( QColor( 'blue' ) ), 1 )
		self._selectionBrush = QBrush( QColor( 0, 0, 255, 50 ) )
		self._circleItemPen = QPen( QBrush( QColor( 'yellow' ) ), 1 )
		self._circleItemBrush = QBrush( QColor( 255, 255, 0, 50 ) )
		self.state = None
		self.recognizer = None
		self._image = None
		self._oneBitImage = None
		self._template = None
		self.dotsPerMillimeterX = None
		self.dotsPerMillimeterY = None

	def setDocument(self, recognizer):
		self.clearImage()

		self.recognizer = recognizer

		image = self.recognizer.image
		self.dotsPerMillimeterX = float( image.dotsPerMeterX() ) / 1000.0
		self.dotsPerMillimeterY = float( image.dotsPerMeterY() ) / 1000.0
		print "DOTS PER MILLIMETER %s, %s" % (self.dotsPerMillimeterX, self.dotsPerMillimeterY)

		self._image = self.addPixmap( QPixmap.fromImage( image ) )
		self._imageBoxes = self.createItemGroup( [] )
		for i in self.recognizer.boxes('text'):
			#rect = QGraphicsRectItem( i.box, self._imageBoxes )
			rect = QGraphicsRectItem( self.mapRectFromRecognizer( i.box ), self._imageBoxes )
			rect.setPen( self._boxItemPen )
			rect.setBrush( self._boxItemBrush )
			self._imageBoxes.addToGroup( rect )

		for i in self.recognizer.boxes('barcode'):
			#circle = QGraphicsEllipseItem( i.position.x(), i.position.y(), 40, 40 )
			rect = QRectF( i.position.x(), i.position.y(), 40, 40 )
			circle = QGraphicsEllipseItem( self.mapRectFromRecognizer( rect ) )
			circle.setPen( self._circleItemPen )
			circle.setBrush( self._circleItemBrush )
			self._imageBoxes.addToGroup( circle )

		self.setImageBoxesVisible( self._imageBoxesVisible )
		self._imageBoxes.setZValue( 2 )

		self._oneBitImage = self.addPixmap( QPixmap.fromImage( self.recognizer.image ) )
		self._oneBitImage.setZValue( 1 )
		self.setBinarizedVisible( self._binarizedVisible )

		self.setTemplateBoxesVisible( self._templateBoxesVisible )

	def mapRectFromRecognizer(self, rect):
		box = QRectF()
		box.setX( rect.x() * self.dotsPerMillimeterX )
		box.setY( rect.y() * self.dotsPerMillimeterY )
		box.setWidth( rect.width() * self.dotsPerMillimeterX )
		box.setHeight( rect.height() * self.dotsPerMillimeterY )
		return box

	def mapRectToRecognizer(self, rect):
		box = QRectF()
		box.setX( rect.x() / self.dotsPerMillimeterX )
		box.setY( rect.y() / self.dotsPerMillimeterY )
		box.setWidth( rect.width() / self.dotsPerMillimeterX )
		box.setHeight( rect.height() / self.dotsPerMillimeterY )
		return box

	def mapPointFromRecognizer(self, point):
		d = QPointF()
		d.setX( point.x() * self.dotsPerMillimeterX )
		d.setY( point.y() * self.dotsPerMillimeterY )
		return d

	def mapPointToRecognizer(self, point):
		d = QPointF()
		d.setX( point.x() / self.dotsPerMillimeterX )
		d.setY( point.y() / self.dotsPerMillimeterY )
		return d

	def setTemplate(self, template):
		self.clearTemplate()
		self._template = template
		self.connect( template, SIGNAL('boxAdded(PyQt_PyObject)'), self.templateBoxAdded )
		self.connect( template, SIGNAL('boxRemoved(PyQt_PyObject)'), self.templateBoxRemoved )
		for box in self._template.boxes:
			self.addTemplateBox( box )

	def templateBoxAdded(self, box):
		self.addTemplateBox( box )

	def templateBoxRemoved(self, box):
		for x in self._templateBoxes:
			if x.templateBox == box:
				self.removeTemplateBox( x )
				break

	def isEnabled(self):
		if self._template and self.recognizer:
			return True
		else:
			return False

	def clear(self):
		if self._imageBoxes:
			self.destroyItemGroup( self._imageBoxes )
		for x in self.items():
			self.removeItem( x )

	def clearTemplate(self):
		for x in self._templateBoxes:
			self.removeItem( x )
		self._templateBoxes = []

	def clearImage(self):
		if self._imageBoxes:
			# When an Item Group is removed all children
			# are reparented. So remove all children after
			# destroying the group.
			boxes = []
			for x in self._imageBoxes.children():
				boxes.append( x )
			self.destroyItemGroup( self._imageBoxes )
			for x in boxes:
				self.removeItem( x )
		if self._image:
			self.removeItem( self._image )
		if self._oneBitImage:
			self.removeItem( self._oneBitImage )

	def setImageBoxesVisible(self, value):
		self._imageBoxesVisible = value
		if self._imageBoxes:
			self._imageBoxes.setVisible( value )
		
	def setTemplateBoxesVisible(self, value):
		self._templateBoxesVisible = value
		for item in self.items():
			if item and unicode(item.data( 0 ).toString()) == 'TemplateBox':
				item.setVisible( value )

	def setFeatureBoxesVisible(self, value):
		self._featureBoxesVisible = value
		for item in self.items():
			if item and unicode(item.data( 0 ).toString()) == 'TemplateBox':
				item.feature.setVisible( value )

	def setBinarizedVisible(self, value):
		self._binarizedVisible = value
		self._oneBitImage.setVisible( value )

	def setMode(self, mode):
		self._mode = mode

	def setActiveItem(self, item):
		previousBox = None
		if self._activeItem:
			self._activeItem.setPen( self._selectionPen )
			self._activeItem.setBrush( self._selectionBrush )
			previousBox = self._activeItem.templateBox
		currentBox = None
		self._activeItem = item
		if item:
			self._activeItem.setPen( self._activeItemPen )
			self._activeItem.setBrush( self._activeItemBrush )
			currentBox = self._activeItem.templateBox
		self.emit( SIGNAL('currentTemplateBoxChanged(PyQt_PyObject,PyQt_PyObject)'), currentBox, previousBox )

	def activeItem(self):
		return self._activeItem
		
	def createTemplateBox(self, rect):
		item = TemplateBoxItem( rect )
		item.setPen( self._selectionPen )
		item.setBrush( self._selectionBrush )
		item.setZValue( 5 )
		item.setData( 0, QVariant( 'TemplateBox' ) )
		self._templateBoxes.append( item )
		self.addItem( item )
		return item

	def addTemplateBox(self, box):
		item = TemplateBoxItem( self.mapRectFromRecognizer( box.rect ), self.mapRectFromRecognizer( box.featureRect ) )
		item.setPen( self._selectionPen )
		item.setBrush( self._selectionBrush )
		item.setZValue( 5 )
		item.setData( 0, QVariant( 'TemplateBox' ) )
		item.templateBox = box
		item.setVisible( self._templateBoxesVisible )
		self._templateBoxes.append( item )
		self.addItem( item )
		self.setActiveItem( item )
		return item

	def removeTemplateBox(self, item):
		if self._activeItem == item:
			self.setActiveItem( None )	
		self._templateBoxes.remove( item )	
		self.removeItem( item )

	def mousePressEvent(self, event):
		if not self.isEnabled():
			return
		if self._mode == self.CreationMode:
			item = self.itemAt( event.scenePos() )
			if item and unicode(item.data( 0 ).toString()) == 'TemplateBox':
				self.setActiveItem( item )
				return

			rect = QRectF(event.scenePos().x(), event.scenePos().y(), 1, 1)
			self._selection = self.createTemplateBox( rect )
		elif self._mode == self.SelectionMode:
			item = self.itemAt( event.scenePos() )
			if item != self._activeItem:
				self._activeItem.setBrush( QBrush() )
				self._activeItem.setPen( QPen() )
				self._activeItem = item
				self._activeItem.setBrush( self._activeItemBrush )
				self._activeItem.setBrush( self._activeItemBrush )

	def mouseReleaseEvent(self, event):
		if not self.isEnabled():
			return
		if self._mode == self.CreationMode and self._selection:
			# Remove the selection. Currently main window will handle
			# the signaland add the box in the template. 
			rect = self._selection.rect()
			self.removeItem( self._selection )
			self._selection = None
			self.emit( SIGNAL('newTemplateBox(QRectF)'), self.mapRectToRecognizer( rect ) )

	def mouseMoveEvent(self, event):
		if not self.isEnabled():
			return
		if self._mode == self.CreationMode and self._selection:
			rect = self._selection.rect()
			rect.setBottomRight( event.scenePos() )
			self._selection.setRect( rect )
		

class MainWindow(QMainWindow):
	Unnamed = _('unnamed')

	def __init__(self, parent=None):
		QMainWindow.__init__(self, parent)
		loadUi( 'mainwindow.ui', self )
		self.scene = DocumentScene()
		self.uiView.setScene( self.scene )
		self.uiView.setRenderHints( QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform )
		self.uiView.setCacheMode( QGraphicsView.CacheBackground )

		self._template = Template( self.Unnamed )
		self.scene.setTemplate(self._template)

		self.uiTool = ToolWidget( self.uiToolDock )

		self.undoGroup = QUndoGroup( self )
		stack = QUndoStack( self.undoGroup )
		self.undoGroup.setActiveStack( stack )

		# Let default Qt Undo and Redo Actions handle the Undo/Redo actions
		# And put them at the very beggining of the Edit menu
		undoAction = self.undoGroup.createUndoAction( self.menuEdit )
		undoAction.setShortcut( "Ctrl+Z" )
		redoAction = self.undoGroup.createRedoAction( self.menuEdit )
		redoAction.setShortcut( "Ctrl+Shift+Z" )
		if self.menuEdit.actions():
			firstAction = self.menuEdit.actions()[0]
		else:
			firstAction = None
		self.menuEdit.insertAction( firstAction, undoAction )
		self.menuEdit.insertAction( firstAction, redoAction )

		self.connect( self.scene, SIGNAL('newTemplateBox(QRectF)'), self.newTemplateBox )
		self.connect( self.scene, SIGNAL('currentTemplateBoxChanged(PyQt_PyObject,PyQt_PyObject)'), self.currentTemplateBoxChanged)
		self.connect( self.actionExit, SIGNAL('triggered()'), self.close )
		self.connect( self.actionOpenImage, SIGNAL('triggered()'), self.openImage )
		self.connect( self.actionOpenTemplate, SIGNAL('triggered()'), self.openTemplate )
		self.connect( self.actionToggleImageBoxes, SIGNAL('triggered()'), self.toggleImageBoxes )
		self.connect( self.actionToggleTemplateBoxes, SIGNAL('triggered()'), self.toggleTemplateBoxes )
		self.connect( self.actionToggleFeatureBoxes, SIGNAL('triggered()'), self.toggleFeatureBoxes )
		self.connect( self.actionToggleBinarized, SIGNAL('triggered()'), self.toggleBinarized )
		self.connect( self.actionLogin, SIGNAL('triggered()'), self.login )
		self.connect( self.actionSaveTemplate, SIGNAL('triggered()'), self.saveTemplate )
		self.connect( self.actionSaveTemplateAs, SIGNAL('triggered()'), self.saveTemplateAs )
		self.connect( self.actionNewTemplate, SIGNAL('triggered()'), self.newTemplate )
		self.connect( self.actionDelete, SIGNAL('triggered()'), self.removeTemplateBox )
		self.connect( self.actionZoom, SIGNAL('triggered()'), self.zoom )
		self.connect( self.actionUnzoom, SIGNAL('triggered()'), self.unzoom )
		self.connect( self.actionFindMatchingTemplate, SIGNAL('triggered()'), self.findMatchingTemplate )
		self.toggleImageBoxes()
		QTimer.singleShot( 1000, self.setup )
		self.updateTitle()
		self.updateActions()

		self.recognizer = Recognizer()
		self.connect( self.recognizer, SIGNAL('finished()'), self.recognized )

	def setup(self):
		#initOcrSystem()	
		#self.scene.setDocument( 'c-0.tif' )

		self.connect( self.uiTool, SIGNAL('recognizerChanged(QString)'), self.recognizerChanged )
		self.uiTool.show()
		self.uiToolDock.setWidget( self.uiTool )

		#rpc.session.login( 'http://admin:admin@127.0.0.1:8069', 'g1' )

	def findMatchingTemplate(self):
		if not rpc.session.logged():
			if not self.login():
				return 
		templates = TemplateStorageManager.loadAll()
		result = self.recognizer.findMatchingTemplate( templates )
		self._template = result['template'] 
		self.scene.setTemplate(self._template)
		self.updateTitle()
		QMessageBox.information( self, _('Template parameters'), _('Template found with offset (%d, %d)') % (result['xOffset'], result['yOffset']) )

	def recognizerChanged(self, recognizer):
		rect = self.uiTool.box.rect 
		self.uiTool.setText( self.scene.recognizer.textInRegion( rect, recognizer ) )

	def newTemplateBox(self, rect):
		# Creating and adding the box to the template
		# will automatically create the Rect in the Scene
		box = TemplateBox()
		box.rect = rect
		box.text = self.scene.recognizer.textInRegion( rect, 'text' )
		box.featureRect = self.scene.recognizer.featureRectInRegion( rect, 'text' )
		add = AddTemplateBoxUndoCommand( self._template, box )
		self.undoGroup.activeStack().push( add )
		
	#def setCurrentTemplateBox(self, box):
		#if self.uiTool.box:
			#self.uiTool.store()
		#self.uiTool.box = box
	def currentTemplateBoxChanged(self, current, previous):
		if self.uiTool.box:
			self.uiTool.store()
		self.uiTool.box = current
		self.actionDelete.setEnabled( bool(current) )

	def openImage(self):
		self.fileName = QFileDialog.getOpenFileName( self )	
		if self.fileName.isNull():
			return

		QApplication.setOverrideCursor( Qt.BusyCursor )
		self.recognizer.startRecognition( QImage(self.fileName) )

	def recognized(self):
		self.scene.setDocument( self.recognizer )
		QApplication.restoreOverrideCursor()

	def toggleImageBoxes(self):
		self.scene.setImageBoxesVisible( self.actionToggleImageBoxes.isChecked() )	

	def toggleTemplateBoxes(self):
		self.scene.setTemplateBoxesVisible( self.actionToggleTemplateBoxes.isChecked() )

	def toggleFeatureBoxes(self):
		self.scene.setFeatureBoxesVisible( self.actionToggleFeatureBoxes.isChecked() )

	def toggleBinarized(self):
		self.scene.setBinarizedVisible( self.actionToggleBinarized.isChecked() )

	def removeTemplateBox(self):
		if not self.uiTool.box:
			return
		delete = DeleteUndoCommand( self._template, self.uiTool.box )
		self.undoGroup.activeStack().push( delete )

	def zoom(self):
		self.uiView.scale( 1.2, 1.2 )

	def unzoom(self):
		self.uiView.scale( 0.8, 0.8 )

	def login(self):
		LoginDialog.defaultHost = 'localhost'
		LoginDialog.defaultPort = 8070
		LoginDialog.defaultProtocol = 'socket://'
		LoginDialog.defaultUserName = 'admin'
		dialog = LoginDialog( self )
		if dialog.exec_() == QDialog.Rejected:
			return False
		if rpc.session.login( dialog.url, dialog.databaseName ) > 0:
			self.updateTitle()
			return True
		else:
			self.updateTitle()
			return False

	def newTemplate(self):
		answer = QMessageBox.question(self, _('New Template'), _('Do you want to save changes to the current template?'), QMessageBox.Save | QMessageBox.No | QMessageBox.Cancel )
		if answer == QMessageBox.Cancel:
			return
		elif answer == QMessageBox.Save:
			if not self.saveTemplate():
				return
		self._template = Template( self.Unnamed )	
		self.scene.setTemplate( self._template )
		self.updateTitle()

	def saveTemplate(self):
		self.uiTool.store()
		if not rpc.session.logged():
			if not self.login():
				return False

		if not self._template.id:
			(name, ok) = QInputDialog.getText( self, _('Save template'), _('Template name:') )
			if not ok:
				return False
			self._template.name = unicode(name)
				

		if self._template.id:
			rpc.session.call( '/object', 'execute', 'nan.template', 'write', [self._template.id], {'name': self._template.name } )
			ids = rpc.session.call( '/object', 'execute', 'nan.template.box', 'search', [('template_id','=',self._template.id)] )
			rpc.session.call( '/object', 'execute', 'nan.template.box', 'unlink', ids )
		else:
			self._template.id = rpc.session.call( '/object', 'execute', 'nan.template', 'create', {'name': self._template.name } )
		for x in self._template.boxes:
			values = { 
				'x': x.rect.x(), 
				'y': x.rect.y(), 
				'width': x.rect.width(), 
				'height': x.rect.height(), 
				'feature_x' : x.featureRect.x(),
				'feature_y' : x.featureRect.y(),
				'feature_width' : x.featureRect.width(),
				'feature_height' : x.featureRect.height(),
				'template_id': self._template.id, 
				'name': x.name, 
				'text': x.text, 
				'recognizer': x.recognizer, 
				'type': x.type, 
				'filter': x.filter 
			}
			rpc.session.call( '/object', 'execute', 'nan.template.box', 'create', values )
		self.updateTitle()
		return True

	def saveTemplateAs(self):
		id = self._template.id
		self._template.id = 0
		if not self.saveTemplate():
			self._template.id = id
		self.updateTitle()

	def openTemplate(self):
		if not rpc.session.logged():
			if not self.login():
				return

		dialog = OpenTemplateDialog(self)
		if dialog.exec_() == QDialog.Rejected:
			return
		model = dialog.group[dialog.id]
		self._template = Template( model.value('name') )
		self._template.id = model.id

		fields = rpc.session.execute('/object', 'execute', 'nan.template.box', 'fields_get')
		model.value('boxes').addFields( fields )
		for x in model.value('boxes'):
			box = TemplateBox()
			box.rect = QRectF( x.value('x'), x.value('y'), x.value('width'), x.value('height') )
			box.featureRect = QRectF( x.value('feature_x'), x.value('feature_y'), 
						  x.value('feature_width'), x.value('feature_height') )
			box.name = x.value('name')
			box.text = x.value('text')
			box.recognizer = x.value('recognizer')
			box.type = x.value('type')
			box.filter = x.value('filter')
			self._template.addBox( box )

		self.scene.setTemplate(self._template)
		self.updateTitle()

	def updateTitle(self):
		self.setWindowTitle( "Planta - [%s]" % self._template.name )
		
		if rpc.session.logged():
			server = '%s [%s]' % (rpc.session.url, rpc.session.databaseName)
		else:
			shortcut = unicode( self.actionLogin.shortcut().toString() )
			if shortcut:
				server = _('Press %s to login') % shortcut
			else:
				server = 'not logged in'
		self.statusBar().showMessage( server )

	def updateActions(self):
		# Allow deleting if there's a TemplateBox selected
		self.actionDelete.setEnabled( bool(self.uiTool.box) )

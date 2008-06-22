from scanner import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.uic import *
import gettext
import locale
import gc

locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain('nanscan', '.')
gettext.textdomain('nanscan')
gettext.install('nanscan', '.', unicode=1)



class ImageItem(QListWidgetItem):
	def __init__(self, parent=None):
		QListWidgetItem.__init__(self, parent)
		self.image = None
		self.name = None
		self.mark = None

	def setName(self, name):
		self.name = name

	# Image should be a QImage
	def setImage(self, image):
		self.image = image
		self.updateIcon()
		
	# Mark should be a QImage
	def setMark(self, mark):
		self.mark = mark
		self.updateIcon()

	def updateIcon(self):
		if not self.image or not self.mark:
			return

		image = self.image.scaled( self.listWidget().iconSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation )
		painter = QPainter( image )
		painter.drawImage( 5, 5, self.mark )
		painter.end()
		self.setIcon( QIcon( QPixmap.fromImage( image ) ) )

class ScanDialog(QDialog):
        def __init__(self, parent=None):
                QDialog.__init__(self, parent)
		
		dir = os.path.abspath( os.path.dirname(__file__) )
		QResource.registerResource( os.path.join(dir,'common.rcc') )
		loadUi( os.path.join(dir,'scandialog.ui'), self )

		self.connect( self.pushAccept, SIGNAL('clicked()'), self.accept )
		self.connect( self.pushScan, SIGNAL('clicked()'), self.scan )
		self.connect( self.pushDuplexScan, SIGNAL('clicked()'), self.duplexScan )
		self.uiList.setIconSize( QSize( 128, 128 ) )
		self.saving = QSemaphore()
		self.setScanning( False )

		# By default images are stored as files in 
		# the temporary directory. The application
		# may choose to override the 'thread' propery
		# with an appropiate SaveThreaded() subclass
		self.saveClass = FileSaveThreaded

	def closeEvent(self, event):
		if self.hasFinished:
			event.accept()
		else:
			event.ignore()

	def setScanning(self, value):
		self.scanning = value
		self.updateAccept()

	def addSaving(self):
		self.saving.release()
		self.updateAccept()
	
	def removeSaving(self):
		self.saving.acquire()
		self.updateAccept()

	def updateAccept(self):
		if self.scanning or self.saving.available():
			self.hasFinished = False
			self.pushAccept.setEnabled( False )
			self.pushScan.setEnabled( False )
			self.pushDuplexScan.setEnabled( False )
			self.setCursor( Qt.BusyCursor )
		else:
			self.hasFinished = True
			self.pushAccept.setEnabled( True )
			self.pushScan.setEnabled( True )
			self.pushDuplexScan.setEnabled( True )
			self.unsetCursor()

        def scan(self):
		self.setScanning( True )
                self.scan = Scanner(self)
		self.scan.setDuplex( False )
                self.connect( self.scan, SIGNAL('scanned(QImage)'), self.scanned )
		self.connect( self.scan, SIGNAL('error(int)'), self.error )
		self.connect( self.scan, SIGNAL('finished()'), self.finished )
                self.scan.startScan()

	def duplexScan(self):
		self.setScanning( True )
                self.scan = Scanner(self)
		self.scan.setDuplex( True )
                self.connect( self.scan, SIGNAL('scanned(QImage)'), self.scanned )
		self.connect( self.scan, SIGNAL('error(int)'), self.error )
		self.connect( self.scan, SIGNAL('finished()'), self.finished )
                self.scan.startScan()

	def error(self, code):
		if code == ScannerError.NoDeviceFound:
			message = 'No device found'
		elif code == ScannerError.CouldNotOpenDevice:
			message = 'Could not open device'
		elif code == ScannerError.AcquisitionError:
			message = 'Error acquiring image'
		else:
			message = 'Unknown error'
		self.setScanning( False )
		QMessageBox.critical( self, 'Scanning Error', message )

        def scanned(self, image):
		item = ImageItem( self.uiList )
		item.setImage( image ) 
		item.setMark( QImage( ':/images/images/save.png' ) )
		item.setName( 'scanned image ' + unicode( QDateTime.currentDateTime().toString() ) )
		item.setToolTip( _('Saving image...') )

		self.uiList.addItem( item )

		self.addSaving()
		if self.saveClass:
			thread = self.saveClass( self )
			thread.item = item
			self.connect( thread, SIGNAL('finished()'), self.saved )
			thread.start()

	def finished(self):
		self.setScanning( False )

	def saved(self):
		self.removeSaving()
		thread = self.sender()

		if not thread.error:
			thread.item.setMark( QImage( ':/images/images/ok.png' ) )
			thread.item.setToolTip( _('Image stored successfully') )
		else:
			thread.item.setMark( QImage( ':/images/images/cancel.png' ) )
			thread.item.setToolTip( _('Error storing image') )
			
		# Free memory used by the BIG image
		thread.item.image = None
		gc.collect()



## @brief Base class for saving the image once scanned.
class SaveThreaded(QThread):
	def __init__(self, parent=None):
		QThread.__init__(self, parent)
		self.item = None
		self.error = True

## @brief This class stores an image into a file in the directory
# specified by 'directory' (temporary directory by default).
class FileSaveThreaded(SaveThreaded):
	directory = unicode( QDir.tempPath() )

	def __init__(self, parent=None):
		SaveThreaded.__init__(self, parent)

	def run(self):
		self.error = True
		d = QDir( FileSaveThreaded.directory )
		d.setSorting( QDir.Name )
		l = d.entryList( ['*.png'] )
		if l:
			last = l[-1]
			last = last.split('.')[0]
			last = int(last)
		else:
			last = 0
		next = "%06d.png" % (last + 1)
		next = os.path.join( FileSaveThreaded.directory, next )
		print "saving: ", next
		if self.item.image.save( next, 'PNG' ):
			self.error = False

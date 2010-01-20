#   Copyright (C) 2008 by Albert Cervera i Areny
#   albert@nan-tic.com
#
#   This program is free software; you can redistribute it and/or modify 
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or 
#   (at your option) any later version. 
#
#   This program is distributed in the hope that it will be useful, 
#   but WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License 
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA. 

from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Current backend should set ScannerBackend to the class
# implementing the Synchronous interface
ScannerBackend = None

class ScannerError:
	NoDeviceFound = 1
	CouldNotOpenDevice = 2
	AcquisitionError = 3
	UnknownError = 4

class Scanner(QObject):
	def __init__(self, parent=None):
		QObject.__init__(self, parent)
		self.resolution = 300
		self.duplex = False

	def listDevices(self):
		scan = ScannerBackend(self)
		devices = scan.listDevices()
		scan.close()
		return devices

	def setResolution(self, value):
		self.resolution = value

	def setDuplex(self, value):
		self.duplex = value

	def startScan(self):
		self.thread = ThreadedScan(self)
		self.thread.resolution = self.resolution
		self.thread.duplex = self.duplex
		self.connect( self.thread, SIGNAL('finished()'), self, SIGNAL('finished()') )
		self.connect( self.thread, SIGNAL('scanned(QImage)'), self, SIGNAL('scanned(QImage)') )
		self.connect( self.thread, SIGNAL('error(int)'), self, SIGNAL('error(int)') )
		self.thread.start()

class ThreadedScan(QThread):
	def __init__(self, parent=None):
		QThread.__init__(self, parent)
		self.resolution = 300
		self.duplex = False

	def run(self):
		s = ScannerBackend()
		s.setResolution( self.resolution )
		s.setDuplex( self.duplex )
		self.connect( s, SIGNAL('scanned(QImage)'), self.scanned, Qt.QueuedConnection )
		self.connect( s, SIGNAL('error(int)'), self, SIGNAL('error(int)'), Qt.QueuedConnection )
		s.scan()
		s.close()

	def scanned(self, image):
		# As we're now out of the thread, we create a new QImage
		# object, otherwise the application will crash
		self.emit( SIGNAL('scanned(QImage)'), QImage( image ) )


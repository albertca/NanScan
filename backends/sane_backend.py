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
import sane
# PIL Module to convert PIL Image Object to QImage
import ImageQt
import common

class SynchronousScanner(QObject):

	def __init__(self, parent=None):
		QObject.__init__(self, parent)
		sane.init()
		self.resolution = 300
	
	# Member of SynchronousScanner Interface
	def listDevices(self):
		# sane.get_devices() returns an structure like the following
		# [('epson:libusb:001:004', 'Epson', 'GT-8300', 'flatbed scanner')]
		return [x[0] for x in sane.get_devices()]

	# Member of SynchronousScanner Interface
	def setResolution(self, value):
		self.resolution = value

	# Member of SynchronousScanner Interface
	def scan(self, name=None):
		if not name:
			devices = self.listDevices()
			if not devices:
				self.emit( SIGNAL('error(int)'), common.ScannerError.NoDeviceFound )
				return
			name = devices[0]

		try:
			print "Trying to open device: ", name
			source = sane.open( name )
			print "opened ", name
		except:
			print "error", name
			self.emit( SIGNAL('error(int)'), common.ScannerError.CouldNotOpenDevice )
			return
			
		source.mode = 'color'
		source.resolution = self.resolution
		source.depth = 32

		print "Multi scan"
		iterator = source.multi_scan()
		print "yea scan"
		while True:
			try:
				print "Obtaining image..."
				image = ImageQt.ImageQt( iterator.next() )
				print "Obtain"
				res = float(self.resolution) * 1000 / 25.4
				image.setDotsPerMeterX( res )
				image.setDotsPerMeterY( res )
				self.emit( SIGNAL('scanned(QImage)'), image )
			except StopIteration, e:
				# If StopIteration is raised, then there are no more images in 
				# the scanner
				pass
			except:
				self.emit( SIGNAL('error(int)'), common.ScannerError.AcquisitionError )

	# Member of SynchronousScanner Interface
	def close(self):
		pass
				
				
common.ScannerBackend = SynchronousScanner

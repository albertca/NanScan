import sys

if sys.version_info[:2] == (2, 5):
	import twain25 as twain 
else:
	import twain26 as twain

import struct
import string
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import Common

class SynchronousScanner(QObject):

	def __init__(self, parent=None):
		QObject.__init__(self, parent)
		self.manager = None
		self.source = None
		self.resolution = 300
		self.duplex = False
	
	def stripNull(self, s):
		offset = string.find(s, '\0')
		if s != -1:
			s= s[:offset]
		return s

	# Member of SynchronousScanner Interface
	def setResolution(self, value):
		self.resolution = value

	# Member of SynchronousScanner Interface
	def setDuplex(self, value):
		self.duplex = value

	# Member of SynchronousScanner Interface
	def listDevices(self):
		manager = twain.SourceManager(0L) 
		fmtString = "L42sHH4s34s34s34s"
		slen = struct.calcsize(fmtString)
		self.identity = struct.pack("%ds" % slen, "")
		
		rv = manager.DSM_Entry(twain.DG_CONTROL, twain.DAT_IDENTITY, twain.MSG_GETFIRST, self.identity)
		
		l = []
		while rv == twain.TWRC_SUCCESS:
			l.append( self.stripNull( self.identity[122:] ) )
			rv = manager.DSM_Entry(twain.DG_CONTROL, twain.DAT_IDENTITY, twain.MSG_GETNEXT, self.identity)
		return l
	
	def open(self, name):
		self.manager = twain.SourceManager( 0, ProductName=name )
		if not self.manager:
			return
		
		if self.source:
			self.source.destroy()
			self.source=None
		self.source = self.manager.OpenSource()
		if self.source:
			print "%s: %s" % ( name, self.source.GetSourceName() )
	
	# Member of SynchronousScanner Interface
	def scan(self, name=None):
		if not name:
			l = self.listDevices()
			if not l:
				print "No device found"
				return Common.ScannerError.NoDeviceFound
			name = l[0]

		try:
			self.open(name)
		except:
			return Common.ScannerError.CouldNotOpenDevice
		if not self.source:
			return Common.ScannerError.CouldNotOpenDevice
		
		try:
			self.source.SetCapability( twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, float(self.resolution) )
			self.source.SetCapability( twain.ICAP_XRESOLUTION, twain.TWTY_FIX32, float(self.resolution) )
		except:
			print "Could not set resolution to '%s'" % self.resolution
			pass

		try:
			self.source.SetCapability( twain.CAP_DUPLEXENABLED, twain.TWTY_BOOL, bool(self.duplex) )
		except:
			print "Could not set duplex to '%s'" % self.duplex
			pass
		try:
			self.source.RequestAcquire(0, 0)
		except:
			return Common.ScannerError.AcquisitionError
		
		while self.next():
			image = self.capture()
			if not image:
				return Common.ScannerError.AcquisitionError
			self.emit( SIGNAL('scanned(QImage)'), image )
		self.source = None
		self.emit( SIGNAL('finished()') )

	def next(self):
		try:
			self.source.GetImageInfo()
			return True
		except:
			return False
		
	def capture(self):
		fileName = "tmp.tmp"
		try:
			(handle, more_to_come) = self.source.XferImageNatively()
		except:
			return None	
		twain.DIBToBMFile(handle, fileName)
		twain.GlobalHandleFree(handle)
		image = QImage( fileName )
		res = float( self.resolution ) * 1000 / 25.4
		image.setDotsPerMeterX( res )
		image.setDotsPerMeterY( res )
		return image
	
	# Member of SynchronousScanner Interface
	def close(self):
		del self.manager

Common.ScannerBackend = SynchronousScanner

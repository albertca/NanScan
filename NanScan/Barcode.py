#   Copyright (C) 2008-2009 by Albert Cervera i Areny
#   albert@nan-tic.com
#
#   This program is free software; you can redistribute it and/or modify 
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or 
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
# Do not import everything as Template is defined in string too
from string import lower
import os
import tempfile
from TemporaryFile import *
from Analyzer import *

class Box:
	def __init__(self):
		self.text = None
		self.type = None
		self.position = None

## @brief Scans an image for barcodes.
class Barcode(Analyzer):
	def __init__(self):
		self.boxes = []

	def parseBardecodeOutput(self, content):
		# Sample output "818043376500 [type: ean13 at: (1798,936)]"
		for line in content.splitlines():
			pieces = line.split( ' ' )
			box = Box()
			box.text = lower(pieces[0])
			box.type = pieces[2]
			pos = pieces[4].strip( '()]' ).split(',')

			x = float(pos[0]) / self.dotsPerMillimeterX
			y = float(pos[1]) / self.dotsPerMillimeterY
			box.position = QPointF( x, y )
			self.boxes.append( box )

	def parseZBarImgOutput(self, content):
		# Sample output "CODE-39:00017"
		for line in content.splitlines():
			pieces = line.split(':')
			box = Box()
			box.text = lower(pieces[1])
			box.type = pieces[0]
			box.position = QPointF(0.0, 0.0)
			self.boxes.append( box )

	def printBoxes(self):
		for x in self.boxes:
			print "Text: %s, Type: %s, Position: %f, %f" % (x.text, x.type, x.position.x(), x.position.y())
		
	## @brief Returns all barcode values concatenated for a given region of the image. 
	def textInRegion(self, region=None):
		for x in self.boxes:
			if not region or region.contains(x.position):
				return unicode(x.text)
		# Always return unicode strings
		return u''

	## @brief Returns the bounding rectangle of the text returned by textInRegion for
	# the given region.
	def featureRectInRegion(self, region=None):
		rect = QRectF()
		for x in self.boxes:
			if not region or region.contains(x.position):
				rect = rect.united( QRectF( x.position, x.position ) )
		return rect

	## @brief Scans the given image (QImage) looking for barcodes.
	def scanBardecode(self, image):
		# Clean boxes so scan() can be called more than once
		self.boxes = []

		# Obtain image resolution
		image = QImage( image )
		self.dotsPerMillimeterX = float( image.dotsPerMeterX() ) / 1000.0
		self.dotsPerMillimeterY = float( image.dotsPerMeterY() ) / 1000.0

		fileName = TemporaryFile.create()
		# Use BMP format instead of PNG, for performance reasons. 
		# BMP takes about 0.5 seconds whereas PNG takes 13.
		image.save( fileName, 'BMP' )
		command = 'bardecode'
		content = self.spawn( command, fileName )
		TemporaryFile.remove( fileName )
		self.parseBardecodeOutput( content )
		self.printBoxes()

	## @brief Scans the given image (QImage) looking for barcodes.
	def scan(self, image):
		# Clean boxes so scan() can be called more than once
		self.boxes = []

		# Obtain image resolution
		image = QImage( image )
		self.dotsPerMillimeterX = float( image.dotsPerMeterX() ) / 1000.0
		self.dotsPerMillimeterY = float( image.dotsPerMeterY() ) / 1000.0

		fileName = TemporaryFile.create( '.bmp' )
		# Use BMP format instead of PNG, for performance reasons. 
		# BMP takes about 0.5 seconds whereas PNG takes 13.
		print image.save( fileName, 'BMP' )
		command = 'zbarimg'
		content = self.spawn( command, fileName )
		TemporaryFile.remove( fileName )
		self.parseZBarImgOutput( content )
		self.printBoxes()

Analyzer.registerAnalyzer( 'barcode', Barcode )

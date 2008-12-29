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
# Do not import everything as Template is defined in string too
from string import lower
import os
import tempfile
from TemporaryFile import *
from Analyzer import *

class Box:
	def __init__(self):
		self.text = None
		self.position = None
		self.size = None
		self.dataCodewords = None
		self.errorCodewordsd = None
		self.dataRegions = None
		self.interleavedBlocks = None
		self.rotationAngle = None
		self.box = None

class DataMatrix(Analyzer):
	def __init__(self):
		self.boxes = []

	# Spawn process and return STDOUT

	def outputTextToPoint(self, text):
		pos = text.strip('(').strip(')').split(',')
		x = float(pos[0]) / self.dotsPerMillimeterX
		y = float(pos[1]) / self.dotsPerMillimeterY
		return QPointF( x, y )

	def parseOutput(self, content):
		# Each datamatrix is a line of the output
		nextText = False
		box = None
		lines = content.splitlines()
		for x in xrange(len(lines)):
			line = lines[x]
			if not box and line == ('-' * 50):
				continue

			if not box:
				box = Box()
				self.boxes.append( box )

			if nextText:
				box.text = line
				nextText = False
				box = None
				continue
			if line == ('-' * 50):
				nextText = True
				continue

			key, value = line.split(':')
			value = value.strip()
			if 'Matrix Size' in key:
				box.size = value
			elif 'Data Codewords' in key:
				box.dataCodewords = value
			elif 'Error Codewords' in key:
				box.errorCodewords = value
			elif 'Data Regions' in key:
				box.dataRegions = value
			elif 'Interleaved Blocks' in key:
				box.interleavedBlocks = value
			elif 'Rotation Angle' in key:
				box.rotationAngle = value
			elif 'Corner 0' in key:
				box.corner0 = self.outputTextToPoint( value )
			elif 'Corner 1' in key:
				box.corner1 = self.outputTextToPoint( value )
			elif 'Corner 2' in key:
				box.corner2 = self.outputTextToPoint( value )
			elif 'Corner 3' in key:
				box.corner3 = self.outputTextToPoint( value ) 
				r1 = QRectF( box.corner0, box.corner1 )
				r2 = QRectF( box.corner2, box.corner3 )
				box.box = r1.united( r2 )

	def printBoxes(self):
		for x in self.boxes:
			print "Text: '%s';  Position: %f, %f;  Size: %f, %f;" % (x.text, x.box.x(), x.box.y(), x.box.width(), x.box.height() )
		
	## @brief Returns all data matrix values concatenated for a given region of the image. 
	def textInRegion(self, region):
		texts = []
		for x in self.boxes:
			if region.intersects(x.box):
				texts.append( unicode(x.text) )

		# Always return unicode strings
		return u''.join( texts )

	## @brief Returns the bounding rectangle of the text returned by textInRegion for
	# the given region.
	def featureRectInRegion(self, region):
		rect = QRectF()
		for x in self.boxes:
			if region.intersects(x.box):
				rect = rect.united( x.box )
		return rect

	## @brief Scans the given image (QImage) looking for barcodes.
	def scan(self, image):
		# Clean boxes so scan() can be called more than once
		self.boxes = []

		# Obtain image resolution
		image = QImage( image )
		self.dotsPerMillimeterX = float( image.dotsPerMeterX() ) / 1000.0
		self.dotsPerMillimeterY = float( image.dotsPerMeterY() ) / 1000.0

		file = TemporaryFile.create()
		image.save( file, 'PNG' )
		command = 'dmtxread'
		content = self.spawn( command, '-n', '-v', file )
		self.parseOutput( content )
		self.printBoxes()

Analyzer.registerAnalyzer( 'dataMatrix', DataMatrix )

if __name__ == '__main__':
	d = DataMatrix()
	d.scan( '/tmp/ex3.png' )


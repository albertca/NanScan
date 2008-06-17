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

import os
# Do not import everything as Template is defined in string too
from string import lower
import codecs
import tempfile
import shutil

from gamera.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Character:
	def __init__(self):
		self.character = None
		self.box = None

def boxComparison(x, y):
	if x.box.x() > y.box.x():
		return 1
	elif x.box.x() < y.box.x():
		return -1
	else:
		return 0

class Ocr:
	file = ""

	def ocr(self):
		directory = tempfile.mkdtemp()
		path = os.path.join( directory, 'tesseract' )
		os.spawnlp(os.P_WAIT, 'tesseract', 'tesseract', self.file, path, '-l', 'spa', 'batch.nochop', 'makebox' )
		f=codecs.open(path + '.txt', 'r', 'utf-8')
		content = f.read()
		f.close()
		shutil.rmtree(directory, True)
		return content

	def parseTesseractOutput(self, input):
		output = []
		# Output example line: "w 116 1724 133 1736"
		# Coordinates start at bottom left corner but we convert this into top left.
		# Convert pixel coordinates into millimeters too.
		for x in input.split('\n'):
			if not x:
				continue
			line = x.split(' ')
			x1 = int(line[1])
			x2 = int(line[3])
			y1 = self.height - int(line[2])
			y2 = self.height - int(line[4])
			width = x2 - x1
			height = y1 - y2

			c = Character()
			c.character = line[0] 

			x1 = float(x1) / self.dotsPerMillimeterX
			width = float(width) / self.dotsPerMillimeterX
			y2 = float(y2) / self.dotsPerMillimeterY
			height = float(height) / self.dotsPerMillimeterY
			c.box = QRectF( x1, y2, width, height )
			output.append( c )
		return output

	def textInRegion(self, region):
		output = []
		for x in self.boxes:
			r = region.intersected(x.box)
			if r.isValid():
				output.append(x.character)
		# We always return unicode strings 
		return u''.join(output)
		
	# Uses convert to convert into gray scale
	def convertToGray(self, input, output):
		os.spawnlp(os.P_WAIT, 'convert', 'convert', '-type', 'grayscale', '-depth', '8', input, output)

	# Uses Gamera OTSU threashold algorithm to convert into binary
	def convertToBinary(self, input, output):
		image = load_image(input)
		# Converting
		img = image.to_greyscale()
		# Thresholding 
		onebit = img.otsu_threshold()
		# Saving for tesseract processing
		onebit.save_tiff(output)
		
	def scan(self, file):
		image = QImage( file )
		self.width = image.width()
		self.height = image.height()
		self.dotsPerMillimeterX = float( image.dotsPerMeterX() ) / 1000.0
		self.dotsPerMillimeterY = float( image.dotsPerMeterY() ) / 1000.0
		
		#self.convertToBinary(file, '/tmp/tmp.tif')
		self.convertToGray(file, '/tmp/tmp.tif')
		self.file = "/tmp/tmp.tif"

		txt = lower( self.ocr() )

		self.boxes = self.parseTesseractOutput(txt)

	def firstBox(self, boxes):
		top = None
		for x in boxes:
			if not top or x.box.y() < top.box.y():
				top = x
		return top

	def formatedText(self, region=None):
		if region:
			# Filter out boxes not in the given region
			boxes = []
			for x in self.boxes:
				if region.intersects(x.box):
					boxes.append(x)
		else:
			# Copy as we'll remove items from the list
			boxes = self.boxes[:]

		lines = []
		while boxes:
			box = self.firstBox( boxes )
			boxes.remove( box )
			line = []
			line.append( box )
			toRemove = []
			for x in boxes:
				if x.box.top() > box.box.bottom():
					continue
				elif x.box.bottom() < box.box.top():
					continue
				line.append( x )
				toRemove.append( x )

			for x in toRemove:
				boxes.remove( x )
			lines.append( line )

		# Now that we have all boxes in its line. Sort each of
		# them
		for line in lines:
			line.sort( boxComparison )


		# Now we have all lines with their characters in their positions
		# Here we write them in a text and add spaces appropiately. 
		# In order to not be distracted with character widths of letters
		# like 'm' or 'i' (which are very wide and narrow), the average
		# width of the letters on a per line basis. This shows good 
		# results, by now, on text with the same char size in the line 
		# which is quite usual.
		text = ''
		for line in lines:
			width = 0
			count = 0
			left = None
			for c in line:
				if left:
					# If separtion between previous and current char
					# is greater than a third of the average character
					# width we'll add a space.
					if c.box.left() - left > ( width / count ) / 3:
						text += u' '
				text += unicode(c.character)
				left = c.box.right()
				width += c.box.width()
				count += 1
			text += u'\n'
		return text

def initOcrSystem():
	init_gamera()


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
		# Loading
		image = load_image(file)
		self.width = image.data.ncols 
		self.height = image.data.nrows
		info = image_info(file)
		self.xResolution = info.x_resolution
		self.yResolution = info.y_resolution
		
		self.convertToBinary(file, '/tmp/tmp.tif')
		#self.convertIntoValidInput(file, '/tmp/tmp.tif')
		self.file = "/tmp/tmp.tif"

		txt = lower( self.ocr() )
		
		self.boxes = self.parseTesseractOutput(txt)

def initOcrSystem():
	init_gamera()



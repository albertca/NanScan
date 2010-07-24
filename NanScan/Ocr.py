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

import os
# Do not import everything as Template is defined in string too
from string import lower
import codecs
import tempfile
import shutil
import math

from TemporaryFile import *
from Analyzer import *
from Block import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *



## @brief This class allows using an OCR and provides several convenient functions 
# regarding text and image processing such as deskewing or obtaining formated text.
class Ocr(Analyzer):
	file = ""

	## @brief Uses tesseract to recognize text of the current image.
	def tesseract(self, fileName):
		try:
			directory = tempfile.mkdtemp()
			path = os.path.join( directory, 'tesseract' )
			self.spawn( 'tesseract', fileName, path, '-l', 'spa', 'batch.nochop', 'makebox' )
			f=codecs.open(path + '.txt', 'r', 'utf-8')
			try:
				content = f.read()
			finally:
				f.close()
			shutil.rmtree(directory, True)
		except IOError, e:
			print "Input/Output error. Probably data was not a valid image: '%s'" % str(e)
			content = ''
		return content

	## @brief Parses tesseract output creating a list of Character objects.
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

	## @brief Uses cuneiform to recognize text of the current image.
	def cuneiform(self, fileName):
		directory = tempfile.mkdtemp()
		path = os.path.join( directory, 'cuneiform.txt' )
		os.spawnlpe(os.P_WAIT, 'cuneiform', 'cuneiform', '-l', 'spa', '-f', 'hocr', '-o', path, fileName )
		f=codecs.open(path, 'r', 'utf-8', errors='ignore')
		try:
			content = f.read()
		finally:
			f.close()
		shutil.rmtree(directory, True)
		return content

	## @brief Parses tesseract output creating a list of Character objects.
	def parseCuneiformOutput(self, input):
		output = []
		pos = input.find('\n')+1
		input = input[pos:]
		lines = input.partition('<span ')[2].split('bbox')
		lines = lines[1:-1]
		# Output example: <span title="bbox 391 595 400 621">l</span>
		# Coordinates start at top left corner as we need.
		for line in lines:
			textBox = line.strip().split(' ')
			x1 = int(textBox[0])
			y1 = int(textBox[1])
			x2 = int(textBox[2])
			y2 = int(textBox[3].partition('"')[0])

			width = x2 - x1
			height = y2 - y1
			
			# Convert pixel coordinates into millimeters too.
			x1 = float(x1) / self.dotsPerMillimeterX
			width = float(width) / self.dotsPerMillimeterX
			y1 = float(y1) / self.dotsPerMillimeterY
			height = float(height) / self.dotsPerMillimeterY

			c = Character()
			c.character = textBox[3].partition('"')[2][1]
			c.box = QRectF( x1, y1, width, height )
			output.append( c )
		return output

	## @brief Returns the text of a given region of the image. 
	# It's the same as calling formatedText().
	def textInRegion(self, region=None):
		return self.block.formatedText( region )

	## @brief Returns the bounding rectangle of the text returned by textInRegion for
	# the given region.
	def featureRectInRegion(self, region=None):
		lines = self.block.textLinesWithSpaces( region )
		rect = QRectF()
		for line in lines:
			rect = rect.united( line.boundingRect() )
			#for c in line:
				#rect = rect.united( c.box )
		return rect	

	## @brief Uses ImageMagick's 'convert' application to convert the given image 
	# (QImage) into gray scale
	def convertToGrayScale(self, image, output):
		input = TemporaryFile.create( '.tif' ) 
		image.save( input, 'TIFF' )
		os.spawnlp(os.P_WAIT, 'convert', 'convert', '-type', 'grayscale', '-depth', '8', input, output)
		TemporaryFile.remove( input )

	## @brief Uses Gamera OTSU threashold algorithm to convert into binary
	def convertToBinary(self, input, output):
		image = load_image(input)
		# Converting
		img = image.to_greyscale()
		# Thresholding 
		onebit = img.otsu_threshold()
		# Saving for tesseract processing
		onebit.save_tiff(output)
		
	## @brief Scans the given image (QImage) with the OCR.
	def scan(self, image):
		self.image = image
		self.width = self.image.width()
		self.height = self.image.height()
		self.dotsPerMillimeterX = float( self.image.dotsPerMeterX() ) / 1000.0
		self.dotsPerMillimeterY = float( self.image.dotsPerMeterY() ) / 1000.0
		
		# Tesseract Steps
		fileName = TemporaryFile.create('.tif') 
		self.convertToGrayScale(image, fileName)
		txt = lower( self.tesseract(fileName) )
		self.boxes = self.parseTesseractOutput(txt)

		# Cuneiform Steps
		# Use BMP format instead of PNG, for performance reasons. 
		# BMP takes about 0.5 seconds whereas PNG takes 13.
		#fileName = TemporaryFile.create( '.bmp' )
		#image.save( fileName )
		#txt = lower( self.cuneiform(fileName) )
		#self.boxes = self.parseCuneiformOutput(txt)

		TemporaryFile.remove( fileName )

		self.block = Block()
		self.block.setBoxes( self.boxes )



	## @brief Calculates slope of text lines
	# This value is used by deskew() function to rotate image and
	# align text horitzontally. Note that the slope can be calculated
	# by the text of only a region of the image.
	#
	# Algorithm:
	#   1- Calculate textLines()
	#   2- For each line with more than three characters calculate the linear 
	#      regression (pick up slope) given by the x coordinate of the box and 
	#      y as the middle point of the box.
	#   3- Calculate the average of all slopes.
	def slope(self, region=None):
		# TODO: We should probably discard values that highly differ
		# from the average for the final value to be used to rotate.
		lines = self.block.textLines( region )
		slopes = []
		for line in lines:
			if len(line) < 3:
				continue
			x = [b.box.x() for b in line]
			y = [b.box.y()+ (b.box.height()/2) for b in line]
			slope, x, y = linearRegression(x, y)
			slopes.append( slope )
		if len(slopes) == 0:
			return 0

		average = 0
		for x in slopes:
			average += x
		average = average / len(slopes)
		return average

	def deskewOnce(self, region=None):
		slope = self.slope( region )
		transform = QTransform()
		transform.rotateRadians( -math.atan( slope ) )
		self.image = self.image.transformed( transform, Qt.SmoothTransformation )

	def deskew(self, region=None):
		slope = self.slope( region )
		if slope > 0.001:
			self.deskewOnce( self, region )
			slope = self.slope( region )
			if slope > 0.001:
				self.deskewOnce( self, region )

Analyzer.registerAnalyzer( 'text', Ocr )


## @brief This function calculates the linearRegression from a list of points.
# Linear regression of y = ax + b
# Usage
# real, real, real = linearRegression(list, list)
# Returns coefficients to the regression line "y=ax+b" from x[] and y[], and R^2 Value
def linearRegression(X, Y):
	if len(X) != len(Y):
		raise ValueError, 'unequal length'
	N = len(X)
	if N <= 2:
		raise ValueError, 'three or more values needed'
	Sx = Sy = Sxx = Syy = Sxy = 0.0
	for x, y in map(None, X, Y):
		Sx = Sx + x
		Sy = Sy + y
		Sxx = Sxx + x*x
		Syy = Syy + y*y
		Sxy = Sxy + x*y
	det = Sxx * N - Sx * Sx
	a, b = (Sxy * N - Sy * Sx)/det, (Sxx * Sy - Sx * Sxy)/det
	meanerror = residual = 0.0
	for x, y in map(None, X, Y):
		meanerror = meanerror + (y - Sy/N)**2
		residual = residual + (y - a * x - b)**2
	RR = 1 - residual/meanerror
	ss = residual / (N-2)
	Var_a, Var_b = ss * N / det, ss * Sxx / det
	#print "y=ax+b"
	#print "N= %d" % N
	#print "a= %g \pm t_{%d;\alpha/2} %g" % (a, N-2, math.sqrt(Var_a))
	#print "b= %g \pm t_{%d;\alpha/2} %g" % (b, N-2, math.sqrt(Var_b))
	#print "R^2= %g" % RR
	#print "s^2= %g" % ss
	return a, b, RR


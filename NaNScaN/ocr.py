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
import math

from temporaryfile import *

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

## @breif This class allows using an OCR and provides several convenient functions 
# regarding text and image processing such as deskewing or obtaining formated text.
class Ocr:
	file = ""

	## @brief Uses tesseract to recognize text of the current image.
	def ocr(self):
		directory = tempfile.mkdtemp()
		path = os.path.join( directory, 'tesseract' )
		os.spawnlp(os.P_WAIT, 'tesseract', 'tesseract', self.file, path, '-l', 'spa', 'batch.nochop', 'makebox' )
		f=codecs.open(path + '.txt', 'r', 'utf-8')
		content = f.read()
		f.close()
		shutil.rmtree(directory, True)
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

	## @brief Returns the text of a given region of the image. 
	# It's the same as calling formatedText().
	def textInRegion(self, region):
		return self.formatedText( region )

	## @brief Returns the bounding rectangle of the text returned by textInRegion for
	# the given region.
	def featureRectInRegion(self, region):
		lines = self.textLinesWithSpaces( region )
		rect = QRectF()
		for line in lines:
			for c in line:
				rect = rect.united( c.box )
		return rect	

	## @brief Uses ImageMagick's 'convert' application to convert the given image 
	# (QImage) into gray scale
	def convertToGrayScale(self, image, output):
		input = TemporaryFile.create( '.tif' ) 
		image.save( input, 'TIFF' )
		os.spawnlp(os.P_WAIT, 'convert', 'convert', '-type', 'grayscale', '-depth', '8', input, output)

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
		
		self.file = TemporaryFile.create('.tif') 
		self.convertToGrayScale(image, self.file)

		txt = lower( self.ocr() )

		self.boxes = self.parseTesseractOutput(txt)

	## @brief Obtains top most box of the given list
	def topMostBox(self, boxes):
		top = None
		for x in boxes:
			if not top or x.box.y() < top.box.y():
				top = x
		return top

	## @brief Obtain text lines in a list of lines where each line is a list
	# of ordered characters.
	# Note that no spaces are added in this function and each character is a 
	# Character class instance.
	# The algorithm used is pretty simple:
	#   1- Put all boxes in a list ('boxes')
	#   2- Search top most box, remove from pending 'boxes' and add in a new line
	#   3- Search all boxes that vertically intersect with current box, remove from
	#       pending and add in the current line
	#   4- Go to number 2 until all boxes have been processed.
	#   5- Sort the characters of each line by the y coordinate.
	def textLines(self, region=None):
		# If we use 'if region:' instead of comparing with None
		# rects with top (or left) >= bottom (or right), will return 
		# False and thus return _all_ boxes instead of _none_.
		# Indeed, 'if region:' is equivalent to 'if region.isValid():'
		if region != None:
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
			box = self.topMostBox( boxes )
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
		return lines

	## @brief This function is similar to textLines() but adds spaces between words.
	# The result is also a list of lines each line being a list of Character objects.
	def textLinesWithSpaces(self, region=None):

		lines = self.textLines( region )

		# Now we have all lines with their characters in their positions.
		# Here we write and add spaces appropiately. 
		# In order not to be distracted with character widths of letters
		# like 'm' or 'i' (which are very wide and narrow), we average
		# width of the letters on a per line basis. This shows good 
		# results, by now, on text with the same char size in the line,
		# which is quite usual.

		for line in lines:
			width = 0
			count = 0
			left = None
			spacesToAdd = []
			words = []
			for c in line:
				if left:
					# If separtion between previous and current char
					# is greater than a third of the average character
					# width we'll add a space.
					if c.box.left() - left > ( width / count ) / 3:
						if spacesToAdd:
							words.append( line[spacesToAdd[-1]:count] )
						spacesToAdd.append( count )

				# c.character is already a unicode string
				left = c.box.right()
				width += c.box.width()
				count += 1

			# Try to find out if they are fixed sized characters
			# We've got some problems with fixed size fonts. In some cases the 'I' letter will
			# have the width of a pipe but the distance between characters will be fixed. In these
			# cases it's very probable our algorithm will add incorrect spaces before and/or after
			# the 'I' letter. This should be fixed by somehow determining if it's a fixed sized
			# font. The commented code below tries to do just that by calculating distances within
			# the letters of each word. We need to find out if something like this can work and 
			# use it.
			#for x in words:
				#dist = []
				#for c in range( len(x)-1 ):
					#dist.append( x[c+1].box.center().x() - x[c].box.center().x() )
				#print 'Paraula: ', (u''.join( [i.character for i in x] )).encode( 'ascii', 'ignore')
				#print 'Distancies: ', dist
					
				
			# Reverse so indexes are still valid after insertions
			spacesToAdd.reverse()
			previousIdx = None
			for idx in spacesToAdd:
				c = Character()
				c.character = u' '
				c.box = QRectF()
				c.box.setTop( line[idx - 1].box.top() )
				c.box.setBottom( line[idx - 1].box.bottom() )
				c.box.setLeft( line[idx - 1].box.right() )
				c.box.setRight( line[idx].box.left() )
				line.insert( idx, c )
		return lines

		
	## @brief Returns the text in the given region as a string. Spaces included.
	def formatedText(self, region=None):
		lines = self.textLinesWithSpaces( region )
		texts = []
		text = u''
		for line in lines:
			for c in line:
				text += c.character
			texts.append(text)
		return u'\n'.join( texts )

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
		lines = self.textLines( region )
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

## @brief Initializes OCR functions that need to be executed once before the library
# can work. Currently only initiates Gamera which is not being used by now.
def initOcrSystem():
	init_gamera()


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


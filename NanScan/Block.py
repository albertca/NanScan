#   Copyright (C) 2009 by Albert Cervera i Areny
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

def boxComparison(x, y):
	if x.box.x() > y.box.x():
		return 1
	elif x.box.x() < y.box.x():
		return -1
	else:
		return 0

def blockDistanceComparison(x, y):
	if x.distance > y.distance:
		return 1
	elif x.distance < y.distance:
		return -1
	else:
		return 0

def blockSizeComparison(x, y):
	xRect = x.rect()
	yRect = y.rect()
	xt = len( xRect.width() * xRect.height() )
	yt = len( yRect.width() * yRect.height() )
	if xt > yt:
		return 1
	elif xt < yt:
		return -1
	else:
		return 0

class Character:
	def __init__(self):
		self.character = None
		self.box = None

## @brief This class represents a group of characters in a document.
class Block:
	slimCharacters = 'iIl1.,; '

	def __init__(self):
		self.document = None
		self._boxes = []
		self.outerDistance = 2.5
		self._rect = None
		self._outerRect = None
	
	def setBoxes(self, boxes):
		self._boxes = boxes
		self.invalidateCache()

	def boxes(self):
		return self._boxes

	def addBox(self, box):
		self._boxes.append( box )
		self.invalidateCache()

	def removeBox(self, box):
		self._boxes.remove( box )
		self.invalidateCache()

	def count(self):
		return len(self._boxes)

	## @brief Returns a unicode string with the text of the current range
	def text(self):
		return self.formatedText()

	def invalidateCache(self):
		self._rect = None
		self._outerRect = None

	## @brief Returns the bounding rectangle of the text in the range
	def rect(self):
		# If we have the value in the cache use it.
		if self._rect:
			return self._rect
		self._rect = QRectF()
		for c in self._boxes:
			self._rect = self._rect.united( c.box )
		return self._rect

	## @brief Returns a bounding rectangle of the text in the block that is 'outerDistance'
	# larger in all sides.
	def outerRect(self):
		if self._outerRect:
			return self._outerRect
		rect = self.rect()
		rect.translate( - self.outerDistance, - self.outerDistance )
		rect.setWidth( rect.width() + self.outerDistance * 2.0 )
		rect.setHeight( rect.height() + self.outerDistance * 2.0 )
		self._outerRect = rect
		return rect

	## @brief Returns a list with all possible ranges of size length of the 
	# given document
	@staticmethod
	def extractAllBlocksFromDocument(lines, distance=0):
		#blocks = []
		#for line in lines:
			#for char in line:
				#blockFound = False
				#for block in blocks:
					#if block.outerRect().intersects( char.box ):
						#block.addBox( char )
						#blockFound = True
						#break
				#if not blockFound:
					#block = Block()
					#block.addBox( char )
					#block.document = lines
					#blocks.append( block )

		# Find initial blocks.
		blocks = []
		for line in lines:
			block = Block()
			block.document = lines
			blocks.append( block )
			for char in line:
				if char.character != u' ' or block.count() == 0:
					block.addBox( char )
				else:
					avgWidth = block.rect().width() / block.count()
					#print "BLOCK: ", block.text().encode('ascii','ignore')
					#print "BLOCK WIDTH: ", block.rect().width()
					#print "BLOCK COUNT: ", block.count()
					#print "BLOCK AVGWIDTH: ", avgWidth
					#print "CHAR WIDTH: ", char.box.width()
					#print "===="
					if char.box.width() > avgWidth * 1.5:
						block = Block()
						block.document = lines
						blocks.append( block )
					else:
						block.addBox( char )

		# Find out if existing blocks should be merged
		merged = True
		while merged:
			merged = False
			for block1 in blocks:
				for block2 in blocks:
					if block1 == block2:
						continue
					if block1.outerRect().intersects( block2.rect() ):
						block1.merge( block2 )
						blocks.remove( block2 )
						merged = True
						break 
				if merged:
					break
		return blocks

	def merge(self, block):
		for box in block._boxes:
			self._boxes.append( box )

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
			for x in self._boxes:
				if region.intersects(x.box):
					boxes.append(x)
		else:
			# Copy as we'll remove items from the list
			boxes = self._boxes[:]

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

	def meanCharacterWidth(self, line):
		# Calculate mean char width
		width = 0.0
		for c in line:
			if not c.character in Block.slimCharacters:
				width += c.box.width()
		width = width / len(line)
		return width

	def distancesBetweenCharacterCenters(self, line):
		width = self.meanCharacterWidth(line)
		previousCenter = None
		previousRight = None
		distance = 0.0
		distances = []
		for c in line:
			if previousCenter and not ignorePrevious:
				# If separation is bigger than mean char width
				# we can consider "for sure" it's another word.
				if c.box.x() - previousRight < width and ( not c.character in Block.slimCharacters ):
					distances.append( c.box.center().x() - previousCenter )
					distance += distances[-1]
			previousCenter = c.box.center().x()
			previousRight = c.box.right()
			if c.character in Block.slimCharacters:
				ignorePrevious = True
			else:
				ignorePrevious = False

		if not distance:
			return None
		#return distance / len(distances)
		return (distance, distances)


	def meanDistanceBetweenCharacterCenters(self, line):
		d = self.distancesBetweenCharacterCenters(line)
		if not d:
			return None
		return d[0] / len( d[1] )

	def deviationDistanceBetweenCharacterCenters(self, line):
		d = self.distancesBetweenCharacterCenters(line)
		if not d:
			return None
		distances = d[1]
		mean = d[0] / len( distances )
		m = 0.0
		for x in distances:
			m += abs( x - mean )
		m = ( m / len(distances) ) / mean 
		return m

	def isFixedPitchFont(self, line):
		if len(line) == 0:
			return False

		m = self.deviationDistanceBetweenCharacterCenters(line)
		if not m:
			return False
		if m < 0.1:
			return True
		else:
			return False


	## @brief This function adds spaces between words of a single line of boxes.
	def textLineWithSpaces(self, line):
		width = 0
		count = 0
		left = None
		words = []
		blocks = []
		averageWidth = []
		# First let's try to find average char width
		for c in line:
			if left:
				if c.box.left() - left > ( width / count ) * 2:
					blocks.append( count )
					averageWidth.append( width / count )
			left = c.box.right()
			width += c.box.width()
			count += 1
		blocks.append( count )
		averageWidth.append( width / count )

		# TODO: Calculate fixedPitch in a per block basis, just like average char width
		fixedPitch = self.isFixedPitchFont( line )
		meanDistance = self.meanDistanceBetweenCharacterCenters( line )

		width = 0
		count = 0
		left = None
		center = None
		spacesToAdd = []
		words = []
		currentBlock = 0
		for c in line:
			if count > blocks[currentBlock]:
				currentBlock += 1
			if left:
				# We act differently if font is has fixedPitch or not.
				if fixedPitch:
					if c.box.center().x() - center > meanDistance * 1.15:
						if spacesToAdd:
							words.append( line[spacesToAdd[-1]:count] )
						spacesToAdd.append( count )
				else:
					# WITH TESSERACT: 1 * 0.333
					# If separtion between previous and current char
					# is greater than a third of the average character
					# width we'll add a space.
					#
					# WITH CUNEIFORM: 1 * 0.4
					#if c.box.left() - left > ( width / count ) * 0.4:
					if c.box.left() - left > averageWidth[currentBlock] * 0.4:
						if spacesToAdd:
							words.append( line[spacesToAdd[-1]:count] )
						spacesToAdd.append( count )

			left = c.box.right()
			center = c.box.center().x()
			width += c.box.width()
			count += 1

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
			self.textLineWithSpaces( line )
		return lines

		
	## @brief Returns the text in the given region as a string. Spaces included.
	def formatedText(self, region=None):
		lines = self.textLinesWithSpaces( region )
		texts = []
		for line in lines:
			text = u''
			for c in line:
				text += c.character
			texts.append(text)
		return u'\n'.join( texts )

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
	def __init__(self):
		self.document = None
		self._boxes = []
		self.outerDistance = 2.5
	
	def setBoxes(self, boxes):
		self._boxes = boxes

	def boxes(self):
		return self._boxes

	def addBox(self, box):
		self._boxes.append( box )

	def count(self):
		return len(self._boxes)

	## @brief Returns a unicode string with the text of the current range
	def text(self):
		return self.formatedText()

	## @brief Returns the bounding rectangle of the text in the range
	def rect(self):
		rect = QRectF()
		for c in self._boxes:
			rect = rect.united( c.box )
		return rect

	## @brief Returns a bounding rectangle of the text in the block that is 'outerDistance'
	# larger in all sides.
	def outerRect(self):
		rect = self.rect()
		rect.translate( - self.outerDistance, - self.outerDistance )
		rect.setWidth( rect.width() + self.outerDistance * 2.0 )
		rect.setHeight( rect.height() + self.outerDistance * 2.0 )
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
				if char.character != u' ':
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

	## @brief This function adds spaces between words of a single line of boxes.
	def textLineWithSpaces(self, line):
		width = 0
		count = 0
		left = None
		spacesToAdd = []
		words = []
		for c in line:
			if left:
				# WITH TESSERACT: 1 * 0.333
				# If separtion between previous and current char
				# is greater than a third of the average character
				# width we'll add a space.
				#
				# WITH CUNEIFORM: 1 * 0.4
				if c.box.left() - left > ( width / count ) * 0.4:
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

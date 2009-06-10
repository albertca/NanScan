#   Copyright (C) 2009 by Albert Cervera i Areny
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
from AbstractBlock import *
from SimpleBlock import *


## @brief This class represents a group of characters in a document.
class Block(AbstractBlock):
	def __init__(self):
		AbstractBlock.__init__(self)

	## @brief Returns a unicode string with the text of the current range
	def text(self):
		return self.formatedText()

	## @brief Returns a list with all possible ranges of size length of the 
	# given document
	@staticmethod
	def extractAllBlocksFromDocument(lines, distance=0):
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

		blockLines = []
		# Now that we have all boxes in its line. 
		# Create a SimpleBlock per line and sort them.
		for line in lines:
			block = SimpleBlock()
			block.setBoxes( line )
			block.sort()
			blockLines.append( block )

		return blockLines


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
			line.addSpaces()
		return lines

		
	## @brief Returns the text in the given region as a string. Spaces included.
	def formatedText(self, region=None):
		lines = self.textLinesWithSpaces( region )
		texts = []
		for line in lines:
			text = u''
			for c in line.boxes():
				text += c.character
			texts.append(text)
		return u'\n'.join( texts )

	## @brief Returns a copy of the current block, optionally picking only
	# boxes in the given region.
	def copy(self, region=None):
		block = Block()
		block.setBoxes( self.boxesInRegion( region ) )
		return block

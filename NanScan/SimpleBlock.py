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

from AbstractBlock import *

## @brief This class represents a group of characters in a document. All in the same line.
class SimpleBlock(AbstractBlock):
	def __init__(self):
		AbstractBlock.__init__(self)

	## @brief Sorts the list of boxes in a left to right order.
	def sort(self):
		self._boxes.sort( boxComparison )

	## @brief Returns a new block with spaces added in the appropiate places.
	def newWithSpaces(self):
		new = SimpleBlock()
		new.setBoxes( self._boxes )
		new.addSpaces()
		return new

	## @brief Adds spaces in the appropiate places in the current block.
	def addSpaces(self):
		allWidth = 0
		wideWidth = 0
		allCount = 0
		wideCount = 0
		left = None
		blocks = []
		averageWidth = []
		# First let's try to find average char width
		for c in self._boxes:
			if left:
				if wideCount:
					avg = wideWidth / wideCount
				else:
					avg = allWidth / allCount

				if c.box.left() - left > avg * 2:
					blocks.append( allCount )
					averageWidth.append( avg )
					wideWidth = 0
					wideCount = 0
			left = c.box.right()
			allWidth += c.box.width()
			allCount += 1
			if not c.character in AbstractBlock.ThinCharacters:
				wideWidth += c.box.width()
				wideCount += 1
		blocks.append( allCount )
		if wideCount:
			averageWidth.append( wideWidth / wideCount )
		else:
			averageWidth.append( allWidth / allCount )
			

		# TODO: Calculate fixedPitch in a per block basis, just like average char width
		fixedPitch = self.isFixedPitchFont()
		meanDistance = self.meanDistanceBetweenCharacterCenters()

		width = 0
		count = 0
		left = None
		center = None
		spacesToAdd = []
		currentBlock = 0
		for c in self._boxes:
			if count > blocks[currentBlock]:
				currentBlock += 1
			if left:
				# We act differently if font is fixedPitch or not.
				if fixedPitch:
					print "FIXED PITCH"
					if c.box.center().x() - center > meanDistance * 1.3:
						spacesToAdd.append( count )
				else:
					# WITH TESSERACT: 1 * 0.333
					# If separtion between previous and current char
					# is greater than a third of the average character
					# width we'll add a space.
					#
					# WITH CUNEIFORM: 1 * 0.4
					if c.box.left() - left > averageWidth[currentBlock] * 0.4:
						print "WIDTH: %s, DIFF: %s" % (averageWidth[currentBlock], c.box.left() - left)
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
			c.box.setTop( self._boxes[idx - 1].box.top() )
			c.box.setBottom( self._boxes[idx - 1].box.bottom() )
			c.box.setLeft( self._boxes[idx - 1].box.right() )
			c.box.setRight( self._boxes[idx].box.left() )
			self._boxes.insert( idx, c )

	def meanCharacterWidth(self):
		# Calculate mean char width
		width = 0.0
		for c in self._boxes:
			if not c.character in AbstractBlock.ThinCharacters:
				width += c.box.width()
		width = width / len(self._boxes)
		return width

	def distancesBetweenCharacterCenters(self):
		width = self.meanCharacterWidth()
		previousCenter = None
		previousRight = None
		distance = 0.0
		distances = []
		for c in self._boxes:
			if previousCenter and not ignorePrevious:
				# If separation is bigger than mean char width
				# we can consider "for sure" it's another word.
				if c.box.x() - previousRight < width and ( not c.character in AbstractBlock.ThinCharacters ):
					distances.append( c.box.center().x() - previousCenter )
					distance += distances[-1]
			previousCenter = c.box.center().x()
			previousRight = c.box.right()
			if c.character in AbstractBlock.ThinCharacters:
				ignorePrevious = True
			else:
				ignorePrevious = False

		if not distance:
			return None
		return (distance, distances)


	def meanDistanceBetweenCharacterCenters(self):
		d = self.distancesBetweenCharacterCenters()
		if not d:
			return None
		return d[0] / len( d[1] )

	def deviationDistanceBetweenCharacterCenters(self):
		d = self.distancesBetweenCharacterCenters()
		if not d:
			return None
		distances = d[1]
		mean = d[0] / len( distances )
		m = 0.0
		for x in distances:
			m += abs( x - mean )
		m = ( m / len(distances) ) / mean 
		return m

	def isFixedPitchFont(self):
		if len(self._boxes) == 0:
			return False

		m = self.deviationDistanceBetweenCharacterCenters()
		if not m:
			return False
		if m < 0.1:
			return True
		else:
			return False

	def text(self):
		new = self.addSpaces()
		text = u''
		for c in new.boxes():
			text += c.character
		return text

	## @brief Returns a copy of the current block, optionally picking only
	# boxes in the given region.
	def copy(self, region=None):
		block = SimpleBlock()
		block.setBoxes( self.boxesInRegion( region ) )
		return block

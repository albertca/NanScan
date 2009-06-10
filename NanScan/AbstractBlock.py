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

## @brief This class represents a group of characters in a document. All in the same line.
class AbstractBlock:
	ThinCharacters = 'iIl1.,; '

	## @brief Constructs an empty Block.
	def __init__(self):
		self.document = None
		self._boxes = []
		self.outerDistance = 2.5
		self._rect = None
		self._outerRect = None
	
	## @brief Sets the current list of boxes.
	def setBoxes(self, boxes):
		self._boxes = boxes
		self.invalidateCache()

	## @brief Returns the current list of boxes.
	def boxes(self):
		return self._boxes

	## @brief Adds the given box to the list of boxes.
	def addBox(self, box):
		self._boxes.append( box )
		self.invalidateCache()

	## @brief Removes the given box from the list of boxes.
	def removeBox(self, box):
		self._boxes.remove( box )
		self.invalidateCache()

	## @brief Removes all the boxes of the given character.
	def removeCharacter(self, char):
		self._boxes = [x for x in serl._boxes if x.character!=char]
		self.invalidateCache()

	## @brief Removes all boxes of the space character.
	def removeSpaces(self):
		self.removeCharacter( ' ' )

	## @brief Returns the number of boxes in the block.
	def count(self):
		return len(self._boxes)

	## @brief Returns the number of boxes in the block.
	def __len__(self):
		return self.count()

	## @brief Returns the box in position pos
	def __getitem__(self, pos):
		return self._boxes[pos]

	## @brief Adds the boxes in AbstractBlock 'block' into the current block.
	def merge(self, block):
		for box in block._boxes:
			self._boxes.append( box )

	## @brief Invalidates the rect and outerRect caches.
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

	## @brief Returns a unicode string with the text of the current range.
	# The default implementation returns an empty string.
	def text(self):
		return u''

	## @brief Returns the bounding rect of all boxes in the block.
	def boundingRect(self):
		rect = QRectF()
		for c in self._boxes:
			rect = rect.united( c.box )
		return rect

	## @brief Returns a copy of the current block, optionally picking only
	# boxes in the given region.
	# 
	# The default implementation returns an AbstractBlock.
	def copy(self, region=None):
		block = AbstractBlock()
		block.setBoxes( self.boxesInRegion( region ) )
		return block

	## @brief Returns a copy the list of boxes that intersect with the 
	# given region. If region is None, it will return a copy of all boxes.
	def boxesInRegion(self, region):
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
		return boxes

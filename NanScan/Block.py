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

## @brief This class represents a group of characters in a document.
class Block:
	def __init__(self):
		self.document = None
		self.boxes = []
		self.outerDistane = 10

	## @brief Returns a unicode string with the text of the current range
	def text(self):
		line = self.document[self.line]
		chars = line[self.pos:self.pos + self.length]
		return u''.join( [x.character for x in chars] )

	## @brief Returns the bounding rectangle of the text in the range
	def rect(self):
		rect = QRectF()
		for c in self.boxes:
			rect = rect.united( c.box )
		return rect

	## @brief Returns a bounding rectangle of the text in the block that is 'outerDistance'
	# larger in all sides.
	def outerRect(self):
		rect = self.rect()
		rect.translate( - self.outerDistance, - self.outerDistance )
		rect.setWidth( rect.width() + self.outerDistance * 2 )
		rect.setHeight( rect.height() + self.outerDistance * 2 )
		return rect

	## @brief Returns a list with all possible ranges of size length of the 
	# given document
	@staticmethod
	def extractAllBlocksFromDocument(lines, length, distance=0):
		if length <= 0:
			return []
		blocks = []
		for line in xrange(len(lines)):
			for char in xrange(len(line)):
				blockFound = False
				for block in blocks:
					if block.outerRect().intersects( char.box ):
						block.boxes.append( char )
						blockFound = True
						break
				if not blockFound:
					block = Block()
					block.boxes.append( char )
					block.document = lines
					blocks.append( block )
		return blocks


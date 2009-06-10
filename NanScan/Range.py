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

def rangeDistanceComparison(x, y):
	if x.distance > y.distance:
		return 1
	elif x.distance < y.distance:
		return -1
	else:
		return 0

def rangeLengthComparison(x, y):
	xt = len( x.text() )
	yt = len( y.text() )
	if xt > yt:
		return 1
	elif xt < yt:
		return -1
	else:
		return 0

def rangeDistanceLengthRatioComparison(x, y):
	xt = x.text()
	if len( xt ):
		xl = (1.0/len(xt)) + float( x.distance ) / len( xt ) 
	else:
		xl = 999
	yt = y.text()
	if len( y.text() ):
		yl = (1.0/len(yt)) + float( y.distance ) / len( yt )
	else:
		yl = 999
	if xl > yl:
		return 1
	elif xl < yl:
		return -1
	else:
		return 0

## @brief This class represents a group of characters in a document.
class Range:
	def __init__(self):
		self.line = 0
		self.pos = 0
		self.length = 0
		self.document = None

	## @brief Returns a unicode string with the text of the current range
	def text(self):
		line = self.document[self.line]
		chars = line[self.pos:self.pos + self.length]
		return u''.join( [x.character for x in chars] )

	## @brief Returns the bounding rectangle of the text in the range
	def rect(self):
		line = self.document[self.line]
		chars = line[self.pos:self.pos + self.length]
		rect = QRectF()
		for c in chars:
			rect = rect.united( c.box )
		return rect

	## @brief Returns a list with all possible ranges of size length of the 
	# given document
	@staticmethod
	def extractAllRangesFromDocument(lines, length, width=0):
		if length <= 0:
			return []
		ranges = []
		for line in xrange(len(lines)):
			if length >= len(lines[line]):
				ran = Range()
				ran.line = line
				ran.pos = 0
				ran.length = len(lines[line])
				ran.document = lines
				#if width:
				#	while ran.rect().width() > width:
				#		ran.length -= 1
				ranges.append( ran )
				continue
			for pos in xrange(len(lines[line]) - length + 1):
				ran = Range()
				ran.line = line
				ran.pos = pos
				ran.length = length
				ran.document = lines
				#if width:
				#	while ran.rect().width() > width:
				#		ran.length -= 1
				ranges.append( ran )
		return ranges


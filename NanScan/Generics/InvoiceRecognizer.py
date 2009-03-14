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


from NanScan.LevenshteinDistance import *
from NanScan.Range import *
from NanScan.TextPatterns import *

class InvoiceRecognizer:
	Tags = { 
		'number': {
			'tag': [
				u'factura',
				u'numero factura',
				u'factura numero',
				u'num. de factura',
				u'factura num.'
			],
			'type': 'mostly-numeric'
		},
		'date': {
			'tag': [
				u'fecha',
				u'fecha factura',
				u'fecha emision',
				u'data:',
				u'data',
				u'data factura'
			],
			'type': 'date'
			# With dates we need to be able to find a date with
			# the format '1 Sep. 2009'. Also we need to find the
			# date without a tag. Something like:
			#
			# 'fallback': functionName,
			# 
			# might be appropiate for those cases in which the
			# tag can't be found.
		},
		'amount': {
			'tag': [
				u'total',
				u'total factura',
				u'total a pagar (euros)'
			],
			'type': 'numeric'
		}
	}
	def recognize(self, recognizer):
		#text = recognizer.textInRegion('text')
		analyzer = recognizer.analyzers['text']
		self.textLines = analyzer.textLinesWithSpaces()
		result = ''
		for tag in InvoiceRecognizer.Tags:
			result += 'Tag: %s, Value: %s\n' % ( tag, self.findTagValue( tag ) )
		return result

        def formatedLine(self, line):
		text = u''
		for c in line:
			text += c.character
		return text

	def findText(self, textToFind):
		ranges = Range.extractAllRangesFromDocument( self.textLines, len(textToFind) )
		for ran in ranges:
			text = ran.text()
			value = Levenshtein.levenshtein( text, textToFind )
			ran.distance = value
		ranges.sort( rangeDistanceComparison )
		if ranges:
			return ranges[0]
		else:
			return None


	def findTagValue(self, tag):
		ranges = []
		for tagData in InvoiceRecognizer.Tags[tag]['tag']:
			ran = self.findText( tagData )
			if ran:
				ranges.append( ran )
		ranges.sort( rangeDistanceComparison )
		#ran = ranges[0]
		distance = ranges[0].distance
		sameDistance = [x for x in ranges if x.distance == distance]
		sameDistance.sort( rangeLengthComparison )
		#print "SECOND 5: ", [x.text().encode('ascii','ignore') for x in sameDistance[:5]]
		ran = sameDistance[-1]

		print "RANGE FOR TAG %s: %s" % ( tag, ran.text().encode('ascii','ignore') )

		# Extract text on the right
		line = self.formatedLine( self.textLines[ ran.line ] )
		rightValue = line[ran.pos+ran.length+1:].strip().split(' ')[0]
		print "R: ", line[ran.pos+ran.length+1:].strip().encode('ascii','ignore')
		print "rightValue: ", rightValue.encode('ascii','ignore')
		print "SAME LINE: ", line.encode('ascii','ignore')

		# Extract text on the bottom
		if ran.line < len(self.textLines)-1:
			line = self.textLines[ran.line+1]
			print "NEXT LINE: ", self.formatedLine( self.textLines[ran.line+1] ).encode('ascii','ignore')
			boxBottom = ran.rect()
			boxBottom.moveTop( line[0].box.y() )
			bottomValue = u''
			for c in line:
				if c.box.intersects( boxBottom ):
					bottomValue += c.character
		else:
			bottomValue = u''
		
		# Decide which of both values match the given tag type
		type = InvoiceRecognizer.Tags[ tag ][ 'type' ]
		if type == 'numeric':
			if isFloat( rightValue ):
				return textToFloat( rightValue )
			elif isFloat( bottomValue ):
				return textToFloat( bottomValue )
			else:
				return None
		elif type == 'date':
			if isDate( rightValue ):
				return textToDate( rightValue )
			elif isDate( bottomValue ):
				return textToDate( bottomValue )
			else:
				return None
		elif type == 'mostly-numeric':
			if isMostlyNumeric( rightValue ):
				return rightValue
			elif isMostlyNumeric( bottomValue ):
				return bottomValue
			else:
				return rightValue
		else:
			return rightValue


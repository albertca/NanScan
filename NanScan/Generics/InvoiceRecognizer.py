# encoding: iso-8859-1
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
from NanScan.Block import *
from NanScan.TextPatterns import *

def findDate( recognizer ):
	ranges = Range.extractAllRangesFromDocument( recognizer.textLines, 10 )
	for ran in ranges:
		text = ran.text()
		if isDate( ran.text() ):
			return textToDate( text )
	return None

def findVat( recognizer ):
	ranges = Range.extractAllRangesFromDocument( recognizer.textLines, 10 )
	for ran in ranges:
		text = ran.text()
		if isVat( ran.text() ):
			return textToVat( text )
	return None

class InvoiceRecognizer:
	Tags = { 
		'number': {
			'tag': [
				u'numero factura',
				u'factura numero',
				u'num. de factura',
				u'factura num.',
				u'nº factura',
				u'factura núm.',
				u'factura',
				u'número de factura'
			],
			'type': 'mostly-numeric'
		},
		'date': {
			'tag': [
				u'fecha de factura'
				u'fecha factura',
				u'fecha emision',
				u'data factura'
				u'fecha',
				u'data:',
				u'data',
			],
			'type': 'date',
			'fallback': findDate,
		},
		'base': {
			'tag': [
				u'base imponible',
				u'base imposable',
				u'total (base imposable)'
			],
			'type': 'numeric'
		},
		'taxes': {
			'tag': [
				u'IVA',
			],
			'type': 'numeric'
		},
		'total': {
			'tag': [
				u'total',
				u'total factura',
				u'total a pagar (euros)'
			],
			'type': 'numeric'
		},
		'vat': {
			'tag': [
				u'nif',
				u'cif',
				u'nif/cif',
				u'nif:',
				u'cif:',
				u'nif/cif:',
				u'nif :',
				u'cif :',
				u'nif/cif :',
			],
			'type': 'vat',
			'fallback': findVat,
		},
		'pagina': {
			'tag': [
				u'pagina',
				u'página',
				u'pàgina',
				u'pag.',
				u'pàg.',
				u'pág.'
			],
			'type': 'page-number'
		}
	}

	def recognize(self, recognizer):
		analyzer = recognizer.analyzers['text']
		self.textLines = analyzer.block.textLinesWithSpaces()
		result = ''
		for tag in InvoiceRecognizer.Tags:
			result += 'Tag: %s, Value: %s\n' % ( tag, self.findTagValue( tag ) )

#		print "========================================"
#		blocks = Block.extractAllBlocksFromDocument( self.textLines )
#		for block in blocks:
#			print "---"
#			print "BLOCK:", block.text().encode('ascii','ignore')
#			print "---"
#		print "========================================"
#		# Try to find out which of the blocks contains customer information
#
#		# This rect, picks up the first third of an A4 paper size.
#		top = QRectF( 0, 0, 210, 99 )
#		tops = []
#		for block in blocks:
#			if block.rect().intersects( top ):
#				tops.append( block )
#		# Once we have all the blocks of the first third of the paper
#		# try to guess which of them is the good one.
#
#		# Remove those blocks too wide
#		sized = []
#		for block in tops:
#			if block.rect().width() < 120:
#				sized.append( block )

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
		return ranges

	def findTagValue(self, tag):
		ranges = []
		for tagData in InvoiceRecognizer.Tags[tag]['tag']:
			ranges += self.findText( tagData )
			#ran = self.findText( tagData )
			#if ran:
				#ranges.append( ran )
		#ranges.sort( rangeDistanceComparison )
		#distance = ranges[0].distance
		#sameDistance = [x for x in ranges if x.distance == distance]
		#sameDistance.sort( rangeLengthComparison )
		#ran = sameDistance[-1]
		ranges.sort( rangeDistanceLengthRatioComparison )
		print "RANGES FOR TAG: %s\n%s" % ( tag, [ran.text().encode('ascii','replace') for ran in ranges[:20]] )
		for ran in ranges[:5]:
			print "RANGE FOR TAG %s: %s" % ( tag, ran.text().encode('ascii','ignore') )
			value = self.findTagValueFromRange( tag, ran )
			if value:
				return value
		return None

	def findTagValueFromRange(self, tag, ran):

		# Extract text on the right
		line = self.textLines[ ran.line ]
		line = line[ran.pos+ran.length+1:]
		rightValue = Block.extractAllBlocksFromDocument( [ line ] )[0].text()


		#print "R: ", line[ran.pos+ran.length+1:].strip().encode('ascii','ignore')
		print "rightValue: ", rightValue.encode('ascii','replace')
		#print "SAME LINE: ", line.encode('ascii','ignore')

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
		print "bottomValue: ", bottomValue.encode('ascii','replace')
		
		# Decide which of both values match the given tag type
		type = InvoiceRecognizer.Tags[ tag ][ 'type' ]
		value = None
		if type == 'numeric':
			if isFloat( rightValue ):
				value = textToFloat( rightValue )
			elif isFloat( bottomValue ):
				value = textToFloat( bottomValue )
		elif type == 'date':
			if isDate( rightValue ):
				value = textToDate( rightValue )
			elif isDate( bottomValue ):
				value = textToDate( bottomValue )
		elif type == 'mostly-numeric':
			if isMostlyNumeric( rightValue ):
				value = textToMostlyNumeric( rightValue )
			elif isMostlyNumeric( bottomValue ):
				value = textToMostlyNumeric( bottomValue )
		elif type == 'vat':
			if isVat( rightValue ):
				value = textToVat( rightValue )
			elif isVat( bottomValue ):
				value = textToVat( bottomValue )
		elif type == 'page-number':
			if isPageNumber( rightValue ):
				value = textToPageNumber( rightValue )
			elif isPageNumber( bottomValue ):
				value = textToPageNumber( bottomValue )
		else:
			value = rightValue

		if not value and 'fallback' in InvoiceRecognizer.Tags[ tag ]:
			value = InvoiceRecognizer.Tags[ tag ]['fallback']( self )
		return value


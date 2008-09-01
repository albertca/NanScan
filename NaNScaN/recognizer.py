# coding=iso-8859-1
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

from PyQt4.QtCore import *
from barcode import *
from ocr import *

from template import *
from document import *
from trigram import *

import tempfile

class Analyze(QThread):
	def __init__(self, analyzer, image, parent=None):
		QThread.__init__(self, parent)
		self.analyzer = analyzer
		self.image = image

	def run(self):
		self.analyzer.scan( self.image )


class Recognizer(QObject):
	def __init__(self, parent=None):
		QObject.__init__(self, parent)
		self.barcode = Barcode()
		self.ocr = Ocr()

	## @brief Returns the text of a given region of the image. 
	def textInRegion(self, region, type=None):
		if type == 'barcode':
			return self.barcode.textInRegion( region )
		elif type == 'text':
			return self.ocr.textInRegion( region )
		else:
			return None

	## @brief Returns the bounding rectangle of the text returned by textInRegion for
	# the given region.
	def featureRectInRegion(self, region, type=None):
		if type == 'barcode':
			return self.barcode.featureRectInRegion( region )
		elif type == 'text':
			return self.ocr.featureRectInRegion( region )
		else:
			return None

	def boxes(self, type):
		if type == 'barcode':
			return self.barcode.boxes
		elif type == 'text':
			return self.ocr.boxes
		else:
			return None

	def analyzersAvailable(self):
		return ['barcode', 'text']
		
	# Synchronous
	def recognize(self, image):
		self.image = image
		self.barcode.scan( image )
		self.ocr.scan( image )

	## @brief Asynchronous: Starts analyzers in background threads. Emits finished() at the end
	def startRecognition(self, image):
		self.image = image
		self.ocrThread = Analyze( self.ocr, image, self )
		self.barcodeThread = Analyze( self.barcode, image, self )
		self.connect( self.ocrThread, SIGNAL('finished()'), self.recognitionFinished )
		self.connect( self.barcodeThread, SIGNAL('finished()'), self.recognitionFinished )
		self.ocrThread.start()
		self.barcodeThread.start()
		
	def recognitionFinished(self):
		if self.ocrThread.isFinished() and self.barcodeThread.isFinished():
			self.emit( SIGNAL('finished()') )

	def filter(self, value, filterType):
		numeric = '0123456789'
		alphabetic = 'abcçdefghijklmnñopqrstuvwxyz'
		if filterType == 'numeric':
			return u''.join( [x for x in value if x in numeric] )
		elif filterType == 'alphabetic':
			return u''.join( [x for x in value if x in alphabetic] )
		elif filterType == 'alphanumeric':
			return u''.join( [x for x in value if x in numeric+alphabetic] )
		elif filterType == 'none':
			return value
		else:
			print "Filter type '%s' not implemented" % filterType
			return value

	## @brief Extracts the information of the recognized image using the
	# given template. 
	# Optionally an x and y offset can be applied to the template before
	# extracting data.
	# Note that the image must have been scanned (using scan() or startScan()) 
	# before using this function.
	def extractWithTemplate(self, template, xOffset = 0, yOffset = 0): 
		if not template:
			return None
		document = Document()
		for templateBox in template.boxes:
			if not templateBox.text:
				continue

			rect = QRectF( templateBox.rect )
			rect.translate( xOffset, yOffset )

			text = self.textInRegion( rect, templateBox.recognizer )
			text = self.filter( text, templateBox.filter )
			documentBox = DocumentBox()
			documentBox.text = text
			documentBox.templateBox = templateBox
			document.addBox( documentBox )
		return document

	## @brief Tries to find out the best template in 'templates' for the current
	# image.
	# Use the optional parameter 'offset' to specify up to how many millimeters
	# the template should be translated to find the best match. Setting this to
	# 5 (the default) will make the template move 5 millimeter to the right,
	# 5 to the left, 5 to the top and 5 to the bottom. This means 121 positions
	# per template.
	# Note that the image must have been scanned (using scan() or startScan()) 
	# before using this function.
	#
	# TODO: Using offsets to find the best template is easy but highly inefficient.
	#  a smarter solution should be implemented.
	def findMatchingTemplate( self, templates, offset = 5 ):
		max = 0
		best = {
			'template': None,
			'document': Document(),
			'xOffset' : 0,
			'yOffset' : 0
		}
		for template in templates:
			if not template.boxes:
				continue
			# Consider up to 5 millimeter offset
			for xOffset in range(-5,6):
				for yOffset in range(-5,6):
					score = 0
					matcherBoxes = 0
					currentDocument = self.extractWithTemplate( template, xOffset, yOffset )
					for documentBox in currentDocument.boxes:
						templateBox = documentBox.templateBox
						if documentBox.templateBox.type != 'matcher':
							print "Jumping %s due to type %s " % ( templateBox.name, templateBox.type )
							continue
						matcherBoxes += 1
						similarity = Trigram.trigram( documentBox.text, templateBox.text )
						score += similarity
					score = score / matcherBoxes
					if score > max:
						max = score
						best = { 
							'template': template,
							'document': currentDocument,
							'xOffset' : xOffset,
							'yOffset' : yOffset
						}
					print "Template %s has score %s with offset (%s,%s)" % (template.name, score, xOffset, yOffset)
		return best

	## @brief Returns a QPoint with the offset that needs to be applied to the given
	# template to best fit the current image.
	def findTemplateOffset( self, template ):
		if not template.boxes:
			return QPoint( 0, 0 )

		lines = self.ocr.textLinesWithSpaces()

		for templateBox in template.boxes:
			if templateBox.type != 'matcher':
				continue

			for line in lines:
				templateBox.text

				


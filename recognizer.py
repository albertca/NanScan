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

import tempfile

# Smarter processing models and functions
def translate(text):
	txt = text
	f=codecs.open('addons/smart_attach/translations.txt', 'r', 'utf-8')
	if not f:
		print "File not found"
		return txt
	translations = f.readlines()
	f.close()
	for x in translations:
		for y in x[1:]:
			txt = txt.replace( y, x[0] )
	return txt

class Analyze(QThread):
	def __init__(self, analyzer, file, parent=None):
		QThread.__init__(self, parent)
		self.analyzer = analyzer
		self.file = file

	def run(self):
		self.analyzer.scan( self.file )


class Recognizer(QObject):
	def __init__(self, parent=None):
		QObject.__init__(self, parent)
		self.barcode = Barcode()
		self.ocr = Ocr()

	def textInRegion(self, region, type=None):
		if type == 'barcode':
			return self.barcode.textInRegion( region )
		elif type == 'text':
			return self.ocr.textInRegion( region )
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
		
	# Synchronous: Returns the types of analyzers available
	def scan(self, file):
		self.fileName = file
		self.barcode.scan( file )
		self.ocr.scan( file )

	# Asynchronous: Starts analyzers in background threads. Emits finished() at the end
	def startScan(self, file):
		self.fileName = file
		self.ocrThread = Analyze( self.ocr, file, self )
		self.barcodeThread = Analyze( self.barcode, file, self )
		self.connect( self.ocrThread, SIGNAL('finished()'), self.scanFinished )
		self.connect( self.barcodeThread, SIGNAL('finished()'), self.scanFinished )
		self.ocrThread.start()
		self.barcodeThread.start()
		
	def scanFinished(self):
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

	def scanWithTemplate(self, file, template):
		if not template:
			return None

		self.scan( file )
		document = Document()
		for templateBox in template.boxes:
			if not templateBox.text:
				continue

			text = self.textInRegion( templateBox.rect, templateBox.recognizer )
			text = self.filter( text, templateBox.filter )
			documentBox = DocumentBox()
			documentBox.text = text
			documentBox.templateBox = templateBox
			document.addBox( documentBox )
		return document

	# Tries to find out the best template in 'templates' for the image file given by 'image'
	# TODO: Should be reestructured to use function scanWithTemplate()
	def findBestTemplate( self, cr, file, templates ):
		self.scan( file ) 
		max = 0
		bestDocument = Document()
		bestTemplate = None
		for template in templates:
			currentDocument = Document()

			if not template.boxes:
				continue
			score = 0
			matcherBoxes = 0
			for templateBox in template.boxes:
				if not templateBox.text:
					continue
				text = self.textInRegion( templateBox.rect, templateBox.recognizer )
				text = self.filter( text, templateBox.filter )

				documentBox = DocumentBox()
				documentBox.text = text
				documentBox.templateBox = templateBox
				currentDocument.addBox( documentBox )

				if templateBox.type != 'matcher':
					print "Jumping %s due to type %s " % ( templateBox.name, templateBox.type )
					continue
				matcherBoxes += 1
				#cr.execute( 'SELECT similarity(%s,%s)', (translate(text), translate(templateBox.text)) )
				cr.execute( 'SELECT similarity(%s,%s)', (text, templateBox.text) )
				similarity = cr.fetchone()[0]
				score += similarity
			score = score / matcherBoxes
			if score > max:
				max = score
				bestTemplate = template
				bestDocument = currentDocument
			print "Template %s has score %s" % (template.name, score)
		return { 'template': bestTemplate, 'document': bestDocument }


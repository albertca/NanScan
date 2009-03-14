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
from Barcode import *
from Ocr import *
from DataMatrix import *

from Analyzer import *
from Template import *
from Document import *
from Trigram import *
from Hamming import *
from LevenshteinDistance import *
from Translator import *
from Range import *

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
		self.analyzers = {}
		for x in Analyzer.analyzers:
			self.analyzers[x] = Analyzer.create(x)
		self.ocr = self.analyzers['text']
		self.image = None
		self.threads = []

	## @brief Returns the text of a given region of the image. 
	def textInRegion(self, region, type=None):
		if type in self.analyzers.keys():
			return self.analyzers[type].textInRegion( region )
		else:
			return None

	## @brief Returns the bounding rectangle of the text returned by textInRegion for
	# the given region.
	def featureRectInRegion(self, region, type=None):
		if type in self.analyzers:
			return self.analyzers[type].featureRectInRegion( region )
		else:
			return None

	def boxes(self, type):
		if type in self.analyzers:
			return self.analyzers[type].boxes
		else:
			return []

	def analyzersAvailable(self):
		return self.analyzers.keys()
		
	# Synchronous
	def recognize(self, image):
		self.image = image
		for analyzer in self.analyzers.values():
			analyzer.scan( image )
		#self.barcode.scan( image )
		#self.ocr.scan( image )

	## @brief Asynchronous: Starts analyzers in background threads. Emits finished() at the end
	def startRecognition(self, image):
		self.image = image
		self.threads = []
		for analyzer in self.analyzers.values():
			thread = Analyze( analyzer, image, self )
			self.connect( thread, SIGNAL('finished()'), self.recognitionFinished )
			self.threads.append( thread )
			thread.start()
		
	def recognitionFinished(self):
		print "THREAD FINISHED"
		for thread in self.threads:
			if thread.isRunning():
				return
		self.emit( SIGNAL('finished()') )
		self.threads = []

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
	#
	# Note that the image must have been scanned (using scan() or startScan()) 
	# before using this function.
	def findMatchingTemplateByOffset( self, templates, offset = 5 ):
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
							print "Jumping %s due to type %s" % ( templateBox.name, templateBox.type )
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


	## @brief Tries to find out the best template in 'templates' for the current
	# image.
	# This algorithm starts by looking for template boxes of type 'matching' in the
	# text and then looks if the relative positions of the new document and template
	# boxes are similar. This is intended to be faster than exhaustive algorithm used
	# in findMatchingTemplateByOffset().
	#
	# Note that the image must have been scanned (using scan() or startScan()) 
	# before using this function.
	def findMatchingTemplateByText( self, templates ):
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
			# Find out template's offset
			offset = self.findTemplateOffset( template )
			if not offset:
				continue

			score = 0
			matcherBoxes = 0
			# Apply template with offset found
			currentDocument = self.extractWithTemplate( template, offset.x(), offset.y() )
			for documentBox in currentDocument.boxes:
				if documentBox.templateBox.type != 'matcher':
					continue
				templateBox = documentBox.templateBox
				matcherBoxes += 1
				similarity = Trigram.trigram( documentBox.text, templateBox.text )
				score += similarity
			score = score / matcherBoxes
			print "Score: ", score
			if score > max:
				max = score
				best = { 
					'template': template,
					'document': currentDocument,
					'xOffset' : offset.x(),
					'yOffset' : offset.y()
				}
		return best

	## @brief Returns a QPoint with the offset that needs to be applied to the given
	# template to best fit the current image.
	def findTemplateOffset( self, template ):
		if not template.boxes:
			return QPoint( 0, 0 )

		lines = self.ocr.textLinesWithSpaces()
		print "FORMATED: ", self.ocr.formatedText().encode( 'ascii', 'replace' )

		# Create a default translator only once
		translator = Translator()

		# This list will keep a pointer to each template box of type 'matcher'
		matchers = []
		for templateBox in template.boxes:
			if templateBox.type != 'matcher':
				continue

			templateBoxText = templateBox.text.strip()
			templateBox.ranges = Range.extractAllRangesFromDocument( lines, len(templateBoxText), templateBox.featureRect.width() + 2 )
			for ran in templateBox.ranges:
				text = ran.text()
				#value = Hamming.hamming( text, templateBoxText, translator )
				#value = 1.0 - Trigram.trigram( text, templateBoxText )
				value = Levenshtein.levenshtein( text, templateBoxText )
				ran.distance = value
				#print "Comparison: '%s', '%s', '%f'" % (text.encode('ascii','ignore'), templateBoxText, value)

			#five = u'|'.join( [ x.text().encode('ascii','ignore') for x in templateBox.ranges[0:200] ])
			#print 'First five ranges: ', five

			templateBox.ranges.sort( rangeDistanceComparison )

			for x in templateBox.ranges[0:20]:
				print "Comparison: '%s', '%s', '%f'" % (x.text().encode('ascii','replace'), templateBoxText, x.distance)
				
			#five = u'|'.join( [ x.text().encode('ascii','ignore') for x in templateBox.ranges[0:10] ])
			#print 'First five ranges: ', five

			if templateBox.ranges:
				bestRange = templateBox.ranges[0]
				print "The best match for template box '%s' is '%s' with distance %d" % (templateBoxText, bestRange.text().encode('ascii','replace'), bestRange.distance )
			matchers.append( templateBox )

		# Once we have all ranges sorted for each template box we search which
		# range combination matches the template.
		iterator = TemplateBoxRangeIterator( matchers )
		i = 0
		for ranges in iterator:
			documentBoxCenter = ranges[0].rect().center()
			templateBoxCenter = matchers[0].featureRect.center()
			diff = documentBoxCenter - templateBoxCenter 
			#print "Difference: ", diff
			#print "Document: ", documentBoxCenter
			#print "Template: ", templateBoxCenter
			found = True
			for pos in range(1,len(ranges)):
				documentBoxCenter = ranges[pos].rect().center()
				templateBoxCenter = matchers[pos].featureRect.center()
				d = documentBoxCenter - templateBoxCenter
				# If difference of relative positions of boxes between 
				# template and document are bigger than 5mm we discard 
				# the ranges
				#print "Difference in loop: ", d
				#print "Document: %s, %s" % ( documentBoxCenter, ranges[pos].rect() )
				#print "Template: ", templateBoxCenter
				#print "Comparison: %s  --- %s" % (abs(d.x()) + 5.0, abs(diff.x() ) )
				if abs(d.x() - diff.x()) > 5:
					found = False
					break
				if abs(d.y() - diff.y()) > 5:
					found = False
					break
			if found:
				break
			i += 1
			if i > 1000:
				break
		if found:
			return diff
		else:
			return None


class TemplateBoxRangeIterator:
	def __init__(self, boxes):
		self.boxes = boxes
		self.pos = [0] * len(self.boxes)
		self.loopPos = [0] * len(self.boxes)
		self.added = None

	def __iter__(self):
		return self

	def next(self):
		result = []	
		for x in range(len(self.boxes)):
			result.append( self.boxes[x].ranges[ self.loopPos[x] ] )

		#print '----'
		#print (u', '.join( [x.text() for x in result] )).encode('ascii', 'replace')
		#print self.pos
		#print self.loopPos
		if self.loopPos == self.pos:
			# Search next value to add
			value = float('infinity')
			pos = 0
			for x in range(len(self.pos)):
				if self.pos[x] >= len(self.boxes[x].ranges) - 1:
					continue
				if self.boxes[x].ranges[ self.pos[x] + 1 ].distance < value:
					value = self.boxes[x].ranges[ self.pos[x] + 1 ].distance
					self.added = x
			# If value is Infinity it means that we reached the end
			# of all possible iterations
			if value == float('infinity'):
				raise StopIteration

			self.pos[self.added] += 1
			self.loopPos = [0] * len(self.boxes)
			self.loopPos[self.added] = self.pos[self.added]
		else:
			for x in range(len(self.loopPos)):
				if x == self.added:
					continue		
				if self.loopPos[x] < self.pos[x]:
					self.loopPos[x] += 1
					break
		return result


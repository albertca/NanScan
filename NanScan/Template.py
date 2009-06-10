#   Copyright (C) 2008-2009 by Albert Cervera i Areny
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

from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

class Template(QObject):
	def __init__(self, name):
		QObject.__init__(self)
		self.id = 0
		self.name = name
		self.boxes = []

	def addBox(self, box):
		self.boxes.append( box )
		self.emit(SIGNAL('boxAdded(PyQt_PyObject)'), box)
	
	def removeBox(self, box):
		self.boxes.remove( box )
		self.emit(SIGNAL('boxRemoved(PyQt_PyObject)'), box)

class TemplateBox:
	recognizers = ['text', 'barcode', 'dataMatrix']
	types = ['matcher','input']
	filters = ['none','numeric','alphabetic','alphanumeric']

	def __init__(self):
		self.rect = QRectF()
		# Holds the rect where the actual text/barcode/whatever
		# is found in the template
		self.featureRect = QRectF()
		self.recognizer = 'text'
		self.type = 'matcher'
		self.filter = 'none'
		self.name = ''
		self.text = '' 
	
	def setType(self, value):
		if value not in TemplateBox.types:
			raise "Type '%s' not valid" % value 
		self._type = value
	def getType(self):
		return self._type
	type=property(getType,setType)

	def setFilter(self, value):
		if value not in TemplateBox.filters:
			raise "Filter '%s' not valid" % value
		self._filter = value
	def getFilter(self):
		return self._filter
	filter=property(getFilter,setFilter)

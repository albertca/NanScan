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

import subprocess
import tempfile
import codecs
import os

class Analyzer:
	analyzers = {}

	def __init__(self):
		self.boxes = []

	@staticmethod
	def registerAnalyzer(name, analyzer):
		Analyzer.analyzers[name] = analyzer

	@staticmethod
	def unregisterAnalyzer(name):
		del Analyzer.analyzers[name]

	@staticmethod
	def create(name):
		return Analyzer.analyzers[name]()

	def scan(self, image):
		pass

	def textInRegion(self, region=None):
		pass

	def featureRectInRegion(self, region=None):
		pass

	# Spawn process and return STDOUT
	def spawn(self, command, *args):
		command = [ command ] + list( args )
		process = subprocess.Popen( command , stdout=subprocess.PIPE )
		content = process.communicate()[0]
		return content

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
import os
import tempfile

class Box:
	def __init__(self):
		self.text = None
		self.type = None
		self.position = None

class Barcode:
	def __init__(self):
		self.boxes = []

	# Spawn process and return STDOUT
	def spawn(self, command, *args):
		(fd,filename) = tempfile.mkstemp()
		previousFd = os.dup(1)
		os.dup2(fd, 1)
		p = os.spawnlp(os.P_WAIT, command, command, *args)
		os.dup2(previousFd, 1)
		os.close(fd)
		os.close(previousFd)
		f = open( filename )
		content = f.read()
		f.close()
		os.unlink( filename )
		return content

	def parseBardecodeOutput(self, content):
		# Sample output "818043376500 [type: ean13 at: (1798,936)]"
		for line in content.splitlines():
			pieces = line.split( ' ' )
			box = Box()
			box.text = pieces[0]
			box.type = pieces[2]
			pos = pieces[4].strip( '()]' ).split(',')
			box.position = QPointF( float(pos[0]), float(pos[1]))
			self.boxes.append( box )

	def printBoxes(self):
		for x in self.boxes:
			print "Text: %s, Type: %s, Position: %f, %f" % (x.text, x.type, x.position.x(), x.position.y())
		
	def textInRegion(self, region):
		for x in self.boxes:
			if region.contains(x.position):
				return unicode(x.text)
		# We always return unicode strings
		return u''

	def scan(self, file):
		# Clean boxes so scan() can be called more than once
		self.boxes = []
		command = '/home/albert/d/git/exact-image-0.5.0/objdir/frontends/bardecode'
		content = self.spawn( command, file )
		self.parseBardecodeOutput( content )
		self.printBoxes()


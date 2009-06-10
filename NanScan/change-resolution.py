#!/usr/bin/python
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


from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys

if len(sys.argv) != 3:
	print "change-resolution.py resolution image"
	print
	print "Sets the resolution of the given image to the given value"
	print "Example: ./change-resolution.py 300 image.png"
	print 
	print "This utility has been created because images obtained with"
	print "scanimage and scanadf sane utilities don't set resolution"
	print "correctly."
	sys.exit()

# Convert resolution to dots per meter
resolution = float(sys.argv[1]) * 1000 / 25.4
file = sys.argv[2]

image = QImage( file )
image.setDotsPerMeterX( resolution )
image.setDotsPerMeterY( resolution )
image.save( file )

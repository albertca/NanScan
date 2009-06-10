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

import ocr
import sys
import codecs
from PyQt4.QtGui import *

ocr.initOcrSystem()

c = ocr.Ocr()
image = QImage()
if not image.load( sys.argv[-1] ):
	print 'Error loading image'
	os.exit(1)

c.scan( image )
print c.formatedText().encode('ascii','ignore')
f=codecs.open( '/tmp/output.txt', 'w', 'utf-8' )
f.write( c.formatedText() )
f.close()
print c.slope()
c.deskewOnce()
c.image.save( '/tmp/rotated.png', 'PNG' )
#print "Image stored in /tmp/rotated.png"


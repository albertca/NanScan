#!/usr/bin/python

##############################################################################
#
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import os
import sys
import glob
import base64
from Koo import Rpc

if len(sys.argv) != 3:
	print 'loader.py database directory'
	sys.exit(1)

Rpc.session.login( 'http://admin:admin@127.0.0.1:8069', sys.argv[1] )

files = glob.glob(sys.argv[2] + "/*.png")
print "F: ", files
for x in files:
	print "Loading file: ", x 
	fields = {}
	fields['name'] = os.path.split(x)[1]
	fields['datas'] = base64.encodestring(open(x, 'rb').read())
	Rpc.session.execute('/object', 'execute', 'nan.document', 'create', fields )


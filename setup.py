#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup for Koo (taken from OpenERP GTK client)
#   taken from straw http://www.nongnu.org/straw/index.html
#   taken from gnomolicious http://www.nongnu.org/gnomolicious/
#   adapted by Nicolas Évrard <nicoe@altern.org>

import imp
import sys
import os
import glob

from stat import ST_MODE

from distutils.file_util import copy_file
from distutils.sysconfig import get_python_lib
from distutils.core import setup

try:
	import py2exe

	# Override the function in py2exe to determine if a dll should be included
        dllList = ('mfc90.dll','msvcp90.dll','qtnetwork.pyd','qtxmlpatterns4.dll','qtsvg4.dll')
	origIsSystemDLL = py2exe.build_exe.isSystemDLL
	def isSystemDLL(pathname):
		if os.path.basename(pathname).lower() in dllList:
			return 0
		return origIsSystemDLL(pathname)
	py2exe.build_exe.isSystemDLL = isSystemDLL
	using_py2exe = True
except:
	using_py2exe = False
	pass

opj = os.path.join

name = 'NanScan'

from NanScan import Version
version = Version.Version

# get python short version
py_short_version = '%s.%s' % sys.version_info[:2]

required_modules = [
	('PyQt4.QtCore', 'Qt4 Core python bindings'),
	('PyQt4.QtGui', 'Qt4 Gui python bindings'),
	('PyQt4.uic', 'Qt4 uic python bindings'),
]

def check_modules():
	ok = True
	for modname, desc in required_modules:
		try:
			exec('import %s' % modname)
		except ImportError:
			ok = False
			print 'Error: python module %s (%s) is required' % (modname, desc)

	if not ok:
		sys.exit(1)


long_desc = '''\
=====================================
Koo Client and Development Platform
=====================================

Koo is a Qt/KDE based client for Open ERP, a complete ERP and CRM. Koo 
aims for great flexibility allowing easy creation of plugins and views, high
integration with KDE4 under Unix, Windows and Mac, as well as providing
a development platform for new applications using the Open ERP server.

A set of server side modules is also provided among the Koo distribution
which provide better attachments handling and full text search capabilities.
'''

classifiers = """\
Development Status :: 5 - Production/Stable
License :: OSI Approved :: GNU General Public License (GPL)
Programming Language :: Python
Topic :: Desktop Environment :: K Desktop Environment (KDE)
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: MacOS
Topic :: Office/Business
"""

                                                      
if len(sys.argv) < 2:
	print "Syntax: setup.py command [options]"
	sys.exit(2)

command = sys.argv[1]

check_modules()

# create startup script
if os.name != 'nt':
	start_script = "cd %s/Planta\nexec %s ./planta.py $@\n" % ( 
		get_python_lib(), sys.executable
	)
	# write script
	f = open('planta', 'w')
	f.write(start_script)
	f.close()
	
	script_files = ['planta']
else:
	script_files = []

packages = [
	'NanScan', 
	'NanScan.Generics', 
	'NanScan.Backends', 
	'Planta',
] 

setup (
	name             = name,
	version          = version,
	description      = "NanScan",
	long_description = long_desc,
	url              = 'http://www.NaN-tic.com',
	author           = 'NaN',
	author_email     = 'info@NaN-tic.com',
	classifiers      = filter(None, classifiers.splitlines()),
	license          = 'GPL',
        data_files       = [
                (opj('lib','site-packages','NanScan','Backends'),[opj('NanScan','Backends','twain.pyd')]),
                (opj('lib','site-packages','NanScan'),[opj('NanScan','ScanDialog.ui')]),
                (opj('lib','site-packages','NanScan'),[opj('NanScan','common.rcc')]),
        ],
	scripts          = script_files,
	windows          = [{
                                'script': opj('Planta','planta.py'),
                            }],
	packages         = packages ,
	package_dir      = {'NanScan': 'NanScan'},
	provides         = [ 'NanScan' ],
	options          = { 
		'py2exe': {
			'includes': ['sip', 'PyQt4.QtNetwork', 'PyQt4.QtWebKit'] + packages 
		}
	}
)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

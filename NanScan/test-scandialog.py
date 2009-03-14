from PyQt4.QtGui import *
from ScanDialog import *
import sys
import os

app = QApplication( sys.argv )

dialog = ScanDialog()

if os.name == 'nt':
	FileSaveThreaded.directory = 'c:\\images'
else:
	FileSaveThreaded.directory = '/tmp/scan'

dialog.exec_()

app.exec_()


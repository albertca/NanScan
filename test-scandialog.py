from PyQt4.QtGui import *
from scandialog import *
import sys

app = QApplication( sys.argv )

dialog = ScanDialog()
FileSaveThreaded.directory = 'c:\\images'
dialog.exec_()

app.exec_()


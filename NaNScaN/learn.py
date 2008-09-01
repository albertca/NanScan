from gamera.core import *
from gamera.knn import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from temporaryfile import *

def initOcrSystem():
	init_gamera()

class GameraLearn:
	def scan(self, image):
		print "Saving image..."
		output = TemporaryFile.create( '.tif' ) 
		image.save( output, 'TIFF' )

		print "Loading image with gamera..."
		img = load_image( output )
		print "Converting to greyscale..."
		img = img.to_greyscale()
		print "Thresholding..."
		onebit = img.otsu_threshold()
		
		# Get connected components from the image
		print "Getting connected components"
		ccs = onebit.cc_analysis()
		# Classify
		#classifier = knn.kNNInteractive()
		#classifier.from_xml_filename('training.xml')
		#classifier.classify_list_automatic( css )

		print "Initiating classifier"
		classifier = kNNNonInteractive( ccs )

		import ocr
		o = ocr.Ocr()
		print "Scanning with tesseract"
		o.scan( image )
		print "Teaching gamera"
		for c in ccs:
			print "Glyph: ", c
			text = o.textInRegion( c )
			classifier.classify_glyph_manual( c, text )


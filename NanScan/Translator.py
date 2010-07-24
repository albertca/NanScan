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

import codecs
import os

## @brief This class provides a simple way of converting similar characters
# to the same one.
#
# This can proof useful to overcome OCR errors and is used in Hamming class,
# for example. Default translation file provides families of characters. For
# example 's', 'S', '$' are in the same one because the OCR may sometimes
# recognize an 'S' as '$'. 'l', 'i' and '|' are in another family.
#
# The text 'eli a sa|de$' will be converted to 'ell a saldes'. The translator
# replaces any element of a family by the first character of the family it is in.
class Translator:
	def __init__(self):
		self.translations = None

	## @brief Sets the translation list.
	# 
	# The list should follow the following structure: [ 'sS$', 'li|', ... ]
	def setTranslations(self, translations):
		self.translations = translations

	## @brief Loads the translation list from the given file.
	#
	# Each character family must be in a different line. See the default
	# translations.txt file if you need an example.
	def load(self, fileName):
		f=codecs.open(fileName, 'r', 'utf-8')
		if not f:
			print "File not found"
			return txt
		try:
			self.translations = f.readlines()
		finally:
			f.close()

	## @brief Returns the given text replacing each character with the first 
	# character of its family or itself if it's not in any character family.
	def translated(self, text):
		if self.translations == None:
			self.load( os.path.join( os.path.abspath(os.path.dirname(__file__)), 'translations.txt' ) )

		result = text
		for x in self.translations:
			for y in x[1:]:
				result = result.replace( y, x[0] )
		return result


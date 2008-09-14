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

from translator import *

## @brief This class calculates the Hamming distance between two strings.
#
# When two given characters differ completely they add 2 to the final distance
# between the strings. Two 'similar' characters (defined by the given translator
# or the default translator if none specified) will add 1 and 0 for two 
# identical characters.
#
# This distinction of 'similar' and 'different' characters can be useful to 
# 'correct' OCR defects.
class Hamming:

	## @brief Calculates Hamming distance between two strings. Optionally a 
	# translator can be provieded. A default translator will be used if none
	# specified.
	@staticmethod
	def hamming( text1, text2, translator = None ):
		if not translator:
			translator = Translator()

		transText1 = translator.translated( text1 )
		transText2 = translator.translated( text2 )

		value = 0
		size = min(len(text1), len(text2))
		for i in range(size):
			if text1[i] == text2[i]:
				continue
			if transText1[i] == transText2[i]:
				value += 1
				continue
			value += 2
		# Note that we need to multiply by 2 because 'errors' weight 2
		# and 'semi-errors' weight 1
		value += abs( len(text1) - len(text2) ) * 2
		return value

if __name__ == '__main__':
	print Hamming.hamming( 'si', '$l' )
	print Hamming.hamming( 'abc', 'abc' )
	print Hamming.hamming( 'abcabc', 'abc' )
	print Hamming.hamming( 'abcdef', 'abc' )
	print Hamming.hamming( 'abcdef', 'bcd' )
	print Hamming.hamming( 'bcdef', 'abc' )
	for x in range(10000):
		Hamming.hamming( 'text de la plantilla', 'text llarg que pot ser del document que tractem actualment' )


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

class Hamming:

	@staticmethod
	def simplify( text ):
		return text

	@staticmethod
	def hamming( text1, text2 ):
		value = 0
		size = min(len(text1), len(text2))
		for i in range(size):
			if text1[i] == text2[i]:
				continue
			if Hamming.simplify( text1[i] ) == Hamming.simplify( text2[i] ):
				value += 1
				continue
			value += 2
		value += abs( len(text1) - len(text2) )
		return value

if __name__ == '__main__':
	print Hamming.hamming( 'abc', 'abc' )
	print Hamming.hamming( 'abcabc', 'abc' )
	print Hamming.hamming( 'abcdef', 'abc' )
	print Hamming.hamming( 'abcdef', 'bcd' )
	print Hamming.hamming( 'bcdef', 'abc' )
	for x in range(10000):
		Hamming.hamming( 'text de la plantilla', 'text llarg que pot ser del document que tractem actualment' )

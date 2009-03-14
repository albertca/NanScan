#   Copyright (C) 2009 by Albert Cervera i Areny
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

from PyQt4.QtCore import *

def textToFloat( value ):
	if ',' in value and '.' in value:
		commaIndex = value.rfind(',')
		periodIndex = value.rfind('.')
		if commaIndex > periodIndex:
			newValue = value.replace( '.', '' ).replace( ',', '.' )
		else:
			newValue = value.replace( ',', '' )
	elif ',' in value:
		newValue = value.replace( ',', '.' )
	else:
		newValue = value
	return float( newValue )

def isFloat( value ):
	try:
		textToFloat( value )
		return True
	except:
		return False

def isDate( value ):
	date = textToDate( value )
	return date.isValid()

def textToDate( value ):
	patterns = ['dd/MM/yyyy', 'dd-MM-yyyy', 'dd-MM-yy', 'dd MMM. yy', 'dd MMMM yyyy', 'dd.mm.yyyy']
	for pattern in patterns:
		date = QDate.fromString( value.replace(' ',''), pattern )
		if date.isValid():
			return date
	return QDate()

def isMostlyNumeric( text ):
	numbers = 0
	for x in text:
		if x in '0123456789':
			numbers += 1
	if numbers > len(text) / 2:
		return True
	else:
		return False


# encoding: iso-8859-1
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
import re

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
	# Remove spaces
	newValue = newValue.replace( ' ', '' )
	# Remove possible coin symbol in the end
	if not newValue[-1] in '0123456789':
		newValue = newValue[:-1]
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
	value = value.replace(' ','')
	# Replace '.' with '/' as QDate.fromString() doesn't like patterns
	# with dots in it. At the same time do the same with dashes. It's
	# faster to replace than to try to convert to QDate.
	value = value.replace('.','/')
	value = value.replace('-','/')
	value = textMonthToNumber( value )
	# Replace texts for cases such as '25 de juny de 2009'
	value = re.sub( r'[a-z]', '', value )
	value = re.sub( r'[A-Z]', '', value )
	patterns = [ 'dd/MM/yyyy', 'dd/MM/yy', 'd/MM/yyyy', 'd/MM/yy' ]
	for pattern in patterns:
		date = QDate.fromString( value, pattern )
		if date.isValid():
			# If only two digits where used to specify year 
			# it probably meant 200x or 20xx not 190x or 19xx 
			# (which is what QDate interprets).
			if date.year() < 1930 and not 'yyyy' in pattern:
				date = date.addYears( 100 )
			return date
	return QDate()

def textMonthToNumber( value ):
	months = [ 
		('gen', '01'), ('gener', '01'), ('enero', '01'), ('january', '01'), 
		('feb', '02'), ('febrer', '02'), ('febrero', '02'), ('february', '02'),
		('mar', '03'), ('marc', '03'), ('marzo', '03'), ('march', '03'),
		('abr', '04'), ('apr', '04'), ('abril', '04'), ('april', '04'),
		('mai', '05'), ('may', '05'), ('maig', '05'), ('mayo', '05'), 
		('jun', '06'), ('jul', '07'), ('juny', '06'), ('junio', '06'), ('june', '06'),
		('ago', '08'), ('agost', '09'), ('agosto', '08'), ('august', '08'), 
		('set', '09'), ('sep', '09'), ('setembre', '09'), ('september', '09'),
		('oct', '10'), ('octubre', '10'), ('october', '10'), 
		('nov', '11'), ('novembre', '11'), ('noviembre', '11'),
		('des', '12'), ('dec', '12'), ('desembre', '12'), ('diciembre', '12'), ('december', '12')
	]
	# reverse sort so longer names are replaced first
	months.sort( key=lambda a: a[0], reverse=True )
	v = value
	for x in months:
		# Try to replace twice. Sometimes instead of 'dec' we see 'dec.'
		v = v.replace( u'%s.' % x[0], u'/%s/' % x[1] )
		v = v.replace( x[0], u'/%s/' % x[1] )
	return v

def isMostlyNumeric( text ):
	text = text.replace(' ','')
	numbers = 0
	for x in text:
		if x in '0123456789':
			numbers += 1
	if numbers > len(text) / 2:
		return True
	else:
		return False

def textToMostlyNumeric( text ):
	text = text.replace(' ','')
	return text

def isVat( text ):
	if textToVat( text ):
		return True
	else:
		return False

def textToVat( text ):
	text = text.replace( ' ', '' )
	text = text.upper()
	expressions = [
 		'^[A-Z][0-9]{8}$', '^[0-9]{8}[A-Z]$'
	]
	for e in expressions:
		ex = re.compile( e )
		if ex.search( text ):
			return text
	return ''

def isPageNumber( text ):
	if textToPageNumber( text ):
		return True
	else:
		return False

def textToPageNumber( text ):
	current = None	
	total = None

	blocks = []
	inSequence = False
	for c in text:
		if c in '0123456789':
			if not inSequence:
				inSequence = True
				blocks.append( u'' )
			blocks[-1] += c
		else:
			inSequence = False
	if len(blocks) > 0:
		current = textToFloat( blocks[0] )
	if len(blocks) > 1:
		total = textToFloat( blocks[1] )

	if current > 100:
		current = None
	if total > 100:
		total = None
	if current:
		return (current, total)
	else:
		return None


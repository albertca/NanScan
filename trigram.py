
class Trigram:

	# Returns a list of the trigrams of a sentence. That is, the list of
	# all trigrams of each of the words in a string. Words are currently 
	# splitted by the space character only.
	# Note that more than a list it's a sorted set. So there are no repeated items.
	@staticmethod
	def trigramList( text ):
		words = text.split( ' ' )
		l = set()
		for x in words:
			for y in Trigram.wordTrigramList( x ):
				l.add( y )
		l = list( l )
		l.sort()
		return l

	# Calculates the list of trigrams contained in a word. If you feed
	# this function with an string with spaces they'll be treated like
	# normal characters. The usual trigram function is trigramList() which
	# returns trigrams for all of it's words.
	# Note that more than a list it's a sorted set. So there are no repeated items.
	@staticmethod
	def wordTrigramList( text ):
		l = set()
		size = len(text) + 1
		text = '  ' + text + ' '
		for x in range(size):
			l.add( text[x:x+3] )
		l = list( l )
		l.sort()
		return l

	# Calculates similarity between two strings using a trigram algorithm.
	# This is based in PostgreSQL pg_trgm implementation.
	# There's also a commented alternative for the final calculation of the
	# distance.
	@staticmethod
	def trigram( text1, text2 ):
		l1 = Trigram.trigramList( text1.lower() )
		l2 = Trigram.trigramList( text2.lower() )
		size1 = len(l1)
		size2 = len(l2)
		p1 = 0
		p2 = 0
		count = 0
		while p1 < size1 and p2 < size2:
			if l1[p1] < l2[p2]:
				p1 += 1
			elif l1[p1] > l2[p2]:
				p2 += 1
			else:
				p1 += 1
				p2 += 1
				count += 1

		return float(count) / float( size1 + size2 - count )

		# Here another way of calculating the similarity
		#if size1 > size2:
			#return float(count) / float( size1 )
		#else:
			#return float(count) / float( size2 )
				
	
if __name__ == '__main__':
	print Trigram.trigramList( 'abc' )
	print Trigram.trigramList( 'abcabc' )
	print Trigram.trigramList( 'hola' )
	print Trigram.trigramList( 'adeu manalet' )

	print Trigram.trigram( 'abc', 'abc' )
	print Trigram.trigram( 'abcabc', 'abc' )
	print Trigram.trigram( 'abcdef', 'abc' )
	print Trigram.trigram( 'abcdef', 'bcd' )
	print Trigram.trigram( 'bcdef', 'abc' )

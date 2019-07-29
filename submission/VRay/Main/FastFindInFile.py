import os

#Implementation of a fast 'find-in-files'.
#Was made to by used by VrsceneParser.py

########################
# PUBLIC FUNCTIONS
########################

class file_identifier:
	def __init__( self, identifierString, foundAtPosition ):
		self.identifierString = identifierString
		self.foundAtPosition = foundAtPosition

# A fast function that identifies where in a file tokens appear.
# Used to quickly scan very large vrscene files for important tokens. Optimized for files several GB in size.
# The results of this function are typically passed into the vrscene file parser functions.
#
# Example input:
#    filename = "my_large_scene.vrscene"
#    identifierStringsArray = [ "SettingsOutput", "RenderChannelColor" ]   #Two strings to look for during the scan. These two are important to vrscene files.
#    whitespaceChars = " \t;{}=\r\n"   #Identifiers must begin and end with one of these whitespace characters.
#
# Example output. The ordered file positions of all the found identifier strings:
#    (array of file_identifiers) [<'SettingsOutput', 818>, <'RenderChannelColor', 7834>, <'RenderChannelColor', 7904>, <'RenderChannelColor', 7995>, <'RenderChannelColor', 8097>]
#

def find_identifiers_in_file( filename, identifierStringsArray, whitespaceChars, threadingController ):

	positionsInFile = []

	#print "Scanning this file for identifier strings: " + filename
	positionsInFile = _fast_find_in_file( filename, identifierStringsArray, whitespaceChars, threadingController )
	
	return positionsInFile


########################
# INTERNAL FUNCTIONS
########################

#Internal function. Don't call this function directly.
def _fast_find_in_file( filename, identifierStringsArray, whitespaceChars, threadingController ):
	#search the last N megabytes of a file
	results = _fast_file_scan( filename, identifierStringsArray, threadingController )
	results = _test_identifier_results_for_whitespace( filename, results, whitespaceChars )
	return results

#Internal function. Don't call this function directly.
#This function performs a fast scan through the file looking for a set of identifier symbols.
#File must be encoded using an encoding that uses 8 bytes per a-zA-Z character.
#Example: ASCII, UTF-8 are good. UFT-16 is no good. Strings in the vrscene itself are decoded as UTF-8.
def _fast_file_scan( filename, identifierStringsArray, threadingController ):

	outputLocations = []

	fileSize = os.path.getsize( filename )

	#Buffer size for reading chunks of data. I ran a bunch of benchmarks on a network drive, and 8K seems to be about optimal.
	bufferSize = 8192

	with open( filename, 'rb' ) as fileHandle:

		bufferPosInFile = 0
		bufferBytes = fileHandle.read( bufferSize )
		while bufferBytes:

			#get the next block of data
			nextBufferBytes = fileHandle.read( bufferSize )

			#search for each identifier in this block (and its between block)
			for identifierString in identifierStringsArray:
				
				#do a straight search of the buffer
				bufferFindIndex = -1
				while True:
					bufferFindIndex = bufferBytes.find( identifierString, bufferFindIndex+1 ) #not using a regex search, because find is very much faster. Not doing byte-by-byte, because that is very very slow.
					if bufferFindIndex == -1:
						break
					foundAtIndexInFile = bufferPosInFile + bufferFindIndex
					outputLocations.append( file_identifier(identifierString, foundAtIndexInFile) )

				#catch the find case where the identifier string falls halfway between two buffer reads
				if nextBufferBytes != None:

					inbetweenBytes = bufferBytes[ len( bufferBytes ) - len(identifierString) + 1 : ] + nextBufferBytes[ 0 : len(identifierString) - 1 ]

					inbetweenFindIndex = -1
					while True:
						inbetweenFindIndex = inbetweenBytes.find( identifierString, inbetweenFindIndex+1 )
						if inbetweenFindIndex == -1:
							break
						foundAtIndexInFile = bufferPosInFile + len( bufferBytes ) - len(identifierString) + 1 + inbetweenFindIndex
						outputLocations.append( file_identifier( identifierString, foundAtIndexInFile ) )

			#do some error checking.
			#for example, if the user searches for a small string (example 'b'), this function is going to blow up with so many hits.
			#this is an arbitrary sanity check that is built in so nothing blows up.
			if len(outputLocations) > 1000:
				raise Exception( "_fast_file_scan: Too many matches found for the following identifier strings. Please refine your search strings: " + str(identifierStringsArray) )

			#get ready for the next loop
			bufferPosInFile += len( bufferBytes )
			bufferBytes = nextBufferBytes

			#Update progress and check for cancel
			threadingController.set_progress( bufferPosInFile / float(fileSize) )
			if threadingController.is_canceled():
				return []

	return outputLocations

#Internal function for _test_identifier_results_for_whitespace
def _is_whitespace( char, whitespaceChars ):
	for wsChar in whitespaceChars:
		if char == wsChar:
			return True
	return False

#Internal function used to make sure the identifier strings found in _fast_file_scan have whitespace before/after them.
#This function was made because doing a regex (rather than a find) on the original data is very very slow.
#It is fast because it is only doing lookups into the file, and not reading or scanning through the file.
#An example of how this function works: The string "vraySettingsOutput" should not be identified as a "SettingsOutput", so
#this function will remove that one because it does not have whitespace before it.
def _test_identifier_results_for_whitespace( filename, locationsOfIdentifiers, whitespaceChars ):
	
	outputLocationsOfIdentifierStrings = []

	fileSize = os.path.getsize( filename )

	with open( filename, 'rb' ) as fileHandle:

		for identifierObj in locationsOfIdentifiers:
			identifierString = identifierObj.identifierString
			identifierLocation = identifierObj.foundAtPosition

			#edge cases where the identifier is at the very beginning or end of the file just include these for simplicity sake. It will do no harm in the cases I've discovered.
			if identifierLocation == 0 or identifierLocation + len(identifierString) == fileSize:
				outputLocationsOfIdentifierStrings.append( identifierObj )
			
			else:

				#move to the byte BEFORE the identifier starts, and read until the byte AFTER it ends.
				fileHandle.seek( identifierLocation - 1 )
				identifierBytes = fileHandle.read( len(identifierString) + 2 ) #read the first and last byte of the identifier string

				#if it begins and ends in whitespace, include it
				if _is_whitespace( identifierBytes[0], whitespaceChars ) and _is_whitespace( identifierBytes[ len(identifierBytes)-1 ], whitespaceChars ):
					outputLocationsOfIdentifierStrings.append( identifierObj )

	return outputLocationsOfIdentifierStrings

import os
import re
import threading

#A file that implements a bunch of useful functions related to getting data out of vrscene files.
import FastFindInFile

#Implementation of a simple and fast vrscene parser.
#Was made to by used by VrsceneUtils.py

########################
# PUBLIC FUNCTIONS
########################

# A threaded and unthreaded function that identifies datablocks in a vrscene file and parses their key/value pairs.
# The results of this function are typically passed into the vrscene utils functions.
# If you're using the threaded version, you can poll for completed results. Only use the unthreaded version if you really have to.
# Do not call this more than once on the same file. It is a waste. Just append to "vrsceneObjectNamesToFind".
#
# Example input:
#    filename = "my_large_scene.vrscene"
#    vrsceneObjectNamesToFind = [ "SettingsOutput", "RenderChannelColor" ]   #Two types of data blocks that we will try to retrieve data for.
#
# Example output:
# {
#     'SettingsOutput vraySettingsOutput': {
#         'img_width': '960',
#         'img_height': '540',
#         'img_file': 'conrads_render.png',
#         'img_dir': 'C:/Users/conrad.wiebe/vrayoutput/',
#         ...
#     },
#     'RenderChannelColor vrayRE_Diffuse': {
#         'alias': '101',
#         'name': 'diffuse'
#     },
#     ...
# }
#

#Threaded version
class get_vrscene_properties_threaded:
    def __init__( self, filename, vrsceneObjectNamesToFind ):
        self._threadingController = threading_controller()
        self._thread = threading.Thread( target = _get_vrscene_properties_internal, args = ( filename, vrsceneObjectNamesToFind, self._threadingController, ) )
        self._thread.start()
    #Client can call this during operation to cancel and complete the operation.
    #Will wait until thread execution has ended.
    def cancel( self ):
        self._threadingController.set_canceled()
        self._thread.join()
    #Returns true if the operation is complete (ie results are in or it's been canceled)
    def is_complete( self ):
        return self._threadingController.is_complete()
    #Gets the progress of the operation. Range is 0.0 to 1.0
    def get_progress( self ):
        return self._threadingController.get_progress()
    #Stops execution until the operation is complete.
    def wait_for_complete( self ):
        self._thread.join()
    #Will return the results if the results are ready.
    #Will return None if the operation was canceled.
    #Will raise an exception if the results are still processing.
    #Will raise an exception if there was a problem with the operation (eg file not found, etc.)
    def get_results( self ):
        if not self._threadingController.is_complete():
            raise Exception( "get_vrscene_properties_threaded: Do not call get_results() until is_complete() return True." )
        if self._threadingController.exception:
            raise self._threadingController.exception #Raise the exception that occured in the thread
        if self._threadingController.is_canceled():
            return None
        return self._threadingController.results

#Unthreaded version.
def get_vrscene_properties_unthreaded( filename, vrsceneObjectNamesToFind ):
    vrsceneThread = get_vrscene_properties_threaded( filename, vrsceneObjectNamesToFind )
    vrsceneThread.wait_for_complete()
    return vrsceneThread.get_results()

########################
# INTERNAL FUNCTIONS
########################

#Internal class for threading control. Do not use this class directly.
class threading_controller:
    def __init__( self ):
        #Output results. Only access these once "is_complete" is true.
        self.results = {}
        self.exception = None

        self._threadLock = threading.Lock()
        self._isComplete = False
        self._isCanceled = False
        self._progress = 0.0

    def is_complete( self ):
        with self._threadLock:
            return self._isComplete
    def get_progress( self ):
        with self._threadLock:
            return self._progress
    def is_canceled( self ):
        with self._threadLock:
            return self._isCanceled

    def set_complete( self ):
        with self._threadLock:
            self._isComplete = True
    def set_progress( self, progress ):
        with self._threadLock:
            self._progress = progress
    def set_canceled( self ):
        with self._threadLock:
            self._isCanceled = True
            self._isComplete = True
            self.results.clear()
            self.exception = None

#Internal function that does the work. See docs for the public version of this function
def _get_vrscene_properties_internal( filename, vrsceneObjectNamesToFind, threadingController ):

    try:
        #error check input
        if type(vrsceneObjectNamesToFind) != type( [] ):
            raise Exception( 'Input to get_vrscene_properties must be an array of strings. Example: [ "SettingsOutput", "RenderChannelColor" ].' )

        whitespaceChars = " \t;{}=\r\n"
        datablockArray = _get_all_data_blocks( filename, vrsceneObjectNamesToFind, whitespaceChars, threadingController )
        for datablock in datablockArray:
            vrsceneBlockTitle, keyValuePairs = _parse_vrscene_data_block( datablock )
            try:
                threadingController.results[vrsceneBlockTitle].update( keyValuePairs )
            except KeyError:
                threadingController.results[vrsceneBlockTitle] = keyValuePairs

    except Exception as e:
        threadingController.results.clear()
        threadingController.exception = e

    threadingController.set_complete()

#Internal function that gets the blocks of data of each of the found identifier strings.
#Reads up to 16K of data for each datablock. This is to avoid unbound reads and can be modified to be larger if we need.
def _get_all_data_blocks( filename, identifierStringsArray, whitespaceChars, threadingController ):

    outputDatablockArray = [] #output

    identifiersArray = FastFindInFile.find_identifiers_in_file( filename, identifierStringsArray, whitespaceChars, threadingController )

    fileSize = os.path.getsize( filename )
    dataBlockBufferSize = 16384 #Each block is read in a maximum of 16K of data. This is hard-limited because we can't do unbound reads.
    with open( filename, 'rb' ) as fileHandle:

        for i in range( 0, len(identifiersArray) ):

            #read from the beginning of this block, to the start of the next block, or 16K, or the end of file (whichever is first)
            startAt = identifiersArray[i].foundAtPosition
            endAt = startAt + dataBlockBufferSize
            endAt = min( endAt, fileSize )
            if i < len(identifiersArray) - 1:
                endAt = min( endAt, identifiersArray[i+1].foundAtPosition )

            #begin the scan at the request spot
            fileHandle.seek( startAt )

            #get the datablock and append it to our output
            datablock = fileHandle.read( endAt - startAt )
            outputDatablockArray.append( datablock )

    return outputDatablockArray

#Internal function that removes comments in the vrscene files, strips the data from strings, and removes any data past the closing "}" parenthesis.
#This is needed later to ensure a smooth parsing of the key/value pairs.
#The performance of this function should be reasonable considering it is operating on a maximum of 16K of data (as defined in _get_data_blocks).
#Returns:
# 1) The title of the vrscene block data. Eg. "SettingsOutput vraySettingsOutput "
# 2) The data inside of the {} parenthesis.
# 3) The data inside of the {} parenthesis, but with all characters in string-quotes replaced with X's. (so they don't get mixed up when parsing)
def _pre_process_data_block( datablock ):

    #this regex has 2 capture groups the first one to try to capture will catch on all strings wrapped in quotes the second one will capture everything starting at 2 slashes going until a new line character is reached.
    #Since capture groups can not overlap this will capture all comments in there own groups which can then be handled in a separate replacement function.
    pattern = re.compile( r'(".*?"|\'.*?\')|(//[^\r\n]*)' )
    
    #this function will take a look at everything that is captured and if it is part of the second capture group it will be removed.
    #Capture Groups 0: everything that is captured. 1: Strings that are captured (Will be ignored). 2: Comments that are captured.
    def commentRepl( matchObj ):        
        if  matchObj.group( 2 ) != None:
            return ""
        return matchObj.group( 0 )
    
    datablock = pattern.sub( commentRepl, datablock )

    #do some error checking on this block.
    #an opening parenthesis MUST occur before the first semi-colon is seen. If not, this block is not in correct format.
    parenthIndex = datablock.find( '{' )
    semicolonIndex = datablock.find( ';' )
    if parenthIndex > semicolonIndex:
        raise Exception( 'vrscene parsing error: Could not identify block of code from file.' )

    #state variables
    state = 0 #0=not in quote, 1=in single quote, 2=in double quote	
    parenthesisLevel = 0
    openingParenthesisFoundAt = -1
    closingParenthesisFoundAt = -1

    vrsceneBlockWithoutStrings = ""
    index = 0
    for char in datablock:

        #part 1: strip this character if it's in a quotation
        insideQuote = False
        if state == 0:
            if char == "'":
                state = 1
            if char == '"':
                state = 2
        elif state == 1:
            if char == "'":
                state = 0
            else:
                insideQuote = True
        else: #state == 2
            if char == '"':
                state = 0
            else:
                insideQuote = True
        if insideQuote:
            char = "X" #strip this char
        if parenthesisLevel > 1 or ( parenthesisLevel == 1 and char != '}' ): #add this character if we're inside of a {} block
            vrsceneBlockWithoutStrings += char

        #part 2: look for parenthesis (and the ending parenthesis to this block)
        if char == '{':
            if parenthesisLevel == 0:
                openingParenthesisFoundAt = index
            parenthesisLevel += 1
        elif char == '}':
            if parenthesisLevel == 1:
                closingParenthesisFoundAt = index
                break #exit out if the last parenthesis closes!
            parenthesisLevel -= 1

        index += 1

    if openingParenthesisFoundAt == -1:
        raise Exception( 'vrscene parsing error: Could not find an opening parenthesis for vrscene object.' )
    if closingParenthesisFoundAt == -1:
        raise Exception( 'vrscene parsing error: Could not find a closing parenthesis. Ensure the vrscene file is formatted correctly, and the vrscene object you requested is less than 16 kilobytes of data.' )
    
    #strip out anything not in the parenthesis block
    vrsceneBlockTitle = datablock[ 0 : openingParenthesisFoundAt ]
    vrsceneBlock = datablock[ openingParenthesisFoundAt+1 : closingParenthesisFoundAt ]

    #return both the proper vrscene data, and the vrscene data that does not contain any data inside quotations.
    return vrsceneBlockTitle, vrsceneBlock, vrsceneBlockWithoutStrings

#internal function
def _parse_vrscene_data_block( datablock ):

    try:
        #Pull and pre-process the data from the datablock retrieved from the file
        vrsceneBlockTitle, vrsceneBlock, vrsceneBlockStripped = _pre_process_data_block( datablock )
    except Exception as e:
        print(str(e)) #Parsing errors, just allow it to fall through and print a warning.
        return "", {}

    #Parse into KEY/VALUE pairs
    outputKeyValuePairs = {}
    lineStart = 0
    lineEnd = vrsceneBlockStripped.find( ';' )
    while lineEnd != -1:
        entry = vrsceneBlock[lineStart : lineEnd]
        entryStripped = vrsceneBlockStripped[lineStart : lineEnd]
        equalPos = entryStripped.find( '=' )
        if equalPos == -1:
            print('vrscene parsing warning: Could not extract key/value pair from this entry in the vrscene file: "' + entry + '". Skipping entry.')
        else:
            key = entry[0:equalPos].strip()
            val = entry[equalPos+1:].strip()
            if key == "" or val == "":
                print('vrscene parsing warning: Could not extract key/value pair from this entry in the vrscene file: "' + entry + '". Skipping entry.')
            else:
                #strip quotes
                if val[0] == "'" and val[len(val)-1] == "'":
                    val = val[1:len(val)-1]
                elif val[0] == '"' and val[len(val)-1] == '"':
                    val = val[1:len(val)-1]
                outputKeyValuePairs[key] = val

        #prepare next loop
        lineStart = lineEnd + 1
        lineEnd = vrsceneBlockStripped.find( ';', lineStart )

    return vrsceneBlockTitle.strip(), outputKeyValuePairs

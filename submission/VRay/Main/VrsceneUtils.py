import os
import time

#A file that implements a bunch of useful functions related to getting data out of vrscene files.
import VrsceneParser
import threading

vrsceneThread = None
cancelThread = False
parseResults = []

########################
# PUBLIC FUNCTIONS
########################

def InsertBeforeExtension( file, component ):
    innerPath, ext = os.path.splitext( file )
    return innerPath+component+ext

def CancelParsing():
    global cancelThread
    
    cancelThread = True
    
def GetProgress():
    global vrsceneThread
    if vrsceneThread:
        return vrsceneThread.get_progress()
    return 0
    
def GetOutputValue():
    global parseResults
    
    return parseResults
    
#This function takes the 'img_dir' and 'img_file' properties from the first 'SettingsOutput' block in the vrscene file, and returns the output file path.
def get_output_data_from_vrscene_file( filename, imgPathOverride = "" ):
    global vrsceneThread
    global cancelThread
    global parseResults
    
    cancelThread = False
    
    vrsceneObjectNamesToFind = ["SettingsOutput",
                                "RenderChannelBumpNormals",
                                "RenderChannelColor",
                                "RenderChannelCoverage",
                                "RenderChannelDenoiser",
                                "RenderChannelDRBucket", 
                                "RenderChannelExtraTex",
                                "RenderChannelGlossiness", 
                                "RenderChannelMtlID",
                                "RenderChannelMultiMatte",
                                "RenderChannelNodeID",
                                "RenderChannelNormals",
                                "RenderChannelObjectSelect", 
                                "RenderChannelRenderID",
                                "RenderChannelToon",
                                "RenderChannelVelocity",
                                "RenderChannelZDepth" ]
    overridePath = ""
    outputSettings = {}
    renderChannels = []
    renderFiles = []
    seconds = 0
    parseResults = []
    
    vrsceneThread = VrsceneParser.get_vrscene_properties_threaded( filename, vrsceneObjectNamesToFind )
    while not vrsceneThread.is_complete():
        time.sleep(1)
        if cancelThread:
            vrsceneThread.cancel()
    
    vrsceneData = vrsceneThread.get_results()

    #Exit out if it was canceled
    if vrsceneData == None:
        parseResults.append(None)
        parseResults.append( "" )
        parseResults.append( -1 )
        parseResults.append( -1 )
        parseResults.append( -1 )
        parseResults.append( -1 )
        return
        
    for objectName in vrsceneData:
        objectProperties = vrsceneData[objectName]
                
        if objectName.startswith( "SettingsOutput" ):
            outputSettings = objectProperties
            
            if 'img_dir' in objectProperties and 'img_file' in objectProperties:
                path = os.path.join( objectProperties['img_dir'], objectProperties['img_file'] )
                
        elif objectName.startswith( "RenderChannel" ):
            renderChannels.append( objectProperties["name"] )
    
    imgDir = ""
    imgFile = ""
    
    if not imgPathOverride == "":
        imgDir, imgFile = os.path.split(imgPathOverride)
        overridePath = imgPathOverride
    else:
        imgDir = outputSettings.get( "img_dir","" )
        imgFile = outputSettings.get( "img_file","" )
        overridePath = os.path.join( imgDir, imgFile )
        imgDir, imgFile = os.path.split( overridePath )
        
    if imgDir == "" or imgFile == "":
        parseResults.append( [] )
        parseResults.append( "" )
        parseResults.append( -1 )
        parseResults.append( -1 )
        parseResults.append( -1 )
        parseResults.append( -1 )
        return
    
    isMultiChannel = int( outputSettings.get( "img_rawFile","0" ) )
    separateFolders = int( outputSettings.get( "relements_separateFolders", "0" ) )

    if isMultiChannel:
        renderChannels = [ "" ]
    else:
        separateAlpha =  int( outputSettings.get( "img_separateAlpha","0" ) )
        
        if separateAlpha:
            renderChannels.insert(0,"Alpha")
        
        noRGBA = int( outputSettings.get( "img_dontSaveRgbChannel","0" ) )
        separateRGBA = int( outputSettings.get( "relements_separate_rgba","0" ) )
        
        if not noRGBA:
            if separateRGBA and separateFolders:
                renderChannels.insert(0,"rgba")
            else:
                renderChannels.insert(0,"")

    relementsDivider = outputSettings.get( "relements_divider","." )
    framePaddingLength = int(outputSettings.get("anim_frame_padding", 4))
    needFrameNumber = int(outputSettings.get("img_file_needFrameNumber", 0))
    
    for channel in renderChannels:
        path = imgDir
        tempImgFile = imgFile
        if not channel == "":
            tempImgFile = InsertBeforeExtension( tempImgFile, relementsDivider+channel )
        
        if separateFolders:
            path = os.path.join( path, channel )
        
        path = os.path.join( path, tempImgFile )
        
        renderFiles.append( path )
    
    height = int( outputSettings.get( "img_width", -1 ) )
    width = int( outputSettings.get( "img_height", -1 ) )
    
    parseResults.append( renderFiles )
    parseResults.append( overridePath )
    parseResults.append( height )
    parseResults.append( width )
    parseResults.append( framePaddingLength )
    parseResults.append( needFrameNumber )

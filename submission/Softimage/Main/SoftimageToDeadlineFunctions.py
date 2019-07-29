from __future__ import print_function, with_statement # with_statement is needed for python 2.5 compatability

import datetime
import os
import re
import subprocess

import win32com.client

Application = win32com.client.Dispatch( 'XSI.Application' )
XSIUIToolkit = win32com.client.Dispatch( 'XSI.UIToolkit' )

##-------------------------------------------------------------------------------------
## SoftimageToDeadlineFunctions.py
## Thinkbox Software Inc, 2016
##
## This script contains all the additional functions used by both
## the SoftimageToDeadline.py and SoftimageToDeadlineLogic.py scripts.
##-------------------------------------------------------------------------------------

##-------------------------------------------------------------------------------------
## HELPER FUNCTIONS
##-------------------------------------------------------------------------------------

def GetDeadlineCommand():
    deadlineBin = ""
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        #if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass
        
    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if deadlineBin == "" and  os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f:
            deadlineBin = f.read().strip()

    deadlineCommand = os.path.join(deadlineBin, "deadlinecommand")
    
    return deadlineCommand

def CallDeadlineCommand( arguments, background=True, readStdout=True ):
    deadlineCommand = GetDeadlineCommand()

    startupinfo = None
    creationflags = 0
    if os.name == 'nt':
        if background:
            # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
            if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            # still show top-level windows, but don't show a console window
            CREATE_NO_WINDOW = 0x08000000   #MSDN process creation flag
            creationflags = CREATE_NO_WINDOW
        
    arguments.insert( 0, deadlineCommand)
    
    stdoutPipe = None
    if readStdout:
        stdoutPipe=subprocess.PIPE
        
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=stdoutPipe, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags )
    proc.stdin.close()
    proc.stderr.close()

    output = ""
    if readStdout:
        output = proc.stdout.read()
    return output

# Gets the ceiling of the specified number.
def Ceiling(num):
    num = float(num)
    floorNumber = Floor(num)
    if(floorNumber == num):
        ceiling = int(num)
    else:
        ceiling = int(floorNumber + 1)
        
    return ceiling

# Gets the floor of the specified number.
def Floor(num):
    number = float(num)
    roundNumber = round(num)
    if(roundNumber > num):
        roundNumber -= 1

    return int(roundNumber)

# Returns true if filename's path is absolute (a full path has been specified).
def IsPathAbsolute(filename):
    drive = filename[0:2].lower()
    driveRegex = re.compile("[a-z]:")
    uncRegex = re.compile("\\\\")
    result=False
    
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        if(re.match(driveRegex,drive) or re.match(uncRegex,drive)):
            result=True
    else:
        if(filename[0:1] == "/"):
            result=True
        
    return result
    
# Returns true if the the filename's path is local.
def IsPathLocal(filename):
    drive = filename[0:2].lower()
    
    result=False
    if(drive=="c:" or drive=="d:" or drive=="e:"):
        result=True

    return result

# Returns true if the extension is valid.
def IsExtensionValid(filename):
    ext2=filename[len(filename)-3:len(filename)]
    ext3=filename[len(filename)-4:len(filename)]
    ext5=filename[len(filename)-6:len(filename)]
        
    result=False
    
    #merely broken up since python statements can't extend multiple lines
    if(ext2==".ct" or ext3==".pic" or ext3==".bmp" or ext3==".tif" or ext3==".tga"):
        result=True
    elif(ext3==".sgi" or ext3==".als" or ext3==".rla" or ext3==".png" or ext3==".hdr"):
        result=True
    elif(ext3==".cth" or ext3==".pal" or ext3==".jpg" or ext3==".yuv" or ext3==".map"):
        result=True
    elif(ext3==".exr" or ext5==".alias"):
        result=True
        
    return result

#Returns the path of the filename.
def GetFilePath(filename):
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        lastSlash = filename.rfind("\\")
    else:
        lastSlash = filename.rfind("/")
    return filename[0:lastSlash+1]

#Returns the base file of the filename (no extension).
def GetFileBaseName(filename):
    lastPeriod = filename.rfind(".")
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        lastSlash = filename.rfind("\\")
    else:
        lastSlash = filename.rfind("/")
    
    baseFilename = filename[lastSlash:lastPeriod]
    if baseFilename[0:1] == "\\" or baseFilename[0:1] == "/":
        baseFilename = baseFilename[1:len(baseFilename)]
    return baseFilename

#Returns the extension of the filename.
def GetExtension(filename):
    lastPeriod = filename.rfind(".")
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        lastSlash = filename.rfind("\\")
    else:
        lastSlash = filename.rfind("/")
    return filename[lastPeriod:len(filename)]

def GetDeadlineLine(arguments, forceShowWindow = False):
    deadlineLine = "Error getting line"
    
    deadlineArray=GetDeadlineArray(arguments, forceShowWindow)
    
    if(len(deadlineArray)<2 or deadlineArray[1] != "Error"):
        if(len(deadlineArray)>0):
            deadlineLine = deadlineArray[0]
        else:
            deadlineLine=""
            
    return deadlineLine
        
#Reads in a list of items from the specified file and returns them in an array.
def GetArray(text):

    text=text.splitlines()
    
    size=0
    for line in text:
        if(line!=""):
            size+=1
            
    tempDeadlineArray = [0]*(size)
    index=0
    for line in text:
        if(line!=""):
            tempDeadlineArray[index] = line
            index+=1
    
    size*=2
    deadlineArray=[0]*(size)
    index=0
    for item in tempDeadlineArray:
        deadlineArray[index] = item
        deadlineArray[index+1] = item
        index+=2


    return deadlineArray

#Returns an array of available items returned from DeadlineCommandBG.exe using the
#specified argument.
def GetDeadlineArray(arguments, forceShowWindow = False):
    deadlineArray = [0]*2
    try:
        deadlineCommand = GetDeadlineCommand()
        arguments.insert(0, deadlineCommand)
        
        startupinfo = None
        creationflags = 0
        if os.name == 'nt':
            if forceShowWindow:
                # still show top-level windows, but don't show a console window
                CREATE_NO_WINDOW = 0x08000000   #MSDN process creation flag
                creationflags = CREATE_NO_WINDOW
            else:
                # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
                if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
                elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
        proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags)
        proc.stdin.close()
        proc.stderr.close()
        
        text = proc.stdout.read()
        
        if(text != "Bad submission arguments"):
            deadlineArray =  GetArray(text)
        else:
            deadlineArray[0]="Bad submission arguments"
            deadlineArray[1]="Error"
    except:
        Application.LogMessage("An Exception was generated attempting to run deadline command with args " + argument)
        deadlineArray[0]="Error getting array"
        deadlineArray[1]="Error"
        
    return deadlineArray

#Returns desired item if it exists in the array, otherwise it returns the first item.
def GetDefaultItem(deadlineArray,desiredItem):
    default = deadlineArray[0]
    
    for item in deadlineArray:
        if(item==desiredItem):
            default=desiredItem
            
    return default

##-------------------------------------------------------------------------------------
## PROPERTY FUNCTIONS
##-------------------------------------------------------------------------------------

#Gets the version from the application and parses it for major/minor.
def GetVersion():
    fullVersionString = Application.Version()
    firstPeriod = fullVersionString.find(".")
    secondPeriod = fullVersionString.find(".",firstPeriod+1)
    return fullVersionString[0:secondPeriod]
        
# Gets the major version from the application as a number instead of a string.
def GetIntVersion():
    fullVersionString = Application.Version()
    firstPeriod = fullVersionString.find(".")
    return int(fullVersionString[0:firstPeriod])

def IsSaveRequired():
    # Check the project
    dirtyCount = Application.ExecuteCommand("GetValue",["Project.dirtycount"])
    if dirtyCount > 0:
        return True
    
    # Check root model - all sub-models will notify up
    dirtyCount = Application.ExecuteCommand("GetValue",[str(Application.ActiveSceneRoot) + ".dirty_count"])
    if dirtyCount > 0:
        return True
    
    return False

def GetOpSetValue( opSet, name, defaultValue ):
    if opSet.Parameters(name) != None:
        return opSet.Parameters(name).Value
    return defaultValue

def IsMentalRay( currPass ):
    renderer = ""
    
    renderer = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".Renderer"])
    if(renderer == ""):
        renderer = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.Renderer"])

    if(renderer.lower() == "mental ray"):
        result=True
    else:
        result=False
        
    return result
    
def IsRedshift( currPass ):
    renderer = ""
    
    renderer = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".Renderer"])
    if(renderer == ""):
        renderer = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.Renderer"])

    if(renderer.lower() == "redshift"):
        result=True
    else:
        result=False
        
    return result

def IsArnold( currPass ):
    renderer = ""
    
    renderer = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".Renderer"])
    if(renderer == ""):
        renderer = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.Renderer"])

    if(renderer.lower() == "arnold render"):
        result=True
    else:
        result=False
        
    return result

def IsVray( currPass ):
    renderer = ""
    
    renderer = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".Renderer"])
    if(renderer == ""):
        renderer = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.Renderer"])

    if(renderer.lower() == "vray"):
        result=True
    else:
        result=False
        
    return result

def GetWorkgroupPath():
    path = ""
    try:
        path = Application.ExecuteCommand("GetValue",["preferences.data_management.workgroup_appl_path"])
    except:
        pass
    return path

#Gets the frame range for the specified pass.
def GetFrameRange(currPass):
    frameString = "0"
    
    index = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".FrameRangeSource"])
    # If index is 3, that means we're using the scene frame range.
    if index == 3:
        index = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.FrameRangeSource"])
        # Scene Render Options - If index is 0, that means we're using a frame range.
        if index == 0:
            lower = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.FrameStart"])
            higher = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.FrameEnd"])
            frameString = (str(lower) + "-" + str(higher))
            # print "Scene Render Options : Frame Range: %s" % frameString
        elif index == 1:
            # If index is 1, that means we're using a frame set.
            frameString = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.FrameSet"])
            # print "Scene Render Options : Frame Set: %s" % frameString
        else:
            # must be using timeline.
            start = int(Application.ExecuteCommand("GetValue",["PlayControl.In"]))
            end = int(Application.ExecuteCommand("GetValue",["PlayControl.Out"]))
            frameString = (str(start) + "-" + str(end))
            # print "Scene Render Options : Timeline: %s" % frameString
    else:
        if index == 0:
            # If index is 0, that means we're using a frame range.
            lower = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".FrameStart"])
            higher = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".FrameEnd"])
            frameString = (str(lower) + "-" + str(higher))
            # print "CURRENT PASS : Frame Range: %s" % frameString
        elif index == 1:
            # If index is 1, that means we're using a frame set.
            frameString = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".FrameSet"])
            # print "CURRENT PASS : Frame Set: %s" % frameString
        else:
            # must be using timeline.
            start = int(Application.ExecuteCommand("GetValue",["PlayControl.In"]))
            end = int(Application.ExecuteCommand("GetValue",["PlayControl.Out"]))
            frameString = (str(start) + "-" + str(end))
            # print "CURRENT PASS : Timeline: %s" % frameString
        
    return frameString

#Gets the current frame.
def GetCurrentFrame():
    #return (str(Application.ExecuteCommand("GetValue",["PlayControl.Current"])))
    return (Application.ExecuteCommand("GetValue",["PlayControl.Current"]))

#Gets the frame step for the specified pass.
def GetFrameStep(currPass):
    #return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".FrameStep"])
    
    frameStep = ""
    
    index = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".FrameRangeSource"])
    # If index is 3, that means we're using the scene frame range.
    if index == 3:
        index = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.FrameRangeSource"])
        # If index is 1, that means we're using a frame set, and we don't need to specify a step frame.
        if index != 1:
            frameStepValue = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.FrameStep"])
            if frameStepValue > 1:
                frameStep = "x" + str(frameStepValue)
    else:
        # If index is 1, that means we're using a frame set, and we don't need to specify a step frame.
        if index != 1:
            frameStepValue = Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".FrameStep"])
            if frameStepValue > 1:
                frameStep = "x" + str(frameStepValue)
            
    return frameStep

#Gets if existing frames should be skipped for the specified pass.
def GetSkipExistingFrames(currPass):
    return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".FrameSkipRendered"])

#Gets the output filename for the specified pass.
def GetOutputFilename(currPass):
    filename = currPass.FrameBuffers(0).GetResolvedPath("")
    
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        filename = filename.replace("/","\\")
    else:
        filename = filename.replace("\\","/")
        
    return filename

def GetFrameBufferOutputFilename(currPass, index):
    filename = currPass.FrameBuffers(index).GetResolvedPath("")
    
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        filename = filename.replace("/","\\")
    else:
        filename = filename.replace("\\","/")
        
    return filename

def GetPluginOutputFolder():
    dir = Application.ExecuteCommand("GetValue",["Passes.RenderOptions.ResolvedOutputDir"])
    
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        dir = dir.replace("/","\\")
    else:
        dir = dir.replace("\\","/")
    
    return dir

#Gets if a movie is being created for the specified pass.
def GetCreateMovie(currPass):
    return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".MovieCreate"])

#Gets the movie filename for the specified pass.
def GetMovieFilename(currPass):
    return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".MovieResolvedFileName"])

#Gets the output filename for the specified FxTree output node
def GetFxOutputFilename(fxTreeOutputNode):
    return Application.ExecuteCommand("GetValue",[fxTreeOutputNode + ".path"])

#Gets the output width for the specified pass.
def GetOutputWidth(currPass):
    if(Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".ImageFormatOverride"])):
        return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".ImageWidth"])
    else:
        return Application.ExecuteCommand("GetValue",["Passes.RenderOptions.ImageWidth"])

def GetOutputHeight(currPass):
    if(Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".ImageFormatOverride"])):
        return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".ImageHeight"])
    else:
        return Application.ExecuteCommand("GetValue",["Passes.RenderOptions.ImageHeight"])
        
#Gets if motion blur is enabled for the specified pass.
def GetMotionBlur( currPass ):
   return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".MotionBlur"])

#Gets the minimum sampling level for the specified pass.
def GetMinSamplingLevel(currPass):
    return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name+ ".mentalray.SamplesMin"])

#Gets the minimum sampling level for the specified pass.
def GetMaxSamplingLevel(currPass):
    return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".mentalray.SamplesMax"])

#Gets if samples jitter is enabled for the specified pass.
def GetSamplesJitter(currPass):
    return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".mentalray.SamplesJitter"])

#Gets the samples filter number specified by the pass
def GetSamplesFilterNumber(currPass):
    return Application.ExecuteCommand("GetValue",["Passes." + currPass.Name + ".mentalray.SamplesFilterType"])

def GetSamplesFilterType(currPass):
    filter = GetSamplesFilterNumber(currPass)
        
    if(filter == 0):
        return "box"
    elif(filter == 1):
        return "triangle"
    elif(filter == 2):
        return "gauss"
    elif(filter == 3):
        return "mitchell"
    elif(filter == 4):
        return "lanczos"
    else:
        return "unknown"
        
def CreateProgressBar( caption, maximum, cancelEnabled ):
    progressBar = XSIUIToolkit.ProgressBar
    progressBar.Maximum = maximum
    progressBar.Caption = caption
    progressBar.CancelEnabled = cancelEnabled
    progressBar.Visible = True
    return progressBar
 
##-------------------------------------------------------------------------------------
## SUBMISSION FILE CREATION FUNCTIONS
##-------------------------------------------------------------------------------------
def WriteIntegrationSettings( submitInfoFile, groupBatch, opSet ):
    integrationSettingsPath = GetOpSetValue( opSet, "integrationSettingsPath", None )

    if integrationSettingsPath != None and integrationSettingsPath != "":
        with open( integrationSettingsPath ) as file:
            for line in file.readlines():
                submitInfoFile.write( "\n" + line )

        batchMode = GetOpSetValue( opSet, "batchMode", None )
        if batchMode != None and batchMode == "True":
            groupBatch = True

        regionRendering = bool( opSet.Parameters( "RegionRenderingCheckBox" ).Value )
        dependentAssembly = bool( opSet.Parameters( "RegionAssemblyJobCheckBox" ).Value )
        singleFrameJob = bool( opSet.Parameters( "RegionSingleJobCheckBox" ) )
        
        if regionRendering and singleFrameJob and dependentAssembly:
            kvpIndex = GetOpSetValue( opSet, "extraKVPIndex", None )
            if kvpIndex != None:
                tileFrame = str( opSet.Parameters( "RegionSingleFrameBox" ).Value )
                submitInfoFile.write( "\nExtraInfoKeyValue%s=FrameRangeOverride=%s" % ( kvpIndex, tileFrame ) )
    
    return groupBatch

#Creates the submission info file.
def CreateSubmissionInfoFile(opSet, currPass, submitInfoFilename, tilePrefix, jobName, batchName):
    Application.LogMessage("Creating Submission Info")
    passesListValue = opSet.Parameters("PassesListToRender").Value

    overridePasses = opSet.Parameters("OverridePasses").Value
    allPasses = opSet.Parameters("RenderAllPasses").Value
    
    isFxTreeJob = opSet.Parameters("FxTreeCheckBox").Value
    isSingleRegionJob = (bool(opSet.Parameters("RegionRenderingCheckBox").Value) and bool(opSet.Parameters("RegionSingleJobCheckBox").Value))
    
    frameStr = ""
    
    if(isFxTreeJob):
        frameStr = opSet.Parameters("Frames").Value
    elif(allPasses or len(passesListValue) > 0):
        if(overridePasses):
            frameStr = opSet.Parameters("Frames").Value
        else:
            isMovie = GetCreateMovie(currPass)
            frameStr = GetFrameRange(currPass)
            
            if(not isMovie):
                frameStr = str(frameStr) + str(GetFrameStep(currPass))
    else:
        frameStr = opSet.Parameters("Frames").Value
    
    Application.LogMessage("Frame range: " + frameStr)
    
    slaveTimeout = opSet.Parameters("SlaveTimeoutNumeric").Value * 60
    
    #Create the submit info file
    submitInfoFile = open(submitInfoFilename,"w")
    
    if(opSet.Parameters("BatchBox").Value):
        submitInfoFile.write("Plugin=SoftimageBatch")
    else:
        submitInfoFile.write("Plugin=Softimage")
        
    submitInfoFile.write("\nName=" + jobName)
    submitInfoFile.write("\nComment=" + opSet.Parameters( "CommentTextBox" ).Value)
    submitInfoFile.write("\nDepartment=" + opSet.Parameters( "DepartmentTextBox" ).Value)
    submitInfoFile.write("\nGroup=" + opSet.Parameters( "GroupComboBox" ).Value)
    submitInfoFile.write("\nPool=" + opSet.Parameters( "PoolComboBox" ).Value)
    submitInfoFile.write("\nSecondaryPool=" + opSet.Parameters( "SecondaryPoolComboBox" ).Value)
    submitInfoFile.write("\nPriority=" + str(opSet.Parameters( "PriorityNumeric" ).Value))
    submitInfoFile.write("\nConcurrentTasks=" + str(opSet.Parameters( "ConcurrentTasksNumeric" ).Value))
    submitInfoFile.write("\nTaskTimeoutSeconds=" + str(slaveTimeout))
    submitInfoFile.write("\nLimitGroups=" + opSet.Parameters( "LimitGroupsTextBox" ).Value)
    submitInfoFile.write("\nJobDependencies=" + opSet.Parameters( "DependenciesTextBox" ).Value)
    
    if opSet.Parameters("IsBlacklist").Value:
        submitInfoFile.write("\nBlacklist=" + opSet.Parameters( "MachineListTextBox" ).Value)
    else:
        submitInfoFile.write("\nWhitelist=" + opSet.Parameters( "MachineListTextBox" ).Value)
        
    if( isFxTreeJob ):
        fxTreeOutputNode = opSet.Parameters("FxTreeComboBox").Value
        submitInfoFile.write("\nOutputFilename0=" + GetFxOutputFilename(fxTreeOutputNode))
    else:
        frameNumber = ""
        if isSingleRegionJob:
            frameNumber = str(opSet.Parameters("RegionSingleFrameBox").Value)
        
        # Specify the output filename for each render channel
        outputIndex = 0
        for i in range( len(currPass.FrameBuffers) ):
            if bool(Application.ExecuteCommand("GetValue",[currPass.FrameBuffers(i).FullName + ".Enabled"])):
                frameBufferOutputFilename = currPass.FrameBuffers(i).GetResolvedPath( frameNumber )
                frameBufferOutputPath = GetFilePath( frameBufferOutputFilename )
                frameBufferOutputBaseName = GetFileBaseName( frameBufferOutputFilename )
                frameBufferOutputExtension = GetExtension( frameBufferOutputFilename )
                
                if isSingleRegionJob:
                    tilesInX = opSet.Parameters("RegionXNumeric").Value
                    tilesInY = opSet.Parameters("RegionYNumeric").Value
                    
                    curTile = 0
                    for y in range(0, tilesInY):
                        for x in range(0, tilesInX):
                            currTilePrefix = "_tile_%sx%s_%sx%s_" % (x+1,y+1,tilesInX,tilesInY)
                            tileFilename = frameBufferOutputPath + currTilePrefix + frameBufferOutputBaseName + frameBufferOutputExtension
                            submitInfoFile.write("\nOutputFilename" + str(outputIndex) + "Tile" + str(curTile) + "=" + tileFilename )                            
                            curTile = curTile + 1
                else:
                    frameBufferOutputFilename = frameBufferOutputPath + tilePrefix + frameBufferOutputBaseName + frameBufferOutputExtension
                    submitInfoFile.write("\nOutputFilename" + str(outputIndex) + "=" + frameBufferOutputFilename )
                    
                outputIndex = outputIndex + 1
    
    submitInfoFile.write("\nEnableAutoTimeout=" + str(opSet.Parameters("AutoTimeout").Value))
    submitInfoFile.write("\nOnJobComplete=" + opSet.Parameters( "OnCompleteComboBox" ).Value)
    
    if isSingleRegionJob:
        submitInfoFile.write("\nTileJob=True" )
        submitInfoFile.write("\nTileJobFrame=" + str(opSet.Parameters("RegionSingleFrameBox").Value))
        submitInfoFile.write("\nTileJobTilesInX=" + str(opSet.Parameters("RegionXNumeric").Value))
        submitInfoFile.write("\nTileJobTilesInY=" + str(opSet.Parameters("RegionYNumeric").Value))
    else:
        submitInfoFile.write("\nFrames=" + frameStr)
    
    if(opSet.Parameters("SubmitSuspended").Value):
        submitInfoFile.write("\nInitialStatus=Suspended")
    
    #Movie renders can only be done as one large chunk on one machine.
    if(not GetCreateMovie(currPass)):
        submitInfoFile.write("\nMachineLimit="+str(opSet.Parameters("MachineLimitNumeric").Value))
        if not isSingleRegionJob:
            submitInfoFile.write("\nChunkSize="+str(opSet.Parameters("ChunkSizeNumeric").Value))
    else:
        submitInfoFile.write("\nMachineLimit=1")
        submitInfoFile.write("\nChunkSize=100000")
    
    regionRendering = bool( opSet.Parameters( "RegionRenderingCheckBox" ).Value )
    dependentAssembly = bool( opSet.Parameters( "RegionAssemblyJobCheckBox" ).Value )

    groupBatch = False
    if regionRendering and dependentAssembly:
        groupBatch = True

    if not regionRendering and (allPasses or len(passesListValue) > 0):
        groupBatch = True
        batchName = opSet.Parameters("JobNameTextBox").Value
    
    if not( regionRendering and dependentAssembly ):
        groupBatch = WriteIntegrationSettings( submitInfoFile, groupBatch, opSet )

    if groupBatch:
        submitInfoFile.write( "\nBatchName=%s" % ( batchName ) )
        
    submitInfoFile.close()

    return submitInfoFilename
  
#Creates the plugin info file.
def CreatePluginInfoFile(opSet, currPass, scene, jobInfoFilename, tilePrefix, scenefile):
    Application.LogMessage("Creating Plugin Info")
    output=""
    isFxTreeJob = opSet.Parameters("FxTreeCheckBox").Value
    
    #Create the job info file
    jobInfoFile = open(jobInfoFilename, "w")
    
    jobInfoFile.write("Version=" + GetVersion())
    jobInfoFile.write("\nThreads=" + str(opSet.Parameters("ThreadsNumeric").Value))
    jobInfoFile.write("\nBuild=" + opSet.Parameters("BuildComboBox").Value)
    jobInfoFile.write("\nLocalRendering=" + str(opSet.Parameters("LocalRenderingBox").Value))
    jobInfoFile.write("\nSkipBatchLicense=" + str(opSet.Parameters("SkipBatchLicenseBox").Value))
    
    workgroupFolder = (opSet.Parameters("WorkgroupFolder").Value).strip()
    if(len(workgroupFolder)>0):
        jobInfoFile.write("\nWorkgroup=" + workgroupFolder)
    
    if (not opSet.Parameters("SubmitXsiSceneCheckBox").Value):
        jobInfoFile.write("\nSceneFile=" + scenefile)
    
    if(isFxTreeJob):
        jobInfoFile.write("\nFxTreeRender=True")
        jobInfoFile.write("\nFxTreeOutputNode=" + opSet.Parameters("FxTreeComboBox").Value)
        jobInfoFile.write("\nFxTreeFrameOffset=" + str(opSet.Parameters("FxTreeFrameOffsetNumeric").Value))
        fxTreeOutputNode = opSet.Parameters("FxTreeComboBox").Value
        jobInfoFile.write("\nFxTreeOutputFile=" + GetFxOutputFilename(fxTreeOutputNode))
    else:
        jobInfoFile.write("\nFxTreeRender=False")
    
        width=GetOutputWidth(currPass)
        height=GetOutputHeight(currPass)
        
        motionBlur=GetMotionBlur(currPass)
        skipFrames=GetSkipExistingFrames(currPass)
        
        jobInfoFile.write("\nPass=" + currPass.Name)
        jobInfoFile.write("\nWidth=" + str(width))
        jobInfoFile.write("\nHeight=" + str(height))
        
        jobInfoFile.write("\nMotionBlur=" + str(motionBlur))
        jobInfoFile.write("\nSkipFrames=" + str(skipFrames))
    
        if(IsMentalRay(currPass)):
            jobInfoFile.write("\nRenderer=Mental Ray")
            jobInfoFile.write("\nSampleMin=" + str(GetMinSamplingLevel(currPass)))
            jobInfoFile.write("\nSampleMax=" + str(GetMaxSamplingLevel(currPass)))
            jobInfoFile.write("\nFilter=" + GetSamplesFilterType(currPass))
            
            jobInfoFile.write("\nSampleJitter=" + str(GetSamplesJitter(currPass)))
            
        if(IsRedshift(currPass)):
            jobInfoFile.write("\nRenderer=Redshift")
            jobInfoFile.write("\nRedshiftGPUsPerTask=" + str(opSet.Parameters("RedshiftGPUsPerTaskNumeric").Value))
            jobInfoFile.write("\nRedshiftGPUsSelectDevices=" + str(opSet.Parameters("RedshiftGPUsSelectDevicesBox").Value))

        if(IsArnold(currPass)):
            jobInfoFile.write("\nRenderer=Arnold")

        if(IsVray(currPass)):
            jobInfoFile.write("\nRenderer=Vray")        
            
        if(bool(opSet.Parameters("RegionRenderingCheckBox").Value)):
            jobInfoFile.write("\nRegionRendering=True")
            if(not bool(opSet.Parameters("RegionSingleJobCheckBox").Value)):
                jobInfoFile.write("\nRegionLeft=" + str(opSet.Parameters("RegionLeft").Value))
                jobInfoFile.write("\nRegionTop=" + str(opSet.Parameters("RegionTop").Value))
                jobInfoFile.write("\nRegionRight=" + str(opSet.Parameters("RegionRight").Value))
                jobInfoFile.write("\nRegionBottom=" + str(opSet.Parameters("RegionBottom").Value))
                jobInfoFile.write("\nTilePrefix=" + tilePrefix)
            else:
                #jobInfoFile.write("\nRegionSingleJob=True")
                #jobInfoFile.write("\nRegionSingleFrame=" + str(opSet.Parameters("RegionSingleFrameBox").Value))
                jobInfoFile.write("\n" + opSet.Parameters("RegionSingleLeft").Value)
                jobInfoFile.write("\n" + opSet.Parameters("RegionSingleTop").Value)
                jobInfoFile.write("\n" + opSet.Parameters("RegionSingleRight").Value)
                jobInfoFile.write("\n" + opSet.Parameters("RegionSingleBottom").Value)
                jobInfoFile.write("\n" + opSet.Parameters("RegionSinglePrefix").Value)
        
        for i in range( len(currPass.FrameBuffers) ):
            jobInfoFile.write("\nFrameBuffer" + str(i) + "=" + currPass.FrameBuffers(i).Name)
        
        jobInfoFile.write("\nFilePath=" + GetPluginOutputFolder())
        
    jobInfoFile.close()

    return jobInfoFilename

def SubmitDeadlineJob(opSet, scene, currPass):
    paddingRegex = re.compile("#+")
    
    Application.LogMessage("SubmitSoftimageToDeadline")
    scenefile = scene.Filename.Value
    
    isFxTreeJob = opSet.Parameters("FxTreeCheckBox").Value
    fxTreeOutputNode = opSet.Parameters("FxTreeComboBox").Value
    
    temp = GetTempFolder()
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        submitInfoFilename = temp + "\\softimage_submit_info"
        jobInfoFilename = temp + "\\softimage_job_info"
    else:
        submitInfoFilename = temp + "/softimage_submit_info"
        jobInfoFilename = temp + "/softimage_job_info"
    
    jobName = opSet.Parameters("JobNameTextBox").Value
    
    if(isFxTreeJob):
        jobName = jobName + " _ " + fxTreeOutputNode
    else:
        jobName = jobName + " - " + currPass.Name
        
    successes=0
    failures=0
    
    #Set up the command line
    startupinfo = None
    if os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    deadlineCommand = GetDeadlineCommand()
    commandLine = "\"" + deadlineCommand + "\" \"" + submitInfoFilename + "\" \"" + jobInfoFilename + "\""
    
    if(opSet.Parameters("SubmitXsiSceneCheckBox").Value):
        commandLine = commandLine + " \"" + scenefile +"\""

    if( not isFxTreeJob and bool( opSet.Parameters("RegionRenderingCheckBox" ).Value ) ):
        jobIds = []
        tilesInX = opSet.Parameters("RegionXNumeric").Value
        tilesInY = opSet.Parameters("RegionYNumeric").Value
        
        deltaX = Floor(float(GetOutputWidth(currPass))/float(tilesInX))
        deltaY = Floor(float(GetOutputHeight(currPass))/float(tilesInY))
        
        singleTileJob = bool(opSet.Parameters("RegionSingleJobCheckBox").Value)
        
        currTile=0
        totalTiles=tilesInX*tilesInY
        
        progressBar = CreateProgressBar( "Tile Job Submission", totalTiles, False )
        
        if( not singleTileJob ):
            currJob = 0
            for y in range(1,tilesInY+1):
                for x in range(1,tilesInX+1):
                    submitInfoFilenameUnique = "%s_%d.job" % ( submitInfoFilename, currJob )
                    jobInfoFilenameUnique = "%s_%d.job" % ( jobInfoFilename, currJob )

                    currTile+=1
                    newY = tilesInY - y + 1
                    
                    regionLeft = max(deltaX * (x-1) -1, 0)
                    regionRight = deltaX + 1
                    regionTop = deltaY + 1
                    regionBottom = max(deltaY * (newY - 1) -1, 0)
                    
                    #if its the last tile in a row or column, make sure any missing/additional pixels (due to rounding of deltaX and deltaY) are accounted for
                    if(y == 1):
                        extraPixels = GetOutputHeight(currPass) - (regionBottom + regionTop)
                        regionTop += extraPixels
                    if(x == tilesInX):
                        extraPixels = GetOutputWidth(currPass) - (regionLeft + regionRight)
                        regionRight += extraPixels
                    
                    opSet.Parameters("RegionLeft").Value = regionLeft
                    opSet.Parameters("RegionRight").Value = regionRight
                    opSet.Parameters("RegionTop").Value = regionTop
                    opSet.Parameters("RegionBottom").Value= regionBottom
                    
                    currJobName = jobName + " (TILE " + str(currTile) + " : " + str(x) + "x" + str(y) + " of " + str(tilesInX) + "x" + str(tilesInY) + ")"
                    tilePrefix = "_tile_" + str(x) + "x" + str(y) + "_" + str(tilesInX) + "x" + str(tilesInY) + "_"
                    
                    progressBar.StatusText = "Submitting Tile Job " + str(currTile) + " of " + str(totalTiles) + " for pass \"" + currPass.Name + "\"..."
                    Application.LogMessage("Submitting Tile Job " + str(currTile) + " of " + str(totalTiles) + " for pass \"" + currPass.Name + "\"")
                    
                    submitInfoFilenameUnique = CreateSubmissionInfoFile(opSet,currPass,submitInfoFilenameUnique,tilePrefix,currJobName,jobName)
                    jobInfoFilenameUnique = CreatePluginInfoFile(opSet,currPass,scene,jobInfoFilenameUnique,tilePrefix,scenefile)
                    
                    arguments = []
                    arguments.append( submitInfoFilenameUnique )
                    arguments.append( jobInfoFilenameUnique )
    
                    output = CallDeadlineCommand( arguments )

                    jobId = ""
                    tempOutput = output.replace( "\r", "" )
                    for line in tempOutput.splitlines():
                        if line.startswith( "JobID=" ):
                            jobId = line.replace( "JobID=", "" )
                            break

                    jobIds.append( jobId )
                    
                    Application.LogMessage(output)
                    successRegex = re.compile("Result=Success")
                    if(re.search(successRegex,output)):
                        successes+=1
                    else:
                        failures+=1
                    
                    progressBar.Increment()

                    currJob+=1
                        
            output = "Submission Results\n\nSuccesses: " + str(successes) + "\nFailures: " + str(failures) + "\n\nSee script log for more details"
        else:
            submitInfoFilename = "%s.job" % submitInfoFilename
            jobInfoFilename = "%s.job" % jobInfoFilename

            opSet.Parameters("RegionSingleLeft").Value = ""
            opSet.Parameters("RegionSingleRight").Value = ""
            opSet.Parameters("RegionSingleTop").Value = ""
            opSet.Parameters("RegionSingleBottom").Value = ""
            opSet.Parameters("RegionSinglePrefix").Value = ""
            
            taskLimit = GetJobTaskLimit()
            
            if tilesInX * tilesInY > int( taskLimit ):
                Application.LogMessage("Unable to submit job with " + (str(tilesInX * tilesInY)) + " tasks.  Task Count exceeded Job Task Limit of "+str(taskLimit))
                return
            
            for y in range(1,tilesInY+1):
                for x in range(1,tilesInX+1):
                    newY = tilesInY - y + 1

                    regionLeft = max(deltaX * (x-1) -1, 0)
                    regionRight = deltaX + 1
                    regionTop = deltaY + 1
                    regionBottom = max(deltaY * (newY - 1) -1, 0)
                    
                    #if its the last tile in a row or column, make sure any missing/additional pixels (due to rounding of deltaX and deltaY) are accounted for
                    if(y == 1):
                        extraPixels = GetOutputHeight(currPass) - (regionBottom + regionTop)
                        regionTop += extraPixels
                    if(x == tilesInX):
                        extraPixels = GetOutputWidth(currPass) - (regionLeft + regionRight)
                        regionRight += extraPixels                            
                    
                    opSet.Parameters("RegionSingleLeft").Value += "RegionLeft" + str(currTile) + "=" + str(regionLeft) + "\n"
                    opSet.Parameters("RegionSingleRight").Value += "RegionRight" + str(currTile) + "=" + str(regionRight) + "\n"
                    opSet.Parameters("RegionSingleTop").Value += "RegionTop" + str(currTile) + "=" + str(regionTop) + "\n"
                    opSet.Parameters("RegionSingleBottom").Value += "RegionBottom" + str(currTile) + "=" + str(regionBottom) + "\n"
                    opSet.Parameters("RegionSinglePrefix").Value += "RegionPrefix" + str(currTile) + "=" + "_tile_" + str(x) + "x" + str(y) + "_" + str(tilesInX) + "x" + str(tilesInY) + "_" + "\n"
                    
                    currTile+=1
            
            opSet.Parameters("RegionSingleTiles").Value = currTile
            
            
            jobCount = 1
            if bool(opSet.Parameters("RegionAssemblyJobCheckBox").Value):
                jobCount = jobCount + len(currPass.FrameBuffers)
            
            progressBar = CreateProgressBar( "Tile Job Submission", jobCount, False )
            
            progressBar.StatusText = "Submitting Single Tile Job for pass \"" + currPass.Name + "\"..."
            Application.LogMessage("Submitting Single Tile Job for pass \"" + currPass.Name + "\"")
            
            frameNumber = str(opSet.Parameters("RegionSingleFrameBox").Value)
            submitInfoFilename = CreateSubmissionInfoFile(opSet,currPass,submitInfoFilename,"",jobName+" (Frame " + frameNumber + " - "+str(currTile)+" Tiles)",jobName)
            jobInfoFilename = CreatePluginInfoFile(opSet,currPass,scene,jobInfoFilename,"",scenefile)

            arguments = []
            arguments.append( submitInfoFilename )
            arguments.append( jobInfoFilename )
            
            output = CallDeadlineCommand( arguments )

            jobId = ""
            tempOutput = output.replace( "\r", "" )
            for line in tempOutput.splitlines():
                if line.startswith( "JobID=" ):
                    jobId = line.replace( "JobID=", "" )
                    break

            jobIds.append( jobId )
            
            Application.LogMessage(output)
            successRegex = re.compile("Result=Success")

            if(re.search(successRegex,output)):
                successes+=1
            else:
                failures+=1
                
            progressBar.Increment()

            if successes + failures > 4:
                output = "Submission Results\n\nSuccesses: " + str(successes) + "\nFailures: " + str(failures) + "\n\nSee script log for more details"

        if bool( opSet.Parameters( "RegionAssemblyJobCheckBox" ).Value ):
            errorOnMissing= bool(opSet.Parameters("RegionErrorOnMissingCheckBox").Value)
            configFiles = []
            startFrame = 1
            endFrame = 1

            if singleTileJob:
                renderFrames = xrange( int( frameNumber ), int( frameNumber ) + 1 )
            else:
                frameNumber = ""
                frames = GetFrameRange( currPass ).split( "-" )
                startFrame = frames[0]
                renderFrames = xrange( int( startFrame ), int( startFrame ) + 1 )
                if len( frames ) > 1:
                    endFrame = frames[1]
                    renderFrames = xrange( int( startFrame ), int( endFrame ) + 1 )

            for i in range( len( currPass.FrameBuffers ) ):
                if bool( Application.ExecuteCommand( "GetValue",[currPass.FrameBuffers( i ).FullName + ".Enabled"] ) ):
                    frameBufferOutputFilename = currPass.FrameBuffers( i ).GetResolvedPath( frameNumber )
                    frameBufferOutputPath = GetFilePath( frameBufferOutputFilename )
                    frameBufferOutputBaseName = GetFileBaseName( frameBufferOutputFilename )
                    frameBufferOutputExtension = GetExtension( frameBufferOutputFilename )
                    
                    outputTileFilename = frameBufferOutputFilename
                    inputImageFilename = frameBufferOutputPath + "_tile_1x1_" + str(tilesInX) + "x" + str(tilesInY) + "_" + frameBufferOutputBaseName + frameBufferOutputExtension
                    
                    currentDateTime = datetime.datetime.now()

                    tileSubmitInfoFilename = temp + "/draft_tile_submit_info.job"
                    tileJobInfoFilename = temp + "/tile_job_info.job"

                    if Application.Platform == "Win32" or Application.Platform == "Win64":
                        tileJobInfoFilename = tileJobInfoFilename.replace( "/", "\\" )
                        tileSubmitInfoFilename = tileSubmitInfoFilename.replace( "/", "\\" )

                    tileSubmitInfo = open( tileSubmitInfoFilename,"w" )

                    #Create the submit info file
                    tileSubmitInfo.write("Plugin=DraftTileAssembler")
                    tileSubmitInfo.write("\nName=" + jobName + " - " + currPass.FrameBuffers(i).Name + " (Frame " + frameNumber + ") - Tile Assembly Job")
                    tileSubmitInfo.write("\nBatchName=" + jobName)
                    tileSubmitInfo.write("\nComment=" + opSet.Parameters( "CommentTextBox" ).Value)
                    tileSubmitInfo.write("\nDepartment=" + opSet.Parameters( "DepartmentTextBox" ).Value)
                    tileSubmitInfo.write("\nGroup=" + opSet.Parameters( "GroupComboBox" ).Value)
                    tileSubmitInfo.write("\nPool=" + opSet.Parameters( "PoolComboBox" ).Value)
                    tileSubmitInfo.write("\nSecondaryPool=" + opSet.Parameters( "SecondaryPoolComboBox" ).Value)
                    tileSubmitInfo.write("\nPriority=" + str(opSet.Parameters( "PriorityNumeric" ).Value))
                    tileSubmitInfo.write("\nConcurrentTasks=" + str(opSet.Parameters( "ConcurrentTasksNumeric" ).Value))
                    tileSubmitInfo.write("\nJobDependencies=" + ",".join( jobIds ) )
                    tileSubmitInfo.write("\nOutputFilename0=" + outputTileFilename)
                    tileSubmitInfo.write("\nOnJobComplete=" + opSet.Parameters( "OnCompleteComboBox" ).Value)
                    tileSubmitInfo.write("\nChunkSize=1")
                    tileSubmitInfo.write("\nMachineLimit=1")

                    if singleTileJob:
                        tileSubmitInfo.write( "\nFrames=%s" % str( opSet.Parameters( "RegionSingleFrameBox" ).Value ) )
                    else:
                        tileSubmitInfo.write( "\nFrames=%s" % opSet.Parameters( "Frames" ).Value )

                    WriteIntegrationSettings( tileSubmitInfo, True, opSet )

                    tileSubmitInfo.close()

                    tileJobInfoFile = open( tileJobInfoFilename, "w" )

                    tileJobInfoFile.write( "ErrorOnMissing=%s" % errorOnMissing )
                    tileJobInfoFile.write("\nCleanupTiles=" + str( opSet.Parameters( "RegionCleanupJobCheckBox" ).Value ) )
                    tileJobInfoFile.write( "\nMultipleConfigFiles=True" )
                    
                    if not os.path.exists(frameBufferOutputPath):
                        try:
                            os.makedirs( frameBufferOutputPath )
                        except:
                            print("Failed to create output " +frameBufferOutputPath)
                            
                    for frame in renderFrames:
                        tileJobConfigFilename = frameBufferOutputPath + "/"+frameBufferOutputBaseName+"_config_{0:%y}_{0:%m}_{0:%d}_{0:%H}_{0:%M}_{0:%S}.txt".format( currentDateTime )

                        #Submitting as multiple jobs places padding into the file name, should remove if it's there
                        paddedFrame = str(frame)
                        foundPadding = paddingRegex.search( tileJobConfigFilename )
                        if foundPadding is not None:
                            lenPadding = len( foundPadding.group(0) )
                            while len( paddedFrame ) < lenPadding:
                                paddedFrame = "0"+paddedFrame
                        
                        
                        tileJobConfigFilename = paddingRegex.sub( str( paddedFrame ), tileJobConfigFilename )
                        tileJobConfigFile = open(tileJobConfigFilename, "w")

                        tileJobConfigFile.write("")
                        tileJobConfigFile.write( "ImageFileName=%s" % ( paddingRegex.sub( str( paddedFrame ),outputTileFilename ) ) )
                        tileJobConfigFile.write("\nTileCount=%s" % str(totalTiles))
                        if( IsMentalRay( currPass ) ):
                            tileJobConfigFile.write("\nTilesCropped=False")
                        else:
                            tileJobConfigFile.write("\nTilesCropped=True")
                        curTile = 0
                        width=GetOutputWidth(currPass)
                        height=GetOutputHeight(currPass)
                        tileJobConfigFile.write( "\nImageWidth=%s" % width )
                        tileJobConfigFile.write( "\nImageHeight=%s" % height )
                        for x in range(0, tilesInX):
                            for y in range(0, tilesInY):
                                newY = tilesInY - y
                                left = max(deltaX * (x), 0)
                                bottom = max(deltaY * (newY - 1), 0)
                                
                                tilePrefix = "_tile_%sx%s_%sx%s_" % (x+1,y+1,tilesInX,tilesInY)
                                tileFilename = frameBufferOutputPath + tilePrefix + frameBufferOutputBaseName + frameBufferOutputExtension
                                tileJobConfigFile.write( "\nTile%sFileName=%s" % ( curTile, paddingRegex.sub( str( paddedFrame ), tileFilename ) ) )
                                tileJobConfigFile.write( "\nTile%sX=%s" % (curTile,left) )
                                tileJobConfigFile.write( "\nTile%sY=%s" % (curTile,bottom) )
                                tileJobConfigFile.write( "\nTile%sHeight=%s" % (curTile, deltaY ))
                                tileJobConfigFile.write( "\nTile%sWidth=%s" % (curTile, deltaX ))
                                curTile = curTile + 1
                        
                        tileJobConfigFile.close()

                        configFiles.append( tileJobConfigFilename )
                    
                    tileJobInfoFile.close()
                    
                    statusMessage = "Submitting Dependent Assembly Job " + str(i+1) + " of " + str(len(currPass.FrameBuffers)) + " for pass \"" + currPass.Name + "\""
                    progressBar.StatusText = "%s..." % statusMessage
                    Application.LogMessage( statusMessage )
                    
                    arguments = []
                    arguments.append( tileSubmitInfoFilename )
                    arguments.append( tileJobInfoFilename )
                    arguments.extend( configFiles )

                    output += "\n\n" + CallDeadlineCommand( arguments )
                    
                    Application.LogMessage( output )
                    successRegex = re.compile("Result=Success")
                    
                    if(re.search(successRegex,tempOutput)):
                        successes+=1
                    else:
                        failures+=1
                    
                    progressBar.Increment()

        progressBar.Visible = False
    else:
        progressBar = CreateProgressBar( "Job Submission", 4, False )    
        
        if(isFxTreeJob):
            progressBar.StatusText = "Submitting FxTree Job..."
            Application.LogMessage("Submitting FxTree Job")
        else:
            progressBar.StatusText = "Submitting Job For Pass \"" + currPass.Name + "\""
            Application.LogMessage("Submitting Job For Pass \"" + currPass.Name + "\"")
        
        progressBar.Increment()
        CreateSubmissionInfoFile(opSet,currPass,submitInfoFilename,"",jobName,jobName)
        
        progressBar.Increment()
        CreatePluginInfoFile(opSet,currPass,scene,jobInfoFilename,"",scenefile)
        
        progressBar.Increment()        
        
        #Submit the job to Deadlineline (wait for return)
        #output = os.popen(commandLine)
        #output = output.read()
        
        # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
        proc = subprocess.Popen(commandLine, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        proc.stdin.close()
        proc.stderr.close()
        
        output = proc.stdout.read()
        
        progressBar.Increment()
        progressBar.Visible = False
        
    return output

def GetJobTaskLimit():
    deadlineCommand = GetDeadlineCommand()
    
    startupinfo = None
    if os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen("\"" + deadlineCommand + "\" -getjobtasklimit", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    proc.stdin.close()
    proc.stderr.close()
    
    root = proc.stdout.read()
    root = root.replace("\n","").replace("\r","")
    return root
    
# Get The Repository Path using DeadlineCommand
def GetRepositoryPath(folder=None, filePath=False):
    deadlineCommand = GetDeadlineCommand()
    
    startupinfo = None
    if os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    

    func = '-getrepositorypath'
    if filePath:
        func = '-getrepositoryfilepath'
    
    if folder == None:
        proc = subprocess.Popen([deadlineCommand, func ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    else:
        proc = subprocess.Popen([deadlineCommand, func, folder], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
   
    proc.stdin.close()
    proc.stderr.close()
    
    path = proc.stdout.read()
    path = path.replace("\n","").replace("\r","")
    return path

def GetTempFolder():
    if(Application.Platform == "Win32" or Application.Platform == "Win64"):
        return os.getenv("Temp")
    else:
        return "/tmp"

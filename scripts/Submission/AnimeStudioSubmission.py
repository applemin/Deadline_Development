from __future__ import print_function
from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

import traceback
import json

from zipfile import *

# For Integration UI
import imp
import os
imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

imp.load_source( 'JobOptionsUI', os.path.join( RepositoryUtils.GetRepositoryPath("submission/Common/Main", True), "JobOptionsUI.py" ) )
import JobOptionsUI


########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None

ProjectManagementOptions = ["Shotgun","FTrack","NIM"]
DraftRequested = True
jobOptions_dialog = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    global jobOptions_dialog
    
    scriptDialog = DeadlineScriptDialog()

    scriptDialog.SetTitle( "Submit Anime Studio/Moho Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'AnimeStudio' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    
    jobOptions_dialog = JobOptionsUI.JobOptionsDialog()
    
    scriptDialog.AddScriptControl( jobOptions_dialog )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Anime Studio/Moho Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Anime Studio/Moho File", 1, 0, "The scene file to be rendered.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Anime Studio/Moho Files (*.anme *.anime *.animeproj *.moho *.mohoproj);;All Files (*)", 1, 1, colSpan=2 )
    sceneBox.ValueModified.connect(SceneBoxChanged)

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output File", 2, 0,  "The output path to render to.", False )
    outputBox = scriptDialog.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "", "JPEG (*.jpg);;BMP (*.bmp);;Targa (*.tga);;PNG (*.png);;PSD (*.psd);;MP4 (*.mp4);;iPhone/iPad Movie (*.m4v);;AVI (*.avi);;QuickTime Movie (*.mov);;Flash (*.swf);;Animated GIF (*.gif)", 2, 1, colSpan=2 )
    outputBox.ValueModified.connect(OutputBoxChanged)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 4, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddSelectionControlToGrid("FormatSuffixBox","CheckBoxControl",False,"Add Format Suffix",4, 2, "If this option is enabled, the format name will be appended to the file name of the output path. Version 9.5 and later.")

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 5, 0 , "The version of Anime Studio (Moho) to render with.", False)
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "10", ("8","9","9.5","10","11","12"), 5, 1 )
    versionBox.ValueModified.connect(VersionChanged)
    scriptDialog.AddSelectionControlToGrid("SubmitSceneBox","CheckBoxControl",False,"Submit Anime Studio/Moho Scene File With Job", 5, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering.")
    
    scriptDialog.AddControlToGrid( "LayerCompLabel", "LabelControl", "Layer Comp", 6, 0 , "Render a specific layer comp, or select All to render all layer comps to separate files.", False)
    layerCompBox = scriptDialog.AddComboControlToGrid( "LayerCompBox", "ComboControl", "", ("","All"), 6, 1 )
    layerCompBox.ValueModified.connect(LayerCompChanged)
    
    enableFasterParsingBox = scriptDialog.AddSelectionControlToGrid("EnableFasterParsingBox","CheckBoxControl",False,"Enable Faster Scene File Parsing",6, 2, "If this option is enabled, a faster, but experimental, method is used to parse the scene file.")
    
    addLayerCompSuffixBox = scriptDialog.AddSelectionControlToGrid("AddLayerCompSuffixBox","CheckBoxControl",False,"Add Layer Comp Suffix",7, 2, "If this option is enabled, adds a layer comp suffix to the rendered file name(s).")
    createFolderForLayerCompsBox = scriptDialog.AddSelectionControlToGrid("CreateFolderForLayerCompsBox","CheckBoxControl",False,"Create Folder for Layer Comps",8, 2, "If this option is enabled, the rendered file(s) will be created in a subfolder of the output path. The subfolder's name will be the layer comp name.")
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Additional Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator6", "SeparatorControl", "Rendering Options", 0, 0, colSpan=2 )
    
    scriptDialog.AddSelectionControlToGrid("AntialiasedBox","CheckBoxControl",True,"Antialiased Edges", 1, 0, "Normally, Anime Studio/Moho renders your shapes with smoothed edges. Uncheck this box to turn this feature off.")
    scriptDialog.AddSelectionControlToGrid("ReducedParticlesBox","CheckBoxControl",False,"Reduced Particles",1, 1, "Some particle effects require hundreds of particles to achieve their effect. Check this box to render fewer particles. The effect may not look as good, but will render much faster if all you need is a preview.")

    scriptDialog.AddSelectionControlToGrid("ShapeEffectsBox","CheckBoxControl",True,"Apply Shape Effects", 2, 0, "If this box is unchecked, Anime Studio/Moho will skip shape effects like shading, texture fills, and gradients.")
    scriptDialog.AddSelectionControlToGrid("ExtraSmoothBox","CheckBoxControl",True,"Extra-smooth Images", 2, 1, "Renders image layers with a higher quality level. Exporting takes longer with this option on.")

    scriptDialog.AddSelectionControlToGrid("LayerEffectsBox","CheckBoxControl",True,"Apply Layer Effects", 3, 0, "If this box is unchecked, Anime Studio/Moho will skip layer effects like layer shadows and layer transparency.")
    scriptDialog.AddSelectionControlToGrid("NtscSafeColorsBox","CheckBoxControl",False,"Use NTSC-safe Colors", 3, 1, "Automatically limits colors to be NTSC safe. This is only an approximation - you should still do some testing to make sure your animation looks good on a TV monitor.")

    scriptDialog.AddSelectionControlToGrid("HalfSizeBox","CheckBoxControl",False,"Render At Half Dimensions", 4, 0, "Check this box to render a smaller version of your movie. This makes rendering faster if you just want a quick preview, and is useful for making smaller movies for the web.")
    scriptDialog.AddSelectionControlToGrid("NoPremultiplyBox","CheckBoxControl",False,"Do Not Premultiply Alpha Channel", 4, 1, "Useful if you plan to composite your Anime Studio/Moho animation with other elements in a video editing program.")

    scriptDialog.AddSelectionControlToGrid("HalfFrameRateBox","CheckBoxControl",False,"Render At Half Frame Rate", 5, 0, "Check this box to skip every other frame in the animation. This makes rendering faster, and results in smaller movie files.")
    #scriptDialog.AddSelectionControlToGrid("MultiThreadedBox","CheckBoxControl",True,"Enable Multi-threaded Rendering", 5, 1, "Enable multithreaded rendering.")
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "QTSeparator", "SeparatorControl", "QT Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "VideoCodecLabel", "LabelControl", "Video Codec (Optional)", 1, 0, "The video codec (leave blank to not specify one). Version 10 and later.", False )
    scriptDialog.AddControlToGrid( "VideoCodecBox", "TextControl", "", 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "QualityLabel", "LabelControl", "Quality", 2, 0, "The quality of the export. Version 10 and later. 0 = Minimum, 1 = Low, 2 = Normal, 3 = High, 4 = Max, 5 = Lossless", False)
    scriptDialog.AddComboControlToGrid( "QualityBox", "ComboControl", "3", ("0","1","2","3","4","5"), 2, 1, expand=False )

    scriptDialog.AddControlToGrid( "DepthLabel", "LabelControl", "Depth", 3, 0 , "The pixel depth of the export. Version 10 and later.", False)
    scriptDialog.AddComboControlToGrid( "DepthBox", "ComboControl", "24", ("24","32"), 3, 1, expand=False )
    
    scriptDialog.AddControlToGrid( "M4VSeparator", "SeparatorControl", "iPhone/iPad Movie Options", 4, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "M4VLabel", "LabelControl", "Format", 5, 0 , "The available formats for m4v movies.", False)
    scriptDialog.AddComboControlToGrid( "M4VBox", "ComboControl", "iPhone Movie (480x320)", ("iPhone Movie (480x320)", "iPhone 4 Movie (960x640)", "iPhone 5 Movie (1136x640)", "iPad Movie (1024x768)", "iPad HD Movie (1280x1024)"), 5, 1, expand=False )
    
    scriptDialog.AddControlToGrid( "AVISeparator", "SeparatorControl", "AVI Options", 6, 0, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "AVILabel", "LabelControl", "Format", 7, 0 , "The available formats for avi movies.", False)
    scriptDialog.AddComboControlToGrid( "AVIBox", "ComboControl", "AVI Movie", ("AVI Movie", "AVI Movie (DV) (720x480)", "AVI Movie (Uncompressed)"), 7, 1, expand=False )
    
    scriptDialog.AddControlToGrid( "SWFSeparator", "SeparatorControl", "SWF Options", 8, 0, colSpan=3 )
    scriptDialog.AddSelectionControlToGrid("VariableLineWidthsBox","CheckBoxControl",False,"Variable Line Widths", 9, 0, "Exports variable line widths to SWF.")
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "AnimeStudioMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ("SceneBox","FramesBox","ChunkSizeBox","VersionBox","OutputBox","SubmitSceneBox","AntialiasedBox", "ShapeEffectsBox", "LayerEffectsBox", "HalfSizeBox", "HalfFrameRateBox", "ReducedParticlesBox", "ExtraSmoothBox", "NtscSafeColorsBox", "NoPremultiplyBox", "VariableLineWidthsBox", "VideoCodecBox", "QualityBox", "DepthBox", "FormatSuffixBox", "M4VBox", "AVIBox", "MultiThreadedBox","EnableFasterParsingBox")
    settings.extend( jobOptions_dialog.getSettingsNames() )
    print(jobOptions_dialog.getSettingsNames())
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    SceneBoxChanged( None )
    OutputBoxChanged( None )
    VersionChanged( None )
        
    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "AnimeStudioSettings.ini" )

def SceneBoxChanged( *args ):
    global scriptDialog
    
    try:
        framesFound = False
        frames = ""
        layerCompNames = ["", "All"]
        sceneFile = scriptDialog.GetValue( "SceneBox" )
        alternateParseScene = scriptDialog.GetValue("EnableFasterParsingBox")
       
        if File.Exists( sceneFile ):
            
            if Path.GetExtension( sceneFile ).lower() == ".anime" or Path.GetExtension( sceneFile ).lower() == ".animeproj":
                
                #for faster method of parsing scene files(experimental)
                if alternateParseScene:
                    
                    if Path.GetExtension( sceneFile ).lower() == ".anime":
                        z = ZipFile(sceneFile)
                        fileStr = z.open("Project.animeproj").read()
                        z.close()
                    else:
                        fileStr = open(sceneFile).read()
                                    
                    target = '"start_frame":'
                    index = fileStr.find(target) + len(target)
                    end = index + fileStr[index:].find(',')
                    startFrame = fileStr[index:end]
                    target = '"end_frame":'
                    index = fileStr.find(target) + len(target)
                    end = index + fileStr[index:].find(',')
                    endFrame = fileStr[index:end]
                    frames = "%s-%s" % (startFrame, endFrame)
                    framesFound = True
                    
                    keys = ["comment","styles","rev_version","layers","major_version","version","project_data","created_date","animated_values","thumbnail","mime_type","metadata",]
                    index = fileStr.find('layercomps') - 1
                    end = len(fileStr)
                    for key in keys:
                        new = fileStr.find(key)
                        if new < index: continue
                        if new < end: end = new
                    
                    search = index              
                    while search < end and search != -1:
                        nextName = fileStr[search+1:].find('name') + 1
                        if nextName == -1:
                            break

                        search += nextName + 5 #len('name"')
                        search += fileStr[search:].find('"') + 1
                        searchEnd = search + fileStr[search:].find('"')
                        layerComp = fileStr[search:searchEnd]
                        if layerComp not in layerCompNames:
                            layerCompNames.append(layerComp)
                else:
                    # The .anime format is just a compressed .animeproj file, so we just need to grab Project.animeproj from the archive get its JSON.
                    if Path.GetExtension( sceneFile ).lower() == ".anime":
                        z = ZipFile(sceneFile, 'r', ZIP_DEFLATED)
                        f = z.open("Project.animeproj")
                        animeJson = json.load(f)
                        z.close()
                    else:
                        f = open(sceneFile)
                        animeJson = json.load(f)
                        f.close()
                    
                    if "project_data" in animeJson:
                        projectData = animeJson["project_data"]
                        frames = "%s-%s" % (projectData["start_frame"], projectData["end_frame"])
                        framesFound = True
                            
                    if "layercomps" in animeJson:
                        layerComps = animeJson["layercomps"]
                        for layerComp in layerComps:
                            layerCompName = layerComp["name"]
                            if layerCompName not in layerCompNames:
                                layerCompNames.append(layerCompName)
            else:
                framesRegex = Regex( "frame_range ([0-9]+) ([0-9]+)" )
                layerCompRegex = Regex( "name \"(.*)\"" )
                nextLineLayerName = False
                
                f = open( sceneFile )
                for currLine in f:
                    line = currLine.strip()
                    
                    # Look for the frame range if we don't have it already.
                    if not framesFound:
                        match = framesRegex.Match( line )
                        if match.Success:
                            frames = match.Groups[1].Value + "-" + match.Groups[2].Value
                            framesFound = True
                    
                    # Look for layer comp names.
                    if line == "### layer comp":
                        nextLineLayerName = True
                    elif nextLineLayerName:
                        match = layerCompRegex.Match( line )
                        if match.Success:
                            layerCompName = match.Groups[1].Value
                            if layerCompName not in layerCompNames:
                                layerCompNames.append(layerCompName)
                                
                        nextLineLayerName = False
                    
                    # We don't need anything after metadata.
                    if line == "### document metadata":
                        break
                    
                f.close()
                    
        if framesFound:
            scriptDialog.SetValue( "FramesBox", frames )
                
        scriptDialog.SetItems( "LayerCompBox", layerCompNames )
    
    except:
        print( "Error parsing scene file: " + traceback.format_exc() )

def OutputBoxChanged( *args ):
    global scriptDialog
    
    outputFile = scriptDialog.GetValue( "OutputBox" )
    version = float(scriptDialog.GetValue( "VersionBox" ))
    
    isFlash = IsFlash( outputFile )
    scriptDialog.SetEnabled( "SWFSeparator", isFlash )
    scriptDialog.SetEnabled( "VariableLineWidthsBox", isFlash )
    
    # These Qt options are only available in 10 and later.
    isQt = IsQt( outputFile ) and (version >= 10)
    scriptDialog.SetEnabled( "QTSeparator", isQt )
    scriptDialog.SetEnabled( "VideoCodecLabel", isQt )
    scriptDialog.SetEnabled( "VideoCodecBox", isQt )
    scriptDialog.SetEnabled( "QualityLabel", isQt )
    scriptDialog.SetEnabled( "QualityBox", isQt )
    scriptDialog.SetEnabled( "DepthLabel", isQt )
    scriptDialog.SetEnabled( "DepthBox", isQt )
    
    isM4v = IsM4V( outputFile )
    scriptDialog.SetEnabled( "M4VSeparator", isM4v )
    scriptDialog.SetEnabled( "M4VLabel", isM4v )
    scriptDialog.SetEnabled( "M4VBox", isM4v )
    
    isAvi = IsAVI( outputFile )
    scriptDialog.SetEnabled( "AVISeparator", isAvi )
    scriptDialog.SetEnabled( "AVILabel", isAvi )
    scriptDialog.SetEnabled( "AVIBox", isAvi )
    
    isMovie = IsMovie( outputFile )
    scriptDialog.SetEnabled( "ChunkSizeLabel", not isMovie )
    scriptDialog.SetEnabled( "ChunkSizeBox", not isMovie )

def VersionChanged( *args ):
    global scriptDialog
    
    outputFile = scriptDialog.GetValue( "OutputBox" )
    version = float(scriptDialog.GetValue( "VersionBox" ))
    layerComp = scriptDialog.GetValue( "LayerCompBox" )
    
    # This option is only available in 9.5 and later.
    scriptDialog.SetEnabled( "FormatSuffixBox", version >= 9.5 )
    
    # This option is only available in 10 and later.
    scriptDialog.SetEnabled( "LayerCompLabel", version >= 10 )
    scriptDialog.SetEnabled( "LayerCompBox", version >= 10 )
    
    # These Qt options are only available in 10 and later.
    isQt = IsQt( outputFile ) and (version >= 10)
    scriptDialog.SetEnabled( "QTSeparator", isQt )
    scriptDialog.SetEnabled( "VideoCodecLabel", isQt )
    scriptDialog.SetEnabled( "VideoCodecBox", isQt )
    scriptDialog.SetEnabled( "QualityLabel", isQt )
    scriptDialog.SetEnabled( "QualityBox", isQt )
    scriptDialog.SetEnabled( "DepthLabel", isQt )
    scriptDialog.SetEnabled( "DepthBox", isQt )
    
    # These extra options for layer comps are only available in 11 and later.
    layerCompOptionsEnabled = (version >= 11) and not (layerComp == "")
    scriptDialog.SetEnabled( "AddLayerCompSuffixBox", layerCompOptionsEnabled )
    scriptDialog.SetEnabled( "CreateFolderForLayerCompsBox", layerCompOptionsEnabled )

def LayerCompChanged( *args ):
    global scriptDialog
    
    version = float(scriptDialog.GetValue( "VersionBox" ))
    layerComp = scriptDialog.GetValue( "LayerCompBox" )
    
    # These extra options for layer comps are only available in 11 and later.
    layerCompOptionsEnabled = (version >= 11) and not (layerComp == "")
    scriptDialog.SetEnabled( "AddLayerCompSuffixBox", layerCompOptionsEnabled )
    scriptDialog.SetEnabled( "CreateFolderForLayerCompsBox", layerCompOptionsEnabled )
    
def IsMovie( outputFile ):
    return IsFlash( outputFile ) or IsQt( outputFile ) or IsAVI( outputFile ) or IsM4V( outputFile) or IsMP4( outputFile ) or IsGIF( outputFile )

def IsFlash( outputFile ):
    return outputFile.lower().endswith( ".swf" )

def IsQt( outputFile ):
    return outputFile.lower().endswith( ".mov" )

def IsM4V( outputFile ):
    return outputFile.lower().endswith( ".m4v" )

def IsAVI( outputFile ):
    return outputFile.lower().endswith( ".avi" )

def IsMP4( outputFile ):
    return outputFile.lower().endswith( ".mp4" )

def IsGIF( outputFile ):
    return outputFile.lower().endswith( ".gif" )
    
def GetOutputFormat( outputFile ):
    global scriptDialog
    
    version = float(scriptDialog.GetValue( "VersionBox" ))
    
    # Supported formats: JPEG, TGA, BMP, PNG, PSD, QT, SWF and GIF (Version 11 and beyond)
    if outputFile.lower().endswith( ".jpg" ):
        return "JPEG"
    if outputFile.lower().endswith( ".tga" ):
        return "TGA"
    if outputFile.lower().endswith( ".bmp" ):
        return "BMP"
    if outputFile.lower().endswith( ".png" ):
        return "PNG"
    if outputFile.lower().endswith( ".psd" ):
        return "PSD"
    if outputFile.lower().endswith( ".mp4" ):
        return "MP4 (H.264-AAC)"
    if outputFile.lower().endswith( ".m4v" ):
        return scriptDialog.GetValue( "M4VBox" )
    if outputFile.lower().endswith( ".avi" ):
        return scriptDialog.GetValue( "AVIBox" )
    if outputFile.lower().endswith( ".mov" ):
        return "QT"
    if outputFile.lower().endswith( ".swf" ):
        return "SWF"
    if (version >= 11) and outputFile.lower().endswith( ".gif" ):
        return "Animated GIF"
    
    return "UNKNOWN"

def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog
    
    versionStr = scriptDialog.GetValue( "VersionBox" )
    version = float(versionStr)
    
    # Check if Anime Studio files exist.
    sceneFile = scriptDialog.GetValue( "SceneBox" ).strip()
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "The Anime Studio/Moho file %s does not exist" % sceneFile, "Error" )
        return
    elif (not scriptDialog.GetValue("SubmitSceneBox") and PathUtils.IsPathLocal(sceneFile)):
        result = scriptDialog.ShowMessageBox( "The Anime Studio/Moho file %s is local and is not being submitted with the job. Are you sure you want to continue?" % sceneFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    # Check output file
    outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
    if len(outputFile) == 0:
        scriptDialog.ShowMessageBox( "Please specify an output file.", "Error" )
        return
    if(not Directory.Exists(Path.GetDirectoryName(outputFile))):
            scriptDialog.ShowMessageBox( "The directory of the output file %s does not exist." % Path.GetDirectoryName(outputFile), "Error" )
            return
    elif( PathUtils.IsPathLocal(outputFile) ):
        result = scriptDialog.ShowMessageBox( "The output file %s is local. Are you sure you want to continue?" % outputFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    outputFormat = GetOutputFormat( outputFile )
    if outputFormat == "UNKNOWN":
        if version < 11:
            validFormatsStr = "jpg, bmp, tga, png, psd, mov, or swf"
        else:
            validFormatsStr = "jpg, bmp, tga, png, psd, mov, swf, or gif"
            
        scriptDialog.ShowMessageBox( "The output format is not supported. Valid formats are %s." % validFormatsStr, "Error" )
        return
    
    
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( outputFile ):
        return

    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return
    
    jobName = scriptDialog.GetValue( "NameBox" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "anime_studio_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=AnimeStudio" )
    writer.WriteLine( "Name=%s" % jobName )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
    writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
    writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "ConcurrentTasksBox" ) )
    writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
    
    writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
    if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    
    writer.WriteLine( "Frames=%s" % frames )
    if IsMovie( outputFile ):
        writer.WriteLine( "ChunkSize=100000" )
    else:
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )

    tempOutputFiles = []

    tempOutputFile = outputFile
    directory = Path.GetDirectoryName( tempOutputFile )
    prefix = Path.GetFileNameWithoutExtension( tempOutputFile )
    extension = Path.GetExtension( tempOutputFile )
    
    # If version is 10 or greater, need to see if All layer comps are being rendered and collect all the comp outputs accordingly.
    if version >= 10 and scriptDialog.GetValue("LayerCompBox") == "All":
        addLayerCompSuffix = (version < 11) or scriptDialog.GetValue("AddLayerCompSuffixBox")
        createFolderForLayerComps = (version >= 11) and scriptDialog.GetValue("CreateFolderForLayerCompsBox")
        
        layerComps =  scriptDialog.GetItems( "LayerCompBox" )
        for layerComp in layerComps:
            if layerComp != "" and layerComp != "All":
                if addLayerCompSuffix:
                    suffix = "-" + layerComp
                else:
                    suffix = ""
                    
                if createFolderForLayerComps:
                    outputDirectory = Path.Combine( directory, layerComp )
                else:
                    outputDirectory = directory
            
                tempLayerOutputFile = Path.Combine( outputDirectory, prefix + suffix + extension )
                tempOutputFiles.append(tempLayerOutputFile)
    else:
        outputDirectory = directory
        suffix = ""
        if (version >= 11) and scriptDialog.GetValue("LayerCompBox") != "":
            layerComp = scriptDialog.GetValue("LayerCompBox")
            
            if scriptDialog.GetValue("AddLayerCompSuffixBox"):
                suffix = "-" + layerComp
            if scriptDialog.GetValue("CreateFolderForLayerCompsBox"):
                outputDirectory = Path.Combine( directory, layerComp )
    
        tempOutputFiles.append( Path.Combine( outputDirectory, prefix + suffix + extension ) )
    
    outputIndex = 0
    for tempOutputFile in tempOutputFiles:
        currOutputFile = tempOutputFile
        
        # If version 9.5 or greater, check if we need to add the format suffix.
        if version >= 9.5 and scriptDialog.GetValue("FormatSuffixBox"):
            directory = Path.GetDirectoryName( currOutputFile )
            prefix = Path.GetFileNameWithoutExtension( currOutputFile )
            extension = Path.GetExtension( currOutputFile )
            currOutputFile = Path.Combine( directory, prefix + "-" + outputFormat + extension )
    
        if not IsMovie( currOutputFile ):
            directory = Path.GetDirectoryName( currOutputFile )
            prefix = Path.GetFileNameWithoutExtension( currOutputFile )
            extension = Path.GetExtension( currOutputFile )
            padding = "#####"
            if version > 8:
                padding = "_#####"
            currOutputFile = Path.Combine( directory, prefix + padding + extension )
        
        writer.WriteLine( "OutputFilename%s=%s" % (outputIndex,currOutputFile) )
        outputIndex = outputIndex + 1
    
    # Integration
    extraKVPIndex = 0
    groupBatch = False
    
    if integration_dialog.IntegrationProcessingRequested():
        extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
        groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()
        
    if groupBatch:
        writer.WriteLine( "BatchName=%s\n" % ( jobName ) ) 
    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "anime_studio_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    if(not scriptDialog.GetValue("SubmitSceneBox")):
        writer.WriteLine("SceneFile=" + sceneFile)
    
    writer.WriteLine( "Version=%s" % versionStr )
    writer.WriteLine( "OutputFormat=%s" % outputFormat )
    writer.WriteLine( "OutputFile=%s" % outputFile )
    
    if version >= 9.5:
        writer.WriteLine( "AddFormatSuffix=%s" % scriptDialog.GetValue("FormatSuffixBox") )
    
    writer.WriteLine( "Antialised=%s" % scriptDialog.GetValue("AntialiasedBox") )
    writer.WriteLine( "ShapeEffects=%s" % scriptDialog.GetValue("ShapeEffectsBox") )
    writer.WriteLine( "LayerEffects=%s" % scriptDialog.GetValue("LayerEffectsBox") )
    writer.WriteLine( "HalfSize=%s" % scriptDialog.GetValue("HalfSizeBox") )
    writer.WriteLine( "HalfFrameRate=%s" % scriptDialog.GetValue("HalfFrameRateBox") )
    writer.WriteLine( "ReducedParticles=%s" % scriptDialog.GetValue("ReducedParticlesBox") )
    writer.WriteLine( "ExtraSmooth=%s" % scriptDialog.GetValue("ExtraSmoothBox") )
    writer.WriteLine( "NtscSafeColors=%s" % scriptDialog.GetValue("NtscSafeColorsBox") )
    writer.WriteLine( "NoPremultiplyAlpha=%s" % scriptDialog.GetValue("NoPremultiplyBox") )
    writer.WriteLine( "VariableLineWidths=%s" % scriptDialog.GetValue("VariableLineWidthsBox") )
    #writer.WriteLine( "MultiThreaded=%s" % scriptDialog.GetValue("MultiThreadedBox") )
    
    if version >= 10:
        writer.WriteLine( "LayerComp=%s" % scriptDialog.GetValue("LayerCompBox") )
        layerComps =  scriptDialog.GetItems( "LayerCompBox" )
        layerCompIndex = 0
        for layerComp in layerComps:
            writer.WriteLine( "LayerComp%s=%s" % (layerCompIndex, layerComp) )
            layerCompIndex = layerCompIndex + 1
        
        writer.WriteLine( "VideoCodec=%s" % scriptDialog.GetValue("VideoCodecBox") )
        writer.WriteLine( "Quality=%s" % scriptDialog.GetValue("QualityBox") )
        writer.WriteLine( "Depth=%s" % scriptDialog.GetValue("DepthBox") )
    
    if version >= 11:
        writer.WriteLine( "AddLayerCompSuffix=%s" % scriptDialog.GetValue("AddLayerCompSuffixBox") )
        writer.WriteLine( "CreateFolderForLayerComps=%s" % scriptDialog.GetValue("CreateFolderForLayerCompsBox") )
    
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( sceneFile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )

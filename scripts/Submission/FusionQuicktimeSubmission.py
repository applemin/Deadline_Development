import clr

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Scripting import *
from Deadline.Plugins import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

# For Integration UI
import imp
import os
imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
presetSettings = None
startup = True
updatingOutputFile = False

ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = False

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global presetSettings
    global startup
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Fusion Quicktime Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Fusion' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "JobOptionsSeparator", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 5, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 6, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 6, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 7, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 8, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 9, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 9, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 9, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SeparatorFusionOptions", "SeparatorControl", "Fusion Options", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Fusion Version", 1, 0, "Select the version of Fusion to generate the Quicktime with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "7", ("5","6","7","8"), 1, 1 )
    versionBox.ValueModified.connect(VersionModified)
    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build", 1, 2, "", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 1, 3 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Input / Output Options", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input Images", 1, 0, "The frames you would like to generate the Quicktime from. If a sequence of frames exist in the same folder, Deadline will automatically collect the range of the frames and will set the Frame Range field accordingly.", False )
    inputBox = scriptDialog.AddSelectionControlToGrid( "InputBox", "FileBrowserControl", "", "All Files (*)", 1, 1, colSpan=3 )
    inputBox.ValueModified.connect(InputImagesModified)

    scriptDialog.AddControlToGrid( "StartFrameLabel", "LabelControl", "Start Frame", 3, 0, "The first frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "StartFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 1 )
    scriptDialog.AddControlToGrid( "EndFrameLabel", "LabelControl", "End Frame", 3, 2, "The last frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "EndFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 3, 3 )
    
    scriptDialog.AddControlToGrid( "FrameRateLabel", "LabelControl", "Frame Rate", 4, 0, "The frame rate of the Quicktime.", False )
    scriptDialog.AddRangeControlToGrid( "FrameRateBox", "RangeControl", 24.00, 0.01, 100.00, 2, 1.00, 4, 1 )
    isOverrideBox = scriptDialog.AddSelectionControlToGrid( "IsOverrideBox", "CheckBoxControl", False, "Override Start", 4, 2, "Allows the starting frame in the Quicktime to be overridden.", False )
    isOverrideBox.ValueModified.connect(IsOverrideModified)
    scriptDialog.AddRangeControlToGrid( "OverrideBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 4, 3 )
    
    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Movie File", 5, 0, "The name of the Quicktime to be generated.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "", "Quicktime Movies (*.mov)", 5, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "CodecLabel", "LabelControl", "Codec", 6, 0, "The codec format to use for the Quicktime.", False )
    scriptDialog.AddComboControlToGrid( "CodecBox", "ComboControl", "None_raw", GetCodecs(), 6, 1 )
    scriptDialog.AddControlToGrid( "MissingFramesLabel", "LabelControl", "On Missing Frames", 6, 2, "What the generator will do when a frame is missing or is unable to load.", False )
    scriptDialog.AddComboControlToGrid( "MissingFramesBox", "ComboControl", "Output Black", ("Fail","Hold Previous","Output Black","Wait"), 6, 3 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Quicktime Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SeparatorQTSettings", "SeparatorControl", "Quicktime Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "BackgroundLabel", "LabelControl", "BG Plate (Optional)", 1, 0, "Specify an optinal background plate. The Quicktime will render using the selected file as the background.", False )
    scriptDialog.AddSelectionControlToGrid( "BackgroundBox", "FileBrowserControl", "", "All Files (*)", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "TemplateLabel", "LabelControl", "Template (Optional)", 2, 0, "Specify an optional Fusion comp to use as a template.", False )
    scriptDialog.AddSelectionControlToGrid( "TemplateBox", "FileBrowserControl", "", "Fusion Files (*.comp)", 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ArtistLabel", "LabelControl", "Artist Name", 3, 0, "The name of the artist who created the render. If left blank, the job's user will be used.", False )
    scriptDialog.AddControlToGrid( "ArtistBox", "TextControl", "", 3, 1 )
    scriptDialog.AddSelectionControlToGrid( "CurveCorrectionBox", "CheckBoxControl", False, "Curve Correction (If Template Is Specified)", 3, 2, "Select to turn on the color curves tool (available when using templates only).", colSpan=2 )

    scriptDialog.AddControlToGrid( "QualityLabel", "LabelControl", "Quality %", 4, 0, "The quality of the Quicktime.", False )
    scriptDialog.AddRangeControlToGrid( "QualityBox", "RangeControl", 75, 0, 100, 0, 1, 4, 1 )
    scriptDialog.AddControlToGrid( "ProxyLabel", "LabelControl", "Proxy", 4, 2, "The ratio of pixels to render (for example, if set to 4, one out of every four pixels will be rendered).", False )
    scriptDialog.AddRangeControlToGrid( "ProxyBox", "RangeControl", 1, 1, 8, 0, 1, 4, 3 )

    scriptDialog.AddControlToGrid( "GammaLabel", "LabelControl", "Gamma", 5, 0, "The gamma level of the Quicktime.", False )
    scriptDialog.AddRangeControlToGrid( "GammaBox", "RangeControl", 1.80000, 0.20000, 5.00000, 5, 0.20000, 5, 1 )
    scriptDialog.AddControlToGrid( "ExpCompLabel", "LabelControl", "Exposure Comp.", 5, 2, "The 'stops' value used to calculate the gain parameter of the Brightness/Contrast tool. The gain parameter is calculated by using the value pow(2,stops).", False )
    scriptDialog.AddRangeControlToGrid( "ExpCompBox", "RangeControl", 0.00000, -3.00000, 3.00000, 5, 0.50000, 5, 3 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "FusionQuicktimeMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
    scriptDialog.EndTabControl()

    scriptDialog.AddGrid()
    loadPresetButton = scriptDialog.AddControlToGrid( "LoadPresetButton", "ButtonControl", "Load Preset", 0, 0, expand=False )
    loadPresetButton.ValueModified.connect(LoadPresetButtonPressed)
    savePresetButton = scriptDialog.AddControlToGrid( "SavePresetButton", "ButtonControl", "Save Preset", 0, 1, expand=False )
    savePresetButton.ValueModified.connect(SavePresetButtonPressed)
    
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 3 )
    
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 4, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 5, expand=False )
    # Make sure all the project management connections are closed properly
    closeButton.ValueModified.connect(integration_dialog.CloseProjectManagementConnections)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ("CategoryBox","DepartmentBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","LimitGroupBox","OnJobCompleteBox","MachineListBox","SubmitSuspendedBox","IsBlacklistBox","InputBox","VersionBox","BuildBox","FrameRateBox","BackgroundBox","TemplateBox","ArtistBox","CurveCorrectionBox","CodecBox","MissingFramesBox","QualityBox","ProxyBox","GammaBox","ExpCompBox","IsOverrideBox","OverrideBox")
    presetSettings = ("VersionBox","BuildBox","FrameRateBox","BackgroundBox","TemplateBox","ArtistBox","CurveCorrectionBox","CodecBox","MissingFramesBox","QualityBox","ProxyBox","GammaBox","ExpCompBox","IsOverrideBox","OverrideBox")
    
    #Should be not from but for testing
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.SetItems( "CodecBox", GetCodecs() )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    
    if scriptDialog.GetValue("ArtistBox").strip() == "":
        scriptDialog.SetValue("ArtistBox", ClientUtils.GetDeadlineUser())
    
    if len( args ) > 0:
        scriptDialog.SetValue( "InputBox", args[0] )
    
    InputImagesModified()
    IsOverrideModified()
        
    startup = False
    
    scriptDialog.ShowDialog( len( args ) > 0 )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "FusionQuicktimeSettings.ini" )

def GetCodecs():
    global scriptDialog
        
    version = int(scriptDialog.GetValue( "VersionBox" ))
    if version == 5:
        return ("Animation_rle",
                "BMP_WRLE",
                "Cinepak_cvid",
                "Component Video_yuv2",
                "DV - PAL_dvcp",
                "DV/DVCPRO - NTSC_dvc",
                "DVCPRO - PAL_dvpp",
                "Graphics_smc",
                "H.261_h261",
                "H.263_h263",
                "H.264_avc1",
                "JPEG 2000_mjp2",
                "Motion JPEG A_mjpa",
                "Motion JPEG B_mjpb",
                "MPEG-4 Video_mp4v",
                "None_raw",
                "Photo - JPEG_jpeg",
                "Planar RGB_8BPS",
                "PNG_png",
                "Sorenson Video_SVQ1",
                "Sorenson Video 3_SVQ3",
                "TGA_tga",
                "TIFF_tiff",
                "Video_rpza")
    else:
        return ("Animation_rle",
                "Avid 1:1x_AV1x",
                "Avid DNxHD Codec_AVdn",
                "Avid DV Codec_AVdv",
                "Avid DV100 Codec_AVd1",
                "Avid Meridien Compressed_AVDJ",
                "Avid Meridien Uncompressed_AVUI",
                "Avid Packed Codec_AVup",
                "BMP_WRLE",
                "Cinepak_cvid",
                "Component Video_yuv2",
                "DV - PAL_dvcp",
                "DV/DVCPRO - NTSC_dvc",
                "DVCPRO - PAL_dvpp",
                "Graphics_smc",
                "H.261_h261",
                "H.263_h263",
                "H.264_avc1",
                "JPEG 2000_mjp2",
                "Motion JPEG A_mjpa",
                "Motion JPEG B_mjpb",
                "MPEG-4 Video_mp4v",
                "None_raw",
                "Photo - JPEG_jpeg",
                "Planar RGB_8BPS",
                "PNG_png",
                "Sorenson Video_SVQ1",
                "Sorenson Video 3_SVQ3",
                "TechSmith EnSharpen_tscc",
                "TGA_tga",
                "TIFF_tiff",
                "Video_rpza")
    
def GetMissingFramesNumber( missingFrames ):
    if missingFrames == "Fail":
        return 0
    elif missingFrames == "Hold Previous":
        return 1
    elif missingFrames == "Output Black":
        return 2
    elif missingFrames == "Wait":
        return 3
    else:
        return 2

def InputImagesModified(*args):
    global startup
    global updatingOutputFile
    
    if not updatingOutputFile:
        success = False
        
        try:
            filename = scriptDialog.GetValue( "InputBox" )
            if filename != "":
                initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
                paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
                
                startFrame = 0
                endFrame = 0
                outputFilename = ""
                
                #if initFrame >= 0 and paddingSize > 0:
                if paddingSize > 0:
                    filename = FrameUtils.GetLowerFrameFilename( filename, initFrame, paddingSize )
                    
                    updatingOutputFile = True
                    scriptDialog.SetValue( "InputBox", filename )
                    updatingOutputFile = False
                    
                    startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
                    endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
                    outputFilename = Path.ChangeExtension( FrameUtils.GetFilenameWithoutPadding( filename ), ".mov" )
                else:
                    outputFilename = Path.ChangeExtension( filename, ".mov" )
                
                scriptDialog.SetValue( "StartFrameBox", startFrame )
                scriptDialog.SetValue( "EndFrameBox", endFrame )
                
                scriptDialog.SetValue( "OutputBox", outputFilename )
                scriptDialog.SetValue( "NameBox", Path.GetFileNameWithoutExtension( outputFilename ) )
                
                success = True
            
        except Exception as e:
            if not startup:
                scriptDialog.ShowMessageBox( e.Message, "Error Parsing Input Images" )
        
        if not success:
            scriptDialog.SetValue( "InputBox", "" )
            scriptDialog.SetValue( "StartFrameBox", 0 )
            scriptDialog.SetValue( "EndFrameBox", 0 )
            scriptDialog.SetValue( "OutputBox", "" )
            scriptDialog.SetValue( "NameBox", "Untitled" )

def IsOverrideModified(*args):
    global scriptDialog
    
    isOverride = scriptDialog.GetValue( "IsOverrideBox" )
    scriptDialog.SetEnabled( "OverrideBox", isOverride )

def VersionModified(*args):
    global scriptDialog
    
    codecs = GetCodecs() 
    scriptDialog.SetItems( "CodecBox", codecs )
    if( len( codecs ) > 0 ):
        scriptDialog.SetValue( "CodecBox", codecs[0] )

def GetSourceDirectory():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "FusionQtPresets" )

def GetSourceFileName( sourceName ):
    return Path.Combine( GetSourceDirectory(), sourceName + ".ini" )

def LoadPresetButtonPressed(*args):
    global scriptDialog
    global presetSettings
    
    sourceDirectory = GetSourceDirectory()
    if not Directory.Exists( sourceDirectory ):
        Directory.CreateDirectory( sourceDirectory )
    
    selectedFile = scriptDialog.ShowOpenFileBrowser( sourceDirectory, "Preset INI Files (*.ini)" )
    if selectedFile != "":
        scriptDialog.LoadSettings( selectedFile, presetSettings )

def SavePresetButtonPressed(*args):
    global scriptDialog
    global presetSettings
    
    sourceDirectory = GetSourceDirectory()
    if not Directory.Exists( sourceDirectory ):
        Directory.CreateDirectory( sourceDirectory )
        
    selectedFile = scriptDialog.ShowSaveFileBrowser( sourceDirectory, "Preset INI Files (*.ini)" )
    if selectedFile != "":
        scriptDialog.SaveSettings( selectedFile, presetSettings )

def SubmitButtonPressed(*args):
    global scriptDialog
    global integration_dialog

    if ( scriptDialog.GetValue( "CodecBox" ) == "" ):
        scriptDialog.ShowMessageBox( "Please select a codec", "Error" )
    else:
        # Check if input files exist.
        inputFile = scriptDialog.GetValue( "InputBox" ).strip()
        
        if(len(inputFile)==0):
            scriptDialog.ShowMessageBox("No input file specified","Error")
            return
            
        if( PathUtils.IsPathLocal( inputFile ) ):
            result = scriptDialog.ShowMessageBox( "The input file " + inputFile + " is local, are you sure you want to continue","Warning", ("Yes","No") )
            if( result == "No" ):
                return
        
        # Check output file.
        outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
        if(len(outputFile)==0):
            scriptDialog.ShowMessageBox("No output file specified","Error")
            return
        if( not Directory.Exists( Path.GetDirectoryName( outputFile ) ) ):
            scriptDialog.ShowMessageBox( "Path for the output file " + outputFile + " does not exist.", "Error" )
            return
        elif( PathUtils.IsPathLocal( outputFile ) ):
            result = scriptDialog.ShowMessageBox( "The output file " + outputFile + " is local, are you sure you want to continue","Warning", ("Yes","No") )
            if( result == "No" ):
                return
        
        version = scriptDialog.GetValue( "VersionBox" )
        
        # Check background file
        backgroundFile = scriptDialog.GetValue( "BackgroundBox" ).strip()
        if( len( backgroundFile ) > 0 ):
            if( not Directory.Exists( Path.GetDirectoryName( backgroundFile ) ) ):
                scriptDialog.ShowMessageBox( "Path for the background plate file " + backgroundFile + " does not exist.", "Error" )
                return
            elif( PathUtils.IsPathLocal( backgroundFile ) ):
                result = scriptDialog.ShowMessageBox( "The background plate  file " + backgroundFile + " is local, are you sure you want to continue","Warning", ("Yes","No") )
                if( result == "No" ):
                    return
        
        # Check the template file
        templateFile = scriptDialog.GetValue( "TemplateBox" ).strip()
        if( len( templateFile ) > 0 ):
            if( not Directory.Exists( Path.GetDirectoryName( templateFile ) ) ):
                scriptDialog.ShowMessageBox( "Path for the template file " + templateFile + " does not exist.", "Error" )
                return
            elif( PathUtils.IsPathLocal( templateFile ) ):
                result = scriptDialog.ShowMessageBox( "The template  file " + templateFile + " is local, are you sure you want to continue","Warning", ("Yes","No") )
                if( result == "No" ):
                    return
        
        # Check if Integration options are valid
        if not integration_dialog.CheckIntegrationSanity( outputFile ):
            return
        
        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "quicktime_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Fusion" )
        writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "MachineLimit=1" )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
        
        if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        writer.WriteLine( "Frames=%s-%s" % (scriptDialog.GetValue( "StartFrameBox" ), scriptDialog.GetValue( "EndFrameBox")) )
        writer.WriteLine( "ChunkSize=100000" )
        writer.WriteLine( "OutputFilename0=%s" % outputFile )
        
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
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "quicktime_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False )
        
        writer.WriteLine( "Version=%s" % version )
        writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
        writer.WriteLine( "QuicktimeJob=True" )
        writer.WriteLine( "QuicktimeInputImages=%s" % inputFile )
        writer.WriteLine( "QuicktimeOutputFile=%s" % outputFile )
        writer.WriteLine( "QuicktimeFrameRate=%s" % scriptDialog.GetValue( "FrameRateBox" ) )
        
        writer.WriteLine( "QuicktimeBackgroundPlate=%s" % backgroundFile )
        writer.WriteLine( "QuicktimeTemplate=%s" % templateFile )
        writer.WriteLine( "QuicktimeCurveCorrect=%s" % scriptDialog.GetValue( "CurveCorrectionBox" ) )
        
        writer.WriteLine( "QuicktimeArtistName=%s" % scriptDialog.GetValue( "ArtistBox" ) )
        writer.WriteLine( "QuicktimeCodec=%s" % scriptDialog.GetValue( "CodecBox" ) )
        writer.WriteLine( "QuicktimeMissingFrames=%d" % GetMissingFramesNumber( scriptDialog.GetValue( "MissingFramesBox" ) ) )
        writer.WriteLine( "QuicktimeQuality=%s" % scriptDialog.GetValue( "QualityBox" ) )
        writer.WriteLine( "QuicktimeProxy=%s" % scriptDialog.GetValue( "ProxyBox" ) )
        writer.WriteLine( "QuicktimeGamma=%s" % scriptDialog.GetValue( "GammaBox" ) )
        writer.WriteLine( "QuicktimeExpCompensation=%s" % scriptDialog.GetValue( "ExpCompBox" ) )
        
        if scriptDialog.GetValue( "IsOverrideBox" ):
            writer.WriteLine( "QuicktimeFrameOverride=%s" % scriptDialog.GetValue( "OverrideBox" ) )
        else:
            writer.WriteLine( "QuicktimeFrameOverride=%s" % scriptDialog.GetValue( "StartFrameBox" ) )
        
        writer.Close()
        
        # Setup the command line arguments.
        arguments = StringCollection()
        
        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        
        # Now submit the job.
        results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        scriptDialog.ShowMessageBox( results, "Submission Results" )

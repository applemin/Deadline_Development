# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import io
import os

from Deadline.Scripting import ClientUtils, FrameUtils, PathUtils, RepositoryUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
fileFormats = {
    "3D model": ( ".3ds", ".dae", ".dwg", ".dxf", ".fbx", ".ifc", ".kmz", ".obj", ".wrl", ".xsi" ),
    "2D image sequence": ( ".bmp", ".jpg", ".png", ".tif" ),
    "2D image": ( ".bmp", ".dwg", ".dxf", ".eps", ".epx", ".jpg", ".pdf", ".png", ".tif" ),
}
scriptDialog = None
settings = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit SketchUp To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'SketchUp' ) )
    
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
    scriptDialog.EndTabPage()

    scriptDialog.AddTabPage( "Render Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "SketchUp Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "SketchUp File", 1, 0, "The scene file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "SketchUp Files (*.skp)", 1, 1, colSpan=3  )

    scriptDialog.AddControlToGrid( "ExportDirectoryLabel", "LabelControl", "Export Directory", 2, 0, "The directory your saved export file is saved to.", False )
    scriptDialog.AddSelectionControlToGrid( "ExportDirectoryBox", "FolderBrowserControl", "", "", 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ExportNameLabel", "LabelControl", "Export File Prefix", 3, 0, "The name of your output file(s), without the format. If blank, uses SketchUp filename.", False )
    scriptDialog.AddControlToGrid( "ExportNameBox", "TextControl", "", 3, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "SceneNameLabel", "LabelControl", "Scene to Export", 4, 0, "The name of the scene to export. If blank, uses currently selected scene.", False )
    scriptDialog.AddControlToGrid( "SceneNameBox", "TextControl", "", 4, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "ExportTypeLabel", "LabelControl", "Export Type", 5, 0, "Specify the type of job you wish to export.", False ) # SU Free only supports .dae and .kmz
    exportTypeBox = scriptDialog.AddComboControlToGrid( "ExportTypeBox", "ComboControl", "3D", ("3D model", "2D image sequence", "2D image"), 5, 1 )
    exportTypeBox.ValueModified.connect( ExportTypeChanged )
    scriptDialog.AddControlToGrid( "ExportFormatLabel", "LabelControl", "Export Format", 5, 2, "Specify the output format of the job.", False )
    exportFormatBox = scriptDialog.AddComboControlToGrid( "ExportFormatBox", "ComboControl", ".dae", (".3ds", ".dae", ".dwg", ".dxf", ".fbx", ".ifc", "kmz", ".obj", ".wrl", ".xsi"), 5, 3 )
    exportFormatBox.ValueModified.connect( JobOptionChanged )

    scriptDialog.AddControlToGrid( "FrameRateLabel", "LabelControl", "Frame Rate", 6, 0, "Specify the frame rate (frames per second) for the image sequence.", False )
    scriptDialog.AddRangeControlToGrid( "FrameRateBox", "RangeControl", 1, 1, 100000, 2, 0.1, 6, 1 )
    scriptDialog.AddControlToGrid( "CompressionLabel", "LabelControl", "Compression Rate", 6, 2, "Specify the compression rate for jpg's (0.0 smallest size, 1.0 best quality).", False )
    scriptDialog.AddRangeControlToGrid( "CompressionRateBox", "RangeControl", 0, 0, 1, 2, 0.1, 6, 3 )

    scriptDialog.AddControlToGrid( "WidthLabel", "LabelControl", "Width", 7, 0, "The width of the exported image in pixels (if 0, will use default width).", False )
    scriptDialog.AddRangeControlToGrid( "WidthBox", "RangeControl", 0, 0, 16000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "AntiAliasBox", "CheckBoxControl", False, "Anti-alias", 7, 2, "Specify if you want to use anti-aliasing.")
    
    scriptDialog.AddControlToGrid( "HeightLabel", "LabelControl", "Height", 8, 0, "The height of the exported image in pixels (if 0, will use default height).", False )
    scriptDialog.AddRangeControlToGrid( "HeightBox", "RangeControl", 0, 0, 16000, 0, 1, 8, 1 )
    scriptDialog.AddSelectionControlToGrid( "TransparentBox", "CheckBoxControl", False, "Transparent", 8, 2, "Specify whether you want the image transparent or not.")

    scriptDialog.AddControlToGrid("VersionLabel", "LabelControl", "Version", 9, 0, "The version of SketchUp to render with.", False )
    scriptDialog.AddComboControlToGrid("VersionBox", "ComboControl", "2018", ("7","8","2013", "2014", "2015", "2016", "2017", "2018" ), 9, 1 )
    scriptDialog.AddSelectionControlToGrid("SubmitSceneBox", "CheckBoxControl", False, "Submit SketchUp Scene", 9, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering.")
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "VRayOptionsSeparator", "SeparatorControl", "V-Ray Options", 0, 0, colSpan=4 )

    useVrayBox = scriptDialog.AddSelectionControlToGrid( "VrayBox", "CheckBoxControl", False, "Use VRay", 1, 0, "If this option is enabled, V-Ray is used to render the sceneFile." )
    useVrayBox.ValueModified.connect( JobOptionChanged )
    vrayVersionBox = scriptDialog.AddComboControlToGrid( "VrayVersionBox", "ComboControl", "2", ("2", "3"), 1, 1 )
    vrayVersionBox.ValueModified.connect( JobOptionChanged )

    scriptDialog.AddControlToGrid( "VrayFramesLabel", "LabelControl", "Frame List", 2, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "VrayFramesBox", "TextControl", "0", 2, 1 )
    scriptDialog.AddControlToGrid( "VrayChunkSizeLabel", "LabelControl", "Frames Per Task", 2, 2, "The number of frames rendered per task in a V-Ray 3 (or later) job.", False )
    scriptDialog.AddRangeControlToGrid( "VrayChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 2, 3 )

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.EndTabControl()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect( SubmitButtonPressed )
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect( scriptDialog.closeEvent )
    scriptDialog.EndGrid()
    settings = ( "DepartmentBox", "PoolBox", "SecondaryPoolBox", "GroupBox", "PriorityBox", "IsBlacklistBox",
                 "MachineListBox", "LimitGroupBox", "ExportTypeBox", "ExportFormatBox", "ExportDirectoryBox",
                 "ExportNameBox", "FrameRateBox", "CompressionRateBox", "WidthBox", "HeightBox", "AntiAliasBox",
                 "TransparentBox", "SceneBox", "VersionBox", "SubmitSceneBox", "SceneNameBox",
                 "VrayBox", "VrayVersionBox", "VrayFramesBox", "VrayChunkSizeBox" )

    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    # Determine if submitting from monitor or from SketchUp
    inAppSubmission = False
    if len( args ) > 0:
        inAppSubmission = True
        scriptDialog.SetValue( "SceneBox", args[0] )
        scriptDialog.SetValue( "VersionBox", args[1] )
        if len( args ) > 2:
            scriptDialog.SetValue( "SceneNameBox", args[2] )
        
        # Keep the submission window above all other windows when submitting from another app.
        scriptDialog.MakeTopMost()

    ExportTypeChanged()

    scriptDialog.ShowDialog( inAppSubmission )


def GetSettingsFilename():
    """
    Helper function that grabs the location of the sticky settings file
    :return: the path of the sticky settinsg file
    """
    return os.path.join( ClientUtils.GetUsersSettingsDirectory(), "SketchUpSettings.ini" )

def is3dModel():
    """
    Helper function to determine if the render is for a 3d model
    :return: a boolean indicating if the render is a 3d model
    """
    global scriptDialog

    return scriptDialog.GetValue( "ExportTypeBox" ) == "3D model"

def is2dAnimation():
    """
    Helper function to determine if the render is for an image sequence
    :return: a boolean indicating if the render is an image sequence
    """
    global scriptDialog

    return scriptDialog.GetValue( "ExportTypeBox" ) == "2D image sequence"

def is2dScene():
    """
    Helper function to determine if the render is for an image
    :return: a boolean indicating if the render is an image
    """
    global scriptDialog

    return scriptDialog.GetValue( "ExportTypeBox" ) == "2D image"

def ExportTypeChanged( *args ):
    """
    Callback for when the type of render changes in the UI
    :param args: source of the event
    """
    global scriptDialog, fileFormats
    exportType = scriptDialog.GetValue( "ExportTypeBox" )
    currentFormat = scriptDialog.GetValue( "ExportFormatBox" )

    # Set the file formats for the export type and choose its selection
    scriptDialog.SetItems( "ExportFormatBox", tuple( fileFormats[ exportType ] ) )
    if currentFormat in fileFormats[ exportType ]:
        scriptDialog.SetValue( "ExportFormatBox", currentFormat )
    else:
        defaultFormat = fileFormats[ exportType ][ 0 ]
        if is2dScene():
            defaultFormat = fileFormats[ exportType ][ 5 ]
        elif is2dAnimation() or is3dModel():
            defaultFormat = fileFormats[ exportType ][ 1 ]
        scriptDialog.SetValue( "ExportFormatBox", defaultFormat )

    JobOptionChanged()

def JobOptionChanged( *args ):
    """
    Callback for when some job options are changed. Mostly used to enable/disable options based on v-ray and export selection
    :param args: source of the event
    """
    global scriptDialog

    # Need to enable the 'Use V-Ray' Checkbox here, since we rely on the enabled state
    scriptDialog.SetEnabled( "VrayBox", not is3dModel() )

    isJPG = scriptDialog.GetValue( "ExportFormatBox" ) == ".jpg"
    vrayVersion = int( scriptDialog.GetValue( "VrayVersionBox" ) )
    isVRay = scriptDialog.GetEnabled( "VrayBox" ) and scriptDialog.GetValue( "VrayBox" )
    isVRay3Animation = isVRay and is2dAnimation() and vrayVersion == 3

    # Job Options
    scriptDialog.SetEnabled( "SceneNameBox", is2dScene() )

    scriptDialog.SetEnabled( "WidthLabel", not is3dModel() )
    scriptDialog.SetEnabled( "WidthBox", not is3dModel() )

    scriptDialog.SetEnabled( "HeightLabel", not is3dModel() )
    scriptDialog.SetEnabled( "HeightBox", not is3dModel() )

    scriptDialog.SetEnabled( "AntiAliasBox", not is3dModel() and not isVRay )
    scriptDialog.SetEnabled( "TransparentBox", not is3dModel() and not isVRay )

    scriptDialog.SetEnabled( "FrameRateLabel", is2dAnimation() and ( not isVRay or ( isVRay and vrayVersion == 2 ) ) )
    scriptDialog.SetEnabled( "FrameRateBox", is2dAnimation() and ( not isVRay or ( isVRay and vrayVersion == 2 ) ) )

    # V-Ray support doesn't currently this JPG compression rate
    scriptDialog.SetEnabled( "CompressionLabel", isJPG and not isVRay )
    scriptDialog.SetEnabled( "CompressionRateBox", isJPG and not isVRay )

    # V-Ray Options
    scriptDialog.SetEnabled( "VrayVersionBox", isVRay )
    scriptDialog.SetEnabled( "VrayFramesLabel", isVRay3Animation )
    scriptDialog.SetEnabled( "VrayFramesBox", isVRay3Animation )
    scriptDialog.SetEnabled( "VrayChunkSizeLabel", isVRay3Animation )
    scriptDialog.SetEnabled( "VrayChunkSizeBox", isVRay3Animation )

def isValidSubmission():
    """
    Runs sanity checks on the current submission params to see if we know the submission is bad, so we can fail
    fast. If there's warnings and/or errors, we present them to the user so they can be fixed.
    :return: a boolean indicating if we believe this submission is valid
    """
    global scriptDialog

    errors = ""
    warnings = ""

    # Check if SU file exists
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if not os.path.isfile( sceneFile ):
        errors += 'SketchUp file "%s" does not exist.\n\n' % sceneFile
    elif PathUtils.IsPathLocal( sceneFile ) and not scriptDialog.GetValue( "SubmitSceneBox" ):
        warnings += 'SketchUp file "%s" is local.\n\n' % sceneFile

    # Check Output
    exportDirectory = scriptDialog.GetValue( "ExportDirectoryBox" ).strip()
    if not exportDirectory:
        errors += "An output directory was not specific.\n\n"
    elif not os.path.isdir( exportDirectory ):
        errors += 'The directory of the output file does not exist: "%s"\n\n' % exportDirectory

    isVray = scriptDialog.GetEnabled( "VrayBox" ) and scriptDialog.GetValue( "VrayBox" )
    vrayVersion = int( scriptDialog.GetValue( "VrayVersionBox" ) )
    vrayFrames = scriptDialog.GetValue( "VrayFramesBox" ).strip()
    # Check if a valid frame range has been specified for V-Ray 3 or later
    if isVray and vrayVersion >= 3 and is2dAnimation() and not FrameUtils.FrameRangeValid( vrayFrames ):
        errors += 'Frame range "%s" is not valid.\n\n' % vrayFrames

    if errors:
        scriptDialog.ShowMessageBox( "The following errors occurred, you must fix these before continuing.\n\n%s" % errors.strip(), "Error" )
        return False
    elif warnings:
        result = scriptDialog.ShowMessageBox( "The following warnings occurred, are you sure you want to continue?\n\n%s" % warnings.strip(), "Warning", ( "Yes", "No" ) )
        if result == "No":
            return False

    return True

def CreateJobSettings():
    """
    Builds up a dictionary of job settings based on the submission options specified in the UI
    :return: a dict containing the settings for the job info file
    """
    global scriptDialog

    jobSettings = {
        "Plugin": "SketchUp",
        "Name": scriptDialog.GetValue( "NameBox" ),
        "Comment": scriptDialog.GetValue( "CommentBox" ),
        "Department": scriptDialog.GetValue( "DepartmentBox" ),
        "Pool": scriptDialog.GetValue( "PoolBox" ),
        "SecondaryPool": scriptDialog.GetValue( "SecondaryPoolBox" ),
        "Group": scriptDialog.GetValue( "GroupBox" ),
        "Priority": scriptDialog.GetValue( "PriorityBox" ),
        "TaskTimeoutMinutes": scriptDialog.GetValue( "TaskTimeoutBox" ),

        "LimitGroups": scriptDialog.GetValue( "LimitGroupBox" ),
        "JobDependencies": scriptDialog.GetValue( "DependencyBox" ),
        "OnJobComplete": scriptDialog.GetValue( "OnJobCompleteBox" ),

        "OutputDirectory0": scriptDialog.GetValue("ExportDirectoryBox").strip(),
    }

    if scriptDialog.GetValue( "IsBlacklistBox" ):
        jobSettings["Blacklist"] = scriptDialog.GetValue( "MachineListBox" )
    else:
        jobSettings["Whitelist"] = scriptDialog.GetValue( "MachineListBox" )

    if scriptDialog.GetValue( "SubmitSuspendedBox" ):
        jobSettings["InitialStatus"] = "Suspended"

    isVray = scriptDialog.GetEnabled( "VrayBox" ) and scriptDialog.GetValue( "VrayBox" )
    vrayVersion = int( scriptDialog.GetValue( "VrayVersionBox" ) )
    if isVray and vrayVersion == 3 and is2dAnimation():
        jobSettings["Frames"] = scriptDialog.GetValue( "VrayFramesBox" ).strip()
        jobSettings["ChunkSize"] = scriptDialog.GetValue( "VrayChunkSizeBox" )

    return jobSettings

def CreatePluginSettings():
    """
    Buids up a dictionary of plugin settings based on the submission options specified in the UI
    :return: a dict containing the settings for the plugin info file
    """
    global scriptDialog
    isVray = scriptDialog.GetEnabled( "VrayBox" ) and scriptDialog.GetValue( "VrayBox" )

    pluginSettings = {
        "ExportType": scriptDialog.GetValue( "ExportTypeBox" ),
        "ExportFormat": scriptDialog.GetValue( "ExportFormatBox" ),
        "ExportDirectory": scriptDialog.GetValue("ExportDirectoryBox").strip(),
        "ExportName": scriptDialog.GetValue( "ExportNameBox" ).strip(),
        "SceneName": scriptDialog.GetValue( "SceneNameBox" ),
        "Version": scriptDialog.GetValue( "VersionBox"),
        "UseVray": isVray,
    }

    if is2dAnimation():
        pluginSettings["FrameRate"] = scriptDialog.GetValue( "FrameRateBox" )

    if is2dScene() or is2dAnimation():
        pluginSettings["Width"] = scriptDialog.GetValue( "WidthBox" )
        pluginSettings["Height"] = scriptDialog.GetValue( "HeightBox" )
        pluginSettings["AntiAlias"] = scriptDialog.GetValue( "AntiAliasBox" )
        pluginSettings["Transparent"] = scriptDialog.GetValue( "TransparentBox" )

        if scriptDialog.GetValue( "ExportFormatBox" ) == ".jpg":
            pluginSettings["CompressionRate"] = scriptDialog.GetValue( "CompressionRateBox" )

    if not scriptDialog.GetValue( "SubmitSceneBox" ):
        pluginSettings["SceneFile"] = scriptDialog.GetValue( "SceneBox" )

    vrayVersion = int( scriptDialog.GetValue( "VrayVersionBox" ) )
    if isVray:
        pluginSettings["VrayVersion"] = vrayVersion

    return pluginSettings

def WriteJobFile( filename, settingsDict ):
    """
    Creates a file of key-value pairs from a dictoinary in the form of "key=value\n"
    :param filename: name of the file to create in the Deadline temp directory
    :param settingsDict: dictionary containing the key value pairs we wish to write to the file
    :return: returns the full path of the created file
    """
    filepath = os.path.join( ClientUtils.GetDeadlineTempPath(), filename )
    with io.open( filepath, "w", encoding="utf-8-sig" ) as fileHandle:
        for key, value in settingsDict.iteritems():
            fileHandle.write( "%s=%s\n" % ( key, value ) )

    return filepath

def SubmitButtonPressed( *args ):
    """
    Callback for when the "submit" button is pushed. Runs the submission logic
    :param args: source of the event
    """
    global scriptDialog

    if not isValidSubmission():
        return

    jobInfoFilename = WriteJobFile( "sketchup_job_info.job", CreateJobSettings() )
    pluginInfoFilename = WriteJobFile( "sketchup_plugin_info.job", CreatePluginSettings() )

    arguments = [ jobInfoFilename, pluginInfoFilename ]
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.append( scriptDialog.GetValue( "SceneBox" ) )

    # submit the job
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )

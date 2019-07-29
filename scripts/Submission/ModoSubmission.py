from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

import datetime
import traceback
import re

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
outputFormats = dict()
outputFormatsByFormat = dict()
outputFileNamesFromScene = None
ProjectManagementOptions = ["Shotgun","FTrack","NIM"]
DraftRequested = True

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global outputFileNamesFromScene
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit modo Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Modo' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )
    
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
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "" )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering. ", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render. " )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "modo Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "modo File", 1, 0, "The scene file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "Luxology Scenes (*.lxo);;All Files (*)", 1, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "ProjectLabel", "LabelControl", "modo Project Folder", 2, 0, "The project folder associated with the scene (used for mapping relative paths)", False )
    scriptDialog.AddSelectionControlToGrid( "ProjectBox", "FolderBrowserControl", "", "", 2, 1, colSpan=3 )
    

    scriptDialog.AddControlToGrid( "PassLabel", "LabelControl", "Pass Group (optional)", 3, 0, "The passes group to render, or blank to not render a passes group. Used in modo 6xx or later.", False )
    scriptDialog.AddControlToGrid( "PassBox", "TextControl", "", 3, 1 )
    scriptDialog.AddSelectionControlToGrid("SubmitSceneBox","CheckBoxControl",False,"Submit modo Scene", 3, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering.")
    scriptDialog.AddSelectionControlToGrid("VRayBox","CheckBoxControl",False,"Render with V-Ray", 3, 3, "If this option is enabled, the scene file will be rendered using V-Ray.")
    
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 4, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 5, 0, "This is the number of frames that will be rendered at a time for each job task. ", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddControlToGrid( "ThreadsLabel", "LabelControl", "Render Threads", 5, 2, "The number of render threads to use. Specify 0 to use automatic render threads.", False )
    scriptDialog.AddRangeControlToGrid( "ThreadsBox", "RangeControl", 0, 0, 256, 0, 1, 5, 3 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 6, 0, "The version of modo to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "12xx", ( "3xx","4xx","5xx","6xx","7xx","8xx","9xx", "10xx", "11xx", "12xx" ), 6, 1 )
    versionBox.ValueModified.connect(VersionBoxChanged)
    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 6, 2, "You can force 32 or 64 bit rendering with this option." )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 6, 3 )

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Output and Tile Rendering")
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "WarningLabel", "LabelControl", "Note that overriding output and Tile Rendering have some limitations when done so from this submission script. If you have the <output> tag in your Output Pattern below, or your scene file uses pass groups or has left and right eye outputs, it is recommended that you submit from the integrated modo submitter.", 0, 0 ).setWordWrap(True)
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    
    scriptDialog.AddControlToGrid( "Separator7", "SeparatorControl", "Output Options", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Folder (optional)", 1, 0, "Specify an output folder. Note that specifying the output is optional unless you want to use tile rendering.", False )
    outputBox = scriptDialog.AddSelectionControlToGrid( "OutputBox", "FolderBrowserControl", "", "", 1, 1, colSpan=3 )
    scriptDialog.AddControlToGrid( "PrefixLabel", "LabelControl", "Output File Prefix", 2, 0, "If specifying an output folder, specify the prefix for the output file name (extension is not required).", False )
    prefixBox = scriptDialog.AddControlToGrid( "PrefixBox", "TextControl", "", 2, 1, colSpan=3 )
    scriptDialog.AddControlToGrid( "PatternLabel", "LabelControl", "Output Pattern", 3, 0, "If specifying an output folder, specify the pattern for the output file name (for example, [<pass>][<output>][<LR>]<FFFF>). Used in modo 6xx or later.", False )
    scriptDialog.AddControlToGrid( "PatternBox", "TextControl", "[<pass>][<output>][<LR>]<FFFF>", 3, 1, colSpan=3 )
    scriptDialog.AddControlToGrid( "FormatLabel", "LabelControl", "Output Format", 4, 0, "If specifying an output folder, specify the format of the output images." )
    formatBox = scriptDialog.AddComboControlToGrid( "FormatBox", "ComboControl", "", ("",), 4, 1, colSpan=3 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Tile Rendering Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "TileFrameLabel", "LabelControl", "Frame To Tile Render", 1, 0, "The frame to tile render.", False )
    scriptDialog.AddRangeControlToGrid( "TileFrameBox", "RangeControl", 1, -1000000, 1000000, 0, 1, 1, 1 )
    tileRenderingBox = scriptDialog.AddSelectionControlToGrid("TileRenderingBox","CheckBoxControl",False,"Enable Tile Rendering", 1, 2, "Enable tile rendering.")
    tileRenderingBox.ValueModified.connect(TileRenderingChanged)

    scriptDialog.AddControlToGrid( "TilesInXLabel", "LabelControl", "Tiles In X", 2, 0, "The number of tiles in the horizontal direction.", False )
    scriptDialog.AddRangeControlToGrid( "TilesInXBox", "RangeControl", 2, 1, 1000, 0, 1, 2, 1 )
    tileDependentBox = scriptDialog.AddSelectionControlToGrid("TileDependentBox","CheckBoxControl",True,"Submit Dependent Assembly Job", 2, 2, "Enable to submit a dependent job that will assemble the tiles from the main job.")
    tileDependentBox.ValueModified.connect(TileDependentChanged)

    scriptDialog.AddControlToGrid( "TilesInYLabel", "LabelControl", "Tiles In Y", 3, 0, "The number of tiles in the vertical direction.", False )
    scriptDialog.AddRangeControlToGrid( "TilesInYBox", "RangeControl", 2, 1, 1000, 0, 1, 3, 1 )
    scriptDialog.AddSelectionControlToGrid("TileCleanUpBox","CheckBoxControl",False,"Clean Up Tiles After Assembly", 3, 2, "Enable to delete the individual tile files after they have been successfully assembled.")

    scriptDialog.AddSelectionControlToGrid("ErrorOnMissingBox","CheckBoxControl",True,"Error On Missing Tiles", 4, 2, "If enabled, Draft will not report an error if there are missing tiles during the assembly.")
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "ModoMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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
    
    #Application Box must be listed before version box or else the application changed event will change the version
    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","SubmitSceneBox","FramesBox","ChunkSizeBox","PassBox","OutputBox","TileFrameBox","TilesInXBox","TilesInYBox","TileDependentBox","TileCleanUpBox","ErrorOnMissingBox","VersionBox","BuildBox","PrefixBox","PatternBox","FormatBox","ThreadsBox","ProjectBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    appSubmission = False
    if len( args ) > 0:
        scriptDialog.SetValue( "SceneBox", args[0] )
        scriptDialog.SetValue( "FramesBox", args[1] )
        
        sceneName = Path.GetFileName( args[0] )
        scriptDialog.SetValue( "NameBox", sceneName )
        
        # Check for any output paths from modo.
        if len( args ) > 2:
            outputFileNamesFromScene = []
            for i in range( 2, len( args ), 2 ):
                outputFileNamesFromScene.append( args[i] ) # file name
                outputFileNamesFromScene.append( args[i+1] ) # format
                
            # If there are any outputs, clear the output path and output prefix options.
            if len( outputFileNamesFromScene ) > 0:
                scriptDialog.SetValue( "OutputBox", "")
                scriptDialog.SetValue( "PrefixBox", "" )
        
        appSubmission = True
        
        # Keep the submission window above all other windows when submitting from another app.
        scriptDialog.MakeTopMost()
    
    # This is hooked up here to avoid errors from loading settings above.
    outputBox.ValueModified.connect(OutputBoxChanged)
    prefixBox.ValueModified.connect(PrefixBoxChanged)
    formatBox.ValueModified.connect(FormatBoxChanged)
    
    VersionBoxChanged()
    OutputBoxChanged()
    PrefixBoxChanged()
    FormatBoxChanged()
    TileRenderingChanged()
    TileDependentChanged()
    
    scriptDialog.ShowDialog( appSubmission )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "ModoSettings.ini" )

def SetVersionOutputFormats():
    global scriptDialog
    global outputFormats
    global outputFormatsByFormat
    
    formats = {}
    formats["3xx"] = ("$FLEX|flx|0|0=Flexible Precision FLX",
                    "$Targa|tga|1|1=Targa",
                    "BMP|BMP|1|1=Windows BMP",
                    "GIF|gif|0|0=Compuserve GIF",
                    "HDR|hdr|0|0=High Dynamic Range HDR",
                    "JPG|jpg|1|1=JPEG",
                    "PNG|png|1|0=PNG",
                    "SGI|SGI|1|0=SGI RGB",
                    "TGA|tga|1|1=Truevision Targa TGA",
                    "TIF|tif|1|0=TIF",
                    "TIF16|tif|1|0=16-Bit TIF",
                    "TIF16BIG|tif|1|0=16-Bit Uncompr. TIF",
                    "openexr|exr|1|0=OpenEXR")
    formats["4xx"] = ("$FLEX|flx|0|0=Flexible Precision FLX",
                    "$Targa|tga|1|1=Targa",
                    "BMP|BMP|1|1=Windows BMP",
                    "GIF|gif|0|0=Compuserve GIF",
                    "HDR|hdr|0|0=High Dynamic Range HDR",
                    "JP2|jp2|0|0=JPEG 2000",
                    "JP216|jp2|0|0=JPEG 2000 16-Bit",
                    "JP216Lossless|jp2|0|0=JPEG 2000 16-Bit Lossless",
                    "JPG|jpg|1|1=JPEG",
                    "PNG|png|1|0=PNG",
                    "PNG16|png|1|0=PNG 16-bit",
                    "PSD|psd|0|0=PSD",
                    "SGI|SGI|1|0=SGI RGB",
                    "TIF|tif|1|0=TIF",
                    "TIF16|tif|1|0=16-Bit TIF",
                    "TIF16BIG|tif|1|0=16-Bit Uncompr. TIF",
                    "openexr|exr|1|0=OpenEXR",
                    "LayeredPSD|psd|0|0=LayeredPSD",
                    "PNGs|png|0|0=Multi-file PNG Layers",
                    "PNGs16|png|0|0=Multi-file 16-bit Layers",
                    "openexrlayers|exr|1|0=Layered OpenEXR")
    formats["5xx"] = ("$FLEX|flx|0|0=Flexible Precision FLX",
                    "$Targa|tga|1|1=Targa",
                    "BMP|BMP|1|1=Windows BMP",
                    "HDR|hdr|0|0=High Dynamic Range HDR",
                    "JP2|jp2|0|0=JPEG 2000",
                    "JP216|jp2|0|0=JPEG 2000 16-Bit",
                    "JP216Lossless|jp2|0|0=JPEG 2000 16-Bit Lossless",
                    "JPG|jpg|1|1=JPEG",
                    "PNG|png|1|0=PNG",
                    "PNG16|png|1|0=PNG 16-bit",
                    "PSD|psd|0|0=PSD",
                    "SGI|SGI|1|0=SGI RGB",
                    "TIF|tif|1|0=TIF",
                    "TIF16|tif|1|0=16-Bit TIF",
                    "TIF16BIG|tif|1|0=16-Bit Uncompr. TIF",
                    "openexr|exr|1|0=OpenEXR 16-bit",
                    "openexr_32|exr|1|0=OpenEXR 32-bit",
                    "openexr_tiled|exr|1|0=OpenEXR Tiled 16-bit",
                    "openexr_tiled32|exr|1|0=OpenEXR Tiled 32-bit",
                    "LayeredPSD|psd|0|0=LayeredPSD",
                    "PNGs|png|0|0=Multi-file PNG Layers",
                    "PNGs16|png|0|0=Multi-file 16-bit Layers",
                    "openexrlayers|exr|1|0=Layered OpenEXR 16-bit",
                    "openexrlayers32|exr|1|0=Layered OpenEXR 32-bit")
    formats["6xx"] = ("$FLEX|flx|0|0=Flexible Precision FLX",
                    "$Targa|tga|1|1=Targa",
                    "BMP|BMP|1|1=Windows BMP",
                    "HDR|hdr|0|0=High Dynamic Range HDR",
                    "JP2|jp2|0|0=JPEG 2000",
                    "JP216|jp2|0|0=JPEG 2000 16-Bit",
                    "JP216Lossless|jp2|0|0=JPEG 2000 16-Bit Lossless",
                    "JPG|jpg|1|1=JPEG",
                    "PNG|png|1|0=PNG",
                    "PNG16|png|1|0=PNG 16-bit",
                    "PSD|psd|0|0=PSD",
                    "SGI|SGI|1|0=SGI RGB",
                    "TIF|tif|1|0=TIF",
                    "TIF16|tif|1|0=16-Bit TIF",
                    "TIF16BIG|tif|1|0=16-Bit Uncompr. TIF",
                    "openexr|exr|1|0=OpenEXR 16-bit",
                    "openexr_32|exr|1|0=OpenEXR 32-bit",
                    "openexr_tiled|exr|1|0=OpenEXR Tiled 16-bit",
                    "openexr_tiled32|exr|1|0=OpenEXR Tiled 32-bit",
                    "LayeredPSD|psd|0|0=LayeredPSD",
                    "PNGs|png|0|0=Multi-file PNG Layers",
                    "PNGs16|png|0|0=Multi-file 16-bit Layers",
                    "openexrlayers|exr|1|0=Layered OpenEXR 16-bit",
                    "openexrlayers32|exr|1|0=Layered OpenEXR 32-bit")
    formats["7xx"] = ("$FLEX|flx|0|0=Flexible Precision FLX",
                    "$Targa|tga|1|1=Targa",
                    "BMP|BMP|1|1=Windows BMP",
                    "HDR|hdr|0|0=High Dynamic Range HDR",
                    "JP2|jp2|0|0=JPEG 2000",
                    "JP216|jp2|0|0=JPEG 2000 16-Bit",
                    "JP216Lossless|jp2|0|0=JPEG 2000 16-Bit Lossless",
                    "JPG|jpg|1|1=JPEG",
                    "PNG|png|1|0=PNG",
                    "PNG16|png|1|0=PNG 16-bit",
                    "PSD|psd|0|0=PSD",
                    "SGI|SGI|1|0=SGI RGB",
                    "TIF|tif|1|0=TIF",
                    "TIF16|tif|1|0=16-Bit TIF",
                    "TIF16BIG|tif|1|0=16-Bit Uncompr. TIF",
                    "openexr|exr|1|0=OpenEXR 16-bit",
                    "openexr_32|exr|1|0=OpenEXR 32-bit",
                    "openexr_tiled|exr|1|0=OpenEXR Tiled 16-bit",
                    "openexr_tiled32|exr|1|0=OpenEXR Tiled 32-bit",
                    "LayeredPSD|psd|0|0=LayeredPSD",
                    "PNGs|png|0|0=Multi-file PNG Layers",
                    "PNGs16|png|0|0=Multi-file 16-bit Layers",
                    "openexrlayers|exr|1|0=Layered OpenEXR 16-bit",
                    "openexrlayers32|exr|1|0=Layered OpenEXR 32-bit")
    formats["8xx"] = ("$FLEX|flx|0|0=Flexible Precision FLX",
                    "$Targa|tga|1|1=Targa",
                    "BMP|BMP|1|1=Windows BMP",
                    "HDR|hdr|0|0=High Dynamic Range HDR",
                    "JPG|jpg|1|1=JPEG",
                    "PNG|png|1|0=PNG",
                    "PNG16|png|1|0=PNG 16-bit",
                    "PSD|psd|0|0=PSD",
                    "SGI|SGI|1|0=SGI RGB",
                    "TIF|tif|1|0=TIF",
                    "TIF16|tif|1|0=16-Bit TIF",
                    "TIF16BIG|tif|1|0=16-Bit Uncompr. TIF",
                    "openexr|exr|1|0=OpenEXR 16-bit",
                    "openexr_32|exr|1|0=OpenEXR 32-bit",
                    "openexr_tiled|exr|1|0=OpenEXR Tiled 16-bit",
                    "openexr_tiled32|exr|1|0=OpenEXR Tiled 32-bit",
                    "LayeredPSD|psd|0|0=LayeredPSD",
                    "PNGs|png|0|0=Multi-file PNG Layers",
                    "PNGs16|png|0|0=Multi-file 16-bit Layers",
                    "openexrlayers|exr|1|0=Layered OpenEXR 16-bit",
                    "openexrlayers32|exr|1|0=Layered OpenEXR 32-bit")
    formats["9xx"] = ("$FLEX|flx|0|0=Flexible Precision FLX",
                    "$Targa|tga|1|1=Targa",
                    "BMP|BMP|1|1=Windows BMP",
                    "HDR|hdr|0|0=High Dynamic Range HDR",
                    "JPG|jpg|1|1=JPEG",
                    "PNG|png|1|0=PNG",
                    "PNG16|png|1|0=PNG 16-bit",
                    "PSD|psd|0|0=PSD",
                    "SGI|SGI|1|0=SGI RGB",
                    "TIF|tif|1|0=TIF",
                    "TIF16|tif|1|0=16-Bit TIF",
                    "TIF16BIG|tif|1|0=16-Bit Uncompr. TIF",
                    "openexr|exr|1|0=OpenEXR 16-bit",
                    "openexr_32|exr|1|0=OpenEXR 32-bit",
                    "openexr_tiled|exr|1|0=OpenEXR Tiled 16-bit",
                    "openexr_tiled32|exr|1|0=OpenEXR Tiled 32-bit",
                    "LayeredPSD|psd|0|0=LayeredPSD",
                    "PNGs|png|0|0=Multi-file PNG Layers",
                    "PNGs16|png|0|0=Multi-file 16-bit Layers",
                    "openexrlayers|exr|1|0=Layered OpenEXR 16-bit",
                    "openexrlayers32|exr|1|0=Layered OpenEXR 32-bit")
    formats["10xx"] = ( "$FLEX|flx|0|0=Flexible Precision FLX",
                    "$Targa|tga|1|1=Targa",
                    "BMP|BMP|1|1=Windows BMP",
                    "HDR|hdr|0|0=High Dynamic Range HDR",
                    "JPG|jpg|1|1=JPEG",
                    "PNG|png|1|0=PNG",
                    "PNG16|png|1|0=PNG 16-bit",
                    "PSD|psd|0|0=PSD",
                    "SGI|SGI|1|0=SGI RGB",
                    "TIF|tif|1|0=TIF",
                    "TIF16|tif|1|0=16-Bit TIF",
                    "TIF16BIG|tif|1|0=16-Bit Uncompr. TIF",
                    "openexr|exr|1|0=OpenEXR 16-bit",
                    "openexr_32|exr|1|0=OpenEXR 32-bit",
                    "openexr_tiled|exr|1|0=OpenEXR Tiled 16-bit",
                    "openexr_tiled32|exr|1|0=OpenEXR Tiled 32-bit",
                    "LayeredPSD|psd|0|0=LayeredPSD",
                    "PNGs|png|0|0=Multi-file PNG Layers",
                    "PNGs16|png|0|0=Multi-file 16-bit Layers",
                    "openexrlayers|exr|1|0=Layered OpenEXR 16-bit",
                    "openexrlayers32|exr|1|0=Layered OpenEXR 32-bit")
    formats["11xx"] = ( "$FLEX|flx|0|0=Flexible Precision FLX",
                    "$Targa|tga|1|1=Targa",
                    "BMP|BMP|1|1=Windows BMP",
                    "HDR|hdr|0|0=High Dynamic Range HDR",
                    "JPG|jpg|1|1=JPEG",
                    "PNG|png|1|0=PNG",
                    "PNG16|png|1|0=PNG 16-bit",
                    "PSD|psd|0|0=PSD",
                    "SGI|SGI|1|0=SGI RGB",
                    "TIF|tif|1|0=TIF",
                    "TIF16|tif|1|0=16-Bit TIF",
                    "TIF16BIG|tif|1|0=16-Bit Uncompr. TIF",
                    "openexr|exr|1|0=OpenEXR 16-bit",
                    "openexr_32|exr|1|0=OpenEXR 32-bit",
                    "openexr_tiled|exr|1|0=OpenEXR Tiled 16-bit",
                    "openexr_tiled32|exr|1|0=OpenEXR Tiled 32-bit",
                    "LayeredPSD|psd|0|0=LayeredPSD",
                    "PNGs|png|0|0=Multi-file PNG Layers",
                    "PNGs16|png|0|0=Multi-file 16-bit Layers",
                    "openexrlayers|exr|1|0=Layered OpenEXR 16-bit",
                    "openexrlayers32|exr|1|0=Layered OpenEXR 32-bit")
    formats["12xx"] = ( "$FLEX|flx|0|0=Flexible Precision FLX",
                    "$Targa|tga|1|1=Targa",
                    "BMP|BMP|1|1=Windows BMP",
                    "HDR|hdr|0|0=High Dynamic Range HDR",
                    "JPG|jpg|1|1=JPEG",
                    "PNG|png|1|0=PNG",
                    "PNG16|png|1|0=PNG 16-bit",
                    "PSD|psd|0|0=PSD",
                    "SGI|SGI|1|0=SGI RGB",
                    "TIF|tif|1|0=TIF",
                    "TIF16|tif|1|0=16-Bit TIF",
                    "TIF16BIG|tif|1|0=16-Bit Uncompr. TIF",
                    "openexr|exr|1|0=OpenEXR 16-bit",
                    "openexr_32|exr|1|0=OpenEXR 32-bit",
                    "openexr_tiled|exr|1|0=OpenEXR Tiled 16-bit",
                    "openexr_tiled32|exr|1|0=OpenEXR Tiled 32-bit",
                    "LayeredPSD|psd|0|0=LayeredPSD",
                    "PNGs|png|0|0=Multi-file PNG Layers",
                    "PNGs16|png|0|0=Multi-file 16-bit Layers",
                    "openexrlayers|exr|1|0=Layered OpenEXR 16-bit",
                    "openexrlayers32|exr|1|0=Layered OpenEXR 32-bit")  
    
    version = scriptDialog.GetValue( "VersionBox" )
    currentFormat = scriptDialog.GetValue( "FormatBox" )
    
    outputFormatsList = []
    outputFormats = dict()
    outputFormatsByFormat = dict()
    for line in formats[version]:
        keyValue = line.split( "=" )
        outputFormatsList.append( keyValue[1] )
        outputFormats[keyValue[1]] = keyValue[0]
        
        outputFormatParts = keyValue[0].split( "|" )
        outputFormatName = outputFormatParts[0]
        outputFormatsByFormat[outputFormatName] = keyValue[0]
    
    scriptDialog.SetItems( "FormatBox", tuple( outputFormatsList ) )
    if len( outputFormatsList ) > 0:
        if currentFormat in outputFormatsList:
            scriptDialog.SetValue( "FormatBox", currentFormat )
        else:            
            scriptDialog.SetValue( "FormatBox", outputFormatsList[0] )

def VersionBoxChanged( *args ):
    global scriptDialog
    
    # Pass option only available in 6xx and later.
    version = GetModoVersion()
    scriptDialog.SetEnabled( "PassLabel", version >= 6 ) 
    scriptDialog.SetEnabled( "PassBox", version >= 6 ) 
    scriptDialog.SetEnabled( "PatternLabel", version >= 6 ) 
    scriptDialog.SetEnabled( "PatternBox", version >= 6 ) 
    
    SetVersionOutputFormats()

def OutputBoxChanged( *args ):
    global scriptDialog
    global outputFormats
    
    outputSpecified = ( len(scriptDialog.GetValue( "OutputBox" ).strip()) > 0 )
    prefixSpecified = ( len(scriptDialog.GetValue( "PrefixBox" ).strip()) > 0 )
    tileRendering = scriptDialog.GetValue( "TileRenderingBox" )
    submitAssembly = scriptDialog.GetValue( "TileDependentBox" )
    version = GetModoVersion()

    outputFormatValue = outputFormats[ scriptDialog.GetValue( "FormatBox" ) ]
    supportsAssembly = (outputFormatValue.split( "|" )[2] == "1")
    
    scriptDialog.SetEnabled( "FormatLabel", outputSpecified )
    scriptDialog.SetEnabled( "FormatBox", outputSpecified )
    scriptDialog.SetEnabled( "PrefixLabel", outputSpecified )
    scriptDialog.SetEnabled( "PrefixBox", outputSpecified )
    scriptDialog.SetEnabled( "PatternLabel", outputSpecified and version >= 6 )
    scriptDialog.SetEnabled( "PatternBox", outputSpecified and version >= 6 )
    
    scriptDialog.SetEnabled( "TileRenderingBox", outputSpecified and prefixSpecified and supportsAssembly )
    scriptDialog.SetEnabled( "TileFrameLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TileFrameBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TilesInXLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TilesInXBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TileDependentBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering )
    scriptDialog.SetEnabled( "TilesInYLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TilesInYBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TileCleanUpBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering and submitAssembly )
    scriptDialog.SetEnabled( "ErrorOnMissingBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering and submitAssembly)

def PrefixBoxChanged( *args ):
    global scriptDialog
    global outputFormats
    
    outputSpecified = ( len(scriptDialog.GetValue( "OutputBox" ).strip()) > 0 )
    prefixSpecified = ( len(scriptDialog.GetValue( "PrefixBox" ).strip()) > 0 )
    tileRendering = scriptDialog.GetValue( "TileRenderingBox" )
    submitAssembly = scriptDialog.GetValue( "TileDependentBox" )
    
    outputFormatValue = outputFormats[ scriptDialog.GetValue( "FormatBox" ) ]
    supportsAssembly = (outputFormatValue.split( "|" )[2] == "1")
    
    scriptDialog.SetEnabled( "TileRenderingBox", outputSpecified and prefixSpecified and supportsAssembly )
    scriptDialog.SetEnabled( "TileFrameLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TileFrameBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TilesInXLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TilesInXBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TileDependentBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering )
    scriptDialog.SetEnabled( "TilesInYLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TilesInYBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
    scriptDialog.SetEnabled( "TileCleanUpBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering and submitAssembly )
    scriptDialog.SetEnabled( "ErrorOnMissingBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering and submitAssembly)

def FormatBoxChanged( *args ):
    global scriptDialog
    global outputFormats
    
    outputSpecified = ( len(scriptDialog.GetValue( "OutputBox" ).strip()) > 0 )
    prefixSpecified = ( len(scriptDialog.GetValue( "PrefixBox" ).strip()) > 0 )
    tileRendering = scriptDialog.GetValue( "TileRenderingBox" )
    submitAssembly = scriptDialog.GetValue( "TileDependentBox" )
    
    formatBoxValue = scriptDialog.GetValue( "FormatBox" )
    if formatBoxValue != None and formatBoxValue != "":
        outputFormatValue = outputFormats[ formatBoxValue ]
        supportsAssembly = (outputFormatValue.split( "|" )[2] == "1")
        
        scriptDialog.SetEnabled( "TileRenderingBox", outputSpecified and prefixSpecified and supportsAssembly )
        scriptDialog.SetEnabled( "TileFrameLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TileFrameBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TilesInXLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TilesInXBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TileDependentBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering )
        scriptDialog.SetEnabled( "TilesInYLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TilesInYBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TileCleanUpBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering and submitAssembly )
        scriptDialog.SetEnabled( "ErrorOnMissingBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering and submitAssembly)
        
def TileRenderingChanged( *args ):
    global scriptDialog
    global outputFormats
    
    outputSpecified = ( len(scriptDialog.GetValue( "OutputBox" ).strip()) > 0 )
    prefixSpecified = ( len(scriptDialog.GetValue( "PrefixBox" ).strip()) > 0 )
    tileRendering = scriptDialog.GetValue( "TileRenderingBox" )
    submitAssembly = scriptDialog.GetValue( "TileDependentBox" )
    
    formatBoxValue = scriptDialog.GetValue( "FormatBox" )
    if formatBoxValue != None and formatBoxValue != "":
        outputFormatValue = outputFormats[ formatBoxValue ]
        supportsAssembly = (outputFormatValue.split( "|" )[2] == "1")
        
        scriptDialog.SetEnabled( "TileRenderingBox", outputSpecified and prefixSpecified and supportsAssembly )
        scriptDialog.SetEnabled( "TileFrameLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TileFrameBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TilesInXLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TilesInXBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TileDependentBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering )
        scriptDialog.SetEnabled( "TilesInYLabel", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TilesInYBox", outputSpecified and prefixSpecified and tileRendering and supportsAssembly )
        scriptDialog.SetEnabled( "TileCleanUpBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering and submitAssembly )
        scriptDialog.SetEnabled( "ErrorOnMissingBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering and submitAssembly)
    
def TileDependentChanged( *args ):
    global scriptDialog
    global outputFormats
    
    outputSpecified = ( len(scriptDialog.GetValue( "OutputBox" ).strip()) > 0 )
    prefixSpecified = ( len(scriptDialog.GetValue( "PrefixBox" ).strip()) > 0 )
    tileRendering = scriptDialog.GetValue( "TileRenderingBox" )
    submitAssembly = scriptDialog.GetValue( "TileDependentBox" )
    
    formatBoxValue = scriptDialog.GetValue( "FormatBox" )
    if formatBoxValue != None and formatBoxValue != "":
        outputFormatValue = outputFormats[ formatBoxValue ]
        supportsAssembly = (outputFormatValue.split( "|" )[2] == "1")
    
        scriptDialog.SetEnabled( "TileCleanUpBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering and submitAssembly )
        scriptDialog.SetEnabled( "ErrorOnMissingBox", outputSpecified and prefixSpecified and supportsAssembly and tileRendering and submitAssembly)

def GetPaddingSize():
    global scriptDialog
    
    outputPattern = scriptDialog.GetValue( "PatternBox" )
    paddingMatch = re.search( "<(F+)>", outputPattern, re.S )
    if paddingMatch:
        return len(paddingMatch.group(1))
    else:
        return 0
        
def GetPadding():
    paddingSize = GetPaddingSize()
    padding = ""
    while len(padding) < paddingSize:
        padding = padding + "#"
    return padding

def GetModoVersion():
    global scriptDialog
    fullVersion = scriptDialog.GetValue( "VersionBox" )
    xLocation = fullVersion.find('x')
    if xLocation < 0:
        xLocation = None
    version = int( fullVersion[ :xLocation ] )
    return version

def WriteIntegrationSettings( writer, groupBatch, requireOverride = False ):
    # Integration
    extraKVPIndex = 0

    if integration_dialog.IntegrationProcessingRequested():
        extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
        groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()
    
    if requireOverride:
        tileFrame = scriptDialog.GetValue( "TileFrameBox" )
        writer.WriteLine( "ExtraInfoKeyValue%d=FrameRangeOverride=%d\n" % ( extraKVPIndex, tileFrame ) )

    return groupBatch        

def SubmitButtonPressed( *args ):
    global scriptDialog
    global outputFormats
    global outputFormatsByFormat
    global outputFileNamesFromScene
    global integration_dialog
    
    warnings = ""
    errors = ""
    # Check if Modo file exists.
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        errors +=  "modo file %s does not exist.\n\n" % sceneFile
    elif (not scriptDialog.GetValue("SubmitSceneBox") and PathUtils.IsPathLocal(sceneFile)):
        warnings += "modo file %s is local and is not being submitted with the job.\n\n" % sceneFile
    
    # Check output file if necessary
    outputFolder = scriptDialog.GetValue( "OutputBox" ).strip()
    outputPrefix = ""
    outputExtension = ""
    outputFormat = ""
    outputSupportsAssembly = False
    assemblyUsesOpaqueOpacity = False
    
    if len(outputFolder) > 0:
        if not Directory.Exists( outputFolder ):
            errors += "Output folder %s does not exist.\n\n" % outputFolder
        elif PathUtils.IsPathLocal(outputFolder):
            warnings += "Output folder %s is local.\n\n" % outputFolder
        
        outputPrefix = scriptDialog.GetValue( "PrefixBox" ).strip()
        if len(outputPrefix) == 0:
            errors += "When specifying an output folder, you must also specify an output file prefix.\n\n"
        
        outputFormatValue = outputFormats[ scriptDialog.GetValue( "FormatBox" ) ]
        formatParts = outputFormatValue.split( "|" )
        outputFormat = formatParts[0]
        outputExtension = "." + formatParts[1]
        outputSupportsAssembly = (formatParts[2] == "1")
        assemblyUsesOpaqueOpacity = (formatParts[3] == "1")
    
    tileRendering = scriptDialog.GetValue( "TileRenderingBox" )
    if tileRendering and (len(outputFolder) == 0 or len(outputPrefix) == 0):
        errors += "You must specify an output folder and file prefix to enable Tile Rendering.\n\n"
        
    tileDependent = scriptDialog.GetValue( "TileDependentBox" )
    tileFrame = int(scriptDialog.GetValue( "TileFrameBox" ))
    tilesInX = int(scriptDialog.GetValue( "TilesInXBox" ))
    tilesInY = int(scriptDialog.GetValue( "TilesInYBox" ))
    tileCount = tilesInX * tilesInY
    
    taskLimit = RepositoryUtils.GetJobTaskLimit()
    if tileCount > taskLimit:
        errors += "Unable to submit job with " + (str(tileCount)) + " tasks.  Task Count exceeded Job Task Limit of "+str(taskLimit) + ".\n\n"
    
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not tileRendering and not FrameUtils.FrameRangeValid( str(frames) ) ):
        errors += "Frame range %s is not valid.\n\n" % str(frames)
        
    passGroup = scriptDialog.GetValue( "PassBox" )
        
    # Check if Integration options are valid
    if not integration_dialog.CheckIntegrationSanity( outputFolder ):
        return
    
    if len( errors ) > 0:
        errors = "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % errors
        scriptDialog.ShowMessageBox( errors, "Error" )
        return

    if len( warnings ) > 0:
        warnings = "Warnings:\n\n%s\nAre you sure you want to continue?\n" % warnings
        result = scriptDialog.ShowMessageBox( warnings, "Warning", ("Yes","No") )
        if result == "No":
            return
    
    jobName = scriptDialog.GetValue( "NameBox" )
    groupBatch = False
    
    if tileRendering and outputSupportsAssembly and tileDependent:
        groupBatch=True

    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "modo_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Modo" )
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
    writer.WriteLine( "ForceReloadPlugin=%s" % (scriptDialog.GetValue( "VRayBox" ) and tileRendering ) )
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    
    if len(outputFolder) > 0:
        if outputFormat != "PNGs" and outputFormat != "PNGs16":
            padding = GetPadding()
            
            if tileRendering:
                currTile = 0
                for y in range( 0, tilesInY ):
                    for x in range( 0, tilesInX ):
                        tilePrefix = "_tile_%sx%s_%sx%s_" % (x+1,y+1,tilesInX,tilesInY)
                        tileFilename = Path.Combine( outputFolder, outputPrefix + tilePrefix + padding + outputExtension )
                        writer.WriteLine( "OutputFilename0Tile%s=%s" % (currTile, tileFilename) )
                        currTile = currTile + 1
            else:
                writer.WriteLine( "OutputFilename0=%s" % Path.Combine( outputFolder, outputPrefix + padding + outputExtension ) )
        else:
            writer.WriteLine( "OutputDirectory0=%s" % outputFolder )
            
    elif outputFileNamesFromScene and len(outputFileNamesFromScene) > 0:
        # Note that outputFileNamesFromScene is only populated when submitting from within modo
        outputIndex = 0
        
        for i in range( 0, len(outputFileNamesFromScene), 2 ):
            currOutputFileName = outputFileNamesFromScene[i]
            currOutputFolder = Path.GetDirectoryName( currOutputFileName )
            currOutputPrefix = Path.GetFileName( currOutputFileName )
            
            currOutputFormatName = outputFileNamesFromScene[i+1]
            if currOutputFormatName in outputFormatsByFormat:
                currOutputFormatValue = outputFormatsByFormat[ currOutputFormatName ]
                currFormatParts = currOutputFormatValue.split( "|" )
                currOutputFormat = currFormatParts[0]
                currOutputExtension = "." + currFormatParts[1]
                currOutputSupportsAssembly = (currFormatParts[2] == "1")
                currAssemblyUsesOpaqueOpacity = (currFormatParts[3] == "1")
                
                if currOutputFormat != "PNGs" and currOutputFormat != "PNGs16":
                    padding = GetPadding()
                    if tileRendering:
                        padding = StringUtils.ToZeroPaddedString( tileFrame, GetPaddingSize(), False )
                    
                    writer.WriteLine( "OutputFilename%s=%s" % (outputIndex, Path.Combine( currOutputFolder, currOutputPrefix + padding + currOutputExtension )) )
                    outputIndex = outputIndex + 1
        
    if tileRendering and outputSupportsAssembly:
        writer.WriteLine("TileJob=True")
        writer.WriteLine("TileJobFrame=%s" % tileFrame)
        writer.WriteLine("TileJobTilesInX=%s" % tilesInX)
        writer.WriteLine("TileJobTilesInY=%s" % tilesInY)
    else:
        writer.WriteLine("Frames=" + str(frames))
        writer.WriteLine("ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox"))
    
    if not( tileRendering and outputSupportsAssembly and tileDependent ):
        groupBatch = WriteIntegrationSettings( writer, groupBatch )
    
    if groupBatch:
        writer.WriteLine( "BatchName=%s\n" % (jobName ) ) 
    writer.Close()
    
    version = scriptDialog.GetValue( "VersionBox" )
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "modo_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Version=%s" % version )
    writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
    writer.WriteLine( "Threads=%s" % scriptDialog.GetValue( "ThreadsBox" ) )
    writer.WriteLine( "PassGroup=%s" % passGroup )
    writer.WriteLine( "VRayRender=%s" % scriptDialog.GetValue( "VRayBox" ) )
    writer.WriteLine( "ProjectDirectory=%s" % scriptDialog.GetValue( "ProjectBox" ) )
    
    
    if( not scriptDialog.GetValue("SubmitSceneBox") ):
        writer.WriteLine( "SceneFile=" + sceneFile )
    else:
        writer.WriteLine( "SceneDirectory=" + os.path.dirname(sceneFile) )
        
    if tileRendering:       
        xPercentage = 100.0 / tilesInX
        yPercentage = 100.0 / tilesInY
        
        currTile = 0
        for y in range( 0, tilesInY ):
            for x in range( 0, tilesInX ):
                left = float(x) * xPercentage
                right = float((x+1)) * xPercentage
                if (x+1) == tilesInX:
                    right = 100.0
                
                top = float(y) * yPercentage
                bottom = float(y+1) * yPercentage
                if (y+1) == tilesInY:
                    bottom = 100.0
                
                tilePrefix = "_tile_%sx%s_%sx%s_" % (x+1,y+1,tilesInX,tilesInY)
                tileFilename = Path.Combine( outputFolder, outputPrefix + tilePrefix )
                
                writer.WriteLine( "RegionLeft%s=%s" % (currTile,left) )
                writer.WriteLine( "RegionRight%s=%s" % (currTile,right) )
                writer.WriteLine( "RegionTop%s=%s" % (currTile,top) )
                writer.WriteLine( "RegionBottom%s=%s" % (currTile,bottom) )
                writer.WriteLine( "RegionFilename%s=%s" % (currTile,tileFilename) )
                
                currTile = currTile + 1
                
        writer.WriteLine( "RegionFormat=%s" % outputFormat )
        writer.WriteLine( "OutputPattern=%s" % scriptDialog.GetValue( "PatternBox" ) )
    else:
        if len(outputFolder) > 0:
            writer.WriteLine( "OutputFilename=%s" % Path.Combine( outputFolder, outputPrefix ) )
            writer.WriteLine( "OutputFormat=%s" % outputFormat )
            writer.WriteLine( "OutputPattern=%s" % scriptDialog.GetValue( "PatternBox" ) )
        
    writer.Close()
    currentDateTime = datetime.datetime.now()
    tileJobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "tile_job_info.job" )
    tilePluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "tile_plugin_info.job" )
    draftConfigFilename = ""
    
    # Create tile assembly job and plugin info file if necessary
    if tileRendering and outputSupportsAssembly and tileDependent:
        tileJobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "draft_tile_job_info.job" )
        tilePluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "draft_tile_plugin_info.job" )
        draftConfigFilename = Path.Combine( outputFolder, outputPrefix + padding+"_config_{0:%y}_{0:%m}_{0:%d}_{0:%H}_{0:%M}_{0:%S}.txt".format(currentDateTime))
        
        paddingSize = GetPaddingSize()
        padding = StringUtils.ToZeroPaddedString( tileFrame, paddingSize, False )
        paddedOutputFilename = Path.Combine( outputFolder, outputPrefix + padding + outputExtension )
        
        writer = StreamWriter( tileJobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=DraftTileAssembler" )
        writer.WriteLine( "Name=" + jobName + " (Frame " + str(tileFrame) + " - Tile Assembly Job)" )
        writer.WriteLine( "BatchName=%s\n" % (jobName ) ) 
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        writer.WriteLine( "Frames=0" )
        writer.WriteLine( "ChunkSize=1" )
        writer.WriteLine( "MachineLimit=1" )
        writer.WriteLine( "OutputFilename0=%s" % paddedOutputFilename )

        WriteIntegrationSettings( writer, True, True )

        writer.Close()
        
        writer = StreamWriter( tilePluginInfoFilename, False, Encoding.Unicode )
        writer.WriteLine("ErrorOnMissing="+str(scriptDialog.GetValue( "ErrorOnMissingBox" )))
        writer.WriteLine( "CleanupTiles=%s" % scriptDialog.GetValue( "TileCleanUpBox" ) )
        writer.Close()
        
        writer = StreamWriter( draftConfigFilename, False, Encoding.Unicode )
        writer.WriteLine("")
        writer.WriteLine("TileCount=%s" % tileCount)
        writer.WriteLine("ImageFolder=%s" % outputFolder)
        writer.WriteLine("ImagePadding=%s" % paddingSize)
        writer.WriteLine("ImageExtension=%s" % outputExtension)
        writer.WriteLine("TilesCropped=False")
        currTile = 0
        writer.WriteLine("DistanceAsPixels=False")
        for y in range( 0, tilesInY ):
            for x in range( 0, tilesInX ):
                
                left = float(x) * float(xPercentage)/100.0
                bottom = float(y+1) * float(yPercentage)/100.0
                if (y+1) == tilesInY:
                    bottom = 1.0
                
                bottom = 1.0 - bottom
            
                tilePrefix = "_tile_%sx%s_%sx%s_" % (x+1,y+1,tilesInX,tilesInY)
                tileFilePrefix = outputPrefix + tilePrefix
            
                writer.WriteLine( "Tile%sPrefix=%s" % (currTile,tileFilePrefix) )
                writer.WriteLine( "Tile%sX=%f" % (currTile,left) )
                writer.WriteLine( "Tile%sY=%f" % (currTile,bottom) )
                writer.WriteLine( "Tile%sHeight=%f" % (currTile,yPercentage/100.0) )
                writer.WriteLine( "Tile%sWidth=%f" % (currTile,xPercentage/100.0) )
                currTile = currTile + 1
             
        writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    if tileRendering and tileDependent:
        arguments.Add( "-multi" )
        arguments.Add( "-dependent" )
        arguments.Add( "-job" )
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( sceneFile )
    
    if tileRendering and outputSupportsAssembly and tileDependent:
        arguments.Add( "-job" )
        arguments.Add( tileJobInfoFilename )
        arguments.Add( tilePluginInfoFilename )
        arguments.Add( draftConfigFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )

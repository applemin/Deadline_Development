from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

import os
import clr

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
presetSettings = None
startup = True
updatingOutputFile = False

#Operations
MSOP_AnimationRender = "Animation Render"
MSOP_SingleViewRender = "Single View Render"
MSOP_SaveMultipleImages = "Save Multiple Images"
MSOP_FileExport = "File Export"
MSOP_Print = "Print"
MSOP_Script = "Run Script"

#Export Modes
EX_VisibleEdges = "Visible Edges"
EX_Luxology = "Luxology"
EX_Autodesk = "DWG / DXF"
EX_SAT = "ACIS SAT"
EX_FlatDGN = "Flat DGN"

#Render Modes
RM_Luxology ="Luxology"
RM_Wireframe = "Wireframe"
RM_Edge = "Visible Edge"
RM_FilledEdge = "Filled Visible Edge"
RM_Smooth = "Smooth"

#Color Modes
CL_RGB = "RGB"
CL_Grayscale = "Grayscale"
CL_256 = "256 Colors"
CL_16 = "16 Colors"
CL_Monochrome = "Monochrome"

MicroStationOperations = [ MSOP_AnimationRender, MSOP_SingleViewRender, MSOP_FileExport, MSOP_SaveMultipleImages, MSOP_Print, MSOP_Script ]
ExportModes = [ EX_Luxology, EX_Autodesk, EX_SAT, EX_VisibleEdges, EX_FlatDGN ]
RenderModes = [ RM_Luxology, RM_Wireframe, RM_Edge, RM_FilledEdge, RM_Smooth ]
ColorModels = [ CL_RGB, CL_Grayscale, CL_256, CL_16, CL_Monochrome ]

curRenderMode = RM_Luxology
curExportMode = EX_Luxology

suppressEvents = False

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global presetSettings
    global startup
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit MicroStation Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'MicroStation' ) )

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
    
    scriptDialog.AddTabPage("Microstation Options")
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "MicroStation Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "OperationLabel", "LabelControl", "Operation", 1, 0, "The operation that will be performed in this MicroStation job.", False )
    operationControl = scriptDialog.AddComboControlToGrid( "OperationBox", "ComboControl", MSOP_AnimationRender, MicroStationOperations, 1, 1, expand=True )
    operationControl.ValueModified.connect( OperationChanged )

    scriptDialog.AddControlToGrid( "ColorLabel", "LabelControl", "Color Model", 1, 2, "The type of Color to use for the render output.", False )
    scriptDialog.AddComboControlToGrid( "ColorBox", "ComboControl", CL_RGB, ColorModels, 1, 3, expand=True )

    scriptDialog.AddControlToGrid( "ModeLabel", "LabelControl", "Mode", 2, 0, "The mode which applies to the selected operation.", False )
    modeControl = scriptDialog.AddComboControlToGrid( "ModeBox", "ComboControl", RM_Luxology, RenderModes, 2, 1, expand=True )
    modeControl.ValueModified.connect( ModeChanged )

    scriptDialog.AddSelectionControlToGrid( "SubmitFileBox", "CheckBoxControl", False, "Submit File(s) With Job", 2, 2, "If enabled, the design (and/or settings) file will be submitted to the Deadline Repository along with the Job.", colSpan=2 )
    
    scriptDialog.AddControlToGrid( "DesignLabel", "LabelControl", "Design File(s)", 3, 0, "The path to the MicroStation Design File(s), or SMI Script to use for this Job.", False )
    inputBox = scriptDialog.AddSelectionControlToGrid( "DesignBox", "MultiFileBrowserControl", "", "MicroStation DGN File (*.dgn);;All Files (*)", 3, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "SettingsLabel", "LabelControl", "Settings File", 4, 0, "The operation-specific Settings file for this Job.", False )
    settingsControl = scriptDialog.AddSelectionControlToGrid( "SettingsBox", "FileBrowserControl", "", "Save Multiple Script Files (*.sm);;Print Definition Files (*.pset);;DWG Settings Files (*.dws);;Script File (*.scr);;Script File As Text (*.txt);;Visual Basic File (*.mvba);;All Files (*)", 4, 1, colSpan=3 )
    settingsControl.ValueModified.connect( UpdateUIStatus )

    # add GUI options for .mvba right here. (Module and Subm)
    scriptDialog.AddControlToGrid( "ModuleLabel", "LabelControl", "Module (.mvba)", 5, 0, "The name of the Module to use within the selected .mvba project file.", False )
    scriptDialog.AddControlToGrid( "ModuleBox", "TextControl", "", 5, 1 )
    scriptDialog.AddControlToGrid( "SubModuleLabel", "LabelControl", "Sub/Function (.mvba)", 5, 2, "The name of the Submodule to use within the specified module.", False )
    scriptDialog.AddControlToGrid( "SubModuleBox", "TextControl", "", 5, 3 )
    scriptDialog.AddControlToGrid( "KeyinLabel", "LabelControl", "Key-in Args (.mvba)", 6, 0, "Any additional arguments to pass to the .mvba script.", False )
    scriptDialog.AddControlToGrid( "KeyinBox", "TextControl", "", 6, 1 )
    scriptDialog.AddControlToGrid( "ViewLabel", "LabelControl", "View Number", 7, 0, "The view number on which to perform the operation.", False )
    scriptDialog.AddRangeControlToGrid( "ViewBox", "RangeControl", 1, 1, 8, 0, 1, 7, 1 )

    scriptDialog.AddControlToGrid( "SavedViewLabel", "LabelControl", "View Name", 7, 2, "The name of the Saved View or View Group to apply before rendering.", False )
    scriptDialog.AddControlToGrid( "SavedViewBox", "TextControl", "", 7, 3, expand=True)

    scriptDialog.AddControlToGrid( "XLabel", "LabelControl", "Output Size X", 8, 0, "The X component of the output size. Set to 0 to use current value, or maintain aspect ratio.", False )
    scriptDialog.AddRangeControlToGrid( "XBox", "RangeControl", 0, 0, 999999999, 0, 1, 8, 1 )
    scriptDialog.AddControlToGrid( "YLabel", "LabelControl", "Output Size Y", 8, 2, "The Y component of the output size. Set to 0 to use current value, or maintain aspect ratio.", False )
    scriptDialog.AddRangeControlToGrid( "YBox", "RangeControl", 0, 0, 999999999, 0, 1, 8, 3 )

    scriptDialog.AddControlToGrid( "EnvironmentLabel", "LabelControl", "Environment", 9, 0, "The name of the Environment Setup to use for rendering.", False )
    scriptDialog.AddControlToGrid( "EnvironmentBox", "TextControl", "", 9, 1 )
    scriptDialog.AddControlToGrid( "RenderSetupLabel", "LabelControl", "Render Setup", 9, 2, "The name of the Render Setup to use.", False )
    scriptDialog.AddControlToGrid( "RenderSetupBox", "TextControl", "", 9, 3 )
    
    scriptDialog.AddControlToGrid( "LightSetupLabel", "LabelControl", "Light Setup", 10, 0, "The name of the Light Setup to use for rendering.", False )
    scriptDialog.AddControlToGrid( "LightSetupBox", "TextControl", "", 10, 1 )
    
    scriptDialog.AddControlToGrid( "FrameLabel", "LabelControl", "Frame List", 11, 0, "The list of Frames to render.", False )
    scriptDialog.AddControlToGrid( "FrameBox", "TextControl", "", 11, 1 )
    scriptDialog.AddControlToGrid( "ChunkLabel", "LabelControl", "Task Size", 11, 2, "The number of Frames (or items) that will be processed at a time for each Task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkBox", "RangeControl", 1, 1, 9999, 0, 1, 11, 3 )

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Path", 12, 0, "The path to the output file for this Job. File type will vary based on the selected Operation and Mode.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "", "All Files (*)", 12, 1, colSpan=3 )

    scriptDialog.AddSelectionControlToGrid( "ConvertToUNCBox", "CheckBoxControl", False, "Convert Network Paths to UNC", 13, 1, "If enabled, Deadline will attempt to replace Mapped Network Drives with UNC Paths.", colSpan=3 )

    scriptDialog.AddSelectionControlToGrid( "DgnReadOnlyBox", "CheckBoxControl", True, "Submit .dgn Scene as Read-Only", 14, 1, "If enabled, Deadline will submit the selected .dgn scene as read-only.", colSpan=3 )



    scriptDialog.EndGrid()

    scriptDialog.EndTabPage()
    scriptDialog.EndTabControl()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 2, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 3, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ("DepartmentBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","LimitGroupBox","OnJobCompleteBox","MachineListBox","SubmitSuspendedBox","IsBlacklistBox",
            "OperationBox","ColorBox","ViewBox","OutputBox","XBox","YBox","SavedViewBox","EnvironmentBox","RenderSetupBox","LightSetupBox","ModeBox","SettingsBox","DesignBox",
            "FrameBox","ChunkBox","ConvertToUNCBox","DgnReadOnlyBox","ModuleBox","SubModuleBox","KeyinBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    UpdateUIStatus()

    scriptDialog.ShowDialog( True )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "MicroStationSettings.ini" )

def OperationChanged( source ):
    global curRenderMode
    global curExportMode
    global scriptDialog
    global suppressEvents

    operation = scriptDialog.GetValue( "OperationBox" )

    suppressEvents = True
    if operation == MSOP_FileExport:
        scriptDialog.SetItems( "ModeBox", ExportModes )
        scriptDialog.SetValue( "ModeBox", curExportMode )
    else:
        scriptDialog.SetItems( "ModeBox", RenderModes )
        scriptDialog.SetValue( "ModeBox", curRenderMode )
    suppressEvents = False

    UpdateUIStatus()

def ModeChanged( source ):
    global curRenderMode
    global curExportMode
    global scriptDialog
    global suppressEvents

    if suppressEvents:
        return

    operation = scriptDialog.GetValue( "OperationBox" )
    newMode = scriptDialog.GetValue( "ModeBox" )

    if operation == MSOP_FileExport:
        curExportMode = newMode
    else:
        curRenderMode = newMode

    UpdateUIStatus()

def UpdateUIStatus():
    global scriptDialog

    newOperation = scriptDialog.GetValue( "OperationBox" )
    newMode = scriptDialog.GetValue( "ModeBox" )

    output = False
    view = False
    frames = False
    chunkSize = False
    luxology = False
    mode = False
    size = False
    settingsFile = False
    color = False
    design = False
    mvba = False

    #true for everything so far
    submitFile = True
    readOnlyCheck = True

    if newOperation == MSOP_SaveMultipleImages:
        chunkSize = True
        settingsFile = True
        readOnlyCheck = False

    elif newOperation == MSOP_FileExport:
        output = True
        mode = True
        design = True

        if newMode == EX_VisibleEdges:
            view = True
        elif newMode == EX_Autodesk:
            settingsFile = True

    elif newOperation == MSOP_AnimationRender:
        design = True
        output = True
        view = True
        frames = True
        chunkSize = True
        mode = True
        size = True
        color = True

        if newMode == RM_Luxology:
            luxology = True

    elif newOperation == MSOP_SingleViewRender:
        design = True
        output = True
        view = True
        mode = True
        size = True
        color = True

        if newMode == RM_Luxology:
            luxology = True

    elif newOperation == MSOP_Print:
        design = True
        output = True
        settingsFile = True

    elif newOperation == MSOP_Script:
        design = True
        settingsFile = True
        mvba = str(scriptDialog.GetValue( "SettingsBox" )).endswith( ".mvba" )



    #Set Enabledness
    scriptDialog.SetEnabled( "DesignLabel", design )
    scriptDialog.SetEnabled( "DesignBox", design )

    scriptDialog.SetEnabled( "ModuleLabel", mvba )
    scriptDialog.SetEnabled( "ModuleBox", mvba )
    scriptDialog.SetEnabled( "SubModuleLabel", mvba )
    scriptDialog.SetEnabled( "SubModuleBox", mvba )
    scriptDialog.SetEnabled( "KeyinLabel", mvba )
    scriptDialog.SetEnabled( "KeyinBox", mvba )

    scriptDialog.SetEnabled( "ViewLabel", view )
    scriptDialog.SetEnabled( "ViewBox", view )
    scriptDialog.SetEnabled( "SavedViewLabel", view )
    scriptDialog.SetEnabled( "SavedViewBox", view )   

    scriptDialog.SetEnabled( "OutputLabel", output )
    scriptDialog.SetEnabled( "OutputBox", output )

    scriptDialog.SetEnabled( "FrameLabel", frames )
    scriptDialog.SetEnabled( "FrameBox", frames )

    scriptDialog.SetEnabled( "ChunkLabel", chunkSize )
    scriptDialog.SetEnabled( "ChunkBox", chunkSize )

    scriptDialog.SetEnabled( "EnvironmentLabel", luxology )
    scriptDialog.SetEnabled( "EnvironmentBox", luxology )
    scriptDialog.SetEnabled( "RenderSetupLabel", luxology )
    scriptDialog.SetEnabled( "RenderSetupBox", luxology )
    scriptDialog.SetEnabled( "LightSetupLabel", luxology )
    scriptDialog.SetEnabled( "LightSetupBox", luxology )

    scriptDialog.SetEnabled( "ModeLabel", mode )
    scriptDialog.SetEnabled( "ModeBox", mode )

    scriptDialog.SetEnabled( "SubmitFileBox", submitFile )

    scriptDialog.SetEnabled( "XLabel", size )
    scriptDialog.SetEnabled( "XBox", size )
    scriptDialog.SetEnabled( "YLabel", size )
    scriptDialog.SetEnabled( "YBox", size )

    scriptDialog.SetEnabled( "ColorLabel", color )
    scriptDialog.SetEnabled( "ColorBox", color )

    scriptDialog.SetEnabled( "SettingsLabel", settingsFile )
    scriptDialog.SetEnabled( "SettingsBox", settingsFile )

    scriptDialog.SetEnabled( "DgnReadOnlyBox", readOnlyCheck )

def SubmitButtonPressed(*args):
    global scriptDialog

    designFiles = [] # This list will have 1 entry (single file) or >=1 entry ( Script && Multifile)
    auxFiles = []
    operation = scriptDialog.GetValue( "OperationBox" )
    settingsFile = scriptDialog.GetValue( "SettingsBox" ).strip()
    outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
    submittingFiles = scriptDialog.GetValue( "SubmitFileBox" )
    convertPaths = scriptDialog.GetValue( "ConvertToUNCBox" )

    files = str( scriptDialog.GetValue( "DesignBox") ).strip()
    files = files.split(';')
    designFiles.extend( files )

    #validation on the settings file
    exportMode = ""
    renderMode = ""
    if operation == MSOP_FileExport:
        exportMode = scriptDialog.GetValue( "ModeBox" )
    elif operation == MSOP_AnimationRender or operation == MSOP_SingleViewRender:
        renderMode = scriptDialog.GetValue( "ModeBox" )


    if operation == MSOP_Print or operation == MSOP_SaveMultipleImages or operation == MSOP_Script or (operation == MSOP_FileExport and exportMode == EX_Autodesk):

        if len( settingsFile ) == 0:
            scriptDialog.ShowMessageBox( "No Settings file was specified.\nYou must specify an appropriate Settings file for this operation.", "Error" )
            return

        if not os.path.exists( settingsFile ):
            scriptDialog.ShowMessageBox( "The specified Settings file does not exist.\nYou must specify a valid, appropriate Settings file for this operation.", "Error" )
            return

        filename, ext = os.path.splitext( settingsFile )
        if operation == MSOP_SaveMultipleImages:
            if ext.lower() == ".sm":
                #need to open this file up to know how many tasks we need
                f = open( settingsFile, 'r' )
                try:
                    line = f.readline()
                    while line:
                        if line.strip().lower().startswith( "designfile" ):
                            entryCount += 1

                        line = f.readline()
                finally:
                    f.close()
            else:
                scriptDialog.ShowMessageBox( "Expected Settings file with extension *.sm for the Save Multiple Images operation.\n\nPlease specify a valid Settings file.", "Error" )
                return
        elif operation == MSOP_Print:
            if ext.lower() != ".pset" and ext.lower() != ".ini":
                scriptDialog.ShowMessageBox( "Expected Settings file with extension *.pset for the Print operation.\n\nPlease specify a valid Settings file.", "Error" )
                return

        elif operation == MSOP_FileExport:
            if ext.lower() != ".dws":
                scriptDialog.ShowMessageBox( "Expected Settings file with extension *.pset for the DWG Export operation.\n\nPlease specify a valid Settings file.", "Error" )
                return

        elif operation == MSOP_Script:
            if ext.lower() != ".scr" and ext.lower() != ".mvba" and ext.lower() != ".txt":
                scriptDialog.ShowMessageBox( "Expected Settings file with extensions *.scr, *.txt or *.mvba for the Script Job operation.\n\nPlease specify a valid Settings file.", "Error" )
                return

        if submittingFiles:
            auxFiles.append( settingsFile )
        elif PathUtils.IsPathLocal( settingsFile ):
            result = scriptDialog.ShowMessageBox( "The specified Settings file seems to be a local file:\n{0}\n\nDo you want to submit this file with the Job?".format( settingsFile ), "Warning", ("Yes", "No") )
            if result == "Yes":
                auxFiles.append( settingsFile )
        elif convertPaths:
            settingsFile = PathUtils.GetFullNetworkPath( settingsFile )
    else:
        settingsFile = ""

    # Check output file.
    if operation != MSOP_SaveMultipleImages and operation != MSOP_Script:
        if len( outputFile ) == 0:
            scriptDialog.ShowMessageBox( "No output file specified", "Error" )
            return

        elif not Directory.Exists( Path.GetDirectoryName( outputFile ) ):
            result = scriptDialog.ShowMessageBox( "The directory for the output file (" + outputFile + ") does not exist.\n\nDo you wish to create it now?", "Warning", ("Yes","No") )
            if result == "Yes":
                Directory.CreateDirectory( Path.GetDirectoryName( outputFile ) )

        elif PathUtils.IsPathLocal( outputFile ):
            result = scriptDialog.ShowMessageBox( "The output file (" + outputFile + ") seems to be local, are you sure you want to continue?","Warning", ("Yes","No") )
            if( result == "No" ):
                return

        elif convertPaths:
            outputFile = PathUtils.GetFullNetworkPath( outputFile )
    else:
        outputFile = ""
    
    #--End Validation That applies to all design files--

    for designFile in designFiles:
        jobAuxFiles = []

        #designFile = scriptDialog.GetValue( "DesignBox" ).strip()
        

        

        #--Do some validation on each design file--

        

        #Check to make sure a design file was specified and exists, if needed
        if operation != MSOP_SaveMultipleImages:
            if len( designFile ) == 0:
                scriptDialog.ShowMessageBox( "No Design file was specified.\nYou must specify a Design file for this operation.", "Error" )
                return

            elif len( designFile ) > 0 and not os.path.exists( designFile ):
                scriptDialog.ShowMessageBox( "The specified Design file does not exist.\nYou must specify a valid Design file for this operation.", "Error" )
                return
                

            if submittingFiles:
                jobAuxFiles.append( designFile )
            elif PathUtils.IsPathLocal( designFile ):
                result = scriptDialog.ShowMessageBox( "The specified Design file seems to be a local file:\n{0}\n\nDo you want to submit this file with the Job?".format( designFile ), "Warning", ("Yes", "No") )
                if result == "Yes":
                    jobAuxFiles.append( designFile )
            elif convertPaths:
                designFile = PathUtils.GetFullNetworkPath( designFile )
        else:
            designFile = ""

        entryCount = 0
        

        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "microstation_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        try:
            writer.WriteLine( "Plugin=MicroStation" )
            writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
            writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
            writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
            writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
            writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
            writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
            writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
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
            
            if entryCount > 0:
                writer.WriteLine( "Frames=0-{0}".format( entryCount - 1 ) )
            elif operation == MSOP_AnimationRender:
                writer.WriteLine( "Frames={0}".format( scriptDialog.GetValue( "FrameBox" ).strip() ) )
            else:
                writer.WriteLine( "Frames=0" )

            if operation == MSOP_SaveMultipleImages or operation == MSOP_AnimationRender:
                writer.WriteLine( "ChunkSize={0}".format( scriptDialog.GetValue( "ChunkBox" ) ) )
            else:
                writer.WriteLine( "ChunkSize=1" )

            if operation != MSOP_SaveMultipleImages and operation != MSOP_Script:
                writer.WriteLine( "OutputFilename0=%s" % outputFile )

            
        finally:
            writer.Close()

        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "microstation_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        try:
            writer.WriteLine( "Operation=%s" % operation )

            if designFile:
                writer.WriteLine( "DesignFile={0}".format( designFile ) )
                writer.WriteLine( "DesignFileReadOnly={0}".format( scriptDialog.GetValue( "DgnReadOnlyBox" ) ) )

            if operation == MSOP_FileExport:
                writer.WriteLine( "ExportMode={0}".format( exportMode ) )

                if exportMode == EX_Autodesk:
                    writer.WriteLine( "DWSFile={0}".format( settingsFile ) )
                elif exportMode == EX_VisibleEdges:
                    writer.WriteLine( "View={0}".format( scriptDialog.GetValue( "ViewBox" ) ) )
                    writer.WriteLine( "SavedView={0}".format( scriptDialog.GetValue( "SavedViewBox" ) ) )
                elif exportMode == EX_FlatDGN:
                    #Merge options for DGN export that pull in references
                    writer.WriteLine( "CExpression0=gMergeOptions.mergeV8.mergeSelfAttachments=2" )
                    writer.WriteLine( "CExpression1=gMergeOptions.mergeV8.mergeExternalAttachments=2" )
                    writer.WriteLine( "CExpression2=gMergeOptions.mergeV8.mergeViewletsHiddenLine=-1" )
                    writer.WriteLine( "CExpression3=gMergeOptions.mergeV8.copyLevelMode=2" )
                    writer.WriteLine( "CExpression4=gMergeOptions.mergeV8.copyNestedAttachments=-1" )

            elif operation == MSOP_SaveMultipleImages:
                writer.WriteLine( "SMIFile={0}".format( settingsFile ) )

            elif operation == MSOP_AnimationRender or operation == MSOP_SingleViewRender:
                writer.WriteLine( "RenderMode={0}".format( renderMode ) )
                writer.WriteLine( "ColorModel={0}".format( scriptDialog.GetValue( "ColorBox" ) ) )

                if renderMode == RM_Luxology:
                    writer.WriteLine( "RenderSetup={0}".format( scriptDialog.GetValue( "RenderSetupBox" ) ) )
                    writer.WriteLine( "Environment={0}".format( scriptDialog.GetValue( "EnvironmentBox" ) ) )
                    writer.WriteLine( "LightSetup={0}".format( scriptDialog.GetValue( "LightSetupBox" ) ) )

                writer.WriteLine( "OutputSizeX={0}".format( scriptDialog.GetValue( "XBox" ) ) )
                writer.WriteLine( "OutputSizeY={0}".format( scriptDialog.GetValue( "YBox" ) ) )

                writer.WriteLine( "View=%s" % scriptDialog.GetValue( "ViewBox" ) )
                if operation != MSOP_AnimationRender:
                    writer.WriteLine( "SavedView={0}".format( scriptDialog.GetValue( "SavedViewBox" ) ) )

            elif operation == MSOP_Print:
                writer.WriteLine( "PSETFile={0}".format( settingsFile ) )

            elif operation == MSOP_Script:
                writer.WriteLine( "ScriptFile={0}".format( settingsFile ) ) # Contents of Settings file dialog used to find script file.

                if ext.lower() == ".mvba": # Pass along module and submodule with keyinArgs
                    writer.WriteLine( "Module={0}".format( scriptDialog.GetValue( "ModuleBox" ) ) )
                    writer.WriteLine( "Submodule={0}".format( scriptDialog.GetValue( "SubModuleBox" ) ) )
                    writer.WriteLine( "KeyinArgs={0}".format( scriptDialog.GetValue( "KeyinBox" ) ) )
                # Read only

            if operation != MSOP_SaveMultipleImages and operation != MSOP_Script:
                writer.WriteLine( "OutputPath=%s" % outputFile )

        finally:
            writer.Close()

        # Setup the command line arguments.
        arguments = []

        arguments.append( jobInfoFilename )
        arguments.append( pluginInfoFilename )

        arguments.extend( jobAuxFiles )
        
        # Now submit the job.
        results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        scriptDialog.ShowMessageBox( results, "Submission Results" )

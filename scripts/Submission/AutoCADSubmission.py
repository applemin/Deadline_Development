from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

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

ProjectManagementOptions = ["Shotgun","FTrack"]
DraftRequested = False

plotterBox = None
plotStyleBox = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global scriptDialog
    global settings
    global plotterBox
    global plotStyleBox
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    
    scriptDialog = DeadlineScriptDialog()
    
    scriptDialog.SetTitle( "Submit AutoCAD Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'AutoCAD' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 0, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 0, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 1, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 1, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 2, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 2, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 0, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 0, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 1, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 1, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 2, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 2, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 3, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 3, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 4, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 4, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. ", False )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 5, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 5, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 6, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 1, 1, 1000000, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 6, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 7, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 8, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 9, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 10, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 10, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 10, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "AutoCAD Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    
    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "AutoCAD File", 0, 0, "The scene file to render.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "AutoCAD Files (*.dwg)", 0, 1, colSpan=2 )
    
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", True, "Submit AutoCAD File", 1, 0, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering." )
    
    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 2, 0, "The version of AutoCAD to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "2016", ("2015","2016"), 2, 1 )
    versionBox.ValueModified.connect(VersionChanged)
    
    scriptDialog.EndGrid()
    
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Render")
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Render Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    submitRenderControl = scriptDialog.AddSelectionControlToGrid( "SubmitRenderBox", "CheckBoxControl", False, "Submit Render Job", 0, 0, "When checked, a render job will be submitted. ", True, 1, 2 )
    submitRenderControl.ValueModified.connect(SubmitRenderValueChanged)
    
    scriptDialog.AddSelectionControlToGrid( "CurrentRenderViewBox", "CheckBoxControl", True, "Render View: Current", 1, 0, "When checked, a task to render the current view will be sent. ", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "TopRenderViewBox", "CheckBoxControl", False, "Render View: Top", 2, 0, "When checked, a task to render the Top view will be sent. ", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "BottomRenderViewBox", "CheckBoxControl", False, "Render View: Bottom", 2, 1, "When checked, a task to render the Bottom view will be sent. ", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "LeftRenderViewBox", "CheckBoxControl", False, "Render View: Left", 3, 0, "When checked, a task to render the Left view will be sent. ", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "RightRenderViewBox", "CheckBoxControl", False, "Render View: Right", 3, 1, "When checked, a task to render the Right view will be sent. ", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "FrontRenderViewBox", "CheckBoxControl", False, "Render View: Front", 4, 0, "When checked, a task to render the Front view will be sent. ", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "BackRenderViewBox", "CheckBoxControl", False, "Render View: Back", 4, 1, "When checked, a task to render the Back view will be sent. ", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "SWIsometricRenderViewBox", "CheckBoxControl", False, "Render View: SW Isometric", 5, 0, "When checked, a task to render the SW Isometric view will be sent. ", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "SEIsometricRenderViewBox", "CheckBoxControl", False, "Render View: SE Isometric", 5, 1, "When checked, a task to render the SE Isometric view will be sent. ", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "NEIsometricRenderViewBox", "CheckBoxControl", False, "Render View: NE Isometric", 6, 0, "When checked, a task to render the NE Isometric view will be sent. ", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "NWIsometricRenderViewBox", "CheckBoxControl", False, "Render View: NW Isometric", 6, 1, "When checked, a task to render the NW Isometric view will be sent. ", True, 1, 1 )
       
    #scriptDialog.AddControlToGrid( "RenderPresetLabel", "LabelControl", "Render Presets", 7, 0, "Render Presets", True )
    #scriptDialog.AddComboControlToGrid( "RenderPresetBox", "ComboControl", "Default", ("Current","Draft","Low","Medium","High","Presentation"), 7, 1 )
    
    scriptDialog.AddControlToGrid( "RenderFileNameLabel", "LabelControl", "Output File Name", 8, 0, "The name of your output file.", False )
    scriptDialog.AddSelectionControlToGrid( "RenderFileNameBox", "FileSaverControl","","All Image Formats (*);;BMP(*.bmp);;PCX(*.pcx);;TGA(*.tga);;TIF(*.tif);;JPEG(*.jpeg;*.jpg);;PNG(*.png)", 8, 1,colSpan=3 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Plot")
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Plot Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    submitPlotControl = scriptDialog.AddSelectionControlToGrid( "SubmitPlotBox", "CheckBoxControl", False, "Submit Plot Job", 0, 0, "When checked, a plot job will be submitted. ", True, 1, 2 )
    submitPlotControl.ValueModified.connect(SubmitPlotValueChanged)
    
    scriptDialog.AddControlToGrid( "PlotterLabel", "LabelControl", "Plotter", 1, 0, "The plotter to use for plotting", True )
    plotterBox = scriptDialog.AddComboControlToGrid( "PlotterBox", "ComboControl", "", (""), 1, 1,colSpan=3 )
    
    scriptDialog.AddControlToGrid( "PlotAreaLabel", "LabelControl", "Plot Area", 2, 0, "The area to plot", True )
    scriptDialog.AddComboControlToGrid( "PlotAreaBox", "ComboControl", "Display", ("Display","Extents"), 2, 1 )
    
    scriptDialog.AddControlToGrid( "PaperWidthLabel", "LabelControl", "Paper Width", 3, 0, "", False )
    scriptDialog.AddRangeControlToGrid( "PaperWidthBox", "RangeControl", 10, 0, 1000, 2, 1, 3, 1 )
    scriptDialog.AddControlToGrid( "PaperHeightLabel", "LabelControl", "Paper Height", 3, 2, "", False )
    scriptDialog.AddRangeControlToGrid( "PaperHeightBox", "RangeControl", 10, 0, 1000, 2, 1, 3, 3 )
    
    scriptDialog.AddControlToGrid( "PaperUnitsLabel", "LabelControl", "Plotter Units", 4, 0, "", True )
    scriptDialog.AddComboControlToGrid( "PaperUnitsBox", "ComboControl", "", ("Inches","Millimeters"), 4, 1 )
    
    fitPlotScaleControl = scriptDialog.AddSelectionControlToGrid( "FitPlotScaleBox", "CheckBoxControl", True, "Fit Plot Scale", 5, 0, "Should the plotter fit to scale or used the specified scale.", True, 1, 2 )
    fitPlotScaleControl.ValueModified.connect(FitPlotScaleValueChanged)
    
    scriptDialog.AddControlToGrid( "PlottedUnitsLabel", "LabelControl", "Plotted Units", 6, 0, "", False )
    scriptDialog.AddRangeControlToGrid( "PlottedUnitsBox", "RangeControl", 1, 0, 100000, 2, 1, 6, 1 )
    scriptDialog.AddControlToGrid( "DrawingUnitsLabel", "LabelControl", "Drawing Units", 6, 2, "", False )
    scriptDialog.AddRangeControlToGrid( "DrawingUnitsBox", "RangeControl", 50, 0, 100000, 2, 1, 6, 3 )
    
    scriptDialog.AddControlToGrid( "PlotStyleTable", "LabelControl", "Plot Style Table", 7, 0, "", True )
    plotStyleBox = scriptDialog.AddComboControlToGrid( "PlotStyleBox", "ComboControl", "", (""), 7, 1 )
    
    scriptDialog.AddSelectionControlToGrid( "UseLineweightsBox", "CheckBoxControl", True, "Use Line weights", 8, 0, "", True, 1, 1 )
    scriptDialog.AddSelectionControlToGrid( "ScaleLineweightsBox", "CheckBoxControl", False, "Scale lineweights", 8, 1, "", True, 1, 1 )
    
    scriptDialog.AddControlToGrid( "PlotFileNameLabel", "LabelControl", "Output File Name", 9, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddSelectionControlToGrid( "PlotFileNameBox", "FileSaverControl","","All files (*)", 9, 1,colSpan=3 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Export")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Export Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    submitPlotControl = scriptDialog.AddSelectionControlToGrid( "SubmitExportBox", "CheckBoxControl", False, "Submit Export Job", 0, 0, "When checked, an export job will be submitted. ", True, 1, 2 )
    submitPlotControl.ValueModified.connect(SubmitExportValueChanged)
    
    scriptDialog.AddControlToGrid( "ExportFileNameLabel", "LabelControl", "Output File Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    exportFilenameBox = scriptDialog.AddSelectionControlToGrid( "ExportFileNameBox", "FileSaverControl","","3D DWF (*.dwf);;3D DWFx (*.dwfx);;FBX (*.fbx);;Metafile (*.wmf);;ACIS (*.sat);;Lithography (*.stl);;Encapsulated PS (*.eps);;DXX Extract (*.dxx);;Bitmap (*.bmp);;Block (*.dwg);;DGN (*.dgn);;IGES (*.iges);;IGES (*.igs)", 1, 1,colSpan=3 )
    exportFilenameBox.ValueModified.connect(ExportFilenameValueChanged)
    
    scriptDialog.AddSelectionControlToGrid( "ExportVisibleBox", "CheckBoxControl", False, "Export Visible Only", 2, 0, "When checked only visible objects will be exported.", True, 1, 2 )
    
    exportAllBox = scriptDialog.AddSelectionControlToGrid( "ExportAllTypesBox", "CheckBoxControl", True, "Export All Types", 3, 0, "", True, 1, 2 )
    exportAllBox.ValueModified.connect(ExportAllValueChanged)
    
    
    scriptDialog.AddSelectionControlToGrid( "ExportObjectsBox", "CheckBoxControl", True, "Export Objects", 4, 0, "", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "ExportCamerasBox", "CheckBoxControl", True, "Export Cameras", 4, 2, "", True, 1, 2 )
    
    scriptDialog.AddSelectionControlToGrid( "ExportLightsBox", "CheckBoxControl", True, "Export Lights", 5, 0, "", True, 1, 2 )
    scriptDialog.AddSelectionControlToGrid( "ExportMaterialsBox", "CheckBoxControl", True, "Export Materials", 5, 2, "", True, 1, 2 )
    scriptDialog.AddControlToGrid( "ExportTexturesLabel", "LabelControl", "Textures", 6, 0, "", True )
    scriptDialog.AddComboControlToGrid( "TexturesBox", "ComboControl", "", ("Embed","Reference","Copy"), 6, 1 )
    scriptDialog.AddControlToGrid( "DGNVersionLabel", "LabelControl", "DGN Version", 7, 0, "", True )
    scriptDialog.AddComboControlToGrid( "DGNVersionBox", "ComboControl", "", ("V8","V7"), 7, 1 )
    scriptDialog.AddControlToGrid( "DGNConversionUnitsLabel", "LabelControl", "Conversion Units", 8, 0, "", True )
    scriptDialog.AddComboControlToGrid( "DGNConversionUnitsBox", "ComboControl", "", ("Master","Sub"), 8, 1 )
    scriptDialog.AddControlToGrid( "DGNMappingSetupLabel", "LabelControl", "Mapping Setup", 9, 0, "", True )
    scriptDialog.AddComboControlToGrid( "DGNMappingSetupBox", "ComboControl", "", ("Standard",), 9, 1 )
    scriptDialog.AddControlToGrid( "DGBSeedFileLabel", "LabelControl", "Seed File Name", 10, 0, "", False )
    scriptDialog.AddSelectionControlToGrid( "DGNSeedFileBox", "FileSaverControl","","Seed File (*.dgn)", 10, 1,colSpan=3 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "AutoCADMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","BuildBox","PluginIniBox","PathConfigBox","MergePathConfigBox","PreLoadBox", "PostLoadBox", "PreFrameBox", "PostFrameBox", "SubmitSceneBox","LocalRenderingBox","IsMaxDesignBox","OneCpuPerTaskBox","OverrideLanguageBox","LanguageBox","GammaCorrectionBox", "GammaInputBox", "GammaOutputBox","DBRServersBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    SubmitRenderValueChanged( None )
    SubmitPlotValueChanged( None )
    SubmitExportValueChanged( None )
    VersionChanged( None )
    
    scriptDialog.ShowDialog( False )

########################################################################
## Helper Functions
########################################################################

def SubmitRenderValueChanged( *args):
    global scriptDialog
    enabled = scriptDialog.GetValue( "SubmitRenderBox" )
    scriptDialog.SetEnabled( "CurrentRenderViewBox", enabled) 
    scriptDialog.SetEnabled( "TopRenderViewBox", enabled )
    scriptDialog.SetEnabled( "BottomRenderViewBox", enabled )
    scriptDialog.SetEnabled( "LeftRenderViewBox", enabled )
    scriptDialog.SetEnabled( "RightRenderViewBox", enabled )
    scriptDialog.SetEnabled( "FrontRenderViewBox", enabled )
    scriptDialog.SetEnabled( "BackRenderViewBox", enabled )
    scriptDialog.SetEnabled( "SWIsometricRenderViewBox", enabled )
    scriptDialog.SetEnabled( "SEIsometricRenderViewBox", enabled )
    scriptDialog.SetEnabled( "NWIsometricRenderViewBox", enabled )
    scriptDialog.SetEnabled( "NEIsometricRenderViewBox", enabled )
    #scriptDialog.SetEnabled( "RenderPresetLabel", enabled )
    #scriptDialog.SetEnabled( "RenderPresetBox", enabled )
    scriptDialog.SetEnabled( "RenderFileNameLabel", enabled )
    scriptDialog.SetEnabled( "RenderFileNameBox", enabled )

def FitPlotScaleValueChanged( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "SubmitPlotBox" ) and not scriptDialog.GetValue( "FitPlotScaleBox")
    scriptDialog.SetEnabled( "PlottedUnitsLabel", enabled)
    scriptDialog.SetEnabled( "PlottedUnitsBox", enabled) 
    scriptDialog.SetEnabled( "DrawingUnitsLabel", enabled) 
    scriptDialog.SetEnabled( "DrawingUnitsBox", enabled) 
    
def SubmitPlotValueChanged( *args):
    global scriptDialog
        
    enabled = scriptDialog.GetValue( "SubmitPlotBox" ) and scriptDialog.GetEnabled("SubmitPlotBox")
    scriptDialog.SetEnabled( "PlotterLabel", enabled) 
    scriptDialog.SetEnabled( "PlotterBox", enabled) 
    scriptDialog.SetEnabled( "PlotAreaLabel", enabled) 
    scriptDialog.SetEnabled( "PlotAreaBox", enabled) 
    scriptDialog.SetEnabled( "PaperWidthLabel", enabled) 
    scriptDialog.SetEnabled( "PaperWidthBox", enabled) 
    scriptDialog.SetEnabled( "PaperHeightLabel", enabled) 
    scriptDialog.SetEnabled( "PaperHeightBox", enabled) 
    scriptDialog.SetEnabled( "PaperUnitsLabel", enabled) 
    scriptDialog.SetEnabled( "PaperUnitsBox", enabled) 
    scriptDialog.SetEnabled( "FitPlotScaleBox", enabled)
    scriptDialog.SetEnabled( "PlotterLabel", enabled)
    scriptDialog.SetEnabled( "PlotStyleTable", enabled)
    scriptDialog.SetEnabled( "PlotStyleBox", enabled)
    scriptDialog.SetEnabled( "UseLineweightsBox", enabled)
    scriptDialog.SetEnabled( "ScaleLineweightsBox", enabled)
    scriptDialog.SetEnabled( "PlotFileNameLabel", enabled)
    scriptDialog.SetEnabled( "PlotFileNameBox", enabled)
    FitPlotScaleValueChanged(None)
 
def SubmitExportValueChanged( *args ):
    global scriptDialog
    
    enabled = scriptDialog.GetValue( "SubmitExportBox" )
    
    scriptDialog.SetEnabled( "ExportFileNameLabel", enabled)
    scriptDialog.SetEnabled( "ExportFileNameBox", enabled)
    
    ExportFilenameValueChanged(None)
       
def ExportFilenameValueChanged( *args):
    global scriptDialog
    enabled = scriptDialog.GetValue( "SubmitExportBox" )
    fileName = scriptDialog.GetValue( "ExportFileNameBox" )
    
    extension = os.path.splitext(fileName)[1]
    
    isFbx = (extension == ".fbx") and enabled
    isDWF = ((extension == ".dwf") or (extension == ".dwfx")) and enabled
    isDGN = (extension == ".dgn") and enabled
    
    scriptDialog.SetEnabled( "ExportVisibleBox", isFbx)
    scriptDialog.SetEnabled( "ExportAllTypesBox", isFbx)
    
    ExportAllValueChanged(None)
    
    scriptDialog.SetEnabled( "ExportTexturesLabel", isFbx)
    scriptDialog.SetEnabled( "TexturesBox", isFbx)
    
    scriptDialog.SetEnabled( "DGNVersionLabel", isDGN)
    scriptDialog.SetEnabled( "DGNVersionBox", isDGN)
    scriptDialog.SetEnabled( "DGNConversionUnitsLabel", isDGN)
    scriptDialog.SetEnabled( "DGNConversionUnitsBox", isDGN)
    scriptDialog.SetEnabled( "DGNMappingSetupLabel", isDGN)
    scriptDialog.SetEnabled( "DGNMappingSetupBox", isDGN)
    scriptDialog.SetEnabled( "DGBSeedFileLabel", isDGN)
    scriptDialog.SetEnabled( "DGNSeedFileBox", isDGN)
 
def ExportAllValueChanged( *args):
    enabled = scriptDialog.GetValue( "SubmitExportBox" )
    fileName = scriptDialog.GetValue( "ExportFileNameBox" )
    exportAll = scriptDialog.GetValue( "ExportAllTypesBox" )
     
    extension = os.path.splitext(fileName)[1]
    
    isFbx = (extension == ".fbx") and enabled
    isDWF = ((extension == ".dwf") or (extension == ".dwfx")) and enabled
    
    scriptDialog.SetEnabled( "ExportObjectsBox", isFbx and not exportAll)
    scriptDialog.SetEnabled( "ExportCamerasBox", isFbx and not exportAll)
    scriptDialog.SetEnabled( "ExportLightsBox", isFbx and not exportAll)
    scriptDialog.SetEnabled( "ExportMaterialsBox", (isFbx and not exportAll) or isDWF)
 
def VersionChanged( *args ):
    global plotterBox
    global plotStyleBox
    version = scriptDialog.GetValue( "VersionBox" )
    
    AutoCADPath = os.path.expandvars("${APPDATA}\\Autodesk\\AutoCAD "+str(version)+"\\R"+str(int(str(version))-1995)+".0")
    
    if os.path.isdir(AutoCADPath+"\\enu\\Plotters"):
        scriptDialog.SetEnabled("SubmitPlotBox",True)
        plotterPath = AutoCADPath +"\\enu\\Plotters"
        plotterFiles = [ f for f in os.listdir(plotterPath) if os.path.isfile(os.path.join(plotterPath,f)) ]
        plotterFiles = [f for f in plotterFiles if (f.endswith(".pc3")) ]
        plotterBox.setTheItems(plotterFiles)
        
        plotStylePath = plotterPath+"\\Plot Styles"
        
        plotStyleFiles = [ f for f in os.listdir(plotStylePath) if os.path.isfile(os.path.join(plotStylePath,f)) ]
        plotStyleFiles = [ f for f in plotStyleFiles if (f.endswith(".ctb")) ]
        plotStyleBox.setTheItems(plotStyleFiles)
    else:
        scriptDialog.SetEnabled("SubmitPlotBox",False)
        plotterBox.setTheItems(["",])
    SubmitPlotValueChanged(None)
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "AutoCADSettings.ini" )

def SubmitRender(showOutput, results):
    global scriptDialog
    global integration_dialog
    jobName = scriptDialog.GetValue( "NameBox" )
    
    currentRenderView = scriptDialog.GetValue( "CurrentRenderViewBox" )
    TopRenderView = scriptDialog.GetValue( "TopRenderViewBox" )
    BottomRenderViewBox = scriptDialog.GetValue( "BottomRenderViewBox" )
    LeftRenderViewBox = scriptDialog.GetValue( "LeftRenderViewBox" )
    RightRenderViewBox = scriptDialog.GetValue( "RightRenderViewBox" )
    FrontRenderViewBox = scriptDialog.GetValue( "FrontRenderViewBox" )
    BackRenderViewBox = scriptDialog.GetValue( "BackRenderViewBox" )
    SWIsometricRenderView = scriptDialog.GetValue( "SWIsometricRenderViewBox" )
    SEIsometricRenderView = scriptDialog.GetValue( "SEIsometricRenderViewBox" )
    NEIsometricRenderView = scriptDialog.GetValue( "NEIsometricRenderViewBox" )
    NWIsometricRenderView = scriptDialog.GetValue( "NWIsometricRenderViewBox" )
    
    frameCount = 0
    
    frameCount = frameCount +1 if currentRenderView else frameCount
    frameCount = frameCount +1 if TopRenderView else frameCount
    frameCount = frameCount +1 if BottomRenderViewBox else frameCount
    frameCount = frameCount +1 if LeftRenderViewBox else frameCount
    frameCount = frameCount +1 if RightRenderViewBox else frameCount
    frameCount = frameCount +1 if FrontRenderViewBox else frameCount
    frameCount = frameCount +1 if BackRenderViewBox else frameCount
    frameCount = frameCount +1 if SWIsometricRenderView else frameCount
    frameCount = frameCount +1 if SEIsometricRenderView else frameCount
    frameCount = frameCount +1 if NEIsometricRenderView else frameCount
    frameCount = frameCount +1 if NWIsometricRenderView else frameCount
    
    if frameCount == 0:
        results[1] +=1
        if showOutput:
            scriptDialog.ShowMessageBox( "Failed to Submit Render Job, no views selected.", "Submission Results" )
        return
    
    if scriptDialog.GetValue( "RenderFileNameBox" ) == "":
        results[1] +=1
        if showOutput:
            scriptDialog.ShowMessageBox( "Failed to submit render job, no output selected.", "Submission Results" )
        return
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "AutoCAD_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=AutoCAD" )
    writer.WriteLine( "Name=%s - Render" % jobName )
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
    
    writer.WriteLine("OutputFilename0=" + scriptDialog.GetValue( "RenderFileNameBox" ));
    
    writer.WriteLine( "Frames=0-%s" % str(frameCount-1) )
    writer.WriteLine( "ChunkSize=1" )
    
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "autocad_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
    if not submitScene:
        writer.WriteLine("SceneFile=%s\n"%fileName)
    
    writer.WriteLine("Version=" + scriptDialog.GetValue( "VersionBox" ));

    writer.WriteLine("JobType=Render");
    
    writer.WriteLine("")
    
    #writer.WriteLine("RenderPreset=" + scriptDialog.GetValue( "RenderPresetBox" ));
    
    #writer.WriteLine("RenderPreset0=Current")
    #writer.WriteLine("RenderPreset1=Draft" )
    #writer.WriteLine("RenderPreset2=Low" )
    #writer.WriteLine("RenderPreset3=Medium" )
    #writer.WriteLine("RenderPreset5=High" )
    #writer.WriteLine("RenderPreset4=Presentation" )   

    viewCount = 0
    
    if currentRenderView:
        writer.WriteLine("RenderView"+str(viewCount)+"=Current")
        viewCount+=1
    if TopRenderView:
        writer.WriteLine("RenderView"+str(viewCount)+"=Top")
        viewCount+=1
    if BottomRenderViewBox:
        writer.WriteLine("RenderView"+str(viewCount)+"=Bottom")
        viewCount+=1
    if LeftRenderViewBox:
        writer.WriteLine("RenderView"+str(viewCount)+"=Left")
        viewCount+=1
    if RightRenderViewBox:
        writer.WriteLine("RenderView"+str(viewCount)+"=Right")
        viewCount+=1
    if FrontRenderViewBox:
        writer.WriteLine("RenderView"+str(viewCount)+"=Front")
        viewCount+=1
    if BackRenderViewBox:
        writer.WriteLine("RenderView"+str(viewCount)+"=Back")
        viewCount+=1
    if SWIsometricRenderView:
        writer.WriteLine("RenderView"+str(viewCount)+"=SW Isometric")
        viewCount+=1
    if SEIsometricRenderView:
        writer.WriteLine("RenderView"+str(viewCount)+"=SE Isometric")
        viewCount+=1
    if NEIsometricRenderView:
        writer.WriteLine("RenderView"+str(viewCount)+"=NE Isometric")
        viewCount+=1
    if NWIsometricRenderView:
        writer.WriteLine("RenderView"+str(viewCount)+"=NW Isometric")
        viewCount+=1

    writer.WriteLine("OutputFileName=" + scriptDialog.GetValue( "RenderFileNameBox" ));
    writer.Close()
    
    arguments = StringCollection()
            
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( sceneFile )
        
    if( showOutput ):
        results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        scriptDialog.ShowMessageBox( results, "Submission Results" )
    else:
        # Now submit the job.
        exitCode = ClientUtils.ExecuteCommand( arguments )
        if( exitCode == 0 ):
            results[0] += 1
        else:
            results[1] += 1

def SubmitPlot(showOutput, results):
    global scriptDialog
    global integration_dialog
    jobName = scriptDialog.GetValue( "NameBox" )
    
    if scriptDialog.GetValue( "PlotFileNameBox" ) == "":
        results[1] +=1
        if showOutput:
            scriptDialog.ShowMessageBox( "Failed to submit plot job, no output selected.", "Submission Results" )
        return
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "AutoCAD_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=AutoCAD" )
    writer.WriteLine( "Name=%s - Plot" % jobName )
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
    
    writer.WriteLine("OutputDirectory0=" + os.path.split(scriptDialog.GetValue( "PlotFileNameBox" ))[0]);
    
    writer.WriteLine( "Frames=0")
    writer.WriteLine( "ChunkSize=1" )
    
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "autocad_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
    if not submitScene:
        writer.WriteLine("SceneFile=%s\n"%fileName)
    
    writer.WriteLine("Version=" + scriptDialog.GetValue( "VersionBox" ));

    writer.WriteLine("JobType=Plot");
    
    writer.WriteLine("PlotFilePrefix=" + scriptDialog.GetValue( "PlotFileNameBox" ));
    writer.WriteLine("Plotter=" + scriptDialog.GetValue( "PlotterBox" ));
    writer.WriteLine("PlotArea=" + scriptDialog.GetValue( "PlotAreaBox" ));
    writer.WriteLine("UsePaperSize=False")
    writer.WriteLine("PaperWidth="+str(scriptDialog.GetValue("PaperWidthBox")))
    writer.WriteLine("PaperHeight="+str(scriptDialog.GetValue("PaperHeightBox")))
    writer.WriteLine("PaperUnits="+str(scriptDialog.GetValue("PaperUnitsBox")))
    writer.WriteLine("FitPlotScale=" + str(scriptDialog.GetValue("FitPlotScaleBox")));
    writer.WriteLine("PlottedUnitScale=" + str(scriptDialog.GetValue("PlottedUnitsBox")));
    writer.WriteLine("DrawingUnitScale=" + str(scriptDialog.GetValue("DrawingUnitsBox")));
    writer.WriteLine("PlotStyleTable=" + str(scriptDialog.GetValue("PlotStyleBox")));
    writer.WriteLine("UseLineWeights=" + str(scriptDialog.GetValue("UseLineweightsBox")));
    writer.WriteLine("ScaleLineWeights=" + str(scriptDialog.GetValue("ScaleLineweightsBox")));
    
    writer.Close()
    
    arguments = StringCollection()
            
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( sceneFile )
        
    if( showOutput ):
        results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        scriptDialog.ShowMessageBox( results, "Submission Results" )
    else:
        # Now submit the job.
        exitCode = ClientUtils.ExecuteCommand( arguments )
        if( exitCode == 0 ):
            results[0] += 1
        else:
            results[1] += 1

def SubmitExport(showOutput, results):
    global scriptDialog
    global integration_dialog
    jobName = scriptDialog.GetValue( "NameBox" )
    
    if scriptDialog.GetValue( "ExportFileNameBox" ) == "":
        results[1] +=1
        if showOutput:
            scriptDialog.ShowMessageBox( "Failed to submit export job, no output selected.", "Submission Results" )
        return
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "AutoCAD_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=AutoCAD" )
    writer.WriteLine( "Name=%s - Export" % jobName )
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
    
    writer.WriteLine("OutputFilename0=" + scriptDialog.GetValue( "ExportFileNameBox" ));
    
    writer.WriteLine( "Frames=0")
    writer.WriteLine( "ChunkSize=1" )
    
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
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "autocad_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
    if not submitScene:
        writer.WriteLine("SceneFile=%s"%fileName)
    
    writer.WriteLine("Version=" + scriptDialog.GetValue( "VersionBox" ));

    writer.WriteLine("JobType=Export");
    
    filename = scriptDialog.GetValue( "ExportFileNameBox" )
    
    ext = os.path.splitext(filename)[1]
    writer.WriteLine("ExportFilename="+filename)
    if ext == ".bmp" or ext == ".sat" or ext == ".wmf" or ext == ".dwf" or ext == ".stl" or ext == ".dwfx" or ext == ".fbx" or ext == ".dxx" or ext == ".iges" or ext == ".igs":
        if ext == ".fbx" and scriptDialog.GetValue("ExportVisibleBox"):
            writer.WriteLine("Selection=Visible")
        else:
            writer.WriteLine("Selection=All")
        if ext == ".fbx":
            writer.WriteLine("ExportAll="+str(scriptDialog.GetValue("ExportAllTypesBox")))
            writer.WriteLine("ExportObjects="+str(scriptDialog.GetValue("ExportObjectsBox")))
            writer.WriteLine("ExportLights="+str(scriptDialog.GetValue("ExportLightsBox")))
            writer.WriteLine("ExportCameras="+str(scriptDialog.GetValue("ExportCamerasBox")))
            writer.WriteLine("ExportMaterials="+str(scriptDialog.GetValue("ExportMaterialsBox")))
            writer.WriteLine("HandleTextures="+scriptDialog.GetValue("TexturesBox"))
        if ext == ".dwf" or ext == ".dwfx":
            writer.WriteLine("ExportMaterials="+str(scriptDialog.GetValue("ExportMaterialsBox")))
    elif ext == ".dgn":
        writer.WriteLine("DGNVersion="+scriptDialog.GetValue("DGNVersionBox"))
        writer.WriteLine("DGNConversionUnits="+scriptDialog.GetValue("DGNConversionUnitsBox"))
        writer.WriteLine("DGNMappingSetup="+scriptDialog.GetValue("DGNMappingSetupBox"))
        writer.WriteLine("DGNMappingSetup0="+scriptDialog.GetValue("DGNMappingSetupBox"))
        writer.WriteLine("DGNSeedFile="+scriptDialog.GetValue("DGNSeedFileBox"))        
        
    writer.Close()
    
    arguments = StringCollection()
            
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( sceneFile )
        
    if( showOutput ):
        results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        scriptDialog.ShowMessageBox( results, "Submission Results" )
    else:
        # Now submit the job.
        exitCode = ClientUtils.ExecuteCommand( arguments )
        if( exitCode == 0 ):
            results[0] += 1
        else:
            results[1] += 1
            
def SubmitButtonPressed( *args ):
    global scriptDialog
    
    try:
        submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
        
        # Check if max files exist.
        sceneFile = scriptDialog.GetValue( "SceneBox" )
        if( sceneFile == "" ):
            scriptDialog.ShowMessageBox( "No AutoCAD file specified", "Error" )
            return
        
        if( not File.Exists( sceneFile ) ):
            scriptDialog.ShowMessageBox("AutoCAD file %s does not exist" % sceneFile, "Error" )
            return
        elif( not submitScene and PathUtils.IsPathLocal( sceneFile ) ):
            result = scriptDialog.ShowMessageBox( "The scene file " + sceneFile + " is local and is not being submitted with the job, are you sure you want to continue?", "Warning", ("Yes","No") )
            if( result == "No" ):
                return
        
        # Check if Integration options are valid
        if not integration_dialog.CheckIntegrationSanity( ):
            return
                        
        successes = 0
        failures = 0
        results = [0,0]#success,fail
        jobCount = 0
        
        submitRenderChecked = scriptDialog.GetValue( "SubmitRenderBox")
        submitPlotChecked = scriptDialog.GetValue( "SubmitPlotBox") and scriptDialog.GetEnabled( "SubmitPlotBox")
        submitExportChecked = scriptDialog.GetValue( "SubmitExportBox")
        
        if submitRenderChecked:
            jobCount+=1
        if submitPlotChecked:
            jobCount+=1
        if submitExportChecked:
            jobCount+=1
            
        if submitRenderChecked:
            SubmitRender( jobCount == 1, results)
        if submitPlotChecked:
            SubmitPlot( jobCount == 1, results)
        if submitExportChecked:
            SubmitExport( jobCount == 1, results)
        
        if( jobCount > 1 ):
            scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (results[0], results[1]), "Submission Results" )
    except:
        import traceback
        scriptDialog.ShowMessageBox(traceback.format_exc(), "")

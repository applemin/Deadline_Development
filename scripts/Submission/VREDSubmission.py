from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

import traceback
from collections import OrderedDict

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

from PyQt5.QtGui import *

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
DraftRequested = True

versionOptions = OrderedDict([
        ("7.0 (2015)", "7.0"),
        ("8.0 (2016)", "8.0"),
        ("9.0 (2017)", "9.0"),
        ("9.1 (2017.1)", "9.1"),
        ("9.2 (2017.2)", "9.2"),
        ("10.0 (2018)", "10.0"),
        ("10.1 (2018.1)", "10.1"),
        ("10.2 (2018.2)", "10.2"),
        ("11.0 (2019)", "11.0")
    ])

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    global versionOptions
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit VRED Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'VRED' ) )
    
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
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("VRED Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "VRED Options", 0, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "VRED File", 1, 0, "The VRED project file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "VRED Essentials Project Binary (*.vpe);;VRED Project Binary (*.vpb);;VRED Project File (*.vpf);;All Files (*)", 1, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 2, 0, "The VRED application version to use.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "11.0 (2019)", versionOptions.keys(), 2, 1 )
    
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit VRED Project File", 2, 2, "If this option is enabled, the project file will be submitted with the job, and then copied locally to the slave machine during rendering.", colSpan=2 )

    scriptDialog.AddControlToGrid( "JobTypeLabel", "LabelControl", "Job Type", 3, 0, "The VRED job type.", False )
    JobTypeBoxBox = scriptDialog.AddComboControlToGrid( "JobTypeBox", "ComboControl", "Render", ("Render","Render Queue","Sequencer"), 3, 1 )
    JobTypeBoxBox.ValueModified.connect(JobTypeChanged)
    renderAnimCheck = scriptDialog.AddSelectionControlToGrid( "RenderAnimationCheck", "CheckBoxControl", True, "Render Animation", 3, 2, "If this option is enabled, the render job will render animations.", colSpan=2 )    
    renderAnimCheck.ValueModified.connect(JobTypeChanged)
    
    scriptDialog.AddControlToGrid( "OutputLabel","LabelControl","Output File", 4, 0, "The filename of the image(s) to be rendered.", False )
    outputBox = scriptDialog.AddSelectionControlToGrid("OutputBox","FileSaverControl","","Windows Bitmap (*.bmp *.dib);;DirectDraw Surface (*.dds);;EXR (*.exr);;HDR (*.hdr);;JFIF (*.jfif);;JPEG (*.jpe *.jpg *.jpeg);;NRRD (*.nrrd);;PGM (*.pgm);;PCX (*.pcx);;PNG (*.png);;PNM (*.pnm);;PPM (*.ppm);;PSB (*.psb);;PSD (*.psd);;RLE (*.rle);;TIFF (*.tif *.tiff);;VIF (*.vif);;All files (*)", 4, 1, colSpan=3)
    outputBox.ValueModified.connect(ChangeOutputFilename)
    #AVI (*.avi);;
    
    scriptDialog.AddControlToGrid( "ViewLabel", "LabelControl", "View / Camera", 5, 0, "The view or camera to render from, if left blank it will use the current view.", False )
    scriptDialog.AddControlToGrid( "ViewBox", "TextControl", "", 5, 1, colSpan=3 )
        
    scriptDialog.AddControlToGrid( "AnimationLabel", "LabelControl", "Animation Clip", 6, 0, "The animation to use, if left blank it will use all enabled clips", False )
    scriptDialog.AddControlToGrid( "AnimationBox", "TextControl", "", 6, 1, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "RenderWidthLabel", "LabelControl", "Render Width", 7, 0, "The width of the images rendered.", False )
    scriptDialog.AddRangeControlToGrid( "RenderWidthBox", "RangeControl", 1920, 1, 1000000, 0, 1, 7, 1 )
    
    scriptDialog.AddControlToGrid( "RenderHeightLabel", "LabelControl", "Render Height", 7, 2, "The height of the images rendered.", False )
    scriptDialog.AddRangeControlToGrid( "RenderHeightBox", "RangeControl", 1080, 1, 1000000, 0, 1, 7, 3 )
    
    scriptDialog.AddControlToGrid( "SuperSamplingLabel", "LabelControl", "Super Sampling Factor", 8, 0, "The height of the images rendered.", False )
    scriptDialog.AddRangeControlToGrid( "SuperSamplingBox", "RangeControl", 32, 1, 1024, 0, 1, 8, 1 )
    scriptDialog.AddControlToGrid( "RenderQualityLabel", "LabelControl", "Render Quality", 8, 2, "The Render quality to use.", False )
    renderQualityBox = scriptDialog.AddComboControlToGrid( "RenderQualityBox", "ComboControl", "Realistic High", ("Analytic Low","Analytic High","Realistic Low","Realistic High","Raytracing","NPR"), 8, 3 )
    renderQualityBox.ValueModified.connect(ChangeRenderQuality)
    
    scriptDialog.AddControlToGrid( "BackgroundColorLabel", "LabelControl", "Background", 9, 0, "The background color.", False )
    scriptDialog.AddControlToGrid( "BackgroundColorBox", "ColorControl", QColor(0,0,0), 9, 1, colSpan=3 )
        
    alphaChannelBox = scriptDialog.AddSelectionControlToGrid( "AlphaChannelBox", "CheckBoxControl", True, "Include Alpha Channel", 10, 0, "If enabled, the rendered images will include an alpha channel." )
    alphaChannelBox.ValueModified.connect(ChangeAlphaChannelBox)
    
    scriptDialog.AddSelectionControlToGrid( "AlphaPremultiplyBox", "CheckBoxControl", True, "Premultiply Alpha", 10, 1, "If enabled, the alpha channel will be premultiplied." )
    scriptDialog.AddSelectionControlToGrid( "ToneMapBox", "CheckBoxControl", False, "Tonemap HDR", 10, 2, "If enabled, tonemapping will be used for .hdr files." )
    
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 11, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 11, 1 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 11, 2, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 11, 3 )
    
    #scriptDialog.AddControlToGrid( "fpsLabel", "LabelControl", "Frames Per Second", 13, 0, "This is the number of frames per second. Used only for rendering avi files.", False )
    #scriptDialog.AddRangeControlToGrid( "fpsBox", "RangeControl", 25, 1, 1000000, 0, 1, 13, 1 )
    
    scriptDialog.AddControlToGrid( "DPILabel", "LabelControl", "DPI", 12, 0, "The dots per inch for the rendered single frame image.", False )
    scriptDialog.AddRangeControlToGrid( "DPIBox", "RangeControl", 72, 1, 1200, 0, 1, 12, 1 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddSelectionControlToGrid( "OverrideRenderPassBox", "CheckBoxControl", False, "Override Render Pass Options", 0, 0, "If enabled, you will use the render pass options from the submitter instead of those from within the scene." )
    
    changeExportBox = scriptDialog.AddSelectionControlToGrid( "ExportRenderPassBox", "CheckBoxControl", False, "Export Render Passes", 0, 1, "If enabled and the render quality is Raytracing, the checked Render Passes will be rendered." )
    changeExportBox.ValueModified.connect(ChangeExportRenderPass)
    
    scriptDialog.AddSelectionControlToGrid( "OverrideMetaDataBox", "CheckBoxControl", False, "Override Embed Meta Data", 1, 0, "If enabled, you will use the Embedded Meta data options from the submitter instead of those from within the scene." )
    
    embedMetaBox = scriptDialog.AddSelectionControlToGrid( "EmbedMetaDataBox", "CheckBoxControl", False, "Embed Meta Data", 1, 1, "When rendering to .png, .jpg, or .tif if enabled the checked Meta data will be embedded." )
    embedMetaBox.ValueModified.connect(ChangeEmbedMeta)
    
    scriptDialog.AddControlToGrid( "SequenceNameLabel", "LabelControl", "Sequence Name", 2, 0, "The name of the sequence to run. If not defined or using 2015 version all sequences will be rendered.", False )
    scriptDialog.AddControlToGrid( "SequenceNameBox", "TextControl", "", 2, 1, colSpan=3 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Render Passes/Meta Data")
    scriptDialog.AddGrid()
    
    scriptDialog.AddControlToGrid( "CombinedChannelLabel", "SeparatorControl", "Combined Channels", 0, 0, colSpan=4 )
    scriptDialog.AddControlToGrid( "ColorChannelLabel", "SeparatorControl", "Color Channels", 1, 0, colSpan=4 )
    
    scriptDialog.AddSelectionControlToGrid( "BeautyPassBox", "CheckBoxControl", False, "Beauty", 2, 0, "If enabled, the specular Beauty pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "DiffuseIBLPassBox", "CheckBoxControl", False, "Diffuse IBL", 2, 1, "If enabled, the Diffuse IBL pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "DiffuseLightPassBox", "CheckBoxControl", False, "Diffuse Light", 2, 2, "If enabled, should the Diffuse Light pass be exported." )
    scriptDialog.AddSelectionControlToGrid( "DiffuseIndirectPassBox", "CheckBoxControl", False, "Diffuse Indirect", 2, 3, "If enabled, should the Diffuse Indirect pass be exported." )
    
    scriptDialog.AddSelectionControlToGrid( "IncandescencePassBox", "CheckBoxControl", False, "Incandescence", 3, 0, "If enabled, the Incandescence pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "BackgroundColorPassBox", "CheckBoxControl", False, "Background Color", 3, 1, "If enabled, the Background Color pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "SpecularReflectionPassBox", "CheckBoxControl", False, "Specular Reflection", 3, 2, "If enabled, should the Specular Reflection pass be exported." )
    scriptDialog.AddSelectionControlToGrid( "GlossyIBLPassBox", "CheckBoxControl", False, "Glossy IBL", 3, 3, "If enabled, should the Glossy IBL pass be exported." )
    
    scriptDialog.AddSelectionControlToGrid( "GlossyLightPassBox", "CheckBoxControl", False, "Glossy Light", 4, 0, "If enabled, the specular Glossy Light pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "GlossyIndirectPassBox", "CheckBoxControl", False, "Glossy Indirect", 4, 1, "If enabled, the Glossy Indirect pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "TranslucentPassBox", "CheckBoxControl", False, "Translucent", 4, 2, "If enabled, should the Translucent pass be exported." )
    scriptDialog.AddSelectionControlToGrid( "TransparencyColorPassBox", "CheckBoxControl", False, "Transparency Color", 4, 3, "If enabled, should the Transparency Color pass be exported." )
    
    scriptDialog.AddControlToGrid( "AuxChannelLabel", "SeparatorControl", "Auxiliary Channels", 5, 0, colSpan=4 )
    
    scriptDialog.AddSelectionControlToGrid( "OcclusionPassBox", "CheckBoxControl", False, "Occlusion", 6, 0, "If enabled, the specular Occlusion pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "MaskPassBox", "CheckBoxControl", False, "Mask", 6, 1, "If enabled, the Mask pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "MaterialIDPassBox", "CheckBoxControl", False, "Material ID", 6, 2, "If enabled, should the Material ID pass be exported." )
    scriptDialog.AddSelectionControlToGrid( "DepthPassBox", "CheckBoxControl", False, "Depth", 6, 3, "If enabled, should the Depth pass be exported." )
    
    scriptDialog.AddSelectionControlToGrid( "NormalPassBox", "CheckBoxControl", False, "Normal", 7, 0, "If enabled, the Specular Normal pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "PositionPassBox", "CheckBoxControl", False, "Position", 7, 1, "If enabled, the Position pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "ViewVectorPassBox", "CheckBoxControl", False, "View Vector", 7, 2, "If enabled, should the View Vector pass be exported." )
    
    scriptDialog.AddControlToGrid( "SeparatedChannelLabel", "SeparatorControl", "Separated Channels", 8, 0, colSpan=4 )
    scriptDialog.AddControlToGrid( "MaterialChannelLabel", "SeparatorControl", "Material Channels", 9, 0, colSpan=4 )
    
    scriptDialog.AddSelectionControlToGrid( "DiffuseColorPassBox", "CheckBoxControl", False, "Diffuse Color", 10, 0, "If enabled, should the Diffuse Color pass be exported." )
    scriptDialog.AddSelectionControlToGrid( "GlossyColorPassBox", "CheckBoxControl", False, "Glossy Color", 10, 1, "If enabled, the Glossy Color pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "SpecularColorPassBox", "CheckBoxControl", False, "Specular Color", 10, 2, "If enabled, the Specular Color pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "TranslucencyColorPassBox", "CheckBoxControl", False, "Translucency Color", 10, 3, "If enabled, should the Translucency Color pass be exported." )
    
    scriptDialog.AddControlToGrid( "IlluminationChannelLabel", "SeparatorControl", "Illumination Channels", 11, 0, colSpan=4 )
    
    scriptDialog.AddSelectionControlToGrid( "IBLDiffusePassBox", "CheckBoxControl", False, "IBL Diffuse", 12, 0, "If enabled, should the IBL Diffuse pass be exported." )
    scriptDialog.AddSelectionControlToGrid( "LightsDiffusePassBox", "CheckBoxControl", False, "Lights Diffuse", 12, 1, "If enabled, should the Lights Diffuse pass be exported." )
    scriptDialog.AddSelectionControlToGrid( "IndirectDiffusePassBox", "CheckBoxControl", False, "Indirect Diffuse", 12, 2, "If enabled, the Indirect Diffuse pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "IBLGlossyPassBox", "CheckBoxControl", False, "IBL Glossy", 12, 3, "If enabled, the IBL Glossy pass will be exported." )
    
    scriptDialog.AddSelectionControlToGrid( "LightsGlossyPassBox", "CheckBoxControl", False, "Lights Glossy", 13, 0, "If enabled, should the Lights Glossy pass be exported." )
    scriptDialog.AddSelectionControlToGrid( "IndirectGlossyPassBox", "CheckBoxControl", False, "Indirect Glossy", 13, 1, "If enabled, should the Indirect Glossy pass be exported." )
    scriptDialog.AddSelectionControlToGrid( "IBLTranslucencyPassBox", "CheckBoxControl", False, "IBL Translucency", 13, 2, "If enabled, the IBL Translucency pass will be exported." )
    scriptDialog.AddSelectionControlToGrid( "LightTranslucencyPassBox", "CheckBoxControl", False, "Light Translucency", 13, 3, "If enabled, the Light Translucency pass will be exported." )
    
    scriptDialog.AddSelectionControlToGrid( "IndirectTranslucencyPassBox", "CheckBoxControl", False, "Indirect Translucency", 14, 0, "If enabled, should the Indirect Translucency pass be exported." )
    scriptDialog.AddSelectionControlToGrid( "IndirectSpecularPassBox", "CheckBoxControl", False, "Indirect Specular", 14, 1, "If enabled, should the Indirect Specular pass be exported." )
    
    scriptDialog.AddControlToGrid( "MetaDataLabel", "SeparatorControl", "Meta Data", 15, 0, colSpan=4 )
    
    scriptDialog.AddSelectionControlToGrid( "EmbedRenderSettingsBox", "CheckBoxControl", False, "Render Settings", 16, 0, "If enabled, the Render Settings will be embedded." )
    scriptDialog.AddSelectionControlToGrid( "EmbedCameraSettingsBox", "CheckBoxControl", False, "Camera Settings", 16, 1, "If enabled, the Camera Settings will be embedded." )
    scriptDialog.AddSelectionControlToGrid( "EmbedNodeVisibilitiesBox", "CheckBoxControl", False, "Node Visibilities", 16, 2, "If enabled, the Node Visibilities will be embedded." )
    scriptDialog.AddSelectionControlToGrid( "EmbedSwitchNodeStatesBox", "CheckBoxControl", False, "Switch Node States", 16, 3, "If enabled, the Switch Node States will be embedded." )

    scriptDialog.AddSelectionControlToGrid( "EmbedSwitchMaterialStatesBox", "CheckBoxControl", False, "Switch Material States", 17, 0, "If enabled, the Switch Material States will be embedded." )

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "VREDMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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

    settings = ( "DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","BongoBox","SubmitSceneBox","VersionBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    JobTypeChanged()
    
    scriptDialog.ShowDialog( False )
    
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "VREDSettings.ini" )

def JobTypeChanged( *args ):
    global scriptDialog
    
    RenderEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Render")
    isAnimation = scriptDialog.GetValue( "RenderAnimationCheck" )
    RenderQueueEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Render Queue")
    SequencerEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Sequencer")

    scriptDialog.SetEnabled( "OutputLabel", RenderEnabled )
    scriptDialog.SetEnabled( "OutputBox", RenderEnabled )
    scriptDialog.SetEnabled( "FramesLabel", RenderEnabled and isAnimation )
    scriptDialog.SetEnabled( "FramesBox", RenderEnabled and isAnimation )

    scriptDialog.SetEnabled( "AnimationLabel", RenderEnabled and isAnimation )
    scriptDialog.SetEnabled( "AnimationBox", RenderEnabled and isAnimation )

    scriptDialog.SetEnabled( "DPILabel", RenderEnabled and not isAnimation )
    scriptDialog.SetEnabled( "DPIBox", RenderEnabled and not isAnimation )

    scriptDialog.SetEnabled( "ViewLabel", RenderEnabled )
    scriptDialog.SetEnabled( "ViewBox", RenderEnabled )

    scriptDialog.SetEnabled( "RenderWidthLabel", RenderEnabled )
    scriptDialog.SetEnabled( "RenderWidthBox", RenderEnabled )
    scriptDialog.SetEnabled( "RenderHeightLabel", RenderEnabled )
    scriptDialog.SetEnabled( "RenderHeightBox", RenderEnabled )
    scriptDialog.SetEnabled( "SuperSamplingLabel", RenderEnabled )
    scriptDialog.SetEnabled( "SuperSamplingBox", RenderEnabled )
    scriptDialog.SetEnabled( "BackgroundColorLabel", RenderEnabled )
    scriptDialog.SetEnabled( "BackgroundColorBox", RenderEnabled )

    scriptDialog.SetEnabled( "RenderQualityLabel", RenderEnabled )
    scriptDialog.SetEnabled( "RenderQualityBox", RenderEnabled )
    
    scriptDialog.SetEnabled( "OverrideRenderPassBox", RenderEnabled )
    scriptDialog.SetEnabled( "OverrideMetaDataBox", RenderEnabled )
    
    scriptDialog.SetEnabled( "SequenceNameLabel", SequencerEnabled )
    scriptDialog.SetEnabled( "SequenceNameBox", SequencerEnabled )
    
    ChangeRenderQuality()
    ChangeOutputFilename()

def ChangeOutputFilename( *args ):
    global scriptDialog

    outputFilename = scriptDialog.GetValue("OutputBox")
    RenderEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Render")
    isAnimation = scriptDialog.GetValue( "RenderAnimationCheck" )
    RenderQueueEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Render Queue")
    SequencerEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Sequencer")
    
    scriptDialog.SetEnabled( "AlphaChannelBox", allowsAlpha(outputFilename) and RenderEnabled )
    
    #scriptDialog.SetEnabled( "fpsLabel", outputFilename.endswith(".avi") and not RenderQueueEnabled )
    #scriptDialog.SetEnabled( "fpsBox", outputFilename.endswith(".avi") and not RenderQueueEnabled )   
    
    scriptDialog.SetEnabled( "ChunkSizeLabel", not outputFilename.endswith(".avi") and RenderEnabled and isAnimation )
    scriptDialog.SetEnabled( "ChunkSizeBox", not outputFilename.endswith(".avi") and RenderEnabled and isAnimation )
    
    allowsMetaData = outputFilename.endswith("png") or outputFilename.endswith("jpg") or outputFilename.endswith("tif")
    
    scriptDialog.SetEnabled( "EmbedMetaDataBox", allowsMetaData and RenderEnabled )
    
    scriptDialog.SetEnabled( "ToneMapBox", RenderEnabled and ( outputFilename.endswith( ".hdr" ) or outputFilename.endswith( ".exr" ) or outputFilename.endswith( ".tiff" ) ) )
    
    ChangeAlphaChannelBox()
    ChangeEmbedMeta()

def ChangeEmbedMeta( *args ):
    global scriptDialog

    embedMetaEnabled = scriptDialog.GetEnabled( "EmbedMetaDataBox" )
    embedMetaValue = scriptDialog.GetValue( "EmbedMetaDataBox" )
    
    scriptDialog.SetEnabled( "MetaDataLabel", embedMetaEnabled and embedMetaValue )
    scriptDialog.SetEnabled( "EmbedRenderSettingsBox", embedMetaEnabled and embedMetaValue )
    scriptDialog.SetEnabled( "EmbedCameraSettingsBox", embedMetaEnabled and embedMetaValue )
    scriptDialog.SetEnabled( "EmbedNodeVisibilitiesBox", embedMetaEnabled and embedMetaValue )
    scriptDialog.SetEnabled( "EmbedSwitchNodeStatesBox", embedMetaEnabled and embedMetaValue )
    scriptDialog.SetEnabled( "EmbedSwitchMaterialStatesBox", embedMetaEnabled and embedMetaValue )    
    
def ChangeAlphaChannelBox( *args ):
    global scriptDialog

    alphaChannelBoxEnabled = scriptDialog.GetEnabled("AlphaChannelBox")
    alphaChannelBoxValue = scriptDialog.GetValue("AlphaChannelBox")
    
    scriptDialog.SetEnabled( "AlphaPremultiplyBox", alphaChannelBoxEnabled and alphaChannelBoxValue )
    
def ChangeRenderQuality( *args ):
    global scriptDialog

    RenderEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Render")
    isAnimation = scriptDialog.GetValue( "RenderAnimationCheck" )
    RenderQueueEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Render Queue")
    SequencerEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Sequencer")
    RenderQuality = scriptDialog.GetValue( "RenderQualityBox" )
    
    scriptDialog.SetEnabled( "ExportRenderPassBox", RenderEnabled and RenderQuality == "Raytracing" )
    ChangeExportRenderPass()
    
def ChangeExportRenderPass( *args ):
    global scriptDialog

    RenderPassEnabled = scriptDialog.GetEnabled( "ExportRenderPassBox" ) 
    RenderPassValue = scriptDialog.GetValue( "ExportRenderPassBox" )
    RenderQuality = scriptDialog.GetValue( "RenderQualityBox" )
    passEnabled = RenderPassEnabled and RenderPassValue and RenderQuality == "Raytracing"
    
    scriptDialog.SetEnabled( "CombinedChannelLabel", passEnabled )
    scriptDialog.SetEnabled( "ColorChannelLabel", passEnabled )
    scriptDialog.SetEnabled( "AuxChannelLabel", passEnabled )
    scriptDialog.SetEnabled( "MaterialChannelLabel", passEnabled )
    scriptDialog.SetEnabled( "IlluminationChannelLabel", passEnabled )
    scriptDialog.SetEnabled( "BeautyPassBox", passEnabled )
    scriptDialog.SetEnabled( "DiffuseIBLPassBox", passEnabled )
    scriptDialog.SetEnabled( "DiffuseLightPassBox", passEnabled )
    scriptDialog.SetEnabled( "DiffuseIndirectPassBox", passEnabled )
    scriptDialog.SetEnabled( "IncandescencePassBox", passEnabled )
    scriptDialog.SetEnabled( "BackgroundColorPassBox", passEnabled )
    scriptDialog.SetEnabled( "SpecularReflectionPassBox", passEnabled )
    scriptDialog.SetEnabled( "GlossyIBLPassBox", passEnabled )
    scriptDialog.SetEnabled( "GlossyLightPassBox", passEnabled )
    scriptDialog.SetEnabled( "GlossyIndirectPassBox", passEnabled )
    scriptDialog.SetEnabled( "TranslucentPassBox", passEnabled )
    scriptDialog.SetEnabled( "TransparencyColorPassBox", passEnabled )
    scriptDialog.SetEnabled( "OcclusionPassBox", passEnabled )
    scriptDialog.SetEnabled( "MaskPassBox", passEnabled )
    scriptDialog.SetEnabled( "MaterialIDPassBox", passEnabled )
    scriptDialog.SetEnabled( "DepthPassBox", passEnabled )
    scriptDialog.SetEnabled( "NormalPassBox", passEnabled )
    scriptDialog.SetEnabled( "PositionPassBox", passEnabled )
    scriptDialog.SetEnabled( "ViewVectorPassBox", passEnabled )
    
    scriptDialog.SetEnabled( "SeparatedChannelLabel", passEnabled )
    scriptDialog.SetEnabled( "DiffuseColorPassBox", passEnabled )
    scriptDialog.SetEnabled( "GlossyColorPassBox", passEnabled )
    scriptDialog.SetEnabled( "SpecularColorPassBox", passEnabled )
    scriptDialog.SetEnabled( "TranslucencyColorPassBox", passEnabled )
    scriptDialog.SetEnabled( "IBLDiffusePassBox", passEnabled )
    scriptDialog.SetEnabled( "LightsDiffusePassBox", passEnabled )
    scriptDialog.SetEnabled( "IndirectDiffusePassBox", passEnabled )
    scriptDialog.SetEnabled( "IBLGlossyPassBox", passEnabled )
    scriptDialog.SetEnabled( "LightsGlossyPassBox", passEnabled )
    scriptDialog.SetEnabled( "IndirectGlossyPassBox", passEnabled )
    scriptDialog.SetEnabled( "IBLTranslucencyPassBox", passEnabled )
    scriptDialog.SetEnabled( "LightTranslucencyPassBox", passEnabled )
    scriptDialog.SetEnabled( "IndirectTranslucencyPassBox", passEnabled )
    scriptDialog.SetEnabled( "IndirectSpecularPassBox", passEnabled )

def allowsAlpha( filename ):
    formats = [".dib",".dds",".exr",".hdr",".jfif",".jpe",".nrrd",".pgm",".pcx",".png",".pnm",".ppm",".psb",".psd",".rle",".tif",".tiff",".vif"]
    filename = str(filename)
    for format in formats:
        if filename.endswith(format):
            return True
    return False

def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    global versionOptions

    try:
        # Check vred file.
        sceneFile = scriptDialog.GetValue( "SceneBox" )
        submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
        if( not File.Exists( sceneFile ) ):
            scriptDialog.ShowMessageBox( "VRED project file %s does not exist" % sceneFile, "Error" )
            return
        elif( not submitScene and PathUtils.IsPathLocal( sceneFile ) ):
            result = scriptDialog.ShowMessageBox( "The VRED project file " + sceneFile + " is local and is not being submitted with the job, are you sure you want to continue", "Warning", ("Yes","No") )
            if( result == "No" ):
                return
        
        # Check output file.
        outputFile = (scriptDialog.GetValue( "OutputBox" )).strip()
        frames = scriptDialog.GetValue( "FramesBox" )
        
        RenderEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Render")
        isAnimation = scriptDialog.GetValue( "RenderAnimationCheck" )
        RenderQueueEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Render Queue")
        SequencerEnabled = (scriptDialog.GetValue( "JobTypeBox" ) == "Sequencer")
        
        if RenderEnabled:
            if( len( outputFile ) == 0 ):
                scriptDialog.ShowMessageBox( "Please specify an output file", "Error" )
                return
            elif( not Directory.Exists( Path.GetDirectoryName( outputFile ) ) ):
                scriptDialog.ShowMessageBox( "Directory for output file %s does not exist" % outputFile, "Error" )
                return
            elif( PathUtils.IsPathLocal( outputFile ) ):
                result = scriptDialog.ShowMessageBox( "Output file " + outputFile + " is local, are you sure you want to continue", "Warning", ("Yes","No") )
                if( result == "No" ):
                    return
            if isAnimation:
                # Check if a valid frame range has been specified.
                if( not FrameUtils.FrameRangeValid( frames ) ):
                    scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
                    return

        # Check if Integration options are valid.
        if not integration_dialog.CheckIntegrationSanity( outputFile ):
            return
        
        jobName = scriptDialog.GetValue( "NameBox" )

        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "vred_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=VRED" )
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
        
        if RenderEnabled and isAnimation:
            writer.WriteLine( "Frames=%s" % frames )
            animationFileName,animationFileExt = os.path.splitext(outputFile)
            writer.WriteLine( "OutputFilename0=%s" %( animationFileName + "-#####" + animationFileExt )  )
        else:
            writer.WriteLine( "Frames=0" )
            if RenderEnabled:
                writer.WriteLine( "OutputFilename0=%s" % outputFile )

        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        
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
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "vred_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        if not submitScene:
            writer.WriteLine( "SceneFile=%s" % sceneFile )
        writer.WriteLine( "OutputFile=%s" % outputFile )
        
        ver = scriptDialog.GetValue( "VersionBox" )
        version = versionOptions.get(ver, "11.0")

        writer.WriteLine( "Version=%s" % version )
        writer.WriteLine( "JobType=%s" % scriptDialog.GetValue( "JobTypeBox" ) )
        writer.WriteLine( "RenderAnimation=%s" % isAnimation )
        writer.WriteLine( "AnimationClip=%s" % scriptDialog.GetValue( "AnimationBox" ) )
        writer.WriteLine( "View=%s" % scriptDialog.GetValue( "ViewBox" ) )
        writer.WriteLine( "RenderWidth=%s" % scriptDialog.GetValue( "RenderWidthBox" ) )
        writer.WriteLine( "RenderHeight=%s" % scriptDialog.GetValue( "RenderHeightBox" ) )
        writer.WriteLine( "SuperSamplingFactor=%s" % scriptDialog.GetValue( "SuperSamplingBox" ) )
        
        bgColor = scriptDialog.GetValue( "BackgroundColorBox" )
        
        writer.WriteLine( "BackgroundRed=%s" % (bgColor.R/255.0)  )
        writer.WriteLine( "BackgroundBlue=%s" % (bgColor.G/255.0) )
        writer.WriteLine( "BackgroundGreen=%s" % (bgColor.B/255.0) )
        
        writer.WriteLine( "IncludeAlphaChannel=%s" % scriptDialog.GetValue( "AlphaChannelBox" ) )
        writer.WriteLine( "PremultiplyAlpha=%s" % scriptDialog.GetValue( "AlphaPremultiplyBox" ) )
        writer.WriteLine( "TonemapHDR=%s" % scriptDialog.GetValue( "ToneMapBox" ) )
        #writer.WriteLine( "FramesPerSecond=%s" % scriptDialog.GetValue( "fpsBox" ) )
        
        writer.WriteLine( "DPI=%s" % scriptDialog.GetValue( "DPIBox" ) )
        
        writer.WriteLine( "RenderQuality=%s" % scriptDialog.GetValue( "RenderQualityBox" ) )
        
        writer.WriteLine( "OverrideRenderPass=%s" % scriptDialog.GetValue( "OverrideRenderPassBox" ) )
        writer.WriteLine( "ExportRenderPass=%s" % scriptDialog.GetValue( "ExportRenderPassBox" ) )
        
        writer.WriteLine( "BeautyPass=%s" % scriptDialog.GetValue( "BeautyPassBox" ) )
        writer.WriteLine( "DiffuseIBLPass=%s" % scriptDialog.GetValue( "DiffuseIBLPassBox" ) )
        writer.WriteLine( "DiffuseLightPass=%s" % scriptDialog.GetValue( "DiffuseLightPassBox" ) )
        writer.WriteLine( "DiffuseIndirectPass=%s" % scriptDialog.GetValue( "DiffuseIndirectPassBox" ) )
        writer.WriteLine( "IncandescencePass=%s" % scriptDialog.GetValue( "IncandescencePassBox" ) )
        writer.WriteLine( "BackgroundColorPass=%s" % scriptDialog.GetValue( "BackgroundColorPassBox" ) )
        writer.WriteLine( "SpecularReflectionPass=%s" % scriptDialog.GetValue( "SpecularReflectionPassBox" ) )
        writer.WriteLine( "GlossyIBLPass=%s" % scriptDialog.GetValue( "GlossyIBLPassBox" ) )
        writer.WriteLine( "GlossyLightPass=%s" % scriptDialog.GetValue( "GlossyLightPassBox" ) )
        writer.WriteLine( "GlossyLightPass=%s" % scriptDialog.GetValue( "GlossyLightPassBox" ) )
        writer.WriteLine( "GlossyIndirectPass=%s" % scriptDialog.GetValue( "GlossyIndirectPassBox" ) )
        writer.WriteLine( "TranslucentPass=%s" % scriptDialog.GetValue( "TranslucentPassBox" ) )
        writer.WriteLine( "TransparencyColorPass=%s" % scriptDialog.GetValue( "TransparencyColorPassBox" ) )
        writer.WriteLine( "OcclusionPass=%s" % scriptDialog.GetValue( "OcclusionPassBox" ) )
        writer.WriteLine( "MaskPass=%s" % scriptDialog.GetValue( "MaskPassBox" ) )
        writer.WriteLine( "MaterialIDPass=%s" % scriptDialog.GetValue( "MaterialIDPassBox" ) )
        writer.WriteLine( "DepthPass=%s" % scriptDialog.GetValue( "DepthPassBox" ) )
        writer.WriteLine( "NormalPass=%s" % scriptDialog.GetValue( "NormalPassBox" ) )
        writer.WriteLine( "PositionPass=%s" % scriptDialog.GetValue( "PositionPassBox" ) )
        writer.WriteLine( "ViewVectorPass=%s" % scriptDialog.GetValue( "ViewVectorPassBox" ) )
        writer.WriteLine( "DiffuseColorPass=%s" % scriptDialog.GetValue( "DiffuseColorPassBox" ) )
        writer.WriteLine( "GlossyColorPass=%s" % scriptDialog.GetValue( "GlossyColorPassBox" ) )
        writer.WriteLine( "SpecularColorPass=%s" % scriptDialog.GetValue( "SpecularColorPassBox" ) )
        writer.WriteLine( "TranslucencyColorPass=%s" % scriptDialog.GetValue( "TranslucencyColorPassBox" ) )
        writer.WriteLine( "IBLDiffusePass=%s" % scriptDialog.GetValue( "IBLDiffusePassBox" ) )
        writer.WriteLine( "LightsDiffusePass=%s" % scriptDialog.GetValue( "LightsDiffusePassBox" ) )
        writer.WriteLine( "IndirectDiffusePass=%s" % scriptDialog.GetValue( "IndirectDiffusePassBox" ) )
        writer.WriteLine( "IBLGlossyPass=%s" % scriptDialog.GetValue( "IBLGlossyPassBox" ) )
        writer.WriteLine( "LightsGlossyPass=%s" % scriptDialog.GetValue( "LightsGlossyPassBox" ) )
        writer.WriteLine( "IndirectGlossyPass=%s" % scriptDialog.GetValue( "IndirectGlossyPassBox" ) )
        writer.WriteLine( "IBLTranslucencyPass=%s" % scriptDialog.GetValue( "IBLTranslucencyPassBox" ) )
        writer.WriteLine( "LightTranslucencyPass=%s" % scriptDialog.GetValue( "LightTranslucencyPassBox" ) )
        writer.WriteLine( "IndirectTranslucencyPass=%s" % scriptDialog.GetValue( "IndirectTranslucencyPassBox" ) )
        writer.WriteLine( "IndirectSpecularPass=%s" % scriptDialog.GetValue( "IndirectSpecularPassBox" ) )
        
        writer.WriteLine( "OverrideMetaData=%s" % scriptDialog.GetValue( "OverrideMetaDataBox" ) )
        writer.WriteLine( "EmbedMetaData=%s" % scriptDialog.GetValue( "EmbedMetaDataBox" ) )
        
        writer.WriteLine( "EmbedRenderSettings=%s" % scriptDialog.GetValue( "EmbedRenderSettingsBox" ) )
        writer.WriteLine( "EmbedCameraSettings=%s" % scriptDialog.GetValue( "EmbedCameraSettingsBox" ) )
        writer.WriteLine( "EmbedNodeVisibilities=%s" % scriptDialog.GetValue( "EmbedNodeVisibilitiesBox" ) )
        writer.WriteLine( "EmbedSwitchNodeStates=%s" % scriptDialog.GetValue( "EmbedSwitchNodeStatesBox" ) )
        writer.WriteLine( "EmbedSwitchMaterialStates=%s" % scriptDialog.GetValue( "EmbedSwitchMaterialStatesBox" ) )
        
        writer.WriteLine( "SequenceName=%s" % scriptDialog.GetValue( "SequenceNameBox" ) )
        
        writer.Close()

        # Setup the command line arguments.
        arguments = StringCollection()

        arguments.Add( jobInfoFilename )
        arguments.Add( pluginInfoFilename )
        if submitScene:
            arguments.Add( sceneFile )

        # Now submit the job.
        results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        scriptDialog.ShowMessageBox( results, "Submission Results" )

    except:
        scriptDialog.ShowMessageBox( traceback.format_exc(), "Error" )
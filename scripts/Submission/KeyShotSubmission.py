from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

import json
import traceback

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

ProjectManagementOptions = ["Shotgun","FTrack","NIM"]
DraftRequested = True

qualityTypeOptions = [ "Advanced Control", "Maximum Time", "Maximum Samples" ]

passInformationDict = {
    "DiffusePassBox": ( "output_diffuse_pass","Diffuse Pass", 3, 0, "IncludeDiffusePass" ),
    "ReflectionPassBox":( "output_reflection_pass","Reflection Pass", 3, 1, "IncludeReflectionPass" ),
    "ClownPassBox":( "output_clown_pass","Clown Pass", 3, 2, "IncludeClownPass" ),
    "LightingPassBox":( "output_direct_lighting_pass","Lighting Pass", 4, 0, "IncludeLightingPass" ),
    "RefractionPassBox":( "output_refraction_pass","Refraction Pass", 4, 1, "IncludeRefractionPass" ),
    "DepthPassBox":( "output_depth_pass","Depth Pass", 4, 2, "IncludeDepthPass" ),
    "GIPassBox":( "output_indirect_lighting_pass","Global Illumination Pass", 5, 0, "IncludeGIPass" ),
    "ShadowPassBox":( "output_shadow_pass","Shadow Pass", 5, 1, "IncludeShadowPass" ),
    "NormalsPassBox":( "output_normals_pass","Normals Pass", 5, 2, "IncludeNormalsPass" ),
    "CausticsPassBox":( "output_caustics_pass","Caustics Pass", 6, 0, "IncludeCausticsPass" ),
    "AOPassBox":( "output_ambient_occlusion_pass","Ambient Occlusion Pass", 6, 1 , "IncludeAOPass")
}

qualityLabelDict = {
    "MaxTimeLabel" : "Maximum Time",
    
    "ProgressiveMaxSamplesLabel" : "Maximum Samples",
    
    "AdvancedMaxSamplesLabel" : "Advanced Control",
    "GlobalIlluminationLabel" : "Advanced Control",
    "RayBouncesLabel" : "Advanced Control",
    "PixelBlurLabel" : "Advanced Control",
    "AntiAliasingLabel" : "Advanced Control",
    "DepthOfFieldLabel" : "Advanced Control",
    "ShadowLabel" : "Advanced Control",
    "CausticsLabel" : "Advanced Control"
 }

qualityOptionDict = {
    "MaxTimeBox" : ( "progressive_max_time", "Maximum Time", "MaxTime" ),
    
    "ProgressiveMaxSamplesBox" : ( "progressive_max_samples", "Maximum Samples", "ProgressiveMaxSamples" ),
    
    "AdvancedMaxSamplesBox" : ( "advanced_samples", "Advanced Control", "AdvancedMaxSamples" ),
    "GlobalIlluminationBox" : ( "engine_global_illumination", "Advanced Control", "GlobalIllumination" ),
    "RayBouncesBox" : ( "engine_ray_bounces", "Advanced Control", "RayBounces" ),
    "PixelBlurBox" : ( "engine_pixel_blur", "Advanced Control", "PixelBlur" ),
    "AntiAliasingBox" : ( "engine_anti_aliasing", "Advanced Control", "AntiAliasing" ),
    "DepthOfFieldBox" : ( "engine_dof_quality", "Advanced Control", "DepthOfField" ),
    "ShadowBox" : ( "engine_shadow_quality", "Advanced Control", "Shadows" ),
    "CausticsBox" : ( "engine_caustics_quality", "Advanced Control", "Caustics" ),
    "SharpShadowsBox" : ( "engine_sharp_shadows", "Advanced Control", "SharpShadows" ),
    "SharperTextureFilteringBox" : ( "engine_sharper_texture_filtering", "Advanced Control", "SharperTextureFiltering" ),
    "GlobalIlluminationCacheBox" : ( "engine_global_illumination_cache", "Advanced Control", "GICache" )
}

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global ProjectManagementOptions
    global DraftRequested
    global integration_dialog
    global passInformationDict
    global qualityOptionDict
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit KeyShot Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'KeyShot' ) )
    
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
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=4 )

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
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. ", colSpan=2 )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator.", colSpan=2 )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "", colSpan=2 )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering. ", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes. ", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render. ", colSpan=2 )
    
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "KeyShot Options", 12, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "KeyShot File", 13, 0, "The KeyShot project file to be rendered.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "All Files (*)", 13, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 14, 0, "The KeyShot application version to use.", False )
    scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "8", ("6","7", "8"), 14, 1 )
    
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit KeyShot Project File", 14, 2, "If this option is enabled, the project file will be submitted with the job, and then copied locally to the slave machine during rendering.", colSpan=2 )
    
    scriptDialog.AddControlToGrid( "OutputLabel","LabelControl","Output File", 15, 0, "The filename of the image(s) to be rendered.", False )
    outputBox = scriptDialog.AddSelectionControlToGrid("OutputBox","FileSaverControl","","JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff);;EXR (*.exr);;PNG (*.png);;All files (*)", 15, 1, colSpan=3)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 16, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 16, 1 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 16, 2, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 16, 3 )    

    scriptDialog.AddControlToGrid( "RenderWidthLabel", "LabelControl", "Render Width", 17, 0, "The width of the images rendered.", False )
    scriptDialog.AddRangeControlToGrid( "RenderWidthBox", "RangeControl", 1920, 1, 1000000, 0, 1, 17, 1 )
    scriptDialog.AddControlToGrid( "RenderHeightLabel", "LabelControl", "Render Height", 17, 2, "The height of the images rendered.", False )
    scriptDialog.AddRangeControlToGrid( "RenderHeightBox", "RangeControl", 1080, 1, 1000000, 0, 1, 17, 3 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Additional Options")
    scriptDialog.AddGrid()

    scriptDialog.AddSelectionControlToGrid( "RenderLayersBox", "CheckBoxControl", False, "Include All Render Layers", 0, 0, "If this option is enabled, all render layers will be rendered separately." )
    scriptDialog.AddSelectionControlToGrid( "IncludeAlphaBox", "CheckBoxControl", False, "Include Alpha (Transparency)", 0, 1, "If this option is enabled, the final image will include alpha." )

    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Render Pass Options", 1, 0, colSpan=2 )

    overrideRenderPassesBox = scriptDialog.AddSelectionControlToGrid( "overrideRenderPassesBox", "CheckBoxControl", False, "Override Render Passes", 2, 0, "If this option is enabled, the output pass settings in the scene will be overridden." )
    overrideRenderPassesBox.ValueModified.connect( OverrideRenderPassesChanged )
    
    for passBox, passInfo in passInformationDict.iteritems():
        scriptDialog.AddSelectionControlToGrid( passBox, "CheckBoxControl", False, passInfo[1], passInfo[2], passInfo[3], ("If this option is enabled, the %s will be output." % passInfo[1].lower() ) )
    
    scriptDialog.EndGrid()    
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Render Quality Options", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "QualityTypeLabel", "LabelControl", "Quality to Render By", 1, 0, "The type of quality to render by.", False )
    qualityTypeBox = scriptDialog.AddComboControlToGrid( "QualityTypeBox", "ComboControl", "", qualityTypeOptions, 1, 1 )
    qualityTypeBox.ValueModified.connect( QualityTypeChanged )
        
    scriptDialog.AddControlToGrid( "AdvancedSamplesSeparator", "SeparatorControl", "Advanced Options", 2, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "AdvancedMaxSamplesLabel", "LabelControl", "Maximum Samples", 3, 0, "Maximum number of samples to render.", False )
    scriptDialog.AddRangeControlToGrid( "AdvancedMaxSamplesBox", "RangeControl", 16, 4, 256, 0, 1, 3, 1 )
    scriptDialog.AddControlToGrid( "GlobalIlluminationLabel", "LabelControl", "Global Illumination", 3, 2, "This will control the quality of all indirect light. If Global Illumination is turned on.", False )
    scriptDialog.AddRangeControlToGrid( "GlobalIlluminationBox", "RangeControl", 1, 1, 5, 3, 1, 3, 3 )
    
    scriptDialog.AddControlToGrid( "RayBouncesLabel", "LabelControl", "Ray Bounces", 4, 0, "Number of times light is reflected/refracted as it passes through a scene.", False )
    scriptDialog.AddRangeControlToGrid( "RayBouncesBox", "RangeControl", 6, 0, 64, 0, 1, 4, 1 )
    scriptDialog.AddControlToGrid( "PixelBlurLabel", "LabelControl", "Pixel Blur", 4, 2, "Number of times light is reflected/refracted as it passes through a scene.", False )
    scriptDialog.AddRangeControlToGrid( "PixelBlurBox", "RangeControl", 1.5, 1, 3, 3, 1, 4, 3 )
    
    scriptDialog.AddControlToGrid( "AntiAliasingLabel", "LabelControl", "Anti Aliasing", 5, 0, "Anti aliasing is a method for smoothing out jagged edges that are created by pixels.", False )
    scriptDialog.AddRangeControlToGrid( "AntiAliasingBox", "RangeControl", 1, 1, 8, 0, 1, 5, 1 )
    scriptDialog.AddControlToGrid( "DepthOfFieldLabel", "LabelControl", "Depth of Field", 5, 2, "This will control the quality of depth of field if it is enabled in the camera tab.", False )
    scriptDialog.AddRangeControlToGrid( "DepthOfFieldBox", "RangeControl", 3, 1, 10, 0, 1, 5, 3 )
    
    scriptDialog.AddControlToGrid( "ShadowLabel", "LabelControl", "Shadow Quality", 6, 0, "Shadow quality will control the shadow quality for ground shadows.", False )
    scriptDialog.AddRangeControlToGrid( "ShadowBox", "RangeControl", 1, 1, 10, 3, 1, 6, 1 )
    scriptDialog.AddControlToGrid( "CausticsLabel", "LabelControl", "Caustics", 6, 2, "Increasing this value will improve the samples and quality of the caustics.", False )
    scriptDialog.AddRangeControlToGrid( "CausticsBox", "RangeControl", 1, 1, 10, 3, 1, 6, 3 )
    
    scriptDialog.AddSelectionControlToGrid( "SharpShadowsBox", "CheckBoxControl", False, "Sharp Shadows", 7, 0, "", colSpan=2 )
    scriptDialog.AddSelectionControlToGrid( "SharperTextureFilteringBox", "CheckBoxControl", False, "Sharper Texture Filtering", 7, 2, "", colSpan=2 )
    scriptDialog.AddSelectionControlToGrid( "GlobalIlluminationCacheBox", "CheckBoxControl", False, "Global Illumiation Cache", 8, 0, "", colSpan=2 )
    
    scriptDialog.AddControlToGrid( "TimeSeparator", "SeparatorControl", "Maximum Time Options", 9, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "MaxTimeLabel", "LabelControl", "Maximum Time (s)", 10, 0, "Maximum time spent rendering (in seconds).", False )
    scriptDialog.AddRangeControlToGrid( "MaxTimeBox", "RangeControl", 30, 1, 86400, 2, 1, 10, 1 )
    
    scriptDialog.AddControlToGrid( "SamplesSeparator", "SeparatorControl", "Maximum Samples Options", 11, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "ProgressiveMaxSamplesLabel", "LabelControl", " Maximum Samples", 12, 0, "Maximum number of samples to render.", False )
    scriptDialog.AddRangeControlToGrid( "ProgressiveMaxSamplesBox", "RangeControl", 16, 1, 256, 0, 1, 12, 1 )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    integration_dialog = IntegrationUI.IntegrationDialog()
    integration_dialog.AddIntegrationTabs( scriptDialog, "KeyShotMonitor", DraftRequested, ProjectManagementOptions, failOnNoTabs=False )
    
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

    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","SubmitSceneBox", "VersionBox")
    settings += tuple( passInformationDict.keys() )
    settings += tuple( qualityOptionDict.keys() )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    OverrideRenderPassesChanged( None )
    QualityTypeChanged( None )
    
    appSubmission = False
    if len( args ) > 0:
        appSubmission = True
        
        if args[0] == "":
            scriptDialog.ShowMessageBox( "The KeyShot scene must be saved before it can be submitted to Deadline.", "Error" )
            return
        
        scriptDialog.SetValue( "SceneBox", args[0] )
        scriptDialog.SetValue( "VersionBox", args[1] )
        scriptDialog.SetValue( "FramesBox", "0-"+args[2] )
        renderOptions = {}
        
        try:
            with open( args[3], "r" ) as optionsFile:
                renderOptions = json.load( optionsFile )
        except:
            pass
        
        scriptDialog.SetValue( "RenderLayersBox", renderOptions.get( "output_render_layers", scriptDialog.GetValue( "RenderLayersBox" ) ) )
        scriptDialog.SetValue( "IncludeAlphaBox", renderOptions.get( "output_alpha_channel", scriptDialog.GetValue( "IncludeAlphaBox" ) ) )
        
        for passBox, passInfo in passInformationDict.iteritems():
            scriptDialog.SetValue( passBox, renderOptions.get( passInfo[ 0 ], scriptDialog.GetValue( passBox ) ) )
        
        if renderOptions.get( "__VERSION", 0 ) < 4:
            maxTimeParam = renderOptions.get( "progressive_max_time", 0.0 )
            advancedSamplesParam = renderOptions.get( "advanced_samples", 16 )
            maxSamplesParam = renderOptions.get( "progressive_max_samples", 0 )
            
            if maxTimeParam == 0 and advancedSamplesParam == 0:
                scriptDialog.SetValue( "QualityTypeBox", "Maximum Samples" )
            elif maxTimeParam == 0 and advancedSamplesParam != 0:
                scriptDialog.SetValue( "QualityTypeBox", "Advanced Control" )
            else:
                scriptDialog.SetValue( "QualityTypeBox", "Maximum Time" )
        else:
            renderMode = renderOptions.get( "render_mode", 0 )
            
            scriptDialog.SetValue( "QualityTypeBox", qualityTypeOptions[ renderMode ] )
        
        
        for qualityBox, qualityOptions in qualityOptionDict.iteritems():
            scriptDialog.SetValue( qualityBox,  renderOptions.get( qualityOptions[ 0 ],  scriptDialog.GetValue( qualityBox ) ) )
        
    scriptDialog.ShowDialog( True )
    
def GetSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "KeyShotSettings.ini" )
    
def OverrideRenderPassesChanged( *args ):
    global scriptDialog
    global passInformationDict
    
    overrideRenderPassEnabled = scriptDialog.GetValue( "overrideRenderPassesBox" )
    
    for passBox in passInformationDict.keys():
        scriptDialog.SetEnabled( passBox, overrideRenderPassEnabled )
        
def QualityTypeChanged( *args ):
    global scriptDialog
    global qualityOptionDict
    global qualityLabelDict
    
    curQualityType = scriptDialog.GetValue( "QualityTypeBox" )
    
    for qualityBox, qualityOptions in qualityOptionDict.iteritems():
        qualityEnabled = ( curQualityType == qualityOptions[1] )
        scriptDialog.SetEnabled( qualityBox, qualityEnabled )
        
    for qualityLabel, qualityType in qualityLabelDict.iteritems():
        qualityEnabled = ( curQualityType == qualityType )
        scriptDialog.SetEnabled( qualityLabel, qualityEnabled )
    
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    global integration_dialog
    global passInformationDict
    global qualityOptionDict

    try:
        warnings = ""
        errors = ""

        # Check keyshot file.
        sceneFile = scriptDialog.GetValue( "SceneBox" )
        submitScene = scriptDialog.GetValue( "SubmitSceneBox" )
        if( not File.Exists( sceneFile ) ):
            errors += "KeyShot project file %s does not exist.\n\n" % sceneFile

        elif( not submitScene and PathUtils.IsPathLocal( sceneFile ) ):
            warnings += "The KeyShot project file " + sceneFile + " is local.\n\n"
        
        # Check output file.
        outputFile = (scriptDialog.GetValue( "OutputBox" )).strip()
        frames = scriptDialog.GetValue( "FramesBox" )
                
        if( len( outputFile ) == 0 ):
            errors += "Please specify an output file"

        elif( not Directory.Exists( Path.GetDirectoryName( outputFile ) ) ):
            warnings += "Directory for output file %s does not exist.\n\n" % outputFile

        elif( PathUtils.IsPathLocal( outputFile ) ):
            warnings += "Output file " + outputFile + " is local.\n\n"

        # Check if saving to single file (animation output should have multiple).
        if "%d" not in outputFile:
            warnings += "Output file should contain '%d' when rendering an animation in order to save each frame in a separate file.\n\n"
        
        # Check if Integration options are valid
        if not integration_dialog.CheckIntegrationSanity( outputFile ):
            return
            
        if len( errors ) > 0:
            scriptDialog.ShowMessageBox( "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % errors, "Errors" )
            return

        if len( warnings ) > 0:
                result = scriptDialog.ShowMessageBox( "Warnings:\n\n%s\nDo you still want to continue?" % warnings, "Warnings", ( "Yes","No" ) )
                if result == "No":
                    return

        jobName = scriptDialog.GetValue( "NameBox" )

        # Create job info file.
        jobInfoFilename = Path.Combine( GetDeadlineTempPath(), "keyshot_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=KeyShot" )
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
        if bool(scriptDialog.GetValue( "IsBlacklistBox" )):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        if bool(scriptDialog.GetValue( "SubmitSuspendedBox" )):
            writer.WriteLine( "InitialStatus=Suspended" )
        
        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        
        # Integration
        extraKVPIndex = 0
        groupBatch = False
        if integration_dialog.IntegrationProcessingRequested():
            extraKVPIndex = integration_dialog.WriteIntegrationInfo( writer, extraKVPIndex )
            groupBatch = groupBatch or integration_dialog.IntegrationGroupBatchRequested()
            
        if groupBatch:
            writer.WriteLine( "BatchName=%s\n" % (jobName ) ) 
        
        writer.Close()
        
        # Create plugin info file.
        pluginInfoFilename = Path.Combine( GetDeadlineTempPath(), "keyshot_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
        if not submitScene:
            writer.WriteLine( "SceneFile=%s" % sceneFile )
        
        writer.WriteLine( "OutputFile=%s" % outputFile )
        writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )
        writer.WriteLine( "RenderWidth=%s" % scriptDialog.GetValue( "RenderWidthBox" ) )
        writer.WriteLine( "RenderHeight=%s" % scriptDialog.GetValue( "RenderHeightBox" ) )
        
        writer.WriteLine( "IncludeRenderLayers=%s" % scriptDialog.GetValue( "RenderLayersBox" ) )
        writer.WriteLine( "IncludeAlpha=%s" % scriptDialog.GetValue( "IncludeAlphaBox" ) )
        writer.WriteLine( "OverrideRenderPasses=%s" % scriptDialog.GetValue( "overrideRenderPassesBox") )
        writer.WriteLine( "QualityType=%s" % scriptDialog.GetValue( "QualityTypeBox" ) )
        
        for passBox, passInfo in passInformationDict.iteritems():
            writer.WriteLine( "%s=%s" % (passInfo[4], scriptDialog.GetValue( passBox ) ) )
        
        for qualityBox, qualityInfo in qualityOptionDict.iteritems():
            writer.WriteLine( "%s=%s" % (qualityInfo[2], scriptDialog.GetValue( qualityBox ) ) )
        
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

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
startup = True
updatingOutputFile = False

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global startup
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Vrimg2Exr Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Vrimg2Exr' ) )
    
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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "V-Ray Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "V-Ray Image File", 1, 0, "The V-Ray Image file(s) to be converted. If you are submitting a sequence of files, you only need to select one vrimg file from the sequence. ", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "V-Ray Image Files (*.vrimg);;All Files (*)", 1, 1, colSpan=2 )
    sceneBox.ValueModified.connect(SceneBoxChanged)

    scriptDialog.AddControlToGrid("OutputLabel","LabelControl","Output File (Optional)", 2, 0, "Optionally override the output file name (do not specify padding). If left blank, the output name will be the same as the input name (with the exr extension).", False)
    scriptDialog.AddSelectionControlToGrid("OutputBox","FileSaverControl","","OpenEXR (*.exr)", 2, 1, colSpan=2)

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames convert.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1, colSpan=2 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Advanced Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Advanced Options", 0, 0, colSpan=3 )

    setChannelBox = scriptDialog.AddSelectionControlToGrid( "SetChannelBox", "CheckBoxControl", False, "Specify Channel", 4, 0, "Enable this option to read the specified channel from the vrimg file and write it as the RGB channel in the output file.", False )
    setChannelBox.ValueModified.connect(SetChannelBoxModified)
    scriptDialog.AddControlToGrid( "ChannelBox", "TextControl", "", 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "LongChanNamesBox", "CheckBoxControl", False, "Long Channel Names", 4, 2, "Enable channel names with more than 31 characters. Produced .exr file will NOT be compatible with OpenEXR 1.x if a long channel name is present." )

    setGammaBox = scriptDialog.AddSelectionControlToGrid( "SetGammaBox", "CheckBoxControl", False, "Set Gamma", 5, 0, "Enable this option to apply the specified gamma correction to the RGB colors before writing to the exr file.", False )
    setGammaBox.ValueModified.connect(SetGammaBoxModified)
    scriptDialog.AddRangeControlToGrid( "GammaBox", "RangeControl", 1.8, 0.2, 5.0, 6, 0.2, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "DataWindowBox", "CheckBoxControl", True, "Crop EXR Data Window", 5, 2, "Tries to find the valid data window from the .vrimg file. This requires that the file can be read in one pass. The non-zero pixels in the alpha channel are used to determine the data window." )

    setBufferSizeBox = scriptDialog.AddSelectionControlToGrid( "SetBufferSizeBox", "CheckBoxControl", False, "Set Buffer Size (MB)", 6, 0, "Enable this option to set the maximum allocated buffer size per channel in megabytes. If the image does not fit into the max buffer size, it is converted in several passes.", False )
    setBufferSizeBox.ValueModified.connect(SetBufferSizeBoxModified)
    scriptDialog.AddRangeControlToGrid( "BufferSizeBox", "RangeControl", 1, 10, 1000000, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "HalfBox", "CheckBoxControl", False, "Store EXR Data as 16-bit (Half)", 6, 2, "Enable this option to store the data in the .exr file as 16-bit floating point numbers instead of 32-bit floating point numbers." )

    setCompressionBox = scriptDialog.AddSelectionControlToGrid( "SetCompressionBox", "CheckBoxControl", False, "Set Compression", 7, 0, "", False )
    setCompressionBox.ValueModified.connect(SetCompressionBoxModified)
    scriptDialog.AddComboControlToGrid( "CompressionBox", "ComboControl", "zip", ("none","piz","pxr24","zip","zips"), 7, 1, "Enable this option to set the compression type. The Zip method is used by default.", False )
    scriptDialog.AddSelectionControlToGrid( "SeparateFilesBox", "CheckBoxControl", False, "Separate Files", 7, 2, "Writes each channel into a separate .exr file." )
    
    scriptDialog.AddControlToGrid( "ThreadsLabel", "LabelControl", "Threads", 8, 0, "The number of computation threads. Specify 0 to use the number of processors available.", False )
    scriptDialog.AddRangeControlToGrid( "ThreadsBox", "RangeControl", 0, 0, 256, 0, 1, 8, 1 )
    scriptDialog.AddSelectionControlToGrid( "MultiPartBox", "CheckBoxControl", False, "Multi Part", 8, 2, "Writes each channel into a separate OpenEXR2 'part'." )
    
    scriptDialog.AddSelectionControlToGrid( "SRGBBox", "CheckBoxControl", False, "Convert RGB Data to the sRGB Color Space", 9, 0, "Enable this option to converts the RGB data from the vrimg file to the sRGB color space (instead of linear RGB space) before writing to the exr file.", colSpan=2 )
    scriptDialog.AddSelectionControlToGrid( "DeleteInputBox", "CheckBoxControl", False, "Delete Input vrimg Files After Conversion", 9, 2, "Enable this option to delete the input vrimg file after the conversion has finished.", False )
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    #Application Box must be listed before version box or else the application changed event will change the version
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","SetChannelBox","ChannelBox","SetGammaBox","GammaBox","HalfBox","SetBufferSizeBox","BufferSizeBox","SRGBBox","SetCompressionBox","CompressionBox","DeleteInputBox","DataWindowBox","MultiPartBox","ThreadsBox","SeparateFilesBox","LongChanNamesBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    if len( args ) > 0:
        scriptDialog.SetValue( "SceneBox", args[0] )
    
    SceneBoxChanged( None )
    SetChannelBoxModified( None )
    SetGammaBoxModified( None )
    SetBufferSizeBoxModified( None )
    SetCompressionBoxModified( None )
    
    startup = False
    
    scriptDialog.ShowDialog( len( args ) > 0 )
    
def SceneBoxChanged( *args ):
    global scriptDialog
    global startup
    global updatingOutputFile
    
    if not updatingOutputFile:
        try:
            filename = scriptDialog.GetValue( "SceneBox" )
            if filename != "":
                initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
                paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
                
                frameString = "0"
                
                #if initFrame >= 0 and paddingSize > 0:
                try:
                    filename = FrameUtils.GetLowerFrameFilename( filename, initFrame, paddingSize )
                    
                    updatingOutputFile = True
                    scriptDialog.SetValue( "SceneBox", filename )
                    updatingOutputFile = False
                    
                    startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
                    endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
                
                    if startFrame != endFrame:
                        frameString = str(startFrame) + "-" + str(endFrame)
                    else:
                        frameString = str(startFrame)
                except:
                    frameString = "0"
                    
                scriptDialog.SetValue( "FramesBox", frameString )
                scriptDialog.SetValue( "NameBox", Path.GetFileNameWithoutExtension( FrameUtils.GetFilenameWithoutPadding( filename ) ) )
        except Exception as e:
            if not startup:
                scriptDialog.ShowMessageBox( e.Message, "Error Parsing Input Images" )

def SetChannelBoxModified( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "ChannelBox", scriptDialog.GetValue( "SetChannelBox" ) )

def SetGammaBoxModified( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "GammaBox", scriptDialog.GetValue( "SetGammaBox" ) )

def SetBufferSizeBoxModified( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "BufferSizeBox", scriptDialog.GetValue( "SetBufferSizeBox" ) )

def SetCompressionBoxModified( *args ):
    global scriptDialog
    scriptDialog.SetEnabled( "CompressionBox", scriptDialog.GetValue( "SetCompressionBox" ) )

def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "VrimgSettings.ini" )
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    
    # Check if V-Ray file exist.
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        result = scriptDialog.ShowMessageBox( "Vrimg file %s does not exist. Are you sure you want to continue" % sceneFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    # If path is local, warn user.
    if (PathUtils.IsPathLocal(sceneFile)):
        result = scriptDialog.ShowMessageBox( "Vrimg file %s is local. Are you sure you want to continue" % sceneFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue( "FramesBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return
    
    paddingSize = FrameUtils.GetPaddingSizeFromFilename( sceneFile )
    padding = ""
    while len(padding) < paddingSize:
        padding = padding + "#"
    
    # Generate the output filename for the submit info file
    outputFilename = scriptDialog.GetValue("OutputBox").strip()
    if(len(outputFilename) > 0):
        if(not Directory.Exists(Path.GetDirectoryName(outputFilename))):
            scriptDialog.ShowMessageBox( "The directory of the output file does not exist:\n" + Path.GetDirectoryName(outputFilename), "Error" )
            return
        elif (PathUtils.IsPathLocal(outputFilename)):
            result = scriptDialog.ShowMessageBox("The output file " + outputFilename + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
            if(result=="No"):
                return
        
        try:
            outputExt = Path.GetExtension(outputFilename)
        except:
            scriptDialog.ShowMessageBox("No extension was found in output file name.","Error")
            return
        
        outputFilename = outputFilename.replace(outputExt, padding + outputExt)
    else:
        outputFilename = FrameUtils.GetFilenameWithoutPadding( sceneFile )
        outputPath = Path.GetDirectoryName( outputFilename )
        outputPrefix = Path.GetFileNameWithoutExtension( outputFilename )
        outputFilename = Path.Combine( outputPath, outputPrefix + padding +".exr" )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "vrimg_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=Vrimg2Exr" )
    writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
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
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
    writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
    writer.WriteLine( "Frames=%s" % frames )
    writer.WriteLine( "ChunkSize=1" )
    
    if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    
    if(len(outputFilename) > 0):
        writer.WriteLine("OutputFilename0=" + outputFilename)
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    
    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "vrimg_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "InputFile=%s" % sceneFile )
    writer.WriteLine( "OutputFile=%s" % scriptDialog.GetValue( "OutputBox" ) )
    writer.WriteLine( "Half=%s" % scriptDialog.GetValue( "HalfBox" ) )
    writer.WriteLine( "sRGB=%s" % scriptDialog.GetValue( "SRGBBox" ) )
    writer.WriteLine( "DataWindow=%s" % scriptDialog.GetValue( "DataWindowBox" ) )
    writer.WriteLine( "SeparateFiles=%s" % scriptDialog.GetValue( "SeparateFilesBox" ) )
    writer.WriteLine( "MultiPart=%s" % scriptDialog.GetValue( "MultiPartBox" ) )
    writer.WriteLine( "SetGamma=%s" % scriptDialog.GetValue( "SetGammaBox" ) )
    writer.WriteLine( "Gamma=%s" % scriptDialog.GetValue( "GammaBox" ) )
    writer.WriteLine( "SetChannel=%s" % scriptDialog.GetValue( "SetChannelBox" ) )
    writer.WriteLine( "Channel=%s" % scriptDialog.GetValue( "ChannelBox" ) )
    writer.WriteLine( "LongChanNames=%s" % scriptDialog.GetValue( "LongChanNamesBox" ) )
    writer.WriteLine( "SetCompression=%s" % scriptDialog.GetValue( "SetCompressionBox" ) )
    writer.WriteLine( "Compression=%s" % scriptDialog.GetValue( "CompressionBox" ) )
    writer.WriteLine( "SetBufferSize=%s" % scriptDialog.GetValue( "SetBufferSizeBox" ) )
    writer.WriteLine( "BufferSize=%s" % scriptDialog.GetValue( "BufferSizeBox" ) )
    writer.WriteLine( "DeleteInputFiles=%s" % scriptDialog.GetValue( "DeleteInputBox" ) )
    writer.WriteLine( "Threads=%s" % scriptDialog.GetValue( "ThreadsBox" ) )
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
        
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
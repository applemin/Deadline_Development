from __future__ import print_function

import os
import re

from Deadline.Scripting import ClientUtils, FrameUtils, PathUtils, RepositoryUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

from System.IO import StreamWriter
from System.Text import Encoding

# For Integration UI
import imp
imp.load_source( 'IntegrationUI', RepositoryUtils.GetRepositoryFilePath( "submission/Integration/Main/IntegrationUI.py", True ) )
import IntegrationUI

# The global scriptDialog is required so that the object is not garbage collected after it's shown.
scriptDialog = None

def __main__( *args ):
    global scriptDialog

    scriptDialog = AltusSubmissionDialog()
    scriptDialog.ShowDialog( False )


class AltusSubmissionDialog( DeadlineScriptDialog ):
    SUPPORTED_VERSIONS = (1.8, 1.9, 2.0, 2.1, 2.3) # Altus doesn't have a legacy 2.2 version we can test

    DRAFT_ENABLED = True
    PROJECT_MANAGEMENT_OPTIONS = ( "Shotgun", "FTrack", "NIM" )

    STICKY_SETTINGS_FILE = os.path.join( ClientUtils.GetUsersSettingsDirectory(), "AltusSettings.ini" )
    STICKY_SETTINGS = (
        "DepartmentBox", "PoolBox", "SecondaryPoolBox", "GroupBox", "PriorityBox", "MachineLimitBox", "IsBlacklistBox",
        "MachineListBox", "LimitGroupBox", "FramesBox", "ChunkSizeBox", "OutputBox", "VersionBox", "ExecutableTypeBox", "ConfigBox",
        "configCheck", "RgbBox", "PositionBox", "AlbedoBox", "AlbedoCheck", "VisibilityBox", "VisibilityCheck", "CausticsBox",
        "CausticsCheck", "NormalsBox", "NormalsCheck", "ExtraBox", "ExtraCheck", "AdditionalBox", "AdditionalCheck", "StereoBox",
        "LayerPreservationBox", "QualityBox", "AOVQualityBox", "ForceContinueIntBox", "FireFlyBox", "TileBox", "TileSizeBox",
        "IgnoreAlphaBox", "SkipFrameRadiusBox", "SinglePassBox", "Force16bitOutputBox", "EXRCompressionBox",
        "HairCheck", "HairBox",
    )

    PASS_TYPES = { "Rgb", "Normals", "Position", "Albedo", "Visibility", "Caustics", "Hair", "Extra", "Additional" }

    # The EXR compressions that Altus accepts. We communicate this choice to Altus via a 0-based index.
    EXR_COMPRESSIONS = ( "No Compression", "RLE", "ZIPS", "ZIP", "PIZ", "PXR24", "B44", "B44A", "DWAA", "DWAB" )

    def __init__(self):
        """
        Creates the submission dialog for Altus
        """
        super( AltusSubmissionDialog, self ).__init__()

        self.integration_dialog = None

        self._create_ui()
        self._apply_sticky_settings()
        self._refresh_ui()

    def _create_ui( self ):
        """
        Performs the creation of the submission dialog
        :return:
        """
        self.SetTitle( "Submit Altus Job To Deadline" )
        self.SetIcon( self.GetIcon( "Altus" ) )

        self.AddTabControl( "Tabs", 0, 0 )

        self._add_job_options_tab()
        self._add_altus_config_options_tab()
        self._add_altus_settings_tab()
        self._add_project_management_tabs()

        self.EndTabControl()

        self._add_submission_buttons()

    def _add_job_options_tab( self ):
        """
        Adds the job options tab to the submission UI. Only to be used by _create_ui()
        :return:
        """
        self.AddTabPage( "Job Options" )

        self.AddGrid()
        self.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

        self.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
        self.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

        self.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
        self.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

        self.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
        self.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

        self.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
        self.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

        self.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0,
                               "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
        self.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

        self.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
        self.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

        self.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0,
                               "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
        self.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

        self.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0,
                               "The number of minutes a Slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
        self.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
        self.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2,
                                        "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job." )

        self.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0,
                               "The number of tasks that can render concurrently on a single Slave. This is useful if the rendering application only uses one thread to render and your Slaves have multiple CPUs.",
                               False )
        self.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
        self.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2,
                                        "If you limit the tasks to a Slave's task limit, then by default, the Slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual Slaves by an administrator." )

        self.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0,
                               "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
        self.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
        self.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2,
                                        "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

        self.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "The whitelisted or blacklisted list of machines.", False )
        self.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

        self.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
        self.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

        self.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0,
                               "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.",
                               False )
        self.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

        self.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
        self.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
        self.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2,
                                        "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid( "Separator3", "SeparatorControl", "Basic Altus Options", 0, 0, colSpan=4 )

        self.AddControlToGrid( "OutputLabel", "LabelControl", "Output File", 1, 0, "The output path for the rendered image.", False )
        self.AddSelectionControlToGrid( "OutputBox", "FileSaverControl", "", "OpenEXR (*.exr);;All Files (*)", 1, 1, colSpan=3 )

        self.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 2, 0, "The list of frames to render.", False )
        self.AddControlToGrid( "FramesBox", "TextControl", "", 2, 1 )

        self.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 2, 2, "This is the number of frames that will be rendered at a time for each job task.", False )
        self.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 2, 3 )

        self.AddControlToGrid( "VersionLabel", "LabelControl", "Altus Version", 3, 0, "Which version of Altus Denoiser will be used.", False )
        versionBox = self.AddComboControlToGrid( "VersionBox", "ComboControl", next(reversed(AltusSubmissionDialog.SUPPORTED_VERSIONS)), AltusSubmissionDialog.SUPPORTED_VERSIONS, 3, 1 )
        versionBox.ValueModified.connect( self._version_changed )

        self.AddControlToGrid( "ExecutableTypeLabel", "LabelControl", "Executable Type", 3, 2, "Which executable type of the Altus Denoiser should be run.", False )
        exeSelect = self.AddComboControlToGrid( "ExecutableTypeBox", "ComboControl", "Auto Select", ("Auto Select", "OpenCl", "GPU", "C++"), 3, 3 )
        exeSelect.ValueModified.connect( self._exe_type_changed )

        self.EndGrid()
        self.EndTabPage()

    def _add_altus_config_options_tab( self ):
        """
        Adds the Altus Config Options tab to the submission UI. Only to be used by _create_ui()
        :return:
        """
        self.AddTabPage( "Altus Config Options", isScrollable=True )

        self.AddGrid()
        self.AddControlToGrid( "Separator4", "SeparatorControl", "Altus Config Options", 0, 0, colSpan=5 )

        self.AddControlToGrid( "ConfigLabel", "LabelControl", "Config File", 1, 0, "The config file containing the options for denoising.", False )
        self.AddSelectionControlToGrid( "ConfigBox", "FileBrowserControl", "", "Config File (*.cfg);;All Files (*)", 1, 1, colSpan=3 )

        config_check = self.AddSelectionControlToGrid( "configCheck", "CheckBoxControl", True, "Use Config File", 1, 4,
                                                      "If enabled a single config file will be used which contains the information for denoising." )
        config_check.ValueModified.connect( self._use_config_changed )

        self.AddSelectionControlToGrid( "StereoBox", "CheckBoxControl", False, "Use Stereo EXR Images", 2, 0,
                                        "When enabled, each file image input in this input file section is expected to be a single stereo exr image." )

        self.AddControlToGrid( "RgbLabel", "LabelControl", "RGB File(s)", 3, 0, "The first frame beauty pass .exr file.", False )
        self.AddSelectionControlToGrid( "RgbBox", "MultiLineMultiFileBrowserControl", "", "OpenEXR (*.exr);;All Files (*)", 3, 1, colSpan=3 )

        self.AddControlToGrid( "PositionLabel", "LabelControl", "Position File(s)", 4, 0, "The first frame world position pass .exr file.", False )
        self.AddSelectionControlToGrid( "PositionBox", "MultiLineMultiFileBrowserControl", "", "OpenEXR (*.exr);;All Files (*)", 4, 1, colSpan=3 )

        self.AddControlToGrid( "AlbedoLabel", "LabelControl", "Albedo File(s)", 5, 0, "The first frame albedo pass .exr file.", False )
        self.AddSelectionControlToGrid( "AlbedoBox", "MultiLineMultiFileBrowserControl", "", "OpenEXR (*.exr);;All Files (*)", 5, 1, colSpan=3 )

        albedo_check = self.AddSelectionControlToGrid( "AlbedoCheck", "CheckBoxControl", True, "Albedo", 5, 4, "Filter using frame albedo passes." )
        albedo_check.ValueModified.connect( self._albedo_changed )

        self.AddControlToGrid( "VisibilityLabel", "LabelControl", "Visibility File(s)", 6, 0, "The first frame direct light visibility pass .exr file.", False )
        self.AddSelectionControlToGrid( "VisibilityBox", "MultiLineMultiFileBrowserControl", "", "OpenEXR (*.exr);;All Files (*)", 6, 1, colSpan=3 )

        visibility_check = self.AddSelectionControlToGrid( "VisibilityCheck", "CheckBoxControl", True, "Visibility", 6, 4, "Filter using frame direct light visibility passes." )
        visibility_check.ValueModified.connect( self._visibility_changed )

        self.AddControlToGrid( "CausticsLabel", "LabelControl", "Caustics File(s)", 7, 0, "The first frame caustic pass .exr file.", False )
        self.AddSelectionControlToGrid( "CausticsBox", "MultiLineMultiFileBrowserControl", "", "OpenEXR (*.exr);;All Files (*)", 7, 1, colSpan=3 )

        caustic_check = self.AddSelectionControlToGrid( "CausticsCheck", "CheckBoxControl", True, "Caustic", 7, 4, "Filter using frame caustic passes." )
        caustic_check.ValueModified.connect( self._caustic_changed )

        self.AddControlToGrid( "NormalsLabel", "LabelControl", "Normals File(s)", 8, 0, "The first frame normal pass .exr file.", False )
        self.AddSelectionControlToGrid( "NormalsBox", "MultiLineMultiFileBrowserControl", "", "OpenEXR (*.exr);;All Files (*)", 8, 1, colSpan=3 )

        normals_check = self.AddSelectionControlToGrid( "NormalsCheck", "CheckBoxControl", True, "Normals", 8, 4, "Filter using frame normal passes." )
        normals_check.ValueModified.connect( self._normals_changed )

        self.AddControlToGrid( "HairLabel", "LabelControl", "Hair File(s)", 9, 0, "The file path(s) of the hair EXR image(s).", False )
        self.AddSelectionControlToGrid( "HairBox", "MultiLineMultiFileBrowserControl", "", "OpenEXR (*.exr);;All Files (*)", 9, 1, colSpan=3 )

        hair_files_check = self.AddSelectionControlToGrid( "HairCheck", "CheckBoxControl", False, "Hair", 9, 4, "Filter using hair EXR images" )
        hair_files_check.ValueModified.connect( self._hair_changed )

        self.AddControlToGrid( "ExtraLabel", "LabelControl", "Extra File(s)", 10, 0, "The file path of an extra AOV EXR image.", False )
        self.AddSelectionControlToGrid( "ExtraBox", "MultiLineMultiFileBrowserControl", "", "OpenEXR (*.exr);;All Files (*)", 10, 1, colSpan=3 )

        extra_files_check = self.AddSelectionControlToGrid( "ExtraCheck", "CheckBoxControl", False, "Extra Files", 10, 4, "Use an extra input for feature detection." )
        extra_files_check.ValueModified.connect( self._extra_files_changed )

        self.AddControlToGrid( "AdditionalLabel", "LabelControl", "Additional File(s)", 11, 0, "The file path(s) of additional AOV EXR image(s).", False )
        self.AddSelectionControlToGrid( "AdditionalBox", "MultiLineMultiFileBrowserControl", "", "OpenEXR (*.exr);;All Files (*)", 11, 1, colSpan=3 )

        additional_files_check = self.AddSelectionControlToGrid( "AdditionalCheck", "CheckBoxControl", False, "Additional Files", 11, 4, "Use an additional input for feature detection." )
        additional_files_check.ValueModified.connect( self._additional_files_changed )

        self.EndGrid()
        self.EndTabPage()

    def _add_altus_settings_tab( self ):
        """
        Adds the Altus Settings tab to the submission UI. Only to be used by _create_ui()
        :return:
        """
        self.AddTabPage( "Altus Settings" )
        self.AddGrid()
        self.AddControlToGrid( "Separator5", "SeparatorControl", "Altus Settings", 0, 0, colSpan=4 )

        self.AddControlToGrid( "RendererLabel", "LabelControl", "Renderer", 1, 0, "Which renderer was used to create the source images.", False )
        self.AddComboControlToGrid( "RendererBox", "ComboControl", "Other", ("3Delight", "Arnold", "Corona", "Maxwell", "Octane", "RedShift", "VRay", "Other"), 1, 1 )

        self.AddControlToGrid( "LayerPreservationLabel", "LabelControl", "Layer Preservation", 1, 2, "Whether or not to preserve original layers in output image.", False )
        self.AddComboControlToGrid( "LayerPreservationBox", "ComboControl", "preserve layers", ("none", "preserve layers"), 1, 3 )

        self.AddControlToGrid( "QualityLabel", "LabelControl", "Output Quality", 2, 0, "What quality should the main output be rendered at.", False )
        self.AddComboControlToGrid( "QualityBox", "ComboControl", "production", ("production", "preview"), 2, 1 )

        self.AddControlToGrid( "AOVQualityLabel", "LabelControl", "Output AOV Quality", 2, 2, "What quality should AOV's be rendered at.", False )
        self.AddComboControlToGrid( "AOVQualityBox", "ComboControl", "production", ("none", "prefiltered", "preview", "production"), 2, 3 )

        self.AddControlToGrid( "FrameRadiusLabel", "LabelControl", "Frame Radius", 3, 0, "The neighboring frames that will be used to average motion blur in an animation.", False )
        self.AddRangeControlToGrid( "FrameRadiusBox", "RangeControl", 0, 1, 1000000, 0, 1, 3, 1 )

        self.AddControlToGrid( "FilterRadiusLabel", "LabelControl", "Filter Radius", 3, 2, "Filter radius. Default value is 10.", False )
        self.AddRangeControlToGrid( "FilterRadiusBox", "RangeControl", 0, 10, 1000000, 0, 1, 3, 3 )

        self.AddControlToGrid( "Kc1Label", "LabelControl", "First Sensitivity", 4, 0,
                               "Filter parameter that controls the sensitivity of the first candidate filter to color differences. A higher value leads to more aggressive filtering (default 0.45).", False )
        self.AddRangeControlToGrid( "Kc1Box", "RangeControl", 0.45, 0.000, 1, 3, 0.01, 4, 1 )

        self.AddControlToGrid( "Kc2Label", "LabelControl", "Second Sensitivity", 4, 2,
                               "Filter parameter that controls the sensitivity of the second candidate filter to color differences. A higher value leads to more agressive filtering (default 0.45).", False )
        self.AddRangeControlToGrid( "Kc2Box", "RangeControl", 0.45, 0.000, 1, 3, 0.01, 4, 3 )

        self.AddControlToGrid( "Kc4Label", "LabelControl", "Final Sensitivity", 5, 0,
                               "Filter parameter that controls the sensitivity of the second pass filter to color differences. A higher value leads to more agressive filtering (default 0.45).", False )
        self.AddRangeControlToGrid( "Kc4Box", "RangeControl", 0.45, 0.000, 1, 3, 0.01, 5, 1 )

        self.AddControlToGrid( "KfLabel", "LabelControl", "Feature Sensitivity", 5, 2,
                               "Filter parameter that controls the sensitivity of all candidates, and the second pass filter, to feature differences. Lowering the kf value may help fine detail preservation and decrease smoothing in the final image.", False )
        self.AddRangeControlToGrid( "KfBox", "RangeControl", 0.6, 0.000, 1, 3, 0.01, 5, 3 )

        self.AddControlToGrid( "ForceContinueLabel", "LabelControl", "Force Continue Level", 6, 0,
                               "Choose the level Altus will attempt to continue after warnings and errors. In Altus 1.8, there is no granular control, it's just a flag equivalent to level 3", False )
        self.AddComboControlToGrid( "ForceContinueIntBox", "ComboControl", "0 - No recovery", ("0 - No recovery", "1 - File IO Errors", "2 - Licensing Errors", "3 - File IO and Licensing Errors"), 6, 1 )

        self.AddControlToGrid( "EXRCompressionLabel", "LabelControl", "EXR Compression", 6, 2, "", False )
        self.AddComboControlToGrid( "EXRCompressionBox", "ComboControl", "No Compression", AltusSubmissionDialog.EXR_COMPRESSIONS, 6, 3, "Sets compression for output EXR images." )

        self.AddSelectionControlToGrid( "FireFlyBox", "CheckBoxControl", False, "Firefly", 7, 1,
                                        "<html><head/><body><p>Enables the firefly suppressor. This will detect and reduce the spread of high energy pixels. By default it’s turned off. Minor performance hit to enable.</p></body></html>" )
        self.AddSelectionControlToGrid( "SkipFrameRadiusBox", "CheckBoxControl", False, "Skip Frame Radius", 7, 2, "For animations, skips frames within the frame radius of the first and end frames." )

        self.AddSelectionControlToGrid( "IgnoreAlphaBox", "CheckBoxControl", False, "Ignore Alpha", 8, 1, "Disables denoising of the alpha channel." )
        self.AddSelectionControlToGrid( "SinglePassBox", "CheckBoxControl", False, "Single Pass", 8, 2, "Use single-pass denoising on images exported from Altus integrated products." )

        self.AddSelectionControlToGrid( "Force16bitOutputBox", "CheckBoxControl", False, "Force 16-bit EXR Output", 9, 1, "Force the output EXR image to be 16 bit to reduce file-size." )

        # Tiling Options
        self.AddControlToGrid( "TilingSeparator", "SeparatorControl", "Tiling Options", 10, 0, colSpan=3 )
        tileCheck = self.AddSelectionControlToGrid( "TileBox", "CheckBoxControl", False, "Use Tiling", 11, 1,
                                                    "<html><head/><body><p>Altus can internally divide, denoise, and combine tiles in order to denoise large images that wouldn’t otherwise fit in memory. Generally this feature is more useful when using GPU’s to denoise since GPU’s typically have a small amount of VRAM. This causes large images to be impossible to denoise on GPU unless using tiling.</p></body></html>" )
        tileCheck.ValueModified.connect( self._tiling_changed )

        self.AddControlToGrid( "TileSizeLabel", "LabelControl", "Tile Size", 11, 2,
                               "<html><head/><body><p>Controls the max size of the internal tile. The tile-size given is an upper bound, the actual tile size will always be less than the tile-size in each dimension. Altus finds the subdivision for each axis independently such that the length of the tile in that axis is smaller than the tile-size maximum. If the tile-size is larger than the full image then it is clamped to the size of the image. By default the tile-size is set to 1024.</p></body></html>",
                               False )
        self.AddRangeControlToGrid( "TileSizeBox", "RangeControl", 1024, 2, 65536, 0, 2, 11, 3 )
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid( "GPUSeparator", "SeparatorControl", "GPU Options", 0, 0, colSpan=4 )

        self.AddControlToGrid( "GPUsPerTaskLabel", "LabelControl", "GPUs Per Task", 1, 0,
                               "The number of GPUs to use per task. If set to 0, the default number of GPUs will be used, unless 'Select GPU Devices' Id's have been defined.", False )
        GPUsPerTaskBox = self.AddRangeControlToGrid( "GPUsPerTaskBox", "RangeControl", 0, 0, 1, 0, 1, 1, 1 )  # Single gpu only (Altus 1.8 currently only supports 1 gpu per thread)
        GPUsPerTaskBox.ValueModified.connect( self._gpus_per_task_changed )

        self.AddControlToGrid( "GPUsSelectDevicesLabel", "LabelControl", "Select GPU Devices", 1, 2, "A comma separated list of the GPU devices to use specified by device Id. 'GPUs Per Task' will be ignored.", False )
        GPUsSelectDevicesBox = self.AddControlToGrid( "GPUsSelectDevicesBox", "TextControl", "", 1, 3 )
        GPUsSelectDevicesBox.ValueModified.connect( self._gpus_select_devices_changed )
        self.EndGrid()

        self.EndTabPage()

    def _add_project_management_tabs( self ):
        """
        Adds the project management tabs to the submission UI. Only to be used by _create_ui()
        :return:
        """
        self.integration_dialog = IntegrationUI.IntegrationDialog()
        self.integration_dialog.AddIntegrationTabs( self, "AltusMonitor", AltusSubmissionDialog.DRAFT_ENABLED, AltusSubmissionDialog.PROJECT_MANAGEMENT_OPTIONS, failOnNoTabs=False )

    def _add_submission_buttons( self ):
        """
        Adds the Submit and Close buttons at the bottom of the submission UI. Only to be used by _create_ui()
        :return:
        """
        self.AddGrid()
        self.AddHorizontalSpacerToGrid( "HSpacer1", 23, 0 )

        submitButton = self.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 23, 3, expand=False )
        submitButton.ValueModified.connect( self._submit_button_pressed )

        closeButton = self.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 23, 4, expand=False )
        # Make sure all the project management connections are closed properly
        closeButton.ValueModified.connect( self.integration_dialog.CloseProjectManagementConnections )
        closeButton.ValueModified.connect( self.closeEvent )
        self.EndGrid()

    def _apply_sticky_settings( self ):
        """
        Loads and enables sticky settings for the submission UI elements.
        :return:
        """
        self.LoadSettings( AltusSubmissionDialog.STICKY_SETTINGS_FILE, AltusSubmissionDialog.STICKY_SETTINGS )
        self.EnabledStickySaving( AltusSubmissionDialog.STICKY_SETTINGS, AltusSubmissionDialog.STICKY_SETTINGS_FILE )

    def _refresh_ui( self ):
        """
        Updates the enabled state of the UI elements after loading sticky settings
        :return:
        """
        self._use_config_changed()
        self._gpus_per_task_changed()
        self._gpus_select_devices_changed()
        self._exe_type_changed()
        self._version_changed()

    def _use_config_changed( self, *args ):
        """
        Callback for when enabling/disabling the configuration file
        :param args:
        :return:
        """
        config_enabled = self.GetValue( "configCheck" )

        self.SetEnabled( "ConfigBox", config_enabled )
        self.SetEnabled( "ConfigLabel", config_enabled )

        self.SetEnabled( "RendererBox", not config_enabled )
        self.SetEnabled( "RendererLabel", not config_enabled )

        self.SetEnabled( "LayerPreservationBox", not config_enabled )
        self.SetEnabled( "LayerPreservationLabel", not config_enabled )

        self.SetEnabled( "QualityBox", not config_enabled )
        self.SetEnabled( "QualityLabel", not config_enabled )

        self.SetEnabled( "AOVQualityBox", not config_enabled )
        self.SetEnabled( "AOVQualityLabel", not config_enabled )

        self.SetEnabled( "FrameRadiusBox", not config_enabled )
        self.SetEnabled( "FrameRadiusLabel", not config_enabled )

        self.SetEnabled( "FilterRadiusBox", not config_enabled )
        self.SetEnabled( "FilterRadiusLabel", not config_enabled )

        self.SetEnabled( "Kc1Box", not config_enabled )
        self.SetEnabled( "Kc1Label", not config_enabled )

        self.SetEnabled( "Kc2Box", not config_enabled )
        self.SetEnabled( "Kc2Label", not config_enabled )

        self.SetEnabled( "Kc4Box", not config_enabled )
        self.SetEnabled( "Kc4Label", not config_enabled )

        self.SetEnabled( "KfBox", not config_enabled )
        self.SetEnabled( "KfLabel", not config_enabled )

        self.SetEnabled( "StereoBox", not config_enabled )
        self.SetEnabled( "ForceContinueIntBox", not config_enabled )
        self.SetEnabled( "ForceContinueLabel", not config_enabled )

        self.SetEnabled( "TileBox", not config_enabled )
        self.SetEnabled( "TileSizeBox", not config_enabled )

        self.SetEnabled( "FireFlyBox", not config_enabled )

        self.SetEnabled( "SkipFrameRadiusBox", not config_enabled )
        self.SetEnabled( "IgnoreAlphaBox", not config_enabled )

        self.SetEnabled( "RgbBox", not config_enabled )
        self.SetEnabled( "RgbLabel", not config_enabled )

        self.SetEnabled( "PositionBox", not config_enabled )
        self.SetEnabled( "PositionLabel", not config_enabled )

        self.SetEnabled( "NormalsCheck", not config_enabled )
        self.SetEnabled( "AlbedoCheck", not config_enabled )
        self.SetEnabled( "VisibilityCheck", not config_enabled )
        self.SetEnabled( "CausticsCheck", not config_enabled )
        self.SetEnabled( "ExtraCheck", not config_enabled )
        self.SetEnabled( "AdditionalCheck", not config_enabled )

        self._normals_changed()
        self._albedo_changed()
        self._visibility_changed()
        self._caustic_changed()
        self._extra_files_changed()
        self._additional_files_changed()
        self._version_changed()

    def _version_changed( self, *args ):
        """
        Callback for when changing the Altus version
        :param args:
        :return:
        """
        version = float( self.GetValue( "VersionBox" ) )
        config_enabled = self.GetValue( "configCheck" )

        if version >= 1.9:
            self.SetValue( "ExecutableTypeBox", "Auto Select" )

        self.SetEnabled( "ExecutableTypeLabel", version == 1.8 )
        self.SetEnabled( "ExecutableTypeBox", version == 1.8 )

        self.SetEnabled( "SkipFrameRadiusBox", version >= 1.9 and not config_enabled )
        self.SetEnabled( "IgnoreAlphaBox", version >= 1.9 and not config_enabled )

        self.SetEnabled( "SinglePassBox", version >= 2.1 and not config_enabled )

        self.SetEnabled( "Force16bitOutputBox", version >= 2.3 and not config_enabled )
        self.SetEnabled( "EXRCompressionLabel", version >= 2.3 and not config_enabled )
        self.SetEnabled( "EXRCompressionBox", version >= 2.3 and not config_enabled )

        # These UI options have dependencies that are also affected by the version of Altus
        self._hair_changed()

    def _gpus_per_task_changed( self, *args ):
        """
        Callback for when changing the gpus per task
        :param args:
        :return:
        """
        gpus_per_task_enabled = ( self.GetValue( "GPUsPerTaskBox" ) == 0 )

        self.SetEnabled( "GPUsSelectDevicesLabel", gpus_per_task_enabled )
        self.SetEnabled( "GPUsSelectDevicesBox", gpus_per_task_enabled )

    def _gpus_select_devices_changed( self, *args ):
        """
        Callback for when changing the selected gpus
        :param args:
        :return:
        """
        gpu_select_device_enabled = self.GetValue( "GPUsSelectDevicesBox" ) == ""

        self.SetEnabled( "GPUsPerTaskLabel", gpu_select_device_enabled )
        self.SetEnabled( "GPUsPerTaskBox", gpu_select_device_enabled )

    def _exe_type_changed( self, *args ):
        """
        Callback for when the changing executable type. Used before Altus 2.X
        :param args:
        :return:
        """
        exe_type = self.GetValue( "ExecutableTypeBox" )
        gpu_enabled = True if exe_type in [ "OpenCl", "GPU", "Auto Select" ] else False

        self.SetEnabled( "GPUsPerTaskLabel", gpu_enabled )
        self.SetEnabled( "GPUsPerTaskBox", gpu_enabled )
        self.SetEnabled( "GPUsSelectDevicesLabel", gpu_enabled )
        self.SetEnabled( "GPUsSelectDevicesBox", gpu_enabled )

    def _tiling_changed( self, *args ):
        """
        Callback for when enabling/disabling the "Use Tiling" checkbox
        :param args:
        :return:
        """
        tile_enabled = self.GetValue( "TileBox" )
        config_enabled = self.GetValue( "configCheck" )

        self.SetEnabled( "TileSizeLabel", tile_enabled and not config_enabled )
        self.SetEnabled( "TileSizeBox", tile_enabled and not config_enabled )

    def _normals_changed( self, *args ):
        """
        Callback for when enabling/disabling the "normals" checkbox
        :param args:
        :return:
        """
        norm_enabled = self.GetValue( "NormalsCheck" )
        config_enabled = self.GetValue( "configCheck" )

        self.SetEnabled( "NormalsBox", norm_enabled and not config_enabled )
        self.SetEnabled( "NormalsLabel", norm_enabled and not config_enabled )

    def _albedo_changed( self, *args ):
        """
        Callback for when enabling/disabling the "albedo" checkbox
        :param args:
        :return:
        """
        albedo_enabled = self.GetValue( "AlbedoCheck" )
        config_enabled = self.GetValue( "configCheck" )

        self.SetEnabled( "AlbedoBox", albedo_enabled and not config_enabled )
        self.SetEnabled( "AlbedoLabel", albedo_enabled and not config_enabled )

    def _visibility_changed( self, *args ):
        """
        Callback for when enabling/disabling the "visibility" checkbox
        :param args:
        :return:
        """
        visibility_enabled = self.GetValue( "VisibilityCheck" )
        config_enabled = self.GetValue( "configCheck" )

        self.SetEnabled( "VisibilityBox", visibility_enabled and not config_enabled )
        self.SetEnabled( "VisibilityLabel", visibility_enabled and not config_enabled )

    def _caustic_changed( self, *args ):
        """
        Callback for when enabling/disabling the "caustic" checkbox
        :param args:
        :return:
        """
        caustic_enabled = self.GetValue( "CausticsCheck" )
        config_enabled = self.GetValue( "configCheck" )

        self.SetEnabled( "CausticsBox", caustic_enabled and not config_enabled )
        self.SetEnabled( "CausticsLabel", caustic_enabled and not config_enabled )

    def _extra_files_changed( self, *args ):
        """
        Callback for when enabling/disabling the "extra files" checkbox
        :param args:
        :return:
        """
        extra_files_enabled = self.GetValue( "ExtraCheck" )
        config_enabled = self.GetValue( "configCheck" )

        self.SetEnabled( "ExtraBox", extra_files_enabled and not config_enabled )
        self.SetEnabled( "ExtraLabel", extra_files_enabled and not config_enabled )

    def _additional_files_changed( self, *args ):
        """
        Callback for when enabling/disabling the "additional files" checkbox
        :param args:
        :return:
        """
        additional_files_enabled = self.GetValue( "AdditionalCheck" )
        config_enabled = self.GetValue( "configCheck" )

        self.SetEnabled( "AdditionalBox", additional_files_enabled and not config_enabled )
        self.SetEnabled( "AdditionalLabel", additional_files_enabled and not config_enabled )

    def _hair_changed( self, *args ):
        """
        Callback for when enabling/disabling the "Hair" checkbox
        :param args:
        :return:
        """
        config_enabled = self.GetValue( "configCheck" )
        version = float( self.GetValue( "VersionBox" ) )

        self.SetEnabled( "HairCheck", version >= 2.3 and not config_enabled )
        hair_enabled = self.GetEnabled( "HairCheck" ) and self.GetValue( "HairCheck" )

        self.SetEnabled( "HairBox", hair_enabled )
        self.SetEnabled( "HairLabel", hair_enabled )

    def _check_output_destination( self, errors, warnings):
        """
        Performs sanity checks on the output destination.
        :param errors: list of encountered errors
        :param warnings: list of encountered warnings
        :return:
        """
        output_folder = self.GetValue( "OutputBox" )
        if not output_folder:
            errors.append("An output path must be selected.")
        else:
            output_dir = os.path.dirname( output_folder )
            if PathUtils.IsPathLocal( output_dir ):
                warnings.append( "Output folder %s is local." % output_dir )

            if not os.path.isdir( output_dir ):
                warnings.append( "Output folder %s does not exist." % output_dir )

    def _pass_enabled( self, pass_type ):
        """
        Determines if the specified pass_type is enabled
        :param pass_type: The pass type to check
        :return: A boolean specifying if the pass_type is enabled
        """
        if pass_type in [ "Rgb", "Position" ]:
            return True
        else:
            return self.GetValue( "%sCheck" % pass_type ) and self.GetEnabled( "%sCheck" % pass_type )
            
    def _check_selected_files( self, pass_type, local_files, errors, warnings ):
        """
        Performs sanity checks on the selected files that will be included in the denoising process
        :param pass_type: The pass type corresponding to the files to check
        :param local_files: Existing list of local files
        :param errors: Existing list of errors
        :param warnings: Existing list of warnings
        :return:
        """
        stereo_enabled = self.GetValue( "StereoBox" )

        if self._pass_enabled( pass_type ):
            files_str = self.GetValue( "%sBox" % pass_type )

            if not files_str:
                errors.append( "No outputs set for the enabled pass: %s." % pass_type )
                return

            split_files = files_str.split( ";" )
            if not stereo_enabled:
                if pass_type != "Extra":
                    if len( split_files ) % 2 != 0:
                        errors.append( "An even number of files must be selected for frame passes if Extra is enabled and not using stereo rendering." )
                else:
                    if len( split_files ) != 2:
                        errors.append( "Two files must be selected for frame passes if Extra is enabled and not using stereo rendering." )

            for split_file in split_files:
                if not os.path.isfile( split_file ):
                    warnings.append( "\nThe selected .exr file %s does not exist." % split_file )
                elif PathUtils.IsPathLocal( split_file ):
                    local_files.append( split_file )
        return

    def _check_config_input( self, errors, warnings ):
        """
        Performs a sanity check on the configuration file input
        :param errors: Existing list of errors
        :param warnings: Existing list of warnings
        :return:
        """
        config_file = self.GetValue( "ConfigBox" )
        if not config_file:
            errors.append( "No config file has been set!" )
        elif not os.path.isfile( config_file ):
            errors.append( "The selected config file %s does not exist." % config_file )
        elif PathUtils.IsPathLocal( config_file ):
            warnings.append( "The selected config file %s is local." % config_file )

    def _check_file_inputs( self, errors, warnings ):
        """
        Performs sanity checks on all specified .exr files
        :param errors: Existing list of errors
        :param warnings: Existing list of warnings
        :return:
        """
        local_files = []

        # Check if input for .exr files are valid.
        for passType in AltusSubmissionDialog.PASS_TYPES:
            self._check_selected_files( passType, local_files, errors, warnings )

        if local_files:
            warning = "The selected .exr files are local:\n%s" % ( "\n".join( local_files ) )
            warnings.append( warning )

    def _submit_button_pressed( self, *args ):
        """
        Callback for the "submit" button. Submits a job to Deadline
        :param args:
        :return:
        """
        warnings = []
        errors = []

        # If using 'select GPU device Ids' then check device Id syntax is valid.
        if self.GetValue( "GPUsPerTaskBox" ) == 0 and self.GetValue( "GPUsSelectDevicesBox" ) != "":
            # regex = re.compile( "^(\d{1,2}(,\d{1,2})*)?$" ) # Multiple gpu check
            regex = re.compile( "^([0-9]|1[0-6])$" ) # Single gpu check (Altus 1.8 currently only supports 1 gpu)

            valid_syntax = regex.match( self.GetValue( "GPUsSelectDevicesBox" ) )
            if not valid_syntax:
                # errors.append( "'Select GPU Devices' syntax is invalid!\nTrailing 'commas' if present, should be removed.\nValid Examples: 0 or 2 or 0,1,2 or 0,3,4 etc" ) # Multiple gpu check
                errors.append( "'Select GPU Device' syntax is invalid!\nSingle GPU ID 0-16 supported only.\nValid Examples: 0 or 1 or 2 etc" ) # Single gpu check (Altus 1.8 currently only supports 1 gpu per thread)

            # Check if concurrent threads > 1.
            if self.GetValue( "ConcurrentTasksBox" ) > 1:
                errors.append( "If using 'Select GPU Devices', then 'Concurrent Tasks' must be set to 1" )

        stereo_enabled = self.GetValue( "StereoBox" )
        version = float( self.GetValue( "VersionBox" ) )
        full_output_path = self.GetValue( "OutputBox" )
        use_config = self.GetValue( "configCheck" )

        # Check if a valid frame range has been specified.
        frames = self.GetValue( "FramesBox" )
        if not FrameUtils.FrameRangeValid( frames ):
            errors.append( "Frame range: %s is not valid" % frames )

        if not full_output_path:
            errors.append( "The output image name is required." )

        self._check_output_destination( errors, warnings )

        if use_config:
            self._check_config_input( errors, warnings )
        else:
            self._check_file_inputs( errors, warnings )

        # Check if Integration options are valid.
        if not self.integration_dialog.CheckIntegrationSanity( full_output_path ):
            return

        if errors:
            self.ShowMessageBox( "The following errors were encountered:\n\n%s\n\nPlease resolve these issues and submit again.\n" % ( "\n".join( errors ) ), "Errors" )
            return

        if warnings:
            result = self.ShowMessageBox( "Warnings:\n\n%s\n\nDo you still want to continue?" % ( "\n".join( warnings ) ), "Warnings", ( "Yes","No" ) )
            if result == "No":
                return

        # Create job info file.
        job_info_file = os.path.join( ClientUtils.GetDeadlineTempPath(), "altus_job_info.job" )
        writer = StreamWriter( job_info_file, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Altus" )
        writer.WriteLine( "Name=%s" % self.GetValue( "NameBox" ) )
        writer.WriteLine( "Comment=%s" % self.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % self.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % self.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % self.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % self.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % self.GetValue( "PriorityBox" ) )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % self.GetValue( "TaskTimeoutBox" ) )
        writer.WriteLine( "EnableAutoTimeout=%s" % self.GetValue( "AutoTimeoutBox" ) )
        writer.WriteLine( "ConcurrentTasks=%s" % self.GetValue( "ConcurrentTasksBox" ) )
        writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % self.GetValue( "LimitConcurrentTasksBox" ) )

        writer.WriteLine( "MachineLimit=%s" % self.GetValue( "MachineLimitBox" ) )
        if self.GetValue( "IsBlacklistBox" ):
            writer.WriteLine( "Blacklist=%s" % self.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % self.GetValue( "MachineListBox" ) )

        writer.WriteLine( "LimitGroups=%s" % self.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % self.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % self.GetValue( "OnJobCompleteBox" ) )

        full_output_path = full_output_path.replace( "\\", "/" )
        writer.WriteLine( "OutputFilename0=%s" % full_output_path )

        if self.GetValue( "SubmitSuspendedBox" ):
            writer.WriteLine( "InitialStatus=Suspended" )

        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % self.GetValue( "ChunkSizeBox" ) )

        extra_kvp_index = 0
        group_batch = False
        if self.integration_dialog.IntegrationProcessingRequested():
            extra_kvp_index = self.integration_dialog.WriteIntegrationInfo( writer, extra_kvp_index )
            group_batch = group_batch or self.integration_dialog.IntegrationGroupBatchRequested()

        if group_batch:
            writer.WriteLine( "BatchName=%s" % ( self.GetValue( "NameBox" ) ) )

        writer.Close()

        # Create plugin info file.
        plugin_info_file = os.path.join( ClientUtils.GetDeadlineTempPath(), "altus_plugin_info.job" )
        writer = StreamWriter( plugin_info_file, False, Encoding.Unicode )

        exe_type = self.GetValue( "ExecutableTypeBox" )
        writer.WriteLine( "ExecutableType=%s" % exe_type )

        writer.WriteLine( "Version=%s" % version )
        writer.WriteLine( "OutputFile=%s" % full_output_path )

        if exe_type in [ "OpenCl", "GPU", "Auto Select" ]:
            writer.WriteLine( "GPUsPerTask=%s" % self.GetValue( "GPUsPerTaskBox" ) )
            writer.WriteLine( "GPUsSelectDevices=%s" % self.GetValue( "GPUsSelectDevicesBox" ) )

        # If config file defined, then skip all other settings.
        if use_config:
            writer.WriteLine( "Config=%s" % self.GetValue( "ConfigBox" ) )
        else:
            for passType in AltusSubmissionDialog.PASS_TYPES:
                if self._pass_enabled( passType ):
                    writer.WriteLine( "%sFiles=%s;" % ( passType, self.GetValue( "%sBox" % passType ) ) )

            writer.WriteLine( "Renderer=%s" % self.GetValue( "RendererBox" ) )
            writer.WriteLine( "PreserveLayers=%s" % self.GetValue( "LayerPreservationBox" ) )
            writer.WriteLine( "OutputQuality=%s" % self.GetValue( "QualityBox" ) )
            writer.WriteLine( "AOVQuality=%s" % self.GetValue( "AOVQualityBox" ) )
            writer.WriteLine( "FrameRadius=%s" % self.GetValue( "FrameRadiusBox" ) )
            writer.WriteLine( "FilterRadius=%s" % self.GetValue( "FilterRadiusBox" ) )
            writer.WriteLine( "Kc_1=%s" % self.GetValue( "Kc1Box" ) )
            writer.WriteLine( "Kc_2=%s" % self.GetValue( "Kc2Box" ) )
            writer.WriteLine( "Kc_4=%s" % self.GetValue( "Kc4Box" ) )
            writer.WriteLine( "Kf=%s" % self.GetValue( "KfBox" ) )
            writer.WriteLine( "Stereo=%s" % stereo_enabled )
            if version == 1.8:
                # 1.8 is either False (Level 0) or True (Level 3)
                writer.WriteLine( "ForceContinue=%s" % bool( self.GetValue( "ForceContinueIntBox" )[ 0 ] ) )
            else:
                writer.WriteLine( "ForceContinueInt=%s" % self.GetValue( "ForceContinueIntBox" )[ 0 ] ) # Just need first character

            # Tile options
            writer.WriteLine( "Tile=%s" % self.GetValue( "TileBox" ) )
            writer.WriteLine( "TileSize=%s" % self.GetValue( "TileSizeBox" ) )

            writer.WriteLine( "FireFly=%s" % self.GetValue( "FireFlyBox" ) )

            if version >= 1.9:
                writer.WriteLine( "SkipFrameRadius=%s" % self.GetValue( "SkipFrameRadiusBox" ) )
                writer.WriteLine( "IgnoreAlpha=%s" % self.GetValue( "IgnoreAlphaBox" ) )

            if version >= 2.1:
                writer.WriteLine( "SinglePass=%s" % self.GetValue( "SinglePassBox" ) )

            if version >= 2.3:
                writer.WriteLine( "Force16bitOutput=%s" % self.GetValue( "Force16bitOutputBox" ) )
                writer.WriteLine( "EXRCompression=%s" % self.GetValue( "EXRCompressionBox" ) )

        writer.Close()

        # Setup the command line arguments.
        arguments = [ job_info_file, plugin_info_file ]

        # Now submit the job.
        results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
        self.ShowMessageBox( results, "Submission Results" )

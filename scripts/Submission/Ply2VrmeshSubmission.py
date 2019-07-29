import io
import os

from Deadline.Scripting import ClientUtils, FrameUtils, PathUtils, RepositoryUtils

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

# The dialog needs to be kept in a module variable otherwise it gets garbage-collected and the dialog disappears
scriptDialog = None

def __main__(*args):
    """The entry-point function called by Deadline to launch the monitor submitter"""

    # We need to assign this to a module variable - otherwise the dialog gets garbage collected and it disappears
    # after returning from the function
    global scriptDialog

    scriptDialog = Ply2VrmeshSubmissionDialog()
    scriptDialog.ShowDialog(False)


class Ply2VrmeshSubmissionDialog(DeadlineScriptDialog):
    """Class containing the ply2vrmesh monitor submitter"""

    # List of UI controls whose values will be persisted in sticky settings. The order is respected when restoring
    # the UI control values
    STICKY_SETTINGS = (
        "DepartmentBox",
        "CategoryBox",
        "PoolBox",
        "SecondaryPoolBox",
        "GroupBox",
        "PriorityBox",
        "IsBlacklistBox",
        "MachineListBox",
        "LimitGroupBox",
        "SceneBox"
    )
    # The path where sticky settings are saved
    STICKY_SETTINGS_PATH = os.path.join(ClientUtils.GetUsersSettingsDirectory(), "Ply2VrmeshSettings.ini")

    # Controls that are only shown when ply2vrmesh version is >= 3
    VERSION_3_CONTROLS = (
        "FlipXPosZBox",
        "PreviewHairsLabel",
        "PreviewHairsBox",
        "SegmentsPerVoxelLabel",
        "SegmentsPerVoxelBox",
        "HairWidthMultiplierLabel",
        "HairWidthMultiplierBox",
        "PreviewParticlesLabel",
        "PreviewParticlesBox",
        "ParticlesPerVoxelLabel",
        "ParticlesPerVoxelBox",
        "ParticleWidthMultiplierLabel",
        "ParticleWidthMultiplierBox",
        "MergeVoxelsBox"
    )



    def __init__(self, *args, **kwargs):
        """Instantiates an instance of Ply2VrmeshSubmissionDialog"""
        super(Ply2VrmeshSubmissionDialog, self).__init__(*args, **kwargs)

        # Initialize this state variable that is used to block recursion in an event handler
        self.updating_output_file = False

        self._create_ui()
        self._apply_sticky_settings()
        self._refresh_ui()

    def _refresh_ui(self):
        """Manually trigger the UI event handlers to update any state of dependent UI controls"""
        self._scene_box_changed()
        self._version_box_changed()
        self._smooth_angle_changed()
        self._merge_box_changed()
        self._vrscene_animation_changed()

    def _apply_sticky_settings(self):
        """Configures sticky settings UI controls and restores them"""

        # Restore previous sticky settings
        self.LoadSettings(self.STICKY_SETTINGS_PATH, self.STICKY_SETTINGS)
        # Configure the UI controls that will be saved as sticky settings
        self.EnabledStickySaving(self.STICKY_SETTINGS, self.STICKY_SETTINGS_PATH)

    def _create_ui(self):
        """Creates the UI controls that make up the submission dialog and wires up all event handlers"""
        self.SetTitle("Submit Ply2Vrmesh Job To Deadline")
        self.SetIcon(self.GetIcon('Ply2Vrmesh'))

        self.AddTabControl("Tabs", 0, 0)

        self.AddTabPage("Job Options")
        self.AddGrid()
        self.AddControlToGrid("JobOptionsSeparator", "SeparatorControl", "Job Description", 0, 0, colSpan=2)

        self.AddControlToGrid("NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False)
        self.AddControlToGrid("NameBox", "TextControl", "Untitled", 1, 1)

        self.AddControlToGrid("CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False)
        self.AddControlToGrid("CommentBox", "TextControl", "", 2, 1)

        self.AddControlToGrid("DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False)
        self.AddControlToGrid("DepartmentBox", "TextControl", "", 3, 1)
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid("Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3)

        self.AddControlToGrid("PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False)
        self.AddControlToGrid("PoolBox", "PoolComboControl", "none", 1, 1)

        self.AddControlToGrid("SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False)
        self.AddControlToGrid("SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1)

        self.AddControlToGrid("GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False)
        self.AddControlToGrid("GroupBox", "GroupComboControl", "none", 3, 1)

        self.AddControlToGrid("PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False)
        self.AddRangeControlToGrid("PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1)

        self.AddControlToGrid("TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False)
        self.AddRangeControlToGrid("TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1)
        self.AddSelectionControlToGrid("IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 5, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist.")

        self.AddControlToGrid("MachineListLabel", "LabelControl", "Machine List", 6, 0, "The whitelisted or blacklisted list of machines.", False)
        self.AddControlToGrid("MachineListBox", "MachineListControl", "", 6, 1, colSpan=2)

        self.AddControlToGrid("LimitGroupLabel", "LabelControl", "Limits", 7, 0, "The Limits that your job requires.", False)
        self.AddControlToGrid("LimitGroupBox", "LimitGroupControl", "", 7, 1, colSpan=2)

        self.AddControlToGrid("DependencyLabel", "LabelControl", "Dependencies", 8, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False)
        self.AddControlToGrid("DependencyBox", "DependencyControl", "", 8, 1, colSpan=2)

        self.AddControlToGrid("OnJobCompleteLabel", "LabelControl", "On Job Complete", 9, 0, "If desired, you can automatically archive or delete the job when it completes.", False)
        self.AddControlToGrid("OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 9, 1)
        self.AddSelectionControlToGrid("SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 9, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.")
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid("Separator3", "SeparatorControl", "V-Ray Options", 0, 0, colSpan=4)

        self.AddControlToGrid("SceneLabel", "LabelControl", "Input Files", 1, 0, "The file to be converted. If a sequence of files exist in the same folder, Deadline will automatically collect the range of the files and will set the Frame Range accordingly. ", False)
        input_box = self.AddSelectionControlToGrid("SceneBox", "FileBrowserControl", "", "PLY Files (*.ply);;OBJ Files (*.obj);;BIN Files (*.bin);;GEO Files (*.geo *.hclassic);;BGEO Files (*.bgeo *.bhclassic);;ABC Files (*.abc);;VRSCENE Files (*.vrscene);;All Files (*)", 1, 1, colSpan=3)
        input_box.ValueModified.connect(self._scene_box_changed)

        self.AddControlToGrid("OutputLabel","LabelControl","Output File (Optional)", 2, 0, "Optionally override the output file name. If left blank, the output name will be the same as the input name (with the vrmesh extension).", False)
        self.AddSelectionControlToGrid("OutputBox","FileSaverControl","","Vrmesh Files (*.vrmesh)", 2, 1, colSpan=3)

        self.AddControlToGrid("FrameListLabel","LabelControl","Frame List", 3, 0, "The frames to render.", False)
        self.AddControlToGrid("FrameListBox", "TextControl", "", 3, 1, colSpan=3)

        self.AddControlToGrid("VersionLabel", "LabelControl", "Version", 4, 0, "The version of V-Ray's Ply2Vrmesh to use.", False)
        version_box = self.AddComboControlToGrid("VersionBox", "ComboControl", "3", ("2","3"), 4, 1)
        version_box.ValueModified.connect(self._version_box_changed)
        self.AddSelectionControlToGrid("AppendBox", "CheckBoxControl", False, "Append", 4, 2, "appends the information as a new frame to the .vrmesh file")
        merge_box = self.AddSelectionControlToGrid("MergeBox", "CheckBoxControl", False, "Merge Output Files", 4, 3, "Merge output files into a single file.")
        merge_box.ValueModified.connect(self._merge_box_changed)

        self.EndGrid()
        self.EndTabPage()

        self.AddTabPage("Conversion Options")
        self.AddGrid()
        smooth_angle_label = self.AddSelectionControlToGrid("SmoothAngleLabel", "CheckBoxControl", False, "Smooth Angle", 0, 0, "a floating point number that specifies the angle (in degrees) used to distinguish if the normals should be  smoothed or not. If present it automatically enables the -smoothNormals flag.", False)
        smooth_angle_label.ValueModified.connect(self._smooth_angle_changed)
        self.AddRangeControlToGrid("SmoothAngleBox", "RangeControl", 0, 0, 1000000, 2, 1, 0, 1)
        self.AddSelectionControlToGrid("SmoothNormalsBox", "CheckBoxControl", False, "Smooth Normals", 0, 2, "generates smooth vertex normals. Only valid for .obj and .geo files; always enabled for .bin files")

        self.AddControlToGrid("MapChannelLabel", "LabelControl", "Map Channel", 1, 0, "stores the UVW coordinates to the specified mapping channel (default is 1). Only valid for .obj and .geo files. When exporting a mesh that will be used in Maya, currently this must be set to 0 or the textures on the mesh will not render properly", False)
        self.AddRangeControlToGrid("MapChannelBox", "RangeControl", 1, 0, 1000000, 0, 1, 1, 1)
        self.AddSelectionControlToGrid("DisableColorSetPackingBox", "CheckBoxControl", False, "Disable Color Set Packing", 1, 2, "only valid for .geo and .bgeo files; disables the packing of float1 and float2 attributes in vertex color sets.")

        self.AddControlToGrid("FPSLabel", "LabelControl", "FPS", 2, 0, "a floating-point number that specifies the frames per second at which a .geo or .bin file is exported, so that vertex velocities can be scaled accordingly. The default is 24.0", False)
        self.AddRangeControlToGrid("FPSBox", "RangeControl", 24, 0, 1000000, 2, 1, 2, 1)
        self.AddSelectionControlToGrid("MaterialIDsBox", "CheckBoxControl", False, "Material IDs", 2, 2, "only valid for .geo files; assigns material IDs based on the primitive groups in the file.")

        self.AddControlToGrid("PreviewFacesLabel", "LabelControl", "Preview Faces", 3, 0, "specifies the maximum number of faces in the .vrmesh preview information. Default is 9973 faces.", False)
        self.AddRangeControlToGrid("PreviewFacesBox", "RangeControl", 9973, 0, 1000000, 0, 1, 3, 1)
        self.AddSelectionControlToGrid("FlipNormalsBox", "CheckBoxControl", False, "Flip Normals", 3, 2, "reverses the face/vertex normals. Only valid for .obj, .geo and .bin files")

        self.AddControlToGrid("FacesPerVoxelLabel", "LabelControl", "Faces Per Voxel", 4, 0, "specifies the maximum number of faces per voxel in the resulting .vrmesh file. Default is 10000 faces.", False)
        self.AddRangeControlToGrid("FacesPerVoxelBox", "RangeControl", 10000, 0, 1000000, 0, 1, 4, 1)
        self.AddSelectionControlToGrid("FlipVertexNormalsBox", "CheckBoxControl", False, "Flip Vertex Normals", 4, 2, "reverses the vertex normals. Only valid for .obj, .geo and .bin files")

        self.AddControlToGrid("PreviewHairsLabel", "LabelControl", "Preview Hairs", 5, 0, "specifies the maximum number of hairs in the .vrmesh preview information. Default is 500 hairs.", False)
        self.AddRangeControlToGrid("PreviewHairsBox", "RangeControl", 500, 0, 1000000, 0, 1, 5, 1)
        self.AddSelectionControlToGrid("FlipFaceNormalsBox", "CheckBoxControl", False, "Flip Face Normals", 5, 2, "reverses the face normals. Only valid for .obj, .geo and .bin files")

        self.AddControlToGrid("SegmentsPerVoxelLabel", "LabelControl", "Segments Per Voxel", 6, 0, "specifies maximum segments per voxel in the resulting .vrmesh file. Default is 64000 hairs.", False)
        self.AddRangeControlToGrid("SegmentsPerVoxelBox", "RangeControl", 64000, 0, 1000000, 0, 1, 6, 1)
        self.AddSelectionControlToGrid("FlipYZBox", "CheckBoxControl", False, "Flip YZ", 6, 2, "swap y/z axes. Needed for some programs i.e. Poser, ZBrush. Valid for .ply, .obj, .geo and .bin files.")

        self.AddControlToGrid("HairWidthMultiplierLabel", "LabelControl", "Hair Width Multiplier", 7, 0, "specifies the multiplier to scale hair widths in the resulting .vrmesh file. Default is 1.0.", False)
        self.AddRangeControlToGrid("HairWidthMultiplierBox", "RangeControl", 1, 0, 1000000, 2, 1, 7, 1)
        self.AddSelectionControlToGrid("FlipYPosZBox", "CheckBoxControl", False, "Flip Y Positive Z", 7, 2, "same as -flipYZ but does not reverse the sign of the z coordinate.")

        self.AddControlToGrid("PreviewParticlesLabel", "LabelControl", "Preview Particles", 8, 0, "specifies the maximum number of particles in the .vrmesh preview information. Default is 20000 particles.", False)
        self.AddRangeControlToGrid("PreviewParticlesBox", "RangeControl", 20000, 0, 1000000, 0, 1, 8, 1)
        self.AddSelectionControlToGrid("FlipXPosZBox", "CheckBoxControl", False, "Flip X Positive Z", 8, 2, "same as -flipYPosZ but swaps x/z axes.")

        self.AddControlToGrid("ParticlesPerVoxelLabel", "LabelControl", "Particles Per Voxel", 9, 0, "specifies maximum particles per voxel in the resulting .vrmesh file. Default is 64000 particles.", False)
        self.AddRangeControlToGrid("ParticlesPerVoxelBox", "RangeControl", 64000, 0, 1000000, 0, 1, 9, 1)
        self.AddSelectionControlToGrid("MergeVoxelsBox", "CheckBoxControl", False, "Merge Voxels", 9, 2, "merge objects before voxelization to reduce overlapping voxels")

        self.AddControlToGrid("ParticleWidthMultiplierLabel", "LabelControl", "Particle Width Multiplier", 10, 0, "specifies the multiplier to scale particles in the resulting .vrmesh file. Default is 1.0.", False)
        self.AddRangeControlToGrid("ParticleWidthMultiplierBox", "RangeControl", 1, 0, 1000000, 2, 1, 10, 1)

        self.AddControlToGrid("VelocityAttrNameLabel", "LabelControl", "Velocity Attr Name", 11, 0, "specifies the name of the point attribute which should be used to generate the velocity channel. By default the 'v' attribute is used.", False)
        self.AddControlToGrid("VelocityAttrNameBox", "TextControl", "v", 11, 1, colSpan=2)

        self.AddControlToGrid("Separator4", "SeparatorControl", "VRSCENE Options", 12, 0, colSpan=3)

        self.AddControlToGrid("VrsceneNodeNameLabel", "LabelControl", "Node Name", 13, 0, "Specifies the name of the node in the VRSCENE file to export", False)
        self.AddControlToGrid("VrsceneNodeNameBox", "TextControl", "", 13, 1, colSpan=2)

        self.AddControlToGrid("VrsceneOptionsLabel", "LabelControl", "Options", 14, 0, "Toggleable options for VRSCENE input files.", False)
        self.AddSelectionControlToGrid("VrsceneApplyTransformBox", "CheckBoxControl", False, "Apply Transform", 14, 1, "Specifies whether to apply the VRSCENE node's transformation matrix to the mesh.")
        self.AddSelectionControlToGrid("VrsceneVelocityBox", "CheckBoxControl", False, "Velocity Channel", 14, 2, "Specifies whether to generate a velocity channel.")

        self.AddControlToGrid("VrsceneAnimationLabel", "LabelControl", "Animation", 15, 0, "Specifies the input VRSCENE animation settings.", False)

        vrscene_animation_box = self.AddSelectionControlToGrid("VrsceneAnimationBox", "CheckBoxControl", False, "Animation", 15, 1, "Specifies whether to use animation on the input VRSCENE.")
        vrscene_animation_box.ValueModified.connect(self._vrscene_animation_changed)

        self.AddControlToGrid("VrsceneStartFrameLabel", "LabelControl", "Start Frame", 16, 1, "Specifies the starting frame to load from the VRSCENE animation.", False)
        self.AddRangeControlToGrid("VrsceneStartFrameBox", "RangeControl", 0, 0, 1000000, 0, 1, 16, 2)

        self.AddControlToGrid("VrsceneEndFrameLabel", "LabelControl", "End Frame", 17, 1, "Specifies the ending frame to load from the VRSCENE animation.", False)
        self.AddRangeControlToGrid("VrsceneEndFrameBox", "RangeControl", 0, 0, 1000000, 0, 1, 17, 2)        
        
        self.EndGrid()

        self.EndTabPage()
        self.EndTabControl()

        self.AddGrid()
        self.AddHorizontalSpacerToGrid("HSpacer1", 0, 0)
        submit_button = self.AddControlToGrid("SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False)
        submit_button.ValueModified.connect(self._submit_button_pressed)
        close_button = self.AddControlToGrid("CloseButton", "ButtonControl", "Close", 0, 2, expand=False)
        close_button.ValueModified.connect(self.closeEvent)
        self.EndGrid()

    def _scene_box_changed(self, *args):
        """Event handler fired when the input file UI control's value is changed"""
        if not self.updating_output_file:
            success = False

            try:
                filename = self.GetValue("SceneBox")
                is_vrscene = False

                if filename != "":
                    init_frame = FrameUtils.GetFrameNumberFromFilename(filename)
                    padding_size = FrameUtils.GetPaddingSizeFromFilename(filename)

                    extension = os.path.splitext(filename)[1].lower()
                    is_vrscene = extension == ".vrscene"

                    start_frame = 0
                    end_frame = 0

                    if padding_size > 0:
                        filename = FrameUtils.GetLowerFrameFilename(filename, init_frame, padding_size)

                        self.updating_output_file = True
                        self.SetValue("SceneBox", FrameUtils.ReplaceFrameNumberWithPadding(filename, "#"))
                        self.updating_output_file = False

                        start_frame = FrameUtils.GetLowerFrameRange(filename, init_frame, padding_size)
                        end_frame = FrameUtils.GetUpperFrameRange(filename, init_frame, padding_size)
                        output_filename = FrameUtils.GetFilenameWithoutPadding(filename)
                    else:
                        output_filename = filename

                    self.SetValue("FrameListBox", "%s-%s" % (start_frame, end_frame))

                    self.SetValue("NameBox", os.path.splitext(os.path.basename(output_filename))[0])
                self.SetEnabled( "VrsceneNodeNameBox", is_vrscene )
                self.SetEnabled( "VrsceneNodeNameLabel", is_vrscene )
                self.SetEnabled( "VrsceneApplyTransformBox", is_vrscene )
                self.SetEnabled( "VrsceneVelocityBox", is_vrscene )
                self.SetEnabled( "VrsceneAnimationBox", is_vrscene )
                animation_checked = self.GetValue( "VrsceneAnimationBox" )
                self.SetEnabled( "VrsceneStartFrameBox", is_vrscene and animation_checked )
                self.SetEnabled( "VrsceneEndFrameBox", is_vrscene and animation_checked )

            except Exception as e:
                self.ShowMessageBox(e.Message, "Error Parsing Input Images")
            else:
                success = True

            if not success:
                self.SetValue("SceneBox", "")
                self.SetValue("NameBox", "Untitled")

    def _version_box_changed(self, *args):
        """Event handler fired when the "Version" drop-down control's value is changed"""
        is_version_3 = (self.GetValue("VersionBox") == "3")

        for control in self.VERSION_3_CONTROLS:
            self.SetEnabled(control, is_version_3)

    def _merge_box_changed(self, *args):
        """Event handler fired when the "Merge Output Files" checkbox is toggled"""
        enabled = not self.GetValue("MergeBox")
        self.SetEnabled("FrameListLabel", enabled)
        self.SetEnabled("FrameListBox", enabled)

    def _smooth_angle_changed(self, *args):
        """Event handler fired when the "Smooth Angle" checkbox is toggled"""
        self.SetEnabled("SmoothAngleBox", self.GetValue("SmoothAngleLabel"))


    def _vrscene_animation_changed( self, *args ):
        checked = self.GetValue( "VrsceneAnimationBox" )
        self.SetEnabled( "VrsceneStartFrameBox", checked )
        self.SetEnabled( "VrsceneEndFrameBox", checked )
    
    def _prompt_warning(self, warning):
        """
        Ply2VrmeshSubmissionDialog._prompt_warning(warning) -> result

        Presents a submission warning to the user and gives them the option of aborting the submission or dismissing
        the warning.

        Arguments:
            warning
                A string containing the warning message to be displayed
        Returns
            result
                A boolean value which is True if the user dismissed the warning or False if the user chose to abort
                the submission
        """
        return self.ShowMessageBox(warning, "Warning", ("Yes", "No")) == "Yes"

    def _show_error(self, error):
        """
        Ply2VrmeshSubmissionDialog._show_error(error)

        Presents a submission error in a consistently titled dialog box to the user

        Arguments:
            error
                A string containing the error message to be displayed
        """
        self.ShowMessageBox(error, "Error")

    def _sanity_checks(self):
        """
        Ply2VrmeshSubmissionDialog._sanity_checks() -> success

        Checks the values of the submitter UI controls and determines if any inputs are invalid. Warnings will be
        presented to the user with the choice of dismissing them or aborting the submission. Errors will be shown in a
        message dialog to the user.

        Returns:
            success
                Returns true if no errors were encountered and there were no undismissed warnings.
        """

        # Warn the user if the directory of the input file does not exist
        scene_file = self.scene_file

        # VRSCENE-specific sanity checks
        extension = os.path.splitext( scene_file )[1].lower()
        if extension == ".vrscene":
            if not self.GetValue("VrsceneNodeNameBox"):
                self.ShowMessageBox("No VRSCENE node name specified.", "Error")
                return
            if self.GetValue("VrsceneAnimationBox"):
                if int(self.GetValue("VrsceneStartFrameBox")) > int(self.GetValue("VrsceneEndFrameBox")):
                    self.ShowMessageBox("Start frame is greater than end frame")
                    return

        if not os.path.isdir(os.path.dirname(scene_file)):
            warning = "The directory of the input file %s does not exist. Are you sure you want to continue?" % scene_file
            if not self._prompt_warning(warning):
                return False

        # Warn the user if path is local
        if PathUtils.IsPathLocal(scene_file):
            warning = "Input file %s is local. Are you sure you want to continue?" % scene_file
            if not self._prompt_warning(warning):
                return False

        if self.output_specified:
            output_path = self.output_path
            output_directory = os.path.dirname(output_path)
            # If the output file is specified, ensure that the directory exists
            if not os.path.isdir(output_directory):
                self._show_error("The directory of the output file does not exist:\n" + output_directory)
                return False
            # Warn the user if the output directory is local
            elif PathUtils.IsPathLocal(output_path):
                warning =  "The output file " + output_path + " is local, are you sure you want to continue?"
                if not self._prompt_warning(warning):
                    return False

            output_ext = os.path.splitext(output_path)[1]
            # Ensure the output file has an extension
            if not output_ext:
                self._show_error("No extension was found in output file name.")
                return False
        # Ensure the output file is specified when using "Merge Output Files"
        elif self.GetValue("MergeBox"):
            self._show_error("An output file must be specified to merge files.")
            return False

        return True

    @property
    def scene_file(self):
        """Returns the value of the input scene"""
        return self.GetValue("SceneBox")

    @property
    def output_path(self):
        """
        Returns the value of the output path.

        If the user has specified an output path in the output file textbox, the value is returned. Otherwise, the
        output path is computed by replacing the input file's extension with ".vrmesh"
        """
        output_path = self.GetValue("OutputBox").strip()

        if not output_path:
            # Compute the expected output path automatically generated by ply2vrmesh based on the input path
            scene_file = self.scene_file
            output_path = os.path.splitext(scene_file)[0] + ".vrmesh"

        return output_path

    @property
    def output_specified(self):
        """
        Returns whether the output file field contains a path or is empty
        """
        return bool(self.GetValue("OutputBox").strip())

    def _submit_button_pressed(self, *args):
        """Event handler fired when the submit button is pressed"""
        if not self._sanity_checks():
            return

        # Create job info file.
        job_info_filename = self._write_job_info_file()

        # Create plugin info file.
        plugin_info_filename = self._write_plugin_info_file()

        # Setup the command line arguments.
        arguments = [ job_info_filename, plugin_info_filename ]

        # Now submit the job.
        results = ClientUtils.ExecuteCommandAndGetOutput(arguments)
        self.ShowMessageBox(results, "Submission Results")

    @staticmethod
    def _write_kv_pair_file(path, kv_pairs):
        """
        Ply2VrmeshSubmissionDialog._write_kv_pair_file(path, kv_paris)

        Write's a job/plugin info file for submission

        Arguments:
            path
                The file-system path to write the submission file to
            kv_pairs
                A dictionary of key-value pairs of strings to write to the submission file
        """
        with io.open(path, 'w', encoding='utf-8-sig') as writer:
            for i, entry in enumerate(kv_pairs.items()):
                key, value = entry
                if i > 0:
                    writer.write(unicode(os.linesep))
                writer.write(unicode(key))
                writer.write(u'=')
                writer.write(unicode(value))

    def _write_plugin_info_file(self):
        """
        Write's the plugin info file based on the submission dialog's UI control values
        """
        plugin_info_filename = os.path.join(ClientUtils.GetDeadlineTempPath(), "ply2vrmesh_plugin_info.job")

        version = int(self.GetValue("VersionBox"))

        scene_file = self.scene_file

        kv_pairs = {
            "Version": version,
            "InputFile": scene_file,
            "Append": self.GetValue("AppendBox"),
            "SetSmoothAngle": self.GetValue("SmoothAngleLabel"),
            "SmoothAngle": self.GetValue("SmoothAngleBox"),
            "FlipNormals": self.GetValue("FlipNormalsBox"),
            "FlipVertexNormals": self.GetValue("FlipVertexNormalsBox"),
            "FlipFaceNormals": self.GetValue("FlipFaceNormalsBox"),
            "FlipYZ": self.GetValue("FlipYZBox"),
            "FlipYPosZ": self.GetValue("FlipYPosZBox"),
            "MapChannel": self.GetValue("MapChannelBox"),
            "DisableColorSetPacking": self.GetValue("DisableColorSetPackingBox"),
            "MaterialIDs": self.GetValue("MaterialIDsBox"),
            "FPS": self.GetValue("FPSBox"),
            "PreviewFaces": self.GetValue("PreviewFacesBox"),
            "FacesPerVoxel": self.GetValue("FacesPerVoxelBox"),
            "VelocityAttrName": self.GetValue("VelocityAttrNameBox"),
            "MergeOutputFiles": self.GetValue("MergeBox")
        }

        if self.output_specified:
            kv_pairs["OutputFile"] = self.output_path

        if version >= 3:
            kv_pairs.update({
                "FlipXPosZ": self.GetValue("FlipXPosZBox"),
                "PreviewHairs": self.GetValue("PreviewHairsBox"),
                "SegmentsPerVoxel": self.GetValue("SegmentsPerVoxelBox"),
                "HairWidthMultiplier": self.GetValue("HairWidthMultiplierBox"),
                "PreviewParticles": self.GetValue("PreviewParticlesBox"),
                "ParticlesPerVoxel": self.GetValue("ParticlesPerVoxelBox"),
                "ParticleWidthMultiplier": self.GetValue("ParticleWidthMultiplierBox"),
                "MergeVoxels": self.GetValue("MergeVoxelsBox")
            })
            extension = os.path.splitext(scene_file)[1].lower()
            if extension == ".vrscene":
                kv_pairs.update({
                    "VrsceneNodeName": self.GetValue( "VrsceneNodeNameBox" ),
                    "VrsceneApplyTm": self.GetValue( "VrsceneApplyTransformBox" ),
                    "VrsceneVelocity": self.GetValue("VrsceneVelocityBox"),
                })
                if self.GetValue( "VrsceneAnimationBox" ):
                    vrscene_frames = "%d-%d" % (
                        self.GetValue( "VrsceneStartFrameBox" ),
                        self.GetValue( "VrsceneEndFrameBox" )
                    )
                    kv_pairs["VrsceneFrames"] = vrscene_frames

        self._write_kv_pair_file(plugin_info_filename, kv_pairs)

        return plugin_info_filename

    def _write_job_info_file(self):
        """
        Write's the job info file based on the submission dialog's UI control values
        """
        job_info_filename = os.path.join(ClientUtils.GetDeadlineTempPath(), "ply2vrmesh_job_info.job")

        kv_pairs = {
            "Plugin": "Ply2Vrmesh",
            "Name": self.GetValue("NameBox"),
            "Comment": self.GetValue("CommentBox"),
            "Department": self.GetValue("DepartmentBox"),
            "Pool": self.GetValue("PoolBox"),
            "SecondaryPool": self.GetValue("SecondaryPoolBox"),
            "Group": self.GetValue("GroupBox"),
            "Priority": self.GetValue("PriorityBox"),
            "TaskTimeoutMinutes": self.GetValue("TaskTimeoutBox"),
            "LimitGroups": self.GetValue("LimitGroupBox"),
            "JobDependencies": self.GetValue("DependencyBox"),
            "OnJobComplete": self.GetValue("OnJobCompleteBox"),
            "Frames": self.GetValue("FrameListBox"),
            "ChunkSize": 100000 if self.GetValue("MergeBox") else 1,
        }
        if self.GetValue("IsBlacklistBox"):
            kv_pairs["Blacklist"] = self.GetValue("MachineListBox")
        else:
            kv_pairs["Whitelist"] = self.GetValue("MachineListBox")
        kv_pairs["OutputFilename0"] = self.output_path
        if self.GetValue("SubmitSuspendedBox"):
            kv_pairs["InitialStatus"] = "Suspended"

        self._write_kv_pair_file(job_info_filename, kv_pairs)

        return job_info_filename

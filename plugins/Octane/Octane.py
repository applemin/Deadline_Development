import os
import platform
import subprocess

from itertools import chain

# Pipes is removed in python3, and its functionality is moved to shlex
try:
    from pipes import quote
except ImportError:
    from shlex import quote

from Deadline.Plugins import DeadlinePlugin, PluginType
from Deadline.Scripting import FileUtils, FrameUtils, PathUtils, RepositoryUtils, StringUtils

def GetDeadlinePlugin():
    return OctanePlugin()

def CleanupDeadlinePlugin(deadlinePlugin):
    deadlinePlugin.Cleanup()
    
class OctanePlugin(DeadlinePlugin):
    Framecount=0
    def __init__(self):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument

    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess(self):
        self.PluginType = PluginType.Simple
        self.StdoutHandling = True
        self.PopupHandling = True
        self.UseProcessTree = True
        self.HideDosWindow = False
        self.CreateNewConsole = True

        framePerFileMode = self.GetBooleanPluginInfoEntryWithDefault( "FramePerFileMode", False )
        if framePerFileMode:
            self.SingleFramesOnly = True
        else:
            self.SingleFramesOnly = False
        
    def RenderExecutable(self):
        version = self.GetPluginInfoEntryWithDefault("Version", "4").strip()
        exe_list = self.GetConfigEntry("Octane_RenderExecutable{0}".format(version))
        exe = FileUtils.SearchFileList(exe_list)

        if not exe:
            self.FailRender('Octane render executable was not found in the comma-separated list "{0}".'
                            'The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor.'.format(exeList))
        
        return exe

    @staticmethod
    def quote_cmdline_args(cmdline):
        """
        A helper function used to quote commandline arguments as needed on a case-by-case basis (args with spaces, escape characters, etc.)

        :param cmdline: The list of commandline arguments
        :return: a string composed of the commandline arguments, quoted properly
        """
        if platform.system() == 'Windows':
            return subprocess.list2cmdline(cmdline)
        else:
            return " ".join(quote(arg) for arg in cmdline)

    def RenderArgument(self):
        """
        Builds up the commandline render arguments as a list which then gets transformed into string

        :return: a string of commandline arguments
        """
        scene_file = self.GetPluginInfoEntry("SceneFile")
        scene_file = PathUtils.ToPlatformIndependentPath(RepositoryUtils.CheckPathMapping(scene_file))

        render_args = ['--no-gui']

        frame_per_file_mode = self.GetBooleanPluginInfoEntryWithDefault( "FramePerFileMode", False )
        if frame_per_file_mode:
            # Octane 1 workflow that's still supported in 2 and onward.
            temp_render_args, scene_file = self.get_frame_per_file_render_arguments()
            render_args.extend(temp_render_args)
        else:
            render_args.extend(self.get_script_render_arguments())

        additional_args = self.GetPluginInfoEntryWithDefault( "AdditionalArgs", "" ).strip()
        if additional_args:
            render_args.append(additional_args)

        render_args.extend(self.get_gpu_render_arguments())
        render_args.append(scene_file)

        return self.quote_cmdline_args(render_args)

    def get_script_render_arguments(self):
        """
        Generates the render arguments for the octane lua script workflow. Octane 2 and later.

        :return: a list of commandline arguments
        """
        output_folder = self.GetPluginInfoEntryWithDefault("OutputFolder", "")
        output_folder = PathUtils.ToPlatformIndependentPath(RepositoryUtils.CheckPathMapping(output_folder))

        lua_script = os.path.join(self.GetPluginDirectory(), "DeadlineOctane.lua")
        filename_template = self.GetPluginInfoEntryWithDefault("FilenameTemplate", "")
        file_format = self.GetPluginInfoEntryWithDefault("FileFormat", "png8")

        render_target_ocs = self.GetPluginInfoEntryWithDefault("RenderTargetOCS", "")
        render_target_orbx = self.GetPluginInfoEntryWithDefault("RenderTargetORBX", "")
        render_target = ""
        if render_target_ocs:
            render_target = render_target_ocs
        elif render_target_orbx:
            render_target = render_target_orbx

        render_args = [
            '-q',
            '--script', lua_script,
            '-a', filename_template,
            '-a', output_folder,
            '-a', file_format,
            '-a', str(self.GetStartFrame()),
            '-a', str(self.GetEndFrame()),
            '-a', render_target,
            '--stop-after-script',
        ]

        sample = self.GetIntegerPluginInfoEntryWithDefault("OverrideSampling", 0)
        if sample > 0:
            render_args.extend(['-s', str(sample)])

        if render_target:
            render_args.extend(['-t', render_target])

        return render_args

    def get_frame_per_file_render_arguments(self):
        """
        Generates the render arguments for when FramePerFile mode is set to True.
        This means that each output frame has an associated scene file with the same frame number.
        This is mostly used in Octane 1 before .orbx was a thing.

        :return: a list of commandline arguments, and the scene file
        """
        render_args = ['-e', '-q']

        sceneFile = self.GetPluginInfoEntry("SceneFile")
        sceneFile = PathUtils.ToPlatformIndependentPath(RepositoryUtils.CheckPathMapping(sceneFile))
        outputFile = self.CreateOutputFile()
        
        paddingSize = 0
        if not self.GetBooleanPluginInfoEntryWithDefault("SingleFile", True):
            currPadding = FrameUtils.GetFrameStringFromFilename(sceneFile)
            paddingSize = len(currPadding)

            if paddingSize > 0:
                newPadding = StringUtils.ToZeroPaddedString(self.GetStartFrame(), paddingSize, False)
                sceneFile = FrameUtils.SubstituteFrameNumber(sceneFile, newPadding)
   
        # Build the new output file name.
        if outputFile:
            outputFile = PathUtils.ToPlatformIndependentPath(RepositoryUtils.CheckPathMapping(outputFile))

            # Add padding to output file if necessary.
            if paddingSize > 0:
                outputFile = FrameUtils.SubstituteFrameNumber(outputFile, newPadding)
                outputPath = os.path.dirname(outputFile)
                outputFileName, outputExtension = os.path.splitext(outputFile)
                
                outputFile = os.path.join(outputPath, outputFileName + newPadding + outputExtension)

            render_args.extend(['-o', outputFile])

        sample = self.GetIntegerPluginInfoEntryWithDefault("OverrideSampling", 0)
        if sample > 0:
            render_args.extend(['-s', str(sample)])

        render_target = self.GetPluginInfoEntryWithDefault("RenderTargetOCS", "")
        if render_target:
            render_args.extend(['-t', render_target])

        return render_args, sceneFile

    def get_gpu_render_arguments(self):
        """
        Determines which gpus to use for the render and creates the corresponding commandline arguments.

        ie. Using GPUs 0, 2, and 3 would look like:
        commandline args: -g 0 -g 2 -g 3
        python list: ['-g', '0', '-g', '2', '-g', '3']

        :return: A list containing the gpu commandline arguments
        """
        result_gpus = []
        gpus_per_task = self.GetIntegerPluginInfoEntryWithDefault("GPUsPerTask", 0)
        gpus_select_devices = self.GetPluginInfoEntryWithDefault("GPUsSelectDevices", "")

        use_select_devices = gpus_select_devices and gpus_per_task == 0
        use_gpus_per_task = not use_select_devices and gpus_per_task > 0

        if self.OverrideGpuAffinity():
            # Ensure the gpu entries are all stringify'd to match other workflows
            override_gpus = [str(gpu) for gpu in self.GpuAffinity()]
            if use_select_devices:
                gpus = gpus_select_devices.split(",")
                not_found_gpus = []
                for gpu in gpus:
                    if gpu in override_gpus:
                        result_gpus.append(gpu)
                    else:
                        not_found_gpus.append(gpu)

                if len(not_found_gpus) > 0:
                    self.LogWarning("The slave is overriding its GPU affinity and the following GPUs do not match the slaves affinity so they will not be used: {0}".format(",".join(not_found_gpus)))
                if len(result_gpus) == 0:
                    self.FailRender("The slave does not have affinity for any of the GPUs specified in the job.")
            elif use_gpus_per_task:
                if gpus_per_task > len(override_gpus):
                    self.LogWarning("The slave is overriding its GPU affinity and the slave only has affinity for {0} slaves of the {1} requested.").format(str(len(override_gpus)), str(gpus_per_task))
                    result_gpus = override_gpus
                else:
                    result_gpus = list(override_gpus)[:gpus_per_task]
            else:
                result_gpus = override_gpus

            self.LogInfo("The slave is overriding the GPUs to render using so the following GPUs will be used: {0}".format(",".join(result_gpus)))

        elif use_select_devices:
            self.LogInfo("Specific GPUs specified, so the following GPUs will be used: {0}".format(gpus_select_devices))
            result_gpus = gpus_select_devices.split(",")

        elif use_gpus_per_task:
            for i in range((self.GetThreadNumber() * gpus_per_task), (self.GetThreadNumber() * gpus_per_task) + gpus_per_task):
                result_gpus.append(str(i))
            self.LogInfo("GPUs per task is greater than 0, so the following GPUs will be used: {0}".format(",".join(result_gpus)))

        # input:  ['0', '2', '3']
        # output: ['-g', '0', '-g', '2', '-g', '3']
        return list(chain.from_iterable(('-g', gpu) for gpu in result_gpus))

    def CreateOutputFile(self):
        outputFile = self.GetPluginInfoEntryWithDefault("OutputFolder", "")
        
        if outputFile[-1:] != "\\":
            outputFile += "\\"

        fileFormat = self.GetPluginInfoEntryWithDefault("FileFormat", "png8")

        if fileFormat in ("png8", "png16"):
            fileFormat = "png"
        elif fileFormat == "exrtonemapped":
            fileFormat = "exr"

        filenameTemplate = self.GetPluginInfoEntryWithDefault("FilenameTemplate", "")
        filenameTemplate = filenameTemplate.replace("%e", fileFormat)
        outputFile += filenameTemplate

        return outputFile

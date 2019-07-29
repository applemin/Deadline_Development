from System import *
from System.Diagnostics import *
from System.IO import *
from System.Text import *
from System.Text.RegularExpressions import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return RibPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the RIB plugin.
######################################################################
class RibPlugin (DeadlinePlugin):
    Renderer = ""
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Simple
        
        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        
        # Set the stdout handlers.
        self.AddStdoutHandlerCallback( r"ERROR.*|error.*|RIB error.*|.*Unable to find shader.*|.*Unable to find out device.*" ).HandleCallback += self.HandleError
        self.AddStdoutHandlerCallback( r"R90000[[:space:]]*([0-9]+)%" ).HandleCallback += self.HandleProgress # BMRT or Entropy
        self.AddStdoutHandlerCallback( r".* ([0-9]+\.[0-9]+)%.*" ).HandleCallback += self.HandleProgress # Aqsis
        self.AddStdoutHandlerCallback( r".* ([0-9]+)% .*" ).HandleCallback += self.HandleProgress # Air
        self.AddStdoutHandlerCallback( r"[[:space:]]*([0-9]+)%" ).HandleCallback += self.HandleProgress # 3delight
        self.AddStdoutHandlerCallback( r"\[\d+\.?\d* \d+\.?\d* \d+\.?\d*\]" ).HandleCallback += self.HandlePointCloudOutput # 3delight point cloud
    
    ## Called by Deadline before the render begins.
    def PreRenderTasks( self ):
        self.Renderer = self.GetPluginInfoEntry( "Renderer" )
        self.LogInfo( "Renderer: " + self.Renderer )
    
    ## Called by Deadline to get the render executable.
    def RenderExecutable( self ):
        renderExeList = self.GetConfigEntry( self.Renderer + "_Executable" )
        renderExe = FileUtils.SearchFileList( renderExeList )
        if( renderExe == "" ):
            self.FailRender( self.Renderer + " render executable was not found in the semicolon separated list \"" + renderExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        return renderExe
    
    ## Called by Deadline to get the render arguments.
    def RenderArgument( self ):
        arguments = self.GetPluginInfoEntryWithDefault( "CommandLineOptions", "" )
        if self.Renderer == "ThreeDelight":
            #Usage: renderdl [options] [file1 ... fileN]
            #-v                : output version to console
            #-h                : output this help
            #-q                : don't print the name of files rendered
            #-d                : add a framebuffer display
            #-D                : add a framebuffer and automatically close it
            #-id               : add an i-display interactive framebuffer
            #-nd               : no display, ignores framebuffer displays in RIB
            #-res x y          : Specify image resolution
            #-beep             : beep when finished all RIBs
            #-beeps            : beep after each rendered RIB
            #-frames f1 f2     : only render frames f1 to f2
            #-crop l r t b     : set a crop window in screen space
            #-stats[1-3]       : display end of frame statistics
            #-statsfile file   : output statistics to 'file'
            #-progress         : print rendering progress at each bucket
            #-noinit           : do not read '.renderdl' file
            #-init             : force reading '.renderdl' file (after -catrib)
            #-test             : render a test image
            #-maxmessages n    : print at most 'n' error or warning messages
            #-filtermessages m : filter out messages in comma separated list
            #
            #Multi-processing options (please read documentation for details)
            #-p n              : launch the render using 'n' threads
            #-P n              : launch the render using 'n' processes
            #-hosts h1,h2,...  : specifies a list of hosts to render on.
            #-tiling t         : sets the tiling mode to use (v, h, m or b).
            #				  This is only meaningful when using processes.
            #-ssh              : use 'ssh' instead of 'rsh' to start renders
            #-jobscript script : use 'script' to start renders
            #-jobscriptparam p : passes 'p' as the first parameter of script
            #
            #RI filtering options (refer to documentation for further details)
            #-rif filter       : adds an RI filter to the filter chain
            #-rifargs args     : starts an argument list
            #-rifend           : ends and argument list
            #
            #RIB output options
            #-catrib           : output RIB to stdout
            #-o file           : when used with -catrib, output RIB to file
            #-binary           : encode RIB in binary format
            #-gzip             : compress RIB using gzip format
            #-callprocedurals  : expand all procedurals and archives
            #-noformat         : perform only minimal formatting of RIB
            #-noheader         : disable the structural header
            
            arguments += " -progress -stats3"
            
        elif self.Renderer == "Air":
            #Usage: AIR [options] {RIBcommands...} RIBfiles...
            #-bevel                               -mode rgb,rgba,z
            #-bs bucketwidth bucketheight         -nodisp
            #-crop left right top bottom          -nosurf
            #-d <render to AIR Show>              -nowarn
            #-e errorfile                         -opp <occlusion prepass)
            #-em <subpixel edgemask>              -pri taskpriority
            #-file imagename                      -reflect
            #-flat flatness                       -res imagewidth imageheight
            #-frames minframe maxframe            -samples xsamples ysamples
            #-g gamma                             -shadows
            #-gi                                  -silent
            #-indirect                            -sm shadingratemultiplier
            #-inkw maxinkwidth                    -stats
            #-ipp <indirect prepass>              -step frameincrement
            #-mf motionfactor                     -threads nthreads
            
            arguments += " -Progress -stats"
            
        elif self.Renderer == "Aqsis":
            #Usage: aqsis [options] [RIB file...]
            #-h, -help              Print this help and exit
            #-version               Print version information and exit
            #-pause                 Wait for a keypress on completion
            #-progress              Print progress information
            #-Progress              Print RenderMan-compatible progress information (ignores -progressformat)
            #-progressformat=string printf-style format string for -progress
            #-endofframe=integer    Equivalent to "endofframe" RIB option
            #-nostandard            Do not declare standard RenderMan parameters
            #-v, -verbose=integer   Set log output level
            #					 0 = errors
            #					 1 = warnings (default)
            #					 2 = information
            #					 3 = debug
            #-echoapi               Echo all RI API calls to the log output (experimental)
            #-z, -priority=integer  Control the priority class of aqsis.
            #					 0 = idle
            #					 1 = normal(default)
            #					 2 = high
            #					 3 = RT
            #-type=string           Specify a display device type to use
            #-addtype=string        Specify a display device type to add
            #-mode=string           Specify a display device mode to use
            #-d, -fb                Same as --type="framebuffer" --mode="rgb"
            #-crop x1 x2 y1 y2      Specify a crop window, values are in screen space.
            #-frames f1 f2          Specify a starting/ending frame to render (inclusive).
            #-frameslist=string     Specify a range of frames to render, ',' separated with '-' to indicate ranges.
            #-nc, -nocolor          Disable colored output
            #-beep                  Beep on completion of all ribs
            #-res x y               Specify the resolution of the render.
            #-option=string         A valid RIB Option string, can be specified multiple times.
            #-mpdump                Output MP list to a custom 'dump' file
            #-rc=string             Override the default RIB configuration file
            #-shaders=string        Override the default shader searchpath(s)
            #-archives=string       Override the default archive searchpath(s)
            #-textures=string       Override the default texture searchpath(s)
            #-displays=string       Override the default display searchpath(s)
            #-procedurals=string    Override the default procedural searchpath(s)
            #-plugins=string        Override the default plugin searchpath(s)
              
            arguments += " -Progress -v 2"
            
        elif self.Renderer == "BMRT":
            #Usage: rendrib [options] file1 ... fileN
            #options:
            #		-res x y          Specify image resolution (if not in RIB)
            #		-samples x y      Specify pixel sampling rate (if not in RIB)
            #		-var v min max    Specify pixel sampling variance
            #		-frames f1 f2     Specify frame interval
            #		-radio n          Perform radiosity calculation with n steps
            #		-crop x1 x2 y1 y2 Set the crop window (screen space units)
            #		-safe             Safety of existing files (no overwrite)
            #		-d [interlace]    Display override - show in framebuffer
            #		-pos x y          Specify image position (for framebuffer display)
            #		-v                Verbose mode
            #		-stats            Display rendering statistics
            #		-silent           Display only error messages
            #		-rayserver        Act as a ray server
            #		-beep             Ring the terminal bell when finished
            #		-arch             Print out the platform architecture code
            
            arguments += " -Progress -stats"
            
        elif self.Renderer == "Entropy":
            #Command line options:
            #	-help             Print help
            #	-version          Print version information
            #	-v                Verbose mode
            #	-silent           Display only error messages
            #	-stats            Display rendering statistics
            #	-threads nthreads Run using nthreads worker threads.
            #	-res x y          Specify image resolution (if not in RIB)
            #	-samples x y      Specify pixel sample rate (if not in RIB)
            #	-frames f1 f2     Specify frame interval
            #	-crop x1 x2 y1 y2 Set the crop window (screen space units)
            #	-d                Display override - show in framebuffer
            #	-dialog           Display dialog box on severe errors
            #	-rayserver        Act as a ray server
            #	-of [filename]    Override output filename in RIB file
            #	-cwd dir          Change working directory before rendering
            #	-arch             Print platform architecture code
                  
            arguments += " -Progress -stats"
            
        elif self.Renderer == "Pixie":
            #Command-line options:
            #-f <range>: Render only a subsequence of frames
            #		   -f 43     = Render only 43'rd frame
            #		   -f 5:15   = Render frames 5 thru 15
            #		   -f 5:2:15 = Render frames 5 thru 15 skipping every other one
            #-q        : Quiet mode (errors/warning ignored)
            #-d        : Ignore the display drivers and use framebuffer
            #-t        : Print renderer statistics after every frame
            #-p        : Display the progress
            
            arguments += " -t"
            
        elif self.Renderer == "RenderMan":
            #usage: prman
            #	[-debug]
            #	[-recover 0|1]
            #	[-progress]
            #	[-p]
            #	[-version]
            #	[-catrib outfile|-]
            #	[-ascii]
            #	[-binary]
            #	[-gzip]
            #	[-rif plug-in [-rifargs arg arg... -rifend]]
            #	[more rif blocks]
            #	[file [file...]]
            
            arguments += " -progress"
            
        elif self.Renderer == "RenderDotC":
            # No arguments...
            arguments += ""
            
        elif self.Renderer == "RenderPipe":
            #usage: renderpipe [options] <renderdrive>|PURE <ribfile>
            #  -o outputfile.tif
            #  -x width
            #  -y height
            #  -a pixel_aspect_ration
            #  -b brightness-gain
            #  -g gamma
            #  -q quantization
            #  -s sample_quality
            
            # No arguments will be appended here. It is up to the user to
            # specify the Render Drive setting in the additional command line
            # options when submitting the job.
            arguments += ""
        
        initialRibFilename = self.GetPluginInfoEntry( "RibFile" ).strip()
        initialRibFilename = RepositoryUtils.CheckPathMapping( initialRibFilename ).replace( "\\", "/" )
        if SystemUtils.IsRunningOnWindows() and initialRibFilename.startswith( "/" ) and not initialRibFilename.startswith( "//" ):
            initialRibFilename = "/" + initialRibFilename
        
        currentPadding = FrameUtils.GetFrameStringFromFilename( initialRibFilename )
        paddingLength = len( currentPadding )
        if paddingLength > 0:
            newPadding = StringUtils.ToZeroPaddedString( self.GetStartFrame(), paddingLength, False )
            initialRibFilename = FrameUtils.SubstituteFrameNumber( initialRibFilename, newPadding )
        
        self.LogInfo( "Rendering file: " + initialRibFilename )
        arguments += " \"" + initialRibFilename.replace( "\\", "/" ) + "\""
        
        return arguments
    
    def HandleError( self ):
        errorMessage = self.GetRegexMatch( 0 )
        ignoreError = False
        
        # This is printed out by 3delight at the end of a render, and is not actually an error message.
        if( errorMessage.find( "error reporting" ) != -1 ):
            ignoreError = True
            
        if not ignoreError:
            self.FailRender( errorMessage )
    
    def HandleProgress( self ):
        self.SetStatusMessage( self.GetRegexMatch( 0 ) )
        self.SetProgress( float(self.GetRegexMatch(1)) )
        #self.SuppressThisLine()
    
    def HandlePointCloudOutput( self ):
        self.SuppressThisLine()

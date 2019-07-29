from __future__ import print_function
import os
import re
import subprocess
import sys
import traceback

import ix, gui

def GetDeadlineCommand():
    deadlineBin = ""
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        #if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass
        
    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if deadlineBin == "" and  os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f:
            deadlineBin = f.read().strip()

    deadlineCommand = os.path.join(deadlineBin, "deadlinecommand")
    
    return deadlineCommand

def CallDeadlineCommand( arguments, hideWindow=True ):
    deadlineCommand = GetDeadlineCommand()
    
    startupinfo = None
    creationflags = 0
    if os.name == 'nt':
        if hideWindow:
            # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
            if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            # still show top-level windows, but don't show a console window
            CREATE_NO_WINDOW = 0x08000000   #MSDN process creation flag
            creationflags = CREATE_NO_WINDOW
    
    arguments.insert( 0, deadlineCommand)
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags)
    output, errors = proc.communicate()

    return output

def SubmitToDeadline():
    scriptPath = CallDeadlineCommand ( ["-GetRepositoryFilePath ", "scripts/Submission/ClarisseSubmission.py" ]).strip()
    if not os.path.isfile( scriptPath ):
        ix.application.message_box( "The ClarisseSubmission.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository.", "Error" )
    else:
        # Get the current project path, and check if the project has been saved yet.
        projectPath = ix.application.get_current_project_filename()
        if not projectPath:
            ix.application.message_box( "Please save this project first.", "Save Project" )
        else:
            # Save the project file.
            print( "Saving project " + projectPath )
            ix.application.save_project(projectPath)
            
            export = ix.application.message_box( "Would you like to export a render archive. If you wish to render with CRender a Render archive must be exported.", "Export Render Archive", ix.api.AppDialog.no(), ix.api.AppDialog.STYLE_YES_NO_CANCEL )
            
            if export.is_cancelled():
                return
            elif export.is_yes():
                print( "Getting render archive path" )
                archivePath = os.path.splitext(projectPath)[0] + ".render"
                archivePath = ix.api.GuiWidget_save_file( ix.application, archivePath, "Specify a file to export the render archive to...", "Render Archives (*.render)\t*.render" )
                if not archivePath:
                    print( "Export canceled" )
                    return
                    
                print( "Exporting project to " + archivePath )
                if not ix.application.export_render_archive( archivePath ):
                    ix.application.message_box( "Failed to export render archive to " + archivePath, "Error" )
                    return
                
                projectPath = archivePath
                  
            frameRange = ix.application.get_current_frame_range()
            startFrame = int(frameRange[0])
            endFrame = int(frameRange[1])

            frameList = str(startFrame)
            if startFrame != endFrame:
                frameList = frameList + "-" + str(endFrame)

            # Grab Images and their layers that have enabled 'render_to_disk'
            objects = ix.api.OfObjectArray()
            ix.application.get_factory().get_all_objects( "Image", objects )
            renderableImages = []
            for image in objects:
                if image.get_attribute( "render_to_disk" )[0]:
                    renderableImages.append(image.get_full_name())
                for layer in image.get_module().get_all_layers():
                    if layer.get_object().get_attribute( "render_to_disk" )[0]:
                        renderableImages.append( layer.get_object().get_full_name() )

            main_version = ix.application.get_version().split( '.' )[0].strip()
            CallDeadlineCommand( [ "-ExecuteScript", scriptPath, projectPath, frameList, main_version, repr( renderableImages ) ], False )
            
###############################################################
## For debugging only.
###############################################################
#~ root = CallDeadlineCommand( ["-root",] ).replace("\n","").replace("\r","")
#~ SubmitToDeadline( root )
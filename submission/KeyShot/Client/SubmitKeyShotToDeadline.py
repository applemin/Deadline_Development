# -*- coding: utf-8 -*-
# AUTHOR Thinkbox Software
# VERSION 10
# Submits a render job to Deadline.

import json
import os
import subprocess

import lux


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

def CallDeadlineCommand( commands, showWindow=True ):
    deadlineCommand = GetDeadlineCommand()
    
    startupinfo = None
    if os.name == 'nt' and not showWindow:
       startupinfo = subprocess.STARTUPINFO()
       startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    args = [ deadlineCommand ]   
    args.extend( commands )
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    output, errors = proc.communicate()
    
    output = output.decode("utf_8")
    output = output.replace("\r","").replace("\n","").replace("\\","/")

    return output

script_file = CallDeadlineCommand( [ "-GetRepositoryFilePath", "scripts/Submission/KeyshotSubmission.py" ], False )
userHomeDir = CallDeadlineCommand( [ "-GetCurrentUserHomeDirectory" ], False )

renderOptionsFile = os.path.join( userHomeDir, "temp", "KeyshotRenderOptions.json" )

renderOptions = lux.getRenderOptions( ).getDict( )

with open( renderOptionsFile, 'w') as fileHandle:
    json.dump( renderOptions, fileHandle )

sceneInfo = lux.getSceneInfo()
sceneFile = sceneInfo["file"]
frameCount = lux.getAnimationInfo( )["frames"]

version = lux.getKeyShotVersion( )[0]

args = []
args.append( "-ExecuteScript" )
args.append( script_file )
args.append( sceneFile )
args.append( str( version ) )
args.append( str( frameCount ) )
args.append( renderOptionsFile )

CallDeadlineCommand( args )

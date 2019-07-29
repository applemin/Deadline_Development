from Deadline.Scripting import *
from System import *
from System.IO import *
import os
import sys

def DraftInit():
    draftRepoPath = RepositoryUtils.GetRepositoryPath( "draft", False )

    if not os.path.exists( draftRepoPath ):
        ClientUtils.LogText( "Draft was not found in the Deadline Repository!" )
        sys.exit()

    if SystemUtils.IsRunningOnMac():
        draftRepoPath = Path.Combine( draftRepoPath, "Mac" )
    else:
        if SystemUtils.IsRunningOnLinux():
            draftRepoPath = Path.Combine( draftRepoPath, "Linux" ) 
        else:
            draftRepoPath = Path.Combine( draftRepoPath, "Windows" )
        
        if SystemUtils.Is64Bit():
            draftRepoPath = Path.Combine( draftRepoPath, "64bit" )
        else:
            draftRepoPath = Path.Combine( draftRepoPath, "32bit" )

    draftQuickSubmissionPath = RepositoryUtils.GetRepositoryPath( "events/DraftEventPlugin/DraftQuickSubmission", True )

    if not os.path.exists( draftQuickSubmissionPath ):
        ClientUtils.LogText( "Draft Quick Submission scripts were not found in the Deadline Repository!" )
        sys.exit()

    sys.path.append( draftRepoPath )
    sys.path.append( draftQuickSubmissionPath )
    
    # Set required environment variables
    newPythonPath = draftRepoPath + os.pathsep + os.pathsep.join( sys.path )
    os.environ['PYTHONPATH'] = newPythonPath
    
    # Give locally set MAGICK path priority over the Draft one
    newMagickPath =  draftRepoPath
    if Environment.GetEnvironmentVariable( "MAGICK_CONFIGURE_PATH" ) != None:
        newMagickPath =  Environment.GetEnvironmentVariable( "MAGICK_CONFIGURE_PATH" ) + Path.PathSeparator + newMagickPath
    
    os.environ['MAGICK_CONFIGURE_PATH'] = newMagickPath
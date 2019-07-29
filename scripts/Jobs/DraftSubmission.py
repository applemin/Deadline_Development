import sys

from System.IO import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
startup = True

import imp
imp.load_source( 'DraftSubmissionBase', RepositoryUtils.GetRepositoryFilePath("submission/Draft/Main/DraftSubmissionBase.py", True) )
from DraftSubmissionBase import *

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global startup

    scriptDialog = CreateDraftScriptDialog()
    
    startup = False
    LoadDefaults()
    InputImagesModified()
    AdjustDistributedJobEnabled()
    scriptDialog.ShowDialog( False )
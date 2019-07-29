import os
import sys

from Deadline.Scripting import *
from Deadline.Jobs import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

def __main__( *args ):
    scriptDialog = DeadlineScriptDialog()
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    if len(selectedJobs) > 0:
        for job in selectedJobs:
            user = RepositoryUtils.GetUserInfo( job.JobUserName, True )
            if user:
                email = user.UserEmailAddress
                subject = job.JobName
                url = "mailto:" + email + "?subject=" + subject
                scriptDialog.OpenUrl(url)

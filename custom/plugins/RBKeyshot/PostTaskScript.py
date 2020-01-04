import os
import sys
import clr

from System import *
from System.Diagnostics import *
from Deadline.Scripting import *
from Deadline.Jobs import *
from System.IO import *
from Deadline.Plugins import *


def __main__(*args):

    print " Running RBKeyshot Post Task Script"
    DeadlinePlugin = args[0]
    current_job = DeadlinePlugin.GetJob()
    print "urrent_job.JobName", current_job.JobName
    print "DeadlinePlugin.GetCurrentTaskId()", DeadlinePlugin.GetCurrentTaskId()

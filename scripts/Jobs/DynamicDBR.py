"""
DynamicDBR.py - Custom method to reduce/increase active slave count that works with DBR/reserve job types
Copyright Thinkbox Software 2016
"""
from System.IO import *
from Deadline.Scripting import *
from FranticX import Environment2

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global scriptDialog
    scriptDialog = DeadlineScriptDialog()

    selectedJobs = MonitorUtils.GetSelectedJobs()

    if len(selectedJobs) > 1:
        scriptDialog.ShowMessageBox( "Only one DBR job can be selected at a time.", "Multiple Jobs Selected" )
        return

    job = selectedJobs[0]
    if Job.JobPlugin not in ( "VraySpawner", "VraySwarm", "3dsmax", "3dsCmd", "CoronaDR", "Modo" ):
        scriptDialog.ShowMessageBox( "Only DBR based jobs should use this script.", "Error" )
        return

    if str( job.JobStatus ) not in ( "Suspended", "Failed", "Completed", "Unknown" ):
        scriptDialog.ShowMessageBox( "Only active DBR jobs can be modified.", "Error" )
        return

    if job.JobPlugin in ( "3dsmax", "3dsCmd", "Modo" ):
        vrayDBRJob = bool( job.GetJobPluginInfoKeyValue( "VRayDBRJob" ) )
        vrayRtDBRJob = bool( job.GetJobPluginInfoKeyValue( "VRayRtDBRJob" ) )
        mentalRayDBRJob = bool( job.GetJobPluginInfoKeyValue( "MentalRayDBRJob" ) )
        modoDBRJob = bool( job.GetJobPluginInfoKeyValue( "ModoDBRJob" ) )
        if not ( vrayDBRJob or vrayRtDBRJob or mentalRayDBRJob or modoDBRJob ):
            scriptDialog.ShowMessageBox( "Only DBR off-load based 3dsmax/3dsCmd/Modo jobs should use this script.", "Error" )
            return

    tasks = RepositoryUtils.GetJobTasks( job, True )
    activeTasksCount = 0
    for task in tasks:
        if IsTaskStatusActive( task.TaskStatus ):
            activeTasksCount += 1

    scriptDialog.AllowResizingDialog( False )
    scriptDialog.SetTitle( "Dynamic DBR Control" )

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "MaxServersLabel", "LabelControl", "Active Servers:", 0, 0 , "This is the maximum number of active Deadline Slaves to be reserved to assist in computing this DBR job.", False )
    scriptDialog.AddRangeControlToGrid( "MaxServersBox", "RangeControl", activeTasksCount, 0, 100, 0, 1, 0, 1 )

    applyButton = scriptDialog.AddControlToGrid( "ApplyButton", "ButtonControl", "Apply", 0, 2, expand=False )
    applyButton.ValueModified.connect(ApplyButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 3, expand=False )
    closeButton.ValueModified.connect(CloseButtonPressed)
    scriptDialog.EndGrid()
    
    scriptDialog.ShowDialog( True )

def ApplyButtonPressed( *args ):
    global scriptDialog
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    job = selectedJobs[0]
    maxServers = int( scriptDialog.GetValue( "MaxServersBox" ) )

    tasks = RepositoryUtils.GetJobTasks( job, True ) #recalculate in-case this is executed more than once in the same dialog session
    tasksArray = []
    activeTasksCount = 0
    for task in tasks:
        theSubArray = []
        theSubArray.append( str(task.TaskId) )
        theSubArray.append( str(task.TaskStatus) )

        if IsTaskStatusActive( task.TaskStatus ):
            activeTasksCount += 1
        tasksArray.append( theSubArray )

    tasksCount = len( tasksArray )

    if maxServers != activeTasksCount:

        #remove slaves from DBR session
        if activeTasksCount > maxServers:
            taskIDsToComplete = []

            #remove any completed tasks
            for i, task in reversed(list(enumerate(tasksArray))):
                 if not IsTaskStatusActive( task[1] ):
                    del tasksArray[i]

            #collect taskIds to complete any tasks
            for i, task in reversed( list( enumerate( tasksArray ) ) ):
                if len( tasksArray ) > maxServers:
                    taskIDsToComplete.append( task[0] )
                    del tasksArray[i]

            taskIDsToComplete.sort()

            #complete some/all active tasks if any present
            for task in tasks.Tasks:
                for i in taskIDsToComplete:
                    if i == task.TaskId:
                        RepositoryUtils.CompleteTasks( job, [task,], Environment2.CleanMachineName )
                        # print( "Completing Task: %s" % task.TaskId ) #debug
        
        #add slaves to DBR session
        if activeTasksCount < maxServers:

            #remove any non-completed tasks (active/rendering)
            for i, task in reversed(list(enumerate(tasksArray))):
                if task[1] != "Completed": #skipping other task states such as suspended, failed or unknown
                    del tasksArray[i]

            #calculate the task count that needs reactiving
            tasksToReactive = maxServers - activeTasksCount

            #collect taskIds to requeue any exising tasks if present, subtracting from tasksToReactive counter
            taskIDsToRequeue = []
            for task in tasksArray:
                if tasksToReactive != 0:
                    taskIDsToRequeue.append(task[0])
                    tasksToReactive -= 1

            taskIDsToRequeue.sort()

            #requeue some/all completed tasks if any present
            for task in tasks.Tasks:
                for i in taskIDsToRequeue:
                    if i == task.TaskId:
                        RepositoryUtils.RequeueTasks( job, [task,] )
                        # print( "Requeuing Task: %s" % task.TaskId ) #debug

            #if tasksToReactive counter != 0, then append new frames to existing job
            if tasksToReactive != 0:
                frameList = str(tasksCount-1) + "-" + str((tasksCount-1) + tasksToReactive)
                RepositoryUtils.AppendJobFrameRange( job, frameList )
                # print( "Appending Frames: %s" % frameList ) #debug

        ClientUtils.LogText( "JobId: %s - Active DBR Slaves set to: %s" % (job.JobId, maxServers) )
    
def CloseButtonPressed( *args ):
    global scriptDialog
    scriptDialog.CloseDialog()

def IsTaskStatusActive( task ):
    return str( status ) in ( "Queued", "Rendering" )

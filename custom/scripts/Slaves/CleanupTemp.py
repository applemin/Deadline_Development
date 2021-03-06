from System.IO import *
from Deadline.Scripting import *


def __main__():
    selectedSlaveInfoSettings = MonitorUtils.GetSelectedSlaveInfoSettings()

    # Get the list of selected machine names from the slave info settings.
    machineNames = SlaveUtils.GetMachineNameOrIPAddresses(selectedSlaveInfoSettings)

    temp_folders = [r"C:\Users\mrb\Desktop\Temp",
                   r"C:\Users\mrb\Desktop\TempRender"]
    for machineName in machineNames:
        print "Running on Machine : %s" % machineName
        for path in temp_folders:
            cmd = "Execute cmd /C rmdir /s /q \"" + path + "\""
            print "Removing Dir : %s with CMD Command : %s " % (path, cmd)
            SlaveUtils.SendRemoteCommand(machineName, cmd)
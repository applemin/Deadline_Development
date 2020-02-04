from System.IO import *
from Deadline.Scripting import *


def __main__():
    selectedSlaveInfoSettings = MonitorUtils.GetSelectedSlaveInfoSettings()

    # Get the list of selected machine names from the slave info settings.
    machineNames = SlaveUtils.GetMachineNameOrIPAddresses(selectedSlaveInfoSettings)

    temp_folder = r"C:\Users\mrb\Desktop\delete"
    for machineName in machineNames:
        print "Running on Machine : %s" % machineName
        SlaveUtils.SendRemoteCommand(machineName, "Execute cmd /C rmdir /Q /S \"" + temp_folder + "\"")
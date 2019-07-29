(
	local du = DeadlineUtil --this is the interface exposed by the Lightning Plug-in which provides communication between Deadline and 3ds Max
	if du == undefined do --if the script is not being run on Deadline (for testing purposes),
	(
		struct DeadlineUtilStruct --define a stand-in struct with the same methods as the Lightning plug-in
		(
			fn SetTitle title = ( format "Title: %\n" title ),
			fn SetProgress percent = (true),
			fn FailRender msg = ( throw msg ),
			fn GetSubmitInfoEntry key = ( undefined ),
			fn GetSubmitInfoEntryElementCount key = ( 0 ),
			fn GetSubmitInfoEntryElement index key = ( undefined ),
			fn GetJobInfoEntry key = ( undefined ),
			fn GetAuxFilename index = ( undefined ),
			fn GetOutputFilename index = ( undefined ),
			fn LogMessage msg = ( format "%\n" msg ),
			fn WarnMessage msg = ( format "Warning: %\n" msg ),
			CurrentFrame = ((sliderTime as string) as integer),
			CurrentTask = ( -1 ),
			SceneFileName = ( maxFilePath + maxFileName ),
			SceneFilePath = ( maxFilePath ),
			JobsDataFolder = ( "" ),
			PluginsFolder = ( "" )
		)
		du = DeadlineUtilStruct() --create an instance of the stand-in struct
	)
	
	du.SetTitle "PhoenixFD Simulation Job" --set the job title 
	du.LogMessage "Starting PhoenixFD Simulation Job..." --output a message to the log
	local st = timestamp() --get the current system time
	
	local thePhoenixFD = execute (du.GetJobInfoEntry "PhoenixFDToSimulate")
	local theIndex = du.CurrentFrame
	if theIndex < 1 or theIndex > thePhoenixFD.count do du.FailRender "Index Out Of Range!"
	local theObject = getNodeByName thePhoenixFD[theIndex]
	A_StartSim(theObject)
	A_Wait(theObject)

	du.LogMessage ("PhoenixFD Simulation of ["+theObject.name+"] finished in "+ ((timestamp() - st)/1000.0) as string + " sec.") --output the job duration
	true --return true if the task has finished successfully, return false to fail the task.
)

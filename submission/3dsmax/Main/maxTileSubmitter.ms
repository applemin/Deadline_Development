(
	local du = DeadlineUtil
	if du == undefined then 
	(
		struct DeadlineUtilStruct (
			fn SetTitle title = ( format "Title: %\n" title ),
			fn SetProgress percent = (true),
			fn FailRender msg = ( throw msg ),
			fn GetJobInfoEntry key = ( undefined ),
			fn GetAuxFilename index = ( undefined ),
			fn LogMessage msg = ( format "%\n" msg ),
			JobsDataFolder = "",
			CurrentFrame = ((sliderTime as string) as integer)
		)
		du = DeadlineUtilStruct()
	)
	
	global SMTDSettings 
	global SMTDFunctions
	local fnScript = ""
	
	try
	(
		local result = -2
			
		local submitOutputFile = sysInfo.tempdir + "submitOutput.txt"
		local submitExitCodeFile = sysInfo.tempdir + "submitExitCode.txt"
		
		deleteFile submitOutputFile
		deleteFile submitExitCodeFile
				
		local commandArguments = "-outputfiles \"" + submitOutputFile + "\" \"" + submitExitCodeFile + "\" -getrepositoryfilepath submission/3dsmax/Main/SubmitMaxToDeadline_Functions.ms"
		local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
		ShellLaunch deadlineCommandBG commandArguments
				
		local startTimeStamp = timestamp()
		local ready = false
		while not ready do
		(
			sleep 0.15
			if doesFileExist submitExitCodeFile do
			(
				local theFile = openFile submitExitCodeFile
				try(result = readValue theFile)catch(result = -2)
				try(close theFile)catch()
				ready = true
			)	
			if timestamp() - startTimeStamp > 10000 then 
			(
				result = -3
				ready = true
			)	
		)
		
		if( result == 0 ) then
		(
			local resultFile = OpenFile submitOutputFile
			local resultMsg = ""
			if (resultFile != undefined) do
			(
				resultMsg = readLine resultFile 
				close resultFile
			)
			
			fnScript = resultMsg
		)
		else
		(
			if result == -3 then
				du.LogMessage "Timed out getting Repository Root from Deadline Command. (error code: 3002)"
			else
				du.LogMessage "Failed to get Repository Root from Deadline Command. (error code: 3003)"	
		)
	)
	catch
		du.LogMessage "Error calling Deadline Command to get Repository Root. (error code: 3004)"
		
		
	if doesFileExist fnScript then
	(
			du.LogMessage "Loading [SubmitMaxToDeadline_Functions.ms] File from Deadline Repository..."
			fileIn fnScript quiet:true
	)
	
	du.LogMessage "Loading File [SubmitterSettingsStruct.ms]..."
	fileIn (du.JobsDataFolder + "\\SubmitterSettingsStruct.ms") quiet:true
	SMTDSettings.TilesRendering = false
	SMTDSettings.RegionRendering = true
	du.LogMessage "Begin Spawning Tile Jobs..."
	SMTDFunctions.spawnTileJobs()
)--end script

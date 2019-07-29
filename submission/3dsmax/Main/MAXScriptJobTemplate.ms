try
(
	local du = DeadlineUtil  --this is the interface exposed by the Lightning Plug-in which provides communication between Deadline and 3ds Max
	if du == undefined do  --if the script is not being run on Deadline (for testing purposes),
	(
		struct DeadlineUtilStruct   --define a stand-in struct with the same methods as the Lightning plug-in
		(
			fn SetTitle title = ( format "Title: %\n" title ),
			fn SetProgress percent = (true),
			fn FailRender msg = ( throw msg ),
			--For "Job Info Parameters" (as displayed in Monitor -> job -> job properties > Submission Params)
			--Please consult the Scripting API reference online -> Deadline.Jobs.Job Class Reference
			--http://docs.thinkboxsoftware.com/products/deadline/8.0/2_Scripting%20Reference/class_deadline_1_1_jobs_1_1_job.html#properties
			--All of our job properties can be accessed here and are prefixed with "Job" such as:
			--fn GetSubmitInfoEntry( "JobSubmitMachine" ), --for "MachineName="
			fn GetSubmitInfoEntry key = ( undefined ),
			fn GetSubmitInfoEntryElementCount key = ( 0 ),
			fn GetSubmitInfoEntryElement index key = ( undefined ),
			--For "Plugin Info Parameters" (as displayed in Monitor -> job -> job properties > Submission Params)
			--Please consult the displayed Key=Value pairs in the "Plugin Info Parameters" in Monitor such as:
			--fn GetJobInfoEntry( "MaxVersion" ), --for "MaxVersion=2017"
			fn GetJobInfoEntry key = ( undefined ),
			fn GetAuxFilename index = ( undefined ),
			fn GetOutputFilename index = ( undefined ),
			fn LogMessage msg = ( format "INFO: %\n" msg ),
			fn WarnMessage msg = ( format "WARNING: %\n" msg ),
			CurrentFrame = ((sliderTime as string) as integer),
			CurrentTask = ( -1 ),
			SceneFileName = ( maxFilePath + maxFileName ),
			SceneFilePath = ( maxFilePath ),
			JobsDataFolder = ( "" ),
			PluginsFolder = ( "" )
		)
		du = DeadlineUtilStruct() --create an instance of the stand-in struct
	)--end if
	
	du.SetTitle "MAXScript Job" --set the job title 
	du.LogMessage "Starting MAXScript Job..." --output a message to the log
	local st = timestamp() --get the current system time
	
	
	
	--YOUR SCENE PROCESSING CODE GOES HERE
	
	
	
	du.LogMessage ("Finished MAXScript Job in "+ ((timestamp() - st)/1000.0) as string + " sec.") --output the job duration
	true  --return true if the task has finished successfully, return false to fail the task.
)--end script
catch
(
	if ((maxVersion())[1]/1000 as integer) >= 19 then --Max2017 or later only
	(
		if hasCurrentExceptionStackTrace() then
		(
			local stackTrace = getCurrentExceptionStackTrace()
			stackTrace =  filterString stackTrace "\n"
			for line in stackTrace do
			(
				if DeadlineUtil == undefined then (format "WARNING: %\n" line) else DeadlineUtil.WarnMessage(line)
			)
		)
	)
	throw()
)
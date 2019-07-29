try
(
	local du = DeadlineUtil 		--this is the interface exposed by the Lightning Plug-in which provides communication between Deadline and 3ds Max
	if du == undefined do  			--if the script is not being run on Deadline (for testing purposes),
	(
		struct DeadlineUtilStruct   --define a stand-in struct with the same methods as the Lightning plug-in
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
	
	fn ExportToVRayStd exportPath startFrame endFrame incrBaseFrame: =
	(
		makeDir (getFileNamePath exportPath) all:true
		sysinfo.currentdir = getFileNamePath exportPath
		
		if not (iskindof renderers.activeShade VRayRT) do renderers.activeShade = VRayRT()
		-- Export is a single frame (non-animation)
		if startFrame == endFrame then
			vrayExportRTScene exportPath separateFiles:false
		-- Export is incremental and we are not exporting the first frame
		else if incrBaseFrame != unsupplied and incrBaseFrame != startFrame then
		(
			-- Export frames into incremental file based on incrBaseFrame
			vrayExportRTScene exportPath separateFiles:false startFrame:startFrame endFrame:endFrame incrBaseFrame:incrBaseFrame
		)
		-- Export is non-incremental or we are exporting the first frame
		else
			-- Export all animation frames into single file
			vrayExportRTScene exportPath separateFiles:false startFrame:startFrame endFrame:endFrame
	)	

	local st = timestamp() --get the current system time
	
	du.SetTitle "VRSCENE Export MAXScript Job" --set the job title 
	du.LogMessage ">Starting VRSCENE Export MAXScript Job..." --output a message to the log
	
	local startFrame = 			(du.GetJobInfoEntry "Render_StartFrame") as integer
	local endFrame = 			(du.GetJobInfoEntry "Render_EndFrame") as integer
	local vrsceneName = 		du.GetJobInfoEntry "Render_InputFilename"
	local exportAnimationMode = du.GetJobInfoEntry "Render_ExportAnimationMode"

	-- This is how to export the VRSCENE file(s)
	--    1 - Single VRSCENE file for all frames
	--    2 - Self-contained VRSCENE file per frame
	--    3 - Incremental VRSCENE file per frame
	if exportAnimationMode == "" do
		exportAnimationMode = "1"
	exportAnimationMode = exportAnimationMode as integer

	du.LogMessage ">Exporting VRSCENE File..."
	if exportAnimationMode ==  1 then
	(
		-- Single VRSCENE file
		ExportToVRayStd vrsceneName startFrame endFrame									--Export the vrscene file for the full time range
	)
	else
	(
		local frameVrsceneName = (getFilenamePath vrsceneName) + (getFilenameFile vrsceneName) + "." + (formattedPrint du.CurrentFrame format:"04i") + (getFilenameType vrsceneName)

		if exportAnimationMode == 2 then
			-- VRSCENE file per frame
			ExportToVRayStd frameVrsceneName du.CurrentFrame (du.CurrentFrame + 1)
		else
			-- VRSCENE file per frame incremental
			ExportToVRayStd frameVrsceneName du.CurrentFrame (du.CurrentFrame + 1) incrBaseFrame:startFrame
	)

	du.LogMessage ("+Finished VRSCENE Export MAXScript Job in "+ ((timestamp() - st)/1000.0) as string + " sec.") --output the job duration
	true  --return true if the submission succeeded
)--end script
catch
(
	if ((maxVersion())[1]/1000 as integer) >= 19 then --Max2017 or later only
	(
		if hasCurrentExceptionStackTrace() then
		(
			local errorMessage = getCurrentException()
			DeadlineUtil.WarnMessage("MaxScript Error: " + errorMessage)
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
(
	local du = DeadlineUtil  --this is the interface exposed by the Lightning Plug-in which provides communication between Deadline and 3ds Max
	if du == undefined do  --if the script is not being run on Deadline (for testing purposes),
	(
		struct DeadlineUtilStruct   --define a stand-in struct with the same methods as the Lightning plug-in
		(
			fn SetTitle title = ( format "Title: %\n" title ),
			fn SetProgress percent = (true),
			fn FailRender msg = ( throw msg ),
			fn GetJobInfoEntry key = ( undefined ),
			fn GetAuxFilename index = ( undefined ),
			fn LogMessage msg = ( format "%\n" msg ),
			CurrentFrame = ((sliderTime as string) as integer)
		)
		du = DeadlineUtilStruct() --create an instance of the stand-in struct
	)--end if
	
	du.SetTitle "MAXScript Job" --set the job title 
	du.LogMessage "Starting MAXScript Job..." --output a message to the log
	local st = timestamp() --get the current system time
	local RTT_SceneData_AppData_Index = 0x41dd73d5

	--hack to force the WriteSceneData() to be executed in 3dsMax file, which should resolve the RTT [outputPath == undefined] issue
	macros.run "Render" "BakeDialog" --open the RTT dialog
	gensettings = gTextureBakeDialog.rollouts.rollouts[1] --get the first sub-rollout
	--Call the changed handler of the "Rendered Frame Window" checkbox
	--without changing its current state
	gensettings.cDisplayFB.changed gensettings.cDisplayFB.state 
	destroyDialog gTextureBakeDialog --close the dialog

	--grab the saved output path from the AppData
	outputPath = getAppData rootNode (RTT_SceneData_AppData_Index+4)

	if outputPath == undefined then
		du.FailRender("ERROR - Render To Texture Output Path is undefined.")
	
	if outputPath[ outputPath.count ] != "\\" then
		outputPath += "\\"

	du.LogMessage ("Output Path is: " + outputPath as string)

	i = fileproperties.findProperty #custom "RTT_Default_Path"
	if (i!=0) then	fileproperties.deleteProperty #custom "RTT_Default_Path"
	fileproperties.addProperty #custom "RTT_Default_Path" outputPath
	
	--have to set file type here to tga, but whatever filetype is set in scene when submitting will actually be used
	i = fileproperties.findProperty #custom "RTT_Default_FileType"
	if (i!=0) then	fileproperties.deleteProperty #custom "RTT_Default_FileType"
	fileproperties.addProperty #custom "RTT_Default_FileType" "tga"

	i = fileproperties.findProperty #custom "RTT_RenderTimeType"
	if (i!=0) then	fileproperties.deleteProperty #custom "RTT_RenderTimeType"
	fileproperties.addProperty #custom "RTT_RenderTimeType" (rendTimeType=4)
	
	objsToBake_string = du.GetJobInfoEntry "BakeObjs"

	objsToBake = filterString objsToBake_string ","

	du.LogMessage "Objects To Bake In This Job:"
	for n in 1 to objsToBake.count do du.LogMessage (objsToBake[n] as string)
	du.LogMessage ("Object Count: " + objsToBake.count as string)

	local hasErrors = false
	local oneObjectPerTask = (du.GetJobInfoEntry "BakeObjsOnePerTask") != "false"
	du.LogMessage ("One Object Per Task is " + oneObjectPerTask as string)
	
	if oneObjectPerTask then
	(
		rendPickupFrames = "0"
		local o = objsToBake[du.CurrentFrame]
		du.LogMessage ("Rendering to Texture - Object "+du.CurrentFrame as string+": ''" + o + "'...")
		try 
		(
			local node = getnodebyname o
			RTT_methods.netbakenode node
		) 
		catch 
		(
			exception = getCurrentException()
			errorMsg = "ERROR: " + exception
			du.LogMessage (errorMsg)
			--format "%: %\n" o errorMsg to:errors
			
			if exception == "-- Runtime error: Bitmap creation failure" then
			(
				du.LogMessage ("-- Make sure an output element has been specified in the Render to Texture dialog")
				--format "-- Make sure an output element has been specified in the Render to Texture dialog\n" to:errors
			)
			hasErrors = true
		)        
	)
	else
	(
		rendPickupFrames = du.CurrentFrame as string
		
		du.LogMessage ("Output Path: " + outputPath)
		du.LogMessage ("Current Frame: " + rendPickupFrames)
		
		--local errors = stringStream ""
		local cnt = 0
		for o in objsToBake do 
		(
			cnt += 1
			du.LogMessage ("Rendering to Texture - Object "+cnt as string+ " of " + objsToBake.count as string + ": '" + o + "'")
			try 
			(
				local node = getnodebyname o
				RTT_methods.netbakenode node
			) 
			catch 
			(
				exception = getCurrentException()
				errorMsg = "ERROR: " + exception
				du.LogMessage (errorMsg)
				--format "%: %\n" o errorMsg to:errors
				
				if exception == "-- Runtime error: Bitmap creation failure" then
				(
					du.LogMessage ("-- Make sure an output element has been specified in the Render to Texture dialog")
					--format "-- Make sure an output element has been specified in the Render to Texture dialog\n" to:errors
				)
				
				hasErrors = true
			)        
		)
	)
	
	if hasErrors then
	(
		du.LogMessage("ERROR - There were errors when rendering. Check log for details.")
		du.FailRender("ERROR - There were errors when rendering. Check log for details.")
	)
	
	
	du.LogMessage ("Finished MAXScript RTT Job in "+ ((timestamp() - st)/1000.0) as string + " sec.") --output the job duration
	true  --return true if the task has finished successfully, return false to fail the task.
)--end script

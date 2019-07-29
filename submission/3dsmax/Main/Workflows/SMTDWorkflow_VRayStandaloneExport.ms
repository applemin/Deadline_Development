(
	global SMTDWorkflow_VrayStandaloneExport	
	global SMTD_VRaySAExportRollout
	rollout SMTD_VRaySAExportRollout "Submit To V-Ray Standalone"
	(
		radiobuttons rad_submissionMode labels:#("Export VRSCENE On This Workstation","Export VRSCENE On Deadline") \
			tooltip:"Exporting on the Workstation can block it for a while, but has no 3ds Max statup overhead.\n\nExporting On Deadline offsets the processing time to the network, but requires a Slave running Windows and 3ds Max."
		
		button btn_export_animation_help "Export Animation: " align:#left across:2 height:20 border:false offset:[-5,0] \
			tooltip:"Specifies how to create VRSCENE file(s) for animations"
		dropdownList ddl_export_animation items:#("Single File", "File Per Frame", "File Per Frame (Incremental)") align:#right width:355 \
			tooltip:"How to generate VRSCENE file(s)\n\n'Single File' will create one VRSCENE file for the entire animation sequence.\n\n'File Per Frame' will create one VRSCENE file for each frame in the animation. Each VRSCENE file will be self-contained. This usually produces larger files, but is better suited for parallel rendering since rendering each frame depends on exactly one VRSCENE file.\n\n'File Per Frame (Incremental)' will produce an initial VRSCENE for the first frame which contains all of the initial geometry, materials, and renderer settings. VRSCENE files created for subsequent frames will reference the first frame and only specify differential changes for the frame. This often reduces the size of the VRSCENE files but the rendering of all frames will depend on the first VRSCENE file. When the scene is heavily animated with geometry modifiers this export mode degrades and `Files Per Frame` is preferrable."
		
		group "VRSCENE Export Job Settings:"
		(
			button btn_pools_help "Pool: " align:#left across:4 width:50 height:20  offset:[-5,0] border:false tooltip:"The POOL lets you group Jobs together, typically on per-Project basis. It also controls the Job Priority -- the order in which a Slave is assigned to Pools matters!\n\nOnly Slaves assigned to the selected Pool will be allowed to pick up the job.\n\nIf 'none' is specified as Pool, any Slave can render it if it has no other jobs in assigned Pools to work on."
			dropdownList ddl_poollist "" width:175 align:#right offset:[-10,-2] tooltip:"The POOL lets you group Jobs together, typically on per-Project basis. It also controls the Job Priority -- the order in which a Slave is assigned to Pools matters!\n\nOnly Slaves assigned to the selected Pool will be allowed to pick up the job.\n\nIf 'none' is specified as Pool, any Slave can render it if it has no other jobs in assigned Pools to work on."
			button btn_pools2_help "Secondary: " align:#left width:65 height:20  offset:[-9,-2] border:false tooltip:"The SECONDARY POOL lets you specify a Pool to use if the primary Pool does not have any available Slaves.\n\nTo DISABLE this feature, ensure you select the EMPTY entry at the top of the list!"
			dropdownList ddl_pool2list "" width:175 align:#right offset:[1,-2] tooltip:"The SECONDARY POOL lets you specify a Pool to use if the primary Pool does not have any available Slaves.\n\nTo DISABLE this feature, ensure you select the EMPTY entry at the top of the list!"

			button btn_group_help "Group: " align:#left across:2 width:50 height:20 offset:[-5,-3] border:false tooltip:"The GROUP lets you limit the job to only specific machines, typically based on hardware or installed software characteristics.\n\nSelect the 'none' Group to turn off Group filtering."
			dropdownlist ddl_group items:#() align:#right width:416 offset:[1,-4] height:20 tooltip:"The GROUP lets you limit the job to only specific machines, typically based on hardware or installed software characteristics.\n\nSelect the 'none' Group to turn off Group filtering."
			
			button btn_onComplete "On Job Completion: " width:115 height:20 border:false offset:[60,-2] across:2 align:#right
			dropdownlist ddl_onComplete items:#("Nothing", "Archive", "Delete") width:175 offset:[1,-2] align:#right
		)
		fn displayPoolsList ddl &PoolName addNone:false =
		(
			if addNone then 
				ddl.items = (join #("") SMTDSettings.Pools)
			else
				ddl.items = SMTDSettings.Pools
			
			local theIndex = findItem ddl.items PoolName
			if theIndex > 0 then 
				ddl.selection = theIndex 
			else
			(
				theIndex = findItem ddl.items "none"
				if theIndex > 0 do
				(
					ddl.selection = theIndex
					PoolName = "none"
				)
			)
		)
		
		fn displayGroupsList ddl &GroupName =
		(
			ddl.items = SMTDSettings.Groups
			
			local theIndex = findItem ddl.items GroupName
			if theIndex > 0 then 
				ddl.selection = theIndex 
			else
			(
				theIndex = findItem ddl.items "none"
				if theIndex > 0 do
				(
					ddl.selection = theIndex 
					GroupName = "none"
				)
			)
		)	
		
		fn initializeControls =
		(
			local theIndex = findItem #("Nothing","Archive","Delete") ::SMTDWorkflow_VrayStandaloneExport.OnComplete
			if theIndex == 0 do theIndex = 1; ::SMTDWorkflow_VrayStandaloneExport.OnComplete = "Nothing"
			ddl_onComplete.selection = theIndex
			ddl_export_animation.selection = SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode
			rad_submissionMode.state = SMTDWorkflow_VrayStandaloneExport.SubmissionMode
			displayPoolsList ddl_poollist &SMTDWorkflow_VrayStandaloneExport.PoolName		
			displayPoolsList ddl_pool2list &SMTDWorkflow_VrayStandaloneExport.Pool2Name addNone:true
			displayGroupsList ddl_group &SMTDWorkflow_VrayStandaloneExport.GroupName
		)
		
		fn updateControls =
		(
			btn_onComplete.enabled = ddl_onComplete.enabled = btn_pools_help.enabled = ddl_poollist.enabled = btn_pools2_help.enabled = ddl_pool2list.enabled =	btn_group_help.enabled = ddl_group.enabled = rad_submissionMode.state == 2
		)
		
		on ddl_onComplete selected itm do
		(
			setIniSetting SMTDPaths.InIFile "SMTDVRSA" "OnComplete" (::SMTDWorkflow_VrayStandaloneExport.onComplete = ddl_onComplete.selected )
			SMTDWorkflow_VrayStandaloneExport.storeSettings()
		)

		on ddl_poollist selected itm do 
		(
			setIniSetting SMTDPaths.InIFile "SMTDVRSA" "PoolName" (::SMTDWorkflow_VrayStandaloneExport.PoolName = ddl_poollist.selected)
			SMTDWorkflow_VrayStandaloneExport.storeSettings()
		)
		
		on ddl_pool2list selected itm do 
		(
			setIniSetting SMTDPaths.InIFile "SMTDVRSA" "Pool2Name" (::SMTDWorkflow_VrayStandaloneExport.Pool2Name = ddl_pool2list.selected) 
			SMTDWorkflow_VrayStandaloneExport.storeSettings()
		)	

		on ddl_group selected itm do 
		(
			setIniSetting SMTDPaths.InIFile "SMTDVRSA" "GroupName" ( (::SMTDWorkflow_VrayStandaloneExport.GroupName = ddl_group.selected) as string )
			SMTDWorkflow_VrayStandaloneExport.storeSettings()
		)	
		
		on rad_submissionMode changed state do
		(
			setIniSetting SMTDPaths.InIFile "SMTDVRSA" "SubmissionMode" ( (::SMTDWorkflow_VrayStandaloneExport.submissionMode = state) as string )
			SMTDWorkflow_VrayStandaloneExport.storeSettings()
			updateControls()
		)
		
		on ddl_export_animation selected itm do
		(
			SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode = itm
			SMTDWorkflow_VrayStandaloneExport.storeSettings()
		)
		
		fn updateRolloutTitle state =
		(
			local theTitle = "Submit To V-Ray Standalone"
			if not state do
			(			
				case ::SMTDWorkflow_VrayStandaloneExport.submissionMode of
				(
					1: theTitle+= " [Local Export]"
					2: theTitle+= " [On Deadline - P1:"+::SMTDWorkflow_VrayStandaloneExport.PoolName+ " P2:"+ ::SMTDWorkflow_VrayStandaloneExport.Pool2Name +" Grp:"+::SMTDWorkflow_VrayStandaloneExport.GroupName+"]"
				)
			)			
			SMTD_VRaySAExportRollout.title = theTitle
		)
		
		on SMTD_VRaySAExportRollout rolledup state do
		(
			updateRolloutTitle state
		)			

		on SMTD_VRaySAExportRollout open do
		(
			initializeControls()
			updateControls()
		)
		
		on SMTD_VRaySAExportRollout close do
		(
		)
	)

	struct SMTDWorkflow_VrayStandaloneExportStruct
	(
		fn isWorkflowActive = (isKindOf VRay RendererClass),	--Mandatory! Return false to disable the workflow so it does not load in SMTD UI
		WorkflowName = "vraystandaloneexport",
		WorkflowTitle = "Submit V-RAY STANDALONE Render Job To Deadline",	--Optional. The description of the workflow displayed in the drop-down list, the file name will be used if this is not defined.
		Description = "Export the scene to VRSCENE to render using V-Ray Standalone on Deadline Slaves running on any supported OS.", --Optional. The detailed description used for tooltips, will default to "" if not defined.
		PoolName = "none",
		Pool2Name = "",
		GroupName = "none",
		SubmissionMode = 1,
		OnComplete = "Nothing",
		ExportAnimationMode = 1,
		
		fn defineUILayout =			--Optional. If not defined, the default legacy layout with all rollouts will be used
		(
			#(
				#(#("VRay Job","Job Settings"),#(#(SMTD_VRaySAExportRollout,true),#(SMTD_JobOptions,true), #(SMTD_JobFailureDetection,false))), 
				#(#("Assets","Assets - Asset Collection And Synchronization"),#(#(SMTD_AssetList,true))),
				#(#("Render","Rendering Options"),#(#(SMTD_ScenePreProcessing,true), #(SMTD_MaxStartup,false))), 
				#(#("Options","Submission Options"),#(#(SMTD_UserOptions,true), #(SMTD_SubmissionTimeouts,false))), 
				#(#("Limits","Black List Management and License Limits"),#(#(SMTD_BlackListSlaves,true)))
			)		
		),
		fn updateUILayout = --Optional. This function could be used to apply changes to the visilibity of existing controls
		(
			local inactiveControls = #("btn_chunk", "spn_chunkSize","chk_restartMax", "chk_forceWorkstationMode", "chk_useSilentMode", "ddl_MaxVersionToForce", "spn_cpuThreads", "chk_EnforceSequentialRendering", "btn_MaxVersionToForce")
			for c in SMTD_JobOptions.controls do 
			(
				c.enabled = findItem inactiveControls c.name == 0
				if not c.enabled do c.tooltip = "No available in this Workflow!"
			)
		),
		fn storeSettings =	--Optional. Implements saving of the workflow's own properties with the scene or on disk
		(
			SMTDFunctions.storeWorkflowSettingsWithScene &SMTDWorkflow_VrayStandaloneExport
		),
		fn restoreSettings = --Optional. Implements restoring of the workflow settings from disk, scene, or both
		(
			local val = execute (getIniSetting SMTDPaths.InIFile "SMTDVRSA"  "SubmissionMode")
			if val == OK do val = 1
			SubmissionMode = val

			local val = (getIniSetting SMTDPaths.InIFile "SMTDVRSA"  "PoolName")
			PoolName = val
			
			local val = (getIniSetting SMTDPaths.InIFile "SMTDVRSA"  "Pool2Name")
			if val == "" do val = "none"
			Pool2Name = val

			local val = (getIniSetting SMTDPaths.InIFile "SMTDVRSA"  "GroupName")
			if val == "" do val = "none"
			GroupName = val
			
			SMTD_MainRollout.Ui_report (">V-Ray Standalone Export Workflow: Restoring Settings From Scene...")
			SMTDFunctions.restoreWorkflowSettingsFromScene &SMTDWorkflow_VrayStandaloneExport
		),		
		fn CanSubmit = 		--Optional. This function is called to enable/disable the SUBMIT button. 
							--It must return an array containing a Boolean and a string with a description: #(false, "Reason"), 
							--where false means disable the button, and the string explains why it was disabled.
							--When the result is true, the string will be ignored and the .description property will be used as button tooltip.
							--Assumed to be #(true,"") if the function is not defined.
		(
			local canSubmitJob = true																			--We start by assuming that a submission is possible, then we will lower the flag if something is not right
			local txt = "SUBMIT a V-RAY STANDALONE Job to Deadline..."						
			if not isKindOf renderers.current VRay do																	--If no objects were enabled for submission,
			(
				txt = "V-RAY is NOT the Current Renderer!\n\nPlease assign V-Ray for 3ds Max as the current renderer to submit to V-Ray Standalone."												--Define the explanation string
				canSubmitJob = false																			--and lower the flag
			)
			#(canSubmitJob, txt)																				--return the boolean and the description as an array	
		),
		
		fn ExportToVRayStd exportPath startFrame endFrame =
		(
			makeDir (getFileNamePath exportPath) all:true
			sysinfo.currentdir = getFileNamePath exportPath
			
			if not (iskindof renderers.activeShade VRayRT) do renderers.activeShade = VRayRT()
			if startFrame == endFrame then
				vrayExportRTScene exportPath separateFiles:false
			else
				vrayExportRTScene exportPath separateFiles:false startFrame:startFrame endFrame:endFrame
		),
	
		fn ReplaceSequenceNumber theFilename theFrame expand:false =
		(
			local theNewFilename = theFilename
			local theBaseName = getFileNameFile theFilename
			local digitCount = 0
			local done = false
			local padMask = "#"

			if expand then
				padMask = "####"

			for i = theBaseName.count to 1 by -1 while not done do 
			(
				local asciiCode = bit.charAsInt theBaseName[i]
				if asciiCode >= 48 and asciiCode <= 57 then digitCount += 1 else done = true
			)
			if digitCount > 0 then 
			(
				theNewFilename = getFileNamePath theFilename + (substring theBaseName 1 (theBaseName.count-digitCount)) + padMask + getFileNameType theFilename
			)
			else
			(
				if findString theBaseName "#" == undefined then
				(
					theNewFilename = getFileNamePath theFilename + theBaseName + "." + padMask + getFileNameType theFilename
				)
				else
				(
					if expand then
					(
						theNewFilename = substituteString theFilename "#" "####"
					)
					else
					(
						theNewFilename = theFilename
					)
				)
			)
			theNewFilename
		),

		fn submitVrsceneJobToDeadline vrsceneName outputFilename startFrame endFrame dependency:"" =
		(
			local precacheFileCount = 0
			local jobInfoFilename = SMTDPaths.submitSubFolder + "\\SMTVRSA_job_info.ini"
			local pluginInfoFilename = SMTDPaths.submitSubFolder + "\\SMTVRSA_plugin_info.ini"

			local jobInfoFile = createFile jobInfoFilename encoding:#utf8 writeBOM:false
			format "Plugin=Vray\n" to:jobInfoFile
			format "Name=% [VRAY SA]\n" SMTDSettings.JobName to:jobInfoFile

			local defaultToken = ("Submitted from 3ds Max "+ SMTDFunctions.getMaxVersion() +" "+ (substituteString ((classof renderers.current) as string) "_" "-")   +" using V-Ray Standalone Workflow")
			local formattedComment = SMTDFunctions.FormatComment SMTDSettings.Comment defaultTokenValue:defaultToken
			format "Comment=%\n" formattedComment to:jobInfoFile
			
			format "Department=%\n" SMTDSettings.Department to:jobInfoFile
			format "Pool=%\n" SMTDSettings.PoolName to:jobInfoFile
			format "SecondaryPool=%\n" SMTDSettings.Pool2Name to:jobInfoFile
			format "Group=%\n" SMTDSettings.Group to:jobInfoFile
			format "Priority=%\n" SMTDSettings.Priority to:jobInfoFile

			if dependency.count > 0 then
			(
				-- Export will happen on Deadline
				format "BatchName=%\n" SMTDSettings.JobName to:jobInfoFile
				format "JobDependency0=%\n" dependency to:jobInfoFile
				if SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode == 2 do
					format "IsFrameDependent=True\n" to:jobInfoFile
			)
			else
			(
				-- Export was done locally
				if SMTDSettings.submitAsSuspended do
					format "InitialStatus=Suspended\n" to:jobInfoFile

				-- Pre-cache .vrscene file(s)

				-- Single File and Files Per Frame (Incremental) both create a master .vrscene file
				if SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode != 2 then
				(
					format "AWSAssetFile%=%\n" precacheFileCount vrsceneName to:jobInfoFile
					precacheFileCount += 1
				)

				-- Files Per Frame and Files Per Frame (Incremental) create frame padded .vrscene files
				if SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode != 1 then
				(
					local childVrscenePattern = (getFilenamePath vrsceneName) + (getFilenameFile vrsceneName) + ".####" + (getFilenameType vrsceneName)
					format "AWSAssetFile%=%\n" precacheFileCount childVrscenePattern to:jobInfoFile
					precacheFileCount += 1
				)
			)

			format "MaxTasksPerSlave=%\n" SMTDSettings.MaxTasksPerSlave to:jobInfoFile
			format "LimitTasksToNumberOfCpus=%\n" SMTDSettings.LimitTasksToNumberOfCpus to:jobInfoFile

			if SMTDSettings.TaskTimeoutEnabled then
				format "TaskTimeoutSeconds=%\n"	SMTDSettings.TaskTimeout 		to:jobInfoFile
			else
				format "TaskTimeoutSeconds=0\n" to:jobInfoFile
			format "EnableAutoTimeout=%\n"			SMTDSettings.AutoTaskTimeout				to:jobInfoFile			
			
			local limitGroups = ""	--initialize Limits to empty string
			local limitGroupsToUseArray = for i in SMTDSettings.LimitGroupsToUse collect i

			--if the renderer is mental ray and Max is a version below 8, or if the workstation mode is forced, add the limit group for the current plugin
			if SMTDSettings.LimitGroupAutoWorkstation == true do
			(
				if SMTDSettings.forceWorkstationMode OR SMTDSettings.SubmitAsMXSJob do  
					append limitGroupsToUseArray (pluginToUse + (SMTDFunctions.getMaxVersion()) + "Workstation")
			)

			if SMTDSettings.limitEnabled then
				format "MachineLimit=%\n" SMTDSettings.machineLimit to:jobInfoFile
			else	
				format "MachineLimit=0\n" to:jobInfoFile

			format "OnJobComplete=%\n" SMTDSettings.OnComplete to:jobInfoFile

			format "Interruptible=%\n" SMTDSettings.JobIsInterruptible to:jobInfoFile

			format "OverrideJobFailureDetection=%\n"  SMTDSettings.OverrideJobFailureDetection to:jobInfoFile	
			format "FailureDetectionJobErrors=%\n" SMTDSettings.FailureDetectionJobErrors to:jobInfoFile  
			format "OverrideTaskFailureDetection=%\n"SMTDSettings.OverrideTaskFailureDetection to:jobInfoFile  
			format "FailureDetectionTaskErrors=%\n" SMTDSettings.FailureDetectionTaskErrors to:jobInfoFile  
			format "SendJobErrorWarning=%\n" SMTDSettings.SendJobErrorWarning  to:jobInfoFile 			
			
			
			--format "LimitConcurrentTasksToNumberOfCpus=True\n" to:jobInfoFile

			format "%=%\n" (if SMTDSettings.SlavesBlackList then "Blacklist" else "Whitelist") (SMTDFunctions.getListAsString SMTDSettings.SlavesList) to:jobInfoFile

			local frames = SMTDFunctions.GetFrameSequenceString()
			format "Frames=%\n" frames to:jobInfoFile
			format "ChunkSize=1\n" to:jobInfoFile --Chunks not supported by VRay Deadline plugin?
			
			-- VRay replaces each hash character with a four-digit frame number
			-- If the user has set an output path with two or more consecutive hash characters, Deadline will be unable to parse
			-- the file names produced by VRay with the current mechanism of communicating frame padding to Deadline
			-- Similarly, if a hash character appears in the directory portion of the path, then each frame will be written in a
			-- different directory which is unsupported by the job output feature of Deadline.
			local dirPart = getFileNamePath outputFilename
			if findString outputFilename "##" == undefined and findString dirPart "#" == undefined then
			(
				format "OutputDirectory0=%\n" (getFileNamePath outputFilename) to:jobInfoFile
				format "OutputFilename0=%\n" (filenameFromPath(ReplaceSequenceNumber outputFilename startFrame expand:true )) to:jobInfoFile
			)

			SMTDSettings.AssetsResolved = SMTDFunctions.resolveAssetsFromAssetTracker SubmitExternalFilesMode:3
			for anAsset in SMTDSettings.AssetsResolved do
			(
				format "AWSAssetFile%=%\n" precacheFileCount anAsset to:jobInfoFile
				precacheFileCount += 1
			)
				
			--format "RequiredAssets=\n" to:jobInfoFile

			close jobInfoFile
			
			local pluginInfoFile = createFile pluginInfoFilename encoding:#utf8 writeBOM:false
			-- When File Per Frame tell V-Ray stand-alone to load a .vrscene file for each frame
			local exportFilePerFrame = SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode == 2
			if exportFilePerFrame then
			(
				-- When using SeparateFilesPerFrame, Deadline's V-Ray plugin expects the InputFilename
				-- plugin info option to include the frame number
				local paddedStartFrame = formattedPrint startFrame format:"04i"
				vrsceneName = (getFilenamePath vrsceneName) + (getFilenameFile vrsceneName) + "." + paddedStartFrame + (getFilenameType vrsceneName)
			)
			format "InputFilename=%\n" vrsceneName to:pluginInfoFile
			format "Threads=0\n" to:pluginInfoFile
			format "SeparateFilesPerFrame=%\n" exportFilePerFrame to:pluginInfoFile
			format "CommandLineOptions=\n" to:pluginInfoFile
			format "VRayEngine=V-Ray\n" to:pluginInfoFile
			format "RTTimeout=0.0\n" to:pluginInfoFile
			format "RTNoise=0.001\n" to:pluginInfoFile
			format "RTSamples=0\n" to:pluginInfoFile
			format "DisplayVFB=False\n" to:pluginInfoFile
			format "AutocloseVFB=True\n" to:pluginInfoFile
			format "DisplaySRGB=On\n" to:pluginInfoFile
			close pluginInfoFile
			
			local initialArgs = "" as stringstream
			format "% %\n"  jobInfoFilename pluginInfoFilename to:initialArgs 	
			local retCode = SMTDFunctions.waitForCommandToComplete (initialArgs as string) SMTDSettings.TimeoutSubmission paramIsFile:false
			local renderMsg = SMTDFunctions.getRenderMessage()
			SMTDFunctions.getJobIDFromMessage renderMsg

			if retCode == #success then 
			(
				try(SMTD_MainRollout.Ui_report ("+Job Submitted Successfully!\n"+renderMsg))catch()
				-- Return the job ID
				SMTDSettings.DeadlineSubmissionLastJobID
			)
			else 
			(
				try(SMTD_MainRollout.Ui_report ("--Job Submission FAILED!\n"+renderMsg))catch()
				-- Return an empty string indicating an error
				""
			)	
		),
	
		fn submitMasterExportJobToDeadline vrsceneName outputFilename startFrame endFrame =
		(
			local jobInfoFilename = SMTDPaths.submitSubFolder + "\\SMTVRSA_job_info.ini"
			local pluginInfoFilename = SMTDPaths.submitSubFolder + "\\SMTVRSA_plugin_info.ini"

			local jobInfoFile = createFile jobInfoFilename encoding:#utf8 writeBOM:false
			
			format "Plugin=3dsmax\n" to:jobInfoFile
			format "BatchName=%\n" SMTDSettings.JobName to:jobInfoFile
			format "Name=% - MXS VRSCENE EXPORT\n" SMTDSettings.JobName to:jobInfoFile
			
			local defaultToken = ("Export 3ds Max "+ SMTDFunctions.getMaxVersion() +" "+ (substituteString ((classof renderers.current) as string) "_" "-")   +" to V-Ray Standalone")
			local formattedComment = SMTDFunctions.FormatComment SMTDSettings.Comment defaultTokenValue:defaultToken
			format "Comment=%\n" formattedComment to:jobInfoFile
			
			format "Department=%\n" SMTDSettings.Department to:jobInfoFile
			format "Pool=%\n" SMTDWorkflow_VrayStandaloneExport.PoolName to:jobInfoFile
			format "SecondaryPool=%\n" SMTDWorkflow_VrayStandaloneExport.Pool2Name to:jobInfoFile
			format "Group=%\n" SMTDWorkflow_VrayStandaloneExport.GroupName to:jobInfoFile
			
			format "Priority=%\n" SMTDSettings.Priority to:jobInfoFile
			format "TaskTimeoutMinutes=0\n" to:jobInfoFile
			format "EnableAutoTimeout=False\n" to:jobInfoFile
			format "ConcurrentTasks=1\n" to:jobInfoFile
			format "LimitConcurrentTasksToNumberOfCpus=True\n" to:jobInfoFile
			format "MachineLimit=0\n" to:jobInfoFile
			format "Whitelist=\n" to:jobInfoFile
			format "JobDependencies=\n" to:jobInfoFile
			format "OnJobComplete=%\n" OnComplete to:jobInfoFile

			-- Specify the job output files for the vrscene export job
			case SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode of
			(
				-- Single VRSCENE file
				1: (
					format "OutputFilename0=%\n" vrsceneName to:jobInfoFile
				)
				-- VRSCENE file per frame
				2: (
					local paddedVrsceneFilename = (getFilenamePath vrsceneName) + (getFilenameFile vrsceneName) + ".####" + (getFilenameType vrsceneName)
					format "OutputFilename0=%\n" paddedVrsceneFilename to:jobInfoFile
				)
				-- VRSCENE file per frame (incremental)
				3: (
					local paddedVrsceneFilename = (getFilenamePath vrsceneName) + (getFilenameFile vrsceneName) + ".####" + (getFilenameType vrsceneName)
					format "OutputFilename0=%\n" paddedVrsceneFilename to:jobInfoFile
					format "OutputFilename1=%\n" vrsceneName to:jobInfoFile
				)
			)

			if SMTDSettings.submitAsSuspended do
				format "InitialStatus=Suspended\n" to:jobInfoFile

			case SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode of
			(
				-- Single VRSCENE file
				1: (
					format "Frames=1\n" to:jobInfoFile
				)
				default: (
					format "Frames=%-%\n" startFrame endFrame to:jobInfoFile
				)
			)

			format "ChunkSize=1\n" to:jobInfoFile
			close jobInfoFile
			
			local pluginInfoFile = createFile pluginInfoFilename encoding:#utf8 writeBOM:false

			format "Version=%\n" (SMTDFunctions.getMaxVersion()) to:pluginInfoFile
			format "UseSilentMode=1\n" to:pluginInfoFile
			format "PopupHandling=1\n" to:pluginInfoFile
			format "MAXScriptJob=1\n" to:pluginInfoFile

			format "Render_InputFilename=%\n" vrsceneName to:pluginInfoFile
			format "Render_StartFrame=%\n" startFrame to:pluginInfoFile
			format "Render_EndFrame=%\n" endFrame to:pluginInfoFile
			format "Render_ExportAnimationMode=%\n" SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode to:pluginInfoFile

			close pluginInfoFile
				
			local TempMaxFile = SMTDPaths.submitSubFolder + maxFileName
			if maxFileName == "" do TempMaxFile += "untitled.max"
			if (doesFileExist TempMaxFile) do deleteFile TempMaxFile
			result = SMTDFunctions.SaveMaxFileCopy TempMaxFile	
			
			local initialArgs = "" as stringstream
			format "% % % %/Workflows/MAXScriptJob_VRayStandaloneExport.ms\n" jobInfoFilename pluginInfoFilename TempMaxFile SMTDPaths.MainSubmissionDir to:initialArgs 	
			local retCode = SMTDFunctions.waitForCommandToComplete (initialArgs as string) SMTDSettings.TimeoutSubmission paramIsFile:false
			local renderMsg = SMTDFunctions.getRenderMessage()
			SMTDFunctions.getJobIDFromMessage renderMsg

			if retCode == #success then
			(
				try(SMTD_MainRollout.Ui_report ("+Job Submitted Successfully!\n"+renderMsg))catch()
			)
			else 
			(
				try(SMTD_MainRollout.Ui_report ("--Job Submission FAILED!\n"+renderMsg))catch()
			)
			-- Return the job ID
			SMTDSettings.DeadlineSubmissionLastJobID
		),
		fn sanityCheckWarnings =
		(
			local outputFilename = rendOutputFilename
			local message = ""
			if (matchPattern outputFilename pattern:"*##*") then
				message = message + "Output path contains consecutive hash characters. V-Ray will replace each hash character with the full frame number. This is likely not what you want.\n\n"

			-- Display any warning messages
			if message.count > 0 then
			(
				message = message + "\nAre you sure you want to submit this job?"
				-- We will proceed if the user presses "Yes"
				queryBox message title:"Submission Warnings"
			)
			else
				true
		),
		
		fn submitJob =		--Optional. Called when the SUBMIT button is pressed. If not defined, the submission will not performed
		(
			renderSceneDialog.commit()

			if not sanityCheckWarnings() then
			(
				try(SMTD_MainRollout.Ui_report ("--User aborted due to sanity checks!\n"))catch()
				return false
			)

			local startFrame = currentTime.frame as integer
			local endFrame = currentTime.frame as integer
			case rendTimeType of
			(
				2: (
						startFrame = animationRange.start.frame as integer
						endFrame = animationRange.end.frame as integer
					)
				3: (
						startFrame = rendStart.frame as integer
						endFrame = rendEnd.frame as integer
					)
			)
			::SMTDFunctions.createSubmissionFolderAndUpdatePaths()
			
			local outputFilename = rendOutputFilename
			if renderers.current.output_splitgbuffer and renderers.current.output_splitfilename != undefined and renderers.current.output_splitfilename != "" and renderers.current.output_useram do
				outputFilename = SMTDFunctions.ReturnVraySplitPath renderers.current.output_splitfilename elementType:"RGB_color"

			local theMaxFileName = getFileNameFile maxFilename
			if theMaxFileName == "" do theMaxFileName = "untitled"
			local vrsceneName = getFileNamePath outputFilename + theMaxFileName +".vrscene"
			local frameVrsceneName = ""
			local paddedFrame = ""
			local vrsceneFileHandle = undefined

			case submissionMode of
			(
				-- Local export (on the submitting workstation)
				default:
				(
					case SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode of
					(
						1: (
								-- Single VRSCENE file for all frames
								exportToVRayStd vrsceneName startFrame endFrame
							)
						2: (
								-- Single VRSCENE file for per frame
								for i = startFrame to endFrame do
								(
									paddedFrame = formattedPrint i format:"04i"
									frameVrsceneName = getFileNamePath outputFilename + theMaxFileName + "." + paddedFrame + ".vrscene"
									exportToVRayStd frameVrsceneName startFrame (startFrame + 1)
								)
							)
						3: (
								-- Single VRSCENE file for per frame (incremental)
								paddedFrame = formattedPrint startFrame format:"04i"
								frameVrsceneName = getFileNamePath outputFilename + theMaxFileName + "." + paddedFrame + ".vrscene"
								exportToVRayStd frameVrsceneName startFrame (startFrame + 1)
								vrsceneFileHandle = createfile vrsceneName
								for i = (startFrame + 1) to endFrame do
								(
									paddedFrame = formattedPrint i format:"04i"
									frameVrsceneName = getFileNamePath outputFilename + theMaxFileName + "." + paddedFrame + ".vrscene"
									exportToVRayStd frameVrsceneName i (i + 1) incrBaseFrame:startFrame
									format "#include \"%\"\n" frameVrsceneName to:vrsceneFileHandle
								)
								close vrsceneFileHandle
							)
					)

					local vrayJobId = submitVrsceneJobToDeadline vrsceneName outputFilename startFrame endFrame
					if vrayJobId.count > 0 and SMTDSettings.AssetsPreCacheFiles == true AND SMTDSettings.AssetsIncludeFilesInJob == true then
					(
						local PrecacheResults = SMTDFunctions.CallDeadlineCommandInMemory ("-AWSPortalPrecacheJob " + vrayJobId ) multiLine:true
						try(SMTD_MainRollout.Ui_report (">AWS Portal Pre-Cache Results: \n\n"+PrecacheResults))catch()
					)
				)
				-- Export on Deadline
				2: 
				(
					local masterExportJobId = submitMasterExportJobToDeadline vrsceneName outputFilename startFrame endFrame

					-- When exporting a VRSCENE per frame, we need to specify the frame padded VRSCENE file in the
					-- V-Ray plug-in input file
					case SMTDWorkflow_VrayStandaloneExport.ExportAnimationMode of
					(
						2: (
							-- Single VRSCENE file for per frame
							paddedFrame = formattedPrint startFrame format:"04i"
							frameVrsceneName = getFileNamePath outputFilename + theMaxFileName + "." + paddedFrame + ".vrscene"
							vrsceneName = frameVrsceneName
						)
						3: (
							-- Single VRSCENE file for per frame (incremental)
							vrsceneFileHandle = createfile vrsceneName
							for i = startFrame to endFrame do
							(
								paddedFrame = formattedPrint i format:"04i"
								frameVrsceneName = getFileNamePath outputFilename + theMaxFileName + "." + paddedFrame + ".vrscene"
								format "#include \"%\"\n" frameVrsceneName to:vrsceneFileHandle
							)
							close vrsceneFileHandle
						)
					)

					submitVrsceneJobToDeadline vrsceneName outputFilename startFrame endFrame dependency:masterExportJobId
				)
			)
		)
	)
	SMTDWorkflow_VrayStandaloneExport = SMTDWorkflow_VrayStandaloneExportStruct()--return an instance of the struct
)

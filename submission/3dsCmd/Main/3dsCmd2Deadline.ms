macroScript Cmd2DeadlineMain category:"Thinkbox" tooltip:"Internal! Use Deadline>MaxCmd2Deadline!"
(
	--------------------------------------------------------------------------------
	-- MaxCmd2DeadlineMain
	-- Deadline submission script for 3dsmax
	-- Copyright (c) 2003-2017 Thinkbox Software Inc
	-- All rights reserved.
	--------------------------------------------------------------------------------
	-- Based on SubmitToDeadline script by Thinkbox Software Inc
	--------------------------------------------------------------------------------
	-- NOTE: This script is being called by the Updater/Launcher
	-- defined in Deadline-MaxCmd2Deadline.mcr
	--------------------------------------------------------------------------------
	global DlgMax2DeadlineRollout
	global MAXCmd2Deadline_PerformSanityCheck
	
	if MAXCmd2Deadline_PerformSanityCheck == undefined then 
		fn MAXCmd2Deadline_PerformSanityCheck = 
		(
			querybox "Sanity Check Function NOT INSTALLED!\nPress [Yes] to SUBMIT the job without sanity check\nPress [No] to CANCEL the submission." title:"Sanity Check Problem:"
		)
	
	try (DestroyDialog DlgMax2DeadlineRollout) catch()

	global M2DSettings
	
	local deadlineMaximumPriority = 100
	local deadlinePools = #()
	local deadlineSecondaryPools = #()
	local deadlineGroups = #()
	
	local DeadlineSubmissionSuccessful = false
	global DeadlineSubmissionLastJobID = "failed"
	
	local kDeadlineSubmitOutput = sysInfo.tempdir + "submitOutput.txt"
	local kDeadlineSubmitExitCode = sysInfo.tempdir + "submitExitCode.txt"

	local LastSubRollout = 1
	local M2D_Rollouts
	local M2D_MaxRollout, M2D_GpuRollout, M2D_AdvancedRollout
	
	global IntegrationKVPs = #()
	--local kHomeDir = "c:\\Deadline\\"
	
	local kHomeDir = ""
	try
	(
		local result = -2

		deleteFile kDeadlineSubmitOutput
		deleteFile kDeadlineSubmitExitCode
		
		local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
		ShellLaunch deadlineCommandBG ("-outputfiles \"" + kDeadlineSubmitOutput + "\" \"" + kDeadlineSubmitExitCode + "\" -GetCurrentUserHomeDirectory")
				
		local startTimeStamp = timestamp()
		local ready = false
		while not ready do
		(
			sleep 0.15
			if doesFileExist kDeadlineSubmitExitCode do
			(
				local theFile = openFile kDeadlineSubmitExitCode
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
			local resultFile = OpenFile kDeadlineSubmitOutput
			local resultMsg = ""
			if (resultFile != undefined) do
			(
				try(resultMsg = readLine resultFile)catch()
				try(close resultFile)catch()
			)
			
			kHomeDir = resultMsg + "\\"
		)
	) catch ()
	
	local kTempDir = kHomeDir + "temp/"
	makeDir kTempDir
	
	local kDeadlineSubmitInfofile = kTempDir + "max_submit_info.job"
	local kDeadlineJobInfofile = kTempDir + "max_job_info.job"
	
	deadlineIniFile = GetDir #plugcfg + "\\Max2Deadline.ini"
	

	--All the settings contained in one of the Tabbed rollouts need to be maintained in a struct like this (kinda like in SMTD).
	--Otherwise, we can't make the settings persist between tab-switching...
	struct M2DSettingsStructure
	(
		--Max render settings
		FrameList = "",
		ChunkSize = 1,
		ForceBuild = 1,
		ShowVFB = true,
		VideoPost = false,
		ContinueOnError = true,
		SubmitScene = true,
		LocalRendering = false,
		
		GammaCorrection = false,
		GammaInput = 1.0,
		GammaOutput = 1.0,
		
		SplitRendering = false,
		SplitStrips = 2,
		SplitOverlap = 0,
		
		DBR = false,
		DBRServers = 5,

		GpusPerTask = 0,
		GpuDevices = "",
		
		PerformSanityCheck = false,

		PathConfig = "",
		RenderPreset = "",
		PreRenderScript = "",
		PostRenderScript = "",
		SceneState = "",
		BatchRender = False,
		BatchRenderName = "",
		StillFrame = False,
		ImageSequenceFile = 1
	)
	
	::M2DSettings = M2DSettingsStructure()
	
	-----------------------------------------------------------------------------------------------
	--MAIN ROLLOUT
	-----------------------------------------------------------------------------------------------

	rollout DlgMax2DeadlineRollout "Submit To Deadline (3dsCmd)" width:410 height:764
	(
		group "Job Description" 
		(
			edittext edt_jobname "Job Name" fieldwidth:310 align:#right 

			edittext edt_comment " Comment" fieldwidth:310 align:#right 
						
			edittext edt_dept "Department" fieldwidth:310 align:#right
		)   
		
		group "Job Scheduling" 
		(
			--label lbl_pools "Pool" align:#left offset:[38,4] across:3
			--dropdownList ddl_poollist "" width:134 align:#center offset:[-55,0]
			--checkbox chk_onlypool "Use Machines In Pool Only" align:#right offset:[-10,3]
			
			label lbl_pools "Pool" align:#left offset:[59,4] across:2
			dropdownList ddl_poollist "" width:302 align:#right offset:[1,0] tooltip:"The pool that your job will be submitted to."
			
			label lbl_secondarypools "Secondary Pool" align:#left offset:[5,4] across:2
			dropdownList ddl_secondarypoollist "" width:302 align:#right offset:[1,0] tooltip:"The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves."

			label lbl_groups "Group" align:#left offset:[50,4] across:2
			dropdownList ddl_groups "" width:302 align:#right offset:[1,0] tooltip:"The group that your job will be submitted to."

			label lbl_priority "Priority" align:#left offset:[45,2] across:3
			progressbar sld_priority width:255 height:18 range:[0,100,50] type:#integer align:#right offset:[82,0]
			spinner spn_priority "" type:#integer fieldwidth:35 align:#right offset:[0,1]
			
			label lbl_timeout "Task Timeout" align:#left offset:[15,3] across:3
			spinner spn_timeout range:[0,5000,0] type:#integer align:#right fieldwidth:100 offset:[-64,2]
			checkbox chk_autoTimeout "Enable Auto Task Timeout" offset:[-50,2] tooltip:"If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job."
			
			label lbl_concurrentTasks "Concurrent Tasks" align:#left offset:[-5,3] across:3
			spinner spn_concurrentTasks range:[1,16,1] type:#integer align:#right fieldwidth:100 offset:[-64,2]
			checkbox chk_concurrentTasks "Limit Tasks To Slave's Task Limit" offset:[-50,2] tooltip:"If you limit the tasks to a Slave's task limit, then by default, the Slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual Slaves by an administrator."

			label lbl_limit "Machine Limit" align:#left offset:[15,3] across:3
			spinner spn_machineLimit range:[0,1000,0] type:#integer align:#right fieldwidth:100 offset:[-64,2]
			checkbox chk_isBlacklist "Machine List Is A Blacklist" offset:[-50,2] tooltip:"You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist."
			
			edittext edt_machineList "Machine List" fieldwidth:275 align:#left offset:[21,0] across:2
			button btn_machineList "..." width:20 align:#left offset:[171,-2] tooltip:"Click to select a Machine List."
			
			edittext edt_limitgroups "Limits" fieldwidth:275 align:#left offset:[53,0] across:2
			button btn_limitgroups "..." width:20 align:#left offset:[171,-2] tooltip:"Click to select Limits."
			
			edittext edt_dependencies "Dependencies" fieldwidth:275 align:#left offset:[12,0] across:2
			button btn_dependencies "..." width:20 align:#left offset:[171,-2] tooltip:"Click to select Job Dependencies."
			
			label lbl_onComplete "On Complete" align:#left offset:[17,4] across:3
			dropdownList ddl_onComplete items:#("Nothing", "Archive", "Delete") align:#left offset:[-45,0] width:110 tooltip:"If desired, you can automatically archive or delete the job when it completes."
			checkbox chk_submitAsSuspended "Submit As Suspended" offset:[-50,4] tooltip:"If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render."
		)
		
		dotNetControl dn_tabs "System.Windows.Forms.TabControl" height:20 width:400 align:#center offset:[0,-3]
		
		subRollout sub_SubRollout width:415 height:208 align:#center offset:[0,-3]
		
		on dn_tabs Selected itm do
		(
			if LastSubRollout != (itm.TabPageIndex+1) do --do not update if the same tab clicked twice
			(
				dn_tabs.enabled = false
				for subroll in M2D_Rollouts[LastSubRollout][2] do
					removeSubRollout sub_SubRollout subroll
				for subroll in M2D_Rollouts[LastSubRollout = itm.TabPageIndex+1][2] do	
					addSubRollout sub_SubRollout subroll
				dn_tabs.enabled = true
			) 
		)--end tabs clicked

		checkbox chk_closeAfterSubmission "Close Dialog After Submission" offset:[0,-3] across:3
		label lbl_lastSubmissionState "Last Submission:" offset:[124,-2]
		progressbar sld_lastSubmissionState width:35 height:18 color:blue align:#right value:100 offset:[8,-3]
		
		button btn_renderdialog "Render Dialog..." width:99 height:30 offset:[-7,-3] align:#center tooltip:"Open 3ds Render Scene Dialog..." across:4
		button btn_openMonitor "Monitor..." width:99 height:30 offset:[-3,-3] align:#center tooltip:"Launch Deadline Monitor..."
		button btn_integration "Pipeline Tools..." width:99 height:30 offset:[2,-3] align:#centre tooltip:"Open the Pipeline Tools Dialog..."
		button btn_submit "SUBMIT" width:99 height:26 offset:[7,-1] align:#centre tooltip:"Submit the current 3ds scene to Deadline."
		
		imgTag tag_submitTop height:2 width:99 offset:[9,-35] align:#right
		imgTag tag_submitBottom height:2 width:99 offset:[9,21] align:#right

		listbox lbx_report height:6 width:400 align:#center offset:[0,0]

		fn AnimateLastSubmissionState =
		(
			sld_lastSubmissionState.value += 1
			if sld_lastSubmissionState.value >= 100 then sld_lastSubmissionState.value = 2
		)
		
		fn Ui_report txt =
		(
			if (MaxVersion())[1] < 6000 then
			(
				local temp = lbx_report.items
				append temp txt
				lbx_report.items = temp
				lbx_report.selection = lbx_report.items.count
			)
			else
			(
				strStream = txt as StringStream
				local temp = lbx_report.items 
				while not eof strStream do
					append temp (readline strStream)
				lbx_report.items = temp
				lbx_report.selection = lbx_report.items.count
			)
		)

		fn SaveMaxFileCopy destFileName =
		(
			sld_lastSubmissionState.value = 50
			local holdMaxDir = (GetDir #autoback) + "/"
			local holdFileName
			local holdTempFileName			
			
			if maxOps.productAppID == #viz then
			(
				holdFileName = holdMaxDir + "vizhold.mx"
				holdTempFileName = holdMaxDir + "vizhold.tmp"
			)
			else
			(
				holdFileName = holdMaxDir + "maxhold.mx"
				holdTempFileName = holdMaxDir + "maxhold.tmp"
			)
			local holdExists = doesFileExist holdFileName
			
			if holdExists then 
			(
				deleteFile holdTempFileName
				renameFile holdFileName holdTempFileName
			)
	
			holdMaxFile()

			if not (doesFileExist holdFileName) do 
				return "Saving the file via hold() did not work."
			
			if not (renameFile holdFileName destFileName) do
				if not (copyFile holdFileName destFileName) do
					return ("Could not copy the saved max file to " + destFileName)
			
			if holdExists do
			(
				deleteFile holdFileName
				renameFile holdTempFileName holdFileName
			)
			
			return undefined
		)

		-- Read a text file into an array, with one entry per line
		fn ReadFileIntoArray filename anArray =
		(
			hFile = OpenFile filename
			res = #failure
			if (hFile != undefined) then
			(
				try 
				(
					while (not eof hFile) do append anArray (ReadLine hFile)
					res = #success
				)
				catch()
					close hFile
			)
			else
				res = #fileNotFound
				
			res     
		)

		fn UpdateComment = 
		(
			if substring edt_comment.text 1 8 == "3dsmax v" or substring edt_comment.text 1 11 == "MAXScript v" or edt_comment.text == "" or substring edt_comment.text 1 8 == "3dsviz v" or substring edt_comment.text 1 10 == "3dsviz 200" do
			(
				if maxOps.productAppID == #viz then
				(
					vString = (((maxVersion())[1])/1000.0) as string
					if vString == "7.0" then
						edt_comment.text = "3dsviz 2006 Scene Submission"
					else if vString == "8.0" then
						edt_comment.text = "3dsviz 2007 Scene Submission"
					else if vString == "9.0" then
						edt_comment.text = "3dsviz 2008 Scene Submission"
					else
						edt_comment.text = "3dsviz "+ vString +" Scene Submission"
				)
				else
				(
					local versionString = ""
					if( ((maxVersion())[1]/1000 as integer) > 9 ) then
						versionString = ((((maxVersion())[1]/1000 as integer) + 1998) as string)
					else
						versionString = (((maxVersion())[1]/1000 as integer) as string)
					edt_comment.text = "3ds Cmd "+ versionString +" Scene Submission"
					
					/*
					vString = (((maxVersion())[1])/1000.0) as string
					if vString == "12.0" then
						edt_comment.text = "3dsmax 2010 Scene Submission"
					else if vString == "11.0" then
						edt_comment.text = "3dsmax 2009 Scene Submission"
					else if vString == "10.0" then
						edt_comment.text = "3dsmax 2008 Scene Submission"
					else
						edt_comment.text = "3dsmax "+ vString +" Scene Submission"
					*/
				)
			)   
		)
		
		fn GetDeadlineLine argument =
		(
			line = "Error getting line"
		
			deleteFile kDeadlineSubmitExitCode
			local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
			ShellLaunch deadlineCommandBG ("-outputfiles \"" + kDeadlineSubmitOutput + "\" \"" + kDeadlineSubmitExitCode + "\" " + argument)
			
			startTimeStamp = timestamp()
			ready = false
			while not ready do
			(
				sleep 0.25
				if doesFileExist kDeadlineSubmitExitCode then
				(
					hFile = OpenFile kDeadlineSubmitOutput
					if (hFile != undefined) then
					(
						try 
						(
							if (not eof hFile) do
							(
								result = (ReadLine hFile)
								if result != "Action was cancelled by user" do line = result
								ready = true
							)
						)
						catch()
							close hFile
					)
				)
				
				if timestamp() - startTimeStamp > 10000 then 
					ready = true
			)
			
			line
		)
		
		fn GetMaximumPriority =
		(
			deadlineMaximumPriority = 100
		
			deleteFile kDeadlineSubmitExitCode
			local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
			ShellLaunch deadlineCommandBG ("-outputfiles \"" + kDeadlineSubmitOutput + "\" \"" + kDeadlineSubmitExitCode + "\" -getmaximumpriority")
			
			startTimeStamp = timestamp()
			ready = false
			result = 0
			while not ready do
			(
				sleep 0.25
				if doesFileExist kDeadlineSubmitExitCode do
				(
					local theFile = openFile kDeadlineSubmitExitCode
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
				local resultFile = OpenFile kDeadlineSubmitOutput
				if (resultFile != undefined) do
				(
					try(deadlineMaximumPriority = readValue resultFile)catch()
					try(close resultFile)catch()
				)
				
				return deadlineMaximumPriority
			)
			
			return #commandFailed
		)
		
		fn CollectPools =
		(
			deadlinePools = #()
			deadlineSecondaryPools = #("")
			deleteFile kDeadlineSubmitExitCode
			local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
			ShellLaunch deadlineCommandBG ("-outputfiles \"" + kDeadlineSubmitOutput + "\" \"" + kDeadlineSubmitExitCode + "\" -pools")
			
			startTimeStamp = timestamp()
			ready = false
			while not ready do
			(
				sleep 0.25
				if doesFileExist kDeadlineSubmitExitCode then
				(
					local result = ReadFileIntoArray kDeadlineSubmitOutput deadlinePools
					
					deadlineSecondaryPools = join deadlineSecondaryPools deadlinePools
					
					return result
				)
				
				if timestamp() - startTimeStamp > 10000 then 
					return #commandFailed
			)
		)
		
		fn CollectGroups =
		(
			deadlineGroups = #()
			deleteFile kDeadlineSubmitExitCode
			local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
			ShellLaunch deadlineCommandBG ("-outputfiles \"" + kDeadlineSubmitOutput + "\" \"" + kDeadlineSubmitExitCode + "\" -groups")
			
			startTimeStamp = timestamp()
			ready = false
			while not ready do
			(
				sleep 0.25
				if doesFileExist kDeadlineSubmitExitCode then
					return ReadFileIntoArray kDeadlineSubmitOutput deadlineGroups
				if timestamp() - startTimeStamp > 10000 then 
					return #commandFailed
			)
		)
		
		fn SaveUI holdScene:false =
		(
			winPos = GetDialogPos DlgMax2DeadlineRollout
			SetIniSetting deadlineIniFile "SubmitDialog" "PositionX" ((winPos.x as integer) as string)
			SetIniSetting deadlineIniFile "SubmitDialog" "PositionY" ((winPos.y as integer) as string)
			
			SetIniSetting deadlineIniFile "AdvancedSettings" "PerformSanityCheck" (M2DSettings.PerformSanityCheck as string)
			SetIniSetting deadlineIniFile "AdvancedSettings" "CloseAfterSubmission" (chk_closeAfterSubmission.state as string)
			
			SetIniSetting deadlineIniFile "JobSettings" "Department" (edt_dept.text)
			SetIniSetting deadlineIniFile "JobSettings" "Group" (ddl_groups.selected)
			
			SetIniSetting deadlineIniFile "JobSettings" "Priority" (spn_priority.value as string)
			SetIniSetting deadlineIniFile "JobSettings" "Pool" (ddl_poollist.selected)
			SetIniSetting deadlineIniFile "JobSettings" "SecondaryPool" (ddl_secondarypoollist.selected)
			
			SetIniSetting deadlineIniFile "JobSettings" "MachineLimit" (spn_machineLimit.value as string)
			SetIniSetting deadlineIniFile "JobSettings" "IsBlacklist" (chk_isBlacklist.state as string)
			SetIniSetting deadlineIniFile "JobSettings" "TaskTimeout" (spn_timeout.value as string)
			SetIniSetting deadlineIniFile "JobSettings" "ConcurrentTasks" (spn_concurrentTasks.value as string)
			SetIniSetting deadlineIniFile "JobSettings" "LimitConcurrentTasksToNumberOfCpus" (chk_concurrentTasks.state as string)
			SetIniSetting deadlineIniFile "JobSettings" "AutoTimeout" (chk_autoTimeout.state as string)
			SetIniSetting deadlineIniFile "JobSettings" "ChunkSize" (M2DSettings.ChunkSize as string)
			
			SetIniSetting deadlineIniFile "JobSettings" "ContinueOnError" (M2DSettings.ContinueOnError as string)
			SetIniSetting deadlineIniFile "JobSettings" "SubmitScene" (M2DSettings.SubmitScene as string)
			SetIniSetting deadlineIniFile "JobSettings" "LocalRendering" (M2DSettings.LocalRendering as string)
			
			SetIniSetting deadlineIniFile "JobSettings" "GammaCorrection" (M2DSettings.GammaCorrection as string)
			SetIniSetting deadlineIniFile "JobSettings" "GammaInput" (M2DSettings.GammaInput as string)
			SetIniSetting deadlineIniFile "JobSettings" "GammaOutput" (M2DSettings.GammaOutput as string)
			
			SetIniSetting deadlineIniFile "SplitSettings" "Splits" (M2DSettings.SplitStrips as string)
			SetIniSetting deadlineIniFile "SplitSettings" "Overlap" (M2DSettings.SplitOverlap as string)
			
			SetIniSetting deadlineIniFile "DBRSettings" "DBRServers" (M2DSettings.DBRServers as string)

			SetIniSetting deadlineIniFile "AdvancedOptions" "PathConfigFile" (M2DSettings.PathConfig)
			SetInISetting deadlineIniFile "AdvancedOptions" "RenderPresetFile" (M2DSettings.RenderPreset)

			SetInISetting deadlineIniFile "AdvancedOptions" "PreRenderScript" (M2DSettings.PreRenderScript)
			SetInISetting deadlineIniFile "AdvancedOptions" "PostRenderScript" (M2DSettings.PostRenderScript)

			SetIniSetting deadlineIniFile "AdvancedOptions" "BatchRender" (M2DSettings.BatchRender as string)
			SetIniSetting deadlineIniFile "AdvancedOptions" "StillFrame" (M2DSettings.StillFrame as string)
			SetIniSetting deadlineIniFile "AdvancedOptions" "ImageSequenceFile" (M2DSettings.ImageSequenceFile as string)
			
			--make sure the global settings (ie, Shotgun) are saved
			if holdScene do
				max hold
		)
		
		fn fixBackSlashes txt =
		(
			for i = 1 to txt.count do
				if substring txt i 1 == "\\" do txt[i] = "/"
			txt
		)
		
		fn getRendererIdString =
		(
			case (renderers.current.classid as string) of
			(
				"#(1, 0)": "scanline"
				"#(1L, 0L)": "scanline"
				
				"#(95494396, 474502030)": "brmax"
				"#(95494396L, 474502030L)": "brmax"
				
				"#(1492548972, 1338981315)": "mentalray"
				"#(1492548972L, 1338981315L)": "mentalray"
				
				"#(1941615238, 2012806412)": "vray"
				"#(1941615238L, 2012806412L)": "vray"
				
				"#(1770671000, 1323107829)": "vrayrt"
				"#(1770671000L, 1323107829L)": "vrayrt"
				
				"#(-1204370534, -399920359)": "krakatoa"
				"#(3090596762L, 3895046937L)": "krakatoa"
				
				"#(217131703, 58075251)": "finalrender"
				"#(217131703L, 58075251L)": "finalrender"
				
				"#(272052741, 712862621)": "maxwell"
				"#(272052741L, 712862621L)": "maxwell"
				
				"#(268839321, 1854680990)": "quicksilver"
				"#(268839321L, 1854680990L)": "quicksilver"
				
				"#(1048411834, 348141227)": "iray"
				"#(1048411834L, 348141227L)": "iray"
				
				"#(1655201228, 1379677700)": "corona"
				"#(1655201228L, 1379677700L)": "corona"
				
				"#(2980325325L, 2688898415L)": "art"
				
				"#(198269858, 1937796512)": "redshift"
				"#(198269858L, 1937796512L)": "redshift"

				"#(-1577524843, 1319335807)": "octane"
				"#(2717442453L, 1319335807L)": "octane"
				
				"#(2980329694L, 2688902778L)": "arnold"
				default: ""
			)   
		)

		fn getMaxVersionAsInteger =
		(
			if( ((maxVersion())[1]/1000 as integer) > 9 ) then
				(((maxVersion())[1]/1000 as integer) + 1998)
			else
				((maxVersion())[1]/1000 as integer)
		)
		
		fn waitForCommandToComplete params timeOutInSec =
		(
			local result = -2
			deleteFile kDeadlineSubmitExitCode
			deleteFile kDeadlineSubmitOutput 
			
			local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
			ShellLaunch deadlineCommandBG ("-outputfiles \"" + kDeadlineSubmitOutput + "\" \"" + kDeadlineSubmitExitCode + "\" " + params)
			
			startTimeStamp = timestamp()
			ready = false
			while not ready do
			(
				sleep 0.25
				AnimateLastSubmissionState()
				if doesFileExist kDeadlineSubmitExitCode then
				(
					theFile = openFile kDeadlineSubmitExitCode 
					try(result = readValue theFile)catch(result = -2)
					close theFile
					ready = true
				)   
				if timestamp() - startTimeStamp > timeOutInSec*1000 then 
				(
					result = -3
					ready = true
				)   
			)               
			return case result of
			(
				0: #success
				(-1): #failed
				(-2): #readerror
				(-3): #timeout
			)   
		)       
		
		fn job_priority_update val =
		(
			if val <= deadlineMaximumPriority do
			(
				theRed = (255.0 - 255.0*val/(deadlineMaximumPriority as float))*2.0
				if theRed > 255 do theRed = 255
				theGreen = 512.0*val/(deadlineMaximumPriority as float)
				if theGreen > 255 do theGreen = 255
				
				spn_priority.value = val
				
				sld_priority.color = [theRed, theGreen, 0]
				sld_priority.value = (val * 100) / deadlineMaximumPriority
			)
		)
		
		fn machine_limit_update val =
		(
			spn_machineLimit.value = val
		)
		
		fn timeout_update val =
		(
			spn_timeout.value = val
		)

		fn concurrent_tasks_update val =
		(
			spn_concurrentTasks.value = val
		)
	
		fn LoadUI =
		(   
			thebmp = bitmap 1 1 color:green
			tag_submitTop.bitmap = thebmp
			tag_submitBottom.bitmap = thebmp

			val = getIniSetting deadlineIniFile "AdvancedSettings" "PerformSanityCheck" 
			if val != "" do M2DSettings.PerformSanityCheck = (execute val)

			val = getIniSetting deadlineIniFile "AdvancedSettings" "CloseAfterSubmission" 
			if val != "" do chk_closeAfterSubmission.state = (execute val)

			edt_dept.text = getIniSetting deadlineIniFile "JobSettings" "Department"

			--val = getIniSetting deadlineIniFile "JobSettings" "PoolExclusive" 
			--if val != "" do chk_onlypool.state = (execute val)
			
			val = getIniSetting deadlineIniFile "JobSettings" "Group"
			if val != "" do
			(
				defItem = findItem deadlineGroups val
				if defItem != 0 do ddl_groups.selection = defItem
			)

			val = getIniSetting deadlineIniFile "JobSettings" "Pool" 
			if val != "" do 
			(
				defItem = findItem deadlinePools val 
				if defItem != 0 do ddl_poollist.selection = defItem
			)
			
			val = getIniSetting deadlineIniFile "JobSettings" "SecondaryPool" 
			if val != "" do 
			(
				defItem = findItem deadlineSecondaryPools val 
				if defItem != 0 do ddl_secondarypoollist.selection = defItem 
			)

			val = getIniSetting deadlineIniFile "JobSettings" "Priority" 
			if val != "" then
			(
				currPriority = (execute val)
				if currPriority > deadlineMaximumPriority do currPriority = deadlineMaximumPriority
				job_priority_update currPriority
			)
			else
			(
				defPriority = deadlineMaximumPriority / 2
				job_priority_update defPriority
			)

			val = getIniSetting deadlineIniFile "JobSettings" "MachineLimit" 
			if val != "" then machine_limit_update (execute val) else machine_limit_update 0
			
			val = getIniSetting deadlineIniFile "JobSettings" "IsBlacklist"
			if val != "" do chk_isBlacklist.state = (execute val)
			
			val = getIniSetting deadlineIniFile "JobSettings" "TaskTimeout" 
			if val != "" then timeout_update (execute val) else timeout_update 0
			
			val = getIniSetting deadlineIniFile "JobSettings" "AutoTimeout"
			if val != "" do chk_autoTimeout.state = (execute val)

			val = getIniSetting deadlineIniFile "JobSettings" "ConcurrentTasks"
			if val != "" then concurrent_tasks_update (execute val) else concurrent_tasks_update 1

			val = getIniSetting deadlineIniFile "JobSettings" "LimitConcurrentTasksToNumberOfCpus"
			if val != "" do chk_concurrentTasks.state = (execute val)
			
			val = getIniSetting deadlineIniFile "JobSettings" "ChunkSize"
			if val != "" then M2DSettings.ChunkSize = (execute val)
			
			val = getIniSetting deadlineIniFile "JobSettings" "ContinueOnError"
			if val != "" do M2DSettings.ContinueOnError = (execute val)
			
			val = getIniSetting deadlineIniFile "JobSettings" "LocalRendering"
			if val != "" do M2DSettings.LocalRendering = (execute val)
			
			val = getIniSetting deadlineIniFile "JobSettings" "SubmitScene"
			if val != "" do M2DSettings.SubmitScene = (execute val)
			
			val = getIniSetting deadlineIniFile "JobSettings" "GammaCorrection"
			if val != "" do M2DSettings.GammaCorrection = (execute val)
			
			val = getIniSetting deadlineIniFile "JobSettings" "GammaInput"
			if val != "" do M2DSettings.GammaInput = (execute val)
			
			val = getIniSetting deadlineIniFile "JobSettings" "GammaOutput"
			if val != "" do M2DSettings.GammaOutput = (execute val)
			
			val = getIniSetting deadlineIniFile "SplitSettings" "Splits"
			if val != "" do M2DSettings.SplitStrips = (execute val)
			
			val = getIniSetting deadlineIniFile "SplitSettings" "Overlap"
			if val != "" do M2DSettings.SplitOverlap = (execute val)
			
			val = getIniSetting deadlineIniFile "DBRSettings" "DBRServers"
			if val != "" do M2DSettings.DBRServers = (execute val)

			M2DSettings.PathConfig = getIniSetting deadlineIniFile "AdvancedOptions" "PathConfigFile"
			M2DSettings.RenderPreset = getIniSetting deadlineIniFile "AdvancedOptions" "RenderPresetFile"
			M2DSettings.PreRenderScript = getIniSetting deadlineIniFile "AdvancedOptions" "PreRenderScript"
			M2DSettings.PostRenderScript = getIniSetting deadlineIniFile "AdvancedOptions" "PostRenderScript"

			val = getIniSetting deadlineIniFile "AdvancedOptions" "BatchRender"
			if val != "" do M2DSettings.BatchRender = (execute val)

			val = getIniSetting deadlineIniFile "AdvancedOptions" "StillFrame"
			if val != "" do M2DSettings.StillFrame = (execute val)

			val = getIniSetting deadlineIniFile "AdvancedOptions" "ImageSequenceFile"
			if val != "" do M2DSettings.ImageSequenceFile = (execute val)

			buildSelection = 1
			if (MaxVersion())[1] > 8000 and maxOps.productAppID != #viz then
			(
				if is64bitApplication() then
					buildSelection = 3
				else
					buildSelection = 2
			)
			M2DSettings.ForceBuild = buildSelection

			UpdateComment()
		)
		
		-- For a given array of frame numbers, creates a compact string in the form used by the
		-- "pickup frames" render type (ie. "1-5,7,9")
		fn GetSequenceString frameNumbers =
		(
			local seqString = StringStream ""
			local curIndex = 1
			while (curIndex <= frameNumbers.count) do
			(
				local baseNumber = frameNumbers[curIndex]
				local baseIndex = curIndex
				local runLen = 1
				while (curIndex < frameNumbers.count) and (baseNumber+runLen) == frameNumbers[curIndex+1] do 
				(
					runLen += 1
					curIndex += 1
				)
				case runLen of
				(
					1:      format "%" (frameNumbers[curIndex].frame as integer) to:seqString
					2:      format "%,%" (frameNumbers[baseIndex].frame as integer) (frameNumbers[curIndex].frame as integer) to:seqString
					default:    format "%-%" (frameNumbers[baseIndex].frame as integer) (frameNumbers[curIndex].frame as integer) to:seqString
				)
				if (curIndex != frameNumbers.count) do format "," to:seqString
					curIndex += 1
			)
			seqString as string
		)
		
		fn SearchIntegrationKVPs searchValue =
		(
			global IntegrationKVPs
			local found = false

			for kvPair in IntegrationKVPs do
			(
				if searchValue == kvPair[1] then
				(
					found = true
				)
			)

			found
		)

		fn FindIntegrationKVPIndex searchValue =
		(
			global IntegrationKVPs
			local index = -1

			for i = 1 to IntegrationKVPs.count do
			(
				if searchValue == IntegrationKVPs[i][1] then
				(
					index = i
				)

			)

			index
		)

		fn CreateSubmitInfoFile filename strip:0 =
		(       
			global IntegrationKVPs

			local submitInfoFile = CreateFile filename

			if (submitInfoFile != undefined) then
			(
				format "Plugin=3dsCmd\n" to:submitInfoFile
				format "ForceReloadPlugin=false\n" to:submitInfoFile

				local frames = M2DSettings.FrameList
				local chunkSize = M2DSettings.ChunkSize
				if M2DSettings.DBR do
				(
					local rendererID = DlgMax2DeadlineRollout.getRendererIdString()
					if (rendererID == "mentalray") or (rendererID == "vray") or (rendererID == "vrayrt") do
					(
						frames = "0-" + ((M2DSettings.DBRServers-1) as string)
						chunkSize = 1
					)
				)

				format "Frames=%\n" frames to:submitInfoFile
				format "ChunkSize=%\n" chunkSize to:submitInfoFile
				format "Priority=%\n" spn_priority.value to:submitInfoFile
				format "Pool=%\n" ddl_poollist.selected to:submitInfoFile
				format "SecondaryPool=%\n" ddl_secondarypoollist.selected to:submitInfoFile
				--format "PoolMachinesOnly=%\n"   chk_onlypool.state        to:submitInfoFile
				
				if strip > 0 then
					format "Name=% - Strip % of %\n" edt_jobname.text strip M2DSettings.SplitStrips to:submitInfoFile
				else
					format "Name=%\n" edt_jobname.text to:submitInfoFile
					
				format "Comment=%\n" edt_comment.text to:submitInfoFile
				format "Department=%\n" edt_dept.text to:submitInfoFile
				format "Group=%\n" ddl_groups.selected to:submitInfoFile
				
				format "LimitGroups=%\n" edt_limitgroups.text to:submitInfoFile
				format "JobDependencies=%\n" edt_dependencies.text to:submitInfoFile
				
				--format "DeleteOnComplete=%\n" chk_autoDelete.checked to:submitInfoFile
				format "OnJobComplete=%\n" ddl_onComplete.selected to:submitInfoFile
				if chk_submitAsSuspended.checked do
					format "InitialStatus=Suspended\n" to:submitInfoFile    
				
				format "TaskTimeoutMinutes=%\n" spn_timeout.value to:submitInfoFile
				format "EnableAutoTimeout=%\n" chk_autoTimeout.checked to:submitInfoFile

				format "ConcurrentTasks=%\n" spn_concurrentTasks.value to:submitInfoFile
				format "LimitConcurrentTasksToNumberOfCpus=%\n" chk_concurrentTasks.checked to:submitInfoFile
				
				format "MachineLimit=%\n" spn_machineLimit.value to:submitInfoFile
				if chk_isBlacklist.checked then
					format "Blacklist=%\n" edt_machineList.text to:submitInfoFile
				else
					format "Whitelist=%\n" edt_machineList.text to:submitInfoFile
				
				outputFilenameIndex = 0

				-- If an output filename is specified, include it in the submit info file
				if rendSaveFile and rendOutputFilename != "" then
				(
					format "OutputDirectory0=%\n" (getFilenamePath rendOutputFilename) to:submitInfoFile
					format "OutputFilename0=%\n" ((getFilenameFile rendOutputFilename) + "####" + (getFilenameType rendOutputFilename)) to:submitInfoFile
					outputFilenameIndex = outputFilenameIndex + 1
				)

				-- Include render elements
				reManager = maxOps.GetCurRenderElementMgr()
				reCount = reManager.NumRenderElements()
				for i = 0 to reCount - 1 do
				(
					if classof (reManager.GetRenderElement i) != Missing_Render_Element_Plug_in do --ignore RE's that return as missing in the scene
					(
						reFilename = reManager.GetRenderElementFilename i
						if reFilename != undefined and reFilename != "" do --skip RE's if output file path is undefined or empty
						(                        
							format "OutputDirectory%=%\n" outputFilenameIndex (getFilenamePath reFilename) to:submitInfoFile
							format "OutputFilename%=%\n" outputFilenameIndex ((getFilenameFile reFilename) + "####" + (getFilenameType reFilename)) to:submitInfoFile                        
							outputFilenameIndex = outputFilenameIndex + 1
						)
					)
				)

				local groupBatch = false

				if SearchIntegrationKVPs "integrationSettingsPath" then
				(
					pathIndex = FindIntegrationKVPIndex "integrationSettingsPath"
					integrationsFile = openFile IntegrationKVPs[pathIndex][2]

					if integrationsFile != undefined then
					(
						while not eof integrationsFile do
						(
							theLine = readline integrationsFile
							
							format "%\n" theLine to:submitInfoFile
						)
					)

					if SearchIntegrationKVPs "batchMode" then
					(
						batchModeIndex = FindIntegrationKVPIndex "batchMode"
						if IntegrationKVPs[batchModeIndex][2] == "True" then
						(
							groupBatch = true
						)
					)
				)

				if groupBatch then
				(
					format "BatchName=%\n" edt_jobname.text to:submitInfoFile
				)

				close submitInfoFile
				true
			)
			else
				false
		)
	
		fn CreateJobInfoFile filename strip:0 =
		(
			local JobInfoFile = CreateFile filename
			if (JobInfoFile != undefined) then
			(
				local version = ((maxVersion())[1] / 1000)
				if maxOps.productAppID == #viz then
				(
					format "Application=VIZ\n" to:JobInfoFile
					version = 2001 + version
				)
				else
				(
					format "Application=Max\n" to:JobInfoFile
					if version > 9 then
						version = 1998 + version
				)
				format "Version=%\n" version to:JobInfoFile

				try
				(
					local VersionInfo = dotnetclass "System.Diagnostics.FileVersionInfo"
					local MyMax = VersionInfo.GetVersionInfo (pathConfig.appendPath (pathConfig.GetDir #maxroot) "3dsmax.exe")
					format "SubmittedFromVersion=%\n" MyMax.FileVersion to:JobInfoFile
				)catch()
				
				-- Design edition retired in Max 2016.
				if( DlgMax2DeadlineRollout.getMaxVersionAsInteger() >= 2010 and DlgMax2DeadlineRollout.getMaxVersionAsInteger() < 2016 ) then
					if( maxOps.productID == #3dsMaxDesign ) then
						format "IsMaxDesign=1\n" to:JobInfoFile
					else
						format "IsMaxDesign=0\n" to:JobInfoFile
				else
					format "IsMaxDesign=0\n" to:JobInfoFile

				local build = case (M2DSettings.ForceBuild) of
				(
					1: "None"
					2: "32bit"
					3: "64bit"
				)
				format "Build=%\n" build to:JobInfoFile

				local theCam = viewport.getCamera() --get viewport camera
				if isValidNode theCam then --if it is valid, output it
					format "Camera=%\n" (theCam.name) to:JobInfoFile
				else					
					format "Camera=\n" to:JobInfoFile --if viewport is not a camera, output no camera.

				format "Camera0=\n" to:JobInfoFile
								
				local cameraCount = 1
				local tcID = TargetCamera.classID as string
				local fcID = FreeCamera.classID as string
				for c in cameras do
				(
					-- only want target cameras or free cameras
					id = c.classID as string
					if id == tcID or id == fcID then
					(
						format "Camera%=%\n" cameraCount c.name to:JobInfoFile
						cameraCount = cameraCount + 1
					)
				)
				
				format "PixelAspect=%\n" renderPixelAspect to:JobInfoFile
				format "ImageWidth=%\n" renderWidth to:JobInfoFile
				format "ImageHeight=%\n" renderHeight to:JobInfoFile
				format "ShowVFB=%\n" M2DSettings.ShowVFB to:JobInfoFile
				format "VideoPost=%\n" M2DSettings.VideoPost to:JobInfoFile
				format "ContinueOnError=%\n" M2DSettings.ContinueOnError to:JobInfoFile
				format "LocalRendering=%\n" M2DSettings.LocalRendering to:JobInfoFile
				
				if M2DSettings.PathConfig != "" do
					format "PathConfigFile=%\n" (FileNameFromPath M2DSettings.PathConfig) to:JobInfoFile

				if M2DSettings.RenderPreset != "" do
					format "RenderPresetFile=%\n" (FileNameFromPath M2DSettings.RenderPreset) to:JobInfoFile

				if M2DSettings.PreRenderScript != "" do
					format "PreRenderScript=%\n" (FileNameFromPath M2DSettings.PreRenderScript) to:JobInfoFile

				if M2DSettings.PostRenderScript != "" do
					format "PostRenderScript=%\n" (FileNameFromPath M2DSettings.PostRenderScript) to:JobInfoFile				

				--SCENE STATE
				format "SceneState=%\n" M2DSettings.SceneState to:JobInfoFile
				
				--BATCH RENDER
				format "BatchRender=%\n" M2DSettings.BatchRender to:JobInfoFile
				format "BatchRenderName=%\n" M2DSettings.BatchRenderName to:JobInfoFile

				format "GammaCorrection=%\n" M2DSettings.GammaCorrection to:JobInfoFile
				format "GammaInput=%\n" M2DSettings.GammaInput to:JobInfoFile
				format "GammaOutput=%\n" M2DSettings.GammaOutput to:JobInfoFile
				
				if rendSaveFile and rendOutputFilename != "" then
				(
					format "RenderOutput=%\n" rendOutputFilename to:JobInfoFile
				)
					
				format "Atmospherics=%\n" rendAtmosphere to:JobInfoFile
				format "HiddenGeometry=%\n" rendHidden to:JobInfoFile
				format "Effects=%\n" renderEffects to:JobInfoFile
				format "AreaLights=%\n" rendSimplifyAreaLights to:JobInfoFile
				format "Displacements=%\n" renderDisplacements to:JobInfoFile
				format "TwoSided=%\n" rendForce2Side to:JobInfoFile
				format "VideoColorCheck=%\n" rendColorCheck to:JobInfoFile
				format "SuperBlack=%\n" rendSuperBlack to:JobInfoFile
				format "RenderToFields=%\n" rendFieldRender to:JobInfoFile
				
				if rendFieldRender do
				(
					fieldOrder = getINISetting (getMAXIniFile()) "Renderer" "FieldOrder"
					if fieldOrder != "" then
					(
						if fieldOrder == "1" then
							format "FieldOrder=Odd\n" to:JobInfoFile
						else
							format "FieldOrder=Even\n" to:JobInfoFile

						format "FieldOrder0=Odd\n" to:JobInfoFile
						format "FieldOrder1=Even\n" to:JobInfoFile
					)
				)

				ditherTrueColor = getINISetting (getMAXIniFile()) "Renderer" "DitherTrue"
				if ditherTrueColor != "" do
					format "DitherTrueColor=%\n" ditherTrueColor to:JobInfoFile

				ditherPaletted = getINISetting (getMAXIniFile()) "Renderer" "DitherPaletted"
				if ditherPaletted != "" do
					format "DitherPaletted=%\n" ditherPaletted to:JobInfoFile

				format "UseAdvLighting=%\n" RadiosityPreferences.useAdvancedLighting to:JobInfoFile
				format "ComputeAdvLighting=%\n" RadiosityPreferences.computeAdvancedLighting to:JobInfoFile
				format "SkipRenderedFrames=%\n" skipRenderedFrames to:JobInfoFile

				local imgSeqFile = case (M2DSettings.ImageSequenceFile) of
				(
					1: "none"
					2: ".imsq"
					3: ".ifl"
				)
				format "ImageSequenceFile=%\n" imgSeqFile to:JobInfoFile
				format "ImageSequenceFile0=none\n" to:JobInfoFile
				format "ImageSequenceFile1=.imsq\n" to:JobInfoFile
				format "ImageSequenceFile2=.ifl\n" to:JobInfoFile

				local reMgr = maxOps.GetCurRenderElementMgr()
				if reMgr != undefined do
				(
					if reMgr.GetElementsActive() then
						format "RenderElements=true\n" to:JobInfoFile
					else
						format "RenderElements=false\n" to:JobInfoFile
				)

				if strip > 0 then
				(
					format "StripRendering=1\n" to:JobInfoFile
					format "StripCount=%\n" M2DSettings.SplitStrips to:JobInfoFile
					format "StripOverlap=%\n" M2DSettings.SplitOverlap to:JobInfoFile
					format "StripNumber=%\n" strip to:JobInfoFile
				)
				
				if M2DSettings.DBR then
				(
					local rendererID = DlgMax2DeadlineRollout.getRendererIdString()
					if (rendererID == "mentalray") do
						format "MentalRayDBRJob=true\n" to:JobInfoFile
					if (rendererID == "vray") do
						format "VRayDBRJob=true\n" to:JobInfoFile
					if (rendererID == "vrayrt") do
						format "VRayRtDBRJob=true\n" to:JobInfoFile
						
					local dbrFrame = DlgMax2DeadlineRollout.GetSequenceString #(currentTime)
					format "DBRJobFrame=%\n" dbrFrame to:JobInfoFile
				)
				
				if( not M2DSettings.SubmitScene ) then
					format "SceneFile=%\n" (maxFilePath + maxFileName) to:JobInfoFile

				if not M2DSettings.DBR do
				(
					format "GPUsPerTask=%\n" M2DSettings.GpusPerTask to:JobInfoFile
					format "GPUsSelectDevices=%\n" M2DSettings.GpuDevices to:JobInfoFile
				)
					
				Close JobInfoFile
				true
			)
			else
				false
		)
		
		fn SubmitJob tempMaxFile stripNumber:0 =
		(
			DeadlineSubmissionSuccessful = false
			sld_lastSubmissionState.color = red
			DeadlineSubmissionLastJobID = "failed"
			
			Ui_report ">Job Submission Started..."
			reopenRenderSceneDialog = false
			if renderSceneDialog.isOpen() then
			(
				renderSceneDialog.Close()
				reopenRenderSceneDialog = true
				Ui_report "+Render Dialog Closed."
			)
			
			Ui_report (">Submitting 3dsCmd Render Job to Deadline...")
			
			if ((CreateSubmitInfoFile kDeadlineSubmitInfofile strip:stripNumber) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Submit Info file"
			if ((CreateJobInfoFile kDeadlineJobInfofile strip:stripNumber) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Job Info file"
			
			local arguments = "\"" + kDeadlineSubmitInfofile + "\" \"" + kDeadlineJobInfofile + "\""
			if( M2DSettings.SubmitScene ) then
				arguments = arguments + " \"" + tempMaxFile + "\""
			if( M2DSettings.PathConfig != "" ) then
				arguments = arguments + " \"" + M2DSettings.PathConfig + "\""
			if( M2DSettings.RenderPreset != "" ) then
				arguments = arguments + " \"" + M2DSettings.RenderPreset + "\""
			if( M2DSettings.PreRenderScript != "" ) then
				arguments = arguments + " \"" + M2DSettings.PreRenderScript + "\""
			if( M2DSettings.PostRenderScript != "" ) then
				arguments = arguments + " \"" + M2DSettings.PostRenderScript + "\""

			retcode = waitForCommandToComplete arguments 3600
			
			local resultFile = OpenFile kDeadlineSubmitOutput
			local renderMsg = "No message."
			if (resultFile != undefined) do
			(
				seek resultFile #eof
				fileSize = filepos resultFile
				seek resultFile 0
				renderMsg = readChars resultFile fileSize errorAtEOF:false
				close resultFile
			)
			
			if reopenRenderSceneDialog then
			(
				renderSceneDialog.Open()
				Ui_report "+Restored the Open State of the Render Scene Dialog."
			)

			if retCode == #success then
			(
				DeadlineSubmissionSuccessful = true
				sld_lastSubmissionState.color = green
				DeadlineSubmissionLastJobID = "failed"
				theStringStream = renderMsg as stringStream
				skipToString theStringStream "JobID="
				try(DeadlineSubmissionLastJobID = readline theStringStream)catch()
				close theStringStream 
				("Job submitted successfully.\n\n" + renderMsg)
			)   
			else
				("DEADLINE JOB SUBMISSION:\n\nFailed to submit job.\n\n" + renderMsg)
		)
		
		fn OpenIntegrationWindow =
		(
			global IntegrationKVPs
			
			DlgMax2DeadlineRollout.Ui_report ">Opening Pipeline Tools Window"
			
			local keyValuePairs = #()
			local outFileName = kTempDir + "integration_stdout.txt"
			local deadlineCmd = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommand.exe"

			local scriptPath = DlgMax2DeadlineRollout.GetDeadlineLine( "-getrepositoryfilepath submission/Integration/Main/IntegrationUIStandAlone.py" )
			scriptPath = trimleft scriptPath
			scriptPath = trimright scriptPath
			
			local theArgs = " -executeScript \"" + scriptPath + "\" 3dsCmd Draft Shotgun FTrack 0 > \"" + outFileName + "\""
			local cmdResult = HiddenDOSCommand ("\"\""+deadlineCmd+"\" "+ theArgs + "\"")
			local resultFile = OpenFile outFileName

			if resultFile != undefined then
			(
				try
				(
					while not eof resultFile do
					(
						theLine = readline resultFile
						theLine = trimleft theLine
						theLine = trimright theLine
						if theLine[1] != "(" then
						(
							local tokens = FilterString theLine "="

							if tokens != undefined and tokens.count > 1 then
							(
								local key = tokens[1]
								local value = tokens[2]
								append keyValuePairs #(key, value)
							)
						)
					)
				)
				catch()

				try( close resultFile )catch()
			)

			if keyValuePairs.count > 0 then
			(
				IntegrationKVPs = keyValuePairs
			)
		)			
		---------------------------     
		--USER INTERFACE HANDLERS--     
		---------------------------     
						
		on DlgMax2DeadlineRollout open do
		(
			dn_tabs.enabled = false
			Ui_report (">Building UI...")
			
			local oldRenderDialogState = renderSceneDialog.isOpen()
			if oldRenderDialogState do
			(
				renderSceneDialog.Close()
				Ui_report ("+Render Dialog Closed.")
			)

			for subroll in M2D_Rollouts[1][2] do 
				addSubRollout DlgMax2DeadlineRollout.sub_SubRollout subroll

			for aTab in M2D_Rollouts do
			(
				DlgMax2DeadlineRollout.dn_tabs.TabPages.add aTab[1][1]
				local theItem = DlgMax2DeadlineRollout.dn_tabs.TabPages.Item[DlgMax2DeadlineRollout.dn_tabs.TabPages.count-1]
				theItem.ToolTipText = aTab[1][2]
			)

			GetMaximumPriority()
			spn_priority.range = [0,deadlineMaximumPriority,deadlineMaximumPriority / 2]

			CollectPools()
			ddl_poollist.items = sort deadlinePools
			ddl_secondarypoollist.items = sort deadlineSecondaryPools
			
			CollectGroups()
			ddl_groups.items = deadlineGroups
			
			Ui_report (">Loading UI Presets...")
			
			--initial default settings
			chk_isBlacklist.checked = true
			chk_concurrentTasks.checked = true
			
			LoadUI()
			if getfilenamefile maxfilename != "" do edt_jobname.text = getfilenamefile maxfilename
			
			local frames = case (rendTimeType) of
			(
				1: GetSequenceString #(currentTime)
				2: GetSequenceString ( for t in animationRange.start to animationRange.end by rendNthFrame collect t )
				3: GetSequenceString ( for t in rendStart to rendEnd by rendNthFrame collect t )
				4: rendPickupFrames
			)
			M2DSettings.FrameList = frames
			Ui_report( "rendTimeType: " + (rendTimeType as string) )
			Ui_report( "FRAMES: " + frames )
			
			if oldRenderDialogState do 
			(
				renderSceneDialog.Open() 
				Ui_report "+Restored the Open State of the Render Scene Dialog."
			)
			
			dn_tabs.enabled = true
			Ui_report ("Ready.")
		)
		
		on edt_dept entered txt do SaveUI()
		
		on sld_priority clicked val do 
		(
			job_priority_update ((val * deadlineMaximumPriority) / 100)
			SaveUI()
		)
		
		on spn_priority changed val do 
		(
			job_priority_update val
			SaveUI()
		)
		
		on spn_machineLimit changed val do
		(
			machine_limit_update val
			SaveUI()
		)
				
		on spn_timeout changed val do
		(
			timeout_update val
			SaveUI()
		)

		on spn_concurrentTasks changed val do
		(
			concurrent_tasks_update val
			SaveUI()
		)

		on chk_concurrentTasks changed state do SaveUI()
	
		on ddl_poollist selected item do SaveUI()
		on ddl_secondarypoollist selected item do SaveUI()
		on ddl_groups selected item do SaveUI()
		--on chk_onlypool changed state do SaveUI()
		on chk_closeAfterSubmission changed state do SaveUI()
		
		on chk_autoTimeout changed state do SaveUI()
		on chk_isBlacklist changed state do SaveUI()
		
		on btn_machineList pressed do
		(
			result = GetDeadlineLine( "-selectmachinelist \"" + edt_machineList.text + "\"" )
			if result != "Error getting line" do edt_machineList.text = result
		)
		
		on btn_limitgroups pressed do
		(
			result = GetDeadlineLine( "-selectlimitgroups \"" + edt_limitgroups.text + "\"" )
			if result != "Error getting line" do edt_limitgroups.text = result
		)
		
		on btn_dependencies pressed do
		(
			result = GetDeadlineLine( "-selectdependencies \"" + edt_dependencies.text + "\"" )
			if result != "Error getting line" do edt_dependencies.text = result
		)
		
		on btn_help pressed do ShellLaunch "http://www.thinkboxsoftware.com/support/" ""

		on DlgMax2DeadlineRollout moved pos do SaveUI()
		
		on btn_integration pressed do OpenIntegrationWindow()

		on btn_submit pressed do 
		(
			if not M2DSettings.PerformSanityCheck or (M2DSettings.PerformSanityCheck and MAXCmd2Deadline_PerformSanityCheck()) then 
			(
				lTempMaxFile = ""
				if( M2DSettings.SubmitScene ) then
				(
					lTempMaxFile = kTempDir + maxFileName
					if maxFileName == "" do lTempMaxFile = lTempMaxFile + "untitled.max"
					if (doesFileExist lTempMaxFile) do deleteFile lTempMaxFile
					
					result = SaveMaxFileCopy lTempMaxFile
					if result != undefined do return result
				)
				else
				(
					if maxFileName == "" then
					(
						filename = getMAXSaveFileName()
						if filename == undefined do return ""
						
						lTempMaxFile = filename
					)
					else
						lTempMaxFile = maxFilePath + maxFileName
					saveMaxFile lTempMaxFile
				)
			
				if M2DSettings.SplitRendering then
				(
					Ui_report "-----------------------------------------------------------------------"
					for i = 1 to M2DSettings.SplitStrips do
					(
						Ui_report ("Submitting split job " + (i as string) + " of " + (M2DSettings.SplitStrips as string))
						SubmitJob lTempMaxFile stripNumber:i
						AnimateLastSubmissionState()
					)
					sld_lastSubmissionState.value = 100
					Ui_report "-----------------------------------------------------------------------"
					Ui_report ("Ready.")
					if chk_closeAfterSubmission.checked and DeadlineSubmissionSuccessful == true do 
					(
						destroyDialog DlgMax2DeadlineRollout 
						MessageBox theMessage title:"Submit To Deadline"
					)   
				)
				else
				(
					theMessage = SubmitJob lTempMaxFile
					sld_lastSubmissionState.value = 100
					Ui_report "-----------------------------------------------------------------------"
					Ui_report theMessage
					Ui_report "-----------------------------------------------------------------------"
					Ui_report ("Ready.")
					if chk_closeAfterSubmission.checked and DeadlineSubmissionSuccessful == true do 
					(
						destroyDialog DlgMax2DeadlineRollout 
						MessageBox theMessage title:"Submit To Deadline"
					)
				)
				
				if( M2DSettings.SubmitScene ) then
					deleteFile lTempMaxFile
			)
		)
				
		on btn_renderdialog pressed do
		(
			if renderSceneDialog.isOpen() then
				renderSceneDialog.close()
			else
				renderSceneDialog.open()
		)

		on btn_openMonitor pressed do
		(
			local deadlineMonitor = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinemonitor.exe"
			shellLaunch deadlineMonitor ""
		)
	)
	

	rollout M2D_MaxRollout "Max Settings"
	(
		edittext edt_frames "Frame List" fieldwidth:306 offset:[-4,0] align:#right
		label lbl_chunkSize "Group Size" align:#left offset:[12,3] across:4
		spinner spn_chunkSize range:[1,1000,1] type:#integer align:#right fieldwidth:122 offset:[10,3]
		label lbl_builds "Force Build" align:#left offset:[38,4]
		dropdownlist ddl_builds items:#("None", "32bit", "64bit") width:90 align:#right offset:[-3,0]
		
		checkbox chk_showvfb "Show Virtual Frame Buffer" align:#left offset:[67,0] across:2
		checkbox chk_videopost "Apply VideoPost To Scene" offset:[39,0]
		
		checkbox chk_continueOnError "Continue On Errors" align:#left offset:[67,0] across:2
		checkbox chk_submitScene "Submit Scene File With Job" offset:[39,0] checked:true
		
		checkbox chk_localRendering "Enable Local Rendering" align:#left offset:[67,0]
		
		checkbox chk_gammaCorrection "Gamma Correction" offset:[67,0] across:5
		label lbl_gammaInput "Input" align:#left offset:[116,3] across:4
		spinner spn_gammaInput range:[0.01,5.00,1.0] type:#float align:#right fieldwidth:35 offset:[44,1]
		label lbl_gammaOutput "Output" align:#left offset:[60,3]
		spinner spn_gammaOutput range:[0.01,5.00,1.0] type:#float align:#right fieldwidth:35 offset:[0,1]
		
		checkbox chk_splitRendering "Split Rendering" offset:[67,0] across:5
		label lbl_splits "Strips" align:#left offset:[116,3] across:4
		spinner spn_splits range:[2,1000,2] type:#integer align:#right fieldwidth:35 offset:[44,1]
		label lbl_overlap "Overlap" align:#left offset:[60,3]
		spinner spn_overlap range:[0,5000,0] type:#integer align:#right fieldwidth:35 offset:[0,1]
		
		checkbox chk_dbr "VRay/Mental Ray DBR (off-load)" offset:[67,0] across:3
		label lbl_dbrServers "Slaves" align:#left offset:[160,3] across:4
		spinner spn_dbrServers range:[1,1000,5] type:#integer align:#right fieldwidth:35 offset:[1,1]
		
		checkbox chk_performSanityCheck "Run Sanity Check On Submission" checked:false offset:[67,0] across:2
		button btn_runSanityCheck "Run Now!" align:#right width:90 offset:[0,-3] tooltip:"Run Sanity Check WITHOUT submitting the scene to Deadline."		
		
		on M2D_MaxRollout open do
		(
			DlgMax2DeadlineRollout.Ui_report ">Opening Max Settings Rollout"
			if (MaxVersion())[1] < 9000 then
			(
				M2DSettings.SplitRendering = false
				chk_splitRendering.enabled = false
				
				M2DSettings.PerformSanityCheck = false
				chk_performSanityCheck.enabled = false
				btn_runSanityCheck.enabled = false
			)
			
			local enableDBR = true
			local rendererID = DlgMax2DeadlineRollout.getRendererIdString()
			if (rendererID == "mentalray") or (rendererID == "vray") or (rendererID == "vrayrt") then
			(
				if (rendererID == "mentalray") and not (renderers.current.DistributedEnable) do
					enableDBR = false
				if (rendererID == "vray") and not (renderers.current.system_distributedRender) do
					enableDBR = false
				if (rendererID == "vrayrt") and not (renderers.current.distributed_rendering) do
					enableDBR = false
			)
			else
				enableDBR = false
			
			if not enableDBR do
			(
				M2DSettings.DBR = false
				chk_dbr.enabled = false
			)
			
			edt_frames.text = M2DSettings.FrameList
			
			spn_chunkSize.value = M2DSettings.ChunkSize
			ddl_builds.selection = M2DSettings.ForceBuild
			
			chk_showvfb.checked = M2DSettings.ShowVFB
			chk_videopost.checked = M2DSettings.VideoPost
			chk_continueOnError.checked = M2DSettings.ContinueOnError
			chk_submitScene.checked = M2DSettings.SubmitScene
			chk_localRendering.checked = M2DSettings.LocalRendering
			
			chk_gammaCorrection.checked = M2DSettings.GammaCorrection
			lbl_gammaInput.enabled = M2DSettings.GammaCorrection
			spn_gammaInput.enabled = M2DSettings.GammaCorrection
			spn_gammaInput.value = M2DSettings.GammaInput
			lbl_gammaOutput.enabled = M2DSettings.GammaCorrection
			spn_gammaOutput.enabled = M2DSettings.GammaCorrection
			spn_gammaOutput.value = M2DSettings.GammaOutput
			
			chk_splitRendering.checked = M2DSettings.SplitRendering
			lbl_splits.enabled = M2DSettings.SplitRendering
			spn_splits.enabled = M2DSettings.SplitRendering
			spn_splits.value = M2DSettings.SplitStrips
			lbl_overlap.enabled = M2DSettings.SplitRendering
			spn_overlap.enabled = M2DSettings.SplitRendering
			spn_overlap.value = M2DSettings.SplitOverlap
			
			chk_dbr.checked = M2DSettings.DBR
			lbl_dbrServers.enabled = M2DSettings.DBR
			spn_dbrServers.value = M2DSettings.DBRServers
			spn_dbrServers.enabled = M2DSettings.DBR
			
			chk_performSanityCheck.checked = M2DSettings.PerformSanityCheck
		)

		on edt_frames changed text do M2DSettings.FrameList = text
		on ddl_builds selected item do M2DSettings.ForceBuild = item
		on chk_showvfb changed state do M2DSettings.ShowVFB = state
		on chk_videopost changed state do M2DSettings.VideoPost = state
		
		on spn_chunkSize changed val do
		(
			M2DSettings.ChunkSize = val
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on chk_continueOnError changed state do
		(
			M2DSettings.ContinueOnError = state
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on chk_submitScene changed state do 
		(
			M2DSettings.SubmitScene = state
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on chk_localRendering changed state do
		(
			M2DSettings.LocalRendering = state
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on spn_gammaInput changed val do
		(
			M2DSettings.GammaInput = val
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on spn_gammaOutput changed val do 
		(
			M2DSettings.GammaOutput = val
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on spn_splits changed val do 
		(
			M2DSettings.SplitStrips = val
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on spn_overlap changed val do 
		(
			M2DSettings.SplitOverlap = val
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on spn_dbrServers changed val do
		(
			M2DSettings.DBRServers = val
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on chk_performSanityCheck changed state do 
		(
			M2DSettings.PerformSanityCheck = state
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on btn_runSanityCheck pressed do 
		(
			MAXCmd2Deadline_PerformSanityCheck()
		)
		
		on chk_gammaCorrection changed state do
		(
			M2DSettings.GammaCorrection = state
		
			lbl_gammaInput.enabled = M2DSettings.GammaCorrection
			spn_gammaInput.enabled = M2DSettings.GammaCorrection
			lbl_gammaOutput.enabled = M2DSettings.GammaCorrection
			spn_gammaOutput.enabled = M2DSettings.GammaCorrection
			
			DlgMax2DeadlineRollout.SaveUI()
		)
		
		on chk_splitRendering changed state do
		(
			M2DSettings.SplitRendering = state
			
			lbl_splits.enabled = state
			spn_splits.enabled = state
			lbl_overlap.enabled = state
			spn_overlap.enabled = state
		)
		
		on chk_dbr changed state do
		(
			M2DSettings.DBR = state
			
			edt_frames.enabled = (not state)
			lbl_dbrServers.enabled = state
			spn_dbrServers.enabled = state
		)
	)

	rollout M2D_GpuRollout "GPU Affinity Overrides"
	(
		label lbl_gpusPerTask "GPUs Per Task" align:#left offset:[17,3] across:2
		spinner spn_gpusPerTask range:[0,15,0] type:#integer align:#left fieldwidth:122 offset:[-100,3]
		edittext edt_gpuDevices "Select GPU Devices" fieldwidth:286 offset:[-6,0] align:#left

		on M2D_GpuRollout open do
		(
			DlgMax2DeadlineRollout.Ui_report ">Opening GPU Affinity Overrides Rollout"
			spn_gpusPerTask.value = M2DSettings.GpusPerTask
			edt_gpuDevices.text = M2DSettings.GpuDevices
			lbl_gpusPerTask.enabled = (edt_gpuDevices.text == "")
			spn_gpusPerTask.enabled = (edt_gpuDevices.text == "")
			edt_gpuDevices.enabled = (spn_gpusPerTask.value == 0)
		)

		on spn_gpusPerTask changed val do
		(
			M2DSettings.GpusPerTask = val
			edt_gpuDevices.enabled = (val == 0)
		)

		on edt_gpuDevices changed text do
		(
			M2DSettings.GpuDevices = text
			lbl_gpusPerTask.enabled = (text == "")
			spn_gpusPerTask.enabled = (text == "")
		)
	)

	rollout M2D_AdvancedRollout "Advanced Settings"
	(
		edittext edt_path_config "Path Config File" fieldwidth:256 align:#left offset:[11,0] across:2
		button btn_path_config "..." width:20 align:#left offset:[165,-2] tooltip:"Click to select an alternate path configuration file."

		edittext edt_render_preset "Render Preset File" fieldwidth:256 align:#left offset:[-2,0] across:2
		button btn_render_preset "..." width:20 align:#left offset:[165,-2] tooltip:"Click to select a render preset settings file."

		edittext edt_preRenderScript "Pre-Render Script" fieldwidth:256 align:#left offset:[1,0] across:2
		button btn_preRenderScript "..." width:20 align:#left offset:[165,-2] tooltip:"Click to select a pre-render maxscript file."

		edittext edt_postRenderScript "Post-Render Script" fieldwidth:256 align:#left offset:[-4,0] across:2
		button btn_postRenderScript "..." width:20 align:#left offset:[165,-2] tooltip:"Click to select a post-render maxscript file."

		label lbl_sceneState "Scene State" align:#left offset:[28,3] across:2 tooltip:"Loads the specified scene state file before rendering the image."
		dropdownList ddl_sceneState "" align:#left offset:[-99,0] width:285
		
		checkbox chk_batchRender "Batch Render (ALL Views)" align:#left offset:[90,0] across:1 tooltip:"Renders all enabled tasks in the Batch Render dialog."

		label lbl_batchRenderName "Batch Render Name" align:#left offset:[-10,3] across:2 tooltip:"Renders batch renders in the file named batch-render-name."
		dropdownList ddl_batchRenderName "" align:#left offset:[-99,0] width:285

		checkbox chk_stillFrame "Remove Padding (Single Frame Only)" align:#left offset:[90,0] across:1 tooltip:"Indicates that this is a still-frame render; no frame suffix will be added."

		label lbl_imageSeqFile "Image Seq. Creation" align:#left offset:[-12,3] across:2 tooltip:"Image-sequence file creation: 0=none; 1=.imsq; 2=.ifl."
		dropdownlist ddl_imageSeqFile items:#("none", ".imsq", ".ifl") align:#left offset:[-99,0] width:80

		on M2D_AdvancedRollout open do
		(
			DlgMax2DeadlineRollout.Ui_report ">Opening Advanced Settings Rollout"
			edt_path_config.text = M2DSettings.PathConfig
			edt_render_preset.text = M2DSettings.RenderPreset
			edt_preRenderScript.text = M2DSettings.PreRenderScript
			edt_postRenderScript.text = M2DSettings.PostRenderScript
			
			sceneStateArray = #("")
			for i = 1 to sceneStateMgr.GetCount() do
				append sceneStateArray (sceneStateMgr.GetSceneState i)
			ddl_sceneState.items = sceneStateArray
			M2DSettings.SceneState = ddl_sceneState.selected

			chk_batchRender.checked = M2DSettings.BatchRender

			numViews = batchRenderMgr.numViews
			viewNames =  (for i = 1 to numViews where (batchRenderMgr.getView i).enabled collect (batchRenderMgr.getView i).name)
			ddl_batchRenderName.items = (join #("") viewNames)
			M2DSettings.BatchRenderName = ddl_batchRenderName.selected

			chk_stillFrame.checked = M2DSettings.StillFrame
			ddl_imageSeqFile.selection = M2DSettings.ImageSequenceFile

			chk_batchRender.enabled = ddl_batchRenderName.selection == 1

			lbl_batchRenderName.enabled = not chk_batchRender.state
			ddl_batchRenderName.enabled = not chk_batchRender.state
		)

		on edt_path_config entered txt do 
		(
			M2DSettings.PathConfig = txt
			DlgMax2DeadlineRollout.SaveUI()
		)

		on edt_render_preset entered txt do
		(
			M2DSettings.RenderPreset = txt
			DlgMax2DeadlineRollout.SaveUI()
		)

		on edt_preRenderScript entered txt do
		(
			M2DSettings.PreRenderScript = txt
			DlgMax2DeadlineRollout.SaveUI()
		)

		on edt_postRenderScript entered txt do
		(
			M2DSettings.PostRenderScript = txt
			DlgMax2DeadlineRollout.SaveUI()
		)

		on btn_path_config pressed do
		(
			pathConfigFile = getOpenFileName caption:"Select a Path Configuration File." types:"Path Configuration File (*.mxp)|*.mxp|All Files (*.*)|*.*|"
			if pathConfigFile != undefined then
			(
				M2DSettings.PathConfig = pathConfigFile
				edt_path_config.text = M2DSettings.PathConfig
				DlgMax2DeadlineRollout.SaveUI()
			)
		)

		on btn_render_preset pressed do
		(
			renderPresetFile = getOpenFileName caption:"Select a Render Preset Settings File." types:"Render Preset Settings File (*.rps)|*.rps|All Files (*.*)|*.*|"
			if renderPresetFile != undefined then
			(
				M2DSettings.RenderPreset = renderPresetFile
				edt_render_preset.text = M2DSettings.RenderPreset
				DlgMax2DeadlineRollout.SaveUI()
			)
		)

		on btn_preRenderScript pressed do
		(
			preRenderScriptFile = getOpenFileName caption:"Select a Pre-Render MAXScript File." types:"MAXScript File (*.ms)|*.ms|All Files (*.*)|*.*|"
			if preRenderScriptFile != undefined then
			(
				M2DSettings.PreRenderScript = preRenderScriptFile
				edt_preRenderScript.text = M2DSettings.PreRenderScript
				DlgMax2DeadlineRollout.SaveUI()
			)
		)

		on btn_postRenderScript pressed do
		(
			postRenderScriptFile = getOpenFileName caption:"Select a Post-Render MAXScript File." types:"MAXScript File (*.ms)|*.ms|All Files (*.*)|*.*|"
			if postRenderScriptFile != undefined then
			(
				M2DSettings.PostRenderScript = postRenderScriptFile
				edt_postRenderScript.text = M2DSettings.PostRenderScript
				DlgMax2DeadlineRollout.SaveUI()
			)
		)

		on ddl_sceneState selected item do
		(
			M2DSettings.SceneState = ddl_sceneState.items[item]
		)
		
		on chk_batchRender changed state do
		(
			M2DSettings.BatchRender = state
			DlgMax2DeadlineRollout.SaveUI()
			lbl_batchRenderName.enabled = not state
			ddl_batchRenderName.enabled = not state
		)

		on ddl_batchRenderName selected item do
		(
			M2DSettings.BatchRenderName = ddl_batchRenderName.items[item]
			if item > 1 then
				chk_batchRender.enabled = False
			else
				chk_batchRender.enabled = True
		)

		on chk_stillFrame changed state do
		(
			M2DSettings.StillFrame = state
			DlgMax2DeadlineRollout.SaveUI()
		)

		on ddl_imageSeqFile selected item do 
		(
			M2DSettings.ImageSequenceFile = item
			DlgMax2DeadlineRollout.SaveUI()
		)
	)

	M2D_Rollouts = #(
		#(#("Max","Max Settings including Split Rendering, DBR off-load and GPU rollouts"),#(M2D_MaxRollout, M2D_GpuRollout)),
		#(#("Advanced","Advanced Rendering Options"),#(M2D_AdvancedRollout))
	)
	
	local winPos = [10, 10]
	
	str = GetIniSetting deadlineIniFile "SubmitDialog" "PositionX"
	if str != "" do winPos.x = str as integer 

	str = GetIniSetting deadlineIniFile "SubmitDialog" "PositionY"
	if str != "" do winPos.y = str as integer

	if winPos.x > sysinfo.DesktopSize.x - 420 do winPos.x = sysinfo.DesktopSize.x - 420 --move back to screen if dual monitor changed to single monitor or if outside the desktop
	if winPos.y > sysinfo.DesktopSize.y - 100 do winPos.y = sysinfo.DesktopSize.y - 700 --if minimized, fit back to screen
	if winPos.x < 0 do winPos.x = 0 
	if winPos.y < 0 do winPos.y = 0 
	
	CreateDialog DlgMax2DeadlineRollout pos:winPos style:#(#style_titlebar, #style_border, #style_sysmenu, #style_minimizebox)

)

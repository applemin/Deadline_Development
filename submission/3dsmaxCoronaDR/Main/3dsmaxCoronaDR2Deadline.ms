macroScript MaxCoronaDR2DeadlineMain category:"Thinkbox" tooltip:"Internal! Use Deadline>MaxCoronaDR2DeadlineMain!"
(
	global DlgMaxCoronaDR2DeadlineRollout
	try (DestroyDialog DlgMaxCoronaDR2DeadlineRollout) catch()
	
	local deadlineMaximumPriority = 100
	local deadlinePools = #()
	local deadlineSecondaryPools = #()
	local deadlineGroups = #()
	local deadlineSlaveNames = #()
	
    local revertDeadlineCoronaDistributedEnabled = false
    local revertDRSlaveAddresses = #()
    local revertDRSlaveResolvedNames = #()

	local DeadlineSubmissionSuccessful = false
	global DeadlineSubmissionLastJobID = "failed"
	local DeadlineJobMaxServers = 10
	
	local kDeadlineSubmitOutput = sysInfo.tempdir + "submitOutput.txt"
	local kDeadlineSubmitExitCode = sysInfo.tempdir + "submitExitCode.txt"
	
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

	deadlineIniFile = GetDir #plugcfg + "\\MaxCoronaDR2Deadline.ini"

	struct CoronaDR_ColorPaletteStruct 
	(
		blueColor, redColor, greenColor, grayColor, lightGrayColor, lightBlueColor, highlightBgColor, textColor, maxBgColor, blackColor
	)
	global CoronaDR_ColorPalette = CoronaDR_ColorPaletteStruct()
	
	fn defineDotNetColors =
	(
		CoronaDR_ColorPalette.textColor = ( ((colorman.getcolor #text) as color)*255)
		CoronaDR_ColorPalette.maxBgColor = (((colorman.getcolor #window)) as color)*255
		CoronaDR_ColorPalette.blackColor = (dotNetClass "System.Drawing.Color").fromARGB CoronaDR_ColorPalette.textColor.r CoronaDR_ColorPalette.textColor.g CoronaDR_ColorPalette.textColor.b
		if CoronaDR_ColorPalette.maxBgColor.v >= 160 then
		(
			CoronaDR_ColorPalette.redColor = (dotNetClass "System.Drawing.Color").fromARGB 192 0 0
			CoronaDR_ColorPalette.greenColor = (dotNetClass "System.Drawing.Color").fromARGB 0 128 0
			CoronaDR_ColorPalette.blueColor = (dotNetClass "System.Drawing.Color").fromARGB 0 0 128
			CoronaDR_ColorPalette.lightBlueColor = (dotNetClass "System.Drawing.Color").fromARGB 90 128 160
			CoronaDR_ColorPalette.grayColor = (dotNetClass "System.Drawing.Color").fromARGB 128 128 128
			CoronaDR_ColorPalette.lightGrayColor = (dotNetClass "System.Drawing.Color").fromARGB 160 160 160
			CoronaDR_ColorPalette.highlightBgColor = (dotNetClass "System.Drawing.Color").fromARGB 180 190 200
		)
		else
		(
			CoronaDR_ColorPalette.redColor = (dotNetClass "System.Drawing.Color").fromARGB 255 128 128
			CoronaDR_ColorPalette.greenColor = (dotNetClass "System.Drawing.Color").fromARGB 128 255 128
			CoronaDR_ColorPalette.blueColor = (dotNetClass "System.Drawing.Color").fromARGB 170 200 255
			CoronaDR_ColorPalette.lightBlueColor = (dotNetClass "System.Drawing.Color").fromARGB 128 160 255
			CoronaDR_ColorPalette.grayColor = (dotNetClass "System.Drawing.Color").fromARGB 192 192 192
			CoronaDR_ColorPalette.lightGrayColor = (dotNetClass "System.Drawing.Color").fromARGB 160 160 160
			CoronaDR_ColorPalette.highlightBgColor = (dotNetClass "System.Drawing.Color").fromARGB 20 40 60
		)				
	)		
	defineDotNetColors()

	-----------------------------------------------------------------------------------------------
	--MAIN ROLLOUT
	-----------------------------------------------------------------------------------------------

	rollout DlgMaxCoronaDR2DeadlineRollout "Setup Corona DR With Deadline" width:410 height:710
	(
		group "Job Description" 
		(
			edittext edt_jobname "Job Name" fieldwidth:310 align:#right 

			edittext edt_comment " Comment" fieldwidth:310 align:#right 
						
			edittext edt_dept "Department" fieldwidth:310 align:#right
		)	

		group "Job Scheduling" 
		(
			label lbl_pools "Pool" align:#left offset:[48,4] across:2
			dropdownList ddl_poollist "" width:310 align:#center offset:[-61,0]
			
			label lbl_secondarypools "Secondary Pool" align:#left offset:[-4,4] across:2
			dropdownList ddl_secondarypoollist "" width:310 align:#center offset:[-61,0]

			label lbl_groups "Group" align:#left offset:[41,4] across:2
			dropdownList ddl_groups "" width:310 align:#center offset:[-61,0]

			label lbl_priority "Priority" align:#left offset:[36,2] across:3
			spinner spn_priority "" type:#integer fieldwidth:122 offset:[-53,1]
			checkbox chk_isBlacklist "Machine List Is A Blacklist" offset:[-25,1]

			label lbl_taskTimeout "Task Timeout" align:#left offset:[6,2] across:3
			spinner spn_taskTimeout "" type:#integer fieldwidth:122 align:#left offset:[-58,1]
			checkbox chk_isInterruptible "Job Is Interruptible" offset:[-25,1]
            
			edittext edt_limitgroups "Limits" fieldwidth:280 align:#left offset:[42,0] across:2
			button btn_limitgroups "..." width:20 align:#left offset:[165,-2] tooltip:"Click to select Limits."
			
			edittext edt_machineList "Machine List" fieldwidth:280 align:#left offset:[10,0] across:2
			button btn_machineList "..." width:20 align:#left offset:[165,-2] tooltip:"Click to select a Machine List."
		)

		group "Corona DR Options"
		(
			label lbl_maxServers "Maximum Servers" align:#left offset:[12,2] across:2
			spinner spn_maxServers "" type:#integer fieldwidth:122 range:[1,100,10] align:#right offset:[-153,1] tooltip:"This is the max. number of Deadline Slaves to be reserved to assist in computing this Corona DR session."

			checkbox chk_useIpAddress "Use Server IP Address Instead of Host Name" offset:[101,1] tooltip:"When enabled, IP address is used instead of DNS resolved Host Name. Use this option when you have no DNS server running on your network."
			checkbox chk_autoUpdate "Automatically Update Server List" offset:[101,1] tooltip:"When enabled, the Active Server List is automatically updated."
			checkbox chk_autoComplete "Complete Job after Render" offset:[101,1] tooltip:"When enabled, the Deadline submitted job will automatically be marked as completed when the current DR session has finished."
            
			edittext edt_jobId "Corona Job ID" fieldwidth:284 align:#left offset:[28,0]
			edittext edt_jobStatus "Corona Job Status" fieldwidth:284 align:#left offset:[8,0]
			
			label lbl_activeServers "Active Servers" across:2 align:#left offset:[25,0]
			multilistbox lbx_activeServers height:9 width:284 align:#right offset:[1,0]
			
			timer tmr_jobUpdate "Job Update Timer" interval:5000 active:false
		)
		
		button btn_startJob "Reserve Servers" width:95 height:30 across:4 offset:[-7,0] tooltip:"Submits a Corona DR job to Deadline to reserve servers..."
		button btn_updateServers "Update Servers" width:95 height:30 offset:[-3,0] tooltip:"Manually update the active server list and job status..."
		button btn_startRender "Start Render" width:95 height:30 offset:[2,0] tooltip:"Starts the Corona DR render..."
		button btn_endJob "Release Servers" width:95 height:30 offset:[7,0] tooltip:"Completes the current Corona DR job..."

		dotNetControl dnc_report "ListView" width:396 height:90 align:#center offset:[0,0]

		fn initReportWindow =
		(
			local lv = dnc_report
			local layout_def = #(#("Time Stamp",40), #("Message",200))
			lv.Clear()
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB CoronaDR_ColorPalette.maxBgColor.r CoronaDR_ColorPalette.maxBgColor.g CoronaDR_ColorPalette.maxBgColor.b
			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.gridLines = false
			lv.fullRowSelect = true
			lv.checkboxes = false
			lv.hideSelection = true
			lv.HeaderStyle = lv.HeaderStyle.None
			for i in layout_def do lv.Columns.add i[1] i[2]
		)

		fn getTimeString =
		(
			theTime = localtime
			substring theTime ((findstring theTime " ")+1) -1
		)
		
		fn Ui_report txt AddTimeStamp:true =
		(
			try
			(
				local strStream = txt as StringStream
				local theRange = #()
				local blackColor = (dotNetClass "System.Drawing.Color").fromARGB CoronaDR_ColorPalette.textColor.r CoronaDR_ColorPalette.textColor.g CoronaDR_ColorPalette.textColor.b
				if CoronaDR_ColorPalette.maxBgColor.v >= 160 then
				(
					local redColor = (dotNetClass "System.Drawing.Color").fromARGB 192 0 0
					local greenColor = (dotNetClass "System.Drawing.Color").fromARGB 0 92 0
					local blueColor = (dotNetClass "System.Drawing.Color").fromARGB 0 0 128
				)
				else
				(
					local redColor = (dotNetClass "System.Drawing.Color").fromARGB 255 128 128
					local greenColor = (dotNetClass "System.Drawing.Color").fromARGB 128 255 128
					local blueColor = (dotNetClass "System.Drawing.Color").fromARGB 192 220 255
				)
				
				local lineCount = 0
				local foreColor = blackColor					
				while not eof strStream do
				(
					--append temp (readline strStream)
					local aLine = readLine strStream
					if aLine == "" do continue
					lineCount +=1
					if lineCount == 1 do
						case of
						(
							default: (
											foreColor = blackColor
							)
							(matchPattern aLine pattern:"?--*"): (
								foreColor = redColor
							)
							(matchPattern aLine pattern:"--*"): (
								foreColor = redColor
							)							
							(matchPattern aLine pattern:"?+*"): (
								foreColor = greenColor
							)
							(matchPattern aLine pattern:"+*"): (
								foreColor = greenColor
							)							
							(matchPattern aLine pattern:">*"): (
								foreColor = blueColor
							)	
							(matchPattern aLine pattern:"==*"): (
								foreColor = blueColor
							)
						)
					local li = dotNetObject "System.Windows.Forms.ListViewItem" (if AddTimeStamp then getTimeString() else "") 
					li.forecolor = foreColor
					local subLi = li.SubItems.add aLine
					append theRange li
				)
				dnc_report.Items.AddRange theRange
				dnc_report.Items.Item[dnc_report.Items.Count-1].EnsureVisible()
				local autoRes = dotNetClass "System.Windows.Forms.ColumnHeaderAutoResizeStyle"
				dnc_report.AutoResizeColumns autoRes.ColumnContent
				try(windows.processPostedMessages())catch()
			)catch()
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

		--Save the local DR settings so they can be restored at the end of Deadline DR interactive session
		fn StoreDRSettings =
		(
			if getRendererIdString() == "corona" do
			(
				revertDRSlaveAddresses = renderers.current.dr_slaveAddresses
				revertDRSlaveResolvedNames = renderers.current.dr_slaveResolvedNames
			)
		)

		--Restore the local DR settings at the end of Deadline DR interactive session
		fn RestoreDRSettings =
		(
			if getRendererIdString() == "corona" do
			(
				renderers.current.dr_slaveAddresses = revertDRSlaveAddresses
				renderers.current.dr_slaveResolvedNames = revertDRSlaveResolvedNames
			)
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
		
		fn CollectRenderingSlaves =
		(
			deadlineSlaveNames = #()
			deleteFile kDeadlineSubmitExitCode
			local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
			ShellLaunch deadlineCommandBG ("-outputfiles \"" + kDeadlineSubmitOutput + "\" \"" + kDeadlineSubmitExitCode + "\" -GetMachinesRenderingJob \"" + DeadlineSubmissionLastJobID + "\" \"" + (chk_useIpAddress.state as string) + "\"")
			
			startTimeStamp = timestamp()
			ready = false
			while not ready do
			(
				sleep 0.25
				if doesFileExist kDeadlineSubmitExitCode then
					return ReadFileIntoArray kDeadlineSubmitOutput deadlineSlaveNames
				if timestamp() - startTimeStamp > 10000 then 
					return #commandFailed
			)
		)

		fn CheckMaxServers = 
		(
			if DeadlineJobMaxServers != spn_maxServers.value do
			(
				Ui_report ("+Updating Max. Servers to " + (spn_maxServers.value as string))

				deleteFile kDeadlineSubmitExitCode
				local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
				ShellLaunch deadlineCommandBG ("-outputfiles \"" + kDeadlineSubmitOutput + "\" \"" + kDeadlineSubmitExitCode + "\" -SetJobFrameRange \"" + DeadlineSubmissionLastJobID + "\" \"0-" + ((spn_maxServers.value-1) as string) + "\" \"" + (1 as string) + "\"" )
				
				startTimeStamp = timestamp()
				ready = false
				while not ready do
				(
					sleep 0.25
					if doesFileExist kDeadlineSubmitExitCode then
					(
						DeadlineJobMaxServers = spn_maxServers.value
						return #success
					)
					if timestamp() - startTimeStamp > 10000 then 
						return #commandFailed
				)
			)
		)
		
		fn GetJobStatus =
		(
			jobInfo = #()
			deleteFile kDeadlineSubmitExitCode
			local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
			ShellLaunch deadlineCommandBG ("-outputfiles \"" + kDeadlineSubmitOutput + "\" \"" + kDeadlineSubmitExitCode + "\" -getjob \"" + DeadlineSubmissionLastJobID + "\" \"false\"")
			
			startTimeStamp = timestamp()
			ready = false
			while not ready do
			(
				sleep 0.25
				if doesFileExist kDeadlineSubmitExitCode then
				(
					result = ReadFileIntoArray kDeadlineSubmitOutput jobInfo
					if result == #success then
					(
						for i = 1 to jobInfo.count do
						(
							if (findString jobInfo[i] "Status=") == 1 then
								return substring jobInfo[i] 8 -1
						)
						
						return "Deleted"
					)
					else
						return #commandFailed
				)
				
				if timestamp() - startTimeStamp > 10000 then 
					return #commandFailed
			)
		)
		
		fn CompleteJob =
		(
			if DeadlineSubmissionLastJobID != "failed" do
			(
                if revertDeadlineCoronaDistributedEnabled do
                (
                	if getRendererIdString() == "corona" do
                    	renderers.current.dr_enable = false
                )

				--restore the artists DR settings on their workstation
				RestoreDRSettings()

				deleteFile kDeadlineSubmitExitCode
				local deadlineCommandBG = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
				ShellLaunch deadlineCommandBG ("-outputfiles \"" + kDeadlineSubmitOutput + "\" \"" + kDeadlineSubmitExitCode + "\" -completejob \"" + DeadlineSubmissionLastJobID + "\"" )
				
				DeadlineSubmissionLastJobID = "failed"
				
				startTimeStamp = timestamp()
				ready = false
				while not ready do
				(
					sleep 0.25
					if doesFileExist kDeadlineSubmitExitCode then
						return #success
					if timestamp() - startTimeStamp > 10000 then 
						return #commandFailed
				)
			)
			
			return #success
		)
		
		fn ResetServerControls =
		(
			lbx_activeServers.items = #()
			edt_jobId.text = ""
			edt_jobStatus.text = ""
			
			btn_startJob.enabled = true
			btn_updateServers.enabled = false
			btn_startRender.enabled = false
			btn_endJob.enabled = false
			edt_jobId.enabled = false
			edt_jobStatus.enabled = false
			lbl_activeServers.enabled = false
			lbx_activeServers.enabled = false
			tmr_jobUpdate.active = false
		)
				
		fn SaveUI =
		(
			winPos = GetDialogPos DlgMaxCoronaDR2DeadlineRollout
			SetIniSetting deadlineIniFile "SubmitDialog" "PositionX" ((winPos.x as integer) as string)
			SetIniSetting deadlineIniFile "SubmitDialog" "PositionY" ((winPos.y as integer) as string)
			
			SetIniSetting deadlineIniFile "JobSettings" "Department" (edt_dept.text)
			SetIniSetting deadlineIniFile "JobSettings" "Group" (ddl_groups.selected)
			
			SetIniSetting deadlineIniFile "JobSettings" "Priority" (spn_priority.value as string)
			SetIniSetting deadlineIniFile "JobSettings" "Pool" (ddl_poollist.selected)
			SetIniSetting deadlineIniFile "JobSettings" "SecondaryPool" (ddl_secondarypoollist.selected)
			
			SetIniSetting deadlineIniFile "JobSettings" "LimitGroups" (edt_limitgroups.text)
			SetIniSetting deadlineIniFile "JobSettings" "MachineList" (edt_machineList.text)
			SetIniSetting deadlineIniFile "JobSettings" "IsBlacklist" (chk_isBlacklist.state as string)
			SetIniSetting deadlineIniFile "JobSettings" "IsInterruptible" (chk_isInterruptible.state as string)
			
			SetIniSetting deadlineIniFile "JobSettings" "MaxServers" (spn_maxServers.value as string)
			SetIniSetting deadlineIniFile "JobSettings" "UseIpAddress" (chk_useIpAddress.state as string)
			SetIniSetting deadlineIniFile "JobSettings" "AutoUpdate" (chk_autoUpdate.state as string)
            SetIniSetting deadlineIniFile "JobSettings" "AutoComplete" (chk_autoComplete.state as string)
		)

		fn fixBackSlashes txt =
		(
			for i = 1 to txt.count do
				if substring txt i 1 == "\\" do txt[i] = "/"
			txt
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
		
		fn jobPriorityUpdate val =
		(
			if val <= deadlineMaximumPriority do
			(
				spn_priority.value = val
			)
		)
		
		fn LoadUI =
		(	
			edt_dept.text = getIniSetting deadlineIniFile "JobSettings" "Department"
			
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
				jobPriorityUpdate currPriority
			)
			else
			(
				defPriority = deadlineMaximumPriority / 2
				jobPriorityUpdate defPriority
			)
			
			val = getIniSetting deadlineIniFile "JobSettings" "IsBlacklist"
			if val != "" do chk_isBlacklist.state = execute val
			
			val = getIniSetting deadlineIniFile "JobSettings" "IsInterruptible"
			if val != "" do chk_isInterruptible.state = execute val
			
			edt_limitgroups.text = getIniSetting deadlineIniFile "JobSettings" "LimitGroups"
			edt_machineList.text = getIniSetting deadlineIniFile "JobSettings" "MachineList"
			
			val = getIniSetting deadlineIniFile "JobSettings" "MaxServers" 
			if val != "" then spn_maxServers.value = execute val
			
			val = getIniSetting deadlineIniFile "JobSettings" "UseIpAddress"
			if val != "" do chk_useIpAddress.state = execute val
			
			val = getIniSetting deadlineIniFile "JobSettings" "AutoUpdate"
			if val != "" do chk_autoUpdate.state = execute val
            
            val = getIniSetting deadlineIniFile "JobSettings" "AutoComplete"
			if val != "" do chk_autoComplete.state = execute val
		)
	
		fn CreateSubmitInfoFile filename =
		(              
			local submitInfoFile = CreateFile filename

			if (submitInfoFile != undefined) then
			(
				format "Plugin=CoronaDR\n" to:submitInfoFile
				format "Frames=0-%\n" (spn_maxServers.value-1) to:submitInfoFile
				format "ChunkSize=1\n" to:submitInfoFile
				format "Priority=%\n" spn_priority.value to:submitInfoFile
				format "Pool=%\n" ddl_poollist.selected to:submitInfoFile
				format "SecondaryPool=%\n"  ddl_secondarypoollist.selected to:submitInfoFile
				format "Name=%\n" edt_jobname.text to:submitInfoFile
				format "Comment=%\n" edt_comment.text to:submitInfoFile
				format "Department=%\n" edt_dept.text to:submitInfoFile
				format "Group=%\n" ddl_groups.selected to:submitInfoFile
				format "LimitGroups=%\n" edt_limitgroups.text to:submitInfoFile
                format "TaskTimeoutMinutes=%\n" spn_taskTimeout.value to:submitInfoFile
                format "OnTaskTimeout=Complete\n" to:submitInfoFile

				if chk_isBlacklist.checked then
					format "Blacklist=%\n" edt_machineList.text to:submitInfoFile
				else
					format "Whitelist=%\n" edt_machineList.text to:submitInfoFile
				
				if chk_isInterruptible.checked then
					format "Interruptible=true\n" to:submitInfoFile

				close submitInfoFile
				true
			)
			else
				false
		)
	
		fn CreateJobInfoFile filename =
		(
			local JobInfoFile = CreateFile filename
			if (JobInfoFile != undefined) then
			(
				Close JobInfoFile
				true
			)
			else
				false
		)
		
		fn SubmitJob =
		(
			--save the artists DR settings on their workstation for later restore
			StoreDRSettings()

			DeadlineSubmissionSuccessful = false
			DeadlineSubmissionLastJobID = "failed"
			
			Ui_report (">Job Submission Started...")
			reopenRenderSceneDialog = false
			if renderSceneDialog.isOpen() then
			(
				renderSceneDialog.Close()
				reopenRenderSceneDialog = true
				Ui_report ("+Render Dialog Closed.")
			)

			--Max 2012 or earlier, ensure Backburner 'Net Render' checkbox is disabled in the Render Scene Dialog.
			if rendusenet do
			(
				rendusenet = false
				Ui_report ("Disabling Backburner 'Net Render'.")
			)
			
			Ui_report (">Submitting Corona DR Job to Deadline...")
			
			if ((CreateSubmitInfoFile kDeadlineSubmitInfofile) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Submit Info file"
			if ((CreateJobInfoFile kDeadlineJobInfofile) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Job Info file"
			
			local arguments = "\"" + kDeadlineSubmitInfofile + "\" \"" + kDeadlineJobInfofile + "\""				
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
				renderSceneDialog.Open()

			if retCode == #success then
			(
				DeadlineSubmissionSuccessful = true
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
		
		fn UpdateJob =
		(
			if DeadlineSubmissionLastJobID != "failed" do
			(
				edt_jobId.text = DeadlineSubmissionLastJobID
				
				jobState = GetJobStatus()
				if jobState != #commandFailed and jobState != "Active" then
				(
					MessageBox ("The Corona DR job is no longer active, it is now " + jobState + ".") title:"Job Status Changed"
					DeadlineSubmissionLastJobID = "failed"
					ResetServerControls()
				)
				else
				(
					CheckMaxServers()

					result = CollectRenderingSlaves()
					serverCount = 0

					if result != #commandFailed do
					(
						lbx_activeServers.items = deadlineSlaveNames
						serverCount = deadlineSlaveNames.count

						if getRendererIdString() == "corona" do
						(

							renderers.current.dr_slaveAddresses = #()
							renderers.current.dr_slaveResolvedNames = #()
							
							if chk_useIpAddress.state then
							(
								--use Slave IP address
								for slaveName in deadlineSlaveNames do
									appendIfUnique renderers.current.dr_slaveAddresses (slaveName as string)
							)
							else
							(
								--use Slave Hostname
								for slaveName in deadlineSlaveNames do
									appendIfUnique renderers.current.dr_slaveAddresses (slaveName as string)
									appendIfUnique renderers.current.dr_slaveResolvedNames (slaveName as string)
							)
						)
					Ui_report ("Updated Active Server List.")
					)

					if jobState != #commandFailed then
					(
						if jobState == "Active" then
						(
							if serverCount > 0 then
								jobState = "Rendering"
							else
								jobState = "Queued"
						)
					
						edt_jobStatus.text = jobState
					)
				)
			)
		)
		
		---------------------------		
		--USER INTERFACE HANDLERS--		
		---------------------------		
						
		on DlgMaxCoronaDR2DeadlineRollout open do
		(
			initReportWindow()

			Ui_report (">Building UI...")
			
			GetMaximumPriority()
			spn_priority.range = [0,deadlineMaximumPriority,deadlineMaximumPriority / 2]
			spn_taskTimeout.range = [0,10000,0]
			CollectPools()
			ddl_poollist.items = sort deadlinePools
			ddl_secondarypoollist.items = sort deadlineSecondaryPools
			
			CollectGroups()
			ddl_groups.items = deadlineGroups
			
			Ui_report (">Loading UI Presets...")
			
			--chk_isBlacklist.checked = false
			
			LoadUI()
			
			local version = ((maxVersion())[1] / 1000)
			if version > 9 then
				version = 1998 + version
			
			if getfilenamefile maxfilename != "" do edt_jobname.text = getfilenamefile maxfilename

			if edt_jobname.text == "" then
				edt_jobname.text = "Corona DR Job (3ds Max " + (version as string) + ")"
			else
				edt_jobname.text = edt_jobname.text + "  -  Corona DR Job (3ds Max " + (version as string) + ")"
			
			lbx_activeServers.items = #()
			edt_jobId.text = ""
			edt_jobStatus.text = ""
			
			btn_updateServers.enabled = false
			btn_startRender.enabled = false
			btn_endJob.enabled = false
			edt_jobId.enabled = false
			edt_jobStatus.enabled = false
			lbl_activeServers.enabled = false
			lbx_activeServers.enabled = false
			
			Ui_report ("+Ready.")
		)
		
		on DlgMaxCoronaDR2DeadlineRollout close do
		(
			if DeadlineSubmissionLastJobID != "failed" do
			(
				messageBox "The Corona DR job will be completed" title:"Warning"
				CompleteJob()
			)
		)
		
		on edt_dept entered txt do SaveUI()
		
		on spn_priority changed val do 
		(
			jobPriorityUpdate val
			SaveUI()
		)
		
		on spn_maxServers changed val do SaveUI()
		
		on ddl_poollist selected item do SaveUI()
		on ddl_secondarypoollist selected item do SaveUI()
		on ddl_groups selected item do SaveUI()
		
		on chk_isBlacklist changed state do SaveUI()
		on chk_isInterruptible changed state do SaveUI()
		on chk_useIpAddress changed state do SaveUI()
		on chk_autoUpdate changed state do SaveUI()
        on chk_autoComplete changed state do SaveUI()
		
		on btn_machineList pressed do
		(
			result = GetDeadlineLine( "-selectmachinelist \"" + edt_machineList.text + "\"" )
			if result != "Error getting line" do edt_machineList.text = result
			SaveUI()
		)
		
		on btn_limitgroups pressed do
		(
			result = GetDeadlineLine( "-selectlimitgroups \"" + edt_limitgroups.text + "\"" )
			if result != "Error getting line" do edt_limitgroups.text = result
			SaveUI()
		)
		
		on DlgMaxCoronaDR2DeadlineRollout moved pos do SaveUI()
		
		--on btn_help pressed do ShellLaunch "http://docs.thinkboxsoftware.com/" ""
		
		on btn_startJob pressed do 
		(
			-- Corona renderer
			if getRendererIdString() == "corona" then
			(
				startJob = true
				
				-- Check current renderer is Corona
				if not renderers.current.dr_enable then
				(
					if queryBox "Corona distributed rendering must be enabled before reserving servers. Would you like to enable it now?" title:"Question" then
	                (
	                    revertDeadlineCoronaDistributedEnabled = true
						renderers.current.dr_enable = true
	                )
					else
						startJob = false
				)

				-- Check version of Corona is NEW enough to support DR property names which changed during the alpha cycle. Newer than v7.2 - 1st Feb. 2015 req.
				if (not isProperty renderers.current #dr_slaveAddresses) or (not isProperty renderers.current #dr_slaveResolvedNames) then
				(
					messageBox "This version of Corona is NOT new enough to support interactive 3dsMax - Corona DR. Please upgrade possibly to the latest nightly build version." title:"Error"
					startJob = false
				)

				-- Warn against "Search LAN during render" checkbox being enabled
				if (isProperty renderers.current #dr_searchDuringRender) and (hasProperty renderers.current #dr_searchDuringRender) and renderers.current.dr_searchDuringRender then
				(
					if queryBox "[Search LAN during render] is enabled and could lead to the wrong machines picking up this DR session. Are you sure you want to proceed?" title:"Question" then
					(
						startJob = true
					)
					else
						startJob = false
				)

				if startJob do
				(
					theMessage = SubmitJob()
					Ui_report theMessage
					Ui_report ("+Ready.")

					edt_jobId.text = ""
					edt_jobStatus.text = ""
					
					if DeadlineSubmissionSuccessful do
					(
						if DeadlineSubmissionLastJobID != "failed" do
							edt_jobId.text = DeadlineSubmissionLastJobID
					
						btn_startJob.enabled = false
						btn_updateServers.enabled = true
						btn_startRender.enabled = true
						btn_endJob.enabled = true
						edt_jobId.enabled = true
						edt_jobStatus.enabled = true
						lbl_activeServers.enabled = true

						lbx_activeServers.enabled = true
						tmr_jobUpdate.active = true
						DeadlineJobMaxServers = spn_maxServers.value
					)
				)
			)
			else
				messageBox "Corona Renderer is NOT the current Renderer! Select Corona Renderer in the Render Scene Dialog." title:"Warning"
		)
		
		on btn_updateServers pressed do
		(
			UpdateJob()
		)
		
		on btn_endJob pressed do
		(
			if queryBox "This will complete the Corona DR job. Do you wish to continue?" title:"Warning" then
			(
				CompleteJob()
				
				Ui_report (">Job has been Completed.")
				
				ResetServerControls()
			)
		)

		on btn_startRender pressed do
		(
			-- Corona renderer
			if getRendererIdString() == "corona" then
			(
				-- Check that DR is enabled before rendering
				startRender = true
				if not renderers.current.dr_enable then
				(
					if queryBox "Corona distributed rendering must be enabled before starting the render. Would you like to enable it now?" title:"Question" then
						renderers.current.dr_enable = true
					else
						startRender = false
				)

				if startRender do
				(
					max quick render					
						Ui_report ("+Render Finished.")
                    if chk_autoComplete.state then
                    (
                        CompleteJob()
                        Ui_report (">Job has been Completed.")
                        ResetServerControls()
                    )
				)
			)
		)

		on tmr_jobUpdate tick do
		(
			tmr_jobUpdate.active = false
			tmr_jobUpdate.ticks = 0
			
			if chk_autoUpdate.state do
			(
				UpdateJob()
			)
			
			tmr_jobUpdate.active = true
		)
		
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
	
	CreateDialog DlgMaxCoronaDR2DeadlineRollout pos:winPos style:#(#style_titlebar, #style_border, #style_sysmenu, #style_minimizebox)  
)

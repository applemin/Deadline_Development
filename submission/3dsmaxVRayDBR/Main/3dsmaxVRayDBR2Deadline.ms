macroScript MaxVRayDBR2DeadlineMain category:"Thinkbox" tooltip:"Internal! Use Deadline>MaxVRayDBR2DeadlineMain!"
(
	--openLog @"c:\debug\debug_log.txt" outputOnly:true --DEBUG only

	try(DestroyDialog VDBR_MainRollout)catch()

	global VDBR_MainRollout					--contains the main rollout (dialog)
	global VDBRPaths = undefined			--contains the structure of paths
	global VDBRColorPalette = undefined		--contains the structure of colors
	global VDBRSettings = undefined			--contains the structure of settings
	global VDBRFunctions = undefined		--contains the structure of functions
	gc()

	struct VDBRPathsStruct 					--the structure of system paths used by the submitter
	(
		HomeDir,
		UserHomeDir,
		LogsDir,
		BinDir,
		TempDir,
		DeadlineExec,
		DeadlineBGExec,
		SubmitInfoFile,
		JobInfoFile,
		SubmitOutput,
		SubmitExitCode,
		IniFile,
		DRConfigFile,
		RTDRConfigFile,
		ConfigFile
	)

	VDBRPaths = VDBRPathsStruct() --the global instance of the paths structure storing the actual paths.

	struct VDBRColorPaletteStruct
	(
		blueColor, redColor, greenColor, grayColor, lightGrayColor, lightBlueColor, highlightBgColor, textColor, maxBgColor, blackColor
	)

	VDBRColorPalette = VDBRColorPaletteStruct()
	
	fn defineDotNetColors =
	(
		VDBRColorPalette.textColor = ( ((colorman.getcolor #text) as color)*255)
		VDBRColorPalette.maxBgColor = (((colorman.getcolor #window)) as color)*255
		VDBRColorPalette.blackColor = (dotNetClass "System.Drawing.Color").fromARGB VDBRColorPalette.textColor.r VDBRColorPalette.textColor.g VDBRColorPalette.textColor.b
		if VDBRColorPalette.maxBgColor.v >= 160 then
		(
			VDBRColorPalette.redColor = (dotNetClass "System.Drawing.Color").fromARGB 192 0 0
			VDBRColorPalette.greenColor = (dotNetClass "System.Drawing.Color").fromARGB 0 128 0
			VDBRColorPalette.blueColor = (dotNetClass "System.Drawing.Color").fromARGB 0 0 128
			VDBRColorPalette.lightBlueColor = (dotNetClass "System.Drawing.Color").fromARGB 90 128 160
			VDBRColorPalette.grayColor = (dotNetClass "System.Drawing.Color").fromARGB 128 128 128
			VDBRColorPalette.lightGrayColor = (dotNetClass "System.Drawing.Color").fromARGB 160 160 160
			VDBRColorPalette.highlightBgColor = (dotNetClass "System.Drawing.Color").fromARGB 180 190 200
		)
		else
		(
			VDBRColorPalette.redColor = (dotNetClass "System.Drawing.Color").fromARGB 255 128 128
			VDBRColorPalette.greenColor = (dotNetClass "System.Drawing.Color").fromARGB 128 255 128
			VDBRColorPalette.blueColor = (dotNetClass "System.Drawing.Color").fromARGB 170 200 255
			VDBRColorPalette.lightBlueColor = (dotNetClass "System.Drawing.Color").fromARGB 128 160 255
			VDBRColorPalette.grayColor = (dotNetClass "System.Drawing.Color").fromARGB 192 192 192
			VDBRColorPalette.lightGrayColor = (dotNetClass "System.Drawing.Color").fromARGB 160 160 160
			VDBRColorPalette.highlightBgColor = (dotNetClass "System.Drawing.Color").fromARGB 20 40 60
		)				
	)

	defineDotNetColors()

	struct VDBRSettingsStruct --the global structure of settings
	(
		WinPos = [10, 10],
		TodaysLogFileName = "",
		TodaysLogFile = undefined,
		JobName = "",
		Comment = "",
		Department = "",
		Pools = #(),
		PoolName = "none",
		Pool2Name = "",
		Groups = #(),
		Group = "none",
		MaximumPriority = -1,
		Priority = 50,
		TaskTimeout = 0,
		LimitGroups = "",
		MachineList = "",
		IsBlacklist = false,
		IsInterruptible = false,
		MaxServers = 5,
		CurrentMax = 5,
		PortNumber = 20204,
		UseIpAddress = false,
		AutoUpdate = true,
		AutoComplete = false,
		SlaveNames = #(),
		SlaveNamesToUse = #(),
		SlaveNamesToIgnore = #(),
		RevertVRayDistributedEnabled = false,
		RevertDRSettings = #(),
		SubmissionSuccessful = false,
		SubmissionLastJobID = "failed",
		JobStatus = "",
		DialogAttached = false,
		DialogReOpening = false,
		DialogIgnoreClose = false,
		IsUpdatingList = false
	)

	VDBRSettings = VDBRSettingsStruct()

	struct VDBRFunctionsStruct --the global structure of functions
	(
		fn getDayString =
		(
			theFilterTime = filterString localtime " /\\-:."
			theTime = "- "
			for i = 1 to 3 do theTime += theFilterTime[i] + "-"
			theTime
		),

		fn getTimeString =
		(
			timeArray = getLocalTime()
			local hour = if timeArray[5] < 10 then (hour = "0" + (timeArray[5] as string)) else (hour = (timeArray[5] as string))
			local minute = if timeArray[6] < 10 then (minute = "0" + (timeArray[6] as string)) else (minute = (timeArray[6] as string))
			local second = if timeArray[7] < 10 then (second = "0" + (timeArray[7] as string)) else (second = (timeArray[7] as string))
			timeString = hour + ":" + minute + ":" + second
		),

		fn ArrayToCommaString array = 
		(
			returnString = ""
			for i in 1 to array.count do
			(
				returnString += array[i] as string
				if i != array.count do
					returnString += ","
			)
			return returnString
		),

		fn UiReport txt LogFileOnly:false AddTimeStamp:true =
		(
			if not LogFileOnly do		
			(
				try
				(
					local strStream = txt as StringStream
					local theRange = #()
					local blackColor = (dotNetClass "System.Drawing.Color").fromARGB VDBRColorPalette.textColor.r VDBRColorPalette.textColor.g VDBRColorPalette.textColor.b
					if VDBRColorPalette.maxBgColor.v >= 160 then
					(
						--DARK COLORS
						local redColor = (dotNetClass "System.Drawing.Color").fromARGB 192 0 0
						local orangeColor = (dotNetClass "System.Drawing.Color").fromARGB 192 100 0
						local greenColor = (dotNetClass "System.Drawing.Color").fromARGB 0 92 0
						local blueColor = (dotNetClass "System.Drawing.Color").fromARGB 0 0 128
					)
					else
					(
						--LIGHT COLORS
						local redColor = (dotNetClass "System.Drawing.Color").fromARGB 255 128 128
						local orangeColor = (dotNetClass "System.Drawing.Color").fromARGB 255 180 50
						local greenColor = (dotNetClass "System.Drawing.Color").fromARGB 128 255 128
						local blueColor = (dotNetClass "System.Drawing.Color").fromARGB 192 220 255
					)
					
					local lineCount = 0
					local foreColor = blackColor					
					while not eof strStream do
					(
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
								(matchPattern aLine pattern:"?!!*"): (
									foreColor = orangeColor
								)
								(matchPattern aLine pattern:"!!*"): (
									foreColor = orangeColor
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
						local li = dotNetObject "System.Windows.Forms.ListViewItem" (if AddTimeStamp then VDBRFunctions.getTimeString() else "")
						li.forecolor = foreColor
						local subLi = li.SubItems.add aLine
						append theRange li
					)
					if VDBR_MainRollout != undefined AND VDBR_MainRollout.open do
					(
						VDBR_MainRollout.dnc_report.Items.AddRange theRange
						VDBR_MainRollout.dnc_report.Items.Item[VDBR_MainRollout.dnc_report.Items.Count-1].EnsureVisible()
						local autoRes = dotNetClass "System.Windows.Forms.ColumnHeaderAutoResizeStyle"
						VDBR_MainRollout.dnc_report.AutoResizeColumns autoRes.ColumnContent
						try(windows.processPostedMessages())catch()
					)
					close strStream
				)catch()	
			)	
			if AddTimeStamp then
				try( format "[%] : %\n" (VDBRFunctions.getTimeString()) txt to:VDBRSettings.TodaysLogFile)catch()
			else	
				try( format "%\n" txt to:VDBRSettings.TodaysLogFile)catch()
		),

		fn PreRenderStatus =
		(
			VDBRFunctions.UiReport ("---- RENDER START ----") LogFileOnly:true
		),

		fn PostRenderStatus =
		(
			VDBRFunctions.UiReport ("---- RENDER STOP ----") LogFileOnly:true
		),

		fn GetWinPos = 
		(
			str = GetIniSetting VDBRPaths.IniFile "SubmitDialog" "PositionX"
			if str != "" do VDBRSettings.WinPos.x = str as integer 

			str = GetIniSetting VDBRPaths.IniFile "SubmitDialog" "PositionY"
			if str != "" do VDBRSettings.WinPos.y = str as integer

			if VDBRSettings.WinPos.x > sysinfo.DesktopSize.x - 420 do VDBRSettings.WinPos.x = sysinfo.DesktopSize.x - 420 --move back to screen if dual monitor changed to single monitor or if outside the desktop
			if VDBRSettings.WinPos.y > sysinfo.DesktopSize.y - 100 do VDBRSettings.WinPos.y = sysinfo.DesktopSize.y - 700 --if minimized, fit back to screen
			if VDBRSettings.WinPos.x < 0 do VDBRSettings.WinPos.x = 0 
			if VDBRSettings.WinPos.y < 0 do VDBRSettings.WinPos.y = 0
		),

		fn SaveWinPos = 
		(
			VDBRSettings.WinPos = GetDialogPos VDBR_MainRollout
			SetIniSetting VDBRPaths.IniFile "SubmitDialog" "PositionX" ((VDBRSettings.WinPos.x as integer) as string)
			SetIniSetting VDBRPaths.IniFile "SubmitDialog" "PositionY" ((VDBRSettings.WinPos.y as integer) as string)
		),

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
		),

		fn GetSubmittedJobName = 
		(
			local jobName = ""
			local version = VDBRFunctions.GetMaxVersion()
			rtText = ""
			if VDBRFunctions.getRendererIdString() == "vrayrt" then rtText = "RT"

			if VDBRSettings.JobName == "" then
				local jobName = "Vray" + rtText + " Spawner Job (3ds Max " + (version as string) + ")"
			else
				local jobName = VDBRSettings.JobName + "  -  Vray" + rtText + " Spawner Job (3ds Max " + (version as string) + ")"

			return jobName
		),

		--Create VRay Config File if it does not exist
		fn CreateConfigFile =
		(
			configFile = createFile VDBRPaths.ConfigFile
			if configFile != undefined then
			(
				close configFile
				VDBRFunctions.UiReport ( ">Created Empty Config File" )
			)
			else
				VDBRFunctions.UiReport ("--Failed to Create Config File. Check Permissions!")
		),

		--Save the local DR settings so they can be restored at the end of Deadline DR interactive session
		fn StoreDRSettings configFile:"" =
		(
			VDBRSettings.RevertDRSettings = #()

			local file = openFile configFile mode:"rt"

			if (file != undefined) then
			(
				while (not eof file) do
				(
					line = (readLine file)
					if line != "" AND line != "  1 20204" AND line != "1 1 20204" do
						append VDBRSettings.RevertDRSettings line
				)
				close file
			)
		),

		--Restore the local DR settings at the end of Deadline DR interactive session
		fn RestoreDRSettings configFile:"" =
		(	
			if configFile != undefined do
			(
				local file = openFile configFile mode:"wt"

				if (file != undefined) then
				(
					for i in VDBRSettings.RevertDRSettings do
						format "%\n" i to:file

					close file
				)
			)
		),

		--Clear the local DR settings between DBR job sessions in Deadline, in the case where the UI is left open, but job is completed/failed/deleted
		fn ClearDRSettings configFile:"" =
		(
			if configFile != undefined do
			(
				local file = openFile configFile mode:"wt"

				if (file != undefined) then
				(
					format "" to:file
					close file
				)
			)
		),

		fn ReadStreamIntoArray txt returnArray =
		(
			if txt != undefined then
			(
				local strStream = txt as StringStream
				while not eof strStream do
				(
					local aLine = readLine strStream
					if aLine != "" do appendIfUnique returnArray aLine
				)
				close strStream
			)
			returnArray
		),

		fn ReadTaskStatusIntoMultiArray txt =
		(
			local returnArray = #()
			local theSubArray = #()
			if txt != undefined do
			(
			    local strStream = txt as StringStream
			    while not eof strStream do
			    (
			        local aLine = readLine strStream
			        if matchPattern aLine pattern:"[*]" then
			        (
			            if theSubArray.count > 1 do append returnArray theSubArray
			            theSubArray = #()
			        )
			        else
			        (
						local splitIndex = findString aLine "="
						if splitIndex != undefined then
						(
							local key = substring aLine 1 (splitIndex  - 1)
							local value = substring aLine (splitIndex  + 1) -1
							case key of
							(
								"TaskId": append theSubArray value --"0"
								"TaskStatus": append theSubArray value --"Queued", "Rendering"
								default: continue
							)
						)
					)
			    )
			    close strStream
			)
			if theSubArray.count > 1 do append returnArray theSubArray
			returnArray
		),

		fn CallDeadlineCommand argument multiLine:false timeOut:3600 =
		(
			--Function supports single line and multiline string return
			local resultMsg = ""
			try (
				local p = dotnetobject "system.diagnostics.process"
				p.StartInfo.FileName = VDBRPaths.DeadlineExec
				p.StartInfo.Arguments = argument
				p.StartInfo.RedirectStandardOutput = true
				p.StartInfo.UseShellExecute = false
				p.StartInfo.CreateNoWindow = true
				p.Start()
				if multiLine then
					local cmdOutput = p.StandardOutput.ReadToEnd() --multiple line output
				else
					local cmdOutput = p.StandardOutput.ReadLine() --single line output
				p.WaitForExit(timeOut)
				if p.ExitCode == 0 do resultMsg = cmdOutput
				p.Dispose()
				p = undefined
			)catch()
			resultMsg
		),

		fn CallDeadlineControl argument =
		(
			--Function to display Deadline UI Control and return single line string only
			local resultMsg = "Error getting line"
			try (
				local p = dotnetobject "system.diagnostics.process"
				p.StartInfo.FileName = VDBRPaths.DeadlineExec
				p.StartInfo.Arguments = argument
				p.StartInfo.RedirectStandardOutput = true
				p.StartInfo.UseShellExecute = false
				p.StartInfo.CreateNoWindow = true
				p.Start()
				local cmdOutput = p.StandardOutput.ReadLine()
				p.WaitForExit()
				if p.ExitCode == 0 do ( if cmdOutput != "Action was cancelled by user" do resultMsg = cmdOutput )
				p.Dispose()
				p = undefined
			)catch()
			resultMsg
		),

		fn GetMaximumPriority =
		(
			VDBRSettings.MaximumPriority = 100
			result = VDBRFunctions.CallDeadlineCommand "-GetMaximumPriority"
			if result != "" do VDBRSettings.MaximumPriority = (result as integer)
		),
		
		fn CollectPools =
		(
			VDBRSettings.Pools = #()
			local cmdOutput = VDBRFunctions.CallDeadlineCommand "-Pools" multiLine:true
			if cmdOutput != "" do VDBRFunctions.ReadStreamIntoArray cmdOutput VDBRSettings.Pools
		),
		
		fn CollectGroups =
		(
			VDBRSettings.Groups = #()
			local cmdOutput = VDBRFunctions.CallDeadlineCommand "-Groups" multiLine:true
			if cmdOutput != "" do VDBRFunctions.ReadStreamIntoArray cmdOutput VDBRSettings.Groups
		),
		
		fn CollectRenderingSlaves =
		(
			VDBRSettings.SlaveNames = #()
			local cmdOutput = VDBRFunctions.CallDeadlineCommand ( "-GetMachinesRenderingJob \"" + VDBRSettings.SubmissionLastJobID + "\" \"" + (VDBRSettings.UseIpAddress as string) + "\"" ) multiLine:true
			if cmdOutput != "" then
				VDBRFunctions.ReadStreamIntoArray cmdOutput VDBRSettings.SlaveNames
			else
				return #commandFailed
		),

		fn WaitForCommandToComplete params timeOutInSec =
		(
			local result = -2
			deleteFile VDBRPaths.SubmitExitCode
			deleteFile VDBRPaths.SubmitOutput
			ShellLaunch VDBRPaths.DeadlineBGExec ("-outputfiles \"" + VDBRPaths.SubmitOutput + "\" \"" + VDBRPaths.SubmitExitCode + "\" " + params)
			
			startTimeStamp = timestamp()
			ready = false
			while not ready do
			(
				sleep 0.25
				if doesFileExist VDBRPaths.SubmitExitCode then
				(
					theFile = openFile VDBRPaths.SubmitExitCode 
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
		),

		fn GetZeros theNumber count:4 =
		(
			local theStr = theNumber as string
			local theCount = count-(theStr.count)
			if theCount < 1 then "" else substring "00000000000" 1 theCount
		),

		fn GetMaxVersion =
		(
			local version = ((maxVersion())[1] / 1000)
			if version > 9 then
				version = 1998 + version
		),

		fn StartBackgroundWorker =
		(
			global BackgroundWorker = dotnetobject "CSharpUtilities.SynchronizingBackgroundWorker"
			BackgroundWorker.WorkerSupportsCancellation = true

			fn TimerThread =
			(
				global DotNetTimer = dotnetobject "System.Timers.Timer"
				DotNetTimer.AutoReset = true --ensure timer is reset after each elapsed time interval
				DotNetTimer.Interval = 30000 --every 30 seconds

				if BackgroundWorker != undefined AND BackgroundWorker.CancellationPending then
				(
					DotNetTimer.Stop() --Stop Timer
					dotnet.removeAllEventHandlers DotNetTimer --Remove Event Handler
		    		DotNetTimer.Dispose() --Dispose Timer
				)
				else
				(
					fn TimerElapsed sender e =
				    (
				    	local rolloutVisible = try(VDBR_MainRollout.open)catch(False)
				    	if not VDBRSettings.IsUpdatingList AND rolloutVisible do VDBR_MainRollout.UpdateJob()
				    )

					fn TimerDisposed sender e =
					(
						DotNetTimer.Stop()
						dotnet.removeAllEventHandlers DotNetTimer --Remove Event Handler
						DotNetTimer.Dispose() --Dispose Timer
						VDBRFunctions.UiReport ("--Timer Thread Disposed") LogFileOnly:true
					)

					dotnet.addEventHandler DotNetTimer "Elapsed" TimerElapsed
					dotnet.addEventHandler DotNetTimer "Disposed" TimerDisposed
					
					DotNetTimer.Start()
				)
			)
			
			fn BackgroundWorkerDisposed sender e =
			(
				dotnet.removeAllEventHandlers BackgroundWorker
				DotNetTimer.Dispose() --Dispose Timer
				VDBRFunctions.UiReport ("--Background Worker Disposed") LogFileOnly:true
			)

			dotNet.addEventHandler BackgroundWorker "DoWork" TimerThread
			dotNet.addEventHandler BackgroundWorker "Disposed" BackgroundWorkerDisposed

			if not BackgroundWorker.IsBusy do
			(
				BackgroundWorker.RunWorkerAsync() --if BackgroundWorker not already running, then run it
				VDBRFunctions.UiReport ( ">Background Worker Started" ) LogFileOnly:true
			)
		),

		fn StopBackgroundWorker =
		(
			if BackgroundWorker != undefined do
			(
				if BackgroundWorker.IsBusy do
				(
					BackgroundWorker.CancelAsync() --BackgroundWorker busy then cancel it
					VDBRFunctions.UiReport ( ">Background Worker Stopped" ) LogFileOnly:true
				)
				BackgroundWorker.Dispose()
				BackgroundWorker = undefined
				DotNetTimer = undefined
			)
		),

		fn ScanForDialog =
		(
			if (maxVersion())[1]/1000 >= 16 AND VDBRFunctions.getRendererIdString() == "vray" do --3dsMax 2014 or later / VRay only
			(
				DialogMonitorOPS.Enabled = true --start the DialogMonitorOPS
				DialogMonitorOps.Interactive = false
				DialogMonitorOPS.UnRegisterNotification id:#VDBR_Dialog
				VDBRFunctions.UiReport (">[Rendering] dialog scanning started") LogFileOnly:true
				callbacks.removeScripts id:#VDBR_UnRegisterDialog
				callbacks.removeScripts id:#VDBR_ReOpenDialog
				callbacks.addScript #beginRenderingActualFrame "try(VDBRFunctions.UnregisterScanForDialog())catch()" id:#VDBR_UnRegisterDialog
				callbacks.addScript #postRender "try(VDBRFunctions.ReOpenDialog())catch()" id:#VDBR_ReOpenDialog
				DialogMonitorOPS.RegisterNotification VDBRFunctions.AttachDialog id:#VDBR_Dialog
			)
		),

		fn AttachDialog = 
		(
			hwnd = DialogMonitorOPS.GetWindowHandle()
-- 			VDBRFunctions.UiReport (">DEBUG: Windows Handle: " + (hwnd as string) ) LogFileOnly:false
-- 			VDBRFunctions.UiReport (">DEBUG: Windows Text Name: " + (UIAccessor.GetWindowText hwnd) as string) LogFileOnly:false
			if hwnd != undefined AND (hwnd as string) != "" do
			(
				if (matchPattern ((UIAccessor.GetWindowText hwnd) as string) pattern:"Rendering*") do
				(
					VDBRFunctions.UiReport (">[AttachDialog] function has been called") LogFileOnly:true
					VDBRSettings.DialogAttached = true
					VDBRSettings.DialogIgnoreClose = true
					try(DestroyDialog VDBR_MainRollout)catch()
					VDBRFunctions.GetWinPos()
					CreateDialog VDBR_MainRollout pos:VDBRSettings.WinPos style:#(#style_titlebar, #style_border, #style_sysmenu, #style_minimizebox) parent:hwnd
					VDBRSettings.DialogIgnoreClose = false
				)
			)
			true --function must return a boolean
		),

		fn UnregisterScanForDialog =
		(
			VDBRFunctions.UiReport ( ">[UnregisterScanForDialog] function has been called" ) LogFileOnly:true
			DialogMonitorOPS.UnRegisterNotification id:#VDBR_Dialog
			DialogMonitorOPS.Enabled = false --stop the DialogMonitorOPS
		),

		fn ReOpenDialog =
		(
			if (maxVersion())[1]/1000 >= 16 AND VDBRFunctions.getRendererIdString() == "vray" do --3dsMax 2014 or later / VRay only
			(
				VDBRSettings.DialogAttached = false
				VDBRSettings.DialogReOpening = true
				VDBRSettings.DialogIgnoreClose = true
				try(DestroyDialog VDBR_MainRollout)catch()
				VDBRFunctions.GetWinPos()
				VDBRFunctions.UiReport (">Re-Opening [VDBR_MainRollout]") LogFileOnly:true
				CreateDialog VDBR_MainRollout pos:VDBRSettings.WinPos style:#(#style_titlebar, #style_border, #style_sysmenu, #style_minimizebox)
				callbacks.removeScripts id:#VDBR_UnRegisterDialog
				callbacks.removeScripts id:#VDBR_ReOpenDialog
				VDBRSettings.DialogIgnoreClose = false
			)
		)
	)

	VDBRFunctions = VDBRFunctionsStruct()

	-----------------------------------------------------------------------------------------------
	--PATHS
	-----------------------------------------------------------------------------------------------

	VDBRPaths.BinDir = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\"
	VDBRPaths.DeadlineExec = VDBRPaths.BinDir + "deadlinecommand.exe"
	VDBRPaths.DeadlineBGExec = VDBRPaths.BinDir + "deadlinecommandbg.exe"

	VDBRPaths.HomeDir = getDir #temp --default to temp folder in case the following code fails
	deadlineHome = VDBRFunctions.CallDeadlineCommand "-GetHomeDirectory"
	if(deadlineHome != "") then VDBRPaths.HomeDir = deadlineHome +"\\"

	VDBRPaths.UserHomeDir = getDir #temp --default to temp folder in case the following code fails
	deadlineUserHome = VDBRFunctions.CallDeadlineCommand "-GetCurrentUserHomeDirectory"
	if(deadlineUserHome != "") then VDBRPaths.UserHomeDir = deadlineUserHome +"\\"

	VDBRPaths.TempDir = VDBRPaths.UserHomeDir + "temp\\"
	makeDir VDBRPaths.TempDir all:true

	VDBRPaths.LogsDir = VDBRPaths.UserHomeDir + "logs\\"
	makedir VDBRPaths.LogsDir all:true

	VDBRPaths.SubmitInfoFile = VDBRPaths.TempDir + "vdbr_submit_info.job"
	VDBRPaths.JobInfoFile = VDBRPaths.TempDir + "vdbr_job_info.job"
	VDBRPaths.SubmitOutput = sysInfo.tempdir + "vdbr_submitOutput.txt"
	VDBRPaths.SubmitExitCode = sysInfo.tempdir + "vdbr_submitExitCode.txt"

	VDBRPaths.IniFile = GetDir #plugcfg + "\\MaxVRayDBR2Deadline.ini"
	VDBRPaths.DRConfigFile = GetDir #plugcfg + "\\vray_dr.cfg"
	VDBRPaths.RTDRConfigFile = GetDir #plugcfg + "\\vrayrt_dr.cfg"
	VDBRPaths.ConfigFile = undefined

	-----------------------------------------------------------------------------------------------
	--MAIN ROLLOUT
	-----------------------------------------------------------------------------------------------

	rollout VDBR_MainRollout "Setup VRay DBR With Deadline" width:410 height:760
	(
		group "Job Description" 
		(
			edittext edt_jobname "Job Name" fieldwidth:310 align:#right
			edittext edt_comment "Comment" fieldwidth:310 align:#right
			edittext edt_dept "Department" fieldwidth:310 align:#right
		)	
		
		group "Job Scheduling" 
		(
			label lbl_pools "Pool" align:#left offset:[48,4] across:2
			dropdownList ddl_poollist "" width:310 align:#center offset:[-61,0]
			
			label lbl_secondarypools "Secondary Pool" align:#left offset:[-4,4] across:2
			dropdownList ddl_pool2list "" width:310 align:#center offset:[-61,0]

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
		
		group "VRay Spawner Options" 
		(
			label lbl_maxServers "Maximum Servers" align:#left offset:[12,2] across:2
			spinner spn_maxServers "" type:#integer fieldwidth:90 range:[1,100,5] align:#left offset:[-94,1] tooltip:"This is the max. number of Deadline Slaves to be reserved to assist in computing this V-Ray DBR session."

			label lbl_portNumber "Port Number" align:#left offset:[12,2] across:3
			spinner spn_portNumber "" type:#integer fieldwidth: 90 range:[1024,65535,20204] align:#left offset:[-30,1] tooltip:"V-Ray/V-Ray RT Port Number.\nDefault: 20204 (V-Ray) / 20206 (V-Ray RT), Min: 1024, Max: 65535.\nAvoid using TCP Port 20205"
			label lbl_portInfo "V-Ray:20204 / V-Ray RT:20206" align:#right offset:[-20,1] tooltip:"V-Ray Production Renderer uses a TCP Port (Default: 20204).\nV-Ray RT Renderer uses a TCP Port (Default: 20206)."

			checkbox chk_useIpAddress "Use Server IP Address Instead of Host Name" offset:[101,1] tooltip:"When enabled, IP address is used instead of DNS resolved Host Name. Use this option when you have no DNS server running on your network."
			checkbox chk_autoUpdate "Automatically Update Server List" offset:[101,1] tooltip:"When enabled, the Active Server List is automatically updated." checked:true
			checkbox chk_autoComplete "Complete Job after Render" offset:[101,1] tooltip:"When enabled, the Deadline submitted job will automatically be marked as completed when the current DBR session has finished."

			edittext edt_jobId "Spawner Job ID" fieldwidth:284 align:#left offset:[21,0]
			edittext edt_jobStatus "Spawner Job Status" fieldwidth:284 align:#left offset:[1,0]

			label lbl_activeServers "Active Servers" across:2 align:#left offset:[25,0]
			dotNetControl lv_activeServers "System.Windows.Forms.ListView" width:284 height:140 align:#right offset:[1,0]

			button btn_CheckAll "Check ALL" width:100 height:20 align:#left offset:[-3,-75] tooltip:"Check All Slaves in the Active Servers list."
			button btn_CheckInvert "INVERT" width:100 height:20 align:#left offset:[-3,0] tooltip:"Invert State of Slaves in the Active Servers list."
			button btn_CheckNone "Check NONE" width:100 height:20 align:#left offset:[-3,0] tooltip:"Check None Slaves in the Active Servers list."
		)
		
		button btn_startJob "Reserve Servers" width:95 height:30 across:4 offset:[-7,0] tooltip:"Submits a VRay Spawner job to Deadline to reserve servers..."
		button btn_updateServers "Update Servers" width:95 height:30 offset:[-3,0] tooltip:"Manually update the active server list and job status..." enabled:false
		button btn_startRender "Start Render" width:95 height:30 offset:[2,0] tooltip:"Starts the VRay DBR render..." enabled:false
		button btn_endJob "Release Servers" width:95 height:30 offset:[7,0] tooltip:"Completes the current VRay Spawner job..." enabled:false

		dotNetControl dnc_report "System.Windows.Forms.ListView" width:396 height:90 align:#center offset:[0,0]

		button btn_clearLogWindow "Clear Log Window" align:#left across:3 height:18 width:135 offset:[-12,-4] tooltip:"Clears the content of the Log Window.\n\nNote that the complete Log is preserved in a text file accessible through the buttons to the right.\n\nRight-clicking any of the 3 buttons will open the Windows Explorer at the Log Files location."
		button btn_openLogNotepad "Open Log in Notepad" align:#center height:18 width:135 offset:[0,-4] tooltip:"Opens the current Log file in Windows Notepad.\n\nRight-clicking any of the 3 buttons will open the Windows Explorer at the Log Files location."
		button btn_clearLogDefaultEditor "Open Log in Default Editor" align:#right height:18 width:135 offset:[12,-4] tooltip:"Opens the current Log file in the Default Editor registered for editing .LOG files.\n\nRight-clicking any of the 3 buttons will open the Windows Explorer at the Log Files location."

		fn initReportWindow =
		(
			try
			(
			local lv = dnc_report
			local layout_def = #(#("Time Stamp",40), #("Message",200))
			lv.Clear()
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB VDBRColorPalette.maxBgColor.r VDBRColorPalette.maxBgColor.g VDBRColorPalette.maxBgColor.b
			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.gridLines = false
			lv.fullRowSelect = true
			lv.checkboxes = false
			lv.hideSelection = true
			lv.HeaderStyle = lv.HeaderStyle.None
			for i in layout_def do lv.Columns.add i[1] i[2]
			)catch()
		)
		
		on btn_clearLogWindow pressed do 
		(
			initReportWindow()
		)
		on btn_openLogNotepad pressed do if doesFileExist VDBRSettings.TodaysLogFileName do shelllaunch "notepad.exe" VDBRSettings.TodaysLogFileName 
		on btn_clearLogDefaultEditor pressed do if doesFileExist VDBRSettings.TodaysLogFileName do shelllaunch VDBRSettings.TodaysLogFileName ""
			
		fn exploreLogFolder =
		(
			try(shellLaunch "Explorer.exe" (getFileNamePath VDBRSettings.TodaysLogFileName))catch()
		)
		on btn_clearLogWindow rightclick do exploreLogFolder()
		on btn_openLogNotepad rightclick do exploreLogFolder()
		on btn_clearLogDefaultEditor rightclick do exploreLogFolder()

		fn ReportSubmissionSettings =
		(
			VDBRFunctions.UiReport ("File Path: ["+ maxFilePath + "]") 
			VDBRFunctions.UiReport ("File Name: ["+ maxFileName + "]")
			local txt = ">SCENE INFO:\n"
			txt += ("\t\tScene Nodes: "+objects.count as string + "\n") 
			txt += ("\t\tGeometry: "+geometry.count as string + "\n") 
			txt += ("\t\tShapes: "+shapes.count as string + "\n") 
			txt += ("\t\tLights: "+lights.count as string  + "\n") 
			txt += ("\t\tCameras: "+cameras.count as string + "\n") 
			txt += ("\t\tHelpers: "+helpers.count as string  + "\n") 
			txt += ("\t\tSpaceWarps: "+spacewarps.count as string + "\n" ) 
			VDBRFunctions.UiReport txt LogFileOnly:true

			local theCam = viewport.getCamera()
			if isValidNode theCam then
				VDBRFunctions.UiReport ("Current View: ["+ theCam.name + "]")
			else
				VDBRFunctions.UiReport ("Current View: Not A Camera")

			VDBRFunctions.UiReport ("Current Renderer: " + (renderers.current as string))
			
			VDBRFunctions.UiReport (">VERSIONS:") LogFileOnly:true

			--3dsmax version
			local VersionInfo = dotnetclass "System.Diagnostics.FileVersionInfo"
			local MyMax = VersionInfo.GetVersionInfo (pathConfig.appendPath (pathConfig.GetDir #maxroot) "3dsmax.exe")
			txt = ("\t3dsMax version: " + MyMax.FileVersion as string)
			VDBRFunctions.UiReport txt LogFileOnly:true
			
			--vray version
			local vrayVersionCheck = try(vrayVersion())catch(undefined) --2 element array returned in VRay v3.0+ only #(version, build)
			if vrayVersionCheck != undefined then
			(
				txt = ("\tVRay version, build: " + (vrayVersionCheck as string))
				vrayVer = (substring vrayVersionCheck[1] 1 3) as float
				if vrayVer < 3.2 do
					txt += ("\n\t\tWARNING: VRay dynamic add DR nodes ONLY supported in VRay 3.2 [SP2] and onwards\n")
			)
			else
			(
				txt = ("\tVRay version: 2")
				txt += ("\n\t\tWARNING: VRay dynamic add DR nodes NOT supported in VRay 2 (Requires min. VRay 3.2 [SP2])\n")
			)

			VDBRFunctions.UiReport txt LogFileOnly:true

			local txt = ">SUBMISSION SETTINGS:\n"
			theProps = getPropNames VDBRSettings
			for p in theProps do
				txt += ( "\t\t" + (p as string) + " = " + (getProperty VDBRSettings p) as string + "\n") 
			VDBRFunctions.UiReport txt LogFileOnly:true
		)

		fn initListView =
		(
			try
			(
			local lv = lv_activeServers
			local layout_def = #(#("Host name / IP address",250))
			lv.foreColor = (dotNetClass "System.Drawing.Color").fromARGB VDBRColorPalette.textColor.r VDBRColorPalette.textColor.g VDBRColorPalette.textColor.b
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB VDBRColorPalette.maxBgColor.r (VDBRColorPalette.maxBgColor.g+15) (VDBRColorPalette.maxBgColor.b+5)
			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.gridLines = true
			lv.fullRowSelect = true
			lv.checkboxes = true
			lv.hideSelection = false
			lv.LabelEdit = false
			for i in layout_def do lv.Columns.add i[1] i[2]
			)catch()
		)

		fn updateListView =
		(
			VDBRSettings.IsUpdatingList = true
			local theRange = #()
			try
			(
				lv_activeServers.Items.clear()
				for i in VDBRSettings.SlaveNames do
				(
					li = dotNetObject "System.Windows.Forms.ListViewItem" i
					
					--new Slaves should always be enabled by default in the UI
					if (findItem VDBRSettings.SlaveNamesToUse i == 0) AND (finditem VDBRSettings.SlaveNamesToIgnore i == 0) then
					(
						li.checked = true
						appendIfUnique VDBRSettings.SlaveNamesToUse i
					)

					--pre-existing Slave should be enabled if the user checks the Slave in the UI
					else if (findItem VDBRSettings.SlaveNamesToUse i > 0) AND (finditem VDBRSettings.SlaveNamesToIgnore i == 0) then
					(
						li.checked = true
						appendIfUnique VDBRSettings.SlaveNamesToUse i
						local theIndex = findItem VDBRSettings.SlaveNamesToIgnore theText
						if theIndex > 0 do deleteItem VDBRSettings.SlaveNamesToIgnore theIndex
					)

					--pre-existing Slave should be disabled if the user un-checks the Slave in the UI
					else if (findItem VDBRSettings.SlaveNamesToIgnore i > 0) AND (findItem VDBRSettings.SlaveNamesToUse i == 0) then
					(
						li.checked = false
						appendIfUnique VDBRSettings.SlaveNamesToIgnore i
						local theIndex = findItem VDBRSettings.SlaveNamesToUse theText
						if theIndex > 0 do deleteItem VDBRSettings.SlaveNamesToUse theIndex
					)

					--append theRange li
					appendIfUnique theRange li
				)	
				lv_activeServers.Items.AddRange theRange
			)catch()

			if VDBRSettings.SlaveNames.count == 0 then
			(
				btn_CheckAll.enabled = false
				btn_CheckInvert.enabled = false
				btn_CheckNone.enabled = false

				--reset the arrays if the Slave list is empty
				VDBRSettings.SlaveNamesToUse = #()
				VDBRSettings.SlaveNamesToIgnore = #()
			)
			else
			(
				btn_CheckAll.enabled = true
				btn_CheckInvert.enabled = true
				btn_CheckNone.enabled = true
			)

			VDBRSettings.IsUpdatingList = false
		)

		local guiExecuted = true
		local selNums = #()
		local checkStates = #()

		on lv_activeServers ItemChecked itm do
		(
			if not VDBRSettings.IsUpdatingList do
			(
				if guiExecuted do
				(
					try(theItem = itm.Item)catch(undefined)
					if theItem != undefined then
					(
						theText = theItem.Text
						if theItem.checked then 
						(
							local theIndex = findItem VDBRSettings.SlaveNamesToIgnore theText
							if theindex > 0 do deleteItem VDBRSettings.SlaveNamesToIgnore theIndex
							appendIfUnique VDBRSettings.SlaveNamesToUse theText
							VDBRFunctions.UiReport ("+Active Servers - Slave ADDED : [" + theText + "]")
						)	
						else
						(
							local theIndex = findItem VDBRSettings.SlaveNamesToUse theText
							if theIndex > 0 do deleteItem VDBRSettings.SlaveNamesToUse theIndex
							appendIfUnique VDBRSettings.SlaveNamesToIgnore theText
							VDBRFunctions.UiReport ("+Active Servers - Slave REMOVED : [" + theText + "]")
						)
					)
					else
						VDBRFunctions.UiReport ("--Active Servers - Item undefined")
				)
			)
		)

		on lv_activeServers MouseUp args do
		(
			guiExecuted = false
			for x = 1 to selNums.count do lv_activeServers.items.item[selNums[x]].checked = checkStates[x] -- correct the checkboxes
			selNums = #(); checkStates = #() -- clear the record
			guiExecuted = true
		)

		on lv_activeServers ItemSelectionChanged args do
		(
			-- record the states of the checkboxes so we can correct them at MouseUp	
			selNums = for x = 0 to lv_activeServers.selectedIndices.count - 1 collect lv_activeServers.selectedIndices.item[x]
			checkStates = for x = 1 to selNums.count collect lv_activeServers.items.item[selNums[x]].checked
		)

		on btn_CheckAll pressed do
		(
			for i = 1 to lv_activeServers.items.count do
				lv_activeServers.items.item[i-1].checked = true
			updateListView()
		)
			
		on btn_CheckInvert pressed do
		(
			for i = 1 to lv_activeServers.items.count do
				lv_activeServers.items.item[i-1].checked = not lv_activeServers.items.item[i-1].checked
			updateListView()
		)

		on btn_CheckNone pressed do
		(
			for i = 1 to lv_activeServers.items.count do
				lv_activeServers.items.item[i-1].checked = false
			updateListView()
		)

		fn SetMaxServers = 
		(
			if VDBRSettings.MaxServers != VDBRSettings.CurrentMax then
			(
				local maxServers = VDBRSettings.MaxServers
				local arguments = ""
				local resultMsg = ""
				VDBRFunctions.UiReport ("+Updating VRay Spawner Count to " + (maxServers as string))

				arguments = ( "-GetJobTasks \"" + VDBRSettings.SubmissionLastJobID + "\" true" )
				local cmdOutput = VDBRFunctions.CallDeadlineCommand arguments multiLine:true
				local tasksArray = #()
				if cmdOutput != "" do tasksArray = VDBRFunctions.ReadTaskStatusIntoMultiArray cmdOutput

				local tasksCount = tasksArray.count

				local activeTasksCount = 0
				for i in 1 to tasksArray.count do
					if tasksArray[i][2] == "Queued" OR tasksArray[i][2] == "Rendering" do activeTasksCount += 1

				--remove Slaves from DBR session
				if activeTasksCount > maxServers then
				(
					local taskIDsToCompleteArray = #()

					for i = tasksArray.count to 1 by -1 where (tasksArray[i][2] != "Queued" AND tasksArray[i][2] != "Rendering") do
						deleteItem tasksArray i

					for i = tasksArray.count to 1 by -1 where tasksArray.count > maxServers do
					(
						append taskIDsToCompleteArray tasksArray[i][1]
						deleteItem tasksArray i
					)

					sort taskIDsToCompleteArray
					taskIds = VDBRFunctions.ArrayToCommaString taskIDsToCompleteArray
					arguments = ( "-CompleteJobTasks \"" + VDBRSettings.SubmissionLastJobID + "\" \"" + taskIds + "\"" )
					--VDBRFunctions.UiReport ( ">DEBUG: CompleteJobTasks: " + (taskIds as string) )
					local resultMsg = VDBRFunctions.CallDeadlineCommand arguments
				)
				
				--add Slaves to DBR session
				else if activeTasksCount < maxServers then
				(
					--remove any non-completed tasks (active/rendering)
					for i = tasksArray.count to 1 by -1 where tasksArray[i][2] != "Completed" do --skipping other task states such as suspended, failed or unknown
						deleteItem tasksArray i

					--calculate the task count that needs reactiving
					local tasksToReactive = maxServers-activeTasksCount
					
					--collect taskIds to requeue any exising tasks if present, subtracting from tasksToReactive counter
					local taskIDsToRequeueArray = #()
					for i in 1 to tasksArray.count where tasksToReactive != 0 do
					(
						append taskIDsToRequeueArray tasksArray[i][1]
						tasksToReactive = tasksToReactive-1
					)

					--requeue some/all completed tasks IF any present
					sort taskIDsToRequeueArray
					taskIds = VDBRFunctions.ArrayToCommaString taskIDsToRequeueArray
					arguments = ( "-RequeueJobTasks \"" + VDBRSettings.SubmissionLastJobID + "\" \"" + taskIds + "\"" )
					local resultMsg = VDBRFunctions.CallDeadlineCommand arguments
					
					--if tasksToReactive counter != 0, then append new frames to existing job
					if tasksToReactive != 0 do
					(
						arguments = ( "-AppendJobFrameRange \"" + VDBRSettings.SubmissionLastJobID + "\" \"" + ((tasksCount-1) as string) + "-" + (((tasksCount-1)+tasksToReactive) as string) + "\"" )
						--VDBRFunctions.UiReport ( ">DEBUG: AppendJobFrameRange: " + ((tasksCount-1) as string) + "-" + (((tasksCount-1)+tasksToReactive) as string) )
						local resultMsg = VDBRFunctions.CallDeadlineCommand arguments
					)
				)
				
				if resultMsg != "" do VDBRSettings.CurrentMax = maxServers
			)
		)
		
		fn GetJobStatus =
		(
			local arguments = ("-GetJobSetting " + "\"" + VDBRSettings.SubmissionLastJobID + "\" Status")
			local resultMsg = VDBRFunctions.CallDeadlineCommand arguments
			if resultMsg == "" do resultMsg = "Deleted"
			return resultMsg
		)
		
		fn ResetSpawnerControls =
		(
			VDBRFunctions.StopBackgroundWorker()

			edt_jobId.text = ( VDBRSettings.SubmissionLastJobID = "" )
			edt_jobStatus.text = ( VDBRSettings.JobStatus = "" )
			lv_activeServers.Items.clear()

			spn_portNumber.enabled = true
			btn_startJob.enabled = true
			btn_updateServers.enabled = false
			btn_startRender.enabled = false
			btn_endJob.enabled = false
			edt_jobId.enabled = false
			edt_jobStatus.enabled = false
			lbl_activeServers.enabled = false
			btn_CheckAll.enabled = false
			btn_CheckInvert.enabled = false
			btn_CheckNone.enabled = false

			VDBRSettings.SlaveNames = #()
			VDBRSettings.SlaveNamesToUse = #()
			VDBRSettings.SlaveNamesToIgnore = #()
		)

		fn CompleteJob =
		(
			if VDBRSettings.SubmissionLastJobID != "failed" do
			(
                if VDBRSettings.revertVRayDistributedEnabled then
                (
                	if VDBRFunctions.getRendererIdString() == "vray" then
                    	renderers.current.system_distributedRender = false
                    else
                    	renderers.current.distributed_rendering = false
                )
				VDBRFunctions.CallDeadlineCommand ( "-CompleteJob \"" + VDBRSettings.SubmissionLastJobID + "\"" )
				VDBRSettings.SubmissionLastJobID = "failed"
				ResetSpawnerControls()
				VDBRFunctions.ClearDRSettings configFile:VDBRPaths.ConfigFile
			)
			VDBRSettings.SubmissionSuccessful = false
		)

		fn DisplayPoolsList =
		(
			ddl_poollist.items = VDBRSettings.Pools
			ddl_pool2list.items = (join #("") VDBRSettings.Pools)
			
			local theIndex = findItem ddl_poollist.items VDBRSettings.PoolName
			if theIndex > 0 then 
				ddl_poollist.selection = theIndex 
			else
			(
				theIndex = findItem ddl_poollist.items "none"
				if theIndex > 0 do
				(
					ddl_poollist.selection = theIndex
					VDBRSettings.PoolName = "none"
				)
			)

			local theIndex = findItem ddl_pool2list.items VDBRSettings.Pool2Name
			if theIndex > 0 then 
				ddl_pool2list.selection = theIndex
			else
			(
				ddl_pool2list.selection = 1
				VDBRSettings.Pool2Name = ""
			)
		)
		
		fn DisplayGroupsList =
		(
			ddl_groups.items = VDBRSettings.Groups
			
			local theIndex = findItem ddl_groups.items VDBRSettings.Group
			if theIndex > 0 then 
				ddl_groups.selection = theIndex 
			else
			(
				theIndex = findItem ddl_groups.items "none"
				if theIndex > 0 do
				(
					ddl_groups.selection = theIndex 
					VDBRSettings.Group = "none"
				)
			)
		)

		on edt_jobname entered txt do 
		(
			VDBRSettings.JobName = txt
			VDBRFunctions.UiReport ("+Job Name Changed To ["+ txt +"]")
		)

		on edt_comment entered txt do
		(
			VDBRSettings.Comment = txt
			VDBRFunctions.UiReport ("+Comment Changed To ["+ txt +"]")
		)

		on edt_dept entered txt do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "Department" (VDBRSettings.Department = txt)
			VDBRFunctions.UiReport ("+Department Changed To ["+ txt +"]")
		)

		on ddl_poollist selected itm do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "Pool" ( (VDBRSettings.PoolName = ddl_poollist.selected) as string )
			VDBRFunctions.UiReport ("+Pool changed to ["+ VDBRSettings.PoolName +"]")
			DisplayPoolsList()
		)
		
		on ddl_pool2list selected itm do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "Pool2Name" ( (VDBRSettings.Pool2Name = ddl_pool2list.selected) as string )
			if VDBRSettings.Pool2Name == "" then
				VDBRFunctions.UiReport ("+Secondary Pool DISABLED.")
			else
				VDBRFunctions.UiReport ("+Secondary Pool changed to ["+ VDBRSettings.Pool2Name +"]")
			DisplayPoolsList()
		)
		
		on ddl_groups selected itm do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "Group" ( (VDBRSettings.Group = ddl_groups.selected) as string )
			VDBRFunctions.UiReport ("+Group Changed To ["+ VDBRSettings.Group +"]")
			DisplayGroupsList()
		)

		fn JobPriorityUpdate val =
		(
			if val <= VDBRSettings.MaximumPriority do
			(
				spn_priority.value = val
			)
			val
		)

		on spn_priority changed value do
		(	
			setIniSetting VDBRPaths.IniFile "JobSettings"  "Priority" ( (VDBRSettings.Priority = (JobPriorityUpdate value)) as string )
			VDBRFunctions.UiReport ("+Priority Spinner changed to ["+ VDBRSettings.Priority as string +"]") LogFileOnly:true
		)

		on spn_taskTimeout changed value do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "TaskTimeout" ( (VDBRSettings.TaskTimeout =  spn_taskTimeout.value) as string )
			VDBRFunctions.UiReport ("+Task Timeout changed to ["+ VDBRSettings.TaskTimeout as string +"]")
		)
		
		on btn_limitgroups pressed do
		(
			result = VDBRFunctions.CallDeadlineControl( "-selectlimitgroups \"" + edt_limitgroups.text + "\"" )
			if result != "Error getting line" then
			(
				edt_limitgroups.text = result
				setIniSetting VDBRPaths.IniFile "JobSettings"  "LimitGroups" (VDBRSettings.LimitGroups = result)
				if VDBRSettings.LimitGroups != "" then
					VDBRFunctions.UiReport ("+Limit Groups Changed To ["+ VDBRSettings.LimitGroups +"]")
				else
					VDBRFunctions.UiReport ("+Limit Groups Changed To [EMPTY]")
			)
		)

		on edt_limitgroups entered txt do
		(
			VDBRSettings.LimitGroups = txt
			VDBRFunctions.UiReport ("+Limit Groups Changed To ["+ VDBRSettings.LimitGroups +"]")
		)
		
		on btn_machineList pressed do
		(
			result = VDBRFunctions.CallDeadlineControl( "-selectmachinelist \"" + edt_machineList.text + "\"" )
			if result != "Error getting line" then
			(
				edt_machineList.text = result
				setIniSetting VDBRPaths.IniFile "JobSettings"  "MachineList" (VDBRSettings.MachineList = result)
				if VDBRSettings.MachineList != "" then
					VDBRFunctions.UiReport ("+Machine List Changed To ["+ VDBRSettings.MachineList +"]")
				else
					VDBRFunctions.UiReport ("+Machine List Changed To [EMPTY]")
			)
		)

		on edt_machineList entered txt do
		(
			VDBRSettings.MachineList = txt
			VDBRFunctions.UiReport ("+Machine List Changed To ["+ VDBRSettings.MachineList +"]")
		)

		on chk_isBlacklist changed state do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "IsBlacklist" ( (VDBRSettings.IsBlacklist = chk_isBlacklist.state) as string )
			VDBRFunctions.UiReport ("+Machine List Is A Blacklist Changed To ["+ VDBRSettings.IsBlacklist as string +"]")
		)

		on chk_isInterruptible changed state do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "IsInterruptible" ( (VDBRSettings.IsInterruptible = chk_isInterruptible.state) as string )
			VDBRFunctions.UiReport ("+Job Is Interruptible Changed To ["+ VDBRSettings.IsInterruptible as string +"]")
		)

		on spn_maxServers changed value do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "MaxServers" ( (VDBRSettings.MaxServers = spn_maxServers.value) as string )
			VDBRFunctions.UiReport ("+Max Servers changed to ["+ VDBRSettings.MaxServers as string +"]")
		)

		on spn_portNumber changed value do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "PortNumber" ( (VDBRSettings.PortNumber =  spn_portNumber.value) as string )
			VDBRFunctions.UiReport ("+Port Number changed to ["+ VDBRSettings.PortNumber as string +"]")
		)

		on chk_useIpAddress changed state do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "UseIpAddress" ( (VDBRSettings.UseIpAddress = chk_useIpAddress.state) as string )
			VDBRFunctions.UiReport ("+Use IP Address Changed To ["+ VDBRSettings.UseIpAddress as string +"]")
		)

		on chk_autoUpdate changed state do
		(
			setIniSetting VDBRPaths.IniFile "JobSettings"  "AutoUpdate" ( (VDBRSettings.AutoUpdate = chk_autoUpdate.state) as string )
			VDBRFunctions.UiReport ("+Auto Update Changed To ["+ VDBRSettings.AutoUpdate as string +"]")

			if VDBRSettings.SubmissionSuccessful AND VDBRSettings.SubmissionLastJobID != "failed" then
			(
				if chk_autoUpdate.state then
				(
					VDBRFunctions.StartBackgroundWorker()
					VDBRFunctions.UiReport (">Background Auto-Update Started")
				)
				else
				(
					VDBRFunctions.StopBackgroundWorker()
					VDBRFunctions.UiReport (">Background Auto-Update Stopped")
				)
			)
		)
        
        on chk_autoComplete changed state do
        (
			setIniSetting VDBRPaths.IniFile "JobSettings"  "AutoComplete" ( (VDBRSettings.AutoComplete = chk_autoComplete.state) as string )
			VDBRFunctions.UiReport ("+Auto Complete Changed To ["+ VDBRSettings.AutoComplete as string +"]")
        )

		fn LoadUI =
		(	
			edt_dept.text = getIniSetting VDBRPaths.IniFile "JobSettings" "Department"

			DisplayPoolsList()
			DisplayGroupsList()

			val = getIniSetting VDBRPaths.IniFile "JobSettings" "Pool" 
			if val != "" do 
			(
				defItem = findItem VDBRSettings.Pools val 
				if defItem != 0 do ddl_poollist.selection = defItem 
			)
			
			val = getIniSetting VDBRPaths.IniFile "JobSettings" "Pool2Name" 
			if val != "" do 
			(
				defItem = findItem VDBRSettings.Pools val 
				if defItem != 0 do ddl_pool2list.selection = defItem 
			)

			val = getIniSetting VDBRPaths.IniFile "JobSettings" "Group"
			if val != "" do
			(
				defItem = findItem VDBRSettings.Groups val
				if defItem != 0 do ddl_groups.selection = defItem
			)

			val = getIniSetting VDBRPaths.IniFile "JobSettings" "Priority" 
			if val != "" then
			(
				currPriority = (execute val)
				if currPriority > VDBRSettings.MaximumPriority do currPriority = VDBRSettings.MaximumPriority
				JobPriorityUpdate currPriority
			)
			else
			(
				defPriority = VDBRSettings.MaximumPriority / 2
				JobPriorityUpdate defPriority
			)

			val = getIniSetting VDBRPaths.IniFile "JobSettings" "TaskTimeout"
			if val != "" then spn_taskTimeout.value = execute val

			val = getIniSetting VDBRPaths.IniFile "JobSettings" "IsBlacklist"
			if val != "" do chk_isBlacklist.state = execute val
			
			val = getIniSetting VDBRPaths.IniFile "JobSettings" "IsInterruptible"
			if val != "" do chk_isInterruptible.state = execute val
			
			edt_limitgroups.text = getIniSetting VDBRPaths.IniFile "JobSettings" "LimitGroups"
			edt_machineList.text = getIniSetting VDBRPaths.IniFile "JobSettings" "MachineList"
			
			val = getIniSetting VDBRPaths.IniFile "JobSettings" "MaxServers" 
			if val != "" then spn_maxServers.value = execute val

			val = getIniSetting VDBRPaths.IniFile "JobSettings" "PortNumber"
			if val != "" then spn_portNumber.value = execute val
			
			val = getIniSetting VDBRPaths.IniFile "JobSettings" "UseIpAddress"
			if val != "" do chk_useIpAddress.state = execute val
			
			val = getIniSetting VDBRPaths.IniFile "JobSettings" "AutoUpdate"
			if val != "" do chk_autoUpdate.state = execute val
            
            val = getIniSetting VDBRPaths.IniFile "JobSettings" "AutoComplete"
			if val != "" do chk_autoComplete.state = execute val

			edt_jobId.text = ""
			edt_jobStatus.text = ""

			btn_updateServers.enabled = false
			btn_startRender.enabled = false
			btn_endJob.enabled = false
			edt_jobId.enabled = false
			edt_jobStatus.enabled = false
			lbl_activeServers.enabled = false
			btn_CheckAll.enabled = false
			btn_CheckInvert.enabled = false
			btn_CheckNone.enabled = false
		)

		fn LoadCachedUI =
		(
			edt_jobname.text = VDBRSettings.JobName
			edt_comment.text = VDBRSettings.Comment
			edt_dept.text = VDBRSettings.Department
			
			DisplayPoolsList()
			DisplayGroupsList()

			val = VDBRSettings.PoolName
			if val != "" do 
			(
				defItem = findItem VDBRSettings.Pools val 
				if defItem != 0 do ddl_poollist.selection = defItem 
			)
			
			val = VDBRSettings.Pool2Name
			if val != "" do 
			(
				defItem = findItem VDBRSettings.Pools val 
				if defItem != 0 do ddl_pool2list.selection = defItem 
			)

			val = VDBRSettings.Group
			if val != "" do
			(
				defItem = findItem VDBRSettings.Groups val
				if defItem != 0 do ddl_groups.selection = defItem
			)

			spn_priority.value = VDBRSettings.Priority
			chk_isBlacklist.state = VDBRSettings.IsBlacklist
			spn_taskTimeout.value = VDBRSettings.TaskTimeout
			chk_isInterruptible.state = VDBRSettings.IsInterruptible
			edt_limitgroups.text = VDBRSettings.LimitGroups
			edt_machineList.text = VDBRSettings.MachineList
			spn_maxServers.value = VDBRSettings.MaxServers
			spn_portNumber.value = VDBRSettings.PortNumber
			chk_useIpAddress.state = VDBRSettings.UseIpAddress
			chk_autoUpdate.state = VDBRSettings.AutoUpdate
			chk_autoComplete.state = VDBRSettings.AutoComplete
			
			edt_jobId.text = VDBRSettings.SubmissionLastJobID
			edt_jobStatus.text = VDBRSettings.JobStatus

			btn_startJob.enabled = false
			btn_updateServers.enabled = true
			btn_startRender.enabled = true
			btn_endJob.enabled = true
			edt_jobId.enabled = true
			edt_jobStatus.enabled = true
			lbl_activeServers.enabled = true
			btn_CheckAll.enabled = true
			btn_CheckInvert.enabled = true
			btn_CheckNone.enabled = true
		)

		fn UpdateControls = 
		(
			VDBRSettings.JobName = edt_jobname.text
			VDBRSettings.Comment = edt_comment.text
			VDBRSettings.Department = edt_dept.text
			VDBRSettings.PoolName = ddl_poollist.selected
			VDBRSettings.Pool2Name = ddl_pool2list.selected
			VDBRSettings.Group = ddl_groups.selected
			VDBRSettings.Priority = spn_priority.value
			VDBRSettings.IsBlacklist = chk_isBlacklist.state
			VDBRSettings.TaskTimeout = spn_taskTimeout.value
			VDBRSettings.IsInterruptible = chk_isInterruptible.state
			VDBRSettings.LimitGroups = edt_limitgroups.text
			VDBRSettings.MachineList = edt_machineList.text
			VDBRSettings.MaxServers = spn_maxServers.value
			VDBRSettings.PortNumber = spn_portNumber.value
			VDBRSettings.UseIpAddress = chk_useIpAddress.state
			VDBRSettings.AutoUpdate = chk_autoUpdate.state
			VDBRSettings.AutoComplete = chk_autoComplete.state
		)
	
		fn CreateSubmitInfoFile filename =
		(              
			local submitInfoFile = createFile filename

			if (submitInfoFile != undefined) then
			(
				format "Plugin=VraySpawner\n" to:submitInfoFile
				format "Frames=0-%\n" (VDBRSettings.MaxServers-1) to:submitInfoFile
				format "ChunkSize=1\n" to:submitInfoFile
				format "Priority=%\n" VDBRSettings.Priority to:submitInfoFile
				format "Pool=%\n" VDBRSettings.PoolName to:submitInfoFile
				format "SecondaryPool=%\n"  VDBRSettings.Pool2Name to:submitInfoFile
				local jobName = VDBRFunctions.GetSubmittedJobName()
				format "Name=%\n" jobName to:submitInfoFile
				format "Comment=%\n" VDBRSettings.Comment to:submitInfoFile
				format "Department=%\n" VDBRSettings.Department to:submitInfoFile
				format "Group=%\n" VDBRSettings.Group to:submitInfoFile
				format "LimitGroups=%\n" VDBRSettings.LimitGroups to:submitInfoFile
                format "TaskTimeoutMinutes=%\n" VDBRSettings.TaskTimeout to:submitInfoFile
                format "OnTaskTimeout=Complete\n" to:submitInfoFile

				if VDBRSettings.IsBlacklist then
					format "Blacklist=%\n" VDBRSettings.MachineList to:submitInfoFile
				else
					format "Whitelist=%\n" VDBRSettings.MachineList to:submitInfoFile
				
				if VDBRSettings.IsInterruptible then
					format "Interruptible=true\n" to:submitInfoFile

				close submitInfoFile
				true
			)
			else
				false
		)
	
		fn CreateJobInfoFile filename =
		(
			local JobInfoFile = createFile filename
			if (JobInfoFile != undefined) then
			(
				local version = VDBRFunctions.GetMaxVersion()
				if VDBRFunctions.getRendererIdString() == "vrayrt" then
					version = "RT" + (version as string)
				format "Version=Max%\n" version to:JobInfoFile

				--VRay RT only
				if VDBRFunctions.getRendererIdString() == "vrayrt" then
				(
					format "PortNumber=%\n" spn_portNumber.value to:JobInfoFile
				)
					
				Close JobInfoFile
				true
			)
			else
				false
		)
		
		fn SubmitJob =
		(
			--save the artists DR settings on their workstation for later restore
			VDBRFunctions.StoreDRSettings configFile:VDBRPaths.ConfigFile

			VDBRSettings.SubmissionSuccessful = false
			VDBRSettings.SubmissionLastJobID = "failed"
			
			reopenRenderSceneDialog = false
			if renderSceneDialog.isOpen() then
			(
				renderSceneDialog.Close()
				reopenRenderSceneDialog = true
				VDBRFunctions.UiReport ("+Render Dialog Closed.")
			)

			--Max 2012 or earlier, ensure Backburner 'Net Render' checkbox is disabled in the Render Scene Dialog.
			if rendusenet do
			(
				rendusenet = false
				VDBRFunctions.UiReport ("Disabling Backburner 'Net Render'.")
			)
			
			ReportSubmissionSettings()

			VDBRFunctions.UiReport (">Submitting VRay Spawner Job to Deadline...")
			
			if ((CreateSubmitInfoFile VDBRPaths.SubmitInfoFile) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Submit Info file"
			if ((CreateJobInfoFile VDBRPaths.JobInfoFile) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Job Info file"
			
			local arguments = "\"" + VDBRPaths.SubmitInfoFile + "\" \"" + VDBRPaths.JobInfoFile + "\""				
			retcode = VDBRFunctions.WaitForCommandToComplete arguments 3600
			
			local resultFile = openFile VDBRPaths.SubmitOutput
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
				VDBRSettings.SubmissionSuccessful = true
				VDBRSettings.SubmissionLastJobID = "failed"
				theStringStream = renderMsg as stringStream
				skipToString theStringStream "JobID="
				try(VDBRSettings.SubmissionLastJobID = readline theStringStream)catch()
				close theStringStream
				("Job submitted successfully.\n\n" + renderMsg)
			)	
			else
				("DEADLINE JOB SUBMISSION:\n\nFailed to submit job.\n\n" + renderMsg)
		)
		
		fn UpdateJob =
		(
			if VDBRSettings.SubmissionLastJobID != "failed" then
			(
				edt_jobId.text = VDBRSettings.SubmissionLastJobID
				
				jobState = GetJobStatus()
				if jobState != "Active" then --job is dead
				(
					VDBRSettings.SubmissionLastJobID = "failed"
					VDBRSettings.SubmissionSuccessful = false
					
					if not VDBRSettings.DialogAttached then
					(
						MessageBox ("The spawner job is no longer active, it is now " + jobState + ".") title:"Job Status Changed"
					)
					
					VDBRFunctions.UiReport ( "The spawner job is no longer active, it is now " + jobState + "." ) LogFileOnly:true
					ResetSpawnerControls()
				)
				else --job is still active
				(
					SetMaxServers()

					result = VDBRFunctions.CollectRenderingSlaves()

					serverCount = 0
					
					if result != #commandFailed do
					(
						updateListView()

-- 						VDBRFunctions.UiReport ( "SlaveNames: " + (VDBRSettings.SlaveNames as string) )
-- 						VDBRFunctions.UiReport ( "SlavesToUse: " + (VDBRSettings.SlaveNamesToUse as string) )
-- 						VDBRFunctions.UiReport ( "SlavesToIgnore: " + (VDBRSettings.SlaveNamesToIgnore as string) )

						serverCount = VDBRSettings.SlaveNamesToUse.count
						
						settingLines = #()

						-- VRay renderer
						if VDBRFunctions.getRendererIdString() == "vray" then
						(
							local configFile = openFile VDBRPaths.DRConfigFile mode:"rt"
							if (configFile != undefined) then
							(
								while (not eof configFile) do
								(
									line = (readLine configFile)
									if (matchPattern line pattern:"restart_slaves *") do
									(
										append settingLines line --Add "restart_slaves *" line to array
										while (not eof configFile) do
										(
											line = (readLine configFile)
											append settingLines line
										)
									)
								)
									
								close configFile
							)
							
							local configFile = openFile VDBRPaths.DRConfigFile mode:"wt"
							if (configFile != undefined) then
							(
								for slaveName in VDBRSettings.SlaveNamesToUse do
									if slaveName != "" do
										format "% 1 %\n" slaveName VDBRSettings.PortNumber to:configFile

								for slaveName in VDBRSettings.SlaveNamesToIgnore do
									if slaveName != "" do
										format "% 0 %\n" slaveName VDBRSettings.PortNumber to:configFile
									
								for i in 1 to settingLines.count do --Ensure certain VRay settings are disabled
								(
									if settingLines[i] == "list_in_scene 1" do settingLines[i] = "list_in_scene 0"
									if (substring (settingLines[i] as string) 1 11) == "max_servers" do settingLines[i] = "max_servers 0"
								)

								for settingLine in settingLines do
									format "%\n" settingLine to:configFile
									
								close configFile
							)
						)
						else
						(
							-- VRay RT renderer
							if VDBRFunctions.getRendererIdString() == "vrayrt" then
							(
								local configFile = openFile VDBRPaths.RTDRConfigFile mode:"rt"
								if (configFile != undefined) then
								(
									while (not eof configFile) do
									(
										line = (readLine configFile)
										if (matchPattern line pattern:"autostart_local_slave *") do
										(
											append settingLines line --Add "autostart_local_slave *" line to array
											while (not eof configFile) do
											(
												line = (readLine configFile)
												append settingLines line
											)
										)
									)
										
									close configFile
								)
								
								local configFile = openFile VDBRPaths.RTDRConfigFile mode:"wt"
								if (configFile != undefined) then
								(
									for slaveName in VDBRSettings.SlaveNamesToUse do
										if slaveName != "" do
											format "% 1 %\n" slaveName VDBRSettings.PortNumber to:configFile

									for slaveName in VDBRSettings.SlaveNamesToIgnore do
										if slaveName != "" do
											format "% 0 %\n" slaveName VDBRSettings.PortNumber to:configFile
										
									for settingLine in settingLines do
										format "%\n" settingLine to:configFile
										
									close configFile
								)
							)

						)
					VDBRFunctions.UiReport ("Updated Active Server List.")
					)
					
					if jobState != "" then
					(
						if jobState == "Active" then
						(
							if serverCount > 0 then
								jobState = "Rendering"
							else
								jobState = "Queued"
						)
					
						edt_jobStatus.text = (VDBRSettings.JobStatus = jobState)
					)
				)
			)
		)

		---------------------------
		--USER INTERFACE HANDLERS--
		---------------------------
		on VDBR_MainRollout open do
		(
			if not VDBRSettings.DialogAttached AND not VDBRSettings.DialogReOpening then
			(
				--start log file
				local allTodaysFiles = getFiles (VDBRPaths.LogsDir + "SetupVRayWithDeadline - ["+ sysinfo.computerName +"] " + VDBRFunctions.getDayString() + "*.log")
				sort allTodaysFiles
				local lastFileNumber = 0
				if allTodaysFiles.count > 0 do
				(
					lastFileNumber = getFileNameFile allTodaysFiles[allTodaysFiles.count]
					lastFileNumber = substring lastFileNumber (lastFileNumber.count-3) 4
					lastFileNumber = (lastFileNumber as integer + 1)
				)
				VDBRSettings.TodaysLogFileName = VDBRPaths.LogsDir + "SetupVRayWithDeadline - ["+ sysinfo.computerName +"] " + VDBRFunctions.getDayString() + VDBRFunctions.GetZeros lastFileNumber + lastFileNumber as string + ".log"
			)
			if not doesFileExist VDBRSettings.TodaysLogFileName then
			(
				VDBRSettings.TodaysLogFile = createFile VDBRSettings.TodaysLogFileName
				local timeArray = getLocalTime()
				local hour = if timeArray[5] < 10 then (hour = "0" + (timeArray[5] as string)) else (hour = (timeArray[5] as string))
				local minute = if timeArray[6] < 10 then (minute = "0" + (timeArray[6] as string)) else (minute = (timeArray[6] as string))
				local second = if timeArray[7] < 10 then (second = "0" + (timeArray[7] as string)) else (second = (timeArray[7] as string))
				local timeString = (timeArray[4] as string) + "-" + (timeArray[2] as string) + "-" + (timeArray[1] as string) + " " + hour + ":" + minute + ":" + second
				format "-- BEGIN - % - %/% - 3ds Max %\n" timeString sysinfo.computerName sysinfo.userName (VDBRFunctions.GetMaxVersion()) to:VDBRSettings.TodaysLogFile
				VDBRFunctions.UiReport ("---- OPEN DIALOG ----") LogFileOnly:true AddTimeStamp:false
			)    
			else
			(
				if not VDBRSettings.DialogAttached AND not VDBRSettings.DialogReOpening then
				(
					VDBRFunctions.UiReport ("---- OPEN DIALOG ----") LogFileOnly:true AddTimeStamp:false
				)
				else
					VDBRFunctions.UiReport ("---- RE-OPENING DIALOG ----") LogFileOnly:true AddTimeStamp:false
			)

			if not VDBRSettings.DialogAttached AND not VDBRSettings.DialogReOpening then
			(
				callbacks.removeScripts id:#VDBR_StatusMessages
				callbacks.addScript #preRender "try(VDBRFunctions.PreRenderStatus())catch()" id:#VDBR_StatusMessages
				callbacks.addScript #postRender "try(VDBRFunctions.PostRenderStatus())catch()" id:#VDBR_StatusMessages
			)

			initReportWindow() --init .NET log report window

			if not VDBRSettings.DialogAttached AND not VDBRSettings.DialogReOpening then VDBRFunctions.UiReport (">Building UI...") else VDBRFunctions.UiReport (">Reloading UI...")

			if VDBRSettings.MaximumPriority == -1 do
			(
				VDBRFunctions.GetMaximumPriority()
				spn_priority.range = [0,VDBRSettings.MaximumPriority,VDBRSettings.MaximumPriority / 2]
			)
			
			spn_taskTimeout.range = [0,10000,0]

			if VDBRSettings.Pools.count == 0 do VDBRFunctions.CollectPools()
			if VDBRSettings.Groups.count == 0 do VDBRFunctions.CollectGroups()

			if not VDBRSettings.DialogAttached AND not VDBRSettings.DialogReOpening then
			(
				VDBRFunctions.UiReport (">Loading UI Presets...")
				LoadUI() --load from INI file
				UpdateControls()
			)
			else
			(
				VDBRFunctions.UiReport (">Reloading UI Presets...")
				LoadCachedUI() --load from struct cache if DialogAttached
			)

			if not VDBRSettings.DialogAttached AND not VDBRSettings.DialogReOpening AND getfilenamefile maxfilename != "" do ( VDBRSettings.JobName = (edt_jobname.text = getfilenamefile maxfilename) as string )

			initListView()

			if not VDBRSettings.DialogAttached AND not VDBRSettings.DialogReOpening then VDBRFunctions.UiReport ("+Ready.") else VDBRFunctions.UiReport ("+Reloaded.")

			UpdateJob()

			--VDBRFunctions.UiReport ( ">DEBUG: VDBRSettings.SubmissionLastJobID: " + (VDBRSettings.SubmissionLastJobID as string) )

			if VDBRSettings.SubmissionLastJobID != "failed" AND VDBRSettings.SubmissionLastJobID != "" do
			(
				jobState = GetJobStatus()

				--VDBRFunctions.UiReport ( ">DEBUG: Job State: " + (jobState as string) )

				if jobState == "Active" then --if job still active
				(
					--VDBRFunctions.UiReport ( ">DEBUG: DialogAttached: " + (VDBRSettings.DialogAttached as string) )
					--VDBRFunctions.UiReport ( ">DEBUG: DialogReOpening: " + (VDBRSettings.DialogReOpening as string) )

					if VDBRSettings.DialogReOpening do VDBRFunctions.ScanForDialog() --ScanForDialog function should be re-enabled if job is still running after rendering
					if VDBRSettings.AutoUpdate do VDBRFunctions.StartBackgroundWorker() --Start Background Worker if job still running & AutoUpdate is enabled
				)
			)
		)
		
		on VDBR_MainRollout close do
		(
			VDBRFunctions.StopBackgroundWorker()

			if not VDBRSettings.DialogIgnoreClose then
			(
				VDBRFunctions.UiReport ("---- QUIT DIALOG ----") LogFileOnly:true AddTimeStamp:false

				if VDBRSettings.SubmissionSuccessful do
				(
					messageBox "The VRay Spawner job will be completed." title:"Warning"
					CompleteJob()
					VDBRFunctions.UiReport (">Job has been Completed.") LogFileOnly:true
				)

				callbacks.removeScripts id:#VDBR_UnRegisterDialog
				callbacks.removeScripts id:#VDBR_ReOpenDialog
				callbacks.removeScripts id:#VDBR_StatusMessages

				local timeArray = getLocalTime()
				local hour = if timeArray[5] < 10 then (hour = "0" + (timeArray[5] as string)) else (hour = (timeArray[5] as string))
				local minute = if timeArray[6] < 10 then (minute = "0" + (timeArray[6] as string)) else (minute = (timeArray[6] as string))
				local second = if timeArray[7] < 10 then (second = "0" + (timeArray[7] as string)) else (second = (timeArray[7] as string))
				local timeString = (timeArray[4] as string) + "-" + (timeArray[2] as string) + "-" + (timeArray[1] as string) + " " + hour + ":" + minute + ":" + second
				format "-- END - % - %/% - 3ds Max %\n" timeString sysinfo.computerName sysinfo.userName (VDBRFunctions.GetMaxVersion()) to:VDBRSettings.TodaysLogFile
				close VDBRSettings.TodaysLogFile
				--closeLog() --DEBUG only
			)
			else
			(
				VDBRFunctions.UiReport ("---- CLOSING DIALOG ----") LogFileOnly:true AddTimeStamp:false
				--flushLog() --DEBUG only
			)
		)

		--Only restore user's original DR settings if the user clicks to close our UI
		on VDBR_MainRollout oktoclose do
		(
			VDBRFunctions.RestoreDRSettings configFile:VDBRPaths.ConfigFile --restore the artist's DR settings on their workstation
			true
		)
		
		on VDBR_MainRollout moved pos do VDBRFunctions.SaveWinPos()
		
		on btn_startJob pressed do 
		(
			VDBRFunctions.UiReport (">Job Submission Started...")

			-- VRay renderer
			if VDBRFunctions.getRendererIdString() == "vray" then
			(
				startJob = true
				if not renderers.current.system_distributedRender then
				(
					if queryBox "VRay distributed rendering must be enabled before reserving servers. Would you like to enable it now?" title:"Question" then
                    (
                        VDBRSettings.revertVRayDistributedEnabled = true
						renderers.current.system_distributedRender = true
                    )
					else
						startJob = false
				)
				
				VDBRPaths.ConfigFile = VDBRPaths.DRConfigFile
				VDBRFunctions.UiReport (">Config File: " + VDBRPaths.ConfigFile) LogFileOnly:true
				
				--Check Config File exists
				if not doesFileExist VDBRPaths.ConfigFile do VDBRFunctions.CreateConfigFile()

				--Check File Permissions on Config File
				if (getFileSecurityInfo VDBRPaths.ConfigFile #read) AND (getFileSecurityInfo VDBRPaths.ConfigFile #write) then
					startJob = true
				else
				(
					startJob = false
					VDBRFunctions.UiReport ("--Config File Access Permissions Invalid")
				)

				if startJob do
				(
					theMessage = SubmitJob()
					VDBRFunctions.UiReport theMessage
					VDBRFunctions.UiReport ("+Ready.")

					edt_jobId.text = ""
					edt_jobStatus.text = ""
					lv_activeServers.Items.clear()
					
					if VDBRSettings.SubmissionSuccessful do
					(
						if VDBRSettings.SubmissionLastJobID != "failed" do
							edt_jobId.text = VDBRSettings.SubmissionLastJobID
					
						btn_startJob.enabled = false
						btn_updateServers.enabled = true
						btn_startRender.enabled = true
						btn_endJob.enabled = true
						edt_jobId.enabled = true
						edt_jobStatus.enabled = true
						lbl_activeServers.enabled = true
						VDBRSettings.MaxServers = spn_maxServers.value
						VDBRSettings.CurrentMax = spn_maxServers.value

						if chk_autoUpdate.state do VDBRFunctions.StartBackgroundWorker()
						VDBRFunctions.ScanForDialog()
						if not VDBRSettings.IsUpdatingList do UpdateJob()
					)
				)
			)
			else 
			(
				-- VRay RT renderer
				if VDBRFunctions.getRendererIdString() == "vrayrt" then
				(
			
					startJob = true
					if not renderers.current.distributed_rendering then
					(
						if queryBox "VRay RT distributed rendering must be enabled before reserving servers. Would you like to enable it now?" title:"Question" then
						(
							VDBRSettings.revertVRayDistributedEnabled = true
							renderers.current.distributed_rendering = true
						)
						else
							startJob = false
					)

					VDBRPaths.ConfigFile = VDBRPaths.RTDRConfigFile
					VDBRFunctions.UiReport (">Config File: " + VDBRPaths.ConfigFile) LogFileOnly:true
					
					--Check Config File exists
					if not doesFileExist VDBRPaths.ConfigFile do VDBRFunctions.CreateConfigFile()

					--Check File Permissions on Config File
					if (getFileSecurityInfo VDBRPaths.ConfigFile #read) AND (getFileSecurityInfo VDBRPaths.ConfigFile #write) then
						startJob = true
					else
					(
						startJob = false
						VDBRFunctions.UiReport ("--Config File Access Permissions Invalid")
					)
					
					if startJob do
					(
						theMessage = SubmitJob()
						VDBRFunctions.UiReport theMessage
						VDBRFunctions.UiReport ("+Ready.")

						edt_jobId.text = ""
						edt_jobStatus.text = ""
						lv_activeServers.Items.clear()
						
						if VDBRSettings.SubmissionSuccessful do
						(
							if VDBRSettings.SubmissionLastJobID != "failed" do
								edt_jobId.text = VDBRSettings.SubmissionLastJobID
						
							spn_portNumber.enabled = false
							btn_startJob.enabled = false
							btn_updateServers.enabled = true
							btn_startRender.enabled = true
							btn_endJob.enabled = true
							edt_jobId.enabled = true
							edt_jobStatus.enabled = true
							lbl_activeServers.enabled = true
							VDBRSettings.MaxServers = spn_maxServers.value
							VDBRSettings.CurrentMax = spn_maxServers.value

							if chk_autoUpdate.state do VDBRFunctions.StartBackgroundWorker()
							VDBRFunctions.ScanForDialog()
							if not VDBRSettings.IsUpdatingList do UpdateJob()
						)
					)
				
				)
				else
					MessageBox "The current renderer is neither VRay nor VRay RT. Please choose one of the two as the current renderer before reserving servers." title:"Error"
			)
		)
		
		on btn_updateServers pressed do
		(
			if not VDBRSettings.IsUpdatingList do UpdateJob()
		)
		
		on btn_endJob pressed do
		(
			if queryBox "This will complete the VRay Spawner job. Do you wish to continue?" title:"Warning" then
			(
				CompleteJob()
				VDBRFunctions.UiReport (">Job has been Completed.")
			)
		)

		on btn_startRender pressed do
		(
			--Ensure latest listView configuration is applied to the vray *.cfg file before attempting render.
			if not VDBRSettings.IsUpdatingList do UpdateJob()

			if VDBRSettings.SlaveNamesToUse.count > 0 then
			(
				-- VRay renderer
				if VDBRFunctions.getRendererIdString() == "vray" then
				(
					startRender = true
					if not renderers.current.system_distributedRender then
					(
						if queryBox "VRay distributed rendering must be enabled before starting the render. Would you like to enable it now?" title:"Question" then
							renderers.current.system_distributedRender = true
						else
							startRender = false
					)
			
					if startRender do
					(
						max quick render					
						VDBRFunctions.UiReport ("+Render Finished.")
	                    if VDBRSettings.AutoComplete then
	                    (
	                        CompleteJob()
	                        VDBRFunctions.UiReport (">Job has been Completed.")
	                    )
					)
				)
				else 
				(
					-- VRay RT renderer
					if VDBRFunctions.getRendererIdString() == "vrayrt" then
					(
						startRender = true
						if not renderers.current.distributed_rendering then
						(
							if queryBox "VRay RT distributed rendering must be enabled before starting the render. Would you like to enable it now?" title:"Question" then
								renderers.current.distributed_rendering = true
							else
								startRender = false
						)
				
						if startRender do
						(
							max quick render					
							VDBRFunctions.UiReport ("+Render Finished.")
							if VDBRSettings.AutoComplete then
							(
							    CompleteJob()
							    VDBRFunctions.UiReport (">Job has been Completed.")
							)
						)
					)
					else
						MessageBox "VRay RT is not the current renderer. Please make it the current renderer before starting the render." title:"Error"
				)
			)
			else
				MessageBox "At least one Deadline Slave needs to be ENABLED in the Active Servers List!" title:"Error"
		)

	)
	
	VDBRFunctions.GetWinPos()
	
	CreateDialog VDBR_MainRollout pos:VDBRSettings.WinPos style:#(#style_titlebar, #style_border, #style_sysmenu, #style_minimizebox)
)
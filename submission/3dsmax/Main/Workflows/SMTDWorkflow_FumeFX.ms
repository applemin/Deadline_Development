(
	global SMTDWorkflow_FumeFX
	global SMTD_FumeFXRollout 
	global SMTD_FumeFXOptionsRollout
	rollout SMTD_FumeFXRollout "FumeFX Simulations"
	(
		local isUpdating = false
		
		button btn_checkAll "Check All" align:#left across:3 height:20 offset:[-10,-5] width:105
		button btn_invert "Invert" align:#center height:20 offset:[-80,-5] width:105
		button btn_updateObjects "Update FumeFX Objects From The Scene..." height:20 align:#right offset:[10,-5] width:260
		dotNetControl dnc_fumeFXSims "System.Windows.Forms.ListView" width:480 height:120 align:#center
		
		edittext edt_SimCacheOutput "Simulation Cache Output Directory Override:" fieldWidth:452 labelOnTop:true align:#left across:2 offset:[-10,-2]
		button btn_SimCacheOutput "..." align:#right offset:[9,15] width:25 height:18
		
		checkbox chk_UseSimCacheOutput "Use Cache Output Directory Override" across:2 align:#left offset:[-10,-2]
		checkbox chk_PermanentSceneChange "Make Directory Override Changes Permanent" align:#right  offset:[10,-2]
				
		fn initListView lv=
		(
			lv.gridLines = true  
			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.fullRowSelect = true 
			lv.checkboxes = true
			lv.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r (SMTD_ColorPalette.maxBgColor.g+5) (SMTD_ColorPalette.maxBgColor.b+15)
			lv.LabelEdit = false
			local column1 = lv.Columns.add "FumeFX Simulator" 150
			local column2 = lv.Columns.add "Simulation Path" 320
		)
		fn populateListView lv =
		(
			isUpdating = true
			local theFumeFXObjects = for o in objects where classof o == FumeFX collect o
			lv.items.clear()
			local theRange = #()
			for i in theFumeFXObjects do
			(
				local li = dotNetObject "System.Windows.Forms.ListViewItem" i.name
				li.checked = findItem ::SMTDWorkflow_FumeFX.FumeFXObjectsToSim i.name > 0
				local thePath = try( (i.GetPath #default)+"####.fxd" )catch("")
				local sub_li = li.SubItems.add thePath
				append theRange li
			)	
			lv.Items.AddRange theRange
			isUpdating = false
		)
		
		fn selectHighlightedObject =														--Function to select the highlighted object from the ListView in the Max Modify Panel
		(
			select (for i = 1 to dnc_fumeFXSims.items.count where dnc_fumeFXSims.items.item[i-1].Selected and isValidNode (theNode = getNodeByName dnc_fumeFXSims.items.item[i-1].Text) collect theNode)  --Collect and select the object that is highlighted
			max modify mode																	--Switch the 3ds Max Command Panel to Modify mode
		)--end fn
		
		fn exploreHighlightedOutput =
		(
			for i = 1 to dnc_fumeFXSims.items.count where dnc_fumeFXSims.items.item[i-1].Selected do try(shellLaunch (getFileNamePath dnc_fumeFXSims.items.item[i-1].subItems.Item[1].text) "")catch()
		)--end fn
		
		on btn_checkAll pressed do 
		(
			::SMTDWorkflow_FumeFX.FumeFXObjectsToSim = for o in objects where classof o == FumeFX collect o.name	--collect all object names
			populateListView dnc_fumeFXSims																			--Populate the content of the ListView
			try(SMTD_MainRollout.updateSubmitButtonState())catch()													--Update the enabled state and text of the SUBMIT button
		)
		on btn_invert pressed do
		(
			::SMTDWorkflow_FumeFX.FumeFXObjectsToSim = for o in objects where classof o == FumeFX and findItem ::SMTDWorkflow_FumeFX.FumeFXObjectsToSim o.name == 0 collect o.name
			populateListView dnc_fumeFXSims																		--Populate the content of the ListView
			try(SMTD_MainRollout.updateSubmitButtonState())catch()												--Update the enabled state and text of the SUBMIT button
		)
		
		on btn_updateObjects pressed do 																		--If the Update button was pressed,
		(
			populateListView dnc_fumeFXSims																		--Populate the content of the ListView
			try(SMTD_MainRollout.updateSubmitButtonState())catch()												--Update the enabled state and text of the SUBMIT button
		)
		
		on btn_SimCacheOutput pressed do																		--If the user pressed the Browse... button for the Output Override path,
		(
			local simCacheOutputString = getSavePath caption:"Set Simulation Cache Output Location" initialdir:(::SMTDWorkflow_FumeFX.SimCacheOutput)  --Open a Save Path dialog at the current location, if any
			if simCacheOutputString != undefined do 															--If a valid path was selected, 
			(
				::SMTDWorkflow_FumeFX.SimCacheOutput = simCacheOutputString									--assign the new path to the UI control
				setINISetting SMTDPaths.InIFile "PhoenixFDWorkflow" "DeadlineSimOutputOverride" (edt_SimCacheOutput.text = ::SMTDWorkflow_FumeFX.SimCacheOutput)
				::SMTDWorkflow_FumeFX.UseSimCacheOutput = chk_UseSimCacheOutput.checked = true				--Check the checkbox to use the Override that was just picked
				::SMTDWorkflow_FumeFX.storeSettings()
				populateListView dnc_fumeFXSims																				--Update the ListView to show the new path in the third column
			)
			chk_UseSimCacheOutput.enabled = doesFileExist edt_SimCacheOutput.text			
			try(SMTD_MainRollout.updateSubmitButtonState())catch()												--Update the SUBMIT button's text and enabled state
		)--end on pressed handler

		on edt_SimCacheOutput entered txt do 																	--If an Output Override path was entered manually, update the SUBMIT button
		(
			setINISetting SMTDPaths.InIFile "PhoenixFDWorkflow" "DeadlineSimOutputOverride" (::SMTDWorkflow_FumeFX.SimCacheOutput = edt_SimCacheOutput.text)
			::SMTDWorkflow_FumeFX.storeSettings()
			chk_UseSimCacheOutput.enabled = doesFileExist edt_SimCacheOutput.text
			try(SMTD_MainRollout.updateSubmitButtonState())catch()
		)

		
		on chk_UseSimCacheOutput changed state do
		(
			::SMTDWorkflow_FumeFX.UseSimCacheOutput = state
			::SMTDWorkflow_FumeFX.storeSettings()
		)
		on chk_PermanentSceneChange changed state do
		(
			::SMTDWorkflow_FumeFX.PermanentSceneChange = state
			::SMTDWorkflow_FumeFX.storeSettings()
		)
		
		on dnc_fumeFXSims mouseClick arg do													--If the user clicked an item with the mouse button,
		(
			rcmenu ffx_rcmenu 																--Define a right-click menu to display
			(
				menuitem mnu_selectObject "Select Highlighted Object In The Scene"			--Menu item to select the highlighed object
				separator sep_10
				menuitem mnu_explorePath "Explore Simulation Path Of Highlighted Object"	--Menu item to explore the output path
				
				on mnu_selectObject picked do SMTD_FumeFXRollout.selectHighlightedObject()	--If the menu item was picked from the menu, call the function to select the highlighted object defined earluer in the scope of the rollout
				on mnu_explorePath picked do SMTD_FumeFXRollout.exploreHighlightedOutput()	--If the menu item was picked from the menu, call the function to explore the simulation path defined earluer in the scope of the rollout
			)--end rcmenu
			if arg.Button == arg.Button.Right do popupmenu ffx_rcmenu pos:mouse.screenpos	--If the right mouse button was pressed, pop up the rcmenu at the current screen position of the mouse cursor
		)--end on mouseClicked handler
		
		on dnc_fumeFXSims MouseDoubleClick arg do 											--If the user double-clicked an item on the ListView,
		(
			if not isUpdating do 															--If the handler is not called by the ListView during its update,
				for i = 1 to dnc_fumeFXSims.items.count do 
					if dnc_fumeFXSims.items.item[i-1].checked then
						appendIfUnique ::SMTDWorkflow_FumeFX.FumeFXObjectsToSim dnc_fumeFXSims.items.item[i-1].Text
					else 
						try(deleteItem ::SMTDWorkflow_FumeFX.FumeFXObjectsToSim (findItem ::SMTDWorkflow_FumeFX.FumeFXObjectsToSim dnc_fumeFXSims.items.item[i-1].Text))catch()
			try(SMTD_MainRollout.updateSubmitButtonState())catch()							--Update the SUBMIT button's enabled state and text
		)--end on MouseDoubleClick handler
		
		on dnc_fumeFXSims ItemChecked arg do 												--If the user checked/unchecked an item on the ListView,
		(
			if not isUpdating do 															--If the handler is not called by the ListView during its update,
				for i = 1 to dnc_fumeFXSims.items.count do 
					if dnc_fumeFXSims.items.item[i-1].checked then
						appendIfUnique ::SMTDWorkflow_FumeFX.FumeFXObjectsToSim dnc_fumeFXSims.items.item[i-1].Text
					else 
						try(deleteItem ::SMTDWorkflow_FumeFX.FumeFXObjectsToSim (findItem ::SMTDWorkflow_FumeFX.FumeFXObjectsToSim dnc_fumeFXSims.items.item[i-1].Text))catch()
			try(SMTD_MainRollout.updateSubmitButtonState())catch()							--Update the SUBMIT button's enabled state and text
		)--end on ItemChecked handler
		
		on SMTD_FumeFXRollout open do
		(
			initListView dnc_fumeFXSims
			populateListView dnc_fumeFXSims
			edt_SimCacheOutput.text = ::SMTDWorkflow_FumeFX.SimCacheOutput
			chk_UseSimCacheOutput.state = ::SMTDWorkflow_FumeFX.UseSimCacheOutput
			chk_PermanentSceneChange.state = ::SMTDWorkflow_FumeFX.PermanentSceneChange
		)
	)
	rollout SMTD_FumeFXOptionsRollout "FumeFX Job Options"
	(
		local VSpacing = 21
		checkbox chk_limitEnabled "Limit: " pos:[300,2] across:2
		spinner spn_machineLimit "Machines: " range:[1,1000,1] type:#integer align:#right fieldwidth:40 offset:[0,-4]

		checkbox chk_TaskTimeoutEnabled "Task Timeout  " align:#left pos:[5,2+VSpacing] across:4
		spinner spn_task_timeout_hours "Hours:" type:#integer align:#right fieldwidth:40 range:[0,24,0] offset:[-14,-1] tooltip:"Task Timeout HOURS"
		spinner spn_task_timeout_minutes "Minutes:" type:#integer align:#right fieldwidth:40 range:[0,59,0] offset:[-9,-1] tooltip:"Task Timeout MINUTES"
		spinner spn_task_timeout_seconds "Seconds:" type:#integer align:#right fieldwidth:40 range:[0,59,0] offset:[0,-1] tooltip:"Task Timeout SECONDS"
		
		checkbox chk_autoTimeout "Enable Auto Task Timeout  " pos:[5,5+VSpacing*2] align:#left
		checkbox chk_restartMax "Restart 3ds Max Between Tasks  " pos:[300,5+VSpacing*2] align:#left
		checkbox chk_interruptible "Job Is Interruptible  " pos:[300,5+VSpacing*3] align:#left
		
		button btn_concurrentTasks "Concurrent Tasks:  " width:115 height:20 border:false pos:[5,2+VSpacing*3] 
		dropdownlist ddl_concurrentTasks "" items:#("None (1 Task)","2 Concurrent Tasks","3 Concurrent Tasks","4 Concurrent Tasks","5 Concurrent Tasks","6 Concurrent Tasks","7 Concurrent Tasks","8 Concurrent Tasks","9 Concurrent Tasks","10 Concurrent Tasks","11 Concurrent Tasks","12 Concurrent Tasks","13 Concurrent Tasks","14 Concurrent Tasks","15 Concurrent Tasks","16 Concurrent Tasks") \
			align:#right width:160 height:20 pos:[120,2+VSpacing*3] 
				
		checkbox chk_limitConcurrentTasks "Limit Tasks To Slave's Task Limit  " align:#left pos:[300,5+VSpacing*4]
		
		button btn_onComplete "On Job Completion  " width:115 height:20 border:false pos:[5,2+VSpacing*4]  
		dropdownlist ddl_onComplete items:#("Nothing", "Archive", "Delete") width:160 pos:[120,2+VSpacing*4]
			
		checkbox chk_submitAsSuspended "Submit Job As Suspended  " align:#left pos:[300,5+VSpacing*5]
		
		button btn_MaxVersionToForce "Force 3ds Max Build:" align:#left pos:[5,2+VSpacing*5] width:115 height:20 border:false
		dropdownlist ddl_MaxVersionToForce items:#("none", "32bit", "64bit") width:160 pos:[120,2+VSpacing*5] 
		
		
		--ROLLOUT FUNCTIONS--
		fn updateTooltips =
		(
			chk_limitEnabled.tooltip = "When checked, only the number of Slaves specified by the Machines: value will be allowed to dequeue the job.\n\nWhen unchecked, any number of Slaves can work on the job."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "LimitEnabled")
			spn_machineLimit.tooltip = "Defines the number of Slaves that will be allowed to dequeue the job at the same time." + (SMTDFunctions.getStickyTooltipText "JobSettings" "MachineLimit")
			
			chk_TaskTimeoutEnabled.tooltip = "When checked, a task will be requeued if it runs longer than the specified time.\n\nThis is useful when the typical rendering time of the job is known from previous submissions and will prevent stalling." + (SMTDFunctions.getStickyTooltipText "JobSettings" "TaskTimeoutEnabled")
			chk_autoTimeout.tooltip = "Enables the Auto Task Timeout option." + (SMTDFunctions.getStickyTooltipText "JobSettings" "AutoTaskTimeout")
			chk_restartMax.tooltip = "When unchecked (default), 3ds Max will be kept in memory for the duration of the give job's processing. This can reduce render time significantly as multiple Tasks can be rendered in sequence without reloading 3ds Max.\n\nWhen checked, 3ds Max will be restarted between tasks, thus releasing all memory and resetting the scene settings at cost of startup time."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "RestartMax")
			chk_interruptible.tooltip = "When checked, the Job may be interrupted by any other Job that is assigned to the same Pool and has a higher Priority.\n\nUse with caution!"+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "JobIsInterruptible")
			local theTooltipText = "Defines the number of Tasks a single Slave can pick up at once (by launching multiple instances of 3ds Max on the same machine).\n\nNote that only one Deadline license will be used, but if rendering in Workstation Mode, multiple licenses of 3ds Max might be required.\n\nThis is useful to maximize performance when the tasks don't saturate all CPUs at 100% and don't use up all memory."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "MaxTasksPerSlave" isList:ddl_concurrentTasks.items)
			btn_concurrentTasks.tooltip = theTooltipText
			try(ddl_concurrentTasks.tooltip = theTooltipText)catch()
			local theTooltipText = "Defines the action to perform when the job has completed rendering successfully.\n\nThe job can be either left untouched, ARCHIVED to improve Repository performance, or automatically DELETED from the Repository."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "MaxTasksPerSlave" isList:ddl_onComplete.items ) 
			btn_onComplete.tooltip = theTooltipText
			try(ddl_onComplete.tooltip = theTooltipText)catch()
			chk_limitConcurrentTasks.tooltip = "When checked, the number of Concurrent Tasks will be limited by the Slave's Task Limit which is typically set to the number of available CPUs.\n\nFor example, if 'Concurrent Tasks' is set to 16 but a Slave has 8 cores, only 8 concurrent tasks will be processed."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "LimitTasksToNumberOfCpus")
			chk_submitAsSuspended.tooltip = "When checked, the Job will be submitted to the Repository as Suspended.\n\nIt will require manual user intervention before becoming active."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "SubmitAsSuspended")
			local theTooltipText = 	"Defines the 3ds Max build to force.\n\nWhen set to 'none', the Slave will launch the first matching version of 3ds Max it finds in its search paths regardless of 32/64 bitness.\n\nWhen set to '32 bit', the Slave will launch the first found 32 bit installation of the matching 3ds Max version.\n\nWhen set to '64 bit', the Slave will launch the first found 64 bit installation of the matching 3ds Max version."
			btn_MaxVersionToForce.tooltip = theTooltipText
			try(ddl_MaxVersionToForce.tooltip = theTooltipText)catch()
		)
		
		fn updateRolloutTitle state =
		(
			local theTitle = "FumeFX Job Options"
			if not state do
			(
				if SMTDSettings.LimitEnabled do theTitle+= " [Limit: "+SMTDSettings.MachineLimit as string+"]"
				if SMTDSettings.TaskTimeoutEnabled do 	theTitle+= " [TTO]"
				if SMTDSettings.AutoTaskTimeout do theTitle+= " [ATTO]"
				if SMTDSettings.SequentialJob do theTitle+= " [Seq.]"
			)
			SMTD_FumeFXOptionsRollout.title = theTitle
		)
		
		fn convertTimeoutToSeconds =
		(
			local theTime = #(spn_task_timeout_hours.value, spn_task_timeout_minutes.value, spn_task_timeout_seconds.value )
			local theVal = theTime[1] * 3600 + theTime[2] * 60 + theTime[3] 
			setIniSetting SMTDPaths.InIFile "JobSettings"  "TaskTimeout" ( (SMTDSettings.TaskTimeout = theVal ) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Task Timeout set to " + theVal as string + " seconds or " + theTime[1] as string + " hour" + (if theTime[1] == 1 then ", " else "s, ") + theTime[2] as string + " minute"+(if theTime[2] == 1 then ", and " else "s, and ") + theTime[3] as string + " second" + (if theTime[3] == 1 then "." else "s."))			
		)

		--EVENT HANDLERS--
		on SMTD_FumeFXOptionsRollout rolledup state do
		(
			updateRolloutTitle state
		)	
		
		on SMTD_FumeFXOptionsRollout open do
		(
			--RESTORE UI VALUES FROM STRUCT
			chk_limitEnabled.state = SMTDSettings.LimitEnabled
			spn_machineLimit.value = SMTDSettings.MachineLimit
			
			ddl_concurrentTasks.selection = SMTDSettings.MaxTasksPerSlave
			chk_limitConcurrentTasks.state = SMTDSettings.LimitTasksToNumberOfCpus
			
			chk_submitAsSuspended.state = SMTDSettings.SubmitAsSuspended 

			chk_TaskTimeoutEnabled.state = SMTDSettings.TaskTimeoutEnabled
			chk_autoTimeout.state = SMTDSettings.AutoTaskTimeout
			chk_restartMax.state = SMTDSettings.RestartMax
			local theHours= (floor (SMTDSettings.TaskTimeout / 3600.0)) as integer
			
			spn_task_timeout_hours.value = theHours
			local theMinutes = (floor ((SMTDSettings.TaskTimeout - theHours*3600) / 60.0)) as integer
			spn_task_timeout_minutes.value = theMinutes 
			local theSeconds = (SMTDSettings.TaskTimeout - theHours*3600 - theMinutes*60) 
			spn_task_timeout_seconds.value = theSeconds
			
			local versionVal = findItem #("none", "32bit", "64bit") SMTDSettings.MaxVersionToForce 
			if versionVal == 0 do versionVal = 1
			ddl_MaxVersionToForce.selection = versionVal
			
			local onCompleteVal = findItem #("Nothing", "Archive", "Delete") SMTDSettings.OnComplete 
			if onCompleteVal == 0 do onCompleteVal = 1
			ddl_onComplete.selection = onCompleteVal
			
			chk_interruptible.checked = SMTDSettings.JobIsInterruptible
			
			--ENABLE/DISABLE UI CONTROLS
			spn_machineLimit.enabled = SMTDSettings.LimitEnabled
			
			btn_MaxVersionToForce.enabled = ddl_MaxVersionToForce.enabled = (maxVersion())[1] > 8000
			spn_task_timeout_hours.enabled = spn_task_timeout_minutes.enabled  = spn_task_timeout_seconds.enabled = chk_TaskTimeoutEnabled.checked

			--SHOW NON-STICKY SETTINGS
			chk_limitEnabled.caption = SMTDFunctions.getStickyCaption "JobSettings" "LimitEnabled" "Limit  "
			spn_MachineLimit.caption = SMTDFunctions.getStickyCaption "JobSettings" "MachineLimit" "Machines: "
			
			chk_TaskTimeoutEnabled.caption = SMTDFunctions.getStickyCaption "JobSettings" "TaskTimeoutEnabled" "Task Timeout:  "
			chk_autoTimeout.caption = SMTDFunctions.getStickyCaption "JobSettings" "AutoTaskTimeout" "Enable Auto Task Timeout  "
			chk_restartMax.caption = SMTDFunctions.getStickyCaption "JobSettings" "RestartMax" "Restart 3ds Max Between Tasks  "
			
			chk_submitAsSuspended.caption  = SMTDFunctions.getStickyCaption "JobSettings" "SubmitAsSuspended" "Submit Job As Suspended  " 
			btn_onComplete.caption  = SMTDFunctions.getStickyCaption "JobSettings" "OnComplete" "On Job Completion:  " 
			btn_concurrentTasks.caption = SMTDFunctions.getStickyCaption "JobSettings" "MaxTasksPerSlave" "Concurrent Tasks:  " 
			chk_limitConcurrentTasks.caption = SMTDFunctions.getStickyCaption "JobSettings" "LimitTasksToNumberOfCpus" "Limit Tasks To Slave's Task Limit  "
			chk_interruptible.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "JobIsInterruptible"  "Job Is Interruptible  " 
			btn_MaxVersionToForce.caption = SMTDFunctions.getStickyCaption "JobSettings" "MaxVersionToForce" "Force 3ds Max Build:  "
				
			updateTooltips()
			updateRolloutTitle SMTD_FumeFXOptionsRollout.open
		)--end on
		
		on chk_TaskTimeoutEnabled changed state do
		(
			local theTime = #(spn_task_timeout_hours.value, spn_task_timeout_minutes.value, spn_task_timeout_seconds.value )
			setIniSetting SMTDPaths.InIFile "JobSettings"  "TaskTimeoutEnabled" ( (SMTDSettings.TaskTimeoutEnabled = state) as string)
			if state then 
				SMTD_MainRollout.Ui_report ("+Job Options: Task Timeout Enabled, Value is "+theTime[1] as string + " hour" + (if theTime[1] == 1 then ", " else "s, ") + theTime[2] as string + " minute"+(if theTime[2] == 1 then ", and " else "s, and ") + theTime[3] as string + " second"+ (if theTime[3] == 1 then "." else "s.")) 
			else 
				SMTD_MainRollout.Ui_report ("+Job Options: Task Timeout Disabled.") 
			
			spn_task_timeout_hours.enabled = spn_task_timeout_minutes.enabled  = spn_task_timeout_seconds.enabled = state
			updateTooltips()
		)
		
		on chk_autoTimeout changed state do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "AutoTaskTimeout" ( (SMTDSettings.AutoTaskTimeout = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Enable Auto Task Timeout set to [" + state as string + "]")
			updateTooltips()
		)
		
		on chk_restartMax changed state do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "RestartMax" ( (SMTDSettings.RestartMax = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Restart 3ds Max Between Tasks set to [" + state as string + "]")
			updateTooltips()
		)
		
		on spn_task_timeout_hours changed val do convertTimeoutToSeconds()
		on spn_task_timeout_minutes changed val do convertTimeoutToSeconds()
		on spn_task_timeout_seconds changed val do convertTimeoutToSeconds()
		
		on chk_limitEnabled changed state do 
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "LimitEnabled" ( (SMTDSettings.LimitEnabled = state) as string)
			spn_machineLimit.enabled = state 
			SMTD_MainRollout.Ui_report ("+Job Options: Machine Limit State set to [" + state as string + "]"+(if state then (", Machine Limit is ["+SMTDSettings.machineLimit as string+"].") else (".") ))
			updateTooltips()				
		)	
		on spn_machineLimit changed value do 
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "MachineLimit" ( (SMTDSettings.machineLimit = value) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Machine Limit Count set to [" + value as string + "]")
			updateTooltips()
		)	
		
		on chk_limitConcurrentTasks changed state do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "LimitTasksToNumberOfCpus" ( (SMTDSettings.LimitTasksToNumberOfCpus = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Limit Tasks To Slave's Task Limit set to [" + state as string + "]")
			updateTooltips()
		)
		
		on chk_interruptible changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "JobIsInterruptible" ((SMTDSettings.JobIsInterruptible = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Job Is Interruptible set to [" + state as string + "].")	
			updateTooltips()
		)
		
		on ddl_concurrentTasks selected itm do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "MaxTasksPerSlave" ( (SMTDSettings.MaxTasksPerSlave = itm) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Concurrent Tasks set to [" + ddl_concurrentTasks.selected + "]")
			updateTooltips()
		)
		
		on chk_submitAsSuspended changed state do 
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "SubmitAsSuspended" ( (SMTDSettings.SubmitAsSuspended = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Submit As Suspended set to [" + state as string + "]")
			updateTooltips()
		)	
		
		on ddl_onComplete selected itm do
		(
			case itm of
			(
				1: SMTDSettings.OnComplete = "Nothing"
				2: SMTDSettings.OnComplete = "Archive"
				3: SMTDSettings.OnComplete = "Delete"
			)
			setIniSetting SMTDPaths.InIFile "JobSettings"  "OnComplete" SMTDSettings.OnComplete
			SMTD_MainRollout.Ui_report ("+Job Options: On Job Completion set to [" + SMTDSettings.OnComplete + "]")
			updateTooltips()
		)
		
		on ddl_MaxVersionToForce selected itm do
		(
			case itm of
			(
				1: SMTDSettings.MaxVersionToForce = "none"
				2: SMTDSettings.MaxVersionToForce = "32bit"
				3: SMTDSettings.MaxVersionToForce = "64bit"
			)
			setIniSetting SMTDPaths.InIFile "JobSettings"  "MaxVersionToForce" SMTDSettings.MaxVersionToForce
			SMTD_MainRollout.Ui_report ("+Job Options: Force 3ds Max build set to [" + SMTDSettings.MaxVersionToForce + "]")
			updateTooltips()
		)
	)

	struct SMTDWorkflow_FumeFXStruct
	(
		fn isWorkflowActive = (isKindOf FumeFX GeometryClass; true),	--Mandatory! Return false to disable the workflow so it does not load in SMTD UI
		WorkflowName = "fumefxsim",
		WorkflowTitle = "Submit FUME FX SIMULATIONS To Deadline",	--Optional. The description of the workflow displayed in the drop-down list, the file name will be used if this is not defined.
		Description = "Submit one or more FumeFX Simulations to be processed on Deadline Slaves.", --Optional. The detailed description used for tooltips, will default to "" if not defined.
		FumeFXObjectsToSim = #(),
		SimCacheOutput = "",
		UseSimCacheOutput = false,
		PermanentSceneChange = false,
		fn defineUILayout =	--Optional. If not defined, the default legacy layout with all rollouts will be used
		(
			#(
				#(#("FumeFX Job","FumeFX Job Settings"),#(#(SMTD_FumeFXRollout,true),#(SMTD_FumeFXOptionsRollout,true), #(SMTD_JobFailureDetection,false))), 
				#(#("Assets","Assets - Asset Collection And Synchronization"),#(#(SMTD_AssetList,true))),
				#(#("Render","Rendering Options"),#(#(SMTD_ScenePreProcessing,true), #(SMTD_MaxStartup,false))), 
				#(#("Options","Submission Options"),#(#(SMTD_UserOptions,true), #(SMTD_SubmissionTimeouts,false))), 
				#(#("Limits","Black List Management and License Limits"),#(#(SMTD_BlackListSlaves,true), #(SMTD_LimitGroups,false)))
			)		
		),
		fn updateUILayout = --Optional. This function could be used to apply changes to the visilibity of existing controls
		(
			
		),
		fn storeSettings =
		(
			--SMTD_MainRollout.Ui_report (">FumeFX Workflow: Storing Settings With Scene...")
			SMTDFunctions.storeWorkflowSettingsWithScene &SMTDWorkflow_FumeFX
		),
		fn restoreSettings =
		(
			SMTD_MainRollout.Ui_report (">FumeFX Workflow: Restoring Settings From Scene...")
			SMTDFunctions.restoreWorkflowSettingsFromScene &SMTDWorkflow_FumeFX propsToSkip:#() 
		),
		fn CanSubmit = 		--Optional. This function is called to enable/disable the SUBMIT button. 
							--It must return an array containing a Boolean and a string with a description: #(false, "Reason"), 
							--where false means disable the button, and the string explains why it was disabled.
							--When the result is true, the string will be ignored and the .description property will be used as button tooltip.
							--Assumed to be #(true,"") if the function is not defined.
		(
			local canSubmitJob = true																			--We start by assuming that a submission is possible, then we will lower the flag if something is not right
			local theObjectsToSim = for o in objects where classof o == FumeFX collect o
			local txt = "SUBMIT a FumeFX SIMULATION Job to Deadline..."						
			if FumeFXObjectsToSim.count == 0 do											--If no FFX objects were found, 
			(
				txt = "No FumeFX Objects CHECKED for Simulation!"												--Define the explanation string
				canSubmitJob = false																			--and lower the flag
			)
			if theObjectsToSim.count == 0 do																	--If no objects were enabled for submission,
			(
				txt = "No FumeFX Objects FOUND in the Scene!"													--Define the explanation string
				canSubmitJob = false																			--and lower the flag
			)
			local localOutputs = for o in theObjectsToSim where findItem FumeFXObjectsToSim o.name > 0 and matchPattern (o.GetPath #default) pattern:"c:\\*" collect o
			if localOutputs.count > 0 and not UseSimCacheOutput do
			(
				txt = (if localOutputs.count == 1 then "One" else localOutputs.count as string) + " active FumeFX Object"+ (if localOutputs.count == 1 then "" else "s") +" pointing at LOCAL Drive C:\\!\nPlease repath and try again!"	--Define the explanation string
				canSubmitJob = false																			--and lower the flag
			)
			#(canSubmitJob, txt)																				--return the boolean and the description as an array	
		),
		fn submitJob =		--Optional. Called when the SUBMIT button is pressed. If not defined, the submission will not performed
		(
			::SMTDSettings = copy ::SMTDSettingsFactory 															--first reset all SMTD Settings to factory defaults 
			--Now restore from the backup only the settings that are required for this workflow:
			local SettingsToRestoreArray = #(#LimitEnabled, #MachineLimit, #MaxTasksPerSlave, #LimitTasksToNumberOfCpus, #SubmitAsSuspended, #TaskTimeoutEnabled, #AutoTaskTimeout, #RestartMax, #TaskTimeout, #MaxVersionToForce, #OnComplete, #JobIsInterruptible)
			for p in SettingsToRestoreArray do														--loop through all relevant properties we need to keep for the submission
				try(setProperty ::SMTDSettings p (getProperty ::SMTDSettings_Backup p))catch()		--a copy of the SMTDSettings is stored in SMTDSettings_Backup before the function is called
				
			SMTDSettings.RestartRenderer = false													--must be off for FumeFX simulations
				
			renderSceneDialog.close()																--close the render dialog
			local oldrendTimeType = rendTimeType 													--store the original time type and start and end frames
			local oldrendStart = rendStart 
			local oldrendEnd  = rendEnd
			local defaultPaths = #()	
			local theObjectsToSim = for o in objects where classof o == FumeFX and findItem FumeFXObjectsToSim o.name > 0 collect o
			
			rendTimeType = 3																		--modify the time mode to custom range
			rendStart = 1																			--set the frame range from 1 
			rendEnd = theObjectsToSim.count 														--to the number of objects, which makes one task per object!
			local MAXScriptFile = SMTDPaths.MainSubmissionDir + "\\Workflows\\MAXScriptJob_SimulateFumeFX.ms"	--the MAXScript job file

			SMTDFunctions.createSubmissionFolderAndUpdatePaths()						--create submission folder with current date and time
			local TempMaxFile = SMTDPaths.submitSubFolder + maxFileName					--build the file name of the file to save
			if maxFileName == "" do TempMaxFile += "untitled.max"						--if the file is untitled, name it like that
			if (doesFileExist TempMaxFile) do deleteFile TempMaxFile					--if the file happens to exist, delete it (should never be the case due to the unique folder)
			
			if UseSimCacheOutput do --and doesFileExist SimCacheOutput
			(
				local newPath = SimCacheOutput
				if not matchPattern newPath pattern:"*\\" do newPath += "\\"
				defaultPaths = for o in theObjectsToSim collect o.GetPath #default
				for o in theObjectsToSim do 
					o.SetPath (newPath+(filenameFromPath (o.GetPath #default))+".fxd") #(#default)
			)

			--Include the simulator names in the default comment
			local txt = "" as stringStream 																			--Start an empty stringStream
			format "3ds Max % Simulating FumeFX Object%: " (SMTDFunctions.getMaxVersion()) (if theObjectsToSim.count > 1 then "s" else "") to:txt				--Output the base comment listing the simulators' count to the stringStream
			for i = 1 to theObjectsToSim.count do 																	--Loop through the names of objects checked for simulation
				format "[%]%" theObjectsToSim[i].name (if i < theObjectsToSim.count then "," else "") to:txt		--If the name is not the last on the list, add a comma behind the name, otherwise do not
			
			local formattedComment = SMTDFunctions.FormatComment SMTDSettings.Comment defaultTokenValue:txt --format the comment, replacing any tokens
			SMTDSettings.Comment = formattedComment										--assign the formatted comment to the property
			if SMTDSettings.Comment == "" do SMTDSettings.Comment = txt					--if the comment is still empty, set it to the default text
			SMTDSettings.ChunkSize = 1													--override the chunk size to 1
			SMTDSettings.SubmitAsMXSJob = true											--switch the job to run a MAXScript
			
			SMTDFunctions.SaveMaxFileCopy TempMaxFile									--save the Max scene file for submission
			
			SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile 				--create a submit info file
			SMTDFunctions.CreateJobInfoFile SMTDPaths.JobInfoFile 						--create a job info file
			local theHandle = openFile SMTDPaths.JobInfoFile mode:"at"					--open the job info file for append writing
			with printAllElements on format "FumeFXToSimulate=%" (for o in theObjectsToSim collect o.name) to:theHandle	--write the array of objects to simulate to it
			close theHandle																--and close the file

			--build the command line arguments with the two job files, the MAX file, and the MAXScript file
			local initialArgs = "\""+SMTDPaths.SubmitInfoFile +"\" \""+SMTDPaths.JobInfoFile+"\" \""+TempMaxFile+ "\" \""+ MAXScriptFile +"\" " 
			local result = SMTDFunctions.waitForCommandToComplete initialArgs SMTDSettings.TimeoutSubmission

			local renderMsg = SMTDFunctions.getRenderMessage() 
			SMTDFunctions.getJobIDFromMessage renderMsg

			if result == #success then 
			(
				try(SMTD_MainRollout.Ui_report ("+Simulation Submitted Successfully!\n"+renderMsg))catch()
			)
			else 
			(
				try(SMTD_MainRollout.Ui_report ("--Simulation Submission FAILED!\n"+renderMsg))catch()
			)	
			rendTimeType = oldrendTimeType
			rendStart = oldrendStart
			rendEnd	= oldrendEnd
			if UseSimCacheOutput and not PermanentSceneChange do
			(
				for i = 1 to theObjectsToSim.count do theObjectsToSim[i].SetPath (defaultPaths[i]+".fxd") #(#default)
			)
			SMTDSettings = copy originalSettings --restore the original settings
		)
	)
	SMTDWorkflow_FumeFX = SMTDWorkflow_FumeFXStruct()--return an instance of the struct
)
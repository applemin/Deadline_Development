(
	global SMTDWorkflow_PhoenixFD
	global SMTD_PhoenixFDRollout 
	
	rollout SMTD_PhoenixFDRollout "PhoenixFD Simulations"
	(
		local PhoenixFDObjectsAll = #()									--this array will be used to collect all PFD objects in the scene
		local isUpdating = false 										--this flag will be raised when the ListView is updating, and will be lowered when it has finished updating
		
	--USER INTERFACE CONTROLS:
		
		button btn_checkAll "Check All" align:#left across:3 height:20 offset:[-10,-5] width:105
		button btn_invert "Invert" align:#center height:20 offset:[-80,-5] width:105
		button btn_updateObjects "Update Phoenix FD Objects From The Scene..." height:20 align:#right offset:[10,-5] width:260
		
		dotNetControl dnc_pfd_objects "ListView" height:140 width:480 align:#center offset:[0,-3]
		
		edittext edt_SimCacheOutput "Simulation Cache Output Directory Override:" fieldWidth:450 labelOnTop:true align:#left across:2 offset:[-10,-2]
		button btn_SimCacheOutput "..." align:#right offset:[10,14] width:25
		
		checkbox chk_UseSimCacheOutput "Use Cache Output Directory Override" across:2 align:#left offset:[-10,-2]
		checkbox chk_permanentSceneChange "Make Directory Override Changes Permanent" align:#right checked:true offset:[10,-2]

	--FUNCTION DEFINITIONS:
		
		local foreColor, bgColor, redColor, greenColor, blueColor  --top-level local variables to store DotNet Color values for use in the ListView
		fn defineDotNetColors = --this function defines the colors based on the background color of 3ds Max - different values for light and dark schemes
		(
			local textColor = ( ((colorman.getcolor #text) as color)*255)
			local maxBgColor = (((colorman.getcolor #window)) as color)*255
			foreColor = (dotNetClass "System.Drawing.Color").fromARGB textColor.r textColor.g textColor.b
			bgColor = (dotNetClass "System.Drawing.Color").fromARGB maxBgColor.r maxBgColor.g maxBgColor.b
			if maxBgColor.v >= 160 then
			(
				--DARK COLORS
				redColor = (dotNetClass "System.Drawing.Color").fromARGB 192 0 0
				greenColor = (dotNetClass "System.Drawing.Color").fromARGB 0 92 0
				blueColor = (dotNetClass "System.Drawing.Color").fromARGB 0 0 128
			)
			else
			(
				--LIGHT COLORS
				redColor = (dotNetClass "System.Drawing.Color").fromARGB 255 128 128
				greenColor = (dotNetClass "System.Drawing.Color").fromARGB 128 255 128
				blueColor = (dotNetClass "System.Drawing.Color").fromARGB 192 220 255
			)
		)

		fn initListView = 																						--Initialize the ListView control
		(
			isUpdating = true 																					--Raise the flag that we are updating the ListView
			local layout_def = #( #("Phoenix FD Object",120),  #("Type",80), #("Output",370)) 					--Column names and widths in pixels
			local lv = dnc_pfd_objects																			--ListView control alias to shorten the code
			lv.Clear()																							--Clear the VistView
			lv.backColor = bgColor																				--Set the background color to match the 3ds Max scheme's background
			lv.View = (dotNetClass "System.Windows.Forms.View").Details											--Set the View to Details mode 
			lv.gridLines = true 																				--Show grid lines
			lv.fullRowSelect = true																				--Selecting anywhere selects the whole row
			lv.checkboxes = true																				--Checkboxes will be used to enable/disable the simulation of objects
			lv.hideSelection = false																			--Always show the selection
			lv.ShowItemToolTips = true																			--Show tooltips, if any
			lv.MultiSelect = false																				--Disable multiple selected items on the List
			for i in layout_def do lv.Columns.add i[1] i[2]														--Add all columns to the ListView
			isUpdating = false																					--Lower the update flag
		)--end fn		

		fn populateListView =																					--Populate the ListView with PFD objects to simulate
		(
			isUpdating = true																					--Raise the flag that we are updating the ListView
			local lv = dnc_pfd_objects																			--ListView control alias to shorten the code
			lv.items.Clear()																					--Clear the VistView
			local theRange = #()																				--Initialize the array to collect ListView Items into
			local useOverride = false																			--When false, we will be showing the original paths, when true, the override path will be shown
			if ::SMTDWorkflow_PhoenixFD.UseSimCacheOutput and doesFileExist ::SMTDWorkflow_PhoenixFD.SimCacheOutput do	--If output override is on and the path is valid,
			(
				local simPath = ::SMTDWorkflow_PhoenixFD.SimCacheOutput											--Grab the path value from the UI control
				if simPath[simPath.count]!="\\" do simPath += "\\"												--and make sure it ends with a backslash
				useOverride = true																				--Raise the flag that we will be showing the override path
			)
			
			for i = 1 to PhoenixFDObjectsAll.count do															--Loop through all PFD objects in the scene
			(
				local theNode = PhoenixFDObjectsAll[i]															--Get the i-th object into a variable
				local li = dotNetObject "System.Windows.Forms.ListViewItem" theNode.name						--Create a ListView Item with the name of the object
				li.checked = findItem ::SMTDWorkflow_PhoenixFD.PhoenixFDObjectsExport theNode.name > 0			--If the object is to be simulated, check the checkbox 
				li.forecolor = case (classof theNode) of														--Set the foreground color based on the object's type
				(
					default: foreColor																			--default text color if we don't know the class (should never be the case)
					FireSmokeSim: redColor																		--red for Fire and Smoke simulation
					LiquidSim: blueColor																		--blue for Liquid simulation
					PHXSimulator: greenColor																	--green for PHX simulation
				)--end case
				local subLi = li.SubItems.add ((classof theNode) as string)										--Add the class of the object to the second column sub-item
				local theOutput = theNode.simoutput																--Grab the simulation output path
				if useOverride do																				--If we are overriding the output,
				(
					theOutput = simPath + (if matchPattern theNode.simoutput pattern:"*$*" then					--The new output will use the override path, plus the file name:
						"ND" + (theNode.inode.handle as string) + "_" + theNode.name + "_####.aur"  			--If the output path contains any Phoenix macros, use the node handle and the node name to construct a file name
					else	
						filenameFromPath theNode.simoutput)														--Otherwise we can just strip the path and take the existing filename
				)--end if
				local subLi = li.SubItems.add theOutput															--Add the output path to the third column's sub-item
				append theRange li																				--Append the whole ListView Item to the Range array
			)--end i loop
			lv.Items.AddRange theRange																			--Add the resulting array of ListView Items as the Range
			isUpdating = false																					--Lower the update flag
		)--end fn
		
		fn collectPFDObjects =																					--Collect all PFD objects, and check the selection to decide what to simulate
		(
			local phoenixFDClasses = #(LiquidSim, FireSmokeSim, PHXSimulator) 									--Array of supported simulator classes
			--local PhoenixFDObjectsSelected = for o in selection where findItem phoenixFDClasses (classof o) > 0 collect o --Collect selected scene simulators
			PhoenixFDObjectsAll = for o in objects where findItem phoenixFDClasses (classof o) > 0 and (getUserProp o "phxgroupname") ==undefined and (getUserProp o "phx_system_id") ==undefined  collect o --collect all simulators
			--::SMTDWorkflow_PhoenixFD.PhoenixFDObjectsExport = for o in PhoenixFDObjectsAll where ( if PhoenixFDObjectsSelected.count == 0 then true else findItem PhoenixFDObjectsSelected o > 0) collect o.name --collect the names of object to export because object is selected, or because nothing is selected
		)--end fn
		
		fn selectHighlightedObject =																			--Function to select the highlighted object from the ListView in the Max Modify Panel
		(
			select (for i = 1 to dnc_pfd_objects.items.count where dnc_pfd_objects.items.item[i-1].Selected collect PhoenixFDObjectsAll[i])	--Collect and select the object that is highlighted
			max modify mode																						--Switch the 3ds Max Command Panel to Modify mode
		)--end fn
		
		fn exploreHighlightedOutput =
		(
			for i = 1 to dnc_pfd_objects.items.count where dnc_pfd_objects.items.item[i-1].Selected do 
			(
				local theFile = dnc_pfd_objects.items.item[i-1].subItems.Item[2].text
				if matchPattern theFile pattern:"$(scene_dir)" then 
					theFile = maxFilePath
				else
					theFile = getFileNamePath theFile
				try(shellLaunch theFile "")catch()
			)
		)--end fn

	--UI EVENT HANDLERS	
		
		on btn_SimCacheOutput pressed do																		--If the user pressed the Browse... button for the Output Override path,
		(
			local simCacheOutputString = getSavePath caption:"Set Simulation Cache Output Location" initialdir:(::SMTDWorkflow_PhoenixFD.SimCacheOutput)  --Open a Save Path dialog at the current location, if any
			if simCacheOutputString != undefined do 															--If a valid path was selected, 
			(
				::SMTDWorkflow_PhoenixFD.SimCacheOutput = simCacheOutputString									--assign the new path to the UI control
				setINISetting SMTDPaths.InIFile "PhoenixFDWorkflow" "DeadlineSimOutputOverride" (edt_SimCacheOutput.text = ::SMTDWorkflow_PhoenixFD.SimCacheOutput)
				::SMTDWorkflow_PhoenixFD.UseSimCacheOutput = chk_UseSimCacheOutput.checked = true				--Check the checkbox to use the Override that was just picked
				::SMTDWorkflow_PhoenixFD.storeSettings()
				populateListView()																				--Update the ListView to show the new path in the third column
			)
			chk_UseSimCacheOutput.enabled = doesFileExist edt_SimCacheOutput.text			
			try(SMTD_MainRollout.updateSubmitButtonState())catch()												--Update the SUBMIT button's text and enabled state
		)--end on pressed handler

		on edt_SimCacheOutput entered txt do 																	--If an Output Override path was entered manually, update the SUBMIT button
		(
			setINISetting SMTDPaths.InIFile "PhoenixFDWorkflow" "DeadlineSimOutputOverride" (::SMTDWorkflow_PhoenixFD.SimCacheOutput = edt_SimCacheOutput.text)
			::SMTDWorkflow_PhoenixFD.storeSettings()
			chk_UseSimCacheOutput.enabled = doesFileExist edt_SimCacheOutput.text
			try(SMTD_MainRollout.updateSubmitButtonState())catch()
		)
		
		on btn_checkAll pressed do 
		(
			collectPFDObjects()
			::SMTDWorkflow_PhoenixFD.PhoenixFDObjectsExport = for o in PhoenixFDObjectsAll collect o.name	--collect all object names
			populateListView()																					--Populate the content of the ListView
			try(SMTD_MainRollout.updateSubmitButtonState())catch()												--Update the enabled state and text of the SUBMIT button
		)
		on btn_invert pressed do
		(
			collectPFDObjects()
			::SMTDWorkflow_PhoenixFD.PhoenixFDObjectsExport = for o in PhoenixFDObjectsAll where findItem ::SMTDWorkflow_PhoenixFD.PhoenixFDObjectsExport o.name == 0 collect o.name
			populateListView()																					--Populate the content of the ListView
			try(SMTD_MainRollout.updateSubmitButtonState())catch()												--Update the enabled state and text of the SUBMIT button
		)
		
		on btn_updateObjects pressed do 																		--If the Update button was pressed,
		(
			collectPFDObjects()																					--Collect the simulators from the scene
			populateListView()																					--Populate the content of the ListView
			try(SMTD_MainRollout.updateSubmitButtonState())catch()												--Update the enabled state and text of the SUBMIT button
		)
		
		on dnc_pfd_objects mouseClick arg do																	--If the user clicked an item with the mouse button,
		(
			rcmenu pfd_rcmenu 																					--Define a right-click menu to display
			(
				menuitem mnu_selectObject "Select Highlighted Object In The Scene"								--Menu item to select the highlighed object
				separator sep_10
				menuitem mnu_explorePath "Explore Simulation Path Of Highlighted Object"						--Menu item to explore the output path
				
				on mnu_selectObject picked do SMTD_PhoenixFDRollout.selectHighlightedObject()					--If the menu item was picked from the menu, call the function to select the highlighted object defined earluer in the scope of the rollout
				on mnu_explorePath picked do SMTD_PhoenixFDRollout.exploreHighlightedOutput()					--If the menu item was picked from the menu, call the function to explore the simulation path defined earluer in the scope of the rollout
			)--end rcmenu
			if arg.Button == arg.Button.Right do popupmenu pfd_rcmenu pos:mouse.screenpos						--If the right mouse button was pressed, pop up the rcmenu at the current screen position of the mouse cursor
		)--end on mouseClicked handler
		
		on dnc_pfd_objects MouseDoubleClick arg do 																--If the user double-clicked an item on the ListView,
		(
			if not isUpdating do 																				--If the handler is not called by the ListView during its update,
				::SMTDWorkflow_PhoenixFD.PhoenixFDObjectsExport = \
					for i = 1 to dnc_pfd_objects.items.count where dnc_pfd_objects.items.item[i-1].checked collect 
						dnc_pfd_objects.items.item[i-1].text													--Collect the names of checked objects into the array
			::SMTDWorkflow_PhoenixFD.storeSettings()					
			try(SMTD_MainRollout.updateSubmitButtonState())catch()												--Update the SUBMIT button's enabled state and text
		)--end on MouseDoubleClick handler
		
		on dnc_pfd_objects ItemChecked arg do 																	--If the user checked/unchecked an item on the ListView,
		(
			if not isUpdating do 																				--If the handler is not called by the ListView during its update,
				::SMTDWorkflow_PhoenixFD.PhoenixFDObjectsExport = \
					for i = 1 to dnc_pfd_objects.items.count where dnc_pfd_objects.items.item[i-1].checked collect 
						dnc_pfd_objects.items.item[i-1].text													--Collect the names of checked objects into the array
			::SMTDWorkflow_PhoenixFD.storeSettings()		
			try(SMTD_MainRollout.updateSubmitButtonState())catch()												--Update the SUBMIT button's enabled state and text
		)--end on ItemChecked handler
		
		on chk_UseSimCacheOutput changed state do 																--If the Simulation Cache Override option was checked or unchecked,
		(
			setINISetting SMTDPaths.InIFile "PhoenixFDWorkflow" "DeadlineSimUseOutputOverride" ((::SMTDWorkflow_PhoenixFD.UseSimCacheOutput = state) as string)
			::SMTDWorkflow_PhoenixFD.storeSettings()
			populateListView()																					--update the ListView as the filename display would change
			try(SMTD_MainRollout.updateSubmitButtonState())catch()																									--and update the SUBMIT button's enabled state and text
		)--end if checkbox handler
		
		on chk_permanentSceneChange changed state do
		(
			setINISetting SMTDPaths.InIFile "PhoenixFDWorkflow" "DeadlineSimPermanentOutputOverride" ((::SMTDWorkflow_PhoenixFD.permanentSceneChange = state) as string)
			::SMTDWorkflow_PhoenixFD.storeSettings()
		)
		
		on SMTD_PhoenixFDRollout open do																		--If the submitter's dialog was opened,
		(
			defineDotNetColors()																				--Define the colors to use in the ListView
			collectPFDObjects()																					--Collect the simulators from the scene
			initListView()																						--Initialize the ListView
			
			--Set the controls to the property values in the Workflow struct which at this point has been updated from disk and MAX scene 
			edt_SimCacheOutput.text = ::SMTDWorkflow_PhoenixFD.SimCacheOutput
			chk_UseSimCacheOutput.checked = ::SMTDWorkflow_PhoenixFD.UseSimCacheOutput
			chk_permanentSceneChange.checked = ::SMTDWorkflow_PhoenixFD.permanentSceneChange
			
			populateListView()																					--Populate the content of the ListView
			try(SMTD_MainRollout.updateSubmitButtonState())catch()												--Update the enabled state and text of the SUBMIT button
		)

		on SMTD_PhoenixFDRollout close do																		--When the dialog is closed, we want to store all relevant UI values in the INI file
		(
		)--end on close handler
	)--end rollout
	
	struct SMTDWorkflow_PhoenixFDStruct
	(
		fn isWorkflowActive = (isKindOf PHXSimulator GeometryClass),	--Mandatory! Return false to disable the workflow so it does not load in SMTD UI
		WorkflowName = "phoenixfd", --Mandatory! Defines the name of the workflow used to ID it and store/restore its properties with the scene
		WorkflowTitle= "Submit PHOENIX FD SIMULATIONS To Deadline",										--the description of the workflow displayed in the drop-down list
		Description = "Submit one or more Phoenix FD Simulations to be processed on Deadline Slaves.", 	--the detailed description used for tooltips
		--Custom Properties of this workflow:
		PhoenixFDObjectsExport = #(),																	--stores the names of the objects to be exported
		UseSimCacheOutput = false,
		SimCacheOutput = "",
		PermanentSceneChange = true,
		--Functions
		fn defineUILayout =
		(
			#(
				#(#("Phoenix FD Job","FumeFX Job Settings"),#(#(SMTD_PhoenixFDRollout,true),#(SMTD_JobOptions,false), #(SMTD_JobFailureDetection,false))), 
				#(#("Assets","Assets - Asset Collection And Synchronization"),#(#(SMTD_AssetList,true))),
				#(#("3ds Max","3ds Max Options"),#(#(SMTD_ScenePreProcessing,true), #(SMTD_MaxStartup,false))), 
				#(#("Options","Submission Options"),#(#(SMTD_UserOptions,true), #(SMTD_SubmissionTimeouts,false))), 
				#(#("Limits","Black List Management and License Limits"),#(#(SMTD_BlackListSlaves,true), #(SMTD_LimitGroups,false)))
			)		
		),
		fn updateUILayout =
		(
			local disableArray = #(#btn_chunk,#btn_chunk, #spn_chunkSize, #ddl_OutOfOrderMethod, #btn_printFrameSequenceToLog, #spn_outOfOrderStep, #chk_forceWorkstationMode, #chk_useSilentMode, #chk_EnforceSequentialRendering )
			for c in SMTD_JobOptions.controls where findItem  disableArray (c.name as name) > 0 do 
			(
				c.enabled = false
				try(c.tooltip = "Not available in this Workflow")catch()
			)
		),
		fn storeSettings =
		(
			SMTDFunctions.storeWorkflowSettingsWithScene &SMTDWorkflow_PhoenixFD
		),
		fn restoreSettings =
		(
			::SMTDWorkflow_PhoenixFD.SimCacheOutput = getINISetting SMTDPaths.InIFile "PhoenixFDWorkflow" "DeadlineSimOutputOverride"	--Get the last Output Override path, and assign to the edit text control

			local val = execute (getINISetting SMTDPaths.InIFile "PhoenixFDWorkflow" "DeadlineSimUseOutputOverride" )					--Get the last Use Override checkbox' state, call execute to turn to a Boolean value
			if val == OK do val = false																									--If it is OK, then there was an empty string, so no previous value exsits. Use false as the default.
			::SMTDWorkflow_PhoenixFD.UseSimCacheOutput = val
			
			local val = execute (getINISetting SMTDPaths.InIFile "PhoenixFDWorkflow" "DeadlineSimPermanentOutputOverride")				--Get the last Permanent Changes checkbox' state, call execute to turn to a Boolean value
			if val == OK do val = true																									--If it is OK, then there was an empty string, so no previous value exsits. Use true as the default.
			::SMTDWorkflow_PhoenixFD.permanentSceneChange = val																			--Set the checkbox' checked state to this value
			
			SMTD_MainRollout.Ui_report (">Phoenix FD Workflow: Restoring Settings From Scene...")
			SMTDFunctions.restoreWorkflowSettingsFromScene &SMTDWorkflow_PhoenixFD propsToSkip:#() 
		),		
		fn canSubmit =																								--Updates the Submit button's enabled state and caption based on some sanity checks
		(
			local phoenixFDClasses = #(LiquidSim, FireSmokeSim, PHXSimulator) 										--Array of supported simulator classes
			local PhoenixFDObjectsAll = for o in objects where findItem phoenixFDClasses (classof o) > 0 and (getUserProp o "phxgroupname") ==undefined and (getUserProp o "phx_system_id") ==undefined  collect o --collect all simulators
			local canSubmitJob = true																				--We start by assuming that a submission is possible, then we will lower the flag if something is not kosher
			local txt = "SUBMIT a Phoenix FD SIMULATION Job to Deadline..."											--Show the default Submit caption
			
			if PhoenixFDObjectsExport.count == 0 do																	--If no objects were enabled for submission,
			(
				txt = "NO Phoenix FD Objects has been CHECKED for Simulation!"
				canSubmitJob = false
			)
			if PhoenixFDObjectsAll.count == 0 do																	--If no PFD objects were found, 
			(
				txt = "NO Phoenix FD Objects have been FOUND in the Scene!"
				canSubmitJob = false
			)

			if not (UseSimCacheOutput and doesFileExist SimCacheOutput) do	--If the override is not active or not a valid path, see if any of the objects to simulate have a $token or are rooted at C:
			(
				if (for o in PhoenixFDObjectsAll where findItem PhoenixFDObjectsExport o.name > 0 and ((matchPattern o.simoutput pattern:"*$*" and matchPattern maxFilePath pattern:"c:\\*") or matchPattern o.simoutput pattern:"c:\\*") collect o).count > 0 do
				(
					txt = "At least one Object uses a LOCAL SIMULATION PATH, and no Directory Override has been specified.\n\nPlease repath the simulator, or enable a valid Directory Override!"
					canSubmitJob = false
				)
			)
			#(canSubmitJob, txt)
		),
		
		fn submitJob =	--called when the SUBMIT button is pressed
		(
			local phoenixFDClasses = #(LiquidSim, FireSmokeSim, PHXSimulator) 										--Array of supported simulator classes
			local PhoenixFDObjectsAll = for o in objects where findItem phoenixFDClasses (classof o) > 0 and (getUserProp o "phxgroupname") ==undefined and (getUserProp o "phx_system_id") ==undefined  collect o --collect all simulators
			local PhoenixFDObjectsToSim = for o in PhoenixFDObjectsAll where findItem PhoenixFDObjectsExport o.name > 0 collect o --Collect the objects checked for simulation
			if PhoenixFDObjectsToSim.count == 0 do 																	--If no objects have been collected
			(
				try(SMTD_MainRollout.Ui_report ("--No Phoenix FD Simulations checked for submission!"))catch()		--print a message
				return false																						--exit
			)
			local MAXFile = getFileNameFile maxfilename																--Get the file name of the scene
			if MAXFile == "" do MAXFile = "Untitled_PhoenixFD_Sim"													--If the scene was not saved yet, use a custom default name
				
			local old_SMTDSettings = copy SMTDSettings																--Store a copy of the current SMTDSettings values in a variable to restore after submission
			
			SMTDFunctions.createSubmissionFolderAndUpdatePaths() 													--create a sub-folder with date and time for submission (this avoids conflicts with other parallel sessions of 3ds Max submitting at the same time)
			
			SMTDSettings.JobName = MAXFile + " [PhoenixFD Simulation]"												--Set the job name based on the scene name with a PFD Sim suffix
			
			--Include the simulator names in the default comment
			local txt = "" as stringStream 																			--Start an empty stringStream
			format "3ds Max % Simulating PhoenixFD Object%: " (SMTDFunctions.getMaxVersion()) (if PhoenixFDObjectsToSim.count > 1 then "s" else "") to:txt		--Output the base comment listing the simulators' count to the stringStream
			for i = 1 to PhoenixFDObjectsToSim.count do 																--Loop through the names of objects checked for simulation
				format "[%]%" PhoenixFDObjectsToSim[i].name (if i < PhoenixFDObjectsToSim.count then "," else "") to:txt		--If the name is not the last on the list, add a comma behind the name, otherwise do not
			
			local formattedComment = SMTDFunctions.FormatComment SMTDSettings.Comment defaultTokenValue:txt
			SMTDSettings.Comment = formattedComment
			if SMTDSettings.Comment == "" do SMTDSettings.Comment = txt												--if the comment is still empty, set it
			
			SMTDSettings.ChunkSize = 1																				--Force a chunk size of 1
			SMTDSettings.SubmitAsMXSJob = true																		--Enable the MAXScript Job option

			renderSceneDialog.close()																				--Close the render scene dialog to ensure all settings are updated
			
			--Store previous states of render scene dialog before modifying them
			local old_rendTimeType = rendTimeType
			local old_rendStart = rendStart
			local old_rendEnd = rendEnd
			
			rendTimeType = 3																						--Set the time type to a range
			rendStart = 1																							--starting from 1
			rendEnd = PhoenixFDObjectsToSim.count																	--with frame count equal to the number of simulators to process - each Deadline task will process one simulator!
			
			local backupSimOutputPaths = #()																		--Initialize an array to hold the original output paths
			local backupSimInputPaths = #()																			--Initialize an array to hold the original input paths
			if UseSimCacheOutput and doesFileExist SimCacheOutput then												--If the Override is enabled and the path is valid,
			(
				local simPath = SimCacheOutput																		--Take the override path into a variable for processing
				if simPath[simPath.count]!="\\" do simPath += "\\"													--Make sure it ends with a backslash
				for i = 1 to PhoenixFDObjectsAll.count where findItem PhoenixFDObjectsExport PhoenixFDObjectsAll[i].name > 0 do	--Loop through all objects checked for simulation,
				(
					local phoenixNode = PhoenixFDObjectsAll[i]														--Get the i-th object from the array as the current one
					append backupSimOutputPaths phoenixNode.simoutput												--Collect the output path into the backup array
					append backupSimInputPaths phoenixNode.rendinput												--Collect the input path into the backup array

					phoenixNode.rendinput = "$(same_as_output)"														--Set the input path to the Same As Output token 
					simFileName = if matchPattern phoenixNode.simoutput pattern:"*$*" then							-- If the output path contains any Phoenix macros, we can't be certain about the filename,
						"ND" + (phoenixNode.inode.handle as string) + "_" + phoenixNode.name + "_####.aur"			--so we use the node handle and the node name to build the new file name
					else	
						filenameFromPath phoenixNode.simoutput														--otherwise we just grab the filename from the existing path
					phoenixNode.simoutput = simPath + simFileName													--and assign the file name prefixed by the new override path to the object
				)--end i loop
			)--end if
			
			local maxFileToSubmit = SMTDPaths.submitSubFolder + MAXFile + ".max" 									--The MAX file will be stored in the dated sub-folder
			SMTDFunctions.SaveMaxFileCopy maxFileToSubmit															--Save the scene under the new file name without changing the scene's path
			
			SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile 											--use the dated sub-folder's path to create the JPB fole
			local theHandle = openFile SMTDPaths.SubmitInfoFile mode:"at"											--then open the resulting file for append writes
			local cnt = 0																							--start a counter at 0 for the number of output paths to show in the Monitor
			for i = 1 to PhoenixFDObjectsToSim.count do																--loop through all objects to be simulated once again,
			(
				format "OutputDirectory%=%\n" cnt (getFileNamePath PhoenixFDObjectsToSim[i].simoutput) to:theHandle	--and append the sim path as OutputDirectory entry
				format "OutputFilename%=%\n" cnt (filenameFromPath PhoenixFDObjectsToSim[i].simoutput) to:theHandle	--and the filename portion as OutputFilename entry
				cnt+=1																								--increment the counter for the next iteration
			)--end i loop
			close theHandle																							--close the file handle
			
			SMTDFunctions.CreateJobInfoFile SMTDPaths.JobInfoFile													--Create the second Job file
			local theHandle = openFile SMTDPaths.JobInfoFile mode:"at"												--Open the resulting file for append writes
			with printAllElements on format "PhoenixFDToSimulate=%" (for o in PhoenixFDObjectsToSim collect o.name) to:theHandle				--and output the names of the nodes to be simulated to a new key=value pair,
			close theHandle																							--then close the file handle
			local SimulationScriptPath = SMTDPaths.MainSubmissionDir + "\\Workflows\\MAXScriptJob_SimulatePhoenixFD.ms"
			local initialArgs = "\""+SMTDPaths.SubmitInfoFile+"\" \""+SMTDPaths.JobInfoFile+"\" \""+maxFileToSubmit+"\" \""+SimulationScriptPath+"\" "	--define the command line arguments to call deadlineCommand with - the two JOB files, the MAX file, and the sim.script
			local result = SMTDFunctions.waitForCommandToComplete initialArgs SMTDSettings.TimeoutSubmission		--call the deadline command with the arguments defined above, and wait for it to return a result
			
			local renderMsg = SMTDFunctions.getRenderMessage()														--Get the message from deadlinecommand
			SMTDFunctions.getJobIDFromMessage renderMsg																--Extract the JobID from the message

			
			if result == #success then 
			(
				try(SMTD_MainRollout.Ui_report ("+Phoenix FD Simulation Submitted Successfully!\n"+renderMsg))catch()
			)
			else 
			(
				try(SMTD_MainRollout.Ui_report ("--Phoenix FD Simulation Submission FAILED!\n"+renderMsg))catch()
			)
			
			--Restore previous time values
			rendTimeType = old_rendTimeType
			rendStart = old_rendStart
			rendEnd = old_rendEnd		
			for p in getPropNames SMTDSettings do 																	--Restore all settings in the SMTDSettings struct to avoid influencing an SMTD UI running in the same session
				try(setProperty SMTDSettings p (getProperty old_SMTDSettings p) )catch()
			
			if UseSimCacheOutput and doesFileExist SimCacheOutput and not permanentSceneChange do					--If overrides were requested, but the permanent option is unchecked,
			(
				for i=1 to PhoenixFDObjectsAll.count where PhoenixFDObjectsExport[i] == true do 					--Loop through all nodes checked for simulation
				(
					local phoenixNode = PhoenixFDObjectsAll[i]														--Get the i-th node
					phoenixNode.simoutput[i] = backupSimOutputPaths[i]												--and restore the simulation output from the backup array
					phoenixNode.rendinput[i] = backupSimInputPaths[i]												--and restore the render cache input from the backup array
				)--end i loop
			)--end if
		)
	)
	::SMTDWorkflow_PhoenixFD = SMTDWorkflow_PhoenixFDStruct()--return an instance of the struct
)
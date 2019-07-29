(
	--------------------------------------------------------
	-- MAXCmd2Deadline Sanity Check
	-- Deadline submission profiling script for 3dsmax
	-- Copyright (c) 2004-2017 by Thinkbox Software Inc
	-- All rights reserved.
	--------------------------------------------------------
	-- Code by Bobo:
	-- 2005/06/27 - Added checks for output file containing PROJECTS and mismatching scene and output PREFIX
	-- 2004/09/30 - Fixed Brazil Camera errors, added Internal check for rendering sequences to Y:
	-- 2004/06/16 - Checkboxes for skipping single tests, status lamp for passed/failed, sticky screen position, 
	--				Added check for Untitled file name,
	-- 				Changed SanityCheck function name to MAXCmd2Deadline_PerformSanityCheck
	-- 2004/06/15 - Fixed listview bg colot to work with dark UI scheme, added tests for MOV files, trailing numbers, added status report line between the listviews.
	-- 2004/06/15 - Changed to ListView ActiveX control. Added tests and fixes for render time and path
	-- 2004/06/11 - Initial version. Checks for empty scene, camera view, mpass mblur and mblur duration implemented.
	--------------------------------------------------------
	
	global MAXCmd2Deadline_PerformSanityCheck 
	global MaxCmd2DeadlineSanityCheckFunctions
	global MaxCmd2Deadline_SanityCheck_errorReportRollout
	global MaxCmd2Deadline_SanityCheck_actionsArray = #()
	global MaxCmd2Deadline_ErrorMessagesArray = #()	
	global SanityCheck_errorReportIndexArray = #()
	
	struct MaxCmd2DeadlineSanityCheckFunctions
	(
		fn GetRendererIdString =
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
				
				default: ""
			)   
		),
		fn CheckForEmptyScene = 
		(
			(objects as array).count > 0
		),
		fn CheckForDuplicateCameraName =
		(
			duplicatesFound = false
			
			local theCameras = for o in objects where findItem Camera.classes (classof o) > 0 collect o
			local theObjects = for o in objects where findItem Camera.classes (classof o) == 0 collect o
			if (theCameras as array).count > 0 then
			(
				for i = 1 to theCameras.count do
				(
					cameraName = theCameras[i].name
					for j = (i + 1) to theCameras.count do
					(
						if cameraName == theCameras[j].name then
						(
							duplicatesFound = true
							exit
						)
					)
					
					if duplicatesFound then exit
					
					for j = 1 to theObjects.count do
					(
						if cameraName == theObjects[j].name then
						(
							duplicatesFound = true
							exit
						)
					)
					
					if duplicatesFound then exit
				)
			)
			
			duplicatesFound == false
		),
		fn CheckForCameraView =
		(
			if MaxCmd2DeadlineSanityCheckFunctions.GetRendererIdString() != "maxwell" then
				viewport.getCamera() != undefined
			else
				true
		),
		fn CheckForMaxwellCameraView =
		(
			if MaxCmd2DeadlineSanityCheckFunctions.GetRendererIdString() == "maxwell" then
				viewport.getCamera() != undefined
			else
				true
		),
		fn CheckForMPassRenderer =
		(
			rendClass = substring (( classof renderers.current) as string) 1 3
			rendClass == "Bra" or rendClass == "Def"
		),
		fn CheckForRenderingSingleFrame =
		(
			rendTimeType > 1
		),
		fn CheckForRenderOutputPath =
		(
			rendOutputFilename != ""
		),
        fn CheckForSaveOutput =
        (
            rendSaveFile
        ),
		fn CheckForLocalDrive =
		(
			local drive_letter = substring rendOutputFilename 1 2
			not (drive_letter == "C:" or drive_letter == "D:" or drive_letter == "E:")
		),
		
		fn CheckForRenderOutputTrail =
		(
			try
			(
				theFileName = getFileNameFile rendOutputFilename
				theFileType = getFileNameType rendOutputFilename
				if theFileType != ".mov" and theFileType != ".avi" and theFileType != ".MOV" and theFileType != ".AVI" then
				(
					if theFileName.count > 3 then
						not (classof (execute (substring theFileName theFileName.count 1)) == Integer and classof (execute (substring theFileName (theFileName.count-3) 4)) != Integer )
					else
						true
				)
				else true
			)catch(true)
		),
		fn CheckForRenderOutputMovie =
		(
			theFileType = getFileNameType rendOutputFilename
			not (theFileType == ".mov" or theFileType == ".avi" or theFileType == ".MOV" or theFileType == ".AVI")
		),
		fn CheckForUntitledFile =
		(
			MaxFileName != ""
		),
		fn CheckForDistributedRendering =
		(
			try
			(
				theRenderClass = substring ((classof renderers.current) as string) 1 3
				case theRenderClass of
				(
					"men" : not (renderers.current.DistributedEnable)
					"VRa" : not (renderers.current.system_distributedRender)
					"V_R" : not (renderers.current.system_distributedRender)
					default: true
				)
			)catch(true)
		),
		fn CheckForValidGpuDevices =
		(
			if (M2DSettings.GpuDevices != undefined) AND (M2DSettings.GpuDevices != "") AND (M2DSettings.GpusPerTask == 0) then
			(
				local rx = dotnetobject "System.Text.RegularExpressions.Regex" "^(\d{1,2}(,\d{1,2})*)?$"
				if rx.isMatch M2DSettings.GpuDevices then true else false
			)
			else true
		),
		fn CheckForGpuConcurrentTasks =
		(
			if (M2DSettings.GpuDevices != undefined) AND (M2DSettings.GpuDevices != "") AND (M2DSettings.GpusPerTask == 0) then
			(
				if DlgMax2DeadlineRollout.spn_concurrentTasks.value > 1 then false else true
			)
			else true
		),
		fn CheckForBadCameraNames =
		(
			local badCamNames=#()
			local theCameras = for o in objects where findItem Camera.classes (classof o) > 0 collect o.name
			if (theCameras as array).count > 0 then
			(
				for n in 1 to theCameras.count do
				(
					tempString = trimLeft theCameras[n]
					tempString = trimRight tempString
					if tempString.count != theCameras[n].count do append badCamNames theCameras[n]
				)
			)
			badCamNames.count == 0
		)
	)
	
	struct MaxCmd2DeadlineRepairFunctions
	(
		fn doNothing = 
		(
			true
		),
		fn cannotFix =
		(
			MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "FATAL" (color 0 0 255) true  ("Please load a new MAX file or create/merge objects before submitting!")
		),	
		fn SuggestPossibleCamera = 
		(
			if (Cameras as array).count > 0 then
			(
				possibleCamera = SelectByName single:true title:"Select Camera to Submit to Deadline:" filter:(fn filterCamera obj = (superclassof obj == Camera))
				if possibleCamera != undefined then
				(
					viewport.setCamera possibleCamera 
					MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true ("Camera ["+ possibleCamera.name +"] set in the current viewport.")
				)	
				else
					MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "FAILED" (color 0 0 255) true "No Camera was selected."
			)	
			else
				MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "FAILED" (color 0 0 0) true "There are NO CAMERAS in the scene."

		),
		fn FixRenderingSingleFrame =
		(
			renderSceneDialog.close()
			rendTimeType = 2
			renderSceneDialog.open()
			MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Rendering Output Time changed to ACTIVE TIME SEGMENT"
		),
		fn FixRenderOutputPath =
		(
			renderSceneDialog.open()
			MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, Pick a valid path, then double-click again to re-test!"
		),
        fn FixSaveOutput =
        (
			renderSceneDialog.close()
			rendSaveFile = true
			renderSceneDialog.open()
        ),
		fn FixRenderOutputTrail =
		(
			rendOutputFilename = getFileNamePath rendOutputFilename + getFileNameFile rendOutputFilename + "_" + getFileNameType rendOutputFilename
		),
		fn FixRenderOutputMovie =
		(
			renderSceneDialog.open()
			MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, please select a single frame format, then double-click again to re-test!"
		),
		fn SaveUntitledFile =
		(
			MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "File>Save As dialog is OPEN. Please save the scene to a file, then double-click again to re-test!"
			max file save 
		),
		fn FixDistributedRendering =
		(           
			try
			(
				theRenderClass = substring ((classof renderers.current) as string) 1 3
				case theRenderClass of
				(
					"men" : renderers.current.DistributedEnable = false
					"VRa" : renderers.current.system_distributedRender = false
					"V_R" : renderers.current.system_distributedRender = false
		                )
			)
			catch()
		),
		fn SuggestValidGpuSyntax =
		(
			MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "Trailing 'commas' should be removed. Valid Examples: 0 or 2 or 0,1,2 or 0,3,4 etc"
		),
		fn FixGpuConcurrentTasks =
		(
			DlgMax2DeadlineRollout.spn_concurrentTasks.value = 1
			MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Concurrent Tasks set to 1."
		),
		fn FixBadCameraNames =
		(
			local theCameras = for o in objects where findItem Camera.classes (classof o) > 0 collect o
			for n in 1 to theCameras.count do
			(
				theCameras[n].name = (trimLeft (trimRight theCameras[n].name) )
			)
			MaxCmd2Deadline_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Removed BAD characters from Camera names."
		)
	)
	
	global MaxCmd2Deadline_SanityChecksToPerform =
	#(
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForEmptyScene, #fail, "The scene does not contain ANY objects!", MaxCmd2DeadlineRepairFunctions.cannotFix, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForUntitledFile, #fix, "The current Scene Name is Untitled.", MaxCmd2DeadlineRepairFunctions.SaveUntitledFile, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForCameraView, #fix, "The current view is NOT a Camera.", MaxCmd2DeadlineRepairFunctions.SuggestPossibleCamera, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForRenderingSingleFrame, #fix, "The Render Time Output is set to SINGLE FRAME!", MaxCmd2DeadlineRepairFunctions.FixRenderingSingleFrame, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForLocalDrive, #fix, "The Render Output Path appears to point at a LOCAL DRIVE!", MaxCmd2DeadlineRepairFunctions.FixRenderOutputPath, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForRenderOutputTrail, #fix, "The Render Output File Name ends with a DIGIT - trailing numbers might fail.", MaxCmd2DeadlineRepairFunctions.FixRenderOutputTrail, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForRenderOutputPath, #warn, "The Render Output Path is NOT DEFINED!", MaxCmd2DeadlineRepairFunctions.FixRenderOutputPath, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForRenderOutputMovie, #warn, "The Render Output is set to a MOVIE format.", MaxCmd2DeadlineRepairFunctions.FixRenderOutputMovie, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForSaveOutput, #fix, "The Render Output will not be saved to a file.", MaxCmd2DeadlineRepairFunctions.FixSaveOutput, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForDistributedRendering, #fix, "The Distributed Rendering option is enabled for this renderer.", MaxCmd2DeadlineRepairFunctions.FixDistributedRendering, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForMaxwellCameraView, #fail, "Maxwell is the renderer and the current view is NOT a Camera.", MaxCmd2DeadlineRepairFunctions.SuggestPossibleCamera, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForDuplicateCameraName, #fail, "The scene contains objects or groups with the same name as a camera!", MaxCmd2DeadlineRepairFunctions.cannotFix, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForValidGpuDevices, #fail, "'Select GPU Devices' syntax is invalid! Trailing 'commas' if present, should be removed.", MaxCmd2DeadlineRepairFunctions.SuggestValidGpuSyntax, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForGpuConcurrentTasks, #fail, "If using 'Select GPU Devices', then 'Concurrent Tasks' must be set to 1!", MaxCmd2DeadlineRepairFunctions.FixGpuConcurrentTasks, true),
		#(MaxCmd2DeadlineSanityCheckFunctions.CheckForBadCameraNames, #fail, "At least one camera name has whitespace, newline, or tab at start/end of camera name.", MaxCmd2DeadlineRepairFunctions.FixBadCameraNames, true)
	)
	
	try(destroyDialog MAXCmd2Deadline_SanityCheck_errorReportRollout)catch()
	
	rollout MAXCmd2Deadline_SanityCheck_errorReportRollout "The Sanity Check Found The Following Problems:"
	(
		local disableEvents = true
		fn initListView lv theType =
		(
			lv.Items.clear()
			lv.gridLines = true
			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB 221 221 225
			lv.FullRowSelect = true
			lv.hideSelection = true
			
			case theType of
			(
				1:
				(
					lv.checkboxes = true
					lv.Columns.add "Error Type" 90
					lv.Columns.add "Error Description" 500
					lv.ForeColor = (dotNetClass "System.Drawing.Color").Red
					lv.multiSelect = false
				)
				2:
				(
					lv.checkboxes = false
					lv.Columns.add "Type" 70
					lv.Columns.add "Message" 520
					lv.ForeColor = (dotNetClass "System.Drawing.Color").DarkBlue
					lv.multiSelect = true
				)
			)		
		)	

		fn fillInSpreadSheet lv theArray =
		(
			lv.Items.clear()
			total_count = theArray.count
			theRange = #()
			for i = 1 to total_count  do
			(
				li = dotNetObject "System.Windows.Forms.ListViewItem" theArray[i][1][2]
				try(li.checked = MaxCmd2Deadline_SanityChecksToPerform[(theArray[i][3])][5])catch()
				li.forecolor = (dotNetClass "System.Drawing.Color").fromARGB theArray[i][1][1].b theArray[i][1][1].g theArray[i][1][1].r
				--li.bold= theArray[i][1][3]
				
				for j = 2 to theArray[i].count do
				(
					li2 = li.SubItems.add (theArray[i][j] as string)
					li2.forecolor = (dotNetClass "System.Drawing.Color").fromARGB theArray[i][1][1].b theArray[i][1][1].g theArray[i][1][1].r
					--li2.bold= theArray[i][1][3]					
				)	
				append theRange li
			)
			lv.Items.AddRange theRange
			for i = 1 to total_count do
				lv.items.item[i-1].forecolor = (dotNetClass "System.Drawing.Color").fromARGB theArray[i][1][1].b theArray[i][1][1].g theArray[i][1][1].r
		)	
		
		fn getSelection lv =
		(
			for i in 0 to lv.Items.count-1 do
			(
				li = lv.Items.item[i]
				if li.selected do return (i+1)
			)
			0
		)
		
		fn setSelection lv index =
		(
			try(lv.Items[index].selected = true)catch()
		)	
		
		fn CollectCheckedStates lv =
		(
			for i in 0 to lv.Items.count-1 do
			(
				try
				(
					li = lv.Items.item[i]
					MaxCmd2Deadline_SanityChecksToPerform[MaxCmd2Deadline_ErrorMessagesArray[i+1][3]][5] = li.checked 
				)catch()	
			)
		)
		
		
------------------------
--UI		
------------------------		

		label lbl_info "Right-click Error to attempt fix. Uncheck to ignore non-fatal errors and warnings." align:#left
		dotNetControl lv_errors "System.Windows.Forms.ListView" width:595 height:150 align:#center offset:[0,0]
		label lb_errors align:#left across:2 
		progressbar prb_status value:100 color:(color 0 255 0) align:#right height:16 width:50 offset:[0,-1]
		dotNetControl lv_actions "System.Windows.Forms.ListView" width:595 height:150 align:#center offset:[0,0]
		fn CollectCheckedAndTest =
		(
			CollectCheckedStates lv_errors
			MAXCmd2Deadline_PerformSanityCheck()
		)
		fn log_action thePrefix theColor theBold theMessage =
		(
			insertItem #(#(theColor, thePrefix, theBold ),theMessage) MaxCmd2Deadline_SanityCheck_actionsArray 1
			fillInSpreadSheet lv_actions MaxCmd2Deadline_SanityCheck_actionsArray
			--setSelection lv_actions 1
		)

		on lv_errors MouseClick itm do 
		(
			if itm.Button.Equals itm.Button.Right then
			(
				theItem= getSelection lv_errors
				if theItem> 0 then
				(
					MaxCmd2Deadline_SanityChecksToPerform[SanityCheck_errorReportIndexArray[theItem]][4]()
					CollectCheckedAndTest()
					setSelection lv_errors theItem
				)
			)	
		)
		
		on lv_actions MouseClick itm do
		(
			if itm.Button.Equals itm.Button.Right then
			(
				text = ""
				for i in 0 to lv_actions.Items.count-1 do
				(
					li = lv_actions.Items.item[i]
					if li.selected then
						text = text + li.SubItems.item[0].Text + ": " + li.SubItems.item[1].Text + "\n"
				)
				setclipboardText text
			)
		)
		
		on lv_errors ItemChecked arg do 
		(
			CollectCheckedStates lv_errors
			MAXCmd2Deadline_PerformSanityCheck updateOnly:true
		)
		
		on lv_errors DoubleClick do CollectCheckedAndTest()
		on lv_actions DoubleClick do CollectCheckedAndTest()
		
		on MaxCmd2Deadline_SanityCheck_errorReportRollout lbuttondown pnt do CollectCheckedAndTest()			
		on MaxCmd2Deadline_SanityCheck_errorReportRollout rbuttondown pnt do CollectCheckedAndTest()			
		
		on MaxCmd2Deadline_SanityCheck_errorReportRollout moved pnt do 
			setIniSetting (GetDir #plugcfg + "/SMTDSanityCheck.ini") "Dialog" "Position" (pnt as string)
	)
	
-------------------------------------------
--MAIN FUNCTION
-------------------------------------------
	fn MAXCmd2Deadline_PerformSanityCheck updateOnly:false =
	(	
		MAXCmd2Deadline_ErrorMessagesArray = #()
		local fatalCount = 0
		local fixCount = 0
		local warnCount = 0
		local totalCount = 0
		
		SanityCheck_errorReportIndexArray = #()		
		if renderSceneDialog.isOpen() do renderSceneDialog.commit()
		
		for c = 1 to MAXCmd2Deadline_SanityChecksToPerform.count do
		(
			if not ((MAXCmd2Deadline_SanityChecksToPerform[c][1])()) do 
			(	
				append SanityCheck_errorReportIndexArray c
				error_prefix = ""
				case MAXCmd2Deadline_SanityChecksToPerform[c][2] of
				(
					#fail: 
					( 
						error_prefix = "FATAL" 
						error_color = color 0 0 255
						error_bold = true
						fatalCount += 1
						totalCount += 1
					)	
					#fix: 
					(
						error_prefix = "Non-Fatal"
						error_color = color 0 100 0
						error_bold = false
						fixCount += 1
						if MAXCmd2Deadline_SanityChecksToPerform[c][5] do totalCount +=1
					)	
					#warn:  
					(
						error_prefix = "Warning"
						error_color = color 100 0 0 
						error_bold = false
						warnCount += 1
					)	
				)
				append MAXCmd2Deadline_errorMessagesArray ( #(#(error_color, error_prefix, error_bold), MAXCmd2Deadline_SanityChecksToPerform[c][3], c ))
			)	
		)	
		if SanityCheck_errorReportIndexArray.count > 0 then
		(
			if not MAXCmd2Deadline_SanityCheck_errorReportRollout.Open do 
			(
				val = getIniSetting (GetDir #plugcfg + "/MAXCmd2DeadlineSanityCheck.ini") "Dialog" "Position" 
				if val != "" then 
				(
					thePos = execute val 
					createDialog MAXCmd2Deadline_SanityCheck_errorReportRollout 600 340 thePos.x thePos.y
				)
				else
					createDialog MAXCmd2Deadline_SanityCheck_errorReportRollout 600 340 
						
				MAXCmd2Deadline_SanityCheck_errorReportRollout.initListView MAXCmd2Deadline_SanityCheck_errorReportRollout.lv_errors 1
				MAXCmd2Deadline_SanityCheck_actionsArray = #()
				MAXCmd2Deadline_SanityCheck_errorReportRollout.log_action "Info" (color 155 0 0) false "Initializing Sanity Check..."
				MAXCmd2Deadline_SanityCheck_errorReportRollout.initListView MAXCmd2Deadline_SanityCheck_errorReportRollout.lv_actions 2
				MAXCmd2Deadline_SanityCheck_errorReportRollout.log_action "Info" (color 155 0 0) false "Done."
			)
			
			if not updateOnly do
			(
				MAXCmd2Deadline_SanityCheck_errorReportRollout.fillInSpreadSheet MAXCmd2Deadline_SanityCheck_errorReportRollout.lv_errors MAXCmd2Deadline_errorMessagesArray
				MAXCmd2Deadline_SanityCheck_errorReportRollout.fillInSpreadSheet MAXCmd2Deadline_SanityCheck_errorReportRollout.lv_actions MAXCmd2Deadline_SanityCheck_actionsArray
			)
			
			txt = ("Detected " + SanityCheck_errorReportIndexArray.count as string + " potential problems: "+fatalCount as string +" Fatal, "+ fixCount as string +" Fixable, ")
			if warnCount == 1 then
				txt += "1 Warning." 
			else
				txt += warnCount as string +" Warnings."
			txt += " Right-click items to copy to clipboard."
				
			if totalCount == 0 then 
				MAXCmd2Deadline_SanityCheck_errorReportRollout.prb_status.color = (color 0 255 0) 
			else 
				MAXCmd2Deadline_SanityCheck_errorReportRollout.prb_status.color = (color 255 0 0) 
			MAXCmd2Deadline_SanityCheck_errorReportRollout.lb_errors.text = txt
			totalCount == 0 
		)
		else
		(	
			destroyDialog MAXCmd2Deadline_SanityCheck_errorReportRollout
			true	
		)	
	)
)

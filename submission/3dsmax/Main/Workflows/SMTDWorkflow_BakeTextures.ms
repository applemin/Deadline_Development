(
	global SMTDWorkflow_BakeTextures
	global SMTD_BakeJobOptionsRollout
	global SMTD_BakeToTextureRollout
	rollout SMTD_BakeToTextureRollout "Render to Texture"
	(
		local isUpdating = false
		
		button btn_update "UPDATE List With Scene Objects Containing Valid And Enabled Texture Bake Elements"  width:480 offset:[0,-3] align:#center --tooltip:"Add the selected object in the scene to the list of objects to bake." offset:[-10,-3] across:3
		
		dotNetControl dnc_objectsToBake "System.Windows.Forms.ListView" width:480 height:120 align:#center offset:[0,-3]
		
		checkbox chk_BakeJobOneObjectPerTask "One Object Per Task" across:4  align:#left offset:[0,0]
		button btn_checkBySelection "Get From Selection" offset:[20,-2] width:110 align:#center  tooltip:"Check the objects currently selected in the scene.\n\nUncheck the ones that are not selected in the scene."
		dropdownlist ddl_nss offset:[34,-2] align:#center width:140 tooltip:"Named Selection Sets in the scene.\n\nUse the button to the right to check objects from the selected NSS.\n\nPress the UPDATE button on top of the rollout to refresh if new NSS have been created."
		button btn_checkByNamedSelection "Get From NSS" offset:[12,-2] align:#right width:80 tooltip:"Check the objects in the specified Named Selection Set.\n\nUncheck the ones that are not in the NSS.\n\nUncheck ALL If no NSS available."
	   
		fn initListView lv=
		(
			lv.gridLines = true  
			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.fullRowSelect = true 
			lv.checkboxes = true
			lv.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r (SMTD_ColorPalette.maxBgColor.g+5) (SMTD_ColorPalette.maxBgColor.b+15)
			lv.LabelEdit = false
			local column1 = lv.Columns.add "Object To Bake" 150
			--local column2 = lv.Columns.add "Bake" 50
			local column3 = lv.Columns.add "Bake Elements" 300
		)
		fn populateListView lv =
		(
			isUpdating = true
			lv.items.clear()
			local theRange = #()
			local obj = ::SMTDWorkflow_BakeTextures.ObjectsToBake
			for i = 1 to obj.count do
			(
				local isChecked = false
				local objectName = "<deleted>"
				if isValidNode obj[i][1] do 
				(
					objectName = obj[i][1].name 
					isChecked = obj[i][2]
				)
				local li = dotNetObject "System.Windows.Forms.ListViewItem" objectName
				--local bakeIsOn = "--"
				if isValidNode obj[i][1] do
				(
					local numBakeEls = obj[i][1].INodeBakeProperties.numBakeElements()
					--bakeIsOn = (if obj[i][1].INodeBakeProperties.bakeEnabled then "YES" else "no")
					local theSS = "" as stringStream
					format "%" (numBakeEls as string) to:theSS
					if numBakeEls > 0 then
					(
						format ": " to:theSS
						for anElement = 1 to numBakeEls-1 do format "%," (classof (obj[i][1].getBakeElement anElement)) to:theSS
						format "%" (classof (obj[i][1].getBakeElement numBakeEls)) to:theSS
					)
					else isChecked = false
					--sub_li = li.SubItems.add bakeIsOn
					sub_li = li.SubItems.add (theSS as string)
				)
				::SMTDWorkflow_BakeTextures.ObjectsToBake[i][2] = li.checked = isChecked
				append theRange li
			)	
			lv.Items.AddRange theRange
			isUpdating = false
		)
		
		
		fn refreshBakeUI = 
		(            
			--::SMTDWorkflow_BakeTextures.ObjectsToBake = for o in objects where isValidNode o[1] collect o --filter for deleted objects
			populateListView dnc_objectsToBake
			ddl_nss.items = for i in SelectionSets collect i.name
			try(SMTD_MainRollout.updateSubmitButtonState())catch()							--Update the SUBMIT button's enabled state and text
		)
		
		fn updateObjectsToBake=
		(
			::SMTDWorkflow_BakeTextures.ObjectsToBake = for o in objects where o.INodeBakeProperties.numBakeElements() > 0 and o.INodeBakeProperties.BakeEnabled == true collect #(o, findItem ::SMTD_objsToBake o > 0 )
		)
		
		on btn_checkBySelection pressed do
		(
			::SMTD_objsToBake = selection as array
			updateObjectsToBake()
			refreshBakeUI()
		)
		on btn_checkByNamedSelection pressed do
		(
			::SMTD_objsToBake = try(for i = 1 to selectionSets[ ddl_nss.selected].count collect selectionSets[ ddl_nss.selected][i])catch(#())
			updateObjectsToBake()
			refreshBakeUI()
		)		

		on btn_update pressed do 
		(
			::SMTDWorkflow_BakeTextures.ObjectsToBake = for o in objects where o.INodeBakeProperties.numBakeElements() > 0 and o.INodeBakeProperties.BakeEnabled == true collect #(o, findItem ::SMTD_objsToBake o > 0 )
			refreshBakeUI()
		)
		on chk_BakeJobOneObjectPerTask changed state do
		(
			setIniSetting SMTDPaths.InIFile "RTT"  "BakeJobOneObjectPerTask" ( (SMTDSettings.BakeJobOneObjectPerTask = state ) as string)
			SMTD_MainRollout.Ui_report ("+Render to Texture Job One Object Per Task set to [" + state as string + "].")
		)
		
		fn selectHighlightedObject =														--Function to select the highlighted object from the ListView in the Max Modify Panel
		(
			select (for i = 1 to dnc_objectsToBake.items.count where dnc_objectsToBake.items.item[i-1].Selected and isValidNode ::SMTDWorkflow_BakeTextures.ObjectsToBake[i][1] collect ::SMTDWorkflow_BakeTextures.ObjectsToBake[i][1])	--Collect and select the object that is highlighted
			max modify mode																	--Switch the 3ds Max Command Panel to Modify mode
		)--end fn
		
		fn HighlightedObjectBakingOnOff state =												--Function to enable baking for the highlighted object from the ListView
		(
			for i = 1 to dnc_objectsToBake.items.count where dnc_objectsToBake.items.item[i-1].Selected and isValidNode ::SMTDWorkflow_BakeTextures.ObjectsToBake[i][1] do 
			(
				if state then
					appendIfUnique ::SMTD_objsToBake ::SMTDWorkflow_BakeTextures.ObjectsToBake[i][1]
				else
					try(deleteItem ::SMTD_objsToBake (findItem ::SMTD_objsToBake ::SMTDWorkflow_BakeTextures.ObjectsToBake[i][1]))catch()
			)
			updateObjectsToBake()
			refreshBakeUI()
		)--end fn		
		
		fn exploreHighlightedOutput =
		(
			for i = 1 to dnc_objectsToBake.items.count where dnc_objectsToBake.items.item[i-1].Selected do try(shellLaunch (getFileNamePath dnc_objectsToBake.items.item[i-1].subItems.Item[1].text) "")catch()
		)--end fn
		
		on dnc_objectsToBake mouseClick arg do												--If the user clicked an item with the mouse button,
		(
			rcmenu bake_rcmenu 																--Define a right-click menu to display
			(
				menuitem mnu_selectObject "SELECT Highlighted Objects In The Scene"			--Menu item to select the highlighed object
				separator sep_10
				menuItem mnu_BakingOn "ENABLE Baking For The Highlighted Objects"
				menuItem mnu_BakingOff "DISABLE Baking For The Highlighted Objects"
				--separator sep_20
				--menuitem mnu_explorePath "EXPLORE Simulation Path Of Highlighted Objects"	--Menu item to explore the output path
				
				on mnu_selectObject picked do ::SMTD_BakeToTextureRollout.selectHighlightedObject()	--If the menu item was picked from the menu, call the function to select the highlighted object defined earluer in the scope of the rollout
				on mnu_BakingOn picked do ::SMTD_BakeToTextureRollout.HighlightedObjectBakingOnOff true
				on mnu_BakingOff picked do ::SMTD_BakeToTextureRollout.HighlightedObjectBakingOnOff false
				--on mnu_explorePath picked do ::SMTD_BakeToTextureRollout.exploreHighlightedOutput()	--If the menu item was picked from the menu, call the function to explore the simulation path defined earluer in the scope of the rollout
			)--end rcmenu
			if arg.Button == arg.Button.Right do popupmenu bake_rcmenu pos:mouse.screenpos	--If the right mouse button was pressed, pop up the rcmenu at the current screen position of the mouse cursor
		)--end on mouseClicked handler		
		
		on dnc_objectsToBake MouseDoubleClick arg do 											--If the user double-clicked an item on the ListView,
		(
			if not isUpdating do 															--If the handler is not called by the ListView during its update,
				for i = 1 to dnc_objectsToBake.items.count do ::SMTDWorkflow_BakeTextures.ObjectsToBake[i][2] = dnc_objectsToBake.items.item[i-1].checked	--collect the checked states of al litems into the array
			try(SMTD_MainRollout.updateSubmitButtonState())catch()							--Update the SUBMIT button's enabled state and text
		)--end on MouseDoubleClick handler
		
		on dnc_objectsToBake ItemChecked arg do 												--If the user checked/unchecked an item on the ListView,
		(
			if not isUpdating do 
			(
				--If the handler is not called by the ListView during its update,
				for i = 1 to dnc_objectsToBake.items.count do ::SMTDWorkflow_BakeTextures.ObjectsToBake[i][2] = dnc_objectsToBake.items.item[i-1].checked	--collect the checked states of al litems into the array
				try(SMTD_MainRollout.updateSubmitButtonState())catch()							--Update the SUBMIT button's enabled state and text
			)
		)--end on ItemChecked handler		

		fn updateRolloutTitle state =
		(
			local theTitle = "Render To Texture"
			if not state do
			(
				if SMTDSettings.BakeJobOneObjectPerTask == true do theTitle += " [Object Per Task]" 
			)
			SMTD_BakeToTextureRollout.title = theTitle
		)
		
		on SMTD_BakeToTextureRollout rolledup state do
		(
			updateRolloutTitle state
		)		
		
		on SMTD_BakeToTextureRollout open do
		(
			chk_BakeJobOneObjectPerTask.state = SMTDSettings.BakeJobOneObjectPerTask
			if SMTD_objsToBake == undefined then SMTD_objsToBake = #()
			updateObjectsToBake()
			initListView dnc_objectsToBake
			refreshBakeUI()
			updateRolloutTitle SMTD_BakeToTextureRollout.open
		)
		on SMTD_BakeToTextureRollout close do
		(
			::SMTD_objsToBake = for o in ::SMTDWorkflow_BakeTextures.ObjectsToBake where o[2] == true collect o[1]
		)
	)--end bake to texture rollout
	
	local SMTDWorkflow_BakeTexturesStruct
	struct SMTDWorkflow_BakeTexturesStruct
	(
		fn isWorkflowActive = (true),	--Mandatory! Set to false to disable the workflow so it does not load in SMTD UI
		WorkflowName = "baketexture",
		WorkflowTitle= "Submit BAKE TEXTURES Job To Deadline",	--the description of the workflow displayed in the drop-down list
		Description = "Submit a Texture Baking job to be processed on Deadline Slaves.", --the detailed description used for tooltips
		ObjectsToBake = #(),
		fn defineUILayout =
		(
			#(
				#(#("Bake Job","Job Settings"),#(#(SMTD_BakeToTextureRollout, true), #(SMTD_JobOptions,true), #(SMTD_JobFailureDetection,false))), 
				#(#("Assets","Assets - Asset Collection And Synchronization"),#(#(SMTD_AssetList,true))),
				#(#("Render","Rendering,DBR, GPU, Pathing and Image Sequence Options"),#(#(SMTD_ScenePreProcessing,true), #(SMTD_MaxStartup,false), #(SMTD_MaxRendering,false), #(SMTD_Gamma,false))), 
				#(#("Options","Submission Options"),#(#(SMTD_UserOptions,true), #(SMTD_RendererExport,false), #(SMTD_SubmissionTimeouts,false))), 
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
		fn canSubmit =
		(
			local canSubmitJob = true																			--We start by assuming that a submission is possible, then we will lower the flag if something is not right
			local theEnabledObjects = (for o in ObjectsToBake where o[2] == true and isValidNode o[1] collect o[1])	--collect the enabled simulators
			local txt = "SUBMIT a TEXTURE BAKING Job to Deadline..."						
			if not renderers.current.supportsTexureBaking do
			(
				txt = "The current renderer ["+(classof renderers.current) as string +"] does not support Texture Baking!"									--Define the explanation string
				canSubmitJob = false																			--and lower the flag
			)
			if (for o in theEnabledObjects where o.INodeBakeProperties.BakeEnabled collect o).count == 0 do
			(
				txt = "The Objects have their Bake Elements disabled!\n\nPlease open the 3ds Max Render To Texture dialog and enable Texture Baking!"	--Define the explanation string
				canSubmitJob = false																			--and lower the flag
			)			
			if (for o in theEnabledObjects where o.INodeBakeProperties.numBakeElements() > 0 collect o).count == 0 do
			(
				txt = "The Objects do not have valid Bake Elements assigned!\n\nPlease open the 3ds Max Render To Texture dialog and assign Bake Elements!"	--Define the explanation string
				canSubmitJob = false																			--and lower the flag
			)
			if theEnabledObjects.count == 0 do																	--If no objects were enabled for submission,
			(
				txt = "No Objects CHECKED for Texture Baking!\n\nPlease check at least one object on the list!"	--Define the explanation string
				canSubmitJob = false																			--and lower the flag
			)
			if ObjectsToBake.count == 0 do																		--If no objects were found, 
			(
				txt = "No Objects Picked For Texture Baking.\n\nPlease select one or more in the scene and press the [ADD Scene Selection] button!"													--Define the explanation string
				canSubmitJob = false																			--and lower the flag
			)			
			#(canSubmitJob, txt)																				--return the boolean and the description as an array	
		),
		fn submitJob =	--called when the SUBMIT button is pressed
		(
			SMTDSettings.IsBakeJob = true
			local oldComment = SMTDSettings.Comment
			::SMTD_objsToBake = for o in ObjectsToBake where isValidNode o[1] AND o[2] == true collect o[1]
			
			--Include the object names in the default comment
			local txt = "" as stringStream 																			--Start an empty stringStream
			format "3ds Max % Texture Baking Object%: " (SMTDFunctions.getMaxVersion()) (if ::SMTD_objsToBake.count > 1 then "s" else "") to:txt				--Output the base comment listing the simulators' count to the stringStream
			for i = 1 to ::SMTD_objsToBake.count do 																--Loop through the names of objects checked for simulation
				format "[%]%" ::SMTD_objsToBake[i].name (if i < ::SMTD_objsToBake.count then "," else "") to:txt	--If the name is not the last on the list, add a comma behind the name, otherwise do not
			
			local formattedComment = SMTDFunctions.FormatComment SMTDSettings.Comment defaultTokenValue:(txt as string)
			SMTDSettings.Comment = formattedComment
			if SMTDSettings.Comment == "" do SMTDSettings.Comment = txt 										--if the comment is still empty, set it
			
			SMTDFunctions.SubmitJobFromUI()
			SMTDSettings.IsBakeJob = false
			SMTDSettings.Comment = oldComment 
		)
	)
	::SMTDWorkflow_BakeTextures = SMTDWorkflow_BakeTexturesStruct()--return an instance of the struct
)
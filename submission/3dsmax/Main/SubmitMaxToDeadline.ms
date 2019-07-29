(
	global TBS_Draft_Functions

	global SMTD_MainRollout
	try(destroyDialog SMTD_MainRollout)catch()

	global SMTDSettings, SMTDFunctions, SMTDSettings_copy
	global SMTDDictionaries
	global SMTD_PerformSanityCheck

	global SMTD_UserDefinedTilesDialog
	try(destroyDialog SMTD_UserDefinedTilesDialog)catch()

	global SMTD_UserDefinedTilesBitmap
	global SMTD_UserDefinedTilesBitmapDisplay = bitmap 400 300

	global SMTD_JobScheduling, SMTD_JobOptions, SMTD_JobFailureDetection, SMTD_JobSubmission, SMTD_AssetList, SMTD_MaxSceneLoading
	global SMTD_MaxRendering, SMTD_ScenePreProcessing, SMTD_Gamma, SMTD_Pathing, SMTD_IMSQ, SMTD_LimitGroups, SMTD_BatchSubmit, SMTD_StateSets, SMTD_DBR, SMTD_GPU, SMTD_BakeToTexture, SMTD_MaxStartup
	global SMTD_Dependencies, SMTD_PassDependencies, SMTD_JobEnvironmentKeys, SMTD_ExtraInfoKeyValues, SMTD_TileOptions

	global SMTD_UserOptions, SMTD_RendererExport, SMTD_SubmissionTimeouts
	global SMTD_RunScripts, SMTD_PythonScripts
	global SMTD_RolloutsLayout
	global SMTD_WorkflowsArray = #()
	global SMTDSettings_Backup
	global SubmitMaxToDeadline_PathingExplorer
	global SMTD_LegacyRolloutsLayout
	global SubmtMaxToDeadline_SettingsBrowser
	global SubmtMaxToDeadline_SubmissionSettingsExplorer

	--SMTD 10 introduced Workflows that change the UI Layout and implement alternative submission logic that can be extended by 3rd party developers and Deadline users.
	--Additional Workflows are defined in the Submission\3dsMax\Main\Workflows folder as scripts named "SMTDWorkflow_*.ms" which define structs with the same Properties and Functions.
	--The Legacy Workflow offers the original SMTD All-In-One functionality as a fallback.
	local SMTD_LegacyWorkflowStruct
	struct SMTD_LegacyWorkflowStruct
	(
		fn isWorkflowActive = (true),
		WorkflowName = "default",
		WorkflowTitle = "DEFAULT 3ds Max Submission To Deadline",
		Description = "This workflow offers all features of SMTD from previous versions in one place.",
		fn defineUILayout =
		(
			SMTD_LegacyRolloutsLayout
		),
		fn updateUILayout =
		(
		),
		fn storeSettings = --optional, store the workflow-specific settings to disk, or with the MAX scene file
		(

		),
		fn restoreSettings = --restore the workflow-specific settings from disk, or from the MAX scene file
		(

		),
		fn canSubmit =	--Updates the Submit button's enabled state and caption based on sanity checks
		(
			#(true, "")
		),
		fn SubmitJob =
		(
			--do nothing, currently hard-coded in the submit button handler
		)
	)
	local WorkflowNames = #("default")
	local loadDefaultWorkflow = true --set to false to hide the default UI and allow only custom worflows (if any) to appear on the list.

	global SMTD_BlackListSlaves, SMTD_TilesRendering, SMTD_RegionRendering, SMTD_ExtraInfo, SMTD_MultiRegionRendering

	persistent global SMTD_objsToBake

	global SMTD_PresetDialog
	global SMTD_PresetDialogMode = #save
	global SMTD_PresetIniFile = ""
	global SMTD_PresetTreeData = #()

	global SMTD_StateSetsTree = #()

	global SMTDIsCurrentlySubmitting = undefined

	--global SMTD_CategoryPatterns = #()

	local SMTD_todaysLogFile = undefined		--The file stream of the log on disk. It is created on SMTD UI start, and is kept open while the UI is open. Should SMTD crash, the file content will remain intact.
	local SMTD_todaysLogFileName = ""			--The file name of the current log. Used to open the file in an editor.
	global SMTD_LogStream = #()					--Internal storage of the log content for custom filtering/log levels
	global SMTD_LogFilters = #()				--Array of log level filters - names appearing on the list will NOT be displayed, e.g. #(#error) will show everything but errors.
	local SMTD_LogShowTimestamp = true			--Show log timestamp

	local LastSubRollout = 1
	local ShowRolloutOpenMsgInLog = false

	local SMTD_HelpURL = "http://docs.thinkboxsoftware.com/products/deadline/"+SMTDSettings.VersionString+"/1_User%20Manual/manual/app-3ds-max.html"

	local undoBuffer = #("Begin SMTD Session")
	local undoBufferData = #(#())
	local undoBufferIndex = 1

	rcmenu SMTD_MainRollout_MainMenu
	(
		subMenu "&Presets"
		(
			menuItem mnu_savePreset "&Save Preset File..."
			menuItem mnu_loadPreset "&Load Preset File..."
			separator sep_10
			menuItem mnu_explorePresetsFolder "&Explore Presets Folder..."
			separator sep_20
			menuItem mnu_loadSettingsFromScene "Reload Settings From .&MAX Scene File..."
			separator sep_30
			menuItem mnu_resetToStartupDefaults "&Reset To Startup Defaults..."
		)
		subMenu "&Tools"
		(
			menuItem mnu_openSettingsBrowser "&Defaults and Sticky Settings Browser..."
			menuItem mnu_openSubmissionExplorer "&Submission Settings Explorer..."
			separator sep_100
			menuItem mnu_exploreTempSubmissionFolder "Explore &Temporary Submission Folder..."
			menuItem mnu_purgeAllTempSubmissionFolders "&Purge All Temporary Submission Folders On SMTD Startup - when unchecked, today's folders will be kept." checked:(matchPattern (getIniSetting SMTDPaths.InIFile "TempFolders" "PurgeAll") pattern:"true")
			separator sep_110
			menuItem mnu_exploreSMTDLogFolder "Explore SMTD &Log Folder..."
			menuItem mnu_openMonitor "Open Monitor"
			menuItem mnu_renderDialog "Open Render Dialog"
		)
		subMenu "&Help"
		(
			menuItem mnu_openHelp "&SMTD Online Help..."
		)

		on mnu_purgeAllTempSubmissionFolders picked do
		(
			local purgeAllFolders = matchPattern (getIniSetting SMTDPaths.InIFile "TempFolders" "PurgeAll") pattern:"true"
			setIniSetting SMTDPaths.InIFile "TempFolders" "PurgeAll" ((not purgeAllFolders) as string)
		)

		on mnu_exploreTempSubmissionFolder picked do
		(
			shellLaunch SMTDPaths.tempDir ""
		)

		on mnu_loadSettingsFromScene picked do
		(
			/*
			local q = querybox "Are you sure you want to reload the SMTD Settings stored in the current 3ds Max scene?" title:"Reload Settings From Scene?"
			if q do
			(
				SMTDFunctions.restoreSettingstFromScene()
				SMTD_MainRollout.updateAllControls()
			)*/

			local theTempStruct = SMTDFunctions.getSettingsAsStructFromScene()
			local theChanges = for p in getPropNames theTempStruct where ((getProperty theTempStruct p) as string != (try((getProperty ::SMTDSettings p)as string)catch(undefined))) collect p
--			print theChanges
			if theChanges.count > 0 then
			(
				SMTD_MainRollout.Ui_report ("+"+theChanges.count as string+" Unique Setting"+ (if theChanges.count == 1 then "" else "s") +" found in the .MAX Scene File.")
				::SMTD_PresetDialogMode = #loadscene
				SMTD_MainRollout.displayPresetDialog()
			)
			else
				SMTD_MainRollout.Ui_report ("!!Nothing to load - current settings are identical to the ones in the .MAX Scene File.")
		)

		on mnu_exploreSMTDLogFolder picked do
		(
			try(shellLaunch "Explorer.exe" (getFileNamePath SMTD_todaysLogFileName))catch()
		)

		on mnu_savePreset picked do
		(
			::SMTD_PresetDialogMode = #save
			SMTD_MainRollout.displayPresetDialog()
		)
		on mnu_loadPreset picked do
		(
			::SMTD_PresetDialogMode = #load
			SMTD_MainRollout.displayPresetDialog()
		)

		on mnu_explorePresetsFolder picked do
		(
			local theFolder = (SMTDPaths.SettingsDir + "\\presets\\")
			makeDir theFolder all:true
			shellLaunch theFolder ""
		)

		on mnu_resetToStartupDefaults picked do
		(
			if (querybox "This will reset all non-sticky settings marked with *\nto their respective start-up defaults.\nSticky settings will retain their values.\n\nAre you sure you want to do that?" title:"Reset SMTD To Startup Defaults?") do
			(
				SMTDFunctions.loadSettings()
				SMTD_MainRollout.updateControls()
				SMTD_MainRollout.dn_tabs.enabled = false
				for subroll in SMTD_MainRollout.sub_SubRollout.Rollouts do
					removeSubRollout SMTD_MainRollout.sub_SubRollout subroll
				for subroll in SMTD_RolloutsLayout[LastSubRollout][2] do
				(
					addSubRollout SMTD_MainRollout.sub_SubRollout subroll[1]
					subroll[1].open = subroll[2]
				)
				SMTD_MainRollout.dn_tabs.enabled = true
			)
		)

		on mnu_openHelp picked do shellLaunch SMTD_HelpURL ""
		on mnu_openSettingsBrowser picked do try(fileIn (SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_SettingsBrowser.ms"))catch()
		on mnu_openSubmissionExplorer picked do try(fileIn (SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_SubmissionSettingsExplorer.ms"))catch()
		on mnu_openMonitor picked do
		(
			SMTD_MainRollout.Ui_report ">Launching External Application: DeadlineMonitor"
			shellLaunch (SMTDPaths.BinDir + "DeadlineMonitor.exe") ""
		)
		on mnu_renderDialog picked do
		(
			if renderSceneDialog.isOpen() then
			(
				SMTD_MainRollout.Ui_report ">Closing Render Scene Dialog"
				renderSceneDialog.close()
			)
			else
			(
				SMTD_MainRollout.Ui_report ">Opening Render Scene Dialog"
				renderSceneDialog.open()
			)
		)
	)

	rcmenu LogWindowOptions_RCMenu
	(
		menuItem mnu_logAll "Show ALL Messages"
		menuItem mnu_logInfoProgressSuccess "Show Only INFO, >PROGRESS and +SUCCESS Messages"
		menuItem mnu_logInfo "Show Only INFO Messages"
		menuItem mnu_logProgress "Show Only >PROGRESS Messages"
		menuItem mnu_logSuccess "Show Only +SUCCESS Messages"
		menuItem mnu_logErrorWarning "Show only --ERROR and !!WARNING Messages"
		menuItem mnu_logError "Show only --ERROR Messages"
		separator sep_10
		menuItem mnu_copySelectedLines "COPY Selected Lines to Windows CLIPBOARD"
		separator sep_20
		menuItem mnu_showLogTimestamp "TIMESTAMP Display in the Log Windows" checked:SMTD_LogShowTimestamp
		separator sep_30
		menuItem mnu_openLogDefaultEditor "OPEN the Current Log in the Default Editor for .LOG files..."
		menuItem mnu_openLogNotepad "OPEN the Current Log in Windows NOTEPAD..."
		separator sep_40
		menuItem mnu_exploreLogFolder "EXPLORE the SMTD Logs folder..."
		separator sep_50
		submenu "CLEAR/RESET Log..."
		(
			menuItem mnu_clearLogWindow "CLEAR Log Window - Changing Filters will restore full content"
			menuItem mnu_clearLogHistory "RESET Log History - Only Log File will persist"
		)

		on mnu_clearLogWindow picked do SMTD_MainRollout.initReportWindow SMTD_MainRollout.dnc_report
		on mnu_clearLogHistory picked do (::SMTD_LogStream = #(); ::SMTD_LogFilters=#(); SMTD_MainRollout.initReportWindow SMTD_MainRollout.dnc_report)
		on mnu_exploreLogFolder picked do SMTD_MainRollout.exploreLogFolder()
		on mnu_openLogNotepad picked do SMTD_MainRollout.openLogNotepad()
		on mnu_openLogDefaultEditor picked do SMTD_MainRollout.openLogDefaultEditor()
		on mnu_copySelectedLines picked do SMTD_MainRollout.copySelectedLinesFromLog()

		on mnu_logAll picked do (::SMTD_LogFilters=#(); SMTD_MainRollout.filterLog())
		on mnu_logInfoProgressSuccess picked do (::SMTD_LogFilters=#(#error,#warning); SMTD_MainRollout.filterLog())
		on mnu_logInfo picked do (::SMTD_LogFilters=#(#error,#warning,#success,#progress); SMTD_MainRollout.filterLog())
		on mnu_logProgress picked do (::SMTD_LogFilters=#(#error,#warning,#info,#success); SMTD_MainRollout.filterLog())
		on mnu_logSuccess picked do (::SMTD_LogFilters=#(#error,#warning,#info,#progress); SMTD_MainRollout.filterLog())
		on mnu_logErrorWarning picked do (::SMTD_LogFilters=#(#info,#progress,#success); SMTD_MainRollout.filterLog())
		on mnu_logError picked do (::SMTD_LogFilters=#(#info,#progress,#success,#warning); SMTD_MainRollout.filterLog())
		on mnu_showLogTimestamp picked do (SMTD_LogShowTimestamp = not SMTD_LogShowTimestamp; SMTD_MainRollout.filterLog())
	)

	local twoArrowsIconBitmap, twoArrowsIconMask, oneArrowIconBitmap, oneArrowIconMask, oneArrowIconReverseBitmap, oneArrowIconReverseMask

	rollout SMTD_MainRollout "Submit To Deadline" width:500 height:740
	(
		local theJobArray = #()
		local PresetFilterString = ""

		button btn_workflow_help "Workflow: " width:65 height:18 pos:[3,7] border:false tooltip:"Select the desired Deadline Submission Workflow from the list..."
		dropdownlist ddl_workflow width:417 pos:[69,5]

		button btn_help_jobname "Job Name:" width:65 height:20 pos:[3,28] tooltip:"The Job Name text field is populated automatically using the 3ds Max scene file name.\n\nYou can also use the [>>] button to set the text to symbolic names to be replaced with the respective value at submission time." border:false
		edittext edt_jobname "" fieldwidth:392 pos:[66,29]
		button btn_getName ">>" width:22 height:18 pos:[465,29] align:#right tooltip:"Set the current Job Name."

		button btn_help_comment "Comment:" width:65 height:20 pos:[3,48] tooltip:"The Comment text field can be used to enter a custom description of the job.\n\nYou can also use the [>>] button to set the text to a symbolic name to be replaced with the respective value at submission time." border:false
		edittext edt_comment "" fieldwidth:392 pos:[66,50]
		button btn_getComment ">>" width:22 height:18 pos:[465,50] tooltip:"Set the current Comment."

		button btn_help_user "User Name:" width:65 height:20 pos:[3,68] tooltip:"The User text field is set automatically to the currently logged user.\n\nYou can enter any name to override the current user name for the job submission." border:false
		edittext edt_user "" fieldwidth:170 pos:[66,70]
		button btn_help_dept "Department:" width:68 height:20 pos:[243,68] tooltip:"The Department text field is optional and can be used to specify the department the user belongs to.\n\nThis field can then be used in the Deadline Monitor to filter and sort by department, but has no other function." border:false
		edittext edt_dept "" fieldwidth:173 pos:[308,70]


		fn createIcons =
		(
			local twoArrowsIconData = #(
				0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
				0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,
				0,0,1,1,0,0,0,0,0,1,1,0,0,0,0,0,
				0,0,1,1,1,0,0,0,0,1,1,1,0,0,0,0,
				0,0,1,1,1,1,0,0,0,1,1,1,1,0,0,0,
				0,0,1,1,1,1,1,0,0,1,1,1,1,1,0,0,
				0,0,1,1,1,1,0,0,0,1,1,1,1,0,0,0,
				0,0,1,1,1,0,0,0,0,1,1,1,0,0,0,0,
				0,0,1,1,0,0,0,0,0,1,1,0,0,0,0,0,
				0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,
				0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
			)
			local oneArrowIconData = #(
				0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,
				0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,
				0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,
				0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,
				0,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,
				0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,
				0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,
				0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,
				0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,
				0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,
				0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
			)

			local oneArrowIconReverseData = for i = oneArrowIconData.count to 1 by -1 collect oneArrowIconData[i]

			fn copyDataToImage &dest &destMask source foreColor xOffset =
			(
				local colorPixel = foreColor
				local clearPixel = ((colorman.getcolor #background) as color)*255
				local opaque = (color 0 0 0)
				local transparent = (color 255 255 255)
				local i = 1
				for y = 0 to 15 do
				(
					local rowPixels = getPixels dest [xOffset,y] 16
					local rowMask = getPixels destMask [xOffset,y] 16
					for x = 0 to 15 do
					(
						rowPixels[x+1] = if source[i] != 0 then colorPixel else clearPixel
						rowMask[x+1] = if source[i] != 0 then opaque else transparent
						i += 1
					)
					setPixels dest [xOffset,y] rowPixels
					setPixels destMask [xOffset,y] rowMask
				)
			)

			twoArrowsIconBitmap = bitmap 32 16
			twoArrowsIconMask = bitmap 32 16
			oneArrowIconBitmap = bitmap 32 16
			oneArrowIconMask = bitmap 32 16
			oneArrowIconReverseBitmap = bitmap 32 16
			oneArrowIconReverseMask = bitmap 32 16

			copyDataToImage &twoArrowsIconBitmap &twoArrowsIconMask twoArrowsIconData ( ((colorman.getcolor #text) as color)*255) 0
			copyDataToImage &twoArrowsIconBitmap &twoArrowsIconMask twoArrowsIconData ( ((colorman.getcolor #shadow) as color)*255) 16

			copyDataToImage &oneArrowIconBitmap &oneArrowIconMask oneArrowIconData ( ((colorman.getcolor #text) as color)*255) 0
			copyDataToImage &oneArrowIconBitmap &oneArrowIconMask oneArrowIconData ( ((colorman.getcolor #shadow) as color)*255) 16

			copyDataToImage &oneArrowIconReverseBitmap &oneArrowIconReverseMask oneArrowIconReverseData ( ((colorman.getcolor #text) as color)*255) 0
			copyDataToImage &oneArrowIconReverseBitmap &oneArrowIconReverseMask oneArrowIconReverseData ( ((colorman.getcolor #shadow) as color)*255) 16

			btn_getName.images = #(twoArrowsIconBitmap,twoArrowsIconMask,2,1,1,2,2)
			btn_getComment.images = #(twoArrowsIconBitmap,twoArrowsIconMask,2,1,1,2,2)
			--SMTD_JobOptions.btn_printFrameSequenceToLog.images = #(twoArrowsIconBitmap,twoArrowsIconMask,2,1,1,2,2)
		)

		fn SetJobName index =
		(
			edt_jobname.text = SMTDSettings.Jobname = theJobArray[index][3] + "_" + theJobArray[index][4]
		)

		fn SetJobNameTo theName =
		(
			SMTDSettings.jobName = SMTD_MainRollout.edt_jobname.text = theName
			SMTD_MainRollout.Ui_report ("+Job Name Changed To OutputFile ["+ theName +"]")
		)

		fn createNameMenu =
		(
			local theINI = SMTDPaths.MainSubmissionDir
			local projectsList = getIniSetting (theINI+"Projects.ini")
			global SMTD_NamesRCMenu
			txt = "rcmenu SMTD_NamesRCMenu\n(\n"

			local jobNamesFilename =theINI + "\\JobNames.ini"
			if doesFileExist jobNamesFilename then
			(
				local jobNamesFile = openFile jobNamesFilename
				if (jobNamesFile != undefined) then
				(
					try
					(
						local count = 0
						while not eof jobNamesFile do
						(
							local fileLine = readLine jobNamesFile
							txt += "menuitem mnu_jobname" + (count as string) + " \"" + fileLine + "\"\n"
							txt += "on mnu_jobname" + (count as string) + " picked do (SMTD_MainRollout.SetJobNameTo( \"" + fileLine + "\" ))\n"
							count += 1
						)
					)
					catch ()
					try(close jobNamesFile)catch()
				)
			)
			else
			(
				txt += "menuitem mnu_jobname0 \"$scene\"\n"
				txt += "on mnu_jobname0 picked do (SMTD_MainRollout.SetJobNameTo( \"$scene\" ))\n"
				txt += "menuitem mnu_jobname1 \"$outputfilename\"\n"
				txt += "on mnu_jobname1 picked do (SMTD_MainRollout.SetJobNameTo( \"$outputfilename\" ))\n"
			)

			/*
			txt += "menuitem mnu_GetMaxName \"Set Job Name To 3ds Max Scene Name...\"\n"
			txt += "on mnu_GetMaxName picked do (SMTD_MainRollout.getNameFromMaxScene())\n"
			txt += "menuitem mnu_GetOutputName \"Set Job Name To Output File Name...\"\n"
			txt += "on mnu_GetOutputName picked do (SMTD_MainRollout.getNameFromOutputFile())\n"
			*/

			cnt = 0
			theJobArray = #()
			for i in projectsList do
			(
				txt += "subMenu \"" + i + "\" (\n"
				theSequenceKeys = getIniSetting (theINI+ i +".ini")
				theSequences = #()

				for k in theSequenceKeys do
				(
					theSequence = substring k 1 5
					if findItem theSequences theSequence == 0 do
					(
						append theSequences theSequence
					)
				)
				for j = 1 to theSequences.count do
				(
					txt += "subMenu \"" + theSequences[j] + "\" (\n"
					for s = 1 to theSequenceKeys.count where matchPattern theSequenceKeys[s] pattern:(theSequences[j]+"*") do
					(
						theKeys = getIniSetting (theINI+ i +".ini") theSequenceKeys[s]
						txt += "subMenu \"" +  theSequenceKeys[s] + "\" (\n"
						for t = 1 to theKeys.count do
						(
							cnt += 1
							txt += "menuItem mnu_"+cnt as string +" \""+ theKeys[t] + "\" \n"
							theJobArray[cnt] = #(i,theSequences[j],theSequenceKeys[s],theKeys[t])
						)
						txt += ")\n"
					)
					txt += ")\n"
				)
				txt += ")\n"
			)
			for i = 1 to cnt do
				txt += "on mnu_" + i as string + " picked do ( SMTD_MainRollout.SetJobName " + i as string + " )\n"

			txt += ")\n"
			execute txt
		)

		on btn_getName pressed do popUpMenu SMTD_NamesRCMenu pos:mouse.screenPos

		fn SetCommentTo theComment reset:false =
		(
			if reset then
				SMTDSettings.Comment = theComment+" "
			else
				if findString SMTDSettings.Comment theComment == undefined do SMTDSettings.Comment += theComment+" "

			SMTD_MainRollout.edt_comment.text = SMTDSettings.Comment
			SMTD_MainRollout.Ui_report ("+Comment Changed To ["+ SMTDSettings.Comment +"]")
		)

		fn createCommentMenu =
		(
			global SMTD_CommentRCMenu
			txt = "rcmenu SMTD_CommentRCMenu\n(\n"
			txt += "menuitem mnu_jobcommentclear \"CLEAR Comment\"\n"
			txt += "on mnu_jobcommentclear picked do (SMTD_MainRollout.SetCommentTo \"\" reset:true)\n"

			txt += "menuitem mnu_jobcommentdefault \"RESET to $default\"\n"
			txt += "on mnu_jobcommentdefault picked do (SMTD_MainRollout.SetCommentTo \"$default\" reset:true )\n"

			local commentsFilename = SMTDPaths.SettingsDir + "\\SubmitMaxToDeadline_CommentFormats.ini"
			if not doesFileExist commentsFilename then
				commentsFilename = SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_CommentFormats.ini"

			if doesFileExist commentsFilename then
			(
				local commentsFile = openFile commentsFilename
				if (commentsFile != undefined) then
				(
					try
					(
						local count = 0
						while not eof commentsFile do
						(
							local fileLine = readLine commentsFile
							local fs = filterString fileLine "="
							if fs.count > 1 and findString ::SMTDSettings.Comment fs[1] == undefined do
							(
								txt += "menuitem mnu_comment" + (count as string) + " \" +" + fs[1] + "\"\n"
								txt += "on mnu_comment" + (count as string) + " picked do (SMTD_MainRollout.SetCommentTo (\"" + fs[1] + "\" ))\n"
								count += 1
							)
						)
					)
					catch ()
					try(close commentsFile)catch()
				)
			)

			txt += ")\n"
			execute txt
		)

		on btn_getComment pressed do
		(
			createCommentMenu()
			popUpMenu SMTD_CommentRCMenu pos:mouse.screenPos
		)

		button btn_pools_help "Pool: " align:#left across:4 width:65 height:20  offset:[-10,0] border:false tooltip:"The POOL lets you group Jobs together, typically on per-Project basis. It also controls the Job Priority -- the order in which a Slave is assigned to Pools matters!\n\nOnly Slaves assigned to the selected Pool will be allowed to pick up the job.\n\nIf 'none' is specified as Pool, any Slave can render it if it has no other jobs in assigned Pools to work on."
		dropdownList ddl_poollist "" width:172 align:#right offset:[-8,-2] tooltip:"The POOL lets you group Jobs together, typically on per-Project basis. It also controls the Job Priority -- the order in which a Slave is assigned to Pools matters!\n\nOnly Slaves assigned to the selected Pool will be allowed to pick up the job.\n\nIf 'none' is specified as Pool, any Slave can render it if it has no other jobs in assigned Pools to work on."

		button btn_pools2_help "Secondary: " align:#left width:65 height:20  offset:[-4,-2] border:false tooltip:"The SECONDARY POOL lets you specify a Pool to use if the primary Pool does not have any available Slaves.\n\nTo DISABLE this feature, ensure you select the EMPTY entry at the top of the list!"
		dropdownList ddl_pool2list "" width:175 align:#right offset:[1,-2] tooltip:"The SECONDARY POOL lets you specify a Pool to use if the primary Pool does not have any available Slaves.\n\nTo DISABLE this feature, ensure you select the EMPTY entry at the top of the list!"


		button btn_group_help "Group: " align:#left across:2 width:65 height:20 offset:[-10,-3] border:false tooltip:"The GROUP lets you limit the job to only specific machines, typically based on hardware or installed software characteristics.\n\nSelect the 'none' Group to turn off Group filtering."
		dropdownlist ddl_group items:#() align:#right width:417 offset:[-1,-4] height:20 tooltip:"The GROUP lets you limit the job to only specific machines, typically based on hardware or installed software characteristics.\n\nSelect the 'none' Group to turn off Group filtering."

		button btn_priority_help "Priority: " align:#left across:3 width:65 height:18 offset:[-10,-3] border:false tooltip:"Left-click slider to set value.\nHold and drag to adjust.\n\nHold CTRL and roll mouse over without left-clicking.\n\nHold SHIFT and roll mouse over to snap by 10."
		progressbar sld_priority width:368 height:18 range:[0,100,50] type:#integer align:#center offset:[3,-2]
		spinner spn_priority "" type:#integer fieldwidth:38 align:#right  offset:[-1,-1] range:[0,100,50]


		dotNetControl dn_tabs "System.Windows.Forms.TabControl" height:20 width:500 align:#center offset:[0,-4]
		subRollout sub_SubRollout width:500 height:440 align:#center offset:[0,-3]

		dropdownlist ddl_presetName items:#() width:300 align:#left across:2
		button btn_loadPreset "Load Preset" width:186 align:#right

		button btn_help_SanityCheck "?" width:20 across:3 align:#left offset:[-5,-40] tooltip:"Click for Online Help on Sanity Check."
		checkbox chk_performSanityCheck "Run Sanity Check Automatically Before Submission" align:#left checked:false offset:[-112,-39]
		button btn_runSanityCheck "Run Sanity Check Now!" align:#right width:186 offset:[0,-43] tooltip:"Run Sanity Check WITHOUT submitting the scene to Deadline."

		--button btn_renderdialog "Render Dialog..." width:100 height:29 offset:[-7,-5] align:#left across:4 tooltip:"Toggle the 3ds Max Render Scene Dialog..."
		--button btn_openMonitor "Monitor..." width:80 height:29 offset:[-3,-5] align:#center tooltip:"Launch Deadline Monitor..."
		button btn_pipelineTools "Pipeline Tools..." width:100 height:20 offset:[2,-5] align:#center tooltip:"Open the Pipeline Tools Dialog..."
		label lbl_pipelineTools "No Pipeline Tools Set" width:200 height:20 offset:[-2,0] align:#center
		checkbutton chk_submit "SUBMIT" width:186 height:25 offset:[7,-4] align:#right tooltip:"Submit the current 3ds Max scene to Deadline." highlightColor:(color 200 0 0)
		imgTag tag_submitTop height:2 width:186
		imgTag tag_submitBottom height:2 width:186

		dotNetControl dnc_report "ListView" width:500 height:105 align:#center offset:[0,-40]

		button btn_LogWindowOptions "Log: ALL" align:#left height:18 width:100 across:4 \
			tooltip:"Opens the Log Options menu.\n\nIt is also available via Right-Click in the Log window itself.\n\nDouble-click a line in the Log window to toggle the Filter between its Message Type, and ALL Types."
		edittext edt_LogFilterPattern text:"Search Logs..." fieldwidth:202 align:#center tooltip:"Search Log Messages"
		--label lbl_lastSubmissionState "Last Submission:" offset:[100,-6] align:#center
		progressbar sld_lastSubmissionState width:186 height:16 color:blue align:#right value:100 offset:[8,-7]

		fn setSubmitButtonWarning message =
		(
			tag_submitTop.bitmap = tag_submitBottom.bitmap = bitmap 1 1 color:red
			chk_submit.tooltip = message
			false
		)

		fn updateSubmitButtonState =
		(
			renderSceneDialog.commit()
			tag_submitTop.bitmap = tag_submitBottom.bitmap = bitmap 1 1 color:green
			local canSubmit = true

			if ddl_workflow.selection == 1 then	--if the default workflow is selected,
			(
				chk_submit.tooltip = "Submit the current 3ds Max scene to Deadline."

				if SMTDSettings.SubmitSceneMode == #globalnetworksave and not doesFileExist SMTDSettings.SubmitSceneGlobalBasePath do
					canSubmit = setSubmitButtonWarning "CANNOT SUBMIT the current 3ds Max scene to Deadline because the GLOBAL NETWORK PATH is not valid!"

				if SMTDSettings.SubmitSceneMode == #networksave and not doesFileExist SMTDSettings.SubmitSceneBasePath do
					canSubmit = setSubmitButtonWarning "CANNOT SUBMIT the current 3ds Max scene to Deadline because the USER-DEFINED NETWORK PATH is not valid!"

				if SMTDFunctions.getRendererIdString() == "vray" AND SMTDSettings.RegionRenderingMode != #none AND (for o in (getClassInstances VRayStereoscopic) where o.enabled == true AND o.view == 0 collect o).count > 0 do
					canSubmit = setSubmitButtonWarning "CANNOT SUBMIT:\nActive VRayStereoscopic Helper set to 'Both' found, and Region Rendering requested at the same time!\n\nEither disable the VRayStereoscopic Helper,\nswitch it to 'Left' or 'Right' view mode,\nor switch the 'Tiles & Region Rendering Options' of SMTD to FULL FRAME mode!"

				local tasksToSubmit = ceil(1.0 * (SMTDFunctions.GetFrameSequenceArray()).count / SMTDSettings.ChunkSize) as integer
				if tasksToSubmit > SMTDSettings.TaskLimit do
					canSubmit = setSubmitButtonWarning ("CANNOT SUBMIT:\nThe number of Tasks (" + tasksToSubmit as string + ") is higher than the current Repository's Task Limit ("+SMTDSettings.TaskLimit as string+").\n\nEither increase the Task Chunk Size,\nreduce the number of Frames to render, or\nincrease the Repository's Task Limit.")
			)
			else		--if not the default workflow,
			(
				local theTooltip = try(SMTD_WorkflowsArray[ddl_workflow.selection].Description)catch("")
				result = try(SMTD_WorkflowsArray[ddl_workflow.selection].CanSubmit())catch(#(true,theTooltip)) 				--call the canSubmit() function if available to ensure the submission can be peformed. default to true if the function is not implemented
				if not result[1] then																				--if the function said no, report on the tooltip of the Submit button
					canSubmit = setSubmitButtonWarning ("CANNOT SUBMIT:\n"+result[2])
				else
					try(chk_submit.tooltip = result[2])catch()		--otherwise display the Description of the workflow
			)
			canSubmit	--return true or false
		)

		fn updateWorkflowMode =
		(
			local itm  = findItem WorkflowNames SMTDSettings.WorkflowMode
			if itm  == 0 do itm  = 1
			ddl_workflow.selection = itm
			SMTD_RolloutsLayout = try(SMTD_WorkflowsArray[itm].defineUILayout())catch(SMTD_LegacyRolloutsLayout)	--get the layout array, or revert to the legacy full layout if function missing
			try(SMTD_WorkflowsArray[itm].restoreSettings())catch()													--try to restore any struct settings that might have been stored with the scene or on disk
			try(ddl_workflow.tooltip = SMTD_WorkflowsArray[itm].Description)catch()									--set the tooltip of the dropdownlist to the description
			try(chk_submit.tooltip = SMTD_WorkflowsArray[itm].Description)catch()									--set the Submit button's tooltip to the description

			dn_tabs.enabled = false
			for subroll in sub_SubRollout.Rollouts do
				removeSubRollout sub_SubRollout subroll
			dn_tabs.TabPages.Clear()
			for aTab in SMTD_RolloutsLayout do
			(
				dn_tabs.TabPages.add aTab[1][1]
				--local theItem = SMTD_MainRollout.dn_tabs.TabPages.Item[SMTD_MainRollout.dn_tabs.TabPages.count-1]
				--theItem.ToolTipText = aTab[1][2]
			)
			for subroll in SMTD_RolloutsLayout[LastSubRollout = 1][2] do
			(
				addSubRollout sub_SubRollout subroll[1]
				subroll[1].open = subroll[2]
			)
			try(SMTD_WorkflowsArray[itm].updateUILayout())catch()													--call the optional function to update visibility of existing controls
			updateSubmitButtonState()																				--make sure the button is updated
			dn_tabs.enabled = true
		)

		fn loadWorkflows =
		(
			local theWorkflowFiles = getFiles (SMTDPaths.MainSubmissionDir+"\\Workflows\\SMTDWorkflow_*.ms")
			SMTD_WorkflowsArray = #(SMTD_LegacyWorkflowStruct())
			local workflowTitles = #(SMTD_WorkflowsArray[1].WorkflowTitle)
			WorkflowNames = #("default")
			for aFile in theWorkflowFiles do
			(
				local result = try(fileIn aFile)catch(undefined)
				if result != undefined then
				(
					if try(result.isWorkflowActive())catch(false) do --make sure the workflow struct is valid, and enabled
					(
						append SMTD_WorkflowsArray result																--append the struct instance to the array
						append workflowTitles (try(result.WorkflowTitle)catch(getFileNameFile aFile)) 					--get the workflow name, or use the file name if the property is missing
						append workflowNames (try(result.WorkflowName)catch(getFileNameFile aFile))
					)
				)
				else
					SMTD_MainRollout.Ui_report ("--FAILED to load Workflow ["+getFileNameFile aFile+"].")
			)
			if loadDefaultWorkflow == false and SMTD_WorkflowsArray.count > 1 do --if no default workflow was requested, and there were valid alternative workflows in the folder, delete the default entry 1
			(
				deleteItem SMTD_WorkflowsArray 1
				deleteItem workflowTitles 1
				deleteItem workflowNames 1
			)

			ddl_workflow.items = workflowTitles
			local theIndex = findItem WorkflowNames SMTDSettings.WorkflowMode
			if theIndex == 0 do theIndex = 1
			ddl_workflow.selection = theIndex
			try(ddl_workflow.tooltip  = SMTD_WorkflowsArray[theIndex].Description)catch()
			updateSubmitButtonState()
		)

		on ddl_workflow selected itm do
		(
			setIniSetting SMTDPaths.InIFile "Workflows" "WorkflowMode" (SMTDSettingsDefaults.WorkflowMode = SMTDSettings.WorkflowMode = WorkflowNames[itm])
			updateWorkflowMode()
			SMTD_MainRollout.Ui_report ("+Switched Workflow to ["+ddl_workflow.selected+"]")							--report the switch to the log
			::SMTDFunctions.storeSettingsWithScene()
		)
		on dn_tabs Selected itm do
		(
			if itm.TabPageIndex >= 0 do
			(
				updateSubmitButtonState()
				if LastSubRollout != (itm.TabPageIndex+1) do 															--do not update if the same tab clicked twice
				(
					dn_tabs.enabled = false
					for subroll in sub_SubRollout.Rollouts do
						removeSubRollout sub_SubRollout subroll
					for subroll in SMTD_RolloutsLayout[LastSubRollout = itm.TabPageIndex+1][2] do
					(
						addSubRollout sub_SubRollout subroll[1]
						subroll[1].open = subroll[2]
					)
					SMTD_WorkflowsArray[ddl_workflow.selection].updateUILayout()
					dn_tabs.enabled = true
				)
			)
		)--end tabs clicked

		on btn_help_SanityCheck pressed do ShellLaunch (SMTD_HelpURL + "#sanity-check") ""

		fn initReportWindow lv =
		(
			local layout_def = #(#("",60), #("",400))
			lv.Clear()
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r SMTD_ColorPalette.maxBgColor.g SMTD_ColorPalette.maxBgColor.b
			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.gridLines = false
			lv.fullRowSelect = true
			lv.checkboxes = false
			lv.hideSelection = false
			lv.HeaderStyle = lv.HeaderStyle.None
			for i in layout_def do lv.Columns.add i[1] i[2]
		)

		fn openLogNotepad =
		(
			if doesFileExist SMTD_todaysLogFileName do shelllaunch "notepad.exe" SMTD_todaysLogFileName
		)
		fn openLogDefaultEditor =
		(
			if doesFileExist SMTD_todaysLogFileName do shelllaunch SMTD_todaysLogFileName ""
		)
		fn exploreLogFolder =
		(
			if doesFileExist SMTD_todaysLogFileName do shellLaunch "Explorer.exe" (getFileNamePath SMTD_todaysLogFileName)
		)

		on btn_LogWindowOptions pressed do popupmenu LogWindowOptions_RCMenu pos:mouse.screenpos
		on btn_LogWindowOptions rightclick do popupmenu LogWindowOptions_RCMenu pos:mouse.screenpos

		on dnc_report MouseUp arg do
		(
			if arg.Button == arg.Button.Right do
				popupmenu LogWindowOptions_RCMenu pos:mouse.screenpos
		)
		on dnc_report DoubleClick arg do
		(
			local theSel = for i = 1 to dnc_report.items.count where dnc_report.items.item[i-1].Selected collect (i-1)
			if theSel.count == 1 do
			(
				local theText = dnc_report.items.item[theSel[1]].subitems.item[1].Text
				case of
				(
					(matchPattern theText pattern:"!!*"):
					(
						if SMTD_LogFilters.count == 0 then
							::SMTD_LogFilters=#(#info,#progress,#success,#error)
						else
							::SMTD_LogFilters=#()
					)
					(matchPattern theText pattern:">*"):
					(
						if SMTD_LogFilters.count == 0 then
							::SMTD_LogFilters=#(#info,#warning,#success,#error)
						else
							::SMTD_LogFilters=#()
					)
					(matchPattern theText pattern:"--*"):
					(
						if SMTD_LogFilters.count == 0 then
							::SMTD_LogFilters=#(#info,#warning,#success,#progress)
						else
							::SMTD_LogFilters=#()
					)
					(matchPattern theText pattern:"+*"):
					(
						if SMTD_LogFilters.count == 0 then
							::SMTD_LogFilters=#(#info,#warning,#error,#progress)
						else
							::SMTD_LogFilters=#()
					)
					default: (
						if SMTD_LogFilters.count == 0 then
							::SMTD_LogFilters=#(#warning,#error,#progress,#success)
						else
							::SMTD_LogFilters=#()
					)
				)--end case
				SMTD_MainRollout.filterLog()
			)
		)

		fn job_priority_update val =
		(
			if (val > SMTDSettings.MaximumPriority) do (val = (SMTDSettings.MaximumPriority / 2))

			--if val <= SMTDSettings.MaximumPriority do
			(
				if keyboard.shiftPressed do val = ((floor(val/10.0))*10.0) as integer
				theRed = (255.0 - 255.0*val/(SMTDSettings.MaximumPriority as float))*2.0
				if theRed > 255 do theRed = 255
				theGreen = 512.0*val/(SMTDSettings.MaximumPriority as float)
				if theGreen > 255 do theGreen = 255

				spn_priority.value = val

				sld_priority.color = [theRed, theGreen, 0]
				sld_priority.value = (val * 100) / SMTDSettings.MaximumPriority
			)
			val
		)

		fn getDayString =
		(
			theFilterTime = filterString localtime " /\\-:."
			theTime = "- "
			for i = 1 to 3 do theTime += theFilterTime[i] + "-"
			theTime
		)

		fn getTimeString =
		(
			timeArray = getLocalTime()
			local hour = if timeArray[5] < 10 then (hour = "0" + (timeArray[5] as string)) else (hour = (timeArray[5] as string))
			local minute = if timeArray[6] < 10 then (minute = "0" + (timeArray[6] as string)) else (minute = (timeArray[6] as string))
			local second = if timeArray[7] < 10 then (second = "0" + (timeArray[7] as string)) else (second = (timeArray[7] as string))
			timeString = hour + ":" + minute + ":" + second
		)

		fn Ui_report txt LogFileOnly:false AddTimeStamp:true =
		(
			if not LogFileOnly do
			(
				try
				(
					local strStream = txt as StringStream
					local theRange = #()
					local blackColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
					if SMTD_ColorPalette.maxBgColor.v >= 160 then
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
						local logLevel = #info
						if lineCount == 1 do	--set the color and log level only if this is the first line of a multi-line log block
						(
							case of
							(
								default: (
									foreColor = blackColor
								)
								(matchPattern aLine pattern:"?--*"): (
									foreColor = redColor
									logLevel = #error
								)
								(matchPattern aLine pattern:"--*"): (
									foreColor = redColor
									logLevel = #error
								)
								(matchPattern aLine pattern:"?!!*"): (
									foreColor = orangeColor
									logLevel = #warning
								)
								(matchPattern aLine pattern:"!!*"): (
									foreColor = orangeColor
									logLevel = #warning
								)
								(matchPattern aLine pattern:"?+*"): (
									foreColor = greenColor
									logLevel = #success
								)
								(matchPattern aLine pattern:"+*"): (
									foreColor = greenColor
									logLevel = #success
								)
								(matchPattern aLine pattern:">*"): (
									foreColor = blueColor
									logLevel = #progress
								)
								(matchPattern aLine pattern:"==*"): (
									foreColor = blueColor
									logLevel = #progress
								)
							)
						)
						local theTimeStamp = (if AddTimeStamp then getTimeString() else "")
						append ::SMTD_LogStream #(theTimeStamp, forecolor, logLevel, aLine)
						if findItem ::SMTD_LogFilters logLevel == 0 do
						(
							local li = dotNetObject "System.Windows.Forms.ListViewItem" (if SMTD_LogShowTimestamp then theTimeStamp else "")
							li.forecolor = foreColor
							local subLi = li.SubItems.add aLine
							append theRange li
						)
					)
					dnc_report.Items.AddRange theRange
					if dnc_report.Items.Count > 0 do dnc_report.Items.Item[dnc_report.Items.Count-1].EnsureVisible()
					local autoRes = dotNetClass "System.Windows.Forms.ColumnHeaderAutoResizeStyle"
					dnc_report.AutoResizeColumns autoRes.ColumnContent
					if not SMTD_LogShowTimestamp do dnc_report.Columns.Item[0].Width = 1
					try(windows.processPostedMessages())catch()
				)catch()
			)
			if AddTimeStamp then
				try( format "[%] : %\n" (getTimeString()) txt to:SMTD_todaysLogFile)catch()
			else
				try( format "%\n" txt to:SMTD_todaysLogFile)catch()
		)

		fn filterLog =
		(
			dnc_report.items.clear()
			local theRange =#()
			for aLine in ::SMTD_LogStream do
			(
				if findItem ::SMTD_LogFilters aLine[3] == 0 and matchPattern aLine[4] pattern:("*"+edt_LogFilterPattern.text+"*") do
				(
					local li = dotNetObject "System.Windows.Forms.ListViewItem" (if SMTD_LogShowTimestamp then aLine[1] else "")
					li.forecolor = aLine[2]
					local subLi = li.SubItems.add aLine[4]
					append theRange li
				)
			)
			dnc_report.Items.AddRange theRange
			local autoRes = dotNetClass "System.Windows.Forms.ColumnHeaderAutoResizeStyle"
			dnc_report.AutoResizeColumns autoRes.ColumnContent
			if not SMTD_LogShowTimestamp do dnc_report.Columns.Item[0].Width = 1
			if theRange.count > 0 do dnc_report.Items.Item[dnc_report.Items.Count-1].EnsureVisible()

			local logButtonCaption = "Log: "
			if ::SMTD_LogFilters.count == 0 then logButtonCaption += "ALL" else
			(
				if findItem ::SMTD_LogFilters #info == 0 do logButtonCaption += "I "
				if findItem ::SMTD_LogFilters #progress == 0 do logButtonCaption += ">P "
				if findItem ::SMTD_LogFilters #success == 0 do logButtonCaption += "+S "
				if findItem ::SMTD_LogFilters #error == 0 do logButtonCaption += "--E "
				if findItem ::SMTD_LogFilters #warning == 0 do logButtonCaption += "!!W "
			)
			btn_LogWindowOptions.caption = logButtonCaption
		)

		on edt_LogFilterPattern changed txt do filterLog()

		fn copySelectedLinesFromLog =
		(
			local theString = "" as stringStream
			for i = 0 to dnc_report.Items.Count-1 do
				if dnc_report.Items.Item[i].selected do
					format "% %\n" dnc_report.Items.Item[i].SubItems.Item[0].Text dnc_report.Items.Item[i].SubItems.Item[1].Text to:theString
			setclipboardText (theString as string)
		)

		fn updateSubRollouts =
		(
			local openStates = for subroll in SMTD_RolloutsLayout[LastSubRollout][2] collect subroll[1].open
			for subroll in sub_SubRollout.rollouts do
				removeSubRollout sub_SubRollout subroll
			for i = 1 to SMTD_RolloutsLayout[LastSubRollout][2].count do
			(
				addSubRollout sub_SubRollout SMTD_RolloutsLayout[LastSubRollout][2][i][1]
				SMTD_RolloutsLayout[LastSubRollout][2][i][1].open = openStates[i]
			)
		)

		fn displayPoolsList =
		(
			ddl_poollist.items = SMTDSettings.Pools
			ddl_pool2list.items = (join #("") SMTDSettings.Pools)

			local theIndex = findItem ddl_poollist.items SMTDSettings.PoolName
			if theIndex > 0 then
				ddl_poollist.selection = theIndex
			else
			(
				theIndex = findItem ddl_poollist.items "none"
				if theIndex > 0 do
				(
					ddl_poollist.selection = theIndex
					SMTDSettings.PoolName = "none"
					::SMTDFunctions.storeSettingsWithScene()
				)
			)

			local theIndex = findItem ddl_pool2list.items SMTDSettings.Pool2Name
			if theIndex > 0 then
				ddl_pool2list.selection = theIndex
			else
			(
				ddl_pool2list.selection = 1
				SMTDSettings.Pool2Name = ""
				::SMTDFunctions.storeSettingsWithScene()
			)
		)

		fn displayGroupsList =
		(
			ddl_group.items = SMTDSettings.Groups

			local theIndex = findItem ddl_group.items SMTDSettings.Group
			if theIndex > 0 then
				ddl_group.selection = theIndex
			else
			(
				theIndex = findItem ddl_group.items "none"
				if theIndex > 0 do
				(
					ddl_group.selection = theIndex
					SMTDSettings.Group = "none"
					::SMTDFunctions.storeSettingsWithScene()
				)
			)
		)

		/*
		fn AutoSuggestCategory =
		(
			st = timestamp()
			if SMTDSettings.AutoSuggestCategory do
			(
				local theCategoryPatternsFile = (SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_CategoryPatterns.ms")
				if doesFileExist theCategoryPatternsFile do
				(
					try(fileIn theCategoryPatternsFile)catch(SMTD_CategoryPatterns=#())
					--local theFullName = (maxFilePath + maxFileName)
					local theFullName = edt_jobname.text
					for thePattern in SMTD_CategoryPatterns do
					(
						local includeThis = false
						for theIncludes in thePattern[1] do
							if matchPattern theFullName pattern:theIncludes do includeThis = true
						for theExcludes in thePattern[2] do
							if matchPattern theFullName pattern:theExcludes do includeThis = false
						if includeThis do
						(
							local theIndex = findItem ddl_category.items thePattern[3]
							if theIndex > 0 do
							(
								ddl_category.selection = theIndex
								SMTDSettings.Category = thePattern[3]
								Ui_report (">Job Name Matched a Pattern - Category Set To ["+ thePattern[3] + "]")
								if thePattern[4] >= 0 do
								(
									job_priority_update (SMTDSettings.Priority = thePattern[4])
									Ui_report (">Priority Set Automatically to ["+ thePattern[4] as string + "] by Category Pattern Matching.")
								)
								exit
							)
						)
					)
				)
			)
			et = timestamp()
			--format "Pattern matching time: %\n" (et-st)
		)
		*/

		fn getNameFromMaxScene =
		(
			local theName = getFileNameFile maxFileName
			if theName == "" do theName = "Untitled 3ds Max Job"
			SMTDSettings.jobName = edt_jobname.text = theName
			Ui_report ("+Job Name Changed To Scene Name ["+ theName +"]")
			--AutoSuggestCategory()
		)

		fn getNameFromOutputFile =
		(
			local theName = ""
			if rendOutputFilename != "" then
			(
				theName = filenameFromPath rendOutputFilename
				if theName == "" do theName = "Untitled 3ds Max Job"
			)
			SMTDSettings.jobName = edt_jobname.text = theName
			Ui_report ("+Job Name Changed To OutputFile ["+ theName +"]")
		)

		fn DateCompareFN v1 v2 valArray: =
		(
			if valArray[v1] > valArray[v2] then -1 else 1
		)

		fn sortFilesByDate theFiles=
		(
			if theFiles.count == 0 do return #()

			local theYearIndex = 3
			local theMonthIndex = 1
			local theDayIndex = 2
			theFileDates = for f in theFiles collect filterString (getFileCreateDate f) " /\\:.;_"
			indexArray = for i = 1 to theFileDates.count collect i
			for f = 1 to theFileDates.count do for i = 1 to theFileDates[f].count do if theFileDates[f][i].count == 1 do theFileDates[f][i] = "0" + theFileDates[f][i]
			for f = 1 to theFileDates.count where try(matchPattern theFileDates[f][7] pattern:"PM")catch(false) do theFileDates[f][4] = (execute theFileDates[f][4] + 12) as string
			theFileDates = for f in theFileDates collect f[theYearIndex]+f[theMonthIndex]+f[theDayIndex]+f[4]+f[5]+f[6]
			qsort indexArray DateCompareFN valArray:theFileDates
			for i in indexArray collect theFiles[i]
		)

		fn loadSaveDialogOpen =
		(
			case SMTD_PresetDialogMode of
			(
				#load:
				(
					SMTD_PresetDialog.title = "SMTD: LOAD Render Preset"
					SMTD_PresetDialog.btn_loadsave.caption = "LOAD PRESET..."
					SMTD_PresetDialog.lbl_edittext.text = "Filter Pattern:"
					theFiles = getFiles (SMTDPaths.SettingsDir + "\\presets\\"+ SMTD_MainRollout.PresetFilterString +"*.SMTDPreset")
					if theFiles.count == 0 then
					(
						SMTD_PresetDialog.btn_loadsave.enabled = false
						SMTD_PresetDialog.ddl_presetsToLoad.items = #()
					)
					else
					(
						theFiles = sortFilesByDate theFiles
						SMTD_PresetDialog.ddl_presetsToLoad.items = for f in theFiles collect getFileNameFile f
						SMTD_PresetDialog.ddl_presetsToLoad.selection = 1
						SMTD_MainRollout.presetToLoadDDLSelected SMTD_PresetDialog.ddl_presetsToLoad.selection
						SMTD_PresetIniFile = (SMTDPaths.SettingsDir + "\\presets\\" + SMTD_PresetDialog.ddl_presetsToLoad.selected + ".SMTDPreset")
					)
				)
				#loadscene:
				(
					SMTD_PresetDialog.title = "SMTD: LOAD Scene Settings"
					SMTD_PresetDialog.btn_loadsave.caption = "LOAD SETTINGS..."
					SMTD_PresetDialog.lbl_edittext.text = ""
					SMTD_PresetDialog.ddl_presetsToLoad.items = #()
					SMTD_PresetDialog.edt_presetsToSave.enabled = SMTD_PresetDialog.ddl_presetsToLoad.enabled = false
					SMTD_PresetIniFile = ""
				)
				#save:
				(
					theFiles = getFiles (SMTDPaths.SettingsDir + "\\presets\\*.SMTDPreset")
					theFiles = sortFilesByDate theFiles
					SMTD_PresetDialog.ddl_presetsToLoad.items = for f in theFiles collect getFileNameFile f

					SMTD_PresetDialog.title = "SMTD: SAVE Render Preset"
					SMTD_PresetDialog.btn_loadsave.caption = "SAVE PRESET..."
					SMTD_PresetDialog.lbl_edittext.text = "Preset Name:"
					local thePresetFileName = if maxFileName != "" then (getFileNameFile maxFileName) else "Preset"
					SMTD_PresetDialog.edt_presetsToSave.text = thePresetFileName
					SMTD_PresetIniFile = (SMTDPaths.SettingsDir + "\\presets\\" + SMTD_PresetDialog.edt_presetsToSave.text + ".SMTDPreset")
				)
			)
		)

		fn presetToLoadDDLSelected itm =
		(
			if itm > 0 then
			(
				if SMTD_PresetDialogMode == #load do
					SMTD_PresetIniFile = (SMTDPaths.SettingsDir + "\\presets\\" + SMTD_PresetDialog.ddl_presetsToLoad.selected + ".SMTDPreset")

				if doesFileExist SMTD_PresetIniFile then
				(
					SMTD_PresetDialog.btn_loadsave.enabled = true
					--FranticParticleRenderMXS.initTreeView SMTD_PresetDialog.dn_tv
				)
				else
				(
					SMTD_PresetDialog.btn_loadsave.enabled = false
				)
			)
			else
			(
				SMTD_PresetIniFile = ""
				SMTD_PresetDialog.btn_loadsave.enabled = false
			)
			SMTD_MainRollout.initTreeView SMTD_PresetDialog.dn_tv
			SMTD_MainRollout.fillInTreeView SMTD_PresetDialog.dn_tv
		)

		fn loadSaveButtonPressed =
		(
			local st = timestamp()
			makeDir (getFilenamePath SMTD_PresetIniFile) all:true
			if SMTD_PresetDialogMode == #save do
			(
				deleteFile SMTD_PresetIniFile
				local theRoot = SMTD_PresetDialog.dn_tv.Nodes.Item[0]
				for catIndex = 1 to SMTD_PresetTreeData[1].count do
				(
					if theRoot.Nodes.Item[catIndex-1].Checked do
					(
						for valueIndex = 1 to SMTD_PresetTreeData[2][catIndex].count do
						(
							if theRoot.Nodes.Item[catIndex-1].Nodes.Item[valueIndex-1].Checked do
							(
								local theValue = try(getProperty SMTDSettings SMTD_PresetTreeData[2][catIndex][valueIndex][3])catch(undefined)
								if theValue != undefined do
									setIniSetting SMTD_PresetIniFile SMTD_PresetTreeData[2][catIndex][valueIndex][1] SMTD_PresetTreeData[2][catIndex][valueIndex][2] (theValue as string)
							)--end if
						)--end valueIndex loop
					)--end if
				)--end catIndex loop
			)--end save

			if SMTD_PresetDialogMode == #load do
			(
				local theRoot = SMTD_PresetDialog.dn_tv.Nodes.Item[0]
				for catIndex = 1 to SMTD_PresetTreeData[1].count do
				(
					if theRoot.Nodes.Item[catIndex-1].Checked do
					(
						for valueIndex = 1 to SMTD_PresetTreeData[2][catIndex].count do
						(
							if theRoot.Nodes.Item[catIndex-1].Nodes.Item[valueIndex-1].Checked do
							(
								local theValue = getIniSetting SMTD_PresetIniFile SMTD_PresetTreeData[2][catIndex][valueIndex][1] SMTD_PresetTreeData[2][catIndex][valueIndex][2]
								if SMTD_PresetTreeData[2][catIndex][valueIndex][4] == true then
									theValue = execute theValue
								else if SMTD_PresetTreeData[2][catIndex][valueIndex][9] == true do
									if theValue != "" then theValue = theValue as name else theValue = #none
								setProperty SMTDSettings SMTD_PresetTreeData[2][catIndex][valueIndex][3] theValue
							)--end if
						)--end valueIndex loop
					)--end if
				)--end catIndex loop
				SMTD_MainRollout.updateControls()
				SMTD_MainRollout.updateSubRollouts()
			)--end if load

			if SMTD_PresetDialogMode == #loadscene do
			(
				local theTempStruct = SMTDFunctions.getSettingsAsStructFromScene()
				local theRoot = SMTD_PresetDialog.dn_tv.Nodes.Item[0]
				for catIndex = 1 to SMTD_PresetTreeData[1].count do
				(
					if theRoot.Nodes.Item[catIndex-1].Checked do
					(
						for valueIndex = 1 to SMTD_PresetTreeData[2][catIndex].count do
						(
							if theRoot.Nodes.Item[catIndex-1].Nodes.Item[valueIndex-1].Checked do
							(
								local theValue = try(getProperty theTempStruct SMTD_PresetTreeData[2][catIndex][valueIndex][3])catch(undefined)
								if theValue != undefined do
								(
									if SMTD_PresetTreeData[2][catIndex][valueIndex][9] == true do
										if theValue != "" then theValue = theValue as name else theValue = #none
									setProperty SMTDSettings SMTD_PresetTreeData[2][catIndex][valueIndex][3] theValue
								)--end if defined
							)--end if checked
						)--end valueIndex loop
					)--end if
				)--end catIndex loop
				SMTD_MainRollout.updateControls()
				SMTD_MainRollout.updateSubRollouts()
			)
			try(destroyDialog SMTD_PresetDialog)catch()
			if SMTD_PresetDialogMode == #loadscene do
				Ui_report ("+Scene Settings Loaded In " + ((timestamp()-st)/1000.0) as string + " sec.")
			if SMTD_PresetDialogMode == #load do
				Ui_report ("+Preset Loaded In " + ((timestamp()-st)/1000.0) as string + " sec.")
			if SMTD_PresetDialogMode == #save do
				Ui_report ("+Preset Saved In " + ((timestamp()-st)/1000.0) as string + " sec.")
		)--end fn

		fn initTreeView tv =
		(
			tv.nodes.Clear()
			tv.checkboxes = true
			tv.HideSelection = false
		)

		fn fillInTreeView tv =
		(
			local st = timestamp()
			theRoot = tv.nodes.add ""

			tv.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			tv.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r SMTD_ColorPalette.maxBgColor.g SMTD_ColorPalette.maxBgColor.b

			case SMTD_PresetDialogMode of
			(
				#save:
				(
					SMTD_PresetDialog.title = "SMTD: SAVE Preset"
					theRoot.text = "SAVE Preset"
					theRoot.forecolor = SMTD_ColorPalette.redColor
				)
				#load:
				(
					SMTD_PresetDialog.title = "SMTD: LOAD Preset"
					if SMTD_PresetDialog.ddl_presetsToLoad.selected != undefined then
						theRoot.text = "LOAD Preset [" + SMTD_PresetDialog.ddl_presetsToLoad.selected + "]"
					else
						theRoot.text = "NO RENDER PRESETS FOUND!"
					theRoot.forecolor = SMTD_ColorPalette.greenColor
				)
				#loadscene:
				(
					SMTD_PresetDialog.title = "SMTD: LOAD Scene Settings"
					theRoot.text = "LOAD Scene Settings [" + maxFilename + "]"
					theRoot.forecolor = SMTD_ColorPalette.greenColor
				)
			)
			theRoot.checked = true

			::SMTD_PresetTreeData = SMTDFunctions.getSettingsListAsTree()
			if SMTD_PresetDialogMode == #load do
			(
				for catIndex = 1 to SMTD_PresetTreeData[1].count do
				(
					for valueIndex = SMTD_PresetTreeData[2][catIndex].count to 1 by -1 do
					(
						theKeys = getIniSetting SMTD_PresetIniFile SMTD_PresetTreeData[2][catIndex][valueIndex][1]
						if findItem theKeys SMTD_PresetTreeData[2][catIndex][valueIndex][2] == 0 do deleteItem SMTD_PresetTreeData[2][catIndex] valueIndex
					)
				)
				for catIndex = SMTD_PresetTreeData[1].count to 1 by -1 do
				(
					if SMTD_PresetTreeData[2][catIndex].count == 0 do
					(
						deleteItem SMTD_PresetTreeData[1] catIndex
						deleteItem SMTD_PresetTreeData[2] catIndex
					)
				)
			)
			if SMTD_PresetDialogMode == #loadscene do
			(
				local theTempStruct = SMTDFunctions.getSettingsAsStructFromScene()
			)
			for catIndex = 1 to SMTD_PresetTreeData[1].count do
			(
				newNode = theRoot.Nodes.add SMTD_PresetTreeData[1][catIndex]
				newNode.checked = false
				newNode.forecolor = SMTD_ColorPalette.blueColor
				for valueIndex = 1 to SMTD_PresetTreeData[2][catIndex].count do
				(
					case SMTD_PresetDialogMode of
					(
						#save:
						(
							newSubNode = newNode.Nodes.add (SMTD_PresetTreeData[2][catIndex][valueIndex][6]+" ["+ (try((getProperty ::SMTDSettings SMTD_PresetTreeData[2][catIndex][valueIndex][3]) as string )catch("--")) +"]")
							newSubNode.checked = not (SMTD_PresetTreeData[2][catIndex][valueIndex][7] == false AND SMTD_PresetTreeData[2][catIndex][valueIndex][8] == false)
							newNode.checked = true
							newSubNode.forecolor = SMTD_ColorPalette.redColor
						)
						#load:
						(
							local fileValue = getIniSetting SMTD_PresetIniFile SMTD_PresetTreeData[2][catIndex][valueIndex][1] SMTD_PresetTreeData[2][catIndex][valueIndex][2]
							local structValue = (try((getProperty ::SMTDSettings SMTD_PresetTreeData[2][catIndex][valueIndex][3]) as string )catch("--"))
							local textToDisplay = SMTD_PresetTreeData[2][catIndex][valueIndex][6] + " ["+ structValue +"]"
							newSubNode = newNode.Nodes.add ""
							if fileValue != structValue then
							(
								textToDisplay+=" -> ["+ fileValue +"]"
								newSubNode.checked = true
								newNode.checked = true
								newSubNode.forecolor = SMTD_ColorPalette.greenColor
								newNode.expand()
							)
							else
							(
								newSubNode.checked = false
								newSubNode.forecolor = SMTD_ColorPalette.grayColor
							)
							newSubNode.text = textToDisplay
						)
						#loadscene:
						(
							local theSceneValue = (try((getProperty theTempStruct SMTD_PresetTreeData[2][catIndex][valueIndex][3]) as string )catch("--"))
							local structValue = (try((getProperty ::SMTDSettings SMTD_PresetTreeData[2][catIndex][valueIndex][3]) as string )catch("--"))
							local textToDisplay = SMTD_PresetTreeData[2][catIndex][valueIndex][6] + " ["+ structValue +"]"
							newSubNode = newNode.Nodes.add ""
							if theSceneValue != structValue then
							(
								textToDisplay+=" -> ["+ theSceneValue +"]"
								newSubNode.checked = true
								newNode.checked = true
								newSubNode.forecolor = SMTD_ColorPalette.greenColor
								newNode.expand()
							)
							else
							(
								newSubNode.checked = false
								newSubNode.forecolor = SMTD_ColorPalette.grayColor
							)
							newSubNode.text = textToDisplay
						)
					)
				)--end valueIndex loop
			)
			theRoot.expand()
		)

		fn displayPresetDialog =
		(
			local st = timestamp()
			Ui_report (">Opening Preset Dialog...")

			try(destroyDialog SMTD_PresetDialog)catch()
			rollout SMTD_PresetDialog ""
			(
				button btn_resetAll "Reset" align:#left width:45 height:20 pos:[5,1]  tooltip:"Reset all Categories and Properties to their start-up checked states."
				button btn_allCatOn "Check All Categories" align:#center width:110 height:20 pos:[52,1] tooltip:"Checks all Categories.\nEquivalent to checking the Root checkbox.\n\nThis will NOT affect the Properties in each Category, only the top-level checkboxes, but this will skip the complete Category!\n\nTo UNCHECK all Categories, simply press [Check All Categories] and then [Invert Categories]!"
				button btn_allCatinvert "Invert Categories" align:#center width:100 height:20 pos:[164,1] tooltip:"Inverts the checked state of all Categories. \n\nThis will NOT affect the Properties in each Category, only the top-level checkboxes."
				button btn_allPropsOn "Check Properties" align:#center width:90 height:20 pos:[266,1] tooltip:"Select a Category, then press to check all Properties that belong to it, as well as the Category itself."
				button btn_allPropsInvert "Invert Properties" align:#right width:90 height:20 pos:[358,1] tooltip:"Select a Category, then press to invert the checked state of all Properties that belong to it."
				edittext edt_searchField pos:[447,2] fieldwidth:143

				dotNetControl dn_tv "TreeView" width:590 height:590 align:#center offset:[0,-3]

				button btn_cancel "Cancel" height:42 width:60 align:#left across:2 offset:[-5,-1]
				button btn_loadsave "SAVE PRESET..." height:42 width:100 align:#right offset:[5,-1]
				label lbl_edittext "Filter Pattern:" pos:[75,618]
				edittext edt_presetsToSave text:"" width:343 pos:[140,617]
				dropdownlist ddl_presetsToLoad width:410 pos:[75,636]

				on btn_resetAll pressed do
				(
					initTreeView dn_tv
					fillInTreeView dn_tv
				)
				on btn_allCatOn pressed do
				(
					dn_tv.Nodes.Item[0].checked = true
					for i = 1 to dn_tv.Nodes.Item[0].Nodes.count do
					(
						dn_tv.Nodes.Item[0].Nodes.Item[i-1].Checked = true
					)
				)
				on btn_allCatinvert pressed do
				(
					for i = 1 to dn_tv.Nodes.Item[0].Nodes.count do
					(
						dn_tv.Nodes.Item[0].Nodes.Item[i-1].Checked = not dn_tv.Nodes.Item[0].Nodes.Item[i-1].Checked
					)
				)
				on btn_allPropsOn pressed do
				(
					for i = 1 to dn_tv.Nodes.Item[0].Nodes.count where dn_tv.Nodes.Item[0].Nodes.Item[i-1].IsSelected == true do
					(
						dn_tv.Nodes.Item[0].Nodes.Item[i-1].checked = true
						for j = 1 to dn_tv.Nodes.Item[0].Nodes.Item[i-1].Nodes.count do
							dn_tv.Nodes.Item[0].Nodes.Item[i-1].Nodes.Item[j-1].Checked = true
					)
				)
				on btn_allPropsInvert pressed do
				(
					for i = 1 to dn_tv.Nodes.Item[0].Nodes.count where dn_tv.Nodes.Item[0].Nodes.Item[i-1].IsSelected == true do
					(
						for j = 1 to dn_tv.Nodes.Item[0].Nodes.Item[i-1].Nodes.count do
							dn_tv.Nodes.Item[0].Nodes.Item[i-1].Nodes.Item[j-1].Checked = not dn_tv.Nodes.Item[0].Nodes.Item[i-1].Nodes.Item[j-1].Checked
					)
				)

				on btn_cancel pressed do
				(
					try(destroyDialog SMTD_PresetDialog)catch()
				)

				on btn_loadsave pressed do
				(
					if edt_presetsToSave.text != "" or findItem #(#loadscene, #load) SMTD_PresetDialogMode > 0 do
						SMTD_MainRollout.loadSaveButtonPressed()
				)

				on dn_tv AfterCheck arg do
				(
					if arg.Node.parent == undefined then
					(
						for i = 1 to dn_tv.Nodes.Item[0].Nodes.count do
							dn_tv.Nodes.Item[0].Nodes.Item[i-1].Checked = arg.Node.Checked
					)
					else
					(
						if arg.Node.parent != dn_tv.Nodes.Item[0] do
						(
							local theParent = arg.Node.parent
							local isChecked = 0
							for i = 1 to theParent.Nodes.count do
							(
								if theParent.Nodes.Item[i-1].Checked then
								(
									if SMTD_PresetDialogMode == #save do theParent.Nodes.Item[i-1].forecolor = SMTD_ColorPalette.redColor
									isChecked+=1
								)
								else
									if SMTD_PresetDialogMode == #save do theParent.Nodes.Item[i-1].forecolor = SMTD_ColorPalette.grayColor
							)
							theParent.forecolor = case of
							(
								(isChecked == 0): SMTD_ColorPalette.lightGrayColor
								default: SMTD_ColorPalette.lightBlueColor
								(isChecked == theParent.Nodes.count): SMTD_ColorPalette.blueColor
							)
						)
					)
				)

				on edt_searchField changed txt do
				(
					for i = 1 to dn_tv.Nodes.Item[0].Nodes.count do
					(
						local expandedNode = false
						for j = 1 to dn_tv.Nodes.Item[0].Nodes.Item[i-1].Nodes.count do
						(
							if txt != "" and matchPattern dn_tv.Nodes.Item[0].Nodes.Item[i-1].Nodes.Item[j-1].Text pattern:("*"+txt+"*") then
							(
								dn_tv.Nodes.Item[0].Nodes.Item[i-1].Nodes.Item[j-1].backcolor = SMTD_ColorPalette.highlightBgColor
								expandedNode = true
							)
							else
								dn_tv.Nodes.Item[0].Nodes.Item[i-1].Nodes.Item[j-1].backcolor = bgColor
						)
						if expandedNode then
						(
							dn_tv.Nodes.Item[0].Nodes.Item[i-1].expand()
						)
						else
						(
							dn_tv.Nodes.Item[0].Nodes.Item[i-1].collapse()
						)
					)
				)

				on edt_presetsToSave entered txt do
				(
					if SMTD_PresetDialogMode == #save do
					(
						SMTD_PresetIniFile = ( SMTDPaths.SettingsDir + "\\presets\\" + txt + ".SMTDPreset")
					)
				)

				on edt_presetsToSave changed txt do
				(
					if SMTD_PresetDialogMode != #save then
					(
						SMTD_MainRollout.PresetFilterString = txt
						SMTD_MainRollout.loadSaveDialogOpen()
						SMTD_MainRollout.presetToLoadDDLSelected ddl_presetsToLoad.selection
					)
					else btn_loadsave.enabled = txt.count > 0
				)

				on ddl_presetsToLoad selected itm do
				(
					if SMTD_PresetDialogMode == #save then
						edt_presetsToSave.entered (edt_presetsToSave.text = ddl_presetsToLoad.selected)
					else
						SMTD_MainRollout.presetToLoadDDLSelected itm
				)

				on SMTD_PresetDialog open do
				(
					if SMTD_PresetDialogMode != #save do edt_presetsToSave.text = SMTD_MainRollout.PresetFilterString
					SMTD_MainRollout.loadSaveDialogOpen()
					initTreeView dn_tv
					fillInTreeView dn_tv
				)
			)
			createDialog SMTD_PresetDialog 600 660 --modal:true
			Ui_report ("+Preset Dialog Created In " + ((timestamp()-st)/1000.0) as string + " sec.")
		)

		on edt_jobname entered txt do
		(
			--SMTDSettings.jobName = txt
			setIniSetting SMTDPaths.InIFile "JobSettings"  "jobName"  (SMTDSettings.jobName = txt)
			Ui_report ("+Job Name Changed To ["+ txt +"]")
			--AutoSuggestCategory()
		)

		--on edt_jobname changed txt do AutoSuggestCategory()

		on edt_comment entered txt do
		(
			SMTDSettings.comment = txt
			Ui_report ("+Comment Changed To ["+ txt +"]")
		)

		on edt_user entered txt do
		(
			SMTDSettings.UserName = txt
			Ui_report ("+UserName Changed To ["+ txt +"]")
		)
		on edt_dept entered txt do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "Department"  (SMTDSettings.Department = txt)
			Ui_report ("+Department Changed To ["+txt +"]")
		)

		on ddl_group selected itm do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "Group" ( (SMTDSettings.Group = ddl_group.selected) as string )
			Ui_report ("+Group Changed To ["+SMTDSettings.Group+"]")
			displayGroupsList()
		)

		on spn_priority changed value do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "Priority" ( (SMTDSettings.Priority= (job_priority_update value)) as string )
			Ui_report ("+Priority Spinner changed to ["+value as string+"]") LogFileOnly:true
		)

		on sld_priority clicked value do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "Priority" ( (SMTDSettings.Priority= (job_priority_update ((value * SMTDSettings.MaximumPriority) / 100))) as string )
			Ui_report ("+Priority Slider changed to ["+value as string+"]") LogFileOnly:true
		)

		on ddl_poollist selected itm do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "PoolName" ( (SMTDSettings.PoolName = ddl_poollist.selected) as string )
			Ui_report ("+Pool changed to ["+SMTDSettings.PoolName+"]")
			displayPoolsList()
		)

		on ddl_pool2list selected itm do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "Pool2Name" ( (SMTDSettings.Pool2Name = ddl_pool2list.selected) as string )
			if SMTDSettings.Pool2Name == "" then
				Ui_report ("+Secondary Pool DISABLED.")
			else
				Ui_report ("+Secondary Pool changed to ["+SMTDSettings.Pool2Name+"]")
			displayPoolsList()
		)

		on chk_performSanityCheck changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "PerformSanityCheck" ( (SMTDSettings.PerformSanityCheck= state) as string)
			SMTD_MainRollout.Ui_report ("+Run Sanity Check Automatically Before Submission set to [" + state as string + "].")
		)

		on btn_runSanityCheck pressed do
		(
			SMTD_MainRollout.Ui_report (">Performing SANITY CHECK...")
			local st = timestamp()
			local result = SMTD_PerformSanityCheck()
			SMTD_MainRollout.Ui_report (">Sanity Check took " + ((timestamp()-st)/1000.0) as string + " sec." )
			if result then
				SMTD_MainRollout.Ui_report (">+The Scene PASSED the Sanity Check.")
			else
				SMTD_MainRollout.Ui_report (">--The Scene DID NOT PASS the Sanity Check!")
		)

		on btn_pipelineTools pressed do
		(
			if maxFileName == "" then
				messageBox "You must first save your scene"
			else
			(
				SMTDFunctions.openPipelineToolsWindow()
				lbl_pipelineTools.text = SMTDSettings.PipelineToolStatus
			)
		)

		on btn_renderdialog pressed do
		(
			if renderSceneDialog.isOpen() then
			(
				Ui_report ">Closing Render Scene Dialog"
				renderSceneDialog.close()
			)
			else
			(
				Ui_report ">Opening Render Scene Dialog"
				renderSceneDialog.open()
			)
		)

		on btn_openMonitor pressed do
		(
			Ui_report ">Launching External Application: DeadlineMonitor"
			shellLaunch (SMTDPaths.BinDir + "DeadlineMonitor.exe") ""
		)

		fn reportSubmissionSettings =
		(
			Ui_report ("File Path: ["+maxFilePath + "]")
			Ui_report("File Name: ["+maxFileName + "]" )
			local txt = ">SCENE INFO:\n"
			try(txt += ("\t\tScene Nodes: "+objects.count as string + "\n") )catch()
			try(txt += ("\t\t\tGeometry: "+geometry.count as string + "\n") )catch()
			try(txt += ("\t\t\tShapes: "+shapes.count as string + "\n") )catch()
			try(txt += ("\t\t\tLights: "+lights.count as string  + "\n") )catch()
			try(txt += ("\t\t\tCameras: "+cameras.count as string + "\n") )catch()
			try(txt += ("\t\t\tHelpers: "+helpers.count as string  + "\n") )catch()
			try(txt += ("\t\t\tSpaceWarps: "+spacewarps.count as string + "\n" ) )catch()
			Ui_report  txt logFileOnly:true

			local theCam = viewport.getCamera()
			if isValidNode theCam then
				Ui_report ("Current View: ["+ theCam.name + "]" )
			else
				Ui_report ("Current View: Not A Camera" )

			--if(SMTDSettings.IsBakeJob) then
			--(
			--    SMTDSettings.SubmitAsMXSJob = true
			--    SMTDSettings.MAXScriptFile = SMTDPaths.MainSubmissionDir + "\\TextureBake.ms"
			--)

			local txt = ">SUBMISSION SETTINGS:\n"
			theProps = getPropNames SMTDSettings
			for p in theProps do
				txt += ( "\t\t" + (p as string) + " = " + (getProperty SMTDSettings p) as string + "\n")
			Ui_report txt logFileOnly:true
		)

		fn unregisterSMTDCallbacks =
		(
			callbacks.removeScripts id:#SubmitMaxToDeadlineSettings
		)
		fn registerSMTDCallbacks =
		(
			callbacks.addScript #filePreSave "::SMTD_MainRollout.jobNameUpdate(); ::SMTDFunctions.storeSettingsWithScene()" id:#SubmitMaxToDeadlineSettings
			callbacks.addScript #systemPostNew "::SMTDSettings = copy ::SMTDSettingsFactory; ::SMTDFunctions.loadSettings(); ::SMTD_MainRollout.updateAllControls(); ::SMTD_MainRollout.jobNameUpdate()" id:#SubmitMaxToDeadlineSettings
			callbacks.addScript #systemPostReset "::SMTDSettings = copy ::SMTDSettingsFactory; ::SMTDFunctions.loadSettings(); ::SMTD_MainRollout.updateAllControls(); ::SMTD_MainRollout.jobNameUpdate()" id:#SubmitMaxToDeadlineSettings
			callbacks.addScript #filePostOpen "::SMTDFunctions.restoreSettingstFromScene(); SMTD_MainRollout.updateAllControls(); SMTD_MainRollout.updateWorkflowMode(); ::SMTD_MainRollout.jobNameUpdate()" id:#SubmitMaxToDeadlineSettings
		)

		on chk_submit changed state do
		(
			if not updateSubmitButtonState() do
			(
				chk_submit.state = false
				Ui_report ("--"+SMTD_MainRollout.chk_submit.tooltip)
				return false
			)
			if state then
			(
				::SMTDFunctions.storeSettingsWithScene() --make sure the current settings are stored with the scene
				::SMTDIsCurrentlySubmitting = true
				chk_submit.caption = "CLICK TO CANCEL SUBMISSION..."
				SMTDSettings.SubmitSceneNetworkReuseLocation = false
				::SMTDSettings_Backup = Copy ::SMTDSettings --store last SMTD Settings
				Ui_report ">SUBMIT Button Pressed."
				local workflowResult = true																													--assume the workflow will be successful
				if ddl_workflow.selection > 1 then 																											--if a custom workflow was selected,
				(
					Ui_report (">Workflow is ["+ddl_workflow.selected+"]")																		--report which one it is
					--SMTD_WorkflowsArray[ddl_workflow.selection].SubmitJob()
					workflowResult = try(SMTD_WorkflowsArray[ddl_workflow.selection].SubmitJob(); true)catch(false)	--run the workflow's submit job function and return true, or return false if it is missing.
					if workflowResult then
					(
						sld_lastSubmissionState.color = green
						sld_lastSubmissionState.value = 100.0
					)
					else
					(
						sld_lastSubmissionState.color = red
						sld_lastSubmissionState.value = 100.0
						Ui_report ("--CANNOT SUBMIT! Calling the SubmitJob() function of the current workflow failed.\n\n" + (if getCurrentException() != undefined then getCurrentException() else ""))		--if no SubmitJob() function, complain!
					)
				)
				if ddl_workflow.selection == 1 do --if legacy workflow, or the custom workflow did not implement a SubmitJob() function...
				(
					local result = undefined
					local sanity = true
					if SMTDSettings.performSanityCheck then
					(
						Ui_report ">Performing Sanity Check..."
						sanity = SMTD_PerformSanityCheck()
						if sanity then
							Ui_report "+Sanity Check PASSED."
						else
						(
							Ui_report "--Sanity Check FAILED!"
							chk_submit.caption = "SUBMIT"
							SMTDSettings.FatalErrorsCount += 1
							chk_submit.state = false
							return false
						)
					)
					else
						Ui_report ">No Sanity Check Performed."

					if SMTDFunctions.getRendererIdString() == "vray" AND SMTDSettings.RegionRenderingMode != #none AND (for o in (getClassInstances VRayStereoscopic) where o.enabled == true AND o.view == 0 collect o).count > 0 do
					(
						Ui_report "--CANNOT SUBMIT! VRayStereoscopic Helper And Region Rendering Are Enabled!"
						Ui_report "--      Please disable VRayStereoscopic Helpers set to 'Both' mode,"
						Ui_report "--      switch from 'Both' to 'Left' or 'Right' mode,"
						Ui_report "--      or switch the SMTD 'Tile & Region Rendering Options' To FULL FRAME!"
						sanity = false
						updateSubmitButtonState()
					)

					if sanity do
					(
						SMTDSettings.nonFatalErrorsCount = 0
						SMTDSettings.FatalErrorsCount = 0
						reportSubmissionSettings()

						unregisterSMTDCallbacks()
						local theMessage = ""
						local theCameras = SMTDFUnctions.GetStereoCamerasFromCurrentView() --returns either the 3 cameras of a stereo rig, or empty array
						local batchName = ""

						if SMTDSettings.UseBatchRender == true and SMTDSettings.BatchRenderMode == 1 then
						(
							Ui_report ">Batch Submission Requested..."
							result = SMTDFunctions.spawnBatchJobsLocal() --forceMaxFile:TempMaxFile
							theMessage = "End Batch Submission."
							--theMessage = SMTDFunctions.SubmitJobFromUI()
						)
						else
						(
							if theCameras.count > 1 and SMTDSettings.StereoCameraMode != #off then
							(
								batchName = SMTDFunctions.getBatchName() + " [STEREO]"
								local theCamerasToSubmit = case SMTDSettings.StereoCameraMode of
								(
									#leftright: #(#(theCameras[1], theCameras[2]), #( SMTDSettings.LeftEyeTag, SMTDSettings.RightEyeTag) )
									#center: (if theCameras.count > 2 then #(#(theCameras[3]), #( SMTDSettings.CenterEyeTag)) else #(#(),#())) --make sure there IS a center camera
									default: #(#(theCameras[1]), #( SMTDSettings.LeftEyeTag) )
									#right: #(#(theCameras[2]), #( SMTDSettings.RightEyeTag) )
									#all: #(theCameras, #( SMTDSettings.LeftEyeTag, SMTDSettings.RightEyeTag, SMTDSettings.CenterEyeTag))
								)
								local msg = ""
								for c = 1 to theCamerasToSubmit[1].count while ::SMTDIsCurrentlySubmitting != False do
								(
									if SMTDSettings.StateSetsSubmit then
										msg += SMTDFunctions.SubmitStateSetJobs batchName:batchName stereoCameraLabel:theCamerasToSubmit[2][c] --forceCamera:theCamerasToSubmit[1][c].name  --the state sets function will have to figure out the camera based on the label
									else
										msg += SMTDFunctions.SubmitJobFromUI batchName:batchName forceCamera:theCamerasToSubmit[1][c].name stereoCameraLabel:theCamerasToSubmit[2][c]

									msg += "\n\n"
								)
								theMessage = msg
							)
							else --single view submission
							(
								theMessage = if SMTDSettings.StateSetsSubmit then
									SMTDFunctions.SubmitStateSetJobs()
								else
									SMTDFunctions.SubmitJobFromUI()
							)
						)

						registerSMTDCallbacks()

						Ui_report ("==JOB [ "+SMTDSettings.JobName+" ] SUBMISSION MESSAGE START======================================================================================")
						Ui_report theMessage
						Ui_report ("==JOB [ "+SMTDSettings.JobName+" ] SUBMISSION MESSAGE END======================================================================================")
						case of
						(
							(SMTDSettings.nonFatalErrorsCount > 1): (Ui_report("!!"+SMTDSettings.nonFatalErrorsCount as string + " Non-Fatal Errors/Warnings were issued during submission. See Log for details!"))
							(SMTDSettings.nonFatalErrorsCount == 1): (Ui_report("!!One Non-Fatal Error/Warning was issued during submission. See Log for details!"))
							default: (Ui_report "+No Non-Fatal Errors/Warnings were issued during submission.")
						)
						case of
						(
							(SMTDSettings.FatalErrorsCount > 1): (Ui_report("--"+SMTDSettings.FatalErrorsCount as string + " FATAL ERRORS were issued during submission. See Log for details!"))
							(SMTDSettings.FatalErrorsCount == 1): (Ui_report("--One FATAL ERROR was issued during submission. See Log for details!"))
							default: (Ui_report "+No Fatal Errors were issued during submission.")
						)
					)
				)--end legacy workflow
				if SMTDSettings.CloseAfterSubmission and SMTDSettings.DeadlineSubmissionSuccessful == true do
				(
					format "%\n" theMessage
					local dialogs_to_destroy = #(
						SMTD_MainRollout,
						SMTD_SanityCheck_errorReportRollout,
						SMTD_UserDefinedTilesDialog,
						SubmitMaxToDeadline_PathingExplorer,
						SubmtMaxToDeadline_SettingsBrowser,
						SubmtMaxToDeadline_SubmissionSettingsExplorer
					)

					for dialog in dialogs_to_destroy do
					(
						try(destroyDialog dialog)catch() --make sure we close all dialogs that we might have opened
					)

				)				
				::SMTDSettings = Copy SMTDSettings_Backup	--restore previous SMTD Settings
				::SMTDFunctions.storeSettingsWithScene() --make sure the current settings are stored with the scene, because saving the MAX file could have updated to intermediate values during submission!
				Ui_report ("Ready.")
				sld_lastSubmissionState.value = 100
				::SMTDIsCurrentlySubmitting = undefined
				chk_submit.caption = "SUBMIT"
				chk_submit.state = false
			)
			else
			(
				::SMTDSettings = Copy SMTDSettings_Backup --restore previous SMTD Settings
				::SMTDIsCurrentlySubmitting = false
				chk_submit.caption = "SUBMIT"
				SMTDSettings.FatalErrorsCount += 1
				Ui_report ("--Submission CANCELED By User!")
			)
		)

		fn updateControls =
		(
			spn_priority.range = [0,SMTDSettings.MaximumPriority,SMTDSettings.Priority]
			job_priority_update SMTDSettings.Priority
			displayPoolsList ()

			displayGroupsList()

			edt_jobname.text = SMTDSettings.JobName
			--AutoSuggestCategory()
			edt_comment.text = SMTDSettings.Comment

			edt_user.text = SMTDSettings.UserName

			edt_dept.text = SMTDSettings.Department
			if maxFilePath != "" AND maxFileName != "" do
				SMTD_MainRollout.Ui_report ("+Current 3ds Max Scene: " + maxFilePath + maxFileName) LogFileOnly:true

			chk_performSanityCheck.state = SMTDSettings.PerformSanityCheck

			btn_pools_help.text = SMTDFunctions.getStickyCaption "JobSettings" "Pool" "Pool: "
			btn_pools2_help.text = SMTDFunctions.getStickyCaption "JobSettings" "Secondary Pool" "Secondary: "
			btn_group_help.text = SMTDFunctions.getStickyCaption "JobSettings" "Group" "Group: "
			btn_priority_help.text = SMTDFunctions.getStickyCaption "JobSettings" "Priority" "Priority: "


			local theFiles = getFiles (SMTDPaths.SettingsDir + "\\presets\\"+ "*.SMTDPreset") --SMTD_MainRollout.PresetFilterString +
			if theFiles.count == 0 then
			(
				btn_loadPreset.enabled = false
				ddl_presetName.items = #()
			)
			else
			(
				btn_loadPreset.enabled = true
				theFiles = sortFilesByDate theFiles
				ddl_presetName.items = for f in theFiles collect getFileNameFile f
				ddl_presetNameselection = 1
			)
		)

		on btn_loadPreset pressed do
		(
			local SMTD_PresetIniFile = (SMTDPaths.SettingsDir + "\\presets\\" + ddl_presetName.selected + ".SMTDPreset")
			local theCategories = getIniSetting SMTD_PresetIniFile
			for catIndex = 1 to theCategories.count do
			(
				local theKeys = getIniSetting SMTD_PresetIniFile theCategories[catIndex]
				for valueIndex = 1 to theKeys.count do
				(
						local theValue = getIniSetting SMTD_PresetIniFile theCategories[catIndex] theKeys[valueIndex]
						try(
							case (classof (getProperty SMTDSettings (theKeys[valueIndex] as name))) of
							(
								String: ()
								default: theValue = execute theValue
								name: theValue = theValue as name
							)
							setProperty SMTDSettings (theKeys[valueIndex] as name) theValue
						)catch()
				)--end valueIndex loop
			)--end catIndex loop
			SMTD_MainRollout.updateControls()
			SMTD_MainRollout.updateSubRollouts()
		)

		fn resizeRollout val =
		(
			try(SMTD_MainRollout.width = 500)catch()

			sub_SubRollout.height = 295 + (val.y-682)

			ddl_presetName.pos = [2,val.y-200]
			btn_loadPreset.pos = [309,val.y-200]

			btn_help_SanityCheck.pos = [2,val.y-178]
			chk_performSanityCheck.pos = [25,val.y-174]
			btn_runSanityCheck.pos = [309,val.y-178]

			--btn_renderdialog.pos = [2000,val.y-154]
			lbl_pipelineTools.pos = [106,val.y-148]
			--btn_openMonitor.pos = [104,val.y-154]
			btn_pipelineTools.pos = [2,val.y-150]
			chk_submit.pos = [309,val.y-154+2]
			tag_submitTop.pos = [309,val.y-154]
			tag_submitBottom.pos = [309,val.y-154+27]

			dnc_report.pos = [0,val.y-105]
			btn_LogWindowOptions.pos = [2,val.y-125]
			edt_LogFilterPattern.pos = [104,val.y-124]
			--lbl_lastSubmissionState.pos = [380,val.y-122]
			sld_lastSubmissionState.pos = [309,val.y-122]

			setIniSetting SMTDPaths.InIFile "Dialog" "Height" (val.y as string)
		)


		on SMTD_MainRollout resized val do
		(
			if val.y < 540 do
			(
				val.y = 540
				SMTD_MainRollout.height = val.y
			)
			resizeRollout val
		)

		on SMTD_MainRollout open do
		(
			dn_tabs.enabled = false

			local purgeAllFolders = matchPattern (getIniSetting SMTDPaths.InIFile "TempFolders" "PurgeAll") pattern:"true"
			SMTDFunctions.cleanUpSubmissionFolders all:purgeAllFolders

			if SMTD_LastSubRollout == undefined do SMTD_LastSubRollout = 1
			--RPM CODE STARTS HERE:
			-- do an initial restore:
			try(
				RPMDataNet.CustomSubmitStruct.RestoreDeadline6Data (RPMdata.getListSelectionIndices RMpasses.lstbox)[1]
			)catch()

			/*
			for subroll in SMTD_RolloutsLayout[1][2] do
			(
				addSubRollout SMTD_MainRollout.sub_SubRollout subroll[1]
				subroll[1].open = subroll[2]
			)
			--SMTD_MainRollout.dn_tabs.showTooltips = true
			for aTab in SMTD_RolloutsLayout do
			(
				SMTD_MainRollout.dn_tabs.TabPages.add aTab[1][1]
				local theItem = SMTD_MainRollout.dn_tabs.TabPages.Item[SMTD_MainRollout.dn_tabs.TabPages.count-1]
				theItem.ToolTipText = aTab[1][2]
			)
			*/
			createIcons()
			if RPMDataNet != undefined and RPMDataNet.CustomSubmitStruct != undefined then
			(
				resizeRollout [500,740]
				ddl_workflow.enabled = false
				SMTDSettings.WorkflowMode = "default"
				ddl_workflow.selection = 1
			)
			else
				resizeRollout (getDialogSize SMTD_MainRollout)
			try(destroyDialog SMTD_UserDefinedTilesDialog)catch()
			makeDir SMTDPaths.LogsDir all:true
			gc light:true
			local allTodaysFiles = getFiles (SMTDPaths.LogsDir + "SubmitMaxToDeadline - ["+ sysinfo.computerName +"] " + getDayString() +"*.log")
			sort allTodaysFiles
			local lastFileNumber = 0
			if allTodaysFiles.count > 0 do
			(
				lastFileNumber = getFileNameFile allTodaysFiles[allTodaysFiles.count]
				lastFileNumber = substring lastFileNumber (lastFileNumber.count-3) 4
				lastFileNumber = (lastFileNumber as integer + 1)
			)
			SMTD_todaysLogFileName = SMTDPaths.LogsDir + "SubmitMaxToDeadline - ["+ sysinfo.computerName +"] " + getDayString() + SMTDFunctions.getZeros lastFileNumber + lastFileNumber as string+".log"
			local timeArray = getLocalTime()
			local hour = if timeArray[5] < 10 then (hour = "0" + (timeArray[5] as string)) else (hour = (timeArray[5] as string))
			local minute = if timeArray[6] < 10 then (minute = "0" + (timeArray[6] as string)) else (minute = (timeArray[6] as string))
			local second = if timeArray[7] < 10 then (second = "0" + (timeArray[7] as string)) else (second = (timeArray[7] as string))
			local timeString = (timeArray[4] as string) + "-" + (timeArray[2] as string) + "-" + (timeArray[1] as string) + " " + hour + ":" + minute + ":" + second
			if not doesFileExist SMTD_todaysLogFileName then
			(
				SMTD_todaysLogFile = createFile SMTD_todaysLogFileName encoding:#utf8 writeBOM:true
				format "-- BEGIN - % - %/% - 3ds Max %\n" timeString sysinfo.computerName sysinfo.userName (SMTDFunctions.getMaxVersion()) to:SMTD_todaysLogFile

				format "---- OPEN DIALOG : % ---- \n" timeString to:SMTD_todaysLogFile
			)
			else
			(
				SMTD_todaysLogFile = openFile SMTD_todaysLogFileName mode:"at"
				format "---- OPEN DIALOG : % ---- \n" timeString to:SMTD_todaysLogFile
			)
			SMTDFunctions.GetPipelineToolStatus()
			lbl_pipelineTools.text = SMTDSettings.PipelineToolStatus
			initReportWindow dnc_report
			Ui_report (">Starting Up...")

			local theIndex = (findString SMTDPaths.MainSubmissionDir "submission")
			SMTD_MainRollout.title = "SMTD : " + (if theIndex == undefined then "***DISCONNECTED***" else substring SMTDPaths.MainSubmissionDir 1 (theIndex-2) )
			updateControls()
			createNameMenu()
			createCommentMenu()
			dn_tabs.enabled = true
			unregisterSMTDCallbacks()
			registerSMTDCallbacks()
		)

		fn updateAllControls =
		(
			SMTD_MainRollout.updateControls()
			SMTD_MainRollout.updateSubRollouts()
		)

		on SMTD_MainRollout close do
		(
			callbacks.removeScripts id:#SubmitMaxToDeadlineSettings

			try(destroyDialog SubmtMaxToDeadline_SettingsBrowser)catch()
			try(destroyDialog SMTD_PresetDialog)catch()

			SMTDFunctions.unregisterCallbacks()
			try
			(
				local timeArray = getLocalTime()
				local hour = if timeArray[5] < 10 then (hour = "0" + (timeArray[5] as string)) else (hour = (timeArray[5] as string))
				local minute = if timeArray[6] < 10 then (minute = "0" + (timeArray[6] as string)) else (minute = (timeArray[6] as string))
				local second = if timeArray[7] < 10 then (second = "0" + (timeArray[7] as string)) else (second = (timeArray[7] as string))
				local timeString = (timeArray[4] as string) + "-" + (timeArray[2] as string) + "-" + (timeArray[1] as string) + " " + hour + ":" + minute + ":" + second
				format "---- CLOSE DIALOG : % ---- \n" timeString to:SMTD_todaysLogFile
				close SMTD_todaysLogFile
			)catch()
		)

		fn jobNameUpdate =
		(
			if SMTDSettings.AutomaticallyUpdateJobName then
			(
				if getfilenamefile maxfilename != "" then
					SMTDSettings.JobName = getfilenamefile maxfilename
				else
					SMTDSettings.JobName = "Untitled 3ds Max Job"

				edt_jobname.text = SMTDSettings.JobName
			)
		)

		on SMTD_MainRollout moved pos do setIniSetting SMTDPaths.InIFile "Dialog" "Position" (pos as string)

		--HELP BUTTON EVENT HANDLERS
		on btn_help_jobname pressed do ShellLaunch (SMTD_HelpURL + "#submission-options") ""
		on btn_help_comment pressed do ShellLaunch  (SMTD_HelpURL + "#submission-options") ""
		on btn_help_user pressed do ShellLaunch (SMTD_HelpURL + "#submission-options") ""
		on btn_help_dept pressed do ShellLaunch (SMTD_HelpURL + "#submission-options") ""

		on btn_pools_help pressed do  ShellLaunch  (SMTD_HelpURL + "#submission-options") ""
		on btn_pools2_help pressed do ShellLaunch (SMTD_HelpURL + "#submission-options") ""
		on btn_group_help pressed do ShellLaunch (SMTD_HelpURL + "#submission-options") ""
		on btn_priority_help pressed do ShellLaunch (SMTD_HelpURL + "#submission-options") ""
	)--end Main rollout

	rollout SMTD_LimitGroups "Limits" rolledup:true
	(
		--button btn_help_limitgroups "?" width:12 across:2 align:#left offset:[-11,-2] tooltip:"Click for Online Help on using Limits."
		label lbl_limitGroups01 "NOTE: If multiple checked, a Slave must match ALL Limits to render the job. " align:#center
		dotNetControl lv_limitGroups "System.Windows.Forms.ListView" width:480 height:240 align:#center

		group "Set these Limits automatically:"
		(
			checkbox chk_autoWorkstation "" align:#left across:3
			checkbox chk_void01 "" visible:false
			checkbox chk_autoMaxUI "'max' for 3dsMaxIO UBL "
		)

		group "Set a Limit automatically based on the current Renderer:"
		(
			checkbox chk_autoArnold "'arnold' (Arnold) " across:3 align:#left
			checkbox chk_autoBrazil "'brazil' (Brazil r/s) "
			checkbox chk_autoCorona "'corona' (Corona) "

			checkbox chk_autoFinalRender "'finalrender' (finalRender) " across:3 align:#left
			checkbox chk_autoIray "'iray' (Iray) "
			checkbox chk_autoKrakatoa "'krakatoa' (Krakatoa) "

			checkbox chk_autoMaxwell "'maxwell' (Maxwell) " across:3 align:#left
			checkbox chk_autoMentalRay "'mentalray' (Mental Ray) "
			checkbox chk_autoOctane "'octane' (Octane) "

			checkbox chk_autoRedshift "'redshift' (Redshift) " align:#left across:3
			checkbox chk_autoVRay "'vray' (V-Ray), 'vrayrt' (V-Ray RT) "
			checkbox chk_void02 "" visible:false
		)
		fn initListView =
		(
			lv_limitGroups.gridLines = true
			lv_limitGroups.View = (dotNetClass "System.Windows.Forms.View").Details
			lv_limitGroups.fullRowSelect = true

			lv_limitGroups.checkboxes = true
			--lv_limitGroups.BackColor = lv_limitGroups.BackColor.FromArgb 210 215 225

			lv_limitGroups.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			lv_limitGroups.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r (amin (SMTD_ColorPalette.maxBgColor.g+15) 255) (amin (SMTD_ColorPalette.maxBgColor.b+5) 255)

			lv_limitGroups.LabelEdit = false
			column = lv_limitGroups.Columns.add "Limits - Click here to update list from the Repository" 350
		)

		local isUpdatingList = false
		fn updateListView =
		(
			isUpdatingList = true
			local theRange = #()
			lv_limitGroups.Items.clear()
			--lv_limitGroups.ListItems.clear()
			for i in SMTDSettings.LimitGroups do
			(
				li = dotNetObject "System.Windows.Forms.ListViewItem" i
				li.checked = findItem SMTDSettings.LimitGroupsToUse i > 0
				append theRange li
			)
			lv_limitGroups.Items.AddRange theRange
			isUpdatingList = false
		)

		on btn_help_limitgroups pressed do ShellLaunch  (SMTD_HelpURL + "#limits-tab") ""

		on lv_limitGroups ColumnClick hdr do
		(
			SMTDFunctions.CollectLimitGroups()
			updateListView()
		)
		on SMTD_LimitGroups open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening Limits Rollout"
			chk_autoWorkstation.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoWorkstation"  ("'" + (SMTDFunctions.getPluginToUse()) + (SMTDFunctions.getMaxVersion()) + "workstation' (Force Workstation mode) ")
			chk_autoBrazil.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoBrazil"  "'brazil' (Brazil r/s) "
			chk_autoFinalRender.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoFinalRender"  "'finalrender' (finalRender) "
			chk_autoKrakatoa.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoKrakatoa"  "'krakatoa' (Krakatoa) "
			chk_autoMaxwell.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoMaxwell"  "'maxwell' (Maxwell) "
			chk_autoVRay.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoVRay"  "'vray' (V-Ray), 'vrayrt' (V-Ray RT) "
			chk_autoCorona.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoCorona"  "'corona' (Corona) "
			chk_autoArnold.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoArnold"  "'arnold' (Arnold) "
			chk_autoIray.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoIray"  "'iray' (Iray) "
			chk_autoMentalRay.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoMentalRay"  "'mentalray' (Mental Ray) "
			chk_autoRedshift.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoRedshift"  "'redshift' (Redshift) "
			chk_autoMaxUI.caption = 	SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoMaxIO"  "'max' (3dsMaxIO UBL) "
			chk_autoOctane.caption = SMTDFunctions.getStickyCaption "LimitGroups" "LimitGroupAutoOctane"  "'octane' (Octane) "

			chk_autoWorkstation.checked = SMTDSettings.LimitGroupAutoWorkstation
			chk_autoBrazil.checked = SMTDSettings.LimitGroupAutoBrazil
			chk_autoFinalRender.checked = SMTDSettings.LimitGroupAutoFinalRender
			chk_autoKrakatoa.checked = SMTDSettings.LimitGroupAutoKrakatoa
			chk_autoMaxwell.checked = SMTDSettings.LimitGroupAutoMaxwell
			chk_autoVRay.checked = SMTDSettings.LimitGroupAutoVRay
			chk_autoCorona.checked = SMTDSettings.LimitGroupAutoCorona
			chk_autoArnold.checked = SMTDSettings.LimitGroupAutoArnold
			chk_autoIray.checked = SMTDSettings.LimitGroupAutoIray
			chk_autoMentalRay.checked = SMTDSettings.LimitGroupAutoMentalRay
			chk_autoRedshift.checked = SMTDSettings.LimitGroupAutoRedshift
			chk_autoMaxUI.checked = SMTDSettings.LimitGroupAutoMaxIO
			chk_autoOctane.checked = SMTDSettings.LimitGroupAutoOctane

			if SMTDSettings.LimitGroups.count == 0 do SMTDFunctions.CollectLimitGroups()

			initListView()
			updateListView()
		)

		on lv_limitGroups ItemChecked itm do
		(
			if not isUpdatingList do
			(
				theItem = itm.Item
				theText = theItem.Text
				if theItem.checked then
				(
					append SMTDSettings.LimitGroupsToUse theText
					SMTD_MainRollout.Ui_report ("+Limits - Limit ADDED : [" + theText + "]")
				)
				else
				(
					theIndex = findItem SMTDSettings.LimitGroupsToUse theText
					if theIndex > 0 then
					(
						deleteItem SMTDSettings.LimitGroupsToUse theIndex
						SMTD_MainRollout.Ui_report ("+Limits - Limit REMOVED : [" + theText + "]")
					)
				)
				theString = "#("
				for i in SMTDSettings.LimitGroupsToUse do (theString += "\""+ i as string + "\",")
				theString += "\"\")"
				setIniSetting SMTDPaths.iniFile "LimitGroups" "LimitGroupsToUse" theString
				SMTD_MainRollout.Ui_report (">LimitGroups - Currently Enabled : [" + theString + "]") LogFileOnly:true
			)
		)

		on chk_autoWorkstation changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoWorkstation" ( (SMTDSettings.LimitGroupAutoWorkstation = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic Workstation Limit mode set to [" + state as string + "]")
		)
		on chk_autoMaxUI changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoMaxIO" ( (SMTDSettings.LimitGroupAutoMaxIO = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic MaxIO Limit mode set to [" + state as string + "]")
		)

		on chk_autoArnold changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoArnold" ( (SMTDSettings.LimitGroupAutoArnold = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic Arnold Limit mode set to [" + state as string + "]")
		)
		on chk_autoBrazil changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoBrazil" ( (SMTDSettings.LimitGroupAutoBrazil = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic Brazil r/s Limit mode set to [" + state as string + "]")
		)
		on chk_autoCorona changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoCorona" ( (SMTDSettings.LimitGroupAutoCorona = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic Corona Limit mode set to [" + state as string + "]")
		)
		on chk_autoFinalRender changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoFinalRender" ( (SMTDSettings.LimitGroupAutoFinalRender = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic finalRender Limit mode set to [" + state as string + "]")
		)
		on chk_autoIray changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoIray" ( (SMTDSettings.LimitGroupAutoFinalRender = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic Iray Limit mode set to [" + state as string + "]")
		)
		on chk_autoKrakatoa changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoKrakatoa" ( (SMTDSettings.LimitGroupAutoKrakatoa = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic Krakatoa Limit mode set to [" + state as string + "]")
		)
		on chk_autoMaxwell changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoMaxwell" ( (SMTDSettings.LimitGroupAutoMaxwell = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic Maxwell Limit mode set to [" + state as string + "]")
		)
		on chk_autoMentalRay changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoMentalRay" ( (SMTDSettings.LimitGroupAutoMaxwell = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic Mental Ray Limit mode set to [" + state as string + "]")
		)
		on chk_autoOctane changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoOctane" ( (SMTDSettings.LimitGroupAutoOctane = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic Octane Limit mode set to [" + state as string + "]")
		)
		on chk_autoRedshift changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoRedshift" ( (SMTDSettings.LimitGroupAutoOctane = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic Redshift Limit mode set to [" + state as string + "]")
		)
		on chk_autoVRay changed state do
		(
			setIniSetting SMTDPaths.InIFile "LimitGroups"  "LimitGroupAutoVRay" ( (SMTDSettings.LimitGroupAutoVRay = state) as string)
			SMTD_MainRollout.Ui_report ("+Limits - Automatic V-Ray Limit mode set to [" + state as string + "]")
		)
	)

	rollout SMTD_BlackListSlaves "Blacklist/Whitelist Slaves" rolledup:false
	(
		local theSlaveInfoFile = (SMTDPaths.SettingsDir + "slaveselectionsets\\slavesinfo.ini" )
		local theSelSetFiles = #()
		--button btn_help_blacklist "?" width:12 across:5 align:#left offset:[-11,-2] tooltip:"Click for Online Help on Blacklisting Slaves."
		checkbox chk_blacklistSticky "Sticky Blacklist Settings" align:#left height:18 offset:[-10,-3] across:4 tooltip:"When checked, the Black List settings specified in this dialog will be stored between sessions and will be applied each time the SMTD Dialog is opened.\n\nWhen unchecked, the Black List settings will have to be specified manually in each new SMTD session."

		button btn_saveSelSet "Save List As Selection Set"  align:#right width:137 height:18 offset:[147,-3] tooltip:"Enter a name in the text field below and press this button to save the right-hand-side list of Slave names as a named preset.\n\nIt can be restored easily by selecting from the drop-down list on the left side, or cleared by selecting the [None] entry."
		button btn_deleteSelSet "Delete"  align:#right width:45 height:18 offset:[78,-3] tooltip:"Select a Selection Set from the drop-down list on the left or enter the name in the text field, then press this button to DELETE the named Selection Set from Disk."
		button btn_exploreSelSet "Explore"  align:#right width:45 height:18 offset:[9,-3] tooltip:"Press to EXPLORE the Selection Sets Folder"

		dropdownlist ddl_slaveSelSet width:230 align:#left across:2 offset:[-10,-5] tooltip:"Lists the previously saved Slave Selection Sets plus the [None] entry which cannot be removed.\n\nSelect a Slave Selection Set from the list to quickly populate the Blacklist/Whitelist with pre-defined machine names."
		edittext edt_SelSetName width:232 align:#right offset:[8,-3]

		label lbl_slavesList " Blacklisted Slaves (Will Not Render):  " align:#left offset:[-10,-3] across:2
		label lbl_blackList " Blacklisted Slaves (May Render):       " align:#right offset:[10,-3]
		dotNetControl dnc_slavesList "ListView" width:230 height:160 align:#left offset:[-10,-3] across:2
		dotNetControl dnc_blackList "ListView" width:230 height:160 align:#right offset:[10,-3]

		button btn_selectAllSlaves "Select ALL" width:114 align:#left across:4 height:18 offset:[-9,-3] tooltip:"Select All Slaves in the left list."
		button btn_selectInvertSlaves "INVERT Selection" width:114 align:#left offset:[-9,-3] height:18 tooltip:"Invert Current Selection."
		button btn_selectAllList "Select ALL" width:114 align:#right offset:[10,-3] height:18 tooltip:"Select All Slaves in the right list."
		button btn_selectInvertList "INVERT Selection" width:114 align:#right height:18 offset:[10,-3] tooltip:"Invert Current Selection."

		edittext edt_filter "" text:"" across:4 align:#left offset:[-13,-3] fieldwidth:114
		button btn_update "UPDATE Slaves Info"  align:#left width:114 height:18 offset:[-9,-3] tooltip:"Reloads the Slave Names and Info from the Repository."

		radiobuttons rad_blackList labels:#("Blacklist","Whitelist") offset:[25,-3] align:#right columns:2 tooltip:"Controls whether the right list will be used as a Blacklist or Whitelist.\n\nWhen set to Blacklist, the machines listed on the right side will be excluded from rendering the submitted job, while the machines listed on the left will be allowed to work on it.\n\nWhen set to Whitelist, the machines listed on the right will be allowed to work on the job and the ones on the left will not."

		button btn_moveToList ">>" width:20 offset:[-171,-185] height:72 tooltip:"Move selected Slaves to the right list" images:#(oneArrowIconBitmap,oneArrowIconMask,2,1,1,2,2)
		button btn_moveToSlaves "<<" width:20 offset:[0,-125] height:72 tooltip:"Move selected Slaves back to the left list." images:#(oneArrowIconReverseBitmap,oneArrowIconReverseMask,2,1,1,2,2)

		fn initDotNetControl lv foreColor BgColor =
		(
			local layout_def = #(#("Slave Name",150), #("Status",55) )
			lv.Clear()
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB BgColor.r BgColor.g BgColor.b
			lv.foreColor = (dotNetClass "System.Drawing.Color").fromARGB foreColor.r foreColor.g foreColor.b
			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.gridLines = true
			lv.fullRowSelect = true
			lv.checkboxes = false
			lv.hideSelection = false
			--lv.HeaderStyle = lv.HeaderStyle.None
			for i in layout_def do lv.Columns.add i[1] i[2]
		)

		fn populateDotNetControl lv theList =
		(
			local theRange = #()
			lv.Items.clear()
			--local foreColor =  (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			local offlineColor = (dotNetClass "System.Drawing.Color").fromARGB 150 150 150
			local idleColor = (dotNetClass "System.Drawing.Color").fromARGB 50 150 255
			local renderColor = (dotNetClass "System.Drawing.Color").fromARGB 0 200 50
			local stalledColor = (dotNetClass "System.Drawing.Color").fromARGB 255 50 50
			local startingColor = (dotNetClass "System.Drawing.Color").fromARGB 200 100 50

			for i in theList do
			(
				local li = dotNetObject "System.Windows.Forms.ListViewItem" i
				local theState = (getIniSetting theSlaveInfoFile i "SlaveStatus")
				local subLi = li.SubItems.add theState
				case theState of
				(
					"Offline": li.forecolor = offlineColor
					"Rendering": (li.forecolor = renderColor; subLi.text = "Render")
					"Idle": li.forecolor = idleColor
					"Stalled": li.forecolor = stalledColor
					default: li.forecolor = startingColor
				)
				append theRange li
			)
			lv.Items.AddRange theRange
		)

		fn storeSlaveList =
		(
			local theListString = "#("
			if SMTDSettings.SlavesList.count > 0 do
			(
				for i = 1 to SMTDSettings.SlavesList.count-1 do theListString += "\"" + SMTDSettings.SlavesList[i] + "\","
				theListString += "\"" + SMTDSettings.SlavesList[SMTDSettings.SlavesList.count]
			)
			theListString += "\")"
			setIniSetting SMTDPaths.InIFile "Blacklist"  "SlavesList" theListString
		)

		fn storeNamedSelectionSet =
		(
			setIniSetting SMTDPaths.InIFile "Blacklist"  "SlavesNamedSet"  (SMTDSettings.SlavesNamedSet )
			SMTD_MainRollout.Ui_report ("+Black/Whitelist: Named Slave Selection set to [" + SMTDSettings.SlavesNamedSet + "]")
		)

		fn populateSlavelists =
		(
			local List1 = for i in (sort SMTDSettings.Slaves) where findItem SMTDSettings.SlavesList i == 0 collect i
			local List2 = for i in (sort SMTDSettings.SlavesList) collect i
			populateDotNetControl dnc_slavesList List1
			populateDotNetControl dnc_blackList List2
			storeSlaveList()
		)

		fn updateSlaveList forceUpdate:false=
		(
			if SMTDSettings.Slaves.count == 0 or forceUpdate do
			(
				SMTDFunctions.CollectSlaves()
			)

			local BgColor1 = color 255 255 255
			local foreColor1 = color 50 50 50
			local BgColor2 = color 50 50 50
			local foreColor2 = color 255 255 255
			if not SMTDSettings.SlavesBlackList then
			(
				BgColor1 = color 50 50 50
				foreColor1 = color 255 255 255
				BgColor2 = color 255 255 255
				foreColor2 = color 50 50 50
			)
			initDotNetControl dnc_slavesList foreColor1 BgColor1
			initDotNetControl dnc_blackList foreColor2 BgColor2

			populateSlavelists()
		)

		fn updateSelectionSetList =
		(
			local thePath = (SMTDPaths.SettingsDir + "slaveselectionsets")
			makeDir SMTDPaths.SettingsDir
			makeDir thePath
			theSelSetFiles = getFiles (thePath + "\\*.slaves")
			ddl_slaveSelSet.items = join #("[None]") (for f in theSelSetFiles collect getFileNameFile f)
			theIndex = findItem ddl_slaveSelSet.items SMTDSettings.SlavesNamedSet
			if theIndex == 0 do theIndex = 1
			ddl_slaveSelSet.selection = theIndex
		)

		fn updateWhiteBlackListCaption =
		(
			case rad_blackList.state of
			(
				1:
				(
					lbl_slavesList.caption = "Whitelisted Slaves (May Render):"
					lbl_blackList.caption = "Blacklisted Slaves (Will Not Render):"
				)
				2:
				(
					lbl_slavesList.caption = "Blacklisted Slaves (Will Not Render):"
					lbl_blackList.caption = "Whitelisted Slaves (May Render):"
				)
			)

		)

		on chk_blacklistSticky changed state do
		(
			setIniSetting SMTDPaths.InIFile "Blacklist"  "SlaveSettingsSticky"  ((SMTDSettings.SlaveSettingsSticky = state) as string)
			SMTD_MainRollout.Ui_report ("+Black/Whitelist: Make Settings Sticky set to [" + state as string + "]")
		)

		on rad_blackList changed val do
		(
			setIniSetting SMTDPaths.InIFile "Blacklist"  "BlackOrWhite" ( (SMTDSettings.SlavesBlackList = (val == 1) ) as string)
			SMTD_MainRollout.Ui_report ("+Black/Whitelist: Mode set to [" + #("Blacklist","Whitelist")[val] + "]")
			updateWhiteBlackListCaption()
			updateSlaveList()
		)

		fn getListViewSelection lv =	--returns an array of the selected ListView items
		(
			try
				for i = 1 to lv.items.count where lv.items.item[i-1].Selected collect i
			catch
				#()
		)

		fn setListViewSelection lv theSel =
		(
			for i = 1 to lv.items.count do lv.items.item[i-1].Selected = theSel[i]
		)

		on btn_selectAllSlaves pressed do
		(
			setListViewSelection dnc_slavesList #{1..dnc_slavesList.Items.Count}
		)

		on btn_selectInvertSlaves pressed do
		(
			local theSel = (getListViewSelection dnc_slavesList) as bitarray
			setListViewSelection dnc_slavesList (#{1..dnc_slavesList.Items.Count}-theSel)
		)

		on btn_selectAllList pressed do
		(
			setListViewSelection dnc_blackList #{1..dnc_blackList.Items.Count}
		)

		on btn_selectInvertList pressed do
		(
			local theSel = (getListViewSelection dnc_blackList) as bitarray
			setListViewSelection dnc_blackList (#{1..dnc_blackList.Items.Count}-theSel)
		)

		on edt_filter changed txt do
		(
			if txt != "" then
			(
				local theSel = (for i = 1 to dnc_slavesList.items.count where matchPattern dnc_slavesList.items.item[i-1].text pattern:(txt+"*") collect i) as bitarray
				setListViewSelection dnc_slavesList theSel
			)
			else
				setListViewSelection dnc_slavesList #{}
		)

		on btn_update pressed do
		(
			SMTDFunctions.CollectSlavesInfo()
			updateSlaveList forceUpdate:true
		)

		on btn_moveToList pressed do
		(
			local theSel = getListViewSelection dnc_slavesList
			local tempArray = deepCopy SMTDSettings.SlavesList
			--local tempArray = for i = 1 to dnc_blackList.items.count collect dnc_blackList.items.item[i-1].text
			local tempArray2 = (for i in theSel collect dnc_slavesList.items.item[i-1].text)
			join tempArray tempArray2
			sort tempArray
			SMTDSettings.SlavesList = deepCopy tempArray
			populateSlavelists()
			theSel = for i in tempArray2 collect (theIndex = findItem tempArray i; if theIndex > 0 then theIndex else dontcollect)
			setListViewSelection dnc_blackList (theSel as bitarray)
		)

		on btn_moveToSlaves pressed do
		(
			local theSel = getListViewSelection dnc_blackList
			local tempArray = deepCopy SMTDSettings.SlavesList
			local tempArray2 = for i in theSel collect SMTDSettings.SlavesList[i]
			for i = theSel.count to 1 by -1 do deleteItem tempArray theSel[i]
			SMTDSettings.SlavesList = deepCopy tempArray
			populateSlavelists()
			local tempArray3 = for i = 1 to dnc_slavesList.items.count collect dnc_slavesList.items.item[i-1].text
			theSel = for i in tempArray2 collect (theIndex = findItem tempArray3 i; if theIndex > 0 then theIndex else dontcollect)
			setListViewSelection dnc_slavesList (theSel as bitarray)
		)

		on dnc_slavesList DoubleClick EventArgs do btn_moveToList.pressed()
		on dnc_blackList DoubleClick EventArgs do btn_moveToSlaves.pressed()

		on btn_saveSelSet pressed do
		(
			if edt_SelSetName.text != "" then
			(
				local theFileName = (SMTDPaths.SettingsDir + "slaveselectionsets\\" + edt_SelSetName.text + ".slaves" )
				if doesFileExist theFileName then
					SMTD_MainRollout.Ui_report ("+Black/Whitelist: Updated Slave Selection Set [" + edt_SelSetName.text + "]." )
				else
					SMTD_MainRollout.Ui_report ("+Black/Whitelist: Created Slave Selection Set [" + edt_SelSetName.text + "]." )

				local theFile = createFile theFileName  encoding:#utf8 writeBOM:true
				if theFile != undefined then
				(
					tempArray = SMTDSettings.SlavesList
					for i in tempArray do
						format "%\n" i to:theFile
					close theFile
					SMTDSettings.SlavesNamedSet = edt_SelSetName.text
					storeNamedSelectionSet()
					--edt_SelSetName.text = ""
					updateSelectionSetList()
				)
			)
			else
				SMTD_MainRollout.Ui_report ("--Black/Whitelist: Could NOT Save - No Name for the Slave Selection Set specified.")
		)

		on btn_exploreSelSet pressed do
		(
			shellLaunch "explorer.exe" (SMTDPaths.SettingsDir + "slaveselectionsets\\")
		)


		on btn_deleteSelSet pressed do
		(
			if edt_SelSetName.text != "" then
			(
				local theFileName = (SMTDPaths.SettingsDir + "slaveselectionsets\\" + edt_SelSetName.text + ".slaves" )
				if doesFileExist theFileName then
				(
					local q = querybox ("Delete Slave Selection Set ["+edt_SelSetName.text+"]?\nIf you click Yes, a Backup of the Selection Set will be created.\nYou can restore the Selection Set by pressing [E] to Explore the folder\nand by removing the .BAK Extension manually.") title:"Delete Slave Selection Set"
					if q then
					(
						if doesFileExist (theFileName+".bak") do deleteFile (theFileName+".bak")
						renameFile theFileName (theFileName+".bak")
						SMTD_MainRollout.Ui_report ("+Black/Whitelist: Removed Slave Selection Set [" + edt_SelSetName.text + "]. Backup File Created." )
						updateSelectionSetList()
						edt_SelSetName.text = ""
					)
				)
				else
					SMTD_MainRollout.Ui_report ("+Black/Whitelist: Could NOT Remove Slave Selection Set [" + edt_SelSetName.text + "] - No Such List!" )
			)
		)

		on ddl_slaveSelSet selected itm do
		(
			if itm > 1 then
			(
				local theFileName = theSelSetFiles[itm-1]
				local theFile = openFile theFileName
				local theArray = #()
				while not eof theFile do
					append theArray (readline theFile)
				close theFile
				SMTDSettings.SlavesList = deepCopy theArray
				populateSlavelists()
			)
			else
			(
				SMTDSettings.SlavesList = #()
				populateSlavelists()
				--mlb_blackList.items = #()
				--mlb_slavesList.items = for i in (sort SMTDSettings.Slaves) collect i
			)
			edt_SelSetName.text = SMTDSettings.SlavesNamedSet = ddl_slaveSelSet.selected
			storeNamedSelectionSet()
			if itm == 1 then edt_SelSetName.text = ""
			storeSlaveList()
		)

		on SMTD_BlackListSlaves open do
		(
			if SMTDSettings.DBR == false do
			(
				if SMTDSettings.SlaveInfoCollected == false do
				(
					SMTDFunctions.CollectSlavesInfo()
					SMTDSettings.SlaveInfoCollected = true
				)

				chk_blacklistSticky.state = SMTDSettings.SlaveSettingsSticky
				rad_blackList.state = if SMTDSettings.SlavesBlackList then 1 else 2

				updateSlaveList()
				updateSelectionSetList()
				updateWhiteBlackListCaption()
			)

			for control in SMTD_BlacklistSlaves.controls do control.enabled = not SMTDSettings.DBR
		)

		on btn_help_blacklist pressed do ShellLaunch  (SMTD_HelpURL + "#limits-tab") ""
	)
	rollout SMTD_PassDependencies "RPM Pass Dependencies" rolledup:true
	(
		checkbox chk_submitAsPassDependent "Submit with Pass Dependencies" offset:[0,-2] align:#left enabled:true across:2
		checkbox chk_do_local_dependencies "Per Pass Dependencies" offset:[60,-2] align:#left enabled:true --across:1
		label lb1 "All passes will be submitted as dependent on checked *if* submitted together, and the " align:#left
		label lb2 "checked jobs are submitted first (reorder passes as needed)" align:#left
		--button btn_updatePasses "Update Pass List" width:150 align:#right offset:[5,-4] tooltip:"Gets current passes"
		dotNetControl dnc_passesToDependOn "ListView" width:480 height:160 align:#center offset:[0,-2]


		fn updatePassDisplay =
		(
			enabled = rpmdata.getcustglobstorage 10000
			if enabled == undefined do enabled = false

			chk_submitAsPassDependent.state = enabled
			islocal = rpmdata.getcustglobstorage 10004
			if islocal == undefined do islocal = false
			chk_do_local_dependencies.state = islocal

			theRange = #()
			if rpmdata.getpasscount() > 0 then
			(
				for i in 1 to rpmdata.getpasscount() do
				(
					local li = dotNetObject "System.Windows.Forms.ListViewItem" (rpmdata.getpassname i)
					li.foreColor = foreColor
					append theRange li
				)
				dnc_passesToDependOn.Items.clear()
				dnc_passesToDependOn.Items.AddRange theRange

				-- restore which are checked
				if islocal == true then
				(
					currentpasses = rpmdata.getpassselection()
					if currentpasses.count > 0 do
					(
						currentpass = currentpasses[1]

						passStates = rpmdata.GetCustPassStorage currentpass 10001
						if passStates != undefined and classof passStates == Array do
						(
							for i in 1 to rpmdata.getpasscount() do
							(
								uniqueindex = (rpmdata.getUniqueFromIndex i)
								--try(dnc_passesToDependOn.Items.item[i - 1].checked = passStates[i]  )catch(dnc_passesToDependOn.Items.item[i - 1].checked = false)

								try(
									 if finditem passStates uniqueindex != 0 do
										dnc_passesToDependOn.Items.item[i - 1].checked = true
								)catch(dnc_passesToDependOn.Items.item[i - 1].checked = false)

							)
						)
					)
				)
				else
				(
				passStates = rpmdata.getcustglobstorage 10001
				if passStates != undefined and classof passStates == Array do
				(
					for i in 1 to rpmdata.getpasscount() do
					(
						uniqueindex = (rpmdata.getUniqueFromIndex i)
						try(
							 if finditem passStates uniqueindex != 0 do
								dnc_passesToDependOn.Items.item[i - 1].checked = true
						)catch(dnc_passesToDependOn.Items.item[i - 1].checked = false)
					)
					)
				)
			) else dnc_passesToDependOn.Items.clear()


		)
		fn storeCheckedPasses =
		(
			local passStates = #()
			islocal  = rpmdata.getcustglobstorage 10004
			if islocal == undefined do islocal = false
			if islocal == false then
			(
				try(passStates = rpmdata.getcustglobstorage 10001)catch(passStates = #(); passStates.count = rpmdata.getpasscount())
			if passStates == undefined do
			(
				passStates = #()
				passStates.count = rpmdata.getpasscount()
			)
			for i in 1 to dnc_passesToDependOn.items.count do
			(
						uniqueindex = (rpmdata.getUniqueFromIndex i)
					if dnc_passesToDependOn.items.item[i-1] == undefined do continue
					if dnc_passesToDependOn.items.item[i-1].checked then
						(
							--passStates[i] = true
							if finditem passStates uniqueindex == 0 do
								append passStates uniqueindex
						)else(
							--passStates[i] = false
							if finditem passStates uniqueindex != 0 do
								deleteitem passStates (finditem passStates uniqueindex)
						)
			)
			rpmdata.setcustglobstorage 10001 passStates
			) else (
				currentpass = rpmdata.getpassselection()
				if currentpass.count > 0 do
				(
					currentpass = currentpass[1]

					try(passStates = rpmdata.GetCustPassStorage currentpass 10001)catch(passStates = #(); passStates.count = rpmdata.getpasscount())
					if passStates == undefined do
					(
						passStates = #()
						--passStates.count = rpmdata.getpasscount()
					)
					for i in 1 to dnc_passesToDependOn.items.count do
					(
							uniqueindex = (rpmdata.getUniqueFromIndex i)
							if dnc_passesToDependOn.items.item[i-1] == undefined do continue
							if dnc_passesToDependOn.items.item[i-1].checked then
							(
								--passStates[i] = true
								if finditem passStates uniqueindex == 0 do
									append passStates uniqueindex
							)else(
								--passStates[i] = false
								if finditem passStates uniqueindex != 0 do
									deleteitem passStates (finditem passStates uniqueindex)
							)
					)
					rpmdata.SetCustPassStorage currentpass 10001 passStates
				)

			)
		)
		--on dnc_passesToDependOn itemchecked event do
		--(
		--	print "itemchecked"
		--	storeCheckedPasses()
		--)
		--on dnc_passesToDependOn mousedown event do
		--(
		--	print "mousedown"
		--	storeCheckedPasses()
		--)
		on dnc_passesToDependOn mouseup event do
		(
			--print "mouseup"
			storeCheckedPasses()
		)
		on dnc_passesToDependOn mouseleave event do
		(
			-- the other events are triggered before the checkbox is actually active. What is up with that.
			--print "mouseleave"
			storeCheckedPasses()
		)

		fn initDotNetControls lv BgColor =
		(
			local layout_def = #(#("Pass Name",470))
			lv.Clear()

			--lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB BgColor.r BgColor.g BgColor.b
			lv.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r SMTD_ColorPalette.maxBgColor.g SMTD_ColorPalette.maxBgColor.b

			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.gridLines = false
			lv.fullRowSelect = true
			lv.checkboxes = true
			lv.hideSelection = true
			--lv.HeaderStyle = lv.HeaderStyle.None
			for i in layout_def do lv.Columns.add i[1] i[2]
		)
		on chk_submitAsPassDependent changed state do
		(
			rpmdata.setcustglobstorage 10000 state
			SMTD_MainRollout.Ui_report ("+Job Options: Submit As Pass Dependent set to [" + state as string + "]")
		)
		on chk_do_local_dependencies changed state do
		(
			rpmdata.setcustglobstorage 10004 state
			updatePassDisplay()
			SMTD_MainRollout.Ui_report ("+Job Options: Submit As Pass Dependent Per Pass set to [" + state as string + "]")
		)

		on SMTD_PassDependencies open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Adding Job Dependencies Per Pass Rollout"

			local theBGColor = ((colorman.getcolor #window) as color)*255
			initDotNetControls dnc_passesToDependOn (theBGColor+(color 0 10 0))

			updatePassDisplay()
		)
	)

	rollout SMTD_Dependencies "Job Dependencies" rolledup:true
	(
		local currentJobsArray = #()


		checkbox chk_submitAsDependent "Submit Job As Dependent *" offset:[0,-2] align:#left enabled:false across:3
		button btn_getJobs "Get Jobs List" width:150 align:#right offset:[5,-4] tooltip:"Populates the Jobs List with all Jobs currently in the Repository. Can Take A While..."
		button btn_clearDependencyList "Clear Dependencies List" width:150 align:#right offset:[10,-4] tooltip:"Removes all Jobs from the Dependency List and unchecks the Submit Job As Dependent option."

		dropdownlist ddl_DependOnPreviousJobMode items:#("Depend On The LAST Submitted Job","Depend On A PREVIOUSLY Submitted Job","CUSTOM Dependency - Press [Get Job List] To Update From Repository...") width:480 align:#center offset:[0,-2]


		dotNetControl dnc_jobsToDependOn "ListView" width:480 height:80 align:#center offset:[0,-2]
		--listbox ddl_jobsToDependOn items:#() offset:[0,-2] height:4 align:#center width:500 enabled:false

		edittext edt_filterJobs "Filter" text:"" fieldwidth:255 align:#left across:3 offset:[-10,-1]
		button btn_clearFilterJobs "X" width:22 height:20 align:#center offset:[58,-2] tooltip:"Clears The Name/ID Filter"
		dropdownlist ddl_filterStatus items:#("") width:165 align:#right offset:[11,-2] align:#right

		button btn_filterMe "Me" across:4 width:22 align:#left offset:[-10,-3] tooltip:"Tries to set the User Filter to the user name specified in the Name field in the Job Description group of controls."
		dropdownlist ddl_filterUser items:#("") width:120 offset:[-100,-3] align:#center
		dropdownlist ddl_filterDept items:#("") width:165 offset:[-70,-3] align:#center
		dropdownlist ddl_filterGroup items:#("") width:165 offset:[10,-3] align:#right

		dotNetControl dnc_allJobs "ListView" width:480 height:150 align:#center offset:[0,-2]
		--listbox ddl_allJobs items:#() offset:[0,-5] height:10 align:#center width:500 enabled:false

		fn initDotNetControls lv BgColor =
		(
			local layout_def = #(#("Job ID",130), #("Job Name",300), #("Status",70), #("Plugin",70), #("User", 70), #("Dept.",70), #("Group",70) )
			lv.Clear()

			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB BgColor.r BgColor.g BgColor.b

			lv.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			--lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r SMTD_ColorPalette.maxBgColor.g SMTD_ColorPalette.maxBgColor.b

			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.gridLines = false
			lv.fullRowSelect = true
			lv.checkboxes = false
			lv.hideSelection = true
			--lv.HeaderStyle = lv.HeaderStyle.None
			for i in layout_def do lv.Columns.add i[1] i[2]
		)

		fn filterJobsList =
		(
			userPattern = if ddl_filterUser.selection == 1 then "*" else ddl_filterUser.selected
			deptPattern = if ddl_filterDept.selection == 1 then "*" else ddl_filterDept.selected
			groupPattern = if ddl_filterGroup.selection == 1 then "*" else ddl_filterGroup.selected
			tmpArray = #()
			for i = 1 to currentJobsArray.count where \
				not SMTDSettings.dependencyJobItems[i] and \
				matchPattern (currentJobsArray[i][1]+currentJobsArray[i][2]) pattern:("*"+edt_FilterJobs.text+"*") and \
				matchPattern currentJobsArray[i][4] pattern:userPattern and \
				matchPattern currentJobsArray[i][5] pattern:deptPattern and \
				matchPattern currentJobsArray[i][6] pattern:groupPattern do
					case ddl_filterStatus.selection of
					(
						1: append tmpArray currentJobsArray[i]
						2: if not matchPattern currentJobsArray[i][7] pattern:"Completed" do append tmpArray currentJobsArray[i]
						default: if matchPattern currentJobsArray[i][7] pattern:ddl_filterStatus.selected do append tmpArray currentJobsArray[i]
					)

			--ddl_allJobs.items = tmpArray

			local theRange = #()
			dnc_allJobs.Items.clear()
			local foreColor =  (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			for i in tmpArray do
			(
				local li = dotNetObject "System.Windows.Forms.ListViewItem" i[2]
				li.forecolor = foreColor
				local subLi = li.SubItems.add i[1]
				local subLi = li.SubItems.add i[7]
				local subLi = li.SubItems.add i[3]
				local subLi = li.SubItems.add i[4]
				local subLi = li.SubItems.add i[5]
				local subLi = li.SubItems.add i[6]
				append theRange li
			)
			dnc_allJobs.Items.AddRange theRange
		)

		fn updateDependencyDisplay =
		(
			allUsersArray = #()
			edt_filterJobs.enabled = btn_clearFilterJobs.enabled = ddl_filterStatus.enabled = btn_filterMe.enabled = ddl_filterUser.enabled = ddl_filterDept.enabled = ddl_filterGroup.enabled = dnc_allJobs.enabled = true
			case SMTDSettings.DependOnPreviousJobMode of
			(
				default:
				(
					currentJobsArray = deepCopy SMTDSettings.JobsArray
					btn_getJobs.enabled = true
				)
				#previous:
				(
					currentJobsArray = deepCopy SMTDSettings.PreviousJobsArray
					btn_getJobs.enabled = false
				)
				#last:
				(
					if SMTDSettings.PreviousJobsArray.count > 0 then
					(
						currentJobsArray = #(SMTDSettings.PreviousJobsArray[SMTDSettings.PreviousJobsArray.count])
					)
					else
					(
						currentJobsArray = #()
					)
					edt_filterJobs.enabled = btn_clearFilterJobs.enabled = ddl_filterStatus.enabled = btn_filterMe.enabled = ddl_filterUser.enabled = ddl_filterDept.enabled = ddl_filterGroup.enabled = dnc_allJobs.enabled = false
					btn_getJobs.enabled = false
				)
			)

			for i in currentJobsArray where findItem allUsersArray i[4] == 0 do append allUsersArray i[4]
			sort allUsersArray
			allUsersArray = join #("ANY USER") allUsersArray
			ddl_filterUser.items = allUsersArray

			allDeptsArray = #()
			for i in currentJobsArray where findItem allDeptsArray i[5] == 0 do append allDeptsArray i[5]
			sort allDeptsArray
			allDeptsArray = join #("ANY DEPARTMENT") allDeptsArray
			ddl_filterDept.items = allDeptsArray

			allCatsArray = #()
			for i in currentJobsArray where findItem allCatsArray i[6] == 0 do append allCatsArray i[6]
			sort allCatsArray
			allCatsArray= join #("ANY GROUP") allCatsArray
			ddl_filterGroup.items = allCatsArray

			allStatesArray = #()
			for i in currentJobsArray where findItem allStatesArray i[7] == 0 do append allStatesArray i[7]
			sort allStatesArray
			allStatesArray = join #("ANY STATUS", "NON-COMPLETED") allStatesArray
			ddl_filterStatus.items = allStatesArray

			SMTDSettings.FullJobsArray = for i in currentJobsArray collect (i[1] + " : " + i[2])
			if currentJobsArray.count > 0 do
			(
				chk_submitAsDependent.enabled = dnc_jobsToDependOn.enabled = dnc_allJobs.enabled = true
			)
			--ddl_jobsToDependOn.items = for i in SMTDSettings.dependencyJobItems collect SMTDSettings.JobsArray[i]

			local theRange = #()
			dnc_jobsToDependOn.items.clear()
			local foreColor =  (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			for i in SMTDSettings.dependencyJobItems do
			(
				local li = dotNetObject "System.Windows.Forms.ListViewItem" currentJobsArray[i][2]
				li.foreColor = foreColor
				local subLi = li.SubItems.add currentJobsArray[i][1]
				subLi = li.SubItems.add currentJobsArray[i][7]
				subLi = li.SubItems.add currentJobsArray[i][3]
				subLi = li.SubItems.add currentJobsArray[i][4]
				subLi = li.SubItems.add currentJobsArray[i][5]
				subLi = li.SubItems.add currentJobsArray[i][6]
				append theRange li
			)
			dnc_jobsToDependOn.Items.AddRange theRange

			filterJobsList()

		)


		on ddl_filterUser selected itm do filterJobsList()
		on ddl_filterDept selected itm do filterJobsList()
		on ddl_filterGroup selected itm do filterJobsList()
		on ddl_filterStatus selected itm do filterJobsList()

		on btn_getJobs pressed do
		(
			SMTDFunctions.CollectJobs()
			updateDependencyDisplay()
		)

		fn getListViewSelection lv =
		(
			try
				(for i = 1 to lv.items.count where lv.items.item[i-1].Selected collect (i-1))
			catch
				#()
		)

		fn addToDependencyList =
		(
			local theSel = getListViewSelection dnc_allJobs
			local tempArray = for i in currentJobsArray collect i[2]
			for i in theSel do
			(
				theItem = findItem tempArray dnc_allJobs.items.Item[i].Text
				if theItem > 0 do SMTDSettings.dependencyJobItems[theItem] = true
			)
			updateDependencyDisplay()
			if dnc_jobsToDependOn.Items.count > 0 do
			(
				SMTDSettings.SubmitAsDependent = chk_SubmitAsDependent.state = true
				SMTD_MainRollout.Ui_report ("+Dependencies: List Populated, Submit Job As Dependent enabled.")
			)
		)

		fn removeFromDependencyList =
		(
			local theSel = getListViewSelection dnc_jobsToDependOn
			local tempArray = for i in currentJobsArray collect i[2]
			for i in theSel do
			(
				theItem = findItem tempArray dnc_jobsToDependOn.items.Item[i].Text
				if theItem > 0 do SMTDSettings.dependencyJobItems[theItem] = false
			)
			updateDependencyDisplay()
			if dnc_jobsToDependOn.Items.count == 0 do
			(
				SMTDSettings.SubmitAsDependent = chk_SubmitAsDependent.state = false
				SMTD_MainRollout.Ui_report ("+Dependencies: List Cleared, Submit Job As Dependent disabled.")
			)
		)

		on dnc_allJobs DoubleClick EventArgs do addToDependencyList()
		on dnc_jobsToDependOn doubleClick EventArgs do removeFromDependencyList()


		on btn_clearDependencyList pressed do
		(
			SMTDSettings.dependencyJobItems = #{}
			updateDependencyDisplay()
			SMTD_MainRollout.Ui_report ("+Dependencies: List Cleared, Submit Job As Dependent disabled.")
			SMTDSettings.SubmitAsDependent = chk_SubmitAsDependent.state = false
		)

		on edt_filterJobs changed txt do
		(
			filterJobsList()
		)

		on btn_clearFilterJobs pressed do
		(
			edt_filterJobs.text = ""
			filterJobsList()
		)

		on btn_filterMe pressed do
		(
			theIndex = findItem ddl_filterUser.items SMTDSettings.UserName
			if theIndex > 0 then ddl_filterUser.selection = theIndex
			filterJobsList()
		)

		on ddl_DependOnPreviousJobMode selected itm do
		(
			SMTDSettings.DependOnPreviousJobMode = #(#last,#previous,#custom)[itm]
			case SMTDSettings.DependOnPreviousJobMode of
			(
				default: SMTDSettings.dependencyJobItems = #{}
				#previous: SMTDSettings.dependencyJobItems = #{}
				#last:
				(
					if SMTDSettings.PreviousJobsArray.count > 0 then
						SMTDSettings.dependencyJobItems = #{1}
					else
						SMTDSettings.dependencyJobItems = #{}
				)
			)
			updateDependencyDisplay()
			local lastState = SMTDSettings.SubmitAsDependent
			SMTDSettings.SubmitAsDependent = chk_SubmitAsDependent.state = dnc_jobsToDependOn.items.count > 0
			if lastState != SMTDSettings.SubmitAsDependent do
			(
				if SMTDSettings.SubmitAsDependent == true then
					SMTD_MainRollout.Ui_report ("+Dependencies: List Populated, Submit Job As Dependent enabled.")
				else
					SMTD_MainRollout.Ui_report ("+Dependencies: List Cleared, Submit Job As Dependent disabled.")
			)
		)


		on chk_submitAsDependent changed state do
		(
			SMTDSettings.SubmitAsDependent = state
			SMTD_MainRollout.Ui_report ("+Job Options: Submit As Dependent set to [" + state as string + "]")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Job Dependencies"
			if not state do
			(
				if SMTDSettings.SubmitAsDependent then
				(
					theTitle += " [On]"
					case SMTDSettings.DependOnPreviousJobMode of
					(
						default: ""
						#last: theTitle += " [Last]"
						#previous: theTitle += " [Previous]"
						#custom: theTitle += " [Custom]"
					)
				)
				else
					theTitle += " [Off]"

			)
			SMTD_Dependencies.title = theTitle
		)

		on SMTD_Dependencies rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_Dependencies open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Adding Job Dependencies Rollout"

			local theBGColor = ((colorman.getcolor #window) as color)*255
			initDotNetControls dnc_jobsToDependOn (theBGColor+(color 0 10 0))
			initDotNetControls dnc_allJobs (theBGColor+(color 0 0 10))

			chk_submitAsDependent.state = SMTDSettings.SubmitAsDependent
			updateDependencyDisplay()

			ddl_DependOnPreviousJobMode.selection = findItem #(#last,#previous,#custom) SMTDSettings.DependOnPreviousJobMode

			updateRolloutTitle SMTD_Dependencies.open
		)

		on btn_help_submitAsDependent pressed do ShellLaunch (SMTD_HelpURL + "#job-tab") ""
		on btn_help_DependsOn pressed do ShellLaunch (SMTD_HelpURL + "#job-tab") ""
	)

	rollout SMTD_JobScheduling "Job Scheduling" rolledup:true
	(
		radiobuttons rad_scheduling labels:#("Disabled *","One Time Only *","Every") columns:1 align:#left offset:[0,-5]
		spinner spn_days offset:[50,-18] fieldwidth:30 type:#integer align:#left across:2 range:[1,365,1]
		label lbl_days "Day(s) *" offset:[-135,-18] align:#left
		spinner spn_month "Start Date - Month: " type:#integer across:3 align:#right fieldwidth:50 range:[1,12,1] offset:[115,-37]
		spinner spn_day "Day: " type:#integer align:#right fieldwidth:50 range:[1,31,1] offset:[54,-37]
		spinner spn_year "Year: " type:#integer align:#right fieldwidth:50 range:[2013,3000,2013] offset:[5,-37]

		spinner spn_hours "Start Time - Hours: " type:#integer across:2 align:#right fieldwidth:50 range:[0,23,0] offset:[130,-3]
		spinner spn_minutes "Minutes:" type:#integer align:#right fieldwidth:50 range:[0,59,0] offset:[4,-3]

		fn updateEnabled =
		(
			spn_month.enabled  = spn_day.enabled = spn_year.enabled = spn_hours.enabled = spn_minutes.enabled = rad_scheduling.state > 1
			spn_days.enabled = rad_scheduling.state > 2
			lbl_days.text = if spn_days.value == 1 then "Day *" else "Days *"

			local theMax = 31
			local theVal = spn_day.value
			local theMonth = spn_month.value
			if theMonth == 2 do
				if (spn_year.value/4) as float == (spn_year.value as float / 4) then theMax = 29 else theMax = 28
			if theMonth == 4 or theMonth == 6 or theMonth == 9 or theMonth == 11 do theMax = 30
			if theVal  > theMax do theVal = theMax
			spn_day.range = [1,theMax,theVal]
		)

		fn setDateTime =
		(
			theDay = spn_day.value as string
			if theDay.count == 1 do theDay = "0"+theDay
			theMonth = spn_month.value as string
			if theMonth.count == 1 do theMonth = "0"+theMonth
			theHH = spn_hours.value as string
			if theHH.count == 1 do theHH = "0" + theHH
			theMM = spn_minutes.value as string
			if theMM.count == 1 do theMM = "0" + theMM
			SMTDSettings.ScheduledStartDateTime =  theDay + "/" + theMonth + "/" + spn_year.value as string + " " + theHH+":"+theMM
		)

		on spn_days changed val do
		(
			updateEnabled()
			SMTDSettings.ScheduledDays = val
			setDateTime()
		)

		on rad_scheduling changed state do
		(
			SMTDSettings.ScheduledType = (#(#None,#Once,#Daily))[state]
			updateEnabled()
			setDateTime()
		)

		on spn_day changed val do
		(
			updateEnabled()
			setDateTime()
		)
		on spn_month changed val do
		(
			updateEnabled()
			setDateTime()
		)
		on spn_year changed val do
		(
			updateEnabled()
			setDateTime()
		)
		on spn_hours changed val do
		(
			updateEnabled()
			setDateTime()
		)
		on spn_minutes changed val do
		(
			updateEnabled()
			setDateTime()
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Job Scheduling"
			if not state do
			(
				case SMTDSettings.ScheduledType of
				(
					default: theTitle += " [Off]"
					#once: theTitle += " [Once]"
					#daily: theTitle += " [Every "+SMTDSettings.ScheduledDays as string+" Day"+(if SMTDSettings.ScheduledDays == 1 then "" else "s")+"]"
				)
				if SMTDSettings.ScheduledType != #none do theTitle += " [Start: "+SMTDSettings.ScheduledStartDateTime + "]"
			)
			SMTD_JobScheduling.title = theTitle
		)

		on SMTD_JobScheduling rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_JobScheduling open do
		(
			theIndex = findItem #(#None,#Once,#Daily) SMTDSettings.ScheduledType
			if theIndex == 0 do theIndex = 1
			rad_scheduling.state = theIndex
			spn_days.value = SMTDSettings.ScheduledDays
			theFS = filterString SMTDSettings.ScheduledStartDateTime "/ :"
			if theFS.count == 5 then
			(
				spn_day.value = theFS[1] as integer
				spn_month.value = theFS[2] as integer
				spn_year.value = theFS[3] as integer
				spn_hours.value = theFS[4] as integer
				spn_minutes.value = theFS[5] as integer
			)
			else
			(
				makeDir SMTDPaths.TempDir all:true
				tempFile = (SMTDPaths.TempDir+ "_TempDate.txt")
				deleteFile tempFile
				theFile = createFile tempFile
				format "Date\n" to:theFile
				close theFile
				theDate = getFileModDate tempFile
				deleteFile tempFile
				theFS = filterString theDate  "/ :"
				spn_day.value = theFS[2] as integer
				spn_month.value = theFS[1] as integer
				spn_year.value = theFS[3] as integer
				spn_hours.value = theFS[4] as integer
				if theFS[7] == "PM" and theFS[4] != "12" do spn_hours.value += 12
				if theFS[7] == "AM" and theFS[4] == "12" do spn_hours.value -= 12
				spn_minutes.value = theFS[5] as integer
			)

			updateEnabled()
			setDateTime()
			updateRolloutTitle SMTD_JobScheduling.open
		)
	)

	rollout SMTD_JobFailureDetection "Job Failure Detection" rolledup:true
	(
		local VSpacing = 18
		checkbox chk_OverrideJobFailureDetection "Override Job Error Limit *" pos:[5,5]
		spinner spn_FailureDetectionJobErrors " *" range:[0,10000,0] type:#integer fieldwidth:40 pos:[150,5]

		checkbox chk_OverrideTaskFailureDetection "Override Task Error Limit *" pos:[280,5]
		spinner spn_FailureDetectionTaskErrors " *" range:[0,10000,0] type:#integer fieldwidth:40 pos:[425,5]

		checkbox chk_SendJobErrorWarning "Send Warning For Job Errors *" pos:[5,5+VSpacing*1]

		on chk_OverrideJobFailureDetection changed state do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "OverrideJobFailureDetection" ( (SMTDSettings.OverrideJobFailureDetection = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Failure Detection: Override Job Error Limit set to [" + state as string + "]")
		)
		on spn_FailureDetectionJobErrors changed val do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "FailureDetectionJobErrors" ( (SMTDSettings.FailureDetectionJobErrors = val) as string)
			SMTD_MainRollout.Ui_report ("+Job Failure Detection: Job Error Limit set to [" + val as string + "]")
		)
		on chk_OverrideTaskFailureDetection changed state do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "OverrideTaskFailureDetection" ( (SMTDSettings.OverrideTaskFailureDetection = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Failure Detection: Override Task Error Limit set to [" + state as string + "]")
		)
		on spn_FailureDetectionTaskErrors changed val do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "FailureDetectionTaskErrors" ( (SMTDSettings.FailureDetectionTaskErrors = val) as string)
			SMTD_MainRollout.Ui_report ("+Job Failure Detection: Task Error Limit set to [" + val as string + "]")
		)
		on chk_SendJobErrorWarning changed state do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "SendJobErrorWarning" ( (SMTDSettings.SendJobErrorWarning = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Failure Detection: Send Warning For Job Errors set to [" + state as string + "]")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Job Failure Detection"
			if not state do
			(
				if SMTDSettings.OverrideJobFailureDetection do theTitle += " [Job Errors: "+SMTDSettings.FailureDetectionJobErrors as string+"]"
				if SMTDSettings.OverrideTaskFailureDetection do theTitle += " [Task Errors: "+SMTDSettings.FailureDetectionTaskErrors as string+"]"
				if SMTDSettings.SendJobErrorWarning do theTitle += " [Send Warnings]"
			)
			SMTD_JobFailureDetection.title = theTitle
		)

		on SMTD_JobFailureDetection rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_JobFailureDetection open do
		(
			chk_OverrideJobFailureDetection.state = SMTDSettings.OverrideJobFailureDetection
			spn_FailureDetectionJobErrors.value = SMTDSettings.FailureDetectionJobErrors
			chk_OverrideTaskFailureDetection.state = SMTDSettings.OverrideTaskFailureDetection
			spn_FailureDetectionTaskErrors.value = SMTDSettings.FailureDetectionTaskErrors
			chk_SendJobErrorWarning.state = SMTDSettings.SendJobErrorWarning

			chk_OverrideJobFailureDetection.caption = SMTDFunctions.getStickyCaption "JobSettings" "OverrideJobFailureDetection" "Override Job Error Limit "
			spn_FailureDetectionJobErrors.caption = SMTDFunctions.getStickyCaption "JobSettings" "FailureDetectionJobErrors" " "
			chk_OverrideTaskFailureDetection.caption = SMTDFunctions.getStickyCaption "JobSettings" "OverrideTaskFailureDetection" "Override Task Error Limit "
			spn_FailureDetectionTaskErrors.caption = SMTDFunctions.getStickyCaption "JobSettings" "FailureDetectionTaskErrors" " "
			chk_SendJobErrorWarning.caption = SMTDFunctions.getStickyCaption "JobSettings" "SendJobErrorWarning" "Send Warning For Job Errors "

			updateRolloutTitle SMTD_JobFailureDetection.open
		)
	)

	rollout SMTD_JobSubmission "Job Submission" rolledup:true
	(
		local stereoMapList = #(#center, #left, #right, #leftright, #all, #off)
		local cameraOrderMapList = #(#none, #lrc, #rlc, #clr, #crl, #lcr, #rcl)

		button btn_stereoCameraJobs "Stereo Camera Jobs:  " width:125 height:22 align:#left pos:[3,3] border:false
		dropdownlist ddl_stereoCameraJobs items:#("Center Eye Only",  "Left Eye Only", "Right Eye Only", "Left and Right Eye", "Left, Right and Center Eye", "Disable Stereo Submission") width:160 pos:[130,3]
		dropdownlist ddl_stereoCameraPrioritiesOrder items:#("Same Priority For All Stereo Jobs",  "Left > Right > Center", "Right > Left > Center", "Center > Left > Right", "Center > Right > Left","Left > Center > Right","Right > Center > Left") width:190 align:#right pos:[292,3]
		checkbox chk_RenderFramesPreviewJob "Render Preview Job First  " pos:[5,28]
		dropdownlist ddl_PreviewJobSecondJobMode items:#("Default","Dependent","Suspended","Depend+Susp.") pos:[160,25] width:100
		spinner spn_PreviewJobPriorityOffset "Priority+:  " range:[-100,100,0] type:#integer pos:[270,29] fieldwidth:35 align:#right
		spinner spn_PreviewJobFrameCount  "# Frames: " range:[2,100,3] type:#integer fieldwidth:35 pos:[382,29] align:#right

		fn updateTooltips =
		(
			local theTooltipText = "Drop-down list controls what Jobs to submit when the Viewport is set to a component of a Stereo Camera rig:\n\nLEFT/RIGHT/CENTER Camera Only - submits only the respective eye regardless of which of the 3 Cameras is active\n\nLEFT and RIGHT Cameras - submits both eyes regardless of which of the 3 Cameras is active\n\nLEFT, RIGHT and CENTER - submits all 3 Cameras regardless of which of them is active\n\nIf the Viewport is not set to a Stereo Camera component, the current view will be submitted regardless of this mode."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "StereoCameraMode" isList:ddl_stereoCameraJobs.items mapList:(for i in stereoMapList collect toLower(i as string)))
			btn_stereoCameraJobs.tooltip = theTooltipText
			try(ddl_stereoCameraJobs.tooltip = theTooltipText)catch()
			try(ddl_stereoCameraPrioritiesOrder.tooltip = "Modifies the Job Priorities of Stereo Camera jobs, allowing one eye to be processed with higher priority than the others.\n\nThe first Camera listed will be submitted with unmodified Priority.\n\nThe second Camera listed will have (Priority-1)\n\nThe third Camera listed will have (Priority-2)"+ (SMTDFunctions.getStickyTooltipText "JobSettings" "StereoCameraPriorityOrder" isList:ddl_stereoCameraPrioritiesOrder.items mapList:(for i in cameraOrderMapList collect toLower(i as string))))catch()
			chk_RenderFramesPreviewJob.tooltip = "When checked, two jobs will be submitted - a PREVIEW job with a fraction of the frames, and a REST job with all other frames.\n\nThe PREVIEW job can be submitted with slightly higher priority and will provide a glimpse into the final result.\n\nIf its output looks incorrect, you can suspend the REST job before wasting render time rendering a wrong submission."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "RenderFramesPreviewJob")
			try(ddl_PreviewJobSecondJobMode.tooltip = "When set to Dependent, the [REST OF FRAMES] Job will be made dependent on the [PREVIEW FRAMES] Job.\n\nWhen set to Default, the [REST OF FRAMES] Job will use the same dependencies (none or custom) as the [PREVIEW FRAMES] Job.\n\nWhen set to Suspended, the [REST OF FRAMES] job will be suspended and must be resumed manually.")catch()

			spn_PreviewJobPriorityOffset.tooltip = "Defines the Priority Increase for the PREVIEW job.\n\nFor example if the Job Priority is set to 50 and this value is +5, the PREVIEW job will be submitted with Priority of 55 and the REST job with 50."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "PreviewJobPriorityOffset")
			spn_PreviewJobFrameCount.tooltip = "Defines the number of frames to be submitted as a PREVIEW job.\n\nThe frames will be taken at equal intervals, for example a value of 2 will send the first and last frames, a value of 3 will send first, middle and last and so on."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "PreviewJobFrameCount")
		)

		on ddl_stereoCameraJobs selected itm do
		(
			SMTDSettings.StereoCameraMode = stereoMapList[itm]
			setIniSetting SMTDPaths.InIFile "JobSettings"  "StereoCameraMode" SMTDSettings.StereoCameraMode
			SMTD_MainRollout.Ui_report ("+Job Options: Stereo Camera Jobs mode set to [" + SMTDSettings.StereoCameraMode+ ": " + ddl_stereoCameraJobs.selected + "]")
			updateTooltips()
		)

		on ddl_stereoCameraPrioritiesOrder selected itm do
		(
			SMTDSettings.StereoCameraPriorityOrder = cameraOrderMapList[itm]
			setIniSetting SMTDPaths.InIFile "JobSettings"  "StereoCameraPriorityOrder" SMTDSettings.StereoCameraPriorityOrder
			SMTD_MainRollout.Ui_report ("+Job Options: Stereo Camera Priority Order mode set to [" + SMTDSettings.StereoCameraPriorityOrder + ": " +ddl_stereoCameraPrioritiesOrder.selected + "]")
			updateTooltips()
		)

		on chk_RenderFramesPreviewJob changed state do
		(
			SMTDSettings.RenderFramesPreviewJob = state
			setIniSetting SMTDPaths.InIFile "JobSettings"  "RenderFramesPreviewJob" ( (SMTDSettings.RenderFramesPreviewJob = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Render Preview Job State set to [" + state as string + "].")
			ddl_PreviewJobSecondJobMode.enabled = spn_PreviewJobPriorityOffset.enabled = spn_PreviewJobFrameCount.enabled = state
			updateTooltips()
		)

		on spn_PreviewJobFrameCount changed value do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "PreviewJobFrameCount" ( (SMTDSettings.PreviewJobFrameCount = value) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Preview Job Frame Count set to [" + value as string + "]")
			updateTooltips()
		)

		on spn_PreviewJobPriorityOffset changed value do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "PreviewJobPriorityOffset" ( (SMTDSettings.PreviewJobPriorityOffset = value) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Preview Job Priority Offset set to [" + value as string + "]")
			updateTooltips()
		)

		on ddl_PreviewJobSecondJobMode selected itm do
		(
			case itm of
			(
				default: (SMTDSettings.PreviewJobSecondJobDependentOnFirst = SMTDSettings.PreviewJobSecondJobSuspended = false)
				2: (SMTDSettings.PreviewJobSecondJobDependentOnFirst = true; SMTDSettings.PreviewJobSecondJobSuspended = false)
				3: (SMTDSettings.PreviewJobSecondJobDependentOnFirst = false; SMTDSettings.PreviewJobSecondJobSuspended = true)
				4: (SMTDSettings.PreviewJobSecondJobDependentOnFirst = true; SMTDSettings.PreviewJobSecondJobSuspended = true)
			)
			setIniSetting SMTDPaths.InIFile "JobSettings"  "PreviewJobSecondJobDependentOnFirst" ( SMTDSettings.PreviewJobSecondJobDependentOnFirst as string)
			setIniSetting SMTDPaths.InIFile "JobSettings"  "PreviewJobSecondJobSuspended" ( SMTDSettings.PreviewJobSecondJobSuspended as string)

			SMTD_MainRollout.Ui_report ("+Job Options: Rest Of Frames Job Submission Mode set to [" + ddl_PreviewJobSecondJobMode.selected + "]")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Job Submission"
			if not state do
			(
				local theIndex = findItem stereoMapList SMTDSettings.StereoCameraMode
				if theIndex == 0 do theIndex = 1
				local camString = #("Center", "Left", "Right", "L+R", "All", "Off")[theIndex]
				theTitle+= " [Stereo: "+camString+"]"
				if SMTDSettings.RenderFramesPreviewJob	do theTitle+= " [Preview: "+SMTDSettings.PreviewJobFrameCount as string+"]"
				if SMTDSettings.SubmitVisibleObjectsOnly do theTitle+= " [Vis.Only]"
			)
			SMTD_JobSubmission.title = theTitle
		)

		on SMTD_JobSubmission rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_JobSubmission open do
		(
			local theIndex = findItem stereoMapList SMTDSettings.StereoCameraMode
			if theIndex == 0 do theIndex = 1
			ddl_stereoCameraJobs.selection = theIndex

			local theIndex = findItem cameraOrderMapList SMTDSettings.StereoCameraPriorityOrder
			if theIndex == 0 do theIndex = 1
			ddl_stereoCameraPrioritiesOrder.selection = theIndex


			chk_RenderFramesPreviewJob.state = SMTDSettings.RenderFramesPreviewJob
			spn_PreviewJobFrameCount.value = SMTDSettings.PreviewJobFrameCount
			spn_PreviewJobPriorityOffset.value = SMTDSettings.PreviewJobPriorityOffset
			ddl_PreviewJobSecondJobMode.selection = 1 + (if SMTDSettings.PreviewJobSecondJobDependentOnFirst then 1 else 0) + (if SMTDSettings.PreviewJobSecondJobSuspended then 2 else 0)

			btn_stereoCameraJobs.caption =  SMTDFunctions.getStickyCaption "JobSettings" "StereoCameraMode" "Stereo Camera Jobs:  "
			chk_RenderFramesPreviewJob.caption = SMTDFunctions.getStickyCaption "JobSettings" "RenderFramesPreviewJob" "Render Preview Job First  "
			spn_PreviewJobFrameCount.caption = SMTDFunctions.getStickyCaption "JobSettings" "PreviewJobFrameCount"  "# Frames: "
			spn_PreviewJobPriorityOffset.caption = SMTDFunctions.getStickyCaption "JobSettings" "PreviewJobPriorityOffset"  "Priority+:  "
			--chk_PreviewJobSecondJobDependentOnFirst.caption = SMTDFunctions.getStickyCaption "JobSettings" "PreviewJobSecondJobDependentOnFirst"  "Dependent  "

			ddl_PreviewJobSecondJobMode.enabled = spn_PreviewJobPriorityOffset.enabled = spn_PreviewJobFrameCount.enabled = SMTDSettings.RenderFramesPreviewJob
			updateTooltips()
			updateRolloutTitle SMTD_JobSubmission.open
		)
	)

	rcmenu printFrameSequenceToLogMenu
	(
		menuItem mnu_ToClipboard "Copy The File Sequence To The Windows CLIPBOARD"
		menuItem mnu_ToLog "Print The File Sequence To The LOG Window/File"

		on mnu_ToClipboard picked do SMTD_JobOptions.printFrameSequence mode:#clipboard
		on mnu_ToLog picked do SMTD_JobOptions.printFrameSequence mode:#log
	)

	rollout SMTD_JobOptions "Job Options"
	(
		local VSpacing = 21
		button btn_chunk "Task Chunk Size (Frames Per Task): " align:#left height:18 pos:[5,2] border:false across:4 --offset:[-112,3]
		spinner spn_chunkSize "" range:[1,1000,1] type:#integer align:#right fieldwidth:40 pos:[212,3]

		checkbox chk_limitEnabled "Limit: " pos:[320,2]
		spinner spn_machineLimit "Machines: " range:[1,1000,1] type:#integer align:#right fieldwidth:40 offset:[8,-4]

		dropdownlist ddl_OutOfOrderMethod items:#("First To Last (Forward)","Every Nth, Then Forward", "Every Nth - Block Fill","Every Nth - Half Raster Refine","Last To First (Reverse)","First And Last Frames First","From Both Ends","From Center","From Both Ends And From Center","Random") \
			height:20 width:210 align:#left pos:[5,2+VSpacing] across:3
		button btn_printFrameSequenceToLog  ">>" align:#center width:46 height:21 tooltip:"Opens a menu with options to Copy Frame Sequence to Windows Clipboard, or Print to the Log File."  offset:[-2,-1]
		spinner spn_outOfOrderStep "Out Of Order Step: " range:[2,1000,10] type:#integer align:#right fieldwidth:40 offset:[8,2]

		checkbox chk_TaskTimeoutEnabled "Task Timeout  " align:#left pos:[5,49] across:4
		spinner spn_task_timeout_hours "Hours:" type:#integer align:#right fieldwidth:40 range:[0,24,0] offset:[21,-2] tooltip:"Task Timeout HOURS"
		spinner spn_task_timeout_minutes "Minutes:" type:#integer align:#right fieldwidth:40 range:[0,59,0] offset:[10,-2] tooltip:"Task Timeout MINUTES"
		spinner spn_task_timeout_seconds "Seconds:" type:#integer align:#right fieldwidth:40 range:[0,59,0] offset:[7,-2] tooltip:"Task Timeout SECONDS"

		checkbox chk_autoTimeout "Enable Auto Task Timeout  " pos:[5,50+VSpacing] align:#left
		checkbox chk_restartMax "Restart 3ds Max Between Tasks  " pos:[300,50+VSpacing] align:#left
		checkbox chk_interruptible "Job Is Interruptible  " pos:[5,50+VSpacing*2] align:#left
		spinner spn_cpuThreads "Render Threads Per Task: " type:#integer align:#left fieldwidth:40 range:[0,32,0] pos:[300,50+VSpacing*2] tooltip:"The number of threads to use during rendering (specify 0 to use all processors available)"
		

		checkbox chk_forceWorkstationMode "Force Workstation Mode  " pos:[5,50+VSpacing*3] align:#left
		checkbox chk_useSilentMode "Enable Silent Mode  " pos:[300,50+VSpacing*3] align:#left

		button btn_concurrentTasks "Concurrent Tasks:  " width:115 height:20 border:false pos:[5,48+VSpacing*4]
		dropdownlist ddl_concurrentTasks "" items:#("None (1 Task)","2 Concurrent Tasks","3 Concurrent Tasks","4 Concurrent Tasks","5 Concurrent Tasks","6 Concurrent Tasks","7 Concurrent Tasks","8 Concurrent Tasks","9 Concurrent Tasks","10 Concurrent Tasks","11 Concurrent Tasks","12 Concurrent Tasks","13 Concurrent Tasks","14 Concurrent Tasks","15 Concurrent Tasks","16 Concurrent Tasks") \
			align:#right width:160 height:20 pos:[120,47+VSpacing*4]

		checkbox chk_limitConcurrentTasks "Limit Tasks To Slave's Task Limit  " align:#left pos:[300,50+VSpacing*4]

		button btn_onComplete "On Job Completion  " width:115 height:20 border:false pos:[5,48+VSpacing*5]
		dropdownlist ddl_onComplete items:#("Nothing", "Archive", "Delete") width:160 pos:[120,47+VSpacing*5]

		checkbox chk_submitAsSuspended "Submit Job As Suspended  " align:#left pos:[300,50+VSpacing*5]

		button btn_MaxVersionToForce "Force 3ds Max Build:" align:#left pos:[5,48+VSpacing*6] width:115 height:20 border:false
		dropdownlist ddl_MaxVersionToForce items:#("none", "32bit", "64bit") width:160 pos:[120,47+VSpacing*6]
		checkbox chk_EnforceSequentialRendering "Enforce Sequential Rendering  " pos:[300,50+VSpacing*6] align:#left

		--ROLLOUT FUNCTIONS--
		fn updateTooltips =
		(
			btn_chunk.tooltip = spn_chunkSize.tooltip = "Defines the number of Tasks (Frames) to be processed at once by a Slave." + (SMTDFunctions.getStickyTooltipText "JobSettings" "ChunkSize")
			chk_limitEnabled.tooltip = "When checked, only the number of Slaves specified by the Machines: value will be allowed to dequeue the job.\n\nWhen unchecked, any number of Slaves can work on the job."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "LimitEnabled")
			spn_machineLimit.tooltip = "Defines the number of Slaves that will be allowed to dequeue the job at the same time." + (SMTDFunctions.getStickyTooltipText "JobSettings" "MachineLimit")
			spn_outOfOrderStep.tooltip = "Defines the Nth frame step to use for the Task List Order settings.\n\nNOTE:\nThis does not let you render only every Nth frame.\nUse the 3ds Max Render Setup dialog\nto render only every Nth frame."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "OutOfOrderStep")

			chk_TaskTimeoutEnabled.tooltip = "When checked, a task will be requeued if it runs longer than the specified time.\n\nThis is useful when the typical rendering time of the job is known from previous submissions and will prevent stalling." + (SMTDFunctions.getStickyTooltipText "JobSettings" "TaskTimeoutEnabled")
			chk_autoTimeout.tooltip = "Enables the Auto Task Timeout option." + (SMTDFunctions.getStickyTooltipText "JobSettings" "AutoTaskTimeout")
			chk_restartMax.tooltip = "When unchecked (default), 3ds Max will be kept in memory for the duration of the give job's processing. This can reduce render time significantly as multiple Tasks can be rendered in sequence without reloading 3ds Max.\n\nWhen checked, 3ds Max will be restarted between tasks, thus releasing all memory and resetting the scene settings at cost of startup time."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "RestartMax")
			spn_cpuThreads.tooltip = "Defines the number of threads/CPUs that each task a slave will use (0=unlimited).\n\nThis can be useful if you are rendering a single threaded job, and you have set Concurrent Tasks to a value greater than 1. "+(SMTDFunctions.getStickyTooltipText "UserOptions" "RenderThreads")
			chk_EnforceSequentialRendering.tooltip = "When checked, the Tasks will be processed in ascending order in order to reduce the performance hit from History-Dependent calculations, for example from particle systems.\n\nWhen unchecked, Tasks can be picked up by Slaves in any order."+ (SMTDFunctions.getStickyTooltipText "JobSettings" "SequentialJob")
			chk_interruptible.tooltip = "When checked, the Job may be interrupted by any other Job that is assigned to the same Pool and has a higher Priority.\n\nUse with caution!"+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "JobIsInterruptible")
			try(ddl_OutOfOrderMethod.tooltip = "Defines the Order in which the Task List will be processed."+(SMTDFunctions.getStickyTooltipText "JobSettings" "OutOfOrderMethod"))catch()
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
			chk_forceWorkstationMode.tooltip = "When checked, 3ds Max will be launched in Workstation Mode using a license and full User Interface."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "ForceWorkstationMode")
			chk_useSilentMode.tooltip = "When checked, some 3ds Max pop-ups will be suppressed when running in Workstation Mode."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "UseSilentMode")
		)

		fn printFrameSequence mode:#clipboard =
		(
			renderSceneDialog.commit()
			local frames = "1"

			case rendTimeType of
			(
				1: (
					local frames = SMTDFunctions.GetSequenceString #(currentTime.frame as integer)
					case mode of
					(
						#clipboard: (setclipboardText frames)
						default: (
							SMTD_MainRollout.Ui_report (">SINGLE FRAME:")
							SMTD_MainRollout.Ui_report ( frames ) AddTimeStamp:false
						)
					)
				)
				2: (
					local currentSequence = for t in animationRange.start to animationRange.end by rendNthFrame collect (t.frame as integer)
					if SMTDSettings.RenderFramesPreviewJob then
					(
						currentSequence1 = SMTDFunctions.outOfOrderSequence currentSequence mode:#nth
						currentSequence1 = SMTDFunctions.outOfOrderMethod currentSequence1 theMethod:SMTDSettings.outOfOrderMethod
						currentSequence2 = SMTDFunctions.outOfOrderSequence currentSequence mode:#rest
						currentSequence2 = SMTDFunctions.outOfOrderMethod currentSequence2 theMethod:SMTDSettings.outOfOrderMethod
						local frames = SMTDFunctions.GetSequenceString currentSequence1
						local frames2 = SMTDFunctions.GetSequenceString currentSequence2
						case mode of
						(
							#clipboard: (
								setclipboardText (frames+"\n"+frames2)
							)
							default: (
								SMTD_MainRollout.Ui_report (">SCENE FRAME SEQUENCE - PREVIEW JOB:")
								SMTD_MainRollout.Ui_report ( frames ) AddTimeStamp:false
								SMTD_MainRollout.Ui_report (">SCENE FRAME SEQUENCE - SECONDARY JOB:")
								SMTD_MainRollout.Ui_report ( frames2 ) AddTimeStamp:false
							)
						)
					)
					else
					(
						currentSequence = SMTDFunctions.outOfOrderMethod currentSequence theMethod:SMTDSettings.outOfOrderMethod
						local frames = SMTDFunctions.GetSequenceString currentSequence
						case mode of
						(
							#clipboard: (setclipboardText frames)
							default:
							(
								SMTD_MainRollout.Ui_report (">SCENE FRAME SEQUENCE:")
								SMTD_MainRollout.Ui_report ( frames ) AddTimeStamp:false
							)
						)
					)
				)
				3: (
					local currentSequence = for t in rendStart to rendEnd by rendNthFrame collect (t.frame as integer)
					if SMTDSettings.RenderFramesPreviewJob then
					(
						currentSequence1 = SMTDFunctions.outOfOrderSequence currentSequence mode:#nth
						currentSequence1 = SMTDFunctions.outOfOrderMethod currentSequence1 theMethod:SMTDSettings.outOfOrderMethod
						currentSequence2 = SMTDFunctions.outOfOrderSequence currentSequence mode:#rest
						currentSequence2 = SMTDFunctions.outOfOrderMethod currentSequence2 theMethod:SMTDSettings.outOfOrderMethod
						local frames = SMTDFunctions.GetSequenceString currentSequence1
						local frames2 = SMTDFunctions.GetSequenceString currentSequence2
						case mode of
						(
							#clipboard: (
								setclipboardText (frames+"\n"+frames2)
							)
							default: (
								SMTD_MainRollout.Ui_report (">SCENE FRAME SEQUENCE - PREVIEW JOB:")
								SMTD_MainRollout.Ui_report ( frames ) AddTimeStamp:false
								SMTD_MainRollout.Ui_report (">SCENE FRAME SEQUENCE - SECONDARY JOB:")
								SMTD_MainRollout.Ui_report ( frames2 ) AddTimeStamp:false
							)
						)
					)
					else
					(
						currentSequence = SMTDFunctions.outOfOrderMethod currentSequence theMethod:SMTDSettings.outOfOrderMethod
						local frames = SMTDFunctions.GetSequenceString currentSequence
						case mode of
						(
							#clipboard: (setclipboardText frames)
							default:
							(
								SMTD_MainRollout.Ui_report (">CUSTOM FRAME SEQUENCE:")
								SMTD_MainRollout.Ui_report ( frames ) AddTimeStamp:false
							)
						)
					)
				)
				4: (
					local frames = rendPickupFrames
					case mode of
					(
						#clipboard: (setclipboardText frames)
						defaullt: (
							SMTD_MainRollout.Ui_report (">PICKUP FRAME SEQUENCE:")
							SMTD_MainRollout.Ui_report ( frames ) AddTimeStamp:false
						)
					)
				)
			)--end case
			--format "%\n" frames
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Job Options"
			if not state do
			(
				if spn_chunkSize.enabled do theTitle+= " [FPT: "+SMTDSettings.ChunkSize as string+"]"
				if SMTDSettings.LimitEnabled do theTitle+= " [Limit: "+SMTDSettings.MachineLimit as string+"]"
				if ddl_outOfOrderMethod.enabled do
					if SMTDSettings.OutOfOrderMethod != #normal do theTitle += " ["+SMTDSettings.OutOfOrderMethod as string+ (if matchPattern (SMTDSettings.OutOfOrderMethod as string) pattern:"*nth*" then " "+SMTDSettings.OutOfOrderStep as string else "") + "]"
				if SMTDSettings.TaskTimeoutEnabled do 	theTitle+= " [TTO]"
				if SMTDSettings.AutoTaskTimeout do theTitle+= " [ATTO]"
				if chk_EnforceSequentialRendering.enabled do
					if SMTDSettings.SequentialJob do theTitle+= " [Seq.]"
			)
			SMTD_JobOptions.title = theTitle
		)

		fn convertTimeoutToSeconds =
		(
			local theTime = #(spn_task_timeout_hours.value, spn_task_timeout_minutes.value, spn_task_timeout_seconds.value )
			local theVal = theTime[1] * 3600 + theTime[2] * 60 + theTime[3]
			setIniSetting SMTDPaths.InIFile "JobSettings"  "TaskTimeout" ( (SMTDSettings.TaskTimeout = theVal ) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Task Timeout set to " + theVal as string + " seconds or " + theTime[1] as string + " hour" + (if theTime[1] == 1 then ", " else "s, ") + theTime[2] as string + " minute"+(if theTime[2] == 1 then ", and " else "s, and ") + theTime[3] as string + " second" + (if theTime[3] == 1 then "." else "s."))
		)

		--EVENT HANDLERS--
		on btn_printFrameSequenceToLog pressed do
		(
			popupmenu printFrameSequenceToLogMenu pos:mouse.screenpos
		)

		on SMTD_JobOptions rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_JobOptions open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening Job Options Rollout"

			--RESTORE UI VALUES FROM STRUCT
			spn_chunkSize.value = SMTDSettings.ChunkSize
			chk_limitEnabled.state = SMTDSettings.LimitEnabled
			spn_machineLimit.value = SMTDSettings.MachineLimit

			spn_outOfOrderStep.value = SMTDSettings.OutOfOrderStep
			local theVal = findItem #(#normal, #nth, #NthBlock, #NthRasterRefine, #reverse, #lastAndFirst, #fromBothEnds, #FromCenter, #fromBothEndsAndCenter, #random) SMTDSettings.OutOfOrderMethod
			if theVal == 0 do theVal = 1
			ddl_outOfOrderMethod.selection = theVal

			ddl_concurrentTasks.selection = SMTDSettings.MaxTasksPerSlave
			chk_limitConcurrentTasks.state = SMTDSettings.LimitTasksToNumberOfCpus

			chk_submitAsSuspended.state = SMTDSettings.SubmitAsSuspended
			chk_EnforceSequentialRendering.state = SMTDSettings.SequentialJob

			chk_TaskTimeoutEnabled.state = SMTDSettings.TaskTimeoutEnabled
			chk_autoTimeout.state = SMTDSettings.AutoTaskTimeout
			chk_restartMax.state = SMTDSettings.RestartMax
			local theHours= (floor (SMTDSettings.TaskTimeout / 3600.0)) as integer

			spn_task_timeout_hours.value = theHours
			local theMinutes = (floor ((SMTDSettings.TaskTimeout - theHours*3600) / 60.0)) as integer
			spn_task_timeout_minutes.value = theMinutes
			local theSeconds = (SMTDSettings.TaskTimeout - theHours*3600 - theMinutes*60)
			spn_task_timeout_seconds.value = theSeconds

			chk_forceWorkstationMode.checked = SMTDSettings.ForceWorkstationMode
			chk_useSilentMode.checked = SMTDSettings.UseSilentMode
			chk_useSilentMode.enabled = chk_forceWorkstationMode.checked

			local versionVal = findItem #("none", "32bit", "64bit") SMTDSettings.MaxVersionToForce
			if versionVal == 0 do versionVal = 1
			ddl_MaxVersionToForce.selection = versionVal

			local onCompleteVal = findItem #("Nothing", "Archive", "Delete") SMTDSettings.OnComplete
			if onCompleteVal == 0 do onCompleteVal = 1
			ddl_onComplete.selection = onCompleteVal

			spn_cpuThreads.value = SMTDSettings.RenderThreads
			chk_interruptible.checked = SMTDSettings.JobIsInterruptible

			--ENABLE/DISABLE UI CONTROLS
			spn_machineLimit.enabled = SMTDSettings.LimitEnabled
			spn_outOfOrderStep.enabled = ddl_OutOfOrderMethod.selection >= 2 AND ddl_OutOfOrderMethod.selection <= 4

			btn_MaxVersionToForce.enabled = ddl_MaxVersionToForce.enabled = (maxVersion())[1] > 8000
			spn_task_timeout_hours.enabled = spn_task_timeout_minutes.enabled  = spn_task_timeout_seconds.enabled = chk_TaskTimeoutEnabled.checked

			--SHOW NON-STICKY SETTINGS
			btn_chunk.caption = SMTDFunctions.getStickyCaption "JobSettings" "ChunkSize" "Task Chunk Size (Frames Per Task): "
			chk_limitEnabled.caption = SMTDFunctions.getStickyCaption "JobSettings" "LimitEnabled" "Limit  "
			spn_MachineLimit.caption = SMTDFunctions.getStickyCaption "JobSettings" "MachineLimit" "Machines: "

			chk_TaskTimeoutEnabled.caption = SMTDFunctions.getStickyCaption "JobSettings" "TaskTimeoutEnabled" "Task Timeout:  "
			chk_autoTimeout.caption = SMTDFunctions.getStickyCaption "JobSettings" "AutoTaskTimeout" "Enable Auto Task Timeout  "
			chk_restartMax.caption = SMTDFunctions.getStickyCaption "JobSettings" "RestartMax" "Restart 3ds Max Between Tasks  "

			spn_outOfOrderStep.caption = SMTDFunctions.getStickyCaption "JobSettings" "OutOfOrderStep"  "Out Of Order Step: "
			chk_EnforceSequentialRendering.caption = SMTDFunctions.getStickyCaption "JobSettings" "SequentialJob" "Enforce Sequential Rendering  "
			chk_submitAsSuspended.caption  = SMTDFunctions.getStickyCaption "JobSettings" "SubmitAsSuspended" "Submit Job As Suspended  "
			btn_onComplete.caption  = SMTDFunctions.getStickyCaption "JobSettings" "OnComplete" "On Job Completion:  "
			btn_concurrentTasks.caption = SMTDFunctions.getStickyCaption "JobSettings" "MaxTasksPerSlave" "Concurrent Tasks:  "
			chk_limitConcurrentTasks.caption = SMTDFunctions.getStickyCaption "JobSettings" "LimitTasksToNumberOfCpus" "Limit Tasks To Slave's Task Limit  "
			chk_interruptible.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "JobIsInterruptible"  "Job Is Interruptible  "
			btn_MaxVersionToForce.caption = SMTDFunctions.getStickyCaption "JobSettings" "MaxVersionToForce" "Force 3ds Max Build:  "

			chk_forceWorkstationMode.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "ForceWorkstationMode"  "Force Workstation Mode  "
			chk_useSilentMode.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "UseSilentMode" "Enable Silent Mode  "

			btn_printFrameSequenceToLog.images = #(twoArrowsIconBitmap,twoArrowsIconMask,2,1,1,2,2)

			updateTooltips()
			updateRolloutTitle SMTD_JobOptions.open
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

		on spn_chunkSize changed value do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "ChunkSize" ( (SMTDSettings.ChunkSize = value) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Chunk Size set to [" + value as string + "]")
			updateTooltips()
			SMTD_MainRollout.updateSubmitButtonState()
		)

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

		on spn_outOfOrderStep changed value do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "OutOfOrderStep" ( (SMTDSettings.OutOfOrderStep = value) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Out Of Order Step Value set to [" + value as string + "]")
			updateTooltips()
		)

		on chk_EnforceSequentialRendering changed state do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "SequentialJob" (( SMTDSettings.SequentialJob = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Enforce Sequenctial Rendering set to [" + state as string + "]")
			updateTooltips()
		)

		on ddl_outOfOrderMethod selected itm do
		(
			local theMethod= case itm of
			(
				1: #normal
				2: #nth
				3: #NthBlock
				4: #NthRasterRefine
				5: #reverse
				6: #lastAndFirst
				7: #fromBothEnds
				8: #fromCenter
				9: #fromBothEndsAndCenter
				10: #random
			)
			setIniSetting SMTDPaths.InIFile "JobSettings"  "OutOfOrderMethod" ( (SMTDSettings.OutOfOrderMethod = theMethod) as string)
			spn_outOfOrderStep.enabled = itm >= 2 AND itm <= 4
			SMTD_MainRollout.Ui_report ("+Job Options: Out Of Order Method set to [" + ddl_outOfOrderMethod.selected + "]")
			updateTooltips()
		)

		on chk_limitConcurrentTasks changed state do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "LimitTasksToNumberOfCpus" ( (SMTDSettings.LimitTasksToNumberOfCpus = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Limit Tasks To Slave's Task Limit set to [" + state as string + "]")
			updateTooltips()
		)

		on spn_cpuThreads changed value do
		(
			SMTD_MainRollout.Ui_report ("+Job Options: Render Threads set to [" + value as string + "].")
			setIniSetting SMTDPaths.InIFile "UserOptions"  "RenderThreads" ( (SMTDSettings.RenderThreads = value) as string)
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

		on chk_forceWorkstationMode changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "ForceWorkstationMode" ((SMTDSettings.ForceWorkstationMode = state) as string)
			chk_useSilentMode.enabled = chk_forceWorkstationMode.checked
			SMTD_MainRollout.Ui_report ("+Rendering: Force Workstation Mode set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_useSilentMode changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "UseSilentMode" ((SMTDSettings.UseSilentMode = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Enable Silent Mode set to [" + state as string + "].")
			updateTooltips()
		)

	)--end JobScheduling rollout

	rollout SMTD_DBR "V-Ray/mental ray/Corona DBR" rolledup:true
	(
		checkbox chk_dbr "V-Ray/mental ray/Corona DBR (Off-Load)* " pos:[5,3] align:#left tooltip:"Check to offload a V-Ray, Mental Ray or Corona DBR render to Deadline."
		spinner spn_dbrServers "Slaves: " range:[1,999,2] type:#integer fieldwidth:30 pos:[260,3] align:#left tooltip:"Number of V-Ray Spawners to run via Deadline Slave."
		checkbox chk_dbr_3dsCmd "Use 3dsCmd Plugin  " pos:[360,3] align:#left tooltip:"When checked, the job will be submitted to the 3dsCmd plugin to avoid using a 3dsMax workstation license for the Master Slave."
		label void_001 "" height:2

		local theSlaveInfoFile = (SMTDPaths.SettingsDir + "slaveselectionsets\\slavesinfo.ini" )
		local theSelSetFiles = #()
		checkbox chk_blacklistSticky "Sticky Blacklist Settings" align:#left height:18 offset:[-10,-3] across:4 tooltip:"When checked, the Master Blacklist/Whitelist settings specified in this dialog will be stored between sessions and will be applied each time the SMTD Dialog is opened.\n\nWhen unchecked, the settings will have to be specified manually in each new SMTD session."

		button btn_saveSelSet "Save List As Selection Set"  align:#right width:137 height:18 offset:[147,-3] tooltip:"Enter a name in the text field below and press this button to save the right-hand-side list of Master Slaves as a named preset.\n\nIt can be restored easily by selecting from the drop-down list on the left side, or cleared by selecting the [None] entry."
		button btn_deleteSelSet "Delete"  align:#right width:45 height:18 offset:[78,-3] tooltip:"Select a Slave Selection Set from the drop-down list on the left or enter the name in the text field, then press this button to DELETE the named Selection Set from Disk."
		button btn_exploreSelSet "Explore"  align:#right width:45 height:18 offset:[9,-3] tooltip:"Press to EXPLORE the Selection Sets Folder"

		dropdownlist ddl_slaveSelSet width:230 align:#left across:2 offset:[-10,-5] tooltip:"Lists the previously saved Slave Selection Sets plus the [None] entry which cannot be removed.\n\nSelect a Slave Selection Set from the list to quickly populate the right-hand list with pre-defined machine names."
		edittext edt_SelSetName width:232 align:#right offset:[8,-3]

		label lbl_leftList "  " align:#left offset:[-7,-3] across:2
		label lbl_rightList " " align:#left offset:[15,-3]
		dotNetControl dnc_slavesList "ListView" width:230 height:160 align:#left offset:[-10,-3] across:2
		dotNetControl dnc_masterList "ListView" width:230 height:160 align:#right offset:[10,-3]

		button btn_selectAllSlaves "Select ALL" width:114 align:#left across:4 height:18 offset:[-9,-3] tooltip:"Select All Slaves in the left list."
		button btn_selectInvertSlaves "INVERT Selection" width:114 align:#left offset:[-9,-3] height:18 tooltip:"Invert Current Selection."
		button btn_selectAllList "Select ALL" width:114 align:#right offset:[10,-3] height:18 tooltip:"Select All Slaves in the right list."
		button btn_selectInvertList "INVERT Selection" width:114 align:#right height:18 offset:[10,-3] tooltip:"Invert Current Selection."

		edittext edt_filter "" text:"" across:4 align:#left offset:[-13,-3] fieldwidth:114
		button btn_update "UPDATE Slaves Info"  align:#left width:114 height:18 offset:[-9,-3] tooltip:"Reloads the Slave Names and Info from the Repository."

		radiobuttons rad_blackList labels:#("Blacklist","Whitelist") offset:[25,-3] align:#right columns:2 tooltip:"Controls whether the right list will be used as a Blacklist or Whitelist.\n\nWhen set to Blacklist, the machines listed on the right side will be excluded from rendering the submitted job, while the machines listed on the left will be allowed to work on it.\n\nWhen set to Whitelist, the machines listed on the right will be allowed to work on the job and the ones on the left will not."

		button btn_moveToList ">>" width:20 offset:[-171,-185] height:72 tooltip:"Move selected Slaves to the right list" images:#(oneArrowIconBitmap,oneArrowIconMask,2,1,1,2,2)
		button btn_moveToSlaves "<<" width:20 offset:[0,-125] height:72 tooltip:"Move selected Slaves back to the left list." images:#(oneArrowIconReverseBitmap,oneArrowIconReverseMask,2,1,1,2,2)

		fn initDotNetControl lv foreColor BgColor =
		(
			local layout_def = #(#("Slave Name",150), #("Status",55) )
			lv.Clear()
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB BgColor.r BgColor.g BgColor.b
			lv.foreColor = (dotNetClass "System.Drawing.Color").fromARGB foreColor.r foreColor.g foreColor.b
			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.gridLines = true
			lv.fullRowSelect = true
			lv.checkboxes = false
			lv.hideSelection = false
			--lv.HeaderStyle = lv.HeaderStyle.None
			for i in layout_def do lv.Columns.add i[1] i[2]
		)

		fn populateDotNetControl lv theList =
		(
			local theRange = #()
			lv.Items.clear()
			local offlineColor = (dotNetClass "System.Drawing.Color").fromARGB 150 150 150
			local idleColor = (dotNetClass "System.Drawing.Color").fromARGB 50 150 255
			local renderColor = (dotNetClass "System.Drawing.Color").fromARGB 0 200 50
			local stalledColor = (dotNetClass "System.Drawing.Color").fromARGB 255 50 50
			local startingColor = (dotNetClass "System.Drawing.Color").fromARGB 200 100 50

			for i in theList do
			(
				local li = dotNetObject "System.Windows.Forms.ListViewItem" i
				local theState = (getIniSetting theSlaveInfoFile i "SlaveStatus")
				local subLi = li.SubItems.add theState
				case theState of
				(
					"Offline": li.forecolor = offlineColor
					"Rendering": (li.forecolor = renderColor; subLi.text = "Render")
					"Idle": li.forecolor = idleColor
					"Stalled": li.forecolor = stalledColor
					default: li.forecolor = startingColor
				)
				append theRange li
			)
			lv.Items.AddRange theRange
		)

		fn storeSlaveList =
		(
			local theListString = "#("
			if SMTDSettings.MastersList.count > 0 do
			(
				for i = 1 to SMTDSettings.MastersList.count-1 do theListString += "\"" + SMTDSettings.MastersList[i] + "\","
				theListString += "\"" + SMTDSettings.MastersList[SMTDSettings.MastersList.count]
			)
			theListString += "\")"
			setIniSetting SMTDPaths.InIFile "Masters" "MastersList" theListString
		)

		fn storeNamedSelectionSet =
		(
			setIniSetting SMTDPaths.InIFile "Masters" "MastersNamedSet" (SMTDSettings.MastersNamedSet )
			SMTD_MainRollout.Ui_report ("+Masters: Named Slaves Selection set to [" + SMTDSettings.MastersNamedSet + "]")
		)

		fn populateSlavelists =
		(
			local List1 = for i in (sort SMTDSettings.Slaves) where findItem SMTDSettings.MastersList i == 0 collect i
			local List2 = for i in (sort SMTDSettings.MastersList) collect i
			populateDotNetControl dnc_slavesList List1
			populateDotNetControl dnc_masterList List2
			storeSlaveList()
		)

		fn updateSlaveList forceUpdate:false=
		(
			if SMTDSettings.Slaves.count == 0 or forceUpdate do
			(
				SMTDFunctions.CollectSlaves()
			)

			local BgColor1 = color 255 255 255
			local foreColor1 = color 50 50 50
			local BgColor2 = color 50 50 50
			local foreColor2 = color 255 255 255
			if not SMTDSettings.MastersBlackList then
			(
				BgColor1 = color 50 50 50
				foreColor1 = color 255 255 255
				BgColor2 = color 255 255 255
				foreColor2 = color 50 50 50
			)
			initDotNetControl dnc_slavesList foreColor1 BgColor1
			initDotNetControl dnc_masterList foreColor2 BgColor2

			populateSlavelists()
		)

		fn updateSelectionSetList =
		(
			local thePath = (SMTDPaths.SettingsDir + "slaveselectionsets")
			makeDir SMTDPaths.SettingsDir
			makeDir thePath
			theSelSetFiles = getFiles (thePath + "\\*.slaves")
			ddl_slaveSelSet.items = join #("[None]") (for f in theSelSetFiles collect getFileNameFile f)
			theIndex = findItem ddl_slaveSelSet.items SMTDSettings.MastersNamedSet
			if theIndex == 0 do theIndex = 1
			ddl_slaveSelSet.selection = theIndex
		)

		fn updateWhiteBlackListCaption =
		(
			case rad_blackList.state of
			(
				1:
				(
					lbl_leftList.caption = "Whitelisted Slaves (May Become Masters):"
					lbl_rightList.caption = "Blacklisted Slaves (Will Never Be Masters):"
				)
				2:
				(
					lbl_leftList.caption = "Blacklisted Slaves (Will Never Be Masters):"
					lbl_rightList.caption = "Whitelisted Slaves (May Become Masters):"
				)
			)

		)

		on chk_blacklistSticky changed state do
		(
			setIniSetting SMTDPaths.InIFile "Masters"  "MastersSettingsSticky"  ((SMTDSettings.MastersSettingsSticky = state) as string)
			SMTD_MainRollout.Ui_report ("+Masters List: Make Settings Sticky set to [" + state as string + "]")
		)

		on rad_blackList changed val do
		(
			setIniSetting SMTDPaths.InIFile "Masters"  "BlackOrWhite" ( (SMTDSettings.MastersBlackList = (val == 1) ) as string)
			SMTD_MainRollout.Ui_report ("+Masters: Mode set to [" + #("Blacklist","Whitelist")[val] + "]")
			updateWhiteBlackListCaption()
			updateSlaveList()
		)

		fn getListViewSelection lv =	--returns an array of the selected ListView items
		(
			try
				for i = 1 to lv.items.count where lv.items.item[i-1].Selected collect i
			catch
				#()
		)

		fn setListViewSelection lv theSel =
		(
			for i = 1 to lv.items.count do lv.items.item[i-1].Selected = theSel[i]
		)

		on btn_selectAllSlaves pressed do
		(
			setListViewSelection dnc_slavesList #{1..dnc_slavesList.Items.Count}
		)

		on btn_selectInvertSlaves pressed do
		(
			local theSel = (getListViewSelection dnc_slavesList) as bitarray
			setListViewSelection dnc_slavesList (#{1..dnc_slavesList.Items.Count}-theSel)
		)

		on btn_selectAllList pressed do
		(
			setListViewSelection dnc_masterList #{1..dnc_masterList.Items.Count}
		)

		on btn_selectInvertList pressed do
		(
			local theSel = (getListViewSelection dnc_masterList) as bitarray
			setListViewSelection dnc_masterList (#{1..dnc_masterList.Items.Count}-theSel)
		)

		on edt_filter changed txt do
		(
			if txt != "" then
			(
				local theSel = (for i = 1 to dnc_slavesList.items.count where matchPattern dnc_slavesList.items.item[i-1].text pattern:(txt+"*") collect i) as bitarray
				setListViewSelection dnc_slavesList theSel
			)
			else
				setListViewSelection dnc_slavesList #{}
		)

		on btn_update pressed do
		(
			SMTDFunctions.CollectSlavesInfo()
			updateSlaveList forceUpdate:true
		)

		on btn_moveToList pressed do
		(
			local theSel = getListViewSelection dnc_slavesList
			local tempArray = deepCopy SMTDSettings.MastersList
			--local tempArray = for i = 1 to dnc_masterList.items.count collect dnc_masterList.items.item[i-1].text
			local tempArray2 = (for i in theSel collect dnc_slavesList.items.item[i-1].text)
			join tempArray tempArray2
			sort tempArray
			SMTDSettings.MastersList = deepCopy tempArray
			populateSlavelists()
			theSel = for i in tempArray2 collect (theIndex = findItem tempArray i; if theIndex > 0 then theIndex else dontcollect)
			setListViewSelection dnc_masterList (theSel as bitarray)
		)

		on btn_moveToSlaves pressed do
		(
			local theSel = getListViewSelection dnc_masterList
			local tempArray = deepCopy SMTDSettings.MastersList
			local tempArray2 = for i in theSel collect SMTDSettings.MastersList[i]
			for i = theSel.count to 1 by -1 do deleteItem tempArray theSel[i]
			SMTDSettings.MastersList = deepCopy tempArray
			populateSlavelists()
			local tempArray3 = for i = 1 to dnc_slavesList.items.count collect dnc_slavesList.items.item[i-1].text
			theSel = for i in tempArray2 collect (theIndex = findItem tempArray3 i; if theIndex > 0 then theIndex else dontcollect)
			setListViewSelection dnc_slavesList (theSel as bitarray)
		)

		on dnc_slavesList DoubleClick EventArgs do btn_moveToList.pressed()
		on dnc_masterList DoubleClick EventArgs do btn_moveToSlaves.pressed()

		on btn_saveSelSet pressed do
		(
			if edt_SelSetName.text != "" then
			(
				local theFileName = (SMTDPaths.SettingsDir + "slaveselectionsets\\" + edt_SelSetName.text + ".slaves" )
				if doesFileExist theFileName then
					SMTD_MainRollout.Ui_report ("+Masters List: Updated Slaves Selection Set [" + edt_SelSetName.text + "]." )
				else
					SMTD_MainRollout.Ui_report ("+Masters List: Created Slaves Selection Set [" + edt_SelSetName.text + "]." )

				local theFile = createFile theFileName encoding:#utf8 writeBOM:true
				if theFile != undefined then
				(
					tempArray = SMTDSettings.MastersList
					for i in tempArray do
						format "%\n" i to:theFile
					close theFile
					SMTDSettings.MastersNamedSet = edt_SelSetName.text
					storeNamedSelectionSet()
					--edt_SelSetName.text = ""
					updateSelectionSetList()
				)
			)
			else
				SMTD_MainRollout.Ui_report ("--Masters List: Could NOT Save - No Name for the Slaves Selection Set specified.")
		)

		on btn_exploreSelSet pressed do
		(
			shellLaunch "explorer.exe" (SMTDPaths.SettingsDir + "slaveselectionsets\\")
		)


		on btn_deleteSelSet pressed do
		(
			if edt_SelSetName.text != "" then
			(
				local theFileName = (SMTDPaths.SettingsDir + "slaveselectionsets\\" + edt_SelSetName.text + ".slaves" )
				if doesFileExist theFileName then
				(
					local q = querybox ("Delete Slaves Selection Set ["+edt_SelSetName.text+"]?\nIf you click Yes, a Backup of the Selection Set will be created.\nYou can restore the Selection Set by pressing [E] to Explore the folder\nand by removing the .BAK Extension manually.") title:"Delete Masters Selection Set"
					if q then
					(
						if doesFileExist (theFileName+".bak") do deleteFile (theFileName+".bak")
						renameFile theFileName (theFileName+".bak")
						SMTD_MainRollout.Ui_report ("+Masters Black/Whitelist: Removed Slaves Selection Set [" + edt_SelSetName.text + "]. Backup File Created." )
						updateSelectionSetList()
						edt_SelSetName.text = ""
					)
				)
				else
					SMTD_MainRollout.Ui_report ("+Masters Black/Whitelist: Could NOT Remove Slaves Selection Set [" + edt_SelSetName.text + "] - No Such List!" )
			)
		)

		on ddl_slaveSelSet selected itm do
		(
			if itm > 1 then
			(
				local theFileName = theSelSetFiles[itm-1]
				local theFile = openFile theFileName
				local theArray = #()
				while not eof theFile do
					append theArray (readline theFile)
				close theFile
				SMTDSettings.MastersList = deepCopy theArray
				populateSlavelists()
			)
			else
			(
				SMTDSettings.MastersList = #()
				populateSlavelists()
				--mlb_blackList.items = #()
				--mlb_slavesList.items = for i in (sort SMTDSettings.Slaves) collect i
			)
			edt_SelSetName.text = SMTDSettings.MastersNamedSet = ddl_slaveSelSet.selected
			storeNamedSelectionSet()
			if itm == 1 then edt_SelSetName.text = ""
			storeSlaveList()
		)

		on chk_dbr changed state do
		(
			SMTDSettings.DBR = state

			spn_dbrServers.enabled = state
			cmdEnabled = state
			local rendererID = SMTDFunctions.getRendererIdString()
			if rendererID == "corona" do
				cmdEnabled = false

			chk_dbr_3dsCmd.enabled = cmdEnabled
			SMTD_MainRollout.Ui_report ("+Rendering: DBR (off-load) option set to [" + state as string + "]")
		)

		on spn_dbrServers changed val do
		(
			setIniSetting SMTDPaths.InIFile "DBROptions"  "DBRServers" ((SMTDSettings.DBRServers = val) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: DBR (off-load) Slaves option set to [" + val as string + "]")
		)

		on chk_dbr_3dsCmd changed state do
		(
			SMTDSettings.DBRUse3dsCmd = state
			setIniSetting SMTDPaths.IniFile "DBROptions"  "DBRUse3dsCmd" ((SMTDSettings.DBRUse3dsCmd = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: DBR (off-load) Use 3dsCmd Plugin option set to [" + state as string + "]")
		)


		fn updateRolloutTitle state =
		(
			local theTitle = "V-Ray/mental ray/Corona DBR"
			if not state then
			(
				if chk_dbr.enabled then
				(
					if chk_dbr.state then
					(
						theTitle+= " [Off-Load] ["+spn_dbrServers.value  as string + " Slave"+(if spn_dbrServers.value==1 then "" else "s")+"]"
						if chk_dbr_3dsCmd.checked then theTitle+= " [Cmd]"
					)
					else
						theTitle+= " [Off]"
				)
				else
				(
					theTitle+= " [Disabled]"
				)
			)
			SMTD_DBR.title = theTitle
		)

		fn updateControls =
		(
			chk_dbr.checked = SMTDSettings.DBR
			spn_dbrServers.value = SMTDSettings.DBRServers
			spn_dbrServers.enabled = SMTDSettings.DBR
			chk_dbr_3dsCmd.checked = SMTDSettings.DBRUse3dsCmd
			chk_dbr_3dsCmd.enabled = SMTDSettings.DBR
			chk_dbr.enabled = true

			local enableDBR = true
			renderSceneDialog.commit()
			local rendererID = SMTDFunctions.getRendererIdString()
			if SMTDFunctions.getRendererSupportsDBROffload() then
			(
				if (rendererID == "mentalray") and not (renderers.current.DistributedEnable) do
					enableDBR = false
				if (rendererID == "vray") and not (renderers.current.system_distributedRender) do
					enableDBR = false
				if (rendererID == "vrayrt") and not (renderers.current.distributed_rendering) do
					enableDBR = false
				if (rendererID == "corona") do
				(
					if (renderers.current.dr_enable) then
					(
						chk_dbr_3dsCmd.checked = false
						chk_dbr_3dsCmd.enabled = false
						SMTDSettings.DBRUse3dsCmd = false
					)
					else
					(
						enableDBR = false
					)

				)
			)
			else
				enableDBR = false


			if not enableDBR do
			(
				SMTDSettings.DBR = false
				chk_dbr.enabled = false
				chk_dbr_3dsCmd.enabled = false
			)
		)

		on SMTD_DBR rolledup state do
		(
			updateControls()
			updateRolloutTitle state
			if state do
			(
				if SMTDSettings.SlaveInfoCollected == false do
				(
					SMTDFunctions.CollectSlavesInfo()
					SMTDSettings.SlaveInfoCollected = true
				)
				updateSlaveList()
			)
		)

		on SMTD_DBR open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening V-Ray/mental ray/Corona DBR Rollout"
			chk_blacklistSticky.state = SMTDSettings.MastersSettingsSticky
			rad_blackList.state = if SMTDSettings.MastersBlackList then 1 else 2
			updateSelectionSetList()
			updateWhiteBlackListCaption()
			updateControls()
			updateRolloutTitle SMTD_DBR.open
		)
	)

	rollout SMTD_ScenePreProcessing "Scene Tweaks" rolledup:false
	(
		local VOffset = 18
		local VOffset2 = 20
		local Column2 = 280

		checkbox chk_mergeXRefs "Merge Object XRefs  " pos:[5,5] align:#left
		checkbox chk_mergeSceneXRefs "Merge Scene XRefs  " pos:[Column2,5] align:#left

		checkbox chk_ClearMaterialEditorOnSubmission "Clear Material Editor In The Submitted File  " pos:[5,5+VOffset*1]
		checkbox chk_UnlockMaterialEditorRenderer "Unlock Material Editor Renderer  " pos:[Column2,5+VOffset*1]

		checkbox chk_useCustomShader "Apply Custom Material To Scene  " pos:[5,5+VOffset*2] align:#left
		dropdownlist ddl_CustomShaderMode items:#("Standard Grayscale Material","Object Wireframe Color","Layer Color","Material Editor Slot 1") width:200 pos:[Column2,2+VOffset*2] align:#left

		checkbox chk_DeleteEmptyStateSets "Delete Empty State Sets In The Submitted File  " pos:[5,5+VOffset*3]
		checkbox chk_OverrideLowPriorityThread "Override Renderer's Low Priority Thread Option (Brazil r/s, V-Ray)  " pos:[5,5+VOffset*4]

		fn updateTooltips =
		(
			chk_mergeXRefs.tooltip = "When checked, Object XRefs will be merged into the scene before it is saved for submission.\nThe scene will be restored to its original state after submission.\n\nIf unchecked, the XRefs will be retained and must be accessible to the Slave when rendering."  + (SMTDFunctions.getStickyTooltipText "RenderingOptions" "MergeXRefsOnSubmission")
			chk_mergeSceneXRefs.tooltip = "When checked, Scene XRefs will be merged into the scene before it is saved for submission.\nThe scene will be restored to its original state after submission.\n\nIf unchecked, the XRefs will be retained and must be accessible to the Slave when rendering." + (SMTDFunctions.getStickyTooltipText "RenderingOptions"  "MergeSceneXRefsOnSubmission")
			chk_ClearMaterialEditorOnSubmission.tooltip = "When checked, the Material Editor's Sample Spheres will be reset to a Default Standard Material to avoid problems in cases where missing classes might be present there but not in the scene.\n\nWhen unchecked, the Material Sample Spheres will be preserved in the submitted file." + (SMTDFunctions.getStickyTooltipText "UserOptions" "ClearMaterialEditorOnSubmission")
			chk_UnlockMaterialEditorRenderer.tooltip = "When checked, the Material Editor's Renderer will be unlocked to use the Default Scanline Renderer to avoid problems with some old versions of V-Ray.\n\nWhen unchecked, the Material Editor Lock Renderer option will be left untouched." + (SMTDFunctions.getStickyTooltipText "UserOptions" "UnlockMEditRenderer")
			chk_useCustomShader.tooltip = "When checked, a uniform custom material specified by the drop-down list to the right will be applied to all scene geometry." + (SMTDFunctions.getStickyTooltipText "RenderingOptions" "UseCustomShader")
			try(ddl_CustomShaderMode.tooltip = "Override the material of all scene geometry objects for quick test renders without textures and complex shading.\n\nSelect from a default gray, a Standard Material with diffuse color matching the object's Wireframe or Layer color, or the first Material Editor slot for custom material." + (SMTDFunctions.getStickyTooltipText "RenderingOptions" "CustomShaderMode"))catch()
			chk_DeleteEmptyStateSets.tooltip = "When checked, any empty State Sets will be deleted from the scene and the State Sets UI will be reset.\n\nThis fixes an ADSK bug when running 3dsMax as a service." + (SMTDFunctions.getStickyTooltipText "UserOptions" "DeleteEmptyStateSets")
			chk_OverrideLowPriorityThread.tooltip = "When checked, the Low Priority Thread option of V-Ray and Brazil r/s will be turned off to ensure full performance in Slave mode.\n\nWhen unchecked, the option will be left untouched, usefull for example if the Job will be running in the background on Workstations in use by artists." + (SMTDFunctions.getStickyTooltipText "UserOptions" "OverrideLowPriorityThread")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Scene Tweaks"
			if not state do
			(
				if SMTDSettings.MergeXRefsOnSubmission or SMTDSettings.MergeSceneXRefsOnSubmission do
				(
					theTitle+=" [Mrg:"
					if SMTDSettings.MergeXRefsOnSubmission do theTitle+= "OXRef"
					if SMTDSettings.MergeXRefsOnSubmission and SMTDSettings.MergeSceneXRefsOnSubmission do theTitle+=","
					if SMTDSettings.MergeSceneXRefsOnSubmission do theTitle+= "SXRef"
					theTitle+="]"
				)
				if SMTDSettings.UseCustomShader do
				(
					theTitle+=" [Mat:"
					theTitle+= case SMTDSettings.CustomShaderMode of
					(
						1: "Gray"
						2: "Wire"
						3: "Layer"
						4: "Slot1"
					)
					theTitle+="]"
				)
				if SMTDSettings.UnlockMEditRenderer or SMTDSettings.ClearMaterialEditorOnSubmission do
				(
					theTitle+=" [MEdit:"
					if SMTDSettings.ClearMaterialEditorOnSubmission do theTitle+="Clr"
					if SMTDSettings.UnlockMEditRenderer and SMTDSettings.ClearMaterialEditorOnSubmission do theTitle+=","
					if SMTDSettings.UnlockMEditRenderer do theTitle+="Unlock"
					theTitle+="]"
				)
				if SMTDSettings.DeleteEmptyStateSets do
				(
					theTitle+=" [Del.E.SS]"
				)
				if SMTDSettings.OverrideLowPriorityThread do
				(
					theTitle+=" [HiPriority]"
				)
			)
			SMTD_ScenePreProcessing.title = theTitle
		)

		--EVENT HANDLERS--
		on chk_mergeXRefs changed state do
		(
--			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "MergeXRefsOnSubmission" ((SMTDSettings.MergeXRefsOnSubmission = state) as string)
			SMTDSettings.MergeXRefsOnSubmission = state
			SMTD_MainRollout.Ui_report ("+Scene Tweaks: Merge XRefs On Submission set to [" + state as string + "]")
			updateTooltips()
		)

		on chk_mergeSceneXRefs changed state do
		(
			SMTDSettings.MergeSceneXRefsOnSubmission = state
			SMTD_MainRollout.Ui_report ("+Scene Tweaks: Merge Scene XRefs On Submission set to [" + state as string + "]")
			updateTooltips()
		)

		on chk_OverrideLowPriorityThread changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "OverrideLowPriorityThread" ( (SMTDSettings.OverrideLowPriorityThread = state) as string)
			SMTD_MainRollout.Ui_report ("+Scene Tweaks: Override Renderer's Low Priority Thread set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_ClearMaterialEditorOnSubmission changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ClearMaterialEditorOnSubmission" ( (SMTDSettings.ClearMaterialEditorOnSubmission = state) as string)
			SMTD_MainRollout.Ui_report ("+Scene Tweaks: Clear Material Editor In Submitted File set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_UnlockMaterialEditorRenderer changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "UnlockMEditRenderer" ( (SMTDSettings.UnlockMEditRenderer = state) as string)
			SMTD_MainRollout.Ui_report ("+Scene Tweaks: Unlock Material Editor set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_DeleteEmptyStateSets changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "DeleteEmptyStateSets" ( (SMTDSettings.DeleteEmptyStateSets = state) as string)
			SMTD_MainRollout.Ui_report ("+Scene Tweaks: Delete Empty States In Submitted File set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_useCustomShader changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "UseCustomShader " ( (SMTDSettings.UseCustomShader = state) as string)
			SMTD_MainRollout.Ui_report ("+Scene Tweaks: Apply Custom Material To Scene set to [" + state as string + "].")
			updateTooltips()
		)
		on ddl_CustomShaderMode selected itm do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "CustomShaderMode" ( (SMTDSettings.CustomShaderMode = itm) as string)
			SMTD_MainRollout.Ui_report ("+Scene Tweaks: Custom Material to be applied to scene set to [" + ddl_CustomShaderMode.selected + "] .")
			updateTooltips()
		)


		on SMTD_ScenePreProcessing rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_ScenePreProcessing open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening Scene Tweaks Rollout"

			chk_mergeXRefs.state = 							SMTDSettings.MergeXRefsOnSubmission
			chk_mergeSceneXRefs.state = 					SMTDSettings.MergeSceneXRefsOnSubmission
			chk_useCustomShader.state = 					SMTDSettings.UseCustomShader
			ddl_CustomShaderMode.selection = 			SMTDSettings.CustomShaderMode
			chk_OverrideLowPriorityThread.state =		SMTDSettings.OverrideLowPriorityThread
			chk_ClearMaterialEditorOnSubmission.state =SMTDSettings.ClearMaterialEditorOnSubmission
			chk_UnlockMaterialEditorRenderer.state = 	SMTDSettings.UnlockMEditRenderer
			chk_DeleteEmptyStateSets.state = 			SMTDSettings.DeleteEmptyStateSets

			chk_mergeXRefs.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "MergeXRefsOnSubmission" "Merge Object XRefs  "
			chk_mergeSceneXRefs.caption = SMTDFunctions.getStickyCaption "RenderingOptions"  "MergeSceneXRefsOnSubmission" "Merge Scene XRefs  "
			chk_useCustomShader.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "UseCustomShader"  "Apply Custom Material To Scene  "
			ddl_CustomShaderMode.items = if SMTDFunctions.IsSettingSticky "RenderingOptions" "CustomShaderMode" then
				#("Standard Grayscale Material","Object Wireframe Color","Layer Color","Material Editor Slot 1")
			else
				#("Standard Grayscale Material *","Object Wireframe Color *","Layer Color *","Material Editor Slot 1 *")

			chk_OverrideLowPriorityThread.caption = SMTDFunctions.getStickyCaption "UserOptions" "OverrideLowPriorityThread"  "Override Renderer's Low Priority Thread Option (Brazil r/s, V-Ray)  "
			chk_ClearMaterialEditorOnSubmission.caption = SMTDFunctions.getStickyCaption "UserOptions" "ClearMaterialEditorOnSubmission"  "Clear Material Editor In The Submitted File  "
			chk_UnlockMaterialEditorRenderer.caption = SMTDFunctions.getStickyCaption "UserOptions" "UnlockMEditRenderer"  "Unlock Material Editor Renderer  "
			chk_DeleteEmptyStateSets.caption = SMTDFunctions.getStickyCaption "UserOptions" "DeleteEmptyStateSets"  "Delete Empty State Sets In The Submitted File  "

			updateTooltips()

			updateRolloutTitle SMTD_ScenePreProcessing.open
		)
	)

	rollout SMTD_MaxStartup "3ds Max Startup" rolledup:true
	(
		local VOffset = 18
		local Column2 = 280

		checkbox chk_useAltPluginIni "Use Alternate Plugin.ini file  " pos:[5,5]
		checkbox chk_suggest_alt_ini "Auto-Detect ini For Current Renderer  " enabled:false pos:[Column2,5]

		dropdownList ddl_alt_ini "" width:270 align:#left enabled:false pos:[4,5+VOffset]
		button btn_edit_alt_ini "Edit Plugin.ini File" pos:[280,5+VOffset] width:100  tooltip:"Press to edit the selected Plugin.ini file." enabled:false
		button btn_browse_alt_ini "Browse Directory" pos:[380,5+VOffset] width:100 tooltip:"Press to open Windows Explorer and browse the Deadline repository directory containing the alternative plugin.ini files." enabled:false

		checkbox chk_missingExt "Ignore Missing External File Errors  " pos:[5,12+VOffset*2] align:#left
		checkbox chk_missingUVW "Ignore Missing UVW Errors  " pos:[Column2,12+VOffset*2] align:#left

		checkbox chk_missingXREF "Ignore Missing XREF Errors  " pos:[5,12+VOffset*3] align:#left
		checkbox chk_missingDLL "Ignore Missing DLL Errors  " pos:[Column2,12+VOffset*3] align:#left

		checkbox chk_pagerOverride "Override Bitmap Pager Setting While Rendering  " pos:[5,12+VOffset*4] align:#left
		checkbox chk_pager "Enable Bitmap Pager  " pos:[Column2,12+VOffset*4] align:#left

		fn updateTooltips =
		(
			chk_useAltPluginIni.tooltip = "Use the Alternate Plugin.ini file."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "UseAltPluginIni")
			chk_suggest_alt_ini.tooltip = "Auto-Detect the Plugin.ini for the Current Renderer."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "AutoSuggestIni")

			chk_missingExt.tooltip = "When checked, missing external file errors will be ignored, and the Job will render potentially incorrect output.\n\nWhen unchecked, missing external file errors will cause the Job to fail."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "IgnoreMissingExternalFiles")
			chk_missingUVW.tooltip = "When checked, missing UVW errors will be ignored, and the Job will render potentially incorrect output.\n\nWhen unchecked, missing UVW errors will cause the Job to fail."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "IgnoreMissingUVWs")

			chk_missingXREF.tooltip = "When checked, missing XREF errors will be ignored, and the Job will render potentially incorrect output.\n\nWhen unchecked, missing XREF errors will cause the Job to fail."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "IgnoreMissingXREFs")
			chk_missingDLL.tooltip = "When checked, missing DLL (Plug-in) errors will be ignored, and the Job will render potentially incorrect output.\n\nWhen unchecked, missing DLL errors will cause the Job to fail."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "IgnoreMissingDLLs")

			chk_pagerOverride.tooltip = "When checked, the 3ds Max Bitmap Pager's enabled state will be overriden according to the value set to the right.\n\nWhen unchecked, the Bitmap Pager settings of the Slaves will be respected."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "OverrideBitmapPager")
			chk_pager.tooltip = "When checked, the 3ds Max Bitmap Pager of all Slaves rendering the Job will be enabled.\n\nWhen unchecked, the Bitmap Pager will be disabled."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "BitmapPager")
		)
		fn checkSuggestPluginIni =
		(
			if chk_suggest_alt_ini.checked then
			(
				SMTDFunctions.SuggestAltIni()
				local theIndex = findItem ddl_alt_ini.items SMTDSettings.AltPluginIni
				if theIndex > 0 then
					ddl_alt_ini.selection = theIndex
				else
					ddl_alt_ini.selection = 1

				SMTDFunctions.registerCallbacks()
			)
			else
				SMTDFunctions.unregisterCallbacks()
		)

		on ddl_alt_ini selected itm do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "AltPluginIni" (SMTDSettings.AltPluginIni = ddl_alt_ini.selected)
			SMTD_MainRollout.Ui_report ("+3ds Max Startup: Alternate Plugin.ini File set to [" + SMTDSettings.AltPluginIni + "]")
		)

		on chk_useAltPluginIni changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "UseAltPluginIni" ((SMTDSettings.UseAltPluginIni = state) as string)
			ddl_alt_ini.enabled = btn_edit_alt_ini.enabled = btn_browse_alt_ini.enabled = chk_suggest_alt_ini.enabled = state
			SMTD_MainRollout.Ui_report ("+3ds Max Startup: Use Alternate Plugin.ini File option set to [" + state as string + "]")
			updateTooltips()
		)

		on chk_suggest_alt_ini changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "AutoSuggest" ((SMTDSettings.AutoSuggestIni = state) as string)
			checkSuggestPluginIni()
			SMTD_MainRollout.Ui_report ("+3ds Max Startup: Auto-Detect Ini For Current Renderer set to [" + state as string + "]")
			updateTooltips()
		)

		on btn_browse_alt_ini pressed do try( shelllaunch "Explorer.exe" SMTDPaths.PluginDir3dsmax) catch()
		on btn_edit_alt_ini pressed do try( edit SMTDSettings.theIniFiles[ddl_alt_ini.selection-1]) catch()

		on chk_pagerOverride changed state do
		(
			chk_pager.enabled = chk_pagerOverride.checked
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "OverrideBitmapPager" ( (SMTDSettings.OverrideBitmapPager= state) as string)
			if SMTDSettings.OverrideBitmapPager then
				SMTD_MainRollout.Ui_report ("+3ds Max Startup: Bitmap Pager will be set to [" + SMTDSettings.BitmapPager as string + "].")
			else
				SMTD_MainRollout.Ui_report ("+3ds Max Startup: Bitmap Pager Override turned off.")
			updateTooltips()
		)
		on chk_pager changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "BitmapPager" ( (SMTDSettings.BitmapPager = state) as string)
			SMTD_MainRollout.Ui_report ("+3ds Max Startup: Bitmap Pager will be set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_missingExt changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "IgnoreMissingExternalFiles" ((SMTDSettings.IgnoreMissingExternalFiles = state) as string)
			SMTD_MainRollout.Ui_report ("+3ds Max Startup: Ignore Missing External File Errors set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_missingUVW changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "IgnoreMissingUVWs" ((SMTDSettings.IgnoreMissingUVWs = state) as string)
			SMTD_MainRollout.Ui_report ("+3ds Max Startup: Ignore Missing UVW Errors set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_missingDLL changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "IgnoreMissingDLLs" ((SMTDSettings.IgnoreMissingDLLs = state) as string)
			SMTD_MainRollout.Ui_report ("+3ds Max Startup: Ignore Missing DLL Errors set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_missingXREF changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "IgnoreMissingXREFs" ((SMTDSettings.IgnoreMissingXREFs = state) as string)
			SMTD_MainRollout.Ui_report ("+3ds Max Startup: Ignore Missing XREF Errors set to [" + state as string + "].")
			updateTooltips()
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "3ds Max Startup"
			if not state do
			(
				if SMTDSettings.UseAltPluginIni do
				(
					theTitle+=" [Alt.INI"
					if SMTDSettings.AutoSuggestIni do theTitle+=" Auto"
					theTitle+="]"
				)
				theTitle+= " [Ignore Missing:"
				if SMTDSettings.IgnoreMissingExternalFiles or SMTDSettings.IgnoreMissingUVWs or SMTDSettings.IgnoreMissingDLLs or SMTDSettings.IgnoreMissingXREFs do
				(
					if SMTDSettings.IgnoreMissingExternalFiles do theTitle+= " Ext"
					if SMTDSettings.IgnoreMissingUVWs do theTitle+= " UVW"
					if SMTDSettings.IgnoreMissingDLLs do theTitle+= " DLL"
					if SMTDSettings.IgnoreMissingXREFs do theTitle+= " XREF"
					theTitle+="]"
				)
				if SMTDSettings.OverrideBitmapPager do
				(
					theTitle+=" [Pgr:"
					theTitle+= if SMTDSettings.BitmapPager then "ON" else "off"
					theTitle+="]"
				)
			)
			SMTD_MaxStartup.title = theTitle
		)

		on SMTD_MaxStartup rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_MaxStartup open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening 3ds Max Startup Rollout"

			SMTDFunctions.CollectAltIni()
			ddl_alt_ini.items = SMTDSettings.theIniFilenames

			local theIndex = findItem ddl_alt_ini.items SMTDSettings.AltPluginIni
			if theIndex > 0 then
				ddl_alt_ini.selection = theIndex
			else
			(
				ddl_alt_ini.selection = 1
				setIniSetting SMTDPaths.InIFile "RenderingOptions"  "AltPluginIni" (SMTDSettings.AltPluginIni = "")
			)

			chk_useAltPluginIni.checked = 				SMTDSettings.UseAltPluginIni
			chk_suggest_alt_ini.checked =				SMTDSettings.AutoSuggestIni
			checkSuggestPluginIni()
			ddl_alt_ini.enabled = btn_edit_alt_ini.enabled = btn_browse_alt_ini.enabled = chk_suggest_alt_ini.enabled = SMTDSettings.UseAltPluginIni

			chk_pagerOverride.checked = 				SMTDSettings.OverrideBitmapPager
			chk_pager.checked = 							SMTDSettings.BitmapPager
			chk_pager.enabled = 							chk_pagerOverride.checked

			chk_missingExt.checked =						SMTDSettings.IgnoreMissingExternalFiles
			chk_missingUVW.checked =					SMTDSettings.IgnoreMissingUVWs
			chk_missingDLL.checked =						SMTDSettings.IgnoreMissingDLLs
			chk_missingXREF.checked = 					SMTDSettings.IgnoreMissingXREFs

			--NON-STICKY DISPLAY
			chk_useAltPluginIni.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "UseAltPluginIni" "Use Alternate Plugin.ini file  "
			chk_suggest_alt_ini.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "AutoSuggestIni" "Auto-Detect ini For Current Renderer  "

			chk_pagerOverride.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "OverrideBitmapPager"  "Override Bitmap Pager Setting While Rendering  "
			chk_pager.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "BitmapPager"  "Enable Bitmap Pager  "

			chk_missingExt.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "IgnoreMissingExternalFiles"  "Ignore Missing External File Errors  "
			chk_missingUVW.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "IgnoreMissingUVWs"  "Ignore Missing UVW Errors  "

			chk_missingXREF.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "IgnoreMissingXREFs"  "Ignore Missing XREF Errors  "
			chk_missingDLL.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "IgnoreMissingDLLs"  "Ignore Missing DLL Errors  "

			updateTooltips()
		)
	)

	rollout SMTD_MaxRendering "3ds Max Rendering" rolledup:true
	(
		local VOffset = 17
		local VOffset2 = 20
		local GroupBase1 = 5
		local GroupBase2 = 25
		local Column2 = 280

		checkbox chk_enableFailOnblackFrames "Fail On Black Frames: " pos:[5,GroupBase1] align:#left
		spinner spn_blackPixelPercentage "Black Pixel %: " range:[0,100,1] type:#integer fieldwidth:50 pos:[349,GroupBase1] align:#left
		spinner spn_blackPixelThreshold "Black Pixel Threshold: " range:[0,1,0.1] scale:0.01 type:#float fieldwidth:50 pos:[312,GroupBase1+VOffset] align:#right
		checkbox chk_blackFramesCheckRenderElements "Fail On Black Render Element Frames " pos:[30,GroupBase1+VOffset] align:#right

		checkbox chk_ignoreRE "Do Not Save Render Element Files  " pos:[5,GroupBase2+VOffset] align:#left
		checkbox chk_showvfb "Show Virtual Frame Buffer  " pos:[Column2,GroupBase2+VOffset] align:#left

		checkbox chk_showrendererFBOverride "Override Renderer Frame Buffer Visibility  " pos:[5,GroupBase2+VOffset*2] align:#left
		checkbox chk_showrendererFB "Show Renderer Frame Buffer  " pos:[Column2,GroupBase2+VOffset*2] align:#left

		checkbox chk_disableProgresUpdate "Disable Progress Update Timeout  " pos:[5,GroupBase2+VOffset*3] align:#left
		checkbox chk_skipRender "Disable Frame Rendering  " pos:[Column2,GroupBase2+VOffset*3] align:#left

		checkbox chk_restartRenderer "Restart Renderer Between Frames  " pos:[5,GroupBase2+VOffset*4] align:#left
		checkbox chk_disableMultipass "Disable Multipass Effects  " pos:[Column2,GroupBase2+VOffset*4] align:#left

		fn updateTooltips =
		(
			chk_enableFailOnblackFrames.tooltip = "When checked, the Task will fail if the percentage of pixels darker than the specified Threshold is higher than the specified Percent value."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "EnableFailOnBlackFrames")
			spn_blackPixelPercentage.tooltip = "The Percentage of pixels darker than the specified Threshold to fail the Task."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "BlackPixelPercentage")
			spn_blackPixelThreshold.tooltip = "The threshold below which a pixel is condiered Black."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "BlackPixelThreshold")
			chk_blackFramesCheckRenderElements.tooltip = "When checked, Render Elements will also be checked for Black Pixels."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "BlackFramesCheckRenderElements")
			chk_ignoreRE.tooltip = "When checked, Render Elements will not be saved."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "IgnoreRenderElements")
			chk_showvfb.tooltip = "When checked, the 3ds Max Rendered Frame Windows will be displayed on the Slave during rendering."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "ShowFrameBuffer")
			chk_showrendererFBOverride.tooltip =  "When checked, overrides the current renderer's Frame Buffer visibility to the value to the right."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "ShowRendererFrameBufferOverride")
			chk_showrendererFB.tooltip = "The new visibility of the current renderer's Frame Buffer when Override is checked."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "ShowRendererFrameBuffer")
			chk_disableProgresUpdate.tooltip = "When checked, Progress Update Timeout checking will be disabled, useful with renderers that don't report progress often."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "DisableProgressUpdateTimeout")
			chk_skipRender.tooltip = "When checked, the actual Frame Rendering will be disabled.\n\nUseful for triggering simulations without rendering an image."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "SkipRender")
			chk_restartRenderer.tooltip = "When checked, the renderer will be restarted between frames. Mostly for working around issues where data might not get cleared between frames."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "RestartRenderer")
			chk_disableMultipass.tooltip = "When checked, Multipass Camera Effects will not be rendered."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "DisableMultipass")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "3ds Max Rendering"
			if not state do
			(
				if SMTDSettings.EnableFailOnBlackFrames do
				(
					theTitle+=" [FoB:" + SMTDSettings.BlackPixelPercentage as string + "% "  + SMTDSettings.BlackPixelThreshold as string
					if SMTDSettings.BlackFramesCheckRenderElements do theTitle += " +RE"
					theTitle += "]"
				)
				if SMTDSettings.ForceWorkstationMode do
				(
					theTitle+=" [WS"
					if SMTDSettings.UseSilentMode do theTitle+=" Silent"
					theTitle += "]"
				)

				if SMTDSettings.IgnoreRenderElements  do theTitle += " [No RE]"
				if SMTDSettings.ShowFrameBuffer do theTitle += " [VFB]"

				if SMTDSettings.ShowRendererFrameBufferOverride do
				(
					theTitle += " [RVFB:"
					theTitle+= if SMTDSettings.ShowRendererFrameBuffer then "ON" else "off"
					theTitle += "]"
				)

				if SMTDSettings.DisableProgressUpdateTimeout do theTitle+=" [No PUT]"
				if SMTDSettings.SkipRender do theTitle+=" [No Frm]"

				if SMTDSettings.RestartRenderer do theTitle+=" [R.Rend]"
				if SMTDSettings.DisableMultipass do theTitle+=" [No MPE]"
			)
			SMTD_MaxRendering.title = theTitle
		)

		--EVENT HANDLERS--
		on SMTD_MaxRendering rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_MaxRendering open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening 3ds Max Rendering Rollout"

			chk_enableFailOnblackFrames.state = 				SMTDSettings.EnableFailOnBlackFrames
			spn_blackPixelPercentage.value = 					SMTDSettings.BlackPixelPercentage
			spn_blackPixelThreshold.value = 					SMTDSettings.BlackPixelThreshold
			chk_blackFramesCheckRenderElements.state =	SMTDSettings.BlackFramesCheckRenderElements
			spn_blackPixelPercentage.enabled = spn_blackPixelThreshold.enabled = chk_blackFramesCheckRenderElements.enabled = SMTDSettings.EnableFailOnBlackFrames

			chk_ignoreRE.state =									SMTDSettings.IgnoreRenderElements
			chk_showvfb.checked = 								SMTDSettings.ShowFrameBuffer
			chk_showrendererFBOverride.checked =			SMTDSettings.ShowRendererFrameBufferOverride
			chk_showrendererFB.checked = 						SMTDSettings.ShowRendererFrameBuffer
			chk_showrendererFB.enabled =						chk_showrendererFBOverride.checked

			chk_disableProgresUpdate.checked =				SMTDSettings.DisableProgressUpdateTimeout
			chk_skipRender.checked = 							SMTDSettings.SkipRender

			chk_restartRenderer.checked = 						SMTDSettings.RestartRenderer
			chk_disableMultipass.checked = 					SMTDSettings.DisableMultipass

			--NON-STICKY DISPLAY
			chk_enableFailOnblackFrames.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "EnableFailOnBlackFrames" "Fail On Black Frames: "
			spn_blackPixelPercentage.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "BlackPixelPercentage" "Black Pixel %: "
			spn_blackPixelThreshold.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "BlackPixelThreshold" "Black Pixel Threshold: "
			chk_blackFramesCheckRenderElements.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "BlackFramesCheckRenderElements" "Fail On Black Render Element Frames "

			chk_showvfb.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "ShowFrameBuffer"   "Show Virtual Frame Buffer  "

			chk_showrendererFBOverride.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "ShowRendererFrameBufferOverride"  "Override Renderer Frame Buffer Visibility  "
			chk_showrendererFB.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "ShowRendererFrameBuffer"  "Show Renderer Frame Buffer  "

			chk_restartRenderer.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RestartRenderer"  "Restart Renderer Between Frames  "
			chk_disableMultipass.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "DisableMultipass"  "Disable Multipass Effects  "
			chk_disableProgresUpdate.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "DisableProgressUpdateTimeout"  "Disable Progress Update Timeout  "
			chk_skipRender.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "SkipRender"  "Disable Frame Rendering  "

			chk_ignoreRE.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "IgnoreRenderElements"  "Do Not Save Render Element Files  "

			updateTooltips()
			updateRolloutTitle SMTD_MaxRendering.open
		)

		on chk_ignoreRE changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "IgnoreRenderElements" ((SMTDSettings.IgnoreRenderElements = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Do Not Save Render Element Files option set to [" + state as string + "]")
			updateTooltips()
		)

		on chk_restartRenderer changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RestartRenderer" ((SMTDSettings.RestartRenderer = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Restart Renderer Between Frames set to [" + state as string + "]")
			updateTooltips()
		)

		on chk_disableMultipass changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "DisableMultipass" ((SMTDSettings.DisableMultipass = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Disable Multipass Effects set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_disableProgresUpdate changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "DisableProgressUpdateTimeout" ((SMTDSettings.DisableProgressUpdateTimeout = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Disable Progress Update Timeout set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_skipRender changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "SkipRender" ((SMTDSettings.SkipRender = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Disable Frame Rendering set to [" + state as string + "].")
			updateTooltips()
		)

		on chk_enableFailOnblackFrames changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "EnableFailOnBlackFrames" ( (SMTDSettings.EnableFailOnBlackFrames= state) as string)
			spn_blackPixelPercentage.enabled = spn_blackPixelThreshold.enabled = chk_blackFramesCheckRenderElements.enabled = state
			SMTD_MainRollout.Ui_report ("+Rendering: Fail On Black Frames set to [" + state as string + "].")
			updateTooltips()
		)
		on spn_blackPixelPercentage changed value do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "BlackPixelPercentage" ( (SMTDSettings.BlackPixelPercentage= value) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Black Pixel Percentage value set to [" + value as string + "].")
			updateTooltips()
		)
		on spn_blackPixelThreshold changed value do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "BlackPixelThreshold" ( (SMTDSettings.BlackPixelThreshold = value) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Black Pixel Threshold value set to [" + value as string + "].")
		)
		on chk_blackFramesCheckRenderElements changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "BlackFramesCheckRenderElements" ( (SMTDSettings.BlackFramesCheckRenderElements = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Fail On Black Render Element Frames [" + state as string + "].")
			updateTooltips()
		)
		on chk_showvfb changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "ShowFrameBuffer" ( (SMTDSettings.ShowFrameBuffer = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Show Frame Buffer set to [" + state as string + "].")
			updateTooltips()
		)
		on chk_showrendererFBOverride changed state do
		(
			chk_showrendererFB.enabled = chk_showrendererFBOverride.checked
			setINISetting SMTDPaths.InIFile "RenderingOptions"  "ShowRendererFrameBufferOverride" ( (SMTDSettings.ShowRendererFrameBufferOverride = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Override Renderer Frame Buffer Visibility set to [" + state as string + "].")
			updateTooltips()
		)
		on chk_showrendererFB changed state do
		(
			setINISetting SMTDPaths.InIFile "RenderingOptions"  "ShowRendererFrameBuffer" ( (SMTDSettings.ShowRendererFrameBuffer = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Show Renderer Frame Buffer set to [" + state as string + "].")
			updateTooltips()
		)
	)--end MaxRendering rollout

	rollout SMTD_Gamma "3ds Max Gamma Options" rolledup:true
	(
		checkbox chk_gammaCorrection "Override Gamma Correction  " pos:[5,5]
		label lbl_gammaInput "Input  " pos:[290,5]
		spinner spn_gammaInput range:[0.01,5.00,1.0] type:#float fieldwidth:35 pos:[320,5]
		label lbl_gammaOutput "Output  " pos:[390,5]
		spinner spn_gammaOutput range:[0.01,5.00,1.0] type:#float fieldwidth:35 pos:[430,5]

		fn updateTooltips =
		(
			chk_gammaCorrection.tooltip = "When checked, the Input and Output Gamma Correction values specified to the right will override the 3ds Max settings on each Slave to ensure consistency."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "GammaCorrection")
			spn_gammaInput.tooltip = "The Input Gamma Correction value used when the Override Gamma Correction option is checked."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "GammaInput")
			spn_gammaOutput.tooltip = "The Output Gamma Correction value used when the Override Gamma Correction option is checked."+ (SMTDFunctions.getStickyTooltipText "RenderingOptions" "GammaOutput")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "3ds Max Gamma Options"
			if not state do
			(
				if SMTDSettings.GammaCorrection then
					theTitle+= " [In: "+SMTDSettings.GammaInput as string+"] [Out: "+SMTDSettings.GammaOutput as string+"]"
				else
					theTitle+= " [Off]"
			)
			SMTD_Gamma.title = theTitle
		)

		on SMTD_Gamma rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_Gamma open do
		(
			chk_gammaCorrection.checked = SMTDSettings.GammaCorrection
			spn_gammaInput.value = SMTDSettings.GammaInput
			spn_gammaOutput.value = SMTDSettings.GammaOutput

			chk_gammaCorrection.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "GammaCorrection"  "Override Gamma Correction  "
			lbl_gammaInput.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "GammaInput"  "Input  "
			lbl_gammaOutput.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "GammaOutput"  "Output  "

			updateTooltips()
			updateRolloutTitle SMTD_Gamma.open
		)

		on chk_gammaCorrection changed state do
		(
			SMTDSettings.GammaCorrection = state
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "GammaCorrection" ((SMTDSettings.GammaCorrection = state) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Gamma Correction set to [" + state as string + "].")
			updateTooltips()
		)
		on spn_gammaInput changed value do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "GammaInput" ( (SMTDSettings.GammaInput= value) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Gamma Input value set to [" + value as string + "].")
			updateTooltips()
		)
		on spn_gammaOutput changed value do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "GammaOutput" ( (SMTDSettings.GammaOutput= value) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Gamma Output value set to [" + value as string + "].")
			updateTooltips()
		)
	)--end gamma options rollout

	rollout SMTD_GPU "GPU Affinity Overrides" rolledup:true
	(
		button btn_GPUsPerTask "GPUs Per Task: " border:false pos:[5,3] width:115
		spinner spn_GPUsPerTask range:[0,15,0] type:#integer fieldwidth:50 pos:[120,5]

		button btn_GPUDevices "Select GPU Devices:  " border:false pos:[5,24] width:115
		edittext edt_GPUDevices "" fieldwidth:360 pos:[120,26]

		fn updateTooltips =
		(
			btn_GPUsPerTask.tooltip = spn_GPUsPerTask.tooltip = "Number of GPU Devices Per Task." + (SMTDFunctions.getStickyTooltipText "GpuOptions" "GpusPerTask")
			local theTooltip = "GPU Devices to be used." + (SMTDFunctions.getStickyTooltipText "GpuOptions" "GpuDevices")
			btn_GPUDevices.tooltip = theTooltip
			try(edt_GPUDevices.tooltip = theTooltip)catch()
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "GPU Affinity Overrides"
			if not state do
			(
				if SMTDSettings.GpusPerTask > 0 then
					theTitle+= " [GPUs/Task: "+SMTDSettings.GpusPerTask as string+"]"
				else if SMTDSettings.GpuDevices != "" then
					theTitle+= " [GPU Devices: "+SMTDSettings.GpuDevices as string+"]"
				else
					theTitle+= " [Disabled]"
			)
			SMTD_GPU.title = theTitle
		)

		on SMTD_GPU rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_GPU open do
		(
			SMTD_MainRollout.Ui_report ">Opening GPU Affinity Overrides Rollout"
			spn_GPUsPerTask.value = SMTDSettings.GpusPerTask
			edt_GPUDevices.text = SMTDSettings.GpuDevices
			btn_GPUsPerTask.enabled = (edt_GPUDevices.text == "")
			spn_GPUsPerTask.enabled = (edt_GPUDevices.text == "")
			edt_GPUDevices.enabled = (spn_GPUsPerTask.value == 0)

			btn_GPUsPerTask.caption = SMTDFunctions.getStickyCaption "GpuOptions" "GpusPerTask"  "GPUs Per Task: "
			btn_GPUDevices.caption = SMTDFunctions.getStickyCaption "GpuOptions" "GpuDevices"  "Select GPU Devices: "

			updateTooltips()
			updateRolloutTitle SMTD_GPU.open
		)

		on spn_GPUsPerTask changed val do
		(
			setIniSetting SMTDPaths.InIFile "GpuOptions" "GpusPerTask" ( (SMTDSettings.GpusPerTask = val) as string)
			SMTD_MainRollout.Ui_report ("+GPU Affinity: GPUs Per Task set to [" + val as string + "].")
			edt_GPUDevices.enabled = (val == 0)
			updateTooltips()
		)

		on edt_GPUDevices changed text do
		(
			setIniSetting SMTDPaths.InIFile "GpuOptions" "GpuDevices" ( ( SMTDSettings.GpuDevices = text) as string)
			SMTD_MainRollout.Ui_report ("+GPU Affinity: GPU Devices set to [" + text + "].")
			btn_GPUsPerTask.enabled = (text == "")
			spn_GPUsPerTask.enabled = (text == "")
			updateTooltips()
		)
	)--end gpu affinity override rollout


	rollout SMTD_Pathing "3ds Max Pathing" rolledup:true
	(
		local VOffset = 17
		local Column2 = 250
		local GroupBase1 = 60 --205
		local GroupBase2 = 150 --295

		checkbox chk_localRendering "Enable Local Rendering  "  pos:[5,5] align:#left \
			tooltip:"When checked, the output image files will be rendered to the local drive of the Slave machine, then copied to the final network location if successfully saved. Multiple attempts will be made to copy if the network is experiencing temporary difficulties.\n\nWhen unchecked, the output will be saved directly to the final network location as specified in the scene's settings." --offset:[-25,0]

		checkbox chk_padding "Remove Filename Padding  " pos:[5,5+VOffset] align:#left \
			tooltip: "When checked, the output filename will not include the current frame number when rendering a single frame.\n\nFor example, instead of 'image0000.exr', the output will be 'image.exr' "
		checkbox chk_strictOutput "Force Strict Output Naming   " pos:[Column2,5+VOffset] align:#left \
			tooltip: "When checked, the output image filename path will be modified to include the scene's name as a sub-folder name.\n\nIf the new output path does not exist, it will be created by the 3dsmax plugin before rendering begins."

		checkbox chk_purifyFilenames "Purify Filenames * " pos:[5,5+VOffset*2] align:#left \
			tooltip: "When checked, filenames will be filtered for invalid characters.\n\nThe list of invalid ASCII codes to check for can be customized via the 'PurifyCharacterCodes' property in the 'SubmitMaxToDeadline_Defaults.ini' Repository file."

		checkbox chk_forceLowerCaseFilenames "Force lower-case Filenames  " pos:[Column2,5+VOffset*2] align:#left \
			tooltip: "When checked, filenames will be forced to lower-case to ensure consistency when storing output on case-sensitive systems."

		button btn_openPathPreview "Open the PREVIEW OUTPUT PATHS Dialog..." width:240 pos:[5,5+VOffset*3]
		button btn_updatePathPreview "UPDATE PREVIEW..." width:235 pos:[Column2,5+VOffset*3]

		checkbox chk_RenderElementsUpdatePaths "Update Render Element Path  " pos:[5,GroupBase1+VOffset*1] align:#left \
			tooltip: "When checked, Render Elements will be repathed to sub-folders within the main output folder.\n\nWhen unchecked, the Render Element paths assigned in 3ds Max will be used."
		checkbox chk_RenderElementsUpdateFilenames "Also Update Render Element Filename  " pos:[Column2,GroupBase1+VOffset*1] align:#left \
			tooltip: "When checked, Render Element file names will also be updated to reflect the name and/or class of the Render Element.\n\nWhen unchecked, the file names assigned in 3ds Max will be used."

		checkbox chk_RenderElementsNameInPath "Include Render Element Name In Path  " pos:[5,GroupBase1+VOffset*2] align:#left \
			tooltip: "When checked, the Render Element Name will be included in the updated Render Element path."
		checkbox chk_RenderElementsNameInFilename "Include Render Element Name In Filename  " pos:[Column2,GroupBase1+VOffset*2] align:#left \
			tooltip: "When checked, the Render Element Name will be included in the updated Render Element filename."

		checkbox chk_RenderElementsTypeInPath "Include Render Element Type In Path  " pos:[5,GroupBase1+VOffset*3] align:#left \
			tooltip: "When checked, the Render Element Type will be included in the updated Render Element path."
		checkbox chk_RenderElementsTypeInFilename "Include Render Element Type In Filename  " pos:[Column2,GroupBase1+VOffset*3] align:#left \
			tooltip: "When checked, the Render Element Type will be included in the updated Render Element filename."

		checkbox chk_RenderElementsPermanentChanges "Permanent Render Element Path Changes  " pos:[5,GroupBase1+VOffset*4] align:#left \
			tooltip: "When checked, the current 3ds Max scene's Render Element filenames will be left modified after the submission.\n\nWhen unchecked, the original Render Element filenames will be restored after submission."
		checkbox chk_RenderElementNamesPermanentChanges "Permanent Render Element Name Changes  " pos:[Column2,GroupBase1+VOffset*4] align:#left

		checkbox chk_RebuildRenderElements "Rebuild Render Elements  " pos:[5,GroupBase1+VOffset*5] align:#left
			tooltip: "When checked, the Render Elements will be rebuilt during the submission to work around known 3ds Max issues (see Online Help for details).\nNote that the file format will be unified with the main render output format."
		checkbox chk_path_include_local "Include Local Paths With Job (not used)  " pos:[Column2,GroupBase1+VOffset*5] align:#left

		checkbox chk_path_config "Use Alternate Paths File  " pos:[5,GroupBase2+VOffset] align:#left
			tooltip: "When checked, the specified .MXP file will be used by the Slaves to find bitmaps that are not found on their primary map paths."
		checkbox chk_path_config_merge "Merge Paths File  " pos:[Column2,GroupBase2+VOffset] align:#left
			tooltip: "When checked, the specified .MXP file will be merged with the primary map paths.\n\nWhen unchecked, the .MXP file will override the Slave's own map paths."

		edittext edt_path_config " " fieldwidth:455 pos:[-4,GroupBase2+VOffset*2] align:#left
		button btn_path_config "..." width:20 height:18 pos:[460,GroupBase2+VOffset*2] align:#left tooltip:"Click to select an .MXP Map Paths file..."

		local tooltip_globalpattern = 	"If a Global Output Filename Pattern is specified via the [RenderingOptions] category, OutputFilenameUserPattern property of the SubmitMaxToDeadline_Defaults.ini file in the Repository\submission\3dsmax folder, this checkbox will be checked automatically. It is not sticky! Unchecking it will ignore the pattern and use the file names from the 3ds Max scene.\n\nThese controls are meant to be used by facilities and universities that want to force the output to a globally specified location by default."

		checkbox chk_ReplaceOutputFilenameWithUserPattern "Override Output Filename By Global Pattern * " pos:[5,GroupBase2+VOffset*3] tooltip:tooltip_globalpattern
		button btn_ReplaceOutputFilenameWithUserPattern "?" width:20 height:VOffset pos:[460,GroupBase2+VOffset*3] tooltip:tooltip_globalpattern

		edittext edt_OutputFilenameUserPattern " " fieldwidth:480 pos:[-4,GroupBase2+VOffset*4] readonly:true

		fn updatePreviewDialog =
		(
			try(::SubmitMaxToDeadline_PathingExplorer.populateListView())catch()
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "3ds Max Pathing"
			if not state do
			(
				if SMTDSettings.RemovePadding do theTitle+= " [NoPad]"
				if SMTDSettings.StrictOutput do theTitle+= " [Strct]"
				if SMTDSettings.PurifyFilenames do theTitle+= " [Prfy]"
				if SMTDSettings.ForceLowerCaseFilenames do theTitle+= " [lc]"

				theTitle+= " [RE:"
				if SMTDSettings.RenderElementsUpdatePaths do theTitle+= " UP"
				if SMTDSettings.RenderElementsUpdateFilenames do theTitle+= " UF"

				if SMTDSettings.RenderElementsIncludeNameInPath do theTitle+= " NiP"
				if SMTDSettings.RenderElementsIncludeNameInFileName do theTitle+= " NiF"
				if SMTDSettings.RenderElementsIncludeTypeInPath do theTitle+= " TiP"
				if SMTDSettings.RenderElementsIncludeTypeInFileName do theTitle+= " TiF"

				if SMTDSettings.RenderElementsPermanentChanges do theTitle+= " PrmP"
				if SMTDSettings.RenderElementNamesPermanentChanges do theTitle+= " PrmF"
				if SMTDSettings.RebuildRenderElements do theTitle+= " Rebuild"
				theTitle+= "]"

				if SMTDSettings.UsePathConfigFile do
				(
					theTitle+= " [Alt.Path"
					if SMTDSettings.MergePathConfigFile do theTitle+= " Mrg"
					theTitle+= " ]"
				)
				if SMTDSettings.ReplaceOutputFilenameWithUserPattern	do
				(
					theTitle+= " [Pttrn]"
				)
			)
			SMTD_Pathing.title = theTitle
		)

		on SMTD_Pathing rolledup state do
		(
			updateRolloutTitle state
			if state do updatePreviewDialog()
		)

		on SMTD_Pathing open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening 3ds Max Pathing Options Rollout"

			chk_localRendering.state = 							SMTDSettings.LocalRendering
			chk_padding.checked = 								SMTDSettings.RemovePadding
			chk_strictOutput.checked = 							SMTDSettings.StrictOutput

			chk_purifyFilenames.checked = 						SMTDSettings.PurifyFilenames
			chk_forceLowerCaseFilenames.checked = 				SMTDSettings.ForceLowerCaseFilenames

			chk_RenderElementsUpdatePaths.state = 				SMTDSettings.RenderElementsUpdatePaths
			chk_RenderElementsUpdateFilenames.state = 			SMTDSettings.RenderElementsUpdateFilenames

			chk_RenderElementsNameInPath.state = 				SMTDSettings.RenderElementsIncludeNameInPath
			chk_RenderElementsNameInFilename.state = 			SMTDSettings.RenderElementsIncludeNameInFileName
			chk_RenderElementsTypeInPath.state = 				SMTDSettings.RenderElementsIncludeTypeInPath
			chk_RenderElementsTypeInFilename.state = 			SMTDSettings.RenderElementsIncludeTypeInFileName

			chk_RenderElementsPermanentChanges.state =			SMTDSettings.RenderElementsPermanentChanges
			chk_RenderElementNamesPermanentChanges.state = 		SMTDSettings.RenderElementNamesPermanentChanges
			chk_RebuildRenderElements.state = 					SMTDSettings.RebuildRenderElements

			chk_path_include_local.checked = 					SMTDSettings.IncludeLocalPaths
			chk_path_config.checked =							SMTDSettings.UsePathConfigFile
			chk_path_config_merge.checked = 					SMTDSettings.MergePathConfigFile
			chk_path_config_merge.enabled = 					chk_path_config.checked
			edt_path_config.text = 								SMTDSettings.PathConfigFile as string
			edt_path_config.enabled = btn_path_config.enabled = chk_path_config.checked

			--NON-STICKY DISPLAY
			chk_localRendering.caption = SMTDFunctions.getStickyCaption "UserOptions" "LocalRendering" "Enable Local Rendering  "

			chk_purifyFilenames.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "PurifyFilenames"  "Purify Filenames  "
			chk_forceLowerCaseFilenames.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "ForceLowerCaseFilenames"  "Force lower-case Filenames  "

			chk_padding.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RemovePadding"  "Remove Filename Padding  "
			chk_strictOutput.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "StrictOutput"  "Force Strict Output Naming  "

			chk_RenderElementsUpdatePaths.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RenderElementsUpdatePaths"  "Update Render Elements Path  "
			chk_RenderElementsUpdateFilenames.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RenderElementsUpdateFilenames"  "Also Update Render Element Filename  "

			chk_RenderElementsNameInPath.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RenderElementsIncludeNameInPath"  "Include Render Element Name In Path  "
			chk_RenderElementsNameInFilename.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RenderElementsIncludeNameInFileName"  "Include Render Element Name In Filename  "
			chk_RenderElementsTypeInPath.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RenderElementsIncludeTypeInPath"  "Include Render Element Type In Path  "
			chk_RenderElementsTypeInFilename.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RenderElementsIncludeTypeInFileName"  "Include Render Element Type In Filename  "

			chk_RenderElementsPermanentChanges.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RenderElementsPermanentChanges"  "Permanent Render Element Path Changes  "
			chk_RenderElementNamesPermanentChanges.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RenderElementNamesPermanentChanges"  "Permanent Render Element Name Changes  "
			chk_RebuildRenderElements.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "RebuildRenderElements" "Rebuild Render Elements  "

			chk_path_config.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "UsePathConfigFile"  "Use Alternate Paths File  "
			chk_path_config_merge.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "MergePathConfigFile"  "Merge Paths File  "
			edt_path_config.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "PathConfigFile"  " "

			chk_path_include_local.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "IncludeLocalPaths"  "Include Local Paths With Job (not used)  "

			edt_OutputFilenameUserPattern.text = SMTDSettings.OutputFilenameUserPattern
			chk_ReplaceOutputFilenameWithUserPattern.state = SMTDSettings.ReplaceOutputFilenameWithUserPattern
			chk_ReplaceOutputFilenameWithUserPattern.enabled = SMTDSettings.OutputFilenameUserPattern != ""

			updateRolloutTitle SMTD_Pathing.open
		)

		on btn_openPathPreview pressed do try(fileIn (SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_PathingExplorer.ms"))catch()
		on btn_updatePathPreview pressed do updatePreviewDialog()

		on chk_localRendering changed state do
		(
			SMTD_MainRollout.Ui_report ("+Pathing: Local Rendering set to [" + state as string + "].")
			setIniSetting SMTDPaths.InIFile "UserOptions"  "LocalRendering" ( (SMTDSettings.LocalRendering = state) as string)
		)

		on chk_purifyFilenames changed state do
		(
			SMTDSettings.PurifyFilenames = state
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "PurifyFilenames" ((SMTDSettings.PurifyFilenames = state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Purify Filenames set to [" + state as string + "].")
			updatePreviewDialog()
		)

		on chk_forceLowerCaseFilenames changed state do
		(
			SMTDSettings.ForceLowerCaseFilenames = state
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "ForceLowerCaseFilenames" ((SMTDSettings.ForceLowerCaseFilenames = state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Force Lower Case Filenames set to [" + state as string + "].")
			updatePreviewDialog()
		)

		on chk_ReplaceOutputFilenameWithUserPattern changed state do
		(
			SMTDSettings.ReplaceOutputFilenameWithUserPattern = state
			SMTD_MainRollout.Ui_report ("+Pathing: Override Output Filename By Global Pattern set to [" + state as string + "] for this session.")
			updatePreviewDialog()
		)

		on chk_RenderElementsUpdatePaths changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RenderElementsUpdatePaths" ((SMTDSettings.RenderElementsUpdatePaths= state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: RenderElements Update Paths set to [" + state as string + "]")
			updatePreviewDialog()
		)

		on chk_RenderElementsUpdateFilenames changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RenderElementsUpdateFilenames" ((SMTDSettings.RenderElementsUpdateFilenames= state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: RenderElements Update Filenames set to [" + state as string + "]")
			updatePreviewDialog()
		)



		on chk_RenderElementsNameInPath changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RenderElementsIncludeNameInPath" ((SMTDSettings.RenderElementsIncludeNameInPath= state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Include RE Name In Paths set to [" + state as string + "]")
			updatePreviewDialog()
		)

		on chk_RenderElementsNameInFilename changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RenderElementsIncludeNameInFileName" ((SMTDSettings.RenderElementsIncludeNameInFileName= state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Include RE Name In Filenames set to [" + state as string + "]")
			updatePreviewDialog()
		)

		on chk_RenderElementsTypeInPath changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RenderElementsIncludeTypeInPath" ((SMTDSettings.RenderElementsIncludeTypeInPath= state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Include RE Type In Paths set to [" + state as string + "]")
			updatePreviewDialog()
		)

		on chk_RenderElementsTypeInFilename changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RenderElementsIncludeTypeInFileName" ((SMTDSettings.RenderElementsIncludeTypeInFileName= state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Include RE Type In Filenames set to [" + state as string + "]")
			updatePreviewDialog()
		)

		on chk_RenderElementsPermanentChanges changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RenderElementsPermanentChanges" ((SMTDSettings.RenderElementsPermanentChanges= state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: RenderElements Permanent Path Changes set to [" + state as string + "]")
		)

		on chk_RenderElementNamesPermanentChanges changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RenderElementNamesPermanentChanges" ((SMTDSettings.RenderElementNamesPermanentChanges= state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: RenderElements Permanent Name Changes set to [" + state as string + "]")
		)

		on chk_RebuildRenderElements changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RebuildRenderElements" ((SMTDSettings.RebuildRenderElements= state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Rebuild RenderElements Changes set to [" + state as string + "]")
		)

		on chk_padding changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RemovePadding" ((SMTDSettings.RemovePadding = state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Remove Filename Padding  set to [" + state as string + "].")
			updatePreviewDialog()
		)

		on chk_strictOutput changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "StrictOutput" ((SMTDSettings.StrictOutput = state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Force Strict Output Naming set to [" + state as string + "].")
			updatePreviewDialog()
		)

		on chk_path_config changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "UsePathConfigFile" ((SMTDSettings.UsePathConfigFile = state) as string)
			chk_path_config_merge.enabled = btn_path_config.enabled = edt_path_config.enabled = chk_path_config.checked
			SMTD_MainRollout.Ui_report ("+Pathing: Use Alternate Path File set to [" + state as string+ "].")
		)

		on chk_path_config_merge changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "MergePathConfigFile" ((SMTDSettings.MergePathConfigFile = state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Merge Path File set to [" + state as string+ "].")
		)

		on chk_path_include_local changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "IncludeLocalPaths" ((SMTDSettings.IncludeLocalPaths = state) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Include Local Paths set to [" + state as string+ "].")
		)

		on edt_path_config entered txt do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "PathConfigFile" ((SMTDSettings.PathConfigFile = txt) as string)
			SMTD_MainRollout.Ui_report ("+Pathing: Alternate Path File ENTERED as [" + txt + "].")
		)

		on btn_path_config pressed do
		(
			pathConfigFile = getOpenFileName caption:"Select A Path Configuration File." types:"Path Configuration File (*.mxp)|*.mxp|All Files (*.*)|*.*|"
			if pathConfigFile != undefined then
			(
				edt_path_config.text = pathConfigFile
				setIniSetting SMTDPaths.InIFile "RenderingOptions"  "PathConfigFile" ((SMTDSettings.PathConfigFile = pathConfigFile) as string)
				SMTD_MainRollout.Ui_report ("+Pathing: Alternate Path File PICKED as [" + pathConfigFile + "].")
			)
		)
	)


	rollout SMTD_IMSQ "Render Output and Autodesk ME Image Sequence (IMSQ) Creation" rolledup:true
	(
		--button btn_help_save_file "?" width:12 across:4 align:#left offset:[-5,-2] tooltip:"Click for Online Help on using the Render Output options."
		checkbox chk_save_file "Save File" pos:[5,5] align:#left across:3 --offset:[-80,0]
		edittext edt_save_file " " fieldwidth:385 pos:[65,5] align:#left --align:#left offset:[-110,0]
		button btn_save_file "..." width:20 height:18 align:#right offset:[10,-2]

		--button btn_help_imsq "?" width:12 across:3 align:#left offset:[-5,-2] tooltip:"Click for Online Help on using the Image File List options."
		checkbox chk_create_imsq "Create Image Sequence (IMSQ) File  " pos:[5,25] align:#left --offset:[-112,0]
		checkbox chk_copy_imsq "Copy IMSQ File On Completion  " pos:[225,25] align:#left --offset:[-38,0]

		--button btn_help_imsq2 "?" width:12 across:3 align:#left offset:[-5,-2] tooltip:"Click for Online Help on using the Image File List options."
		edittext edt_imsq_path " " fieldwidth:452 pos:[-2,45] align:#left across:2 --align:#left offset:[-116,0]
		button btn_imsq_path "..." width:20 height:18 align:#right offset:[10,0]

		on btn_help_save_file pressed do ShellLaunch (SMTD_HelpURL + "#render-tab") ""
		on btn_help_imsq pressed do ShellLaunch (SMTD_HelpURL + "#render-tab") ""
		on btn_help_imsq2 pressed do ShellLaunch (SMTD_HelpURL + "#render-tab") ""


		fn updateRolloutTitle state =
		(
			local theTitle = "Render Output and Autodesk ME Image Sequence (IMSQ) Creation"
			if not state do
			(
				if SMTDSettings.CreateImsqFile do
				(
					theTitle+=" [IMSQ "
					if SMTDSettings.CopyImsqFile do theTitle+=" Copy"
					theTitle+="]"
				)
			)
			SMTD_IMSQ.title = theTitle
		)

		on SMTD_IMSQ rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_IMSQ open do
		(
			chk_save_file.checked = rendSaveFile
			edt_save_file.enabled = rendSaveFile
			btn_save_file.enabled = rendSaveFile
			edt_save_file.text = rendOutputFilename

			chk_create_imsq.checked =				SMTDSettings.CreateImsqFile
			chk_copy_imsq.checked = 				SMTDSettings.CopyImsqFile
			edt_imsq_path.text = 					SMTDSettings.ImsqOutputPath as string
			chk_copy_imsq.enabled = 				chk_create_imsq.checked
			btn_imsq_path.enabled = 				edt_imsq_path.enabled = (chk_create_imsq.checked and chk_copy_imsq.checked)

			chk_create_imsq.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "CreateImsqFile"  "Create Image Sequence (IMSQ) File  "
			chk_copy_imsq.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "CopyImsqFile"  "Copy IMSQ File On Completion  "
			edt_imsq_path.caption = SMTDFunctions.getStickyCaption "RenderingOptions" "ImsqOutputPath"  " "

			updateRolloutTitle SMTD_IMSQ.open
		)

		on chk_save_file changed state do
		(
			rendSaveFile = state
			edt_save_file.enabled = rendSaveFile
			btn_save_file.enabled = rendSaveFile
			SMTD_MainRollout.Ui_report ("+Rendering: Save File set to [" + state as string + "].")

			edt_save_file.text = rendOutputFilename
			SMTD_MainRollout.Ui_report ("+Rendering: Render Output set to [" + edt_save_file.text + "].")

			if renderSceneDialog.isOpen() do renderSceneDialog.update()
		)

		on edt_save_file entered txt do
		(
			rendOutputFilename = txt
			SMTD_MainRollout.Ui_report ("+Rendering: Render Output set to [" + txt + "].")

			if renderSceneDialog.isOpen() do renderSceneDialog.update()
		)

		on btn_save_file pressed do
		(
			renderOutput = getBitmapSaveFileName caption:"Render Output File" filename:rendOutputFilename
			if renderOutput != undefined then
			(
				edt_save_file.text = renderOutput
				rendOutputFilename = renderOutput
				SMTD_MainRollout.Ui_report ("+Rendering: Render Output set to [" + renderOutput + "].")
			)

			if renderSceneDialog.isOpen() do renderSceneDialog.update()
		)

		on chk_create_imsq changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "CreateImsqFile" ((SMTDSettings.CreateImsqFile = state) as string)
			chk_copy_imsq.enabled = chk_create_imsq.checked
			btn_imsq_path.enabled = edt_imsq_path.enabled = (chk_create_imsq.checked and chk_copy_imsq.checked)
			SMTD_MainRollout.Ui_report ("+Rendering: Create Image Sequence (IMSQ) File set to [" + state as string+ "].")
		)

		on chk_copy_imsq changed state do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "CopyImsqFile" ((SMTDSettings.CopyImsqFile = state) as string)
			btn_imsq_path.enabled = edt_imsq_path.enabled = (chk_create_imsq.checked and chk_copy_imsq.checked)
			SMTD_MainRollout.Ui_report ("+Rendering: Copy Image IMSQ File On Completion set to [" + state as string+ "].")
		)

		on edt_imsq_path entered txt do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "ImsqOutputPath" ((SMTDSettings.ImsqOutputPath = txt) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Path to copy IMSQ file to ENTERED as [" + txt + "].")
		)
		on btn_imsq_path pressed do
		(
			imsqOutput = getSavePath caption:"Select a folder to copy the imsq file to."
			if imsqOutput != undefined then
			(
				edt_imsq_path.text = imsqOutput
				setIniSetting SMTDPaths.InIFile "RenderingOptions"  "ImsqOutputPath" ((SMTDSettings.ImsqOutputPath = imsqOutput) as string)
				SMTD_MainRollout.Ui_report ("+Rendering: Path to copy IMSQ file to PICKED as [" + imsqOutput + "].")
			)
		)
	)--end IMSQ rollout

	rollout SMTD_UserOptions "User Options"
	(
		local VSpace = 18

		checkbox chk_closeAfterSubmission "Close SMTD Dialog After Submission  " pos:[5,5] tooltip:"When checked, the submission dialog will be closed when a job is successfully submitted."

		checkbox chk_updateJobName "Automatically Update Job Name When Scene File Name Changes  " pos:[5,5+VSpace*1] align:#left  tooltip:"When checked, the Job Name will be changed each time the Scene File Name changes because the scene has been resaved under a new name or a new scene has been loaded.\n\nWhen unchecked, the Job Name will stay as last entered even if the scene name changes."

		checkbox chk_DumpFileProperties "Dump Scene File Properties to Job Log Report  " pos:[5,5+VSpace*2] tooltip:"When checked, [customize.ms] will dump the current 3dsMax scene file's properties to the job log report.\n\n(for debugging purposes only)."

		checkbox chk_WarnAboutMissingExternalFiles "Warn about Missing External Files on Submission  " pos:[5,5+VSpace*3] tooltip:"When checked, a warning will be issued if external files are missing.\n\nWhen unchecked, no warning will be issued."

		checkbox chk_WarnAboutCopyingExternalFiles "Warn about Copying External Files with Job if  " pos:[5,5+VSpace*4] tooltip:"When checked, a warning will be issued if external files are to be copied and their count or size exceed the threshold.\n\nWhen unchecked, no warning will be issued."
		spinner spn_CopyExternalFilesCountThreshold "Count >" pos:[255,6+VSpace*4] type:#integer range:[0,1000000,100] fieldwidth:40
		spinner spn_CopyExternalFilesMBThreshold "OR Size in MB >" pos:[355,6+VSpace*4] type:#integer range:[0,1000000,1024] fieldwidth:40

		checkbox chk_overrideLanguage "Override 3ds Max Language  " pos:[5,5+VSpace*5] align:#left
		dropdownlist ddl_language items:#() width:230 pos:[255,5+VSpace*5] align:#left

		on chk_closeAfterSubmission changed state do
		(
			SMTD_MainRollout.Ui_report ("+User Options: Close SMTD Dialog After Submission set to [" + state as string + "].")
			setIniSetting SMTDPaths.InIFile "UserOptions"  "CloseAfterSubmission" ( (SMTDSettings.CloseAfterSubmission = state) as string)
		)

		on chk_DumpFileProperties changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "DumpFileProperties" ( (SMTDSettings.DumpFileProperties = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Dump File Properties set to [" + state as string + "].")
		)

		on chk_WarnAboutMissingExternalFiles changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "WarnAboutMissingExternalFiles" ( (SMTDSettings.WarnAboutMissingExternalFiles = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Warn About Missing External Files set to [" + state as string + "].")
		)

		on chk_overrideLanguage changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "OverrideLanguage" ( (SMTDSettings.OverrideLanguage = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Override 3ds Max Language set to [" + state as string + "].")
			ddl_language.enabled = SMTDSettings.OverrideLanguage
		)

		on ddl_language selected itm do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "Language" ( (SMTDSettings.Language = itm) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Language set to [" + ddl_language.selected + "] .")
		)

		on chk_updateJobName changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "AutomaticallyUpdateJobName" ( (SMTDSettings.AutomaticallyUpdateJobName = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Automatically Update Job Name set to [" + state as string + "].")
		)

		on chk_WarnAboutCopyingExternalFiles changed state do
		(

			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExternalFilesWarningOn" ( (SMTDSettings.ExternalFilesWarningOn = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Warn About Copying External Files set to [" + state as string + "].")
		)

		on spn_CopyExternalFilesCountThreshold changed val do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExternalFilesWarningCount" ( (SMTDSettings.ExternalFilesWarningCount = val) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Warn About Copying External Files Count Threshold set to [" + val as string + "].")
		)
		on spn_CopyExternalFilesMBThreshold changed val do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExternalFilesWarningMB" ( (SMTDSettings.ExternalFilesWarningMB = val) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Warn About Copying External Files Size In MB Threshold set to [" + val as string + "].")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "User Options"
			if not state do
			(
				if SMTDSettings.CloseAfterSubmission do theTitle+= " [Close]"
				if SMTDSettings.AutomaticallyUpdateJobName do theTitle+= " [AutoName]"
				if SMTDSettings.DumpFileProperties do theTitle+= " [Dump]"
				if SMTDSettings.WarnAboutMissingExternalFiles do theTitle+= " [Missing]"
				if SMTDSettings.ExternalFilesWarningOn do
				(
					theTitle+= " [Ext:" + SMTDSettings.ExternalFilesWarningCount as string + ":"+SMTDSettings.ExternalFilesWarningMB as string+"]"
				)

				if SMTDSettings.OverrideLanguage do
				(
					theTitle+= " [Lang:"
					theTitle+= ddl_language.items[SMTDSettings.Language]
					theTitle+= "]"
				)

			)
			SMTD_UserOptions.title = theTitle
		)

		on SMTD_UserOptions rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_UserOptions open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening User Options Rollout"
			chk_closeAfterSubmission.state = SMTDSettings.CloseAfterSubmission
			chk_DumpFileProperties.state = SMTDSettings.DumpFileProperties
			chk_WarnAboutMissingExternalFiles.state = SMTDSettings.WarnAboutMissingExternalFiles
			chk_overrideLanguage.state = SMTDSettings.OverrideLanguage
			chk_updateJobName.state = SMTDSettings.AutomaticallyUpdateJobName

			chk_WarnAboutCopyingExternalFiles.state = SMTDSettings.ExternalFilesWarningOn
			spn_CopyExternalFilesCountThreshold.value = SMTDSettings.ExternalFilesWarningCount
			spn_CopyExternalFilesMBThreshold.value = SMTDSettings.ExternalFilesWarningMB

			if SMTDFunctions.getMaxVersionAsInteger() >= 2016 then
			(
				appendIfUnique SMTDSettings.LanguageArray "Brazilian Portuguese"
				appendIfUnique SMTDSettings.LanguageCodeArray "BTP"
			)

			ddl_language.items = SMTDSettings.LanguageArray

			ddl_language.enabled = SMTDSettings.OverrideLanguage

			local theIndex = 0
			if SMTDFunctions.getMaxVersionAsInteger() >= 2013 then
			(
				theIndex = SMTDSettings.Language
				if theIndex == 0 do
				(
					local languageInfo = sysinfo.GetMaxLanguage()
					local languageCode = languageInfo[3]
					theIndex = findItem SMTDSettings.LanguageCodeArray languageCode
				)
			)
			else
			(
				chk_overrideLanguage.enabled = false
				ddl_language.enabled = false
			)
			if theIndex > 0 then
			(
				ddl_language.selection = theIndex
				SMTDSettings.Language = theIndex
			)
			else
			(
				ddl_language.selection = 1
				SMTDSettings.Language = 1
			)

			--chk_autoSuggestCategory.caption = SMTDFunctions.getStickyCaption "UserOptions" "AutoSuggestCategory"  "Auto-Suggest Job Category and Priority  "
			--chk_sortPoolsAlphabetically.caption = SMTDFunctions.getStickyCaption "UserOptions" "PoolsSort"   "Sort Pool Names Alphabetically -- digits > Upper Case > lower case  "

			--chk_submitScene.caption = SMTDFunctions.getStickyCaption "UserOptions" "SubmitScene" "Submit Scene File With Job  "
			chk_closeAfterSubmission.caption = SMTDFunctions.getStickyCaption "UserOptions" "CloseAfterSubmission" "Close SMTD Dialog After Submission  "
			chk_DumpFileProperties.caption = SMTDFunctions.getStickyCaption "UserOptions" "DumpFileProperties"  "Dump Scene File Properties to Job Log Report  "
			chk_WarnAboutMissingExternalFiles.caption = SMTDFunctions.getStickyCaption "UserOptions" "WarnAboutMissingExternalFiles"  "Warn about Missing External Files on Submission  "
			chk_overrideLanguage.caption = SMTDFunctions.getStickyCaption "UserOptions" "OverrideLanguage" "Override 3ds Max Language  "
			chk_updateJobName.caption = SMTDFunctions.getStickyCaption "UserOptions" "AutomaticallyUpdateJobName"  "Automatically Update Job Name When Scene File Name Changes  "
			chk_WarnAboutCopyingExternalFiles.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExternalFilesWarningOn"  "Warn about Copying External Files with Job if  "

			updateRolloutTitle SMTD_UserOptions.open
		)
	)

	rollout SMTD_RendererExport "Renderer Settings Export" rolledup:true
	(
		local VSpace = 18
		local Column2 = 165
		local Column3 = 325
		checkbox chk_ExportAdvancedRenderOutputFiles "Export Renderer Caching Output Files  " pos:[5,5] \
			tooltip:"When checked, any renderer-specific caching output files which will be generated as part of this render job will be added as Deadline Monitor output paths accessible via the right-click View Output menu of the job.\n\nMental Ray, Corona and V-Ray caching files are currently supported."

		checkbox chk_ExportAdvancedRenderInfoScanline "3ds Max Scanline  " pos:[5,5+VSpace]
		checkbox chk_ExportAdvancedRenderInfoQuicksilver "3ds Max Quicksilver  " pos:[Column2,5+VSpace]
		checkbox chk_ExportAdvancedRenderInfoArt "Autodesk ART  " pos:[Column3,5+VSpace]

		checkbox chk_ExportAdvancedRenderInfoArnold  "Solid Angle Arnold  " pos:[5,5+VSpace*2]
		checkbox chk_ExportAdvancedRenderInfoIRay "NVidia iray  " pos:[Column2,5+VSpace*2]
		checkbox chk_ExportAdvancedRenderInfoMentalRay "NVidia Mental Ray  " pos:[Column3,5+VSpace*2]

		checkbox chk_ExportAdvancedRenderInfoVRay "Chaos Group V-Ray  " pos:[5,5+VSpace*3]
		checkbox chk_ExportAdvancedRenderInfoVRayRT "Chaos Group V-Ray RT  " pos:[Column2,5+VSpace*3]
		checkbox chk_ExportAdvancedRenderInfoCorona "Render Legion Corona  " pos:[Column3,5+VSpace*3]

		checkbox chk_ExportAdvancedRenderInfoKrakatoa "Thinkbox Krakatoa MX  " pos:[5,5+VSpace*4]
		checkbox chk_ExportAdvancedRenderInfoRedshift "RRT Redshift  " pos:[Column2,5+VSpace*4]
		checkbox chk_ExportAdvancedRenderInfoMaxwell "Next Limit Maxwell  " pos:[Column3,5+VSpace*4]

		checkbox chk_ExportAdvancedRenderInfoOctane "OTOY Octane  " pos:[5,5+VSpace*5]
		checkbox chk_ExportAdvancedRenderInfoFinalRender "Cebas finalRender  " pos:[Column2,5+VSpace*5]
		checkbox chk_ExportAdvancedRenderInfoBrazil2 "SplutterFish Brazil r/s 2.x  " pos:[Column3,5+VSpace*5]

		on chk_ExportAdvancedRenderOutputFiles changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderOutputFiles" ( (SMTDSettings.ExportAdvancedRenderOutputFiles = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Renderer Caching Output Files set to [" + state as string + "].")
		)

		on chk_ExportAdvancedRenderInfoScanline changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoScanline" ( (SMTDSettings.ExportAdvancedRenderInfoScanline = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For Scanline set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoMentalRay changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoMentalRay" ( (SMTDSettings.ExportAdvancedRenderInfoMentalRay = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For Mental Ray set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoBrazil2 changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoBrazil2" ( (SMTDSettings.ExportAdvancedRenderInfoBrazil2 = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For Brazil r/s 2.x set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoVRay changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoVRay" ( (SMTDSettings.ExportAdvancedRenderInfoVRay = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For V-Ray set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoVRayRT changed state do
		(
			setIniSetting SMTDPaths.IniFile "UserOptions"  "ExportAdvancedRenderInfoVRayRT" ( (SMTDSettings.ExportAdvancedRenderInfoVRayRT = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For V-Ray RT set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoCorona changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoCorona" ( (SMTDSettings.ExportAdvancedRenderInfoCorona = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For Corona set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoArt changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoArt" ( (SMTDSettings.ExportAdvancedRenderInfoArt = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For ART set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoArnold changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoArnold" ( (SMTDSettings.ExportAdvancedRenderInfoArnold = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For Arnold set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoFinalRender changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoFinalRender" ( (SMTDSettings.ExportAdvancedRenderInfoFinalRender = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For finanRender set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoMaxwell changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoMaxwell" ( (SMTDSettings.ExportAdvancedRenderInfoMaxwell = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For Maxwell set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoQuicksilver changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoQuicksilver" ( (SMTDSettings.ExportAdvancedRenderInfoQuicksilver = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For Quicksliver set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoIRay changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoIRay" ( (SMTDSettings.ExportAdvancedRenderInfoIRay = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For iray set to [" + state as string + "].")
		)
		on chk_ExportAdvancedRenderInfoKrakatoa changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoKrakatoa" ( (SMTDSettings.ExportAdvancedRenderInfoKrakatoa = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For Krakatoa set to [" + state as string + "].")
		)

		on chk_ExportAdvancedRenderInfoRedshift changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoRedshift" ( (SMTDSettings.ExportAdvancedRenderInfoRedshift = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For Redshift set to [" + state as string + "].")
		)

		on chk_ExportAdvancedRenderInfoOctane changed state do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "ExportAdvancedRenderInfoOctane" ( (SMTDSettings.ExportAdvancedRenderInfoOctane = state) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Export Adv. Render Info For Octane set to [" + state as string + "].")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Renderer Settings Export"
			if not state do
			(
				if not SMTDSettings.ExportAdvancedRenderOutputFiles do theTitle+= " [-Cache]"
				if not SMTDSettings.ExportAdvancedRenderInfoScanline do theTitle+= " [-SL]"
				if not SMTDSettings.ExportAdvancedRenderInfoMentalRay do theTitle+= " [-mr]"
				if not SMTDSettings.ExportAdvancedRenderInfoBrazil2 do theTitle+= " [-Br2]"
				if not SMTDSettings.ExportAdvancedRenderInfoVRay do theTitle+= " [-Vr]"
				if not SMTDSettings.ExportAdvancedRenderInfoVRayRT  do theTitle+= " [-VrRT]"
				if not SMTDSettings.ExportAdvancedRenderInfoCorona do theTitle+= " [-Crn]"
				if not SMTDSettings.ExportAdvancedRenderInfoArt do theTitle+= " [-ART]"
				if not SMTDSettings.ExportAdvancedRenderInfoKrakatoa  do theTitle+= " [-KMX]"
				if not SMTDSettings.ExportAdvancedRenderInfoFinalRender do theTitle+= " [-fR]"
				if not SMTDSettings.ExportAdvancedRenderInfoMaxwell do theTitle+= " [-Mxwl]"
				if not SMTDSettings.ExportAdvancedRenderInfoQuicksilver do theTitle+= " [-QS]"
				if not SMTDSettings.ExportAdvancedRenderInfoIRay do theTitle+= " [-iR]"
				if not SMTDSettings.ExportAdvancedRenderInfoRedshift do theTitle+= " [-RS]"
				if not SMTDSettings.ExportAdvancedRenderInfoArnold do theTitle+= " [-Arnld]"
				if not SMTDSettings.ExportAdvancedRenderInfoOctane do theTitle+= " [-Oct]"
			)
			SMTD_RendererExport.title = theTitle
		)

		on SMTD_RendererExport rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_RendererExport open do
		(
			chk_ExportAdvancedRenderOutputFiles.state = SMTDSettings.ExportAdvancedRenderOutputFiles
			chk_ExportAdvancedRenderInfoScanline.state = SMTDSettings.ExportAdvancedRenderInfoScanline
			chk_ExportAdvancedRenderInfoMentalRay.state = SMTDSettings.ExportAdvancedRenderInfoMentalRay
			chk_ExportAdvancedRenderInfoBrazil2.state = SMTDSettings.ExportAdvancedRenderInfoBrazil2
			chk_ExportAdvancedRenderInfoVRay.state = SMTDSettings.ExportAdvancedRenderInfoVRay
			chk_ExportAdvancedRenderInfoVRayRT.state = SMTDSettings.ExportAdvancedRenderInfoVRayRT
			chk_ExportAdvancedRenderInfoCorona.state = SMTDSettings.ExportAdvancedRenderInfoCorona
			chk_ExportAdvancedRenderInfoArt.state = SMTDSettings.ExportAdvancedRenderInfoArt
			chk_ExportAdvancedRenderInfoKrakatoa.state = SMTDSettings.ExportAdvancedRenderInfoKrakatoa
			chk_ExportAdvancedRenderInfoFinalRender.state = SMTDSettings.ExportAdvancedRenderInfoFinalRender
			chk_ExportAdvancedRenderInfoMaxwell.state = SMTDSettings.ExportAdvancedRenderInfoMaxwell
			chk_ExportAdvancedRenderInfoQuicksilver.state = SMTDSettings.ExportAdvancedRenderInfoQuicksilver
			chk_ExportAdvancedRenderInfoIRay.state = SMTDSettings.ExportAdvancedRenderInfoIRay
			chk_ExportAdvancedRenderInfoRedshift.state = SMTDSettings.ExportAdvancedRenderInfoRedshift
			chk_ExportAdvancedRenderInfoArnold.state = SMTDSettings.ExportAdvancedRenderInfoArnold
			chk_ExportAdvancedRenderInfoOctane.state = SMTDSettings.ExportAdvancedRenderInfoOctane

			chk_ExportAdvancedRenderOutputFiles.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderOutputFiles"   "Export Renderer Caching Output Files  "
			chk_ExportAdvancedRenderInfoScanline.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoScanline"   "3ds Max Scanline  "
			chk_ExportAdvancedRenderInfoMentalRay.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoMentalRay"   "NVidia Mental Ray  "
			chk_ExportAdvancedRenderInfoBrazil2.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoBrazil2"   "SplutterFish Brazil r/s 2.x  "
			chk_ExportAdvancedRenderInfoVRay.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoVRay"   "Chaos Group V-Ray  "
			chk_ExportAdvancedRenderInfoVRayRT.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoVRayRT"  "Chaos Group V-Ray RT  "
			chk_ExportAdvancedRenderInfoCorona.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoCorona"   "Render Legion Corona  "
			chk_ExportAdvancedRenderInfoArt.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoArt"   "Autodesk ART  "
			chk_ExportAdvancedRenderInfoArnold.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoArnold"   "Solid Angle Arnold  "
			chk_ExportAdvancedRenderInfoKrakatoa.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoKrakatoa"   "Thinkbox Krakatoa MX  "
			chk_ExportAdvancedRenderInfoFinalRender.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoFinalRender"   "Cebas finalRender  "
			chk_ExportAdvancedRenderInfoMaxwell.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoMaxwell"   "Next Limit Maxwell  "
			chk_ExportAdvancedRenderInfoQuicksilver.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoQuicksilver"   "3ds Max Quicksilver  "
			chk_ExportAdvancedRenderInfoIRay.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoIRay"   "NVidia iray  "
			chk_ExportAdvancedRenderInfoRedshift.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoRedshift"   "RRT Redshift  "
			chk_ExportAdvancedRenderInfoOctane.caption = SMTDFunctions.getStickyCaption "UserOptions" "ExportAdvancedRenderInfoOctane"   "OTOY Octane  "

			updateRolloutTitle SMTD_RendererExport.open
		)
	)

	rollout SMTD_SubmissionTimeouts "Submission Timeouts" rolledup:true
	(
		spinner spn_TimeoutSubmission "Job Submission Timeout in seconds: " offset:[0,0] align:#right fieldwidth:50 type:#integer range:[30,10000,3600]
		spinner spn_TimeoutCollectData "Data Collection Timeout in seconds: " offset:[0,-3] align:#right fieldwidth:50 type:#integer range:[10,10000,60]

		on btn_help_submissiontimeout  pressed do ShellLaunch (SMTD_HelpURL + "#options-tab") ""
		on btn_help_datatimeout  pressed do ShellLaunch (SMTD_HelpURL + "#options-tab") ""

		--EVENT HANDLERS--
		on spn_TimeoutSubmission changed value do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "TimeoutSubmission" ( (SMTDSettings.TimeoutSubmission = value) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Job Submission Timeout set to [" + value as string + "] seconds.")
		)
		on spn_TimeoutCollectData changed value do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "TimeoutCollectData" ( (SMTDSettings.TimeoutCollectData = value) as string)
			SMTD_MainRollout.Ui_report ("+User Options: Data Collection Timeout set to [" + value as string + "] seconds.")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Submission Timeouts"
			if not state do
			(
				theTitle+= " [Job: "+SMTDSettings.TimeoutSubmission as string+"]"
				theTitle+= " [Data: "+SMTDSettings.TimeoutCollectData as string+"]"
			)
			SMTD_SubmissionTimeouts.title = theTitle
		)

		on SMTD_SubmissionTimeouts rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_SubmissionTimeouts open do
		(
			spn_TimeoutSubmission.value = SMTDSettings.TimeoutSubmission
			spn_TimeoutCollectData.value = SMTDSettings.TimeoutCollectData

			spn_TimeoutSubmission.caption = SMTDFunctions.getStickyCaption "UserOptions" "TimeoutSubmission"   "Job Submission Timeout in seconds: "
			spn_TimeoutCollectData.caption = SMTDFunctions.getStickyCaption "UserOptions" "TimeoutCollectData"   "Data Collection Timeout in seconds: "

			updateRolloutTitle SMTD_SubmissionTimeouts.open
		)
	)

	rollout SMTD_PythonScripts "Run Python Scripts" rolledup:true
	(
		checkbox chk_runPreJobScript "Run Pre-Job Script*" align:#left checked:false offset:[-6,0] across:2 \
			tooltip:"When checked, the specified Python script will be executed before the Job has started processing."
		button btn_getPreJobScript "Pick Pre-Job Script..." align:#right width:140 height:18 offset:[5,-3] tooltip:"Pick a Pre-Job Script File."
		edittext edt_PreJobScript text:"" offset:[-10,-5] width:480

		checkbox chk_runPostJobScript "Run Post-Job Script*" align:#left checked:false offset:[-6,0] across:2 \
			tooltip:"When checked, the specified Python script will be executed after the Job has finished processing."
		button btn_getPostJobScript "Pick Post-Job Script..." align:#right width:140 height:18 offset:[5,-3] tooltip:"Pick a Post-Job Script File."
		edittext edt_PostJobScript text:"" offset:[-10,-5] width:480

		checkbox chk_runPreTaskScript "Run Pre-Task Script*" align:#left checked:false offset:[-6,0] across:2 \
			tooltip:"When checked, the specified Python script will be executed before each Task is processed."
		button btn_getPreTaskScript "Pick Pre-Task Script..." align:#right width:140 height:18 offset:[5,-3] tooltip:"Pick a Pre-Task Script File."
		edittext edt_PreTaskScript text:"" offset:[-10,-5] width:480

		checkbox chk_runPostTaskScript "Run Post-Task Script*" align:#left checked:false offset:[-6,0]  across:2 \
			tooltip:"When checked, the specified Python script will be executed after each Task has finished processing."
		button btn_getPostTaskScript "Pick Post-Task Script..." align:#right width:140 height:18 offset:[5,-3] tooltip:"Pick a Post-Task Script File."
		edittext edt_PostTaskScript text:"" offset:[-10,-5] width:480

		on btn_help_runPreJobScript pressed do ShellLaunch (SMTD_HelpURL + "#scripts-tab") ""
		on btn_help_runPostJobScript pressed do ShellLaunch (SMTD_HelpURL + "#scripts-tab") ""
		on btn_help_runPreTaskScript pressed do ShellLaunch (SMTD_HelpURL + "#scripts-tab") ""
		on btn_help_runPostTaskScript pressed do ShellLaunch (SMTD_HelpURL + "#scripts-tab") ""

		on chk_runPreJobScript changed state do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "RunPreJobScript" ( (SMTDSettings.RunPreJobScript = state) as string)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Run Pre-Job Script set to [" + state as string + "].")
		)

		on chk_runPostJobScript changed state do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "RunPostJobScript" ( (SMTDSettings.RunPostJobScript = state) as string)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Run Post-Job Script set to [" + state as string + "].")
		)

		on chk_runPreTaskScript changed state do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "RunPreTaskScript" ( (SMTDSettings.RunPreTaskScript = state) as string)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Run Pre-Task Script set to [" + state as string + "].")
		)

		on chk_runPostTaskScript changed state do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "RunPostTaskScript" ( (SMTDSettings.RunPostTaskScript = state) as string)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Run Post-Task Script set to [" + state as string + "].")
		)

		on edt_PreJobScript entered txt do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "PreJobScriptFile" (SMTDSettings.PreJobScriptFile = txt)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Pre-Job Script Path ENTERED as [" + txt + "].") LogFileOnly:true
		)

		on btn_getPreJobScript pressed do
		(
			local theFile = getOpenFileName caption:"Select PRE-Job Script File" types:"Python File (*.py)|*.py|All Files (*.*)|*.*"
			if theFile != undefined do
			(
				setIniSetting SMTDPaths.InIFile "Scripts"  "RunPreJobScript" ( (chk_runPreJobScript.state = SMTDSettings.RunPreJobScript = true) as string)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Run Pre-Job Script ENABLED automatically.")
				setIniSetting SMTDPaths.InIFile "Scripts"  "PreJobScriptFile" (edt_PreJobScript.text = SMTDSettings.PreJobScriptFile = theFile)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Pre-Job Script Path PICKED as [" + theFile+ "].") LogFileOnly:true
			)
		)

		on edt_PostJobScript entered txt do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "PostJobScriptFile" (SMTDSettings.PostJobScriptFile = txt)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Post-Job Script Path ENTERED as [" + txt + "].") LogFileOnly:true
		)

		on btn_getPostJobScript pressed do
		(
			local theFile = getOpenFileName caption:"Select POST-Job Script File" types:"Python File (*.py)|*.py|All Files (*.*)|*.*"
			if theFile != undefined do
			(
				setIniSetting SMTDPaths.InIFile "Scripts"  "RunPostJobScript" ( (chk_runPostJobScript.state = SMTDSettings.RunPostJobScript = true) as string)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Run Post-Job Script ENABLED automatically.")
				setIniSetting SMTDPaths.InIFile "Scripts"  "PostJobScriptFile" (edt_PostJobScript.text = SMTDSettings.PostJobScriptFile = theFile)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Post-Job Script Path PICKED as [" + theFile+ "].") LogFileOnly:true
			)
		)

		on edt_PreTaskScript entered txt do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "PreTaskScriptFile" (SMTDSettings.PreTaskScriptFile = txt)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Pre-Task Script Path ENTERED as [" + txt + "].") LogFileOnly:true
		)

		on btn_getPreTaskScript pressed do
		(
			local theFile = getOpenFileName caption:"Select PRE-Task Script File" types:"Python File (*.py)|*.py|All Files (*.*)|*.*"
			if theFile != undefined do
			(
				setIniSetting SMTDPaths.InIFile "Scripts"  "RunPreTaskScript" ( (chk_runPreTaskScript.state = SMTDSettings.RunPreTaskScript = true) as string)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Run Pre-Task Script ENABLED automatically.")
				setIniSetting SMTDPaths.InIFile "Scripts"  "PreTaskScriptFile" (edt_PreTaskScript.text = SMTDSettings.PreTaskScriptFile = theFile)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Pre-Task Script Path PICKED as [" + theFile+ "].") LogFileOnly:true
			)
		)

		on edt_PostTaskScript entered txt do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "PostTaskScriptFile" (SMTDSettings.PostTaskScriptFile = txt)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Post-Task Script Path ENTERED as [" + txt + "].") LogFileOnly:true
		)

		on btn_getPostTaskScript pressed do
		(
			local theFile = getOpenFileName caption:"Select POST-Task Script File" types:"Python File (*.py)|*.py|All Files (*.*)|*.*"
			if theFile != undefined do
			(
				setIniSetting SMTDPaths.InIFile "Scripts"  "RunPostTaskScript" ( (chk_runPostTaskScript.state = SMTDSettings.RunPostTaskScript = true) as string)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Run Post-Task Script ENABLED automatically.")
				setIniSetting SMTDPaths.InIFile "Scripts"  "PostTaskScriptFile" (edt_PostTaskScript.text = SMTDSettings.PostTaskScriptFile = theFile)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Post-Task Script Path PICKED as [" + theFile+ "].") LogFileOnly:true
			)
		)
		fn updateRolloutTitle state =
		(
			local theTitle = "Run Python Scripts"
			if not state do
			(
				hasScripts = false
				if SMTDSettings.RunPreJobScript  and SMTDSettings.PreJobScriptFile != "" do (theTitle += " [PreJob]"; hasScripts = true)
				if SMTDSettings.RunPostJobScript  and SMTDSettings.PostJobScriptFile != "" do (theTitle += " [PostJob]"; hasScripts = true)
				if SMTDSettings.RunPreTaskScript  and SMTDSettings.PreTaskScriptFile != "" do (theTitle += " [PreTask]"; hasScripts = true)
				if SMTDSettings.RunPostTaskScript  and SMTDSettings.PostTaskScriptFile != "" do (theTitle += " [PostTask]"; hasScripts = true)
				if not hasScripts do theTitle = "Run Python Scripts [None]"
			)
			SMTD_PythonScripts.title = theTitle
		)

		on SMTD_PythonScripts rolledup state do
		(
			updateRolloutTitle state
		)
		on SMTD_PythonScripts open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening Run Python Scripts Rollout"
			chk_runPreJobScript.state =		SMTDSettings.RunPreJobScript
			chk_runPostJobScript.state = 	SMTDSettings.RunPostJobScript
			chk_runPreTaskScript.state = 	SMTDSettings.RunPreTaskScript
			chk_runPostTaskScript.state = 	SMTDSettings.RunPostTaskScript

			edt_PreJobScript.text = 		SMTDSettings.PreJobScriptFile
			edt_PostJobScript.text = 		SMTDSettings.PostJobScriptFile
			edt_PreTaskScript.text = 		SMTDSettings.PreTaskScriptFile
			edt_PostTaskScript.text = 		SMTDSettings.PostTaskScriptFile

			chk_runPreJobScript.caption = SMTDFunctions.getStickyCaption "Scripts" "RunPreJobScript"   "Run Pre-Job Script  "
			chk_runPostJobScript.caption = SMTDFunctions.getStickyCaption "Scripts" "RunPostJobScript"   "Run Post-Job Script  "
			chk_runPreTaskScript.caption = SMTDFunctions.getStickyCaption "Scripts" "RunPreTaskScript"   "Run Pre-Task Script  "
			chk_runPostTaskScript.caption = SMTDFunctions.getStickyCaption "Scripts" "RunPostTaskScript"   "Run Post-Task Script  "

			updateRolloutTitle SMTD_PythonScripts.open
		)
	)

	rollout SMTD_RunScripts "Run Maxscript Scripts"
	(
		group "MAXScript Scene Processing Job - No Rendering"
		(
			checkbox chk_SubmitAsMXSJob "Submit Script Job*" align:#left checked:false offset:[-6,0] across:2 \
				tooltip:"When checked, the Job will be submitted as a MAXScript Job.\n\nIt will use the current scene but won't launch the renderer, instead it will run the specified MAXScript."
			checkbox chk_SingleTaskJob "Single Task*" align:#left checked:false offset:[-40,0] \
				tooltip:"When checked, the Job will contain a single task.\n\nThe MAXScript will thus be run just once.\n\nWhen unchecked, one task per frame will be created and the MAXScript will run once per task. It can query the current frame to perform a different operation accordingly."

			checkbox chk_forceWorkstationMode "Workstation Mode*" align:#left checked:false offset:[-6,0] across:2 \
				tooltip:"When checked, the Job will run in Workstation Mode. This will launch 3ds Max with the UI enabled and will require a 3ds Max license.\n\nWhen unchecked, the Job will be run in Slave mode. Many MAXScript functions, esp. those related to UI interaction and file operations will not be available."
			checkbox chk_popupHandling "Popup Handling*" aligh:#left checked:true offset:[-40,0] \
				tooltip:"When checked, Popups will be handled automatically.\n\nWhen unchecked, no popup handling will be performed."

			edittext edt_MAXScriptFile text:"" offset:[-10,-3] width:475

			button btn_getFromTemplate "New Script From Template" align:#left across:3 width:156 height:18 offset:[-5,-3] \
				tooltip:"Get a new MAXScript File from Template."
			button btn_getMAXScript  "Pick Script..." align:#center width:156 height:18 offset:[0,-3] \
				tooltip:"Pick an Existing MAXScript File From Disk."
			button btn_editMAXScript "Edit MAXScript File" align:#right width:156 height:18 offset:[5,-3] \
				tooltip:"Create a NEW MAXScript File from Template."
		)

		group "Render Job - Load/Frame Pre/Post Scripts"
		(
			checkbox chk_runPreLoadScript "Run Pre-Load Script*" align:#left checked:false offset:[-6,0] across:2 \
				tooltip:"When checked, the specified Pre-Load script will be executed before the 3ds Max scene is loaded for rendering."
			button btn_getPreLoadScript "Pick Pre-Load Script..." align:#right width:150 height:18 offset:[5,-3] tooltip:"Pick a Pre-Load Script File."
			edittext edt_PreLoadScript text:"" offset:[-10,-5] width:475

			checkbox chk_runPostLoadScript "Run Post-Load Script*" align:#left checked:false offset:[-6,0] across:2 \
				tooltip:"When checked, the specified Post-Load script will be executed after the 3ds Max scene has been loaded for rendering.\n\nYou can think of this script as 'Pre-Render'."
			button btn_getPostLoadScript "Pick Post-Load Script..." align:#right width:150 height:18 offset:[5,-3] tooltip:"Pick a Post-Load Script File."
			edittext edt_PostLoadScript text:"" offset:[-10,-5] width:475


			checkbox chk_runPreFrameScript "Run Pre-Frame Script*" align:#left checked:false offset:[-6,0] across:2 \
				tooltip:"When checked, the specified Pre-Frame script will be executed before each frame is rendered.\n\nNote that you cannot modify the content of the scene or the settings of the renderer at this point."
			button btn_getPreFrameScript "Pick Pre-Frame Script..." align:#right width:150 height:18 offset:[5,-3] tooltip:"Pick a Pre-Frame Script File."
			edittext edt_PreFrameScript text:"" offset:[-10,-5] width:475


			checkbox chk_runPostFrameScript "Run Post-Frame Script*" align:#left checked:false offset:[-6,0] across:2 \
				tooltip:"When checked, the specified Post-Frame script will be executed after each frame is rendered."

			button btn_getPostFrameScript "Pick Post-Frame Script..." align:#right width:150 height:18 offset:[5,-3] tooltip:"Pick a Post-Frame Script File."
			edittext edt_PostFrameScript text:"" offset:[-10,-5] width:475
		)

		on btn_help_SubmitAsMXSJob pressed do ShellLaunch (SMTD_HelpURL + "#scripts-tab") ""
		on btn_help_runPreLoadScript pressed do ShellLaunch (SMTD_HelpURL + "#scripts-tab") ""
		on btn_help_runPostLoadScript pressed do ShellLaunch (SMTD_HelpURL + "#scripts-tab") ""
		on btn_help_runPreFrameScript pressed do ShellLaunch (SMTD_HelpURL + "#scripts-tab") ""
		on btn_help_runPostFrameScript pressed do ShellLaunch (SMTD_HelpURL + "#scripts-tab") ""

		group "Post-Submission Function Call"
		(
			edittext edt_PostSubmissionScript text:"" offset:[-10,-5] width:475
		)

		on edt_PostSubmissionScript entered txt do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "PostSubmissionFunction" txt
		)


		on btn_editMAXScript pressed do
		(
			if doesFileExist SMTDSettings.MAXScriptFile do edit SMTDSettings.MAXScriptFile
		)

		on chk_SingleTaskJob changed state do
		(
			SMTDSettings.SingleTaskJob = state
			SMTD_MainRollout.Ui_report ("+Run Scripts: Single Task Job set to [" + state as string + "] for this session. Not Sticky.")
		)

		on chk_popupHandling changed state do
		(
			SMTDSettings.PopupHandling = state
			SMTD_MainRollout.UI_report ("+Run Scripts: Popup Handling set to [" + state as string + "] for this session. Not Sticky.")
		)

		on btn_getFromTemplate pressed do
		(
			local q = true
			if SMTDSettings.MAXScriptFile != "" then
				q = querybox ("Are you sure you want to replace the MAXScript Job File\n[" + SMTDSettings.MAXScriptFile + "]\nwith a new MAXScript File From Template?") title:"New MAXScript Job File From Template?"
			if q then
			(
				local thePath = SMTDPaths.MainSubmissionDir + "\\MAXScriptJobTemplate.ms"
				if doesFileExist thePath then
				(
					local theDir = GetDir #userScripts + "\\SubmitMaxToDeadline"
					makeDir theDir all:true
					local theFileName = theDir + "\\MAXScriptJob_" + getFileNameFile maxFileName + "_" +(random 10000 1000000) as string  +".ms"
					copyFile thePath theFileName
					SMTDSettings.SubmitAsMXSJob = chk_SubmitAsMXSJob.state = true
					edt_MAXScriptFile.text = SMTDSettings.MAXScriptFile = theFileName
					edit theFileName
				)
				else
					SMTD_MainRollout.Ui_report ("--Run Scripts: Template File [MAXScriptJobTemplate.ms] Not Found in the Repository.")
			)
			else
				SMTD_MainRollout.Ui_report ("--Run Scripts: New MAXScript Job File From Template Canceled By User.")
		)

		on chk_SubmitAsMXSJob changed state do
		(
			SMTDSettings.SubmitAsMXSJob = state
			SMTDSettings.TilesRendering = false
			SMTD_MainRollout.Ui_report ("+Run Scripts: Submit Scene as MAXScript Job set to [" + state as string + "] for this session. Not Sticky.")
		)

		on edt_MAXScriptFile entered txt do
		(
			SMTDSettings.MAXScriptFile = txt
			SMTD_MainRollout.Ui_report ("+Run Scripts: MAXScript Job File Path ENTERED as [" + txt + "] for this session. Not Sticky.") LogFileOnly:true
		)

		on btn_getMAXScript  pressed do
		(
			local theDir = GetDir #userScripts + "\\SubmitMaxToDeadline"
			makeDir theDir	 all:true
			local theFile = getOpenFileName filename:(theDir+"\\") caption:"Select MAXScript Job File" types:"MAXScript File (*.ms)|*.ms|All Files (*.*)|*.*"
			if theFile != undefined do
			(
				edt_MAXScriptFile.text = SMTDSettings.MAXScriptFile = theFile
				chk_SubmitAsMXSJob.state = true
				SMTDSettings.SubmitAsMXSJob = true
				SMTD_MainRollout.Ui_report ("+Run Scripts: MAXScript Job File Path PICKED as [" + theFile+ "] for this session. Not Sticky.")
				SMTD_MainRollout.Ui_report ("+Run Scripts: MAXScript Job ENABLED automatically for this session. Not Sticky.")
			)
		)

		on chk_ForceWorkstationMode changed state do
		(
			SMTDSettings.ForceWorkstationMode = state
			SMTD_MainRollout.Ui_report ("+Run Scripts: Workstation Mode set to [" + state as string + "] for this session. Not Sticky.")
		)

		on chk_runPreLoadScript changed state do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "RunPreLoadScript" ( (SMTDSettings.RunPreLoadScript = state) as string)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Run Pre-Load Script set to [" + state as string + "].")
		)

		on chk_runPostLoadScript changed state do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "RunPostLoadScript" ( (SMTDSettings.RunPostLoadScript = state) as string)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Run Post-Load Script set to [" + state as string + "].")
		)

		on chk_runPreFrameScript changed state do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "RunPreFrameScript" ( (SMTDSettings.RunPreFrameScript = state) as string)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Run Pre-Frame Script set to [" + state as string + "].")
		)

		on chk_runPostFrameScript changed state do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "RunPostFrameScript" ( (SMTDSettings.RunPostFrameScript = state) as string)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Run Post-Frame Script set to [" + state as string + "].")
		)

		on edt_PreLoadScript entered txt do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "PreLoadScriptFile" (SMTDSettings.PreLoadScriptFile = txt)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Pre-Load Script Path ENTERED as [" + txt + "].") LogFileOnly:true
		)

		on btn_getPreLoadScript pressed do
		(
			local theFile = getOpenFileName caption:"Select PRE-Load Script File" types:"MAXScript File (*.ms)|*.ms|All Files (*.*)|*.*"
			if theFile != undefined do
			(
				setIniSetting SMTDPaths.InIFile "Scripts"  "RunPreLoadScript" ( (chk_runPreLoadScript.state = SMTDSettings.RunPreLoadScript = true) as string)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Run Pre-Load Script ENABLED automatically.")
				setIniSetting SMTDPaths.InIFile "Scripts"  "PreLoadScriptFile" (edt_PreLoadScript.text = SMTDSettings.PreLoadScriptFile = theFile)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Pre-Load Script Path PICKED as [" + theFile+ "].") LogFileOnly:true
			)
		)

		on edt_PostLoadScript entered txt do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "PostLoadScriptFile" (SMTDSettings.PostLoadScriptFile = txt)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Post-Load Script Path ENTERED as [" + txt + "].") LogFileOnly:true
		)

		on btn_getPostLoadScript pressed do
		(
			local theFile = getOpenFileName caption:"Select POST-Load Script File" types:"MAXScript File (*.ms)|*.ms|All Files (*.*)|*.*"
			if theFile != undefined do
			(
				setIniSetting SMTDPaths.InIFile "Scripts"  "RunPostLoadScript" ( (chk_runPostLoadScript.state = SMTDSettings.RunPostLoadScript = true) as string)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Run Post-Load Script ENABLED automatically.")
				setIniSetting SMTDPaths.InIFile "Scripts"  "PostLoadScriptFile" (edt_PostLoadScript.text = SMTDSettings.PostLoadScriptFile = theFile)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Post-Load Script Path PICKED as [" + theFile+ "].") LogFileOnly:true
			)
		)

		on edt_PreFrameScript entered txt do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "PreFrameScriptFile" (SMTDSettings.PreFrameScriptFile = txt)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Pre-Frame Script Path ENTERED as [" + txt + "].") LogFileOnly:true
		)

		on btn_getPreFrameScript pressed do
		(
			local theFile = getOpenFileName caption:"Select PRE-Frame Script File" types:"MAXScript File (*.ms)|*.ms|All Files (*.*)|*.*"
			if theFile != undefined do
			(
				setIniSetting SMTDPaths.InIFile "Scripts"  "RunPreFrameScript" ( (chk_runPreFrameScript.state = SMTDSettings.RunPreFrameScript = true) as string)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Run Pre-Frame Script ENABLED automatically.")
				setIniSetting SMTDPaths.InIFile "Scripts"  "PreFrameScriptFile" (edt_PreFrameScript.text = SMTDSettings.PreFrameScriptFile = theFile)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Pre-Frame Script Path PICKED as [" + theFile+ "].") LogFileOnly:true
			)
		)

		on edt_PostFrameScript entered txt do
		(
			setIniSetting SMTDPaths.InIFile "Scripts"  "PostFrameScriptFile" (SMTDSettings.PostFrameScriptFile = txt)
			SMTD_MainRollout.Ui_report ("+Run Scripts: Post-Frame Script Path ENTERED as [" + txt + "].") LogFileOnly:true
		)

		on btn_getPostFrameScript pressed do
		(
			local theFile = getOpenFileName caption:"Select POST-Frame Script File" types:"MAXScript File (*.ms)|*.ms|All Files (*.*)|*.*"
			if theFile != undefined do
			(
				setIniSetting SMTDPaths.InIFile "Scripts"  "RunPostFrameScript" ( (chk_runPostFrameScript.state = SMTDSettings.RunPostFrameScript = true) as string)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Run Post-Frame Script ENABLED automaticall.")
				setIniSetting SMTDPaths.InIFile "Scripts"  "PostFrameScriptFile" (edt_PostFrameScript.text = SMTDSettings.PostFrameScriptFile = theFile)
				SMTD_MainRollout.Ui_report ("+Run Scripts: Post-Frame Script Path PICKED as [" + theFile+ "].") LogFileOnly:true
			)
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Run MAXScript Scripts"
			if not state do
			(
				hasScripts = false
				if SMTDSettings.SubmitAsMXSJob and SMTDSettings.MAXScriptFile != "" do (theTitle += " [MXS Job]"; hasScripts=true)
				if SMTDSettings.SingleTaskJob do theTitle += " [1 Task]"
				if SMTDSettings.ForceWorkstationMode do theTitle += " [FWS]"
				if SMTDSettings.PopupHandling do theTitle += " [PUH]"

				if SMTDSettings.RunPreLoadScript  and SMTDSettings.PreLoadScriptFile != "" do (theTitle += " [PreLoad]"; hasScripts=true)
				if SMTDSettings.RunPostLoadScript  and SMTDSettings.PostLoadScriptFile != "" do (theTitle += " [PostLoad]"; hasScripts=true)
				if SMTDSettings.RunPreFrameScript  and SMTDSettings.PreFrameScriptFile != "" do (theTitle += " [PreFrame]"; hasScripts=true)
				if SMTDSettings.RunPostFrameScript  and SMTDSettings.PostFrameScriptFile != "" do (theTitle += " [PostFrame]"; hasScripts=true)
				if not hasScripts do theTitle = "Run MAXScript Scripts [None]"
			)
			SMTD_RunScripts.title = theTitle
		)

		on SMTD_RunScripts rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_RunScripts open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening Run MAXScript Scripts Rollout"
			chk_runPreLoadScript.state =		SMTDSettings.RunPreLoadScript
			chk_runPostLoadScript.state = 	SMTDSettings.RunPostLoadScript
			chk_runPreFrameScript.state = 	SMTDSettings.RunPreFrameScript
			chk_runPostFrameScript.state = 	SMTDSettings.RunPostFrameScript

			edt_PreLoadScript.text = 			SMTDSettings.PreLoadScriptFile
			edt_PostLoadScript.text = 		SMTDSettings.PostLoadScriptFile
			edt_PreFrameScript.text = 		SMTDSettings.PreFrameScriptFile
			edt_PostFrameScript.text = 		SMTDSettings.PostFrameScriptFile

			chk_SubmitAsMXSJob.state = 	SMTDSettings.SubmitAsMXSJob
			edt_MAXScriptFile.text = 			SMTDSettings.MAXScriptFile
			chk_SingleTaskJob.state = 		SMTDSettings.SingleTaskJob
			chk_ForceWorkstationMode.state = SMTDSettings.ForceWorkstationMode
			chk_popupHandling.state = 		SMTDSettings.PopupHandling

			edt_PostSubmissionScript.text = getIniSetting SMTDPaths.InIFile "Scripts"  "PostSubmissionFunction"

			chk_runPreLoadScript.caption = SMTDFunctions.getStickyCaption "Scripts" "RunPreLoadScript"   "Run Pre-Load Script  "
			chk_runPostLoadScript.caption = SMTDFunctions.getStickyCaption "Scripts" "RunPostLoadScript"   "Run Post-Load Script  "
			chk_runPreFrameScript.caption = SMTDFunctions.getStickyCaption "Scripts" "RunPreFrameScript"   "Run Pre-Frame Script  "
			chk_runPostFrameScript.caption = SMTDFunctions.getStickyCaption "Scripts" "RunPostFrameScript"   "Run Post-Frame Script  "

			updateRolloutTitle SMTD_RunScripts.open
		)
	)

	rollout SMTD_BatchSubmit "Batch Submission"
	(
		dropdownlist ddl_batchRenderMode items:#("Submit All Batch Jobs From The Local Workstation","Submit Master Job In Workstation Mode, Spawn Batch Jobs On Deadline") align:#center

		checkbox chk_useBatchRender "Use Data from 3ds Max Batch Render  " across:3 offset:[0,2]
		button btn_openBatchRenderUI "Open Dialog..." align:#right offset:[50,0] width:100
		button btn_updateInfo "Update Info" align:#right width:100

		group "Info"
		(
			label lbl_batch01 ""
		)

		checkbox chk_CleanupSubmissionFoldersAfterEachBatchJob "Cleanup Submission Folders After Each Batch Job  " --offset:[0,2]

		fn updateBatchRenderInfo =
		(
			local numViews = batchRenderMgr.numViews
			local numActiveViews = (for i = 1 to numViews where (batchRenderMgr.getView i).enabled collect i).count
			lbl_batch01.text =  numActiveViews as string  +" of " + numViews  as string + " Views are Enabled."
		)

		on btn_openBatchRenderUI pressed do actionMan.executeAction -43434444 "4096"
		on btn_updateInfo pressed do updateBatchRenderInfo()
		on chk_useBatchRender changed state do
		(
			SMTDSettings.UseBatchRender = state
			setIniSetting SMTDPaths.InIFile "BatchRender" "UseBatchRender" (state as string)
			SMTD_MainRollout.Ui_report ("+Batch Rendering: Use Data from 3ds Max Batch Render set to [" + state as string + "].")
		)

		on ddl_batchRenderMode selected itm do
		(
			SMTDSettings.BatchRenderMode = itm
			setIniSetting SMTDPaths.InIFile "BatchRender" "BatchRenderMode" (itm as string)
			SMTD_MainRollout.Ui_report ("+Batch Rendering Mode set to [" + ddl_batchRenderMode.selected + "].")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Batch Submission"
			if not state do
			(
				local numViews = batchRenderMgr.numViews
				local count = (for i = 1 to numViews where (batchRenderMgr.getView i).enabled collect i).count
				theTitle += (if SMTDSettings.UseBatchRender then " [On, "+count as string+" of "+numViews as string+" Batch View"+(if count == 1 then "" else "s")+" Enabled]" else " [Off]")
				if SMTDSettings.UseBatchRender do
					theTitle += (if SMTDSettings.BatchRenderMode == 1 then " [Local]" else " [Master Job]")
			)
			SMTD_BatchSubmit.title = theTitle
		)

		on chk_CleanupSubmissionFoldersAfterEachBatchJob changed state do
		(
			SMTDSettings.CleanupSubmissionFoldersAfterEachBatchJob = state
			setIniSetting SMTDPaths.InIFile "BatchRender" "CleanupSubmissionFoldersAfterEachBatchJob" (state as string)
			SMTD_MainRollout.Ui_report ("+Batch Rendering: Cleanup Submission Folder After Each Batch Job set to [" + state as string + "].")
		)

		on SMTD_BatchSubmit rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_BatchSubmit open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening Batch Submission Rollout"
			chk_useBatchRender.checked = SMTDSettings.UseBatchRender
			ddl_batchRenderMode.selection = SMTDSettings.BatchRenderMode
			chk_useBatchRender.caption = SMTDFunctions.getStickyCaption "BatchRender" "UseBatchRender"   "Use Data from 3ds Max Batch Render  "
			chk_CleanupSubmissionFoldersAfterEachBatchJob.checked = SMTDSettings.CleanupSubmissionFoldersAfterEachBatchJob
			updateBatchRenderInfo()
			updateRolloutTitle SMTD_BatchSubmit.open
		)
	)--end batch submission rollout

	rollout SMTD_UserDefinedTilesDialog "User-Defined Tiles - Click To Toggle"
	(
		radiobuttons rad_previewImage labels:#("Current Viewport", "Last Rendered Image") columns:2 pos:[5,5]
		button btn_all "All" width:38 pos:[270,2]
		button btn_none "None" width:38 pos:[310,2]
		button btn_invert "Invert" width:38 pos:[350,2]
		--button btn_addSelectedObjects "Add Sel." width:68 pos:[390,2] tooltip:"Adds Tiles based on the bounding boxes of the currently selected scene objects."
		--button btn_removeSelectedObjects "Remove Sel." width:68 pos:[460,2] tooltip:"Removes Tiles based on the bounding boxes of the currently selected scene objects."

		bitmap bmp_tiles width:SMTDSettings.CustomTilesPreviewWidth height:SMTDSettings.CustomTilesPreviewHeight pos:[0,25]

		timer tmr_dialogResizeTimer interval:50

		fn updateTilesDisplay =
		(
			local XFactor = (SMTDSettings.CustomTilesPreviewWidth/SMTDSettings.TilesInX)
			local YFactor = (SMTDSettings.CustomTilesPreviewHeight/SMTDSettings.TilesInY)
			SMTD_UserDefinedTilesBitmapDisplay = copy SMTD_UserDefinedTilesBitmap
			if SMTD_UserDefinedTilesBitmapDisplay != undefined do
			(
				for x = 0 to (SMTDSettings.CustomTilesPreviewWidth-1) by XFactor  do
					for y = 0 to (SMTDSettings.CustomTilesPreviewHeight-1) do
						setPixels SMTD_UserDefinedTilesBitmapDisplay [x,y] #(red)
				thePixels = for i in 0 to (SMTDSettings.CustomTilesPreviewWidth-1) collect red
				for y = 0 to (SMTDSettings.CustomTilesPreviewHeight-1) by YFactor do
						setPixels SMTD_UserDefinedTilesBitmapDisplay [0,y] thePixels
				for coords in SMTDSettings.CustomTiles do
				(
					thePixels = for i in 1 to XFactor collect white
					for y = 0 to YFactor-1 by 2 do
					(
						thePixels = getPixels SMTD_UserDefinedTilesBitmapDisplay [(coords.x-1)*XFactor, (coords.y-1)*YFactor+y] XFactor
						for p = 1 to thePixels.count do
						(
							thePixels[p] /=0.5
							thePixels[p] += white/2
						)
						setPixels SMTD_UserDefinedTilesBitmapDisplay [(coords.x-1)*XFactor, (coords.y-1)*YFactor+y] thePixels
					)
				)
				bmp_tiles.bitmap = SMTD_UserDefinedTilesBitmapDisplay
			)
			SMTD_TilesRendering.updateLabel()
		)

		on SMTD_UserDefinedTilesDialog lbuttonup pos do
		(
			pos += [0,-25]
			coords = pos / [SMTDSettings.CustomTilesPreviewWidth,SMTDSettings.CustomTilesPreviewHeight] * [SMTDSettings.TilesInX, SMTDSettings.TilesInY]
			coords = Point2 ( (ceil coords.x) as integer) ((ceil coords.y) as integer)
			theIndex = findItem SMTDSettings.CustomTiles coords
			if theIndex > 0 then
				deleteItem SMTDSettings.CustomTiles theIndex
			else
				append SMTDSettings.CustomTiles coords
			updateTilesDisplay()
		)

		fn SelectedObjectTiles mode:#add =
		(
			for o in selection do
			(
				local theTM = o.transform
				local XTiles = #()
				local YTiles = #()
				local bbox = nodeGetBoundingBox o theTM
				local theMin = bbox[1]
				local theMax = bbox[2]
				in coordsys theTM
				(
					--gw.setTransform (theTM)
					for v in #(theMin, theMax, [theMin.x,theMin.y,theMax.z], [theMin.x,theMax.y,theMin.z], [theMax.x,theMin.y,theMin.z], [theMin.x,theMax.y,theMax.z], [theMax.x,theMin.y,theMax.z], [theMax.x,theMax.y,theMin.z]) do
					(
						local thePos = v * viewport.getTM()
						local screen_origin = mapScreenToView [0,0] (thePos.z) [SMTDSettings.CustomTilesPreviewWidth,SMTDSettings.CustomTilesPreviewHeight]
						end_screen = mapScreenToView [SMTDSettings.CustomTilesPreviewWidth,SMTDSettings.CustomTilesPreviewHeight] (thePos.z) [SMTDSettings.CustomTilesPreviewWidth,SMTDSettings.CustomTilesPreviewHeight]
						world_size = screen_origin-end_screen
						x_aspect = SMTDSettings.CustomTilesPreviewWidth/(abs world_size.x)
						y_aspect = SMTDSettings.CustomTilesPreviewHeight/(abs world_size.y)
						screen_coords = point2 (x_aspect*(thePos.x-screen_origin.x)) (-(y_aspect*(thePos.y-screen_origin.y)))
						coords = screen_coords / [SMTDSettings.CustomTilesPreviewWidth,SMTDSettings.CustomTilesPreviewHeight] * [SMTDSettings.TilesInX, SMTDSettings.TilesInY]
						coords = Point2 ( (ceil coords.x) as integer) ((ceil coords.y) as integer)
						append XTiles coords.x
						append YTiles coords.y
					)--end v loop
				)
				for x = amin XTiles to amax XTiles do
				(
					for y = amin YTiles to amax YTiles do
					(
						if mode == #add then
						(
							appendIfUnique SMTDSettings.CustomTiles [x,y]
						)
						else
						(
							theIndex = findItem SMTDSettings.CustomTiles [x,y]
							if theIndex > 0 do deleteItem SMTDSettings.CustomTiles theIndex
						)
					)
				)
			)--end o loop
			updateTilesDisplay()
		)

		/*
		on btn_addSelectedObjects pressed do
		(
			SelectedObjectTiles mode:#add
		)
		on btn_removeSelectedObjects pressed do
		(
			SelectedObjectTiles mode:#remove
		)
		*/

		on btn_none pressed do
		(
			SMTDSettings.CustomTiles = #()
			updateTilesDisplay()
		)
		on btn_invert pressed do
		(
			local CustomTiles = #()
			for y = 1 to SMTDSettings.TilesInY do
				for x = 1 to SMTDSettings.TilesInX do
				(
					local theIndex = findItem SMTDSettings.CustomTiles [x,y]
					if theIndex == 0 do append CustomTiles [x,y]
				)
			SMTDSettings.CustomTiles = for i in CustomTiles collect i
			updateTilesDisplay()
		)
		on btn_all pressed do
		(
			SMTDSettings.CustomTiles = #()
			for y = 1 to SMTDSettings.TilesInY do
				for x = 1 to SMTDSettings.TilesInX do
					append SMTDSettings.CustomTiles [x,y]
			updateTilesDisplay()
		)

		fn trimImage capturedImage =
		(
			local theVS = getViewSize()
			local theTargetAspect = 1.0*RenderWidth/RenderHeight*renderPixelAspect
			local theViewAspect = 1.0*theVS.x/theVS.y
			if theViewAspect < theTargetAspect then
			(
				local targetHeight = (theVS.x/theTargetAspect) as integer
				local targetImage  = bitmap theVS.x targetHeight
				local dif = theVS.y - targetHeight
				for i in 0 to targetHeight-1 do
					setPixels targetImage [0,i] (getPixels capturedImage [0,i+dif/2] theVS.x)
				targetImage
			)
			else
			(
				local targetWidth = (theVS.y*theTargetAspect) as integer
				local targetImage  = bitmap targetWidth theVS.y
				local dif = theVS.x - targetWidth
				for i in 0 to (theVS.y - 1) do
					setPixels targetImage [0,i] (getPixels capturedImage [dif/2-1,i] (theVS.x-dif))
				targetImage
			)
		)

		fn updateBitmapDisplay =
		(
			freescenebitmaps()
			gc light:true
			SMTD_UserDefinedTilesBitmap = bitmap SMTDSettings.CustomTilesPreviewWidth SMTDSettings.CustomTilesPreviewHeight
			if rad_previewImage.state == 1 then
			(
				theBmp = trimImage (gw.getViewportDIB())
				copy theBmp SMTD_UserDefinedTilesBitmap
			)
			else
			(
				renderSceneDialog.commit()
				if rendOutputFileName != "" then
				(
					try
					(
						tempBitmap = openBitmap rendOutputFileName
						copy tempBitmap SMTD_UserDefinedTilesBitmap
					)
					catch
					(
						local theFiles = getFiles (getFileNamePath rendOutputFileName + getFileNameFile rendOutputFileName + "*" + getFileNameType rendOutputFileName )
						theFiles = for f in theFiles where not matchPattern f pattern:"*_tile_*" collect f
						if theFiles.count > 0 then  --FIX ME - Load Current Frame If Possible
							try( copy (openBitmap theFiles[1]) SMTD_UserDefinedTilesBitmap)catch()
					)
				)
				else
				(
					copy (getLastRenderedImage()) SMTD_UserDefinedTilesBitmap
				)
			)
			updateTilesDisplay()
		)
--

		on rad_previewImage changed state do
			updateBitmapDisplay()

		on tmr_dialogResizeTimer tick do
		(
			updateBitmapDisplay()
			tmr_dialogResizeTimer.active = false
		)

		fn DialogResized newSize =
		(
			SMTDSettings.CustomTilesPreviewWidth = newSize.x
			SMTDSettings.CustomTilesPreviewHeight = newSize.y-30

			bmp_tiles.width = SMTDSettings.CustomTilesPreviewWidth
			bmp_tiles.height = SMTDSettings.CustomTilesPreviewHeight

			tmr_dialogResizeTimer.active = false
			tmr_dialogResizeTimer.active = true
		)

		on SMTD_UserDefinedTilesDialog resized newsize do
		(
			DialogResized newsize
			setIniSetting SMTDPaths.InIFile "TilesRendering"  "CustomTilesPreviewWidth" (newsize.x as string)
			setIniSetting SMTDPaths.InIFile "TilesRendering"  "CustomTilesPreviewHeight" ((newsize.y-30) as string)
		)

		on SMTD_UserDefinedTilesDialog open do
		(
			renderSceneDialog.commit()
			SMTD_MainRollout.Ui_report (">Tiles Rendering: Opening User Tiles Dialog...")
			DialogResized [SMTDSettings.CustomTilesPreviewWidth,SMTDSettings.CustomTilesPreviewHeight+30]
			updateBitmapDisplay()
		)
		on SMTD_UserDefinedTilesDialog close do
		(
			SMTD_MainRollout.Ui_report (">Tiles Rendering: Closing User Tiles Dialog.")
			SMTD_MainRollout.Ui_report ("+Tiles Rendering: Custom Tiles: " + SMTDSettings.CustomTiles as string )
			try(SMTD_TilesRendering.chk_toggleUserTilesDialog.state = false)catch()
		)
	)

	rollout SMTD_TileOptions "Tiles & Region Rendering Options"
	(
		local renderingModesEnums = #(#none, #singleFrameMultiRegion, #animationMultiRegion, #singleFrameTiles, #maxRegion)
		dropdownlist ddl_RegionRenderingMode items:#(
			"FULL FRAME Rendering, All Region Options DISABLED",
			"SINGLE FRAME, MULTI-REGION 'Jigsaw' Rendering - Single Job, Regions As Tasks",
			"ANIMATION, MULTI-REGION 'Jigsaw' Rendering - One Job Per Region, Frames As Tasks",
			"SINGLE FRAME TILE Rendering - Single Job, Tiles As Tasks",
			"3DS MAX REGION Rendering - Single Job, Frames As Tasks"
		) width:466 align:#center offset:[0,-4]

		checkbox chk_singleTileJobCleanup "Cleanup Tiles After Assembly  " across:2 align:#left offset:[0,-3] tooltip:"When checked, the single frame partial images will be deleted after a successfull assembly.\n\nWhen unchecked, the partial images will be left for later reuse (e.g. via 'Specify Tiles To Rerender' option) or for future reference."
		spinner spn_tilePadding "Pixel Padding: " range:[0,200,0] type:#integer fieldwidth:35 align:#right offset:[0,-3] tooltip:"Pad the rendered Region with pixels on all sides to introduce an overlapping safety region during assembly."
		checkbox chk_MultiRegionCopyDraftConfig "Copy Draft Config Files To Output Folder  " across:2 align:#left offset:[0,-3] tooltip:"When checked, the Draft Asssembly configuration files will be copied as a backup / reference to the Render Output Folder."
		checkbox chk_singleTileJobDraftErrorOnMissing "Draft Assembly Job Error On Missing Tiles  " offset:[10,-3] align:#right tooltip:"When checked, the Draft Assembly Job will fail if there are missing tiles.\n\nWhen unchecked, the Draft Assembly job will assemble the existing fragments and ignore any missing ones without an error."

		group "Assembler Pool, Group and Priority:"
		(
			checkbox chk_assemblerOverride "Override Pool, Group, Priority for Assembly Job  " across:1 align:#left offset:[0,-2] tooltip: "When checked, the Assembly job will use these pool, secondary pool (optional), group (optional), priority settings."

			button btn_assembler_pools_help "Pool: " align:#left across:4 width:55 height:20  offset:[-6,-3] border:false tooltip:"The POOL lets you group Jobs together, typically on per-Project basis. It also controls the Job Priority -- the order in which a Slave is assigned to Pools matters!\n\nOnly Slaves assigned to the selected Pool will be allowed to pick up the job.\n\nIf 'none' is specified as Pool, any Slave can render it if it has no other jobs in assigned Pools to work on."
			dropdownList ddl_assembler_poollist "" width:170 align:#right offset:[-12,-3] tooltip:"The POOL lets you group Jobs together, typically on per-Project basis. It also controls the Job Priority -- the order in which a Slave is assigned to Pools matters!\n\nOnly Slaves assigned to the selected Pool will be allowed to pick up the job.\n\nIf 'none' is specified as Pool, any Slave can render it if it has no other jobs in assigned Pools to work on."

			button btn_assembler_pools2_help "Secondary: " align:#left width:65 height:20  offset:[-8,-3] border:false tooltip:"The SECONDARY POOL lets you specify a Pool to use if the primary Pool does not have any available Slaves.\n\nTo DISABLE this feature, ensure you select the EMPTY entry at the top of the list!"
			dropdownList ddl_assembler_pool2list "" width:175 align:#right offset:[5,-3] tooltip:"The SECONDARY POOL lets you specify a Pool to use if the primary Pool does not have any available Slaves.\n\nTo DISABLE this feature, ensure you select the EMPTY entry at the top of the list!"

			button btn_assembler_group_help "Group: " align:#left across:2 width:55 height:20 offset:[-6,-4] border:false tooltip:"The GROUP lets you limit the job to only specific machines, typically based on hardware or installed software characteristics.\n\nSelect the 'none' Group to turn off Group filtering."
			dropdownlist ddl_assembler_group items:#() align:#right width:417 offset:[5,-4] height:20 tooltip:"The GROUP lets you limit the job to only specific machines, typically based on hardware or installed software characteristics.\n\nSelect the 'none' Group to turn off Group filtering."

			button btn_assembler_priority_help "Priority: " align:#left across:3 width:55 height:18 offset:[-6,-4] border:false tooltip:"Left-click slider to set value.\nHold and drag to adjust.\n\nHold CTRL and roll mouse over without left-clicking.\n\nHold SHIFT and roll mouse over to snap by 10."
			progressbar sld_assembler_priority width:368 height:18 range:[0,100,50] type:#integer align:#center offset:[3,-4]
			spinner spn_assembler_priority "" type:#integer fieldwidth:38 align:#right offset:[5,-3] range:[0,100,50]
		)

		fn assembler_job_priority_update val =
		(
			if (val > SMTDSettings.MaximumPriority) do (val = (SMTDSettings.MaximumPriority / 2))

			--if val <= SMTDSettings.MaximumPriority do
			(
				if keyboard.shiftPressed do val = ((floor(val/10.0))*10.0) as integer
				theRed = (255.0 - 255.0*val/(SMTDSettings.MaximumPriority as float))*2.0
				if theRed > 255 do theRed = 255
				theGreen = 512.0*val/(SMTDSettings.MaximumPriority as float)
				if theGreen > 255 do theGreen = 255

				spn_assembler_priority.value = val

				sld_assembler_priority.color = [theRed, theGreen, 0]
				sld_assembler_priority.value = (val * 100) / SMTDSettings.MaximumPriority
			)
			val
		)

		fn displayAssemblerPoolsList =
		(
			ddl_assembler_poollist.items = SMTDSettings.Pools
			ddl_assembler_pool2list.items = (join #("") SMTDSettings.Pools)

			local theIndex = findItem ddl_assembler_poollist.items SMTDSettings.AssemblerPoolName
			if theIndex > 0 then
				ddl_assembler_poollist.selection = theIndex
			else
			(
				theIndex = findItem ddl_assembler_poollist.items "none"
				if theIndex > 0 do
				(
					ddl_assembler_poollist.selection = theIndex
					SMTDSettings.AssemblerPoolName = "none"
				)
			)

			local theIndex = findItem ddl_assembler_pool2list.items SMTDSettings.AssemblerPool2Name
			if theIndex > 0 then
				ddl_assembler_pool2list.selection = theIndex
			else
			(
				ddl_assembler_pool2list.selection = 1
				SMTDSettings.AssemblerPool2Name = ""
			)
		)

		fn displayAssemblerGroupsList =
		(
			ddl_assembler_group.items = SMTDSettings.Groups

			local theIndex = findItem ddl_assembler_group.items SMTDSettings.AssemblerGroup
			if theIndex > 0 then
				ddl_assembler_group.selection = theIndex
			else
			(
				theIndex = findItem ddl_assembler_group.items "none"
				if theIndex > 0 do
				(
					ddl_assembler_group.selection = theIndex
					SMTDSettings.AssemblerGroup = "none"
				)
			)
		)

		fn updateRolloutRollupStates =
		(
			local itm = ddl_RegionRenderingMode.selection
			case of
			(
				(itm==1): (
					SMTD_MultiRegionRendering.open = SMTD_RegionRendering.open = SMTD_TilesRendering.open = false
					SMTD_MultiRegionRendering.title = "'Jigsaw' Multi-Region Rendering"
					SMTD_RegionRendering.title = "3ds Max Region Rendering"
					SMTD_TilesRendering.title = "Tile Rendering"
				)
				(itm ==2 or itm == 3): (
					SMTD_MultiRegionRendering.open = true
					SMTD_RegionRendering.open = SMTD_TilesRendering.open = false
					SMTD_MultiRegionRendering.title = "ACTIVE: 'Jigsaw' "+(if itm ==2 then "Single-Frame " else "Animation ")+"Multi-Region Rendering"
					SMTD_RegionRendering.title = "3ds Max Region Rendering"
					SMTD_TilesRendering.title = "Tile Rendering"

				)
				(itm ==4): (
					SMTD_MultiRegionRendering.open = SMTD_RegionRendering.open = false
					SMTD_TilesRendering.open = true
					SMTD_MultiRegionRendering.title = "'Jigsaw' Multi-Region Rendering"
					SMTD_RegionRendering.title = "3ds Max Region Rendering"
					SMTD_TilesRendering.title = "ACTIVE: "+(if itm ==4 then "Single-Frame " else "Animation ")+"Tile Rendering"
				)
				(itm == 5):
				(
					SMTD_MultiRegionRendering.open = SMTD_TilesRendering.open = false
					SMTD_RegionRendering.open = true
					SMTD_MultiRegionRendering.title = "'Jigsaw' Multi-Region Rendering"
					SMTD_RegionRendering.title = "ACTIVE: 3ds Max "+(#("","Crop ","Blowup ")[SMTDSettings.RegionType])+"Region Rendering"
					SMTD_TilesRendering.title = "Tile Rendering"
				)
			)
		)

		fn updateControls =
		(
			spn_tilePadding.value = SMTDSettings.TilesPadding
			--chk_singleTileJob.state = SMTDSettings.SingleTileJob
			chk_MultiRegionCopyDraftConfig.state = SMTDSettings.MultiRegionCopyDraftConfig
			chk_singleTileJobDraftErrorOnMissing.state = SMTDSettings.SingleTileJobDraftErrorOnMissing
			chk_singleTileJobCleanup.state = SMTDSettings.SingleTileJobCleanup
			chk_assemblerOverride.state = SMTDSettings.AssemblerOverride

			local theIndex = findItem renderingModesEnums SMTDSettings.RegionRenderingMode
			if theIndex == 0 do theIndex = 1
			ddl_RegionRenderingMode.selection = theIndex
			updateRolloutRollupStates()

			chk_MultiRegionCopyDraftConfig.enabled = chk_singleTileJobDraftErrorOnMissing.enabled = chk_singleTileJobCleanup.enabled = (SMTDSettings.RegionRenderingMode == #singleFrameTiles AND SMTDSettings.SingleTileJobDependent) OR SMTDSettings.RegionRenderingMode == #singleFrameMultiRegion OR SMTDSettings.RegionRenderingMode ==  #animationMultiRegion --(SMTDSettings.SingleTileJob AND SMTDSettings.SingleTileJobDependent) OR SMTDSettings.MultiRegionRendering

			if (SMTDSettings.RegionRenderingMode == #singleFrameTiles AND SMTDSettings.SingleTileJobDependent) OR SMTDSettings.RegionRenderingMode == #singleFrameMultiRegion OR SMTDSettings.RegionRenderingMode ==  #animationMultiRegion then
			(
				chk_assemblerOverride.enabled = true
				if chk_assemblerOverride.state then
				(
					btn_assembler_pools_help.enabled = ddl_assembler_poollist.enabled = btn_assembler_pools2_help.enabled = ddl_assembler_pool2list.enabled = btn_assembler_group_help.enabled = ddl_assembler_group.enabled = btn_assembler_priority_help.enabled = sld_assembler_priority.enabled = spn_assembler_priority.enabled = true
				)
				else
				(
					btn_assembler_pools_help.enabled = ddl_assembler_poollist.enabled = btn_assembler_pools2_help.enabled = ddl_assembler_pool2list.enabled = btn_assembler_group_help.enabled = ddl_assembler_group.enabled = btn_assembler_priority_help.enabled = sld_assembler_priority.enabled = spn_assembler_priority.enabled = false
				)

			)
			else
			(
				chk_assemblerOverride.enabled = false
				btn_assembler_pools_help.enabled = ddl_assembler_poollist.enabled = btn_assembler_pools2_help.enabled = ddl_assembler_pool2list.enabled = btn_assembler_group_help.enabled = ddl_assembler_group.enabled = btn_assembler_priority_help.enabled = sld_assembler_priority.enabled = spn_assembler_priority.enabled = false
			)

			if SMTDSettings.MaximumPriority == -1 do
			(
				SMTDFunctions.GetMaximumPriority()
				spn_priority.range = [0,SMTDSettings.MaximumPriority,SMTDSettings.MaximumPriority / 2]
			)
			assembler_job_priority_update SMTDSettings.AssemblerPriority

			if SMTDSettings.Pools.count == 0 do SMTDFunctions.CollectPools()
			displayAssemblerPoolsList()

			if SMTDSettings.Groups.count == 0 do SMTDFunctions.CollectGroups()
			displayAssemblerGroupsList()

			btn_assembler_pools_help.text = SMTDFunctions.getStickyCaption "AssemblerSettings" "Assembler Pool" "Pool: "
			btn_assembler_pools2_help.text = SMTDFunctions.getStickyCaption "AssemblerSettings" "Assembler Secondary Pool" "Secondary: "
			btn_assembler_group_help.text = SMTDFunctions.getStickyCaption "AssemblerSettings" "Assembler Group" "Group: "
			btn_assembler_priority_help.text = SMTDFunctions.getStickyCaption "AssemblerSettings" "Assembler Priority" "Priority: "

			SMTD_TilesRendering.updateControls()
		)

		on ddl_RegionRenderingMode selected itm do
		(
			setIniSetting SMTDPaths.InIFile "MultiRegionRendering"  "RegionRenderingMode" ( (SMTDSettings.RegionRenderingMode = renderingModesEnums[itm]) as string)
			SMTD_MainRollout.Ui_report ("+Tile/Region Rendering Mode set to [" + ddl_RegionRenderingMode.selected + "]")
			updateRolloutRollupStates()
			updateControls()
			SMTD_MainRollout.updateSubmitButtonState()
		)

		on spn_tilePadding changed val do
		(
			setIniSetting SMTDPaths.InIFile "TilesRendering"  "TilesPadding" ( (SMTDSettings.TilesPadding = spn_tilePadding.value) as string)
			SMTD_MainRollout.Ui_report ("+Tile/Region Rendering: Tiles Pixel Padding set to [" + spn_tilePadding.value as string + "]")
		)

		on chk_MultiRegionCopyDraftConfig changed state do
		(
			setIniSetting SMTDPaths.InIFile "MultiRegionRendering" "MultiRegionCopyDraftConfig " ( (SMTDSettings.MultiRegionCopyDraftConfig = state) as string)
			SMTD_MainRollout.Ui_report ("+Tile/Region Rendering: Copy Draft Config Files To Output Folder set to [" + state as string + "].")
		)

		/*
		on chk_singleTileJob changed state do
		(
			setIniSetting SMTDPaths.InIFile "TilesRendering" "SingleTileJob" ( (SMTDSettings.SingleTileJob = state) as string)
			SMTD_MainRollout.Ui_report ("+Tile/Region Rendering: Single Tile Job set to [" + state as string + "].")

			updateControls()
			SMTD_TilesRendering.updateControls()
		)*/

		on chk_singleTileJobCleanup changed state do
		(
			setIniSetting SMTDPaths.InIFile "TilesRendering" "SingleTileJobCleanup" ( (SMTDSettings.SingleTileJobCleanup = state) as string)
			SMTD_MainRollout.Ui_report ("+Tile/Region Rendering: Single Tile Cleanup Assembly Job set to [" + state as string + "].")

			updateControls()
		)

		on chk_singleTileJobDraftErrorOnMissing changed state do
		(
			setIniSetting SMTDPaths.InIFile "TilesRendering" "SingleTileJobDraftErrorOnMissing" ( (SMTDSettings.SingleTileJobDraftErrorOnMissing = state) as string)
			SMTD_MainRollout.Ui_report ("+Tile/Region Rendering: Draft Job Error On Missing set to [" + state as string + "].")

			updateControls()
		)

		on chk_assemblerOverride changed state do
		(
			setIniSetting SMTDPaths.InIFile "AssemblerSettings" "AssemblerOverride" ( (SMTDSettings.AssemblerOverride = state) as string)
			SMTD_MainRollout.Ui_report ("+Tile/Region Rendering: Assembler Override set to [" + state as string + "].")

			updateControls()
		)

		on ddl_assembler_poollist selected itm do
		(
			setIniSetting SMTDPaths.InIFile "AssemblerSettings" "AssemblerPoolName" ( (SMTDSettings.AssemblerPoolName = ddl_assembler_poollist.selected) as string )
			SMTD_MainRollout.Ui_report ("+Assembler Pool changed to ["+SMTDSettings.AssemblerPoolName+"]")
			displayAssemblerPoolsList()
		)

		on ddl_assembler_pool2list selected itm do
		(
			setIniSetting SMTDPaths.InIFile "AssemblerSettings" "AssemblerPool2Name" ( (SMTDSettings.AssemblerPool2Name = ddl_assembler_pool2list.selected) as string )
			if SMTDSettings.AssemblerPool2Name == "" then
				SMTD_MainRollout.Ui_report ("+Assembler Secondary Pool DISABLED.")
			else
				SMTD_MainRollout.Ui_report ("+Assembler Secondary Pool changed to ["+SMTDSettings.AssemblerPool2Name+"]")
			displayAssemblerPoolsList()
		)

		on ddl_assembler_group selected itm do
		(
			setIniSetting SMTDPaths.InIFile "AssemblerSettings" "AssemblerGroup" ( (SMTDSettings.AssemblerGroup = ddl_assembler_group.selected) as string )
			SMTD_MainRollout.Ui_report ("+Assembler Group Changed To ["+SMTDSettings.AssemblerGroup+"]")
			displayAssemblerGroupsList()
		)

		on spn_assembler_priority changed value do
		(
			setIniSetting SMTDPaths.InIFile "AssemblerSettings" "AssemblerPriority" ( (SMTDSettings.AssemblerPriority= (assembler_job_priority_update value)) as string )
			SMTD_MainRollout.Ui_report ("+Assembler Priority Spinner changed to ["+value as string+"]") LogFileOnly:true
		)

		on sld_assembler_priority clicked value do
		(
			setIniSetting SMTDPaths.InIFile "AssemblerSettings" "AssemblerPriority" ( (SMTDSettings.AssemblerPriority= (assembler_job_priority_update ((value * SMTDSettings.MaximumPriority) / 100))) as string )
			SMTD_MainRollout.Ui_report ("+Assembler Priority Slider changed to ["+value as string+"]") LogFileOnly:true
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Tiles & Region Rendering Options"
			if not state do
			(
				case SMTDSettings.RegionRenderingMode of
				(
					default: theTitle += " [Full Frame]"
					#singleFrameMultiRegion: theTitle += " [Single Frame Multi-Region]"
					#animationMultiRegion: theTitle += " [Animation Multi-Region]"
					#singleFrameTiles: theTitle += " [Single Frame Tiles]"
					#maxRegion:  theTitle += " [3ds Max Region]"
				)
			)
			SMTD_TileOptions.title = theTitle
		)

		on SMTD_TileOptions rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_TileOptions open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening Tile & Region Rendering Options Rollout"
			updateControls()

			--chk_singleTileJob.caption = SMTDFunctions.getStickyCaption "TilesRendering" "SingleTileJob" "Submit A Single Job For The Current Frame  "
			chk_MultiRegionCopyDraftConfig.caption = SMTDFunctions.getStickyCaption "MultiRegionRendering" "MultiRegionCopyDraftConfig"   "Copy Draft Config Files To Output Folder  "
			chk_singleTileJobCleanup.caption = SMTDFunctions.getStickyCaption "TilesRendering" "SingleTileJobCleanup"   "Cleanup Tiles After Assembly  "
			chk_singleTileJobDraftErrorOnMissing.caption = SMTDFunctions.getStickyCaption "TilesRendering" "SingleTileJobDraftErrorOnMissing"   "Draft Assembly Job Error On Missing Tiles  "
			spn_tilePadding.caption = SMTDFunctions.getStickyCaption "TilesRendering" "TilesPadding"   "Pixel Padding: "

			updateRolloutTitle SMTD_TileOptions.open
		)
	)

	rollout SMTD_TilesRendering "Tile Rendering" rolledup:true
	(
		local lastX = 4
		local lastY = 3

		group "IMPORTANT NOTE:"
		(
			--label lbl_tiles01 "While you can render Tiles to any supported bitmap format, not all file formats"
			--label lbl_tiles02 "are supported by the Deadline Tile Assembler. Known supported formats include:"
			label lbl_tiles02 "For automated assembly of the final image, supported image formats include:"
			label lbl_tiles03 "BMP, DDS, EXR, JPG, JPE, JPEG, PNG, RGB, RGBA, SGI, TGA, TIF, TIFF"
		)

		group "Tile Rendering Settings"
		(
			checkbox chk_tilesRendering "Enable Tiles Rendering  " across:3 align:#left visible:false
			spinner spn_tilesInX "Tiles In X: " range:[1,200,4] type:#integer  fieldwidth:35 align:#right offset:[28,0]
			spinner spn_tilesInY "Tiles In Y: " range:[1,200,3] type:#integer fieldwidth:35 align:#right offset:[1,0]

			checkbox chk_showTilesGizmo "Show Tiles In Viewport *" across:2 align:#left
			checkbox chk_tileBlowupMode "Enable Blowup Mode  " offset:[10,0]

			checkbox chk_useCustomTiles "Re-Render User-Defined Tiles*" across:2 offset:[0,0]  align:#left
			checkbutton chk_toggleUserTilesDialog "Specify Tiles To Re-render..." width:220 height:19 align:#right offset:[0,-2]

			checkbox chk_singleTileJobDependent "Submit Dependent Assembly Job  " across:2 align:#left

		)



		--group "Mutiple Tile Job Settings"
		--(
			--checkbox chk_machineLimitForJobs "Split Machine Limit Between Tile Jobs  " align:#left
			label lbl_tiles "Total Number Of Jobs: 12" align:#right
		--)

		fn checkTileXValidity =
		(
			--local continueChecking = ((RenderWidth/spn_tilesInX.value) as float != (1.0*RenderWidth/spn_tilesInX.value))
			local continueChecking = false
			if SMTDSettings.tileBlowupMode then
			(
				continueChecking = ((RenderWidth/spn_tilesInX.value) as float != (1.0*RenderWidth/spn_tilesInX.value))
				continueChecking = continueChecking or (((RenderWidth/spn_tilesInX.value)/spn_tilesInX.value) as float != (1.0*(RenderWidth/spn_tilesInX.value)/spn_tilesInX.value))
			)

			if continueChecking then
			(
				if spn_tilesInX.value > lastX then
				(
					lastX = spn_tilesInX.value
					if spn_tilesInX.value < 200 then
						spn_tilesInX.value += 1
					else
						lastX = 1000
					checkTileXValidity()
				)
				else
				(
					lastX = spn_tilesInX.value
					spn_tilesInX.value -= 1
					checkTileXValidity()
				)
			)
		)

		fn checkTileYValidity =
		(
			--local continueChecking = ((RenderHeight/spn_tilesInY.value) as float != (1.0*RenderHeight/spn_tilesInY.value))
			local continueChecking = false
			if SMTDSettings.tileBlowupMode then
			(
				continueChecking = ((RenderHeight/spn_tilesInY.value) as float != (1.0*RenderHeight/spn_tilesInY.value))
				continueChecking = continueChecking or (((RenderHeight/spn_tilesInY.value)/spn_tilesInY.value) as float != (1.0*(RenderHeight/spn_tilesInY.value)/spn_tilesInY.value))
			)

			if continueChecking then
			(
				if spn_tilesInY.value > lastY then
				(
					lastY = spn_tilesInY.value
					if spn_tilesInY.value < 200 then
						spn_tilesInY.value += 1
					else
						lastY = 1000
					checkTileYValidity()
				)
				else
				(
					lastY = spn_tilesInY.value
					spn_tilesInY.value -= 1
					checkTileYValidity()
				)
			)
		)
		fn checkTileValidity =
		(
			spn_tilesInX.changed spn_tilesInX.value
			spn_tilesInY.changed spn_tilesInY.value
		)

		fn updateTileGizmo =
		(
			local theTileGizmo= getNodeByName "SMTDTileGizmo"
			if isValidNode theTileGizmo do
			(
				theTileGizmo.tilesX = spn_tilesInX.value
				theTileGizmo.tilesY = spn_tilesInY.value
				redrawViews()
			)
		)

		fn createTileGizmo state =
		(
			if state then
			(
				-- enforce safe frames when displaying the gizmo
				displaySafeFrames = true

				renderSceneDialog.Commit()
				local theTileGizmo = getNodeByName "SMTDTileGizmo"
				if not isValidNode theTileGizmo and DLTileManipulator != undefined do
				(
					theTileGizmo = DLTileManipulator name:"SMTDTileGizmo"
					theTileGizmo.transform.controller = transform_script()
					theTileGizmo.isSelected = true
					redrawViews()
					theTileGizmo.isSelected = false
					theInterface = LayerManager.getLayerFromName "SMTD_Gizmos"
					if theInterface == undefined do
						theInterface = LayerManager.newLayerFromName "SMTD_Gizmos"
					theInterface.addnode theTileGizmo
					theInterface.ishidden = theInterface.isFrozen = false
				)
				updateTileGizmo()
			)
			else
			(
				local theTileGizmo= getNodeByName "SMTDTileGizmo"
				if isValidNode theTileGizmo do delete theTileGizmo
				try(LayerManager.deleteLayerByName "SMTD_Gizmos")catch()
			)
		)

		fn updateLabel =
		(
			local txt = "Total Number Of Tiles: "
			local tilesCount = if SMTDSettings.useCustomTiles then
				SMTDSettings.CustomTiles.count
			else
				( SMTDSettings.TilesInX * SMTDSettings.TilesInY )
			txt += tilesCount as string
			if SMTDSettings.LimitEnabled then
				txt += ". Limit: " + SMTDSettings.MachineLimit as string + " Machine"+(if SMTDSettings.MachineLimit == 1 then "" else "s")+"/Tile Job"
			else
				txt += ". No Machine Limit."

			lbl_tiles.text = txt
		)

		fn updateControls =
		(
			chk_useCustomTiles.state = SMTDSettings.useCustomTiles
			--chk_tilesRendering.state = SMTDSettings.TilesRendering
			chk_tileBlowupMode.state = SMTDSettings.TileBlowupMode
			chk_tileBlowupMode.caption = SMTDFunctions.getStickyCaption "TilesRendering" "TileBlowupMode" "Enable Blowup Mode  "

			chk_singleTileJobDependent.state = SMTDSettings.SingleTileJobDependent
		)

		on chk_showTilesGizmo changed state do createTileGizmo state

		on chk_toggleUserTilesDialog changed state do
		(
			try(destroyDialog SMTD_UserDefinedTilesDialog)catch()
			if state do
				createDialog SMTD_UserDefinedTilesDialog (SMTDSettings.CustomTilesPreviewWidth) (SMTDSettings.CustomTilesPreviewHeight+30) ((GetDialogPos SMTD_MainRollout).x+526)  (GetDialogPos SMTD_MainRollout).y style:#(#style_titlebar, #style_border, #style_sysmenu, #style_minimizebox, #style_resizing)
		)

		/*
		on chk_machineLimitForJobs changed state do
		(
			SMTDSettings.MachineLimitTileJobs = state
			updateLabel()
			SMTD_MainRollout.Ui_report ("+Tiles Rendering: Split Machine Limit Between Tile Jobs set to [" + state as string + "] for this session. Not Sticky.")
		)
		*/

		on spn_tilesInX changed val do
		(
			if SMTDSettings.tileBlowupMode then
			(
				checkTileXValidity()
				lastX = spn_tilesInX.value

				spn_tilesInY.value = spn_tilesInX.value
				checkTileYValidity()
				lastY = spn_tilesInY.value
				setIniSetting SMTDPaths.InIFile "TilesRendering"  "TilesInY" ( (SMTDSettings.TilesInY= spn_tilesInY.value) as string)

				spn_tilesInX.value = spn_tilesInY.value
			)

			checkTileXValidity()
			lastX = spn_tilesInX.value
			setIniSetting SMTDPaths.InIFile "TilesRendering"  "TilesInX" ( (SMTDSettings.TilesInX= spn_tilesInX.value) as string)
			updateLabel()
			SMTD_MainRollout.Ui_report ("+Tiles Rendering: Tiles In X set to [" + spn_tilesInX.value as string + "] for this session. Not Sticky.") LogFileOnly:true
			try(SMTD_UserDefinedTilesDialog.updateTilesDisplay())catch()
			updateTileGizmo()
		)

		on spn_tilesInY changed val do
		(
			if SMTDSettings.tileBlowupMode then
			(
				checkTileYValidity()
				lastY = spn_tilesInY.value

				spn_tilesInX.value = spn_tilesInY.value
				checkTileXValidity()
				lastX = spn_tilesInX.value
				setIniSetting SMTDPaths.InIFile "TilesRendering"  "TilesInX" ( (SMTDSettings.TilesInX= spn_tilesInX.value) as string)

				spn_tilesInY.value = spn_tilesInX.value
			)

			checkTileYValidity()
			lastY = spn_tilesInY.value
			setIniSetting SMTDPaths.InIFile "TilesRendering"  "TilesInY" ( (SMTDSettings.TilesInY= spn_tilesInY.value) as string)
			updateLabel()
			SMTD_MainRollout.Ui_report ("+Tiles Rendering: Tiles In Y set to [" + spn_tilesInY.value as string + "] for this session. Not Sticky.") LogFileOnly:true
			try(SMTD_UserDefinedTilesDialog.updateTilesDisplay())catch()
			updateTileGizmo()
		)

		/*
		on chk_tilesRendering changed state do
		(
			if state do
			(
				SMTDSettings.RegionRendering = SMTD_RegionRendering.chk_RegionRendering.state = false
				SMTDSettings.MultiRegionRendering = SMTD_MultiRegionRendering.chk_MultiRegionRendering.state  = false
			)

			setIniSetting SMTDPaths.InIFile "TilesRendering" "TilesRendering" ( (SMTDSettings.TilesRendering = state) as string)
			SMTD_MainRollout.Ui_report ("+Tiles Rendering: Enable Distributed Tiles Rendering set to [" + state as string + "] for this session.")
		)
		*/

		on chk_useCustomTiles changed state do
		(
			SMTDSettings.useCustomTiles = state
			updateLabel()
			SMTD_MainRollout.Ui_report ("+Tiles Rendering: Use Custom Tiles set to [" + state as string + "] for this session. Not Sticky.")
			if state do SMTD_MainRollout.Ui_report ("+Tiles Rendering: Custom Tiles: " + SMTDSettings.CustomTiles as string )
		)

		on chk_singleTileJobDependent changed state do
		(
			setIniSetting SMTDPaths.InIFile "TilesRendering" "SingleTileJobDependent" ( (SMTDSettings.SingleTileJobDependent = state) as string)
			SMTD_MainRollout.Ui_report ("+Tiles Rendering: Single Tile Dependent Assembly Job set to [" + state as string + "].")

			updateControls()
			SMTD_TileOptions.updateControls()
		)

		fn updateTilesForBlowupState state =
		(
			if state then
			(
				spn_tilesInX.value = spn_tilesInY.value
				checkTileXValidity()
				lastX = spn_tilesInX.value

				spn_tilesInY.value = spn_tilesInX.value
				checkTileYValidity()
				lastY = spn_tilesInY.value
				setIniSetting SMTDPaths.InIFile "TilesRendering"  "TilesInY" ( (SMTDSettings.TilesInY= spn_tilesInY.value) as string)

				spn_tilesInX.value = spn_tilesInY.value
				checkTileXValidity()
				lastX = spn_tilesInX.value
				setIniSetting SMTDPaths.InIFile "TilesRendering"  "TilesInX" ( (SMTDSettings.TilesInX= spn_tilesInX.value) as string)
				updateLabel()
				SMTD_MainRollout.Ui_report ("+Tiles Rendering: Tiles In X set to [" + spn_tilesInX.value as string + "] for this session. Not Sticky.") LogFileOnly:true
				try(SMTD_UserDefinedTilesDialog.updateTilesDisplay())catch()
				updateTileGizmo()
			)
		)

		on chk_tileBlowupMode changed state do
		(
			setIniSetting SMTDPaths.InIFile "TilesRendering" "TileBlowupMode" ( (SMTDSettings.TileBlowupMode = state) as string)
			SMTD_MainRollout.Ui_report ("+Tiles Rendering: Blowup Mode set to [" + state as string + "].")
			updateTilesForBlowupState state
		)

		on SMTD_TilesRendering open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening Tiles Rendering Rollout"
			updateControls()

			--chk_machineLimitForJobs.state = SMTDSettings.MachineLimitTileJobs

			spn_tilesInX.changed (lastX = spn_tilesInX.value = SMTDSettings.TilesInX)
			spn_tilesInY.changed (lastY = spn_tilesInY.value = SMTDSettings.TilesInY)

			updateLabel()
			callbacks.removeScripts id:#SMTD_MonitorRenderParameters
			callbacks.addScript #renderParamsChanged "SMTD_TilesRendering.checkTileValidity()" id:#SMTD_MonitorRenderParameters

			callbacks.removeScripts id:#SMTD_PreTileGizmoCallback
			callbacks.removeScripts id:#SMTD_PostTileGizmoCallback
			callbacks.addScript #filePreSave "if SMTD_TilesRendering.chk_showTilesGizmo.state do SMTD_TilesRendering.createTileGizmo false" id:#SMTD_PreTileGizmoCallback
			callbacks.addScript #filePostSave "if SMTD_TilesRendering.chk_showTilesGizmo.state do SMTD_TilesRendering.createTileGizmo true" id:#SMTD_PostTileGizmoCallback

			--chk_tilesRendering.caption = SMTDFunctions.getStickyCaption "TilesRendering" "TilesRendering"   "Enable Tiles Rendering  "
			spn_tilesInX.caption = SMTDFunctions.getStickyCaption "TilesRendering" "TilesInX"   "Tiles In X: "
			spn_tilesInY.caption = SMTDFunctions.getStickyCaption "TilesRendering" "TilesInY"   "Tiles In Y: "
			--chk_machineLimitForJobs.caption = SMTDFunctions.getStickyCaption "TilesRendering" "MachineLimitTileJobs"   "Split Machine Limit Between Tile Jobs  "

			chk_singleTileJobDependent.caption = SMTDFunctions.getStickyCaption "TilesRendering" "SingleTileJobDependent"   "Submit Dependent Assembly Job  "
		)

		on SMTD_TilesRendering rolledUp val do
		(
			--SMTD_MultiRegionRendering.open = not val
		)

		on SMTD_TilesRendering close do
		(
			callbacks.removeScripts id:#SMTD_MonitorRenderParameters
			callbacks.removeScripts id:#SMTD_PreTileGizmoCallback
			callbacks.removeScripts id:#SMTD_PostTileGizmoCallback
			createTileGizmo false
		)
	)

	rcmenu MultiRegion_CreateFrom_Menu
	(
		menuItem mnu_createFromSceneSelection "Create From SCENE SELECTION..." enabled:(selection.count > 0)
		menuItem mnu_createFromGrid "Create From TILES GRID..."
		menuItem mnu_createFromGridUserTiles "Create From Tiles Grid USER TILES..."
		menuItem mnu_createFromMaxRegion "Create From 3DS MAX REGION..."
		separator sep10
		menuItem mnu_fillRegionsB "OPTIMAL FILL Of Empty Areas" enabled:(SMTDSettings.MultiRegionData.count > 0)
		menuItem mnu_fillRegionsH "HORIZONTAL FILL Of Empty Areas" enabled:(SMTDSettings.MultiRegionData.count > 0)
		menuItem mnu_fillRegionsV "VERTICAL FILL Of Empty Areas" enabled:(SMTDSettings.MultiRegionData.count > 0)
		menuItem mnu_fillRegionsG "GRID FILL Of Empty Areas" enabled:(SMTDSettings.MultiRegionData.count > 0)

		separator sep20
		menuItem mnu_createOptimizedRegions25 "OPTIMIZE Regions, Overlap Threshold > 25%..."
		menuItem mnu_createOptimizedRegions50 "OPTIMIZE Regions, Overlap Threshold > 50%..."
		menuItem mnu_createOptimizedRegions75 "OPTIMIZE Regions, Overlap Threshold > 75%..."

		on mnu_createFromMaxRegion picked do SMTD_MultiRegionRendering.createFromMaxRegion()
		on mnu_createFromGrid picked do SMTD_MultiRegionRendering.createFromTilesGrid()
		on mnu_createFromGridUserTiles picked do SMTD_MultiRegionRendering.createFromTilesGrid usertiles:true
		on mnu_createFromSceneSelection picked do
		(
			SMTD_MultiRegionRendering.createFromSceneSelection ()
			--SMTD_MultiRegionRendering.optimizeOverlappingRegions theThreshold:0.25
		)
		on mnu_fillRegionsG picked do SMTD_MultiRegionRendering.fillRegions mode:#g
		on mnu_fillRegionsH picked do SMTD_MultiRegionRendering.fillRegions mode:#h
		on mnu_fillRegionsV picked do SMTD_MultiRegionRendering.fillRegions mode:#v
		on mnu_fillRegionsB picked do SMTD_MultiRegionRendering.fillRegions mode:#b

		on mnu_createOptimizedRegions25 picked do SMTD_MultiRegionRendering.optimizeOverlappingRegions theThreshold:0.25
		on mnu_createOptimizedRegions50 picked do SMTD_MultiRegionRendering.optimizeOverlappingRegions theThreshold:0.5
		on mnu_createOptimizedRegions75 picked do SMTD_MultiRegionRendering.optimizeOverlappingRegions theThreshold:0.75
	)

	rcmenu MultiRegion_FileSave_Menu
	(
		menuItem mnu_loadPreset "LOAD Regions From Disk Preset File..."
		menuItem mnu_mergePreset "MERGE Regions From Disk Preset File..."
		separator sep10
		menuItem mnu_savePreset "SAVE Regions To Disk Preset File..." enabled:(SMTDSettings.MultiRegionData.count > 0)

		on mnu_loadPreset picked do SMTD_MultiRegionRendering.loadRegionsPresetFile()
		on mnu_mergePreset picked do SMTD_MultiRegionRendering.mergeRegionsPresetFile()
		on mnu_savePreset picked do SMTD_MultiRegionRendering.saveRegionsPresetFile()
	)

	rcmenu MultiRegion_FitPaddingOptions_Menu
	(
		menuitem mnu_padding100 "100%" checked:(SMTDSettings.MultiRegionFitPadding == 100.0)
		menuitem mnu_padding75 "75%" checked:(SMTDSettings.MultiRegionFitPadding == 75.0)
		menuitem mnu_padding50 "50%" checked:(SMTDSettings.MultiRegionFitPadding == 50.0)
		menuitem mnu_padding40 "40%" checked:(SMTDSettings.MultiRegionFitPadding == 40.0)
		menuitem mnu_padding30 "30%" checked:(SMTDSettings.MultiRegionFitPadding == 30.0)
		menuitem mnu_padding20 "20%" checked:(SMTDSettings.MultiRegionFitPadding == 20.0)
		menuitem mnu_padding10 "10%" checked:(SMTDSettings.MultiRegionFitPadding == 10.0)
		menuitem mnu_padding0 "No Padding" checked:(SMTDSettings.MultiRegionFitPadding == 0.0)

		on mnu_padding100 picked do (SMTDSettings.MultiRegionFitPadding = 100.0; SMTD_MultiRegionRendering.updateFitPadding())
		on mnu_padding75 picked do (SMTDSettings.MultiRegionFitPadding = 75.0; SMTD_MultiRegionRendering.updateFitPadding())
		on mnu_padding50 picked do (SMTDSettings.MultiRegionFitPadding = 50.0; SMTD_MultiRegionRendering.updateFitPadding())
		on mnu_padding40 picked do (SMTDSettings.MultiRegionFitPadding = 40.0; SMTD_MultiRegionRendering.updateFitPadding())
		on mnu_padding30 picked do (SMTDSettings.MultiRegionFitPadding = 30.0; SMTD_MultiRegionRendering.updateFitPadding())
		on mnu_padding20 picked do (SMTDSettings.MultiRegionFitPadding = 20.0; SMTD_MultiRegionRendering.updateFitPadding())
		on mnu_padding10 picked do (SMTDSettings.MultiRegionFitPadding = 10.0; SMTD_MultiRegionRendering.updateFitPadding())
		on mnu_padding0 picked do (SMTDSettings.MultiRegionFitPadding = 0.0; SMTD_MultiRegionRendering.updateFitPadding())
	)


	persistent global SMTD_MultiRegionSettingsPersistentGlobal
	if SMTD_MultiRegionSettingsPersistentGlobal == undefined do SMTD_MultiRegionSettingsPersistentGlobal = #()
	global SMTD_MultiRegion2DTrackingStruct
	struct SMTD_MultiRegion2DTrackingStructDef
	(
		FromFrame = 0,
		ToFrame = 100,
		TrackMode = #precise,
		PaddingPercent = 10.0,
		SelectedObjects = #()
	)
	SMTD_MultiRegion2DTrackingStruct = SMTD_MultiRegion2DTrackingStructDef()

	global SMTD_MultiRegion2DTrackingDialog
	rollout SMTD_MultiRegion2DTrackingDialog "Track Region To Selected Objects" width:400 height:120
	(
		spinner spn_fromFrame "Track From Frame:" range:[-1000000,1000000,animationRange.start] type:#integer fieldwidth:55 across:2
		spinner spn_toFrame "To Frame:" range:[-1000000,1000000,animationRange.end] type:#integer fieldwidth:55 align:#right

		radiobuttons rad_mode labels:#("Tight But Slow Vertex-Based Tracking", "Loose But Quick Object Bounding Box Tracking") default:(findItem #(#precise,#quick) SMTD_MultiRegion2DTrackingStruct.TrackMode)

		spinner spn_PaddingPercent "Padding %:" range:[0,100.0,SMTD_MultiRegion2DTrackingStruct.PaddingPercent] type:#float fieldwidth:45 align:#right

		button btn_trackit "TRACK REGION..." width:186 height:30 across:2 align:#left
		button btn_cancel "Cancel" width:186 height:30 align:#right

		fn updateStruct =
		(
			SMTD_MultiRegion2DTrackingStruct.FromFrame = spn_fromFrame.value
			SMTD_MultiRegion2DTrackingStruct.ToFrame = spn_toFrame.value
			SMTD_MultiRegion2DTrackingStruct.PaddingPercent = spn_PaddingPercent.value
		)

		on rad_mode changed state do
		(
			SMTD_MultiRegion2DTrackingStruct.TrackMode = #(#precise, #quick)[rad_mode.state]
			if state == 1 then
				spn_PaddingPercent.value = SMTD_MultiRegion2DTrackingStruct.PaddingPercent = SMTDSettings.MultiRegionFitPadding
			else
				spn_PaddingPercent.value = SMTD_MultiRegion2DTrackingStruct.PaddingPercent = 0.0
		)

		on btn_trackit pressed do
		(
			updateStruct()
			destroyDialog SMTD_MultiRegion2DTrackingDialog
			SMTD_MultiRegionRendering.TrackSelectionOverTime()
		)
		on btn_cancel pressed do destroyDialog SMTD_MultiRegion2DTrackingDialog

		on SMTD_MultiRegion2DTrackingDialog open do
		(
			updateStruct()
			SMTD_MultiRegion2DTrackingDialog.title = if SMTD_MultiRegion2DTrackingStruct.SelectedObjects.count == 1 then
				"Track "+SMTD_MultiRegion2DTrackingStruct.SelectedObjects[1].name+""
			else
				"Track "+ SMTD_MultiRegion2DTrackingStruct.SelectedObjects.count as string+" Selected Object" + (if SMTD_MultiRegion2DTrackingStruct.SelectedObjects.count == 1 then "" else "s")
			setFocus btn_trackit
		)
	)--end multi-region 2d tracker dialog rollout

	rollout SMTD_MultiRegionRendering "'Jigsaw' Multi-Region Rendering" rolledup:true
	(
		local theMRManipulator
		local theRegionGizmo
		local lastSelectedLines = #()
		local interpolateKeyframe, setRegionKeyframe, FitToSelectionButtonEvent

		--checkbox chk_MultiRegionRendering "Enable Multi-Region Rendering * " offset:[0,-5] across:3 visible:false
		button btn_updateRegions "UPDATE List"  width:120 height:18 align:#left offset:[-10,-5] across:4 tooltip:"Update the list, for example after changing the Render Resolution."
		button btn_loadSaveRegions " [] LOAD/SAVE File.." width:120 height:18 align:#center offset:[-2,-5] tooltip:"Save, Load or Merge the current Regions list using a disk preset file."
		button btn_getFromCamera " [] GET From Camera..." width:120 height:18 align:#center offset:[3,-5] tooltip:"Add a new Region to the list."
		button btn_saveInCamera " [] STORE In Camera..." width:120 height:18 align:#right offset:[10,-5] tooltip:"Create a grid of Regions based on the Tile Grid settings."

		/*
		button btn_saveRegions "SAVE To File.." across:4 width:120 height:18 align:#left offset:[-10,-5] tooltip:"Save the current Regions list to a disk preset file to be reused later."
		button btn_loadRegions "LOAD From File..."  width:120 height:18 align:#center offset:[-2,-5] tooltip:"Load a previously saved Regions preset file from disk, replacing the current list."
		button btn_mergeRegions "MERGE From File... " width:120 height:18 align:#center offset:[3,-5] tooltip:"Merge a previously saved Regions preset file into the current Regions list."
		*/

		edittext edt_presetDescription "Notes:" text:"" offset:[9,-4] width:480 align:#right

		button btn_addRegion "ADD New Region" across:4 width:120 height:18 align:#left offset:[-10,-4] tooltip:"Add a new Region to the list."
		button btn_createFrom " [] CREATE From..." width:120 height:18 align:#center offset:[-2,-4] tooltip:"Create a grid of Regions based on the Tile Grid settings."
		button btn_cloneRight  "Clone LEFT | RIGHT"   width:120 height:18 align:#center offset:[3,-4] tooltip:"Clone the currently selected Region by moving it to the left or right by its width.\n\nPress LEFT Mouse Button for LEFT\nPress RIGHT Mouse Button for RIGHT"
		button btn_cloneDown "Clone UP | DOWN"   width:120 height:18 align:#right offset:[10,-4] tooltip:"Clone the currently selected Region by moving it up or down by its height.\n\nPress LEFT Mouse Button for UP\nPress RIGHT Mouse Button for DOWN"

		button btn_FitToSelection  "FIT To Sel. Objects"   across:5 width:98 height:18 align:#left offset:[-10,-5] tooltip:"Press LEFT Mouse Button to fit the highlighted region to the selected geometry objects based on the mesh vertices.\n\nPress RIGHT Mouse Button to perform `Quick And Loose Fit` using the World-Oriented Bounding Box corners."
		button btn_FitOptions "[]" width:22 height:18 offset:[-39,-5] tooltip:"Set the Padding Percentage for Tight Fit operations."
		button btn_track2D "TRACK Region..." width:120 height:18 align:#center offset:[-60,-5] tooltip:"Tracks the highlighted region to one or more selected geomety objects.\n\nPress LEFT Mouse button to open the Track Region dialog pre-set for tight vertex-based fitting.\n\nPress RIGHT Mouse Button to open the Track Region dialog pre-set of 'Quick And Loose' bounding box-based fitting."
		button btn_selectInvertSelection "SELECT | INVERT"  width:120 height:18 align:#center offset:[-32,-5] tooltip:"Press LEFT Mouse Button to SELECT all regions.\n\nPress RIGHT Mouse Button to INVERT the Region list selection."
		button btn_removeRegion "DELETE Region" width:120 height:18 align:#right offset:[10,-5] tooltip:"Remove the selected Regions from the list.\n\nYou will be prompted to confirm the operation first."

		--imgtag img_animKeys height:3 width:460 offset:[0,-3]
		progressbar prg_animKeysDivider width:480 height:5 color:(color 180 180 180) value:100.0 offset:[10,-6] align:#right
		button btn_setKey  "SET Keyframe"   across:4 width:120 height:18 align:#left offset:[-10,-6] tooltip:"Set key for selected regions on the current frame."
		button btn_prevKey "<< PREVIOUS Key"  width:120 height:18 align:#center offset:[-2,-6] tooltip:"Go to previous key."
		button btn_nextKey "NEXT Key >>" width:120 height:18 align:#center offset:[3,-6] tooltip:"Go to next key."
		button btn_deleteKey "DELETE Keyframe" width:120 height:18 align:#right offset:[10,-6] tooltip:"Press LEFT Mouse Button to Delete Keys from selected regions on the Current Frame.\n\nPress RIGHT Mouse Button to Delete ALL Keys from selected regions."

		dotNetControl lv_regions "System.Windows.Forms.ListView" width:480 height:180 align:#center offset:[0,-4]

		spinner spn_posX "X" fieldwidth:35 type:#integer across:8 align:#left offset:[-10,-3] range:[0,100000,0]
		spinner spn_posY "Y" fieldwidth:35 type:#integer offset:[-17,-3] range:[0,100000,0]
		spinner spn_W "W" fieldwidth:35 type:#integer offset:[-15,-3] range:[1,100000,1]
		spinner spn_H "H" fieldwidth:35 type:#integer offset:[-15,-3] range:[1,100000,1]
		spinner spn_TilesX "T" fieldwidth:22 type:#integer offset:[-30,-3] range:[1,10,2]
		spinner spn_TilesY "" fieldwidth:22 type:#integer offset:[-53,-3] range:[1,10,2]
		checkbox chk_lock "" offset:[-47,-2]
		edittext edt_notes text:"" fieldwidth:152 align:#right offset:[14,-3]

		button btn_undo "UNDO..." width:96 height:18 align:#left offset:[-10,-2] tooltip:"Press LEFT Mouse Button to Undo last step.\n\nPress RIGHT Mouse Button to Undo to any previous step by selecting from a list." across:5
		button btn_redo "REDO..." width:96 height:18 align:#center offset:[-4,-2] tooltip:"Press LEFT Mouse Button to Redo last undone step.\n\nPress RIGHT Mouse Button to Redo to any undone step by selecting from a list."
		button btn_hold "HOLD" width:96 height:18 align:#center offset:[0,-2] tooltip:"Press LEFT Mouse Button to manually create an Undo Record with the current state.\n\nSome changes like moving the Region Gizmo or entering new Coordinates do not create an Undo record manually.\n\nCreate a Manual Hold if you intend to make many changes and want to be sure you can revert to the current state."
		button btn_splitToTiles "SPLIT To Tiles" width:96 height:18 align:#center offset:[4,-2] tooltip:"Press LEFT Mouse Button to Split a single Region into multiple new Regions according to its Tiles values."
		button btn_mergeHighlighted "MERGE Selected"   width:96 height:18 align:#right offset:[10,-2] tooltip:"Press LEFT Mouse Button to Merge two or more highlighted Regions using their common bounding box."

		edittext lbl_areaReport "" align:#right offset:[10,-4] readOnly:true fieldwidth:481
		dropdownlist ddl_BackgroundMode items:#("Assemble Over EMPTY Background","Compose Over PREVIOUS OUTPUT Image", "Compose Over CUSTOM SINGLE Image", "Compose Over CUSTOM Image SEQUENCE") across:2 align:#left offset:[-10,-3] width:240
		button btn_pickUserDefinedImage "Pick Custom Background Image..." width:238 height:18 offset:[11,-2] align:#right
		edittext edt_userDefinedImage "" align:#right offset:[10,-5] readOnly:false fieldwidth:481

		fn updateFitPadding =
		(
			btn_FitOptions.text = (SMTDSettings.MultiRegionFitPadding as integer) as string
			setIniSetting SMTDPaths.InIFile "MultiRegionRendering" "MultiRegionFitPadding" (SMTDSettings.MultiRegionFitPadding as string)
		)

		local isUpdatingList = false
		fn initListView =
		(
			--showProperties lv_regions
			lv_regions.gridLines = true
			lv_regions.View = (dotNetClass "System.Windows.Forms.View").Details
			lv_regions.fullRowSelect = true
			lv_regions.HideSelection = false

			lv_regions.checkboxes = true
			--lv_regions.BackColor = lv_regions.BackColor.FromArgb 210 215 225

			lv_regions.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			lv_regions.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r (amin (SMTD_ColorPalette.maxBgColor.g+5) 255) (amin (SMTD_ColorPalette.maxBgColor.b+15) 255)

			lv_regions.LabelEdit = false
			lv_regions.Columns.add "On #" 40
			lv_regions.Columns.add "X" 45
			lv_regions.Columns.add "Y" 45
			lv_regions.Columns.add "Width" 42
			lv_regions.Columns.add "Height" 45
			lv_regions.Columns.add "Tiles" 42
			lv_regions.Columns.add "Keys" 35
			lv_regions.Columns.add "Lock" 35
			lv_regions.Columns.add "Notes" 400
		)

		fn getListViewSelection =	--returns an array of the selected ListView items
		(
			try
				sort (for i = 1 to lv_regions.items.count where lv_regions.items.item[i-1].Selected collect lv_regions.items.item[i-1].subItems.item[0].tag as integer)
			catch
				#()
		)

		fn setListViewSelection theSel =
		(
			for i = 1 to lv_regions.items.count do
				try( lv_regions.items.item[i-1].Selected = findItem theSel (lv_regions.items.item[i-1].subItems.item[0].tag as integer) > 0 )catch()
			lv_regions.focus()
		)

		fn mapListIndexToTag theArray =
		(
			local theResult = #()
			for i in theArray do
			(
				for j = 1 to lv_regions.items.count do
				(
					local theTag = (lv_regions.items.item[j-1].subItems.item[0].tag as integer)
					if theTag == i do append theResult theTag
				)
			)
			sort (theResult)
		)

		fn mapTagToListIndex theArray =
		(
			local theResult = #()
			for i in theArray do
			(
				for j = 1 to lv_regions.items.count do
				(
					local theTag = (lv_regions.items.item[j-1].subItems.item[0].tag as integer)
					if theTag == i do append theResult j
				)
			)
			sort (theResult)
		)

		fn CompileComparer =
		(
			local source = ""
			source+="using System;\n"
			source+="using System.Windows.Forms;\n"
			source+="using System.Collections;\n"
			source+="public class ListViewItemComparer : IComparer\n"
			source+="{\n"
			source+="  private int col;\n"
			source+="  private int sort;\n"
			source+="  public ListViewItemComparer()\n"
			source+="  {\n"
			source+="      col = 0;\n"
			source+="      sort = 1;\n"
			source+="  }\n"
			source+="  public ListViewItemComparer(int column, int sorting)\n"
			source+="  {\n"
			source+="    sort = sorting;\n"
			source+="    col = column;\n"
			source+="  }\n"
			source+="  public int Compare(object x, object y)\n"
			source+="  {\n"
			source+="      if ((((ListViewItem)x).SubItems[col].Tag.GetType() == typeof(float))){\n"
			source+="      float compResult = (((float)((ListViewItem)x).SubItems[col].Tag) - ((float)((ListViewItem)y).SubItems[col].Tag));\n"
			source+="      if (compResult>0) return sort * 1; if (compResult < 0) return sort * -1; return 0;"
			source+="   } else \n"
			source+="   return ((String.Compare(((ListViewItem)x).SubItems[col].Text, ((ListViewItem)y).SubItems[col].Text))*sort);\n"
			source+="  }\n"
			source+="}\n"

			csharpProvider = dotnetobject "Microsoft.CSharp.CSharpCodeProvider"
			compilerParams = dotnetobject "System.CodeDom.Compiler.CompilerParameters"
			compilerParams.ReferencedAssemblies.AddRange #("System.dll", "System.Windows.Forms.dll")
			compilerParams.GenerateInMemory = true
			compilerResults = csharpProvider.CompileAssemblyFromSource compilerParams #(source)
			if compilerResults.Errors.Count == 0 then
			(
				compilerResults.CompiledAssembly
			)
			else
			(
				--showProperties compilerResults.CompiledAssembly.Errors
				for i = 0 to compilerResults.Errors.Count-1 do
					format "%\n" compilerResults.Errors.Item[i].ErrorText
				false
			)
		)
		local theAssembly = CompileComparer()
		local lastColumnClicked = 0
		local sortDirection = 1

		on lv_regions ColumnClick args do
		(
			if lastColumnClicked == args.Column then
				sortDirection =  sortDirection * -1
			else
				lastColumnClicked = args.Column
			lv_regions.ListViewItemSorter = dotNetObject "ListViewItemComparer" args.Column sortDirection
		)


		fn sceneSelectionChangedCallback =
		(
			try(deselect theMRManipulator)catch()
			try(deselect theRegionGizmo)catch()
			redrawViews()
			local theSel = getListViewSelection()
			local theObjects = (for o in selection where findItem GeometryClass.classes (classof o) > 0 and classof o != TargetObject collect o)
			btn_FitToSelection.text = "FIT to "+theObjects.count as string+" Object"  + (if theObjects.count != 1 then "s" else "")
			btn_FitToSelection.enabled = btn_track2D.enabled = theObjects.count > 0 and theSel.count == 1
		)

		fn updateEnabledStates =
		(
			local theSel = getListViewSelection()
			--btn_selectAllRegions.enabled=
			btn_selectInvertSelection.enabled = btn_updateRegions.enabled = SMTDSettings.MultiRegionData.count > 0
			btn_track2D.enabled = btn_FitToSelection.enabled = theSel.count == 1
			btn_removeRegion.enabled = btn_setKey.enabled = btn_prevKey.enabled = btn_nextKey.enabled = btn_deleteKey.enabled = theSel.count > 0
			btn_mergeHighlighted.enabled = theSel.count > 1
			btn_cloneDown.enabled = btn_cloneRight.enabled = theSel.count > 0
			btn_undo.enabled = undoBufferIndex > 1
			btn_redo.enabled = undoBufferIndex < undoBufferData.count
			btn_splitToTiles.enabled = (theSel.count == 1 and (SMTDSettings.MultiRegionData[theSel[1]][6] > 1 or SMTDSettings.MultiRegionData[theSel[1]][7] > 1))
			btn_removeRegion.text = if theSel.count == 1 then "DELETE Region" else "DELETE Regions"
			sceneSelectionChangedCallback()

			case ddl_BackgroundMode.selection of
			(
				1: (
					SMTDSettings.MultiRegionBackground = #off
					btn_pickUserDefinedImage.enabled = false
					edt_userDefinedImage.readonly = true
				)
				2: (
					SMTDSettings.MultiRegionBackground = #previous
					btn_pickUserDefinedImage.enabled = false
					edt_userDefinedImage.readonly = true
				)
				3: (
					SMTDSettings.MultiRegionBackground = #single
					btn_pickUserDefinedImage.enabled = true
					edt_userDefinedImage.readonly = false
				)
				4: (
					SMTDSettings.MultiRegionBackground = #sequence
					btn_pickUserDefinedImage.enabled = true
					edt_userDefinedImage.readonly = false
				)
			)

		)

		fn addCommas txt =
		(
			if matchPattern txt pattern:"*L" do txt = substring txt 1 (txt.count-1)
			if matchPattern txt pattern:"*P" do txt = substring txt 1 (txt.count-1)
			theDot = findString txt "."
			if theDot == undefined then
			(
				newTxt = ""

				theDot = txt.count
			)
			else
			(
				newTxt = substring txt theDot -1
				theDot -= 1
			)
			cnt = 0
			for i = theDot to 1 by -1 do
			(
				cnt +=1
				newTxt = txt[i] + newTxt
				if cnt == 3 and i > 1 and txt[i-1] != "-" do
				(
					newTxt = "," + newTxt
					cnt = 0
				)
			)
			newTxt
		)

		fn updateTotalCount =
		(
			local totalCount = 0 --all tiles
			local activeCount = 0 --active tiles
			local activeRegions = 0 --active regions
			local activeAreaInPixels = 0
			for i in SMTDSettings.MultiRegionData  do
			(
				totalCount += i[6]*i[7]
				if i[1] == True do
				(
					activeRegions+=1
					activeCount += i[6]*i[7]
					activeAreaInPixels += (i[4]*renderWidth*i[5]*renderHeight) as integer
				)

			)

			--lbl_totalCount.text
			local txt = activeCount as string +" of "+ totalCount as string +" Tiles, " + activeRegions as string + " of " + SMTDSettings.MultiRegionData.count as string + " Regions. "
			local totalPixels = renderWidth*renderHeight
			local pixelPercentage = 100.0*activeAreaInPixels/totalPixels
			lbl_areaReport.text = txt + (addCommas (activeAreaInPixels as string)) +" Region Pixels out of "+ (addCommas (totalPixels as string)) + " Total ("+pixelPercentage as string+"%)"
			--if activeCount == 0 do chk_MultiRegionRendering.state = SMTDSettings.MultiRegionRendering = false
		)

		fn updateListView =
		(
			isUpdatingList = true
			local theSel = getListViewSelection()
			local theRange = #()
			lv_regions.Items.clear()
			for i = 1 to SMTDSettings.MultiRegionData.count do
			(
				local intval = interpolateKeyframe i
				SMTDSettings.MultiRegionData[i][2] = intval[2]
				SMTDSettings.MultiRegionData[i][3] = intval[3]
				SMTDSettings.MultiRegionData[i][4] = intval[4]
				SMTDSettings.MultiRegionData[i][5] = intval[5]

				local theX = (floor (SMTDSettings.MultiRegionData[i][2]*renderWidth)) as integer
				local theY = (floor (SMTDSettings.MultiRegionData[i][3]*renderHeight)) as integer
				local theW = (floor (SMTDSettings.MultiRegionData[i][4]*renderWidth)) as integer
				local theH = (floor (SMTDSettings.MultiRegionData[i][5]*renderHeight)) as integer
				local theTilesX = SMTDSettings.MultiRegionData[i][6]
				local theTilesY = SMTDSettings.MultiRegionData[i][7]
				if theTilesX == 0 do theTilesX = 1
				if theTilesY == 0 do theTilesY = 1

				li = dotNetObject "System.Windows.Forms.ListViewItem" (i as string)
				li.checked = SMTDSettings.MultiRegionData[i][1]
				(li.SubItems.Item 0).tag = i as float

				subLi = li.SubItems.add (theX as string )
				(li.SubItems.Item 1).tag = theX as float

				subLi = li.SubItems.add (theY as string )
				(li.SubItems.Item 2).tag = theY as float

				subLi = li.SubItems.add (theW as string )
				(li.SubItems.Item 3).tag = theW as float

				subLi = li.SubItems.add (theH as string )
				(li.SubItems.Item 4).tag = theH as float

				subLi = li.SubItems.add (theTilesX as string + "x" + theTilesY as string )
				(li.SubItems.Item 5).tag = (theTilesX as string + "x" + theTilesY as string )

				local theArray = SMTDSettings.MultiRegionData[i][10]
				local theKeyCount = "--"
				if theArray != undefined and theArray.count > 0 do theKeyCount = theArray.count as string
				subLi = li.SubItems.add theKeyCount
				(li.SubItems.Item 6).tag = if theArray != undefined then theArray.count as float else 0.0

				subLi = li.SubItems.add (if SMTDSettings.MultiRegionData[i][11] != true then "--" else "Lock")
				(li.SubItems.Item 7).tag = (if SMTDSettings.MultiRegionData[i][11] != true then 1 else 0)

				subLi = li.SubItems.add (SMTDSettings.MultiRegionData[i][8] as string)
				(li.SubItems.Item 8).tag = (SMTDSettings.MultiRegionData[i][8] as string)

				append theRange li
			)
			lv_regions.Items.AddRange theRange
			setListViewSelection theSel
			isUpdatingList = false
			updateEnabledStates()
			--try(deselect theMRManipulator)catch()
			--try(select selection)catch()
		)

		fn updateListViewOnTimeChange =
		(
			for i =1 to SMTDSettings.MultiRegionData.count do
			(
				local intval = interpolateKeyframe i
				SMTDSettings.MultiRegionData[i][2] = intval[2]
				SMTDSettings.MultiRegionData[i][3] = intval[3]
				SMTDSettings.MultiRegionData[i][4] = intval[4]
				SMTDSettings.MultiRegionData[i][5] = intval[5]

				local theIndex = (mapTagToListIndex #(i))[1]

				local theX = (floor (SMTDSettings.MultiRegionData[i][2]*RenderWidth) ) as integer
				lv_regions.items.Item[theIndex-1].SubItems.Item[1].Text = theX as string
				lv_regions.items.Item[theIndex-1].SubItems.Item[1].Tag = theX as float

				local theY = (floor (SMTDSettings.MultiRegionData[i][3]*RenderHeight) ) as integer
				lv_regions.items.Item[theIndex-1].SubItems.Item[2].Text = theY as string
				lv_regions.items.Item[theIndex-1].SubItems.Item[2].Tag = theY as float

				local theW = (floor (SMTDSettings.MultiRegionData[i][4]*RenderWidth) ) as integer
				lv_regions.items.Item[theIndex-1].SubItems.Item[3].Text = theW as string
				lv_regions.items.Item[theIndex-1].SubItems.Item[3].Tag = theW as float

				local theH = (floor (SMTDSettings.MultiRegionData[i][5]*RenderHeight) ) as integer
				lv_regions.items.Item[theIndex-1].SubItems.Item[4].Text = theH as string
				lv_regions.items.Item[theIndex-1].SubItems.Item[4].Tag = theH as float

				lv_regions.items.Item[theIndex-1].SubItems.Item[5].Text = SMTDSettings.MultiRegionData[i][6] as string + "x" + SMTDSettings.MultiRegionData[i][7] as string

				local theArray = SMTDSettings.MultiRegionData[i][10]
				local theKeysCount = "--"
				if theArray != undefined and theArray.count > 0 do theKeysCount = theArray.count as string
				lv_regions.items.Item[theIndex-1].SubItems.Item[6].Text = theKeysCount
				lv_regions.items.Item[theIndex-1].SubItems.Item[6].Tag = if theArray != undefined then theArray.count as float else 0.0

				lv_regions.items.Item[theIndex-1].SubItems.Item[7].Text = (if SMTDSettings.MultiRegionData[i][11] != true then "--" else "Lock")
				lv_regions.items.Item[theIndex-1].SubItems.Item[8].Text = SMTDSettings.MultiRegionData[i][8]
				--updateSpinners()
			)
		)

		fn updateSpinners =
		(
			local theSel = getListViewSelection()
			spn_TilesX.enabled = spn_TilesY.enabled = theSel.count > 0
			if theSel.count == 1 then
			(
				spn_posX.enabled = spn_posY.enabled = spn_W.enabled = spn_H.enabled = SMTDSettings.MultiRegionData[theSel[1]][11] != true
				spn_posX.value = floor (SMTDSettings.MultiRegionData[theSel[1]][2]*RenderWidth)
				spn_posY.value = floor (SMTDSettings.MultiRegionData[theSel[1]][3]*RenderHeight)
				spn_W.value = floor (SMTDSettings.MultiRegionData[theSel[1]][4]*RenderWidth)
				spn_H.value = floor (SMTDSettings.MultiRegionData[theSel[1]][5]*RenderHeight)
				spn_TilesX.value =SMTDSettings.MultiRegionData[theSel[1]][6]
				spn_TilesY.value =SMTDSettings.MultiRegionData[theSel[1]][7]
				edt_notes.text= SMTDSettings.MultiRegionData[theSel[1]][8]
				chk_lock.state = SMTDSettings.MultiRegionData[theSel[1]][11] == true
			)
			else
			(
				spn_posX.enabled = spn_posY.enabled = spn_W.enabled = spn_H.enabled = false
				spn_posX.value = spn_posY.value = 0
				spn_W.value = spn_H.value = spn_TilesX.value = spn_TilesY.value=  1
				edt_notes.text = ""
			)
			updateEnabledStates()
			updateTotalCount()
		)

		fn updateCurrentLine =
		(
			for i in lastSelectedLines do
			(
				local theIndex = (mapTagToListIndex #(i))[1]
				--print theIndex
				local theX = (floor (SMTDSettings.MultiRegionData[i][2]*RenderWidth) ) as integer
				lv_regions.items.Item[theIndex-1].SubItems.Item[1].Text = theX as string
				lv_regions.items.Item[theIndex-1].SubItems.Item[1].Tag = theX as float

				local theY = (floor (SMTDSettings.MultiRegionData[i][3]*RenderHeight) ) as integer
				lv_regions.items.Item[theIndex-1].SubItems.Item[2].Text = theY as string
				lv_regions.items.Item[theIndex-1].SubItems.Item[2].Tag = theY as float

				local theW = (floor (SMTDSettings.MultiRegionData[i][4]*RenderWidth) ) as integer
				lv_regions.items.Item[theIndex-1].SubItems.Item[3].Text = theW as string
				lv_regions.items.Item[theIndex-1].SubItems.Item[3].Tag = theW as float

				local theH = (floor (SMTDSettings.MultiRegionData[i][5]*RenderHeight) ) as integer
				lv_regions.items.Item[theIndex-1].SubItems.Item[4].Text = theH as string
				lv_regions.items.Item[theIndex-1].SubItems.Item[4].Tag = theH as float

				lv_regions.items.Item[theIndex-1].SubItems.Item[5].Text = SMTDSettings.MultiRegionData[i][6] as string + "x" + SMTDSettings.MultiRegionData[i][7] as string

				local theArray = SMTDSettings.MultiRegionData[i][10]
				local theKeysCount = "--"
				if theArray != undefined and theArray.count > 0 do theKeysCount = theArray.count as string
				lv_regions.items.Item[theIndex-1].SubItems.Item[6].Text = theKeysCount
				lv_regions.items.Item[theIndex-1].SubItems.Item[6].Tag = if theArray != undefined then theArray.count as float else 0.0

				lv_regions.items.Item[theIndex-1].SubItems.Item[7].Text = (if SMTDSettings.MultiRegionData[i][11] != true then "--" else "Lock")
				lv_regions.items.Item[theIndex-1].SubItems.Item[8].Text = SMTDSettings.MultiRegionData[i][8]
				--updateSpinners()
			)
		)

		local createMRManipulator, createRegionGizmo, updateToRegionGizmo
		fn createUndoRecord theTitle=
		(
			if undoBufferIndex < undoBufferData.count do
			(
				for i = undoBufferData.count to undoBufferIndex+1 by -1 do
				(
					deleteItem undoBufferData i
					deleteItem undoBuffer i
				)
			)
			append undoBuffer theTitle
			local theSel = getListViewSelection()
			for i = 1 to SMTDSettings.MultiRegionData.count do SMTDSettings.MultiRegionData[i][9] = findItem theSel i > 0
			append undoBufferData (deepCopy SMTDSettings.MultiRegionData)
			undoBufferIndex = undoBufferData.count
			updateEnabledStates()
		)

		fn undoRedo =
		(
			SMTDSettings.MultiRegionData = deepCopy undoBufferData[undoBufferIndex]
			updateListView()
			local restoreSelection = for i = 1 to SMTDSettings.MultiRegionData.count where SMTDSettings.MultiRegionData[i][9]==True collect i
			setListViewSelection (lastSelectedLines= restoreSelection)
			createMRManipulator()
			createRegionGizmo (restoreSelection.count == 1)
			updateToRegionGizmo()
			updateSpinners()
			updateEnabledStates()
		)

		fn undoOneStepBack =
		(
			if undoBufferIndex > 1 do
			(
				undoBufferIndex -= 1
				undoRedo()
			)
		)

		fn redoOneStepForward =
		(
			if undoBufferIndex < undoBufferData.count do
			(
				undoBufferIndex += 1
				undoRedo()
			)
		)

		fn undoTo step =
		(
			undoBufferIndex = step
			undoRedo()
		)

		fn createUndoRedoMenu mode =
		(
			local txt = "" as stringStream
			format "rcmenu DL_MRRendering_Undo_Menu ( \n" to:txt
			if mode == #undo then
			(
				start = undoBufferIndex-1
				end = 1
				step = -1
				offset = 1
			)
			else
			(
				start = undoBufferIndex+1
				end = undoBuffer.count
				step = 1
				offset = 0
			)
			for i = start to end by step do
			(
				format "menuItem mnu_% \"%\" \n" i undoBuffer[i+offset] to:txt
				format "on mnu_% picked do SMTD_MultiRegionRendering.undoTo % \n" i i to:txt
			)
			format ")\n" to:txt
			DL_MRRendering_Undo_Menu = execute (txt as string)
		)

		on btn_hold pressed do createUndoRecord "HOLD Created Manually."
		on btn_undo pressed do undoOneStepBack()
		on btn_redo pressed do redoOneStepForward()
		on btn_undo rightclick do
		(
			theMenu = createUndoRedoMenu #undo
			popupMenu theMenu pos:mouse.screenpos
		)
		on btn_redo rightclick do
		(
			theMenu = createUndoRedoMenu #redo
			popupMenu theMenu pos:mouse.screenpos
		)


		fn updateFromRegionGizmo =
		(
			if lastSelectedLines.count == 1 do
			(
				local theRegionGizmo = getNodeByName "SMTDRegionGizmo"
				if isValidNode theRegionGizmo do
				(
					SMTDSettings.MultiRegionData[lastSelectedLines[1]][2] = theRegionGizmo.cornerX
					SMTDSettings.MultiRegionData[lastSelectedLines[1]][3] = theRegionGizmo.cornerY
					SMTDSettings.MultiRegionData[lastSelectedLines[1]][4] = theRegionGizmo.cornerX2-theRegionGizmo.cornerX
					SMTDSettings.MultiRegionData[lastSelectedLines[1]][5] = theRegionGizmo.cornerY2-theRegionGizmo.cornerY
				)
				updateCurrentLine()
				try( theMRManipulator.updateGizmos 0 "" )catch()
			)
		)

		fn updateToRegionGizmo =
		(
			if lastSelectedLines.count == 1 do
			(
				--local theRegionGizmo = getNodeByName "SMTDRegionGizmo"
				if isValidNode theRegionGizmo do
				(
					try
					(
						theRegionGizmo.cornerX = SMTDSettings.MultiRegionData[lastSelectedLines[1]][2]
						theRegionGizmo.cornerY = SMTDSettings.MultiRegionData[lastSelectedLines[1]][3]
						theRegionGizmo.cornerX2 = theRegionGizmo.cornerX+SMTDSettings.MultiRegionData[lastSelectedLines[1]][4]
						theRegionGizmo.cornerY2 = theRegionGizmo.cornerY+SMTDSettings.MultiRegionData[lastSelectedLines[1]][5]
						theRegionGizmo.tilesX = SMTDSettings.MultiRegionData[lastSelectedLines[1]][6]
						theRegionGizmo.tilesY = SMTDSettings.MultiRegionData[lastSelectedLines[1]][7]
					)catch()
				)
			)
			try( theMRManipulator.updateGizmos 0 "")catch()
			redrawViews()
		)

		fn createRegionGizmo state =
		(
			manipulateMode = true
			if state then
			(
				-- enforce safe frames when displaying the gizmo
				displaySafeFrames = true

				renderSceneDialog.Commit()
				theRegionGizmo = getNodeByName "SMTDRegionGizmo"
				if not isValidNode theRegionGizmo and DLRegionManipulator != undefined do
				(
					local oldSel= selection as array
					theRegionGizmo = DLRegionManipulator name:"SMTDRegionGizmo"
					try
					(
						local theExposureInterface = NodeExposureInterface.Create theRegionGizmo
						for i = 0 to 8 do theExposureInterface.SetExposed false i
					)catch()
					theRegionGizmo.transform.controller = transform_script()
					theRegionGizmo.isSelected = true
					redrawViews()
					theRegionGizmo.isSelected = false
					select oldSel
					theInterface = LayerManager.getLayerFromName "SMTD_Gizmos"
					if theInterface == undefined do
						theInterface = LayerManager.newLayerFromName "SMTD_Gizmos"
					theInterface.addnode theRegionGizmo
					theInterface.ishidden = theInterface.isFrozen = false
				)
				updateToRegionGizmo()
			)
			else
			(
				theRegionGizmo = getNodeByName "SMTDRegionGizmo"
				if isValidNode theRegionGizmo do delete theRegionGizmo
				try(LayerManager.deleteLayerByName "SMTD_Gizmos")catch()
			)
		)

		fn createMRManipulator =
		(
			if not SMTD_MultiRegionRendering.open do return false
			manipulateMode = true
			displaySafeFrames = true
			theMRManipulator = getNodeByName "DLMultiRegionManipulator"
			if theMRManipulator  == undefined do
			(
				theMRManipulator = DLMultiRegionManipulator name:"DLMultiRegionManipulator"
				try
				(
					local theExposureInterface = NodeExposureInterface.Create theMRManipulator
					for i = 0 to 8 do theExposureInterface.SetExposed false i
				)catch()
				--theMRManipulator.isFrozen = true
				theMRManipulator.transform.controller = transform_script()
				theInterface = LayerManager.getLayerFromName "SMTD_Gizmos"
				if theInterface == undefined do
					theInterface = LayerManager.newLayerFromName "SMTD_Gizmos"
				theInterface.addnode theMRManipulator
				theInterface.ishidden = theInterface.isFrozen = false
			)
			createRegionGizmo true
		)

		fn removeMRManipulator =
		(
			local theRegionGizmo = getNodeByName "DLMultiRegionManipulator"
			if isValidNode theRegionGizmo do delete theRegionGizmo
			try(LayerManager.deleteLayerByName "SMTD_Gizmos")catch()
			createRegionGizmo false
		)

		fn transpoint v =
		(
			local screen_width=RenderWidth
			local screen_height=RenderHeight
			local thePos = v * viewport.getTM()
			screen_origin = mapScreenToView [0,0] (thePos.z) [screen_width,screen_height]
			end_screen = mapScreenToView [screen_width,screen_height] (thePos.z) [screen_width,screen_height]
			world_size = screen_origin-end_screen
			x_aspect = screen_width/(abs world_size.x)
			y_aspect = screen_height/(abs world_size.y)
			screen_coords = point2 (x_aspect*(thePos.x-screen_origin.x)) (-(y_aspect*(thePos.y-screen_origin.y)))
			screen_coords.x /= screen_width
			screen_coords.y /= screen_height
			screen_coords
		)

		fn fitToSelection selected =
		(
			local xSize = gw.getWinSizeX() - 1
			local ySize = gw.getWinSizeY() - 1

			local vpAspect = gw.getWinSizeX() as float / gw.getWinSizeY() as float
			local rAspect = RenderWidth as float / RenderHeight * renderPixelAspect

			if rAspect > vpAspect then
			(
				ySize = gw.getWinSizeX() / rAspect
				xDiff = 0
				yDiff = (gw.getWinSizeY() - ySize)/2
			)
			else
			(
				xSize = gw.getWinSizeY() * rAspect
				xDiff = 0.5*(gw.getWinSizeX() - xSize)
				yDiff = 0
			)

			local xCoords = #()
			local yCoords = #()
			for o in selected do
			(
				local theTM = o.transform
				in coordsys theTM
				(
					local bbox = nodeLocalBoundingBox o
					local theMin = bbox[1]
					local theMax = bbox[2]
					gw.setTransform (theTM)
					for v in #(theMin, theMax, [theMin.x,theMin.y,theMax.z], [theMin.x,theMax.y,theMin.z], [theMax.x,theMin.y,theMin.z], [theMin.x,theMax.y,theMax.z], [theMax.x,theMin.y,theMax.z], [theMax.x,theMax.y,theMin.z]) do
					(
						local thePos = gw.transPoint v
						if thePos == undefined then
							thePos = transpoint v
						else
						(
							thePos -= [xDiff,yDiff,0]
							thePos.x /= xSize
							thePos.y /= ySize
						)
						append xCoords (thePos.x)
						append yCoords (thePos.y)
					)--end v loop
				)
			)
			theMinX = (amin xCoords)
			if theMinX < 0.0 do theMinX = 0.0

			theMaxX = (amax xCoords)
			if theMaxX > 1.0 do theMaxX = 1.0

			theMinY = (amin yCoords)
			if theMinY < 0.0 do theMinY = 0.0

			theMaxY = (amax yCoords)
			if theMaxY > 1.0 do theMaxY = 1.0

			--format "[%,%] [%,%]\n" theMinX theMinY theMaxX theMaxY
			#(theMinX, theMinY, theMaxX, theMaxY)
		)

		fn bestFitToSelection selected reportTime:true =
		(
			local st = timestamp()
			local xSize = gw.getWinSizeX() - 1
			local ySize = gw.getWinSizeY() - 1

			local vpAspect = gw.getWinSizeX() as float / gw.getWinSizeY() as float
			local rAspect = RenderWidth as float / RenderHeight * renderPixelAspect

			if rAspect > vpAspect then
			(
				ySize = gw.getWinSizeX() / rAspect
				xDiff = 0
				yDiff = (gw.getWinSizeY() - ySize)/2
			)
			else
			(
				xSize = gw.getWinSizeY() * rAspect
				xDiff = 0.5*(gw.getWinSizeX() - xSize)
				yDiff = 0
			)

			local xCoords = #()
			local yCoords = #()
			gw.setTransform(Matrix3 1)
			for o in selected do
			(
				--classof o
				local theMesh = snapshotAsMesh o
				--format "% numverts = %\n" o theMesh.numverts
				if classof theMesh == TriMesh do
				(
					local minX = 100.0
					local maxX = -100.0
					local minY = 100.0
					local maxY = -100.0
					for v = 1 to theMesh.numverts do
					(
						local thePos = gw.transPoint (getVert theMesh v)
						if thePos == undefined then
							thePos = transpoint (getVert theMesh v)
						else
						(
							thePos -= [xDiff,yDiff,0]
							thePos.x /= xSize
							thePos.y /= ySize
						)
						if thePos.x < minX do minX = thePos.x
						if thePos.x > maxX do maxX = thePos.x
						if thePos.y < minY do minY = thePos.y
						if thePos.y > maxY do maxY = thePos.y
					)--end v loop
					join xCoords #(minX, maxX)
					join yCoords #(minY, maxY)
					delete theMesh
				)--end if valid mesh
				--format "xCoords = %\n" xCoords
				--format "yCoords = %\n" yCoords
			)
			theMinX = if xCoords.count > 0 then (amin xCoords) else 0.0
			if theMinX < 0.0 do theMinX = 0.0

			theMaxX = if xCoords.count > 0 then (amax xCoords) else 1.0
			if theMaxX > 1.0 do theMaxX = 1.0

			theMinY = if yCoords.count > 0 then (amin yCoords) else 0.0
			if theMinY < 0.0 do theMinY = 0.0

			theMaxY = if yCoords.count > 0 then  (amax yCoords) else 1.0
			if theMaxY > 1.0 do theMaxY = 1.0

			if reportTime do
				SMTD_MainRollout.Ui_report ("+Precise Fit Region To "+ selected.count as string +" object"+(if selected.count == 1 then "" else "s")+" took "+ ((timestamp()-st)/1000.0) as string +" sec.")

			#(theMinX, theMinY, theMaxX, theMaxY)
		)

		fn FitToSelectionButtonEvent mode:#quick createUndo:true =
		(
			local theSel = getListViewSelection()
			local theObjects = (for o in selection where findItem GeometryClass.classes (classof o) > 0 and classof o != TargetObject collect o)
			if theSel.count == 1 and theObjects.count > 0 do
			(
				local result = if mode ==#quick then fitToSelection theObjects else bestfitToSelection theObjects

				local paddingPercent = if mode ==#quick then 0 else SMTDSettings.MultiRegionFitPadding
				local paddingX = (result[3]-result[1])*paddingPercent/200.0
				local paddingY = (result[4]-result[2])*paddingPercent/200.0
				result[1] -= paddingX
				if result[1] < 0.0 do result[1] = 0.0
				result[2] -= paddingY
				if result[2] < 0.0 do result[2] = 0.0
				result[3] += paddingX
				if result[3] > 1.0 do result[3] = 1.0
				result[4] += paddingY
				if result[4] > 1.0 do result[4] = 1.0

				SMTDSettings.MultiRegionData[theSel[1]][2] = result[1]
				SMTDSettings.MultiRegionData[theSel[1]][3] = result[2]
				SMTDSettings.MultiRegionData[theSel[1]][4] = result[3]-result[1]
				SMTDSettings.MultiRegionData[theSel[1]][5] = result[4]-result[2]
				updateCurrentLine()
				updateToRegionGizmo()
				if createUndo do
					createUndoRecord ( ( if mode ==#quick then "Quick " else "Tight ") + "Fit Region #"+theSel[1] as string+" To " + (if theObjects.count == 1 then ("'"+theObjects[1].name+"'") else (theObjects.count as string + " Objects")))
			)
		)

		on btn_FitOptions pressed do
		(
			popupMenu MultiRegion_FitPaddingOptions_Menu pos:mouse.screenpos
		)
		on btn_FitOptions rightclick do
		(
			popupMenu MultiRegion_FitPaddingOptions_Menu pos:mouse.screenpos
		)

		on btn_FitToSelection pressed do
		(
			FitToSelectionButtonEvent mode:#precise
		)
		on btn_FitToSelection rightclick do
		(
			FitToSelectionButtonEvent mode:#quick
		)

		fn TrackSelectionOverTime =
		(
			local st = timestamp()
			local theSel = getListViewSelection()
			local theObjects = (for o in selection where findItem GeometryClass.classes (classof o) > 0 and classof o != TargetObject collect o)
			local theDependencies = #()
			for o in objects do
			(
				join theDependencies (refs.DependentNodes o)
				for i in theObjects where findItem (refs.dependents o) i > 0 do appendIfUnique theDependencies i
			)
			--print "DEPENDENCIES:"
			--print theDependencies
			if theSel.count == 1 and theObjects.count > 0 do
			(
				local allObjects = objects as array
				local allObjectsVisibility = for o in allObjects collect o.isHidden
				for o in allObjects where findItem theObjects o == 0 and o != theRegionGizmo and findItem theDependencies o == 0 do o.isHidden = true
				local oldViewportMode = viewport.GetRenderLevel()
				viewport.SetRenderLevel #box
				local lastTime = sliderTime
				createUndoRecord ( "HOLD Before "+ ( if SMTD_MultiRegion2DTrackingStruct.TrackMode ==#quick then "Quick " else "Tight ") + "2D Tracking of Region #"+theSel[1] as string+" To " + (if theObjects.count == 1 then ("'"+theObjects[1].name+"'") else (theObjects.count as string + " Objects")))

				progressStart "Tracking Region..."
				local oldX = -1
				local oldY = -1
				local oldW = -1
				local oldH = -1
				for t = SMTD_MultiRegion2DTrackingStruct.FromFrame to SMTD_MultiRegion2DTrackingStruct.ToFrame do
				(
					if not (progressUpdate (100.0*(t-SMTD_MultiRegion2DTrackingStruct.FromFrame)/(SMTD_MultiRegion2DTrackingStruct.ToFrame-SMTD_MultiRegion2DTrackingStruct.FromFrame))) do exit
					sliderTime = t

					local result = if SMTD_MultiRegion2DTrackingStruct.TrackMode ==#quick then fitToSelection theObjects else bestfitToSelection theObjects reportTime:false

					local paddingX = (result[3]-result[1])*SMTD_MultiRegion2DTrackingStruct.PaddingPercent/200.0
					local paddingY = (result[4]-result[2])*SMTD_MultiRegion2DTrackingStruct.PaddingPercent/200.0
					result[1] -= paddingX
					if result[1] < 0.0 do result[1] = 0.0
					result[2] -= paddingY
					if result[2] < 0.0 do result[2] = 0.0
					result[3] += paddingX
					if result[3] > 1.0 do result[3] = 1.0
					result[4] += paddingY
					if result[4] > 1.0 do result[4] = 1.0

					if oldX as string == result[1] as string  AND oldY as string == result[2] as string AND oldW as string  == (result[3]-result[1]) as string  AND oldH as string == (result[4]-result[2]) as string then
					(
						local theArray = SMTDSettings.MultiRegionData[theSel[1]][10]
						if theArray == undefined do theArray = #()
						local theMin = 0
						local theEqual = 0
						for i = theArray.count to 1 by -1 do
						(
							if theArray[i][1] == sliderTime.frame as integer do deleteItem theArray i
						)
						SMTDSettings.MultiRegionData[theSel[1]][10] = theArray
					)
					else
					(
						SMTDSettings.MultiRegionData[theSel[1]][2] = result[1]
						SMTDSettings.MultiRegionData[theSel[1]][3] = result[2]
						SMTDSettings.MultiRegionData[theSel[1]][4] = result[3]-result[1]
						SMTDSettings.MultiRegionData[theSel[1]][5] = result[4]-result[2]
						updateCurrentLine()
						updateToRegionGizmo()
						setRegionKeyframe()
					)
					--remember the last values
					oldX = SMTDSettings.MultiRegionData[theSel[1]][2]
					oldY = SMTDSettings.MultiRegionData[theSel[1]][3]
					oldW = SMTDSettings.MultiRegionData[theSel[1]][4]
					oldH = SMTDSettings.MultiRegionData[theSel[1]][5]
					--format "% % % %\n" oldX oldY oldW oldH
				)
				SMTDSettings.MultiRegionData[theSel[1]][11] = true --lock after tracking!
				createUndoRecord ( ( if SMTD_MultiRegion2DTrackingStruct.TrackMode ==#quick then "Quick " else "Tight ") + "2D Tracking of Region #"+theSel[1] as string+" To " + (if theObjects.count == 1 then ("'"+theObjects[1].name+"'") else (theObjects.count as string + " Objects")))
				sliderTime = lastTime
				SMTD_MainRollout.Ui_report ("+"+( if SMTD_MultiRegion2DTrackingStruct.TrackMode ==#quick then "Quick " else "Tight ")+ "Tracking of Region #"+theSel[1] as string+" To "+ theObjects.count as string +" object"+(if theObjects.count == 1 then "" else "s")+" took "+ ((timestamp()-st)/1000.0) as string +" sec.")
				for i = 1 to allObjects.count do allObjects[i].isHidden = allObjectsVisibility[i]
				viewport.SetRenderLevel oldViewportMode
				progressEnd()

			)
		)

		on btn_track2D pressed do
		(
			local theObjects = (for o in selection where findItem GeometryClass.classes (classof o) > 0 and classof o != TargetObject collect o)
			if theObjects.count > 0 then
			(
				SMTD_MultiRegion2DTrackingStruct.TrackMode = #precise
				SMTD_MultiRegion2DTrackingStruct.PaddingPercent = SMTDSettings.MultiRegionFitPadding
				SMTD_MultiRegion2DTrackingStruct.SelectedObjects = theObjects
				createDialog SMTD_MultiRegion2DTrackingDialog modal:true
			)
			else
				messagebox "Please select at least one Geometry object and try again!" title:"Region Tracking"
		)
		on btn_track2D rightclick do
		(
			local theObjects = (for o in selection where findItem GeometryClass.classes (classof o) > 0 and classof o != TargetObject collect o)
			if theObjects.count > 0 then
			(
				SMTD_MultiRegion2DTrackingStruct.TrackMode = #quick
				SMTD_MultiRegion2DTrackingStruct.PaddingPercent = 0.0
				SMTD_MultiRegion2DTrackingStruct.SelectedObjects = theObjects
				createDialog SMTD_MultiRegion2DTrackingDialog modal:true
			)
			else
				messagebox "Please select at least one Geometry object and try again!" title:"Region Tracking"
		)

		on spn_posX changed val do
		(
			local theSel = getListViewSelection()
			if theSel.count == 1 do
			(
				SMTDSettings.MultiRegionData[theSel[1]][2] = 1.0*val/renderWidth
				updateCurrentLine()
				updateToRegionGizmo()
			)
		)
		on spn_posY changed val do
		(
			local theSel = getListViewSelection()
			if theSel.count == 1 do
			(
				SMTDSettings.MultiRegionData[theSel[1]][3] = 1.0*val/renderHeight
				updateCurrentLine()
				updateToRegionGizmo()
			)
		)
		on spn_W changed val do
		(
			local theSel = getListViewSelection()
			if theSel.count == 1 do
			(
				SMTDSettings.MultiRegionData[theSel[1]][4] = 1.0*val/renderWidth
				updateCurrentLine()
				updateToRegionGizmo()
			)
		)
		on spn_H changed val do
		(
			local theSel = getListViewSelection()
			if theSel.count == 1 do
			(
				SMTDSettings.MultiRegionData[theSel[1]][5] = 1.0*val/renderHeight
				updateCurrentLine()
				updateToRegionGizmo()
			)
		)
		on spn_TilesX changed val do
		(
			local theSel = getListViewSelection()
			for i in theSel do
			(
				SMTDSettings.MultiRegionData[i][6] = val
			)
			updateCurrentLine()
			updateToRegionGizmo()
			updateEnabledStates()
			updateTotalCount()
		)
		on spn_TilesY changed val do
		(
			local theSel = getListViewSelection()
			for i in theSel do
			(
				SMTDSettings.MultiRegionData[i][7] = val
			)
			updateCurrentLine()
			updateToRegionGizmo()
			updateEnabledStates()
			updateTotalCount()
		)

		on chk_lock changed state do
		(
			local theSel = getListViewSelection()
			for i in theSel do
			(
				SMTDSettings.MultiRegionData[i][11] = state
			)
			updateCurrentLine()
			updateToRegionGizmo()
			updateEnabledStates()
			updateSpinners()
		)

		on edt_notes entered txt do
		(
			local theSel = getListViewSelection()
			if theSel.count == 1 and txt != "" do
			(
				SMTDSettings.MultiRegionData[theSel[1]][8] = substituteString (substituteString txt "\"" "'") "\\" "/"
				updateCurrentLine()
			)
		)

		on btn_addRegion pressed do
		(
			local theSel = getListViewSelection()
			local theObjects = (for o in selection where findItem GeometryClass.classes (classof o) > 0 and classof o != TargetObject collect o)
			if theObjects.count > 0 OR SMTDSettings.MultiRegionData.count == 0 OR theSel.count == 0 then
			(
				append SMTDSettings.MultiRegionData #(true, 0.0, 0.0, 1.0, 1.0, 1, 1, "New Region")
				updateListView()
				lastSelectedLines = #(SMTDSettings.MultiRegionData.count)
				setListViewSelection (mapListIndexToTag lastSelectedLines)
				if theObjects.count > 0 do
					FitToSelectionButtonEvent mode:#quick createUndo:false
			)
			else
			(

				theMinX = 10000
				theMinY = 10000
				theMaxX = -10000
				theMaxY = -10000
				for i in theSel do
				(
					if SMTDSettings.MultiRegionData[i][2] < theMinX do theMinX = SMTDSettings.MultiRegionData[i][2]
					if SMTDSettings.MultiRegionData[i][2]+SMTDSettings.MultiRegionData[i][4] > theMaxX do theMaxX = SMTDSettings.MultiRegionData[i][2]+SMTDSettings.MultiRegionData[i][4]
					if SMTDSettings.MultiRegionData[i][3] < theMinY do theMinY = SMTDSettings.MultiRegionData[i][3]
					if SMTDSettings.MultiRegionData[i][3]+SMTDSettings.MultiRegionData[i][5] > theMaxY do theMaxY = SMTDSettings.MultiRegionData[i][3]+SMTDSettings.MultiRegionData[i][5]
				)
				theHeight = theMaxY-theMinY
				theWidth = theMaxX-theMinX
				if theMaxX-theMinX > theMaxY-theMinY then
				(
					theMinY += theHeight
				)
				else
				(
					theMinX += theWidth
				)
				if theMinX < 0 do theMinX = 0
				if theMinY < 0 do theMinY = 0
				if theMinX+theWidth > 1 do theWidth = 1.0-theMinX
				if theMinY+theHeight > 1 do theHeight = 1.0-theMinY
				if theHeight > 0 and theWidth > 0 then
					append SMTDSettings.MultiRegionData #(true, theMinX, theMinY, theWidth, theHeight, 1, 1, "New Region")
				else
					return false
			)
			updateListView()
			lastSelectedLines=#(SMTDSettings.MultiRegionData.count)
			setListViewSelection (mapListIndexToTag lastSelectedLines)
			updateSpinners()
			createRegionGizmo true
			updateToRegionGizmo()
			updateEnabledStates()
			createUndoRecord ("Add New Region "+(SMTDSettings.MultiRegionData.count+1)  as string)
		)

		fn cloneLeftRight dir =
		(
			local theSel = getListViewSelection()
			local theNewSelection = #()
			for i in theSel do
			(
				local newRecord = deepCopy SMTDSettings.MultiRegionData[i]
				newRecord[10]=#()
				newRecord[11]=false
				theWidth = copy newRecord[4]
				if dir == #right then
				(
					newRecord[2] += theWidth
					if newRecord[2]+theWidth > 1.0 do theWidth = 1.0-newRecord[2]
					newRecord[4] = theWidth
					newRecord[8] = "Clone Right - Region "+i as string
				)
				else
				(
					newRecord[2] -= theWidth
					if newRecord[2] < 0.0 do
					(
						theWidth -= abs (newRecord[2])
						newRecord[2] = 0
					)
					newRecord[4] = theWidth
					newRecord[8] = "Clone Left - Region "+i as string
				)
				if theWidth > 0 do
				(
					append SMTDSettings.MultiRegionData newRecord
					append theNewSelection SMTDSettings.MultiRegionData.count
				)
			)
			if theNewSelection.count > 0 do
			(
				updateListView()
				updateSpinners()
				lastSelectedLines=theNewSelection
				setListViewSelection (mapListIndexToTag lastSelectedLines)
				createRegionGizmo (theNewSelection.count == 1)
				if theNewSelection.count == 1 then
				(
					updateToRegionGizmo()
					theString = ("Clone "+ (if dir == #left then "Left" else "Right")+" Region #" + theSel[1] as string + " To #" +theNewSelection[1]  as string)
				)
				else
				(
					theString = ("Clone "+ (if dir == #left then "Left " else "Right ")+ theSel.count as string + " Regions")
				)
				createUndoRecord theString
				redrawViews()
			)
		)

		on btn_cloneRight pressed do cloneLeftRight #left
		on btn_cloneRight rightclick do cloneLeftRight #right


		fn cloneUpDown dir =
		(
			local theSel = getListViewSelection()
			local theNewSelection = #()
			for i in theSel do
			(
				local newRecord = deepCopy SMTDSettings.MultiRegionData[i]
				newRecord[10]=#()
				newRecord[11]=false
				theHeight = copy newRecord[5]

				if dir == #down then
				(
					newRecord[3] += theHeight
					if newRecord[3]+theHeight > 1.0 do theHeight = 1.0-newRecord[3]
					newRecord[5] = theHeight
					newRecord[8] = "Clone Down - Region "+i as string
				)
				else
				(
					newRecord[3] -= theHeight
					if newRecord[3] < 0.0 do
					(
						theHeight -= abs (newRecord[3])
						newRecord[3] = 0
					)
					newRecord[5] = theHeight
					newRecord[8] = "Clone Up - Region "+i as string
				)
				if theHeight > 0 do
				(
					append SMTDSettings.MultiRegionData newRecord
					append theNewSelection SMTDSettings.MultiRegionData.count
				)
			)
			if theNewSelection.count > 0 do
			(
				updateListView()
				updateSpinners()

				lastSelectedLines=theNewSelection
				setListViewSelection (mapListIndexToTag lastSelectedLines)

				createRegionGizmo (theNewSelection.count == 1)
				if theNewSelection.count == 1 then
				(
					updateToRegionGizmo()
					theString = ("Clone "+ (if dir == #left then "Left" else "Right")+" Region #" + theSel[1] as string + " To #" +theNewSelection[1]  as string)
				)
				else
				(
					theString = ("Clone "+ (if dir == #left then "Left " else "Right ")+ theSel.count as string + " Regions")
				)
				createUndoRecord theString
				redrawViews()
			)
		)
		on btn_cloneDown pressed do cloneUpDown #up
		on btn_cloneDown rightclick do	cloneUpDown #down

		fn saveRegionsPresetFile =
		(
			theOutpath = SMTDPaths.SettingsDir + "MultiRegionPresets\\"
			makeDir theOutpath all:true
			theOutpath += if MaxFileName == "" then
				(SMTDSettings.MultiRegionData.count as string + "_" +"Regions.RegionPreset")
				else
				(getFileNameFile maxFileName+"_"+ SMTDSettings.MultiRegionData.count as string + "_" + "Regions" + ".RegionPreset")
			theOutFile = getSaveFileName filename:theOutpath types:"Region Presets (*.RegionPreset)|*.RegionPreset|All Files (*.*)|*.*"
			if theOutFile != undefined do
			(
				local theFileHandle = createFile theOutFile encoding:#utf8 writeBOM:true
				with PrintAllElements on format "global DeadlineMultiRegionData = %\n" SMTDSettings.MultiRegionData to:theFileHandle
				close theFileHandle
			)
		)

		fn loadRegionsPresetFile =
		(
			theOutpath = SMTDPaths.SettingsDir + "MultiRegionPresets\\"
			theOutpath += "*.RegionPreset"
			theOutFile = getOpenFileName filename:theOutpath types:"Region Presets (*.RegionPreset)|*.RegionPreset|All Files (*.*)|*.*"
			if theOutFile != undefined do
			(
				createUndoRecord ("HOLD Before Loading Disk Preset [" + getFileNameFile theOutFile +"]")
				global DeadlineMultiRegionData = #()
				fileIn theOutFile
				if DeadlineMultiRegionData != undefined and DeadlineMultiRegionData.count > 0 do
					SMTDSettings.MultiRegionData = deepCopy DeadlineMultiRegionData
				updateListView()

				lastSelectedLines=#(1)
				setListViewSelection (mapListIndexToTag lastSelectedLines)

				updateSpinners()
				createRegionGizmo true
				updateToRegionGizmo()
				updateEnabledStates()
				createUndoRecord ("After Loading Disk Preset [" + getFileNameFile theOutFile +"]")
			)
		)

		fn mergeRegionsPresetFile =
		(
			theOutpath = SMTDPaths.SettingsDir + "MultiRegionPresets\\"
			theOutpath += "*.RegionPreset"
			theOutFile = getOpenFileName filename:theOutpath types:"Region Presets (*.RegionPreset)|*.RegionPreset|All Files (*.*)|*.*"
			if theOutFile != undefined do
			(
				createUndoRecord ("HOLD Before Merging Disk Preset [" + getFileNameFile theOutFile +"]")
				global DeadlineMultiRegionData = #()
				fileIn theOutFile
				if DeadlineMultiRegionData != undefined and DeadlineMultiRegionData.count > 0 do
					join SMTDSettings.MultiRegionData (deepCopy DeadlineMultiRegionData)
				updateListView()
				updateSpinners()
				createRegionGizmo false
				updateEnabledStates()
				createUndoRecord ("After Merging Disk Preset [" + getFileNameFile theOutFile +"]")
			)
		)

		on btn_loadSaveRegions pressed do popupMenu MultiRegion_FileSave_Menu pos:mouse.screenpos

		on btn_selectInvertSelection pressed do --select all
		(
			setListViewSelection (for i = 1 to SMTDSettings.MultiRegionData.count collect i)
			local theSel = lastSelectedLines = getListViewSelection()
			createRegionGizmo (theSel.count == 1)
			updateSpinners()
			updateEnabledStates()
		)

		on btn_selectInvertSelection rightclick do
		(
			local theSel = getListViewSelection()
			setListViewSelection ((#{1..SMTDSettings.MultiRegionData.count}-(theSel as bitarray)) as array)
			local theSel = getListViewSelection()
			lastSelectedLines  = mapTagToListIndex theSel
			createRegionGizmo (theSel.count == 1)
			updateToRegionGizmo()
			updateSpinners()
			updateEnabledStates()
		)

		on btn_removeRegion pressed do
		(
			local theSel = getListViewSelection()
			if theSel.count > 0 do
			(
				local theString = "Remove "
				theString += if theSel.count == 1 then
					"Region #"+theSel[1] as string
				else
					theSel.count as string +" Regions"
				createUndoRecord ("HOLD Before " +theString)
				for i = theSel.count to 1 by -1 do
					deleteItem SMTDSettings.MultiRegionData theSel[i]
				updateListView()
				updateSpinners()
				createRegionGizmo false
				updateEnabledStates()
				redrawViews()
				createUndoRecord (theString)
			)
		)

		on btn_updateRegions pressed do
		(
			updateListView()
			updateSpinners()
		)

		fn setRegionKeyframe =
		(
			local theSel = getListViewSelection()
			if theSel.count > 0 do
			(
				for aSel in theSel do
				(
					local theArray = SMTDSettings.MultiRegionData[aSel][10]
					if theArray == undefined do theArray = #()
					local theMin = 0
					local theEqual = 0
					for i = 1 to theArray.count do
					(
						if theArray[i][1] <= sliderTime.frame as integer do theMin = i
						if theArray[i][1] == sliderTime.frame as integer do theEqual = i
					)
					--format "theMin = %  theEqual = %\n" theMin theEqual
					if theEqual == 0 then
						insertItem #(sliderTime.frame as integer, SMTDSettings.MultiRegionData[aSel][2], SMTDSettings.MultiRegionData[aSel][3], SMTDSettings.MultiRegionData[aSel][4], SMTDSettings.MultiRegionData[aSel][5] ) theArray (theMin+1)
					else
						theArray[theEqual] = #(sliderTime.frame as integer, SMTDSettings.MultiRegionData[aSel][2], SMTDSettings.MultiRegionData[aSel][3], SMTDSettings.MultiRegionData[aSel][4], SMTDSettings.MultiRegionData[aSel][5] )
					SMTDSettings.MultiRegionData[aSel][10] = theArray
					--format "%\n" SMTDSettings.MultiRegionData[aSel][10]
				)
				updateListView()
			)
		)

		on btn_setKey pressed do
		(
			setRegionKeyframe()
		)

		on btn_deleteKey pressed do
		(
			local theSel = getListViewSelection()
			if theSel.count > 0 do
			(
				createUndoRecord ("HOLD Before Deleting Current Frame Keys.")
				for aSel in theSel do
				(
					local theArray = SMTDSettings.MultiRegionData[aSel][10]
					if theArray == undefined do theArray = #()
					local theMin = 0
					local theEqual = 0
					for i = theArray.count to 1 by -1 do
					(
						if theArray[i][1] == sliderTime.frame as integer do deleteItem theArray i
					)
					SMTDSettings.MultiRegionData[aSel][10] = theArray
					--format "%\n" SMTDSettings.MultiRegionData[aSel][10]
				)
				createUndoRecord ("Delete Current Frame "+(sliderTime.frame as integer) as string+" Keys from "+theSel.count as string+" highlighted Region"+(if theSel.count == 1 then "." else "s."))
				updateListView()
			)
		)

		on btn_deleteKey rightclick do
		(
			local theSel = getListViewSelection()
			if theSel.count > 0 do
			(
				if (querybox ("Are you sure you want to DELETE ALL KEYS from "+ theSel.count as string + " Highlighted Region"+(if theSel.count == 1 then "?" else "s?")) title:"Delete All Keys?") then
				(
					createUndoRecord ("HOLD Before Deleting ALL Keys.")
					for aSel in theSel do
					(
						SMTDSettings.MultiRegionData[aSel][10] = #()
					)
					createUndoRecord ("Delete ALL Keys from "+theSel.count as string+" highlighted Region"+(if theSel.count == 1 then "." else "s."))
					updateListView()
				)
			)
		)

		on btn_prevKey pressed do
		(
			local theSel = getListViewSelection()
			local prevFrames = #()
			local prevTime = sliderTime.frame as integer
			if theSel.count > 0 do
			(
				for aSel in theSel do
				(
					local theArray = SMTDSettings.MultiRegionData[aSel][10]
					if theArray == undefined do theArray = #()
					for i = theArray.count to 1 by -1 do
					(
						if theArray[i][1] < prevTime do append prevFrames theArray[i][1]
					)
					sort prevFrames
					if prevFrames.count >0 do prevTime = prevFrames[prevFrames.count]
					sliderTime = prevTime
				)
				--updateListView()
			)
		)
		on btn_nextKey pressed do
		(
			local theSel = getListViewSelection()
			local nextFrames = #()
			local nextTime = sliderTime.frame as integer
			if theSel.count > 0 do
			(
				for aSel in theSel do
				(
					local theArray = SMTDSettings.MultiRegionData[aSel][10]
					if theArray == undefined do theArray = #()
					for i = theArray.count to 1 by -1 do
					(
						if theArray[i][1] > nextTime do append nextFrames theArray[i][1]
					)
					sort nextFrames
					if nextFrames.count > 0 do nextTime = nextFrames[1]
					sliderTime = nextTime
				)
				--updateListView()
			)
		)


		fn interpolateKeyframe tileIndex =
		(
			local theArray = SMTDSettings.MultiRegionData[tileIndex][10]
			if theArray == undefined or theArray.count == 0 then
				#(sliderTime.frame as integer, SMTDSettings.MultiRegionData[tileIndex][2], SMTDSettings.MultiRegionData[tileIndex][3], SMTDSettings.MultiRegionData[tileIndex][4], SMTDSettings.MultiRegionData[tileIndex][5])
			else if theArray.count == 1 then theArray[1]
			else
			(
				local theMin = 0
				local theEqual = 0
				for i = 1 to theArray.count do
				(
					if theArray[i][1] <= sliderTime.frame as integer do theMin = i
					if theArray[i][1] == sliderTime.frame as integer do theEqual = i
				)
				returnValue = if theMin == theArray.count then
					theArray[theArray.count]
				else if theMin == 0 then theArray[1]
				else
				(
					local theLeftRecord  = theArray[theMin]
					local theRightRecord = theArray[theMin+1]
					local factor = (1.0 * sliderTime.frame as integer-theLeftRecord[1]) / (theRightRecord[1]-theLeftRecord[1])
					--format "% (%)-> %\n" theLeftRecord factor theRightRecord
					#(sliderTime.frame as integer, theLeftRecord[2]*(1-factor) + theRightRecord[2]*factor, theLeftRecord[3]*(1-factor) + theRightRecord[3]*factor, theLeftRecord[4]*(1-factor) + theRightRecord[4]*factor, theLeftRecord[5]*(1-factor) + theRightRecord[5]*factor )
				)
				returnValue
			)
		)

		on ddl_BackgroundMode selected itm do
		(
			updateEnabledStates()
		)

		fn createFromMaxRegion =
		(
			local theRect = if viewport.activeViewport > 0 then
			(
				viewport.getRegionRect (viewport.activeViewport)
			)
			else
			(
				Box2 0 0 RenderWidth RenderHeight
			)
			append SMTDSettings.MultiRegionData #(true, (1.0*theRect.x/RenderWidth), (1.0*theRect.y/RenderHeight), (1.0*theRect.w/RenderWidth), (1.0*theRect.h/RenderHeight), 1, 1, "3ds Max Region Gizmo [X:"+ theRect.x as string + " Y:"+ theRect.y as string + " W:"+theRect.w as string + " H:"+theRect.h as string + "]" )
			updateListView()
			setListViewSelection (lastSelectedLines=#(SMTDSettings.MultiRegionData.count))
			createMRManipulator()
			createRegionGizmo true
			updateToRegionGizmo()
			updateSpinners()
			updateEnabledStates()
			createUndoRecord ("Create Region From 3ds Max Region Gizmo [X:"+ theRect.x as string + " Y:"+ theRect.y as string + " W:"+theRect.w as string + " H:"+theRect.h as string + "]")
		)

		fn createFromTilesGrid usertiles:false =
		(
			local result = if SMTDSettings.MultiRegionData.count == 0 then #no else (yesNoCancelBox ("Click [Yes] to REPLACE the Regions with a Grid of " + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string + " Tiles.\nClick [No] to APPEND to the existing list.\nClick [Cancel] to do nothing.") title:"Replace Or Append Regions?")
			case result of
			(
				#yes: (
							createRegionGizmo false
							removeMRManipulator()
							SMTDSettings.MultiRegionData = #()
				)
				#cancel: return false
			)
			local cnt = 0
			for y in 1 to SMTDSettings.TilesInY do
			(
				for x in 1 to SMTDSettings.TilesInX do
				(
					if usertiles == false or findItem SMTDSettings.CustomTiles [x,y] > 0 do
					(
						cnt +=1
						append SMTDSettings.MultiRegionData #(true, 1.0*(x-1)/SMTDSettings.TilesInX, 1.0*(y-1)/SMTDSettings.TilesInY, 1.0/SMTDSettings.TilesInX, 1.0/SMTDSettings.TilesInY, 1, 1, SMTDSettings.TilesInX as string + "x"+ SMTDSettings.TilesInY as string+ " Grid Tile #" + cnt as string)
					)
				)
			)
			updateListView()
			setListViewSelection (lastSelectedLines=#(1))
			createMRManipulator()
			createRegionGizmo true
			updateToRegionGizmo()
			updateSpinners()
			updateEnabledStates()
			if usertiles == true then
				createUndoRecord ("Create "+SMTDSettings.CustomTiles.count as string+" User Regions From "+SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string+ " Tiles Grid")
			else
				createUndoRecord ("Create Regions From "+SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string+ " Tiles Grid")
		)

		fn createFromSceneSelection =
		(
			local theSelection = (for o in selection where findItem GeometryClass.classes (classof o) > 0 collect o)
			if theSelection.count == 0 do
			(
				messagebox "No renderable geometry objects selected!" title:"Cannot Create Regions!"
				return false
			)
			local result = if SMTDSettings.MultiRegionData.count == 0 then #no else (yesNoCancelBox ("Click [Yes] to REPLACE the Regions.\nClick [No] to APPEND to the existing list.\nClick [Cancel] to do nothing.") title:"Replace Or Append Regions?")
			case result of
			(
				#yes: (
							createRegionGizmo false
							removeMRManipulator()
							SMTDSettings.MultiRegionData = #()
				)
				#cancel: return false
			)

			for o in theSelection do
			(
				local result = bestFitToSelection #(o)
				local paddingX = (result[3]-result[1])*SMTDSettings.MultiRegionFitPadding/200.0
				local paddingY = (result[4]-result[2])*SMTDSettings.MultiRegionFitPadding/200.0
				result[1] -= paddingX
				if result[1] < 0.0 do result[1] = 0.0
				result[2] -= paddingY
				if result[2] < 0.0 do result[2] = 0.0
				result[3] += paddingX
				if result[3] > 1.0 do result[3] = 1.0
				result[4] += paddingY
				if result[4] > 1.0 do result[4] = 1.0
				append SMTDSettings.MultiRegionData #(true, result[1], result[2], result[3]-result[1], result[4]-result[2], 1, 1, "Region from '" + o.name+"'")
			)
			updateListView()
			setListViewSelection (lastSelectedLines=#(1))
			createMRManipulator()
			createRegionGizmo true
			updateToRegionGizmo()
			updateSpinners()
			updateEnabledStates()
			createUndoRecord ("Create Regions From " +theSelection.count as string+" Selected Objects.")
		)

		on btn_createFrom pressed do popupMenu MultiRegion_CreateFrom_Menu pos:mouse.screenpos

		fn mergeRegions theSel deleteRest:true =
		(
			local theMinX = 1000000
			local theMinY = 1000000
			local theMaxX = -1000000
			local theMaxY = -1000000
			for i in theSel do
			(
				if SMTDSettings.MultiRegionData[i][2] < theMinX do theMinX = SMTDSettings.MultiRegionData[i][2]
				if SMTDSettings.MultiRegionData[i][2]+SMTDSettings.MultiRegionData[i][4] > theMaxX do theMaxX = SMTDSettings.MultiRegionData[i][2]+SMTDSettings.MultiRegionData[i][4]

				if SMTDSettings.MultiRegionData[i][3] < theMinY do theMinY = SMTDSettings.MultiRegionData[i][3]
				if SMTDSettings.MultiRegionData[i][3]+SMTDSettings.MultiRegionData[i][5] > theMaxY do theMaxY = SMTDSettings.MultiRegionData[i][3]+SMTDSettings.MultiRegionData[i][5]
			)
			if deleteRest do
				for i = theSel.count to 2 by -1 do deleteItem SMTDSettings.MultiRegionData theSel[i]
			SMTDSettings.MultiRegionData[theSel[1]][2] = theMinX
			SMTDSettings.MultiRegionData[theSel[1]][3] = theMinY
			SMTDSettings.MultiRegionData[theSel[1]][4] = theMaxX-theMinX
			SMTDSettings.MultiRegionData[theSel[1]][5] = theMaxY-theMinY
			local theNumbers = ""
			for i in theSel do theNumbers+=i as string+","
			theNumbers[theNumbers.count]	= "."
			SMTDSettings.MultiRegionData[theSel[1]][8] = "Merged Regions " + theNumbers

		)
		on btn_mergeHighlighted pressed do
		(
			local theSel = getListViewSelection()
			if theSel.count > 1 do
			(
				mergeRegions theSel
				updateListView()
				setListViewSelection (lastSelectedLines=#(theSel[1]))
				createMRManipulator()
				createRegionGizmo true
				updateToRegionGizmo()
				updateSpinners()
				updateEnabledStates()
				createUndoRecord ("Merge "+theSel.count as string+" Selected Regions")
			)
		)


		fn IsContainedInBoxes theExistingRegions TestRegion =
		(
			local returnValue = false
			for j in theExistingRegions while not returnValue do
				if contains j TestRegion.center do returnValue = true
			returnValue
		)

		fn optimizeBorderingRegions theNewRegions mode:#h =
		(
			for i = theNewRegions.count-1 to 1 by -1 do
			(
				local reg1x1 = theNewRegions[i][1]
				local reg1x2 = theNewRegions[i][3]
				local reg1y1= theNewRegions[i][2]
				local reg1y2 = theNewRegions[i][4]
				for j = theNewRegions.count to 2 by -1 do
				(
					local reg2x1 = theNewRegions[j][1]
					local reg2x2 = theNewRegions[j][3]
					local reg2y1= theNewRegions[j][2]
					local reg2y2 = theNewRegions[j][4]

					local mergeRegions = false
					--if mode === #h and reg1x1 == reg2x2 and reg1y1 == reg2y1 and reg1y2 ==reg2y2 do mergeRegions = true
					if mode == #h do
					(
						if reg1x2 == reg2x1 and reg1y1 == reg2y1 and reg1y2 ==reg2y2 do mergeRegions = true
						if mergeRegions do
						(
							deleteItem theNewRegions j
							theNewRegions[i] = #(reg1x1, reg1y1, reg2x2, reg1y2)
							working = true
						)
					)
					if mode == #v do
					(
						if reg1x1 == reg2x1 and reg1x2 == reg2x2 and reg1y2 ==reg2y1 do mergeRegions = true
						if mergeRegions do
						(
							deleteItem theNewRegions j
							theNewRegions[i] = #(reg1x1, reg1y1, reg1x2, reg2y2)
							working = true
						)
					)
				)
			)
			theNewRegions
		)

		fn fillRegions mode:#g =
		(
			local oldRegionCount = SMTDSettings.MultiRegionData.count
			createUndoRecord ("HOLD "+ oldRegionCount as string+" Regions Before Filling Empty Areas")
			local theGridX = #(0.0,1.0)
			local theGridY = #(0.0,1.0)
			local theExistingRegions = #()

			for i = 1 to SMTDSettings.MultiRegionData.count do
			(
				local region1Def = SMTDSettings.MultiRegionData[i]
				local x11 = region1Def[2]
				local y11 = region1Def[3]
				local x12 = (region1Def[2]+region1Def[4])
				local y12 = (region1Def[3]+region1Def[5])
				appendIfUnique theGridX x11
				appendIfUnique theGridX x12
				appendIfUnique theGridY y11
				appendIfUnique theGridY y12
				append theExistingRegions (Box2 [x11*RenderWidth,y11*RenderHeight] [x12*RenderWidth, y12*RenderHeight] )
			)
			sort theGridX
			sort theGridY
			--with printAllElements on format "theGridX = %\n" theGridX
			--with printAllElements on format "theGridY = %\n" theGridY

			--format "theExistingRegions=%\n" theExistingRegions
			local theNewRegions = #()
			for y = 1 to theGridY.count-1 do
			(
				for x = 1 to theGridX.count-1 do
				(
					local test = IsContainedInBoxes theExistingRegions (Box2 [theGridX[x]*RenderWidth,theGridY[y]*RenderHeight] [theGridX[x+1]*RenderWidth,theGridY[y+1]*RenderHeight] )
					--format "Region % Contained: %\n" (Box2 [theGridX[x]*RenderWidth,theGridY[y]*RenderHeight] [theGridX[x+1]*RenderWidth,theGridY[y+1]*RenderHeight] ) test
					if not test do
						append theNewRegions #(theGridX[x], theGridY[y], theGridX[x+1], theGridY[y+1])
				)--end x loop
			)--end y loop
			--with printAllElements on format "theNewRegions = %\n" theNewRegions

			if mode == #h or mode == #b do theNewRegions = optimizeBorderingRegions theNewRegions mode:#h
			if mode == #v or mode == #b do theNewRegions = optimizeBorderingRegions theNewRegions mode:#v

			local cnt = 0
			for i in theNewRegions do
			(
				cnt+=1
				append SMTDSettings.MultiRegionData #(true, i[1], i[2], i[3]-i[1], i[4]-i[2], 1,1, "Fill Region "+cnt as string, false, #(), false)
			)

			if cnt > 0 do
			(
				updateListView()
				lastSelectedLines = #(1)
				createMRManipulator()
				createRegionGizmo true
				updateToRegionGizmo()
				updateSpinners()
				updateEnabledStates()
				createUndoRecord ("HOLD After Filling Empty Areas with "+cnt as string+ " Regions")
			)
		)

		fn optimizeOverlappingRegions theThreshold:0.25 =
		(
			local oldRegionCount = SMTDSettings.MultiRegionData.count
			createUndoRecord ("HOLD Before Optimizing "+ oldRegionCount as string+" Regions")
			local done = false
			while not done do
			(
				local toDelete = #()
				for i = SMTDSettings.MultiRegionData.count to 2 by -1 where not findItem toDelete i > 0 do
				(
					local region1Def = SMTDSettings.MultiRegionData[i]
					local x11 = region1Def[2]*RenderWidth
					local y11 = region1Def[3]*RenderHeight
					local x12 = (region1Def[2]+region1Def[4])*RenderWidth
					local y12 = (region1Def[3]+region1Def[5])*RenderHeight
					local a1= region1Def[4]*region1Def[5]*RenderWidth*RenderHeight

					for j = i-1  to 1 by -1 where not findItem toDelete j > 0 do
					(
						local region2Def = SMTDSettings.MultiRegionData[j]
						local x21 = region2Def[2]*RenderWidth
						local y21 = region2Def[3]*RenderHeight
						local x22 = (region2Def[2]+region2Def[4])*RenderWidth
						local y22 = (region2Def[3]+region2Def[5])*RenderHeight
						local a2= region2Def[4]*region2Def[5]*RenderWidth*RenderHeight

						local x_overlap = amax #(0, amin #(x12,x22) - amax #(x11,x21))
						local y_overlap = amax #(0, amin #(y12,y22) - amax #(y11,y21))
						local overlapArea = x_overlap * y_overlap
						--format "overlap area: % \n" overlapArea
						--format "a1: % a2: %\n" a1 a2
						if overlapArea > 0 do
						(
							if a1 > a2 then
							(
								--format "Ratio 2: %\n" (overlapArea/a2)
								if overlapArea/a2 > theThreshold do
								(
									appendIfUnique toDelete i
									mergeRegions #(j,i) deleteRest:false
								)
							)
							else
							(
								--format "Ratio 1: %\n" ( overlapArea/a1)
								if overlapArea/a1 > theThreshold  do
								(
									appendIfUnique toDelete j
									mergeRegions #(i,j) deleteRest:false
								)
							)
						)
					)
				)
				sort toDelete
				--format "ToDelete = %\n" toDelete
				--format "SMTDSettings.MultiRegionData = %\n" SMTDSettings.MultiRegionData
				for i = toDelete.count to 1 by -1 do deleteItem SMTDSettings.MultiRegionData toDelete[i]
				if toDelete.count == 0 do done = true
			)
			updateListView()
			lastSelectedLines = #(1)
			createMRManipulator()
			createRegionGizmo true
			updateToRegionGizmo()
			updateSpinners()
			updateEnabledStates()
			if oldRegionCount !=  SMTDSettings.MultiRegionData.count do
				createUndoRecord ("Optimize "+ oldRegionCount as string+" Regions down to "+ SMTDSettings.MultiRegionData.count as string+" - Overlap Threshold:"+ theThreshold as string )
		)

		fn SubTilesToRegions =
		(
			local theSel = getListViewSelection()
			if theSel.count == 1 do
			(
				local theNewRegions = #()
				theX = SMTDSettings.MultiRegionData[theSel[1]][2]
				theY = SMTDSettings.MultiRegionData[theSel[1]][3]
				theWStep = SMTDSettings.MultiRegionData[theSel[1]][4] / SMTDSettings.MultiRegionData[theSel[1]][6]
				theHStep = SMTDSettings.MultiRegionData[theSel[1]][5] / SMTDSettings.MultiRegionData[theSel[1]][7]
				for y = 1 to SMTDSettings.MultiRegionData[theSel[1]][7] do
				(
					for x = 1 to SMTDSettings.MultiRegionData[theSel[1]][6]  do
					(
						append SMTDSettings.MultiRegionData #(SMTDSettings.MultiRegionData[theSel[1]][1], SMTDSettings.MultiRegionData[theSel[1]][2]+((x-1)*theWStep), SMTDSettings.MultiRegionData[theSel[1]][3]+((y-1)*theHStep), theWStep, theHStep, 1,1,"Tile Split "+ x as string +"x" + y as string+" of Region #"+theSel[1] as string )
						append theNewRegions (SMTDSettings.MultiRegionData.count-1)
					)
				)
				deleteItem SMTDSettings.MultiRegionData theSel[1]
				updateListView()
				setListViewSelection (lastSelectedLines= theNewRegions)
				createMRManipulator()
				createRegionGizmo false
				updateEnabledStates()
				redrawViews()
				createUndoRecord ("Split Region #"+theSel[1] as string+" Tiles To "+x as string +"x"+y as string + " Regions")
			)
		)

		on btn_splitToTiles pressed do SubTilesToRegions()


		fn createToCameraMenu theCamera =
		(
			local txt  = stringStream ""
			format "rcMenu SetToCamera_Menu (\n" to:txt
			format "menuItem mnu_delete \"To Delete a Preset, hold SHIFT and select an entry from the list below.\" \n" to:txt
			format "separator sep_10\n" to:txt
			local theRecord = #()
			local cnt = 0
			while theRecord != undefined do
			(
				cnt +=1
				theRecord = try(execute (getAppData theCamera (20130626+cnt)))catch(undefined)
				if theRecord != undefined then
				(
					local theComment = theRecord[6]
					if theComment == undefined do theComment = "No User Notes"
					format "menuItem mnu_slot% \"[% Regions] - '%' - Saved by %@% on % in '%'\" \n" cnt theRecord[1].count theComment theRecord[2] theRecord[3] theRecord[4] (if theRecord[5] == undefined or theRecord[4] == "" then "Untitled" else theRecord[5]) to:txt
					format "on mnu_slot% picked do if keyboard.shiftpressed then SMTD_MultiRegionRendering.removeCameraSlot % else SMTD_MultiRegionRendering.setToCamera TheSlot:% Override:true\n" cnt cnt cnt to:txt
				)
				else
				(
					format "separator sep_20\n" to:txt
					format "menuItem mnu_slot% \"Save New Preset...\" \n" cnt cnt to:txt
					format "on mnu_slot% picked do SMTD_MultiRegionRendering.setToCamera TheSlot:% \n" cnt cnt to:txt
				)
			)
			format ")\n" to:txt
			execute (txt as string)
		)

		fn removeCameraSlot theSlot =
		(
			local theCamera = viewport.getCamera()
			if isValidNode theCamera do
			(
				local q =querybox ("Are you sure you want to PERMANENTLY DELETE Preset Slot "+ theSlot as string+ " from "+ theCamera.name) title:"Delete Preset Slot?"
				if q do
				(
					local theRecord = #()
					local cnt = 0
					local lastRecord = 0
					while theRecord != undefined do
					(
						cnt +=1
						theRecord = try(execute (getAppData theCamera (20130626+cnt)))catch(undefined)
						if theRecord != undefined then
						(
							lastRecord = cnt
						)
					)
					for i = theSlot+1 to lastRecord do
					(
						setAppData theCamera (20130626+i-1) (getAppData theCamera (20130626+i))
					)
					setAppData theCamera (20130626+lastRecord) "undefined"
				)
			)
		)

		fn setToCamera theSlot:1 Override:false=
		(
			local theCamera = viewport.getCamera()
			if isValidNode theCamera do
			(
				local q = if Override then
					queryBox ("Are you sure you want to OVERWRITE the existing Slot "+theSlot as string+"?" ) title:"Overwrite Preset Slot?"
				else
					true
				if q do with PrintAllElements on setAppData theCamera (20130626+TheSlot) (#(SMTDSettings.MultiRegionData, sysinfo.username, sysinfo.computername, localtime, maxFileName, edt_presetDescription.text ) as string)
			)
		)

		on btn_saveInCamera pressed do
		(
			local theCamera = viewport.getCamera()
			if isValidNode theCamera then
			(
				SetToCamera_Menu = createToCameraMenu theCamera
				popUpMenu SetToCamera_Menu pos:mouse.screenpos
			)
			else
				messagebox "Active View is NOT a Camera!\n\nPlease select a Camera View, or set the current View to a Camera and try again!" title:"Not A Camera!"
		)

		fn getFromCamera TheSlot:1 =
		(
			local theCamera = viewport.getCamera()
			if isValidNode theCamera do
			(
				local theArray = try(execute (getAppData theCamera (20130626+TheSlot)))catch(undefined)
				if theArray != undefined do
					SMTDSettings.MultiRegionData = deepCopy theArray[1]
				edt_presetDescription.text = if theArray[6] != undefined then theArray[6] else ""
				updateListView()
				if SMTDSettings.MultiRegionData.count > 0 do setListViewSelection (lastSelectedLines= #(1) )
				createMRManipulator()
				createRegionGizmo true
				updateEnabledStates()
				updateSpinners()
				redrawViews()
				createUndoRecord ("Load Camera Preset From Slot "+TheSlot as string)
			)
		)

		fn createFromCameraMenu theCamera =
		(
			local txt  = stringStream ""
			format "rcMenu GetFromCamera_Menu (\n" to:txt
			local cnt = 0
			local theRecord = ""
			while theRecord != undefined do
			(
				cnt+=1
				theRecord = try(execute (getAppData theCamera (20130626+cnt)))catch(undefined)
				if theRecord != undefined do
				(
					local theComment = theRecord[6]
					if theComment == undefined do theComment = "No User Notes"
					format "menuItem mnu_slot% \"[% Regions] - '%' - Saved by %@% on % in '%'\" \n" cnt theRecord[1].count theComment theRecord[2] theRecord[3] theRecord[4] (if theRecord[5] == undefined or theRecord[4] == "" then "Untitled" else theRecord[5]) to:txt
					format "on mnu_slot% picked do SMTD_MultiRegionRendering.getFromCamera TheSlot:% \n" cnt cnt to:txt
				)
			)
			format ")\n" to:txt
			execute (txt as string)
		)

		on btn_getFromCamera pressed do
		(
			local theCamera = viewport.getCamera()
			if isValidNode theCamera then
			(
				GetFromCamera_Menu = createFromCameraMenu theCamera
				popUpMenu GetFromCamera_Menu pos:mouse.screenpos
			)
			else
				messagebox "Active View is NOT a Camera!\n\nPlease select a Camera View, or set the current View to a Camera and try again!" title:"Not A Camera!"
		)

		on lv_regions MouseClick args do
		(
			if args.Button == args.Button.Left do
			(
				updateSpinners()
				lastSelectedLines = getListViewSelection()
				createRegionGizmo (lastSelectedLines.count == 1)
				updateToRegionGizmo()
				updateEnabledStates()
			)
		)

		on lv_regions ItemChecked args do
		(
			if not isUpdatingList do
			(
				SMTDSettings.MultiRegionData[args.Item.Index+1][1] = args.Item.Checked
				try( theMRManipulator.updateGizmos 0 "" )catch()
				max views redraw
				redrawViews()
			)
			updateTotalCount()
		)

		local selNums = #()
		local checkStates = #()

		on lv_regions MouseUp args do
		(
			try(for x = 1 to selNums.count do lv_regions.items.item[selNums[x]].checked=checkStates[x])catch() -- correct the checkboxes
			selNums=#(); checkStates=#() -- clear the record
		)

		on lv_regions ItemSelectionChanged args do
		(
			-- record the states of the checkboxes so we can correct them at MouseUp
			selNums=for x=0 to lv_regions.selectedIndices.count-1 collect lv_regions.selectedIndices.item[x]
			checkStates=for x=1 to selNums.count collect lv_regions.items.item[selNums[x]].checked
		)

		/*
		on chk_MultiRegionRendering changed state do
		(
			local hasEnabledRegions = (for i in SMTDSettings.MultiRegionData where i[1] == True collect i).count > 0
			SMTDSettings.MultiRegionRendering = state
			if state and not hasEnabledRegions do
			(
				chk_MultiRegionRendering.state = SMTDSettings.MultiRegionRendering = false
				SMTD_MainRollout.Ui_report ("--Cannot Enable Multi-Region Rendering - No Active Regions Defined!")
			)

			if SMTDSettings.TilesRendering and SMTDSettings.MultiRegionRendering do
			(
				SMTD_TilesRendering.chk_tilesRendering.checked = SMTDSettings.TilesRendering = false
			)
			SMTD_MainRollout.Ui_report ("+Multi-Region Rendering set to [" + SMTDSettings.MultiRegionRendering as string + "] for this session.")

			SMTD_TileOptions.updateControls()
		)
		*/

		on btn_pickUserDefinedImage pressed do
		(
			local theFile = getOpenFilename caption:("Select Custom Background Image"+(if SMTDSettings.MultiRegionBackground == #single then "" else " Sequence")) historyCategory:"RegionBackground" types:"All Image Files Formats Supported by DRAFT|*.exr;*.bmp;*.dds;*.jpg;*.jpe;*.jpeg;*.png;*.tga;*.tif;*.tiff;*.sgi;*.rgb;*.rgba|OpenEXR Image File (*.EXR)|*.exr|BMP Image File (*.BMP)|*.bmp|DDS (*.DDS)|*.dds|JPEG Image File (*.JPG, *.JPE, *.JPEG)|*.jpg;*.jpe;*.jpeg|Portable Network Graphics Image File (*.PNG)|*.png|Targa (*.TGA)|*.tga|Tagged Image File Format (*.TIF, *.TIFF)|*.tif;*.tiff|SGI Image File (*.RGB, *.RGBA, *.SGI)|*.rgb;*.rgba;*.sgi"
			if theFile != undefined do
				edt_userDefinedImage.text = SMTDSettings.MultiRegionBackgroundImage = theFile
		)


		fn timeCallbackFunction =
		(
			updateListViewOnTimeChange()
			updateToRegionGizmo()
		)

		fn unregisterCallbacks =
		(
			unregisterTimeCallback timeCallbackFunction
		)

		fn registerCallbacks =
		(
			unregisterCallbacks()
			registerTimeCallback timeCallbackFunction
		)

		on SMTD_MultiRegionRendering rolledUp val do
		(
			if val then
			(
				createMRManipulator()
			)
			else
			(
				removeMRManipulator()
			)
		)

		on SMTD_MultiRegionRendering open do
		(
			--img_animKeys.bitmap = bitmap 10 10 color:(color 200 100 100)
			SMTDSettings.MultiRegionData = deepCopy ::SMTD_MultiRegionSettingsPersistentGlobal
			--chk_MultiRegionRendering.checked = SMTDSettings.MultiRegionRendering
			local theIndex = findItem #(#off, #previous, #single, #sequence) SMTDSettings.MultiRegionBackground
			if theIndex == 0 do theIndex = 1
			ddl_BackgroundMode.selection = theIndex
			edt_userDefinedImage.text = SMTDSettings.MultiRegionBackgroundImage

			initListView()
			updateListView()
			updateSpinners()
			--createMRManipulator()
			callbacks.removeScripts id:#DLMultiRegionManipulator
			callbacks.addScript #filePreSave "SMTD_MultiRegionRendering.removeMRManipulator()" id:#DLMultiRegionManipulator
			callbacks.addScript #filePostSave "SMTD_MultiRegionRendering.createMRManipulator()" id:#DLMultiRegionManipulator
			callbacks.addScript #selectionSetChanged "SMTD_MultiRegionRendering.sceneSelectionChangedCallback()" id:#DLMultiRegionManipulator
			registerCallbacks()
			updateFitPadding()
			SMTD_TileOptions.updateRolloutRollupStates()
		)
		on SMTD_MultiRegionRendering close do
		(
			::SMTD_MultiRegionSettingsPersistentGlobal = deepCopy SMTDSettings.MultiRegionData
			callbacks.removeScripts id:#DLMultiRegionManipulator
			removeMRManipulator()
			unregisterCallbacks()
		)
	)--end multi-region rollout

	rollout SMTD_RegionRendering "3ds Max Region Rendering" rolledup:true
	(
		group "Region Rendering"
		(
			--checkbox chk_regionRendering "Enable Region Rendering*" across:3
			label lbl_regionRendering "Region Rendering Mode:" across:3
			dropdownlist ddl_regionType items:#("Region", "Crop", "Blowup") offset:[10,-2] width:140
			checkbox chk_useMaxRegion "Use 3ds Max Region" align:#right

			spinner spn_regionLeft "Corner X:" range:[-99999,99999,0] type:#integer fieldwidth:50 across:4
			spinner spn_regionTop "Corner Y:" range:[-99999,99999,0] type:#integer fieldwidth:50
			spinner spn_regionWidth "Width:" range:[1,99999,100] type:#integer fieldwidth:50
			spinner spn_regionHeight "Height:" range:[0,99999,100] type:#integer fieldwidth:50

			checkbox chk_showRegionGizmo "Show Region Gizmo*" across:2 offset:[0,3]
			button chk_updateValues "Update Region Values" width:200 align:#right
		)

		fn getRegionFromActiveViewport =
		(
			if viewport.activeViewport > 0 then
			(

				local theRect

				if SMTDSettings.RegionType == 3 then
					theRect = viewport.getBlowupRect (viewport.activeViewport)
				else
					theRect = viewport.getRegionRect (viewport.activeViewport)
				spn_regionLeft.value = SMTDSettings.RegionLeft = theRect.x
				spn_regionTop.value =SMTDSettings.RegionTop = theRect.y
				spn_regionWidth.value = theRect.w
				spn_regionHeight.value = theRect.h
				SMTDSettings.RegionRight = theRect.x+theRect.w
				SMTDSettings.RegionBottom = theRect.y+theRect.h
			)
			else
			(
				spn_regionLeft.value = SMTDSettings.RegionLeft = 0
				spn_regionTop.value = SMTDSettings.RegionTop = 0
				spn_regionWidth.value = SMTDSettings.RegionRight = RenderWidth
				spn_regionHeight.value = SMTDSettings.RegionBottom = RenderHeight
			)
		)

		fn setRegionToActiveViewport =
		(
			if viewport.activeViewport > 0 do
			(
				if SMTDSettings.RegionType == 3 then
					viewport.setBlowupRect (viewport.activeViewport) (Box2 spn_regionLeft.value spn_regionTop.value spn_regionWidth.value spn_regionHeight.value)
				else
					viewport.setRegionRect (viewport.activeViewport) (Box2 spn_regionLeft.value spn_regionTop.value spn_regionWidth.value spn_regionHeight.value)

			)
		)

		fn updateRegionGizmo =
		(
			local theRegionGizmo = getNodeByName "SMTDMaxRegionGizmo"
			if isValidNode theRegionGizmo do
			(
				theRegionGizmo.cornerX = spn_regionLeft.value / RenderWidth as float
				theRegionGizmo.cornerY = spn_regionTop.value / RenderHeight as float
				theRegionGizmo.cornerX2 = (spn_regionLeft.value + spn_regionWidth.value) / RenderWidth as float
				theRegionGizmo.cornerY2 = (spn_regionTop.value + spn_regionHeight.value) / RenderHeight as float
			)
		)

		fn updateFromRegionGizmo =
		(
			local theRegionGizmo = getNodeByName "SMTDMaxRegionGizmo"
			if isValidNode theRegionGizmo do
			(
				SMTD_RegionRendering.spn_regionLeft.value = floor (theRegionGizmo.cornerX*RenderWidth)
				SMTD_RegionRendering.spn_regionTop.value = floor (theRegionGizmo.cornerY*RenderHeight)
				SMTD_RegionRendering.spn_regionWidth.value = floor ((theRegionGizmo.cornerX2-theRegionGizmo.cornerX)*RenderWidth)
				SMTD_RegionRendering.spn_regionHeight.value = floor ((theRegionGizmo.cornerY2-theRegionGizmo.cornerY)*RenderHeight)
				SMTDSettings.RegionLeft = spn_regionLeft.value
				SMTDSettings.RegionTop = spn_regionTop.value
				SMTDSettings.RegionRight = (spn_regionWidth.value+SMTDSettings.RegionLeft)
				SMTDSettings.RegionBottom= (spn_regionHeight.value+SMTDSettings.RegionTop)
				setRegionToActiveViewport()
			)
		)

		fn createRegionGizmo state =
		(
			--manipulateMode = state
			if state then
			(
				-- enforce safe frames when displaying the gizmo
				displaySafeFrames = true

				renderSceneDialog.Commit()
				local theRegionGizmo = getNodeByName "SMTDMaxRegionGizmo"
				if not isValidNode theRegionGizmo and DLMaxRegionManipulator != undefined do
				(
					theRegionGizmo = DLMaxRegionManipulator name:"SMTDMaxRegionGizmo"
					theRegionGizmo.transform.controller = transform_script()
					theRegionGizmo.isSelected = true
					redrawViews()
					theRegionGizmo.isSelected = false
					theInterface = LayerManager.getLayerFromName "SMTD_Gizmos"
					if theInterface == undefined do
						theInterface = LayerManager.newLayerFromName "SMTD_Gizmos"
					theInterface.addnode theRegionGizmo
					theInterface.ishidden = theInterface.isFrozen = false
				)
				updateRegionGizmo()
			)
			else
			(
				local theRegionGizmo = getNodeByName "SMTDMaxRegionGizmo"
				if isValidNode theRegionGizmo do delete theRegionGizmo
				try(LayerManager.deleteLayerByName "SMTD_Gizmos")catch()
			)
		)

		on chk_showRegionGizmo changed state do createRegionGizmo state
		/*
		on chk_regionRendering changed state do
		(
			if state then
				SMTDSettings.TilesRendering = SMTD_TilesRendering.chk_tilesRendering.state = false

			SMTDSettings.RegionRendering = state
			SMTD_MainRollout.Ui_report ("+Region Rendering: Enable Region Rendering set to [" + state as string + "] for this session. Not Sticky.")
		)
		*/
		on ddl_regionType selected itm do
		(
			SMTDSettings.RegionType = itm
			setIniSetting SMTDPaths.InIFile "TilesRendering" "RegionType" (SMTDSettings.RegionType as string)
			SMTD_MainRollout.Ui_report ("+Region Rendering: Region Type set to [" + ddl_regionType.selected + "].")
			getRegionFromActiveViewport()
			local leftValue = spn_regionLeft.value
			local topValue = spn_regionTop.value
			if ddl_regionType.selected == "Blowup" then
			(
				spn_regionLeft.range = [-99999,99999,0]
				if leftValue < -99999 do leftValue = -99999
				if leftValue > 99999 do leftValue = 99999

				spn_regionTop.range = [-99999,99999,0]
				if topValue < -99999 do topValue = -99999
				if topValue > 99999 do topValue = 99999
				spn_regionWidth.enabled = false
			)
			else
			(
				spn_regionLeft.range = [0,99999,0]
				if leftValue < 0 do leftValue = 0
				if leftValue > 99999 do leftValue = 99999

				spn_regionTop.range = [0,99999,0]
				if topValue < 0 do topValue = 0
				if topValue > 99999 do topValue = 99999
				spn_regionWidth.enabled = true
			)
			spn_regionLeft.value = leftValue
			spn_regionTop.value = topValue

			--I am not sure if we want this when swapping between modes since it will mess up what you have saved in each mode since
			--setRegionToActiveViewport()
			updateRegionGizmo()
			SMTD_TileOptions.updateRolloutRollupStates()
		)

		on spn_regionLeft changed val do
		(
			if ddl_regionType.selected != "Blowup" then
			(
				if spn_regionLeft.value+spn_regionWidth.value > renderWidth do spn_regionLeft.value = renderWidth - spn_regionWidth.value
			)
			SMTDSettings.RegionLeft = spn_regionLeft.value
			setRegionToActiveViewport()
			local theRect
			if SMTDSettings.RegionType == 3 then
				theRect = viewport.getBlowupRect (viewport.activeViewport)
			else
				theRect = viewport.getRegionRect (viewport.activeViewport)
			spn_regionWidth.value = theRect.w
			SMTDSettings.RegionRight = theRect.x+theRect.w
			updateRegionGizmo()
		)
		on spn_regionTop changed val do
		(
			if ddl_regionType.selected != "Blowup" then
			(
				if spn_regionTop.value+spn_regionHeight.value > renderHeight do spn_regionTop.value = renderHeight - spn_regionHeight.value
			)
			SMTDSettings.RegionTop = spn_regionTop.value
			setRegionToActiveViewport()
			local theRect
			if SMTDSettings.RegionType == 3 then
				theRect = viewport.getBlowupRect (viewport.activeViewport)
			else
				theRect = viewport.getRegionRect (viewport.activeViewport)
			spn_regionWidth.value = theRect.w
			SMTDSettings.RegionRight = theRect.x+theRect.w
			updateRegionGizmo()
		)
		on spn_regionWidth changed val do
		(
			if ddl_regionType.selected != "Blowup" then
			(
				if spn_regionLeft.value+spn_regionWidth.value > renderWidth do spn_regionWidth.value = renderWidth - spn_regionLeft.value
			)
			SMTDSettings.RegionRight = (spn_regionWidth.value+SMTDSettings.RegionLeft)
			setRegionToActiveViewport()
			updateRegionGizmo()
		)
		on spn_regionHeight changed val do
		(
			if ddl_regionType.selected != "Blowup" then
			(
				if spn_regionTop.value+spn_regionHeight.value > renderHeight do spn_regionHeight.value = renderHeight - spn_regionTop.value
			)
			SMTDSettings.RegionBottom= (spn_regionHeight.value+SMTDSettings.RegionTop)
			setRegionToActiveViewport()
			local theRect
			if SMTDSettings.RegionType == 3 then
				theRect = viewport.getBlowupRect (viewport.activeViewport)
			else
				theRect = viewport.getRegionRect (viewport.activeViewport)

			spn_regionWidth.value = theRect.w
			SMTDSettings.RegionRight = theRect.x+theRect.w
			updateRegionGizmo()
		)

		on chk_updateValues pressed do
		(
			getRegionFromActiveViewport()
			updateRegionGizmo()
		)

		on chk_useMaxRegion changed state do
		(
			chk_updateValues.enabled = spn_regionLeft.enabled = spn_regionTop.enabled = spn_regionWidth.enabled = spn_regionHeight.enabled = chk_showRegionGizmo.enabled = (not state)
			if not state do
			(
				chk_showRegionGizmo.state = false
			)

			SMTDSettings.RegionUseMaxValues = state
			setIniSetting SMTDPaths.InIFile "TilesRendering" "RegionUseMaxValues" (state as string)
			SMTD_MainRollout.Ui_report ("+Region Rendering: Use 3ds Max Region set to [" + state as string + "].")
		)

		on SMTD_RegionRendering open do
		(
			if ShowRolloutOpenMsgInLog do SMTD_MainRollout.Ui_report ">Opening Region Rendering Rollout"
			--chk_RegionRendering.state = SMTDSettings.RegionRendering
			ddl_regionType.selection = SMTDSettings.RegionType

			chk_useMaxRegion.state = SMTDSettings.RegionUseMaxValues
			chk_updateValues.enabled = spn_regionLeft.enabled = spn_regionTop.enabled = spn_regionWidth.enabled = spn_regionHeight.enabled = chk_showRegionGizmo.enabled = (not chk_useMaxRegion.state)

			getRegionFromActiveViewport()

			createRegionGizmo chk_showRegionGizmo.state

			local leftValue = spn_regionLeft.value
			local topValue = spn_regionTop.value
			if ddl_regionType.selected == "Blowup" then
			(
				spn_regionLeft.range = [-99999,99999,0]
				if leftValue < -99999 do leftValue = -99999
				if leftValue > 99999 do leftValue = 99999

				spn_regionTop.range = [-99999,99999,0]
				if topValue < -99999 do topValue = -99999
				if topValue > 99999 do topValue = 99999
				spn_regionWidth.enabled = false
			)
			else
			(
				spn_regionLeft.range = [0,99999,0]
				if leftValue < 0 do leftValue = 0
				if leftValue > 99999 do leftValue = 99999

				spn_regionTop.range = [0,99999,0]
				if topValue < 0 do topValue = 0
				if topValue > 99999 do topValue = 99999
				spn_regionWidth.enabled = true
			)
			spn_regionLeft.value = leftValue
			spn_regionTop.value = topValue

			chk_useMaxRegion.caption = SMTDFunctions.getStickyCaption "TilesRendering" "RegionUseMaxValues" "Use 3ds Max Region  "

			callbacks.removeScripts id:#SMTD_PreRegionGizmoCallback
			callbacks.removeScripts id:#SMTD_PostRegionGizmoCallback
			callbacks.addScript #filePreSave "if SMTD_RegionRendering.chk_showRegionGizmo.state do SMTD_RegionRendering.createRegionGizmo false" id:#SMTD_PreRegionGizmoCallback
			callbacks.addScript #filePostSave "if SMTD_RegionRendering.chk_showRegionGizmo.state do SMTD_RegionRendering.createRegionGizmo true" id:#SMTD_PostRegionGizmoCallback
			SMTD_TileOptions.updateRolloutRollupStates()
		)

		on SMTD_RegionRendering close do
		(
			callbacks.removeScripts id:#SMTD_PreRegionGizmoCallback
			callbacks.removeScripts id:#SMTD_PostRegionGizmoCallback
			createRegionGizmo false
		)
	)--end 3ds max region rendering rollout

	rollout SMTD_BakeToTexture "Render to Texture"
	(
		group "Render to Texture options"
		(
			checkbox chk_isBakeJob "Submit as Render to Texture Job" across:2
			checkbox chk_BakeJobOneObjectPerTask "One Object Per Task"

			multiListBox lbx1 "Bake these objects:" align:#left  width:390 height:5 across:2
			button btn_add "Add"  width:61 height:18 align:#right tooltip:"Add the selected object in the scene to the list of objects to bake." offset:[1,20]
			button btn_Remove "Remove" width:61 height:18 align:#right offset:[0,-50] tooltip:"Remove the select object in the list from the list."
			button btn_clearAll "Clear All" width:61 height:18 align:#right tooltip:"Clears all objects from the list."
		)

		fn refreshBakeUI =
		(
			if SMTDSettings.isBakeJob then
			(
				SMTD_objsToBake = for o in SMTD_objsToBake where (isvalidobj o) collect o
				lbx1.items = for i in SMTD_objsToBake collect i.name
			)
			btn_add.enabled = chk_BakeJobOneObjectPerTask.enabled = btn_Remove.enabled = btn_clearAll.enabled = lbx1.enabled = SMTDSettings.isBakeJob
		)

		fn getFilePath =
		(
			path = edt_filePath.text
			if path == "" then
			(
				path = getdir #image		-- image directory is the default
			)
			if path[ path.count ] != "\\" then
				path += "\\"

			-- format "        file path: % \n" path
			path
		)

		on edt_filePath entered txt do
		(
			SMTD_bakeOutputPath = txt
		)

		on btn_pathSelect pressed do
		(
			path = GetSavePath caption:"Select Output Path" initialDir:(getFilePath())
			if path != undefined then
			(
				edt_filePath.text = path
			)
		)

		on btn_add pressed do
		(
			join SMTD_objsToBake (for i in selection where (finditem SMTD_objsToBake i==0) collect i)
			refreshBakeUI()
		)

		on btn_Remove pressed do
		(
			if lbx1.items.count > 0 then
				(
					SMTD_objsToBake = for i in (#{1..lbx1.items.count} - lbx1.selection) collect (getnodebyname lbx1.items[i])
					refreshBakeUI()
				)
		)

		on btn_clearAll pressed do
		(
			SMTD_objsToBake = #()
			refreshBakeUI()
		)

		on chk_isBakeJob changed state do
		(
			setIniSetting SMTDPaths.InIFile "RTT"  "IsBakeJob" ( (SMTDSettings.IsBakeJob = state ) as string)
			SMTD_MainRollout.Ui_report ("+Submit as Render to Texture Job set to [" + state as string + "].")
			refreshBakeUI()
		)

		on chk_BakeJobOneObjectPerTask changed state do
		(
			setIniSetting SMTDPaths.InIFile "RTT"  "IsBakeJob" ( (SMTDSettings.BakeJobOneObjectPerTask = state ) as string)
			SMTD_MainRollout.Ui_report ("+Render to Texture Job One Object Per Task set to [" + state as string + "].")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Render To Texture"
			if not state do
			(
				theTitle += (if SMTDSettings.IsBakeJob == true then " [On]" else " [Off]")
			)
			SMTD_BakeToTexture.title = theTitle
		)

		on SMTD_BakeToTexture rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_BakeToTexture open do
		(
			chk_isBakeJob.state = SMTDSettings.IsBakeJob
			chk_BakeJobOneObjectPerTask.state = SMTDSettings.BakeJobOneObjectPerTask
			if SMTD_objsToBake == undefined then SMTD_objsToBake = #()

			refreshBakeUI()
			SMTD_BakeToTexture.open =  SMTDSettings.IsBakeJob
			updateRolloutTitle SMTD_BakeToTexture.open
		)
	)--end bake to texture rollout

	local controlHeight = 210 --amin #(210, 100 + StateSetsChildren.count*18)

	rollout SMTD_StateSets "State Sets"
	(
		local theRoot

		checkbox chk_submitCheckedStateSets "Submit Checked State Sets  " offset:[-3,-3] across:2
		checkbox chk_StateSetRenameOutput "Add State Set Name to Output Filename  " offset:[3,-3]

		dotNetControl dn_tv "TreeView" width:480 height:controlHeight align:#center offset:[0,-3]

		button btn_CheckAll "Check ALL" across:4 width:100 height:20 align:#left offset:[-7,0]
		button btn_CheckInvert "INVERT" width:100 height:20 align:#left offset:[-20,0]
		button btn_CheckNone "Check NONE" width:100 height:20 align:#left offset:[-34,0]
		button btn_updateSSlist "UPDATE LIST" align:#right offset:[7,0] 	width:100

		local isUpdating = false
		fn initTreeView tv =
		(
			isUpdating = true
			tv.nodes.Clear()
			tv.checkboxes = true
			tv.HideSelection = false
			tv.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			tv.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r SMTD_ColorPalette.maxBgColor.g SMTD_ColorPalette.maxBgColor.b
			theRoot = tv.nodes.add "State Sets"
			theRoot.text = "State Sets"
			theRoot.forecolor = SMTD_ColorPalette.blueColor
			theRoot.checked = true
			isUpdating = false
		)

		on dn_tv AfterCheck arg do
		(
			if not isUpdating do
			(
				if arg.Node.parent == undefined then
				(
					for i = 1 to SMTD_StateSetsTree.count do
					(
						if keyboard.controlPressed then
							SMTD_StateSetsTree[i][2] = SMTD_StateSetsTree[i][5].checked = not SMTD_StateSetsTree[i][5].checked
						else
							SMTD_StateSetsTree[i][2] = SMTD_StateSetsTree[i][5].checked = arg.Node.checked

							if SMTD_StateSetsTree[i][2] then
								appendIfUnique SMTDSettings.StateSetsNamesList SMTD_StateSetsTree[i][3]
							else
							(
								local theIndex = findItem SMTDSettings.StateSetsNamesList SMTD_StateSetsTree[i][3]
								if theIndex > 0 do deleteItem SMTDSettings.StateSetsNamesList theIndex
							)
					)
				)
				else
				(
					--try
					(
						if arg.Node.tag != undefined do
						(
							SMTD_StateSetsTree[arg.Node.tag][2] = arg.Node.checked
							if arg.Node.checked then
								appendIfUnique SMTDSettings.StateSetsNamesList SMTD_StateSetsTree[arg.Node.tag][3]
							else
							(
								local theIndex = findItem SMTDSettings.StateSetsNamesList SMTD_StateSetsTree[arg.Node.tag][3]
								if theIndex > 0 do deleteItem SMTDSettings.StateSetsNamesList theIndex
							)
						)
					)
					--catch()
				)
			)
		)

		fn updateStateSetsList =
		(
			isUpdating = true
			initTreeView dn_tv
			::SMTD_StateSetsTree = #()
			local ssP = try(dotNetObject "Autodesk.Max.StateSets.Plugin")catch(undefined)
			if ssP != undefined do
			(
				if ssP.Instance.EntityManager.RootEntity.Children.Count > 0 then
				(
					SMTDFunctions.getStateSetChildrenRecursive ssP.Instance.EntityManager.RootEntity.MasterStateSet theRoot #()
					theRoot.expand()
					for i = 1 to SMTD_StateSetsTree.count do SMTD_StateSetsTree[i][2] = SMTD_StateSetsTree[i][5].checked = findItem SMTDSettings.StateSetsNamesList SMTD_StateSetsTree[i][3] > 0
				)
				else
					theRoot.text = "No State Sets"
			)
			if SMTD_StateSetsTree.count == 0 then
				chk_submitCheckedStateSets.enabled = chk_submitCheckedStateSets.state = false
			else
			(
				chk_submitCheckedStateSets.enabled = true
				chk_submitCheckedStateSets.state = SMTDSettings.StateSetsSubmit
			)
			isUpdating = false
		)

		on btn_CheckAll pressed do
		(
			SMTDSettings.StateSetsNamesList = #()
			for i = 1 to SMTD_StateSetsTree.count do
			(
				SMTD_StateSetsTree[i][2] = SMTD_StateSetsTree[i][5].checked = true
				append SMTDSettings.StateSetsNamesList SMTD_StateSetsTree[i][3]
			)
		)

		on btn_CheckInvert pressed do
		(
			SMTDSettings.StateSetsNamesList = #()
			for i = 1 to SMTD_StateSetsTree.count do
			(
				SMTD_StateSetsTree[i][2] = SMTD_StateSetsTree[i][5].checked = not SMTD_StateSetsTree[i][5].checked
				if SMTD_StateSetsTree[i][2] do append SMTDSettings.StateSetsNamesList SMTD_StateSetsTree[i][3]
			)
		)
		on btn_CheckNone pressed do
		(
			SMTDSettings.StateSetsNamesList = #()
			for i = 1 to SMTD_StateSetsTree.count do
			(
				SMTD_StateSetsTree[i][2] = SMTD_StateSetsTree[i][5].checked = false
			)
		)

		on btn_updateSSlist pressed do updateStateSetsList()

		on chk_submitCheckedStateSets changed state do
		(
			SMTDSettings.StateSetsSubmit = state
			setIniSetting SMTDPaths.InIFile "StateSets" "StateSetsSubmit" ( (SMTDSettings.StateSetsSubmit = state) as string)
			SMTD_MainRollout.Ui_report ("+State Sets: Submit Checked State Sets to [" + state as string + "].")
		)

		on chk_StateSetRenameOutput changed state do
		(
			SMTDSettings.StateSetRenameOutput = state
			setIniSetting SMTDPaths.InIFile "StateSets" "StateSetRenameOutput" (state as string)
			SMTD_MainRollout.Ui_report ("+State Sets: Add State Set Name to Output set to [" + state as string + "].")
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "State Sets"
			if not state do
			(
				local count = SMTDSettings.StateSetsNamesList.count
				theTitle += (if chk_submitCheckedStateSets.state then " [On, "+count as string+" State Set"+(if count == 1 then "" else "s")+" Checked]" else " [Off]")
				if chk_submitCheckedStateSets.state and SMTDSettings.StateSetRenameOutput do theTitle += " [Rename Output]"
			)
			SMTD_StateSets.title = theTitle
		)

		on SMTD_StateSets rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_StateSets open do
		(
			chk_StateSetRenameOutput.checked = SMTDSettings.StateSetRenameOutput
			updateStateSetsList()
			chk_submitCheckedStateSets.caption = SMTDFunctions.getStickyCaption "StateSets" "StateSetsSubmit"  "Submit Checked State Sets  "
			chk_StateSetRenameOutput.caption = SMTDFunctions.getStickyCaption "StateSets" "StateSetRenameOutput"  "Add State Set Name to Output Filename  "
			updateRolloutTitle SMTD_StateSets.open
		)
	)

	rollout SMTD_ExtraInfo "Extra Info"
	(
		button btn_extraInfo0 "Extra Info 0: *" align:#left offset:[-10,-5] border:false width:80 across:2
		edittext edt_extraInfo0 "" fieldwidth:400 align:#right offset:[10,-3]

		button btn_extraInfo1 "Extra Info 1: *" align:#left offset:[-10,-5] border:false width:80 across:2
		edittext edt_extraInfo1 "" fieldwidth:400 align:#right offset:[10,-3]

		button btn_extraInfo2 "Extra Info 2: *" align:#left offset:[-10,-5] border:false width:80 across:2
		edittext edt_extraInfo2 "" fieldwidth:400 align:#right offset:[10,-3]

		button btn_extraInfo3 "Extra Info 3: *" align:#left offset:[-10,-5] border:false width:80 across:2
		edittext edt_extraInfo3 "" fieldwidth:400 align:#right offset:[10,-3]

		button btn_extraInfo4 "Extra Info 4: *" align:#left offset:[-10,-5] border:false width:80 across:2
		edittext edt_extraInfo4 "" fieldwidth:400 align:#right offset:[10,-3]

		button btn_extraInfo5 "Extra Info 5: *" align:#left offset:[-10,-5] border:false width:80 across:2
		edittext edt_extraInfo5 "" fieldwidth:400 align:#right offset:[10,-3]

		button btn_extraInfo6 "Extra Info 6: *" align:#left offset:[-10,-5] border:false width:80 across:2
		edittext edt_extraInfo6 "" fieldwidth:400 align:#right offset:[10,-3]

		button btn_extraInfo7 "Extra Info 7: *" align:#left offset:[-10,-5] border:false width:80 across:2
		edittext edt_extraInfo7 "" fieldwidth:400 align:#right offset:[10,-3]

		button btn_extraInfo8 "Extra Info 8: *" align:#left offset:[-10,-5] border:false width:80 across:2
		edittext edt_extraInfo8 "" fieldwidth:400 align:#right offset:[10,-3]

		button btn_extraInfo9 "Extra Info 9: *" align:#left offset:[-10,-5] border:false width:80 across:2
		edittext edt_extraInfo9 "" fieldwidth:400 align:#right offset:[10,-3]

		on edt_extraInfo0 entered txt do
		(
			SMTDSettings.ExtraInfo0 = txt
			if SMTDFunctions.IsSettingSticky "ExtraInfo" "ExtraInfo0" then
			(
				setIniSetting SMTDPaths.InIFile "ExtraInfo"  "ExtraInfo0" txt
				SMTD_MainRollout.Ui_report ("+Extra Info 0 set to [" + txt + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+Extra Info 0 set to [" + txt + "] for the current session.")
			)
		)
		on edt_extraInfo1 entered txt do
		(
			SMTDSettings.ExtraInfo1 = txt
			if SMTDFunctions.IsSettingSticky "ExtraInfo" "ExtraInfo1" then
			(
				setIniSetting SMTDPaths.InIFile "ExtraInfo"  "ExtraInfo1" txt
				SMTD_MainRollout.Ui_report ("+Extra Info 1 set to [" + txt + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+Extra Info 1 set to [" + txt + "] for the current session.")
			)
		)
		on edt_extraInfo2 entered txt do
		(
			SMTDSettings.ExtraInfo2 = txt
			if SMTDFunctions.IsSettingSticky "ExtraInfo" "ExtraInfo2" then
			(
				setIniSetting SMTDPaths.InIFile "ExtraInfo"  "ExtraInfo2" txt
				SMTD_MainRollout.Ui_report ("+Extra Info 2 set to [" + txt + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+Extra Info 2 set to [" + txt + "] for the current session.")
			)
		)
		on edt_extraInfo3 entered txt do
		(
			SMTDSettings.ExtraInfo3 = txt
			if SMTDFunctions.IsSettingSticky "ExtraInfo" "ExtraInfo3" then
			(
				setIniSetting SMTDPaths.InIFile "ExtraInfo"  "ExtraInfo3" txt
				SMTD_MainRollout.Ui_report ("+Extra Info 3 set to [" + txt + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+Extra Info 3 set to [" + txt + "] for the current session.")
			)
		)
		on edt_extraInfo4 entered txt do
		(
			SMTDSettings.ExtraInfo4 = txt
			if SMTDFunctions.IsSettingSticky "ExtraInfo" "ExtraInfo4" then
			(
				setIniSetting SMTDPaths.InIFile "ExtraInfo"  "ExtraInfo4" txt
				SMTD_MainRollout.Ui_report ("+Extra Info 4 set to [" + txt + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+Extra Info 4 set to [" + txt + "] for the current session.")
			)
		)
		on edt_extraInfo5 entered txt do
		(
			SMTDSettings.ExtraInfo5 = txt
			if SMTDFunctions.IsSettingSticky "ExtraInfo" "ExtraInfo5" then
			(
				setIniSetting SMTDPaths.InIFile "ExtraInfo"  "ExtraInfo5" txt
				SMTD_MainRollout.Ui_report ("+Extra Info 5 set to [" + txt + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+Extra Info 5 set to [" + txt + "] for the current session.")
			)
		)
		on edt_extraInfo6 entered txt do
		(
			SMTDSettings.ExtraInfo6 = txt
			if SMTDFunctions.IsSettingSticky "ExtraInfo" "ExtraInfo6" then
			(
				setIniSetting SMTDPaths.InIFile "ExtraInfo"  "ExtraInfo6" txt
				SMTD_MainRollout.Ui_report ("+Extra Info 6 set to [" + txt + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+Extra Info 6 set to [" + txt + "] for the current session.")
			)
		)
		on edt_extraInfo7 entered txt do
		(
			SMTDSettings.ExtraInfo7 = txt
			if SMTDFunctions.IsSettingSticky "ExtraInfo" "ExtraInfo7" then
			(
				setIniSetting SMTDPaths.InIFile "ExtraInfo"  "ExtraInfo7" txt
				SMTD_MainRollout.Ui_report ("+Extra Info 7 set to [" + txt + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+Extra Info 7 set to [" + txt + "] for the current session.")
			)
		)
		on edt_extraInfo8 entered txt do
		(
			SMTDSettings.ExtraInfo8 = txt
			if SMTDFunctions.IsSettingSticky "ExtraInfo" "ExtraInfo8" then
			(
				setIniSetting SMTDPaths.InIFile "ExtraInfo"  "ExtraInfo8" txt
				SMTD_MainRollout.Ui_report ("+Extra Info 8 set to [" + txt + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+Extra Info 8 set to [" + txt + "] for the current session.")
			)
		)
		on edt_extraInfo9 entered txt do
		(
			SMTDSettings.ExtraInfo9 = txt
			if SMTDFunctions.IsSettingSticky "ExtraInfo" "ExtraInfo9" then
			(
				setIniSetting SMTDPaths.InIFile "ExtraInfo"  "ExtraInfo9" txt
				SMTD_MainRollout.Ui_report ("+Extra Info 9 set to [" + txt + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+Extra Info 9 set to [" + txt + "] for the current session.")
			)
		)

		fn updateUI =
		(
			btn_extraInfo0.caption = SMTDFunctions.getStickyCaption "ExtraInfo" "ExtraInfo0" "Extra Info 0: "
			btn_extraInfo1.caption = SMTDFunctions.getStickyCaption "ExtraInfo" "ExtraInfo1" "Extra Info 1: "
			btn_extraInfo2.caption = SMTDFunctions.getStickyCaption "ExtraInfo" "ExtraInfo2" "Extra Info 2: "
			btn_extraInfo3.caption = SMTDFunctions.getStickyCaption "ExtraInfo" "ExtraInfo3" "Extra Info 3: "
			btn_extraInfo4.caption = SMTDFunctions.getStickyCaption "ExtraInfo" "ExtraInfo4" "Extra Info 4: "
			btn_extraInfo5.caption = SMTDFunctions.getStickyCaption "ExtraInfo" "ExtraInfo5" "Extra Info 5: "
			btn_extraInfo6.caption = SMTDFunctions.getStickyCaption "ExtraInfo" "ExtraInfo6" "Extra Info 6: "
			btn_extraInfo7.caption = SMTDFunctions.getStickyCaption "ExtraInfo" "ExtraInfo7" "Extra Info 7: "
			btn_extraInfo8.caption = SMTDFunctions.getStickyCaption "ExtraInfo" "ExtraInfo8" "Extra Info 8: "
			btn_extraInfo9.caption = SMTDFunctions.getStickyCaption "ExtraInfo" "ExtraInfo9" "Extra Info 9: "

			edt_extraInfo0.enabled = edt_extraInfo1.enabled = edt_extraInfo2.enabled =edt_extraInfo3.enabled = edt_extraInfo4.enabled = edt_extraInfo5.enabled = true
			edt_extraInfo0.text = SMTDSettings.ExtraInfo0
			edt_extraInfo1.text = SMTDSettings.ExtraInfo1
			edt_extraInfo2.text = SMTDSettings.ExtraInfo2
			edt_extraInfo3.text = SMTDSettings.ExtraInfo3
			edt_extraInfo4.text = SMTDSettings.ExtraInfo4
			edt_extraInfo5.text = SMTDSettings.ExtraInfo5
			edt_extraInfo6.text = SMTDSettings.ExtraInfo6
			edt_extraInfo7.text = SMTDSettings.ExtraInfo7
			edt_extraInfo8.text = SMTDSettings.ExtraInfo8
			edt_extraInfo9.text = SMTDSettings.ExtraInfo9
		)

		fn getExtraInfoCount =
		(
			local count = 0
			if edt_extraInfo0.text != "" do count+=1
			if edt_extraInfo2.text != "" do count+=1
			if edt_extraInfo3.text != "" do count+=1
			if edt_extraInfo4.text != "" do count+=1
			if edt_extraInfo5.text != "" do count+=1
			if edt_extraInfo6.text != "" do count+=1
			if edt_extraInfo7.text != "" do count+=1
			if edt_extraInfo8.text != "" do count+=1
			if edt_extraInfo9.text != "" do count+=1
			count
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Extra Info "
			if not state do
			(
				local count = getExtraInfoCount()
				if count > 0 then
					theTitle += "["+ count as string +" Extra Field"+ (if count == 1 then "" else "s")+"]"
				else
					theTitle += "[None]"
			)
			SMTD_ExtraInfo.title = theTitle
		)

		on SMTD_ExtraInfo rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_ExtraInfo open do
		(
			updateUI()
			SMTD_ExtraInfo.open =  ((getExtraInfoCount()) > 0)
			updateRolloutTitle SMTD_ExtraInfo.open
		)
	)

	rollout SMTD_ExtraInfoKeyValues "Extra Info Keys"
	(
		dotNetControl lv_extraInfoKeys "System.Windows.Forms.ListView" width:480 height:120 align:#center
		button btn_remove "X" across:4 width:20 height:18 align:#left offset:[-12,0] enabled:false tooltip:"REMOVE the key and its value from the list."
		edittext edt_key fieldwidth:100 across:2 align:#left offset:[-108,0]
		edittext edt_value fieldwidth:328 align:#center offset:[-10,0]
		button btn_add "+" width:20 height:18 align:#right offset:[8,0] enabled:false

		fn initListView =
		(
			lv_extraInfoKeys.gridLines = true
			lv_extraInfoKeys.View = (dotNetClass "System.Windows.Forms.View").Details
			lv_extraInfoKeys.fullRowSelect = true

			lv_extraInfoKeys.checkboxes = false

			lv_extraInfoKeys.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			lv_extraInfoKeys.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r (amin (SMTD_ColorPalette.maxBgColor.g+5) 255) (amin (SMTD_ColorPalette.maxBgColor.b+15) 255)

			lv_extraInfoKeys.LabelEdit = false
			column1 = lv_extraInfoKeys.Columns.add "Extra Info KEY" 120
			column2 = lv_extraInfoKeys.Columns.add "Extra Info VALUE" 355
		)

		local isUpdatingList = false
		fn updateListView =
		(
			isUpdatingList = true
			local theRange = #()
			lv_extraInfoKeys.Items.clear()
			for i in SMTDSettings.ExtraInfoKeyValues do
			(
				li = dotNetObject "System.Windows.Forms.ListViewItem" i[1]
				subli = li.SubItems.add i[2]
				append theRange li
			)
			lv_extraInfoKeys.Items.AddRange theRange
			isUpdatingList = false
		)

		fn updateButtonStates =
		(
			local matchesExistingKey = (for i in SMTDSettings.ExtraInfoKeyValues where matchPattern i[1] pattern:edt_key.text collect i[1]).count > 0
			local matchesExistingValue = (for i in SMTDSettings.ExtraInfoKeyValues where (matchPattern i[1] pattern:edt_key.text AND matchPattern i[2] pattern:edt_value.text) collect i[1]).count > 0
			btn_add.enabled = edt_key.text.count != 0 and not matchesExistingValue
			btn_add.caption = if matchesExistingKey then "O" else "+"
			btn_add.tooltip = if matchesExistingKey then "OVERWRITE the existing Key's Value" else "ADD the New Key and its Value to the list."
			btn_remove.enabled = edt_key.text.count != 0 and matchesExistingKey
		)

		fn updateUI =
		(
			updateListView()
			updateButtonStates()
		)

		fn filterCharacters txt mode:#key=
		(
			local filterArray = #("=")
			if mode == #key do join filterArray #("%","<",">","^","&","|",":"," ","\"")
			for i in filterArray do txt = substituteString txt i "_"
			txt
		)

		fn getListViewSelection lv =
		(
			try(for i = 1 to lv.items.count where lv.items.item[i-1].Selected collect i)catch #()
		)

		fn setListViewSelection lv theSel =
		(
			for i = 1 to lv.items.count do lv.items.item[i-1].Selected = theSel[i]
		)

		on lv_extraInfoKeys ItemSelectionChanged EventArgs do
		(
			local theSel = getListViewSelection lv_extraInfoKeys
			for i in theSel do
			(
				edt_key.text = lv_extraInfoKeys.items.item[i-1].text
				edt_value.text = lv_extraInfoKeys.items.item[i-1].SubItems.item[1].text
			)
			updateButtonStates()
		)

		on btn_remove pressed do
		(
			SMTD_MainRollout.Ui_report ("+REMOVED Extra Info Key [" +edt_key.text + "="+ edt_value.text + "].")
			for i = SMTDSettings.ExtraInfoKeyValues.count to 1 by -1 where matchPattern SMTDSettings.ExtraInfoKeyValues[i][1] pattern:edt_key.text do deleteItem SMTDSettings.ExtraInfoKeyValues i
			--edt_key.text = edt_value.text = ""
			updateUI()
		)

		on edt_key changed txt do updateButtonStates()
		on edt_value changed txt do updateButtonStates()

		on btn_add pressed do
		(
			local theIndexArray = for i = 1 to SMTDSettings.ExtraInfoKeyValues.count where matchPattern SMTDSettings.ExtraInfoKeyValues[i][1] pattern:edt_key.text collect i
			if theIndexArray.count > 0 then
			(
				for i in theIndexArray do
				(
					SMTD_MainRollout.Ui_report ("+UPDATED Extra Info Key [" +edt_key.text + "=" + SMTDSettings.ExtraInfoKeyValues[i][2] +"] to ["+ edt_key.text + "=" + edt_value.text + "].")
					SMTDSettings.ExtraInfoKeyValues[i][2] = filterCharacters edt_value.text mode:#value
				)
			)
			else
			(
				append SMTDSettings.ExtraInfoKeyValues #(filterCharacters edt_key.text mode:#key, filterCharacters edt_value.text mode:#value)
				SMTD_MainRollout.Ui_report ("+ADDED Extra Info Key [" +edt_key.text + "="+ edt_value.text + "].")
			)
			edt_key.text = edt_value.text = ""
			updateUI()
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Extra Info Keys "
			if not state do
			(
				local count = SMTDSettings.ExtraInfoKeyValues.count
				if count > 0 then
					theTitle += "["+ count as string +" Extra Key"+ (if count == 1 then "" else "s")+"]"
				else
					theTitle += "[None]"
			)
			SMTD_ExtraInfoKeyValues.title = theTitle
		)

		on SMTD_ExtraInfoKeyValues rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_ExtraInfoKeyValues open do
		(
			initListView()
			updateUI()
			SMTD_ExtraInfoKeyValues.open = SMTDSettings.ExtraInfoKeyValues.count > 0
			updateRolloutTitle SMTD_ExtraInfoKeyValues.open
		)

	)
	rollout SMTD_JobEnvironmentKeys "Job Environment Keys"
	(
		checkbox chk_includeEnvironment "Include Current Environment With Submission " align:#left across:2 tooltip:"When checked, the submitting machine's Environment Keys and Values will be included in the Job submission automatically. If a Key with the same name is defined manually, the manual Value will be used instead.\n\nWhen unchecked, only the manually defined Environment Keys and Values will be included, if any."
		checkbox chk_UseJobEnvironmentOnly "Use Only Job Environment When Rendering " align:#right tooltip:"When checked, only the Job Environment values will be used when rendering.\n\nWhen unchecked, the Job Environment keys will be merged with the Slave's Environment, overriding any keys with the same name."
		dotNetControl lv_environment "System.Windows.Forms.ListView" width:480 height:120 align:#center
		button btn_remove "X" across:4 width:20 height:18 align:#left offset:[-12,0] enabled:false tooltip:"REMOVE the Key and its Value from the list."
		edittext edt_key fieldwidth:100 across:2 align:#left offset:[-108,0]
		edittext edt_value fieldwidth:328 align:#center offset:[-10,0]
		button btn_add "+" width:20 height:18 align:#right offset:[8,0] enabled:false

		fn initListView =
		(
			lv_environment.gridLines = true
			lv_environment.View = (dotNetClass "System.Windows.Forms.View").Details
			lv_environment.fullRowSelect = true

			lv_environment.checkboxes = false

			lv_environment.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			lv_environment.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r (amin (SMTD_ColorPalette.maxBgColor.g+15) 255) (amin (SMTD_ColorPalette.maxBgColor.b+5) 255)

			lv_environment.LabelEdit = false
			column1 = lv_environment.Columns.add "Environment KEY" 120
			column2 = lv_environment.Columns.add "Environment VALUE" 350
		)

		local isUpdatingList = false
		fn updateListView =
		(
			isUpdatingList = true
			local theRange = #()
			lv_environment.Items.clear()
			for i in SMTDSettings.EnvironmentKeyValues  do
			(
				li = dotNetObject "System.Windows.Forms.ListViewItem" i[1]
				subli = li.SubItems.add i[2]
				append theRange li
			)
			lv_environment.Items.AddRange theRange
			isUpdatingList = false
		)


		on chk_includeEnvironment changed state do
		(
			SMTDSettings.IncludeEnvironment = state
			if SMTDFunctions.IsSettingSticky "JobEnvironmentKeys" "IncludeEnvironment" then
			(
				setIniSetting SMTDPaths.InIFile "JobEnvironmentKeys"  "IncludeEnvironment" (state as string)
				SMTD_MainRollout.Ui_report ("+'Include Job Environment Keys With Submission' set to [" +state as string + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+'Include Job Environment Keys With Submission' set to [" +state as string + "] for the current session.")
			)
		)
		on chk_UseJobEnvironmentOnly changed state do
		(
			SMTDSettings.UseJobEnvironmentOnly = state

			if SMTDFunctions.IsSettingSticky "JobEnvironmentKeys" "UseJobEnvironmentOnly" then
			(
				setIniSetting SMTDPaths.InIFile "JobEnvironmentKeys"  "UseJobEnvironmentOnly" (state as string)
				SMTD_MainRollout.Ui_report ("+'Use Only Job Environment Keys' set to [" +state as string + "].")
			)
			else
			(
				SMTD_MainRollout.Ui_report ("+'Use Only Job Environment Keys' set to [" +state as string + "] for the current session.")
			)
		)


		fn updateButtonStates =
		(
			local matchesExistingKey = (for i in SMTDSettings.EnvironmentKeyValues where matchPattern i[1] pattern:edt_key.text collect i[1]).count > 0
			local matchesExistingValue = (for i in SMTDSettings.EnvironmentKeyValues where (matchPattern i[1] pattern:edt_key.text AND matchPattern i[2] pattern:edt_value.text) collect i[1]).count > 0
			btn_add.enabled = edt_key.text.count != 0 and not matchesExistingValue
			btn_add.caption = if matchesExistingKey then "O" else "+"
			btn_add.tooltip = if matchesExistingKey then "OVERWRITE the existing Key's Value" else "ADD the New Key and its Value to the list."
			btn_remove.enabled = edt_key.text.count != 0 and matchesExistingKey
		)

		fn updateUI =
		(
			chk_includeEnvironment.caption = SMTDFunctions.getStickyCaption "JobEnvironmentKeys" "IncludeEnvironment" "Include Current Environment With Submission "
			chk_UseJobEnvironmentOnly.caption = SMTDFunctions.getStickyCaption "JobEnvironmentKeys" "UseJobEnvironmentOnly" "Use Only Job Environment Keys "

			chk_includeEnvironment.checked = SMTDSettings.IncludeEnvironment
			chk_UseJobEnvironmentOnly.checked = SMTDSettings.UseJobEnvironmentOnly

			updateListView()
			updateButtonStates()
		)

		fn filterCharacters txt mode:#key=
		(
			local filterArray = #("=")
			if mode == #key do join filterArray #("%","<",">","^","&","|",":"," ","\"")
			for i in filterArray do txt = substituteString txt i "_"
			txt
		)

		fn getListViewSelection lv =
		(
			try(for i = 1 to lv.items.count where lv.items.item[i-1].Selected collect i)catch #()
		)

		fn setListViewSelection lv theSel =
		(
			for i = 1 to lv.items.count do lv.items.item[i-1].Selected = theSel[i]
		)

		on lv_environment ItemSelectionChanged EventArgs do
		(
			local theSel = getListViewSelection lv_environment
			for i in theSel do
			(
				edt_key.text = lv_environment.items.item[i-1].text
				edt_value.text = lv_environment.items.item[i-1].SubItems.item[1].text
			)
			updateButtonStates()
		)

		on btn_remove pressed do
		(
			SMTD_MainRollout.Ui_report ("+REMOVED Environment Key [" +edt_key.text + "="+ edt_value.text + "].")
			for i = SMTDSettings.EnvironmentKeyValues.count to 1 by -1 where matchPattern SMTDSettings.EnvironmentKeyValues[i][1] pattern:edt_key.text do deleteItem SMTDSettings.EnvironmentKeyValues i
			--edt_key.text = edt_value.text = ""
			updateUI()
		)

		on edt_key changed txt do updateButtonStates()
		on edt_value changed txt do updateButtonStates()

		on btn_add pressed do
		(
			local theIndexArray = for i = 1 to SMTDSettings.EnvironmentKeyValues.count where matchPattern SMTDSettings.EnvironmentKeyValues[i][1] pattern:edt_key.text collect i
			if theIndexArray.count > 0 then
			(
				for i in theIndexArray do
				(
					SMTD_MainRollout.Ui_report ("+UPDATED Environment Key [" +edt_key.text + "=" + SMTDSettings.EnvironmentKeyValues[i][2] +"] to ["+ edt_key.text + "=" + edt_value.text + "].")
					SMTDSettings.EnvironmentKeyValues[i][2] = filterCharacters edt_value.text mode:#value
				)
			)
			else
			(
				append SMTDSettings.EnvironmentKeyValues #(filterCharacters edt_key.text mode:#key, filterCharacters edt_value.text mode:#value)
				SMTD_MainRollout.Ui_report ("+ADDED Environment Key [" +edt_key.text + "="+ edt_value.text + "].")
			)
			edt_key.text = edt_value.text = ""
			updateUI()
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Job Environment Keys"
			if not state do
			(
				local count = SMTDSettings.EnvironmentKeyValues.count
				if count > 0 then
					theTitle += " ["+ count as string +" Env. Key"+ (if count == 1 then "" else "s")+"]"
				else
					theTitle += " [None]"
				if SMTDSettings.IncludeEnvironment do theTitle += " [Incl.Env.]"
				if SMTDSettings.UseJobEnvironmentOnly do theTitle += " [Use Job Env.Only]"
			)
			SMTD_JobEnvironmentKeys.title = theTitle
		)

		on SMTD_JobEnvironmentKeys rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_JobEnvironmentKeys open do
		(
			initListView()
			updateUI()
			SMTD_JobEnvironmentKeys.open = SMTDSettings.EnvironmentKeyValues.count > 0
			updateRolloutTitle SMTD_JobEnvironmentKeys.open
		)
	)

	rollout SMTD_AssetList "Scene And Asset Files" rolledup:false
	(
		progressbar prg_sceneSubmissionMode width:15 height:22 across:2 align:#left offset:[-10,-2] value:100 color:(white*0.75)
		dropdownlist ddl_sceneSubmissionMode offset:[10,-2] align:#right width:463
		button btn_setAlternativeNetworkStorage "..." across:2 height:18 width:15 offset:[-10,-3] align:#left
		edittext edt_alternativeNetworkStorage fieldwidth:462 offset:[9,-3] align:#right

		checkbox chk_SubmitVisibleObjectsOnly "Submit Visible Objects Only (Experimental, Creates Compact Max File)  "  offset:[5,-3]  align:#left  \
			tooltip:"When checked, only the objects currently visible in the scene or indirectly affecting the renderable objects in the scene will be submitted for rendering (depending on the Submit Scene options)\n\nWhen unchecked (default), the complete scene will be submitted for rendering.\n\nThis mode is considered Experimental and it might not work under certain circumstances.\n\nBe sure to test it out with your scenes before relying on it for final production rendering!"

		progressbar prg_assetSubmissionMode width:15 height:22 across:2 align:#left offset:[-10,0] value:100 color:(white*0.75)
		dropdownlist ddl_SubmitExternalFilesMode width:463 align:#right offset:[10,0]

		label lbl_info "" offset:[0,-1] across:3 align:#left
		checkbox chk_autoUpdate "Auto-Update  " align:#center offset:[25,-2]
		button btn_update "UPDATE Assets List" align:#right width:160 offset:[10,-5] height:18 tooltip:"Re-scans the scene for new Assets..."
		dotNetControl lv_assetsList "System.Windows.Forms.ListView" width:480 height:240 align:#center offset:[0,-2]
		checkbox chk_collectAllAssets "Collect All Available Frames In A Sequence" across:2 \
			tooltip:"When unchecked, only files from an external file sequence required by the current render time interval will be collected.\n\nWhen checked, all frames in a sequence will be collected, even if not required for rendering.\n\nThe latter is useful to ensure all files will be available if you intend to modify the frame range after submission."
		button btn_exportList "Export List..." align:#right offset:[10,-5] width:180 tooltip:"Save all assets to a text file, one filename per line."
		checkbox chk_preCacheAssets "Pre-Cache Asset Files On AWS" tooltip:"When checked, all assets will be pre-cached on AWS so Slaves that required them will be able to find them."

		fn updateAssetSubmissionMode =
		(
			prg_assetSubmissionMode.color = case SMTDSettings.SubmitExternalFilesMode of
			(
				default: (color 100 200 255)
				2: (color 255 200 100)
				3: (color 100 255 100)
			)
		)

		fn updateSubmissionMode =
		(
			local theIndex = findItem #(#reposave, #networksaveanduse, #globalnetworksave, #networksave, #networkremap) SMTDSettings.SubmitSceneMode
			if theIndex == 0 or theIndex > ddl_sceneSubmissionMode.items.count do
			(
				theIndex = 1
				SMTDSettings.SubmitSceneMode = #reposave
			)
			if SMTDSettings.SubmitExternalFilesMode > 1 and SMTDSettings.AssetsResolved.count > 0 do theIndex = 1
			ddl_sceneSubmissionMode.selection = theIndex

			local theTooltipText = case theIndex of
				(
					1: "The current scene will be saved to a temporary file which will be sent with the job and will be stored in the Job's folder in the Repository."
					2: "The current scene will be saved to its original location, and will be referenced by the job. \n\nAssuming the file resides on a dedicated file server, this will speed up submission and rendering significantly."
					3: "The current scene will be saved to a temporary file which will be copied to a Globally-Defined Alternative Network Location (e.g. dedicated file server).\n\nIt is specified in Repository\Submission\3dsmax\SubmitMaxToDeadline_Defaults.ini [UserOptions] SubmitSceneGlobalBasePath key.\n\nIt will be referenced by the Job via its path only.\n\nThis will reduce the load on the Repository server."
					4: "The current scene will be saved to a temporary file which will be copied to a User-Defined Alternative Network Location (e.g. dedicated file server) stored as a local setting.\n\nIt will be referenced by the Job via its path only.\n\nThis will reduce the load on the Repository server."
					5: "The current scene will NOT be saved, but the scene path will be remapped to the custom network path provided globally. \n\nAssuming the file resides on a dedicated file server, this will speed up submission and rendering significantly, but current changes to the scene objects will be ignored."
				)

			-- progressbar tooltips not supported in max 2016 and earlier
			try(prg_sceneSubmissionMode.tooltip = theTooltipText)catch()
			-- drop down tooltips not supported in max 2008 and earlier
			try(ddl_sceneSubmissionMode.tooltip = theTooltipText)catch()

			prg_sceneSubmissionMode.color = case theIndex of
			(
				1: (color 255 200 100)
				2: (color 255 255 100)
				3: (color 100 255 100)
				4: (color 200 100 255)
				5: (color 100 200 255)
				6: (color 255 100 255)
			)
			edt_alternativeNetworkStorage.enabled = findItem #(#networksave, #networkremap) SMTDSettings.SubmitSceneMode > 0
			edt_alternativeNetworkStorage.readonly = SMTDSettings.SubmitSceneMode == #networkremap
			btn_setAlternativeNetworkStorage.enabled = SMTDSettings.SubmitSceneMode == #networksave
			ddl_sceneSubmissionMode.enabled = not (SMTDSettings.SubmitExternalFilesMode > 1 and SMTDSettings.AssetsResolved.count > 0)
			if not ddl_sceneSubmissionMode.enabled and SMTDSettings.SubmitSceneMode != #reposave do
			(
				prg_sceneSubmissionMode.color = color 255 100 100
				local theTooltipText = "POSSIBLE OVERRIDE: The scene will be saved and submitted with the job to the Repository if any external assets are included in the submission."

				try(prg_sceneSubmissionMode.tooltip = theTooltipText)catch()
				try(ddl_sceneSubmissionMode.tooltip = theTooltipText)catch()
			)

			edt_alternativeNetworkStorage.text = (case SMTDSettings.SubmitSceneMode of
				(
					#globalnetworksave: SMTDSettings.SubmitSceneGlobalBasePath
					#networksave: SMTDSettings.SubmitSceneBasePath
					#networkremap: (
						local theCurrentPath = (maxFilePath + maxFileName)
						global SMTD_RemapLocalToNetworkPath
						fn SMTD_RemapLocalToNetworkPath thepath = ( thepath )
						local theScriptFile = (SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_RemapLocalToNetworkPath.ms"  )
						if doesFileExist theScriptFile do try(fileIn theScriptFile)catch()
						::SMTD_RemapLocalToNetworkPath theCurrentPath
					)
					default: ""
				)
			)
			SMTD_MainRollout.updateSubmitButtonState()
		)

		fn initListView lv =
		(
			lv.gridLines = true
			lv.View = (dotNetClass "System.Windows.Forms.View").Details
			lv.fullRowSelect = true

			lv.checkboxes = false

			lv.foreColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
			lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r (amin (SMTD_ColorPalette.maxBgColor.g+15) 255) (amin (SMTD_ColorPalette.maxBgColor.b+5) 255)

			lv.LabelEdit = false
			column1 = lv.Columns.add "Asset Filename" 220
			column2 = lv.Columns.add "Asset Path - Right-Click To Reveal In Explorer" 500
		)

		fn updateListView lv forceUpdate:false =
		(
			local theRange = #()
			lv.Items.clear()
			if forceUpdate do SMTDSettings.AssetsResolved = SMTDFunctions.resolveAssetsFromAssetTracker SubmitExternalFilesMode:SMTDSettings.SubmitExternalFilesMode
			for i in SMTDSettings.AssetsResolved do
			(
				li = dotNetObject "System.Windows.Forms.ListViewItem" (filenameFromPath i)
				sub_li = li.SubItems.add (getFileNamePath i)
				append theRange li
			)
			lv.Items.AddRange theRange
			isUpdatingList = false
			lbl_info.text = case SMTDSettings.SubmitExternalFilesMode of
			(
				default: "Asset Collection Disabled"
				1: (SMTDSettings.AssetsResolved.count as string +" Asset File"+ (if SMTDSettings.AssetsResolved.count == 1 then "" else "s") + " Found:")
				2: (SMTDSettings.AssetsResolved.count as string +" Local Asset File"+ (if SMTDSettings.AssetsResolved.count == 1 then "" else "s") + " Found:")
				3: (SMTDSettings.AssetsResolved.count as string +" Asset File"+ (if SMTDSettings.AssetsResolved.count == 1 then "" else "s") + " Found:")
			)
		)

		on lv_assetsList MouseClick args do
		(
			if args.Button == args.Button.Right do
			(
				theItem = (lv_assetsList.HitTest args.x args.y)
				--subItem = theItem.SubItem
				--popupmenu pos:mouse.screenpos
				thePath = theItem.subitem.text
				if doesFileExist thePath do shellLaunch thePath ""
			)
		)

		on lv_assetsList DoubleClick args do
		(
		)

		on btn_update pressed do
		(
			updateListView lv_assetsList forceUpdate:true
			updateSubmissionMode()
		)

		on btn_exportList pressed do
		(
			local theFile = getSaveFileName caption:"Please specify a text file to write the Assets List to..." filename:("Assets_"+(getFilenameFile maxfilename)) types:"Text file (*.txt)|*.txt|All Files (*.*)|*.*"
			if theFile != undefined do
			(
				theFileHandle = createFile theFile encoding:#utf8 writeBOM:true
				for f in SMTDSettings.AssetsResolved do
					format "%\n" f to:theFileHandle
				close theFileHandle
				shellLaunch "notepad.exe" theFile
			)
		)

		on chk_collectAllAssets changed state do
		(
			setIniSetting SMTDPaths.InIFile "Assets" "AssetSyncAllFiles" (state as string)
			SMTD_MainRollout.Ui_report ("+Collect All Available Frames In A Sequence Set To ["+ state as string +"]")
			SMTDSettings.AssetSyncAllFiles = state
			updateListView lv_assetsList forceUpdate:chk_autoUpdate.checked
		)

		on chk_preCacheAssets changed state do
		(
			setIniSetting SMTDPaths.InIFile "Assets" "AssetsPreCacheFiles" (state as string)
			SMTD_MainRollout.Ui_report ("+Precache Asset Files set to ["+ state as string +"]")
			SMTDSettings.AssetsPreCacheFiles = state
		)

		on ddl_SubmitExternalFilesMode selected itm do
		(
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "SubmitExternalFilesMode" ((SMTDSettings.SubmitExternalFilesMode = ddl_SubmitExternalFilesMode.selection) as string)
			SMTD_MainRollout.Ui_report ("+Rendering: Submit External Files Mode set to [" + ddl_SubmitExternalFilesMode.items[ddl_SubmitExternalFilesMode.selection] + "].")
			updateListView lv_assetsList forceUpdate:chk_autoUpdate.checked
			updateAssetSubmissionMode()
			updateSubmissionMode()
		)

		on chk_SubmitVisibleObjectsOnly changed state do
		(
			setIniSetting SMTDPaths.InIFile "JobSettings"  "SubmitVisibleObjectsOnly" ( (SMTDSettings.SubmitVisibleObjectsOnly = state) as string)
			SMTD_MainRollout.Ui_report ("+Job Options: Submit Visible Objects Only option set to [" + state as string + "]")
			if state AND SMTDFunctions.HasActiveSceneXRefs() then
				messagebox "The file contains active SCENE XREFs!\nScene XRefs are not supported by the 'Submit Visible Objects Only' feature!\nTo avoid data loss, the state of this option will be ignorred and\bthe complete scene will be submitted." title:"Scene XRefs Warning"
		)

		on ddl_sceneSubmissionMode selected itm do
		(
			SMTDSettings.SubmitSceneMode = case itm of
			(
				1: #reposave
				2: #networksaveanduse
				3: #globalnetworksave
				4: #networksave
				5: #networkremap
			)
			setIniSetting SMTDPaths.InIFile "UserOptions"  "SubmitSceneMode"  (SMTDSettings.SubmitSceneMode as string)
			updateSubmissionMode()
		)

		on btn_setAlternativeNetworkStorage pressed do
		(
			local thePath = getSavePath()
			if thePath != undefined do
			(
				setIniSetting SMTDPaths.InIFile "UserOptions"  "SubmitSceneBasePath" (edt_alternativeNetworkStorage.text = SMTDSettings.SubmitSceneBasePath = thePath)
				updateSubmissionMode()
			)
		)

		on edt_alternativeNetworkStorage entered txt do
		(
			setIniSetting SMTDPaths.InIFile "UserOptions"  "SubmitSceneBasePath" (edt_alternativeNetworkStorage.text = SMTDSettings.SubmitSceneBasePath = txt)
			updateSubmissionMode()
		)
		on chk_autoUpdate changed state do
		(
			setIniSetting SMTDPaths.InIFile "Assets"  "AssetsAutoUpdateList" ((SMTDSettings.AssetsAutoUpdateList = state) as string)
			updateListView lv_assetsList forceUpdate:SMTDSettings.AssetsAutoUpdateList
		)

		fn updateRolloutTitle state =
		(
			local theTitle = "Scene And Asset Files"
			if not state do
			(
				case SMTDSettings.SubmitSceneMode of
				(
					#reposave: theTitle+= " [Repository Save]"
					#networksaveanduse: theTitle+= " [Original Network Save]"
					#globalnetworksave: theTitle+= " [Global Network Save]"
					#networksave: theTitle+= " [Custom Network Save]"
					#networkremap: theTitle+= " [Network Remap]"
				)
				case SMTDSettings.SubmitExternalFilesMode of
				(
					default: ()
					2: theTitle+= " [Copy Local Assets]"
					3: theTitle+= " [Copy All Assets]"
					4: theTitle+= " [Local Cache]"
				)
			)
			SMTD_AssetList.title = theTitle
		)

		on SMTD_AssetList rolledup state do
		(
			updateRolloutTitle state
		)

		on SMTD_AssetList open do
		(
			SMTD_AssetList.open = false
			initListView lv_assetsList
			updateListView lv_assetsList forceUpdate:SMTDSettings.AssetsAutoUpdateList
			chk_collectAllAssets.state = SMTDSettings.AssetSyncAllFiles
			chk_preCacheAssets.state = SMTDSettings.AssetsPreCacheFiles
			ddl_SubmitExternalFilesMode.selection = SMTDSettings.SubmitExternalFilesMode
			ddl_SubmitExternalFilesMode.enabled = (SMTDSettings.CurrentRepository == "")
			updateAssetSubmissionMode()

			local theItems =	#("SAVE and Submit Current Scene File with the Job to the REPOSITORY",
					"SAVE and Use Current Scene's ORIGINAL NETWORK PATH",
					"SAVE and Submit Current Scene File to GLOBAL NETWORK PATH",
					"SAVE and Submit Current Scene File to USER-DEFINED NETWORK PATH"
					--"DO NOT SAVE And Use Current Scene's ORIGINAL NETWORK PATH"
					)
			local theScriptFile = (SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_RemapLocalToNetworkPath.ms"  )
			if doesFileExist theScriptFile do append theItems "DO NOT SAVE And REMAP Current Scene's Path To NETWORK PATH"
			ddl_sceneSubmissionMode.items = theItems

			updateSubmissionMode()
			chk_SubmitVisibleObjectsOnly.state = SMTDSettings.SubmitVisibleObjectsOnly

			ddl_SubmitExternalFilesMode.items = if SMTDFunctions.IsSettingSticky "RenderingOptions" "SubmitExternalFilesMode" then
				#("Do NOT copy External File References to Repository","Copy LOCAL External File References to Repository","Copy ALL External File References to Repository")--,"Cache External File References On Slave (Experimental)"
			else
				#("Do NOT copy External File References to Repository*","Copy LOCAL External File References to Repository*","Copy ALL External File References to Repository*") --,"Cache External File References On Slave (Experimental)*")

			chk_autoUpdate.state = SMTDSettings.AssetsAutoUpdateList
			chk_autoUpdate.caption = SMTDFunctions.getStickyCaption "Assets" "AssetsAutoUpdateList" "Auto-Update "

			chk_SubmitVisibleObjectsOnly.caption = SMTDFunctions.getStickyCaption "JobSettings" "SubmitVisibleObjectsOnly" "Submit Visible Objects Only (Experimental, Creates Compact Max File) "
			SMTD_AssetList.open = true
		)
	)

	SMTD_LegacyRolloutsLayout = #(
		#(#("Job","Job Settings including the Job Options, Job Dependencies and Job Scheduling rollouts"),#(#(SMTD_JobSubmission,false), #(SMTD_JobOptions,true), #(SMTD_Dependencies,false), #(SMTD_PassDependencies,false), #(SMTD_JobScheduling,false), #(SMTD_JobFailureDetection,false))),
		#(#("Assets","Assets - Asset Collection And Synchronization"),#(#(SMTD_AssetList,true))),
		#(#("Render","Rendering,DBR, GPU, Pathing and Image Sequence Options"),#(#(SMTD_ScenePreProcessing,true), #(SMTD_MaxStartup,false), #(SMTD_MaxRendering,false), #(SMTD_DBR,false), #(SMTD_GPU,false), #(SMTD_Gamma,false), #(SMTD_Pathing,false), #(SMTD_IMSQ,false))),
		#(#("Options","Submission Options"),#(#(SMTD_UserOptions,true), #(SMTD_RendererExport,false), #(SMTD_SubmissionTimeouts,false))),
		#(#("Limits","Black List Management and License Limits"),#(#(SMTD_BlackListSlaves,true), #(SMTD_LimitGroups,false))),
		#(#("StateSets","State Sets - Batch Submission of Render Passes"),#(#(SMTD_StateSets,true))),
		#(#("Scripts","Python and MAXScripts to run at Submission and at Render time, as well as MAXScript Job Submission"),#(#(SMTD_PythonScripts,false), #(SMTD_RunScripts,true))),
		#(#("Tiles","Tile Rendering - Splitting a frame between multiple Slaves"),#(#(SMTD_TileOptions,true),#(SMTD_MultiRegionRendering,false), #(SMTD_TilesRendering,false), #(SMTD_RegionRendering,false))),
		#(#("Misc","Includes Batch Submit and Extra Info Keys"), #(#(SMTD_BatchSubmit,true), #(SMTD_ExtraInfo,false), #(SMTD_ExtraInfoKeyValues,false), #(SMTD_JobEnvironmentKeys,false)))
	)
	SMTD_RolloutsLayout = SMTD_LegacyRolloutsLayout
	local ssP = try(dotNetObject "Autodesk.Max.StateSets.Plugin")catch(undefined)
	if ssP == undefined do
		for i = SMTD_RolloutsLayout.count to 1 by -1 where matchPattern SMTD_RolloutsLayout[i][1][1] pattern:"StateSets" do
			deleteItem SMTD_RolloutsLayout i
	if rpmData == undefined or RPMDataNet.CustomSubmitStruct == undefined do deleteItem SMTD_RolloutsLayout[1][2] 4

	case SMTDFunctions.getRepositoryList() of
	(
		#success:
		(
			local thePos = [100,100]
			local theVal = getIniSetting SMTDPaths.InIFile "Dialog" "Position"
			if theVal != "" do thePos = execute theVal
			if thePos.x > sysinfo.DesktopSize.x - 420 do thePos.x = sysinfo.DesktopSize.x - 420 --move back to screen if dual monitor changed to single monitor or if outside the desktop
			if thePos.y > sysinfo.DesktopSize.y - 100 do thePos.y = sysinfo.DesktopSize.y - 700 --if minimized, fit back to screen
			if thePos.x < 0 do thePos.x = 0
			if thePos.y < 0 do thePos.y = 0

			if rpmdata != undefined and RPMDataNet.CustomSubmitStruct != undefined then
			(
				rpmdata.RPMCustomSubmit=#()
				append rpmdata.RPMCustomSubmit SMTD_MainRollout
				RPMDataNet.CustomSubmitStruct.Deadline6Rollout = SMTD_MainRollout

				local RPM_Layout = #()
				for i in SMTD_RolloutsLayout do
					append RPM_Layout #(i[1], (for j in i[2] collect j[1]) )

				RPMDataNet.CustomSubmitStruct.Deadline6SubRolloutItems = RPM_Layout
				SMTDFunctions.loadSettings()
				--SMTDFunctions.CollectSubmissionInfo()
			)
			else
			(
				local theHeight = 740
				local theVal = getIniSetting SMTDPaths.InIFile "Dialog" "Height"
				if theVal != "" do theHeight = execute theVal
				if theHeight > sysinfo.DesktopSize.y-thePos.y do theHeight = 740

				SMTDFunctions.restoreSettingstFromScene base:#sticky --load to ensure the rollouts added to the dialog contain the right data
				CreateDialog SMTD_MainRollout 500 theHeight pos:thePos style:#(#style_titlebar, #style_border, #style_sysmenu, #style_minimizebox, #style_resizing)  menu:SMTD_MainRollout_MainMenu
				SMTDFunctions.restoreSettingstFromScene base:#sticky --reload to ensure the Log which was initialized after the creation reports what was loaded!

				SMTD_MainRollout.loadWorkflows()
				SMTD_MainRollout.updateWorkflowMode()
				SMTD_MainRollout.Ui_report ("Ready.")
				#success
			)
		)
		#timeout: MessageBox "DeadlineCommand.exe failed to return a list of Repositories within reasonable time!" title:"SubmitMaxToDeadline"
		#failed: MessageBox "DeadlineCommand.exe command failed to return a list of Repositories!" title:"SubmitMaxToDeadline"
		#readerror: MessageBox "DeadlineCommand.exe command failed to return a valid list of Repositories!" title:"SubmitMaxToDeadline"
	)--end case
	SMTDFunctions.cleanUpSubmissionFolders()
)--end script
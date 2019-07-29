(
	global SMTD_MainRollout 							--contains the main rollout (dialog)
	global SMTDFunctions 								--contains the struct of functions 
	global SMTDPaths 									--contains the struct of paths
	global SMTDSettings 								--contains the struct of settings
	global SMTDSettingsFactory 							--the factory defaults struct
	global SMTDSettingsDefaults 						--the user defaults after loading all sticky settings and global defaults
	global SMTD_SceneMaterials = #() 					--used to collect all scene materials for custom shader rendering
	global SMTD_LastMessage = ""						--stores the last message when calling the alternative submitJob() function typically used by 3rd party scripts
	global SMTD_objsToBake 								--used for collecting the objects for texture baking
	global SMTD_StateSetsTree = #() 					--stores the state sets tree 
	global SMTD_StateSetsTreeForSubmission = #() 		--stores the state sets tree 
	global SMTD_DebugPrintsOn = false 					--when set to true, additional debug info will be printed to the Listener
	global sfs 											--makes sure the brazil structure is predefined
	global SMTD_IntegrationKVPs = #() 					--key value pairs array
	global SMTDIsCurrentlySubmitting = undefined 		--True when UI SUBMIT button was checked, False when unchecked to cancel, and Undefined in all other cases (for compatibility with older 3rd party submission scripts).
	global SMTDSaveInSceneExclusionList = #() 			--contains the SMTDSetting properties which should not be loaded from the MAX scene file
	global SMTD_externalResourcesMode = #assetTracker 	--#legacy --this is a temporary switch to allow testing the new Asset Tracker functionality vs. the old introspection functions

	try(destroyDialog SMTD_MainRollout)catch() --make sure the SMTD UI is closed before reinitializing all structures
	
	struct SMTDPathsStruct --the structure of system paths used by the submitter
	(
		HomeDir,
		UserHomeDir,
		BinDir,
		LogsDir,
		TempDir,
		SettingsDir,
		DeadlineExec,
		DeadlineBGExec,
		SubmitInfoFile,
		JobInfoFile,
		DraftConfigFile,
		ResultFile,
		BitmapList,
		RestoreTempMaxFile,
		SubmitOutput ,
		SubmitExitCode,
		IniFile,
		ImsqVbscriptFile,
		submitSubFolder,
		MainSubmissionDir,
		IntegrationDir,
		PluginDir, -- contains the root of the 3dsmax plugin folder. Obsolete, not used within SMTD anymore. Use PluginDir3dsmax for the direct path to the 3dsmax plugin folder.
		PluginDir3dsmax, -- path to the 3dsmax plugin folder.
		DraftDir
	)
	
	SMTDPaths = SMTDPathsStruct() --the global instance of the paths structure storing the actual paths.
	SMTDPaths.BinDir = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\" --we grab the path to the binaries from the Windows Env. variable introduced in Deadline 7
	SMTDPaths.DeadlineExec = SMTDPaths.BinDir + "deadlinecommand.exe" --this is the deadlinecommand that returns results in memory
	SMTDPaths.DeadlineBGExec = SMTDPaths.BinDir + "deadlinecommandbg.exe" --this one writes the results to files on disk
	
	global SMTDExternalRefsArray
	struct SMTDExternalRefsArrayStruct 
	(
		totalSubsArray = #(),
		storeBitmapPath = #(),
		storeHdriPath = #(),
		StoreSceneXRefs = #(),
		StoreObjectXRefs = #(),
		StoreSceneVrayProxies = #(),
		StoreSceneCoronaProxies = #(),
		StoreSceneMRProxies = #(),
		StoreRendererPaths = #(),
		StoreBrazilv2RendererPaths = #(),
		StoreAnimaPaths = #()
	)
	SMTDExternalRefsArray = SMTDExternalRefsArrayStruct()
	
	
	struct SMTD_ColorPaletteStruct 
	(
		orangeColor, blueColor, redColor, greenColor, grayColor, lightGrayColor, lightBlueColor, highlightBgColor, textColor, maxBgColor, blackColor
	)
	global SMTD_ColorPalette = SMTD_ColorPaletteStruct()
	
	fn defineDotNetColors =
	(
		SMTD_ColorPalette.textColor = ( ((colorman.getcolor #text) as color)*255)
		SMTD_ColorPalette.maxBgColor = (((colorman.getcolor #window)) as color)*255
		SMTD_ColorPalette.blackColor = (dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.textColor.r SMTD_ColorPalette.textColor.g SMTD_ColorPalette.textColor.b
		if SMTD_ColorPalette.maxBgColor.v >= 160 then
		(
			SMTD_ColorPalette.redColor = (dotNetClass "System.Drawing.Color").fromARGB 192 0 0
			SMTD_ColorPalette.orangeColor = (dotNetClass "System.Drawing.Color").fromARGB 240 160 0
			SMTD_ColorPalette.greenColor = (dotNetClass "System.Drawing.Color").fromARGB 0 128 0
			SMTD_ColorPalette.blueColor = (dotNetClass "System.Drawing.Color").fromARGB 0 0 128
			SMTD_ColorPalette.lightBlueColor = (dotNetClass "System.Drawing.Color").fromARGB 90 128 160
			SMTD_ColorPalette.grayColor = (dotNetClass "System.Drawing.Color").fromARGB 128 128 128
			SMTD_ColorPalette.lightGrayColor = (dotNetClass "System.Drawing.Color").fromARGB 160 160 160
			SMTD_ColorPalette.highlightBgColor = (dotNetClass "System.Drawing.Color").fromARGB 180 190 200
		)
		else
		(
			SMTD_ColorPalette.redColor = (dotNetClass "System.Drawing.Color").fromARGB 255 128 128
			SMTD_ColorPalette.orangeColor = (dotNetClass "System.Drawing.Color").fromARGB 255 180 50
			SMTD_ColorPalette.greenColor = (dotNetClass "System.Drawing.Color").fromARGB 128 255 128
			SMTD_ColorPalette.blueColor = (dotNetClass "System.Drawing.Color").fromARGB 170 200 255
			SMTD_ColorPalette.lightBlueColor = (dotNetClass "System.Drawing.Color").fromARGB 128 160 255
			SMTD_ColorPalette.grayColor = (dotNetClass "System.Drawing.Color").fromARGB 192 192 192
			SMTD_ColorPalette.lightGrayColor = (dotNetClass "System.Drawing.Color").fromARGB 160 160 160
			SMTD_ColorPalette.highlightBgColor = (dotNetClass "System.Drawing.Color").fromARGB 20 40 60
		)				
	)		
	defineDotNetColors()
	
	--The global structure of settings
	--This structure holds ALL settings needed by the submit function,
	--thus there is no need for the actual UI to be ever opened in order to submit a Max scene job
	--Just set the desired settings in this structure or keep the defaults and call the submit function.
	struct SMTDSettingsStructure 						
	(
		VersionString = "10.0", --Only used for documentation links, updated from -GetSubmissionInfo shortversion
		JobName = "3ds Max Deadline Job",
		Comment = "",
		UserName = sysinfo.username,
		Department = "",
		Group = "none",
		Groups = #(),
		
		Category = "", --obsolete, left for backwards compatibility 
		Categories = #(), --obsolete, left for backwards compatibility 
		
		theIniFiles = #(),
		theIniFilenames = #(),
		
		RepositoryList = #("DISABLED"),
		RepositoryListActual = #(),
		
		CurrentRepository = "",
		CurrentRepository2 = "",
		Pools = #(),
		PoolExclusive = false,
		PoolName = "none",
		Pool2Name = "",
		
		SubmitScene = true,
		SubmitSceneMode = #reposave, --#reposave, #networksave, #globalnetworksave, #networksaveanduse, #networkremap
		SubmitSceneBasePath = "",
		SubmitSceneGlobalBasePath = "",
		SubmitSceneNetworkLocation = "",
		SubmitSceneNetworkReuseLocation = false, --when true, the submission will use the already saved file from SubmitSceneNetworkLocation. Mainly for State Sets submission  
		
		ExternalFilesWarningOn = false,
		ExternalFilesWarningCount = 100,
		ExternalFilesWarningMB = 1024,		

		OneCpuPerTask = false,
		RenderThreads=0,
		LocalRendering = true,
		CloseAfterSubmission = false,
		PoolsSort = false, --obsolete, left for backwards compatibility
		MaximumPriority = -1,
		Priority = 50,
		LimitEnabled = false,
		MachineLimit = 1,
		RenderOutOfOrder = false,
		OutOfOrderMethod = #normal,
		OutOfOrderStep = 10,
		SubmitAsSuspended = false,
		SubmitAsDependent = false,
		AutoDelete = false,
		OnComplete = "Nothing",
		ChunkSize = 1,
		SequentialJob = false,
		MaxVersionToForce = "none",
		MaxVersionToForceSticky = false, --deprecated in Deadline 10
		TaskLimit = 5000,
		
		OverrideFailOnExistingMaxProcess = false,
		FailOnExistingMaxProcess = false,
		
		DisableProgressUpdateTimeout = false,
		SkipRender = false,
		JobIsInterruptible = false,
		
		MaxTasksPerSlave = 1,
		LimitTasksToNumberOfCpus = true,
		
		JobsArray = #(),
		FullJobsArray = #(),
		PreviousJobsArray = #(),
		DependencyJobItems = #{},
		ResumeOnDeletedDependencies = false,
		DependOnPreviousJobMode = #previous,

		AssemblerOverride = false,
		AssemblerPoolName = "none",
		AssemblerPool2Name = "",
		AssemblerGroup = "none",
		AssemblerPriority = 50,
		
		TilesInX = 1,
		TilesInY = 1,
		TilesRendering = false, --deprecated, see RegionRenderingMode
		TileBlowupMode = false,
		SingleTileJob = true,  --deprecated, see RegionRenderingMode
		SingleTileJobDependent = true,
		SingleTileJobCleanup = false,
		SingleTileJobDraft = true,  --deprecated, always using Draft
		SingleTileJobDraftErrorOnMissing = true,
		SingleTileJobLeft = "",
		SingleTileJobRight = "",
		SingleTileJobTop = "",
		SingleTileJobBottom = "",
		SingleTileJobFilename = "",
		SingleTileJobReFilename = "",
		SingleTileJobTileCount = 0,
		SingleTileJobFrameList = "",
		--TilesSubmissionMode = #local,
		TilesPadding = 0,
		TilesSubmissionJobIDs = #(),
		RegionRendering = false,
		RegionLeft = 0,
		RegionTop = 0,
		RegionRight = 100,
		RegionBottom = 100,
		RegionType = 1, --1 = Region (NOCROP)  2 = CROP  3 = BLOWUP  used only if RegionRendering is True
		RegionUseMaxValues = true,
		CustomTiles = #(),
		UseCustomTiles = false,
		CustomTilesPreviewWidth = 640,
		CustomTilesPreviewHeight = 480,	
		MultiRegionData = #(),
		MultiRegionRendering = false,
		MultiRegionBackground = #off,
		MultiRegionBackgroundImage = "",
		MultiRegionCopyDraftConfig = false,
		MultiRegionFitPadding = 10.0,
		--MachineLimitTileJobs = false,
		
		RawBufferFileName = "",
		RawBufferFile = "",
		SplitBufferFilename = "",
		SplitBufferFile = "",
		
		DBR = false,
		DBRServers = 5,
		DBRUse3dsCmd = true,

		GpusPerTask = 0,
		GpuDevices = "",
		
		RegionRenderingMode = #none, --#none, #singleFrameMultiRegion, #animationMultiRegion, #singleFrameTiles, #maxRegion
		
		UseSubmissionQueue = false,
		
		LimitGroups = #(),
		LimitGroupsToUse = #(),
		LimitGroupAutoBrazil = false,
		LimitGroupAutoVRay = false,
		LimitGroupAutoCorona = false,
		LimitGroupAutoKrakatoa = false,
		LimitGroupAutoFinalRender = false,
		LimitGroupAutoMaxwell = false,
		LimitGroupAutoWorkstation = false,
		LimitGroupAutoRedshift = false,
		LimitGroupAutoMaxIO = false,
		LimitGroupAutoArnold = false,
		LimitGroupAutoIray = false,
		LimitGroupAutoMentalRay = false,
		LimitGroupAutoOctane = false,
				
		DropSubmission = false,
		BgSubmission = false,
		UseJpegOutput = false,
		JpegOutputPath = "",
		AlternateEmails = "",
		NotificationNote = "",
		
		TransferPool = "none",
		TransferGroup = "none",
		TransferPriority = 50,
		TransferDeleteOnComplete = true,
		TransferJobAsSuspended = false,
		TransferCompressed = true,
		
		UseAltPluginIni = false,
		AutoSuggestIni = false,
		AltINISelection = 1, 
		AltPluginIni = "",
		AltIniPath = "c:\\", --obsolete
		
		EnableFailOnBlackFrames = false,
		BlackPixelPercentage = 1,
		BlackPixelThreshold = 0.1,
		BlackFramesCheckRenderElements = false,
		
		RemovePadding = false,
		
		GammaCorrection = false,
		GammaInput = 1.0,
		GammaOutput = 1.0,
		
		IgnoreMissingExternalFiles = true,
		IgnoreMissingUVWs = true,
		IgnoreMissingXREFs = true,
		IgnoreMissingDLLs = false,
		DisableMultipass = false,
		MergeXRefsOnSubmission = false,
		MergeSceneXRefsOnSubmission = false,
		
		ForceWorkstationMode = false,
		UseSilentMode = true,
		PopupHandling = true,
		
		RestartRenderer = true,
		StrictOutput = false,
		ShowFrameBuffer = true,

		ShowRendererFrameBufferOverride = false,
		ShowRendererFrameBuffer = true,
		
		OverrideBitmapPager = false,
		BitmapPager = false,
		
		SubmitExternalFiles = false,
		SubmitExternalFilesMode = 1,
		
		PerformSanityCheck = true,
		DeadlineSubmissionSuccessful = false,
		DeadlineSubmissionLastJobID = "none",
		
		DependOnPreviousJobID = "",
		DependOnPreviousJob = false,
		
		SubmitVisibleObjectsOnly = false,
		
		CopyVbscriptFile = false,
		CreateImsqFile = false,
		CopyImsqFile = false,
		ImsqOutputPath = "",
		
		UsePathConfigFile = false,
		MergePathConfigFile = false,
		PathConfigFile = "",
		IncludeLocalPaths = false,
		
		RunPreLoadScript = false,
		RunPostLoadScript = false,
		RunPreFrameScript = false,
		RunPostFrameScript = false,
		
		PreLoadScriptFile = "",
		PostLoadScriptFile = "",
		PreFrameScriptFile = "",
		PostFrameScriptFile = "",
		
		RunPreJobScript = false,
		RunPostJobScript = false,
		RunPreTaskScript = false,
		RunPostTaskScript = false,
		
		PreJobScriptFile = "",
		PostJobScriptFile = "",
		PreTaskScriptFile = "",
		PostTaskScriptFile = "",
		
		SubmitAsMXSJob = false,
		MAXScriptFile = "",
		SingleTaskJob = false,
		
		UseCustomShader = false,
		CustomShaderMode = 1,
		--AutoSuggestCategory = true,
		
		UseBatchRender = false,
		BatchRenderMode = 1,
		CleanupSubmissionFoldersAfterEachBatchJob = true,
		
		RenderFramesPreviewJob = false,
		PreviewJobFrameCount  = 3,
		PreviewJobPriorityOffset = 1,
		PreviewJobSecondJobDependentOnFirst = true,
		PreviewJobSecondJobSuspended = false,
		
		RenderElementsUpdatePaths = true,
		RenderElementsUpdateFilenames = true,
		RenderElementsIncludeNameInPath = false,
		RenderElementsIncludeTypeInPath = false,
		RenderElementsIncludeNameInFileName = true,
		RenderElementsIncludeTypeInFileName = false,
		RenderElementsPermanentChanges = true,
		RebuildRenderElements = true,
		IgnoreRenderElements = false,
		Delimiter = ".", --use the "SubmitMaxToDeadline_Defaults.ini" file to configure the Delimiter to another character such as Delimiter="" (blank) under [RenderingOptions] category.
		OutputFilenamePattern = "$SC$TD$SS$TD$BN", --"$BN.$SS$TD$SC", -- $SC=StereoCamera; $TD=TokenDelimiter (see below); $SS=StateSet; $BN=BaseName
		OutputFilenameTokenDelimiter = "_",
		PurifyFilenames = false,
		PurifyCharacterCodes = #(33,35,42,63), --#("#","!","?","*"),
		ForceLowerCaseFilenames = false,
		ReplaceOutputFilenameWithUserPattern = false,
		OutputFilenameUserPattern = "", --the pattern should be defined under [RenderingOptions] category, OutputFilenameUserPattern key of the repository file "SubmitMaxToDeadline_Defaults.ini".
		RenderElementNamesPermanentChanges = true,
		OriginalRenderElementNames = #(),
		
		QuicktimeGenerate = false, --deprecated
		QuicktimeSettingsFile = "", --deprecated
		QuicktimePoolName = "none", --deprecated
		QuicktimeGroupName = "none", --deprecated
		QuicktimeFilenameMode = 1, --deprecated
		QuicktimeCustomFilename = "quicktime_animation", --deprecated
		QuicktimesToGenerate = #(), --deprecated
		
		Slaves = #(),
		SlavesList = #(),
		SlavesBlackList = true,
		SlavesNamedSet = "",
		SlaveSettingsSticky = true,
		SlaveInfo = #(),
		SlaveInfoCollected = false,
		
		MastersList = #(),
		MastersBlackList = true,
		MastersNamedSet = "",
		MastersSettingsSticky = true,
		
		TimeoutSubmission = 3600,
		TimeoutQTSubmission = 120, --deprecated
		TimeoutCollectData = 60,
		
		AutomaticallyUpdateJobName = false,
		OverrideLowPriorityThread = true,
		MeditMaterialsStorage = #(),
		ClearMaterialEditorOnSubmission = true,
		UnlockMEditRenderer = false,
		
		ExportAdvancedRenderOutputFiles = true,
		ExportAdvancedRenderInfoScanline = true,
		ExportAdvancedRenderInfoMentalRay = true,
		ExportAdvancedRenderInfoBrazil = false, --not used anymore, left for compatibility
		ExportAdvancedRenderInfoBrazil2 = true,
		ExportAdvancedRenderInfoVRay = true,
		ExportAdvancedRenderInfoVRayRT = true,
		ExportAdvancedRenderInfoKrakatoa = true,
		ExportAdvancedRenderInfoAmaretto = false, --not used anymore, left for compatibility
		ExportAdvancedRenderInfoArnold = true,
		ExportAdvancedRenderInfoFinalRender = true,
		ExportAdvancedRenderInfoMaxwell = true,
		ExportAdvancedRenderInfoQuicksilver = true,
		ExportAdvancedRenderInfoIRay = true,
		ExportAdvancedRenderInfoCorona = true,
		ExportAdvancedRenderInfoArt = true,
		ExportAdvancedRenderInfoRedshift = true,
		ExportAdvancedRenderInfoOctane = true,
		
		DumpFileProperties = false,
		MissingFiles = #(),
		WarnAboutMissingExternalFiles = true,
		
		OverrideLanguage = false,
		Language = 0,
		LanguageArray = #("English", "French", "German", "Japanese", "Korean", "Simplified Chinese"),
		LanguageCodeArray = #("ENU", "FRA", "DEU", "JPN", "KOR", "CHS" ),
		
		ScheduledType = #none,  --None/Once/Daily
		ScheduledDays = 1,
		ScheduledStartDateTime = "", --dd/MM/yyyy HH:mm
		
		TaskTimeoutEnabled = false,
		TaskTimeout = 0,
		AutoTaskTimeout = false,
		RestartMax = false,
		
		IsBakeJob = false,
		BakeJobOneObjectPerTask = true,
		
		ExtraInfo0 = "",
		ExtraInfo1 = "",
		ExtraInfo2 = "",
		ExtraInfo3 = "",
		ExtraInfo4 = "",
		ExtraInfo5 = "",
		ExtraInfo6 = "",
		ExtraInfo7 = "",
		ExtraInfo8 = "",
		ExtraInfo9 = "",
		ExtraInfoKeyValues = #(),	--populate this array from your own scripts with key/value sub-arrays in the form #( #(KeyName, KeyValue), #(KeyName, KeyValue) ... #(KeyName, KeyValue)) The indexing will be handled automatically

		EnvironmentKeyValues = #(),	--populate this array from your own scripts with kay/value sub-arrays in the form #( #(KeyName, KeyValue), #(KeyName, KeyValue) ... #(KeyName, KeyValue)) The indexing will be handled automatically
		IncludeEnvironment = false,
		UseJobEnvironmentOnly = false,

		ProjectManagement = "Shotgun",

		SGDraftTemplate = "",
		SGVersion= "",
		SGDescription = "",
		SGTask = "", 
		SGEntity = "",
		SGUser = "",
		SGProject = "",
		SGUpdate = false,
		SGDisplayInfo = #(),
		SGJobSettings = #(),
		SGCreateMovie = false,
		SGCreateFilmStrip = false,

		FTAsset = "",
		FTDescription = "",
		FTTask = "",
		FTUser = "",
		FTProject = "",
		FTUpdate = false,
		FTDisplayInfo = #(),
		FTJobSettings = #(),
		
		NIMUser = "",
		NIMRender = "",
		NIMDescription = "",
		NIMUpdate = false,
		NIMDisplayInfo = #(),
		NIMJobSettings = #(),
		
		DraftQuick = false,
		DraftFormats = #(),
		DraftFormat = "",
		DraftResolutions = #(),
		DraftResolution = "",
		DraftCodec = "",
		DraftFrameRates = #(),
		DraftFrameRate = "24",
		DraftQuality = 85,
		DraftRestrictions = #(),
		DraftTemplate = "",
		DraftSubmitJob = false,
		DraftShotgunUpload = true,
		DraftUser = "",
		DraftEntity = "",
		DraftVersion = "",
		DraftExtraArgs = "",

		DeleteEmptyStateSets = false,
		StateSetsSubmit = false,
		StateSetsList = #{},
		StateSetsNamesList = #(),
		StateSetToRender = 0,
		StateSetName = "",
		StateSetInfo = "",
		StateSetRenameOutput = false,
		
		StereoCameraMode = #left, -- #all = if active view is any stereo sub-camera, submit #left, #right and #center jobs; #leftright = if the view is any stereo sub-camera, submit #left and #rgith; #left = submit left eye only; #right = submit right eye only, #center = submit center camera only
		LeftEyeTag = "LE",
		RightEyeTag = "RE",
		CenterEyeTag = "CE",
		StereoCameraPriorityOrder = #none, --#lrc, #rlc, #clr, #crl, #lcr, #rcl
		
		OverrideJobFailureDetection = false, 	-- If true, the job will ignore the global Job Failure Detection settings and instead use its own (default = false).
		FailureDetectionJobErrors = 0,  		-- If OverrideJobFailureDetection is true, this sets the number of errors before the job fails. If set to 0, job failure detection will be disabled.
		OverrideTaskFailureDetection = false,  	-- If true, the job will ignore the global Task Failure Detection settings and instead use its own (default = false).
		FailureDetectionTaskErrors = 0,  		-- If OverrideTaskFailureDetection is true, this sets the number of errors before a task for the job fails. If set to 0, task failure detection will be disabled.
		--IgnoreBadJobDetection = false,  		-- If true, Slaves will never mark the job as bad for themselves. This means that they will continue to make attempts at jobs that often report errors until the job is complete, or until it fails (default = false).
		SendJobErrorWarning = true, 			-- If the job should send warning notifications when it reaches a certain number of errors (default = false).		
		
		nonFatalErrorsCount = 0,
		FatalErrorsCount = 0,
		
		PreviewJobLabel = "PREVIEW FRAMES",
		PreviewRestJobLabel = "REST OF FRAMES",
		BatchMasterJobLabel = "BATCH MASTER",
		MAXScriptJobLabel = "MAXSCRIPT",
		
		AssetsResolved = #(),
		AssetsAutoUpdateList = true,
		AssetSyncAllFiles = false,
		AssetsPreCacheFiles = true,
		AssetsIncludeFilesInJob = true,
		
		WorkflowMode = "default",
		
		UseCustomFrameList = false,			-- for 3rd party developers, when set to true allows the CustomFrameList (see below) to define the frames to be rendered.
		CustomFrameList = #(0),				-- for 3rd party developers, when UseCustomFrameList is set to true, this array will define the frames to be rendered. If not an array or empty, the current frame will be used.
		ExtraOutputFilenames = #(),			-- for 3rd party developers, populate with filenames to add to the job's right click menu in the Monitor. Will be indexed automatically as OutputFilename#
		ExtraJobInfoKeys = #(),				-- for 3rd party developers, populate with #(Key, Value) sub-arrays to write custom values to the Job Info file.
		ExtraPluginInfoKeys = #(),			-- for 3rd party developers, populate with #(Key, Value) sub-arrays to write custom values to the Plugin Info file.
		
		PipelineToolStatus = "No Pipeline Tools Enabled"
		
	)
	::SMTDSettingsFactory = SMTDSettingsStructure()
	::SMTDSettingsDefaults = SMTDSettingsStructure()
	::SMTDSettings = SMTDSettingsStructure()
	
	struct SMTDDictionariesStructure
	(
		DraftFormatsDict = dotNetObject "System.Collections.Hashtable",
		DraftResolutionsDict = dotNetObject "System.Collections.Hashtable",
		DraftCodecsDict = dotNetObject "System.Collections.Hashtable",
		DraftRestrictionsDict = dotNetObject "System.Collections.Hashtable"
	)
	::SMTDDictionaries = SMTDDictionariesStructure()
	
	--Increase heap size to 64 MB just in case.
	if heapSize < 67108864 do heapSize = 67108864
	
	struct SMTDFunctions
	(
		--Returns the name of the plugin to use
		fn getPluginToUse =
		(
			if (SMTDSettings.DBR and SMTDSettings.DBRUse3dsCmd) then
				"3dsCmd"
			else
				"3dsmax"
		),
		
		fn getMaxVersion =
		(
			if( ((maxVersion())[1]/1000 as integer) > 9 ) then
				((((maxVersion())[1]/1000 as integer) + 1998) as string)
			else
				(((maxVersion())[1]/1000 as integer) as string)
		),
		
		fn getMaxVersionAsInteger =
		(
			if( ((maxVersion())[1]/1000 as integer) > 9 ) then
				(((maxVersion())[1]/1000 as integer) + 1998)
			else
				((maxVersion())[1]/1000 as integer)
		),
		
		fn IsSettingSticky theCategory theKey =
		( 
			local theStickyFile = getDir #userScripts + "\\SubmitMaxToDeadline_StickySettings.ini"  
			local theLocalStickyFile = SMTDPaths.SettingsDir + "\\SubmitMaxToDeadline_StickySettings.ini"  
			local isSticky = true --If INI key is not set, we assume the setting is sticky
			local theValue = toLower (getINISetting theStickyFile theCategory theKey) 
			--if there is such a global entry, see whether it is false or not. 
			if theValue != "" do isSticky = theValue != "false"
			--if there is such a local entry, see whether it is false or not
			local theValue = toLower (getINISetting theLocalStickyFile theCategory theKey)
			if theValue != "" do isSticky = theValue != "false"
			isSticky 
		),
		
		fn getGlobalDefault theCategory theKey theDefault executeIt:true =
		(
			local theDefaultFile = getDir #userScripts + "\\SubmitMaxToDeadline_Defaults.ini"  --this is the global defaults file.
			local theKeys = getIniSetting theDefaultFile theCategory  --get all keys from the category in the file
			local result = theDefault --initialize the result to the factory default
			if findItem theKeys theKey > 0 do --if a global default exists, 
			(
				local theResult = getIniSetting theDefaultFile theCategory theKey  --get the value from the file
				if executeIt then --if necessary, convert to MAXScript value
				(
					result = try(execute theResult)catch(OK)  
					if result == OK do result = theDefault 	 --if conversion failed, use the factory default.	
				)
				else
					result = theResult --if no conversion necessary, use the result as is - it will remain a string
			)
			result  --return the global default
		),
		
		fn getStoreInSceneExclusionList =
		(
			global SMTDSaveInSceneExclusionList = #(#pools,#groups,#maximumpriority,#tasklimit,#username,#Delimiter,#OutputFilenamePattern,#OutputFilenameTokenDelimiter,#theIniFiles,#theIniFilenames,#RepositoryList,#RepositoryListActual, #JobsArray, #FullJobsArray, #PreviousJobsArray, #DependencyJobItems, #SubmitSceneGlobalBasePath)
			local theFile = getDir #userScripts + "\\SubmitMaxToDeadline_ExcludeFromSceneStorage.ini"  --this is the global exclusion file.
			local theCats = getIniSetting theFile
			for c in theCats do 
			(
				local theKeys = getIniSetting theFile c
				for k in theKeys where (execute (getIniSetting theFile c k)) == True  do append ::SMTDSaveInSceneExclusionList (k as name)
			)
		),
		
		fn getStickyCaption theCategory theKey theCaption =
		(
			if not (SMTDFunctions.IsSettingSticky theCategory theKey) then
			(
				theCaption
				theCaption[theCaption.count] = "*"
			)
			theCaption
		),
		
		fn getStickyTooltipText theCategory theKey isList: mapList: =
		(
			if (SMTDFunctions.IsSettingSticky theCategory theKey) then
			(
				local theValue = getIniSetting SMTDPaths.InIFile theCategory theKey --try(getProperty SMTDSettingsDefaults theKey)catch("") --()
				if isList != unsupplied do 
				(
					if mapList == unsupplied then
					(
						theValue = try(execute theValue)catch("???")
						if isKindOf theValue Number and theValue > 0 and theValue < isList.count do theValue = isList[theValue]
					)
					else
					(
						local theIndex = findItem mapList (toLower theValue)
						if theIndex > 0 do theValue = theValue as string + " : '" + isList[theIndex] + "'"
					)
				)
				if theValue == "" then
					"\n\nThis property is currently STICKY.\nNo user value has been recorded yet."
				else
					"\n\nThis property is currently STICKY.\nThe last recorded value of ["+ theValue as string +"] will be used for NEW Scenes."
			)
			else
			(
				local theValue = try(GetProperty SMTDSettingsDefaults theKey)catch("")
				if isList != unsupplied do 
				(
					if mapList == unsupplied then
					(					
						theValue = try(execute theValue)catch("???")
						if isKindOf theValue Number and theValue > 0 and theValue < isList.count do theValue = isList[theValue]
					)
					else
					(
						local theIndex = findItem mapList (toLower (theValue as string))
						if theIndex > 0 do theValue = theValue as string + " : '" + isList[theIndex] + "'"
					)
				)
				"\n\nThis property is currently NOT STICKY.\nA default value of ["+ theValue as string +"] will be used for NEW Scenes."
			)
		),
		
		--Returns the value of the specified category and key, or the default value if the key is empty.
		--If the executeIt optional keyword is passed as false, the result will be returned as string
		--If true or not specified, the value will be converted to a MAXScript value via execute() call, for example for Integers, Booleans etc.
		fn getINI theCategory theKey theDefault executeIt:true useStickyFile:true isSticky:true =
		(
			local theDefault = SMTDFunctions.getGlobalDefault theCategory theKey theDefault executeIt:executeIt --set the default to global if available
			local result = theDefault
			local isSticky = isSticky
			if useStickyFile do isSticky = SMTDFunctions.IsSettingSticky theCategory theKey isSticky:isSticky
			if isSticky do --to disable stickyness, enter "false" for the given key. 
			(
				if executeIt then
				(
					result = try(execute (getIniSetting SMTDPaths.InIFile theCategory theKey))catch(OK) --if sticky, try to load from local file.
					if result == OK do result = theDefault --if the value was not in the local file, assume default.
				)
				else 
				(
					result = (getIniSetting SMTDPaths.IniFile theCategory theKey) --if sticky, load from local file without executing.
				)	
			)	
			result
		),

		
		fn getSettingsList =
		(
			#(
				--  1:INI Category				 2:Prop.Name								3:Struct Prop.Name							4:exec	5:UI Section											6: UI Name or Description		7:use sticky file 8:is sticky
				#("Workflows",					"WorkflowMode",								#WorkflowMode,								false,	"Workflows",											"Workflow Mode"),
				#("JobSettings",				"JobName", 									#JobName, 									false, 	"Job Description", 										"Job Name" ),
				#("JobSettings",				"Comment", 									#Comment, 									false, 	"Job Description", 										"Comment" ),
				#("JobSettings",				"Department", 								#Department, 								false, 	"Job Description", 										"Department" ),
				
				#("JobSettings",				"PoolName", 								#PoolName, 									false, 	"Pool, Group and Priority",								"Pool" ),
				#("JobSettings",				"Pool2Name", 								#Pool2Name, 								false, 	"Pool, Group and Priority",								"Secondary Pool" ),
					
				#("JobSettings",				"Group", 									#Group,		 								false, 	"Pool, Group and Priority",								"Group" ),
				#("JobSettings",				"Priority", 								#Priority, 									true, 	"Pool, Group and Priority", 							"Priority" ),
				
				#("UserOptions",				"SubmitSceneMode", 							#SubmitSceneMode, 							false, 	"Scene File Submission Options",						"Scene File Submission Mode" ),
				#("UserOptions",				"SubmitSceneBasePath", 						#SubmitSceneBasePath,		 				false, 	"Scene File Submission Options", 						"Scene File Base Path" ),
				#("UserOptions",				"SubmitSceneGlobalBasePath", 				#SubmitSceneGlobalBasePath, 				false, 	"Scene File Submission Options", 						"Scene File Global Base Path", false, false ),

				#("UserOptions",				"PerformSanityCheck", 						#PerformSanityCheck, 						true, 	"Sanity Check",											"Run Sanity Check Automatically Before Submission" ),
				
				#("JobSettings",				"LimitEnabled", 							#LimitEnabled, 								true, 	"Job Options",											"Limit Number Of Machines Rendering Concurrently" ),
				#("JobSettings",				"MachineLimit", 							#MachineLimit, 								true, 	"Job Options",											"Machines" ),
				#("JobSettings",				"RenderOutOfOrder", 						#RenderOutOfOrder, 							true, 	"Job Options",											"Render Out Of Order" ),
				#("JobSettings",				"OutOfOrderMethod",							#OutOfOrderMethod, 							false, 	"Job Options",											"Out Of Order Method" ),
				#("JobSettings",				"OutOfOrderStep", 							#OutOfOrderStep,							true, 	"Job Options",											"Nth Frame" ),
				
				#("JobSettings",				"ChunkSize", 								#ChunkSize, 								true, 	"Job Options",											"Chunk Size" ),
				#("JobSettings",				"RenderFramesPreviewJob", 					#RenderFramesPreviewJob, 					true, 	"Job Options",											"Render Frames Preview Job" ),
				#("JobSettings",				"PreviewJobFrameCount", 					#PreviewJobFrameCount, 						true, 	"Job Options",											"Preview Job Frame Count" ),
				#("JobSettings",				"PreviewJobPriorityOffset", 				#PreviewJobPriorityOffset, 					true, 	"Job Options",											"Preview Job Priority Offset" ),
				#("JobSettings",				"PreviewJobSecondJobDependentOnFirst",	 	#PreviewJobSecondJobDependentOnFirst,		true, 	"Job Options",											"Preview Job Second Job Dependent On First" ),
				#("JobSettings",				"PreviewJobSecondJobSuspended", 			#PreviewJobSecondJobSuspended, 				true, 	"Job Options",											"Preview Job Second Job Suspended" ),
								
				#("JobSettings",				"SequentialJob", 							#SequentialJob, 							true, 	"Job Options",											"Enforce Sequential Rendering" ),
				#("JobSettings",				"SubmitVisibleObjectsOnly", 				#SubmitVisibleObjectsOnly, 					true, 	"Job Options",											"Submit Visible Objects Only" ),

				#("JobSettings",				"MaxTasksPerSlave", 						#MaxTasksPerSlave, 							true, 	"Job Options",											"Concurrent Tasks" ),
				#("JobSettings",				"LimitTasksToNumberOfCpus", 				#LimitTasksToNumberOfCpus, 					true, 	"Job Options",											"Limit Tasks To Number Of Cpus" ),
	
				#("JobSettings",				"OnComplete", 								#OnComplete, 								false, 	"Job Options",											"On Job Completion" ),
				#("JobSettings",				"SubmitAsSuspended", 						#SubmitAsSuspended, 						true, 	"Job Options",											"Submit As Suspended" ),
					
				#("JobSettings",				"TaskTimeoutEnabled",						#TaskTimeoutEnabled,						true, 	"Job Options",											"Task Timeout On" ),
				#("JobSettings",				"TaskTimeout", 								#TaskTimeout,								true, 	"Job Options",											"Task Timeout In Seconds" ),
				#("JobSettings",				"AutoTaskTimeout", 							#AutoTaskTimeout,							true, 	"Job Options",											"Auto Task Timeout On" ),
				#("JobSettings",				"RestartMax", 								#RestartMax, 								true, 	"Job Options",											"Restart 3ds Max Between Tasks" ),
				#("JobSettings",				"MaxVersionToForce", 						#MaxVersionToForce, 						false, 	"Job Options",											"Force 3ds Max Build" ),
				#("JobSettings",				"StereoCameraMode", 						#StereoCameraMode, 							false, 	"Job Options",											"Stereo Camera Job Submission Mode" ),
				#("JobSettings",				"StereoCameraPriorityOrder", 				#StereoCameraPriorityOrder, 				false, 	"Job Options",											"Stereo Camera Job Priority Mode" ),
				
				
				
				#("JobSettings",				"LeftEyeTag", 								#LeftEyeTag, 								false, 	"Job Options",											"Stereo Camera Left Eye Tag", false, false ),
				#("JobSettings",				"RightEyeTag", 								#RightEyeTag, 								false, 	"Job Options",											"Stereo Camera Right Eye Tag", false, false ),
				#("JobSettings",				"CenterEyeTag", 							#CenterEyeTag, 								false, 	"Job Options",											"Stereo Camera Center Eye Tag", false, false ),
					
					
				#("JobSettings",				"OverrideJobFailureDetection",				#OverrideJobFailureDetection, 				true, 	"Job Failure Detection",								"Override Job Error Limit" ),
				#("JobSettings",				"FailureDetectionJobErrors", 				#FailureDetectionJobErrors, 				true, 	"Job Failure Detection",								"Job Error Limit" ),
				#("JobSettings",				"OverrideTaskFailureDetection",				#OverrideTaskFailureDetection,				true, 	"Job Failure Detection",								"Override Task Error Limit" ),
				#("JobSettings",				"FailureDetectionTaskErrors", 				#FailureDetectionTaskErrors, 				true, 	"Job Failure Detection",								"Task Error Limit" ),
				#("JobSettings",				"SendJobErrorWarning", 						#SendJobErrorWarning, 						true, 	"Job Failure Detection",								"Send Job Error Warning" ),

				#("RemoteSubmission",			"DropSubmission", 							#DropSubmission, 							true, 	"Remote Submission",									"Drop Submission" ),
				#("RemoteSubmission",			"BgSubmission", 							#BgSubmission, 								true, 	"Remote Submission",									"Background Submission" ),
				#("RemoteSubmission",			"TransferPool", 							#TransferPool, 								false, 	"Remote Submission",									"Transfer Pool" ),
				#("RemoteSubmission",			"TransferGroup", 							#TransferGroup, 							false, 	"Remote Submission",									"Transfer Group" ),
				#("RemoteSubmission",			"TransferPriority", 						#TransferPriority, 							true, 	"Remote Submission",									"Transfer Priority" ),
				#("RemoteSubmission",			"TransferDeleteOnComplete",		 			#TransferDeleteOnComplete, 					true, 	"Remote Submission",									"Delete On Complete" ),
				#("RemoteSubmission",			"TransferJobAsSuspended", 					#TransferJobAsSuspended, 					true, 	"Remote Submission",									"Transfer Job As Suspended" ),
				#("RemoteSubmission",			"TransferCompressed", 						#TransferCompressed, 						true, 	"Remote Submission",									"Transfer Compressed" ),

				#("RenderingOptions",			"UseAltPluginIni", 							#UseAltPluginIni, 							true, 	"3ds Max Rendering",									"Use Alternate Plugin.ini" ),
				#("RenderingOptions",			"AutoSuggest", 								#AutoSuggestIni, 							true, 	"3ds Max Rendering",									"Auto-Detect ini For Current Renderer" ),
				#("RenderingOptions",			"AltPluginIni", 							#AltPluginIni, 								false, 	"3ds Max Rendering",									"Alternate Plugin.ini" ),

				#("RenderingOptions",			"EnableFailOnBlackFrames", 					#EnableFailOnBlackFrames,					true, 	"3ds Max Rendering",									"Fail On Black Frames" ),
				#("RenderingOptions",			"BlackPixelPercentage", 					#BlackPixelPercentage,						true, 	"3ds Max Rendering",									"Black Pixel Percentage" ),
				#("RenderingOptions",			"BlackPixelThreshold", 						#BlackPixelThreshold,						true, 	"3ds Max Rendering",									"Black Pixel Threshold" ),
				#("RenderingOptions",			"BlackFramesCheckRenderElements",			#BlackFramesCheckRenderElements,			true,	"3ds Max Rendering",									"Fail On Black Frames" ),
				
				#("RenderingOptions",			"OverrideBitmapPager", 						#OverrideBitmapPager,						true, 	"3ds Max Rendering",									"Override Bitmap Pager Setting While Rendering" ),
				#("RenderingOptions",			"BitmapPager", 								#BitmapPager,								true, 	"3ds Max Rendering",									"Bitmap Pager Enabled" ),
				
				#("RenderingOptions",			"GammaCorrection", 							#GammaCorrection,							true, 	"3ds Max Rendering",									"Enable Gamma Correction" ),
				#("RenderingOptions",			"GammaInput", 								#GammaInput,								true, 	"3ds Max Rendering",									"Gamma Input" ),
				#("RenderingOptions",			"GammaOutput", 								#GammaOutput,								true, 	"3ds Max Rendering",									"Gamma Output" ),
				
				#("RenderingOptions",			"SubmitExternalFilesMode", 					#SubmitExternalFilesMode,					true, 	"3ds Max Rendering",									"Submit External Files Mode" ),
				#("RenderingOptions",			"MergeXRefsOnSubmission", 					#MergeXRefsOnSubmission,					true, 	"3ds Max Rendering",									"Merge Object XRefs" ),
				#("RenderingOptions",			"MergeSceneXRefsOnSubmission", 				#MergeSceneXRefsOnSubmission,				true, 	"3ds Max Rendering",									"Merge Scene XRefs On Submission" ),
				#("RenderingOptions",			"ForceWorkstationMode", 					#ForceWorkstationMode,						true, 	"3ds Max Rendering",									"Force Workstation Mode" ),
				#("RenderingOptions",			"UseSilentMode", 							#UseSilentMode,								true, 	"3ds Max Rendering",									"Enable Silent Mode" ),
				#("RenderingOptions",			"IgnoreMissingExternalFiles", 				#IgnoreMissingExternalFiles,				true, 	"3ds Max Rendering",									"Ignore Missing External File Errors" ),
				#("RenderingOptions",			"IgnoreMissingUVWs", 						#IgnoreMissingUVWs,							true, 	"3ds Max Rendering",									"Ignore Missing UVW Errors" ),
				#("RenderingOptions",			"IgnoreMissingXREFs", 						#IgnoreMissingXREFs,						true, 	"3ds Max Rendering",									"Ignore Missing XREF Errors" ),
				#("RenderingOptions",			"IgnoreMissingDLLs", 						#IgnoreMissingDLLs,							true, 	"3ds Max Rendering",									"Ignore Missing DLL Errors" ),

				#("RenderingOptions",			"IgnoreRenderElements", 					#IgnoreRenderElements,						true, 	"3ds Max Rendering",									"Do Not Save Render Element Files" ),
				#("RenderingOptions",			"ShowFrameBuffer", 							#ShowFrameBuffer,							true, 	"3ds Max Rendering",									"Show Virtual Frame Buffer" ),
				#("RenderingOptions",			"ShowRendererFrameBufferOverride",			#ShowRendererFrameBufferOverride,			true,	"3ds Max Rendering",									"Override Renderer Frame Buffer Visibility" ),
				#("RenderingOptions",			"ShowRendererFrameBuffer",					#ShowRendererFrameBuffer,					true,	"3ds Max Rendering",									"Show Renderer Frame Buffer" ),

				#("RenderingOptions",			"DisableProgressUpdateTimeout", 			#DisableProgressUpdateTimeout,				true, 	"3ds Max Rendering",									"Disable Progress Update Timeout" ),
				#("RenderingOptions",			"SkipRender",						 		#SkipRender,								true, 	"3ds Max Rendering",									"Disable Frame Rendering" ),
				#("RenderingOptions",			"DisableMultipass", 						#DisableMultipass,							true, 	"3ds Max Rendering",									"Disable Multipass" ),

				#("RenderingOptions",			"ForceRestartRenderer", 					#none,										true, 	"Defaults INI File Only",								"Force Restart for mental ray, Brazil and V-Ray", false, false ),
				#("RenderingOptions",			"RestartRenderer", 							#RestartRenderer,							true, 	"3ds Max Rendering",									"Restart Renderer" ),

				#("RenderingOptions",			"JobIsInterruptible", 						#JobIsInterruptible,						true, 	"3ds Max Rendering",									"Job Is Interruptible" ),
				#("RenderingOptions",			"UseCustomShader", 							#UseCustomShader,							true, 	"3ds Max Rendering",									"Apply Custom Material To Scene" ),
				#("RenderingOptions",			"CustomShaderMode", 						#CustomShaderMode,							true, 	"3ds Max Rendering",									"Custom Material Mode" ),

				#("RenderingOptions",			"RemovePadding", 							#RemovePadding,								true, 	"3ds Max Pathing Options",								"Remove Filename Padding" ),
				#("RenderingOptions",			"StrictOutput", 							#StrictOutput,								true, 	"3ds Max Pathing Options",								"Force Strict Output Naming" ),
				#("RenderingOptions",			"Delimiter",								#Delimiter,									false,	"3ds Max Pathing Options",								"Filename Delimiter Symbol (not exposed to UI)", false, false ), --cannot ever be sticky, even if Repo Sticky INI file says it is, since we have no UI. Uses either factory default . (Period), or a global value from Repo Defaults INI. Taken As String.
				#("RenderingOptions",			"OutputFilenamePattern",					#OutputFilenamePattern,						false,	"3ds Max Pathing Options",								"Frame Number Delimiter Symbol (not exposed to UI)", false, false ), --cannot ever be sticky, even if Repo Sticky INI file says it is, since we have no UI. Uses either factory default, or a global value from Repo Defaults INI. Taken As String.
				#("RenderingOptions",			"OutputFilenameTokenDelimiter",				#OutputFilenameTokenDelimiter,				false,	"3ds Max Pathing Options",								"Token Delimiter Symbol (not exposed to UI)", false, false ), --cannot ever be sticky, even if Repo Sticky INI file says it is, since we have no UI. Uses either factory default _ (Underscore), or a global value from Repo Defaults INI. Taken As String.

				#("RenderingOptions",			"PurifyFilenames",							#PurifyFilenames,							true,	"3ds Max Pathing Options",								"Purify Filenames" ), --false, false ), 
				#("RenderingOptions",			"PurifyCharacterCodes",						#PurifyCharacterCodes,						true,	"3ds Max Pathing Options",								"Purify Characters ASCII List (not exposed to UI)", false, false ),
				#("RenderingOptions",			"ForceLowerCaseFilenames", 					#ForceLowerCaseFilenames,					true, 	"3ds Max Pathing Options",								"Force Lower-Case Filenames" ),
				#("RenderingOptions",			"RenderElementsUpdatePaths", 				#RenderElementsUpdatePaths,					true, 	"3ds Max Pathing Options",								"Auto-Update Render Elements' Paths" ),
				#("RenderingOptions",			"RenderElementsUpdateFilenames",			#RenderElementsUpdateFilenames,				true, 	"3ds Max Pathing Options",								"Auto-Update Render Elements' Filenames" ),
				#("RenderingOptions",			"RenderElementsIncludeNameInPath",			#RenderElementsIncludeNameInPath,			true, 	"3ds Max Pathing Options",								"Include RE Name In Paths" ),
				#("RenderingOptions",			"RenderElementsIncludeTypeInPath",			#RenderElementsIncludeTypeInPath,			true, 	"3ds Max Pathing Options",								"Include RE Type In Paths" ),
				#("RenderingOptions",			"RenderElementsIncludeNameInFileName",		#RenderElementsIncludeNameInFileName,		true, 	"3ds Max Pathing Options",								"Include RE Name In FileNames" ),
				#("RenderingOptions",			"RenderElementsIncludeTypeInFileName",		#RenderElementsIncludeTypeInFileName,		true, 	"3ds Max Pathing Options",								"Include RE Type In Filenames" ),
				#("RenderingOptions",			"RenderElementsPermanentChanges",			#RenderElementsPermanentChanges,			true, 	"3ds Max Pathing Options",								"Permanent Render Element Path Changes" ),
				#("RenderingOptions",			"RenderElementNamesPermanentChanges",		#RenderElementNamesPermanentChanges,		true, 	"3ds Max Pathing Options",								"Permanent Render Element Name Changes" ),
				
				#("RenderingOptions",			"RebuildRenderElements", 					#RebuildRenderElements,						true, 	"3ds Max Pathing Options",								"Rebuild Render Elements" ),
				#("RenderingOptions",			"IncludeLocalPaths", 						#IncludeLocalPaths,							true, 	"3ds Max Pathing Options",								"Include Local Paths With Job" ),

				#("RenderingOptions",			"UsePathConfigFile", 						#UsePathConfigFile,							true, 	"3ds Max Pathing Options",								"Use Alternate Paths File" ),
				#("RenderingOptions",			"MergePathConfigFile", 						#MergePathConfigFile,						true, 	"3ds Max Pathing Options",								"Merge Paths File" ),
				#("RenderingOptions",			"PathConfigFile", 							#PathConfigFile,							false, 	"3ds Max Pathing Options",								"Paths Configuration File" ),

				#("RenderingOptions",			"OutputFilenameUserPattern", 				#OutputFilenameUserPattern,					false, 	"3ds Max Pathing Options",								"Override Output Filename By Global Pattern", false, false ),
				#("RenderingOptions",			"ReplaceOutputFilenameWithUserPattern",		#ReplaceOutputFilenameWithUserPattern,		false,	"3ds Max Pathing Options", 								"Output Filename Global Pattern", false, false ), --this is never sticky, set to true if pattern exists, can be overridden temporarily for current session!
			
				#("RenderingOptions",			"ImsqOutputPath", 							#ImsqOutputPath,							false, 	"Render Output and Autodesk ME Image Sequence (IMSQ) Creation",	"Image Sequence Filename" ),
				#("RenderingOptions",			"CreateImsqFile", 							#CreateImsqFile,							true, 	"Render Output and Autodesk ME Image Sequence (IMSQ) Creation",	"Create Image Sequence (IMSQ) File" ),
				#("RenderingOptions",			"CopyImsqFile", 							#CopyImsqFile,								true, 	"Render Output and Autodesk ME Image Sequence (IMSQ) Creation",	"Use Alternate Paths File" ),

				#("StateSets",					"StateSetsSubmit", 							#StateSetsSubmit,							true, 	"State Sets",											"Submit Checked State Sets" ),
				#("StateSets",					"StateSetRenameOutput", 					#StateSetRenameOutput,						true, 	"State Sets",											"Add State Set Name to Output Filename" ),
				#("StateSets",					"StateSetsNamesList", 						#StateSetsNamesList,						true, 	"State Sets",											"State Set Names To Submit" ),
						
				#("Scripts",					"RunPreJobScript", 							#RunPreJobScript,							true, 	"Run Python Scripts",									"Run Pre-Job Script" ),
				#("Scripts",					"PreJobScriptFile", 						#PreJobScriptFile,							false, 	"Run Python Scripts",									"Pre-Job Script File" ),
				#("Scripts",					"RunPostJobScript", 						#RunPostJobScript,							true, 	"Run Python Scripts",									"Run Post-Job Script" ),
				#("Scripts",					"PostJobScriptFile", 						#PostJobScriptFile,							false, 	"Run Python Scripts",									"Post-Job Script File" ),
				#("Scripts",					"RunPreTaskScript", 						#RunPreTaskScript,							true, 	"Run Python Scripts",									"Run Pre-Task Script" ),
				#("Scripts",					"PreTaskScriptFile", 						#PreTaskScriptFile,							false, 	"Run Python Scripts",									"Pre-Task Script File" ),
				#("Scripts",					"RunPostTaskScript", 						#RunPostTaskScript,							true, 	"Run Python Scripts",									"Run Post-Task Script" ),
				#("Scripts",					"PostTaskScriptFile", 						#PostTaskScriptFile,						false, 	"Run Python Scripts",									"Post-Task Script File" ),
			
				#("Scripts",					"RunPreLoadScript", 						#RunPreLoadScript,							true, 	"Run MAXScript Scripts",								"Run Pre-Load Script" ),
				#("Scripts",					"PreLoadScriptFile", 						#PreLoadScriptFile,							false, 	"Run MAXScript Scripts",								"Pre-Load Script File" ),
				#("Scripts",					"RunPostLoadScript", 						#RunPostLoadScript,							true, 	"Run MAXScript Scripts",								"Run Post-Load Script" ),
				#("Scripts",					"PostLoadScriptFile", 						#PostLoadScriptFile,						false, 	"Run MAXScript Scripts",								"Post-Load Script File" ),
				#("Scripts",					"RunPreFrameScript", 						#RunPreFrameScript,							true, 	"Run MAXScript Scripts",								"Run Pre-Frame Script" ),
				#("Scripts",					"PreFrameScriptFile", 						#PreFrameScriptFile,						false, 	"Run MAXScript Scripts",								"Pre-Frame Script File" ),
				#("Scripts",					"RunPostFrameScript", 						#RunPostFrameScript,						true, 	"Run MAXScript Scripts",								"Run Post-Load Script" ),
				#("Scripts",					"PostFrameScriptFile", 						#PostFrameScriptFile,						false, 	"Run MAXScript Scripts",								"Post-Load Script File" ),
			
				#("UserOptions",				"LocalRendering", 							#LocalRendering,							true, 	"User Options",											"Enable Local Rendering" ),
				#("UserOptions",				"OneCpuPerTask", 							#OneCpuPerTask,								true, 	"User Options",											"One CPU Per Task" ), --deprecated
				#("UserOptions",				"Render Threads", 							#RenderThreads,								true, 	"User Options",											"Render Threads Per Task" ),
				#("UserOptions",				"AutomaticallyUpdateJobName", 				#AutomaticallyUpdateJobName,				true, 	"User Options",											"Automatically Update Job Name" ),
				#("UserOptions",				"OverrideLowPriorityThread", 				#OverrideLowPriorityThread,					true, 	"User Options",											"Override Renderer's Low Priority Thread Option (Brazil r/s, V-Ray)" ),
				#("UserOptions",				"ClearMaterialEditorOnSubmission", 			#ClearMaterialEditorOnSubmission,			true, 	"User Options",											"Clear Material Editor In The Submitted File" ),
				#("UserOptions",				"UnlockMEditRenderer", 						#UnlockMEditRenderer,						true, 	"User Options",											"Unlock Material Editor Renderer" ),
				#("UserOptions",				"DeleteEmptyStateSets",						#DeleteEmptyStateSets,						true,	"User Options",											"Delete Empty State Sets In The Submitted File"),
				#("UserOptions",				"DumpFileProperties",						#DumpFileProperties,						true,	"User Options",											"Dump Scene File Properties to Job Log Report"),
				#("UserOptions",				"CloseAfterSubmission", 					#CloseAfterSubmission, 						true, 	"User Options",											"Close After Submission" ),
				
				#("UserOptions",				"WarnAboutMissingExternalFiles", 			#WarnAboutMissingExternalFiles,				true, 	"User Options",											"Warn About Missing External Files On Submission" ),

				#("UserOptions",				"ExternalFilesWarningOn", 					#ExternalFilesWarningOn,					true, 	"3ds Max Rendering",									"Warn About Submit External Files" ),
				#("UserOptions",				"ExternalFilesWarningCount", 				#ExternalFilesWarningCount,					true, 	"3ds Max Rendering",									"External Files Count Warning Threshold" ),
				#("UserOptions",				"ExternalFilesWarningMB", 					#ExternalFilesWarningMB,					true, 	"3ds Max Rendering",									"External Files MB Warning Threshold" ),

				#("UserOptions",				"OverrideLanguage",							#OverrideLanguage,							true,	"User Options",											"Override 3ds Max Language" ),
				
				#("UserOptions",				"ExportAdvancedRenderOutputFiles",			#ExportAdvancedRenderOutputFiles,			true,	"Export Renderer Specific Advanced Settings",			"Export Renderer Caching Output Files" ),
				#("UserOptions",				"ExportAdvancedRenderInfoScanline",			#ExportAdvancedRenderInfoScanline,			true,	"Export Renderer Specific Advanced Settings",			"3ds Max Scanline" ),
				#("UserOptions",				"ExportAdvancedRenderInfoQuicksilver",		#ExportAdvancedRenderInfoQuicksilver,		true,	"Export Renderer Specific Advanced Settings",			"3ds Max Quicksilver" ),
				#("UserOptions",				"ExportAdvancedRenderInfoIRay",				#ExportAdvancedRenderInfoIRay,				true,	"Export Renderer Specific Advanced Settings",			"NVIDIA Iray" ),
				
				#("UserOptions",				"ExportAdvancedRenderInfoVRay",				#ExportAdvancedRenderInfoVRay,				true,	"Export Renderer Specific Advanced Settings",			"Chaos Group V-Ray" ),
				#("UserOptions",				"ExportAdvancedRenderInfoVRayRT",			#ExportAdvancedRenderInfoVRayRT,			true,	"Export Renderer Specific Advanced Settings",			"Chaos Group V-Ray RT" ),
				#("UserOptions",				"ExportAdvancedRenderInfoMentalRay",		#ExportAdvancedRenderInfoMentalRay,			true,	"Export Renderer Specific Advanced Settings",			"NVIDIA Mental Ray" ),
				#("UserOptions",				"ExportAdvancedRenderInfoBrazil2",			#ExportAdvancedRenderInfoBrazil2,			true,	"Export Renderer Specific Advanced Settings",			"SplutterFish Brazil r/s 2.x" ),

				#("UserOptions",				"ExportAdvancedRenderInfoKrakatoa",			#ExportAdvancedRenderInfoKrakatoa,			true,	"Export Renderer Specific Advanced Settings",			"Thinkbox Krakatoa MX" ),
				#("UserOptions",				"ExportAdvancedRenderInfoFinalRender",		#ExportAdvancedRenderInfoFinalRender,		true,	"Export Renderer Specific Advanced Settings",			"Cebas finalRender" ),
				#("UserOptions",				"ExportAdvancedRenderInfoMaxwell",			#ExportAdvancedRenderInfoMaxwell,			true,	"Export Renderer Specific Advanced Settings",			"Next Limit Maxwell" ),
				#("UserOptions",				"ExportAdvancedRenderInfoCorona",			#ExportAdvancedRenderInfoCorona,			true,	"Export Renderer Specific Advanced Settings",			"Render Legion Corona" ),
				#("UserOptions",				"ExportAdvancedRenderInfoArt",				#ExportAdvancedRenderInfoArt,				true,	"Export Renderer Specific Advanced Settings",			"Autodesk ART" ),
				#("UserOptions",				"ExportAdvancedRenderInfoRedshift",			#ExportAdvancedRenderInfoRedshift,			true,	"Export Renderer Specific Advanced Settings",			"Redshift Rendering Technologies Redshift" ),
				#("UserOptions",				"ExportAdvancedRenderInfoOctane",			#ExportAdvancedRenderInfoOctane,			true,	"Export Renderer Specific Advanced Settings",			"OTOY Octane" ),

				#("UserOptions",				"ExportAdvancedRenderInfoArnold",			#ExportAdvancedRenderInfoArnold,			true,	"Export Renderer Specific Advanced Settings",			"Solid Angle Arnold" ),
				
				#("UserOptions",				"TimeoutSubmission", 						#TimeoutSubmission,							true, 	"Submission Timeouts",									"Job Submission Timeout in seconds" ),
				#("UserOptions",				"TimeoutCollectData", 						#TimeoutCollectData,						true, 	"Submission Timeouts",									"Data Collection Timeout in seconds" ),

				#("LimitGroups",				"LimitGroups", 								#LimitGroups,								true, 	"Limits",												"Limits" ),
				#("LimitGroups",				"LimitGroupsToUse", 						#LimitGroupsToUse,							true, 	"Limits",												"Limits To Use" ),
				#("LimitGroups",				"LimitGroupAutoBrazil",						#LimitGroupAutoBrazil,						true, 	"Limits",												"Automatically set 'brazil' Limit when rendering with Brazil r/s." ),
				#("LimitGroups",				"LimitGroupAutoVRay", 						#LimitGroupAutoVRay,						true, 	"Limits",												"Automatically set 'vray' Limit when rendering with Chaos Group V-Ray." ),
				#("LimitGroups",				"LimitGroupAutoCorona",						#LimitGroupAutoCorona,						true,	"Limits",												"Automatically set 'corona' Limit when rendering with Render Legion Corona." ),
				#("LimitGroups",				"LimitGroupAutoKrakatoa",					#LimitGroupAutoKrakatoa,					true, 	"Limits",												"Automatically set 'krakatoa' Limit when rendering with Thinkbox Krakatoa MX." ),
				#("LimitGroups",				"LimitGroupAutoFinalRender",				#LimitGroupAutoFinalRender,					true, 	"Limits",												"Automatically set 'finalrender' Limit when rendering with Cebas finalRender." ),
				#("LimitGroups",				"LimitGroupAutoMaxwell", 					#LimitGroupAutoMaxwell,						true, 	"Limits",												"Automatically set 'maxwell' Limit when rendering with NextLimit Maxwell." ),
				#("LimitGroups",				"LimitGroupAutoWorkstation", 				#LimitGroupAutoWorkstation,					true, 	"Limits",												"Automatically set '3dsmaxworkstation' Limit for Workstation Mode." ),
				#("LimitGroups",				"LimitGroupAutoMaxIO", 						#LimitGroupAutoMaxIO,						true, 	"Limits",												"Automatically set 'max' Limit when rendering on AWS using 3dsmaxIO UBL licenses." ),
				#("LimitGroups",				"LimitGroupAutoRedshift", 					#LimitGroupAutoRedshift,					true, 	"Limits",												"Automatically set 'redshift' Limit when rendering with Redshift Rendering Technologies Redshift." ),
				#("LimitGroups",				"LimitGroupAutoArnold", 					#LimitGroupAutoArnold,						true, 	"Limits",												"Automatically set 'arnold' Limit when rendering with Solid Angle Arnold." ),
				#("LimitGroups",				"LimitGroupAutoIray", 						#LimitGroupAutoIray,						true, 	"Limits",												"Automatically set 'iray' Limit when rendering with NVIDIA Iray." ),
				#("LimitGroups",				"LimitGroupAutoMentalRay", 					#LimitGroupAutoMentalRay,					true, 	"Limits",												"Automatically set 'mentalray' Limit when rendering with NVIDIA Mental Ray." ),
				#("LimitGroups",				"LimitGroupAutoOctane", 					#LimitGroupAutoOctane,						true, 	"Limits",												"Automatically set 'octane' Limit when rendering with OTOY Octane." ),
				
				#("AssemblerSettings",			"AssemblerOverride",						#AssemblerOverride,							true,	"Multi-Region Rendering",								"Assembler Override" ),
				#("AssemblerSettings",			"AssemblerPoolName",						#AssemblerPoolName,							false,	"Multi-Region Rendering",								"Assembler Pool" ),
				#("AssemblerSettings",			"AssemblerPool2Name",						#AssemblerPool2Name,						false,	"Multi-Region Rendering",								"Assembler Secondary Pool" ),
				#("AssemblerSettings",			"AssemblerGroup",							#AssemblerGroup,							false,	"Multi-Region Rendering",								"Assembler Group" ),
				#("AssemblerSettings",			"AssemblerPriority",						#AssemblerPriority,							true,	"Multi-Region Rendering",								"Assembler Priority" ),

				#("MultiRegionRendering",		"RegionRenderingMode",						#RegionRenderingMode,						false,	"Multi-Region Rendering", 								"Multi-Region/Tile Rendering Mode", true, false, true),
				#("MultiRegionRendering",		"MultiRegionCopyDraftConfig", 				#MultiRegionCopyDraftConfig,				true, 	"Multi-Region Rendering",								"Copy Draft Config Files To Output Folder" ),
				#("MultiRegionRendering",		"MultiRegionBackground",					#MultiRegionBackground,						true, 	"Multi-Region Rendering",								"Assemble Over Background Mode" ),
				#("MultiRegionRendering",		"MultiRegionBackgroundImage",				#MultiRegionBackgroundImage,				false, 	"Multi-Region Rendering",								"User-Defined Background Image" ),
				#("MultiRegionRendering",		"MultiRegionFitPadding",					#MultiRegionFitPadding,						true, 	"Multi-Region Rendering",								"Fit Region Padding Percentage", false, true ),  --always sticky
				
				#("TilesRendering",				"TilesPadding", 							#TilesPadding,								true, 	"Tile Rendering",										"Pixel Padding" ),
				#("TilesRendering",				"SingleTileJobCleanup", 					#SingleTileJobCleanup,						true, 	"Tile Rendering",										"Cleanup Tiles After Assembly" ),
				#("TilesRendering",				"SingleTileJobDraftErrorOnMissing", 		#SingleTileJobDraftErrorOnMissing,			true, 	"Tile Rendering",										"Draft Assembly Job Error On Missing Tile" ),
				#("TilesRendering",				"TilesInX", 								#TilesInX,									true, 	"Tile Rendering",										"Tiles In X" ),
				#("TilesRendering",				"TilesInY", 								#TilesInY,									true, 	"Tile Rendering",										"Tiles In Y" ),
				#("TilesRendering",				"TileBlowupMode", 							#TileBlowupMode,							true, 	"Tile Rendering",										"Enable Blowup Mode" ),
				#("TilesRendering",				"SingleTileJobDependent", 					#SingleTileJobDependent,					true, 	"Tile Rendering",										"Submit Dependent Assembly Job" ),
				#("TilesRendering",				"CustomTilesPreviewWidth", 					#CustomTilesPreviewWidth,					true, 	"Tile Rendering",										"Width of the Custom Tiles Preview Image" ),
				#("TilesRendering",				"CustomTilesPreviewHeight",					#CustomTilesPreviewHeight,					true, 	"Tile Rendering",										"Height of the Custom Tiles Preview Image" ),
				
				#("TilesRendering",				"RegionType", 								#RegionType,								true, 	"Region Rendering",										"Region Type: 1=Region 2=Crop 3=Blowup" ),
				#("TilesRendering",				"RegionUseMaxValues", 						#RegionUseMaxValues,						true, 	"Region Rendering",										"Use 3ds Max Region Values" ),
	
				#("DBROptions",					"DBR", 										#DBR,										true, 	"DBR Options",											"Enable DBR", false, false ),
				#("DBROptions",					"DBRServers", 								#DBRServers,								true, 	"DBR Options",											"Number of Slaves for DBR" ),
				#("DBROptions",					"DBRUse3dsCmd",								#DBRUse3dsCmd,								true,	"DBR Options",											"Use 3dsCmd instead of 3dsMax Plugin"),

				#("GpuOptions",					"GpusPerTask",								#GpusPerTask,								true,	"Gpu Options",											"GPUs Per Task" ),
				#("GpuOptions",					"GpuDevices",								#GpuDevices,								false,	"Gpu Options",											"Select GPU Devices" ),
				
				#("Blacklist",					"SlaveSettingsSticky", 						#SlaveSettingsSticky,						true, 	"Blacklist/Whitelist Slaves",							"Make Blacklist Settings Sticky", false, true ),
				#("Blacklist",					"BlackOrWhite", 							#SlavesBlackList,							true, 	"Blacklist/Whitelist Slaves",							"Blacklist", false, true ),
				#("Blacklist",					"SlavesList", 								#SlavesList,								true, 	"Blacklist/Whitelist Slaves",							"Slaves List", false, true ),
				#("Blacklist",					"SlavesNamedSet", 							#SlavesNamedSet,							false, 	"Blacklist/Whitelist Slaves",							"Slaves Selection Set", false, true ),
				
				#("Masters",					"MastersSettingsSticky", 					#MastersSettingsSticky,						true, 	"DBR Off-Load Masters",									"Make Masters Settings Sticky", false, true ),
				#("Masters",					"BlackOrWhite", 							#MastersBlackList,							true, 	"DBR Off-Load Masters",									"Blacklist/Whitelist Slaves For DBR Masters", false, true ),
				#("Masters",					"MastersNamedSet", 							#MastersNamedSet,							false, 	"DBR Off-Load Masters",									"Masters Selection Set", false, true ),
				#("Masters",					"MastersList", 								#MastersList,								true, 	"DBR Off-Load Masters",									"Masters List", false, true ),
				
				
				#("DraftSettings",				"DraftSubmitJob", 							#DraftSubmitJob,							true, 	"Deadline Draft Post-Render Processing",				"Submit Dependent Draft Job" ),
				#("DraftSettings",				"DraftShotgunUpload", 						#DraftShotgunUpload,						true, 	"Deadline Draft Post-Render Processing",				"Upload to Shotgun" ),
				#("DraftSettings",				"DraftQuick", 								#DraftQuick,								true, 	"Deadline Draft Post-Render Processing",				"Quick" ),
				#("DraftSettings",				"DraftFormat", 								#DraftFormat,								false, 	"Deadline Draft Post-Render Processing",				"Draft Format" ),
				#("DraftSettings",				"DraftCodec", 								#DraftCodec,								false, 	"Deadline Draft Post-Render Processing",				"Draft Codec" ),
				#("DraftSettings",				"DraftResolution", 							#DraftResolution,							false, 	"Deadline Draft Post-Render Processing",				"Draft Resolution" ),
				#("DraftSettings",				"DraftQuality", 							#DraftQuality,								true, 	"Deadline Draft Post-Render Processing",				"Draft Quality" ),
				#("DraftSettings",				"DraftFrameRate", 							#DraftFrameRate,							false, 	"Deadline Draft Post-Render Processing",				"Draft Frame Rate" ),
				#("DraftSettings",				"DraftTemplate", 							#DraftTemplate,								false, 	"Deadline Draft Post-Render Processing",				"Template" ),
				#("DraftSettings",				"DraftUser", 								#DraftUser,									false, 	"Deadline Draft Post-Render Processing",				"User" ),
				#("DraftSettings",				"DraftEntity", 								#DraftEntity,								false, 	"Deadline Draft Post-Render Processing",				"Entity" ),
				#("DraftSettings",				"DraftVersion", 							#DraftVersion,								false, 	"Deadline Draft Post-Render Processing",				"Version" ),
				
				#("ExtraInfo",					"ExtraInfo0",								#ExtraInfo0,								false,	"Extra Info", 											"Extra Info 0", true, false),
				#("ExtraInfo",					"ExtraInfo1",								#ExtraInfo1,								false,	"Extra Info", 											"Extra Info 1", true, false),
				#("ExtraInfo",					"ExtraInfo2",								#ExtraInfo2,								false,	"Extra Info", 											"Extra Info 2", true, false),
				#("ExtraInfo",					"ExtraInfo3",								#ExtraInfo3,								false,	"Extra Info", 											"Extra Info 3", true, false),
				#("ExtraInfo",					"ExtraInfo4",								#ExtraInfo4,								false,	"Extra Info", 											"Extra Info 4", true, false),
				#("ExtraInfo",					"ExtraInfo5",								#ExtraInfo5,								false,	"Extra Info", 											"Extra Info 5", true, false),
				#("ExtraInfo",					"ExtraInfo6",								#ExtraInfo6,								false,	"Extra Info", 											"Extra Info 6", true, false),
				#("ExtraInfo",					"ExtraInfo7",								#ExtraInfo7,								false,	"Extra Info", 											"Extra Info 7", true, false),
				#("ExtraInfo",					"ExtraInfo8",								#ExtraInfo8,								false,	"Extra Info", 											"Extra Info 8", true, false),
				#("ExtraInfo",					"ExtraInfo9",								#ExtraInfo9,								false,	"Extra Info", 											"Extra Info 9", true, false),

				#("JobEnvironmentKeys",			"IncludeEnvironment",						#IncludeEnvironment,						true,	"Include Environment",									"Include Environment"),
				#("JobEnvironmentKeys",			"UseJobEnvironmentOnly",					#UseJobEnvironmentOnly,						true,	"Use Job Environment Only",								"Use Job Environment Only"),
		
				#("RTT", 						"IsBakeJob",								#IsBakeJob,									true,	"Render to Texture", 									"Submit as Render to Texture Job", true, false),
				#("RTT", 						"BakeJobOneObjectPerTask", 					#BakeJobOneObjectPerTask,					true,	"Render to Texture", 									"One Object Per Task"),

				#("BatchRender",				"UseBatchRender", 							#UseBatchRender, 							true,	"Batch Submission", 									"Use Data from 3ds Max Batch Render" ),
				#("BatchRender",				"BatchRenderMode",							#BatchRenderMode, 							true,	"Batch Submission", 									"Batch Render Mode - Local / Master Batch" ),
				#("BatchRender", 				"CleanupSubmissionFoldersAfterEachBatchJob",#CleanupSubmissionFoldersAfterEachBatchJob, true, 	"Batch Submission", 									"Cleanup Submission Folders After Each Batch Job"),
				
				#("Assets", 					"AssetSyncAllFiles", 						#AssetSyncAllFiles,							true, 	"Scene And Asset Files",					 			"Collect All Available Frames In A Sequence"), 
				#("Assets", 					"AssetsAutoUpdateList", 					#AssetsAutoUpdateList,						true, 	"Scene And Asset Files",					 			"Automatically Update Assets List In The UI"), 
				#("Assets", 					"AssetsPreCacheFiles", 						#AssetsPreCacheFiles,						true, 	"Precache Asset Files",					 				"Pre-cache all Asset Files to the AWS Portal Infrastructure."),
				#("Assets", 					"AssetsIncludeFilesInJob", 					#AssetsIncludeFilesInJob,					true, 	"Synchronize Asset Files",					 			"Include Asset Files in Job Metadata for AWS Portal Asset Sync."),
				
				#("CustomLabels", 				"PreviewJobLabel", 							#PreviewJobLabel,							false, 	"Preview Job", 											"Preview Frames Label", true, false), 
				#("CustomLabels", 				"PreviewRestJobLabel", 						#PreviewRestJobLabel,						false, 	"Preview Job",											"Rest Of Frames Label", true, false), 
				#("CustomLabels", 				"BatchMasterJobLabel", 						#BatchMasterJobLabel,						false, 	"Batch Job", 											"Batch Master Job Label", true, false), 
				#("CustomLabels", 				"MAXScriptJobLabel", 						#MAXScriptJobLabel,							false, 	"MAXScript Job", 										"MAXScript Job Label", true, false)
			)
		),
		
		fn getSettingsListAsTree =
		(
			local theSettingsList = SMTDFunctions.getSettingsList()
			local theCategories = #()
			local theLeafs = #()
			for i in theSettingsList do appendIfUnique theCategories i[5]
			for i in theSettingsList do
			(
				theIndex = findItem theCategories i[5]
				if theLeafs[theIndex] == undefined do theLeafs[theIndex] = #()
				append theLeafs[theIndex] i
			)
			#(theCategories,theLeafs)
		),
		
		--This function loads the STICKY settings from the local INI file and stuffs them into the SMTDSettings structure.
		--After calling this function, all settings that are not marked with * in the UI will be set to the last settings from the UI
		--If you are calling the submit function from an outside script without the UI, you might want to call this function first to
		--replace the factory defaults with the user defaults before submitting...
		fn loadSettings =
		(
			local theSettingsList = SMTDFunctions.getSettingsList()
			
			for i in theSettingsList where i[3] != #none do
			(
				theDefault = getProperty SMTDSettings i[3]
				theValue = SMTDFunctions.getInI i[1] i[2] theDefault executeIt:i[4] useStickyFile:(not (i[7]==false)) isSticky:(not (i[8]==false))
					
				--format "% theDefault=% theValue=%\n" i[3] theDefault theValue
					
				if findItem #("RegionRenderingMode") i[2] > 0 do
				(
					if findItem #("none", "singleframemultiregion", "animationmultiregion", "singleframetiles", "maxregion") (tolower (theValue as string)) == 0 do theValue = "none"
					theValue = theValue as name	
				)
				if findItem #("SubmitSceneMode") i[2] > 0 do 
				(
					if theValue == "" or matchPattern theValue pattern:"networkuse" do theValue = "reposave"
					theValue = theValue as name
				)
				if findItem #("StereoCameraMode") i[2] > 0 do 
				(
					if theValue == "" do theValue = "left"
					theValue = theValue as name
				)
				if findItem #("StereoCameraPriorityOrder") i[2] > 0 do 
				(
					if theValue == "" do theValue = "none"
					theValue = theValue as name
				)				
				if findItem #("LeftEyeTag") i[2] > 0 do 
				(
					if theValue == "" do theValue = "LE"
				)
				if findItem #("RightEyeTag") i[2] > 0 do 
				(
					if theValue == "" do theValue = "RE"
				)
				if findItem #("CenterEyeTag") i[2] > 0 do 
				(
					if theValue == "" do theValue = "CE"
				)				
				--prevent non-existing INI file values from setting the value to "" if there is a factory default already:
				if findItem #("DraftFormat","DraftCodec","DraftResolution","DraftFrameRate")  i[2] > 0 and theValue == "" do 
				(
					theValue = theDefault
				)
				
				setProperty SMTDSettings i[3] theValue
			)
			
			if SMTDSettings.JobName == "" or SMTDSettings.AutomaticallyUpdateJobName then
			(
				if getfilenamefile maxfilename != "" then
					SMTDSettings.JobName = getfilenamefile maxfilename
				else
					SMTDSettings.JobName = "Untitled 3ds Max Job"
			)
				
			if SMTDSettings.OutOfOrderMethod == "" then
				SMTDSettings.OutOfOrderMethod = #normal
			else	
				SMTDSettings.OutOfOrderMethod = SMTDSettings.OutOfOrderMethod as name		

			if is64bitApplication() then
				SMTDSettings.MaxVersionToForce = "64bit"
			else
				SMTDSettings.MaxVersionToForce = "32bit"
			
			local rendererID = SMTDFunctions.getRendererIdString() 
			
			if (SMTDFunctions.getInI "RenderingOptions" "ForceRestartRenderer" true useStickyFile:false isSticky:false) do
			(
				if rendererID == "mentalray" or rendererID == "vray" or rendererID == "brmax" or rendererID == "corona" then
					SMTDSettings.RestartRenderer = true
			)
			
			if SMTDSettings.OutputFilenameUserPattern != "" do SMTDSettings.ReplaceOutputFilenameWithUserPattern = true
				
			SMTDSettings.LimitGroups = for i in SMTDSettings.LimitGroups where i != "" collect i --clear empty names
			SMTDSettings.LimitGroupsToUse = for i in SMTDSettings.LimitGroupsToUse where i != "" collect i --clear empty names
				
			if not SMTDSettings.SlaveSettingsSticky then --if settings are sticky, load the last settings, otherwise reset the sticky settings on disk
			(
				SMTDSettings.SlavesList = #()
				SMTDSettings.SlavesBlackList = true
				--setIniSetting SMTDPaths.InIFile "Blacklist"  "SlavesNamedSet"  SMTDSettings.SlavesNamedSet 
				setIniSetting SMTDPaths.InIFile "Blacklist"  "BlackOrWhite" (SMTDSettings.SlavesBlackList as string) 
				setIniSetting SMTDPaths.InIFile "Blacklist"  "SlavesList" "#()" 
			)		
			if not SMTDSettings.MastersSettingsSticky then --if settings are sticky, load the last settings, otherwise reset the sticky settings on disk
			(
				SMTDSettings.MastersList = #()
				SMTDSettings.MastersBlackList = true
				--setIniSetting SMTDPaths.InIFile "Masters"  "MastersNamedSet"  SMTDSettings.MastersNamedSet 
				setIniSetting SMTDPaths.InIFile "Masters"  "BlackOrWhite" (SMTDSettings.MastersBlackList as string)
				setIniSetting SMTDPaths.InIFile "Masters"  "MastersList" "#()" 
			)
			
			SMTDSettings.UserName = SMTDFunctions.GetDeadlineUser()
			
			SMTDSettingsDefaults = copy SMTDSettings
			SMTDFunctions.getStoreInSceneExclusionList()
		),
			
		fn storeSettingsWithScene =
		(
			local theSS = "" as stringStream

			format "#( " to:theSS
			local thePropNames = getPropNames ::SMTDSettings
			for i = 1 to thePropNames.count do 
			(
				local p = thePropNames[i]
				local theProp = (getProperty ::SMTDSettings p)
				if classof theProp == String then 
					format "#(%,\"%\")" p (substituteString theProp "\\" "\\\\") to:theSS
				else
					format "#(%,%)" p theProp to:theSS
				if p != thePropNames[thePropNames.count] then
					format "," to:theSS 
				else 
					format ")" to:theSS 
			)
			
			with PrintAllElements on 
			(
				setAppData trackViewNodes 20170222 (theSS as string)
			)
		),
		
		fn restoreSettingstFromScene base:#current =
		(
			case base of
			(
				#factory: ( ::SMTDSettings = copy ::SMTDSettingsFactory ) --start with factory defaults
				#sticky:  ( ::SMTDSettings = copy ::SMTDSettingsFactory; SMTDFunctions.loadSettings())--start with latest sticky settings
				default: ( )  --including #current mode, start with the current dialog settings
			)
			
			local theData = getAppData trackViewNodes 20170222 
			if theData != undefined then 
				theData = try(execute theData)catch(#())
			else
				theData = #()
			if theData.count == 0 then
				try(SMTD_MainRollout.Ui_report ("!!NO SMTD Settings found in the 3ds Max Scene."))catch()
			else
			(
				local actualCount = 0
				for p in theData do
				(
					if isProperty ::SMTDSettings p[1] and findItem ::SMTDSaveInSceneExclusionList p[1] == 0 do
					(
						try
						(
							setProperty ::SMTDSettings  p[1] p[2]
							actualCount += 1
						)
						catch
						(
							try(SMTD_MainRollout.Ui_report  ("  --FAILED to load ["+p[1] as string+"="+p[2] as string+"]..."))catch() 
						)
					)
				)
				try(SMTD_MainRollout.Ui_report ("+"+actualCount as string +" of "+theData.count as string +" SMTD Settings loaded from the 3ds Max Scene."))catch()
			)
		),
		
		fn getSettingsAsStructFromScene base:#current =
		(
			case base of
			(
				#factory: ( TempSMTDSettings = copy ::SMTDSettingsFactory ) --start with factory defaults
				#sticky:  ( TempSMTDSettings = copy ::SMTDSettingsFactory; SMTDFunctions.loadSettings() )--start with latest sticky settings
				default: ( TempSMTDSettings = copy ::SMTDSettings )  --including #current mode, start with current dialog settings
			)			
			
			local theData = getAppData trackViewNodes 20170222 
			if theData != undefined then 
				theData = try(execute theData)catch(#())
			else
				theData = #()
					
			for p in theData do
				if isProperty ::SMTDSettings p[1] and findItem ::SMTDSaveInSceneExclusionList p[1] == 0 do
					try (setProperty TempSMTDSettings  p[1] p[2]) catch ()
			
			TempSMTDSettings	
		),
		
		fn storeWorkflowSettingsWithScene &WorkflowStruct =
		(
			local theHash = abs ((dotNetObject "System.String" WorkflowStruct.WorkflowName).GetHashCode()) 
			local theSS = "" as stringStream

			format "#( " to:theSS
			local thePropNames = getPropNames WorkflowStruct
			thePropNames = for p in thePropNames where findItem #(#WorkflowName, #WorkflowTitle, #Description) p == 0 and classof (getProperty WorkflowStruct p) != MAXScriptFunction collect p
			for i = 1 to thePropNames.count do 
			(
				local p = thePropNames[i]
				local theProp = (getProperty WorkflowStruct p)
				if classof theProp == String then 
					format "#(%,\"%\")" p (substituteString theProp "\\" "\\\\") to:theSS
				else
					format "#(%,%)" p theProp to:theSS
				if p != thePropNames[thePropNames.count] then
					format "," to:theSS 
				else 
					format ")" to:theSS 
			)
			with PrintAllElements on 
			(
				setAppData trackViewNodes theHash (theSS as string)
			)
		),		
		
		fn restoreWorkflowSettingsFromScene &WorkflowStruct propsToSkip:#() =
		(
			local theHash = abs ((dotNetObject "System.String" WorkflowStruct.WorkflowName).GetHashCode()) 
			local theData = getAppData trackViewNodes theHash 
			if theData != undefined then 
				theData = try(execute theData)catch(#())
			else
				theData = #()
			if theData.count == 0 then
				try(SMTD_MainRollout.Ui_report ("!!NO Workflow Settings found in the 3ds Max Scene."))catch()
			else
			(
				local actualCount = 0
				for p in theData do
				(
					if isProperty WorkflowStruct p[1] and findItem propsToSkip p[1] == 0 do
					(
						try
						(
							setProperty WorkflowStruct  p[1] p[2]
							actualCount += 1
						)
						catch
						(
							try(SMTD_MainRollout.Ui_report  ("  --FAILED to load ["+p[1] as string+"="+p[2] as string+"]..."))catch() 
						)
					)
				)
				try(SMTD_MainRollout.Ui_report ("+"+actualCount as string +" of "+theData.count as string +" Workflow Setting"+(if theData.count == 1 then "" else "s")+" loaded from the 3ds Max Scene."))catch()
			)
		),

		fn SetPipelineToolStatus statusMessage =
		(
		    SMTDSettings.PipelineToolStatus = statusMessage
		),

		fn openPipelineToolsWindow =
		(
			try( SMTD_MainRollout.Ui_report ( ">Opening Integration Window" ) ) catch()

			if SMTDFunctions.getMaxVersionAsInteger() >= 2014 then -- Native Python added in 2014
			(
				local getPipelineToolsInfo = "import sys; sys.path.append('" + substituteString SMTDPaths.IntegrationDir "\\" "/" + "'); import GetPipelineToolsInfo; GetPipelineToolsInfo.getInfo('" + substituteString SMTDPaths.TempDir "\\" "/" + "')"
				try(python.Execute getPipelineToolsInfo)catch(format "*** % ***\n" (getCurrentException()))
			)
			else
			(
				try( SMTD_MainRollout.Ui_report( "--Pipeline Tools: Unable to grab scene information, as there is no native Python in this version of 3ds Max. Need version 2014 or later." ) ) catch() 
			)

			local keyValuePairs = #()
			local outFileName = SMTDPaths.TempDir + "integration_stdout.txt"
			local deadlineCmd = systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommand.exe"

			-- when launching 3dsmax through Shotgun, Shotgun will add their own Python directories into PYTHONPATH, which ends up breaking pipeline tools
			-- remove the PYTHONPATH before launching UI
			local environment = dotNetClass "System.Environment"
			local pythonPath = environment.GetEnvironmentVariable "PYTHONPATH" 
			environment.SetEnvironmentVariable "PYTHONPATH" ""

			-- Code for pipeline tools V2
			local integrationPath = SMTDPaths.IntegrationDir + "IntegrationUIStandAlone.py"
			sceneName = maxFilePath + maxFileName
			local theArgs = " -executeScript \"" + integrationPath + "\" -v 2 3dsmax -d Shotgun FTrack NIM " + "--path " + "\"" + sceneName + "\""

			try
			(
			    statusMessage = SMTDFunctions.CallDeadlineCommandInMemory theArgs throwOnExitCode:true multiLine: true
			)
			catch
			(
				local ex = getCurrentException()
				print ex
				statusMessage = "Pipeline Tools Error"
			)
			-- No output from the script indicates that the user cancelled the dialog or closed it
			-- without pressing the "OK" button. Both scenarios should be treated as a no-op
			if statusMessage != "" then
				SMTDFunctions.SetPipelineToolStatus(statusMessage)

			local resultFile = OpenFile outFileName
			
			-- if PYTHONPATH actually had stuff then put it back
			if pythonPath != undefined then
				environment.SetEnvironmentVariable "PYTHONPATH" pythonPath

			if resultFile != undefined then
			(
				try
				(
					while not eof resultFile do
					(
						theLine = readline resultFile
						theLine = trimright( trimleft( theLine ) )
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

				try( close resultFile ) catch()
			)

			if keyValuePairs.count > 0 then
			(
				::SMTD_IntegrationKVPs = keyValuePairs
			)
		),

		fn searchIntegrationKVPs searchValue =
		(
			local found = false

			for kvPair in ::SMTD_IntegrationKVPs do
			(
				if searchValue == kvPair[1] then
				(
					found = true
				)
			)
			found
		),

		fn findIntegrationKVPIndex searchValue =
		(
			local index = -1

			for i = 1 to ::SMTD_IntegrationKVPs.count do
			(
				if searchValue == ::SMTD_IntegrationKVPs[i][1] then
				(
					index = i
				)
			)
			index
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

		fn getRendererObject = 
		(
			case (renderers.current.classid as string) of
			(
				"#(1941615238, 2012806412)": renderers.current
				"#(1941615238L, 2012806412L)": renderers.current
				
				"#(1770671000, 1323107829)": renderers.current.V_Ray_settings
				"#(1770671000L, 1323107829L)": renderers.current.V_Ray_settings

				default: renderers.current
			)
		),
		
		fn getRendererSupportsDBROffload =
		(
			local rendererID = SMTDFunctions.getRendererIdString()
			(rendererID == "mentalray") or (rendererID == "vray") or (rendererID == "vrayrt") or (rendererID == "corona")
		),

		fn getFilesFromIFL iflFile =
		(
			if SMTDFunctions.getMaxVersionAsInteger() >= 2017 then -- Python wrappers added in 2017
			(
				local sys = python.Import("sys")
				try
				(
					-- list.index will fail if it's not in the list ( why not -1? :[ )
					sys.path.index(SMTDPaths.MainSubmissionDir)
				)
				catch
				(
					sys.path.append(SMTDPaths.MainSubmissionDir)
				)
				local DeadlineMaxFunctions = python.Import("DeadlineMaxFunctions")
				local ifl = DeadlineMaxFunctions.IFLParser(iflFile)
				local files = ifl.getFilesInIFL()

				-- must transform python list into maxscript list
				return SMTDFunctions.getMaxscriptListFromPythonList(files)
			)
			else
			(
				local results = #()
				local dir = getFileNamePath iflFile
				local iflContent = ( dotNetClass "System.IO.File" ).ReadAllLines iflFile
				for filename in iflContent do
				(
					if getFileNamePath filename == "" do filename = dir + filename
					if doesFileExist filename do append results filename
				)
				return results
			)
		),

		fn getMaxscriptListFromPythonList pythonList =
		(
			maxscriptList = #()
			if SMTDFunctions.getMaxVersionAsInteger() >= 2017 then -- Python wrappers added in 2017
			(
				bi = python.Import("__builtin__")
				for i = 1 to bi.len(pythonList) do
				(
					append maxscriptList pythonList[i]
				)
			)
			else
			(
				throw "function getMaxscriptListFromPythonList is only available in 3dsmax 2017 or later."
			)
			return maxscriptList
		),
		
		fn ReadInFile filename =
		(
			local results = #()
			try
			(
				local resultFile = ( dotNetClass "System.IO.File" ).ReadAllLines filename
			)			
			catch
			(
				try( SMTD_MainRollout.Ui_report ( "--QuickDraft File: File Not Found ["+filename+"]" ) ) catch()
			)

			if resultFile != undefined then
			(
				for theLine in resultFile do
				(
					theLine = trimright theLine
					theLine = trimleft theLine
					append results theLine
				)
			)
			else
			(
				try( SMTD_MainRollout.Ui_report ( "--QuickDraft File: Problem reading file ["+filename+"]" ) ) catch()
			)	
			results
		),

		fn getRenderDimensions =
		(
			local m_renderWidth = renderWidth
			local m_renderHeight = renderHeight
			local m_renderPixelAspect = renderPixelAspect

			local rendererID = SMTDFunctions.getRendererIdString()
			if rendererID == "vray" do --NOT applicable for VRay RT renderer
			(
				vr = renderers.current
				if vr.output_on == true AND vr.output_getsetsfrommax == false do
				(
					m_renderWidth = vr.output_width
					m_renderHeight = vr.output_height
					m_renderPixelAspect = vr.output_aspect
				)
			)
			#(m_renderWidth,m_renderHeight,m_renderPixelAspect)
		),
		
		fn AnimateLastSubmissionState =
		(
			try
			(
				SMTD_MainRollout.sld_lastSubmissionState.value += 1 
				if SMTD_MainRollout.sld_lastSubmissionState.value >= 100 do SMTD_MainRollout.sld_lastSubmissionState.value = 50
			)catch()
		),
		
		fn purifyFileName theFileName =
		(
			for i = 1 to theFileName.count do
				if findItem SMTDSettings.PurifyCharacterCodes (bit.charAsInt theFileName[i]) > 0 do theFileName[i] = "_"
			theFileName	
		),
		
		fn purifyRenderElementName theName =
		(
			for i = 1 to theName.count do
				if findItem #(" ", "#") theName[i] > 0 do theName[i] = "_"
			theName	
		),	
		
		fn storeRenderElementNames =
		(
			local reManager = maxOps.GetCurRenderElementMgr()
			SMTDSettings.OriginalRenderElementNames = #()
			if reManager != undefined do
			(
				local reCount = reManager.NumRenderElements()
				for i = 0 to reCount - 1 do
				(
					if classof (reManager.GetRenderElement i) != Missing_Render_Element_Plug_in do
					(
						local theElement = reManager.GetRenderElement i
						if theElement != undefined AND theElement.elementName != undefined do --protect against 3rd party renderers which have not fully implemented RE support in 3dsMax
							SMTDSettings.OriginalRenderElementNames[i+1] = theElement.elementName
					)
				)
			)
		),
		
		fn restoreRenderElementNames =
		(
			local reManager = maxOps.GetCurRenderElementMgr()
			if reManager != undefined do
			(
				local reCount = reManager.NumRenderElements()
				for i = 0 to reCount - 1 do
				(
					if classof (reManager.GetRenderElement i) != Missing_Render_Element_Plug_in do
					(
						local theElement = reManager.GetRenderElement i
						local theName = SMTDSettings.OriginalRenderElementNames[i+1]
						if theElement != undefined AND theElement.elementName != undefined do --protect against 3rd party renderers which have not fully implemented RE support in 3dsMax
							if theName != undefined do theElement.elementName = theName
					)
				)
			)
		),

		fn fixRenderElementNames =
		(
			local reManager = maxOps.GetCurRenderElementMgr()
			if reManager != undefined do
			(
				local reCount = reManager.NumRenderElements()
				for i = 0 to reCount - 1 do
				(
					if classof (reManager.GetRenderElement i) != Missing_Render_Element_Plug_in do
					(
						local theElement = reManager.GetRenderElement i
						if theElement != undefined AND theElement.elementName != undefined do --protect against 3rd party renderers which have not fully implemented RE support in 3dsMax
							theElement.elementName = SMTDFunctions.purifyRenderElementName theElement.elementName 
					)
				)
			)
		),
		
		fn GetNetworkPath subDir:"" =
		(
			local resultMsg = ""
			try
			(
				local result = SMTDFunctions.CallDeadlineCommandInMemory ("-getrepositorypath "+subDir) multiLine:false timeOut:10
				if result != "" then
				(
					resultMsg = result
				)
				else
					resultMsg = "***DISCONNECTED***"
			) catch()
			resultMsg
		),
		
		--This function calls the deadline executable with the supplied parameters and waits for a specified time in SECONDS for the execution to complete
		--If the result is not returned in the given time, a #timeout result is returned.
		fn waitForCommandToComplete params timeOutInSec paramIsFile:false dontWait:false =
		(
			local result = -2
			deleteFile SMTDPaths.SubmitExitCode
			deleteFile SMTDPaths.SubmitOutput
			
			if paramIsFile then
				ShellLaunch SMTDPaths.DeadlineBGExec params
			else
				ShellLaunch SMTDPaths.DeadlineBGExec (" -outputfiles \""+SMTDPaths.SubmitOutput+"\" \""+SMTDPaths.SubmitExitCode+"\" " + params)
			
			if dontWait do return #queued
			
			local startTimeStamp = timestamp()
			local ready = false
			while not ready do
			(
				sleep 0.15
				SMTDFunctions.AnimateLastSubmissionState()
				try(windows.processPostedMessages())catch()
				if ::SMTDIsCurrentlySubmitting == false do 
				(
					result = -4
					ready = true
				)
				if doesFileExist SMTDPaths.SubmitExitCode do
				(
					local theFile = openFile SMTDPaths.SubmitExitCode
					try(result = readValue theFile)catch(result = -2)
					try(close theFile)catch()
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
				default: #failed --handle non-zero codes as failure
				(-2): #readerror
				(-3): #timeout
				(-4): #cancel
			)	
		),

		--This function reads the content of a file into the supplied array.
		fn ReadFileIntoArray theFilename theArray =
		(
			local theFile = OpenFile theFilename 
			local result = #failure
			if theFile != undefined then
			(
				try 
				(
					while not eof theFile do 
						append theArray (ReadLine theFile )
					result = #success
				)
				catch()
				close theFile 
			)
			else
				result = #fileNotFound
			result
		),
	
		--Reads the list of available repositories.
		fn getRepositoryList =
		(
			try(SMTD_MainRollout.Ui_report (">Collecting Repository Networks..."))catch()
			
			local result = #success
			local tempArray = #("DISABLED")
			--SMTDFunctions.ReadFileIntoArray "Y:\\Winnipeg\\Deadline\\RemoteSubmissionRepositories.ini" tempArray
			--SMTDFunctions.ReadFileIntoArray "V:\\deadline_synch\\RemoteSubmissionRepositories.ini" tempArray
			SMTDFunctions.ReadFileIntoArray "Z:\\assets\\scripts\\mxs\\RemoteSubmissionRepositories.ini" tempArray
			
			local tempRepositoryList = #()
			local tempRepositoryListActual = #()
			for i in tempArray do
			(
				local parts = filterString i ","
				append tempRepositoryList parts[1]
				append tempRepositoryListActual parts[2]
			)
			SMTDSettings.RepositoryList = tempRepositoryList
			SMTDSettings.RepositoryListActual = tempRepositoryListActual
			result
		),
		
		fn getRepositoryListFilename =
		(
			SMTDPaths.MainSubmissionDir + "\\RemoteSubmissionRepositories.ini"
		),
		
		fn getZeros theNumber count:4=
		(
			local theStr = theNumber as string
			local theCount = count-(theStr.count)
			if theCount < 1 then "" else substring "00000000000" 1 theCount					
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
		
		fn CallDeadlineCommandInMemory argument multiLine:false throwOnExitCode:false timeOut:3600 =
		(
			local st = timestamp()
			--Function supports single line and multiline string return
			local resultMsg = ""
			local exitCode = 0
			try (
				local p = dotnetobject "system.diagnostics.process"
				p.StartInfo.FileName = SMTDPaths.DeadlineExec
				p.StartInfo.Arguments = argument
				p.StartInfo.RedirectStandardOutput = true
				p.StartInfo.RedirectStandardError = true
				p.StartInfo.UseShellExecute = false
				p.StartInfo.CreateNoWindow = true
				p.Start()
				if multiLine then
					local cmdOutput = p.StandardOutput.ReadToEnd() --multiple line output
				else
					local cmdOutput = p.StandardOutput.ReadLine() --single line output
				p.WaitForExit(timeOut)
				if p.ExitCode == 0 then
				    resultMsg = cmdOutput
				else
				(
					-- Print stderr if any is captured
					local cmdError = p.StandardError.ReadToEnd()
					if cmdError != "" do print cmdError
					print cmdOutput
					exitCode = p.ExitCode
				)
				p.Dispose()
				p = undefined
			)catch(
				local ex = getCurrentException()
				print "The following error occurred while calling Deadline Command:"
				print ex
			)
			if SMTD_DebugPrintsOn == true do format "--(CallDeadlineCommandInMemory %) took % ms.\n" argument (timestamp()-st)
			if throwOnExitCode and exitCode != 0 then
				throw ("Deadline command returned exit code: " + (exitCode as string))
			resultMsg
		),

		fn CallDeadlineControl argument =
		(
			--Function to display Deadline UI Control and return single line string only
			local resultMsg = "Error getting line"
			try (
				local p = dotnetobject "system.diagnostics.process"
				p.StartInfo.FileName = SMTDPaths.DeadlineExec
				p.StartInfo.Arguments = argument
				p.StartInfo.RedirectStandardOutput = true
				p.StartInfo.UseShellExecute = false
				p.StartInfo.CreateNoWindow = true
				p.Start()
				local cmdOutput = p.StandardOutput.ReadLine()
				p.WaitForExit()
				if p.ExitCode == 0 do ( if cmdOutput != "Action was canceled by user" do resultMsg = cmdOutput )
				p.Dispose()
				p = undefined
			)catch()
			resultMsg
		),
		
		fn CollectPools =
		(
			try(SMTD_MainRollout.Ui_report (">Collecting Pools..."))catch()
			local st = timestamp()	
			SMTDSettings.Pools = #()
			local cmdOutput = SMTDFunctions.CallDeadlineCommandInMemory "-Pools"  multiLine:true timeOut:SMTDSettings.TimeoutCollectData
			if cmdOutput != "" then 
			(
				SMTDFunctions.ReadStreamIntoArray cmdOutput SMTDSettings.Pools
				try(SMTD_MainRollout.Ui_report ("+"+  SMTDSettings.Pools.count as string +" Pool"+ (if SMTDSettings.Pools.count == 1 then "" else "s") +" Collected in "+ ((timestamp()-st)/1000.0) as string +" sec. " ))catch()
			)
			else
				try(SMTD_MainRollout.Ui_report ("--Failed To Collect Pools."))catch()	
		),
		
		fn CollectGroups =
		(
			try(SMTD_MainRollout.Ui_report (">Collecting Groups..."))catch()
			local st = timestamp()	
			SMTDSettings.Groups = #()
			local cmdOutput = SMTDFunctions.CallDeadlineCommandInMemory "-Groups" multiLine:true timeOut:SMTDSettings.TimeoutCollectData
			if cmdOutput != "" then
			(
				SMTDFunctions.ReadStreamIntoArray cmdOutput SMTDSettings.Groups timeOut:SMTDSettings.TimeoutCollectData
				try(SMTD_MainRollout.Ui_report ("+"+  SMTDSettings.Groups.count as string +" Group" + (if SMTDSettings.Groups.count == 1 then "" else "s")+ " Collected in "+ ((timestamp()-st)/1000.0) as string +" sec. " ))catch()
			)
			else
				try(SMTD_MainRollout.Ui_report ("--Failed To Collect Groups."))catch()	
		),
		
		fn GetMaximumPriority =
		(
			try(SMTD_MainRollout.Ui_report (">Querying Maximum Priority..."))catch()
			local st = timestamp()	
			SMTDSettings.MaximumPriority = 100
			local cmdOutput = SMTDFunctions.CallDeadlineCommandInMemory "-GetMaximumPriority" timeOut:SMTDSettings.TimeoutCollectData
			if cmdOutput != "" then
			(
				SMTDSettings.MaximumPriority = (cmdOutput as integer)
				try(SMTD_MainRollout.Ui_report ("+Maximum Priority of "+ SMTDSettings.MaximumPriority as string +" Queried in "+ ((timestamp()-st)/1000.0) as string +" sec. " ))catch()
			)
			else
				try(SMTD_MainRollout.Ui_report ("--Failed To Query Maximum Priority, Defaulting to 100."))catch()
		),		
		
		--Reads the list of available Slaves
		fn CollectSlaves=
		(
			try(SMTD_MainRollout.Ui_report (">Collecting Slaves..."))catch()
			local st = timestamp()
			SMTDSettings.Slaves = #()	
			local cmdOutput = SMTDFunctions.CallDeadlineCommandInMemory ("-slaves " + SMTDSettings.CurrentRepository ) multiLine:true timeOut:SMTDSettings.TimeoutCollectData
			if cmdOutput != "" then			
			(
				SMTDFunctions.ReadStreamIntoArray cmdOutput SMTDSettings.Slaves timeOut:SMTDSettings.TimeoutCollectData
				try(SMTD_MainRollout.Ui_report ("+"+ SMTDSettings.Slaves.count as string +" Slave"+(if SMTDSettings.Slaves.count == 1 then "" else "s")+" Collected in "+ ((timestamp()-st)/1000.0) as string +" sec. " ))catch()
				try(SMTD_MainRollout.sld_lastSubmissionState.value = 100.0)catch()
			)
			else
				try(SMTD_MainRollout.Ui_report ("--Failed To Collect Slaves."))catch()
		),	

		fn CollectSlavesInfo =
		(
			try(SMTD_MainRollout.Ui_report (">Collecting Info on all Slaves"))catch()
			local st = timestamp()	
			local oldOutput = SMTDPaths.SubmitOutput --remember current deadlineCommand output files
			local oldResult = SMTDPaths.SubmitExitCode
			makeDir (SMTDPaths.SettingsDir + "slaveselectionsets") all:true --make sure the subfolder exists
			SMTDPaths.SubmitOutput = (SMTDPaths.SettingsDir + "slaveselectionsets\\slavesinfo.ini" ) --repoint both deadlineCommand files to the new folder
			SMTDPaths.SubmitExitCode = (SMTDPaths.SettingsDir + "slaveselectionsets\\slavesinfo.result" )
			deleteFile SMTDPaths.SubmitOutput --remove any slavesinfo file that might exist
			local result = SMTDFunctions.waitForCommandToComplete ("-getslaves true "+ SMTDSettings.CurrentRepository ) SMTDSettings.TimeoutCollectData 
			SMTDPaths.SubmitOutput = oldOutput --set both paths back to where they used to be
			SMTDPaths.SubmitExitCode = oldResult 
			if result == #success then			
			(
				try(SMTD_MainRollout.Ui_report ("+Slave Info collected in "+ ((timestamp()-st)/1000.0) as string +" sec. " ))catch()
				try(SMTD_MainRollout.sld_lastSubmissionState.value = 100.0)catch()
			)				
			else
				if result == #timeout then
					try(SMTD_MainRollout.Ui_report ("--Failed To Collect Slaves Info in " + SMTDSettings.TimeoutCollectData as string + " seconds.\nConsider Increasing the Data Collection Timeout in the User Options tab."))catch()
				else
					try(SMTD_MainRollout.Ui_report ("--Failed To Collect Slaves Info."))catch()
			result 		
		),
			
		fn unregisterCallbacks =
		(
			callbacks.removeScripts id:#SubmitMaxToDeadlineAltIni
		),
		
		fn registerCallbacks =
		(
			SMTDFunctions.unregisterCallbacks()
			callbacks.addScript #FilePostOpen "try(SMTDFunctions.SuggestAltIni())catch()" id:#SubmitMaxToDeadlineAltIni
			if (maxVersion())[1]/1000 >= 6 do
				callbacks.addScript #PostRendererChange "try(SMTDFunctions.SuggestAltIni())catch()" id:#SubmitMaxToDeadlineAltIni
		),
		
		fn CollectAltIni =
		(
			try
			(
				if SMTDPaths.PluginDir3dsmax != "" then
				(
					SMTDSettings.theIniFiles = getFiles (SMTDPaths.PluginDir3dsmax+ "\\plugin*.ini")
					sort SMTDSettings.theIniFiles
					theFileNames = for i in SMTDSettings.theIniFiles collect getFileNameFile i
					insertItem  "[Default]" theFileNames 1
					SMTDSettings.theIniFilenames = theFileNames
				)
			) 
			catch
			(
				try(SMTD_MainRollout.Ui_report ("--Error Collecting Alternative Plugin.Ini files"))catch()
				SMTDSettings.theIniFiles = #()
				SMTDSettings.theIniFilenames = #("[Default]")
			)
		),

		fn SuggestAltIni =
		(
			SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[1] 
			case SMTDFunctions.getRendererIdString() of
			(
				"scanline" : SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[1] 
				"brmax" : for i = 2 to SMTDSettings.theIniFilenames.count where matchPattern SMTDSettings.theIniFilenames[i] pattern:"*brazil*"  do SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[i]
				"finalrender" : for i = 2 to SMTDSettings.theIniFilenames.count where matchPattern SMTDSettings.theIniFilenames[i] pattern:"*fr*" != undefined or matchPattern SMTDSettings.theIniFilenames[i] pattern:"*final*" do SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[i]
				"iray" : for i = 2 to SMTDSettings.theIniFilenames.count where matchPattern SMTDSettings.theIniFilenames[i] pattern:"*iray*" != undefined do SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[i]
				"mentalray" : for i = 2 to SMTDSettings.theIniFilenames.count where matchPattern SMTDSettings.theIniFilenames[i] pattern:"*mr*" or matchPattern SMTDSettings.theIniFilenames[i] pattern:"*mental*"  do SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[i]
				"vray" : for i = 2 to SMTDSettings.theIniFilenames.count where matchPattern SMTDSettings.theIniFilenames[i] pattern:"*vray*" do SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[i]
				"vrayrt" : for i = 2 to SMTDSettings.theIniFilenames.count where matchPattern SMTDSettings.theIniFilenames[i] pattern:"*vrrt*" do SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[i]
				"maxwell" : for i = 2 to SMTDSettings.theIniFilenames.count where matchPattern SMTDSettings.theIniFilenames[i] pattern:"*maxwell*" do SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[i]
				"krakatoa" : for i = 2 to SMTDSettings.theIniFilenames.count where matchPattern SMTDSettings.theIniFilenames[i] pattern:"*krak*" do SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[i]
				"corona" : for i = 2 to SMTDSettings.theIniFilenames.count where matchPattern SMTDSettings.theIniFilenames[i] pattern:"*corona*" do SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[i]
				"quicksilver" : for i = 2 to SMTDSettings.theIniFilenames.count where matchPattern SMTDSettings.theIniFilenames[i] pattern:"*quick*" do SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[i]
				default: SMTDSettings.AltPluginIni = SMTDSettings.theIniFilenames[1]
			)
		),
		
		--Reads the list of existing jobs and their IDs.
		fn CollectJobs userOnly:false=
		(
			try(SMTD_MainRollout.Ui_report (">Collecting Jobs - This operation can take a long time..."))catch()
			local st = timestamp()
			local tempArray= #()
			local result 
			if userOnly then
				result = SMTDFunctions.CallDeadlineCommandInMemory ("-getjobs -user "+SMTDSettings.UserName ) multiLine:true timeOut:SMTDSettings.TimeoutCollectData
			else	
				result = SMTDFunctions.CallDeadlineCommandInMemory ("-getjobs" ) multiLine:true timeOut:SMTDSettings.TimeoutCollectData
			try(SMTD_MainRollout.sld_lastSubmissionState.value = 100.0)catch()
			--print result
			if  result != "" then			
			(
				try
				(
					theFile = result as stringStream --openFile SMTDPaths.SubmitOutput 
					theName = theID = thePlugin = theUser = theDept = theGroup = theStatus = undefined					
					while not eof theFile do
					(
						str = readLine theFile
						if str != "" do
						(
							if matchPattern str pattern:"Name=*" do theName = substring str 6 -1
							if matchPattern str pattern:"JobId=*" do theID = substring str 7 -1
							if matchPattern str pattern:"PluginName=*" do thePlugin = substring str 12 -1
							if matchPattern str pattern:"UserName=*" do theUser = substring str 10 -1
							if matchPattern str pattern:"Department=*" do theDept= substring str 12 -1
							if matchPattern str pattern:"Group=*" do theGroup = substring str 7 -1
							if matchPattern str pattern:"Status=*" do theStatus= substring str 8 -1
							if theName != undefined AND theID != undefined AND theStatus != undefined AND thePlugin != undefined AND theUser != undefined AND theDept != undefined AND theGroup != undefined  do  --
							(
								append tempArray #(theName,theID,thePlugin,theUser,theDept,theGroup, theStatus)
								--format "%\n" #(theName,theID,thePlugin,theUser,theDept,theGroup, theStatus)
								theName = theID = thePlugin = theUser = theDept = theGroup = theStatus = undefined
							)
						)
					)--end while loop
					--close theFile
				)catch()	
				SMTDSettings.JobsArray = tempArray	
				try(SMTD_MainRollout.Ui_report ("+"+ tempArray.count as string +" Jobs Collected in " + ((timestamp()-st)/1000.0) as string +" sec. " ))catch()
			)
			else
				if result == #timeout then
					try(SMTD_MainRollout.Ui_report ("--Failed To Collect Jobs in " + SMTDSettings.TimeoutCollectData as string + " seconds.\nConsider Increasing the Data Collection Timeout in the User Options tab."))catch()
				else
					try(SMTD_MainRollout.Ui_report ("--Failed To Collect Jobs."))catch()
			result 	
		),
				
		-- Returns the current user in the deadline.ini file, or the current system user if the file is not found.
		fn GetDeadlineUser =
		(
			local user = sysinfo.username --assume the current system name as default
			try
			(
				local fileHandle = openFile (SMTDPaths.UserHomeDir + "deadline.ini") --try to open the deadline.ini file for reading
				if fileHandle != undefined do --if the file open succeeded,
				(
					while not eof fileHandle do --loop through all lines in the file
					(
						local fileLine = readLine fileHandle --read the next line
						if matchPattern fileLine pattern:"User=*" do --if the line starts with User=
							user = substring fileLine 6 -1  --get the rest of the line to the right of the =
					)
				)
				close fileHandle 
			)catch()
						
			user
		),
		
		fn collectSubAnims theObj =
		(
			local theSubsArray = #()
			for i = 1 to theObj.numsubs do
			(
				append theSubsArray (subAnim = theObj[i])
				local theClass = try(classof subAnim.object)catch(undefined)
				if theClass != Unwrap_UVW AND theClass != Master_Point_Controller do
					join SMTDExternalRefsArray.totalSubsArray (SMTDFunctions.collectSubAnims subAnim)
			)	
			theSubsArray
		),

		/*
		fn collectSubAnims theObj =
		(
			local theSubsArray = #()
			append SMTDExternalRefsArray.totalSubsArray theObj
			for i = 1 to theObj.numsubs do
			(
				append theSubsArray (theSubAnim = theObj[i])
				local theClass = try(classof theSubAnim.object)catch(undefined)
				if theClass != Unwrap_UVW AND theClass != Master_Point_Controller do 
					join SMTDExternalRefsArray.totalSubsArray (SMTDFunctions.collectSubAnims theSubAnim)
				if theClass == VRayBump2Normal do
					join SMTDExternalRefsArray.totalSubsArray (SMTDFunctions.collectSubAnims theSubAnim.object.bump_map) 
				if theClass == Unwrap_UVW do 
					for j in theSubAnim.object.texMapList do 
						join SMTDExternalRefsArray.totalSubsArray (SMTDFunctions.collectSubAnims j) 
			)	
			theSubsArray
		),
		*/
		
		--Reads the list of available LimitGroups
		fn CollectLimitGroups =
		(
			try(SMTD_MainRollout.Ui_report (">Collecting Limits...Please wait."))catch()
			local tempArray = #("")
			local st = timestamp()
			local result = SMTDFunctions.CallDeadlineCommandInMemory ("-limitgroups " + SMTDSettings.CurrentRepository ) multiLine:true timeOut:SMTDSettings.TimeoutCollectData
			try(SMTD_MainRollout.sld_lastSubmissionState.value = 100)catch()
			if  result != "" then			
			(
				local ss = result as stringStream
				while not eof ss do append tempArray (readLine ss)
				SMTDSettings.LimitGroups = for i in tempArray where i != "" collect i
				theString = "#("
				for i in SMTDSettings.LimitGroups do (theString += "\"" + i as string + "\",")
				theString += "\"\")"
				setIniSetting SMTDPaths.iniFile "LimitGroups" "LimitGroups" theString 
				try(SMTD_MainRollout.Ui_report ("+"+ SMTDSettings.LimitGroups.count as string +" Limit"+(if SMTDSettings.LimitGroups.count == 1 then "" else "s") +" Collected in "+ ((timestamp()-st)/1000.0) as string +" sec. " ))catch()
			)
			else
				if result == #timeout then
					try(SMTD_MainRollout.Ui_report ("--Failed To Collect Limits  in " + SMTDSettings.TimeoutCollectData as string + " seconds.\nConsider Increasing the Data Collection Timeout in the User Options tab."))catch()
				else
					try(SMTD_MainRollout.Ui_report ("--Failed To Collect Limits."))catch()
			result 	
		),				
		
		fn CollectCategories = (#()), --obsolete, left for backwards compatibility
		
		fn collectMissingFile o = 
		(
			append SMTDSettings.MissingFiles o
		),	
		
		fn checkForMissingMaps =
		(
			SMTDSettings.MissingFiles = #()
			enumerateFiles SMTDFunctions.collectMissingFile #missing
		),

		fn IsLocalPath thePath =
		(
			local localDrives = "abcdefABCDEF"
			if classof thePath == String and thePath.count > 0 then --fixing for VRay Proxy which can have $.filename == undefined which is BAD!
			(
				not (pathIsNetworkPath thePath)
			)
			else
				false
		),

		fn convertPathToLocal TextureCacheFolder thePath =
		(
			local newName = copy thePath
			if pathConfig.isUncPath thePath then
			(
				newName[1] = "_"
				newName[2] = "_"
			)
			else
				newName = substituteString newName ":" "_"
			TextureCacheFolder + newName
		),
		
		fn convertPathToRemote TextureCacheFolder thePath =
		(
			local newName = copy thePath 
			newName = substring newName (TextureCacheFolder.count+1) -1
			if newName[1] != "_" and newName[2] == "_" then 
				newName[2] = ":"
			else if newName[1] == "_" and newName[2] == "_" do
			(
				newName[1] = "\\"
				newName[2] = "\\"
			)		
			newName
		),		
		
		fn isPathInLocalCache TextureCacheFolder thePath =
		(
			matchPattern thePath pattern:(TextureCacheFolder+"*")		
		),		

		fn isPropertyOKForSubmissionToRepository thePropName =
		(
			local result = false
			local rendererID = SMTDFunctions.getRendererIdString() 
			--VRay properties:
			if rendererID == "vray" do
			(
				vr = renderers.current
				if thePropName == #adv_irradmap_loadFileName AND vr.gi_primary_type == 0 AND (vr.adv_irradmap_mode == 2 OR vr.adv_irradmap_mode == 7) do result = true
				if thePropName == #caustics_loadFileName AND vr.caustics_on == true AND vr.caustics_mode == 1 do result = true
				if thePropName == #photonMap_loadFileName AND (vr.gi_primary_type == 1 OR vr.gi_secondary_type == 1) AND vr.photonMap_mode == 1 do result = true
				if thePropName == #lightcache_loadFileName AND (vr.gi_primary_type == 3 OR vr.gi_secondary_type == 3) AND vr.lightcache_mode == 2 do result = true
			)
			--VRay RT properties:
			if rendererID == "vrayrt" do
			(
				vr = renderers.current.V_Ray_settings
				if thePropName == #lightcache_loadFileName AND (vr.gi_primary_type == 3 OR vr.gi_secondary_type == 3) AND vr.lightcache_mode == 2 do result = true
			)
			--Corona properties:
			if rendererID == "corona" do
			(
				cr = renderers.current
				if thePropName == #gi_hdCache_file AND (cr.gi_hdCache_precalcMode == 1 OR cr.gi_hdCache_precalcMode == 2) AND (cr.shading_secondarySolver == 3 OR cr.shading_secondarySolver == 4) do result = true
				--Corona 1.6 changed the property name by prefixing the letter: "u" (gi_hd -> gi_uhd)
				if thePropName == #gi_uhdCache_file AND (cr.gi_uhdCache_precalcMode == 1 OR cr.gi_uhdCache_precalcMode == 2) AND cr.shading_primarySolver == 1 AND cr.shading_secondarySolver == 4 do result = true
			)
			--Mental Ray properties:
			if rendererID == "mentalray" do 
			(
				mr = renderers.current
				if thePropName == #FinalGatherFilename AND mr.UseFinalGatherFile == true AND mr.FinalGatherFreeze == true do result = true
				--Max2010+ only feature: mr.PhotonFreeze
				if (maxVersion())[1]/1000 >= 12 then
					(if thePropName == #PhotonMapFilename AND (mr.CausticsEnable == true OR mr.GlobalIllumEnable == true) AND mr.PhotonMapUseFile  == true AND mr.PhotonFreeze  == true do result = true)
				else
					(if thePropName == #PhotonMapFilename AND (mr.CausticsEnable == true OR mr.GlobalIllumEnable == true) AND mr.PhotonMapUseFile  == true do result = true)
				if thePropName == #ShadowMapFilename AND mr.EnableShadowMaps  == true AND mr.UseShadowMapFile == true AND mr.ShadowMapRebuild == false do result = true
			)
			--Brazil 2 properties:
			if rendererID == "brmax" do
			(
				local brazilRenderer = ::sfs.b2_lib.getActiveB2() --Force global scope to access SplutterFish Script libraries!
				local blockNames = #("System_Options_Parameter_Block_Holder","Sampling_Parameter_Block_Holder","Motion_Blur_Parameter_Block_Holder","Ray_Server_Parameter_Block_Holder","Luma_Server_Parameter_Block_Holder","Render_Cache_Parameter_Block_Holder","Photon_Server_Parameter_Block_Holder","Render_Pass_Parameter_Block_Holder")
				if thePropName == #user_filename and brazilRenderer["Render_Cache_Parameter_Block_Holder"].file_mode == 2 do result = true
			)
			result
		),

		fn returnAllBitmaps =
		(
			--print "Collecting Bitmaps..."
			local allBitmaps = #()
			local bitmapsArray = #()
			local hdriArray = #()
			local theMaterials = #()

			SMTDExternalRefsArray.totalSubsArray = #()
			SMTDExternalRefsArray.storeBitmapPath = #()	-- #(object|undefined, original source path, actual source path after duplicate handling )
			SMTDExternalRefsArray.storeHdriPath = #()
			SMTDExternalRefsArray.StoreObjectXRefs = #()
			SMTDExternalRefsArray.StoreSceneXRefs = #()
			SMTDExternalRefsArray.StoreSceneVrayProxies = #()
			SMTDExternalRefsArray.StoreSceneCoronaProxies = #()
			SMTDExternalRefsArray.StoreSceneMRProxies = #()
			SMTDExternalRefsArray.StoreRendererPaths = #()
			SMTDExternalRefsArray.StoreBrazilv2RendererPaths = #()

			local collisions = 0
			local fileNamesForCollisionCheck = #()
			local pathNamesForCollisionCheck = #()
			
			st1 = timestamp()
			for o in objects do 
			(
				SMTDFunctions.collectSubAnims o
			)	
			try(SMTD_MainRollout.Ui_report ("+Traversed " + objects.count as string +" Objects and Collected "+ SMTDExternalRefsArray.totalSubsArray.count as string +" SubAnims in "+ ((timestamp()-st1)/1000.0) as string  + " sec."))catch()
			
			local theRenderer = SMTDFunctions.getRendererObject()
			local theProps = try(getPropNames theRenderer)catch(#())

			--DEALING WITH RENDERER PROPERTIES FOR BRAZIL 2:
			if SMTDFunctions.getRendererIdString() == "brmax" then
			(
				local brCounter = 0
				SMTDExternalRefsArray.StoreRendererPaths = #()
				local brazilRenderer = ::sfs.b2_lib.getActiveB2() --Force global scope to access SplutterFish Script libraries!
				local blockNames = #("System_Options_Parameter_Block_Holder","Sampling_Parameter_Block_Holder","Motion_Blur_Parameter_Block_Holder","Ray_Server_Parameter_Block_Holder","Luma_Server_Parameter_Block_Holder","Render_Cache_Parameter_Block_Holder","Photon_Server_Parameter_Block_Holder","Render_Pass_Parameter_Block_Holder")
				for blockName in blockNames do
				(
					local theBlock = brazilRenderer[blockName]
					if theBlock != undefined then
					(
						local propNames = getPropNames theBlock.object
						if propNames != undefined then
						(
							for p in propNames do
							(
								local theProp = (getProperty theBlock.object p)
								if superclassof theProp == TextureMap do
								(
									append theMaterials theProp
									brCounter += 1
								)
							)
						)
					)
				)--end blockName loop
				try(SMTD_MainRollout.Ui_report "")catch()
				case brCounter of
				(
					default: try(SMTD_MainRollout.Ui_report ("+Found "+ brCounter as string+ " Populated Brazil r/s v2 Texture Map Slots.") )catch()
					0: try(SMTD_MainRollout.Ui_report ("!!No Populated Brazil r/s v2 Texture Map Slots Found."))catch()
					1: try(SMTD_MainRollout.Ui_report ("+Found One Populated Brazil r/s v2 Texture Map Slot."))catch()
				)					
				
				
				theProp = brazilRenderer["Render_Cache_Parameter_Block_Holder"].user_filename
				if doesFileExist theProp and brazilRenderer["Render_Cache_Parameter_Block_Holder"].file_mode == 2 do 
				(
					if (SMTDSettings.SubmitExternalFilesMode == 2 and SMTDFunctions.IsLocalPath theProp) or (SMTDSettings.SubmitExternalFilesMode == 3) do 
					(
						append SMTDExternalRefsArray.StoreRendererPaths #(theProp, theProp)
						append SMTDExternalRefsArray.StoreBrazilv2RendererPaths #(brazilRenderer["Render_Cache_Parameter_Block_Holder"], #user_filename, theProp)
					)
				)	

				theProp = brazilRenderer["Photon_Server_Parameter_Block_Holder"].gi_user_filename
				if doesFileExist theProp and brazilRenderer["Photon_Server_Parameter_Block_Holder"].gi_file_mode == 2 do 
				(
					if (SMTDSettings.SubmitExternalFilesMode == 2 and SMTDFunctions.IsLocalPath theProp) or (SMTDSettings.SubmitExternalFilesMode == 3) do 
					(
						append SMTDExternalRefsArray.StoreRendererPaths #(theProp, theProp)
						append SMTDExternalRefsArray.StoreBrazilv2RendererPaths #(brazilRenderer["Photon_Server_Parameter_Block_Holder"], #gi_user_filename, theProp)
					)
				)	
				
				theProp = brazilRenderer["Photon_Server_Parameter_Block_Holder"].cst_user_filename
				if doesFileExist theProp and brazilRenderer["Photon_Server_Parameter_Block_Holder"].cst_file_mode == 2 do 
				(
					if (SMTDSettings.SubmitExternalFilesMode == 2 and SMTDFunctions.IsLocalPath theProp) or (SMTDSettings.SubmitExternalFilesMode == 3) do 
					(
						append SMTDExternalRefsArray.StoreRendererPaths #(theProp, theProp)
						append SMTDExternalRefsArray.StoreBrazilv2RendererPaths #(brazilRenderer["Photon_Server_Parameter_Block_Holder"], #cst_user_filename, theProp)
					)
				)	
				
			)
			else --DEALING WITH RENDERER PROPERTIES FOR VRAY, CORONA, MENTAL RAY
			(
				SMTDExternalRefsArray.StoreRendererPaths = for p in theProps collect 
				(
					local theProp = try(getProperty theRenderer p)catch(undefined)
					if (p != undefined) AND (classof theProp == String and doesFileExist theProp) AND (SMTDFunctions.isPropertyOKForSubmissionToRepository p) then
					(
						if SMTDSettings.SubmitExternalFilesMode == 2 then --if locals only, check and append if local.
							if SMTDFunctions.IsLocalPath theProp then #(p, theProp) else dontcollect
						else
							#(p, theProp)
					)
					else dontcollect
				)
			)
			
			local theRendererName = case (SMTDFunctions.getRendererIdString()) of
			(
				default: (classof theRenderer) as string
				"scanline": "Default Scanline Renderer"
				"brmax": "Brazil r/s v2 Renderer"
				"mentalray": "Mental Ray Renderer"
				"vray": "V-Ray Renderer"
				"vrayrt": "V-Ray RT Renderer"
				"corona": "Corona Renderer"
				"krakatoa": "Krakatoa Renderer"
			)
			local thePathType = case SMTDSettings.SubmitExternalFilesMode of
			(
				default: "Path"
				2: "Local Path"
			)
			try(SMTD_MainRollout.Ui_report "")catch()
			if SMTDExternalRefsArray.StoreRendererPaths.count == 0 then
				try(SMTD_MainRollout.Ui_report ("!!No "+ theRendererName + " " + thePathType + "s Collected." ))catch()
			else
				try(SMTD_MainRollout.Ui_report ("+Collected "+ SMTDExternalRefsArray.StoreRendererPaths.count as string + " "+ theRendererName + " " + thePathType + (if SMTDExternalRefsArray.StoreRendererPaths.count != 1 then "s." else ".")  ))catch()
			for o in SMTDExternalRefsArray.StoreRendererPaths do	
				try(SMTD_MainRollout.Ui_report ("\t["+o[2]+"] >> ["+ fileNameFromPath o[3] +"]") LogFileOnly:true )catch()

			for p in theProps where \
				(try(superclassof (getProperty theRenderer p) == textureMap)catch(false)) OR \
				(try(superclassof (getProperty theRenderer p) == material)catch(false)) \
				do append theMaterials (getProperty theRenderer p)
			for m in theMaterials do SMTDFunctions.collectSubAnims m

			for o in SMTDExternalRefsArray.totalSubsArray do
			(
				if classof o == Point_Cache do ( continue )
				if classof o == VRayProxy do ( continue )
				if classof o == CProxy do ( continue )
				if classof o == mr_Proxy do ( continue )
				if classof o == Point_CacheSpacewarpModifier do ( continue )
				
				if classof o.object == Point_Cache do ( continue )
				if classof o.object == Point_CacheSpacewarpModifier do ( continue )
				
				if (isProperty o #filename or isProperty o.object #filename) and findItem bitmapsArray o.object == 0 do
					append bitmapsArray o.object
				if (isProperty o #HDRIMapName or isProperty o.object #HDRIMapName) and findItem hdriArray o.object == 0 do
					append hdriArray o.object
			)
			
			for m in theMaterials where isProperty m #filename and findItem bitmapsArray m == 0 do append bitmapsArray m
			
			--now go through all bitmaps and collect unique bitmaps and IFL contents for copying
			local bitmapsArrayToProcess = #()
			for o in bitmapsArray do
			(
				if o.filename != undefined AND findItem allBitmaps o.filename == 0 do  --if not on the list yet,
				(
					if SMTDSettings.SubmitExternalFilesMode == 2 then --if locals only, check and append if local.
					(
						if SMTDFunctions.IsLocalPath o.filename do 
						(
							append allBitmaps o.filename
							append bitmapsArrayToProcess o
						)	
					)	
					else
					(
						append allBitmaps o.filename --if all, append every single one
						append bitmapsArrayToProcess o
					)
				)
				if o.filename != undefined AND matchPattern (getFileNameType o.filename) pattern:"*IFL" do
				(
					goOn = SMTDFunctions.IsLocalPath o.filename
					if SMTDSettings.SubmitExternalFilesMode >= 3 do goOn = true
					if goOn do
					(
						local filesInIFL = SMTDFunctions.getFilesFromIFL(o.filename)
						for filePath in filesInIFL do
						(
							if findItem allBitmaps filePath == 0 do 
							(
								append allBitmaps filePath
							)
							append SMTDExternalRefsArray.storeBitmapPath #(undefined, filePath, filePath)
							if findItem fileNamesForCollisionCheck (fileNameFromPath filePath) == 0 do
							(
								append fileNamesForCollisionCheck (fileNameFromPath filePath)
							)
						)
					)
				)
			)
			
			local hdriArrayToProcess = #()
			for o in hdriArray do
			(
				if o.HDRIMapName != undefined AND findItem allBitmaps o.HDRIMapName == 0 do  --if not on the list yet,
				(
					if SMTDSettings.SubmitExternalFilesMode == 2 then --if locals only, check and append if local.
					(
						if SMTDFunctions.IsLocalPath o.HDRIMapName do 
						(
							append allBitmaps o.HDRIMapName
							append hdriArrayToProcess o
						)	
					)	
					else
					(
						append allBitmaps o.HDRIMapName --if all, append every single one
						append hdriArrayToProcess o
					)
				)
				if o.HDRIMapName != undefined AND matchPattern (getFileNameType o.HDRIMapName) pattern:"*IFL" do
				(
					goOn = SMTDFunctions.IsLocalPath o.HDRIMapName
					if SMTDSettings.SubmitExternalFilesMode >= 3 do goOn = true
					if goOn do
					(
						local filesInIFL = SMTDFunctions.getFilesFromIFL(o.HDRIMapName)
						for filePath in filesInIFL do
						(
							if findItem allBitmaps filePath == 0 do
							(
								append allBitmaps filePath
							)
							append SMTDExternalRefsArray.storeBitmapPath #(undefined, filePath, filePath)
							if findItem fileNamesForCollisionCheck (fileNameFromPath filePath) == 0 do
							(
								append fileNamesForCollisionCheck (fileNameFromPath filePath)
							)
						)
					)
				)
			)

			local TextureCacheFolder = (dotnetclass "System.Environment").GetFolderPath (dotnetclass "System.Environment+SpecialFolder").CommonApplicationData + "\\PF_LocalVFXCache\\LocalTexturesCache\\"

			--Store original texture object and filename, then reset to filename only, no path:
			for o in bitmapsArrayToProcess do
			(
				local theTargetFilename = o.filename
				local theFilename = filenameFromPath theTargetFilename 
				local theIndex1 = findItem fileNamesForCollisionCheck theFilename 
				local theIndex2 = findItem pathNamesForCollisionCheck o.filename

				if theIndex1 > 0 and theIndex2 == 0 then --if the file name exists on the list but the whole path does not, we can assume this is a collision!
				(
					collisions += 1
					-- Ensure we have a unique filename before continuing to the next bitmap
					do
					(
						local guid = genClassID returnValue:true
						theTargetFilename = getFileNameFile o.filename + "_" + guid[1] as string + guid[2] as string + getFileNameType o.filename
						local index = findItem fileNamesForCollisionCheck theTargetFilename
					)
					while( index > 0 )

					theTargetFilename = SMTDPaths.submitSubFolder + theTargetFilename
					copyFile o.filename theTargetFilename
				)
				
				if theIndex1 == 0 and theIndex2 == 0 then --if both don't know the file, then it must be new, add it to both lists!
				(
					append fileNamesForCollisionCheck theFilename 
					append pathNamesForCollisionCheck o.filename
				)
				
				append SMTDExternalRefsArray.storeBitmapPath #(o, o.filename, theTargetFilename)
				if SMTDSettings.SubmitExternalFilesMode > 1 and SMTDSettings.SubmitExternalFilesMode < 4 do o.filename = fileNameFromPath theTargetFilename
				if SMTDSettings.SubmitExternalFilesMode == 4 do o.filename = SMTDFunctions.convertPathToLocal TextureCacheFolder theTargetFilename
			)
			
			for o in hdriArrayToProcess do
			(
				local theTargetFilename = o.HDRIMapName
				local theFilename = filenameFromPath theTargetFilename 
				local theIndex1 = findItem fileNamesForCollisionCheck theFilename 
				local theIndex2 = findItem pathNamesForCollisionCheck o.HDRIMapName

				if theIndex1 > 0 and theIndex2 == 0 then --if the file name exists on the list but the whole path does not, we can assume this is a collision!
				(
					collisions += 1
					-- Ensure we have a unique filename before continuing to the next hdri
					do
					(
						local guid = genClassID returnValue:true
						theTargetFilename = getFileNameFile o.HDRIMapName + "_" + guid[1] as string + guid[2] as string + getFileNameType o.HDRIMapName
						local index = findItem fileNamesForCollisionCheck theTargetFilename
					)
					while( index > 0 )

					theTargetFilename = SMTDPaths.submitSubFolder + theTargetFilename
					copyFile o.HDRIMapName theTargetFilename
				)
				
				if theIndex1 == 0 and theIndex2 == 0 then --if both don't know the file, then it must be new, add it to both lists!
				(
					append fileNamesForCollisionCheck theFilename 
					append pathNamesForCollisionCheck o.HDRIMapName
				)
				
				append SMTDExternalRefsArray.storeHdriPath #(o, o.HDRIMapName, theTargetFilename)
				if SMTDSettings.SubmitExternalFilesMode > 1 and SMTDSettings.SubmitExternalFilesMode < 4 do o.HDRIMapName = fileNameFromPath theTargetFilename
				if SMTDSettings.SubmitExternalFilesMode == 4 do o.HDRIMapName = SMTDFunctions.convertPathToLocal TextureCacheFolder theTargetFilename
			)
			
			--Report the result of the collection
			try(SMTD_MainRollout.Ui_report "")catch()
			local theLocalString = if SMTDSettings.SubmitExternalFilesMode == 2 then " Local" else ""
			case (bitmapsArrayToProcess.count + hdriArrayToProcess.count) of
			(
				default: try(SMTD_MainRollout.Ui_report ("+Collected "+ (bitmapsArrayToProcess.count + hdriArrayToProcess.count) as string+ theLocalString +" Scene Bitmaps with " + pathNamesForCollisionCheck.count as string + " unique "+(if pathNamesForCollisionCheck.count == 1 then "filename" else "filenames")+" and "+ collisions as string + " file name "+(if collisions == 1 then "collision." else "collisions.")  ))catch()
				0: try(SMTD_MainRollout.Ui_report ("!!No"+ theLocalString+" Scene Bitmaps Collected."))catch()
				1: try(SMTD_MainRollout.Ui_report ("+Collected One"+theLocalString+" Scene Bitmap."))catch()
			)
			
			--Dump All Bitmap Names to the Log File
			for o in SMTDExternalRefsArray.storeBitmapPath do 
				try(SMTD_MainRollout.Ui_report ("\t["+o[2]+"] >> ["+ fileNameFromPath o[3] +"]") LogFileOnly:true )catch()
			for o in SMTDExternalRefsArray.storeHdriPath do 
				try(SMTD_MainRollout.Ui_report ("\t["+o[2]+"] >> ["+ fileNameFromPath o[3] +"]") LogFileOnly:true )catch()
				
			/*
			for o in SMTDExternalRefsArray.storeBitmapPath do 
				try(SMTD_MainRollout.Ui_report ("\t["+o[2]+"] >> ["+ fileNameFromPath o[3] +"]") LogFileOnly:true )catch()
			*/

			--Append Renderer specific paths here to "storeBitmapPath" so it does not appear in bitmap list when printed to SMTD log
			for p in SMTDExternalRefsArray.StoreRendererPaths do
			(
				append SMTDExternalRefsArray.storeBitmapPath #(undefined, p[2], p[2]) 
				setProperty theRenderer p[1] (filenameFromPath p[2]) --remove the path
			)
			
			for o in SMTDExternalRefsArray.StoreBrazilv2RendererPaths do
			(
				append SMTDExternalRefsArray.storeBitmapPath #(undefined, o[3], o[3])
				setProperty o[1] o[2] (filenameFromPath o[3])
			)
			
			-- Collect VRay Proxy Objects
			if VRayProxy != undefined and SMTDSettings.SubmitExternalFilesMode > 1 do
			(
				SMTDExternalRefsArray.StoreSceneVrayProxies = #()
				local uniqueVRayProxyFiles = #()
				local uniqueVRayProxyPaths = #()
				local VRaycollisions = 0
				for o in getClassInstances VRayProxy do
				(
					if (SMTDSettings.SubmitExternalFilesMode == 2 AND SMTDFunctions.IsLocalPath o.filename) OR SMTDSettings.SubmitExternalFilesMode == 3 do 
					(
						local theTargetFilename = o.filename
						local theFilename = filenameFromPath theTargetFilename 
						local theIndex1 = findItem uniqueVRayProxyFiles theFilename
						local theIndex2 = findItem uniqueVRayProxyPaths o.filename
						if theIndex1 > 0 and theIndex2 == 0 then --if the file name appears on the file list but not on the paths list, then it is a duplicate with different path = collision!
						(
							VRaycollisions += 1
							theTargetFilename = SMTDPaths.submitSubFolder + getFileNameFile theTargetFilename + "_" + VRaycollisions as string + "_" + getFileNameType theTargetFilename
							append allBitmaps o.filename
							append uniqueVRayProxyPaths o.filename
							append SMTDExternalRefsArray.StoreSceneVrayProxies #(o, o.filename, theTargetFilename)
							copyFile o.filename theTargetFilename
						)
						else if theIndex1 == 0 and theIndex2 == 0 then --if it is on neither lists, then it is a new unique path to add
						(
							append uniqueVRayProxyFiles theFilename 
							append uniqueVRayProxyPaths o.filename
							append allBitmaps o.filename
							append SMTDExternalRefsArray.StoreSceneVrayProxies #(o, o.filename, o.filename)
						)
						else --if it is not a new or a collision, it is existing already, but we have to collect the file name for restoring 
						(
							append SMTDExternalRefsArray.StoreSceneVrayProxies #(o, o.filename, o.filename)
						)
						--append SMTDExternalRefsArray.storeBitmapPath #(o, o.filename, fileNameFromPath theTargetFilename)
						o.filename = fileNameFromPath theTargetFilename
					)--end copy to repository
					if SMTDSettings.SubmitExternalFilesMode == 4 do
					(
						theNetworkFileName = if SMTDFunctions.isPathInLocalCache TextureCacheFolder o.filename then
							SMTDFunctions.convertPathToRemote TextureCacheFolder o.filename
						else
							o.filename
						if findItem allBitmaps theNetworkFileName == 0 do append allBitmaps theNetworkFileName
						if not (SMTDFunctions.isPathInLocalCache TextureCacheFolder o.filename) do 
						(
							local theLocalPath = SMTDFunctions.convertPathToLocal TextureCacheFolder o.filename
							append SMTDExternalRefsArray.StoreSceneVrayProxies #(o, o.filename, theLocalPath)
							o.filename = theLocalPath 
						)
					)--end local cache on Slave
				)--end o loop
				try(SMTD_MainRollout.Ui_report "")catch()
				case uniqueVRayProxyPaths.count of
				(
					0:	try(SMTD_MainRollout.Ui_report ("!!No"+ (if SMTDSettings.SubmitExternalFilesMode == 2 then " Local " else " ")+ "V-Ray Proxies Collected." ))catch()
					1: try(SMTD_MainRollout.Ui_report ("+Collected One"+ (if SMTDSettings.SubmitExternalFilesMode == 2 then " Local " else " ")+ "V-Ray Proxy." ))catch()
					default: try(SMTD_MainRollout.Ui_report ("+Collected "+ uniqueVRayProxyPaths.count as string + " Unique" + (if SMTDSettings.SubmitExternalFilesMode == 2 then " Local " else " ")+ "V-Ray Proxies from "+ SMTDExternalRefsArray.StoreSceneVrayProxies.count as string +" Proxy Objects."  ))catch()
				)
				for o in SMTDExternalRefsArray.StoreSceneVrayProxies do	
					try(SMTD_MainRollout.Ui_report ("\t["+o[2]+"] >> ["+ fileNameFromPath o[3] +"]") LogFileOnly:true )catch()
			)

			-- Collect Corona Proxy Objects
			if CProxy != undefined and SMTDSettings.SubmitExternalFilesMode > 1 do
			(
				SMTDExternalRefsArray.StoreSceneCoronaProxies = #()
				local uniqueCoronaProxyFiles = #()
				local uniqueCoronaProxyPaths = #()
				local Coronacollisions = 0
				for o in getClassInstances CProxy do
				(
					if (SMTDSettings.SubmitExternalFilesMode == 2 AND SMTDFunctions.IsLocalPath o.filename) OR SMTDSettings.SubmitExternalFilesMode == 3 do 
					(
						local theTargetFilename = o.filename
						local theFilename = filenameFromPath theTargetFilename 
						local theIndex1 = findItem uniqueCoronaProxyFiles theFilename
						local theIndex2 = findItem uniqueCoronaProxyPaths o.filename
						if theIndex1 > 0 and theIndex2 == 0 then --if the file name appears on the file list but not on the paths list, then it is a duplicate with different path = collision!
						(
							Coronacollisions += 1
							theTargetFilename = SMTDPaths.submitSubFolder + getFileNameFile theTargetFilename + "_" + Coronacollisions as string + "_" + getFileNameType theTargetFilename 
							append allBitmaps o.filename
							append uniqueCoronaProxyPaths o.filename
							append SMTDExternalRefsArray.StoreSceneCoronaProxies #(o, o.filename, theTargetFilename)
							copyFile o.filename theTargetFilename
						)
						else if theIndex1 == 0 and theIndex2 == 0 then --if it is on neither lists, then it is a new unique path to add
						(
							append uniqueCoronaProxyFiles theFilename
							append uniqueCoronaProxyPaths o.filename
							append allBitmaps o.filename
							append SMTDExternalRefsArray.StoreSceneCoronaProxies #(o, o.filename, o.filename)
						)
						else --if it is not a new or a collision, it is existing already, but we have to collect the file name for restoring 
						(
							append SMTDExternalRefsArray.StoreSceneCoronaProxies #(o, o.filename, o.filename)
						)
						--append SMTDExternalRefsArray.storeBitmapPath #(o, o.filename, fileNameFromPath theTargetFilename)
						o.filename = fileNameFromPath theTargetFilename
					)--end copy to repository
					if SMTDSettings.SubmitExternalFilesMode == 4 do
					(
						theNetworkFileName = if SMTDFunctions.isPathInLocalCache TextureCacheFolder o.filename then
							SMTDFunctions.convertPathToRemote TextureCacheFolder o.filename
						else
							o.filename
						if findItem allBitmaps theNetworkFileName == 0 do append allBitmaps theNetworkFileName
						if not (SMTDFunctions.isPathInLocalCache TextureCacheFolder o.filename) do 
						(
							local theLocalPath = SMTDFunctions.convertPathToLocal TextureCacheFolder o.filename
							append SMTDExternalRefsArray.StoreSceneCoronaProxies #(o, o.filename, theLocalPath)
							o.filename = theLocalPath 
						)
					)--end local cache on Slave
				)--end o loop
				try(SMTD_MainRollout.Ui_report "")catch()
				case uniqueCoronaProxyPaths.count of
				(
					0:	try(SMTD_MainRollout.Ui_report ("!!No"+ (if SMTDSettings.SubmitExternalFilesMode == 2 then " Local " else " ")+ "Corona Proxies Collected." ))catch()
					1: try(SMTD_MainRollout.Ui_report ("+Collected One"+ (if SMTDSettings.SubmitExternalFilesMode == 2 then " Local " else " ")+ "Corona Proxy." ))catch()
					default: try(SMTD_MainRollout.Ui_report ("+Collected "+ uniqueCoronaProxyPaths.count as string + " Unique" + (if SMTDSettings.SubmitExternalFilesMode == 2 then " Local " else " ")+ "Corona Proxies from "+ SMTDExternalRefsArray.StoreSceneCoronaProxies.count as string +" Proxy Objects."  ))catch()
				)
				for o in SMTDExternalRefsArray.StoreSceneCoronaProxies do	
					try(SMTD_MainRollout.Ui_report ("\t["+o[2]+"] >> ["+ fileNameFromPath o[3] +"]") LogFileOnly:true )catch()
			)

			-- Collect Mental Ray Proxy Objects
			if mr_Proxy != undefined and SMTDSettings.SubmitExternalFilesMode > 1 do
			(
				SMTDExternalRefsArray.StoreSceneMRProxies = #()
				local uniqueMRProxyFiles = #()
				local uniqueMRProxyPaths = #()
				local mrcollisions = 0
				for o in getClassInstances mr_Proxy do
				(
					if (SMTDSettings.SubmitExternalFilesMode == 2 AND SMTDFunctions.IsLocalPath o.filename) OR SMTDSettings.SubmitExternalFilesMode == 3 do 
					(
						local theTargetFilename = o.filename
						local theFilename = filenameFromPath theTargetFilename 
						local theIndex1 = findItem uniqueMRProxyFiles theFilename
						local theIndex2 = findItem uniqueMRProxyPaths o.filename
						if theIndex1 > 0 and theIndex2 == 0 then --if the file name appears on the file list but not on the paths list, then it is a duplicate with different path = collision!
						(
							mrcollisions += 1
							theTargetFilename = getFileNameFile theTargetFilename + "_" + mrcollisions as string + "_" + getFileNameType theTargetFilename 
							if o.animated == true then
							(
								local theAnimationFiles = SMTDFunctions.GetAnimationFiles o.filename
								for f in theAnimationFiles do
								(
									append allBitmaps f
									append uniqueMRProxyPaths f
								)
								append SMTDExternalRefsArray.StoreSceneMRProxies #(o, o.filename, theTargetFilename)
							)
							else
							(
								append allBitmaps o.filename
								append uniqueMRProxyPaths o.filename
								append SMTDExternalRefsArray.StoreSceneMRProxies #(o, o.filename, theTargetFilename)
							)
						)
						else if theIndex1 == 0 and theIndex2 == 0 then --if it is on neither lists, then it is a new unique path to add
						(
							if o.animated == true then
							(
								local theAnimationFiles = SMTDFunctions.GetAnimationFiles o.filename
								for f in theAnimationFiles do
								(
									append uniqueMRProxyFiles (filenameFromPath f) 
									append uniqueMRProxyPaths f
									append allBitmaps f
								)
								append SMTDExternalRefsArray.StoreSceneMRProxies #(o, o.filename, theFilename)
							)
							else
							(
								append uniqueMRProxyFiles theFilename 
								append uniqueMRProxyPaths o.filename
								append allBitmaps o.filename
								append SMTDExternalRefsArray.StoreSceneMRProxies #(o, o.filename, theFilename)
							)
						)
						else --if it is not a new or a collision, it is existing already, but we have to collect the file name for restoring 
						(
							append SMTDExternalRefsArray.StoreSceneMRProxies #(o, o.filename, o.filename)
						)
						o.filename = fileNameFromPath theTargetFilename
					)--end copy to repository
					if SMTDSettings.SubmitExternalFilesMode == 4 do
					(
						theNetworkFileName = if SMTDFunctions.isPathInLocalCache TextureCacheFolder o.filename then
							SMTDFunctions.convertPathToRemote TextureCacheFolder o.filename
						else
							o.filename
						if findItem allBitmaps theNetworkFileName == 0 do append allBitmaps theNetworkFileName
						if not (SMTDFunctions.isPathInLocalCache TextureCacheFolder o.filename) do 
						(
							local theLocalPath = SMTDFunctions.convertPathToLocal TextureCacheFolder o.filename
							append SMTDExternalRefsArray.StoreSceneMRProxies #(o, o.filename, theLocalPath)
							o.filename = theLocalPath 
						)
					)--end local cache on Slave
				)--end o loop
				try(SMTD_MainRollout.Ui_report "")catch()
				case uniqueMRProxyPaths.count of
				(
					0:	try(SMTD_MainRollout.Ui_report ("!!No"+ (if SMTDSettings.SubmitExternalFilesMode == 2 then " Local " else " ")+ "mental ray Proxy Files Collected." ))catch()
					1: try(SMTD_MainRollout.Ui_report ("+Collected One"+ (if SMTDSettings.SubmitExternalFilesMode == 2 then " Local " else " ")+ "mental ray Proxy File." ))catch()
					default: try(SMTD_MainRollout.Ui_report ("+Collected "+ uniqueMRProxyPaths.count as string + " Unique" + (if SMTDSettings.SubmitExternalFilesMode == 2 then " Local " else " ")+ "mental ray Proxy Files from "+ SMTDExternalRefsArray.StoreSceneMRProxies.count as string +" Proxy Objects."  ))catch()
				)
				for o in SMTDExternalRefsArray.StoreSceneMRProxies do	
					try(SMTD_MainRollout.Ui_report ("\t["+o[2]+"] >> ["+ fileNameFromPath o[3] +"]") LogFileOnly:true )catch()
			)		

			--Do the same for XRefs
			SMTDExternalRefsArray.StoreSceneXRefs = #()
			if not SMTDSettings.MergeSceneXRefsOnSubmission then
			(
				for i = 1 to (xrefs.getXRefFileCount()) do
				(
					o = (xrefs.getXRefFile i)
					local shouldBeCollected = (not o.disabled) AND (doesfileexist o.filename) AND ((SMTDSettings.SubmitExternalFilesMode == 2 AND SMTDFunctions.IsLocalPath o.filename) OR SMTDSettings.SubmitExternalFilesMode == 3)
					append SMTDExternalRefsArray.StoreSceneXRefs #(o, o.filename, o.filename, shouldBeCollected)
					if shouldBeCollected do --only collect if not disabled and the Scene XREF actually exists!
					(
						append allBitmaps o.filename
						o.filename = fileNameFromPath o.filename
					)
				)
				try(SMTD_MainRollout.Ui_report "")catch()
				local activeXRefsCount = (for o in SMTDExternalRefsArray.StoreSceneXRefs where o[4] collect o).count
				case activeXRefsCount of
				(
					default: try(SMTD_MainRollout.Ui_report ("+Collected "+ activeXRefsCount as string +" Scene XREFs."))catch()
					0: (
						try(SMTD_MainRollout.Ui_report ("!!No Scene XREFs Collected."))catch()
					)
					1: try(SMTD_MainRollout.Ui_report ("+Collected One Scene XREF."))catch()
				)

				for o in SMTDExternalRefsArray.StoreSceneXRefs where o[4] do
					try(SMTD_MainRollout.Ui_report ("\t["+o[2]+"] >> "+"["+o[3]+"]") LogFileOnly:true )catch()
			)
			else
			(
				try(SMTD_MainRollout.Ui_report ("!!Merge Scene XREF Requested, Collecting Skipped."))catch()
				SMTDSettings.nonFatalErrorsCount+=1
			)
			
			if not SMTDSettings.MergeXRefsOnSubmission then 
			(
				SMTDExternalRefsArray.StoreObjectXRefs = #()
				for o in (objXrefs.getAllXRefObjects()) do
				(
					if (SMTDSettings.SubmitExternalFilesMode == 2 AND SMTDFunctions.IsLocalPath o.filename) OR SMTDSettings.SubmitExternalFilesMode == 3 do --if local and locals only, or if all paths wanted
					(
						append SMTDExternalRefsArray.StoreObjectXRefs #(o, o.filename, o.filename)
						o.filename = fileNameFromPath o.filename
					)
				)	
				
				local uniquePaths = #()
				for o in SMTDExternalRefsArray.StoreObjectXRefs where findItem uniquePaths o[2] == 0 do append uniquePaths o[2]
				for o in uniquePaths do append allBitmaps o
				
				try(SMTD_MainRollout.Ui_report "")catch()
				case SMTDExternalRefsArray.StoreObjectXRefs.count of
				(
					default: (
						if uniquePaths.count != 1 then
							try(SMTD_MainRollout.Ui_report ("+Collected "+ SMTDExternalRefsArray.StoreObjectXRefs.count as string +" Object XREFs with "+ uniquePaths.count as string + " Unique Paths."))catch()
						else
							try(SMTD_MainRollout.Ui_report ("+Collected "+ SMTDExternalRefsArray.StoreObjectXRefs.count as string +" Object XREFs with One Unique Path."))catch()
					)
					0: (
						try(SMTD_MainRollout.Ui_report ("!!No Object XREFs Collected."))catch()
						)
					1: try(SMTD_MainRollout.Ui_report ("+Collected One Object XREF."))catch()
				)
				
				for o in uniquePaths do
				(
					try(SMTD_MainRollout.Ui_report ("\t["+o+"] >> ["+fileNameFromPath o +"]") LogFileOnly:true )catch()
					for i in SMTDExternalRefsArray.StoreObjectXRefs where i[2] == o do
						try(
							SMTD_MainRollout.Ui_report ("\t\t["+i[1].objectName +"]") LogFileOnly:true 
						)catch()
				)
			)
			else
			(
				try(SMTD_MainRollout.Ui_report ("!!Merge Object XREF Requested, Collecting Skipped."))catch()
				SMTDSettings.nonFatalErrorsCount+=1
			)					
			try(SMTD_MainRollout.Ui_report "")catch()
					
			allBitmaps
		),
		
		fn restoreExternalReferencePaths =
		(
			--Restore Bitmaps
			for o in SMTDExternalRefsArray.storeBitmapPath where o[1] != undefined do o[1].filename = o[2]
			for o in SMTDExternalRefsArray.storeHdriPath where o[1] != undefined do o[1].HDRIMapName = o[2]
			
			--Restore Scene XRefs
			for i = 1 to (xrefs.getXRefFileCount()) do
			(
				local o = (xrefs.getXRefFile i)
				o.filename = SMTDExternalRefsArray.StoreSceneXRefs[i][2]
			)
			
			--Restore Object XRefs
			for o in SMTDExternalRefsArray.StoreObjectXRefs do o[1].filename = o[2]
			
			--Restore VRay Proxies
			if VRayProxy != undefined and SMTDSettings.SubmitExternalFilesMode > 1 do
				for o in SMTDExternalRefsArray.StoreSceneVrayProxies do o[1].filename = o[2]

			--Restore Corona Proxies
			if CProxy != undefined and SMTDSettings.SubmitExternalFilesMode > 1 do
				for o in SMTDExternalRefsArray.StoreSceneCoronaProxies do o[1].filename = o[2]			

			--Restore mr Proxies
			if mr_Proxy != undefined and SMTDSettings.SubmitExternalFilesMode > 1 do
				for o in SMTDExternalRefsArray.StoreSceneMRProxies do o[1].filename = o[2]
				
			--Restore Renderer Paths
			for o in SMTDExternalRefsArray.StoreRendererPaths do
			(
				local theRenderer = SMTDFunctions.getRendererObject()
				try(setProperty theRenderer o[1] o[2])catch()
			)
			
			--Restore Brazil 2 Paths
			for o in SMTDExternalRefsArray.StoreBrazilv2RendererPaths do
			(
				setProperty o[1] o[2] o[3]
			)			
		),
		
		fn createExternalFilesList filesList =
		(
			local ExternalFilesListName = getFileNamePath SMTDPaths.JobInfoFile + "\\ExternalFilesList.txt"
			local theListOfExternalFiles = "" as StringStream
			for aFile in filesList do format "%\n" aFile to:theListOfExternalFiles 
			(dotNetClass "System.IO.File").WriteAllText ExternalFilesListName (theListOfExternalFiles as string)
			ExternalFilesListName
		),
		
		fn ExportAnima2Anipack =
		(
			SMTDExternalRefsArray.StoreAnimaPaths= #()
			local AnimaDummies = try(getClassInstances anima2scene)catch(#())
			local anipacksToSubmit = #()
			for o in AnimaDummies do
			(
				local st = timestamp()
				if SMTDSettings.SubmitExternalFilesMode == 3 OR (SMTDSettings.SubmitExternalFilesMode == 2 and (SMTDFunctions.IsLocalPath o.anima2projectpath)) do
				(
					try(SMTD_MainRollout.Ui_report (">Processing Anima2 Scene Helper ["+(refs.dependentNodes o)[1].name+"]"))catch()
					local theNewFile = getFileNamePath SMTDPaths.JobInfoFile + getFileNameFile o.anima2projectpath + ".anipack"
					append SMTDExternalRefsArray.StoreAnimaPaths #(o,o.anima2projectpath)
					o.saveanipack = theNewFile
					o.anima2projectpath = filenameFromPath o.anima2projectpath
					if doesFileExist theNewFile then
					(
						append anipacksToSubmit theNewFile
						local fileSize = getFileSize theNewFile
						fileSize /= 1024.0*1024.0
						try(SMTD_MainRollout.Ui_report ("+Saved Anima2 assets to file ["+filenameFromPath theNewFile+"] of size "+fileSize as string+" MB in "+((timestamp()-st)/1000.0) as string + " sec." ))catch()
					)
					else
					(
						try(SMTD_MainRollout.Ui_report ("--Failed to Save Anima2 assets to ["+filenameFromPath theNewFile+"]"))catch()
					)
				)
			)--end o loop
			anipacksToSubmit
		),
		
		fn restoreAnima2Paths =
		(
			if SMTDExternalRefsArray.StoreAnimaPaths.count > 0 do
				try(SMTD_MainRollout.Ui_report (">Restoring Anima2 Project Paths..."))catch()
			for o in SMTDExternalRefsArray.StoreAnimaPaths do o[1].anima2projectpath = o[2]
		),
		
		fn ReplaceSequenceNumber theFilename theFrame wildcard:"" =
		(
			local theNewFilename = theFilename
			local theBaseName = getFileNameFile theFilename
			local digitCount = 0
			local done = false
			for i = theBaseName.count to 1 by -1 while not done do 
			(
				local asciiCode = bit.charAsInt theBaseName[i]
				if asciiCode >= 48 and asciiCode <= 57 then digitCount += 1 else done = true
			)
			if digitCount > 0 then 
			(
				theNewFilename = getFileNamePath theFilename + substring theBaseName 1 (theBaseName.count-digitCount) 
				case wildcard of
				(
					default: (theNewFilename += (formattedPrint theFrame format:("0"+digitCount as string+"i")) )
					"*": (theNewFilename += "*" )
					"#": (theNewFilename += (substring "###################" 1 digitCount) )
				)
				theNewFilename += getFileNameType theFilename
			)
			else
			(
				theNewFilename = getFileNamePath theFilename + theBaseName
				case wildcard of
				(
					default: (theNewFilename += (formattedPrint theFrame format:"04i") )
					"*": (theNewFilename += "*" )
					"#": (theNewFilename += "####" )
				)
				theNewFilename += getFileNameType theFilename				
			)
			theNewFilename
		),
		
		--ASSET SYNC CHANGES START
		fn PRTLoaderRequiredRenderFrames aPRTLoader testFilename =
		(
			renderSceneDialog.commit()
			local theFilesList = aPRTLoader.fileList
			local theIndex = findItem aPRTLoader.fileList testFilename
			local renderFrames = SMTDFunctions.GetFrameSequenceArray()
			local filenamesToLoad = #()			
			if theIndex > 0 and aPRTLoader.fileListFlags[theIndex] > 1 do --if the file is set to enabled in renderer...
			(
				if doesFileExist testFilename do
				(
					if aPRTLoader.loadSingleFrame then 
						filenamesToLoad = #(testFilename)
					else
					(
						if SMTDSettings.AssetSyncAllFiles then
						(
							local theSequencePattern = SMTDFunctions.ReplaceSequenceNumber testFilename 0 wildcard:"*"
							filenamesToLoad = getFiles (theSequencePattern)
						)
						else
						(
							for aFrame in renderFrames do
							(
								local theActualFrame = aFrame + aPRTLoader.frameOffset
								if aPRTLoader.enablePlaybackGraph do theActualFrame = at time aFrame aPRTLoader.playbackGraphTime + aPRTLoader.frameOffset
								if aPRTLoader.limitToRange do
								(
									if theActualFrame < aPRTLoader.rangeStartFrame do theActualFrame = aPRTLoader.rangeStartFrame
									if theActualFrame > aPRTLoader.rangeEndFrame do theActualFrame = aPRTLoader.rangeEndFrame
								)
								appendIfUnique filenamesToLoad (SMTDFunctions.ReplaceSequenceNumber testFilename ((floor (theActualFrame+0.5)) as integer))
							)
						)
					)
				)
			)
			filenamesToLoad
		),		

		fn StokeFieldLoaderRequiredRenderFrames theLoader testFilename =
		(
			renderSceneDialog.commit()
			local renderFrames = SMTDFunctions.GetFrameSequenceArray()
			local filenamesToLoad = #()			
			if theLoader.FilenamePattern == testFilename do 
			(
				if doesFileExist testFilename do
				(
					if not theLoader.SubstituteSequenceNumber then 
						filenamesToLoad = #(testFilename)
					else
					(
						if SMTDSettings.AssetSyncAllFiles then
						(
							local theSequencePattern = SMTDFunctions.ReplaceSequenceNumber testFilename 0 wildcard:"*"
							filenamesToLoad = getFiles theSequencePattern
						)
						else
						(
							for aFrame in renderFrames do
							(
								local theActualFrame = aFrame + theLoader.PlaybackOffset
								if theLoader.UsePlaybackTime do theActualFrame = at time aFrame theLoader.PlaybackTime + theLoader.PlaybackOffset
								if theLoader.UsePlaybackRange do
								(
									if theActualFrame < theLoader.PlaybackRangeStart do theActualFrame = theLoader.PlaybackRangeStart
									if theActualFrame > theLoader.PlaybackRangeEnd do theActualFrame = theLoader.PlaybackRangeEnd
								)
								appendIfUnique filenamesToLoad (SMTDFunctions.ReplaceSequenceNumber testFilename ((floor (theActualFrame+0.5)) as integer))
							)
						)
					)
				)
			)
			filenamesToLoad
		),			

		fn PointCacheRequiredRenderFrames aPCache testFilename:"" thePath:"" theNamePattern:"" theType:"" =
		(
			renderSceneDialog.commit()
			local theBaseFilename = aPCache.filename
			local renderFrames = SMTDFunctions.GetFrameSequenceArray()
			local filenamesToLoad = #()
			if doesFileExist theBaseFilename and (testFilename == "" OR theBaseFilename == testFilename) do
			(		
				for aFrame in renderFrames do
				(
					case aPCache.playbackType of
					(
						default: (
							appendIfUnique filenamesToLoad (thePath+theNamePattern + aFrame as string + theType)
						)							
						1: (
							if aFrame >= aPCache.playbackStart do 
								appendIfUnique filenamesToLoad (thePath+theNamePattern + aFrame as string + theType)
						)
						2: (
							if aFrame >= aPCache.playbackStart AND aFrame <= aPCache.playbackEnd do 
								appendIfUnique filenamesToLoad (thePath+theNamePattern + aFrame as string + theType)
						)
						3: (
							theActualFrame = at time aFrame aPCache.playbackFrame
							appendIfUnique filenamesToLoad (thePath + theNamePattern + ((floor (theActualFrame+0.5)) as integer) as string + theType)
						)
					)
				)
			)
			filenamesToLoad
		),	
		
		fn XMeshRequiredRenderFrames = --Collect XMesh sequences and all their data files
		(
			local st = timestamp()
			local theFiles = #()
			local theDataFiles = #()
			local theFilesToReturn = #()
			
			local BasePathCache = #()
			local ChannelMapCache = #()
			
			local theXMeshLoaders = try(getClassInstances XMeshLoader)catch(#())
			if theXMeshLoaders.count > 0 do 
			(
				local renderFrames = SMTDFunctions.GetFrameSequenceArray()
				local theMessage = ">Processing "+theXMeshLoaders.count as string +" XMesh Loader"+(if theXMeshLoaders.count == 1 then "" else "s")+"..."
				try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)
				local cnt = 0
				for anXMeshLoader in theXMeshLoaders do
				(
					cnt+=1
					local st1 = timestamp()
					local dataFiles = #()
					local dataFilesCollected = #()
					local theBaseFilename = anXMeshLoader.renderSequence
					if anXMeshLoader.renderSequenceID == 1 do theBaseFilename = anXMeshLoader.proxySequence					
					if doesFileExist theBaseFilename do
					(
						local thePattern = SMTDFunctions.ReplaceSequenceNumber theBaseFilename 0 wildcard:"*"
						local theIndex = findItem BasePathCache thePattern
						if theIndex == 0 then
						(
							local thePath = getFileNamePath theBaseFilename --get the resolved path of the file
							for theLine in ((dotNetClass "System.IO.File" ).ReadAllLines theBaseFilename) do
							(
								join dataFiles (for i in (filterString theLine "</>") where matchPattern i pattern:"*.xmdat" collect (thePath + i) )
							)--end theLine loop
							append BasePathCache thePattern
							append ChannelMapCache dataFiles
						)
						else
						(
							dataFiles = ChannelMapCache[theIndex]
						)
					)
					--format "%\n" dataFiles
					local filenamesToLoad = #()
					if theBaseFilename != undefined do
					(		
						if anXMeshLoader.loadSingleFrame then
						(
							filenamesToLoad = #(theBaseFilename)
							dataFilesCollected = deepCopy dataFiles
						)
						else
						(
							if SMTDSettings.AssetSyncAllFiles then
							(
								local theSequencePattern = SMTDFunctions.ReplaceSequenceNumber theBaseFilename 0 wildcard:"*"
								filenamesToLoad = getFiles theSequencePattern
								for aData in dataFiles do
								(								
									local theSequencePattern = SMTDFunctions.ReplaceSequenceNumber aData 0 wildcard:"*"
									join dataFilesCollected (getFiles theSequencePattern)
								)
							)
							else
							(
								for aFrame in renderFrames do
								(
									local theActualFrame = aFrame + anXMeshLoader.frameOffset
									if anXMeshLoader.enablePlaybackGraph do theActualFrame = at time aFrame anXMeshLoader.playbackGraphTime + anXMeshLoader.frameOffset
									if anXMeshLoader.limitToRange do
									(
										if theActualFrame < anXMeshLoader.rangeFirstFrame do theActualFrame = anXMeshLoader.rangeFirstFrame
										if theActualFrame > anXMeshLoader.rangeLastFrame do theActualFrame = anXMeshLoader.rangeLastFrame
									)
									append filenamesToLoad (SMTDFunctions.ReplaceSequenceNumber theBaseFilename ((floor (theActualFrame+0.5)) as integer))
									join dataFilesCollected (for aData in dataFiles collect (SMTDFunctions.ReplaceSequenceNumber aData ((floor (theActualFrame+0.5)) as integer)) )
								)
							)
						)
						for i in filenamesToLoad do appendIfUnique theFiles i
						for i in dataFilesCollected do appendIfUnique theDataFiles i
						try(windows.processPostedMessages())catch()
						local theMessage = " +XMesh Loader "+ cnt as string + " of " + theXMeshLoaders.count as string+ " - " +filenamesToLoad.count as string+" XMesh Header file"+(if filenamesToLoad.count == 1 then "" else "s")+ " and " + dataFilesCollected.count as string+" XMesh Data file"+(if dataFilesCollected.count == 1 then "" else "s in "+((timestamp()-st1)/1000.0) as string +" seconds.")
						try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)
					)--end if basename valid
				)--end xMeshLoaders loop
				
				local theMessage = "+Collected "+theFiles.count as string+" unique XMesh Header file"+(if theFiles.count == 1 then "" else "s")
				try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)
				local theMessage = "+Collected "+theDataFiles.count as string+" unique XMesh Data file"+(if theDataFiles.count == 1 then "" else "s")
				try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)
				
				join theFiles theDataFiles
				for aFile in theFiles where doesFileExist aFile do appendIfUnique theFilesToReturn aFile
				local theMessage = "+Collected "+ theFilesToReturn.count as string +" unique XMesh Files in "+(((timestamp()-st))/1000.0) as string+" seconds."
				try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)
			)--end if XMesh Loaders present			
			theFilesToReturn
		),		
		
		fn PhoenixFDRequiredRenderFrames =
		(
			local thePhoenixObjects = for o in objects where isKindOf o FireSmokeSim or isKindOf o LiquidSim or isKindOf o VRayVolumeGrid collect o			
			local renderFrames = SMTDFunctions.GetFrameSequenceArray()
			local filenamesToLoad = #()			
			for aPhoenixObject in thePhoenixObjects do
			(
				local theBaseFilename = if matchPattern aPhoenixObject.rendinput pattern:"$(same_as_output)" then
				(
					if matchPattern aPhoenixObject.simoutput pattern:"$(scene_dir)" then 
						maxFilePath+maxFileName+"_Phoenix2_frames\\ND"+aPhoenixObject.inode.handle as string+"_"+aPhoenixObject.name+"_####.aur"
					else
						aPhoenixObject.simoutput
				)
				else
					aPhoenixObject.rendinput
				
				if SMTDSettings.AssetSyncAllFiles then
				(
					theBaseFilename = substituteString theBaseFilename "#" "0"
					local theSequencePattern = SMTDFunctions.ReplaceSequenceNumber theBaseFilename 0 wildcard:"*"
					for i in (sort (getFiles (theSequencePattern))) do appendIfUnique filenamesToLoad i
				)
				else
				(
					local theLength = aPhoenixObject.playat+aPhoenixObject.inplength
					if aPhoenixObject.inplength == 0 do theLength = 10^8
					for aFrame in renderFrames do
					(
						if aFrame >= aPhoenixObject.playat and aFrame <= theLength do
						(
							theBaseFilename = substituteString theBaseFilename "#" "0"
							local theActualFrame = aPhoenixObject.inpoffset + ((aFrame - aPhoenixObject.playat)*aPhoenixObject.play_speed)
							local theFile = (SMTDFunctions.ReplaceSequenceNumber theBaseFilename ((floor (theActualFrame+0.5)) as integer)) 
							if doesFileExist theFile do appendIfUnique filenamesToLoad theFile
						)
					)
				)
			)--end fire loop
			filenamesToLoad
		),
		
		fn VRayRequiredRenderFrames =
		(
			local theFiles = #()
			local theVRayHDRI = try(getClassInstances VRayHDRI)catch(#())
			local VRayTokens = #(#("<UDIM>","*"),#("<UVTILE>","*"),#("$U","*"),#("$V","*")) 
			for i = 2 to 9 do 
			(
				append VRayTokens #(("$" + i as string + "U"), substring "??????????" 1 i)
				append VRayTokens #(("$" + i as string + "V"), substring "??????????" 1 i)
			)
			for aMap in theVRayHDRI do 
			(
				local theFilename = aMap.HDRIMapName
				if theFilename == undefined do continue
				
				for aToken in VRayTokens do
				(
					theFilename = substituteString  theFilename aToken[1] aToken[2]
					theFilename = substituteString  theFilename (toLower aToken[1]) aToken[2]
				)
				if matchPattern theFilename pattern:"*<*>*" do --if there are any custom tags in the filename,
				(
					local theNodes = refs.dependentNodes aMap	--get all scene nodes that depend on the texture
					for aNode in theNodes do					--for each node,
					(
						local theFilename2 = copy theFilename	--start with a copy of the filename
						local theFS = filterString theFilename2 "<>" splitEmptyTokens:true	--and split it to an array of tokens separated by < or >
						-- for example, if the path is C:\Users\bobo\Documents\3dsMax\renderoutput\testbobo.<objecttag><tag2>.0000.exr
						-- it splits to #("C:\Users\bobo\Documents\3dsMax\renderoutput\testbobo.", "objecttag", "", "tag2", ".0000.exr")
						-- so all even entries in the array are the tokens we want to process, and the odd ones are to be skipped.
						for j = 2 to theFS.count by 2 do 		--start with the second token and skip every 2nd token
						(
							local val = getUserProp aNode theFS[j]	--get the User Property named like the token of the current node
							if val != undefined and val != "" do	--and if it is not invalid or empty,
							(
								theFilename2 = substituteString theFilename2 ("<"+theFS[j]+">") val	--replace the custom tag with the object property value
							)
						)
						join theFiles (getFiles theFilename2)		--and collect the files matching that filename
					)--end node loop
				)
				join theFiles (getFiles theFilename)
			)
			theFiles
		),
		
		fn RealFlowRequiredRenderFrames =
		(
			local renderFrames = SMTDFunctions.GetFrameSequenceArray()
			local filenamesToLoad = #()			
			local theRFObjects = for o in objects where isKindOf o ParticleLoader collect o
			for anObject in theRFObjects do
			(
				local existingFiles = sort (getFiles (anObject.binPath +"\\"+ anObject.binPrefix+ "*.bin"))
				if existingFiles.count > 0 do
				(
					local theBaseFilename = existingFiles[1]
					if SMTDSettings.AssetSyncAllFiles then
					(
						for i in existingFiles do appendIfUnique filenamesToLoad i
					)
					else
					(
						for aFrame in renderFrames do
						(
							local theActualFrame =  aFrame-anObject.FrameOffset
							local theFile = (SMTDFunctions.ReplaceSequenceNumber theBaseFilename theActualFrame)
							if doesFileExist theFile do appendIfUnique filenamesToLoad theFile
						)
					)				
				)
			)--end particle loader loop
			local theRFObjects = for o in objects where isKindOf o MeshLoader collect o
			for anObject in theRFObjects do
			(
				local existingFiles = sort (getFiles (anObject.path +"\\"+ anObject.Prefix+ "*.bin"))
				if existingFiles.count > 0 do
				(
					local theBaseFilename = existingFiles[1]
					if SMTDSettings.AssetSyncAllFiles then
					(
						for i in existingFiles do appendIfUnique filenamesToLoad i
					)
					else
					(
						for aFrame in renderFrames do
						(
							local theActualFrame = aFrame-anObject.Start+anObject.Offset
							if not (anObject.useStop and aFrame > anObject.Stop) do
							(
								local theFile = (SMTDFunctions.ReplaceSequenceNumber theBaseFilename theActualFrame)
								if doesFileExist theFile do appendIfUnique filenamesToLoad theFile
							)
						)
					)				
				)
			)--end particle loader loop			
			filenamesToLoad
		),		
		
		fn resolveOutputAssetsFromAssetTracker =
		(
			renderSceneDialog.commit()															--make sure the Render Dialog is updated
			ATSOps.Refresh() 																	--make sure the Asset Tracker is updated
			local FileList = #() 																--initialize the array to get the paths into
			ATSOps.GetFiles &FileList  															--get the paths into the array
			FileList = for f in FileList where not ATSOps.IsInputFile f collect f 				--filter only output assets
			local ResolvedFileList = #() 														--initialize an array for the resolved assets
			ATSOps.GetResolvedPaths &FileList &ResolvedFileList 								--resolve all paths
			ResolvedFileList = for f in ResolvedFileList where f != undefined collect toLower f --filter out invalid or inaccessible file names
		),
		
		fn resolveAssetsFromAssetTracker SubmitExternalFilesMode:3 =
		(
			-- Currently supports all Asset Tracker single files,
			-- plus additional special handling for:
			-- IFL image lists
			-- FXD sequences incl. corresponding FDC file from FumeFX simulators
			-- PhoenixFD files
			-- FXD, VDB and F3D sequences from Stoke Field Loader objects
			-- PRT, BIN, RPC, XYZ and all other PRT Loader sequences
			-- XMesh sequences incl. all data files
			-- BIN in RealFlow Particle and Mesh Loaders
			-- AUR, VDB, F3D in VRayVolumeGrid
			if SubmitExternalFilesMode < 1 or SubmitExternalFilesMode > 3 do return #()
			try(SMTD_MainRollout.Ui_report (">Resolving External Files Using Asset Tracker..."))catch()
			
			local st1 = timestamp()																--get the current system time
			renderSceneDialog.commit()															--commit the current render settings to ensure the time range is calculated correctly
			ATSOps.Refresh() 																	--make sure the Asset Tracker is updated
			local FileList = #() 																--initialize the array to get the paths into
			ATSOps.GetFiles &FileList  															--get the paths into the array
			FileList = for f in FileList where ATSOps.IsInputFile f and filenameFromPath f != maxFileName collect f --filter only input assets
			local ResolvedFileList = #() 														--initialize an array for the resolved assets
			ATSOps.GetResolvedPaths &FileList &ResolvedFileList 								--resolve all paths
			ResolvedFileList = for f in ResolvedFileList where f != undefined and doesFileExist f collect f --filter out invalid or inaccessible file names
			local theMessage = "+Asset Tracker Resolved "+ ResolvedFileList.count as string + (if ResolvedFileList.count == 1 then " File" else " Files") + " in "+(((timestamp()-st1))/1000.0) as string+" seconds."
			try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)			--report how long it took to get the assets from AT
			local dependentFileList = #() 														--collect files referenced by the resolved files (e.g. XMDat files, PRT sequence files, IFL image files etc.)
			for f in ResolvedFileList do 														--go through the collected file names
			(
				if matchPattern (getFileNameType f) pattern:".IFL" do 							--if the extension is IFL, it is an image file list and we also need to collect all referenced files 
				(
					local goOn = SMTDFunctions.IsLocalPath f									--check to see if the path is local to decide whether to process
					if SubmitExternalFilesMode !=2 do goOn = true								--if submitting only local paths was not requested, override the decision
					if goOn do																	--if the file should be processed,
					(
						local filesInIFL = SMTDFunctions.getFilesFromIFL(f)
						for filePath in filesInIFL do
						(
							appendIfUnique dependentFileList filePath
						)
					)--end if goOn
				)--end if IFL
				
				if matchPattern (getFileNameType f) pattern:".MC" and matchPattern (getFileNameFile f) pattern:"*Frame*" do --if the extension is MC and the file name contains "Frame", this is probably a multi-file Point Cache
				(
					local theMessage = ">Processing Possible Point Cache File Sequence ["+ f + "]"	--create a message to inform the user
					try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)		--and show it in the log or Listener
					local thePath = getFileNamePath f												--get the path of the file
					local theName = getFileNameFile f												--get the file name without path and extension
					local theType = getFileNameType f												--get the extension only
					local theNamePattern = substring theName 1 ((findString theName "Frame")+4)		--get the base file name without the frame number suffix
					if SMTDSettings.AssetSyncAllFiles then											--if the synching of all files was requested
					(
						local theFiles = getFiles (thePath + theNamePattern + "*" + theType)		--collect all files of the sequence
					)
					else																			--if only the required subset of files was requested,
					(
						local theFiles = #()														--initialize an array to collect files
						local thePointCaches = getClassInstances Point_Cache						--get all point cache instances from the scene
						local theTestPattern = thePath + substring theNamePattern 1 (theNamePattern.count-5) + ".xml"	--figure out the XML file a Point Cache would use for this sequence
						for aPCache in thePointCaches do											--loop through all point caches to see which one uses the test pattern, and collect the actual sequence list
							for i in (SMTDFunctions.PointCacheRequiredRenderFrames aPCache testFilename:theTestPattern thePath:thePath theNamePattern:theNamePattern theType:theType) where doesFileExist i do appendIfUnique theFiles i					
					)
					for aFile in theFiles do appendIfUnique dependentFileList aFile					--append all unique files to the dependent file list
				)--end if multi-frame point cache
				
				if matchPattern (getFileNameType f) pattern:".FXD" do 								--if the extension is FXD, it is most probably part of a FumeFX sequence, and we also need to collect the .FDC file
				(
					local theMessage = ">Processing Possible FumeFX File Sequence ["+ f + "]"		--report to the user that a possible FXD sequence was found
					try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)
					local theSequencePattern = SMTDFunctions.ReplaceSequenceNumber f 0 wildcard:"*"	--build a file name pattern to get the whole sequence
					if SMTDSettings.AssetSyncAllFiles then											--if the collection of all files was requested,
					(
						local theFiles = getFiles (theSequencePattern)								--collect all matching files
					)
					else																			--if only the required files should be collected,
					(
						local renderFrames = SMTDFunctions.GetFrameSequenceArray()					--get the list of all frames to be rendered
						local theFiles = for aFrame in renderFrames where doesFileExist (aFile = SMTDFunctions.ReplaceSequenceNumber f aFrame) collect aFile	--collect all files that match those frame numbers
					)
					for aFile in theFiles do appendIfUnique dependentFileList aFile					--append the unique files to the dependent file list
					local theFiles = getFiles (getFileNamePath theSequencePattern + getFileNameFile theSequencePattern + ".fdc" )	--also look for the FDC file matching the file sequence
					for aFile in theFiles do appendIfUnique dependentFileList aFile					--and add the FDC file to the dependent file list
				)
				
				if (isKindOf StokeGlobalInterface Interface) and findItem #(".vdb",".fxd",".f3d") (toLower (getFileNameType f)) > 0 do --if Stoke is installed, and the extension is VDB, F3D or FXD, it could be part of a Stoke Field Loader sequence
				(
					local theMessage = ">Processing Possible Stoke File Sequence ["+ f + "]"
					try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)
					local theSequencePattern = SMTDFunctions.ReplaceSequenceNumber f 0 wildcard:"*"
					if SMTDSettings.AssetSyncAllFiles then
					(
						local theFiles = getFiles (theSequencePattern)
					)
					else
					(
						local frameOwnerFound = false
						local theFiles = #()
						local theFieldLoaders = try(getClassInstances Stoke_Field_Loader_Base)catch(#())
						for aLoader in theFieldLoaders do
						(
							local theLoaderFrames = (SMTDFunctions.StokeFieldLoaderRequiredRenderFrames aLoader f)
							if theLoaderFrames.count > 0 do 
							(
								frameOwnerFound = true
								for i in theLoaderFrames do if doesFileExist i do appendIfUnique theFiles i					
							)
						)
						if not frameOwnerFound do
						(
							local renderFrames = SMTDFunctions.GetFrameSequenceArray()
							for aFrame in renderFrames where doesFileExist (aFile = SMTDFunctions.ReplaceSequenceNumber f aFrame) do appendIfUnique theFiles aFile
						)
					)
						
					for aFile in theFiles do appendIfUnique dependentFileList aFile					
				)
				
				--Process Krakatoa PRT Loader inputs (one reference file used for the whole sequence)
				if FranticParticles != undefined AND findItem #(".prt",".csv",".bin",".rpc",".xyz",".pts",".ptx") (toLower (getFileNameType f)) > 0 do --if the extension is a valid PRT Loader input, collect all other files of the sequence 
				(
					local theMessage = ">Processing Possible PRT Loader File Sequence ["+ f + "]"
					try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)
					local theFiles = #()
					local thePath = getFileNamePath f --get the resolved path of the file
					local thePRTLoaders = try(getClassInstances KrakatoaPRTLoader)catch(#())
					for aPRTLoader in thePRTLoaders do
						for i in (SMTDFunctions.PRTLoaderRequiredRenderFrames aPRTLoader f) do if doesFileExist i do appendIfUnique theFiles i					
					
					local goOn = SMTDFunctions.IsLocalPath f
					if SubmitExternalFilesMode != 2 do goOn = true
					if goOn do
						for aFile in theFiles do appendIfUnique dependentFileList aFile
				)--end if PRT Loader sequence
				
				if matchPattern (getFileNameType f) pattern:".xmesh" do	-- If Asset Tracker collected an XMesh file, let's collect all files if the XMesh Loader was XREF-ed, or all files were requested.
				(
					local theMessage = ">Processing Possible XMesh File Sequence ["+ f + "]"
					try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)						
					local collectAllFiles = SMTDSettings.AssetSyncAllFiles == true
					if not collectAllFiles do -- if collecting all scene files was not requested, we must look for existing XMesh Loaders
					(
						local pathFound = false -- we assume the path does not exist in the scene
						for anXMeshLoader in getClassInstances XMeshLoader do -- then we check all XMesh Loader instances to see if they use that path
						(
							local theBaseFilename = anXMeshLoader.renderSequence --normally we only care for the render sequence
							if anXMeshLoader.renderSequenceID == 1 do theBaseFilename = anXMeshLoader.proxySequence	--unless the proxy sequence is set to render
							if toLower theBaseFilename == toLower f do pathFound = true --if the path is used by the loader, we raise the flag
						)
						if not pathFound do --if no XMesh Loader claimed that file, we can assume it ended up in the Asset Tracker via a Scene XREF
						(
							collectAllFiles = true --we raise the flag to force the collection of all XMesh and XMDat files matching the referenced file
							local theMessage = ">No matching XMesh Loader found, assuming a Scene XREF! Collecting All Available Files..."
							try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)	
						)
					)
					if collectAllFiles do -- if collecting all files was triggered by user request or a scene XRef,
					(
						local theFiles = getFiles (SMTDFunctions.ReplaceSequenceNumber f 0 wildcard:"*") --collect all files matching the pattern
						local goOn = SMTDFunctions.IsLocalPath f 
						if SubmitExternalFilesMode != 2 do goOn = true
						if goOn do
						(
							local dataFiles = #()
							for aFile in theFiles do 
							(
								appendIfUnique dependentFileList aFile	
								local thePath = getFileNamePath aFile
								for theLine in ((dotNetClass "System.IO.File" ).ReadAllLines aFile) do
									join dataFiles (for i in (filterString theLine "</>") where matchPattern i pattern:"*.xmdat" collect (thePath + i) )
							)
							for aFile in dataFiles do appendIfUnique dependentFileList aFile
						)		
					)--end if collectAllFiles
				)--end if an XMesh

				try(windows.processPostedMessages())catch()
			)--end f loop
			
			if SMTDSettings.AssetSyncAllFiles == false do join dependentFileList (SMTDFunctions.XMeshRequiredRenderFrames()) --only collect XMesh from scene objects if not already collected via Asset Tracker
			join dependentFileList (SMTDFunctions.PhoenixFDRequiredRenderFrames())
			join dependentFileList (SMTDFunctions.RealFlowRequiredRenderFrames())
			join dependentFileList (SMTDFunctions.VRayRequiredRenderFrames())	
			for f in dependentFileList do appendIfUnique ResolvedFileList f
			if SubmitExternalFilesMode == 2 do 												--if only local files should be collected,
				ResolvedFileList = for f in ResolvedFileList where (SMTDFunctions.IsLocalPath f) collect f 	--filter the list from local files
			local theMessage = "+Resolved "+ ResolvedFileList.count as string + (if ResolvedFileList.count == 1 then " File" else " Files")+" in "+(((timestamp()-st1))/1000.0) as string+" seconds."
			try(SMTD_MainRollout.Ui_report theMessage)catch(format "%\n" theMessage)
			sort ResolvedFileList											--sort the files in alphabetical order
			ResolvedFileList 												--return the resolved paths
		),
		
		fn GetAnimationBaseCount theBaseName =
		(
			local lastDigit = 0
			for i = theBaseName.count to 1 by -1 do
				if findString "1234567890" theBaseName[i] == undefined do lastDigit = i; exit
			lastDigit
		),
		
		fn GetAnimationFiles theFilePath =
		(
			local theBaseName = getFileNameFile theFilePath 
			local lastDigit = SMTDFunctions.GetAnimationBaseCount theBaseName
			getFiles (thePathPattern = getFileNamePath theFilePath + substring theBaseName 1 lastDigit + "*" + getFileNameType theFilePath)
		),
		
		fn RenameTargetAnimationFile theSource theTarget =
		(
			local theBaseName1 = getFileNameFile theSource 
			local lastDigit1 = SMTDFunctions.GetAnimationBaseCount theBaseName1
			local theBaseName2 = getFileNameFile theTarget 
			local lastDigit2 = SMTDFunctions.GetAnimationBaseCount theBaseName2
			local theNumber = if lastDigit1 < theBaseName1.count then 
				(substring theBaseName1 (lastDigit1+1) -1 )
			else 
				""
			getFileNamePath theTarget + (substring theBaseName2 1 lastDigit2)  + theNumber + getFileNameType theTarget
		),		
		
		--Returns the frame sequence string
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
					1:		format "%" frameNumbers[curIndex] to:seqString
					2:		format "%,%" frameNumbers[baseIndex] frameNumbers[curIndex] to:seqString
					default:	format "%-%" frameNumbers[baseIndex] frameNumbers[curIndex] to:seqString
				)
				if (curIndex != frameNumbers.count) do format "," to:seqString
				curIndex += 1
			)
			--try(SMTD_MainRollout.Ui_report ">Sequence String:" )catch()
			--try(SMTD_MainRollout.Ui_report (seqString as string) )catch()
			seqString as string
		),
		
		--Returns the out of order sequence
		fn outOfOrderSequence theFramesArray mode:#both =
		(
			local startArray = #()
			
			local step = if mode != #both then
				1.0*(theFramesArray.count-1) / (SMTDSettings.PreviewJobFrameCount - 1)
			else
				SMTDSettings.outOfOrderStep
				
			for i = 1 to theFramesArray.count by step do
				append startArray theFramesArray[i]
			local endArray = for i = 1 to theFramesArray.count where findItem startArray theFramesArray[i] == 0 collect theFramesArray[i]
			case mode of
			(
				#both: startArray + endArray 
				#nth: startArray 
				#rest: endArray 
			)	
		),
		
		fn outOfOrderMethod theFramesArray theMethod:#normal =
		(
			case theMethod of
			(
				default: theFramesArray
				#normal: theFramesArray
				#reverse: for i = theFramesArray.count to 1 by -1 collect theFramesArray[i]
				#lastAndFirst:
				(
					if theFramesArray.count < 3 then
						theFramesArray
					else
					(
						local temp = #()
						append temp theFramesArray[1]
						append temp theFramesArray[theFramesArray.count]
						for i = 2 to (theFramesArray.count - 1) do
							append temp theFramesArray[i]
						temp
					)
				)
				#nth:
				(
					local startArray = #()
					local theStep = SMTDSettings.outOfOrderStep
					for i = 1 to theFramesArray.count by theStep do
						append startArray theFramesArray[i]
					local endArray = for i = 1 to theFramesArray.count where findItem startArray theFramesArray[i] == 0 collect theFramesArray[i]
					startArray + endArray 
				)
				#fromBothEnds: 
				(
					local temp = #()
					for i = 1 to theFramesArray.count / 2 do 
					(
						append temp theFramesArray[i]
						append temp theFramesArray[theFramesArray.count - i + 1]
					)	
					for i in theFramesArray where findItem temp i == 0 do append temp i --make sure nothing was left behind
					temp
				)
				#fromBothEndsAndCenter:
				(
					local temp = #()
					for i = 1 to theFramesArray.count / 4 do 
					(
						append temp theFramesArray[i]
						append temp theFramesArray[theFramesArray.count - i + 1]
						append temp theFramesArray[theFramesArray.count / 2 - i + 1]
						append temp theFramesArray[theFramesArray.count / 2 + i]
					)	
					for i in theFramesArray where findItem temp i == 0 do append temp i --make sure nothing was left behind
					temp
				)
				#fromCenter:
				(
					local temp = #()
					for i = theFramesArray.count / 2 to 1 by -1 do 
					(
						append temp theFramesArray[i]
						append temp theFramesArray[theFramesArray.count - i + 1]
					)	
					for i in theFramesArray where findItem temp i == 0 do append temp i --make sure nothing was left behind
					temp					
				)
				#NthBlock: 
				(
					local temp = #()
					theStep = SMTDSettings.outOfOrderStep
					theBlockSize = theFramesArray.count/theStep
					for i = 1 to theBlockSize do
						for j = 0 to theStep-1  do
							append temp theFramesArray[i+j*theBlockSize]
					for i in theFramesArray where findItem temp i == 0 do append temp i --make sure nothing was left behind	
					temp 
				)
				#NthRasterRefine:
				(
					local temp = #()
					local theStep = SMTDSettings.outOfOrderStep
					while theStep > 1 do
					(
						for i = 1 to theFramesArray.count by theStep where findItem temp theFramesArray[i] == 0 do
							append temp theFramesArray[i]
						theStep /=	 2
					)		
					for i = 1 to theFramesArray.count where findItem temp theFramesArray[i] == 0 do append temp theFramesArray[i]
					temp 
				)
				#random:
				(
					local temp = #()
					local temp2 = for i in theFramesArray collect i
					--seed 12345
					while temp2.count > 0 do 
					(
						theIndex = random 1 temp2.count
						append temp temp2[theIndex]
						deleteItem temp2 theIndex
					)
					temp
				)
			)--end case
		),

		fn DeleteEmptyStateSets = 
		(
			if not SMTDSettings.StateSetsSubmit do
			(
				try
				(
					local ssP = try(dotNetObject "Autodesk.Max.StateSets.Plugin")catch(undefined)
					if ssP == undefined do ssP = try(dotNetObject "Ephere.Plugins.Autodesk.Max.Zookeeper.Plugin")catch(undefined)
					if ssP != undefined then
					(
						local ssPi = ssP.Instance
						StateSetsRootEntry = ssPi.EntityManager.RootEntity
						if StateSetsRootEntry.Children.count > 0 then
						(
							-- 3dsmax 2015 added the boolean parameter to GetDescendantStateSetPaths()
							StateSetsChildren = #()
							if( ((maxVersion())[1]/1000 as integer) >= 17 ) then
								StateSetsChildren = StateSetsRootEntry.Children.Item[0].GetDescendantStateSetPaths(false)
							else
								StateSetsChildren = StateSetsRootEntry.Children.Item[0].GetDescendantStateSetPaths()
							
							EmptySS = (for i in 1 to StateSetsChildren.count where (StateSetsChildren.Item[i-1][1].IsEmpty == True) collect n).count == StateSetsChildren.count

							if EmptySS do
							(
								-- hide & reset State Sets dialog
								ssPi.HideMainFrame()
								with quiet on ssPi.ResetAndDelete()
								try(SMTD_MainRollout.Ui_report ("+Empty State Sets have been Deleted"))catch()
							)
						)
					)
				)catch()
			)
		),

		fn SaveMaxFileCopy destFileName useMaxHold:false =
		(
			try(SMTD_MainRollout.sld_lastSubmissionState.value = 50)catch()

			if not SMTDSettings.StateSetsSubmit AND SMTDSettings.DeleteEmptyStateSets do SMTDFunctions.DeleteEmptyStateSets()
			
			if useMaxHold then
			(
				local holdMaxDir = (GetDir #autoback) + "\\"
				local holdFileName = if maxOps.productAppID == #max then --still works in Max2016 after Design has been retired
					holdMaxDir + "maxhold.mx"
				else
					holdMaxDir + "vizhold.mx"
		
				local holdTempFileName = holdMaxDir + "maxhold.tmp"
				local holdExists = doesFileExist holdFileName
				
				if holdExists then 
				(
					deleteFile holdTempFileName
					renameFile holdFileName holdTempFileName
				)
		
				holdMaxFile()
				
				if not (doesFileExist holdFileName) do 
				(
					SMTDSettings.FatalErrorsCount += 1
					return ("--Saving the file as ["+ holdFileName +"] via hold() did not work.")
				)
				
				deleteFile destFileName --need to remove any old file before copying over
				if not (renameFile holdFileName destFileName) do
				(
					if not (copyFile holdFileName destFileName) do
					(
						SMTDSettings.FatalErrorsCount += 1
						return ("--Could not copy the saved scene file to " + destFileName)
					)
				)
				
				if holdExists do
				(
					deleteFile holdFileName
					renameFile holdTempFileName holdFileName
				)				
			)
			else
			(
				saveMaxFile destFileName clearNeedSaveFlag:false useNewFile:false quiet:true
				if not (doesFileExist destFileName) do 
				(
					SMTDSettings.FatalErrorsCount += 1
					return ("--Saving the file as ["+ destFileName +"] did not work.")
				)
			)
			return undefined
		),

		fn RestoreMaxFileCopy sourceFileName =
		(
			local holdMaxDir = (GetDir #autoback) + "/"
			local holdFileName = if maxOps.productAppID == #max then --still works in Max2016 after Design has been retired
				holdMaxDir + "maxhold.mx"
			else
				holdMaxDir + "vizhold.mx"			
			local holdTempFileName = holdMaxDir + "maxhold.tmp"
			local holdExists = doesFileExist holdFileName
			
			if holdExists then
			(
				deleteFile holdTempFileName
				renameFile holdFileName holdTempFileName
			)
			
			copyFile sourceFileName holdFileName
			if not (doesFileExist holdFileName) do return "Restoring the file via fetch() did not work." 
			
			fetchMaxFile quiet:true
			
			if holdExists do
			(
				deleteFile holdFileName
				renameFile holdTempFileName holdFileName
			)
			return undefined
		),	
		
		fn collectSceneMaterials =
		(
			try(SMTD_MainRollout.Ui_report (">Enumerating Scene Objects and Materials"))catch()
			SMTD_SceneMaterials = for o in objects collect #(o, o.material, o.colorByLayer)
		),
		
		fn assignCustomShaders =
		(
			case SMTDSettings.CustomShaderMode of
			(
				1: (
					objects.material = standard()
					shaderType = "Standard Grayscale Shader"
				)	
				2: (
					objects.material = undefined
					shaderType = "Object Wireframe Colors"
				)
				3: (
					objects.material = undefined
					objects.colorByLayer = true
					shaderType = "Layer Colors"
				)	
				4: (
					if superclassof meditmaterials[1] == Material then 
					(
						objects.material = meditmaterials[1] 
						shaderType = "Material Editor Slot 1"
					)
					else 
					(
						objects.material = standard()
						shaderType = "Standard Grayscale Material Instead Of Medit Slot 1"
					)	
				)	
			)	
			try(SMTD_MainRollout.Ui_report ("+Assigned "+ shaderType +" To Scene Objects"))catch()
		),
		
		fn restoreSceneMaterials =
		(
			for o in SMTD_SceneMaterials do 
			(
				o[1].material = o[2]
				o[1].colorByLayer = o[3]
			)	
			SMTD_SceneMaterials =#()
			try(SMTD_MainRollout.Ui_report ("+Restored Materials Of Scene Objects"))catch()
		),
		fn clearMaterialEditor =
		(
			global SMTDSettings_MeditMaterialsStorage = for i = 1 to 24 collect meditMaterials[i]
			for i = 1 to 24 do meditMaterials[i] = standard()
		),
		
		fn restoreMaterialEditor =
		(
			for i = 1 to 24 do try(meditMaterials[i] = SMTDSettings_MeditMaterialsStorage[i])catch()
		),
		
		fn HasActiveSceneXRefs =
		(
			theCount = xrefs.getXRefFileCount()
			(for i = 1 to theCount where not (xrefs.getXRefFile i).disabled collect i).count > 0
		),
		
		fn SaveMaxFileVisibleOnly destFileName =
		(
			try(SMTD_MainRollout.sld_lastSubmissionState.value = 50)catch()
			if not SMTDSettings.StateSetsSubmit AND SMTDSettings.DeleteEmptyStateSets do SMTDFunctions.DeleteEmptyStateSets()
			--COLLECT ALL GEOMETRY THAT IS VISIBLE TO CAMERA OR REFLECTIONS
			local theNodesToSave = for o in objects where findItem geometryClass.classes (classof o) > 0 AND (not o.isHiddenInVpt and o.renderable and (o.primaryVisibility or o.secondaryVisibility)) collect o
			format "Submitting % Geometry Object(s)\n" theNodesToSave.count
			--ADD ALL LIGHTS,CAMERAS, HELPERS AND NODES ENABLED AS BONES
			join theNodesToSave (for o in objects where findItem Light.classes (classof o) > 0 OR findItem Camera.classes (classof o) > 0 OR findItem Helper.classes (classof o) > 0 or o.boneEnable == true collect o)

			--ADD RENDERABLE SHAPES 
			join theNodesToSave (for o in objects where findItem Shape.classes (classof o) > 0 AND (try(o.baseobject.renderable)catch(true)) collect o)

			format "Submitting TOTAL: % of %\n" theNodesToSave.count objects.count
			--SAVE THE COLLECTED OBJECTS - ANY DEPENDENTS WILL ALSO BE SAVED AUTOMATICALLY
			saveNodes theNodesToSave destFileName
			if doesFileExist destFileName then 
				undefined 
			else 
				"Saving Of Visible Objects Only Failed."
		),
		
		fn RenderElementsStoreVrayVFB =
		(
			global SMTD_RenderElementVrayVFB = #()
			
			local reManager = maxOps.GetCurRenderElementMgr()
			if reManager != undefined do
			(
				local reCount = reManager.NumRenderElements()
				for i = 0 to reCount - 1 do
				(
					local reCurr = (reManager.GetRenderElement i)
					if classof reCurr != Missing_Render_Element_Plug_in AND hasProperty reCurr "vrayVFB" then
						SMTD_RenderElementVrayVFB[i+1] = reCurr.vrayVFB
					else
						SMTD_RenderElementVrayVFB[i+1] = false --Just a place holder!
				)
			)
		),
		
		fn RenderElementsUpdateVrayVFB =
		(
			local reManager = maxOps.GetCurRenderElementMgr()
			if reManager != undefined do
			(
				if reManager.GetElementsActive() then 
				(
					local reCount = reManager.NumRenderElements()
					for i = 0 to reCount - 1 do
					(
						local reCurr = (reManager.GetRenderElement i)
						if classof reCurr != Missing_Render_Element_Plug_in AND hasProperty reCurr "vrayVFB" do
						(
							if reCurr.vrayVFB do
							(
								try(SMTD_MainRollout.Ui_report ("+Disabling V-Ray Frame Buffer for render element " + reCurr.elementName))catch()
								reCurr.vrayVFB = false
							)
						)
					)
				)
			)
		),
		
		fn RenderElementsRestoreVrayVFB =
		(
			if classof SMTD_RenderElementVrayVFB == Array do
			(
				local reManager = maxOps.GetCurRenderElementMgr()
				if reManager != undefined do
				(
					local reCount = reManager.NumRenderElements()
					for i = 0 to reCount - 1 do
					(
						local reCurr = (reManager.GetRenderElement i)
						if classof reCurr != Missing_Render_Element_Plug_in AND hasProperty reCurr "vrayVFB" do
						(
							local currVrayVFB = SMTD_RenderElementVrayVFB[i+1]
							if currVrayVFB == true do
							(
								try(SMTD_MainRollout.Ui_report ("+Reenabling V-Ray Frame Buffer for render element " + reCurr.elementName))catch()
								reCurr.vrayVFB = true
							)
						)
					)
				)
			)
		),
		
		fn RenderElementsStorePaths =
		(
			local reManager = maxOps.GetCurRenderElementMgr()
			if reManager != undefined do
			(
				local reCount = reManager.NumRenderElements()
				global SMTD_RenderElementPaths = #()
				for i = 0 to reCount - 1 do
				(
					if classof (reManager.GetRenderElement i) != Missing_Render_Element_Plug_in do
						SMTD_RenderElementPaths[i+1] = reManager.GetRenderElementFilename i
				)
			)
		),

		fn ReturnVraySplitPath oldPath elementType:"" =
		(
			--oldPath = renderers.current.output_splitfilename
			--elementType = "RGB_color" or "Alpha"
			local fileName = (getFileNameFile oldPath)
			local fileExtension = (getFileNameType oldPath)
			local newPath = (getFileNamePath oldPath)

			if (isProperty renderers.current #output_separateFolders and renderers.current.output_separateFolders == true) then --if VRay saving separate folders, add the element type as a sub-folder
				newPath = newPath+elementType+"\\"
			else
				if SMTDSettings.LocalRendering == true and SMTDSettings.RenderElementsIncludeNameInPath == true do  --if VRay is not saving separate folders, and SMTD is doing local rendering with sub-folders, add the element type as a sub-folder
					newPath = newPath+elementType+"\\"
			--If Local Rendering is off and VRay is not controlling the folder structure, then VRay will simply save all elements in the Split Output folder, ignoring Render Element names or SMTD custom names. So SMTD cannot modify the path in this case.
				
			newPath = newPath+fileName+fileExtension

			if SMTDSettings.purifyFilenames do newPath = SMTDFunctions.purifyFilename newPath 
			if SMTDSettings.ForceLowerCaseFilenames do newPath = toLower newPath

			local newDir = (getFileNamePath newPath)

			--makeDir newDir all:true --create directory

			return newPath
		),
		fn RenderElementsPathUpdater outputFilename overrideReFilename:False =
		(
			local processedNames = #()
			local processedNamesUsage = #()
			local reManager = maxOps.GetCurRenderElementMgr()
			if reManager != undefined do
			(
				if reManager.GetElementsActive() then
				(
					local reCount = reManager.NumRenderElements()
					for i = 0 to reCount - 1 do
					(
						reObject = reManager.GetRenderElement i
						if classof reObject != Missing_Render_Element_Plug_in do
						(
							local reFilename = reManager.GetRenderElementFilename i
							
							--Override reFilename if V-Vray VFB enabled and Split Channels is enabled
							if overrideReFilename then reFilename = outputFilename
							
							
							--Prefix render element with State Set name if not prefixed yet
							--if SMTDSettings.StateSetsSubmit and SMTDSettings.StateSetRenameOutput  and not matchPattern (getFilenameFile reFilename) pattern:(SMTDSettings.StateSetName +"_*")  do
								--reFilename = getFileNamePath reFilename + SMTDSettings.StateSetName +"_"+(getFilenameFile reFilename) + (getFilenameType reFilename)

							local theElement = reManager.GetRenderElement i
							if SMTDSettings.RenderElementsUpdateFilenames then
							(
								local theIndex = findItem processedNames theElement.elementName
								if theIndex == 0 then
								(
									append processedNames theElement.elementName 
									append processedNamesUsage 1
								)
								else
								(
									processedNamesUsage[theIndex] += 1
									theElement.elementName += processedNamesUsage[theIndex] as string
								)
							)
							
							local theElementFolder = ""
							
							-- If including both RE type and name in the folder, then separate with an underscore
							if SMTDSettings.RenderElementsIncludeNameInPath and SMTDSettings.RenderElementsIncludeTypeInPath then
								theElementFolder = theElement.elementName + "_" + (classof theElement) as string 
							else
							(
								-- See if either the RE type or name is stored in the folder.
								if SMTDSettings.RenderElementsIncludeNameInPath do
									theElementFolder = theElement.elementName
								if SMTDSettings.RenderElementsIncludeTypeInPath do
									theElementFolder = (classof theElement) as string
							)
							if (hasProperty theElement "vrayVFB" and theElement.vrayVFB) do
							(
								if (isProperty renderers.current #output_separateFolders and renderers.current.output_separateFolders == true) then
									theElementFolder = theElement.elementName
								else
									if SMTDSettings.LocalRendering == false do theElementFolder = "" --if rendering VRay without local rendering and V-Ray is not making sub-folders, we must override the element folder to empty string!
							)
							
							-- Build up the new path, and only include the element folder if it's been set above
							local newPath = (getFileNamePath outputFilename)
							if theElementFolder != "" do
								newPath += theElementFolder
							
							if SMTDSettings.purifyFilenames do newPath = SMTDFunctions.purifyFilename newPath 
							if SMTDSettings.ForceLowerCaseFilenames do newPath = toLower newPath
							
							--create directory if RE is enabled or in the case of V-Ray VFB, if 'vrayVFB' property is enabled
							--if theElement.enabled OR (hasProperty theElement "vrayVFB" and theElement.vrayVFB) do
								--if not ((isProperty renderers.current #output_separateFolders and renderers.current.output_separateFolders == true)) do 
									--makeDir newPath all:true
							
							if SMTDSettings.RenderElementsUpdateFilenames then
							(
								local theNewFileName = (newPath +"\\" + getFileNameFile outputFilename)
								
								-- See if either the RE type or name is stored in the file name
								-- Include RE name/type in RE filename should be skipped if V-Ray VFB Split is enabled
								-- VFB has its own override logic of V-Ray "splitName.reName.####.ext"
								if SMTDSettings.RenderElementsIncludeNameInFileName and not overrideReFilename do
									theNewFileName += ("_" + theElement.elementName)
								if SMTDSettings.RenderElementsIncludeTypeInFileName and not overrideReFilename do
									theNewFileName += ("_" + ((classof theElement) as string))
									
								local theNewExtension = (getFileNameType reFilename)
								if theNewExtension == undefined or theNewExtension == "" do
									theNewExtension += (getFileNameType outputFilename)
								theNewFileName += theNewExtension
								
								if SMTDSettings.purifyFilenames do theNewFileName = SMTDFunctions.purifyFilename theNewFileName 
								if SMTDSettings.ForceLowerCaseFilenames do theNewFileName = toLower theNewFileName
								reManager.SetRenderElementFilename i theNewFileName
							)
							else
							(
								local theNewFileName = if reFilename != undefined and reFilename != "" then
									(newPath +"\\" + getFileNameFile reFilename + getFileNameType reFilename)
								else
									 (newPath +"\\" + theElement.elementName + "_" + ((classof theElement) as string) + getFileNameType outputFilename)
								
								if SMTDSettings.purifyFilenames do theNewFileName = SMTDFunctions.purifyFilename theNewFileName
								if SMTDSettings.ForceLowerCaseFilenames do theNewFileName = toLower theNewFileName
								reManager.SetRenderElementFilename i theNewFileName
							)
						)--end if not missing element
					)--end i loop
				)--end if
			)--end if reManager undefined
		),
		
		fn RenderElementsUpdatePaths =
		(
			local outputFilename = rendOutputFilename
			local theRenderer = SMTDFunctions.getRendererObject()
			local theRendererName = SMTDFunctions.getRendererIdString()

			--VRay specific VFB code to handle RAW or Split Filename handling for RE paths, which overrides std output filename in 3dsMax
			if (theRendererName == "vray" OR theRendererName == "vrayrt") AND theRenderer.output_on then
			(
				--check if saving RE paths as separate RE files via VFB. If so, update RE paths with "output_splitfilename" override path, incl. sub-dirs if applicable
				if (theRenderer.output_splitgbuffer AND theRenderer.output_splitfilename != undefined AND theRenderer.output_splitfilename != "") then
				(
					local outputFilename = theRenderer.output_splitfilename
					SMTDFunctions.RenderElementsPathUpdater outputFilename overrideReFilename:True
				)--end if saving RE paths as separate RE files via VFB
				
				--check if saving a RAW image and Split Filename is disabled. If so, clear RE paths in UI as they are ignored by VFB
				else if (theRenderer.output_saveRawFile AND theRenderer.output_rawFileName != undefined AND theRenderer.output_rawFileName != "") then
				(
					local reManager = maxOps.GetCurRenderElementMgr()
					if reManager.GetElementsActive() then 
					(
						local reCount = reManager.NumRenderElements()
						for i = 0 to reCount - 1 do
						(
							reManager.SetRenderElementFilename i ""
						)--end for loop
					)--end if
				)--end if RAW image not being saved from VFB
			)
			--only update RE paths if the 3dsmax standard output filename isn't empty
			else if (outputFilename != undefined and outputFilename != "" and rendSaveFile) then
			(
				SMTDFunctions.RenderElementsPathUpdater outputFilename overrideReFilename:False
			)--end if update RE paths 
		),
		
		fn RenderElementsRestorePaths =
		(
			local reManager = maxOps.GetCurRenderElementMgr()
			if reManager != undefined do
			(
				local reCount = reManager.NumRenderElements()
				if classof SMTD_RenderElementPaths == Array do
				(
					for i = 0 to reCount - 1 do
					(
						if classof (reManager.GetRenderElement i) != Missing_Render_Element_Plug_in do					
						(
							if SMTD_RenderElementPaths[i+1] == undefined or SMTD_RenderElementPaths[i+1] == "" then
								reManager.SetRenderElementFilename i ""
							else
								reManager.SetRenderElementFilename i (SMTD_RenderElementPaths[i+1])
						)
					)
				)
			)--end if undefined
		),

		fn RebuildRenderElements = 
		(
			if RendOutputFilename != undefined or RendOutputFilename != "" do
			(
				local reManager = maxOps.GetCurRenderElementMgr()
				if reManager != undefined do
				(
					local AR_Elements = #()
					local AR_ElementProps = #()
					local AR_ElementFilenames = #()
					local AR_Elementnames = #()
					for i = 1 to reManager.numRenderElements() do
					(
						local theElement = reManager.getRenderElement (i - 1)
						if classof theElement != Missing_Render_Element_Plug_in do
						(
							append AR_Elements (classof theElement)
							local arrayOfProps = #()
							local thePropNames = getPropNames theElement
							if classof theElement == rsDepth and isProperty theElement #Maximum_Depth do append thePropNames #Maximum_Depth	--special handling for Redshift 2.5.30 rsDepth maxDepth value
							for prop in thePropNames do
								try(append arrayOfProps #(prop, (getproperty theElement prop)))catch()
							append AR_ElementProps arrayOfProps
							append AR_ElementNames theElement.elementName
							append AR_ElementFilenames (reManager.GetRenderElementFilename (i - 1))
						)
					)
					reManager.RemoveAllRenderElements()
					for i = 1 to AR_Elements.count do
					(
						reManager.addRenderElement (execute((AR_Elements[i] as string) + "()"))
						local theElement = reManager.getRenderElement (i - 1)
						for j in AR_ElementProps[i] do
							try(setproperty theElement j[1] j[2])catch()
						if AR_ElementFilenames[i] == undefined or AR_ElementFilenames[i] == "" then
							reManager.SetRenderElementFilename (i-1) ""
						else
							reManager.SetRenderElementFilename (i - 1) (getFilenamePath AR_ElementFilenames[i] + getFilenameFile AR_ElementFilenames[i] + getFilenameType RendOutputFilename)
						theElement.elementName = AR_ElementNames[i]
					)
				)--end if undefined
			)
		),

		fn IsSettingSticky theCategory theKey isSticky:true =
		( 
			local theStickyFile = getDir #userScripts + "\\SubmitMaxToDeadline_StickySettings.ini"
			local theLocalStickyFile = SMTDPaths.SettingsDir + "\\SubmitMaxToDeadline_StickySettings.ini"
			local isSticky = isSticky --If INI key is not set, we set to true if the property does not override its own stickiness via the array element 8
			local theValue = (getINISetting theStickyFile theCategory theKey) 
			--if there is such a global entry, see whether it is false or not. 
			if theValue != "" then isSticky = theValue != "false"
			--if there is such a local entry, see whether it is false or not
			local theValue = (getINISetting theLocalStickyFile theCategory theKey)
			if theValue != "" then isSticky = theValue != "false"
			isSticky 
		),
		
		fn FormatJobName currJobName =
		(
			local nameFormats = #()
			
			-- if a local version of the file exists, use that instead
			local nameFormatFilename = SMTDPaths.SettingsDir + "\\SubmitMaxToDeadline_NameFormats.ini"
			if not doesFileExist nameFormatFilename then
				nameFormatFilename = SMTDPaths.MainSubmissionDir+"\\SubmitMaxToDeadline_NameFormats.ini"
			
			local nameFormatFile = openFile nameFormatFilename
			if (nameFormatFile != undefined) then
			(
				try
				(
					while not eof nameFormatFile do
					(
						local fileLine = readLine nameFormatFile 
						local index = findString fileLine "="
						if (index != undefined and index < fileLine.count) then
						(
							nameFormats = append nameFormats #( (substring fileLine 1 (index-1)), (substring fileLine (index+1) -1) )
						)
					)
				)
				catch ()
				try(close nameFormatFile)catch()
			)
			
			for currNameFormat in nameFormats do
			(
				local searchVars = findstring currJobName currNameFormat[1]   
				if searchVars != undefined do
					currJobName = replace currJobName searchVars currNameFormat[1].count (execute currNameFormat[2])
			)
			currJobName
		),
		
		fn FormatComment currComment defaultTokenValue:"" =
		(
			local commentFormats = #()
			
			-- if a local version of the file exists, use that instead
			local commentFormatFilename = SMTDPaths.SettingsDir + "\\SubmitMaxToDeadline_CommentFormats.ini"
			if not doesFileExist commentFormatFilename then
				commentFormatFilename = SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_CommentFormats.ini"
			
			local commentFormatFile = openFile commentFormatFilename
			if (commentFormatFile != undefined) then
			(
				try
				(
					while not eof commentFormatFile do
					(
						local fileLine = readLine commentFormatFile 
						local index = findString fileLine "="
						if (index != undefined and index < fileLine.count) then
						(
							local theToken = (substring fileLine 1 (index-1))
							local theValue = (substring fileLine (index+1) -1)
							if theToken == "$default" and defaultValue != "" do theValue = defaultTokenValue
							theValue = try(execute theValue)catch(theValue)
							if theValue == OK do theValue = ""
							commentFormats = append commentFormats #(theToken, theValue)
						)
					)
				)
				catch ()
				try(close commentFormatFile)catch()
			)
			
			for currCommentFormat in commentFormats do
			(
				currComment = substituteString currComment currCommentFormat[1]  currCommentFormat[2] 
			)
			currComment
		),

		fn FormatExtraInfo currExtraInfo =
		(
			local extraInfoFormats = #()
			
			-- if a local version of the file exists, use that instead
			local extraInfoFormatFilename = SMTDPaths.SettingsDir + "\\SubmitMaxToDeadline_ExtraInfoFormats.ini"
			if not doesFileExist extraInfoFormatFilename then
				extraInfoFormatFilename = SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_ExtraInfoFormats.ini"
			
			local extraInfoFormatFile = openFile extraInfoFormatFilename
			if (extraInfoFormatFile != undefined) then
			(
				try
				(
					while not eof extraInfoFormatFile do
					(
						local fileLine = readLine extraInfoFormatFile 
						local index = findString fileLine "="
						if (index != undefined and index < fileLine.count) then
						(
							extraInfoFormats = append extraInfoFormats #( (substring fileLine 1 (index-1)), (substring fileLine (index+1) -1) )
						)
					)
				)
				catch ()
				try(close extraInfoFormatFile)catch()
			)
			
			for currExtraInfoFormat in extraInfoFormats do
			(
				local searchVars = findstring currExtraInfo currExtraInfoFormat[1]   
				if searchVars != undefined do
					currExtraInfo = replace currExtraInfo searchVars currExtraInfoFormat[1].count (execute currExtraInfoFormat[2])
			)
			currExtraInfo
		),
		
		fn getPickupFramesAsArray =
		(
			local theList = rendPickupFrames
			local theFrames = #()
			for i in filterString theList "," do 
			(
					local theArray = filterString i "-"
					if theArray.count == 2 then
					(
						theArray[1] = execute theArray[1]
						theArray[2] = execute theArray[2]
						sort theArray
						for j = theArray[1] to theArray[2] do appendIfUnique theFrames j
					)
					else
						appendIfUnique theFrames (execute i)
			)
			theFrames
		),
		
		fn GetFrameSequenceString frameMode:#both =
		(
			if SMTDSettings.UseCustomFrameList == true then
			(
				if isKindOf SMTDSettings.CustomFrameList Array and SMTDSettings.CustomFrameList.count > 0 then
				(
					if frameMode == #both then 
						SMTDFunctions.GetSequenceString SMTDSettings.CustomFrameList
					else
						SMTDFunctions.GetSequenceString (SMTDFunctions.outOfOrderSequence SMTDSettings.CustomFrameList mode:frameMode)
				)
				else
					SMTDFunctions.GetSequenceString #(currentTime.frame as integer)
			)
			else
			(			
				case rendTimeType of
				(
					1: SMTDFunctions.GetSequenceString #(currentTime.frame as integer)
					2: (
						local currentSequence = for t in animationRange.start to animationRange.end by rendNthFrame collect (t.frame as integer)
						if frameMode == #both then 
							currentSequence = SMTDFunctions.outOfOrderMethod currentSequence theMethod:SMTDSettings.outOfOrderMethod
						else	
						(
							currentSequence = SMTDFunctions.outOfOrderSequence currentSequence mode:frameMode
							currentSequence = SMTDFunctions.outOfOrderMethod currentSequence theMethod:SMTDSettings.outOfOrderMethod
						)	
						SMTDFunctions.GetSequenceString currentSequence 
					)	
					3: (
						local currentSequence = for t in rendStart to rendEnd by rendNthFrame collect (t.frame as integer)
						if frameMode == #both then 
							currentSequence = SMTDFunctions.outOfOrderMethod currentSequence theMethod:SMTDSettings.outOfOrderMethod
						else	
						(
							currentSequence = SMTDFunctions.outOfOrderSequence currentSequence mode:frameMode
							currentSequence = SMTDFunctions.outOfOrderMethod currentSequence theMethod:SMTDSettings.outOfOrderMethod
						)	
						SMTDFunctions.GetSequenceString currentSequence 
					)	
					4: (
							rendPickupFrames
							/*
							--explicit list
							with PrintAllElements on local val = (SMTDFunctions.getPickupFramesAsArray()) as string
							val = substring val 3 (val.count-3)
							*/
					)
				)
			)
		),		
		
		fn GetFrameSequenceArray frameMode:#both =
		(
			if SMTDSettings.UseCustomFrameList == true then
			(
				if isKindOf SMTDSettings.CustomFrameList Array and SMTDSettings.CustomFrameList.count > 0 then
				(
					if frameMode == #both then 
						SMTDSettings.CustomFrameList
					else
						SMTDFunctions.outOfOrderSequence SMTDSettings.CustomFrameList mode:frameMode
				)
				else
					#(currentTime.frame as integer)
			)
			else
			(
				case rendTimeType of
				(
					1: #(currentTime.frame as integer)
					2: (
						local currentSequence = for t in animationRange.start to animationRange.end by rendNthFrame collect (t.frame as integer)
						if frameMode == #both then 
							currentSequence = SMTDFunctions.outOfOrderMethod currentSequence theMethod:SMTDSettings.outOfOrderMethod
						else	
						(
							currentSequence = SMTDFunctions.outOfOrderSequence currentSequence mode:frameMode
							currentSequence = SMTDFunctions.outOfOrderMethod currentSequence theMethod:SMTDSettings.outOfOrderMethod
						)	
						currentSequence 
					)	
					3: (
						local currentSequence = for t in rendStart to rendEnd by rendNthFrame collect (t.frame as integer)
						if frameMode == #both then 
							currentSequence = SMTDFunctions.outOfOrderMethod currentSequence theMethod:SMTDSettings.outOfOrderMethod
						else	
						(
							currentSequence = SMTDFunctions.outOfOrderSequence currentSequence mode:frameMode
							currentSequence = SMTDFunctions.outOfOrderMethod currentSequence theMethod:SMTDSettings.outOfOrderMethod
						)	
						currentSequence 
					)	
					4: (SMTDFunctions.getPickupFramesAsArray())
				)
			)
		),

		fn GetPipelineToolStatus =
		(
			pipelineToolsDir = substituteString SMTDPaths.IntegrationDir "\\" "/"
			jobWriterPath = pipelineToolsDir + "JobWriter.py"
			sceneName = maxFilePath + maxFileName
			pipelineOptions = " 3dsmax " + "--status " + "--scene-path \"" + substituteString sceneName "\\" "/"
			jobWriterArgs = " -executeScript \"" + jobWriterPath + "\"" + pipelineOptions
			statusMessage = SMTDFunctions.CallDeadlineCommandInMemory ( jobWriterArgs )
			SMTDFunctions.SetPipelineToolStatus( statusMessage )
		),

		fn ConcatenatePipelineSettingsToJob filePath batchName =
		(
			pipelineToolsDir = substituteString SMTDPaths.IntegrationDir "\\" "/"
			jobWriterPath = pipelineToolsDir + "JobWriter.py"
			sceneName = maxFilePath + maxFileName
			pipelineOptions = " 3dsmax " + "--write " + "--scene-path \"" + substituteString sceneName "\\" "/" + "\" --job-path " + "\"" + substituteString filePath "\\" "/" + "\"" + " --batch-name " + "\"" + batchName + "\""
			jobWriterArgs = " -executeScript \"" + jobWriterPath + "\"" + pipelineOptions
			SMTDFunctions.CallDeadlineCommandInMemory ( jobWriterArgs )
		),
		
		fn writeSceneFileToFile property fileHook =
		(
			local scenePath = ""
			case SMTDSettings.SubmitSceneMode of
			(
				default: ()
				#networksave:
				(
					scenePath = SMTDSettings.SubmitSceneNetworkLocation
				)
				#globalnetworksave:
				(
					scenePath = SMTDSettings.SubmitSceneNetworkLocation
				)
				#networkuse:
				(
					scenePath = maxFilePath + maxFileName
				)
				#networksaveanduse:
				(
					scenePath = maxFilePath + maxFileName
				)
				#networkremap:
				(
					local theCurrentPath = (maxFilePath + maxFileName)
					global SMTD_RemapLocalToNetworkPath
					fn SMTD_RemapLocalToNetworkPath thepath = (thepath)
					local theScriptFile = (SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_RemapLocalToNetworkPath.ms"  )
					if doesFileExist theScriptFile do try(fileIn theScriptFile)catch()
					theCurrentPath = ::SMTD_RemapLocalToNetworkPath theCurrentPath
					scenePath = theCurrentPath
				)					
			)
			
			if scenePath != "" then
			(
				format "%=%\n" property scenePath to:fileHook
				true
			)
			else
				false
	
		),

		-- A render element produces zero or more file artifacts. Returns an array of the filename suffixes
		-- corresponding to each artifact created by the passed render element.
		fn RenderElementArtifactSuffixes reObject =
		(
			if classof reObject == VRayDenoiser then
				-- VRayDenoiser is a special-case. Depending on the mode of the render
				-- element, it will generate zero or more of the following artifacts:
				-- ("<PREFIX>.origRGB.<EXT>", "<PREFIX>.<RE_NAME>.<EXT>")
				-- and preserves the prior result with the filename "PREFIX.origRGB.SUFFIX"
				case reObject.mode of
				(
					0: #()
					1: #("origRGB")
					2: #("origRGB", reObject.elementName)
				)
			else
				#(reObject.elementName)
		),
		
		-- NOTES: 
			-- includeBothOutputs is no longer used, but it is left here for legacy purposes.
			-- customOutputFile: is not longer used, but it is left here for legacy purposes.
		-- THIS IS NOWADAYS CALLED THE JOB INFO FILE
		fn CreateSubmitInfoFile filename customPlugin: customOutputFile: includeBothOutputs:false frameMode:#both customFrameSequence:"" batchName:"" currentTileString:"" stereoCameraLabel:"" =
		(
			local oldJobName = SMTDSettings.JobName
			
			if SMTDSettings.StateSetsSubmit do
			(
				SMTDSettings.Comment = "State Set: " + SMTDSettings.StateSetName
				SMTDSettings.JobName = oldJobName + " [STATE SET '"+SMTDSettings.StateSetName+"']"
			)
			
			local formattedJobName = (SMTDFunctions.FormatJobName SMTDSettings.JobName )
			local formattedComment = (SMTDFunctions.FormatComment SMTDSettings.Comment)
			SMTDSettings.JobName = oldJobName
			
			local submitInfoFile = CreateFile filename encoding:#utf8 writeBOM:true
			if (submitInfoFile != undefined) then
			(
				if customPlugin == unsupplied then 
				(
					local pluginToUse = SMTDFunctions.getPluginToUse()
					format "Plugin=%\n" pluginToUse to:submitInfoFile
				)
				else 
				(
					format "Plugin=%\n" customPlugin to:submitInfoFile
				)
				
				if SMTDSettings.CurrentRepository != "" then  
					format "NetworkRoot=%\n" SMTDSettings.CurrentRepository  to:submitInfoFile
				else
				(
					if SMTDSettings.CurrentRepository2 != "" do
					(
						--format "TransferJobToRepository=%\n" SMTDSettings.CurrentRepository2  to:submitInfoFile
						--format "TransferJobAsSuspended=%\n" SMTDSettings.TransferJobAsSuspended to:submitInfoFile
						
						format "NotificationEmails=%\n" SMTDSettings.AlternateEmails to:submitInfoFile
						
						local notificationNote = substituteString SMTDSettings.NotificationNote "\r" ""
						notificationNote = substituteString notificationNote "\n" "[EOL]"
						format "NotificationNote=%\n" notificationNote to:submitInfoFile
					)
				)

				local theBlackWhiteList = SMTDSettings.SlavesList
				local theKeyword = if SMTDSettings.SlavesBlackList then "Blacklist" else "Whitelist"
				if SMTDSettings.DBR do --if DBR Offload job, use the DBR settings
				(
					theBlackWhiteList = SMTDSettings.MastersList
					theKeyword = if SMTDSettings.MastersBlackList then "Blacklist" else "Whitelist"
				)
				local theSlaveListString = SMTDFunctions.getListAsString theBlackWhiteList
				format "%=%\n" theKeyword theSlaveListString to:submitInfoFile

				local depJobIds = ""
				if SMTDSettings.SubmitAsDependent and (frameMode != #rest OR SMTDSettings.PreviewJobSecondJobDependentOnFirst == false) do
				(
					local theJobs = SMTDSettings.DependencyJobItems as array
					local currentJobsArray = case SMTDSettings.DependOnPreviousJobMode of
					(
						default: deepCopy SMTDSettings.JobsArray
						#previous: deepCopy SMTDSettings.PreviousJobsArray
						#last: 
						(
							if SMTDSettings.PreviousJobsArray.count > 0 then
								#(SMTDSettings.PreviousJobsArray[SMTDSettings.PreviousJobsArray.count])
							else
								#()
						)
					)
					for i = 1 to theJobs.count do
					(
						depJobIds += currentJobsArray[theJobs[i]][2] 
						if i < theJobs.count do depJobIds += ","
					)	
				)	
				if SMTDSettings.PreviewJobSecondJobDependentOnFirst == true AND frameMode == #rest do
				(
					depJobIds += SMTDSettings.DeadlineSubmissionLastJobID	
				)

				if rpmdata != undefined and RPMDataNet != undefined and RPMDataNet.CustomSubmitStruct != undefined do --only if RPM is active
				(
					--MODIFIED by grant
					-- first we collect the job dependencies based on our UI settings:
					-- we are getting this data again - rather then store it in the struct (as it shouldn't be stored restored) lets just grab it again as it is lightweight
					previouslysubmittedJobs = rpmdata.getcustglobstorage 10002 -- array of submitted jobs in this submission session
					isperpassdependency = rpmdata.getcustglobstorage 10004 
					doPassDependency = rpmdata.getcustglobstorage 10000
					if isperpassdependency == true then
					(
						try(passDependencyList = rpmdata.GetCustPassStorage RPMDataNet.CustomSubmitStruct.lastRestoredPass 10001)catch(passDependencyList = #(); passDependencyList.count = rpmdata.getpasscount())
						--passDependencyList = rpmdata.getcustglobstorage 10001
					)
					else
						passDependencyList = rpmdata.getcustglobstorage 10001
					if previouslysubmittedJobs == undefined do previouslysubmittedJobs = #()
					if doPassDependency == undefined do doPassDependency = False
					if passDependencyList == undefined do passDependencyList = #()
					if doPassDependency == true do
					(
						for i in 1 to previouslysubmittedJobs.count do
						(
							--passIndex = rpmcaptureprops.getpassindexfromnumb previouslysubmittedJobs[i][2]
							if finditem passDependencyList previouslysubmittedJobs[i][2]  != 0 do
							(
								if depJobIds.count != 0 do depJobIds += ","
								depJobIds += previouslysubmittedJobs[i][1]
							)
						)
					)
				)
				
				if depJobIds.count > 0 do
				(
					format "JobDependencies=%\n" depJobIds  to:submitInfoFile
					format "ResumeOnDeletedDependencies=%\n" SMTDSettings.ResumeOnDeletedDependencies to:submitInfoFile
				)				
						
				if SMTDSettings.submitAsSuspended OR SMTDSettings.CurrentRepository2 != "" OR (SMTDSettings.PreviewJobSecondJobSuspended AND frameMode == #rest)do --OR (SMTDSettings.SubmitExternalFilesMode > 1 AND SMTDSettings.SubmitExternalFilesMode < 4 )
					format "InitialStatus=Suspended\n" to:submitInfoFile	
				
				if SMTDSettings.SequentialJob do
					format "Sequential=1\n" to:submitInfoFile	
				
				if SMTDSettings.IsBakeJob and SMTDSettings.BakeJobOneObjectPerTask then
				(
					local framesSS = "" as stringStream
					for i = 1 to SMTD_objsToBake.count-1 do format "%," i to:framesSS
					format "%" SMTD_objsToBake.count to:framesSS	
					local frames = framesSS as string
					format "Frames=%\n" frames 	to:submitInfoFile
					format "ChunkSize=1\n" to:submitInfoFile					
				)
				else
				(
					local frames = SMTDFunctions.GetFrameSequenceString frameMode:frameMode
					--if SMTDSettings.TilesRendering AND SMTDSettings.TilesSubmissionMode == #deadline do frames = "1"
					if SMTDSettings.SubmitAsMXSJob AND SMTDSettings.SingleTaskJob do frames = "1"
					if SMTDSettings.UseBatchRender AND SMTDSettings.BatchRenderMode == 2 do frames = "1"
						
					if customFrameSequence != "" do frames = customFrameSequence
					
					--SINGLE FRAME TILE OR MULTI-REGION RENDERING
					if findItem #(#singleFrameTiles, #singleFrameMultiRegion) SMTDSettings.RegionRenderingMode > 0 then
					(
						--if SMTDSettings.UseCustomTiles then
						--	format "Frames=%\n"			SMTDSettings.SingleTileJobFrameList			to:submitInfoFile
						--else
						--	format "Frames=0-%\n" 		(SMTDSettings.SingleTileJobTileCount-1)		to:submitInfoFile
						--format "ChunkSize=1\n"														to:submitInfoFile
						
						format "TileJob=True\n"														to:submitInfoFile
						format "TileJobFrame=%\n"		(currentTime.frame as integer)				to:submitInfoFile
						
						-- SINGLE FRAME MULTI-REGION
						if findItem #(#singleFrameMultiRegion) SMTDSettings.RegionRenderingMode > 0 then
						(
							local totalRegions = 0
							for i in SMTDSettings.MultiRegionData where i[1] do totalRegions += i[6]*i[7]
							format "TileJobTilesInX=%\n"	totalRegions to:submitInfoFile
							format "TileJobTilesInY=1\n"	 											to:submitInfoFile
						)
						-- SINGLE FRAME TILE
						else
						(
							format "TileJobTilesInX=%\n"	SMTDSettings.TilesInX						to:submitInfoFile
							format "TileJobTilesInY=%\n"	SMTDSettings.TilesInY						to:submitInfoFile
						)
						
						--Only do this if rendering single frame custom tiles
						if SMTDSettings.UseCustomTiles and SMTDSettings.RegionRenderingMode == #singleFrameTiles do
							format "InitialUncompletedTaskIds=%\n"			SMTDSettings.SingleTileJobFrameList			to:submitInfoFile
					)
					else
					(
						local chunkSize = SMTDSettings.ChunkSize
					
						if SMTDSettings.DBR do
						(
							local rendererID = SMTDFunctions.getRendererIdString()
							if SMTDFunctions.getRendererSupportsDBROffload() do
							(
								frames = "0-" + ((SMTDSettings.DBRServers-1) as string)
								chunkSize = 1
							)
						)
					
						format "Frames=%\n" 		frames 						to:submitInfoFile
						format "ChunkSize=%\n" 		SMTDSettings.ChunkSize		to:submitInfoFile
					)
				)--end not Bake Texture
				
				--format "ReorderFrames=%\n" 			(rendTimeType == 4)			to:submitInfoFile
				format "Priority=%\n" 				SMTDSettings.Priority 	 	to:submitInfoFile
				format "Pool=%\n" 					SMTDSettings.PoolName		to:submitInfoFile
				if SMTDSettings.Pool2Name != "" do
					format "SecondaryPool=%\n" 		SMTDSettings.Pool2Name		to:submitInfoFile

				if SMTDSettings.TaskTimeoutEnabled then
					format "TaskTimeoutSeconds=%\n" 		SMTDSettings.TaskTimeout 		to:submitInfoFile
				else
					format "TaskTimeoutSeconds=0\n" 									to:submitInfoFile
				format "EnableAutoTimeout=%\n"			SMTDSettings.AutoTaskTimeout				to:submitInfoFile
				
				format "ForceReloadPlugin=%\n"			SMTDSettings.RestartMax						to:submitInfoFile

				format "MaxTasksPerSlave=%\n" 			SMTDSettings.MaxTasksPerSlave				to:submitInfoFile
				format "LimitTasksToNumberOfCpus=%\n" 	SMTDSettings.LimitTasksToNumberOfCpus		to:submitInfoFile
				
				local theSpecialLabel = ""
				if SMTDSettings.SubmitAsMXSJob then
				(
					theSpecialLabel = " ["+SMTDSettings.MAXScriptJobLabel+"]"
					if SMTDSettings.IsBakeJob do 
					(
						theSpecialLabel += " [RTT "+ SMTD_objsToBake.count as string 
						theSpecialLabel += (if SMTD_objsToBake.count == 1 then " Object" else " Objects")
						if SMTDSettings.BakeJobOneObjectPerTask then theSpecialLabel += ", One Per Task]" else theSpecialLabel +="]"
					)
				)
				else
				(
					case SMTDSettings.RegionRenderingMode of
					(
						#animationMultiRegion: --if SMTDSettings.MultiRegionRendering and not SMTDSettings.SingleTileJob then
						(
								local totalRegions = 0
								for i in SMTDSettings.MultiRegionData where i[1] do totalRegions += i[6]*i[7]
								local activeRegions = (for i in SMTDSettings.MultiRegionData where i[1] collect i).count
								theSpecialLabel = " [Multi-Frame - " + activeRegions as string + " Region"+(if activeRegions == 1 then ", " else "s, ") +totalRegions as string+" Sub-Region"+(if totalRegions == 1 then "]" else "s]")
						)
						
						#singleFrameMultiRegion: --if SMTDSettings.MultiRegionRendering then
						(
							local totalRegions = 0
							for i in SMTDSettings.MultiRegionData where i[1] do totalRegions += i[6]*i[7]
							local activeRegions = (for i in SMTDSettings.MultiRegionData where i[1] collect i).count
							theSpecialLabel = " [Frame " + ((currentTime.frame as integer) as string) + " - " + activeRegions as string + " Region"+(if activeRegions == 1 then ", " else "s, ") +totalRegions as string+" Sub-Region"+(if totalRegions == 1 then "]" else "s]")
						)					
						
						#singleFrameTiles:  --if SMTDSettings.TilesRendering then
						(
							--if SMTDSettings.SingleTileJob then
							theSpecialLabel = " [Frame " + ((currentTime.frame as integer) as string) + " - " + ((SMTDSettings.TilesInX * SMTDSettings.TilesInY) as string) + " Tiles]"
						)
						
						default: --anything else
						(
							if SMTDSettings.UseBatchRender and SMTDSettings.BatchRenderMode == 2 then
								theSpecialLabel = " ["+SMTDSettings.BatchMasterJobLabel+"]"
							else
								theSpecialLabel = case frameMode of
								(
									#both: ""
									#nth: " ["+SMTDSettings.PreviewJobLabel+"]" 
									#rest: " ["+SMTDSettings.PreviewRestJobLabel+"]" 	
								)
						)
					)--end case
				)
				
				local stereoCameraNameToken = if stereoCameraLabel == "" then "" else " ["+stereoCameraLabel+"]"
				local stereoCameraToken = stereoCameraLabel --if stereoCameraLabel == "" then "" else stereoCameraLabel+"_"
				
				format "Name=%%%\n" 				formattedJobName stereoCameraNameToken theSpecialLabel 	to:submitInfoFile
				format "UserName=%\n"				SMTDSettings.UserName		to:submitInfoFile
				format "Comment=%\n" 				formattedComment			to:submitInfoFile
				
				format "Department=%\n" 			SMTDSettings.Department 	to:submitInfoFile				
				format "Group=%\n" 					SMTDSettings.Group 			to:submitInfoFile				
				
				if SMTDSettings.RunPreJobScript do
					format "PreJobScript=%\n" SMTDSettings.PreJobScriptFile to:submitInfoFile
				if SMTDSettings.RunPostJobScript do
					format "PostJobScript=%\n" SMTDSettings.PostJobScriptFile to:submitInfoFile
				if SMTDSettings.RunPostTaskScript then
					format "PostTaskScript=%\n" SMTDSettings.PostTaskScriptFile to:submitInfoFile
				if SMTDSettings.RunPreTaskScript do
					format "PreTaskScript=%\n" SMTDSettings.PreTaskScriptFile to:submitInfoFile
				
				case SMTDSettings.ScheduledType of
				(
					#None: (format "ScheduledType=None\n" to:submitInfoFile	)
					#Once: 
					(
						format "ScheduledType=Once\n" to:submitInfoFile	
						format "ScheduledStartDateTime=%\n" SMTDSettings.ScheduledStartDateTime to:submitInfoFile	
					)
					#Daily: 
					(
						format "ScheduledType=Daily\n" to:submitInfoFile	
						format "ScheduledDays=%\n" SMTDSettings.ScheduledDays to:submitInfoFile	
						format "ScheduledStartDateTime=%\n" SMTDSettings.ScheduledStartDateTime to:submitInfoFile	
					)
				)

				--MONITOR RC RENDER OUTPUT DIRECTORIES & FILENAMES
				--If an output filename is specified, include it in the submit info file for accessing through the Monitor's RC Menu
				local outputFilenameIndex = 0
				if ::SMTDSettings.IsBakeJob == true do
				(
					local thePath = RTT_data.FileOutput_FilePath
					for i = 1 to ::SMTD_objsToBake.count do
					(
						local theInterface = ::SMTD_objsToBake[i].INodeBakeProperties
						for anElement = 1 to theInterface.numBakeElements() do
						(
							local theBE = theInterface.getBakeElement anElement
							if theBE.enabled do
							(
								local filename = theBE.fileName
								format "OutputFilename%=%%%%\n" outputFilenameIndex (getFileNamePath filename) (getFileNameFile filename) (formattedPrint (currentTime.frame as integer) format:"04i") (getFileNameType filename) to:submitInfoFile
								outputFilenameIndex += 1
							)--end if enabled
						)--end anElement loop
					)--end i loop
				)
				local theRenderOutput = rendOutputFilename
				if rendSaveFile and theRenderOutput != undefined and theRenderOutput != "" do
				(
					if SMTDSettings.purifyFilenames do theRenderOutput = SMTDFunctions.purifyFilename theRenderOutput				
					if SMTDSettings.ForceLowerCaseFilenames do theRenderOutput = toLower theRenderOutput
					if SMTDSettings.SubmitSceneMode == #networkremap do theRenderOutput = ::SMTD_RemapLocalToNetworkPath theRenderOutput
					case SMTDSettings.RegionRenderingMode of
					(
						#animationMultiRegion:
						(
							local tempFile = SMTDFunctions.GetFormattedOutputFilename theRenderOutput stereoCameraToken:stereoCameraLabel regionString:currentTileString
							if tempFile != "" do 
								format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
						)
						#singleFrameMultiRegion:
						(
							local theIndex = 0
							for aData in SMTDSettings.MultiRegionData where aData[1] == True do
							(
								for y2 = 1 to aData[7] do
								(
									for x2 = 1 to aData[6] do
									(
										local regionString = "_region_" + theIndex as string + "_"
										local tempFile = SMTDFunctions.GetFormattedOutputFilename theRenderOutput stereoCameraToken:stereoCameraLabel regionString:regionString
										if tempFile != "" do
										(
											format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
											theIndex += 1
										)
									)
								)
							)
						)
						#singleFrameTiles:
						(
							local theIndex = 0
							for y = 1 to SMTDSettings.TilesInY do
							(
								for x = 1 to SMTDSettings.TilesInX do
								(
									local tileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string  + "_"
									local tempFile = SMTDFunctions.GetFormattedOutputFilename theRenderOutput stereoCameraToken:stereoCameraLabel regionString:tileString	
									if tempFile != "" do 
									(
										format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
										theIndex += 1
									)
								)
							)
						)
						default: --anything else
						(
							local tempFile = SMTDFunctions.GetFormattedOutputFilename theRenderOutput stereoCameraToken:stereoCameraLabel
							if tempFile != "" do format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
						)
					)
					outputFilenameIndex += 1
				)--end if 3ds Max render output enabled and valid
				
				--Optionally add Renderer specific caching files as Deadline Monitor Output Paths (only if NOT tile rendering as otherwise it messes up OutputFilename#Tile? pathing for DTA)
				local tileRender = findItem #(#animationTiles, #singleFrameTiles,#singleFrameMultiRegion, #animationMultiRegion) SMTDSettings.RegionRenderingMode > 0
				if SMTDSettings.ExportAdvancedRenderOutputFiles AND not tileRender do
				(
					--Show any additional mental ray paths like light maps and other caches as outputs in the Deadline Monitor for exploring
					--MENTAL RAY RENDERER PATHS
					if SMTDFunctions.getRendererIdString() == "mentalray" do
					(
						local theFilenameProps = #()
						
						if (isProperty renderers.current #Export_On_Render) and (getProperty renderers.current #Export_On_Render) do
							append theFilenameProps #Export_Filename
						
						if (isProperty renderers.current #FinalGatherEnable2) and (getProperty renderers.current #FinalGatherEnable2) and (isProperty renderers.current #UseFinalGatherFile) and (getProperty renderers.current #UseFinalGatherFile) then
						(
							if (isProperty renderers.current #FinalGatherFreeze) and (not getProperty renderers.current #FinalGatherFreeze) do --only if writing (not reading) fgm files
								append theFilenameProps #FinalGatherFilename
						)
						
						if ((isProperty renderers.current #GlobalIllumEnable) and (getProperty renderers.current #GlobalIllumEnable)) or ((isProperty renderers.current #CausticsEnable) and (getProperty renderers.current #CausticsEnable)) then
						(
							if (isProperty renderers.current #PhotonMapUseFile) and (getProperty renderers.current #PhotonMapUseFile) then
							(
								if (isProperty renderers.current #PhotonFreeze) and (not getProperty renderers.current #PhotonFreeze) do --only if writing (not reading) pmap (Photon/Caustics) files
									append theFilenameProps #PhotonMapFilename
							)
						)
						
						local alreadyExported = #()
						for p in theFilenameProps where (isProperty renderers.current p) do
						(
							local reFilename = getProperty renderers.current p
							if ( reFilename != undefined AND reFilename != "" ) do
							(
								if SMTDSettings.purifyFilenames do reFilename = SMTDFunctions.purifyFilename reFilename
								if SMTDSettings.ForceLowerCaseFilenames do reFilename = toLower reFilename
								if SMTDSettings.purifyFilenames or SMTDSettings.ForceLowerCaseFilenames do setProperty renderers.current p reFilename
								if findItem alreadyExported reFilename == 0 do
								(
									if (getFilenamePath reFilename) != "" do --skip if non-rooted path
									(
										--calculate padding if required
										local paddingString = "####"
										if (findItem #(#singleFrameTiles, #singleFrameMultiRegion) SMTDSettings.RegionRenderingMode > 0) do
											paddingString = formattedPrint (currentTime.frame as integer) format:"04i"

										--incremental mi files
										if p == #Export_Filename AND (isProperty renderers.current #Incremental_Echo) AND (not getProperty renderers.current #Incremental_Echo) do
											reFilename = (getFilenamePath reFilename) + (getFilenameFile reFilename) + paddingString + (getFilenameType reFilename)

										--incremental fgm files
										if p == #FinalGatherFilename AND (isProperty renderers.current #IlluminationCacheMode) AND ((getProperty renderers.current #IlluminationCacheMode) > 0) do
											reFilename = (getFilenamePath reFilename) + (getFilenameFile reFilename) + paddingString + (getFilenameType reFilename)

										--incremental photon/caustics files
										if p == #PhotonMapFilename AND (isProperty renderers.current #IlluminationCacheMode) AND ((getProperty renderers.current #IlluminationCacheMode) > 0) do
											reFilename = (getFilenamePath reFilename) + (getFilenameFile reFilename) + paddingString + (getFilenameType reFilename)

										format "OutputFilename%=%\n" outputFilenameIndex reFilename to:submitInfoFile --need to get the filename only!
										outputFilenameIndex += 1

										append alreadyExported reFilename
									)
								)
							)--end if
						)--end p loop
					)--end if MENTAL RAY RENDERER PATHS

					--Show any additional corona paths like hdCache maps as outputs in the Deadline Monitor for exploring
					--CORONA RENDERER PATHS
					if SMTDFunctions.getRendererIdString() == "corona" do
					(
						
						--Check Corona version. Version's earlier than Alpha v6 are NOT supported and are no longer available from Corona Renderer website.
						coronaVersion = try(CoronaRenderer.CoronaFp.getCoronaVersion())catch(undefined)

						local theFilenameProps = #()

						if coronaVersion == undefined then --assume Corona Alpha v6 FREE VERSION / NO UPDATES / NO SUPPORT
						(
							if (isProperty renderers.current #renderer) and ((getProperty renderers.current #renderer == 0) or (getProperty renderers.current #renderer == 2)) do
							(
								if (isProperty renderers.current #GI_solver) and (getProperty renderers.current #GI_solver == 1) do
								(
									if (isProperty renderers.current #GI_secondary_solver) and (getProperty renderers.current #GI_secondary_solver == 3) do
										append theFilenameProps #Secondary_GI_filename
								)
							)
						)
						else if coronaVersion == "Alpha v7.2" then --Corona Alpha v7.2
						(
							if (isProperty renderers.current #GI_solver) and (getProperty renderers.current #GI_solver == 1) do
							(
								if (isProperty renderers.current #GI_secondary_solver) and (getProperty renderers.current #GI_secondary_solver == 3) do
								(
									if (isProperty renderers.current #HD_cache_precalculation_mode) and (getProperty renderers.current #HD_cache_precalculation_mode == 2) do
									(
										if (isProperty renderers.current #HD_cache_save) and (getProperty renderers.current #HD_cache_save) do
											append theFilenameProps #HD_cache_dump_filename
									)
								)
							)
						)
						else --Production Release of Corona v1.0 onwards
						(
							if (isProperty renderers.current #shading_primarySolver) and (getProperty renderers.current #shading_primarySolver == 1) do
							(
								if (isProperty renderers.current #shading_secondarySolver) and ((getProperty renderers.current #shading_secondarySolver == 3) or (getProperty renderers.current #shading_secondarySolver == 4)) do
								(
									--Corona 1.5 or earlier (#shading_secondarySolver == 3)
									if (isProperty renderers.current #gi_hdCache_precalcMode) then
									(
										if (getProperty renderers.current #gi_hdCache_precalcMode == 0) or (getProperty renderers.current #gi_hdCache_precalcMode == 2) do
										(
											if (isProperty renderers.current #gi_hdCache_save) and (getProperty renderers.current #gi_hdCache_save) do append theFilenameProps #gi_hdCache_file
										)
									)
									--Corona 1.6 changed the property name by prefixing the letter: "u" (gi_hd -> gi_uhd) (#shading_secondarySolver == 4)
									else if (isProperty renderers.current #gi_uhdCache_precalcMode) do
									(
										if (getProperty renderers.current #gi_uhdCache_precalcMode == 0) or (getProperty renderers.current #gi_uhdCache_precalcMode == 2) do
										(
											if (isProperty renderers.current #gi_uhdCache_save) and (getProperty renderers.current #gi_uhdCache_save) do append theFilenameProps #gi_uhdCache_file
										)
									)
								)
							)
						)

						local alreadyExported = #()
						for p in theFilenameProps where (isProperty renderers.current p) do
						(
							local reFilename = getProperty renderers.current p
							if ( reFilename != undefined and reFilename != "" ) do
							(
								if SMTDSettings.purifyFilenames do reFilename = SMTDFunctions.purifyFilename reFilename
								if SMTDSettings.ForceLowerCaseFilenames do reFilename = toLower reFilename
								if SMTDSettings.purifyFilenames or SMTDSettings.ForceLowerCaseFilenames do setProperty renderers.current p reFilename
								if findItem alreadyExported reFilename == 0 do
								(
									if (getFilenamePath reFilename) != "" do --skip if non-rooted path
									(
										format "OutputFilename%=%\n" outputFilenameIndex reFilename to:submitInfoFile
										outputFilenameIndex += 1
										append alreadyExported reFilename
									)
								)
							)--end if
						)--end p loop
					)--end if CORONA RENDERER PATHS
					
					--Show any additional vray paths like light maps and other caches as outputs in the Deadline Monitor for exploring
					--VRAY RENDERER PATHS
					if (SMTDFunctions.getRendererIdString() == "vray" OR SMTDFunctions.getRendererIdString() == "vrayrt") do
					(
						--NON-IMAGE RENDERER FILE PROPERTIES
						local theFilenameProps = #()
						
						local theRenderer = SMTDFunctions.getRendererObject()

						if (isProperty theRenderer #gi_on) and (getProperty theRenderer #gi_on) do
						(
							if ((isProperty theRenderer #gi_primary_type) and (getProperty theRenderer #gi_primary_type == 0)) do
							(
								--ignore if "From file", "Bucket mode" or "Animation (rendering)" is selected (reading instead of writing vrmap file)
								if (isProperty theRenderer #adv_irradmap_mode) and (getProperty theRenderer #adv_irradmap_mode != 2) and (getProperty theRenderer #adv_irradmap_mode != 5) and (getProperty theRenderer #adv_irradmap_mode != 7) do
								(
									if (isProperty theRenderer #adv_irradmap_autoSave) and (getProperty theRenderer #adv_irradmap_autoSave) do -- only if irr map autosave enabled
										append theFilenameProps #adv_irradmap_autoSaveFileName
								)
							)
							
							if ((isProperty theRenderer #gi_primary_type) and (getProperty theRenderer #gi_primary_type == 1)) OR ((isProperty theRenderer #gi_secondary_type) and (getProperty theRenderer #gi_secondary_type == 1)) do
							(
								if (isProperty theRenderer #photonMap_mode) and (getProperty theRenderer #photonMap_mode == 0) do --only if writing Photon map 
								(
									if (isProperty theRenderer #photonMap_autoSave) and (getProperty theRenderer #photonMap_autoSave) do --only if Photon map autosave enabled
										append theFilenameProps #photonMap_autoSaveFileName
								)
							)

							if ((isProperty theRenderer #gi_primary_type) and (getProperty theRenderer #gi_primary_type == 3)) OR ((isProperty theRenderer #gi_secondary_type) and (getProperty theRenderer #gi_secondary_type == 3)) do
							(
								if (isProperty theRenderer #lightcache_mode) and (getProperty theRenderer #lightcache_mode != 2) do --only if writing lightcache map
								(
									if (isProperty theRenderer #lightcache_autoSave) and (getProperty theRenderer #lightcache_autoSave) do --only if lightcache autosave enabled
										append theFilenameProps #lightcache_autoSaveFileName
								)
							)
						)
						
						if (isProperty theRenderer #caustics_on) and (getProperty theRenderer #caustics_on) do
						(
							if (isProperty theRenderer #caustics_mode) and (getProperty theRenderer #caustics_mode == 0) do --only if writing Caustics map
							(
								if (isProperty theRenderer #caustics_autoSave) and (getProperty theRenderer #caustics_autoSave) do --only if Caustics map autosave enabled
									append theFilenameProps #caustics_autoSaveFileName
							)
						)

						local alreadyExported = #()
						for p in theFilenameProps where (isProperty theRenderer p) do
						(
							local reFilename = getProperty theRenderer p
							if ( reFilename != undefined and reFilename != "" ) do
							(
								if SMTDSettings.purifyFilenames do reFilename = SMTDFunctions.purifyFilename reFilename
								if SMTDSettings.ForceLowerCaseFilenames do reFilename = toLower reFilename
								if SMTDSettings.purifyFilenames or SMTDSettings.ForceLowerCaseFilenames do setProperty theRenderer p reFilename
								if findItem alreadyExported reFilename == 0 do
								(
									if (getFilenamePath reFilename) != "" do --skip if non-rooted path
									(
										--calculate padding if required
										local paddingString = "####"
										if (findItem #(#singleFrameTiles, #singleFrameMultiRegion) SMTDSettings.RegionRenderingMode > 0) do
											paddingString = formattedPrint (currentTime.frame as integer) format:"04i"

										--incremental vrmap files during "Animation (prepass)"
										if p == #adv_irradmap_autoSaveFileName AND (isProperty theRenderer #adv_irradmap_mode) AND (getProperty theRenderer #adv_irradmap_mode == 6) do
											reFilename = (getFilenamePath reFilename) + (getFilenameFile reFilename) + paddingString + (getFilenameType reFilename)

										format "OutputFilename%=%\n" outputFilenameIndex reFilename to:submitInfoFile
										outputFilenameIndex += 1
										append alreadyExported reFilename
									)
								)
							)--end if
						)--end p loop

						--V-RAY RAW FILE SPECIFIC CODE -- RENDERER IMAGE FILE PROPERTIES
						local theFilenameProps = #()

						if (isProperty theRenderer #output_on) and (getProperty theRenderer #output_on) do
						(
							if (isProperty theRenderer #output_saveRawFile) and (getProperty theRenderer #output_saveRawFile) do
								append theFilenameProps #output_rawFileName
						)

						local alreadyExported = #()
						for p in theFilenameProps where (isProperty theRenderer p) do
						(
							local reFilename = getProperty theRenderer p
							if ( reFilename != undefined and reFilename != "" ) do
							(
								if SMTDSettings.purifyFilenames do reFilename = SMTDFunctions.purifyFilename reFilename
								if SMTDSettings.ForceLowerCaseFilenames do reFilename = toLower reFilename
								if SMTDSettings.purifyFilenames or SMTDSettings.ForceLowerCaseFilenames do setProperty theRenderer p reFilename
								if findItem alreadyExported reFilename == 0 do
								(
									case SMTDSettings.RegionRenderingMode of
									(
										#animationMultiRegion:
										(
											local addFrameDelimiter = false
											if (p == #output_rawFileName) then
												if (isProperty theRenderer #fileName_addDot) and (getProperty theRenderer #fileName_addDot) do addFrameDelimiter = true
											else
												addFrameDelimiter = true
											local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:currentTileString stripPaddingNumbers:false addFrameDelimiter:addFrameDelimiter
											format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
										)
										#singleFrameMultiRegion:
										(
											local theIndex = 0
											for aData in SMTDSettings.MultiRegionData where aData[1] == True do
											(
												for y2 = 1 to aData[7] do
												(
													for x2 = 1 to aData[6] do
													(
														local regionString = "_region_" + theIndex as string + "_"
														local addFrameDelimiter = false
														if (p == #output_rawFileName) then
															if (isProperty theRenderer #fileName_addDot) and (getProperty theRenderer #fileName_addDot) do addFrameDelimiter = true
														else
															addFrameDelimiter = true
														local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:regionString stripPaddingNumbers:false addFrameDelimiter:addFrameDelimiter
														
														format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
														theIndex += 1
													)
												)
											)
										)
										#singleFrameTiles:
										(
											local theIndex = 0
											for y = 1 to SMTDSettings.TilesInY do
											(
												for x = 1 to SMTDSettings.TilesInX do
												(
													local tileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string  + "_"
													local addFrameDelimiter = false
													if (p == #output_rawFileName) then
														if (isProperty theRenderer #fileName_addDot) and (getProperty theRenderer #fileName_addDot) do addFrameDelimiter = true
													else
														addFrameDelimiter = true
													local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:tileString stripPaddingNumbers:false addFrameDelimiter:addFrameDelimiter
													
													format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
													theIndex += 1
												)
											)
										)
										default: --anything else
										(										
											local addFrameDelimiter = false
											if (p == #output_rawFileName) then
												if (isProperty theRenderer #fileName_addDot) and (getProperty theRenderer #fileName_addDot) do addFrameDelimiter = true
											else
												addFrameDelimiter = true
											local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:"" stripPaddingNumbers:false addFrameDelimiter:addFrameDelimiter
											format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
										)
									)

									outputFilenameIndex += 1
									append alreadyExported reFilename
								)
							)--end if
						)--end p loop (VRAY RAW FILE ONLY)
						
						/*
						--Handle Lens Effects in VRay VFB, if enabled and set to save separate image files
						if (isProperty theRenderer #output_on) and (getProperty theRenderer #output_on) and (isProperty theRenderer #output_saveRawFile) and (getProperty theRenderer #output_saveRawFile) do
						(
							--Bloom:
							if (SMTDSettings.getVRayVFBProperty #bloom type:#boolean) == true and findItem #("image", "both") (SMTDSettings.getVRayVFBProperty #bloommode) > 0 do --bloom is on and a bloom image should be saved
							(
								local reFilename = getProperty theRenderer #output_rawFileName
								reFilename = getFileNamePath reFilename + getFileNameFile reFilename + getFileNameType reFilename
								local addFrameDelimiter = false
								if (p == #output_rawFileName) then
									if (isProperty theRenderer #fileName_addDot) and (getProperty theRenderer #fileName_addDot) do addFrameDelimiter = true
								else
									addFrameDelimiter = true
								local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:"" stripPaddingNumbers:false addFrameDelimiter:addFrameDelimiter

								format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
								outputFilenameIndex+=1
							)
						)
						*/
						
					)--end if VRAY RENDERER PATHS
				)

				-- VRAY SPECIFIC RE HANDLING CODE
				-- VRay renderer & VRay VFB ENABLED
				local theRenderer = SMTDFunctions.getRendererObject()
				if (SMTDFunctions.getRendererIdString() == "vray" OR SMTDFunctions.getRendererIdString() == "vrayrt") AND theRenderer.output_on then
				(
					-- VRay "Separate Render Channels" is ENABLED
					if theRenderer.output_splitgbuffer AND theRenderer.output_useram do --V-Ray Split Channels is disabled if "Memory frame buffer" is disabled in V-Ray FB settings
					(
						local reFilename = theRenderer.output_splitfilename

						if ( reFilename != undefined and reFilename != "" ) do
						(
							local replaceHashes = false
							try( replaceHashes = renderers.current.output_expandFrameNumber )catch()
						
							--splitRGB monitor output path
							if theRenderer.output_splitRGB then
							(
								local reFilename = theRenderer.output_splitfilename
								local reFilename = SMTDFunctions.ReturnVraySplitPath reFilename elementType:"RGB_color"
								
								case SMTDSettings.RegionRenderingMode of
								(
									#animationMultiRegion:
									(
										local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(currentTileString + ".RGB_color.") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
										format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
									)
									#singleFrameMultiRegion:
									(
										local theIndex = 0
										for aData in SMTDSettings.MultiRegionData where aData[1] == True do
										(
											for y2 = 1 to aData[7] do
											(
												for x2 = 1 to aData[6] do
												(
													local regionString = "_region_" + theIndex as string + "_"
													local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(regionString + ".RGB_color.") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
													format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
													theIndex += 1
												)
											)
										)
									)
									#singleFrameTiles:
									(
										local theIndex = 0
										for y = 1 to SMTDSettings.TilesInY do
										(
											for x = 1 to SMTDSettings.TilesInX do
											(
												local tileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string  + "_"
												local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(tileString + ".RGB_color.") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
												format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
												theIndex += 1
											)
										)
									)
									default: --anything else
									(
										local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(".RGB_color.") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
										format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
									)
								)

								outputFilenameIndex += 1
							)
							
							--splitAlpha monitor output path
							if theRenderer.output_splitAlpha then
							(
								local reFilename = theRenderer.output_splitfilename
								local reFilename = SMTDFunctions.ReturnVraySplitPath reFilename elementType:"Alpha"

								case SMTDSettings.RegionRenderingMode of
								(
									#animationMultiRegion:
									(
										local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(currentTileString + ".Alpha.") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
										format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
									)
									#singleFrameMultiRegion:
									(
										local theIndex = 0
										for aData in SMTDSettings.MultiRegionData where aData[1] == True do
										(
											for y2 = 1 to aData[7] do
											(
												for x2 = 1 to aData[6] do
												(
													local regionString = "_region_" + theIndex as string + "_"
													local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(regionString + ".Alpha.") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
													format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
													theIndex += 1
												)
											)
										)
									)
									#singleFrameTiles:
									(
										local theIndex = 0
										for y = 1 to SMTDSettings.TilesInY do
										(
											for x = 1 to SMTDSettings.TilesInX do
											(
												local tileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string  + "_"
												local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(tileString + ".Alpha.") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
												format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
												theIndex += 1
											)
										)
									)
									default: --anything else
									(
										local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(".Alpha.") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
										format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
									)
								)
								outputFilenameIndex += 1
							)

							--"Separate Render Channels" RE monitor output paths
							local reManager = maxOps.GetCurRenderElementMgr()
							if reManager != undefined do
							(
								if reManager.GetElementsActive() then --only write paths if the Render Elements are globally enabled
								(
									local reCount = reManager.NumRenderElements()
									for i = 0 to reCount - 1 do
									(
										reObject = reManager.GetRenderElement i
										if classof reObject != Missing_Render_Element_Plug_in AND classof reObject != VRayOptionRE AND classof reObject != VRayAlpha do
										(
											if hasProperty reObject "vrayVFB" and reObject.vrayVFB do
											(
												local reArtifactSuffixes = SMTDFunctions.RenderElementArtifactSuffixes(reObject)
												for reArtifactSuffix in reArtifactSuffixes do
												(
													local reFilename = reManager.GetRenderElementFilename i
													--If the render elements were never updated to have names, they will still be saved by V-Ray according to the Separate render channels / Separate folders options.
													if reFilename == undefined or reFilename  == "" do
													(
														reFilename = theRenderer.output_splitfilename
														if isProperty theRenderer #output_separateFolders and theRenderer.output_separateFolders == true do
														(
															reFilename = getFilenamePath reFilename + reArtifactSuffix + "\\" + filenameFromPath reFilename
														)
													)
													case SMTDSettings.RegionRenderingMode of
													(
														#animationMultiRegion:
														(
															local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(currentTileString+"."+ reArtifactSuffix +".") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
															format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
														)
														#singleFrameMultiRegion:
														(
															local theIndex = 0
															for aData in SMTDSettings.MultiRegionData where aData[1] == True do
															(
																for y2 = 1 to aData[7] do
																(
																	for x2 = 1 to aData[6] do
																	(
																		local regionString = "_region_" + theIndex as string + "_"
																		local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(regionString + "." + reArtifactSuffix + ".") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
																		format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
																		theIndex += 1
																	)
																)
															)
														)
														#singleFrameTiles:
														(
															local theIndex = 0
															for y = 1 to SMTDSettings.TilesInY do
															(
																for x = 1 to SMTDSettings.TilesInX do
																(
																	local tileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string  + "_"
																	local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:(tileString + "." + reArtifactSuffix + ".") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
																	format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
																	theIndex += 1
																)
															)
														)
														default: --anything else
														(
															local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:("." + reArtifactSuffix + ".") stripPaddingNumbers:false addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
															format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
														)
													)
													outputFilenameIndex += 1
												)
											)--end if VRAY VFB is enabled
										)--end if not missing RE
									)--end i loop
								)--end if REs active
							)--end if reManager not undefined
						)--end if reFilename valid
					)--end if splitgbuffer
				)--end if vray and output on
				else
				(
					elementsToSkip = #()
					
					-- if this is 3dsmax 2011 or later, check to see if we're rendering to the new adsk exr format
					if ((maxVersion())[1]/1000 as integer) >= 13 do
					(
						if rendSaveFile and rendOutputFilename != undefined do
						(
							rend_type = getFileNameType rendOutputFilename
							is_exr = matchPattern rend_type pattern:".exr" ignoreCase:true
							is_fxr = matchPattern rend_type pattern:".fxr" ignoreCase:true
							
							-- If we are, we need to tell Deadline which render elements are to be embedded in the exr file so that it doesn't save them separately
							if (is_exr or is_fxr) and (fopenexr != undefined) do
							(
								if fopenexr.isAutoAddRenderElements() then
								(
									--The elements are being added automatically, so check the re manager.
									local reManager = maxOps.GetCurRenderElementMgr()
									if reManager != undefined do
									(
										if reManager.GetElementsActive() then 
										(
											local reCount = reManager.NumRenderElements()
											for i = 0 to reCount - 1 do
											(
												local theElement = reManager.GetRenderElement i
												if classof theElement != Missing_Render_Element_Plug_in AND classof theElement != VRayOptionRE do
													if theElement.enabled do
														append elementsToSkip theElement.elementName
											)
										)
									)--end if reManager undefined
								)
								else
								(
									--The elements are manually specified, so check the layers in the exr itself
									for i = 0 to fopenexr.numLayers() do
									(
										if (fopenexr.getLayerType i) == 1 then
											append elementsToSkip (fopenexr.getLayerName i)
									)
								)
							)
						)
					)
					
					-- generic loop to dump all RE's to OutputFilename# if applicable
					local reManager = maxOps.GetCurRenderElementMgr()
					if reManager != undefined do
					(
						if reManager.GetElementsActive() then --only write paths if the Render Elements are globally enabled
						(
							local reCount = reManager.NumRenderElements()
							for i = 0 to reCount - 1 do
							(
								reObject = reManager.GetRenderElement i
								if classof reObject != Missing_Render_Element_Plug_in AND reObject.enabled AND classof reObject != VRayOptionRE then
								(
									if (findItem elementsToSkip reObject.elementName) == 0 do
									(
										local reFilename = reManager.GetRenderElementFilename i

										if ( reFilename != undefined and reFilename != "" ) do
										(
											if SMTDSettings.purifyFilenames do reFilename = SMTDFunctions.purifyFilename reFilename
											if SMTDSettings.ForceLowerCaseFilenames do reFilename = toLower reFilename
											if SMTDSettings.purifyFilenames or SMTDSettings.ForceLowerCaseFilenames  do reManager.SetRenderElementFilename i reFilename
											if SMTDSettings.SubmitSceneMode == #networkremap do reFilename = ::SMTD_RemapLocalToNetworkPath reFilename

											case SMTDSettings.RegionRenderingMode of
											(
												#animationMultiRegion:
												(
													local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:currentTileString stripPaddingNumbers:false addFrameDelimiter:true
													format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
												)
												#singleFrameMultiRegion:
												(
													local theIndex = 0
													for aData in SMTDSettings.MultiRegionData where aData[1] == True do
													(
														for y2 = 1 to aData[7] do
														(
															for x2 = 1 to aData[6] do
															(
																local regionString = "_region_" + theIndex as string + "_"
																local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:regionString stripPaddingNumbers:false addFrameDelimiter:true
																format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
																theIndex += 1
															)
														)
													)
												)
												#singleFrameTiles:
												(
													local theIndex = 0
													for y = 1 to SMTDSettings.TilesInY do
													(
														for x = 1 to SMTDSettings.TilesInX do
														(
															local tileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string  + "_"
															local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:tileString stripPaddingNumbers:false addFrameDelimiter:true
															format "OutputFilename%Tile%=%\n" outputFilenameIndex theIndex tempFile to:submitInfoFile
															theIndex += 1
														)
													)
												)
												default: --anything else
												(
													local tempFile = SMTDFunctions.GetFormattedOutputFilename reFilename stereoCameraToken:stereoCameraLabel regionString:"" stripPaddingNumbers:false addFrameDelimiter:true
													format "OutputFilename%=%\n" outputFilenameIndex tempFile to:submitInfoFile
												)
											)
											outputFilenameIndex += 1
										)--end if refilename is valid
									)--end if not skipping this RE
								)--end if valid and enabled	RE
							)--end i loop (render elements iterator)
						)--end if REs active
					)--end if reManager not undefined
				)--end else loop
				
				for aFile in SMTDSettings.ExtraOutputFilenames do
				(
					format "OutputFilename%=%\n" outputFilenameIndex aFile to:submitInfoFile
					outputFilenameIndex += 1
				)

				local limitGroups = ""	--initialize Limits to empty string
				local limitGroupsToUseArray = for i in SMTDSettings.LimitGroupsToUse collect i

				--if the workstation mode is forced, add the limit group for the current plugin
				if SMTDSettings.LimitGroupAutoWorkstation == true do
				(
					if SMTDSettings.forceWorkstationMode do   --OR SMTDSettings.SubmitAsMXSJob --MXS job should not require WS unless explicitly requested
						append limitGroupsToUseArray (pluginToUse + (SMTDFunctions.getMaxVersion()) + "workstation")
				)

				--if the renderer is X, add the X limit group to the string. now in alphabetical order, and lower case!
				local rendID = SMTDFunctions.getRendererIdString()
				if SMTDSettings.LimitGroupAutoArnold == true 		AND rendID == "arnold" 		do appendIfUnique limitGroupsToUseArray "arnold"
				if SMTDSettings.LimitGroupAutoBrazil == true 		AND rendID == "brmax" 		do appendIfUnique limitGroupsToUseArray "brazil"
				if SMTDSettings.LimitGroupAutoCorona == true 		AND rendID == "corona" 		do appendIfUnique limitGroupsToUseArray "corona"
				if SMTDSettings.LimitGroupAutoFinalRender == true 	AND rendID == "finalrender"	do appendIfUnique limitGroupsToUseArray "finalrender"				
				if SMTDSettings.LimitGroupAutoIray == true 			AND rendID == "iray"		do appendIfUnique limitGroupsToUseArray "iray"				
				if SMTDSettings.LimitGroupAutoKrakatoa == true 		AND rendID == "krakatoa" 	do appendIfUnique limitGroupsToUseArray "krakatoa"				
				if SMTDSettings.LimitGroupAutoMaxIO == true 									do appendIfUnique limitGroupsToUseArray "max"
				if SMTDSettings.LimitGroupAutoMaxwell == true 		AND rendID == "maxwell" 	do appendIfUnique limitGroupsToUseArray "maxwell"
				if SMTDSettings.LimitGroupAutoOctane == true 		AND rendID == "octane"		do appendIfUnique limitGroupsToUseArray "octane"
				if SMTDSettings.LimitGroupAutoRedshift == true 		AND rendID == "redshift" 	do appendIfUnique limitGroupsToUseArray "redshift"
				if SMTDSettings.LimitGroupAutoVray == true 			AND rendID == "vray" 		do appendIfUnique limitGroupsToUseArray "vray"
				if SMTDSettings.LimitGroupAutoVray == true 			AND rendID == "vrayrt" 		do appendIfUnique limitGroupsToUseArray "vrayrt"

				for i = 1 to limitGroupsToUseArray.count do
				(
					limitGroups += limitGroupsToUseArray [i] 
					if i < limitGroupsToUseArray.count do limitGroups += ","
				)	

				--if any Limits have been collected, output them						
				if limitGroups != "" do format "LimitGroups=%\n" limitGroups to:submitInfoFile

				--if limit is requested, set it, otherwise output 0 (no limit)
				if SMTDSettings.limitEnabled then
					format "MachineLimit=%\n" SMTDSettings.machineLimit to:submitInfoFile
				else	
					format "MachineLimit=0\n" to:submitInfoFile

				format "OnJobComplete=%\n" SMTDSettings.OnComplete to:submitInfoFile

				format "Interruptible=%\n" SMTDSettings.JobIsInterruptible to:submitInfoFile

				if SMTDSettings.CopyVbscriptFile do
					format "PostJobScript=copyImsq.py\n" to:submitInfoFile

				format "OverrideJobFailureDetection=%\n"  SMTDSettings.OverrideJobFailureDetection to:submitInfoFile	
				format "FailureDetectionJobErrors=%\n" SMTDSettings.FailureDetectionJobErrors to:submitInfoFile  
				format "OverrideTaskFailureDetection=%\n"SMTDSettings.OverrideTaskFailureDetection to:submitInfoFile  
				format "FailureDetectionTaskErrors=%\n" SMTDSettings.FailureDetectionTaskErrors to:submitInfoFile  
				format "SendJobErrorWarning=%\n" SMTDSettings.SendJobErrorWarning  to:submitInfoFile 

				local tileRender = findItem #(#animationTiles, #singleFrameTiles,#singleFrameMultiRegion, #animationMultiRegion) SMTDSettings.RegionRenderingMode > 0

				-- Code for determining whether ot not we are using group batch, and if so setting batch name.
				if not tileRender then
				(
					local groupBatch = false

					if SMTDFunctions.searchIntegrationKVPs "integrationSettingsPath" then
					(
						if SMTDFunctions.searchIntegrationKVPs "batchMode" then
						(
							batchModeIndex = SMTDFunctions.findIntegrationKVPIndex "batchMode"
							if ::SMTD_IntegrationKVPs[batchModeIndex][2] == "True" then
							(
								groupBatch = true
							)
						)
					)

					if groupBatch and batchName == "" then
					(
						batchName = formattedJobName
					)
				)
				
				format "ExtraInfo0=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo0) to:submitInfoFile
				format "ExtraInfo1=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo1) to:submitInfoFile
				format "ExtraInfo2=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo2) to:submitInfoFile
				format "ExtraInfo3=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo3) to:submitInfoFile
				format "ExtraInfo4=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo4) to:submitInfoFile
				format "ExtraInfo5=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo5) to:submitInfoFile
				format "ExtraInfo6=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo6) to:submitInfoFile
				format "ExtraInfo7=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo7) to:submitInfoFile
				format "ExtraInfo8=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo8) to:submitInfoFile
				format "ExtraInfo9=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo9) to:submitInfoFile
				
				--ExtraInfoKeyValues
				local kvpIndex = 0
				if SMTDFunctions.searchIntegrationKVPs "extraKVPIndex" then
				(
					kvpIndex = ::SMTD_IntegrationKVPs[SMTDFunctions.findIntegrationKVPIndex "extraKVPIndex"][2]
				)
				
				for kvi in SMTDSettings.ExtraInfoKeyValues do
				(
					try
					(
						format "ExtraInfoKeyValue%=%=%\n" kvpIndex kvi[1] kvi[2] to:submitInfoFile		
						kvpIndex += 1
					)catch()
				)
				
				--EnvironmentKeyValues
				kvpIndex = 0
				for kvi in SMTDSettings.EnvironmentKeyValues do
				(
					try
					(
						format "EnvironmentKeyValue%=%=%\n" kvpIndex kvi[1] kvi[2] to:submitInfoFile
						kvpIndex += 1
					)catch()
				)
				format "IncludeEnvironment=%\n" SMTDSettings.IncludeEnvironment to:submitInfoFile
				format "UseJobEnvironmentOnly=%\n" SMTDSettings.UseJobEnvironmentOnly to:submitInfoFile

				if batchName != undefined and batchName != "" then
				(
					format "BatchName=%\n" batchName to:submitInfoFile
				)
				
				for aKeyPair in SMTDSettings.ExtraJobInfoKeys where isKindOf aKeyPair Array and aKeyPair.count == 2 do
				(
					format "%=%\n" aKeyPair[1] aKeyPair[2] to:submitInfoFile
				) 			

				local assetID = 0		
				if SMTDSettings.AssetsIncludeFilesInJob == true do				
				if ( SMTDFunctions.writeSceneFileToFile ("AWSAssetFile0" ) submitInfoFile) do
					assetID += 1
				
				close submitInfoFile
				
				-- WRITE ASSETS FOR AWS CLOUD SYNC HERE
				if SMTDSettings.AssetsIncludeFilesInJob == true do
				(
					SMTDSettings.AssetsResolved = SMTDFunctions.resolveAssetsFromAssetTracker SubmitExternalFilesMode:3
					
					local st123 = timestamp()
					local theSStream = "" as stringStream
					for anAsset in SMTDSettings.AssetsResolved do
					(
						format "AWSAssetFile%=%\r\n" assetID anAsset to:theSStream
						assetID += 1
					)
					(dotNetClass "System.IO.File").AppendAllText filename (theSStream as string)
					try(SMTD_MainRollout.Ui_report ("+"+assetID as string+" AWSAssetFile entr"+(if assetID == 1 then "y" else "ies")+" written in "+ ((timestamp()-st123)/1000.0) as string + " sec.") )catch()
				)

				if not tileRender then
				(
					SMTDFunctions.ConcatenatePipelineSettingsToJob SMTDPaths.SubmitInfoFile formattedJobName
				)
				true
			)
			else
				false
		),
		
		fn getListAsString theList =
		(
			local theListString = ""
			if theList.count > 0 do
			(
				for i = 1 to theList.count-1 do 
					theListString += theList[i] + ","
				theListString += theList[theList.count]
			)
			theListString
		),
		
		fn getDelimiterToken =
		(
			--Decide once on delimiters and stereo labels, then reuse for all filenames below
			local delimiter = SMTDSettings.Delimiter
			if SMTDSettings.RemovePadding AND (findItem #(#none, #maxRegion, #singleFrameTiles, #singleFrameMultiRegion) SMTDSettings.RegionRenderingMode > 0) do delimiter = ""
			delimiter 
		),
		
		fn GetFormattedOutputFilename theRenderOutput addFramePadding:true stereoCameraToken:"" regionString:"" stripPaddingNumbers:true addFrameDelimiter:true replaceHashesWithFramePadding:false =
		(
			--format "theRenderOutput=%\n" theRenderOutput
			if theRenderOutput == undefined or theRenderOutput == "" do return ""
			local TokenPattern = SMTDSettings.OutputFilenamePattern 						--a copy of the pattern for token substitution
			local TokenDelimiter = SMTDSettings.OutputFilenameTokenDelimiter				--the token delimiter string, default is "_"
			
			if findString theRenderOutput "#" == undefined do
			(
				replaceHashesWithFramePadding = false
			)
			if SMTDSettings.purifyFilenames do 
				theRenderOutput = SMTDFunctions.purifyFilename theRenderOutput				--purify the new filename if requested
			
			local basePath = getFilenamePath theRenderOutput								--the path portion of the filename
			local baseName = getFilenameFile theRenderOutput								--the base portion (no path, no extension) of the filename
			local baseType = getFilenameType theRenderOutput								--the extension of the filename
			local delimiter = SMTDFunctions.getDelimiterToken()								--the delimiter to add between base portion and frame number/padding
			local stateSetName = SMTDSettings.StateSetName				 					--the state set name, "" if no state set is being submitted
			if not SMTDSettings.StateSetRenameOutput or not SMTDSettings.StateSetsSubmit do --if renaming the SS output was disabled, or not an SS submission
				stateSetName = "" 															--reset the token to empty string
			
			local paddingString = ""														--assume no frame number padding in the beginning
			if addFramePadding == true then 												--the path is being formatted for Monitor right click menus, or for single frame region rendering
			(
				-- Need to watch out for the special case where the output filename already ends in 4 digits.
				-- In this case, we need to strip the 4 digits before adding the "####" part.
				if stripPaddingNumbers == true and replaceHashesWithFramePadding == false  do
				(
					if rendTimeType != 1 and baseName.count > 4 and baseName[baseName.count] != "." then	--if not single frame saving, and the file name is longer than 4, and does not end with a dot,
					(
						try
						(
							padding = (substring baseName (baseName.count - 3) -1) as integer				--see if the last 4 characters produce an integer
							if padding != undefined do														--if they do, strip them from the name
								baseName = substring baseName 1 (baseName.count - 4)
						)
						catch()
					)
				)

				paddingString = "####" 															--this will be the padding when rendering animated regions
				if ( (findItem #(#singleFrameTiles, #singleFrameMultiRegion) SMTDSettings.RegionRenderingMode > 0) or rendTimeType == 1 ) and replaceHashesWithFramePadding == false do
					paddingString = formattedPrint (currentTime.frame as integer) format:"04i" 	--this will be the padding if rendering single frame regions or full frame
			
				if SMTDSettings.RemovePadding and rendTimeType == 1 do paddingString = ""		--this will be the padding if remove padding was requested while rendering a single frame
				if paddingString == "" or addFrameDelimiter == false do delimiter = ""			--in that case, or if requested via parameter, the frame delimiter will be dropped, too
			)
			--else
			(
				if matchPattern baseName pattern:("*"+stereoCameraToken+tokenDelimiter+"*") do stereoCameraToken = ""	--if the stereo token is already included, do not add it again
			)
			
			TokenPattern = substituteString TokenPattern "$SC" stereoCameraToken			--replace stereo camera token
			TokenPattern = substituteString TokenPattern "$SS" stateSetName					--replace state set name token
			TokenPattern = substituteString TokenPattern "$BN" baseName						--replace base name token
			TokenPattern = substituteString TokenPattern "$TD" tokenDelimiter				--replace token delimiter
			TokenPattern = substituteString TokenPattern "$"   "_"							--replace any leftover $ with underscore
			if replaceHashesWithFramePadding do
			(
				newTokenPattern = substituteString TokenPattern "#" paddingString							--replace replace all hashes with the full frame padding string
				
				if newTokenPattern != TokenPattern do
				(
					TokenPattern = newTokenPattern
					delimiter  = ""
					paddingString = ""
					
					if substring regionString regionString.count regionString.count == "." do
					(
						regionString = substring regionString 1 (regionString.count - 1)
					)
					 
				)
			)
				
			TokenPattern = substituteString TokenPattern (tokenDelimiter+tokenDelimiter) tokenDelimiter									--replace double delimiter tokens with single delimiter
			if matchPattern TokenPattern pattern:(tokenDelimiter+"*") do TokenPattern = substring TokenPattern 2 -1						--strip prefix delimiter
			--if matchPattern TokenPattern pattern:("*"+tokenDelimiter) do TokenPattern = substring TokenPattern 1 (TokenPattern.count-1)	--strip suffix delimiter
			
			if addFrameDelimiter == false do delimiter = ""																	--if no delimiter requested, make it empty string
				
			TokenPattern += regionString																					--append the region signature
			TokenPattern += delimiter																						--append the frame delimiter
			TokenPattern += paddingString																					--append the padding string
			TokenPattern += basetype																						--append the type extension
			
			local newFilename = basePath + TokenPattern																		--combine the path with the replaced token

			if SMTDSettings.ForceLowerCaseFilenames do newFilename = toLower newFilename									--lowercase the filename if requested
			if SMTDSettings.SubmitSceneMode == #networkremap do newFilename = ::SMTD_RemapLocalToNetworkPath newFilename 	--remap the path if requested
			
			--format "newFilename=%\n" newFilename
			--format "-------------------------------------------\n"

			newFilename
		),		
		
		fn getRendOutputFilename renderOutput tileString:"" stereoCameraToken:"" addFrameDelimiter:true =
		(
			if not rendSaveFile or renderOutput == undefined or renderOutput == "" do return ""
			SMTDFunctions.GetFormattedOutputFilename rendOutputFilename addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraToken stripPaddingNumbers:true addFrameDelimiter:addFrameDelimiter
		),
		
		fn getVRayVFBProperty propName type:#default =
		(
			try
			(
				local theVal = vfbControl propName
				if theVal == OK then 
					undefined 
				else
					case type of
					(
						default: theVal[1]
						#boolean: (theVal[1] != 0)
					)
			)
			catch undefined
		),
		
		fn setVRayVFBProperty propName newValue =
		(
			try
			(
				vfbControl propName newValue
			)
			catch undefined
		),
		
		fn ExploreSubmissionInfoFiles source:#job =
		(
			SMTDFunctions.createSubmissionFolderAndUpdatePaths() --create a new submission folder
			renderSceneDialog.commit()
			local tileString = ""
			local forceCamera = ""
			local stereoCameraLabel = ""
			SMTDSettings.StateSetName =	""
			if SMTDSettings.StateSetsSubmit and SMTDSettings.StateSetRenameOutput do 
			(
				local stateSetsListArray = SMTDSettings.StateSetsList as array
				if stateSetsListArray.count > 0 do
				(
					local ssP = try(dotNetObject "Autodesk.Max.StateSets.Plugin")catch(undefined)
					if ssP != undefined do
					(
						::SMTD_StateSetsTreeForSubmission = #()
						StateSetsRootEntry = ssP.Instance.EntityManager.RootEntity
						SMTDFunctions.getStateSetChildrenForSubmissionRecursive StateSetsRootEntry.MasterStateSet #()
					)
					--if SMTD_StateSetsTreeForSubmission.count == SMTD_StateSetsTree.count then
					(
						SMTDSettings.StateSetName =	SMTD_StateSetsTreeForSubmission[stateSetsListArray[1]][3]
					)
				)
			)
			theCamera = viewport.getcamera()
			if isValidNode theCamera do forceCamera = theCamera.name
			local theCameras = SMTDFunctions.GetStereoCamerasFromCurrentView()
			if theCameras.count > 1 and SMTDSettings.StereoCameraMode != #off then
			(
				local theCamerasToSubmit = case SMTDSettings.StereoCameraMode of
				(
					#leftright: #(#(theCameras[1], theCameras[2]), #( SMTDSettings.LeftEyeTag, SMTDSettings.RightEyeTag) )
					#center: (if theCameras.count > 2 then #(#(theCameras[3]), #( SMTDSettings.CenterEyeTag)) else #(#(),#())) --make sure there IS a center camera
					default: #(#(theCameras[1]), #( SMTDSettings.LeftEyeTag) )
					#right: #(#(theCameras[2]), #( SMTDSettings.RightEyeTag) )
					#all: #(theCameras, #( SMTDSettings.LeftEyeTag, SMTDSettings.RightEyeTag, SMTDSettings.CenterEyeTag))
				)
				forceCamera = theCamerasToSubmit[1][1].name
				stereoCameraLabel = theCamerasToSubmit[2][1]
			)
			
			
			SMTDFunctions.RenderElementsStorePaths()
			--SMTDFunctions.storeRenderElementNames()
			
			local oldrendOutputFilename = rendOutputFilename --capture the current output filename
			if SMTDSettings.ReplaceOutputFilenameWithUserPattern do
			(
				OutputFilenameByUserPattern = copy SMTDSettings.OutputFilenameUserPattern
				OutputFilenameByUserPattern = substituteString OutputFilenameByUserPattern "$user" SMTDSettings.userName
				local theMaxFileName = (getFileNameFile maxFileName)
				if theMaxFileName == "" do theMaxFileName = "Untitled"
				OutputFilenameByUserPattern = substituteString OutputFilenameByUserPattern "$scene" theMaxFileName
				
				local theFilterTime = filterString localtime " /\\-:."
				local theTime = ""
				for i = 1 to theFilterTime.count-1 where (classof (execute theFilterTime[i]) != Integer) do deleteItem theFilterTime i
				for i = 1 to theFilterTime.count-1 do theTime += theFilterTime[i] + "_"
				theTime += theFilterTime[theFilterTime.count]	
				OutputFilenameByUserPattern = substituteString OutputFilenameByUserPattern "$date" theTime
				OutputFilenameByUserPattern = substituteString OutputFilenameByUserPattern "$" "_"
				makeDir (getFileNamePath OutputFilenameByUserPattern) all:true
				if doesFileExist (getFileNamePath OutputFilenameByUserPattern) do
				(
					rendOutputFilename = OutputFilenameByUserPattern
				)
			)

			if SMTDSettings.StrictOutput == true then
			(
				if RendOutputFilename != "" then
				(						   
					try(SMTD_MainRollout.Ui_report ">Strict Output Check...")catch()
					local theRenderPath = getFilenamePath RendOutputFilename
					local directory = getFilenameFile maxFilename
					local filename = getFilenameFile maxFilename
					local extension = getFilenameType RendOutputFilename
								
					-- if the output path already contains the max filename, assume that
					-- it already contains the correct directory structure, so we don't keep
					-- appending directories everytime the job is submitted
					if findString theRenderPath directory != undefined then
						RendOutputFilename = theRenderPath + filename + extension
					else
						RendOutputFilename = theRenderPath + directory + "\\" + filename + extension
					try(SMTD_MainRollout.Ui_report ("+Strict Output is ["+RendOutputFilename+"]"))catch()
				)
			)--end strict output

			SMTDFunctions.RenderElementsUpdatePaths()			
			
			theFile = case source of
			(
				#job: SMTDPaths.tempdir + "\\explore_jobInfoFile.job"
				default: SMTDPaths.tempdir + "\\explore_pluginInfoFile.job"
			)
			case source of
			(
				#job: SMTDFunctions.CreateSubmitInfoFile theFile batchName:"" currentTileString:tileString stereoCameraLabel:stereoCameraLabel
				default: SMTDFunctions.CreateJobInfoFile theFile tileString:tileString forceCamera:forceCamera stereoCameraLabel:stereoCameraLabel
			)

			rendOutputFilename = oldrendOutputFilename
			SMTDFunctions.RenderElementsRestorePaths()

			--SMTDFunctions.RenderElementsUpdatePaths()	
			--SMTDFunctions.restoreRenderElementNames() --Restore original Render Element names 
			SMTDSettings.StateSetName =	""
			local resultArray = ( dotNetClass "System.IO.File" ).ReadAllLines theFile
			resultArray
		),
		
		--THIS IS NOW CALLED PLUGIN INFO FILE!
		fn CreateJobInfoFile filename renderOutputOverride:"" tileString:"" forceCamera:"" stereoCameraLabel:"" =
		(
			local JobInfoFile = CreateFile filename encoding:#utf8 writeBOM:true
			if (JobInfoFile != undefined) then
			(
				local maxVersionToUse = SMTDFunctions.getMaxVersion()
				format "Version=%\n" maxVersionToUse to:JobInfoFile
				
				try
				(
					local VersionInfo = dotnetclass "System.Diagnostics.FileVersionInfo"
					local MyMax = VersionInfo.GetVersionInfo (pathConfig.appendPath (pathConfig.GetDir #maxroot) "3dsmax.exe")
					format "SubmittedFromVersion=%\n" MyMax.FileVersion to:JobInfoFile	
				)catch()

				try
				(
					local rendererName = renderers.current as string
					local rendererId = renderers.current.classid as string
					format "SubmittedRendererName=%\n" rendererName to:JobInfoFile
					format "SubmittedRendererId=%\n" rendererId to:JobInfoFile
				)catch()
				
				-- Design edition retired in Max 2016.
				if( SMTDFunctions.getMaxVersionAsInteger() >= 2010 and SMTDFunctions.getMaxVersionAsInteger() < 2016 ) then
					if( maxOps.productID == #3dsMaxDesign ) then
						format "IsMaxDesign=1\n" to:JobInfoFile
					else
						format "IsMaxDesign=0\n" to:JobInfoFile
				else
					format "IsMaxDesign=0\n" to:JobInfoFile
				
				SMTDFunctions.writeSceneFileToFile "SceneFile" JobInfoFile

				--Store Current Scene Selection
				local theSelectionArray = for o in selection collect o.inode.handle
				with PrintAllElements on format "SceneSelection=%\n" theSelectionArray to:JobInfoFile

				format "Padding=%\n" 4 to:JobInfoFile
				format "RemovePadding=%\n" (if SMTDSettings.RemovePadding and rendTimeType == 1 then 1 else 0) to:JobInfoFile
				
				format "IgnoreMissingExternalFiles=%\n" (if SMTDSettings.IgnoreMissingExternalFiles then 1 else 0) to:JobInfoFile
				format "IgnoreMissingUVWs=%\n" (if SMTDSettings.IgnoreMissingUVWs then 1 else 0) to:JobInfoFile
				format "IgnoreMissingDLLs=%\n" (if SMTDSettings.IgnoreMissingDLLs then 1 else 0) to:JobInfoFile
				format "IgnoreMissingXREFs=%\n" (if SMTDSettings.IgnoreMissingXREFs then 1 else 0) to:JobInfoFile
				format "DisableMultipass=%\n" (if SMTDSettings.DisableMultipass then 1 else 0) to:JobInfoFile
				format "LocalRendering=%\n" (if SMTDSettings.LocalRendering then 1 else 0) to:JobInfoFile
				format "RenderThreads=%\n" ( SMTDSettings.RenderThreads ) to:JobInfoFile
				format "DumpFileProperties=%\n" (if SMTDSettings.DumpFileProperties then true else false) to:JobInfoFile

				if SMTDFunctions.getMaxVersionAsInteger() >= 2013 then
				(
					if SMTDSettings.OverrideLanguage then
					(
						local theIndex = SMTDSettings.Language
						if theIndex == 0 do
						(
							local languageInfo = sysinfo.GetMaxLanguage()
							local languageCode = languageInfo[3] 
							theIndex = findItem SMTDSettings.LanguageCodeArray languageCode
						)
					
						if theIndex > 0 then
							format "Language=%\n" SMTDSettings.LanguageCodeArray[theIndex] to:JobInfoFile
						else
							format "Language=Default\n" to:JobInfoFile
					)
					else
						format "Language=Default\n" to:JobInfoFile
				)
				
				if SMTDSettings.forceWorkstationMode OR (SMTDSettings.UseBatchRender AND SMTDSettings.BatchRenderMode == 2) then
				(
					format "UseSlaveMode=0\n" to:JobInfoFile
					if SMTDSettings.UseSilentMode then
						format "UseSilentMode=1\n" to:JobInfoFile
					else
						format "UseSilentMode=0\n" to:JobInfoFile
				)
				else
				(
					format "UseSlaveMode=1\n" to:JobInfoFile
					format "UseSilentMode=0\n" to:JobInfoFile
				)
				
				if SMTDSettings.PopupHandling then
					format "PopupHandling=1\n" to:JobInfoFile
				else
					format "PopupHandling=0\n" to:JobInfoFile
				
				if SMTDSettings.UsePathConfigFile then
				(
					if SMTDSettings.SubmitSceneMode == #reposave then
					(
						format "PathConfigFile=%\n" (FileNameFromPath SMTDSettings.PathConfigFile) to:JobInfoFile
					)
					else
						format "PathConfigFile=%\n" SMTDSettings.PathConfigFile to:JobInfoFile

					if SMTDSettings.MergePathConfigFile then
						format "MergePathConfigFile=1\n" to:JobInfoFile
					else
						format "MergePathConfigFile=0\n" to:JobInfoFile
				)
				
				if SMTDSettings.IncludeLocalPaths then
				(
					format "IncludeLocalPaths=1\n" to:JobInfoFile
					local pathCount = pathConfig.mapPaths.count()
					format "LocalMapPathsCount=%\n" pathCount to:JobInfoFile
					for j = 1 to pathCount do 
						format "LocalMapPath%=%\n" j (pathConfig.mapPaths.get j) to:JobInfoFile
				)
				else
					format "IncludeLocalPaths=0\n" to:JobInfoFile
				
				
				if SMTDSettings.StateSetsSubmit and SMTDSettings.SubmitSceneMode != #reposave then
				(
					format "RenderStateSet=1\n" to:JobInfoFile
					format "StateSetToRender=%\n" SMTDSettings.StateSetToRender to:JobInfoFile
				)
				else
					format "RenderStateSet=0\n" to:JobInfoFile			

				if rendTimeType == 2 or rendTimeType == 3 then
					format "FrameNumberBase=%\n" rendFileNumberBase to:JobInfoFile
				
				format "RestartRendererMode=%\n" ( if SMTDSettings.RestartRenderer then 1 else 0 ) to:JobInfoFile
				format "DisableProgressUpdateTimeout=%\n" ( if SMTDSettings.DisableProgressUpdateTimeout then 1 else 0 ) to:JobInfoFile
				format "SkipRender=%\n" ( if SMTDSettings.SkipRender then 1 else 0 ) to:JobInfoFile

				if SMTDSettings.MaxTasksPerSlave > 1 then 
				(
					format "OverrideFailOnExistingMaxProcess=true\n" to:JobInfoFile
					format "FailOnExistingMaxProcess=false\n" to:JobInfoFile
				)
				else
				(
					format "OverrideFailOnExistingMaxProcess=%\n" SMTDSettings.OverrideFailOnExistingMaxProcess to:JobInfoFile
					format "FailOnExistingMaxProcess=%\n" SMTDSettings.FailOnExistingMaxProcess to:JobInfoFile				
				)				
				  
				if SMTDSettings.IsBakeJob then
				(
					bakeString = "BakeObjs="
					
					for o in SMTD_objsToBake do 
						bakeString += o.name + ","
					
					bakeString[bakestring.count] = "\n"
					
					format bakeString to:JobInfoFile
					
					if SMTDSettings.BakeJobOneObjectPerTask == true then
						format "BakeObjsOnePerTask=true\n" to:JobInfoFile
					else
						format "BakeObjsOnePerTask=false\n" to:JobInfoFile
				)

				if not SMTDSettings.DBR do
				(
					format "GPUsPerTask=%\n" SMTDSettings.GpusPerTask to:JobInfoFile
					format "GPUsSelectDevices=%\n" SMTDSettings.GpuDevices to:JobInfoFile
				)
				
				--MR/VRay off-load DBR job submission
				if SMTDSettings.DBR do
				(
					local rendererID = SMTDFunctions.getRendererIdString()
					if (rendererID == "mentalray") do
						format "MentalRayDBRJob=true\n" to:JobInfoFile
					if (rendererID == "vray") do
						format "VRayDBRJob=true\n" to:JobInfoFile
					if (rendererID == "vrayrt") do
						format "VRayRtDBRJob=true\n" to:JobInfoFile
					if (rendererID == "corona") do
						format "CoronaDBRJob=true\n" to:JobInfoFile
					
					local dbrFrame = SMTDFunctions.GetSequenceString #(currentTime.frame as integer)
					format "DBRJobFrame=%\n" dbrFrame to:JobInfoFile

					--3dsCmd specific render flags
					format "Application=Max\n" to:JobInfoFile
					format "Build=%\n" SMTDSettings.MaxVersionToForce to:JobInfoFile
					format "PixelAspect=%\n" renderPixelAspect to:JobInfoFile
					format "ImageWidth=%\n" renderWidth to:JobInfoFile
					format "ImageHeight=%\n" renderHeight to:JobInfoFile
					
					-- If the V-Ray / V-Ray RT frame buffer is on, then disable the max frame buffer
					local theRenderer = SMTDFunctions.getRendererObject()
					if (SMTDFunctions.getRendererIdString() == "vray" OR SMTDFunctions.getRendererIdString() == "vrayrt") AND theRenderer.output_on then
						format "ShowVFB=0\n" to:JobInfoFile
					else
					(
						if SMTDSettings.ShowFrameBuffer then
							format "ShowVFB=1\n" to:JobInfoFile
						else
							format "ShowVFB=0\n" to:JobInfoFile
					)

					format "ContinueOnError=True\n" to:JobInfoFile

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

					local reMgr = maxOps.GetCurRenderElementMgr()
					if reMgr != undefined do
					(
						if reMgr.GetElementsActive() then
							format "RenderElements=true\n" to:JobInfoFile
						else
							format "RenderElements=false\n" to:JobInfoFile
					)
				)--end MR/VRay off-load DBR job submission
				
				local theCam = viewport.getCamera() --get viewport camera
				if forceCamera == "" then --no forced camera
				(
					if isValidNode theCam then --if it is valid, output it
						format "Camera=%\n" (theCam.name) to:JobInfoFile
					else					
						format "Camera=\n" to:JobInfoFile --if viewport is not a camera, output no camera.
				)	
				else	
					format "Camera=%\n" forceCamera to:JobInfoFile --if camera was supplied, force output to it.
				
				format "Camera0=\n" to:JobInfoFile

				--Write out all cameras found in the current scene:								
				local theCameras = for c in objects where findItem Camera.classes (classof c) > 0 collect c
				for c = 1 to theCameras.count do
					format "Camera%=%\n" c theCameras[c].name to:JobInfoFile
				--If the current view is not a camera (it could be a light for example), make sure it is added to the list, otherwise the list would be invalid
				if isValidNode theCam AND findItem theCameras theCam == 0 do
					format "Camera%=%\n" (theCameras.count+1) theCam.name to:JobInfoFile
				
				if SMTDSettings.RunPreLoadScript do
					format "PreLoadScript=%\n" (FileNameFromPath SMTDSettings.PreLoadScriptFile) to:JobInfoFile
				if SMTDSettings.RunPostLoadScript do
					format "PostLoadScript=%\n" (FileNameFromPath SMTDSettings.PostLoadScriptFile) to:JobInfoFile
				if SMTDSettings.RunPostFrameScript then
					format "PostFrameScript=%\n" (FileNameFromPath SMTDSettings.PostFrameScriptFile) to:JobInfoFile
				if SMTDSettings.RunPreFrameScript do
					format "PreFrameScript=%\n" (FileNameFromPath SMTDSettings.PreFrameScriptFile) to:JobInfoFile
				
				format "MaxVersionToForce=%\n" SMTDSettings.MaxVersionToForce to:JobInfoFile
				format "MaxVersionToForce0=none\n" to:JobInfoFile
				format "MaxVersionToForce1=32bit\n" to:JobInfoFile
				format "MaxVersionToForce2=64bit\n" to:JobInfoFile
				
				if SMTDSettings.UseJpegOutput do
				(
					format "UseJpegOutput=1\n" to:JobInfoFile
					format "JpegOutputPath=%\n" SMTDSettings.JpegOutputPath to:JobInfoFile
				)
				
				if SMTDSettings.UseAltPluginIni and SMTDSettings.AltPluginIni != "" and SMTDSettings.AltPluginIni != "[Default]" do
					format "OverridePluginIni=%.ini\n" SMTDSettings.AltPluginIni to:JobInfoFile
				
				if SMTDSettings.enableFailOnBlackFrames then
					format "FailOnBlackFrames=1\n" to:JobInfoFile
				else
					format "FailOnBlackFrames=0\n" to:JobInfoFile
				format "BlackPixelPercentage=%\n" SMTDSettings.blackPixelPercentage to:JobInfoFile
				format "BlackPixelThreshold=%\n" SMTDSettings.blackPixelThreshold to:JobInfoFile
				if SMTDSettings.BlackFramesCheckRenderElements then
					format "BlackFramesCheckRenderElements=1\n" to:JobInfoFile
				else
					format "BlackFramesCheckRenderElements=0\n" to:JobInfoFile
				
				if SMTDSettings.GammaCorrection then
					format "GammaCorrection=1\n" to:JobInfoFile
				else
					format "GammaCorrection=0\n" to:JobInfoFile
				format "GammaInput=%\n" SMTDSettings.GammaInput to:JobInfoFile
				format "GammaOutput=%\n" SMTDSettings.GammaOutput to:JobInfoFile
				
				-- if output file is empty, check if rendering with vray and saving a raw image, and ignore render elements if so
				--if (SMTDFunctions.getRendererIdString() == "krakatoa") or (SMTDFunctions.getRendererIdString() == "vray" and renderers.current.output_on and renderers.current.output_rawFileName != undefined and renderers.current.output_rawFileName != "" ) then
				--if (SMTDFunctions.getRendererIdString() == "vray" and renderers.current.output_on and ((renderers.current.output_rawFileName != undefined and renderers.current.output_rawFileName != "") or (renderers.current.output_splitfilename != undefined and renderers.current.output_splitfilename != "")) ) then
				--	format "IgnoreRenderElements=1\n" to:JobInfoFile
				--else
				--	format "IgnoreRenderElements=%\n" (if SMTDSettings.IgnoreRenderElements then 1 else 0) to:JobInfoFile
				format "IgnoreRenderElements=%\n" (if SMTDSettings.IgnoreRenderElements then 1 else 0) to:JobInfoFile

				format "RenderElementsIncludeNameInPath=%\n" SMTDSettings.RenderElementsIncludeNameInPath to:JobInfoFile
				format "RenderElementsIncludeTypeInPath=%\n" SMTDSettings.RenderElementsIncludeTypeInPath to:JobInfoFile
				
				-- If this is 3dsmax 2011 or later, check to see if we're rendering to the new exr format
				if ((maxVersion())[1]/1000 as integer) >= 13 do
				(
					if rendSaveFile and rendOutputFilename != undefined do
					(
						rend_type = getFileNameType rendOutputFilename
						is_exr = matchPattern rend_type pattern:".exr" ignoreCase:true
						is_fxr = matchPattern rend_type pattern:".fxr" ignoreCase:true
						
						-- If we are, we need to tell Deadline which render elements are to be embedded in the exr file so that it doesn't save them separately
						if (is_exr or is_fxr) and (fopenexr != undefined) do
						(
							elementIndex = 0
							if fopenexr.isAutoAddRenderElements() then
							(
								--The elements are being added automatically, so check the re manager.
								local reManager = maxOps.GetCurRenderElementMgr()
								if reManager != undefined do
								(
									if reManager.GetElementsActive() then 
									(
										local reCount = reManager.NumRenderElements()
										for i = 0 to reCount - 1 do
										(
											local theElement = reManager.GetRenderElement i
											if classof theElement != Missing_Render_Element_Plug_in AND theElement.enabled AND classof theElement != VRayOptionRE do
											(
												format "IgnoreRenderElementsByName%=%\n" elementIndex theElement.elementName to:JobInfoFile
												elementIndex += 1
											)
										)
									)
								)--end if reManager undefined
							)
							else
							(
								--The elements are manually specified, so check the layers in the exr itself
								for i = 0 to fopenexr.numLayers() do
								(
									if (fopenexr.getLayerType i) == 1 then
									(
										format "IgnoreRenderElementsByName%=%\n" elementIndex (fopenexr.getLayerName i) to:JobInfoFile
										elementIndex += 1
									)
								)
							)
						)
					)
				)
				
				local filenameToRender = ""
				renderOutput = rendOutputFilename
				if renderOutputOverride != "" do renderOutput = renderOutputOverride
				if rendSaveFile and renderOutput != undefined and renderOutput != "" do 
					filenameToRender = SMTDFunctions.GetFormattedOutputFilename renderOutput addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel
				if SMTD_DebugPrintsOn do format "RenderOutput=%\n" filenameToRender
				
				--local delimiter  = SMTDFunctions.getDelimiterToken()
				--local stereoCameraToken = if stereoCameraLabel == "" then "" else stereoCameraLabel+"_"
				
				format "RenderOutput=%\n" filenameToRender to:JobInfoFile
				format "SaveFile=%\n" rendSaveFile to:JobInfoFile

				if SMTDSettings.RegionRenderingMode != #none do
					format "RenderElementTiles=1\n" to:JobInfoFile
				
				-- If any render elements are specified, include them
				local includeRenderElementPaths = true
				if includeRenderElementPaths do
				(
					local reManager = maxOps.GetCurRenderElementMgr()
					local outputFilenameIndex = 0
					local theRenderer = SMTDFunctions.getRendererObject()
					local theRendererName = SMTDFunctions.getRendererIdString()

					if reManager != undefined do
					(
						if reManager.GetElementsActive() then 
						(
							local reCount = reManager.NumRenderElements()
							for i = 0 to reCount - 1 do
							(
								reObject = reManager.GetRenderElement i
								local elementName = reObject.elementName
								if classof reObject != Missing_Render_Element_Plug_in AND reObject.enabled AND classof reObject != VRayOptionRE then
								(
									reFilename = reManager.GetRenderElementFilename i
									
									if reFilename != undefined and reFilename != "" then
									(
										/*
										if SMTDSettings.StateSetsSubmit and SMTDSettings.StateSetRenameOutput do
										(
											if (theRendererName == "vray" OR theRendererName == "vrayrt") AND theRenderer.output_on AND theRenderer.output_splitgbuffer AND theRenderer.output_splitfilename != "" AND theRenderer.output_useram then
												if not matchPattern (getFilenameFile theRenderer.output_splitfilename) pattern:(SMTDSettings.StateSetName +"_*") do
													reFilename = getFileNamePath theRenderer.output_splitfilename + SMTDSettings.StateSetName +"_"+(getFilenameFile theRenderer.output_splitfilename) + (getFilenameType reFilename)
											else
												if not matchPattern (getFilenameFile reFilename) pattern:(SMTDSettings.StateSetName +"_*") do
													reFilename = getFileNamePath reFilename + SMTDSettings.StateSetName +"_"+(getFilenameFile reFilename) + (getFilenameType reFilename)

											try(SMTD_MainRollout.Ui_report (">State Set Rename Output Requested. New Render Element Output File is:"))catch()
											try(SMTD_MainRollout.Ui_report ("  ["+reFilename+"]"))catch()
										)	
										
										reFilename = getFilenamePath reFilename + stereoCameraToken + filenameFromPath reFilename
										
										if SMTDSettings.purifyFilenames do reFilename = SMTDFunctions.purifyFilename reFilename				
										if SMTDSettings.ForceLowerCaseFilenames do reFilename = toLower reFilename
										if SMTDSettings.purifyFilenames or SMTDSettings.ForceLowerCaseFilenames do reManager.SetRenderElementFilename i reFilename
										if SMTDSettings.SubmitSceneMode == #networkremap do reFilename = ::SMTD_RemapLocalToNetworkPath reFilename

										--local delimiter = SMTDSettings.Delimiter
										--if SMTDSettings.RemovePadding AND (findItem #(#none, #maxRegion, #singleFrameTiles, #singleFrameMultiRegion) SMTDSettings.RegionRenderingMode > 0) do delimiter = ""
										*/
										--TILE/REGION RENDERING ENABLED
										local outputFilename = ""

										if tileString != "" then
										(
											if theRendererName == "vray" then --V-Ray RT does not support tile/region rendering
											(
												--Override reFilename if renderer is VRay, VFB is enabled, "Separate render channels" is enabled and splitfilename != ""
												if theRenderer.output_on and theRenderer.output_splitgbuffer and theRenderer.output_splitfilename != "" and theRenderer.output_useram then
												(
													if classof reObject != VRayAlpha then
													(
														local reArtifactSuffixes = SMTDFunctions.RenderElementArtifactSuffixes(reObject)
														if (reArtifactSuffixes.count > 0) then
														(
															local replaceHashes = false
															try( replaceHashes = renderers.current.output_expandFrameNumber )catch()
															-- HACK: Because the VRayDenoiser is a special-case that
															-- can generate multiple render elements, we manually add
															-- any outputs beyond one since the enclosing loop is
															-- structured for 1:1 mapping between a render element
															-- and an output suffix
															for j = 2 to reArtifactSuffixes.count do
															(
																outputFilename = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:(reArtifactSuffixes[j]+tileString) stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
																format "RenderElementOutputFilename%=%\n" outputFilenameIndex outputFilename to:JobInfoFile
																outputFilenameIndex = outputFilenameIndex + 1
															)
															outputFilename = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:(reArtifactSuffixes[1]+tileString) stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
														)
														else if classof reObject != VRayAlpha then
														(
															local replaceHashes = false
															try( replaceHashes = renderers.current.output_expandFrameNumber )catch()
															outputFilename = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:(elementName+tileString) stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
														)
													)
												)
												else
													outputFilename = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
											)
											else
												outputFilename = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
										)
										--NOT TILE/REGION RENDERING
										else
										(
											if (theRendererName == "vray" OR theRendererName == "vrayrt") then
											(
												--Override reFilename if renderer is VRay, VFB is enabled, "Separate render channels" is enabled and splitfilename != ""
												if theRenderer.output_on and theRenderer.output_splitgbuffer and theRenderer.output_splitfilename != "" and theRenderer.output_useram then
												(
													if classof reObject != VRayAlpha do
													(
														local replaceHashes = false
														try( replaceHashes = renderers.current.output_expandFrameNumber )catch()
														outputFilename = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:(SMTDSettings.Delimiter+elementName) stereoCameraToken:stereoCameraLabel addFrameDelimiter:true replaceHashesWithFramePadding:replaceHashes
													)
												)
												else
													outputFilename = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:"" stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
											)
											else
												outputFilename = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:"" stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
										)
										if SMTD_DebugPrintsOn do format "outputFileName=%\n" outputFileName
										if outputFileName != "" do
										(
											format "RenderElementOutputFilename%=%\n" outputFilenameIndex outputFilename to:JobInfoFile
											outputFilenameIndex = outputFilenameIndex + 1
										)
									)
									else
									(
										try(SMTD_MainRollout.Ui_report ("!!Skipping as Standard 3dsMax Render Element Output Filename is undefined."))catch()
										SMTDSettings.nonFatalErrorsCount+=1
									)
								)--end if enabled	
							)--end i loop
						)--end if REs active
					)--end if reManager undefined
				)

				-- If the V-Ray frame buffer is on, then disable the max frame buffer
				local theRenderer = SMTDFunctions.getRendererObject()
				local theRendererName = SMTDFunctions.getRendererIdString()
				if (theRendererName == "vray" OR theRendererName == "vrayrt") AND theRenderer.output_on then
					format "ShowFrameBuffer=0\n" to:JobInfoFile
				else
					format "ShowFrameBuffer=%\n" SMTDSettings.ShowFrameBuffer to:JobInfoFile

				-- If V-Ray, V-Ray RT, Corona or Redshift renderer
				if theRendererName == "vray" OR theRendererName == "vrayrt" OR theRendererName == "corona" OR theRendererName == "redshift" do
					format "ShowRendererFrameBufferOverride=%\n" SMTDSettings.ShowRendererFrameBufferOverride to:JobInfoFile
					format "ShowRendererFrameBuffer=%\n" SMTDSettings.ShowRendererFrameBuffer to:JobInfoFile

				format "OverrideBitmapPager=%\n" SMTDSettings.OverrideBitmapPager to:JobInfoFile
				format "BitmapPager=%\n" SMTDSettings.BitmapPager to:JobInfoFile

				--if (SMTDSettings.TilesRendering AND SMTDSettings.TilesSubmissionMode == #deadline )or SMTDSettings.SubmitAsMXSJob or SMTDSettings.UseBatchRender do
				if SMTDSettings.SubmitAsMXSJob or (SMTDSettings.UseBatchRender AND SMTDSettings.BatchRenderMode == 2) do
					format "MAXScriptJob=1\n" to:JobInfoFile
				
				--REGION RENDERING SETTINGS EXPORT STARTS HERE:
				local regionMode = SMTDSettings.RegionRenderingMode --SMTDFunctions.GetTileOrRegionMode()
				local tilesRendering = findItem #(#singleFrameTiles) regionMode > 0
				local multiRegionRendering = findItem #(#singleFrameMultiRegion, #animationMultiRegion) regionMode > 0
				local singleFrameRendering = findItem #(#singleFrameTiles, #singleFrameMultiRegion) regionMode > 0
				local AssemblyMode = #draft --default to draft, unless...
				if (regionMode == #singleFrameTiles AND NOT SMTDSettings.SingleTileJobDependent) do AssemblyMode = #none
				
				if regionMode != #none do 
					try(SMTD_MainRollout.Ui_report (">Region Mode: " + regionMode as string+" | Assembler Mode: "+ AssemblyMode as string) LogFileOnly:true)catch()
				
				local renderingModesEnums = #(#none, #singleFrameMultiRegion, #animationMultiRegion, #singleFrameTiles, #maxRegion)

				--if #maxRegion or #none
				if (findItem renderingModesEnums regionMode > 0) AND (regionMode == #maxRegion OR regionMode == #none) do
				--if (findItem renderingModesEnums regionMode > 0) do
				(
					local theRenderer = SMTDFunctions.getRendererObject()
					local theRendererName = SMTDFunctions.getRendererIdString()
					if (theRendererName == "vray" OR theRendererName == "vrayrt") AND theRenderer.output_on do
					(
						--SPLIT RENDER CHANNELS
						if (theRenderer.output_splitgbuffer AND theRenderer.output_splitfilename != undefined AND theRenderer.output_splitfilename != "" AND theRenderer.output_useram) do
						(
							SMTDSettings.SplitBufferFile = "SplitBufferFile="+(theRenderer.output_splitgbuffer as string)+"\n"
							local theFile = SMTDFunctions.GetFormattedOutputFilename theRenderer.output_splitfilename addFramePadding:false regionString:"" stereoCameraToken:stereoCameraLabel addFrameDelimiter:false
							if SMTD_DebugPrintsOn do format "SplitBufferFilename=%\n" theFile
							SMTDSettings.SplitBufferFilename = "SplitBufferFilename0="+theFile+"\n"
							format "%" SMTDSettings.SplitBufferFile to:JobInfoFile
							format "%" SMTDSettings.SplitBufferFilename to:JobInfoFile
							--theRenderer.output_rawFileName = theFile
						)

						local delimiter = SMTDSettings.Delimiter
						if SMTDSettings.RemovePadding do delimiter = ""

						--RAW FILE
						if (theRenderer.output_saveRawFile AND theRenderer.output_rawFileName != undefined AND theRenderer.output_rawFileName != "") then
						(
							SMTDSettings.RawBufferFile = "RawBufferFile="+(theRenderer.output_saveRawFile as string)+"\n"
							local addFrameDelimiter = false
							if (isProperty theRenderer #fileName_addDot) and (getProperty theRenderer #fileName_addDot) do addFrameDelimiter = true
							local theFile = SMTDFunctions.GetFormattedOutputFilename theRenderer.output_rawFileName addFramePadding:false regionString:"" stereoCameraToken:stereoCameraLabel addFrameDelimiter:addFrameDelimiter
							if SMTD_DebugPrintsOn do format "RawBufferFile=%\n" theFile
							SMTDSettings.RawBufferFilename = "RawBufferFilename0="+theFile+"\n"
							format "%" SMTDSettings.RawBufferFile to:JobInfoFile
							format "%" SMTDSettings.RawBufferFilename to:JobInfoFile
						)
					)--end if vray renderer
				)--end if #maxRegion or #none

				--if (findItem renderingModesEnums regionMode > 0) do
				if (findItem renderingModesEnums regionMode > 0) AND regionMode != #none do
				(
					format "RegionRendering=1\n" to:JobInfoFile
					if ( SMTDFunctions.getRendererIdString() == "vray" and renderers.current.output_on ) do
					(
						format "%" SMTDSettings.SplitBufferFile to:JobInfoFile
						format "%" SMTDSettings.SplitBufferFilename to:JobInfoFile
						format "%" SMTDSettings.RawBufferFile to:JobInfoFile
						format "%" SMTDSettings.RawBufferFilename to:JobInfoFile

						if renderers.current.output_splitgbuffer AND renderers.current.output_useram then
						(
							local splitChannelCount = 0
							local splitChannelNames = ""
							local splitChannelTypes = ""
							if renderers.current.output_splitRGB then
							(
								splitChannelNames += "SplitChannelNames"+(splitChannelCount as string)+"=RGB_color\n"
								splitChannelTypes += "SplitChannelTypes"+(splitChannelCount as string)+"=RGB_color\n"
								splitChannelCount += 1
							)
							if renderers.current.output_splitAlpha then
							(
								splitChannelNames += "SplitChannelNames"+(splitChannelCount as string)+"=Alpha\n"
								splitChannelTypes += "SplitChannelTypes"+(splitChannelCount as string)+"=Alpha\n"
								splitChannelCount += 1
							)
							
							if reManager.GetElementsActive() then
							(
								local reCount = reManager.NumRenderElements()
								for i = 0 to reCount - 1 do
								(
									local reObject = reManager.GetRenderElement i
									if classof reObject != Missing_Render_Element_Plug_in AND reObject.enabled AND classof reObject != VRayOptionRE AND classof reObject != VRayAlpha then
									(									
										local reArtifactSuffixes = SMTDFunctions.RenderElementArtifactSuffixes(reObject)
										for reArtifactSuffix in reArtifactSuffixes do
										(
											splitChannelNames += "SplitChannelNames"+(splitChannelCount as string)+"="+reArtifactSuffix+"\n"
											local reType = (classof reObject) as string
											splitChannelTypes += "SplitChannelTypes"+(splitChannelCount as string)+"="+reType+"\n"
											splitChannelCount += 1
										)
									)
								)
							)
							format "%" splitChannelNames to:JobInfoFile
							format "%" splitChannelTypes to:JobInfoFile
						)--end if splitChannels enabled
					)--end if VRay is renderer & VFB enabled
					
					if regionMode == #maxRegion then 
					(
						local useMaxRegion = SMTDSettings.RegionUseMaxValues
						if not (isKindOf SMTDSettings.RegionLeft Number) do useMaxRegion = true --ensure the value in the region is a number (it could be an array left over from MF/MR)
						if useMaxRegion then
						(
							if viewport.activeViewport > 0 then 
							(
								local theRect;
								if SMTDSettings.RegionType > 2 then
									theRect = viewport.getBlowupRect (viewport.activeViewport)
								else
									theRect = viewport.getRegionRect (viewport.activeViewport)
								tempLeft = theRect.x
								tempTop = theRect.y
								tempRight = theRect.x + theRect.w
								tempBottom = theRect.y + theRect.h
							)
							else
							(
								tempLeft = 0
								tempTop = 0
								renderDimensions = SMTDFunctions.getRenderDimensions() --#(renderWidth,renderHeight,renderPixelAspect)
								tempRight = renderDimensions[1]
								tempBottom = renderDimensions[2]
							)			
							format "RegionLeft=%\n" tempLeft to:JobInfoFile
							format "RegionTop=%\n" tempTop to:JobInfoFile
							format "RegionRight=%\n" tempRight to:JobInfoFile
							format "RegionBottom=%\n" tempBottom to:JobInfoFile
						)
						else --this  is only for UI-less submissions where the SMTDSettings.RegionLeft etc. were set by a script. Normally, the Max region values and the SMTD values should match anyway
						(
							format "RegionLeft=%\n" (SMTDSettings.RegionLeft as integer) to:JobInfoFile
							format "RegionTop=%\n" (SMTDSettings.RegionTop as integer) to:JobInfoFile
							format "RegionRight=%\n" (SMTDSettings.RegionRight as integer) to:JobInfoFile
							format "RegionBottom=%\n" (SMTDSettings.RegionBottom as integer) to:JobInfoFile
						)
						format "RegionPadding=0\n" to:JobInfoFile
						format "RegionType=%\n" #("NOCROP","CROP","BLOWUP")[SMTDSettings.RegionType] to:JobInfoFile
					)
					else
					(
						format "RegionPadding=%\n" SMTDSettings.TilesPadding to:JobInfoFile
						if SMTDSettings.TileBlowupMode and tilesRendering  then --SMTDSettings.TilesRendering
							format "RegionType=BLOWUP\n" to:JobInfoFile
						else
							format "RegionType=CROP\n" to:JobInfoFile
					)

					if regionMode == #singleFrameMultiRegion or regionMode == #singleFrameTiles then
					(
						try(SMTD_MainRollout.Ui_report (">Single Frame Regions or Tiles...") LogFileOnly:true )catch()
						--format "RegionSingleJob=True\n" to:JobInfoFile
						--format "RegionSingleFrame=%\n" (currentTime.frame as integer) to:JobInfoFile
						format "%" SMTDSettings.SingleTileJobLeft to:JobInfoFile
						format "%" SMTDSettings.SingleTileJobTop to:JobInfoFile
						format "%" SMTDSettings.SingleTileJobRight to:JobInfoFile
						format "%" SMTDSettings.SingleTileJobBottom to:JobInfoFile
						format "%" SMTDSettings.SingleTileJobFilename to:JobInfoFile
						format "%" SMTDSettings.SingleTileJobReFilename to:JobInfoFile
					)
					else
						try(SMTD_MainRollout.Ui_report (">NOT Single Frame Regions or Tiles...") LogFileOnly:true)catch()
					
					if regionMode == #animationMultiRegion do
					(
						format "RegionAnimation=1\n" to:JobInfoFile
						with PrintAllElements on 
						(
							local txt1 = substring (SMTDSettings.RegionLeft as string) 3 -1
							txt1 = substring txt1 1 (txt1.count-1)
							local txt2 = substring (SMTDSettings.RegionTop as string) 3 -1
							txt2 = substring txt2 1 (txt2.count-1)
							local txt3 = substring (SMTDSettings.RegionRight as string) 3 -1
							txt3 = substring txt3 1 (txt3.count-1)
							local txt4 = substring (SMTDSettings.RegionBottom as string) 3 -1
							txt4 = substring txt4 1 (txt4.count-1)
						)
						format "RegionLeft=%\n" txt1  to:JobInfoFile
						format "RegionTop=%\n" txt2 to:JobInfoFile
						format "RegionRight=%\n" txt3 to:JobInfoFile
						format "RegionBottom=%\n" txt4 to:JobInfoFile							
					)
				)--end in some region mode
				
				renderDimensions = SMTDFunctions.getRenderDimensions() --#(renderWidth,renderHeight,renderPixelAspect)

				if regionMode != #none then
				(
					-- Only include the render width/height in blowup mode, because we don't want to allow people to change
					-- the resolution for normal tile jobs. However, if the job is tile/region/jigsaw, then include AssembledRenderWidth/Height
					-- for reference purposes only.
					if SMTDSettings.TileBlowupMode then
					(
						format "RenderWidth=%\n" ((floor (1.0*renderDimensions[1]/SMTDSettings.TilesInX)) as integer) to:JobInfoFile
						format "RenderHeight=%\n" ((floor (1.0*renderDimensions[2]/SMTDSettings.TilesInY)) as integer) to:JobInfoFile
						format "renderPixelAspect=%\n" renderDimensions[3] to:JobInfoFile
					)
					else
					(
						format "AssembledRenderWidth=%\n" renderDimensions[1] to:JobInfoFile
						format "AssembledRenderHeight=%\n" renderDimensions[2] to:JobInfoFile
					)
				)
				else
				(
					format "RenderWidth=%\n" renderDimensions[1] to:JobInfoFile
					format "RenderHeight=%\n" renderDimensions[2] to:JobInfoFile
					format "renderPixelAspect=%\n" renderDimensions[3] to:JobInfoFile
				)
				--REGION RENDERING SETTINGS EXPORT ENDS HERE
				
				--SCENE STATES
				/*
				format "SceneState=\n" to:JobInfoFile
				format "SceneState0=\n" to:JobInfoFile
				for i = 1 to sceneStateMgr.GetCount() do
					format "SceneState%=\n" i (sceneStateMgr.getSceneState i) to:JobInfoFile
				*/

				format "rendAtmosphere=%\n" rendAtmosphere to:JobInfoFile
				format "renderEffects=%\n" renderEffects to:JobInfoFile
				format "renderDisplacements=%\n" renderDisplacements to:JobInfoFile
				format "rendSimplifyAreaLights=%\n" rendSimplifyAreaLights to:JobInfoFile
				format "rendForce2Side=%\n" rendForce2Side to:JobInfoFile
				format "rendHidden=%\n" rendHidden to:JobInfoFile
				format "rendColorCheck=%\n" rendColorCheck to:JobInfoFile
				format "rendSuperBlack=%\n" rendSuperBlack to:JobInfoFile
				format "rendFieldRender=%\n" rendFieldRender to:JobInfoFile

				format "SkipRenderedFrames=%\n" skipRenderedFrames to:JobInfoFile

				format "backgroundColor=%\n" backgroundColor to:JobInfoFile
				format "useEnvironmentMap=%\n" useEnvironmentMap to:JobInfoFile
				format "ambientColor=%\n" ambientColor to:JobInfoFile
				format "lightTintColor=%\n" lightTintColor to:JobInfoFile
				format "lightLevel=%\n" lightLevel to:JobInfoFile

				--EXPORT ADVANCED RENDERING SETTINGS STARTS HERE
				local rendererID = SMTDFunctions.getRendererIdString()
				if rendererID == "scanline" AND SMTDSettings.ExportAdvancedRenderInfoScanline then
				(	
				
					for p in getPropNames renderers.current do
						try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()
				
					format "scanline_globalSamplerClassByName0=Max 2.5 Star\n"  to:JobInfoFile
					format "scanline_globalSamplerClassByName1=Hammersley\n"  to:JobInfoFile
					format "scanline_globalSamplerClassByName2=Adaptive Halton\n"  to:JobInfoFile
					format "scanline_globalSamplerClassByName3=Adaptive Uniform\n"  to:JobInfoFile
					
					format "scanline_antialiasFilterClassByName=%\n" (classof scanlineRender.antiAliasFilter) to:JobInfoFile
					format "scanline_antialiasFilterClassByName0=Area\n" to:JobInfoFile
					format "scanline_antialiasFilterClassByName1=Quadratic\n" to:JobInfoFile
					format "scanline_antialiasFilterClassByName2=cubic\n" to:JobInfoFile
					format "scanline_antialiasFilterClassByName3=Catmull_Rom\n" to:JobInfoFile
					format "scanline_antialiasFilterClassByName4=Blackman\n" to:JobInfoFile
					format "scanline_antialiasFilterClassByName5=Video\n" to:JobInfoFile
					format "scanline_antialiasFilterClassByName6=Plate_Match_MAX_R2\n" to:JobInfoFile
					format "scanline_antialiasFilterClassByName7=Cook_Variable\n" to:JobInfoFile
					format "scanline_antialiasFilterClassByName8=Soften\n" to:JobInfoFile
					format "scanline_antialiasFilterClassByName9=Mitchell_Netravali\n" to:JobInfoFile
					format "scanline_antialiasFilterClassByName10=Blendfilter\n" to:JobInfoFile
					
					local theVal = if classof scanlineRender.antiAliasFilter == blend then scanlineRender.antiAliasFilter.blend else 0.3
					format "scanline_antialiasFilterBlend=%\n"  theVal to:JobInfoFile

					if classof scanlineRender.antiAliasFilter == Mitchell_Netravali then 
					(
						theVal1=scanlineRender.antiAliasFilter.Blur 
						theVal2=scanlineRender.antiAliasFilter.Ringing
					)	
					else	
						theVal1 = theVal2 = 0.3333
					format "scanline_antialiasFilterBlur=%\n"  theVal1 to:JobInfoFile	
					format "scanline_antialiasFilterRinging=%\n"  theVal2 to:JobInfoFile	
				)
				
				if rendererID == "brmax" AND SMTDSettings.ExportAdvancedRenderInfoBrazil2 then
				(
					local brazilRenderer = ::sfs.b2_lib.getActiveB2() --Force global scope to access SplutterFish Script libraries!
					
					local blockNames = #("System_Options_Parameter_Block_Holder","Sampling_Parameter_Block_Holder","Motion_Blur_Parameter_Block_Holder","Ray_Server_Parameter_Block_Holder","Luma_Server_Parameter_Block_Holder","Render_Cache_Parameter_Block_Holder","Photon_Server_Parameter_Block_Holder","Render_Pass_Parameter_Block_Holder")
					for blockName in blockNames do
					(
						local block = brazilRenderer[blockName]
						if block != undefined then
						(
							local propNames = getPropNames block.object
							if propNames != undefined then
							(
								for p in propNames do
								(
									try(format "%_%=%\n" rendererID (p as string) (getProperty block.object p) to:JobInfoFile)catch()
								)
							)
						)
					)
					
					local block = brazilRenderer["System_Options_Parameter_Block_Holder"]
					if block != undefined then
					(
						local item_list = #("Hilbert","Top to Bottom","Left to Right","Center Out","Random")
						format "brmax_bucket_order_enums=%\n"  item_list[block.object.bucket_order+1] to:JobInfoFile
						for i = 0 to item_list.count-1 do 
							format "brmax_bucket_order_enums%=%\n" i item_list[i+1] to:JobInfoFile
						
						item_list = #("16","24","32","48","64")
						format "brmax_bucket_size_enums=%\n"  item_list[block.object.bucket_size+1] to:JobInfoFile
						for i = 0 to item_list.count-1 do 
							format "brmax_bucket_size_enums%=%\n" i item_list[i+1] to:JobInfoFile
						
						item_list = #("Disable","Automatic","Specify")
						format "brmax_rend_threading_mode_enums=%\n"  item_list[block.object.rend_threading_mode+1] to:JobInfoFile
						for i = 0 to item_list.count-1 do 
							format "brmax_rend_threading_mode_enums%=%\n" i item_list[i+1] to:JobInfoFile
					)
					
					block = brazilRenderer["Sampling_Parameter_Block_Holder"]
					if block != undefined then
					(
						local item_list = #("BrAreaFilter","BrMitNetFilter","BrCatmullRomFilter","BrCookVariableFilter","BrBlackmanFilter","BrVideoFilter","BrGaussianFilter")
						format "brmax_filter_name_enums=%\n"  block.object.filter_name to:JobInfoFile
						for i = 0 to item_list.count-1 do 
							format "brmax_filter_name_enums%=%\n" i item_list[i+1] to:JobInfoFile
					)
					
					block = brazilRenderer["Motion_Blur_Parameter_Block_Holder"]
					if block != undefined then
					(
						local item_list = #("Off","Image Motion Blur","3D Motion Blur")
						format "brmax_motion_blur_type_enums=%\n"  item_list[block.object.motion_blur_type+1] to:JobInfoFile
						for i = 0 to item_list.count-1 do 
							format "brmax_motion_blur_type_enums%=%\n" i item_list[i+1] to:JobInfoFile
						
						item_list = #("None","Basic")
						format "brmax_shutter_type_enums=%\n"  item_list[block.object.shutter_type+1] to:JobInfoFile
						for i = 0 to item_list.count-1 do 
							format "brmax_shutter_type_enums%=%\n" i item_list[i+1] to:JobInfoFile
					)
					
					block = brazilRenderer["Ray_Server_Parameter_Block_Holder"]
					if block != undefined then
					(
						local item_list = #("BrDefaultAccel","BrLDAccel","BrLDKDTreeAccelDesc")
						format "brmax_ray_accel_name_enums=%\n"  block.object.ray_accel_name to:JobInfoFile
						for i = 0 to item_list.count-1 do 
							format "brmax_ray_accel_name_enums%=%\n" i item_list[i+1] to:JobInfoFile
					)
					
					block = brazilRenderer["Luma_Server_Parameter_Block_Holder"]
					if block != undefined then
					(
						local item_list = #("No Enhancement","Auto-Occlusion","Retrace")
						format "brmax_rendercache_detail_mode_enums=%\n"  item_list[block.object.rendercache_detail_mode+1] to:JobInfoFile
						for i = 0 to item_list.count-1 do 
							format "brmax_rendercache_detail_mode_enums%=%\n" i item_list[i+1] to:JobInfoFile
					)
				)
				
				--KRAKATOA EXPORT PROPERTIES
				if rendererID == "krakatoa" AND SMTDSettings.ExportAdvancedRenderInfoKrakatoa then
				(
					--Krakatoa - All Versions
					try(format "%_Version=%\n" rendererID FranticParticles.version to:JobInfoFile)catch()
					--Krakatoa 1.0.x and 1.1.x versions:
					if execute (substring FranticParticles.version 1 3) < 1.5 then
					(
						theArray = #("Volumetric Density","Additive Density","Constant Alpha")
						try(format "%_%=%\n" rendererID "Density_DensityMethod" (FranticParticles.GetProperty "Density:DensityMethod") to:JobInfoFile)catch()
						for i = 0 to theArray.count-1 do
							format "%_%%=%\n" rendererID "Density_DensityMethod" i theArray[i+1] to:JobInfoFile
						
						theArray = #("No Scaling", "Material Opacity")
						try(format "%_%=%\n" rendererID "DensityScalingSource" (FranticParticles.GetProperty "DensityScalingSource") to:JobInfoFile)catch()
						for i = 0 to theArray.count-1 do
							format "%_%%=%\n" rendererID "DensityScalingSource" i theArray[i+1] to:JobInfoFile
						
						theArray = #("Volumetric Density","Additive Density","Constant Alpha")
						try(format "%_%=%\n" rendererID "Lighting_Density_DensityMethod" (FranticParticles.GetProperty "Lighting:Density:DensityMethod") to:JobInfoFile)catch()
						for i = 0 to theArray.count-1 do
							format "%_%%=%\n" rendererID "Lighting_Density_DensityMethod" i theArray[i+1] to:JobInfoFile
						
						try(format "%_%=%\n" rendererID "UseGlobalColorOverride" (FranticParticles.GetProperty "UseGlobalColorOverride") to:JobInfoFile)catch()

						theArray = #("Choose Color", "Medit1", "No Material","Blended Z Depth","Blended Camera Distance")
						try(format "%_%=%\n" rendererID "ParticleColorSource"  (FranticParticles.GetProperty "ParticleColorSource") to:JobInfoFile)catch()
						for i = 0 to theArray.count-1 do
							format "%_%%=%\n" rendererID "ParticleColorSource" i theArray[i+1] to:JobInfoFile

						try(format "%_%=%\n" rendererID "ChosenColor" (FranticParticles.GetProperty "ChosenColor") to:JobInfoFile)catch()
						
						try(format "%_%=%\n" rendererID "UseLighting" (FranticParticles.GetProperty "UseLighting") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "Lighting_Specular_Enabled" (FranticParticles.GetProperty "Lighting:Specular:Enabled") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "Lighting_Specular_Glossiness" (FranticParticles.GetProperty "Lighting:Specular:Glossiness") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "Lighting_Specular_Level" (FranticParticles.GetProperty "Lighting:Specular:Level") to:JobInfoFile)catch()
						
						try(format "%_%=%\n" rendererID "RenderParticleFlowGeometry" (FranticParticles.GetProperty "RenderParticleFlowGeometry") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderParticleFlowBBox" (FranticParticles.GetProperty "RenderParticleFlowBBox") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderParticleFlowPhantom" (FranticParticles.GetProperty "RenderParticleFlowPhantom") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderParticleObjectExt" (FranticParticles.GetProperty "RenderParticleObjectExt") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "RenderMaxParticles" (FranticParticles.GetProperty "RenderMaxParticles") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderThinkingParticles" (FranticParticles.GetProperty "RenderThinkingParticles") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderGeometryVertices" (FranticParticles.GetProperty "RenderGeometryVertices") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderKrakatoaLoaders" (FranticParticles.GetProperty "RenderKrakatoaLoaders") to:JobInfoFile)catch()
					)
					else --Krakatoa 1.5.x+
					(
						try(format "%_%=%\n" rendererID "IgnoreSceneLights" (FranticParticles.GetProperty "IgnoreSceneLights") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "UseEnvironmentReflections" (FranticParticles.GetProperty "UseEnvironmentReflections") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "UseFilterColor" (FranticParticles.GetProperty "UseFilterColor") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "UseEmissionColor" (FranticParticles.GetProperty "UseEmissionColor") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "AdditiveMode" (FranticParticles.GetProperty "AdditiveMode") to:JobInfoFile)catch()
						
						try(format "%_%=%\n" rendererID "ColorOverride_Enabled" (FranticParticles.GetProperty "ColorOverride:Enabled") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "ColorOverride_Color" (FranticParticles.GetProperty "ColorOverride:Color") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "ColorOverride_BlendAmount" (FranticParticles.GetProperty "ColorOverride:BlendAmount") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "AbsorptionOverride_Enabled" (FranticParticles.GetProperty "AbsorptionOverride:Enabled") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "AbsorptionOverride_Color" (FranticParticles.GetProperty "AbsorptionOverride:Color") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "AbsorptionOverride_BlendAmount" (FranticParticles.GetProperty "AbsorptionOverride:BlendAmount") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "EmissionOverride_Enabled" (FranticParticles.GetProperty "EmissionOverride:Enabled") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "EmissionOverride_Color" (FranticParticles.GetProperty "EmissionOverride:Color") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "EmissionOverride_BlendAmount" (FranticParticles.GetProperty "EmissionOverride:BlendAmount") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "DensityOverride_Enabled" (FranticParticles.GetProperty "DensityOverride:Enabled") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "DensityOverride_Color" (FranticParticles.GetProperty "DensityOverride:Color") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "DensityOverride_BlendAmount" (FranticParticles.GetProperty "DensityOverride:BlendAmount") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "VoxelSize" (FranticParticles.GetProperty "VoxelSize") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "VoxelFilterRadius" (FranticParticles.GetProperty "VoxelFilterRadius") to:JobInfoFile)catch()
						
						try(format "%_%=%\n" rendererID "PhaseEccentricity" (FranticParticles.GetProperty "PhaseEccentricity") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "IgnoreMissingParticles" (FranticParticles.GetProperty "IgnoreMissingParticles") to:JobInfoFile)catch()

						theArray = #("Particle Rendering","Voxel Rendering")
						try(format "%_%=%\n" rendererID "RenderingMethod" (FranticParticles.GetProperty "RenderingMethod") to:JobInfoFile)catch()
						for i = 0 to theArray.count-1 do
							format "%_%%=%\n" rendererID "RenderingMethod" i theArray[i+1] to:JobInfoFile

						theArray = #("Isotropic","Phong Surface","Henyey-Greenstein","Schlick","Kajiya-Kay Hair") 
						try(format "%_%=%\n" rendererID "PhaseFunction" (FranticParticles.GetProperty "PhaseFunction") to:JobInfoFile)catch()
						for i = 0 to theArray.count-1 do
							format "%_%%=%\n" rendererID "PhaseFunction" i theArray[i+1] to:JobInfoFile
						
						try(format "%_%=%\n" rendererID "RenderParticleFlowGeometry" (FranticParticles.GetProperty "RenderParticleFlowGeometry") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderParticleFlowBBox" (FranticParticles.GetProperty "RenderParticleFlowBBox") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderParticleFlowPhantom" (FranticParticles.GetProperty "RenderParticleFlowPhantom") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "RenderFumeFX" (FranticParticles.GetProperty "RenderFumeFX") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderMaxParticles" (FranticParticles.GetProperty "RenderMaxParticles") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderThinkingParticles" (FranticParticles.GetProperty "RenderThinkingParticles") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "RenderGeometryVertices" (FranticParticles.GetProperty "RenderGeometryVertices") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderKrakatoaLoaders" (FranticParticles.GetProperty "RenderKrakatoaLoaders") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "RenderGeometryVolumes" (FranticParticles.GetProperty "RenderGeometryVolumes") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "GlobalParticlePercentage" (FranticParticles.GetProperty "GlobalParticlePercentage") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "Lighting_Specular_SpecularPower" (FranticParticles.GetProperty "Lighting:Specular:SpecularPower") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "Lighting_Specular_Level" (FranticParticles.GetProperty "Lighting:Specular:Level") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "Channel_Allocate_SpecularPower" (FranticParticles.GetProperty "Channel:Allocate:SpecularPower") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "Channel_Allocate_SpecularLevel" (FranticParticles.GetProperty "Channel:Allocate:SpecularLevel") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "Channel_Allocate_PhaseEccentricity" (FranticParticles.GetProperty "Channel:Allocate:PhaseEccentricity") to:JobInfoFile)catch()

						try(format "%_%=%\n" rendererID "Matte_RayDivisions" (FranticParticles.GetProperty "Matte:RayDivisions") to:JobInfoFile)catch()
						try(format "%_%=%\n" rendererID "Matte_SaveMultipleLayers" (FranticParticles.GetProperty "Matte:SaveMultipleLayers") to:JobInfoFile)catch()
					)
					
				
					try(format "%_%=%\n" rendererID "Density_LinkLightingAndRenderingDensity" (FranticParticles.GetProperty "Density:LinkLightingAndRenderingDensity") to:JobInfoFile)catch()
					try(format "%_%=%\n" rendererID "Density_DensityPerParticle" (FranticParticles.GetProperty "Density:DensityPerParticle") to:JobInfoFile)catch()
					try(format "%_%=%\n" rendererID "Density_DensityExponent" (FranticParticles.GetProperty "Density:DensityExponent") to:JobInfoFile)catch()

					try(format "%_%=%\n" rendererID "Lighting_Density_DensityPerParticle" (FranticParticles.GetProperty "Lighting:Density:DensityPerParticle") to:JobInfoFile)catch()
					try(format "%_%=%\n" rendererID "Lighting_Density_DensityExponent" (FranticParticles.GetProperty "Lighting:Density:DensityExponent") to:JobInfoFile)catch()

					try(format "%_%=%\n" rendererID "UseDepthMaps" (FranticParticles.GetProperty "UseDepthMaps") to:JobInfoFile)catch()
					
					theArray = #("Nearest Neighbor","Bilinear","Bicubic")
					try(format "%_%=%\n" rendererID "DrawPointFilter" (FranticParticles.GetProperty "DrawPointFilter") to:JobInfoFile)catch()
					for i = 0 to theArray.count-1 do
						format "%_%%=%\n" rendererID "DrawPointFilter" i theArray[i+1] to:JobInfoFile
					
					theArray = #("Nearest Neighbor","Bilinear","Bicubic")
					try(format "%_%=%\n" rendererID "AttenuationLookupFilter" (FranticParticles.GetProperty "AttenuationLookupFilter") to:JobInfoFile)catch()
					for i = 0 to theArray.count-1 do
						format "%_%%=%\n" rendererID "AttenuationLookupFilter" i theArray[i+1] to:JobInfoFile

					try(format "%_%=%\n" rendererID "EnableMotionBlur" (FranticParticles.GetProperty "EnableMotionBlur") to:JobInfoFile)catch()
					try(format "%_%=%\n" rendererID "EnableDepthOfField" (FranticParticles.GetProperty "EnableDepthOfField") to:JobInfoFile)catch()
					try(format "%_%=%\n" rendererID "EnableAttenuationMapSaving" (FranticParticles.GetProperty "EnableAttenuationMapSaving") to:JobInfoFile)catch()

					try(format "%_%=%\n" rendererID "MotionBlurSegments" (FranticParticles.GetProperty "MotionBlurSegments") to:JobInfoFile)catch()
					try(format "%_%=%\n" rendererID "JitteredMotionBlur" (FranticParticles.GetProperty "JitteredMotionBlur") to:JobInfoFile)catch()
					try(format "%_%=%\n" rendererID "DepthOfFieldSampleRate" (FranticParticles.GetProperty "DepthOfFieldSampleRate") to:JobInfoFile)catch()
					
					try(format "%_%=%\n" rendererID "BackgroundColor" (FranticParticles.GetProperty "BackgroundColor") to:JobInfoFile)catch()
					try(format "%_%=%\n" rendererID "UseEnvironmentColor" (FranticParticles.GetProperty "UseEnvironmentColor") to:JobInfoFile)catch()

					try(format "%_%=%\n" rendererID "PostDivideByAlpha" (FranticParticles.GetProperty "PostDivideByAlpha") to:JobInfoFile)catch()
					try(format "%_%=%\n" rendererID "ShutterAngleInDegrees" (FranticParticles.GetProperty "ShutterAngleInDegrees") to:JobInfoFile)catch()
					try(format "%_%=%\n" rendererID "ShutterBias" (FranticParticles.GetProperty "ShutterBias") to:JobInfoFile)catch()

					
					try(format "%_%=%\n" rendererID "Matte_UseMatteObjects" (FranticParticles.GetProperty "Matte:UseMatteObjects") to:JobInfoFile)catch()
				)--END KRAKATOA EXPORT PROPERTIES
				
				--MENTAL RAY RENDERER PROPERTIES
				if rendererID == "mentalray" AND SMTDSettings.ExportAdvancedRenderInfoMentalRay then
				(
					for p in getPropNames renderers.current do
						try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()

					local samples_list = #("1/64","1/16", "1/4", "1", "4", "16", "64", "256", "1024" )
					format "mentalray_MinimumSamples_enums=%\n" samples_list[renderers.current.MinimumSamples+4] to:JobInfoFile
					for i = 0 to samples_list.count-1 do 
						format "mentalray_MinimumSamples_enums%=%\n" i samples_list[i+1] to:JobInfoFile
						
					format "mentalray_MaximumSamples_enums=%\n" samples_list[renderers.current.MaximumSamples+4] to:JobInfoFile
					for i = 0 to samples_list.count-1 do 
						format "mentalray_MaximumSamples_enums%=%\n" i samples_list[i+1] to:JobInfoFile
					
					local filter_list = #("Box", "Gauss", "Triangle", "Mitchell", "Lanczos")
					format "mentalray_filter_enums=%\n" filter_list[renderers.current.filter+1] to:JobInfoFile
					for i = 0 to 4 do 
						format "mentalray_filter_enums%=%\n" i filter_list[i+1] to:JobInfoFile
						
					local order_list = #("Hilbert (best)", "Spiral", "Left to right", "Right to left", "Top-down", "Bottom-up")
					format "mentalray_TaskOrder_enums=%\n" order_list[renderers.current.TaskOrder+1] to:JobInfoFile
					for i = 0 to 5 do 
						format "mentalray_TaskOrder_enums%=%\n" i order_list[i+1] to:JobInfoFile				

					local order_list = for i = 1 to 15 collect ((i*i) as string)
					format "mentalray_RapidCollectRate_enums=%\n" order_list[renderers.current.RapidCollectRate] to:JobInfoFile
					for i = 0 to order_list.count-1 do 
						format "mentalray_RapidCollectRate_enums%=%\n" i order_list[i+1] to:JobInfoFile				
				)--END MENTAL RAY RENDERER PROPERTIES
				
				--FINAL RENDERER PROPERTIES
				if rendererID == "finalrender" AND SMTDSettings.ExportAdvancedRenderInfoFinalRender then
				(
					for p in getPropNames renderers.current do
						try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()
					
					local filter_list = #("Area","Blackman","Blend","Catmull-Rom","Cook Variable","Cubic","Plate Match/MAX R2","Mitchell-Netravali","Quadratic", "Sharp Quadratic", "Soften", "VRayBoxFilter","VRayLanczosFilter","VRaySincFilter","VRayTriangleFilter","Video")
					for i = 0 to filter_list.count-1 do 
						format "finalrender_aaFilterName%=%\n" i filter_list[i+1] to:JobInfoFile
					
					local size_list = #("16","32","64","128","256")
					format "finalrender_bucketSize_enums=%\n"  size_list[renderers.current.bucketSize+1] to:JobInfoFile
					for i = 0 to size_list.count-1 do 
						format "finalrender_bucketSize_enums%=%\n" i size_list[i+1] to:JobInfoFile
						
					local order_list = #("Top to Bottom","Left to Right","Spiral","Random","Hilbert")
					format "finalrender_bucketOrder_enums=%\n"  order_list[renderers.current.bucketOrder+1] to:JobInfoFile
					for i = 0 to order_list.count-1 do 
						format "finalrender_bucketOrder_enums%=%\n" i order_list[i+1] to:JobInfoFile
					
					local clear_list = #("Nothing","Clear Buffer","Clear Grid","Darken")
					format "finalrender_clearOptions_enums=%\n"  clear_list[renderers.current.clearOptions+1] to:JobInfoFile
					for i = 0 to clear_list.count-1 do 
						format "finalrender_clearOptions_enums%=%\n" i clear_list[i+1] to:JobInfoFile
					
					local storage_list = #("int (8 bpc)","int (16 bpc)","float (32 bpc)")
					format "finalrender_storage_enums=%\n"  storage_list[renderers.current.storage+1] to:JobInfoFile
					for i = 0 to storage_list.count-1 do 
						format "finalrender_storage_enums%=%\n" i storage_list[i+1] to:JobInfoFile
					
					local mode_list = #("Intensity","Intensity Centered","Vector Local Space","Vector Camera Space","Vector World Space")
					format "finalrender_mtdMode_enums=%\n"  mode_list[renderers.current.mtdMode+1] to:JobInfoFile
					for i = 0 to mode_list.count-1 do 
						format "finalrender_mtdMode_enums%=%\n" i mode_list[i+1] to:JobInfoFile
						
					local lens_list = #("Circular","Rhombic","Hexagon","Octagon","Triangle","Pentagon","Heptagon","Nanogon")
					format "finalrender_lensType_enums=%\n"  lens_list[renderers.current.lensType+1] to:JobInfoFile
					for i = 0 to lens_list.count-1 do 
						format "finalrender_lensType_enums%=%\n" i lens_list[i+1] to:JobInfoFile
					
					local type_list = #("Linear","Exponential","HSV Exponential","Gamma")
					format "finalrender_colorMapType_enums=%\n"  type_list[renderers.current.colorMapType+1] to:JobInfoFile
					for i = 0 to type_list.count-1 do 
						format "finalrender_colorMapType_enums%=%\n" i type_list[i+1] to:JobInfoFile
					
					local sampling_list = #("Absolute","Relative","Automatic")
					format "finalrender_geomSmpMode_enums=%\n"  sampling_list[renderers.current.geomSmpMode+1] to:JobInfoFile
					for i = 0 to sampling_list.count-1 do 
						format "finalrender_geomSmpMode_enums%=%\n" i sampling_list[i+1] to:JobInfoFile
					
					local skylight_list = #("Simple Sky","Physical Sky")
					format "finalrender_skyType_enums=%\n"  skylight_list[renderers.current.skyType+1] to:JobInfoFile
					for i = 0 to skylight_list.count-1 do 
						format "finalrender_skyType_enums%=%\n" i skylight_list[i+1] to:JobInfoFile
				)--END FINAL RENDERER PROPERTIES

				--VRAY RENDERER PROPERTIES
				if rendererID == "vray" AND SMTDSettings.ExportAdvancedRenderInfoVRay then
				(
					for p in getPropNames renderers.current do
					(
						--Ensure if rawFileName is declared that we add Delimiter to the end of the filename
						if p != undefined and p != "" and p == #output_rawFileName then
						(
							local tempFile = getProperty renderers.current #output_rawFileName
							if tempFile != undefined and tempFile != "" do --Now adding the stereo camera token and state set token if needed
							(
								local addFrameDelimiter = false
								if (isProperty renderers.current #fileName_addDot) and (getProperty renderers.current #fileName_addDot) do addFrameDelimiter = true
								
								local rawFile = SMTDFunctions.GetFormattedOutputFilename tempFile addFramePadding:false regionString:"" stereoCameraToken:stereoCameraLabel addFrameDelimiter:addFrameDelimiter
								try(format "%_%=%\n" rendererID (p as string) rawFile to:JobInfoFile)catch()
							)
						)
						else if p != undefined and p != "" and p == #output_splitfilename then
						(
							local tempFile = getProperty renderers.current #output_splitfilename
							if tempFile != undefined and tempFile != "" do --Now adding the stereo camera token and state set token if needed
							(
								local splitFile = SMTDFunctions.GetFormattedOutputFilename tempFile addFramePadding:false regionString:"" stereoCameraToken:stereoCameraLabel addFrameDelimiter:false
								try(format "%_%=%\n" rendererID (p as string) splitFile to:JobInfoFile)catch()
							)
						)
						else if p != undefined and p != #system_vrayLog_show do --Remove #system_vrayLog_show entry as it is handled explicitly further down
								try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()
					)--end p loop
						
					if (hasProperty renderers.current #gi_primary_type) do
					(
						local enum_list = #("Irradiance map","Photon map","Brute force","Light cache")
						format "vray_gi_primary_type_enums=%\n"  enum_list[renderers.current.gi_primary_type+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_gi_primary_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #gi_secondary_type) do
					(
						local enum_list = #("None","Photon map","Brute force","Light cache")
						format "vray_gi_secondary_type_enums=%\n"  enum_list[renderers.current.gi_secondary_type+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_gi_secondary_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #gi_irradmap_previewMode) do
					(
						local enum_list = #("Show new samples as brighter","Show new samples as green","Full preview")
						format "vray_gi_irradmap_previewMode_enums=%\n" enum_list[renderers.current.gi_irradmap_previewMode+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do
							format "vray_gi_irradmap_previewMode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #gi_irradmap_detail_scale) do
					(
						local enum_list = #("Screen","World")
						format "vray_gi_irradmap_detail_scale_enums=%\n" enum_list[renderers.current.gi_irradmap_detail_scale+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do
							format "vray_gi_irradmap_detail_scale_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #adv_irradmap_interpolationType) do
					(
						local enum_list = #("Weighted average (good/robust)","Least squares fit (good/smooth)", "Delone triangulation (good/exact)","Least squares w/ Voronoi weights (test)")
						format "vray_adv_irradmap_interpolationType_enums=%\n"  enum_list[renderers.current.adv_irradmap_interpolationType+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_adv_irradmap_interpolationType_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #adv_irradmap_lookupType) do
					(
						local enum_list = #("Quad-balanced (good)","Nearest (draft)", "Overlapping (very good/fast)","Density-based (best)")
						format "vray_adv_irradmap_lookupType_enums=%\n"  enum_list[renderers.current.adv_irradmap_lookupType+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_adv_irradmap_lookupType_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					--IRRADIANCE MAP MODE REQUIRES SPECIAL HANDLING BOTH HERE AND WHEN CUSTOMIZING!
					--ONLY VRAY ADVANCED VERSIONS 1.4, 1.5 & 2.x/3.x ARE CURRENTLY HANDLED EXPLICITLY.

					if (hasProperty renderers.current #adv_irradmap_mode) do
					(
						--SPECIAL CASE HANDLING FOR VRAY ADVANCED 1.4 - BUCKET MODE IS FIRST ENUM!
						if matchPattern ((classof renderers.current) as string) pattern:"*_1_4*" then
						(
							local enum_list = #("Bucket Mode","Single Frame", "Multiframe Incremental","From File","Add to Current Map","Incremental Add to Current Map")
							format "vray_adv_irradmap_mode_enums=%\n"  enum_list[renderers.current.adv_irradmap_mode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_adv_irradmap_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile		
						)
						--SPECIAL CASE HANDLING FOR VRAY ADVANCED 1.5 - BUCKET MODE IS LAST ENUM!
						else if matchPattern ((classof renderers.current) as string) pattern:"*_1_5*" then
						(
							local enum_list = #("Single Frame", "Multiframe Incremental","From File","Add to Current Map","Incremental Add to Current Map","Bucket Mode")
							format "vray_adv_irradmap_mode_enums=%\n"  enum_list[renderers.current.adv_irradmap_mode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_adv_irradmap_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)
						--SPECIAL CASE HANDLING FOR VRAY ADVANCED 2.x & 3.x
						else
						(
							local enum_list = #("Single frame", "Multiframe incremental","From file","Add to current map","Incremental add to current map","Bucket mode","Animation (prepass)","Animation (rendering)")
							format "vray_adv_irradmap_mode_enums=%\n"  enum_list[renderers.current.adv_irradmap_mode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_adv_irradmap_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)
					)

					if (hasProperty renderers.current #options_defaultLights) AND classof(renderers.current.options_defaultLights) == Integer then
					(
						local enum_list = #("Off","On", "Off with GI")
						format "vray_options_defaultLights_enums=%\n"  enum_list[renderers.current.options_defaultLights+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_options_defaultLights_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)
					if (hasProperty renderers.current #options_overrideMtl_excl_type) then
					(
						local enum_list = #("Include/Exclude list","Exclude layers","Exclude object IDs")
						format "vray_options_overrideMtl_excl_type_enums=%\n"  enum_list[renderers.current.options_overrideMtl_excl_type+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_options_overrideMtl_excl_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #lightcache_scale) do
					(
						--LC Scale
						local enum_list = #("Screen","World")
						format "vray_lightcache_scale_enums=%\n" enum_list[renderers.current.lightcache_scale+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do
							format "vray_lightcache_scale_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #lightcache_filter_type) do
					(
						--LC Filter
						local enum_list = #("None","Nearest","Fixed")
						format "vray_lightcache_filter_type_enums=%\n" enum_list[renderers.current.lightcache_filter_type+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do
							format "vray_lightcache_filter_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					/*
					--Disabled due to conflict which is explained in customise.ms
					if (hasProperty renderers.current #lightcache_mode) do
					(
						--LC Mode
						local enum_list = #("Single frame","Fly-through","From file","Progressive path tracing")
						format "vray_lightcache_mode_enums=%\n" enum_list[renderers.current.lightcache_mode+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do
							format "vray_lightcache_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)
					*/

					if (hasProperty renderers.current #system_region_sequence) do
					(
						--Sequence
						local enum_list = #("Top->Bottom","Left->Right", "Checker","Spiral","Triangulation","Hilbert curve")
						format "vray_system_region_sequence_enums=%\n"  enum_list[renderers.current.system_region_sequence+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_system_region_sequence_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #system_region_meaning) do
					(
						--Division Method
						local enum_list = #("Size","Count")
						format "vray_system_region_meaning_enums=%\n"  enum_list[renderers.current.system_region_meaning+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_system_region_meaning_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #system_previousRender) do
					(
						--Previous render
						local enum_list = #("Unchanged","Cross","Fields","Darken","Blue","Clear")
						format "vray_system_previousRender_enums=%\n"  enum_list[renderers.current.system_previousRender+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_system_previousRender_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #system_instancedObjects) do
					(
						--Default geometry
						local enum_list = #("Static","Dynamic","Auto")
						format "vray_system_instancedObjects_enums=%\n"  enum_list[renderers.current.system_instancedObjects+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_system_instancedObjects_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #system_frameStamp_justify) do
					(
						--Frame Stamp - Justify
						local enum_list = #("Left", "Center", "Right")
						format "vray_system_frameStamp_justify_enums=%\n"  enum_list[renderers.current.system_frameStamp_justify+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_system_frameStamp_justify_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					--SPECIAL CASE HANDLING FOR VRAY ADVANCED v1-v2.x / v3.x
					vrayVersionCheck = try(vrayVersion())catch(undefined) --2 element array returned in VRay v3.0+ only #(version, build)
					if vrayVersionCheck != undefined then
					(
						local vrayVer = vrayVersionCheck[1][1] as integer
						if vrayVer >= 3 do (
							if (hasProperty renderers.current #colorMapping_adaptationOnly) do
							(
								-- "colorMapping_adaptationOnly" - VRay v3+
								local enum_list = #("Color mapping and gamma","None (don't apply anything)", "Color mapping only (no gamma)")
								format "vray_colorMapping_adaptationOnly_enums=%\n" enum_list[renderers.current.colorMapping_adaptationOnly+1] to:JobInfoFile
								for i = 0 to enum_list.count-1 do
									format "vray_colorMapping_adaptationOnly_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)
							
							if (hasProperty renderers.current #imageSampler_type) do
							(
								-- "imageSampler_type" - VRay v3+
								local enum_list = #("Bucket","Adaptive", "Adaptive subdivision","Progressive")
								format "vray_imageSampler_type_enums=%\n"  enum_list[renderers.current.imageSampler_type+1] to:JobInfoFile
								for i = 0 to enum_list.count-1 do 
									format "vray_imageSampler_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)

							if (hasProperty renderers.current #imageSampler_type_new) do
							(
								-- "imageSampler_type_new" - VRay v3.40+
								local enum_list = #("Bucket","Progressive","Adaptive subdivision")
								format "vray_imageSampler_type_new_enums=%\n"  enum_list[renderers.current.imageSampler_type_new+1] to:JobInfoFile
								for i = 0 to enum_list.count-1 do 
									format "vray_imageSampler_type_new_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)

							if (hasProperty renderers.current #camera_type) do
							(
								-- "camera_type" - VRay v3+
								local enum_list = #("Default","Spherical","Cylindrical (point)","Cylindrical (ortho)","Box","Fish eye","Warped spherical (old-style)","Orthographic","Perspective","Spherical panorama")
								format "vray_camera_type_enums=%\n" enum_list[renderers.current.camera_type+1] to:JobInfoFile
								for i = 0 to enum_list.count-1 do
									format "vray_camera_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)
						)
					)
					else
					(	
						if matchPattern ((classof renderers.current) as string) pattern:"*_2_40_04*" then
						(
							if (hasProperty renderers.current #colorMapping_adaptationOnly) do
							(
								-- "colorMapping_adaptationOnly" - VRay v2.40.04 only
								local enum_list = #("Color mapping and gamma","None (don't apply anything)", "Color mapping only (no gamma)")
								format "vray_colorMapping_adaptationOnly_enums=%\n" enum_list[renderers.current.colorMapping_adaptationOnly+1] to:JobInfoFile
								for i = 0 to enum_list.count-1 do
									format "vray_colorMapping_adaptationOnly_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)
						)
						else
						(
							if (hasProperty renderers.current #colorMapping_adaptationOnly) do
							(
								-- "colorMapping_adaptationOnly" - VRay v1/2.40.03 or earlier only
								local enum_list = #("true","false") --Do NOT change the case of true/false! (keep it lowercase)
								format "vray_colorMapping_adaptationOnly_enums=%\n" renderers.current.colorMapping_adaptationOnly to:JobInfoFile
								for i = 0 to enum_list.count-1 do
									format "vray_colorMapping_adaptationOnly_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)
						)

						if (hasProperty renderers.current #imageSampler_type) do
						(
							-- "imageSampler_type" - VRay v1/2
							local enum_list = #("Fixed Rate","Adaptive QMC", "Adaptive Subdivision")
							format "vray_imageSampler_type_enums=%\n"  enum_list[renderers.current.imageSampler_type+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_imageSampler_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)
						
						if (hasProperty renderers.current #camera_type) do
						(
							-- "camera_type" - VRay v1/2
							local enum_list = #("Default","Spherical","Cylindrical (point)","Cylindrical (ortho)","Box","Fish eye","Warped spherical (old-style)")
							format "vray_camera_type_enums=%\n" enum_list[renderers.current.camera_type+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "vray_camera_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)
					)

					--Show Log Window
					if (hasProperty renderers.current #system_vrayLog_show) AND classof(renderers.current.system_vrayLog_show) == Integer then
					(
						local enum_list = #("Never","Always","Only on error/warning","Only on error")
						format "vray_system_vrayLog_show_enums=%\n"  enum_list[renderers.current.system_vrayLog_show+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vray_system_vrayLog_show_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)
					else
						try(format "vray_system_vrayLog_show=%\n" (getProperty renderers.current #system_vrayLog_show) to:JobInfoFile)catch()
				)--END VRAY RENDERER PROPERTIES

				--VRAY RT RENDERER PROPETIES
				if rendererID == "vrayrt" AND SMTDSettings.ExportAdvancedRenderInfoVRayRT then
				(
					--EXPORT ALL VRAY RENDERER SETTINGS (EMBEDDED IN RT RENDERER)
					if (isProperty renderers.current #V_Ray_settings) do
					(
						for p in getPropNames renderers.current.V_Ray_settings do
							--Ensure if rawFileName is declared that we add Delimiter to the end of the filename
							if p != undefined and p != "" and p == #output_rawFileName then
							(
								tempFile = getProperty renderers.current.V_Ray_settings #output_rawFileName
								if tempFile != undefined and tempFile != "" then
								(
									rawFile = (getFileNamePath tempFile) + (getFileNameFile tempFile)
									if (SMTDSettings.RemovePadding and rendTimeType == 1) then
									()
									else
									(
										if(isProperty renderers.current.V_Ray_settings #fileName_addDot) and (getProperty renderers.current.V_Ray_settings #fileName_addDot) do rawFile += SMTDSettings.Delimiter
									)
										
									rawFile += (getFileNameType tempFile)
									try(format "vray_%=%\n" (p as string) rawFile to:JobInfoFile)catch()
								)
							)
							else
								if p != undefined and p != #system_vrayLog_show do --Remove #system_vrayLog_show entry as it is handled explicitly further down
									try(format "vray_%=%\n" (p as string) (getProperty renderers.current.V_Ray_settings p) to:JobInfoFile)catch()

						if (hasProperty renderers.current.V_Ray_settings #gi_primary_type) do
						(
							local enum_list = #("Irradiance map","Photon map","Brute force","Light cache")
							format "vray_gi_primary_type_enums=%\n"  enum_list[renderers.current.V_Ray_settings.gi_primary_type+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_gi_primary_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #gi_secondary_type) do
						(
							local enum_list = #("None","Photon map","Brute force","Light cache")
							format "vray_gi_secondary_type_enums=%\n"  enum_list[renderers.current.V_Ray_settings.gi_secondary_type+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_gi_secondary_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #gi_irradmap_previewMode) do
						(
							local enum_list = #("Show new samples as brighter","Show new samples as green","Full preview")
							format "vray_gi_irradmap_previewMode_enums=%\n" enum_list[renderers.current.V_Ray_settings.gi_irradmap_previewMode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "vray_gi_irradmap_previewMode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #gi_irradmap_detail_scale) do
						(
							local enum_list = #("Screen","World")
							format "vray_gi_irradmap_detail_scale_enums=%\n" enum_list[renderers.current.V_Ray_settings.gi_irradmap_detail_scale+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "vray_gi_irradmap_detail_scale_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #adv_irradmap_interpolationType) do
						(
							local enum_list = #("Weighted average (good/robust)","Least squares fit (good/smooth)", "Delone triangulation (good/exact)","Least squares w/ Voronoi weights (test)")
							format "vray_adv_irradmap_interpolationType_enums=%\n"  enum_list[renderers.current.V_Ray_settings.adv_irradmap_interpolationType+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_adv_irradmap_interpolationType_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #adv_irradmap_lookupType) do
						(
							local enum_list = #("Quad-balanced (good)","Nearest (draft)", "Overlapping (very good/fast)","Density-based (best)")
							format "vray_adv_irradmap_lookupType_enums=%\n"  enum_list[renderers.current.V_Ray_settings.adv_irradmap_lookupType+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_adv_irradmap_lookupType_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						--IRRADIANCE MAP MODE REQUIRES SPECIAL HANDLING BOTH HERE AND WHEN CUSTOMIZING!
						--ONLY VRAY ADVANCED VERSIONS 1.4, 1.5 & 2.x/3.x ARE CURRENTLY HANDLED EXPLICITLY.

						if (hasProperty renderers.current.V_Ray_settings #adv_irradmap_mode) do
						(
							--SPECIAL CASE HANDLING FOR VRAY ADVANCED 1.4 - BUCKET MODE IS FIRST ENUM!
							if matchPattern ((classof renderers.current) as string) pattern:"*_1_4*" then
							(
								local enum_list = #("Bucket Mode","Single Frame", "Multiframe Incremental","From File","Add to Current Map","Incremental Add to Current Map")
								format "vray_adv_irradmap_mode_enums=%\n"  enum_list[renderers.current.V_Ray_settings.adv_irradmap_mode+1] to:JobInfoFile
								for i = 0 to enum_list.count-1 do 
									format "vray_adv_irradmap_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile		
							)
							--SPECIAL CASE HANDLING FOR VRAY ADVANCED 1.5 - BUCKET MODE IS LAST ENUM!
							else if matchPattern ((classof renderers.current) as string) pattern:"*_1_5*" then
							(
								local enum_list = #("Single Frame", "Multiframe Incremental","From File","Add to Current Map","Incremental Add to Current Map","Bucket Mode")
								format "vray_adv_irradmap_mode_enums=%\n"  enum_list[renderers.current.V_Ray_settings.adv_irradmap_mode+1] to:JobInfoFile
								for i = 0 to enum_list.count-1 do 
									format "vray_adv_irradmap_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)
							--SPECIAL CASE HANDLING FOR VRAY ADVANCED 2.x & 3.x
							else
							(
								local enum_list = #("Single frame", "Multiframe incremental","From file","Add to current map","Incremental add to current map","Bucket mode","Animation (prepass)","Animation (rendering)")
								format "vray_adv_irradmap_mode_enums=%\n"  enum_list[renderers.current.V_Ray_settings.adv_irradmap_mode+1] to:JobInfoFile
								for i = 0 to enum_list.count-1 do 
									format "vray_adv_irradmap_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)
						)

						if (hasProperty renderers.current.V_Ray_settings #options_defaultLights) AND classof(renderers.current.V_Ray_settings.options_defaultLights) == Integer then
						(
							local enum_list = #("Off","On", "Off with GI")
							format "vray_options_defaultLights_enums=%\n"  enum_list[renderers.current.V_Ray_settings.options_defaultLights+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_options_defaultLights_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #options_overrideMtl_excl_type) then
						(
							local enum_list = #("Include/Exclude list","Exclude layers","Exclude object IDs")
							format "vray_options_overrideMtl_excl_type_enums=%\n"  enum_list[renderers.current.V_Ray_settings.options_overrideMtl_excl_type+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_options_overrideMtl_excl_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #lightcache_scale) do
						(
							--LC Scale
							local enum_list = #("Screen","World")
							format "vray_lightcache_scale_enums=%\n" enum_list[renderers.current.V_Ray_settings.lightcache_scale+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "vray_lightcache_scale_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #lightcache_filter_type) do
						(
							--LC Filter
							local enum_list = #("None","Nearest","Fixed")
							format "vray_lightcache_filter_type_enums=%\n" enum_list[renderers.current.V_Ray_settings.lightcache_filter_type+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "vray_lightcache_filter_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						/*
						if (hasProperty renderers.current.V_Ray_settings #lightcache_mode) do
						(
							-- Disabled due to conflict which is explained in customise.ms - MO
							--LC Mode
							local enum_list = #("Single frame","Fly-through","From file","Progressive path tracing")
							format "vray_lightcache_mode_enums=%\n" enum_list[renderers.current.V_Ray_settings.lightcache_mode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "vray_lightcache_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)
						*/

						if (hasProperty renderers.current.V_Ray_settings #system_region_sequence) do
						(
							--Sequence
							local enum_list = #("Top->Bottom","Left->Right", "Checker","Spiral","Triangulation","Hilbert curve")
							format "vray_system_region_sequence_enums=%\n"  enum_list[renderers.current.V_Ray_settings.system_region_sequence+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_system_region_sequence_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #system_region_meaning) do
						(
							--Division Method
							local enum_list = #("Size","Count")
							format "vray_system_region_meaning_enums=%\n"  enum_list[renderers.current.V_Ray_settings.system_region_meaning+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_system_region_meaning_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #system_previousRender) do
						(
							--Previous render
							local enum_list = #("Unchanged","Cross","Fields","Darken","Blue","Clear")
							format "vray_system_previousRender_enums=%\n"  enum_list[renderers.current.V_Ray_settings.system_previousRender+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_system_previousRender_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #system_instancedObjects) do
						(
							--Default geometry
							local enum_list = #("Static","Dynamic","Auto")
							format "vray_system_instancedObjects_enums=%\n"  enum_list[renderers.current.V_Ray_settings.system_instancedObjects+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_system_instancedObjects_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						if (hasProperty renderers.current.V_Ray_settings #system_frameStamp_justify) do
						(
							--Frame Stamp - Justify
							local enum_list = #("Left", "Center", "Right")
							format "vray_system_frameStamp_justify_enums=%\n"  enum_list[renderers.current.V_Ray_settings.system_frameStamp_justify+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_system_frameStamp_justify_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)

						--SPECIAL CASE HANDLING FOR VRAY ADVANCED v1-v2.x / v3.x
						vrayVersionCheck = try(vrayVersion())catch(undefined) --2 element array returned in VRay v3.0+ only #(version, build)
						if vrayVersionCheck != undefined then
						(
							local vrayVer = vrayVersionCheck[1][1] as integer
							if vrayVer >= 3 do (
								if (hasProperty renderers.current.V_Ray_settings #colorMapping_adaptationOnly) do
								(
									-- "colorMapping_adaptationOnly" - VRay v3+
									local enum_list = #("Color mapping and gamma","None (don't apply anything)", "Color mapping only (no gamma)")
									format "vray_colorMapping_adaptationOnly_enums=%\n" enum_list[renderers.current.V_Ray_settings.colorMapping_adaptationOnly+1] to:JobInfoFile
									for i = 0 to enum_list.count-1 do
										format "vray_colorMapping_adaptationOnly_enums%=%\n" i enum_list[i+1] to:JobInfoFile
								)
								
								if (hasProperty renderers.current.V_Ray_settings #camera_type) do
								(
									-- "camera_type" - VRay v3+
									local enum_list = #("Default","Spherical","Cylindrical (point)","Cylindrical (ortho)","Box","Fish eye","Warped spherical (old-style)","Orthographic","Perspective","Spherical panorama")
									format "vray_camera_type_enums=%\n" enum_list[renderers.current.V_Ray_settings.camera_type+1] to:JobInfoFile
									for i = 0 to enum_list.count-1 do
										format "vray_camera_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
								)
							)
						)
						else
						(	
							if matchPattern ((classof renderers.current) as string) pattern:"*_2_40_04*" then
							(
								if (hasProperty renderers.current.V_Ray_settings #colorMapping_adaptationOnly) do
								(
									-- "colorMapping_adaptationOnly" - VRay v2.40.04 only
									local enum_list = #("Color mapping and gamma","None (don't apply anything)", "Color mapping only (no gamma)")
									format "vray_colorMapping_adaptationOnly_enums=%\n" enum_list[renderers.current.V_Ray_settings.colorMapping_adaptationOnly+1] to:JobInfoFile
									for i = 0 to enum_list.count-1 do
										format "vray_colorMapping_adaptationOnly_enums%=%\n" i enum_list[i+1] to:JobInfoFile
								)
							)
							else
							(
								if (hasProperty renderers.current.V_Ray_settings #colorMapping_adaptationOnly) do
								(
									-- "colorMapping_adaptationOnly" - VRay v1/2.40.03 or earlier only
									local enum_list = #("true","false") --Do NOT change the case of true/false! (keep it lowercase)
									format "vray_colorMapping_adaptationOnly_enums=%\n" renderers.current.V_Ray_settings.colorMapping_adaptationOnly to:JobInfoFile
									for i = 0 to enum_list.count-1 do
										format "vray_colorMapping_adaptationOnly_enums%=%\n" i enum_list[i+1] to:JobInfoFile
								)
							)
							
							if (hasProperty renderers.current.V_Ray_settings #camera_type) do
							(
								-- "camera_type" - VRay v1/2
								local enum_list = #("Default","Spherical","Cylindrical (point)","Cylindrical (ortho)","Box","Fish eye","Warped spherical (old-style)")
								format "vray_camera_type_enums=%\n" enum_list[renderers.current.V_Ray_settings.camera_type+1] to:JobInfoFile
								for i = 0 to enum_list.count-1 do
									format "vray_camera_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)
						)

						--Show Log Window
						if (hasProperty renderers.current.V_Ray_settings #system_vrayLog_show) AND classof(renderers.current.V_Ray_settings.system_vrayLog_show) == Integer then
						(
							local enum_list = #("Never","Always","Only on error/warning","Only on error")
							format "vray_system_vrayLog_show_enums=%\n"  enum_list[renderers.current.V_Ray_settings.system_vrayLog_show+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "vray_system_vrayLog_show_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)
						else
							try(format "vray_system_vrayLog_show=%\n" (getProperty renderers.current.V_Ray_settings #system_vrayLog_show) to:JobInfoFile)catch()
					)--end if not V_Ray_settings property exists

					--EXPORT ALL VRAY RT SPECIFIC SETTINGS
					for p in getPropNames renderers.current do
						try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()

					if (hasProperty renderers.current #engine_type) do
					(
						local enum_list = #("CPU","OpenCL","CUDA")
						format "vrayrt_engine_type_enums=%\n"  enum_list[renderers.current.engine_type+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vrayrt_engine_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #opencl_resizeTextures) do
					(
						local enum_list = #("Full-size textures","Resize all textures","On-demand mip-mapped textures")
						format "vrayrt_opencl_resizeTextures_enums=%\n"  enum_list[renderers.current.opencl_resizeTextures+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vrayrt_opencl_resizeTextures_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #opencl_textureFormat) do
					(
						local enum_list = #("Float","Half","8-bit")
						format "vrayrt_opencl_textureFormat_enums=%\n"  enum_list[renderers.current.opencl_textureFormat+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vrayrt_opencl_textureFormat_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #stereo_type) do
					(
						local enum_list = #("Disabled","Left/Right","Interlaced","Checkered","Anaglyph (Red, Cyan)","Anaglyph (Green, Magenta)","OpenGL stereo","Duplicate (mono)","OpenVR (mono)","OpenVR (stereo)","Oculus Rift (mono)","Oculus Rift (stereo)")
						format "vrayrt_stereo_type_enums=%\n"  enum_list[renderers.current.stereo_type+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "vrayrt_stereo_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)

					if (hasProperty renderers.current #output_layout) do
					(
						local enum_list = #("Side-by-side","Top-bottom")
						format "vrayrt_output_layout_enums=%\n"  enum_list[renderers.current.output_layout+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do
							format "vrayrt_output_layout_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)
				)
				--END VRAY RT RENDERER PROPETIES

				--MAXWELL RENDERER PROPERTIES
				if rendererID == "maxwell" AND SMTDSettings.ExportAdvancedRenderInfoMaxwell then
				(
					for p in getPropNames renderers.current do
					(
						try
						(
							p = (p as string)
							prop = (getProperty renderers.current p)
							
							-- Special case handling for string values - we need to strip off the leading #
							if p == "gsMXCLFlags" or p == "gsMXSOutputPath" or p == "gsMXIOutputPath" or p == "slApertureImagePath" or p == "slObscureImagePath" then
							(
								prop = (prop as string)
								if prop.count > 0 and prop[1] == "#" then
									prop = replace prop 1 1 ""
							)
							format "%_%=%\n" rendererID p prop to:JobInfoFile
						)
						catch ()
					)
					
					if renderers.current.version >= 20 then
					(
						/*
						local enum_list = #("Per Object","On", "Off")
						format "maxwell_gsMotionBlur_enums=%\n"  enum_list[renderers.current.gsMotionBlur+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "maxwell_gsMotionBlur_enums%=%\n" i enum_list[i+1] to:JobInfoFile						
						*/
						
						/*
						local enum_list = #("sRGB","Adobe RGB 98", "Apple RGB / SGI","PAL / SECAM","NTSC 1953","NTSC 1979","Wide Gamut RGB","ProPhoto RGB (ROMM)","ECI RGB","CIE 1931","Bruce RGB","ColorMatch RGB","Best RGB","Don RGB 4")
						format "maxwell_gsColorSpace_enums=%\n"  enum_list[renderers.current.gsColorSpace+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "maxwell_gsColorSpace_enums%=%\n" i enum_list[i+1] to:JobInfoFile						
						*/
						
						/*
						try
						(
							local enum_list = #("8","16", "32")
							format "maxwell_gsDepth_enums=%\n"  renderers.current.gsDepth to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "maxwell_gsDepth_enums%=%\n" i enum_list[i+1] to:JobInfoFile	
						)
						catch ()
						*/
						
						local enum_list = #("Diffuse+Reflection","Diffuse", "Reflection")
						format "maxwell_gsChannelRenderType_enums=%\n"  enum_list[renderers.current.gsChannelRenderType+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "maxwell_gsChannelRenderType_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					)
				)--END MAXWELL RENDERER PROPERTIES

				--CORONA RENDERER PROPERTIES
				if rendererID == "corona" AND SMTDSettings.ExportAdvancedRenderInfoCorona then
				(
					for p in getPropNames renderers.current do
						try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()

					--Check Corona version. Version's earlier than Alpha v6 are NOT supported and are no longer available from Corona Renderer website.
					coronaVersion = try(CoronaRenderer.CoronaFp.getCoronaVersion())catch(undefined)

					if coronaVersion == undefined or coronaVersion == "Alpha v7.2" then --assume Corona Alpha v6 FREE VERSION / NO UPDATES / NO SUPPORT or Corona Alpha v7.2
					(
						try(
						enum_list = #( "Bucket", "--", "Progressive", "Bidir/VCM" ) -- "--" handles irregular order of DDL items
						format "corona_renderer_enums=%\n"  enum_list[renderers.current.renderer+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "corona_renderer_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.renderer]"))catch())

						try(
						enum_list = #( "None", "Path Tracing" )
						format "corona_GI_solver_enums=%\n"  enum_list[renderers.current.GI_solver+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "corona_GI_solver_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.GI_solver]"))catch())

						try(
						enum_list = #( "None", "Path Tracing", "--", "HD Cache" ) -- "--" handles irregular order of DDL items
						format "corona_GI_secondary_solver_enums=%\n"  enum_list[renderers.current.GI_secondary_solver+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "corona_GI_secondary_solver_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.GI_secondary_solver]"))catch())

						try(
						enum_list = #( "Circular", "Bladed", "Custom" )
						format "corona_Type_of_bokeh_shape_enums=%\n"  enum_list[renderers.current.Type_of_bokeh_shape+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "corona_Type_of_bokeh_shape_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.Type_of_bokeh_shape]"))catch())

						try(
						enum_list = #( "None", "Native 3dsmax VFB", "Corona VFB" )
						format "corona_Type_of_VFB_window_enums=%\n"  enum_list[renderers.current.Type_of_VFB_window+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "corona_Type_of_VFB_window_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.Type_of_VFB_window]"))catch())

						try(
						enum_list = #( "None", "Box", "Gaussian", "Tent" ) -- "Tent" & "Gaussian" order swapped to match the DDL item index
						format "corona_Image_Filter_enums=%\n"  enum_list[renderers.current.Image_Filter+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "corona_Image_Filter_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.Image_Filter]"))catch())

						-- Not exposed to UI, but render property is present in Corona Alpha v6 & Alpha v7
						try(
						enum_list = #( "[PT+MIS] Path Tracing + Next Event Estimage", "[LT] Light Tracing", "[PPM] Progressive Photon Mapping", "[BDPM] Bidirectional PPM", "[BDPT] Bidirectional Path Tracing", "[VCM] Vertex Connection and Merging" )
						format "corona_VCM_mode_enums=%\n"  enum_list[renderers.current.VCM_mode+1] to:JobInfoFile
						for i = 0 to enum_list.count-1 do 
							format "corona_VCM_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
						)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.VCM_mode]"))catch())

						if coronaVersion == "Alpha v7.2" then --Corona Alpha v7.2 ONLY
						(
							try(
							enum_list = #( "Calculate From Scratch", "Load From File", "Load From File + Append" )
							format "corona_HD_cache_precalculation_mode_enums=%\n"  enum_list[renderers.current.HD_cache_precalculation_mode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "corona_HD_cache_precalculation_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.HD_cache_precalculation_mode]"))catch())
						)
					)
					--All other versions including pre 1.0 / final 1.0+ build
					else
					(
						if isProperty renderers.current #colormap_exposureType do
						(
							try(
							enum_list = #( "Use simple exposure", "Use photographic exposure" )
							format "corona_colormap_exposureType_enums=%\n"  enum_list[renderers.current.colormap_exposureType+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_colormap_exposureType_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.colormap_exposureType]"))catch())
						)

						if isProperty renderers.current #shading_primarySolver do
						(
							try(
							enum_list = #( "None (biased)", "Path Tracing" )
							format "corona_shading_primary_solver_enums=%\n"  enum_list[renderers.current.shading_primarySolver+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_shading_primary_solver_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.shading_primarySolver]"))catch())
						)

						if isProperty renderers.current #shading_secondarySolver do
						(
							try(
							enum_list = #( "None (biased)", "Path Tracing", "UHD Cache" )
							format "corona_shading_secondary_solver_enums=%\n"  enum_list[renderers.current.shading_secondarySolver+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_shading_secondary_solver_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.shading_secondarySolver]"))catch())
						)

						if isProperty renderers.current #bg_source do
						(
							try(
							enum_list = #( "Use 3ds max settings (Environment tab)", "Use Corona:" )
							format "corona_bg_source_enums=%\n"  enum_list[renderers.current.bg_source+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_bg_source_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.bg_source]"))catch())
						)

						if isProperty renderers.current #dof_bokehShape do
						(
							try(
							enum_list = #( "Circular", "Bladed", "Custom" )
							format "corona_dof_bokehShape_enums=%\n"  enum_list[renderers.current.dof_bokehShape+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_dof_bokehShape_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.dof_bokehShape]"))catch())
						)

						if isProperty renderers.current #geometry_displace_subdivType do
						(
							try(
							enum_list = #( "Screen size (px):", "World size (units):" )
							format "corona_geometry_displace_subdivType_enums=%\n"  enum_list[renderers.current.geometry_displace_subdivType+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_geometry_displace_subdivType_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.geometry_displace_subdivType]"))catch())
						)

						if isProperty renderers.current #shading_renderEngine do
						(
							try(
							enum_list = #( "Bucket", "--", "Progressive", "Bidir/VCM" ) -- "--" handles irregular order of DDL items
							format "corona_shading_renderEngine_enums=%\n"  enum_list[renderers.current.shading_renderEngine+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_shading_renderEngine_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.shading_renderEngine]"))catch())
						)

						if isProperty renderers.current #geometry_accelerationStructure do
						(
							try(
							enum_list = #( "None (slooow)", "BVH full SAH", "Intel(r) Embree" )
							format "corona_geometry_accelerationStructure_enums=%\n"  enum_list[renderers.current.geometry_accelerationStructure+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_geometry_accelerationStructure_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.geometry_accelerationStructure]"))catch())
						)
						
						if isProperty renderers.current #system_randomSampler do
						(
							try(
							enum_list = #( "Shared PRNG", "Per-pixel Shirley", "One-sample High-D", "5D Deterministic + PRNG", "Optimal 1S High-D", "Per-pixel Xorshift128", "Per-pixel TEA", "Per-pixel Xorshift*", "5D High-D + PRNG" )
							format "corona_system_randomSampler_enums=%\n"  enum_list[renderers.current.system_randomSampler+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_system_randomSampler_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.system_randomSampler]"))catch())
						)

						if isProperty renderers.current #texmapFiltering do
						(
							try(
							enum_list = #( "None", "All but opacity", "All" )
							format "corona_texmapFiltering_enums=%\n"  enum_list[renderers.current.texmapFiltering+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_texmapFiltering_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.texmapFiltering]"))catch())
						)

						if isProperty renderers.current #lights_solver do
						(
							try(
							enum_list = #( "Combined", "Better Object-based", "Object-based" )
							format "corona_lights_solver_enums=%\n"  enum_list[renderers.current.lights_solver+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_lights_solver_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.lights_solver]"))catch())
						)

						if isProperty renderers.current #lights_samplingMode do
						(
							try(
							enum_list = #( "Lights only", "BSDF only", "MIS - both (best)" )
							format "corona_lights_samplingMode_enums=%\n"  enum_list[renderers.current.lights_samplingMode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_lights_samplingMode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.lights_samplingMode]"))catch())
						)

						if isProperty renderers.current #gi_vcm_mode do
						(
							-- Not exposed to UI, but render property is present in Corona Alpha v6, Alpha v7 & pre1.0 build
							try(
							enum_list = #( "[PT+MIS] Path Tracing + Next Event Estimage", "[LT] Light Tracing", "[PPM] Progressive Photon Mapping", "[BDPM] Bidirectional PPM", "[BDPT] Bidirectional Path Tracing", "[VCM] Vertex Connection and Merging" )
							format "corona_gi_vcm_mode_enums=%\n"  enum_list[renderers.current.gi_vcm_mode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "corona_gi_vcm_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.gi_vcm_mode]"))catch())
						)

						if isProperty renderers.current #gi_uhdcache_preset do
						(
							-- Not exposed to UI, but render property is present in Corona Alpha pre1.0 build
							try(
							enum_list = #( "Still frame (fast precomputation)", "Animation (flickerfree)" )
							format "corona_gi_uhdcache_preset_enums=%\n"  enum_list[renderers.current.gi_uhdcache_preset+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "corona_gi_uhdcache_preset_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.gi_uhdcache_preset]"))catch())
						)

						if isProperty renderers.current #gi_hdCache_precalcMode do
						(
							try(
							enum_list = #( "Calculate From Scratch", "Load From File", "Load From File + Append" )
							format "corona_gi_hdCache_precalcMode_enums=%\n"  enum_list[renderers.current.gi_hdCache_precalcMode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "corona_gi_hdCache_precalcMode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.gi_hdCache_precalcMode]"))catch())
						)

						--Corona 1.6 changed the property name by prefixing the letter: "u" (gi_hd -> gi_uhd)
						if isProperty renderers.current #gi_uhdCache_precalcMode do
						(
							try(
							enum_list = #( "Calculate from scratch", "Load from file", "Load from file + append" )
							format "corona_gi_uhdCache_precalcMode_enums=%\n"  enum_list[renderers.current.gi_uhdCache_precalcMode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "corona_gi_uhdCache_precalcMode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.gi_uhdCache_precalcMode]"))catch())
						)

						if isProperty renderers.current #vfb_type do
						(
							try(
							enum_list = #( "None", "Native 3dsmax VFB", "Corona VFB" )
							format "corona_vfb_type_enums=%\n"  enum_list[renderers.current.vfb_type+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "corona_vfb_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.vfb_type]"))catch())
						)

						if isProperty renderers.current #image_filter_type do
						(
							try(
							enum_list = #( "None", "Box", "Gaussian", "Tent" ) -- "Tent" & "Gaussian" order swapped to match the DDL item index
							format "corona_image_filter_type_enums=%\n"  enum_list[renderers.current.image_filter_type+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do 
								format "corona_image_filter_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.image_filter_type]"))catch())
						)

						if isProperty renderers.current #image_prefilter_type do --new property in Corona 1.4 (replaces above option)
						(
							try(
							enum_list = #( "None", "Box", "Tent", "Parabolic", "Symmetric Tent", "Hann", "Blackman-Harris" ) -- "Symmetric Tent" & "Parabolic" order swapped to match the DDL item index
							format "corona_image_prefilter_type_enums=%\n" enum_list[renderers.current.image_prefilter_type+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_image_prefilter_type_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.image_prefilter_type]"))catch())
						)

						if isProperty renderers.current #renderSelected_mode do --new property in Corona 1.3
						(
							try(
							enum_list = #( "Disabled", "Viewport selection", "Object GBuffer ID", "Include/exclude list" ) -- "Include/exclude list" & "Viewport selection" order swapped to match DDL item index
							format "corona_renderSelected_mode_enums=%\n"  enum_list[renderers.current.renderSelected_mode+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_renderSelected_mode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.renderSelected_mode]"))catch())
						)

						if isProperty renderers.current #denoise_filterType do --new property in Corona 1.4, added "Gather data for later" [3] entry in v1.5
						(
							try(
							enum_list = #( "None", "Only remove fireflies", "Full denoising", "Gather data for later" )
							format "corona_denoise_filterType_enums=%\n" enum_list[renderers.current.denoise_filterType+1] to:JobInfoFile
							for i = 0 to enum_list.count-1 do
								format "corona_denoise_filterType_enums%=%\n" i enum_list[i+1] to:JobInfoFile
							)catch(try(SMTD_MainRollout.Ui_report ("--Corona Render Property Not Present. Skipping: [renderers.current.denoise_filterType]"))catch())
						)

						--hard-wired progressive render timeLimit options to override "corona_progressive_timeLimit" (milliseconds) in Monitor UI
						format "corona_progressive_timeLimit_override=false\n" to:JobInfoFile
						format "corona_progressive_timeLimit_hours=0\n" to:JobInfoFile
						format "corona_progressive_timeLimit_minutes=0\n" to:JobInfoFile
						format "corona_progressive_timeLimit_seconds=0\n" to:JobInfoFile
					)
				)--END CORONA RENDERER PROPERTIES

				--AUTODESK ART RENDERER PROPERTIES
				if rendererID == "art" AND SMTDSettings.ExportAdvancedRenderInfoArt then
				(
					for p in getPropNames renderers.current do
						try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()

					local enum_list = #("Advanced Path Tracing","Fast Path Tracing")
					format "art_render_method_enums=%\n"  enum_list[renderers.current.render_method+1] to:JobInfoFile
					for i = 0 to enum_list.count-1 do 
						format "art_render_method_enums%=%\n" i enum_list[i+1] to:JobInfoFile
				)--END AUTODESK ART RENDERER PROPERTIES
				
				--AUTODESK ARNOLD RENDERER PROPERTIES
				if rendererID == "arnold" AND SMTDSettings.ExportAdvancedRenderInfoArnold then
				(
					for p in getPropNames renderers.current do
						try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()
				)--END AUTODESK ARNOLD RENDERER PROPERTIES
				
				--IRAY RENDERER PROPERTIES
				if rendererID == "iray" AND SMTDSettings.ExportAdvancedRenderInfoIRay then
				(
					for p in getPropNames renderers.current do
					(
						if p != undefined and p == #HardwareReport then
						(
							local result = SMTDFunctions.ParseEolToSemicolon(getProperty renderers.current p)
							try(format "%_%=%\n" rendererID "HardwareReportString" result to:JobInfoFile)catch()
						)
						else
							try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()
					)
					
					enum_list = #( "#time", "#iterations", "#unlimited" )
					for i = 0 to enum_list.count-1 do 
						format "iray_durationMode%=%\n" i enum_list[i+1] to:JobInfoFile
					
					enum_list = #( "#Box", "#gauss", "#triangle" )
					for i = 0 to enum_list.count-1 do 
						format "iray_imageFilterType%=%\n" i enum_list[i+1] to:JobInfoFile

					enum_list = #( "#length", "#parametric" )
					for i = 0 to enum_list.count-1 do
						format "iray_displacementDisplaceMethod%=%\n" i enum_list[i+1] to:JobInfoFile
				)--END IRAY RENDERER PROPERTIES
				
				--QUICKSILVER RENDERER PROPERTIES
				if rendererID == "quicksilver" AND SMTDSettings.ExportAdvancedRenderInfoQuicksilver then
				(
					for p in getPropNames renderers.current do
						try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()

					/*
					-- Hardware Sampling Quality
					index = case renderers.current.HardwareSamplingQuality of
					(
						#none: 1
						#2x: 2
						#4x: 3
						#8x: 4
					)
					
					enum_list = #("None (Draft)", "2x", "4x", "8x")
					format "quicksilver_HardwareSamplingQuality_enums=%\n"  enum_list[index] to:JobInfoFile
					for i = 0 to enum_list.count-1 do 
						format "quicksilver_HardwareSamplingQuality_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					*/
					
					/*
					-- Software Sampling Quality
					index = case renderers.current.SoftwareSamplingQuality of
					(
						#none: 1
						#4x: 2
						#16x: 3
					)
					
					enum_list = #("None (Draft)", "4x", "16x")
					format "quicksilver_SoftwareSamplingQuality_enums=%\n"  enum_list[index] to:JobInfoFile
					for i = 0 to enum_list.count-1 do 
						format "quicksilver_SoftwareSamplingQuality_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					*/
					
					/*
					-- Depth of Field Mode
					index = case try(renderers.current.DepthOfFieldMode)catch(#camera) of
					(
						#camera: 1
						#Override: 2
					)
					
					enum_list = #("From Camera","Override Camera")
					format "quicksilver_DepthOfFieldMode_enums=%\n"  enum_list[index] to:JobInfoFile
					for i = 0 to enum_list.count-1 do 
						format "quicksilver_DepthOfFieldMode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					*/
					
					/*
					-- Transparency Mode
					index = case renderers.current.TransparencyMode of
					(
						#simple: 1
						#Best: 2
					)	

					enum_list = #("Simple","Best")
					format "quicksilver_TransparencyMode_enums=%\n"  enum_list[index] to:JobInfoFile
					for i = 0 to enum_list.count-1 do 
						format "quicksilver_TransparencyMode_enums%=%\n" i enum_list[i+1] to:JobInfoFile
					*/
				)--END QUICKSILVER RENDERER PROPERTIES
				
				--REDSHIFT RENDERER PROPERTIES
				if rendererID == "redshift" AND SMTDSettings.ExportAdvancedRenderInfoRedshift then
				(
					for p in getPropNames renderers.current do
					(
						try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()
					)
				)--END REDSHIFT RENDER PROPERTIES

				--OCTANE RENDERER PROPERTIES
				if rendererID == "octane" and SMTDSettings.ExportAdvancedRenderInfoOctane then
				(
					for p in getPropNames renderers.current do
					(
						try(format "%_%=%\n" rendererID (p as string) (getProperty renderers.current p) to:JobInfoFile)catch()
					)
				)--END OCTANE RENDERER PROPERTIES

				--EXPORT ADVANCED RENDERING SETTINGS ENDS HERE
				
				for aKeyPair in SMTDSettings.ExtraPluginInfoKeys where isKindOf aKeyPair Array and aKeyPair.count == 2 do
				(
					format "%=%\n" aKeyPair[1] aKeyPair[2] to:JobInfoFile
				) 

				Close JobInfoFile
				true
			)
			else
				false
		),
		
		fn saveSettingsStructToMSFile theFileName =
		(
			theProps = getPropNames SMTDSettings 
			theFile = createFile theFileName encoding:#utf8 writeBOM:true
			options.printAllElements = true
			for p in theProps do
			(
				theVal = (getProperty SMTDSettings p)
				case classof theVal of
				(
					string: (
						theVal = "\"" + theVal + "\""
						newStr = ""
						for i = 1 to theVal.count do 
							newStr += (if theVal[i] == "\\" then "\\\\" else theVal[i] )
						theVal = newStr
					)
					array: (
						theVal = SMTDFunctions.formatValue theVal
					)
				)
				
				format "SMTDSettings.% = %\n" (p as string) theVal to:theFile 
			)	
			close theFile
		),
		
		fn formatValue theVal =
		(
			case classof theVal of
			(
				string: (
					newStr = ""
					for i = 1 to theVal.count do 
						newStr += (if theVal[i] == "\\" then "\\\\" else theVal[i] )
					theVal = newStr
				)
				array: (
					for i = 1 to theVal.count do
						theVal[i] = (SMTDFunctions.formatValue theVal[i])
				)
			)
			theVal
		),
		
		fn CreateImsqFile imsqFilename =
		(
			startFrame = case (rendTimeType) of
			(
				1: SMTDFunctions.GetSequenceString #(currentTime)
				2: SMTDFunctions.GetSequenceString ( SMTDFunctions.outOfOrderSequence (for t in animationRange.start to animationRange.start by 1 collect t) )
				3: SMTDFunctions.GetSequenceString ( SMTDFunctions.outOfOrderSequence (for t in rendStart to rendStart by 1 collect t) )
				4: 0
			)
			
			endFrame = case (rendTimeType) of
			(
				1: SMTDFunctions.GetSequenceString #(currentTime)
				2: SMTDFunctions.GetSequenceString ( SMTDFunctions.outOfOrderSequence (for t in animationRange.end to animationRange.end by 1 collect t) )
				3: SMTDFunctions.GetSequenceString ( SMTDFunctions.outOfOrderSequence (for t in rendEnd to rendEnd by 1 collect t) )
				4: 0
			)
			
			local imsqFile = CreateFile imsqFilename encoding:#utf8 writeBOM:true
			if (imsqFile != undefined) then
			(
				path = getFilenamePath RendOutputFilename
				filename = getFilenameFile RendOutputFilename
				extension = getFilenameType RendOutputFilename
						
				format "<ImageSequence Pattern=\"%%[####]%\" " path filename extension to:imsqFile
				format "First=\"%\" Last=\"%\" " startFrame endFrame to:imsqFile
				format "FrameRate=\"%/1\" />\n" frameRate to:imsqFile
								
				Close imsqFile
				true
			)
			else
				false
		),
		
		fn CreateImsqVbscript imsqVbscript imsqFilename =
		(
			local scriptFile = CreateFile imsqVbscript encoding:#utf8 writeBOM:true
			if (scriptFile != undefined) then
			(
				filename = getFilenameFile imsqFilename
				extension = getFilenameType imsqFilename
			
				copyPath = SMTDSettings.ImsqOutputPath + "\\" + filename + extension

				format ("from System.IO import *\n") to:scriptFile
				format ("from Deadline.Scripting import *\n\n") to:scriptFile
				format ("def __main__( *args ):\n") to:scriptFile
				format ("	deadlinePlugin = args[0]\n") to:scriptFile
				format ("	deadlinePlugin.LogInfo( r'Copying imsq file to " + copyPath + "...' )\n") to:scriptFile
				format ("	File.Copy( r'" + imsqFilename + "', r'" + copyPath + "', True )\n") to:scriptFile
				format ("	deadlinePlugin.LogInfo( 'Copy complete.' )\n") to:scriptFile
				
				Close scriptFile
				true
			)
			else
				false
		),
		
		fn createSubmissionFolderAndUpdatePaths =
		(
			local theSubFolder = ""
			do(
				local theFilterTime = filterString localtime " /\\-:"
				local theTime = ""
				for i = 1 to theFilterTime.count-1 do theTime += theFilterTime[i] + "_"
				theTime += theFilterTime[theFilterTime.count]	
				theSubFolder = SMTDPaths.TempDir + theTime + "\\"
			)while (doesFileExist theSubFolder)
			makeDir theSubFolder all:true
			SMTDPaths.submitSubFolder = theSubFolder
			SMTDPaths.SubmitInfoFile = 	theSubFolder + "max_submit_info.job"
			SMTDPaths.JobInfoFile = 	theSubFolder + "max_job_info.job"
			SMTDPaths.ResultFile = theSubFolder + "max_output.txt"
			SMTDPaths.BitmapList = theSubFolder + "max_sceneBitmaps.txt"
			SMTDPaths.RestoreTempMaxFile = theSubFolder + "max_backup_file.mx"
			SMTDPaths.SubmitOutput = theSubFolder + "submitOutput.txt"
			SMTDPaths.SubmitExitCode = theSubFolder + "submitExitCode.txt"
			SMTDPaths.ImsqVbscriptFile = theSubFolder + "copyImsq.py"
			SMTDPaths.DraftConfigFile = theSubFolder  + "draft_tile_config.txt"
			theSubFolder
		),

		fn getDateTimeFormatSeparator = 
		(
			local cultureInfo = dotNetClass "System.Globalization.CultureInfo"
			local culture = cultureInfo.CurrentCulture
			local dateTimeFormat = culture.DateTimeFormat
			dateSeparator = dateTimeFormat.DateSeparator
		),
		
		fn cleanUpSubmissionFolders all:false exclude:#() =
		(
			local sysio = dotNetClass "System.IO.Directory"
			local theFilterTime = filterString localtime " /\\-:."
			local theTime = "*"

			local dateSeparator = SMTDFunctions.getDateTimeFormatSeparator()

			for i = 1 to 2 do theTime += theFilterTime[i] + dateSeparator
			theTime += theFilterTime[3] + "*"
			
			theDirs = getDirectories (SMTDPaths.TempDir+"*")
			theDirs = for d in theDirs where (not matchPattern d pattern:theTime or all == true) and not matchPattern d pattern:"*lightning*" collect d
			theDirs = for d in theDirs where (for j in exclude where matchPattern d pattern:j collect j).count == 0 collect d
			for d in theDirs do
			(
				for f in getFiles (d+"*") do deleteFile f
				try(sysio.Delete d true)catch()
			)
		),
		
		fn replaceFrameNumber filename newFrame =
		(
			local theName = getFileNameFile filename
			local frameString = ""
			local done = false
			for i = theName.count to 1 by -1 while not done do
			(
				if findString "0123456789#-" theName[i] == undefined then
					done = true
				else
					frameString = theName[i]+frameString
			)
			theName = substring theName 1 (theName.count-frameString.count) + (formattedPrint newFrame format:"04i")
			getFileNamePath filename + theName + getFileNameType filename
		),
		
		fn replaceAllHashesWithFrameNumber filename newFrame =
		(
			regex = dotnetclass "system.text.regularexpressions.regex"
			rePattern = "#+"
			
			local theName = getFileNameFile filename
			theName = regex.replace theName rePattern (formattedPrint newFrame format:"04i")
			getFileNamePath filename + theName + getFileNameType filename
		),

		fn interpolateAnimatedRegion aData theTime =
		(
			local theArray = aData[10]
			local returnValue= if theArray == undefined or theArray.count == 0 then 
				#(theTime, aData[2], aData[3], aData[4], aData[5]) --constant value
			else if theArray.count == 1 then theArray[1] --one key
			else --multiple keys
			(
				local theMin = 0
				local theEqual = 0
				for i = 1 to theArray.count do 
				(
					if theArray[i][1] <= theTime as integer do theMin = i
					if theArray[i][1] == theTime as integer do theEqual = i
				)
				returnValue = if theMin == theArray.count then 
					theArray[theArray.count]
				else if theMin == 0 then theArray[1]
				else 
				(
					local theLeftRecord  = theArray[theMin]
					local theRightRecord = theArray[theMin+1]
					local factor = (1.0 * theTime as integer-theLeftRecord[1]) / (theRightRecord[1]-theLeftRecord[1])
					--format "% (%)-> %\n" theLeftRecord factor theRightRecord
					#(theTime as integer, theLeftRecord[2]*(1-factor) + theRightRecord[2]*factor, theLeftRecord[3]*(1-factor) + theRightRecord[3]*factor, theLeftRecord[4]*(1-factor) + theRightRecord[4]*factor, theLeftRecord[5]*(1-factor) + theRightRecord[5]*factor )
				)
			)	
			returnValue				
		),
		
		fn getBatchName =
		(
			(SMTDFunctions.FormatJobName SMTDSettings.JobName) + " BATCH [" + localtime +"]"
		),

		fn ParseEolToSemicolon tempString =
		(
			--remove carriage returns and line feeds
			removeChars = "\n\r"
			for a = 1 to removeChars.count do (tempString = substituteString tempString removeChars[a] ";")
			
			--deal with duplicate trailing semicolons
			while (matchPattern tempString pattern:"*;;*") do (tempString = substituteString tempString ";;" ";")
			tempString = (trimLeft (trimRight tempString ";") ";")

			tempString
		),

		--SUBMIT TILE JOBS
		fn spawnTileJobs forceMaxFile:"" batchName:"" forceCamera:"" stereoCameraLabel:"" =
		(
			try(SMTD_MainRollout.Ui_report (">Spawning Tile Jobs."))catch()
			
			if batchName == "" do batchName = SMTDFunctions.getBatchName() --when spawning tile jobs, we assume that all of them should be batched together.
				
			local stereoCameraToken = ""
			if stereoCameraLabel != "" do stereoCameraToken = stereoCameraLabel+"_"
			
			SMTDSettings.TilesSubmissionJobIDs = #()

			renderDimensions = SMTDFunctions.getRenderDimensions() --#(renderWidth,renderHeight,renderPixelAspect)

			local DeltaX = (floor (1.0*renderDimensions[1]/SMTDSettings.TilesInX)) as integer
			local DeltaY = (floor (1.0*renderDimensions[2]/SMTDSettings.TilesInY)) as integer
			
			if SMTDSettings.TileBlowupMode then
			(
				DeltaX = (floor (1.0*(renderDimensions[1]/SMTDSettings.TilesInX)/SMTDSettings.TilesInX)) as integer
				DeltaY = (floor (1.0*(renderDimensions[2]/SMTDSettings.TilesInY)/SMTDSettings.TilesInY)) as integer
			)
			
			local theOutput = rendOutputFileName
			local theOutPath = getFileNamePath theOutput
			local theBaseName = getFileNameFile theOutput
			local theOutType = getFileNameType theOutput
			local theJobName = SMTDSettings.JobName
			
			local TempMaxFile 
			if forceMaxFile == "" then
				TempMaxFile = maxFilePath + maxFileName
			else	
				TempMaxFile = forceMaxFile

			local theNetworkPath = SMTDPaths.MainSubmissionDir + "\\" 

			local BitmapsCopyData = #()
			if SMTDSettings.CurrentRepository == "" and SMTDSettings.SubmitExternalFilesMode > 1 do
				BitmapsCopyData = SMTDFunctions.GetExternalFilesToCopy()
			
			local currentTile = 0

--------------------------------------------------------------				
--MULTI-FRAME MULTI-REGION  RENDERING
--------------------------------------------------------------				
			if SMTDSettings.RegionRenderingMode == #animationMultiRegion do
			(
				try(SMTD_MainRollout.Ui_report (">Multi-Frame Multi-Region Data Preparation..."))catch()

				SMTDSettings.SingleTileJobLeft = ""
				SMTDSettings.SingleTileJobRight = ""
				SMTDSettings.SingleTileJobTop = ""
				SMTDSettings.SingleTileJobBottom = ""
				SMTDSettings.SingleTileJobFilename = ""
				SMTDSettings.SingleTileJobReFilename = ""
				local SingleTileJobReFilenameSS = "" as stringStream
				local reManager = maxOps.GetCurRenderElementMgr()
				local reObjects = #()

				if reManager != undefined do
				(
					local reCount = reManager.NumRenderElements()
					reObjects = for i = 0 to reCount-1 collect
					(
						local reObject = reManager.GetRenderElement i
						#(reObject, try(reObject.enabled)catch(false), try(reManager.GetRenderElementFilename i)catch(""))
					)
				)--end if reManager undefined				
				
				local tileLefts = #()
				local tileBottoms = #()
				local currentFrame = 0
				local currentFrameList = ""
				
				local framesList = SMTDFunctions.GetFrameSequenceArray()
				
				local regionRenderJobIds = #()
				
				local splitFileName = ""
				local splitName = ""
				local rawName = ""
				local rawFileName = ""
				if (SMTDFunctions.getRendererIdString() == "vray") then
				(
					splitName = renderers.current.output_splitfilename
					local splitFile = renderers.current.output_splitgbuffer
					
					if(splitFile==true) then
					(
						if(splitName == undefined or splitName == "") then
						(
							splitFile = false
						)
						else
						(
							SMTDSettings.SplitBufferFile = "SplitBufferFile="+(splitFile as string)+"\n" --True/False
						)
					)
					
					local rawFile = renderers.current.output_saveRawFile
					rawName = renderers.current.output_rawFileName
					
					if(rawFile==true) then
					(
						if(rawName == undefined or rawName == "") then
						(
							rawFile = false
						)
						else
						(
							SMTDSettings.RawBufferFile = "RawBufferFile="+(rawFile as string)+"\n" --True/False
						)
					)
				)
				
				local currentIndex = 0
				for aData in SMTDSettings.MultiRegionData where aData[1] == True while ::SMTDIsCurrentlySubmitting != False do
				(
					for y = 1 to aData[7] while ::SMTDIsCurrentlySubmitting != False do
					(
						for x = 1 to aData[6] while ::SMTDIsCurrentlySubmitting != False do
						(
							try(windows.processPostedMessages())catch()
							SMTDFunctions.createSubmissionFolderAndUpdatePaths() --create a new submission folder
								
							local tempLeft = #()
							local tempTop = #()
							local tempRight = #()
							local tempBottom = #()
							
							local tileString = "_region_" + (currentIndex) as string + "_"
							local splitCount = 0
							local rawCount = 0
							SMTDSettings.SplitBufferFilename = ""
							SMTDSettings.RawBufferFilename = ""
							if splitFile==true do
							(
								splitFileName = getFilenamePath splitName
								splitFileName += stereoCameraToken
								if SMTDSettings.StateSetsSubmit and SMTDSettings.StateSetRenameOutput and not matchPattern (getFilenameFile splitName) pattern:(SMTDSettings.StateSetName +"_*") do splitFileName += SMTDSettings.StateSetName + "_"
								splitFileName +=(getFilenameFile splitName)+tileString+(getFilenameType splitName) --Delimiter is NOT required here as the VRay split RE is already delimited
							)
								
							if rawFile==true do
							(
								rawFileName = getFilenamePath rawName
								rawFileName += stereoCameraToken
								if SMTDSettings.StateSetsSubmit and SMTDSettings.StateSetRenameOutput and not matchPattern (getFilenameFile rawName) pattern:(SMTDSettings.StateSetName +"_*") do rawFileName += SMTDSettings.StateSetName + "_"
								rawFileName+=(getFilenameFile rawName)+tileString
								if (isProperty renderers.current #fileName_addDot) and (getProperty renderers.current #fileName_addDot) do rawFileName+=SMTDSettings.Delimiter
								rawFileName+=(getFilenameType rawName)
							)
							
							renderDimensions = SMTDFunctions.getRenderDimensions() --#(renderWidth,renderHeight,renderPixelAspect)

							for t in framesList do --loop through all frames
							(
								local theAnimRegionValue = SMTDFunctions.interpolateAnimatedRegion aData t
								local theTileWidth = theAnimRegionValue[4]/aData[6]
								local theTileHeight = theAnimRegionValue[5]/aData[7]
								local corner1X = ((floor ((theAnimRegionValue[2]+(theTileWidth*(x-1)))*renderDimensions[1])) as integer)
								local corner1Y = ((floor ((theAnimRegionValue[3]+(theTileHeight*(y-1)))*renderDimensions[2])) as integer)
								local corner2X = ((floor (((theAnimRegionValue[2]+(theTileWidth*x))*renderDimensions[1])+0.5)) as integer)
								local corner2Y = ((floor (((theAnimRegionValue[3]+(theTileHeight*y))*renderDimensions[2])+0.5)) as integer)

								append tempLeft corner1X
								append tempTop corner1Y
								append tempRight corner2X
								append tempBottom corner2Y
									
								--format "Time %: LeftX:% LeftY:% RightX:% RightY:% RegionWidth:% ActualWidth:%  RegionHeight:% ActualHeight: %\n" t corner1X corner1Y corner2X corner2Y (corner2X-corner1X) (renderWidth*theTileWidth) (corner2Y-corner1Y) (theTileHeight*renderHeight)
								
								if (SMTDFunctions.getRendererIdString() == "vray") then
								(
									if(splitFile==true) then
									(
										SMTDSettings.SplitBufferFilename += "SplitBufferFilename" + (splitCount as string) + "=" + splitFileName+"\n"
										splitCount += 1
									)
									
									if(rawFile==true) then
									(
										SMTDSettings.RawBufferFilename += "RawBufferFilename" + (rawCount as string) + "=" + rawFileName+"\n"
										rawCount += 1
									)
								)

								--append tileLefts corner1X
								--append tileBottoms (RenderHeight - corner2Y)							

							)--end t loop		

							SMTDSettings.RegionLeft = tempLeft
							SMTDSettings.RegionRight = tempRight
							SMTDSettings.RegionTop = tempTop
							SMTDSettings.RegionBottom = tempBottom
							
							currentTile +=1
							if currentFrameList == "" then
								currentFrameList = (currentFrame as string)
							else
								currentFrameList = currentFrameList + "," + (currentFrame as string) 

							try(SMTD_MainRollout.Ui_report (">Submitting Multi-Frame, Multi-Region Job " + currentIndex as string ))catch()
							SMTDSettings.JobName = theJobName + " - Region "+ currentIndex as string
								
							---------------------------------------
							--ACTUAL SUBMISSION
							---------------------------------------
							SMTDSettings.SingleTileJobReFilename = SingleTileJobReFilenameSS as string
							SMTDSettings.SingleTileJobTileCount = currentTile
							
							SMTDSettings.SingleTileJobFrameList = ""
														
							SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile batchName:batchName currentTileString:("_region_" + currentIndex as string + "_") stereoCameraLabel:stereoCameraLabel
								
							SMTDFunctions.CreateJobInfoFile SMTDPaths.JobInfoFile tileString:("_region_" + currentIndex as string + "_") forceCamera:forceCamera stereoCameraLabel:stereoCameraLabel --renderOutputOverride:(theOutPath + theBaseName  + "_region_" + currentIndex as string + "_" + theOutType)
							
							local initialArgs = "" as stringStream
							format "-outputfiles\n%\n%\n" SMTDPaths.SubmitOutput  SMTDPaths.SubmitExitCode to:initialArgs
							
							if SMTDSettings.bgSubmission do format "-background\n-notify\n" to:initialArgs 
							if SMTDSettings.dropSubmission do format "-drop\n" to:initialArgs 
							
							if( SMTDSettings.SubmitSceneMode == #reposave ) then
								format "%\n%\n%\n" SMTDPaths.SubmitInfoFile SMTDPaths.JobInfoFile TempMaxFile to:initialArgs 
							else
								format "%\n%\n" SMTDPaths.SubmitInfoFile SMTDPaths.JobInfoFile to:initialArgs 
							 
							if SMTDSettings.CopyVbscriptFile do format "%\n" SMTDPaths.ImsqVbscriptFile to:initialArgs
							if SMTDSettings.RunPreLoadScript do format "%\n" SMTDSettings.PreLoadScriptFile to:initialArgs
							if SMTDSettings.RunPostLoadScript do format "%\n" SMTDSettings.PostLoadScriptFile to:initialArgs
							if SMTDSettings.RunPreFrameScript do format "%\n" SMTDSettings.PreFrameScriptFile to:initialArgs
							if SMTDSettings.RunPostFrameScript do format "%\n" SMTDSettings.PostFrameScriptFile to:initialArgs
							if SMTDSettings.SubmitSceneMode == #reposave do
							(
								if SMTDSettings.UsePathConfigFile and doesFileExist SMTDSettings.PathConfigFile do format "%\n" SMTDSettings.PathConfigFile to:initialArgs
							)

							--Output external files to the command line for copying
							if SMTDSettings.SubmitExternalFilesMode > 1 do				
								for aBitmap in BitmapsCopyData where findItem SMTDSettings.MissingFiles aBitmap[2] == 0 do
									format "%\n" aBitmap[2] to:initialArgs

							/*	
							if theExternalFilesToCopy.count > 0 then
								SMTDFunctions.CopyExternalFilesWithinRepository theExternalFilesToCopy
							else
								SMTDFunctions.CopyExternalFilesToRepository()
							*/

							local initialArgsFileName = (getFileNamePath SMTDPaths.JobInfoFile + "MultiRegionRenderArgsFile.txt") 
							local initialArgsFile = createFile initialArgsFileName encoding:#utf8 writeBOM:true
							format "%\n" (initialArgs as string) to:initialArgsFile
							close initialArgsFile 
							initialArgsFileName = "\""+initialArgsFileName+"\""
							
							retcode = SMTDFunctions.waitForCommandToComplete initialArgsFileName SMTDSettings.TimeoutSubmission paramIsFile:true dontWait:SMTDSettings.UseSubmissionQueue
							if not SMTDSettings.UseSubmissionQueue do
							(
								local renderMsg = SMTDFunctions.getRenderMessage()				
								try(SMTD_MainRollout.Ui_report ((if retcode == #success then "+" else "--")+"Submission Result: \n\n" + renderMsg))catch()		
							)
							if retcode == #success or retcode == #queued then
							(
								if retcode == #success do
								(
									SMTDFunctions.getJobIDFromMessage renderMsg
									SMTDFunctions.SubmitTransferJob() -- submits a remote transfer job if necessary
									append regionRenderJobIds SMTDSettings.DeadlineSubmissionLastJobID	
									
									if SMTDSettings.AssetsPreCacheFiles == true AND SMTDSettings.AssetsIncludeFilesInJob == true then
									(
										local PrecacheResults = SMTDFunctions.CallDeadlineCommandInMemory ("-AWSPortalPrecacheJob " + SMTDSettings.DeadlineSubmissionLastJobID ) multiLine:true
										try(SMTD_MainRollout.Ui_report (">AWS Portal Pre-Cache Results: \n\n"+PrecacheResults))catch()
									)
								)
							)--end success
							else
								return false
							currentIndex += 1
						)--end x loop
					)--end y loop
				)--end i loop (active regions)			

-- NOW SUBMIT DEPENDENT DRAFT ASSEMBLY JOBS
				local jobName = SMTDSettings.JobName 
				if stereoCameraLabel != "" do jobName += " ["+stereoCameraLabel+"]"
				if SMTDSettings.StateSetsSubmit and SMTDSettings.StateSetRenameOutput do jobName += (" [STATE SET '"+ SMTDSettings.StateSetName + "']")
				
				if rendSaveFile and ::SMTDIsCurrentlySubmitting != False then
				(
					if rendOutputFilename != undefined and rendOutputFilename != "" then
					(
						try(SMTD_MainRollout.Ui_report (">Submitting Draft Assembly Job For Multi-Frame, Multi-Regions Beauty Pass"))catch()

						local paddingString = formattedPrint (currentTime.frame as integer) format:"04i"

						local outputImageFilenames = #()
						--local fileCount = 0
						filenameToRender = SMTDFunctions.GetFormattedOutputFilename rendOutputFilename addFramePadding:true regionString:"" stereoCameraToken:stereoCameraLabel
							
						append outputImageFilenames filenameToRender	
						
						local inputImageFilenames = #()
						local theIndex = 0
						for aData2 in SMTDSettings.MultiRegionData where aData2[1] == True do
						(
							for y2 = 1 to aData2[7] do
							(
								for x2 = 1 to aData2[6] do
								(
									local currTileString = "_region_" + theIndex as string + "_" 
									local theFile = SMTDFunctions.GetFormattedOutputFilename rendOutputFilename addFramePadding:false regionString:currTileString stereoCameraToken:stereoCameraLabel
									append inputImageFilenames theFile
									theIndex += 1
								)
							)
						)
						local SingleLayerTilesCount = inputImageFilenames.count --this is the number of tiles before RE are considered!

						local jobIdsString = "" as stringStream 
						for j in regionRenderJobIds do format "%," j to:jobIdsString 
						jobIdsString = jobIdsString as string
						jobIdsString = substring jobIdsString 1 (jobIdsString.count-1)
						local tileResult = SMTDFunctions.SubmitDraftTileAssemblerJob jobIdsString (theJobName + " ["+SingleLayerTilesCount as string + " Animation Regions Draft Assembly - Beauty RGBA]") outputImageFilenames SingleLayerTilesCount tileLefts tileBottoms inputImageFilenames framesList batchName:batchName
						local renderMsg = SMTDFunctions.getRenderMessage()
						try(SMTD_MainRollout.Ui_report ((if tileResult then "+" else "--")+"Submission Result: \n\n" + renderMsg))catch()		
						
						if not tileResult do return false
					)
					else
					(
						try(SMTD_MainRollout.Ui_report ("!!Skipping Draft Assembly Job Submission as Render Output Filename is undefined."))catch()
						SMTDSettings.nonFatalErrorsCount+=1
					)
				)
				else
				(
					try(SMTD_MainRollout.Ui_report ("!!Skipping Draft Assembly Job Submission as Render Output Save File is disabled."))catch()
					SMTDSettings.nonFatalErrorsCount+=1
				)

				-- If any render elements are specified, include them 
				elementsToSkip = #()
				
				-- If rendering with VRay frame buffer, then we don't want to assemble the render elements because they
				-- are embedded in the main image.
				if (SMTDFunctions.getRendererIdString() == "vray" and renderers.current.output_on ) then
				(
					local paddingString = formattedPrint (currentTime.frame as integer) format:"04i"
					
					local jobIdsString = "" as stringStream 
					for j in regionRenderJobIds do format "%," j to:jobIdsString 
					jobIdsString = jobIdsString as string
					jobIdsString = substring jobIdsString 1 (jobIdsString.count-1)
					
					if renderers.current.output_saveRawFile then
					(
						local rawName = renderers.current.output_rawFileName

						if ( rawName != undefined and rawName != "" ) then
						(
							local rawBaseName = (getFilenameFile rawName) --el.elementName
							local rawOutputType = (getFilenameType rawName)
							local rawPath = (getFilenamePath rawName)
							
							if not matchPattern rawOutputType pattern:"*vrimg*" then
							(
								local outputImageFilenames = #()
								local inputImageFilenames = #()										
								local theIndex = 0

								local theFile = SMTDFunctions.GetFormattedOutputFilename rawName addFramePadding:true regionString:"" stereoCameraToken:stereoCameraLabel addFrameDelimiter:((isProperty renderers.current #fileName_addDot) and (getProperty renderers.current #fileName_addDot))
								append outputImageFilenames theFile
								
								local theIndex = 0
								for aData in SMTDSettings.MultiRegionData where aData[1] == True do
								(
									for y = 1 to aData[7] do
									(
										for x = 1 to aData[6] do
										(
											local currTileString = "_region_" + theIndex as string + "_" 
											local theFile = SMTDFunctions.GetFormattedOutputFilename rawName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:((isProperty renderers.current #fileName_addDot) and (getProperty renderers.current #fileName_addDot))
											append inputImageFilenames theFile
											--SMTD_MainRollout.Ui_report (">MRR Render Element Input Filename ["+theFile+"]")
											theIndex += 1
										)--end x loop
									)--end y loop
								)--end region loop
								try(SMTD_MainRollout.Ui_report (">Submitting Draft Assembly Job For Multi-Frame, Multi-Regions Raw Buffer."))catch()
								local tileCount = inputImageFilenames.count
								local tileResult = SMTDFunctions.SubmitDraftTileAssemblerJob jobIdsString (theJobName + " ["+ tileCount as string +" Animation Regions Draft Assembly - Raw Buffer]") outputImageFilenames tileCount tileLefts tileBottoms inputImageFilenames framesList batchName:batchName
								local renderMsg = SMTDFunctions.getRenderMessage()				
								try(SMTD_MainRollout.Ui_report ((if tileResult then "+" else "--")+"Submission Result: \n\n" + renderMsg))catch()		
								if not tileResult do return false
							)
							else
							(
								try(SMTD_MainRollout.Ui_report ("!!Skipping Draft Assembly Job Submission For VRay Raw Buffer, File Format .vrimg Not Supported!"))catch()
								SMTDSettings.nonFatalErrorsCount+=1
							)
						)
						else
						(
							try(SMTD_MainRollout.Ui_report ("!!Skipping Draft Assembly Job Submission For VRay Raw Buffer as File Path is Empty."))catch()
							SMTDSettings.nonFatalErrorsCount+=1
						)
					)
					
					if renderers.current.output_splitgbuffer AND renderers.current.output_useram then
					(
						local splitName = renderers.current.output_splitfilename

						if ( splitName != undefined and splitName != "" ) then
						(						
							local replaceHashes = false
							try( replaceHashes = renderers.current.output_expandFrameNumber )catch()
						
							if renderers.current.output_splitRGB then
							(
								--Update VFB Split Channels FilePath
								local splitName = renderers.current.output_splitfilename
								local splitName = SMTDFunctions.ReturnVraySplitPath splitName elementType:"RGB_color"
								local splitBaseName = (getFilenameFile splitName)
								local splitOutputType = (getFilenameType splitName)
								local splitPath = (getFilenamePath splitName)

								local outputImageFilenames = #()
								local inputImageFilenames = #()										
								local theIndex = 0
								
								local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:".RGB_color." stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
								append outputImageFilenames theFile
								
								local theIndex = 0
								for aData in SMTDSettings.MultiRegionData where aData[1] == True do
								(
									for y = 1 to aData[7] do
									(
										for x = 1 to aData[6] do
										(
											local currTileString = "_region_" + theIndex as string + "_" + ".RGB_color."
											local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
											append inputImageFilenames theFile
											--SMTD_MainRollout.Ui_report (">MRR Render Element Input Filename ["+theFile+"]")
											theIndex += 1
										)--end x loop
									)--end y loop
								)--end region loop
								try(SMTD_MainRollout.Ui_report (">Submitting Draft Assembly Job For Multi-Frame, Multi-Regions [RGB_color] Render Element."))catch()
								
								local tileCount = inputImageFilenames.count
								local tileResult = SMTDFunctions.SubmitDraftTileAssemblerJob jobIdsString (theJobName + " ["+tileCount as string+ " Animation Regions Draft Assembly - RE:RGB_color]") outputImageFilenames tileCount tileLefts tileBottoms inputImageFilenames framesList batchName:batchName replaceHashes:replaceHashes
								local renderMsg = SMTDFunctions.getRenderMessage()				
								try(SMTD_MainRollout.Ui_report ((if tileResult then "+" else "--")+"Submission Result: \n\n" + renderMsg))catch()		
								if not tileResult do return false
							)
							
							if renderers.current.output_splitAlpha then
							(
								--Update VFB Split Channels FilePath
								local splitName = renderers.current.output_splitfilename
								local splitName = SMTDFunctions.ReturnVraySplitPath splitName elementType:"Alpha"
								local splitBaseName = (getFilenameFile splitName)
								local splitOutputType = (getFilenameType splitName)
								local splitPath = (getFilenamePath splitName)

								local outputImageFilenames = #()
								local inputImageFilenames = #()										
								local theIndex = 0
								
								local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:".Alpha." stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
								append outputImageFilenames theFile
								
								local theIndex = 0
								for aData in SMTDSettings.MultiRegionData where aData[1] == True do
								(
									for y = 1 to aData[7] do
									(
										for x = 1 to aData[6] do
										(
											local currTileString = "_region_" + theIndex as string + "_" + ".Alpha."
											local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
											append inputImageFilenames theFile
											--SMTD_MainRollout.Ui_report (">MRR Render Element Input Filename ["+theFile+"]")
											theIndex += 1
										)--end x loop
									)--end y loop
								)--end region loop
								try(SMTD_MainRollout.Ui_report (">Submitting Draft Assembly Job For Multi-Frame, Multi-Regions [Alpha] Render Element."))catch()
								
								local tileCount = inputImageFilenames.count
								local tileResult = SMTDFunctions.SubmitDraftTileAssemblerJob jobIdsString (theJobName + " ["+tileCount as string+ " Animation Regions Draft Assembly - RE:Alpha]") outputImageFilenames tileCount tileLefts tileBottoms inputImageFilenames framesList batchName:batchName replaceHashes:replaceHashes
								local renderMsg = SMTDFunctions.getRenderMessage()				
								try(SMTD_MainRollout.Ui_report ((if tileResult then "+" else "--")+"Submission Result: \n\n" + renderMsg))catch()		
								if not tileResult do return false
							)
							
							local reManager = maxOps.GetCurRenderElementMgr()
							if reManager != undefined do
							(
								if reManager.GetElementsActive() then 
								(
									local reCount = reManager.NumRenderElements()
									for i = 0 to reCount - 1 do
									(
										local reObject = reManager.GetRenderElement i
										if classof reObject != Missing_Render_Element_Plug_in AND reObject.enabled AND classof reObject != VRayOptionRE AND classof reObject != VRayAlpha then
										(
											--Re-define splitName to include any SMTD pathing options specific for VFB RE Split Channels
											local splitName = reManager.GetRenderElementFilename i
											local splitBaseName = (getFilenameFile splitName)
											local splitOutputType = (getFilenameType splitName)
											local splitPath = (getFilenamePath splitName)

											local reArtifactSuffixes = SMTDFunctions.RenderElementArtifactSuffixes(reObject)
											for reArtifactSuffix in reArtifactSuffixes do
											(
												local outputImageFilenames = #()
												local inputImageFilenames = #()
												local theIndex = 0

												local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:("." + reArtifactSuffix + ".") stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
												append outputImageFilenames theFile
												try(SMTD_MainRollout.Ui_report (">Render Element [" + reArtifactSuffix + "] Output Filename ["+theFile+"]"))catch()

												local theIndex = 0
												for aData in SMTDSettings.MultiRegionData where aData[1] == True do
												(
													for y = 1 to aData[7] do
													(
														for x = 1 to aData[6] do
														(
															local currTileString = "_region_" + theIndex as string + "_" + "." + reArtifactSuffix + "."
															local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
															append inputImageFilenames theFile
															--SMTD_MainRollout.Ui_report (">MRR Render Element Input Filename ["+theFile+"]")
															theIndex += 1
														)--end x loop
													)--end y loop
												)--end region loop
												try(SMTD_MainRollout.Ui_report (">Submitting Draft Assembly Job For Multi-Frame, Multi-Regions [" + reArtifactSuffix + "] Render Element."))catch()

												local tileCount = inputImageFilenames.count
												local tileResult = SMTDFunctions.SubmitDraftTileAssemblerJob jobIdsString (theJobName + " [" + tileCount as string + " Animation Regions Draft Assembly - RE:" + reArtifactSuffix + "]") outputImageFilenames tileCount tileLefts tileBottoms inputImageFilenames framesList batchName:batchName replaceHashes:replaceHashes
												local renderMsg = SMTDFunctions.getRenderMessage()
												try(SMTD_MainRollout.Ui_report ((if tileResult then "+" else "--")+"Submission Result: \n\n" + renderMsg))catch()
												if not tileResult do return false
											)
										)--is re enabled?
									)
								)
							)--end if reManager undefined
						)
						else
						(
							try(SMTD_MainRollout.Ui_report ("!!Skipping Draft Assembly Job Submission For VRay Split Buffer as File Path is Empty."))catch()
							SMTDSettings.nonFatalErrorsCount+=1
						)
					)
				)
				else
				(
					-- If this is 3dsmax 2011 or later, check to see if we're rendering to the new exr format
					if ((maxVersion())[1]/1000 as integer) >= 13 do
					(
						if rendSaveFile then
						(
							if rendOutputFilename != undefined and rendOutputFilename != "" then
							(
								rend_type = getFileNameType rendOutputFilename
								is_exr = matchPattern rend_type pattern:".exr" ignoreCase:true
								is_fxr = matchPattern rend_type pattern:".fxr" ignoreCase:true
								
								-- If we are, we need to tell Deadline which render elements are to be embedded in the exr file so that it doesn't save them separately
								if (is_exr or is_fxr) and (fopenexr != undefined) do
								(
									if fopenexr.isAutoAddRenderElements() then
									(
										--The elements are being added automatically, so check the re manager.
										local reManager = maxOps.GetCurRenderElementMgr()
										if reManager != undefined do
										(
											if reManager.GetElementsActive() then 
											(
												local reCount = reManager.NumRenderElements()
												for i = 0 to reCount - 1 do
												(
													local theElement = reManager.GetRenderElement i
													if classof theElement != Missing_Render_Element_Plug_in AND theElement.enabled AND classof theElement != VRayOptionRE do
														append elementsToSkip theElement.elementName
												)
											)
										)--end if reManger undefined
									)
									else
									(
										--The elements are manually specified, so check the layers in the exr itself
										for i = 0 to fopenexr.numLayers() do
										(
											if (fopenexr.getLayerType i) == 1 then
												append elementsToSkip (fopenexr.getLayerName i)
										)
									)
								)
							)
							else
							(
								try(SMTD_MainRollout.Ui_report ("!!Skipping Embedded RE's as Render Output Filename is undefined."))catch()
								SMTDSettings.nonFatalErrorsCount+=1
							)
						)
						else
						(
							try(SMTD_MainRollout.Ui_report ("!!Skipping Embedded RE's as Render Output Save File is disabled."))catch()
							SMTDSettings.nonFatalErrorsCount+=1
						)
					)

					local reManager = maxOps.GetCurRenderElementMgr()
					if reManager != undefined do
					(
						if reManager.GetElementsActive() then
						(
							local reCount = reManager.NumRenderElements()
							for i = 0 to reCount - 1 do
							(
								local reObject = reManager.GetRenderElement i
								if classof reObject != Missing_Render_Element_Plug_in AND reObject.enabled AND classof reObject != VRayOptionRE then
								(
									if (findItem elementsToSkip reObject.elementName) == 0 do
									(
										
										local outputImageFilenames = #()
										local inputImageFilenames = #()										
										local theIndex = 0
										
										local reFilename = reManager.GetRenderElementFilename i
										if reFilename != undefined and reFilename != "" then
										(
											local theFile = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:true regionString:"" stereoCameraToken:stereoCameraLabel
											append outputImageFilenames theFile
											
											local theIndex = 0
											for aData in SMTDSettings.MultiRegionData where aData[1] == True do
											(
												for y = 1 to aData[7] do
												(
													for x = 1 to aData[6] do
													(
														local currTileString = "_region_" + theIndex as string + "_" 
														local theFile = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:currTileString stereoCameraToken:stereoCameraLabel
														append inputImageFilenames theFile
														theIndex += 1
													)--end x loop
												)--end y loop
											)--end region loop
											try(SMTD_MainRollout.Ui_report (">Submitting Draft Assembly Job For Multi-Frame, Multi-Regions ["+reObject.elementName+"] Render Element."))catch()
											
											local tileResult = SMTDFunctions.SubmitDraftTileAssemblerJob jobIdsString (theJobName + " ["+SingleLayerTilesCount as string+ " Animation Regions Draft Assembly - RE:"+ reObject.elementName+"]") outputImageFilenames SingleLayerTilesCount tileLefts tileBottoms inputImageFilenames framesList batchName:batchName
											local renderMsg = SMTDFunctions.getRenderMessage()				
											try(SMTD_MainRollout.Ui_report ((if tileResult then "+" else "--")+"Submission Result: \n\n" + renderMsg))catch()		
											if not tileResult do return false		
										)--is re path and name
										else
										(
											try(SMTD_MainRollout.Ui_report ("!!Skipping Draft Assembly Job Submission For MF, MR ["+reObject.elementName+"] Render Element as Filename is Empty."))catch()
											SMTDSettings.nonFatalErrorsCount+=1
										)
									)--skip?
								)--is re enabled?
							)--end re loop
						)--end RE Manager active
					)--end if reManager undefined
				)--end not vray output
				
				--SMTDSettings.RegionRendering = false
				SMTDSettings.JobName = theJobName								
							
				return true
			)--end  SMTDSettings.RegionRenderingMode == #animationMultiRegion

-------------------------------------------------------------------------					
--SINGLE-FRAME TILE OR MULTI-REGION RENDERING
-------------------------------------------------------------------------				
			
			if SMTDSettings.RegionRenderingMode == #singleFrameTiles or SMTDSettings.RegionRenderingMode == #singleFrameMultiRegion do
			(
				SMTDSettings.SingleTileJobLeft = ""
				SMTDSettings.SingleTileJobRight = ""
				SMTDSettings.SingleTileJobTop = ""
				SMTDSettings.SingleTileJobBottom = ""
				SMTDSettings.SingleTileJobFilename = ""
				SMTDSettings.SingleTileJobReFilename = ""

				SMTDSettings.SplitBufferFilename = ""
				SMTDSettings.RawBufferFilename = ""				
				
				local SingleTileJobReFilenameSS = "" as stringStream
				local reManager = maxOps.GetCurRenderElementMgr()
				local reObjects = #()

				local theRenderer = SMTDFunctions.getRendererObject()
				local theRendererID = SMTDFunctions.getRendererIdString()
				if reManager != undefined do
				(
					local reCount = reManager.NumRenderElements()
					reObjects = for i = 0 to reCount-1 collect
					(
						local reObject = reManager.GetRenderElement i
						local reFilename = try(reManager.GetRenderElementFilename i)catch("") 
						#(reObject, try(reObject.enabled)catch(false), reFilename) 
					)
				)--end if reManager undefined
				
				local tileLefts = #()
				local tileBottoms = #()

				local currentFrame = 0
				local currentFrameList = ""
				local customFrameList = ""

				--if #singleFrameTiles OR #singleFrameMultiRegion then inject currentTime.frame as the paddingString
				local paddingString = formattedPrint (currentTime.frame as integer) format:"04i"
				local paddingOutputString = formattedPrint (currentTime.frame as integer) format:"04i"
				--if RemovePadding then strip the output padding only. V-Ray will always add 0000 even for a single frame render, RAW & Split RE's
				if SMTDSettings.RemovePadding do paddingOutputString = ""
				--if RemovePadding then remove the delimiter only in NON V-Ray VFB Region/RegionRE output and then handle downstream DTA/TA jobs
				local delimiter = SMTDSettings.Delimiter
				if SMTDSettings.RemovePadding do delimiter = ""

-------------------------------------------------------------------------
--SINGLE FRAME, MULTI-REGION RENDERING
-------------------------------------------------------------------------
				if SMTDSettings.RegionRenderingMode == #singleFrameMultiRegion do
				(
					try(SMTD_MainRollout.Ui_report (">Single Frame Multi Region Data Preparation..."))catch()
					
					renderDimensions = SMTDFunctions.getRenderDimensions() --#(renderWidth,renderHeight,renderPixelAspect)

					local currentIndex = 0
					for aData in SMTDSettings.MultiRegionData where aData[1] == True do
					(
						for y = 1 to aData[7] do
						(
							for x = 1 to aData[6] do
							(
								theTileWidth = aData[4]/aData[6]
								theTileHeight = aData[5]/aData[7]
								tempLeft = (floor ((aData[2]+(theTileWidth*(x-1)))*renderDimensions[1])) as integer
								tempTop = (floor ((aData[3]+(theTileHeight*(y-1)))*renderDimensions[2])) as integer
								tempRight = (floor (((aData[2]+(theTileWidth*x))*renderDimensions[1])+0.5)) as integer
								tempBottom = (floor (((aData[3]+(theTileHeight*y))*renderDimensions[2])+0.5)) as integer

								append tileLefts tempLeft
								append tileBottoms (renderDimensions[2] - tempBottom)							
									
								SMTDSettings.SingleTileJobLeft = SMTDSettings.SingleTileJobLeft + "RegionLeft" + (currentIndex as string) + "=" + (tempLeft as string) + "\n"
								SMTDSettings.SingleTileJobTop = SMTDSettings.SingleTileJobTop + "RegionTop" + (currentIndex as string) + "=" + (tempTop as string) + "\n"
								SMTDSettings.SingleTileJobRight = SMTDSettings.SingleTileJobRight + "RegionRight" + (currentIndex as string) + "=" + (tempRight as string) + "\n"
								SMTDSettings.SingleTileJobBottom = SMTDSettings.SingleTileJobBottom + "RegionBottom" + (currentIndex as string) + "=" + (tempBottom as string) + "\n"						
									
								local tileString = "_region_" + (currentIndex) as string + "_"
								local regionFileName = SMTDFunctions.GetFormattedOutputFilename theOutput addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel
								SMTDSettings.SingleTileJobFilename = SMTDSettings.SingleTileJobFilename + "RegionFilename" + (currentIndex as string) + "=" + regionFileName + "\n"
								
								if (SMTDFunctions.getRendererIdString() == "vray") and renderers.current.output_on == true then
								(
									if renderers.current.output_splitgbuffer and renderers.current.output_splitfilename != undefined and renderers.current.output_useram then
									(
										SMTDSettings.SplitBufferFile = "SplitBufferFile="+(renderers.current.output_splitgbuffer as string)+"\n"
										local splitFileName = ""
										local splitName = renderers.current.output_splitfilename
										if(splitName != undefined and splitName != "") then
										(
											local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:false
											SMTDSettings.SplitBufferFilename += "SplitBufferFilename" + (currentIndex as string) + "=" + theFile+"\n"
										)
									)
									
									if renderers.current.output_saveRawFile and renderers.current.output_rawFileName != undefined then
									(
										SMTDSettings.RawBufferFile = "RawBufferFile="+(renderers.current.output_saveRawFile as string)+"\n"
										local rawName = renderers.current.output_rawFileName
										if(rawName != undefined and rawName != "") then
										(
											local theFile = SMTDFunctions.GetFormattedOutputFilename rawName addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:((isProperty renderers.current #fileName_addDot) and (getProperty renderers.current #fileName_addDot))
											SMTDSettings.RawBufferFilename = SMTDSettings.RawBufferFileName +"RawBufferFilename" + (currentIndex as string) + "=" + theFile+"\n"
										)
									)
								)
								
								-- If any render elements are specified, include them 
								local outputFilenameIndex = 0
								if reManager.GetElementsActive() then 
								(
									for anElement in reObjects where anElement[2] == true do
									(
										local reFilename = anElement[3]
										if reFilename != undefined and reFilename != "" do
										(
											local regionReFileName = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
											format "RegionReFilename%_%=%\n" currentIndex outputFilenameIndex regionReFileName to:SingleTileJobReFilenameSS
											outputFilenameIndex += 1
										)
									)
								)

								currentTile +=1
								if currentFrameList == "" then
									currentFrameList = (currentFrame as string)
								else
									currentFrameList = currentFrameList + "," + (currentFrame as string) 

								currentIndex += 1
							)--end x loop
						)--end y loop
					)--end i loop (active regions)
				)--end single frame multi-region rendering
				
-------------------------------------------------------------------------								
--SINGLE FRAME TILE RENDERING
-------------------------------------------------------------------------								
				if SMTDSettings.RegionRenderingMode == #singleFrameTiles do 
				(
					try(SMTD_MainRollout.Ui_report (">Single Frame Tiles Data Preparation..."))catch()

					renderDimensions = SMTDFunctions.getRenderDimensions() --#(renderWidth,renderHeight,renderPixelAspect)

					local rawName = ""
					local rawFileName = ""
					local splitFileName = ""
					local splitName = ""

					SMTDSettings.SplitBufferFilename = ""
					SMTDSettings.RawBufferFilename = ""

					if (SMTDFunctions.getRendererIdString() == "vray") then
					(
						splitName = renderers.current.output_splitfilename
						local splitFile = renderers.current.output_splitgbuffer
						
						if(splitFile) then
						(
							if(splitName == undefined or splitName == "") then
							(
								splitFile = false
							)
							else
							(
								SMTDSettings.SplitBufferFile = "SplitBufferFile="+(splitFile as string)+"\n" --True/False
							)
						)
						
						local rawFile = renderers.current.output_saveRawFile
						rawName = renderers.current.output_rawFileName
						
						if(rawFile) then
						(
							if(rawName == undefined or rawName == "") then
							(
								rawFile = false
							)
							else
							(
								SMTDSettings.RawBufferFile = "RawBufferFile="+(rawFile as string)+"\n" --True/False
							)
						)
					)
					
					for y = 1 to SMTDSettings.TilesInY do
					(
						for x = 1 to SMTDSettings.TilesInX do
						(
							--Remove this line to export all tiles
							--if not SMTDSettings.UseCustomTiles or findItem SMTDSettings.CustomTiles (Point2 x y) > 0 do
							(
								local tempRight = (DeltaX*x) as integer
								if x == SMTDSettings.TilesInX then
								(
									tempRight = renderDimensions[1]
									if SMTDSettings.TileBlowupMode then
									tempRight = (floor (1.0*(renderDimensions[1]/SMTDSettings.TilesInX))) as integer
								)

								local tempBottom = (DeltaY*y) as integer
								if y == SMTDSettings.TilesInY then
								(
									tempBottom = renderDimensions[2]
									if SMTDSettings.TileBlowupMode then
									tempBottom = (floor (1.0*(renderDimensions[2]/SMTDSettings.TilesInY))) as integer
								)

								local currentIndex = currentTile
								--if SMTDSettings.UseCustomTiles do currentIndex = currentFrame
								
								tempLeft = ((DeltaX*(x-1)) as integer)
								tempTop = ((DeltaY*(y-1)) as integer)
								
								append tileLefts tempLeft
								append tileBottoms (renderDimensions[2] - tempBottom)

								SMTDSettings.SingleTileJobLeft = SMTDSettings.SingleTileJobLeft + "RegionLeft" + (currentIndex as string) + "=" + (tempLeft as string) + "\n"
								SMTDSettings.SingleTileJobTop = SMTDSettings.SingleTileJobTop + "RegionTop" + (currentIndex as string) + "=" + (tempTop as string) + "\n"
								SMTDSettings.SingleTileJobRight = SMTDSettings.SingleTileJobRight + "RegionRight" + (currentIndex as string) + "=" + (tempRight as string) + "\n"
								SMTDSettings.SingleTileJobBottom = SMTDSettings.SingleTileJobBottom + "RegionBottom" + (currentIndex as string) + "=" + (tempBottom as string) + "\n"

								local tileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string  + "_"
								local regionFileName = SMTDFunctions.GetFormattedOutputFilename theOutput addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
								SMTDSettings.SingleTileJobFilename = SMTDSettings.SingleTileJobFilename + "RegionFilename" + (currentIndex as string) + "=" + regionFileName + "\n"

								-- If any render elements are specified, include them 
								local outputFilenameIndex = 0
								if reManager.GetElementsActive() then 
								(
									for anElement in reObjects where anElement[2] == true do
									(
										local reFilename = anElement[3]
										if reFilename != undefined and reFilename != "" do
										(
											local regionReFileName = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
											format "RegionReFilename%_%=%\n" currentIndex outputFilenameIndex regionReFileName to:SingleTileJobReFilenameSS
											outputFilenameIndex += 1
										)
									)
								)
								if (SMTDFunctions.getRendererIdString() == "vray" and renderers.current.output_on ) then
								(
									if renderers.current.output_splitgbuffer and renderers.current.output_useram then
									(
										local splitName = renderers.current.output_splitfilename
										if splitName != undefined and splitName != "" then 
										(
											local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:false
											SMTDSettings.SplitBufferFilename += "SplitBufferFilename" + (currentIndex as string) + "=" + theFile+"\n"
										)
									)									

									if renderers.current.output_saveRawFile then
									(
										local rawName = renderers.current.output_rawFileName
										if rawName != undefined and rawName != "" then
										(
											local theFile = SMTDFunctions.GetFormattedOutputFilename rawName addFramePadding:false regionString:tileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:((isProperty renderers.current #fileName_addDot) and (getProperty renderers.current #fileName_addDot))
											SMTDSettings.RawBufferFilename += "RawBufferFilename" + (currentIndex as string) + "=" + theFile +"\n"
										)
									)
								)
									
								currentTile +=1
								if currentFrameList == "" then
									currentFrameList = (currentFrame as string)
								else
									currentFrameList += "," + (currentFrame as string) 
								
								--Collect the custom tile indices
								if SMTDSettings.UseCustomTiles AND findItem SMTDSettings.CustomTiles (Point2 x y) > 0 do
								(
									if customFrameList == "" then
										customFrameList = currentFrame as string
									else
										customFrameList += "," + (currentFrame as string) 
								)								
							)
							currentFrame += 1
						)--end x loop
					)--end y loop
				)--end single frame tiles

--Dependent Job is needed if:
--Single Frame Tile Rendering and SingleTileJobDependent is checked
--Multi-Region Rendering is requested, regardless of whether Single or Multiple Frames

				local tilesRendering = findItem #(#singleFrameTiles) SMTDSettings.RegionRenderingMode > 0
				local multiRegionRendering = findItem #(#singleFrameMultiRegion, #animationMultiRegion) SMTDSettings.RegionRenderingMode > 0
				
				local AssemblyMode = #none
				if (SMTDSettings.SingleTileJobDependent OR MultiRegionRendering) do AssemblyMode = #draft
			
				SMTDSettings.SingleTileJobReFilename = SingleTileJobReFilenameSS as string
				
				SMTDSettings.SingleTileJobTileCount = currentTile
				
				SMTDSettings.SingleTileJobFrameList = ""
				--Use the customFrameList indices to enable the tasks that should be uncompleted:
				if SMTDSettings.UseCustomTiles do SMTDSettings.SingleTileJobFrameList = customFrameList
				
				SMTDFunctions.createSubmissionFolderAndUpdatePaths()
				SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile batchName:batchName stereoCameraLabel:stereoCameraLabel
				SMTDFunctions.CreateJobInfoFile SMTDPaths.JobInfoFile forceCamera:forceCamera stereoCameraLabel:stereoCameraLabel
				
				local initialArgs = "" as stringStream
				format "-outputfiles\n%\n%\n" SMTDPaths.SubmitOutput  SMTDPaths.SubmitExitCode to:initialArgs
				
				if SMTDSettings.bgSubmission do format "-background\n-notify\n" to:initialArgs 
				if SMTDSettings.dropSubmission do format "-drop\n" to:initialArgs 
				
				if( SMTDSettings.SubmitSceneMode == #reposave ) then
					format "%\n%\n%\n" SMTDPaths.SubmitInfoFile SMTDPaths.JobInfoFile TempMaxFile to:initialArgs 
				else
					format "%\n%\n" SMTDPaths.SubmitInfoFile SMTDPaths.JobInfoFile to:initialArgs 
				 
				if SMTDSettings.CopyVbscriptFile do format "%\n" SMTDPaths.ImsqVbscriptFile to:initialArgs
				if SMTDSettings.RunPreLoadScript do format "%\n" SMTDSettings.PreLoadScriptFile to:initialArgs
				if SMTDSettings.RunPostLoadScript do format "%\n" SMTDSettings.PostLoadScriptFile to:initialArgs
				if SMTDSettings.RunPreFrameScript do format "%\n" SMTDSettings.PreFrameScriptFile to:initialArgs
				if SMTDSettings.RunPostFrameScript do format "%\n" SMTDSettings.PostFrameScriptFile to:initialArgs
				if SMTDSettings.SubmitSceneMode == #reposave do
				(
					if SMTDSettings.UsePathConfigFile and doesFileExist SMTDSettings.PathConfigFile do format "%\n" SMTDSettings.PathConfigFile to:initialArgs
				)

				--Output external files to the command line for copying
				if SMTDSettings.SubmitExternalFilesMode > 1 do				
					for aBitmap in BitmapsCopyData where findItem SMTDSettings.MissingFiles aBitmap[2] == 0 do
						format "%\n" aBitmap[2] to:initialArgs
					
				local initialArgsFileName = (getFileNamePath SMTDPaths.JobInfoFile + "initialArgsFile.txt") 
				local initialArgsFile = createFile initialArgsFileName encoding:#utf8 writeBOM:true
				format "%\n" (initialArgs as string) to:initialArgsFile
				close initialArgsFile 
				initialArgsFileName = "\""+initialArgsFileName+"\""
				
				retcode = SMTDFunctions.waitForCommandToComplete initialArgsFileName SMTDSettings.TimeoutSubmission paramIsFile:true dontWait:SMTDSettings.UseSubmissionQueue
				
				if not SMTDSettings.UseSubmissionQueue do
				(
					local renderMsg = SMTDFunctions.getRenderMessage()				
					try(SMTD_MainRollout.Ui_report ((if retcode == #success then "+" else "--")+"Submission Result: \n\n" + renderMsg))catch()		
				)
				
				if retcode == #success or retcode == #queued then
				(
					SMTDFunctions.getJobIDFromMessage renderMsg
					if not SMTDSettings.UseSubmissionQueue do SMTDFunctions.SubmitTransferJob() -- submits a remote transfer job if necessary
------------------------------------------------------------
-- SINGLE FRAME - MULTI-REGION OR TILES
-- SUBMIT DEPENDENT JOB HERE
------------------------------------------------------------
					if AssemblyMode == #draft  then
					(
						local jobId = SMTDSettings.DeadlineSubmissionLastJobID
						local jobName = SMTDSettings.JobName 
						if SMTDSettings.StateSetsSubmit and SMTDSettings.StateSetRenameOutput do jobName += (" [STATE SET '"+ SMTDSettings.StateSetName + "']")
						jobName += " - Draft Tile Assembly"

						local outputImageFilenames = #()
						local inputImageFilenames = #()
						local fileCount = 0

						local theFile = SMTDFunctions.GetFormattedOutputFilename theOutput addFramePadding:true regionString:"" stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
						append outputImageFilenames theFile

						if MultiRegionRendering then
						(
							local theIndex = 0
							for aData2 in SMTDSettings.MultiRegionData where aData2[1] == True do
							(
								for y = 1 to aData2[7] do
								(
									for x = 1 to aData2[6] do
									(
										local currTileString = "_region_" + theIndex as string + "_" 
										local theFile = SMTDFunctions.GetFormattedOutputFilename theOutput addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
										append inputImageFilenames theFile
										theIndex += 1
									)
								)
							)
						)--end multi-region rendering
						else
						(
							for y = 1 to SMTDSettings.TilesInY do
							(
								for x = 1 to SMTDSettings.TilesInX do
								(
									fileCount +=1
									local currTileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string+"_"
									local theFile = SMTDFunctions.GetFormattedOutputFilename theOutput addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
									append inputImageFilenames theFile
								)
							)
						)
						local SingleLayerTilesCount = inputImageFilenames.count --this is the number of tiles before RE are considered!
						
						if not rendSaveFile or rendOutputFilename == undefined or rendOutputFilename == "" do
						(
							inputImageFilenames = #()
							outputImageFilenames = #()
						)
						-- If any render elements are specified, include them 
						elementsToSkip = #()
						
						-- If rendering with VRay frame buffer, then we don't want to assemble the render elements because they
						-- are embedded in the main image.
						if (SMTDFunctions.getRendererIdString() == "vray" and renderers.current.output_on) then
						(
							if renderers.current.output_saveRawFile and  renderers.current.output_rawFileName != undefined and renderers.current.output_rawFileName != "" then
							(
								local rawName = renderers.current.output_rawFileName
								local rawOutputType = (getFilenameType rawName)
								if not matchPattern rawOutputType pattern:"*vrimg*" do --Draft does not support the assembling of vrimg files
								(
									local theFile = SMTDFunctions.GetFormattedOutputFilename rawName addFramePadding:true regionString:"" stereoCameraToken:stereoCameraLabel addFrameDelimiter:((isProperty renderers.current #fileName_addDot) and (getProperty renderers.current #fileName_addDot))
									
									append outputImageFilenames theFile

									if MultiRegionRendering then
									(
										local theIndex = 0
										for aData2 in SMTDSettings.MultiRegionData where aData2[1] == True do
										(
											for y = 1 to aData2[7] do
											(
												for x = 1 to aData2[6] do
												(
													local currTileString = "_region_" + theIndex as string + "_" 
													local theFile = SMTDFunctions.GetFormattedOutputFilename rawName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:((isProperty renderers.current #fileName_addDot) and (getProperty renderers.current #fileName_addDot))
													append inputImageFilenames theFile
													theIndex += 1
												)
											)
										)														
									)		
									else	
									(													
										for y = 1 to SMTDSettings.TilesInY do
										(
											for x = 1 to SMTDSettings.TilesInX do
											(
												local currTileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string + "_"
												local theFile = SMTDFunctions.GetFormattedOutputFilename rawName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:((isProperty renderers.current #fileName_addDot) and (getProperty renderers.current #fileName_addDot))
												append inputImageFilenames theFile
											)
										)
									)
								)--end if not vrimg
							)--if rawfile defined

							if renderers.current.output_splitgbuffer and renderers.current.output_splitfilename != undefined and renderers.current.output_splitfilename != "" and renderers.current.output_useram then
							(
								local replaceHashes = false
								try( replaceHashes = renderers.current.output_expandFrameNumber )catch()
								
								if renderers.current.output_splitRGB then
								(
									--Update VFB Split Channels FilePath
									local splitName = SMTDFunctions.ReturnVraySplitPath renderers.current.output_splitfilename elementType:"RGB_color"
									local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:".RGB_color" stereoCameraToken:stereoCameraLabel addFrameDelimiter:true replaceHashesWithFramePadding:replaceHashes
									
									append outputImageFilenames theFile
									--try(SMTD_MainRollout.Ui_report (">Split RGB Output Filename ["+theFile+"]"))catch()
									if MultiRegionRendering then
									(
										local theIndex = 0
										for aData2 in SMTDSettings.MultiRegionData where aData2[1] == True do
										(
											for y = 1 to aData2[7] do
											(
												for x = 1 to aData2[6] do
												(
													local currTileString = "_region_" + theIndex as string + "_" + ".RGB_color."
													local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
													append inputImageFilenames theFile
													--try(SMTD_MainRollout.Ui_report (">Multi-Region Draft Assembler Split RGB Input Filename ["+theFile+"]"))catch()
													theIndex += 1
												)
											)
										)														
									)		
									else	
									(													
										for y = 1 to SMTDSettings.TilesInY do
										(
											for x = 1 to SMTDSettings.TilesInX do
											(
												local currTileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string + "_" + ".RGB_color."
												local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
												append inputImageFilenames theFile
												--try(SMTD_MainRollout.Ui_report (">Draft Tile Assembler Split RGB Input Filename ["+theFile+"]"))catch()
											)
										)
									)
								)
								
								if renderers.current.output_splitAlpha then
								(
									--Update VFB Split Channels FilePath
									local splitName = SMTDFunctions.ReturnVraySplitPath renderers.current.output_splitfilename elementType:"Alpha"
									local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:".Alpha" stereoCameraToken:stereoCameraLabel addFrameDelimiter:true replaceHashesWithFramePadding:replaceHashes
									append outputImageFilenames theFile
									--try(SMTD_MainRollout.Ui_report (">Split Alpha Output Filename ["+theFile+"]"))catch()
									if MultiRegionRendering then
									(
										local theIndex = 0
										for aData2 in SMTDSettings.MultiRegionData where aData2[1] == True do
										(
											for y = 1 to aData2[7] do
											(
												for x = 1 to aData2[6] do
												(
													local currTileString = "_region_" + theIndex as string + "_" + ".Alpha."
													local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
													append inputImageFilenames theFile
													--try(SMTD_MainRollout.Ui_report (">Multi-Region Draft Assembler Split Alpha Input Filename ["+theFile+"]"))catch()
													theIndex += 1
												)
											)
										)														
									)		
									else --tile rendering
									(													
										for y = 1 to SMTDSettings.TilesInY do
										(
											for x = 1 to SMTDSettings.TilesInX do
											(
												local currTileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string + "_" + ".Alpha."
												local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:false replaceHashesWithFramePadding:replaceHashes
												append inputImageFilenames theFile
												--try(SMTD_MainRollout.Ui_report (">Draft Tile Assembler Split Alpha Input Filename ["+theFile+"]"))catch()
											)
										)
									)
								)
								
								local reManager = maxOps.GetCurRenderElementMgr()
								if reManager != undefined do
								(
									if reManager.GetElementsActive() then 
									(
										local reCount = reManager.NumRenderElements()
										for i = 0 to reCount - 1 do
										(
											local reObject = reManager.GetRenderElement i
											if classof reObject != Missing_Render_Element_Plug_in AND reObject.enabled AND classof reObject != VRayOptionRE AND classof reObject != VRayAlpha then
											(
												local splitName = reManager.GetRenderElementFilename i
												local reArtifactSuffixes = SMTDFunctions.RenderElementArtifactSuffixes(reObject)
												for reArtifactSuffix in reArtifactSuffixes do
												(
													--Re-define splitName to include any SMTD pathing options specific for VFB RE Split Channels
													local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:("."+reArtifactSuffix) stereoCameraToken:stereoCameraLabel addFrameDelimiter:true replaceHashesWithFramePadding:replaceHashes

													append outputImageFilenames theFile
													--try(SMTD_MainRollout.Ui_report (">Render Element Output Filename ["+theFile+"]"))catch()

													if MultiRegionRendering then
													(
														local theIndex = 0
														for aData2 in SMTDSettings.MultiRegionData where aData2[1] == True do
														(
															for y = 1 to aData2[7] do
															(
																for x = 1 to aData2[6] do
																(
																	local currTileString = "_region_" + theIndex as string + "_" + "." + reArtifactSuffix
																	local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true replaceHashesWithFramePadding:replaceHashes
																	append inputImageFilenames theFile
																	--try(SMTD_MainRollout.Ui_report (">Multi-Region Draft Assembler Render Element Input Filename ["+theFile+"]"))catch()
																	theIndex += 1
																)
															)
														)
													)
													else
													(
														for y = 1 to SMTDSettings.TilesInY do
														(
															for x = 1 to SMTDSettings.TilesInX do
															(
																local currTileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string + "_"	+ "." + reArtifactSuffix
																local theFile = SMTDFunctions.GetFormattedOutputFilename splitName addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true replaceHashesWithFramePadding:replaceHashes
																append inputImageFilenames theFile
																--try(SMTD_MainRollout.Ui_report (">Draft Tile Assembler Render Element Input Filename ["+theFile+"]"))catch()
															)
														)
													)
												)
											)--is re enabled?
										)--end re loop
									)--end Render Elements Active
								)--end if reManager undefined
							)--if splitfile defined
						)--end if VFB enabled
						else
						(
							-- If this is 3dsmax 2011 or later, check to see if we're rendering to the new exr format
							if ((maxVersion())[1]/1000 as integer) >= 13 do
							(
								if rendSaveFile then
								(
									if rendOutputFilename != undefined and rendOutputFilename != "" then
									(
										rend_type = getFileNameType rendOutputFilename
										is_exr = matchPattern rend_type pattern:".exr" ignoreCase:true
										is_fxr = matchPattern rend_type pattern:".fxr" ignoreCase:true
										
										-- If we are, we need to tell Deadline which render elements are to be embedded in the exr file so that it doesn't save them separately
										if (is_exr or is_fxr) and (fopenexr != undefined) do
										(
											if fopenexr.isAutoAddRenderElements() then
											(
												--The elements are being added automatically, so check the re manager.
												local reManager = maxOps.GetCurRenderElementMgr()
												if reManager != undefined do
												(
													if reManager.GetElementsActive() then 
													(
														local reCount = reManager.NumRenderElements()
														for i = 0 to reCount - 1 do
														(
															local theElement = reManager.GetRenderElement i
															if classof theElement != Missing_Render_Element_Plug_in AND theElement.enabled AND classof theElement != VRayOptionRE do
																append elementsToSkip theElement.elementName
														)
													)
												)--end if reManager undefined
											)
											else
											(
												--The elements are manually specified, so check the layers in the exr itself
												for i = 0 to fopenexr.numLayers() do
												(
													if (fopenexr.getLayerType i) == 1 then
														append elementsToSkip (fopenexr.getLayerName i)
												)
											)
										)
									)
									else
									(
										try(SMTD_MainRollout.Ui_report ("!!Skipping Embedded RE's as Render Output Filename is undefined."))catch()
										SMTDSettings.nonFatalErrorsCount+=1
									)
								)
								else
								(
									try(SMTD_MainRollout.Ui_report ("!!Skipping Embedded RE's as Render Output Save File is disabled."))catch()
									SMTDSettings.nonFatalErrorsCount+=1
								)
							)

							-- RENDER ELEMENTS
							local reManager = maxOps.GetCurRenderElementMgr()
							if reManager != undefined do
							(
								if reManager.GetElementsActive() then 
								(
									local reCount = reManager.NumRenderElements()
									for i = 0 to reCount - 1 do
									(
										local reObject = reManager.GetRenderElement i
										if classof reObject != Missing_Render_Element_Plug_in AND reObject.enabled AND classof reObject != VRayOptionRE then
										(
											if (findItem elementsToSkip reObject.elementName) == 0 do
											(
												local reFilename = reManager.GetRenderElementFilename i
												try(SMTD_MainRollout.Ui_report (">Render Element "+reObject.elementName + " Original Filename ["+reFilename+"]"))catch()
												if reFilename != undefined and reFilename != "" then
												(
													local theFile = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:true regionString:"" stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
													append outputImageFilenames theFile
													try(SMTD_MainRollout.Ui_report (">Render Element Output Filename ["+theFile+"]"))catch()
													
													if MultiRegionRendering then
													(
														local theIndex = 0
														for aData2 in SMTDSettings.MultiRegionData where aData2[1] == True do
														(
															for y = 1 to aData2[7] do
															(
																for x = 1 to aData2[6] do
																(
																	local currTileString = "_region_" + theIndex as string + "_"
																	local theFile = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
																	append inputImageFilenames theFile
																	theIndex += 1
																)
															)
														)														
													)		
													else	
													(													
														for y = 1 to SMTDSettings.TilesInY do
														(
															for x = 1 to SMTDSettings.TilesInX do
															(
																local currTileString = "_tile_" + x as string + "x" + y as string + "_" + SMTDSettings.TilesInX as string + "x" + SMTDSettings.TilesInY as string + "_"
																local theFile = SMTDFunctions.GetFormattedOutputFilename reFilename addFramePadding:true regionString:currTileString stereoCameraToken:stereoCameraLabel addFrameDelimiter:true
																append inputImageFilenames theFile
															)
														)
													)

												)--is re path and name 
											)--skip?
										)--is re enabled?
									)--end re loop
								)--end Render Elements Active
							)--end if reManager undefined
						)--end new EXR format
						
						if MultiRegionRendering then
						(					
							tileCount = SingleLayerTilesCount 		
						)
						else
						(
							tileCount = fileCount
						)

						try(SMTD_MainRollout.Ui_report (">Submitting Draft Assembly Job."))catch()
						local framesList = #(currentTime.frame as integer)
						local tileResult = SMTDFunctions.SubmitDraftTileAssemblerJob jobId jobName outputImageFilenames tileCount tileLefts tileBottoms inputImageFilenames framesList batchName:batchName replaceHashes:replaceHashes
						if not tileResult then
							return false

					)--end single tile job dependent
				)--end success
				else
					return false
				
				return true
			)--end single frame
			true
		),
		
		fn getTimeStampString =
		(
			local theTime = getLocalTime()
			deleteItem theTime 3
			local txt = ""
			for i = 1 to 6 do 
			(	
				txt+=theTime[i] as string
				if i < 6 do txt+= "_"
				if i == 3 do txt+= "_"
				if( i == 2 or i == 3) and theTime[i] < 10 do txt+= "0"
			)
			txt
		),
		
		fn SubmitDraftTileAssemblerJob jobId jobName outputImageFilenames tileCount tileLefts tileBottoms inputImageFilenames FramesList batchName:"" replaceHashes:false =
		(
			if outputImageFilenames.count == 0 do --no tiles are being created
			(
				SMTDSettings.FatalErrorsCount += 1
				try(SMTD_MainRollout.Ui_report ("--Failed Draft Assembly Job Submission as NO Output Image Filenames declared!"))catch()
				return false
			)

			local formattedJobName = (SMTDFunctions.FormatJobName jobName)
			local formattedComment = "Draft Assembler Dependent Job Submission from 3ds Max"
			
			local tilesRendering = findItem #(#singleFrameTiles) SMTDSettings.RegionRenderingMode > 0
			local multiRegionRendering = findItem #(#singleFrameMultiRegion, #animationMultiRegion) SMTDSettings.RegionRenderingMode > 0
			
			SMTDFunctions.createSubmissionFolderAndUpdatePaths()
			
			local tileJobInfoFile = CreateFile SMTDPaths.SubmitInfoFile encoding:#utf8 writeBOM:true
			if (tileJobInfoFile != undefined) then
			(
				format "Plugin=DraftTileAssembler\n" to:tileJobInfoFile
				format "Name=%\n" formattedJobName to:tileJobInfoFile
				format "BatchName=%\n" batchName to:tileJobInfoFile
				format "UserName=%\n" SMTDSettings.UserName to:tileJobInfoFile
				format "Comment=%\n" formattedComment to:tileJobInfoFile
				format "Department=%\n" SMTDSettings.Department to:tileJobInfoFile

				if not SMTDSettings.AssemblerOverride then
				(
					format "Priority=%\n" SMTDSettings.Priority to:tileJobInfoFile
					format "Pool=%\n" SMTDSettings.PoolName to:tileJobInfoFile
					if SMTDSettings.Pool2Name != "" do
						format "SecondaryPool=%\n" SMTDSettings.Pool2Name to:tileJobInfoFile
					format "Group=%\n" SMTDSettings.Group to:tileJobInfoFile
				)
				else
				(
					format "Priority=%\n" SMTDSettings.AssemblerPriority to:tileJobInfoFile
					format "Pool=%\n" SMTDSettings.AssemblerPoolName to:tileJobInfoFile
					if SMTDSettings.AssemblerPool2Name != "" do
						format "SecondaryPool=%\n" SMTDSettings.AssemblerPool2Name to:tileJobInfoFile
					format "Group=%\n" SMTDSettings.AssemblerGroup to:tileJobInfoFile
				)

				format "OnJobComplete=%\n" SMTDSettings.OnComplete to:tileJobInfoFile
				
				if not SMTDSettings.UseSubmissionQueue do
					format "JobDependencies=%\n" jobId to:tileJobInfoFile
				
				
				format "ResumeOnDeletedDependencies=%\n" SMTDSettings.ResumeOnDeletedDependencies to:tileJobInfoFile
				if findItem #(#singleFrameMultiRegion, #singleFrameTiles) SMTDSettings.RegionRenderingMode == 0 then --not single frame region, do frame dependent assembly
				(
					format "IsFrameDependent=1\n" to:tileJobInfoFile
					local FramesListString = "" as stringStream
					for f in FramesList do format "%," f to:FramesListString
					FramesListString = FramesListString as string
					FramesListString = substring FramesListString 1 (FramesListString.count-1)
					format "Frames=%\n" FramesListString to:tileJobInfoFile
				)
				else
					format "Frames=0-%\n" ((outputImageFilenames.count*FramesList.count)-1) to:tileJobInfoFile --output as many tasks as there are aux files times the number of frames,

				/*
				if FramesList.count > 1 then
				(
					local theFramesString = "" as stringStream
					for f in FramesList do format "%," f to:theFramesString
				)
				else
				(
					format "Frames=1-%\n" outputImageFilenames.count to:tileJobInfoFile
				)
				*/

				format "ChunkSize=1\n" to:tileJobInfoFile
				--format "MachineLimit=1\n" to:tileJobInfoFile

				for i = 1 to outputImageFilenames.count do
					format "OutputFilename%=%\n" (i-1) outputImageFilenames[i] to:tileJobInfoFile


				format "ExtraInfo0=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo0) to:tileJobInfoFile
				format "ExtraInfo1=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo1) to:tileJobInfoFile
				format "ExtraInfo2=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo2) to:tileJobInfoFile
				format "ExtraInfo3=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo3) to:tileJobInfoFile
				format "ExtraInfo4=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo4) to:tileJobInfoFile
				format "ExtraInfo5=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo5) to:tileJobInfoFile
				format "ExtraInfo6=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo6) to:tileJobInfoFile
				format "ExtraInfo7=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo7) to:tileJobInfoFile
				format "ExtraInfo8=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo8) to:tileJobInfoFile
				format "ExtraInfo9=%\n" (SMTDFunctions.FormatExtraInfo SMTDSettings.ExtraInfo9) to:tileJobInfoFile
				
				Close tileJobInfoFile
				SMTDFunctions.ConcatenatePipelineSettingsToJob SMTDPaths.SubmitInfoFile batchName
			)
			else
				return false

			local tileJobPluginFile = CreateFile SMTDPaths.JobInfoFile encoding:#utf8 writeBOM:true
			if (tileJobPluginFile != undefined) then
			(
				format "CleanupTiles=%\n" SMTDSettings.SingleTileJobCleanup to:tileJobPluginFile
				format "ErrorOnMissing=%\n" SMTDSettings.SingleTileJobDraftErrorOnMissing to:tileJobPluginFile
				format "MultipleConfigFiles=true\n" to:tileJobPluginFile
				if SMTDSettings.MultiRegionBackground == #previous or SMTDSettings.RegionRenderingMode == #singleFrameTiles do
				(
					format "ErrorOnMissingBackground=False\n" to:tileJobPluginFile
				)
				Close tileJobPluginFile
			)
			else
				return false

			local tileArgs = "" as stringstream
			format "-outputfiles\n%\n%\n" SMTDPaths.SubmitOutput  SMTDPaths.SubmitExitCode to:tileArgs						
			if SMTDSettings.bgSubmission do format "-background\n -notify\n" to:tileArgs 
			if SMTDSettings.dropSubmission do format "-drop\n" to:tileArgs 
			format "%\n"	SMTDPaths.SubmitInfoFile to:tileArgs 
			format "%\n"	SMTDPaths.JobInfoFile to:tileArgs 
			
			local theLeftsBottomsCounter = 0
			local dateString = SMTDFunctions.getTimeStampString()
			for f in FramesList do
			(
				for i = 0 to (outputImageFilenames.count-1) do
				(
					local currentDraftFileName = substituteString (getFileNameFile outputImageFilenames[i+1]) "####" ""
					currentDraftFileName += "_"+i as string+"_config_"+ dateString + "_" + (formattedPrint f format:"04i") + getFileNameType SMTDPaths.DraftConfigFile
					local remoteConfigFileName = (getFileNamePath outputImageFilenames[i+1] + currentDraftFileName)
					local currConfigFileName = (getFileNamePath SMTDPaths.SubmitInfoFile + currentDraftFileName)
					
					format "%\n"	currConfigFileName to:tileArgs 
					local draftConfigFile = "" as stringStream --write the file in memory, then dump at once via DotNet
					if (draftConfigFile != undefined) then
					(
						format "\n" to:draftConfigFile

						if (SMTDSettings.RemovePadding and rendTimeType == 1) then
							format "ImageFileName=%\n" outputImageFilenames[i+1] to:draftConfigFile
						else if replaceHashes == true then
							format "ImageFileName=%\n" (SMTDFunctions.replaceAllHashesWithFrameNumber outputImageFilenames[i+1] f) to:draftConfigFile
						else
							format "ImageFileName=%\n" (SMTDFunctions.replaceFrameNumber outputImageFilenames[i+1] f) to:draftConfigFile

						case SMTDSettings.MultiRegionBackground of
						(
							#previous:
							(
								if (SMTDSettings.RemovePadding and rendTimeType == 1) then
									format "BackgroundSource=%\n" outputImageFilenames[i+1] to:draftConfigFile
								else if replaceHashes == true then
									format "BackgroundSource=%\n" (SMTDFunctions.replaceAllHashesWithFrameNumber outputImageFilenames[i+1] f) to:draftConfigFile
								else
									format "BackgroundSource=%\n" (SMTDFunctions.replaceFrameNumber outputImageFilenames[i+1] f) to:draftConfigFile
							)
							#single: --only output custom background for Beauty pass
							(
								if i == 0 do format "BackgroundSource=%\n" SMTDSettings.MultiRegionBackgroundImage to:draftConfigFile
							)
							#sequence: --only output custom background for Beauty pass
							(
								if i == 0 do
								(
									if replaceHashes == true then
										format "BackgroundSource=%\n" (SMTDFunctions.replaceAllHashesWithFrameNumber SMTDSettings.MultiRegionBackgroundImage f) to:draftConfigFile
									else
										format "BackgroundSource=%\n" (SMTDFunctions.replaceFrameNumber SMTDSettings.MultiRegionBackgroundImage f) to:draftConfigFile
								)
							)
						)

						format "TileCount=%\n" tileCount to:draftConfigFile
						format "TilesCropped=True\n" to:draftConfigFile
						format "DistanceAsPixels=True\n" to:draftConfigFile

						renderDimensions = SMTDFunctions.getRenderDimensions() --#(renderWidth,renderHeight,renderPixelAspect)

						format "ImageWidth=%\n" renderDimensions[1] to:draftConfigFile
						format "ImageHeight=%\n" renderDimensions[2] to:draftConfigFile

						if MultiRegionRendering then
						(
							local theIndex = 0
							for aData in SMTDSettings.MultiRegionData where aData[1] == True do
							(
								for y = 1 to aData[7] do
								(
									for x = 1 to aData[6] do
									(
										try(windows.processPostedMessages())catch()
										theLeftsBottomsCounter+=1

										if (SMTDSettings.RemovePadding and rendTimeType == 1) then
											format "Tile%FileName=%\n" theIndex inputImageFilenames[(i * tileCount)+theIndex+1] to:draftConfigFile
										else if replaceHashes == true then
											format "Tile%FileName=%\n" theIndex (SMTDFunctions.replaceAllHashesWithFrameNumber inputImageFilenames[(i * tileCount)+theIndex+1] f) to:draftConfigFile
										else
											format "Tile%FileName=%\n" theIndex (SMTDFunctions.replaceFrameNumber inputImageFilenames[(i * tileCount)+theIndex+1] f) to:draftConfigFile

										local theAnimRegionValue = SMTDFunctions.interpolateAnimatedRegion aData f
										local theTileWidth = theAnimRegionValue[4]/aData[6]
										local theTileHeight = theAnimRegionValue[5]/aData[7]
										local corner1X = ((floor ((theAnimRegionValue[2]+(theTileWidth*(x-1)))*renderDimensions[1])) as integer)
										local corner2Y = renderDimensions[2] - ((floor (((theAnimRegionValue[3]+(theTileHeight*y))*renderDimensions[2])+0.5)) as integer)

										format "Tile%X=%\n" theIndex corner1X to:draftConfigFile
										format "Tile%Y=%\n" theIndex corner2Y to:draftConfigFile
										theIndex += 1	
									)
								)
							)
						)
						else
						(
							for j = 0 to tileCount-1 do
							(
								if (SMTDSettings.RemovePadding and rendTimeType == 1) then
									format "Tile%FileName=%\n" j inputImageFilenames[(i * tileCount) + j + 1] to:draftConfigFile
								else if replaceHashes == true then
									format "Tile%FileName=%\n" j (SMTDFunctions.replaceAllHashesWithFrameNumber inputImageFilenames[(i * tileCount) + j + 1] f) to:draftConfigFile
								else
									format "Tile%FileName=%\n" j (SMTDFunctions.replaceFrameNumber inputImageFilenames[(i * tileCount) + j + 1] f) to:draftConfigFile

								format "Tile%X=%\n" j tileLefts[j+1] to:draftConfigFile
								format "Tile%Y=%\n" j tileBottoms[j+1] to:draftConfigFile
							)
						)
						(dotNetClass "System.IO.File").WriteAllText currConfigFileName (draftConfigFile as string)
						--Close draftConfigFile
						if SMTDSettings.MultiRegionCopyDraftConfig == true do 
							copyFile currConfigFileName remoteConfigFileName 
					)
					else
						return false
				)--outputfile loop
			)--end frame loop	
			
			local initialArgsFileName = (getFileNamePath SMTDPaths.JobInfoFile + "initialArgsFile.txt") 
			(dotNetClass "System.IO.File").WriteAllText initialArgsFileName (tileArgs as string)
			
			retcode = SMTDFunctions.waitForCommandToComplete ("\"" + initialArgsFileName+"\"") SMTDSettings.TimeoutSubmission paramIsFile:true dontWait:SMTDSettings.UseSubmissionQueue 
			try(SMTD_MainRollout.Ui_report (">Draft Assembly Job Submission Returned " + retcode as string))catch()
			if retcode != #success and retcode != #queued then
				return false
			
			true
		),
		
		--SUBMIT BATCH JOBS LOCALLY
		fn spawnBatchJobsLocal = 
		(
			SMTDSettings.UseBatchRender = false --before spawning new jobs, make sure they don't become batch masters
			
			local batchName = SMTDFunctions.getBatchName()

			renderDimensions = SMTDFunctions.getRenderDimensions() --#(renderWidth,renderHeight,renderPixelAspect)

			local def_RenderWidth = renderDimensions[1]
			local def_RenderHeight = renderDimensions[2]
			local def_RenderPixelAspect = renderDimensions[3]
			local def_Camera = viewport.getCamera()
			local def_rendOutputFileName = rendOutputFileName 
			local def_rendSaveFile = rendSaveFile
			local def_rendTimeType = rendTimeType 
			local def_rendStart = rendStart
			local def_rendEnd = rendEnd
			
			local theJobName = SMTDSettings.JobName
			local currentJob = 0
			local numViews = batchRenderMgr.numViews 
			local views = (for i = 1 to numViews collect (batchRenderMgr.getView i))
			local numberOfBatchJobs =  (for i = 1 to numViews where (batchRenderMgr.getView i).enabled collect i).count
			
			local needMaxReload = false
			--local theNetworkPath = SMTDPaths.MainSubmissionDir + "\\"

			SMTDFunctions.createSubmissionFolderAndUpdatePaths()
			local originalPath = SMTDPaths.RestoreTempMaxFile
			local originalFolder = SMTDPaths.submitSubFolder
			try(SMTD_MainRollout.Ui_report ("Backup Scene Path: [" + originalPath + "]"))catch()
			if (result = SMTDFunctions.SaveMaxFileCopy originalPath useMaxHold:false) != undefined do
			(
				try(SMTD_MainRollout.Ui_report ("SAVING BACKUP FILE:\n" + result))catch()
				SMTDSettings.UseBatchRender = true	
				return false
			)
			
			renderSceneDialog.close()
			for i = 1 to numViews do
			(
				try(SMTD_MainRollout.Ui_report (">Processing View "+i as string + " of " + numViews as string))catch()
				local theView = views[i]
				if theView.enabled then 
				(
					if needMaxReload then
					(
						try(SMTD_MainRollout.Ui_report (">Reloading original scene..."))catch()
						SMTDFunctions.RestoreMaxFileCopy originalPath
						needMaxReload = false
					)	
					else
					(
						RenderWidth = def_RenderWidth 
						RenderHeight = def_RenderHeight 
						RenderPixelAspect = def_RenderPixelAspect 
						if (def_Camera != undefined) and (IsValidNode def_Camera) do viewport.setCamera def_Camera
						rendOutputFileName = def_rendOutputFileName 
						rendSaveFile = def_rendSaveFile
						rendTimeType = def_rendTimeType 
						rendStart = def_rendStart 
						rendEnd = def_rendEnd 
					)
					
					if theView.outputFilename == "" and rendOutputFilename == "" do 
					(
						try(SMTD_MainRollout.Ui_report ("--View Definition ["+ theView.name +"] has NO Output File Name - Skipping..."))catch()
						continue
					)
						
					(
						currentJob+=1
						SMTDSettings.JobName = theJobName + " ["+ theView.name + "] (BATCH " + currentJob as string+ " of " + numberOfBatchJobs as string + ")"
						
						--Load Scene State
						if theView.sceneStateName == "" then
						(
							try(SMTD_MainRollout.Ui_report ("!!No Scene State Defined For This View"))catch()
							SMTDSettings.nonFatalErrorsCount+=1
						)
						else
						(
							try(SMTD_MainRollout.Ui_report (">Restoring Scene State [" + theView.sceneStateName + "]"))catch()
							result = sceneStateMgr.RestoreAllParts theView.sceneStateName
							if result then
							(
								try(SMTD_MainRollout.Ui_report ("+Scene State Manager Successfully Restored the Scene State."))catch()
								needMaxReload = true
							)	
							else
							(
								try(SMTD_MainRollout.Ui_report ("--Scene State Manager FAILED to Restore the Scene State"))catch()
								SMTDSettings.nonFatalErrorsCount+=1									
							)
						)		
						
						--Load Render Preset
						if (fileNameFromPath theView.presetFile) == "" then
						(
							try(SMTD_MainRollout.Ui_report ("!!No Render Preset Defined For This View"))catch()
							SMTDSettings.nonFatalErrorsCount+=1								
						)
						else
						(
							try(SMTD_MainRollout.Ui_report (">Loading Render Preset [" +  theView.presetFile + "]"))catch()
							result = renderpresets.LoadAll 0 theView.presetFile
							if result then
							(
								try(SMTD_MainRollout.Ui_report ("+Render Presets Manager Successfully Loaded the Render Preset."))catch()
								needMaxReload = true
							)	
							else
							(
								try(SMTD_MainRollout.Ui_report ("!!Render Presets Manager FAILED to Load the Render Preset For This View"))catch()
								SMTDSettings.nonFatalErrorsCount+=1									
							)
						)	
						
						local forceCamera = ""
						--Set Camera if specified
						if isValidNode theView.camera then
						(
							forceCamera = theView.camera.name
							try(viewport.setCamera (getNodeByName forceCamera))catch()
							if def_Camera == undefined do needMaxReload = true
						)	
						else if def_Camera != undefined do forceCamera = def_Camera.name
						
						--Set New Output File
						if theView.outputFilename != "" do rendOutputFileName = theView.outputFilename --get path from Batch Render Dialog, if specified
						rendSaveFile = true
						renderSceneDialog.open()
						renderSceneDialog.close()	
						
						--Set Alternative Resolution and Pixel Aspect if Override Preset is on
						--Set Alternative Frame Range is Override Preset is on
						if theView.overridePreset then
						(
							RenderWidth = theView.width
							RenderHeight = theView.height
							RenderPixelAspect = theView.pixelAspect
							rendTimeType = 3
							rendStart = theView.startFrame
							rendEnd = theView.endFrame
						)	
						
						try(SMTD_MainRollout.Ui_report (">Spawning Batch Job " + SMTDSettings.JobName))catch()
						rendUseActiveView = true	
						local msg = SMTDFunctions.SubmitJobFromUI batchName:batchName forceCamera:forceCamera
						try(SMTD_MainRollout.Ui_report (msg)) catch()
						if SMTDSettings.CleanupSubmissionFoldersAfterEachBatchJob do SMTDFunctions.cleanUpSubmissionFolders all:true exclude:#(originalFolder)
					)
				)
				else
				(
					try(SMTD_MainRollout.Ui_report ("!!View Definition ["+ theView.name +"] is disabled - Skipping..."))catch()
					SMTDSettings.nonFatalErrorsCount+=1						
				)
			)--end batch loop
			try(SMTD_MainRollout.Ui_report (">Restoring Scene Backup From [" + originalPath + "]" ))catch()
			SMTDFunctions.RestoreMaxFileCopy originalPath
			SMTDSettings.JobName = theJobName
			SMTDSettings.UseBatchRender = true
			true
		),

		--SUBMIT BATCH JOBS FROM A SLAVE TO DEADLINE
		fn spawnBatchJobs =
		(
			SMTDSettings.UseBatchRender = false --before spawning new jobs, make sure they don't become batch masters

			renderDimensions = SMTDFunctions.getRenderDimensions() --#(renderWidth,renderHeight,renderPixelAspect)
			
			local def_RenderWidth = renderDimensions[1]
			local def_RenderHeight = renderDimensions[2]
			local def_RenderPixelAspect = renderDimensions[3]
			local def_Camera = viewport.getCamera()
			local def_rendOutputFileName = rendOutputFileName 
			local def_rendSaveFile = rendSaveFile
			local def_rendTimeType = rendTimeType 
			local def_rendStart = rendStart
			local def_rendEnd = rendEnd
			
			local batchName = SMTDFunctions.getBatchName()
			
			local theJobName = SMTDSettings.JobName
			local currentJob = 0
			local numViews = batchRenderMgr.numViews 
			local views = (for i = 1 to numViews collect (batchRenderMgr.getView i))
			local numberOfBatchJobs =  (for i = 1 to numViews where (batchRenderMgr.getView i).enabled collect i).count
			
			local needMaxReload = false
			
			local ExternalFilesListName = ""
			if SMTDSettings.CurrentRepository == "" and SMTDSettings.SubmitExternalFilesMode > 1 do
			(
				local ExternalFilesListName = DeadlineUtil.SceneFilePath + "\\ExternalFilesList.txt"  
				if doesFileExist ExternalFilesListName then
				(
					try(DeadlineUtil.logMessage "External File List Found!")catch()
				)
				else
					try(DeadlineUtil.logMessage "External File List DOES NOT Exist!")catch()
			)
			
			for i = 1 to numViews do
			(
				local theView = views[i]
				if theView.enabled then 
				(
					if needMaxReload then
					(
						try(DeadlineUtil.LogMessage (">Reloading original scene..."))catch()
						--loadMaxFile (maxFilePath + maxFileName) quiet:true
						loadMaxFile (DeadlineUtil.SceneFilePath + "\\" + maxFileName) quiet:true
						needMaxReload = false
					)	
					else
					(
						RenderWidth = def_RenderWidth 
						RenderHeight = def_RenderHeight 
						RenderPixelAspect = def_RenderPixelAspect 
						if (def_Camera != undefined) and (IsValidNode def_Camera) do viewport.setCamera def_Camera
						rendOutputFileName = def_rendOutputFileName 
						rendSaveFile = def_rendSaveFile
						rendTimeType = def_rendTimeType 
						rendStart = def_rendStart 
						rendEnd = def_rendEnd 
					)
					
					if theView.outputFilename != "" then
					(
						currentJob+=1
						try(DeadlineUtil.SetProgress (100.0*i/numViews) )catch()
						try(DeadlineUtil.LogMessage (">Processing View Definition ["+ theView.name +"] ..."))catch()	
						SMTDSettings.JobName = theJobName + " ["+ theView.name + "] (BATCH " + currentJob as string+ " of " + numberOfBatchJobs as string + ")"
						
						--Load Scene State
						if theView.sceneStateName == "" then
						(	
							try(DeadlineUtil.LogMessage ("!!No Scene State Defined For This View"))catch()
							SMTDSettings.nonFatalErrorsCount+=1		
						)
						else
						(
							try(DeadlineUtil.LogMessage (">Restoring Scene State [" + theView.sceneStateName + "]"))catch()
							result = sceneStateMgr.RestoreAllParts theView.sceneStateName
							if result then
							(
								try(DeadlineUtil.LogMessage ("+Scene State Manager Successfully Restored the Scene State."))catch()
								needMaxReload = true
							)	
							else
							(
								try(eadlineUtil.LogMessage ("!!Scene State Manager FAILED to Restore the Scene State"))catch()
								SMTDSettings.nonFatalErrorsCount+=1		
							)
						)		
						
						--Load Render Preset
						if (fileNameFromPath theView.presetFile) == "" then
						(
							try(DeadlineUtil.LogMessage ("!!No Render Preset Defined For This View"))catch()
							SMTDSettings.nonFatalErrorsCount+=1		
						)
						else
						(
							--DeadlineUtil.LogMessage (">Loading Render Preset [" + (fileNameFromPath theView.presetFile) + "]")
							--result = renderpresets.LoadAll 0 (maxFilePath + (fileNameFromPath theView.presetFile))
							try(DeadlineUtil.LogMessage (">Loading Render Preset [" + (DeadlineUtil.SceneFilePath + "\\" + (fileNameFromPath theView.presetFile)) + "]"))catch()
							result = renderpresets.LoadAll 0 (DeadlineUtil.SceneFilePath + "\\" + (fileNameFromPath theView.presetFile))
							if result then
							(
								try(DeadlineUtil.LogMessage ("+Render Presets Manager Successfully Loaded the Render Preset."))catch()
								needMaxReload = true
							)	
							else
							(
								try(DeadlineUtil.LogMessage ("!!Render Presets Manager FAILED to Load the Render Preset For This View"))catch()
								SMTDSettings.nonFatalErrorsCount+=1
							)
						)	
						
						local forceCamera = ""
						--Set Camera if specified
						if isValidNode theView.camera then
						(
							forceCamera = theView.camera.name
							try(viewport.setCamera (getNodeByName forceCamera))catch()
							if def_Camera == undefined do needMaxReload = true
						)	
						else if def_Camera != undefined do forceCamera = def_Camera.name						
						
						--Set New Output File
						if theView.outputFilename != "" do rendOutputFileName = theView.outputFilename --get path from Batch Render Dialog
						rendSaveFile = true
						
						--Set Alternative Resolution and Pixel Aspect if Override Preset is on
						--Set Alternative Frame Range is Override Preset is on
						if theView.overridePreset then
						(
							RenderWidth = theView.width
							RenderHeight = theView.height
							RenderPixelAspect = theView.pixelAspect
							rendTimeType = 3
							rendStart = theView.startFrame
							rendEnd = theView.endFrame
						)	
						
						try(DeadlineUtil.LogMessage (">Spawning Batch Job " + SMTDSettings.JobName))catch()
						try(SMTD_MainRollout.Ui_report (">Spawning Batch Job " + SMTDSettings.JobName))catch()
						rendUseActiveView = true
						local msg = SMTDFunctions.SubmitJobFromUI batchName:batchName forceCamera:forceCamera externalFilesList:ExternalFilesListName
						try(SMTD_MainRollout.Ui_report (msg)) catch()
						if SMTDSettings.CleanupSubmissionFoldersAfterEachBatchJob do SMTDFunctions.cleanUpSubmissionFolders all:true
					)
					else
					(
						try(DeadlineUtil.LogMessage ("!!View Definition ["+ theView.name +"] has NO Output File Name - Skipping..."))catch()
						SMTDSettings.nonFatalErrorsCount+=1		
					)
				)
				else
				(
					try(DeadlineUtil.LogMessage ("!!View Definition ["+ theView.name +"] is disabled - Skipping..."))catch()				
					SMTDSettings.nonFatalErrorsCount+=1		
				)
			)--end batch loop
			SMTDSettings.UseBatchRender = true
			true
		),
		
		fn getJobIDFromMessage renderMsg =
		(
			SMTDSettings.DeadlineSubmissionLastJobID = "failed"
			theStringStream = renderMsg as stringStream
			skipToString theStringStream "JobID="
			try(SMTDSettings.DeadlineSubmissionLastJobID = readline theStringStream)catch()
			close theStringStream 
		),

		fn getRenderMessage =
		(
			local renderMsg = "" as stringStream
			local resultArray = try ( ( dotNetClass "System.IO.File" ).ReadAllLines SMTDPaths.SubmitOutput )catch(#(""))
			for i in resultArray do format "%\n" i to:renderMsg
			
			/*
			local resultFile = OpenFile SMTDPaths.SubmitOutput
			local renderMsg = "No message."
			if (resultFile != undefined) do
			(
				seek resultFile #eof
				local fileSize = filepos resultFile
				seek resultFile 0
				renderMsg = readChars resultFile fileSize errorAtEOF:false
				close resultFile
			)*/
			
			renderMsg as string
		),
		
		fn GetExternalFilesToCopy =
		(
			local uniquenamedata = #()
			local BitmapsCopyData = #()
			if SMTDSettings.CurrentRepository == "" AND SMTDSettings.SubmitExternalFilesMode > 1 AND SMTDSettings.SubmitExternalFilesMode < 4  do
			(
				for o in SMTDExternalRefsArray.storeBitmapPath where findItem uniquenamedata o[2] == 0 do 
				(
					append uniquenamedata o[2]
					append BitmapsCopyData #(o[2],o[3])
				)	
				for o in SMTDExternalRefsArray.storeHdriPath where findItem uniquenamedata o[2] == 0 do 
				(
					append uniquenamedata o[2]
					append BitmapsCopyData #(o[2],o[3])
				)	
				for o in SMTDExternalRefsArray.StoreSceneXRefs where o[4] AND findItem uniquenamedata o[2] == 0 do 
				(
					append uniquenamedata o[2]
					append BitmapsCopyData #(o[2],o[3])
				)	
				for o in SMTDExternalRefsArray.StoreObjectXRefs where findItem uniquenamedata o[2] == 0 do 
				(
					append uniquenamedata o[2]
					append BitmapsCopyData #(o[2],o[3])
				)	
				for o in SMTDExternalRefsArray.StoreSceneVrayProxies where findItem uniquenamedata o[2] == 0 do 
				(
					append uniquenamedata o[2]
					append BitmapsCopyData #(o[2],o[3])
				)
				for o in SMTDExternalRefsArray.StoreSceneCoronaProxies where findItem uniquenamedata o[2] == 0 do 
				(
					append uniquenamedata o[2]
					append BitmapsCopyData #(o[2],o[3])
				)
				for o in SMTDExternalRefsArray.StoreSceneMRProxies where findItem uniquenamedata o[2] == 0 do 
				(
					if o[1].animated then
					(
						local theAnimationFiles = SMTDFunctions.GetAnimationFiles o[2]
						for f in theAnimationFiles do
						(
							append uniquenamedata f
							append BitmapsCopyData #(f, SMTDFunctions.RenameTargetAnimationFile f o[3])
						)
					)
					else
					(
						append uniquenamedata o[2]
						append BitmapsCopyData #(o[2],o[3])
					)
				)
				local animaData = SMTDFunctions.ExportAnima2Anipack()
				for o in animaData do
				(
					append BitmapsCopyData #(o, o)
				)
			)
			BitmapsCopyData
		),
		

		fn SubmitTransferJob =
		(
			-- Only submit a transfer job if a remote repository has been selected.
			if SMTDSettings.CurrentRepository2 != "" do
			(
				try(SMTD_MainRollout.Ui_report ">Submitting Transfer Job.")catch()
				
				local transferJobID = SMTDSettings.DeadlineSubmissionLastJobID
				local transferJobRepository = SMTDSettings.CurrentRepository2
				local transferAsSuspended = SMTDSettings.TransferJobAsSuspended
				local transferCompress = SMTDSettings.TransferCompressed
				local transferEmailResults = true
				local transferRemoveLocal = true
				
				local transferJobName = ("Transfer of " + (SMTDFunctions.FormatJobName SMTDSettings.JobName) + " (" + transferJobID + ")")
				local transferDepartment = SMTDSettings.Department
				local transferPool = SMTDSettings.TransferPool
				local transferGroup = SMTDSettings.TransferGroup
				local transferPriority = SMTDSettings.TransferPriority
				local transferDeleteOnComplete = SMTDSettings.TransferDeleteOnComplete
				
				local jobInfoFilename = SMTDPaths.TempDir + "job_transfer_info.job"
				local pluginInfoFilename = SMTDPaths.TempDir + "job_transfer_plugin.job"
				
				-- Create job info file
				local jobInfoFile = CreateFile jobInfoFilename encoding:#utf8 writeBOM:true
				if (jobInfoFile != undefined) then
				(
					format "Plugin=JobTransfer\n"										to:jobInfoFile
					format "Name=%\n" 						transferJobName				to:jobInfoFile
					format "BatchName=%\n" 					SMTDSettings.JobName		to:jobInfoFile
					format "UserName=%\n"					SMTDSettings.UserName		to:jobInfoFile
					format "Department=%\n" 				transferDepartment		 	to:jobInfoFile
					format "Pool=%\n" 						transferPool				to:jobInfoFile
					format "Group=%\n" 						transferGroup				to:jobInfoFile
					format "Priority=%\n" 					transferPriority 	 		to:jobInfoFile
					format "Frames=0\n"													to:jobInfoFile
					format "ChunkSize=1\n" 												to:jobInfoFile
					if transferDeleteOnComplete do
						format "OnJobComplete=Delete\n"									to:jobInfoFile
					close jobInfoFile
				)
				
				-- Create the plugin info file
				local pluginInfoFile = CreateFile pluginInfoFilename encoding:#utf8 writeBOM:true
				if (pluginInfoFile != undefined) then
				(
					format "TransferJobID=%\n" 				transferJobID				to:pluginInfoFile
					format "TransferRepository=%\n"			transferJobRepository		to:pluginInfoFile
					format "SuspendedAfterTransfer=%\n" 	transferAsSuspended			to:pluginInfoFile
					format "RemoveLocalAfterTransfer=%\n" 	transferRemoveLocal			to:pluginInfoFile
					format "EmailResultsAfterTransfer=%\n" 	transferEmailResults		to:pluginInfoFile
					format "CompressFiles=%\n" 				transferCompress 	 		to:pluginInfoFile
					
					format "TransferJobFrames=\n"										to:pluginInfoFile
					format "TransferJobChunkSize=\n"									to:pluginInfoFile
					
					close pluginInfoFile
				)
				
				-- Submit the transfer job
				local initialArgs = "\"" + jobInfoFilename + "\" \"" + pluginInfoFilename + "\""
				local retCode = SMTDFunctions.waitForCommandToComplete initialArgs SMTDSettings.TimeoutSubmission
				if retCode == #success then
				(
					renderMsg = SMTDFunctions.getRenderMessage()
					try(SMTD_MainRollout.Ui_report ("Transfer Job submitted successfully.\n\n" + renderMsg))catch()
					try(SMTD_MainRollout.sld_lastSubmissionState.color = green)catch()
				)	
				else	
				(
					try(SMTD_MainRollout.sld_lastSubmissionState.color = red*0.7)catch()
					if result == #timeout then
						try(SMTD_MainRollout.Ui_report ("--Failed To Submit Transfer Job in " + SMTDSettings.TimeoutSubmission as string + " seconds.\nConsider Increasing the Job Submission Timeout in the User Options tab."))catch()
					else	
						try(SMTD_MainRollout.Ui_report ("--Failed To Submit Transfer Job."))catch()
				)
			)
		),
		
		fn SubmitJob createJobInfo:true createSubmitInfo:true timeout:3600 =
		(
			SMTDSettings.DeadlineSubmissionSuccessful = false
			SMTDSettings.DeadlineSubmissionLastJobID = "failed"
			renderSceneDialog.Commit()
			try(SMTD_RegionRendering.chk_showRegionGizmo.changed (SMTD_RegionRendering.chk_showRegionGizmo.state = false))catch()
			try(SMTD_TilesRendering.chk_showRegionGizmo.changed (SMTD_TilesRendering.chk_showRegionGizmo.state = false))catch()
				
			SMTDFunctions.createSubmissionFolderAndUpdatePaths()
				
			local TempMaxFile = ""
			local submitSceneMode = SMTDSettings.SubmitSceneMode							--remember the current MAX scene saving mode
			if SMTDSettings.SubmitExternalFilesMode > 1 do 									--if submitting external assets is enabled, 
			(
				SMTDSettings.SubmitSceneMode = #reposave									--force MAX file in the Repository
				SMTDSettings.SubmitSceneNetworkReuseLocation = false						--lower the scene reuse flag too
			)	
			case SMTDSettings.SubmitSceneMode of
			(
				#reposave: 
				(
					local TempMaxFile = getFileNamePath (SMTDPaths.RestoreTempMaxFile) + maxFileName
					if maxFileName == "" do TempMaxFile += "untitled.max"
					if (doesFileExist TempMaxFile) do deleteFile TempMaxFile
					result = SMTDFunctions.SaveMaxFileCopy TempMaxFile
					if result != undefined do return result
				)
				default: --#networksave or #globalnetworksave
				(
					local theFilterTime = filterString localtime " /\\-:."
					local theTime = ""
					for i = 1 to theFilterTime.count-1 where (classof (execute theFilterTime[i]) != Integer) do deleteItem theFilterTime i
					for i = 1 to theFilterTime.count do theTime += theFilterTime[i] + "_"
					if SMTDSettings.SubmitSceneMode == #networksave then
						TempMaxFile = SMTDSettings.SubmitSceneBasePath +"\\"+SMTDSettings.userName+"\\"+theTime+"\\"
					else
						TempMaxFile = SMTDSettings.SubmitSceneGlobalBasePath +"\\"+SMTDSettings.userName+"\\"+theTime+"\\"
					makedir TempMaxFile all:true
					TempMaxFile += (if maxFileName == "" then "untitled.max" else maxFileName)
					result = SMTDFunctions.SaveMaxFileCopy TempMaxFile
					if result != undefined do return result
				)
				#networkuse: 
				(
					if maxFileName == "" then
					(
						filename = getMAXSaveFileName()
						if filename == undefined do return ""
						
						TempMaxFile = filename
					)
					else
						TempMaxFile = maxFilePath + maxFileName
					if not SMTDSettings.StateSetsSubmit AND SMTDSettings.DeleteEmptyStateSets do SMTDFunctions.DeleteEmptyStateSets()
					saveMaxFile TempMaxFile
				)
				#networksaveanduse:
				(
					if maxFileName == "" then
					(
						filename = getMAXSaveFileName()
						if filename == undefined do return ""
						
						TempMaxFile = filename
					)
					else
						TempMaxFile = maxFilePath + maxFileName
					if not SMTDSettings.StateSetsSubmit AND SMTDSettings.DeleteEmptyStateSets do SMTDFunctions.DeleteEmptyStateSets()
					saveMaxFile TempMaxFile
				)
				#networkremap:
				(
					
				)				
			)
				
			local initialArgs = "" As StringStream
			format "-outputfiles\n%\n%\n" SMTDPaths.SubmitOutput  SMTDPaths.SubmitExitCode to:initialArgs
			
			if SMTDSettings.bgSubmission do format "-background\n-notify\n" to:initialArgs
			if SMTDSettings.dropSubmission do format "-drop\n" to:initialArgs
			
			if createSubmitInfo do
				if ((SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile) != true) do return #SubmitInfoFileCreationFailed
			if createJobInfo do
				if ((SMTDFunctions.CreateJobInfoFile SMTDPaths.JobInfoFile) != true) do return #JobInfoFileCreationFailed
			
			if not doesFileExist SMTDPaths.SubmitInfoFile do return #SubmitInfoFileMissing
			if not doesFileExist SMTDPaths.JobInfoFile do return #JobInfoFileMissing
			
			if( SMTDSettings.SubmitSceneMode == #reposave ) then
				format "%\n%\n%\n" SMTDPaths.SubmitInfoFile SMTDPaths.JobInfoFile TempMaxFile to:initialArgs
			else
				format "%\n%\n" SMTDPaths.SubmitInfoFile SMTDPaths.JobInfoFile to:initialArgs
			
			if SMTDSettings.SubmitAsMXSJob do format "%\n" SMTDSettings.MAXScriptFile to:initialArgs
				
			local BitmapsCopyData = #()
			if SMTDSettings.CurrentRepository == "" and SMTDSettings.SubmitExternalFilesMode > 1 do
				BitmapsCopyData = SMTDFunctions.GetExternalFilesToCopy()			
			
			--Output external files to the command line for copying
			if SMTDSettings.SubmitExternalFilesMode > 1 do			
				for aBitmap in BitmapsCopyData where findItem SMTDSettings.MissingFiles aBitmap[2] == 0 do
					format "%\n" aBitmap[2] to:initialArgs				
				
			local initialArgsFileName = (getFileNamePath SMTDPaths.JobInfoFile + "initialArgsFile.txt") 
			local initialArgsFile = createFile initialArgsFileName encoding:#utf8 writeBOM:true
			format "%\n" (initialArgs as string) to:initialArgsFile
			close initialArgsFile 
			initialArgsFileName = "\""+initialArgsFileName+"\""
			
			local retCode = SMTDFunctions.waitForCommandToComplete initialArgsFileName timeout paramIsFile:true		
			
			SMTD_LastMessage = SMTDFunctions.getRenderMessage()
			if retCode == #success then
			(
				SMTDSettings.DeadlineSubmissionSuccessful = true
				SMTDFunctions.getJobIDFromMessage SMTD_LastMessage
				if SMTDSettings.AssetsPreCacheFiles == true AND SMTDSettings.AssetsIncludeFilesInJob == true then
				(
					local PrecacheResults = SMTDFunctions.CallDeadlineCommandInMemory ("-AWSPortalPrecacheJob " + SMTDSettings.DeadlineSubmissionLastJobID ) multiLine:true
					try(SMTD_MainRollout.Ui_report (">AWS Portal Pre-Cache Results: \n\n"+PrecacheResults))catch()
				)
				--SMTDFunctions.CopyExternalFilesToRepository() --try to copy external bitmaps
				SMTDFunctions.SubmitTransferJob() -- submits a remote transfer job if necessary
			)	
			SMTDSettings.SubmitSceneMode = submitSceneMode --restore the submit scene mode if it was overridden
			retCode 
		),
		
		fn getStateSetChildrenRecursive theParent theTVParent parentArray =
		(
			for i = 0 to theParent.Children.count-1 do
			(
				currentParentArray = deepCopy parentArray
				local isActualState = theParent.Children.Item[i].ToString() == "Autodesk.Max.StateSets.Entities.StateSets.StateSet"
				local isScriptState = theParent.Children.Item[i].ToString() == "Autodesk.Max.StateSets.Entities.StateSets.Scripted"

				if isScriptState do append currentParentArray theParent.Children.Item[i]				
				if isActualState do
				(
					local theName = theParent.Children.Item[i].Name
					local stateIsEmpty = try(theParent.Children.Item[i].IsEmpty)catch(true)
					local theDesc =  (if stateIsEmpty then "No Changes Recorded" else (try(theParent.Children.Item[i].Children.Item[0].Name)catch("???")))
					if matchPattern theDesc pattern:"1 *" then theDesc = substring theDesc 1 (theDesc.count-1)
					local newNode = if theTVParent != undefined then
						theTVParent.Nodes.add (theName+ " ["+theDesc+"]")
					else
						undefined
					if newNode != undefined do
					(
						newNode.checked = not stateIsEmpty
						newNode.forecolor = if newNode.checked then SMTD_ColorPalette.greenColor else SMTD_ColorPalette.grayColor
						newNode.Tag = ::SMTD_StateSetsTree.count+1
					)
					append currentParentArray theParent.Children.Item[i]
					append SMTD_StateSetsTree #(currentParentArray, not stateIsEmpty, theName, theDesc, newNode)
					if findItem #("Autodesk.Max.StateSets.Entities.StateSets.StateSet", "Autodesk.Max.StateSets.Entities.StateSets.Master") (theParent.Children.Item[i].ToString()) > 0 do
					(
						SMTDFunctions.getStateSetChildrenRecursive theParent.Children.Item[i] newNode currentParentArray
					)
					if newNode != undefined do newNode.expand()
				)
			)		
			return true
		),
		
		fn getStateSetChildrenForSubmissionRecursive theParent parentArray =
		(
			for i = 0 to theParent.Children.count-1 do
			(
				currentParentArray = deepCopy parentArray
				local isActualState = theParent.Children.Item[i].ToString() == "Autodesk.Max.StateSets.Entities.StateSets.StateSet"
				local isScriptState = theParent.Children.Item[i].ToString() == "Autodesk.Max.StateSets.Entities.StateSets.Scripted"
				
				if isScriptState do append currentParentArray theParent.Children.Item[i]				
				if isActualState do
				(
					local theName = theParent.Children.Item[i].Name
					local stateIsEmpty = try(theParent.Children.Item[i].IsEmpty)catch(true)
					local theDesc =  (if stateIsEmpty then "No Changes Recorded" else (try(theParent.Children.Item[i].Children.Item[0].Name)catch("???")))
					if matchPattern theDesc pattern:"1 *" then theDesc = substring theDesc 1 (theDesc.count-1)
					append currentParentArray theParent.Children.Item[i]
					append SMTD_StateSetsTreeForSubmission #(currentParentArray, not stateIsEmpty, theName, theDesc)
					if findItem #("Autodesk.Max.StateSets.Entities.StateSets.StateSet", "Autodesk.Max.StateSets.Entities.StateSets.Master") (theParent.Children.Item[i].ToString()) > 0 do
					(
						SMTDFunctions.getStateSetChildrenForSubmissionRecursive theParent.Children.Item[i] currentParentArray
					)
				)
			)		
			return true
		),
		
		fn SubmitStateSetJobs batchName:"" forceCamera:"" stereoCameraLabel:"" =
		(
			local StateSetsRootEntry
			if SMTDSettings.StateSetsSubmit then
			(
				local theMessages = "" as stringStream
				local theCount = (SMTDSettings.StateSetsList as array).count
				local theCountString1 = if theCount == 1 then "ONE" else theCount as string
				local theCountString2 = if theCount == 1 then "SET" else "SETS"
					
				format ">SUBMITTING % STATE %\n" theCountString1 theCountString2 to:theMessages
				--format "SMTDSettings.StateSetsList=%\n" SMTDSettings.StateSetsList

				local ssP = try(dotNetObject "Autodesk.Max.StateSets.Plugin")catch(undefined)
				if ssP != undefined do
				(
					::SMTD_StateSetsTreeForSubmission = #()
					StateSetsRootEntry = ssP.Instance.EntityManager.RootEntity
					SMTDFunctions.getStateSetChildrenForSubmissionRecursive StateSetsRootEntry.MasterStateSet #()
				)
				--if SMTD_StateSetsTreeForSubmission.count == SMTD_StateSetsTree.count then
				(
					local oldState = StateSetsRootEntry.MasterStateSet.CurrentState
					local cnt = 0
					
					if batchName == "" do batchName = SMTDFunctions.getBatchName()
					for i = SMTD_StateSetsTreeForSubmission.count to 1 by -1 where findItem SMTDSettings.StateSetsNamesList SMTD_StateSetsTreeForSubmission[i][3] > 0 do
					(
						cnt += 1
						SMTDSettings.StateSetToRender = i
						SMTDSettings.StateSetName =	SMTD_StateSetsTreeForSubmission[i][3]
						SMTDSettings.StateSetInfo = SMTD_StateSetsTreeForSubmission[i][4]
						format ">Submitting State Set %: % : %\n" SMTDSettings.StateSetToRender SMTDSettings.StateSetName SMTDSettings.StateSetInfo to:theMessages
						StateSetsRootEntry.MasterStateSet.CurrentState = SMTD_StateSetsTreeForSubmission[i][1]
						
						local theCameras = SMTDFUnctions.GetStereoCamerasFromCurrentView() --returns either the 3 cameras of a stereo rig, or empty array
						if stereoCameraLabel != "" do 
						(
							if theCameras.count == 3 then
							(
								forceCamera = case stereoCameraLabel of
								(
									(SMTDSettings.LeftEyeTag): theCameras[1].name
									(SMTDSettings.RightEyeTag): theCameras[2].name
									(SMTDSettings.CenterEyeTag): theCameras[3].name
									default: ""
								)
								format "+% Stereo Camera Requested, State Set Stereo Camera Is [%]\n" stereoCameraLabel forceCamera to:theMessages
							)
							else
							(
								local theViewCamera = viewport.getCamera()
								local theViewCameraName = "Current View"
								if isValidNode theViewCamera do theViewCameraName = theViewCamera.name
								format "--% Stereo Camera Requested, But State Set View Is [%]\n" stereoCameraLabel theViewCameraName to:theMessages
							)
						)
						
						format "\n%\n" ("==STATE SET [ "+SMTDSettings.StateSetName+" ] SUBMISSION MESSAGE START======================================================================================") to:theMessages

						if  SMTDSettings.SubmitSceneMode != #reposave  then
							SMTDSettings.SubmitSceneNetworkReuseLocation = cnt != 1 --when cnt is 1, set to false, otherwise true to reuse the file!
						else
							SMTDSettings.SubmitSceneNetworkReuseLocation  = false
							
						local theMessage = SMTDFunctions.SubmitJobFromUI batchName:batchName forceCamera:forceCamera stereoCameraLabel:stereoCameraLabel
						format "%\n\n" theMessage to:theMessages
						format "%\n\n" ("==STATE SET JOB [ "+SMTDSettings.StateSetName+" ] SUBMISSION MESSAGE END======================================================================================") to:theMessages
					)--end loop
					StateSetsRootEntry.MasterStateSet.CurrentState = oldState
					SMTDSettings.SubmitSceneNetworkReuseLocation = false
					if cnt == 0 do 
					(
						SMTDSettings.FatalErrorsCount += 1
						theMessages = "--No State Sets were enabled for Submission!"
					)
					theMessages as string
				)
				/*else 
				(
					SMTDSettings.FatalErrorsCount += 1
					"--The Scene State Sets DO NOT MATCH the State Sets Displayed In SMTD UI!\nPlease Press the [UPDATE LIST] Button in the StateSets Tab, then Submit Again!"
				)*/
			)--end if
			else 
			(
				SMTDSettings.FatalErrorsCount += 1
				"--State Sets submission function called, but State Sets submission was disabled via SMTDSettings.StateSetsSubmit=false"
			)
		),		
		
		fn GetStereoCamerasFromCurrentView =
		(
			--This function will attempt to figure out the left/right/center cameras based on what camera is active in the current view
			--It works with the VRay Stereo Camera rig, the native Stereo Camera rig of 3ds Max, or custom rigs that follow the following rules
			-- * The custom cameras must contain the token "left", "right" or "center"/"centre" to be considered part of the custom stereo rig - the tokes will be used to determine which is which
			-- * A custom stereo rig *must* contain at least a "left" and a "right" camera with a common parent, the "center" camera is optional.
			-- * If the common parent is not another camera, it must contain the token "stereo" in its name. Such a parent can be a helper, a group head, or any other object.
			--* If the common parent is another camera, it can be the "center" camera (in which case the center camera will also be submittable), or any other camera (but it won't be submittable)
			
			local theViewCamera = viewport.getCamera() --get the current view's camera
			if theViewCamera != undefined then --if it is valid,
			(
				--first see if an active VRayStereoscopic Helper exists and the renderer is set to VRay
				if SMTDFunctions.getRendererIdString() == "vray" AND (for o in getClassInstances VRayStereoscopic where o.enabled == true collect o).count > 0 then
				(
					#() --return nothing, VRay will handle this internally
				)
				else 
				(
					if classof theViewCamera == XRefObject do return #()
					--see if it is part of a VRay stereo rig: - either the center camera which has a VRayStereoRigSlaveControl controller, or a left/right eye camera which is controlled by such a controller:
					local VRayRig = if classof theViewCamera.transform.controller == VRayStereoRigSlaveControl then
						#(theViewCamera.transform.controller)
					else
						for o in refs.dependents theViewCamera where classof o == VRayStereoRigSlaveControl collect o
							
					--If we found at least one VRayStereoRigSlaveControl controller, we can collect the left/right/center cameras of the first controller and return them.
					--Note that it is technically possible (although highly unlikely) to have the same left and right eye cameras assigned to more than one Vray stereo controller.
						--If that's the case, and a left or right eye is set in the viewport. the FIRST controller found will be used, and its controlled camera will be sent as center eye
						--However, if the CENTER eye is set in the viewport, it will point at the specific controller, so then the corresponding explicit center eye camera will be sent.
					if VRayRig.count > 0 then 
					(
						local theChildren = #()
						append theChildren VRayRig[1].left_camera_in_use
						append theChildren VRayRig[1].right_camera_in_use
						join theChildren (refs.dependentNodes VRayRig[1])
						return theChildren
					)					
					else 	--try to find any objects that include the current view's camera in its parent list, and the parent is either a native stereo rig head, contains the token "stereo" in the object's name, or happens to be a camera, too
					(
						local theParents = (for o in objects where (try(findItem o.children theViewCamera > 0)catch(false)) AND (classof o == Stereo_Camera_Assembly_Head_Object OR matchPattern o.name pattern:"*stereo*" or isKindOf o Camera) collect o)
						append theParents theViewCamera --add the camera to the parents list, in case it was used as the parent of the stereo rig
						if theParents.count > 0 then --if any parents were found that match the above rules,
						(
							for p in theParents do --loop through the parents
							(
								local theChildren = for o in p.children where isKindOf o Camera collect o --collect all cameras that are linked to that parent
								if isKindOf p Camera do append theChildren p --if cameras are linked to another camera (e.g. the Center one), include the parent in the list of children
								if classof p != Stereo_Camera_Assembly_Head_Object do --if not a native stereo rig, we need to figure out the left/right/center cameras by name and put them in the right order
								(
									local theOrderedChildren = #() --this will be the list in correct order
									local theCameras1 = for o in theChildren where matchPattern o.name pattern:"*left*" collect o --collect all cameras that contain "left" in their name
									if theCameras1.count > 0 then  --if there were any, use the first one found, otherwise skip the loop as we cannot submit stereo cameras without a left camera
										append theOrderedChildren theCameras1[1] 
									else
										continue
									
									theCameras1 = for o in theChildren where matchPattern o.name pattern:"*right*" collect o --collect all right cameras, same as above
									if theCameras1.count > 0 then 
										append theOrderedChildren theCameras1[1] 
									else
										continue
									
									theCameras1 = for o in theChildren where (matchPattern o.name pattern:"*center*" or matchPattern o.name pattern:"*centre*") collect o --collect all center / centre cameras
									if theCameras1.count > 0 do  --if there were any, add the first one
										append theOrderedChildren theCameras1[1] 
									if theOrderedChildren.count > 1 then --at this point, we should have at least left+right, or left+right+center collected in the right order. If yes, we will return them as the result, otherwise we skip the loop
										theChildren = theOrderedChildren
									else 
										continue
								)
								
								if theChildren.count > 1 then --if we got at least two cameras collected, we return them, otherwise we skip the loop
									return theChildren
								else
									continue
							)--end p loop
							#() --if all parents' loops were skipped, we will end up here without a stereo rig, so we return an empty array
						)
						else --if no parents were found, we return an empty array 
							#()
					)--end not Vray Rig
				)--end no VRay Stereo Helper
			)--end if camera not undefined
			else #() --if the view was not a valid camera object, we return an empty array
		),
		
		fn canSubmitPreviewJob TilesRendering MultiRegionRendering logWarning:true =
		(
			if not SMTDSettings.RenderFramesPreviewJob do return false
				
			if logWarning do try(SMTD_MainRollout.Ui_report ">Preview Job Submission was requested, checking for validity...")catch()
			
			if SMTDSettings.SubmitAsMXSJob do
			(
				if logWarning do 
				(
					try(SMTD_MainRollout.Ui_report "!!Cannot Submit Preview Job: A MAXScript Job was requested.")catch()
					SMTDSettings.nonFatalErrorsCount+=1	
				)
				return false
			)
			if (SMTDSettings.UseCustomFrameList == true and ((isKindOf SMTDSettings.CustomFrameList Array and SMTDSettings.CustomFrameList.count < 2 ) or not isKindOf SMTDSettings.CustomFrameList Array)) do
			(
				if logWarning do 
				(				
					try(SMTD_MainRollout.Ui_report "!!Cannot Submit Preview Job: Rendering a Single Custom Frame was requested via SMTDSettings.UseCustomFrameList and SMTDSettings.CustomFrameList properties.")catch()
					SMTDSettings.nonFatalErrorsCount+=1	
				)	
				return false
			)
			if (SMTDSettings.UseCustomFrameList == true and isKindOf SMTDSettings.CustomFrameList Array and SMTDSettings.CustomFrameList.count <= SMTDSettings.PreviewJobFrameCount ) do
			(
				if logWarning do 
				(				
					try(SMTD_MainRollout.Ui_report ("!!Cannot Submit Preview Job: Custom Frames List requested via SMTDSettings.CustomFrameList contains "+SMTDSettings.CustomFrameList.count as string + " frames, Preview Job set to "+SMTDSettings.PreviewJobFrameCount as string +" frames.") )catch()
					SMTDSettings.nonFatalErrorsCount+=1	
				)	
				return false
			)			
			if rendTimeType == 1 and SMTDSettings.UseCustomFrameList != true do
			(
				if logWarning do 
				(				
					try(SMTD_MainRollout.Ui_report "!!Cannot Submit Preview Job: Rendering a Single Frame was requested.")catch()
					SMTDSettings.nonFatalErrorsCount+=1	
				)	
				return false
			)						
			if rendTimeType == 4 and SMTDSettings.UseCustomFrameList != true do
			(
				if logWarning do 
				(				
					try(SMTD_MainRollout.Ui_report "!!Cannot Submit Preview Job: Rendering a Custom Frame List was requested.")catch()
					SMTDSettings.nonFatalErrorsCount+=1	
				)
				return false
			)
			if TilesRendering do
			(
				if logWarning do 
				(				
					try(SMTD_MainRollout.Ui_report "!!Cannot Submit Preview Job: Tiles Rendering was requested.")catch()
					SMTDSettings.nonFatalErrorsCount+=1	
				)
				return false
			)
			if MultiRegionRendering do
			(
				if logWarning do 
				(				
					try(SMTD_MainRollout.Ui_report "!!Cannot Submit Preview Job: Multi-Region Rendering was requested.")catch()
					SMTDSettings.nonFatalErrorsCount+=1	
				)
				return false
			)
			if (SMTDFunctions.GetFrameSequenceString frameMode:#rest).count == 0 do
			(
				if logWarning do 
				(				
					try(SMTD_MainRollout.Ui_report "!!Cannot Submit Preview Job: Requested Preview Job would include All Frames - will submit a Regular Job instead.")catch()
					SMTDSettings.nonFatalErrorsCount+=1	
				)
				return false
			)
			if logWarning do try(SMTD_MainRollout.Ui_report "+Preview Job Submission is possible.")catch()
			true
		),		
------------------------------------------------------------------
--MAIN SUBMISSION FUNCTION
------------------------------------------------------------------
		fn SubmitJobFromUI batchName:"" forceCamera:"" stereoCameraLabel:"" externalFilesList:"" =
		(
			--Some additional sanity checking...
			local tilesRendering = findItem #(#singleFrameTiles) SMTDSettings.RegionRenderingMode > 0
			local multiRegionRendering = findItem #(#singleFrameMultiRegion, #animationMultiRegion) SMTDSettings.RegionRenderingMode > 0

			if SMTDSettings.MultiRegionData.count == 0 and ::SMTD_MultiRegionSettingsPersistentGlobal != undefined and ::SMTD_MultiRegionSettingsPersistentGlobal.count > 0 do
				SMTDSettings.MultiRegionData = deepCopy ::SMTD_MultiRegionSettingsPersistentGlobal
			local activeRegions = 0
			local badRegions = 0
			for i in SMTDSettings.MultiRegionData  do
			(
				if i[1] == True do activeRegions+=1
				if i[4] == 0 or i[5] == 0 do badRegions +=1
			)

			if multiRegionRendering  do
			(
				--Check for active regions in jigsaw
				if activeRegions == 0 do
				(
					try(SMTD_MainRollout.sld_lastSubmissionState.color = red)catch()
					SMTDSettings.FatalErrorsCount += 1
					return "--FAILED: Multi-Region Rendering Requested, But No Active Regions Found!"
				)
				--Check jigsaw active regions have width/height defined
				if badRegions > 0 do
				(
					try(SMTD_MainRollout.sld_lastSubmissionState.color = red)catch()
					SMTDSettings.FatalErrorsCount += 1
					return "--FAILED: Multi-Region Rendering - Bad Regions With ZERO Width Or Height!"
				)
			)
			
			if SMTDSettings.RegionRenderingMode == #singleFrameMultiRegion do
			(
				if activeRegions > SMTDSettings.TaskLimit do
				(  
					result = "--FAILED: Unable to submit job with "+(activeRegions as string)+" tasks.  Task Count exceeded Repository Job Task Limit of "+(SMTDSettings.TaskLimit as string)
					SMTDSettings.FatalErrorsCount += 1
					try(SMTD_MainRollout.Ui_report (result))catch()
					return result
				)
			)
			if SMTDSettings.RegionRenderingMode == #singleFrameTiles do
			(
				if SMTDSettings.TilesInX * SMTDSettings.TilesInY > SMTDSettings.TaskLimit do
				(  
					result = "--FAILED: Unable to submit job with "+((SMTDSettings.TilesInX * SMTDSettings.TilesInY) as string)+" tasks.  Task Count exceeded Repository Job Task Limit of "+(SMTDSettings.TaskLimit as string)
					SMTDSettings.FatalErrorsCount += 1
					try(SMTD_MainRollout.Ui_report (result))catch()
					return result
				)
			)

			try(SMTD_MainRollout.Ui_report ">Job Submission Started...")catch()
			SMTDSettings.DeadlineSubmissionSuccessful = false
			try(SMTD_MainRollout.sld_lastSubmissionState.color = red)catch()
			SMTDSettings.DeadlineSubmissionLastJobID = "failed"
			
			try(SMTD_RegionRendering.chk_showRegionGizmo.changed (SMTD_RegionRendering.chk_showRegionGizmo.state = false))catch()
			try(SMTD_TilesRendering.chk_showTilesGizmo.changed (SMTD_TilesRendering.chk_showTilesGizmo.state = false))catch()
			
			local bitmapFilenames = #()
			local backupSceneFileSaved = false
			local theXRefObjects = #()
			local theSceneXRefsCount = 0
			local renderMsg = "--"
			local warnAboutMissingFiles = true
			local oldMatEditorOpenState = false
			local oldVRayVFBState = false
			
			local oldSubmitMaxScript = false
			local oldMaxScriptFile = ""
				
			local oldRenderDialogState = renderSceneDialog.isOpen()
			renderSceneDialog.Close()
			
			if oldRenderDialogState do
			(
				try(SMTD_MainRollout.Ui_report "+Render Dialog Closed.")catch()
			)	
			
			local oldRendUseActiveView = rendUseActiveView
			if not rendUseActiveView and viewport.activeViewportID > viewport.numViews do 
			(
				rendUseActiveView = true
				try(SMTD_MainRollout.Ui_report "+UNLOCKED the Render View - the Current Viewport was MAXIMIZED!")catch()
			)
			
			if batchName == "" do
			(
				if ( SMTDSettings.DraftSubmitJob AND NOT (SMTDSettings.UseBatchRender == true and SMTDSettings.BatchRenderMode == 2 ) ) do
				(
					try(SMTD_MainRollout.Ui_report (">BatchName Needed For Future Draft Job"))catch()
					batchName = SMTDFunctions.getBatchName() --batch if Draft is enabled
				)
				if SMTDFunctions.canSubmitPreviewJob TilesRendering MultiRegionRendering logWarning:false do
				(
					try(SMTD_MainRollout.Ui_report (">BatchName Needed For Preview Job"))catch()
					batchName = SMTDFunctions.getBatchName() --batch if submitting preview job
				)
			)
			try(SMTD_MainRollout.Ui_report (">BatchName: ["+batchName+"]"))catch()
			
			SMTDSettings.CopyVbscriptFile = false
				
			SMTDFunctions.createSubmissionFolderAndUpdatePaths()

			if rpmdata != undefined and RPMDataNet != undefined and RPMDataNet.CustomSubmitStruct != undefined do --only if RPM is active
			(
				previouslysubmittedJobs = rpmdata.getcustglobstorage 10002 -- array of submitted jobs in this submission session
				doPassDependency = rpmdata.getcustglobstorage 10000
				passDependencyList = rpmdata.getcustglobstorage 10001
				if previouslysubmittedJobs == undefined do previouslysubmittedJobs = #()
				if doPassDependency == undefined do doPassDependency = False
				if passDependencyList == undefined do passDependencyList = #()
				warnAboutMissingFiles = false
			)

			-- If merging of XRefs is requested, try to save a temp. copy of the scene and then merge the xrefs into the scene.
			-- This was moved up here to allow the bitmaps of xrefs to be collected, too.
				
			--if SMTDSettings.CurrentRepository == "" then ( --Bobo:Not sure why this would matter, if we are merging, we are merging regardless of target repository
			if SMTDSettings.MergeXRefsOnSubmission or SMTDSettings.MergeSceneXRefsOnSubmission do
			(
				theXRefObjects = for i = 1 to objXRefMgr.recordCount collect (objXRefMgr.GetRecord i) --where (objXRefMgr.GetRecord i).enabled
				
				theSceneXRefsCount = xrefs.getXRefFileCount()
				if (SMTDSettings.MergeXRefsOnSubmission AND theXRefObjects.count > 0) OR (SMTDSettings.MergeSceneXRefsOnSubmission AND theSceneXRefsCount > 0) do 
				(
					try(SMTD_MainRollout.Ui_report ">Saving Scene To Backup File Before Merging XRefs..."	)catch()
					if (doesFileExist SMTDPaths.RestoreTempMaxFile) do deleteFile SMTDPaths.RestoreTempMaxFile
					if (result = SMTDFunctions.SaveMaxFileCopy SMTDPaths.RestoreTempMaxFile useMaxHold:true) != undefined do
						return ("SAVING BACKUP FILE:\n" + result)
					backupSceneFileSaved = true
					if SMTDSettings.MergeSceneXRefsOnSubmission do
					(
						local done = false
						local failedToRemove = #()
						for scenexrefdepth = 1 to 100 while not done do --attempting to merge up to 100 levels deep to avoid an infinite while loop if there is a problem with the logic below... :)
						(
							theSceneXRefsCount = xrefs.getXRefFileCount()
							for i = theSceneXRefsCount to 1 by -1 do
							(
								local theXRefFile = (xrefs.getXRefFile i)
								local theFileName = theXRefFile.filename 
								if doesFileExist theFileName then
								(
								   if not theXRefFile.disabled then
								   (
									  local result = merge theXRefFile
									  if result == true then
									  (
										 try(SMTD_MainRollout.Ui_report ("+Merged Scene XRef File "+ i as string + " ["+ theFileName +"]")   )catch()
									  )
									  else
									  (
										 try(SMTD_MainRollout.Ui_report ("!!FAILED To Merge Scene XRef File "+ i as string + " ["+ theFileName +"]")   )catch()
										 SMTDSettings.nonFatalErrorsCount+=1
										 appendIfUnique failedToRemove theFileName
									  )
								   )
								   else
								   (
									  local result = delete theXRefFile
									  if result == 0 then
									  (
										 try(SMTD_MainRollout.Ui_report ("+Deleted Disabled Scene XRef File "+ i as string + " ["+ theFileName +"]")   )catch()
									  )
									  else -- this should never happen:
									  (
										 try(SMTD_MainRollout.Ui_report ("!!FAILED to Delete Disabled Scene XRef File "+ i as string + " ["+ theFileName +"]")   )catch()
										 SMTDSettings.nonFatalErrorsCount+=1
										 appendIfUnique failedToRemove theFileName
									  )
								   )
								)
								else
								(
								   local result = delete theXRefFile
								   if result == 0 then
								   (
									  try(SMTD_MainRollout.Ui_report ("+Deleted Missing Scene XRef File "+ i as string + " ["+ theFileName +"]")   )catch()
								   )
								   else --this should never happen:
								   (
									  try(SMTD_MainRollout.Ui_report ("!!FAILED to Delete Missing Scene XRef File "+ i as string + " ["+ theFileName +"]")   )catch()
									  SMTDSettings.nonFatalErrorsCount+=1
									  appendIfUnique failedToRemove theFileName
								   )                     
								)
							)--end i loop
							local numberOfFilesToMerge = 0
							theSceneXRefsCount = xrefs.getXRefFileCount()
							for i = 1 to theSceneXRefsCount do
							(
								local theXRefFile = xrefs.getXRefFile i
								if findItem failedToRemove theXRefFile.filename == 0 do numberOfFilesToMerge += 1
							)
							done = numberOfFilesToMerge == 0
							try(SMTD_MainRollout.Ui_report ("+End of Scene XRef Merging Iteration "+ scenexrefdepth as string + " - "+ (if done then "DONE!" else (numberOfFilesToMerge as string + " file(s) left.") ) )   )catch()
						)--end for while loop
					)--end if merge scene xrefs
					
					if SMTDSettings.MergeXRefsOnSubmission do 
					(
						for i = objXRefMgr.recordCount to 1 by -1 do 
						(							
							local theRecord = objXRefMgr.GetRecord i
							local theSourceFileName = theRecord.srcFileName 
							if theRecord.enabled then --merge only the enabled XRef objects
							(
								local result = objXRefMgr.MergeRecordIntoScene theRecord 
								if result == true then
								(
									try(SMTD_MainRollout.Ui_report ("+Merged XRef Object Record "+ i as string + " ["+ theSourceFileName+"]")	)catch()
								)
								else
								(
									try(SMTD_MainRollout.Ui_report ("!!FAILED to Merge XRef Object Record "+ i as string + " ["+ theSourceFileName+"]")	)catch()
									SMTDSettings.nonFatalErrorsCount+=1
								)
							)
							else --if disabled, remove the record to avoid surprises at render time
							(
								theRecord.enabled = true --have to enable it before removing?! WTF Autodesk?
								local result = objXRefMgr.RemoveRecordFromScene theRecord --remove disabled record
								if result == true then
								(
									try(SMTD_MainRollout.Ui_report ("+Removed Disabled XRef Object Record "+ i as string + " ["+ theSourceFileName+"]")	)catch()
								)
								else
								(
									theRecord.enabled = false
									try(SMTD_MainRollout.Ui_report ("!!FAILED to Remove Disabled XRef Object Record "+ i as string + " ["+ theSourceFileName+"]")	)catch()
									SMTDSettings.nonFatalErrorsCount+=1
								)
							)
						)--end i loop
					)
				)	
			)	
			
			try(SMTD_MainRollout.Ui_report ">Checking For Missing External Files..."	)catch()
			SMTDFunctions.checkForMissingMaps()
			
			-- Only warn about missing files if we're not submitting from RPM. Don't want to prompt them each time.
			if warnAboutMissingFiles and SMTDSettings.MissingFiles.count > 0 then
			(
				try(SMTD_MainRollout.Ui_report ">Missing Files:")catch()
				for i in SMTDSettings.MissingFiles do 
					try(SMTD_MainRollout.Ui_report ("   " + i ))catch()
				local txt = if SMTDSettings.MissingFiles.count == 1 then "File" else "Files"
				local theMessage = "The Scene Contains "+  SMTDSettings.MissingFiles.count as string +" Missing External "+ txt + ".\n\n"
				if SMTDSettings.WarnAboutMissingExternalFiles then
				(
					if SMTDSettings.IgnoreMissingExternalFiles then
					(
						theMessage += "The 'Ignore Missing External File Errors' option is checked - \n"
						theMessage += "The job will render successfully but incorrectly!\n\n"
					)
					else
					(	
						theMessage += "The 'Ignore Missing External File Errors' option is NOT checked -\n"
						theMessage += "The job will not render correctly. It is suggested to cancel the submission\n\n!"
					)	
					
					theMessage += "Press Yes to Continue Submission.\nPress No to Cancel Submission and Correct the Problems."
					local theAnswer = querybox theMessage title:"SMTD: Missing External Files"
					if not theAnswer do return "--Submission Canceled by User - Missing External Files Found!"
				)
			)				

			queryExternalFiles = true
			local theBitmapsFileName = ""
			if SMTDSettings.CurrentRepository == "" do
			(
				if SMTDSettings.SubmitExternalFilesMode > 1 do
				(
					try(SMTD_MainRollout.Ui_report ">Collecting External Files..."	)catch()
					if maxfilepath != "" do sysinfo.currentdir = maxfilepath --this sets the current directory to the location of the MAX file, so if the bitmaps are stripped of paths, it would resolve them using the MAX source directory
					if SMTD_externalResourcesMode == #legacy then --use the old asset collection code
					(
						bitmapFilenames = SMTDFunctions.returnAllBitmaps() --get the list of files
						local BitmapsCopyData = SMTDFunctions.GetExternalFilesToCopy() --collect the files to be copied with the job
					)
					else --if the new Asset Tracker mode was requested
					(
						bitmapFilenames = SMTDFunctions.resolveAssetsFromAssetTracker SubmitExternalFilesMode:SMTDSettings.SubmitExternalFilesMode --get the file list from the Asset Tracker
						local BitmapsCopyData = for f in bitmapFilenames collect #(f, f) --and build a bitmap copy list from it
						local animaData = SMTDFunctions.ExportAnima2Anipack() --save Anima2 anipacks and get the assets back
						for o in animaData do append BitmapsCopyData #(o, o) --add the collected anipacks to the assets list for copying
					)
					/*if SMTDSettings.SubmitExternalFilesMode == 4 then
					(
						theBitmapsFileName = SMTDFunctions.createExternalFilesList bitmapFilenames
					)
					else*/
					(
						local sizeInMB = 0.0
						for b in BitmapsCopyData do
							sizeInMB += getFileSize b[1]
						sizeInMB /= 1024.0*1024.0
						local txt = if BitmapsCopyData.count == 1 then "File" else "Files"
						try(SMTD_MainRollout.Ui_report ("+Found "+ BitmapsCopyData.count as string +" External "+ txt +" with "+ sizeInMB as string +" MB."))catch()
						if SMTDSettings.ExternalFilesWarningOn AND (BitmapsCopyData.count > SMTDSettings.ExternalFilesWarningCount or sizeInMB > SMTDSettings.ExternalFilesWarningMB) do
							queryExternalFiles = querybox (BitmapsCopyData.count as string + " External "+txt+" (" + sizeInMB as string + " MB) Found In The Scene.\nYou have requested to submit External Files to the Repository.\nDo you want to continue?") title:"Submit To Deadline: External Files Found"
					)	
				)
			)
			
			if not queryExternalFiles then
			(
				try(SMTD_MainRollout.sld_lastSubmissionState.color = red*0.5; SMTD_MainRollout.sld_lastSubmissionState.value = 100.0)catch()
				if backupSceneFileSaved == true then
				(
					try(SMTD_MainRollout.Ui_report ">Restoring Original Scene From Backup File..."	)catch()
					SMTDFunctions.RestoreMaxFileCopy SMTDPaths.RestoreTempMaxFile
				)				
				else
				(
					try(SMTD_MainRollout.Ui_report ">Restoring Original External File Paths..."	)catch()
					SMTDFunctions.restoreExternalReferencePaths()
				)
				return ("DEADLINE JOB SUBMISSION:\n\nExternal Files Submission Canceled by User.")				
			)
			
			local submitSceneMode = SMTDSettings.SubmitSceneMode															--get the current MAX scene saving mode
			if SMTDSettings.SubmitExternalFilesMode > 1 and BitmapsCopyData.count > 0 and submitSceneMode != #reposave do 	--if submitting external assets is enabled, and assets were found,
			(
				SMTDSettings.SubmitSceneMode = #reposave																	--force the saving of the MAX file in the Repository's Job folder
				SMTDSettings.SubmitSceneNetworkReuseLocation = false 														--lower the scene reuse flag too
				local modeString = "Assets"
				if SMTDSettings.SubmitExternalFilesMode == 2 do modeString = "Local Assets"
				try(SMTD_MainRollout.Ui_report ("!!"+modeString+" will be copied to the Repository."))catch()				--and let the user know
				try(SMTD_MainRollout.Ui_report ("!!Forcing 'SAVE and Submit Current Scene File with the Job to the REPOSITORY' mode."))catch()
				SMTDSettings.nonFatalErrorsCount+=1					
			)
			if SMTDSettings.StrictOutput == true and SMTDSettings.SubmitSceneMode == #networksaveanduse do					--if strict output, and saving to the original path,
			(
				SMTDSettings.SubmitSceneMode = #reposave																	--force the saving of the MAX file in the Repository's Job folder
				SMTDSettings.SubmitSceneNetworkReuseLocation = false 														--lower the scene reuse flag too
				try(SMTD_MainRollout.Ui_report ("!!'Force Strict Output Naming' is checked!"))catch()						--and let the user know...
				try(SMTD_MainRollout.Ui_report ("!!Forcing 'SAVE and Submit Current Scene File with the Job to the REPOSITORY' mode."))catch()
				SMTDSettings.nonFatalErrorsCount+=1					
			)
			
			-- need to close State Sets UI if open to stop crash when 3dsMax running via service
			local oldSSDialogState = False
			try
			(
				local ssP = try(dotNetObject "Autodesk.Max.StateSets.Plugin")catch(undefined)
				if ssP == undefined do ssP = try(dotNetObject "Ephere.Plugins.Autodesk.Max.Zookeeper.Plugin")catch(undefined)
				if ssP != undefined then
				(
					local ssPi = ssP.Instance

					oldSSDialogState = try(ssPi.IsMainFrameVisible)catch(undefined) --IsMainFrameVisible not implemented in < Max2015, so return undefined, so we close but not restore dialog

					if oldSSDialogState != undefined AND oldSSDialogState then
					(
						--Max 2015 Ext2 added "Sequencer Mode..." to State Sets
						if (hasProperty ssPi "IsInSequencerMode") AND ssPi.IsInSequencerMode then
						(
							ssPi.ToggleMainFrame()
							ssPi.HideMainFrame()
							try(SMTD_MainRollout.Ui_report "+State Sets [Sequencer Mode...] Exited and Dialog Closed.")catch()
							try(SMTD_MainRollout.Ui_report "+State Sets Dialog Closed.")catch()
						)
						else if (hasProperty ssPi "IsInSequencerMode") AND (not ssPi.IsInSequencerMode) then
						(
							ssPi.HideMainFrame()
							try(SMTD_MainRollout.Ui_report "+State Sets Dialog Closed.")catch()
						)
						
						--earlier than Max2015
						if not (hasProperty ssPi "IsInSequencerMode") then
						(
							ssPi.HideMainFrame()
							try(SMTD_MainRollout.Ui_report "+State Sets Dialog Closed.")catch()
						)
					)
					else
					(
						ssPi.HideMainFrame()
						try(SMTD_MainRollout.Ui_report "+State Sets Dialog Closed.")catch()
					)
				)
			)
			catch()
			
			-- need to close scene explorers to workaround a problem (2008 to 2014)
			local oldSceneExplorerStates = #()
			if ((maxVersion())[1] >= 10000) AND ((maxVersion())[1] < 17000) do
			(
				SceneExplorerManager.CloseManageInstancesDialog()
				for i = 1 to SceneExplorerManager.GetExplorerCount() do
				(
					local name = SceneExplorerManager.GetExplorerName i
					local visible = SceneExplorerManager.ExplorerIsOpen name
					append oldSceneExplorerStates visible
					if visible do SceneExplorerManager.CloseExplorer name
				)
			)
			
			local oldMeditLockedState = renderers.medit_locked --get the locked state of the Medit renderer
			if oldMeditLockedState == true and SMTDSettings.UnlockMEditRenderer == true do 
			(
				renderers.medit_locked = false --if locked, unlock it. This was requested by Jon Reynolds to fix problems with VRay 1.5, might not be needed in general but does not hurt either.
				try(SMTD_MainRollout.Ui_report "+Unlocked the Material Editor Renderer.")catch()
			)	
			if SMTDSettings.ClearMaterialEditorOnSubmission do 
			(
				oldMatEditorOpenState = MatEditor.isOpen()
				if oldMatEditorOpenState do MatEditor.Close()
				try(SMTD_MainRollout.Ui_report "+Closed Material Editor...")catch()
				SMTDFunctions.clearMaterialEditor()
				try(SMTD_MainRollout.Ui_report "+Cleared Material Editor...")catch()
			)	
			
			if not SMTDSettings.RenderElementNamesPermanentChanges do 
			(
				try(SMTD_MainRollout.Ui_report ">Storing the Render Elements Names...")catch()
				SMTDFunctions.storeRenderElementNames() --Store original Render Element names for later restoration
			)

			try(SMTD_MainRollout.Ui_report ">Purifying the Render Elements Names...")catch()
			SMTDFunctions.fixRenderElementNames() --remove spaces and other unwanted characters from Render Element instance names
			
			-- CHECK VRAY VFB if not bake job
			if not SMTDSettings.IsBakeJob then
			(
				/*
				if SMTDFunctions.getRendererIdString() == "vray" do
				(
					if renderers.current.output_on and renderers.current.output_saveRawFile then
					(
						-- If tiled exrs are being rendered, automatically disable the memory frame buffer
						oldVRayVFBState = renderers.current.output_useram
						renderers.current.output_useram = false
						SMTD_MainRollout.Ui_report "+Disabled V-Ray Frame Buffer rendering to RAM."
					)
					else
					(
						-- Otherwise, just disable the vray vfb entirely
						oldVRayVFBState = renderers.current.output_on
						renderers.current.output_on = false
						SMTD_MainRollout.Ui_report "+Disabled V-Ray Frame Buffer."
						
						SMTDFunctions.RenderElementsStoreVrayVFB()
						SMTDFunctions.RenderElementsUpdateVrayVFB()
					)
				)
				*/
			)
			else
			(
				oldMaxScriptFile = SMTDSettings.SubmitAsMXSJob
				oldSubmitMaxScript = SMTDSettings.MAXScriptFile
				
				SMTDSettings.SubmitAsMXSJob = true
				SMTDSettings.MAXScriptFile = SMTDPaths.MainSubmissionDir+"\\TextureBake.ms"
				
				try(SMTD_MainRollout.Ui_report "+Overwriting MaxScript Job Settings.")catch()
			)
			
			--FORCE HIGH PRIORITY THREAD
			if SMTDSettings.OverrideLowPriorityThread do
			(
				try (
					VRAY_lowThreadPriority = renderers.current.system_lowThreadPriority
					if VRAY_lowThreadPriority do  (
					renderers.current.system_lowThreadPriority = false
					SMTD_MainRollout.Ui_report ("+Forcing V-Ray Low Thread Priority to [false].")
					)
				)catch() 
				try (
					BRAZIL_lowThreadPriority = renderers.current.low_priority_thread_on
					if BRAZIL_lowThreadPriority do (
					renderers.current.low_priority_thread_on = false
					SMTD_MainRollout.Ui_report ("+Forcing Brazil r/s Low Thread Priority to [false].")
					)
				)catch() 
			)

			local oldrendOutputFilename = rendOutputFilename --capture the current output filename
			if SMTDSettings.ReplaceOutputFilenameWithUserPattern do
			(
				OutputFilenameByUserPattern = copy SMTDSettings.OutputFilenameUserPattern
				OutputFilenameByUserPattern = substituteString OutputFilenameByUserPattern "$user" SMTDSettings.userName
				local theMaxFileName = (getFileNameFile maxFileName)
				if theMaxFileName == "" do theMaxFileName = "Untitled"
				OutputFilenameByUserPattern = substituteString OutputFilenameByUserPattern "$scene" theMaxFileName
				
				local theFilterTime = filterString localtime " /\\-:."
				local theTime = ""
				for i = 1 to theFilterTime.count-1 where (classof (execute theFilterTime[i]) != Integer) do deleteItem theFilterTime i
				for i = 1 to theFilterTime.count-1 do theTime += theFilterTime[i] + "_"
				theTime += theFilterTime[theFilterTime.count]	
				OutputFilenameByUserPattern = substituteString OutputFilenameByUserPattern "$date" theTime
				OutputFilenameByUserPattern = substituteString OutputFilenameByUserPattern "$" "_"
				makeDir (getFileNamePath OutputFilenameByUserPattern) all:true
				if doesFileExist (getFileNamePath OutputFilenameByUserPattern) do
				(
					rendOutputFilename = OutputFilenameByUserPattern
				)
			)	

			if SMTDSettings.RebuildRenderElements do
			(
				try(SMTD_MainRollout.Ui_report ">Rebuilding Render Elements")catch()
				SMTDFunctions.RebuildRenderElements()
				try(SMTD_MainRollout.Ui_report "+Rebuilt Render Elements")catch()
			)

			local retcode = #success		
			
			if SMTDSettings.StrictOutput == true then
			(
				if RendOutputFilename != "" then
				(						   
					try(SMTD_MainRollout.Ui_report ">Strict Output Check...")catch()
					local theRenderPath = getFilenamePath RendOutputFilename
					local directory = getFilenameFile maxFilename
					local filename = getFilenameFile maxFilename
					local extension = getFilenameType RendOutputFilename
								
					-- if the output path already contains the max filename, assume that
					-- it already contains the correct directory structure, so we don't keep
					-- appending directories everytime the job is submitted
					if findString theRenderPath directory != undefined then
						RendOutputFilename = theRenderPath + filename + extension
					else
						RendOutputFilename = theRenderPath + directory + "\\" + filename + extension
					try(SMTD_MainRollout.Ui_report ("+Strict Output is ["+RendOutputFilename+"]"))catch()
				)
			)--end strict output
			
			if SMTDSettings.RenderElementsUpdatePaths do
			(
				try(SMTD_MainRollout.Ui_report ">Updating Render Elements Paths..."	)catch()
				if not SMTDSettings.RenderElementsPermanentChanges do 
				(
					SMTDFunctions.RenderElementsStorePaths()
					try(SMTD_MainRollout.Ui_report "+Stored Render Elements Paths."	)catch()
				)	
				SMTDFunctions.RenderElementsUpdatePaths()
				try(SMTD_MainRollout.Ui_report "+Updated Render Elements Paths."	)catch()
			)				
			
			--Output Info about Repository being submitted to
			try
			(
				if SMTDSettings.CurrentRepository != "" then
				(
					SMTD_MainRollout.Ui_report (">Submitting "+ SMTDFunctions.getPluginToUse() +" Render Job to Remote Repository:")
					SMTD_MainRollout.Ui_report ("["+ SMTDSettings.CurrentRepository +"]...")
				)	
				else
					SMTD_MainRollout.Ui_report (">Submitting "+ SMTDFunctions.getPluginToUse() +" Render Job to Local Repository...")
			)catch()		

			local TempMaxFile = ""
			case of
			(
				(SMTDSettings.SubmitSceneMode == #reposave):
				(
					TempMaxFile = SMTDPaths.submitSubFolder + maxFileName
					if maxFileName == "" do TempMaxFile += "untitled.max"
					if (doesFileExist TempMaxFile) do deleteFile TempMaxFile
				)
				(SMTDSettings.SubmitSceneMode == #networksaveanduse):
				(
					if SMTDSettings.SubmitSceneNetworkReuseLocation == false do
					(
						if maxFileName == "" then
						(
							filename = getMAXSaveFileName()
							if filename == undefined do return "--Submission Canceled by User - scene must be saved before submission"
							
							TempMaxFile = filename
						)
						else
							TempMaxFile = maxFilePath + maxFileName
						if not SMTDSettings.StateSetsSubmit AND SMTDSettings.DeleteEmptyStateSets do SMTDFunctions.DeleteEmptyStateSets()
						saveMaxFile TempMaxFile
					)
				)
				(SMTDSettings.SubmitSceneMode == #networksave OR SMTDSettings.SubmitSceneMode == #globalnetworksave):
				(
					if SMTDSettings.SubmitSceneNetworkReuseLocation == false or SMTDSettings.SubmitSceneNetworkLocation == "" then --if saving requested, or last saved file name not defined
					(
						local theFilterTime = filterString localtime " /\\-:."
						local theTime = ""
						for i = 1 to theFilterTime.count-1 where (classof (execute theFilterTime[i]) != Integer) do deleteItem theFilterTime i
						for i = 1 to theFilterTime.count do theTime += theFilterTime[i] + "_"
						if SMTDSettings.SubmitSceneMode == #networksave then
							TempMaxFile = SMTDSettings.SubmitSceneBasePath +"\\"+SMTDSettings.userName+"\\"+theTime+"\\"
						else
							TempMaxFile = SMTDSettings.SubmitSceneGlobalBasePath +"\\"+SMTDSettings.userName+"\\"+theTime+"\\"
						makedir TempMaxFile all:true
						TempMaxFile += (if maxFileName == "" then "untitled.max" else maxFileName)
						SMTDSettings.SubmitSceneNetworkLocation = TempMaxFile
					)
					else
						TempMaxFile = SMTDSettings.SubmitSceneNetworkLocation
				)
				(SMTDSettings.SubmitSceneMode == #networkremap): ( )				
			)

			if SMTDSettings.SubmitSceneMode != #networkuse and SMTDSettings.SubmitSceneMode != #networksaveanduse and SMTDSettings.SubmitSceneMode != #networkremap and SMTDSettings.SubmitSceneNetworkReuseLocation == false then
			(
				if SMTDSettings.UseCustomShader do
				(
					try(SMTD_MainRollout.Ui_report ">Applying Custom Shaders...")catch()
					SMTDFunctions.CollectSceneMaterials()
					SMTDFunctions.assignCustomShaders()
				)

				if SMTDSettings.SubmitVisibleObjectsOnly and not SMTDFunctions.HasActiveSceneXRefs() then
				(
					try(SMTD_MainRollout.Ui_report (">Saving Visible Objects For Submission to ["	+ TempMaxFile + "]"))catch()
					result = SMTDFunctions.SaveMaxFileVisibleOnly TempMaxFile
				)	
				else
				(
					try(SMTD_MainRollout.Ui_report (">Saving Scene For Submission to ["	+ TempMaxFile + "]"))catch()
					result = SMTDFunctions.SaveMaxFileCopy TempMaxFile
				)	
				
				if SMTDSettings.UseCustomShader do
				(
					try(SMTD_MainRollout.Ui_report ">Restoring Scene Shaders...")catch()
					SMTDFunctions.restoreSceneMaterials()
				)
			)
			else result = undefined
	
			if result != undefined do return result
			
			if RendOutputFilename != "" and SMTDSettings.CreateImsqFile then
			(
				try(SMTD_MainRollout.Ui_report ">Creating Image Sequence File...")catch()
				path = getFilenamePath RendOutputFilename
				filename = getFilenameFile RendOutputFilename
				imsqFilename = path + filename + ".imsq"
				if ((SMTDFunctions.CreateImsqFile imsqFilename) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Image Sequence file"
				
				if SMTDSettings.CopyImsqFile and SMTDSettings.ImsqOutputPath != "" then
				(
					if ((SMTDFunctions.CreateImsqVbscript SMTDPaths.ImsqVbscriptFile imsqFilename) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Image Sequence Vbscript file"
					SMTDSettings.CopyVbscriptFile = true
				)										   
			)
			
			try(SMTD_MainRollout.sld_lastSubmissionState.color = yellow)catch()

			local oldStereoPriority = SMTDSettings.Priority
			
			--TILE/REGION SUBMISSION
			if findItem #(#singleFrameTiles,#singleFrameMultiRegion, #animationMultiRegion) SMTDSettings.RegionRenderingMode > 0 then
			(
				try(SMTD_MainRollout.Ui_report ">Initiating Tiles Submission...")catch()
				result = SMTDFunctions.spawnTileJobs forceMaxFile:TempMaxFile batchName:batchName forceCamera:forceCamera stereoCameraLabel:stereoCameraLabel
				if result then retCode = #success else retCode = #tileFailure
				renderMsg = SMTDFunctions.getRenderMessage()
			)
			else --REGULAR SUBMISSION
			(
				try(SMTD_MainRollout.Ui_report ">Initiating Regular Job Submission...")catch()
				local initialArgs = "" as stringstream
				format "-outputfiles\n%\n%\n" SMTDPaths.SubmitOutput  SMTDPaths.SubmitExitCode to:initialArgs
				
				if SMTDSettings.bgSubmission do format "-background\n-notify\n" to:initialArgs
				if SMTDSettings.dropSubmission do format "-drop\n" to:initialArgs 
				
				if( SMTDSettings.SubmitSceneMode == #reposave ) then
					format "%\n%\n%\n" SMTDPaths.SubmitInfoFile SMTDPaths.JobInfoFile  TempMaxFile  to:initialArgs 
				else
					format "%\n%\n" SMTDPaths.SubmitInfoFile SMTDPaths.JobInfoFile  to:initialArgs 
				
				--If scripts enabled, send the script files as aux. files:
				if SMTDSettings.SubmitAsMXSJob then
				(
					format "%\n" SMTDSettings.MAXScriptFile to:initialArgs 
					try(SMTD_MainRollout.Ui_report "+This is a MAXScript Job!")catch()
				)
				else
				(
					/*
					if SMTDSettings.SubmitExternalFilesMode == 4 then
					(
						for aBitmap in BitmapsCopyData where findItem SMTDSettings.MissingFiles aBitmap[1] == 0 do
						format "\"%\" \n" aBitmap[1] to:initialArgs
						--initialArgs += "\"" + theBitmapsFileName + "\" " 
						SMTDSettings.RunPreLoadScript = true
						SMTDSettings.PreLoadScriptFile = SMTDPaths.MainSubmissionDir + "\\DeadlineMaxCacheTexturesOnSlave_PreLoad.ms"
						--initialArgs += "\"" +SMTDSettings.PreLoadScriptFile+ "\" " 
					)	
					*/
					
					if SMTDSettings.CopyVbscriptFile do format "%\n" SMTDPaths.ImsqVbscriptFile to:initialArgs
					if SMTDSettings.RunPreLoadScript do format "%\n" SMTDSettings.PreLoadScriptFile to:initialArgs
					if SMTDSettings.RunPostLoadScript do format "%\n" SMTDSettings.PostLoadScriptFile to:initialArgs
					if SMTDSettings.RunPreFrameScript do format "%\n" SMTDSettings.PreFrameScriptFile to:initialArgs
					if SMTDSettings.RunPostFrameScript do format "%\n" SMTDSettings.PostFrameScriptFile to:initialArgs
					if SMTDSettings.SubmitSceneMode == #reposave do
					(
						if SMTDSettings.UsePathConfigFile and doesFileExist SMTDSettings.PathConfigFile do format "%\n" SMTDSettings.PathConfigFile to:initialArgs
					)
			
					if SMTDSettings.UseBatchRender and SMTDSettings.BatchRenderMode == 2 do 
					(
						try(SMTD_MainRollout.Ui_report ">Batch Master Job - Adding Batch Submitter Script To Auxiliary File")catch()
						local theNetworkPath = SMTDPaths.MainSubmissionDir + "\\"
						format "%\n" (theNetworkPath + "maxBatchSubmitter.ms") to:initialArgs 
						
						local numViews = batchRenderMgr.numViews 
						for i = 1 to numViews do
						(
							local theView = batchRenderMgr.getView i
							if theView.enabled and theView.presetFile != "" do
								format "%\n" theView.presetFile to:initialArgs 
						)
						
						theBitmapsFileName = SMTDFunctions.createExternalFilesList bitmapFilenames
						format "%\n" (theBitmapsFileName) to:initialArgs 
					)	
					if (SMTDSettings.UseBatchRender and SMTDSettings.BatchRenderMode == 2) do  --SMTDSettings.TilesRendering or 
					(
						try(SMTD_MainRollout.Ui_report ">Master Job - Saving SMTD Struct Settings To Auxiliary File...")catch()
						SMTDFunctions.saveSettingsStructToMSFile (getFileNamePath SMTDPaths.JobInfoFile + "SubmitterSettingsStruct.ms")
						format "%\n" (getFileNamePath SMTDPaths.JobInfoFile + "SubmitterSettingsStruct.ms") to:initialArgs 
					)
				)	

				if externalFilesList != "" then
				(
					local theEFLFile = openFile externalFilesList
					if theEFLFile != undefined do
					(
						while not eof theEFLFile do 
						(
							local theLine = readLine theEFLFile 
							format "%%\n" (getFileNamePath externalFilesList) (filenamefrompath theLine) to:initialArgs
						)
						close theEFLFile
					)
				)
				else
				(
					--Output external files to the command line for copying
					if SMTDSettings.SubmitExternalFilesMode > 1 do				
						for aBitmap in BitmapsCopyData where findItem SMTDSettings.MissingFiles aBitmap[2] == 0 do
							format "%\n" aBitmap[2] to:initialArgs
				)
				
				local initialArgsFileName = (getFileNamePath SMTDPaths.JobInfoFile + "initialArgsFile.txt") 
				local initialArgsFile = createFile initialArgsFileName encoding:#utf8 writeBOM:true
				format "%\n" (initialArgs as string) to:initialArgsFile
				close initialArgsFile 
				initialArgsFileName = "\""+initialArgsFileName+"\""
					
				--CHANGE PRIORITY FOR STEREO CAMERAS
				case SMTDSettings.StereoCameraPriorityOrder	of
				(
					#lrc: ( --left right center
						if stereoCameraLabel == SMTDSettings.RightEyeTag do SMTDSettings.Priority -= 1
						if stereoCameraLabel == SMTDSettings.CenterEyeTag do SMTDSettings.Priority -= 2
					)
					#rlc: ( --right left center
						if stereoCameraLabel == SMTDSettings.LeftEyeTag do SMTDSettings.Priority -= 1
						if stereoCameraLabel == SMTDSettings.CenterEyeTag do SMTDSettings.Priority -= 2
					)
					#clr: ( --center left right 
						if stereoCameraLabel == SMTDSettings.LeftEyeTag do SMTDSettings.Priority -= 1
						if stereoCameraLabel == SMTDSettings.RightEyeTag do SMTDSettings.Priority -= 2
					)					
					#crl: ( --center right left 
						if stereoCameraLabel == SMTDSettings.RightEyeTag do SMTDSettings.Priority -= 1
						if stereoCameraLabel == SMTDSettings.LeftEyeTag do SMTDSettings.Priority -= 2
					)	
					#lcr: ( --left center right
						if stereoCameraLabel == SMTDSettings.CenterEyeTag do SMTDSettings.Priority -= 2
						if stereoCameraLabel == SMTDSettings.RightEyeTag do SMTDSettings.Priority -= 2
					)	
					#rcl: ( --right center left 
						if stereoCameraLabel == SMTDSettings.CenterEyeTag do SMTDSettings.Priority -= 1
						if stereoCameraLabel == SMTDSettings.LeftEyeTag do SMTDSettings.Priority -= 2
					)						
				)
				if SMTDSettings.Priority < 0 do SMTDSettings.Priority = 0
				
				--IF FRAMES PREVIEW JOB REQUESTED, SUBMIT TWO JOBS - ONE FOR EVERY NTH, ONE FOR THE REST
				if SMTDFunctions.canSubmitPreviewJob TilesRendering MultiRegionRendering then
				(
					try(SMTD_MainRollout.Ui_report ">Submitting Two Jobs: Frame Preview and Remaining Frames...")catch()
					oldPriority = SMTDSettings.Priority
					SMTDSettings.Priority += SMTDSettings.PreviewJobPriorityOffset
					if SMTDSettings.Priority > SMTDSettings.MaximumPriority do SMTDSettings.Priority = SMTDSettings.MaximumPriority -- max. value used to be hard-coded to 100, now is variable
					if SMTDSettings.Priority < 0 do SMTDSettings.Priority = 0
					
					--if ((SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile frameMode:#nth) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Submit Info file"
					local result = false
					--if (SMTDFunctions.getRendererIdString() == "vray" and renderers.current.output_on and renderers.current.output_rawFileName != undefined and renderers.current.output_rawFileName != "" ) then
					--	result = SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile customOutputFile:renderers.current.output_rawFileName includeBothOutputs:true frameMode:#nth
					--else
					--	result = SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile frameMode:#nth
					
					result = SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile frameMode:#nth batchName:batchName stereoCameraLabel:stereoCameraLabel
					if not result do return "DEADLINE JOB SUBMISSION:\n\nCould not create Submit Info file"
					
					if ((SMTDFunctions.CreateJobInfoFile SMTDPaths.JobInfoFile forceCamera:forceCamera stereoCameraLabel:stereoCameraLabel) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Job Info file"
					
					
					try(SMTD_MainRollout.Ui_report ">Submitting Frame Preview Job...")catch()
					retcode = SMTDFunctions.waitForCommandToComplete initialArgsFileName SMTDSettings.TimeoutSubmission paramIsFile:true
					SMTDSettings.Priority = oldPriority 
					renderMsg = SMTDFunctions.getRenderMessage()
					SMTDFunctions.getJobIDFromMessage renderMsg
					if retCode == #success then
					(
						try(SMTD_MainRollout.Ui_report ("Frames Preview Job Submitted Successfully.\n\n" + renderMsg) )catch()
						
						if SMTDSettings.AssetsPreCacheFiles == true AND SMTDSettings.AssetsIncludeFilesInJob == true then
						(
							local PrecacheResults = SMTDFunctions.CallDeadlineCommandInMemory ("-AWSPortalPrecacheJob " + SMTDSettings.DeadlineSubmissionLastJobID ) multiLine:true
							try(SMTD_MainRollout.Ui_report (">AWS Portal Pre-Cache Results: \n\n"+PrecacheResults))catch()
						)
									
						--SMTDFunctions.CopyExternalFilesToRepository() --copy files to preview job
						SMTDFunctions.SubmitTransferJob() -- submits a remote transfer job if necessary
						
						--if ((SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile frameMode:#rest) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Submit Info file"
						local result = false
						--if (SMTDFunctions.getRendererIdString() == "vray" and renderers.current.output_on and renderers.current.output_rawFileName != undefined and renderers.current.output_rawFileName != "" ) then
						--	result = SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile customOutputFile:renderers.current.output_rawFileName includeBothOutputs:true frameMode:#rest
						--else
						--	result = SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile frameMode:#rest
						result = SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile frameMode:#rest batchName:batchName
						if not result do return "DEADLINE JOB SUBMISSION:\n\nCould not create Submit Info file"
						
						try(SMTD_MainRollout.Ui_report ">Submitting Remaining Frames Job...")catch()
						retcode = SMTDFunctions.waitForCommandToComplete initialArgsFileName SMTDSettings.TimeoutSubmission paramIsFile:true
						renderMsg = SMTDFunctions.getRenderMessage()
						SMTDFunctions.getJobIDFromMessage renderMsg
						if retCode == #success then
						(
							try(SMTD_MainRollout.Ui_report ("Remaining Frames Job submitted successfully.\n\n" + renderMsg) )catch()
							
							if SMTDSettings.AssetsPreCacheFiles == true AND SMTDSettings.AssetsIncludeFilesInJob == true then
							(
								local PrecacheResults = SMTDFunctions.CallDeadlineCommandInMemory ("-AWSPortalPrecacheJob " + SMTDSettings.DeadlineSubmissionLastJobID ) multiLine:true
								try(SMTD_MainRollout.Ui_report (">AWS Portal Pre-Cache Results: \n\n"+PrecacheResults))catch()
							)
									
							--SMTDFunctions.CopyExternalFilesToRepository() --copy files to main job
							SMTDFunctions.SubmitTransferJob() -- submits a remote transfer job if necessary
						)	
						else
						(
							try(SMTD_MainRollout.Ui_report ("Remaining Frames Job Submission FAILED.\n\n" + renderMsg) )catch()
						)
					)	
					else
					(
						try(SMTD_MainRollout.Ui_report ("Frames Preview Job Submission FAILED.\n\n" + renderMsg) )catch()
					)
				)
				
				else  --otherwise submit just one job
				(
					try(SMTD_MainRollout.Ui_report ">Submitting All Frames In One Job...")catch()
					
					--if ((SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Submit Info file"
					local result = false
					--if (SMTDFunctions.getRendererIdString() == "vray" and renderers.current.output_on and renderers.current.output_rawFileName != undefined and renderers.current.output_rawFileName != "" ) then
					--	result = SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile customOutputFile:renderers.current.output_rawFileName includeBothOutputs:true
					--else
					--	result = SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile
					result = SMTDFunctions.CreateSubmitInfoFile SMTDPaths.SubmitInfoFile batchName:batchName stereoCameraLabel:stereoCameraLabel
					if not result do return "DEADLINE JOB SUBMISSION:\n\nCould not create Submit Info file"
					
					if ((SMTDFunctions.CreateJobInfoFile SMTDPaths.JobInfoFile forceCamera:forceCamera stereoCameraLabel:stereoCameraLabel) != true) do return "DEADLINE JOB SUBMISSION:\n\nCould not create Job Info file"
					
					try(SMTD_MainRollout.Ui_report ("Command Line Arguments: ["+initialArgs+"]\n\n"))catch()
					retCode = SMTDFunctions.waitForCommandToComplete initialArgsFileName SMTDSettings.TimeoutSubmission paramIsFile:true
					renderMsg = SMTDFunctions.getRenderMessage()
					SMTDFunctions.getJobIDFromMessage renderMsg 
					if retCode == #success do
					(
						if SMTDSettings.AssetsPreCacheFiles == true AND SMTDSettings.AssetsIncludeFilesInJob == true then
						(
							local PrecacheResults = SMTDFunctions.CallDeadlineCommandInMemory ("-AWSPortalPrecacheJob " + SMTDSettings.DeadlineSubmissionLastJobID ) multiLine:true
							try(SMTD_MainRollout.Ui_report (">AWS Portal Pre-Cache Results: \n\n"+PrecacheResults))catch()
						)
						--SMTDFunctions.CopyExternalFilesToRepository()
						SMTDFunctions.SubmitTransferJob() -- submits a remote transfer job if necessary
						
						--Auto-Dependencies
						
						append SMTDSettings.PreviousJobsArray #(SMTDSettings.JobName,SMTDSettings.DeadlineSubmissionLastJobID,"3dsmax",SMTDSettings.UserName,SMTDSettings.Department,SMTDSettings.Group, "Previous")
						try(::SMTD_Dependencies.updateDependencyDisplay())catch()
					)
				)
			)--end if not local tiles submission
			
			if not oldRendUseActiveView do 
			(
				rendUseActiveView = false --restore viewport lock if it used to be engaged. Won't be touched if it used to be TRUE (unchecked) anyway
				try(SMTD_MainRollout.Ui_report "+Restored the Render View Lock.")catch()
			)
			SMTDSettings.SubmitSceneMode = submitSceneMode --restore the submit scene mode if it was overridden
			SMTDSettings.Priority = oldStereoPriority
			
			--If the merging of XRef objects was requested and there were any, restore the copy of the scene from the temp. file
			if backupSceneFileSaved == true then
			(
				try(SMTD_MainRollout.Ui_report ">Restoring Original Scene From Backup File..."	)catch()
				SMTDFunctions.RestoreMaxFileCopy SMTDPaths.RestoreTempMaxFile
			)
			else --we only need to restore the paths if the scene was not restored from a temp. file
			(
				if SMTDSettings.SubmitExternalFilesMode > 1 and not (SMTDSettings.UseBatchRender AND  SMTDSettings.BatchRenderMode == 1) do --and SMTDSettings.SubmitExternalFilesMode < 4
				(
					try(SMTD_MainRollout.Ui_report ">Restoring Original External File Paths..."	)catch()
					SMTDFunctions.restoreExternalReferencePaths()
				)	
			)
			
			if oldMeditLockedState == true and SMTDSettings.UnlockMEditRenderer == true do 
			(
				renderers.medit_locked = true --if the MEdit renderer was previously locked, lock it again.
				try(SMTD_MainRollout.Ui_report "+Restored the Locked State of the Material Editor Renderer.")catch()
			)
			
			if ((maxVersion())[1] >= 10000) AND ((maxVersion())[1] < 17000) do
			(
				for i = 1 to SceneExplorerManager.GetExplorerCount() do
				(
					if oldSceneExplorerStates[i] do
					(
						local name = SceneExplorerManager.GetExplorerName i
						SceneExplorerManager.OpenExplorer name
					)
				)
			)
			
			--restore Anima2 paths
			SMTDFunctions.restoreAnima2Paths()
			
			--restore the output file name if changed by global pattern, or by strict output
			if SMTDSettings.ReplaceOutputFilenameWithUserPattern or SMTDSettings.StrictOutput == true do
			(
				rendOutputFilename = oldrendOutputFilename
			)
			
			if oldRenderDialogState do 
			(
				renderSceneDialog.Open() 
				try(SMTD_MainRollout.Ui_report "+Restored the Open State of the Render Scene Dialog.")catch()
			)

			--restore state sets dialog if open
			if oldSSDialogState != undefined AND oldSSDialogState do
			(
				try
				(
					ssP = try(dotNetObject "Autodesk.Max.StateSets.Plugin")catch(undefined)
					if ssP == undefined do ssP = try(dotNetObject "Ephere.Plugins.Autodesk.Max.Zookeeper.Plugin")catch(undefined)
					if ssP != undefined then
					(
						ssPi = ssP.Instance
						ssPi.ShowMainFrame()
						try(SMTD_MainRollout.Ui_report "+Restored the Open State of the State Sets Dialog.")catch()
					)
				)
				catch()
			)

			if SMTDSettings.ClearMaterialEditorOnSubmission do 
			(
				SMTDFunctions.restoreMaterialEditor()
				try(SMTD_MainRollout.Ui_report "+Restored the Material Editor Samples...")catch()
				if oldMatEditorOpenState do 
				(
					MatEditor.Open()
					try(SMTD_MainRollout.Ui_report "+Restored the Material Editor open state."	)catch()
				)
			)
			
			if not SMTDSettings.IsBakeJob then
			(
				/*
				if SMTDFunctions.getRendererIdString() == "vray" do
				(
					if renderers.current.output_on and renderers.current.output_saveRawFile then
					(
						if oldVRayVFBState do
						(
							renderers.current.output_useram = true
							try(SMTD_MainRollout.Ui_report "+Reenabled V-Ray Frame Buffer rendering to RAM.")catch()
						)
					)
					else
					(
						if oldVRayVFBState do
						(
							renderers.current.output_on = true
							try(SMTD_MainRollout.Ui_report "+Reenabled V-Ray Frame Buffer.")catch()
						)
						
						SMTDFunctions.RenderElementsRestoreVrayVFB()
					)
				)
				*/
			)
			else
			(
				SMTDSettings.SubmitAsMXSJob = oldMaxScriptFile
				SMTDSettings.MAXScriptFile = oldSubmitMaxScript
				try(SMTD_MainRollout.Ui_report "+Restored MaxScript Job Settings.")catch()
			)
			
			if SMTDSettings.OverrideLowPriorityThread do
			(
				try (
					if VRAY_lowThreadPriority do (
					renderers.current.system_lowThreadPriority = true
					SMTD_MainRollout.Ui_report ("+Restored V-Ray Low Thread Priority to [true].")
					)
				)catch()
				try (
					if BRAZIL_lowThreadPriority do (
					renderers.current.low_priority_thread_on = true
					SMTD_MainRollout.Ui_report ("+Restored Brazil Low Thread Priority to [true].")
					)
				)catch()
			)
			
			if SMTDSettings.RenderElementsUpdatePaths do
			(
				if not SMTDSettings.RenderElementsPermanentChanges do 
				(
					SMTDFunctions.RenderElementsRestorePaths()
					try(SMTD_MainRollout.Ui_report "+Restored the Render Elements Paths.")catch()
				)	
			)	
			
			if not SMTDSettings.RenderElementNamesPermanentChanges do 
			(
				SMTDFunctions.restoreRenderElementNames() --Restore original Render Element names 
				try(SMTD_MainRollout.Ui_report "+Restored the Render Elements Names.")catch()
			)

			case retCode of
			(
				#success:
				(
					local copyResult = 0
					SMTDSettings.DeadlineSubmissionSuccessful = true
					
					if copyResult == 0 then
						try(SMTD_MainRollout.sld_lastSubmissionState.color = green; SMTD_MainRollout.sld_lastSubmissionState.value = 100)catch()
					else	
						try(SMTD_MainRollout.sld_lastSubmissionState.color = red*0.75 + green*0.5; SMTD_MainRollout.sld_lastSubmissionState.value = 100)catch()
						
					try
					(
						local theFn =  (getIniSetting SMTDPaths.InIFile "Scripts"  "PostSubmissionFunction")
						if theFn != "" then
						(
							execute theFn
							try(SMTD_MainRollout.Ui_report ("+Executed Post-Submission Function: "+  theFn) )catch()
						)
					)
					catch
					(
						try(SMTD_MainRollout.Ui_report ("!!Failed To Execute Post-Submission Function: "+  theFn) )catch()
						SMTDSettings.nonFatalErrorsCount+=1
					)	
					--print renderMsg; --FIXME
						
					("+JOB SUBMITTED SUCCESSFULLY.\n\n" + renderMsg)
				)--end success	
				#failed:
				(
					SMTDSettings.FatalErrorsCount+=1
					try(SMTD_MainRollout.sld_lastSubmissionState.color = red; SMTD_MainRollout.sld_lastSubmissionState.value = 100.0)catch()
					("--DEADLINE JOB SUBMISSION FAILED:\n\nFailed to submit job.\n\n" + renderMsg)
				)--end failed	
				#readerror:
				(
					SMTDSettings.FatalErrorsCount+=1
					try(SMTD_MainRollout.sld_lastSubmissionState.color = red; SMTD_MainRollout.sld_lastSubmissionState.value = 100.0)catch()
					("--DEADLINE JOB SUBMISSION FAILED:\n\nRead Error.\n\n" + renderMsg)
				)--end read error
				#timeout:
				(
					SMTDSettings.FatalErrorsCount+=1
					try(SMTD_MainRollout.sld_lastSubmissionState.color = red; SMTD_MainRollout.sld_lastSubmissionState.value = 100.0)catch()
					("--DEADLINE JOB SUBMISSION TIMED OUT AFTER "+ SMTDSettings.TimeoutSubmission as string +" SECONDS!\nConsider increasing the Job Submission Timeout in the User Options tab.\n\n")
				)
				default: 
				(
					SMTDSettings.FatalErrorsCount+=1
					try(SMTD_MainRollout.sld_lastSubmissionState.color = red; SMTD_MainRollout.sld_lastSubmissionState.value = 100.0)catch()
					("--DEADLINE JOB SUBMISSION FAILED FOR UNKNOWN REASON.\n\n")
				)
				#tileFailure: 
				(
					SMTDSettings.FatalErrorsCount+=1
					try(SMTD_MainRollout.sld_lastSubmissionState.color = red; SMTD_MainRollout.sld_lastSubmissionState.value = 100.0)catch()
					("--DEADLINE DISTRIBUTED TILES JOB SUBMISSION FAILED.\n\n") --scroll back up message stack to understand the reason for failure in the SMTD log
				)
				#cancel:
				(
					try(SMTD_MainRollout.sld_lastSubmissionState.color = red; SMTD_MainRollout.sld_lastSubmissionState.value = 100.0)catch()
					("--DEADLINE SUBMISSION CANCELED BY THE USER.\n\n") --scroll back up message stack to understand the reason for failure in the SMTD log
				)
			)--end retCode case
			
		),--end submit job fn	
		
		fn InitializeSubmitInfo =
		(
			local st0 = timestamp()
			::SMTDSettings = copy ::SMTDSettingsFactory --force the SMTDSettings struct to the factory defaults
			SMTDPaths.HomeDir = SMTDPaths.UserHomeDir = getDir #temp + "\\" --default to temp folder in case the following code fails
			SMTDPaths.MainSubmissionDir = SMTDPaths.PluginDir = SMTDPaths.PluginDir3dsmax = SMTDPaths.DraftDir = SMTDPaths.IntegrationDir = ""
			local theSubmissionInfoArray = #()
			local deadlineSubmissionInfo = SMTDFunctions.CallDeadlineCommandInMemory \
					"-GetSubmissionInfo homedir userhomedir pools groups maxpriority tasklimit shortversion repodir:submission/3dsmax/Main repodir:submission/Draft/Main repodir:submission/Integration/Main repodir:plugins/3dsmax false" multiLine:true
			if deadlineSubmissionInfo != "" do theSubmissionInfoArray = filterString deadlineSubmissionInfo "\r\n"
			
			if theSubmissionInfoArray.count > 0 then
			(
				for i = 1 to theSubmissionInfoArray.count where matchPattern theSubmissionInfoArray[i] pattern:"[*]" do theSubmissionInfoArray[i] = toLower theSubmissionInfoArray[i]
				
				local theIndex = findItem theSubmissionInfoArray "[maxpriority]"
				if theIndex > 0 do 
				(
					local val = execute theSubmissionInfoArray[theIndex+1]
					SMTDSettingsDefaults.MaximumPriority = SMTDSettingsFactory.MaximumPriority = SMTDSettings.MaximumPriority = if isKindOf val Number then val else 100
				)
				local theIndex = findItem theSubmissionInfoArray "[tasklimit]"
				if theIndex > 0 do 
				(
					local val = execute theSubmissionInfoArray[theIndex+1]
					SMTDSettingsDefaults.TaskLimit = SMTDSettingsFactory.TaskLimit = SMTDSettings.TaskLimit = if isKindOf val Number then val else 5000
				)	
				local theIndex = findItem theSubmissionInfoArray "[shortversion]"
				if theIndex > 0 do 
				(
					local val = theSubmissionInfoArray[theIndex+1]
					SMTDSettingsDefaults.VersionString = SMTDSettingsFactory.VersionString = SMTDSettings.VersionString = val
				)					
				local theIndex = findItem theSubmissionInfoArray "[homedir]"
				if theIndex > 0 do SMTDPaths.HomeDir = theSubmissionInfoArray[theIndex+1]+ "\\"
					
				local theIndex = findItem theSubmissionInfoArray "[userhomedir]"
				if theIndex > 0 do SMTDPaths.UserHomeDir = theSubmissionInfoArray[theIndex+1]+ "\\"

				local theIndex = findItem theSubmissionInfoArray "[repodir]"
				if theIndex > 0 do 
				(
					SMTDPaths.MainSubmissionDir = theSubmissionInfoArray[theIndex+1]+ "\\"
					SMTDPaths.DraftDir = theSubmissionInfoArray[theIndex+2]+ "\\"
					SMTDPaths.IntegrationDir = theSubmissionInfoArray[theIndex+3]+ "\\"
					SMTDPaths.PluginDir3dsMax = theSubmissionInfoArray[theIndex+4]+ "\\"
					SMTDPaths.PluginDir = (pathConfig.removePathLeaf theSubmissionInfoArray[theIndex+4])+ "\\"
				)
				local theIndex = findItem theSubmissionInfoArray "[pools]"
				if theIndex > 0 do
				(
					local done = false
					SMTDSettings.Pools = #()
					for i = theIndex+1 to theSubmissionInfoArray.count while not done do
					(
						if matchPattern theSubmissionInfoArray[i] pattern:"[*]" then 
							done = true
						else
							append SMTDSettings.Pools theSubmissionInfoArray[i]
					)
					SMTDSettingsDefaults.Pools = SMTDSettingsFactory.Pools = SMTDSettings.Pools
				)
				local theIndex = findItem theSubmissionInfoArray "[groups]"
				if theIndex > 0 do
				(
					local done = false
					SMTDSettings.Groups = #()
					for i = theIndex+1 to theSubmissionInfoArray.count while not done do
					(
						if matchPattern theSubmissionInfoArray[i] pattern:"[*]" then 
							done = true
						else
							append SMTDSettings.Groups theSubmissionInfoArray[i]
					)
					SMTDSettingsDefaults.Groups = SMTDSettingsFactory.Groups = SMTDSettings.Groups
				)	
				
				SMTDPaths.TempDir = SMTDPaths.UserHomeDir + "temp\\"
				SMTDPaths.LogsDir = SMTDPaths.UserHomeDir + "logs\\"
				SMTDPaths.SettingsDir = SMTDPaths.UserHomeDir + "settings\\"
				
				SMTDPaths.SubmitInfoFile = SMTDPaths.TempDir + "max_submit_info.job"
				SMTDPaths.JobInfoFile = SMTDPaths.TempDir + "max_job_info.job"
				SMTDPaths.ResultFile = SMTDPaths.TempDir + "max_output.txt"
				SMTDPaths.BitmapList = SMTDPaths.TempDir + "max_sceneBitmaps.txt"
				SMTDPaths.RestoreTempMaxFile = SMTDPaths.TempDir + "max_backup_file.mx"
				SMTDPaths.DraftConfigFile = SMTDPaths.TempDir + "draft_tile_config.txt"
				
				SMTDPaths.SubmitOutput = sysInfo.tempdir + "submitOutput.txt"
				SMTDPaths.SubmitExitCode = sysInfo.tempdir + "submitExitCode.txt"
				
				SMTDPaths.submitSubFolder = sysInfo.tempdir
				
				SMTDPaths.InIFile = GetDir #plugcfg + "\\SubmitMaxToDeadline.ini"
				SMTDPaths.ImsqVbscriptFile = SMTDPaths.TempDir+ "copyImsq.py"		
				--format "Loading Submission Info Took % ms\n" (timestamp()-st0)
				true
			)
			else 
			(
				format "--Failed to get Deadline Directories.\n"
				false
			)			
		)
	)--end SMTDFunctions struct
	SMTDFunctions.InitializeSubmitInfo()
)--end local scope

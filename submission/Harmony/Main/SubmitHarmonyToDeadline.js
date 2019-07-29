HarmonyIniFilename = "";

function callDeadlineCommand( args )
{
	var commandLine = "";
	var deadlineBin = "";
	
	deadlineBin = System.getenv( "DEADLINE_PATH" )
	if( ( deadlineBin === null || deadlineBin == "" )  && about.isMacArch() )
	{
		var file = new File( "/Users/Shared/Thinkbox/DEADLINE_PATH" );
		file.open(FileAccess.ReadOnly);
		deadlineBin = file.read();
		file.close();
	}
		
	if( deadlineBin === null || deadlineBin == "" )
	{
		commandLine = "deadlinecommand";
	}
	else
	{
		deadlineBin = trim(deadlineBin);
		commandLine = deadlineBin + "/deadlinecommand";
	}
	
	commandArgs = [];
	commandArgIndex = 0;
	commandArgs[commandArgIndex++] = commandLine;
	for( arg in args)
	{
		commandArgs[commandArgIndex++] = args[arg];
	}
	var status = Process.execute(commandArgs);
	var mOut = Process.stdout;
	
	var result = mOut;
	return result;
}

function trim(string)
{
	return string
		.replace( "\n","" )
		.replace( "\r", "" )
		.replace( "^\s+", "" )
		.replace( "\s+$");
}

function parseBool( value )
{
	value = value.toLowerCase();
	if( value == "1" || value == "t" || value == "true" )
		return true;
	else
		return false;
}

function deadlineStringToArray( str )
{
	str = str.replace( "\r", "" );
	var tempArray = str.split( '\n' );
	var array;
	
	if( tempArray.length > 0 )
	{
		array = new Array( tempArray.length - 1 );
	
		// Only loop to second last item in tempArray, because the last item is always empty.
		for( var i = 0; i < tempArray.length - 1; i ++ )
			array[i] = tempArray[i].replace( "\n", "" ).replace( "\r", "" );
	}
	else
		array = new Array( 0 );
	
	return array;
}

function getIniSetting( key, defaultValue )
{
	var value = defaultValue;
	var filename;
	
	filename = getIniFile();
	iniFile = File( filename);
	if( iniFile.exists )
	{
		iniFile.open( FileAccess.ReadOnly );
		while( ! iniFile.eof )
		{
			var line = iniFile.readLine();
			var index = line.indexOf( "=" );
			if( index > 0 )
			{
				var currKey = line.substring( 0, index );
				if( currKey == key )
				{
					value = line.substring( index + 1 );
					value = value.trim();
					break;
				}
			}
		}
		iniFile.close();
	}
	
	return value;
}

function setIniSetting( key, value )
{
	var iniFileContentsString = "";
	var filename;

	filename = getIniFile();
	iniFile = File( filename );
	if( iniFile.exists )
	{
		iniFile.open( FileAccess.ReadOnly );
		iniFileContentsString = iniFile.read() + "\n";
		iniFile.close();
	}

	var iniFileContents = deadlineStringToArray( iniFileContentsString );

	newIniFile = File( filename );
	newIniFile.open( FileAccess.WriteOnly);
	
	for( var i = 0; i < iniFileContents.length; i ++ )
	{
		var line = iniFileContents[i];
		if( line.length > 0 )
		{
			var index = line.indexOf( "=" );
			if( index > 0 )
			{
				var currKey = line.substring( 0, index );
				if( currKey != key )
					newIniFile.writeLine( line );
			}
		}
	}
			
	newIniFile.writeLine( key + "=" + value );
	
	newIniFile.close();
	
}

// Sets the global function above so that deadlinecommand only gets called once
// to get the settings directory.
function getIniFile()
{
	if (HarmonyIniFilename == "" )
	{
		var prefix = callDeadlineCommand(["-GetSettingsDirectory"]);
		prefix = trim(prefix);
		
		if (about.isMacArch() || about.isLinuxArch() )
			HarmonyIniFilename = prefix + "/harmony_submission.ini";
		else
			HarmonyIniFilename = prefix + "\\harmony_submission.ini";
	}
	return HarmonyIniFilename;
}

function modifyOutputPaths( path )
{
	path = path.replace( "\\", "/" );
	var results = "";
	
	if( about.isWindowsArch() && ( path.indexOf( ":/" ) == 1 ||  path.indexOf( "//" ) == 0 ) )
	{
		results = path;
	}
	else if( !about.isWindowsArch() && path.indexOf( "/" ) == 0 )
	{
		results = path;
	}
	else
	{
		results = scene.currentProjectPath()+"/"+path;
	}
	return results;	

}

function InnerSubmitToDeadline( path )
{
	
	// Value to detect if user installed the incorrect script
	sentinal = 1;
	
	var uiPath = trim(path) + "/SubmitHarmonyToDeadline.ui";
	this.ui = UiLoader.load(uiPath);
	
	this.getMachineList = function( )
	{
		var originalMachineList = this.ui.jobOptionsBox.machineListBox.text; 
		var machineListString = callDeadlineCommand( ["-selectmachinelist",originalMachineList] );
		if( machineListString.indexOf( "Action was cancelled by user" ) == -1 )
			this.ui.jobOptionsBox.machineListBox.setText( trim( machineListString )  );
	}
	
	this.getLimits = function( )
	{
		var originalLimits = this.ui.jobOptionsBox.limitsBox.text; 
		var limitsString = callDeadlineCommand( ["-selectlimitgroups",originalLimits] );
		if( limitsString.indexOf( "Action was cancelled by user" ) == -1 )
			this.ui.jobOptionsBox.limitsBox.setText( trim( limitsString )  );
	}
	
	this.getDependencies = function( )
	{
		var originalDependencies = this.ui.jobOptionsBox.dependenciesBox.text; 
		var dependenciesString = callDeadlineCommand( ["-selectdependencies",originalDependencies] );
		if( dependenciesString.indexOf( "Action was cancelled by user" ) == -1 )
			this.ui.jobOptionsBox.dependenciesBox.setText( trim( dependenciesString )  );
	}
	
	this.useResolutionName = function ( )
	{
		useResName = this.ui.renderOptionsGroup.useResolutionNameBox.checked;

		if( useResName )
		{
			this.ui.renderOptionsGroup.resolutionXBox.setEnabled( true );
			this.ui.renderOptionsGroup.resolutionYBox.setEnabled( true );
			this.ui.renderOptionsGroup.fieldOfViewBox.setEnabled( true );
			this.ui.renderOptionsGroup.resolutionPresetBox.setEnabled( false );
			this.ui.renderOptionsGroup.presetName.setEnabled( false );
		}
		else
		{
			this.ui.renderOptionsGroup.resolutionXBox.setEnabled( false );
			this.ui.renderOptionsGroup.resolutionYBox.setEnabled( false );
			this.ui.renderOptionsGroup.fieldOfViewBox.setEnabled( false );
			this.ui.renderOptionsGroup.resolutionPresetBox.setEnabled( true );
			this.ui.renderOptionsGroup.presetName.setEnabled( this.ui.renderOptionsGroup.resolutionPresetBox.currentText == "Custom" );
		}
	}

	this.resPresetChanged = function ( )
	{
		this.ui.renderOptionsGroup.presetName.setEnabled( this.ui.renderOptionsGroup.resolutionPresetBox.currentText == "Custom" );
	}
	
	this.submit = function( )
	{
		results = "";
		tempFolder = "";
		
		tempFolder = callDeadlineCommand( ["-GetCurrentUserHomeDirectory"] )
		tempFolder = trim( tempFolder )
		if (about.isMacArch() || about.isLinuxArch() )
			tempFolder = tempFolder + "/temp/";
		else
			tempFolder = tempFolder + "\\temp\\";
		
		sceneFile = scene.currentProjectPath() +"/"+ scene.currentVersionName()+".xstage";
		
		env = scene.currentEnvironment();
		job = scene.currentJob();
		sceneName = scene.currentScene();
		sceneVersion = scene.currentVersion();
		
		isDB = true
		if( env == "Digital" )
			isDB = false
		
		jobName = this.ui.jobDescriptionGroup.jobNameBox.text;
		comment = this.ui.jobDescriptionGroup.commentBox.text;
		department = this.ui.jobDescriptionGroup.departmentBox.text;
		
		group = this.ui.jobOptionsBox.groupBox.currentText;
		pool = this.ui.jobOptionsBox.poolBox.currentText;
		secondaryPool = this.ui.jobOptionsBox.secondaryPoolBox.currentText;
		priority = this.ui.jobOptionsBox.priorityBox.value;
		taskTimeout = this.ui.jobOptionsBox.taskTimeoutBox.value;
		limitGroups = this.ui.jobOptionsBox.limitsBox.text;
		concurrentTasks = this.ui.jobOptionsBox.concurrentTasksBox.value;
		jobDependencies = this.ui.jobOptionsBox.dependenciesBox.text;
		onComplete = this.ui.jobOptionsBox.onCompleteBox.currentText;
		machineList = this.ui.jobOptionsBox.machineListBox.text;
		isBlacklist = this.ui.jobOptionsBox.machineListIsBlacklistBox.checked;
		submitSuspended = this.ui.jobOptionsBox.submitSuspendedBox.checked;
		machineLimit = this.ui.jobOptionsBox.machineLimitBox.value;
		chunkSize = this.ui.jobOptionsBox.chunkSizeBox.value;
		frameList = this.ui.renderOptionsGroup.frameListBox.text;
		
		submitScene = this.ui.jobOptionsBox.submitSceneBox.checked;
		useResName = this.ui.renderOptionsGroup.useResolutionNameBox.checked;
		resolutionName = this.ui.renderOptionsGroup.resolutionPresetBox.currentText;
		presetName = this.ui.renderOptionsGroup.presetName.text.trim();
		camera = this.ui.renderOptionsGroup.cameraBox.currentText;
		resolutionX = this.ui.renderOptionsGroup.resolutionXBox.value;
		resolutionY = this.ui.renderOptionsGroup.resolutionYBox.value;
		resolutionFov = this.ui.renderOptionsGroup.fieldOfViewBox.value;

		var versionRegex = / (\d+)\.\d+\.\d/;
		var resNameRegex = /^[\w-]+$/;
		versionInformation = about.getVersionInfoStr();
		matches = versionInformation.match( versionRegex );
		version = matches[1]

		//Error Message handling
		var errorMessages = [];

		if( useResName && resolutionName == "Custom" && !presetName.match( resNameRegex ) )
		{
			errorMessages.push( "\nYour custom resolution preset may only contain alphanumeric characters, hyphens, and underscores." );
		}

		if( errorMessages.length != 0 )
		{
			MessageBox.information( "Error:\n"+errorMessages+"\n\nPlease fix these issues and submit again." );
			return;
		}

		jobInfoFilePath = tempFolder+"harmony_submit_info.job"
		var jobInfoFile = new File( jobInfoFilePath );
		jobInfoFile.open(FileAccess.WriteOnly);
		jobInfoFile.writeLine("Plugin=Harmony")
		jobInfoFile.writeLine( "Name=" + jobName );
		jobInfoFile.writeLine( "Comment=" + comment );
		jobInfoFile.writeLine( "Department=" + department );
		
		jobInfoFile.writeLine( "Group=" +group );
		jobInfoFile.writeLine( "Pool=" +pool );
		jobInfoFile.writeLine( "SecondaryPool=" +secondaryPool );
		jobInfoFile.writeLine( "Priority=" +priority );
		jobInfoFile.writeLine( "TaskTimeoutMinutes=" +taskTimeout );
		jobInfoFile.writeLine( "LimitGroups=" + limitGroups );
		jobInfoFile.writeLine( "ConcurrentTasks=" + concurrentTasks );
		jobInfoFile.writeLine( "JobDependencies=" + jobDependencies );
		jobInfoFile.writeLine( "OnJobComplete=" + onComplete );
		jobInfoFile.writeLine( "Frames=" + frameList );
		jobInfoFile.writeLine( "MachineLimit=" + machineLimit );
		jobInfoFile.writeLine( "ChunkSize=" + chunkSize );
		
		if( isBlacklist )
			jobInfoFile.writeLine( "Blacklist=" + machineList );
		else
			jobInfoFile.writeLine( "Whitelist=" + machineList );
		
		if( submitSuspended )
			jobInfoFile.writeLine( "InitialStatus=Suspended" );
		
		var n = node.numberOfSubNodes("Top");
		var root = node.root();
		var name;
		var outputNum = 0;
		for(i = 0; i < n; ++i)
		{
			name = node.subNode(root, i);

			if(node.type(name) == "WRITE")
			{
				var exportType = node.getTextAttr( name, 1, "exportToMovie" );
				if( exportType == "Output Drawings" ||exportType == "OutputMovieAndKeepFrames" )
				{
					var outputPath = node.getTextAttr( name, 1, "drawingName" );
					var paddingLength = node.getTextAttr( name, 1, "leadingZeros" );
					var drawingType = node.getTextAttr( name, 1, "drawingType" )
					
					outputPath = modifyOutputPaths( outputPath );
					drawingType = drawingType.toLowerCase()
					for(h = 0; h <= paddingLength; ++h )
					{
						outputPath = outputPath + "#";
					}
					
					//Drawing types are the output file formats that are used when rendering for example "TGA1", "scan", "tvg" "PSDDP4"
					//the file extension is always the first 3 letters with the exception of scan.
					if( drawingType  == "scan" )
					{
						outputPath = outputPath + "." + drawingType;
					}
					else
					{
						outputPath = outputPath + "." + drawingType.substr(0, 3);
					}
					
					jobInfoFile.writeLine("OutputFilename"+outputNum+"=" +outputPath );
					
					outputNum++;
				}
				
				if( exportType == "Output Movie" ||exportType == "OutputMovieAndKeepFrames" )
				{
					var outputPath = node.getTextAttr( name, 1, "moviePath" );
					outputPath = modifyOutputPaths( outputPath );
					jobInfoFile.writeLine("OutputFilename"+outputNum+"=" +outputPath+".mov" );
					outputNum++;
				}
			}
		}
		
		jobInfoFile.close();
		
		pluginInfoFilePath = tempFolder+"harmony_plugin_info.job"
		var pluginInfoFile = new File( pluginInfoFilePath );
		pluginInfoFile.open(FileAccess.WriteOnly);
		pluginInfoFile.writeLine("Version="+version);
		
		pluginInfoFile.writeLine("ProjectPath="+scene.currentProjectPath());
		
		if( isDB )
		{
			pluginInfoFile.writeLine("IsDatabase=True");
			pluginInfoFile.writeLine("Environment="+env);
			pluginInfoFile.writeLine("Job="+job);
			pluginInfoFile.writeLine("SceneName="+sceneName);
			pluginInfoFile.writeLine("SceneVersion="+sceneVersion);
			
		}
		else
		{
			pluginInfoFile.writeLine("IsDatabase=False");
			if( !submitScene )
			{
				pluginInfoFile.writeLine("SceneFile="+sceneFile);
			}
		}

		pluginInfoFile.writeLine("UsingResPreset="+useResName);
		if( useResName )
		{
			pluginInfoFile.writeLine("ResolutionName="+resolutionName);
			if( resolutionName == "Custom" )
			{
				pluginInfoFile.writeLine("PresetName="+presetName);
			}
		}
		else
		{
			pluginInfoFile.writeLine("ResolutionX="+resolutionX);
			pluginInfoFile.writeLine("ResolutionY="+resolutionY);
			pluginInfoFile.writeLine("FieldOfView="+resolutionFov);
		}

		pluginInfoFile.writeLine("Camera="+camera);
		
		var n = node.numberOfSubNodes("Top");
		var root = node.root();
		var name;
		var outputNum = 0;
		for(i = 0; i < n; ++i)
		{
			name = node.subNode(root, i);

			if(node.type(name) == "WRITE")
			{
				var exportType = node.getTextAttr( name, 1, "exportToMovie" );
				if( exportType == "Output Drawings" ||exportType == "OutputMovieAndKeepFrames" )
				{
					var outputPath = node.getTextAttr( name, 1, "drawingName" );
					var paddingLength = node.getTextAttr( name, 1, "leadingZeros" );
					var drawingType = node.getTextAttr( name, 1, "drawingType" )
					var startFrame = node.getTextAttr( name, 1, "start" )
					pluginInfoFile.writeLine("Output"+outputNum+"Node="+name);
					pluginInfoFile.writeLine("Output"+outputNum+"Type=Image");
					pluginInfoFile.writeLine("Output"+outputNum+"Path=" +outputPath );
					pluginInfoFile.writeLine("Output"+outputNum+"LeadingZero=" +paddingLength );
					pluginInfoFile.writeLine("Output"+outputNum+"Format=" +drawingType );
					pluginInfoFile.writeLine("Output"+outputNum+"StartFrame=" +startFrame );
					
					outputNum++;
				}
				
				if( exportType == "Output Movie" ||exportType == "OutputMovieAndKeepFrames" )
				{
					var outputPath = node.getTextAttr( name, 1, "moviePath" );
					pluginInfoFile.writeLine("Output"+outputNum+"Node="+name);
					pluginInfoFile.writeLine("Output"+outputNum+"Type=Movie");
					pluginInfoFile.writeLine("Output"+outputNum+"Path=" +outputPath );
					outputNum++;
				}
			}
		}
		
		
		
		pluginInfoFile.close();
		
		renderArguments = [];
		renderArgCount = 0;
		renderArguments[renderArgCount++] = jobInfoFilePath;
		renderArguments[renderArgCount++] = pluginInfoFilePath;
		if( submitScene )
			renderArguments[renderArgCount++] = sceneFile;
		
		results = callDeadlineCommand(renderArguments);
		
		MessageBox.information( results );
		
		setIniSetting( "Department", department );
		setIniSetting( "Group",group );
		setIniSetting( "Pool",pool );
		setIniSetting( "SecondaryPool", secondaryPool );
		setIniSetting( "Priority", priority );
		setIniSetting( "MachineLimit", machineLimit );
		setIniSetting( "LimitGroups", limitGroups );
		setIniSetting( "MachineList", machineList );
		setIniSetting( "IsBlacklist", isBlacklist );
		setIniSetting( "SubmitSuspended", submitSuspended );
		setIniSetting( "ChunkSize", chunkSize );
		setIniSetting( "SubmitScene", submitScene );
		setIniSetting( "OnComplete", onComplete );
		setIniSetting( "TaskTimeout", taskTimeout );
		setIniSetting( "ConcurrentTasks", concurrentTasks );
		setIniSetting( "JobDependencies", jobDependencies );
		
	}
	
	this.close = function( )
	{
		this.ui.close();
	}
	
	var initDepartment = getIniSetting( "Department", "" );
	var initGroup = getIniSetting( "Group", "none" );
	var initPool = getIniSetting( "Pool", "none" );
	var initSecondaryPool = getIniSetting( "SecondaryPool", "" );
	var initPriority = parseInt( getIniSetting( "Priority", "50" ) );
	var initMachineLimit = parseInt( getIniSetting( "MachineLimit", 0 ) );
	var initLimitGroups = getIniSetting( "LimitGroups", "" );
	var initMachineList = getIniSetting( "MachineList", "" );
	var initIsBlacklist = parseBool( getIniSetting( "IsBlacklist", "false" ) );
	var initSubmitSuspended = parseBool( getIniSetting( "SubmitSuspended", "false" ) );
	var initChunkSize = parseInt( getIniSetting( "ChunkSize", "1" ) );
	var initSubmitScene = parseBool( getIniSetting( "SubmitScene", "false" ) );
	var initOnComplete = getIniSetting( "OnComplete", "Nothing" );
	var initTaskTimeout = parseInt( getIniSetting( "TaskTimeout", "0" ) );
	var initConcurrentTasks = parseInt( getIniSetting( "ConcurrentTasks", "1" ) );
	
	resolutionX = scene.currentResolutionX();
	resolutionY = scene.currentResolutionY();
	resolutionFov = scene.defaultResolutionFOV();
	emptyArray = [""];
	cameras = emptyArray.concat( node.getCameras() );
	curCam = cameras.indexOf(node.getDefaultCamera());
	
	var poolString = callDeadlineCommand( ["-pools"] );
	var pools = deadlineStringToArray( poolString );
	initPoolIndex = pools.indexOf(initPool);
	secondaryPools = [""]
	secondaryPools = secondaryPools.concat(pools)
	initSecondaryPoolIndex = secondaryPools.indexOf(initSecondaryPool);
		
	var groupString = callDeadlineCommand( ["-groups"] );
	var groups = deadlineStringToArray( groupString );
	initGroupIndex = groups.indexOf(initGroup);
	
	var maxPriorityString = callDeadlineCommand( ["-getmaximumpriority"] );
	var maximumPriority = parseInt(maxPriorityString);
	if (initPriority > maximumPriority)
		initPriority = Math.round( maximumPriority / 2 );
	
	//Not Connected to Database
	if( scene.currentEnvironment() != "Digital" )
	{
		env = scene.currentEnvironment();
		job = scene.currentJob();
		sceneName = scene.currentScene();
		version = scene.currentVersion();
		versionName = scene.currentVersionName();
		jobName = env + " " + job + " " + sceneName + " ver: " + version + " " + versionName
		this.ui.jobDescriptionGroup.jobNameBox.setText( jobName )
	}
	else
	{
		this.ui.jobDescriptionGroup.jobNameBox.setText( scene.currentScene() + " - "+scene.currentVersionName() )
	}
	
	this.ui.jobDescriptionGroup.departmentBox.setText( initDepartment )
	
	this.ui.jobOptionsBox.poolBox.addItems( pools );
	if(initPoolIndex >=0)
		this.ui.jobOptionsBox.poolBox.setCurrentIndex( initPoolIndex );
	
	this.ui.jobOptionsBox.secondaryPoolBox.addItems( secondaryPools );
	if(initSecondaryPoolIndex >=0)
		this.ui.jobOptionsBox.secondaryPoolBox.setCurrentIndex( initSecondaryPoolIndex );
	
	this.ui.jobOptionsBox.groupBox.addItems( groups );
	if(initGroupIndex >= 0)
		this.ui.jobOptionsBox.groupBox.setCurrentIndex( initGroupIndex );
	
	this.ui.jobOptionsBox.priorityBox.maximum = maximumPriority;
	this.ui.jobOptionsBox.priorityBox.setValue(initPriority);
	this.ui.jobOptionsBox.machineLimitBox.setValue(initMachineLimit);
	this.ui.jobOptionsBox.limitsBox.setText(initLimitGroups);
	this.ui.jobOptionsBox.machineListBox.setText(initMachineList);
	this.ui.jobOptionsBox.machineListIsBlacklistBox.setChecked(initIsBlacklist);
	this.ui.jobOptionsBox.submitSuspendedBox.setChecked(initSubmitSuspended);
	this.ui.jobOptionsBox.chunkSizeBox.setValue(initChunkSize);
	this.ui.jobOptionsBox.submitSceneBox.setChecked(initSubmitScene);
	
	this.ui.jobOptionsBox.machineListButton.pressed.connect( this, this.getMachineList );
	this.ui.jobOptionsBox.limitsButton.pressed.connect( this, this.getLimits );
	this.ui.jobOptionsBox.dependenciesButton.pressed.connect( this, this.getDependencies );
	this.ui.jobOptionsBox.concurrentTasksBox.setValue(initConcurrentTasks);
	this.ui.jobOptionsBox.taskTimeoutBox.setValue(initTaskTimeout);
	
	this.ui.submitButton.pressed.connect( this, this.submit );
	this.ui.closeButton.pressed.connect( this, this.close );
	
	onCompletes = new Array( 3 );
	onCompletes[0] = "Nothing";
	onCompletes[1] = "Archive";
	onCompletes[2] = "Delete";
	this.ui.jobOptionsBox.onCompleteBox.addItems( onCompletes );

	resPresets = ["HDTV_1080p24","HDTV_1080p25","HDTV_720p24","4K_UHD","8K_UHD","DCI_2K","DCI_4K","film-2K","film-4K",
				"film-1.33_H","film-1.66_H","film-1.66_V","Cineon","NTSC","PAL","2160p","1440p","1080p","720p","480p",
				"360p","240p","low","Web_Video","Game_512","Game_512_Ortho","WebCC_Preview","Custom"];
	this.ui.renderOptionsGroup.resolutionPresetBox.addItems( resPresets );
	this.ui.renderOptionsGroup.resolutionPresetBox['currentIndexChanged(int)'].connect( this, this.resPresetChanged );
	this.ui.renderOptionsGroup.resolutionPresetBox.setEnabled( false );
	this.ui.renderOptionsGroup.presetName.setEnabled( false );
	this.ui.renderOptionsGroup.useResolutionNameBox.pressed.connect( this, this.useResolutionName );
	this.ui.renderOptionsGroup.frameListBox.setText("1-"+frame.numberOf())
	this.ui.renderOptionsGroup.resolutionXBox.setValue( resolutionX );
	this.ui.renderOptionsGroup.resolutionYBox.setValue( resolutionY );
	this.ui.renderOptionsGroup.fieldOfViewBox.setValue( resolutionFov );
	this.ui.renderOptionsGroup.cameraBox.addItems( cameras );
	if( curCam >= 0 )
		this.ui.renderOptionsGroup.cameraBox.setCurrentIndex( curCam );
	
	if( scene.currentEnvironment() != "Digital" )
		this.ui.jobOptionsBox.submitSceneBox.setEnabled( false );
	
	this.ui.exec();
	
}


//----------------------------------------------------------
// A script for submitting Lightwave scenes to Deadline.
// Ryan Russell (Thinkbox Software Inc) 2009.
//----------------------------------------------------------

@version 2.2
@warnings
@script generic

//----------------------------------------------------------
// Global Variables
//----------------------------------------------------------

// Controls.
departmentCtrl;
groupCtrl;
contentCtrl;
configCtrl;
chunkSizeCtrl;
poolCtrl;
secondaryPoolCtrl;
//poolMachinesCtrl;
priorityCtrl;
machineLimitCtrl;
submitSceneCtrl;
limitGroupsCtrl;
dependenciesCtrl;
machineListCtrl;
isBlacklistCtrl;
buildCtrl;
screamerNetCtrl;
fprimeCtrl;
pipelineStatusCtrl;

// Paths.
tempPath = string( getdir("Temp"), "/");
configINIFilePath = string( getdir( "Settings" ), "/lw_config_dir.ini" );

// Default settings for submission dialog.
lwVersion = hostVersion();
contentDir = getdir( "Content" );
configDir = getdir( "Settings" );
chunkSize = 1;
//poolMachinesOnly = false;
maximumPriority = 100;
priority = 50;
machineLimit = 0;
submitScene = false;
screamerNet = true;
fprime = false;
department = "";
pools;
selectedPoolStr = "none";
secondaryPools;
selectedSecondaryPoolStr = "";
groups;
selectedGroupStr = "none";
builds;
selectedBuildStr = "None";
onCompletes;
selectedOnCompleteStr = "Nothing";
pipelineToolStatus = "No Pipeline Tools Set";

integrationItems;

//----------------------------------------------------------
// Functions
//----------------------------------------------------------

// Loads the sticky settings.
loadUISettings
{
	integrationItems[1] = "";
	
	configINIFile = File( configINIFilePath,"r" );
	if( configINIFile && configINIFile.linecount() >= 13 )
	{
		department          = configINIFile.read();
		selectedGroupStr    = configINIFile.read();
		contentDir          = configINIFile.read();
		configDir           = configINIFile.read();
		chunkSize           = number( configINIFile.read() );
		selectedPoolStr     = configINIFile.read();
		selectedSecondaryPoolStr = configINIFile.read();
		//poolMachinesOnly    = number( configINIFile.read() );
		priority            = number( configINIFile.read() );
		machineLimit        = number( configINIFile.read() );
		submitScene         = number( configINIFile.read() );
		selectedBuildStr    = configINIFile.read();
		screamerNet         = number( configINIFile.read() );
		fprime              = number( configINIFile.read() );
		
		
		configINIFile.close();
		
		if( chunkSize <= 0 )
			chunkSize = 1;
		
		if( priority < 0 || priority > 100 )
			priority = 50;
		
		if( machineLimit <= 0 )
			machineLimit = 0;
		
		if( submitScene != 0 || submitScene != 1 )
			submitScene = true;
		
		if( screamerNet != 0 || screamerNet != 1 )
			screamerNet = true;
		
		if( fprime != 0 || fprime != 1 )
			fprime = false;
			
	}
}

// Saves the sticky settings.
saveUISettings
{
	configINIFile = File(configINIFilePath,"w");
	if( configINIFile )
	{
		configINIFile.writeln( getvalue( departmentCtrl ) );
		configINIFile.writeln( groups[ getvalue( groupCtrl ) ] );
		configINIFile.writeln( getvalue( contentCtrl ) );
		configINIFile.writeln( getvalue( configCtrl ) );
		configINIFile.writeln( getvalue( chunkSizeCtrl ) );
		configINIFile.writeln( pools[ getvalue( poolCtrl ) ] );
		configINIFile.writeln( secondaryPools[ getvalue( secondaryPoolCtrl ) ] );
		//configINIFile.writeln( getvalue( poolMachinesCtrl ) );
		configINIFile.writeln( getvalue( priorityCtrl ) );
		configINIFile.writeln( getvalue( machineLimitCtrl ) );
		configINIFile.writeln( getvalue( submitSceneCtrl ) );
		configINIFile.writeln( builds[ getvalue( buildCtrl ) ] );
		configINIFile.writeln( getvalue( screamerNetCtrl ) );
		configINIFile.writeln( getvalue( fprimeCtrl ) );

		
		configINIFile.close();
	}
}

//Gets the path to the specified subdirectory within the repo
getRepositoryFilePath: subdir
{
	path = "";

	command = " -GetRepositoryFilePath ";
	if ( subdir != nil || subdir != "" )
	{
		command += subdir;
	}

	output = deadlineCommand( command );
	if (output[1] != nil && output[1] != "")
	{
		path = output[1];
	}

	return path;
}

// Calls DeadlineCommand and returns an array which contains the lines of output received.
deadlineCommand: command
{
	outputFilename = string( tempPath, "submitoutput.txt" );
	exitcodeFilename = string( tempPath, "submitexitcode.txt" );
	
	deadlineCommandPath = "";
	arguments = string( " -outputfiles \"", outputFilename, "\" \"", exitcodeFilename, "\" ", command );
	
	// Use the SYSTEMROOT environment variable to determine if we're on Windows or OSX. 
	deadlineBin = getenv( "DEADLINE_PATH" );
	
	if( deadlineBin == nil || deadlineBin == ""  )
	{
		deadlinePath = "/Users/Shared/Thinkbox/DEADLINE_PATH";
		deadlinePathFile = File( deadlinePath, "r" );
		if( deadlinePathFile )
		{
			deadlineBin = deadlinePathFile.read();
			deadlinePathFile.close();
		}
	}
	deadlineBin.trunc();
	
	if( getenv( "SYSTEMROOT" ) != nil )
	{
		// We're on Windows!
		if( deadlineBin == nil || deadlineBin == ""  )
		{
			deadlineCommandBG = "deadlinecommandbg.exe" ;
		}
		else
		{
			deadlineCommandBG = string( deadlineBin, "\\deadlinecommandbg.exe" );
		}
		spawn( deadlineCommandBG, arguments );
	}
	else
	{
		// We're on OSX!
		// If deadlinecommandbg exists at the default install location, just use the full path instead of assuming it's in the path.
		if( deadlineBin == nil || deadlineBin == "" )
		{
			deadlineCommandPath = "deadlinecommandbg";
		}
		else
		{
			deadlineCommandPath = string( deadlineBin, "/deadlinecommandbg" );
		}
		// Need the graves (a.k.a. backquotes) in here, since spawn actually calls 'open' in OSX, which opens a file.
		// It's a bit of a hack, and prints an error in the console (though this won't be visible to the user unless
		// they look in the console log), but it's necessary since the OSX version of spawn() is dumb.
		spawn( string("`", deadlineCommandPath, arguments, "`" ) );
	}
	
	index = 1;
	result[ index ] = "";
	
	outputFile = File( outputFilename, "r" ) || error( "ERROR: deadlineCommand: Cannot open output file for reading." );
	while( !outputFile.eof() )
	{
		result[ index ] = outputFile.read();
		index = index + 1;
	}
	outputFile.close();
	
	return result;
}

// Calls DeadlineCommand to display a directory selection dialog.
getDirectory: initialDirectory
{
	results = deadlineCommand( string( "-getdirectory \"", initialDirectory, "\"" ) );
	selectedDirectory = results[1];
	if( selectedDirectory != nil && size( selectedDirectory ) > 0 )
		return selectedDirectory;
	return initialDirectory;
}

// Checks if the given path is local.
isPathLocal: filePath
{
	drive = strlower( strleft( filePath, 1 ) );
	return ( drive == "c" || drive == "d" || drive == "e" );
}

// Parses the line for filename information.
parsePrefix: line
{
	prefix = "";
	
	// The line is in the format PREFIX FILENAME_PREFIX. Since the filename can
	// have spaces, we must start building the filename after the first space.
	array = parse( " ", line );
	for( i = 2; i <= sizeof( array ); i ++ )
	{
		if( i == 2 )
			prefix = string( prefix, array[ i ] );
		else
			prefix = string( prefix, " ", array[ i ] );
	}
	
	return prefix;
}

// Parses the line for extension information.
parseExtension: line
{
	ext = "";
	
	array = parse( "(", line );
	if( sizeof( array ) >= 2 )
	{
		// If the line contains brackets, then it's in the form PREFIX FORMAT(.ext),
		// and we must parse the extension from the line.
		array = parse( ")", array[ 2 ] );
		ext = array[ 1 ];
	}
	else
	{
		// If the line contains no brackets, then it's in the form PREFIX FORMAT, and
		// we have to set the extension based on the format name.
		array = parse( " ", line );
		if( sizeof( array ) > 1 )
		{
			format = strlower( array[ 2 ] );
			if( format == "_flexible" || format == "_flexiblelegacy" )
				ext = ".flx";
			else if( format == "_ilbm" || format == "_ilbm32" )
				ext = ".iff";
			else if( format == "_targa" )
				ext = ".tga";
		}
	}
	
	return ext;
}

getOutputLine: prefix, ext, format, count
{
	outputLine = "";
	
	if( ext != "" )
	{
		if( hostVersion() < 9.5 )
		{
			// These output formats are hardcoded because we don't know where to get them from Lightwave. :P
			filenameFormats[ 1 ] = "###";    // Name001
			filenameFormats[ 2 ] = "###";    // Name001.xxx
			filenameFormats[ 3 ] = "####";   // Name0001
			filenameFormats[ 4 ] = "####";   // Name0001.xxx
			filenameFormats[ 5 ] = "_###";   // Name_001
			filenameFormats[ 6 ] = "_###";   // Name_001.xxx
			filenameFormats[ 7 ] = "_####";  // Name_0001
			filenameFormats[ 8 ] = "_####";  // Name_0001.xxx
		}
		else
		{
			filenameFormats[ 1 ] = "###";     // Name001
			filenameFormats[ 2 ] = "###";     // Name001.xxx
			filenameFormats[ 3 ] = "####";    // Name0001
			filenameFormats[ 4 ] = "####";    // Name0001.xxx
			filenameFormats[ 5 ] = "#####";   // Name00001
			filenameFormats[ 6 ] = "#####";   // Name00001.xxx
			filenameFormats[ 7 ] = "######";  // Name000001
			filenameFormats[ 8 ] = "######";  // Name000001.xxx
			filenameFormats[ 9 ] = "_###";    // Name_001
			filenameFormats[ 10 ] = "_###";   // Name_001.xxx
			filenameFormats[ 11 ] = "_####";  // Name_0001
			filenameFormats[ 12 ] = "_####";  // Name_0001.xxx
			filenameFormats[ 13 ] = "_#####";  // Name_00001
			filenameFormats[ 14 ] = "_#####";  // Name_00001.xxx
			filenameFormats[ 15 ] = "_######"; // Name_000001
			filenameFormats[ 16 ] = "_######"; // Name_000001.xxx
		}
		
		// If we retrieved the extension, give the whole filename to Deadline.
		filename = string( prefix, filenameFormats[ format ] );
		if( format % 2 == 0 )
			filename = string( filename, ext );
		outputLine = string( "OutputFilename", count, "=", filename );
	}
	else
	{
		// If no extension was retrieved, just give the directory to Deadline.
		prefixParts = split( prefix );
		outputLine = string( "OutputDirectory", count, "=", prefixParts[ 1 ], prefixParts[ 2 ] );
	}
	
	return outputLine;
}

arrayToStr : array, separator
{
	strOut = "";
	
	if( array != nil )
	{
		for( i = 1; i <= sizeof( array ); i ++ )
		{
			if ( i == 1 )
				strOut = array[i];
			else
				strOut = strOut + separator + array[i];
		}
	}
	
	return strOut;
}

strToArray : strIn, separator
{
	if ( strIn == "" || strIn == nil )
		return nil;
	else
		return parse( separator, strIn );
}

// Concatenate pipeline tool settings for the scene to the .job file.
concatenatePipelineSettingsToJob : jobPath, batchName
{
	jobWriterPath = getRepositoryFilePath( "submission/Integration/Main/JobWriter.py" );
	sceneFilePath = Scene().filename;

	additionalInfo = string( " LightWave --write --scene-path ", sceneFilePath, " --job-path ", jobPath, " --batch-name ", batchName );
	command = string( "-executescript \"", jobWriterPath,"\"", additionalInfo );
	deadlineCommand( command );
}

// Grabs a status message from the JobWriter that indicates which pipeline tools have settings enabled for the current scene.
retrievePipelineToolStatus
{
	jobWriterPath = getRepositoryFilePath( "submission/Integration/Main/JobWriter.py" );
	sceneFilePath = Scene().filename;

	additionalInfo = string(" LightWave --status --scene-path ", sceneFilePath );
	command = string( "-executescript \"", jobWriterPath,"\"", additionalInfo );
	statusMessageArray = deadlineCommand( command );

	statusMessage = arrayToStr( statusMessageArray, "" );
	return statusMessage;
}

// Updates the pipeline tools status label with a non-empty status message as there's always a status associated with the pipeline tools.
updatePipelineToolStatusLabel : statusMessage
{
	if( strlower( strleft( statusMessage, 5 ) ) == "error" )
	{
		setvalue( pipelineStatusCtrl, "Pipeline Tools Error" );
		warn( statusMessage );
	}
	else
		setvalue( pipelineStatusCtrl, statusMessage );
}

//----------------------------------------------------------
// Button Click Events
//----------------------------------------------------------

// Ask the user for a content directory.
contentBrowse
{  
	setvalue( contentCtrl, getDirectory( getvalue( contentCtrl ) ) );
}

// Ask the user for a config directory.
configBrowse
{
	setvalue( configCtrl, getDirectory( getvalue( configCtrl ) ) );
}

// Ask the user to select the Limits.
limitGroupsBrowse
{
	results = deadlineCommand( string( "-selectlimitgroups \"", getvalue( limitGroupsCtrl ), "\"" ) );
	limitGroups = results[1];
	if( limitGroups != "Action was cancelled by user" )
		setvalue( limitGroupsCtrl, limitGroups );
}

// Ask the user to select the job dependencies.
dependenciesBrowse
{
	results = deadlineCommand( string( "-selectdependencies \"", getvalue( dependenciesCtrl ), "\"" ) );
	dependencies = results[1];
	if( dependencies != "Action was cancelled by user" )
		setvalue( dependenciesCtrl, dependencies );
}

// Ask the user to select the machine list.
machineListBrowse
{
	results = deadlineCommand( string( "-selectmachinelist \"", getvalue( machineListCtrl ), "\"" ) );
	machineList = results[1];
	if( machineList != "Action was cancelled by user" )
		setvalue( machineListCtrl, machineList );
}

connectToPipelineTools
{
	integrationPath = getRepositoryFilePath( "submission/Integration/Main/IntegrationUIStandAlone.py" );
	sceneFilePath = Scene().filename;

	additionalInfo = string( " -v 2 LightWave -d Shotgun FTrack NIM --path ", sceneFilePath );
	command = string( "-executescript \"", integrationPath,"\"", additionalInfo );
	statusMessageArray = deadlineCommand( command );

	statusMessage = arrayToStr( statusMessageArray, "" );
	updatePipelineToolStatusLabel( statusMessage );
}

enableCtrls : value
{
	return value;
}

//----------------------------------------------------------
// Main Script
//----------------------------------------------------------

generic
{
	// Ensure that scene is saved before submitting.
	if( Scene().filename == "(unnamed)" )
		SaveSceneAs();
	else
		SaveSceneAs( Scene().filename );
	
	// Get the scene.
	scene = Scene();
	
	// Parse the Lightwave scene file to find any output information we can, since there
	// aren't any lscript hooks into the Render Options.
	outputRgb = true;
	outputRgbPrefix = "";
	outputRgbExt = "";
	
	outputAlpha = true;
	outputAlphaPrefix = "";
	outputAlphaExt = "";
	
	outputFilenameFormat = 1;  
	
	saveRgbRe = regexp( "SaveRGB 0" );
	saveRgbImagesPrefixRe = regexp( "SaveRGBImagesPrefix .*" );
	saveRgbImageSaverRe = regexp( "RGBImageSaver.*" );
	
	saveAlphaRe = regexp( "SaveAlpha 0" );
	saveAlphaImagesPrefixRe = regexp( "SaveAlphaImagesPrefix .*" );
	saveAlphaImageSaverRe = regexp( "AlphaImageSaver.*" );
	
	outputFilenameFormatRe = regexp( "OutputFilenameFormat.*" );
	
	// Open the scene file.
	sceneFile = File( scene.filename, "r" ) || error( "ERROR: Scene: Cannot open scene file for reading. Ensure that the scene has been saved." );
	while( !sceneFile.eof() )
	{
		line = sceneFile.read();
		
		// RGB filename parsing.
		if( line == saveRgbRe )
			outputRgb = false;
		else if( line == saveRgbImageSaverRe )
			outputRgbExt = parseExtension( line );
		else if( line == saveRgbImagesPrefixRe )
			outputRgbPrefix = parsePrefix( line );
		
		// Alpha filename parsing.
		else if( line == saveAlphaRe )
			outputAlpha = false;
		else if( line == saveAlphaImageSaverRe )
			outputAlphaExt = parseExtension( line );
		else if( line == saveAlphaImagesPrefixRe )
			outputAlphaPrefix = parsePrefix( line );
		
		// Output format parsing.
		else if( line == outputFilenameFormatRe )
		{
			array = parse( " ", line );
			outputFilenameFormat = integer( array[ 2 ] ) + 1;
		}
	}
	sceneFile.close();
	
	// Ensure that an output location has been specified.
	if( ( !outputRgb || outputRgbPrefix == "" ) && ( !outputAlpha || outputAlphaPrefix == "" ) )
		error( "ERROR: Render Options: No RGB or Alpha output specified. At least one must be specified." );
	
	// Check for any warnings that should be displayed to the user.
	preWarningIndex = 1;
	preWarningMessages;
	
	if( outputRgb && outputRgbPrefix != "" )
	{
		// Warn user if RGB output path is local.
		if( isPathLocal( outputRgbPrefix ) )
		{
			preWarningMessages[ preWarningIndex ] = "Render Options: The path for your RGB output is local.";
			preWarningMessages[ preWarningIndex + 1 ] = "";
			preWarningIndex = preWarningIndex + 2;
		}
		
		// Warn user if RGB output path is missing the extension.
		if( outputRgbExt == "" )
		{
			preWarningMessages[ preWarningIndex ] = "Render Options: The path for your RGB output doesn't have an extension specified.";
			preWarningMessages[ preWarningIndex + 1 ] = "";
			preWarningIndex = preWarningIndex + 2;
		}
	}
	
	if( outputAlpha && outputAlphaPrefix != "" )
	{
		// Warn user if alpha output path is local.
		if( isPathLocal( outputAlphaPrefix ) )
		{
			preWarningMessages[ preWarningIndex ] = "Render Options: The path for your Alpha output is local.";
			preWarningMessages[ preWarningIndex + 1 ] = "";
			preWarningIndex = preWarningIndex + 2;
		}
		
		// Warn user if alpha output path is missing the extension.
		if( outputAlphaExt == "" )
		{
			preWarningMessages[ preWarningIndex ] = "Render Options: The path for your Alpha output doesn't have an extension specified.";
			preWarningMessages[ preWarningIndex + 1 ] = "";
			preWarningIndex = preWarningIndex + 2;
		}
	}
	
	// Show the warning(s) if necessary.
	if( preWarningIndex > 1 )
	{
		reqbegin( "Warning" );
		ctltext( "", preWarningMessages );      
		ctltext( "", "Click OK to continue, otherwise click Cancel." );
		if( !reqpost() )
			return;
		reqend();
	}
	
	// Load the sticky settings.
	loadUISettings();
	
	// Get the maximum priority;
	maximumPriorityArray = deadlineCommand( "-getmaximumpriority" );
	maximumPriority = number(maximumPriorityArray[1]);
	if( maximumPriority == nil )
		maximumPriority = 100;
	
	if( priority > maximumPriority )
		priority = maximumPriority / 2;
	
	// Get the pools.
	pools = deadlineCommand( "-pools" );
	selectedPool = 1;
	for( i = 1; i <= sizeof( pools ); i ++ )
	{
		if( pools[ i ] == selectedPoolStr )
			selectedPool = i;
	}
	
	secondaryPools[ 1 ] = "";
	selectedSecondaryPool = 1;   
	for( i = 1; i <= sizeof( pools ); i ++ )
	{
		secondaryPools[i+1] = pools[i];
		if( secondaryPools[ i+1 ] == selectedSecondaryPoolStr )
		selectedSecondaryPool = i;
	}
	
	// Get the groups.
	groups = deadlineCommand( "-groups" );
	selectedGroup = 1;
	for( i = 1; i <= sizeof( groups ); i ++ )
	{
		if( groups[ i ] == selectedGroupStr )
			selectedGroup = i;
	}
	
	// Get the frame string.
	startFrame = scene.framestart; 
	endFrame = scene.frameend;
	byFrame = scene.framestep;
	initFrameStr = string( startFrame, "-", endFrame );
	if( byFrame > 1 )
		initFrameStr = string( initFrameStr, "x", byFrame );
	
	// Get the build.
	builds[1] = "None";
	builds[2] = "32bit";
	builds[3] = "64bit";
	selectedBuild = 1;
	for( i = 1; i <= sizeof( builds ); i ++ )
	{
		if( builds[ i ] == selectedBuildStr )
			selectedBuild = i;
	}
	
	onCompletes[1] = "Nothing";
	onCompletes[2] = "Archive";
	onCompletes[3] = "Delete";
	selectedOnComplete = 1;
	for( i = 1; i <= sizeof( onCompletes ); i ++ )
	{
		if( onCompletes[ i ] == selectedOnCompleteStr )
			selectedOnComplete = i;
	}
	
	// Create the submission dialog.
	reqbegin( "Submit to Deadline" ); 
	reqsize( 420, 625 );
	
	tabCtrl = ctltab( "Job Options");
	ctlposition( tabCtrl, 5, 5, 200, 20 );
	
	//-----Job Options Tab----
	// Job Description
	jobNameCtrl = ctlstring( "Job Name", scene.name );
	ctlposition( jobNameCtrl, 43, 30, 370, 20 );
	ctlpage( 1, jobNameCtrl );
	
	commentCtrl = ctlstring( "Comment", "" );
	ctlposition( commentCtrl, 47, 55, 366, 20 );
	ctlpage( 1, commentCtrl );
	
	departmentCtrl = ctlstring( "Department", department );
	ctlposition( departmentCtrl, 36, 80, 377, 20 );
	ctlpage( 1, departmentCtrl );
	
	separator1 = ctlsep( 2, 308 );
	ctlposition( separator1, 14, 110, 398, 5 );
	ctlpage( 1, separator1 );
	
	// Job Scheduling
	poolCtrl = ctlpopup( "Pool", selectedPool, pools );
	ctlposition( poolCtrl, 69, 120, 169, 20 );
	ctlpage( 1, poolCtrl );
	
	secondaryPoolCtrl = ctlpopup( "Secondary Pool", selectedSecondaryPool, secondaryPools );
	ctlposition( secondaryPoolCtrl, 14, 145, 224, 20 );
	ctlpage( 1, secondaryPoolCtrl );
	
	groupCtrl = ctlpopup( "Group", selectedGroup, groups );
	ctlposition( groupCtrl, 61, 170, 177, 20 );
	ctlpage( 1, groupCtrl );
	
	priorityCtrl = ctlminislider( "Priority", priority, 0, maximumPriority );
	ctlposition( priorityCtrl, 59, 195, 157, 20 );
	ctlpage( 1, priorityCtrl );

	machineLimitCtrl = ctlminislider( "Machine Limit", machineLimit, 0, 1000 );
	ctlposition( machineLimitCtrl, 25, 220, 191, 20 );
	ctlpage( 1, machineLimitCtrl );
	
	taskTimeoutCtrl = ctlminislider( "Task Timeout", 0, 0, 5000 );
	ctlposition( taskTimeoutCtrl, 25, 245, 191, 20 );
	ctlpage( 1, taskTimeoutCtrl );
	
	concurrentCtrl = ctlminislider( "Conc. Tasks", 1, 1, 16 );
	ctlposition( concurrentCtrl, 30, 270, 186, 20 );
	ctlpage( 1, concurrentCtrl );
	isBlacklistCtrl = ctlcheckbox( "Machine List is a Blacklist", 0 );
	ctlposition( isBlacklistCtrl, 243, 270, 170, 20 );
	ctlpage( 1, isBlacklistCtrl );
	
	machineListCtrl = ctlstring( "Machine List", "" );
	ctlposition( machineListCtrl, 30, 295, 358, 20 );
	ctlpage( 1, machineListCtrl );
	machineListBrowseCtrl = ctlbutton( "...", 18, "machineListBrowse" );
	ctlposition( machineListBrowseCtrl, 393, 295, 20, 20 );
	ctlpage( 1, machineListBrowseCtrl );
	
	limitGroupsCtrl = ctlstring( "Limits", "" );
	ctlposition( limitGroupsCtrl, 64, 320, 324, 20 );
	ctlpage( 1, limitGroupsCtrl );
	limitGroupsBrowseCtrl = ctlbutton( "...", 18, "limitGroupsBrowse" );
	ctlposition( limitGroupsBrowseCtrl, 393, 320, 20, 20 );
	ctlpage( 1, limitGroupsBrowseCtrl );
	
	dependenciesCtrl = ctlstring( "Dependencies", "" );
	ctlposition( dependenciesCtrl, 21, 345, 367, 20 );
	ctlpage( 1, dependenciesCtrl );
	dependenciesBrowseCtrl = ctlbutton( "...", 18, "dependenciesBrowse" );
	ctlposition( dependenciesBrowseCtrl, 393, 345, 20, 20 );
	ctlpage( 1, dependenciesBrowseCtrl );
	
	onCompleteCtrl = ctlpopup( "On Complete", selectedOnComplete, onCompletes );
	ctlposition( onCompleteCtrl, 29, 375, 209, 20 );
	ctlpage( 1, onCompleteCtrl );
	submitSuspendedCtrl = ctlcheckbox( "Submit As Suspended", 0 );
	ctlposition( submitSuspendedCtrl, 243, 375, 170, 20 );
	ctlpage( 1, submitSuspendedCtrl );
	
	separator2 = ctlsep( 2, 330 );
	ctlposition( separator2, 14, 400, 398, 5);
	ctlpage( 1, separator2 );
	
	// Lightwave Options
	framesCtrl = ctlstring( "Frame List", initFrameStr );
	ctlposition( framesCtrl, 42, 410, 371, 20 );
	ctlpage( 1, framesCtrl );
	
	chunkSizeCtrl = ctlminislider( "Frames Per Task", chunkSize, 1, 1000 );
	ctlposition( chunkSizeCtrl, 10, 435, 178, 20 );
	ctlpage( 1, chunkSizeCtrl );
	
	contentCtrl = ctlstring( "Content Dir", contentDir );
	ctlposition( contentCtrl, 37, 460, 351, 20 );
	ctlpage( 1, contentCtrl );
	contentBrowseCtrl = ctlbutton( "...", 18, "contentBrowse" );
	ctlposition( contentBrowseCtrl, 393, 460, 20, 20 );
	ctlpage( 1, contentBrowseCtrl );
	
	configCtrl = ctlstring( "Config Dir", configDir );
	ctlposition( configCtrl, 44, 485, 344, 20 );
	ctlpage( 1, configCtrl );
	configBrowseCtrl = ctlbutton( "...", 18, "configBrowse" );
	ctlposition( configBrowseCtrl, 393, 485, 20, 20 );
	ctlpage( 1, configBrowseCtrl );
	
	buildCtrl = ctlpopup( "Force Build", selectedBuild, builds );
	ctlposition( buildCtrl, 37, 510, 201, 20 );
	ctlpage( 1, buildCtrl );
	submitSceneCtrl = ctlcheckbox( "Submit Lightwave Scene File", submitScene );
	ctlposition( submitSceneCtrl, 243, 510, 170, 20 );
	ctlpage( 1, submitSceneCtrl );
	
	fprimeCtrl = ctlcheckbox( "Use FPrime Renderer", fprime );
	ctlposition( fprimeCtrl, 96, 535, 142, 20 );
	ctlpage( 1, fprimeCtrl );
	screamerNetCtrl = ctlcheckbox( "Use ScreamerNet Rendering", screamerNet );
	ctlposition( screamerNetCtrl, 243, 535, 170, 20 );
	ctlpage( 1, screamerNetCtrl );
	
	pipelineConnectCtrl = ctlbutton( "Pipeline Tools", 120, "connectToPipelineTools" );
	ctlposition( pipelineConnectCtrl, 96, 560, 142, 20 );
	ctlpage( 1, pipelineConnectCtrl );
	pipelineStatusCtrl = ctltext( "", pipelineToolStatus );
	ctlposition( pipelineStatusCtrl, 250, 563, 142, 20 );

	statusMessage = retrievePipelineToolStatus();
	updatePipelineToolStatusLabel( statusMessage );
	//-----End Job Options Tab----

	// Get the result of the dialog.
	dialogResult = reqpost();
	saveUISettings();
	if( !dialogResult )
		return;
	
	// Populate variables with values from the dialog.
	jobname         = getvalue( jobNameCtrl );
	comment         = getvalue( commentCtrl );
	department      = getvalue( departmentCtrl );
	group           = groups[ getvalue( groupCtrl ) ];
	contentDir      = getvalue( contentCtrl );
	configDir       = getvalue( configCtrl );
	frameStr        = getvalue( framesCtrl );
	chunkSize       = getvalue( chunkSizeCtrl );
	pool            = pools[ getvalue( poolCtrl ) ];
	secondaryPool = secondaryPools[ getvalue( secondaryPoolCtrl ) ];
	//poolMachinesOnly= getvalue( poolMachinesCtrl );
	priority        = getvalue( priorityCtrl );
	machineLimit    = getvalue( machineLimitCtrl );
	slaveTimeout    = getvalue( taskTimeoutCtrl );
	concurrentTasks = getvalue( concurrentCtrl );
	machineList = getvalue( machineListCtrl );
	isBlacklist = getvalue( isBlacklistCtrl );
	limitGroups     = getvalue( limitGroupsCtrl );
	dependencies    = getvalue( dependenciesCtrl );
	submitSuspended = getvalue( submitSuspendedCtrl );
	//deleteOnComplete= getvalue( deleteOnCompleteCtrl );
	onComplete      = onCompletes[ getvalue( onCompleteCtrl ) ];
	submitScene     = getvalue( submitSceneCtrl );
	lightwaveBuild  = builds[ getvalue( buildCtrl ) ];
	screamerNet     = getvalue( screamerNetCtrl );
	fprime          = getvalue( fprimeCtrl );
			
	// Clear the dialog.
	reqend();
	
	// Check for any warnings that should be displayed to the user.
	warningIndex = 1;
	warningMessages;
	
	// Warn the user if they are not submitting the scene file, and the scene path is local.
	if( !submitScene && isPathLocal( scene.filename ) )
	{
		warningMessages[ warningIndex ] = "The Lighwave scene is local and is not being submitted.";
		warningMessages[ warningIndex + 1 ] = "";
		warningIndex = warningIndex + 2;
	}
	
	// Show the warning(s) if necessary.
	if( warningIndex > 1 )
	{
		reqbegin( "Warning" );
		ctltext( "", warningMessages );      
		ctltext( "", "Click OK to submit this job, otherwise click Cancel." );
		if( !reqpost() )
			return;
		reqend();
	}
	
	// Create submit info file.
	submitInfoFilename = string( tempPath, "lw_submit_info.job" );
	submitInfoFile = File( submitInfoFilename, "w" ) || error( "ERROR: Submission: Cannot open submit info file for writing" );
	submitInfoFile.writeln( "Plugin=Lightwave" );
	submitInfoFile.writeln( "Name=", jobname );
	submitInfoFile.writeln( "Department=", department );
	submitInfoFile.writeln( "Group=", group );
	submitInfoFile.writeln( "Frames=", frameStr );
	submitInfoFile.writeln( "ChunkSize=", chunkSize );
	submitInfoFile.writeln( "Priority=", priority );
	submitInfoFile.writeln( "Pool=", pool );
	submitInfoFile.writeln( "SecondaryPool=", secondaryPool );
	//submitInfoFile.writeln( "PoolMachinesOnly=", poolMachinesOnly );
	submitInfoFile.writeln( "MachineLimit=", machineLimit );
	submitInfoFile.writeln( "Comment=", comment );
	//submitInfoFile.writeln( "DeleteOnComplete=", deleteOnComplete );
	submitInfoFile.writeln( "OnJobComplete=", onComplete );
	submitInfoFile.writeln( "TaskTimeoutMinutes=", slaveTimeout );
	submitInfoFile.writeln( "ConcurrentTasks=", concurrentTasks );
	submitInfoFile.writeln( "LimitGroups=", limitGroups );
	submitInfoFile.writeln( "JobDependencies=", dependencies );
	if( submitSuspended )
		submitInfoFile.writeln( "InitialStatus=Suspended" );
	
	if( isBlacklist )
		submitInfoFile.writeln( "Blacklist=", machineList );
	else
		submitInfoFile.writeln( "Blacklist=", machineList );
	
	count = 0;
	if( outputRgb && outputRgbPrefix != "" )
	{
		submitInfoFile.writeln( getOutputLine( outputRgbPrefix, outputRgbExt, outputFilenameFormat, count ) );
		count = count + 1;
	}
	if( outputAlpha && outputAlphaPrefix != "" )
		submitInfoFile.writeln( getOutputLine( outputAlphaPrefix, outputAlphaExt, outputFilenameFormat, count ) );

	submitInfoFile.close();

	concatenatePipelineSettingsToJob( submitInfoFilename, jobname );

	// Create job info file.
	jobInfoFilename = string( tempPath, "lw_job_info.job" );
	jobInfoFile = File( jobInfoFilename, "w" ) || error( "ERROR: Submission: Cannot open job info file for writing" );
	jobInfoFile.writeln( "LW_Version=", lwVersion );
	jobInfoFile.writeln( "LW_Build=", lightwaveBuild );
	jobInfoFile.writeln( "ContentDir=", contentDir );
	jobInfoFile.writeln( "ConfigDir=", configDir );
	jobInfoFile.writeln( "UseScreamerNet=", screamerNet );
	jobInfoFile.writeln( "UseFPrime=", fprime );
	if( !submitScene )
		jobInfoFile.writeln( "SceneFile=", scene.filename );
	jobInfoFile.close();

	// Submit the job to deadline.
	submitCommand = string( "\"", submitInfoFilename, "\" \"", jobInfoFilename, "\"" );
	if( submitScene )
		submitCommand = string( submitCommand, " \"", scene.filename, "\"" );
	results = deadlineCommand( submitCommand );
	
	// Dislpay the results to the user.
	reqbegin( "Results" );
	ctltext( "", results );
	ctltext( "", "Click OK or Cancel to continue." );
	reqpost();
	reqend();
}


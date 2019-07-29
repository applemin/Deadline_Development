{
	// Value to detect if user installed the incorrect script
	sentinal = 1;

	function trim(string)
	{
		return string
			.replace( "\n","" )
			.replace( "\r", "" )
			.replace( "^\s+", "" )
			.replace( "\s+$");
	}

	//Calls deadline with the given arguments.  Checks the OS and calls DeadlineCommand appropriately.
	function callDeadlineCommand( args )
	{
		var commandLine = "";
		
		deadlineBin = $.getenv("DEADLINE_PATH")
		if( (deadlineBin === null || deadlineBin == "") && (system.osName == "MacOS" ))
		{
			deadlineBin = system.callSystem("cat /Users/Shared/Thinkbox/DEADLINE_PATH");
		}
		
		deadlineBin = trim(deadlineBin);
		//On OSX, we look for the DEADLINE_PATH file. On other platforms, we use the environment variable.
		if (deadlineBin == "" )
		{
			commandLine =  "\"deadlinecommand\" "
		}
		else
		{
			if (system.osName == "MacOS")
			{
				commandLine = "\"" + deadlineBin + "/deadlinecommand\" ";
			}
			else
			{
				commandLine = "\"" + deadlineBin + "\\deadlinecommand.exe\" ";
			}
		}
		
		commandLine = commandLine + args;
		
		result = system.callSystem(commandLine);

		if( system.osName == "MacOS" )
		{
			result = cleanUpResults( result, "Could not set X local modifiers" );
			result = cleanUpResults( result, "Could not find platform independent libraries" );
			result = cleanUpResults( result, "Could not find platform dependent libraries" );
			result = cleanUpResults( result, "Consider setting $PYTHONHOME to" );
			result = cleanUpResults( result, "using built-in colorscheme" );
		}
		//result = result.replace("\n", "");
		//result = result.replace("\r", "");
		return result;
	}
	
	// Looks for the given txt in result, and if found, that line and all previous lines are removed.
	function cleanUpResults( result, txt )
	{
		newResult = result;
		
		txtIndex = result.indexOf( txt );
		if( txtIndex >= 0 )
		{
			eolIndex = result.indexOf( "\n", txtIndex );
			if( eolIndex >= 0 )
				newResult = result.substring( eolIndex + 1 );
		}
		
		return newResult;
	}
	
	scriptPath = callDeadlineCommand( "GetRepositoryFilePath submission/AfterEffects/Main/SubmitAEToDeadline.jsx" ).replace("\r","").replace("\n","");

	subFileHandle = File( scriptPath );

	// Handle new pathing rules
	if ( !subFileHandle.exists )
	{
		scriptPath = scriptPath.replace( "^/Volumes", "" );   // OS X
		scriptPath = scriptPath.replace( "^(.*):\\", "/\1/"); // Windows

		subFileHandle = File( scriptPath );
		if ( !subFileHandle.exists )
		{
			alert( "The SubmitAEToDeadline.jsx script could not be found in the Deadline Repository (" + scriptPath + "). Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository." );
		}
	}

	subFileHandle.open( "r" );
	eval( subFileHandle.read() );
	subFileHandle.close();
}


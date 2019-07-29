submissionDir = callDeadlineCommand( ["-GetRepositoryPath", "submission/Harmony/Main"] )
scriptPath = trim(submissionDir) + "/SubmitHarmonyToDeadline.js";

include( scriptPath );

function callDeadlineCommand( args )
{
	var commandLine = "";
	var deadlineBin = "";
	
	deadlineBin = System.getenv( "DEADLINE_PATH" )
	if( ( deadlineBin === null || deadlineBin == "" ) && about.isMacArch() )
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
	
function SubmitToDeadline()
{	
	if (typeof InnerSubmitToDeadline === 'undefined') 
	{
		MessageBox.information( "Failed to import Deadline" );
	}
	else
	{
		InnerSubmitToDeadline( submissionDir );
	}
	
}


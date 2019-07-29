-- DEPRECATED NOTE:
-- This script is for Eyeon versions of Generation. Not for Blackmagic versions.
-- It is now deprecated. Please do not modify this file because it is for legacy versions of Generation.
-- All new changes will be made in the "DeadlineBlackmagicGenerationClient.lua" version of the script.

--------------------------------------------------------
-- Proxy Generation Deadline Submission Script
--------------------------------------------------------

--------------------------------------------------------
-- Set the temp directory.
--------------------------------------------------------
tempDir = os.getenv( "TEMP" )

submitOutputFile = tempDir .. "\\submitOutput.txt"
submitExitCodeFile = tempDir .. "\\submitexitcode.txt"

--------------------------------------------------------
-- Helper Functions
--------------------------------------------------------
function GetNumberFromFile( filename )
	local fh = io.open( filename, 'r' )
	if fh == nil then
		return nil
	end
	
	local result = fh:read( "*l" )
	io.close( fh )
	
	return tonumber( result )
end

function RunDeadlineCommand( options )

	os.remove( submitExitCodeFile )
	
	local deadlineBin = os.getenv( "DEADLINE_PATH" )
	local executeSucceeded = executebg( "\"" .. deadlineBin .. "\\deadlinecommandbg.exe\" -outputfiles \"" .. submitOutputFile .. "\" \"" .. submitExitCodeFile .. "\" " .. options )
	if not executeSucceeded then
		messagebox( "Could not execute deadlinecommandbg.exe", "Submit to Deadline Proxy" )
		return nil
	end
	
	local incr = 1/10
	-- Give it 3600 seconds to complete
	local i = 0
	for i = 0,3600,incr do
		if fileexists( submitExitCodeFile ) then
			break
		end
		wait(incr)
	end
	
	if not fileexists( submitExitCodeFile ) then
		messagebox( "Failed to get a response from deadlinecommandbg.exe", "Submit to Deadline Proxy" )
		return nil
	end
	
	retcode = GetNumberFromFile( submitExitCodeFile )
	if retcode == nil then
		messagebox( "Failed to get a valid return code from deadlinecommandbg.exe", "Submit to Deadline Proxy" )
		return nil
	end
	
 	os.remove( submitExitCodeFile )
	
	return retcode
end

function GetDeadlineRepositoryPath()

	local retcode = RunDeadlineCommand( "-getrepositoryfilepath submission/Generation/Main/SubmitGenerationToDeadline.lua" )
	if retcode ~= 0 then
		messagebox( "Failed to get repository root from deadlinecommandbg.exe", "Submit to Deadline Proxy" )
		return nil
	end
	
	local result = nil
	local fh = io.open( submitOutputFile )
	if fh ~= nil then
		result = fh:read( "*l" )
		io.close(fh)        
	end
	
	os.remove( submitOutputFile )
	
	return result
end

--------------------------------------------------------
-- Main Script
--------------------------------------------------------

gen = App()
for key,value in pairs(getmetatable(gen)) do
    print("found member " .. key);
end

scriptPath = GetDeadlineRepositoryPath()
print ( scriptPath )
if not fileexists( scriptPath ) then
	d = {}
	d[1] = {"Msg", Name = "Submit to Deadline Proxy", "Text", ReadOnly = true, Lines = 10, Default = "The SubmitGenerationToDeadline.eyeonscript script could not be\nfound in the Deadline Repository. Please make sure\nthat the Deadline Client has been installed on this\nmachine, that the Deadline Client bin folder is set in the DEADLINE_PATH\nenvironment variable, and that the Deadline Client has been\nconfigured to point to a valid Repository." }
	comp:AskUser( "Submit to Deadline Proxy" , d )

	--MessageDlg ("Submit to Deadline Proxy", "The SubmitGenerationToDeadline.eyeonscript script could not be\nfound in the Deadline Repository. Please make sure\nthat the Deadline Client has been installed on this\nmachine, that the Deadline Client bin folder is set in the DEADLINE_PATH\nenvironment variable, and that the Deadline Client has been\nconfigured to point to a valid Repository.", "Okay" ) 
	
	return nil
end

print( string.format("Running script \"%s\"\n", scriptPath) );
dofile( scriptPath )

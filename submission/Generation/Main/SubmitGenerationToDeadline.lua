-- DEPRECATED NOTE:
-- This script is for Eyeon versions of Generation. Not for Blackmagic versions.
-- It is now deprecated. Please do not modify this file because it is for legacy versions of Generation.
-- All new changes will be made in the "SubmitBlackmagicGenerationToDeadline.lua" version of the script.

--------------------------------------------------------
-- Main Generation Deadline Submission Script
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
	print "in RunDeadlineCommand()"
	os.remove( submitExitCodeFile )
	
	local deadlineBin = os.getenv( "DEADLINE_PATH" )
	local executeSucceeded = executebg( "\"" .. deadlineBin .. "\\deadlinecommandbg.exe\" -outputfiles \"" .. submitOutputFile .. "\" \"" .. submitExitCodeFile .. "\" " .. options )
	if not executeSucceeded then
		MessageBox( "Could not execute deadlinecommandbg.exe", "Submit to Deadline Proxy" )
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
		MessageBox( "Failed to get a response from deadlinecommandbg.exe", "Submit to Deadline Proxy" )
		return nil
	end
	
	retcode = GetNumberFromFile( submitExitCodeFile )
	if retcode == nil then
		MessageBox( "Failed to get a valid return code from deadlinecommandbg.exe", "Submit to Deadline Proxy" )
		return nil
	end
	
 	os.remove( submitExitCodeFile )
	
	return retcode
end

function GetDeadlineRepositoryPath()

	local retcode = RunDeadlineCommand( "-getrepositoryfilepath scripts/Submission/FusionSubmission.py" )
	if retcode ~= 0 then
		MessageBox( "Failed to get repository path from deadlinecommandbg.exe", "Submit to Deadline Proxy" )
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

gen:Log( "========================================================================================================" )
gen:Log( "Submit Generation To Deadline" )
gen:Log( "========================================================================================================" )

print "inside Main()"

-- Get the project
project = gen:Project()
projectPath = project:Path()
gen:Log( "Project path: " .. projectPath )

jobName = project:Name()
gen:Log( "Project name: " .. jobName )

compFiles = ""

-- Get the list of selected items
thumbTable = project:SelectedThumbs()
if #thumbTable > 0 then
	gen:Log( "Selection count: " .. #thumbTable )

	-- Loop through the selected items.
	for i,thumb in ipairs(thumbTable) do
		-- Only submit it if it is a valid comp
		comp = thumb:RefFilename()
		if comp then
			-- Handle relative paths.
			cleanComp = string.gsub( comp, [[PROJECT:]], projectPath )
			gen:Log( "Submitting comp: " .. cleanComp )
			
			-- Append comp to the list of comp files
			compFiles = compFiles .. "\"" .. cleanComp .. "\" "
		end
	end
	
	-- Get the Fusion monitor submission script path
	scriptPath = GetDeadlineRepositoryPath()
	if not fileexists( scriptPath ) then
		gen:Log( "The FusionSubmission.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is in your PATH, and that the Deadline Client has been configured to point to a valid Repository." )
	else
		-- Build up the script arguments
		scriptArgs = "\"" .. jobName .. "\" " .. compFiles
		
		-- Open the submission script
		gen:Log( "Running submission script " .. scriptPath )
		RunDeadlineCommand( "-executeScript \"" .. scriptPath .. "\" " .. scriptArgs )
	end
else
	gen:Log( "Nothing selected\n" )
end

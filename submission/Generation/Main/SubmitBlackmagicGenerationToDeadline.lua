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

local function iswindows()
	return (package.config:sub(1,1) == "\\")
end

local function rtrim(s)
  return s:gsub( "^([%s]*[^%s]*)%s*$", "%1" )
end

local function getDeadlineCommand()
	deadlineCommand = ""
	deadlinePath = os.getenv( "DEADLINE_PATH" )
	
	if not iswindows() and ( deadlinePath == nil or deadlinePath == "" ) then
		if fileexists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) then
			input = assert( io.open( "/Users/Shared/Thinkbox/DEADLINE_PATH", 'r' ) )
			deadlinePath = assert( input:read( '*a' ) )
			input:close()
			
			deadlinePath = rtrim( deadlinePath )
		end
	end
	
	if deadlinePath == nil or deadlinePath == "" then
		deadlineCommand = "deadlinecommand"
	else
		deadlineCommand = deadlinePath .."/deadlinecommand"
	end
		
	return deadlineCommand
end

local function RunDeadlineCommand( options )

	deadlineCommand = getDeadlineCommand()
	local command, commandOutput = "", ""
	local input;

	print( "Running command: \"" .. deadlineCommand .. "\" " .. options )

	if iswindows() then
		--io.popen Strips the first and last Quote in a command if there are more then 2 quotes so we wrap everything in quotes to guarantee this will not fail.
		command = "\"\"" .. deadlineCommand .. "\" " .. options .. "\""
		input = assert( io.popen( command, 'r' ) )
		commandOutput = assert( input:read( '*a' ) )
		input:close()
	else
		--os.execute Strips the first and last Quote in a command if there are more then 2 quotes so we wrap everything in quotes to guarantee this will not fail.
		local tempFile = "/tmp/deadline_fusion_output.txt"
		os.remove( tempFile )
		
		command = "\"\"" .. deadlineCommand .. "\" " .. options .. " > \"" .. tempFile .. "\"\""
		os.execute( command )
		input = assert( io.open( tempFile, 'r' ) )
		commandOutput = assert( input:read( '*a' ) )
		input:close()
		
		os.remove( tempFile )
	end
	
	return rtrim(commandOutput)
end

function GetDeadlineRepositoryFilePath()
	return RunDeadlineCommand( "-getrepositoryfilepath scripts/Submission/FusionSubmission.py" )
end

--------------------------------------------------------
-- Main Script
--------------------------------------------------------
gen = App()

gen:Log( "========================================================================================================" )
gen:Log( "Submit Generation To Deadline" )
gen:Log( "========================================================================================================" )

-- Get the project
project = gen:ProjectGet()
projectPath = project.Path

gen:Log( "Project path: " .. projectPath )

jobName = project.Name
gen:Log( "Project name: " .. jobName )

compFiles = ""

-- Get the list of selected items
thumbTable = project:SelectedVersions()
if #thumbTable > 0 then
	gen:Log( "Selection count: " .. #thumbTable )

	-- Loop through the selected items.
	for i,thumb in ipairs(thumbTable) do
		-- Only submit it if it is a valid comp
		comp = thumb:GetLoader():RefFilename()
		if comp then
			-- Handle relative paths.
			cleanComp = string.gsub( comp, [[PROJECT:]], projectPath )
			gen:Log( "Submitting comp: " .. cleanComp )
			
			-- Append comp to the list of comp files
			compFiles = compFiles .. "\"" .. cleanComp .. "\" "
		end
	end
	
	-- Get the Fusion monitor submission script path
	scriptPath = GetDeadlineRepositoryFilePath()
	if not fileexists( scriptPath ) then
		gen:Log( "The FusionSubmission.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is in your PATH, and that the Deadline Client has been configured to point to a valid Repository." )
	else
		-- Build up the script arguments
		scriptArgs = "--name \"" .. jobName .. "\" " .. compFiles
		
		-- Open the submission script
		gen:Log( RunDeadlineCommand( "-executeScript \"" .. scriptPath .. "\" " .. scriptArgs ) )
	end
else
	gen:Log( "Nothing selected\n" )
end

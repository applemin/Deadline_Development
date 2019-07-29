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
function MessageBox( msg, title )
	local d = {}
	d[1] = {"Msg", Name = msg, "Text", ReadOnly = true, Lines = 0 }
	comp:AskUser( title, d )
end

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
  local n = #s
  while n > 0 and s:find("^%s", n) do n = n - 1 end
  return s:sub(1, n)
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

	if iswindows() then
		command = "\"" .. deadlineCommand .. "\" " .. options
		input = assert( io.popen( command, 'r' ) )
		commandOutput = assert( input:read( '*a' ) )
		input:close()
	else
		
		local tempFile = "/tmp/deadline_fusion_output.txt"
		os.remove( tempFile )
		
		command = "\"" .. deadlineCommand .. "\" " .. options .. " > " .. tempFile
		os.execute( command )
		input = assert( io.open( tempFile, 'r' ) )
		commandOutput = assert( input:read( '*a' ) )
		input:close()
		
		os.remove( tempFile )
	end
	
	return rtrim(commandOutput)
end

function GetDeadlineRepositoryPath()
	local path = RunDeadlineCommand( "-GetRepositoryFilePath submission/Generation/Main/SubmitBlackmagicGenerationToDeadline.lua" )
	
	if ( path == "" or path == nil ) then
		MessageBox( "Failed to get repository path from deadlinecommand", "Submit to Deadline Proxy" )
		return nil
	else
		return path
	end
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
	d[1] = {"Msg", Name = "Submit to Deadline Proxy", "Text", ReadOnly = true, Lines = 10, Default = "The SubmitBlackmagicGenerationToDeadline.lua script could not be\nfound in the Deadline Repository. Please make sure\nthat the Deadline Client has been installed on this\nmachine, that the Deadline Client bin folder is set in the DEADLINE_PATH\nenvironment variable, and that the Deadline Client has been\nconfigured to point to a valid Repository." }
	comp:AskUser( "Submit to Deadline Proxy" , d )

	--MessageDlg ("Submit to Deadline Proxy", "The SubmitGenerationToDeadline.eyeonscript script could not be\nfound in the Deadline Repository. Please make sure\nthat the Deadline Client has been installed on this\nmachine, that the Deadline Client bin folder is set in the DEADLINE_PATH\nenvironment variable, and that the Deadline Client has been\nconfigured to point to a valid Repository.", "Okay" ) 
	
	return nil
end

print( string.format("Running script \"%s\"\n", scriptPath) );
dofile( scriptPath )

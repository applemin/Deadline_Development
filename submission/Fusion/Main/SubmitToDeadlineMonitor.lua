--------------------------------------------------------
-- Fusion 5 Deadline Submission Script
--------------------------------------------------------

---------------------------------------------------------------------------------
-- These are included here, just in case eyeon.scriptlib is not available.
---------------------------------------------------------------------------------
function deadlineGetExtension(name)
	local i = 0
	for i = string.len(name), 1, -1 do
		local teststring = string.sub(name, i, i)
		if teststring == "." then
			return string.sub(name, i+1, -1)
		end
	end
end

function deadlineTrimExtension(filename)
	local period_loc = 0
	--print(filename)
	local i = 0
	for i = string.len(filename), 1, -1 do
		if string.sub(filename, i, i) == "." then
			period_loc = i
			break
		end
	end
	--print(string.sub(filename, 1, period_loc-1))
	return string.sub(filename, 1, period_loc-1)
end

function deadlineGetFilePath(path)
	local i = 0
	for i = string.len(path), 1, -1 do
		teststring = string.sub(path, i, i)
		if teststring == "\\" or teststring == "/" then
			return string.sub(path, 1, i)
		end
	end
end

---------------------------------------------------------------------------------
-- Additional helper functions.
---------------------------------------------------------------------------------

local function iswindows()
	return (package.config:sub(1,1) == "\\")
end

local function rtrim(s)
  local n = #s
  while n > 0 and s:find("^%s", n) do n = n - 1 end
  return s:sub(1, n)
end

-- Checks if the path is saving to a movie format.
function pathIsMovieFormat(path)
	local extension = deadlineGetExtension(path)
	if extension ~= nil then 
		extension = string.lower(extension)
		if		( extension == "avi" ) or ( extension == "vdr" ) or ( extension == "wav" ) or
				( extension == "dvs" ) or
				( extension == "fb"  ) or
				( extension == "omf" ) or ( extension == "omfi" ) or
				( extension == "stm" ) or
				( extension == "tar" ) or
				( extension == "vpv" ) or
				( extension == "mov" ) then
			return true
		end
	end
	return false
end

-- Replaces the frame number in the filename with the given frame number.
function replaceFrameNo(filename, frameNumber)
	-- the filename without the extension
	local fileNoExt = deadlineTrimExtension(filename)
	-- just the extension (no dot)
	local fileExt = deadlineGetExtension(filename)
	
	local numberStart = string.len(fileNoExt)

	local i = 0
	for i = string.len(fileNoExt), 1, -1 do
		if tonumber(string.sub(fileNoExt, i, i)) == nil then
			numberStart = i
			break
		end
	end
	
	local fileNoNumbers = string.sub( fileNoExt, 1, numberStart )
	
	local digitCount = string.len(fileNoExt) - numberStart
	if digitCount == 0 then
		digitCount = 4
	end
	
	local digits
	-- if no frame number is specified, pad it with ? characters,
	-- otherwise replace the frame number
	if frameNumber == nil then
		digits = "?"
	
		while string.len(digits) < digitCount do
			digits = "?" .. digits
		end
	else
		digits = tostring( frameNumber )
	
		while string.len(digits) < digitCount do
			digits = "0" .. digits
		end
	end
	
	if fileExt == nil then
		fileExt = ""
	end
	
	return fileNoNumbers .. digits .. "." .. fileExt
end

-- Check the table that stores the integration settings for a specific key
function MessageBox(msg, theTitle)
	local d = {}
	d[1] = {"Msg", Name = msg, "Text", ReadOnly = true, Lines = 0 }
	comp:AskUser( theTitle, d )
end

function OKCancelDlg(msg, title)
	local d = {}
	d[1] = {"Msg", Name = msg, "Text", ReadOnly = true, Lines = 0 }
	local dialog = comp:AskUser( title, d )

	if dialog == nil then
		return false
	else
		return true
	end
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
		-- On *nix systems io.popen doesn't grab stdout, so we use os.execute and pipe the results into a file that we read.
		local tempFile = os.tmpname()
		
		command = "\"" .. deadlineCommand .. "\" " .. options .. " > \"" .. tempFile .. "\""
		os.execute( command )
		input = assert( io.open( tempFile, 'r' ) )
		commandOutput = assert( input:read( '*a' ) )
		input:close()
		
		os.remove( tempFile )
	end
	
	return rtrim(commandOutput)
end

function GetDeadlineRepositoryFilePath(subdir)

	local path = ""
	local options = ""

	if (subdir == nil or subdir == "" ) then
		options = "-GetRepositoryPath"
	else
		options = "-GetRepositoryFilePath " .. subdir
	end
	
	path = RunDeadlineCommand( options )
	
	if ( path == nil or path == "" ) then
		MessageBox( "Failed to get repository path from deadlinecommand.exe", "Submit to Deadline Proxy" )
		return nil
	end
	return path
end

-- Does a few basic checks on the file
function SanityCheck(comp)
	local loaders = GetLoaders(comp)
	local savers = GetSavers(comp)
	local message = ""

	local i = 0
	for i = 1, table.getn(loaders), 1 do
		local attr = loaders[i]:GetAttrs()
		if not attr.TOOLB_PassThrough then
			local cl = attr.TOOLST_Clip_Name
				if cl == nil then
					message = message .. "Loader \"" .. attr.TOOLS_Name .. "\" has no input path specified.\n"
				else
					for j = 1, table.getn(cl) do
						local name = cl[j]
						if( string.sub(name, 1, 2) == "C:" or string.sub(name, 1, 2) == "c:" ) then
								message = message .. "Loader \"" .. attr.TOOLS_Name .. "\" is loading from the local c: drive.\n"
						else
							if( string.sub(name, 1, 2) == "D:" or string.sub(name, 1, 2) == "d:" ) then
								message = message .. "Loader \"" .. attr.TOOLS_Name .. "\" is loading from the local d: drive.\n"
							else
								if( string.sub(name, 1, 2) == "E:" or string.sub(name, 1, 2) == "e:" ) then
									message = message .. "Loader \"" .. attr.TOOLS_Name .. "\" is loading from the local e: drive.\n"
								end
							end
						end
					end
				end
		end
	end

	local saverCount = 0
	for i = 1, table.getn(savers) do
		local attr = savers[i]:GetAttrs()
		if not attr.TOOLB_PassThrough then
			local cl = savers[i].Clip[fusion.TIME_UNDEFINED]
			local name = cl
			
			if( string.sub(name, 1, 2) == "C:" or string.sub(name, 1, 2) == "c:" ) then
				message = message .. "Saver \"" .. attr.TOOLS_Name .. "\" is saving to the local c: drive.\n"
			else
				if( string.sub(name, 1, 2) == "D:" or string.sub(name, 1, 2) == "d:" ) then
						message = message .. "Saver \"" .. attr.TOOLS_Name .. "\" is saving to the local d: drive.\n"
				else
						if( string.sub(name, 1, 2) == "E:" or string.sub(name, 1, 2) == "e:" ) then
								message = message .. "Saver \"" .. attr.TOOLS_Name .. "\" is saving to the local e: drive.\n"
						end
				end
			end
			
			name = fusion:MapPath( name )
							
			-- check to make sure the saver contains a complete path
			if iswindows() then
				x, y = string.find( name, "%a:" )
				if not (x == 1) then
					tempName = string.gsub( name, "\\", "/" )
					x, y = string.find( tempName, "//" )
					if not (x == 1) then
						message = message .. "Saver \"" .. attr.TOOLS_Name .. "\" does not contain a complete output path.\n"
					end
				end
			end
			
			local nameTrim = deadlineTrimExtension(name)
			local endDigitsCount = 0
			for k = string.len(nameTrim), 1, -1 do
				if (tonumber(string.sub( nameTrim, k, k )) == nil) then
					break
				end
				endDigitsCount = endDigitsCount + 1
			end
			if endDigitsCount > 0 and endDigitsCount < 4 then
				if not pathIsMovieFormat(name) then
					message = message .. "Saver \"" .. attr.TOOLS_Name .. "\" output file ends in a small number\n"
				end
			end
			if( name == "" ) then
				message = message .. "Saver \"" .. attr.TOOLS_Name .. "\" has an empty output.\n"
			end
			
			if cl==nil then
				message = message .. "Saver \"" .. attr.TOOLS_Name .. "\" has no output.\n"
			end
			saverCount = saverCount + 1
		end
	end

	if saverCount == 0 then
		message = message .. "There are no savers which haven't been passed through.\n"
	end
	
	local deadlinePath= GetDeadlineRepositoryFilePath("submission/Fusion/Main/CustomSanityChecks.eyeonscript")
	if deadlinePath ~= nil and deadlinePath ~= "" then
		local customSanityScript = (deadlinePath):gsub("%s+", "")
		if fileexists( customSanityScript ) then
			dofile( customSanityScript )
			print( "Executed custom sanity check script, " .. customSanityScript )
			message = message .. CustomDeadlineSanityChecks(comp)
		end
	end
	
	return message
end

function writeDeadlineSettings()
	
	settingNames = { "DEADLINE_AutoTimeout", "DEADLINE_CheckOutput", "DEADLINE_DefaultChunkSize", "DEADLINE_DefaultCommandLineMode",
		"DEADLINE_DefaultDepartment", "DEADLINE_DefaultFirstAndLast", "DEADLINE_DefaultGroup", "DEADLINE_DefaultMachineLimit",
		"DEADLINE_DefaultPool", "DEADLINE_DefaultPriority", "DEADLINE_DefaultSecondaryPool", "DEADLINE_DefaultSlaveTimeout",
		"DEADLINE_FrameRange", "DEADLINE_LimitGroups", "DEADLINE_OutputFilenames", "DEADLINE_PostJobScript",
		"DEADLINE_SubmitComp" }
	settings = {}
	hasElements = false
	for k, v in pairs(settingNames) do
		settingVal = fusion:GetData(v)
		if settingVal ~= nil then 
			settings[v] = settingVal
			hasElements = true
		end 
	end
	
	if hasElements == false then
		return ""
	end
	
	-- Set the temp directory.
	tempDir = nil
	if iswindows() then
		tempDir = os.getenv( "TEMP" )
	else
		tempDir = "/tmp"
	end
	
	settingsFile = tempDir .. "/DeadlineFusionSettings.txt"
	
	fh = io.open( settingsFile, 'w' )
	if fh == nil then
		MessageBox( "Could not generate settings file", "Submit to Deadline" )
		return
	end
	
	fh:write( '{"DeadlineSettings":{\n' )
	local isFirst = true
	for settingName, settingVal in pairs(settings) do
		if isFirst then
			isFirst = false
		else
			fh:write( ',\n' )
		end
		fh:write( '"' .. settingName .. '":"' .. settingVal .. '"' )
	end
	fh:write( '\n}\n}' )
	
	io.close(fh)
	
	return settingsFile
	
end

local function GetCompOutputs()
	local savers = GetSavers(composition)
	local results = {}
	local count = 1
	local i = 0

	for i, saver in pairs(savers) do
		if not saver:GetAttrs().TOOLB_PassThrough then
			-- TODO sanity check: outputDir == nil => saver without an output specified
			outPath = saver.Clip[1]
			-- For non-movie formats, do the padding with ? characters
			if not pathIsMovieFormat(outPath) then
				outPath = replaceFrameNo( outPath, nil )
			end
			results[count] = fusion:MapPath( outPath )
			count = count + 1
		end
	end

	return results
end

-- end functions
-- Set the temp directory.
ca = comp:GetAttrs()

-- First check if the file has ever been saved
-- If it hasn't, report an error and exit
if ca.COMPS_FileName == "" then
	MessageBox( "You must save the comp before you can submit it.", "Submit to Deadline" )
	return
end

-- Reset limit group option in case previous custom sanity check modified it
sanityMessage = SanityCheck(composition)
if not (sanityMessage == "") then
	if not OKCancelDlg( sanityMessage .. "\n\nPress OK to submit this job.", "Sanity Check" ) then
		return
	end
end

-- Now check if the flow was modified. If it is, ask to save it.
if ca.COMPB_Modified then
	if  OKCancelDlg( "The comp has been modified, save it for submission?", "Submit to Deadline" ) then
		comp:Save(ca.COMPS_FileName)
	else
		return
	end
end

local settingsFile = writeDeadlineSettings()

local repositoryPath = GetDeadlineRepositoryFilePath("scripts/Submission/FusionSubmission.py")
local scriptPath = rtrim( repositoryPath )
local scriptCommand = "-ExecuteScript \"" .. scriptPath .. "\""

-- Append command-line arguments to pass to the submission dialog

local outputs = GetCompOutputs()
local i = 0
local output = ""

for i, output in pairs(outputs) do
	scriptCommand = scriptCommand .. " --output \"" .. output .. "\""
end

local framerange = tostring(ca.COMPN_RenderStartTime) .. "-" .. tostring(ca.COMPN_RenderEndTime)
scriptCommand = scriptCommand .. " --frames \"" .. framerange .. "\""

local fusionVersion = fusion:GetAttrs().FUSIONS_Version
fusionVersion = fusionVersion:match("(%d+%.%d+)")
scriptCommand = scriptCommand .. " --fusion-version \"" .. fusionVersion .. "\""

if not (settingsFile == "") then
	scriptCommand = scriptCommand .. " --settings \"" .. settingsFile .. "\""
end

scriptCommand = scriptCommand .. " \"" .. ca.COMPS_FileName .. "\""

print( RunDeadlineCommand( scriptCommand ) )

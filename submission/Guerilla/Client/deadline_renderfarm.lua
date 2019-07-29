
-- Deadline renderfarm interface
class( "Deadline", "RenderFarm" )

local function iswindows()
    return (package.config:sub(1,1) == "\\")
end

local function rtrim(s)
  local n = #s
  while n > 0 and s:find("^%s", n) do n = n - 1 end
  return s:sub(1, n)
end

local function fixpath( path )
    path = path:gsub( "\\", "/" )
    while string.len( path ) > 0 and string.sub( path, string.len( path ) - 1 ) == "/" do
        path = string.sub( path, -1 )
    end
    return path
end

local function fileexists(name)
   local f=io.open(name,"r")
   if f~=nil then io.close(f) return true else return false end
end

local function rundeadlinecommand( deadlinePath, options )
    local s = ""

    if iswindows() then
        local command = "\"" .. deadlinePath .. "/deadlinecommand.exe\" " .. options
        local f = assert( io.popen( command, 'r' ) )
        s = assert( f:read( '*a' ) )
        f:close()
    else
        local tempFile = "/tmp/deadline_guerilla_output.txt"
        os.remove( tempFile )
        
        local command = "\"" .. deadlinePath .. "/deadlinecommand\" " .. options .. " > " .. tempFile
        os.execute( command )
        local f = assert( io.open( tempFile, 'r' ) )
        s = assert( f:read( '*a' ) )
        f:close()
        
        os.remove( tempFile )
    end
    
    return rtrim(s)
end

local function messagebox( message, title )
    -- Only display the message box if 'ui.titlewindow' is defined. Otherise, we're in nogui mode.
    if ui.titlewindow then
        local win = ui.titlewindow()
        win:settitle( title )
        
        local label = ui.text( "label", win )
        label:settext( message )
        label:setpos { x=8, y=8, w=ui.right-16, h=20 }
        function label:editupdated( text )
            print( text )
        end
        
        local okbutton = ui.textbutton( "okbutton", win, "OK" )
        okbutton:setpos { x=8, w=100, h=20, y=ui.bottom - 8 }
        function okbutton:buttonclicked()
            win:destroy()
        end
        
        win:setpos { w=600, h=60 }
        win:show()
    else
        print( title .. ": " .. message )
    end
end

function Deadline:construct()
	LocalPlug( self, "DeadlinePath", Plug.NoSerial, types.string, "" )
    
    local deadlinePath = os.getenv( "DEADLINE_PATH" )
    print( "Checking DEADLINE_PATH environment variable" )
    if deadlinePath then
        deadlinePath = fixpath( deadlinePath )
        self.DeadlinePath:Set( deadlinePath )
    else
        print( "DEADLINE_PATH environment variable not defined" )
    end
end

local typeopenmonitor = types.actionbutton("Open")
function typeopenmonitor.action (plugs)
	if plugs and plugs[1] then
        local deadline = plugs[1]:getnode()
        local deadlinePath = deadline.DeadlinePath:get()
        
        local monitorPath = ""
        if iswindows() then
            monitorPath = deadlinePath .. "/deadlinemonitor.exe"
        else
            monitorPath = deadlinePath .. "/deadlinemonitor"
        end

		print( "Launching Deadline Monitor: " .. monitorPath )
        os.execute( 'start "" "' .. monitorPath .. '"' )
	end
end

function Deadline:gettemplate()
	return
		{ "Deadline",
			{
				{ "Deadline Path", self.DeadlinePath },
                { "Open Monitor", self.DeadlinePath, typeopenmonitor },
			}
		}
end

function Deadline:submit( jobs, options )
    local success = false
    
    local deadlinePath = self.DeadlinePath:get()
    local scriptPath = rundeadlinecommand( deadlinePath, "-getrepositoryfilepath submission/Guerilla/Main/SubmitGuerillaToDeadline.lua" )
    scriptPath = fixpath( scriptPath )
    
    if fileexists( scriptPath ) then
        assert( loadfile( scriptPath ) )()
        success = submittodeadline( self, jobs, options, deadlinePath )
    else
        print( "The SubmitGuerillaToDeadline.lua script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has beenconfigured to point to a valid Repository." )
        messagebox( "The SubmitGuerillaToDeadline.lua script could not be found. See Console for details.", "Submission Error" )
    end
    
    return success
end

-- The main deadline renderfarm interface
RenderFarm.declare( Deadline() )
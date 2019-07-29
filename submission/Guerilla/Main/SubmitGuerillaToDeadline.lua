
local function iswindows()
    return (package.config:sub(1,1) == "\\")
end

local function _osgetenv( var )
	return os.getenv( var ) or ""
end

local function expand( str )
	repeat
		local	occ
		str, occ = string.gsub( str, "%$%((.-)%)", _osgetenv )
	until occ == 0
	return str
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
    
    local commandPath = ""
    if iswindows() then
        local command = "\"\"" .. deadlinePath .. "/deadlinecommand.exe\" " .. options .. "\""
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

local function splitstring( str, sep )
    local sep, fields = sep or ":", {}
    local pattern = string.format( "([^%s]+)", sep )
    str:gsub( pattern, function(c) fields[#fields+1] = c end )
    return fields
end

local function splitkeyvalue( str )
    local keyValue = nil

    local s, e = str:find( "=" )
    if s then
        keyValue = {}
        table.insert( keyValue, str:sub( 1, s - 1 ) )
        
        if s < str:len() then
            table.insert( keyValue, str:sub( s + 1 ) )
        else
            table.insert( keyValue, "" )
        end
    end
    
    return keyValue
end

local function makeString( len )
    if len <= 0 then
        len = 1
    end

    local s = ""
    for i = 1, len do
        local n = math.random(97, 122)
        s = s .. string.char( n )
    end
    
    return s
end

local function submitdeadlinejob( deadlinePath, deadlineTemp, submissionOptions, script, args, frameList, jobsdir, imagesdir, title, dependencies, frameDependent )
    
    -- Make a unique string for the job submission files.
    local uniqueString = makeString( 5 )
    
    -- Create the job info file.
    local jobInfoFileName = deadlineTemp .. "/guerilla_job_info_" .. uniqueString .. ".txt"
    local jobInfoFile = io.open( jobInfoFileName, 'w' )
    
    jobInfoFile:write( "Plugin=Guerilla\n" )
    jobInfoFile:write( "Name=" .. title .. "\n" )
    jobInfoFile:write( "Frames=" .. frameList .. "\n" )
    jobInfoFile:write( "ChunkSize=1\n" )
    jobInfoFile:write( "BatchName=" .. submissionOptions[ "BatchName" ] .. "\n" )
    jobInfoFile:write( "Comment=" .. submissionOptions[ "Comment" ] .. "\n" )
    jobInfoFile:write( "Department=" .. submissionOptions[ "Department" ] .. "\n" )
    jobInfoFile:write( "Pool=" .. submissionOptions[ "Pool" ] .. "\n" )
    jobInfoFile:write( "SecondaryPool=" .. submissionOptions[ "SecondaryPool" ] .. "\n" )
    jobInfoFile:write( "Group=" .. submissionOptions[ "Group" ] .. "\n" )
    jobInfoFile:write( "Priority=" .. submissionOptions[ "Priority" ] .. "\n" )
    jobInfoFile:write( "TaskTimeoutMinutes=" .. submissionOptions[ "TaskTimeoutMinutes" ] .. "\n" )
    jobInfoFile:write( "EnableAutoTimeout=" .. submissionOptions[ "EnableAutoTimeout" ] .. "\n" )
    jobInfoFile:write( "LimitConcurrentTasksToNumberOfCpus=" .. submissionOptions[ "LimitConcurrentTasksToNumberOfCpus" ] .. "\n" )
    jobInfoFile:write( "MachineLimit=" .. submissionOptions[ "MachineLimit" ] .. "\n" )
    jobInfoFile:write( "LimitGroups=" .. submissionOptions[ "LimitGroups" ] .. "\n" )
    jobInfoFile:write( "OnJobComplete=" .. submissionOptions[ "OnJobComplete" ] .. "\n" )
    
    if submissionOptions[ "Blacklist" ] ~= nil then
        jobInfoFile:write( "Blacklist=" .. submissionOptions[ "Blacklist" ] .. "\n" )
    else
        jobInfoFile:write( "Whitelist=" .. submissionOptions[ "Whitelist" ] .. "\n" )
    end
    
    if submissionOptions[ "JobDependencies" ] == "" then
        jobInfoFile:write( "JobDependencies=" .. table.concat( dependencies, "," ) .. "\n" )
    else
        jobInfoFile:write( "JobDependencies=" .. submissionOptions[ "JobDependencies" ] .. "," .. table.concat( dependencies, "," ) .. "\n" )
    end
    
    if frameDependent then
        jobInfoFile:write( "IsFrameDependent=True\n" )
    end
    
    if submissionOptions[ "InitialStatus" ] ~= nil then
        jobInfoFile:write( "InitialStatus=" .. submissionOptions[ "InitialStatus" ] .. "\n" )
    end
    
    if imagesdir then
        jobInfoFile:write( "OutputDirectory0=" .. imagesdir .. "\n" )
    end
    
    io.close( jobInfoFile )
    
    -- Create the plugin info file.
    local pluginInfoFileName = deadlineTemp .. "/guerilla_plugin_info_" .. uniqueString .. ".txt"
    local pluginInfoFile = io.open( pluginInfoFileName, 'w' )
    
    pluginInfoFile:write( "ScriptFile=" .. jobsdir .. "/" .. script .. "\n" )
    pluginInfoFile:write( "ScriptArgs=" .. args .. "\n" )
    
    io.close( pluginInfoFile )
    
    -- Submit the job and clean up the submission files.
    local results = rundeadlinecommand( deadlinePath, "\"" .. jobInfoFileName .. "\" \"" .. pluginInfoFileName .. "\"" )
    --os.remove( jobInfoFileName )
    --os.remove( pluginInfoFileName )
    
    -- Print the results.
    print( "" )
    print( results )
    
    -- Parse and return the job ID.
    local jobId = nil
    results:gsub( "JobID=([0-9a-zA-Z]+)", function( id ) jobId = id end )
    return jobId
end

function submittodeadline( deadlineRenderFarm, jobs, options, deadlinePath )
    
    local scriptPath = rundeadlinecommand( deadlinePath, "-getrepositoryfilepath scripts/Submission/GuerillaSubmission.py" )

    local frames = rangetonumbers( options.FrameRange )
    local jobsdir = fs.expand( options.JobsDirectory ):gsub( "\\", "/" )
    
    local imagesdir = os.getenv( "IMAGES" )
    if imagesdir then
        imagesdir = expand( imagesdir ):gsub( "\\", "/" )
    end

    -- Run the Monitor submission script to get the submission options. The actual submission is done by this script later.    
    local deadlinePath = deadlineRenderFarm.DeadlinePath:get()
    local submissionOptionsStr = rundeadlinecommand( deadlinePath, "-ExecuteScript \"" .. scriptPath .. "\" \"" .. options.Name .. "\" \"" .. options.FrameRange .. "\" \"" .. jobsdir .. "\""  )
    submissionOptionsStr = submissionOptionsStr:gsub( "\r", "" )

    -- Parse the results from the submission script into a table that we can use later.
    local tempSubmissionOptions = splitstring( submissionOptionsStr, "\n" )
    
    local success = false
    local submissionOptions = {}
    for k, opt in ipairs( tempSubmissionOptions ) do
        -- If the results contain "SUBMISSION OPTIONS", then we should proceed with the submission.
        if opt == "SUBMISSION OPTIONS" then
            success = true
        elseif success then
            -- We only want the text that is printed out after "SUBMISSION OPTIONS"
            local keyValue = splitkeyvalue( opt )
            submissionOptions[ keyValue[1] ] = keyValue[2]
        end
    end
    
    -- If the submisison was canceled, just return.
    if not success then
        print( "Submission cancelled" )
        return false
    end
    
    -- Get temp directory for submission files.
    local deadlineHome = rundeadlinecommand( deadlinePath, "-GetCurrentUserHomeDirectory" )
    deadlineHome = fixpath( deadlineHome )
    local deadlineTemp = deadlineHome .. "/temp"
    
    -- Determine the batch name, if more than one job is being submitted.
    local batchName = ""
    if table.getn( jobs ) > 1 then
        batchName = submissionOptions[ "Name" ]
    end
    submissionOptions[ "BatchName" ] = batchName

    -- Add a propert to all jobs to keep track of their Deadline job ID (for dependencies)
    for id, job in ipairs (jobs) do
		job.DeadlineId = {}
	end
    
    -- Loop through all the jobs and submit them.
    local submittedJobs = 0
    for id, job in ipairs( jobs ) do
    
        -- Only submit enabled jobs.
        if job.Enabled and (job.Array or (job.Type == "pre") or (job.Type == "post")) then
            local	deadlineids = {}
            
            -- Compute dependencies for this job
            local dependencies = {}
            local frameDependent = true
            if table.getn(job.Dependencies) == 0 then
                frameDependent = false
            else
                for k, didx in ipairs (job.Dependencies) do
                    local	dep
                    for i, job in ipairs (jobs) do
                        if job.JobId == didx then
                            dep = job
                            break
                        end
                    end
                    
                    -- This job can only be frame dependent if it and the job it depends on is a frame job.
                    if not job.Array or not dep.Array then
                        frameDependent = false
                    end
                    
                    for f, id in pairs (dep.DeadlineId) do
                        table.insert (dependencies, id)
                    end
                end
            end
            
            -- Submit a job for each image tile if this is a distributed frame.
            for kd = 1, (job.DistributedArg and options.Distributed or 1) do
                local title = ""
                local script = ""
                local args = ""
                local frameList = ""
                
                -- Pre and post jobs are single frame jobs.
                if job.Type == "pre" or job.Type == "post" then
                    frameList = "0"
                    if job.Type == "pre" then
                        script = job:getscriptfile(frames[1])
                        title = job:getscriptname(frames[1])
                    else
                        script = job:getscriptfile(frames[#frames])
                        title = job:getscriptname(frames[#frames])
                    end
                else
                    frameList = options.FrameRange
                    script = job:getscriptfile(frames[1])
                    title = job:getscriptname(frames[1])
                    title = title:gsub( "(fr:[0-9]+)", function( frame ) return "frames" end )
                end
                
                if job.DistributedArg then
                    args = '"' .. job.DistributedArg:gsub( "%$%(distributed%)", kd ) .. '"'
                    title = title .. " (" .. job.DistributedArg:gsub( "%$%(distributed%)", kd ) .. ")"
                end
                
                local deadlineid = submitdeadlinejob( deadlinePath, deadlineTemp, submissionOptions, script, args, frameList, jobsdir, imagesdir, title, dependencies, frameDependent )
                if not deadlineid then
                    messagebox( "Job submission failed. See Console for details.", "Submission Error" )
                    return false
                end
                
                submittedJobs = submittedJobs + 1
                table.insert(deadlineids, deadlineid)                
            end
            
            job.DeadlineId = deadlineids
        end
    end
    
    if submittedJobs > 0 then
        messagebox( "Successfully submitted " .. tostring( submittedJobs ) .. " job(s). See Console for details.", "Submission Successful" )
    end
    
    return true
end
(
    if not IsNetServer() then --only run if 3dsMax is in workstation mode
    (
	    local repoRoot = ""
	    try
		(
			local result = -2
				
			local submitOutputFile = sysInfo.tempdir + "submitOutput.txt"
			local submitExitCodeFile = sysInfo.tempdir + "submitExitCode.txt"
			
			deleteFile submitOutputFile
			deleteFile submitExitCodeFile
					
			
	        local commandArguments = "-outputfiles \"" + submitOutputFile + "\" \"" + submitExitCodeFile + "\" -getrepositorypath submission/3dsmax/Main"
			local deadlineCommandBG =  systemTools.getEnvVariable( "DEADLINE_PATH" ) + "\\deadlinecommandbg.exe"
			ShellLaunch deadlineCommandBG commandArguments
					
			local startTimeStamp = timestamp()
			local ready = false
			while not ready do
			(
				sleep 0.15
				if doesFileExist submitExitCodeFile do
				(
					local theFile = openFile submitExitCodeFile
					try(result = readValue theFile)catch(result = -2)
					try(close theFile)catch()
					ready = true
				)	
				if timestamp() - startTimeStamp > 10000 then 
				(
					result = -3
					ready = true
				)	
			)
			if( result == 0 ) then
			(
				local resultFile = OpenFile submitOutputFile
				local resultMsg = ""
				if (resultFile != undefined) do
				(
					try(resultMsg = readLine resultFile)catch()
					try(close resultFile)catch()
				)
				
				RepoRoot = resultMsg + "\\"
	            fileIn (RepoRoot+"SMTDMenuCreator.ms")
			)
		)catch(throw())
	)
)
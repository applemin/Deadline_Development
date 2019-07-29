macroScript Cmd2Deadline category:"Deadline" buttontext:"Deadline (3dsCmd)" tooltip:"Submit Max To Deadline (3dsCmd)"
(
	--------------------------------------------------------
	-- MAXCmd2Deadline Updater/Launcher
	-- Deadline submission script for 3dsmax
	-- Copyright (c) 2003-2017 Thinkbox Software Inc
	-- All rights reserved.

	local messageTitle = "Deadline (3dsCmd)"
	local goOn = true
	local deadlinePath = systemTools.getEnvVariable( "DEADLINE_PATH" )

	if deadlinePath == undefined do
	(
		messagebox "The system environment variable DEADLINE_PATH is not defined on this computer. Please re-run Deadline client installer or set it manually." title:messageTitle
		goOn = false
	)

	local VersionInfo = dotnetclass "System.Diagnostics.FileVersionInfo"
	local MyMax = VersionInfo.GetVersionInfo (pathConfig.appendPath (pathConfig.GetDir #maxroot) "3dsmax.exe")
	try(
		--format "%\n" ( "3dsMax, API, SDK version: " + (maxversion() as string) )
		--format "%\n" ( "3dsmax.exe version: " + (MyMax.FileVersion as string) )
		if findItem #("14.0.0.121","14.6.0.388","15.0.0.347","15.1.348.0","16.4.265.0") (MyMax.FileVersion as string) > 0 do 
		(
			messagebox ("A version of 3ds Max ("+ (MyMax.FileVersion as string) +") that is known to be incompatible has been detected!\n\nPlease UPDATE 3ds Max to the latest Product Update (PU/SP), then try launching again!") title:messageTitle 
			goOn = false
		)
	)
	catch
	(
		format "--FAILED to Confirm 3dsMax.exe Version.\n"
	)

	if goOn then
	(
		-- call DeadlineCommand to find the network root (assume it is in the path)
		theNetworkRoot = ""
		try
		(
			local result = -2
				
			local submitOutputFile = sysInfo.tempdir + "submitOutput.txt"
			local submitExitCodeFile = sysInfo.tempdir + "submitExitCode.txt"
			
			deleteFile submitOutputFile
			deleteFile submitExitCodeFile
					
			local commandArguments = "-outputfiles \"" + submitOutputFile + "\" \"" + submitExitCodeFile + "\" -getrepositorypath submission/3dsCmd/Main"
			local deadlineCommandBG = deadlinePath + "\\deadlinecommandbg.exe"
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
				
				theNetworkRoot = resultMsg
			)
			else
			(
				if result == -3 then
					messageBox "Timed out getting Repository Root from Deadline Command. (error code: 1003)"
				else
					messageBox "Failed to get Repository Root from Deadline Command. (error code: 1004)"	
			)
		)
		catch
			messageBox "Error calling Deadline Command to get Repository Root. (error code: 1005)"

	    -- if network root was found, try to automatically update submission script.
	    if theNetworkRoot != "" then
	    (
			 try 
			 ( 
			mainScript = theNetworkRoot + "/3dsCmd2Deadline.ms"
			sanityCheckScript = theNetworkRoot + "/3dsCmd2DeadlineSanityCheck.ms"
							
				if doesFileExist mainScript then
				(
					format "MaxCmd2Deadline Script File FOUND in the Deadline Repository...\n"
	                format "MaxCmd2Deadline Script File path: \"%\"\n" mainScript
					fileIn mainScript quiet:true
					format "MaxCmd2Deadline Macro UPDATED.\n"
									
					if doesFileExist sanityCheckScript then
					(
						format "SanityCheck Script File FOUND in the Deadline Repository...\n"
						fileIn sanityCheckScript quiet:true
						format "SanityCheck Functions UPDATED.\n"
					)
				)
				else
					messageBox "Failed To Update MaxCmd2Deadline Script from Deadline Repository. (error code: 1005)"
			) 
			catch
			 	messageBox "Error Accessing Deadline Repository. (error code: 1006)"
		)
		else
			messageBox "Could not get repository root. (error code: 1010)"
		
		macros.run "Thinkbox" "Cmd2DeadlineMain"
	)
)

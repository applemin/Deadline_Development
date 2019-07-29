macroScript SubmitMaxToDeadline category:"Deadline" buttontext:"Deadline" tooltip:"Submit Max To Deadline"
(
	--------------------------------------------------------
	-- Submit MAX To Deadline Updater/Launcher
	-- Deadline submission script for 3dsmax
	-- Copyright (c) 2003-2017 Thinkbox Software Inc
	-- All rights reserved.
	--------------------------------------------------------
	local sttotal = timestamp()													--Get the current system time for reporting the duration of the launch.
	format "Launching Submit Max To Deadline (SMTD)...\n"						--Log a line to the Listener to inform the user the launching started.
	global SMTD_AutoLoadSuccessful												--This variable contains a boolean flag denoting whether the auto-loading via startup script succeeded during 3ds Max launch.
	global SMTD_TilesRendering													--Pre-declaring a global variable holding the Tiles rollout
	global SMTD_RegionRendering													--Pre-declaring a global variable holding the Region Rendering rollout
	global SMTD_StartupDialog_Rollout 											--Pre-declaring a global variable to hold the progress dialog of the SMTD Launcher...
	try(destroyDialog SMTD_StartupDialog_Rollout )catch()						--...and making sure it is closed.
	try(destroyDialog SMTD_MainRollout)catch()									--This is important - we need to close a previously open UI so that it can save settings to the MAX scene before any new settings are initialized!
	local messageTitle = "SMTD"													--This is the title of any popup message dialogs.
	local goOn = true															--This flag will control whether the launch process should continue or not
	local deadlinePath = systemTools.getEnvVariable( "DEADLINE_PATH" )			--Get the DEADLINE_PATH Environment variable to locate the Deadline Binaries
	if deadlinePath == undefined do												--If the Env. variable is not defined, warn the user and stop the loading
	(
		messagebox "The system environment variable DEADLINE_PATH is not defined on this computer. Please re-run Deadline client installer or set it manually." title:messageTitle
		goOn = false
	)
	
	if ::RPMDeadline6DataStruct != undefined do									--If RPM Data is already defined, it means the SMTD rollouts have already been added to RPM. Warn and stop.
	(
		messagebox "SMTD submission scripts have already been loaded by RPM.\n\nTo use SMTD outside of RPM, please\nrestart 3ds Max and open SMTD without launching RPM." title:messageTitle 
		goOn = false
	)
	
	local VersionInfo = dotnetclass "System.Diagnostics.FileVersionInfo"		--Get the FileVersionInfo DotNet class to check the 3ds Max executable for known bad versions...
	local MyMax = VersionInfo.GetVersionInfo (pathConfig.appendPath (pathConfig.GetDir #maxroot) "3dsmax.exe")	--get the 3ds Max version from the binary
	try(
		--format "%\n" ( "3dsMax, API, SDK version: " + (maxversion() as string) )
		--format "%\n" ( "3dsmax.exe version: " + (MyMax.FileVersion as string) )
		if findItem #("14.0.0.121","14.6.0.388","15.0.0.347","15.1.348.0","16.4.265.0") (MyMax.FileVersion as string) > 0 do --If the version is known as bad, warn the user and stop
		(
			messagebox ("A version of 3ds Max ("+ (MyMax.FileVersion as string) +") that is known to be incompatible with SMTD has been detected!\n\nPlease UPDATE 3ds Max to the latest Product Update (PU/SP), then try launching SMTD again!") title:messageTitle 
			goOn = false
		)
	)
	catch																		--Handle any errors in getting the version from the 3dsmax.exe file
	(
		format "--FAILED to Confirm 3dsMax.exe Version.\n"						--Just report the failure to the Listener, but do not stop the loading.
	)
	
	rollout SMTD_StartupDialog_Rollout "Submit Max To Deadline Loading..."		--Dialog rollout to display the loading progress and current operation
	(
		progressbar prg_loading color:green height:20 width:280
		label lbl_progress "Startup..."
		
		fn progressSliderUpdate val =											--This function is similar to the one used in SMTD for the Priority sloder
		(
			local theRed = (255.0 - 255.0*val/100.0)*2.0						--It calculates a red color which is maximum red when the vall argument is between 0.0 and 50.0, then falls off
			if theRed > 255 do theRed = 255										--Clamp it as it can go up to 510 otherwise.
			local theGreen = 512.0*val/100.0									--The green component does the opposite, growing from 0 to 255 while val goes from 0.0 to 50.0, then it is 255 for the second half
			if theGreen > 255 do theGreen = 255									--Clamp it as it can go up to 512 otherwise.
			prg_loading.color = [theRed, theGreen, 0]							--Combine the two components to make a red->yellow->green gradient as value goes from 0.0 to 100.0
			prg_loading.value = val												--Set the progress bar length to the value, too.
		)--end fn		
	)--end rollout
	
	if goOn then																--If nothing bad has happened so far, continue loading
	(
		createDialog SMTD_StartupDialog_Rollout 300 50							--Create a dialog from the rollout
		
		SMTD_StartupDialog_Rollout.progressSliderUpdate 15.0					--Set the progress bar to 15%, reddish color
		SMTD_StartupDialog_Rollout.lbl_progress.text = "Looking for the Submission Directory..."	--Set the progress text to show we are looking for the Submission folder in the Repo.
		local theSubmissionDir = ""												--Initialize the submission directory to empty string
		local st = timestamp()													--Get the system timer again to measure how long it took to call DeadlineCommandBG
		try																		--Catch any errors in the following code block...
		(
			local result = -2													--Default the result to error -2 
				
			local submitOutputFile = sysInfo.tempdir + "submitOutput.txt"		--Get the output here
			local submitExitCodeFile = sysInfo.tempdir + "submitExitCode.txt"	--Use the temporary directory to write the exit code
			
			deleteFile submitOutputFile											--Delete the output file
			deleteFile submitExitCodeFile										--Delete the exit code file
					
			--Build Command Line to query the Repo path
			local commandArguments = "-outputfiles \"" + submitOutputFile + "\" \"" + submitExitCodeFile + "\" -getrepositorypath submission/3dsmax/Main"
			local deadlineCommandBG = deadlinePath + "\\deadlinecommandbg.exe"	--Define the command line application to call
			ShellLaunch deadlineCommandBG commandArguments						--Launch DeadlineCommandBG with the given command line arguments
					
			local startTimeStamp = timestamp()									--Get the system timer to start waiting for the command line call to finish
			local ready = false													--Set a flag to False, will raise to True when the command line call returns
			while not ready do													--Loop while the flag is False...
			(
				sleep 0.1														--Wait for 1/10 of a second before checking again
				if doesFileExist submitExitCodeFile do							--If the exit code file appears, the command line call has finished
				(
					local theFile = openFile submitExitCodeFile					--Open the exit code file to check the result
					try(result = readValue theFile)catch(result = -2)			--Read the first value from the file, assume -2 if the reading failed for any reason
					try(close theFile)catch()									--Try to close the file if the openFile call succeeded
					ready = true												--Raise the flag to exit the loop
				)--end if exit code exists
				if timestamp() - startTimeStamp > 10000 then 					--Check to see if 10 seconds have passed since the call
				(
					result = -3													--If yes, set the result to -3 (timed out)
					ready = true												--and raise the flag to exit the loop
				)--end if timeout
			)--end while not ready loop
			if( result == 0 ) then												--If the exit code was 0, this means the call finished successfully
			(
				local resultFile = OpenFile submitOutputFile
				local resultMsg = ""
				if (resultFile != undefined) do
				(
					try(resultMsg = readLine resultFile)catch()
					try(close resultFile)catch()
				)
				theSubmissionDir = resultMsg
			)
			else																--If the submission failed, let the user know why:
			(
				goOn = false													--set the flag to stop any further loading of files
				local errorMessage = case result of
				(
					(-3): "Timed out getting Repository Path from Deadline Command. (error code: 1003)"  	--If the command line call timed out (-3), prepare a time-out message
					1: (																				--If the result is 1, there might have been an error we can read from the result file
						local theSubmissionInfoArray = try(( dotNetClass "System.IO.File" ).ReadAllLines submitOutputFile)catch(#("Errored out getting Repository Path from Deadline Command. (error code: 1006)"))
						theSubmissionInfoArray[1]
					)						
					default: "Failed to get Repository Path from Deadline Command. (error code: 1004)"	--If something else happened (-2), prepare a more general message.
				)
				format "--%\n" errorMessage										--Show the message in the Listener
				messageBox errorMessage title:messageTitle						--and pop up the message in a dialog
			)
		)
		catch
		(
			goOn = false
			format "--Unable to find Repository root\nThe exception thrown was \"%\"\n" (getCurrentException())
		
			local errorMessage = "Error calling Deadline Command to get Repository Path. (error code: 1005)\n"
			errorMessage += "\n"
			errorMessage += "This may be caused by:\n"
			errorMessage += "- The Deadline Client package not being installed\n"
			errorMessage += "- The DEADLINE_PATH environment variable not being set\n"
			errorMessage += "- DeadlineCommand being unable to run\n"
			errorMessage += "\n"
			errorMessage += "See the listener window for more details\n"
			messageBox errorMessage title:messageTitle
		)
		if goOn do	 															--If everything went ok so far, show how long it took to get the path
			format "Repository Path [%] Resolved in % ms\n" (substituteString theSubmissionDir "/" "\\") (timestamp()-st)
		
		fn getFileInfoDotNet theFileName = 										--Get all necessary information from files to see if they need to be copied
		(
			local fileLookup = dotnetobject "System.IO.DirectoryInfo" (getFileNamePath theFileName)			--Get directory info for the folder of the file
			local allMatchingFiles = try ( fileLookup.getFiles (filenameFromPath theFileName) ) catch(#())	--Get the files matching our file
			if allMatchingFiles.count == 1 then																--Theres should be exactly one file matching
			(
				local dotNetFile = allMatchingFiles[1]														--Get the matching entry into a variable,
				#(dotNetFile.FullName, dotNetFile.lastWriteTime.ToString(), dotNetFile.length)				--and collect the name, modified time, and size
			)
			else #()																						--If not found, return an empty array
		)--end fn
		
		--Define the files that we need to load with the information needed to process them:
		local theFilesToLoad = #(
			--#(1: File Name, 						2: Base Error Code,		3: target folder, 			4: fatal error, 	5:autoload off if missing  	6:load this file  7:force loading even if file was local and same)
			#("RegionManipulator.ms", 								1040, 	#userStartupScripts,		false,				false,						true),
			#("TileManipulator.ms", 								1042,	#userStartupScripts,		false,				false,						true),
			#("SubmitMaxToDeadline_Functions.ms", 					1004, 	#userScripts, 				true,				false,						true,				false), --flag 7 is not used anymore
			#("SubmitMaxToDeadline_SanityCheck_Private.ms", 		1024, 	#userScripts,				false,				true,						true),
			#("SubmitMaxToDeadline_SanityCheck_General.ms", 		1020, 	#userScripts,				false,				true,						true),
			#("SubmitMaxToDeadline_SanityCheck.ms", 				1022, 	#userScripts,				false,				false,						true),
			#("SubmitMaxToDeadline.ms", 							1030, 	#userScripts,				true,				false,						false),
			#("SubmitMaxToDeadline_Defaults.ini", 					1101, 	#userScripts,				false,				false,						false),
			#("SubmitMaxToDeadline_StickySettings.ini", 			1102, 	#userScripts,				false,				false,						false),
			#("SubmitMaxToDeadline_ExcludeFromSceneStorage.ini",	1103, 	#userScripts,				false,				false,						false)
		)
		
		local theLocalLauncherFilename = (GetDir #userStartupScripts + "\\SMTD_Loader.ms")					--This is the startup script's name - this script would pre-load SMTD when 3ds Max boots up.
		local localLauncherExists = doesFileExist theLocalLauncherFilename									--We check once to see if the local launcher script exists to make loading decisions later on.
		--format "SMTD_AutoLoadSuccessful = %\n" ::SMTD_AutoLoadSuccessful									--Optionally print the result of the auto loading script
		
		for i = 1 to theFilesToLoad.count while goOn == true do												--While no script has failed to load, loop through all scripts to load definitions
		(
			--local st = timestamp()																		--Stop the current time
			local theFileDef = theFilesToLoad[i]															--Store the script definition array in a shorter variable for easier access 

			SMTD_StartupDialog_Rollout.progressSliderUpdate (10 + (90.0*i/theFilesToLoad.count))			--Grow the progress bar with each processed file
			SMTD_StartupDialog_Rollout.lbl_progress.text = "Loading File [" + theFilesToLoad[i][1] + "]"	--And show the name of the file being processed
			try(windows.processPostedMessages())catch() 													--This function is available only in 3dsMax 2011 and higher, it forces the UI to update and avoid "white windows"
			try( 																							--Run inside an error trap
				local theScript = theSubmissionDir + "\\" + theFileDef[1]									--This is the path to the Repository copy of the script
				local theTarget = (GetDir theFileDef[3] + "\\" + theFileDef[1])								--This is the path to the local copy of the same script
				if doesFileExist theScript then																--If the source script exists in the Repository,
				(
					local theInfo1 = getFileInfoDotNet theScript											--Collect its file info
					local theInfo2 = if doesFileExist theTarget then getFileInfoDotNet theTarget else #("","","")	--Get info on the target if it exists, otherwise assume defaults
					local loadResult = undefined															--Initialize the result to undefined
					if theInfo1[2] != theInfo2[2] or theInfo1[3] != theInfo2[3] then 						--if the last modified time or the file sizes are different, copy the file over
					(
						deleteFile theTarget																--Delete the target script if it exists to allow the copying 
						copyFile theScript theTarget														--Copy the source script to the local target path to speed up evaluation
						
						if theFileDef[6] == true do loadResult = fileIn theTarget quiet:true				--If the file is one we are supposed to load, then evaluate it and get the result
						if theFileDef[5] == true do SMTD_AutoLoadSuccessful = false  						--If this file is one that requeries the remaining files to be reloaded, lower the auto-load flag 
					)
					else																					--If the two files are identical
					(
						if theFileDef[7] == true then 														--If set to force evaluation, 
							loadResult = fileIn theTarget quiet:true 										--evaluate the local file
						else if not localLauncherExists or SMTD_AutoLoadSuccessful != true do 				--If the local launcher script does not exist or autoloading locally failed
							if theFileDef[6] == true do loadResult = fileIn theTarget quiet:true 			--a file that requires the remaining files to load has been reloaded so this file needs to be reloaded, too
					)
					if loadResult == false do (goOn = false)												--if a fileIn() resulted in False (currently only the SMTD Functions script returns True or False), stop loading
				)	
				else																						--If the source script does not exist, warn the user
				(
					local errorMessage = ("Failed To Find the file ["+theFileDef[1]+"] in the Deadline Repository. (error code: "+ theFileDef[2] as string  +")")
					format "--%\n" errorMessage
					messageBox errorMessage title:messageTitle
					if theFileDef[4] == true do goOn = false 												--Failed to find a file, so stop if the file is required
				)
			)
			catch																							--If any error was trapped in the above code block,
			(
				local errorMessage = ("Failed To Load the file ["+theFileDef[1]+"] from the Deadline Repository. (error code: "+(theFileDef[2]+1) as string+")")	--define the error message,
				format "--%\n" errorMessage																	--Print the message to the Listener
				format "--The exception thrown was \"%\"\n" (getCurrentException())							--Show the error for debugging purposes
				messageBox errorMessage title:messageTitle													--and display in the pop up
				if theFileDef[4] == true do goOn = false													--If the file is required, stop the loading
			)
			--format "\t%: % ms\n" theFileDef[1] (timestamp()-st) 											--Un-Remark to print the total time it has taken since the start to load this file
		)
		
		local theLocalLauncher = "" as StringStream 														--create a file that will try to load the files when max is opened next time to find out if everything needs to be reloaded or if they can just do the comparison.
		format "global SMTD_AutoLoadSuccessful = true\n" to:theLocalLauncher								--Set the auto-load global variable to True when the script is run on 3dsMax startup
		for i in theFilesToLoad where i[3] != #userStartupScripts and i[6] == true do						--Find all files that need to be loaded, but do not live in the startup scripts folder,
			format "try(fileIn (getDir % + \"/%\") quiet:true )catch(::SMTD_AutoLoadSuccessful = false)\n" i[3] i[1] to:theLocalLauncher	--add them to the stringStream for saving to the file
		(dotNetClass "System.IO.File").WriteAllText theLocalLauncherFilename (theLocalLauncher as string) 	--Use dotNet file IO to speed up the file saving
		
		SMTD_StartupDialog_Rollout.progressSliderUpdate 100.0												--Set the progress bar to maximum and green color
		SMTD_StartupDialog_Rollout.lbl_progress.text = "Launching Submit Max To Deadline..."				--Tell the user SMTD is being launched
		try(destroyDialog SMTD_StartupDialog_Rollout )catch()												--Close the startup dialog
		
		if goOn then																						--If nothing bad has happened thus far, we can launch the SMTD UI
		(
			::SMTD_AutoLoadSuccessful = true																--Raise the flag that everything loaded successfully
			::SMTDFunctions.InitializeSubmitInfo()															--Load all submission info like Pools, Groups, and various Directories from the cache we created earlier in this script
			fileIn (getDir #userScripts+ "\\SubmitMaxToDeadline.ms") 										--Evaluate the SMTD UI script
			format "Total SMTD Launcher Time: %ms\n" (timestamp()-sttotal)									--Report the total time it took to process and load all scripts
		)
		else format "--SMTD Loading Failed!\n"																--If something went wrong, let the user know.
	)--end if goOn
)--end script
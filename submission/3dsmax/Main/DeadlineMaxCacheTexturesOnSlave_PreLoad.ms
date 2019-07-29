(
	local theBitmapsToCopy  = #()
	local theBitmapsToProcess = #()
	local theCacheDirectory = (dotnetclass "System.Environment").GetFolderPath (dotnetclass "System.Environment+SpecialFolder").CommonApplicationData + "\\PF_LocalVFXCache\\LocalTexturesCache\\" --@"C:\Documents and Settings\All Users\Application Data\PF_LocalVFXCache\LocalTexturesCache\" --
	
	local du = DeadlineUtil  --this is the interface exposed by the Lightning Plug-in which provides communication between Deadline and 3ds Max
	if du == undefined do  --if the script is not being run on Deadline (for testing purposes),
	(
		struct DeadlineUtilStruct   --define a stand-in struct with the same methods as the Lightning plug-in
		(
			fn SetTitle title = ( format "Title: %\n" title ),
			fn SetProgress percent = (true),
			fn FailRender msg = ( throw msg ),
			fn GetJobInfoEntry key = ( undefined ),
			fn GetAuxFilename index = ( undefined ),
			fn LogMessage msg = ( format "%\n" msg ),
			CurrentFrame = ((sliderTime as string) as integer)
		)
		du = DeadlineUtilStruct() --create an instance of the stand-in struct
	)--end if
	
	fn convertPathToLocal TextureCacheFolder thePath =
	(
		if matchPattern thePath pattern:(TextureCacheFolder+"*") then
		(
			thePath 
		)
		else
		(
			local newName = copy thePath
			if pathConfig.isUncPath thePath then
			(
				newName[1] = "_"
				newName[2] = "_"
			)
			else
				newName = substituteString newName ":" "_"
			TextureCacheFolder + newName
		)
	)	
	
	fn getFileInfoDotNet theFileName =
	(
		local fileLookup = dotnetobject "System.IO.DirectoryInfo" (getFileNamePath theFileName)
		local allMatchingFiles = #()
		try (
			allMatchingFiles = fileLookup.getFiles (filenamefrompath theFileName) 
		) catch()
		if allMatchingFiles.count == 1 then
		(
			local dotNetFile = allMatchingFiles[1]
			local fname = dotNetFile.FullName
			local date_ = dotNetFile.lastWriteTime.ToString()
			local size_ = dotNetFile.length
			#(fname, date_, size_)
		)
		else
			#("???","???","???")
	)	
	
	fn convertUniversalTimeToSeconds theTime = 
	(
		--(Year times days times hours plus 6 hours + month's number of days times hours                                         / days times hours / hours ) the whole multiplied by seconds, plus minutes times 60 plus seconds
		(((theTime[1]*365L)*24+6)+(#(31,28,31,30,31,30,31,31,30,31,30,31)[theTime[2]])*24 + theTime[4]*24 + theTime[5])*3600L+ theTime[6]*60L + theTime[7]
	)
	
	fn getFreeSpaceOnC =
	(
		sysinfo.currentdir = getDir #temp
		dosCommand "dir c: >_temp.txt"
		local theFileHandle = openFile "_temp.txt"
		while not eof theFileHandle do theLine = readLine theFileHandle
		close theFileHandle
		deleteFile "_temp.txt"
		local theFS = filterString theLine " "
		local theIndex = findItem theFS "bytes"
		local theValue = theFS[theIndex-1]
		theValue = substituteString theValue "," ""
		theValue+="L"
		execute theValue
	)	
	
	local theFoldersToProcess = #()
	local theFilesToDelete = #()
	local theFilesToDeleteData = #()
	local theIndexArray = #()
	
	fn getFolderRecursive theRoot =
	(
		append theFoldersToProcess theRoot
		theSubDirs = getDirectories (theRoot + "*")
		for d in theSubDirs do getFolderRecursive d
	)
	
	fn compareFN v1 v2 valArray: =
	(
		local v1i = valArray[v1][1]
		local v2i = valArray[v2][1]
		if v1i > v2i then 1 else -1
	)

	
	fn collectCandidatesForDeleting =
	(
		getFolderRecursive theCacheDirectory
		local theTabuNames = for f in theBitmapsToProcess collect fileNameFromPath f --these are the names of the bitmaps used in the current job. We may not delete them
		for d in theFoldersToProcess do --for every folder,
		(
			theFiles = getFiles (d+"*.*") --collect all files, then filter the INI files and those on the tabu list.
			theFiles = for f in theFiles where not (matchPattern (getFileNameType f) pattern:".ini") collect f
			theFiles = for f in theFiles where findItem theTabuNames (fileNameFromPath f) == 0 collect f
			join theFilesToDelete theFiles
		)
		
		theFilesToDeleteData = for f in theFilesToDelete collect 
		(
			theVal1 = (getIniSetting (f+".ini") "Usage" "Counter")
			if theVal1 == "" then 
				theVal1 = 1
			else 
				theVal1 = execute theVal1
			theVal2 = (getIniSetting (f+".ini") "LastUsed" "Date")
			if theVal2 == "" then
				theVal2 = getUniversalTime()
			else
				theVal2 = execute theVal2
			local ageInSeconds = (convertUniversalTimeToSeconds (getUniversalTime())) - (convertUniversalTimeToSeconds theVal2)
			local theSize = (getFileInfoDotNet f)[3]
			#(ageInSeconds, theVal1, theSize)
		)
	)
	
	
	--TODO: Clean up texture cache
	fn performCleanup theFreeSpace totalSizeToCopy =
	(
		--*Collect all textures currently on disk and not used by the current scene.
		--*Also collect usage data (if available)
		
		collectCandidatesForDeleting()
		
		--*Collect the top textures from the list until the sum of their sizes exceeds the required space to free up
		
		local theTotalSizeToDelete = 0L --reset to 0
		for i in theFilesToDeleteData do theTotalSizeToDelete += i[3] --find out how many bytes would be freed up if we would delete all collected maps
			
		if theTotalSizeToDelete > totalSizeToCopy then --if cleaning up all collected map would provide enough space for the incoming bitmaps,
		(
			--*Sort the texture list based on last usage data (and usage counter)
			--*The variable theFilesToDelete now contains the files that could be deleted, with the top of the list being the oldest files
			--*The variable theFilesToDeleteData also contains the data (age, usage count and size)
			
			theIndexArray = for i = 1 to theFilesToDelete.count collect i
			qsort theIndexArray compareFN valArray:theFilesToDeleteData
			theFilesToDelete = for i in theIndexArray collect theFilesToDelete[i]
			theFilesToDeleteData = for i in theIndexArray collect theFilesToDeleteData[i]			
			
			theTotalSizeToDelete = 0L --reset as counter of how much was deleted
			local cnt = 0 --init. a counter
			while theTotalSizeToDelete < totalSizeToCopy do --repeat until enough disk space has been freed up for all incoming bitmaps
			(
				cnt+=1 --increment the counter
				deleteFile theFilesToDelete[cnt] --delete the next bitmap
				theTotalSizeToDelete+= theFilesToDeleteData[cnt][3] --and increase the deleted disk space value
			)
			--at this point, there should be enough disk space to copy the incoming bitmaps.
			true
		)
		else false --*If the sum of the texture sizes to be deleted does not satisfy the requirements of the job, return false.
	)
	
	du.SetTitle "Texture Caching" --set the job title 
	du.LogMessage "Starting Texture Caching..." --output a message to the log
	local st = timestamp() --get the current system time
	local theFile = getFileNamePath (getSourceFileName()) + "\\ExternalFilesList.txt"
	du.LogMessage ("ExternalFilesList.txt Exists: " + (doesFileExist theFile) as string)
	
	local theFileHandle = openFile theFile
	local totalSizeToCopy = 0L
	while not eof theFileHandle do append theBitmapsToProcess (readLine theFileHandle)
	close theFileHandle
		
	du.LogMessage (">Cache Directory: [" + theCacheDirectory  + "]")
	if makeDir theCacheDirectory all:true then
		du.LogMessage ("+Cache Directory Created.")
	else
		du.LogMessage (">Cache Directory Exists.")
	
	for f in theBitmapsToProcess do
	(
		if doesFileExist f then
		(
			local theTargetFile = convertPathToLocal theCacheDirectory f
			du.LogMessage (">Local Path: ["+theTargetFile+"]")
			makeDir (getFileNamePath theTargetFile) all:true
			local originalData = getFileInfoDotNet f
			du.LogMessage (">Source File Info: "+originalData as string)
			local localData = getFileInfoDotNet theTargetFile 
			du.LogMessage (">Target File Info: "+localData as string)
			
			local theTargetINIFile = theTargetFile+".ini"
			local theVal = execute (getIniSetting theTargetINIFile "Usage" "Counter")
			if theVal == OK do theVal = 0
			theVal+=1
			setIniSetting theTargetINIFile "Usage" "Counter" (theVal as string)
			local theTimeString = (getUniversalTime() as string)
			setIniSetting theTargetINIFile "LastUsed" "Date" theTimeString
			--setIniSetting theTargetINIFile "UsageHistory" theTimeString ""
			
			if not doesFileExist theTargetFile or originalData[2] != localData[2] or originalData[3] != localData[3]  then
			(
				totalSizeToCopy+=originalData[3]
				append theBitmapsToCopy #(f,theTargetFile)
				deleteFile theTargetFile
			)
			else
				du.LogMessage ("--File [" +theTargetFile+"] already exists with same size and modified date.")			
		)
		else 
			du.LogMessage ("--File [" +f+"] is missing on the network!!!")		
	)--end f loop
	--At this point we have a list of the bitmaps to copy and the total size in bytes of all textures to copy
	du.LogMessage (">[" +theBitmapsToCopy.count as string +"] files collected for copying...")	
	
	--Now we can get the free space on C: and see if we have to perform any cleanup:
	local theFreeSpace = getFreeSpaceOnC()
	du.LogMessage (">Disk C: Free Space is [" +theFreeSpace as string +"] bytes.")	
	du.LogMessage (">Disk Space Required for the collected textures is [" +totalSizeToCopy as string +"] bytes.")	
	
	local result = true
	--FIXME: Disabled cleanup for now, should be tested first.
	/*
	if theFreeSpace-totalSizeToCopy < 2000000000L do  --if copying the textures would result in less than 2GB, clean up some older textures
		result = performCleanup theFreeSpace totalSizeToCopy
	*/
	
	--Now if we have enough space, we can perform the copying of the ones that need to be copied
	if result then
	(
		for f in theBitmapsToCopy do
		(	
			local result = copyFile f[1] f[2]
			if result then 
				du.LogMessage ("+Copied File From ["+f[1]+"] to [" +f[2]+"]")
			else
				du.LogMessage ("--Failed to Copy File ["+f[1]+"] to [" +f[2]+"]")
		)--end f loop
	)
	
	du.LogMessage ("Finished Texture Caching in "+ ((timestamp() - st)/1000.0) as string + " sec.") --output the job duration
	true  --return true if the task has finished successfully, return false to fail the task.
)--end script

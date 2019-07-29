-- Pre Load Path Mapping (only runs on Deadline)
-- Copyright © 2005-2018 by Thinkbox Software Inc.
-- All rights reserved.
(
	--Interface exposed by the Lightning plugin which provides communication between Deadline and 3ds Max.
	local du = DeadlineUtil
	local MaxFileAssets = #() --collect any .MAX file XRefs in this array
	
	fn getMAXSceneFile =
	(
		local theMAXScene = ""
		local count = 0
		local theAux = ""
		
		do
		(
			theAux = du.GetAuxFilename count
			
			if theAux != undefined do
			(
				if matchPattern theAux pattern:"*.max" do
				(
					theMAXScene = theAux
					theAux = undefined
				)
			)
			
			count += 1
		)
		while theAux != undefined
		
		if theMAXScene == "" do 
		(
			--If the aux. file is not a .max file, look for the SceneFile in the Job Info.
			theMAXScene = du.GetJobInfoEntry "SceneFile"
			du.LogMessage ( ">No .max file found as an auxiliary data file, looking for referenced [SceneFile] in Job Info: [" + theMAXScene + "]." )
		)
		
		theMAXScene
	)

	fn createTempMAXSceneFile theMAXScene forceCopy:false =
	(
		local tempFilePath = ""
		local sysPath = dotNetClass "System.IO.Path"
		local sysDir = dotNetClass "System.IO.Directory"

		if du.GetJobInfoEntry "SceneFile" != undefined or forceCopy == true then
		(
			--Create a copy of the scene file if one has not already been made (by submitting the scene file).
			tempFilePath = sysPath.Combine du.PluginsFolder ( "tempMaxScene" + ( du.CurrentTask as string ) )

			if not sysDir.Exists tempFilePath then
			(
				makeDir tempFilePath
			)
		)

		if tempFilePath != "" then
		(
			local fileName = filenameFromPath theMAXScene
			tempFilePath = sysPath.Combine tempFilePath fileName
			du.LogMessage ( "A temporary copy of the .MAX file has been created for path mapping." )
			copyFile theMAXScene tempFilePath
		)
		else
		(
			tempFilePath = theMAXScene
		)

		tempFilePath
	)
	
	fn getMAXFileAssets theMAXScene isMain:true = 
	(
		local changesMade = False
		local tempFilePath = ""

		if theMAXScene != undefined and doesFileExist theMAXScene then
		(
			if isMain == true then
				tempFilePath = createTempMAXSceneFile theMAXScene
			else
				tempFilePath = theMAXScene --if an XRef, we are already working with a copy of the file
			du.LogMessage ( ">Remapping all asset paths of file ["+tempFilePath+"]" )
			local fileAssets = getMAXFileAssetMetadata theMAXScene
			if fileAssets != undefined then --the above function might return undefined instead of an array if the MAX scene file is corrupted!
			(
				for i = 1 to fileAssets.count do
				(
					local theSource = fileAssets[i].filename
					local theTarget = du.GetPathMappedFilename( theSource )

					if theSource != theTarget then
					(
						changesMade = True
						--du.LogMessage ( "  +Source Path: " + theSource )
						--du.LogMessage ( "  +Mapped Path: " + theTarget )
						--du.LogMessage ( "---------------------------------------------------------------------------" )
					)

					fileAssets[i].filename = theTarget
					if matchPattern (getFileNameType theTarget) pattern:".max" do --if the asset is a MAX scene file, collect it for remapping
					(
						local tempAssetFilePath = createTempMAXSceneFile theTarget forceCopy:true --create a copy of the XRef file for remapping
						fileAssets[i].filename = tempAssetFilePath --update the master scene's asset to the copy filename
						append MaxFileAssets tempAssetFilePath --collect the copy for asset remapping
					)
				)

				if changesMade then
				(
					setMAXFileAssetMetadata tempFilePath fileAssets
				)
				else
				(
					du.LogMessage ( ">No asset paths needed to be remapped." )
					tempFilePath = ""
				)
			)
			else
			(
				du.WarnMessage ( "--FAILED to access the Asset Metadata of "+ theMAXScene )
				tempFilePath = ""
			)
		)
		else
		(
			du.WarnMessage ( "--No .max scene file submitted with this job, so could not modify the asset paths." )
			du.WarnMessage ( "--Please make sure the .max scene file is submitted with the job as an auxiliary file." )
		)

		return tempFilePath
	)
	
	du.LogMessage ( "===========================================================================" )
	du.LogMessage ( ">Modifying asset paths of Main Scene File..." )
	du.LogMessage ( "===========================================================================" )
	local newMaxFilePath = getMAXFileAssets ( getMAXSceneFile() )
	du.LogMessage ( ">Finished modifying asset paths of Main Scene File." )
	while MaxFileAssets.count > 0 do --if any XRef MAX scenes were collected from assets, take the first one...
	(
		du.LogMessage ( ">Checking asset paths of XRef Scene File ["+MaxFileAssets[1]+"]" )
		getMAXFileAssets ( MaxFileAssets[1] ) --remap its assets, while collecting its possible .MAX file XRefs into the same array
		deleteItem MaxFileAssets 1 --and delete the first entry from the array
	)--this will loop until no MAX files are left to remap
	du.LogMessage ( "===========================================================================" )

	newMaxFilePath
)

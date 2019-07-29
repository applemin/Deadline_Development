(
	driveToUncMappings = #()
	currItemArray = #()
	
	try(destroyDialog SMTD_ResourceCheckRollout)catch()
	rollout SMTD_ResourceCheckRollout "Remote Resource Checking Utility"
	(
		label lbl_local "Local Repository:" align:#left
		label lbl_remote "Remote Repository:" align:#left
		--label lbl_size "Data Size To Copy Over: 0 KB" pos:[620,48] align:#left
		label lbl_size "Data Size To Copy Over: 0 MB" pos:[620,48] align:#left
		
		button btn_scanLocal "Display Scene Resources" pos:[8,40]
		button btn_scanRemote "Scan For Remote Discrepencies" pos:[160,40]
		
		checkbox chk_filterExisting "Show Existing Resources" checked:true pos:[360,4]
		checkbox chk_filterSizeDiff "Show Resources With Size Differences" checked:true pos:[360,24]
		checkbox chk_filterMissing "Show Missing Resources" checked:true pos:[360,44]
		
		button btn_copyMissing "Copy Over Missing Files" pos:[492,324]
		button btn_filmoutMissing "Create Filmout For Missing Files" pos:[630,324]
		checkbox chk_includeSizeDiff "Overwrite Files With Size Differences And Backup Originals" checked:true pos:[492,350]
		
		dotNetControl lv_resources "System.Windows.Forms.ListView" height:250 width:840 pos:[5,65] align:#lef
		edittext txt_status "Status:                                                                                                       " fieldwidth:400 pos:[5,330] LabelOnTop:True ReadOnly:True
		progressbar prg_mainProgress color:blue pos:[5,375]
		
		on SMTD_ResourceCheckRollout open do
		(
			lbl_local.text = "Local Repository: " + SMTDFunctions.GetNetworkRoot()
			btn_copyMissing.enabled = false
			btn_filmoutMissing.enabled = false
			chk_includeSizeDiff.enabled = false
			
			if SMTDSettings.CurrentRepository2 == "" then
			(
				btn_scanRemote.enabled = false
				lbl_remote.text = "Remote Repository: Not Selected"
			)
			else
			(
				lbl_remote.text = "Remote Repository: " + SMTDSettings.CurrentRepository2
				
				iniFile = "V:\\deadline_synch\\RemoteResourcePaths.ini"
				if doesFileExist iniFile then
				(
					local tempArray = #()
					SMTDFunctions.ReadFileIntoArray iniFile tempArray
					
					for i in tempArray do
					(
						local parts = filterString i ","
						
						local machineName = tolower parts[1]
						if (findString SMTDSettings.CurrentRepository2 machineName) != undefined then
						(
							for i = 2 to parts.count by 2 do
							(
								local driveToUncMapping = #()
								append driveToUncMapping parts[i]
								append driveToUncMapping parts[i+1]
								append driveToUncMappings driveToUncMapping
							)
						)
					)
				)
			)
			
			lv_resources.gridLines = true  
			lv_resources.View = (dotNetClass "System.Windows.Forms.View").Details
			lv_resources.CheckBoxes = true
			lv_resources.LabelEdit = false
			lv_resources.Enabled = true
			lv_resources.MultiSelect = true
			lv_resources.FullRowSelect = true
			lv_resources.BackColor = lv_resources.BackColor.FromArgb 225 215 219
			lv_resources.Scrollable = true
			lv_resources.HeaderStyle = (dotNetClass "System.Windows.Forms.ColumnHeaderStyle").Nonclickable
			lv_resources.Sorting = (dotNetClass "System.Windows.Forms.SortOrder").Ascending;
			
			local header = dotNetObject "System.Windows.Forms.ColumnHeader"
			header.Text = "File"
			header.Width = 620
			lv_resources.Columns.Add( header ) 
			
			local header = dotNetObject "System.Windows.Forms.ColumnHeader"
			header.Text = "State"
			header.Width = 100
			lv_resources.Columns.Add( header ) 
			
			local header = dotNetObject "System.Windows.Forms.ColumnHeader"
			header.Text = "File Size"
			header.Width = 100
			lv_resources.Columns.Add( header ) 
			
			lv_resources.Refresh()
		)
		
		on btn_scanLocal pressed do
		(
			btn_copyMissing.enabled = false
			btn_filmoutMissing.enabled = false
			chk_includeSizeDiff.enabled = false
			
			SMTD_ResourceCheckRollout.UpdateStatus ("Gathering local scene resources")
			
			prg_mainProgress.value = 0
			
			local lineItems = #()
			
			/*
			append lineItems #(SMTD_ResourceCheckRollout.GetFullMaxFilePath(),"Exists")
			
			local resources = SMTD_ResourceCheckRollout.GetMissingSceneResources()
			for resource in resources do
				append lineItems #(resource,"Missing")
			
			prg_mainProgress.value = 25
			
			resources = SMTD_ResourceCheckRollout.GetExistingSceneResources()
			for resource in resources do
				append lineItems #(resource,"Exists")
			
			prg_mainProgress.value = 50
			
			resources = SMTD_ResourceCheckRollout.GetMissingClothMeshResources()
			for resource in resources do
				append lineItems #(resource,"Missing")
				
			prg_mainProgress.value = 75
			
			resources = SMTD_ResourceCheckRollout.GetExistingClothMeshResources()
			for resource in resources do
				append lineItems #(resource,"Exists")
			*/
			
			local resources = SMTD_ResourceCheckRollout.GetMissingAssetSceneResources()
			for resource in resources do
				append lineItems #(resource,"Missing")
			
			prg_mainProgress.value = 25
			
			resources = SMTD_ResourceCheckRollout.GetExistingAssetSceneResources()
			for resource in resources do
				append lineItems #(resource,"Exists")
			
			prg_mainProgress.value = 50
			
			resources = SMTD_ResourceCheckRollout.GetMissingSyClothResources()
			for resource in resources do
				append lineItems #(resource,"Missing")
				
			prg_mainProgress.value = 75
			
			resources = SMTD_ResourceCheckRollout.GetExistingSyClothResources()
			for resource in resources do
				append lineItems #(resource,"Exists")
			
			--lbl_size.text = "Data Size To Copy Over: 0 KB"
			lbl_size.text = "Data Size To Copy Over: 0 MB"
			
			SMTD_ResourceCheckRollout.PopulateListView lineItems
			SMTD_ResourceCheckRollout.UpdateStatus ("Collected " + (lineItems.count as string) + " local resources")
			
			prg_mainProgress.value = 100
			
			txt_status.caption = "Viewing: Local Resources"
		)
		
		on btn_scanRemote pressed do
		(
			local lineItems = #()
			
			local localResources = #()
			local remoteResources = #()
			
			SMTD_ResourceCheckRollout.UpdateStatus ("Gathering remote scene resources")
			
			local resources = SMTD_ResourceCheckRollout.GetSceneResources()
			for resource in resources do
			(
				local remotePath = SMTD_ResourceCheckRollout.ConvertPath resource #driveToUnc
				if remotePath != "" then
				(
					append localResources resource
					append remoteResources remotePath
				)
			)
			
			local localFileData = SMTD_ResourceCheckRollout.CollectFileData localResources
			local remoteFileData = SMTD_ResourceCheckRollout.CollectFileData remoteResources
			
			local totalFileSizes = 0
			for i = 1 to localFileData.count do
			(
				local state = "Exists"
				local localFileSize = -1
				
				if remoteFileData[i][3] == "missing" then
				(
					-- If local file is missing, we only care that the remote file is actually there.
					if localFileData[i][3] != "missing" then
					(
						state = "Missing"
						localFileSize = SMTD_ResourceCheckRollout.BytesToKB( localFileData[i][2] as integer )
						totalFileSizes = totalFileSizes + localFileSize
					)
					else
						state = "Missing In Both"
				)
				else
				(
					-- If local file is missing, we only care that the remote file is actually there.
					if localFileData[i][3] != "missing" then
					(
						localFileSize = SMTD_ResourceCheckRollout.BytesToKB( localFileData[i][2] as integer )
						if (remoteFileData[i][2] as integer) != (localFileData[i][2] as integer) then
						(
							state = "File Sizes Differ"
							totalFileSizes = totalFileSizes + localFileSize
						)
						--else if remoteFileData[i][3] != localFileData[i][3] then
						--	state = "Mod Times Differ"
					)
				)
				
				local results = #()
				append results remoteFileData[i][1]
				append results state
				append results localFileData[i][1]
				append results localFileSize
				append results true
				append lineItems results
			)
			
			local totalFileSizesMB = totalFileSizes / 1000
			--lbl_size.text = "Data Size To Copy Over: " + (totalFileSizes as string) + " KB"
			lbl_size.text = "Data Size To Copy Over: " + (totalFileSizes as string) + " MB"
			
			btn_copyMissing.enabled = true
			btn_filmoutMissing.enabled = true
			chk_includeSizeDiff.enabled = true
			
			SMTD_ResourceCheckRollout.PopulateListView lineItems
			SMTD_ResourceCheckRollout.UpdateStatus ("Collected " + (lineItems.count as string) + " remote resources")
			
			txt_status.caption = "Viewing: Remote Resources"
		)
		
		on chk_filterExisting changed state do
		(
			SMTD_ResourceCheckRollout.PopulateListView undefined
		)
		
		on chk_filterMissing changed state do
		(
			SMTD_ResourceCheckRollout.PopulateListView undefined
		)
		
		on chk_filterSizeDiff changed state do
		(
			SMTD_ResourceCheckRollout.PopulateListView undefined
		)
		
		on btn_copyMissing pressed do
		(
			local missingFiles = #()
			local sizeDiffFiles = #()
			
			SMTD_ResourceCheckRollout.UpdateStatus ("Copying files...")
			
			for item in currItemArray do
			(
				if item.count > 4 and (item[5] as booleanClass) then
				(
					if item[2] == "Missing" then
					(
						local missingFile = #()
						append missingFile item[3]
						append missingFile item[1]
						append missingFiles missingFile
					)
					else if chk_includeSizeDiff.state and item[2] == "File Sizes Differ" then
					(
						local sizeDiffFile = #()
						append sizeDiffFile item[3]
						append sizeDiffFile item[1]
						append sizeDiffFiles sizeDiffFile
					)
				)
			)
			
			local message = ""
			if missingFiles.count > 0 and sizeDiffFiles.count > 0 then
				message = "You are about to copy over " + (missingFiles.count as string) + " missing files and copy over/backup " + (sizeDiffFiles.count as string) + " files with different sizes. This may take a while. Do you wish to continue?"
			else if missingFiles.count > 0 then
				message = "You are about to copy over " + (missingFiles.count as string) + " missing files. This may take a while. Do you wish to continue?"
			else if sizeDiffFiles.count > 0 then
				message = "You are about to copy over/backup " + (sizeDiffFiles.count as string) + " files with different sizes. This may take a while. Do you wish to continue?"
			
			if message == "" then
				messagebox "There are no files that need to be copied over." title:"Copy Over Missing Files"
			else if (querybox message title:"Copy Over Missing Files") then
			(
				local count = 1
				local totalCount = missingFiles.count + sizeDiffFiles.count
				
				prg_mainProgress.value = 0
				for missingFile in missingFiles do
				(
					local localFilename = missingFile[1]
					local remoteFilename = missingFile[2]
					
					if (copyFile localFilename remoteFilename) then
						SMTD_ResourceCheckRollout.UpdateStatus ("Copied " + localFilename + " to " + remoteFilename + " successfully.")
					else
					(
						format "\r\nFailed copy operation so trying to make directory....\r\n"
						local tmpDosCommand = ("md " + "\"" + (getFilenamePath remoteFilename) + "\"")
						if (HiddenDOSCommand tmpDosCommand startpath:"C:\\") == 0 then 
						(
							if (copyFile localFilename remoteFilename) then
								SMTD_ResourceCheckRollout.UpdateStatus ("Copied " + localFilename + " to " + remoteFilename + " successfully.")
							else
								SMTD_ResourceCheckRollout.UpdateStatus ("FAILED TO COPY " + localFilename + " TO " + remoteFilename)
						)
						else
							SMTD_ResourceCheckRollout.UpdateStatus ("FAILED TO CREATE DIRECTORY FOR " + remoteFilename)
					)
					
					prg_mainProgress.value = 100*count/totalCount
					count = count + 1
				)
				
				for sizeDiffFile in sizeDiffFiles do
				(
					local localFilename = sizeDiffFile[1]
					local remoteFilename = sizeDiffFile[2]
					
					local backupCount = 1
					local backupRemoteFilename = remoteFilename + ".backup_1"
					while (doesFileExist backupRemoteFilename) do
					(
						backupCount = backupCount + 1
						backupRemoteFilename = remoteFilename + ".backup_" + (backupCount as string)
					)
					
					if (renameFile remoteFilename backupRemoteFilename) then
					(
						SMTD_ResourceCheckRollout.UpdateStatus ("Backed up " + remoteFilename + " to " + backupRemoteFilename + " successfully.")
						if (copyFile localFilename remoteFilename) then
							SMTD_ResourceCheckRollout.UpdateStatus ("Copied " + localFilename + " to " + remoteFilename + " successfully.")
						else
							SMTD_ResourceCheckRollout.UpdateStatus ("FAILED TO COPY " + localFilename + " TO " + remoteFilename)
					)
					else
						SMTD_ResourceCheckRollout.UpdateStatus ("FAILED TO BACKUP " + remoteFilename)
					
					prg_mainProgress.value = 100*count/totalCount
					count = count + 1
				)
				
				SMTD_ResourceCheckRollout.UpdateStatus ("Finished copying files")
			)
		)
		
		on btn_filmoutMissing pressed do
		(
			local filmoutExecutable = "C:\\Program Files (x86)\\Frantic Films\\AssetTransferAgent\\AssetTransferAgent.exe"
			if not doesFileExist filmoutExecutable then
				filmoutExecutable = "C:\\Program Files\\Frantic Films\\AssetTransferAgent\\AssetTransferAgent.exe"
			if not doesFileExist filmoutExecutable then
				messageBox "The AssetTransferAgent.exe application could not be found. Talk to IT about getting it installed on your machine" title:"Create Filmout For Missing Files"
			else
			(
				local filmoutFiles = #()
				
				for item in currItemArray do
				(
					if item.count > 4 and (item[5] as booleanClass) then
					(
						if item[2] == "Missing" then
							append filmoutFiles item[3]
						else if chk_includeSizeDiff.state and item[2] == "File Sizes Differ" then
							append filmoutFiles item[3]
					)
				)
				
				if filmoutFiles.count == 0 then
					messagebox "There are no files that need to be copied over." title:"Create Filmout For Missing Files"
				else if (querybox ("You are about to create a filmout ticket for " + (filmoutFiles.count as string) + " files. Make sure that you specify the office that you want the files transferred to!! Do you wish to continue?") title:"Create Filmout For Missing Files") then
				(
					ShellLaunch filmoutExecutable ""
					Sleep(1)
					
					local count = 1
					prg_mainProgress.value = 0
					for filmoutFile in filmoutFiles do
					(
						ShellLaunch filmoutExecutable ("\"" + filmoutFile + "\"")
						Sleep(1)
						
						prg_mainProgress.value = 100*count/filmoutFiles.count
						count = count + 1
					)
					
					messagebox "All files have been added to the FilmoutTicketAgent application." title:"Create Filmout For Missing Files"
				)
			)
		)
		
		fn UpdateStatus status =
		(
			SMTD_MainRollout.Ui_report (">  " + status)
			txt_status.text = status
		)
		
		fn BytesToKB bytes =
		(
			local kb = bytes
			if kb >= 0 then
			(
				if kb > 0 then
				(
					kb = kb / 1000
					if kb == 0 do kb = 1
				)
			)
			kb
		)
		
		on lv_resources ItemChecked sender e do
		(
			local itemFilename = (e.Item.Text as string)
			for item in currItemArray do
			(
				if item.count > 4 and item[1] == itemFilename then
				(
					item[5] = e.Item.Checked
					exit
				)
			)
			
			local totalFileSizes = 0
			for item in currItemArray do
			(
				if item.count > 4 and (item[5] as booleanClass) then
				(
					local localFileSize = (item[4] as integer)
					if localFileSize >= 0 then
						totalFileSizes = totalFileSizes + (item[4] as integer)
				)
			)
			
			local totalFileSizesMB = totalFileSizes / 1000
			--lbl_size.text = "Data Size To Copy Over: " + (totalFileSizes as string) + " KB"
			lbl_size.text = "Data Size To Copy Over: " + (totalFileSizesMB as string) + " MB"
		)
		
		fn PopulateListView itemArray =
		(
			if itemArray != undefined then
				currItemArray = SMTD_ResourceCheckRollout.CopyDeepArray itemArray
			
			lv_resources.Items.Clear()
			lv_resources.BeginUpdate()
			for i = 1 to currItemArray.count do
			(
				local li = dotNetObject "System.Windows.Forms.ListViewItem"
				li.text = currItemArray[i][1]
				
				local state = (currItemArray[i][2] as string)
				li.SubItems.Add( state )
				
				local filtered = false
				if state == "Exists" then
				(
					li.ForeColor = li.ForeColor.FromArgb 0 128 0
					filtered = not chk_filterExisting.state
				)
				else if state == "Missing" then
				(
					li.ForeColor = li.ForeColor.FromArgb 255 0 0
					filtered = not chk_filterMissing.state
				)
				else if state == "File Sizes Differ" then
				(
					li.ForeColor = li.ForeColor.FromArgb 0 0 255
					filtered = not chk_filterSizeDiff.state
				)
				
				local fileSizeString = "n/a"
				if currItemArray[i].count > 3 then
				(
					local localFileSize = (currItemArray[i][4] as integer)
					if localFileSize != undefined and localFileSize >= 0 then
						fileSizeString = (localFileSize as string) + " KB"
				)
				li.SubItems.Add( fileSizeString )
				
				local checked = false
				if state != "Missing In Both" and state != "Exists" and currItemArray[i].count > 4 then
				(
					local checkedValue = (currItemArray[i][5] as booleanClass)
					if checkedValue != undefined then
						checked = checkedValue
				)
				li.Checked = checked
				
				li.Tag = currItemArray
				
				if not filtered then
					lv_resources.Items.Add li
			)
			lv_resources.EndUpdate()
			lv_resources.Refresh()
		)
		
		fn CopyDeepArray originalArray =
		(
			copiedArray = #()
			for i = 1 to originalArray.count do
			(
				tempArray = #()
				for j = 1 to originalArray[i].count do
					append tempArray (copy originalArray[i][j])
				append copiedArray (copy tempArray #noMap)
			)
			return copiedArray
		)
		
		fn GetSceneResources =
		(
			local sceneResources = #()
			
			for resource in SMTD_ResourceCheckRollout.GetExistingAssetSceneResources() do
				if (finditem sceneResources resource) == 0 do append sceneResources resource
			
			for resource in SMTD_ResourceCheckRollout.GetMissingAssetSceneResources() do
				if (finditem sceneResources resource) == 0 do append sceneResources resource
			
			for resource in SMTD_ResourceCheckRollout.GetExistingSyClothResources() do
				if (finditem sceneResources resource) == 0 do append sceneResources resource
			
			for resource in SMTD_ResourceCheckRollout.GetMissingSyClothResources() do
				if (finditem sceneResources resource) == 0 do append sceneResources resource
			
			sceneResources 
		)
		
		fn GetExistingAssetSceneResources =
		(
			SMTD_ResourceCheckRollout.GetAssetSceneResources false
		)
		
		fn GetMissingAssetSceneResources =
		(
			SMTD_ResourceCheckRollout.GetAssetSceneResources true
		)
		
		fn GetAssetSceneResources missing =
		(
			local resources = #()
			
			ATSOps.Refresh()
			local activeProvider = ATSOps.GetActiveProvider()
			local fileList = #()
			ATSOps.GetFiles &fileList
			
			for filename in fileList do
			(
				local lowerFilename = toLower filename
				if (finditem resources lowerFilename) == 0 and ATSOps.IsInputFile filename then
				(
					local status = ATSOps.GetFileSystemStatus filename
					if (missing and (findItem status #missing) != 0) or (not missing and (findItem status #missing) == 0) then
						append resources lowerFilename
				)
			)
			
			resources
		)
		
		fn GetExistingSyClothResources =
		(
			SMTD_ResourceCheckRollout.GetSyClothResources false
		)
		
		fn GetMissingSyClothResources =
		(
			SMTD_ResourceCheckRollout.GetSyClothResources true
		)
		
		fn GetSyClothResources missing =
		(
			local clothResources = #()
			for o in objects do 
			(
				for m in o.modifiers do
				(
					if ((classof m) as string) == "syCloth" and m.Cache != undefined and m.Cache != "" then
					(
						local lowerFilename = toLower m.Cache
						local fileExists = (doesFileExist m.Cache)
						if (finditem clothResources lowerFilename) == 0 and ((missing and not fileExists) or (not missing and fileExists)) then
							append clothResources lowerFilename
					)
				)
			)
			clothResources
		)
		
		fn ConvertPath filepath type =
		(
			newFilepath = ""
			if type == #driveToUnc then
			(
				for driveToUncMapping in driveToUncMappings do
				(
					if findstring (tolower filepath) (tolower driveToUncMapping[1]) == 1 then
						newFilepath = replace filepath 1 driveToUncMapping[1].count driveToUncMapping[2]
				)
			)
			else if type == #uncToDrive then
			(
				for driveToUncMapping in driveToUncMappings do
				(
					if findstring (tolower filepath) (tolower driveToUncMapping[2]) == 1 then
						newFilepath = replace filepath 1 driveToUncMapping[2].count driveToUncMapping[1]
				)
			)
			newFilepath
		)
		
		fn CollectFileData paths =
		(
			directories = SMTD_ResourceCheckRollout.CollectUniqueDirectories paths
			rawFileData = SMTD_ResourceCheckRollout.CollectRawFileData directories
			fileData = SMTD_ResourceCheckRollout.AssembleFileData rawFileData
			
			local fileDataArray = #()
			for currPath in paths do
			(
				local found = false
				for currFileData in fileData while not found do
				(
					if (tolower currPath) == (tolower currFileData[1]) then
					(
						append fileDataArray currFileData
						found = true
					)
				)
				
				if not found then
				(
					local missingFileData = #()
					append missingFileData currPath
					append missingFileData "0"
					append missingFileData "missing"
					append fileDataArray missingFileData
				)
			)
			fileDataArray
		)
		
		fn CollectUniqueDirectories paths =
		(
			local directories = #()
			for currPath in paths do
			(
				directory = tolower (getFilenamePath currPath)
				if (finditem directories directory) == 0 do
					append directories directory
			)
			directories
		)
		
		fn CollectRawFileData directories =
		(
			local count = 1
			prg_mainProgress.value = 0
			
			local fileDataArray = #()
			for directory in directories do
			(
				local tempFilename = sysInfo.tempdir + "filedata.txt"
				HiddenDOSCommand ( "dir \"" + directory + "\" /a-d /-c /tw > " + tempFilename ) startpath:"c:\\"
				
				local tempFile = openFile tempFilename
				if tempFile != undefined then
				(
					while not eof tempFile do
					(
						local currLine = readline tempFile
						if currLine.count > 0 and currLine[1] != " " then
						(
							local fileData = #()
							append fileData currLine
							append fileData directory
							append fileDataArray fileData
						)
					)
					close tempFile
				)
				
				prg_mainProgress.value = 100*count/directories.count
				count = count + 1
			)
			return fileDataArray
		)
		
		fn AssembleFileData rawFileData =
		(
			local fileDataArray = #()
			for currData in rawFileData do
			(
				local cachedStringStream = currData[1] as stringStream
				local filedate = (readDelimitedString cachedStringStream " ")
				
				seek cachedStringStream 12
				local filetime = (readDelimitedString cachedStringStream " ")
				
				seek cachedStringStream 18
				local fileAmOrPm = (readDelimitedString cachedStringStream " ")
				
				seek cachedStringStream 20
				local filesize = (filterstring (readChars cachedStringStream 18) " ")[1]
				
				seek cachedStringStream 39
				local filenameonly = (readLine cachedStringStream)
				local directory = currData[2]
				
				local filename = directory + filenameonly
				local fileDateTime = (filedate + " " + filetime + " " + fileAmOrPm)
				
				--format "\nTest results: %, %, %" filename filesize fileDateTime
				
				local fileData = #()
				append fileData filename
				append fileData filesize
				append fileData fileDateTime
				append fileDataArray fileData
			)
			fileDataArray
		)
	)
	
	createDialog SMTD_ResourceCheckRollout 850 400
)
-----------------------------------------------------------------------------------------------------------------------------------------------
--THIS FILE CONTAINS THE GENERAL CHECKS TO BE PERFORMED AND THE FUNCTIONS
--TO BE USED TO CHECK AND REPAIR THE SCENE BEFORE SUBMISSION
-----------------------------------------------------------------------------------------------------------------------------------------------
--THIS FILE MAY BE UPDATED WHEN DEADLINE IS UPDATED.
--MODIFY AT YOUR OWN RISK!
-----------------------------------------------------------------------------------------------------------------------------------------------

(
	global SMTD_SanityCheckFunctions
	global SMTD_RepairFunctions 
	global SMTD_SanityChecksToPerform
	global SMTD_SanityCheck_errorReportRollout

	struct SMTD_SanityCheckFunctions
	(
		fn ReturnRETypes =
		(
			global reTypes = #()
			local reManager = maxOps.GetCurRenderElementMgr()
			if reManager != undefined do
			(
				local reCount = reManager.NumRenderElements()
				for i = 0 to reCount - 1 do
					if (reManager.GetRenderElement i).enabled then
					(
						append reTypes (reManager.GetRenderElement i)
					)
			)--end if reManger undefined
			return reTypes
		),
		fn ReturnREPaths =
		(
			global rePaths = #()
			local reManager = maxOps.GetCurRenderElementMgr()
			if reManager != undefined do
			(
				local reCount = reManager.NumRenderElements()
				for i = 0 to reCount - 1 do
					if reManager.GetRenderElementFilename i != undefined and reManager.GetRenderElementFilename i != "" then
					(
						append rePaths (reManager.GetRenderElementFilename i)
					)
			)--end if reManager undefined
			return rePaths
		),
		fn ReturnFumeFXObjects =
		(
			global FumeFXObjects = #()
			for i = 1 to geometry.count where (classof geometry[i] == FumeFX) do
			(
				append FumeFXObjects geometry[i]
			)
			return FumeFXObjects
		),
		fn GetRendererIdString =
		(
			case (renderers.current.classid as string) of
			(
				"#(1, 0)": "scanline"
				"#(1L, 0L)": "scanline"
				
				"#(95494396, 474502030)": "brmax"
				"#(95494396L, 474502030L)": "brmax"
				
				"#(1492548972, 1338981315)": "mentalray"
				"#(1492548972L, 1338981315L)": "mentalray"
				
				"#(1941615238, 2012806412)": "vray"
				"#(1941615238L, 2012806412L)": "vray"
				
				"#(1770671000, 1323107829)": "vrayrt"
				"#(1770671000L, 1323107829L)": "vrayrt"
				
				"#(-1204370534, -399920359)": "krakatoa"
				"#(3090596762L, 3895046937L)": "krakatoa"
				
				"#(217131703, 58075251)": "finalrender"
				"#(217131703L, 58075251L)": "finalrender"
				
				"#(272052741, 712862621)": "maxwell"
				"#(272052741L, 712862621L)": "maxwell"
				
				"#(268839321, 1854680990)": "quicksilver"
				"#(268839321L, 1854680990L)": "quicksilver"
				
				"#(1048411834, 348141227)": "iray"
				"#(1048411834L, 348141227L)": "iray"
				
				"#(1655201228, 1379677700)": "corona"
				"#(1655201228L, 1379677700L)": "corona"
				
				"#(2980325325L, 2688898415L)": "art"
				
				"#(2980329694L, 2688902778L)": "arnold"
				
				"#(198269858, 1937796512)": "redshift"
				"#(198269858L, 1937796512L)": "redshift"
				
				default: ""
			)   
		),
		fn CheckForEmptyScene = 
		(
			(objects as array).count > 0
		),
		fn CheckForLockedViewport =
		(
			-- the locked viewport rendering seems to work fine in max 2015
			if( ((maxVersion())[1]/1000 as integer) > 16 ) then
				true
			else
			(
				-- option only available in 3dsmax 2009 to 2014
				if( ((maxVersion())[1]/1000 as integer) > 10 ) then
					rendUseActiveView
				else
					true
			)
		),
		fn CheckForDuplicateCameraName =
		(
			local st = timestamp()
			local duplicateCameras = #()
			
			local theCameras = for o in objects where findItem Camera.classes (classof o) > 0 collect o
			local theObjects = for o in objects where findItem Camera.classes (classof o) == 0 collect o
			for i = 1 to theCameras.count do
			(
				for j = (i + 1) to theCameras.count do
					if theCameras[i].name == theCameras[j].name do
					(
						format "--Camera [%] has the same name as Camera [%]\n" theCameras[i] theCameras[j]
						appendIfUnique duplicateCameras theCameras[i]
					)
				
				for o in theObjects do
					if theCameras[i].name == o.name do
					(
						format "--Camera [%] has the same name as [%]\n" theCameras[i] o
						appendIfUnique duplicateCameras theCameras[i]
					)
			)
			local pluralString = (if duplicateCameras.count == 1 then "" else "s")
			if duplicateCameras.count > 0 do
				format "--% Camera% With Duplicated Name% Found among % scene objects in % ms\n" duplicateCameras.count pluralString pluralString objects.count (timestamp()-st)
			duplicateCameras.count == 0
		),
		fn CheckForCameraView =
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() != "maxwell" then
				viewport.getCamera() != undefined
			else
				true
		),
		fn CheckForMaxwellCameraView =
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "maxwell" then
				viewport.getCamera() != undefined
			else
				true
		),
		fn CheckForMaxwellSingleFrame =
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "maxwell" then
				rendTimeType != 1
			else
				true
		),
		fn CheckForMPassRenderer =
		(
			rendClass = substring (( classof renderers.current) as string) 1 3
			rendClass == "Bra" or rendClass == "Def"
		),
		fn CheckForRenderingSingleFrame =
		(
			-- Maxwell has it's own fatal error when a single frame is being rendered, so we can
			-- skip this check if Maxwell is the current renderer.
			if SMTD_SanityCheckFunctions.GetRendererIdString() != "maxwell" then
			(
				if ( not SMTDSettings.RemovePadding ) then
					rendTimeType > 1
				else
					true
			)
			else
				true
		),
		fn CheckForRenderingMultiFrame =
		(
			if ( SMTDSettings.RemovePadding ) then
				rendTimeType == 1
			else
				true
		),
		fn CheckForRenderOutputPath =
		(
			rendOutputFilename != ""
		),
		fn CheckForRenderOutputSaveFlag =
		(
			rendOutputFilename == "" OR rendSaveFile 
		),
		fn CheckForLocalDrive =
		(
			local drive_letter = substring rendOutputFilename 1 2
			not (drive_letter == "C:" or drive_letter == "D:" or drive_letter == "E:")
		),	
		fn CheckForRestartRenderer =
		(
			local rendererID = case (renderers.current.classid as string) of
			(
				"#(1, 0)": true --scanline
				"#(1L, 0L)": true --scanline

				"#(1387076610, 288174012)": SMTDSettings.RestartRenderer --brazil
				"#(1387076610L, 288174012L)": SMTDSettings.RestartRenderer --brazil

				"#(95494396, 474502030)": SMTDSettings.RestartRenderer --brmax
				"#(95494396L, 474502030L)": SMTDSettings.RestartRenderer --brmax

				"#(1492548972, 1338981315)": true --mentalray
				"#(1492548972L, 1338981315L)": true --mentalray

				"#(1941615238, 2012806412)": if (not renderers.current.options_dontRenderImage) then SMTDSettings.RestartRenderer else true --vray
				"#(1941615238L, 2012806412L)": if (not renderers.current.options_dontRenderImage) then SMTDSettings.RestartRenderer else true --vray

				"#(1770671000, 1323107829)": if (not renderers.current.V_Ray_settings.options_dontRenderImage) then SMTDSettings.RestartRenderer else true --vrayrt
				"#(1770671000L, 1323107829L)": if (not renderers.current.V_Ray_settings.options_dontRenderImage) then SMTDSettings.RestartRenderer else true --vrayrt

				default: true
			)
		),
		fn CheckForRenderOutputTrail =
		(
			if ( rendTimeType > 1 ) then
			(
				theFileName = getFileNameFile rendOutputFilename
				theFileType = getFileNameType rendOutputFilename
				if not matchPattern theFileType pattern:"*mov" and not matchPattern theFileType pattern:"*avi" then
				(
					if theFileName.count > 3 then
						not (try((classof (execute (substring theFileName theFileName.count 1)) == Integer and classof (execute (substring theFileName (theFileName.count-3) 4)) != Integer ))catch(false))
					else true
				)
				else true
			)
			else true
		),
		fn CheckForRenderOutputMovie =
		(
			theFileType = getFileNameType rendOutputFilename
			not (matchPattern theFileType pattern:"*mov" or matchPattern theFileType pattern:"*avi")
		),
		fn CheckForUntitledFile =
		(
			MaxFileName != ""
		),
		
		fn CheckForDistributedRendering =
		(
			case (renderers.current.classid as string) of
			(
				"#(1492548972, 1338981315)": not (renderers.current.DistributedEnable) --mentalray
				"#(1492548972L, 1338981315L)": not (renderers.current.DistributedEnable) --mentalray
				"#(1941615238, 2012806412)": not (renderers.current.system_distributedRender) --vray
				"#(1941615238L, 2012806412L)": not (renderers.current.system_distributedRender) --vray
				"#(1770671000, 1323107829)": not (renderers.current.distributed_rendering) --vrayrt
				"#(1770671000L, 1323107829L)": not (renderers.current.distributed_rendering) --vrayrt
				default: true
			)
		),
		
		fn CheckForWorkstationDistributedRendering =
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "vray" then
			(
				if renderers.current.system_distributedRender AND not SMTDSettings.DBRUse3dsCmd then
					SMTDSettings.forceWorkstationMode
				else
					true
			)
			else if SMTD_SanityCheckFunctions.GetRendererIdString() == "vrayrt" AND not SMTDSettings.DBRUse3dsCmd then
			(
				if renderers.current.distributed_rendering then
					SMTDSettings.forceWorkstationMode
				else
					true
			)
			else
				true
		),

		fn CheckForVRayDBROffLoadWorkstation =
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "vray" OR SMTD_SanityCheckFunctions.GetRendererIdString() == "vrayrt" then
			(
				if (SMTDSettings.DBR and not SMTDSettings.DBRUse3dsCmd) then
				(
					SMTDSettings.forceWorkstationMode
				)
				else true
			)
			else true
		),
		
		fn CheckForVRayNoFinalImage =
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "vray" then
			(
				if renderers.current.options_dontRenderImage then
					(not SMTDSettings.RestartRenderer) and SMTDSettings.LimitEnabled and (SMTDSettings.MachineLimit == 1)
				else
					true
			)
			else if SMTD_SanityCheckFunctions.GetRendererIdString() == "vrayrt" then
			(
				if renderers.current.V_Ray_settings.options_dontRenderImage then
					(not SMTDSettings.RestartRenderer) and SMTDSettings.LimitEnabled and (SMTDSettings.MachineLimit == 1)
				else
					true
			)
			else
				true
		),

		fn CheckForVRayMultipleHashes =
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "vray" and SMTDSettings.WorkflowMode == "vraystandaloneexport" then
				not (matchPattern rendOutputFilename pattern:"*#*#*")
			else
				true
		),
		fn CheckForVRayConsecutiveHashes =
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "vray" and SMTDSettings.WorkflowMode == "vraystandaloneexport" then
				not (matchPattern rendOutputFilename pattern:"*##*")
			else
				true
		),
		fn CheckForVRayHashInOutputDir =
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "vray" and SMTDSettings.WorkflowMode == "vraystandaloneexport" then
			(
				local outputDir = getFileNamePath rendOutputFilename
				not (matchPattern outputDir pattern:"*#*")
			)
			else
				true
		),
		
		fn CheckForKrakatoaCacheState =
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "krakatoa" then
				not (FranticParticles.GetBoolProperty "EnableParticleCache")
			else
				true
		),
		fn CheckForTileRenderAndVrayVfb = --VRay renderer only (not applicable to VRay RT)
		(
			if SMTDSettings.TilesRendering then
			(
				if SMTD_SanityCheckFunctions.GetRendererIdString() == "vray" then
					not renderers.current.output_on
				else
					true
			)
			else
				true
		),
		fn CheckForRenderElements =
		(
			undefinedFileName = true
			if not SMTDSettings.RenderElementsUpdatePaths do
			(
				reMgr = maxOps.GetCurRenderElementMgr()
				if reMgr != undefined do
				(
					for i = 0 to (reMgr.numrenderelements()-1) do
					(
						fname = reMgr.GetRenderElementFileName i
						if fname == undefined or fname == "" then
						(				
							undefinedFileName = false
						)
					)
				)--end if reMgr undefined
			)
			undefinedFileName
		),
		fn CheckForOutputPathLength =
		(
			RenderOutput = rendOutputFilename
			if RenderOutput.count > 254 then
				false
			else
				true
		),
		fn CheckForREPathLength = 
		(
			re = maxOps.GetCurRenderElementMgr()
			if re != undefined then
			(
				if re.numrenderelements() != 0 then
					(
						Paths = SMTD_SanityCheckFunctions.ReturnREPaths()
						(PathLengths = for n in 1 to Paths.count where (Paths[n].count > 254) collect n).count == 0
					)
				else true
			)--end if re undefined
			else true
		),
		fn CheckForDuplicateREPaths = 
		(
			re = maxOps.GetCurRenderElementMgr()
			if re != undefined then
			(
				if re.numrenderelements() != 0 then
					(
						Paths = SMTD_SanityCheckFunctions.ReturnREPaths()
						uniquePaths = makeuniquearray Paths
						
						local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
						if renderer == "vray" OR renderer == "vrayrt" then
						(
							if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings
							if vr.output_on do return true --exit if V-Ray VFB is enabled as duplicate RE is not applicable
						)
						
						Paths.count == uniquePaths.count
					)
				else true
			)--end if re undefined
			else true
		),
		fn CheckForObjectNames =
		(
			if geometry.count > 0 then
				(
					(for o in 1 to geometry.count where (geometry[o].name.count > 254) collect o).count == 0
				)
			else true
		),
		fn CheckForCorruptGroup =
		(
			if objects.count > 0 then
				(
					(for n in 1 to objects.count where ((isgrouphead objects[n] == true) AND (objects[n].children.count == 0)) collect n).count == 0
				)
			else true
		),
		fn CheckForActiveJigsawRegions =
		(
			if SMTDSettings.RegionRenderingMode == #singleFrameMultiRegion OR SMTDSettings.RegionRenderingMode == #animationMultiRegion then
			(
				(for o in SMTDSettings.MultiRegionData where (o)[1] == true collect true).count != 0
			)
			else true
		),
		fn CheckForVRayRawFileName =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings
				if vr.output_on and vr.output_saveRawFile then
				(
					vr.output_rawFileName != ""
				)
				else true
			)
			else true
		),
		fn CheckForVRaySplitFileName =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings
				if vr.output_on and vr.output_splitgbuffer then
				(
					vr.output_splitfilename != ""
				)
				else true
			)
			else true
		),
		fn CheckForVRayRegionRender =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings
				if vr.output_on then
				(
					not vrayVFBGetRegionEnabled()
				)
				else true
			)
			else true
		),
		fn CheckForVRayRegionRenderAndDenoiser =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			local isRegionRender = (SMTDSettings.RegionRenderingMode != #none)
			local result = true
			if (renderer == "vray" or renderer == "vrayrt") and isRegionRender then
			(
				local theRenderer = SMTDFunctions.getRendererObject()
				-- VRayDenoiser render element is only applied when using the V-Ray frame buffer
				-- (theRenderer.output_on) with the memory buffer enabled (theRenderer.output_useram) and either:
				--    1. outputting a V-Ray raw image file (theRenderer.output_saveRawFile) OR
				--    2. outputing separate render channels (theRenderer.output_splitgbuffer)
				if theRenderer.output_on AND theRenderer.output_useram AND (theRenderer.output_splitgbuffer OR theRenderer.output_saveRawFile)  then
				(
					local reManager = maxOps.GetCurRenderElementMgr()
					if reManager != undefined and reManager.GetElementsActive() then
					(
						for i = 0 to reManager.NumRenderElements() - 1 while result do
						(
							local reObject = reManager.GetRenderElement i
							result = (classof reObject != VRayDenoiser)
						)
					)
				)
			)
			result
		),
		fn CheckForVRayTrackMouse =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				local vrayVer = 2
				vrayVersionCheck = try(vrayVersion())catch(undefined)
				if vrayVersionCheck != undefined then (
					vrayVer = vrayVersionCheck[1][1] as integer
				)
				if vrayVer >= 3 then
				(
					if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings

					if vr.output_on then
					(
						-- Function only available in V-Ray v3.1 onwards
						try((vfbControl(#trackmouse))[1] == 0)catch(true)
					)
					else true
				)
				else true
			)
			else true
		),
		fn CheckForCameraMatchBmp =
		(
			oldView = viewport.activeViewport
			bitmapCount = #()
			for i in 1 to viewport.numViews do
			(
				viewport.activeViewport = i
				if backgroundimagefilename != "" then
				(
					append bitmapCount backgroundimagefilename
				)
			)
			try(viewport.activeViewport = oldView)catch()
			bitmapCount.count == 0
		),
		fn CheckForTgaBitDepth =
		(
			if rendOutputFilename != "" then
			(
				if (toLower (getFileNameType rendOutputFilename)) == ".tga" then
				(
					Targa.getColorDepth() == 32
				)
				else true
			)
			else true
		),
		fn CheckForVRayVFBTA =
		(
			local enabledTA = #()
			if SMTDSettings.RegionRenderingMode == #singleFrameTiles and (not SMTDSettings.SingleTileJobDraft) then
			(
				local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
				if renderer == "vray" OR renderer == "vrayrt" then
				(
					if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings
					
					if vr.output_on and vr.output_splitgbuffer then
					(
						reTypes = SMTD_SanityCheckFunctions.ReturnRETypes()
						if reTypes.count != 0 then
						(
							classTypes = #(VRayAlpha, VRayReflection, VRayReflectionFilter, VRayRefraction, VRayRefractionFilter)

							for n in 1 to reTypes.count do
							(
								if findItem classTypes (classof reTypes[n]) > 0 then
								(
									--Append the Render Element Name as string to the enabledTA array if it matches one of the above classType array items
									append enabledTA (reTypes[n].elementName as string)
								)
							)
						)
						if vr.output_splitAlpha then
						(
							--Additionally, if "Save alpha" is enabled in the V-Ray VFB, then append this to the enabledTA array
							append enabledTA "Save alpha"
						)
					)
				)
			)
			--If array != 0 then there is either a V-Ray RE (16bit) or VFB "Save Alpha" (16bit) which will fail via Tile Assembler and must use Draft Tile Assembler instead.
			enabledTA.count == 0
		),
		fn CheckForVRayValidIMAPFile = --VRay renderer only (not applicable to VRay RT)
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "vray" then
			(
				vr = renderers.current
				if vr.gi_on AND vr.gi_primary_type == 0 AND vr.adv_irradmap_mode == 2 then
				(
					if (vr.adv_irradmap_loadFileName == "") OR (vr.adv_irradmap_loadFileName == undefined) then
					(
						false
					)
					else if (not doesFileExist vr.adv_irradmap_loadFileName) then
					(
						false
					)
					else if ((toLower (getFileNameType vr.adv_irradmap_loadFileName)) != ".vrmap") then
					(
						false
					)
					else true
				)
				else true
			)
			else true
		),
		fn CheckForVRayValidPhotonFile = --VRay renderer only (not applicable to VRay RT)
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "vray" then
			(
				vr = renderers.current
				if vr.gi_on AND (vr.gi_primary_type == 1 OR vr.gi_secondary_type == 1) AND vr.photonMap_mode == 1 then
				(
					if (vr.photonMap_loadFileName == "") OR (vr.photonMap_loadFileName == undefined) then
					(
						false
					)
					else if (not doesFileExist vr.photonMap_loadFileName) then
					(
						false
					)
					else if ((toLower (getFileNameType vr.photonMap_loadFileName)) != ".vrpmap") then
					(
						false
					)
					else true
				)
				else true
			)
			else true
		),
		fn CheckForVRayValidLCFile =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings

				if vr.gi_on AND (vr.gi_primary_type == 3 OR vr.gi_secondary_type == 3) AND vr.lightcache_mode == 2 then
				(
					if (vr.lightcache_loadFileName == "") OR (vr.lightcache_loadFileName == undefined) then
					(
						false
					)
					else if (not doesFileExist vr.lightcache_loadFileName) then
					(
						false
					)
					else if ((toLower (getFileNameType vr.lightcache_loadFileName)) != ".vrlmap") then
					(
						false
					)
					else true
				)
				else true
			)
			else true
		),
		fn CheckForVRayValidCausticsFile = --VRay renderer only (not applicable to VRay RT)
		(
			if SMTD_SanityCheckFunctions.GetRendererIdString() == "vray" then
			(
				vr = renderers.current
				if vr.caustics_on AND vr.caustics_mode == 1 then
				(
					if (vr.caustics_loadFileName == "") OR (vr.caustics_loadFileName == undefined) OR (not doesFileExist vr.caustics_loadFileName) then
					(
						false
					)
					else true
				)
				else true
			)
			else true
		),
		fn CheckForActiveShade =
		(
			if( ((maxVersion())[1]/1000 as integer) >= 15 ) then --Max2013 or newer
			(
				renderers.renderDialogMode != #activeShade
			)
			else true
		),
		fn CheckForFumeFXSimProgress =
		(
			FumeFXObjects = SMTD_SanityCheckFunctions.ReturnFumeFXObjects()
			if FumeFXObjects.count > 0 and (SMTDSettings.DisableProgressUpdateTimeout != true) then
			(
				(for n in FumeFXObjects where (n.BackBurnerSim) collect n).count == 0
			)
			else true
		),
		fn CheckForFumeFXSimChunkSize =
		(
			FumeFXObjects = SMTD_SanityCheckFunctions.ReturnFumeFXObjects()
			if FumeFXObjects.count > 0 and (rendTimeType != 1) then
			(
				(for n in FumeFXObjects where (n.BackBurnerSim) collect n).count == 0
			)
			else true
		),
		fn CheckForFumeFXSimMachineLimit =
		(
			FumeFXObjects = SMTD_SanityCheckFunctions.ReturnFumeFXObjects()
			if (FumeFXObjects.count > 0 and (SMTDSettings.LimitEnabled != true)) or (FumeFXObjects.count > 0 and (SMTDSettings.MachineLimit != 1)) then
			(
				(for n in FumeFXObjects where (n.BackBurnerSim) collect n).count == 0
			)
			else true
		),
		fn CheckForDoubleDelimiterRenderOutput =
		(
			delimiter = SMTDSettings.Delimiter
			local fileExt = getFilenameType rendOutputFilename
			if delimiter != "" AND (matchPattern rendOutputFilename pattern:("*" + delimiter + fileExt)) then
			(
				false
			)
			else true
		),
		fn CheckForDoubleDelimiterVFBRaw = --checking if Deadline delimiter is duplicated up with user entered period character
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				delimiter = SMTDSettings.Delimiter
				if delimiter != "" then
				(
					if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings

					if vr.output_on AND vr.output_saveRawFile AND vr.output_rawFileName != "" then
					(
						local fileExt = getFilenameType vr.output_rawFileName
						if matchPattern vr.output_rawFileName pattern:("*" + delimiter + fileExt) then
						(
							false
						)
						else true
					)
					else true
				)
				else true
			)
			else true
		),
		fn CheckForDoubleDelimiterVFBRawNative = --checking if Deadline delimiter is set to blank but VRay VFB RAW native delimiter is enabled and user entered period character as well
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				delimiter = SMTDSettings.Delimiter
				if delimiter == "" then
				(
					if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings

					if (hasProperty vr #fileName_addDot) AND vr.fileName_addDot then
					(
						if vr.output_on AND vr.output_saveRawFile AND vr.output_rawFileName != "" then
						(
							local fileExt = getFilenameType vr.output_rawFileName
							if matchPattern vr.output_rawFileName pattern:("*" + "." + fileExt) then
							(
								false
							)
							else true
						)
						else true
					)
					else true
				)
				else true
			)
			else true
		),
		fn CheckForDoubleDelimiterSplitChannels =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				delimiter = SMTDSettings.Delimiter
				if delimiter != "" then
				(
					if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings

					if vr.output_on AND vr.output_splitgbuffer AND vr.output_splitfilename != "" AND vr.output_splitfilename != undefined then
					(
						local fileExt = getFilenameType vr.output_splitfilename
						if matchPattern vr.output_splitfilename pattern:("*" + delimiter + fileExt) then
						(
							false
						)
						else true
					)
					else true
				)
				else true
			)
			else true
		),
		fn CheckForDoubleDelimiterRenderElement =
		(
			delimiter = SMTDSettings.Delimiter
			if delimiter != "" then
			(
				re = maxOps.GetCurRenderElementMgr()
				if re != undefined then
				(
					if re.numrenderelements() != 0 then
					(
						Paths = SMTD_SanityCheckFunctions.ReturnREPaths()

						for i = 1 to Paths.count do
						(
							local fileName = getFileNameFile Paths[i]

							if matchPattern fileName pattern:("*" + delimiter) then
							(
								return false
							)
						)

						true
					)
					else true
				)--end if re undefined
				else true
			)
			else true
		),
		fn CheckForVRayVFBValidRegion =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" then
			(
				vr = renderers.current
				if vr.output_on AND (vrayVFBGetRegionEnabled()) then
				(
					if vr.output_getsetsfrommax then
						((vrayVFBGetRegion())[1] < RenderWidth) and ((vrayVFBGetRegion())[2] < RenderHeight)
					else
						((vrayVFBGetRegion())[1] < vr.output_width) and ((vrayVFBGetRegion())[2] < vr.output_height)
				)
				else true
			)
			else true
		),
		fn CheckForVRayRenderMaskEmptySel =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings
				if vr.imageSampler_renderMask_type == 1 then --Texture
				(
					if vr.imageSampler_renderMask_texmap == undefined then false else true
				)
				else if vr.imageSampler_renderMask_type == 2 then --Selected
				(
					if selection.count == 0 then false else true
				)
				else if vr.imageSampler_renderMask_type == 3 then --Include/Exclude list
				(
					includeList = try((vr.includeListRenderSubset).count)catch(0)
					excludeList = try((vr.excludeListRenderSubset).count)catch(0)
					if (includeList + excludeList) == 0 then false else true
				)
				else if vr.imageSampler_renderMask_type == 4 then --Layers
				(
					layerCount = try((vr.imageSampler_renderMask_layers).count)catch(0)
					if layerCount == 0 then false else true
				)
				else if vr.imageSampler_renderMask_type == 5 then --Object IDs
				(
					if vr.imageSampler_renderMask_objectIDs == "" then false else true
				)
				else true
			)
			else true
		),
		fn CheckForVRayVFB =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings
				if vr.output_on AND not vr.output_splitgbuffer then false else true
			)
			else true
		),
		fn CheckForUniqueREPaths =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" OR renderer == "vrayrt" then
			(
				if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings
				if vr.output_on do return true --If V-Ray VFB enabled for output, then let one of the other SMTD sanity checks continue validating various situations and return true here
			)
			--If renderer not V-Ray/RT then continue to check for possible file collision for RE's
			reTypes = SMTD_SanityCheckFunctions.ReturnRETypes()
			if reTypes.count != 0 then
			(
				if (SMTDSettings.RenderElementsUpdatePaths OR SMTDSettings.RenderElementsUpdateFilenames) then
				(
					if not SMTDSettings.RenderElementsIncludeNameInPath AND not SMTDSettings.RenderElementsIncludeTypeInPath AND not SMTDSettings.RenderElementsIncludeNameInFileName AND not SMTDSettings.RenderElementsIncludeTypeInFileName then
					(
						false
					)
					else true
				)
				else true
			)
			else true
		),
		fn CheckForValidGpuDevices =
		(
			if (SMTDSettings.GpuDevices != undefined) AND (SMTDSettings.GpuDevices != "") AND (SMTDSettings.GpusPerTask == 0) then
			(
				local rx = dotnetobject "System.Text.RegularExpressions.Regex" "^(\d{1,2}(,\d{1,2})*)?$"
				if rx.isMatch SMTDSettings.GpuDevices then true else false
			)
			else true
		),
		fn CheckForGpuConcurrentTasks =
		(
			if (SMTDSettings.GpuDevices != undefined) AND (SMTDSettings.GpuDevices != "") AND (SMTDSettings.GpusPerTask == 0) then
			(
				if SMTDSettings.MaxTasksPerSlave > 1 then false else true
			)
			else true
		),
		fn CheckForBadCameraNames =
		(
			local badCamNames=#()
			local theCameras = for o in objects where findItem Camera.classes (classof o) > 0 collect o.name
			if (theCameras as array).count > 0 then
			(
				for n in 1 to theCameras.count do
				(
					tempString = trimLeft theCameras[n]
					tempString = trimRight tempString
					if tempString.count != theCameras[n].count do append badCamNames theCameras[n]
				)
			)
			badCamNames.count == 0
		),
		fn CheckForCoronaRegionRender =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "corona" then
			(
				try(not renderers.current.system_vfbRegions_enabled)catch(true)
			)
			else true
		),
		fn CheckForRedshiftConcurrency =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if (renderer == "redshift") AND (SMTDSettings.GpusPerTask != 1) then
			(
				if SMTDSettings.MaxTasksPerSlave > 1 then false else true
			)
			else true
		)
	)

	struct SMTD_RepairFunctions
	(
		fn doNothing = 
		(
			true
		),
		fn cannotFix =
		(
			SMTD_SanityCheck_errorReportRollout.log_action "FATAL" (color 0 0 255) true  ("Please load a new MAX file or create/merge objects before submitting!")
		),	
		fn SuggestPossibleCamera = 
		(
			local theCameras = for o in objects where findItem Camera.classes (classof o) > 0 collect o
			if (theCameras as array).count > 0 then
			(
				possibleCamera = SelectByName single:true title:"Select Camera to Submit to Deadline:" filter:(fn filterCamera obj = (superclassof obj == Camera))
				if possibleCamera != undefined then
				(
					viewport.setCamera possibleCamera 
					SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true ("Camera ["+ possibleCamera.name +"] set in the current viewport.")
				)	
				else
					SMTD_SanityCheck_errorReportRollout.log_action "FAILED" (color 0 0 255) true "No Camera was selected."
			)	
			else
				SMTD_SanityCheck_errorReportRollout.log_action "FAILED" (color 0 0 0) true "There are NO CAMERAS in the scene."

		),
		fn FixDuplicateCameraName =
		(
			local duplicateCameras = #()
			local theCameras = for o in objects where findItem Camera.classes (classof o) > 0 collect o
			local theObjects = for o in objects where findItem Camera.classes (classof o) == 0 collect o
			for i = 1 to theCameras.count do
			(
				for j = (i + 1) to theCameras.count do
					if theCameras[i].name == theCameras[j].name do
					(
						appendIfUnique duplicateCameras theCameras[i]
					)
				
				for o in theObjects do
					if theCameras[i].name == o.name do
					(
						appendIfUnique duplicateCameras theCameras[i]
					)
			)
			local done = false
			local cnt = 0
			for o in duplicateCameras while not done do
			(
				cnt += 1
				local oldName = o.name
				local hasCameraName = 
				local newName = o.name
				if not matchPattern o.name pattern:"*camera*" do newName += "_camera"
				newName = uniquename newName
				local theMessage = "" as stringStream
				format "The Camera \n%\n"  o to:theMessage
				format "has a duplicate name!\n\n" to:theMessage
				format "Click [Yes] to RENAME it to '%'\n" newName to:theMessage
				format "Click [No] to SELECT this Camera for manual editing.\n" to:theMessage
				format "Click [Cancel] to CANCEL the fixing routine.\n" to:theMessage
				local answer = yesnocancelbox (theMessage as string) title:("Rename "+cnt as string + (if duplicateCameras.count == 1 then " Camera with Duplicate Name" else (" of "+duplicateCameras.count as string  +" Cameras with Duplicate Names")))
				case answer of
				(
					#yes: (
						o.name = newName
						SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true ("Camera ["+ oldName +"] renamed to ["+ newName +"].")
					)
					#no: 	(
						select o
						SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0 ) true ("Camera ["+ oldName +"] selected for manual editing.")
						done = true
					)
					#cancel: (
						SMTD_SanityCheck_errorReportRollout.log_action "Cancel" (color 0 0 255) true ("Camera renaming canceled by the user.")
						done = true
					)
				)
			)
		),		
		fn EnableMPassMBlur = 
		(
			theCam = viewport.getCamera() 
			if theCam != undefined do 
			(
				if classof theCam.mpassEffect != Motion_BlurMPassCamEffect do 
					theCam.mpassEffect = Motion_BlurMPassCamEffect()
				theCam.mpassEnabled = true
				SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true ("Enabled MultiPass Motion Blur in Camera ["+theCam.name+"]")
			)	
		),
		fn FixLockedViewport =
		(
			-- option only available in 3dsmax 2009 and later
			if( ((maxVersion())[1]/1000 as integer) > 10 ) do
			(
				renderSceneDialog.close()
				rendUseActiveView = true
				renderSceneDialog.open()
				SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Locked viewport disabled."
			)
		),
		fn FixRenderingSingleFrame =
		(
			renderSceneDialog.close()
			rendTimeType = 2
			renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Rendering Output Time changed to ACTIVE TIME SEGMENT."
		),
		fn FixRenderingMultiFrame =
		(
			renderSceneDialog.close()
			rendTimeType = 1
			renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Rendering Output Time changed to SINGLE FRAME."
		),
		fn FixRenderOutputPath =
		(
			renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, Pick a valid path, then re-test!"
		),
		fn FixRenderOutputSaveFlag =
		(
			renderSceneDialog.close()
			rendSaveFile = true
			renderSceneDialog.open()
		),
		fn FixRestartRenderer =
		(
			SMTDSettings.RestartRenderer = true
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "RestartRenderer" (SMTDSettings.RestartRenderer as string)
		),
		fn FixRenderOutputTrail =
		(
			rendOutputFilename = getFileNamePath rendOutputFilename + getFileNameFile rendOutputFilename + "_" + getFileNameType rendOutputFilename
		),
		fn FixRenderOutputMovie =
		(
			renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, please select a single frame format, then re-test!"
		),
		fn SaveUntitledFile =
		(
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "File>Save As dialog is OPEN. Please save the scene to a file, then re-test!"
			max file save 
		),
		fn FixDistributedRendering =
		(
			case (renderers.current.classid as string) of
			(
				"#(1492548972, 1338981315)": renderers.current.DistributedEnable = false --mentalray
				"#(1492548972L, 1338981315L)": renderers.current.DistributedEnable = false --mentalray
				"#(1941615238, 2012806412)": renderers.current.system_distributedRender = false --vray
				"#(1941615238L, 2012806412L)": renderers.current.system_distributedRender = false --vray
				"#(1770671000, 1323107829)": renderers.current.distributed_rendering = false --vrayrt
				"#(1770671000L, 1323107829L)": renderers.current.distributed_rendering = false --vrayrt
				default: true
			)
		),
		fn FixVRayDistributedRendering =
		(
			SMTDSettings.ForceWorkstationMode = true
			setIniSetting SMTDPaths.InIFile "RenderingOptions"  "ForceWorkstationMode" (SMTDSettings.ForceWorkstationMode as string)
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Workstaton Mode has been enabled."
		),
		fn FixVRayNoFinalImage =
		(
			SMTDSettings.RestartRenderer = false
			SMTDSettings.LimitEnabled = true
			SMTDSettings.MachineLimit = 1
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Restart Renderer disabled, Machine Limit enabled and set to 1."
		),
		fn FixVRayMultipleHashes =
		(
			renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, ensure the output path contains at most one hash character."
		),
		fn FixVRayConsecutiveHashes =
		(
			local renderDialogState = renderSceneDialog.isOpen()
			local oldFilename = rendOutputFilename
			renderSceneDialog.close()
			local tokens = filterString rendOutputFilename "#"
			local newOutput = "" as stringStream
			for i = 1 to tokens.count - 1 do
				format "%#" tokens[i] to:newOutput
			format "%" tokens[tokens.count] to:newOutput
			rendOutputFilename = newOutput as string
			if renderDialogState do renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 0 155 0) false ("Output filename changed from [" + oldFilename + "] to [" + rendOutputFilename + "]")
		),
		fn FixVRayHashInOutputDir =
		(
			renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, ensure the output directory contains no hash characters."
		),
		fn FixKrakatoaCache =
		(
			try(
				FranticParticles.SetProperty "EnableParticleCache" "false"
				FranticParticles.SetProperty "EnableLightingCache" "false"
				SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Krakatoa PCache and LCache turned OFF."
				Krakatoa_GUI_Main.refresh_GUI()
			)catch()
		),
		fn FixMaxwellSingleFrame =
		(
			renderSceneDialog.close()
			rendTimeType = 4
			rendPickupFrames = (((slidertime as integer) / ticksperframe) as string)
			renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Rendering Output Time changed to animation with just the current frame."
		),
		fn FixTileRenderAndVrayVfb =
		(
			renderers.current.output_on = false
		),
		fn FixRenderElements =
		(
			renderSceneDialog.close()
			renderSceneDialog.open() 
			for i=1 to tabbedDialogs.getNumPages #render do
			(
				if (tabbedDialogs.getPageTitle #render i) == "Render Elements" then
					tabbedDialogs.setCurrentPage #render i
			)
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) true "If using V-Ray Frame Buffer and ALL RE's have been Disabled, then IGNORE this Sanity Check!"
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) true "Ensure that a Render Element Output File has been selected for each Render Element!"
		),
		fn FixOutputPathLength =
		(
			renderSceneDialog.open()
			if tabbedDialogs.isOpen #render do
				--Common Tab
				tabbedDialogs.setCurrentPage #render #(1379758294, 1692354418)
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) true "Try reducing the Render Output Path Length < 255 characters!"
		),
		fn FixREPathLength =
		(
			renderSceneDialog.open()
			if tabbedDialogs.isOpen #render do
				--RE Tab
				tabbedDialogs.setCurrentPage #render #(1547006576, 1564889954)
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) true "Try reducing the RE - Render Path Length < 255 characters!"
		),
		fn FixDuplicateREPaths =
		(
			renderSceneDialog.open()
			if tabbedDialogs.isOpen #render do
				--RE Tab
				tabbedDialogs.setCurrentPage #render #(1547006576, 1564889954)
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) true "One or more Render Elements are saving to the same File!"
		),
		fn FixObjectNames =
		(
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "One or more objects have a name > 255 characters!"
		),
		fn FixCorruptGroup =
		(
			nodeSel=#()
			(for n in 1 to objects.count where ((isgrouphead objects[n] == true) AND (objects[n].children.count == 0)) do (append nodeSel objects[n]))
			if nodeSel.count > 0 then
			(
				for n in 1 to nodeSel.count do
				(
					SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true ("Group Deleted: ["+ nodeSel[n].name +"]")
				)
			)
			delete nodeSel
		),
		fn FixVRayRawFileName =
		(
			renderSceneDialog.open()
			if tabbedDialogs.isOpen #render do
				tabbedDialogs.setCurrentPage #render #(539584185, 72172985) --VRay Tab
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "V-Ray Frame Buffer (VFB): [V-Ray raw image file] - Ensure you enter a valid image file save path."
		),
		fn FixVRaySplitFileName =
		(
			renderSceneDialog.open()
			if tabbedDialogs.isOpen #render do
				tabbedDialogs.setCurrentPage #render #(539584185, 72172985) --VRay Tab
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "V-Ray Frame Buffer (VFB): [Separate render channels] - Ensure you enter a valid image file save path."
		),
		fn FixVRayRegionRender =
		(
			vrayVFBSetRegionEnabled false
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "V-Ray Frame Buffer (VFB): [Region render] is now DISABLED!"
		),
		fn FixVRayTrackMouse =
		(
			try(
				vfbControl(#trackmouse) false --function only available in V-Ray v3.1 onwards
				SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "V-Ray Frame Buffer (VFB): [Track mouse while rendering] is now DISABLED!"
			)catch()
		),
		fn FixCameraMatchBmp =
		(
			oldView = viewport.activeViewport
			cameraBitmaps=#()
			for n in 1 to viewport.numViews do
			(
				viewport.activeViewport = n
				if backgroundimagefilename != "" then
				(
					append cameraBitmaps backgroundimagefilename
				)
			)
			for n in 1 to cameraBitmaps.count do (SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true ("Deleted: ["+ cameraBitmaps[n] +"]"))

			for n in 1 to viewport.numViews do
			(
				viewport.activeViewport = n
				if backgroundimagefilename != "" then
				(
					backgroundimagefilename = ""
				)
			)
			try(viewport.activeViewport = oldView)catch()
		),
		fn FixTgaBitDepth =
		(
			renderSceneDialog.open()
			if tabbedDialogs.isOpen #render do
				tabbedDialogs.setCurrentPage #render #(1379758294, 1692354418) --Common Tab
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, change the Render Output, *.tga bit depth to 32bit for Alpha."
		),
		fn FixVRayVFBTA =
		(
			SMTDSettings.SingleTileJobDraft = true
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Use Draft for Assembly has been ENABLED."
		),
		fn FixVRayValidIMAPFile =
		(
			renderSceneDialog.open()
			try(
			if tabbedDialogs.isOpen #render do
				tabbedDialogs.setCurrentPage #render #(353437075,945298394) --VRay GI tab
			)catch()
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, V-Ray GI tab, ensure IMAP File (*.vrmap) is set to a valid file path."
		),
		fn FixVRayValidPhotonFile = 
		(
			renderSceneDialog.open()
			try(
			if tabbedDialogs.isOpen #render do
				tabbedDialogs.setCurrentPage #render #(353437075,945298394) --VRay GI tab
			)catch()
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, V-Ray GI tab, ensure Photon File (*.vrpmap) is set to a valid file path."
		),
		fn FixVRayValidLCFile =
		(
			renderSceneDialog.open()
			try(
			if tabbedDialogs.isOpen #render do
				tabbedDialogs.setCurrentPage #render #(353437075,945298394) --VRay GI tab
			)catch()
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, V-Ray GI tab, ensure LC File (*.vrlmap) is set to a valid file path."
		),
		fn FixVRayValidCausticsFile =
		(
			renderSceneDialog.open()
			try(
			if tabbedDialogs.isOpen #render do
				tabbedDialogs.setCurrentPage #render #(353437075,945298394) --VRay GI tab
			)catch()
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the Render Scene Dialog, V-Ray GI tab, ensure Caustics File (*.vrpmap) is set to a valid file path."
		),
		fn FixActiveShade =
		(
			renderers.renderDialogMode = #Production
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Production Render Mode has been ENABLED."
		),
		fn FixFumeFXSimProgress =
		(
			SMTDSettings.DisableProgressUpdateTimeout = true
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Progress Update Timeout has been DISABLED for FumeFX Sim Job."
		),
		fn FixFumeFXSimChunkSize =
		(
			rendTimeType = 1
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Rendering Output Time set to SINGLE FRAME for FumeFX Sim Job."
		),
		fn FixFumeFXSimMachineLimit =
		(
			SMTDSettings.LimitEnabled = true
			SMTDSettings.MachineLimit = 1
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Machine Limit ENABLED and Set to 1 for FumeFX Sim Job."
		),
		fn FixVRayDBROffLoadWorkstation =
		(
			SMTDSettings.DBRUse3dsCmd = True
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "V-Ray off-load DBR will now use the 3dsCmd plugin."	
		),
		fn FixDoubleDelimiterRenderOutput =
		(
			local oldState = renderSceneDialog.isOpen()
			if oldState == true then renderSceneDialog.close()

			local fileName = getFileNameFile rendOutputFilename
			local newFileName = replace fileName fileName.count 1 "" 

			rendOutputFilename = getFileNamePath rendOutputFilename + newFileName + getFileNameType rendOutputFilename
			
			if oldState == true then renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Removed extra delimiter from render output filename."
		),
		fn FixDoubleDelimiterVFBRaw =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings

			local oldState = renderSceneDialog.isOpen()
			if oldState == true then renderSceneDialog.close()

			local fileName = vr.output_rawFileName
			local splitFile = filterString fileName "."

			local extensionIndex = findString fileName ("." + splitFile[splitFile.count])

			vr.output_rawFileName = replace fileName (extensionIndex - 1) 1 ""
			
			if oldState == true then renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Removed extra delimiter from V-Ray raw image filename."
		),
		fn FixDoubleDelimiterSplitChannels = 
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings

			local oldState = renderSceneDialog.isOpen()
			if oldState == true then renderSceneDialog.close()

			local fileName = vr.output_splitfilename
			local splitFile = filterString fileName "."

			local extensionIndex = findString fileName ("." + splitFile[splitFile.count])

			vr.output_splitfilename = replace fileName (extensionIndex - 1) 1 ""
			
			if oldState == true then renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Removed extra delimiter from the separate render channel filename."
		),
		fn FixDoubleDelimiterRenderElement =
		(
			local oldState = renderSceneDialog.isOpen()
			if oldState == true then renderSceneDialog.close()

			local reManager = maxOps.GetCurRenderElementMgr()
			delimiter = SMTDSettings.Delimiter
			Paths = SMTD_SanityCheckFunctions.ReturnREPaths()

			for i = 1 to Paths.count do
			(
				local fileName = getFileNameFile Paths[i]

				if matchPattern fileName pattern:("*" + delimiter) then
				(
					local newFileName = replace fileName fileName.count 1 "" 
					reManager.SetRenderElementFilename (i - 1) (getFileNamePath rendOutputFilename + newFileName + getFileNameType rendOutputFilename)
				)
			)

			if oldState == true then renderSceneDialog.open()
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Removed extra delimiter(s) from render element filename(s)."
		),
		fn FixVRayVFBValidRegion =
		(
			vrayVFBSetRegionEnabled false
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "V-Ray Frame Buffer (VFB): [Region render] has been DISABLED!"
		),
		fn FixVRayRenderMaskEmptySel =
		(
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "In the RSD -> V-Ray tab, 'Image sampler (Antialiasing)' rollout, ensure 'Render mask' selection is VALID!"
		),
		fn FixVRayVFB =
		(
			local renderer = SMTD_SanityCheckFunctions.GetRendererIdString()
			if renderer == "vray" then vr = renderers.current else vr = renderers.current.V_Ray_settings
			vr.output_on = false
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "V-Ray VFB Disabled"
		),
		fn FixUniqueREPaths =
		(
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "Ensure at least one 'Include' RE checkbox option is enabled in SMTD -> Render -> 3ds Max Pathing."
		),
		fn SuggestValidGpuSyntax =
		(
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "Trailing 'commas' should be removed. Valid Examples: 0 or 2 or 0,1,2 or 0,3,4 etc"
		),
		fn FixGpuConcurrentTasks =
		(
			SMTDSettings.MaxTasksPerSlave = 1
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Concurrent Tasks set to 1."
		),
		fn FixBadCameraNames =
		(
			local theCameras = for o in objects where findItem Camera.classes (classof o) > 0 collect o
			for n in 1 to theCameras.count do
			(
				theCameras[n].name = (trimLeft (trimRight theCameras[n].name) )
			)
			SMTD_SanityCheck_errorReportRollout.log_action "Fixed" (color 0 155 0) true "Removed BAD characters from Camera names."
		),
		fn FixCoronaRegionRender = 
		(
			renderers.current.system_vfbRegions_enabled = false
			SMTD_SanityCheck_errorReportRollout.log_action "Hint" (color 155 0 0) false "Corona Frame Buffer (VFB): [Region render] is now DISABLED!"
		)
	)

	global SMTD_SanityChecksToPerform =
	#(
		#(SMTD_SanityCheckFunctions.CheckForEmptyScene, #fail, "The scene does not contain ANY objects!", SMTD_RepairFunctions.cannotFix, true),
		#(SMTD_SanityCheckFunctions.CheckForUntitledFile, #fix, "The current Scene Name is Untitled.", SMTD_RepairFunctions.SaveUntitledFile, true),
		#(SMTD_SanityCheckFunctions.CheckForCameraView, #fix, "The current view is NOT a Camera.", SMTD_RepairFunctions.SuggestPossibleCamera, true),
		#(SMTD_SanityCheckFunctions.CheckForRenderingSingleFrame, #fix, "The Render Time Output is set to SINGLE FRAME!", SMTD_RepairFunctions.FixRenderingSingleFrame, true),
		#(SMTD_SanityCheckFunctions.CheckForLocalDrive, #fix, "The Render Output Path appears to point at a LOCAL DRIVE!", SMTD_RepairFunctions.FixRenderOutputPath, true),
		#(SMTD_SanityCheckFunctions.CheckForRenderOutputTrail, #fix, "The Render Output File Name ends with a DIGIT - trailing numbers might fail.", SMTD_RepairFunctions.FixRenderOutputTrail, true),
		#(SMTD_SanityCheckFunctions.CheckForRenderOutputPath, #fix, "The Render Output Path is NOT DEFINED!", SMTD_RepairFunctions.FixRenderOutputPath, true),
		#(SMTD_SanityCheckFunctions.CheckForRenderOutputMovie, #warn, "The Render Output is set to a MOVIE format.", SMTD_RepairFunctions.FixRenderOutputMovie, true),
		#(SMTD_SanityCheckFunctions.CheckForRenderOutputSaveFlag, #fix, "The Render Output Save File Checkbox is NOT CHECKED! No Frames Will Be Saved!", SMTD_RepairFunctions.FixRenderOutputSaveFlag, true),
		#(SMTD_SanityCheckFunctions.CheckForDistributedRendering, #warn, "The Distributed Rendering option is enabled for this renderer.", SMTD_RepairFunctions.FixDistributedRendering, true),
		#(SMTD_SanityCheckFunctions.CheckForMaxwellCameraView, #fail, "Maxwell is the renderer and the current view is NOT a Camera.", SMTD_RepairFunctions.SuggestPossibleCamera, true),
		#(SMTD_SanityCheckFunctions.CheckForDuplicateCameraName, #fail, "The scene contains Cameras with non-unique names. See MAXScript Listener for details.", SMTD_RepairFunctions.FixDuplicateCameraName, true),
		#(SMTD_SanityCheckFunctions.CheckForWorkstationDistributedRendering, #fix, "Workstation Mode must be enabled to use V-Ray Distributed Rendering (via 3dsmax plugin).", SMTD_RepairFunctions.FixVRayDistributedRendering, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayNoFinalImage, #warn, "Not rendering final image (GI), so Restart Renderer should be disabled, and Machine Limit set to 1.", SMTD_RepairFunctions.FixVRayNoFinalImage, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayMultipleHashes, #warn, "The Render Output Path contains multiple hash characters. V-Ray replaces each hash with a 4-digit frame number.", SMTD_RepairFunctions.FixVRayMultipleHashes, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayConsecutiveHashes, #warn, "The Render Output Path contains consecutive hash characters. V-Ray replaces each hash with a 4-digit frame number. Job output will not appear in the Monitor.", SMTD_RepairFunctions.FixVRayConsecutiveHashes, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayHashInOutputDir, #warn, "The Render Output Directory contains one or more hash character(s). V-Ray will create frames in different directories.", SMTD_RepairFunctions.FixVRayHashInOutputDir, true),
		--#(SMTD_SanityCheckFunctions.CheckForMaxwellSingleFrame, #fail, "Maxwell is the renderer and the Render Time Output is set to a SINGLE FRAME!", SMTD_RepairFunctions.FixMaxwellSingleFrame, true),
		#(SMTD_SanityCheckFunctions.CheckForRenderingMultiFrame, #fix, "The Render Time Output is NOT set to single frame, and Remove Filename Padding is enabled!", SMTD_RepairFunctions.FixRenderingMultiFrame, true),
		#(SMTD_SanityCheckFunctions.CheckForKrakatoaCacheState, #fix, "The current Renderer is Krakatoa and Particle Cache is ON!", SMTD_RepairFunctions.FixKrakatoaCache, true),
		#(SMTD_SanityCheckFunctions.CheckForRestartRenderer, #warn, "Restart Renderer Between Frames is disabled and V-Ray or Brazil is the selected renderer.", SMTD_RepairFunctions.FixRestartRenderer, true),
		#(SMTD_SanityCheckFunctions.CheckForLockedViewport, #warn, "Viewport is currently locked, which can result in incorrect renders with Deadline.", SMTD_RepairFunctions.FixLockedViewport, true),
		#(SMTD_SanityCheckFunctions.CheckForTileRenderAndVrayVfb, #warn, "Tile Rendering is enabled and the V-Ray VFB is currently on.", SMTD_RepairFunctions.FixTileRenderAndVrayVfb, true),
		#(SMTD_SanityCheckFunctions.CheckForRenderElements, #fix, "One or more Render Element Save File Paths are EMPTY! (V-Ray? - Disable the Individual RE)", SMTD_RepairFunctions.FixRenderElements, true),
		#(SMTD_SanityCheckFunctions.CheckForOutputPathLength, #fail, "Render Output Path length exceeds 255 characters!", SMTD_RepairFunctions.FixOutputPathLength, true),
		#(SMTD_SanityCheckFunctions.CheckForREPathLength, #fail, "Render Elements Output Path length exceeds 255 characters!", SMTD_RepairFunctions.FixREPathLength, true),
		#(SMTD_SanityCheckFunctions.CheckForDuplicateREPaths, #fail, "Duplicate Render Elements saving to same File Found!", SMTD_RepairFunctions.FixDuplicateREPaths, true),
		#(SMTD_SanityCheckFunctions.CheckForObjectNames, #fail, "Scene Object(s) contain names > 255 characters!", SMTD_RepairFunctions.FixObjectNames, true),
		#(SMTD_SanityCheckFunctions.CheckForCorruptGroup, #fail, "Corrupt Group(s) detected in your Scene!", SMTD_RepairFunctions.FixCorruptGroup, true),
		#(SMTD_SanityCheckFunctions.CheckForActiveJigsawRegions, #fail, "Multi-Region Rendering Requested, But No Active Regions Found!", SMTD_RepairFunctions.doNothing, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayRawFileName, #fail, "V-Ray Save Raw Image File is Enabled, but Raw Image File Path is Empty!", SMTD_RepairFunctions.FixVRayRawFileName, true),
		#(SMTD_SanityCheckFunctions.CheckForVRaySplitFileName, #fail, "V-Ray Save Separate Render Channels is Enabled, but Separate Render Channels File Path is Empty!", SMTD_RepairFunctions.FixVRaySplitFileName, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayRegionRender, #fix, "V-Ray VFB - [Region render] button might need to be Disabled!", SMTD_RepairFunctions.FixVRayRegionRender, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayTrackMouse, #fail, "V-Ray VFB - [Track mouse while rendering] button should be Disabled!", SMTD_RepairFunctions.FixVRayTrackMouse, true),
		#(SMTD_SanityCheckFunctions.CheckForCameraMatchBmp, #fix, "Camera Match Background Image(s) in your Scene. Right-click to REMOVE these ref. bitmaps!", SMTD_RepairFunctions.FixCameraMatchBmp, true),
		#(SMTD_SanityCheckFunctions.CheckForTgaBitDepth, #fix, "Alpha Channel will NOT be stored if saving *.tga file @ 16/24bit depth! Select 32bit for Alpha!", SMTD_RepairFunctions.FixTgaBitDepth, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayVFBTA, #fail, "V-Ray RE:[Alpha,Reflection,Refraction] or [Save alpha] requires Draft Tile Assembler. NOT supported with TA.", SMTD_RepairFunctions.FixVRayVFBTA, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayValidIMAPFile, #fix, "V-Ray IMAP File (*.vrmap) set to 'From File' is missing/invalid file path!", SMTD_RepairFunctions.FixVRayValidIMAPFile, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayValidPhotonFile, #fix, "V-Ray Photon File (*.vrpmap) set to 'From File' is missing/invalid file path!", SMTD_RepairFunctions.FixVRayValidPhotonFile, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayValidLCFile, #fix, "V-Ray LC File (*.vrlmap) set to 'From File' is missing/invalid file path!", SMTD_RepairFunctions.FixVRayValidLCFile, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayValidCausticsFile, #fix, "V-Ray Caustics File (*.vrpmap) set to 'From File' is missing/invalid file path!", SMTD_RepairFunctions.FixVRayValidCausticsFile, true),
		#(SMTD_SanityCheckFunctions.CheckForActiveShade, #fix, "Current Scene is Rendering in Active Shade Mode. Are you sure you want to Submit?", SMTD_RepairFunctions.FixActiveShade, true),
		#(SMTD_SanityCheckFunctions.CheckForFumeFXSimProgress, #fix, "FumeFX Sim Job? - Disable Progress Timeout MUST be ENABLED!", SMTD_RepairFunctions.FixFumeFXSimProgress, true),
		#(SMTD_SanityCheckFunctions.CheckForFumeFXSimChunkSize, #fix, "FumeFX - Sim Jobs ONLY need to be a SINGLE FRAME (ALL Frames will be Simulated)", SMTD_RepairFunctions.FixFumeFXSimChunkSize, true),
		#(SMTD_SanityCheckFunctions.CheckForFumeFXSimMachineLimit, #fix, "FumeFX - Sim Jobs MUST have a MACHINE LIMIT = 1 (RUN only on 1 machine)", SMTD_RepairFunctions.FixFumeFXSimMachineLimit, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayDBROffLoadWorkstation, #fix, "V-Ray DBR off-load requires WORKSTATION mode to be ENABLED. [Use 3dsCmd Plugin] to avoid!", SMTD_RepairFunctions.FixVRayDBROffLoadWorkstation, true),
		#(SMTD_SanityCheckFunctions.CheckForDoubleDelimiterRenderOutput, #fix, "Render output file already has a delimiter in it!", SMTD_RepairFunctions.FixDoubleDelimiterRenderOutput, true),
		#(SMTD_SanityCheckFunctions.CheckForDoubleDelimiterVFBRaw, #fix, "V-Ray raw image file [DUPLICATE DOT] delimiter/user entered", SMTD_RepairFunctions.FixDoubleDelimiterVFBRaw, true),
		#(SMTD_SanityCheckFunctions.CheckForDoubleDelimiterVFBRawNative, #fix, "V-Ray raw image file [DUPLICATE DOT] fileName_addDot/user entered", SMTD_RepairFunctions.FixDoubleDelimiterVFBRaw, true),
		#(SMTD_SanityCheckFunctions.CheckForDoubleDelimiterSplitChannels, #fix, "V-Ray separate render channel files already have a delimiter in them!", SMTD_RepairFunctions.FixDoubleDelimiterSplitChannels, true),
		#(SMTD_SanityCheckFunctions.CheckForDoubleDelimiterRenderElement, #fix, "At least one render element output file already has a delimiter in it!", SMTD_RepairFunctions.FixDoubleDelimiterRenderElement, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayVFBValidRegion, #fail, "V-Ray VFB - Render Region is outside the bounds of the current render resolution!", SMTD_RepairFunctions.FixVRayVFBValidRegion, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayRenderMaskEmptySel, #fail, "V-Ray - AA Render mask selection is currently invalid, which will cause the render to hang!", SMTD_RepairFunctions.FixVRayRenderMaskEmptySel, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayVFB, #warn, "V-Ray VFB Enabled - 3ds Max 'Render Elements' will NOT save. This may be as intended?", SMTD_RepairFunctions.FixVRayVFB, true),
		#(SMTD_SanityCheckFunctions.CheckForVRayRegionRenderAndDenoiser, #fail, "VRayDenoiser is enabled and is NOT compatible with tile/region rendering. Only use one of these features.", SMTD_RepairFunctions.doNothing, true),
		#(SMTD_SanityCheckFunctions.CheckForUniqueREPaths, #fix, "Render Elements may overwrite each other as file paths may NOT be unique! Check!", SMTD_RepairFunctions.FixUniqueREPaths, true),
		#(SMTD_SanityCheckFunctions.CheckForValidGpuDevices, #fail, "'Select GPU Devices' syntax is invalid! Trailing 'commas' if present, should be removed.", SMTD_RepairFunctions.SuggestValidGpuSyntax, true),
		#(SMTD_SanityCheckFunctions.CheckForGpuConcurrentTasks, #fail, "If using 'Select GPU Devices', then 'Concurrent Tasks' must be set to 1!", SMTD_RepairFunctions.FixGpuConcurrentTasks, true),
		#(SMTD_SanityCheckFunctions.CheckForBadCameraNames, #fail, "At least one camera name has whitespace, newline, or tab at start/end of camera name.", SMTD_RepairFunctions.FixBadCameraNames, true),
		#(SMTD_SanityCheckFunctions.CheckForCoronaRegionRender, #fix, "Corona VFB - [Region render] button might need to be Disabled!", SMTD_RepairFunctions.FixCoronaRegionRender, true),
		#(SMTD_SanityCheckFunctions.CheckForRedshiftConcurrency, #fail, "Redshift does not support running multiple processes on the same GPU. Concurrent Tasks must be set to 1 or GPUs per task set to 1!", SMTD_RepairFunctions.FixGpuConcurrentTasks, true)
	)
)

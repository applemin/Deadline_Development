Sub SetAdditionalRenderOptions( passName, width, height, sampleMin, sampleMax, sampleFilter, sampleJitter, isRegionRender, outputPrefix, xMin, yMin, xMax, yMax, gpus )
	
	If width <> "" Then
		SetValue "Passes.List.*.ImageWidth", width
		SetValue "Passes.RenderOptions.ImageWidth", width
	End If
	
	If height <> "" Then
		SetValue "Passes.List.*.ImageHeight", height
		SetValue "Passes.RenderOptions.ImageHeight", height
	End If
	
	If sampleMin <> "" Then
		SetValue "Passes.List.*.mentalray.SamplesMin", sampleMin
	End If
		
	If sampleMax <> "" Then
		SetValue "Passes.List.*.mentalray.SamplesMax", sampleMax
	End If
	
	If sampleFilter <> "" Then
		sampleFilter = LCase( sampleFilter )
		If sampleFilter = "box" Then
			SetValue "Passes.List.*.mentalray.SamplesFilterType", 0
		ElseIf sampleFilter = "triangle" Then
			SetValue "Passes.List.*.mentalray.SamplesFilterType", 1
		ElseIf sampleFilter = "gauss" Then
			SetValue "Passes.List.*.mentalray.SamplesFilterType", 2
		ElseIf sampleFilter = "mitchell" Then
			SetValue "Passes.List.*.mentalray.SamplesFilterType", 3
		ElseIf sampleFilter = "lanczos" Then
			SetValue "Passes.List.*.mentalray.SamplesFilterType", 4
		End If	
	End If
		
	If sampleJitter <> "" Then
		SetValue "Passes.List.*.mentalray.SamplesJitter", sampleJitter
	End If
	
	If outputPrefix <> "" Then
		Set fileSystem = CreateObject( "Scripting.FileSystemObject" )
		
		If passName <> "" Then
			Set pass = GetValue( "Passes." & passName )
			
			For Each frameBuffer In pass.FrameBuffers
				frameBufferPath = GetValue( "Passes." & passName & "." & frameBuffer.Name & ".Filename" )
				frameBufferFilename = fileSystem.GetFileName( frameBufferPath )
				frameBufferPath = fileSystem.GetParentFolderName( frameBufferPath )
				SetValue "Passes." & passName & "." & frameBuffer.Name & ".Filename", fileSystem.BuildPath( frameBufferPath, outputPrefix & frameBufferFilename )
			Next
		Else
			mainPath = GetValue( "Passes.List.*.Main.Filename" )
			mainFilename = fileSystem.GetFileName( mainPath )
			mainPath = fileSystem.GetParentFolderName( mainPath )
			SetValue "Passes.List.*.Main.Filename", fileSystem.BuildPath( mainPath, outputPrefix & mainFilename )
		End If
	End If
	
	If xMin <> "" And yMin <> "" And xMax <> "" And yMax <> "" Then
		SetValue "Passes.List.*.CropWindowEnabled", True
		SetValue "Passes.List.*.CropWindowOffsetX", xMin
		SetValue "Passes.List.*.CropWindowHeight", yMin
		SetValue "Passes.List.*.CropWindowWidth", xMax
		SetValue "Passes.List.*.CropWindowOffsetY", yMax
	End If
	
	If gpus <> "" Then
		gpuArray = Split( gpus, "," )
		Redshift_SelectCudaDevices gpuArray
	End If
End Sub

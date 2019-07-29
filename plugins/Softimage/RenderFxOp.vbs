Function RenderFxOpMain( sceneFilename, fxTreeOutputNode, startFrame, endFrame, stepFrame, frameOffset, outputFilename )
	' Open the scene file
	OpenScene sceneFilename, False, False
	
	' Set the frame settings
	SetValue fxTreeOutputNode & ".StartFrame", startFrame
	SetValue fxTreeOutputNode & ".EndFrame", endFrame
	SetValue fxTreeOutputNode & ".Step", stepFrame
	SetValue fxTreeOutputNode & ".FrameOffset", frameOffset
	
	' Override the output filename if it is not empty
	If outputFilename <> "" Then
		SetValue fxTreeOutputNode & ".FileName", outputFilename
	End If
	
	' Render the fx tree output node
	RenderFxOp fxTreeOutputNode, False
	
	' Set the return code
	RenderFxOpMain = 0
End Function

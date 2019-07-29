' The startup script used in the SoftimageBatch Plugin. This script uses files to communicate with Deadline.
Sub RenderMain( commandFilename, ackFilename )
	LogMessage "Command Filename: " & commandFilename
	LogMessage "Ack Filename: " & ackFilename
	
	' Tell Deadline that we're ready to go.
	SendResponse ackFilename, "Ready"
	
	' The main loop waits for commands from Deadline and executes them.
	finished = False
	While Not finished
		command = WaitForCommand( commandFilename )
		
		' The Quit command - time to exit!
		If command = "Quit" Then
			LogMessage "Quitting Softimage"
			SendResponse ackFilename, "Exiting"
			finished = True
		
		' The general execution command - execute whichever function we're told to.
		ElseIf InStr( command, "ExecuteCommand=" ) <> 0 Then
			equalIndex = InStr( command, "=" )
			header = Right(command,Len(command)-equalIndex)
			
			LogMessage "Executing command: " + header
			
			openBraceIndex = InStr( header,"(" )
			functionName = Left( header, openBraceIndex - 1 )
			
			arguments = Right( header, Len(header) - openBraceIndex )
			closeBraceIndex = InStrRev( arguments, ")" )
			arguments = Left( arguments, Len(arguments) - (Len(arguments) - closeBraceIndex) - 1 )
			argumentList = Split( arguments, "," )

			' Don't try to replace any "(" or ")" chars which may be present in XSI filename.
			If functionName <> "OpenScene" Then
				For i = 0 To UBound( argumentList )
					argumentList(i) = ApplyCast( argumentList( i ) )
				Next
			End If
			
			result = ExecuteCommand( functionName, argumentList )
			If functionName = "GetValue" Then
				SendResponse ackFilename, result
			Else
				SendResponse ackFilename, "Ready"
			End If
		
		' The workgroup command - change the workgroup.
		Elseif InStr( command, "Workgroup=" ) <> 0 Then
			equalIndex = InStr( command, "=" )
			workgroup = Right( command, Len(command) - equalIndex )
			
			LogMessage "Changing Workgroup to " & workgroup
			
			AddWorkgroup workgroup
			ActivateWorkgroup workgroup
			
			SendResponse ackFilename, "Ready"
		
		' Unknown command - log a message that will cause Deadline to error out.
		Else
			LogMessage "ERROR : UNKNOWN STATEMENT: " & command
			SendResponse ackFilename, "ERROR : UNKNOWN STATEMENT: " & command
		End If
	Wend
End Sub

' Sends a response file to Deadline.
Sub SendResponse( ackFilename, response )
	Set fileSystem = CreateObject( "Scripting.FileSystemObject" )
	Set file = fileSystem.CreateTextFile( ackFilename, True )
	file.WriteLine response
	file.Close
End Sub

' Waits for a command file from Deadline.
Function WaitForCommand( commandFilename )
	Set fileSystem = CreateObject( "Scripting.FileSystemObject" )
	
	commandRead = False
	While Not commandRead
		While Not fileSystem.FileExists( commandFilename )
		Wend
		
		fileOpen = False
		
		On Error Resume Next
		Set file = fileSystem.OpenTextFile( commandFilename )
		If err = 0 Then
			fileOpen = True
		End If
		On Error GoTo 0
		
		If fileOpen Then
			On Error Resume Next
			command = file.ReadLine
			If err = 0 Then
				commandRead = True
			End If
			On Error GoTo 0
			
			file.Close
		End If
	Wend
	
	On Error Resume Next
	While fileSystem.FileExists( commandFilename )
		fileSystem.DeleteFile( commandFilename )
	Wend
	On Error GoTo 0
	
	WaitForCommand = command
End Function

' Applies a cast to the argument if the argument is in one of the forms:
'   int(arg)
'   float(arg)
'   str(arg)
'   bool(arg)
'   array(arg)
Function ApplyCast( arg )
	openBraceIndex = InStr( arg, "(" )
	closeBraceIndex = InStrRev( arg, ")" )
	
	If closeBraceIndex <> 0 and openBraceIndex <> 0 Then
		castType = Left( arg, openBraceIndex - 1 )
		newArg = Right( arg, Len(arg) - openBraceIndex )
		closeBraceIndex = InStrRev( newArg, ")" )
		newArg = Left( newArg, Len(arg) - (Len(arg) - closeBraceIndex) - 1 )
		
		if castType = "int" Then
			newArg = Cint( newArg )
		elseif castType = "float" Then
			newArg = Cdbl( newArg )
		elseif castType = "str" Then
			newArg = Cstr( newArg )
		elseif castType = "bool" Then
			newArg = Cbool( newArg )
		elseif castType = "array" Then
			newArg = Split( newArg, ";" )
		End If
		
		ApplyCast = newArg
	Else
		ApplyCast = arg
	End If
End Function
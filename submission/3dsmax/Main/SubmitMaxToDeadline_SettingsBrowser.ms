global SubmtMaxToDeadline_SettingsBrowser
try(destroyDialog SubmtMaxToDeadline_SettingsBrowser)catch()
rollout SubmtMaxToDeadline_SettingsBrowser "SMTD: Defaults and Sticky Settings Browser"
(
	dotNetControl dnc_propertiesList "ListView" width:1194 height:594 align:#center offset:[0,-3]  
	
	fn getGlobalDefault theCategory theKey executeIt =
	(
		local theDefaultFile = SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_Defaults.ini"
		local theKeys = getIniSetting theDefaultFile theCategory 
		local result = undefined 
		if findItem theKeys theKey > 0 do 
			result = getIniSetting theDefaultFile theCategory theKey  
		result  
	)
	
	fn IsSettingSticky theCategory theKey =
	( 
		local theStickyFile = SMTDPaths.MainSubmissionDir + "\\SubmitMaxToDeadline_StickySettings.ini"  
		local theLocalStickyFile = SMTDPaths.SettingsDir + "\\SubmitMaxToDeadline_StickySettings.ini"  
		local isSticky = #sticky 
		local theValue = (getINISetting theStickyFile theCategory theKey) 
		if theValue != "" do if not matchPattern theValue pattern:"false" then isSticky = #global else isSticky = #notstickyglobal
		local theValue = (getINISetting theLocalStickyFile theCategory theKey)
		if theValue != "" do if not matchPattern theValue pattern:"false" then isSticky = #local else isSticky = #notstickylocal
		isSticky 
	)	
	
	fn updateList =
	(
		local theSettingsList = SMTDFunctions.getSettingsList()
		local lv = dnc_propertiesList
		local layout_def = #(
			#("INI Category",100, "This is the [Category] name used in the repository files 'SubmitMaxToDeadline_Defaults.ini' and 'SubmitMaxToDeadline_StickySettings.ini'"), 
			#("Property",150, "This is the Property= (key) name used in the repository files 'SubmitMaxToDeadline_Defaults.ini' and 'SubmitMaxToDeadline_StickySettings.ini'"), 
			#("Stickiness",100, "The stickiness of a property can be controlled by the Global 'SubmitMaxToDeadline_StickySettings.ini' file, by a local 'SubmitMaxToDeadline_StickySettings.ini' file, or it could be hard-coded in the SMTD script itself.\n\nThe value in this column takes into account all these factors to show the 'sticky' behavior of the Property."), 
			#("Factory Default", 120,"This is the hard-coded value given to the property by the SMTD script.\n\nIt will only persist of the Property is not sticky and no Global Default is specified."),
			#("Global Default",120,"This is the Global Default value specified for the Property via the 'SubmitMaxToDeadline_Defaults.ini' Repository file.\n\nIt will be used if the property is set to not sticky."), 
			#("Local Sticky Value",120,"This is the value saved to the local disk last time the property was changed via the UI.\n\nIt will be used if the property is set to sticky."), 
			#("Scene File Value", 120, "This is the value stored inside the MAX file. It is the last value set when the scene was saved. If shown in (brackets), the value is excluded at loading time via the 'SubmitMaxToDeadline_ExcludeFromSceneStorage.ini' repository file."),
			#("Final Value",120,"This is the actual value SMTD will use after taking into account the Stickiness settings and the various default values listed to the left."),  
			#("UI Rollout Name",200,"This is the name of the UI rollout the property is exposed in."), 
			#("UI Control Name / Description",330,"This is the name of the UI control responsible for setting the property, or a description of the property if not exposed to the UI.") 
		)
		
		lv.Clear()
		lv.backColor = (dotNetClass "System.Drawing.Color").fromARGB 221 221 225
		lv.View = (dotNetClass "System.Windows.Forms.View").Details
		lv.gridLines = true 
		lv.fullRowSelect = true
		lv.checkboxes = false
		lv.hideSelection = false		
		for i in layout_def do lv.Columns.add i[1] i[2]
			
		local theSceneData = getAppData trackViewNodes 20170222 
		if theSceneData != undefined then 
			theSceneData = try(execute theSceneData)catch(#())
		else
			theSceneData = #()
		local theSceneDataNames = for i in theSceneData collect i[1]
			
		local theRange = #()
		for i in theSettingsList do
		(
			local li = dotNetObject "System.Windows.Forms.ListViewItem" i[1]
			local subLi = li.SubItems.add i[2] 
			local theFactoryValue = try((getProperty ::SMTDSettingsFactory i[3]))catch("--")
			local theValue = try((getProperty ::SMTDSettings i[3]))catch("--")
			local theDefault = getGlobalDefault i[1] i[2] i[4]
			if theDefault == undefined do theDefault = "<no value>"
				
			local localStickyValue = "<no value>"
			if findItem (getIniSetting SMTDPaths.IniFile i[1]) i[2] > 0 do localStickyValue = getIniSetting SMTDPaths.IniFile i[1] i[2]
			local theSceneValue = "--" 
			local theSceneValueIndex = findItem theSceneDataNames i[3]
			if theSceneValueIndex > 0 do theSceneValue = theSceneData[theSceneValueIndex][2]
			if findItem ::SMTDSaveInSceneExclusionList i[3] > 0 do theSceneValue = "("+theSceneValue as string+")"
			local redColor = (dotNetClass "System.Drawing.Color").fromARGB 255 221 221
			local greenColor = (dotNetClass "System.Drawing.Color").fromARGB 221 255 221
			local greenColor2 = (dotNetClass "System.Drawing.Color").fromARGB 231 255 211
			local greenColor3 = (dotNetClass "System.Drawing.Color").fromARGB 211 255 231
			
			local blueColor = (dotNetClass "System.Drawing.Color").fromARGB 221 221 255 
			local blueColor2 = (dotNetClass "System.Drawing.Color").fromARGB 211 231 255 
			
			local yellowColor = (dotNetClass "System.Drawing.Color").fromARGB 255 255 221
				
			local Sticky = "Not Sticky"
			local BGColor = blueColor
			
			if i[7] != false then
			(
				case IsSettingSticky i[1] i[2] of
				(
					default: (
						Sticky = "Sticky by Default"
						BGColor = greenColor2
					)
					#global: (
						Sticky = "Sticky - Global INI"
						BGColor = greenColor
					)
					#local: (
						Sticky = "Sticky - Local INI"
						BGColor = greenColor3
					)
					#notstickyglobal: (
						Sticky = "Not Sticky - Global INI"
						BGColor = blueColor
					)
					#notstickylocal: (
						Sticky = "Not Sticky - Local INI"
						BGColor = blueColor2
					)
				)
			)
			else if i[8] == true then 
			(
				Sticky = "Sticky - Hard-Coded" 
				BGColor = yellowColor
			)
			else 
			(
				Sticky = "Not Sticky - Hard-Coded"
				BGColor = redColor
			)
			li.backColor = BGColor
			local subLi = li.SubItems.add (Sticky) 
			local subLi = li.SubItems.add (theFactoryValue as string)
			local subLi = li.SubItems.add (theDefault as string)
			local subLi = li.SubItems.add (localStickyValue as string)
			local subLi = li.SubItems.add (theSceneValue as string)
			local subLi = li.SubItems.add (theValue as string)
			local subLi = li.SubItems.add i[5]
			local subLi = li.SubItems.add i[6]
			append theRange li
		)
		lv.Items.AddRange theRange 
		
		local autoRes = dotNetClass "System.Windows.Forms.ColumnHeaderAutoResizeStyle"
		lv.AutoResizeColumns autoRes.ColumnContent			
	)
	
	
	fn CompileComparer = 
	(
		local source = ""
		source+="using System;\n"
		source+="using System.Windows.Forms;\n"
		source+="using System.Collections;\n"
		source+="public class ListViewItemComparerSMTDBrowser : IComparer\n"
		source+="{\n"
		source+="  private int col;\n"
		source+="  private int sort;\n"
		source+="  public ListViewItemComparerSMTDBrowser()\n"
		source+="  {\n"
		source+="      col = 0;\n"
		source+="      sort = 1;\n"
		source+="  }\n"
		source+="  public ListViewItemComparerSMTDBrowser(int column, int sorting)\n"
		source+="  {\n"
		source+="    sort = sorting;\n"
		source+="    col = column;\n"
		source+="  }\n"
		source+="  public int Compare(object x, object y)\n"
		source+="  {\n"
		source+="   return ((String.Compare(((ListViewItem)x).SubItems[col].Text, ((ListViewItem)y).SubItems[col].Text))*sort);\n"
		source+="  }\n"
		source+="}\n"	
		csharpProvider = dotnetobject "Microsoft.CSharp.CSharpCodeProvider"
		compilerParams = dotnetobject "System.CodeDom.Compiler.CompilerParameters"
		compilerParams.ReferencedAssemblies.AddRange #("System.dll", "System.Windows.Forms.dll")
		compilerParams.GenerateInMemory = true
		compilerResults = csharpProvider.CompileAssemblyFromSource compilerParams #(source)
		if compilerResults.Errors.Count == 0 then 
		(
			compilerResults.CompiledAssembly
		)
		else
		(
			--showProperties compilerResults.CompiledAssembly.Errors
			for i = 0 to compilerResults.Errors.Count-1 do
				format "%\n" compilerResults.Errors.Item[i].ErrorText
			false
		)
	)

	local lastColumnClicked = -1
	local sortDirection = 1
	local theAssembly = CompileComparer()	
	
	on dnc_propertiesList ColumnClick args do
	(
		if lastColumnClicked == args.Column then 
			sortDirection =  sortDirection * -1
		else 
			lastColumnClicked = args.Column 
		dnc_propertiesList.ListViewItemSorter = dotNetObject "ListViewItemComparerSMTDBrowser" args.Column sortDirection
	)
	
	
	fn resizeDialog val =
	(
		dnc_propertiesList.width = val.x-6
		dnc_propertiesList.height = val.y-6
	)	
	
	on SubmtMaxToDeadline_SettingsBrowser resized val do
	(
		resizeDialog val
	)	
	
	on SubmtMaxToDeadline_SettingsBrowser open do
	(
		updateList()
	)
)
createDialog SubmtMaxToDeadline_SettingsBrowser 1200 600 style:#(#style_titlebar, #style_border, #style_sysmenu, #style_minimizebox, #style_resizing, #style_maximizebox  ) --menu:MainMenu
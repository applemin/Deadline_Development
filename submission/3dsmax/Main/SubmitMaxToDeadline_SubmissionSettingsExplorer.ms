global SubmtMaxToDeadline_SubmissionSettingsExplorer
try(destroyDialog SubmtMaxToDeadline_SubmissionSettingsExplorer)catch()
rollout SubmtMaxToDeadline_SubmissionSettingsExplorer "SMTD: Submission Settings Explorer"
(
	local theContent = #()
	local theFilters = #()
	
	label lbl_filter "Filter By Key:"  pos:[10,5]
	dropdownlist ddl_filter width:200 pos:[80,3]
	
	edittext edt_filter "Filter By Value:" pos:[300,5] fieldwidth:200
	
	label lbl_source "Submission File:" pos:[600,6]
	dropdownlist ddl_source items:#("Job Info File", "Plugin Info File") width:100 pos:[680,3]
	button btn_update "UPDATE!" width:100 pos:[800,3]

	dotNetControl dnc_List "ListView" width:1194 height:570 align:#center offset:[0,-3]  
	
	fn updateList =
	(
		local lv = dnc_List
		local layout_def = #(
			#("Key",100, ""), 
			#("Value",600, "")
		)
		
		lv.Clear()
		lv.backColor =if ddl_source.selection == 1 then (dotNetClass "System.Drawing.Color").fromARGB 221 221 235 else (dotNetClass "System.Drawing.Color").fromARGB 221 235 221 
		lv.View = (dotNetClass "System.Windows.Forms.View").Details
		lv.gridLines = true 
		lv.fullRowSelect = true
		lv.checkboxes = false
		lv.hideSelection = false		
		for i in layout_def do lv.Columns.add i[1] i[2]
	)
	
	local foreColor = (dotNetClass "System.Drawing.Color").fromARGB 0 0 0
	local redColor = (dotNetClass "System.Drawing.Color").fromARGB 128 0 0
	local blueBGColor = (dotNetClass "System.Drawing.Color").fromARGB 200 200 255
	local greenBGColor = (dotNetClass "System.Drawing.Color").fromARGB 200 255 200 
	
	fn populateListView =
	(
		local lv = dnc_List
		lv.Items.Clear()
		local theRange = #()
		local thePattern = theFilters[ddl_filter.selection][2]
		bgColor =if ddl_source.selection == 1 then (dotNetClass "System.Drawing.Color").fromARGB 221 221 235 else (dotNetClass "System.Drawing.Color").fromARGB 221 235 221 
		for i in theContent do
		(
			local theKVP = filterString i "=" splitEmptyTokens:true
			local theKey = theKVP[1]
			local theValue = theKVP[theKVP.count]
			if theKVP.count > 2 do for j = 2 to theKVP.count-1 do theKey+= "="+theKVP[j]
			if theKVP.count > 0 and matchPattern theKey pattern:thePattern and ((edt_filter.text.count == 0 AND theValue == "") or matchPattern theValue pattern:("*"+edt_filter.text+"*")) do
			(
				local li = dotNetObject "System.Windows.Forms.ListViewItem" theKey
				case ddl_source.selection of
				(
					1:
					(
						li.backcolor = if matchPattern theKey pattern:theFilters[2][2] then blueBGColor 					
							else if matchPattern theKey pattern:theFilters[3][2] then greenBGColor
							else bgColor 
					)
					--default: (li.backcolor = blackColor)
				)
				
				local subLi = li.SubItems.add (if theValue == "" then "<empty string>" else theValue)
				if theValue == "" then li.forecolor = redColor else foreColor
				append theRange li
			)
		)
		lv.Items.AddRange theRange 
		local autoRes = dotNetClass "System.Windows.Forms.ColumnHeaderAutoResizeStyle"
		lv.AutoResizeColumns autoRes.ColumnContent			
	)
	
	fn updateKeyFilter =
	(
		theFilters = if ddl_source.selection == 1 then 
			#(#("ALL", "*"),#("OutputFilename","OutputFilename*"), #("ExtraInfo","ExtraInfo*"))
		else
			#(#("ALL", "*"))
				
		for i in theContent do 
		(
			local theKVP = filterString i "="
			append theFilters #(theKVP[1], theKVP[1]+"*")
		)
		ddl_filter.items = for i in theFilters collect i[1]
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
	
	on dnc_List ColumnClick args do
	(
		if lastColumnClicked == args.Column then 
			sortDirection =  sortDirection * -1
		else 
			lastColumnClicked = args.Column 
		dnc_List.ListViewItemSorter = dotNetObject "ListViewItemComparerSMTDBrowser" args.Column sortDirection
	)
	
	on ddl_source selected itm do 
	(
		theContent = SMTDFunctions.ExploreSubmissionInfoFiles source:(#(#job,#plugin)[itm])
		updateKeyFilter()
		updateList()
		populateListView()
	)
	on btn_update pressed do
	(
		theContent = SMTDFunctions.ExploreSubmissionInfoFiles source:(if ddl_source.selection == 1 then #job else #plugin)
		populateListView()
	)	

	on ddl_filter selected itm do
	(
		populateListView()
	)	
	
	on edt_filter changed txt do
	(
		populateListView()
	)
	
	fn resizeDialog val =
	(
		dnc_List.width = val.x-6
		dnc_List.height = val.y-30
		btn_update.pos = [val.x-104,3]
	)	
	
	on SubmtMaxToDeadline_SubmissionSettingsExplorer resized val do
	(
		resizeDialog val
	)	
	
	on SubmtMaxToDeadline_SubmissionSettingsExplorer open do
	(
		theContent = SMTDFunctions.ExploreSubmissionInfoFiles source:(if ddl_source.selection == 1 then #job else #plugin)
		resizeDialog [SubmtMaxToDeadline_SubmissionSettingsExplorer.width, SubmtMaxToDeadline_SubmissionSettingsExplorer.height]
		updateKeyFilter()
		updateList()
		populateListView()
	)
)
createDialog SubmtMaxToDeadline_SubmissionSettingsExplorer 1200 600 style:#(#style_titlebar, #style_border, #style_sysmenu, #style_minimizebox, #style_resizing, #style_maximizebox  ) --menu:MainMenu
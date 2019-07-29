global SubmitMaxToDeadline_PathingExplorer
try(destroyDialog SubmitMaxToDeadline_PathingExplorer)catch()
rollout SubmitMaxToDeadline_PathingExplorer "SMTD: Preview Output Paths"
(
	local theContent = #()
	
	label lbl_maxPathLength "Max. Path Length:" pos:[600,6]
	dropdownlist ddl_maxPathLength items:#("260", "256", "240","150") width:60 pos:[690,3]
	
	button btn_update "UPDATE!" width:200 pos:[10,3]

	dotNetControl dnc_List "ListView" width:1194 height:250 align:#center offset:[0,-3]  
	dotNetControl dnc_Report "ListView" width:1194 height:90 align:#center offset:[0,-3]  
	

	local foreColor = (dotNetClass "System.Drawing.Color").fromARGB 0 0 0
	local backColor = (dotNetClass "System.Drawing.Color").fromARGB 221 221 235
	local backColor2 = (dotNetClass "System.Drawing.Color").fromARGB 221 235 221 
	local redColor = (dotNetClass "System.Drawing.Color").fromARGB 128 0 0
	local greenColor = (dotNetClass "System.Drawing.Color").fromARGB 0 90 0
	local blueBGColor = (dotNetClass "System.Drawing.Color").fromARGB 200 200 255
	local greenBGColor = (dotNetClass "System.Drawing.Color").fromARGB 200 255 200 
	
	fn resizeDialog val =
	(
		if val.y < 200 do val.y = 200
		SubmitMaxToDeadline_PathingExplorer.width = val.x
		SubmitMaxToDeadline_PathingExplorer.height = val.y
		
		dnc_List.width = val.x-6
		dnc_List.height = val.y-120
		
		dnc_Report.width = val.x-6
		dnc_Report.pos.y = val.y-90
		
		lbl_maxPathLength.pos = [val.x-160,6]
		ddl_maxPathLength.pos = [val.x-62,3]
		--btn_update.pos = [val.x-104,3]
	)		
	
	fn generateReport =
	(
		local report = #()
		local theLine = ""
		theLine+= "The 3ds Max Render Setup Dialog > Render Output > SAVE FILE checkbox is " + (if rendSaveFile == true then "checked." else "UNCHECKED!")
		theLine+= " The OUTPUT FILENAME was "+ (if rendOutputFilename != "" then "set." else "NOT SET!")
		append report theLine
		theLine = ""
		
		append report ("Current renderer is "+ (classof renderers.current) as string + ".")
		local rendererID = SMTDFunctions.getRendererIdString()
		local theRenderer = renderers.current
		renderSceneDialog.commit()
		if rendererID == "vray" do
		(
			if theRenderer.output_splitgbuffer AND theRenderer.output_useram do
			(
				append report "V-Ray is set to use MEMORY FRAME BUFFER, and SEPARATE RENDER CHANNELS are enabled!"
				if (isProperty theRenderer #output_separateFolders and theRenderer.output_separateFolders == true) then
				(
					append report "The V-Ray VFB SEPARATE FOLDERS option is checked. Render Channels / Render Elements will respect the V-Ray Settings and ignore the SMTD Pathing rules!"
				)
				else
				(
					if SMTDSettings.LocalRendering == false do
					(
						append report "LOCAL RENDERING is turned OFF in SMTD, and V-Ray controls the saving of Separate Render Channels. Some SMTD Pathing features will be ignored!"
					)
				)
			)
		)
		local theRange = #()
		lv = dnc_Report
		lv.Items.Clear()
		for i in report do
		(
			local li = dotNetObject "System.Windows.Forms.ListViewItem" i
			append theRange li
		)
		lv.Items.AddRange theRange 
		local autoRes = dotNetClass "System.Windows.Forms.ColumnHeaderAutoResizeStyle"
		lv.AutoResizeColumns autoRes.ColumnContent		
	)
	
	fn updateList which:#paths =
	(
		case which of
		(
			default: 
			(
				local lv = dnc_List
				local layout_def = #(
					#("Path",600),
					#("Filename",200),
					#("Length",50)
				)
				lv.HeaderStyle = lv.HeaderStyle.Clickable
				lv.backColor = backColor --(dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r (SMTD_ColorPalette.maxBgColor.g) (SMTD_ColorPalette.maxBgColor.b)
				lv.gridLines = true 
			)
			#report: 
			(
				local lv = dnc_Report
				local layout_def = #(
					#("Message",1000)
				)
				lv.HeaderStyle = lv.HeaderStyle.None
				lv.backColor = backColor2 --(dotNetClass "System.Drawing.Color").fromARGB SMTD_ColorPalette.maxBgColor.r (SMTD_ColorPalette.maxBgColor.g) (SMTD_ColorPalette.maxBgColor.b)
				lv.gridLines = false
			)			
		)
		lv.Clear()
		lv.View = (dotNetClass "System.Windows.Forms.View").Details
		lv.fullRowSelect = true
		lv.checkboxes = false
		lv.hideSelection = false
		--lv.showColumns = true
		--showProperties lv
		for i in layout_def do lv.Columns.add i[1] i[2]
	)
	
	fn populateListView =
	(
		local lv = dnc_List
		local theRange = #()
		theContent = SMTDFunctions.ExploreSubmissionInfoFiles source:#job
		lv.Items.Clear()
		local maxPathLength = #(260,256,250,150)[ddl_maxPathLength.selection]
		for i in theContent where MatchPattern i pattern:"OutputFilename*=*" do
		(
			local theKVP = filterString i "=" splitEmptyTokens:true
			local theKey = theKVP[1]
			local theValue = theKVP[2]
			if theValue != "" do
			(
				local li = dotNetObject "System.Windows.Forms.ListViewItem" (getFileNamePath theValue)
				local subLi = li.SubItems.add (filenamefrompath theValue)
				li.forecolor = if theValue.count > maxPathLength then redColor else greenColor
				local subLi = li.SubItems.add  ("   "+(theValue.count as string)+"   ")
				append theRange li
			)
		)
		lv.Items.AddRange theRange 
		local autoRes = dotNetClass "System.Windows.Forms.ColumnHeaderAutoResizeStyle"
		lv.AutoResizeColumns autoRes.ColumnContent		
		columnsWidth = 10
		for i = 0 to lv.Columns.count-1 do columnsWidth+= lv.Columns.Item[i].Width
		if columnsWidth > sysinfo.DesktopSize.x do columnsWidth = sysinfo.DesktopSize.x
		if columnsWidth < 800 do columnsWidth = 800			
		resizeDialog [amax #(SubmitMaxToDeadline_PathingExplorer.width, columnsWidth), 120+57+dnc_List.items.count*19]
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
	
	on ddl_maxPathLength selected itm do 
	(
		populateListView()
	)
	on btn_update pressed do
	(
		populateListView()
		generateReport()
	)	

	on SubmitMaxToDeadline_PathingExplorer resized val do
	(
		resizeDialog val
	)	
	
	on SubmitMaxToDeadline_PathingExplorer open do
	(
		updateList which:#paths
		updateList which:#report
		populateListView()
		generateReport()
	)
)
createDialog SubmitMaxToDeadline_PathingExplorer 1200 300 style:#(#style_titlebar, #style_border, #style_sysmenu, #style_minimizebox, #style_resizing, #style_maximizebox  ) --menu:MainMenu
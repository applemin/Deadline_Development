(
	local theMainMenu = menuMan.getMainMenuBar()
	local theDeadlineMenu = menuMan.findMenu "Deadline"
	
	if theDeadlineMenu != undefined do
	(
		menuMan.unRegisterMenu theDeadlineMenu
		menuMan.updateMenuBar() 
	)	
	theDeadlineMenu = menuMan.createMenu "Deadline"

	local theMenuDefinitionArray = #(
		#(#menuitem,"SubmitMaxToDeadline","Deadline","Submit Max To Deadline"),
		#(#separator),
		#(#menuitem,"Cmd2Deadline","Deadline","Submit Max To Deadline (3dsCmd)"),
		#(#menuitem,"MaxVRayDBR2Deadline","Deadline","Submit VRay DBR To Deadline"),
		#(#menuitem,"MaxCoronaDR2Deadline","Deadline","Submit Corona DR To Deadline")
	)

	for aDef in theMenuDefinitionArray do
	(
		case aDef[1] of
		(
			default:
			(
				try
				(
					theAction = menuMan.createActionItem aDef[2] aDef[3]
					theAction.setTitle aDef[4]
					theAction.setUseCustomTitle true
					theDeadlineMenu.addItem theAction -1
				)catch()
			)
			#separator: 
			(
				try
				(
					theAction = menuMan.createSeparatorItem()
					theDeadlineMenu.addItem theAction -1
				)catch()
			)
		)--end case
	)--end aDef loop
	
	theSubMenu = menuMan.createSubMenuItem "Deadline" theDeadlineMenu
	theMainMenu.addItem theSubMenu -1
	menuMan.updateMenuBar() 
)--end script
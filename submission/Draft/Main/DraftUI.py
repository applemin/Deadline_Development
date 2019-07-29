from __future__ import print_function
import sys
import os
import re

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from System.IO import File
from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Main Function Called By Deadline for Draft standalone (for debugging)
########################################################################
def __main__( *args ):
    global scriptDialog
    parentAppName = ""
    addPMComponents = False
    fromDraftSubmitter = False
    firstFrameFile = None
    
    #Parse out the args (if any)
    for arg in args:
        argLower = str(arg).lower()
        if argLower == "addpmcomponents":
            addPMComponents = True
        elif argLower  == "fromdraftsubmitter":
            fromDraftSubmitter = True
        elif argLower == "parentappname":
            parentAppName = arg
        elif argLower == "firstframefile":
            firstFrameFile = arg

    scriptDialog = DraftDialog( parentAppName=parentAppName, addPMComponents=addPMComponents, fromDraftSubmitter=fromDraftSubmitter, firstFrameFile=firstFrameFile )

    # Add control buttons
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer", 0, 0 )
    okButton = scriptDialog.AddControlToGrid( "OkButton", "ButtonControl", "OK", 0, 1, expand=False )
    okButton.clicked.connect( OKButtonClicked )
    cancelButton = scriptDialog.AddControlToGrid( "CancelButton", "ButtonControl", "Cancel", 0, 2, expand=False )
    cancelButton.clicked.connect( CancelButtonClicked )
    scriptDialog.EndGrid()

    scriptDialog.ShowDialog( True )

def OKButtonClicked():
    global scriptDialog

    if not scriptDialog.CheckDraftSanity():
        return

    settingsDict = scriptDialog.GetSettingsDictionary()
    
    for key in settingsDict.keys():
        ClientUtils.LogText( "%s=%s" % ( key, settingsDict[key] ) )

    super( DraftDialog, scriptDialog ).accept()

def CancelButtonClicked():
    super( DraftDialog, scriptDialog ).reject()

########################################################################
## Subclass of DeadlineControlDialog for Draft UI
########################################################################
class DraftDialog( DeadlineScriptDialog ):
    def __init__( self, parentAppName="", addPMComponents=False, fromDraftSubmitter=False, parent=None, firstFrameFile="" ):
        super( DraftDialog, self ).__init__( parent )

        self.SetTitle( "Draft" )

        self.parentAppName = parentAppName
        self.fromDraftSubmitter = fromDraftSubmitter
        self.addPMComponents = addPMComponents
        self.firstFrameFile = firstFrameFile
        self.outputPaddingSize = 0
        
        if self.fromDraftSubmitter:
            self.SetIcon( self.GetIcon( 'DraftPlugin' ) )

        self.Formats = []
        self.Resolutions = []
        self.FrameRates = []
        self.Luts = []
        self.Restrictions = []

        self.FormatsDict = {}
        self.ResolutionsDict = {}
        self.CodecsDict = {}
        self.LutsDict = {}
        self.RestrictionsDict = {}

        self.stickySettings = ()
        self.settingsDict = {}
        
        # Populate Draft option lists for drop downs
        self.ReadInDraftOptions()
        
        dialogWidth = 485
        controlHeight = -1 #20

        self.AddRow()
        self.AddControl( "Separator", "SeparatorControl", "Draft Fields", dialogWidth, controlHeight )
        self.EndRow()

        self.AddGrid()
        # Add Draft Submission box if necessary
        if not self.fromDraftSubmitter:
            draftSubmitBox = self.AddSelectionControlToGrid( "DraftSubmitBox", "CheckBoxControl", False, "Submit Draft Job On Completion", 0, 0, "If enabled, Deadline will automatically submit a Draft job after this job completes." )
            draftSubmitBox.ValueModified.connect( self.UpdateDraft )
        # Add project management upload results if necessary
        self.EndGrid()

        # Add Quick Draft
        self.AddGrid()
        self.draftQuickRadio = self.AddRadioControlToGrid( "DraftQuickRadio", "RadioControl", True, "Quick", "RadioGroup", 0, 0, "If selected, Draft will generate an image or a movie based on the options specified below." )
        self.draftQuickRadio.ValueModified.connect(self.UpdateDraft)
        self.EndGrid()
        
        self.AddGrid()
        self.AddControlToGrid( "IndentLabel1", "LabelControl", "    ", 1, 0, "", False )
        self.AddControlToGrid( "DraftFormatLabel", "LabelControl", "Format", 1, 1, "The output format used by the Quick Draft submission.", False )
        self.draftFormatBox = self.AddComboControlToGrid( "DraftFormatBox", "ComboControl", "Output Type", self.Formats, 1, 2, expand=True ) 
        self.draftFormatBox.ValueModified.connect(self.AdjustQuality)
        self.draftFormatBox.ValueModified.connect(self.AdjustCodecs)
        self.draftFormatBox.ValueModified.connect(self.AdjustFrameRates)
        
        self.AddControlToGrid( "IndentLabel5", "LabelControl", "  ", 1, 3, "", False )
        self.AddHorizontalSpacerToGrid( "ColumnSpacer", 1, 6 )

        selectedFormat = self.FormatsDict[self.GetValue( "DraftFormatBox" )][0]
        self.AddControlToGrid( "DraftCodecLabel", "LabelControl", "Compression", 1, 4, "The compression used by the Quick Draft submission.", False )
        draftCodecBox = self.AddComboControlToGrid( "DraftCodecBox", "ComboControl", "Output Type", self.CodecsDict[selectedFormat], 1, 5, expand=True )
        draftCodecBox.ValueModified.connect(self.AdjustFrameRates)
        draftCodecBox.ValueModified.connect(self.AdjustQuality)

        self.AddControlToGrid( "DraftResolutionLabel", "LabelControl", "Resolution", 2, 1, "The resolution used by the Quick Draft submission.", False )
        self.AddComboControlToGrid( "DraftResolutionBox", "ComboControl", "Output Type", self.Resolutions, 2, 2, expand=True )
        
        self.AddControlToGrid( "DraftQualityLabel", "LabelControl", "Quality", 2, 4, "The quality used by the Quick Draft submission.", False )
        self.AddRangeControlToGrid( "DraftQualityBox", "RangeControl", 85, 0, 100, 0, 1, 2, 5, expand=True )
        
        self.AddControlToGrid( "DraftFrameRateLabel", "LabelControl", "Frame Rate", 3, 4, "The frame rate used by the Quick Draft submission.", False )
        self.AddComboControlToGrid( "DraftFrameRateBox", "ComboControl", "Output Type", self.FrameRates, 3, 5, expand=True )
        self.SetValue( "DraftFrameRateBox", 24 )
        
        self.AddControlToGrid( "DraftColorSpaceInLabel", "LabelControl", "Color Space In", 4, 1, "The color space in.", False )
        draftColorSpaceInBox = self.AddComboControlToGrid( "DraftColorSpaceInBox", "ComboControl", "Output Type", self.Luts, 4, 2, expand=True )
        draftColorSpaceInBox.ValueModified.connect(self.UpdateDraft)
        
        self.AddControlToGrid( "DraftColorSpaceOutLabel", "LabelControl", "Color Space Out", 4, 4, "The color space out.", False )
        self.AddComboControlToGrid( "DraftColorSpaceOutBox", "ComboControl", "Output Type", self.Luts, 4, 5, expand=True )
        self.EndGrid()
        
        self.AddGrid()
        self.AddControlToGrid( "IndentLabel4", "LabelControl", "    ", 1, 0, "", False )
        draftAnnotationsCheckBox = self.AddSelectionControlToGrid( "DraftAnnotationsCheckBox", "CheckBoxControl", False, "Add Annotations", 6, 1, "Click to add frame annotations.", expand=False )
        draftAnnotationsCheckBox.ValueModified.connect(self.UpdateDraft)
        
        draftAnnotationButton = self.AddControlToGrid( "DraftAnnotationButton", "ButtonControl", "Edit Annotations", 6, 2, "Click to edit frame annotations.", expand=True, colSpan=2 )
        draftAnnotationButton.ValueModified.connect(self.OpenCreateAnnotationsUI)

        annotationHiddenField = self.AddControlToGrid( "DraftAnnotationsBox", "TextControl", "", 6, 4, expand=True, colSpan=4 )
        annotationHiddenField.hide()
        annotationImageHiddenField = self.AddControlToGrid( "DraftAnnotationsImageBox", "TextControl", "", 6, 5 )
        annotationImageHiddenField.hide()
        annotationResWidthHiddenField = self.AddControlToGrid( "DraftAnnotationsResWidthBox", "TextControl", "", 6, 6 )
        annotationResWidthHiddenField.hide()
        annotationResHeightHiddenField = self.AddControlToGrid( "DraftAnnotationsResHeightBox", "TextControl", "", 6, 7 )
        annotationResHeightHiddenField.hide()
        annotationResHeightHiddenField = self.AddControlToGrid( "DraftAnnotationsBGRedColorBox", "TextControl", "", 6, 8 )
        annotationResHeightHiddenField.hide()
        annotationResHeightHiddenField = self.AddControlToGrid( "DraftAnnotationsBGGreenColorBox", "TextControl", "", 6, 9 )
        annotationResHeightHiddenField.hide()
        annotationResHeightHiddenField = self.AddControlToGrid( "DraftAnnotationsBGBlueColorBox", "TextControl", "", 6, 10 )
        annotationResHeightHiddenField.hide()
        self.EndGrid()
        
        # Add Custom Draft
        self.AddGrid()
        self.draftCustomRadio = self.AddRadioControlToGrid( "DraftCustomRadio", "RadioControl", False, "Custom", "RadioGroup", 0, 0, "If selected, Draft will generate a job using the Draft template specified below." )
        self.draftCustomRadio.ValueModified.connect(self.UpdateDraft)
        self.EndGrid()
        
        self.AddGrid()
        self.AddControlToGrid( "IndentLabel2", "LabelControl", "    ", 0, 0, "", False )
        self.AddControlToGrid( "DraftTemplateLabel", "LabelControl", "Draft Template", 0, 1, "The Draft template to use.", False )
        self.AddSelectionControlToGrid( "DraftTemplateBox", "FileBrowserControl", "", "Template Files (*.py);;All Files (*)", 0, 2, colSpan=3 )
        
        self.AddControlToGrid( "DraftUserLabel", "LabelControl", "User Name", 1, 1, "The user name used by the Draft template.", False )
        self.AddControlToGrid( "DraftUserBox", "TextControl", "", 1, 2, colSpan=1 )
        
        self.AddControlToGrid( "DraftEntityLabel", "LabelControl", "Entity Name", 1, 3, "The entity name used by the Draft template.", False )
        self.AddControlToGrid( "DraftEntityBox", "TextControl", "", 1, 4, colSpan=1 )

        self.AddControlToGrid( "DraftVersionLabel", "LabelControl", "Version Name", 2, 1, "The version name used by the Draft template.", False )
        self.AddControlToGrid( "DraftVersionBox", "TextControl", "", 2, 2, colSpan=1 )
        
        self.AddControlToGrid( "ArgsLabel", "LabelControl", "Additional Args", 2, 3, "The arguments to pass to the Draft template. If no extra arguments are required, leave this blank.", False )
        self.AddControlToGrid( "ArgsBox", "TextControl", "", 2, 4, colSpan=1 )
        
        self.EndGrid()

        # Add project management button if necessary
        if self.addPMComponents:
            self.AddGrid()
            self.AddControlToGrid( "IndentLabel3", "LabelControl", "    ", 0, 0, "", False )
            self.draftPMButton = self.AddControlToGrid( "DraftPMButton", "ButtonControl", "Use Project Management Data", 0, 1, expand=False)
            self.AddHorizontalSpacerToGrid( "ShotgunSpacer", 0, 2 )
            self.EndGrid()

            self.draftQuickRadio.ValueModified.connect(self.AdjustPMButtons)
            self.draftCustomRadio.ValueModified.connect(self.AdjustPMButtons)
            self.draftFormatBox.ValueModified.connect(self.AdjustPMButtons)
        
        self.stickySettings = ( "DraftQuickRadio", "DraftFormatBox", "DraftCodecBox", "DraftResolutionBox", "DraftQualityBox", "DraftFrameRateBox", "DraftColorSpaceInBox", "DraftColorSpaceOutBox", "DraftAnnotationsCheckBox", "DraftAnnotationsBox", "DraftAnnotationsImageBox", "DraftAnnotationsResWidthBox", "DraftAnnotationsResHeightBox", "DraftAnnotationsBGRedColorBox", "DraftAnnotationsBGGreenColorBox", "DraftAnnotationsBGBlueColorBox", "DraftCustomRadio", "DraftTemplateBox", "DraftUserBox", "DraftEntityBox", "DraftVersionBox", "ArgsBox" )
        self.LoadSettings( self.GetSettingsFilename(), self.stickySettings )
        self.EnabledStickySaving( self.stickySettings, self.GetSettingsFilename() )

        self.UpdateDraft()

    def reject( self ):
        parent = self.parent()
        if parent == None:
            QDialog.reject()
        else:
            # The parent dialog is 4 levels up, the levels in-between consist of widgets and tab controls which don't implement reject
            self.window().reject()

    def UpdateDraft( self ):
        draftEnabled = self.DraftJobRequested()
        draftQuickEnabled = self.GetValue( "DraftQuickRadio" )
        draftCustomEnabled = self.GetValue( "DraftCustomRadio" )
        draftCreatesMovie = self.IsMovieFromFormat( self.GetValue( "DraftFormatBox" ) )
        draftColorSpacesEnabled = self.GetValue( "DraftColorSpaceInBox" ) != "Undefined"
        draftAnnotationsEnabled = self.GetValue( "DraftAnnotationsCheckBox" )
        
        self.SetEnabled( "DraftQuickRadio", draftEnabled )
        self.SetEnabled( "DraftFormatBox", draftEnabled and draftQuickEnabled )
        self.SetEnabled( "DraftFormatLabel", draftEnabled and draftQuickEnabled )
        self.SetEnabled( "DraftResolutionBox", draftEnabled and draftQuickEnabled )
        self.SetEnabled( "DraftResolutionLabel", draftEnabled and draftQuickEnabled )
        self.SetEnabled( "DraftCodecBox", draftEnabled and draftQuickEnabled )
        self.SetEnabled( "DraftCodecLabel", draftEnabled and draftQuickEnabled )
        self.SetEnabled( "DraftFrameRateLabel", draftEnabled and draftQuickEnabled and draftCreatesMovie )
        self.SetEnabled( "DraftFrameRateBox", draftEnabled and draftQuickEnabled and draftCreatesMovie )
        self.SetEnabled( "DraftColorSpaceInLabel", draftEnabled and draftQuickEnabled )
        self.SetEnabled( "DraftColorSpaceInBox", draftEnabled and draftQuickEnabled )
        self.SetEnabled( "DraftColorSpaceOutLabel", draftEnabled and draftQuickEnabled and draftColorSpacesEnabled )
        self.SetEnabled( "DraftColorSpaceOutBox", draftEnabled and draftQuickEnabled and draftColorSpacesEnabled )
        self.SetEnabled( "DraftAnnotationsCheckBox", draftEnabled and draftQuickEnabled )
        self.SetEnabled( "DraftAnnotationButton", draftEnabled and draftAnnotationsEnabled and draftQuickEnabled )
        
        self.SetEnabled( "DraftCustomRadio", draftEnabled )
        self.SetEnabled( "DraftTemplateLabel", draftEnabled and draftCustomEnabled )
        self.SetEnabled( "DraftTemplateBox", draftEnabled and draftCustomEnabled )
        self.SetEnabled( "DraftUserLabel", draftEnabled and draftCustomEnabled )
        self.SetEnabled( "DraftUserBox", draftEnabled and draftCustomEnabled )
        self.SetEnabled( "DraftVersionLabel", draftEnabled and draftCustomEnabled )
        self.SetEnabled( "DraftVersionBox", draftEnabled and draftCustomEnabled )
        self.SetEnabled( "DraftEntityLabel", draftEnabled and draftCustomEnabled )
        self.SetEnabled( "DraftEntityBox", draftEnabled and draftCustomEnabled )
        self.SetEnabled( "ArgsLabel", draftEnabled and draftCustomEnabled )
        self.SetEnabled( "ArgsBox", draftEnabled and draftCustomEnabled )

        self.AdjustQuality()
        self.AdjustColorSpaces()
        if self.addPMComponents:
            self.AdjustPMButtons()

    def AdjustPMButtons( self ):
        draftEnabled = self.DraftJobRequested()
        draftCustomEnabled = self.GetValue( "DraftCustomRadio" )
        draftCreatesMovie = self.IsMovieFromFormat( self.GetValue( "DraftFormatBox" ) )
        
        self.SetEnabled( "DraftPMButton", draftEnabled and draftCustomEnabled )

    def SetOptions( self, type, options ):
        draftBox = "Draft" + type + "Box"
       
        # Adjust the drop down. If possible, keep previous selection.
        selection = self.GetValue( draftBox )
        self.SetItems( draftBox, options )
        if( selection in options ):
            self.SetValue( draftBox, selection )
        elif type == "FrameRate":
            self.SetValue( "DraftFrameRateBox", 24 )

    def GetOptions( self, selection, selectionType, validOptions ):
        if selection in self.RestrictionsDict:
            if selectionType in self.RestrictionsDict[selection]:
                restrictedOptions = self.RestrictionsDict[selection][selectionType]
                validOptions = set( validOptions ).intersection( restrictedOptions )
        return validOptions

    def ValidQuality( self, selectedFormat, selectedCodec, enableQuality ):
        if selectedFormat in self.RestrictionsDict:
            if enableQuality in self.RestrictionsDict[selectedFormat]:
                validQualityCodecs = self.RestrictionsDict[selectedFormat][enableQuality]
                if selectedCodec in (codec.lower() for codec in validQualityCodecs):
                    return True
        return False

    def AdjustCodecs( self ):
        # Consider restrictions from selected format 
        selectedFormat = self.FormatsDict[self.GetValue( "DraftFormatBox" )][0]
        validOptions = self.GetOptions(selectedFormat, "Codec", self.CodecsDict[selectedFormat])

        # Set valid options
        self.SetOptions( "Codec", validOptions )
            
    def AdjustQuality( self ):
        draftEnabled = self.DraftJobRequested()
        draftQuickEnabled = self.GetValue( "DraftQuickRadio" )
        selectedFormat = self.FormatsDict[self.GetValue( "DraftFormatBox" )][0]
        selectedCodec = self.GetValue( "DraftCodecBox" )
        draftQualityEnabled = self.ValidQuality( selectedFormat, selectedCodec, "EnableQuality" )

        self.SetEnabled( "DraftQualityBox", draftEnabled and draftQuickEnabled and draftQualityEnabled )
        self.SetEnabled( "DraftQualityLabel", draftEnabled and draftQuickEnabled and draftQualityEnabled )

    def AdjustFrameRates( self ):
        draftCreatesMovie = self.IsMovieFromFormat( self.GetValue( "DraftFormatBox" ) )
        self.SetEnabled( "DraftFrameRateLabel", draftCreatesMovie )
        self.SetEnabled( "DraftFrameRateBox", draftCreatesMovie )

        # Get all options for frame rate
        validOptions = self.FrameRates
        
        # Consider restrictions from selected format 
        selectedFormat = self.FormatsDict[self.GetValue( "DraftFormatBox" )][0]
        validOptions = self.GetOptions( selectedFormat, "FrameRate", validOptions )
        
        # Consider restrictions from selected codec 
        selectedCodec = self.GetValue( "DraftCodecBox" )
        validOptions = self.GetOptions( selectedCodec, "FrameRate", validOptions )
        
        # Set valid options
        self.SetOptions( "FrameRate", validOptions )

    def AdjustColorSpaces( self ):
        if self.GetValue( "DraftColorSpaceInBox" ) == "Undefined":
            self.SetValue( "DraftColorSpaceOutBox", "Undefined" )
        
    def ReadInDraftOptions( self ):
        # Read in configuration files for Draft drop downs
        mainDraftFolder = RepositoryUtils.GetRepositoryPath( "submission/Draft/Main", True )
        self.Formats = self.ReadInFormatsFile( os.path.join( mainDraftFolder, "formats.txt" ) )
        self.Resolutions = self.ReadInResolutionsFile( os.path.join( mainDraftFolder, "resolutions.txt" ) )
        self.ReadInCodecsFile( os.path.join( mainDraftFolder, "codecs.txt" ) )
        self.FrameRates = self.ReadInFile( os.path.join( mainDraftFolder, "frameRates.txt" ) )
        self.Luts = self.ReadInLutsFile( os.path.join( mainDraftFolder, "luts.txt" ) )
        
        # Read special restrictions for the list of options
        self.Restrictions = self.ReadInRestrictionsFile( os.path.join( mainDraftFolder, "restrictions.txt" ) )

    def ReadInFormatsFile( self, filename ):
        results = []
        try:
            for line in open( filename ):
                words = line.split( ',' )
                name = words[1].strip() + " (" + words[0].strip() + ")"
                results.append( name )
                self.FormatsDict[name] = [words[0].strip(), words[2].strip()]
            results = filter( None, results )
        except:
            errorMsg = "Failed to read in configuration file " + filename + "."
            print(errorMsg)
            raise Exception( errorMsg )
        return results

    def ReadInResolutionsFile( self, filename ):
        results = []
        try:
            for line in open( filename ):
                words = line.split( ',' )
                name = words[1].strip() 
                results.append( name )
                self.ResolutionsDict[name] = words[0].strip()
            results = filter( None, results )
        except:
            errorMsg = "Failed to read in configuration file " + filename + "."
            print(errorMsg)
            raise Exception( errorMsg )
        return results

    def ReadInFile( self, filename ):
        try:
            results = filter( None, [line.strip() for line in open( filename )] )
        except: 
            errorMsg = "Failed to read in configuration file " + filename + "."
            print(errorMsg)
            raise Exception( errorMsg )
        return results

    def ReadInRestrictionsFile( self, filename ):
        results = []
        try:
            for line in open( filename ):
                words = line.split( ':' )
                name = words[0].strip()
                restriction = words[1].split( '=' )
                restrictionType = restriction[0].strip()
                restrictionList = map( str.strip, restriction[1].split( "," ) )
                if not name in self.RestrictionsDict:
                    results.append( name )
                    self.RestrictionsDict[name] = {}
                    self.RestrictionsDict[name][restrictionType] = restrictionList
                else:
                    self.RestrictionsDict[name][restrictionType] = restrictionList
            results = filter( None, results )
        except:
            errorMsg = "Failed to read in configuration file " + filename + "."
            print(errorMsg)
            raise Exception( errorMsg )
        return results

    def ReadInCodecsFile( self, filename ):
        try:
            for line in open( filename ):
                words = line.split( ':' )
                name = words[0].strip()
                codecList = map( str.strip, words[1].split( "," ) )
                if not name in self.CodecsDict:
                    self.CodecsDict[name] = {}

                self.CodecsDict[name] = codecList

        except:
            errorMsg = "Failed to read in configuration file " + filename + "."
            print(errorMsg)
            raise Exception( errorMsg )

    def ReadInLutsFile( self, filename ):
        results = []
        try:
            for line in open( filename ):
                words = line.split( ',' )
                name = words[0].strip() 
                results.append( name )
                self.LutsDict[name] = words[1].strip()
            results = filter( None, results )
        except:
            errorMsg = "Failed to read in configuration file " + filename + "."
            print(errorMsg)
            raise Exception( errorMsg )
        return results
        
    def IsMovieFromFormat( self, format ):
        return ( self.FormatsDict[format][1] == 'movie' )

    def GetValidDraftOutputFilename( self, paddedName ):
        draftCustomEnabled = self.GetValue( "DraftCustomRadio" )
        draftQuickEnabled = self.GetValue( "DraftQuickRadio" )
        
        if draftCustomEnabled:
            #Generate default output name by stripping padding and switching to .mov
            directory, outputFileName = os.path.split( paddedName )
            outputFileName, extension = os.path.splitext( outputFileName.replace( "#", "" ) )
            outputFileName = outputFileName.rstrip( "_.- " ) + ".mov" 

        elif draftQuickEnabled:
            directory, outputFileName = os.path.split( paddedName )
            
            if self.IsMovieFromFormat( self.GetValue( "DraftFormatBox" ) ):
                #Strip padding, since it creates a single movie file
                outputFileName = outputFileName.replace( "#", "" )
            
            #Replace extension with output format from QuickDraft
            outputFileName, extension = os.path.splitext( outputFileName )
            outputFileName = outputFileName.rstrip( "_.- " ) + "." + self.GetQuickDraftExtension() 
        return outputFileName

    def CheckDraftSanity( self, outputFile = "dummy" ):
        # Check the output file
        if( outputFile == "" ):
            self.ShowMessageBox( "A Draft job can only be submitted if you specify the Output File under the Job Options.", "Error" )
            return False

        # Check for a Draft template in the case of a Custom Draft 
        if self.GetValue( "DraftCustomRadio" ) and not self.DraftTemplateIsValid():
            return False

        return True

    def DraftTemplateIsValid( self ):
        draftTemplate = self.GetValue( "DraftTemplateBox" )
        if( not File.Exists( draftTemplate ) ):
            self.ShowMessageBox( "Draft template file \"%s\" does not exist." % draftTemplate, "Error" )
            return False
        elif( PathUtils.IsPathLocal( draftTemplate ) ):
            result = self.ShowMessageBox( "The Draft template file \"%s\" is local, are you sure you want to continue?" % draftTemplate,"Warning", ( "Yes","No" ) )
            if( result == "No" ):
                return False
        return True

    def GetSettingsDictionary( self, projectManagement=None, createVersion=False, uploadDraftMovie=False ):
        return self.CreateSettingsDictionary( projectManagement, createVersion, uploadDraftMovie )

    def CreateSettingsDictionary( self, projectManagement, createVersion, uploadDraftMovie ):
        self.settingsDict = {}

        if self.GetValue( "DraftQuickRadio" ):
            self.settingsDict["SubmitQuickDraft"] = True
            self.settingsDict["DraftExtension"] = self.FormatsDict[self.GetValue( "DraftFormatBox" )][0]
            self.settingsDict["DraftType"] = self.FormatsDict[self.GetValue( "DraftFormatBox" )][1]
            self.settingsDict["DraftResolution"] = self.ResolutionsDict[self.GetValue( "DraftResolutionBox" )]
            self.settingsDict["DraftCodec"] = self.GetValue( "DraftCodecBox" )
            if self.ValidQuality( self.FormatsDict[self.GetValue( "DraftFormatBox" )][0], self.GetValue( "DraftCodecBox" ), "EnableQuality" ):
                self.settingsDict["DraftQuality"] = self.GetValue( "DraftQualityBox" )
            self.settingsDict["DraftFrameRate"] = self.GetValue( "DraftFrameRateBox" )
            self.settingsDict["DraftColorSpaceIn"] = self.LutsDict[self.GetValue( "DraftColorSpaceInBox" )]
            self.settingsDict["DraftColorSpaceOut"] = self.LutsDict[self.GetValue( "DraftColorSpaceOutBox" )]
            if self.GetValue( "DraftAnnotationsCheckBox" ):
                self.settingsDict["DraftAnnotationsString"] = self.GetValue( "DraftAnnotationsBox" )
                self.settingsDict["DraftAnnotationsImageString"] = self.GetValue( "DraftAnnotationsImageBox" )
                self.settingsDict["DraftAnnotationsResWidthString"] = self.GetValue( "DraftAnnotationsResWidthBox" )
                self.settingsDict["DraftAnnotationsResHeightString"] = self.GetValue( "DraftAnnotationsResHeightBox" )
                self.settingsDict["DraftAnnotationsFramePaddingSize"] = self.outputPaddingSize

        elif self.GetValue( "DraftCustomRadio" ):
            self.settingsDict["DraftTemplate"] = self.GetValue( "DraftTemplateBox" )
            self.settingsDict["DraftUsername"] = self.GetValue( "DraftUserBox" )
            self.settingsDict["DraftEntity"] = self.GetValue( "DraftEntityBox" )
            self.settingsDict["DraftVersion"] = self.GetValue( "DraftVersionBox" )
            self.settingsDict["DraftExtraArgs"] = self.GetValue( "ArgsBox" )

        if projectManagement != "None":
            uploadToProjectManagement = self.addPMComponents and createVersion and uploadDraftMovie

            if( projectManagement == "Shotgun"):
                self.settingsDict["DraftUploadToShotgun"] = uploadToProjectManagement
            elif( projectManagement == "FTrack"):
                self.settingsDict["FT_DraftUploadMovie"] = uploadToProjectManagement
            elif( projectManagement == "NIM") :
                self.settingsDict["DraftUploadToNim"] = uploadToProjectManagement

        self.SaveSettings( self.GetSettingsFilename(), self.stickySettings )

        return self.settingsDict
    
    def GetDraftScriptArguments( self ):
        draftCustomEnabled = self.GetValue( "DraftCustomRadio" )
        draftQuickEnabled = self.GetValue( "DraftQuickRadio" )
        
        #prep the script arguments
        args = []
        if draftCustomEnabled:
            args.append( 'username="%s" ' % self.GetValue( "DraftUserBox" ) )
            args.append( 'entity="%s" ' % self.GetValue( "DraftEntityBox" ) )
            args.append( 'version="%s" ' % self.GetValue( "DraftVersionBox" ) )

            #remove spaces between equal signs and other text
            extraArgs = self.GetValue( "ArgsBox" )
            regexStr = r"(\S*)\s*=\s*(\S*)"
            replStr = r"\1=\2"
            extraArgs = re.sub( regexStr, replStr, extraArgs )
            
            args.append( extraArgs )

        elif draftQuickEnabled:
            args.append( 'resolution="%s" ' % self.ResolutionsDict[self.GetValue( "DraftResolutionBox" )] )
            args.append( 'codec="%s" ' % self.GetValue( "DraftCodecBox" ) )
            args.append( 'colorSpaceIn="%s" ' % self.LutsDict[self.GetValue( "DraftColorSpaceInBox" )] )
            args.append( 'colorSpaceOut="%s" ' % self.LutsDict[self.GetValue( "DraftColorSpaceOutBox" )] )
            if self.GetValue( "DraftAnnotationsCheckBox" ):
                args.append( 'annotationsString="%s" ' % str( self.GetValue( "DraftAnnotationsBox" ) ).strip() )
                args.append( 'annotationsImageString="%s" ' % str( self.GetValue( "DraftAnnotationsImageBox" ) ).strip() )
                args.append( 'annotationsResWidthString="%s" ' % str( self.GetValue( "DraftAnnotationsResWidthBox" ) ).strip() )
                args.append( 'annotationsResWidthString="%s" ' % str( self.GetValue( "DraftAnnotationsResHeightBox" ) ).strip() )
                args.append( 'annotationsFramePaddingSize="%s" ' % str( self.outputPaddingSize ).strip() )
            else:
                args.append( 'annotationsString="None" ' )
                args.append( 'annotationsImageString="None" ' )
                args.append( 'annotationsResWidthString="None" ' )
                args.append( 'annotationsResWidthString="None" ' )
                args.append( 'annotationsFramePaddingSize="None" ' )

            if self.IsMovieFromFormat( self.GetValue( "DraftFormatBox" ) ):
                args.append( 'quality="%s" ' % self.GetValue( "DraftQualityBox" ) )
                args.append( 'frameRate="%s" ' % self.GetValue( "DraftFrameRateBox" ) )
                args.append( 'quickType="createMovie" ' )
            else:
                if self.GetEnabled( "DraftQualityBox" ):
                    args.append( 'quality="%s" ' % self.GetValue( "DraftQualityBox" ) )
                else:
                    args.append( 'quality="None" ' )
                args.append( 'quickType="createImages" ' )

        self.SaveSettings( self.GetSettingsFilename(), self.stickySettings )
        
        return args

    def GetDraftScript( self ):
        draftCustomEnabled = self.GetValue( "DraftCustomRadio" )
        draftQuickEnabled = self.GetValue( "DraftQuickRadio" )

        draftScript = ""

        if draftCustomEnabled:
            # Check if Draft files exist.
            draftScript = self.GetValue("DraftTemplateBox")
            if( draftCustomEnabled and not os.path.isfile( draftScript ) ):
                self.ShowMessageBox( "Cannot find Draft script '%s'" % draftScript, "Error" )
                draftScript = ""

        elif draftQuickEnabled:
            draftScript = RepositoryUtils.GetRepositoryFilePath( "events/DraftEventPlugin/DraftQuickSubmission/QuickDraft.py", True )

        return draftScript

    def GetSettingsFilename( self ):
        return os.path.join( ClientUtils.GetUsersSettingsDirectory(), str(self.parentAppName) + "QuickCustomDraftSettings.ini" )

    def PopulateCustomDraftFields( self, projectManagement, settingsDict ):
        draftTemplateName = self.GetValue( "DraftTemplateBox" )
        user = self.GetValue( "DraftUserBox" )
        entityName = self.GetValue( "DraftEntityBox" )
        version = self.GetValue( "DraftVersionBox" )

        # Pull out the variables we need
        if projectManagement == "Shotgun":
            user = settingsDict.get( 'UserName', "" )
            task = settingsDict.get( 'TaskName', "" )
            project = settingsDict.get( 'ProjectName', "" )
            entity = settingsDict.get( 'EntityName', "" )
            draftTemplate = settingsDict.get( 'DraftTemplate', "" )
            if task.strip() != "" and task.strip() != "None":
                entityName = task
            elif project.strip() != "" and entity.strip() != "":
                entityName = "%s > %s" % ( project, entity )
            elif entity.strip() != "":
                entityName = entity
            if draftTemplate and draftTemplate != "None":
                draftTemplateName = draftTemplate
            else:
                config = RepositoryUtils.GetEventPluginConfig( "Shotgun" )
                template = config.GetConfigEntryWithDefault( "ShotgunDraftTemplate", "" ).strip()
                if template:
                    draftTemplateName = template
                    
            version = settingsDict.get( 'VersionName', "" )
        elif projectManagement == "FTrack":
            config = RepositoryUtils.GetEventPluginConfig( "FTrack" )
            template = config.GetConfigEntryWithDefault( "FTrackDraftTemplate", "" ).strip()
            if template:
                draftTemplateName = template
                
            user = settingsDict.get( 'FT_Username', "" )
            entityName = settingsDict.get( 'FT_TaskName', "" )
            version = settingsDict.get( 'FT_AssetName', "" )
        elif projectManagement == "NIM":
            config = RepositoryUtils.GetEventPluginConfig( "NIM" )
            template = config.GetConfigEntryWithDefault( "NIMDraftTemplate", "" ).strip()
            if template:
                draftTemplateName = template
                
            user = settingsDict.get( 'nim_user', "" )
            entityName = settingsDict.get( 'nim_showName', "" )
            version = settingsDict.get( 'nim_shotName', "" )
            if not entityName and not version:
                entityName = settingsDict.get( 'nim_assetName', "" )

        # Populate Custom Draft fields using project management settings
        self.SetValue( "DraftTemplateBox", draftTemplateName )
        self.SetValue( "DraftUserBox", user )
        self.SetValue( "DraftEntityBox", entityName )
        self.SetValue( "DraftVersionBox", version )

    def DraftJobRequested( self ):
        return self.fromDraftSubmitter or self.GetValue( "DraftSubmitBox" )

    def GetQuickDraftExtension( self ):
        return self.FormatsDict[self.GetValue( "DraftFormatBox" )][0]

    def UpdateOutputPaddingSize( self, outputFileName ):
        outputFileName = FrameUtils.ReplacePaddingWithFrameNumber( outputFileName, 1 )
        self.outputPaddingSize = FrameUtils.GetPaddingSizeFromFilename( outputFileName )
    
    def OpenCreateAnnotationsUI( self ):
        annotationStringArg = "annotationString=" + self.GetValue( "DraftAnnotationsBox" )
        firstFrameFileArg = "firstFrameFile=" + self.firstFrameFile
        stickyImageFileArg = "stickyImageFile=" + self.GetValue( "DraftAnnotationsImageBox" )
        resolutionWidthArg = "resolutionWidth=" + self.GetValue( "DraftAnnotationsResWidthBox" )
        resolutionHeightArg = "resolutionHeight=" + self.GetValue( "DraftAnnotationsResHeightBox" )
        framePaddingArg = "framePadding=" + str( self.outputPaddingSize )
        backgroundRedColorArg = "backgroundRedColor=" + self.GetValue( "DraftAnnotationsBGRedColorBox" )
        backgroundGreenColorArg = "backgroundGreenColor=" + self.GetValue( "DraftAnnotationsBGGreenColorBox" )
        backgroundBlueColorArg = "backgroundBlueColor=" + self.GetValue( "DraftAnnotationsBGBlueColorBox" )

        script = RepositoryUtils.GetRepositoryFilePath("submission/Draft/Main/DraftAnnotationsUI.py", True )
        args = [ "-ExecuteScript", script, annotationStringArg, firstFrameFileArg, stickyImageFileArg, resolutionWidthArg, resolutionHeightArg, framePaddingArg, backgroundRedColorArg, backgroundGreenColorArg, backgroundBlueColorArg ]

        output = ClientUtils.ExecuteCommandAndGetOutput( args )
        resultArray = output.split( '\n' )
        annotationsString = ""
        annotationsImageString = ""
        resolutionWidthString = ""
        resolutionHeightString = ""
        backgroundRedColorString = ""
        backgroundGreenColorString = ""
        backgroundBlueColorString = ""
        
        for line in resultArray:
            if line.startswith( "Create Annotation has been Cancelled" ):
                return
            elif line.startswith("Error:"):
                self.ShowMessageBox( "An error occurred while creating annotations.\n " + output + " No annotations will be created.", "Warning" )
                return
            elif line.startswith("DraftAnnotationsString="):
                annotationsString = line.replace("DraftAnnotationsString=","")
            elif line.startswith("DraftAnnotationsImageString="):
                annotationsImageString = line.replace( "DraftAnnotationsImageString=", "" )
            elif line.startswith("DraftAnnotationsResWidthString="):
                resolutionWidthString = line.replace( "DraftAnnotationsResWidthString=", "" )
            elif line.startswith("DraftAnnotationsResHeightString="):
                resolutionHeightString = line.replace( "DraftAnnotationsResHeightString=", "" )
            elif line.startswith("DraftAnnotationsBGRedColorString="):
                backgroundRedColorString = line.replace( "DraftAnnotationsBGRedColorString=", "" )
            elif line.startswith("DraftAnnotationsBGGreenColorString="):
                backgroundGreenColorString = line.replace( "DraftAnnotationsBGGreenColorString=", "" )
            elif line.startswith("DraftAnnotationsBGBlueColorString="):
                backgroundBlueColorString = line.replace( "DraftAnnotationsBGBlueColorString=", "" )
                
        if annotationsString and len( annotationsString.strip() ) != 0:
            self.SetValue( "DraftAnnotationsBox", annotationsString )

        self.SetValue( "DraftAnnotationsImageBox", annotationsImageString )
        self.SetValue( "DraftAnnotationsResWidthBox", resolutionWidthString )
        self.SetValue( "DraftAnnotationsResHeightBox", resolutionHeightString )
        self.SetValue( "DraftAnnotationsBGRedColorBox", backgroundRedColorString )
        self.SetValue( "DraftAnnotationsBGGreenColorBox", backgroundGreenColorString )
        self.SetValue( "DraftAnnotationsBGBlueColorBox", backgroundBlueColorString )
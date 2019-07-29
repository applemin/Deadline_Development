from __future__ import print_function
import sys
import os

from System.IO import File
from Deadline.Scripting import *

########################################################################
## Globals
########################################################################
scriptDialog = None

Formats = []
Resolutions = []
FrameRates = []
Restrictions = []

FormatsDict = {}
ResolutionsDict = {}
CodecsDict = {}
RestrictionsDict = {}

########################################################################

def AddDraftUI( scriptDialogHandle ):
    global scriptDialog
    scriptDialog = scriptDialogHandle
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator", "SeparatorControl", "Draft", 0, 0 )
    scriptDialog.EndGrid()
    
    # Add Draft Submission box
    scriptDialog.AddGrid()
    draftSubmitBox = scriptDialog.AddSelectionControlToGrid( "DraftSubmitBox", "CheckBoxControl", False, "Submit Draft Job On Completion", 0, 0, "If enabled, Deadline will automatically submit a Draft job after this job completes." )
    draftSubmitBox.ValueModified.connect(SubmitDraftChanged)
    
    scriptDialog.AddSelectionControlToGrid( "DraftUploadShotgunBox", "CheckBoxControl", False, "Upload Draft Results To Shotgun", 0, 1, "If enabled, the Draft results will be uploaded to Shotgun when it is complete." )
    scriptDialog.SetEnabled( "DraftUploadShotgunBox", False )
    scriptDialog.EndGrid()
    
    (draftQuickRadio, draftCustomRadio, draftFormatBox) = AddQuickAndCustomDraftOptions( scriptDialog )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "IndentLabel3", "LabelControl", "  ", 0, 0, "", False )
    draftShotgunButton = scriptDialog.AddControlToGrid( "DraftShotgunButton", "ButtonControl", "Use Shotgun Data", 0, 1, expand=False)
    draftShotgunButton.ValueModified.connect(DraftShotgunButtonPressed)
    scriptDialog.AddHorizontalSpacerToGrid( "ShotgunSpacer", 0, 2 )
    scriptDialog.EndGrid()
    
    draftQuickRadio.ValueModified.connect(AdjustShotgunButtons)
    draftCustomRadio.ValueModified.connect(AdjustShotgunButtons)
    draftFormatBox.ValueModified.connect(AdjustShotgunButtons)

def AddQuickAndCustomDraftOptions( scriptDialogHandle ):
    global scriptDialog
    scriptDialog = scriptDialogHandle    
    
    # Populate Draft option lists for drop downs
    ReadInDraftOptions()
    
    # Add Quick Draft
    scriptDialog.AddGrid()
    draftQuickRadio = scriptDialog.AddRadioControlToGrid( "DraftQuickRadio", "RadioControl", True, "Quick", "RadioGroup", 0, 0, "If selected, Draft will generate an image or a movie based on the options specified below." )
    draftQuickRadio.ValueModified.connect(QuickDraftOptionChanged)
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "IndentLabel1", "LabelControl", "  ", 0, 0, "", False )
    scriptDialog.AddControlToGrid( "DraftFormatLabel", "LabelControl", "Format", 0, 1, "The output format used by the Quick Draft submission.", False )
    draftFormatBox = scriptDialog.AddComboControlToGrid( "DraftFormatBox", "ComboControl", "Output Type", Formats, 0, 2, expand=False )	
    draftFormatBox.ValueModified.connect(AdjustQuality)
    draftFormatBox.ValueModified.connect(AdjustCodecs)
    draftFormatBox.ValueModified.connect(AdjustFrameRates)

    selectedFormat = FormatsDict[scriptDialog.GetValue( "DraftFormatBox" )][0]
    scriptDialog.AddControlToGrid( "DraftCodecLabel", "LabelControl", "Compression", 0, 3, "The compression used by the Quick Draft submission.", False )
    draftCodecBox = scriptDialog.AddComboControlToGrid( "DraftCodecBox", "ComboControl", "Output Type", CodecsDict[selectedFormat], 0, 4, expand=True )
    draftCodecBox.ValueModified.connect(AdjustFrameRates)
    draftCodecBox.ValueModified.connect(AdjustQuality)

    scriptDialog.AddControlToGrid( "DraftResolutionLabel", "LabelControl", "Resolution", 1, 1, "The resolution used by the Quick Draft submission.", False )
    scriptDialog.AddComboControlToGrid( "DraftResolutionBox", "ComboControl", "Output Type", Resolutions, 1, 2, expand=False )
    
    scriptDialog.AddControlToGrid( "DraftQualityLabel", "LabelControl", "Quality", 1, 3, "The quality used by the Quick Draft submission.", False )
    scriptDialog.AddRangeControlToGrid( "DraftQualityBox", "RangeControl", 85, 0, 100, 0, 1, 1, 4, expand=False )
    
    scriptDialog.AddControlToGrid( "DraftFrameRateLabel", "LabelControl", "Frame Rate", 1, 5, "The frame rate used by the Quick Draft submission.", False )
    scriptDialog.AddComboControlToGrid( "DraftFrameRateBox", "ComboControl", "Output Type", FrameRates, 1, 6, expand=False )
    scriptDialog.SetValue( "DraftFrameRateBox", 24 )
    scriptDialog.EndGrid()
    
    # Add Custom Draft
    scriptDialog.AddGrid()
    draftCustomRadio = scriptDialog.AddRadioControlToGrid( "DraftCustomRadio", "RadioControl", False, "Custom", "RadioGroup", 0, 0, "If selected, Draft will generate a job using the Draft template specified below." )
    draftCustomRadio.ValueModified.connect(QuickDraftOptionChanged)
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "IndentLabel2", "LabelControl", "  ", 0, 0, "", False )
    scriptDialog.AddControlToGrid( "DraftTemplateLabel", "LabelControl", "Draft Template", 0, 1, "The Draft template to use.", False )
    scriptDialog.AddSelectionControlToGrid( "DraftTemplateBox", "FileBrowserControl", "", "Template Files (*.py);;All Files (*)", 0, 2, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "DraftUserLabel", "LabelControl", "User Name", 1, 1, "The user name used by the Draft template.", False )
    scriptDialog.AddControlToGrid( "DraftUserBox", "TextControl", "", 1, 2, colSpan=1 )
    
    scriptDialog.AddControlToGrid( "DraftEntityLabel", "LabelControl", "Entity Name", 1, 3, "The entity name used by the Draft template.", False )
    scriptDialog.AddControlToGrid( "DraftEntityBox", "TextControl", "", 1, 4, colSpan=1 )

    scriptDialog.AddControlToGrid( "DraftVersionLabel", "LabelControl", "Version Name", 2, 1, "The version name used by the Draft template.", False )
    scriptDialog.AddControlToGrid( "DraftVersionBox", "TextControl", "", 2, 2, colSpan=1 )
    
    scriptDialog.AddControlToGrid( "ArgsLabel", "LabelControl", "Additional Args", 2, 3, "The arguments to pass to the Draft template. If no extra arguments are required, leave this blank.", False )
    scriptDialog.AddControlToGrid( "ArgsBox", "TextControl", "", 2, 4, colSpan=1 )
    
    scriptDialog.EndGrid()
    
    return (draftQuickRadio, draftCustomRadio, draftFormatBox)
    
def SubmitDraftChanged( *args ):
    integrationEnabled = scriptDialog.GetValue( "CreateVersionBox" )
    draftEnabled = scriptDialog.GetValue( "DraftSubmitBox" )
    draftQuickEnabled = scriptDialog.GetValue( "DraftQuickRadio" )
    draftCustomEnabled = scriptDialog.GetValue( "DraftCustomRadio" )
    draftCreatesMovie = IsMovieFromFormat( scriptDialog.GetValue( "DraftFormatBox" ) )
    
    scriptDialog.SetEnabled( "DraftQuickRadio", draftEnabled )
    scriptDialog.SetEnabled( "DraftFormatBox", draftEnabled and draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftFormatLabel", draftEnabled and draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftResolutionBox", draftEnabled and draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftResolutionLabel", draftEnabled and draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftCodecBox", draftEnabled and draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftCodecLabel", draftEnabled and draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftFrameRateLabel", draftEnabled and draftQuickEnabled and draftCreatesMovie )
    scriptDialog.SetEnabled( "DraftFrameRateBox", draftEnabled and draftQuickEnabled and draftCreatesMovie )
    
    scriptDialog.SetEnabled( "DraftCustomRadio", draftEnabled )
    scriptDialog.SetEnabled( "DraftTemplateLabel", draftEnabled and draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftTemplateBox", draftEnabled and draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftUserLabel", draftEnabled and draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftUserBox", draftEnabled and draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftVersionLabel", draftEnabled and draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftVersionBox", draftEnabled and draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftEntityLabel", draftEnabled and draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftEntityBox", draftEnabled and draftCustomEnabled )
    scriptDialog.SetEnabled( "ArgsLabel", draftEnabled and draftCustomEnabled )
    scriptDialog.SetEnabled( "ArgsBox", draftEnabled and draftCustomEnabled )
    
    scriptDialog.SetEnabled( "DraftUploadShotgunBox", integrationEnabled and draftEnabled and ( draftCreatesMovie or draftCustomEnabled ) )
    scriptDialog.SetEnabled( "DraftShotgunButton", integrationEnabled and draftEnabled and draftCustomEnabled )
    
    if draftEnabled:
        AdjustQuality()
    else:
        scriptDialog.SetEnabled( "DraftQualityBox", False )
        scriptDialog.SetEnabled( "DraftQualityLabel", False )
    
def QuickDraftOptionChanged( *args ):
    draftQuickEnabled = scriptDialog.GetValue( "DraftQuickRadio" )
    draftCustomEnabled = scriptDialog.GetValue( "DraftCustomRadio" )
    draftCreatesMovie = IsMovieFromFormat( scriptDialog.GetValue( "DraftFormatBox" ) )
    
    scriptDialog.SetEnabled( "DraftFormatBox", draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftFormatLabel", draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftResolutionBox", draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftResolutionLabel", draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftCodecBox", draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftCodecLabel", draftQuickEnabled )
    scriptDialog.SetEnabled( "DraftFrameRateLabel", draftQuickEnabled and draftCreatesMovie )
    scriptDialog.SetEnabled( "DraftFrameRateBox", draftQuickEnabled and draftCreatesMovie )
    
    scriptDialog.SetEnabled( "DraftTemplateLabel", draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftTemplateBox", draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftUserLabel", draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftUserBox", draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftVersionLabel", draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftVersionBox", draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftEntityLabel", draftCustomEnabled )
    scriptDialog.SetEnabled( "DraftEntityBox", draftCustomEnabled )
    scriptDialog.SetEnabled( "ArgsLabel", draftCustomEnabled )
    scriptDialog.SetEnabled( "ArgsBox", draftCustomEnabled )
    
    AdjustQuality()
    
def AdjustShotgunButtons( *args ):
    integrationEnabled = scriptDialog.GetValue( "CreateVersionBox" )
    draftEnabled = scriptDialog.GetValue( "DraftSubmitBox" )
    draftCustomEnabled = scriptDialog.GetValue( "DraftCustomRadio" )
    draftCreatesMovie = IsMovieFromFormat( scriptDialog.GetValue( "DraftFormatBox" ) )   

    scriptDialog.SetEnabled( "DraftUploadShotgunBox", integrationEnabled and draftEnabled and ( draftCreatesMovie or draftCustomEnabled ) )
    scriptDialog.SetEnabled( "DraftShotgunButton", integrationEnabled and draftEnabled and draftCustomEnabled )
    
def SetOptions(type, options):
    draftBox = "Draft" + type + "Box"
   
    # Adjust the drop down. If possible, keep previous selection.
    selection = scriptDialog.GetValue( draftBox )
    scriptDialog.SetItems( draftBox, options )
    if( selection in options ):
        scriptDialog.SetValue( draftBox, selection )      
    elif ( type == "FrameRate" ):
        scriptDialog.SetValue( "DraftFrameRateBox", 24 )

def GetOptions( selection, selectionType, validOptions ):
    if selection in RestrictionsDict:
        if selectionType in RestrictionsDict[selection]:
            restrictedOptions = RestrictionsDict[selection][selectionType]
            validOptions = set( validOptions ).intersection( restrictedOptions )
    return validOptions

def ValidQuality( selectedFormat, selectedCodec, enableQuality ):
    if selectedFormat in RestrictionsDict:
        if enableQuality in RestrictionsDict[selectedFormat]:
            validQualityCodecs = RestrictionsDict[selectedFormat][enableQuality]
            if selectedCodec in (codec.lower() for codec in validQualityCodecs):
                return True
    return False

def AdjustCodecs( *args ):
    # Consider restrictions from selected format 
    selectedFormat = FormatsDict[scriptDialog.GetValue( "DraftFormatBox" )][0]
    validOptions = GetOptions(selectedFormat, "Codec", CodecsDict[selectedFormat])

    # Set valid options
    SetOptions( "Codec", validOptions )
        
def AdjustQuality( *args ):
    draftQuickEnabled = scriptDialog.GetValue( "DraftQuickRadio" )
    selectedFormat = FormatsDict[scriptDialog.GetValue( "DraftFormatBox" )][0]
    selectedCodec = scriptDialog.GetValue( "DraftCodecBox" )
    draftQualityEnabled = ValidQuality( selectedFormat, selectedCodec, "EnableQuality" )

    scriptDialog.SetEnabled( "DraftQualityBox", draftQuickEnabled and draftQualityEnabled )
    scriptDialog.SetEnabled( "DraftQualityLabel", draftQuickEnabled and draftQualityEnabled )

def AdjustFrameRates( *args ):
    draftCreatesMovie = IsMovieFromFormat( scriptDialog.GetValue( "DraftFormatBox" ) )
    scriptDialog.SetEnabled( "DraftFrameRateLabel", draftCreatesMovie )
    scriptDialog.SetEnabled( "DraftFrameRateBox", draftCreatesMovie )

    # Get all options for frame rate
    validOptions = FrameRates
    
    # Consider restrictions from selected format 
    selectedFormat = FormatsDict[scriptDialog.GetValue( "DraftFormatBox" )][0]
    validOptions = GetOptions( selectedFormat, "FrameRate", validOptions )
    
    # Consider restrictions from selected codec 
    selectedCodec = scriptDialog.GetValue( "DraftCodecBox" )
    validOptions = GetOptions( selectedCodec, "FrameRate", validOptions )
    
    # Set valid options
    SetOptions( "FrameRate", validOptions )

def DraftShotgunButtonPressed( *args ):
    # Get integrationSettings from the Project Management fields 
    integrationSettings = {} 
    info = scriptDialog.GetValue( "IntegrationEntityInfoBox" )
    lines = info.splitlines()
    for line in lines:
        entries = line.split( ':' )
        integrationSettings[entries[0].strip()]=entries[1].strip()
    
    draftTemplateName = ""
    user = ""
    entityName = ""
    version = ""
    
    if( scriptDialog.GetValue( "IntegrationTypeBox" ) == "Shotgun" ):
        # Pull out the variables we need
        user = integrationSettings.get( 'User Name', "" )
        task = integrationSettings.get( 'Task Name', "" )
        project = integrationSettings.get( 'Project Name', "" )
        entity = integrationSettings.get( 'Entity Name', "" )
        draftTemplate = integrationSettings.get( 'Draft Template', "" )
    
        entityName = ""
        if task.strip() != "" and task.strip() != "None":
            entityName = task
        elif project.strip() != "" and entity.strip() != "":
            entityName = "%s > %s" % ( project, entity )
    
        draftTemplateName = ""
        if draftTemplate.strip() != "" and draftTemplate != "None":
            draftTemplateName = draftTemplate
    
        version = scriptDialog.GetValue( "IntegrationVersionBox" )
    
    elif( scriptDialog.GetValue( "IntegrationTypeBox" ) == "FTrack" ):
        user = integrationSettings.get( 'User Name', "" )
        entityName = integrationSettings.get( 'Task Name', "" )
        version = scriptDialog.GetValue( "IntegrationVersionBox" )
    
    elif( scriptDialog.GetValue( "IntegrationTypeBox" ) == "NIM" ):
        user = integrationSettings.get( 'User Name', "" )
        entityName = integrationSettings.get( 'Task ID', "" )
        version = scriptDialog.GetValue( "IntegrationVersionBox" )
        
    # Populate Custom Draft fields using shotgun settings
    scriptDialog.SetValue( "DraftTemplateBox", draftTemplateName )
    scriptDialog.SetValue( "DraftUserBox", user )
    scriptDialog.SetValue( "DraftEntityBox", entityName )
    scriptDialog.SetValue( "DraftVersionBox", version )

def UpdateDraftControlText():
    uploadCheckBoxText = ""
    useIntegrationButtonText = ""
    
    if( scriptDialog.GetValue( "IntegrationTypeBox" ) == "Shotgun" ):
        uploadCheckBoxText = "Upload Draft Results To Shotgun"
        useIntegrationButtonText = "Use Shotgun Data"
    elif( scriptDialog.GetValue( "IntegrationTypeBox" ) == "FTrack" ):
        uploadCheckBoxText = "Upload Draft Results To FTrack"
        useIntegrationButtonText = "Use FTrack Data"
    elif( scriptDialog.GetValue( "IntegrationTypeBox" ) == "NIM" ):
        uploadCheckBoxText = "Upload Draft Results To NIM"
        useIntegrationButtonText = "Use NIM Data"
        
    scriptDialog.SetValue( "DraftShotgunButton", useIntegrationButtonText )
    
    uploadShotgunCheckBox = scriptDialog.NameControlPairs()["DraftUploadShotgunBox"]
    uploadShotgunCheckBox.setText( uploadCheckBoxText )

def IsValidDraftTemplate():
    # Check for a Draft template in the case of a Custom Draft
    if( scriptDialog.GetValue( "DraftCustomRadio" ) ):
        draftTemplate = scriptDialog.GetValue( "DraftTemplateBox" )
        if( not File.Exists( draftTemplate ) ):
            scriptDialog.ShowMessageBox( "Draft template file \"%s\" does not exist." % draftTemplate, "Error" )
            return False
        elif( PathUtils.IsPathLocal( draftTemplate ) ):
            result = scriptDialog.ShowMessageBox( "The Draft template file \"%s\" is local, are you sure you want to continue?" % draftTemplate,"Warning", ( "Yes","No" ) )
            if( result == "No" ):
                return False
    return True

def GetQuickDraftScriptArguments():
    args = []
    args.append( 'resolution="%s" ' % ResolutionsDict[scriptDialog.GetValue( "DraftResolutionBox" )] )
    args.append( 'codec="%s" ' % scriptDialog.GetValue( "DraftCodecBox" ) )

    if IsMovieFromFormat( scriptDialog.GetValue( "DraftFormatBox" ) ):
        args.append( 'quality="%s" ' % scriptDialog.GetValue( "DraftQualityBox" ) )
        args.append( 'frameRate="%s" ' % scriptDialog.GetValue( "DraftFrameRateBox" ) )
    else:
        if scriptDialog.GetEnabled( "DraftQualityBox" ):
            args.append( 'quality="%s" ' % scriptDialog.GetValue( "DraftQualityBox" ) )
        else:
            args.append( 'quality="None" ' )
    
    return args
    
def GetQuickDraftExtension():
    return FormatsDict[scriptDialog.GetValue( "DraftFormatBox" )][0]
    
def WriteDraftJobInfo( writer, extraKVPIndex ):
    if scriptDialog.GetValue( "DraftQuickRadio" ):
        writer.WriteLine( "ExtraInfoKeyValue%d=SubmitQuickDraft=True\n" % ( extraKVPIndex ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftExtension=%s\n" % ( extraKVPIndex, FormatsDict[scriptDialog.GetValue( "DraftFormatBox" )][0] ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftType=%s\n" % ( extraKVPIndex, FormatsDict[scriptDialog.GetValue( "DraftFormatBox" )][1] ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftResolution=%s\n" % ( extraKVPIndex, ResolutionsDict[scriptDialog.GetValue( "DraftResolutionBox" )] ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftCodec=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "DraftCodecBox" ) ) )
        extraKVPIndex += 1
        if ValidQuality( FormatsDict[scriptDialog.GetValue( "DraftFormatBox" )][0], scriptDialog.GetValue( "DraftCodecBox" ), "EnableQuality" ):
            writer.WriteLine( "ExtraInfoKeyValue%d=DraftQuality=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "DraftQualityBox" ) ) )
            extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftFrameRate=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "DraftFrameRateBox" ) ) )
        extraKVPIndex += 1

    elif scriptDialog.GetValue( "DraftCustomRadio" ):
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftTemplate=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "DraftTemplateBox" ) ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftUsername=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "DraftUserBox" ) ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftEntity=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "DraftEntityBox" ) ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftVersion=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "DraftVersionBox" ) ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftExtraArgs=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "ArgsBox" ) ) )
        extraKVPIndex += 1     

    if( scriptDialog.GetValue( "IntegrationTypeBox" ) == "Shotgun"):
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftUploadToShotgun=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "DraftUploadShotgunBox" ) and scriptDialog.GetValue( "CreateVersionBox" ) ) )
    elif( scriptDialog.GetValue( "IntegrationTypeBox" ) == "FTrack"):
        writer.WriteLine( "ExtraInfoKeyValue%d=FT_DraftUploadMovie=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "DraftUploadShotgunBox" ) and scriptDialog.GetValue( "CreateVersionBox" ) ) )
    elif( scriptDialog.GetValue( "IntegrationTypeBox" ) == "NIM") :
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftUploadToNim=%s\n" % ( extraKVPIndex, scriptDialog.GetValue( "DraftUploadShotgunBox" ) and scriptDialog.GetValue( "CreateVersionBox" ) ) )
        
    extraKVPIndex += 1
    return extraKVPIndex

def ReadInDraftOptions():
    global Formats 
    global Resolutions
    global FrameRates
    global Restrictions
    
    # Read in configuration files for Draft drop downs
    mainDraftFolder = RepositoryUtils.GetRepositoryPath( "submission/Draft/Main", True )
    Formats = ReadInFormatsFile( os.path.join( mainDraftFolder, "formats.txt" ) )
    Resolutions = ReadInResolutionsFile( os.path.join( mainDraftFolder, "resolutions.txt" ) )
    ReadInCodecsFile( os.path.join( mainDraftFolder, "codecs.txt" ) )
    FrameRates = ReadInFile( os.path.join( mainDraftFolder, "frameRates.txt" ) )
    
    # Read special restrictions for the list of options
    Restrictions = ReadInRestrictionsFile( os.path.join( mainDraftFolder, "restrictions.txt" ) )

def ReadInFormatsFile( filename ):
    global FormatsDict
    results = []
    try:
        for line in open( filename ):
            words = line.split( ',' )
            name = words[1].strip() + " (" + words[0].strip() + ")"
            results.append( name )
            FormatsDict[name] = [words[0].strip(), words[2].strip()]
        results = filter( None, results )
    except:
        errorMsg = "Failed to read in configuration file " + filename + "."
        print(errorMsg)
        raise Exception( errorMsg )
    return results

def ReadInResolutionsFile( filename ):
    global ResolutionsDict
    results = []
    try:
        for line in open( filename ):
            words = line.split( ',' )
            name = words[1].strip() 
            results.append( name )
            ResolutionsDict[name] = words[0].strip()
        results = filter( None, results )
    except:
        errorMsg = "Failed to read in configuration file " + filename + "."
        print(errorMsg)
        raise Exception( errorMsg )
    return results

def ReadInFile( filename ):
    try:
        results = filter( None, [line.strip() for line in open( filename )] )
    except: 
        errorMsg = "Failed to read in configuration file " + filename + "."
        print(errorMsg)
        raise Exception( errorMsg )
    return results

def ReadInRestrictionsFile( filename ):
    global RestrictionsDict
    results = []
    try:
        for line in open( filename ):
            words = line.split( ':' )
            name = words[0].strip()
            restriction = words[1].split( '=' )
            restrictionType = restriction[0].strip()
            restrictionList = map( str.strip, restriction[1].split( "," ) )
            if not name in RestrictionsDict:
                results.append( name )
                RestrictionsDict[name] = {}
                RestrictionsDict[name][restrictionType] = restrictionList
                #RestrictionsDict[name] = [[restrictionType, restrictionList]]
            else:
                RestrictionsDict[name][restrictionType] = restrictionList
                #RestrictionsDict[name].append([restrictionType, restrictionList])
        results = filter( None, results )
    except:
        errorMsg = "Failed to read in configuration file " + filename + "."
        print(errorMsg)
        raise Exception( errorMsg )
    return results

def ReadInCodecsFile( filename ):
    global CodecsDict
    try:
        for line in open( filename ):
            words = line.split( ':' )
            name = words[0].strip()
            codecList = map( str.strip, words[1].split( "," ) )
            if not name in CodecsDict:
                CodecsDict[name] = {}

            CodecsDict[name] = codecList

    except:
        errorMsg = "Failed to read in configuration file " + filename + "."
        print(errorMsg)
        raise Exception( errorMsg )

def IsMovieFromFormat( format ):
    return ( FormatsDict[format][1] == 'movie' )
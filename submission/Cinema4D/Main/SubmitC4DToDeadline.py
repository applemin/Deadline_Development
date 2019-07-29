from __future__ import print_function

import io
import json
import os
import re
import shutil
import string
import subprocess
import sys
import tempfile
import time
import traceback
from collections import namedtuple

try:
    import ConfigParser
except ImportError:
    print( "Could not load ConfigParser module, sticky settings will not be loaded/saved" )

import c4d
from c4d import documents
from c4d import gui
from c4d import plugins

useTakes = False
try:
    from c4d.modules import takesystem
    useTakes = True
except ImportError:
    print( "Could not load takesystem module, modules will not be used." )

useTokens = False
try:
    from c4d.modules import tokensystem
    useTokens = True
except ImportError:
    print("Could not load tokensystem module, module will not be used.")


# A rectangular region
Region = namedtuple("Region", ["left", "top", "right", "bottom"])


## The submission dialog class.
class SubmitC4DToDeadlineDialog( gui.GeDialog ):
    
    LabelWidth = 200
    TextBoxWidth = 600
    ComboBoxWidth = 180
    RangeBoxWidth = 190
    SliderLabelWidth = 180

    renderersDict = {
        # third-party
        1029988:"arnold",
        1034128:"iray", #NVIDIA IRAY
        1036219:"redshift",
        1019782:"vray",
        1029525:"octane",

        # OpenGL
        300001061:"ogl_hardware",
        1:"ogl_software",

        # Built-in
        0:"standard",
        1023342:"physical",
        1037639:"prorender",
        1016630:"cineman"
    }

    gpuRenderers = [ "redshift" ]

    mPassTypePrefixDict ={
        "Ambient":"ambient",
        "Ambient Occlusion":"ao",
        "Atmosphere":"atmos",
        "Atmosphere (Multiply)":"atmosmul",
        "Caustics":"caustics",
        "Depth":"depth",
        "Diffuse":"diffuse",
        "Global Illumination":"gi",
        "Illumination":"illum",
        "Material Color":"matcolor",
        "Material Diffusion":"matdif",
        "Material Environment":"matenv",
        "Material Luminance":"matlum",
        "Material Normal":"normal",
        "Material Reflection":"matrefl",
        "Material Specular":"matspec",
        "Material Specular Color":"matspeccol",
        "Material Transparency":"mattrans",
        "Material UVW":"uv",
        "Motion Vector":"motion",
        "Reflection":"refl",
        "Refraction":"refr",
        "RGBA Image":"rgb",
        "Shadow":"shadow",
        "Specular":"specular"
    }

    exportFileTypeDict = {
        "Arnold" : "Arnold Scene Source File (*.ass)",
        "Redshift" : "Redshift Proxy File (*.rs)"
    }
    
    ARNOLD_PLUGIN_ID = 1029988
    ARNOLD_ASS_EXPORT = 1029993
    ARNOLD_C4D_DISPLAY_DRIVER_TYPE = 1927516736
    ARNOLD_DRIVER = 1030141
    
    REDSHIFT_PLUGIN_ID = 1036219
    REDSHIFT_EXPORT_PLUGIN_ID = 1038650

    VRAY_MULTIPASS_PLUGIN_ID = 1028268
    
    def __init__( self ):
        c4d.StatusSetBar( 25 )
        stdout = None
        
        print( "Grabbing submitter info..." )
        try:
            dcOutput = CallDeadlineCommand( [ "-prettyJSON", "-GetSubmissionInfo", "Pools", "Groups", "MaxPriority", "TaskLimit", "UserHomeDir", "RepoDir:submission/Cinema4D/Main", "RepoDir:submission/Integration/Main", ], useDeadlineBg=True )
            output = json.loads( dcOutput, encoding="utf8" )
        except:
            gui.MessageDialog( "Unable to get submitter info from Deadline:\n\n" + traceback.format_exc() )
            raise
        
        if output[ "ok" ]:
            self.SubmissionInfo = output[ "result" ]
        else:
            gui.MessageDialog( "DeadlineCommand returned a bad result and was unable to grab the submitter info.\n\n" + output[ "result" ] )
            c4d.StatusClear()
            raise Exception( output[ "result" ] )
        
        c4d.StatusSetBar( 70 )
        
        # Pools
        self.Pools = []
        self.SecondaryPools = [ " " ] # Need to have a space, since empty strings don't seem to show up.
        for pool in self.SubmissionInfo[ "Pools" ]:
            pool = pool.strip()
            self.Pools.append( pool )
            self.SecondaryPools.append( pool ) 
            
        if not self.Pools:
            self.Pools.append( "none" )
            self.SecondaryPools.append( "none" ) 
        
        c4d.StatusSetBar( 75 )
        
        # Groups
        self.Groups = []
        for group in self.SubmissionInfo[ "Groups" ]:
            self.Groups.append( group.strip() )
        
        if not self.Groups:
            self.Groups.append( "none" )
            
        c4d.StatusSetBar( 80 )
        
        # Maximum Priority / Task Limit
        self.MaximumPriority = int( self.SubmissionInfo.get( "MaxPriority", 100 ) )
        self.TaskLimit = int( self.SubmissionInfo.get( "TaskLimit", 5000 ) )
        
        c4d.StatusSetBar( 85 )
        
        # User Home Deadline Directory
        self.DeadlineHome = self.SubmissionInfo[ "UserHomeDir" ].strip()
        self.DeadlineSettings = os.path.join( self.DeadlineHome, "settings" )
        self.DeadlineTemp = os.path.join( self.DeadlineHome, "temp" )
        
        c4d.StatusSetBar( 90 )
        
        # Repository Directories
        self.C4DSubmissionDir = self.SubmissionInfo[ "RepoDirs" ][ "submission/Cinema4D/Main" ].strip()
        self.IntegrationDir = self.SubmissionInfo[ "RepoDirs" ][ "submission/Integration/Main" ].strip()
        
        c4d.StatusSetBar( 100 )
        
        # Set On Job Complete settings.
        self.OnComplete = ( "Archive", "Delete", "Nothing" )
        
        # Set Build settings.
        self.Builds = ( "None", "32bit", "64bit" )
        
        self.Exporters = []
        if plugins.FindPlugin( SubmitC4DToDeadlineDialog.ARNOLD_PLUGIN_ID ) is not None:
            self.Exporters.append( "Arnold" )
            
        if plugins.FindPlugin( SubmitC4DToDeadlineDialog.REDSHIFT_PLUGIN_ID ) is not None:
            self.Exporters.append( "Redshift" )
        
        self.Takes = []
        self.TakesDict = {}
        takesCanbeMarked = True
        if useTakes:
            # Set Takes setting
            doc = documents.GetActiveDocument()
            takeData = doc.GetTakeData()
            take = takeData.GetMainTake()
            #Takes were able to be marked starting in C4D R17 SP1 so this will make sure it doesn't break in 
            
            try:
                take.IsChecked()
            except:
                takesCanbeMarked = False
                
            self.CurrentTake = takeData.GetCurrentTake().GetName()
            while take:
                name = take.GetName()
                if name not in self.Takes: # Prevents duplicates
                    self.Takes.append( name )
                    self.TakesDict[ name ] = take

                take = GetNextObject( take )
        else:
            self.CurrentTake = " "
        
        if takesCanbeMarked:
            self.Takes.insert( 0, "Marked" )
        
        if len(self.Takes) > 1:
            self.Takes.insert( 0, "All" )
            
        self.Takes.insert( 0, " " )
        
        self.AssembleOver = [ "Blank Image", "Previous Output", "Selected Image" ]
        
        self.dialogIDs = {
            # Job Options
            "NameBoxID" : 0,
            "CommentBoxID" : 0,
            "DepartmentBoxID" : 0,
            "PoolBoxID" : 0,
            "SecondaryPoolBoxID" : 0,
            "GroupBoxID" : 0,
            "PriorityBoxID" : 0,
            "UseBatchBoxID" : 0,
            "AutoTimeoutBoxID" : 0,
            "TaskTimeoutBoxID" : 0,
            "ConcurrentTasksBoxID" : 0,
            "LimitConcurrentTasksBoxID" : 0,
            "MachineLimitBoxID" : 0,
            "IsBlacklistBoxID" : 0,
            "MachineListBoxID" :0,
            "MachineListButtonID" : 0,
            "LimitGroupsBoxID" : 0,
            "LimitGroupsButtonID" : 0,
            "DependenciesBoxID" : 0,
            "DependenciesButtonID" : 0,
            "OnCompleteBoxID" : 0,
            "SubmitSuspendedBoxID" : 0,
            "FramesBoxID" : 0,
            "EnableFrameStepBoxID" : 0,
            "TakeFramesBoxID" : 0,

            # Cinema4D Options
            "ChunkSizeBoxID" : 0,
            "ThreadsBoxID" : 0,
            "TakesBoxID" : 0,
            "IncludeMainBoxID" : 0,
            "BuildBoxID" : 0,
            "LocalRenderingBoxID" : 0,
            "SubmitSceneBoxID" : 0,
            "ExportProjectBoxID" : 0,
            "CloseOnSubmissionID" : 0,

            # Output Override Options
            "OutputOverrideID" : 0,
            "OutputOverrideButtonID" : 0,
            "OutputMultipassOverrideID" : 0,
            "OutputMultipassOverrideButtonID" : 0,

            # Gpu Override Options
            "GPUsPerTaskID" : 0,
            "SelectGPUDevicesID" : 0,

            # Export Options
            "ExportJobID" : 0,
            "ExportJobTypesID" : 0,
            "ExportLocalID" : 0,
            "ExportDependentJobBoxID" : 0,

            # General Export Options 
            "ExportPoolBoxID" : 0,
            "ExportSecondaryPoolBoxID" : 0,
            "ExportGroupBoxID" : 0,
            "ExportPriorityBoxID" : 0,
            "ExportMachineLimitBoxID" : 0,
            "ExportConcurrentTasksBoxID" : 0,
            "ExportTaskTimeoutBoxID" : 0,
            "ExportLimitGroupsBoxID" : 0,
            "ExportLimitGroupsButtonID" : 0,
            "ExportMachineListBoxID" : 0,
            "ExportMachineListButtonID" : 0,
            "ExportOnCompleteBoxID" : 0,
            "ExportIsBlacklistBoxID" : 0,
            "ExportThreadsBoxID" : 0,
            "ExportSubmitSuspendedBoxID" : 0,
            "ExportLimitConcurrentTasksBoxID" : 0,
            "ExportAutoTimeoutBoxID" : 0,
            "ExportLocationBoxID" : 0,
            "ExportLocationButtonID" : 0,

            # Region Rendering Options
            "RegionRenderTypeID" : 0,
            "EnableRegionRenderingID" : 0,
            "TilesInXID" : 0,
            "TilesInYID" : 0,
            "SingleFrameTileJobID" : 0,
            "SingleFrameJobFrameID" : 0,
            "SubmitDependentAssemblyID" : 0,
            "CleanupTilesID" : 0,
            "ErrorOnMissingTilesID" : 0,
            "AssembleTilesOverID" : 0,
            "BackgroundImageID" : 0,
            "BackgroundImageButtonID" : 0,
            "ErrorOnMissingBackgroundID" : 0,

            # Generic Dialog Buttons
            "PipelineToolStatusID" : 0,
            "SubmitButtonID" : 0,
            "CancelButtonID" : 0,
            "UnifiedIntegrationButtonID" : 0
        }

        # Set all the IDs for the dialog
        self.NextID = 0
        for dialogID in self.dialogIDs.keys():
            self.dialogIDs[ dialogID ] = self.GetNextID()
        
        c4d.StatusClear()
    
    def GetNextID( self ):
        self.NextID += 1
        return self.NextID
    
    def StartGroup( self, label ):
        self.GroupBegin( self.GetNextID(), 0, 0, 20, label, 0 )
        self.GroupBorder( c4d.BORDER_THIN_IN )
        self.GroupBorderSpace( 4, 4, 4, 4 )
    
    def EndGroup( self ):
        self.GroupEnd()
    
    def AddTextBoxGroup( self, id, label ):
        self.GroupBegin( self.GetNextID(), 0, 2, 1, "", 0 )
        self.AddStaticText( self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth, 0, label, 0 )
        self.AddEditText( id, 0, SubmitC4DToDeadlineDialog.TextBoxWidth, 0 )
        self.GroupEnd()
    
    def AddComboBoxGroup( self, id, label, checkboxID=-1, checkboxLabel="" ):
        self.GroupBegin( self.GetNextID(), 0, 3, 1, "", 0 )
        self.AddStaticText( self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth, 0, label, 0 )
        self.AddComboBox( id, 0, SubmitC4DToDeadlineDialog.ComboBoxWidth, 0 )
        if checkboxID >= 0 and checkboxLabel != "":
            self.AddCheckbox( checkboxID, 0, SubmitC4DToDeadlineDialog.LabelWidth + SubmitC4DToDeadlineDialog.ComboBoxWidth + 12, 0, checkboxLabel )
        elif checkboxID > -2:
            self.AddStaticText( self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth + SubmitC4DToDeadlineDialog.ComboBoxWidth + 12, 0, "", 0 )
        self.GroupEnd()
    
    def AddRangeBoxGroup( self, id, label, min, max, inc, checkboxID=-1, checkboxLabel="" ):
        self.GroupBegin( self.GetNextID(), 0, 3, 1, "", 0 )
        self.AddStaticText( self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth, 0, label, 0 )
        self.AddEditNumberArrows( id, 0, SubmitC4DToDeadlineDialog.RangeBoxWidth, 0 )
        if checkboxID >= 0 and checkboxLabel != "":
            self.AddCheckbox( checkboxID, 0, SubmitC4DToDeadlineDialog.LabelWidth + SubmitC4DToDeadlineDialog.ComboBoxWidth + 12, 0, checkboxLabel )
        else:
            self.AddStaticText( self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth + SubmitC4DToDeadlineDialog.RangeBoxWidth + 4, 0, "", 0 )
        self.SetLong( id, min, min, max, inc )
        self.GroupEnd()
    
    def AddSelectionBoxGroup( self, id, label, buttonID ):
        self.GroupBegin( self.GetNextID(), 0, 3, 1, "", 0 )
        self.AddStaticText( self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth, 0, label, 0 )
        self.AddEditText( id, 0, SubmitC4DToDeadlineDialog.TextBoxWidth - 56, 0 )
        self.AddButton( buttonID, 0, 8, 0, "..." )
        self.GroupEnd()
    
    def AddCheckboxGroup( self, checkboxID, checkboxLabel, textID, buttonID ):
        self.GroupBegin( self.GetNextID(), 0, 3, 1, "", 0 )
        self.AddCheckbox( checkboxID, 0, SubmitC4DToDeadlineDialog.LabelWidth, 0, checkboxLabel )
        self.AddEditText( textID, 0, SubmitC4DToDeadlineDialog.TextBoxWidth - 56, 0 )
        self.AddButton( buttonID, 0, 8, 0, "..." )
        self.GroupEnd()
    
    ## This is called when the dialog is initialized.
    def CreateLayout( self ):
        self.SetTitle( "Submit To Deadline" )
        
        self.TabGroupBegin( self.GetNextID(), 0 )
        #General Options Tab
        self.GroupBegin( self.GetNextID(), c4d.BFH_LEFT, 0, 20, "General Options", 0 )
        self.GroupBorderNoTitle( c4d.BORDER_NONE )
        
        self.StartGroup( "Job Description" )
        self.AddTextBoxGroup( self.dialogIDs[ "NameBoxID" ], "Job Name" )
        self.AddTextBoxGroup( self.dialogIDs[ "CommentBoxID" ], "Comment" )
        self.AddTextBoxGroup( self.dialogIDs[ "DepartmentBoxID" ], "Department" )
        self.EndGroup()
        
        self.StartGroup( "Job Options" )
        self.AddComboBoxGroup( self.dialogIDs[ "PoolBoxID" ], "Pool" )
        self.AddComboBoxGroup( self.dialogIDs[ "SecondaryPoolBoxID" ], "Secondary Pool" )
        self.AddComboBoxGroup( self.dialogIDs[ "GroupBoxID" ], "Group" )
        self.AddRangeBoxGroup( self.dialogIDs[ "PriorityBoxID" ], "Priority", 0, 100, 1 )
        self.AddRangeBoxGroup( self.dialogIDs[ "TaskTimeoutBoxID" ], "Task Timeout", 0, 999999, 1, self.dialogIDs[ "AutoTimeoutBoxID" ], "Enable Auto Task Timeout" )
        self.AddRangeBoxGroup( self.dialogIDs[ "ConcurrentTasksBoxID" ], "Concurrent Tasks", 1, 16, 1, self.dialogIDs[ "LimitConcurrentTasksBoxID" ], "Limit Tasks To Slave's Task Limit" )
        self.AddRangeBoxGroup( self.dialogIDs[ "MachineLimitBoxID" ], "Machine Limit", 0, 999999, 1, self.dialogIDs[ "IsBlacklistBoxID" ], "Machine List is a Blacklist" )
        self.AddSelectionBoxGroup( self.dialogIDs[ "MachineListBoxID" ], "Machine List", self.dialogIDs[ "MachineListButtonID" ] )
        self.AddSelectionBoxGroup( self.dialogIDs[ "LimitGroupsBoxID" ], "Limit Groups", self.dialogIDs[ "LimitGroupsButtonID" ] )
        self.AddSelectionBoxGroup( self.dialogIDs[ "DependenciesBoxID" ], "Dependencies", self.dialogIDs[ "DependenciesButtonID" ] )
        self.AddComboBoxGroup( self.dialogIDs[ "OnCompleteBoxID" ], "On Job Complete", self.dialogIDs[ "SubmitSuspendedBoxID" ], "Submit Job As Suspended" )
        self.EndGroup()
        
        self.StartGroup( "Cinema 4D Options" )

        self.AddComboBoxGroup( self.dialogIDs[ "TakesBoxID" ], "Take List", self.dialogIDs[ "IncludeMainBoxID" ], "Include Main take in All takes" )

        self.AddTextBoxGroup( self.dialogIDs[ "FramesBoxID" ], "Frame List" )

        self.GroupBegin( self.GetNextID(), c4d.BFH_LEFT, 4, 1, "", 0 )
        self.AddStaticText( self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth, 0, "", 0 )
        self.AddCheckbox( self.dialogIDs[ "TakeFramesBoxID" ], 0, SubmitC4DToDeadlineDialog.LabelWidth + 23, 0, "Use Take Frame Range" )
        self.AddCheckbox( self.dialogIDs[ "EnableFrameStepBoxID" ], 0, 0, 0, "Submit all frames as single task" )
        self.GroupEnd()
        
        self.AddRangeBoxGroup( self.dialogIDs[ "ChunkSizeBoxID" ], "Frames Per Task", 1, 999999, 1, self.dialogIDs[ "SubmitSceneBoxID" ], "Submit Cinema 4D Scene File" )
        self.AddRangeBoxGroup( self.dialogIDs[ "ThreadsBoxID" ], "Threads To Use", 0, 256, 1, self.dialogIDs[ "ExportProjectBoxID" ], "Export Project Before Submission" )
        self.AddComboBoxGroup( self.dialogIDs[ "BuildBoxID" ], "Build To Force", self.dialogIDs[ "LocalRenderingBoxID" ], "Enable Local Rendering" )
        
        self.GroupBegin( self.GetNextID(), c4d.BFH_LEFT, 4, 1, "", 0 )
        self.AddStaticText( self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth, 0, "", 0 )
        self.AddCheckbox( self.dialogIDs[ "CloseOnSubmissionID" ], 0, SubmitC4DToDeadlineDialog.LabelWidth + 23, 0, "Close On Submission" )
        self.AddCheckbox( self.dialogIDs[ "UseBatchBoxID" ], 0, 0, 0, "Use Batch Plugin" )
        self.GroupEnd()

        self.GroupBegin(self.GetNextID(), c4d.BFH_LEFT, 4, 1, "", 0)
        self.AddStaticText(self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth, 0, "", 0)
        self.AddButton(self.dialogIDs["UnifiedIntegrationButtonID"], c4d.BFH_CENTER, 183, 0, "Pipeline Tools")
        self.AddStaticText(self.dialogIDs["PipelineToolStatusID"], c4d.BFH_CENTER, 380, 0, "No Tools Set", 0)
        self.EndGroup()
        
        self.EndGroup()

        self.GroupEnd() #General Options Tab
        
        # Advanced Options Tab
        self.GroupBegin( self.GetNextID(), c4d.BFV_TOP, 0, 20, "Advanced Options", 0 )
        self.GroupBorderNoTitle( c4d.BORDER_NONE )

        # Output Overrides
        self.StartGroup( "Output Overrides" )
        self.AddSelectionBoxGroup( self.dialogIDs[ "OutputOverrideID" ], "Output File", self.dialogIDs[ "OutputOverrideButtonID" ] )
        self.AddSelectionBoxGroup( self.dialogIDs[ "OutputMultipassOverrideID" ], "Multipass File", self.dialogIDs[ "OutputMultipassOverrideButtonID" ] )
        self.EndGroup()
        
        # GPU AFFINITY
        self.StartGroup( "GPU Affinity Overrides" )
        self.AddRangeBoxGroup( self.dialogIDs[ "GPUsPerTaskID" ], "GPUs Per Task", 0, 16, 1 )
        self.AddTextBoxGroup( self.dialogIDs[ "SelectGPUDevicesID" ], "Select GPU Devices" )
        self.EndGroup()
        
        self.StartGroup( "Region Rendering" )
        self.AddCheckbox( self.dialogIDs[ "EnableRegionRenderingID" ], 0, SubmitC4DToDeadlineDialog.LabelWidth+SubmitC4DToDeadlineDialog.ComboBoxWidth + 12, 0, "Enable Region Rendering" )
        self.AddRangeBoxGroup( self.dialogIDs[ "TilesInXID" ], "Tiles In X", 1, 100, 1 )
        self.AddRangeBoxGroup( self.dialogIDs[ "TilesInYID" ], "Tiles In Y", 1, 100, 1 )
        
        self.GroupBegin( self.GetNextID(), 0, 3, 1, "", 0 )
        self.AddRangeBoxGroup( self.dialogIDs[ "SingleFrameJobFrameID" ], "Frame to Render", 0, 9999999, 1, self.dialogIDs[ "SingleFrameTileJobID" ], "Submit All Tiles as a Single Job." )
        self.GroupEnd() 
        self.AddCheckbox( self.dialogIDs[ "SubmitDependentAssemblyID" ], 0, SubmitC4DToDeadlineDialog.LabelWidth+SubmitC4DToDeadlineDialog.ComboBoxWidth + 12, 0, "Submit Dependent Assembly Job" )
        self.AddCheckbox( self.dialogIDs[ "CleanupTilesID" ], 0, SubmitC4DToDeadlineDialog.LabelWidth+SubmitC4DToDeadlineDialog.ComboBoxWidth + 12, 0, "Cleanup Tiles After Assembly" )
        self.AddCheckbox( self.dialogIDs[ "ErrorOnMissingTilesID" ], 0, SubmitC4DToDeadlineDialog.LabelWidth+SubmitC4DToDeadlineDialog.ComboBoxWidth + 12, 0, "Error on Missing Tiles" )
        self.AddComboBoxGroup( self.dialogIDs[ "AssembleTilesOverID" ], "Assemble Tiles Over" )
        
        self.AddSelectionBoxGroup( self.dialogIDs[ "BackgroundImageID" ], "Background Image", self.dialogIDs[ "BackgroundImageButtonID" ] )
        self.AddCheckbox( self.dialogIDs[ "ErrorOnMissingBackgroundID" ], 0, SubmitC4DToDeadlineDialog.LabelWidth+SubmitC4DToDeadlineDialog.ComboBoxWidth + 12, 0, "Error on Missing Background" )
        
        self.EndGroup()
        self.GroupEnd() #Region Rendering Tab

        #Export Jobs Tab
        self.GroupBegin( self.GetNextID(), c4d.BFV_TOP, 0, 40, "Export Jobs", 0 )
        self.StartGroup( "Export Jobs" )
        self.GroupBegin( self.GetNextID(), c4d.BFH_LEFT, 4, 1, "", 0 )
        self.AddCheckbox( self.dialogIDs[ "ExportJobID" ], 0, 624, 0, "Submit Export Job" )
        self.AddStaticText( self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth, 0, "", 0 )
        self.GroupEnd()
        self.AddComboBoxGroup( self.dialogIDs[ "ExportJobTypesID" ], "Export Type" )
        self.AddSelectionBoxGroup( self.dialogIDs[ "ExportLocationBoxID" ], "Export File Location", self.dialogIDs[ "ExportLocationButtonID" ] )
        self.EndGroup()#Export Group

        self.StartGroup( "Dependent Job Options" )
        self.GroupBegin( self.GetNextID(), c4d.BFH_LEFT, 4, 1, "", 0 )
        self.AddCheckbox( self.dialogIDs[ "ExportDependentJobBoxID" ], 0, 0, 0, "Submit Dependent Job" )
        self.AddCheckbox( self.dialogIDs[ "ExportLocalID" ], 0, 0, 0, "Export Locally" )
        self.GroupEnd()

        self.GroupBegin( self.GetNextID(), c4d.BFH_LEFT, 4, 1, "", 0 )
        self.AddStaticText( self.GetNextID(), 0, SubmitC4DToDeadlineDialog.LabelWidth, 0, "", 0 )
        self.GroupEnd()

        self.AddComboBoxGroup( self.dialogIDs[ "ExportPoolBoxID" ], "Pool" )
        self.AddComboBoxGroup( self.dialogIDs[ "ExportSecondaryPoolBoxID" ], "Secondary Pool" )
        self.AddComboBoxGroup( self.dialogIDs[ "ExportGroupBoxID" ], "Group" )
        self.AddRangeBoxGroup( self.dialogIDs[ "ExportPriorityBoxID" ], "Priority", 0, 100, 1 )
        self.AddRangeBoxGroup( self.dialogIDs[ "ExportThreadsBoxID" ], "Threads To Use", 0, 256, 1 )
        self.AddRangeBoxGroup( self.dialogIDs[ "ExportTaskTimeoutBoxID" ], "Task Timeout", 0, 999999, 1, self.dialogIDs[ "ExportAutoTimeoutBoxID" ], "Enable Auto Task Timeout" )
        self.AddRangeBoxGroup( self.dialogIDs[ "ExportConcurrentTasksBoxID" ], "Concurrent Tasks", 1, 16, 1, self.dialogIDs[ "ExportLimitConcurrentTasksBoxID" ], "Limit Tasks To Slave's Task Limit" )
        self.AddRangeBoxGroup( self.dialogIDs[ "ExportMachineLimitBoxID" ], "Machine Limit", 0, 999999, 1, self.dialogIDs[ "ExportIsBlacklistBoxID" ], "Machine List is a Blacklist" )
        self.AddSelectionBoxGroup( self.dialogIDs[ "ExportMachineListBoxID" ], "Machine List", self.dialogIDs[ "ExportMachineListButtonID" ] )
        self.AddSelectionBoxGroup( self.dialogIDs[ "ExportLimitGroupsBoxID" ], "Limit Groups", self.dialogIDs[ "ExportLimitGroupsButtonID" ] )
        self.AddComboBoxGroup( self.dialogIDs[ "ExportOnCompleteBoxID" ], "On Job Complete", self.dialogIDs[ "ExportSubmitSuspendedBoxID" ], "Submit Job As Suspended" )
        self.EndGroup()#Job Options Group

        self.GroupEnd() #Export Jobs tab
        self.GroupEnd() #Tab group
        
        self.GroupBegin( self.GetNextID(), c4d.BFH_SCALE, 0, 1, "", 0 )
        self.AddButton( self.dialogIDs[ "SubmitButtonID" ], 0, 100, 0, "Submit" )
        self.AddButton( self.dialogIDs[ "CancelButtonID" ], 0, 100, 0, "Cancel" )
        self.GroupEnd()
        
        return True
    
    ## This is called after the dialog has been initialized.
    def InitValues( self ):
        scene = documents.GetActiveDocument()
        frameRate = scene.GetFps()
        
        startFrame = 0
        endFrame = 0
        stepFrame = 0
        
        renderData = scene.GetActiveRenderData().GetData()
        frameMode = renderData.GetLong( c4d.RDATA_FRAMESEQUENCE )
        if frameMode == c4d.RDATA_FRAMESEQUENCE_MANUAL:
            startFrame = renderData.GetTime( c4d.RDATA_FRAMEFROM ).GetFrame( frameRate )
            endFrame = renderData.GetTime( c4d.RDATA_FRAMETO ).GetFrame( frameRate )
            stepFrame = renderData.GetLong( c4d.RDATA_FRAMESTEP )
        elif frameMode == c4d.RDATA_FRAMESEQUENCE_CURRENTFRAME:
            startFrame = scene.GetTime().GetFrame( frameRate )
            endFrame = startFrame
            stepFrame = 1
        elif frameMode == c4d.RDATA_FRAMESEQUENCE_ALLFRAMES:
            startFrame = scene.GetMinTime().GetFrame( frameRate )
            endFrame = scene.GetMaxTime().GetFrame( frameRate )
            stepFrame = renderData.GetLong( c4d.RDATA_FRAMESTEP )
        elif frameMode == c4d.RDATA_FRAMESEQUENCE_PREVIEWRANGE:
            startFrame = scene.GetLoopMinTime().GetFrame( frameRate )
            endFrame = scene.GetLoopMaxTime().GetFrame( frameRate )
            stepFrame = renderData.GetLong( c4d.RDATA_FRAMESTEP )
        
        frameList = str(startFrame)
        if startFrame != endFrame:
            frameList = frameList + "-" + str(endFrame)
        if stepFrame > 1:
            frameList = frameList + "x" + str(stepFrame)
        
        initName = os.path.splitext( scene.GetDocumentName() )[0]
        initComment = ""
        initDepartment = ""
        
        initPool = "none"
        initSecondaryPool = " " # Needs to have a space
        initGroup = "none"
        initPriority = 50
        initMachineLimit = 0
        initTaskTimeout = 0
        initAutoTaskTimeout = False
        initConcurrentTasks = 1
        initLimitConcurrentTasks = True
        initIsBlacklist = False
        initMachineList = ""
        initLimitGroups = ""
        initDependencies = ""
        initOnComplete = "Nothing"
        initSubmitSuspended = False
        
        initTakes = "None"
        initUseTakeFrames = False
        initIncludeMainTake = False
        initFrames = frameList
        initChunkSize = 1
        initThreads = 0
        initBuild = "None"
        initSubmitScene = False
        initExportProject = False
        initLocalRendering = False
        initCloseOnSubmission = True
        initUseBatch = True

        initExporter = ""

        initExportJob = False
        initExportJobLocal = False
        initExportDependentJob = False

        initExportLocation = ""
        initExportPool = "none"
        initExportSecondaryPool = " " # Needs to have a space
        initExportGroup = "none"
        initExportPriority = 50
        initExportThreads = 0
        initExportTaskTimeout = 0
        initExportAutoTaskTimeout = False
        initExportConcurrentTasks = 1
        initExportLimitConcurrentTasks = True
        initExportMachineLimit = 0
        initExportMachineList = ""
        initExportIsBlacklist = False
        initExportLimitGroups = ""
        initExportOnComplete = "Nothing"
        initExportSubmitSuspended = False
        initExportDependencies = ""

        initEnableRegionRendering = False
        initTilesInX = 2
        initTilesInY = 2
        initSingleFrameTileJob = True
        initSingleFrameJobFrame = 0
        initSubmitDependentAssembly = True
        initCleanupTiles = False
        initErrorOnMissingTiles = True
        initAssembleTilesOver = "Blank Image"
        initBackgroundImage = ""
        initErrorOnMissingBackground = True
        initSelectedAssembleOver = 0

        initOutputOverride = ""
        initOutputMultipassOverride = ""

        initGPUsPerTask = 0
        initGPUsSelectDevices = ""
        
        # Read in sticky settings
        self.ConfigFile = os.path.join( self.DeadlineSettings, "c4d_py_submission.ini" )
        try:
            if os.path.isfile( self.ConfigFile ):
                config = ConfigParser.ConfigParser()
                config.read( self.ConfigFile )
                
                if config.has_section( "Sticky" ):
                    if config.has_option( "Sticky", "Department" ):
                        initDepartment = config.get( "Sticky", "Department" )
                    if config.has_option( "Sticky", "Pool" ):
                        initPool = config.get( "Sticky", "Pool" )
                    if config.has_option( "Sticky", "SecondaryPool" ):
                        initSecondaryPool = config.get( "Sticky", "SecondaryPool" )
                    if config.has_option( "Sticky", "Group" ):
                        initGroup = config.get( "Sticky", "Group" )
                    if config.has_option( "Sticky", "Priority" ):
                        initPriority = config.getint( "Sticky", "Priority" )
                    if config.has_option( "Sticky", "MachineLimit" ):
                        initMachineLimit = config.getint( "Sticky", "MachineLimit" )
                    if config.has_option( "Sticky", "LimitGroups" ):
                        initLimitGroups = config.get( "Sticky", "LimitGroups" )
                    if config.has_option( "Sticky", "ConcurrentTasks" ):
                        initConcurrentTasks = config.getint( "Sticky", "ConcurrentTasks" )
                    if config.has_option( "Sticky", "IsBlacklist" ):
                        initIsBlacklist = config.getboolean( "Sticky", "IsBlacklist" )
                    if config.has_option( "Sticky", "MachineList" ):
                        initMachineList = config.get( "Sticky", "MachineList" )
                    if config.has_option( "Sticky", "SubmitSuspended" ):
                        initSubmitSuspended = config.getboolean( "Sticky", "SubmitSuspended" )
                    if config.has_option( "Sticky", "ChunkSize" ):
                        initChunkSize = config.getint( "Sticky", "ChunkSize" )

                    if config.has_option( "Sticky", "IncludeMainTake" ):
                        initIncludeMainTake = config.getboolean( "Sticky", "IncludeMainTake" )
                    if config.has_option( "Sticky", "OutputOverride" ):
                        initOutputOverride = config.get( "Sticky", "OutputOverride" )
                    if config.has_option( "Sticky", "OutputMultipassOverride" ):
                        initOutputMultipassOverride = config.get( "Sticky", "OutputMultipassOverride" )
                    if config.has_option( "Sticky", "UseTakeFrames" ):
                        initUseTakeFrames = config.getboolean( "Sticky", "UseTakeFrames" )
                    if config.has_option( "Sticky", "SubmitScene" ):
                        initSubmitScene = config.getboolean( "Sticky", "SubmitScene" )
                    if config.has_option( "Sticky", "Threads" ):
                        initThreads = config.getint( "Sticky", "Threads" )
                    if config.has_option( "Sticky", "ExportProject" ):
                        initExportProject = config.getboolean( "Sticky", "ExportProject" )
                    if config.has_option( "Sticky", "Build" ):
                        initBuild = config.get( "Sticky", "Build" )
                    if config.has_option( "Sticky", "LocalRendering" ):
                        initLocalRendering = config.getboolean( "Sticky", "LocalRendering" )
                    if config.has_option( "Sticky", "CloseOnSubmission" ):
                        initCloseOnSubmission = config.getboolean( "Sticky", "CloseOnSubmission" )
                    if config.has_option( "Sticky", "UseBatchPlugin" ):
                        initUseBatch = config.getboolean( "Sticky", "UseBatchPlugin" )

                    if config.has_option( "Sticky", "ExportJob" ):
                        initExportJob = config.getboolean( "Sticky", "ExportJob" )
                    if config.has_option( "Sticky", "ExportDependentJob" ):
                        initExportDependentJob = config.getboolean( "Sticky", "ExportDependentJob" )
                    if config.has_option( "Sticky", "LocalExport" ):
                        initExportJobLocal = config.getboolean( "Sticky", "LocalExport" )
                    if config.has_option( "Sticky", "ExportPool" ):
                        initExportPool = config.get( "Sticky", "ExportPool" )
                    if config.has_option( "Sticky", "ExportSecondaryPool" ):
                        initExportSecondaryPool = config.get( "Sticky", "ExportSecondaryPool" )
                    if config.has_option( "Sticky", "ExportGroup" ):
                        initExportGroup = config.get( "Sticky", "ExportGroup" )
                    if config.has_option( "Sticky", "ExportPriority" ):
                        initExportPriority = config.getint( "Sticky", "ExportPriority" )
                    if config.has_option( "Sticky", "ExportMachineLimit" ):
                        initExportMachineLimit = config.getint( "Sticky", "ExportMachineLimit" )
                    if config.has_option( "Sticky", "ExportLimitGroups" ):
                        initExportLimitGroups = config.get( "Sticky", "ExportLimitGroups" )
                    if config.has_option( "Sticky", "ExportIsBlacklist" ):
                        initExportIsBlacklist = config.getboolean( "Sticky", "ExportIsBlacklist" )
                    if config.has_option( "Sticky", "ExportMachineList" ):
                        initExportMachineList = config.get( "Sticky", "ExportMachineList" )
                    if config.has_option( "Sticky", "ExportSubmitSuspended" ):
                        initExportSubmitSuspended = config.getboolean( "Sticky", "ExportSubmitSuspended" )
                    if config.has_option( "Sticky", "ExportThreads" ):
                        initExportThreads = config.getint( "Sticky", "ExportThreads" )
                    if config.has_option( "Sticky", "ExportOutputLocation" ):
                        initExportLocation = config.get( "Sticky", "ExportOutputLocation" )    

                    if config.has_option( "Sticky", "EnableRegionRendering" ):
                        initEnableRegionRendering = config.getboolean( "Sticky", "EnableRegionRendering" )
                    if config.has_option( "Sticky", "TilesInX" ):
                        initTilesInX = config.getint( "Sticky", "TilesInX" )
                    if config.has_option( "Sticky", "TilesInY" ):
                        initTilesInY = config.getint( "Sticky", "TilesInY" )
                    if config.has_option( "Sticky", "SingleFrameTileJob" ):
                        initSingleFrameTileJob = config.getboolean( "Sticky", "SingleFrameTileJob" )
                    if config.has_option( "Sticky", "SingleFrameJobFrame" ):
                        initSingleFrameJobFrame = config.getint( "Sticky", "SingleFrameJobFrame" )
                    if config.has_option( "Sticky", "SubmitDependentAssembly" ):
                        initSubmitDependentAssembly = config.getboolean( "Sticky", "SubmitDependentAssembly" )
                    if config.has_option( "Sticky", "CleanupTiles" ):
                        initCleanupTiles = config.getboolean( "Sticky", "CleanupTiles" )
                    if config.has_option( "Sticky", "ErrorOnMissingTiles" ):
                        initErrorOnMissingTiles = config.getboolean( "Sticky", "ErrorOnMissingTiles" )
                    if config.has_option( "Sticky", "AssembleTilesOver" ):
                        initAssembleTilesOver = config.get( "Sticky", "AssembleTilesOver" )
                    if config.has_option( "Sticky", "BackgroundImage" ):
                        initBackgroundImage = config.get( "Sticky", "BackgroundImage" )
                    if config.has_option( "Sticky", "ErrorOnMissingBackground" ):
                        initErrorOnMissingBackground = config.getboolean( "Sticky", "ErrorOnMissingBackground" )
                    if config.has_option( "Sticky", "SelectedAssembleOver" ):
                        initSelectedAssembleOver = config.getint( "Sticky", "SelectedAssembleOver" )    

                    if config.has_option( "Sticky", "GPUsPerTask" ):
                        initGPUsPerTask = config.getint( "Sticky", "GPUsPerTask" )
                    if config.has_option( "Sticky", "GPUsSelectDevices" ):
                        initGPUsSelectDevices = config.get( "Sticky", "GPUsSelectDevices" )
        except:
            print( "Could not read sticky settings:\n" + traceback.format_exc() )
        
        if initPriority > self.MaximumPriority:
            initPriority = self.MaximumPriority / 2
       
        # Populate the combo boxes, and figure out the default selected index if necessary.       
        selectedPoolID = self.setComboBoxOptions( self.Pools, self.dialogIDs[ "PoolBoxID" ], initPool )
        selectedSecondaryPoolID = self.setComboBoxOptions( self.SecondaryPools, self.dialogIDs[ "SecondaryPoolBoxID" ], initSecondaryPool )
        selectedGroupID = self.setComboBoxOptions( self.Groups, self.dialogIDs[ "GroupBoxID" ], initGroup )
        selectedOnCompleteID = self.setComboBoxOptions( self.OnComplete, self.dialogIDs[ "OnCompleteBoxID" ], initOnComplete )
        selectedBuildID = self.setComboBoxOptions( self.Builds, self.dialogIDs[ "BuildBoxID" ], initBuild )
        selectedTakeID = self.setComboBoxOptions( self.Takes, self.dialogIDs[ "TakesBoxID" ], initTakes )

        # Populate the Export combo boxes, and figure out the default selected index if necessary.
        selectExportJobTypeID = self.setComboBoxOptions( self.Exporters, self.dialogIDs[ "ExportJobTypesID" ], initExporter )
        selectedExportPoolID = self.setComboBoxOptions( self.Pools, self.dialogIDs[ "ExportPoolBoxID" ], initExportPool )
        selectedExportSecondaryPoolID = self.setComboBoxOptions( self.SecondaryPools, self.dialogIDs[ "ExportSecondaryPoolBoxID" ], initExportSecondaryPool )
        selectedExportGroupID = self.setComboBoxOptions( self.Groups, self.dialogIDs[ "ExportGroupBoxID" ], initExportGroup )
        selectedExportOnCompleteID = self.setComboBoxOptions( self.OnComplete, self.dialogIDs[ "ExportOnCompleteBoxID" ], initExportOnComplete )
        
        selectedAssembleOverID = self.setComboBoxOptions( self.AssembleOver, self.dialogIDs[ "AssembleTilesOverID" ], initSelectedAssembleOver )

        self.Enable( self.dialogIDs[ "TakesBoxID" ], useTakes )
        self.Enable( self.dialogIDs[ "IncludeMainBoxID" ], useTakes )
        self.Enable( self.dialogIDs[ "TakeFramesBoxID" ], useTakes )

        # Set the default settings.
        self.SetString( self.dialogIDs[ "NameBoxID" ], initName )
        self.SetString( self.dialogIDs[ "CommentBoxID" ], initComment )
        self.SetString( self.dialogIDs[ "DepartmentBoxID" ], initDepartment )

        self.SetLong( self.dialogIDs[ "PoolBoxID" ], selectedPoolID )
        self.SetLong( self.dialogIDs[ "SecondaryPoolBoxID" ], selectedSecondaryPoolID )
        self.SetLong( self.dialogIDs[ "GroupBoxID" ], selectedGroupID )
        self.SetLong( self.dialogIDs[ "PriorityBoxID" ], initPriority, 0, self.MaximumPriority, 1 )
        self.SetLong( self.dialogIDs[ "MachineLimitBoxID" ], initMachineLimit )
        self.SetLong( self.dialogIDs[ "TaskTimeoutBoxID" ], initTaskTimeout )
        self.SetBool( self.dialogIDs[ "AutoTimeoutBoxID" ], initAutoTaskTimeout )
        self.SetLong( self.dialogIDs[ "ConcurrentTasksBoxID" ], initConcurrentTasks )
        self.SetBool( self.dialogIDs[ "LimitConcurrentTasksBoxID" ], initLimitConcurrentTasks )
        self.SetBool( self.dialogIDs[ "IsBlacklistBoxID" ], initIsBlacklist )
        self.SetString( self.dialogIDs[ "MachineListBoxID" ], initMachineList )
        self.SetString( self.dialogIDs[ "LimitGroupsBoxID" ], initLimitGroups )
        self.SetString( self.dialogIDs[ "DependenciesBoxID" ], initDependencies )
        self.SetLong( self.dialogIDs[ "OnCompleteBoxID" ], selectedOnCompleteID )
        self.SetBool( self.dialogIDs[ "SubmitSuspendedBoxID" ], initSubmitSuspended )
        self.SetLong( self.dialogIDs[ "ChunkSizeBoxID" ], initChunkSize )

        # Find current take in list of all takes
        selectedTakeID = self.Takes.index( str( self.CurrentTake ) )
        self.SetLong( self.dialogIDs[ "TakesBoxID" ], selectedTakeID )
        self.SetBool( self.dialogIDs[ "IncludeMainBoxID" ], initIncludeMainTake )
        self.SetString( self.dialogIDs[ "FramesBoxID" ], initFrames )
        self.SetBool( self.dialogIDs[ "TakeFramesBoxID" ], initUseTakeFrames )
        self.SetBool( self.dialogIDs[ "SubmitSceneBoxID" ], initSubmitScene )
        self.SetLong( self.dialogIDs[ "ThreadsBoxID" ], initThreads )
        self.SetBool( self.dialogIDs[ "ExportProjectBoxID" ], initExportProject )
        self.SetLong( self.dialogIDs[ "BuildBoxID" ], selectedBuildID )
        self.SetBool( self.dialogIDs[ "LocalRenderingBoxID" ], initLocalRendering )
        self.SetBool( self.dialogIDs[ "CloseOnSubmissionID" ], initCloseOnSubmission )
        self.SetBool( self.dialogIDs[ "UseBatchBoxID" ], initUseBatch )

        self.SetBool( self.dialogIDs[ "EnableFrameStepBoxID" ], False )
        self.EnableFrameStep()
        self.Enable( self.dialogIDs[ "SubmitSceneBoxID" ], not initExportProject )
        self.Enable( self.dialogIDs[ "UseBatchBoxID" ], ( c4d.GetC4DVersion() / 1000 ) >= 15 )

        self.SetBool( self.dialogIDs[ "EnableRegionRenderingID" ], initEnableRegionRendering )
        self.SetLong( self.dialogIDs[ "TilesInXID" ], initTilesInX )
        self.SetLong( self.dialogIDs[ "TilesInYID" ], initTilesInY )
        self.SetBool( self.dialogIDs[ "SingleFrameTileJobID" ], initSingleFrameTileJob )
        self.SetLong( self.dialogIDs[ "SingleFrameJobFrameID" ], initSingleFrameJobFrame )
        self.SetBool( self.dialogIDs[ "SubmitDependentAssemblyID" ], initSubmitDependentAssembly )
        self.SetBool( self.dialogIDs[ "CleanupTilesID" ], initCleanupTiles )
        self.SetBool( self.dialogIDs[ "ErrorOnMissingTilesID" ], initErrorOnMissingTiles )
        self.SetLong( self.dialogIDs[ "AssembleTilesOverID" ], selectedAssembleOverID)
        self.SetString( self.dialogIDs[ "BackgroundImageID" ], initBackgroundImage )
        self.SetBool( self.dialogIDs[ "ErrorOnMissingBackgroundID" ], initErrorOnMissingBackground )

        self.EnableRegionRendering()

        self.SetString( self.dialogIDs[ "OutputOverrideID" ], initOutputOverride )
        self.SetString( self.dialogIDs[ "OutputMultipassOverrideID" ], initOutputMultipassOverride )

        self.SetLong( self.dialogIDs[ "GPUsPerTaskID" ] , initGPUsPerTask )
        self.SetString( self.dialogIDs[ "SelectGPUDevicesID" ] , initGPUsSelectDevices )

        self.EnableGPUAffinityOverride()
        
        #If 'CustomSanityChecks.py' exists, then it executes. This gives the user the ability to change default values
        self.SanityCheckFile = os.path.join( self.C4DSubmissionDir, "CustomSanityChecks.py" )
        if os.path.isfile( self.SanityCheckFile ):
            print( "Running sanity check script: " + self.SanityCheckFile )
            try:
                import CustomSanityChecks
                sanityResult = CustomSanityChecks.RunSanityCheck( self )
                if not sanityResult:
                    print( "Sanity check returned False, exiting" )
                    self.Close()
            except:
                gui.MessageDialog( "Could not run CustomSanityChecks.py script:\n" + traceback.format_exc() )

        self.SetString( self.dialogIDs[ "ExportLocationBoxID" ], initExportLocation )
        self.SetBool( self.dialogIDs[ "ExportJobID" ], initExportJob )
        if len( self.Exporters ) == 0:
            self.SetBool( self.dialogIDs[ "ExportJobID" ], False )
            self.Enable( self.dialogIDs[ "ExportJobID" ], False )
        self.EnableExportFields()

        self.SetBool( self.dialogIDs[ "ExportLocalID" ], initExportJobLocal )
        self.SetBool( self.dialogIDs[ "ExportDependentJobBoxID" ], initExportDependentJob )
        self.EnableDependentExportFields()

        self.SetLong( self.dialogIDs[ "ExportPoolBoxID" ], selectedExportPoolID )
        self.SetLong( self.dialogIDs[ "ExportSecondaryPoolBoxID" ], selectedExportSecondaryPoolID )
        self.SetLong( self.dialogIDs[ "ExportGroupBoxID" ], selectedExportGroupID )
        self.SetLong( self.dialogIDs[ "ExportPriorityBoxID" ], initExportPriority, 0, self.MaximumPriority, 1 )
        self.SetLong( self.dialogIDs[ "ExportThreadsBoxID" ], initExportThreads )
        self.SetLong( self.dialogIDs[ "ExportTaskTimeoutBoxID" ], initExportTaskTimeout )
        self.SetBool( self.dialogIDs[ "ExportAutoTimeoutBoxID" ], initExportAutoTaskTimeout )
        self.SetLong( self.dialogIDs[ "ExportConcurrentTasksBoxID" ], initExportConcurrentTasks )
        self.SetBool( self.dialogIDs[ "ExportLimitConcurrentTasksBoxID" ], initExportLimitConcurrentTasks )
        self.SetLong( self.dialogIDs[ "ExportMachineLimitBoxID" ], initExportMachineLimit )
        self.SetBool( self.dialogIDs[ "ExportIsBlacklistBoxID" ], initExportIsBlacklist )
        self.SetString( self.dialogIDs[ "ExportMachineListBoxID" ], initExportMachineList )
        self.SetString( self.dialogIDs[ "ExportLimitGroupsBoxID" ], initExportLimitGroups )
        self.SetLong( self.dialogIDs[ "ExportOnCompleteBoxID" ], selectedExportOnCompleteID )
        self.SetBool( self.dialogIDs[ "ExportSubmitSuspendedBoxID" ], initExportSubmitSuspended )

        statusMessage = self.retrievePipelineToolStatus()
        self.updatePipelineToolStatusLabel( statusMessage )

        self.EnableOutputOverrides()

        return True

    def setComboBoxOptions( self, options, dialogID, stickyValue ):
        selectedID = 0
        for i, option in enumerate(options):
            self.AddChild( dialogID, i, option )
            if stickyValue == option:
                selectedID = i

        return selectedID

    def getTakeFrames( self, s ):
        try:
            start = s.index( "<%" ) + len( "<%" )
            end = s.index( "%>", start )
            return s[start:end]
        except ValueError:
            return ""

    def stripTakeName( self, s ):
        try:
            start = s.index( "<%"  )
            end = s.index( "%>" )
            return s.replace(s[start:end+2], "")
        except ValueError:
            return ""

    def EnableExportFields( self ):
        exportEnabled = self.GetBool( self.dialogIDs[ "ExportJobID" ] )

        self.Enable( self.dialogIDs[ "ExportDependentJobBoxID" ], exportEnabled )
        self.Enable( self.dialogIDs[ "ExportJobTypesID" ], exportEnabled )
        self.Enable( self.dialogIDs[ "ExportLocationButtonID" ], exportEnabled )
        self.Enable( self.dialogIDs[ "ExportLocationBoxID" ], exportEnabled )

        self.EnableDependentExportFields()

    def EnableDependentExportFields( self ):
        dependentExportEnabled = self.GetBool( self.dialogIDs[ "ExportDependentJobBoxID" ] )
        exportJobEnabled = self.GetBool( self.dialogIDs[ "ExportJobID" ] )

        self.Enable( self.dialogIDs[ "ExportPoolBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportSecondaryPoolBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportGroupBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportPriorityBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportThreadsBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportTaskTimeoutBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportAutoTimeoutBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportConcurrentTasksBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportLimitConcurrentTasksBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportMachineLimitBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportIsBlacklistBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportMachineListBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportMachineListButtonID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportLimitGroupsBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportLimitGroupsButtonID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportOnCompleteBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportSubmitSuspendedBoxID" ], (dependentExportEnabled and exportJobEnabled) )
        self.Enable( self.dialogIDs[ "ExportLocalID" ], (dependentExportEnabled and exportJobEnabled) )

    def EnableFrameStep( self ):
        frameStepEnabled = self.GetBool( self.dialogIDs[ "EnableFrameStepBoxID" ] )
        
        isSingleTileJob = self.GetBool( self.dialogIDs[ "SingleFrameTileJobID" ] ) and self.IsRegionRenderingEnabled()
        self.Enable( self.dialogIDs[ "ChunkSizeBoxID" ], not frameStepEnabled and not isSingleTileJob )

    def IsGPUAffinityOverrideEnabled( self ):
        """
        A utility function to determine if the current renderer supports GPU Affinity Overrides
        :return: Whether or not we can override the GPU affinity of the Current Renderer.
        """
        return self.getRenderer( ) in self.gpuRenderers

    def EnableGPUAffinityOverride( self ):
        enabled = self.IsGPUAffinityOverrideEnabled()

        self.Enable( self.dialogIDs[ "GPUsPerTaskID" ], enabled )
        self.Enable( self.dialogIDs[ "SelectGPUDevicesID" ], enabled )

    def IsRegionRenderingEnabled( self ):
        return self.GetBool( self.dialogIDs[ "EnableRegionRenderingID" ] ) and self.GetBool( self.dialogIDs[ "UseBatchBoxID" ] )
    
    def EnableRegionRendering( self ):
        self.Enable( self.dialogIDs[ "EnableRegionRenderingID" ], self.GetBool( self.dialogIDs[ "UseBatchBoxID" ] ) )

        enable = self.IsRegionRenderingEnabled()
            
        self.Enable( self.dialogIDs[ "TilesInXID" ], enable )
        self.Enable( self.dialogIDs[ "TilesInYID" ], enable )
        self.Enable( self.dialogIDs[ "SingleFrameTileJobID" ], enable )
        self.Enable( self.dialogIDs[ "SubmitDependentAssemblyID" ], enable )
        self.Enable( self.dialogIDs[ "CleanupTilesID" ], enable )
        self.Enable( self.dialogIDs[ "ErrorOnMissingTilesID" ], enable )
        self.Enable( self.dialogIDs[ "AssembleTilesOverID" ], enable )
        
        self.IsSingleFrameTileJob()
        self.AssembleOverChanged()
        self.EnableOutputOverrides()

    def IsOutputOverrideEnabled( self ):
        return not self.GetBool( self.dialogIDs[ "ExportJobID" ] )
    
    def EnableOutputOverrides( self ):
        enable = self.IsOutputOverrideEnabled()

        self.Enable( self.dialogIDs[ "OutputOverrideID" ], enable )
        self.Enable( self.dialogIDs[ "OutputMultipassOverrideID" ], enable )

    def IsSingleFrameTileJob( self ):
        isSingleJob = self.GetBool( self.dialogIDs[ "SingleFrameTileJobID" ] ) and self.IsRegionRenderingEnabled()
            
        self.Enable( self.dialogIDs[ "SingleFrameJobFrameID" ], isSingleJob )
        self.Enable( self.dialogIDs[ "EnableFrameStepBoxID" ], not isSingleJob )
        self.Enable( self.dialogIDs[ "FramesBoxID" ], not isSingleJob )
        
        self.EnableFrameStep()
    
    def AssembleOverChanged( self ):
        assembleOver = self.GetLong( self.dialogIDs[ "AssembleTilesOverID" ] )
        if assembleOver == 0:
            self.Enable( self.dialogIDs[ "BackgroundImageID" ], False )
            self.Enable( self.dialogIDs[ "BackgroundImageButtonID" ], False )
            self.Enable( self.dialogIDs[ "ErrorOnMissingBackgroundID" ], False )
        elif assembleOver == 1:
            self.Enable( self.dialogIDs[ "BackgroundImageID" ], False )
            self.Enable( self.dialogIDs[ "BackgroundImageButtonID" ], False )
            self.Enable( self.dialogIDs[ "ErrorOnMissingBackgroundID" ], True )
        elif assembleOver == 2:
            self.Enable( self.dialogIDs[ "BackgroundImageID" ], True )
            self.Enable( self.dialogIDs[ "BackgroundImageButtonID" ], True )
            self.Enable( self.dialogIDs[ "ErrorOnMissingBackgroundID" ], True )
    
    def retrievePipelineToolStatus( self ):
        """
        Grabs a status message from the JobWriter that indicates which pipeline tools have settings enabled for the current scene.
        :return: A string representing the status of the pipeline tools for the current scene.
        """
        jobWriterPath = os.path.join( self.IntegrationDir, "JobWriter.py" )
        scenePath = documents.GetActiveDocument().GetDocumentPath()
        args = [ "-ExecuteScript", jobWriterPath, "Cinema4D", "--status", "--scene-path", scenePath ]
        statusMessage = CallDeadlineCommand( args )

        return statusMessage

    def updatePipelineToolStatusLabel( self, statusMessage ):
        """
        Updates the pipeline tools status label with a non-empty status message as there's always a status associated with the pipeline tools.
        :param statusMessage: A non-empty string representing the status of the pipeline tools for the current scene.
        :return: None
        """
        if not statusMessage:
            raise ValueError( 'The status message for the pipeline tools label is not allowed to be empty.' )

        if statusMessage.startswith( "Error" ):
            self.SetString( self.dialogIDs[ "PipelineToolStatusID" ], "Pipeline Tools Error" )
            print( statusMessage )
        else:
            self.SetString( self.dialogIDs[ "PipelineToolStatusID" ], statusMessage )

    def OpenIntegrationWindow( self ):
        """
        Launches a graphical interface for the pipeline tools, attempts to grab local project management info from the scene, and updates the
        Pipeline Tools status label indicating which project management tools are being used.
        :return: None
        """
        if self.IntegrationDir not in sys.path:
            sys.path.append( self.IntegrationDir )

        try:
            import GetPipelineToolsInfo
            GetPipelineToolsInfo.getInfo( self.DeadlineTemp )
        except ImportError:
            print( "Failed to import GetPipelineToolsInfo.py." )
            print( traceback.format_exc() )

        print( "\nOpening Integration window" )
        integrationPath = os.path.join( self.IntegrationDir, "IntegrationUIStandAlone.py" )
        scenePath = documents.GetActiveDocument().GetDocumentPath()
        args = ["-ExecuteScript", integrationPath, "-v", "2", "Cinema4D", "-d", "Shotgun", "FTrack", "NIM", "--path", scenePath]
        statusMessage = CallDeadlineCommand( args, hideWindow=False, useArgFile=True )
        self.updatePipelineToolStatusLabel( statusMessage )

    def ConcatenatePipelineSettingsToJob( self, jobInfoPath, batchName ):
        """
        Concatenate pipeline tool settings for the scene to the .job file.
        :param jobInfoPath: Path to the .job file.
        :param batchName: Value of the 'batchName' job info entry, if it is required.
        :return: None
        """

        jobWriterPath = os.path.join( self.IntegrationDir, "JobWriter.py" )
        scenePath = documents.GetActiveDocument().GetDocumentPath()
        argArray = ["-ExecuteScript", jobWriterPath, "Cinema4D", "--write", "--scene-path", scenePath, "--job-path",
                    jobInfoPath, "--batch-name", batchName.decode('utf-8')]
        CallDeadlineCommand( argArray, hideWindow=False, useArgFile=True )

    def SubmitDependentExportJob( self, renderer, jobIds, groupBatch, take ):
        """
        Submits the dependent render job for the current renderer following the export process
        :param renderer: string representation of the current renderer
        :param jobIds: a list of dependent job IDs
        :param groupBatch: boolean used to determine if we should batch the jobs
        :param take: the current take to render
        :return: the results from submitting the job via deadlinecommand
        """
        scene = documents.GetActiveDocument()
        jobName = self.GetString( self.dialogIDs[ "NameBoxID" ] )

        exportDependencies = ",".join( jobIds )

        renderData = self.GetRenderInfo( scene, take ).GetData()

        if take:
            jobName += " - %s" % take

        jobName += " - %s Standalone" % renderer

        outputPath = renderData.GetFilename( c4d.RDATA_PATH )
        outputOverride = self.GetString( self.dialogIDs[ "OutputOverrideID" ] ).strip()
        if self.IsOutputOverrideEnabled() and len( outputOverride ) > 0:
            outputPath = outputOverride

        if not os.path.isabs( outputPath ):
            scenePath = scene.GetDocumentPath()
            outputPath = os.path.join( scenePath, outputPath )

        outputFormat = renderData.GetLong( c4d.RDATA_FORMAT )
        outputNameFormat = renderData.GetLong( c4d.RDATA_NAMEFORMAT )

        print( "\nCreating %s standalone job info file" % renderer )
        exportJobInfoFile = os.path.join( self.DeadlineTemp, "%s_submit_info.job" % renderer.lower() )

        jobContents = {
            "Plugin": renderer,
            "Name": jobName,
            "Pool": self.Pools[ self.GetLong( self.dialogIDs[ "ExportPoolBoxID" ] ) ],
            "SecondaryPool": "",
            "Group": self.Groups[ self.GetLong( self.dialogIDs[ "ExportGroupBoxID" ] ) ],
            "Priority": self.GetLong( self.dialogIDs[ "ExportPriorityBoxID" ] ),
            "MachineLimit": self.GetLong( self.dialogIDs[ "ExportMachineLimitBoxID" ] ),
            "TaskTimeoutMinutes": self.GetLong( self.dialogIDs[ "ExportTaskTimeoutBoxID" ] ),
            "EnableAutoTimeout": self.GetBool( self.dialogIDs[ "ExportAutoTimeoutBoxID" ] ),
            "ConcurrentTasks": self.GetLong( self.dialogIDs[ "ExportConcurrentTasksBoxID" ] ),
            "LimitConcurrentTasksToNumberOfCpus": self.GetBool( self.dialogIDs[ "ExportLimitConcurrentTasksBoxID" ] ),
            "LimitGroups": self.GetString( self.dialogIDs[ "ExportLimitGroupsBoxID" ] ),
            "JobDependencies": exportDependencies,
            "OnJobComplete": self.OnComplete[ self.GetLong( self.dialogIDs[ "ExportOnCompleteBoxID" ] ) ],
            "IsFrameDependent": True,
            "ChunkSize": 1,
        }

        if groupBatch:
            jobContents["BatchName"] = self.GetString( self.dialogIDs[ "NameBoxID" ] )

        # If it's not a space, then a secondary pool was selected.
        if self.SecondaryPools[ self.GetLong( self.dialogIDs[ "ExportSecondaryPoolBoxID" ] ) ] != " ":
            jobContents["SecondaryPool"] = self.SecondaryPools[ self.GetLong( self.dialogIDs[ "ExportSecondaryPoolBoxID" ] ) ]

        if self.GetBool( self.dialogIDs[ "TakeFramesBoxID" ] ):
            framesPerSecond = renderData.GetReal( c4d.RDATA_FRAMERATE )
            startFrame = renderData.GetTime( c4d.RDATA_FRAMEFROM ).GetFrame( framesPerSecond )
            endFrame = renderData.GetTime( c4d.RDATA_FRAMETO ).GetFrame( framesPerSecond )
            frames = "%s-%s" % ( startFrame, endFrame )
        else:
            frames  = self.GetString( self.dialogIDs[ "FramesBoxID" ] )
        jobContents["Frames"] = frames

        if self.GetBool( self.dialogIDs[ "ExportSubmitSuspendedBoxID" ] ):
            jobContents["InitialStatus"] = "Suspended"

        if self.GetBool( self.dialogIDs[ "ExportIsBlacklistBoxID" ] ):
            jobContents["Blacklist"] = self.GetString( self.dialogIDs[ "ExportMachineListBoxID" ] )
        else:
            jobContents["Whitelist"] = self.GetString( self.dialogIDs[ "ExportMachineListBoxID" ] )

        outputFilename = self.GetOutputFileName( outputPath, outputFormat, outputNameFormat, take )
        if outputFilename:
            jobContents["OutputFilename0"] = outputFilename

        self.writeInfoFile( exportJobInfoFile, jobContents )
        self.ConcatenatePipelineSettingsToJob( exportJobInfoFile, self.GetString( self.dialogIDs[ "NameBoxID" ] ) )

        print( "Creating %s standalone plugin info file" % renderer )
        exportPluginInfoFile = os.path.join( self.DeadlineTemp, "%s_plugin_info.job" % renderer.lower() )
        pluginContents = {}

        exportFilename = self.getExportFilename( renderer, take )
        if renderer == "Redshift":
            pluginContents["SceneFile"] = exportFilename
        else:
            pluginContents["InputFile"] = exportFilename

        if renderer == "Arnold":
            pluginContents["Threads"] = self.GetLong( self.dialogIDs[ "ExportThreadsBoxID" ] )
            pluginContents["CommandLineOptions"] = ""
            pluginContents["Verbose"] = 4

        self.writeInfoFile( exportPluginInfoFile, pluginContents )

        print( "Submitting %s standalone job" % renderer )
        c4d.StatusSetSpin()
        args = [ exportJobInfoFile, exportPluginInfoFile ]

        results = ""
        try:
            results = CallDeadlineCommand( args, useArgFile=True )
        except:
            results = "An error occurred while submitting the job to Deadline."
        
        print( results )
        return results

    def writeInfoFile( self, filename, fileContents ):
        """
        Creates a Deadline info file (job or plugin) at a specified filename using a dict containing the submission parameters
        :param filename: The path to the info file
        :param fileContents: A dictionary of submission key-value pairs to be written to the info file
        :return: None
        """
        # A list comprehension with a join statement on a newline doesn't work here, since we're mixing and matches types which
        # causes unicode decode issues. As such, iterating over the  items is the cleanest method that works in python 2 and 3.

        with open( filename, "wb" ) as fileHandle:
            for key, value in fileContents.items():
                fileHandle.write( "%s=%s\n" % ( key, value ) )

    def getExportFilename( self, renderer, take ):
        """
        Builds up the export filename based on the renderer and the current take
        :param renderer: The renderer used for the render
        :param take: The current take
        :return: A string containing the resulting filename
        """
        exportFilename = self.GetString( self.dialogIDs[ "ExportLocationBoxID" ] )

        if not os.path.isabs( exportFilename ):
            scene = documents.GetActiveDocument()
            scenePath = scene.GetDocumentPath()
            exportFilename = os.path.join( scenePath, exportFilename )

        exportFilename, extension = os.path.splitext( exportFilename )

        exportFilename = "%s_%s" % (exportFilename, take)
        if renderer != "Redshift":
            exportFilename += "."

        exportFilename += "0000"
        exportFilename += extension

        return exportFilename

    def WriteStickySettings( self ):
        print( "Writing sticky settings" )
        # Save sticky settings
        try:
            config = ConfigParser.ConfigParser()
            config.add_section( "Sticky" )

            config.set( "Sticky", "Department", self.GetString( self.dialogIDs[ "DepartmentBoxID" ] ) )
            config.set( "Sticky", "Pool", self.Pools[ self.GetLong( self.dialogIDs[ "PoolBoxID" ] ) ] )
            config.set( "Sticky", "SecondaryPool", self.SecondaryPools[ self.GetLong( self.dialogIDs[ "SecondaryPoolBoxID" ] ) ] )
            config.set( "Sticky", "Group", self.Groups[ self.GetLong( self.dialogIDs[ "GroupBoxID" ] ) ] )
            config.set( "Sticky", "Priority", str( self.GetLong( self.dialogIDs[ "PriorityBoxID" ] ) ) )
            config.set( "Sticky", "MachineLimit", str( self.GetLong( self.dialogIDs[ "MachineLimitBoxID" ] ) ) )
            config.set( "Sticky", "IsBlacklist", str( self.GetBool( self.dialogIDs[ "IsBlacklistBoxID" ] ) ) )
            config.set( "Sticky", "MachineList", self.GetString( self.dialogIDs[ "MachineListBoxID" ] ) )
            config.set( "Sticky", "ConcurrentTasks", str( self.GetLong( self.dialogIDs[ "ConcurrentTasksBoxID" ] ) ) )
            config.set( "Sticky", "LimitGroups", self.GetString( self.dialogIDs[ "LimitGroupsBoxID" ] ) )
            config.set( "Sticky", "SubmitSuspended", str( self.GetBool( self.dialogIDs[ "SubmitSuspendedBoxID" ] ) ) )
            config.set( "Sticky", "ChunkSize", str( self.GetLong( self.dialogIDs[ "ChunkSizeBoxID" ] ) ) )

            config.set( "Sticky", "IncludeMainTake", str( self.GetBool( self.dialogIDs[ "IncludeMainBoxID" ] ) ) )
            config.set( "Sticky", "UseTakeFrames", str( self.GetBool( self.dialogIDs[ "TakeFramesBoxID" ] ) ) )
            config.set( "Sticky", "SubmitScene", str( self.GetBool( self.dialogIDs[ "SubmitSceneBoxID" ] ) ) )
            config.set( "Sticky", "Threads", str( self.GetLong( self.dialogIDs[ "ThreadsBoxID" ] ) ) )
            config.set( "Sticky", "ExportProject", str( self.GetBool( self.dialogIDs[ "ExportProjectBoxID" ] ) ) )
            config.set( "Sticky", "Build", self.Builds[ self.GetLong( self.dialogIDs[ "BuildBoxID" ] ) ] )
            config.set( "Sticky", "LocalRendering", str( self.GetBool( self.dialogIDs[ "LocalRenderingBoxID" ] ) ) )
            config.set( "Sticky", "CloseOnSubmission", str( self.GetBool( self.dialogIDs[ "CloseOnSubmissionID" ] ) ) )
            config.set( "Sticky", "UseBatchPlugin", str( self.GetBool( self.dialogIDs[ "UseBatchBoxID" ] ) ) )

            config.set( "Sticky", "ExportJob", self.GetBool( self.dialogIDs[ "ExportJobID" ] ) )
            config.set( "Sticky", "ExportDependentJob", self.GetBool( self.dialogIDs[ "ExportDependentJobBoxID" ] ) )
            config.set( "Sticky", "LocalExport", self.GetBool( self.dialogIDs[ "ExportLocalID" ] ) )
            config.set( "Sticky", "ExportPool", self.Pools[ self.GetLong( self.dialogIDs[ "ExportPoolBoxID" ] ) ] )
            config.set( "Sticky", "ExportSecondaryPool", self.SecondaryPools[ self.GetLong( self.dialogIDs[ "ExportSecondaryPoolBoxID" ] ) ] )
            config.set( "Sticky", "ExportGroup", self.Groups[ self.GetLong( self.dialogIDs[ "ExportGroupBoxID" ] ) ] )
            config.set( "Sticky", "ExportPriority", str( self.GetLong( self.dialogIDs[ "ExportPriorityBoxID" ] ) ) )
            config.set( "Sticky", "ExportMachineLimit", str( self.GetLong( self.dialogIDs[ "ExportMachineLimitBoxID" ] ) ) )
            config.set( "Sticky", "ExportIsBlacklist", str( self.GetBool( self.dialogIDs[ "ExportIsBlacklistBoxID" ] ) ) )
            config.set( "Sticky", "ExportMachineList", self.GetString( self.dialogIDs[ "ExportMachineListBoxID" ] ) )
            config.set( "Sticky", "ExportLimitGroups", self.GetString( self.dialogIDs[ "ExportLimitGroupsBoxID" ] ) )
            config.set( "Sticky", "ExportSubmitSuspended", str( self.GetBool( self.dialogIDs[ "ExportSubmitSuspendedBoxID" ] ) ) )
            config.set( "Sticky", "ExportThreads", str( self.GetLong( self.dialogIDs[ "ExportThreadsBoxID" ] ) ) )
            config.set( "Sticky", "ExportOutputLocation", self.GetString( self.dialogIDs[ "ExportLocationBoxID" ] ) )

            config.set( "Sticky", "EnableRegionRendering", self.GetBool( self.dialogIDs[ "EnableRegionRenderingID" ] ) )
            config.set( "Sticky", "TilesInX", str( self.GetLong( self.dialogIDs[ "TilesInXID" ] ) ) )
            config.set( "Sticky", "TilesInY", str( self.GetLong( self.dialogIDs[ "TilesInYID" ] ) ) )
            config.set( "Sticky", "SingleFrameTileJob", self.GetBool( self.dialogIDs[ "SingleFrameTileJobID" ] ) )
            config.set( "Sticky", "SingleFrameJobFrame", str( self.GetLong( self.dialogIDs[ "SingleFrameJobFrameID" ] ) ) )
            config.set( "Sticky", "SubmitDependentAssembly", self.GetBool( self.dialogIDs[ "SubmitDependentAssemblyID" ] ) )
            config.set( "Sticky", "CleanupTiles", self.GetBool( self.dialogIDs[ "CleanupTilesID" ] ) )
            config.set( "Sticky", "ErrorOnMissingTiles", self.GetBool( self.dialogIDs[ "ErrorOnMissingTilesID" ] ) )
            config.set( "Sticky", "AssembleTilesOver", self.AssembleOver[ self.GetLong( self.dialogIDs[ "AssembleTilesOverID" ] ) ] )
            config.set( "Sticky", "BackgroundImage", self.GetString( self.dialogIDs[ "BackgroundImageID" ] ) )
            config.set( "Sticky", "ErrorOnMissingBackground", self.GetBool( self.dialogIDs[ "ErrorOnMissingBackgroundID" ] ) )

            config.set( "Sticky", "OutputOverride", self.GetString( self.dialogIDs[ "OutputOverrideID" ] ) )
            config.set( "Sticky", "OutputMultipassOverride", self.GetString( self.dialogIDs[ "OutputMultipassOverrideID" ] ) )

            config.set( "Sticky" ,"GPUsPerTask", self.GetLong( self.dialogIDs[ "GPUsPerTaskID" ] ) )
            config.set( "Sticky", "GPUsSelectDevices", self.GetString( self.dialogIDs[ "SelectGPUDevicesID" ] ) )
            
            with open( self.ConfigFile, "w" ) as fileHandle:
                config.write( fileHandle )
        except:
            print( "Could not write sticky settings:\n" + traceback.format_exc() )

    def renderOutputSanityCheck(self, scene, takes):
        """
        Make sure that render output is being saved and has a output defined. If multi-pass is enabled ensure it has
        output too.
        Check the following:
        If the output is set to be saved
        If the output has an output path set
        If there is an output path set, is the output path local

        If multi-pass is enabled do the same as above, but for the multi-pass output.

        Return a list of what's wrong.
        :param c4d.documents.BaseDocument -- scene: The scene to be submitted to Deadline
        :param String -- takes: The Cinema4D takes in the scene
        :return List: A list of warning messages related to render output
        """
        message = []

        def check_output_settings(save_image_container_id, output_path_container_id, is_multipass, take_name):
            """
            Check if the render output settings are in a good state and add any issues to the list of warning messages.

            Container ids can be found here (https://developers.maxon.net/docs/Cinema4DPythonSDK/html/modules/c4d.documents/RenderData/index.html)
            :param int -- save_image_container_id:
            :param int -- output_path_container_id:
            :param bool -- is_multipass: Whether or not we are checking multipass output
            :param String -- take_name: The name the take to check
            """
            # If the takes name is "" or None it's because takes aren't being used. No need to include takes in the
            # messaging at that point.
            take_message = ' in the "{}" take'.format(take_name) if take_name else ""
            message_prefix = ' multipass' if is_multipass else ""

            if not render_data.GetBool(save_image_container_id):
                message.append("The{} output image is not set to be saved{}.".format(message_prefix, take_message))
            else:
                output_path = render_data.GetFilename(output_path_container_id)

                if not output_path:
                    message.append("The{} output image does not have a path set{}.".format(message_prefix, take_message))
                elif IsPathLocal(output_path):
                    message.append(
                        "The{} output image path '{}'{} is local and may not be accessible by your render nodes.".format(message_prefix, output_path, take_message)
                    )

        for take in takes:
            render_data = self.GetRenderInfo(scene, take).GetData()
            check_output_settings(save_image_container_id=c4d.RDATA_SAVEIMAGE, output_path_container_id=c4d.RDATA_PATH,
                                  is_multipass=False, take_name=take)

            if render_data.GetBool(c4d.RDATA_MULTIPASS_ENABLE):
                check_output_settings(save_image_container_id=c4d.RDATA_MULTIPASS_SAVEIMAGE,
                                      output_path_container_id=c4d.RDATA_MULTIPASS_FILENAME, is_multipass=True,
                                      take_name=take)

        return message

    def SubmitJob( self ):
        jobName = self.GetString( self.dialogIDs[ "NameBoxID" ] )
        comment = self.GetString( self.dialogIDs[ "CommentBoxID" ] )
        department = self.GetString( self.dialogIDs[ "DepartmentBoxID" ] )
        
        pool = self.Pools[ self.GetLong( self.dialogIDs[ "PoolBoxID" ] ) ]
        secondaryPool = self.SecondaryPools[ self.GetLong( self.dialogIDs[ "SecondaryPoolBoxID" ] ) ]
        group = self.Groups[ self.GetLong( self.dialogIDs[ "GroupBoxID" ] ) ]
        priority = self.GetLong( self.dialogIDs[ "PriorityBoxID" ] )
        machineLimit = self.GetLong( self.dialogIDs[ "MachineLimitBoxID" ] )
        taskTimeout = self.GetLong( self.dialogIDs[ "TaskTimeoutBoxID" ] )
        autoTaskTimeout = self.GetBool( self.dialogIDs[ "AutoTimeoutBoxID" ] )
        concurrentTasks = self.GetLong( self.dialogIDs[ "ConcurrentTasksBoxID" ] )
        limitConcurrentTasks = self.GetBool( self.dialogIDs[ "LimitConcurrentTasksBoxID" ] )
        isBlacklist = self.GetBool( self.dialogIDs[ "IsBlacklistBoxID" ] )
        machineList = self.GetString( self.dialogIDs[ "MachineListBoxID" ] )
        limitGroups = self.GetString( self.dialogIDs[ "LimitGroupsBoxID" ] )
        dependencies = self.GetString( self.dialogIDs[ "DependenciesBoxID" ] )
        onComplete = self.OnComplete[ self.GetLong( self.dialogIDs[ "OnCompleteBoxID" ] ) ]
        submitSuspended = self.GetBool( self.dialogIDs[ "SubmitSuspendedBoxID" ] )

        activeTake = self.Takes[ self.GetLong( self.dialogIDs[ "TakesBoxID" ] ) ]
        IncludeMainTake = self.GetBool( self.dialogIDs[ "IncludeMainBoxID" ] )

        frames = self.GetString( self.dialogIDs[ "FramesBoxID" ] )
        useTakeFrames = self.GetBool( self.dialogIDs[ "TakeFramesBoxID" ] )
        frameStepEnabled = self.GetBool( self.dialogIDs[ "EnableFrameStepBoxID" ] )
        frameStep = 1
        chunkSize = self.GetLong( self.dialogIDs[ "ChunkSizeBoxID" ] )
        threads = self.GetLong( self.dialogIDs[ "ThreadsBoxID" ] )
        build = self.Builds[ self.GetLong( self.dialogIDs[ "BuildBoxID" ] ) ]
        submitScene = self.GetBool( self.dialogIDs[ "SubmitSceneBoxID" ] )
        exportProject = self.GetBool( self.dialogIDs[ "ExportProjectBoxID" ] )
        localRendering = self.GetBool( self.dialogIDs[ "LocalRenderingBoxID" ] )
        useBatchPlugin = self.GetBool( self.dialogIDs[ "UseBatchBoxID" ] )

        exportJob = self.GetBool( self.dialogIDs[ "ExportJobID" ] )
        if self.Exporters:
            exporter = self.Exporters[ self.GetLong( self.dialogIDs[ "ExportJobTypesID" ] ) ]
        dependentExport = self.GetBool( self.dialogIDs[ "ExportDependentJobBoxID" ] ) and exportJob
        localExport = self.GetBool( self.dialogIDs[ "ExportLocalID" ] ) and dependentExport
        exportFilename = self.GetString( self.dialogIDs[ "ExportLocationBoxID" ] )

        GPUsPerTask = self.GetLong( self.dialogIDs[ "GPUsPerTaskID" ] )
        GPUsSelectDevices = self.GetString( self.dialogIDs[ "SelectGPUDevicesID" ] )

        EnableRegionRendering = self.IsRegionRenderingEnabled()
        TilesInX = self.GetLong( self.dialogIDs[ "TilesInXID" ] )
        TilesInY = self.GetLong( self.dialogIDs[ "TilesInYID" ] )
        SingleFrameTileJob = self.GetBool( self.dialogIDs[ "SingleFrameTileJobID" ] )
        SingleFrameJobFrame = self.GetLong( self.dialogIDs[ "SingleFrameJobFrameID" ] )
        SubmitDependentAssembly = self.GetBool( self.dialogIDs[ "SubmitDependentAssemblyID" ] )
        CleanupTiles = self.GetBool( self.dialogIDs[ "CleanupTilesID" ] )
        ErrorOnMissingTiles = self.GetBool( self.dialogIDs[ "ErrorOnMissingTilesID" ] )
        AssembleTilesOver = self.AssembleOver[ self.GetLong( self.dialogIDs[ "AssembleTilesOverID" ] ) ]
        BackgroundImage = self.GetString( self.dialogIDs[ "BackgroundImageID" ] )
        ErrorOnMissingBackground = self.GetBool( self.dialogIDs[ "ErrorOnMissingBackgroundID" ] )

        regionJobCount = 1
        regionOutputCount = 1
        if EnableRegionRendering and not SingleFrameTileJob:
            regionJobCount = TilesInX * TilesInY
        if EnableRegionRendering and SingleFrameTileJob:
            regionOutputCount = TilesInX * TilesInY
        
        warningMessages = []
        errorMessages = []
        
        scene = documents.GetActiveDocument()
        sceneName = scene.GetDocumentName()
        scenePath = scene.GetDocumentPath()
        sceneFilename = os.path.join( scenePath, sceneName )
        takesToRender = self.getTakesToRender(activeTake)

        if IsPathLocal( sceneFilename) and not submitScene:
            warningMessages.append("The c4d file %s is local and is not being submitted with the Job." %sceneFilename)

        warningMessages.extend(self.renderOutputSanityCheck(scene, takesToRender))
        
        if exportJob:
            if exportFilename == "":
                errorMessages.append("Export file location is blank. No scene files will be exported.")
            if exporter == "Arnold":
                if not hasArnoldDriver():
                    warningMessages.append("The scene file does not contain an Arnold Driver node. The Arnold Scene created will not produce any Output.")
                
        if EnableRegionRendering and TilesInX * TilesInY > self.TaskLimit and SingleFrameTileJob:
            errorMessages.append("Unable to submit a job with more tasks (%s) than the task limit (%s). Adjust 'Tiles In X' and 'Tiles In Y' so that their product is less than or equal to the task limit." % ( TilesInX * TilesInY, self.TaskLimit ))

        if frameStepEnabled and not ( EnableRegionRendering and SingleFrameTileJob ):
            if "," in frames:
                errorMessages.append("Unable to submit non contiguous frame ranges when submitting all frames as a single task.")
            else:
                match = re.search( "x(\\d+)", frames )
                if match is not None:
                    frameStep = int(match.group(1))
                    frames = re.sub( "x\\d+", "", frames)
        
        if errorMessages:
            errorMessages.insert(0, "The following errors were detected:\n")
            errorMessages.append("\nPlease fix these issues and submit again.")
            gui.MessageDialog("\n".join(errorMessages))
            return False
        
        if warningMessages:
            warningMessages.insert(0, "The following warnings were detected:\n")
            warningMessages.append("\nDo you still wish to submit this job to Deadline?")
            if not gui.QuestionDialog("\n".join(warningMessages)):
                return False
        
        groupBatch = ((EnableRegionRendering and SubmitDependentAssembly) or
                      (dependentExport and not localExport) or
                      (len(takesToRender) > 1))
        
        c4dMajorVersion = c4d.GetC4DVersion() / 1000
        scene = documents.GetActiveDocument()
        renderData = scene.GetActiveRenderData().GetData()
        framesPerSecond = renderData.GetReal( c4d.RDATA_FRAMERATE )
        successes = 0
        failures = 0
        # Loop through the list of takes and submit them all
        for take in takesToRender:
            jobIds = []
            submissionSuccess = 0
            exportFilename = ""
            if exportJob:
                exportFilename = self.GetString( self.dialogIDs[ "ExportLocationBoxID" ] )
                exportFilename, extension = os.path.splitext( exportFilename )
                exportFilename = "%s_%s" % ( exportFilename, take )
                
                if exporter == "Arnold":
                    exportFilename += ".####"
                
                exportFilename += extension

            for jobRegNum in xrange( regionJobCount ):
                if exportProject:
                    scene = documents.GetActiveDocument()
                    sceneName = scene.GetDocumentName()
                    originalSceneFilename = os.path.join( scene.GetDocumentPath(), sceneName )
                    
                    print( "Exporting scene" )
                    c4d.StatusSetSpin()
                    c4d.CallCommand( 12255 )
                    c4d.StatusClear()
                    
                    scene = documents.GetActiveDocument()
                    sceneName = scene.GetDocumentName()
                    newSceneFilename = os.path.join( scene.GetDocumentPath(), sceneName )
                    
                    # If the scene file name hasn't changed, that means that they canceled the export dialog.
                    if newSceneFilename == originalSceneFilename:
                        return False
                    
                    submitScene = False # can't submit scene if it's being exported
                
                scene = documents.GetActiveDocument()
                sceneName = scene.GetDocumentName()
                scenePath = scene.GetDocumentPath()
                sceneFilename = os.path.join( scenePath, sceneName )
                renderInfo = self.GetRenderInfo( scene, take )
                renderData = renderInfo.GetData()
                
                saveOutput = renderData.GetBool( c4d.RDATA_SAVEIMAGE )
                outputPath = renderData.GetFilename( c4d.RDATA_PATH )
                outputOverride = self.GetString( self.dialogIDs[ "OutputOverrideID" ] ).strip()
                if self.IsOutputOverrideEnabled() and len( outputOverride ) > 0:
                    outputPath = outputOverride

                if not os.path.isabs( outputPath ):
                    outputPath = os.path.join( scenePath, outputPath )

                outputFormat = renderData.GetLong( c4d.RDATA_FORMAT )
                outputNameFormat = renderData.GetLong( c4d.RDATA_NAMEFORMAT )
                alphaEnabled = renderData.GetBool( c4d.RDATA_ALPHACHANNEL )
                separateAlpha = renderData.GetBool( c4d.RDATA_SEPARATEALPHA )

                saveMP = renderData.GetBool( c4d.RDATA_MULTIPASS_ENABLE ) and renderData.GetBool( c4d.RDATA_MULTIPASS_SAVEIMAGE )
                mpPath = renderData.GetFilename( c4d.RDATA_MULTIPASS_FILENAME )
                outputMultipassOverride = self.GetString( self.dialogIDs[ "OutputMultipassOverrideID" ] ).strip()
                if len( outputMultipassOverride ) > 0:
                    mpPath = outputMultipassOverride

                if not os.path.isabs( mpPath ):
                    mpPath = os.path.join( scenePath, mpPath )

                mpFormat = renderData.GetLong( c4d.RDATA_MULTIPASS_SAVEFORMAT )
                mpSuffix = renderData.GetBool( c4d.RDATA_MULTIPASS_SUFFIX )
                mpUsers = False
                try:
                    mpUsers = renderData.GetBool( c4d.RDATA_MULTIPASS_USERNAMES )
                except:
                    pass
                width = renderData.GetLong( c4d.RDATA_XRES )
                height = renderData.GetLong( c4d.RDATA_YRES )
                
                if not localExport:
                    print( "Creating C4D submit info file" )
                    jobInfoFile = os.path.join( self.DeadlineTemp, "c4d_submit_info.job" )

                    tempJobName = jobName
                    if not take == "Main" and not take == "":
                        tempJobName += " - " + take

                    if EnableRegionRendering and not SingleFrameTileJob:
                        tempJobName += " - Region " + str( jobRegNum )

                    jobContents = {
                        "Plugin": "Cinema4D",
                        "Name": tempJobName,
                        "Comment": comment,
                        "Department": department,
                        "Group": group,
                        "Pool": pool,
                        "SecondaryPool": "",
                        "Priority": priority,
                        "MachineLimit": machineLimit,
                        "TaskTimeoutMinutes": taskTimeout,
                        "EnableAutoTimeout": autoTaskTimeout,
                        "ConcurrentTasks": concurrentTasks,
                        "LimitConcurrentTasksToNumberOfCpus": limitConcurrentTasks,
                        "LimitGroups": limitGroups,
                        "JobDependencies": dependencies,
                        "OnJobComplete": onComplete,
                    }

                    if groupBatch:
                        jobContents["BatchName"] = jobName

                    if useBatchPlugin and c4dMajorVersion >= 15:
                        jobContents["Plugin"] = "Cinema4DBatch"

                    # If it's not a space, then a secondary pool was selected.
                    if secondaryPool != " ":
                        jobContents["SecondaryPool"] = secondaryPool

                    if EnableRegionRendering and SingleFrameTileJob and not exportJob:
                        jobContents["TileJob"] = True
                        jobContents["TileJobFrame"] = SingleFrameJobFrame
                        jobContents["TileJobTilesInX"] = TilesInX
                        jobContents["TileJobTilesInY"] = TilesInY
                    else:
                        if useTakeFrames:
                            startFrame = renderData.GetTime( c4d.RDATA_FRAMEFROM ).GetFrame( framesPerSecond )
                            endFrame = renderData.GetTime( c4d.RDATA_FRAMETO ).GetFrame( framesPerSecond )
                            takeFrames = "%s-%s" % ( startFrame, endFrame )
                            jobContents[ "Frames" ] = takeFrames
                        else:
                            jobContents["Frames"] = frames

                        if frameStepEnabled:
                            jobContents["ChunkSize"] = 10000
                        else:
                            jobContents["ChunkSize"] = chunkSize

                    if submitSuspended:
                        jobContents["InitialStatus"] = "Suspended"

                    if isBlacklist:
                        jobContents["Blacklist"] = machineList
                    else:
                        jobContents["Whitelist"] = machineList

                    outputFilenameLine = False
                    outputDirectoryLine = False
                    outputFileCount = 0

                    if not exportJob:
                        for outputRegNum in xrange( regionOutputCount ):
                            regionPrefix = ""
                            if EnableRegionRendering:
                                if SingleFrameTileJob:
                                    regionPrefix = "_Region_%s_" % outputRegNum
                                else:
                                    regionPrefix = "_Region_%s_" % jobRegNum

                            if saveOutput and outputPath != "":
                                outputFilename = self.GetOutputFileName( outputPath, outputFormat, outputNameFormat, take, regionPrefix=regionPrefix )
                                if outputFilename:
                                    jobContents["OutputFilename%s" % outputFileCount] = outputFilename
                                    outputFileCount += 1
                                    if alphaEnabled and separateAlpha:
                                        tempOutputFolder, tempOutputFile = os.path.split(outputFilename)

                                        jobContents["OutputFilename%s" % outputFileCount] =  os.path.join( tempOutputFolder, "A_"+tempOutputFile )
                                        outputFileCount += 1
                                else:
                                    jobContents[ "OutputDirectory%s" % outputFileCount ] = os.path.dirname( outputPath )
                                    outputFileCount += 1

                            if saveMP and mpPath:
                                if self.isSingleMultipassFile( renderData ):
                                    mpFilename = self.GetOutputFileName( mpPath, mpFormat, outputNameFormat, take, isMulti = True, regionPrefix=regionPrefix )
                                    if mpFilename:
                                        jobContents["OutputFilename%s" % outputFileCount] = mpFilename
                                    else:
                                        jobContents[ "OutputDirectory%s" % outputFileCount ] = os.path.dirname( mpPath )

                                    outputFileCount += 1
                                else:
                                    for mPass, postEffect in self.getEachMultipass( take ):
                                        mpFilename = self.GetOutputFileName( mpPath, mpFormat, outputNameFormat, take, isMulti=True, mpass=mPass, mpassSuffix=mpSuffix, mpUsers=mpUsers,
                                                                             regionPrefix=regionPrefix, postEffect=postEffect )
                                        if mpFilename:
                                            jobContents[ "OutputFilename%s" % outputFileCount ] = mpFilename
                                        else:
                                            jobContents[ "OutputDirectory%s" % outputFileCount ] = os.path.dirname( mpPath )
                                        outputFileCount += 1
                    else:
                        if not os.path.isabs( exportFilename ):
                            scenePath = scene.GetDocumentPath()
                            exportFilename = os.path.join( scenePath, exportFilename )

                        jobContents[ "OutputDirectory%s" % outputFileCount ] = os.path.dirname( exportFilename )

                    self.writeInfoFile( jobInfoFile, jobContents )

                    if not ( EnableRegionRendering and SubmitDependentAssembly ):
                        self.ConcatenatePipelineSettingsToJob( jobInfoFile, jobName )

                    print( "Creating C4D plugin info file" )
                    renderer = self.getRenderer( scene, take )
                    pluginInfoFile = os.path.join( self.DeadlineTemp, "c4d_plugin_info.job" )

                    pluginContents = {
                        "Version": c4dMajorVersion,
                        "Build": build,
                        "Threads": threads,
                        "Width": width,
                        "Height": height,
                        "LocalRendering": localRendering,
                        "Take": take,
                        "RegionRendering": EnableRegionRendering,
                        "HasTexturePaths": True,
                    }

                    if not submitScene:
                        pluginContents["SceneFile"] = sceneFilename

                    if self.IsGPUAffinityOverrideEnabled():
                        pluginContents["GPUsPerTask"] = GPUsPerTask
                        pluginContents["GPUsSelectDevices"] = GPUsSelectDevices

                    if exportJob:
                        pluginContents["Renderer"] = "%sExport" % exporter
                        pluginContents["ExportFile"] = exportFilename
                    else:
                        if renderer:
                            pluginContents["Renderer"] = renderer
                        if EnableRegionRendering:
                            if SingleFrameTileJob:
                                for outputRegNum in xrange( regionOutputCount ):
                                    tile_region = compute_tile_region(outputRegNum,
                                                                      TilesInX,
                                                                      TilesInY,
                                                                      height,
                                                                      width,
                                                                      renderer)

                                    pluginContents["RegionLeft%s" % outputRegNum] = tile_region.left
                                    pluginContents["RegionRight%s" % outputRegNum] = tile_region.right
                                    pluginContents["RegionTop%s" % outputRegNum] = tile_region.top
                                    pluginContents["RegionBottom%s" % outputRegNum] = tile_region.bottom

                                    if saveOutput and outputPath:
                                        path, prefix = os.path.split( outputPath )
                                        extlessPrefix, tempOutputExtension = os.path.splitext( prefix )
                                        pluginContents["FilePath"] = path
                                        pluginContents["RegionPrefix%s" % outputRegNum] = "%s_region_%s_" % (extlessPrefix, outputRegNum)

                                    if saveMP and mpPath:
                                        path, prefix = os.path.split( mpPath )
                                        extlessPrefix, tempOutputExtension = os.path.splitext( prefix )
                                        pluginContents["MultiFilePath"] = path
                                        pluginContents["MultiFileRegionPrefix%s" % outputRegNum] = "%s_region_%s_" % (extlessPrefix, outputRegNum )
                            else:
                                tile_region = compute_tile_region(jobRegNum,
                                                                  TilesInX,
                                                                  TilesInY,
                                                                  height,
                                                                  width,
                                                                  renderer)

                                pluginContents["RegionLeft"] = tile_region.left
                                pluginContents["RegionRight"] = tile_region.right
                                pluginContents["RegionTop"] = tile_region.top
                                pluginContents[ "RegionBottom" ] = tile_region.bottom

                                if saveOutput and outputPath:
                                    path, prefix = os.path.split( outputPath )
                                    extlessPrefix, tempOutputExtension = os.path.splitext( prefix )
                                    pluginContents["FilePath"] = path
                                    pluginContents["FilePrefix"] = "%s_region_%s_" % ( extlessPrefix, jobRegNum )

                                if saveMP and mpPath:
                                    path, prefix = os.path.split( mpPath )
                                    extlessPrefix, tempOutputExtension = os.path.splitext( prefix )
                                    pluginContents["MultiFilePath"] = path
                                    pluginContents["MultiFilePrefix"] = "%s_region_%s_" % ( extlessPrefix, jobRegNum )
                        else:
                            if saveOutput and outputPath:
                                head, tail = os.path.split( outputPath )
                                pluginContents["FilePath"] = head
                                pluginContents["FilePrefix"] = tail

                            if saveMP and mpPath:
                                head, tail = os.path.split( mpPath )
                                pluginContents["MultiFilePath"] = head
                                pluginContents["MultiFilePrefix"] = tail

                    if frameStepEnabled:
                        pluginContents["EnableFrameStep"] = True
                        pluginContents["FrameStep"] = frameStep

                    # Add the texture search paths, if they exist
                    for index, path in enumerate( self.getTextureSearchPaths() ):
                        pluginContents[ "TexturePath%s" % index ] = path

                    self.writeInfoFile( pluginInfoFile, pluginContents )

                    print( "Submitting job" )
                    c4d.StatusSetSpin()

                    args = [ jobInfoFile, pluginInfoFile ]
                    if submitScene:
                        args.append( sceneFilename )
                    
                    results = ""
                    try:
                        results = CallDeadlineCommand( args, useArgFile=True )
                        submissionSuccess += 1
                    except:
                        results = "An error occurred while submitting the job to Deadline."
                    
                    print( results )
                    
                    successfulSubmission = ( results.find( "Result=Success" ) != -1 )
                    
                    if successfulSubmission:
                        successes+=1
                        jobId = ""
                        resultArray = results.split()
                        for line in resultArray:
                            if line.startswith("JobID="):
                                jobId = line.replace("JobID=","")
                                break
                        if not jobId == "":
                            jobIds.append( jobId )
                    else:
                        failures+=1
                # Local Export
                elif localExport:
                    if take != "":
                        selectTake = self.GetTakeFromName( take )
                        scene.GetTakeData().SetCurrentTake( selectTake )

                    numExports = 1

                    if useTakeFrames:
                        startFrame = renderData.GetTime( c4d.RDATA_FRAMEFROM ).GetFrame( framesPerSecond )
                        endFrame = renderData.GetTime( c4d.RDATA_FRAMETO ).GetFrame( framesPerSecond )
                    else:
                        parsedFrameList = CallDeadlineCommand( [ "-ParseFrameList", self.GetString( self.dialogIDs[ "FramesBoxID" ] ), "False" ] ).strip()
                        parsedFrameList = parsedFrameList.split( "," )
                        numExports = len( parsedFrameList )

                    for i in xrange( 0, numExports ):
                        if not useTakeFrames:
                            startFrame = int( parsedFrameList[i] )
                            endFrame = int ( parsedFrameList[i] )

                        if exporter == "Arnold":
                            options = c4d.BaseContainer()
                            options.SetInt32( 6, startFrame )
                            options.SetInt32( 7, endFrame )

                            options.SetFilename( 0, exportFilename )
                            
                            scene.GetSettingsInstance( c4d.DOCUMENTSETTINGS_DOCUMENT ).SetContainer( SubmitC4DToDeadlineDialog.ARNOLD_ASS_EXPORT, options )
                         
                            c4d.CallCommand( SubmitC4DToDeadlineDialog.ARNOLD_ASS_EXPORT )

                        elif exporter == "Redshift":
                            plug = c4d.plugins.FindPlugin( SubmitC4DToDeadlineDialog.REDSHIFT_EXPORT_PLUGIN_ID, c4d.PLUGINTYPE_SCENESAVER )

                            op = {}
                            plug.Message( c4d.MSG_RETRIEVEPRIVATEDATA, op )
                            imexporter = op[ "imexporter" ]
                            imexporter[ c4d.REDSHIFT_PROXYEXPORT_AUTOPROXY_CREATE ] = False
                            imexporter[ c4d.REDSHIFT_PROXYEXPORT_ANIMATION_RANGE ] = c4d.REDSHIFT_PROXYEXPORT_ANIMATION_RANGE_MANUAL
                            imexporter[ c4d.REDSHIFT_PROXYEXPORT_ANIMATION_FRAME_START ] = startFrame
                            imexporter[ c4d.REDSHIFT_PROXYEXPORT_ANIMATION_FRAME_END ] = endFrame
                            imexporter[ c4d.REDSHIFT_PROXYEXPORT_ANIMATION_FRAME_STEP ] = 1

                            documents.SaveDocument(scene, exportFilename, c4d.SAVEDOCUMENTFLAGS_0, SubmitC4DToDeadlineDialog.REDSHIFT_EXPORT_PLUGIN_ID)

                if dependentExport:
                    results = self.SubmitDependentExportJob( exporter, jobIds, groupBatch, take )

                    successfulSubmission = ( results.find( "Result=Success" ) != -1 )
                    if successfulSubmission:
                        successes+=1
                        jobId = ""
                        resultArray = results.split()
                        for line in resultArray:
                            if line.startswith( "JobID=" ):
                                jobId = line.replace( "JobID=", "" )
                                break
                        if not jobId == "":
                            jobIds.append( jobId )
                    else:
                        failures+=1

            if EnableRegionRendering and SubmitDependentAssembly:
                if SingleFrameTileJob:
                    
                    configFiles = []
                    outputFiles = []
                    
                    paddedFrame = str(SingleFrameJobFrame)
                    while len( paddedFrame ) < 4:
                        paddedFrame = "0" + paddedFrame
                    
                    if saveOutput and outputPath:
                        configFiles.append( self.createDTAConfigFile( SingleFrameJobFrame, renderData, outputPath, outputFormat, outputNameFormat, take )  )
                        outputFile = self.GetOutputFileName( outputPath, outputFormat, outputNameFormat, take )
                        outputFiles.append( outputFile.replace( "####", paddedFrame )  )
                        
                        if alphaEnabled and separateAlpha:
                            configFiles.append( self.createDTAConfigFile( SingleFrameJobFrame, renderData, outputPath, outputFormat, outputNameFormat, take, isAlpha=True )  )
                            outputFile = self.GetOutputFileName( outputPath, outputFormat, outputNameFormat, take )
                            tempOutputFolder, tempOutputFile = os.path.split( outputFile )
                            outputFile = os.path.join( tempOutputFolder, "A_"+tempOutputFile )
                            outputFiles.append( outputFile.replace( "####", paddedFrame )  )
                        
                    if saveMP and mpPath:
                        if self.isSingleMultipassFile( renderData ):
                            configFiles.append( self.createDTAConfigFile( SingleFrameJobFrame, renderData, mpPath, mpFormat, outputNameFormat, take, isMulti=True )  )
                            outputFile = self.GetOutputFileName( mpPath, mpFormat, outputNameFormat, take, isMulti=True )
                            outputFiles.append( outputFile.replace( "####", paddedFrame )  )
                        else:
                            for mPass, postEffect in self.getEachMultipass( take ):
                                configFiles.append(
                                    self.createDTAConfigFile( SingleFrameJobFrame, renderData, mpPath, mpFormat, outputNameFormat, take, isMulti=True, mpass=mPass, mpassSuffix=mpSuffix,
                                                              mpUsers=mpUsers, postEffect=postEffect ) )
                                outputFile = self.GetOutputFileName( mpPath, mpFormat, outputNameFormat, take, isMulti=True, mpass=mPass, mpassSuffix=mpSuffix, mpUsers=mpUsers, postEffect=postEffect )
                                outputFiles.append( outputFile.replace( "####", paddedFrame ) )
                    
                    if self.submitDependentAssemblyJob( outputFiles, configFiles, successes + failures, jobIds ):
                        successes +=1
                    else:
                        failures += 1
                else:
                    frameListString = CallDeadlineCommand( [ "-ParseFrameList", self.GetString( self.dialogIDs[ "FramesBoxID" ] ), "False" ] ).strip()
                    frameList = frameListString.split( ",")
                    
                    if saveOutput and outputPath:
                        configFiles = []
                        outputFiles = []
                        for frame in frameList:
                            configFiles.append( self.createDTAConfigFile( frame, renderData, outputPath, outputFormat, outputNameFormat, take )  )
                            
                        outputFile = self.GetOutputFileName( outputPath, outputFormat, outputNameFormat, take )
                        outputFiles.append( outputFile )
                        
                        if self.submitDependentAssemblyJob( outputFiles, configFiles, successes + failures, jobIds ):
                            successes +=1
                        else:
                            failures += 1
                                                        
                        if alphaEnabled and separateAlpha:
                            
                            configFiles = []
                            outputFiles = []
                            for frame in frameList:
                                configFiles.append( self.createDTAConfigFile( frame, renderData, outputPath, outputFormat, outputNameFormat, take, isAlpha=True )  )
                                
                            outputFile = self.GetOutputFileName( outputPath, outputFormat, outputNameFormat, take )
                            tempOutputFolder, tempOutputFile = os.path.split( outputFile )
                            outputFile = os.path.join( tempOutputFolder, "A_"+tempOutputFile )
                            outputFiles.append( outputFile )
                            
                            if self.submitDependentAssemblyJob( outputFiles, configFiles, successes + failures, jobIds ):
                                successes +=1
                            else:
                                failures += 1
                        
                        if saveMP and mpPath:
                            if self.isSingleMultipassFile( renderData ):
                                configFiles = []
                                outputFiles = []
                                
                                for frame in frameList:
                                    configFiles.append( self.createDTAConfigFile( frame, renderData, mpPath, mpFormat, outputNameFormat, take, isMulti = True )  )
                                outputFile = self.GetOutputFileName( mpPath, mpFormat, outputNameFormat, take, isMulti = True )
                                outputFiles.append( outputFile )
                                
                                if self.submitDependentAssemblyJob( outputFiles, configFiles, successes + failures, jobIds ):
                                    successes +=1
                                else:
                                    failures += 1
                            else:

                                for mPass, postEffect in self.getEachMultipass( take ):
                                    configFiles = []
                                    outputFiles = []
                                    for frame in frameList:
                                        configFiles.append(
                                            self.createDTAConfigFile( frame, renderData, mpPath, mpFormat, outputNameFormat, take, isMulti=True, mpass=mPass, mpassSuffix=mpSuffix, mpUsers=mpUsers,
                                                                      postEffect=postEffect ) )
                                    outputFile = self.GetOutputFileName( mpPath, mpFormat, outputNameFormat, take, isMulti=True, mpass=mPass, mpassSuffix=mpSuffix, mpUsers=mpUsers,
                                                                         postEffect=postEffect )
                                    outputFiles.append( outputFile )

                                    if self.submitDependentAssemblyJob( outputFiles, configFiles, successes + failures, jobIds ):
                                        successes += 1
                                    else:
                                        failures += 1
                                       
                                       
        c4d.StatusClear()
        if successes + failures == 1:
            gui.MessageDialog( results )
        elif successes + failures > 1:
            gui.MessageDialog( "Submission Results\n\nSuccesses: " + str(successes) + "\nFailures: " + str(failures) + "\n\nSee script console for more details" )
        else:
            gui.MessageDialog( "Submission Failed. No takes selected." )
            return False
        
        return True

    def getTakesToRender(self, activeTake):
        """
        Determine which takes in the scene to render. If 'All' is selected render all of the takes in the scene. If
        'Marked' is selected then render all of the checked of takes in the scene. Else render the take that's selected
        in the drop down.
        :param String -- activeTake: The currently selected take in the scene
        :return List: A list of the takes to render.
        """
        takesToRender = []
        # If takes is set to All, remove All and Main from list
        if self.Takes[self.GetLong(self.dialogIDs["TakesBoxID"])] == "All":
            self.Takes.remove("All")
            self.Takes.remove(" ")

            # This will only fail in C4D R17 without a service pack
            try:
                self.Takes.remove("Marked")
            except:
                pass

            if not self.GetBool(self.dialogIDs["IncludeMainBoxID"]):
                self.Takes.remove("Main")
            takesToRender = self.Takes  # Set takesToRender to the remaining takes
        elif self.Takes[self.GetLong(self.dialogIDs["TakesBoxID"])] == "Marked":
            # Set Takes setting
            takesToRender = []
            doc = documents.GetActiveDocument()
            takeData = doc.GetTakeData()
            take = takeData.GetMainTake()

            while take:
                name = take.GetName()
                if take.IsChecked() and name not in takesToRender:
                    takesToRender.append(name)

                take = GetNextObject(take)
        else:
            if activeTake == " ":
                activeTake = ""
            takesToRender.append(activeTake)
        return takesToRender

    def isSingleMultipassFile( self, renderData ):
        """
        Determine whether or not multipass renders will be saved into a single multilayer file or multiple individual files.
        :param renderData: The render settings object that we are pulling information from.
        :return: Whether a single file will be rendered or not.
        """

        mpFormat = renderData.GetLong( c4d.RDATA_MULTIPASS_SAVEFORMAT )
        mpOneFile = renderData.GetBool( c4d.RDATA_MULTIPASS_SAVEONEFILE )

        #Only B3D, PSD, PSB, TIF, and EXR files can be saved as a single image.
        return mpOneFile and mpFormat in ( c4d.FILTER_B3D, c4d.FILTER_PSD, c4d.FILTER_PSB, c4d.FILTER_TIF_B3D, c4d.FILTER_TIF, c4d.FILTER_EXR )

    
    # This is called when a user clicks on a button or changes the value of a field.
    def Command( self, id, msg ):
        # The Limit Group browse button was pressed.
        if id == self.dialogIDs[ "LimitGroupsButtonID" ]:
            c4d.StatusSetSpin()
            
            currLimitGroups = self.GetString( self.dialogIDs[ "LimitGroupsBoxID" ] )
            result = CallDeadlineCommand( ["-selectlimitgroups",currLimitGroups], hideWindow=False )
            result = result.replace( "\n", "" ).replace( "\r", "" )
            
            if result != "Action was cancelled by user":
                self.SetString( self.dialogIDs[ "LimitGroupsBoxID" ], result )
            
            c4d.StatusClear()
        
        # The Dependencies browse button was pressed.
        elif id == self.dialogIDs[ "DependenciesButtonID" ]:
            c4d.StatusSetSpin()
            
            currDependencies = self.GetString( self.dialogIDs[ "DependenciesBoxID" ] )
            result = CallDeadlineCommand( ["-selectdependencies",currDependencies], hideWindow=False )
            result = result.replace( "\n", "" ).replace( "\r", "" )
            
            if result != "Action was cancelled by user":
                self.SetString( self.dialogIDs[ "DependenciesBoxID" ], result )
            
            c4d.StatusClear()
        
        elif id == self.dialogIDs[ "MachineListButtonID" ]:
            c4d.StatusSetSpin()
            
            currMachineList = self.GetString( self.dialogIDs[ "MachineListBoxID" ] )
            result = CallDeadlineCommand( ["-selectmachinelist",currMachineList], hideWindow=False )
            result = result.replace( "\n", "" ).replace( "\r", "" )
            
            if result != "Action was cancelled by user":
                self.SetString( self.dialogIDs[ "MachineListBoxID" ], result )
            
            c4d.StatusClear()
        
        elif id == self.dialogIDs[ "ExportProjectBoxID" ]:
            self.Enable( self.dialogIDs[ "SubmitSceneBoxID" ], not self.GetBool( self.dialogIDs[ "ExportProjectBoxID" ] ) )
        
        elif id == self.dialogIDs[ "EnableFrameStepBoxID" ]:
            self.EnableFrameStep()

        elif id == self.dialogIDs[ "OutputOverrideButtonID" ]:
            c4d.StatusSetSpin()
            try:
                currTemplate = self.GetString( self.dialogIDs[ "OutputOverrideID" ] )
                if not os.path.isabs( currTemplate ):
                    scenePath = documents.GetActiveDocument().GetDocumentPath()
                    currTemplate = os.path.join( scenePath, currTemplate )

                result = CallDeadlineCommand( [ "-SelectFilenameSave", currTemplate ] )
                if result != "Action was cancelled by user" and result != "":
                    self.SetString( self.dialogIDs[ "OutputOverrideID" ], result )
            finally:
                c4d.StatusClear()

        elif id == self.dialogIDs[ "OutputMultipassOverrideButtonID" ]:
            c4d.StatusSetSpin()
            try:
                currTemplate = self.GetString( self.dialogIDs[ "OutputMultipassOverrideID" ] )
                if not os.path.isabs( currTemplate ):
                    scenePath = documents.GetActiveDocument().GetDocumentPath()
                    currTemplate = os.path.join( scenePath, currTemplate )
                
                result = CallDeadlineCommand( [ "-SelectFilenameSave", currTemplate ] )
                if result != "Action was cancelled by user" and result != "":
                    self.SetString( self.dialogIDs[ "OutputMultipassOverrideID" ], result )
            finally:
                c4d.StatusClear()

        elif id == self.dialogIDs[ "UseBatchBoxID" ]:
            self.EnableRegionRendering()
        
        elif id == self.dialogIDs[ "EnableRegionRenderingID" ]:
            self.EnableRegionRendering()
        
        elif id == self.dialogIDs[ "SingleFrameTileJobID" ]:
            self.IsSingleFrameTileJob()
        
        elif id == self.dialogIDs[ "AssembleTilesOverID" ]:
            self.AssembleOverChanged()
        
        elif id == self.dialogIDs[ "BackgroundImageButtonID" ]:
            backgroundImage = c4d.storage.LoadDialog( type=c4d.FILESELECTTYPE_IMAGES, title="Background Image" )
            if backgroundImage is not None:
                self.SetString(self.dialogIDs[ "BackgroundImageID" ], backgroundImage )
                
        elif id == self.dialogIDs[ "ExportJobID" ]:
            self.EnableExportFields()
            self.EnableOutputOverrides()

        elif id == self.dialogIDs[ "ExportDependentJobBoxID" ]:
            self.EnableDependentExportFields()

        elif id == self.dialogIDs[ "ExportMachineListButtonID" ]:
            c4d.StatusSetSpin()
            
            currMachineList = self.GetString( self.dialogIDs[ "ExportMachineListBoxID" ] )
            result = CallDeadlineCommand( ["-selectmachinelist",currMachineList], hideWindow=False )
            result = result.replace( "\n", "" ).replace( "\r", "" )
            
            if result != "Action was cancelled by user":
                self.SetString( self.dialogIDs[ "ExportMachineListBoxID" ], result )
            
            c4d.StatusClear()

        elif id == self.dialogIDs[ "ExportLimitGroupsButtonID" ]:
            c4d.StatusSetSpin()
            
            currLimitGroups = self.GetString( self.dialogIDs[ "ExportLimitGroupsBoxID" ] )
            result = CallDeadlineCommand( ["-selectlimitgroups",currLimitGroups], hideWindow=False )
            result = result.replace( "\n", "" ).replace( "\r", "" )
            
            if result != "Action was cancelled by user":
                self.SetString( self.dialogIDs[ "ExportLimitGroupsBoxID" ], result )
            
            c4d.StatusClear()

        elif id == self.dialogIDs[ "ExportLocationButtonID" ]:
            c4d.StatusSetSpin()
            exporter = self.Exporters[ self.GetLong( self.dialogIDs[ "ExportJobTypesID" ] ) ]
            exportFileType = self.exportFileTypeDict[exporter]

            try:
                currTemplate = self.GetString( self.dialogIDs[ "ExportLocationBoxID" ] )
                result = CallDeadlineCommand( ["-SelectFilenameSave", currTemplate, exportFileType] )
                
                if result != "Action was cancelled by user" and result != "":
                    self.SetString( self.dialogIDs[ "ExportLocationBoxID" ], result )
            finally:
                c4d.StatusClear()
        
        elif id == self.dialogIDs[ "UnifiedIntegrationButtonID" ]:
            self.OpenIntegrationWindow()

        # The Submit or the Cancel button was pressed.
        elif id == self.dialogIDs[ "SubmitButtonID" ] or id == self.dialogIDs[ "CancelButtonID" ]:
            self.WriteStickySettings()

            # Close the dialog if the Cancel button was clicked
            if id == self.dialogIDs[ "SubmitButtonID" ]:
                if not self.SubmitJob():
                    return True

            if id == self.dialogIDs[ "CancelButtonID" ] or self.GetBool( self.dialogIDs[ "CloseOnSubmissionID" ] ):
                self.Close()

        return True
    
    def submitDependentAssemblyJob( self, outputFiles, configFiles, jobNum, dependentIDs ):
        jobName = self.GetString( self.dialogIDs[ "NameBoxID" ] )
        department = self.GetString( self.dialogIDs[ "DepartmentBoxID" ] )
            
        pool = self.Pools[ self.GetLong( self.dialogIDs[ "PoolBoxID" ] ) ]
        secondaryPool = self.SecondaryPools[ self.GetLong( self.dialogIDs[ "SecondaryPoolBoxID" ] ) ]
        group = self.Groups[ self.GetLong( self.dialogIDs[ "GroupBoxID" ] ) ]
        priority = self.GetLong( self.dialogIDs[ "PriorityBoxID" ] )
        machineLimit = self.GetLong( self.dialogIDs[ "MachineLimitBoxID" ] )
        taskTimeout = self.GetLong( self.dialogIDs[ "TaskTimeoutBoxID" ] )
        autoTaskTimeout = self.GetBool( self.dialogIDs[ "AutoTimeoutBoxID" ] )
        limitConcurrentTasks = self.GetBool( self.dialogIDs[ "LimitConcurrentTasksBoxID" ] )
        isBlacklist = self.GetBool( self.dialogIDs[ "IsBlacklistBoxID" ] )
        machineList = self.GetString( self.dialogIDs[ "MachineListBoxID" ] )
        limitGroups = self.GetString( self.dialogIDs[ "LimitGroupsBoxID" ] )
        onComplete = self.OnComplete[ self.GetLong( self.dialogIDs[ "OnCompleteBoxID" ] ) ]
        
        ErrorOnMissingTiles = self.GetBool( self.dialogIDs[ "ErrorOnMissingTilesID" ] )
        AssembleTilesOver = self.AssembleOver[ self.GetLong( self.dialogIDs[ "AssembleTilesOverID" ] ) ]
        BackgroundImage = self.GetString( self.dialogIDs[ "BackgroundImageID" ] )
        ErrorOnMissingBackground = self.GetBool( self.dialogIDs[ "ErrorOnMissingBackgroundID" ] )
        CleanupTiles = self.GetBool( self.dialogIDs[ "CleanupTilesID" ] )
        
        jobInfoFile = os.path.join( self.DeadlineTemp, "draft_submit_info%s.job" % jobNum )
        jobContents = {
            "Plugin": "DraftTileAssembler",
            "BatchName": jobName,
            "Name": "%s - Assembly Job" % jobName,
            "Comment": "Draft Tile Assembly Job",
            "Department": department,
            "Pool": pool,
            "SecondaryPool": "",
            "Group": group,
            "Priority": priority,
            "MachineLimit": machineLimit,
            "LimitGroups": limitGroups,
            "JobDependencies": ",".join( dependentIDs ),
            "OnJobComplete": onComplete,
        }

        # If it's not a space, then a secondary pool was selected.
        if secondaryPool != " ":
            jobContents["SecondaryPool"] = secondaryPool

        if isBlacklist:
            jobContents["Blacklist"] = machineList
        else:
            jobContents["Whitelist"] = machineList

        outputFileNum = 0
        for outputFile in outputFiles:
            jobContents["OutputFilename%s" % outputFileNum] = outputFile
            outputFileNum += 1

        if not self.GetBool( self.dialogIDs[ "SingleFrameTileJobID" ] ):
            frames = self.GetString( self.dialogIDs[ "FramesBoxID" ] )
            jobContents["Frames"] = frames
        else:
            jobContents["Frames"] = "0-%s" % ( outputFileNum - 1 )

        self.writeInfoFile( jobInfoFile, jobContents )
        self.ConcatenatePipelineSettingsToJob( jobInfoFile, jobName )

        pluginInfoFile = os.path.join( self.DeadlineTemp, "draft_plugin_info%s.job" % jobNum )
        pluginContents = {
            "ErrorOnMissing": ErrorOnMissingTiles,
            "ErrorOnMissingBackground": ErrorOnMissingBackground,
            "CleanupTiles": CleanupTiles,
            "MultipleConfigFiles": len(configFiles) > 0,
        }
        self.writeInfoFile( pluginInfoFile, pluginContents )

        print( "Submitting Dependent Assembly Job..." )
        args = [ jobInfoFile, pluginInfoFile ]
        args.extend( configFiles )
        
        results = ""
        try:
            results = CallDeadlineCommand( args, useArgFile=True )
        except:
            results = "An error occurred while submitting the job to Deadline.\n" + traceback.format_exc()
            
        successfulSubmission = ( results.find( "Result=Success" ) != -1 )
        print( results )
       
        return successfulSubmission
        
    def createDTAConfigFile(  self, frame, renderData, outputPath, outputFormat, outputNameFormat, take, isMulti=False, mpass=None, mpassSuffix=False, mpUsers=False, isAlpha=False, postEffect="" ):
        outputName = self.GetOutputFileName( outputPath, outputFormat, outputNameFormat, take, isMulti=isMulti, mpass=mpass, mpassSuffix=mpassSuffix, mpUsers=mpUsers, postEffect=postEffect )
        if isAlpha:
            tempOutputFolder, tempOutputFile = os.path.split(outputName)
            outputName = os.path.join( tempOutputFolder, "A_"+tempOutputFile )
        
        paddedFrame = str(frame)
        while len( paddedFrame ) < 4:
            paddedFrame = "0" + paddedFrame

        width = renderData.GetLong( c4d.RDATA_XRES )
        height = renderData.GetLong( c4d.RDATA_YRES )
        TilesInX = self.GetLong( self.dialogIDs[ "TilesInXID" ] )
        TilesInY = self.GetLong( self.dialogIDs[ "TilesInYID" ] )

        outputName = outputName.replace( "####", paddedFrame )
        fileName, fileExtension = os.path.splitext(outputName)
        
        date = time.strftime("%Y_%m_%d_%H_%M_%S")
        configFilename = "%s_%s_config_%s.txt" % ( fileName, frame, date )
        configContents = {
            "ImageFileName": outputName,
            "ImageHeight": height,
            "ImageWidth": width,
            "TilesCropped": False,
            "TileCount": TilesInX * TilesInY,
        }

        backgroundType = self.AssembleOver[ self.GetLong( self.dialogIDs[ "AssembleTilesOverID" ] ) ]
        if backgroundType == "Previous Output":
            configContents["BackgroundSource"] = outputName
        elif backgroundType == "Selected Image":
            BackgroundImage = self.GetString( self.dialogIDs[ "BackgroundImageID" ] )
            configContents["BackgroundSource"] = BackgroundImage

        currTile = 0
        regionNum = 0
        for y in range(TilesInY):
            for x in range(TilesInX):
                left = ( float( x ) /TilesInX ) * width
                left = int( left + 0.5 )

                right = ( float( x + 1.0 ) /TilesInX ) * width
                right = int( right + 0.5 )
                tileWidth = right - left

                top = ( float( y + 1 ) /TilesInY ) * height
                top = height - int( top + 0.5 )

                tileHeight = int ( ( float( y + 1 ) /TilesInY ) * height +0.5 ) - int ( ( float( y ) /TilesInY ) * height +0.5 )

                regionPrefix = "_Region_%s_" % regionNum
                regionOutputFileName = self.GetOutputFileName( outputPath, outputFormat, outputNameFormat, take, isMulti=isMulti,
                                                               mpass=mpass, mpassSuffix=mpassSuffix, mpUsers=mpUsers,
                                                               regionPrefix=regionPrefix, postEffect=postEffect )
                if isAlpha:
                    tempOutputFolder, tempOutputFile = os.path.split(regionOutputFileName)
                    regionOutputFileName = os.path.join( tempOutputFolder, "A_"+tempOutputFile )
                regionOutputFileName = regionOutputFileName.replace( "####", paddedFrame )

                configContents["Tile%iFileName" % currTile] = regionOutputFileName
                configContents["Tile%iX" % currTile] = left
                configContents["Tile%iY" % currTile] = top
                configContents["Tile%iWidth" % currTile] = tileWidth
                configContents["Tile%iHeight" % currTile] = tileHeight

                currTile += 1
                regionNum += 1

        self.writeInfoFile( configFilename, configContents )

        return configFilename

    def getTextureSearchPaths( self ):
        """
        A wrapper function to grab the texture search paths based on the Cinema 4D major version.
        :return: List of texture search paths
        """
        c4dMajorVersion = c4d.GetC4DVersion() / 1000

        # In R20, they deprecated GetGlobalTexturePath() and created GetGlobalTexturePaths()
        if c4dMajorVersion >= 20:
            # Search paths looks like this: [ ['C:\\my\\path\\to\\search', True], ... ]
            return [ path for path, isEnabled in c4d.GetGlobalTexturePaths() if isEnabled ]
        else:
            return [ c4d.GetGlobalTexturePath( index ) for index in range( 10 ) ]
    
    def get_token_context(self, doc, take="", isMulti=False, mpass=None, mpUsers=False, postEffect="" ):
        if take == "" and useTakes:
            take = doc.GetTakeData().GetCurrentTake().GetName()
        rdata = doc.GetActiveRenderData()
        bd = doc.GetRenderBaseDraw()
        fps = doc.GetFps()
        time = doc.GetTime()
        range_ = ( rdata[ c4d.RDATA_FRAMEFROM ], rdata[ c4d.RDATA_FRAMETO ] )

        #The project name is created from the document name (eg. myfile.c4d) with the extension stripped off
        projName = doc.GetDocumentName()
        extIndex = projName.rfind( '.' )
        if extIndex != -1:
            projName = projName[ 0:extIndex ]
        
        context = {
            'prj': projName,
            'camera': bd.GetSceneCamera( doc ).GetName(),
            'take': take,
            # 'pass': 
            # 'userpass':
            'frame': doc.GetTime().GetFrame( doc.GetFps() ),
            'rs': rdata.GetName(),
            'res': '%dx%d' % ( rdata[c4d.RDATA_XRES ], rdata[ c4d.RDATA_YRES ] ),
            'range': '%d-%d' % tuple(x.GetFrame(fps) for x in range_),
            'fps': fps }
        
        if not isMulti:
            context[ 'pass' ] = "rgb"
            context[ 'userpass' ] = "RGB"
        elif mpass:
            passType = mpass[ c4d.MULTIPASSOBJECT_TYPE ]
            if passType == c4d.VPBUFFER_BLEND:
                blendCount = self.GetBlendIndex( mpass )
                context[ 'userpass' ] = mpass.GetName() + "blend_" + str( blendCount )
                if mpUsers:
                    context[ 'pass' ] = mpass.GetName() + "blend_" + str( blendCount )
                else:
                    context[ 'pass' ] = "blend_" + str( blendCount )
            elif passType == c4d.VPBUFFER_ALLPOSTEFFECTS:
                context[ 'pass' ] = postEffect.lower()
                context[ 'userpass' ] = postEffect
            else:
                context[ 'userpass' ] = mpass.GetName()
                if mpUsers:
                    context[ 'pass' ] = mpass.GetName().lower()
                else:
                    #Layer Type code does not work if "User Defined Layer Name" is enabled in render settings and we are currently unable to pull that setting.
                    if passType == c4d.VPBUFFER_OBJECTBUFFER:
                        bufferID = mpass[ c4d.MULTIPASSOBJECT_OBJECTBUFFER ]
                        context[ 'pass' ] = ( "object_%s" % bufferID )
                    else:
                        context[ 'pass' ] = SubmitC4DToDeadlineDialog.gpuRenderers[ mpass.GetTypeName() ]
                        
        return context

    def get_renderPathData(self, doc, activeTake="", isMulti=False, mpass=None, mpUsers=False, postEffect="" ):
        take = None

        if useTakes:
            takeData = doc.GetTakeData()
            mainTake = takeData.GetMainTake()

            if activeTake != "":
                take = mainTake.GetDown()
                while take is not None:
                    if take.GetName() == activeTake:
                        break
                    take = take.GetNext()
            else: 
                take = takeData.GetCurrentTake()

        rdata = doc.GetActiveRenderData()
        rBc = rdata.GetData()
                
        if isMulti and mpass:
            rBc = mpass.GetData()

        rpData = {
            '_doc': doc,
            '_rData': rdata,
            '_rBc': rBc,
            '_frame': doc.GetTime().GetFrame( doc.GetFps() )
        }

        if take:
            rpData[ '_take' ] = take
        
        if not isMulti:
            rpData[ '_layerName' ] = "rgb"
            rpData[ '_layerTypeName' ] = "RGB"
        elif mpass:
            passType = mpass[ c4d.MULTIPASSOBJECT_TYPE ]
            if passType == c4d.VPBUFFER_BLEND:
                blendCount = self.GetBlendIndex( mpass )
                rpData[ '_layerName' ] = mpass.GetName() + "blend_" + str( blendCount )
                if mpUsers:
                    rpData[ '_layerTypeName' ] = mpass.GetName() + "blend_" + str( blendCount )
                else:
                    rpData[ '_layerTypeName' ] = "blend_" + str( blendCount )
            elif passType == c4d.VPBUFFER_ALLPOSTEFFECTS:
                rpData[ 'pass' ] = postEffect.lower()
                rpData[ 'userpass' ] = postEffect
            else:
                rpData[ '_layerName' ] = mpass.GetName()
                
                if mpUsers:
                    rpData[ '_layerTypeName' ] = mpass.GetName().lower()
                else:
                    #Layer Type code does not work if "User Defined Layer Name" is enabled in render settings and we are currently unable to pull that setting.
                    if passType == c4d.VPBUFFER_OBJECTBUFFER:
                        bufferID = mpass[ c4d.MULTIPASSOBJECT_OBJECTBUFFER ]
                        rpData[ '_layerTypeName' ] = ( "object_%s" % bufferID )
                    else:
                        rpData[ '_layerTypeName' ] = SubmitC4DToDeadlineDialog.mPassTypePrefixDict[ mpass.GetTypeName() ]
        
        return rpData

    def tokenSystem_eval( self, text, rpData ):
        return tokensystem.FilenameConvertTokens( text, rpData )
        
    def token_eval( self, text, context ):
        return TokenString( text ).safe_substitute( context )
        
    def GetOutputFileName( self, outputPath, outputFormat, outputNameFormat, take, isMulti=False, mpass=None, mpassSuffix=False, mpUsers=False, regionPrefix="", postEffect="" ):
        if not outputPath:
            return ""
        
        doc = documents.GetActiveDocument()
        # C4D always throws away the last extension in the file name, so we'll do that too.
        outputPrefix, tempOutputExtension = os.path.splitext( outputPath )
        outputExtension = self.GetExtensionFromFormat( outputFormat )
        
        if isMulti and mpass is not None:
             #Layer Type code does not work if "User Defined Layer Name" is enabled in render settings and we are currently unable to pull that setting.
            if mpUsers:
                passType = mpass[c4d.MULTIPASSOBJECT_TYPE]
                if passType == c4d.VPBUFFER_BLEND:
                    blendCount = self.GetBlendIndex( mpass )
                    mpassValue = blendCount + "blend_" + str(blendCount )
                elif passType == c4d.VPBUFFER_ALLPOSTEFFECTS:
                    mpassValue = postEffect
                else:
                    mpassValue = mpass.GetName()
            else:
                passType = mpass[c4d.MULTIPASSOBJECT_TYPE]
                if passType == c4d.VPBUFFER_OBJECTBUFFER:
                    bufferID = mpass[c4d.MULTIPASSOBJECT_OBJECTBUFFER]
                    mpassValue = ("object_%s" %bufferID)
                elif passType == c4d.VPBUFFER_BLEND:
                    blendCount = self.GetBlendIndex( mpass )
                    mpassValue = ( "blend_%s" % blendCount )
                elif passType == c4d.VPBUFFER_ALLPOSTEFFECTS:
                    mpassValue = postEffect.lower()
                else:
                    mpassValue = SubmitC4DToDeadlineDialog.mPassTypePrefixDict[mpass.GetTypeName()]
        
            if mpassSuffix:
                mpassValue = "_"+mpassValue
                outputPrefix = outputPrefix + regionPrefix + mpassValue
            else:
                mpassValue = mpassValue+"_"
                outPrefixParts = os.path.split(outputPrefix)
                outputPrefix = os.path.join( outPrefixParts[0],  mpassValue+outPrefixParts[1] + regionPrefix ) 
        else:
            outputPrefix = outputPrefix + regionPrefix
                
        # If the name requires an extension, and an extension could not be determined,
        # we simply return an empty output filename because we don't have all the info.
        if outputNameFormat == 0 or outputNameFormat == 3 or outputNameFormat == 6:
            if outputExtension == "":
                return ""

        if useTokens:
            rpData = self.get_renderPathData( doc, take, isMulti=isMulti, mpass=mpass, mpUsers = mpUsers, postEffect = postEffect )
            outputPrefix = self.tokenSystem_eval( outputPrefix, rpData )
        else:
            context = self.get_token_context( doc, take=take, isMulti=isMulti, mpass=mpass, mpUsers = mpUsers, postEffect = postEffect )
            outputPrefix = self.token_eval( outputPrefix, context )
        
        # If the output ends with a digit, and the output name scheme doesn't start with a '.', then C4D automatically appends an underscore.
        if len( outputPrefix ) > 0 and outputPrefix[ len( outputPrefix ) - 1 ].isdigit() and outputNameFormat not in ( 2, 5, 6 ):
            outputPrefix = outputPrefix + "_"
        
        # Format the output filename based on the selected output name.
        if outputNameFormat == 0:
            return outputPrefix + "####." + outputExtension
        elif outputNameFormat == 1:
            return outputPrefix + "####"
        elif outputNameFormat == 2:
            return outputPrefix + ".####"
        elif outputNameFormat == 3:
            return outputPrefix + "###." + outputExtension
        elif outputNameFormat == 4:
            return outputPrefix + "###"
        elif outputNameFormat == 5:
            return outputPrefix + ".###"
        elif outputNameFormat == 6:
            return outputPrefix + ".####." + outputExtension
        
        return ""
    
    def GetBlendIndex( self, MPass ):
        blendCount = 1
        remainingMPass = MPass.GetNext()
        while remainingMPass is not None:
            remainingPassType = remainingMPass[ c4d.MULTIPASSOBJECT_TYPE ]
            if remainingPassType == c4d.VPBUFFER_BLEND:
                blendCount += 1
            remainingMPass = remainingMPass.GetNext()
        return blendCount
    
    def GetExtensionFromFormat( self, outputFormat ):
        extension = ""
        
        # These values are pulled from coffeesymbols.h, which can be found in
        # the 'resource' folder in the C4D install directory.
        if outputFormat == 1102: # BMP
            extension = "bmp"
        elif outputFormat == 1109: # B3D
            extension = "b3d"
        elif outputFormat == 1023737: # DPX
            extension = "dpx"
        elif outputFormat == 1103: # IFF
            extension = "iff"
        elif outputFormat == 1104: # JPG
            extension = "jpg"
        elif outputFormat == 1016606: # openEXR
            extension = "exr"
        elif outputFormat == 1106: # PSD
            extension = "psd"
        elif outputFormat == 1111: # PSB
            extension = "psb"
        elif outputFormat == 1105: # PICT
            extension = "pct"
        elif outputFormat == 1023671: # PNG
            extension = "png"
        elif outputFormat == 1001379: # HDR
            extension = "hdr"
        elif outputFormat == 1107: # RLA
            extension = "rla"
        elif outputFormat == 1108: # RPF
            extension = "rpf"
        elif outputFormat == 1101: # TGA
            extension = "tga"
        elif outputFormat == 1110: # TIF (B3D Layers)
            extension = "tif"
        elif outputFormat == 1100: # TIF (PSD Layers)
            extension = "tif"
        elif outputFormat == 1024463: # IES
            extension = "ies"
        elif outputFormat == 1122: # AVI
            extension = "avi"
        elif outputFormat == 1125: # QT
            extension = "mov"
        elif outputFormat == 1150: # QT (Panarama)
            extension = "mov"
        elif outputFormat == 1151: # QT (object)
            extension = "mov"
        elif outputFormat == 1112363110: # QT (bmp)
            extension = "bmp"
        elif outputFormat == 1903454566: # QT (image)
            extension = "qtif"
        elif outputFormat == 1785737760: # QT (jp2)
            extension = "jp2"
        elif outputFormat == 1246774599: # QT (jpg)
            extension = "jpg"
        elif outputFormat == 943870035: # QT (photoshop)
            extension = "psd"
        elif outputFormat == 1346978644: # QT (pict)
            extension = "pct"
        elif outputFormat == 1347307366: # QT (png)
            extension = "png"
        elif outputFormat == 777209673: # QT (sgi)
            extension = "sgi"
        elif outputFormat == 1414088262: # QT (tiff)
            extension = "tif"
        
        return extension
    
    def GetOptions( self, selection, selectionType, validOptions ):
        if selection in self.RestrictionsDict:
            if selectionType in self.RestrictionsDict[selection]:
                restrictedOptions = self.RestrictionsDict[selection][selectionType]
                validOptions = list( set( validOptions ).intersection( restrictedOptions ) )
        return validOptions

    def GetTakeFromName( self, name ):
        if name in self.TakesDict:
            return self.TakesDict[name]
        else:
            return None
    
    def GetRenderInfo( self, scene, take=None ):
        renderInfo = None
        
        if take:
            takeData = scene.GetTakeData()
            effectiveRenderData = self.GetTakeFromName( take ).GetEffectiveRenderData( takeData )
            if effectiveRenderData is not None:
                renderInfo = effectiveRenderData[ 0 ]
        
        if renderInfo is None:
            renderInfo = scene.GetActiveRenderData()
            
        return renderInfo

    def getRenderer( self, scene=None, take=None, renderInfo=None):
       if renderInfo is None:
           if scene is None:
               scene = documents.GetActiveDocument()
           if take is None:
               takeData = scene.GetTakeData()
               take = takeData.GetMainTake().GetName()
           renderInfo = self.GetRenderInfo( scene, take )
       return self.GetRendererName( renderInfo[c4d.RDATA_RENDERENGINE] )

    def getPostEffectPasses( self, take=None ):
        """
        Retrieves a list of all post effects passes for the current renderer
        :param take: the take that is being submitted
        :return: A list of render passes that will be renderered
        """
        scene = documents.GetActiveDocument()
        renderInfo = self.GetRenderInfo( scene, take )

        renderer = self.getRenderer( scene=scene, take=take, renderInfo=renderInfo )
        if renderer == "iray":
            return self.getIrayPostEffectPasses( renderInfo )
        elif renderer == "arnold":
            return self.getArnoldPostEffectPasses( scene )
        elif renderer == "vray":
            return self.getVrayPostEffectPasses( scene )
        return []

    def getIrayPostEffectPasses( self, renderInfo ):
        """
        Retrieves a list of post effects which Iray will render with the current settings
        :param renderInfo: The current render settings object
        :return: the list of Post effects passes
        """
        videoPost = renderInfo.GetFirstVideoPost()
        while videoPost is not None and not self.GetRendererName( videoPost.GetType() ) == "iray":
            videoPost = videoPost.GetNext()

        if not videoPost:
            return []

        irayPostEffects = [
            #THE CAPITALIZATION MISTAKE IS ON PURPOSE BECAUSE IRAY HAS THAT MISTAKE IN THE FILE NAMES
            ( c4d.VP_IRAY_MULTIPASS_AUX_ALPHA, "NVIDIA Iray ALpha_" ),
            ( c4d.VP_IRAY_MULTIPASS_AUX_DEPTH, "NVIDIA Iray Depth_" ),
            ( c4d.VP_IRAY_MULTIPASS_AUX_NORMAL, "NVIDIA Iray Normal_" ),
            ( c4d.VP_IRAY_MULTIPASS_AUX_UV, "NVIDIA Iray UVs_" ),
        ]

        # Get all the iray post effect passes in use
        passes = [ passName for passId, passName in irayPostEffects if videoPost[ passId ] ]
        # Append the pass number to the pass name in the order they're rendered, one-indexed
        return [ passName + str(i) for i, passName in enumerate( passes, 1 ) ]
            
    def getArnoldPostEffectPasses( self, scene ):
        """
        Returns a list of post effects which Arnold will render with the current settings
        :param scene: the current scene
        :return: the list of post effects passes
        """
        # Arnold drivers completely ignore Takes, so grab all of them from the scene
        drivers = [ obj for obj in scene.GetObjects() if obj.GetType() == SubmitC4DToDeadlineDialog.ARNOLD_DRIVER ]

        # Even if there are no drivers or if they and every AOV is disabled, Arnold will always render an alpha pass first
        passes = [ "alpha_1" ]
        for driver in drivers:
            # Currently only support c4d_display_drivers, since the other drivers need to be special cased across this script (user_layer_names, output_prefix, etc.)
            if driver[ c4d.C4DAI_DRIVER_TYPE ] == SubmitC4DToDeadlineDialog.ARNOLD_C4D_DISPLAY_DRIVER_TYPE:
                # Get all enabled AOVs for the driver
                AOVs = driver.GetChildren()

                # c4d.ID_BASEOBJECT_GENERATOR_FLAG is checking if the AOV is enabled. c4d_display_driver ignores the beauty AOV (it's the regular image file, instead of a multipass)
                driverPasses = [ AOV.GetName() + "_" + str(i) for i, AOV in enumerate( AOVs, 2 ) if AOV[ c4d.ID_BASEOBJECT_GENERATOR_FLAG ] and AOV.GetName() != "beauty" ]

                # Add them to the existing passes
                passes.extend( driverPasses )

                # Arnold only cares about the first 'driver_c4d_display' driver in the scene. This will need to be changed when you add support for more driver types ("continue" if it's not the first one)
                break

        # Remove any duplicates, since we only support region rendering for the beauty/multi-pass image file output location (no custom locations for AOVs/drivers)
        return set( passes )
        
    def getVrayPostEffectPasses( self, scene ):
        """
        Returns a list of the names of each pass that is rendered by the Post Effects Multipass object.
        :param scene: A hook to the current scene.
        :return: a list of the pass naming for each Vray Multipass object.
        """
        # Scene Hooks
        mpSceneHook = scene.FindSceneHook( self.VRAY_MULTIPASS_PLUGIN_ID )
        try:
            branch = mpSceneHook.GetBranchInfo()
        except AttributeError:
            #GetBranchInfo was exposed to python C4D R19
            return []

        #Multipass nodes are stored in the last branch
        categoryNode = branch[ -1 ]["head"].GetFirst()

        #Vray Post Effects are stored in a linked list of Category nodes which each contain a list of the nodes within that category.
        channels = []
        while categoryNode:
            # Process the nodes within a category if the category is enabled.
            if categoryNode.GetData()[ c4d.MPNODE_ISENABLED ]:
                channelNode = categoryNode.GetDown()
                while channelNode:
                    #process the individual channels in a category if they are enabled.
                    if channelNode.GetData()[c4d.MPNODE_ISENABLED]:
                        channels.append( channelNode.GetName() )

                    channelNode = channelNode.GetNext()

            categoryNode = categoryNode.GetNext()

        #Vray Post Effects pass names are always of the form NodeName_Index with index starting at 2.
        #The nodes are always indexed in the reverse order than what we can walk.
        return [ "%s_%s" % ( nodeName, index ) for index, nodeName in enumerate( reversed(channels),2) ]

    def getEachMultipass( self, take=None ):
        """
        A generator function which will yield every multipass defined in the current render settings.
        For Post Effect Passes it will return each pass as defined by the current renderer
        :param take: Which take we are currently submitting.
        :return: Tuples in the form of ( Multipass Object, Post Effect Pass )
        """

        scene = documents.GetActiveDocument()

        for additionalPass in self.getAdditionalMultipasses( take=take ):
            yield ( additionalPass, "" )

        mPass = scene.GetActiveRenderData().GetFirstMultipass()
        while mPass is not None:
            if not mPass.GetBit( c4d.BIT_VPDISABLED ):
                passType = mPass[c4d.MULTIPASSOBJECT_TYPE]

                if passType == c4d.VPBUFFER_ALLPOSTEFFECTS:
                    for innerPass in self.getPostEffectPasses( take=take ):
                        yield ( mPass, innerPass )
                else:
                    yield ( mPass, "" )

            mPass = mPass.GetNext()
        

    def getAdditionalMultipasses( self, take=None ):
        """
        Some renderers always add specific additional passes that are always added regardless of what Multipasses are enabled
        :param take: The current take that is being rendered.
        :return: A list of Multipass objects that are added outside of the user defined Multipasses.
        """
        renderer = self.getRenderer( take=take )

        if renderer == "vray":
            return self.getVrayAdditionalPasses( )

        return [ ]

    @staticmethod
    def getVrayAdditionalPasses(  ):
        """
        VRay automatically adds an RGB pass if one is not already set within the Render settings
        :return: A list containing all multipass objects that are added by V-ray ( RGB if none is defined )
        """
        scene = documents.GetActiveDocument()
        passes = []

        mPass = scene.GetActiveRenderData().GetFirstMultipass()
        #Go through all of the multipasses and break out if we find an RGBA pass
        while mPass is not None:
            if not mPass.GetBit( c4d.BIT_VPDISABLED ):
                passType = mPass[ c4d.MULTIPASSOBJECT_TYPE ]
                if passType == c4d.VPBUFFER_RGBA:
                    break
            mPass = mPass.GetNext()
        else:
            # we did not find an RGBA Pass so we create our own.
            rgbPass = c4d.BaseList2D( c4d.Zmultipass )
            rgbPass.GetDataInstance()[ c4d.MULTIPASSOBJECT_TYPE ] = c4d.VPBUFFER_RGBA
            rgbPass.SetName( "rgb" )
            passes.append(rgbPass)

        return passes

    def GetRendererName( self, rendererID ):
        if rendererID in self.renderersDict:
            return self.renderersDict[ rendererID ]
        else:
            return None

## Class to create the submission menu item in C4D.
class SubmitC4DtoDeadlineMenu( plugins.CommandData ):
    ScriptPath = ""
    
    def __init__( self, path ):
        self.ScriptPath = path
    
    def Execute( self, doc ):
        if SaveScene():
            dialog = SubmitC4DToDeadlineDialog()
            dialog.Open( c4d.DLG_TYPE_MODAL )
        return True
    
    def GetScriptName( self ):
        return "Submit To Deadline"

    
def GetDeadlineCommand( useDeadlineBg=False ):
    deadlineBin = ""
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        #if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass
        
    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if not deadlineBin and os.path.isfile( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with io.open( "/Users/Shared/Thinkbox/DEADLINE_PATH", encoding="utf-8" ) as f:
            deadlineBin = f.read().strip()
    
    exeName = "deadlinecommand"
    if useDeadlineBg:
        exeName += "bg"
    
    deadlineCommand = os.path.join( deadlineBin, exeName )

    return deadlineCommand

def CreateArgFile( arguments, tmpDir ):
    tmpFile = os.path.join( tmpDir, "args.txt" )
    
    with io.open( tmpFile, 'w', encoding="utf-8-sig" ) as fileHandle:
        fileHandle.write( u"\n".join(arguments) )
        
    return tmpFile
    
def CallDeadlineCommand( arguments, hideWindow=True, useArgFile=False, useDeadlineBg=False ):
    deadlineCommand = GetDeadlineCommand( useDeadlineBg )
    tmpdir = None
    
    if useArgFile or useDeadlineBg:
        tmpdir = tempfile.mkdtemp()
        
    startupArgs = [deadlineCommand]
    
    if useDeadlineBg:
        arguments = ["-outputfiles", os.path.join(tmpdir,"dlout.txt"), os.path.join(tmpdir,"dlexit.txt") ] + arguments
    
    startupinfo = None
    creationflags = 0

    if os.name == 'nt':
        if hideWindow:
            # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
            if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            # still show top-level windows, but don't show a console window
            CREATE_NO_WINDOW = 0x08000000   #MSDN process creation flag
            creationflags = CREATE_NO_WINDOW

    if useArgFile:
        arguments = [ CreateArgFile( arguments, tmpdir ) ]
    
    arguments = startupArgs + arguments
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags)
    output, errors = proc.communicate()
    
    if useDeadlineBg:
        with io.open( os.path.join( tmpdir, "dlout.txt" ), 'r', encoding='utf-8' ) as fileHandle:
            output = fileHandle.read()
    
    if tmpdir:
        try:
            shutil.rmtree(tmpdir)
        except:
            print( 'Failed to remove temp directory: "%s"' % tmpdir )

    return output.strip()

class TokenString(string.Template):
    idpattern = '[a-zA-Z]+'

# Iterate through objects in take (op)
def GetNextObject( op ):
    if op == None:
      return None
  
    if op.GetDown():
      return op.GetDown()
  
    while not op.GetNext() and op.GetUp():
      op = op.GetUp()
  
    return op.GetNext()    

## Global function to save the scene. Returns True if the scene has been saved and it's OK to continue.
def SaveScene():
    scene = documents.GetActiveDocument()
    
    # Save the scene if required.
    if scene.GetDocumentPath() == "" or scene.GetChanged():
        print( "Scene file needs to be saved" )
        c4d.CallCommand( 12098 ) # this is the ID for the Save command (from Command Manager)
        if scene.GetDocumentPath() == "":
            gui.MessageDialog( "The scene must be saved before it can be submitted to Deadline" )
            return False
    
    return True

def IsPathLocal( path ):
    lowerPath = path.lower()
    if lowerPath.startswith( "c:" ) or lowerPath.startswith( "d:" ) or lowerPath.startswith( "e:" ):
        return True
    return False
    
def hasArnoldDriver():
    doc = documents.GetActiveDocument()
    return innerHasArnoldDriver( doc, doc.GetFirstObject() )
    
def innerHasArnoldDriver(doc, bl2d):
    while bl2d:
        if bl2d.GetTypeName() == "Arnold Driver":
            return True
        
        if innerHasArnoldDriver( doc, bl2d.GetDown() ):
            return True
        bl2d = bl2d.GetNext()

    return False

def compute_tile_region(tile_num, tiles_in_x, tiles_in_y, height, width, renderer):
    """
    Computes the coordinates for a tile based on the renderer, image pixel dimensions, and the
    tile grid.

    Arguments:
        tile_num (int): The index of the tile between the range of [0, tiles_in_x * tiles_in_y)
        tiles_in_x (int): The number of tiles in the x-axis
        tiles_in_y (int): The number of tiles in the y-axis
        height (int): The number of pixels for the full image in the y-axis
        width (int): The number of pixels for the full image in the x-axis
        renderer (str): The name of the renderer. Different renderers expect different region coordinate
            representations.
    
    Returns:
        Region: A named tuple containing the region coordinates for the tile.
    """

    # Compute which tile we are calculating
    y, x = divmod( tile_num, tiles_in_x )

    if renderer == "octane":
        # Octane uses floating-point percentages in the range of [0, 1] to specify the render region. Each
        # region boundary (top/left/bottom/right) is expressed as a percentage of the pixels in the corresponding
        # dimension away from the boundary's image border.

        # Compute the percentage factors for each of the tile dimensions.
        x_tile_pct = 1.0 / tiles_in_x
        y_tile_pct = 1.0 / tiles_in_y
        # Pad by the percentage of the dimension making up one pixel in case the
        # number of tiles does not evenly divide the output image dimension
        x_tile_pad = 1.0 / width
        y_tile_pad = 1.0 / height

        
        left = max(0, x_tile_pct * x - x_tile_pad)                  # Percentage from the left
        right = min(1.0, 1.0 - left - x_tile_pct - x_tile_pad)      # Percentage from the right
        top = max(0, y_tile_pct * y - y_tile_pad)                   # Percentage from the top
        bottom = min(1.0, 1.0 - top - y_tile_pct - y_tile_pad)      # Percentage from the bottom
    else:
        # Other renderers use the standard C4D region coordinates and are expressed in pixel offsets
        # where the origin is the top-left corner

        # Compute the number of pixels from the left image border
        left = ( float( x ) / tiles_in_x ) * width
        left = int( left + 0.5 )

        # Compute the number of pixels from the right image border
        right = ( float( x + 1 ) / tiles_in_x ) * width
        right = int( right + 0.5 )
        right = width - right

        # Compute the number of pixels from the top image border
        top = ( float( y ) / tiles_in_y ) * height
        top = int( top + 0.5 )

        # Compute the number of pixels from the bottom image border
        bottom = ( float( y + 1 ) / tiles_in_y ) *height
        bottom = int( bottom + 0.5 )
        bottom = height - bottom
    
    return Region(
        left=left,
        top=top,
        right=right,
        bottom=bottom
    )

## Global function used to register our submission script as a plugin.
def main( path ):
    pluginID = 1025665
    plugins.RegisterCommandPlugin( pluginID, "Submit To Deadline", 0, None, "Submit a Cinema 4D job to Deadline.", SubmitC4DtoDeadlineMenu( path ) )

## For debugging.
if __name__=='__main__':
    if SaveScene():
        dialog = SubmitC4DToDeadlineDialog()
        dialog.Open( c4d.DLG_TYPE_MODAL )

import json
import os
import sys
import traceback

try:
    import nim_core.nim as nim
    usingNim = True
except:
    usingNim = False

try:
    import sgtk
    usingShotgun = True
except:
    usingShotgun = False

def getNimInfoFromScene( nimInfo ):
    args = ( nimInfo, )
    if nimInfo.app() == "Maya":
        import nim_core.nim_maya as nimPlugin
    elif nimInfo.app() == "Nuke":
        import nim_core.nim_nuke as nimPlugin
    elif nimInfo.app() == "C4D":
        import nim_core.nim_c4d as nimPlugin
        nimC4DPluginId = 1032427
        args = ( nimInfo, nimC4DPluginId )
    elif nimInfo.app() == "3dsMax":
        import nim_core.nim_3dsmax as nimPlugin
    elif nimInfo.app() == "Houdini":
        import nim_core.nim_houdini as nimPlugin
    
    nimPlugin.get_vars( *args )

def getInfoFromShotgun( context ):
    shotgunInfo = {}
    
    if context.user is not None:
        # login is not guaranteed to be in the user dict
        shotgunInfo[ "UserLogin" ] = context.user.get( "login", "" )
        shotgunInfo[ "UserName" ] = context.user[ "name" ]
    
    if context.project is not None:
        shotgunInfo[ "ProjectName" ] = context.project[ "name" ]
        shotgunInfo[ "ProjectId" ] = context.project[ "id" ]
    
    if context.entity is not None:
        shotgunInfo[ "EntityName" ] = context.entity[ "name" ]
        shotgunInfo[ "EntityId" ] = context.entity[ "id" ]
        shotgunInfo[ "EntityType" ] = context.entity[ "type" ]
    
    if context.task is not None:
        shotgunInfo[ "TaskName" ] = context.task[ "name" ]
        shotgunInfo[ "TaskId" ] = context.task[ "id" ]

    return shotgunInfo

def writeInfoFile( tempPath, pipelineToolsInfo ):
    with open( os.path.join( tempPath, "pipeline_tools_info.json" ), "w" ) as fileHandle:
        fileHandle.write( json.dumps( pipelineToolsInfo ) )

def getInfo( tempPath ):
    pipelineToolsInfo = {
        "NIM" : {},
        "Shotgun" : {}
    }

    if usingNim:
        nimInfo = nim.NIM()
        getNimInfoFromScene( nimInfo )
        # If there's actually info in this scene tied to NIM, pass it along, otherwise ensure NIM stays an empty dict
        if nimInfo.nim.get( "job", {} ).get( "ID", "" ):
            pipelineToolsInfo[ "NIM" ] = nimInfo.nim
    
    if usingShotgun:
        context = sgtk.platform.current_engine().context
        pipelineToolsInfo[ "Shotgun" ] = getInfoFromShotgun( context )
    
    writeInfoFile( tempPath, pipelineToolsInfo )

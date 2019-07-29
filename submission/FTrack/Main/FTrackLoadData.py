
def getFtrackData():
    # get ftrack data from launched app
    import os
    error = [ "[Error]" ]
    try:
        import ftrack
    except:
        return error

    import json
    import base64

    ftrackConnectVar = os.environ.get( 'FTRACK_CONNECT_EVENT' );
    if ftrackConnectVar is None:
        return error

    decodedEventData = json.loads(
        base64.b64decode(
            ftrackConnectVar
        )
    )

    try:
        taskId = decodedEventData.get( 'selection' )[ 0 ][ 'entityId' ]
        user = decodedEventData.get( 'source' )[ 'user' ]
        task = ftrack.Task( taskId )
    except:
        return error
    
    ftrackData = []
    ftrackData.append( "FT_Username=%s" % user[ 'username' ] )
    ftrackData.append( "FT_TaskName=%s" % task.getName() )
    ftrackData.append( "FT_TaskId=%s" % task.getId() )
    ftrackData.append( "FT_Description=%s" % task.getDescription() )

    try:
        project = task.getProject()
        ftrackData.append( "FT_ProjectName=%s" % project.getName() )
        ftrackData.append( "FT_ProjectId=%s" % project.getId() )
    except:
        pass
    
    try:
        asset = task.getAssets()[ 0 ]
        ftrackData.append( "FT_AssetName=%s" % asset.getName() )
        ftrackData.append( "FT_AssetId=%s" % asset.getId() )
    except:
        pass
    
    return ftrackData
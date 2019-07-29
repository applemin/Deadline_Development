from __future__ import print_function
import threading
import time
import socket
import sys
import os
import tempfile
import uuid
import traceback
import platform
import subprocess

import maya.cmds as cmds
import maya.utils as utils
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMaya as OpenMaya


def GetDeadlineCommand():
    deadlineBin = ""
    try:
        deadlineBin = os.environ['DEADLINE_PATH']
    except KeyError:
        #if the error is a key error it means that DEADLINE_PATH is not set. however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
        pass
        
    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if deadlineBin == "" and  os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f:
            deadlineBin = f.read().strip()

    deadlineCommand = os.path.join(deadlineBin, "deadlinecommand")
    
    return deadlineCommand
    
#A thread that is created in maya to communicate with the Jigsaw UI.
class MyThread(threading.Thread):
    sockIn = None
    sockOut = None
    tempFile = None
    savedRegions = ""
    usingWidth = 1
    usingHeight = 1
    def run(self):
        #Create an input socket on an open port
        HOSTin = ''                 # Symbolic name meaning all available interfaces
        PORTin = self.get_open_port()              # Arbitrary non-privileged port
        self.sockIn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockIn.bind((HOSTin, PORTin))
        self.sockIn.listen(1)
        repo = CallDeadlineCommand(["-GetRepositoryRoot"]).rstrip()
        
        #in the main thread get a screen shot
        screenshot = utils.executeInMainThreadWithResult(self.getScreenshot)
        info = screenshot.split("=")
        #if the screenshot exists then continue else create the failed message and return
        draftPath = repo+os.sep+"draft"
        if len(info) == 1:
            utils.executeInMainThreadWithResult(self.failedScreenshot)
            return
        
        deadlineCommand = GetDeadlineCommand()
        deadlineBin = os.path.dirname( deadlineCommand )
        
        if platform.system() == "Linux":
            if not deadlineBin == "":
                newLDPath = os.path.join(deadlineBin,"python","lib")+os.pathsep+draftPath
                if "LD_LIBRARY_PATH" in os.environ:
                    newLDPath = newLDPath + os.pathsep + os.environ["LD_LIBRARY_PATH"]
                os.environ["LD_LIBRARY_PATH"] = newLDPath
        elif platform.system() == "Darwin":
            if not deadlineBin == "":
                draftPath = os.path.join(draftPath,"Mac")
                newDYLDPath = os.path.join(deadlineBin,"python","lib")+os.pathsep+draftPath
                if "DYLD_LIBRARY_PATH" in os.environ:
                    newDYLDPath = newDYLDPath + os.pathsep + os.environ["DYLD_LIBRARY_PATH"]

                os.environ["DYLD_LIBRARY_PATH"] = newDYLDPath
            
        #Get deadlinecommand to execute a script and pass in a screenshot and the port to connect to.
        CallDeadlineCommand(["-executescript",repo+os.sep+"submission"+os.sep+"Jigsaw"+os.sep+"Jigsaw.py",str(PORTin),info[1]], False, False)
        
        conn, addr = self.sockIn.accept()
        #wait to receive the a message with the port in which to connect to for outgoing messages
        data = recvData(conn)
        if not data:
            #If we do not get one return
            conn.close()
            return
        HostOut = 'localhost'
        PORTout = int(data)
        self.sockOut = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockOut.connect((HostOut, PORTout))
        #constantly listen 
        while 1:
            data = recvData(conn)
            #if we do not get data then exit
            if not data:
                break
            #otherwise split the data on =
            command = str(data).split("=")
            #if we got the command exit then break out of the loop
            if command[0].lower() == "exit":
                break
            #if we were told to get the screenshot then retrieve a screenshot and send it to the jigsaw ui
            elif command[0].lower() == "getscreenshot":
                screenshot = utils.executeInMainThreadWithResult(self.getScreenshot)
                if(not screenshot):
                    cmds.confirmDialog(title="No Background", message="Unable to get background. Make sure that the viewport is selected.");
                    self.closeJigsaw()
                else:
                    self.sockOut.sendall(screenshot+"\n")
            #When we are told to fit the region
            elif command[0].lower() == "getselected":
                mode = 0#Vertex
                padding = 0 #percentage based padding
                if len(command)>1:
                    arguments=command[1].split(";")
                    arguments[0].split()
                    if arguments[0].lower() == "tight":
                        mode = 0#vertex
                    elif arguments[0].lower() == "loose":
                        mode = 1#boundingbox
                    padding = float(arguments[1])
                regions = self.getSelectedBoundingRegion(mode, padding)
                regionMessage = ""
                for region in regions:
                    if not regionMessage == "":
                        regionMessage+=";"
                    first = True
                    for val in region:
                        if not first:
                            regionMessage+=","
                        regionMessage += str(val)
                        first = False
                self.sockOut.sendall("create="+regionMessage+"\n")
            #when told to save the regions save them to the scene
            elif command[0].lower() == "saveregions":
                if not len(command)>1:
                    utils.executeInMainThreadWithResult(self.saveRegions, "")
                else:
                    utils.executeInMainThreadWithResult(self.saveRegions, command[1])
            #when told to load the regions send the regions back to Jigsaw 
            elif command[0].lower() == "loadregions":
                self.sockOut.sendall("loadregions="+utils.executeInMainThreadWithResult(self.loadRegions)+"\n")
            
        conn.close()
        try:
            os.remove(self.tempFile)
        except:
            pass
    #if we failed to get the screen shot the first time then let the user know.  This will be run on the main thread
    def failedScreenshot(self):
        cmds.confirmDialog( title='Unable to open Jigsaw', message='Failed to get screenshot.\nPlease make sure the current Viewport is selected')
    def requestSave(self):
        self.sockOut.sendall("requestSave\n")
    #Save the regions to the scene
    def saveRegions(self, regions):
        try:
            #create a jigsaw settings node if one doesn't exist yet
            if not cmds.objExists("JigsawSettings"):
                cmds.createNode("unknown", name="JigsawSettings")
                cmds.addAttr("JigsawSettings",longName="totalRegions", at="long",dv=0, k=True)
                cmds.addAttr("JigsawSettings",longName="JigsawRegions", dt="Int32Array", k=True)
            mayaRegions = []
            curRegion = 0
            for region in regions.split(";"):
                #if we need to create a new regions, then add one
                #print region
                if not cmds.objExists("JigsawSettings.JigsawRegion"+str(curRegion)):
                    cmds.addAttr("JigsawSettings",longName="JigsawRegion"+str(curRegion), at="compound",nc=8, k=True)
                    cmds.addAttr("JigsawSettings",longName="Region"+str(curRegion)+"xPos",at="double",parent = "JigsawRegion"+str(curRegion))
                    cmds.addAttr("JigsawSettings",longName="Region"+str(curRegion)+"yPos",at="double",parent = "JigsawRegion"+str(curRegion))
                    cmds.addAttr("JigsawSettings",longName="Region"+str(curRegion)+"width",at="double",parent = "JigsawRegion"+str(curRegion))
                    cmds.addAttr("JigsawSettings",longName="Region"+str(curRegion)+"height",at="double",parent = "JigsawRegion"+str(curRegion))
                    cmds.addAttr("JigsawSettings",longName="Region"+str(curRegion)+"tilesInX",at="long",parent = "JigsawRegion"+str(curRegion))
                    cmds.addAttr("JigsawSettings",longName="Region"+str(curRegion)+"tilesInY",at="long",parent = "JigsawRegion"+str(curRegion))
                    cmds.addAttr("JigsawSettings",longName="Region"+str(curRegion)+"enabled",at="bool",parent = "JigsawRegion"+str(curRegion))
                    cmds.addAttr("JigsawSettings",longName="Region"+str(curRegion)+"Active",at="bool",parent = "JigsawRegion"+str(curRegion))
                data = region.split(",") 
                if len(data)==7:
                    cmds.setAttr("JigsawSettings.Region"+str(curRegion)+"xPos", float(data[0])/float(self.usingWidth))
                    cmds.setAttr("JigsawSettings.Region"+str(curRegion)+"yPos", float(data[1])/float(self.usingHeight))
                    cmds.setAttr("JigsawSettings.Region"+str(curRegion)+"width", float(data[2])/float(self.usingWidth))
                    cmds.setAttr("JigsawSettings.Region"+str(curRegion)+"height", float(data[3])/float(self.usingHeight))
                    cmds.setAttr("JigsawSettings.Region"+str(curRegion)+"tilesInX", int(data[4]))
                    cmds.setAttr("JigsawSettings.Region"+str(curRegion)+"tilesInY", int(data[5]))
                    cmds.setAttr("JigsawSettings.Region"+str(curRegion)+"enabled", to_bool(data[6]))
                    cmds.setAttr("JigsawSettings.Region"+str(curRegion)+"Active", True)
                    cmds.setKeyframe("JigsawSettings", attribute ="JigsawRegion"+str(curRegion))
                    curRegion +=1
            #if we have more regions then were saved this time go through all of the remaining regions and set them to inactive.
            totalRegions = cmds.getAttr("JigsawSettings.totalRegions")
            if curRegion > totalRegions:
                cmds.setAttr("JigsawSettings.totalRegions", curRegion)
            else:
                for i in range(curRegion,totalRegions):
                    cmds.setAttr("JigsawSettings.Region"+str(i)+"Active", False)
                    cmds.setKeyframe("JigsawSettings", attribute ="JigsawRegion"+str(i))
            
            cmds.setAttr("JigsawSettings.JigsawRegions", mayaRegions, type = "Int32Array")
            cmds.setKeyframe("JigsawSettings", at = "JigsawRegions")
        except:
            print(traceback.format_exc())
    
    #Create a string out of all of the saved regions and return them.
    def loadRegions(self):
        if cmds.objExists("JigsawSettings"):
            if cmds.objExists("JigsawSettings.JigsawRegions"):
                regionCount = cmds.getAttr("JigsawSettings.totalRegions")
                result =""
                for i in range(0,regionCount):
                    if cmds.getAttr("JigsawSettings.Region"+str(i)+"Active"):
                        if i>0:
                            result+=";"

                        data = str(int(cmds.getAttr("JigsawSettings.Region"+str(i)+"xPos")*self.usingWidth)) +","
                        data += str(int(cmds.getAttr("JigsawSettings.Region"+str(i)+"yPos")*self.usingHeight)) +","
                        data += str(int(cmds.getAttr("JigsawSettings.Region"+str(i)+"width")*self.usingWidth)) +","
                        data += str(int(cmds.getAttr("JigsawSettings.Region"+str(i)+"height")*self.usingHeight)) +","
                        data += str(cmds.getAttr("JigsawSettings.Region"+str(i)+"tilesInX")) +","
                        data += str(cmds.getAttr("JigsawSettings.Region"+str(i)+"tilesInY"))+","
                        data += str(cmds.getAttr("JigsawSettings.Region"+str(i)+"enabled"))
                        result += str(data)
                return result
        return ""
    
    #Get the Jigsaw UI to return all of the regions and return an array of the ints with the appropriate positions
    def getRegions(self, invert = True):
        self.sockOut.sendall("getrenderregions\n")
        data = recvData(self.sockOut)
        renderHeight = cmds.getAttr('defaultResolution.height')
        renderWidth = cmds.getAttr('defaultResolution.width')
        
        widthMultiplier = renderWidth/(self.usingWidth+0.0)
        heightMultiplier = renderHeight/(self.usingHeight+0.0)
                
        regionString = str(data)
        regionData = regionString.split("=")
        regions = []
        if regionData[0] == "renderregion" and len(regionData) >1:
            regionData = regionData[1]
            regionData = regionData.split(";")
            for region in regionData:
                coordinates = region.split(",")
                if len(coordinates) == 4:
                    regions.append( int( (float(coordinates[0])*widthMultiplier) +0.5) )
                    regions.append(int( ( (float(coordinates[0])+float(coordinates[2])) *widthMultiplier) +0.5))
                    if invert:
                        value = int((float(coordinates[1])+float(coordinates[3]))*heightMultiplier +0.5)
                        regions.append(renderHeight - value)
                        value = int(float(coordinates[1])*heightMultiplier +0.5)
                        regions.append(renderHeight-value)
                    else:
                        regions.append( int( (float(coordinates[1])*heightMultiplier) +0.5) )
                        regions.append(int( ( (float(coordinates[1])+float(coordinates[3])) *heightMultiplier) +0.5))
        return regions
    
    #get the screenshot of the current viewport by playblasting it.
    def getScreenshot(self):
        #takes a screenshot of the current viewport
        if self.tempFile is None:
            filename = str(uuid.uuid4())
            self.tempFile = tempfile.gettempdir()+os.sep+filename+".png"
            
        cam = cmds.optionMenuGrp("frw_camera",q=True,value=True)
        
        #if not cam == "":
        #    cmds.lookThru(cam)
            
            
        panel = cmds.getPanel( withFocus=True )
        camera = ""
        if "modelPanel" == cmds.getPanel(typeOf=panel):
            camera = cmds.modelEditor(panel, q=True, camera=True)#`modelEditor -q -camera $panel`;
        else:
            return "screenshot"
            
        filmGate = cmds.camera(camera, q=True, displayFilmGate=True)
        resolutionGate = cmds.camera(camera, q=True, displayResolution=True)
        cmds.camera(camera,e=True, displayFilmGate=False)
        cmds.camera(camera,e=True, displayResolution=False)
        format = cmds.getAttr("defaultRenderGlobals.imageFormat")
        cmds.setAttr("defaultRenderGlobals.imageFormat", 32)
        
        modelWidth = cmds.layout(panel, q = True, width=True)
        modelHeight = cmds.layout(panel, q = True, height=True)
        
        renderWidth = cmds.getAttr("defaultResolution.width")
        renderHeight = cmds.getAttr("defaultResolution.height")
        
        if renderWidth < modelWidth and renderHeight<modelHeight:
            self.usingWidth = renderWidth
            self.usingHeight = renderHeight
        else:
            renderRatio = renderWidth/(renderHeight+0.0)
            widthRatio = renderWidth/(modelWidth+0.0)
            heightRatio = renderHeight/(modelHeight+0.0)
            if widthRatio<=1 and heightRatio<=1:
                usingWidth = renderWidth
                usingHeight = renderHeight
            elif widthRatio > heightRatio:
                self.usingWidth = int(modelWidth)
                self.usingHeight = int(modelWidth/renderRatio)
            else:
                self.usingWidth = int(modelHeight*renderRatio)
                self.usingHeight = int(modelHeight)
               
        time = cmds.currentTime( query=True )
        cmds.playblast(frame=time, format="image",cf=self.tempFile, v =0,orn=0,w=self.usingWidth, h=self.usingHeight, p = 100)
        cmds.setAttr("defaultRenderGlobals.imageFormat",format)
        cmds.camera(camera, e=True, displayFilmGate=filmGate)
        cmds.camera(camera, e=True, displayResolution=resolutionGate)
        return "screenshot="+self.tempFile
    
    #Let jigsaw know that we want it to exit.
    def closeJigsaw(self):
        self.sockOut.sendall("exit\n")
    
    def setGates(self, vals):
        panel = cmds.getPanel( withFocus=True )
        camera = ""
        if "modelPanel" == cmds.getPanel(typeOf=panel):
            camera = cmds.modelEditor(panel, q=True, camera=True)#`modelEditor -q -camera $panel`;
            
        filmGate = cmds.camera(camera, q=True, displayFilmGate=True)
        resolutionGate = cmds.camera(camera, q=True, displayResolution=True)
        cmds.camera(camera,e=True, displayFilmGate=vals[0])
        cmds.camera(camera,e=True, displayResolution=vals[1])
        return [filmGate,resolutionGate]
    
    def getFilmFit(self):
        panel = cmds.getPanel( withFocus=True )
        camera = ""
        if "modelPanel" == cmds.getPanel(typeOf=panel):
            camera = cmds.modelEditor(panel, q=True, camera=True)#`modelEditor -q -camera $panel`;
        return cmds.camera(camera, q=True, filmFit = True)
        
        
    #get the bounding regions of all of the selected objects
    #Mode = False: Tight vertex based bounding box
    #Mode = True: Loose Bounding box based
    def getSelectedBoundingRegion(self, mode=False, padding = 0.0):
        # get current render width and height settings
        renderHeight = cmds.getAttr('defaultResolution.height')
        renderWidth = cmds.getAttr('defaultResolution.width')
        
        widthMultiplier = renderWidth/(self.usingWidth+0.0)
        heightMultiplier = renderHeight/(self.usingHeight+0.0)
        
        gates = utils.executeInMainThreadWithResult( self.setGates, [False,False] )
        
        # get the active viewport
        activeView = OpenMayaUI.M3dView.active3dView()

        # define python api pointers to get data from api class
        xPtrInit = OpenMaya.MScriptUtil()
        yPtrInit = OpenMaya.MScriptUtil()
        widthPtrInit = OpenMaya.MScriptUtil()
        heightPtrInit = OpenMaya.MScriptUtil()

        xPtr = xPtrInit.asUintPtr()
        yPtr = yPtrInit.asUintPtr()
        widthPtr = widthPtrInit.asUintPtr()
        heightPtr = heightPtrInit.asUintPtr()

        # retreive viewport width and height
        activeView.viewport(xPtr, yPtr, widthPtr, heightPtr)
        viewX = xPtrInit.getUint( xPtr )
        viewY = yPtrInit.getUint( yPtr )
        viewWidth = widthPtrInit.getUint( widthPtr )
        viewHeight = heightPtrInit.getUint( heightPtr )
        
        # determine aspect ratio of render size
        # then determine what the viewport renderable height is
        aspectRatio = float(renderHeight) / float(renderWidth)
        heightDiff = 0  # actual viewport renderable pixels
        heightClip = 0	# area of user viewport not renderable

        # get the active selection
        selection = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList( selection )
        iterSel = OpenMaya.MItSelectionList(selection, OpenMaya.MFn.kMesh)

        # loop through the selected nodes
        boundingBoxes = []
        while not iterSel.isDone():
            # bounding box vars
            minX = 0
            maxX = 0
            minY = 0
            maxY = 0

            iterGeoNum = 0
            
            if mode == 0:#by vertex
                dagPath = OpenMaya.MDagPath()
                iterSel.getDagPath( dagPath )
                iterGeo = OpenMaya.MItGeometry( dagPath )

                # iterate through vertex positions
                # check each vertex position and get its x, y cordinate in the viewport
                # generate the minimum x and y position and the max x and y position
                
                while not iterGeo.isDone():
                    vertexMPoint = iterGeo.position(OpenMaya.MSpace.kWorld)
                    xPosShortPtrInit = OpenMaya.MScriptUtil()
                    yPosShortPtrInit = OpenMaya.MScriptUtil()
                    xPosShortPtr = xPosShortPtrInit.asShortPtr()
                    yPosShortPtr = yPosShortPtrInit.asShortPtr()

                    activeView.worldToView(vertexMPoint, xPosShortPtr, yPosShortPtr)

                    xPos = xPosShortPtrInit.getShort(xPosShortPtr)
                    yPos = yPosShortPtrInit.getShort(yPosShortPtr)
                    if iterGeoNum == 0:
                        minX = xPos
                        minY = yPos

                    if xPos < minX: minX = xPos
                    if xPos > maxX: maxX = xPos
                    if yPos < minY: minY = yPos
                    if yPos > maxY: maxY = yPos
                    
                    iterGeoNum = iterGeoNum + 1
                    iterGeo.next()
            elif mode == 1: #by boundingbox
                objNames = []
                iterSel.getStrings(objNames)
                
                for name in objNames:
                    bbox = cmds.exactWorldBoundingBox(name)
                    XVals = [bbox[0],bbox[3]]
                    YVals = [bbox[1],bbox[4]]
                    ZVals = [bbox[2],bbox[5]]
                    #print bbox
                
                    for x in XVals:
                        for y in YVals:
                            for z in ZVals:
                                point = OpenMaya.MPoint(x,y,z)
                                xPosShortPtrInit = OpenMaya.MScriptUtil()
                                yPosShortPtrInit = OpenMaya.MScriptUtil()
                                xPosShortPtr = xPosShortPtrInit.asShortPtr()
                                yPosShortPtr = yPosShortPtrInit.asShortPtr()
                                
                                activeView.worldToView(point, xPosShortPtr, yPosShortPtr)

                                xPos = xPosShortPtrInit.getShort(xPosShortPtr)
                                yPos = yPosShortPtrInit.getShort(yPosShortPtr)
                                if iterGeoNum == 0:
                                    minX = xPos
                                    minY = yPos

                                if xPos < minX: minX = xPos
                                if xPos > maxX: maxX = xPos
                                if yPos < minY: minY = yPos
                                if yPos > maxY: maxY = yPos
                                iterGeoNum = iterGeoNum + 1
            # move on to next selected node
            iterSel.next()
            
            # the renderWindowCheckAndRenderRegion arguments are ymax, xmin, ymin, xmax		
            # convert the min max values to scalars between 0 and 1
            minXScalar = 0
            maxXScalar = 0
            minYScalar = 0
            maxYScalar = 0
            
            filmFit = ""
            filmFit =  utils.executeInMainThreadWithResult( self.getFilmFit )
            if filmFit == "horizontal":
                renderableHeight = viewWidth * aspectRatio
                heightDiff = viewHeight - renderableHeight
                heightClip = heightDiff / 2
                
                minXScalar = float(minX)/float(viewWidth)
                maxXScalar = float(maxX)/float(viewWidth)
                    
                if(renderWidth > renderHeight or heightDiff < 0 ):
                    minYScalar = ( float( minY ) - heightClip ) / float( renderableHeight )
                    maxYScalar = ( float( maxY ) - heightClip ) / float( renderableHeight )
                    
                else:
                    minYScalar = ( float( minY ) + heightClip ) / float( renderableHeight )
                    maxYScalar = ( float( maxY ) + heightClip ) / float( renderableHeight )
                    
            elif filmFit == "vertical":
                renderableWidth = viewHeight / aspectRatio
                widthDiff = viewWidth - renderableWidth
                widthClip = widthDiff / 2
                
                minYScalar = float(minY)/float(viewHeight)
                maxYScalar = float(maxY)/float(viewHeight)
                
                if( renderHeight > renderWidth or widthDiff < 0  ):
                    minXScalar = ( float( minX ) - widthClip ) / float( renderableWidth )
                    maxXScalar = ( float( maxX ) - widthClip ) / float( renderableWidth )
                else:
                    minXScalar = ( float( minX ) + widthClip ) / float( renderableWidth )
                    maxXScalar = ( float( maxX ) + widthClip ) / float( renderableWidth )               
            

            # define viewport pixel based bounding box and scalar bounding box
            # scalar is the only one useful for rendering a region
            
            padding = max(padding,0.0)
            
            x = minXScalar*renderWidth
            y = renderHeight - maxYScalar*renderHeight
            #y = renderHeight-(renderWidth*maxYScalar+0.5)
            width = (maxXScalar-minXScalar)*renderWidth+1.5
            height = renderHeight*(maxYScalar-minYScalar)+1.5
                        
            xPadding = int(((width*padding)/200)+0.5)
            yPadding = int(((height*padding)/200)+0.5)
            
            x1 = int((x-xPadding)/widthMultiplier+0.5)
            y1 = int((y-yPadding)/heightMultiplier+0.5)
            x2 = int((width+xPadding*2)/widthMultiplier+0.5)
            y2 = int((height+yPadding*2)/heightMultiplier+0.5)
            
            boundingBoxFinalRegion = [ x1, y1, x2, y2 ]
            boundingBoxes.append(boundingBoxFinalRegion)
            
            print("Added Bounding Box")
        
        print("Done Select Bounding Region")
        
        utils.executeInMainThreadWithResult( self.setGates, gates )
        
        return boundingBoxes
    
    #find a random open port to connect to
    def get_open_port(self):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        port = s.getsockname()[1]
        s.close()
        return port

#Call Deadline command
def CallDeadlineCommand( arguments, hideWindow=True, readStdout=True ):
    environment = None
    
    deadlineCommand = GetDeadlineCommand()
            
    if os.name == 'nt':
        
        # Need to set the PATH, cuz windows 8 seems to load DLLs from the PATH earlier that cwd....
        environment = {}
        for key in os.environ.keys():
            environment[key] = str(os.environ[key])
        environment['PATH'] = str(os.path.dirname( deadlineCommand ) + ";" + os.environ['PATH'])
    
    startupinfo = None
    if hideWindow and os.name == 'nt':
        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    stdoutPipe = None
    if readStdout:
        stdoutPipe=subprocess.PIPE
    
    arguments.insert( 0, deadlineCommand)
        
    proc = subprocess.Popen(arguments, stdout=stdoutPipe, startupinfo=startupinfo, env=environment)
    
    output = ""
    if readStdout:
        output = proc.stdout.read()
    
    return output

def recvData(theSocket):
    totalData=[]
    data=''
    while True:
        data=theSocket.recv(8192)
        if not data:
            return
        if "\n" in data:
            totalData.append(data[:data.find("\n")])
            break
        totalData.append(data)
    return ''.join(totalData)
    
def to_bool(value):
    valid = {'true': True, 't': True, '1': True,
             'false': False, 'f': False, '0': False,
             }   

    if isinstance(value, bool):
        return value

    if not isinstance(value, basestring):
        raise ValueError('invalid literal for boolean. Not a string.')

    lower_value = value.lower()
    if lower_value in valid:
        return valid[lower_value]
    else:
        raise ValueError('invalid literal for boolean: "%s"' % value)
    
if __name__ == '__main__':
    jigsawThread = MyThread(name="JigsawThread")
    jigsawThread.start()
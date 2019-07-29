import os
import re

from System.IO import *

from Deadline.Scripting import *
from Deadline.Plugins import *
from System.Text.RegularExpressions import *

def GetDeadlinePlugin():
    return VrayPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class VrayPlugin(DeadlinePlugin):
    CurrFrame = -1
    TotalFrames = -1
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess(self):
        self.SingleFramesOnly = True
        self.StdoutHandling = True
        
        self.AddStdoutHandlerCallback( "Subdividing frame ([0-9]+) of ([0-9]+)" ).HandleCallback += self.HandleFrameProgress
        self.AddStdoutHandlerCallback( "Processing voxel ([0-9]+) of ([0-9]+)" ).HandleCallback += self.HandleVoxelProgress
        
    def RenderExecutable(self):
        version = self.GetPluginInfoEntryWithDefault( "Version", "3" )
        self.LogInfo("Using Ply2Vrmesh version " + version )
        
        exeList = self.GetConfigEntry( "Ply2Vrmesh_RenderExecutable_" + version )
        exe = FileUtils.SearchFileList( exeList )
        if( exe == "" ):
            self.FailRender( "Ply2Vrmesh " + version + " render executable was not found in the semicolon separated list \"" + exeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return exe
        
    def RenderArgument(self):
        version = self.GetIntegerPluginInfoEntryWithDefault( "Version", 3 )
        
        arguments = ""
        
        filename = self.GetPluginInfoEntry( "InputFile" ).strip()
        filename = RepositoryUtils.CheckPathMapping( filename )
        filename = self.FixPath( filename )
        
        if not self.GetBooleanPluginInfoEntryWithDefault("MergeOutputFiles",False):
            paddingRegex = Regex( "(#+)\.")
            match = paddingRegex.Match(filename)
            if match.Success:
                value = match.Groups[ 1 ].Value
                frame = self.GetStartFrame()
                frame = StringUtils.ToZeroPaddedString( frame, len(value) )
                
                filename = re.sub( "(#+)\.", frame+".", filename ) 
        
        arguments = arguments + " \"" + filename + "\""
        
        outFilename = self.GetPluginInfoEntryWithDefault( "OutputFile", "" ).strip()
        if outFilename != "":
            outFilename = RepositoryUtils.CheckPathMapping( outFilename )
            outFilename = self.FixPath( outFilename )
            
            if not self.GetBooleanPluginInfoEntryWithDefault("MergeOutputFiles",False):
                paddingRegex = Regex( "(#+)\.")
                match = paddingRegex.Match(outFilename)
                if match.Success:
                    value = match.Groups[ 1 ].Value
                    frame = self.GetStartFrame()
                    frame = StringUtils.ToZeroPaddedString( frame, len(value) )
                    outFilename = re.sub( "(#+)\.", frame+".", outFilename ) 
            
            arguments = arguments + " \"" + outFilename + "\""
            
        # appends the information as a new frame to the .vrmesh file
        if self.GetBooleanPluginInfoEntryWithDefault( "Append", False ):
            arguments = arguments + " -append"
        
        # generates smooth vertex normals. Only valid for .obj and .geo files; always enabled for .bin files
        if self.GetBooleanPluginInfoEntryWithDefault( "SmoothNormals", False ) and (self.IsObj( filename ) or self.IsGeo( filename )):
            arguments = arguments + " -smoothNormals"
        
        # a floating point number that specifies the angle (in degrees) used to distinguish if the normals should be  smoothed or not. If present it automatically enables the -smoothNormals flag.
        if self.GetBooleanPluginInfoEntryWithDefault( "SetSmoothAngle", False ):
            smoothAngle = self.GetFloatPluginInfoEntryWithDefault( "SmoothAngle", -1.0 )
            if smoothAngle >= 0.0:
                arguments = arguments + " -smoothAngle " + str(smoothAngle)
        
        # reverses the face/vertex normals. Only valid for .obj, .geo and .bin files
        if self.GetBooleanPluginInfoEntryWithDefault( "FlipNormals", False ) and (self.IsObj( filename ) or self.IsGeo( filename ) or self.IsBin( filename )):
            arguments = arguments + " -flipNormals"
        
        # reverses the vertex normals. Only valid for .obj, .geo and .bin files
        if self.GetBooleanPluginInfoEntryWithDefault( "FlipVertexNormals", False ) and (self.IsObj( filename ) or self.IsGeo( filename ) or self.IsBin( filename )):
            arguments = arguments + " -flipVertexNormals"
        
        # reverses the face normals. Only valid for .obj, .geo and .bin files
        if self.GetBooleanPluginInfoEntryWithDefault( "FlipFaceNormals", False ) and (self.IsObj( filename ) or self.IsGeo( filename ) or self.IsBin( filename )):
            arguments = arguments + " -flipFaceNormals"
        
        # swap y/z axes. Needed for some programs i.e. Poser, ZBrush. Valid for .ply, .obj, .geo and .bin files.
        if self.GetBooleanPluginInfoEntryWithDefault( "FlipYZ", False ) and (self.IsPly( filename ) or self.IsObj( filename ) or self.IsGeo( filename ) or self.IsBin( filename )):
            arguments = arguments + " -flipYZ"
        
        # same as -flipYZ but does not reverse the sign of the z coordinate.
        if self.GetBooleanPluginInfoEntryWithDefault( "FlipYPosZ", False ) and (self.IsPly( filename ) or self.IsObj( filename ) or self.IsGeo( filename ) or self.IsBin( filename )):
            arguments = arguments + " -flipYPosZ"
        
        # same as -flipYPosZ but swaps x/z axes.
        if version >= 3 and self.GetBooleanPluginInfoEntryWithDefault( "FlipXPosZ", False ) and (self.IsPly( filename ) or self.IsObj( filename ) or self.IsGeo( filename ) or self.IsBin( filename )):
            arguments = arguments + " -flipXPosZ"
        
        # stores the UVW coordinates to the specified mapping channel (default is 1). Only valid for .obj and .geo files. When exporting a mesh that will be used in Maya,
        # currently this must be set to 0 or the textures on the mesh will not render properly
        mapChannel = self.GetIntegerPluginInfoEntryWithDefault( "MapChannel", 1 )
        if mapChannel >= 0 and (self.IsObj( filename ) or self.IsGeo( filename )):
            arguments = arguments + " -mapChannel " + str(mapChannel)
        
        # only valid for .geo and .bgeo files; disables the packing of float1 and float2 attributes in vertex color sets.
        if self.GetBooleanPluginInfoEntryWithDefault( "DisableColorSetPacking", False ) and (self.IsGeo( filename ) or self.IsBGeo( filename )):
            arguments = arguments + " -disableColorSetPacking"
        
        # only valid for .geo files; assigns material IDs based on the primitive groups in the file.
        if self.GetBooleanPluginInfoEntryWithDefault( "MaterialIDs", False ) and self.IsGeo( filename ):
            arguments = arguments + " -materialIDs"
        
        # a floating-point number that specifies the frames per second at which a .geo or .bin file is exported, so that vertex velocities can be scaled accordingly. The default is 24.0
        fps = self.GetFloatPluginInfoEntryWithDefault( "FPS", 24.0 )
        if fps >= 0.0 and (self.IsGeo( filename ) or self.IsBin( filename )):
            arguments = arguments + " -fps " + str(fps)
        
        # specifies the maximum number of faces in the .vrmesh preview information. Default is 9973 faces.
        previewFaces = self.GetIntegerPluginInfoEntryWithDefault( "PreviewFaces", 9973 )
        if previewFaces >= 0:
            arguments = arguments + " -previewFaces " + str(previewFaces)
            
        # specifies the maximum number of faces per voxel in the resulting .vrmesh file. Default is 10000 faces.
        facesPerVoxel = self.GetIntegerPluginInfoEntryWithDefault( "FacesPerVoxel", 10000 )
        if facesPerVoxel >= 0:
            arguments = arguments + " -facesPerVoxel " + str(facesPerVoxel)
            
        # specifies the maximum number of hairs in the .vrmesh preview information. Default is 500 hairs.
        previewHairs = self.GetIntegerPluginInfoEntryWithDefault( "PreviewHairs", 500 )
        if version >= 3 and previewHairs >= 0:
            arguments = arguments + " -previewHairs " + str(previewHairs)
            
        # specifies maximum segments per voxel in the resulting .vrmesh file. Default is 64000 hairs.
        segmentsPerVoxel = self.GetIntegerPluginInfoEntryWithDefault( "SegmentsPerVoxel", 64000 )
        if version >= 3 and segmentsPerVoxel >= 0:
            arguments = arguments + " -segmentsPerVoxel " + str(segmentsPerVoxel)
        
        # specifies the multiplier to scale hair widths in the resulting .vrmesh file. Default is 1.0.
        hairWidthMultiplier = self.GetFloatPluginInfoEntryWithDefault( "HairWidthMultiplier", 1.0 )
        if version >= 3 and hairWidthMultiplier > 0.0:
            arguments = arguments + " -hairWidthMultiplier " + str(hairWidthMultiplier)
        
        # specifies the maximum number of particles in the .vrmesh preview information. Default is 20000 particles.
        previewParticles = self.GetIntegerPluginInfoEntryWithDefault( "PreviewParticles", 20000 )
        if version >= 3 and previewParticles >= 0:
            arguments = arguments + " -previewParticles " + str(previewParticles)
        
        # specifies maximum particles per voxel in the resulting .vrmesh file. Default is 64000 particles.
        particlesPerVoxel = self.GetIntegerPluginInfoEntryWithDefault( "ParticlesPerVoxel", 64000 )
        if version >= 3 and particlesPerVoxel >= 0:
            arguments = arguments + " -particlesPerVoxel " + str(particlesPerVoxel)

        # specifies the multiplier to scale particles in the resulting .vrmesh file. Default is 1.0.
        particleWidthMultiplier = self.GetFloatPluginInfoEntryWithDefault( "ParticleWidthMultiplier", 1.0 )
        if version >= 3 and particleWidthMultiplier > 0.0:
            arguments = arguments + " -particleWidthMultiplier " + str(particleWidthMultiplier)
        
        # merge objects before voxelization to reduce overlapping voxels
        if version >= 3 and self.GetBooleanPluginInfoEntryWithDefault( "MergeVoxels", False ):
            arguments = arguments + " -mergeVoxels"
        
        # specifies the name of the point attribute which should be used to generate the velocity channel. By default the 'v' attribute is used.
        velocityAttrName = self.GetPluginInfoEntryWithDefault( "VelocityAttrName", "v" ).strip()
        if len(velocityAttrName) > 0:
            arguments = arguments + " -velocityAttrName " + str(velocityAttrName)
        
        if self.GetBooleanPluginInfoEntryWithDefault("MergeOutputFiles",False):
            arguments = arguments + " -mergeFiles"

        if self.IsVrscene( filename ):
            vrsceneNodeName = self.GetPluginInfoEntry( "VrsceneNodeName" )

            # Sanity check when no vrscene node is specified. The submitter prevents this in the user interface, but
            # it might happen with manual job submission. Fail the render with a helpful error message.
            if not vrsceneNodeName:
                self.FailRender( "No node name was specified for the VRSCENE file" )

            arguments = arguments + " -vrsceneNodeName " + vrsceneNodeName

            if self.GetBooleanPluginInfoEntryWithDefault( "VrsceneApplyTm", False):
                arguments = arguments + " -vrsceneApplyTm"

            if self.GetBooleanPluginInfoEntryWithDefault( "VrsceneVelocity", False ):
                arguments = arguments + " -vrsceneVelocity"

            vrsceneFrames = self.GetPluginInfoEntryWithDefault( "VrsceneFrames", "" )
            if vrsceneFrames:
                arguments = arguments + " -vrsceneFrames " + vrsceneFrames
        
        return arguments
    
    def FixPath( self, path ):
        if SystemUtils.IsRunningOnWindows():
            # Check if it is a unc path
            if(path.startswith("\\")):
                if(path[0:2] != "\\\\"):
                    path = "\\" + path
            elif(path.startswith("/")):
                if(path[0:2] != "//"):
                    path = "/" + path
        else:
            path = path.replace("\\","/")
            if(path[0:2] == "//"):
                path = path[1:-1]
        
        return path
    
    def IsObj( self, file ):
        return ( Path.GetExtension( file ).lower() == ".obj" )
    
    def IsBin( self, file ):
        return ( Path.GetExtension( file ).lower() == ".bin" )
    
    def IsGeo( self, file ):
        return ( Path.GetExtension( file ).lower() == ".geo" )
    
    def IsBGeo( self, file ):
        return ( Path.GetExtension( file ).lower() == ".bgeo" )
    
    def IsPly( self, file ):
        return ( Path.GetExtension( file ).lower() == ".ply" )

    def IsVrscene( self, path ):
        return ( Path.GetExtension( path ).lower() == ".vrscene" )
        
    def HandleFrameProgress( self ):
        self.CurrFrame = int(self.GetRegexMatch(1))
        self.TotalFrames = int(self.GetRegexMatch(2))
    
    def HandleVoxelProgress( self ):
        if self.CurrFrame != -1 and self.TotalFrames != -1 and self.TotalFrames != 0:
            currVoxel = int(self.GetRegexMatch(1))
            totalVoxels = int(self.GetRegexMatch(2))
            
            if totalVoxels != 0:
                frameProgress = 100.0 * float(self.CurrFrame - 1) / float(self.TotalFrames)
                voxelProgress = 100.0 * float(currVoxel - 1) / float(totalVoxels)
                totalProgress = frameProgress + (voxelProgress / float(self.TotalFrames))
            
                self.SetProgress( totalProgress )
                self.SetStatusMessage( "Subdividing frame " + str(self.CurrFrame) + " of " + str(self.TotalFrames) + ", processing voxel " + str(currVoxel) + " of " + str(totalVoxels) )

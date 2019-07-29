from __future__ import print_function
import os
import re
import shutil
import sys
import tempfile

import Draft

control_chars = ''.join(map(unichr, range(0,32)+range(127,160)))
control_char_re = re.compile('[%s]' % re.escape(control_chars))

def remove_control_chars(s):
    return control_char_re.sub('', s)

# Make sure we were given a config file so we can complete an assembly job
if len(sys.argv) < 2:
    raise Exception( "No control file given" )

try:
    controlFile = sys.argv[1]
    # We are going to assume that we are to error on missing tiles unless we are told otherwise
    errorOnMissing = True

    if len(sys.argv) > 2:
        errorOnMissingStr = sys.argv[2].lower()
        if errorOnMissingStr != "true" and errorOnMissingStr != "1":
            errorOnMissing = False

    print( "Error on missing tiles = " + str(errorOnMissing) )

    errorOnMissingBackground = True

    if len(sys.argv) > 4:
        errorOnMissingBackgroundStr = sys.argv[4].lower()
        if errorOnMissingBackgroundStr != "true" and errorOnMissingBackgroundStr != "1":
            errorOnMissingBackground = False

    print( "Error on missing Background = " + str(errorOnMissingBackground) )

    tempFolder = tempfile.gettempdir()
    if len(sys.argv) > 5:
        tempFolder = sys.argv[5]
        
    print( 'Temporary Folder = "%s"' % tempFolder )

    data = {}
    #open the config file as a unicode file (since some of our submitters write unicode files)
    with open(controlFile, "rU") as f:
        for line in f:
            text = line.strip()
            #remove all non printable characters most notably unicode start file characters
            text = remove_control_chars(text)
            info = text.split("=", 1)
            if len(info) > 1:
                try:
                    data[str(info[0])] = info[1]
                except:
                    #should never be called
                    print( "Failed" )

    # Default the height and width of the new image to be -1 this is done as a precaution
    configWidth = -1
    configHeight = -1
    imagesDict = {}

    # Find out if the distances given are in pixels or 0.0-1.0 range
    distanceAsPixels = True
    if "DistanceAsPixels" in data:
        if data["DistanceAsPixels"].lower() == "false" or data["DistanceAsPixels"] == "0":
            distanceAsPixels = False

    print( "Distance as pixels = " + str(distanceAsPixels) )

    channelNames = None
    imageInfo = None
    tileImageInfo = None

    # The draft tile assembler can put together all files with given prefixes in folders or individual given files
    if not "ImageFolder" in data:
        print( "Assembling Single File" )

        # Create the assembler that will handle all the stitching
        assembler = Draft.TileAssembler()
        
        assemblingFileName = data["ImageFileName"]
        tempFileName = os.path.join(tempFolder, os.path.basename(assemblingFileName))
        try:
            print( "Assembling File: " + assemblingFileName )
            print( "Writing File to temporary location: " + tempFileName )
        except:
            print( "No final file name given" )
            raise

        if "ImageWidth" in data and "ImageHeight" in data:
            configWidth = int(data["ImageWidth"])
            configHeight = int(data["ImageHeight"])

        if data["TilesCropped"].lower() != "true" and data["TilesCropped"] != "1":
            print( "Tiles are not cropped" )
        else:
            print( "Tiles are cropped" )

        if "BackgroundSource" in data:
            print( "Background Source Provided" )
            try:
                imageInfo = Draft.ImageInfo()
                backgroundImage = Draft.Image.ReadFromFile(data["BackgroundSource"], imageInfo)
                backgroundWidth = backgroundImage.width
                backgroundHeight = backgroundImage.height
                channelNames = backgroundImage.GetChannelNames()
                assembler.SetSize(backgroundWidth, backgroundHeight)
                assembler.AddTile(backgroundImage, 0, 0)

                print( "Background Source Found" )
                print( "Final Image Dimensions = " + str(backgroundWidth) + "x" + str(backgroundHeight) )
            except:
                if errorOnMissingBackground:
                    print( "Unable to read background source image: " + str(data["BackgroundSource"]) )
                    raise
                else:
                    print( "Unable to read background source image: " + data["BackgroundSource"] + ". Continuing with blank background" )
                    if(configWidth != -1 and configHeight != -1):
                        assembler.SetSize(configWidth, configHeight)
                        print( "Final Image Dimensions = " + str(configWidth) + "x" + str(configHeight) )
        # Otherwise if we were given a height and a width create a new image using the given height and width
        elif(configWidth != -1 and configHeight != -1):
            assembler.SetSize(configWidth, configHeight)
            print( "Final Image Dimensions = " + str(configWidth) + "x" + str(configHeight) )
        else:
            print( "Image height and width not provided. Final image dimensions will be based off first tile provided." )

        tileNum = 0

        if not "TileCount" in data:
            print( "No TileCount provided. A tile Count must be provided to perform assembly." )
            raise Exception( "A tile Count must be provided to perform assembly" )

        print( "TileCount given: " + str(data["TileCount"]) )

        # Go through each tile given up to a max of tile count
        while tileNum < int(data["TileCount"]):
            tileName = "Tile" + str(tileNum)
            # Try to read in the file
            try:
                tileImageInfo = Draft.ImageInfo()
                tileFilename = data[tileName + "FileName"]
                tileImage = Draft.Image.ReadFromFile(tileFilename, tileImageInfo)
            # If the tileFilename does not exist in our dictionary then handle it
            except KeyError:
                if errorOnMissing:
                    print( "Tile" + str(tileNum) + "FileName missing from configuration file" )
                    raise
                else:
                    print( "Tile" + str(tileNum) + "FileName missing from configuration file" )
                    print( "Skipping missing tile: " + str(tileNum) )
                    tileNum += 1
                    continue
            # If we were unable to read in the file handle it
            except Exception as e:
                if errorOnMissing:
                    print( "Unable to read file: " + tileFilename + " for tile: " + str(tileName) )
                    if "NoDecodeDelegateForThisImageFormat" in str(e):
                        print( "Invalid Format" )
                    elif "UnableToOpenBlob" in str(e):
                        print( "File does not exist" )
                    raise
                else:
                    print( "Unable to read file: " + tileFilename + " for tile: " + str(tileName) )
                    if "NoDecodeDelegateForThisImageFormat" in str(e):
                        print( "Invalid Format" )
                    elif "UnableToOpenBlob" in str(e):
                        print( "File does not exist" )
                    print( "Skipping missing tile: " + str(tileNum) )
                    tileNum += 1
                    continue

            if channelNames is None:
                channelNames = tileImage.GetChannelNames()

            # If a new image has not been created then the height and width will be negative 1
            if configWidth < 0 or configHeight < 0:
                # If the tiles are cropped then we have no basis for the final image so we raise an exception
                # Otherwise we use the dimensions of the first image
                if data["TilesCropped"].lower() == "true":
                    print( "Tiles are cropped and no width and height was specified." )
                    raise Exception( "Must specify width and height of final image if tiles are cropped." )

                configWidth = tileImage.width
                configHeight = tileImage.height

                assembler.SetSize(configWidth, configHeight)
                print( "Using height and width of image: " + data[tileName + "FileName"] )
                print( "Final Image Dimensions = " + str(configWidth) + "x" + str(configHeight) )

            # Get the position of the given tile
            try:
                x = float(data[tileName + "X"])
                y = float(data[tileName + "Y"])
            except:
                print( "No position given for tile: " + tileName )
                raise

            if not distanceAsPixels:
                x = float(x) * configWidth
                y = float(y) * configHeight
                x = int(x+0.5)
                y = int(y+0.5)
            else:
                x = int(x)
                y = int(y)

            # Crop the tiles if they are not currently cropped
            if data["TilesCropped"].lower() != "true" and data["TilesCropped"] != "1":
                try:
                    tileWidth = float(data[tileName + "Width"])
                    tileHeight = float(data[tileName + "Height"])
                except:
                    print( "No dimensions given for cropping: " + tileName )
                    raise

                left = float(data[tileName + "X"])
                bottom = float(data[tileName + "Y"])
                right = left + float(tileWidth)
                top = bottom + float(tileHeight)

                # Cropping is done using pixel amounts so convert all distances to pixels
                if not distanceAsPixels:
                    left = left * tileImage.width
                    bottom = bottom * tileImage.height
                    right = right * tileImage.width
                    top = top * tileImage.height

                # Round the dimensions to the nearest pixel
                left = int(left + 0.5)
                bottom = int(bottom + 0.5)
                right = int(right + 0.5)
                top = int(top + 0.5)

                print( tileName + " cropping area: [Left: " + str(left) + ", Right: " + str(right) + ", Top: " + str(top) + ", Bottom: " + str(bottom) + "]" )
                tileImage.Crop(left, bottom, right, top)
                
                tileWidth = tileImage.width
                tileHeight = tileImage.height
            else:
                tileWidth = tileImage.width
                tileHeight = tileImage.height

            print( tileName + " position: " + str(x) + ", " + str(y) )
            print( tileName + " dimension: " + str(tileWidth) + ", " + str(tileHeight) )

            tileChannels = tileImage.GetChannelNames()
            newChannels = list(set(tileChannels) - set(channelNames))

            for channel in newChannels:
                val = 0.0
                if channel.lower() == "a":
                    val = 1.0
                channelNames.append(channel)
                print( "Adding Channel: " + channel )

            # Add the tile to the Assembler
            assembler.AddTile(tileImage, x, y)
            tileNum += 1

        # Set image info from the last tile if not already set with background image's tile decription
        if imageInfo is None and tileImageInfo is not None:
            imageInfo = tileImageInfo

        if channelNames is not None:
            assembler.SetChannels(channelNames)
            print( "Total Number of Output Channels: " + str(len(channelNames)) )
            print( "Output Channels: " )
            for channelName in channelNames:
                print( str(channelName) )

        # Make sure the output order is respected
        sys.stdout.flush()

        # Perform the assembly job
        assembler.AssembleToFile(tempFileName, imageInfo)
        print( "Copying output file from: " + tempFileName + " to final output location: " + assemblingFileName )
        shutil.copyfile( tempFileName, assemblingFileName )
        try:
            print( "Deleting: '%s'" % tempFileName )
            os.remove(tempFileName)
        except:
            print( "Failed to remove: '%s'" % tempFileName )
        
    else:
        print( "Assembling Folder" )

        imageNum = 0
        tileNum = 0

        # Make sure that the config file contains the necessary information to get the correct files
        try:
            inputDirectory = data["ImageFolder"]
            print( "ImageFolder: " + inputDirectory )
            extension = data["ImageExtension"]
            print( "ImageExtension: " + str(extension) )
        except:
            print( "ImageExtension missing from config file" )
            raise

        # Make sure we have a tile count so we can complete the job
        if not "TileCount" in data:
            raise Exception( "A tile Count must be provided to perform assembly" )

        outputPrefix = ""
        if "ImagePrefix" in data:
            outputPrefix = data["ImagePrefix"]

        try:
            tileFileNames = os.listdir(inputDirectory)
        except:
            print( "Unable to read Image Folder: " + inputDirectory )
            raise

        if "ImageWidth" in data and "ImageHeight" in data:
            configWidth = int(data["ImageWidth"])
            configHeight = int(data["ImageHeight"])

        if data["TilesCropped"].lower() != "true" and data["TilesCropped"] != "1":
            print( "Tiles are not cropped" )
        else:
            print( "Tiles are cropped" )

        # Go through all files in the given directory and add all file names that match prefix extension
        fileCount = 0
        while tileNum < int(data["TileCount"]):
            try:
                tileName = "Tile" + str(tileNum)
                prefix = None
                try:
                    prefix = data[tileName + "Prefix"]
                except:
                    print( "Tile prefix: " + tileName + "Prefix missing from config File" )
                    raise 
                for tileFileName in tileFileNames:
                    if tileFileName.lower().startswith(prefix.lower()) and tileFileName.lower().endswith(extension.lower()):
                        nameWithoutPrefix = tileFileName.replace(prefix, "").replace(extension, "")
                        if nameWithoutPrefix not in imagesDict:
                            imagesDict[nameWithoutPrefix] = {}
                        print( "Found file: " + tileFileName + " matching: " + tileName + "Prefix: " + prefix )
                        imagesDict[nameWithoutPrefix][tileNum] = tileFileName
                        fileCount += 1
                tileNum += 1
            except:
                if errorOnMissing:
                    raise
                else:
                    print( "Continuing" )
                    tileNum += 1
        
        # For each unique key in the dictionary create an image
        fileNum = 0
        imageNum = 1
        totalImgCount = len(imagesDict)
        for key in imagesDict:
            print( "Assembling image: " + str(imageNum) + " of " + str(totalImgCount) )
            # Create the assembler that will handle all the stitching
            assembler = Draft.TileAssembler()

            channelNames = None
            imageInfo = Draft.ImageInfo()

            print( "Assembling File: " + inputDirectory + os.sep + key + extension )

            tileNum = 0
            # If given a background image use it as the base image
            if "BackgroundSource" in data:
                print( "Background Source Provided" )
                try:
                    imageInfo = Draft.ImageInfo()
                    backgroundImage = Draft.Image.ReadFromFile(data["BackgroundSource"], imageInfo)
                    backgroundWidth = backgroundImage.width
                    backgroundHeight = backgroundImage.height
                    channelNames = backgroundImage.GetChannelNames()

                    assembler.SetSize(backgroundWidth, backgroundHeight)
                    assembler.AddTile(backgroundImage, 0, 0)

                    print( "Background Source Found" )
                    print( "Final Image Dimensions = " + str(backgroundWidth) + "x" + str(backgroundHeight) )

                except:
                    if errorOnMissingBackground:
                        print( "Unable to read background source image: " + str(data["BackgroundSource"]) )
                        raise
                    else:
                        print( "Unable to read background source image: " + data["BackgroundSource"] + ". Continuing Render with blank background." )
                        if(configWidth != -1 and configHeight != -1):
                            assembler.SetSize(configWidth, configHeight)
                            print( "Final Image Dimensions = " + str(configWidth) + "x" + str(configHeight) )
            # Otherwise if we were given a height and a width create a new image using the given height and width
            elif(configWidth != -1 and configHeight != -1):
                assembler.SetSize(configWidth, configHeight)
                print( "Final Image Dimensions = " + str(configWidth) + "x" + str(configHeight) )
            else:
                print( "Image height and width not provided. Final image dimensions will be based off first tile provided." )

            # Go through each tile given up to a max of tile count
            while tileNum < int(data["TileCount"]):
                tileName = "Tile" + str(tileNum)
                print( "Retrieving: " + tileName )
                try:
                    filePath = data["ImageFolder"] + os.sep + imagesDict[key][tileNum]
                    print( "Path to file: " + filePath )
                except:
                    if errorOnMissing:
                        print( "Missing tile: " + str(tileNum) + " in folder for key: " + key )
                        raise
                    else:
                        print( "Missing tile: " + str(tileNum) + " in folder for key: " + key )
                        print( "Continuing" )
                        tileNum += 1
                        continue
                
                # Try to read in the file
                try:
                    print( "Reading Image" )
                    tileImageInfo = Draft.ImageInfo()
                    tileImage = Draft.Image.ReadFromFile(filePath, tileImageInfo)
                    print( "Image successfully read" )
                except:
                    if errorOnMissing:
                        print( "Unable to read file: " + filePath )
                        raise
                    else:
                        print( "Unable to read file: " + filePath )
                        print( "Continuing" )
                        tileNum += 1
                        continue

                if channelNames is None:
                    channelNames = tileImage.GetChannelNames()

                # If a new image has not been created then the height and width will be negative 1
                if configWidth < 0 or configHeight < 0:
                    # If the tiles are cropped then we have no basis for the final image so we raise an exception
                    # Otherwise we use the dimensions of the first image
                    if data["TilesCropped"].lower() == "true":
                        print( "Tiles are cropped and no height or background image was specified." )
                        raise Exception( "Must specify height and width of final image if tiles are cropped." )
                    configWidth = tileImage.width
                    configHeight = tileImage.height

                    assembler.SetSize(configWidth, configHeight)
                    print( "Using height and width of image: " + filePath )
                    print( "Final Image Dimensions = " + str(configWidth) + "x" + str(configHeight) )

                # Get the position of the given tile
                try:
                    x = float(data[tileName + "X"])
                    y = float(data[tileName + "Y"])
                except:
                    print( "No position given for tile: " + tileName )
                    raise

                # If the distance was given in pixels then convert it to a 0.0-1.0 scale
                # This is done since draft uses a 0-1 ratio for Compositing
                if not distanceAsPixels:
                    x = float(x) * configWidth
                    y = float(y) * configHeight
                    x = int(x + 0.5)
                    y = int(y + 0.5)
                else:
                    x = int(x)
                    y = int(y)

                # Crop the tiles if they are not currently cropped
                if data["TilesCropped"].lower() != "true" and data["TilesCropped"] != "1":
                    try:
                        tileWidth = float(data[tileName + "Width"])
                        tileHeight = float(data[tileName + "Height"])
                    except:
                        print( "No dimensions given for cropping: " + tileName )
                        raise

                    left = float(data[tileName + "X"])
                    bottom = float(data[tileName + "Y"])
                    right = left + float(tileWidth)
                    top = bottom + float(tileHeight)

                    # Cropping is done using pixel amounts so convert all distances to pixels
                    if not distanceAsPixels:
                        left = left * tileImage.width
                        bottom = bottom * tileImage.height
                        right = right * tileImage.width
                        top = top * tileImage.height

                    # Round the dimensions to the nearest pixel
                    left = int(left + 0.5)
                    bottom = int(bottom + 0.5)
                    right = int(right + 0.5)
                    top = int(top + 0.5)

                    print( tileName + " cropping area: [Left: " + str(left) + ", Right: " + str(right) + ", Top: " + str(top) + ", Bottom: " + str(bottom) + "]" )
                    tileImage.Crop(left, bottom, right, top)
                    
                    tileWidth = tileImage.width
                    tileHeight = tileImage.height
                else:
                    tileWidth = tileImage.width
                    tileHeight = tileImage.height

                print( tileName + " position: " + str(x) + ", " + str(y) )
                print( tileName + " dimension: " + str(tileWidth) + ", " + str(tileHeight) )

                tileChannels = tileImage.GetChannelNames()
                newChannels = list(set(tileChannels) - set(channelNames))

                for channel in newChannels:
                    val = 0.0
                    if channel.lower() == "a":
                        val = 1.0
                    channelNames.append(channel)
                    print( "Adding Channel: " + channel )

                # Add the tile to the Assembler
                assembler.AddTile(tileImage, x, y)
                tileNum += 1
                fileNum += 1

            # Set image info from the last tile if not already set with background image's tile decription
            if imageInfo is None and tileImageInfo is not None:
                imageInfo = tileImageInfo

            if channelNames is not None:
                assembler.SetChannels(channelNames)
                print( "Total Number of Output Channels: " + str(len(channelNames)) )
                print( "Output Channels: " )
                for channelName in channelNames:
                    print( str(channelName) )

            # Make sure the output order is respected
            sys.stdout.flush()

            # Perform the assembly job
            assembler.AssembleToFile(inputDirectory + os.sep + outputPrefix + key + extension, imageInfo)
            imageNum += 1

    if len(sys.argv) > 3:
        cleanupTilesStr = sys.argv[3].lower()
        cleanupTiles = False
        # Check if we are to cleanup the tiles
        if cleanupTilesStr == "true" or cleanupTilesStr == "1":
            cleanupTiles = True

        if cleanupTiles:
            print( "Cleaning up Tiles..." )
            if not "ImageFolder" in data:
                tileNum = 0
                # Go through each tile and try to remove the file
                while tileNum < int(data["TileCount"]):
                    tileName = "Tile" + str(tileNum)
                    try:
                        print( "Deleting: " + data[tileName + "FileName"] )
                        os.remove(data[tileName + "FileName"])
                        print( "Deleted: " + data[tileName + "FileName"] )
                    # By this time we would have errored out if error on missing was enabled
                    except KeyError:
                        pass
                    except OSError:
                        print( "Failed to delete: " + data[tileName + "FileName"] )
                        pass
                    tileNum += 1
            else:
                # Go through each key in the dictionary and try to remove the associated files
                for key in imagesDict:
                    tileNum = 0
                    while tileNum < int(data["TileCount"]):
                        tileName = "Tile" + str(tileNum)
                        try:
                            filePath = data["ImageFolder"] + os.sep + imagesDict[key][tileNum]
                            try:
                                print( "Deleting: " + str(filePath) )
                                os.remove(filePath)
                                print( "Deleted: " + str(filePath) )
                            except OSError:
                                print( "Failed to delete: " + str(filePath) )
                                pass
                        except KeyError:
                            pass
                        tileNum += 1
        else:
            print( "Not cleaning up tiles" )
    else:
        print( "Not cleaning up tiles" )

except Exception as e:
    print( str(e) )
    print( "Draft Tile Assembler Failed! See job log for more details." )
    raise

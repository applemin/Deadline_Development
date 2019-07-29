----------------------------------------------------------------------------------------------------
-- Renders all the available render targets of the loaded project.
-- Asks the user for an output directory and saves all the images into that directory 
-- (e.g. <rendertargetname>_01.png, <rendertargetname>_02.png, ...)
--
-- @author      Mark Basset, Octane dev team and others
-- @description Batch rendering for Octane.
-- @version     0.41
-- @script-id   OctaneRender batch rendering

-- Global table with our settings. All global variables should be here to keep an overview.
-- Note: This file has been edited and reduced from it's original format. See issue #3214 -> DeadlineOctane.lua download to view the original (which
-- was also reduced from Octane's official version). The edits that were made were deleting unused gSettings and methods.
-- TODO: a property table here would make everything more compact.
local gSettings =
{
    -- the copied scene graph
    sceneGraph         = nil,
    -- list of render target nodes in the current project together with their enable state
    -- and export file format
    renderTargets      = {},
    -- name of render target node to render
    renderTargetName   = arg[6], 
    -- absolute path to the output directory of the rendered images // was = nil
    -- outputDirectory    = "C:/Users/%USERNAME%/Desktop/DeadlineLua/" .. octane.file.getFileNameWithoutExtension(octane.project.getCurrentProject()),
    outputDirectory    = arg[2],
    -- true to override the max samples/px
    overrideMaxSamples = false,
    -- max samples/px
    maxSamples         = 1000,
    -- filename template for the output files
    template           = arg[1],
    -- filetype to render
    outputFileType     = arg[3],
    -- handle for the batch render function
    batchRender        = nil,
    -- framerate
    fps                = nil,
    -- delta value between 2 animation frames (1 / fps)
    dT                 = nil,
    -- frame number where we start rendering
    startFrame         = arg[4],
    -- frame number where we finish rendering (inclusive)
    endFrame           = arg[5],
    -- true if we use custom file numbering
    useFileNumbering   = false,
    -- frame number from which we start number files
    fileNumber         = 0,
    -- skip existing files
    skipExisting       = false,
    -- save all enabled render passes
    saveAllPasses      = true,
    -- save the render passes as a layered exr
    saveMultiLayerExr  = true,
    -- save additional deep image output
    saveDeepImage      = false,
    -- how many sub frames to render
    subFrameCount      = nil
}


-- sorts a table alpha numerically
-- (snippet from http://notebook.kulchenko.com/algorithms/alphanumeric-natural-sorting-for-humans-in-lua)
local function alphanumsort(nodes)
    local function padnum(d)
        local dec, n = string.match(d, "(%.?)0*(.+)")
        return #dec > 0 and ("%.12f"):format(d) or ("%s%03d%s"):format(dec, #n, n)
    end
    local function compare(n0, n1) 
        local a, b = n0.name, n1.name
        return a:gsub("%.?%d+",padnum)..("%3d"):format(#b)
        < b:gsub("%.?%d+",padnum)..("%3d"):format(#a)
    end
    table.sort(nodes, compare)
end


local FRAME_MARGIN = 0.1


-- returns the index of the last frame
local function calculateLastFrame()
    local interval = gSettings.sceneGraph:getAnimationTimeSpan()
    return math.ceil (interval[2] * gSettings.fps - FRAME_MARGIN)
end


local function frameToTime(frame)
    return frame * gSettings.dT
end


-- prefixes a frame number with zeroes
local function prefixWithZeroes(frame)
    -- frame can end up being a double (ie. 0.0) so we want to ensure it's an integer to not mess up padding
    frame = math.floor(frame)

    -- calculate the number of digits
    local lastFrame = calculateLastFrame()
    if gSettings.useFileNumbering then
        lastFrame  = lastFrame + gSettings.fileNumber
    end
    -- minimum of 4 digits
    local digitCount = math.max(4, math.ceil(math.log10(lastFrame)))

    -- prefix with zeroes
    local frameStr = tostring(frame)
    while (#frameStr < digitCount) do
        frameStr = "0"..frameStr
    end

    return frameStr
end


local function createFilename(ix, frame, subFrameIx, name, imageType, pass)
    -- common extension for our image output types
    local fileExtensions = 
    {
        [octane.imageSaveType.PNG8]          = "png",
        [octane.imageSaveType.PNG16]         = "png",
        [octane.imageSaveType.EXR]           = "exr",
        [octane.imageSaveType.EXRTONEMAPPED] = "exr",
    }
    local s = gSettings.template
    -- %i -> index of the render target
    s = string.gsub(s, "%%i", string.format("%d", ix))
    -- %f -> frame number
    if gSettings.useFileNumbering then
        s = string.gsub(s, "%%f", string.format("%d", gSettings.fileNumber + frame))
    else
        s = string.gsub(s, "%%f", string.format("%d", frame))
    end
    -- %F -> frame number prefixed with zeroes (i.e. 1 -> 001)
    if gSettings.useFileNumbering then
        s = string.gsub(s, "%%F", prefixWithZeroes(gSettings.fileNumber + frame))
    else
        s = string.gsub(s, "%%F", prefixWithZeroes(frame))
    end  
    -- %s -> sub frame number
    s = string.gsub(s, "%%s", string.format("%d", subFrameIx))
    -- %n -> name of the node
    s = string.gsub(s, "%%n", name)
    -- %e -> extension
    s = string.gsub(s, "%%e", fileExtensions[imageType])
    -- %t -> timestamp (h_m_s)
    s = string.gsub(s, "%%t", os.date("%H_%M_%S"))
    -- %p -> render pass name
    s = string.gsub(s, "%%p", pass)
    return s
end


local function findFileType(name)
    -- common extension for our image output types
    local fileExtensions = 
    {
        ["png8"] = octane.imageSaveType.PNG8,
        ["png16"] = octane.imageSaveType.PNG16,
        ["exr"] = octane.imageSaveType.EXR,
        ["exrtonemapped"] = octane.imageSaveType.EXRTONEMAPPED,
    }

    return fileExtensions[name]
end


local function createRenderPassExportObjs(renderTargetNode)
    -- get the render passes node
    local rpNode = renderTargetNode:getInputNode(octane.P_RENDER_PASSES)
    if not rpNode then
        return nil 
    end

    -- create the export objects
    local objs = {}
    for _, id in ipairs(octane.render.getAllRenderPassIds()) do
        local info = octane.render.getRenderPassInfo(id)
        if info.pinId ~= octane.P_UNKNOWN then
            if rpNode:getPinValue(info.pinId) then
                local exportObj =
                {
                    ["exportName"]   = nil,
                    ["origName"]     = info.name,
                    ["renderPassId"] = info.renderPassId,
                }
                table.insert(objs, exportObj)
            end
        else
            local exportObj =
            {
                ["exportName"]   = nil,
                ["origName"]     = info.name,
                ["renderPassId"] = info.renderPassId,
            }
            table.insert(objs, exportObj)
        end
    end
    return objs
end



local function saveDeepImage(ix, frame, nodeName)
    if gSettings.saveDeepImage and octane.render.canSaveDeepImage() then
        local deepFilename = createFilename(ix, frame, nodeName, octane.imageSaveType.EXR, "Beauty")
        local deepPath = octane.file.join(gSettings.outputDirectory, "deep_"..deepFilename)
        octane.render.saveDeepImage(deepPath)
    end
end

----------------------------------------------------------------------------------------------------
-- Batch rendering


-- The batch rendering function. This will render each frame for each selected render target.
gSettings.batchRender = function()
 -- create the output directory if it does not exist yet
    if gSettings.outputDirectory and octane.file.isAbsolute(gSettings.outputDirectory) 
        and not octane.file.exists(gSettings.outputDirectory) then
        octane.file.createDirectory(gSettings.outputDirectory)
    end

    -- render each animation frame
    for frame = gSettings.startFrame,gSettings.endFrame do
        -- update the time in the scene
        gSettings.sceneGraph:updateTime(frameToTime(frame))
        -- render all the render targets that are enabled
        for ix, renderTarget in ipairs(gSettings.renderTargets) do
            if renderTarget.render then
                -- override max samples if configured
                if gSettings.overrideMaxSamples then
                    renderTarget.node:getInputNode(octane.P_KERNEL):setPinValue(octane.P_MAX_SAMPLES, gSettings.maxSamples)
                end

                -- create the render pass export objects (returns nil when there aren't any passes)
                local renderPassExportObjs = createRenderPassExportObjs(renderTarget.node)

                -- for every sub frame
                for subFrameIx = 0, gSettings.subFrameCount - 1 do
                    if gSettings.subFrameCount > 1 then
                        -- setup the sub frame times for the animation settings node
                        local animationSettingsNode = renderTarget.node:getInputNode(octane.P_ANIMATION)

                        -- these are in percentages.
                        local subFrameStart = subFrameIx / gSettings.subFrameCount
                        local subFrameEnd   = (subFrameIx + 1.0) / gSettings.subFrameCount

                        -- set the values in the animation settings node
                        animationSettingsNode:setPinValue(octane.P_SUBFRAME_START, subFrameStart)
                        animationSettingsNode:setPinValue(octane.P_SUBFRAME_END,   subFrameEnd)
                    end

                    -- 1) save out all the render passes
                    if renderPassExportObjs and gSettings.saveAllPasses then
                        -- a) multi-layer EXR
                        if renderTarget.fileType == octane.imageSaveType.EXR and gSettings.saveMultiLayerExr then
                            for _, exportObj in ipairs(renderPassExportObjs) do
                                -- don't prefix the name of the beauty pass, the beauty pass should be
                                -- in the RGBA channels
                                if exportObj.renderPassId == octane.renderPassId.BEAUTY then
                                    exportObj.exportName = ""
                                else
                                    exportObj.exportName = exportObj.origName
                                end
                            end

                            -- create an output path for the image
                            local filename = createFilename(ix, frame, subFrameIx, renderTarget.node.name, renderTarget.fileType, "all")
                            local path

                            if gSettings.outputDirectory then
                                path = octane.file.join(gSettings.outputDirectory, filename)
                            else
                                path = string.format("%s [dry-run]", filename)
                            end

                            local skipFrame = gSettings.skipExisting and gSettings.outputDirectory and octane.file.exists(path)

                            -- do the rendering of the image
                            if not skipFrame then
                                octane.render.start
                                { 
                                    renderTargetNode = renderTarget.node,
                                    callback         = function()
                                    end
                                }
                            end

                             -- save out the multi layer EXR
                             if gSettings.outputDirectory and path and not skipFrame then
                                octane.render.saveRenderPassesMultiExr(path, renderPassExportObjs, 4, true)
                                -- optionally save out the deep image
                                saveDeepImage(ix, frame, renderTarget.node.name)
                            end
                        -- b) each render pass as a discrete file
                        else
                            -- create file names for each file
                            for _, exportObj in ipairs(renderPassExportObjs) do
                                exportObj.exportName = createFilename(ix, frame, subFrameIx, renderTarget.node.name, renderTarget.fileType, exportObj.origName)
                            end

                            local path

                            if gSettings.outputDirectory then
                                path = gSettings.outputDirectory
                            else
                                path = "[dry-run]"
                            end

                            -- check if at least 1 file doesn't exits
                            local skipFrame = gSettings.skipExisting

                            if skipFrame then
                                for _, exportObj in ipairs(renderPassExportObjs) do
                                    local fullPath = octane.file.join(path, exportObj.exportName)
                                    if not octane.file.exists(fullPath) then
                                        skipFrame = false
                                        break
                                    end
                                end
                            end

                            -- do the rendering of the image
                            if not skipFrame then
                                octane.render.start
                                { 
                                    renderTargetNode = renderTarget.node,
                                    callback         = function()
                                    end
                                }
                            end

                            -- save out the passes as discrete files
                            if gSettings.outputDirectory and path and not skipFrame then
                                octane.render.saveRenderPasses(path, renderPassExportObjs, renderTarget.fileType)

                                -- optionally save out the deep image
                                saveDeepImage(ix, frame, renderTarget.node.name)
                            end
                        end
                    -- 2) only save out the beauty pass
                    else
                        -- create an output path for the image
                        local filename = createFilename(ix, frame, subFrameIx, renderTarget.node.name, renderTarget.fileType, "main")
                        local path

                        if gSettings.outputDirectory then
                            path = octane.file.join(gSettings.outputDirectory, filename)
                        else
                            path = string.format("%s [dry-run]", filename)
                        end

                        local skipFrame = gSettings.skipExisting and gSettings.outputDirectory and octane.file.exists(path)

                        -- do the rendering of the image
                        if not skipFrame then
                            octane.render.start
                            { 
                                renderTargetNode = renderTarget.node,
                                callback         = function()
                                end
                            }
                        end

                        -- save out the image
                        if gSettings.outputDirectory and path and not skipFrame then
                            octane.render.saveImage(path, renderTarget.fileType)

                            -- optionally save out the deep image
                            saveDeepImage(ix, frame, renderTarget.node.name)
                        end
                    end
                end
            end
        end
    end
end



---------------------------------------------------------------------------------------------------
-- Main script

-- Octane 2 compatibility hack
if not octane.imageSaveType then
    octane.imageSaveType = octane.render.imageType
end

-- create a copy of the original project
gSettings.sceneGraph = octane.nodegraph.createRootGraph("Project Copy")
gSettings.sceneGraph:copyFromGraph(octane.project.getSceneGraph())


-- initialize global variables.
gSettings.fps           = gSettings.fps or octane.project.getProjectSettings():getAttribute(octane.A_FRAMES_PER_SECOND)
gSettings.dT            = 1 / gSettings.fps
gSettings.subFrameCount = gSettings.subFrameCount or 1
gSettings.fileNumber    = gSettings.fileNumber or 0

-- fetch all the render target nodes
local renderTargetNodes = gSettings.sceneGraph:findNodes(octane.NT_RENDERTARGET, true)

-- if no render targets are found -> error out
if #renderTargetNodes == 0 then
    error("No render targets in this project.")
end

-- sort all the render target nodes alphanumerically
alphanumsort(renderTargetNodes)

local checkRenderTarget = true

if gSettings.renderTargetName == nil or gSettings.renderTargetName == '' then
    checkRenderTarget = false
end

-- initialize the state for the render targets
for _, node in ipairs(renderTargetNodes) do
    if not checkRenderTarget or node.name == gSettings.renderTargetName then
        local state =
        {
            ["node"]     = node,
            ["render"]   = true,
            ["fileType"] = findFileType(gSettings.outputFileType),
        }
        table.insert(gSettings.renderTargets, state)
    end
end

-- run batch render
gSettings.batchRender()
# hfTextureOptimizer v0.1 by renry
# rev 4/1/2013

# tools for optimizing scenes with way too much RAM devoted to texture loading.
# can analyze total file texture usage in a scene, convert big textures to vray-compatible mipmap EXRs.

import os,operator,subprocess
import maya.cmds as cmds

def analyzeScene():
    # tallys up all file texture nodes in the scene and returns a list of dictionaries, as well as a total filesize for all textures.
    fileNodes = cmds.ls(type='file')
    filesList = []
    totalSize = 0
    projectPath = cmds.workspace(q=1,fn=1)
    for i in fileNodes:
        filePath = cmds.getAttr(i+'.fileTextureName')
        filesDict = {}
        if projectPath not in filePath:
            filePath = projectPath + '/' + filePath
        if not os.path.exists(filePath):
            pass
        else:
            filesDict['filename'] = filePath
            filesize = os.path.getsize(filePath) / (1024.0*1024.0)
            filesDict['size'] = filesize
            filesList.append(filesDict)
            totalSize = totalSize + filesize
    filesList = sorted(filesList, key=operator.itemgetter('size'),reverse=True)
    print 'Total file texture size: %f' % (totalSize)
    return filesList,totalSize

def editCell(*args):
    # dummy function for table because maya sucks
    return True
    
    
def showAnalysis(filesList,totalSize):
    # show a shitty dialog listing why your textures are all terrible
    windowName = 'hfTextureUI'
    if cmds.window(windowName,exists=1):
        cmds.deleteUI(windowName)
    window = cmds.window(windowName,widthHeight=(1000,600))
    form = cmds.formLayout()
    table = cmds.scriptTable(rows=len(filesList)+2, columns=2, height=550, label=[(1,"Texture Path"), (2,"Size (MB)")], ed=0, cw=[(1,750),(2,200)],ccc=editCell)
    cmds.formLayout(form, edit=True, attachForm=[(table, 'top', 0), (table, 'left', 0), (table, 'right', 0)])
    for index,item in enumerate(filesList):
        cmds.scriptTable(table,e=1,cellIndex=(index+1,1),cellValue=item['filename'])
        cmds.scriptTable(table,e=1,cellIndex=(index+1,2),cellValue=item['size'])
    cmds.scriptTable(table,e=1,cellIndex=(len(filesList)+2,2),cellValue=totalSize)
    cmds.scriptTable(table,e=1,cellIndex=(len(filesList)+2,1),cellValue='TOTAL SIZE (MB)')
    cmds.showWindow(window)
    
def convertToEXR(thresh=10.0):
    # for all file textures in the scene, if the texture is > 10MB and is not connected to a vrayDisplacement object,
    # convert it into a tiled EXR using img2tiledexr.exe
    projectPath = cmds.workspace(q=1,fn=1)
    fileNodes = [f for f in cmds.ls(type='file') if not cmds.listConnections(f,type='luminance')]
    for i in fileNodes:
        filePath = cmds.getAttr(i+'.fileTextureName')
        filesDict = {}
        if projectPath not in filePath:
            filePath = projectPath + '/' + filePath
        if not os.path.exists(filePath):
            pass
        else:
            size = os.path.getsize(filePath) / (1024.0*1024.0)
            if size > thresh and '_TILED.exr' not in filePath:
                
                # convert this shit
                convertFile = os.path.splitext(filePath)[0]+'_TILED.exr'
                if not os.path.exists(convertFile):
                    print 'Converting %s to %s' % (filePath, convertFile)
                    execStr = '"C:/Program Files/Chaos Group/V-Ray/Maya 2013 for x64/bin/img2tiledexr.exe" "%s" "%s"' % (filePath, convertFile)
                    subp = subprocess.Popen(execStr,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout,stderr = subp.communicate()
                    if stderr:
                        print 'ERROR converting: %s' % stderr
                # relink file texture
                fixedPath = convertFile.split(projectPath+'/')[-1]
                cmds.setAttr(i+'.fileTextureName',fixedPath,type='string')
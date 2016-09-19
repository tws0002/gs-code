import maya.standalone as std
import maya.cmds as cmds
import maya.mel as mel
import os
import sys
import pickle
import shutil
import time

# warning: a render could cancel without throwing a bad exit code if the scene can't render for some other reason (such as missing references)
# probably need to make some kind of detection for this.


inputFile = open(os.path.join(os.environ['USERPROFILE'],'mustacheDB_out'),'r')
infile = pickle.load(inputFile)

def renderPreview(infile,*args):
    std.initialize(name='python')
    sys.stdout.write('Initializing Maya Python interpreter.')
    # load mental ray
    if not cmds.pluginInfo('Mayatomr.mll',q=1,l=1):
        loaded = cmds.loadPlugin('Mayatomr.mll',qt=1)
    name,screenshot,textures,scenePath,ren = doFileAnalysis(infile)
    data = (name.strip(),screenshot.strip(),','.join(textures),scenePath.replace('\\','/'))
    # return output to STDOUT as a pickled string.
    outputFile = open(os.path.join(os.environ['USERPROFILE'],'mustacheDB_in'),'w')
    outPickle = pickle.dump(data,outputFile,pickle.HIGHEST_PROTOCOL)
    outputFile.close()
    sys.stdout.write('FUCK YOU')
    return outputFile
    # return output
    
def doFileAnalysis(infile,*args):
    print '\ninfile: %s' % (infile)
    print 'project: %s' % (cmds.workspace(q=1,fn=1))
    cmds.file(infile,o=1,f=1)
    # first: if this is not a mayaBinary file, save it as one.
    scenePath = infile
    if os.path.splitext(infile)[-1] != '.mb':
        # remove all unknown nodes and save as MB
        unk = cmds.ls(type='unknown')
        if unk:
            for i in unk:
                try:
                    cmds.lockNode(i,lock=0)
                    cmds.delete(i)
                except:
                    pass
        scenePath = os.path.splitext(infile)[0]+'.mb'
        cmds.file(rename=scenePath)
        cmds.file(s=1,f=1,type='mayaBinary')
    meshes = []
    surfaces = []
    meshes = cmds.ls(type='mesh',l=1)
    surfaces = cmds.ls(type='nurbsSurface',l=1)
    # create temp camera
    cam = cmds.camera()
    cmds.setAttr(cam[0]+'.rx',-35)
    cmds.setAttr(cam[0]+'.ry',45)
    meshXforms = []
    if meshes:
        for mesh in meshes:
            xf = cmds.listRelatives(mesh,p=1,f=1)[0]
            meshXforms.append(xf)
    if surfaces:
        for surface in surfaces:
            xf = cmds.listRelatives(surface,p=1,f=1)[0]
            meshXforms.append(xf)
    meshXforms = [f for f in meshXforms if cmds.getAttr(f+'.visibility') == 1]
    if not meshXforms:
        # nothing here, throw an error
        cmds.quit(ec=86,f=1)
    cmds.select(meshXforms)
    # set active resolution before fitting.
    cmds.setAttr('defaultResolution.aspectLock',0)
    cmds.setAttr('defaultResolution.width',720)
    cmds.setAttr('defaultResolution.height',405)
    cmds.setAttr('defaultResolution.pixelAspect',1)
    cmds.setAttr('defaultResolution.deviceAspectRatio',1.778)
    cmds.viewFit(cam[1],f=0.9)
    cmds.viewClipPlane(cam[1],acp=1)
    cmds.select(cl=1)
    allCams = cmds.ls(type='camera')
    for c in allCams:
        cmds.setAttr(c+'.renderable',0)
    cmds.setAttr(cam[1]+'.renderable',1)
    engine = cmds.sets(renderable=1,noSurfaceShader=1,em=1)
    mat = cmds.shadingNode('surfaceShader',asShader=1)
    cmds.connectAttr(mat+'.outColor',engine+'.surfaceShader')
    aotex = cmds.shadingNode('mib_amb_occlusion',asTexture=1)
    cmds.connectAttr(aotex+'.outValue',mat+'.outColor')
    cmds.setAttr(aotex+'.samples',32)
    # create a new temporary render layer and add all objects
    rlayer = cmds.createRenderLayer(n='tempLayer',g=1,mc=1)
    # assign AO shader to all meshes and surfaces
    if meshes:
        cmds.sets(meshes,e=1,fe=engine)
    if surfaces:
        cmds.sets(surfaces,e=1,fe=engine)
    # get all existing file textures and add the paths to a list
    textures = []
    fileNodes = cmds.ls(type='file')
    for node in fileNodes:
        tex = cmds.getAttr(node+'.fileTextureName')
        textures.append(tex.strip().replace('\n',''))
    # set mental ray as the current renderer and set up output settings
    cmds.setAttr('defaultRenderGlobals.currentRenderer','mentalRay',type='string')
    # to prevent overwriting other images with the same name, use the unix timestamp as the image name.
    rand_imageFilePrefix = str(int(time.time()))
    mel.eval('miCreateDefaultNodes();')
    cmds.setAttr('defaultRenderGlobals.imageFormat',8)
    cmds.setAttr('defaultRenderGlobals.outFormatControl',0)
    cmds.setAttr('defaultRenderGlobals.useFrameExt',0)
    cmds.setAttr('defaultRenderGlobals.animation',0)
    cmds.setAttr('defaultRenderGlobals.useMayaFileName',1)
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix',rand_imageFilePrefix,type='string')
    mel.eval('miCreateDefaultNodes();')
    cmds.setAttr('miDefaultOptions.rayTracing',1)
    cmds.setAttr('miDefaultOptions.maxSamples',2)
    cmds.setAttr('miDefaultOptions.minSamples',0)
    cmds.setAttr('miDefaultOptions.maxReflectionRays',1)
    cmds.setAttr('miDefaultOptions.finalGather',0)
    cmds.setAttr('miDefaultOptions.filter',2)
    # get output filename
    tempProject = cmds.workspace(q=1,fn=1)
    outFile = os.path.join(tempProject,'images',rlayer,rand_imageFilePrefix+'.jpg')
    # disable all render layers except rlayer
    layers = cmds.ls(type='renderLayer')
    for layer in layers:
        cmds.setAttr(layer+'.renderable',0)
    cmds.setAttr(rlayer+'.renderable',1)
    ren = cmds.Mayatomr(r=1,camera=cam[1],x=720,y=405,l=rlayer,rv=5)
    st = 'screenshot written to %s' % (outFile)
    print(st)
    return infile,outFile,textures,scenePath,ren
    
# run the script.
renderPreview(infile)
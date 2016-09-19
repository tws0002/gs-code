# maya scene to FBX conversion script v0.2
# henry foster (henry@toadstorm.com) 4/26/2012
#
# two main functions: one to bake non-skinned objects into world space and export one big FBX. another to create geocaches of skinned objects
#                     in world space, which requires creating a blend shape from the original mesh and blending it to the deformed mesh.
#

# TO DO LIST:
#
# objects won't be recognized as skins if any other node is feeding into the history after a deformer before the mesh; for example, an attributeTransfer node.

import maya.cmds as cmds
import maya.mel as mel
import os

def makeObjectGroups(selection,*args):
    # for each selected transform, get the shape node if one exists. look for the inMesh connection. if it is of a specified type (deformers, etc) then add
    # the transform to the skins list. otherwise add to nonskins.
    deformerList = ['polyTriangulate','skinCluster','nonLinear','wrap','ffd','cluster','wire','blendShape','jiggle','sculpt','polyTweakUV','historySwitch','nurbsTessellate']
    skins = []
    nonskins = []
    for i in selection:
        print 'DEBUG: %s' % (i)
        # get the shape node(s), then get the node connected to shape.inmesh
        shapes = cmds.listRelatives(i,s=1)
        isDeformed = False
        if shapes:
            for j in shapes:
                if cmds.objectType(j) == 'mesh':
                    inConn = cmds.listConnections(j+'.inMesh')
                    if inConn:
                        if cmds.objectType(inConn[0]) in deformerList:
                            isDeformed = True
                            break
                elif cmds.objectType(j) == 'nurbsSurface':
                    inConn = cmds.listConnections(j+'.create')
                    if inConn:
                        if cmds.objectType(inConn[0]) in deformerList:
                            isDeformed = True
                            break
            if isDeformed:
                skins.append(i)
            else:
                nonskins.append(i)
    # remove duplicates from both lists
    skins = list(set(skins))
    nonskins = list(set(nonskins))
    return skins, nonskins

def importReferences(*args):
    # import all objects from references. this is to allow reparenting before export.
    refs = [f for f in cmds.file(q=1,r=1) if cmds.referenceQuery(f,il=1) == True]
    for r in refs:
        cmds.file(r,ir=1)

def bakeNonskins(objects,*args):
    # bake objects to world space.
    # create a locator constrained to each object, bake the constraints, then unparent objects, constrain to locators, and bake.
    print 'RUNNING bakeNonskins'
    locators = []
    constraints = []
    for x in range(0,len(objects)):
        loc = cmds.spaceLocator()[0]
        locators.append(loc)
        pc = cmds.parentConstraint(objects[x],loc)
        sc = cmds.scaleConstraint(objects[x],loc)
        constraints.append(pc)
        constraints.append(sc)
    # bake locators.
    mel.eval('setNamedPanelLayout "Single Perspective View"')
    perspPane = cmds.getPanel(vis=1)
    cmds.scriptedPanel('graphEditor1',e=1,rp=perspPane[0])
    start = cmds.playbackOptions(q=1,min=1)
    end = cmds.playbackOptions(q=1,max=1)
    cmds.select(locators)
    cmds.bakeResults(simulation=1,cp=0,s=0,sb=1.0,t=(start,end))
    # now, parent objects to world space, then constrain them to the locators in order.
    # need to delete all channel information first.
    # in order to run CBdeleteConnection, we need to source a particular MEL.
    mel.eval('source channelBoxCommand.mel;')
    for c in constraints:
        cmds.delete(c)
    chans = ['tx','ty','tz','rx','ry','rz','sx','sy','sz','v']
    objectsWorldSpace = []
    for x in range(0,len(objects)):
        for ch in chans:
            melstr = 'CBdeleteConnection "'+objects[x]+'.'+ch+'";'
            mel.eval(melstr)
            # unlock channel, in case it's locked
            cmds.setAttr(objects[x]+'.'+ch,lock=0)
        # try to parent to world space. if this fails, it's already in world space.
        try:
            renamed = cmds.parent(objects[x],w=1)[0]
            objectsWorldSpace.append(renamed)
        except RuntimeError:
            objectsWorldSpace.append(objects[x])
        # now apply constraints from the locator with the same index x.
        cmds.parentConstraint(locators[x],objectsWorldSpace[x])
        cmds.scaleConstraint(locators[x],objectsWorldSpace[x])
    # now bake out the constraints on objectsWorldSpace.
    cmds.select(objectsWorldSpace)
    cmds.bakeResults(simulation=1,cp=0,s=0,sb=1.0,t=(start,end))
    for l in locators:
        cmds.delete(l)
    # now export objectsWorldSpace as FBX.
    mel.eval('FBXResetExport;')
    mel.eval('FBXExportCacheFile -v false;')
    mel.eval('FBXExportCameras -v true;')
    cacheDir = os.path.join(cmds.workspace(q=1,fn=1),'data','FBX',os.path.splitext(cmds.file(q=1,sn=1,shn=1))[0],'keyframes').replace('\\','/')
    if not os.path.exists(cacheDir): os.makedirs(cacheDir)
    fbxFile = os.path.join(cacheDir,os.path.splitext(cmds.file(q=1,sn=1,shn=1))[0]+'_NONSKINS.fbx').replace('\\','/')
    cmds.select(objectsWorldSpace)
    evalStr = 'FBXExport -f "'+fbxFile+'" -s'
    mel.eval(evalStr)
    print 'Exported non-skins to %s' % (fbxFile)

def bakeSkins(objects,*args):
    # for each object (transform), create a duplicate, unlock channels, move to world space, freeze xforms, then wrap deform it to the original.
    # disable all display smoothing to speed things up and prevent max from interpreting the points incorrectly.
    print '\nRUNNING bakeSkins'
    polys = cmds.ls(type='mesh')
    cmds.displaySmoothness(polys,du=0,dv=0,pw=4,ps=1,po=1)
    start = cmds.playbackOptions(q=1,min=1)
    end = cmds.playbackOptions(q=1,max=1)
    # create a quick select set to house the deforming geometry. all duplicates will be added to this set for the fbx plugin.
    cmds.select(cl=1)
    exportSet = cmds.sets(text='gCharacterSet',n='FBXExportSet')
    cacheDir = os.path.join(cmds.workspace(q=1,fn=1),'data','FBX',os.path.splitext(cmds.file(q=1,sn=1,shn=1))[0],'pointCache').replace('\\','/')
    if not os.path.exists(cacheDir): os.makedirs(cacheDir)
    # block the viewport
    mel.eval('setNamedPanelLayout "Single Perspective View"')
    perspPane = cmds.getPanel(vis=1)
    cmds.scriptedPanel('graphEditor1',e=1,rp=perspPane[0])
    # wraps = []
    # cycle through objects
    for obj in objects:
        dupe = cmds.duplicate(obj,rc=1,rr=1)[0]
        chans = ['tx','ty','tz','rx','ry','rz','sx','sy','sz','v']
        for i in chans:
            cmds.setAttr(dupe+'.'+i,lock=False)
        try:
            dupe = cmds.parent(dupe,w=1)[0]
        except RuntimeError:
            pass
        cmds.delete(dupe,ch=1)
        blend = cmds.blendShape(obj,dupe,foc=1,origin='world')
        cmds.blendShape(blend,e=1,w=[0,1.0])
        cmds.sets(dupe,add=exportSet)
        dupeShape = cmds.listRelatives(dupe,s=1,ni=1)[0]
    # next run the MEL export commands for FBX.
    # the FBX plugin will automatically create the geocache, so there's no reason for me to write them out manually.
    mel.eval('FBXResetExport;')
    mel.eval('FBXExportCacheFile -v true;')
    evalStr = 'FBXExportQuickSelectSetAsCache -v '+exportSet+';'
    mel.eval(evalStr)
    mel.eval('FBXExportInputConnections -v false;')
    # select the objects to export from the selection set.
    cmds.select(exportSet)
    cmds.select(exportSet,add=1,ne=1)
    fbxFile = os.path.join(cacheDir,os.path.splitext(cmds.file(q=1,sn=1,shn=1))[0]+'_SKINS.fbx').replace('\\','/')
    evalStr = 'FBXExport -f "'+fbxFile+'" -s'
    mel.eval(evalStr)
    print ('Exported skins and point caches to %s') % (fbxFile)

def doExport(objects=False,exportSkins=True,exportNonskins=True,*args):
    # actually perform the bakes and exports.
    if objects:
        objects = cmds.ls(sl=1)
    importReferences()
    print '\nRUNNING doExport'
    if objects==False:
        all = []
        polys = cmds.ls(type='mesh')
        nurbs = cmds.ls(type='nurbsSurface')
        cams = [f for f in cmds.ls(type='camera') if cmds.getAttr(f+'.renderable') == 1]
        all.extend(polys)
        all.extend(nurbs)
        all.extend(cams)
        objects = []
        for i in all:
            xform = cmds.listRelatives(i,p=1)[0]
            objects.append(xform)
        objects = list(set(objects))
    skins, nonskins = makeObjectGroups(objects)
    if exportSkins and skins:
        bakeSkins(skins)
    if exportNonskins and nonskins:
        bakeNonskins(nonskins)

# now for some UI code...

def maya2FBX(*args):
    cmds.loadPlugin('fbxmaya',qt=1)
    windowName = 'maya2FBXUI'
    if cmds.window(windowName,q=1,exists=1): cmds.deleteUI(windowName)
    window = cmds.window(windowName,title='Smart FBX Exporter')
    form = cmds.formLayout()
    tx1 = cmds.text(ww=1,w=380,h=30,al='left',l='EXPORTING TO FBX WILL BREAK YOUR SCENE. You should save first.',fn='boldLabelFont',parent=form)
    tx2 = cmds.text(ww=1,w=380,h=30,al='left',l='Export skins: Bake and export anything that deforms, including non-linear deformers.',parent=form)
    tx3 = cmds.text(ww=1,w=380,h=30,al='left',l='Export non-skins: Bake and export keyframe animation for objects that do not deform, including cameras.',parent=form)
    exportSelected = cmds.checkBox(l='Selected objects only',v=1,parent=form)
    skinsBtn = cmds.button(l='Export skins',w=100,h=50,parent=form,c=lambda *x: doExport(cmds.checkBox(exportSelected,q=1,v=1),True,False))
    nonskinsBtn = cmds.button(l='Export non-skins',w=100,h=50,parent=form,c=lambda *x: doExport(cmds.checkBox(exportSelected,q=1,v=1),False,True))
    bothBtn = cmds.button(l='Export both',w=100,h=50,bgc=[0.6,0.7,1.0],parent=form,c=lambda *x: doExport(cmds.checkBox(exportSelected,q=1,v=1)))
    tm1 = 10
    tm2 = 50
    tm3 = 90
    tm4 = 140
    tm5 = 180
    lm1 = 10
    lm2 = 120
    lm3 = 230
    cmds.formLayout(form,e=1,attachForm=[(tx1,'top',tm1),(tx1,'left',lm1),(tx2,'top',tm2),(tx2,'left',lm1),(tx3,'top',tm3),(tx3,'left',lm1),
                                     (exportSelected,'top',tm4),(exportSelected,'left',lm1),(skinsBtn,'top',tm5),(skinsBtn,'left',lm1),
                                     (nonskinsBtn,'top',tm5),(nonskinsBtn,'left',lm2),(bothBtn,'top',tm5),(bothBtn,'left',lm3)])
    cmds.showWindow(window)
    cmds.window(window,e=1,w=400,h=250)
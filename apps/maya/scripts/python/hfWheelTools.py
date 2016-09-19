import maya.cmds as cmds
import operator

def convertMotionToCurve(target,start=False,end=False,accuracy=100,increment=1):
    if not start:
        start = cmds.playbackOptions(q=1,min=1)
    if not end:
        end = cmds.playbackOptions(q=1,max=1)
    cmds.select(target)
    motionTrail = cmds.snapshot(motionTrail=1,startTime=start,endTime=end,increment=increment,update='animCurve')
    # motionTrail[0] = shape, [1] = xform
    pts = cmds.getAttr(motionTrail[0]+'.pts')
    ptsFix = [f[:-1] for f in pts]
    # make duplicate curve
    newCurve = cmds.curve(d=1,ws=1,p=ptsFix)
    cmds.rebuildCurve(newCurve,rt=0,s=accuracy,kr=0)
    cmds.delete(motionTrail)
    return newCurve
    
    
def matchPathToKeyframes(targets,origCurves,start=False,end=False,increment=1):
    # match a path animation as closely as possible to original keyframed animation.
    # duplicate curve and loft into a surface.
    # create locator at target's pivot. attach to original curve. 
    # create pointOnSurfaceInfo, use lofted surface.create as input, use locatorShape.worldPosition as reference pos.
    # per each increment, find the result.u of the pointOnSurfaceInfo, then set the motion path uValue to this value.
    # return motion path.
    if not start:
        start = cmds.playbackOptions(q=1,min=1)
    if not end:
        end = cmds.playbackOptions(q=1,max=1)
    pointOnSurfaces = []
    motionPaths = []
    surfaces = []
    dupeCurves = []
    newLocs = []
    outLocs = []
    for k,i in enumerate(targets):
        origShape = cmds.listRelatives(origCurves[k],s=1)[0]
        dupeCurve = cmds.duplicate(origCurves[k])[0]
        dupeShape = cmds.listRelatives(dupeCurve,s=1)[0]
        origTy = cmds.getAttr(dupeCurve+'.ty')
        origDeg = cmds.getAttr(dupeShape+'.degree')
        cmds.setAttr(dupeCurve+'.ty',origTy+0.001)
        loft = cmds.loft(origShape,dupeShape,po=0,d=origDeg)
        surface = cmds.listConnections(loft,type='nurbsSurface')[0]
        
        newLoc = cmds.spaceLocator()[0]
        newLocShape = cmds.listRelatives(newLoc,s=1)[0]
        cmds.pointConstraint(i,newLoc)
        
        pointOnSurface = cmds.createNode('closestPointOnSurface')
        cmds.connectAttr(newLocShape+'.worldPosition',pointOnSurface+'.inPosition')
        cmds.connectAttr(surface+'.create',pointOnSurface+'.inputSurface') 
        outLoc = cmds.spaceLocator()[0]
        motionPath = cmds.pathAnimation(outLoc,c=origCurves[k],stu=start,etu=end)
        cmds.cutKey(motionPath,cl=1,time=(0,9999999),at='uValue')
        pointOnSurfaces.append(pointOnSurface)
        motionPaths.append(motionPath)
        surfaces.append(surface)
        dupeCurves.append(dupeCurve)
        newLocs.append(newLoc)
        outLocs.append(outLoc)
        
    # for each frame, check pointOnSurface.result.u and key motionPath.uValue to match
    for f in range(start,end,increment):
        cmds.currentTime(f)
        for k,i in enumerate(targets):
            u = cmds.getAttr(pointOnSurfaces[k]+'.result.v')
            if u == 1.0:
                u = 0.999999
            cmds.setKeyframe(motionPaths[k],at='uValue',v=u)    
    # cleanup
    cmds.delete(surfaces)
    cmds.delete(dupeCurves)
    cmds.delete(pointOnSurfaces)
    cmds.delete(newLocs)
    return outLocs
    
def bakeRotations(locators,targets,axis,diameter,start=False,end=False,increment=1):
    # given an object on a motion path and a rotation axis, figure out how many degrees it needs to be rotated per frame
    # and bake rotation to keyframes.
    pi = 3.14159
    if not start:
        start = cmds.playbackOptions(q=1,min=1)
    if not end:
        end = cmds.playbackOptions(q=1,max=1)
    motionPaths = []
    curves = []
    curveInfos = []
    arcLengths = []
    for i in locators:        
        motionPath = cmds.listConnections(i,type='motionPath')[0]
        curve = cmds.listConnections(motionPath,type='nurbsCurve')[0]
        curveInfo = cmds.createNode('curveInfo')
        cmds.connectAttr(curve+'.worldSpace[0]',curveInfo+'.inputCurve')
        arcLength = cmds.getAttr(curveInfo+'.arcLength')
        
        motionPaths.append(motionPath)
        curves.append(curve)
        curveInfos.append(curveInfo)
        arcLengths.append(arcLength)
        
    for f in range(start,end,increment):
        cmds.currentTime(f)
        for k,i in enumerate(targets):
            uVal = cmds.getAttr(motionPaths[k]+'.uValue')
            rotations = (arcLengths[k] * uVal) / (diameter * pi)
            deg = rotations * 360.0
            # set rotation value of target along axis "axis" to deg
            axisName = 'r'+axis
            cmds.setKeyframe(i,at=axisName, v=deg)
    # cleanup
    cmds.delete(curves)
    cmds.delete(locators)
    
def doAutoRotations(targets,axis,diameter,accuracy,start,end,increment=1):
    # do everything
    origCurves = []
    for i in targets:
        newCurve = convertMotionToCurve(i,start,end,accuracy,increment)
        origCurves.append(newCurve)
    outLocs = matchPathToKeyframes(targets,origCurves,start,end,increment)
    bakeRotations(outLocs,targets,axis,diameter,start,end,increment)
    
def hfWheelToolsRotationUI(increment=1):
    # i hate UI
    lm = [10,120]
    tm = [10,40,70,100,130,190]
    windowTitle = 'Wheel Auto-rotation UI'
    windowName = 'hfWheelRotateUI'
    if cmds.window(windowName,q=1,exists=1): cmds.deleteUI(windowName)
    rotateWindow = cmds.window(windowName,title=windowTitle)
    flayout = cmds.formLayout()
    axisLabel = cmds.text(l='Rotation axis:')
    axisCtrl = cmds.optionMenu()
    cmds.menuItem(l='x')
    cmds.menuItem(l='y')
    cmds.menuItem(l='z')
    diamLabel = cmds.text(l='Diameter:')
    diamCtrl = cmds.floatField(w=60)
    accLabel = cmds.text(l='Accuracy:')
    startLabel = cmds.text(l='Start:')
    endLabel = cmds.text(l='End:')
    startCtrl = cmds.intField(w=60,v=int(cmds.playbackOptions(q=1,min=1)))
    endCtrl = cmds.intField(w=60,v=int(cmds.playbackOptions(q=1,max=1)))
    accCtrl = cmds.intSliderGrp(min=1,max=500,value=100,step=10,w=250,f=1)
    btnCtrl = cmds.button(w=100,h=50,l='bake rotation',c=lambda *x: doAutoRotations(cmds.ls(sl=1),cmds.optionMenu(axisCtrl,q=1,v=1),cmds.floatField(diamCtrl,q=1,v=1),cmds.intSliderGrp(accCtrl,q=1,v=1),cmds.intField(startCtrl,q=1,v=1),cmds.intField(endCtrl,q=1,v=1),increment))
    cmds.formLayout(flayout,e=1,attachForm=[(axisLabel,'left',lm[0]),(axisLabel,'top',tm[0]),(axisCtrl,'left',lm[1]),(axisCtrl,'top',tm[0]),(diamLabel,'left',lm[0]),(diamLabel,'top',tm[1]),(diamCtrl,'left',lm[1]),(diamCtrl,'top',tm[1]),(accLabel,'left',lm[0]),(accLabel,'top',tm[2]),(accCtrl,'left',lm[1]),(accCtrl,'top',tm[2]),(btnCtrl,'left',lm[0]),(btnCtrl,'top',tm[-1]),(startLabel,'left',lm[0]),(startLabel,'top',tm[3]),(startCtrl,'left',lm[1]),(startCtrl,'top',tm[3]),(endLabel,'left',lm[0]),(endLabel,'top',tm[4]),(endCtrl,'left',lm[1]),(endCtrl,'top',tm[4])])
    cmds.showWindow(rotateWindow)
    cmds.window(windowName,e=1,w=350,h=180)
    
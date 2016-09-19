# support scripts for hfRig v0.02
# henry foster (henry@toadstorm.com), 2012/02/13

import maya.cmds as cmds

def getWorldSpace(target,*args):
    # use a locator and a parent constraint to quickly get the worldspace coordinates of an object.
    loc = cmds.spaceLocator()[0]
    pc = cmds.parentConstraint(target,loc)
    tx = cmds.getAttr(loc+'.tx')
    ty = cmds.getAttr(loc+'.ty')
    tz = cmds.getAttr(loc+'.tz')
    cmds.delete(loc)
    return (tx,ty,tz)

def getVectorMult(v0,v1,ratio,*args):
    # apply scalar 'ratio' to vectors v0 and v1, return result.
    outX = ((v1[0]-v0[0])*ratio)+v0[0]
    outY = ((v1[1]-v0[1])*ratio)+v0[1]
    outZ = ((v1[2]-v0[2])*ratio)+v0[2]
    return (outX,outY,outZ)

def makeCurve(curveType,name,target='',matchAxes=True,color=0,*args):
    # generate a simple control curve based on curveType.
    # if target is defined, point constraint the curve's parent group to the target.
    # if matchAxes is true, orient the curve's parent group to match the rotation axes of target.
    curve = ''
    if curveType=='arrow':
        curve = cmds.curve(d=1,p=[(0,0.6724194,0.4034517),(0,0,0.4034517),(0,0,0.6724194),(0,-0.4034517,0),(0,0,-0.6724194),(0,0,-0.4034517),(0,0.6724194,-0.4034517),(0,0.6724194,0.4034517)],k=[0,1,2,3,4,5,6,7])
        cmds.setAttr(curve+'.rz',90)
        cmds.setAttr(curve+'.ry',90)
        cmds.setAttr(curve+'.sx',1.5)
        cmds.setAttr(curve+'.sy',1.5)
        cmds.setAttr(curve+'.sz',1.5)
    elif curveType=='cross':
        curve = cmds.curve(d=1,p=[(1,0,-1),(2,0,-1),(2,0,1),(1,0,1),(1,0,2),(-1,0,2),(-1,0,1),(-2,0,1),(-2,0,-1),(-1,0,-1),(-1,0,-2),(1,0,-2),(1,0,-1)],k=[0,1,2,3,4,5,6,7,8,9,10,11,12])
        cmds.setAttr(curve+'.rx',90)
    elif curveType=='snow':
        curve = cmds.curve(d=1,p=[(4.4408920985006262e-01,-0.0015683700000006517,2),(1.0000000000000004,-6.6613381477509392e-016,1.9999999999999998),(1.0000000000000002,-4.4408920985006257e-016,0.99999999999999978),(2,-6.6613381477509383e-016,0.99999999999999956),(2,0,-0.0015683700000002077),(2,1,-2.2204460492503131e-016),(1,1,-2.2204460492503131e-016),(1,2,-4.4408920985006262e-016),(-1,2,-4.4408920985006262e-016),(-1,1,-2.2204460492503131e-016),(-2,1,-2.2204460492503131e-016),(-2,-1,2.2204460492503131e-016),(-1,-1,2.2204460492503131e-016),(-1,-2,4.4408920985006262e-016),(1,-2,4.4408920985006262e-016),(1,-1,2.2204460492503131e-016),(2,-1,2.2204460492503131e-016),(2,0,-0.0015683700000002077),(2,-6.6613381477509383e-016,0.99999999999999956),(1.0000000000000002,-4.4408920985006257e-016,0.99999999999999978),(1.0000000000000004,-6.6613381477509392e-016,1.9999999999999998),(0.099999999999998312,-0.0014115330000006563,2),(4.4408920985006262e-016,-0.0015683700000006517,2),(-0.10000000000000098,-0.0014115330000006067,2),(-0.99999999999999956,-2.2204460492503136e-016,2.0000000000000004),(-0.99999999999999978,-4.9303806576313238e-032,1.0000000000000002),(-1.9999999999999998,2.2204460492503121e-016,1.0000000000000004),(-2,6.6613381477509383e-016,-0.99999999999999956),(-1.0000000000000002,4.4408920985006257e-016,-0.99999999999999978),(-1.0000000000000004,6.6613381477509392e-016,-1.9999999999999998),(0.99999999999999956,2.2204460492503136e-016,-2.0000000000000004),(0.99999999999999978,4.9303806576313238e-032,-1.0000000000000002),(1.9999999999999998,-2.2204460492503121e-016,-1.0000000000000004),(2,-6.6613381477509383e-016,0.99999999999999956),(1.0000000000000002,-4.4408920985006257e-016,0.99999999999999978),(1.0000000000000004,-6.6613381477509392e-016,1.9999999999999998),(0.099999999999998312,-0.0014115330000006563,2),(4.4408920985006262e-016,-0.0015683700000006517,2),(3.9968028886505572e-016,-0.10141153300000205,2),(0,-1.0000000000000004,1.9999999999999998),(-2.2204460492503131e-016,-1.0000000000000002,0.99999999999999978),(-6.6613381477509392e-016,-2,0.99999999999999956),(-1.1102230246251565e-015,-1.9999999999999998,-1.0000000000000004),(-6.6613381477509392e-016,-0.99999999999999978,-1.0000000000000002),(-8.8817841970012523e-016,-0.99999999999999956,-2),(0,1.0000000000000004,-1.9999999999999998),(2.2204460492503131e-016,1.0000000000000002,-0.99999999999999978),(6.6613381477509392e-016,2,-0.99999999999999956),(1.1102230246251565e-015,1.9999999999999998,1.0000000000000004),(6.6613381477509392e-016,0.99999999999999978,1.0000000000000002),(8.8817841970012523e-016,0.99999999999999956,2),(0.0015683700000006517,-4.4443745794708893e-016,2),(4.4408920985006262e-016,-0.0015683700000006517,2)],
        k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52])
        cmds.setAttr(curve+'.sx',0.5)
        cmds.setAttr(curve+'.sy',0.5)
        cmds.setAttr(curve+'.sz',0.5)
    elif curveType=='square':
        curve = cmds.curve(d=1,p=[(-1,0,1),(1,0,1),(1,0,-1),(-1,0,-1),(-1,0,1)],k=[0,1,2,3,4])
        cmds.setAttr(curve+'.rx',90)
    elif curveType=='circle':
        curve = cmds.curve(d=3,p=[(-0.50525882489399365,0,-0.83512503818809947),(0.022313365804565437,0,-0.96744341986682636),(0.71031056148790783,0,-0.71031056148790783),(1,0,0),(0.71031056148790783,0,0.71031056148790783),(0,0,1),(-0.71031056148790783,0,0.71031056148790783),(-0.98309609442669621,0,0.0077060138797057087),(-0.81476494957991508,0,-0.54554155937325666),(-0.50525882489399365,0,-0.83512503818809947),(0.022313365804565437,0,-0.96744341986682636),(0.71031056148790783,0,-0.71031056148790783)],
        k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13])
        cmds.setAttr(curve+'.rx',90)
    elif curveType=='cube':
        curve = cmds.curve(d=1,p=[(-0.5,0.5,0.5),(0.5,0.5,0.5),(0.5,0.5,-0.5),(-0.5,0.5,-0.5),(-0.5,0.5,0.5),(-0.5,-0.5,0.5),(-0.5,-0.5,-0.5),(0.5,-0.5,-0.5),(0.5,-0.5,0.5),(-0.5,-0.5,0.5),(0.5,-0.5,0.5),(0.5,0.5,0.5),(0.5,0.5,-0.5),(0.5,-0.5,-0.5),(-0.5,-0.5,-0.5),(-0.5,0.5,-0.5)],
        k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
        cmds.setAttr(curve+'.sx',2)
        cmds.setAttr(curve+'.sy',2)
        cmds.setAttr(curve+'.sz',2)
    elif curveType=='roundCube':
        curve = cmds.curve(d=1,p=[(-0.5009066471890149,0.60793641188909775,0.73118575537458508),(0.50090664718901801,0.82865315865866107,0.87846330410159157),(0.50090664718901801,0.97968935442399785,0.44742662270877043),(0.50090664718901801,1.0202129758943719,1.1245241575642032e-015),(0.50090664718901801,0.97968935442399829,-0.44742662270876832),(0.50090664718901801,0.82865315865866107,-0.87846330410158957),(-0.5009066471890149,0.60793641188909775,-0.73118575537458297),(-0.5009066471890149,0.60793641188909775,0.73118575537458508),(-0.50090664718901501,-0.6079364118891063,0.73118575537458508),(-0.50090664718901501,-0.6079364118891063,-0.73118575537458297),(0.5009066471890179,-0.82865315865866929,-0.87846330410158957),(0.5009066471890179,-0.97968935442400651,-0.44742662270876832),(0.5009066471890179,-1.0202129758943803,1.0238432495687358e-015),(0.5009066471890179,-0.97968935442400651,0.44742662270877043),(0.5009066471890179,-0.82865315865866929,0.87846330410159157),(-0.50090664718901501,-0.6079364118891063,0.73118575537458508),(0.5009066471890179,-0.82865315865866929,0.87846330410159157),(0.5009066471890179,-0.42205688324657348,1.042971853654209),(0.5009066471890179,-4.0646663654151772e-015,1.0784992010176448),(0.5009066471890179,0.42205688324656521,1.042971853654209),(0.50090664718901801,0.82865315865866107,0.87846330410159157),(0.50090664718901801,0.97968935442399785,0.44742662270877043),(0.50090664718901801,1.0202129758943719,1.1245241575642032e-015),(0.50090664718901801,0.97968935442399829,-0.44742662270876832),(0.50090664718901801,0.82865315865866107,-0.87846330410158957),(0.50090664718901801,0.42205688324656515,-1.0429718536542065),(0.5009066471890179,-4.090379302991285e-015,-1.0784992010176429),(0.5009066471890179,-0.42205688324657353,-1.0429718536542065),(0.5009066471890179,-0.82865315865866929,-0.87846330410158957),(-0.50090664718901501,-0.6079364118891063,-0.73118575537458297),(-0.5009066471890149,0.60793641188909775,-0.73118575537458297)],
        k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30])
        cmds.setAttr(curve+'.rx',90)
        cmds.setAttr(curve+'.ry',0)
        cmds.setAttr(curve+'.rz',180)
        cmds.setAttr(curve+'.tx',0.5)
        cmds.move(-0.5,0,0,curve+'.scalePivot',r=1)
        cmds.move(-0.5,0,0,curve+'.rotatePivot',r=1)
    elif curveType=='flatCube':
        curve = cmds.curve(d=1,p=[(-1.4454197399737647,0.074786005662381347,0.33859391820135609),(-0.0011382759774108964,0.18032561162967517,0.5),(-0.0011382759774108964,0.18032561162967517,-0.5),(-1.4454197399737647,0.074786005662381347,-0.33859391820135609),(-1.4454197399737647,0.074786005662381347,0.33859391820135609),(-1.4454197399737647,-0.074786005662381347,0.33859391820135609),(-1.4454197399737647,-0.074786005662381347,-0.33859391820135609),(-0.0011382759774108964,-0.18032561162967517,-0.5),(-0.0011382759774108964,-0.18032561162967517,0.5),(-1.4454197399737647,-0.074786005662381347,0.33859391820135609),(-0.0011382759774108964,-0.18032561162967517,0.5),(-0.0011382759774108964,0.18032561162967517,0.5),(-0.0011382759774108964,0.18032561162967517,-0.5),(-0.0011382759774108964,-0.18032561162967517,-0.5),(-1.4454197399737647,-0.074786005662381347,-0.33859391820135609),(-1.4454197399737647,0.074786005662381347,-0.33859391820135609)],
        k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
        cmds.setAttr(curve+'.rx',90)
        cmds.setAttr(curve+'.ry',0)
        cmds.setAttr(curve+'.rz',180)
    elif curveType=='orient':
        curve = cmds.curve(d=3,p=[(0.0959835,0.604001,-0.0987656),(0.500783,0.500458,-0.0987656),(0.751175,0.327886,-0.0987656),(0.751175,0.327886,-0.0987656),(0.751175,0.327886,-0.336638),(0.751175,0.327886,-0.336638),(1.001567,0,0),(1.001567,0,0),(0.751175,0.327886,0.336638),(0.751175,0.327886,0.336638),(0.751175,0.327886,0.0987656),(0.751175,0.327886,0.0987656),(0.500783,0.500458,0.0987656),(0.0959835,0.604001,0.0987656),(0.0959835,0.604001,0.0987656),(0.0959835,0.500458,0.500783),(0.0959835,0.327886,0.751175),(0.0959835,0.327886,0.751175),(0.336638,0.327886,0.751175),(0.336638,0.327886,0.751175),(0,0,1.001567),(0,0,1.001567),(-0.336638,0.327886,0.751175),(-0.336638,0.327886,0.751175),(-0.0959835,0.327886,0.751175),(-0.0959835,0.327886,0.751175),(-0.0959835,0.500458,0.500783),(-0.0959835,0.604001,0.0987656),(-0.0959835,0.604001,0.0987656),(-0.500783,0.500458,0.0987656),(-0.751175,0.327886,0.0987656),(-0.751175,0.327886,0.0987656),(-0.751175,0.327886,0.336638),(-0.751175,0.327886,0.336638),(-1.001567,0,0),(-1.001567,0,0),(-0.751175,0.327886,-0.336638),(-0.751175,0.327886,-0.336638),(-0.751175,0.327886,-0.0987656),(-0.751175,0.327886,-0.0987656),(-0.500783,0.500458,-0.0987656),(-0.0959835,0.604001,-0.0987656),(-0.0959835,0.604001,-0.0987656),(-0.0959835,0.500458,-0.500783),(-0.0959835,0.327886,-0.751175),(-0.0959835,0.327886,-0.751175),(-0.336638,0.327886,-0.751175),(-0.336638,0.327886,-0.751175),(0,0,-1.001567),(0,0,-1.001567),(0.336638,0.327886,-0.751175),(0.336638,0.327886,-0.751175),(0.0959835,0.327886,-0.751175),(0.0959835,0.327886,-0.751175),(0.0959835,0.500458,-0.500783),(0.0959835,0.604001,-0.0987656)],
        k=[0,0,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,53,53])
        cmds.setAttr(curve+'.rx',90)
    elif curveType=='bendedDoubleArrow':
        curve = cmds.curve(d=3,p=[(0.095983499999999999,0.60400100000000012,-0.098765600000000009),(0.095983499999999999,0.60400100000000012,0.098765600000000009),(0.095983499999999999,0.60400100000000012,0.098765600000000009),(0.095983499999999999,0.50045799999999996,0.50078300000000009),(0.095983499999999999,0.32788600000000001,0.75117500000000004),(0.095983499999999999,0.32788600000000001,0.75117500000000004),(0.33663799999999999,0.32788600000000001,0.75117500000000004),(0.33663799999999999,0.32788600000000001,0.75117500000000004),(0,0,1.0015670000000001),(0,0,1.0015670000000001),(-0.33663799999999999,0.32788600000000001,0.75117500000000004),(-0.33663799999999999,0.32788600000000001,0.75117500000000004),(-0.095983499999999999,0.32788600000000001,0.75117500000000004),(-0.095983499999999999,0.32788600000000001,0.75117500000000004),(-0.095983499999999999,0.50045799999999996,0.50078300000000009),(-0.095983499999999999,0.60400100000000012,0.098765600000000009),(-0.095983499999999999,0.60400100000000012,0.098765600000000009),(-0.095983499999999999,0.60400100000000012,-0.098765600000000009),(-0.095983499999999999,0.60400100000000012,-0.098765600000000009),(-0.095983499999999999,0.50045799999999996,-0.50078300000000009),(-0.095983499999999999,0.32788600000000001,-0.75117500000000004),(-0.095983499999999999,0.32788600000000001,-0.75117500000000004),(-0.33663799999999999,0.32788600000000001,-0.75117500000000004),(-0.33663799999999999,0.32788600000000001,-0.75117500000000004),(0,0,-1.0015670000000001),(0,0,-1.0015670000000001),(0.33663799999999999,0.32788600000000001,-0.75117500000000004),(0.33663799999999999,0.32788600000000001,-0.75117500000000004),(0.095983499999999999,0.32788600000000001,-0.75117500000000004),(0.095983499999999999,0.32788600000000001,-0.75117500000000004),(0.095983499999999999,0.50045799999999996,-0.50078300000000009),(0.095983499999999999,0.60400100000000012,-0.098765600000000009)],
        k=[0,0,0,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,41,42,43,44,45,46,47,48,49,50,51,52,53,53,53])
        cmds.setAttr(curve+'.rx',90)
        cmds.setAttr(curve+'.rz',-90)
    elif curveType=='spike':
        curve = cmds.curve(d=1,p=[(-0.26962052657709101,0.26962052657709457,3.978142725902245e-006),(0.26962052657709101,0.26962052657709457,3.978142725902245e-006),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-0.26962052657709101,0.26962052657709457,3.978142725902245e-006),(-0.26962052657709101,-0.26962052657708835,3.978142725902245e-006),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(0.26962052657709101,-0.26962052657708835,3.978142725902245e-006),(-0.26962052657709101,-0.26962052657708835,3.978142725902245e-006),(0.26962052657709101,-0.26962052657708835,3.978142725902245e-006),(0.26962052657709101,0.26962052657709457,3.978142725902245e-006),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432),(-9.2566414394923413e-005,-9.2566414394035235e-005,-1.6708418691196432)],
        k=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
        cmds.setAttr(curve+'.rx',180)
        cmds.setAttr(curve+'.ry',90)
    # create a group at the origin to contain the control.
    curve = cmds.rename(curve,name)
    cmds.makeIdentity(curve,a=1,t=1,r=1,s=1)
    ctrlGrp = cmds.group(em=1,n=name+'_grp',w=1,r=1)
    pc = cmds.pointConstraint(curve,ctrlGrp)
    cmds.delete(pc)
    cmds.parent(curve,ctrlGrp)
    if target != '':
        # constrain the ctrlGrp to the target, then delete the constraint.
        # if matchAxes=True, also orient constraint.
        pc = cmds.pointConstraint(target,ctrlGrp)[0]
        cmds.delete(pc)
        if matchAxes:
            oc = cmds.orientConstraint(target,ctrlGrp)[0]
            cmds.delete(oc)
        cmds.makeIdentity(curve,a=1,t=1,r=1,s=1)
    # the controller is fitted and in place. now let the user fuck with it until they're ready to apply the constraints.
    cmds.select(curve)
    if color != 0:
        curveShape = cmds.listRelatives(curve,s=1)[0]
        cmds.setAttr(curveShape+'.overrideEnabled',1)
        cmds.setAttr(curveShape+'.drawOverride.overrideColor',color)
    return curve

def swapCurve(curve,newType,*args):
    # replace an existing control curve with a new one.
    curveParent = cmds.listRelatives(curve,p=1)[0]
    curveShape = cmds.listRelatives(curve,s=1)[0]
    color = cmds.getAttr(curveShape+'.drawOverride.overrideColor')
    newCurve = makeCurve(newType,curve+'_replace',curveParent,True,color)
    # match xforms from curve to newCurve.
    tx,ty,tz = cmds.getAttr(curve+'.tx'),cmds.getAttr(curve+'.ty'),cmds.getAttr(curve+'.tz')
    rx,ry,rz = cmds.getAttr(curve+'.rx'),cmds.getAttr(curve+'.ry'),cmds.getAttr(curve+'.rz')
    sx,sy,sz = cmds.getAttr(curve+'.sx'),cmds.getAttr(curve+'.sy'),cmds.getAttr(curve+'.sz')
    cmds.setAttr(newCurve+'.tx',tx)
    cmds.setAttr(newCurve+'.ty',ty)
    cmds.setAttr(newCurve+'.tz',tz)
    cmds.setAttr(newCurve+'.rx',rx)
    cmds.setAttr(newCurve+'.ry',ry)
    cmds.setAttr(newCurve+'.rz',rz)
    cmds.setAttr(newCurve+'.sx',sx)
    cmds.setAttr(newCurve+'.sy',sy)
    cmds.setAttr(newCurve+'.sz',sz)
    cmds.delete(curveParent)
    newCurve = cmds.rename(newCurve,curve)
    newCurveParent = cmds.listRelatives(curve,p=1)[0]
    cmds.rename(newCurveParent,newCurve+'_grp')
    return newCurve

def changeCurveColor(curve,color,*args):
    curveShape = cmds.listRelatives(curve,s=1)[0]
    cmds.setAttr(curveShape+'.drawOverride.overrideColor',color)

def applyCtrl(curve,target,point=True,orient=True,scale=True):
    # make them constraints. easy enough.
    # first, if the control has been moved, shift the pivot so that it matches the pivot of its parent group.
    tx,ty,tz = cmds.getAttr(curve+'.tx'),cmds.getAttr(curve+'.ty'),cmds.getAttr(curve+'.tz')
    cmds.setAttr(curve+'.rotatePivotX',tx*-1.0)
    cmds.setAttr(curve+'.rotatePivotY',ty*-1.0)
    cmds.setAttr(curve+'.rotatePivotZ',tz*-1.0)
    cmds.setAttr(curve+'.scalePivotX',tx*-1.0)
    cmds.setAttr(curve+'.scalePivotY',ty*-1.0)
    cmds.setAttr(curve+'.scalePivotZ',tz*-1.0)
    cmds.makeIdentity(curve,a=1,t=1,r=1,s=1)
    if point and orient:
        cmds.parentConstraint(curve,target,mo=1)
    elif point and not orient:
        cmds.parentConstraint(curve,target,sr=['x','y','z'],mo=1)
    elif orient and not point:
        cmds.parentConstraint(curve,target,st=['x','y','z'],mo=1)
    if scale:
        cmds.scaleConstraint(curve,target,mo=1)

def snapSwitch(setKeys=1,findNode=0,*args):
    # from a selected object, traverse the DAG until we find the pivot object, figure out the current control state,
    # then swap to the opposite state and set a key on the ik/fk switch.
    # if findNode==1, then just select the pivot object so the user can look at current switch keyframes.
    testObj = cmds.ls(sl=1)[0]
    attachPivot = ''
    messageConns = cmds.listConnections(testObj+'.message')
    for i in messageConns:
        if cmds.attributeQuery('hfRig',node=i,ex=1):
            attachPivot = i
    if attachPivot == '':
        cmds.error("Couldn't find the control node from the selected object. Try selecting a controller.")
    if findNode:
        cmds.select(attachPivot)
        return
    # now the hard work. from attachPivot, we can get the names of all our controls and bones.
    ikCtrl = cmds.listConnections(attachPivot+'.ik_ctrl')[0]
    ik_pvCtrl = cmds.listConnections(attachPivot+'.ik_pvCtrl')[0]
    ik_fk_switch = cmds.getAttr(attachPivot+'.IK_FK_switch')
    fkTopCtrl = cmds.listConnections(attachPivot+'.fkTopCtrl')[0]
    fkMidCtrl = cmds.listConnections(attachPivot+'.fkMidCtrl')[0]
    fkBotCtrl = cmds.listConnections(attachPivot+'.fkBotCtrl')[0]
    fkPoleVectorGuide = cmds.listConnections(attachPivot+'.fk_poleVectorGuide')[0]
    ik_top = cmds.listConnections(attachPivot+'.ik_top')[0]
    ik_mid = cmds.listConnections(attachPivot+'.ik_mid')[0]
    ik_bot = cmds.listConnections(attachPivot+'.ik_bot')[0]
    fk_bot = cmds.listConnections(attachPivot+'.fk_bot')[0]
    curveCtrl = cmds.listConnections(attachPivot+'.curveCtrl')[0]
    # based on whether we are currently in FK mode or IK mode, get the values of the objects we want and then move the other set of controls.
    if ik_fk_switch == 1:
        # ik to fk. easy.
        top_rotate = cmds.getAttr(ik_top+'.rotate')[0]
        mid_rotate = cmds.getAttr(ik_mid+'.rotate')[0]
        bot_rotate = cmds.getAttr(ik_bot+'.rotate')[0]
        top_scale = cmds.getAttr(ik_top+'.scale')[0]
        mid_scale = cmds.getAttr(ik_mid+'.scale')[0]
        m0,m1,m2 = getWorldSpace(curveCtrl)
        curveRotate = cmds.xform(curveCtrl,q=1,ws=1,ro=1)
        # set attributes on the fk controllers, then set a key.
        cmds.setAttr(fkTopCtrl+'.rx',top_rotate[0])
        cmds.setAttr(fkTopCtrl+'.ry',top_rotate[1])
        cmds.setAttr(fkTopCtrl+'.rz',top_rotate[2])
        cmds.setAttr(fkMidCtrl+'.rx',mid_rotate[0])
        cmds.setAttr(fkMidCtrl+'.ry',mid_rotate[1])
        cmds.setAttr(fkMidCtrl+'.rz',mid_rotate[2])
        cmds.setAttr(fkBotCtrl+'.rx',bot_rotate[0])
        cmds.setAttr(fkBotCtrl+'.ry',bot_rotate[1])
        cmds.setAttr(fkBotCtrl+'.rz',bot_rotate[2])
        cmds.setAttr(fkTopCtrl+'.sx',top_scale[0])
        # cmds.setAttr(fkMidCtrl+'.sx',mid_scale[0])
        cmds.setAttr(curveCtrl+'.IK_FK_switch',0)
        # check the midpoint and make sure it didn't shift.
        if setKeys:
            cmds.setKeyframe(fkTopCtrl+'.rx')
            cmds.setKeyframe(fkTopCtrl+'.ry')
            cmds.setKeyframe(fkTopCtrl+'.rz')
            cmds.setKeyframe(fkTopCtrl+'.sx')
            cmds.setKeyframe(fkMidCtrl+'.rx')
            cmds.setKeyframe(fkMidCtrl+'.ry')
            cmds.setKeyframe(fkMidCtrl+'.rz')
            cmds.setKeyframe(fkMidCtrl+'.sx')
            cmds.setKeyframe(fkBotCtrl+'.rx')
            cmds.setKeyframe(fkBotCtrl+'.ry')
            cmds.setKeyframe(fkBotCtrl+'.rz')
            cmds.setKeyframe(curveCtrl+'.IK_FK_switch')
        # now doublecheck the midpoint.
        n0,n1,n2 = getWorldSpace(curveCtrl)
        if m0!=n0 or m1!=n1 or m2!=n2:
            cmds.xform(curveCtrl,ws=1,t=[m0,m1,m2])
            cmds.xform(curveCtrl,ws=1,ro=[curveRotate[0],curveRotate[1],curveRotate[2]])
            if setKeys:
                chans = ['tx','ty','tz','rx','ry','rz']
                for c in chans:
                    cmds.setKeyframe(curveCtrl+'.'+c)
        # toggle rig visibility.
        cmds.setAttr(curveCtrl+'.showFKControls',1)
        cmds.setAttr(curveCtrl+'.showIKControls',0)
    else:
        # fk to ik. a little trickier. start by getting the translate value of fk_bot, then get the translate of fkPoleVectorGuide.
        # use these values to position the ikCtrl and ik_pvCtrl.
        # the midpoint controller is the tricky part... if the fk joints are not evenly scaled, the ik won't match unless the midpoint
        # controller ends up in the exact same place. get its worldspace coords before and after the snap. if they don't match,
        # snap the controller into the correct place and set a key.
        b0,b1,b2 = getWorldSpace(fkBotCtrl)
        g0,g1,g2 = getWorldSpace(fkPoleVectorGuide)
        m0,m1,m2 = getWorldSpace(curveCtrl)
        curveRotate = cmds.xform(curveCtrl,q=1,ws=1,ro=1)
        cmds.xform(ikCtrl,ws=1,t=[b0,b1,b2])
        cmds.xform(ik_pvCtrl,ws=1,t=[g0,g1,g2])
        # now set rotations. the wrist isn't going to get rotations in quite the same way because the parenting structure is a little different.
        # use a temporary orient constraint.
        # rx,ry,rz = cmds.getAttr(fkBotCtrl+'.rx'),cmds.getAttr(fkBotCtrl+'.ry'),cmds.getAttr(fkBotCtrl+'.rz')
        # cmds.setAttr(ikCtrl+'.rx',rx)
        # cmds.setAttr(ikCtrl+'.ry',ry)
        # cmds.setAttr(ikCtrl+'.rz',rz)
        cmds.setAttr(curveCtrl+'.IK_FK_switch',1)
        oc = cmds.orientConstraint(fkBotCtrl,ikCtrl)
        cmds.delete(oc)
        if setKeys:
            chans = ['tx','ty','tz','rx','ry','rz']
            for c in chans:
                cmds.setKeyframe(ikCtrl+'.'+c)
            chans = ['tx','ty','tz']
            for c in chans:
                cmds.setKeyframe(ik_pvCtrl+'.'+c)
            cmds.setKeyframe(curveCtrl+'.IK_FK_switch')
        # now we need to compare the curveCtrl's current xforms against its previous xforms. if different, move to the original coordinates
        # and set a keyframe.
        n0,n1,n2 = getWorldSpace(curveCtrl)
        if m0!=n0 or m1!=n1 or m2!=n2:
            cmds.xform(curveCtrl,ws=1,t=[m0,m1,m2])
            cmds.xform(curveCtrl,ws=1,ro=[curveRotate[0],curveRotate[1],curveRotate[2]])
            if setKeys:
                chans = ['tx','ty','tz','rx','ry','rz']
                for c in chans:
                    cmds.setKeyframe(curveCtrl+'.'+c)
        cmds.setAttr(curveCtrl+'.showFKControls',0)
        cmds.setAttr(curveCtrl+'.showIKControls',1)
    # reselect whatever we had selected.
    cmds.select(testObj)
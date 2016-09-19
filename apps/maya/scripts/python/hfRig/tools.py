""" 
hfRig miscellaneous tools by renry (henry@toadstorm.com)
v0.01
11/26/2012

Miscellaneous tools for handling rigging operations.
"""

import maya.cmds as cmds

def getWorldSpace(target,*args):
    # return the world space coordinates of target: translate, rotate, scale as a list of tuples.
    dm = cmds.createNode('decomposeMatrix')
    cmds.connectAttr(target+'.worldMatrix',dm+'.inputMatrix')
    outTranslate = cmds.getAttr(dm+'.outputTranslate')[0]
    outRotate = cmds.getAttr(dm+'.outputRotate')[0]
    outScale = cmds.getAttr(dm+'.outputScale')[0]
    cmds.delete(dm)
    return outTranslate, outRotate, outScale
    
def getMidpoint(obj1,obj2,bias=0.5,*args):
    # return world space translate for an object that rests directly between obj1 and obj2. optional bias moves midpoint towards obj1 or obj2.
    v0 = getWorldSpace(obj1)[0]
    v1 = getWorldSpace(obj2)[0]
    midpoint = [ ((b-a)*bias)+a for a,b in zip(v0,v1) ]
    return midpoint
    
def splitJoint(start,end,splits):
    # get the vector of the child joint and divide it by splits. then put a goddamn joint at that vector for each split.
    parent_ = start
    vec = cmds.getAttr(end+'.translate')[0]
    for x in range(1,splits+1):
        # range should be 1/5, 2/5... 4/5
        div = float(x)/(splits+1)
        newvec = [f*div for f in vec]
        # duplicate start, parent to start, move to newvec, parent to parent_, reset parent_.
        newjnt = cmds.duplicate(start,po=1)[0]
        newjnt = cmds.parent(newjnt,start)[0]
        cmds.setAttr(newjnt+'.tx',newvec[0])
        cmds.setAttr(newjnt+'.ty',newvec[1])
        cmds.setAttr(newjnt+'.tz',newvec[2])
        if parent_ != start:
            newjnt = cmds.parent(newjnt,parent_)[0]
        newjnt = cmds.rename(newjnt,start+'_split_'+str(x))
        # force connect parent.scale --> child.inversescale
        if not cmds.listConnections(newjnt+'.inverseScale'):
            cmds.connectAttr(parent_+'.scale',newjnt+'.inverseScale',f=1)
        parent_ = newjnt
    # parent end to parent_
    cmds.parent(end,parent_)
    cmds.connectAttr(parent_+'.scale',end+'.inverseScale')
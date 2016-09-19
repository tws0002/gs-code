import maya.cmds as cmds

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
import maya.cmds as cmds

def addDeformerControls(nonlinear,controller):
    # for a given nonlinear deformer, get all attributes, add to controller and connect
    chans = [f for f in cmds.listAttr(nonlinear,k=1) if 'weightList.weights' not in f]
    for ch in chans:
        atType = cmds.attributeQuery(ch,node=nonlinear,at=1) # returns string
        isSoftRange = cmds.attributeQuery(ch,node=nonlinear,se=1)
        softRange = []
        if isSoftRange:
            softRange = cmds.attributeQuery(ch,node=nonlinear,s=1) # returns list of floats/ints
        atName = nonlinear+'_'+ch
        defaultValue = cmds.getAttr(nonlinear+'.'+ch)
        # add attribute to controller and set value to match
        cmds.select(controller)
        try:
            if isSoftRange:
                cmds.addAttr(ln=atName,defaultValue=defaultValue,smn=softRange[0],smx=softRange[1],k=1,at=atType)
            else:
                cmds.addAttr(ln=atName,defaultValue=defaultValue,k=1,at=atType)
            cmds.setAttr(controller+'.'+atName,cb=1,l=0)
            cmds.setAttr(controller+'.'+atName,k=1)
            cmds.connectAttr(controller+'.'+atName, nonlinear+'.'+ch)
            print 'added channel %s to controller %s' % (atName,controller)
        except:
            print 'could not add attribute %s to controller %s' % (atName,controller)
            
def getDeformersFromMesh(object):
    meshes = cmds.listRelatives(object,s=1)
    deformers = []
    if meshes:
        for i in meshes:
            history = cmds.listHistory(i)
            d = [f for f in history if cmds.objectType(f) == 'nonLinear']
            if d:
                deformers.extend(d)
    return deformers
    
def controlDeformers():
    # select any number of objects with nonlinear deformers. select a control object last. the control object will be given channels to control
    # the channels on any nonlinear deformers attached to the selected objects.
    sel = cmds.ls(sl=1)
    if sel:
        objects = sel[:-1]
        controller = sel[-1]
        allDeformers = []
        for i in objects:
            d = getDeformersFromMesh(i)
            if d:
                allDeformers.extend(d)
        # remove duplicates
        allDeformers = list(set(allDeformers))
        print 'deformers found: %s' % (','.join(allDeformers))
        for d in allDeformers:
            addDeformerControls(d,controller)
    else:
        # you are stupid
        print 'select any number of transforms, and a control object last.'
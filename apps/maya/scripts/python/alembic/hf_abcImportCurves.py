# ALEMBIC CURVES IMPORTER v0.1 by renry (henry@toadstorm.com)
#
# Imports animated NURBS curves exported in the Alembic format from Houdini.

def importCurves():
    import maya.cmds as cmds
    import maya.mel as mel
    import os
    # create default group
    cmds.select(cl=1)
    importGroup = cmds.group(em=1,n="ALEMBIC_CURVES")
    dataPath = os.path.join(cmds.workspace(q=1,dir=1),"cache")
    fileFilter = "Alembic Files (*.abc)"
    # get abc file
    getFile = cmds.fileDialog2(ds=1,cap="Choose Alembic Cache...",dir=dataPath,ff=fileFilter,fm=1)[0]
    melStr = 'AbcImport -rpr '+importGroup+' "'+getFile+'"'
    abcNode = mel.eval(melStr)
    # get all curves underneath the importGroup
    curves = cmds.listRelatives(importGroup,ad=1,typ="nurbsCurve")
    # loop through each curve and connect to abcnode
    for x in range(0,len(curves)):
        try:
            cmds.connectAttr(abcNode+'.outNCurveGrp['+str(x)+']',curves[x]+'.create',f=1)
        except (RuntimeError):
            pass
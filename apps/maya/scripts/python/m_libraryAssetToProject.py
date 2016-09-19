import maya.standalone as std
import sys
import os

std.initialize(name='python')
import maya.cmds as cmds

path = sys.argv[1]
cmds.file(path,o=1,f=1)
try:
    if not cmds.objExists('GEOgrp'):
        groups = []
        GEOgrp = cmds.group(em=1,n='GEOgrp')
        groups.append(GEOgrp)
        RIGgrp = cmds.group(em=1,n='RIGgrp')
        groups.append(RIGgrp)
        GUTSgrp = cmds.group(em=1,n='GUTSgrp')
        groups.append(GUTSgrp)
        # cmds.select(['GEOgrp','RIGgrp','GUTSgrp'],add=1)
        name = os.path.splitext(os.path.basename(path))[0]+'_GRP'
        groups.append(cmds.group(GEOgrp,RIGgrp,GUTSgrp,n=name))
        # lock channels.
        axes = ['x','y','z']
        chans = ['t','r','s']
        for a in axes:
            for b in chans:
                for group in groups:
                    cmds.setAttr(group+'.'+b+a,lock=1)
        for g in groups:
            cmds.lockNode(group,lock=True)
except Exception, err:
    sys.stderr.write(str(err))
# make initial sets.
if not cmds.objExists('CACHEset'):
    cacheset = cmds.sets(n='CACHEset',em=1)
    rigset = cmds.sets(n='RIGset',em=1)
    # lockdown sets.
    cmds.lockNode(cacheset,lock=1)
    cmds.lockNode(rigset,lock=1)
# if this is not a mayaBinary file it will need to be converted.
unk = cmds.ls(type='unknown')
if unk:
    for i in unk:
        cmds.lockNode(i,lock=0)
        cmds.delete(i)
if os.path.splitext(path)[-1] != '.mb':
    cmds.file(rename=os.path.splitext(path)[0]+'.mb')
outFile = cmds.file(s=1,f=1,type='mayaBinary')
sys.stdout.write(outFile)
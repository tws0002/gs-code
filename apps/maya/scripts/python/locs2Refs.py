import maya.cmds as cmds
import os

# select a set of xforms. for each xform, grab the world space transform information, create a reference to a file, throw that reference onto every xform.

def locs2Refs():
    xforms = [f for f in cmds.ls(sl=1) if cmds.objectType(f) == 'transform']
    # open file dialog.
    refFile = cmds.fileDialog2(ds=1,fm=1,dir=cmds.workspace(q=1,dir=1))
    print refFile
    namesp = os.path.splitext(os.path.basename(refFile[0]))[0]
    returnFile = cmds.file(refFile[0],r=1,ns=namesp)
    refXforms = [f.split(':')[-1] for f in cmds.referenceQuery(returnFile,n=1) if cmds.objectType(f) == 'transform']
    refXforms = sorted(refXforms)
    cmds.file(returnFile,rr=1)
    # make dialog to choose controller.
    windowName = 'locs2RefsWindow'
    if cmds.window(windowName,q=1,exists=1) == True: cmds.deleteUI(windowName)
    window = cmds.window(windowName,title='choose a pivot transform',w=310,h=570)
    form = cmds.formLayout()
    scrollList = cmds.textScrollList(w=300,h=500,ams=0)
    okBtn = cmds.button(w=130,h=50,l='ok',c=lambda *x: applyRefs(returnFile,xforms,cmds.textScrollList(scrollList,q=1,si=1)[0],window))
    cancelBtn = cmds.button(w=130,h=50,l='cancel',c=lambda x: cmds.deleteUI(window))
    for x in refXforms:
        cmds.textScrollList(scrollList,e=1,a=x)
    cmds.formLayout(form,e=1,attachForm=[(scrollList,'top',5),(scrollList,'left',5),(okBtn,'top',510),(okBtn,'left',5),(cancelBtn,'top',510),(cancelBtn,'left',140)])
    cmds.showWindow(window)
    cmds.window(window,e=1,w=310,h=570)
    
def applyRefs(refFile,locs,control,window,*args):
    # make a ref file for each loc, then constraint the control to the loc.
    for loc in locs:
        namesp = os.path.splitext(os.path.basename(refFile))[0]
        ref = cmds.file(refFile,r=1,ns=namesp,shd='renderLayersByName')
        actualNamesp = cmds.file(ref,q=1,ns=1)
        refControl = actualNamesp+':'+control
        pc = cmds.parentConstraint(loc,refControl)
        cmds.delete(pc)
    cmds.deleteUI(window)
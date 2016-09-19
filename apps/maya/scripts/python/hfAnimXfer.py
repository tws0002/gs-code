# hfAnimXfer v0.23 by henry foster, henry@toadstorm.com 06/30/2011
#
# exports animation curves to files for import later.
# create a temp node, add attributes for each channel for object that's being copied.

import os
import maya.cmds as cmds
import maya.mel as mel
import natSort

def copyAnim(filename,objs,*args):
    #objs = cmds.ls(sl=1)
    # first: is there even anything here?
    if len(objs) < 1:
        return False
    # check for unknown nodes: this prevents ASCII conversion.
    unk = cmds.ls(type='unknown')
    if len(unk) > 0:
        cmds.error('You have unknown nodes in your scene. Run the cleanup utility before exporting animation.')
    if cmds.objExists('animXferTEMP'): cmds.delete('animXferTEMP')
    cmds.createNode('transform',n='animXferTEMP')
    for obj in objs:
        attrs = cmds.listAttr(obj,k=1)
        startTime = -100000
        endTime = 100000
        for attr in attrs:
            numkeys = cmds.keyframe(obj,q=1,at=attr,kc=1)
            if numkeys > 0:
                cmds.addAttr('animXferTEMP',at='double',longName=obj.replace(':','___')+'_ANIM_'+attr)
                cmds.copyKey(obj, t=(startTime,endTime), at=attr)
                cmds.pasteKey('animXferTEMP',option='replaceCompletely',at=obj.replace(':','___')+'_ANIM_'+attr)
    cmds.select('animXferTEMP')
    if filename.split('.')[-1] != '.ma':
        filename = filename + '.ma'
    f = cmds.file(filename,es=1,chn=1,type='mayaAscii',force=1)
    print 'wrote animation to file: %s' % (f)
    cmds.delete('animXferTEMP')
    
def pasteAnim(filename,namespace='',*args):
    errorsList = []
    # if namespace is given, replace everything before the '___' with the new string
    if cmds.objExists('animXferTEMP'): cmds.delete('animXferTEMP')
    try:
        cmds.file(filename,i=1)
        if not cmds.objExists('animXferTEMP'):
            # you fucked up
            cmds.error('animXferTEMP not found in imported file. aborting.')
    except RuntimeError:
        errString = 'Could not find file %s' % (filename)
        cmds.warning(errString)
        errorsList.append(errString)
        return errorsList
    # list all the attrs of the temp node. make a list of all channels that have 'ANIM' in them.
    attrs = [a for a in cmds.listAttr('animXferTEMP') if a.find('_ANIM_') != -1]
    startTime = -100000
    endTime = 100000
    for a in attrs:
        # parse each attr by splitting into namespace,obj and attr.
        # namespace___obj_ANIM_attr
        # dictionary: obj=channel
        # separate namespace first and replace with substitute namespace if given.
        ns = ''
        obj = ''
        if a.find('___') != -1:
            # namespace lives here
            if namespace != '':
                ns = namespace
            else:
                ns = a.split('___')[0]
            obj = a.split('___')[1].split('_ANIM_')[0]
        else:
            obj = a.split('_ANIM_')[0]
        chan = a.split('_ANIM_')[1]
        fullName = ''
        if ns != '':
            fullName = ns+':'+obj
        else:
            fullName = obj
        # print 'checking for keys on: %s.%s' % (fullName,chan)
        # print 'checking animXferTEMP.%s' % (a)
        # now copy keys from the given channel, and paste them to the object we build from fullName.chan
        numkeys = cmds.keyframe('animXferTEMP',q=1,at=a,t=(startTime,endTime),kc=1)
        # print 'found %d keys on this channel.' % (numkeys)
        if numkeys > 0:
            cmds.copyKey('animXferTEMP',t=(startTime,endTime),at=a)
            try:
                if cmds.getAttr(fullName+'.'+chan,lock=1) == 1:
                    cmds.setAttr(fullName+'.'+chan,lock=0)
                cmds.pasteKey(fullName,option='replaceCompletely',at=chan)
                print 'pasted %d keys to %s.%s' % (numkeys,fullName,chan)
            except:
                errorString = "Couldn't paste keys to %s.%s" % (fullName,chan)
                cmds.warning(errorString)
                errorsList.append(errorString)
        # DEBUG
        # confirm = cmds.confirmDialog(title='debug',message='finished iteration',button=['ok','stop'],cancelButton='stop',dismissString='stop')
        # if confirm=='stop': return
    if len(errorsList) > 0:
        return errorsList
    else:
        return True

def bakeKeys(objs,start,end,windowOff=1,smartBake=0,*args):
    # bake out all channels for selected objects.
    # first, switch to graph editor to speed up baking.
    if windowOff==1:
        mel.eval('setNamedPanelLayout "Single Perspective View"')
        perspPane = cmds.getPanel(vis=1)
        cmds.scriptedPanel('graphEditor1',e=1,rp=perspPane[0])
    # prevent file save after baking.
    cmds.file(rts=1)
    cmds.select(objs)
    start = float(start)
    end = float(end)
    cmds.bakeResults(simulation=1,smart=smartBake,cp=0,s=0,sb=1.0,t=(start,end))

def getControls(namespace,*args):
    # get all controls under a namespace.
    allCurves = cmds.ls(type='nurbsCurve')
    # we only want curves in our namespace, and with no overrides (it's selectable)
    controlCurveShapes = [c for c in allCurves if c.split(':')[0] == namespace and cmds.getAttr(c+'.overrideDisplayType') == 0]
    # now get the parent of each shape and return it if it's a transform
    controlCurveXforms = [cmds.listRelatives(x,p=1)[0] for x in controlCurveShapes if cmds.objectType(cmds.listRelatives(x,p=1)[0],isType='transform') == True]
    return controlCurveXforms

def getActiveNamespaces(*args):
    # return namespaces that have active references.
    # for all referenced files, get the namespace if the reference is not deferred (unloaded)
    namespaces = [cmds.file(f,q=1,namespace=1) for f in cmds.file(q=1,r=1) if not cmds.file(f,q=1,dr=1)]
    return namespaces

def massAnimExport(namespaces,s,e,includeCameras=0,windowOff=1,smartBake=0,*args):
    # for each namespace, select all control objects, bake channels, then export the animation.
    # first, get all the controls.
    allControls = []
    camXForms = []
    for n in namespaces:
        allControls.extend(getControls(n))
    # now bake that shit
    #s = cmds.playbackOptions(q=1,min=1)
    #e = cmds.playbackOptions(q=1,max=1)
    if includeCameras==1:
        # add cameras to allControls for purposes of baking.
        ignoreCams = ['perspShape','topShape','sideShape','frontShape']
        exportCams = [c for c in cmds.ls(type='camera') if cmds.getAttr(c+'.renderable') == 1 and c not in ignoreCams]
        for cam in exportCams:
            xforms = cmds.listRelatives(cam,p=1)
            newCam = cmds.duplicate(xforms[0],n=xforms[0]+'_BAKE')
            try: 
                cmds.parent(newCam[0],w=1)
            except RuntimeError:
                # the camera is probably already in world space.
                pass
            cmds.parentConstraint(xforms[0],newCam[0],mo=0)
            camXForms.append(newCam[0])
        allControls.extend(camXForms)
    bakeKeys(allControls,s,e,windowOff,smartBake)
    # again for cameras. never smart bake cameras.
    #if includeCameras==1:
    #    bakeKeys(camXForms,s,e,windowOff,0)
    # now we have to export these curves to files. this should be based on the scene name.
    dataPath = os.path.join(cmds.workspace(q=1,fn=1),'data','animExport',os.path.splitext(cmds.file(q=1,sn=1,shn=1))[0])
    if not os.path.exists(dataPath):
        os.makedirs(dataPath)
    # for each namespace, select the controls and run copyAnim.
    for n in namespaces:
        controls = getControls(n)
        copyAnim(os.path.join(dataPath,n),controls)
    if includeCameras==1:
        # don't copy the animation, but export the cameras to a subfolder.
        for cam in camXForms:
            path = os.path.join(dataPath,'CAMERAS')
            if not os.path.exists(path):
                os.makedirs(path)
            filename = os.path.join(dataPath,'CAMERAS',cam.replace(':','_'))+'.ma'
            cmds.select(cam)
            f = cmds.file(filename,es=1,chn=1,type='mayaAscii',force=1)
            print 'camera %s exported to: %s' % (cam,filename)
    cmds.warning('Animation data exported to: %s' % (dataPath))
    return dataPath

def massAnimImport(namespaces,folder,versionUI='',*args):
    # for each namespace, grab the matching file in folder and run pasteAnim.
    if versionUI != '':
        cmds.deleteUI(versionUI)
    pasteErrors = []
    for n in namespaces:
        impfile = os.path.join(folder,n)+'.ma'
        errors = pasteAnim(impfile,n)
        if errors != True:
            pasteErrors.extend(errors)
    if len(pasteErrors) > 0:
        print('\n-----ANIM IMPORT ERROR LOG-----')
        for e in pasteErrors:
            print(e)
        cmds.warning('Error importing animation data. See script editor for details.')
    else:
        mel.eval('print "Animation imported successfully!"')
    return folder
        
def importAnimUI(*args):
    # UI to list namespaces for import.
    windowName = 'hfImportAnimUI'
    windowTitle = 'ANIM IMPORT'
    if cmds.window(windowName,q=1,exists=1): cmds.deleteUI(windowName)
    window = cmds.window(windowName,title=windowTitle)
    form = cmds.formLayout()
    assetList = cmds.textScrollList(w=220,h=400,ams=1)
    assetLabel = cmds.text(l='select assets to import to:')
    selBtn = cmds.button(l='import selected',w=220,h=50, c=lambda x: animImportVersionUI(cmds.textScrollList(assetList,q=1,si=1),window))
    allBtn = cmds.button(l='import ALL',w=220,h=50, c=lambda x: animImportVersionUI(getActiveNamespaces(),window))
    cancelBtn = cmds.button(l='cancel',w=220,h=50,c=lambda x: cmds.deleteUI(window))
    cmds.formLayout(form,e=1,attachForm=[(assetLabel,'top',5),(assetLabel,'left',5),(assetList,'top',25),(assetList,'left',5),
        (selBtn,'top',475),(selBtn,'left',5),(cancelBtn,'top',585),(cancelBtn,'left',5),(allBtn,'top',530),(allBtn,'left',5)])
    # populate assetList
    nsList = getActiveNamespaces()
    for ns in nsList:
        cmds.textScrollList(assetList,e=1,a=ns)
    cmds.showWindow(window)
    cmds.window(window,e=1,w=230,h=645)

def animImportVersionUI(namespaces,importUI,*args):
    # used to pick what version to import from. passes namespaces arg from massAnimImportUI.
    # build a browser window listing all of the folders present in the data/animExport folder.
    cmds.deleteUI(importUI)
    windowName = 'hfImportAnimVersionUI'
    windowTitle = 'ANIM IMPORT VERSION'
    dataPath = os.path.join(cmds.workspace(q=1,fn=1),'data/animExport/')
    if cmds.window(windowName,q=1,exists=1): cmds.deleteUI(windowName)
    window = cmds.window(windowName,title=windowTitle)
    form = cmds.formLayout()
    folderListCtrl = cmds.textScrollList(w=400,h=400,ams=0)
    folderFilterLabel = cmds.text(l='filter:')
    folderFilterCtrl = cmds.textField(w=100,tx='',cc=lambda x: filterFolderList(cmds.textField(folderFilterCtrl,q=1,tx=1),folderListCtrl))
    goBtn = cmds.button(l='import',w=100,h=50,c=lambda x: massAnimImport(namespaces,os.path.join(dataPath,cmds.textScrollList(folderListCtrl,q=1,si=1)[0]),window))
    cancelBtn = cmds.button(l='cancel',w=100,h=50,c=lambda x: cmds.deleteUI(window))
    cmds.formLayout(form,e=1,attachForm=[(folderFilterLabel,'top',5),(folderFilterLabel,'left',5),(folderFilterCtrl,'top',3),(folderFilterCtrl,'left',50),
        (folderListCtrl,'top',30),(folderListCtrl,'left',5),(goBtn,'top',440),(goBtn,'left',5),(cancelBtn,'top',440),(cancelBtn,'left',120)])
    # stock folder list
    filterFolderList('',folderListCtrl)
    cmds.showWindow(window)
    cmds.window(window,e=1,w=410,h=500)

def filterFolderList(filter,control,*args):
    # print 'debug: filterFolderList using filter %s for control %s' % (filter,control)
    # for the import version UI. stocks the folder list based on the original filter.
    dataPath = os.path.join(cmds.workspace(q=1,fn=1),'data/animExport/')
    versionList = [f for f in os.listdir(dataPath) if os.path.isdir(os.path.join(dataPath,f))]
    # now match each of these versions against the filter.
    filteredList = versionList
    if filter != '':
        filteredList = [f for f in versionList if f.upper().find(filter.upper()) != -1]
    cmds.textScrollList(control,e=1,ra=1)
    filteredList = natSort.natsorted(filteredList)
    for f in filteredList:
        cmds.textScrollList(control,e=1,a=f)

def exportAnimUI(*args):
    # UI to list namespaces for animation export.
    windowName = 'hfExportAnimUI'
    windowTitle = 'ANIM EXPORT'
    if cmds.window(windowName,q=1,exists=1): cmds.deleteUI(windowName)
    window = cmds.window(windowName,title=windowTitle)
    form = cmds.formLayout()
    assetList = cmds.textScrollList(w=220,h=400,ams=1)
    assetLabel = cmds.text(l='select assets to export:')
    startLabel = cmds.text(l='start:')
    endLabel = cmds.text(l='end:')
    startCtrl = cmds.textField(w=60,tx=cmds.playbackOptions(q=1,min=1))
    endCtrl = cmds.textField(w=60,tx=cmds.playbackOptions(q=1,max=1))
    exportCamerasCtrl = cmds.checkBox(l='export renderable cameras?',v=0)
    selBtn = cmds.button(l='export selected',w=220,h=50, c=lambda x: massAnimExport(cmds.textScrollList(assetList,q=1,si=1),cmds.textField(startCtrl,q=1,tx=1),cmds.textField(endCtrl,q=1,tx=1),cmds.checkBox(exportCamerasCtrl,q=1,v=1)))
    allBtn = cmds.button(l='export ALL',w=220,h=50, c=lambda x: massAnimExport(getActiveNamespaces(),cmds.textField(startCtrl,q=1,tx=1),cmds.textField(endCtrl,q=1,tx=1),cmds.checkBox(exportCamerasCtrl,q=1,v=1)))
    cancelBtn = cmds.button(l='cancel',w=220,h=50,c=lambda x: cmds.deleteUI(window))
    cmds.formLayout(form,e=1,attachForm=[(assetLabel,'top',5),(assetLabel,'left',5),(assetList,'top',25),(assetList,'left',5),
        (selBtn,'top',495),(selBtn,'left',5),(cancelBtn,'top',605),(cancelBtn,'left',5),(allBtn,'top',550),(allBtn,'left',5),
        (startLabel,'top',440),(startLabel,'left',5),(endLabel,'top',440),(endLabel,'left',120),(startCtrl,'left',40),
        (startCtrl,'top',438),(endCtrl,'left',150),(endCtrl,'top',438),(exportCamerasCtrl,'left',5),(exportCamerasCtrl,'top',460)])
    # populate assetList
    nsList = getActiveNamespaces()
    for ns in nsList:
        cmds.textScrollList(assetList,e=1,a=ns)
    cmds.showWindow(window)
    cmds.window(window,e=1,w=230,h=665)
# toggleVraySubdiv.py v0.1 by renry
# interface to quickly add/remove vray subdivision options to meshes.

import maya.cmds as cmds
import maya.mel as mel
import natSort

def toggleVraySubdiv(objs,toggle,notSubList,subList,*args):
    retards = []
    for obj in objs:
        # does the object not have vray subdiv attributes? if not, run this command.
        if cmds.attributeQuery('vraySubdivEnable',exists=1,node=obj) == False:
            melCmd = 'vray addAttributesFromGroup '+obj+' vray_subdivision '+str(toggle)
            mel.eval(melCmd)
        try:
            cmds.setAttr(obj+'.vraySubdivEnable',toggle)
        except RuntimeError:
            # the attrs must have just been created on this guy, which means we don't really need to set them to anything since they're on by default.
            retards.append(obj)
    popSubdivLists(notSubList,subList,retards)
    
def popSubdivLists(notSubList,subList,retards,*args):
    subdivEnabledGeo = []
    notSubdivGeo = []
    geoList = [f for f in cmds.ls(type='mesh') if cmds.getAttr(f+'.intermediateObject') == 0]
    subdivGeo = [f for f in geoList if cmds.attributeQuery('vraySubdivEnable',exists=1,node=f) == True]
    subdivEnabledGeo = [f for f in subdivGeo if cmds.getAttr(f+'.vraySubdivEnable') == 1]
    notSubdivGeo = [f for f in geoList if f not in subdivEnabledGeo and f not in retards]
    subdivEnabledGeo = natSort.natsorted(subdivEnabledGeo)
    notSubdivGeo = natSort.natsorted(notSubdivGeo)
    subdivEnabledGeo.extend(retards)
    cmds.textScrollList(subList,e=1,ra=1)
    cmds.textScrollList(notSubList,e=1,ra=1)
    for i in subdivEnabledGeo:
        cmds.textScrollList(subList,e=1,a=i)
    for i in notSubdivGeo:
        cmds.textScrollList(notSubList,e=1,a=i)
    return notSubdivGeo,subdivEnabledGeo

def setSubdivAttr(obj,toggle,*args):
    # actually runs the setAttr recursively in case the attribute doesn't exist yet.
    try:
        cmds.setAttr(obj+'.vraySubdivEnable',toggle)
    except RuntimeError:
        setSubdivAttr(obj,toggle)
            
def vraySubdivUI():
    # lists polygon geo in two textScrollLists, based on whether or not the geo has subdiv properties or not.
    # if any poly geo is selected, highlight them automatically.
    sel = cmds.ls(sl=1)
    selMeshes = []
    for i in sel:
        shapes = cmds.listRelatives(i,s=1)
        # is the thing we selected actually a mesh itself?
        if cmds.objectType(i,isType='mesh'):
            selMeshes.append(i)
        else:
            try:
                for s in shapes:
                    # print 'DEBUG: checking out possible shape %s' % (s)
                    if cmds.objectType(s,isType='mesh'):
                        selMeshes.append(s)
            except TypeError:
                # this object either has no shape node, or is a shape node.
                # print 'object %s has no shape node?' % (i) 
                pass
    windowName = 'vraySubdivUI'
    windowTitle = 'Vray per-object subdivision'
    if cmds.window(windowName,q=1,exists=1): cmds.deleteUI(windowName)
    window = cmds.window(windowName,title=windowTitle)
    form = cmds.formLayout()
    notSubdivLabel = cmds.text(l='subdivide off',fn='boldLabelFont')
    subdivLabel = cmds.text(l='subdivide on',fn='boldLabelFont')
    notSubdivList = cmds.textScrollList(w=280,h=500,ams=1)
    subdivList = cmds.textScrollList(w=280,h=500,ams=1)
    subOnBtn = cmds.button(label='enable >>',w=280,h=50,c=lambda *x: toggleVraySubdiv(cmds.textScrollList(notSubdivList,q=1,si=1),1,notSubdivList,subdivList))
    subOffBtn = cmds.button(label='<< disable',w=280,h=50,c=lambda *x: toggleVraySubdiv(cmds.textScrollList(subdivList,q=1,si=1),0,notSubdivList,subdivList))
    cmds.formLayout(form,e=1,attachForm=[(notSubdivLabel,'top',5),(notSubdivLabel,'left',5),(subdivLabel,'top',5),(subdivLabel,'left',320),(notSubdivList,'top',20),(notSubdivList,'left',5),(subdivList,'top',20),(subdivList,'left',320),
                                         (subOnBtn,'top',530),(subOnBtn,'left',5),(subOffBtn,'top',530),(subOffBtn,'left',320)])
    # populate lists.
    retards = []
    notSubdiv,subdiv = popSubdivLists(notSubdivList,subdivList,retards)
    notSubdiv = [f for f in notSubdiv if f in selMeshes]
    subdiv = [f for f in subdiv if f in selMeshes]
    if len(selMeshes) > 0:
        cmds.textScrollList(notSubdivList,e=1,si=notSubdiv)
        cmds.textScrollList(subdivList,e=1,si=subdiv)
    cmds.showWindow(window)
    cmds.window(window,e=1,w=630,h=630)
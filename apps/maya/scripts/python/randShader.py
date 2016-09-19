import maya.cmds as cmds
import random

def randShader():
    # for selected objects, choose from a list of shaders to apply, then randomly apply shaders.
    windowName = 'randShaderUI'
    if cmds.window(windowName,q=1,exists=1): cmds.deleteUI(windowName)
    window = cmds.window(windowName,t='select materials')
    form = cmds.formLayout()
    scrollList = cmds.textScrollList(w=300,h=400,ams=1)
    matsList = [cmds.listConnections(f+'.surfaceShader',s=1,d=0) for f in cmds.ls(type='shadingEngine') if f != 'initialShadingGroup']
    matsList = sorted(matsList)
    for m in matsList:
        cmds.textScrollList(scrollList,e=1,a=m)
    okBtn = cmds.button(w=100,h=50,l='go',c=lambda *x: applyRandShaders(cmds.ls(sl=1),cmds.textScrollList(scrollList,q=1,si=1)))
    cancelBtn = cmds.button(w=100,h=50,l='cancel',c=lambda x: cmds.deleteUI(window))
    cmds.formLayout(form,e=1,attachForm=[(scrollList,'top',5),(scrollList,'left',5),(okBtn,'top',410),(okBtn,'left',5),(cancelBtn,'top',410),(cancelBtn,'left',115)])
    cmds.showWindow(window)
    cmds.window(window,e=1,w=310,h=510)
    
def applyRandShaders(objs,mats,*args):
    for obj in objs:
        rand = random.randint(0,len(mats)-1)
        randMat = mats[rand]
        cmds.select(obj,r=1)
        try:
            cmds.hyperShade(a=randMat)
        except:
            pass
    cmds.select(objs)

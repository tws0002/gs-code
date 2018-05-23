import maya.cmds as cmds
import maya.mel as mel
import json

lightAovs={"rsAov_DiffuseFilter":"Diffuse Filter",
            "rsAov_DiffuseLighting":"Diffuse Lighting",
            "rsAov_GlobalIlluminationRaw":"Global Illumination Raw",
            "rsAov_GlobalIllumination":"Global Illumination",
            "rsAov_Reflections":"Reflections",
            "rsAov_Refractions":"Refractions",
            "rsAov_SpecularLighting":"Specular Lighting",
            "rsAov_SubSurfaceScatterRaw":"Sub Surface Scatter Raw",
            "rsAov_SubSurfaceScatter":"Sub Surface Scatter",
            "rsAov_TotalDiffuseLightingRaw":"Total Diffuse Lighting Raw",
            "rsAov_Emission":"Emission"}
utilAovs={"rsAov_AmbientOcclusion":"Ambient Occlusion",
            "rsAov_BumpNormals":"Bump Normals",
            "rsAov_Depth":"Depth",
            "rsAov_MotionVectors":"Motion Vectors",
            "rsAov_WorldPosition":"World Position",
            "rsAov_Normals":"Normals"}
matteAovs={"rsAov_ObjectID":"ObjectID"}

def generateIDs(item,attr,dict,renderLayer):
    hsh= abs(hash(item)) % (10 ** 7)
    while hsh in dict.keys():
        hsh+=1
    if hsh in dict.keys():
        print 'FOUND:',hsh,item
    if attr in cmds.listAttr(item):
        #cmds.editRenderLayerAdjustment(item+'.'+attr, layer=renderLayer)#add layer overide
        cmds.setAttr(item+'.'+attr,int(hsh))
    if not hsh in dict.keys():
        dict[hsh]=item
    return dict,hsh


def setupOverides():
    #### Select renderLayer with geo, will create Matte layer.
    beautyRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
    currentRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
    matteLayer=currentRenderLayer.replace("Beauty","Matte")

    #create Matte layer
    if not cmds.objExists(matteLayer):
        cmds.createRenderLayer(n=matteLayer,nr=1)

    #add geo
    contents= cmds.editRenderLayerMembers(currentRenderLayer,q=1,fn=1)  
    if contents:
        for obj in contents:
            try:
                cmds.editRenderLayerMembers(matteLayer,obj,nr=1) 
            except:
                pass
    cmds.editRenderLayerGlobals(currentRenderLayer=matteLayer)
    currentRenderLayer=matteLayer

    #ADD existing visbility overides from object properties
    #get settings from any existing layer ObjectProperties, to copy to matte settings
    existingVis=[]
    layerAdj=cmds.editRenderLayerAdjustment(currentRenderLayer, query=True, layer=True )
    if layerAdj:
        for adj in layerAdj:
            try:
                node,attr=adj.split('.')
                if node:
                    if cmds.nodeType(node)=='RedshiftVisibility':
                        existingVis.append([adj,cmds.getAttr(adj)])
            except:
                pass


    #TURN OFF LIGHTS, make optimizations
    for light in cmds.ls(type='RedshiftPhysicalLight'):
        cmds.editRenderLayerAdjustment(light+'.on', layer=currentRenderLayer)
        cmds.setAttr(light+'.on',0)

    turnOff=[   "redshiftOptions.primaryGIEngine",
                "redshiftOptions.secondaryGIEngine",
                "redshiftOptions.emissionEnable",
                "redshiftOptions.subsurfaceScatteringEnable",
                "redshiftOptions.refractionRaysEnable",
                "redshiftOptions.reflectionRaysEnable",
                "defaultRenderGlobals.enableDefaultLight" ]
    for to in turnOff:
        cmds.editRenderLayerAdjustment(to, layer=currentRenderLayer)
        cmds.setAttr(to,0)  

    #assume ulityMatteLayerOveride exists from setupRenderElements.py script
    #cmds.editRenderLayerAdjustment("utilityMatteLayerOveride.matteEnable", layer=currentRenderLayer)
    #cmds.setAttr("utilityMatteLayerOveride.matteEnable",1)
    #get list of all aovs, turn off all
    existingAovs=cmds.ls(type='RedshiftAOV')
    for aov in existingAovs:
        cmds.editRenderLayerAdjustment(aov+".enabled", layer=currentRenderLayer)
        cmds.setAttr(aov+".enabled",0) 

    #turn on matte only
    for aov in matteAovs.keys():
        if aov in existingAovs:
            cmds.setAttr(aov+".enabled",1) 

    #set layer overide renderSettings, turn off GI, resolution, filtering, lights,turn on Deep
    cmds.editRenderLayerAdjustment("redshiftOptions.aovEnableDeepOutput", layer=currentRenderLayer)
    cmds.editRenderLayerAdjustment("redshiftOptions.aovDeepMergeMode", layer=currentRenderLayer)
    cmds.editRenderLayerAdjustment("redshiftOptions.exrForceMultilayer", layer=currentRenderLayer)
    cmds.editRenderLayerAdjustment("redshiftOptions.exrMultipart", layer=currentRenderLayer)
    cmds.editRenderLayerAdjustment("defaultRenderGlobals.enableDefaultLight",layer=currentRenderLayer)
    cmds.editRenderLayerAdjustment("redshiftOptions.unifiedMaxSamples",layer=currentRenderLayer)#force antialiasing edges for mattes
    cmds.editRenderLayerAdjustment("redshiftOptions.unifiedMinSamples",layer=currentRenderLayer)
    cmds.setAttr("redshiftOptions.aovEnableDeepOutput",1)
    cmds.setAttr("redshiftOptions.aovDeepMergeMode",1)
    cmds.setAttr("redshiftOptions.exrForceMultilayer",0)
    cmds.setAttr("redshiftOptions.exrMultipart",0)
    cmds.setAttr("redshiftOptions.unifiedMaxSamples",32)
    cmds.setAttr("redshiftOptions.unifiedMinSamples",32)
    cmds.setAttr("defaultRenderGlobals.enableDefaultLight",1)

    existingAovs=cmds.ls(type='RedshiftAOV')
    if not 'rsAov_ObjectID' in existingAovs:
        aov=mel.eval("redshiftCreateAov(\"ObjectID\")")
        cmds.setAttr(aov+".enabled",1)
        cmds.setAttr(aov+".filePrefix","<BeautyPath>/<RenderPass>/<BeautyFile>.<RenderPass>",type="string")
        cmds.setAttr(aov+".exrCompression", 4)
    try:
        mel.eval("redshiftUpdateActiveAovList")  
    except:
        print 'Aov Window not found'

def setupIDs():
    currentRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
    #apply IDs      
    objIDs={}
    sceneData={'asset':{},'material':{},'object':{}}
    for sh in cmds.ls(g=1):
        try:
            shadingGrps= cmds.listConnections(sh,type='shadingEngine')
            if shadingGrps:
                shader = cmds.ls(cmds.listConnections(shadingGrps),materials=1)[0]
                objIDs,id=generateIDs(sh,'rsObjectId',objIDs,currentRenderLayer)
        except:
            print sh,' error'


def writeSceneData():
    sceneDataPath=cmds.fileDialog2(dialogStyle=2,fm=0)[0]     
    sceneData={'asset':{},'material':{},'object':{}}
    for sh in cmds.ls(g=1):
        shadingGrps= cmds.listConnections(sh,type='shadingEngine')
        if shadingGrps:
            shader = cmds.ls(cmds.listConnections(shadingGrps),materials=1)[0]
            asset=sh.split(':')[0]
            id= abs(hash(sh)) % (10 ** 7)
            if not asset in sceneData['asset'].keys():
                sceneData['asset'][asset]=[]
            sceneData['asset'][asset].append(id)
            if not shader in sceneData['material'].keys():
                sceneData['material'][shader]=[]
            sceneData['material'][shader].append(id)
            sceneData['object'][id]=sh
    with open(sceneDataPath, 'w') as fp:
        json.dump(sceneData, fp)

def main():
    #get selected renderLayer
    currentRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
    if not "_Beauty" in currentRenderLayer:
        cmds.confirmDialog(m="_\"Beauty\" not found in renderlayer")
    else:
        setupOverides()
        setupIDs()
        #writeSceneData()

'''
import sys
sys.path.append('C:/Users/mlavoy/Documents/mlTools/maya/automatte')

import maya_setupMatteLayerRS
reload(maya_setupMatteLayerRS)
maya_setupMatteLayerRS.main()
'''
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


def setupIDs():
    currentRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
    #apply IDs      
    objIDs={}
    sceneData={'asset':{},'material':{},'object':{}}
    for sh in cmds.ls(g=1):
        shadingGrps= cmds.listConnections(sh,type='shadingEngine')
        if shadingGrps:
            shader = cmds.ls(cmds.listConnections(shadingGrps),materials=1)[0]
            objIDs,id=generateIDs(sh,'rsObjectId',objIDs,currentRenderLayer)

def main():
    #get selected renderLayer
    currentRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
    if not "_Beauty" in currentRenderLayer:
        cmds.confirmDialog(m="_\"Beauty\" not found in renderlayer")
    else:
        setupIDs()

'''
import sys
sys.path.append('C:/Users/mlavoy/Documents/mlTools/maya/automatte')

import maya_setupMatteLayerRS
reload(maya_setupMatteLayerRS)
maya_setupMatteLayerRS.main()
'''
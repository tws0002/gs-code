


import maya.cmds as cmds
import maya.mel as mel
import os
#find Id file in work/maya/data folder
filepath=cmds.file(sn=1,q=1)

#data=filepath.split("scenes")[0]+"data"
data='//scholar/projects/dairy_farmers_canada/03_production/01_cg/01_MAYA/scenes/work.lavoy'
objectIDfile=data+'/objectIDs.txt'
matIDfile=data+'/materialIDs.txt'

def loadIdsFromFile(contents):
    lines=contents.split("\n")
    idDict={}
    for line in lines:
        if line:
            id,node=line.split("=")
            node=node.strip("\r")
            idDict[id]=node
    return idDict

def getIDsDict():
    if not os.path.exists(objectIDfile):
        fileObject=open(objectIDfile,"w")
        fileObject.close()
    fileObject=open(objectIDfile,"r")
    contents=fileObject.read()
    fileObject.close()
    objIDs=loadIdsFromFile(contents)

    #if not os.path.exists(matIDfile):
    #    fileObject=open(matIDfile,"w")
    #    fileObject.close()
    #fileObject=open(matIDfile,"r")
    #contents=fileObject.read()
    #fileObject.close()
    #matIDs=loadIdsFromFile(contents)
    return objIDs

def writeIDs(filepath,dict):

    contents=''
    keys=dict.keys()
    keys.sort()
    for k in keys:
        contents+=k.zfill(6)+"="+dict[k]+"\n"
    fileObject=open(filepath,"w")
    fileObject.write(contents)
    fileObject.close()


def getAssignedMaterials():
    assignedMats=[]
    #if not default materials
    for sg in cmds.ls(type="shadingEngine"):
        if not "initial" in sg:
            #if shader group is assigned to geo
            if [x for x in cmds.listConnections(sg) if "transform" in cmds.nodeType(x)]:
                print sg
                nodes=[sg]
                for n in nodes:
                    srcConnections=cmds.listConnections(n,s=1,d=0)
                    if srcConnections:
                        for i in srcConnections:
                            if "VRay" in cmds.nodeType(i):
                                nodes.append(i)
                print nodes
                assignedMats.extend(nodes)
    return assignedMats

def getRenderedShapes():
    shapes=[]
    sel=cmds.ls(type='shadingEngine')
    for s in sel:
        connected=cmds.sets(s,q=1)
        if connected:
            shapes.extend(connected)

    shadedShapes=[]  
    selection=cmds.ls(sl=1)
    for sel in selection:
        for shape in cmds.listRelatives(sel,type='shape'):
            if shape in shapes:
                shadedShapes.append(shape)
    return shadedShapes

def main():
    filepath=cmds.file(sn=1,q=1)#get scholar asset name
    asset=filepath.split('/01_models/')[1].split('/')[0]#get scholar asset name
    objIDs=getIDsDict()

    existingObjects={}
    for k in objIDs.keys():
        existingObjects[objIDs[k]]=k
    geo=getRenderedShapes()
    index=0
    for g in geo:
        g_namespaced=asset+":"+g
        #if not "vrayObjectID" in cmds.listAttr(g):
        #    mel.eval("vrayAddAttr "+g+" vrayObjectID")
        while str(index).zfill(6) in objIDs.keys():
            index+=1
        if g_namespaced in existingObjects.keys():
            cmds.setAttr(g+".rsObjectId",int(existingObjects[g_namespaced]))
            print index,g,"set"
        else:
            cmds.setAttr(g+".rsObjectId",index)
            print index,g
            objIDs[str(index).zfill(6)]=g_namespaced
    writeIDs(objectIDfile,objIDs)
    '''
    existingMats=[]
    for k in matIDs.keys():
        existingMats.append(matIDs[k])
    assignedSGs=[]
    #get assignedSG from all shapes in scene
    shadingGrps = cmds.listConnections(geo,type='shadingEngine')
    #remove duplicates
    shadingGrps = list(set(shadingGrps))

    index=0
    for sh in shadingGrps:
        shade=cmds.listConnections(sh+".surfaceShader")[0]
        if not "vrayMaterialId" in cmds.listAttr(shade):
            mel.eval("vrayAddAttr "+shade+" vraySeparator_vray_material_id")
            mel.eval("vrayAddAttr "+shade+" vrayColorId")
            mel.eval("vrayAddAttr "+shade+" vrayMaterialId")
           
        while str(index).zfill(6) in matIDs.keys():
            index+=1
        if not shade in existingMats:
            cmds.setAttr(shade+".vrayColorId",float(index),float(index),float(index),type="double3")
            print index,shade
            matIDs[str(index).zfill(6)]=shade
    writeIDs(matIDfile,matIDs)
    
    custAttrib=''
    for id in objIDs.keys():
        custAttrib+="obj"+id+"="+objIDs[id].replace("Shape","")+";\n"
    for id in matIDs.keys():
        custAttrib+="mat"+id+"="+matIDs[id].replace("Shape","")+";\n"

    cmds.setAttr("vraySettings.imgOpt_exr_attributes",custAttrib,type="string")
    '''
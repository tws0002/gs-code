lightAovs={ "rsAov_DiffuseFilter":"Diffuse Filter",
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
utilAovs={  "rsAov_AmbientOcclusion":"Ambient Occlusion",
            "rsAov_BumpNormals":"Bump Normals",
            "rsAov_Depth":"Depth",
            "rsAov_MotionVectors":"Motion Vectors",
            "rsAov_WorldPosition":"World Position",
            "rsAov_WorldPosition_filter":"World Position",
            "rsAov_Normals":"Normals"}
matteAovs={  "rsAov_ObjectID":"ObjectID"}

def main():
    import maya.cmds as cmds
    import maya.mel as mel
    #### Select renderLayer with geo, will create lighting passes and utility layer.

    #get selected renderLayer
    beautyRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
    currentRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
    
    #get settings from any existing layer ObjectProperties, to copy to utility settings
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


    if not "_Beauty" in currentRenderLayer:
        cmds.confirmDialog(m="_\"Beauty\" not found in renderlayer")
    else:
        utilityLayer=currentRenderLayer.replace("Beauty","PuzzleMatte")

        #create Utility layer
        if not cmds.objExists(utilityLayer):
            cmds.createRenderLayer(n=utilityLayer,nr=1)

        #add geo
        print "adding geo to",utilityLayer
        contents= cmds.editRenderLayerMembers(currentRenderLayer,q=1,fn=1)  
        if contents:
            for obj in contents:
                if cmds.objExists(obj):
                    cmds.editRenderLayerMembers(utilityLayer,obj,nr=1) 
        cmds.editRenderLayerGlobals(currentRenderLayer=utilityLayer)
        currentRenderLayer=utilityLayer

        #add layer ObjectProperties
        for vis in existingVis:
            attr,val=vis
            cmds.editRenderLayerAdjustment(attr, layer=currentRenderLayer)
            cmds.setAttr(attr,val)

        #TURN OFF LIGHTS, make optimizations
        sceneLights=[]
        sceneLights.extend(cmds.ls(type='RedshiftPhysicalLight'))
        sceneLights.extend(cmds.ls(type='RedshiftPhysicalSun'))
        sceneLights.extend(cmds.ls(type='RedshiftDomeLight'))
        sceneLights.extend(cmds.ls(type='RedshiftPortalLight'))
        sceneLights.extend(cmds.ls(type='RedshiftIESLight'))
        for light in sceneLights:
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


        '''
        #CREATE mattes based on asset data found in shape nodes
        matteData={}
        mats=cmds.ls(type='shadingEngine')
        for mat in mats:
            if 'matteLayer' in cmds.listAttr(mat):
                matteLayer=cmds.getAttr(mat+".matteLayer")
                if matteLayer:
                    layer,color,name=matteLayer.split(".")
                    id=cmds.getAttr(mat+".rsMaterialId")
                    if not layer in matteData.keys():
                        matteData[layer]={'red':'','green':'','blue':''}
                    matteData[layer][color]=id

        existingAovs=cmds.ls(type='RedshiftAOV')
        for layer in matteData.keys():
            aovMatteName='rsAov_'+layer
            if not aovMatteName in existingAovs:
                aov=mel.eval("redshiftCreateAov(\"Puzzle Matte\")")
                cmds.setAttr(aov+".name",layer,type="string")
                cmds.setAttr(aov+".enabled",0)
                cmds.setAttr(aov+".filePrefix","<BeautyPath>/<RenderPass>/<BeautyFile>.<RenderPass>",type="string")
                cmds.setAttr(aov+".exrCompression", 4)
                cmds.rename(aov,aovMatteName)
            if matteData[layer]['red']:
                cmds.setAttr(aovMatteName+'.redId',matteData[layer]['red'])
            if matteData[layer]['green']:
                cmds.setAttr(aovMatteName+'.greenId',matteData[layer]['green'])
            if matteData[layer]['blue']:
                cmds.setAttr(aovMatteName+'.blueId',matteData[layer]['blue'])
        '''
        try:
            mel.eval("redshiftUpdateActiveAovList")
        except:
            pass

        #DETERMINE WHICH MATTES ARE USED IN CURRENT LAYER
        layerMembers=[]
        for mem in cmds.editRenderLayerMembers(beautyRenderLayer,q=1,fn=1):
            mem=mem.split('|')[1]
            if not mem in layerMembers:
                layerMembers.append(mem)

        #get list of all aovs, turn off all
        existingAovs=cmds.ls(type='RedshiftAOV')
        for aov in existingAovs:
            cmds.editRenderLayerAdjustment(aov+".enabled", layer=currentRenderLayer)
            cmds.setAttr(aov+".enabled",0) 

        #get all existing puzzleIDs
        existingAovs=cmds.ls(type='RedshiftAOV')
        existingMaterialIDs=[]
        #add all aovs
        for aov in existingAovs:
            if 'Puzzle' in aov:
                for m in ['redId','greenId','blueId']:
                    idVal=cmds.getAttr(aov+'.'+m)
                    if idVal:
                        existingMaterialIDs.append(idVal)

        #create dict of ids and referenceAssets              
        objects={}
        for sh in cmds.ls(type='mesh'):
            shadingGrps= cmds.listConnections(sh,type='shadingEngine')
            if shadingGrps:
                shGrpName=shadingGrps[0]
                ref=shGrpName.split(':')[0]
                if 'prop' in ref or 'char' in ref or 'plant' in ref:
                    id=abs(hash(ref)) % (10 ** 7)
                    cmds.setAttr(shGrpName+'.rsMaterialId',id)
                    if not ref in objects.keys():
                        objects[id]=ref
                else:
                    id=abs(hash(shGrpName)) % (10 ** 7)
                    cmds.setAttr(shGrpName+'.rsMaterialId',id)
                    if not shGrpName in objects.keys():
                        objects[id]=shGrpName
                        
        count=0
        for id in objects.keys():
            if not id in existingMaterialIDs:
                if count==0:
                    aov=mel.eval("redshiftCreateAov(\"Puzzle Matte\")")
                    cmds.setAttr(aov+'.exrCompression',4)
                    cmds.setAttr(aov+'.redId',id)
                if count==1:
                    cmds.setAttr(aov+'.greenId',id)
                if count==2:
                    cmds.setAttr(aov+'.blueId',id)
                count+=1
                if count==3:
                    count=0        
        mel.eval("redshiftUpdateActiveAovList") 


        #turn on Puzzle only
        existingAovs=cmds.ls(type='RedshiftAOV')
        for aov in existingAovs:
            if 'Puzzle' in aov:
                cmds.setAttr(aov+".enabled",1) 
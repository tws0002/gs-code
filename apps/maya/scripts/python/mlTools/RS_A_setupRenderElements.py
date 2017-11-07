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
            "rsAov_Normals":"Normals",
            "rsAov_ObjectID":"ObjectID"}
matteAovs={  "rsAov_ObjectID":"ObjectID"}

def main():
    import maya.cmds as cmds
    import maya.mel as mel
    #### Select renderLayer with geo, will create lighting passes and utility layer.
    #FORCE FILEPATH OUT
    filepath=cmds.file(sn=1,q=1)
    shotname=filepath.split('/lighting')[0].split('/')[-1]
    outpath=shotname+'/<Layer>/<Scene>/<Scene>_<Layer>'
    #cmds.setAttr('defaultRenderGlobals.imageFilePrefix',l=0)
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix',outpath,type="string")
    #cmds.setAttr('defaultRenderGlobals.imageFilePrefix',l=1)

    #SET FILE SETTINGS
    cmds.setAttr("redshiftOptions.exrCompression", 4)#zip1
    cmds.setAttr("redshiftOptions.exrForceMultilayer",1)#split aovs
    cmds.setAttr("redshiftOptions.aovGlobalEnableMode",1)
    cmds.setAttr("redshiftOptions.exrMultipart",1)

    #get selected renderLayer
    currentRenderLayer=cmds.editRenderLayerGlobals(q=1, crl=1) 
    
    if not "_Beauty" in currentRenderLayer:
        cmds.confirmDialog(m="_\"Beauty\" not found in renderlayer name")
    else:
        #CREATE AOVS
        existingAovs=cmds.ls(type='RedshiftAOV')
        #add all aovs
        for lightAov in lightAovs.keys():
            if not lightAov in existingAovs:
                mel.eval("redshiftCreateAov(\""+lightAovs[lightAov]+"\")")
        for utilAov in utilAovs.keys():
            if not utilAov in existingAovs:
                aov=mel.eval("redshiftCreateAov(\""+utilAovs[utilAov]+"\")")
                if utilAov=='rsAov_WorldPosition_filter':
                    cmds.setAttr(aov+'.name',"P_filter",type="string")
                cmds.rename(aov,utilAov)
        mel.eval("redshiftUpdateActiveAovList")  

        #get list of all aovs, turn off all, force settings
        existingAovs=cmds.ls(type='RedshiftAOV')
        for aov in existingAovs:
            cmds.setAttr(aov+".enabled",0)
            #setPath and exr
            cmds.setAttr(aov+".filePrefix","<BeautyPath>/<RenderPass>/<BeautyFile>.<RenderPass>",type="string")
            cmds.setAttr(aov+".exrCompression", 4)
            cmds.editRenderLayerAdjustment(aov+".enabled", layer=currentRenderLayer)
            cmds.setAttr(aov+".enabled",0) 
            #set worldP to center
            if aov == 'rsAov_WorldPosition' or aov == 'rsAov_Depth':
                cmds.setAttr(aov+".filterMode", 3)
            if aov == 'rsAov_MotionVectors':
                cmds.setAttr(aov+'.outputRawVectors',1)
                cmds.setAttr(aov+'.filtering',0)
        #turn on lighting aovs only
        for aov in lightAovs.keys():
            if aov in existingAovs:
                cmds.setAttr(aov+".enabled",1) 
        #ADD matte properties to be used for additional render layers
        #get root nodes to plug into matte parameters
        parents=[]
        for s in cmds.ls(g=1):
            par = cmds.ls(s, long=True)[0].split('|')[1]
            if not par in parents:
                parents.append(par)
        if not cmds.objExists('utilityMatteLayerOveride'):
            rsMatteOveride=cmds.createNode("RedshiftMatteParameters",n="utilityMatteLayerOveride")
            cmds.sets(parents,edit=1,forceElement=rsMatteOveride)
        #set and turn off overide for lighting
        cmds.setAttr("utilityMatteLayerOveride.matteShowBackground",0)
        cmds.setAttr("utilityMatteLayerOveride.matteEnable",0)

        #set layerOverides on lights and opts
        sceneLights=[]
        sceneLights.extend(cmds.ls(type='RedshiftPhysicalLight'))
        sceneLights.extend(cmds.ls(type='RedshiftPhysicalSun'))
        sceneLights.extend(cmds.ls(type='RedshiftDomeLight'))
        sceneLights.extend(cmds.ls(type='RedshiftPortalLight'))
        sceneLights.extend(cmds.ls(type='RedshiftIESLight'))
        for light in sceneLights:
            cmds.editRenderLayerAdjustment(light+'.on', layer=currentRenderLayer)

        opts=[   "redshiftOptions.primaryGIEngine",
                    "redshiftOptions.secondaryGIEngine",
                    "redshiftOptions.emissionEnable",
                    "redshiftOptions.subsurfaceScatteringEnable",
                    "redshiftOptions.refractionRaysEnable",
                    "redshiftOptions.reflectionRaysEnable"]
        for to in opts:
            cmds.editRenderLayerAdjustment(to, layer=currentRenderLayer)
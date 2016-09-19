# render layer assistant script
#
# quickly create passes and typical overrides for render layer setups.
# render layer types: beauty, tech
# beauty passes: diffuse, lighting, reflect, refract, SSS, GI, selfIllum, specular, caustics, shadow, lightSelect(s)
# tech passes: AO, UV, fresnel, Z (aliased/antialiased), velocity, normals, bumpnormals
# typical render overrides: lights OFF, GI OFF, glossy effects OFF, env override OFF
# beauty: all ON (no GI if no GI buffer created)
#
# vrayAddRenderElement <elemName>

import maya.cmds as cmds
import maya.mel as mel

def parseElementNames(i,*args):
    # each vray pass has a unique name. this is a sort of dictionary function to return the vray command needed to generate each pass.
    elemDict = { 'diffuse':'diffuseChannel',
                 'reflection':'reflectChannel',
                 'refraction':'refractChannel',
                 'self-illumination':'selfIllumChannel',
                 'shadow':'shadowChannel',
                 'specular':'specularChannel',
                 'lighting':'lightingChannel',
                 'GI':'giChannel',
                 'caustics':'causticsChannel',
                 'SSS':'FastSSS2Channel',
                 'normals':'normalsChannel',
                 'bump normals':'bumpNormalsChannel',
                 'z-depth':'zdepthChannel',
                 'velocity':'velocityChannel',
                 'AO':'ExtraTexElement',
                 'UV':'ExtraTexElement',
                 'fresnel':'ExtraTexElement',
                 'pointWorld':'ExtraTexElement',
                 'rawShadow':'rawShadowChannel'
               }
    if elemDict[i]:
        return elemDict[i]
    else:
        return False


def defineBeautyLayer(layerName,passes,globalOverrides=1,*args):
    # GIven a layer name and an array of passes, create the passes and enable them as an override on that layer.
    # also enable lights, GI, etc if necessary
    passList = []
    cmds.editRenderLayerGlobals(crl='defaultRenderLayer')
    # global overrides
    if globalOverrides:
        cmds.setAttr('vraySettings.globopt_light_doLights',0)
        cmds.setAttr('vraySettings.globopt_mtl_glossy',0)
        cmds.setAttr('vraySettings.cam_overrideEnvtex',0)
        cmds.setAttr('vraySettings.giOn',0)
    for p in passes:
        # check for duplicate
        elements = [cmds.getAttr(f+'.vrayClassType') for f in cmds.ls(type='VRayRenderElement')]
        extraTexes = [f for f in cmds.ls(type='VRayRenderElement') if cmds.getAttr(f+'.vrayClassType') == 'ExtraTexElement']
        extraTexNames = [cmds.getAttr(f+'.vray_name_extratex') for f in extraTexes]
        if (parseElementNames(p) not in elements) or (parseElementNames(p) == 'ExtraTexElement' and p not in extraTexNames):
            melCmd = 'vrayAddRenderElement '+parseElementNames(p)
            mel.eval(melCmd)
            # get new pass by loading selection
            newPass = cmds.ls(sl=1)[0]
            passList.append(newPass)
            cmds.setAttr(newPass+'.enabled',0)
    # now go through passList and make an override for the beauty layer.
    cmds.editRenderLayerGlobals(crl=layerName)
    cmds.editRenderLayerGlobals(eaa=1)
    for p in passList:
        cmds.editRenderLayerAdjustment(p+'.enabled')
        cmds.setAttr(p+'.enabled',1)
    # global overrides
    if globalOverrides:
        cmds.editRenderLayerAdjustment('vraySettings.globopt_light_doLights')
        cmds.editRenderLayerAdjustment('vraySettings.globopt_mtl_glossy')
        cmds.editRenderLayerAdjustment('vraySettings.cam_overrideEnvtex')
        cmds.setAttr('vraySettings.globopt_light_doLights',1)
        cmds.setAttr('vraySettings.globopt_mtl_glossy',1)
        cmds.setAttr('vraySettings.cam_overrideEnvtex',1)
        if 'GI' in passes:
            cmds.editRenderLayerAdjustment('vraySettings.giOn')
            cmds.setAttr('vraySettings.giOn',1)
    # done.
    print '\nBeauty layer settings applied to layer %s.' % (layerName)

def defineTechLayer(layerName,passes,globalOverrides=1,*args):
    # same thing as tech layer, but don't worry about overrides (you won't need them) and instead worry about
    # creating textures as needed for AO,GI,UV
    passList = []
    cmds.editRenderLayerGlobals(crl='defaultRenderLayer')
    if globalOverrides:
        cmds.setAttr('vraySettings.globopt_light_doLights',0)
        cmds.setAttr('vraySettings.globopt_mtl_glossy',0)
        cmds.setAttr('vraySettings.cam_overrideEnvtex',0)
        cmds.setAttr('vraySettings.giOn',0)
    for p in passes:
        elements = [cmds.getAttr(f+'.vrayClassType') for f in cmds.ls(type='VRayRenderElement')]
        extraTexes = [f for f in cmds.ls(type='VRayRenderElement') if cmds.getAttr(f+'.vrayClassType') == 'ExtraTexElement']
        extraTexNames = [cmds.getAttr(f+'.vray_name_extratex') for f in extraTexes]
        if (parseElementNames(p) not in elements) or (parseElementNames(p) == 'ExtraTexElement' and p not in extraTexNames):
            melCmd = 'vrayAddRenderElement '+parseElementNames(p)
            mel.eval(melCmd)
            newPass = cmds.ls(sl=1)[0]
            # exceptions for ExtraTex elements AO, UV or fresnel
            if p=='AO':
                aoTex = cmds.shadingNode('VRayDirt',at=1)
                # set better sampling for default
                cmds.setAttr(aoTex+'.subdivs',24)
                cmds.connectAttr(aoTex+'.outColor',newPass+'.vray_texture_extratex',f=1)
                cmds.setAttr(newPass+'.vray_name_extratex','AO',type='string')
                newPass = cmds.rename(newPass,'vrayRE_AO')
            elif p=='UV':
                uvTex = cmds.shadingNode('place2dTexture',au=1)
                cmds.connectAttr(uvTex+'.outUV.outU',newPass+'.vray_texture_extratex.vray_texture_extratexR',f=1)
                cmds.connectAttr(uvTex+'.outUV.outV',newPass+'.vray_texture_extratex.vray_texture_extratexG',f=1)
                cmds.setAttr(newPass+'.vray_name_extratex','UV',type='string')
                newPass = cmds.rename(newPass,'vrayRE_UV')
            elif p=='fresnel':
                fTex = cmds.shadingNode('VRayFresnel',at=1)
                cmds.connectAttr(fTex+'.outColor',newPass+'.vray_texture_extratex',f=1)
                cmds.setAttr(newPass+'.vray_name_extratex','fresnel',type='string')
                newPass = cmds.rename(newPass,'vrayRE_Fresnel')
            elif p=='pointWorld':
                pwTex = cmds.shadingNode('samplerInfo',au=1)
                cmds.connectAttr(pwTex+'.pointWorld',newPass+'.vray_texture_extratex',f=1)
                cmds.setAttr(newPass+'.vray_name_extratex','pointWorld',type='string')
                cmds.setAttr(newPass+'.vray_filtering_extratex',0)
                cmds.setAttr(newPass+'.vray_considerforaa_extratex',0)
                newPass = cmds.rename(newPass,'vrayRE_pointWorld')
            elif p=='z-depth':
                cmds.setAttr(newPass+'.vray_filtering_zdepth',0)
                cmds.setAttr(newPass+'.vray_depthClamp',0)
            elif p=='velocity':
                cmds.setAttr(newPass+'.vray_filtering_velocity',0)
                cmds.setAttr(newPass+'.vray_clamp_velocity',0)
                cmds.setAttr(newPass+'.vray_max_velocity',10)
            cmds.setAttr(newPass+'.enabled',0)
            passList.append(newPass)
    # now set overrides.
    cmds.editRenderLayerGlobals(crl=layerName)
    for p in passList:
        cmds.editRenderLayerAdjustment(p+'.enabled')
        cmds.setAttr(p+'.enabled',1)
    cmds.editRenderLayerGlobals(crl='defaultRenderLayer')
    # done.
    print '\nTech layer settings applied to layer %s.' % (layerName)

def quickPassesUI():
    # dropdown list at top chooses between 'beauty' and 'tech' layers. picking a layer type changes the checkbox dropdowns below.
    # also offer a dropdown input for the layer you want to apply settings to.
    window = 'quickPassesWindow'
    if cmds.window(window,q=1,exists=1): cmds.deleteUI(window)
    cmds.window(window,t='VRay Quick Passes',w=250,h=400)
    wrapper = cmds.formLayout()
    overrideCheck = cmds.checkBox(l='globals overrides?',v=1)
    goBtn = cmds.button(l='create passes',bgc=[0.6,0.7,1.0],w=150,h=50,c=lambda *x: doCreatePasses(cmds.optionMenu(typeSelect,q=1,v=1),checkLayout,cmds.optionMenu(layerSelect,q=1,v=1),cmds.checkBox(overrideCheck,q=1,v=1)))
    typeSelect = cmds.optionMenu(l='Layer type: ',cc=lambda *x: popPassList(checkLayout,cmds.optionMenu(typeSelect,q=1,v=1)))
    cmds.menuItem(l='beauty')
    cmds.menuItem(l='tech')
    layerSelect = cmds.optionMenu(l='Layer name:')
    renderLayers = [f for f in cmds.ls(type='renderLayer') if ':' not in f]
    for i in renderLayers:
        cmds.menuItem(l=i)
    # next up is a placeholder for a checkbox array.
    checkLayout = cmds.columnLayout(rs=5,parent=wrapper)
    # populate checklist.
    popPassList(checkLayout,cmds.optionMenu(typeSelect,q=1,v=1))
    # layout wrapper.
    lm1=5
    lm2=15
    tm1=5
    tm2=30
    tm3=55
    tm4=85
    tm5=340
    cmds.formLayout(wrapper,e=1,attachForm=[(typeSelect,'left',lm1),(typeSelect,'top',tm1),(layerSelect,'left',lm1),(layerSelect,'top',tm2),
                                            (checkLayout,'left',lm2),(checkLayout,'top',tm4),(goBtn,'left',lm1),(goBtn,'top',tm5),(overrideCheck,'left',lm1),(overrideCheck,'top',tm3)])
    cmds.showWindow(window)
    cmds.window(window,e=1,w=250,h=400)

def popPassList(layout,layerType,*args):
    # remove existing children of the layout, then add checkboxes as needed for each layout type.
    children = cmds.columnLayout(layout,q=1,ca=1)
    if children:
        for c in children:
            cmds.deleteUI(c)
    if layerType == 'beauty':
        passes = ['lighting','diffuse','GI','specular','reflection','refraction','self-illumination','SSS','shadow','caustics','rawShadow']
        for p in sorted(passes,key=str.lower):
            checkBox = cmds.checkBox(l=p,parent=layout)
    elif layerType == 'tech':
        passes = ['z-depth','velocity','AO','UV','normals','bump normals','fresnel','pointWorld']
        for p in sorted(passes,key=str.lower):
            checkBox = cmds.checkBox(l=p,parent=layout)

def doCreatePasses(layerType,layout,layerName,*args):
    # depending on layer type, run the appropriate function. parse checkbox values and pass them to the function.
    checkCtrls = cmds.columnLayout(layout,q=1,ca=1)
    passes = []
    for i in checkCtrls:
        if cmds.checkBox(i,q=1,v=1):
            label = cmds.checkBox(i,q=1,l=1)
            passes.append(label)
    if layerType == 'beauty':
        defineBeautyLayer(layerName,passes)
    elif layerType == 'tech':
        defineTechLayer(layerName,passes)
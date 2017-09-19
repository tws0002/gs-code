import maya.cmds as cmds

def setRenderPrefix2():
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix',l=0)
    filepath=cmds.file(sn=1,q=1)
    shotname=filepath.split('/lighting')[0].split('/')[-1]
    imagePrefix = shotname+'/<Layer>/<Scene>/<Scene>_<Layer>'
    forceSceneAttrs()
    if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'vray':
        if cmds.getAttr('vraySettings.imageFormatStr') == 'exr (multichannel)':
            imagePrefix = imagePrefix + '.'
        cmds.setAttr('vraySettings.fileNamePrefix', imagePrefix, type='string')
    else:
        try:
            cmds.setAttr('defaultRenderGlobals.imageFilePrefix', imagePrefix, type='string')
        except:
            pass

def overwriteRenderPath():
    import mustache
    mustache.M.MSUB.setRenderPrefix=setRenderPrefix2
    print 'mustache renderpath fix'

try:
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix',l=0)
except:
    pass
overwriteRenderPath()

def forceSceneAttrs():
    cmds.setAttr("redshiftOptions.motionBlurEnable",0)
    if cmds.objExists('rsAov_MotionVectors'):
        cmds.setAttr('rsAov_MotionVectors.outputRawVectors',1)
        cmds.setAttr('rsAov_MotionVectors.filtering',0)
        print 'fixed MV'
    if cmds.objExists('rsAov_m_mortonC'):
        cmds.setAttr('rsAov_m_mortonC.blueId',509)
    if cmds.objExists('rsAov_m_miaYoungestB'):
        cmds.setAttr('rsAov_m_miaYoungestB.blueId',106)
    if cmds.objExists('rsAov_m_miaMidB'):
        cmds.setAttr('rsAov_m_miaMidB.blueId',206)  
    if cmds.objExists('rsAov_m_miaTeenB'):
        cmds.setAttr('rsAov_m_miaTeenB.blueId',306)  
    if cmds.objExists('rsAov_m_miaAdultB'):
        cmds.setAttr('rsAov_m_miaAdultB.blueId',406)  

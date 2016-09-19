# m_massAssetEdit.py v0.02 by Henry Foster (henry@toadstorm.com), 7/25/2011
#
# for use with }MUSTACHE{. adds render layers, overrides and shading assignments to a list of files, automatically incrementing versions.

import sys
import pickle
import subprocess
import maya.standalone
import maya.cmds as cmds
import maya.mel as mel
import os

assets = pickle.loads(sys.argv[1])
impFiles = pickle.loads(sys.argv[2])
masterFlag = int(sys.argv[3])
user = sys.argv[4]
melScript = pickle.loads(sys.argv[5])
pyScript = pickle.loads(sys.argv[6])
doOverrides = sys.argv[7]
sys.stdout.write('\nInitializing Maya Python interpreter.')
maya.standalone.initialize(name='python')

# for each asset, import materials file, create renderLayer[x], assign all objects, assign material[x] to objects, assign overrides[x] to objects,
# remove namespace (use force flag), master if necessary, save up.

for asset in assets:

    sys.stdout.write('\nProcessing asset: '+asset+'\n')
    cmds.file(asset,open=1,f=1)
    importLayers = []
    modLayers = []
    for impFile in impFiles:
        cmds.file(impFile,i=1,ns='massAssetEdit')
        sourceGeo = 'massAssetEdit:massAssetEditGEOShape'
        layerName = os.path.splitext(impFile.split('EXPORT_')[-1])[0]
        shadingGroup = cmds.listConnections(sourceGeo,s=0,d=1,p=0,type='shadingEngine')[0]
        meshes = cmds.ls(type=['mesh','nurbsSurface'])
        xforms = []
        for mesh in meshes:
            xforms.append(cmds.listRelatives(mesh,p=1)[0])
        # make a new renderLayer if it doesn't already exist.
        layers = cmds.ls(type='renderLayer')
        if layerName in layers:
            cmds.editRenderLayerGlobals(crl=layerName)
            if layerName != 'defaultRenderLayer':
                cmds.editRenderLayerMembers(layerName,xforms)
                modLayers.append(layerName)
        else:
            cmds.createRenderLayer(xforms,mc=1,name=layerName)
            cmds.setAttr(layerName+'.renderable',0)
            importLayers.append(layerName)
        # assign material to objects if material isn't default.
        if shadingGroup.split(':')[-1] != 'initialShadingGroup':
            cmds.select(meshes,r=1)
            cmds.sets(e=1,forceElement=shadingGroup)
        if int(doOverrides) == 1:
            for mesh in meshes:
                if cmds.getAttr(sourceGeo+'.castsShadows') != cmds.getAttr(mesh+'.castsShadows'):
                    cmds.setAttr(mesh+'.castsShadows',cmds.getAttr(sourceGeo+'.castsShadows'))
                if cmds.getAttr(sourceGeo+'.receiveShadows') != cmds.getAttr(mesh+'.receiveShadows'):
                    cmds.setAttr(mesh+'.receiveShadows',cmds.getAttr(sourceGeo+'.receiveShadows'))
                if cmds.getAttr(sourceGeo+'.primaryVisibility') != cmds.getAttr(mesh+'.primaryVisibility'):
                    cmds.setAttr(mesh+'.primaryVisibility',cmds.getAttr(sourceGeo+'.primaryVisibility'))
                if cmds.getAttr(sourceGeo+'.visibleInReflections') != cmds.getAttr(mesh+'.visibleInReflections'):
                    cmds.setAttr(mesh+'.visibleInReflections',cmds.getAttr(sourceGeo+'.visibleInReflections'))
                if cmds.getAttr(sourceGeo+'.visibleInRefractions') != cmds.getAttr(mesh+'.visibleInRefractions'):
                    cmds.setAttr(mesh+'.visibleInRefractions',cmds.getAttr(sourceGeo+'.visibleInRefractions'))
        # delete unused garbage, remove namespace.
        cmds.delete('massAssetEdit:massAssetEditGEO')
        cmds.namespace(set=':')
        cmds.namespace(mv=('massAssetEdit',':'),force=1)
        cmds.namespace(rm='massAssetEdit')
    # okay, now swap back to masterLayer and version up.
    cmds.editRenderLayerGlobals(crl='defaultRenderLayer')
    # before versioning, any MEL or Python commands to run?
    if melScript != '':
        # execute.
        try:
            mel.eval(melScript)
        except:
            error = sys.exc_info()
            errString = 'Error executing custom MEL script: \n%s: %s' % (error[0],error[2])
            sys.stdout.write(errString)
    if pyScript != '':
        try:
            exec pyScript
        except:
            error = sys.exc_info()
            errString = 'Error executing custom Python script: \n%s: %s' % (error[0],error[2])
            sys.stdout.write(errString)
    versionsFolder = os.path.dirname(asset)
    # first, are we supposed to master this thing?
    if masterFlag == 1:
        # find and overwrite the master file.
        masterFileName = '_'.join(cmds.file(q=1,sn=1,shn=1).split('_')[0:-2])
        masterFilePath = os.path.join(versionsFolder,'..',masterFileName+'.mb')
        cmds.file(rename=masterFilePath)
        cmds.file(s=1,f=1)
        sys.stdout.write('\nNew master saved: '+cmds.file(q=1,sn=1))
    # now check versionsFolder and save up.
    versionFiles = [f for f in os.listdir(versionsFolder) if os.path.splitext(f)[-1] == '.mb' or os.path.splitext(f)[-1] == '.ma']
    hiVersion = '000'
    for f in versionFiles:
        # get the highest version.
        versionNum = f.split('_')[-2].strip('v')
        if int(versionNum) > int(hiVersion):
            hiVersion = versionNum
    hiVersion = str(int(hiVersion) + 1).zfill(3)
    # rename the file using the version we want.
    assetName = '_'.join(asset.split('_')[0:-2])
    newFileName = assetName+'_v'+hiVersion+'_'+user+'.mb'
    newFilePath = os.path.join(versionsFolder,newFileName)
    cmds.file(rename=newFilePath)
    writeFile = cmds.file(s=1,f=1)
    sys.stdout.write('\nNew version saved: ' + writeFile)
    # create a textfile annotation. we can't make a screenshot because we're in yatch mode so ignore that part.
    textPath = os.path.join(os.path.dirname(asset),'..','_pipeline',os.path.splitext(cmds.file(q=1,sn=1,shn=1))[0]+'.txt')
    openFile = open(textPath,'w')
    editString = ''
    if len(importLayers) > 0:
        editString = 'New render layer(s) %s automatically added by Mustache. ' % (', '.join(importLayers))
    if len(modLayers) > 0:
        editString = editString + 'Existing render layers %s modified by Mustache' % (', '.join(modLayers))
    if len(importLayers) == 0 and len(modLayers) == 0:
        # this was probably an edit to the masterLayer. just print a generic string.
        editString = 'Default object render settings modified by Mustache.'
    pickle.dump(editString,openFile)
    openFile.close()

print '\noperation complete! press enter to exit.'
end = raw_input()